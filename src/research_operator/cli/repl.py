from __future__ import annotations

from pathlib import Path
import shlex

from rich.console import Console
from rich.panel import Panel

from research_operator.core.advisor import answer_session_query, review_project_brief
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
            "Yatiri — Asistente Académico\nPsicología | Ciencias Sociales | Métodos | Docencia\n"
            "Escriba una consulta o use /help\n"
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
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            should_exit = handle_slash_command(state, user_input)
            if should_exit:
                break
            continue

        console.print(answer_session_query(state, user_input))


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
        else:
            console.print(f"Modo activo: {state.mode}")
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
        "  /attach <ruta>        adjuntar carpeta de proyecto como contexto\n"
        "  /detach               quitar contexto adjunto\n"
        "\n[bold]Sesión:[/bold]\n"
        "  /mode <modo>          cambiar modo activo\n"
        "  /context              ver estado de la sesión\n"
        "  /clear                borrar historial de conversación\n"
        "  /memory show          ver memorias disponibles\n"
        "  /memory pin <nombre>  fijar memoria en el contexto\n"
        "\n[bold]Sistema:[/bold]\n"
        "  /provider             ver proveedor activo\n"
        "  /doctor               diagnóstico completo de proveedores\n"
        "  /mcp                  ver MCPs detectados\n"
        "  /exit                 salir\n"
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
