import csv
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, reverse
from django.utils.html import format_html
from .models import Submission, InterestRate, PdfConfig


def exportar_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="evaluaciones.csv"'
    response.write('﻿')
    writer = csv.writer(response)
    writer.writerow([
        'Fecha', 'Nombre', 'Email', 'Teléfono',
        'Valor Propiedad (UF)', 'Pie (UF)', 'Monto Crédito (UF)',
        'Plazo (años)', 'Tasa (%)', 'Renta Bruta (CLP)', 'Deudas (CLP)',
        'Cuota Mensual (UF)', 'Cuota Mensual (CLP)',
        'Relación Cuota/Ingreso (%)', 'Califica'
    ])
    for s in queryset:
        writer.writerow([
            s.created_at.strftime('%d/%m/%Y %H:%M'),
            s.nombre_completo, s.email, s.telefono,
            s.valor_propiedad, s.pie, s.monto_credito,
            s.plazo_anios, s.tasa_interes, s.renta_bruta_clp, s.deudas_vigentes_clp,
            s.cuota_mensual, s.cuota_mensual_clp,
            s.relacion_cuota_ingreso,
            'Sí' if s.califica else 'No'
        ])
    return response

exportar_csv.short_description = "Exportar seleccionados a CSV"


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['nombre_completo', 'email', 'valor_propiedad',
                    'cuota_display', 'relacion_cuota_ingreso',
                    'estado_califica', 'created_at', 'acciones']
    list_filter = ['califica', 'created_at', 'plazo_anios']
    search_fields = ['nombre_completo', 'email']
    readonly_fields = [
        'nombre_completo', 'email', 'telefono',
        'valor_propiedad', 'pie', 'monto_credito', 'plazo_anios',
        'tasa_interes', 'tasa_interes_nombre',
        'renta_bruta_clp', 'deudas_vigentes_clp', 'valor_uf',
        'cuota_mensual', 'cuota_mensual_clp',
        'relacion_cuota_ingreso', 'renta_minima_requerida_clp',
        'costo_total_credito', 'califica', 'created_at', 'pdf_preview_panel'
    ]
    actions = [exportar_csv]
    list_per_page = 25

    fieldsets = (
        ('Datos de Contacto', {
            'fields': ('nombre_completo', 'email', 'telefono')
        }),
        ('Datos del Crédito', {
            'fields': ('valor_propiedad', 'pie', 'monto_credito', 'plazo_anios',
                       'tasa_interes', 'tasa_interes_nombre',
                       'renta_bruta_clp', 'deudas_vigentes_clp', 'valor_uf')
        }),
        ('Resultado', {
            'fields': ('cuota_mensual', 'cuota_mensual_clp',
                       'relacion_cuota_ingreso', 'renta_minima_requerida_clp',
                       'costo_total_credito', 'califica', 'created_at')
        }),
        ('Vista Previa del PDF', {
            'fields': ('pdf_preview_panel',),
            'classes': ('wide',),
        }),
    )

    def cuota_display(self, obj):
        return f"{obj.cuota_mensual:.2f} UF (${obj.cuota_mensual_clp:,.0f})"
    cuota_display.short_description = "Cuota Mensual"

    def estado_califica(self, obj):
        if obj.califica:
            return format_html('<span style="color:#16a34a;font-weight:700;">&#10004; Califica</span>')
        return format_html('<span style="color:#dc2626;font-weight:700;">&#10008; No Califica</span>')
    estado_califica.short_description = "Estado"

    def acciones(self, obj):
        preview_url = reverse('admin:calculadora_submission_preview_pdf', args=[obj.pk])
        download_url = reverse('admin:calculadora_submission_download_pdf', args=[obj.pk])
        return format_html(
            '<a class="btn-preview-pdf" href="{}" target="_blank" style="margin-right:6px;">&#128065; Ver PDF</a>'
            '<a class="btn-preview-pdf" href="{}" style="background:#270164;">&#11015; Descargar</a>',
            preview_url, download_url
        )
    acciones.short_description = "Acciones"

    def pdf_preview_panel(self, obj):
        if not obj.pk:
            return "Guarde primero para ver la vista previa."
        preview_url = reverse('admin:calculadora_submission_preview_pdf', args=[obj.pk])
        return format_html(
            '<div class="pdf-preview-container">'
            '<h3>&#128196; Así se verá el PDF que descarga el usuario</h3>'
            '<iframe src="{}"></iframe>'
            '</div>',
            preview_url
        )
    pdf_preview_panel.short_description = "Vista Previa"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/preview-pdf/',
                 self.admin_site.admin_view(self.preview_pdf_view),
                 name='calculadora_submission_preview_pdf'),
            path('<int:pk>/download-pdf/',
                 self.admin_site.admin_view(self.download_pdf_view),
                 name='calculadora_submission_download_pdf'),
        ]
        return custom_urls + urls

    def preview_pdf_view(self, request, pk):
        from .utils.pdf_generator import generar_pdf
        submission = Submission.objects.get(pk=pk)
        pdf_config = PdfConfig.load()
        pdf_buffer = generar_pdf(submission, pdf_config)
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="preview_{submission.pk}.pdf"'
        return response

    def download_pdf_view(self, request, pk):
        from .utils.pdf_generator import generar_pdf
        submission = Submission.objects.get(pk=pk)
        pdf_config = PdfConfig.load()
        pdf_buffer = generar_pdf(submission, pdf_config)
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="evaluacion_{submission.pk}.pdf"'
        return response

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


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
    list_display = ['__str__', 'valor_uf_display', 'updated_at']
    fieldsets = (
        ('Colores del Formulario Público', {
            'description': 'Estos colores se aplican al formulario que ven los usuarios (y en iframe de WordPress).',
            'fields': ('form_color_primario', 'form_color_secundario',
                       'form_color_califica', 'form_color_no_califica')
        }),
        ('Colores del PDF', {
            'description': 'Estos colores se aplican al documento PDF que se descarga.',
            'fields': ('logo', 'color_primario', 'color_secundario')
        }),
        ('Textos del PDF', {
            'fields': ('header_text', 'footer_text')
        }),
        ('Valor UF', {
            'fields': ('valor_uf',),
            'description': 'El valor de la UF se usa para convertir la cuota mensual (UF) a pesos chilenos.'
        }),
        ('Opciones de Contenido del PDF', {
            'fields': ('mostrar_deudas', 'mostrar_tabla_amortizacion')
        }),
    )

    def valor_uf_display(self, obj):
        return f"${obj.valor_uf:,.0f}"
    valor_uf_display.short_description = "Valor UF"

    def has_add_permission(self, request):
        return not PdfConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
