# Stock-Tracker：AI 強化股票分析引擎

這是一個給新手也能使用的股票追蹤與分析專案，重點市場為**美股與港股**。

## 這個模板現在可以做什麼
- 從 `configs/watchlist_us_hk.csv` 載入自選股
- 透過 Yahoo Finance（`yfinance`）抓取市場/基本面欄位
- 彙整 Yahoo Finance 的近期新聞
- 用規則式方法做新聞情緒分數與基本面分數
- 自動輸出每週 Markdown 報告到 `reports/`

## 快速開始
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

輸出檔案範例：
- `reports/weekly_report_YYYYMMDD.md`

## 重要提醒
本專案僅供學習與研究流程用途，**不構成投資建議**。


## CSV 填寫建議（讓你更快產報告）
- 一列一家公司，固定四欄：`ticker,name,market,thesis`
- thesis 建議固定公式：`Driver + Moat; validate: KPI; risk: 風險`
- thesis 若包含逗號 `,`，請用雙引號包起來
- 先從 8-12 檔開始，避免追蹤過載
