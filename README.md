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

- Consultar con contexto iberoamericano por defecto
- Buscar en **SciELO** y **OpenAlex** y recibir síntesis fundamentada en las fuentes recuperadas
- Trabajar en modos especializados: búsqueda, diseño de investigación, metodología, docencia, redacción y revisión crítica
- Ver qué MCPs de investigación tienes instalados en Claude Code y cómo usarlos. Esto, para que la búsqueda esté integrada
- Mantener historial de conversación dentro de la sesión
- Crear un espacio de trabajo estructurado para cada proyecto

Funciona con **DeepSeek API** (muy bajo costo), u otra api. También se puede usar **Ollama** local (sin internet, sin costo).

---

## Instalación

### Requisitos previos

- Python 3.10 o superior
- Una [API key de DeepSeek](https://platform.deepseek.com/api_keys) **o** [Ollama](https://ollama.com) instalado localmente
- Git

### Pasos

```bash
git clone https://github.com/sebastianligueno/yatiri
cd yatiri
pip install -e .
yatiri setup    # configura API key y región
yatiri          # abre la sesión interactiva
```

Con pipx (entorno aislado, recomendado):

```bash
pipx install git+https://github.com/sebastianligueno/yatiri
yatiri setup
```

Ver [INSTALL.md](INSTALL.md) para instrucciones detalladas en Windows, macOS y Linux.

### Configurar la API key manualmente

```bash
# DeepSeek (recomendado, por el costo)
export DEEPSEEK_API_KEY="tu-clave"

# O guárdarla permanente:
echo "tu-clave" > ~/.deepseek_key
echo 'export DEEPSEEK_API_KEY=$(cat ~/.deepseek_key)' >> ~/.bashrc
```

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
/mcp    Ver MCPs detectados y sugerencias de instalación
/doctor Diagnóstico de proveedores activos
/clear  Limpiar historial de la sesión
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
| `verify` | Revisión crítica, saltos inferenciales, trazabilidad |

---

## Fuentes de búsqueda

| Fuente | Qué cubre |
|--------|-----------|
| SciELO | Iberoamérica, artículos revisados por pares |
| OpenAlex | 250M+ trabajos globales, open access |
| Web (DuckDuckGo) | Institucional, normativa, prensa académica |

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

## MCPs de investigación

Yatiri detecta qué herramientas MCP tienes instaladas en Claude Code, Codex u otros agentes vía terminal (Zotero, Scite, Semantic Scholar, OpenAlex, PubMed, etc.) y las muestra con el comando `/mcp`.

**Limitación importante:** Yatiri no puede *llamar* directamente a esos MCPs —eso solo lo puede hacer el asistente que tiene acceso al protocolo MCP. Lo que hace es inventariarte lo disponible y sugerirte cómo usarlo desde Claude Code u otra plataforma para búsquedas más avanzadas.

---

## Rigor epistémico

El LLM está instruido para:

- Distinguir explícitamente entre fuentes recuperadas en la sesión y conocimiento de entrenamiento
- No citar autores, años ni DOIs que no haya recuperado
- Presentar evidencia contraria o matices que cuestionen la dirección de la consulta
- Calibrar la certeza del lenguaje según lo que los datos permiten
- Indicar cuándo la evidencia es insuficiente en lugar de rellenar con afirmaciones plausibles

Esto reduce alucinaciones bibliográficas y sesgo confirmatorio, pero no los elimina. Por eso, siempre se debe verificar las referencias antes de usarlas, pero entiendo que esto es propio de cualquier trabajo de investigación

---

## Estado del proyecto

v0.3.0 — en desarrollo activo. Las funciones centrales funcionan. Hay partes sin pulir. Si encuentras algo roto, abre un issue.

---

## Licencia

[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — libre para usar, adaptar y compartir con atribución; no comercial; las adaptaciones mantienen la misma licencia.

---

*Desarrollado con asistencia de Claude (Anthropic). Las decisiones de diseño, el enfoque regional, los casos de uso y la dirección del proyecto son del autor.*
