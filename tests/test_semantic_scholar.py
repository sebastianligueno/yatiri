"""
Complementa test_core_search_filters.py::TestSemanticScholar (que ya
cubre el parámetro `year`). Aquí: parseo completo de resultados y URLs.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from research_operator.core.semantic_scholar import search_semantic_scholar


def _mock_response(json_data: dict) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = json_data
    return resp


class TestSearchSemanticScholar:
    def test_parsea_resultado_con_doi(self):
        with patch("research_operator.core.semantic_scholar._requests") as mock_requests:
            mock_requests.get.return_value = _mock_response({"data": [{
                "title": "Convivencia escolar",
                "abstract": "Un resumen " * 60,
                "year": 2019,
                "citationCount": 12,
                "authors": [{"name": "Ana Pérez"}, {"name": "Luis Soto"}],
                "externalIds": {"DOI": "10.1234/abc"},
                "openAccessPdf": {},
            }]})
            results = search_semantic_scholar("convivencia")
            assert len(results) == 1
            r = results[0]
            assert r.url == "https://doi.org/10.1234/abc"
            assert r.citations == 12
            assert "Ana Pérez et al." in r.snippet

    def test_sin_doi_usa_pdf_open_access(self):
        with patch("research_operator.core.semantic_scholar._requests") as mock_requests:
            mock_requests.get.return_value = _mock_response({"data": [{
                "title": "X",
                "externalIds": {},
                "openAccessPdf": {"url": "https://oa.example.org/x.pdf"},
            }]})
            results = search_semantic_scholar("x")
            assert results[0].url == "https://oa.example.org/x.pdf"

    def test_sin_doi_ni_pdf_usa_url_semantic_scholar(self):
        with patch("research_operator.core.semantic_scholar._requests") as mock_requests:
            mock_requests.get.return_value = _mock_response({"data": [{
                "title": "X", "paperId": "abc123", "externalIds": {}, "openAccessPdf": {},
            }]})
            results = search_semantic_scholar("x")
            assert results[0].url == "https://www.semanticscholar.org/paper/abc123"

    def test_sin_titulo_se_descarta(self):
        with patch("research_operator.core.semantic_scholar._requests") as mock_requests:
            mock_requests.get.return_value = _mock_response({"data": [{"title": ""}]})
            assert search_semantic_scholar("x") == []

    def test_error_de_red_devuelve_vacio(self):
        with patch("research_operator.core.semantic_scholar._requests") as mock_requests:
            mock_requests.get.side_effect = TimeoutError("timeout")
            assert search_semantic_scholar("x") == []

    def test_sin_requests_instalado_devuelve_vacio(self):
        with patch("research_operator.core.semantic_scholar._requests", None):
            assert search_semantic_scholar("x") == []
