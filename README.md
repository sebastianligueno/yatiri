# Yatiri

*Asistente personal de terminal para investigación académica en Iberoamérica*

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![AI Assisted](https://img.shields.io/badge/developed%20with-Claude%20AI-blueviolet)](https://claude.ai)

---

## Por qué existe

La hice para uso propio. Soy docente universitario en Chile y trabajo con bibliografía en inglés, pero también en español y portugués. Los asistentes académicos que encontré priorizaban el circuito anglosajón: sus fuentes por defecto, sus criterios de relevancia y su noción de "literatura pertinente" apuntaban al Norte global en inglés.

Yatiri parte de otra hipótesis: la producción académica en Psicología, Ciencias Sociales, Educación e Historia tiene un circuito iberoamericano propio —con sus revistas, sus archivos y sus debates— que merece ser priorizado, no tratado como periferia. Al mismo tiempo, no ignoro la importancia de la literatura de corriente principal que se escribe principalmente en inglés, sino que se integra como capa adicional, no como única fuente de autoridad.

Respecto al nombre, viene del aymara: *yatiri* es el que sabe, el que lee señales dispersas para orientar a otros. Me vino como inspiración de mi novia, quien conoce y ama bien ese pueblo. El nombre me pareció justo.

Si te sirve para tu propio trabajo, úsala. Si la mejoras, comparte bajo la misma licencia.

---

## Qué hace

Sesión interactiva en el terminal con la que puedes:

- Consultar con contexto iberoamericano por defecto (configurable)
- Buscar en múltiples fuentes académicas internacionales y recibir síntesis fundamentada
- Trabajar en modos especializados: búsqueda, diseño, metodología, docencia, redacción y revisión crítica
- Construir una **ficha de proyecto** con `/brief` y recibir revisión crítica con `/review`
- Ver qué MCPs de investigación tienes instalados en Claude Code y cómo usarlos
- Mantener historial de conversación dentro de la sesión
- Crear un workspace estructurado para cada proyecto con `yatiri init`

Funciona con **DeepSeek**, **OpenAI**, **Groq**, **Anthropic** o **Ollama** local —el que tengas disponible.

---

## Instalación

### Requisitos

- Python 3.10 o superior
- Git
- Al menos una de: [DeepSeek API key](https://platform.deepseek.com/api_keys) · [OpenAI API key](https://platform.openai.com) · [Groq API key](https://console.groq.com) · [Anthropic API key](https://console.anthropic.com) · [Ollama](https://ollama.com) local

### Pasos

```bash
git clone https://github.com/sebastianligueno/yatiri
cd yatiri
pip install -e .
yatiri setup    # configura proveedor y región
yatiri          # abre la sesión interactiva
```

Con pipx (entorno aislado):

```bash
pipx install git+https://github.com/sebastianligueno/yatiri
yatiri setup
```

### Configuración rápida de clave

```bash
# Cualquier proveedor, guárdalo permanente:
echo "tu-clave" > ~/.deepseek_key
echo 'export DEEPSEEK_API_KEY=$(cat ~/.deepseek_key)' >> ~/.bashrc
```

Ver [INSTALL.md](INSTALL.md) para instrucciones detalladas en Windows, macOS y Linux.

---

## Uso básico

```bash
yatiri                              # sesión interactiva
yatiri setup                        # configurar proveedor y región
yatiri init mi_proyecto             # crear workspace de investigación
yatiri chat "consulta" --mode search
```

Dentro de la sesión:

```
/search burnout docente Chile revisiones
/design Estudio mixto sobre bienestar académico universitario
/teach  Clase de 90 min sobre muestreo probabilístico
/write  Estructura para introducción de artículo empírico
/verify ¿Las afirmaciones del manuscrito tienen respaldo en los datos?

/brief  → completar ficha de proyecto (paradigma, pregunta, marco teórico, método…)
/review → revisión crítica del proyecto como evaluador externo

/mcp    ver MCPs detectados y sugerencias de instalación
/doctor diagnóstico de proveedores activos
/clear  limpiar historial de la sesión
```

---

## Modos

| Modo | Para qué |
|------|----------|
| `general` | Consulta académica libre |
| `search` | Búsqueda bibliográfica, síntesis de fuentes |
| `quant` | Diseño cuantitativo, estadística, supuestos |
| `qual` | Análisis cualitativo, codificación, corpus |
| `design` | Diseño de investigación, coherencia metodológica |
| `teach` | Planificación docente, secuencias, evaluación |
| `write` | Redacción académica, estructura argumental |
| `verify` | Revisión crítica de argumentos y trazabilidad |

---

## Fuentes de búsqueda

Todas las fuentes son gratuitas y de acceso abierto. No requieren clave.

| Fuente | Región | Qué cubre |
|--------|--------|-----------|
| SciELO | Iberoamérica | Revistas peer-reviewed en español y portugués |
| OpenAlex | Global | 250M+ works, open access, multidisciplinar |
| Semantic Scholar | Global | 200M+ papers, grafos de citación, IA |
| PubMed / NCBI | Global | Biomedicina, psicología clínica, salud mental |
| HAL | Europa / Francófonos | Ciencias sociales, humanidades, educación |
| J-STAGE | Japón / Asia | Todas las disciplinas, colaboraciones asiáticas |
| DuckDuckGo | Web | Institucional, normativa, prensa académica |

> **Sobre África:** AJOL (African Journals Online) no tiene API pública. AfricArXiv está parcialmente indexado en OpenAlex. Es una deuda pendiente del proyecto.

---

## Proveedores LLM

`yatiri setup` configura el proveedor. En modo `auto`, prueba en orden según las claves disponibles.

| Proveedor | Clave | Modelo por defecto | Nota |
|-----------|-------|--------------------|------|
| DeepSeek | `DEEPSEEK_API_KEY` | deepseek-chat | Bajo costo, recomendado |
| OpenAI | `OPENAI_API_KEY` | gpt-4o-mini | URL base configurable (Azure, etc.) |
| Groq | `GROQ_API_KEY` | llama-3.1-8b-instant | Rápido, capa gratuita disponible |
| Anthropic | `ANTHROPIC_API_KEY` | claude-haiku-4-5 | Claude API directa |
| Ollama | sin clave | phi4-mini:3.8b | Local, sin internet, sin costo |

---

## Región

Por defecto, `latam` —América Latina en español y portugués. Se puede cambiar con `yatiri setup`.

| Región | Idiomas prioritarios |
|--------|----------------------|
| `latam` | es, pt |
| `iberia` | es, pt |
| `chile` | es |
| `brazil` | pt, es |
| `global` | es, pt, en |

---

## Ficha de proyecto y revisión crítica

`/brief` abre un formulario interactivo que guarda en la sesión:

- Paradigma (cuantitativo / cualitativo / mixto)
- Fenómeno o problema de investigación
- Pregunta o hipótesis principal
- Objetivo general y objetivos específicos
- Marco teórico
- Metodología y plan de análisis
- Participantes / corpus / muestra

`/review` toma esa ficha y la evalúa como lo haría un evaluador externo: busca inconsistencias internas, amenazas a la validez, supuestos no explicitados y sesgos en el diseño. No valida —critica. El objetivo es que el proyecto llegue más sólido a un evaluador real.

---

## MCPs de investigación

Yatiri detecta qué herramientas MCP tienes instaladas en Claude Code (Zotero, Scite, Semantic Scholar, OpenAlex, PubMed, etc.) y las muestra con `/mcp`.

**Limitación:** Yatiri no puede llamar directamente a esos MCPs —eso requiere Claude Code como intermediario. Lo que hace es inventariarte lo disponible y sugerirte cómo usarlo desde Claude Code para búsquedas más avanzadas. Las APIs que esos MCPs usan (Semantic Scholar, PubMed, OpenAlex) están integradas directamente en Yatiri.

---

## Rigor epistémico

El LLM está instruido para:

- Distinguir entre fuentes recuperadas en la sesión y conocimiento de entrenamiento
- No citar autores, años ni DOIs que no haya recuperado
- Presentar evidencia contraria o matices que cuestionen la dirección de la consulta
- Calibrar el lenguaje según lo que los datos permiten
- Indicar cuándo la evidencia es insuficiente

Esto reduce alucinaciones bibliográficas y sesgo confirmatorio, pero no los elimina. Verifica siempre las referencias antes de usarlas.

---

## Estado del proyecto

v0.3.0 — en desarrollo activo. Las funciones centrales funcionan. Hay partes sin pulir. Si encuentras algo roto, abre un issue.

---

## Licencia

[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — libre para usar, adaptar y compartir con atribución; no comercial; las adaptaciones mantienen la misma licencia.

---

*Desarrollado con asistencia de Claude (Anthropic). Las decisiones de diseño, el enfoque regional, los casos de uso y la dirección del proyecto son del autor.*
