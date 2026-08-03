"""
Servidor MCP para Yatiri (research_operator).

Expone la búsqueda multi-fuente que ya vive en core/*.py (CrossRef, OpenAlex,
PubMed, HAL, J-STAGE, Semantic Scholar, SciELO) como una sola herramienta MCP,
sin pasar por el estado conversacional de Yatiri (SessionState/advisor) ni por
DeepSeek: la síntesis de resultados la hace el modelo que llama a esta
herramienta (Claude), no research_operator.

Ejecución local (stdio):
  python mcp_server.py

Registro en Claude Code:
  claude mcp add yatiri --scope user -- \
      /home/sebastianligueno/.pyenv/versions/3.12.6/bin/python \
      /media/COMUN/Documentos/Python/Research_Operator/src/research_operator/mcp_server.py
"""

from __future__ import annotations

import dataclasses
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Literal

try:
    import requests
except ImportError:
    requests = None

# mcp>=2.0 renombró FastMCP a mcp.server.mcpserver.MCPServer; este archivo
# no está migrado, por eso pyproject.toml fija "mcp>=1.0,<2.0".
from mcp.server.fastmcp import FastMCP

from research_operator.core.crossref import search_crossref
from research_operator.core.hal import search_hal
from research_operator.core.jstage import search_jstage
from research_operator.core.logging_config import get_logger
from research_operator.core.openalex import search_openalex
from research_operator.core.pubmed import search_pubmed
from research_operator.core.scielo import search_scielo
from research_operator.core.semantic_scholar import search_semantic_scholar

_logger = get_logger(__name__)

mcp = FastMCP("yatiri")

_SOURCES: dict[str, Any] = {
    "crossref": search_crossref,
    "openalex": search_openalex,
    "pubmed": search_pubmed,
    "hal": search_hal,
    "jstage": search_jstage,
    "semantic_scholar": search_semantic_scholar,
    "scielo": search_scielo,
}

# Fuentes cuya función core acepta year_from/year_to (ver core/*.py)
_YEAR_FILTER_SOURCES = {"crossref", "openalex", "pubmed", "semantic_scholar"}

_CITEDBY_META_URL = "https://citedby.scielo.org/api/v1/meta/"

_CACHE_TTL_SECONDS = 3600
_cache: dict[tuple, tuple[float, str]] = {}


def _normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    d = doi.strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    return d.rstrip("/") or None


def _normalize_title(title: str | None) -> str:
    if not title:
        return ""
    t = title.strip().lower()
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _dedupe_key(d: dict) -> tuple[str, str]:
    doi = _normalize_doi(d.get("doi"))
    if doi:
        return ("doi", doi)
    return ("title", _normalize_title(d.get("title")))


def _scielo_citing_count(title: str) -> int | None:
    """
    Best-effort: consulta si algún artículo de la red SciELO cita este
    título, vía citedby.scielo.org/api/v1/meta/ (coincidencia por texto
    de título, no por DOI/PID exacto — puede tener falsos negativos si el
    título no coincide letra por letra con el registrado en SciELO).
    El endpoint /doi/ del mismo servicio estaba devolviendo error 500 al
    verificar esto (2026-07-31), por eso se usa /meta/ en su lugar.
    """
    if requests is None:
        return None
    try:
        resp = requests.get(
            _CITEDBY_META_URL,
            params={"title": title},
            headers={"User-Agent": "yatiri-mcp/1.0"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("article", {}).get("total_received")
    except Exception as exc:
        _logger.warning("citedby.scielo.org falló para %r: %s: %s", title, type(exc).__name__, exc)
        return None


@mcp.tool(
    annotations={
        "title": "Búsqueda académica multi-fuente (Yatiri)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
def multi_source_search(
    query: str,
    max_results: int = 5,
    sources: list[str] | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    response_format: Literal["markdown", "json"] = "markdown",
    enrich_scielo_citations: bool = False,
) -> str:
    """
    Busca en paralelo en las fuentes académicas ya integradas en Yatiri:
    CrossRef, OpenAlex, PubMed, HAL, J-STAGE, Semantic Scholar y SciELO
    (metadatos vía articlemeta; si eso no trae nada, cae a un fallback vía
    DuckDuckGo filtrado por dominio scielo.* — el buscador propio de
    SciELO, search.scielo.org, sigue bloqueado por protección anti-bot en
    su motor Solr, así que esta fuente rinde menos que las demás y puede
    devolver 0 resultados igual). Las consultas corren en threads
    simultáneos, así que el tiempo total es el de la fuente más lenta, no
    la suma de todas. Los resultados duplicados entre fuentes (mismo DOI,
    o mismo título normalizado si no hay DOI) se fusionan en una sola
    entrada que lista en qué fuentes apareció — esa coincidencia entre
    fuentes independientes es en sí una señal de relevancia. Las
    respuestas se cachean en memoria por 1 hora (misma consulta y mismos
    parámetros no vuelve a golpear las APIs).

    Args:
        query: Términos de búsqueda en español, portugués o inglés.
        max_results: Máximo de resultados por fuente (default 5).
        sources: Subconjunto de fuentes a consultar. Valores válidos:
            crossref, openalex, pubmed, hal, jstage, semantic_scholar,
            scielo. Si se omite, consulta todas.
        year_from: Año mínimo de publicación. Solo aplica a crossref,
            openalex, pubmed y semantic_scholar (hal/jstage/scielo lo
            ignoran, no lo soportan en su API).
        year_to: Año máximo de publicación. Mismas fuentes que year_from.
        response_format: 'markdown' (legible) o 'json' (para programar
            un pipeline posterior).
        enrich_scielo_citations: si es True, para cada resultado único
            consulta (best-effort, por coincidencia de título) si algún
            artículo de la red SciELO lo cita — cross-check de literatura
            latinoamericana aunque el resultado original no sea de
            SciELO. Más lento (una llamada extra por resultado).

    Returns:
        Resultados deduplicados en el formato pedido, con título, año,
        autores (si están disponibles), DOI/URL, fuentes donde apareció y
        snippet. Cada fuente que falle o no tenga resultados se reporta
        explícitamente en vez de omitirse en silencio.
    """
    selected = sources or list(_SOURCES.keys())
    unknown = [s for s in selected if s not in _SOURCES]
    if unknown:
        return f"Fuentes desconocidas: {unknown}. Válidas: {list(_SOURCES.keys())}"

    cache_key = (
        query, max_results, tuple(sorted(selected)), year_from, year_to,
        response_format, enrich_scielo_citations,
    )
    cached = _cache.get(cache_key)
    if cached is not None and time.monotonic() - cached[0] < _CACHE_TTL_SECONDS:
        return cached[1]

    raw: dict[str, tuple[list | None, str | None]] = {}
    with ThreadPoolExecutor(max_workers=len(selected)) as pool:
        futures = {}
        for name in selected:
            kwargs: dict = {"max_results": max_results}
            if name in _YEAR_FILTER_SOURCES:
                kwargs["year_from"] = year_from
                kwargs["year_to"] = year_to
            futures[pool.submit(_SOURCES[name], query, **kwargs)] = name
        for future in as_completed(futures):
            name = futures[future]
            try:
                raw[name] = (future.result(), None)
            except Exception as e:
                _logger.warning("Fuente %s falló para %r: %s: %s", name, query, type(e).__name__, e)
                raw[name] = (None, f"{type(e).__name__}: {e}")

    status_lines: list[str] = []
    seen: dict[tuple[str, str], dict] = {}
    unique_results: list[dict] = []
    for name in selected:
        results, error = raw[name]
        if error is not None:
            status_lines.append(f"- [{name}] Error: {error}")
            continue
        if not results:
            status_lines.append(f"- [{name}] Sin resultados.")
            continue
        for r in results:
            d = dataclasses.asdict(r)
            key = _dedupe_key(d)
            existing = seen.get(key)
            if existing is not None:
                existing["_sources"].append(name)
                for field in ("doi", "url", "authors", "snippet", "year"):
                    if not existing.get(field) and d.get(field):
                        existing[field] = d[field]
                continue
            d["_sources"] = [name]
            seen[key] = d
            unique_results.append(d)

    if enrich_scielo_citations and unique_results:
        with ThreadPoolExecutor(max_workers=min(8, len(unique_results))) as pool:
            futures = {
                pool.submit(_scielo_citing_count, d["title"]): d
                for d in unique_results
                if d.get("title")
            }
            for future in as_completed(futures):
                futures[future]["_scielo_cited_by"] = future.result()

    if response_format == "json":
        payload = []
        for d in unique_results:
            entry = {
                "title": d.get("title"),
                "year": d.get("year"),
                "authors": d.get("authors"),
                "doi": d.get("doi"),
                "url": d.get("url"),
                "snippet": d.get("snippet"),
                "sources": d["_sources"],
            }
            if enrich_scielo_citations:
                entry["scielo_cited_by"] = d.get("_scielo_cited_by")
            payload.append(entry)
        result = json.dumps(
            {"query": query, "status": status_lines, "results": payload},
            ensure_ascii=False, indent=2,
        )
        _cache[cache_key] = (time.monotonic(), result)
        return result

    lines: list[str] = [f"# Búsqueda multi-fuente: \"{query}\"\n", *status_lines, ""]
    for d in unique_results:
        title = d.get("title", "(sin título)")
        year = d.get("year", "")
        authors = d.get("authors")
        doi = d.get("doi")
        url = d.get("url", "")
        snippet = d.get("snippet", "")
        srcs = ", ".join(d["_sources"])
        header = f"- **{title}**"
        if year:
            header += f" ({year})"
        lines.append(header)
        lines.append(f"  - Fuentes: {srcs}")
        if authors:
            lines.append(f"  - Autores: {authors}")
        if doi:
            lines.append(f"  - DOI: {doi}")
        if url:
            lines.append(f"  - URL: {url}")
        if enrich_scielo_citations:
            cited = d.get("_scielo_cited_by")
            lines.append(
                f"  - Citado por artículos SciELO: {cited if cited is not None else 'no verificable'}"
            )
        if snippet:
            lines.append(f"  - {snippet[:300]}")

    lines.append(f"\nTotal de resultados únicos: {len(unique_results)}")
    result = "\n".join(lines)
    _cache[cache_key] = (time.monotonic(), result)
    return result


if __name__ == "__main__":
    mcp.run()
