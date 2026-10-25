"""ARSК Russian-community pilot: separate corpus, no changes to German pilot."""
import csv
from pathlib import Path
from urllib.parse import urlparse
from .discovery import discover_candidates
from .classifier import classify_page, FIELDS
from .derk_preliminary_coding import classify, RULES

SOURCES = [
    "https://arskrk.kz/novosti-arsk/novosti-arsk",
    "https://arskrk.kz/novosti-arsk/regiony",
]
OUT = Path("data/content_intelligence/russian_preliminary_review.csv")
AUDIT = Path("derk_results/russian_all_candidates.csv")

def run():
    candidates, seen = [], set()
    for source in SOURCES:
        print("ARSК section:", source, flush=True)
        try:
            found = discover_candidates(source, limit=30)
        except Exception as exc:
            print("Section unavailable:", str(exc), flush=True)
            continue
        for item in found:
            url = item["url"]
            path = urlparse(url).path.lower()
            # Avoid section index pages, PDF archives and unrelated site sections.
            if "/novosti-arsk/" not in path or url.rstrip("/") == source.rstrip("/"):
                continue
            if url in seen:
                continue
            seen.add(url)
            candidates.append(item)
    print("Unique candidate links:", len(candidates), flush=True)
    rows = [classify_page(item) for item in candidates]
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    articles = [r for r in rows if r["classification"] == "article"]
    coded = [classify(row, RULES["Русские"]) for row in articles]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = list(coded[0]) if coded else list(FIELDS) + [
        "internal_agenda_preliminary", "internal_evidence",
        "origin_agenda_preliminary", "origin_evidence",
        "state_language_preliminary", "state_language_evidence",
        "internal_agenda_verified", "origin_agenda_verified",
        "state_language_verified", "verified_article", "review_note"
    ]
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(coded)
    print(f"ARSК: {len(candidates)} candidates; {len(articles)} preliminary articles; output {OUT}", flush=True)
    if not articles:
        print("WARNING: No extracted articles. Inspect audit artifact; do not infer zero publication activity.", flush=True)

if __name__ == "__main__":
    run()
