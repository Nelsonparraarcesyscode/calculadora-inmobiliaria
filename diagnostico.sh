#!/bin/bash
# Diagnóstico rápido del despliegue en cPanel.
# Uso: bash diagnostico.sh
DOMAIN="calculadora.petermanncapitalgroup.cl"
source "$HOME/virtualenv/calculadora-inmobiliaria/3.12/bin/activate" 2>/dev/null
cd "$HOME/calculadora-inmobiliaria" || exit 1

echo "===== 1. Codigo HTTP de la portada (esperado: 200) ====="
curl -sk -o /dev/null -w "%{http_code}\n" "https://$DOMAIN/"

echo "===== 2. Codigo HTTP del admin (esperado: 302) ====="
curl -sk -o /dev/null -w "%{http_code}\n" "https://$DOMAIN/admin/"

echo "===== 3. Codigo HTTP del login del admin (esperado: 200) ====="
curl -sk -o /dev/null -w "%{http_code}\n" "https://$DOMAIN/admin/login/"

echo "===== 4. Codigo HTTP de un estatico del admin (esperado: 200) ====="
curl -sk -o /dev/null -w "%{http_code}\n" "https://$DOMAIN/static/admin/css/base.css"

echo "===== 5. Admin probado DENTRO de Django, sin pasar por Apache (esperado: 302) ====="
python manage.py shell -c "from django.test import Client; print(Client(SERVER_NAME='calculadora.petermanncapitalgroup.cl').get('/admin/', secure=True).status_code)" 2>&1 | tail -3

echo "===== 6. Ultimas 5 lineas de passenger.log ====="
tail -5 "$HOME/logs/passenger.log" 2>/dev/null || echo "(sin log)"

echo "===== FIN DEL DIAGNOSTICO ====="
