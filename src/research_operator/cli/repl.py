from __future__ import annotations

from pathlib import Path
import shlex

from rich.console import Console
from rich.panel import Panel

from research_operator.core.advisor import answer_session_query, review_project_brief
from research_operator.core.bibtex_search import find_in_library, search_local_library
from research_operator.core.config import get_config
from research_operator.core.export_md import export_results_to_md
from research_operator.core.llm import estimate_cost
from research_operator.core.vault_export import export_to_vault, get_vault_folders
from research_operator.core.academic_stack import render_stack_report
from research_operator.core.llm import active_provider_label, provider_diagnostics
from research_operator.core.mcp_detect import render_mcp_report
from research_operator.core.memory import list_memories
from research_operator.core.project import ensure_research_layout, init_project_config, research_dir
from research_operator.core.session import ProjectBrief, SessionState
from research_operator.core.scanner import scan_project

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
except Exception:  # pragma: no cover
    PromptSession = None
    FileHistory = None


console = Console()


def start_repl() -> None:
    state = SessionState()
    console.print(
        Panel.fit(
            "Yatiri — Asistente Académico\n"
            "Psicología · Ciencias Sociales · Métodos · Docencia\n\n"
            "Puedes escribir directamente o usar comandos:\n"
            "  /search <tema>     busca en SciELO, OpenAlex, Semantic Scholar, HAL, J-STAGE…\n"
            "  /brief             completa la ficha de tu proyecto de investigación\n"
            "  /review            revisión crítica del proyecto (como evaluador externo)\n"
            "  /export            exporta resultados como fichas .md para Obsidian/Zettlr\n"
            "  /design /teach /write /verify   modos especializados\n"
            "  /doctor            diagnóstico de proveedor activo\n"
            "  /help              lista completa de comandos\n\n"
            f"{active_provider_label()}",
            title="Yatiri",
        )
    )

    session = build_prompt_session()
    while True:
        try:
            user_input = read_input(session, state)
        except (EOFError, KeyboardInterrupt):
            console.print("\nSesión terminada.")
            if state.total_input_tokens > 0:
                console.print(_render_cost(state))
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            should_exit = handle_slash_command(state, user_input)
            if should_exit:
                break
            continue

        response = answer_session_query(state, user_input)
        console.print(response)
        if state.mode == "search" and state.last_search_results:
            _show_library_matches(state, query=state.last_search_query)


def build_prompt_session():
    history_path = Path.home() / ".yatiri" / "repl_history"
    try:
        history_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        history_path = Path("/tmp") / "yatiri_repl_history"
    if PromptSession and FileHistory:
        return PromptSession(history=FileHistory(str(history_path)))
    return None


def read_input(session, state: SessionState) -> str:
    prompt = f"yatiri[{state.mode}]> "
    if session is None:
        return input(prompt).strip()
    return session.prompt(prompt).strip()


def handle_slash_command(state: SessionState, raw: str) -> bool:
    parts = shlex.split(raw)
    command = parts[0].lower()
    args = parts[1:]

    if command in {"/exit", "/quit"}:
        return True
    if command == "/clear":
        state.clear_history()
        console.print("Historial de conversación borrado.")
        return False
    if command == "/help":
        console.print(render_help())
        return False
    if command == "/provider":
        console.print(active_provider_label())
        return False
    if command == "/doctor":
        console.print(provider_diagnostics())
        return False
    if command == "/mcp":
        console.print(render_mcp_report())
        return False
    if command == "/mode":
        if args:
            state.mode = args[0].lower()
            console.print(f"Modo activo: {state.mode}")
        else:
            console.print(f"Modo activo: {state.mode}")
        return False
    if command in {"/search", "/quant", "/qual", "/design", "/teach", "/write", "/verify"}:
        state.mode = command[1:]
        query = " ".join(args)
        if query:
            console.print(answer_session_query(state, query))
            if command == "/search" and state.last_search_results:
                _show_library_matches(state, query=state.last_search_query)
        else:
            console.print(f"Modo activo: {state.mode}")
        return False
    if command == "/export":
        _run_export(state, args)
        return False
    if command == "/cost":
        console.print(_render_cost(state))
        return False
    if command == "/brief":
        run_brief_form(state)
        return False
    if command == "/review":
        console.print("[bold]Revisión crítica del proyecto...[/bold]")
        console.print(review_project_brief(state))
        return False
    if command == "/attach":
        if not args:
            console.print("Uso: /attach /ruta")
            return False
        target = Path(args[0]).expanduser().resolve()
        if not target.exists():
            console.print(f"No existe: {target}")
            return False
        state.attached_path = target
        if not (research_dir(target) / "project.yaml").exists():
            try:
                ensure_research_layout(target)
                init_project_config(target)
                scan_project(target)
            except OSError:
                console.print("No fue posible escribir `.research`. Se adjunta solo para lectura.")
        console.print(f"Contexto adjunto: {target}")
        return False
    if command == "/detach":
        state.attached_path = None
        console.print("Contexto adjunto eliminado.")
        return False
    if command == "/context":
        console.print(render_context(state))
        return False
    if command == "/memory":
        if not args or args[0] == "show":
            console.print(render_memories(state))
            return False
        if args[0] == "pin" and len(args) > 1:
            state.pin_memory(args[1])
            console.print(f"Memoria fijada: {args[1]}")
            return False
        if args[0] == "unpin" and len(args) > 1:
            state.unpin_memory(args[1])
            console.print(f"Memoria liberada: {args[1]}")
            return False
        console.print("Uso: /memory show | /memory pin <nombre> | /memory unpin <nombre>")
        return False
    console.print(f"Comando no reconocido: {command}. Usa /help.")
    return False


def _run_export(state: SessionState, args: list[str]) -> None:
    if not state.last_search_results:
        console.print("No hay resultados de búsqueda en la sesión. Usa /search primero.")
        return

    vault_path_str = get_config("YATIRI_VAULT_PATH")

    # Si hay --vault o vault configurado, exportar con clasificación temática
    use_vault = "--vault" in args or (vault_path_str and "--local" not in args)

    if use_vault and vault_path_str:
        vault_path = Path(vault_path_str).expanduser()
        folders = get_vault_folders(vault_path)
        if folders:
            console.print(f"Exportando al vault: [cyan]{vault_path}[/cyan]")
            summary = export_to_vault(state.last_search_results, vault_path)
            total = sum(len(v) for v in summary.values())
            console.print(f"[green]{total} fichas exportadas:[/green]")
            for folder_name, files in summary.items():
                console.print(f"  {folder_name}/  ({len(files)} fichas)")
                for p in files:
                    console.print(f"    {p.name}")
            return

    # Sin vault: exportar a carpeta especificada o cwd/bibliografía
    output_dir = Path(args[0]).expanduser() if args and not args[0].startswith("--") \
        else Path.cwd() / "bibliografía"
    created = export_results_to_md(state.last_search_results, output_dir)
    if created:
        console.print(f"[green]{len(created)} fichas exportadas en:[/green] {output_dir}")
        for p in created:
            console.print(f"  {p.name}")
    else:
        console.print("No se pudo exportar ningún resultado.")


def _show_library_matches(state: SessionState, query: str = "") -> None:
    """Cruza resultados de búsqueda con la biblioteca BibTeX y muestra entradas relevantes del tema."""
    bib_path_str = get_config("YATIRI_BIBTEX_PATH")
    if not bib_path_str:
        return
    bib_path = Path(bib_path_str).expanduser()
    if not bib_path.exists():
        return

    # 1. Cruce exacto: cada resultado web contra la biblioteca (DOI o título)
    found_in_lib = []
    not_in_lib = []
    for result in state.last_search_results:
        doi = getattr(result, "url", "")
        doi = doi.replace("https://doi.org/", "").strip() if "doi.org" in doi else ""
        title = getattr(result, "title", "")
        match = find_in_library(doi, title, bib_path)
        if match:
            found_in_lib.append((result, match))
        else:
            not_in_lib.append(result)

    # 2. Búsqueda temática directa en la biblioteca con la misma consulta
    local_hits = []
    if query:
        already_shown = {e.key for _, e in found_in_lib}
        local_hits = [e for e in search_local_library(query, bib_path, max_results=5)
                      if e.key not in already_shown]

    if not found_in_lib and not not_in_lib and not local_hits:
        return

    lines = ["\n[dim]── Biblioteca local ──[/dim]"]

    if found_in_lib:
        lines.append(f"[green]Coincidencia exacta ({len(found_in_lib)}):[/green]")
        for result, entry in found_in_lib:
            lines.append(f"  ✓ [{entry.key}]  {getattr(result, 'title', '')[:65]}")

    if local_hits:
        lines.append(f"[cyan]Ya tienes sobre este tema ({len(local_hits)}):[/cyan]")
        for entry in local_hits:
            lines.append(f"  ◆ [{entry.key}]  {entry.short_ref()}")

    if not_in_lib:
        lines.append(f"[yellow]No están en tu biblioteca ({len(not_in_lib)}):[/yellow]")
        for result in not_in_lib[:5]:
            lines.append(f"  – {getattr(result, 'title', '')[:65]}")

    console.print("\n".join(lines))


def _render_cost(state: SessionState) -> str:
    if state.total_input_tokens == 0 and state.total_output_tokens == 0:
        return "Sin uso registrado en esta sesión."
    provider = state.last_provider or "desconocido"
    cost = estimate_cost(provider, state.total_input_tokens, state.total_output_tokens)
    lines = [
        f"Proveedor: {provider}",
        f"Tokens entrada:  {state.total_input_tokens:,}",
        f"Tokens salida:   {state.total_output_tokens:,}",
        f"Total tokens:    {state.total_input_tokens + state.total_output_tokens:,}",
        f"Costo estimado:  ${cost:.4f} USD",
    ]
    if cost < 0.001:
        lines.append("(precio referencial — puede variar según modelo exacto)")
    return "\n".join(lines)


def run_brief_form(state: SessionState) -> None:
    """Formulario interactivo para construir la ficha de proyecto."""
    console.print(
        Panel.fit(
            "Ficha de proyecto de investigación\n"
            "Responde cada campo. Enter vacío para omitir o mantener el valor actual.",
            title="/brief",
        )
    )
    brief = state.brief

    def ask(label: str, current: str = "") -> str:
        hint = f" [{current}]" if current else ""
        try:
            val = input(f"  {label}{hint}: ").strip()
            return val if val else current
        except (EOFError, KeyboardInterrupt):
            return current

    brief.paradigm = ask(
        "Paradigma (cuantitativo / cualitativo / mixto)", brief.paradigm
    )
    brief.context = ask(
        "Contexto (disciplina, país, institución)", brief.context
    )
    brief.phenomenon = ask(
        "Fenómeno o problema de investigación", brief.phenomenon
    )
    brief.research_question = ask(
        "Pregunta de investigación o hipótesis principal", brief.research_question
    )
    brief.general_objective = ask(
        "Objetivo general", brief.general_objective
    )

    console.print("  Objetivos específicos (Enter vacío para terminar):")
    if brief.specific_objectives:
        console.print(f"    Actuales: {brief.specific_objectives}")
        if input("  ¿Reemplazar objetivos específicos? (s/N): ").strip().lower() in {"s", "si", "sí"}:
            brief.specific_objectives = []
    if not brief.specific_objectives:
        while True:
            obj = input(f"    Objetivo {len(brief.specific_objectives)+1}: ").strip()
            if not obj:
                break
            brief.specific_objectives.append(obj)

    brief.theoretical_framework = ask(
        "Marco teórico (teorías, autores clave, conceptos centrales)", brief.theoretical_framework
    )
    brief.methodology = ask(
        "Metodología (diseño, enfoque, técnica de recolección)", brief.methodology
    )
    brief.sample = ask(
        "Participantes / corpus / unidad de análisis", brief.sample
    )
    brief.analysis_plan = ask(
        "Plan de análisis (pruebas, software, categorías)", brief.analysis_plan
    )

    console.print("")
    console.print("[green]Ficha guardada en la sesión.[/green]")
    console.print(brief.to_text())
    console.print("\nUsa [bold]/review[/bold] para obtener revisión crítica del proyecto.")


def render_help() -> str:
    return (
        "\n[bold]Consultas:[/bold]\n"
        "  /search <consulta>    búsqueda académica (SciELO, OpenAlex, SS, PubMed, HAL, J-STAGE)\n"
        "  /design <consulta>    diseño de investigación\n"
        "  /quant <consulta>     metodología cuantitativa\n"
        "  /qual  <consulta>     metodología cualitativa\n"
        "  /teach <consulta>     planificación docente\n"
        "  /write <consulta>     redacción académica\n"
        "  /verify <consulta>    revisión crítica de argumentos\n"
        "\n[bold]Proyecto:[/bold]\n"
        "  /brief                completar ficha de proyecto (paradigma, pregunta, objetivos…)\n"
        "  /review               revisión crítica del proyecto como evaluador externo\n"
        "  /export [ruta]        exportar como fichas .md — a vault Obsidian si está configurado\n"
        "  /export --local [ruta] exportar a carpeta local (ignora vault configurado)\n"
        "  /attach <ruta>        adjuntar carpeta de proyecto como contexto\n"
        "  /detach               quitar contexto adjunto\n"
        "\n[bold]Sesión:[/bold]\n"
        "  /mode <modo>          cambiar modo activo\n"
        "  /context              ver estado de la sesión\n"
        "  /clear                borrar historial de conversación\n"
        "  /memory show          ver memorias disponibles\n"
        "  /memory pin <nombre>  fijar memoria en el contexto\n"
        "\n[bold]Sistema:[/bold]\n"
        "  /cost                 tokens y costo estimado de la sesión\n"
        "  /provider             ver proveedor activo\n"
        "  /doctor               diagnóstico completo de proveedores\n"
        "  /mcp                  ver MCPs detectados\n"
        "  /exit                 salir (muestra costo si hay uso)\n"
    )


def render_context(state: SessionState) -> str:
    lines = [
        f"Modo: {state.mode}",
        f"Contexto adjunto: {state.attached_path or 'ninguno'}",
        f"Memorias fijadas: {', '.join(state.pinned_memories) or 'ninguna'}",
        f"Historial: {len(state.messages)//2} intercambios",
    ]
    if not state.brief.is_empty():
        lines.append("Ficha de proyecto: cargada (usa /review para revisión crítica)")
    else:
        lines.append("Ficha de proyecto: vacía (usa /brief para completarla)")
    return "\n".join(lines)


def render_memories(state: SessionState) -> str:
    lines = ["Memorias disponibles:"]
    for memory in list_memories():
        marker = "*" if memory.slug in state.pinned_memories else "-"
        lines.append(f"{marker} {memory.slug}: {memory.title}")
    return "\n".join(lines)
