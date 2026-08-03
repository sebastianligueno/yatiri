"""
Cubre core/zotero.py: búsqueda directa contra la Web API de Zotero
(mockeando requests, sin golpear la API real) y el cruce por
DOI/título de find_in_zotero.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import research_operator.core.config as config_mod
from research_operator.core.zotero import (
    _extract_year,
    _format_authors,
    _parse_item,
    find_in_zotero,
    has_credentials,
    search_zotero,
)


def _isolate_config(tmp_path, monkeypatch):
    cfg_dir = tmp_path / ".yatiri"
    monkeypatch.setattr(config_mod, "_CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(config_mod, "_CONFIG_FILE", cfg_dir / "config.yaml")
    for key in config_mod._ENV_ALIASES.values():
        monkeypatch.delenv(key, raising=False)


def _mock_response(json_data) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = json_data
    return resp


def _item(**overrides) -> dict:
    data = {
        "itemType": "journalArticle",
        "title": "Convivencia escolar en Chile",
        "DOI": "10.1234/abc",
        "url": "",
        "publicationTitle": "Revista de Psicología",
        "date": "2021-03",
        "creators": [{"creatorType": "author", "firstName": "Ana", "lastName": "Pérez"}],
        "abstractNote": "Un resumen sobre convivencia escolar.",
    }
    data.update(overrides)
    return {"key": "ABCD1234", "data": data}


class TestHasCredentials:
    def test_sin_configurar_es_false(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        assert has_credentials() is False

    def test_con_ambas_claves_es_true(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        monkeypatch.setenv("ZOTERO_API_KEY", "clave")
        monkeypatch.setenv("ZOTERO_LIBRARY_ID", "1217578")
        assert has_credentials() is True

    def test_solo_una_clave_es_false(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        monkeypatch.setenv("ZOTERO_API_KEY", "clave")
        assert has_credentials() is False


class TestSearchZotero:
    def test_sin_requests_instalado_devuelve_vacio(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        monkeypatch.setenv("ZOTERO_API_KEY", "clave")
        monkeypatch.setenv("ZOTERO_LIBRARY_ID", "1217578")
        with patch("research_operator.core.zotero.requests", None):
            assert search_zotero("convivencia") == []

    def test_sin_credenciales_no_hace_la_llamada(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        with patch("research_operator.core.zotero.requests") as mock_requests:
            assert search_zotero("convivencia") == []
            mock_requests.get.assert_not_called()

    def test_parsea_resultado_y_manda_headers_correctos(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        monkeypatch.setenv("ZOTERO_API_KEY", "clave-secreta")
        monkeypatch.setenv("ZOTERO_LIBRARY_ID", "1217578")
        with patch("research_operator.core.zotero.requests") as mock_requests:
            mock_requests.get.return_value = _mock_response([_item()])
            results = search_zotero("convivencia")
            assert len(results) == 1
            assert results[0].title == "Convivencia escolar en Chile"
            assert results[0].doi == "10.1234/abc"
            assert results[0].key == "ABCD1234"
            call = mock_requests.get.call_args
            assert "1217578" in call.args[0]
            assert call.kwargs["headers"]["Zotero-API-Key"] == "clave-secreta"

    def test_filtra_attachments_y_notas(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        monkeypatch.setenv("ZOTERO_API_KEY", "clave")
        monkeypatch.setenv("ZOTERO_LIBRARY_ID", "1217578")
        with patch("research_operator.core.zotero.requests") as mock_requests:
            mock_requests.get.return_value = _mock_response([
                _item(itemType="attachment", title="PDF adjunto"),
                _item(itemType="note", title=""),
                _item(),
            ])
            results = search_zotero("convivencia")
            assert len(results) == 1

    def test_error_de_red_devuelve_vacio(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        monkeypatch.setenv("ZOTERO_API_KEY", "clave")
        monkeypatch.setenv("ZOTERO_LIBRARY_ID", "1217578")
        with patch("research_operator.core.zotero.requests") as mock_requests:
            mock_requests.get.side_effect = ConnectionError("sin red")
            assert search_zotero("convivencia") == []

    def test_respeta_max_results(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        monkeypatch.setenv("ZOTERO_API_KEY", "clave")
        monkeypatch.setenv("ZOTERO_LIBRARY_ID", "1217578")
        with patch("research_operator.core.zotero.requests") as mock_requests:
            items = [_item(title=f"Paper {i}") for i in range(5)]
            mock_requests.get.return_value = _mock_response(items)
            assert len(search_zotero("x", max_results=2)) == 2


class TestParseItem:
    def test_sin_titulo_devuelve_none(self):
        assert _parse_item({"key": "X", "data": {"itemType": "journalArticle", "title": ""}}) is None

    def test_url_por_defecto_desde_doi(self):
        result = _parse_item(_item(url=""))
        assert result.url == "https://doi.org/10.1234/abc"

    def test_usa_book_title_si_no_hay_publication_title(self):
        result = _parse_item(_item(publicationTitle="", bookTitle="Un libro"))
        assert result.journal == "Un libro"


class TestExtractYear:
    def test_extrae_de_fecha_parcial(self):
        assert _extract_year("2021-03") == "2021"

    def test_sin_fecha_devuelve_none(self):
        assert _extract_year("") is None


class TestFormatAuthors:
    def test_formatea_apellido_e_inicial(self):
        creators = [{"lastName": "Pérez", "firstName": "Ana"}]
        assert _format_authors(creators) == "Pérez, A."

    def test_usa_name_si_no_hay_apellido(self):
        creators = [{"name": "Grupo de Investigación X"}]
        assert _format_authors(creators) == "Grupo de Investigación X"

    def test_agrega_et_al_con_mas_de_tres(self):
        creators = [{"lastName": f"Autor{i}", "firstName": "X"} for i in range(4)]
        assert _format_authors(creators).endswith("et al.")

    def test_sin_creadores_devuelve_none(self):
        assert _format_authors([]) is None


class TestFindInZotero:
    def test_sin_credenciales_devuelve_none(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        assert find_in_zotero("10.1234/abc", "Convivencia escolar") is None

    def test_encuentra_por_doi_exacto(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        monkeypatch.setenv("ZOTERO_API_KEY", "clave")
        monkeypatch.setenv("ZOTERO_LIBRARY_ID", "1217578")
        with patch("research_operator.core.zotero.requests") as mock_requests:
            mock_requests.get.return_value = _mock_response([_item()])
            result = find_in_zotero("10.1234/abc", "")
            assert result is not None
            assert result.key == "ABCD1234"

    def test_doi_sin_coincidencia_intenta_por_titulo(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        monkeypatch.setenv("ZOTERO_API_KEY", "clave")
        monkeypatch.setenv("ZOTERO_LIBRARY_ID", "1217578")
        with patch("research_operator.core.zotero.requests") as mock_requests:
            mock_requests.get.side_effect = [
                _mock_response([_item(DOI="10.9999/otro")]),  # búsqueda por DOI: no matchea
                _mock_response([_item()]),  # búsqueda por título: matchea
            ]
            result = find_in_zotero("10.1234/abc", "Convivencia escolar en Chile")
            assert result is not None

    def test_sin_coincidencia_devuelve_none(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        monkeypatch.setenv("ZOTERO_API_KEY", "clave")
        monkeypatch.setenv("ZOTERO_LIBRARY_ID", "1217578")
        with patch("research_operator.core.zotero.requests") as mock_requests:
            mock_requests.get.return_value = _mock_response([_item(title="Algo totalmente distinto")])
            result = find_in_zotero("", "Convivencia escolar en Chile")
            assert result is None

    def test_sin_doi_ni_titulo_devuelve_none(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        monkeypatch.setenv("ZOTERO_API_KEY", "clave")
        monkeypatch.setenv("ZOTERO_LIBRARY_ID", "1217578")
        assert find_in_zotero("", "") is None
