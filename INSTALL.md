# Instalación de Scholar CLI

Asistente académico de terminal para Psicología y Ciencias Sociales.  
Funciona en **Windows, macOS y Linux** con Python 3.10 o superior.

---

## Requisitos previos

- Python 3.10+ instalado ([python.org](https://www.python.org/downloads/))
- Conexión a internet (para DeepSeek y búsquedas académicas)
- Opcional: [Ollama](https://ollama.com) para modo local sin API

Verificar Python:

```bash
python --version      # Windows
python3 --version     # macOS / Linux
```

---

## Instalación

### Opción A — pipx (recomendado: entorno aislado, sin conflictos)

```bash
pip install pipx
pipx install git+https://github.com/usuario/scholar-cli
```

### Opción B — uv (más rápido)

```bash
pip install uv
uv tool install git+https://github.com/usuario/scholar-cli
```

### Opción C — pip directo

```bash
pip install git+https://github.com/usuario/scholar-cli
```

### Opción D — desde el código fuente (para desarrollo)

```bash
git clone https://github.com/usuario/scholar-cli
cd scholar-cli
pip install -e .
```

---

## Configuración de la API key

Después de instalar, ejecuta el wizard de configuración:

```bash
scholar setup
```

Este comando es interactivo, guarda la clave en `~/.scholar_operator/config.yaml` y **no requiere modificar variables de entorno del sistema**.

### Alternativa: variable de entorno

**Linux / macOS** — agregar a `~/.bashrc` o `~/.zshrc`:

```bash
export DEEPSEEK_API_KEY="tu-clave-aqui"
```

**Windows (PowerShell)** — permanente para el usuario:

```powershell
[System.Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "tu-clave-aqui", "User")
```

**Windows (CMD)**:

```cmd
setx DEEPSEEK_API_KEY "tu-clave-aqui"
```

> La clave de DeepSeek se obtiene en [platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys).  
> El modelo `deepseek-chat` tiene costo muy bajo (~$0.28/millón de tokens de entrada).

---

## Primer uso

```bash
scholar            # abre sesión interactiva
scholar setup      # configura API key y proveedor
scholar init .     # inicializa workspace en el directorio actual
```

Dentro de la sesión:

```
/help                                      → lista de comandos
/search burnout docente universitario      → búsqueda académica
/teach Diseña una clase sobre muestreo     → diseño de clase
/design Estudio sobre bienestar docente    → diseño de investigación
/attach /ruta/al/proyecto                  → adjunta contexto de carpeta
/doctor                                    → diagnóstico de proveedores
```

Modo no interactivo (scripts, terminales sin TTY):

```bash
scholar chat "Diseña una clase sobre muestreo" --mode teach
scholar chat "burnout docente" --mode search
scholar chat "¿Qué dice el manuscrito?" --mode verify --attach ./mi_proyecto
```

---

## Uso sin API (modo Ollama local)

Para usar sin clave y sin conexión a internet:

1. Instalar [Ollama](https://ollama.com)
2. Descargar un modelo:

```bash
ollama pull gemma3:4b       # equilibrio calidad/velocidad (~3 GB)
ollama pull phi4-mini       # liviano (~2.5 GB)
ollama pull llama3.2:3b     # opción alternativa
```

3. Configurar:

```bash
scholar setup
# → Proveedor: ollama
# → Modelo Ollama: gemma3:4b
```

O definir variable de entorno:

```bash
export SCHOLAR_MODEL_PROVIDER=ollama
export SCHOLAR_OLLAMA_MODEL=gemma3:4b
```

---

## Workspace de investigación

Crear una carpeta de proyecto con estructura completa:

```bash
scholar init mi_investigacion
```

Esto genera:

```
mi_investigacion/
├── data/
│   ├── raw/          ← datos originales
│   └── processed/    ← datos procesados
├── docs/             ← documentos de trabajo
├── notes/            ← notas y memos
├── maps/             ← mapas conceptuales
├── paper/            ← manuscrito(s)
├── .research/        ← metadatos del proyecto
└── README.md
```

Luego dentro de Scholar:

```
/attach /ruta/a/mi_investigacion
/verify ¿Qué afirmaciones necesitan respaldo?
```

---

## Actualizar

```bash
pipx upgrade scholar-cli                               # si usó pipx
uv tool upgrade scholar-cli                            # si usó uv
pip install --upgrade git+https://github.com/...       # si usó pip
```

---

## Solución de problemas

**`scholar: command not found`**  
Asegurarse de que `~/.local/bin` (Linux/macOS) o el directorio de scripts de Python está en el PATH.

**DeepSeek no responde / timeout**  
Verificar clave con `scholar setup` → mostrar configuración actual. Revisar `scholar /doctor` dentro de la sesión.

**Ollama: 404 Not Found**  
El daemon de Ollama no está corriendo. Ejecutar `ollama serve` en otra terminal antes de abrir Scholar.

**Windows: error de codificación**  
Abrir terminal con `chcp 65001` para UTF-8, o usar Windows Terminal (no CMD clásico).
