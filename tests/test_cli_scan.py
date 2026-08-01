from __future__ import annotations

from pathlib import Path

from research_operator.cli.scan import run_scan


class TestRunScan:
    def test_escanea_proyecto_vacio(self, tmp_path: Path, capsys):
        run_scan(tmp_path)
        out = capsys.readouterr().out
        assert "Proyecto:" in out
        assert "Perfil inferido:" in out
        assert "Reporte:" in out
        assert (tmp_path / ".research" / "reports" / "project_scan.md").exists()

    def test_detecta_fuentes_markdown(self, tmp_path: Path, capsys):
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "protocolo.md").write_text("# Protocolo", encoding="utf-8")
        run_scan(tmp_path)
        out = capsys.readouterr().out
        assert "Fuentes registradas: 1" in out

    def test_es_idempotente(self, tmp_path: Path, capsys):
        run_scan(tmp_path)
        capsys.readouterr()
        run_scan(tmp_path)  # segunda corrida no debe fallar
        out = capsys.readouterr().out
        assert "Proyecto:" in out
