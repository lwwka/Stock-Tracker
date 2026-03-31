from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from src.collectors.news_collector import NewsItem


@dataclass
class LLMAnalysisResult:
    used_llm: bool
    short_summaries: list[str]
    thesis_en: str
    thesis_zh: str
    bull_case: str
    base_case: str
    bear_case: str


class LLMAnalyzer:
    """Low-token LLM pipeline with truncation, filtering, 2-stage summarize, and cache dedupe."""

    def __init__(self, cache_path: Path | None = None) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
        self.cache_path = cache_path or Path("data/processed/llm_news_cache.json")
        self.cache = self._load_cache()

    def analyze_stock(
        self,
        ticker: str,
        company_name: str,
        thesis_hint: str,
        news_items: list[NewsItem],
    ) -> LLMAnalysisResult:
        filtered = _filter_relevant_news(news_items, ticker, company_name)
        if not filtered:
            return _fallback_result(thesis_hint)

        # only process new items (cache dedupe)
        prepared = [_prepare_news_text(item) for item in filtered]
        new_entries = [entry for entry in prepared if entry["hash"] not in self.cache]

        if new_entries and self.api_key:
            summaries = [self._stage1_micro_summary(entry["text"]) for entry in new_entries]
            for entry, summary in zip(new_entries, summaries):
                self.cache[entry["hash"]] = summary
            self._save_cache()

        cached_summaries = [self.cache.get(entry["hash"], entry["text"][:120]) for entry in prepared]
        compact_summaries = [s[:220] for s in cached_summaries[:6]]

        if self.api_key:
            final = self._stage2_scenario(company_name, ticker, thesis_hint, compact_summaries)
            if final:
                return final

        # fallback when no API or API failed
        joined = " | ".join(compact_summaries[:3])[:320]
        return LLMAnalysisResult(
            used_llm=False,
            short_summaries=compact_summaries[:3],
            thesis_en=(thesis_hint or "No thesis provided")[:240],
            thesis_zh=f"初步觀點：{(thesis_hint or '未提供 thesis')[:120]}",
            bull_case=f"If momentum stays strong: {joined}",
            base_case="Mixed signals, monitor revenue/margin trend and risk headlines.",
            bear_case="If negative headlines continue and guidance weakens, reduce conviction.",
        )

    def _stage1_micro_summary(self, text: str) -> str:
        prompt = (
            "Summarize this stock news in <=30 words, factual only, one sentence. "
            "Output plain text only.\n\n"
            f"{text}"
        )
        result = self._call_llm(prompt, max_tokens=80)
        if result:
            return result.strip()[:220]
        return text[:160]

    def _stage2_scenario(
        self,
        company_name: str,
        ticker: str,
        thesis_hint: str,
        summaries: list[str],
    ) -> LLMAnalysisResult | None:
        joined = "\n".join(f"- {s}" for s in summaries[:6])
        prompt = (
            "You are a financial research assistant. Based on the short summaries, produce concise drafts. "
            "Return strict JSON with keys: thesis_en, thesis_zh, bull_case, base_case, bear_case. "
            "Keep each field short. Total response should be brief.\n\n"
            f"Company: {company_name} ({ticker})\n"
            f"User thesis hint: {thesis_hint}\n"
            f"News summaries:\n{joined}\n"
        )
        raw = self._call_llm(prompt, max_tokens=250)
        if not raw:
            return None

        data = _safe_json_loads(raw)
        if not data:
            return None

        return LLMAnalysisResult(
            used_llm=True,
            short_summaries=summaries[:6],
            thesis_en=str(data.get("thesis_en", ""))[:250],
            thesis_zh=str(data.get("thesis_zh", ""))[:250],
            bull_case=str(data.get("bull_case", ""))[:250],
            base_case=str(data.get("base_case", ""))[:250],
            bear_case=str(data.get("bear_case", ""))[:250],
        )

    def _call_llm(self, prompt: str, max_tokens: int) -> str | None:
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are concise and return requested format only."},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.2,
            }
            req = Request(
                url="https://api.openai.com/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                method="POST",
            )
            with urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError, URLError, TimeoutError):
            return None

    def _load_cache(self) -> dict[str, str]:
        try:
            if self.cache_path.exists():
                return json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            pass
        return {}

    def _save_cache(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.cache, ensure_ascii=False, indent=2), encoding="utf-8")


def _prepare_news_text(item: NewsItem) -> dict[str, str]:
    text = f"{item.title.strip()}\n{(item.summary or '').strip()[:500]}".strip()
    digest = hashlib.sha1(f"{item.title}|{item.link}|{item.summary}".encode("utf-8")).hexdigest()
    return {"hash": digest, "text": text}


def _filter_relevant_news(news_items: list[NewsItem], ticker: str, company_name: str) -> list[NewsItem]:
    keys = {
        ticker.lower(),
        ticker.split(".")[0].lower(),
        company_name.lower().split(" ")[0],
        "earnings",
        "guidance",
        "margin",
        "revenue",
        "lawsuit",
        "regulation",
        "acquisition",
        "ai",
    }

    results: list[NewsItem] = []
    for item in news_items:
        text = f"{item.title} {item.summary}".lower()
        if any(k and k in text for k in keys):
            results.append(item)
    return results[:8]


def _safe_json_loads(raw: str) -> dict[str, Any] | None:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    try:
        return json.loads(text)
    except ValueError:
        return None


def _fallback_result(thesis_hint: str) -> LLMAnalysisResult:
    return LLMAnalysisResult(
        used_llm=False,
        short_summaries=[],
        thesis_en=(thesis_hint or "No thesis available")[:240],
        thesis_zh=f"初步觀點：{(thesis_hint or '未提供 thesis')[:120]}",
        bull_case="Bull: if growth and margin trend improve with supportive news flow.",
        base_case="Base: mixed signals; keep tracking execution and demand.",
        bear_case="Bear: recurring negative headlines + weak fundamentals.",
    )
