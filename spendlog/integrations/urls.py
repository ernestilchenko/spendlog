from django.urls import path

from . import views

app_name = 'integrations'

urlpatterns = [
    path('api/apple-pay/', views.apple_pay_ingest, name='apple_pay_ingest'),
    path('apple-pay/', views.apple_pay_setup, name='apple_pay_setup'),
    path('apple-pay/token/', views.token_regenerate, name='token_regenerate'),
]
