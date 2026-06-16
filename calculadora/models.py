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


class Propiedad(models.Model):
    """Unidad disponible (modelo plano). Se filtra contra el precio máximo del usuario."""
    edificio = models.CharField(max_length=200, verbose_name="Edificio / Proyecto")
    comuna = models.CharField(max_length=120, verbose_name="Comuna")
    entrega = models.CharField(max_length=120, default="Entrega Inmediata", verbose_name="Entrega")
    tipologia = models.CharField(max_length=60, verbose_name="Tipología", help_text="Ej: 2D + 1B")

    precio_uf = models.FloatField(
        verbose_name="Precio (UF)", validators=[MinValueValidator(0.01)],
        help_text="Precio de la unidad en UF. Se usa para filtrar contra el presupuesto del cliente."
    )

    superficie_total_m2 = models.FloatField(verbose_name="Superficie Total (m²)", default=0)
    superficie_util_m2 = models.FloatField(verbose_name="Superficie Útil (m²)", default=0)
    superficie_terraza_m2 = models.FloatField(verbose_name="Superficie Terraza (m²)", default=0)

    imagen = models.ImageField(upload_to='propiedades/', blank=True, null=True, verbose_name="Imagen")
    enlace = models.URLField(
        max_length=500, blank=True, default="",
        verbose_name="Enlace (WhatsApp / embudo)",
        help_text="A dónde lleva el botón de la tarjeta (ej: https://wa.me/569...)."
    )

    activa = models.BooleanField(default=True, verbose_name="Activa")
    orden = models.IntegerField(default=0, verbose_name="Orden", help_text="Menor número aparece primero.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Propiedad"
        verbose_name_plural = "Propiedades"
        ordering = ['orden', 'precio_uf']

    def __str__(self):
        return f"{self.edificio} — {self.tipologia} ({self.precio_uf:.0f} UF)"


class Submission(models.Model):
    nombre_completo = models.CharField(max_length=200, verbose_name="Nombre Completo")
    email = models.EmailField()
    telefono = models.CharField(max_length=20, verbose_name="Teléfono", blank=True, default="")

    # Datos ingresados
    sueldo_liquido_clp = models.FloatField(verbose_name="Sueldo Líquido (CLP)", default=0)
    complementa_renta = models.BooleanField(verbose_name="¿Complementa renta?", default=False)
    sueldo_2_clp = models.FloatField(verbose_name="Sueldo Nº2 (CLP)", default=0)
    plazo_anios = models.IntegerField(verbose_name="Plazo (años)", default=0)
    pie_pct = models.FloatField(verbose_name="Pie (%)", default=0)
    tasa_interes = models.FloatField(verbose_name="Tasa Interés (%)", default=0)
    tasa_interes_nombre = models.CharField(max_length=100, verbose_name="Nombre Tasa", blank=True, default="")
    valor_uf = models.FloatField(verbose_name="Valor UF al momento de evaluación", default=0)
    factor_endeudamiento = models.FloatField(verbose_name="Factor de Endeudamiento", default=3.6)

    # Resultados
    dividendo_uf = models.FloatField(verbose_name="Dividendo Mensual (UF)", default=0)
    dividendo_clp = models.FloatField(verbose_name="Dividendo Mensual (CLP)", default=0)
    precio_maximo_uf = models.FloatField(verbose_name="Precio Máximo Depto (UF)", default=0)
    precio_maximo_clp = models.FloatField(verbose_name="Precio Máximo Depto (CLP)", default=0)
    financiamiento_uf = models.FloatField(verbose_name="Financiamiento Banco (UF)", default=0)
    financiamiento_clp = models.FloatField(verbose_name="Financiamiento Banco (CLP)", default=0)
    pie_uf = models.FloatField(verbose_name="Pie / Ahorro (UF)", default=0)
    pie_clp = models.FloatField(verbose_name="Pie / Ahorro (CLP)", default=0)
    unidades_encontradas = models.IntegerField(verbose_name="Unidades Encontradas", default=0)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Evaluación")

    class Meta:
        verbose_name = "Evaluación"
        verbose_name_plural = "Evaluaciones"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nombre_completo} - {self.precio_maximo_uf:.0f} UF ({self.created_at.strftime('%d/%m/%Y')})"


class PdfConfig(models.Model):
    # Colores corporativos del formulario público (paleta Peterman)
    form_color_primario = models.CharField(max_length=7, default="#5D1314", verbose_name="Color Primario",
                                           help_text="Color de títulos, botones y encabezados de tabla.")
    form_color_secundario = models.CharField(max_length=7, default="#A2998F", verbose_name="Color Secundario",
                                              help_text="Color de acentos, bordes y textos de apoyo.")
    form_color_fondo = models.CharField(max_length=7, default="#FDEFD6", verbose_name="Color de Fondo",
                                        help_text="Fondo crema de las tarjetas/secciones.")
    form_color_califica = models.CharField(max_length=7, default="#16a34a", verbose_name="Color 'Califica'")
    form_color_no_califica = models.CharField(max_length=7, default="#dc2626", verbose_name="Color 'No Califica'")

    logo = models.ImageField(upload_to='pdf/', blank=True, null=True, verbose_name="Logo")

    # Parámetros de negocio
    valor_uf = models.FloatField(
        default=38000.00,
        verbose_name="Valor UF actual ($)",
        help_text="Valor de la UF en pesos chilenos. Actualizar periódicamente (fuente: SII.cl)."
    )
    factor_endeudamiento = models.FloatField(
        default=3.6,
        verbose_name="Factor de Endeudamiento",
        validators=[MinValueValidator(1.0)],
        help_text="El dividendo máximo = sueldo líquido / este factor. Por defecto 3,6 (≈27,8% del sueldo)."
    )
    pie_pct_default = models.FloatField(
        default=10.0,
        verbose_name="Pie por defecto (%)",
        help_text="Porcentaje de pie preseleccionado en la calculadora."
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración"
        verbose_name_plural = "Configuración"

    def __str__(self):
        return "Configuración"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
