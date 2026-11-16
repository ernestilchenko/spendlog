from django.urls import path

from . import views

app_name = 'reports'

urlpatterns = [
    path('api/summary/weekly/', views.weekly_summary, name='weekly_summary'),
]
