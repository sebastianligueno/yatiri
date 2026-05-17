# Inventario académico

Fecha de revisión: 2026-05-14

## Clientes integrados hoy

- `DeepSeek API`: cliente remoto principal para conversación.
- `Ollama`: respaldo local.
- `DuckDuckGo HTML`: búsqueda web simple, sin garantías académicas ni citación estructurada.

## MCP complementarios de trabajo

- `Freeplane MCP`: MCP oficial para mapas conceptuales y mapas mentales; útil para planificación de capítulos, clases y argumentos.

## MCP académicos vigentes en el entorno

- `scite MCP`: prioridad principal para verificación de literatura, Smart Citations, alertas editoriales y lectura focalizada.
- `PubMed` o `Europe PMC`: prioridad alta para emociones cuando el capítulo toca salud mental, clínica, neurociencia afectiva o psicobiología.
- `Scopus MCP`: autores, afiliaciones, revistas, métricas y BibTeX por DOI.
- `Zotero MCP`: consulta de biblioteca propia con enriquecimiento de scite.
- `Consensus MCP`: complemento permanente para descubrimiento inicial de artículos y mapeo rápido de evidencia, aunque el saldo actual esté agotado.

## Fuentes abiertas prioritarias en español

- `SciELO`: prioridad alta para búsqueda regional en español y portugués; ya quedó integrado en beta al modo `search`.
- `Redalyc`: fuerte para ciencias sociales, educación y humanidades.
- `Dialnet`: útil para artículos, tesis, capítulos y revistas hispanohablantes.
- `Latindex`: útil sobre todo para identificación y evaluación de revistas.

## Fuentes gratuitas de alta prioridad

- `PubMed`: prioridad gratuita principal para literatura biomédica y psicológica indexada en MEDLINE/PubMed.
- `Europe PMC`: complemento abierto fuerte para acceso, metadatos y enlaces a texto completo.
- `SciELO`: prioridad abierta para cobertura iberoamericana en español y portugués.
- `OpenAlex`: complemento abierto útil para descubrimiento y cited-by.
- `Crossref`: complemento abierto útil para DOI y metadatos.

## Fuentes excluidas

- `Sci-Hub`: excluido del diseño por razones legales y de cumplimiento.

## Diagnóstico de integración

Estado actual de `Scholar CLI`:

- sí integra clientes LLM directos;
- no integra todavía un cliente MCP nativo;
- no resuelve aún citas académicas con trazabilidad de fuente desde la terminal.
- puede convivir con `Freeplane MCP` como herramienta externa complementaria.

## Recomendación operativa

Para un flujo de escritura académica serio:

1. usar `scite MCP` como ruta principal de evidencia;
2. sumar `PubMed` o `Europe PMC` cuando el tema se acerque a clínica o neurociencia;
3. usar `Scopus MCP` para métricas, revistas, autores y BibTeX;
4. usar `Zotero MCP` para conectar con la biblioteca personal;
5. usar `Consensus MCP` como apoyo para descubrimiento rápido;
6. buscar en `SciELO`, `Redalyc`, `Dialnet` y `Latindex` cuando se necesite cobertura iberoamericana;
7. dejar `DuckDuckGo HTML` sólo como apoyo secundario para web institucional o prensa.

## Conectores recomendables a sumar

- `OpenAlex`: cobertura abierta de works, authors y venues.
- `Crossref`: resolución DOI y metadatos bibliográficos.
- `PubMed` o `Europe PMC`: si el proyecto entra en clínica, salud o neurociencia afectiva.
