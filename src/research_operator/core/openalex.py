from __future__ import annotations

from dataclasses import dataclass
import os

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

OPENALEX_URL = "https://api.openalex.org/works"


@dataclass(slots=True)
class OpenAlexResult:
    title: str
    url: str
    snippet: str
    doi: str | None
    journal: str | None
    year: str | None
    source_type: str = "academic"


def search_openalex(query: str, max_results: int = 5) -> list[OpenAlexResult]:
    if requests is None:
        return []

    params: dict = {
        "search": query,
        "per-page": max_results,
        "select": "title,doi,publication_year,primary_location,open_access,abstract_inverted_index",
    }
    email = os.environ.get("SCHOLAR_CONTACT_EMAIL", "")
    if email:
        params["mailto"] = email

    try:
        response = requests.get(
            OPENALEX_URL,
            params=params,
            headers={"User-Agent": "YatiriCLI/0.3"},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
    except Exception:
        return []

    results: list[OpenAlexResult] = []
    for item in data.get("results", [])[:max_results]:
        title = item.get("title") or ""
        if not title:
            continue

        raw_doi = item.get("doi") or None
        doi = raw_doi.replace("https://doi.org/", "") if raw_doi else None

        oa_url = (item.get("open_access") or {}).get("oa_url") or ""
        url = oa_url or (f"https://doi.org/{doi}" if doi else "")

        year = str(item.get("publication_year") or "")

        source = ((item.get("primary_location") or {}).get("source") or {})
        journal = source.get("display_name")

        snippet = _reconstruct_abstract(item.get("abstract_inverted_index"))

        results.append(
            OpenAlexResult(
                title=title,
                url=url,
                snippet=snippet[:320],
                doi=doi,
                journal=journal,
                year=year,
            )
        )

    return results


def _reconstruct_abstract(inverted_index: dict | None) -> str:
    if not inverted_index:
        return ""
    try:
        position_word: dict[int, str] = {}
        for word, positions in inverted_index.items():
            for pos in positions:
                position_word[pos] = word
        return " ".join(position_word[i] for i in sorted(position_word))
    except Exception:
        return ""
