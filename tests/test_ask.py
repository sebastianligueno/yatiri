"""
Complementa test_cli_ask.py (que cubre answer_question de punta a punta).
Aquí: las funciones internas de ranking y construcción de respuesta.
"""
from __future__ import annotations

from pathlib import Path

from research_operator.core.ask import (
    build_answer,
    content_bonus,
    extract_snippet,
    fallback_score,
    rank_sources,
    role_bonus,
)


class TestRoleBonus:
    def test_ruta_reproducible_bonifica_project_doc(self):
        assert role_bonus("project_doc", ["ruta", "reproducible"]) == 4

    def test_metodologia_bonifica_pipeline(self):
        assert role_bonus("pipeline", ["metodologia"]) == 4

    def test_manuscrito_bonifica_manuscript(self):
        assert role_bonus("manuscript", ["manuscrito"]) == 4

    def test_sin_coincidencia_no_bonifica(self):
        assert role_bonus("source", ["cualquier", "cosa"]) == 0


class TestContentBonus:
    def test_cuenta_tokens_en_contenido(self, tmp_path: Path):
        (tmp_path / "doc.md").write_text("convivencia escolar y bienestar", encoding="utf-8")
        assert content_bonus(tmp_path, {"path": "doc.md"}, ["convivencia", "bienestar"]) == 6

    def test_extension_no_indexada_no_bonifica(self, tmp_path: Path):
        (tmp_path / "img.png").write_bytes(b"\x89PNG")
        assert content_bonus(tmp_path, {"path": "img.png"}, ["convivencia"]) == 0

    def test_archivo_inexistente_no_bonifica(self, tmp_path: Path):
        assert content_bonus(tmp_path, {"path": "no-existe.md"}, ["convivencia"]) == 0

    def test_path_invalido_no_rompe(self, tmp_path: Path):
        assert content_bonus(tmp_path, {"path": None}, ["convivencia"]) == 0


class TestFallbackScore:
    def test_project_doc_tres(self):
        assert fallback_score({"role": "project_doc"}) == 3

    def test_pipeline_dos(self):
        assert fallback_score({"role": "pipeline"}) == 2

    def test_manuscript_dos(self):
        assert fallback_score({"role": "manuscript"}) == 2

    def test_otro_uno(self):
        assert fallback_score({"role": "source"}) == 1


class TestRankSources:
    def test_ordena_por_score_y_luego_por_path(self, tmp_path: Path):
        (tmp_path / "convivencia.md").write_text("nada relevante aquí", encoding="utf-8")
        (tmp_path / "otro.md").write_text("nada relevante aquí", encoding="utf-8")
        sources = [
            {"path": "otro.md", "role": "source"},
            {"path": "convivencia.md", "role": "source"},
        ]
        ranked = rank_sources(tmp_path, sources, "convivencia")
        assert ranked[0]["path"] == "convivencia.md"

    def test_usa_fallback_score_si_no_hay_coincidencia(self, tmp_path: Path):
        sources = [{"path": "a.md", "role": "project_doc"}, {"path": "b.md", "role": "source"}]
        ranked = rank_sources(tmp_path, sources, "término sin relación")
        assert ranked[0]["path"] == "a.md"


class TestExtractSnippet:
    def test_recorta_alrededor_del_token(self, tmp_path: Path):
        path = tmp_path / "doc.md"
        path.write_text("x" * 100 + " convivencia escolar " + "y" * 100, encoding="utf-8")
        snippet = extract_snippet(path, "convivencia")
        assert "convivencia" in snippet

    def test_sin_coincidencia_devuelve_inicio(self, tmp_path: Path):
        path = tmp_path / "doc.md"
        path.write_text("contenido sin términos relevantes", encoding="utf-8")
        snippet = extract_snippet(path, "inexistente")
        assert snippet.startswith("contenido")

    def test_archivo_vacio(self, tmp_path: Path):
        path = tmp_path / "doc.md"
        path.write_text("", encoding="utf-8")
        assert extract_snippet(path, "algo") == "Archivo textual sin contenido legible."

    def test_archivo_inexistente(self, tmp_path: Path):
        assert extract_snippet(tmp_path / "no-existe.md", "algo") == "No fue posible leer este archivo como texto."


class TestBuildAnswer:
    def test_incluye_pregunta_perfil_y_fuentes(self):
        cfg = {"project": {"profile": "qualitative"}}
        answer = build_answer(cfg, "¿Qué es convivencia escolar?", [("doc.md", "un fragmento")])
        assert "Pregunta: ¿Qué es convivencia escolar?" in answer
        assert "Perfil del proyecto: qualitative" in answer
        assert "doc.md" in answer

    def test_perfil_por_defecto_si_falta(self):
        answer = build_answer({}, "pregunta", [])
        assert "mixed_methods" in answer
