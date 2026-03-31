from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class NewsItem:
    title: str
    publisher: str
    published_at: datetime | None
    summary: str
    link: str


class NewsCollector:
    """Collect recent company news from Yahoo Finance ticker feed if available."""

    def fetch_recent_news(self, ticker: str, limit: int = 8) -> list[NewsItem]:
        try:
            import yfinance as yf  # type: ignore
        except ModuleNotFoundError:
            return []

        try:
            raw_items: list[dict[str, Any]] = yf.Ticker(ticker).news or []
        except Exception:
            return []

        results: list[NewsItem] = []
        for item in raw_items[:limit]:
            content = item.get("content", {}) if isinstance(item, dict) else {}
            published_ts = content.get("pubDate") or item.get("providerPublishTime")

            published_at = None
            if isinstance(published_ts, (int, float)):
                published_at = datetime.fromtimestamp(published_ts, tz=timezone.utc)

            results.append(
                NewsItem(
                    title=(content.get("title") or item.get("title") or "").strip(),
                    publisher=(content.get("provider", {}).get("displayName") or item.get("publisher") or "Unknown").strip(),
                    published_at=published_at,
                    summary=(content.get("summary") or "").strip(),
                    link=content.get("canonicalUrl", {}).get("url") or item.get("link") or "",
                )
            )
        return results
