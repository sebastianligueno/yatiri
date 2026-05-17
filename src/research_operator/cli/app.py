from __future__ import annotations

import argparse
from pathlib import Path
import sys

from research_operator.cli.ask import run_ask
from research_operator.cli.init import run_init
from research_operator.cli.repl import start_repl
from research_operator.cli.run import run_step
from research_operator.cli.scan import run_scan
from research_operator.cli.setup import run_setup
from research_operator.cli.status import run_status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yatiri",
        description="Yatiri — Asistente académico de terminal para investigación en Iberoamérica",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    chat_parser = subparsers.add_parser("chat", help="Consulta rápida no interactiva")
    chat_parser.add_argument("question", help="Consulta a resolver")
    chat_parser.add_argument("--mode", default="general", help="Modo: general, search, quant, qual, design, teach, write, verify")
    chat_parser.add_argument("--attach", default=None, help="Ruta opcional para adjuntar contexto")

    subparsers.add_parser("setup", help="Configura API key y proveedor de forma interactiva")

    init_parser = subparsers.add_parser("init", help="Inicializa workspace de investigación en la ruta indicada")
    init_parser.add_argument("path", nargs="?", default=".", help="Ruta del proyecto")

    scan_parser = subparsers.add_parser("scan", help="Escanea un proyecto y genera reporte")
    scan_parser.add_argument("path", nargs="?", default=".", help="Ruta del proyecto")

    status_parser = subparsers.add_parser("status", help="Muestra estado del proyecto")
    status_parser.add_argument("path", nargs="?", default=".", help="Ruta del proyecto")

    ask_parser = subparsers.add_parser("ask", help="Responde preguntas usando archivos del proyecto")
    ask_parser.add_argument("question", help="Pregunta sobre el proyecto")
    ask_parser.add_argument("path", nargs="?", default=".", help="Ruta del proyecto")

    run_parser = subparsers.add_parser("run", help="Ejecuta un paso del pipeline")
    run_parser.add_argument("step_id", help="Identificador del paso")
    run_parser.add_argument("path", nargs="?", default=".", help="Ruta del proyecto")

    return parser


def main() -> None:
    if len(sys.argv) == 1:
        start_repl()
        return

    parser = build_parser()
    args = parser.parse_args()
    if args.command == "chat":
        from research_operator.core.advisor import answer_session_query
        from research_operator.core.project import ensure_research_layout, init_project_config, research_dir
        from research_operator.core.scanner import scan_project
        from research_operator.core.session import SessionState

        state = SessionState(mode=args.mode)
        if args.attach:
            root = Path(args.attach).expanduser().resolve()
            if (research_dir(root) / "project.yaml").exists():
                state.attached_path = root
            else:
                try:
                    ensure_research_layout(root)
                    init_project_config(root)
                    scan_project(root)
                except OSError:
                    pass
            state.attached_path = root
        print(answer_session_query(state, args.question))
        return
    if args.command == "setup":
        run_setup()
        return
    if args.command == "init":
        root = Path(args.path).expanduser().resolve()
        run_init(root)
        return
    if args.command == "scan":
        root = Path(args.path).expanduser().resolve()
        run_scan(root)
        return
    if args.command == "status":
        root = Path(args.path).expanduser().resolve()
        run_status(root)
        return
    if args.command == "ask":
        root = Path(args.path).expanduser().resolve()
        run_ask(root, args.question)
        return
    if args.command == "run":
        root = Path(args.path).expanduser().resolve()
        run_step(root, args.step_id)
        return

    parser.error(f"Comando no soportado: {args.command}")
