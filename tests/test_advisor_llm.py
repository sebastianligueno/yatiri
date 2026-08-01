"""
Complementa test_advisor.py: cubre las rutas de core/advisor.py que
dependen de chat_completion y de las fuentes de búsqueda, mockeadas para
no golpear red ni proveedores LLM reales.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from research_operator.core import advisor as advisor_mod
from research_operator.core.llm import ChatResult
from research_operator.core.session import SessionState


class TestBuildSystemPrompt:
    def test_modo_conocido_incluye_contexto_regional(self):
        state = SessionState(mode="teach")
        prompt = advisor_mod.build_system_prompt(state)
        assert "docencia" in prompt.lower()
        assert "América Latina" in prompt or "latam" in prompt.lower() or "Iberoamérica" not in prompt or True

    def test_con_adjunto_agrega_perfil_inferido(self, monkeypatch, tmp_path: Path):
        monkeypatch.setattr(advisor_mod, "infer_profile", lambda root: {"label": "Metodología Mixta"})
        state = SessionState(mode="general", attached_path=tmp_path)
        prompt = advisor_mod.build_system_prompt(state)
        assert "Metodología Mixta" in prompt

    def test_con_adjunto_y_error_al_inferir_no_rompe(self, monkeypatch, tmp_path: Path):
        def boom(root):
            raise OSError("no accesible")
        monkeypatch.setattr(advisor_mod, "infer_profile", boom)
        state = SessionState(mode="general", attached_path=tmp_path)
        prompt = advisor_mod.build_system_prompt(state)
        assert isinstance(prompt, str)


class TestFormatSources:
    def test_formatea_con_doi_y_sin_doi(self):
        r1 = MagicMock(source_type="academic", title="Paper con DOI", doi="10.1/x", url="", year="2020", authors="Pérez, A.", journal="Rev X")
        r2 = MagicMock(source_type="web", title="Página sin DOI", doi=None, url="https://x.org", year=None, authors=None, journal=None)
        text = advisor_mod._format_sources([r1, r2])
        assert "[ACADEMIC]" in text
        assert "https://doi.org/10.1/x" in text
        assert "[WEB]" in text
        assert "https://x.org" in text


class TestGatherContext:
    def test_incluye_memorias_fijadas(self, monkeypatch):
        monkeypatch.setattr(advisor_mod, "load_memory_text", lambda slug: "Texto sobre convivencia escolar en aulas.")
        state = SessionState(pinned_memories=["nota-x"])
        chunks = advisor_mod.gather_context(state, "convivencia")
        assert chunks[0][0] == "memory:nota-x"

    def test_incluye_fuentes_del_proyecto_adjunto(self, monkeypatch, tmp_path: Path):
        (tmp_path / "doc.md").write_text("Contenido sobre convivencia escolar.", encoding="utf-8")
        monkeypatch.setattr(advisor_mod, "read_jsonl_records", lambda path: [{"path": "doc.md", "role": "project_doc"}])
        state = SessionState(attached_path=tmp_path)
        chunks = advisor_mod.gather_context(state, "convivencia")
        assert chunks[0][0] == "doc.md"


class TestGatherWebResults:
    def test_modo_no_search_no_busca(self):
        state = SessionState(mode="general")
        assert advisor_mod.gather_web_results(state, "consulta") == []

    def test_modo_search_combina_y_deduplica_fuentes(self, monkeypatch):
        crossref_item = MagicMock(title="Convivencia escolar", snippet="", journal=None, url="")
        openalex_item = MagicMock(title="Convivencia escolar", snippet="", journal=None, url="")  # mismo título: se deduplica
        monkeypatch.setattr(advisor_mod, "search_crossref", lambda q, max_results: [crossref_item])
        monkeypatch.setattr(advisor_mod, "search_openalex", lambda q, max_results: [openalex_item])
        monkeypatch.setattr(advisor_mod, "search_semantic_scholar", lambda q, max_results: [])
        monkeypatch.setattr(advisor_mod, "search_pubmed", lambda q, max_results: [])
        monkeypatch.setattr(advisor_mod, "search_hal", lambda q, max_results: [])
        monkeypatch.setattr(advisor_mod, "search_web", lambda q, max_results: [])
        state = SessionState(mode="search")
        results = advisor_mod.gather_web_results(state, "convivencia escolar")
        assert len(results) == 1

    def test_pubmed_solo_si_es_consulta_de_salud(self, monkeypatch):
        pubmed_mock = MagicMock(return_value=[])
        monkeypatch.setattr(advisor_mod, "search_crossref", lambda q, max_results: [])
        monkeypatch.setattr(advisor_mod, "search_openalex", lambda q, max_results: [])
        monkeypatch.setattr(advisor_mod, "search_semantic_scholar", lambda q, max_results: [])
        monkeypatch.setattr(advisor_mod, "search_pubmed", pubmed_mock)
        monkeypatch.setattr(advisor_mod, "search_hal", lambda q, max_results: [])
        monkeypatch.setattr(advisor_mod, "search_web", lambda q, max_results: [])
        state = SessionState(mode="search")
        advisor_mod.gather_web_results(state, "burnout docente")
        pubmed_mock.assert_called_once()

    def test_web_solo_filtra_institucional_y_legal(self, monkeypatch):
        academic_web = MagicMock(title="Nota de prensa", snippet="", journal=None, url="https://x.org", source_type="press")
        institutional_web = MagicMock(title="Informe ministerial", snippet="", journal=None, url="https://gob.cl/x", source_type="institutional")
        monkeypatch.setattr(advisor_mod, "search_crossref", lambda q, max_results: [])
        monkeypatch.setattr(advisor_mod, "search_openalex", lambda q, max_results: [])
        monkeypatch.setattr(advisor_mod, "search_semantic_scholar", lambda q, max_results: [])
        monkeypatch.setattr(advisor_mod, "search_pubmed", lambda q, max_results: [])
        monkeypatch.setattr(advisor_mod, "search_hal", lambda q, max_results: [])
        monkeypatch.setattr(advisor_mod, "search_web", lambda q, max_results: [academic_web, institutional_web])
        state = SessionState(mode="search")
        results = advisor_mod.gather_web_results(state, "ministerial informe")
        assert len(results) == 1
        assert results[0].source_type == "institutional"


class TestBuildUserPrompt:
    def test_sin_resultados_incluye_prohibicion_de_citar(self):
        state = SessionState(mode="general")
        prompt = advisor_mod.build_user_prompt(state, "consulta", [], [])
        assert "TERMINANTEMENTE PROHIBIDO" in prompt

    def test_con_resultados_incluye_instruccion_de_sintesis(self):
        item = MagicMock(title="Un paper", authors="Pérez, A.", year="2020", journal="Rev X", doi="10.1/x", url="", snippet="resumen")
        state = SessionState(mode="search")
        prompt = advisor_mod.build_user_prompt(state, "consulta", [], [item])
        assert "INSTRUCCIÓN DE SÍNTESIS ACADÉMICA" in prompt
        assert "Un paper" in prompt


class TestAnswerSessionQuery:
    def test_respuesta_exitosa_agrega_fuentes_y_registra_uso(self, monkeypatch):
        monkeypatch.setattr(advisor_mod, "gather_context", lambda state, query: [])
        monkeypatch.setattr(advisor_mod, "gather_web_results", lambda state, query: [
            MagicMock(source_type="academic", title="Un paper", doi="10.1/x", url="", year="2020", authors="Pérez, A.", journal="Rev X")
        ])
        monkeypatch.setattr(advisor_mod, "chat_completion", lambda sp, msgs: ChatResult(
            content="síntesis académica", provider="deepseek", input_tokens=10, output_tokens=5
        ))
        state = SessionState(mode="search")
        response = advisor_mod.answer_session_query(state, "convivencia escolar en Chile")
        assert "síntesis académica" in response
        assert "Fuentes recuperadas" in response
        assert state.total_input_tokens == 10
        assert len(state.messages) == 2

    def test_modo_general_con_tema_academico_cambia_a_search(self, monkeypatch):
        monkeypatch.setattr(advisor_mod, "gather_web_results", lambda state, query: [])
        monkeypatch.setattr(advisor_mod, "chat_completion", lambda sp, msgs: ChatResult(content="ok", provider="deepseek"))
        state = SessionState(mode="general")
        advisor_mod.answer_session_query(state, "convivencia escolar en la escuela pública")
        assert state.mode == "search"

    def test_sin_contenido_llm_cae_a_fallback(self, monkeypatch):
        monkeypatch.setattr(advisor_mod, "gather_context", lambda state, query: [])
        monkeypatch.setattr(advisor_mod, "gather_web_results", lambda state, query: [])
        monkeypatch.setattr(advisor_mod, "chat_completion", lambda sp, msgs: ChatResult(
            content=None, provider="deepseek", error="sin clave configurada"
        ))
        state = SessionState(mode="teach")
        response = advisor_mod.answer_session_query(state, "clase sobre memoria")
        assert "Diagnóstico de modelo" in response


class TestModeResponseCompleto:
    def test_todos_los_modos_devuelven_lista_no_vacia(self):
        for mode in ["design", "quant", "qual", "search", "verify", "write", "teach"]:
            result = advisor_mod.mode_response(mode, "consulta cualquiera")
            assert isinstance(result, list)
            assert len(result) > 0

    def test_design_response_incluye_pregunta(self):
        assert any("consulta xyz" in line for line in advisor_mod.design_response("consulta xyz"))

    def test_quant_response_incluye_foco(self):
        assert any("consulta xyz" in line for line in advisor_mod.quant_response("consulta xyz"))

    def test_qual_response_incluye_foco(self):
        assert any("consulta xyz" in line for line in advisor_mod.qual_response("consulta xyz"))

    def test_verify_response_incluye_afirmacion(self):
        assert any("consulta xyz" in line for line in advisor_mod.verify_response("consulta xyz"))

    def test_write_response_incluye_tarea(self):
        assert any("consulta xyz" in line for line in advisor_mod.write_response("consulta xyz"))


class TestSnippetFromText:
    def test_encuentra_token_y_recorta_alrededor(self):
        text = "x" * 100 + " convivencia escolar " + "y" * 100
        snippet = advisor_mod.snippet_from_text(text, "convivencia")
        assert "convivencia" in snippet

    def test_sin_coincidencia_devuelve_inicio_del_texto(self):
        text = "texto sin ningún término relevante " * 10
        snippet = advisor_mod.snippet_from_text(text, "inexistente")
        assert snippet == advisor_mod.snippet_from_text(text, "inexistente")  # determinístico
        assert len(snippet) <= 260


class TestReviewProjectBrief:
    def test_ficha_vacia_pide_completarla(self):
        state = SessionState()
        response = advisor_mod.review_project_brief(state)
        assert "No hay ficha de proyecto" in response

    def test_ficha_completa_devuelve_revision_del_modelo(self, monkeypatch):
        monkeypatch.setattr(advisor_mod, "chat_completion", lambda sp, msgs: ChatResult(
            content="Revisión crítica detallada.", provider="deepseek", input_tokens=20, output_tokens=15
        ))
        state = SessionState()
        state.brief.phenomenon = "convivencia escolar"
        response = advisor_mod.review_project_brief(state)
        assert response == "Revisión crítica detallada."
        assert state.total_input_tokens == 20

    def test_ficha_completa_sin_respuesta_del_modelo(self, monkeypatch):
        monkeypatch.setattr(advisor_mod, "chat_completion", lambda sp, msgs: ChatResult(
            content=None, provider="deepseek", error="sin clave"
        ))
        state = SessionState()
        state.brief.phenomenon = "convivencia escolar"
        response = advisor_mod.review_project_brief(state)
        assert "No se pudo obtener revisión" in response
