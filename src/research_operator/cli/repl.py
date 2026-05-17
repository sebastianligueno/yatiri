from __future__ import annotations

from pathlib import Path
import shlex

from rich.console import Console
from rich.panel import Panel

from research_operator.core.advisor import answer_session_query
from research_operator.core.academic_stack import render_stack_report
from research_operator.core.llm import active_provider_label, provider_diagnostics
from research_operator.core.mcp_detect import render_mcp_report
from research_operator.core.memory import list_memories
from research_operator.core.project import ensure_research_layout, init_project_config, research_dir
from research_operator.core.session import SessionState
from research_operator.core.scanner import scan_project

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
except Exception:  # pragma: no cover - optional fallback
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
                console.print("No fue posible escribir `.research` en esa ruta. Se adjunta solo para lectura.")
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
    console.print(f"Comando no reconocido: {command}")
    return False


def render_help() -> str:
    return (
        "/help\n"
        "/mode <general|search|quant|qual|design|teach|write|verify>\n"
        "/search <consulta>\n"
        "/quant <consulta>\n"
        "/qual <consulta>\n"
        "/design <consulta>\n"
        "/teach <consulta>\n"
        "/write <consulta>\n"
        "/verify <consulta>\n"
        "/attach <ruta>\n"
        "/detach\n"
        "/context\n"
        "/clear\n"
        "/memory show\n"
        "/memory pin <nombre>\n"
        "/memory unpin <nombre>\n"
        "/provider\n"
        "/doctor\n"
        "/mcp\n"
        "/exit"
    )


def render_context(state: SessionState) -> str:
    attached = str(state.attached_path) if state.attached_path else "ninguno"
    pinned = ", ".join(state.pinned_memories) if state.pinned_memories else "ninguna"
    return f"Modo: {state.mode}\nContexto adjunto: {attached}\nMemorias fijadas: {pinned}"


def render_memories(state: SessionState) -> str:
    lines = ["Memorias disponibles:"]
    for memory in list_memories():
        marker = "*" if memory.slug in state.pinned_memories else "-"
        lines.append(f"{marker} {memory.slug}: {memory.title}")
    return "\n".join(lines)
