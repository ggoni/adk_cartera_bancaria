"""
Pipeline de agentes ADK — SequentialAgent con 3 LlmAgents.

Cada agente usa output_key para guardar su resultado en el estado compartido
de la sesión, y los agentes posteriores lo leen con {variable} en sus
instructions.
"""

from pathlib import Path
from google.adk.agents import LlmAgent, SequentialAgent

from tools.agent_tools import (
    leer_cartera,
    ejecutar_motor_reglas,
    generar_reporte_auditoria,
)

# ============================================================================
# RUTAS (relativas al directorio del proyecto)
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent
INPUT_CSV = str(BASE_DIR / "data" / "g3_cartera_clientes.csv")
OUTPUT_CSV = str(BASE_DIR / "output" / "cartera_clasificada.csv")
AUDIT_REPORT = str(BASE_DIR / "output" / "reporte_auditoria.txt")

# ============================================================================
# MODELO
# ============================================================================
from google.adk.models.lite_llm import LiteLlm

# Gemini Flash es rápido y barato. Para mayor calidad, usar "gemini-2.0-pro".
# Ahora configurado usando OpenRouter vía LiteLLM
MODEL = LiteLlm(model="openrouter/qwen/qwen3-5-plus")

# ============================================================================
# AGENTE 1: ANALISTA DE RIESGO
# ============================================================================

analista_riesgo = LlmAgent(
    name="analista_riesgo",
    model=MODEL,
    description="Analista senior de riesgo crediticio bancario chileno.",
    instruction=f"""Eres un analista de riesgo con 15 años de experiencia en banca retail chilena.

Tu tarea tiene dos pasos:

1. Primero, usa la herramienta 'leer_cartera' con filepath='{INPUT_CSV}'
   para obtener un resumen estadístico de la cartera.

2. Luego, usa la herramienta 'ejecutar_motor_reglas' con
   input_filepath='{INPUT_CSV}' y output_filepath='{OUTPUT_CSV}'
   para clasificar a cada cliente.

Reporta ambos resultados: el resumen de la cartera y la distribución
de la clasificación resultante. Cada decisión es trazable a una regla
del catálogo (R01-R07).
""",
    tools=[leer_cartera, ejecutar_motor_reglas],
    output_key="resultado_analisis",
)

# ============================================================================
# AGENTE 2: ESTRATEGA COMERCIAL
# ============================================================================

estratega_comercial = LlmAgent(
    name="estratega_comercial",
    model=MODEL,
    description="Estratega comercial de banca personas.",
    instruction=f"""Eres un estratega comercial con experiencia en cross-selling bancario en Chile.

El analista de riesgo ya clasificó la cartera. Sus resultados son:
{{resultado_analisis}}

Tu tarea es revisar la clasificación y emitir una opinión comercial:
1. ¿La distribución por acción es comercialmente viable?
2. ¿Hay concentraciones excesivas en una sola acción?
3. ¿Los clientes premium/select están bien atendidos?

Usa la herramienta 'leer_cartera' con filepath='{OUTPUT_CSV}' si
necesitas verificar datos adicionales del archivo clasificado.

Emite recomendaciones específicas si detectas problemas.
""",
    tools=[leer_cartera],
    output_key="revision_comercial",
)

# ============================================================================
# AGENTE 3: AUDITOR
# ============================================================================

auditor = LlmAgent(
    name="auditor_cumplimiento",
    model=MODEL,
    description="Auditor interno de modelos de decisión crediticia.",
    instruction=f"""Eres un auditor especializado en modelos de decisión crediticia.

Contexto del analista: {{resultado_analisis}}
Contexto del estratega: {{revision_comercial}}

Tu tarea es generar el reporte de auditoría formal. Usa la herramienta
'generar_reporte_auditoria' con classified_filepath='{OUTPUT_CSV}'
y report_filepath='{AUDIT_REPORT}'.

Verifica completitud, trazabilidad y coherencia. Incluye el reporte
completo en tu respuesta final.
""",
    tools=[generar_reporte_auditoria],
    output_key="reporte_auditoria",
)

# ============================================================================
# PIPELINE SECUENCIAL
# ============================================================================

pipeline = SequentialAgent(
    name="clasificacion_cartera_bancaria",
    description=(
        "Pipeline secuencial para clasificar cartera de clientes bancarios. "
        "Ejecuta análisis de riesgo, revisión comercial y auditoría."
    ),
    sub_agents=[analista_riesgo, estratega_comercial, auditor],
)
