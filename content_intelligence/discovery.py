"""Discover candidate article URLs from an explicitly approved public website.

Discovery is read-only. Candidates are NOT verified articles and are NOT stored.
The researcher must review results before inclusion in the research corpus.
"""
from __future__ import annotations

from urllib.parse import urljoin, urlparse, urldefrag
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

from .collector import validate_public_url

USER_AGENT = 'DERK-Research-Pilot/0.2 (academic research; human review)'
MAX_BYTES = 3_000_000


def _get(url: str) -> tuple[str, str]:
    """Download a public text page, disallowing redirects and oversized responses."""
    validate_public_url(url)
    response = requests.get(url, headers={'User-Agent': USER_AGENT},
                            timeout=15, allow_redirects=False, stream=True)
    try:
        if 300 <= response.status_code < 400:
            raise ValueError('Источник перенаправляет запрос; проверьте конечный URL вручную.')
        response.raise_for_status()
        kind = response.headers.get('Content-Type', '').lower()
        if not any(x in kind for x in ('html', 'xml', 'rss', 'atom', 'text/plain')):
            raise ValueError('Источник не является HTML/XML страницей.')
        data = bytearray()
        for chunk in response.iter_content(65536):
            data.extend(chunk)
            if len(data) > MAX_BYTES:
                raise ValueError('Источник превышает лимит 3 МБ.')
        return data.decode(response.encoding or 'utf-8', errors='replace'), kind
    finally:
        response.close()


def _same_site(candidate: str, root: str) -> bool:
    a, b = urlparse(candidate), urlparse(root)
    return a.scheme in ('http', 'https') and a.hostname == b.hostname and not a.username and not a.password


# Preliminary classification only: a URL is never verified as an article here.
_NAVIGATION_PATHS = {
    'istoriya-organizatsii', 'region', 'archive-news', 'library',
    'retsepty', 'mediatеka', 'mediateka', 'contacts', 'kontakt',
    'kontakty', 'about', 'o-nas', 'news', 'novosti',
}
_NAVIGATION_TITLES = {
    'история организации', 'регионы', 'архив новостей',
    'библиотека', 'немецкая кухня', 'медиатека', 'контакты',
}


def classify_candidate(url: str, title: str = '') -> str:
    """Mark obvious navigation links for review; do not discard anything."""
    path = urlparse(url).path.strip('/').lower()
    segment = path.split('/')[-1] if path else ''
    label = ' '.join(title.casefold().split())
    if segment in _NAVIGATION_PATHS or label in _NAVIGATION_TITLES:
        return 'navigation_review'
    if 'sft_category=' in url.lower():
        return 'navigation_review'
    return 'article_candidate'


def discover_candidates(source_url: str, limit: int = 40) -> list[dict]:
    """Discover links from a site's landing/listing page; no crawling or DB writes.

    Returns candidate URLs only. An article must later be extracted and reviewed.
    """
    if not 1 <= limit <= 100:
        raise ValueError('limit должен быть от 1 до 100')
    source_url = validate_public_url(source_url)
    markup, kind = _get(source_url)
    result: list[dict] = []
    seen: set[str] = set()

    def add(href: str, title: str = '') -> None:
        absolute = urldefrag(urljoin(source_url, href.strip()))[0]
        if not _same_site(absolute, source_url):
            return
        if absolute.rstrip('/') == source_url.rstrip('/') or absolute in seen:
            return
        if urlparse(absolute).path.lower().endswith(('.jpg','.jpeg','.png','.gif','.pdf','.zip','.mp4','.webp')):
            return
        seen.add(absolute)
        result.append({'url': absolute, 'title_hint': title.strip(), 'status': 'candidate',
                       'review_group': classify_candidate(absolute, title)})

    if 'xml' in kind or markup.lstrip().startswith('<?xml'):
        try:
            root = ET.fromstring(markup)
            for item in root.iter():
                if item.tag.rsplit('}', 1)[-1].lower() in ('item', 'entry', 'url'):
                    link = ''
                    title = ''
                    for child in item:
                        name = child.tag.rsplit('}', 1)[-1].lower()
                        if name == 'loc' or name == 'link':
                            link = (child.attrib.get('href') or child.text or '').strip()
                        elif name == 'title':
                            title = child.text or ''
                    if link:
                        add(link, title)
                    if len(result) >= limit:
                        break
        except ET.ParseError as exc:
            raise ValueError('Некорректный XML RSS или sitemap.') from exc
    else:
        soup = BeautifulSoup(markup, 'html.parser')
        # Prioritise links in article listings; fallback to other visible links.
        primary = soup.select('article a[href], main a[href], [class*="news"] a[href], [class*="post"] a[href]')
        anchors = primary if primary else soup.select('a[href]')
        for a in anchors:
            href = a.get('href', '')
            if not href or href.startswith(('mailto:', 'tel:', 'javascript:')):
                continue
            add(href, a.get_text(' ', strip=True))
            if len(result) >= limit:
                break
    return result
