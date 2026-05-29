import re


def limpiar_rut(rut: str) -> str:
    return re.sub(r'[^0-9kK]', '', rut).upper()


def validar_rut(rut: str) -> bool:
    """Valida un RUT chileno usando módulo 11."""
    rut_limpio = limpiar_rut(rut)
    if len(rut_limpio) < 2:
        return False

    cuerpo = rut_limpio[:-1]
    dv_ingresado = rut_limpio[-1]

    if not cuerpo.isdigit():
        return False

    suma = 0
    multiplo = 2
    for digito in reversed(cuerpo):
        suma += int(digito) * multiplo
        multiplo = multiplo + 1 if multiplo < 7 else 2

    resto = suma % 11
    dv_calculado = str(11 - resto)

    if dv_calculado == '11':
        dv_calculado = '0'
    elif dv_calculado == '10':
        dv_calculado = 'K'

    return dv_ingresado == dv_calculado


def formatear_rut(rut: str) -> str:
    """Formatea RUT: 12.345.678-9"""
    rut_limpio = limpiar_rut(rut)
    if len(rut_limpio) < 2:
        return rut
    cuerpo = rut_limpio[:-1]
    dv = rut_limpio[-1]
    cuerpo_formateado = ''
    for i, d in enumerate(reversed(cuerpo)):
        if i > 0 and i % 3 == 0:
            cuerpo_formateado = '.' + cuerpo_formateado
        cuerpo_formateado = d + cuerpo_formateado
    return f"{cuerpo_formateado}-{dv}"
