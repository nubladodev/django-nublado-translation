import pytest

from django.conf import settings as django_settings

from django_nublado_translation.conf.app_settings import SETTINGS_DICT_NAME, app_settings


class TestAppSettings:
    """
    Tests for the app settings.
    """

    def test_app_settings_dict_name(self):
        """
        Sanity check. Make sure app settings dict namme is the desired value.
        """
        assert SETTINGS_DICT_NAME == "DJANGO_NUBLADO_TRANSLATION"

    def test_app_settings_values(self):
        assert (
            app_settings.SOURCE_LANGUAGE
            == django_settings.LANGUAGE_CODE
        )
