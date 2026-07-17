web: python manage.py collectstatic --noinput && python manage.py migrate && python seed.py && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
