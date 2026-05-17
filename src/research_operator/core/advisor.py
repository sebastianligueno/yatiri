from __future__ import annotations

from pathlib import Path
import re

from research_operator.core.ask import extract_snippet
from research_operator.core.config import get_region
from research_operator.core.llm import active_provider_label, chat_completion, provider_diagnostics
from research_operator.core.memory import load_memory_text
from research_operator.core.openalex import search_openalex
from research_operator.core.profiles import infer_profile
from research_operator.core.project import research_dir
from research_operator.core.pubmed import search_pubmed
from research_operator.core.registry import read_jsonl_records
from research_operator.core.scielo import search_scielo
from research_operator.core.semantic_scholar import search_semantic_scholar
from research_operator.core.session import SessionState
from research_operator.core.web_search import search_web


_EPISTEMIC_BASE = (
    "Normas epistémicas irrenunciables: "
    "(1) distingue siempre entre lo que proviene de fuentes recuperadas en esta sesión y lo que proviene de tu conocimiento de entrenamiento; "
    "(2) cuando uses conocimiento de entrenamiento, indícalo explícitamente con frases como 'según la literatura' o 'en general se reporta'; "
    "(3) no cites autores, años ni DOIs que no hayas recuperado en esta sesión —si no tienes la fuente, di que no la tienes; "
    "(4) si la evidencia disponible es insuficiente para responder con confianza, dilo; "
    "(5) presenta activamente evidencia contraria o matices que cuestionen la dirección de la consulta; "
    "(6) calibra la certeza: usa 'sugiere', 'es consistente con', 'habría que verificar' según corresponda, nunca afirmes más de lo que los datos permiten."
)

MODE_GUIDANCE = {
    "general": f"Asistente académico para Psicología y Ciencias Sociales. {_EPISTEMIC_BASE}",
    "search": f"Modo búsqueda: sintetiza solo desde las fuentes recuperadas en esta sesión. Si no hay fuentes suficientes, indícalo antes de responder. {_EPISTEMIC_BASE}",
    "quant": f"Modo cuantitativo: prioriza operacionalización, supuestos y cautelas estadísticas. Señala cuando una interpretación excede lo que el diseño permite. {_EPISTEMIC_BASE}",
    "qual": f"Modo cualitativo: prioriza trazabilidad interpretativa entre dato, código, categoría e inferencia. Advierte cuando se generalizan hallazgos más allá del corpus. {_EPISTEMIC_BASE}",
    "design": f"Modo diseño: prioriza coherencia entre pregunta, objetivos, unidad de análisis y amenazas de validez. Señala inconsistencias aunque no se pidan. {_EPISTEMIC_BASE}",
    "teach": f"Modo docencia: prioriza claridad pedagógica, secuencia didáctica y evaluación formativa. {_EPISTEMIC_BASE}",
    "write": f"Modo redacción: prioriza estructura argumental y economía de lenguaje. Señala afirmaciones que necesiten respaldo antes de publicar. {_EPISTEMIC_BASE}",
    "verify": f"Modo verificación: tu tarea principal es encontrar problemas, no confirmar lo que se dice. Identifica afirmaciones sin respaldo, saltos inferenciales, generalizaciones indebidas y posibles sesgos de confirmación. {_EPISTEMIC_BASE}",
}


def build_system_prompt(state: SessionState) -> str:
    base = MODE_GUIDANCE.get(state.mode, MODE_GUIDANCE["general"])

    region = get_region()
    base = f"{base} {region['context']}"

    if state.attached_path:
        try:
            profile = infer_profile(state.attached_path)
            label = profile.get("label", "")
            if label:
                base = f"{base} El proyecto adjunto corresponde al perfil: {label}."
        except Exception:
            pass
    return base


def answer_session_query(state: SessionState, query: str) -> str:
    context_chunks = gather_context(state, query)
    web_results = gather_web_results(state, query)
    system_prompt = build_system_prompt(state)
    user_content = build_user_prompt(state, query, context_chunks, web_results)

    messages = list(state.messages) + [{"role": "user", "content": user_content}]
    llm_result = chat_completion(system_prompt, messages)
    if llm_result.content:
        state.add_exchange(user_content, llm_result.content)
        response = llm_result.content
        if web_results:
            response = response.rstrip() + "\n\nFuentes recuperadas:\n" + "\n".join(
                f"- [{item.source_type}] {item.title}: {item.url}" for item in web_results[:5]
            )
        return response
    return fallback_response(state, query, context_chunks, web_results, llm_result.error)


def gather_context(state: SessionState, query: str) -> list[tuple[str, str]]:
    chunks: list[tuple[str, str]] = []

    for slug in state.pinned_memories:
        text = load_memory_text(slug)
        if text:
            chunks.append((f"memory:{slug}", snippet_from_text(text, query)))

    if state.attached_path:
        sources = read_jsonl_records(research_dir(state.attached_path) / "sources.jsonl")
        ranked = rank_attached_sources(state.attached_path, sources, query)
        for source in ranked[:4]:
            path = state.attached_path / source["path"]
            chunks.append((source["path"], extract_snippet(path, query)))

    return chunks


def gather_web_results(state: SessionState, query: str):
    if state.mode != "search":
        return []
    region = get_region()
    results = []
    # Fuentes iberoamericanas siempre presentes
    results += search_scielo(query, max_results=3)
    results += search_openalex(query, max_results=3)
    # Semantic Scholar y PubMed: amplían cobertura global
    results += search_semantic_scholar(query, max_results=3)
    # PubMed: prioritario en regiones globales o cuando hay términos clínicos
    if region.get("languages") and "en" in region["languages"] or _is_health_query(query):
        results += search_pubmed(query, max_results=2)
    # Web general
    results += search_web(query, max_results=3)
    return results


def _is_health_query(query: str) -> bool:
    health_terms = {
        "salud", "clínico", "clínica", "terapia", "psicopatología", "diagnóstico",
        "dsm", "cie", "mental health", "clinical", "therapy", "psychiatric",
        "burnout", "estrés", "ansiedad", "depresión", "trauma", "bienestar",
    }
    q = query.lower()
    return any(term in q for term in health_terms)


def build_user_prompt(state: SessionState, query: str, chunks: list[tuple[str, str]], web_results: list) -> str:
    lines = [
        f"Modo: {state.mode}",
        f"Consulta: {query}",
        "",
        "Contexto disponible:",
    ]
    for label, text in chunks:
        lines.append(f"- {label}: {text}")
    if web_results:
        lines.append("")
        lines.append("Resultados web recuperados:")
        for item in web_results:
            lines.append(f"- {item.source_type} | {item.title} | {item.url} | {item.snippet}")
    lines.append("")
    if web_results:
        lines.append(
            "INSTRUCCIÓN: sintetiza la respuesta usando las fuentes recuperadas arriba. "
            "Cita el título o URL de la fuente cuando hagas una afirmación específica. "
            "Si las fuentes no son suficientes para responder, dilo antes de completar con conocimiento general. "
            "No inventes autores, años ni datos que no aparezcan en las fuentes recuperadas."
        )
    else:
        lines.append(
            "INSTRUCCIÓN: no hay fuentes recuperadas en esta sesión. "
            "Responde con conocimiento general pero márcalo explícitamente como tal. "
            "No cites autores ni años específicos a menos que estés seguro de su existencia. "
            "Si la respuesta requiere evidencia empírica, recomienda buscarla con /search."
        )
    return "\n".join(lines)


def fallback_response(
    state: SessionState,
    query: str,
    chunks: list[tuple[str, str]],
    web_results: list,
    llm_error: str | None,
) -> str:
    direct = direct_answer_if_possible(state.mode, query, chunks, web_results)
    if direct:
        if llm_error:
            return direct + "\n\nDiagnóstico de modelo:\n" + summarize_model_issue(llm_error)
        return direct

    header = [
        f"Modo: {state.mode}",
        f"Consulta: {query}",
        "",
        synthesize_intro(state.mode),
    ]
    if chunks:
        header.append("")
        header.append("Contexto recuperado:")
        for label, text in chunks:
            header.append(f"- `{label}`: {text}")
    else:
        header.append("")
        header.append("Sin contexto documental adjunto. La respuesta se limita a orientación general.")
    if web_results:
        header.append("")
        header.append("Resultados web:")
        for item in web_results:
            header.append(f"- [{item.source_type}] {item.title}: {item.url}")

    if llm_error:
        header.append("")
        header.append("Diagnóstico de modelo:")
        header.append(summarize_model_issue(llm_error))

    header.append("")
    header.extend(mode_response(state.mode, query))
    return "\n".join(header)


def synthesize_intro(mode: str) -> str:
    intros = {
        "search": "En este modo conviene partir delimitando población, fenómeno, contexto y tipo de fuente.",
        "quant": "En este modo conviene separar diseño, variables, análisis e interpretación antes de concluir.",
        "qual": "En este modo conviene distinguir material empírico, codificación, categorías e inferencia.",
        "design": "En este modo conviene alinear pregunta, objetivos, diseño y amenazas de validez.",
        "teach": "En este modo conviene secuenciar objetivo, contenido, actividad, evaluación y cierre.",
        "write": "En este modo conviene ordenar tesis, evidencia, transición y alcance de cada afirmación.",
        "verify": "En este modo conviene localizar afirmaciones, soporte y posibles saltos inferenciales.",
    }
    return intros.get(mode, "Modo general activo para consulta académica.")


def mode_response(mode: str, query: str) -> list[str]:
    if mode == "teach":
        return teach_response(query)
    if mode == "design":
        return design_response(query)
    if mode == "quant":
        return quant_response(query)
    if mode == "qual":
        return qual_response(query)
    if mode == "search":
        return search_response(query)
    if mode == "verify":
        return verify_response(query)
    if mode == "write":
        return write_response(query)
    return [
        "Sugerencia:",
        "- si necesita más precisión, cambie de modo con `/mode` o use `/attach` para sumar contexto;",
        f"- también puede reformular la consulta en términos más operativos: {simplify_query(query)}",
    ]


def simplify_query(query: str) -> str:
    words = tokenize(query)
    return " ".join(words[:10]) if words else query


def teach_response(query: str) -> list[str]:
    topic = extract_topic_phrase(query)
    return [
        "Propuesta de salida:",
        "1. Aprendizaje esperado",
        f"- Al final de la clase, el estudiantado debería poder explicar y aplicar: {topic}.",
        "2. Estructura sugerida de 90 minutos",
        "- 10 min: activación de conocimientos previos con pregunta o caso breve;",
        "- 20 min: exposición guiada de conceptos centrales con ejemplo disciplinar;",
        "- 20 min: demostración o ejercicio resuelto paso a paso;",
        "- 25 min: actividad aplicada en parejas o grupos pequeños;",
        "- 10 min: puesta en común y corrección de errores frecuentes;",
        "- 5 min: cierre con síntesis y ticket de salida.",
        "3. Evaluación rápida",
        "- ticket de salida con una pregunta de aplicación;",
        "- mini ejercicio para distinguir uso correcto e incorrecto del concepto.",
        "4. Recomendación pedagógica",
        "- use una analogía cercana a Psicología o Educación;",
        "- traduzca definiciones a interpretación práctica;",
        "- cierre con una pregunta de aplicación y no solo de memoria.",
    ]


def design_response(query: str) -> list[str]:
    return [
        "Esqueleto de diseño sugerido:",
        f"- Pregunta central: {query}",
        "- Objetivo general: formular qué quiere describir, explicar o interpretar;",
        "- Objetivos específicos: 3 como máximo, cada uno con verbo observable;",
        "- Unidad de análisis: personas, instituciones, textos, eventos o interacciones;",
        "- Diseño recomendable: cuantitativo, cualitativo o mixto según el tipo de inferencia buscada;",
        "- Fuente de datos esperable: encuesta, entrevista, corpus documental, base secundaria o diseño mixto;",
        "- Amenazas a vigilar: sesgo de selección, ambigüedad temporal, validez de constructo, sobreinferencias.",
        "Siguiente paso útil:",
        "- convierta la pregunta en objetivo general, tres objetivos específicos y una unidad de análisis explícita.",
    ]


def quant_response(query: str) -> list[str]:
    return [
        "Guía cuantitativa inicial:",
        f"- Foco analítico: {query}",
        "- Defina variable dependiente e independientes;",
        "- Identifique nivel de medición y estructura de los datos;",
        "- Distinga si necesita descripción, contraste, asociación o modelamiento;",
        "- Aclare unidad de observación y tamaño muestral esperado;",
        "- Revise supuestos antes de interpretar resultados;",
        "- No traduzca asociación en causalidad si el diseño no lo permite.",
    ]


def qual_response(query: str) -> list[str]:
    return [
        "Guía cualitativa inicial:",
        f"- Foco analítico: {query}",
        "- Delimite corpus y criterio de segmentación;",
        "- Defina unidad analítica: tema, episodio, enunciado, actor, recurso discursivo;",
        "- Separe dato, código, categoría e interpretación;",
        "- explicite criterio de saturación o de cierre analítico si corresponde;",
        "- Si trabaja ACD, explicite el marco antes de atribuir efectos discursivos.",
    ]


def search_response(query: str) -> list[str]:
    es_query, en_query = build_search_queries(query)
    return [
        "Estrategia de búsqueda sugerida:",
        f"- Tema base: {query}",
        "- Bloque 1: fenómeno o concepto principal;",
        "- Bloque 2: población o unidad social;",
        "- Bloque 3: contexto institucional, geográfico o temporal;",
        "- Bloque 4: tipo de estudio o enfoque metodológico si corresponde.",
        "Consulta sugerida en español:",
        f"- {es_query}",
        "Consulta sugerida en inglés:",
        f"- {en_query}",
        "Tipos de fuente a separar:",
        "- academic: artículos, revisiones, capítulos;",
        "- institutional: informes, ministerios, organismos internacionales;",
        "- legal: leyes, reglamentos, normas;",
        "- press/web: cobertura periodística o divulgativa.",
        "Consejo operativo:",
        "- combine términos amplios y específicos;",
        "- separe búsqueda académica, institucional y normativa.",
    ]


def verify_response(query: str) -> list[str]:
    return [
        "Ruta de verificación sugerida:",
        f"- Afirmación o argumento a revisar: {query}",
        "- Identifique qué parte es dato, qué parte es interpretación y qué parte es conclusión;",
        "- verifique si cada afirmación remite a tabla, cita, resultado o referencia concreta;",
        "- marque saltos entre hallazgo descriptivo y afirmación causal o normativa.",
        "- explicite qué afirmaciones quedarían como plausibles pero no todavía demostradas.",
    ]


def write_response(query: str) -> list[str]:
    return [
        "Ruta de escritura sugerida:",
        f"- Tarea de redacción: {query}",
        "- defina primero la función del texto: introducción, método, resultados, discusión o cierre;",
        "- escriba una idea central por párrafo;",
        "- conecte cada afirmación con evidencia o referencia;",
        "- cierre cada sección dejando claro su aporte al argumento total.",
    ]


def direct_answer_if_possible(mode: str, query: str, chunks: list[tuple[str, str]], web_results: list) -> str | None:
    lowered = query.lower()
    if "ruta reproducible" in lowered and chunks:
        return (
            "Ruta reproducible identificada:\n"
            "1. partir desde archivos originales `csv`;\n"
            "2. normalizar e ingerir los originales;\n"
            "3. escribir almacenamiento columnar `parquet`;\n"
            "4. regenerar objetos analíticos desde `parquet`;\n"
            "5. hacer que los manuscritos lean solo productos regenerables.\n\n"
            "Soporte contextual:\n"
            + "\n".join(f"- `{label}`" for label, _ in chunks[:3])
        )
    if mode == "teach" and ("clase" in lowered or "90 minutos" in lowered):
        topic = extract_topic_phrase(query)
        return (
            f"Plan de clase preliminar sobre {topic}\n"
            "1. Inicio, 10 min: activar ideas previas con una pregunta aplicada a Psicología.\n"
            "2. Desarrollo I, 20 min: explicar concepto, tipos y criterios de uso.\n"
            "3. Desarrollo II, 20 min: resolver un ejemplo guiado paso a paso.\n"
            "4. Actividad, 25 min: ejercicio breve en parejas con discusión de decisiones.\n"
            "5. Cierre, 15 min: retroalimentación, errores frecuentes y ticket de salida.\n\n"
            "Si quiere, el siguiente paso es convertir esto en guion docente, diapositivas o rúbrica."
        )
    if mode == "search" and web_results:
        lines = [
            f"Búsqueda web inicial para: {query}",
            "",
            "Resultados encontrados:",
        ]
        for item in web_results:
            lines.append(f"- [{item.source_type}] {item.title}")
            lines.append(f"  {item.url}")
            lines.append(f"  {item.snippet}")
        lines.append("")
        lines.append("Lectura inicial:")
        lines.append("- separe primero resultados académicos, institucionales y prensa;")
        lines.append("- si busca evidencia fuerte, priorice revisiones, meta-análisis y estudios empíricos según el problema.")
        lines.append("")
        lines.append("Siguiente paso recomendado:")
        lines.append("- delimitar tipo de fuente: artículo académico, informe institucional, legislación o prensa;")
        lines.append("- luego refinar la consulta con población, contexto y periodo.")
        return "\n".join(lines)
    return None


def build_search_queries(query: str) -> tuple[str, str]:
    quoted = query.strip()
    spanish = f'"{quoted}" AND (psicología OR educación OR "ciencias sociales")'
    english = f'"{quoted}" AND (psychology OR education OR "social sciences")'
    return spanish, english


def summarize_model_issue(error: str) -> str:
    return f"{error}\n{active_provider_label()}\n(use /doctor para diagnóstico completo)"


def extract_topic_phrase(query: str) -> str:
    lowered = query.strip()
    patterns = [
        r"clase de \d+ minutos sobre (.+)",
        r"clase sobre (.+)",
        r"sobre (.+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, lowered, re.IGNORECASE)
        if match:
            return match.group(1).rstrip("?. ")
    return query.rstrip("?. ")


def rank_attached_sources(root: Path, sources: list[dict], query: str) -> list[dict]:
    tokens = tokenize(query)
    scored: list[tuple[int, dict]] = []
    for source in sources:
        path_text = source["path"].lower()
        score = sum(2 for token in tokens if token in path_text)
        full_path = root / source["path"]
        try:
            text = full_path.read_text(encoding="utf-8", errors="ignore")[:4000].lower()
        except Exception:
            text = ""
        score += sum(3 for token in tokens if token in text)
        if source.get("role") == "project_doc":
            score += 2
        scored.append((score, source))
    scored.sort(key=lambda item: (-item[0], item[1]["path"]))
    return [item[1] for item in scored]


def snippet_from_text(text: str, query: str) -> str:
    compact = re.sub(r"\s+", " ", text)
    for token in tokenize(query):
        idx = compact.lower().find(token)
        if idx >= 0:
            start = max(0, idx - 80)
            end = min(len(compact), idx + 220)
            return compact[start:end].strip()
    return compact[:260].strip()


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-ZáéíóúñÁÉÍÓÚÑ]{4,}", text.lower())
