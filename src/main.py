from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.analyzers.fundamental_analyzer import FundamentalAnalyzer
from src.analyzers.sentiment_analyzer import SentimentAnalyzer
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
    report_generator = ReportGenerator()

    stocks: list[StockReportInput] = []
    for item in watchlist:
        snapshot = market_collector.fetch_snapshot(item.ticker)
        news = news_collector.fetch_recent_news(item.ticker)
        sentiment = sentiment_analyzer.analyze(news)
        fundamental = fundamental_analyzer.analyze(snapshot)

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
            )
        )

    content = report_generator.build_markdown(stocks)
    out_file = output_dir / f"weekly_report_{datetime.now(timezone.utc):%Y%m%d}.md"
    out_file.write_text(content, encoding="utf-8")
    return out_file


if __name__ == "__main__":
    report_path = run()
    print(f"Report generated: {report_path}")
