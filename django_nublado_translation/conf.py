"""
Simple, prefix-based app settings.

Thanks to Benjamin Balder Back for the idea in the the blog post 
https://overtag.dk/v2/blog/a-settings-pattern-for-reusable-django-apps/
"""
from dataclasses import dataclass
from typing import Any

from django.conf import settings as django_settings
from django.utils.translation import gettext_lazy as _


# App settings prefix
settings_prefix = "DJANGO_MULTILINGUA_"


@dataclass(frozen=True)
class AppSettings:

    DJANGO_MULTILINGUA_SOURCE_LANGUAGE: str = django_settings.LANGUAGE_CODE

    def __getattribute__(self, __name: str) -> Any:
        """
        Get prefixed attribute, or overriden prefixed attribute in django.conf.settings.
        """
        if __name.startswith(settings_prefix) and hasattr(django_settings, __name):
            return getattr(django_settings, __name)

        return super().__getattribute__(__name)


app_settings = AppSettings()