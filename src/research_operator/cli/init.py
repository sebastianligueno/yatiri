from __future__ import annotations

from pathlib import Path

from research_operator.core.project import ensure_research_layout, init_project_config


_WORKSPACE_DIRS = [
    "data/raw",
    "data/processed",
    "docs",
    "notes",
    "maps",
    "paper",
]

_README_TEMPLATE = """\
# {name}

## Descripción

*(Reemplaza este texto con la descripción del proyecto.)*

## Estructura

```
{name}/
├── data/
│   ├── raw/          ← datos originales sin modificar
│   └── processed/    ← datos procesados o transformados
├── docs/             ← documentos de trabajo, protocolos, reportes
├── notes/            ← notas y memos de investigación
├── maps/             ← mapas conceptuales (Freeplane u otro)
├── paper/            ← manuscrito(s)
└── .research/        ← metadatos del proyecto (Yatiri)
```

## Uso con Yatiri

Abrir sesión interactiva con contexto del proyecto:

```bash
yatiri
/attach .
```

O directamente:

```bash
yatiri chat "Consulta sobre el proyecto" --attach .
```

Comandos útiles dentro de la sesión:

```
/search <consulta>    búsqueda académica (SciELO + OpenAlex + web)
/design <consulta>    diseño de investigación
/write <consulta>     redacción académica
/verify <consulta>    revisión crítica de argumentos
/teach <consulta>     diseño de clases y materiales docentes
/doctor               diagnóstico de proveedores activos
```

## Proveedores de IA

Configura tu clave con:

```bash
yatiri setup
```

O define la variable de entorno:

```bash
export DEEPSEEK_API_KEY="tu-clave"
```
"""


def run_init(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _create_workspace_dirs(root)
    ensure_research_layout(root)
    config_path = init_project_config(root)
    _create_readme(root)
    print(f"Workspace inicializado en: {root}")
    print(f"Configuración del proyecto: {config_path}")
    print("")
    print("Estructura creada:")
    for d in _WORKSPACE_DIRS:
        print(f"  {root / d}/")
    print(f"  {root / '.research'}/")
    print("")
    print("Próximo paso:")
    print("  yatiri setup      → configurar API key")
    print("  yatiri            → abrir sesión interactiva")


def _create_workspace_dirs(root: Path) -> None:
    for rel in _WORKSPACE_DIRS:
        target = root / rel
        target.mkdir(parents=True, exist_ok=True)
        gitkeep = target / ".gitkeep"
        if not any(target.iterdir()) and not gitkeep.exists():
            gitkeep.touch()


def _create_readme(root: Path) -> None:
    target = root / "README.md"
    if target.exists():
        return
    name = root.name.replace("_", " ").replace("-", " ").strip() or "Proyecto"
    target.write_text(_README_TEMPLATE.format(name=name), encoding="utf-8")
