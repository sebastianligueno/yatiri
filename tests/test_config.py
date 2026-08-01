"""
Cubre core/config.py. Todos los tests aíslan _CONFIG_FILE/_CONFIG_DIR con
tmp_path (vía monkeypatch) para no leer ni escribir el ~/.yatiri real del
usuario, y limpian las env vars relevantes para no depender del entorno
donde corre pytest.
"""
from __future__ import annotations

import research_operator.core.config as config_mod
from research_operator.core.config import (
    REGIONS,
    config_summary,
    delete_config,
    get_config,
    get_region,
    save_config,
)


def _isolate_config_file(tmp_path, monkeypatch):
    cfg_dir = tmp_path / ".yatiri"
    monkeypatch.setattr(config_mod, "_CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(config_mod, "_CONFIG_FILE", cfg_dir / "config.yaml")
    for key in config_mod._ENV_ALIASES.values():
        monkeypatch.delenv(key, raising=False)


class TestGetConfig:
    def test_sin_archivo_ni_env_devuelve_default(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        assert get_config("DEEPSEEK_API_KEY", "por-defecto") == "por-defecto"

    def test_env_var_tiene_prioridad_sobre_archivo(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        save_config("DEEPSEEK_API_KEY", "del-archivo")
        monkeypatch.setenv("DEEPSEEK_API_KEY", "de-env")
        assert get_config("DEEPSEEK_API_KEY") == "de-env"

    def test_archivo_corrupto_no_rompe_y_devuelve_default(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        config_mod._CONFIG_DIR.mkdir(parents=True)
        config_mod._CONFIG_FILE.write_text(": : esto no es yaml válido : :", encoding="utf-8")
        assert get_config("DEEPSEEK_API_KEY", "default") == "default"


class TestSaveDeleteConfig:
    def test_save_y_get_roundtrip(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        save_config("AMAUTA_REGION", "chile")
        assert get_config("AMAUTA_REGION") == "chile"

    def test_delete_config_quita_clave(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        save_config("AMAUTA_REGION", "chile")
        delete_config("AMAUTA_REGION")
        assert get_config("AMAUTA_REGION", "latam") == "latam"

    def test_delete_config_ultima_clave_borra_archivo(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        save_config("AMAUTA_REGION", "chile")
        delete_config("AMAUTA_REGION")
        assert not config_mod._CONFIG_FILE.exists()


class TestGetRegion:
    def test_default_es_latam(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        assert get_region() == REGIONS["latam"]

    def test_region_configurada(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        save_config("AMAUTA_REGION", "brazil")
        assert get_region() == REGIONS["brazil"]

    def test_region_desconocida_cae_a_latam(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        save_config("AMAUTA_REGION", "inexistente")
        assert get_region() == REGIONS["latam"]


class TestConfigSummary:
    def test_enmascara_claves_no_expone_valor_completo(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-1234567890abcdef")
        summary = config_summary()
        assert "1234567890" not in summary["deepseek_key"]
        assert summary["deepseek_key"].startswith("sk-1")

    def test_sin_clave_indica_no_configurada(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        summary = config_summary()
        assert summary["deepseek_key"] == "(no configurada)"
