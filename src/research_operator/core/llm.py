from __future__ import annotations

from dataclasses import dataclass
import os

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


def chat_completion(system_prompt: str, messages: list[dict]) -> ChatResult:
    """messages: lista de {"role": "user"|"assistant", "content": str}"""
    provider = (get_config("SCHOLAR_MODEL_PROVIDER") or "auto").lower()
    attempted: list[str] = []
    errors: list[str] = []

    if provider in {"deepseek", "auto"}:
        attempted.append("deepseek")
        response = deepseek_chat(system_prompt, messages)
        if response.content:
            return response
        if response.error:
            errors.append(f"deepseek={response.error}")

    if provider in {"ollama", "auto"}:
        attempted.append("ollama")
        response = ollama_chat(system_prompt, messages)
        if response.content:
            return response
        if response.error:
            errors.append(f"ollama={response.error}")

    provider_label = provider if provider != "auto" else " -> ".join(attempted or ["none"])
    return ChatResult(content=None, provider=provider_label, error="; ".join(errors) if errors else "no provider available")


def active_provider_label() -> str:
    provider = get_config("SCHOLAR_MODEL_PROVIDER") or "auto"
    deepseek_key = bool(get_config("DEEPSEEK_API_KEY"))
    ollama_url = get_config("SCHOLAR_OLLAMA_URL") or "http://localhost:11434/api/chat"
    return f"provider={provider}, deepseek_key={'yes' if deepseek_key else 'no'}, ollama={ollama_url}"


def provider_diagnostics() -> str:
    lines = [
        active_provider_label(),
        f"requests_available={'yes' if requests is not None else 'no'}",
        f"deepseek_model={get_config('DEEPSEEK_MODEL') or 'deepseek-chat'}",
        f"ollama_model={get_config('SCHOLAR_OLLAMA_MODEL') or 'phi4-mini:3.8b'}",
        "",
        render_stack_report(),
    ]
    return "\n".join(lines)


def deepseek_chat(system_prompt: str, messages: list[dict]) -> ChatResult:
    if requests is None:
        return ChatResult(content=None, provider="deepseek", error="requests not installed")

    api_key = get_config("DEEPSEEK_API_KEY")
    if not api_key:
        return ChatResult(content=None, provider="deepseek", error="missing DEEPSEEK_API_KEY (use `yatiri setup`)")

    base_url = get_config("DEEPSEEK_BASE_URL") or "https://api.deepseek.com"
    model = get_config("DEEPSEEK_MODEL") or "deepseek-chat"
    thinking_mode = get_config("DEEPSEEK_THINKING_MODE") or "disabled"

    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "stream": False,
        "max_tokens": 4096,
    }
    if thinking_mode != "disabled":
        payload["thinking"] = {"type": thinking_mode}
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(
            f"{base_url.rstrip('/')}/chat/completions",
            json=payload,
            headers=headers,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            return ChatResult(content=None, provider="deepseek", error="empty choices")
        return ChatResult(content=choices[0].get("message", {}).get("content"), provider="deepseek")
    except Exception as exc:
        return ChatResult(content=None, provider="deepseek", error=str(exc))


def ollama_chat(system_prompt: str, messages: list[dict]) -> ChatResult:
    if requests is None:
        return ChatResult(content=None, provider="ollama", error="requests not installed")

    url = get_config("SCHOLAR_OLLAMA_URL") or "http://localhost:11434/api/chat"
    model = get_config("SCHOLAR_OLLAMA_MODEL") or "phi4-mini:3.8b"
    payload = {
        "model": model,
        "stream": False,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "options": {"temperature": 0.2, "num_ctx": 8192},
    }
    try:
        response = requests.post(url, json=payload, timeout=45)
        response.raise_for_status()
        data = response.json()
        return ChatResult(content=data.get("message", {}).get("content"), provider="ollama")
    except Exception as exc:
        return ChatResult(content=None, provider="ollama", error=str(exc))
