import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / '.env')

from .base import *  # noqa: E402,F401,F403

DEBUG = False

ALLOWED_HOSTS = ['testserver']

DATABASES['default']['TEST'] = {'NAME': os.environ.get('TEST_DB_NAME', 'test_spendlog')}  # noqa: F405

PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

ANTHROPIC_API_KEY = ''

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}

MIDDLEWARE = [middleware for middleware in MIDDLEWARE if 'whitenoise' not in middleware]  # noqa: F405
