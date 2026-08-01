from __future__ import annotations

import research_operator.core.memory as memory_mod
from research_operator.core.memory import extract_title, list_memories, load_memory_text


def _isolate_memory_dir(tmp_path, monkeypatch):
    mem_dir = tmp_path / "memories"
    monkeypatch.setattr(memory_mod, "MEMORY_DIR", mem_dir)
    return mem_dir


class TestListMemories:
    def test_dir_inexistente_devuelve_vacio(self, tmp_path, monkeypatch):
        _isolate_memory_dir(tmp_path, monkeypatch)
        assert list_memories() == []

    def test_lista_solo_md_ordenados(self, tmp_path, monkeypatch):
        mem_dir = _isolate_memory_dir(tmp_path, monkeypatch)
        mem_dir.mkdir()
        (mem_dir / "b.md").write_text("# Beta\ncontenido", encoding="utf-8")
        (mem_dir / "a.md").write_text("# Alfa\ncontenido", encoding="utf-8")
        (mem_dir / "ignorar.txt").write_text("no cuenta", encoding="utf-8")
        notas = list_memories()
        assert [n.slug for n in notas] == ["a", "b"]


class TestExtractTitle:
    def test_usa_encabezado_markdown(self, tmp_path):
        path = tmp_path / "nota.md"
        path.write_text("# Mi Título\ncuerpo", encoding="utf-8")
        assert extract_title(path) == "Mi Título"

    def test_sin_encabezado_usa_primera_linea_no_vacia(self, tmp_path):
        path = tmp_path / "nota.md"
        path.write_text("\n\nprimera línea con contenido\nresto", encoding="utf-8")
        assert extract_title(path) == "primera línea con contenido"

    def test_archivo_vacio_usa_nombre_de_archivo(self, tmp_path):
        path = tmp_path / "nota-vacia.md"
        path.write_text("", encoding="utf-8")
        assert extract_title(path) == "nota-vacia"


class TestLoadMemoryText:
    def test_carga_por_slug(self, tmp_path, monkeypatch):
        mem_dir = _isolate_memory_dir(tmp_path, monkeypatch)
        mem_dir.mkdir()
        (mem_dir / "proyecto-x.md").write_text("# Proyecto X\ndetalle", encoding="utf-8")
        assert load_memory_text("proyecto-x") == "# Proyecto X\ndetalle"

    def test_slug_inexistente_devuelve_none(self, tmp_path, monkeypatch):
        _isolate_memory_dir(tmp_path, monkeypatch)
        assert load_memory_text("no-existe") is None
