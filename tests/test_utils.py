import pytest

from django.utils.translation import gettext_lazy as _
from django.conf import settings

from django_nublado_translation.conf.app_settings import SETTINGS_DICT_NAME
from django_nublado_translation.utils import (
    get_translation_languages,
    get_translation_languages_enum,
)

from .support.constants import TEST_LANGUAGES, LANG_EN, LANG_ES, LANG_DE


@pytest.fixture()
def _test_languages(set_django_setting):
    set_django_setting("LANGUAGES", TEST_LANGUAGES
)

def assert_enum_correct(enum, source_language):
    assert source_language not in enum.values
    for code, label in settings.LANGUAGES:
        if code != source_language:
            assert code in enum.values
            assert label in enum.labels


class TestUtils:
    def test_get_translation_languages(self):
        assert settings.LANGUAGE_CODE == LANG_EN
        translation_languages = get_translation_languages()
        assert set(translation_languages) == {LANG_ES, LANG_DE}

    def test_get_translation_languages_enum(
        self,
        set_django_setting,
        translation_app_settings,
    ):
        enum = get_translation_languages_enum()
        assert settings.LANGUAGE_CODE == LANG_EN
        assert translation_app_settings.SOURCE_LANGUAGE == settings.LANGUAGE_CODE
        assert_enum_correct(enum, translation_app_settings.SOURCE_LANGUAGE)

        # Override source language.
        set_django_setting(
            SETTINGS_DICT_NAME,
            {"SOURCE_LANGUAGE": LANG_ES},
        )
        translation_app_settings.reload()
        assert translation_app_settings.SOURCE_LANGUAGE == LANG_ES
        enum = get_translation_languages_enum()
        assert_enum_correct(enum, translation_app_settings.SOURCE_LANGUAGE)
