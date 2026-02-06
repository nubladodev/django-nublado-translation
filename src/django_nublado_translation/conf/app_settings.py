from dataclasses import dataclass

from django.conf import settings as django_settings

from django_nublado_core.conf.base import AppSettings

# The app's settings dict name
SETTINGS_DICT_NAME = "DJANGO_NUBLADO_TRANSLATION"

# The app settings default values.
SETTINGS_DEFAULTS = {
    "SOURCE_LANGUAGE": django_settings.LANGUAGE_CODE
}


@dataclass(frozen=True)
class AppData:
    SOURCE_LANGUAGE: str


app_settings = AppSettings(
    defaults=SETTINGS_DEFAULTS,
    settings_dict_name=SETTINGS_DICT_NAME,
    cls=AppData,
)

