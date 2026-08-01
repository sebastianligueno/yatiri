"""
Cubre el parser BibTeX propio de core/bibtex_search.py (sin dependencias
externas, maneja llaves anidadas) — hasta ahora sin tests.
"""
from __future__ import annotations

from research_operator.core.bibtex_search import (
    BibEntry,
    _clean,
    _extract_fields,
    _parse_bib,
    _split_entries,
    find_in_library,
    search_local_library,
)

SAMPLE_BIB = """
@article{palacios2020convivencia,
  title = {La convivencia escolar en {Chile}: un análisis crítico},
  author = {Palacios, Diego and Pérez, Ana},
  year = {2020},
  journal = {Revista de Psicología},
  doi = {10.1234/rp.2020.1},
  abstract = {Un resumen sobre convivencia y bienestar socioemocional.},
}

@book{ovejero2010,
  title = {Psicología social},
  author = {Ovejero, Anastasio},
  year = {2010},
}
"""


class TestSplitEntries:
    def test_separa_dos_entradas(self):
        entries = list(_split_entries(SAMPLE_BIB))
        assert len(entries) == 2
        assert entries[0][0] == "article"
        assert entries[1][0] == "book"

    def test_respeta_llaves_anidadas(self):
        entries = list(_split_entries(SAMPLE_BIB))
        _, body = entries[0]
        assert "{Chile}" in body


class TestExtractFields:
    def test_extrae_campos_con_llaves(self):
        _, body = next(_split_entries(SAMPLE_BIB))
        fields = _extract_fields(body)
        assert fields["year"] == "2020"
        assert "convivencia escolar" in fields["title"].lower()

    def test_valor_numerico_sin_delimitador(self):
        fields = _extract_fields("year = 2019, title = {Un título}")
        assert fields["year"] == "2019"


class TestClean:
    def test_quita_llaves_simples(self):
        assert _clean("La {Convivencia} Escolar") == "La Convivencia Escolar"

    def test_quita_llaves_dobles(self):
        assert _clean("un {{acrónimo}} especial") == "un acrónimo especial"

    def test_colapsa_espacios(self):
        assert _clean("texto   con    espacios") == "texto con espacios"


class TestParseBib:
    def test_parsea_ambas_entradas(self):
        entries = _parse_bib(SAMPLE_BIB)
        assert len(entries) == 2
        keys = {e.key for e in entries}
        assert "palacios2020convivencia" in keys

    def test_genera_key_si_falta(self):
        bib = "@article{, title = {Un tema cualquiera}, author = {Rossi, Luca}, year = {2018}}"
        entries = _parse_bib(bib)
        assert len(entries) == 1
        assert entries[0].key.startswith("rossi2018")

    def test_ignora_entrada_sin_titulo(self):
        bib = "@comment{esto no cuenta}\n" + SAMPLE_BIB
        entries = _parse_bib(bib)
        assert len(entries) == 2


class TestBibEntry:
    def test_matches_cuenta_tokens_encontrados(self):
        entry = BibEntry(key="k", entry_type="article", title="Convivencia escolar", author="", year="2020")
        assert entry.matches("convivencia bienestar") == 1

    def test_matches_doi_case_insensitive(self):
        entry = BibEntry(key="k", entry_type="article", doi="10.1234/ABC")
        assert entry.matches_doi("10.1234/abc") is True

    def test_short_ref_formatea_autor_year_titulo(self):
        entry = BibEntry(
            key="k", entry_type="article",
            title="La convivencia escolar en Chile",
            author="Palacios, Diego and Pérez, Ana",
            year="2020",
        )
        ref = entry.short_ref()
        assert ref.startswith("Palacios et al. (2020)")


class TestSearchLocalLibrary:
    def test_busca_por_relevancia(self, tmp_path):
        bib_path = tmp_path / "library.bib"
        bib_path.write_text(SAMPLE_BIB, encoding="utf-8")
        results = search_local_library("convivencia escolar", bib_path)
        assert len(results) == 1
        assert results[0].key == "palacios2020convivencia"

    def test_sin_coincidencias_devuelve_vacio(self, tmp_path):
        bib_path = tmp_path / "library.bib"
        bib_path.write_text(SAMPLE_BIB, encoding="utf-8")
        assert search_local_library("tema inexistente xyz", bib_path) == []

    def test_archivo_inexistente_devuelve_vacio(self, tmp_path):
        assert search_local_library("cualquiera", tmp_path / "no-existe.bib") == []


class TestFindInLibrary:
    def test_encuentra_por_doi(self, tmp_path):
        bib_path = tmp_path / "library2.bib"
        bib_path.write_text(SAMPLE_BIB, encoding="utf-8")
        entry = find_in_library("10.1234/rp.2020.1", "", bib_path)
        assert entry is not None
        assert entry.key == "palacios2020convivencia"

    def test_encuentra_por_titulo_similar(self, tmp_path):
        bib_path = tmp_path / "library3.bib"
        bib_path.write_text(SAMPLE_BIB, encoding="utf-8")
        entry = find_in_library("", "convivencia escolar chile análisis crítico", bib_path)
        assert entry is not None
        assert entry.key == "palacios2020convivencia"

    def test_sin_coincidencia_devuelve_none(self, tmp_path):
        bib_path = tmp_path / "library4.bib"
        bib_path.write_text(SAMPLE_BIB, encoding="utf-8")
        assert find_in_library("10.9999/no-existe", "tema totalmente distinto", bib_path) is None
