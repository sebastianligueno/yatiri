from __future__ import annotations

from pathlib import Path

from research_operator.core.project import ensure_research_layout, init_project_config
from research_operator.core.scanner import scan_project


def run_scan(root: Path) -> None:
    ensure_research_layout(root)
    init_project_config(root)
    report = scan_project(root)

    print(f"Proyecto: {report.project_name}")
    print(f"Perfil inferido: {report.profile_id}")
    print(f"Fuentes registradas: {report.source_count}")
    print(f"Pasos de pipeline detectados: {report.pipeline_count}")
    print(f"Reporte: {report.report_path}")
