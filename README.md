# Google ADK — Motor de Reglas para Clasificación de Cartera Bancaria

## Descripción

Sistema multi-agente construido con el Agent Development Kit (ADK) de Google
que clasifica una cartera de clientes bancarios en tres acciones comerciales
usando un motor de reglas determinista y auditable.

Tres agentes operan en pipeline secuencial (`SequentialAgent`):

1. **Analista de Riesgo** (`LlmAgent`): Lee la cartera, ejecuta el motor de reglas
   mediante un `FunctionTool`, y guarda los resultados en el estado compartido.
2. **Estratega Comercial** (`LlmAgent`): Lee el resumen del analista desde el
   estado y valida la coherencia comercial.
3. **Auditor** (`LlmAgent`): Genera el reporte de auditoría formal verificando
   completitud, trazabilidad y coherencia.

## Diferencias clave con la versión CrewAI

| Aspecto | CrewAI | Google ADK |
|---------|--------|------------|
| Orquestación | `Crew` + `Process.sequential` | `SequentialAgent` + `sub_agents` |
| Compartir estado | `context=[tarea_anterior]` | `output_key` + `{variable}` en instructions |
| Tools | Subclase `BaseTool` + Pydantic | Funciones Python puras como `FunctionTool` |
| Ejecución | `crew.kickoff()` síncrono | `runner.run_async()` asíncrono |
| LLM | `LiteLlm(model_id="openrouter/...")` | `model="gemini-2.0-flash"` (nativo Gemini) o vía LiteLLM |

## Requisitos

- Python >= 3.10 (recomendado 3.12)
- Una API key de OpenRouter (gratuita)
- `uv` package manager (ver instalación abajo)

## Instalación de uv (si no lo tienes)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Setup del Proyecto

### 1. Clonar y entrar al proyecto

```bash
cd adk_cartera_bancaria
```

### 2. Crear entorno virtual

```bash
uv venv --python 3.12
```

### 3. Activar entorno virtual

```bash
# Linux/macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\activate

# Windows (CMD)
.venv\Scripts\activate.bat
```

### 4. Instalar dependencias

```bash
uv sync
```

### 5. Configurar API Key

```bash
# Copiar template
cp .env.example .env
```

Edita `.env` con tu editor favorito:

```
OPENROUTER_API_KEY=sk-or-v1-tu-api-key-aqui
```

**Obtener API key gratuita**: https://openrouter.ai/keys

### 6. Verificar instalación

```bash
# Verificar que las dependencias están instaladas
python -c "import pandas; import google.adk; print('✓ Instalación correcta')"

# Verificar que el CSV de ejemplo existe
ls data/g3_cartera_clientes.csv
```

## Ejecución

```bash
# Asegurar que el entorno está activado
source .venv/bin/activate

# Ejecutar el pipeline
python main.py
```

## Troubleshooting

| Problema | Solución |
|----------|----------|
| `ModuleNotFoundError: No module named 'google'` | Ejecutar `uv sync` |
| `OPENROUTER_API_KEY not found` | Verificar que `.env` existe y tiene la key |
| `FileNotFoundError: g3_cartera_clientes.csv` | Colocar CSV en `data/` |
| `Permission denied` | Verificar permisos de escritura en `output/` |

## Uso

```bash
# Colocar tu CSV de cartera en data/
cp tu_cartera.csv data/g3_cartera_clientes.csv

# Ejecutar
python main.py
```

## Salidas

| Archivo | Descripción |
|---------|-------------|
| `output/cartera_clasificada.csv` | CSV con columnas: accion_sugerida, regla_aplicada, justificacion |
| `output/reporte_auditoria.txt` | Reporte formal de auditoría |

## Estructura del proyecto

```
adk_cartera_bancaria/
├── main.py                     # Punto de entrada (async)
├── pipeline.py                 # SequentialAgent + LlmAgents
├── requirements.txt
├── .env.example
├── README.md
├── tools/
│   ├── __init__.py
│   ├── regla_engine.py         # Motor de reglas determinista (lógica pura)
│   └── agent_tools.py          # FunctionTools para los agentes ADK
├── data/
│   └── g3_cartera_clientes.csv
└── output/
```

## Catálogo de reglas

| Regla | Acción | Condiciones principales |
|-------|--------|------------------------|
| R01 | Banca de inversión | segmento ∈ {premium, select}, tiene_inversion, saldo > $2M, score > 550 |
| R02 | Banca de inversión | premium, no invierte, saldo > $8M, score > 700 |
| R03 | Banca de inversión | ingreso > $5M, saldo > $5M, score > 600 |
| R04 | Hipotecario | preaprobado > $5M, score > 500, ingreso > $2M, antigüedad > 60m, capacidad > $4M |
| R05 | Hipotecario | select/premium, capacidad > $3M, score > 550, 28-55 años, sin consumo |
| R06 | Hipotecario | masivo, ingreso > $1.5M, capacidad > $3.5M, score > 450, >90m, abona sueldo, sin consumo |
| R07 | Más cupo TC | Default — ninguna regla anterior aplica |
