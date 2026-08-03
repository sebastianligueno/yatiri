"""Búsqueda directa en la biblioteca personal de Zotero vía Web API v3.

No depende de que Claude Code esté abierto ni de que BetterBibTeX haya
re-exportado el .bib local (ver core/bibtex_search.py para ese flujo
offline). Requiere ZOTERO_API_KEY y ZOTERO_LIBRARY_ID configurados
(`yatiri setup` → opción Zotero). Sin credenciales, las funciones
devuelven vacío/None igual que el resto de fetchers — no rompe el
flujo de búsqueda general.

Docs: https://www.zotero.org/support/dev/web_api/v3/basics
"""
from __future__ import annotations

import re
from dataclasses import dataclass

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

from research_operator.core.config import get_config
from research_operator.core.logging_config import get_logger

_logger = get_logger(__name__)

_BASE = "https://api.zotero.org"
_HEADERS_BASE = {"Zotero-API-Version": "3", "User-Agent": "YatiriCLI/0.3"}


@dataclass(slots=True)
class ZoteroResult:
    title: str
    url: str
    snippet: str
    doi: str | None
    journal: str | None
    year: str | None
    authors: str | None
    key: str
    source_type: str = "zotero"


def has_credentials() -> bool:
    return bool(get_config("ZOTERO_API_KEY")) and bool(get_config("ZOTERO_LIBRARY_ID"))


def search_zotero(query: str, max_results: int = 5) -> list[ZoteroResult]:
    if requests is None:
        return []
    api_key = get_config("ZOTERO_API_KEY")
    library_id = get_config("ZOTERO_LIBRARY_ID")
    if not api_key or not library_id:
        return []
    try:
        resp = requests.get(
            f"{_BASE}/users/{library_id}/items",
            params={
                "q": query,
                "qmode": "everything",
                "limit": max_results,
                "format": "json",
            },
            headers={**_HEADERS_BASE, "Zotero-API-Key": api_key},
            timeout=15,
        )
        resp.raise_for_status()
        items = resp.json()
    except Exception as exc:
        _logger.warning("Zotero falló para %r: %s: %s", query, type(exc).__name__, exc)
        return []

    results: list[ZoteroResult] = []
    for item in items:
        parsed = _parse_item(item)
        if parsed:
            results.append(parsed)
        if len(results) >= max_results:
            break
    return results


def find_in_zotero(doi: str | None, title: str | None) -> ZoteroResult | None:
    """Best-effort: busca coincidencia exacta por DOI, o por solape de título si no hay DOI."""
    if not has_credentials():
        return None
    if doi:
        for r in search_zotero(doi, max_results=5):
            if r.doi and r.doi.strip().lower() == doi.strip().lower():
                return r
    if title:
        title_tokens = set(_tokenize(title))
        if not title_tokens:
            return None
        for r in search_zotero(title, max_results=5):
            r_tokens = set(_tokenize(r.title))
            if not r_tokens:
                continue
            overlap = len(title_tokens & r_tokens) / len(title_tokens)
            if overlap >= 0.7:
                return r
    return None


def _parse_item(item: dict) -> ZoteroResult | None:
    data = item.get("data", {})
    if data.get("itemType") in {"attachment", "note"}:
        return None
    title = data.get("title") or ""
    if not title:
        return None
    doi = data.get("DOI") or None
    url = data.get("url") or (f"https://doi.org/{doi}" if doi else "")
    journal = data.get("publicationTitle") or data.get("bookTitle") or None
    year = _extract_year(data.get("date", ""))
    authors = _format_authors(data.get("creators") or [])
    snippet = (data.get("abstractNote") or "")[:400]
    return ZoteroResult(
        title=title,
        url=url,
        snippet=snippet,
        doi=doi,
        journal=journal,
        year=year,
        authors=authors,
        key=item.get("key", ""),
    )


def _extract_year(date_str: str) -> str | None:
    match = re.search(r"(19|20)\d{2}", date_str or "")
    return match.group(0) if match else None


def _format_authors(creators: list[dict]) -> str | None:
    names = []
    for c in creators[:3]:
        last = c.get("lastName", "")
        first = c.get("firstName", "")
        if last:
            initials = f"{first[0]}." if first else ""
            names.append(f"{last}, {initials}".strip(", "))
        elif c.get("name"):
            names.append(c["name"])
    if not names:
        return None
    if len(creators) > 3:
        names.append("et al.")
    return "; ".join(names)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-ZáéíóúñÁÉÍÓÚÑ]{4,}", text.lower())
