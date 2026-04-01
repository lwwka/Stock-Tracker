from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.backtesting.metrics import run_signal_backtest


st.set_page_config(page_title="Stock-Tracker Dashboard", layout="wide")

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_PATH = ROOT / "data" / "processed" / "latest_snapshot.json"
HISTORY_PATH = ROOT / "data" / "processed" / "snapshot_history.parquet"

st.title("📊 Stock-Tracker Dashboard")
st.caption("Data source: data/processed/latest_snapshot.json")

if not SNAPSHOT_PATH.exists():
    st.warning("No snapshot found. Run `python -m src.main` first.")
    st.stop()

rows = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
df = pd.DataFrame(rows)
if df.empty:
    st.warning("Snapshot is empty.")
    st.stop()

market_filter = st.multiselect("Market", sorted(df["market"].dropna().unique().tolist()), default=sorted(df["market"].dropna().unique().tolist()))
filtered = df[df["market"].isin(market_filter)].copy()

col1, col2, col3 = st.columns(3)
col1.metric("Stocks", len(filtered))
col2.metric("Avg Fundamental Score", f"{filtered['fundamental_score'].mean():.2f}" if len(filtered) else "N/A")
col3.metric("Avg Sentiment Score", f"{filtered['sentiment_score'].mean():.2f}" if len(filtered) else "N/A")

st.subheader("Fundamental score by ticker")
fig_f = px.bar(
    filtered.sort_values("fundamental_score", ascending=False),
    x="ticker",
    y="fundamental_score",
    color="market",
    hover_data=["name", "fundamental_label"],
)
st.plotly_chart(fig_f, use_container_width=True)

st.subheader("Sentiment score scatter")
fig_s = px.scatter(
    filtered,
    x="sentiment_score",
    y="fundamental_score",
    color="market",
    hover_name="ticker",
    hover_data=["name", "price", "day_change_pct"],
)
st.plotly_chart(fig_s, use_container_width=True)

st.subheader("Watchlist table")
show_cols = [
    "ticker",
    "name",
    "market",
    "price",
    "day_change_pct",
    "fundamental_score",
    "fundamental_label",
    "sentiment_score",
    "sentiment_label",
    "llm_used",
]
st.dataframe(filtered[show_cols], use_container_width=True)

st.subheader("LLM draft details")
ticker = st.selectbox("Ticker", filtered["ticker"].tolist())
row = filtered[filtered["ticker"] == ticker].iloc[0]
st.markdown(f"**Thesis EN:** {row['thesis_en']}")
st.markdown(f"**Thesis 中文:** {row['thesis_zh']}")
st.markdown(f"**Bull:** {row['bull_case']}")
st.markdown(f"**Base:** {row['base_case']}")
st.markdown(f"**Bear:** {row['bear_case']}")


st.subheader("Strategy Backtest (Signal-based)")
backtest = run_signal_backtest(HISTORY_PATH)
if backtest is None:
    st.info("Not enough history for backtest yet. Keep running `python -m src.main` daily.")
else:
    b1, b2, b3 = st.columns(3)
    b1.metric("CAGR", f"{backtest.cagr * 100:.2f}%")
    b2.metric("Sharpe", f"{backtest.sharpe:.2f}")
    b3.metric("Max Drawdown", f"{backtest.max_drawdown * 100:.2f}%")

    eq = backtest.equity_curve.copy()
    fig_eq = px.line(eq, x="date", y="equity", title="Equity Curve")
    st.plotly_chart(fig_eq, use_container_width=True)

