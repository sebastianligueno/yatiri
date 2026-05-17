# Yatiri

**Asistente académico de terminal para investigación en Iberoamérica**

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![AI Assisted](https://img.shields.io/badge/developed%20with-Claude%20AI-blueviolet)](https://claude.ai)

---

*Yatiri* es una palabra aymara del norte de Chile: el que sabe, el que lee los signos para orientar a otros. En las comunidades andinas es el consejero que interpreta fuentes dispersas y guía la decisión.

Esta herramienta toma ese nombre porque hace exactamente eso: lee múltiples fuentes académicas y orienta el trabajo de investigación desde el terminal.

## Por qué existe

La mayoría de los asistentes de IA académicos asumen un contexto anglófono. Sus fuentes predeterminadas, sus criterios de relevancia y su noción de "literatura pertinente" apuntan al circuito inglés del Norte global.

Yatiri parte de la hipótesis contraria: la investigación en Psicología, Ciencias Sociales, Educación e Historia en Chile, Argentina, México, Brasil, España y el resto de Iberoamérica tiene su propia producción, sus propias revistas y sus propios archivos. Merece una herramienta que los conozca y los priorice.

## Qué hace

- Sesión interactiva en el terminal con modos especializados: búsqueda, diseño de investigación, metodología cuantitativa y cualitativa, docencia, redacción y revisión crítica
- Búsqueda académica en **SciELO**, **OpenAlex** y web, con síntesis por LLM
- Contexto regional configurable: `latam` (por defecto), `iberia`, `chile`, `brazil`, `global`
- Detecta los **MCPs ya instalados** en Claude Code y los reporta como parte del stack disponible
- Historial de conversación multi-turno dentro de la sesión
- Workspace de investigación estructurado con `yatiri init`
- Funciona con **DeepSeek API** (bajo costo) u **Ollama** local (sin internet, sin costo)

## Instalación rápida

```bash
git clone https://github.com/sebastianligueno/yatiri
cd yatiri
pip install -e .
yatiri setup    # configura API key y región
yatiri          # abre la sesión interactiva
```

Con pipx (entorno aislado):

```bash
pipx install git+https://github.com/sebastianligueno/yatiri
```

Ver [INSTALL.md](INSTALL.md) para instrucciones detalladas en Windows, macOS y Linux.

## Uso básico

```bash
yatiri                          # sesión interactiva
yatiri setup                    # configurar API key y región
yatiri init mi_proyecto         # crear workspace de investigación
yatiri chat "consulta" --mode search
```

Dentro de la sesión:

```
/search burnout docente Chile revisiones sistemáticas
/teach Diseña una clase de 90 min sobre muestreo probabilístico
/design Estudio mixto sobre bienestar académico en universidades regionales
/verify ¿Las afirmaciones del manuscrito tienen respaldo en los datos?
/mcp                            # ver MCPs instalados y sugerencias
/doctor                         # diagnóstico de proveedores activos
```

## Modos

| Modo | Para qué |
|------|----------|
| `general` | Consulta académica libre |
| `search` | Estrategia bibliográfica, recuperación de fuentes |
| `quant` | Diseño cuantitativo, estadística, supuestos |
| `qual` | Análisis cualitativo, corpus, codificación |
| `design` | Diseño de investigación, coherencia metodológica |
| `teach` | Planificación docente, secuencias, evaluación |
| `write` | Redacción académica, estructura argumental |
| `verify` | Revisión crítica, saltos inferenciales, trazabilidad |

## Fuentes integradas

| Fuente | Cobertura | Clave |
|--------|-----------|-------|
| SciELO | Iberoamérica, artículos revisados | No |
| OpenAlex | 250M+ works global, open access | No |
| DuckDuckGo | Web general, institucional, prensa | No |

## Regiones

```bash
yatiri setup   # opción 4: cambiar región
```

| Región | Idiomas | Fuentes prioritarias |
|--------|---------|----------------------|
| `latam` | es, pt | SciELO, Redalyc, Dialnet |
| `iberia` | es, pt | Dialnet, CSIC, SciELO |
| `chile` | es | SciELO-Chile, ANID |
| `brazil` | pt, es | SciELO-Brasil, CAPES |
| `global` | es, pt, en | OpenAlex, PubMed |

## Requisitos

- Python 3.10+
- [DeepSeek API key](https://platform.deepseek.com/api_keys) (recomendado, muy bajo costo) o [Ollama](https://ollama.com) para modo local

## Documentación

- [MANUAL.md](MANUAL.md) — manual completo en español
- [INSTALL.md](INSTALL.md) — instalación detallada para Windows, macOS y Linux

## Limitaciones

- La integración con MCPs es de detección e inventario. Las búsquedas avanzadas con Zotero, Scite o Semantic Scholar se hacen desde Claude Code.
- Los modelos locales pequeños (< 7B) tienen calidad limitada para redacción académica compleja.
- Verificar siempre las referencias que el LLM mencione en modo fallback — puede construir citas plausibles pero no verificadas.

## Licencia

[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — libre para usar, compartir y adaptar con atribución; no comercial; las adaptaciones deben mantener la misma licencia.

---

## Sobre el nombre

*Yatiri* viene del aymara del norte de Chile: el que sabe, el consejero que lee señales dispersas para orientar a otros. La palabra ya es compuesta: *yati* (saber) + *-ri* (agente). El nombre está tomado de la tradición intelectual de los pueblos andinos, con respeto.

---

## Nota sobre desarrollo asistido por IA

Este proyecto fue desarrollado con asistencia de Claude (Anthropic) como herramienta colaborativa. Las decisiones de diseño, el conocimiento de dominio, los casos de uso y la dirección del proyecto son propios del autor. La asistencia de IA se usó para generación de código, depuración y redacción de documentación.

---

*Versión 0.3.0 · Mayo 2026*
