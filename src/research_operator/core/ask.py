from __future__ import annotations

from pathlib import Path
import re

from research_operator.core.project import load_project_config, research_dir
from research_operator.core.registry import read_jsonl_records


def answer_question(root: Path, question: str) -> str:
    cfg = load_project_config(root)
    sources = read_jsonl_records(research_dir(root) / "sources.jsonl")
    if not sources:
        return "No hay fuentes indexadas todavía. Corre `research scan` primero."

    ranked = rank_sources(root, sources, question)
    snippets: list[tuple[str, str]] = []
    for source in ranked[:5]:
        snippet = extract_snippet(root / source["path"], question)
        snippets.append((source["path"], snippet))

    return build_answer(cfg, question, snippets)


def rank_sources(root: Path, sources: list[dict], question: str) -> list[dict]:
    tokens = tokenize(question)
    scored: list[tuple[int, dict]] = []

    for source in sources:
        rel_path = source["path"].lower()
        score = sum(2 for token in tokens if token in rel_path)
        score += role_bonus(source.get("role", ""), tokens)
        score += content_bonus(root, source, tokens)
        if score == 0:
            score = fallback_score(source)
        scored.append((score, source))

    scored.sort(key=lambda item: (-item[0], item[1]["path"]))
    return [item[1] for item in scored]


def extract_snippet(path: Path, question: str) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return "No fue posible leer este archivo como texto."

    compact = re.sub(r"\s+", " ", text)
    tokens = tokenize(question)
    for token in tokens:
        idx = compact.lower().find(token)
        if idx >= 0:
            start = max(0, idx - 90)
            end = min(len(compact), idx + 220)
            return compact[start:end].strip()

    return compact[:260].strip() if compact else "Archivo textual sin contenido legible."


def build_answer(cfg: dict, question: str, snippets: list[tuple[str, str]]) -> str:
    profile = cfg.get("project", {}).get("profile", "mixed_methods")
    lines = [
        f"Pregunta: {question}",
        f"Perfil del proyecto: {profile}",
        "",
        "Lectura preliminar:",
    ]

    for path, snippet in snippets:
        lines.append(f"- `{path}`: {snippet}")

    lines.extend(["", "Base documental:"])
    for path, _ in snippets:
        lines.append(f"- `{path}`")

    return "\n".join(lines)


def tokenize(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-zA-ZáéíóúñÁÉÍÓÚÑ]{4,}", text.lower())]


def role_bonus(role: str, tokens: list[str]) -> int:
    joined = " ".join(tokens)
    bonus = 0
    if "ruta" in joined or "reproduc" in joined:
        if role in {"project_doc", "pipeline", "derived_data", "manuscript"}:
            bonus += 4
    if "metod" in joined or "protoc" in joined:
        if role in {"project_doc", "pipeline"}:
            bonus += 4
    if "manuscrito" in joined or "articulo" in joined:
        if role == "manuscript":
            bonus += 4
    return bonus


def content_bonus(root: Path, source: dict, tokens: list[str]) -> int:
    try:
        path = Path(source["path"])
    except Exception:
        return 0

    suffix = path.suffix.lower()
    if suffix not in {".md", ".qmd", ".py", ".r", ".csv"}:
        return 0

    full_path = root / source["path"]
    if not full_path.exists():
        return 0

    try:
        text = full_path.read_text(encoding="utf-8", errors="ignore")[:5000].lower()
    except Exception:
        return 0

    return sum(3 for token in tokens if token in text)


def fallback_score(source: dict) -> int:
    role = source.get("role", "")
    if role == "project_doc":
        return 3
    if role == "pipeline":
        return 2
    if role == "manuscript":
        return 2
    return 1
