from __future__ import annotations

from research_operator.core.config import REGIONS, config_summary, delete_config, get_config, save_config

try:
    from rich.console import Console
    from rich.table import Table
    _console = Console()
    def _print(msg: str) -> None:
        _console.print(msg)
except Exception:
    def _print(msg: str) -> None:
        print(msg)


_PROVIDERS = ["auto", "deepseek", "ollama"]
_DEEPSEEK_MODELS = ["deepseek-chat", "deepseek-reasoner"]


def run_setup() -> None:
    _print("\n[bold]Yatiri — Configuración[/bold]")
    _print("Esto se guarda en [cyan]~/.yatiri/config.yaml[/cyan]")
    _print("Las variables de entorno siguen teniendo prioridad si están definidas.\n")

    _show_current()

    _print("\n¿Qué quiere configurar?")
    _print("  1. Proveedor y modelo principal")
    _print("  2. DeepSeek API key")
    _print("  3. Ollama URL y modelo")
    _print("  4. Región e idioma de búsqueda")
    _print("  5. Borrar configuración guardada")
    _print("  6. Salir sin cambios\n")

    choice = _ask("Opción [1-6]", default="6").strip()

    if choice == "1":
        _configure_provider()
    elif choice == "2":
        _configure_deepseek_key()
    elif choice == "3":
        _configure_ollama()
    elif choice == "4":
        _configure_region()
    elif choice == "5":
        _clear_config()
    else:
        _print("Sin cambios.")

    _print("")


def _show_current() -> None:
    summary = config_summary()
    try:
        table = Table(title="Configuración actual", show_header=True)
        table.add_column("Parámetro", style="cyan")
        table.add_column("Valor")
        table.add_row("Proveedor", summary["provider"])
        table.add_row("DeepSeek key", summary["deepseek_key"])
        table.add_row("DeepSeek model", summary["deepseek_model"])
        table.add_row("Ollama URL", summary["ollama_url"])
        table.add_row("Ollama model", summary["ollama_model"])
        table.add_row("Archivo config", summary["config_file"])
        _console.print(table)
    except Exception:
        for k, v in summary.items():
            _print(f"  {k}: {v}")


def _configure_provider() -> None:
    _print(f"Proveedores disponibles: {', '.join(_PROVIDERS)}")
    _print("  auto     — intenta DeepSeek primero, luego Ollama")
    _print("  deepseek — solo DeepSeek API (requiere clave)")
    _print("  ollama   — solo Ollama local (sin clave, requiere daemon)")
    provider = _ask("Proveedor", default=get_config("SCHOLAR_MODEL_PROVIDER") or "auto").strip().lower()
    if provider not in _PROVIDERS:
        _print(f"Valor no reconocido, usando 'auto'.")
        provider = "auto"
    save_config("SCHOLAR_MODEL_PROVIDER", provider)
    _print(f"Proveedor guardado: {provider}")

    if provider in {"deepseek", "auto"}:
        _print(f"\nModelos DeepSeek: {', '.join(_DEEPSEEK_MODELS)}")
        model = _ask("Modelo DeepSeek", default=get_config("DEEPSEEK_MODEL") or "deepseek-chat").strip()
        if model:
            save_config("DEEPSEEK_MODEL", model)
            _print(f"Modelo guardado: {model}")


def _configure_deepseek_key() -> None:
    _print("\nObtén tu clave en https://platform.deepseek.com/api_keys")
    current = get_config("DEEPSEEK_API_KEY")
    if current:
        _print(f"Clave actual: {current[:4]}...{current[-4:] if len(current) > 8 else '***'}")
        if _ask("¿Reemplazar?", default="n").strip().lower() not in {"s", "si", "sí", "y", "yes"}:
            return
    key = _ask_secret("Nueva API key (Enter para cancelar)")
    if key:
        save_config("DEEPSEEK_API_KEY", key)
        _print("Clave guardada.")
    else:
        _print("Sin cambios.")


def _configure_ollama() -> None:
    url = _ask("Ollama URL", default=get_config("SCHOLAR_OLLAMA_URL") or "http://localhost:11434/api/chat").strip()
    if url:
        save_config("SCHOLAR_OLLAMA_URL", url)
    model = _ask("Modelo Ollama", default=get_config("SCHOLAR_OLLAMA_MODEL") or "phi4-mini:3.8b").strip()
    if model:
        save_config("SCHOLAR_OLLAMA_MODEL", model)
    _print("Configuración Ollama guardada.")


def _configure_region() -> None:
    _print("\nRegiones disponibles:")
    for key, info in REGIONS.items():
        current = " ← actual" if key == (get_config("AMAUTA_REGION") or "latam") else ""
        _print(f"  {key:10} {info['label']}{current}")
        _print(f"            Idiomas: {', '.join(info['languages'])}")
        _print(f"            Fuentes: {', '.join(info['priority_sources'][:3])}")
    region = _ask("\nRegión", default=get_config("AMAUTA_REGION") or "latam").strip().lower()
    if region not in REGIONS:
        _print(f"Región no reconocida. Opciones: {', '.join(REGIONS.keys())}")
        return
    save_config("AMAUTA_REGION", region)
    _print(f"Región guardada: {REGIONS[region]['label']}")


def _clear_config() -> None:
    confirm = _ask("¿Borrar toda la configuración guardada? (s/N)", default="n").strip().lower()
    if confirm in {"s", "si", "sí", "y", "yes"}:
        for key in ["DEEPSEEK_API_KEY", "DEEPSEEK_MODEL", "SCHOLAR_MODEL_PROVIDER",
                    "SCHOLAR_OLLAMA_URL", "SCHOLAR_OLLAMA_MODEL"]:
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
