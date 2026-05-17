from __future__ import annotations

from dataclasses import dataclass
import html
import os
import re
from urllib.parse import quote_plus

try:
    import requests
except Exception:  # pragma: no cover
    requests = None


ARTICLEMETA_URL = os.environ.get("SCIELO_ARTICLEMETA_URL", "https://articlemeta.scielo.org/api/v1/article/")
SEARCH_URL = os.environ.get("SCIELO_SEARCH_URL", "https://search.scielo.org/")


@dataclass(slots=True)
class SciELOResult:
    title: str
    url: str
    snippet: str
    doi: str | None
    journal: str | None
    collection: str | None
    year: str | None
    source_type: str = "scielo"


def search_scielo(query: str, max_results: int = 5) -> list[SciELOResult]:
    if requests is None:
        return []

    results = search_scielo_articlemeta(query, max_results=max_results)
    if results:
        return results[:max_results]
    return search_scielo_html(query, max_results=max_results)


def search_scielo_articlemeta(query: str, max_results: int = 5) -> list[SciELOResult]:
    params_candidates = [
        {"q": query, "limit": max_results, "offset": 0},
        {"title": query, "limit": max_results, "offset": 0},
    ]

    for params in params_candidates:
        try:
            response = requests.get(
                ARTICLEMETA_URL,
                params=params,
                headers={"User-Agent": "YatiriCLI/0.3"},
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
        except Exception:
            continue

        objects = extract_objects(data)
        if not objects:
            continue

        parsed = [parse_articlemeta_object(item) for item in objects]
        filtered = [item for item in parsed if item and looks_relevant(item, query)]
        if filtered:
            return filtered[:max_results]

    return []


def extract_objects(payload) -> list[dict]:
    if isinstance(payload, dict):
        for key in ("objects", "results", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        if "article" in payload and isinstance(payload["article"], list):
            return [item for item in payload["article"] if isinstance(item, dict)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def parse_articlemeta_object(item: dict) -> SciELOResult | None:
    title = first_text(
        item.get("title"),
        item.get("title_en"),
        item.get("title_pt"),
        item.get("title_es"),
        nested_get(item, "titles"),
    )
    if not title:
        return None

    abstract = first_text(
        item.get("abstract"),
        item.get("abstract_en"),
        item.get("abstract_pt"),
        item.get("abstract_es"),
        nested_get(item, "abstracts"),
    )
    doi = first_text(item.get("doi"), nested_get(item, "doi"))
    url = first_text(
        item.get("url"),
        item.get("html"),
        item.get("url_html"),
        nested_get(item, "url"),
        nested_get(item, "urls"),
    )
    if not url and doi:
        url = f"https://doi.org/{doi}"
    if not url:
        pid = first_text(item.get("pid"), item.get("pid_v2"), item.get("code"))
        collection = first_text(item.get("collection"), item.get("collection_acron"))
        if pid and collection:
            url = build_scielo_article_url(collection, pid)
        else:
            url = ""

    return SciELOResult(
        title=clean_text(title),
        url=url,
        snippet=clean_text(abstract)[:320],
        doi=doi,
        journal=first_text(item.get("journal_title"), item.get("journal")),
        collection=first_text(item.get("collection"), item.get("collection_acron")),
        year=extract_year(item),
    )


def build_scielo_article_url(collection: str, pid: str) -> str:
    return f"https://www.scielo.org/{collection}/j/*/a/{pid}/"


def extract_year(item: dict) -> str | None:
    for key in ("publication_year", "year", "created", "publication_date"):
        value = first_text(item.get(key))
        if not value:
            continue
        match = re.search(r"(19|20)\d{2}", value)
        if match:
            return match.group(0)
    return None


def search_scielo_html(query: str, max_results: int = 5) -> list[SciELOResult]:
    try:
        response = requests.get(
            f"{SEARCH_URL}?lang=es&q={quote_plus(query)}",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20,
        )
        response.raise_for_status()
    except Exception:
        return []

    return parse_scielo_search_html(response.text, max_results=max_results)


def parse_scielo_search_html(payload: str, max_results: int = 5) -> list[SciELOResult]:
    anchor_pattern = re.compile(
        r'<a[^>]*href="(?P<url>https?://[^"]+)"[^>]*>(?P<title>.*?)</a>',
        re.DOTALL | re.IGNORECASE,
    )
    results: list[SciELOResult] = []
    seen: set[str] = set()

    for match in anchor_pattern.finditer(payload):
        url = html.unescape(match.group("url"))
        if url in seen:
            continue
        if "scielo" not in url and "doi.org" not in url:
            continue

        title = clean_text(match.group("title"))
        if len(title) < 12:
            continue

        snippet = extract_local_snippet(payload, match.start(), match.end())
        doi_match = re.search(r"10\.\d{4,9}/[^\s\"<]+", snippet)
        results.append(
            SciELOResult(
                title=title,
                url=url,
                snippet=snippet[:320],
                doi=doi_match.group(0) if doi_match else None,
                journal=None,
                collection=None,
                year=extract_year_from_text(snippet),
            )
        )
        seen.add(url)
        if len(results) >= max_results:
            break

    return results


def extract_local_snippet(payload: str, start: int, end: int) -> str:
    window = payload[end:end + 900]
    text = clean_text(window)
    return text[:320]


def extract_year_from_text(text: str) -> str | None:
    match = re.search(r"(19|20)\d{2}", text)
    return match.group(0) if match else None


def clean_text(raw: str) -> str:
    text = re.sub(r"<.*?>", " ", raw or "")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def first_text(*values) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    return item.strip()
                if isinstance(item, dict):
                    nested = first_text(*item.values())
                    if nested:
                        return nested
        if isinstance(value, dict):
            nested = first_text(*value.values())
            if nested:
                return nested
    return None


def nested_get(item: dict, key: str):
    value = item.get(key)
    if value is not None:
        return value
    for nested_key in ("resource", "metadata", "article"):
        nested = item.get(nested_key)
        if isinstance(nested, dict) and key in nested:
            return nested.get(key)
    return None


def looks_relevant(item: SciELOResult, query: str) -> bool:
    tokens = tokenize(query)
    blob = f"{item.title} {item.snippet} {item.journal or ''}".lower()
    if not tokens:
        return True
    return any(token in blob for token in tokens)


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-ZáéíóúñÁÉÍÓÚÑ]{4,}", text.lower())
