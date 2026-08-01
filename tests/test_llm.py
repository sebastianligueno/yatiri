"""
Cubre core/llm.py: estimate_cost, el dispatch de chat_completion (orden
"auto" con fallback), cada _*_chat / _openai_compat, y los diagnósticos.
Aísla ~/.yatiri/config.yaml igual que test_config.py para no depender de
las claves reales del usuario.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import research_operator.core.config as config_mod
from research_operator.core.llm import (
    ChatResult,
    _anthropic_chat,
    _call_provider,
    _ollama_chat,
    _openai_compat,
    active_provider_label,
    chat_completion,
    estimate_cost,
    provider_diagnostics,
)


def _isolate_config(tmp_path, monkeypatch):
    cfg_dir = tmp_path / ".yatiri"
    monkeypatch.setattr(config_mod, "_CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(config_mod, "_CONFIG_FILE", cfg_dir / "config.yaml")
    for key in config_mod._ENV_ALIASES.values():
        monkeypatch.delenv(key, raising=False)


def _mock_response(json_data: dict, status_ok: bool = True) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = json_data
    return resp


class TestEstimateCost:
    def test_calcula_costo_proporcional_a_tokens(self):
        cost = estimate_cost("deepseek", 1_000_000, 1_000_000)
        assert cost == 0.27 + 1.10

    def test_proveedor_desconocido_es_gratis(self):
        assert estimate_cost("inexistente", 1000, 1000) == 0.0

    def test_ollama_es_gratis(self):
        assert estimate_cost("ollama", 1_000_000, 1_000_000) == 0.0


class TestOpenaiCompat:
    def test_sin_requests_instalado(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        with patch("research_operator.core.llm.requests", None):
            result = _openai_compat("sys", [], "https://x", "key", "modelo", "deepseek")
            assert result.content is None
            assert "requests no instalado" in result.error

    def test_sin_api_key(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        result = _openai_compat("sys", [], "https://x", "", "modelo", "deepseek")
        assert result.content is None
        assert "sin clave" in result.error

    def test_respuesta_exitosa(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        with patch("research_operator.core.llm.requests") as mock_requests:
            mock_requests.post.return_value = _mock_response({
                "choices": [{"message": {"content": "respuesta"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            })
            result = _openai_compat("sys", [], "https://x", "clave", "modelo", "deepseek")
            assert result.content == "respuesta"
            assert result.input_tokens == 10
            assert result.output_tokens == 5

    def test_respuesta_sin_choices(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        with patch("research_operator.core.llm.requests") as mock_requests:
            mock_requests.post.return_value = _mock_response({"choices": []})
            result = _openai_compat("sys", [], "https://x", "clave", "modelo", "deepseek")
            assert result.content is None
            assert result.error == "respuesta vacía"

    def test_error_de_red(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        with patch("research_operator.core.llm.requests") as mock_requests:
            mock_requests.post.side_effect = ConnectionError("sin red")
            result = _openai_compat("sys", [], "https://x", "clave", "modelo", "deepseek")
            assert result.content is None
            assert "sin red" in result.error


class TestAnthropicChat:
    def test_sin_api_key(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        result = _anthropic_chat("sys", [])
        assert result.content is None
        assert "sin clave" in result.error

    def test_respuesta_exitosa_concatena_bloques_de_texto(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        with patch("research_operator.core.llm.requests") as mock_requests:
            mock_requests.post.return_value = _mock_response({
                "content": [{"type": "text", "text": "hola"}, {"type": "text", "text": "mundo"}],
                "usage": {"input_tokens": 3, "output_tokens": 2},
            })
            result = _anthropic_chat("sys", [])
            assert result.content == "hola mundo"
            assert result.provider == "anthropic"


class TestOllamaChat:
    def test_respuesta_exitosa(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        with patch("research_operator.core.llm.requests") as mock_requests:
            mock_requests.post.return_value = _mock_response({"message": {"content": "respuesta local"}})
            result = _ollama_chat("sys", [])
            assert result.content == "respuesta local"
            assert result.provider == "ollama"

    def test_error_de_red(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        with patch("research_operator.core.llm.requests") as mock_requests:
            mock_requests.post.side_effect = TimeoutError("timeout")
            result = _ollama_chat("sys", [])
            assert result.content is None


class TestCallProvider:
    def test_proveedor_desconocido(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        result = _call_provider("inexistente", "sys", [])
        assert "proveedor desconocido" in result.error


class TestChatCompletion:
    def test_usa_proveedor_explicito(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        monkeypatch.setenv("SCHOLAR_MODEL_PROVIDER", "ollama")
        with patch("research_operator.core.llm._ollama_chat") as mock_ollama:
            mock_ollama.return_value = ChatResult(content="ok", provider="ollama")
            result = chat_completion("sys", [])
            assert result.content == "ok"
            mock_ollama.assert_called_once()

    def test_modo_auto_prueba_en_orden_hasta_encontrar_exito(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        with patch("research_operator.core.llm._call_provider") as mock_call:
            def side_effect(name, *a, **k):
                if name == "groq":
                    return ChatResult(content="respuesta de groq", provider="groq")
                return ChatResult(content=None, provider=name, error=f"{name} sin clave")
            mock_call.side_effect = side_effect
            result = chat_completion("sys", [])
            assert result.content == "respuesta de groq"
            assert result.provider == "groq"

    def test_modo_auto_sin_ningun_proveedor_disponible(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        with patch("research_operator.core.llm._call_provider") as mock_call:
            mock_call.return_value = ChatResult(content=None, provider="x", error="sin clave")
            result = chat_completion("sys", [])
            assert result.content is None
            assert "→" in result.provider


class TestActiveProviderLabel:
    def test_sin_ninguna_clave_usa_ollama(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        label = active_provider_label()
        assert "activos=ollama" in label

    def test_con_clave_deepseek(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
        label = active_provider_label()
        assert "deepseek" in label


class TestProviderDiagnostics:
    def test_incluye_disponibilidad_de_requests_y_stack(self, tmp_path, monkeypatch):
        _isolate_config(tmp_path, monkeypatch)
        text = provider_diagnostics()
        assert "requests_available=" in text
        assert "deepseek_model=" in text
