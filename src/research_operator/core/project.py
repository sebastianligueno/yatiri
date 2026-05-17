from __future__ import annotations

from pathlib import Path
import re

import yaml

from research_operator.core.models import CheckResult, ProjectState
from research_operator.core.profiles import load_profile, run_profile_checks
from research_operator.core.registry import count_jsonl_records


RESEARCH_DIRNAME = ".research"


def research_dir(root: Path) -> Path:
    return root / RESEARCH_DIRNAME


def config_path(root: Path) -> Path:
    return research_dir(root) / "project.yaml"


def ensure_research_layout(root: Path) -> None:
    base = research_dir(root)
    for path in [
        base,
        base / "index",
        base / "reports",
        base / "notes",
        base / "notes" / "memos",
        base / "notes" / "continuity",
    ]:
        path.mkdir(parents=True, exist_ok=True)

    for filename in ["sources.jsonl", "runs.jsonl", "claims.jsonl"]:
        target = base / filename
        if not target.exists():
            target.write_text("", encoding="utf-8")


def init_project_config(root: Path) -> Path:
    target = config_path(root)
    if target.exists():
        return target

    project_name = root.name.replace("_", " ").strip() or "Proyecto"
    project_id = slugify(root.name) or "project"

    payload = {
        "schema_version": 1,
        "project": {
            "id": project_id,
            "name": project_name,
            "profile": "mixed_methods",
            "root": ".",
            "language": "es",
            "author": "",
            "description": "",
        },
        "paths": {
            "docs": ["docs"],
            "manuscripts": ["paper"],
            "scripts": ["analysis/scripts"],
            "raw_data": ["data/raw"],
            "derived_data": ["data/derived"],
            "outputs": ["output"],
            "concept_maps": ["maps", "mindmaps"],
            "bibliography": [],
        },
        "discovery": {
            "include_globs": [
                "README.md",
                "docs/**/*.md",
                "paper/**/*.qmd",
                "analysis/scripts/**/*.R",
                "src/**/*.py",
                "data-raw/manifests/**/*.csv",
                "data-derived/**/*.csv",
                "data-derived/**/*.rds",
                "data/processed/**/*.md",
                "data/audit/**/*.csv",
            ],
            "exclude_globs": [
                ".git/**",
                ".venv/**",
                "node_modules/**",
                ".research/**",
                "__pycache__/**",
                ".Rproj.user/**",
                ".cache/**",
            ],
        },
        "pipeline": {"steps": []},
        "evidence": {
            "claim_style": "project",
            "require_support_for_assertions": True,
            "support_types": [
                "quote",
                "table",
                "derived_file",
                "source_note",
                "bibliography_entry",
            ],
        },
        "academic_search": {
            "primary": "scite",
            "always_include": [
                "pubmed",
                "consensus",
                "scopus",
                "zotero",
            ],
            "spanish_open_sources": [
                "scielo",
                "redalyc",
                "dialnet",
                "latindex",
            ],
            "quality_open_priority": [
                "pubmed",
                "europe_pmc",
                "scielo",
                "openalex",
                "crossref",
            ],
            "fallback_web_sources": [
                "openalex",
                "crossref",
            ],
            "excluded_sources": [
                "scihub",
            ],
        },
        "concept_mapping": {
            "preferred_tool": "freeplane_mcp",
            "map_paths": [
                "maps",
                "mindmaps",
            ],
            "default_port": 6298,
            "requires_local_token": True,
        },
        "writing": {
            "active_manuscripts": [],
            "default_output_format": "qmd",
        },
        "agent": {
            "provider": "ollama",
            "model_main": "phi4-mini:3.8b",
            "model_light": "qwen3:1.7b",
            "max_context_files": 12,
        },
    }

    target.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return target


def load_project_config(root: Path) -> dict:
    target = config_path(root)
    if not target.exists():
        raise FileNotFoundError(f"No existe configuracion: {target}")
    return yaml.safe_load(target.read_text(encoding="utf-8")) or {}


def load_project_state(root: Path) -> ProjectState:
    cfg = load_project_config(root)
    project = cfg.get("project", {})
    profile_id = project.get("profile", "mixed_methods")
    profile = load_profile(profile_id)

    check_results = [
        CheckResult(label=result["label"], status=result["status"])
        for result in run_profile_checks(root, profile)
    ]

    return ProjectState(
        project_name=project.get("name", root.name),
        profile_id=profile_id,
        root=root,
        config_path=config_path(root),
        source_count=count_jsonl_records(research_dir(root) / "sources.jsonl"),
        run_count=count_jsonl_records(research_dir(root) / "runs.jsonl"),
        claim_count=count_jsonl_records(research_dir(root) / "claims.jsonl"),
        checks=check_results,
    )


def slugify(value: str) -> str:
    lowered = value.lower()
    cleaned = re.sub(r"[^a-z0-9]+", "_", lowered)
    return cleaned.strip("_")
