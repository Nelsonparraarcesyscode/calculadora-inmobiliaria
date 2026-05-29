"""Seed script: creates default interest rates, PDF config, and admin user."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from calculadora.models import InterestRate, PdfConfig

# Default interest rates
rates = [
    {'nombre': 'Tasa Preferencial', 'porcentaje': 3.5, 'plazo_min_anios': 10, 'plazo_max_anios': 30},
    {'nombre': 'Tasa Estándar', 'porcentaje': 4.5, 'plazo_min_anios': 5, 'plazo_max_anios': 30},
    {'nombre': 'Tasa Flexible', 'porcentaje': 5.5, 'plazo_min_anios': 5, 'plazo_max_anios': 20},
]

for rate in rates:
    InterestRate.objects.get_or_create(nombre=rate['nombre'], defaults=rate)
    print(f"  Tasa: {rate['nombre']} ({rate['porcentaje']}%)")

# Default PDF config
PdfConfig.load()
print("  PdfConfig creada")

# Admin user
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@localhost', 'admin123')
    print("  Superusuario creado: admin / admin123")
else:
    print("  Superusuario ya existe")

print("Seed completado.")
