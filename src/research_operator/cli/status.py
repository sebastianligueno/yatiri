from __future__ import annotations

from pathlib import Path

from research_operator.core.project import load_project_state


def run_status(root: Path) -> None:
    state = load_project_state(root)

    print(f"Proyecto: {state.project_name}")
    print(f"Raiz: {state.root}")
    print(f"Perfil: {state.profile_id}")
    print(f"Config: {state.config_path}")
    print(f"Fuentes registradas: {state.source_count}")
    print(f"Ejecuciones registradas: {state.run_count}")
    print(f"Claims registradas: {state.claim_count}")
    print("Chequeos:")
    for check in state.checks:
        print(f"- [{check.status}] {check.label}")
