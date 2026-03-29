# Stock-Tracker: AI-Enhanced Financial Analysis Engine

A beginner-friendly stock tracking and analysis project focused on **US and Hong Kong markets**.

## What this template now does
- Load a watchlist from `configs/watchlist_us_hk.csv`
- Collect market/fundamental fields via Yahoo Finance (`yfinance`)
- Pull recent ticker news from Yahoo Finance feed
- Run simple rule-based sentiment + fundamental scoring
- Generate a weekly Markdown report under `reports/`

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
