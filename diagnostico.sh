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

echo "===== 4b. URL Django SIN la palabra admin (esperado: 200) ====="
curl -sk -o /dev/null -w "%{http_code}\n" "https://$DOMAIN/api/rates/"

echo "===== 4c. URL inexistente SIN la palabra admin (esperado: 404) ====="
curl -sk -o /dev/null -w "%{http_code}\n" "https://$DOMAIN/ruta-de-prueba/"

echo "===== 4d. URL inexistente CON la palabra admin (404 = no hay bloqueo; 500 = bloqueo por patron) ====="
curl -sk -o /dev/null -w "%{http_code}\n" "https://$DOMAIN/prueba-admin-xyz/"

echo "===== 5. Admin probado DENTRO de Django, sin pasar por Apache (esperado: 302) ====="
python manage.py shell -c "from django.test import Client; print(Client(SERVER_NAME='calculadora.petermanncapitalgroup.cl').get('/admin/', secure=True).status_code)" 2>&1 | tail -3

echo "===== 6. Ultimas 5 lineas de passenger.log ====="
tail -5 "$HOME/logs/passenger.log" 2>/dev/null || echo "(sin log)"

DOCROOT="$HOME/public_html/calculadora.petermanncapitalgroup.cl"
echo "===== 7. Contenido del docroot del subdominio ====="
ls -la "$DOCROOT" 2>/dev/null || echo "(no existe el docroot)"

echo "===== 8. .htaccess del docroot ====="
cat "$DOCROOT/.htaccess" 2>/dev/null || echo "(no existe .htaccess en el docroot)"

echo "===== FIN DEL DIAGNOSTICO ====="
