from __future__ import annotations

from pathlib import Path

from research_operator.cli.ask import run_ask
from research_operator.cli.scan import run_scan


class TestRunAsk:
    def test_responde_sin_fuentes_indexadas(self, tmp_path: Path, capsys):
        run_ask(tmp_path, "cualquier pregunta")
        out = capsys.readouterr().out
        assert "No hay fuentes indexadas" in out

    def test_responde_con_fuentes_tras_scan(self, tmp_path: Path, capsys):
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "metodologia.md").write_text(
            "Descripción de la metodología cuantitativa del estudio.", encoding="utf-8"
        )
        run_scan(tmp_path)
        capsys.readouterr()
        run_ask(tmp_path, "metodología")
        out = capsys.readouterr().out
        assert "Pregunta: metodología" in out
        assert "metodologia.md" in out
