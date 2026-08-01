from __future__ import annotations

import json
from pathlib import Path

import research_operator.core.mcp_detect as mcp_detect_mod
from research_operator.core.mcp_detect import detect_mcps, render_mcp_report


def _isolate_settings_paths(monkeypatch, tmp_path: Path, settings: dict | None):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(mcp_detect_mod.Path, "home", classmethod(lambda cls: fake_home))
    if settings is not None:
        settings_dir = fake_home / ".claude"
        settings_dir.mkdir(parents=True)
        (settings_dir / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
    return fake_home


class TestDetectMcps:
    def test_sin_settings_devuelve_solo_recomendados(self, tmp_path, monkeypatch):
        _isolate_settings_paths(monkeypatch, tmp_path, settings=None)
        report = detect_mcps()
        assert report.installed == []
        assert len(report.missing_recommended) == 4

    def test_mcp_conocido_se_resuelve_por_nombre_exacto(self, tmp_path, monkeypatch):
        _isolate_settings_paths(monkeypatch, tmp_path, settings={
            "mcpServers": {"zotero": {"command": "zotero-mcp"}}
        })
        report = detect_mcps()
        assert len(report.installed) == 1
        assert report.installed[0].label == "Zotero"
        assert report.installed[0].cap == "bibliography"
        assert not any(r["name"] == "zotero" for r in report.missing_recommended)

    def test_mcp_desconocido_usa_info_generica(self, tmp_path, monkeypatch):
        _isolate_settings_paths(monkeypatch, tmp_path, settings={
            "mcpServers": {"mi-servidor-raro": {"url": "https://x"}}
        })
        report = detect_mcps()
        assert report.installed[0].cap == "other"
        assert report.installed[0].label == "mi-servidor-raro"

    def test_settings_json_corrupto_no_rompe(self, tmp_path, monkeypatch):
        fake_home = _isolate_settings_paths(monkeypatch, tmp_path, settings=None)
        settings_dir = fake_home / ".claude"
        settings_dir.mkdir(parents=True)
        (settings_dir / "settings.json").write_text("esto no es json {{{", encoding="utf-8")
        assert detect_mcps().installed == []

    def test_has_cap(self, tmp_path, monkeypatch):
        _isolate_settings_paths(monkeypatch, tmp_path, settings={
            "mcpServers": {"scite": {"transport": "http"}}
        })
        report = detect_mcps()
        assert report.has_cap("verification") is True
        assert report.has_cap("discovery") is False


class TestRenderMcpReport:
    def test_incluye_instalados_y_recomendados(self, tmp_path, monkeypatch):
        _isolate_settings_paths(monkeypatch, tmp_path, settings={
            "mcpServers": {"zotero": {"command": "zotero-mcp"}}
        })
        text = render_mcp_report()
        assert "[bibliography] Zotero" in text
        assert "MCPs recomendados no instalados" in text
        assert "Scite MCP" in text

    def test_sin_ninguno_instalado(self, tmp_path, monkeypatch):
        _isolate_settings_paths(monkeypatch, tmp_path, settings=None)
        text = render_mcp_report()
        assert "Ningún MCP detectado" in text
