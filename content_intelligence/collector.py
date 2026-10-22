"""Pilot extractor for a single public article URL.

Only explicitly approved public websites should be analysed. No database writes.
"""
from __future__ import annotations

import ipaddress
import json
import socket
from urllib.parse import urlparse

import trafilatura


def validate_public_url(url: str) -> str:
    """Reject local/private hosts. Revalidate redirected destinations separately."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Требуется публичная ссылка http(s).")
    if parsed.username or parsed.password:
        raise ValueError("Ссылки со встроенными учётными данными запрещены.")
    host = parsed.hostname
    if host.lower() in {"localhost", "localhost.localdomain"} or host.lower().endswith((".local", ".internal")):
        raise ValueError("Локальные адреса запрещены.")
    try:
        addresses = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError("Не удалось определить адрес сайта.") from exc
    for item in addresses:
        ip = ipaddress.ip_address(item[4][0])
        if not ip.is_global:
            raise ValueError("Непубличные сетевые адреса запрещены.")
    return url.strip()


def extract_article_from_html(url: str, html: str) -> dict:
    """Parse supplied HTML without making any network request."""
    result = trafilatura.extract(
        html, url=url, output_format="json", with_metadata=True,
        include_links=False, favor_precision=True,
    )
    if not result:
        raise ValueError("Не удалось выделить текст статьи из HTML.")
    item = json.loads(result)
    return {
        "url": url,
        "title": item.get("title") or "",
        "date": item.get("date") or "",
        "author": item.get("author") or "",
        "text": item.get("text") or "",
        "language": item.get("language") or "",
    }


def collect_article(url: str) -> dict:
    """Fetch one article without redirects (pilot safety boundary)."""
    import requests

    url = validate_public_url(url)
    response = requests.get(url, timeout=15, allow_redirects=False,
                            headers={"User-Agent": "DERK-Research-Pilot/0.1"},
                            stream=True)
    try:
        if 300 <= response.status_code < 400:
            raise ValueError("Сайт перенаправляет запрос. Укажите конечный публичный URL.")
        response.raise_for_status()
        if "html" not in response.headers.get("Content-Type", "").lower():
            raise ValueError("Ссылка не ведёт на HTML-страницу.")
        maximum = 3_000_000
        raw = bytearray()
        for chunk in response.iter_content(chunk_size=65536):
            raw.extend(chunk)
            if len(raw) > maximum:
                raise ValueError("Страница превышает лимит пилотного сборщика (3 МБ).")
        response.encoding = response.encoding or "utf-8"
        return extract_article_from_html(url, bytes(raw).decode(response.encoding, errors="replace"))
    finally:
        response.close()
