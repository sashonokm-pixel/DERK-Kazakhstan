"""DERK Korean Association pilot: preliminary, read-only website article screening.

Run from repository root: python -m content_intelligence.korean_pilot
Candidate URLs and thematic signals require human review.
"""
import csv
from pathlib import Path
from urllib.parse import urlparse

from .discovery import discover_candidates
from .classifier import classify_page, FIELDS
from .derk_preliminary_coding import classify, RULES

SOURCES = ["https://koreans.kz/ru/novosti"]
OUT = Path("data/content_intelligence/korean_preliminary_review.csv")
AUDIT = Path("derk_results/korean_all_candidates.csv")


def run():
    candidates, seen = [], set()
    for source in SOURCES:
        print("Korean Association news section:", source, flush=True)
        try:
            found = discover_candidates(source, limit=100)
        except Exception as exc:
            print("Section unavailable:", str(exc), flush=True)
            continue
        for item in found:
            url = item["url"]
            parsed = urlparse(url)
            # Accept news article URLs, including possible query-based article links.
            # Other navigation links are retained only in the audit if needed later.
            if not parsed.path.lower().startswith("/ru/novosti/"):
                continue
            if url.rstrip("/") == source.rstrip("/") or url in seen:
                continue
            seen.add(url)
            candidates.append(item)
    print("Unique candidate links:", len(candidates), flush=True)
    rows = [classify_page(item) for item in candidates]
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    articles = [row for row in rows if row.get("classification") == "article"]
    coded = [classify(row, RULES["Корейцы"]) for row in articles]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = list(coded[0]) if coded else list(FIELDS) + [
        "internal_agenda_preliminary", "internal_evidence",
        "origin_agenda_preliminary", "origin_evidence",
        "state_language_preliminary", "state_language_evidence",
        "internal_agenda_verified", "origin_agenda_verified",
        "state_language_verified", "verified_article", "review_note",
    ]
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(coded)
    print(f"Korean Association: {len(candidates)} candidates; "
          f"{len(articles)} preliminary articles; output {OUT}", flush=True)
    if not articles:
        print("WARNING: No extracted articles. Check site URL patterns and audit; "
              "do not infer zero publication activity.", flush=True)


if __name__ == "__main__":
    run()

