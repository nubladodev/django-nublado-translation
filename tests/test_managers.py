import pytest

from django.utils.translation import activate

from .models import (
    ModelTestSetup,
    TranslationSourceTestModel,
    TranslationTestModel,
)


@pytest.fixture
def source():
    source = TranslationSourceTestModel.objects.create(
        name="foo foo",
        slug="foo-foo",
    )
    return source


@pytest.fixture
def translation_es(source, language_es):
    translation_es = TranslationTestModel.objects.create(
        source=source,
        language=language_es,
        name="fee fee",
        slug="fee-fee",
    )
    return translation_es


@pytest.fixture
def translation_de(source, language_de):
    translation_de = TranslationTestModel.objects.create(
        source=source,
        language=language_de,
        name="faa faa",
        slug="faa-faa",
    )
    return translation_de


@pytest.mark.django_db(transaction=True)
class TestTranslationSourceManager(ModelTestSetup):
    source_model = TranslationSourceTestModel
    translation_model = TranslationTestModel
    test_models = [source_model, translation_model]

    def test_prefecth_translations(
        self,
        source,
        language_es,
        translation_es,
        translation_de
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
        translation_queryset = self.translation_model.objects.filter(language=language_es)
        source = self.source_model.objects.prefetch_translations(queryset=translation_queryset).get(pk=source_pk)
        assert source.translations.count() == 1
        assert source.translations.first() == translation_es
