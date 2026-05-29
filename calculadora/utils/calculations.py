def calcular_cuota_mensual(monto: float, tasa_anual: float, plazo_anios: int) -> float:
    """Amortización francesa: cuota fija mensual en UF."""
    if monto <= 0 or tasa_anual <= 0 or plazo_anios <= 0:
        return 0.0
    r = tasa_anual / 100 / 12
    n = plazo_anios * 12
    cuota = monto * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    return round(cuota, 4)


def evaluar_credito(
    valor_propiedad: float,
    pie: float,
    plazo_anios: int,
    tasa_anual: float,
    renta_bruta_clp: float,
    deudas_vigentes_clp: float,
    valor_uf: float,
) -> dict:
    monto_credito = valor_propiedad - pie
    if monto_credito <= 0:
        return {
            'monto_credito': 0,
            'cuota_mensual': 0.0,
            'cuota_mensual_clp': 0,
            'relacion_cuota_ingreso': 0.0,
            'renta_minima_requerida_clp': 0,
            'costo_total_credito': 0.0,
            'califica': False,
        }
    cuota_uf = calcular_cuota_mensual(monto_credito, tasa_anual, plazo_anios)
    cuota_clp = round(cuota_uf * valor_uf)

    carga_total_clp = cuota_clp + deudas_vigentes_clp
    relacion = round(carga_total_clp / renta_bruta_clp * 100, 2) if renta_bruta_clp > 0 else 100.0
    califica = relacion <= 25.0

    renta_minima_clp = round(carga_total_clp / 0.25)
    costo_total = round(cuota_uf * plazo_anios * 12, 4)

    return {
        'monto_credito': round(monto_credito, 4),
        'cuota_mensual': cuota_uf,
        'cuota_mensual_clp': cuota_clp,
        'relacion_cuota_ingreso': relacion,
        'renta_minima_requerida_clp': renta_minima_clp,
        'costo_total_credito': costo_total,
        'califica': califica,
    }
