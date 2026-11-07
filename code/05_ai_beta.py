"""AI-beta control for the stacked-event test (pre-specified in docs/research_design.md, 8d).

Question: does merchant exposure (x) still predict event returns once each firm's general
sensitivity to AI stocks (b_ai) is accounted for?

Outputs (output/tables):
  ai_beta_firm.csv      firm x event: exposure x, AI beta (per factor), market-model and
                        two-factor CARs
  ai_beta_pooled.csv    pooled sign-adjusted beta under each specification and factor, with
                        firm-clustered and placebo-date p-values
  ai_beta_deepseek.csv  DeepSeek-day cross-section: CAR[0,0] on x, b_ai and placebo dummy
"""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from config import (AI_FACTORS, DERIVED, EST_WINDOW, EVENTS, MARKET_TICKER, MIN_EST_OBS,
                    N_PLACEBO_DRAWS, PLACEBO_SEED, RAW, STACK_WINDOW, TABLES)
from es_utils import car, load_returns, relative_days

_spec = importlib.util.spec_from_file_location(
    "stacked", Path(__file__).with_name("04_stacked_events.py"))
st = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(st)


def orthogonalise(r_ai: pd.Series, r_m: pd.Series, mask: pd.Series) -> pd.Series:
    d = pd.concat([r_ai, r_m], axis=1, keys=["ai", "m"])[mask].dropna()
    fit = sm.OLS(d["ai"], sm.add_constant(d["m"])).fit()
    return r_ai - fit.params["const"] - fit.params["m"] * r_m


def two_factor(r_i, r_m, r_perp, mask):
    d = pd.concat([r_i, r_m, r_perp], axis=1, keys=["i", "m", "ai"])[mask].dropna()
    if len(d) < MIN_EST_OBS:
        return None
    p = sm.OLS(d["i"], sm.add_constant(d[["m", "ai"]])).fit().params
    return p["const"], p["m"], p["ai"]


def placebo_with_controls(sums: pd.DataFrame, x: pd.Series, plc: pd.Series,
                          ctrl: pd.Series | None, signs: list[int], n: int, rng,
                          ctrl_common: pd.DataFrame | None = None) -> np.ndarray:
    """Pooled beta on random non-event dates.

    ctrl: firm-level control with an event-specific coefficient (AI beta).
    ctrl_common: date x firm control with one common coefficient (AI beta x factor move).
    """
    tick = sums.columns
    xv, pv = x[tick].to_numpy(), plc[tick].to_numpy()
    cv = None if ctrl is None else ctrl[tick].to_numpy()
    k = len(signs)
    width = 2 * k + (k if cv is not None else 0) + (1 if ctrl_common is not None else 0) + 1
    out = np.empty(n)
    for i in range(n):
        pick = rng.choice(len(sums), size=k, replace=False)
        sg = rng.permutation(signs)
        ys, Xs = [], []
        for j, (di, s) in enumerate(zip(pick, sg)):
            y = sums.iloc[di].to_numpy()
            cc = None if ctrl_common is None else ctrl_common.loc[sums.index[di], tick].to_numpy()
            ok = ~np.isnan(y) & ~np.isnan(xv)
            if cv is not None:
                ok &= ~np.isnan(cv)
            if cc is not None:
                ok &= ~np.isnan(cc)
            Xj = np.zeros((ok.sum(), width))
            Xj[:, j] = 1.0
            Xj[:, k + j] = pv[ok]
            if cv is not None:
                Xj[:, 2 * k + j] = cv[ok]
            if cc is not None:
                Xj[:, -2] = cc[ok]
            Xj[:, -1] = s * xv[ok]
            ys.append(y[ok])
            Xs.append(Xj)
        out[i] = np.linalg.lstsq(np.vstack(Xs), np.concatenate(ys), rcond=None)[0][-1]
    return out


def main() -> None:
    firms = pd.read_csv(DERIVED / "exposure.csv").set_index("ticker")
    rets = load_returns()
    prices = pd.read_csv(RAW / "prices_yf.csv", index_col=0, parse_dates=True).loc[rets.index]
    r_m = rets[MARKET_TICKER]
    excl1 = st.near_events(rets.index, pad=1)
    excl3 = st.near_events(rets.index, pad=3)

    base = st.build_panel(rets, prices, firms)  # x, market-model CARs, exclusion flags
    L = STACK_WINDOW[1] - STACK_WINDOW[0] + 1
    plc = (firms["sector_type"] == "placebo").astype(float)
    x_dec = firms["merchant_mw_per_bn"] / 100
    rng = np.random.default_rng(PLACEBO_SEED + 1)
    signs = [e["sign"] for e in EVENTS]

    # Full-sample residuals for placebo dates.
    full = ~excl1
    mm_resid, bai_full, f2_resid = {}, {}, {fac: {} for fac in AI_FACTORS}
    perp_full = {fac: orthogonalise(rets[fac], r_m, full) for fac in AI_FACTORS}
    for t in firms.index:
        d = pd.concat([rets[t], r_m], axis=1, keys=["i", "m"])[full].dropna()
        p = sm.OLS(d["i"], sm.add_constant(d["m"])).fit().params
        mm_resid[t] = rets[t] - p["const"] - p["m"] * r_m
        for fac in AI_FACTORS:
            a, bm, bai = two_factor(rets[t], r_m, perp_full[fac], full)
            f2_resid[fac][t] = rets[t] - a - bm * r_m - bai * perp_full[fac]
            bai_full[(fac, t)] = bai

    def window_sums(resid: dict) -> pd.DataFrame:
        r = pd.DataFrame(resid)
        s = r.rolling(L).sum().shift(-(L - 1))
        ok = ~excl3 & ~excl3.shift(-(L - 1), fill_value=True) & s.notna().mean(axis=1).gt(0.95)
        return s[ok]

    mm_sums = window_sums(mm_resid)

    firm_rows, pooled_rows, ds_rows = [], [], []
    for fac in AI_FACTORS:
        add = []
        for e in EVENTS:
            rel = relative_days(rets.index, e["date"])
            est = (rel >= EST_WINDOW[0]) & (rel <= EST_WINDOW[1]) & ~excl1
            perp = orthogonalise(rets[fac], r_m, est)
            for t in firms.index:
                tf = two_factor(rets[t], r_m, perp, est)
                if tf is None:
                    continue
                a, bm, bai = tf
                ar2 = rets[t] - a - bm * r_m - bai * perp
                add.append({"event": e["id"], "ticker": t, "factor": fac, "b_ai": bai,
                            "CAR01_2f": car(ar2, rel, *STACK_WINDOW),
                            "CAR00_2f": car(ar2, rel, 0, 0),
                            "factor_CAR01": car(perp, rel, *STACK_WINDOW)})
        panel = base.merge(pd.DataFrame(add), on=["event", "ticker"], how="inner")
        firm_rows.append(panel)
        main_df = panel[~panel["excluded_party"]]

        # Spec 0 (reference): market-model CARs, no control (reproduces 8c on this sample).
        r0 = st.pooled(main_df, "CAR01", "x")
        d0 = placebo_with_controls(mm_sums, x_dec, plc, None, signs, N_PLACEBO_DRAWS, rng)
        # Spec 1 (primary): two-factor abnormal returns.
        r1 = st.pooled(main_df, "CAR01_2f", "x")
        d1 = placebo_with_controls(window_sums(f2_resid[fac]), x_dec, plc, None, signs,
                                   N_PLACEBO_DRAWS, rng)
        # Spec 2: market-model CARs with event-specific AI-beta control.
        d = main_df.dropna(subset=["CAR01", "b_ai"])
        X = st.design(d, "x")
        ev = pd.get_dummies(d["event"], prefix="ai").astype(float).mul(d["b_ai"], axis=0)
        X = pd.concat([X.drop(columns="beta"), ev, X["beta"]], axis=1)
        res2 = sm.OLS(d["CAR01"], X).fit(cov_type="cluster", cov_kwds={"groups": d["ticker"]})
        r2 = {"beta": res2.params["beta"], "se_firm_cluster": res2.bse["beta"],
              "p_firm_cluster": res2.pvalues["beta"], "N": int(res2.nobs),
              "n_events": d["event"].nunique()}
        ctrl = pd.Series({t: bai_full[(fac, t)] for t in firms.index})
        d2 = placebo_with_controls(mm_sums, x_dec, plc, ctrl, signs, N_PLACEBO_DRAWS, rng)

        # Spec 3 (exploratory, added after seeing specs 1-2): control = AI beta x the AI
        # factor's actual CAR[0,1] on that event, one common coefficient. Lets the data price
        # the AI-sentiment channel at any scale, but ties its sign to what AI stocks did.
        d3 = main_df.dropna(subset=["CAR01", "b_ai", "factor_CAR01"]).copy()
        d3["ai_pred"] = d3["b_ai"] * d3["factor_CAR01"]
        X3 = st.design(d3, "x")
        X3 = pd.concat([X3.drop(columns="beta"), d3["ai_pred"], X3["beta"]], axis=1)
        res3 = sm.OLS(d3["CAR01"], X3).fit(cov_type="cluster",
                                           cov_kwds={"groups": d3["ticker"]})
        r3 = {"beta": res3.params["beta"], "se_firm_cluster": res3.bse["beta"],
              "p_firm_cluster": res3.pvalues["beta"], "N": int(res3.nobs),
              "n_events": d3["event"].nunique(),
              "ai_pred_coef": res3.params["ai_pred"], "ai_pred_p": res3.pvalues["ai_pred"]}
        fsum = perp_full[fac].rolling(L).sum().shift(-(L - 1))
        cc = pd.DataFrame({t: ctrl[t] * fsum for t in firms.index})
        d3draws = placebo_with_controls(mm_sums, x_dec, plc, None, signs, N_PLACEBO_DRAWS, rng,
                                        ctrl_common=cc)

        for name, r, draws in [("market model, no control (reference)", r0, d0),
                               ("two-factor abnormal returns (primary)", r1, d1),
                               ("market model + event-specific AI-beta control", r2, d2),
                               ("exploratory: market model + AI beta x factor move", r3,
                                d3draws)]:
            pooled_rows.append({"factor": fac, "spec": name, **r,
                                "p_placebo_one_sided": (draws >= r["beta"]).mean(),
                                "placebo_draws": len(draws)})

        # DeepSeek day alone.
        ds = panel[panel["event"] == "deepseek"].dropna(subset=["CAR00", "b_ai"])
        for y in ["CAR00", "CAR00_2f"]:
            for cols in (["x", "placebo"], ["x", "b_ai", "placebo"]):
                rr = sm.OLS(ds[y], sm.add_constant(ds[cols])).fit(cov_type="HC3")
                ds_rows.append({"factor": fac, "outcome": y, "regressors": "+".join(cols),
                                "x_coef": rr.params["x"], "x_se_HC3": rr.bse["x"],
                                "x_p_HC3": rr.pvalues["x"],
                                "b_ai_coef": rr.params.get("b_ai", np.nan),
                                "b_ai_p_HC3": rr.pvalues.get("b_ai", np.nan),
                                "corr_x_bai": ds["x"].corr(ds["b_ai"]), "N": int(rr.nobs)})

    TABLES.mkdir(parents=True, exist_ok=True)
    fr = pd.concat(firm_rows)
    keep = ["event", "ticker", "group", "factor", "x", "b_ai", "excluded_party", "CAR01",
            "CAR01_2f", "CAR00", "CAR00_2f", "factor_CAR01"]
    fr[keep].to_csv(TABLES / "ai_beta_firm.csv", index=False, float_format="%.6f")
    pr = pd.DataFrame(pooled_rows)
    pr.to_csv(TABLES / "ai_beta_pooled.csv", index=False, float_format="%.5f")
    dr = pd.DataFrame(ds_rows)
    dr.to_csv(TABLES / "ai_beta_deepseek.csv", index=False, float_format="%.5f")

    summ = fr[fr["event"] == "deepseek"].groupby(["factor", "group"])["b_ai"].mean().unstack()
    fac_moves = fr.drop_duplicates(["factor", "event"])[["factor", "event", "factor_CAR01"]]
    with pd.option_context("display.width", 220, "display.float_format", "{:.4f}".format):
        print("Mean AI beta by group (DeepSeek estimation window):\n", summ)
        print("\nAI-factor CAR[0,1] (orthogonalised) by event:\n", fac_moves.to_string(index=False))
        print("\n", pr.to_string(index=False))
        print("\n", dr.to_string(index=False))


if __name__ == "__main__":
    main()
