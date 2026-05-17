from __future__ import annotations

from dataclasses import dataclass, field

try:
    import requests as _requests
except ImportError:
    _requests = None

_BASE = "https://api.semanticscholar.org/graph/v1"
_FIELDS = "title,abstract,year,authors,openAccessPdf,citationCount,externalIds"
_HEADERS = {"User-Agent": "YatiriCLI/0.3 (research tool; contact: yatiri-bot)"}


@dataclass
class SemanticResult:
    title: str
    url: str
    snippet: str
    source_type: str = "academic"
    year: int | None = None
    citations: int | None = None


def search_semantic_scholar(query: str, max_results: int = 4) -> list[SemanticResult]:
    if _requests is None:
        return []
    try:
        resp = _requests.get(
            f"{_BASE}/paper/search",
            params={"query": query, "fields": _FIELDS, "limit": max_results},
            headers=_HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])
    except Exception:
        return []

    results = []
    for item in data:
        title = item.get("title") or ""
        if not title:
            continue
        doi = (item.get("externalIds") or {}).get("DOI", "")
        pdf_url = (item.get("openAccessPdf") or {}).get("url", "")
        url = (
            f"https://doi.org/{doi}" if doi
            else pdf_url
            or f"https://www.semanticscholar.org/paper/{item.get('paperId', '')}"
        )
        abstract = item.get("abstract") or ""
        snippet = abstract[:280].rstrip() + ("…" if len(abstract) > 280 else "")
        authors = item.get("authors") or []
        if authors:
            author_str = authors[0].get("name", "")
            if len(authors) > 1:
                author_str += " et al."
            snippet = f"{author_str}. {snippet}" if snippet else author_str

        results.append(
            SemanticResult(
                title=title,
                url=url,
                snippet=snippet,
                year=item.get("year"),
                citations=item.get("citationCount"),
            )
        )
    return results
