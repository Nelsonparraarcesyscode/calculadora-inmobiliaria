def factor_anualidad(tasa_anual: float, plazo_anios: int) -> float:
    """Factor de valor presente de una anualidad (amortización francesa).

    monto_credito = cuota_periodica * factor_anualidad
    factor = (1 - (1 + r)^-n) / r   con r = tasa mensual, n = nº de meses.
    """
    if tasa_anual <= 0 or plazo_anios <= 0:
        return 0.0
    r = tasa_anual / 100 / 12
    n = plazo_anios * 12
    return (1 - (1 + r) ** -n) / r


def calcular_capacidad(
    sueldo_liquido_clp: float,
    sueldo_2_clp: float,
    plazo_anios: int,
    tasa_anual: float,
    pie_pct: float,
    valor_uf: float,
    factor_endeudamiento: float = 3.6,
) -> dict:
    """Calcula, a partir del sueldo líquido, el precio máximo de depto que se puede adquirir.

    Reglas de negocio (Peterman):
      - dividendo máximo = (sueldo líquido + sueldo 2) / factor_endeudamiento
      - precio máximo (UF) = dividendo_UF * factor_anualidad(tasa, plazo)
      - financiamiento banco = precio máximo * (1 - pie%)
      - pie / ahorro = precio máximo * pie%
    """
    ingreso_total = (sueldo_liquido_clp or 0) + (sueldo_2_clp or 0)
    pie_frac = (pie_pct or 0) / 100.0

    vacio = {
        'dividendo_clp': 0.0, 'dividendo_uf': 0.0,
        'precio_maximo_uf': 0.0, 'precio_maximo_clp': 0.0,
        'financiamiento_uf': 0.0, 'financiamiento_clp': 0.0,
        'pie_uf': 0.0, 'pie_clp': 0.0,
    }

    if ingreso_total <= 0 or valor_uf <= 0 or factor_endeudamiento <= 0:
        return vacio

    dividendo_clp = ingreso_total / factor_endeudamiento
    dividendo_uf = dividendo_clp / valor_uf

    factor = factor_anualidad(tasa_anual, plazo_anios)
    precio_maximo_uf = dividendo_uf * factor
    if precio_maximo_uf <= 0:
        return vacio

    precio_maximo_clp = precio_maximo_uf * valor_uf
    financiamiento_uf = precio_maximo_uf * (1 - pie_frac)
    pie_uf = precio_maximo_uf * pie_frac

    return {
        'dividendo_clp': round(dividendo_clp),
        'dividendo_uf': round(dividendo_uf, 2),
        'precio_maximo_uf': round(precio_maximo_uf, 2),
        'precio_maximo_clp': round(precio_maximo_clp),
        'financiamiento_uf': round(financiamiento_uf, 2),
        'financiamiento_clp': round(financiamiento_uf * valor_uf),
        'pie_uf': round(pie_uf, 2),
        'pie_clp': round(pie_uf * valor_uf),
    }
