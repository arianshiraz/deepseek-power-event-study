"""Shared event-study helpers: returns, market model, CARs, Kolari-Pynnonen tests."""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from config import MARKET_TICKER, MIN_EST_OBS, RAW


def load_returns() -> pd.DataFrame:
    """Daily simple returns on the market trading calendar."""
    prices = pd.read_csv(RAW / "prices_yf.csv", index_col=0, parse_dates=True)
    prices = prices[prices[MARKET_TICKER].notna()]
    return prices.pct_change(fill_method=None).iloc[1:]


def relative_days(index: pd.DatetimeIndex, event_date: str) -> pd.Series:
    pos = index.get_loc(pd.Timestamp(event_date))
    return pd.Series(np.arange(len(index)) - pos, index=index, name="rel")


def fit_market_model(r_i: pd.Series, r_m: pd.Series, est_mask: pd.Series):
    df = pd.concat([r_i, r_m], axis=1, keys=["ri", "rm"])[est_mask].dropna()
    if len(df) < MIN_EST_OBS:
        return None
    res = sm.OLS(df["ri"], sm.add_constant(df["rm"])).fit()
    s = np.sqrt(res.ssr / res.df_resid)
    return {"alpha": res.params["const"], "beta": res.params["rm"], "s": s,
            "T": len(df), "resid": res.resid}


def car(ar: pd.Series, rel: pd.Series, a: int, b: int) -> float:
    w = ar[(rel >= a) & (rel <= b)]
    return w.sum() if len(w) == b - a + 1 and w.notna().all() else np.nan


def kp_tests(scar: pd.Series, resid: pd.DataFrame) -> dict:
    """Boehmer-Musumeci-Poulsen t and the Kolari-Pynnonen (2010) cross-correlation adjustment."""
    scar = scar.dropna()
    n = len(scar)
    if n < 2:
        return {"N": n, "t_bmp": np.nan, "rbar": np.nan, "t_kp": np.nan, "p_kp": np.nan}
    t_bmp = scar.mean() * np.sqrt(n) / scar.std(ddof=1)
    c = resid[scar.index].corr().to_numpy()
    rbar = c[~np.eye(n, dtype=bool)].mean()
    t_kp = t_bmp * np.sqrt((1 - rbar) / (1 + (n - 1) * rbar))
    return {"N": n, "t_bmp": t_bmp, "rbar": rbar, "t_kp": t_kp,
            "p_kp": 2 * stats.t.sf(abs(t_kp), df=n - 1)}
