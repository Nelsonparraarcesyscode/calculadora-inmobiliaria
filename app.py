"""
WSGI entry point for cPanel Python App hosting (Passenger).

IMPORTANTE: en cPanel el "Application startup file" debe ser este archivo
(app.py) y el "Entry point" debe ser "application". NO usar el nombre
passenger_wsgi.py: cPanel genera su propio passenger_wsgi.py (una plantilla
que carga el startup file) y si ambos se llaman igual, el archivo se importa
a sí mismo en un bucle infinito (RecursionError).
"""
import os
import sys

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(__file__))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Load .env if available
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
except ImportError:
    pass

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
