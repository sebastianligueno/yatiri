from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


MEMORY_DIR = Path.home() / ".yatiri" / "memories"


@dataclass(slots=True)
class MemoryNote:
    slug: str
    title: str
    path: Path


def list_memories() -> list[MemoryNote]:
    if not MEMORY_DIR.exists():
        return []
    notes: list[MemoryNote] = []
    for path in sorted(MEMORY_DIR.glob("*.md")):
        notes.append(
            MemoryNote(
                slug=path.stem,
                title=extract_title(path),
                path=path,
            )
        )
    return notes


def load_memory_text(slug: str) -> str | None:
    for note in list_memories():
        if note.slug == slug:
            return note.path.read_text(encoding="utf-8", errors="ignore")
    return None


def extract_title(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
        if line:
            return re.sub(r"\s+", " ", line)[:80]
    return path.stem
