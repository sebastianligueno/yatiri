from __future__ import annotations

from research_operator.core.config import REGIONS, config_summary, delete_config, get_config, save_config

try:
    from rich.console import Console
    from rich.table import Table
    _console = Console()
    def _print(msg: str) -> None:
        _console.print(msg)
except Exception:
    _console = None
    def _print(msg: str) -> None:
        print(msg)


_PROVIDERS = ["auto", "deepseek", "openrouter", "openai", "groq", "anthropic", "ollama"]

_PROVIDER_INFO = {
    "auto":        "intenta en orden: DeepSeek → OpenRouter → OpenAI → Groq → Anthropic → Ollama",
    "deepseek":    "DeepSeek API — bajo costo, buena calidad  https://platform.deepseek.com",
    "openrouter":  "OpenRouter — acceso a 300+ modelos (Qwen, Kimi, Mistral, Llama…)  https://openrouter.ai",
    "openai":      "OpenAI API — o cualquier API compatible (base URL configurable)",
    "groq":        "Groq — inferencia rápida, modelos Llama  https://console.groq.com",
    "anthropic":   "Anthropic / Claude API  https://console.anthropic.com",
    "ollama":      "Ollama local — sin internet, sin costo  https://ollama.com",
}


def run_setup() -> None:
    _print("\n[bold]Yatiri — Configuración[/bold]")
    _print("Guardado en [cyan]~/.yatiri/config.yaml[/cyan]  (las variables de entorno tienen prioridad)\n")

    _show_current()

    _print("\n¿Qué quieres configurar?")
    _print("  1. Proveedor LLM")
    _print("  2. DeepSeek")
    _print("  3. OpenRouter  (Qwen, Kimi, Mistral, DeepSeek y 300+ modelos)")
    _print("  4. OpenAI (o API compatible)")
    _print("  5. Groq")
    _print("  6. Anthropic / Claude")
    _print("  7. Ollama local")
    _print("  8. Región e idioma de búsqueda")
    _print("  9. Borrar configuración guardada")
    _print(" 10. Salir\n")

    choice = _ask("Opción [1-10]", default="10").strip()

    dispatch = {
        "1": _configure_provider,
        "2": lambda: _configure_api_key("deepseek"),
        "3": lambda: _configure_api_key("openrouter"),
        "4": lambda: _configure_api_key("openai"),
        "5": lambda: _configure_api_key("groq"),
        "6": lambda: _configure_api_key("anthropic"),
        "7": _configure_ollama,
        "8": _configure_region,
        "9": _clear_config,
    }
    fn = dispatch.get(choice)
    if fn:
        fn()
    else:
        _print("Sin cambios.")
    _print("")


def _show_current() -> None:
    summary = config_summary()
    try:
        table = Table(title="Configuración actual", show_header=True)
        table.add_column("Parámetro", style="cyan", min_width=18)
        table.add_column("Valor")
        rows = [
            ("Proveedor activo", summary["provider"]),
            ("Región", summary["region"]),
            ("DeepSeek key", summary["deepseek_key"]),
            ("DeepSeek model", summary["deepseek_model"]),
            ("OpenAI key", summary["openai_key"]),
            ("OpenAI model", summary["openai_model"]),
            ("Groq key", summary["groq_key"]),
            ("Groq model", summary["groq_model"]),
            ("Anthropic key", summary["anthropic_key"]),
            ("Anthropic model", summary["anthropic_model"]),
            ("Ollama URL", summary["ollama_url"]),
            ("Ollama model", summary["ollama_model"]),
        ]
        for k, v in rows:
            table.add_row(k, v)
        _console.print(table)
    except Exception:
        for k, v in summary.items():
            _print(f"  {k}: {v}")


def _configure_provider() -> None:
    _print("\nProveedores disponibles:")
    for name, desc in _PROVIDER_INFO.items():
        marker = " ←" if name == (get_config("SCHOLAR_MODEL_PROVIDER") or "auto") else ""
        _print(f"  {name:<12} {desc}{marker}")
    provider = _ask("\nProveedor", default=get_config("SCHOLAR_MODEL_PROVIDER") or "auto").strip().lower()
    if provider not in _PROVIDERS:
        _print(f"No reconocido. Opciones: {', '.join(_PROVIDERS)}")
        return
    save_config("SCHOLAR_MODEL_PROVIDER", provider)
    _print(f"Proveedor guardado: [green]{provider}[/green]")


def _configure_api_key(provider: str) -> None:
    key_map = {
        "deepseek":    ("DEEPSEEK_API_KEY",    "DEEPSEEK_MODEL",    "deepseek-chat",
                        "https://platform.deepseek.com/api_keys",
                        ["deepseek-chat", "deepseek-reasoner"]),
        "openrouter":  ("OPENROUTER_API_KEY",  "OPENROUTER_MODEL",  "deepseek/deepseek-chat",
                        "https://openrouter.ai/keys",
                        [
                            "deepseek/deepseek-chat",
                            "qwen/qwen-2.5-72b-instruct",
                            "moonshotai/moonshot-v1-8k",
                            "mistralai/mistral-7b-instruct",
                            "meta-llama/llama-3.1-8b-instruct",
                            "google/gemini-flash-1.5",
                        ]),
        "openai":      ("OPENAI_API_KEY",      "OPENAI_MODEL",      "gpt-4o-mini",
                        "https://platform.openai.com/api-keys",
                        ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini"]),
        "groq":        ("GROQ_API_KEY",        "GROQ_MODEL",        "llama-3.1-8b-instant",
                        "https://console.groq.com/keys",
                        ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "mixtral-8x7b-32768"]),
        "anthropic":   ("ANTHROPIC_API_KEY",   "ANTHROPIC_MODEL",   "claude-haiku-4-5-20251001",
                        "https://console.anthropic.com/settings/keys",
                        ["claude-haiku-4-5-20251001", "claude-sonnet-4-6", "claude-opus-4-6"]),
    }
    key_cfg, model_cfg, default_model, key_url, models = key_map[provider]

    _print(f"\n{provider.capitalize()} — clave API")
    _print(f"Obtén tu clave en: {key_url}")
    current = get_config(key_cfg)
    if current:
        _print(f"Clave actual: {current[:4]}...{current[-4:] if len(current) > 8 else '***'}")
        if _ask("¿Reemplazar?", default="n").strip().lower() not in {"s", "si", "sí", "y", "yes"}:
            pass  # skip key replacement but still ask model
        else:
            key = _ask_secret("Nueva API key (Enter para cancelar)")
            if key:
                save_config(key_cfg, key)
                _print("Clave guardada.")
    else:
        key = _ask_secret("API key (Enter para cancelar)")
        if key:
            save_config(key_cfg, key)
            _print("Clave guardada.")

    _print(f"Modelos disponibles: {', '.join(models)}")
    model = _ask("Modelo", default=get_config(model_cfg) or default_model).strip()
    if model:
        save_config(model_cfg, model)
        _print(f"Modelo guardado: {model}")

    # Para OpenAI: opción de base URL personalizada (APIs compatibles)
    if provider == "openai":
        current_url = get_config("OPENAI_BASE_URL")
        _print("\nSi usas una API compatible (Together AI, Azure, LM Studio…) puedes")
        _print("configurar una URL base diferente. Deja vacío para usar OpenAI oficial.")
        url = _ask("Base URL", default=current_url or "https://api.openai.com/v1").strip()
        if url and url != "https://api.openai.com/v1":
            save_config("OPENAI_BASE_URL", url)
            _print(f"Base URL guardada: {url}")
        elif not url:
            delete_config("OPENAI_BASE_URL")


def _configure_ollama() -> None:
    _print("\nOllama local — requiere que el daemon esté corriendo (`ollama serve`)")
    url = _ask("URL", default=get_config("SCHOLAR_OLLAMA_URL") or "http://localhost:11434/api/chat").strip()
    if url:
        save_config("SCHOLAR_OLLAMA_URL", url)
    model = _ask("Modelo", default=get_config("SCHOLAR_OLLAMA_MODEL") or "phi4-mini:3.8b").strip()
    if model:
        save_config("SCHOLAR_OLLAMA_MODEL", model)
    _print("Configuración Ollama guardada.")


def _configure_region() -> None:
    _print("\nRegiones disponibles:")
    current_region = get_config("AMAUTA_REGION") or "latam"
    for key, info in REGIONS.items():
        marker = " ← actual" if key == current_region else ""
        _print(f"  {key:<10} {info['label']}{marker}")
        _print(f"             Idiomas: {', '.join(info['languages'])}")
        _print(f"             Fuentes: {', '.join(info['priority_sources'][:3])}")
    region = _ask("\nRegión", default=current_region).strip().lower()
    if region not in REGIONS:
        _print(f"Región no reconocida. Opciones: {', '.join(REGIONS.keys())}")
        return
    save_config("AMAUTA_REGION", region)
    _print(f"Región guardada: {REGIONS[region]['label']}")


def _clear_config() -> None:
    confirm = _ask("¿Borrar toda la configuración guardada? (s/N)", default="n").strip().lower()
    if confirm in {"s", "si", "sí", "y", "yes"}:
        all_keys = [
            "DEEPSEEK_API_KEY", "DEEPSEEK_MODEL", "DEEPSEEK_BASE_URL",
            "OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_BASE_URL",
            "GROQ_API_KEY", "GROQ_MODEL",
            "ANTHROPIC_API_KEY", "ANTHROPIC_MODEL",
            "SCHOLAR_MODEL_PROVIDER", "SCHOLAR_OLLAMA_URL", "SCHOLAR_OLLAMA_MODEL",
            "AMAUTA_REGION",
        ]
        for key in all_keys:
            delete_config(key)
        _print("Configuración borrada. Las variables de entorno siguen activas.")
    else:
        _print("Cancelado.")


def _ask(prompt: str, default: str = "") -> str:
    display = f"{prompt} [{default}]: " if default else f"{prompt}: "
    try:
        value = input(display).strip()
        return value if value else default
    except (EOFError, KeyboardInterrupt):
        return default


def _ask_secret(prompt: str) -> str:
    import getpass
    try:
        return getpass.getpass(f"{prompt}: ").strip()
    except (EOFError, KeyboardInterrupt):
        return ""
