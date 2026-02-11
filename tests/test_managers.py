import pytest

from django.db.models import Manager
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

    def test_prefetch_translations_no_queryset(self, source, translation_es, translation_de):
        """
        prefetch_translations always returns the results in a list referenced by the 
        attribute prefetched_translations.
        """
        source_pk = source.pk

        # Before prefetch: no attribute exists
        assert not hasattr(source, "prefetched_translations")

        # without translation filter.
        source = (
            self.source_model.objects
            .prefetch_translations()
            .get(pk=source_pk)
        )

        # After prefetch: prefetched_translations exists and is a list
        assert hasattr(source, "prefetched_translations")
        assert isinstance(source.prefetched_translations, list)
        assert len(source.prefetched_translations) == 2
        assert translation_es in source.prefetched_translations
        assert translation_de in source.prefetched_translations

        # Original related manager still works
        assert isinstance(source.translations, Manager)
        all_translations = list(source.translations.all())
        assert translation_es in all_translations
        assert translation_de in all_translations

    def test_prefetch_translations_with_queryset(self, source, translation_es, translation_de):
        """
        prefetch_translations always returns the results in a list referenced by the 
        attribute prefetched_translations.
        """
        source_pk = source.pk

        # Before prefetch: no attribute exists
        assert not hasattr(source, "prefetched_translations")

        # translation filter
        translation_qs = self.translation_model.objects.filter(language=LANG_ES)

        # with translation filter.
        source = (
            self.source_model.objects
            .prefetch_translations(queryset=translation_qs)
            .get(pk=source_pk)
        )

        # After prefetch: prefetched_translations exists and is a list
        assert hasattr(source, "prefetched_translations")
        assert isinstance(source.prefetched_translations, list)
        assert len(source.prefetched_translations) == 1
        assert translation_es in source.prefetched_translations
        assert translation_de not in source.prefetched_translations

        # Original related manager still works
        assert isinstance(source.translations, Manager)
        all_translations = list(source.translations.all())
        assert translation_es in all_translations
        assert translation_de in all_translations


@pytest.mark.django_db(transaction=True)
class TestTranslationManager(TestModelSetup):
    source_model = TranslationSourceTestModel
    translation_model = TranslationTestModel
    test_models = [source_model, translation_model]

    def test_with_source(self, translation_es):
        translation = self.translation_model.objects.get(pk=translation_es.pk)
        assert translation.__class__.source.is_cached(translation) is False

        translation = (
            self.translation_model.objects
            .with_source()
            .get(pk=translation_es.pk)
        )
        assert translation.__class__.source.is_cached(translation) is True

