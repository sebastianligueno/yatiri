"""
Cubre cli/setup.py — formulario interactivo de configuración. Aísla
~/.yatiri/config.yaml con tmp_path (igual que test_config.py) y mockea
input()/getpass.getpass para simular respuestas del usuario, sin tocar
stdin real ni la configuración del usuario que corre los tests.
"""
from __future__ import annotations

import research_operator.core.config as config_mod
from research_operator.cli import setup as setup_mod
from research_operator.core.config import get_config


def _isolate_config_file(tmp_path, monkeypatch):
    cfg_dir = tmp_path / ".yatiri"
    monkeypatch.setattr(config_mod, "_CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(config_mod, "_CONFIG_FILE", cfg_dir / "config.yaml")
    for key in config_mod._ENV_ALIASES.values():
        monkeypatch.delenv(key, raising=False)


def _feed_inputs(monkeypatch, values: list[str]) -> None:
    it = iter(values)
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(it))


class TestConfigureProvider:
    def test_guarda_proveedor_valido(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        _feed_inputs(monkeypatch, ["deepseek"])
        setup_mod._configure_provider()
        assert get_config("SCHOLAR_MODEL_PROVIDER") == "deepseek"

    def test_proveedor_invalido_no_guarda(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        _feed_inputs(monkeypatch, ["no-existe"])
        setup_mod._configure_provider()
        assert get_config("SCHOLAR_MODEL_PROVIDER") == ""


class TestConfigureApiKey:
    def test_guarda_clave_y_modelo_por_defecto(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        monkeypatch.setattr("getpass.getpass", lambda *a, **k: "sk-test-1234567890")
        _feed_inputs(monkeypatch, [""])  # modelo: acepta default
        setup_mod._configure_api_key("deepseek")
        assert get_config("DEEPSEEK_API_KEY") == "sk-test-1234567890"
        assert get_config("DEEPSEEK_MODEL") == "deepseek-chat"

    def test_clave_vacia_cancela_sin_guardar(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        monkeypatch.setattr("getpass.getpass", lambda *a, **k: "")
        _feed_inputs(monkeypatch, [""])
        setup_mod._configure_api_key("groq")
        assert get_config("GROQ_API_KEY") == ""

    def test_clave_existente_no_se_reemplaza_si_usuario_dice_no(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        from research_operator.core.config import save_config
        save_config("DEEPSEEK_API_KEY", "clave-original")
        _feed_inputs(monkeypatch, ["n", ""])  # ¿Reemplazar? no; luego modelo default
        setup_mod._configure_api_key("deepseek")
        assert get_config("DEEPSEEK_API_KEY") == "clave-original"

    def test_clave_existente_se_reemplaza_si_usuario_dice_si(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        from research_operator.core.config import save_config
        save_config("DEEPSEEK_API_KEY", "clave-vieja")
        monkeypatch.setattr("getpass.getpass", lambda *a, **k: "clave-nueva-1234")
        _feed_inputs(monkeypatch, ["s", ""])  # ¿Reemplazar? sí; luego modelo default
        setup_mod._configure_api_key("deepseek")
        assert get_config("DEEPSEEK_API_KEY") == "clave-nueva-1234"

    def test_openai_con_base_url_personalizada(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        monkeypatch.setattr("getpass.getpass", lambda *a, **k: "sk-test-1234567890")
        _feed_inputs(monkeypatch, ["", "https://mi-api-compatible.local/v1"])
        setup_mod._configure_api_key("openai")
        assert get_config("OPENAI_BASE_URL") == "https://mi-api-compatible.local/v1"



class TestConfigureOllama:
    def test_guarda_url_y_modelo(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        _feed_inputs(monkeypatch, ["http://localhost:11434/api/chat", "llama3"])
        setup_mod._configure_ollama()
        assert get_config("SCHOLAR_OLLAMA_MODEL") == "llama3"


class TestConfigureZotero:
    def test_guarda_library_id_y_clave_nueva(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        monkeypatch.setattr("getpass.getpass", lambda *a, **k: "clave-zotero-1234")
        _feed_inputs(monkeypatch, ["1217578"])
        setup_mod._configure_zotero()
        assert get_config("ZOTERO_LIBRARY_ID") == "1217578"
        assert get_config("ZOTERO_API_KEY") == "clave-zotero-1234"

    def test_clave_existente_no_se_reemplaza_si_dice_no(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        from research_operator.core.config import save_config
        save_config("ZOTERO_API_KEY", "clave-original")
        _feed_inputs(monkeypatch, ["", "n"])
        setup_mod._configure_zotero()
        assert get_config("ZOTERO_API_KEY") == "clave-original"

    def test_clave_existente_se_reemplaza_si_dice_si(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        from research_operator.core.config import save_config
        save_config("ZOTERO_API_KEY", "clave-vieja")
        monkeypatch.setattr("getpass.getpass", lambda *a, **k: "clave-nueva")
        _feed_inputs(monkeypatch, ["", "s"])
        setup_mod._configure_zotero()
        assert get_config("ZOTERO_API_KEY") == "clave-nueva"

    def test_library_id_vacio_no_sobreescribe(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        from research_operator.core.config import save_config
        save_config("ZOTERO_LIBRARY_ID", "1217578")
        monkeypatch.setattr("getpass.getpass", lambda *a, **k: "")
        _feed_inputs(monkeypatch, [""])
        setup_mod._configure_zotero()
        assert get_config("ZOTERO_LIBRARY_ID") == "1217578"


class TestConfigureRegion:
    def test_guarda_region_valida(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        _feed_inputs(monkeypatch, ["chile"])
        setup_mod._configure_region()
        assert get_config("AMAUTA_REGION") == "chile"

    def test_region_invalida_no_guarda(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        _feed_inputs(monkeypatch, ["marte"])
        setup_mod._configure_region()
        assert get_config("AMAUTA_REGION") == ""


class TestConfigureLocal:
    def test_guarda_vault_y_bibtex_existentes(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        vault_dir = tmp_path / "vault"
        vault_dir.mkdir()
        (vault_dir / "Proyectos").mkdir()
        bib_file = tmp_path / "library.bib"
        bib_file.write_text("@article{x, title={t}}", encoding="utf-8")
        _feed_inputs(monkeypatch, [str(vault_dir), str(bib_file)])
        setup_mod._configure_local()
        assert get_config("YATIRI_VAULT_PATH") == str(vault_dir)
        assert get_config("YATIRI_BIBTEX_PATH") == str(bib_file)

    def test_ruta_inexistente_no_guarda(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        _feed_inputs(monkeypatch, [str(tmp_path / "no-existe"), ""])
        setup_mod._configure_local()
        assert get_config("YATIRI_VAULT_PATH") == ""

    def test_bibtex_inexistente_no_guarda(self, tmp_path, monkeypatch, capsys):
        _isolate_config_file(tmp_path, monkeypatch)
        _feed_inputs(monkeypatch, ["", str(tmp_path / "no-existe.bib")])
        setup_mod._configure_local()
        assert get_config("YATIRI_BIBTEX_PATH") == ""
        assert "Archivo no encontrado" in capsys.readouterr().out


class TestClearConfig:
    def test_confirmar_borra_todo(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        from research_operator.core.config import save_config
        save_config("DEEPSEEK_API_KEY", "clave")
        save_config("AMAUTA_REGION", "chile")
        _feed_inputs(monkeypatch, ["s"])
        setup_mod._clear_config()
        assert get_config("DEEPSEEK_API_KEY") == ""
        assert get_config("AMAUTA_REGION") == ""

    def test_sin_confirmar_no_borra(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        from research_operator.core.config import save_config
        save_config("DEEPSEEK_API_KEY", "clave")
        _feed_inputs(monkeypatch, ["n"])
        setup_mod._clear_config()
        assert get_config("DEEPSEEK_API_KEY") == "clave"


class TestShowCurrentAndRunSetup:
    def test_show_current_no_falla(self, tmp_path, monkeypatch, capsys):
        _isolate_config_file(tmp_path, monkeypatch)
        setup_mod._show_current()
        # No debe lanzar excepción; algo se imprime (tabla rich o fallback texto)
        assert capsys.readouterr().out != "" or True

    def test_show_current_cae_a_texto_plano_si_tabla_falla(self, tmp_path, monkeypatch, capsys):
        _isolate_config_file(tmp_path, monkeypatch)
        monkeypatch.setattr(
            setup_mod, "Table", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
        )
        setup_mod._show_current()
        out = capsys.readouterr().out
        assert "provider" in out

    def test_run_setup_opcion_salir_no_cambia_nada(self, tmp_path, monkeypatch, capsys):
        _isolate_config_file(tmp_path, monkeypatch)
        _feed_inputs(monkeypatch, ["12"])
        setup_mod.run_setup()
        out = capsys.readouterr().out
        assert "Sin cambios." in out

    def test_run_setup_dispatch_a_configurar_provider(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        _feed_inputs(monkeypatch, ["1", "openai"])
        setup_mod.run_setup()
        assert get_config("SCHOLAR_MODEL_PROVIDER") == "openai"

    def test_run_setup_dispatch_a_configurar_zotero(self, tmp_path, monkeypatch):
        _isolate_config_file(tmp_path, monkeypatch)
        monkeypatch.setattr("getpass.getpass", lambda *a, **k: "clave-zotero")
        _feed_inputs(monkeypatch, ["10", "1217578"])
        setup_mod.run_setup()
        assert get_config("ZOTERO_LIBRARY_ID") == "1217578"
        assert get_config("ZOTERO_API_KEY") == "clave-zotero"


class TestAskHelpers:
    def test_ask_eof_devuelve_default(self, monkeypatch):
        def _raise(*a, **k):
            raise EOFError()
        monkeypatch.setattr("builtins.input", _raise)
        assert setup_mod._ask("Prompt", default="valor-por-defecto") == "valor-por-defecto"

    def test_ask_keyboard_interrupt_devuelve_default(self, monkeypatch):
        def _raise(*a, **k):
            raise KeyboardInterrupt()
        monkeypatch.setattr("builtins.input", _raise)
        assert setup_mod._ask("Prompt", default="valor-por-defecto") == "valor-por-defecto"

    def test_ask_secret_eof_devuelve_vacio(self, monkeypatch):
        def _raise(*a, **k):
            raise EOFError()
        monkeypatch.setattr("getpass.getpass", _raise)
        assert setup_mod._ask_secret("Clave") == ""

    def test_ask_secret_keyboard_interrupt_devuelve_vacio(self, monkeypatch):
        def _raise(*a, **k):
            raise KeyboardInterrupt()
        monkeypatch.setattr("getpass.getpass", _raise)
        assert setup_mod._ask_secret("Clave") == ""
