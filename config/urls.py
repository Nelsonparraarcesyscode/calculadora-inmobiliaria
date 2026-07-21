from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve

admin.site.site_header = "Calculadora Inmobiliaria"
admin.site.site_title = "Admin"
admin.site.index_title = "Panel de Administración"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('calculadora.urls')),
]

# Servir archivos de media desde Django. Para sitios pequeños es suficiente;
# en cPanel evita tener que configurar un alias de Apache para /media/.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
