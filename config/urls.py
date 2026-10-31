from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('', include('spendlog.dashboard.urls')),
    path('', include('spendlog.users.urls')),
    path('transactions/', include('spendlog.transactions.urls')),
    path('', include('spendlog.categories.urls')),
    path('', include('spendlog.integrations.urls')),
]
