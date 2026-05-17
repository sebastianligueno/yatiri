from __future__ import annotations

from pathlib import Path
import re

import yaml

from research_operator.core.models import ScanReport
from research_operator.core.profiles import infer_profile, run_profile_checks
from research_operator.core.project import config_path, load_project_config, research_dir
from research_operator.core.registry import append_jsonl


def scan_project(root: Path) -> ScanReport:
    cfg = load_project_config(root)
    inferred = infer_profile(root)
    cfg["project"]["profile"] = inferred["id"]
    cfg["project"]["id"] = sanitize_id(root.name)
    cfg["paths"] = infer_paths(root, cfg.get("paths", {}))
    config_path(root).write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")

    discovered_sources = discover_sources(root, cfg)
    sources_path = research_dir(root) / "sources.jsonl"
    sources_path.write_text("", encoding="utf-8")
    for record in discovered_sources:
        append_jsonl(sources_path, record)

    pipeline_steps = detect_pipeline_steps(root)
    cfg["pipeline"]["steps"] = pipeline_steps
    config_path(root).write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")

    report_path = research_dir(root) / "reports" / "project_scan.md"
    checks = run_profile_checks(root, inferred)
    report_path.write_text(build_report(root, inferred, discovered_sources, pipeline_steps, checks), encoding="utf-8")

    return ScanReport(
        project_name=cfg["project"]["name"],
        profile_id=inferred["id"],
        source_count=len(discovered_sources),
        pipeline_count=len(pipeline_steps),
        report_path=report_path,
    )


def discover_sources(root: Path, cfg: dict) -> list[dict]:
    include_globs = cfg.get("discovery", {}).get("include_globs", [])
    exclude_terms = cfg.get("discovery", {}).get("exclude_globs", [])
    records: list[dict] = []
    seen: set[Path] = set()

    for pattern in include_globs:
        for path in root.glob(pattern):
            if path.is_dir() or path in seen:
                continue
            rel_path = path.relative_to(root)
            rel_text = rel_path.as_posix()
            if any(_matches_exclude(rel_text, term) for term in exclude_terms):
                continue
            seen.add(path)
            records.append(
                {
                    "id": f"src_{len(records)+1:04d}",
                    "path": rel_text,
                    "type": infer_source_type(path),
                    "role": infer_source_role(rel_text),
                    "status": "active",
                }
            )

    records.sort(key=lambda item: item["path"])
    return records


def detect_pipeline_steps(root: Path) -> list[dict]:
    steps: list[dict] = []
    scripts_dir = root / "analysis" / "scripts"
    if scripts_dir.exists():
        for script in sorted(scripts_dir.glob("*.R")):
            step_id = sanitize_id(script.stem)
            steps.append(
                {
                    "id": step_id,
                    "label": script.stem.replace("_", " "),
                    "kind": "shell",
                    "run": f"Rscript {script.relative_to(root).as_posix()}",
                    "outputs": detect_outputs_from_name(script.stem),
                }
            )
    elif (root / "src").exists():
        for script in sorted((root / "src").rglob("cli.py")):
            steps.append(
                {
                    "id": script.stem.lower(),
                    "label": script.stem.replace("_", " "),
                    "kind": "shell",
                    "run": f"python3 {script.relative_to(root).as_posix()}",
                    "outputs": [],
                }
            )
    return steps


def build_report(root: Path, profile: dict, sources: list[dict], pipeline_steps: list[dict], checks: list[dict]) -> str:
    lines = [
        "# Project Scan",
        "",
        f"- Proyecto: {root.name}",
        f"- Perfil inferido: {profile['id']}",
        f"- Fuentes detectadas: {len(sources)}",
        f"- Pasos de pipeline detectados: {len(pipeline_steps)}",
        "",
        "## Chequeos",
        "",
    ]
    for check in checks:
        lines.append(f"- [{check['status']}] {check['label']}")

    lines.extend(["", "## Fuentes clave", ""])
    for record in sources[:20]:
        lines.append(f"- `{record['path']}` ({record['type']})")

    lines.extend(["", "## Pipeline detectado", ""])
    if pipeline_steps:
        for step in pipeline_steps:
            lines.append(f"- `{step['id']}` -> `{step['run']}`")
    else:
        lines.append("- No se detectaron scripts canonicos.")

    return "\n".join(lines) + "\n"


def infer_source_type(path: Path) -> str:
    suffix = path.suffix.lower()
    return {
        ".md": "markdown",
        ".qmd": "qmd_manuscript",
        ".r": "r_script",
        ".py": "python_script",
        ".csv": "dataset_csv",
        ".rds": "dataset_rds",
        ".xml": "xml_source",
        ".html": "html_source",
        ".bib": "bibtex",
    }.get(suffix, "file")


def infer_source_role(rel_text: str) -> str:
    if rel_text.startswith("paper/"):
        return "manuscript"
    if rel_text.startswith("analysis/scripts/"):
        return "pipeline"
    if rel_text.startswith("docs/") or rel_text == "README.md":
        return "project_doc"
    if "data-raw" in rel_text or "data/raw" in rel_text:
        return "raw_data"
    if "data-derived" in rel_text or "data/derived" in rel_text:
        return "derived_data"
    return "source"


def _matches_exclude(path_text: str, exclude_pattern: str) -> bool:
    normalized = exclude_pattern.replace("/**", "")
    return normalized and normalized in path_text


def detect_outputs_from_name(stem: str) -> list[str]:
    lower = stem.lower()
    if "derived" in lower:
        return ["data-derived"]
    if "parquet" in lower:
        return ["data/parquet"]
    if "render" in lower:
        return ["paper"]
    return []


def infer_paths(root: Path, current: dict) -> dict:
    paths = dict(current)
    paths["docs"] = existing_or_default(root, ["docs"], ["docs"])
    paths["manuscripts"] = existing_or_default(root, ["paper"], ["paper"])
    paths["scripts"] = existing_or_default(root, ["analysis/scripts", "scripts"], ["analysis/scripts"])
    paths["raw_data"] = existing_or_default(root, ["data-raw", "data/raw"], ["data/raw"])
    paths["derived_data"] = existing_or_default(root, ["data-derived", "data/derived"], ["data/derived"])
    paths["outputs"] = existing_or_default(root, ["output", "outputs"], ["output"])
    paths.setdefault("bibliography", [])
    return paths


def existing_or_default(root: Path, candidates: list[str], default: list[str]) -> list[str]:
    found = [candidate for candidate in candidates if (root / candidate).exists()]
    return found or default


def sanitize_id(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", value.lower())
    return cleaned.strip("_")
