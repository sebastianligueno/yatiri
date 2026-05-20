# Instalación de Yatiri

Asistente académico de terminal para Psicología y Ciencias Sociales.  
Funciona en **Windows, macOS y Linux** con Python 3.10 o superior.

---

## Requisitos previos

- Python 3.10+ instalado ([python.org](https://www.python.org/downloads/))
- Git
- Conexión a internet (para DeepSeek y búsquedas académicas)
- Opcional: [Ollama](https://ollama.com) para modo local sin API

Verificar Python:

```bash
python --version      # Windows
python3 --version     # macOS / Linux
```

---

## Instalación

### Desde el código fuente (recomendado)

```bash
git clone https://github.com/sebastianligueno/yatiri
cd yatiri
pip install -e .
```

### Desde GitHub directamente

```bash
pip install git+https://github.com/sebastianligueno/yatiri
```

---

## Configuración de la API key

Después de instalar, ejecuta el wizard de configuración:

```bash
yatiri setup
```

Este comando es interactivo, guarda la clave en `~/.yatiri/config.yaml` y **no requiere modificar variables de entorno del sistema**.

### Alternativa: variable de entorno

**Linux / macOS** — agregar a `~/.bashrc` o `~/.zshrc`:

```bash
export DEEPSEEK_API_KEY="tu-clave-aqui"
```

**Windows (PowerShell)** — permanente para el usuario:

```powershell
[System.Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "tu-clave-aqui", "User")
```

> La clave de DeepSeek se obtiene en [platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys).  
> El modelo `deepseek-chat` tiene costo muy bajo (~$0.28/millón de tokens de entrada).

---

## Primer uso

```bash
yatiri            # abre sesión interactiva
yatiri setup      # configura API key y proveedor
yatiri init .     # inicializa workspace en el directorio actual
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
yatiri chat "Diseña una clase sobre muestreo" --mode teach
yatiri chat "burnout docente" --mode search
yatiri chat "¿Qué dice el manuscrito?" --mode verify --attach ./mi_proyecto
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
yatiri setup
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
yatiri init mi_investigacion
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

---

## Actualizar

```bash
cd yatiri
git pull
pip install -e .
```

---

## Solución de problemas

**`yatiri: command not found`**  
Asegurarse de que `~/.local/bin` (Linux/macOS) esté en el PATH. Agregar a `~/.bashrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

**DeepSeek no responde / timeout**  
Verificar clave con `yatiri setup` → mostrar configuración actual. Revisar `yatiri /doctor` dentro de la sesión.

**Ollama: 404 Not Found**  
El daemon de Ollama no está corriendo. Ejecutar `ollama serve` en otra terminal antes de abrir Yatiri.

**Windows: error de codificación**  
Abrir terminal con `chcp 65001` para UTF-8, o usar Windows Terminal (no CMD clásico).
