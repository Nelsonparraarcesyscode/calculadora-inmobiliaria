import csv
import io
import json
from django.contrib import admin, messages
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.html import format_html
from django.views.decorators.http import require_POST
from .models import Submission, InterestRate, Propiedad, PdfConfig


# Columnas del CSV de propiedades (sin imágenes).
PROPIEDAD_CSV_FIELDS = [
    'id', 'edificio', 'comuna', 'entrega', 'tipologia', 'precio_uf',
    'superficie_total_m2', 'superficie_util_m2', 'superficie_terraza_m2',
    'enlace', 'activa', 'orden',
]


def _parse_num(value):
    """Acepta '2.160', '2160', '1.234.567', '42,33' o '42.33' y devuelve float.

    Reglas de desambiguación (formato chileno vs estándar):
      - Si hay coma -> la coma es el decimal y los puntos son miles. ('1.234,5' -> 1234.5)
      - Sólo puntos: 2+ puntos -> todos son miles. ('1.234.567' -> 1234567)
        1 punto con 3 dígitos tras él -> es separador de miles. ('2.160' -> 2160)
        1 punto con otra cantidad de dígitos -> es decimal. ('42.33' -> 42.33, '2160.0' -> 2160)
    """
    s = str(value).strip()
    if s == '':
        return 0.0
    if ',' in s:
        return float(s.replace('.', '').replace(',', '.'))
    if s.count('.') > 1:
        return float(s.replace('.', ''))
    if s.count('.') == 1:
        entero, frac = s.split('.')
        if len(frac) == 3:  # patrón de miles: 2.160
            return float(entero + frac)
    return float(s)


def _parse_bool(value):
    return str(value).strip().lower() in ('1', 'true', 'si', 'sí', 'yes', 'x', 'activa')


def exportar_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="evaluaciones.csv"'
    response.write('﻿')
    writer = csv.writer(response)
    writer.writerow([
        'Fecha', 'Nombre', 'Email', 'Teléfono',
        'Sueldo Líquido (CLP)', 'Complementa', 'Sueldo 2 (CLP)',
        'Plazo (años)', 'Pie (%)', 'Tasa (%)',
        'Precio Máximo (UF)', 'Precio Máximo (CLP)',
        'Financiamiento (UF)', 'Pie (UF)', 'Dividendo (UF)', 'Dividendo (CLP)',
        'Unidades Encontradas'
    ])
    for s in queryset:
        writer.writerow([
            s.created_at.strftime('%d/%m/%Y %H:%M'),
            s.nombre_completo, s.email, s.telefono,
            s.sueldo_liquido_clp, 'Sí' if s.complementa_renta else 'No', s.sueldo_2_clp,
            s.plazo_anios, s.pie_pct, s.tasa_interes,
            s.precio_maximo_uf, s.precio_maximo_clp,
            s.financiamiento_uf, s.pie_uf, s.dividendo_uf, s.dividendo_clp,
            s.unidades_encontradas
        ])
    return response

exportar_csv.short_description = "Exportar seleccionados a CSV"


def exportar_propiedades_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="propiedades.csv"'
    response.write('﻿')  # BOM para Excel
    writer = csv.writer(response)
    writer.writerow(PROPIEDAD_CSV_FIELDS)
    for p in queryset:
        writer.writerow([
            p.id, p.edificio, p.comuna, p.entrega, p.tipologia, p.precio_uf,
            p.superficie_total_m2, p.superficie_util_m2, p.superficie_terraza_m2,
            p.enlace, 'si' if p.activa else 'no', p.orden,
        ])
    return response

exportar_propiedades_csv.short_description = "Exportar seleccionadas a CSV (sin imágenes)"


@admin.register(Propiedad)
class PropiedadAdmin(admin.ModelAdmin):
    list_display = ['miniatura', 'edificio', 'tipologia', 'comuna',
                    'precio_uf', 'superficie_total_m2', 'activa', 'orden']
    list_editable = ['precio_uf', 'activa', 'orden']
    list_filter = ['activa', 'comuna', 'entrega']
    search_fields = ['edificio', 'comuna', 'tipologia']
    list_per_page = 30
    actions = [exportar_propiedades_csv]
    change_list_template = 'admin/calculadora/propiedad/change_list.html'

    fieldsets = (
        ('Proyecto', {
            'fields': ('edificio', 'comuna', 'entrega', 'tipologia', 'precio_uf')
        }),
        ('Superficies (m²)', {
            'fields': ('superficie_total_m2', 'superficie_util_m2', 'superficie_terraza_m2')
        }),
        ('Imagen y enlace', {
            'fields': ('imagen', 'enlace')
        }),
        ('Publicación', {
            'fields': ('activa', 'orden')
        }),
    )

    def miniatura(self, obj):
        if obj.imagen:
            return format_html(
                '<img src="{}" style="height:42px;width:60px;object-fit:cover;border-radius:4px;" />',
                obj.imagen.url
            )
        return "—"
    miniatura.short_description = "Imagen"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('importar-csv/', self.admin_site.admin_view(self.importar_csv_view),
                 name='calculadora_propiedad_importar_csv'),
            path('exportar-csv/', self.admin_site.admin_view(self.exportar_todo_csv_view),
                 name='calculadora_propiedad_exportar_csv'),
        ]
        return custom + urls

    def exportar_todo_csv_view(self, request):
        return exportar_propiedades_csv(self, request, Propiedad.objects.all())

    def importar_csv_view(self, request):
        if request.method == 'POST':
            archivo = request.FILES.get('archivo_csv')
            if not archivo:
                self.message_user(request, "Debes seleccionar un archivo CSV.", level=messages.ERROR)
                return redirect('..')
            try:
                texto = archivo.read().decode('utf-8-sig')
            except UnicodeDecodeError:
                texto = archivo.read().decode('latin-1')
            reader = csv.DictReader(io.StringIO(texto))

            creadas, actualizadas, errores = 0, 0, []
            for i, row in enumerate(reader, start=2):
                try:
                    campos = {
                        'edificio': (row.get('edificio') or '').strip(),
                        'comuna': (row.get('comuna') or '').strip(),
                        'entrega': (row.get('entrega') or 'Entrega Inmediata').strip(),
                        'tipologia': (row.get('tipologia') or '').strip(),
                        'precio_uf': _parse_num(row.get('precio_uf')),
                        'superficie_total_m2': _parse_num(row.get('superficie_total_m2')),
                        'superficie_util_m2': _parse_num(row.get('superficie_util_m2')),
                        'superficie_terraza_m2': _parse_num(row.get('superficie_terraza_m2')),
                        'enlace': (row.get('enlace') or '').strip(),
                        'activa': _parse_bool(row.get('activa') or 'si'),
                        'orden': int(_parse_num(row.get('orden') or 0)),
                    }
                    if not campos['edificio'] or not campos['tipologia']:
                        raise ValueError("faltan 'edificio' o 'tipologia'")

                    pk = (row.get('id') or '').strip()
                    if pk and Propiedad.objects.filter(pk=pk).exists():
                        Propiedad.objects.filter(pk=pk).update(**campos)
                        actualizadas += 1
                    else:
                        Propiedad.objects.create(**campos)
                        creadas += 1
                except Exception as e:
                    errores.append(f"Fila {i}: {e}")

            if creadas or actualizadas:
                self.message_user(
                    request,
                    f"Importación completada: {creadas} creada(s), {actualizadas} actualizada(s).",
                    level=messages.SUCCESS,
                )
            for err in errores[:10]:
                self.message_user(request, err, level=messages.WARNING)
            if len(errores) > 10:
                self.message_user(request, f"... y {len(errores) - 10} error(es) más.", level=messages.WARNING)
            if not creadas and not actualizadas and not errores:
                self.message_user(request, "El archivo no contenía filas válidas.", level=messages.WARNING)
            return redirect('..')

        return render(request, 'admin/calculadora/propiedad/importar_csv.html', {
            'title': 'Importar propiedades desde CSV',
            'campos': PROPIEDAD_CSV_FIELDS,
            'opts': self.model._meta,
        })


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['nombre_completo', 'email', 'estado_badge', 'sueldo_display',
                    'precio_maximo_display', 'unidades_encontradas', 'created_at']
    list_filter = ['estado', 'created_at', 'plazo_anios', 'complementa_renta']
    change_list_template = 'admin/calculadora/submission/change_list.html'
    search_fields = ['nombre_completo', 'email']
    readonly_fields = [
        'nombre_completo', 'email', 'telefono',
        'sueldo_liquido_clp', 'complementa_renta', 'sueldo_2_clp',
        'plazo_anios', 'pie_pct', 'tasa_interes', 'tasa_interes_nombre',
        'valor_uf', 'factor_endeudamiento',
        'dividendo_uf', 'dividendo_clp',
        'precio_maximo_uf', 'precio_maximo_clp',
        'financiamiento_uf', 'financiamiento_clp',
        'pie_uf', 'pie_clp', 'unidades_encontradas', 'created_at',
    ]
    actions = [exportar_csv]
    list_per_page = 25

    fieldsets = (
        ('Seguimiento', {
            'fields': ('estado',)
        }),
        ('Datos de Contacto', {
            'fields': ('nombre_completo', 'email', 'telefono')
        }),
        ('Datos Ingresados', {
            'fields': ('sueldo_liquido_clp', 'complementa_renta', 'sueldo_2_clp',
                       'plazo_anios', 'pie_pct', 'tasa_interes', 'tasa_interes_nombre',
                       'valor_uf', 'factor_endeudamiento')
        }),
        ('Resultado', {
            'fields': ('dividendo_uf', 'dividendo_clp',
                       'precio_maximo_uf', 'precio_maximo_clp',
                       'financiamiento_uf', 'financiamiento_clp',
                       'pie_uf', 'pie_clp', 'unidades_encontradas', 'created_at')
        }),
    )

    ESTADO_COLORES = {
        'nuevo': '#2563eb',
        'contactado': '#d97706',
        'calificado': '#7c3aed',
        'ganado': '#16a34a',
        'perdido': '#9ca3af',
    }

    def estado_badge(self, obj):
        color = self.ESTADO_COLORES.get(obj.estado, '#6b7280')
        return format_html(
            '<span style="background:{}18;color:{};border:1px solid {}40;'
            'border-radius:999px;padding:2px 10px;font-weight:700;font-size:11px;">{}</span>',
            color, color, color, obj.get_estado_display()
        )
    estado_badge.short_description = "Estado"
    estado_badge.admin_order_field = 'estado'

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('pipeline/', self.admin_site.admin_view(self.pipeline_view),
                 name='calculadora_submission_pipeline'),
            path('pipeline/mover/', self.admin_site.admin_view(require_POST(self.pipeline_mover_view)),
                 name='calculadora_submission_pipeline_mover'),
        ]
        return custom + urls

    def pipeline_view(self, request):
        columnas = []
        for key, label in Submission.ESTADOS:
            qs = Submission.objects.filter(estado=key)
            columnas.append({
                'key': key,
                'label': label,
                'color': self.ESTADO_COLORES.get(key, '#6b7280'),
                'leads': qs[:200],  # tope defensivo por columna
                'total': qs.count(),
            })
        context = {
            **self.admin_site.each_context(request),
            'title': 'Pipeline de Leads',
            'columnas': columnas,
            'opts': self.model._meta,
            'puede_mover': request.user.has_perm('calculadora.change_submission'),
        }
        return render(request, 'admin/calculadora/submission/pipeline.html', context)

    def pipeline_mover_view(self, request):
        """Cambia el estado de un lead (drag & drop del Kanban)."""
        if not request.user.has_perm('calculadora.change_submission'):
            return JsonResponse({'ok': False, 'error': 'Sin permisos para mover leads.'}, status=403)
        try:
            data = json.loads(request.body)
            lead_id = int(data['id'])
            estado = str(data['estado'])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return HttpResponseBadRequest('Payload inválido')
        if estado not in dict(Submission.ESTADOS):
            return HttpResponseBadRequest('Estado inválido')
        actualizado = Submission.objects.filter(pk=lead_id).update(estado=estado)
        if not actualizado:
            return JsonResponse({'ok': False, 'error': 'El lead ya no existe.'}, status=404)
        return JsonResponse({'ok': True})

    def sueldo_display(self, obj):
        return f"${obj.sueldo_liquido_clp:,.0f}"
    sueldo_display.short_description = "Sueldo Líquido"

    def precio_maximo_display(self, obj):
        return f"{obj.precio_maximo_uf:,.0f} UF (${obj.precio_maximo_clp:,.0f})"
    precio_maximo_display.short_description = "Precio Máximo"

    def has_add_permission(self, request):
        # Los leads solo se crean desde el formulario público, nunca a mano.
        return False

    # has_change_permission queda en el default (permiso de Django): el registro
    # es accesible, pero todos los datos capturados están en readonly_fields, así
    # que en la práctica solo se puede editar 'estado' (workflow del pipeline).


@admin.register(InterestRate)
class InterestRateAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'porcentaje', 'plazo_min_anios', 'plazo_max_anios', 'estado_activa']
    list_filter = ['activa']

    def estado_activa(self, obj):
        if obj.activa:
            return format_html('<span style="color:#16a34a;font-weight:700;">&#9679; Activa</span>')
        return format_html('<span style="color:#999;">&#9675; Inactiva</span>')
    estado_activa.short_description = "Estado"


@admin.register(PdfConfig)
class PdfConfigAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'valor_uf_display', 'factor_endeudamiento', 'updated_at']
    fieldsets = (
        ('Colores corporativos', {
            'description': 'Se aplican al formulario público (y en iframe).',
            'fields': ('form_color_primario', 'form_color_secundario', 'form_color_fondo',
                       'form_color_califica', 'form_color_no_califica', 'logo')
        }),
        ('Parámetros de negocio', {
            'fields': ('valor_uf', 'factor_endeudamiento', 'pie_pct_default'),
            'description': 'Valor UF (fuente SII.cl), factor de endeudamiento y pie por defecto.'
        }),
    )

    def valor_uf_display(self, obj):
        return f"${obj.valor_uf:,.0f}"
    valor_uf_display.short_description = "Valor UF"

    def has_add_permission(self, request):
        return not PdfConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
