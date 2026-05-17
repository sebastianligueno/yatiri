"""Búsqueda en HAL (Hyper Articles en Ligne) — archivo abierto francófono y europeo.

API pública sin clave: https://api.archives-ouvertes.fr/search/
Cobertura: Francia, Suiza, Bélgica, Quebec, Magreb y colaboraciones europeas.
Disciplinas: ciencias sociales, humanidades, educación, psicología y más.
"""
from __future__ import annotations

from dataclasses import dataclass

try:
    import requests as _requests
except ImportError:
    _requests = None

_BASE = "https://api.archives-ouvertes.fr/search/"
_FIELDS = "title_s,abstract_s,uri_s,producedDate_tdate,authFullName_s,journalTitle_s,docType_s"
_HEADERS = {"User-Agent": "YatiriCLI/0.3 (research tool)"}


@dataclass
class HALResult:
    title: str
    url: str
    snippet: str
    source_type: str = "academic"
    year: int | None = None


def search_hal(query: str, max_results: int = 3) -> list[HALResult]:
    if _requests is None:
        return []
    try:
        resp = _requests.get(
            _BASE,
            params={
                "q": query,
                "fl": _FIELDS,
                "rows": max_results,
                "wt": "json",
                "sort": "score desc",
            },
            headers=_HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        docs = resp.json().get("response", {}).get("docs", [])
    except Exception:
        return []

    results = []
    for doc in docs:
        title_raw = doc.get("title_s") or []
        title = title_raw[0] if isinstance(title_raw, list) else str(title_raw)
        if not title:
            continue
        url = doc.get("uri_s", "")
        abstract_raw = doc.get("abstract_s") or []
        abstract = abstract_raw[0] if isinstance(abstract_raw, list) else str(abstract_raw or "")
        snippet = abstract[:280].rstrip() + ("…" if len(abstract) > 280 else "")
        authors_raw = doc.get("authFullName_s") or []
        if authors_raw:
            a = authors_raw[0] if isinstance(authors_raw, list) else authors_raw
            if isinstance(authors_raw, list) and len(authors_raw) > 1:
                a += " et al."
            snippet = f"{a}. {snippet}" if snippet else a
        year = _extract_year(doc.get("producedDate_tdate", ""))
        results.append(HALResult(title=title, url=url, snippet=snippet, year=year))
    return results


def _extract_year(date_str: str) -> int | None:
    if date_str and len(date_str) >= 4 and date_str[:4].isdigit():
        return int(date_str[:4])
    return None
