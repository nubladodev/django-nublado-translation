import pytest

from django.utils.translation import activate

from .support.models import (
    TestModelSetup,
    TranslationSourceTestModel,
    TranslationTestModel,
)
from .support.constants import LANG_ES, LANG_DE


@pytest.fixture
def source():
    source = TranslationSourceTestModel.objects.create(
        name="foo foo",
        slug="foo-foo",
    )
    return source


@pytest.fixture
def translation_es(source):
    translation_es = TranslationTestModel.objects.create(
        source=source,
        language=LANG_ES,
        name="fee fee",
        slug="fee-fee",
    )
    return translation_es


@pytest.fixture
def translation_de(source):
    translation_de = TranslationTestModel.objects.create(
        source=source,
        language=LANG_DE,
        name="faa faa",
        slug="faa-faa",
    )
    return translation_de


@pytest.mark.django_db(transaction=True)
class TestTranslationSourceManager(TestModelSetup):
    source_model = TranslationSourceTestModel
    translation_model = TranslationTestModel
    test_models = [source_model, translation_model]

    def test_prefecth_translations(
        self, source, translation_es, translation_de
    ):
        source_pk = source.pk

        # source without preloaded translations
        with pytest.raises(AttributeError):
            cached = source._prefetched_objects_cache["translations",]
        assert hasattr(source, "_prefetched_objects_cache") is False

        # source with prefetched translations
        source = self.source_model.objects.prefetch_translations().get(pk=source_pk)
        assert source._prefetched_objects_cache["translations"].count() == 2
        assert source.translations.count() == 2

        # source with prefetched translations filtered by queryset
        translation_queryset = self.translation_model.objects.filter(
            language=LANG_ES
        )
        source = self.source_model.objects.prefetch_translations(
            queryset=translation_queryset
        ).get(pk=source_pk)
        assert source.translations.count() == 1
        assert source.translations.first() == translation_es
