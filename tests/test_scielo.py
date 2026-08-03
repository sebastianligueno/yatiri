from __future__ import annotations

from unittest.mock import MagicMock, patch

from research_operator.core.scielo import (
    build_scielo_article_url,
    clean_text,
    extract_objects,
    extract_year,
    extract_year_from_text,
    first_text,
    looks_relevant,
    nested_get,
    parse_articlemeta_object,
    parse_scielo_search_html,
    search_scielo,
    search_scielo_articlemeta,
    search_scielo_html,
    search_scielo_web,
    tokenize,
)
from research_operator.core.web_search import WebResult


def _mock_response(json_data=None, text: str = "") -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = json_data
    resp.text = text
    return resp


class TestFirstText:
    def test_toma_primer_string_no_vacio(self):
        assert first_text(None, "", "  ", "valor") == "valor"

    def test_extrae_de_lista(self):
        assert first_text(["", "de lista"]) == "de lista"

    def test_extrae_de_dict_anidado(self):
        assert first_text({"es": "", "en": "en inglés"}) == "en inglés"

    def test_todo_vacio_devuelve_none(self):
        assert first_text(None, "", []) is None


class TestNestedGet:
    def test_valor_directo(self):
        assert nested_get({"title": "X"}, "title") == "X"

    def test_valor_anidado_en_resource(self):
        assert nested_get({"resource": {"title": "Y"}}, "title") == "Y"

    def test_ausente_devuelve_none(self):
        assert nested_get({}, "title") is None


class TestExtractObjects:
    def test_extrae_de_clave_objects(self):
        assert extract_objects({"objects": [{"a": 1}]}) == [{"a": 1}]

    def test_extrae_de_lista_directa(self):
        assert extract_objects([{"a": 1}]) == [{"a": 1}]

    def test_payload_no_reconocido_devuelve_vacio(self):
        assert extract_objects("texto plano") == []


class TestParseArticlemetaObject:
    def test_parsea_objeto_completo(self):
        item = {
            "title": "Convivencia escolar en Chile",
            "abstract": "Un resumen sobre convivencia.",
            "doi": "10.1234/abc",
            "journal_title": "Revista X",
            "collection": "chl",
            "publication_year": "2021",
        }
        result = parse_articlemeta_object(item)
        assert result.title == "Convivencia escolar en Chile"
        assert result.doi == "10.1234/abc"
        assert result.url == "https://doi.org/10.1234/abc"
        assert result.year == "2021"

    def test_sin_titulo_devuelve_none(self):
        assert parse_articlemeta_object({}) is None

    def test_construye_url_desde_pid_si_no_hay_doi_ni_url(self):
        item = {"title": "Un artículo", "pid": "S0123", "collection": "chl"}
        result = parse_articlemeta_object(item)
        assert result.url == build_scielo_article_url("chl", "S0123")


class TestExtractYear:
    def test_extrae_de_publication_year(self):
        assert extract_year({"publication_year": "2019"}) == "2019"

    def test_extrae_de_texto_con_fecha(self):
        assert extract_year({"created": "2020-03-01"}) == "2020"

    def test_sin_anio_devuelve_none(self):
        assert extract_year({}) is None


class TestTokenizeAndRelevance:
    def test_tokenize_descarta_cortas(self):
        assert tokenize("la convivencia y el bienestar") == ["convivencia", "bienestar"]

    def test_looks_relevant_sin_tokens_es_true(self):
        from research_operator.core.scielo import SciELOResult
        r = SciELOResult(title="X", url="", snippet="", doi=None, journal=None, collection=None, year=None)
        assert looks_relevant(r, "") is True

    def test_looks_relevant_coincide_en_titulo(self):
        from research_operator.core.scielo import SciELOResult
        r = SciELOResult(title="Convivencia escolar", url="", snippet="", doi=None, journal=None, collection=None, year=None)
        assert looks_relevant(r, "convivencia") is True

    def test_looks_relevant_no_coincide(self):
        from research_operator.core.scielo import SciELOResult
        r = SciELOResult(title="Otro tema", url="", snippet="", doi=None, journal=None, collection=None, year=None)
        assert looks_relevant(r, "convivencia") is False


class TestCleanText:
    def test_quita_html_y_colapsa_espacios(self):
        assert clean_text("<p>Hola   mundo</p>") == "Hola mundo"


class TestExtractYearFromText:
    def test_encuentra_anio_en_texto(self):
        assert extract_year_from_text("publicado en 2018 por la revista") == "2018"

    def test_sin_anio_devuelve_none(self):
        assert extract_year_from_text("sin fecha aquí") is None


class TestSearchScieloArticlemeta:
    def test_parsea_resultados_relevantes(self):
        with patch("research_operator.core.scielo.requests") as mock_requests:
            mock_requests.get.return_value = _mock_response({
                "objects": [{"title": "Convivencia escolar", "abstract": "sobre convivencia"}]
            })
            results = search_scielo_articlemeta("convivencia")
            assert len(results) == 1

    def test_filtra_resultados_no_relevantes(self):
        with patch("research_operator.core.scielo.requests") as mock_requests:
            mock_requests.get.return_value = _mock_response({
                "objects": [{"title": "Tema totalmente distinto", "abstract": "nada que ver"}]
            })
            assert search_scielo_articlemeta("convivencia escolar") == []

    def test_error_de_red_continua_al_siguiente_candidato_y_devuelve_vacio(self):
        with patch("research_operator.core.scielo.requests") as mock_requests:
            mock_requests.get.side_effect = ConnectionError("sin red")
            assert search_scielo_articlemeta("x") == []


class TestParseScieloSearchHtml:
    def test_extrae_resultados_de_html(self):
        html = (
            '<a href="https://www.scielo.br/articulo">'
            "Convivencia y bienestar escolar en la escuela pública</a>"
            "Resumen del artículo con más contexto para el snippet local."
        )
        results = parse_scielo_search_html(html)
        assert len(results) == 1
        assert "Convivencia" in results[0].title

    def test_ignora_enlaces_no_scielo_ni_doi(self):
        html = '<a href="https://otrapagina.com/x">Un título largo cualquiera aquí</a>'
        assert parse_scielo_search_html(html) == []

    def test_ignora_titulos_muy_cortos(self):
        html = '<a href="https://scielo.cl/x">corto</a>'
        assert parse_scielo_search_html(html) == []


class TestSearchScieloHtml:
    def test_error_de_red_devuelve_vacio(self):
        with patch("research_operator.core.scielo.requests") as mock_requests:
            mock_requests.get.side_effect = TimeoutError("timeout")
            assert search_scielo_html("x") == []


class TestSearchScieloWeb:
    def test_se_queda_solo_con_dominios_scielo(self):
        web_results = [
            WebResult(title="Un paper en SciELO", url="https://scielo.cl/x", snippet="sobre 2020", domain="scielo.cl", source_type="academic"),
            WebResult(title="Otro resultado", url="https://otrapagina.com/x", snippet="nada que ver", domain="otrapagina.com", source_type="web"),
        ]
        with patch("research_operator.core.scielo.search_web", return_value=web_results):
            results = search_scielo_web("convivencia")
            assert len(results) == 1
            assert results[0].title == "Un paper en SciELO"
            assert results[0].year == "2020"

    def test_respeta_max_results(self):
        web_results = [
            WebResult(title=f"Paper {i}", url=f"https://scielo.br/{i}", snippet="", domain="scielo.br", source_type="academic")
            for i in range(5)
        ]
        with patch("research_operator.core.scielo.search_web", return_value=web_results):
            assert len(search_scielo_web("x", max_results=2)) == 2

    def test_sin_resultados_scielo_devuelve_vacio(self):
        web_results = [WebResult(title="X", url="https://otrapagina.com", snippet="", domain="otrapagina.com", source_type="web")]
        with patch("research_operator.core.scielo.search_web", return_value=web_results):
            assert search_scielo_web("x") == []


class TestSearchScielo:
    def test_sin_requests_instalado_devuelve_vacio(self):
        with patch("research_operator.core.scielo.requests", None):
            assert search_scielo("x") == []

    def test_usa_html_si_articlemeta_no_da_resultados(self):
        with patch("research_operator.core.scielo.requests") as mock_requests:
            empty = _mock_response({"objects": []})
            html_resp = _mock_response(text='<a href="https://scielo.cl/x">Un título suficientemente largo</a>')
            mock_requests.get.side_effect = [empty, empty, html_resp]
            results = search_scielo("consulta cualquiera")
            assert len(results) == 1

    def test_cae_a_web_si_articlemeta_y_html_no_dan_resultados(self):
        with patch("research_operator.core.scielo.requests") as mock_requests:
            empty = _mock_response({"objects": []})
            html_resp = _mock_response(text="<html>sin resultados</html>")
            mock_requests.get.side_effect = [empty, empty, html_resp]
            web_results = [
                WebResult(title="Un paper", url="https://scielo.cl/y", snippet="resumen", domain="scielo.cl", source_type="academic")
            ]
            with patch("research_operator.core.scielo.search_web", return_value=web_results):
                results = search_scielo("consulta cualquiera")
                assert len(results) == 1
                assert results[0].title == "Un paper"
