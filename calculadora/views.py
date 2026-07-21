import json
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_GET

from .forms import CalculadoraForm
from .models import InterestRate, Submission, Propiedad, PdfConfig
from .utils.calculations import calcular_capacidad

# Máximo de evaluaciones guardadas por IP por hora (anti-spam de leads).
MAX_ENVIOS_POR_HORA = 15


def _client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


@xframe_options_exempt
def calculadora_view(request):
    tasas = InterestRate.objects.filter(activa=True)
    config = PdfConfig.load()

    resultado = None
    propiedades = []
    submission = None
    financiamiento_pct = None

    if request.method == 'POST':
        form = CalculadoraForm(request.POST, tasas=tasas)
        if form.is_valid():
            data = form.cleaned_data
            throttle_key = f'calc-envios-{_client_ip(request)}'
            envios = cache.get(throttle_key, 0)
            # La tasa pudo desactivarse entre cargar y enviar el formulario.
            tasa = tasas.filter(id=data['tasa_interes_id']).first()

            if envios >= MAX_ENVIOS_POR_HORA:
                form.add_error(
                    None, 'Has realizado demasiadas simulaciones en poco tiempo. '
                          'Intenta nuevamente en una hora.')
            elif tasa is None:
                form.add_error(
                    'tasa_interes_id',
                    'La tasa seleccionada ya no está disponible. Recarga la página.')
            else:
                resultado = calcular_capacidad(
                    sueldo_liquido_clp=data['sueldo_liquido_clp'],
                    sueldo_2_clp=data['sueldo_2_clp'],
                    plazo_anios=int(data['plazo_anios']),
                    tasa_anual=tasa.porcentaje,
                    pie_pct=float(data['pie_pct']),
                    valor_uf=config.valor_uf,
                    factor_endeudamiento=config.factor_endeudamiento,
                )

                propiedades = list(
                    Propiedad.objects.filter(
                        activa=True,
                        precio_uf__lte=resultado['precio_maximo_uf'],
                    )
                )

                submission = Submission.objects.create(
                    nombre_completo=data['nombre_completo'],
                    email=data['email'],
                    telefono=data.get('telefono', ''),
                    sueldo_liquido_clp=data['sueldo_liquido_clp'],
                    complementa_renta=(data.get('complementa_renta') == 'si'),
                    sueldo_2_clp=data['sueldo_2_clp'],
                    plazo_anios=int(data['plazo_anios']),
                    pie_pct=float(data['pie_pct']),
                    tasa_interes=tasa.porcentaje,
                    tasa_interes_nombre=tasa.nombre,
                    valor_uf=config.valor_uf,
                    factor_endeudamiento=config.factor_endeudamiento,
                    dividendo_uf=resultado['dividendo_uf'],
                    dividendo_clp=resultado['dividendo_clp'],
                    precio_maximo_uf=resultado['precio_maximo_uf'],
                    precio_maximo_clp=resultado['precio_maximo_clp'],
                    financiamiento_uf=resultado['financiamiento_uf'],
                    financiamiento_clp=resultado['financiamiento_clp'],
                    pie_uf=resultado['pie_uf'],
                    pie_clp=resultado['pie_clp'],
                    unidades_encontradas=len(propiedades),
                )
                financiamiento_pct = 100 - float(data['pie_pct'])
                cache.set(throttle_key, envios + 1, 60 * 60)
    else:
        form = CalculadoraForm(tasas=tasas)

    tasas_json = json.dumps([
        {'id': t.id, 'nombre': t.nombre, 'porcentaje': t.porcentaje,
         'plazo_min': t.plazo_min_anios, 'plazo_max': t.plazo_max_anios}
        for t in tasas
    ])

    response = render(request, 'calculadora/form.html', {
        'form': form,
        'tasas_json': tasas_json,
        'valor_uf': config.valor_uf,
        'factor_endeudamiento': config.factor_endeudamiento,
        'pie_pct_default': config.pie_pct_default,
        'config': config,
        'resultado': resultado,
        'propiedades': propiedades,
        'submission': submission,
        'financiamiento_pct': financiamiento_pct,
    })
    # Permite el embed SOLO desde los dominios autorizados (anti-clickjacking).
    # X-Frame-Options no soporta lista blanca, por eso la vista está exenta
    # de ese header y el control se hace con CSP frame-ancestors.
    ancestors = ' '.join(["'self'"] + settings.CALC_FRAME_ANCESTORS)
    response['Content-Security-Policy'] = f'frame-ancestors {ancestors}'
    return response


@require_GET
def rates_json(request):
    tasas = InterestRate.objects.filter(activa=True).values(
        'id', 'nombre', 'porcentaje', 'plazo_min_anios', 'plazo_max_anios'
    )
    return JsonResponse(list(tasas), safe=False)
