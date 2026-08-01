# Yatiri: guía de la versión CLI y de la versión MCP

Estado verificado contra el código: 2026-07-31, commit `6f73d7a`.

Yatiri es el nombre de uso del proyecto `research_operator` (también instalado
bajo el alias `scholar`): un asistente académico de terminal orientado a
investigación en español y portugués, con foco declarado en Iberoamérica.
Existe en dos formas que comparten el mismo código base pero se usan de
manera distinta: una **CLI/REPL independiente** (la versión "normal", pensada
para trabajar sin Claude Code abierto) y un **servidor MCP** (agregado el
2026-07-31, pensado para que Claude Code consuma una parte específica de esa
misma lógica como herramienta).

Repositorio: `https://github.com/sebastianligueno/yatiri`.

---

## 1. Arquitectura común a ambas versiones

El código vive en `src/research_operator/`, dividido en dos capas:

- `core/`: funciones puras, sin dependencia de terminal ni de MCP. Cada
  fuente académica tiene su propio módulo (`crossref.py`, `openalex.py`,
  `pubmed.py`, `hal.py`, `jstage.py`, `semantic_scholar.py`, `scielo.py`),
  todas con la misma forma: `search_X(query, max_results, ...) -> list[XResult]`,
  donde `XResult` es un dataclass con campos como `title`, `url`, `snippet`,
  `doi`, `journal`, `year`, `authors`. Además están `advisor.py` (el
  orquestador que agrega fuentes y sintetiza con un LLM), `llm.py`
  (multi-proveedor), `session.py` (estado conversacional), `memory.py`,
  `profiles.py`, `scanner.py`, `runner.py`, `export_md.py`, `vault_export.py`,
  `config.py`.
- `cli/`: la capa de interfaz — `argparse` para los comandos de nivel
  superior y un REPL con comandos `/slash` — que simplemente llama a las
  funciones de `core/`.

Esta separación es la que permitió construir la versión MCP sin reescribir
nada: el servidor MCP es una tercera capa liviana sobre `core/`, paralela a
`cli/`, no una bifurcación del proyecto.

### Proveedores de modelo (LLM)

Configurables en `~/.yatiri/config.yaml` o variables de entorno. Soportados:
DeepSeek, OpenRouter, OpenAI (o cualquier API compatible), Groq, Anthropic,
y Ollama local. Con `SCHOLAR_MODEL_PROVIDER=auto` (el default), Yatiri prueba
en orden `deepseek → openrouter → openai → groq → anthropic → ollama` hasta
que uno responda. En la práctica, para Sebastián el proveedor activo es
DeepSeek (clave en `~/.deepseek_key`), con Ollama como respaldo local.

### Perfiles de región y de proyecto

Dos sistemas de perfiles distintos, no confundir:

- **Región** (`core/config.py`, `REGIONS`): `latam`, `iberia`, `global`,
  `chile`, `brasil`. Define idiomas y fuentes prioritarias que se inyectan
  en el prompt de síntesis (ej. `chile` prioriza SciELO-Chile, repositorios
  ANID, Redalyc).
- **Perfil de proyecto** (`profiles/*.yaml`: `historical_discourse.yaml`,
  `mixed_methods.yaml`, `quant_social_r.yaml`): usado por `yatiri scan` para
  inferir de qué tipo de proyecto de investigación se trata (según
  carpetas/archivos presentes) y correr checks específicos de ese perfil.

---

## 2. Versión CLI / REPL (la "normal")

### Instalación

`pip install -e .` directo (sin venv/pipx, por preferencia explícita ya
fijada). Entry points `yatiri` y `scholar`, ambos apuntan a
`research_operator.main:main`. En este equipo, symlink en
`~/.local/bin/yatiri`, interpretado por pyenv 3.12.6.

### Comandos de nivel superior (`argparse`)

Se invocan como `yatiri <comando> [argumentos]`:

| Comando | Qué hace |
|---|---|
| `chat "<pregunta>" [--mode] [--attach]` | Consulta puntual no interactiva. Corre `answer_session_query` una sola vez y termina. Funciona en cualquier directorio, no requiere workspace inicializado. |
| `setup` | Configuración interactiva de API key y proveedor. |
| `init [ruta]` | Inicializa un workspace de investigación (`.research/project.yaml`) en la ruta dada. |
| `scan [ruta]` | Escanea el proyecto, infiere su perfil (`profiles/*.yaml`) y genera un reporte. |
| `status [ruta]` | Muestra el estado del proyecto. Requiere que `.research/project.yaml` ya exista — falla con `FileNotFoundError` si no. |
| `ask "<pregunta>" [ruta]` | Responde usando los archivos del proyecto como contexto. |
| `run <step_id> [ruta]` | Ejecuta un paso de pipeline definido en `project.yaml` (comando de shell arbitrario vía `subprocess`). |

Si se invoca `yatiri` sin argumentos, arranca el **REPL interactivo**.

### REPL y comandos `/slash`

Dentro del REPL (`cli/repl.py`), además de conversación libre, hay comandos
con prefijo `/`:

| Comando | Función |
|---|---|
| `/exit`, `/quit` | Salir. |
| `/clear` | Borra el historial de la sesión. |
| `/help` | Ayuda. |
| `/provider` | Muestra el proveedor LLM activo. |
| `/doctor` | Diagnóstico de proveedores configurados (`provider_diagnostics`). |
| `/mcp` | Detecta qué servidores MCP tiene instalados Claude Code y recomienda cuáles instalar (`core/mcp_detect.py`) — Yatiri **lee** tu configuración de Claude Code, pero nunca habló el protocolo MCP hasta la versión agregada en esta misma fecha. |
| `/mode <modo>` | Cambia de modo: `general, search, quant, qual, design, teach, write, verify`. |
| `/search`, `/quant`, `/qual`, `/design`, `/teach`, `/write`, `/verify` | Atajos que cambian de modo y ejecutan la consulta en un solo paso. |
| `/export [ruta \| --vault \| --local]` | Exporta los últimos resultados de búsqueda como fichas `.md` con frontmatter YAML (compatibles con Obsidian/Zettlr/Joplin/Notion). Si hay un vault configurado, clasifica automáticamente por carpeta temática. |
| `/cost` | Costo estimado de la sesión (tokens de entrada/salida). |
| `/brief` | Formulario para construir la ficha estructurada del proyecto (`ProjectBrief`: paradigma, fenómeno, pregunta, objetivos, marco teórico, metodología, muestra, plan de análisis). |
| `/review` | Revisión crítica del proyecto según esa ficha, sensible al paradigma declarado. |
| `/attach <ruta>` / `/detach` | Adjunta o quita una carpeta de contexto local (inicializa `.research` si no existe). |
| `/context` | Muestra el contexto activo. |
| `/memory show \| pin <nombre> \| unpin <nombre>` | Memorias persistentes en `~/.yatiri/memories/`. |

### El corazón de la búsqueda: `core/advisor.py`

`answer_session_query(state, query)` es la función que atienden tanto `chat`
como los modos `/search` etc. Internamente:

1. Decide si la consulta es "temática" (dispara búsqueda) o conversacional.
2. Llama en secuencia a las fuentes académicas relevantes según el modo y la
   región configurada.
3. Construye un prompt con un bloque de normas epistémicas **irrenunciables**:
   distinguir explícitamente fuente recuperada en la sesión vs. conocimiento
   de entrenamiento del modelo, y prohibición absoluta de inventar
   referencias, autores, años, DOIs o URLs. Si no hay fuente recuperada, la
   instrucción es responder "No tengo fuentes recuperadas" en vez de
   fabricar una cita.
4. Envía todo al proveedor LLM activo (`core/llm.py`) y devuelve prosa
   continua con citas APA 7 inline, sección de vacíos y referencias.

Esto es lo que la versión MCP **no** reproduce — ver más abajo por qué.

### Limitaciones conocidas de la versión CLI

- Búsqueda débil en literatura clásica anglosajona (indexa bien producción
  hispanoamericana vía CrossRef/OpenAlex, pero consultas como autores
  clásicos en inglés devuelven ruido).
- SciELO: `core/scielo.py` intenta primero `articlemeta` y cae a scraping
  HTML si falla — en la práctica, la búsqueda por texto libre de SciELO está
  bloqueada del lado del servidor (ver sección 4), así que esta fuente rinde
  poco o nada dentro de Yatiri también.
- `status`, `scan`, `ask`, `run` requieren workspace inicializado
  (`.research/project.yaml`); `chat` no.

---

## 3. Versión MCP (agregada 2026-07-31)

### Qué es y por qué se hizo distinto a simplemente "envolver todo"

`src/research_operator/mcp_server.py` es un servidor MCP nuevo, registrado en
Claude Code como `yatiri` (`claude mcp add yatiri --scope user -- <python del
pyenv> mcp_server.py`). Corre con el mismo intérprete pyenv 3.12.6 donde ya
está instalado `research_operator` — no necesitó un entorno aparte.

La decisión de diseño clave: **no expone `advisor.py` tal cual**. El motivo
es que `answer_session_query` depende de `SessionState`, un objeto con
historial de conversación, modo activo, memorias fijadas, etc. — es
inherentemente *stateful*. El protocolo MCP, en cambio, es fundamentalmente
*stateless* por invocación: cada llamada a una herramienta es independiente,
sin sesión implícita entre una y otra. Envolver `advisor.py` directamente
habría requerido inventar un mecanismo de sesión artificial (ids de sesión,
persistencia entre llamadas) solo para simular algo que Claude Code ya
resuelve mejor con su propio contexto de conversación.

En cambio, el servidor MCP expone únicamente la pieza que **no** depende de
estado ni de un LLM intermedio: la capa de búsqueda multi-fuente de `core/`.
La síntesis (leer los resultados, discriminar relevancia, redactar con
citas) queda en manos de quien llama a la herramienta — Claude, no DeepSeek
vía Yatiri. Esto evita, de paso, una cadena rara de "un modelo llamando a
otro modelo" sin necesidad real.

### La única herramienta: `multi_source_search`

```
multi_source_search(
    query: str,
    max_results: int = 5,
    sources: list[str] | None = None,       # crossref, openalex, pubmed,
                                              # hal, jstage, semantic_scholar,
                                              # scielo — None = todas
    year_from: int | None = None,
    year_to: int | None = None,
    response_format: "markdown" | "json" = "markdown",
    enrich_scielo_citations: bool = False,
) -> str
```

Comportamiento:

- Consulta las fuentes seleccionadas **en paralelo** (`ThreadPoolExecutor`),
  no en secuencia — el tiempo total es el de la fuente más lenta (~2-20 s),
  no la suma de todas (que llegaba a ~90 s en el peor caso probado antes de
  paralelizar).
- **Deduplica** resultados repetidos entre fuentes: primero por DOI
  normalizado: si no hay DOI, por título normalizado (minúsculas, sin
  puntuación, espacios colapsados). Al fusionar, conserva la entrada con más
  campos completos y lista todas las fuentes donde apareció — coincidencia
  entre fuentes independientes es en sí una señal de relevancia.
- `year_from`/`year_to` se propagan solo a las fuentes que lo soportan
  nativamente: CrossRef, OpenAlex, PubMed, Semantic Scholar. Se agregó este
  soporte a esos cuatro módulos de `core/` como parte de este trabajo (antes
  no existía ni siquiera para uso interno de `advisor.py`); HAL, J-STAGE y
  SciELO lo ignoran porque sus APIs no lo permiten.
- `enrich_scielo_citations`: opcional porque agrega una llamada HTTP extra
  por resultado. Consulta `citedby.scielo.org/api/v1/meta/` (búsqueda por
  título) para saber si algún artículo de la red SciELO cita ese resultado
  — funciona para *cualquier* fuente, no solo para resultados que ya vengan
  de SciELO. Es un cruce best-effort (coincidencia de texto de título, no
  DOI/PID exacto).
- Caché en memoria del proceso, TTL de 1 hora, por combinación exacta de
  parámetros. Como el servidor corre como subproceso persistente durante la
  sesión de Claude Code, repetir la misma búsqueda no vuelve a golpear las
  APIs externas.
- Cada fuente que falla o no devuelve nada se reporta explícitamente
  (`[fuente] Error: ...` o `[fuente] Sin resultados.`), nunca se omite en
  silencio.

### Qué se pierde respecto a la versión CLI

- No hay síntesis en prosa con estructura fija (Estado de la
  investigación/Vacíos/Referencias) — eso lo produce Claude a partir del
  resultado crudo, con sus propios criterios, no con las normas epistémicas
  explícitas que trae `advisor.py`.
- No hay modos (`/quant`, `/qual`, `/design`, `/teach`, `/write`, `/verify`),
  ni `/brief`/`/review` (ficha de proyecto y revisión crítica), ni memoria
  persistente de sesión, ni exportación directa a vault con clasificación
  temática. Todo eso vive en `core/` y podría exponerse como herramientas
  adicionales en el futuro, pero no se hizo — quedó fuera de alcance
  deliberadamente para esta primera versión.
- No usa DeepSeek en absoluto: la búsqueda es puramente de recuperación
  (HTTP a las APIs académicas), sin llamada a ningún LLM de por medio.

---

## 4. SciELO: el caso aparte

Ambas versiones (CLI y MCP) heredan la misma limitación de origen: el motor
de búsqueda por texto libre de SciELO (`search.scielo.org`) está protegido
por un desafío anti-bot de todo el sitio (proof-of-work vía JavaScript,
"Bunny Shield") que bloquea cualquier cliente HTTP simple — no hay ajuste de
headers o User-Agent que lo resuelva, y no existe una API alternativa oficial
con búsqueda por palabra clave (`articlemeta.scielo.org` nunca la tuvo, solo
permite consultar por PID/ISSN/fecha exactos).

Existe además un servidor MCP **standalone** dedicado a SciELO
(`~/IA_Modelos_y_Datos/mcp-servers/scielo-mcp/`, no versionado en este
repositorio), registrado por separado en Claude Code, con dos herramientas
que sí funcionan (`scielo_get_article` por PID/DOI, `scielo_journal_browse`
por país/área temática) y dos que están documentadas como no disponibles
(`scielo_search`, `scielo_search_author`) por la misma razón. El detalle
completo de ese diagnóstico está en la memoria de Claude
(`project_scielo_yatiri_mcp.md`), no en este repositorio.

---

## 5. Resumen comparativo

| | CLI / REPL | MCP |
|---|---|---|
| Dónde corre | Terminal, standalone | Subproceso de Claude Code |
| Requiere Claude Code abierto | No | Sí |
| Síntesis con LLM propio | Sí (DeepSeek u otro proveedor configurado) | No — la hace quien invoca la herramienta |
| Búsqueda multi-fuente | Sí, secuencial, dentro de `advisor.py` | Sí, en paralelo, deduplicada, con filtros de año y caché |
| Modos de trabajo (`/quant`, `/write`, etc.) | Sí | No |
| Ficha de proyecto y revisión crítica | Sí (`/brief`, `/review`) | No |
| Exportación a vault Obsidian | Sí (`/export`) | No |
| Memoria de sesión persistente | Sí (`~/.yatiri/memories/`) | No |
| Cruce de citas SciELO por título | No | Sí (`enrich_scielo_citations`) |
| Salida estructurada en JSON | No | Sí (`response_format="json"`) |

En síntesis: la versión CLI es la herramienta completa de asistencia
metodológica y de escritura; la versión MCP es, por ahora, un motor de
recuperación multi-fuente rápido y deduplicado que Claude Code puede invocar
como una herramienta más, sin las capacidades conversacionales ni de
exportación que sí tiene la CLI.
