"""Download daily adjusted prices for the firm universe and the market proxy.

Writes data/raw/prices_yf.csv (wide, adjusted close) and data/raw/download_meta.json.
Yahoo data can be revised, so the raw file is kept as downloaded and never edited.
"""
import json
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

from config import END, FIRMS, MARKET_TICKER, RAW, START


def main() -> None:
    firms = pd.read_csv(FIRMS)
    tickers = sorted(set(firms["ticker"]) | {MARKET_TICKER})

    data = yf.download(
        tickers, start=START, end=END, auto_adjust=True, progress=False, threads=True
    )
    prices = data["Close"].sort_index()

    missing = [t for t in tickers if t not in prices.columns or prices[t].dropna().empty]
    RAW.mkdir(parents=True, exist_ok=True)
    prices.to_csv(RAW / "prices_yf.csv")

    meta = {
        "source": "Yahoo Finance via yfinance",
        "yfinance_version": yf.__version__,
        "downloaded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "start": START,
        "end": END,
        "adjusted": True,
        "n_tickers": len(tickers),
        "missing": missing,
        "first_valid_date": {t: str(prices[t].first_valid_index().date())
                             for t in prices.columns if prices[t].notna().any()},
    }
    (RAW / "download_meta.json").write_text(json.dumps(meta, indent=2))

    print(f"saved {prices.shape[1]} series x {prices.shape[0]} days")
    if missing:
        print("MISSING:", missing)
    download_mcap(sorted(firms["ticker"]))


def download_mcap(tickers: list[str], date: str = "2024-12-31") -> None:
    """Equity market cap at the last pre-event year-end: shares outstanding x unadjusted close."""
    px = yf.download(tickers, start="2024-12-27", end="2025-01-03", auto_adjust=False,
                     progress=False)["Close"]
    px = px[px.index <= pd.Timestamp(date)].iloc[-1]
    rows = []
    for t in tickers:
        s = yf.Ticker(t).get_shares_full(start="2024-09-01", end="2025-01-10")
        if s is None or s.empty:
            rows.append({"ticker": t, "shares": None, "shares_date": None})
            continue
        s.index = s.index.tz_localize(None)
        s = s[s.index <= pd.Timestamp(date)]
        rows.append({"ticker": t, "shares": float(s.iloc[-1]) if len(s) else None,
                     "shares_date": str(s.index[-1].date()) if len(s) else None})
    m = pd.DataFrame(rows)
    m["close"] = m["ticker"].map(px)
    m["mcap_bn"] = m["shares"] * m["close"] / 1e9
    m.to_csv(RAW / "mcap_20241231.csv", index=False)
    print("market caps:", m["mcap_bn"].notna().sum(), "of", len(m))


if __name__ == "__main__":
    main()
