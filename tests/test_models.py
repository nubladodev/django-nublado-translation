import pytest

from django.db import models, IntegrityError
from django.core.exceptions import ValidationError
from django.utils.translation import activate, gettext_lazy as _

from django_nublado_translation.models import (
    TranslationModel,
    TranslationLanguageModel,
)

from .support.models import (
    TestModelSetup,
    TranslationLanguageTestModel,
    TranslationSourceTestModel,
    TranslationTestModel,
    CustomSourceTestModel,
    CustomTranslationTestModel,
)
from .support.constants import TEST_LANGUAGES, TEST_APP_LABEL, LANG_EN, LANG_ES, LANG_DE


@pytest.fixture(autouse=True)
def _test_languages(set_django_setting):
    set_django_setting("LANGUAGES", TEST_LANGUAGES)


# Tests
@pytest.mark.django_db(transaction=True)
class TestTranslationLanguageModel(TestModelSetup):

    translation_language_model = TranslationLanguageTestModel
    test_models = [translation_language_model]

    def test_language_choices(self, translation_app_settings):
        """
        The language choices are from an enum,
        and the source language isn't a member.
        """
        for language_code, label in TranslationLanguageModel.LanguageChoices.choices:
            assert language_code != translation_app_settings.SOURCE_LANGUAGE

    def test_language_not_in_choices(self, translation_app_settings):
        """
        An exception is raised if a language code not included in
        the language choices is assigned.
        """
        invalid_language = "xx"
        source_language = translation_app_settings.SOURCE_LANGUAGE

        obj = self.translation_language_model.objects.create(
            name="hello", language="es"
        )

        # A language code not in the translation-language choices
        error_message = f"Value '{invalid_language}' is not a valid choice."
        with pytest.raises(ValidationError) as excinfo:
            obj.language = invalid_language
            obj.full_clean()
        assert error_message in str(excinfo.value)

        # The default language isn't in the translation-language choices.
        error_message = f"Value '{source_language}' is not a valid choice."
        with pytest.raises(ValidationError) as excinfo:
            obj.language = source_language
            obj.full_clean()
        assert error_message in str(excinfo.value)


@pytest.mark.django_db(transaction=True)
class TestTranslationSourceModel(TestModelSetup):
    """
    Tests for the abstract model TranslationSourceModel
    """

    source_model = TranslationSourceTestModel
    translation_model = TranslationTestModel

    test_models = [
        source_model,
        translation_model,
    ]

    def test_translations_dict(self):
        source = self.source_model.objects.create(
            name="foo foo",
            slug="foo-foo",
        )
        translation_es = self.translation_model.objects.create(
            source=source,
            language=LANG_ES,
            name="fee fee",
            slug="fee-fee",
        )
        translation_de = self.translation_model.objects.create(
            source=source,
            language=LANG_DE,
            name="faa faa",
            slug="faa-faa",
        )
        translations_dict = source.translations_dict
        assert len(translations_dict) == 2
        assert translations_dict[LANG_ES] == translation_es
        assert translations_dict[LANG_DE] == translation_de

    def test_clear_translations_dict_cache(self):
        source = self.source_model.objects.create(name="foo", slug="foo")
        translation_es = self.translation_model.objects.create(
            source=source, language=LANG_ES, name="fee", slug="fee"
        )

        # Access translations_dict to build cache
        translations_dict = source.translations_dict
        assert "_translations_dict" in source.__dict__

        # Clear cache.
        source.clear_translations_dict_cache()
        assert "_translations_dict" not in source.__dict__

        # Access again rebuilds cache.
        translations_dict = source.translations_dict
        assert "_translations_dict" in source.__dict__

    def test_build_translations_dict(self):
        source = self.source_model.objects.create(name="foo", slug="foo")
        translation_es = self.translation_model.objects.create(
            source=source, language=LANG_ES, name="fee", slug="fee"
        )
        translation_de = self.translation_model.objects.create(
            source=source, language=LANG_DE, name="faa", slug="faa"
        )

        result = source._build_translations_dict()
        assert result == {LANG_ES: translation_es, LANG_DE: translation_de}

        # Ensure it's a new dict (not cached)
        assert result is not source.translations_dict

    def test_has_translation(self):
        source = self.source_model.objects.create(
            name="foo foo",
            slug="foo-foo",
        )
        translation_es = self.translation_model.objects.create(
            source=source,
            language=LANG_ES,
            name="fee fee",
            slug="fee-fee",
        )

        assert source.has_translation(LANG_ES) is True
        assert source.has_translation(LANG_DE) is False
        assert source.has_translation("xx") is False

    def test_get_translation(self):
        source = self.source_model.objects.create(
            name="foo foo",
            slug="foo-foo",
        )
        translation_es = self.translation_model.objects.create(
            source=source,
            language=LANG_ES,
            name="fee fee",
            slug="fee-fee",
        )
        translation_de = self.translation_model.objects.create(
            source=source,
            language=LANG_DE,
            name="faa faa",
            slug="faa-faa",
        )

        translation = source.get_translation(LANG_ES)
        assert translation == translation_es

        translation = source.get_translation(LANG_DE)
        assert translation == translation_de

        # Return None if no translation is found.
        translation = source.get_translation("fr")
        assert translation is None

        # Test fallback es-ar -> es
        translation = source.get_translation("es-ar")
        assert translation == translation_es

    def test_get_current_translation(self):
        """
        Get the translation of the current language.
        """
        source = self.source_model.objects.create(
            name="foo foo",
            slug="foo-foo",
        )
        translation_es = self.translation_model.objects.create(
            source=source,
            language=LANG_ES,
            name="fee fee",
            slug="fee-fee",
        )

        # Default language
        translation = source.get_current_translation()
        assert translation is None

        # es
        activate(LANG_ES)
        translation = source.get_current_translation()
        assert translation == translation_es

        # de
        activate(LANG_DE)
        translation = source.get_current_translation()
        assert translation is None

    def test_get_available_translation_languages(self):
        source = self.source_model.objects.create(
            name="foo foo",
            slug="foo-foo",
        )

        languages = source.get_available_translation_languages()
        assert set(languages) == {LANG_ES, LANG_DE}

        translation_es = self.translation_model.objects.create(
            source=source,
            language=LANG_ES,
            name="fee fee",
            slug="fee-fee",
        )

        languages = source.get_available_translation_languages()
        assert set(languages) == {LANG_DE}

        translation_de = self.translation_model.objects.create(
            source=source,
            language=LANG_DE,
            name="fuh fuh",
            slug="fuh-fuh",
        )

        languages = source.get_available_translation_languages()
        assert languages == []

@pytest.mark.django_db(transaction=True)
class TestTranslationModel(TestModelSetup):
    """
    Tests for the abstract model TranslationSourceModel
    """

    source_model = TranslationSourceTestModel
    translation_model = TranslationTestModel

    custom_source_model = CustomSourceTestModel
    # Customized source_name and translations_name
    custom_translation_model = CustomTranslationTestModel

    test_models = [
        source_model,
        custom_source_model,
        translation_model,
        custom_translation_model,
    ]

    def test_default_attrs(self):
        """
        The abstract model has the expected attributes and default values.
        """
        assert TranslationModel.source_model is None
        assert TranslationModel.source_name == "source"

    def test_get_source_field_name(self):
        # TODO: Test this better. 
        assert TranslationModel.get_source_field_name() == "source"

    def test_unique_in_source_unique_by_language_in_translation(self):
        """
        Unique fields that are to be translated from the source model
        are made unique by language in the translation model.
        """
        # Slug is unique in the source model.
        assert self.source_model._meta.get_field("slug").unique is True

        # Slug isn't unique in the translation model (it's unique with language).
        assert self.translation_model._meta.get_field("slug").unique is False

        constraints = self.translation_model._meta.constraints
        assert any(
            isinstance(c, models.UniqueConstraint)
            and set(c.fields) == {"language", "slug"}
            for c in constraints
        )
        source = self.source_model.objects.create(
            name="foo",
            slug="foo",
        )
        translation_1 = self.translation_model.objects.create(
            source=source,
            language=LANG_ES,
            name="bar",
            slug="bar",
        )
        translation_2 = self.translation_model.objects.create(
            source=source,
            language=LANG_DE,
            name="bar",
            slug="bar",
        )

        # This shouldn't raise an error: Two slugs with the same value, 
        # but different languages.
        translation_1.slug = translation_2.slug
        translation_1.full_clean()
        translation_1.save()

        # Now let's fire that expected error.
        translation_1.language = translation_2.language

        # Violating the (language, slug) unique constraint.
        with pytest.raises(IntegrityError) as excinfo:
            translation_1.save()


    def test_unique_constraints(self):
        constraints = self.translation_model._meta.constraints
        print(constraints)

        expected_name = f"{TEST_APP_LABEL}_{TranslationTestModel.__name__.lower()}_scoped_unique"
        assert any(
            isinstance(c, models.UniqueConstraint)
            and set(c.fields) == {"language", "slug"}
            and c.name == expected_name
            for c in constraints
        ), f"Missing expected UniqueConstraint: {expected_name}"

        expected_name = (
            f"{TEST_APP_LABEL}_{TranslationTestModel.__name__.lower()}_language_source_unique"
        )
        assert any(
            isinstance(c, models.UniqueConstraint)
            and set(c.fields) == {"language", "source"}
            and c.name == expected_name
            for c in constraints
        ), f"Missing expected UniqueConstraint: {expected_name}"

    def test_unique_constraints_with_further_scope(self):
        assert False

    def test_unique_constrants_for_custom_source_name(self):
        # A TranslationModel with a different name for the source field, "parent" in this example.
        custom_constraints = self.custom_translation_model._meta.constraints

        assert any(
            isinstance(c, models.UniqueConstraint)
            and set(c.fields) == {"language", "parent"}
            for c in custom_constraints
        )
        assert any(
            isinstance(c, models.UniqueConstraint)
            and set(c.fields) == {"language", "slug"}
            for c in custom_constraints
        )

    def test_default_source_name(self):
        source = self.source_model.objects.create(
            name="foo",
            slug="foo",
        )
        translation = self.translation_model.objects.create(
            source=source,
            language=LANG_ES,
            name="bar",
            slug="bar",
        )

        # Default source fk: source
        assert hasattr(translation, "source")
        assert translation.source == source

        # Reverse relation exists
        assert translation in source.translations.all()

    def test_custom_source_name(self):
        source = self.custom_source_model.objects.create(
            name="foo",
            slug="foo",
        )

        translation = self.custom_translation_model.objects.create(
            parent=source,
            language=LANG_ES,
            name="bar",
            slug="bar",
        )

        # Custom source fk: "parent"
        assert hasattr(translation, "parent")
        assert translation.parent == source
        assert not hasattr(translation, "source")

    def test_default_translations_name(self):
        source = self.source_model.objects.create(
            name="foo",
            slug="foo",
        )
        translation = self.translation_model.objects.create(
            source=source,
            language=LANG_ES,
            name="bar",
            slug="bar",
        )

        assert hasattr(source, "translations")
        assert translation in source.translations.all()