from __future__ import annotations

from dataclasses import dataclass

from src.collectors.market_collector import MarketSnapshot


@dataclass
class FundamentalResult:
    score: int
    label: str
    reasons: list[str]


class FundamentalAnalyzer:
    """Simple beginner-friendly rule-based quality scoring (0-5)."""

    def analyze(self, snapshot: MarketSnapshot) -> FundamentalResult:
        score = 0
        reasons: list[str] = []

        if snapshot.revenue_growth is not None:
            if snapshot.revenue_growth > 0.1:
                score += 2
                reasons.append("Revenue growth is healthy (>10%).")
            elif snapshot.revenue_growth > 0:
                score += 1
                reasons.append("Revenue is still growing.")
            else:
                reasons.append("Revenue growth is weak or negative.")
        else:
            reasons.append("Revenue growth data unavailable.")

        if snapshot.trailing_pe is not None:
            if snapshot.trailing_pe < 25:
                score += 1
                reasons.append("Valuation is not stretched (P/E < 25).")
            else:
                reasons.append("Valuation may be expensive (high P/E).")

        if snapshot.debt_to_equity is not None:
            if snapshot.debt_to_equity < 100:
                score += 2
                reasons.append("Balance sheet leverage is manageable.")
            else:
                reasons.append("Leverage appears elevated.")
        else:
            reasons.append("Debt/equity data unavailable.")

        if score >= 4:
            label = "Strong"
        elif score >= 2:
            label = "Watch"
        else:
            label = "Caution"

        return FundamentalResult(score=score, label=label, reasons=reasons)
