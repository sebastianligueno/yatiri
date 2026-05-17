from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

_MAX_HISTORY = 20  # máximo de mensajes almacenados (10 intercambios)


@dataclass(slots=True)
class SessionState:
    mode: str = "general"
    attached_path: Path | None = None
    pinned_memories: list[str] = field(default_factory=list)
    messages: list[dict] = field(default_factory=list)

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
