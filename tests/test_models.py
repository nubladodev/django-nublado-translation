import pytest

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import activate

from django_nublado_translation.models import (
    TranslationModel,
    TranslationLanguageModel,
)

from .models import (
    TestModelSetup,
    TranslationLanguageTestModel,
    TranslationSourceTestModel,
    TranslationTestModel,
    CustomSourceTestModel,
    CustomTranslationTestModel,
)

# Tests
@pytest.mark.django_db(transaction=True)
class TestTranslationLanguageModel(TestModelSetup):

    model = TranslationLanguageTestModel
    test_models = [model]

    def test_language_fixtures_valid(self, language_es, language_de):
        # Get all allowed languages
        allowed = TranslationLanguageModel.LanguageChoices.values
        assert language_es in allowed
        assert language_de in allowed

    def test_language_choices(self, translation_app_settings):
        """
        The language choices are from an enum,
        and the source language isn't a member.
        """
        for language_code, label in TranslationLanguageModel.LanguageChoices.choices:
            assert (
                language_code
                != translation_app_settings.SOURCE_LANGUAGE
            )

    def test_language_not_in_choices(self, translation_app_settings):
        """
        An exception is raised if a language code not included in
        the language choices is assigned.
        """
        invalid_language = "xx"
        source_language = translation_app_settings.SOURCE_LANGUAGE

        obj = self.model.objects.create(name="hello", language="es")

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

    def test_translations_dict(
        self,
        language_es,
        language_de,
    ):
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
        translations_dict = source.translations_dict
        assert len(translations_dict) == 2
        assert translations_dict[language_es] == translation_es
        assert translations_dict[language_de] == translation_de

    def test_has_translation(self, language_es, language_de):
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

        assert source.has_translation(language_es) is True
        assert source.has_translation(language_de) is False     
        assert source.has_translation("xx") is False

    def test_get_translation(self, language_es, language_de):
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

        translation = source.get_translation(language_es)
        assert translation == translation_es

        translation = source.get_translation(language_de)
        assert translation == translation_de

        # Return None if no translation is found.
        translation = source.get_translation("fr")
        assert translation is None


    def test_get_current_translation(self, language_es, language_de):
        """
        Get the translation of the current language.
        """
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

        # Default language
        translation = source.get_current_translation()
        assert translation is None
   
        # es
        activate(language_es)
        translation = source.get_current_translation()
        assert translation == translation_es
    
        # de
        activate(language_de)
        translation = source.get_current_translation()
        assert translation is None

@pytest.mark.django_db(transaction=True)
class TestTranslationModel(TestModelSetup):
    """
    Tests for the abstract model TranslationSourceModel
    """

    source_model = TranslationSourceTestModel
    custom_source_model = CustomSourceTestModel
    translation_model = TranslationTestModel
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
        assert TranslationModel.translation_fields == []
        assert TranslationModel.translations_name == "translations"

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

    def test_meta(self):
        constraints = self.translation_model._meta.constraints
        custom_constraints = self.custom_translation_model._meta.constraints

        assert any(
            isinstance(c, models.UniqueConstraint)
            and set(c.fields) == {"language", "slug"}
            for c in constraints
        )
        assert any(
            isinstance(c, models.UniqueConstraint)
            and set(c.fields) == {"language", "source"}
            for c in constraints
        )

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

    def test_unique_constraints_applied(self):
        translation_model = TranslationTestModel

        # Collect all unique constraints
        unique_constraints = [
            c
            for c in translation_model._meta.constraints
            if isinstance(c, models.UniqueConstraint)
        ]

        # Check that there is a language + source constraint
        expected_name = (
            f"{TranslationSourceTestModel._meta.db_table}_language_source_unique"
        )
        assert any(
            c.name == expected_name for c in unique_constraints
        ), f"Missing expected UniqueConstraint: {expected_name}"

        # Check that there is a language + slug constraint.
        expected_name = (
            f"{TranslationSourceTestModel._meta.db_table}_language_slug_unique"
        )
        assert any(
            c.name == expected_name for c in unique_constraints
        ), f"Missing expected UniqueConstraint: {expected_name}"

        # Optionally, verify the fields for each constraint.
        for c in unique_constraints:
            if c.name.endswith("language_source_unique"):
                assert set(c.fields) == {"language", "source"}
            if c.name.endswith("language_slug_unique"):
                assert set(c.fields) == {"language", "slug"}

    def test_default_source_name(self, language_es):
        source = self.source_model.objects.create(
            name="foo",
            slug="foo",
        )
        translation = self.translation_model.objects.create(
            source=source,
            language=language_es,
            name="bar",
            slug="bar",
        )

        # Default source fk: source
        assert hasattr(translation, "source")
        assert translation.source == source

        # Reverse relation exists
        assert translation in source.translations.all()

    def test_custom_source_name(self, language_es):
        source = self.custom_source_model.objects.create(
            name="foo",
            slug="foo",
        )

        translation = self.custom_translation_model.objects.create(
            parent=source,
            language=language_es,
            name="bar",
            slug="bar",
        )

        # Custom source fk: "parent"
        assert hasattr(translation, "parent")
        assert translation.parent == source
        assert not hasattr(translation, "source")
        assert translation in source.localized.all()


    def test_default_translations_name(self, language_es):
        source = self.source_model.objects.create(
            name="foo",
            slug="foo",
        )
        translation = self.translation_model.objects.create(
            source=source,
            language=language_es,
            name="bar",
            slug="bar",
        )

        assert hasattr(source, "translations")
        assert translation in source.translations.all()

    def test_custom_translations_name(self, language_es):

        source = self.custom_source_model.objects.create(
            name="foo",
            slug="foo",
        )
        translation = self.custom_translation_model.objects.create(
            parent=source,
            language=language_es,
            name="bar",
            slug="bar",
        )
        assert hasattr(source, "localized")
        assert translation in source.localized.all()
        assert not hasattr(source, "translations")