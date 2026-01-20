import pytest

from django.utils.translation import activate
from django.conf import settings


@pytest.fixture(autouse=True)
def set_default_language():
    activate(settings.LANGUAGE_CODE)


@pytest.fixture
def language_es():
    return "es"


@pytest.fixture
def language_de():
    return "de"
