import os
from pathlib import Path

import dj_database_url
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def get_env_variable(name, default=None):
    value = os.environ.get(name, default)
    if value is None:
        raise ImproperlyConfigured(f'Set the {name} environment variable')
    return value


def get_env_list(name, default=''):
    return [item.strip() for item in get_env_variable(name, default).split(',') if item.strip()]


SECRET_KEY = get_env_variable('SECRET_KEY')

DEBUG = False

ALLOWED_HOSTS = get_env_list('ALLOWED_HOSTS')

CSRF_TRUSTED_ORIGINS = get_env_list('CSRF_TRUSTED_ORIGINS')

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

LOCAL_APPS = [
    'spendlog.core.apps.CoreConfig',
    'spendlog.users.apps.UsersConfig',
    'spendlog.categories.apps.CategoriesConfig',
    'spendlog.transactions.apps.TransactionsConfig',
    'spendlog.integrations.apps.IntegrationsConfig',
    'spendlog.dashboard.apps.DashboardConfig',
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': dj_database_url.parse(get_env_variable('DATABASE_URL'), conn_max_age=60),
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = 'users:login'
LOGIN_REDIRECT_URL = 'dashboard:home'
LOGOUT_REDIRECT_URL = 'users:login'

LANGUAGE_CODE = 'en'

LANGUAGES = [
    ('en', _('English')),
    ('pl', _('Polish')),
    ('uk', _('Ukrainian')),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

TIME_ZONE = 'Europe/Warsaw'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

ANTHROPIC_API_KEY = get_env_variable('ANTHROPIC_API_KEY', '')
CATEGORIZER_MODEL = get_env_variable('CATEGORIZER_MODEL', 'claude-opus-5')
CATEGORIZER_TIMEOUT_SECONDS = 20.0

CURRENCY_SYMBOL = 'zł'
