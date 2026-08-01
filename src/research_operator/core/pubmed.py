from __future__ import annotations

from dataclasses import dataclass

try:
    import requests as _requests
except ImportError:
    _requests = None

from research_operator.core.logging_config import get_logger

_logger = get_logger(__name__)

_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
_HEADERS = {"User-Agent": "YatiriCLI/0.3 (research tool; contact: yatiri-bot)"}


@dataclass
class PubMedResult:
    title: str
    url: str
    snippet: str
    source_type: str = "academic"
    year: int | None = None


def search_pubmed(
    query: str,
    max_results: int = 3,
    year_from: int | None = None,
    year_to: int | None = None,
) -> list[PubMedResult]:
    if _requests is None:
        return []
    ids = _esearch(query, max_results, year_from=year_from, year_to=year_to)
    if not ids:
        return []
    return _esummary(ids)


def _esearch(
    query: str,
    retmax: int,
    year_from: int | None = None,
    year_to: int | None = None,
) -> list[str]:
    params = {"db": "pubmed", "term": query, "retmax": retmax, "retmode": "json"}
    if year_from or year_to:
        params["datetype"] = "pdat"
        params["mindate"] = str(year_from) if year_from else "1900"
        params["maxdate"] = str(year_to) if year_to else "3000"
    try:
        resp = _requests.get(
            f"{_BASE}/esearch.fcgi",
            params=params,
            headers=_HEADERS,
            timeout=8,
        )
        resp.raise_for_status()
        return resp.json().get("esearchresult", {}).get("idlist", [])
    except Exception as exc:
        _logger.warning("PubMed esearch falló para %r: %s: %s", query, type(exc).__name__, exc)
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
    except Exception as exc:
        _logger.warning("PubMed esummary falló: %s: %s", type(exc).__name__, exc)
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
