"""Stacked-event test of H4 (pre-specified in docs/research_design.md, section 8c).

CAR_ie = a_e + g_e * placebo_i + beta * (s_e * x_ie) + e_ie,   H4: beta > 0.

Outputs (output/tables):
  stacked_firm_event.csv     one row per firm x event: exposure, CARs, exclusion flag
  stacked_event_slopes.csv   event-by-event exposure slopes (HC3)
  stacked_pooled.csv         pooled beta: main spec and robustness, firm-clustered and
                             placebo-date p-values
  stacked_placebo_draws.csv  placebo-date distribution of beta for the main spec
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm

from config import (DERIVED, EST_WINDOW, EVENTS, MARKET_TICKER, N_PLACEBO_DRAWS, PLACEBO_SEED,
                    RAW, STACK_WINDOW, TABLES)
from es_utils import car, fit_market_model, load_returns, relative_days

YEAR_END = pd.Timestamp("2024-12-31")


def near_events(index: pd.DatetimeIndex, pad: int) -> pd.Series:
    bad = pd.Series(False, index=index)
    for e in EVENTS:
        p = index.get_loc(pd.Timestamp(e["date"]))
        bad.iloc[max(p - pad, 0): p + pad + 1] = True
    return bad


def build_panel(rets, prices, firms) -> pd.DataFrame:
    r_m = rets[MARKET_TICKER]
    excl = near_events(rets.index, pad=1)
    um = firms["merchant_mw_per_bn"] * firms["mcap_bn"]  # uncontracted non-regulated MW
    p_dec = prices.loc[prices.index[prices.index <= YEAR_END][-1]]
    rows = []
    for e in EVENTS:
        rel = relative_days(rets.index, e["date"])
        est = (rel >= EST_WINDOW[0]) & (rel <= EST_WINDOW[1]) & ~excl
        d_pre = rel.index[rel == -11][0]
        for t in firms.index:
            mm = fit_market_model(rets[t], r_m, est)
            if mm is None:
                continue
            ar = rets[t] - mm["alpha"] - mm["beta"] * r_m
            mcap_e = firms.loc[t, "mcap_bn"] * prices.loc[d_pre, t] / p_dec[t]
            rows.append({
                "event": e["id"], "label": e["label"], "date": e["date"], "sign": e["sign"],
                "ticker": t, "group": firms.loc[t, "group"],
                "placebo": float(firms.loc[t, "sector_type"] == "placebo"),
                "merchant": float(firms.loc[t, "group"] == "merchant"),
                "x": um[t] / mcap_e / 100,  # 100 MW per $bn, pre-event value
                "excluded_party": t in e["exclude"],
                "CAR01": car(ar, rel, *STACK_WINDOW), "CAR00": car(ar, rel, 0, 0),
            })
    return pd.DataFrame(rows)


def design(df: pd.DataFrame, xcol: str) -> pd.DataFrame:
    ev = pd.get_dummies(df["event"], prefix="ev").astype(float)
    evp = ev.mul(df["placebo"], axis=0).add_prefix("plc_")
    signed = (df["sign"] * df[xcol]).rename("beta")
    return pd.concat([ev, evp, signed], axis=1)


def pooled(df: pd.DataFrame, y: str, xcol: str) -> dict:
    d = df.dropna(subset=[y])
    X = design(d, xcol)
    res = sm.OLS(d[y], X).fit(cov_type="cluster", cov_kwds={"groups": d["ticker"]})
    return {"beta": res.params["beta"], "se_firm_cluster": res.bse["beta"],
            "p_firm_cluster": res.pvalues["beta"], "N": int(res.nobs),
            "n_events": d["event"].nunique()}


def placebo_draws(resid_L: pd.DataFrame, x_dec: pd.Series, placebo: pd.Series,
                  signs: list[int], n: int, rng) -> np.ndarray:
    """beta from stacked regressions on random non-event dates with permuted signs."""
    dates = resid_L.index
    tick = resid_L.columns
    xv, pv = x_dec[tick].to_numpy(), placebo[tick].to_numpy()
    k = len(signs)
    out = np.empty(n)
    for i in range(n):
        pick = rng.choice(len(dates), size=k, replace=False)
        sg = rng.permutation(signs)
        ys, Xs = [], []
        for j, (di, s) in enumerate(zip(pick, sg)):
            y = resid_L.iloc[di].to_numpy()
            ok = ~np.isnan(y)
            Xj = np.zeros((ok.sum(), 2 * k + 1))
            Xj[:, j] = 1.0
            Xj[:, k + j] = pv[ok]
            Xj[:, -1] = s * xv[ok]
            ys.append(y[ok])
            Xs.append(Xj)
        b = np.linalg.lstsq(np.vstack(Xs), np.concatenate(ys), rcond=None)[0]
        out[i] = b[-1]
    return out


def main() -> None:
    firms = pd.read_csv(DERIVED / "exposure.csv").set_index("ticker")
    rets = load_returns()
    prices = pd.read_csv(RAW / "prices_yf.csv", index_col=0, parse_dates=True).loc[rets.index]
    panel = build_panel(rets, prices, firms)
    TABLES.mkdir(parents=True, exist_ok=True)
    panel.to_csv(TABLES / "stacked_firm_event.csv", index=False, float_format="%.6f")
    main_df = panel[~panel["excluded_party"]]

    # Event-by-event slopes (unsigned x; H4 predicts sign = s_e).
    sl = []
    for e in EVENTS:
        d = main_df[main_df["event"] == e["id"]].dropna(subset=["CAR01"])
        X = sm.add_constant(d[["placebo", "x"]])
        r = sm.OLS(d["CAR01"], X).fit(cov_type="HC3")
        sl.append({"event": e["id"], "label": e["label"], "date": e["date"], "sign": e["sign"],
                   "beta_e": r.params["x"], "se_HC3": r.bse["x"], "p_HC3": r.pvalues["x"],
                   "N": int(r.nobs), "sign_matches": np.sign(r.params["x"]) == e["sign"]})
    pd.DataFrame(sl).to_csv(TABLES / "stacked_event_slopes.csv", index=False,
                            float_format="%.5f")

    # Placebo-date machinery: one market model over the whole sample, excluding events.
    r_m = rets[MARKET_TICKER]
    excl3 = near_events(rets.index, pad=3)
    resid = {}
    for t in firms.index:
        mm = fit_market_model(rets[t], r_m, ~near_events(rets.index, pad=1))
        if mm is not None:
            resid[t] = rets[t] - mm["alpha"] - mm["beta"] * r_m
    resid = pd.DataFrame(resid)
    x_dec = firms["merchant_mw_per_bn"] / 100
    merch = (firms["group"] == "merchant").astype(float)
    plc = (firms["sector_type"] == "placebo").astype(float)

    def window_sums(L):
        s = resid.rolling(L).sum().shift(-(L - 1))  # sum of days t .. t+L-1
        ok_dates = ~excl3 & s.notna().mean(axis=1).gt(0.95)
        ok_dates &= ~excl3.shift(-(L - 1), fill_value=True)
        return s[ok_dates]

    rng = np.random.default_rng(PLACEBO_SEED)
    signs_all = [e["sign"] for e in EVENTS]
    specs = [
        ("main: CAR[0,1], x, parties excluded", main_df, "CAR01", "x", 2, x_dec, signs_all),
        ("parties included", panel, "CAR01", "x", 2, x_dec, signs_all),
        ("window CAR[0,0]", main_df, "CAR00", "x", 1, x_dec, signs_all),
        ("merchant dummy instead of x", main_df, "CAR01", "merchant", 2, merch, signs_all),
    ]
    for e in EVENTS:
        keep = [f for f in EVENTS if f["id"] != e["id"]]
        specs.append((f"drop {e['id']}", main_df[main_df["event"] != e["id"]], "CAR01", "x", 2,
                      x_dec, [f["sign"] for f in keep]))

    out, main_draws = [], None
    for name, d, y, xcol, L, xp, signs in specs:
        res = pooled(d, y, xcol)
        draws = placebo_draws(window_sums(L), xp, plc, signs, N_PLACEBO_DRAWS, rng)
        res.update({"spec": name,
                    "p_placebo_one_sided": (draws >= res["beta"]).mean(),
                    "p_placebo_two_sided": (np.abs(draws) >= abs(res["beta"])).mean(),
                    "placebo_draws": len(draws)})
        out.append(res)
        if main_draws is None:
            main_draws = draws
    cols = ["spec", "beta", "se_firm_cluster", "p_firm_cluster", "p_placebo_one_sided",
            "p_placebo_two_sided", "N", "n_events", "placebo_draws"]
    pooled_tab = pd.DataFrame(out)[cols]
    pooled_tab.to_csv(TABLES / "stacked_pooled.csv", index=False, float_format="%.5f")
    pd.DataFrame({"beta": main_draws}).to_csv(TABLES / "stacked_placebo_draws.csv", index=False,
                                              float_format="%.6f")

    with pd.option_context("display.width", 200, "display.float_format", "{:.4f}".format):
        print(pd.DataFrame(sl).to_string(index=False))
        print(pooled_tab.to_string(index=False))


if __name__ == "__main__":
    main()
