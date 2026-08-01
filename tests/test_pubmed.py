"""
Complementa test_core_search_filters.py::TestPubMed (que ya cubre los
parámetros de fecha en _esearch). Aquí: _extract_year, _esummary y el
flujo completo de search_pubmed.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from research_operator.core.pubmed import _esummary, _extract_year, search_pubmed


def _mock_response(json_data: dict) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = json_data
    return resp


class TestExtractYear:
    def test_extrae_anio_de_4_digitos(self):
        assert _extract_year("2020 Jan 15") == 2020

    def test_sin_anio_devuelve_none(self):
        assert _extract_year("fecha desconocida") is None


class TestEsummary:
    def test_parsea_resultado_con_autores(self):
        with patch("research_operator.core.pubmed._requests") as mock_requests:
            mock_requests.get.return_value = _mock_response({
                "result": {
                    "111": {
                        "title": "Convivencia escolar.",
                        "pubdate": "2020 Jan",
                        "authors": [{"name": "Pérez A"}, {"name": "Soto L"}],
                        "source": "Rev Psicol",
                    }
                }
            })
            results = _esummary(["111"])
            assert len(results) == 1
            r = results[0]
            assert r.title == "Convivencia escolar"  # sin punto final
            assert r.year == 2020
            assert "Pérez A et al." in r.snippet
            assert r.url == "https://pubmed.ncbi.nlm.nih.gov/111/"

    def test_item_con_error_se_descarta(self):
        with patch("research_operator.core.pubmed._requests") as mock_requests:
            mock_requests.get.return_value = _mock_response({"result": {"111": {"error": "not found"}}})
            assert _esummary(["111"]) == []

    def test_error_de_red_devuelve_vacio(self):
        with patch("research_operator.core.pubmed._requests") as mock_requests:
            mock_requests.get.side_effect = TimeoutError("timeout")
            assert _esummary(["111"]) == []


class TestSearchPubmed:
    def test_flujo_completo_esearch_a_esummary(self):
        with patch("research_operator.core.pubmed._requests") as mock_requests:
            esearch_resp = _mock_response({"esearchresult": {"idlist": ["111"]}})
            esummary_resp = _mock_response({"result": {"111": {"title": "X", "pubdate": "2020"}}})
            mock_requests.get.side_effect = [esearch_resp, esummary_resp]
            results = search_pubmed("burnout docente")
            assert len(results) == 1

    def test_sin_ids_no_llama_esummary(self):
        with patch("research_operator.core.pubmed._requests") as mock_requests:
            mock_requests.get.return_value = _mock_response({"esearchresult": {"idlist": []}})
            assert search_pubmed("x") == []
            assert mock_requests.get.call_count == 1

    def test_sin_requests_instalado_devuelve_vacio(self):
        with patch("research_operator.core.pubmed._requests", None):
            assert search_pubmed("x") == []
