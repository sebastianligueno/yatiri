"""
Complementa test_core_search_filters.py::TestCrossRef (que ya cubre los
filtros de año). Aquí: filtrado de títulos basura, límite de resultados,
_extract_year y _format_authors.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from research_operator.core.crossref import _extract_year, _format_authors, search_crossref


def _mock_response(json_data: dict) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = json_data
    return resp


def _item(**overrides) -> dict:
    base = {
        "title": ["Convivencia escolar en Chile: un análisis"],
        "DOI": "10.1234/x",
        "container-title": ["Revista X"],
        "published": {"date-parts": [[2021]]},
        "author": [{"family": "Pérez", "given": "Ana"}],
        "abstract": "Un resumen suficientemente largo para no descartarse.",
    }
    base.update(overrides)
    return base


class TestSearchCrossrefFiltrado:
    def test_sin_requests_instalado_devuelve_vacio(self):
        with patch("research_operator.core.crossref.requests", None):
            assert search_crossref("x") == []

    def test_error_de_red_devuelve_vacio(self):
        with patch("research_operator.core.crossref.requests") as mock_requests:
            mock_requests.get.side_effect = ConnectionError("sin red")
            assert search_crossref("x") == []

    def test_descarta_sin_titulo(self):
        with patch("research_operator.core.crossref.requests") as mock_requests:
            mock_requests.get.return_value = _mock_response({"message": {"items": [_item(title=[])]}})
            assert search_crossref("x") == []

    def test_descarta_titulos_basura(self):
        with patch("research_operator.core.crossref.requests") as mock_requests:
            mock_requests.get.return_value = _mock_response({
                "message": {"items": [_item(title=["References"])]}
            })
            assert search_crossref("x") == []

    def test_descarta_capitulo_sin_abstract_y_titulo_corto(self):
        with patch("research_operator.core.crossref.requests") as mock_requests:
            mock_requests.get.return_value = _mock_response({
                "message": {"items": [_item(title=["Un capítulo"], abstract="")]}
            })
            assert search_crossref("x") == []

    def test_titulo_corto_pero_con_abstract_se_conserva(self):
        with patch("research_operator.core.crossref.requests") as mock_requests:
            mock_requests.get.return_value = _mock_response({
                "message": {"items": [_item(title=["Un capítulo"])]}
            })
            assert len(search_crossref("x")) == 1

    def test_respeta_max_results(self):
        with patch("research_operator.core.crossref.requests") as mock_requests:
            items = [_item(title=[f"Un tema académico número {i}"]) for i in range(5)]
            mock_requests.get.return_value = _mock_response({"message": {"items": items}})
            assert len(search_crossref("x", max_results=2)) == 2


class TestExtractYear:
    def test_extrae_primer_anio(self):
        assert _extract_year({"date-parts": [[2020, 5]]}) == "2020"

    def test_sin_published_devuelve_none(self):
        assert _extract_year(None) is None

    def test_date_parts_vacio_devuelve_none(self):
        assert _extract_year({"date-parts": [[]]}) is None


class TestFormatAuthors:
    def test_sin_autores_devuelve_none(self):
        assert _format_authors([]) is None

    def test_formatea_apellido_e_iniciales(self):
        assert _format_authors([{"family": "Pérez", "given": "Ana María"}]) == "Pérez, A. M."

    def test_agrega_et_al_si_hay_mas_de_tres(self):
        authors = [{"family": f"Autor{i}", "given": "X"} for i in range(5)]
        result = _format_authors(authors)
        assert result.endswith("et al.")

    def test_autor_sin_given_solo_apellido(self):
        assert _format_authors([{"family": "Pérez"}]) == "Pérez"
