"""
Cubre las funciones puras de core/advisor.py — el orquestador con más
lógica de negocio del proyecto y, hasta ahora, sin un solo test (0% cobertura).
No se prueba answer_session_query/review_project_brief completos porque
dependen de chat_completion (red); esas rutas quedan para tests con mocks
si se retoman más adelante.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from research_operator.core.advisor import (
    _is_health_query,
    _is_relevant,
    _is_topic_query,
    _title_key,
    build_search_queries,
    direct_answer_if_possible,
    extract_topic_phrase,
    fallback_response,
    mode_response,
    rank_attached_sources,
    simplify_query,
    synthesize_intro,
    tokenize,
)
from research_operator.core.session import SessionState


class TestTokenize:
    def test_descarta_palabras_cortas(self):
        assert tokenize("el la de TDAH y escuela") == ["tdah", "escuela"]

    def test_normaliza_a_minusculas(self):
        assert tokenize("Psicología SOCIAL") == ["psicología", "social"]


class TestIsTopicQuery:
    def test_consulta_corta_no_es_tema(self):
        assert _is_topic_query("hola") is False

    def test_pregunta_meta_no_es_tema(self):
        assert _is_topic_query("cómo uso yatiri para buscar") is False

    def test_consulta_academica_es_tema(self):
        assert _is_topic_query("convivencia escolar en educación parvularia") is True


class TestIsHealthQuery:
    def test_detecta_termino_clinico(self):
        assert _is_health_query("burnout docente en contexto escolar") is True

    def test_consulta_sin_terminos_clinicos(self):
        assert _is_health_query("historia de la psicología en Chile") is False


class TestTitleKey:
    def test_normaliza_puntuacion_y_mayusculas(self):
        assert _title_key("El TDAH: ¿medicalización?") == "eltdahmedicalización"

    def test_trunca_a_60(self):
        largo = "a" * 100
        assert len(_title_key(largo)) == 60


class TestIsRelevant:
    def test_sin_tokens_siempre_relevante(self):
        result = MagicMock(title="algo", snippet="", journal=None, url="")
        assert _is_relevant(result, []) is True

    def test_coincide_por_titulo(self):
        result = MagicMock(title="Convivencia escolar", snippet="", journal=None, url="")
        assert _is_relevant(result, ["convivencia"]) is True

    def test_no_coincide(self):
        result = MagicMock(title="Otro tema", snippet="", journal=None, url="")
        assert _is_relevant(result, ["convivencia"]) is False


class TestBuildSearchQueries:
    def test_arma_consulta_es_y_en(self):
        es, en = build_search_queries("bienestar docente")
        assert "bienestar docente" in es
        assert "psicología" in es
        assert "psychology" in en


class TestSimplifyQuery:
    def test_trunca_a_10_tokens(self):
        query = " ".join(f"palabra{i}larga" for i in range(15))
        assert len(simplify_query(query).split()) == 10

    def test_query_sin_tokens_devuelve_original(self):
        assert simplify_query("a e i") == "a e i"


class TestExtractTopicPhrase:
    def test_extrae_de_clase_de_n_minutos_sobre(self):
        assert extract_topic_phrase("clase de 90 minutos sobre sesgos cognitivos") == "sesgos cognitivos"

    def test_extrae_de_clase_sobre(self):
        assert extract_topic_phrase("clase sobre memoria de trabajo") == "memoria de trabajo"

    def test_sin_patron_devuelve_query_limpia(self):
        assert extract_topic_phrase("memoria de trabajo?") == "memoria de trabajo"


class TestSynthesizeIntro:
    def test_modo_conocido(self):
        assert "diseño" in synthesize_intro("quant").lower()

    def test_modo_desconocido_usa_default(self):
        assert synthesize_intro("inexistente") == "Modo general activo para consulta académica."


class TestModeResponse:
    def test_modo_teach_delega_a_teach_response(self):
        lines = mode_response("teach", "clase sobre atención")
        assert any("Aprendizaje esperado" in line for line in lines)

    def test_modo_general_da_sugerencia_generica(self):
        lines = mode_response("general", "algo")
        assert any("Sugerencia" in line for line in lines)


class TestRankAttachedSources:
    def test_prioriza_coincidencia_en_path_y_project_doc(self, tmp_path: Path):
        (tmp_path / "convivencia.md").write_text("texto sin relación", encoding="utf-8")
        (tmp_path / "otro.md").write_text("texto sin relación", encoding="utf-8")
        sources = [
            {"path": "otro.md", "role": "manuscript"},
            {"path": "convivencia.md", "role": "project_doc"},
        ]
        ranked = rank_attached_sources(tmp_path, sources, "convivencia escolar")
        assert ranked[0]["path"] == "convivencia.md"

    def test_source_sin_archivo_no_rompe(self, tmp_path: Path):
        sources = [{"path": "inexistente.md", "role": "manuscript"}]
        ranked = rank_attached_sources(tmp_path, sources, "consulta cualquiera")
        assert ranked[0]["path"] == "inexistente.md"


class TestDirectAnswerIfPossible:
    def test_ruta_reproducible_con_chunks(self):
        chunks = [("pipeline.py", "contenido")]
        respuesta = direct_answer_if_possible("general", "necesito una ruta reproducible", chunks, [])
        assert respuesta is not None
        assert "parquet" in respuesta

    def test_sin_coincidencia_devuelve_none(self):
        assert direct_answer_if_possible("general", "consulta cualquiera", [], []) is None

    def test_modo_search_con_resultados_arma_listado(self):
        item = MagicMock(source_type="academic", title="Un paper", url="https://x.org", snippet="resumen")
        respuesta = direct_answer_if_possible("search", "tema", [], [item])
        assert respuesta is not None
        assert "Un paper" in respuesta


class TestFallbackResponse:
    def test_incluye_diagnostico_si_hay_error_de_modelo(self):
        state = SessionState(mode="general")
        respuesta = fallback_response(state, "consulta cualquiera", [], [], "sin clave configurada")
        assert "Diagnóstico de modelo" in respuesta

    def test_sin_contexto_ni_error(self):
        state = SessionState(mode="teach")
        respuesta = fallback_response(state, "algo", [], [], None)
        assert "Sin contexto documental adjunto" in respuesta
