from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MarketSnapshot:
    ticker: str
    current_price: float | None
    previous_close: float | None
    day_change_pct: float | None
    market_cap: float | None
    trailing_pe: float | None
    forward_pe: float | None
    revenue_growth: float | None
    debt_to_equity: float | None


class MarketCollector:
    """Collect price and basic fundamental fields from Yahoo Finance if available."""

    def fetch_snapshot(self, ticker: str) -> MarketSnapshot:
        try:
            import yfinance as yf  # type: ignore
        except ModuleNotFoundError:
            return _empty_snapshot(ticker)

        try:
            info: dict[str, Any] = yf.Ticker(ticker).info
        except Exception:
            return _empty_snapshot(ticker)

        current_price = _to_float(info.get("currentPrice"))
        previous_close = _to_float(info.get("previousClose"))

        day_change_pct = None
        if current_price is not None and previous_close not in (None, 0):
            day_change_pct = (current_price - previous_close) / previous_close * 100

        return MarketSnapshot(
            ticker=ticker,
            current_price=current_price,
            previous_close=previous_close,
            day_change_pct=day_change_pct,
            market_cap=_to_float(info.get("marketCap")),
            trailing_pe=_to_float(info.get("trailingPE")),
            forward_pe=_to_float(info.get("forwardPE")),
            revenue_growth=_to_float(info.get("revenueGrowth")),
            debt_to_equity=_to_float(info.get("debtToEquity")),
        )


def _empty_snapshot(ticker: str) -> MarketSnapshot:
    return MarketSnapshot(
        ticker=ticker,
        current_price=None,
        previous_close=None,
        day_change_pct=None,
        market_cap=None,
        trailing_pe=None,
        forward_pe=None,
        revenue_growth=None,
        debt_to_equity=None,
    )


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
