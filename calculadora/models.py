from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class InterestRate(models.Model):
    nombre = models.CharField(max_length=100)
    porcentaje = models.FloatField(
        validators=[MinValueValidator(0.1), MaxValueValidator(30.0)],
        help_text="Tasa de interés anual (%)"
    )
    plazo_min_anios = models.IntegerField(default=5, validators=[MinValueValidator(1)])
    plazo_max_anios = models.IntegerField(default=30, validators=[MaxValueValidator(40)])
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tasa de Interés"
        verbose_name_plural = "Tasas de Interés"
        ordering = ['porcentaje']

    def __str__(self):
        return f"{self.nombre} ({self.porcentaje}%)"


class Submission(models.Model):
    nombre_completo = models.CharField(max_length=200, verbose_name="Nombre Completo")
    email = models.EmailField()
    telefono = models.CharField(max_length=20, verbose_name="Teléfono", blank=True, default="")

    valor_propiedad = models.FloatField(verbose_name="Valor Propiedad (UF)", validators=[MinValueValidator(0.01)])
    pie = models.FloatField(verbose_name="Pie (UF)", validators=[MinValueValidator(0)])
    monto_credito = models.FloatField(verbose_name="Monto Crédito (UF)")
    plazo_anios = models.IntegerField(verbose_name="Plazo (años)")
    tasa_interes = models.FloatField(verbose_name="Tasa Interés (%)")
    tasa_interes_nombre = models.CharField(max_length=100, verbose_name="Nombre Tasa")
    renta_bruta_clp = models.FloatField(verbose_name="Renta Bruta Mensual (CLP)", validators=[MinValueValidator(0.01)])
    deudas_vigentes_clp = models.FloatField(verbose_name="Deudas Vigentes Mensuales (CLP)", default=0)
    valor_uf = models.FloatField(verbose_name="Valor UF al momento de evaluación")

    cuota_mensual = models.FloatField(verbose_name="Cuota Mensual (UF)")
    cuota_mensual_clp = models.FloatField(verbose_name="Cuota Mensual (CLP)")
    relacion_cuota_ingreso = models.FloatField(verbose_name="Relación Cuota/Ingreso (%)")
    renta_minima_requerida_clp = models.FloatField(verbose_name="Renta Mínima Requerida (CLP)")
    costo_total_credito = models.FloatField(verbose_name="Costo Total del Crédito (UF)")
    califica = models.BooleanField(verbose_name="¿Califica?")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Evaluación")

    class Meta:
        verbose_name = "Evaluación"
        verbose_name_plural = "Evaluaciones"
        ordering = ['-created_at']

    def __str__(self):
        estado = "Califica" if self.califica else "No Califica"
        return f"{self.nombre_completo} - {estado} ({self.created_at.strftime('%d/%m/%Y')})"


class PdfConfig(models.Model):
    # Colores del formulario público
    form_color_primario = models.CharField(max_length=7, default="#1e3a5f", verbose_name="Color Primario del Formulario",
                                           help_text="Color del encabezado y botón del formulario público")
    form_color_secundario = models.CharField(max_length=7, default="#4a90d9", verbose_name="Color Secundario del Formulario",
                                              help_text="Color de acentos y hover del formulario público")
    form_color_califica = models.CharField(max_length=7, default="#16a34a", verbose_name="Color 'Califica'")
    form_color_no_califica = models.CharField(max_length=7, default="#dc2626", verbose_name="Color 'No Califica'")

    # Configuración del PDF
    logo = models.ImageField(upload_to='pdf/', blank=True, null=True, verbose_name="Logo")
    color_primario = models.CharField(max_length=7, default="#1e3a5f", verbose_name="Color Primario del PDF")
    color_secundario = models.CharField(max_length=7, default="#4a90d9", verbose_name="Color Secundario del PDF")
    header_text = models.CharField(
        max_length=200,
        default="Simulación de Crédito Hipotecario",
        verbose_name="Texto del Encabezado"
    )
    footer_text = models.TextField(
        default="Este documento es una simulación y no constituye una oferta de crédito.",
        verbose_name="Texto del Pie de Página"
    )
    valor_uf = models.FloatField(
        default=38000.00,
        verbose_name="Valor UF actual ($)",
        help_text="Valor de la UF en pesos chilenos. Actualizar periódicamente."
    )
    mostrar_deudas = models.BooleanField(default=True, verbose_name="Mostrar Deudas en PDF")
    mostrar_tabla_amortizacion = models.BooleanField(default=False, verbose_name="Mostrar Tabla de Amortización")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración PDF"
        verbose_name_plural = "Configuración PDF"

    def __str__(self):
        return "Configuración PDF"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
