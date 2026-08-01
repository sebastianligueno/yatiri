from __future__ import annotations

from unittest.mock import MagicMock, patch

from research_operator.core.jstage import search_jstage

_ATOM_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:prism="http://prismstandard.org/namespaces/basic/2.0/">
  <entry>
    <title>Cognición social en contexto escolar</title>
    <link rel="alternate" href="https://jstage.jst.go.jp/article/x"/>
    <summary>Un resumen sobre cognición social.</summary>
    <author><name>Kenji Tanaka</name></author>
    <prism:publicationDate>2018-04-01</prism:publicationDate>
  </entry>
</feed>
"""


def _mock_response(content: bytes) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.content = content
    return resp


class TestSearchJstage:
    def test_parsea_entrada_atom_completa(self):
        with patch("research_operator.core.jstage._requests") as mock_requests:
            mock_requests.get.return_value = _mock_response(_ATOM_XML.encode("utf-8"))
            results = search_jstage("cognición social")
            assert len(results) == 1
            r = results[0]
            assert r.title == "Cognición social en contexto escolar"
            assert r.url == "https://jstage.jst.go.jp/article/x"
            assert r.year == 2018
            assert "Kenji Tanaka" in r.snippet

    def test_entrada_sin_titulo_se_descarta(self):
        xml = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry><title></title></entry>
</feed>"""
        with patch("research_operator.core.jstage._requests") as mock_requests:
            mock_requests.get.return_value = _mock_response(xml.encode("utf-8"))
            assert search_jstage("x") == []

    def test_xml_invalido_devuelve_vacio(self):
        with patch("research_operator.core.jstage._requests") as mock_requests:
            mock_requests.get.return_value = _mock_response(b"no es xml valido <<<")
            assert search_jstage("x") == []

    def test_sin_requests_instalado_devuelve_vacio(self):
        with patch("research_operator.core.jstage._requests", None):
            assert search_jstage("x") == []
