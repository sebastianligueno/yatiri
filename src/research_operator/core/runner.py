from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shlex
import subprocess

from research_operator.core.project import load_project_config, research_dir
from research_operator.core.registry import append_jsonl


def run_pipeline_step(root: Path, step_id: str) -> dict:
    cfg = load_project_config(root)
    steps = cfg.get("pipeline", {}).get("steps", [])
    step = next((item for item in steps if item.get("id") == step_id), None)
    if step is None:
        raise ValueError(f"No existe step_id `{step_id}` en project.yaml")

    command = step["run"]
    process = subprocess.run(
        shlex.split(command),
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = research_dir(root) / "reports" / f"run_{step_id}_{ts}.log"
    log_path.write_text(
        f"$ {command}\n\nSTDOUT\n{process.stdout}\n\nSTDERR\n{process.stderr}\n",
        encoding="utf-8",
    )

    record = {
        "ts": datetime.now().isoformat(),
        "step_id": step_id,
        "command": command,
        "exit_code": process.returncode,
        "log_path": str(log_path),
        "outputs": step.get("outputs", []),
    }
    append_jsonl(research_dir(root) / "runs.jsonl", record)
    return record
