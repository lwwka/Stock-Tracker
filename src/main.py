from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.analyzers.fundamental_analyzer import FundamentalAnalyzer
from src.analyzers.sentiment_analyzer import SentimentAnalyzer
from src.analyzers.llm_analyzer import LLMAnalyzer
from src.collectors.market_collector import MarketCollector
from src.collectors.news_collector import NewsCollector
from src.reporting.report_generator import ReportGenerator, StockReportInput


@dataclass
class WatchItem:
    ticker: str
    name: str
    market: str
    thesis: str


def load_watchlist(path: Path) -> list[WatchItem]:
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [
            WatchItem(
                ticker=_normalize_ticker(row["ticker"].strip()),
                name=row["name"].strip(),
                market=row.get("market", "").strip(),
                thesis=row.get("thesis", "").strip(),
            )
            for row in reader
            if row.get("ticker") and row.get("name")
        ]


def _normalize_ticker(raw_ticker: str) -> str:
    """Normalize ticker symbols for known market formats.

    Example: 5.HK -> 0005.HK, 388.HK -> 0388.HK
    """
    ticker = raw_ticker.strip().upper()

    if ticker.endswith(".HK"):
        code = ticker[:-3]
        if code.isdigit() and 1 <= len(code) <= 4:
            return f"{int(code):04d}.HK"

    return ticker



def _write_dashboard_snapshot(stocks: list[StockReportInput], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for stock in stocks:
        rows.append({
            "ticker": stock.ticker,
            "name": stock.name,
            "market": stock.market,
            "price": stock.snapshot.current_price,
            "day_change_pct": stock.snapshot.day_change_pct,
            "market_cap": stock.snapshot.market_cap,
            "fundamental_score": stock.fundamental.score,
            "fundamental_label": stock.fundamental.label,
            "sentiment_score": stock.sentiment.score,
            "sentiment_label": stock.sentiment.label,
            "llm_used": stock.llm.used_llm,
            "thesis_en": stock.llm.thesis_en,
            "thesis_zh": stock.llm.thesis_zh,
            "bull_case": stock.llm.bull_case,
            "base_case": stock.llm.base_case,
            "bear_case": stock.llm.bear_case,
        })

    output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")



def _append_snapshot_history(stocks: list[StockReportInput], output_path: Path) -> None:
    """Append today's cross-sectional snapshot into history parquet."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    today = datetime.now(timezone.utc).date().isoformat()
    rows = []
    for stock in stocks:
        rows.append({
            "date": today,
            "ticker": stock.ticker,
            "name": stock.name,
            "market": stock.market,
            "price": stock.snapshot.current_price,
            "day_change_pct": stock.snapshot.day_change_pct,
            "fundamental_score": stock.fundamental.score,
            "sentiment_score": stock.sentiment.score,
            "llm_used": stock.llm.used_llm,
        })

    new_df = pd.DataFrame(rows)

    if output_path.exists():
        old_df = pd.read_parquet(output_path)
        combined = pd.concat([old_df, new_df], ignore_index=True)
        # keep latest record per (date, ticker) in case run multiple times a day
        combined = combined.drop_duplicates(subset=["date", "ticker"], keep="last")
    else:
        combined = new_df

    combined = combined.sort_values(["date", "ticker"]).reset_index(drop=True)
    try:
        combined.to_parquet(output_path, index=False)
    except Exception:
        # parquet engine may be unavailable; keep a CSV fallback for continuity
        output_path.with_suffix(".csv").write_text(combined.to_csv(index=False), encoding="utf-8")



def run() -> Path:
    root = Path(__file__).resolve().parents[1]
    watchlist_path = root / "configs" / "watchlist_us_hk.csv"
    output_dir = root / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    watchlist = load_watchlist(watchlist_path)

    market_collector = MarketCollector()
    news_collector = NewsCollector()
    sentiment_analyzer = SentimentAnalyzer()
    fundamental_analyzer = FundamentalAnalyzer()
    llm_analyzer = LLMAnalyzer(cache_path=root / "data" / "processed" / "llm_news_cache.json")
    report_generator = ReportGenerator()

    stocks: list[StockReportInput] = []
    for item in watchlist:
        snapshot = market_collector.fetch_snapshot(item.ticker)
        news = news_collector.fetch_recent_news(item.ticker)
        sentiment = sentiment_analyzer.analyze(news)
        fundamental = fundamental_analyzer.analyze(snapshot)
        llm_result = llm_analyzer.analyze_stock(item.ticker, item.name, item.thesis, news)

        stocks.append(
            StockReportInput(
                ticker=item.ticker,
                name=item.name,
                market=item.market,
                thesis=item.thesis,
                snapshot=snapshot,
                sentiment=sentiment,
                fundamental=fundamental,
                news=news,
                llm=llm_result,
            )
        )

    content = report_generator.build_markdown(stocks)
    out_file = output_dir / f"weekly_report_{datetime.now(timezone.utc):%Y%m%d}.md"
    out_file.write_text(content, encoding="utf-8")

    data_dir = root / "data" / "processed"
    dashboard_data_path = data_dir / "latest_snapshot.json"
    history_parquet_path = data_dir / "snapshot_history.parquet"

    _write_dashboard_snapshot(stocks, dashboard_data_path)
    _append_snapshot_history(stocks, history_parquet_path)
    return out_file


if __name__ == "__main__":
    report_path = run()
    print(f"Report generated: {report_path}")
