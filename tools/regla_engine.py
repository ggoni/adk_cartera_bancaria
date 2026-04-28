"""
================================================================================
MOTOR DE REGLAS DETERMINISTA
================================================================================

Catálogo de 7 reglas con evaluación por prioridad jerárquica.
Módulo independiente de cualquier framework de agentes.

Prioridad: R01 > R02 > R03 > R04 > R05 > R06 > R07 (default)
================================================================================
"""

import pandas as pd


REGLAS = [
    {
        "codigo": "R01",
        "nombre": "Inversor activo de alto patrimonio",
        "accion": "Banca de inversión",
        "condicion": lambda r: (
            r["segmento"] in ("premium", "select")
            and r["tiene_inversion"] == True
            and r["saldo_promedio_clp"] > 2_000_000
            and r["score_riesgo"] > 550
        ),
        "justificacion": lambda r: (
            f"[R01] Cliente {r['segmento']} con inversiones activas y saldo "
            f"promedio de ${r['saldo_promedio_clp']:,.0f}. Score {r['score_riesgo']}. "
            f"Perfil sofisticado apto para ampliar diversificación."
        ),
    },
    {
        "codigo": "R02",
        "nombre": "Premium con patrimonio líquido sin inversión",
        "accion": "Banca de inversión",
        "condicion": lambda r: (
            r["segmento"] == "premium"
            and r["tiene_inversion"] == False
            and r["saldo_promedio_clp"] > 8_000_000
            and r["score_riesgo"] > 700
        ),
        "justificacion": lambda r: (
            f"[R02] Cliente premium con saldo líquido de ${r['saldo_promedio_clp']:,.0f} "
            f"sin inversiones. Score {r['score_riesgo']}. Oportunidad de captura patrimonial."
        ),
    },
    {
        "codigo": "R03",
        "nombre": "Alto ingreso y saldo sin inversión",
        "accion": "Banca de inversión",
        "condicion": lambda r: (
            r["tiene_inversion"] == False
            and r["ingreso_mensual_clp"] > 5_000_000
            and r["saldo_promedio_clp"] > 5_000_000
            and r["score_riesgo"] > 600
        ),
        "justificacion": lambda r: (
            f"[R03] Ingreso de ${r['ingreso_mensual_clp']:,.0f} con saldo de "
            f"${r['saldo_promedio_clp']:,.0f} sin inversiones. "
            f"Candidato a asesoría patrimonial."
        ),
    },
    {
        "codigo": "R04",
        "nombre": "Alta capacidad con estabilidad demostrada",
        "accion": "Ofrecer hipotecario",
        "condicion": lambda r: (
            r["monto_preaprobado_credito_clp"] > 5_000_000
            and r["score_riesgo"] > 500
            and r["ingreso_mensual_clp"] > 2_000_000
            and r["antiguedad_cliente_meses"] > 60
            and r["capacidad_endeudamiento_clp"] > 4_000_000
        ),
        "justificacion": lambda r: (
            f"[R04] Preaprobado ${r['monto_preaprobado_credito_clp']:,.0f}, "
            f"capacidad ${r['capacidad_endeudamiento_clp']:,.0f}, "
            f"ingreso ${r['ingreso_mensual_clp']:,.0f}, "
            f"{r['antiguedad_cliente_meses']} meses de antigüedad. "
            f"Perfil estable para hipotecario."
            + (" Abona sueldo." if r["abona_sueldo"] else "")
        ),
    },
    {
        "codigo": "R05",
        "nombre": "Select/Premium joven sin consumo vigente",
        "accion": "Ofrecer hipotecario",
        "condicion": lambda r: (
            r["segmento"] in ("select", "premium")
            and r["capacidad_endeudamiento_clp"] > 3_000_000
            and r["score_riesgo"] > 550
            and 28 <= r["edad"] <= 55
            and r["tiene_credito_consumo"] == False
        ),
        "justificacion": lambda r: (
            f"[R05] Segmento {r['segmento']} sin consumo, capacidad "
            f"${r['capacidad_endeudamiento_clp']:,.0f}, edad {r['edad']}. "
            f"Compatible con adquisición de vivienda."
        ),
    },
    {
        "codigo": "R06",
        "nombre": "Masivo estable con alta capacidad",
        "accion": "Ofrecer hipotecario",
        "condicion": lambda r: (
            r["segmento"] == "masivo"
            and r["ingreso_mensual_clp"] > 1_500_000
            and r["capacidad_endeudamiento_clp"] > 3_500_000
            and r["score_riesgo"] > 450
            and r["antiguedad_cliente_meses"] > 90
            and r["abona_sueldo"] == True
            and r["tiene_credito_consumo"] == False
        ),
        "justificacion": lambda r: (
            f"[R06] Masivo con ingreso ${r['ingreso_mensual_clp']:,.0f}, "
            f"capacidad ${r['capacidad_endeudamiento_clp']:,.0f}, "
            f"{r['antiguedad_cliente_meses']} meses. Abona sueldo, sin consumo."
        ),
    },
]


def _justificacion_default(r: pd.Series) -> str:
    partes = ["[R07]"]
    if r["tiene_tarjeta_credito"] and r["monto_preaprobado_tc_clp"] > 300_000:
        partes.append(f"TC activa con ${r['monto_preaprobado_tc_clp']:,.0f} preaprobados.")
    elif not r["tiene_tarjeta_credito"] and r["monto_preaprobado_tc_clp"] > 200_000:
        partes.append(f"Sin TC pero ${r['monto_preaprobado_tc_clp']:,.0f} preaprobados.")
    else:
        partes.append(f"Preaprobado TC ${r['monto_preaprobado_tc_clp']:,.0f}.")
    if r["n_transacciones_mes"] > 15:
        partes.append(f"{r['n_transacciones_mes']} txn/mes.")
    if r["usa_tc_otro_banco"]:
        partes.append("Usa TC en otro banco.")
    if r["abona_sueldo"]:
        partes.append("Abona sueldo.")
    if r["score_riesgo"] > 400:
        partes.append(f"Score {r['score_riesgo']} aceptable.")
    else:
        partes.append(f"Score {r['score_riesgo']}, cupo conservador.")
    return " ".join(partes)


def evaluar_cliente(row: pd.Series) -> tuple[str, str, str]:
    """Evalúa un cliente contra el catálogo. Retorna (accion, codigo, justificacion)."""
    for regla in REGLAS:
        if regla["condicion"](row):
            return regla["accion"], regla["codigo"], regla["justificacion"](row)
    return "Más cupo en tarjeta de crédito", "R07", _justificacion_default(row)


def ejecutar_motor(df: pd.DataFrame) -> pd.DataFrame:
    """Ejecuta el motor sobre un DataFrame completo."""
    resultados = df.apply(evaluar_cliente, axis=1, result_type="expand")
    df = df.copy()
    df["accion_sugerida"] = resultados[0]
    df["regla_aplicada"] = resultados[1]
    df["justificacion"] = resultados[2]
    return df
