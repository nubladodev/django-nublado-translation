import pytest

from .test_project.models import (
    ModelTestSetup,
    TranslationSourceTestModel,
    TranslationTestModel,
)


@pytest.mark.django_db(transaction=True)
class TestTranslationSourceManager(ModelTestSetup):
    source_model = TranslationSourceTestModel
    translation_model = TranslationTestModel
    test_models = [source_model, translation_model]

    def test_prefecth_translation(self, language_es, language_de):
        source = self.source_model.objects.create(
            name="foo foo",
            slug="foo-foo",
        )
        translation_es = self.translation_model.objects.create(
            source=source,
            language=language_es,
            name="fee fee",
            slug="fee-fee",
        )
        translation_de = self.translation_model.objects.create(
            source=source,
            language=language_de,
            name="faa faa",
            slug="faa-faa",
        )

        # source without preloaded translations
        with pytest.raises(AttributeError):
            cached = source._prefetched_objects_cache["translations",]
        assert hasattr(source, "_prefetched_objects_cache") is False

        # source with prefetched translations
        source = self.source_model.objects.prefetch_translations().get(pk=source.id)
        assert source._prefetched_objects_cache["translations"].count() == 2

        # source with prefetched translations filtered by queryset
        assert False