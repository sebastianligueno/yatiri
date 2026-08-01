from __future__ import annotations

from dataclasses import dataclass
import os

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

from research_operator.core.logging_config import get_logger

_logger = get_logger(__name__)

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


def _build_filter(
    query: str,
    language: str | None = "es",
    year_from: int | None = None,
    year_to: int | None = None,
) -> str:
    filters = []
    if language:
        filters.append(f"language:{language}")
    q_lower = query.lower()
    for term, code in _COUNTRY_CODES.items():
        if term in q_lower:
            filters.append(f"institutions.country_code:{code}")
            break
    if year_from:
        filters.append(f"from_publication_date:{year_from}-01-01")
    if year_to:
        filters.append(f"to_publication_date:{year_to}-12-31")
    return ",".join(filters)


def search_openalex(
    query: str,
    max_results: int = 5,
    language: str | None = "es",
    year_from: int | None = None,
    year_to: int | None = None,
) -> list[OpenAlexResult]:
    if requests is None:
        return []

    params: dict = {
        "search": query,
        "filter": _build_filter(query, language=language, year_from=year_from, year_to=year_to),
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
    except Exception as exc:
        _logger.warning("OpenAlex falló para %r: %s: %s", query, type(exc).__name__, exc)
        return []

    # Si el filtro de país no devuelve resultados, reintentar sin el país
    if not data.get("results") and "country_code" in params.get("filter", ""):
        params["filter"] = _build_filter("", language=language, year_from=year_from, year_to=year_to)
        try:
            response = requests.get(OPENALEX_URL, params=params, headers={"User-Agent": "YatiriCLI/0.3"}, timeout=20)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            _logger.warning("OpenAlex (reintento sin país) falló para %r: %s: %s", query, type(exc).__name__, exc)
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
    except Exception as exc:
        _logger.debug("No se pudo reconstruir abstract de OpenAlex: %s: %s", type(exc).__name__, exc)
        return ""
