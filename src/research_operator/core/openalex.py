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
    authors: str | None = None
    source_type: str = "academic"


_COUNTRY_CODES: dict[str, str] = {
    "chile": "CL", "chileno": "CL", "chilena": "CL", "chilenos": "CL",
    "argentina": "AR", "argentino": "AR", "argentina": "AR",
    "brasil": "BR", "brazil": "BR", "brasileño": "BR",
    "colombia": "CO", "colombiano": "CO",
    "méxico": "MX", "mexico": "MX", "mexicano": "MX",
    "perú": "PE", "peru": "PE", "peruano": "PE",
    "españa": "ES", "spain": "ES", "español": "ES",
}


def _build_filter(query: str) -> str:
    filters = ["language:es"]
    q_lower = query.lower()
    for term, code in _COUNTRY_CODES.items():
        if term in q_lower:
            filters.append(f"institutions.country_code:{code}")
            break
    return ",".join(filters)


def search_openalex(query: str, max_results: int = 5) -> list[OpenAlexResult]:
    if requests is None:
        return []

    params: dict = {
        "search": query,
        "filter": _build_filter(query),
        "per-page": max_results,
        "select": "title,doi,publication_year,primary_location,open_access,abstract_inverted_index,authorships",
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

    # Si el filtro de país no devuelve resultados, reintentar solo con idioma
    if not data.get("results") and "country_code" in params.get("filter", ""):
        params["filter"] = "language:es"
        try:
            response = requests.get(OPENALEX_URL, params=params, headers={"User-Agent": "YatiriCLI/0.3"}, timeout=20)
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
        authors = _format_authors(item.get("authorships") or [])

        results.append(
            OpenAlexResult(
                title=title,
                url=url,
                snippet=snippet[:600],
                doi=doi,
                journal=journal,
                year=year,
                authors=authors,
            )
        )

    return results


def _format_authors(authorships: list[dict]) -> str | None:
    if not authorships:
        return None
    names = [
        a["author"]["display_name"]
        for a in authorships[:3]
        if a.get("author", {}).get("display_name")
    ]
    if not names:
        return None
    if len(authorships) > 3:
        names.append("et al.")
    return "; ".join(names)


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
