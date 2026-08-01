from __future__ import annotations

from pathlib import Path

import yaml

from research_operator.cli.run import run_step
from research_operator.core.project import config_path, ensure_research_layout, init_project_config


def _add_pipeline_step(root: Path, step_id: str, command: str) -> None:
    ensure_research_layout(root)
    init_project_config(root)
    cfg = yaml.safe_load(config_path(root).read_text(encoding="utf-8"))
    cfg["pipeline"]["steps"] = [{"id": step_id, "label": step_id, "kind": "shell", "run": command, "outputs": []}]
    config_path(root).write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")


class TestRunStep:
    def test_ejecuta_step_y_registra_log(self, tmp_path: Path, capsys):
        _add_pipeline_step(tmp_path, "saludo", "echo hola")
        run_step(tmp_path, "saludo")
        out = capsys.readouterr().out
        assert "Step: saludo" in out
        assert "Exit code: 0" in out
        log_files = list((tmp_path / ".research" / "reports").glob("run_saludo_*.log"))
        assert len(log_files) == 1
        assert "hola" in log_files[0].read_text(encoding="utf-8")

    def test_step_inexistente_lanza_value_error(self, tmp_path: Path):
        ensure_research_layout(tmp_path)
        init_project_config(tmp_path)
        try:
            run_step(tmp_path, "no-existe")
            assert False, "debía lanzar ValueError"
        except ValueError:
            pass
