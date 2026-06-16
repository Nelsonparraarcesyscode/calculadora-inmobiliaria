import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_GET

from .forms import CalculadoraForm
from .models import InterestRate, Submission, Propiedad, PdfConfig
from .utils.calculations import calcular_capacidad


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
            tasa = InterestRate.objects.get(id=data['tasa_interes_id'])

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
    else:
        form = CalculadoraForm(tasas=tasas)

    tasas_json = json.dumps([
        {'id': t.id, 'nombre': t.nombre, 'porcentaje': t.porcentaje,
         'plazo_min': t.plazo_min_anios, 'plazo_max': t.plazo_max_anios}
        for t in tasas
    ])

    return render(request, 'calculadora/form.html', {
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


@require_GET
def rates_json(request):
    tasas = InterestRate.objects.filter(activa=True).values(
        'id', 'nombre', 'porcentaje', 'plazo_min_anios', 'plazo_max_anios'
    )
    return JsonResponse(list(tasas), safe=False)
