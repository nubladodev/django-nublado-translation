import pytest

from django.utils.translation import activate
from django.conf import settings


@pytest.fixture(autouse=True)
def set_default_language():
    activate(settings.LANGUAGE_CODE)


@pytest.fixture()
def translation_app_settings():
    """A fresh, uncached instance of this app's settings for testing."""
    from django_nublado_translation.conf.app_settings import app_settings

    app_settings._loaded = False
    app_settings._data = None
    return app_settings


@pytest.fixture
def set_django_setting(monkeypatch):
    def _func(name, value):
        monkeypatch.setattr(settings, name, value, raising=False)

    return _func


@pytest.fixture
def language_es():
    return "es"


@pytest.fixture
def language_de():
    return "de"
