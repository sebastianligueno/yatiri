from __future__ import annotations

from pathlib import Path

from research_operator.core.project import ensure_research_layout, init_project_config
from research_operator.core.runner import run_pipeline_step


def run_step(root: Path, step_id: str) -> None:
    ensure_research_layout(root)
    init_project_config(root)
    result = run_pipeline_step(root, step_id)

    print(f"Step: {result['step_id']}")
    print(f"Exit code: {result['exit_code']}")
    print(f"Command: {result['command']}")
    print(f"Log: {result['log_path']}")
