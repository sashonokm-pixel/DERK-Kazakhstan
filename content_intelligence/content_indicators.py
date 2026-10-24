
"""DERK Content Intelligence — three research indicators.

Input: derk_results/article_corpus.csv
Output: derk_results/content_review.csv
        derk_results/content_summary.csv

No database writes. Human verification is required.
"""

import csv
from pathlib import Path

SOURCE = Path("derk_results/article_corpus.csv")
REVIEW = Path("derk_results/content_review.csv")
SUMMARY = Path("derk_results/content_summary.csv")

HOMELAND = "Germany"

def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def prepare_review():
    """Preserve existing human labels when regenerating the review."""
    existing = {}
    if REVIEW.exists():
        existing = {
            row["url"]: row for row in read_csv(REVIEW)
        }

    rows = []
    for article in read_csv(SOURCE):
        url = article.get("url", "")
        old = existing.get(url, {})

        rows.append({
            "url": url,
            "title": article.get("title", ""),
            "date": article.get("date", ""),
            "language": article.get("language", ""),
            "text": article.get("text", ""),
            "kazakhstan_related": old.get("kazakhstan_related", ""),
            "homeland_related": old.get("homeland_related", ""),
            "verified_article": old.get("verified_article", ""),
        })

    fields = [
        "url", "title", "date", "language", "text",
        "kazakhstan_related", "homeland_related",
        "verified_article"
    ]
    write_csv(REVIEW, rows, fields)
    return rows

def calculate(rows):
    """Only verified articles with complete labels are analysed."""
    valid = []
    for row in rows:
        labels = [
            row.get("verified_article", "").strip().lower(),
            row.get("kazakhstan_related", "").strip().lower(),
            row.get("homeland_related", "").strip().lower(),
        ]
        if all(label in ("yes", "no") for label in labels):
            if labels[0] == "yes":
                valid.append(row)

    total = len(valid)
    if not total:
        return {
            "articles": 0,
            "kazakhstan_percent": "",
            "homeland_percent": "",
            "kazakh_language": "not_assessed",
        }

    kaz = sum(
        r["kazakhstan_related"].strip().lower() == "yes"
        for r in valid
    )
    homeland = sum(
        r["homeland_related"].strip().lower() == "yes"
        for r in valid
    )
    kazakh = any(
        r.get("language", "").strip().lower() == "kk"
        for r in valid
    )

    return {
        "articles": total,
        "kazakhstan_percent": round(100 * kaz / total, 1),
        "homeland_percent": round(100 * homeland / total, 1),
        "kazakh_language": "yes" if kazakh else "no_in_sample",
    }

def main():
    rows = prepare_review()
    result = calculate(rows)
    result["historical_homeland"] = HOMELAND

    write_csv(SUMMARY, [result], list(result.keys()))

    print("DERK Content Intelligence")
    print("Articles awaiting review:", len(rows))
    print("Verified results:", result)
    print("Review file:", REVIEW)
    print("Summary file:", SUMMARY)

if __name__ == "__main__":
    main()

