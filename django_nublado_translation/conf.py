from django.conf import settings as django_settings

from django_nublado_core.conf import AppSettingsBase

# App settings prefix
settings_prefix = "NUBLADO_TRANSLATION_"


class AppSettings(AppSettingsBase):

    NUBLADO_TRANSLATION_SOURCE_LANGUAGE = django_settings.LANGUAGE_CODE

    @property
    def app_settings_prefix(self):
        return settings_prefix


app_settings = AppSettings()
