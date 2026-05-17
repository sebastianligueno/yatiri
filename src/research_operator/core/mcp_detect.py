from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


# Capacidades que cada MCP aporta
_MCP_CAPABILITIES: dict[str, dict] = {
    "zotero":           {"cap": "bibliography",   "label": "Zotero",           "desc": "Biblioteca personal, notas, PDFs"},
    "scite":            {"cap": "verification",   "label": "Scite",            "desc": "Smart citations, retracciones, lectura focalizada"},
    "scopus-mcp":       {"cap": "metrics",        "label": "Scopus",           "desc": "Métricas de autores, revistas y afiliaciones"},
    "semantic-scholar": {"cap": "discovery",      "label": "Semantic Scholar", "desc": "Descubrimiento amplio, grafos de citación"},
    "openalex":         {"cap": "open_access",    "label": "OpenAlex",         "desc": "250M+ works, open access, sin clave"},
    "freeplane":        {"cap": "concept_maps",   "label": "Freeplane",        "desc": "Mapas conceptuales en terminal"},
    "bx-scholar":       {"cap": "search",         "label": "BX Scholar",       "desc": "Búsqueda académica adicional"},
    # MCPs remotos de Claude.ai
    "claude.ai Consensus":        {"cap": "discovery",    "label": "Consensus",        "desc": "Descubrimiento rápido, resúmenes de evidencia"},
    "claude.ai PubMed":           {"cap": "biomedical",   "label": "PubMed",           "desc": "Biomedicina, psicología clínica, neurociencia"},
    "claude.ai Scholar Gateway":  {"cap": "fulltext",     "label": "Wiley/Scholar",    "desc": "Acceso a texto completo Wiley/Blackwell"},
    "claude.ai Hugging Face":     {"cap": "models",       "label": "Hugging Face",     "desc": "Modelos, datasets, papers de ML"},
}

# MCPs recomendados que podrían no estar instalados
_RECOMMENDED: list[dict] = [
    {
        "name": "zotero",
        "label": "Zotero MCP",
        "install": "pip install zotero-mcp",
        "why": "Conecta tu biblioteca personal. Esencial para recuperar y enriquecer referencias propias.",
        "priority": 1,
    },
    {
        "name": "scite",
        "label": "Scite MCP",
        "install": "claude mcp add scite --transport http https://api.scite.ai/mcp",
        "why": "Smart citations: verifica si un paper fue respaldado, refutado o mencionado. Detecta retracciones.",
        "priority": 2,
    },
    {
        "name": "semantic-scholar",
        "label": "Semantic Scholar MCP",
        "install": "pip install semantic-scholar-mcp && claude mcp add semantic-scholar -- semantic-scholar-mcp",
        "why": "Grafos de citación, papers influyentes, búsqueda semántica. Cubre arXiv y más.",
        "priority": 3,
    },
    {
        "name": "openalex",
        "label": "OpenAlex MCP",
        "install": "npm install -g openalex-mcp && claude mcp add openalex -- openalex-mcp",
        "why": "250M+ works, open access. Alternativa abierta a Scopus/WoS. Sin clave.",
        "priority": 4,
    },
]


@dataclass
class McpStatus:
    name: str
    label: str
    cap: str
    desc: str
    installed: bool
    url_or_cmd: str = ""


@dataclass
class McpReport:
    installed: list[McpStatus] = field(default_factory=list)
    missing_recommended: list[dict] = field(default_factory=list)

    def has_cap(self, cap: str) -> bool:
        return any(m.installed and m.cap == cap for m in self.installed)


def detect_mcps() -> McpReport:
    """Lee la configuración de Claude Code y detecta qué MCPs están disponibles."""
    configured = _read_claude_settings()
    report = McpReport()

    for raw_name, cfg in configured.items():
        url_or_cmd = cfg.get("url") or cfg.get("command") or ""
        info = _resolve_info(raw_name)
        report.installed.append(
            McpStatus(
                name=raw_name,
                label=info["label"],
                cap=info["cap"],
                desc=info["desc"],
                installed=True,
                url_or_cmd=str(url_or_cmd),
            )
        )

    installed_names = {m.name for m in report.installed}
    for rec in sorted(_RECOMMENDED, key=lambda r: r["priority"]):
        if rec["name"] not in installed_names:
            report.missing_recommended.append(rec)

    return report


def render_mcp_report() -> str:
    report = detect_mcps()
    lines = ["MCPs detectados en el entorno:", ""]

    if report.installed:
        for m in report.installed:
            lines.append(f"  [{m.cap}] {m.label}")
            lines.append(f"    {m.desc}")
    else:
        lines.append("  Ningún MCP detectado en ~/.claude/settings.json")

    if report.missing_recommended:
        lines.append("")
        lines.append("MCPs recomendados no instalados:")
        for rec in report.missing_recommended:
            lines.append(f"  P{rec['priority']}. {rec['label']}")
            lines.append(f"    {rec['why']}")
            lines.append(f"    Instalar: {rec['install']}")

    return "\n".join(lines)


def _read_claude_settings() -> dict[str, dict]:
    """Lee los servidores MCP configurados en Claude Code."""
    for path in [
        Path.home() / ".claude" / "settings.json",
        Path.home() / ".config" / "claude" / "settings.json",
    ]:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return data.get("mcpServers", {})
            except Exception:
                continue
    return {}


def _resolve_info(name: str) -> dict:
    """Busca la info de un MCP por nombre exacto o por substring."""
    if name in _MCP_CAPABILITIES:
        return _MCP_CAPABILITIES[name]
    name_lower = name.lower()
    for key, info in _MCP_CAPABILITIES.items():
        if key.lower() in name_lower or name_lower in key.lower():
            return info
    return {"cap": "other", "label": name, "desc": "MCP adicional configurado"}
