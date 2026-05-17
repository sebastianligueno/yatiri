from __future__ import annotations

from dataclasses import dataclass
import html
import re
from urllib.parse import quote_plus, urlparse

try:
    import requests
except Exception:  # pragma: no cover
    requests = None


@dataclass(slots=True)
class WebResult:
    title: str
    url: str
    snippet: str
    domain: str
    source_type: str


def search_web(query: str, max_results: int = 5) -> list[WebResult]:
    if requests is None:
        return []

    try:
        response = requests.get(
            f"https://html.duckduckgo.com/html/?q={quote_plus(query)}",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20,
        )
        response.raise_for_status()
    except Exception:
        return []

    return parse_duckduckgo_html(response.text, max_results=max_results)


def parse_duckduckgo_html(payload: str, max_results: int = 5) -> list[WebResult]:
    pattern = re.compile(
        r'<a[^>]*class="result__a"[^>]*href="(?P<url>[^"]+)"[^>]*>(?P<title>.*?)</a>.*?'
        r'<a[^>]*class="result__snippet"[^>]*>(?P<snippet>.*?)</a>',
        re.DOTALL,
    )
    results: list[WebResult] = []
    for match in pattern.finditer(payload):
        title = clean_html(match.group("title"))
        url = html.unescape(match.group("url"))
        snippet = clean_html(match.group("snippet"))
        results.append(
            WebResult(
                title=title,
                url=url,
                snippet=snippet,
                domain=extract_domain(url),
                source_type=classify_source_type(url, title, snippet),
            )
        )
        if len(results) >= max_results:
            break
    return results


def clean_html(raw: str) -> str:
    text = re.sub(r"<.*?>", " ", raw)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def classify_source_type(url: str, title: str, snippet: str) -> str:
    blob = f"{url} {title} {snippet}".lower()
    if any(token in blob for token in ["scielo", "doi.org", "springer", "wiley", "tandfonline", "sagepub", "sciencedirect"]):
        return "academic"
    if any(token in blob for token in [".gov", ".gob", "ministerio", "ine.", "bcn.", "unesco", "who.int", "oecd", "cepal"]):
        return "institutional"
    if any(token in blob for token in ["ley", "norma", "decreto", "reglamento", "bcn.cl/leychile"]):
        return "legal"
    if any(token in blob for token in ["news", "noticia", "diario", "emol", "latercera", "biobiochile"]):
        return "press"
    return "web"
