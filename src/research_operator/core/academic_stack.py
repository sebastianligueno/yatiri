from __future__ import annotations

from dataclasses import dataclass
import os
import shutil


@dataclass(slots=True)
class StackItem:
    name: str
    kind: str
    status: str
    integration: str
    note: str
    priority: int = 99


def current_stack() -> list[StackItem]:
    deepseek_key = bool(os.environ.get("DEEPSEEK_API_KEY"))
    ollama_url = os.environ.get("SCHOLAR_OLLAMA_URL", "http://localhost:11434/api/chat")
    freeplane_bin = shutil.which("freeplane")

    return [
        StackItem(
            name="DeepSeek API",
            kind="client",
            status="configured" if deepseek_key else "missing_config",
            integration="integrated",
            note="Cliente principal remoto para respuestas conversacionales.",
        ),
        StackItem(
            name="Ollama",
            kind="client",
            status="configured_url",
            integration="integrated",
            note=f"Respaldo local esperado en {ollama_url}. Requiere daemon y modelo descargado.",
        ),
        StackItem(
            name="DuckDuckGo HTML",
            kind="client",
            status="fragile",
            integration="integrated",
            note="Búsqueda web simple por scraping HTML; fallback de último recurso. Frágil ante cambios de estructura.",
        ),
        StackItem(
            name="OpenAlex API",
            kind="client",
            status="integrated",
            integration="integrated",
            note="Búsqueda académica abierta y gratuita: 250M+ works, autores, venues, citas. Sin clave requerida.",
        ),
        StackItem(
            name="Freeplane MCP",
            kind="concept_map_mcp",
            status="installed_local" if freeplane_bin else "not_detected",
            integration="external_official",
            note=(
                f"Servidor MCP oficial para mapas conceptuales en Freeplane; binario detectado en {freeplane_bin}."
                if freeplane_bin
                else "Servidor MCP oficial de Freeplane disponible, pero no se detectó el binario local."
            ),
            priority=10,
        ),
        StackItem(
            name="scite MCP",
            kind="academic_mcp",
            status="active_in_codex",
            integration="not_integrated",
            note="Fuerte para verificación con citas inteligentes, alertas editoriales y lectura focalizada.",
            priority=1,
        ),
        StackItem(
            name="PubMed or Europe PMC",
            kind="academic_mcp",
            status="active_in_codex",
            integration="not_integrated",
            note="Prioridad alta cuando el tema toca clínica, salud mental, neurociencia afectiva o psicobiología.",
            priority=2,
        ),
        StackItem(
            name="Scopus MCP",
            kind="academic_mcp",
            status="active_in_codex",
            integration="not_integrated",
            note="Útil para autores, afiliaciones, revistas, métricas y BibTeX por DOI.",
            priority=3,
        ),
        StackItem(
            name="Zotero MCP",
            kind="academic_mcp",
            status="active_in_codex",
            integration="not_integrated",
            note="Útil para consultar biblioteca propia y enriquecerla con señales de scite.",
            priority=4,
        ),
        StackItem(
            name="Consensus MCP",
            kind="academic_mcp",
            status="active_in_codex",
            integration="not_integrated",
            note="Bueno para descubrimiento rápido de literatura y mapeo inicial de evidencia; dejarlo como complemento permanente aunque el saldo actual esté agotado.",
            priority=5,
        ),
        StackItem(
            name="SciELO",
            kind="spanish_open",
            status="integrated",
            integration="integrated",
            note="Fuente abierta prioritaria en español y portugués; integrada en modo search con ArticleMeta y fallback HTML.",
            priority=6,
        ),
        StackItem(
            name="Redalyc",
            kind="spanish_open",
            status="candidate",
            integration="not_integrated",
            note="Complemento abierto importante para ciencias sociales y humanidades en español.",
            priority=7,
        ),
        StackItem(
            name="Dialnet",
            kind="spanish_open",
            status="candidate",
            integration="not_integrated",
            note="Útil para artículos, capítulos, tesis y revistas del ámbito hispanohablante.",
            priority=8,
        ),
        StackItem(
            name="Latindex",
            kind="spanish_open",
            status="candidate",
            integration="not_integrated",
            note="Más útil para identificación y evaluación de revistas que para recuperación profunda de texto.",
            priority=9,
        ),
        StackItem(
            name="OpenAlex (avanzado)",
            kind="candidate",
            status="candidate",
            integration="partial",
            note="Búsqueda básica integrada. Pendiente: filtros por año, tipo de estudio, cited-by, y autores.",
        ),
        StackItem(
            name="Crossref",
            kind="candidate",
            status="candidate",
            integration="not_integrated",
            note="Útil para DOI, metadatos, referencias y resolución bibliográfica reproducible.",
        ),
        StackItem(
            name="Europe PMC API",
            kind="candidate",
            status="candidate",
            integration="not_integrated",
            note="Conector abierto recomendable para extracción biomédica reproducible si se implementa integración técnica propia.",
        ),
    ]


def render_stack_report() -> str:
    lines = [
        "Academic stack:",
        "Clientes integrados:",
    ]

    for item in current_stack():
        if item.kind != "client":
            continue
        lines.append(f"- {item.name} | status={item.status} | integration={item.integration}")
        lines.append(f"  {item.note}")

    lines.append("")
    lines.append("MCP de mapas conceptuales:")
    for item in sorted(current_stack(), key=lambda item: item.priority):
        if item.kind != "concept_map_mcp":
            continue
        lines.append(f"- {item.name} | status={item.status} | integration={item.integration}")
        lines.append(f"  {item.note}")

    lines.append("")
    lines.append("Prioridad académica vigente:")
    for item in sorted(current_stack(), key=lambda item: item.priority):
        if item.kind not in {"academic_mcp", "spanish_open"}:
            continue
        lines.append(f"- P{item.priority}: {item.name} | status={item.status} | integration={item.integration}")
        lines.append(f"  {item.note}")

    lines.append("")
    lines.append("MCP académicos vigentes en el entorno:")
    for item in sorted(current_stack(), key=lambda item: item.priority):
        if item.kind != "academic_mcp":
            continue
        lines.append(f"- {item.name} | status={item.status} | integration={item.integration}")
        lines.append(f"  {item.note}")

    lines.append("")
    lines.append("Fuentes abiertas en español recomendadas:")
    for item in sorted(current_stack(), key=lambda item: item.priority):
        if item.kind != "spanish_open":
            continue
        lines.append(f"- {item.name} | status={item.status} | integration={item.integration}")
        lines.append(f"  {item.note}")

    lines.append("")
    lines.append("MCP o conectores recomendables a sumar:")
    for item in sorted(current_stack(), key=lambda item: item.priority):
        if item.kind != "candidate":
            continue
        lines.append(f"- {item.name} | status={item.status} | integration={item.integration}")
        lines.append(f"  {item.note}")

    return "\n".join(lines)
