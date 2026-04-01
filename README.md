# Stock-Tracker: AI-Enhanced Financial Analysis Engine

A beginner-friendly stock tracking and analysis project focused on **US and Hong Kong markets**.

## What this template now does
- Load a watchlist from `configs/watchlist_us_hk.csv`
- Collect market/fundamental fields via Yahoo Finance (`yfinance`)
- Pull recent ticker news from Yahoo Finance feed
- Run simple rule-based sentiment + fundamental scoring
- Generate token-optimized LLM drafts (EN/中文 thesis + bull/base/bear)
- Generate a weekly Markdown report under `reports/`
- HK tickers are auto-normalized: `5.HK -> 0005.HK`, `388.HK -> 0388.HK`

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

Generated output example:
- `reports/weekly_report_YYYYMMDD.md`

## Important disclaimer
This repository is for educational research workflow only and **not investment advice**.


## Environment notes (Windows / macOS)
- Recommended Python: **3.10-3.12**
- macOS install: `pip install -r requirements-mac.txt`
- Windows install: `pip install -r requirements-windows.txt`
- If using Python 3.13+, some upstream warnings may appear from data provider libraries.


## Optional LLM setup (token-optimized)
- Set `OPENAI_API_KEY` to enable LLM summarization.
- Optional `OPENAI_MODEL` (default: `gpt-4o-mini`).
- Cost controls included:
  - title + first 500 chars only
  - 2-stage summarization
  - cache dedupe (`data/processed/llm_news_cache.json`)
  - capped final output fields

Example:
```bash
export OPENAI_API_KEY=your_key
export OPENAI_MODEL=gpt-4o-mini
python -m src.main
```


## Dashboard
1. Generate/update data snapshot:
```bash
python -m src.main
```
2. Launch dashboard:
```bash
streamlit run src/dashboard/app.py
```
The dashboard reads `data/processed/latest_snapshot.json` and shows charts/tables.
It also appends history to `data/processed/snapshot_history.parquet` and renders a signal backtest equity curve (CAGR/Sharpe/Max Drawdown).


## Startup & Testing Commands

### Startup (pipeline + dashboard)
```bash
# 1) Activate venv
source .venv/bin/activate

# 2) Run pipeline (generate markdown report + snapshot JSON)
python -m src.main

# 3) Start dashboard
streamlit run src/dashboard/app.py
```

### Basic checks
```bash
# Compile check
python -m compileall src

# Pipeline smoke test
python -m src.main

# Verify dashboard snapshot exists
python - <<'PY'
from pathlib import Path
p = Path('data/processed/latest_snapshot.json')
print('snapshot_exists=', p.exists(), 'path=', p)
PY
```

### Windows PowerShell startup
```powershell
# 1) Activate venv
.venv\Scripts\Activate.ps1

# 2) Run pipeline
python -m src.main

# 3) Start dashboard
streamlit run src/dashboard/app.py
```
