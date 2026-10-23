"""DERK: conservative article classification and auditable CSV corpus.

Replace content_intelligence/classifier.py with this file. Read-only: no DB writes.
"""
from __future__ import annotations

import csv
import re
from datetime import date
from pathlib import Path

from .collector import collect_article
from .discovery import discover_candidates

MIN_ARTICLE_WORDS = 80
MIN_SHORT_NEWS_WORDS = 40
FIELDS = ["url", "title_hint", "review_group", "classification", "title", "date",
          "author", "language", "word_count", "text", "reason"]


def detect_language(text: str) -> str:
    """Language identification is provisional; do not force a label on short text."""
    if len(text.strip()) < 100:
        return ""
    try:
        from langdetect import DetectorFactory, detect_langs
        DetectorFactory.seed = 0
        predictions = detect_langs(text[:10000])
        if predictions and predictions[0].prob >= 0.85:
            return predictions[0].lang
    except Exception:
        pass
    return ""


def _valid_date(value: str) -> bool:
    try:
        date.fromisoformat(value[:10])
        return True
    except (ValueError, TypeError):
        return False


def classify_page(candidate: dict) -> dict:
    """Classify a page, preserving text and reason even if excluded."""
    row = {key: "" for key in FIELDS}
    row.update(url=candidate["url"], title_hint=candidate.get("title_hint", ""),
               review_group=candidate.get("review_group", ""),
               classification="needs_review", word_count=0)
    try:
        article = collect_article(candidate["url"])
    except Exception as exc:
        row["reason"] = f"Не удалось извлечь материал: {exc}"
        return row

    row.update({key: article.get(key, "") or "" for key in
                ("title", "date", "author", "language", "text")})
    row["word_count"] = len(re.findall(r"\b[\w-]+\b", row["text"], flags=re.UNICODE))
    if not row["language"]:
        row["language"] = detect_language(row["text"])

    if row["review_group"] == "navigation_review":
        row["classification"] = "service_page"
        row["reason"] = "Навигационная страница: исключена из корпуса, сохранена в журнале"
    elif row["title"] and row["word_count"] >= MIN_ARTICLE_WORDS:
        row["classification"] = "article"
        row["reason"] = "Заголовок и достаточный объём текста"
    elif (row["title"] and MIN_SHORT_NEWS_WORDS <= row["word_count"] < MIN_ARTICLE_WORDS
          and _valid_date(row["date"])):
        row["classification"] = "article"
        row["reason"] = "Короткая новость: заголовок, дата и текст"
    else:
        row["reason"] = "Требуется ручная проверка признаков публикации"
    return row


def build_corpus(source_url: str, limit: int = 40, output_dir: str = "derk_results",
                 date_from: str | None = None, date_to: str | None = None) -> dict:
    """Collect candidates; optionally restrict the corpus to ISO date range.

    Out-of-range or undated articles remain in the audit CSV, never silently lost.
    """
    for bound in (date_from, date_to):
        if bound:
            date.fromisoformat(bound)
    if date_from and date_to and date_from > date_to:
        raise ValueError("date_from не может быть позже date_to")

    rows = [classify_page(item) for item in discover_candidates(source_url, limit=limit)]
    for row in rows:
        if row["classification"] != "article" or not (date_from or date_to):
            continue
        published = row["date"][:10]
        if not _valid_date(published):
            row["classification"] = "needs_review"
            row["reason"] = "Дата не определена: проверить перед включением в период"
        elif (date_from and published < date_from) or (date_to and published > date_to):
            row["classification"] = "outside_period"
            row["reason"] = "Публикация вне заданного исследовательского периода"

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    for filename, records in (
        ("all_candidates.csv", rows),
        ("article_corpus.csv", [row for row in rows if row["classification"] == "article"]),
    ):
        with (destination / filename).open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(records)

    return {"found": len(rows), "articles": sum(r["classification"] == "article" for r in rows),
            "service_pages": sum(r["classification"] == "service_page" for r in rows),
            "needs_review": sum(r["classification"] == "needs_review" for r in rows),
            "outside_period": sum(r["classification"] == "outside_period" for r in rows),
            "output_dir": str(destination)}

