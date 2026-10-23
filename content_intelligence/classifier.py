"""DERK: classify discovered links using the existing article collector.

Read-only: no database writes. Every candidate remains in the audit CSV.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

from .collector import collect_article
from .discovery import discover_candidates

MIN_WORDS = 80


def classify_page(candidate: dict) -> dict:
    """Return an auditable classification, retaining the original candidate."""
    row = {
        "url": candidate["url"],
        "title_hint": candidate.get("title_hint", ""),
        "review_group": candidate.get("review_group", ""),
        "classification": "needs_review",
        "title": "", "date": "", "author": "", "language": "",
        "word_count": 0, "text": "", "reason": "",
    }
    try:
        article = collect_article(candidate["url"])
    except Exception as exc:
        row["reason"] = f"Не удалось подтвердить публикацию: {exc}"
        return row

    row.update({key: article.get(key, "") for key in ("title", "date", "author", "language", "text")})
    row["word_count"] = len(re.findall(r"\b[\w-]+\b", row["text"], flags=re.UNICODE))
    if candidate.get("review_group") == "navigation_review":
        row["classification"] = "service_page"
        row["reason"] = "Навигационный URL или заголовок; текст сохранён для проверки"
    elif row["word_count"] >= MIN_WORDS and row["title"]:
        row["classification"] = "article"
        row["reason"] = "Извлечены заголовок и содержательный текст"
    else:
        row["reason"] = "Недостаточно признаков для автоматического подтверждения статьи"
    return row


def build_corpus(source_url: str, limit: int = 40, output_dir: str = "derk_results") -> dict:
    """Create article corpus and full review log from an approved website."""
    candidates = discover_candidates(source_url, limit=limit)
    rows = [classify_page(item) for item in candidates]
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    fields = ["url", "title_hint", "review_group", "classification", "title", "date",
              "author", "language", "word_count", "text", "reason"]
    for filename, records in (
        ("all_candidates.csv", rows),
        ("article_corpus.csv", [row for row in rows if row["classification"] == "article"]),
    ):
        with (destination / filename).open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerows(records)
    return {
        "found": len(rows),
        "articles": sum(row["classification"] == "article" for row in rows),
        "service_pages": sum(row["classification"] == "service_page" for row in rows),
        "needs_review": sum(row["classification"] == "needs_review" for row in rows),
        "output_dir": str(destination),
    }
