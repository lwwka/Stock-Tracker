from __future__ import annotations

from dataclasses import dataclass

from src.collectors.news_collector import NewsItem


POSITIVE_WORDS = {
    "beat",
    "growth",
    "upgrade",
    "strong",
    "record",
    "expansion",
    "profit",
    "surge",
    "partnership",
    "improve",
    "上調",
    "成長",
    "創新高",
    "擴張",
    "利潤",
}

NEGATIVE_WORDS = {
    "miss",
    "downgrade",
    "lawsuit",
    "weak",
    "decline",
    "risk",
    "cut",
    "delay",
    "loss",
    "investigation",
    "下調",
    "衰退",
    "虧損",
    "風險",
    "調查",
}


@dataclass
class SentimentResult:
    score: float
    label: str
    positive_hits: int
    negative_hits: int


class SentimentAnalyzer:
    def analyze(self, news_items: list[NewsItem]) -> SentimentResult:
        positive_hits = 0
        negative_hits = 0

        for item in news_items:
            text = f"{item.title} {item.summary}".lower()
            positive_hits += sum(1 for word in POSITIVE_WORDS if word in text)
            negative_hits += sum(1 for word in NEGATIVE_WORDS if word in text)

        total_hits = positive_hits + negative_hits
        score = 0.0 if total_hits == 0 else (positive_hits - negative_hits) / total_hits

        if score > 0.2:
            label = "Positive"
        elif score < -0.2:
            label = "Negative"
        else:
            label = "Neutral"

        return SentimentResult(
            score=round(score, 3),
            label=label,
            positive_hits=positive_hits,
            negative_hits=negative_hits,
        )
