from django.test import TestCase, RequestFactory
from django.test import override_settings

from .forms import CalculadoraForm
from .models import InterestRate, PdfConfig
from .utils.calculations import calcular_cuota_mensual, evaluar_credito
from .utils.rut_validator import validar_rut, formatear_rut


class CalcularCuotaMensualTests(TestCase):
    """Tests para la función de amortización francesa."""

    def test_cuota_normal(self):
        # 2400 UF, 5% anual, 20 años → cuota esperada ≈ 15.84 UF
        cuota = calcular_cuota_mensual(2400, 5.0, 20)
        self.assertAlmostEqual(cuota, 15.8389, places=2)

    def test_monto_cero(self):
        self.assertEqual(calcular_cuota_mensual(0, 5.0, 20), 0.0)

    def test_tasa_cero(self):
        self.assertEqual(calcular_cuota_mensual(2400, 0, 20), 0.0)

    def test_plazo_cero(self):
        self.assertEqual(calcular_cuota_mensual(2400, 5.0, 0), 0.0)

    def test_monto_negativo(self):
        self.assertEqual(calcular_cuota_mensual(-100, 5.0, 20), 0.0)


class EvaluarCreditoTests(TestCase):
    """Tests para la evaluación completa de crédito."""

    def test_califica_renta_alta(self):
        result = evaluar_credito(
            valor_propiedad=3000,
            pie=600,
            plazo_anios=20,
            tasa_anual=5.0,
            renta_bruta_clp=3000000,
            deudas_vigentes_clp=0,
            valor_uf=38000,
        )
        self.assertTrue(result['califica'])
        self.assertGreater(result['monto_credito'], 0)
        self.assertGreater(result['cuota_mensual'], 0)

    def test_no_califica_renta_baja(self):
        result = evaluar_credito(
            valor_propiedad=3000,
            pie=600,
            plazo_anios=20,
            tasa_anual=5.0,
            renta_bruta_clp=500000,
            deudas_vigentes_clp=0,
            valor_uf=38000,
        )
        self.assertFalse(result['califica'])
        self.assertGreater(result['relacion_cuota_ingreso'], 25.0)

    def test_pie_mayor_que_propiedad_no_califica(self):
        """Bug fix: pie > valor_propiedad debería retornar califica=False."""
        result = evaluar_credito(
            valor_propiedad=1000,
            pie=1200,
            plazo_anios=20,
            tasa_anual=5.0,
            renta_bruta_clp=2000000,
            deudas_vigentes_clp=0,
            valor_uf=38000,
        )
        self.assertFalse(result['califica'])
        self.assertEqual(result['monto_credito'], 0)

    def test_pie_igual_propiedad_no_califica(self):
        result = evaluar_credito(
            valor_propiedad=1000,
            pie=1000,
            plazo_anios=20,
            tasa_anual=5.0,
            renta_bruta_clp=2000000,
            deudas_vigentes_clp=0,
            valor_uf=38000,
        )
        self.assertFalse(result['califica'])

    def test_renta_cero_no_califica(self):
        result = evaluar_credito(
            valor_propiedad=3000,
            pie=600,
            plazo_anios=20,
            tasa_anual=5.0,
            renta_bruta_clp=0,
            deudas_vigentes_clp=0,
            valor_uf=38000,
        )
        self.assertFalse(result['califica'])
        self.assertEqual(result['relacion_cuota_ingreso'], 100.0)

    def test_deudas_afectan_calificacion(self):
        # Sin deudas califica
        r1 = evaluar_credito(
            valor_propiedad=2000, pie=400, plazo_anios=20,
            tasa_anual=5.0, renta_bruta_clp=2000000,
            deudas_vigentes_clp=0, valor_uf=38000,
        )
        # Con deudas altas no califica
        r2 = evaluar_credito(
            valor_propiedad=2000, pie=400, plazo_anios=20,
            tasa_anual=5.0, renta_bruta_clp=2000000,
            deudas_vigentes_clp=1000000, valor_uf=38000,
        )
        self.assertGreater(r2['relacion_cuota_ingreso'], r1['relacion_cuota_ingreso'])


class FormValidationTests(TestCase):
    """Tests para validación del formulario."""

    @classmethod
    def setUpTestData(cls):
        cls.tasa = InterestRate.objects.create(
            nombre="Test", porcentaje=5.0,
            plazo_min_anios=5, plazo_max_anios=30, activa=True
        )

    def _form_data(self, **overrides):
        data = {
            'nombre_completo': 'Juan Pérez',
            'email': 'juan@ejemplo.cl',
            'telefono': '+56912345678',
            'valor_propiedad': 3000,
            'pie': 600,
            'plazo_anios': '20',
            'tasa_interes_id': str(self.tasa.id),
            'renta_bruta_clp': 2000000,
            'deudas_vigentes_clp': 0,
        }
        data.update(overrides)
        return data

    def test_form_valido(self):
        tasas = InterestRate.objects.filter(activa=True)
        form = CalculadoraForm(self._form_data(), tasas=tasas)
        self.assertTrue(form.is_valid())

    def test_form_pie_mayor_que_propiedad(self):
        tasas = InterestRate.objects.filter(activa=True)
        form = CalculadoraForm(self._form_data(pie=3500), tasas=tasas)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_form_pie_igual_que_propiedad(self):
        tasas = InterestRate.objects.filter(activa=True)
        form = CalculadoraForm(self._form_data(pie=3000), tasas=tasas)
        self.assertFalse(form.is_valid())

    def test_form_valor_propiedad_negativo(self):
        tasas = InterestRate.objects.filter(activa=True)
        form = CalculadoraForm(self._form_data(valor_propiedad=-100), tasas=tasas)
        self.assertFalse(form.is_valid())

    def test_form_deudas_vacia_se_convierte_a_cero(self):
        tasas = InterestRate.objects.filter(activa=True)
        form = CalculadoraForm(
            self._form_data(deudas_vigentes_clp=''), tasas=tasas
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['deudas_vigentes_clp'], 0)


class RutValidatorTests(TestCase):
    """Tests para validación de RUT chileno."""

    def test_rut_valido(self):
        self.assertTrue(validar_rut('12.345.678-5'))

    def test_rut_valido_sin_formato(self):
        self.assertTrue(validar_rut('123456785'))

    def test_rut_invalido(self):
        self.assertFalse(validar_rut('12.345.678-0'))

    def test_rut_corto(self):
        self.assertFalse(validar_rut('1'))

    def test_formatear_rut(self):
        self.assertEqual(formatear_rut('123456785'), '12.345.678-5')


class ViewIntegrationTests(TestCase):
    """Tests de integración para la vista principal."""

    @classmethod
    def setUpTestData(cls):
        cls.tasa = InterestRate.objects.create(
            nombre="Fija", porcentaje=4.5,
            plazo_min_anios=5, plazo_max_anios=30, activa=True
        )
        PdfConfig.objects.get_or_create(pk=1)

    def test_get_form(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Simulador de Crédito Hipotecario')

    def test_post_valid_returns_pdf(self):
        response = self.client.post('/', {
            'nombre_completo': 'María López',
            'email': 'maria@test.cl',
            'valor_propiedad': 3000,
            'pie': 600,
            'plazo_anios': '20',
            'tasa_interes_id': str(self.tasa.id),
            'renta_bruta_clp': 2000000,
            'deudas_vigentes_clp': 0,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_post_pie_mayor_que_propiedad_shows_error(self):
        response = self.client.post('/', {
            'nombre_completo': 'Test User',
            'email': 'test@test.cl',
            'valor_propiedad': 1000,
            'pie': 1500,
            'plazo_anios': '20',
            'tasa_interes_id': str(self.tasa.id),
            'renta_bruta_clp': 2000000,
            'deudas_vigentes_clp': 0,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'El pie debe ser menor al valor de la propiedad')

    def test_rates_json_endpoint(self):
        response = self.client.get('/api/rates/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['nombre'], 'Fija')
