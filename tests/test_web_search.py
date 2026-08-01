from __future__ import annotations

from unittest.mock import MagicMock, patch

from research_operator.core.web_search import (
    classify_source_type,
    extract_domain,
    parse_duckduckgo_html,
    search_web,
)

_DDG_HTML = """
<div class="result">
  <a class="result__a" href="https://scielo.cl/articulo">Convivencia escolar en Chile</a>
  <a class="result__snippet">Un estudio sobre convivencia y bienestar.</a>
</div>
"""


class TestParseDuckduckgoHtml:
    def test_extrae_titulo_url_y_snippet(self):
        results = parse_duckduckgo_html(_DDG_HTML)
        assert len(results) == 1
        r = results[0]
        assert r.title == "Convivencia escolar en Chile"
        assert r.url == "https://scielo.cl/articulo"
        assert "bienestar" in r.snippet
        assert r.source_type == "academic"

    def test_respeta_max_results(self):
        html = _DDG_HTML * 3
        results = parse_duckduckgo_html(html, max_results=2)
        assert len(results) == 2


class TestExtractDomain:
    def test_extrae_dominio_en_minusculas(self):
        assert extract_domain("https://WWW.Scielo.CL/x") == "www.scielo.cl"

    def test_url_invalida_devuelve_vacio(self):
        assert extract_domain(None) == ""


class TestClassifySourceType:
    def test_academico_por_dominio(self):
        assert classify_source_type("https://doi.org/10.1/x", "t", "s") == "academic"

    def test_institucional_por_dominio_gob(self):
        assert classify_source_type("https://mineduc.gob.cl/x", "t", "s") == "institutional"

    def test_legal_por_palabra_clave(self):
        assert classify_source_type("https://x.cl", "Nueva ley de convivencia", "s") == "legal"

    def test_prensa_por_dominio(self):
        assert classify_source_type("https://emol.com/x", "t", "s") == "press"

    def test_default_web(self):
        assert classify_source_type("https://blog-personal.com/x", "t", "s") == "web"


class TestSearchWeb:
    def test_error_de_red_devuelve_vacio(self):
        with patch("research_operator.core.web_search.requests") as mock_requests:
            mock_requests.get.side_effect = ConnectionError("sin red")
            assert search_web("consulta") == []

    def test_sin_requests_instalado_devuelve_vacio(self):
        with patch("research_operator.core.web_search.requests", None):
            assert search_web("consulta") == []

    def test_llama_a_duckduckgo_y_parsea(self):
        with patch("research_operator.core.web_search.requests") as mock_requests:
            resp = MagicMock()
            resp.raise_for_status.return_value = None
            resp.text = _DDG_HTML
            mock_requests.get.return_value = resp
            results = search_web("convivencia escolar")
            assert len(results) == 1
