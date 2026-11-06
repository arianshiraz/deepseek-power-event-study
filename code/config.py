"""Shared settings for the DeepSeek power-sector event study."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DERIVED = ROOT / "data" / "derived"
FIRMS = ROOT / "data" / "classification" / "firms.csv"
TABLES = ROOT / "output" / "tables"
FIGURES = ROOT / "output" / "figures"

MARKET_TICKER = "SPY"

# Download range: covers a ~260-trading-day estimation window before the earliest stacked
# event (30 Jul 2024) and 20 days after the DeepSeek event.
START = "2023-05-01"
END = "2025-03-31"

# Main event: first US trading session after DeepSeek R1 drew wide attention.
EVENT_DATE = "2025-01-27"

# Estimation window, in trading days relative to the event (inclusive).
EST_WINDOW = (-260, -11)
MIN_EST_OBS = 100

# Event windows for cumulative abnormal returns, in trading days relative to the event.
CAR_WINDOWS = [(0, 0), (0, 1), (0, 5), (0, 20), (-5, -1)]

# Stacked-event test of H4 (pre-specified 6 Nov 2026; docs/research_design.md section 8c).
# sign: predicted direction of AI-load news for merchant value; exclude: parties to the event.
EVENTS = [
    {"id": "pjm_bra", "date": "2024-07-30", "sign": +1, "exclude": [],
     "label": "PJM capacity auction (Jul 2024)"},
    {"id": "crane_ppa", "date": "2024-09-20", "sign": +1, "exclude": ["CEG"],
     "label": "Crane PPA (Sep 2024)"},
    {"id": "ferc_isa", "date": "2024-11-01", "sign": -1, "exclude": ["TLN"],
     "label": "FERC rejects Talen ISA (Nov 2024)"},
    {"id": "deepseek", "date": "2025-01-27", "sign": -1, "exclude": [],
     "label": "DeepSeek (Jan 2025)"},
]
STACK_WINDOW = (0, 1)
N_PLACEBO_DRAWS = 2000
PLACEBO_SEED = 20261106

# Other dated AI-electricity news, removed from the estimation window so that
# they do not inflate residual variance or bias betas. Dates verified 2026-11-05;
# check intraday timing before using them as events in their own right.
SECONDARY_EVENTS = {
    "2024-07-30": "PJM 2025/26 capacity auction clears at $269.92/MW-day",
    "2024-09-20": "Constellation-Microsoft Crane (TMI-1) restart PPA",
    "2024-11-01": "FERC rejects amended Talen-Amazon Susquehanna ISA",
    "2024-11-04": "First session after the FERC order",
}
