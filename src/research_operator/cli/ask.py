from __future__ import annotations

from pathlib import Path

from research_operator.core.ask import answer_question
from research_operator.core.project import ensure_research_layout, init_project_config


def run_ask(root: Path, question: str) -> None:
    ensure_research_layout(root)
    init_project_config(root)
    print(answer_question(root, question))
