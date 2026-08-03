from __future__ import annotations

import html
import re
from dataclasses import dataclass
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

from research_operator.core.logging_config import get_logger

_logger = get_logger(__name__)


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
    except Exception as exc:
        _logger.warning("Búsqueda web (DuckDuckGo) falló para %r: %s: %s", query, type(exc).__name__, exc)
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
        raw_url = html.unescape(match.group("url"))
        url = resolve_ddg_redirect(raw_url)
        if url is None:
            continue
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


def resolve_ddg_redirect(url: str) -> str | None:
    """Resuelve una URL de redirección de DuckDuckGo (//duckduckgo.com/l/?uddg=...)
    a la URL real de destino. Si `url` no es un redirect, la devuelve sin
    cambios. Devuelve None si es un redirect pero no se pudo recuperar el
    destino — el resultado original no sirve para nada aguas abajo (dominio
    y clasificación de fuente quedarían sobre duckduckgo.com, no sobre el
    sitio real)."""
    if "duckduckgo.com/l/" not in url and not url.startswith("//duckduckgo"):
        return url
    parsed = urlparse(url if url.startswith("http") else "https:" + url)
    uddg = parse_qs(parsed.query).get("uddg", [""])
    if uddg and uddg[0]:
        return unquote(uddg[0])
    return None


def clean_html(raw: str) -> str:
    text = re.sub(r"<.*?>", " ", raw)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_domain(url: str) -> str:
    if not url:
        return ""
    try:
        return urlparse(url).netloc.lower()
    except Exception as exc:
        _logger.debug("No se pudo parsear dominio de %r: %s: %s", url, type(exc).__name__, exc)
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
