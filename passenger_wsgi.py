"""
Passenger WSGI entry point for cPanel Python App hosting.
cPanel uses Phusion Passenger to serve Python/Django apps.
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
