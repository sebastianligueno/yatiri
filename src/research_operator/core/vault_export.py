"""Export directo al vault de Obsidian con clasificación temática automática.

Lee las carpetas del vault configurado, clasifica cada resultado según
similitud entre su contenido y el nombre de la carpeta, y guarda la ficha
en la ubicación correcta.
"""
from __future__ import annotations

import re
from pathlib import Path

from research_operator.core.export_md import export_results_to_md


def get_vault_folders(vault_path: Path) -> list[Path]:
    """Devuelve subcarpetas directas del vault (candidatas a temas)."""
    if not vault_path.exists():
        return []
    return sorted([
        d for d in vault_path.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ])


def classify_to_folder(result, folders: list[Path]) -> Path:
    """
    Clasifica un resultado en la carpeta más adecuada según similitud de tokens.
    Si no hay coincidencia clara, devuelve la primera carpeta o None.
    """
    if not folders:
        return None
    text = " ".join([
        getattr(result, "title", ""),
        getattr(result, "snippet", ""),
    ]).lower()
    result_tokens = set(_tokenize(text))
    if not result_tokens:
        return folders[0]

    best_score = 0
    best_folder = folders[0]
    for folder in folders:
        folder_tokens = set(_tokenize(folder.name))
        overlap = len(result_tokens & folder_tokens)
        if overlap > best_score:
            best_score = overlap
            best_folder = folder

    return best_folder


def export_to_vault(
    results: list,
    vault_path: Path,
    auto_classify: bool = True,
) -> dict[str, list[Path]]:
    """
    Exporta resultados directamente al vault, clasificando por carpeta temática.
    Devuelve dict {nombre_carpeta: [archivos_creados]}.
    """
    folders = get_vault_folders(vault_path)
    summary: dict[str, list[Path]] = {}

    if not auto_classify or not folders:
        # Sin vault o sin clasificación: exportar a raíz del vault
        created = export_results_to_md(results, vault_path)
        summary["raíz"] = created
        return summary

    # Clasificar cada resultado
    groups: dict[Path, list] = {}
    for result in results:
        folder = classify_to_folder(result, folders)
        groups.setdefault(folder, []).append(result)

    for folder, group in groups.items():
        created = export_results_to_md(group, folder)
        if created:
            summary[folder.name] = created

    return summary


def _tokenize(text: str) -> list[str]:
    return re.findall(r'[a-zA-ZáéíóúñÁÉÍÓÚÑ]{4,}', text.lower())
