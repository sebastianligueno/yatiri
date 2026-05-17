# Yatiri

*Herramienta personal de terminal para investigación académica en Iberoamérica*

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![AI Assisted](https://img.shields.io/badge/developed%20with-Claude%20AI-blueviolet)](https://claude.ai)

---

La hice para uso propio. Soy docente universitario en Chile y trabajo con bibliografía en español y portugués. Los asistentes que encontré priorizaban el circuito anglosajón, así que armé algo que buscara en SciELO y OpenAlex y me respondiera desde ese contexto.

El nombre viene del aymara: *yatiri* es el que sabe, el que lee señales dispersas para orientar a otros. Lo elegí porque me lo sugirió alguien que quiero mucho y que conoce bien ese pueblo.

Si te sirve, úsala. Si la mejoras, comparte.

---

## Qué hace

Abre una sesión interactiva en el terminal con la que puedes:

- Hacer consultas académicas con contexto iberoamericano
- Buscar en **SciELO** y **OpenAlex** y recibir una síntesis
- Trabajar en distintos modos: búsqueda, diseño de investigación, metodología, docencia, redacción, revisión crítica
- Detectar qué MCPs tienes instalados en Claude Code y usarlos como parte del stack
- Mantener historial de conversación dentro de la sesión
- Crear un workspace estructurado para cada proyecto

Funciona con **DeepSeek** (muy bajo costo) u **Ollama** local (sin internet, sin costo).

## Instalación

```bash
git clone https://github.com/sebastianligueno/yatiri
cd yatiri
pip install -e .
yatiri setup    # configura API key y región
yatiri          # abre la sesión interactiva
```

Con pipx:

```bash
pipx install git+https://github.com/sebastianligueno/yatiri
```

Ver [INSTALL.md](INSTALL.md) para instrucciones en Windows, macOS y Linux.

## Uso básico

```bash
yatiri                              # sesión interactiva
yatiri setup                        # configurar proveedor y región
yatiri init mi_proyecto             # crear workspace de investigación
yatiri chat "consulta" --mode search
```

Dentro de la sesión:

```
/search burnout docente Chile
/teach Diseña una clase sobre muestreo probabilístico
/design Estudio mixto sobre bienestar académico
/verify ¿Las afirmaciones del manuscrito tienen respaldo?
/mcp     ver MCPs disponibles
/doctor  diagnóstico de proveedores activos
```

## Modos

| Modo | Para qué |
|------|----------|
| `general` | Consulta académica libre |
| `search` | Búsqueda bibliográfica, fuentes |
| `quant` | Diseño cuantitativo, estadística |
| `qual` | Análisis cualitativo, codificación |
| `design` | Diseño de investigación |
| `teach` | Planificación docente |
| `write` | Redacción académica |
| `verify` | Revisión crítica de argumentos |

## Región por defecto

`latam` — América Latina en español y portugués. Se puede cambiar con `yatiri setup`.

## Requisitos

- Python 3.10+
- [DeepSeek API key](https://platform.deepseek.com/api_keys) o [Ollama](https://ollama.com) local

## Estado

Herramienta en desarrollo activo, v0.3.0. Las funciones centrales funcionan. Hay partes que todavía están sin pulir. Si encuentras algo roto, abre un issue.

## Licencia

[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — libre para usar, adaptar y compartir con atribución; no comercial; las adaptaciones mantienen la misma licencia.

---

*Desarrollado con asistencia de Claude (Anthropic). Las decisiones de diseño, el enfoque y los casos de uso son del autor.*
