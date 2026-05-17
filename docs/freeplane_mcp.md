# Freeplane MCP

Fecha de revisión: 2026-05-14

## Estado en esta máquina

- Binario detectado: `/usr/bin/freeplane`
- Tipo de integración: MCP oficial de Freeplane
- Estado práctico desde este sandbox: no verificable de extremo a extremo porque aquí no se pueden abrir sockets locales

## Qué ofrece

Freeplane documenta un servidor MCP oficial para que otra app local pueda leer o modificar mapas mentales desde Freeplane.

Casos de uso:

- construir mapas conceptuales de capítulos;
- reorganizar nodos desde una app MCP;
- mantener Freeplane como interfaz principal para el mapa;
- combinar escritura académica con mapas de conceptos, autores o argumentos.

## Requisitos

- Freeplane versión `1.13.1` o superior;
- habilitar AI integration en Freeplane;
- activar el servidor MCP sólo cuando se vaya a usar;
- definir puerto y token local.

## Configuración en Freeplane

Abrir preferencias AI desde el panel AI y configurar:

- `AI MCP server enabled`
- `AI MCP server port`
- `MCP token`

Valores recomendados:

- puerto: `6298`
- autenticación: `Authorization: Bearer <MCP token>`

Compatibilidad documentada por Freeplane:

- `Authorization: Bearer <MCP token>` como cabecera preferida
- `X-Freeplane-MCP-Token: <MCP token>` como cabecera legacy

## Notas operativas

- si el token está vacío, Freeplane genera uno en el primer intento y rechaza esa primera petición;
- después hay que copiar el token generado y reintentar;
- conviene desactivar el servidor MCP cuando no se use.

## Uso recomendado en este proyecto

Usar `Freeplane MCP` para:

1. mapas del capítulo sobre emociones;
2. mapas de autores, teorías y debates;
3. matrices visuales de dimensiones afectivas, regulación y contextos;
4. esquemas para clases y capítulos antes de redactar.

## Rutas sugeridas en el proyecto

- `maps/`
- `mindmaps/`

## Fuentes

- Freeplane MCP server:
  https://docs.freeplane.org/ai/model-context-protocol-server.html
- Freeplane AI integration:
  https://docs.freeplane.org/ai/ai-integration-getting-started.html
