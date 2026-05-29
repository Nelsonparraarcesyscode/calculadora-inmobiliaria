from django.urls import path
from . import views

app_name = 'calculadora'

urlpatterns = [
    path('', views.calculadora_view, name='form'),
    path('api/rates/', views.rates_json, name='rates_json'),
]
