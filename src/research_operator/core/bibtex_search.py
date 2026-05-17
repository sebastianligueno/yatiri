"""Búsqueda en biblioteca BibTeX local.

Lee el archivo .bib configurado en YATIRI_BIBTEX_PATH y cruza
resultados de búsqueda con lo que ya existe en la biblioteca del usuario.
Parser minimalista sin dependencias externas, maneja llaves anidadas.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass
class BibEntry:
    key: str
    entry_type: str
    title: str = ""
    author: str = ""
    year: str = ""
    doi: str = ""
    journal: str = ""
    keywords: str = ""
    abstract: str = ""

    def matches(self, query: str) -> int:
        tokens = _tokenize(query)
        haystack = " ".join([
            self.title, self.author, self.keywords, self.abstract, self.year
        ]).lower()
        return sum(1 for t in tokens if t in haystack)

    def matches_doi(self, doi: str) -> bool:
        if not doi or not self.doi:
            return False
        return self.doi.strip().lower() == doi.strip().lower()

    def short_ref(self) -> str:
        author_last = self.author.split(" and ")[0].split(",")[0].strip() if self.author else ""
        suffix = " et al." if " and " in self.author else ""
        year = f" ({self.year})" if self.year else ""
        return f"{author_last}{suffix}{year} — {self.title[:70]}"


@lru_cache(maxsize=1)
def _load_library(bib_path: str) -> list[BibEntry]:
    path = Path(bib_path)
    if not path.exists():
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    return _parse_bib(text)


def search_local_library(query: str, bib_path: Path, max_results: int = 5) -> list[BibEntry]:
    entries = _load_library(str(bib_path))
    if not entries:
        return []
    scored = [(e.matches(query), e) for e in entries]
    scored = [(s, e) for s, e in scored if s > 0]
    scored.sort(key=lambda x: -x[0])
    return [e for _, e in scored[:max_results]]


def find_in_library(doi: str, title: str, bib_path: Path) -> BibEntry | None:
    entries = _load_library(str(bib_path))
    if doi:
        for e in entries:
            if e.matches_doi(doi):
                return e
    if title:
        title_tokens = set(_tokenize(title))
        if not title_tokens:
            return None
        best_score, best = 0.0, None
        for e in entries:
            entry_tokens = set(_tokenize(e.title))
            if not entry_tokens:
                continue
            overlap = len(title_tokens & entry_tokens) / len(title_tokens)
            if overlap > best_score:
                best_score, best = overlap, e
        if best_score >= 0.7:
            return best
    return None


# ── Parser ────────────────────────────────────────────────────────────────────

def _parse_bib(text: str) -> list[BibEntry]:
    entries = []
    for entry_type, body in _split_entries(text):
        if entry_type in {"comment", "string", "preamble"}:
            continue
        body = body.strip()
        # Detectar clave de cita en la primera línea no vacía (ej. "authorYEARword,")
        # Algunos exportadores ponen la clave en la segunda línea tras un salto después de {
        key = ""
        for _line in body.split("\n"):
            candidate = _line.strip().rstrip(",")
            if not candidate:
                continue
            if "=" not in candidate and not candidate.startswith("{"):
                key = candidate
                body = body[body.find(_line) + len(_line):].lstrip(",\n ")
            break
        fields = _extract_fields(body)
        title = _clean(fields.get("title", ""))
        if not title:
            continue
        if not key:
            raw_author = _clean(fields.get("author", "noauthor"))
            author_last = re.sub(r"[{}]", "", re.split(r"[,\s]", raw_author)[0]).lower()
            year = fields.get("year", "")
            title_word = re.findall(r"[a-zA-Z]{4,}", title.lower())
            key = f"{author_last}{year}{title_word[0] if title_word else 'notitle'}"
        entries.append(BibEntry(
            key=key,
            entry_type=entry_type,
            title=title,
            author=_clean(fields.get("author", "")),
            year=_clean(fields.get("year", "")),
            doi=_clean(fields.get("doi", "")),
            journal=_clean(fields.get("journal", fields.get("booktitle", ""))),
            keywords=_clean(fields.get("keywords", "")),
            abstract=_clean(fields.get("abstract", ""))[:400],
        ))
    return entries


def _split_entries(text: str):
    """Divide el .bib en bloques (entry_type, body) respetando llaves anidadas."""
    i = 0
    n = len(text)
    while i < n:
        # Buscar inicio de entrada @type{
        at = text.find("@", i)
        if at == -1:
            break
        # Leer tipo
        m = re.match(r"@(\w+)\s*\{", text[at:], re.IGNORECASE)
        if not m:
            i = at + 1
            continue
        entry_type = m.group(1).lower()
        start = at + m.end()  # justo después de la llave de apertura
        # Avanzar balanceando llaves
        depth = 1
        j = start
        while j < n and depth > 0:
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
            j += 1
        body = text[start:j - 1]  # sin la llave de cierre
        yield entry_type, body
        i = j


def _extract_fields(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    # Campos con llaves anidadas: field = {value {nested} more}
    i = 0
    n = len(body)
    while i < n:
        # Buscar field =
        m = re.search(r'(\w+)\s*=\s*', body[i:])
        if not m:
            break
        fname = m.group(1).lower()
        pos = i + m.end()
        if pos >= n:
            break
        c = body[pos]
        if c == "{":
            # Extraer valor balanceando llaves
            depth = 1
            j = pos + 1
            while j < n and depth > 0:
                if body[j] == "{":
                    depth += 1
                elif body[j] == "}":
                    depth -= 1
                j += 1
            fields[fname] = body[pos + 1:j - 1]
            i = j
        elif c == '"':
            end = body.find('"', pos + 1)
            if end == -1:
                break
            fields[fname] = body[pos + 1:end]
            i = end + 1
        else:
            # Valor sin delimitador (año numérico)
            vm = re.match(r'(\d+)', body[pos:])
            if vm:
                fields[fname] = vm.group(1)
            i = pos + 1
    return fields


def _clean(text: str) -> str:
    text = re.sub(r'\{\{([^{}]+)\}\}', r'\1', text)  # {{word}} → word
    text = re.sub(r'\{([^{}]+)\}', r'\1', text)       # {word} → word
    text = re.sub(r'\\[a-zA-Z]+\{([^{}]*)\}', r'\1', text)
    text = re.sub(r"\\['`\"^~=.]?\{?([a-zA-Z])\}?", r'\1', text)
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    return " ".join(text.split()).strip()


def _tokenize(text: str) -> list[str]:
    return re.findall(r'[a-zA-ZáéíóúñÁÉÍÓÚÑ]{4,}', text.lower())
