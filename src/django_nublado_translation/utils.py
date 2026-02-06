from django.db import models
from django.conf import settings as django_settings

from django_nublado_translation.conf.app_settings import app_settings


def get_translation_languages_enum(*, enum_name="TranslationLanguagesEnum"):
    """
    Return a TextChoices enum for translation languages.

    Excludes the source language defined in app settings.

    Args:
        enum_name: 
            Optional. Name of the enum class.  

    Returns:
        A Django TextChoices enum for the translation languages.
    """
    source_language = app_settings.SOURCE_LANGUAGE
    # Translation languages (without source language).
    members = [
        (key.replace("-", "_").upper(), (key, label))
        for key, label in django_settings.LANGUAGES
        if key != source_language
    ]
    return models.TextChoices(
        enum_name,
        members,
    )