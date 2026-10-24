
"""DERK Content Intelligence: three research indicators.

Analyses a manually verified article corpus.
Read-only: does not change the database or source files.
"""

import csv
from pathlib import Path


def analyse_articles(articles, homeland, kazakh_language="kk"):
    """Calculate indicators from manually coded article records."""
    articles = list(articles)
    total = len(articles)

    if total == 0:
        return {
            "total_articles": 0,
            "kazakhstan_percent": None,
            "homeland_percent": None,
            "kazakh_content": None,
        }

    kazakhstan_count = sum(
        1 for article in articles
        if str(article["kazakhstan_related"]).strip().lower() == "yes"
    )

    homeland_count = sum(
        1 for article in articles
        if str(article["homeland_related"]).strip().lower() == "yes"
    )

    kazakh_content = any(
        str(article["language"]).strip().lower() == kazakh_language
        for article in articles
    )

    return {
        "total_articles": total,
        "homeland": homeland,
        "kazakhstan_percent": round(kazakhstan_count / total * 100, 1),
        "homeland_percent": round(homeland_count / total * 100, 1),
        "kazakh_content": kazakh_content,
    }


def load_verified_corpus(filename):
    """Read a manually reviewed CSV with the required coding fields."""
    required = {
        "kazakhstan_related",
        "homeland_related",
        "language",
    }

    with Path(filename).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        missing = required - set(reader.fieldnames or [])

        if missing:
            raise ValueError(
                "Missing research columns: " + ", ".join(sorted(missing))
            )

        articles = list(reader)

    for number, article in enumerate(articles, start=2):
        for field in ("kazakhstan_related", "homeland_related"):
            if str(article[field]).strip().lower() not in ("yes", "no"):
                raise ValueError(
                    f"Row {number}: {field} must be yes or no"
                )

    return articles
