from __future__ import annotations

from pathlib import Path

from research_operator.cli.scan import run_scan
from research_operator.cli.status import run_status


class TestRunStatus:
    def test_muestra_estado_tras_scan(self, tmp_path: Path, capsys):
        run_scan(tmp_path)
        capsys.readouterr()
        run_status(tmp_path)
        out = capsys.readouterr().out
        assert "Proyecto:" in out
        assert "Perfil:" in out
        assert "Chequeos:" in out

    def test_falla_sin_proyecto_inicializado(self, tmp_path: Path):
        try:
            run_status(tmp_path)
            assert False, "debía lanzar FileNotFoundError"
        except FileNotFoundError:
            pass
