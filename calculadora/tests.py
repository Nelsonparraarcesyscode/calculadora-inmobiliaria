from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .admin import _parse_num, _parse_bool
from .forms import CalculadoraForm
from .models import InterestRate, PdfConfig, Propiedad, Submission
from .utils.calculations import factor_anualidad, calcular_capacidad
from .views import MAX_ENVIOS_POR_HORA


class CsvParseTests(TestCase):
    def test_parse_num_chileno_y_estandar(self):
        casos = {'2.160': 2160.0, '2160': 2160.0, '1.234.567': 1234567.0,
                 '42,33': 42.33, '42.33': 42.33, '2160.0': 2160.0,
                 '1.234,5': 1234.5, '': 0.0, '3': 3.0}
        for entrada, esperado in casos.items():
            self.assertAlmostEqual(_parse_num(entrada), esperado, places=4, msg=entrada)

    def test_parse_bool(self):
        self.assertTrue(_parse_bool('si'))
        self.assertTrue(_parse_bool('1'))
        self.assertFalse(_parse_bool('no'))
        self.assertFalse(_parse_bool(''))


class PropiedadCsvAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser('admin', 'a@a.cl', 'admin123')
        cls.prop = Propiedad.objects.create(
            edificio="Existente", comuna="Chillán", tipologia="2D + 1B", precio_uf=2160)

    def setUp(self):
        self.client.login(username='admin', password='admin123')

    def test_export_sin_columna_imagen(self):
        r = self.client.get('/admin/calculadora/propiedad/exportar-csv/')
        self.assertEqual(r.status_code, 200)
        header = r.content.decode('utf-8-sig').splitlines()[0]
        self.assertNotIn('imagen', header)
        self.assertIn('precio_uf', header)

    def test_import_crea_y_actualiza(self):
        csv_txt = (
            "id,edificio,comuna,entrega,tipologia,precio_uf,superficie_total_m2,"
            "superficie_util_m2,superficie_terraza_m2,enlace,activa,orden\r\n"
            f"{self.prop.id},Editado,Las Condes,Inmediata,9D,1.234,50,48,2,,si,5\r\n"
            ",Nuevo,Talca,Inmediata,1D,2.999,30,28,0,,si,1\r\n"
            ",,sin tipologia,X,,1,1,1,0,,si,0\r\n"
        )
        up = SimpleUploadedFile("p.csv", csv_txt.encode("utf-8-sig"), content_type="text/csv")
        r = self.client.post('/admin/calculadora/propiedad/importar-csv/', {'archivo_csv': up})
        self.assertEqual(r.status_code, 302)
        self.prop.refresh_from_db()
        self.assertEqual(self.prop.precio_uf, 1234.0)
        self.assertEqual(self.prop.edificio, "Editado")
        nuevo = Propiedad.objects.get(edificio="Nuevo")
        self.assertEqual(nuevo.precio_uf, 2999.0)
        # La fila sin tipología no se crea.
        self.assertFalse(Propiedad.objects.filter(comuna="sin tipologia").exists())


class FactorAnualidadTests(TestCase):
    def test_factor_normal(self):
        # 5,95% anual, 10 años → factor ≈ 90,276
        self.assertAlmostEqual(factor_anualidad(5.95, 10), 90.2757, places=2)

    def test_tasa_cero(self):
        self.assertEqual(factor_anualidad(0, 10), 0.0)

    def test_plazo_cero(self):
        self.assertEqual(factor_anualidad(5.0, 0), 0.0)


class CalcularCapacidadTests(TestCase):
    """Reglas de negocio Peterman: sueldo líquido → precio máximo del depto."""

    def test_ejemplo_referencia(self):
        # Caso real entregado por el cliente.
        r = calcular_capacidad(
            sueldo_liquido_clp=10_000_000, sueldo_2_clp=0,
            plazo_anios=10, tasa_anual=5.95, pie_pct=10,
            valor_uf=40782.27, factor_endeudamiento=3.6,
        )
        self.assertEqual(r['dividendo_clp'], 2_777_778)
        self.assertAlmostEqual(r['dividendo_uf'], 68.11, places=2)
        self.assertAlmostEqual(r['precio_maximo_uf'], 6149.02, places=2)
        self.assertEqual(r['precio_maximo_clp'], 250_770_815)
        self.assertAlmostEqual(r['financiamiento_uf'], 5534.11, places=2)
        self.assertEqual(r['financiamiento_clp'], 225_693_734)
        self.assertAlmostEqual(r['pie_uf'], 614.90, places=2)
        self.assertEqual(r['pie_clp'], 25_077_082)

    def test_complemento_renta_suma(self):
        base = calcular_capacidad(5_000_000, 0, 10, 5.95, 10, 40782.27, 3.6)
        comp = calcular_capacidad(5_000_000, 5_000_000, 10, 5.95, 10, 40782.27, 3.6)
        self.assertAlmostEqual(comp['precio_maximo_uf'], base['precio_maximo_uf'] * 2, places=1)

    def test_pie_afecta_financiamiento(self):
        r = calcular_capacidad(10_000_000, 0, 10, 5.95, 20, 40782.27, 3.6)
        self.assertAlmostEqual(r['financiamiento_uf'] + r['pie_uf'], r['precio_maximo_uf'], places=1)
        self.assertAlmostEqual(r['pie_uf'], r['precio_maximo_uf'] * 0.20, places=1)

    def test_ingreso_cero(self):
        r = calcular_capacidad(0, 0, 10, 5.95, 10, 40782.27, 3.6)
        self.assertEqual(r['precio_maximo_uf'], 0.0)

    def test_uf_cero(self):
        r = calcular_capacidad(10_000_000, 0, 10, 5.95, 10, 0, 3.6)
        self.assertEqual(r['precio_maximo_uf'], 0.0)


class FormValidationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tasa = InterestRate.objects.create(
            nombre="Test", porcentaje=5.95,
            plazo_min_anios=5, plazo_max_anios=30, activa=True
        )

    def _data(self, **overrides):
        data = {
            'nombre_completo': 'Juan Pérez',
            'email': 'juan@ejemplo.cl',
            'telefono': '+56912345678',
            'sueldo_liquido_clp': '10.000.000',
            'complementa_renta': 'no',
            'sueldo_2_clp': '0',
            'plazo_anios': '10',
            'pie_pct': '10',
            'tasa_interes_id': str(self.tasa.id),
        }
        data.update(overrides)
        return data

    def test_form_valido(self):
        form = CalculadoraForm(self._data(), tasas=InterestRate.objects.all())
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['sueldo_liquido_clp'], 10_000_000)

    def test_sueldo_obligatorio(self):
        form = CalculadoraForm(self._data(sueldo_liquido_clp=''), tasas=InterestRate.objects.all())
        self.assertFalse(form.is_valid())

    def test_sueldo2_se_ignora_si_no_complementa(self):
        form = CalculadoraForm(
            self._data(complementa_renta='no', sueldo_2_clp='500.000'),
            tasas=InterestRate.objects.all()
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['sueldo_2_clp'], 0)

    def test_sueldo2_se_usa_si_complementa(self):
        form = CalculadoraForm(
            self._data(complementa_renta='si', sueldo_2_clp='500.000'),
            tasas=InterestRate.objects.all()
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['sueldo_2_clp'], 500_000)


class ViewIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tasa = InterestRate.objects.create(
            nombre="CMF", porcentaje=5.95,
            plazo_min_anios=5, plazo_max_anios=30, activa=True
        )
        cfg = PdfConfig.load()
        cfg.valor_uf = 40782.27
        cfg.factor_endeudamiento = 3.6
        cfg.save()
        Propiedad.objects.create(edificio="Gamero 436", comuna="Chillán",
                                 tipologia="2D + 1B", precio_uf=2160, activa=True)
        Propiedad.objects.create(edificio="Caro", comuna="Las Condes",
                                 tipologia="3D + 2B", precio_uf=9000, activa=True)

    def setUp(self):
        # El cache local persiste entre tests: limpiar el contador anti-spam.
        cache.clear()

    def _post_data(self, **overrides):
        data = {
            'nombre_completo': 'María López',
            'email': 'maria@test.cl',
            'telefono': '',
            'sueldo_liquido_clp': '10.000.000',
            'complementa_renta': 'no',
            'sueldo_2_clp': '0',
            'plazo_anios': '10',
            'pie_pct': '10',
            'tasa_interes_id': str(self.tasa.id),
        }
        data.update(overrides)
        return data

    def test_get_form(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Calcula tu Departamento')

    def test_post_calcula_y_filtra(self):
        response = self.client.post('/', self._post_data())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '6.149,02')
        # Sólo la propiedad de 2160 UF cabe en el presupuesto (no la de 9000).
        sub = Submission.objects.latest('created_at')
        self.assertEqual(sub.unidades_encontradas, 1)
        self.assertContains(response, 'Gamero 436')

    def test_honeypot_rechaza_bots(self):
        response = self.client.post('/', self._post_data(sitio_web='http://spam.com'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Submission.objects.count(), 0)

    def test_rate_limit_por_ip(self):
        # Simular que la IP ya agotó su cuota horaria.
        cache.set('calc-envios-127.0.0.1', MAX_ENVIOS_POR_HORA, 3600)
        response = self.client.post('/', self._post_data())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Submission.objects.count(), 0)
        self.assertContains(response, 'demasiadas simulaciones')

    def test_tasa_desactivada_no_falla(self):
        # Tasa inactiva no listada en el form → el POST no debe dar 500.
        inactiva = InterestRate.objects.create(
            nombre="Vieja", porcentaje=9.9, activa=False)
        response = self.client.post('/', self._post_data(tasa_interes_id=str(inactiva.id)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Submission.objects.count(), 0)

    def test_rates_json_endpoint(self):
        response = self.client.get('/api/rates/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['nombre'], 'CMF')
