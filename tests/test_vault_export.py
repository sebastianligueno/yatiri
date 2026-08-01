from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from research_operator.core.vault_export import classify_to_folder, export_to_vault, get_vault_folders


@dataclass
class _FakeResult:
    title: str
    snippet: str = ""


class TestGetVaultFolders:
    def test_vault_inexistente_devuelve_vacio(self, tmp_path: Path):
        assert get_vault_folders(tmp_path / "no-existe") == []

    def test_ignora_carpetas_ocultas_y_archivos(self, tmp_path: Path):
        (tmp_path / "Convivencia").mkdir()
        (tmp_path / ".obsidian").mkdir()
        (tmp_path / "nota.md").write_text("x", encoding="utf-8")
        folders = get_vault_folders(tmp_path)
        assert [f.name for f in folders] == ["Convivencia"]


class TestClassifyToFolder:
    def test_sin_carpetas_devuelve_none(self):
        assert classify_to_folder(_FakeResult(title="X"), []) is None

    def test_elige_carpeta_con_mas_solapamiento(self, tmp_path: Path):
        f1 = tmp_path / "Convivencia Escolar"
        f2 = tmp_path / "Neurociencia"
        f1.mkdir()
        f2.mkdir()
        result = _FakeResult(title="Convivencia escolar en aula", snippet="bienestar socioemocional")
        assert classify_to_folder(result, [f1, f2]) == f1

    def test_sin_tokens_usa_primera_carpeta(self, tmp_path: Path):
        f1 = tmp_path / "A"
        f2 = tmp_path / "B"
        f1.mkdir()
        f2.mkdir()
        assert classify_to_folder(_FakeResult(title="a"), [f1, f2]) == f1


class TestExportToVault:
    def test_sin_auto_classify_exporta_a_raiz(self, tmp_path: Path):
        (tmp_path / "Convivencia").mkdir()
        summary = export_to_vault([_FakeResult(title="Un tema")], tmp_path, auto_classify=False)
        assert "raíz" in summary
        assert len(summary["raíz"]) == 1

    def test_con_auto_classify_agrupa_por_carpeta(self, tmp_path: Path):
        folder = tmp_path / "Convivencia Escolar"
        folder.mkdir()
        results = [_FakeResult(title="Convivencia escolar", snippet="bienestar")]
        summary = export_to_vault(results, tmp_path, auto_classify=True)
        assert "Convivencia Escolar" in summary
        assert len(summary["Convivencia Escolar"]) == 1

    def test_sin_carpetas_cae_a_raiz_aunque_auto_classify(self, tmp_path: Path):
        summary = export_to_vault([_FakeResult(title="X")], tmp_path, auto_classify=True)
        assert "raíz" in summary
