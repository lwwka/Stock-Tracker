# Stock-Tracker：AI 強化股票分析引擎

這是一個給新手也能使用的股票追蹤與分析專案，重點市場為**美股與港股**。

## 這個模板現在可以做什麼
- 從 `configs/watchlist_us_hk.csv` 載入自選股
- 透過 Yahoo Finance（`yfinance`）抓取市場/基本面欄位
- 彙整 Yahoo Finance 的近期新聞
- 用規則式方法做新聞情緒分數與基本面分數
- 產生低耗 token 的 LLM 草稿（中英 thesis + bull/base/bear）
- 自動輸出每週 Markdown 報告到 `reports/`
- 港股 ticker 會自動補零清洗：例如 `5.HK -> 0005.HK`、`388.HK -> 0388.HK`

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


## 環境版本建議（Windows / macOS）
- 建議 Python 版本：**3.10-3.12**
- macOS 安裝：`pip install -r requirements-mac.txt`
- Windows 安裝：`pip install -r requirements-windows.txt`
- 若使用 Python 3.13+，資料來源套件可能仍會有相容性警告。


## 可選 LLM 設定（低耗 token）
- 設定 `OPENAI_API_KEY` 才會啟用 LLM 摘要。
- 可選 `OPENAI_MODEL`（預設：`gpt-4o-mini`）。
- 內建節流策略：
  - 只送 title + 前 500 字
  - 兩段式摘要流程
  - cache 去重（`data/processed/llm_news_cache.json`）
  - 最終輸出欄位長度限制

範例：
```bash
export OPENAI_API_KEY=your_key
export OPENAI_MODEL=gpt-4o-mini
python -m src.main
```


## Dashboard
1. 先產生/更新資料快照：
```bash
python -m src.main
```
2. 啟動 dashboard：
```bash
streamlit run src/dashboard/app.py
```
Dashboard 會讀取 `data/processed/latest_snapshot.json` 顯示圖表與表格。
