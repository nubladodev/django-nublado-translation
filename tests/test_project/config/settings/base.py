import os
import sys
from pathlib import Path

from django.utils.translation import gettext_lazy as _
from django.db.models import TextChoices


# Get key env values from the virtual environment.
def get_env_variable(var_name):
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = "Set the {} environment variable.".format(var_name)
        raise Exception(error_msg)


# Project name to be used globally.
PROJECT_NAME = "django-nublado-translation"

SECRET_KEY = get_env_variable("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
ALLOWED_HOSTS = []

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
    "django_nublado_translation",
    "django_nublado_core",
]

THIRD_PARTY_APPS = []
INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS + THIRD_PARTY_APPS

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

# Language Enums
languages_members = [(key.upper(), (key, label)) for key, label in LANGUAGES]
LANGUAGES_ENUM = TextChoices("LanguagesEnum", languages_members)

# Translation languages (LANGUAGES without default language)
translation_languages_members = [
    (key.upper(), (key, label)) for key, label in LANGUAGES if key != LANGUAGE_CODE
]
TRANSLATION_LANGUAGES_ENUM = TextChoices(
    "TranslationLanguagesEnum",
    translation_languages_members,
)

# LOCALE_PATHS = (BASE_DIR / APP_DIR / "project_app" / "locale",)
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
