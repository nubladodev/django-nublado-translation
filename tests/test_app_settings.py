import pytest

from django.conf import settings as django_settings

from django_nublado_translation.conf import app_settings


class TestAppSettings:
    """
    Tests for the app settings.
    """

    def test_app_settings_prefix(self):
        assert app_settings.app_settings_prefix == "NUBLADO_TRANSLATION_"

    def test_app_settings_values(self):
        assert (
            app_settings.NUBLADO_TRANSLATION_SOURCE_LANGUAGE
            == django_settings.LANGUAGE_CODE
        )
