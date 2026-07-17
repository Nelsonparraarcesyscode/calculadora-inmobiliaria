# Despliegue en cPanel (Passenger + Python)

## Requisitos previos
- cPanel con soporte **Setup Python App** (Passenger)
- Python 3.10+ disponible en el servidor

## Pasos de despliegue

### 1. Crear aplicación Python en cPanel
1. Ve a **cPanel → Setup Python App → Create Application**
2. Selecciona Python 3.10+ (o la versión más reciente disponible)
3. **Application root**: `calculadora-inmobiliaria` (la carpeta del proyecto)
4. **Application URL**: `/` o el subdominio deseado
5. **Application startup file**: `passenger_wsgi.py`
6. Click **Create**

### 2. Subir archivos
Sube todo el proyecto (sin `venv/`, `__pycache__/`, `db.sqlite3`) al directorio configurado.

### 3. Instalar dependencias
Desde el terminal virtual de cPanel (o SSH):
```bash
cd ~/calculadora-inmobiliaria
source /home/USUARIO/virtualenv/calculadora-inmobiliaria/3.x/bin/activate
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
Copia el archivo de ejemplo y edítalo:
```bash
cp .env.example .env
nano .env
```
Genera un SECRET_KEY seguro:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
Configura:
- `DJANGO_SECRET_KEY` → el valor generado
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS=tudominio.cl,www.tudominio.cl`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://tudominio.cl,https://www.tudominio.cl`

### 5. Migrar base de datos y collectstatic
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 6. Cargar datos iniciales (opcional)
```bash
python seed.py
```

### 7. Reiniciar la aplicación
```bash
mkdir -p tmp
touch tmp/restart.txt
```
O desde cPanel → Setup Python App → **Restart**

## Estructura en el servidor
```
~/calculadora-inmobiliaria/
├── .env                     ← Variables de entorno (NO commitear)
├── .htaccess                ← Seguridad Apache
├── passenger_wsgi.py        ← Entry point Passenger
├── manage.py
├── requirements.txt
├── db.sqlite3               ← Base de datos (se crea con migrate)
├── staticfiles/             ← Static files (se crea con collectstatic)
├── media/pdf/               ← PDFs generados
├── config/
├── calculadora/
└── tmp/restart.txt          ← Touch para reiniciar
```

## Despliegue en Railway — variables requeridas
En Railway (detectado por `RAILWAY_PUBLIC_DOMAIN`) el proyecto arranca con `DEBUG=False`
y **exige** estas variables (Settings → Variables del servicio):

| Variable | Obligatoria | Descripción |
|---|---|---|
| `DJANGO_SECRET_KEY` | Sí | Si falta, la app no arranca (por diseño). |
| `DJANGO_SUPERUSER_PASSWORD` | Recomendada | Sin ella, `seed.py` no crea/actualiza el superusuario. |
| `DJANGO_SUPERUSER_USERNAME` | No (default `admin`) | Usuario del admin. |
| `DJANGO_MEDIA_ROOT` | Recomendada | Ruta de un volumen persistente (ej: `/data/media`) para que las imágenes subidas sobrevivan a los deploys. Requiere montar un Volume en el servicio. |

> Nota: si la instalación quedó con el antiguo usuario `admin/admin123`, al definir
> `DJANGO_SUPERUSER_PASSWORD` el próximo deploy actualizará la contraseña automáticamente.

## Notas de seguridad
- El `.htaccess` deniega acceso directo a `.env`, `db.sqlite3` y archivos `.py`
- `DEBUG=False` activa HSTS, SSL redirect, secure cookies automáticamente
- Actualiza el valor UF desde el admin: `/admin/`

## Embed en WordPress (iframe)
La vista tiene `@xframe_options_exempt` para permitir embed. Usa:
```html
<iframe src="https://tudominio.cl/" width="100%" height="900" frameborder="0"></iframe>
```
