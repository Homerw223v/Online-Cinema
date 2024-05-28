import os
from pathlib import Path

from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv
from split_settings.tools import include

if not os.getenv("EXTERNAL_ENV"):
    load_dotenv()

include(
    "components/databases.py",
    "components/installed_apps.py",
    "components/logging.py",
)

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", get_random_secret_key())

DEBUG = os.getenv("DEBUG", default=False) == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").split()

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

AUTH_API_LOGIN_URL = os.getenv("AUTH_API_LOGIN_URL")
AUTH_API_USER_INFO_URL = os.getenv("AUTH_API_USER_INFO_URL")

AUTHENTICATION_BACKENDS = [
    "config.utils.auth.CustomBackend",
    # 'django.contrib.auth.backends.ModelBackend',
]
AUTH_USER_MODEL = "users.User"

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "ru-RU"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOCALE_PATHS = ["movies/locale"]
