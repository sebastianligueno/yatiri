from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from research_operator.core.export_md import _escape_yaml, _slugify, export_results_to_md


@dataclass
class _FakeResult:
    title: str
    url: str = ""
    snippet: str = ""
    source_type: str = "academic"
    year: str | None = None
    citations: int | None = None


class TestSlugify:
    def test_quita_tildes_y_ene(self):
        assert _slugify("Ñoños en acción") == "nonos-en-accion"

    def test_colapsa_espacios_y_guiones(self):
        assert _slugify("Un   título -- con espacios") == "un-titulo-con-espacios"


class TestEscapeYaml:
    def test_escapa_comillas_dobles(self):
        assert _escape_yaml('Título con "comillas"') == 'Título con \\"comillas\\"'


class TestExportResultsToMd:
    def test_crea_un_archivo_por_resultado_con_titulo(self, tmp_path: Path):
        results = [
            _FakeResult(title="Convivencia escolar", url="https://x.org", snippet="resumen", year="2021"),
            _FakeResult(title=""),  # sin título: se descarta
        ]
        created = export_results_to_md(results, tmp_path)
        assert len(created) == 1
        assert created[0].exists()

    def test_contenido_incluye_frontmatter_y_resumen(self, tmp_path: Path):
        results = [_FakeResult(title="Un paper", url="https://x.org", snippet="resumen breve", year="2019")]
        created = export_results_to_md(results, tmp_path)
        text = created[0].read_text(encoding="utf-8")
        assert 'title: "Un paper"' in text
        assert "year: 2019" in text
        assert "resumen breve" in text

    def test_crea_directorio_si_no_existe(self, tmp_path: Path):
        output = tmp_path / "sub" / "carpeta"
        export_results_to_md([_FakeResult(title="X")], output)
        assert output.exists()
