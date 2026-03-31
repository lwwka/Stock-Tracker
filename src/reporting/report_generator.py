from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from src.analyzers.fundamental_analyzer import FundamentalResult
from src.analyzers.sentiment_analyzer import SentimentResult
from src.collectors.market_collector import MarketSnapshot
from src.collectors.news_collector import NewsItem


@dataclass
class StockReportInput:
    ticker: str
    name: str
    market: str
    thesis: str
    snapshot: MarketSnapshot
    sentiment: SentimentResult
    fundamental: FundamentalResult
    news: list[NewsItem]


class ReportGenerator:
    def build_markdown(self, stocks: list[StockReportInput]) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            "# Weekly Stock Tracker Report",
            f"Generated at: {now}",
            "",
            "> For educational use only. Not investment advice.",
            "",
        ]

        for stock in stocks:
            lines.extend(
                [
                    f"## {stock.ticker} - {stock.name} ({stock.market})",
                    f"- Thesis / 追蹤假設: {stock.thesis}",
                    f"- Price: {_fmt(stock.snapshot.current_price)}",
                    f"- Day Change: {_fmt_pct(stock.snapshot.day_change_pct)}",
                    f"- Market Cap: {_fmt(stock.snapshot.market_cap)}",
                    f"- Fundamental Score: {stock.fundamental.score}/5 ({stock.fundamental.label})",
                    f"- Sentiment: {stock.sentiment.label} (score={stock.sentiment.score}, +{stock.sentiment.positive_hits}/-{stock.sentiment.negative_hits})",
                    "",
                    "### Fundamental Notes",
                    *[f"- {reason}" for reason in stock.fundamental.reasons],
                    "",
                    "### Top News",
                ]
            )

            if stock.news:
                for item in stock.news[:3]:
                    published = item.published_at.strftime("%Y-%m-%d") if item.published_at else "N/A"
                    lines.append(f"- [{published}] {item.title} ({item.publisher})")
            else:
                lines.append("- No recent news found.")

            lines.append("")

        return "\n".join(lines)


def _fmt(value: float | None) -> str:
    if value is None:
        return "N/A"
    if value > 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if value > 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    return f"{value:.2f}"


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.2f}%"
