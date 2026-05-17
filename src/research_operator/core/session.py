from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

_MAX_HISTORY = 20  # máximo de mensajes almacenados (10 intercambios)


@dataclass
class ProjectBrief:
    """Ficha estructurada de proyecto de investigación."""
    paradigm: str = ""           # cuantitativo / cualitativo / mixto
    phenomenon: str = ""         # fenómeno o problema central
    research_question: str = ""  # pregunta principal o hipótesis
    general_objective: str = ""
    specific_objectives: list[str] = field(default_factory=list)
    theoretical_framework: str = ""
    methodology: str = ""
    sample: str = ""             # participantes, corpus, unidad de análisis
    analysis_plan: str = ""
    context: str = ""            # país, institución, disciplina

    def is_empty(self) -> bool:
        return not any([
            self.phenomenon, self.research_question, self.general_objective,
        ])

    def to_text(self) -> str:
        lines = ["=== FICHA DE PROYECTO ==="]
        if self.paradigm:
            lines.append(f"Paradigma: {self.paradigm}")
        if self.context:
            lines.append(f"Contexto: {self.context}")
        if self.phenomenon:
            lines.append(f"Fenómeno/problema: {self.phenomenon}")
        if self.research_question:
            lines.append(f"Pregunta / hipótesis: {self.research_question}")
        if self.general_objective:
            lines.append(f"Objetivo general: {self.general_objective}")
        if self.specific_objectives:
            lines.append("Objetivos específicos:")
            for i, obj in enumerate(self.specific_objectives, 1):
                lines.append(f"  {i}. {obj}")
        if self.theoretical_framework:
            lines.append(f"Marco teórico: {self.theoretical_framework}")
        if self.methodology:
            lines.append(f"Metodología: {self.methodology}")
        if self.sample:
            lines.append(f"Participantes / corpus: {self.sample}")
        if self.analysis_plan:
            lines.append(f"Plan de análisis: {self.analysis_plan}")
        return "\n".join(lines)


@dataclass(slots=False)
class SessionState:
    mode: str = "general"
    attached_path: Path | None = None
    pinned_memories: list[str] = field(default_factory=list)
    messages: list[dict] = field(default_factory=list)
    brief: ProjectBrief = field(default_factory=ProjectBrief)
    last_search_results: list = field(default_factory=list)
    last_search_query: str = ""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    last_provider: str = ""

    def record_usage(self, provider: str, input_tokens: int, output_tokens: int) -> None:
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        if provider:
            self.last_provider = provider

    def pin_memory(self, slug: str) -> None:
        if slug not in self.pinned_memories:
            self.pinned_memories.append(slug)

    def unpin_memory(self, slug: str) -> None:
        if slug in self.pinned_memories:
            self.pinned_memories.remove(slug)

    def add_exchange(self, user_content: str, assistant_content: str) -> None:
        self.messages.append({"role": "user", "content": user_content})
        self.messages.append({"role": "assistant", "content": assistant_content})
        if len(self.messages) > _MAX_HISTORY:
            self.messages = self.messages[-_MAX_HISTORY:]

    def clear_history(self) -> None:
        self.messages.clear()
