"""Rebuild every table and figure: python run_all.py (from the repository root).

Figures need R (>= 4.3) with tidyplots, ggdist, distributional, dplyr, readr, tidyr.
Set RSCRIPT to the Rscript path if it is not on PATH.
"""
import os
import runpy
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CODE = ROOT / "code"
sys.path.insert(0, str(CODE))

for script in ["01_download_prices.py", "02_build_exposure.py", "03_event_study.py",
               "04_stacked_events.py", "05_ai_beta.py"]:
    print(f"== {script}")
    runpy.run_path(str(CODE / script), run_name="__main__")

rscript = os.environ.get("RSCRIPT") or shutil.which("Rscript")
if rscript:
    print("== 06_figures.R")
    subprocess.run([rscript, str(CODE / "06_figures.R")], cwd=ROOT, check=True)
else:
    print("Rscript not found: set RSCRIPT to build figures (code/06_figures.R)")
