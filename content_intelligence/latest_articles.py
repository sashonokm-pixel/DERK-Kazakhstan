"""DERK pilot: collect dated candidate articles from a public news archive.

Run: python content_intelligence/latest_articles.py
Requires: requests, beautifulsoup4, trafilatura.
Output is a REVIEW LIST, not a validated research corpus.
"""
from __future__ import annotations

import csv
import re
import time
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup
import trafilatura
from trafilatura.metadata import extract_metadata

from content_intelligence.collector import validate_public_url

ARCHIVE = "https://wiedergeburt-kasachstan.de/archive-news/"
TARGET = 30
MAX_PAGES = 5
MAX_CANDIDATES = 120
OUTPUT = Path("derk_results/latest_articles_review.csv")
HEADERS = {"User-Agent": "DERK-Research-Pilot/0.3 (academic; contact site owner for bulk access)"}


def fetch(url: str) -> str:
    validate_public_url(url)
    with requests.get(url, headers=HEADERS, timeout=20, stream=True,
                      allow_redirects=False) as response:
        if response.status_code in (429, 403):
            raise RuntimeError(f"Site declined access ({response.status_code}); stop and seek permission")
        if 300 <= response.status_code < 400:
            raise RuntimeError(f"Redirect at {url}; inspect manually")
        response.raise_for_status()
        if "html" not in response.headers.get("Content-Type", "").lower():
            raise ValueError(f"Not an HTML page: {url}")
        content = bytearray()
        for chunk in response.iter_content(65536):
            content.extend(chunk)
            if len(content) > 3_000_000:
                raise ValueError(f"Page too large: {url}")
        return content.decode(response.encoding or "utf-8", errors="replace")


def same_site(url: str) -> bool:
    a, b = urlparse(url), urlparse(ARCHIVE)
    return a.scheme in ("https", "http") and a.hostname == b.hostname and not a.username


def canonical(href: str, base: str) -> str:
    return urldefrag(urljoin(base, href))[0]


# Sections of the website that are not news articles.
EXCLUDED_PATHS = {
    "archive-news",
    "biblioteka",
    "library",
    "mediateka",
    "mediаteka",
    "istoriya-organizatsii",
    "predprinimatelstvo",
    "molodezh",
    "obuchenie",
    "sotsialnaya-rabota",
    "contacts",
    "kontakty",
    "region",
    "regions",
}

def archive_links(markup: str, page_url: str):
    soup = BeautifulSoup(markup, "html.parser")
    article_links, next_pages = [], []
    for a in soup.select("a[href]"):
        url = canonical(a.get("href", ""), page_url)
        if not same_site(url):
            continue
        path = urlparse(url).path.lower().rstrip("/") 
        last_segment = path.split("/")[-1]
        if last_segment in EXCLUDED_PATHS:
            continue

        if path.endswith((".pdf", ".jpg", ".png", ".zip", ".webp")):
            continue
        classes = " ".join(a.get("class", []))
        rel = " ".join(a.get("rel", []))
        parent_classes = " ".join(a.parent.get("class", [])) if a.parent else ""
        hint = (a.get_text(" ", strip=True) or a.get("title", "")).strip()
        is_pagination = ("sf_paged=" in url or "page/" in path or
                         "next" in rel.lower() or "pagination" in (classes + parent_classes).lower())
        if is_pagination and ("archive-news" in path or "sf_paged=" in url):
            if url != page_url:
                next_pages.append(url)
            continue
        if not hint or path in ("", "/archive-news"):
            continue
        article_links.append((url, hint))
    return article_links, next_pages


def normal_date(value: str) -> str:
    value = (value or "").strip()[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return ""
    try:
        parsed = date.fromisoformat(value)
        return value if parsed <= date.today() else ""
    except ValueError:
        return ""


def examine(url: str, hint: str) -> dict:
    html = fetch(url)
    meta = extract_metadata(html, default_url=url)
    extracted = trafilatura.extract(html, include_comments=False) or ""
    published = normal_date(getattr(meta, "date", "") if meta else "")
    title = (getattr(meta, "title", "") if meta else "") or hint
    # No date guessing: undated pages must be manually checked.
    return {"url": url, "title": title, "published_date": published,
            "word_count": len(extracted.split()),
            "review_status": "dated_candidate" if published and len(extracted.split()) >= 60
            else "manual_review"}


def main():
    queue, visited_pages, seen_urls, rows = [ARCHIVE], set(), set(), []
    while queue and len(visited_pages) < MAX_PAGES and len(seen_urls) < MAX_CANDIDATES:
        page = queue.pop(0)
        if page in visited_pages:
            continue
        print("Archive page:", page)
        try:
            links, more = archive_links(fetch(page), page)
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            print("Archive page failed:", exc)
            break
        visited_pages.add(page)
        for next_page in more:
            if next_page not in visited_pages and next_page not in queue:
                queue.append(next_page)
        for url, hint in links:
            if url in seen_urls or len(seen_urls) >= MAX_CANDIDATES:
                continue
            seen_urls.add(url)
            try:
                rows.append(examine(url, hint))
            except (requests.RequestException, ValueError, RuntimeError) as exc:
                print("Skipping:", url, str(exc)[:100])
            time.sleep(0.3)
        time.sleep(0.5)

    dated = sorted((r for r in rows if r["review_status"] == "dated_candidate"),
                   key=lambda r: (r["published_date"], r["url"]), reverse=True)
    chosen = dated[:TARGET]
    chosen_urls = {r["url"] for r in chosen}
    for row in rows:
        row["selected_for_review"] = "yes" if row["url"] in chosen_urls else "no"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fields = ["url", "title", "published_date", "word_count", "review_status", "selected_for_review"]
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: r["published_date"], reverse=True))
    print(f"Checked {len(rows)} pages; found {len(dated)} dated text candidates; selected {len(chosen)}/{TARGET}")
    print("Review file:", OUTPUT)
    if len(chosen) < TARGET:
        print("WARNING: Fewer than 30 dated candidates; do not treat this as a complete sample.")
    print("Human verification of dates and article status is required before analysis.")


if __name__ == "__main__":
    main()
