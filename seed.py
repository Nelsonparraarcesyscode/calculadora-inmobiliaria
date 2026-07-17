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

# Admin user — credenciales SÓLO por variables de entorno (nunca hardcodeadas).
admin_username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
admin_password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
admin_email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@localhost')

if not admin_password:
    print("  DJANGO_SUPERUSER_PASSWORD no definida: no se crea/actualiza superusuario.")
    print("  (Créalo manualmente con: python manage.py createsuperuser)")
else:
    user = User.objects.filter(username=admin_username).first()
    if user is None:
        User.objects.create_superuser(admin_username, admin_email, admin_password)
        print(f"  Superusuario creado: {admin_username}")
    else:
        # Sincroniza la contraseña con la variable de entorno (remedia
        # instalaciones antiguas que quedaron con una clave por defecto).
        user.set_password(admin_password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f"  Superusuario actualizado: {admin_username}")

print("Seed completado.")
