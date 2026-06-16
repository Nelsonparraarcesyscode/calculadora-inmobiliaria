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

# Servir archivos de media también en producción (Railway no tiene un
# servidor web separado para /media/). Para sitios pequeños es suficiente.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
