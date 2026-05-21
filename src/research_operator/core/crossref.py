from __future__ import annotations

import html
import re
from dataclasses import dataclass

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

_BASE = "https://api.crossref.org/works"
_HEADERS = {"User-Agent": "YatiriCLI/0.3 (mailto:sebastianligueno@gmail.com; tool: yatiri academic assistant)"}

# Títulos que son metadata de libros, no contenido académico
_JUNK_TITLES = re.compile(
    r"^(front matter|back matter|abreviaturas?|abreviaciones?|"
    r"comité\s+(científico|editorial|organizador)|índice|"
    r"acknowledgements?|agradecimientos?|preface|prefacio|"
    r"table of contents?|contents?|copyright|contraportada|"
    r"bibliografía$|references?$|notas?$|anexos?$|apéndice)$",
    re.IGNORECASE,
)


@dataclass(slots=True)
class CrossRefResult:
    title: str
    url: str
    snippet: str
    doi: str | None
    journal: str | None
    year: str | None
    authors: str | None
    source_type: str = "academic"


def search_crossref(query: str, max_results: int = 5) -> list[CrossRefResult]:
    if requests is None:
        return []
    try:
        resp = requests.get(
            _BASE,
            params={"query": query, "rows": max_results},
            headers=_HEADERS,
            timeout=20,
        )
        resp.raise_for_status()
        items = resp.json().get("message", {}).get("items", [])
    except Exception:
        return []

    results: list[CrossRefResult] = []
    for item in items:
        if len(results) >= max_results:
            break
        title_list = item.get("title") or []
        title = title_list[0] if title_list else ""
        if not title:
            continue
        if _JUNK_TITLES.match(title.strip()):
            continue
        # Descartar capítulos sin abstract y con títulos muy cortos (probablemente metadata)
        raw_abstract = item.get("abstract") or ""
        if not raw_abstract and len(title.split()) < 4:
            continue

        doi = item.get("DOI") or None
        url = f"https://doi.org/{doi}" if doi else ""

        journal_list = item.get("container-title") or []
        journal = journal_list[0] if journal_list else None

        year = _extract_year(item.get("published") or item.get("published-print") or item.get("created"))

        authors = _format_authors(item.get("author") or [])

        raw_abstract = item.get("abstract") or ""
        snippet = _clean(raw_abstract)[:600]

        results.append(CrossRefResult(
            title=_clean(title),
            url=url,
            snippet=snippet,
            doi=doi,
            journal=journal,
            year=year,
            authors=authors,
        ))
    return results


def _extract_year(published: dict | None) -> str | None:
    if not published:
        return None
    parts = published.get("date-parts", [[]])
    if parts and parts[0]:
        return str(parts[0][0])
    return None


def _format_authors(authors: list[dict]) -> str | None:
    if not authors:
        return None
    names = []
    for a in authors[:3]:
        family = a.get("family", "")
        given = a.get("given", "")
        if family:
            initials = " ".join(f"{p[0]}." for p in given.split() if p) if given else ""
            names.append(f"{family}, {initials}".strip(", "))
    if len(authors) > 3:
        names.append("et al.")
    return "; ".join(names)


def _clean(raw: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()
