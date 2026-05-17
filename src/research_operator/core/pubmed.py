from __future__ import annotations

from dataclasses import dataclass

try:
    import requests as _requests
except ImportError:
    _requests = None

_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
_HEADERS = {"User-Agent": "YatiriCLI/0.3 (research tool; contact: yatiri-bot)"}


@dataclass
class PubMedResult:
    title: str
    url: str
    snippet: str
    source_type: str = "academic"
    year: int | None = None


def search_pubmed(query: str, max_results: int = 3) -> list[PubMedResult]:
    if _requests is None:
        return []
    ids = _esearch(query, max_results)
    if not ids:
        return []
    return _esummary(ids)


def _esearch(query: str, retmax: int) -> list[str]:
    try:
        resp = _requests.get(
            f"{_BASE}/esearch.fcgi",
            params={"db": "pubmed", "term": query, "retmax": retmax, "retmode": "json"},
            headers=_HEADERS,
            timeout=8,
        )
        resp.raise_for_status()
        return resp.json().get("esearchresult", {}).get("idlist", [])
    except Exception:
        return []


def _esummary(ids: list[str]) -> list[PubMedResult]:
    try:
        resp = _requests.get(
            f"{_BASE}/esummary.fcgi",
            params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
            headers=_HEADERS,
            timeout=8,
        )
        resp.raise_for_status()
        result_data = resp.json().get("result", {})
    except Exception:
        return []

    results = []
    for pmid in ids:
        item = result_data.get(pmid, {})
        if not item or item.get("error"):
            continue
        title = item.get("title", "").rstrip(".")
        if not title:
            continue
        pub_date = item.get("pubdate", "")
        year = _extract_year(pub_date)
        authors = item.get("authors", [])
        author_str = ""
        if authors:
            author_str = authors[0].get("name", "")
            if len(authors) > 1:
                author_str += " et al."
        source = item.get("source", "")
        snippet_parts = [p for p in [author_str, source, pub_date] if p]
        snippet = " · ".join(snippet_parts)
        results.append(
            PubMedResult(
                title=title,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                snippet=snippet,
                year=year,
            )
        )
    return results


def _extract_year(pub_date: str) -> int | None:
    for part in pub_date.split():
        if part.isdigit() and len(part) == 4:
            return int(part)
    return None
