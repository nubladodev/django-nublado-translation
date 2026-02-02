import os
import sys
from pathlib import Path

from django.utils.translation import gettext_lazy as _


# Get key env values from the virtual environment.
def get_env_variable(var_name):
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = "Set the {} environment variable.".format(var_name)
        raise Exception(error_msg)


SECRET_KEY = get_env_variable("DJANGO_SECRET_KEY")

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1"]

# Apps
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

LOCAL_APPS = [
    "django_nublado_core",
    "django_nublado_translation",
]
INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
]

# Internationalization

# Default language code
LANGUAGE_CODE = "en"

LANGUAGES = [
    (LANGUAGE_CODE, _("English")),
    ("es", _("Spanish")),
    ("de", _("German")),
]

# Variations of LANGUAGES in different data types.
LANGUAGES_DICT = {key: value for key, value in LANGUAGES}

TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.environ["DATABASE_NAME"],
        "USER": os.environ["DATABASE_USER"],
        "PASSWORD": os.environ["DATABASE_PWD"],
        "HOST": "localhost",
        "PORT": "",
        "TEST": {
            "NAME": os.environ["TEST_DATABASE_NAME"],
        },
    }
}


# Logging
LOGGING = {
    "version": 1,
    # Version of logging
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    # Handlers
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "nublado-debug.log",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    # Loggers
    "loggers": {
        "django": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": True,
        },

    },
}