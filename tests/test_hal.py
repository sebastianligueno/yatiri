from __future__ import annotations

from unittest.mock import MagicMock, patch

from research_operator.core.hal import _extract_year, search_hal


def _mock_response(json_data: dict) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = json_data
    return resp


class TestExtractYear:
    def test_extrae_anio_de_fecha_valida(self):
        assert _extract_year("2020-05-01") == 2020

    def test_fecha_vacia_devuelve_none(self):
        assert _extract_year("") is None

    def test_fecha_corta_devuelve_none(self):
        assert _extract_year("202") is None


class TestSearchHal:
    def test_parsea_resultado_completo(self):
        with patch("research_operator.core.hal._requests") as mock_requests:
            mock_requests.get.return_value = _mock_response({
                "response": {"docs": [{
                    "title_s": ["Convivencia escolar"],
                    "uri_s": "https://hal.science/x",
                    "abstract_s": ["Un resumen amplio " * 30],
                    "authFullName_s": ["Ana Pérez", "Luis Soto"],
                    "producedDate_tdate": "2019-01-01",
                }]}
            })
            results = search_hal("convivencia")
            assert len(results) == 1
            r = results[0]
            assert r.title == "Convivencia escolar"
            assert r.year == 2019
            assert "Ana Pérez et al." in r.snippet

    def test_sin_titulo_se_descarta(self):
        with patch("research_operator.core.hal._requests") as mock_requests:
            mock_requests.get.return_value = _mock_response({"response": {"docs": [{"title_s": []}]}})
            assert search_hal("x") == []

    def test_error_de_red_devuelve_vacio(self):
        with patch("research_operator.core.hal._requests") as mock_requests:
            mock_requests.get.side_effect = TimeoutError("timeout")
            assert search_hal("x") == []

    def test_sin_requests_instalado_devuelve_vacio(self):
        with patch("research_operator.core.hal._requests", None):
            assert search_hal("x") == []
