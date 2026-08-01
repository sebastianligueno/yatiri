"""
Cubre el flujo completo de multi_source_search en mcp_server.py: dedupe
entre fuentes, caché en memoria, formato markdown/json, fuentes
desconocidas, manejo de errores por fuente y enriquecimiento SciELO.
_dedupe_key/_normalize_doi/_normalize_title ya están cubiertos en
test_mcp_server_dedupe.py.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from research_operator import mcp_server as mcp_mod
from research_operator.core.crossref import CrossRefResult
from research_operator.core.openalex import OpenAlexResult


def _crossref(title="Un paper", doi="10.1234/abc", **kw):
    return CrossRefResult(
        title=title, url=f"https://doi.org/{doi}", snippet="resumen", doi=doi,
        journal="Revista X", year="2020", authors="Pérez, A.", **kw,
    )


def _openalex(title="Un paper", doi="10.1234/abc", **kw):
    return OpenAlexResult(
        title=title, url=f"https://doi.org/{doi}", snippet="resumen oa", doi=doi,
        journal="Revista X", year="2020", authors="Pérez, A.", **kw,
    )


@pytest.fixture(autouse=True)
def _clear_cache(monkeypatch):
    monkeypatch.setattr(mcp_mod, "_cache", {})


def _patch_sources(monkeypatch, **funcs):
    for name, fn in funcs.items():
        monkeypatch.setitem(mcp_mod._SOURCES, name, fn)


class TestFuentesDesconocidas:
    def test_fuente_invalida_devuelve_mensaje_de_error(self):
        result = mcp_mod.multi_source_search("x", sources=["no-existe"])
        assert "Fuentes desconocidas" in result


class TestDedupeYFusion:
    def test_mismo_doi_en_dos_fuentes_se_fusiona(self, monkeypatch):
        _patch_sources(
            monkeypatch,
            crossref=lambda query, **kw: [_crossref()],
            openalex=lambda query, **kw: [_openalex()],
        )
        result = mcp_mod.multi_source_search("x", sources=["crossref", "openalex"])
        assert "Total de resultados únicos: 1" in result
        assert "crossref, openalex" in result

    def test_titulos_distintos_no_se_fusionan(self, monkeypatch):
        _patch_sources(
            monkeypatch,
            crossref=lambda query, **kw: [_crossref(title="Paper A", doi="10.1/a")],
            openalex=lambda query, **kw: [_openalex(title="Paper B", doi="10.1/b")],
        )
        result = mcp_mod.multi_source_search("x", sources=["crossref", "openalex"])
        assert "Total de resultados únicos: 2" in result


class TestEstadoPorFuente:
    def test_fuente_sin_resultados_se_reporta(self, monkeypatch):
        _patch_sources(monkeypatch, crossref=lambda query, **kw: [])
        result = mcp_mod.multi_source_search("x", sources=["crossref"])
        assert "[crossref] Sin resultados." in result

    def test_fuente_con_excepcion_se_reporta_como_error(self, monkeypatch):
        def boom(query, **kw):
            raise ConnectionError("sin red")
        _patch_sources(monkeypatch, crossref=boom)
        result = mcp_mod.multi_source_search("x", sources=["crossref"])
        assert "[crossref] Error: ConnectionError: sin red" in result


class TestFiltrosDeAnio:
    def test_year_filter_solo_a_fuentes_soportadas(self, monkeypatch):
        crossref_mock = MagicMock(return_value=[])
        hal_mock = MagicMock(return_value=[])
        _patch_sources(monkeypatch, crossref=crossref_mock, hal=hal_mock)
        mcp_mod.multi_source_search("x", sources=["crossref", "hal"], year_from=2020, year_to=2022)
        assert crossref_mock.call_args.kwargs.get("year_from") == 2020
        assert "year_from" not in hal_mock.call_args.kwargs


class TestFormatoRespuesta:
    def test_json_incluye_campos_esperados(self, monkeypatch):
        _patch_sources(monkeypatch, crossref=lambda query, **kw: [_crossref()])
        result = mcp_mod.multi_source_search("x", sources=["crossref"], response_format="json")
        payload = json.loads(result)
        assert payload["query"] == "x"
        assert payload["results"][0]["doi"] == "10.1234/abc"
        assert payload["results"][0]["sources"] == ["crossref"]


class TestCache:
    def test_misma_consulta_no_vuelve_a_golpear_la_fuente(self, monkeypatch):
        mock_fn = MagicMock(return_value=[_crossref()])
        _patch_sources(monkeypatch, crossref=mock_fn)
        mcp_mod.multi_source_search("misma consulta", sources=["crossref"])
        mcp_mod.multi_source_search("misma consulta", sources=["crossref"])
        assert mock_fn.call_count == 1

    def test_consulta_distinta_si_vuelve_a_llamar(self, monkeypatch):
        mock_fn = MagicMock(return_value=[_crossref()])
        _patch_sources(monkeypatch, crossref=mock_fn)
        mcp_mod.multi_source_search("consulta a", sources=["crossref"])
        mcp_mod.multi_source_search("consulta b", sources=["crossref"])
        assert mock_fn.call_count == 2


class TestEnrichScieloCitations:
    def test_agrega_conteo_de_citas_scielo(self, monkeypatch):
        _patch_sources(monkeypatch, crossref=lambda query, **kw: [_crossref()])
        monkeypatch.setattr(mcp_mod, "_scielo_citing_count", lambda title: 7)
        result = mcp_mod.multi_source_search("x", sources=["crossref"], enrich_scielo_citations=True)
        assert "Citado por artículos SciELO: 7" in result

    def test_json_incluye_scielo_cited_by(self, monkeypatch):
        _patch_sources(monkeypatch, crossref=lambda query, **kw: [_crossref()])
        monkeypatch.setattr(mcp_mod, "_scielo_citing_count", lambda title: 3)
        result = mcp_mod.multi_source_search(
            "x", sources=["crossref"], response_format="json", enrich_scielo_citations=True
        )
        payload = json.loads(result)
        assert payload["results"][0]["scielo_cited_by"] == 3


class TestScieloCitingCount:
    def test_sin_requests_devuelve_none(self, monkeypatch):
        monkeypatch.setattr(mcp_mod, "requests", None)
        assert mcp_mod._scielo_citing_count("un título") is None

    def test_error_de_red_devuelve_none(self, monkeypatch):
        mock_requests = MagicMock()
        mock_requests.get.side_effect = TimeoutError("timeout")
        monkeypatch.setattr(mcp_mod, "requests", mock_requests)
        assert mcp_mod._scielo_citing_count("un título") is None

    def test_respuesta_exitosa_devuelve_total(self, monkeypatch):
        mock_requests = MagicMock()
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = {"article": {"total_received": 5}}
        mock_requests.get.return_value = resp
        monkeypatch.setattr(mcp_mod, "requests", mock_requests)
        assert mcp_mod._scielo_citing_count("un título") == 5
