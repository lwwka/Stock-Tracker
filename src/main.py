from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

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

    dashboard_data_path = root / "data" / "processed" / "latest_snapshot.json"
    _write_dashboard_snapshot(stocks, dashboard_data_path)
    return out_file


if __name__ == "__main__":
    report_path = run()
    print(f"Report generated: {report_path}")
