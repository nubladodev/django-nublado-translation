import pytest

from django.utils.translation import gettext_lazy as _
from django.conf import settings

from django_nublado_translation.conf.app_settings import SETTINGS_DICT_NAME
from django_nublado_translation.utils import get_translation_languages_enum

TEST_LANGUAGES = [
    ("en", _("English")),
    ("es", _("Spanish")),
    ("de", _("German")),
    ("ja", _("Japanese")),
]


def assert_enum_correct(enum, source_language):
    assert source_language not in enum.values
    for code, label in settings.LANGUAGES:
        if code != source_language:
            assert code in enum.values
            assert label in enum.labels


class TestUtils:

    def test_get_translation_languages_enum(self, set_django_setting, translation_app_settings):
        assert translation_app_settings._loaded is False
        set_django_setting(
            "LANGUAGES",
            TEST_LANGUAGES,
        )

        enum = get_translation_languages_enum()
        assert settings.LANGUAGE_CODE == "en"
        assert translation_app_settings.SOURCE_LANGUAGE == settings.LANGUAGE_CODE
        assert_enum_correct(enum, translation_app_settings.SOURCE_LANGUAGE)
  
        # Override source language.
        set_django_setting(
            SETTINGS_DICT_NAME,
            {"SOURCE_LANGUAGE": "es"},
        )
        translation_app_settings.reload()
        assert translation_app_settings.SOURCE_LANGUAGE == "es"
        enum = get_translation_languages_enum()
        assert_enum_correct(enum, translation_app_settings.SOURCE_LANGUAGE)
