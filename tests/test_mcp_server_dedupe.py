"""
Cubre la deduplicación de multi_source_search (mcp_server.py, 2026-07-31):
mismo DOI o mismo título normalizado entre fuentes distintas debe fusionarse
en una sola entrada.
"""
from __future__ import annotations

from research_operator.mcp_server import _dedupe_key, _normalize_doi, _normalize_title


class TestNormalizeDoi:
    def test_none_devuelve_none(self):
        assert _normalize_doi(None) is None

    def test_minusculas_y_sin_barra_final(self):
        assert _normalize_doi("10.1234/ABC/") == "10.1234/abc"

    def test_quita_prefijo_url(self):
        assert _normalize_doi("https://doi.org/10.1234/abc") == "10.1234/abc"
        assert _normalize_doi("https://dx.doi.org/10.1234/abc") == "10.1234/abc"


class TestNormalizeTitle:
    def test_minusculas_sin_puntuacion_espacios_colapsados(self):
        assert (
            _normalize_title("  El TDAH: ¿Medicalización   o   cuidado?  ")
            == "el tdah medicalización o cuidado"
        )

    def test_vacio(self):
        assert _normalize_title(None) == ""
        assert _normalize_title("") == ""


class TestDedupeKey:
    def test_prioriza_doi_sobre_titulo(self):
        d = {"doi": "10.1234/abc", "title": "Un título"}
        assert _dedupe_key(d) == ("doi", "10.1234/abc")

    def test_mismo_doi_en_formatos_distintos_da_misma_clave(self):
        a = {"doi": "https://doi.org/10.1234/ABC/", "title": "Título A"}
        b = {"doi": "10.1234/abc", "title": "Título A distinto en mayúsculas"}
        assert _dedupe_key(a) == _dedupe_key(b)

    def test_sin_doi_cae_a_titulo_normalizado(self):
        a = {"doi": None, "title": "El TDAH y la escuela"}
        b = {"doi": None, "title": "  el tdah   Y LA escuela  "}
        assert _dedupe_key(a) == _dedupe_key(b) == ("title", "el tdah y la escuela")

    def test_titulos_distintos_no_colisionan(self):
        a = {"doi": None, "title": "El TDAH y la escuela"}
        b = {"doi": None, "title": "La convivencia escolar"}
        assert _dedupe_key(a) != _dedupe_key(b)
