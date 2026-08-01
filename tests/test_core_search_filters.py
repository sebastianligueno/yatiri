"""
Cubre el cambio del 2026-07-31: se agregó year_from/year_to a crossref,
openalex, pubmed y semantic_scholar. Dos cosas importan:

1. Compatibilidad hacia atrás: llamar sin year_from/year_to (como hace
   core/advisor.py hoy) no debe agregar ningún filtro de fecha a la
   petición HTTP — si esto se rompe, advisor.py empieza a filtrar de
   más sin que nadie lo pida.
2. Los filtros, cuando se piden, viajan en el formato que cada API
   externa espera.

No se golpea la red: se reemplaza requests.get por un doble que devuelve
una respuesta mínima con la forma real de cada API (capturada con curl
contra las APIs en vivo antes de escribir esto).
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from research_operator.core.crossref import search_crossref
from research_operator.core.openalex import _build_filter, search_openalex
from research_operator.core.pubmed import _esearch
from research_operator.core.semantic_scholar import search_semantic_scholar


def _mock_response(json_data: dict) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = json_data
    return resp


CROSSREF_ITEM = {
    "title": ["Un título de prueba"],
    "DOI": "10.1234/prueba",
    "container-title": ["Revista de Prueba"],
    "published": {"date-parts": [[2021]]},
    "author": [{"family": "Pérez", "given": "Ana"}],
    "abstract": "Un resumen suficientemente largo para no ser descartado como metadata.",
}


class TestCrossRef:
    def test_sin_filtro_de_anio_no_agrega_parametro_filter(self):
        with patch("research_operator.core.crossref.requests") as mock_requests:
            mock_requests.get.return_value = _mock_response(
                {"message": {"items": [CROSSREF_ITEM]}}
            )
            results = search_crossref("prueba")
            params = mock_requests.get.call_args.kwargs["params"]
            assert "filter" not in params
            assert len(results) == 1

    def test_con_year_from_y_year_to_arma_filter_correcto(self):
        with patch("research_operator.core.crossref.requests") as mock_requests:
            mock_requests.get.return_value = _mock_response(
                {"message": {"items": [CROSSREF_ITEM]}}
            )
            search_crossref("prueba", year_from=2020, year_to=2022)
            params = mock_requests.get.call_args.kwargs["params"]
            assert params["filter"] == "from-pub-date:2020-01-01,until-pub-date:2022-12-31"

    def test_solo_year_from(self):
        with patch("research_operator.core.crossref.requests") as mock_requests:
            mock_requests.get.return_value = _mock_response(
                {"message": {"items": [CROSSREF_ITEM]}}
            )
            search_crossref("prueba", year_from=2020)
            params = mock_requests.get.call_args.kwargs["params"]
            assert params["filter"] == "from-pub-date:2020-01-01"


class TestOpenAlex:
    def test_build_filter_default_preserva_idioma_es(self):
        # Antes del fix, "language:es" estaba hardcodeado; ahora debe
        # seguir siendo el default para no cambiar el comportamiento de
        # advisor.py, que llama a search_openalex sin especificar idioma.
        assert _build_filter("cualquier consulta") == "language:es"

    def test_build_filter_permite_desactivar_idioma(self):
        assert "language" not in _build_filter("consulta", language=None)

    def test_build_filter_agrega_rango_de_fechas(self):
        f = _build_filter("consulta", year_from=2020, year_to=2022)
        assert "from_publication_date:2020-01-01" in f
        assert "to_publication_date:2022-12-31" in f

    def test_search_openalex_sin_filtro_de_anio(self):
        with patch("research_operator.core.openalex.requests") as mock_requests:
            mock_requests.get.return_value = _mock_response({"results": []})
            search_openalex("prueba")
            params = mock_requests.get.call_args.kwargs["params"]
            assert "publication_date" not in params["filter"]


class TestPubMed:
    def test_esearch_sin_fechas_no_agrega_datetype(self):
        with patch("research_operator.core.pubmed._requests") as mock_requests:
            mock_requests.get.return_value = _mock_response(
                {"esearchresult": {"idlist": []}}
            )
            _esearch("prueba", 5)
            params = mock_requests.get.call_args.kwargs["params"]
            assert "datetype" not in params
            assert "mindate" not in params

    def test_esearch_con_year_from_agrega_mindate(self):
        with patch("research_operator.core.pubmed._requests") as mock_requests:
            mock_requests.get.return_value = _mock_response(
                {"esearchresult": {"idlist": []}}
            )
            _esearch("prueba", 5, year_from=2020)
            params = mock_requests.get.call_args.kwargs["params"]
            assert params["datetype"] == "pdat"
            assert params["mindate"] == "2020"
            assert params["maxdate"] == "3000"


class TestSemanticScholar:
    def test_sin_filtro_de_anio_no_agrega_parametro_year(self):
        with patch("research_operator.core.semantic_scholar._requests") as mock_requests:
            mock_requests.get.return_value = _mock_response({"data": []})
            search_semantic_scholar("prueba")
            params = mock_requests.get.call_args.kwargs["params"]
            assert "year" not in params

    def test_con_rango_de_anios_arma_parametro_year(self):
        with patch("research_operator.core.semantic_scholar._requests") as mock_requests:
            mock_requests.get.return_value = _mock_response({"data": []})
            search_semantic_scholar("prueba", year_from=2020, year_to=2022)
            params = mock_requests.get.call_args.kwargs["params"]
            assert params["year"] == "2020-2022"
