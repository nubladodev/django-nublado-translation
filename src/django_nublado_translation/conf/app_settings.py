from dataclasses import dataclass

from django.conf import settings as django_settings

from django_nublado_core.conf.loader import load_app_settings

# The app's settings dict name
SETTINGS_DICT_NAME = "DJANGO_NUBLADO_TRANSLATION"

# The app settings default values.
SETTINGS_DEFAULTS = {
    "SOURCE_LANGUAGE": django_settings.LANGUAGE_CODE
}


@dataclass(frozen=True)
class AppSettings:
    SOURCE_LANGUAGE: str


app_settings = load_app_settings(
    defaults=SETTINGS_DEFAULTS,
    settings_dict_name=SETTINGS_DICT_NAME,
    cls=AppSettings,
)

