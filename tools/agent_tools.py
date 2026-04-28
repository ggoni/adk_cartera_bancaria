"""
FunctionTools para Google ADK.

En ADK, las herramientas son funciones Python puras con docstrings claros
y type hints. El framework las envuelve automáticamente como FunctionTool
cuando se pasan en la lista `tools` de un Agent.

Cada función recibe parámetros tipados y retorna un dict con los resultados.
"""

import pandas as pd
from pathlib import Path
from .regla_engine import ejecutar_motor, REGLAS


def leer_cartera(filepath: str) -> dict:
    """Lee un archivo CSV de cartera bancaria y devuelve un resumen estadístico.

    Incluye cantidad de clientes, distribución por segmento, estadísticas de
    ingreso, score de riesgo, saldos y penetración de productos.

    Args:
        filepath: Ruta al archivo CSV de cartera de clientes.

    Returns:
        dict: Resumen con total_clientes, segmentos, estadísticas de ingreso,
              score, saldo y penetración de productos.
    """
    df = pd.read_csv(filepath)
    return {
        "status": "success",
        "total_clientes": len(df),
        "segmentos": df["segmento"].value_counts().to_dict(),
        "ingreso_medio": f"${df['ingreso_mensual_clp'].mean():,.0f}",
        "ingreso_mediana": f"${df['ingreso_mensual_clp'].median():,.0f}",
        "score_riesgo_medio": f"{df['score_riesgo'].mean():.0f}",
        "score_riesgo_min": int(df["score_riesgo"].min()),
        "score_riesgo_max": int(df["score_riesgo"].max()),
        "saldo_promedio_medio": f"${df['saldo_promedio_clp'].mean():,.0f}",
        "pct_con_inversion": f"{df['tiene_inversion'].mean()*100:.1f}%",
        "pct_con_tarjeta_credito": f"{df['tiene_tarjeta_credito'].mean()*100:.1f}%",
        "pct_con_credito_consumo": f"{df['tiene_credito_consumo'].mean()*100:.1f}%",
        "pct_abona_sueldo": f"{df['abona_sueldo'].mean()*100:.1f}%",
    }


def ejecutar_motor_reglas(input_filepath: str, output_filepath: str) -> dict:
    """Ejecuta el motor de reglas determinista sobre la cartera completa.

    Evalúa 7 reglas en orden de prioridad (R01-R07) para asignar a cada
    cliente exactamente una acción comercial. Agrega al CSV las columnas:
    accion_sugerida, regla_aplicada y justificacion.

    Args:
        input_filepath: Ruta al CSV de cartera de clientes.
        output_filepath: Ruta donde guardar el CSV con las acciones asignadas.

    Returns:
        dict: Resultado con distribución por acción, por regla y métricas.
    """
    df = pd.read_csv(input_filepath)
    df = ejecutar_motor(df)

    Path(output_filepath).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_filepath, index=False, encoding="utf-8-sig")

    dist_accion = {}
    for accion, count in df["accion_sugerida"].value_counts().items():
        dist_accion[accion] = {"cantidad": int(count), "porcentaje": f"{count/len(df)*100:.1f}%"}

    dist_regla = {}
    for regla in sorted(df["regla_aplicada"].unique()):
        count = int(len(df[df["regla_aplicada"] == regla]))
        nombre = next(
            (r["nombre"] for r in REGLAS if r["codigo"] == regla),
            "Default — Más cupo TC",
        )
        dist_regla[regla] = {"nombre": nombre, "cantidad": count}

    metricas = {}
    for accion, group in df.groupby("accion_sugerida"):
        metricas[accion] = {
            "score_medio": f"{group['score_riesgo'].mean():.0f}",
            "ingreso_medio": f"${group['ingreso_mensual_clp'].mean():,.0f}",
        }

    return {
        "status": "success",
        "clientes_procesados": len(df),
        "archivo_guardado": output_filepath,
        "distribucion_por_accion": dist_accion,
        "distribucion_por_regla": dist_regla,
        "metricas_por_accion": metricas,
    }


def generar_reporte_auditoria(classified_filepath: str, report_filepath: str) -> dict:
    """Genera un reporte de auditoría formal sobre el CSV ya clasificado.

    Verifica completitud (todos los clientes tienen asignación), trazabilidad
    (cada cliente tiene código de regla válido), coherencia de umbrales, y
    genera estadísticas detalladas de distribución.

    Args:
        classified_filepath: Ruta al CSV ya clasificado con acciones.
        report_filepath: Ruta donde guardar el reporte de auditoría en texto.

    Returns:
        dict: Resultados de las verificaciones y el reporte completo.
    """
    df = pd.read_csv(classified_filepath)

    sin_accion = int(df["accion_sugerida"].isna().sum())
    sin_regla = int(df["regla_aplicada"].isna().sum())
    sin_justificacion = int(df["justificacion"].isna().sum())

    reglas_validas = {"R01", "R02", "R03", "R04", "R05", "R06", "R07"}
    reglas_encontradas = set(df["regla_aplicada"].unique())
    reglas_invalidas = reglas_encontradas - reglas_validas

    alertas = []
    bi = df[df["accion_sugerida"] == "Banca de inversión"]
    if len(bi) > 0 and bi["score_riesgo"].min() < 500:
        n = int(len(bi[bi["score_riesgo"] < 500]))
        alertas.append(f"ALERTA: {n} clientes en Banca de inversión con score < 500")

    hip = df[df["accion_sugerida"] == "Ofrecer hipotecario"]
    if len(hip) > 0 and hip["capacidad_endeudamiento_clp"].min() < 2_000_000:
        n = int(len(hip[hip["capacidad_endeudamiento_clp"] < 2_000_000]))
        alertas.append(f"ALERTA: {n} clientes en hipotecario con capacidad < $2M")

    # Generar reporte en texto
    reporte = (
        f"{'='*70}\n"
        f"REPORTE DE AUDITORÍA — MOTOR DE REGLAS v1.0.0\n"
        f"{'='*70}\n\n"
        f"1. VERIFICACIÓN DE COMPLETITUD\n"
        f"   Total clientes:              {len(df)}\n"
        f"   Sin acción asignada:          {sin_accion}\n"
        f"   Sin regla asignada:           {sin_regla}\n"
        f"   Sin justificación:            {sin_justificacion}\n"
        f"   Estado: {'PASS' if sin_accion == 0 and sin_regla == 0 else 'FAIL'}\n\n"
        f"2. VERIFICACIÓN DE TRAZABILIDAD\n"
        f"   Reglas encontradas:           {sorted(reglas_encontradas)}\n"
        f"   Reglas inválidas:             {sorted(reglas_invalidas) if reglas_invalidas else 'Ninguna'}\n"
        f"   Estado: {'PASS' if not reglas_invalidas else 'FAIL'}\n\n"
        f"3. DISTRIBUCIÓN POR ACCIÓN\n"
    )
    for accion, count in df["accion_sugerida"].value_counts().items():
        pct = count / len(df) * 100
        reporte += f"   {accion:45s} {count:4d}  ({pct:5.1f}%)\n"

    reporte += "\n4. DISTRIBUCIÓN POR REGLA\n"
    for regla in sorted(df["regla_aplicada"].unique()):
        count = len(df[df["regla_aplicada"] == regla])
        nombre = next(
            (r["nombre"] for r in REGLAS if r["codigo"] == regla),
            "Default — Más cupo TC",
        )
        reporte += f"   {regla} — {nombre:45s} {count:4d}\n"

    reporte += "\n5. MÉTRICAS POR ACCIÓN\n"
    for accion, group in df.groupby("accion_sugerida"):
        reporte += (
            f"   {accion}\n"
            f"     Score medio: {group['score_riesgo'].mean():.0f} | "
            f"Ingreso medio: ${group['ingreso_mensual_clp'].mean():,.0f} | "
            f"Saldo medio: ${group['saldo_promedio_clp'].mean():,.0f}\n"
        )

    if alertas:
        reporte += "\n6. ALERTAS DE COHERENCIA\n"
        for alerta in alertas:
            reporte += f"   {alerta}\n"
    else:
        reporte += "\n6. ALERTAS DE COHERENCIA\n   Ninguna alerta detectada.\n"

    reporte += f"\n{'='*70}\n"

    Path(report_filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(report_filepath, "w", encoding="utf-8") as f:
        f.write(reporte)

    return {
        "status": "success",
        "completitud": "PASS" if sin_accion == 0 else "FAIL",
        "trazabilidad": "PASS" if not reglas_invalidas else "FAIL",
        "alertas": alertas if alertas else ["Ninguna alerta detectada"],
        "reporte_guardado": report_filepath,
        "reporte_texto": reporte,
    }
