"""
Complementa test_core_search_filters.py::TestOpenAlex (que ya cubre
_build_filter y el caso sin resultados). Aquí: parseo completo de
resultados, reintento sin país, reconstrucción de abstract y autores.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from research_operator.core.openalex import _format_authors, _reconstruct_abstract, search_openalex


def _mock_response(json_data: dict) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = json_data
    return resp


_ITEM = {
    "title": "Convivencia escolar en Chile",
    "doi": "https://doi.org/10.1234/abc",
    "publication_year": 2021,
    "primary_location": {"source": {"display_name": "Revista de Educación"}},
    "open_access": {"oa_url": "https://oa.example.org/pdf"},
    "abstract_inverted_index": {"Un": [0], "resumen": [1], "breve": [2]},
    "authorships": [
        {"author": {"display_name": "Ana Pérez"}},
        {"author": {"display_name": "Luis Soto"}},
    ],
}


class TestReconstructAbstract:
    def test_reconstruye_orden_original(self):
        assert _reconstruct_abstract({"Un": [0], "resumen": [1], "breve": [2]}) == "Un resumen breve"

    def test_vacio_devuelve_vacio(self):
        assert _reconstruct_abstract(None) == ""

    def test_indice_malformado_no_rompe(self):
        assert _reconstruct_abstract("no es un dict") == ""


class TestFormatAuthors:
    def test_formatea_hasta_tres_autores(self):
        authorships = [{"author": {"display_name": f"Autor {i}"}} for i in range(2)]
        assert _format_authors(authorships) == "Autor 0; Autor 1"

    def test_agrega_et_al_si_hay_mas_de_tres(self):
        authorships = [{"author": {"display_name": f"Autor {i}"}} for i in range(5)]
        result = _format_authors(authorships)
        assert result.endswith("et al.")

    def test_sin_autores_devuelve_none(self):
        assert _format_authors([]) is None


class TestSearchOpenalex:
    def test_parsea_resultado_completo(self):
        with patch("research_operator.core.openalex.requests") as mock_requests:
            mock_requests.get.return_value = _mock_response({"results": [_ITEM]})
            results = search_openalex("convivencia")
            assert len(results) == 1
            r = results[0]
            assert r.title == "Convivencia escolar en Chile"
            assert r.doi == "10.1234/abc"
            assert r.url == "https://oa.example.org/pdf"
            assert r.journal == "Revista de Educación"
            assert r.authors == "Ana Pérez; Luis Soto"
            assert r.snippet == "Un resumen breve"

    def test_sin_titulo_se_descarta(self):
        with patch("research_operator.core.openalex.requests") as mock_requests:
            mock_requests.get.return_value = _mock_response({"results": [{"title": ""}]})
            assert search_openalex("x") == []

    def test_reintenta_sin_pais_si_no_hay_resultados(self):
        with patch("research_operator.core.openalex.requests") as mock_requests:
            first = _mock_response({"results": []})
            second = _mock_response({"results": [_ITEM]})
            mock_requests.get.side_effect = [first, second]
            results = search_openalex("psicología en Chile", language="es")
            assert len(results) == 1
            second_call_params = mock_requests.get.call_args.kwargs["params"]
            assert "country_code" not in second_call_params["filter"]

    def test_reintento_con_error_de_red_devuelve_vacio(self):
        with patch("research_operator.core.openalex.requests") as mock_requests:
            first = _mock_response({"results": []})
            mock_requests.get.side_effect = [first, ConnectionError("sin red")]
            assert search_openalex("psicología en Chile", language="es") == []

    def test_error_de_red_en_primer_intento_devuelve_vacio(self):
        with patch("research_operator.core.openalex.requests") as mock_requests:
            mock_requests.get.side_effect = ConnectionError("sin red")
            assert search_openalex("x") == []

    def test_sin_requests_instalado_devuelve_vacio(self):
        with patch("research_operator.core.openalex.requests", None):
            assert search_openalex("x") == []

    def test_doi_url_por_defecto_sin_open_access(self):
        item = dict(_ITEM, open_access={})
        with patch("research_operator.core.openalex.requests") as mock_requests:
            mock_requests.get.return_value = _mock_response({"results": [item]})
            results = search_openalex("x")
            assert results[0].url == "https://doi.org/10.1234/abc"
