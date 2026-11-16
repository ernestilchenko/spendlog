from django.urls import path

from . import views

app_name = 'banking'

urlpatterns = [
    path('', views.bank_overview, name='overview'),
    path('connect/', views.bank_connect, name='connect'),
    path('callback/', views.bank_callback, name='callback'),
    path('sync/', views.bank_sync, name='sync'),
]
