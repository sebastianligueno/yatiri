# Amauta — Manual de usuario

*Amauta* es una palabra quechua y aymara que designa al sabio, al maestro, al conocedor. En las culturas andinas, el amauta era quien custodiaba y transmitía el saber colectivo. José Carlos Mariátegui eligió ese nombre para la revista intelectual más influyente del siglo XX latinoamericano (Lima, 1926–1930).

Esta herramienta toma ese nombre porque su propósito es el mismo: acompañar el trabajo de quienes producen y enseñan conocimiento en Iberoamérica.

---

## Qué es Amauta

Amauta es un asistente académico de terminal. Se abre desde la línea de comandos y permite hacer consultas de investigación, diseño metodológico, búsqueda bibliográfica, planificación docente y revisión crítica de argumentos, usando el modelo de lenguaje que el usuario tenga configurado y las herramientas académicas que ya tenga instaladas.

**No reemplaza a Claude Code, Zotero, Scite ni ninguna otra herramienta.** Amauta las recoge y las coordina. Si un MCP ya está instalado, lo reporta y lo tiene en cuenta. Si falta uno útil, lo sugiere. Si hay una clave de API configurada, la usa. Si no hay nada, igual funciona con las fuentes abiertas integradas (SciELO, OpenAlex, DuckDuckGo).

### Por qué existe

La mayor parte de los asistentes de IA académicos están diseñados para el mundo anglófono. Sus bases de conocimiento, sus fuentes predeterminadas y sus supuestos de contexto apuntan a revistas en inglés, circuitos del Norte global y sistemas bibliográficos que excluyen gran parte de la producción iberoamericana.

Amauta parte de la hipótesis contraria: la investigación en Psicología, Ciencias Sociales, Educación e Historia en España, Chile, México, Brasil, Argentina y el resto de América Latina tiene su propia producción, sus propias revistas, sus propios archivos, y merece una herramienta que los conozca y los priorice.

---

## Instalación

### Requisitos

- Python 3.10 o superior
- Conexión a internet (para búsquedas y APIs)
- Opcional: [Ollama](https://ollama.com) para modo offline

### Desde el repositorio

```bash
git clone https://github.com/usuario/amauta-cli
cd amauta-cli
pip install -e .
```

### Con pipx (entorno aislado, recomendado para distribución)

```bash
pipx install git+https://github.com/usuario/amauta-cli
```

### Con uv

```bash
uv tool install git+https://github.com/usuario/amauta-cli
```

Verificar instalación:

```bash
amauta --help
```

---

## Primer uso

### 1. Configurar proveedor y API key

```bash
amauta setup
```

Este comando interactivo guarda la configuración en `~/.scholar_operator/config.yaml`. No requiere tocar variables de entorno del sistema. Las variables de entorno siguen teniendo prioridad si ya están definidas.

Opciones disponibles en el wizard:
- Proveedor: `auto` (DeepSeek → Ollama), `deepseek`, `ollama`
- DeepSeek API key (se obtiene en [platform.deepseek.com](https://platform.deepseek.com/api_keys))
- Modelo DeepSeek: `deepseek-chat` (recomendado), `deepseek-reasoner`
- Ollama URL y modelo local
- **Región e idioma de búsqueda** (ver sección Regiones)

### 2. Abrir la sesión interactiva

```bash
amauta
```

Aparece el prompt `amauta[general]>`. Desde ahí puede escribir cualquier consulta o usar los comandos con `/`.

### 3. Inicializar un workspace de investigación

```bash
amauta init mi_proyecto
```

Crea la estructura de carpetas completa, el README y la configuración interna del proyecto.

---

## Modos de trabajo

Amauta tiene ocho modos. Cada uno orienta al modelo con un conjunto de prioridades específicas.

| Modo | Comando | Para qué |
|------|---------|----------|
| general | `/mode general` | Consulta académica libre |
| search | `/search` | Estrategia bibliográfica y recuperación de fuentes |
| quant | `/quant` | Diseño cuantitativo, estadística, supuestos |
| qual | `/qual` | Análisis cualitativo, corpus, codificación |
| design | `/design` | Diseño de investigación, coherencia metodológica |
| teach | `/teach` | Planificación docente, secuencias, evaluación |
| write | `/write` | Redacción académica, estructura argumental |
| verify | `/verify` | Revisión crítica, saltos inferenciales, trazabilidad |

El modo se activa con `/mode <nombre>` o directamente como prefijo de la consulta:

```
/teach Diseña una clase de 90 minutos sobre muestreo para segundo año
/design Propón un diseño mixto para estudiar burnout docente
/verify ¿Esta afirmación está respaldada por los datos del manuscrito?
```

---

## Comandos de sesión

### Consulta y modos

```
/help                          lista de comandos
/mode <modo>                   cambiar modo activo
/<modo> <consulta>             cambiar modo y consultar en un solo paso
```

### Contexto y proyecto

```
/attach /ruta/al/proyecto      adjuntar carpeta como contexto
/detach                        desconectar el contexto adjunto
/context                       mostrar modo, contexto y memorias activos
```

### Historial

```
/clear                         borrar historial de la sesión actual
```

### Memoria

```
/memory show                   listar memorias disponibles
/memory pin <nombre>           fijar una memoria en la sesión
/memory unpin <nombre>         desfijar una memoria
```

Las memorias se leen desde `~/.scholar_operator/memories/`. Son archivos Markdown que persisten entre sesiones.

### Diagnóstico

```
/provider                      proveedor activo y estado de la clave
/doctor                        diagnóstico completo de proveedores
/mcp                           MCPs detectados y sugerencias de instalación
/exit                          terminar la sesión
```

---

## Modo no interactivo

Para usar Amauta desde scripts, terminales sin TTY, o integrar en flujos automatizados:

```bash
amauta chat "consulta" --mode <modo>
amauta chat "consulta" --mode search --attach /ruta/proyecto
```

Ejemplos:

```bash
amauta chat "burnout docente en Chile: revisiones sistemáticas disponibles" --mode search
amauta chat "Diseña una clase de 90 min sobre muestreo probabilístico" --mode teach
amauta chat "¿Cuál es la ruta reproducible desde datos originales hasta manuscrito?" \
  --mode verify --attach /ruta/a/mi_investigacion
```

---

## Fuentes de búsqueda integradas

En modo `search`, Amauta consulta en paralelo:

| Fuente | Tipo | Cobertura | Clave |
|--------|------|-----------|-------|
| SciELO | Abierta | Iberoamérica, artículos revisados | No |
| OpenAlex | Abierta | 250M+ works global, open access | No |
| DuckDuckGo | Web | General, institucional, prensa | No |

La respuesta del LLM integra y sintetiza los resultados, distinguiendo entre dato recuperado y sugerencia inferida.

### Fuentes en español y portugués

La priorización regional (ver sección Regiones) orienta al modelo a:
- Buscar y citar primero en SciELO y Redalyc antes que en bases anglófonas
- Considerar revistas de Dialnet, CSIC, repositorios ANID (Chile), CAPES (Brasil)
- Reportar cuando una búsqueda no arroja resultados en la región configurada, en lugar de silenciosamente sustituir con literatura en inglés

---

## Regiones e idiomas

La región configura el contexto geográfico y cultural de todas las respuestas, no solo la búsqueda.

| Región | Idiomas | Fuentes prioritarias |
|--------|---------|----------------------|
| `latam` | es, pt | SciELO, Redalyc, Dialnet, OpenAlex |
| `iberia` | es, pt | Dialnet, SciELO, CSIC, Redalyc |
| `chile` | es | SciELO-Chile, ANID, Redalyc |
| `brazil` | pt, es | SciELO-Brasil, CAPES, Redalyc |
| `global` | es, pt, en | OpenAlex, Semantic Scholar, PubMed |

La región por defecto es `latam`. Para cambiarla:

```bash
amauta setup
# → opción 4: Región e idioma
```

O directamente con variable de entorno:

```bash
export AMAUTA_REGION=chile
```

---

## Integración con MCPs

### Qué son los MCPs

Model Context Protocol (MCP) es el estándar de integración de herramientas de Anthropic. Claude Code, Cursor y otros agentes pueden conectarse a servicios externos a través de MCPs. Amauta detecta los MCPs que el usuario ya tiene instalados en Claude Code y los reporta como parte del contexto disponible.

### Cómo funciona la detección

Al ejecutar `/mcp`, Amauta lee `~/.claude/settings.json` y lista:
- Qué MCPs están configurados y qué capacidad aporta cada uno
- Cuáles de los recomendados no están instalados, con instrucciones de instalación

### MCPs recomendados

| MCP | Capacidad | Por qué importa |
|-----|-----------|-----------------|
| **Zotero** | Biblioteca personal | Recupera, consulta y enriquece tus propias referencias |
| **Scite** | Verificación | Smart citations: si un paper fue apoyado, refutado o mencionado |
| **Semantic Scholar** | Descubrimiento | Grafos de citación, papers influyentes, cobertura de arXiv |
| **OpenAlex** | Open access | 250M+ works sin clave, alternativa abierta a Scopus |
| **Scopus** | Métricas | Métricas de autores, revistas y afiliaciones (requiere acceso institucional) |
| **Consensus** | Síntesis rápida | Resúmenes de evidencia por pregunta de investigación |

### Cómo instalar MCPs faltantes

La salida de `/mcp` incluye el comando exacto de instalación para cada MCP sugerido. Por ejemplo:

```bash
pip install zotero-mcp
claude mcp add zotero -- zotero-mcp serve

claude mcp add scite --transport http https://api.scite.ai/mcp
```

Una vez instalados, `/mcp` los reconocerá automáticamente en la próxima sesión.

---

## Workspace de investigación

`amauta init <ruta>` crea un espacio de trabajo estructurado:

```
mi_investigacion/
├── data/
│   ├── raw/          ← datos originales sin modificar
│   └── processed/    ← datos procesados o transformados
├── docs/             ← documentos de trabajo, protocolos, reportes
├── notes/            ← notas y memos de investigación
├── maps/             ← mapas conceptuales (Freeplane u otro)
├── paper/            ← manuscrito(s)
└── .research/        ← metadatos del proyecto (Amauta)
    ├── project.yaml  ← configuración del proyecto
    ├── sources.jsonl ← registro de fuentes
    ├── claims.jsonl  ← registro de afirmaciones
    └── runs.jsonl    ← historial de operaciones
```

Para adjuntar el workspace a una sesión:

```
/attach /ruta/a/mi_investigacion
```

Una vez adjunto, los modos `verify` y `write` pueden hacer referencia al contenido del proyecto.

---

## Uso con Ollama (sin API, offline)

Para investigadores sin presupuesto para APIs o sin conexión estable:

### 1. Instalar Ollama

Descargar desde [ollama.com](https://ollama.com). Disponible para Windows, macOS y Linux.

### 2. Descargar un modelo

```bash
ollama pull gemma3:4b       # recomendado: calidad/velocidad/tamaño (3 GB)
ollama pull llama3.2:3b     # alternativa liviana
ollama pull phi4-mini       # muy liviano (~2.5 GB)
```

### 3. Configurar Amauta

```bash
amauta setup
# → Proveedor: ollama
# → Modelo Ollama: gemma3:4b
```

### 4. Iniciar el daemon y abrir Amauta

```bash
ollama serve       # en una terminal
amauta             # en otra terminal
```

El modo `auto` (por defecto) intenta DeepSeek primero y cae a Ollama si no hay clave o hay error de conexión.

---

## Proveedores de IA

| Proveedor | Clave | Costo aprox. | Notas |
|-----------|-------|--------------|-------|
| DeepSeek API | Sí | ~$0.28/M tokens entrada | Recomendado. Muy bajo costo, buena calidad |
| Ollama (local) | No | Gratis | Requiere hardware. Calidad variable según modelo |

La clave de DeepSeek se obtiene en [platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys). El modelo `deepseek-chat` tiene el mejor equilibrio costo/calidad para tareas académicas conversacionales.

---

## Casos de uso

### Búsqueda bibliográfica en español

```
/search burnout docente universitario revisiones sistemáticas iberoamérica
```

Recupera resultados de SciELO y OpenAlex, los pasa al LLM para síntesis, y distingue entre lo que encontró y lo que no.

### Diseño de clase

```
/teach Diseña una clase de 90 minutos sobre análisis de regresión para tercer año de Psicología
```

Genera objetivo de aprendizaje, secuencia didáctica, actividad práctica, evaluación formativa y recomendaciones pedagógicas.

### Diseño de investigación

```
/design Quiero estudiar el efecto del trabajo remoto sobre el bienestar de docentes universitarios chilenos
```

Propone pregunta, objetivos, diseño, unidad de análisis y amenazas a la validez.

### Revisión de manuscrito

```
/attach /ruta/mi_paper
/verify ¿Qué afirmaciones del manuscrito no tienen respaldo en los datos?
```

### Estrategia de búsqueda para revisión sistemática

```
/search "relación entre autoeficacia y rendimiento académico" estrategia PRISMA bases de datos
```

Genera los bloques de búsqueda en español e inglés, tipos de fuente a separar y estrategia de inclusión/exclusión.

---

## Configuración avanzada

### Variables de entorno

```bash
export DEEPSEEK_API_KEY="sk-..."
export DEEPSEEK_MODEL="deepseek-chat"
export SCHOLAR_MODEL_PROVIDER="auto"    # auto | deepseek | ollama
export SCHOLAR_OLLAMA_MODEL="gemma3:4b"
export SCHOLAR_OLLAMA_URL="http://localhost:11434/api/chat"
export AMAUTA_REGION="latam"            # latam | iberia | chile | brazil | global
export SCHOLAR_CONTACT_EMAIL="tu@email.com"   # mejora la tasa de respuesta de OpenAlex
```

### Archivo de configuración

`~/.scholar_operator/config.yaml` — generado por `amauta setup`. Las variables de entorno tienen prioridad sobre este archivo.

### Memorias persistentes

Amauta puede leer notas de sesión anteriores desde `~/.scholar_operator/memories/`. Cada archivo `.md` en esa carpeta es una memoria disponible con `/memory show`.

---

## Estructura del proyecto (para desarrolladores)

```
src/research_operator/
├── cli/
│   ├── app.py        ← entrada principal, subcomandos
│   ├── repl.py       ← sesión interactiva (REPL)
│   ├── setup.py      ← wizard de configuración
│   └── init.py       ← inicialización de workspace
├── core/
│   ├── advisor.py    ← orquestación de respuestas por modo
│   ├── config.py     ← configuración, regiones, env vars
│   ├── llm.py        ← DeepSeek + Ollama con historial multi-turno
│   ├── mcp_detect.py ← detección de MCPs instalados en Claude Code
│   ├── openalex.py   ← búsqueda en OpenAlex REST API
│   ├── scielo.py     ← búsqueda en SciELO (ArticleMeta + HTML)
│   ├── web_search.py ← búsqueda web (DuckDuckGo HTML)
│   ├── session.py    ← estado de sesión e historial
│   ├── memory.py     ← memorias persistentes
│   ├── profiles.py   ← detección de perfil de proyecto
│   └── project.py    ← layout y configuración de workspace
└── profiles/
    ├── historical_discourse.yaml
    ├── mixed_methods.yaml
    └── quant_social_r.yaml
```

---

## Limitaciones actuales

- La integración con MCPs es de **detección e inventario**, no de llamada directa. Las búsquedas avanzadas con Zotero, Scite o Semantic Scholar se realizan desde Claude Code, no desde Amauta.
- La búsqueda con DuckDuckGo es frágil: los cambios en su HTML pueden romperla.
- Los modelos de Ollama más pequeños (< 7B) tienen calidad limitada para redacción académica compleja.
- Amauta no valida autenticamente la existencia de los papers que menciona en sus respuestas de modo fallback: use siempre `/verify` o un MCP de verificación (Scite) para confirmar referencias.

---

## Hoja de ruta

**Corto plazo**
- Integración directa con Redalyc y Dialnet (sin depender de DuckDuckGo)
- Llamadas directas a las APIs REST de Zotero y Semantic Scholar desde Amauta
- Respuestas en streaming (salida progresiva en el terminal)

**Mediano plazo**
- Exportación de respuestas a Markdown, Quarto y DOCX
- Plantillas para protocolos PRISMA, matrices de análisis cualitativo y guiones docentes
- Integración con CrossRef para resolución bibliográfica reproducible

**Largo plazo**
- Interfaz TUI con `textual` (paneles, scroll, historial visual)
- Plugin de disciplina para Derecho, Historia y Lingüística aplicada

---

## Créditos

- Nombre: *Amauta* — palabra quechua/aymara para el sabio, el maestro, el conocedor.  
  Mariátegui, J. C. (1926–1930). *Amauta*. Lima.
- Backends de IA: DeepSeek API, Ollama
- Fuentes integradas: SciELO, OpenAlex, DuckDuckGo
- Dependencias: PyYAML, prompt_toolkit, rich, requests

---

*Versión 0.3.0 — Mayo 2026*
