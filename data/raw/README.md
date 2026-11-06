# Raw data provenance

Nothing in this folder is committed except this file. `code/01_download.py` recreates it.

| File | Source | Created by | Notes |
|---|---|---|---|
| `prices_yf.csv` | Yahoo Finance via yfinance, daily adjusted close | `code/01_download.py` | Data can be revised; download time in `download_meta.json` |
| `download_meta.json` | Generated | `code/01_download_prices.py` | yfinance version, timestamp, missing tickers, first valid date per ticker |
| `mcap_20241231.csv` | Yahoo Finance via yfinance (shares outstanding history and unadjusted close) | `code/01_download_prices.py` | Equity market value at 31 Dec 2024 |
| `eia860/2024/` | EIA-860 2024 annual (final), https://www.eia.gov/electricity/data/eia860/archive/xls/eia8602024.zip | `code/02_build_exposure.py` | First downloaded 6 Nov 2026; generator, plant, owner, utility files |

Planned:

| File | Source |
|---|---|
| Fama and French daily factors | Kenneth French data library |
| FY2023 10-K contract passages | SEC EDGAR |
