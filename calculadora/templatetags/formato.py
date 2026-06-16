from django import template

register = template.Library()


@register.filter
def miles(value, decimales=0):
    """Formatea un número al estilo chileno: miles con '.' y decimal con ','.

    Uso: {{ valor|miles }}  ->  250.770.815
         {{ valor|miles:2 }} ->  6.149,02
    """
    if value is None or value == '':
        return ''
    try:
        dec = int(decimales)
        num = float(value)
    except (ValueError, TypeError):
        return value
    # Formato US "1,234,567.89" y luego se intercambian los separadores.
    s = f"{num:,.{dec}f}"
    return s.replace(',', '§').replace('.', ',').replace('§', '.')
