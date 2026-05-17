"""Búsqueda en J-STAGE — plataforma académica japonesa de acceso abierto.

API pública sin clave: https://api.jstage.jst.go.jp/searchapi/do
Cobertura: Japón y colaboraciones asiáticas.
Disciplinas: ciencias naturales, sociales, humanidades, educación.
Responde en XML (Atom/OpenSearch).
"""
from __future__ import annotations

from dataclasses import dataclass
import xml.etree.ElementTree as ET

try:
    import requests as _requests
except ImportError:
    _requests = None

_BASE = "https://api.jstage.jst.go.jp/searchapi/do"
_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "prism": "http://prismstandard.org/namespaces/basic/2.0/",
}
_HEADERS = {"User-Agent": "YatiriCLI/0.3 (research tool)"}


@dataclass
class JStageResult:
    title: str
    url: str
    snippet: str
    source_type: str = "academic"
    year: int | None = None


def search_jstage(query: str, max_results: int = 3) -> list[JStageResult]:
    if _requests is None:
        return []
    try:
        resp = _requests.get(
            _BASE,
            params={"text": query, "count": max_results, "lang": "1"},
            headers=_HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception:
        return []

    results = []
    for entry in root.findall("atom:entry", _NS):
        title_el = entry.find("atom:title", _NS)
        title = title_el.text.strip() if title_el is not None and title_el.text else ""
        if not title:
            continue
        link_el = entry.find("atom:link[@rel='alternate']", _NS)
        url = link_el.get("href", "") if link_el is not None else ""
        if not url:
            link_el = entry.find("atom:link", _NS)
            url = link_el.get("href", "") if link_el is not None else ""
        summary_el = entry.find("atom:summary", _NS)
        summary = summary_el.text.strip() if summary_el is not None and summary_el.text else ""
        snippet = summary[:280].rstrip() + ("…" if len(summary) > 280 else "")
        # Author
        author_el = entry.find("atom:author/atom:name", _NS)
        if author_el is not None and author_el.text:
            snippet = f"{author_el.text.strip()}. {snippet}" if snippet else author_el.text.strip()
        # Year from prism:publicationDate or atom:updated
        year = None
        pub_date = entry.findtext("prism:publicationDate", namespaces=_NS) or \
                   entry.findtext("atom:updated", namespaces=_NS) or ""
        if pub_date and len(pub_date) >= 4 and pub_date[:4].isdigit():
            year = int(pub_date[:4])

        results.append(JStageResult(title=title, url=url, snippet=snippet, year=year))
    return results
