import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_GET

from .forms import CalculadoraForm
from .models import InterestRate, Submission, PdfConfig
from .utils.calculations import evaluar_credito
from .utils.pdf_generator import generar_pdf


@xframe_options_exempt
def calculadora_view(request):
    tasas = InterestRate.objects.filter(activa=True)
    pdf_config = PdfConfig.load()

    if request.method == 'POST':
        form = CalculadoraForm(request.POST, tasas=tasas)
        if form.is_valid():
            data = form.cleaned_data
            tasa = InterestRate.objects.get(id=data['tasa_interes_id'])

            resultado = evaluar_credito(
                valor_propiedad=data['valor_propiedad'],
                pie=data['pie'],
                plazo_anios=int(data['plazo_anios']),
                tasa_anual=tasa.porcentaje,
                renta_bruta_clp=data['renta_bruta_clp'],
                deudas_vigentes_clp=data['deudas_vigentes_clp'],
                valor_uf=pdf_config.valor_uf,
            )

            submission = Submission.objects.create(
                nombre_completo=data['nombre_completo'],
                email=data['email'],
                telefono=data.get('telefono', ''),
                valor_propiedad=data['valor_propiedad'],
                pie=data['pie'],
                monto_credito=resultado['monto_credito'],
                plazo_anios=int(data['plazo_anios']),
                tasa_interes=tasa.porcentaje,
                tasa_interes_nombre=tasa.nombre,
                renta_bruta_clp=data['renta_bruta_clp'],
                deudas_vigentes_clp=data['deudas_vigentes_clp'],
                valor_uf=pdf_config.valor_uf,
                cuota_mensual=resultado['cuota_mensual'],
                cuota_mensual_clp=resultado['cuota_mensual_clp'],
                relacion_cuota_ingreso=resultado['relacion_cuota_ingreso'],
                renta_minima_requerida_clp=resultado['renta_minima_requerida_clp'],
                costo_total_credito=resultado['costo_total_credito'],
                califica=resultado['califica'],
            )

            pdf_buffer = generar_pdf(submission, pdf_config)
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="evaluacion_{submission.pk}.pdf"'
            return response
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
        'valor_uf': pdf_config.valor_uf,
        'config': pdf_config,
    })


@require_GET
def rates_json(request):
    tasas = InterestRate.objects.filter(activa=True).values(
        'id', 'nombre', 'porcentaje', 'plazo_min_anios', 'plazo_max_anios'
    )
    return JsonResponse(list(tasas), safe=False)
