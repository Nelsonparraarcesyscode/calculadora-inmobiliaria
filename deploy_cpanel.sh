#!/bin/bash
# Despliegue en cPanel (Passenger). Ejecutar en la Terminal de cPanel:
#   bash calculadora-inmobiliaria/deploy_cpanel.sh
# Es re-ejecutable: sirve tanto para el primer despliegue como para actualizar.
set -e

DOMAIN="calculadora.petermanncapitalgroup.cl"
APP_DIR="$HOME/calculadora-inmobiliaria"
VENV_ACTIVATE="$HOME/virtualenv/calculadora-inmobiliaria/3.12/bin/activate"

if [ ! -f "$VENV_ACTIVATE" ]; then
    echo "ERROR: no existe el virtualenv en $VENV_ACTIVATE"
    echo "Crea primero la aplicación en cPanel -> Setup Python App (Python 3.12)."
    exit 1
fi

source "$VENV_ACTIVATE"
cd "$APP_DIR"
mkdir -p "$HOME/logs" tmp

echo "==> Instalando dependencias..."
pip install -q -r requirements.txt

if [ ! -f .env ]; then
    echo "==> Configurando .env (primera vez)"
    read -s -p "Elige la contraseña del admin (sin espacios ni #): " ADMIN_PASS
    echo
    SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
    cat > .env <<EOF
DJANGO_SECRET_KEY=$SECRET
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=$DOMAIN
DJANGO_CSRF_TRUSTED_ORIGINS=https://$DOMAIN
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=$ADMIN_PASS
DJANGO_SUPERUSER_EMAIL=nelson.parra@syscode.cloud
EOF
    chmod 600 .env
fi

sed -i "s#/home/USUARIO#$HOME#" .htaccess

echo "==> Migrando base de datos..."
python manage.py migrate
echo "==> Recolectando archivos estaticos..."
python manage.py collectstatic --noinput
echo "==> Cargando datos iniciales..."
python seed.py
touch tmp/restart.txt

echo ""
echo "Despliegue completado: https://$DOMAIN"
echo "Admin: https://$DOMAIN/admin/"
