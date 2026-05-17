from __future__ import annotations

import os
from pathlib import Path

import yaml

_CONFIG_DIR = Path.home() / ".yatiri"
_CONFIG_FILE = _CONFIG_DIR / "config.yaml"

# Mapeo de claves internas a variables de entorno equivalentes
_ENV_ALIASES: dict[str, str] = {
    # DeepSeek
    "DEEPSEEK_API_KEY": "DEEPSEEK_API_KEY",
    "DEEPSEEK_MODEL": "DEEPSEEK_MODEL",
    "DEEPSEEK_BASE_URL": "DEEPSEEK_BASE_URL",
    "DEEPSEEK_THINKING_MODE": "DEEPSEEK_THINKING_MODE",
    # OpenRouter (acceso a cientos de modelos: Qwen, Kimi, Mistral, DeepSeek, etc.)
    "OPENROUTER_API_KEY": "OPENROUTER_API_KEY",
    "OPENROUTER_MODEL": "OPENROUTER_MODEL",
    # OpenAI (o cualquier API compatible)
    "OPENAI_API_KEY": "OPENAI_API_KEY",
    "OPENAI_MODEL": "OPENAI_MODEL",
    "OPENAI_BASE_URL": "OPENAI_BASE_URL",
    # Groq
    "GROQ_API_KEY": "GROQ_API_KEY",
    "GROQ_MODEL": "GROQ_MODEL",
    # Anthropic
    "ANTHROPIC_API_KEY": "ANTHROPIC_API_KEY",
    "ANTHROPIC_MODEL": "ANTHROPIC_MODEL",
    # Proveedor y Ollama
    "SCHOLAR_MODEL_PROVIDER": "SCHOLAR_MODEL_PROVIDER",
    "SCHOLAR_OLLAMA_MODEL": "SCHOLAR_OLLAMA_MODEL",
    "SCHOLAR_OLLAMA_URL": "SCHOLAR_OLLAMA_URL",
    "SCHOLAR_CONTACT_EMAIL": "SCHOLAR_CONTACT_EMAIL",
    # Región
    "AMAUTA_REGION": "AMAUTA_REGION",
    "AMAUTA_LANGUAGES": "AMAUTA_LANGUAGES",
}

# Perfiles de región predefinidos
REGIONS: dict[str, dict] = {
    "latam": {
        "label": "América Latina",
        "languages": ["es", "pt"],
        "priority_sources": ["SciELO", "Redalyc", "Dialnet", "OpenAlex", "Latindex"],
        "context": (
            "El contexto geográfico y cultural es América Latina. "
            "Priorice literatura en español y portugués, y fuentes iberoamericanas "
            "(SciELO, Redalyc, Dialnet). Incluya perspectivas latinoamericanas cuando estén disponibles."
        ),
    },
    "iberia": {
        "label": "Iberoamérica (España + Latinoamérica)",
        "languages": ["es", "pt"],
        "priority_sources": ["Dialnet", "SciELO", "Redalyc", "CSIC", "OpenAlex"],
        "context": (
            "El contexto es iberoamericano: España, Portugal y América Latina. "
            "Priorice literatura en español y portugués, incluyendo fuentes españolas "
            "(Dialnet, Revistas CSIC) junto con SciELO y Redalyc."
        ),
    },
    "global": {
        "label": "Global (multilingüe)",
        "languages": ["es", "pt", "en"],
        "priority_sources": ["OpenAlex", "Semantic Scholar", "PubMed", "SciELO"],
        "context": (
            "Contexto global y multilingüe. Use literatura en español, portugués e inglés "
            "sin priorizar una región específica."
        ),
    },
    "chile": {
        "label": "Chile",
        "languages": ["es"],
        "priority_sources": ["SciELO-Chile", "Repositorios ANID", "Redalyc", "OpenAlex"],
        "context": (
            "El contexto geográfico es Chile. Priorice literatura chilena y latinoamericana "
            "en español, incluyendo repositorios nacionales (ANID, U. de Chile, PUC) y SciELO Chile."
        ),
    },
    "brazil": {
        "label": "Brasil / América Latina lusófona",
        "languages": ["pt", "es"],
        "priority_sources": ["SciELO-Brasil", "CAPES", "Redalyc", "OpenAlex"],
        "context": (
            "El contexto es Brasil y la América Latina lusófona. "
            "Priorice literatura en portugués e incluya fuentes del sistema CAPES y SciELO Brasil."
        ),
    },
}


def get_region() -> dict:
    """Devuelve el perfil de región activo."""
    key = get_config("AMAUTA_REGION") or "latam"
    return REGIONS.get(key, REGIONS["latam"])


def _load_file() -> dict:
    if not _CONFIG_FILE.exists():
        return {}
    try:
        data = yaml.safe_load(_CONFIG_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def get_config(key: str, default: str = "") -> str:
    """Lee una clave de configuración. Env var tiene prioridad sobre archivo."""
    env_key = _ENV_ALIASES.get(key, key)
    env_val = os.environ.get(env_key, "")
    if env_val:
        return env_val
    return str(_load_file().get(key, default))


def save_config(key: str, value: str) -> None:
    """Guarda una clave en ~/.yatiri/config.yaml."""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = _load_file()
    data[key] = value
    _CONFIG_FILE.write_text(
        yaml.safe_dump(data, sort_keys=True, allow_unicode=True),
        encoding="utf-8",
    )


def delete_config(key: str) -> None:
    data = _load_file()
    data.pop(key, None)
    if data:
        _CONFIG_FILE.write_text(
            yaml.safe_dump(data, sort_keys=True, allow_unicode=True),
            encoding="utf-8",
        )
    elif _CONFIG_FILE.exists():
        _CONFIG_FILE.unlink()


def config_summary() -> dict:
    """Devuelve el estado visible de la configuración (sin mostrar claves completas)."""
    return {
        "provider": get_config("SCHOLAR_MODEL_PROVIDER") or "auto",
        "deepseek_key": _mask(get_config("DEEPSEEK_API_KEY")),
        "deepseek_model": get_config("DEEPSEEK_MODEL") or "deepseek-chat",
        "openrouter_key": _mask(get_config("OPENROUTER_API_KEY")),
        "openrouter_model": get_config("OPENROUTER_MODEL") or "deepseek/deepseek-chat",
        "openai_key": _mask(get_config("OPENAI_API_KEY")),
        "openai_model": get_config("OPENAI_MODEL") or "gpt-4o-mini",
        "groq_key": _mask(get_config("GROQ_API_KEY")),
        "groq_model": get_config("GROQ_MODEL") or "llama-3.1-8b-instant",
        "anthropic_key": _mask(get_config("ANTHROPIC_API_KEY")),
        "anthropic_model": get_config("ANTHROPIC_MODEL") or "claude-haiku-4-5-20251001",
        "ollama_url": get_config("SCHOLAR_OLLAMA_URL") or "http://localhost:11434/api/chat",
        "ollama_model": get_config("SCHOLAR_OLLAMA_MODEL") or "phi4-mini:3.8b",
        "region": get_config("AMAUTA_REGION") or "latam",
        "config_file": str(_CONFIG_FILE),
    }


def _mask(value: str) -> str:
    if not value:
        return "(no configurada)"
    if len(value) <= 8:
        return "***"
    return value[:4] + "..." + value[-4:]
