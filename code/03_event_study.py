"""Market-model event study of the 27 Jan 2025 DeepSeek shock on US power-sector equities.

Groups and exposure measures come from data/derived/exposure.csv (02_build_exposure.py).

Outputs (output/tables):
  firm_car.csv         firm-level betas, residual s.d., abnormal and cumulative abnormal returns
  group_tests.csv      mean CAR by group with BMP and Kolari-Pynnonen adjusted t-statistics
  portfolio_tests.csv  equal-weighted group and long-short portfolio CARs
  gradient.csv         cross-sectional CAR regressions (group dummies under three classification
                       versions; continuous exposure), with HC3 s.e. and placebo-day p-values
  deepseek_ar_paths.csv  firm-level daily AR and cumulative AR, days -5 to +20 (for R figures)
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from config import (CAR_WINDOWS, DERIVED, EST_WINDOW, EVENT_DATE, MARKET_TICKER,
                    SECONDARY_EVENTS, TABLES)
from es_utils import car, fit_market_model, kp_tests, load_returns, relative_days

GROUPS = ["merchant", "hybrid", "regulated", "placebo"]


def gradient(fc: pd.DataFrame, resid_df: pd.DataFrame, X: pd.DataFrame, coef: str,
             spec: str) -> list[dict]:
    """CAR regressed on X for each post-event window; placebo-day p-value for `coef`."""
    out = []
    for a, b in CAR_WINDOWS:
        if a < 0:
            continue
        L = b - a + 1
        col = f"CAR[{a},{b}]"
        y = fc[col].dropna()
        ols = sm.OLS(y, X.loc[y.index]).fit(cov_type="HC3")
        roll = resid_df.rolling(L).sum().iloc[L - 1:]
        placebo = []
        for d in roll.index:
            yy = roll.loc[d].dropna()
            xx = X.loc[yy.index]
            if (xx[coef] != 0).sum() < 2:
                continue
            placebo.append(sm.OLS(yy, xx).fit().params[coef])
        placebo = np.asarray(placebo)
        b_c = ols.params[coef]
        out.append({"spec": spec, "coef": coef, "window": col, "N": int(ols.nobs),
                    "estimate": b_c, "se_HC3": ols.bse[coef],
                    "p_HC3": ols.pvalues[coef], "placebo_days": len(placebo),
                    "p_placebo_days": (np.abs(placebo) >= abs(b_c)).mean(),
                    "note": "overlapping windows" if L > 1 else ""})
    return out


def main() -> None:
    firms = pd.read_csv(DERIVED / "exposure.csv").set_index("ticker")
    rets = load_returns()
    rel = relative_days(rets.index, EVENT_DATE)
    r_m = rets[MARKET_TICKER]

    secondary = pd.to_datetime(list(SECONDARY_EVENTS))
    est_mask = (rel >= EST_WINDOW[0]) & (rel <= EST_WINDOW[1]) & ~rets.index.isin(secondary)

    rows, ar_all, resid_all = [], {}, {}
    for t in firms.index:
        if t not in rets:
            continue
        mm = fit_market_model(rets[t], r_m, est_mask)
        if mm is None:
            print(f"skip {t}: fewer than {MIN_EST_OBS} estimation days")
            continue
        ar = rets[t] - mm["alpha"] - mm["beta"] * r_m
        ar_all[t], resid_all[t] = ar, mm["resid"]
        row = {"ticker": t, "group": firms.loc[t, "group"], "beta": mm["beta"],
               "s": mm["s"], "T_est": mm["T"]}
        for a, b in CAR_WINDOWS:
            row[f"CAR[{a},{b}]"] = car(ar, rel, a, b)
        rows.append(row)

    fc = pd.DataFrame(rows).set_index("ticker")
    ar_df = pd.DataFrame(ar_all)
    resid_df = pd.DataFrame(resid_all)
    TABLES.mkdir(parents=True, exist_ok=True)
    fc.join(firms[["group_prelim", "group_v10", "merchant_mw_per_bn", "nr_mw_per_bn"]]) \
        .to_csv(TABLES / "firm_car.csv", float_format="%.5f")

    # Group means with BMP / Kolari-Pynnonen tests (standardized CAR = CAR / (s * sqrt(L))).
    gt = []
    for g in GROUPS:
        sub = fc[fc["group"] == g]
        for a, b in CAR_WINDOWS:
            col = f"CAR[{a},{b}]"
            scar = sub[col] / (sub["s"] * np.sqrt(b - a + 1))
            gt.append({"group": g, "window": col, "mean_CAR": sub[col].mean(),
                       "median_CAR": sub[col].median(), **kp_tests(scar, resid_df)})
    pd.DataFrame(gt).to_csv(TABLES / "group_tests.csv", index=False, float_format="%.4f")

    # Portfolio approach: one return series per portfolio, so no cross-correlation problem.
    def ew(g):
        return rets[fc.index[fc["group"] == g]].mean(axis=1)
    ports = {g: ew(g) for g in GROUPS}
    ports["merchant_minus_regulated"] = ports["merchant"] - ports["regulated"]
    pt = []
    for name, rp in ports.items():
        mm = fit_market_model(rp, r_m, est_mask)
        ar = rp - mm["alpha"] - mm["beta"] * r_m
        for a, b in CAR_WINDOWS:
            c = car(ar, rel, a, b)
            tstat = c / (mm["s"] * np.sqrt(b - a + 1))
            pt.append({"portfolio": name, "window": f"CAR[{a},{b}]", "CAR": c, "t": tstat,
                       "p": 2 * stats.t.sf(abs(tstat), df=mm["T"] - 2), "beta": mm["beta"]})
    pd.DataFrame(pt).to_csv(TABLES / "portfolio_tests.csv", index=False, float_format="%.4f")

    # Cross-sectional gradients.
    f = firms.loc[fc.index]
    gr = []
    for version in ["group", "group_v10", "group_prelim"]:
        d = pd.get_dummies(f[version]).reindex(columns=["merchant", "hybrid", "placebo"],
                                               fill_value=0).astype(float)
        gr += gradient(fc, resid_df, sm.add_constant(d), "merchant", f"dummies_{version}")
    placebo_d = (f["sector_type"] == "placebo").astype(float).rename("placebo")
    for measure in ["merchant_mw_per_bn", "nr_mw_per_bn"]:
        x = (f[measure] / 100).rename(measure)  # per 100 MW per $bn
        X = sm.add_constant(pd.concat([x, placebo_d], axis=1))
        gr += gradient(fc, resid_df, X, measure, f"continuous_{measure}_per100")
        elec = f["sector_type"] == "electric"
        X_e = sm.add_constant(x[elec].to_frame())
        gr += gradient(fc.loc[elec], resid_df[fc.index[elec]], X_e, measure,
                       f"continuous_{measure}_per100_electric_only")
    pd.DataFrame(gr).to_csv(TABLES / "gradient.csv", index=False, float_format="%.4f")

    # Firm-level AR paths, days -5 to +20, for the R figures (code/05_figures.R).
    win = (rel >= -5) & (rel <= 20)
    paths = ar_df.loc[win].copy()
    paths.index = rel[win].values
    long = paths.stack().rename("ar").reset_index()
    long.columns = ["rel", "ticker", "ar"]
    long = long.sort_values(["ticker", "rel"])
    long["car"] = long.groupby("ticker")["ar"].cumsum()
    long["group"] = long["ticker"].map(fc["group"])
    long.to_csv(TABLES / "deepseek_ar_paths.csv", index=False, float_format="%.6f")

    with pd.option_context("display.width", 200, "display.float_format", "{:.4f}".format):
        print(pd.DataFrame(pt).query("window in ['CAR[0,0]','CAR[0,1]','CAR[0,5]','CAR[-5,-1]']"))
        print(pd.DataFrame(gr).query("window in ['CAR[0,0]','CAR[0,1]']")
              .drop(columns=["note"]).to_string(index=False))


if __name__ == "__main__":
    main()
