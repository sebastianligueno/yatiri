from __future__ import annotations

from dataclasses import dataclass

from research_operator.core.academic_stack import render_stack_report
from research_operator.core.config import get_config

try:
    import requests
except Exception:  # pragma: no cover
    requests = None


@dataclass(slots=True)
class ChatResult:
    content: str | None
    provider: str
    error: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0


# Precios aproximados por millón de tokens (USD) — input / output
_PRICING: dict[str, tuple[float, float]] = {
    "deepseek":    (0.27, 1.10),
    "openrouter":  (0.27, 1.10),   # varía por modelo; default deepseek
    "openai":      (0.15, 0.60),   # gpt-4o-mini
    "groq":        (0.05, 0.08),   # llama-3.1-8b-instant
    "anthropic":   (0.80, 4.00),   # claude-haiku
    "ollama":      (0.00, 0.00),
}


def estimate_cost(provider: str, input_tokens: int, output_tokens: int) -> float:
    inp_price, out_price = _PRICING.get(provider, (0.0, 0.0))
    return (input_tokens * inp_price + output_tokens * out_price) / 1_000_000


# Orden de intento para modo "auto": primero el que tenga clave
_AUTO_ORDER = ["deepseek", "openrouter", "openai", "groq", "anthropic", "ollama"]


def chat_completion(system_prompt: str, messages: list[dict]) -> ChatResult:
    """Despacha la consulta al proveedor configurado o al primero disponible."""
    provider = (get_config("SCHOLAR_MODEL_PROVIDER") or "auto").lower()

    candidates = _AUTO_ORDER if provider == "auto" else [provider]
    errors: list[str] = []

    for name in candidates:
        result = _call_provider(name, system_prompt, messages)
        if result.content:
            return result
        if result.error:
            errors.append(f"{name}={result.error}")

    label = provider if provider != "auto" else " → ".join(candidates)
    return ChatResult(
        content=None,
        provider=label,
        error="; ".join(errors) if errors else "ningún proveedor disponible",
    )


def _call_provider(name: str, system_prompt: str, messages: list[dict]) -> ChatResult:
    if name == "deepseek":
        return _openai_compat(
            system_prompt, messages,
            base_url=get_config("DEEPSEEK_BASE_URL") or "https://api.deepseek.com",
            api_key=get_config("DEEPSEEK_API_KEY"),
            model=get_config("DEEPSEEK_MODEL") or "deepseek-chat",
            provider_name="deepseek",
            extra_payload=_deepseek_extra(),
        )
    if name == "openai":
        return _openai_compat(
            system_prompt, messages,
            base_url=get_config("OPENAI_BASE_URL") or "https://api.openai.com/v1",
            api_key=get_config("OPENAI_API_KEY"),
            model=get_config("OPENAI_MODEL") or "gpt-4o-mini",
            provider_name="openai",
        )
    if name == "openrouter":
        model = get_config("OPENROUTER_MODEL") or "deepseek/deepseek-chat"
        return _openai_compat(
            system_prompt, messages,
            base_url="https://openrouter.ai/api/v1",
            api_key=get_config("OPENROUTER_API_KEY"),
            model=model,
            provider_name="openrouter",
            extra_headers={
                "HTTP-Referer": "https://github.com/sebastianligueno/yatiri",
                "X-Title": "Yatiri Academic Assistant",
            },
        )
    if name == "groq":
        return _openai_compat(
            system_prompt, messages,
            base_url="https://api.groq.com/openai/v1",
            api_key=get_config("GROQ_API_KEY"),
            model=get_config("GROQ_MODEL") or "llama-3.1-8b-instant",
            provider_name="groq",
        )
    if name == "anthropic":
        return _anthropic_chat(system_prompt, messages)
    if name == "ollama":
        return _ollama_chat(system_prompt, messages)
    return ChatResult(content=None, provider=name, error=f"proveedor desconocido: {name}")


def _deepseek_extra() -> dict:
    thinking_mode = get_config("DEEPSEEK_THINKING_MODE") or "disabled"
    if thinking_mode != "disabled":
        return {"thinking": {"type": thinking_mode}}
    return {}


def _openai_compat(
    system_prompt: str,
    messages: list[dict],
    base_url: str,
    api_key: str,
    model: str,
    provider_name: str,
    extra_payload: dict | None = None,
    extra_headers: dict | None = None,
) -> ChatResult:
    if requests is None:
        return ChatResult(content=None, provider=provider_name, error="requests no instalado")
    if not api_key:
        return ChatResult(
            content=None, provider=provider_name,
            error=f"sin clave {provider_name.upper()}_API_KEY (usa `yatiri setup`)",
        )
    payload: dict = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "stream": False,
        "max_tokens": 4096,
    }
    if extra_payload:
        payload.update(extra_payload)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    try:
        resp = requests.post(
            f"{base_url.rstrip('/')}/chat/completions",
            json=payload, headers=headers, timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            return ChatResult(content=None, provider=provider_name, error="respuesta vacía")
        usage = data.get("usage", {})
        return ChatResult(
            content=choices[0].get("message", {}).get("content"),
            provider=provider_name,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
        )
    except Exception as exc:
        return ChatResult(content=None, provider=provider_name, error=str(exc))


def _anthropic_chat(system_prompt: str, messages: list[dict]) -> ChatResult:
    if requests is None:
        return ChatResult(content=None, provider="anthropic", error="requests no instalado")
    api_key = get_config("ANTHROPIC_API_KEY")
    if not api_key:
        return ChatResult(
            content=None, provider="anthropic",
            error="sin clave ANTHROPIC_API_KEY (usa `yatiri setup`)",
        )
    model = get_config("ANTHROPIC_MODEL") or "claude-haiku-4-5-20251001"
    payload = {
        "model": model,
        "max_tokens": 4096,
        "system": system_prompt,
        "messages": messages,
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            json=payload, headers=headers, timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        content_blocks = data.get("content", [])
        text = " ".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
        usage = data.get("usage", {})
        return ChatResult(
            content=text or None, provider="anthropic",
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
        )
    except Exception as exc:
        return ChatResult(content=None, provider="anthropic", error=str(exc))


def _ollama_chat(system_prompt: str, messages: list[dict]) -> ChatResult:
    if requests is None:
        return ChatResult(content=None, provider="ollama", error="requests no instalado")
    url = get_config("SCHOLAR_OLLAMA_URL") or "http://localhost:11434/api/chat"
    model = get_config("SCHOLAR_OLLAMA_MODEL") or "phi4-mini:3.8b"
    payload = {
        "model": model,
        "stream": False,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "options": {"temperature": 0.2, "num_ctx": 8192},
    }
    try:
        resp = requests.post(url, json=payload, timeout=45)
        resp.raise_for_status()
        return ChatResult(
            content=resp.json().get("message", {}).get("content"),
            provider="ollama",
        )
    except Exception as exc:
        return ChatResult(content=None, provider="ollama", error=str(exc))


def active_provider_label() -> str:
    provider = get_config("SCHOLAR_MODEL_PROVIDER") or "auto"
    keys = {
        "deepseek": bool(get_config("DEEPSEEK_API_KEY")),
        "openrouter": bool(get_config("OPENROUTER_API_KEY")),
        "openai": bool(get_config("OPENAI_API_KEY")),
        "groq": bool(get_config("GROQ_API_KEY")),
        "anthropic": bool(get_config("ANTHROPIC_API_KEY")),
    }
    keys_str = ", ".join(f"{k}={'sí' if v else 'no'}" for k, v in keys.items())
    ollama = get_config("SCHOLAR_OLLAMA_URL") or "http://localhost:11434/api/chat"
    return f"provider={provider}, claves=[{keys_str}], ollama={ollama}"


def provider_diagnostics() -> str:
    lines = [
        active_provider_label(),
        f"requests_available={'sí' if requests is not None else 'no'}",
        f"deepseek_model={get_config('DEEPSEEK_MODEL') or 'deepseek-chat'}",
        f"openai_model={get_config('OPENAI_MODEL') or 'gpt-4o-mini'}",
        f"groq_model={get_config('GROQ_MODEL') or 'llama-3.1-8b-instant'}",
        f"anthropic_model={get_config('ANTHROPIC_MODEL') or 'claude-haiku-4-5-20251001'}",
        f"ollama_model={get_config('SCHOLAR_OLLAMA_MODEL') or 'phi4-mini:3.8b'}",
        "",
        render_stack_report(),
    ]
    return "\n".join(lines)
