"""
Punto de entrada — Clasificación de Cartera Bancaria con Google ADK.

Uso:
    python main.py
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from google.adk.runners import InMemoryRunner
from google.genai import types

from pipeline import pipeline, INPUT_CSV, OUTPUT_CSV, AUDIT_REPORT


APP_NAME = "clasificacion_cartera"
USER_ID = "analista_principal"
SESSION_ID = "sesion_clasificacion"


async def main():
    if not Path(INPUT_CSV).exists():
        print(f"ERROR: No se encontró el archivo de cartera en {INPUT_CSV}")
        print("Coloca tu CSV en la carpeta data/ con el nombre g3_cartera_clientes.csv")
        sys.exit(1)

    # Asegurar directorio de salida
    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("GOOGLE ADK — CLASIFICACIÓN DE CARTERA BANCARIA")
    print("=" * 70)
    print(f"  Entrada:  {INPUT_CSV}")
    print(f"  Salida:   {OUTPUT_CSV}")
    print(f"  Reporte:  {AUDIT_REPORT}")
    print("=" * 70)

    # Crear runner con el pipeline secuencial
    runner = InMemoryRunner(agent=pipeline, app_name=APP_NAME)

    # Crear sesión
    await runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

    # Ejecutar el pipeline
    prompt = (
        "Ejecuta el pipeline completo de clasificación de cartera bancaria: "
        "1) Lee y analiza la cartera, "
        "2) Ejecuta el motor de reglas para clasificar cada cliente, "
        "3) Revisa la coherencia comercial, "
        "4) Genera el reporte de auditoría."
    )

    print("\nEjecutando pipeline...\n")

    final_text = ""
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=types.Content(
            role="user",
            parts=[types.Part(text=prompt)],
        ),
    ):
        # Imprimir eventos intermedios de cada agente
        if event.author and event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    print(f"[{event.author}] {part.text[:200]}...")
                    if event.is_final_response():
                        final_text = part.text

    print("\n" + "=" * 70)
    print("RESULTADO FINAL")
    print("=" * 70)
    if final_text:
        print(final_text)

    print(f"\nArchivos generados:")
    print(f"  CSV clasificado:    {OUTPUT_CSV}")
    print(f"  Reporte auditoría:  {AUDIT_REPORT}")


if __name__ == "__main__":
    asyncio.run(main())
