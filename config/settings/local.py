from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / '.env')

from .base import *  # noqa: E402,F401,F403

DEBUG = True

ALLOWED_HOSTS = ['*']
