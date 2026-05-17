# Arquitectura inicial

## Capas

- `cli`: parsea comandos y muestra resultados
- `core.project`: detecta raiz, carga configuracion y resuelve rutas
- `core.profiles`: infiere perfil y ejecuta chequeos
- `core.registry`: administra `.research/*.jsonl`

## Estado del MVP

El MVP implementado en este scaffold cubre:

- `init`
- `scan`
- `status`

Todavia no ejecuta pipelines ni hace retrieval semantico.
