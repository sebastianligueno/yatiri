"""Exporta resultados de búsqueda como fichas bibliográficas en Markdown.

Formato compatible con Obsidian, Zettlr, Joplin y Notion.
Cada resultado genera un archivo .md con frontmatter YAML.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path


def export_results_to_md(results: list, output_dir: Path) -> list[Path]:
    """
    Exporta una lista de resultados de búsqueda como fichas .md.
    Devuelve las rutas de los archivos creados.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    created = []
    for result in results:
        path = _write_card(result, output_dir)
        if path:
            created.append(path)
    return created


def _write_card(result, output_dir: Path) -> Path | None:
    title = getattr(result, "title", "") or ""
    if not title:
        return None
    url = getattr(result, "url", "") or ""
    snippet = getattr(result, "snippet", "") or ""
    source_type = getattr(result, "source_type", "academic")
    year = getattr(result, "year", None)
    citations = getattr(result, "citations", None)

    slug = _slugify(title)[:80]
    filename = output_dir / f"{slug}.md"

    # Frontmatter YAML
    lines = ["---"]
    lines.append(f'title: "{_escape_yaml(title)}"')
    if url:
        lines.append(f"url: {url}")
    if year:
        lines.append(f"year: {year}")
    lines.append(f"source: {source_type}")
    if citations is not None:
        lines.append(f"citations: {citations}")
    lines.append(f"added: {date.today().isoformat()}")
    lines.append("tags: [bibliografía, yatiri]")
    lines.append("---")
    lines.append("")
    lines.append(f"# {title}")
    lines.append("")
    if url:
        lines.append(f"**URL:** {url}")
        lines.append("")
    if snippet:
        lines.append("## Resumen")
        lines.append("")
        lines.append(snippet)
        lines.append("")
    lines.append("## Notas")
    lines.append("")
    lines.append("*(espacio para tus notas)*")
    lines.append("")

    filename.write_text("\n".join(lines), encoding="utf-8")
    return filename


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[áàäâ]", "a", text)
    text = re.sub(r"[éèëê]", "e", text)
    text = re.sub(r"[íìïî]", "i", text)
    text = re.sub(r"[óòöô]", "o", text)
    text = re.sub(r"[úùüû]", "u", text)
    text = re.sub(r"[ñ]", "n", text)
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text)
    return text.strip("-")


def _escape_yaml(text: str) -> str:
    return text.replace('"', '\\"')
