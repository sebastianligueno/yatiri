from __future__ import annotations

from pathlib import Path

from research_operator.cli.init import _WORKSPACE_DIRS, run_init


class TestRunInit:
    def test_crea_estructura_de_directorios(self, tmp_path: Path, capsys):
        root = tmp_path / "proyecto_x"
        run_init(root)
        for rel in _WORKSPACE_DIRS:
            assert (root / rel).is_dir()
        assert (root / ".research").is_dir()

    def test_crea_config_y_readme(self, tmp_path: Path, capsys):
        root = tmp_path / "proyecto_x"
        run_init(root)
        assert (root / ".research" / "project.yaml").exists()
        assert (root / "README.md").exists()

    def test_no_sobreescribe_readme_existente(self, tmp_path: Path, capsys):
        root = tmp_path / "proyecto_x"
        root.mkdir()
        (root / "README.md").write_text("contenido propio del usuario", encoding="utf-8")
        run_init(root)
        assert (root / "README.md").read_text(encoding="utf-8") == "contenido propio del usuario"

    def test_es_idempotente(self, tmp_path: Path, capsys):
        root = tmp_path / "proyecto_x"
        run_init(root)
        run_init(root)  # no debe fallar ni duplicar
        assert (root / "data" / "raw").is_dir()

    def test_imprime_resumen(self, tmp_path: Path, capsys):
        root = tmp_path / "proyecto_x"
        run_init(root)
        out = capsys.readouterr().out
        assert "Workspace inicializado" in out
        assert str(root) in out
