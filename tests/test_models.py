import pytest

from django.db import models, connection
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.conf import settings

from django_nublado_translation.models import (
    TranslationLanguageModel,
    TranslationSourceModel,
    TranslationModel,
)
from django_nublado_translation.conf import app_settings


# Test Models
test_app_label = "test_django_nublado_translation"


class ModelTestSetup:
    test_models = []

    def setup_method(self, method):
        with connection.schema_editor() as schema_editor:
            schema_editor.connection.in_atomic_block = False
            for model in self.test_models:
                schema_editor.create_model(model)

    def teardown_method(self, method):
        with connection.schema_editor() as schema_editor:
            schema_editor.connection.in_atomic_block = False
            for model in self.test_models:
                schema_editor.delete_model(model)
            schema_editor.connection.in_atomic_block = True


class TranslationLanguageTestModel(TranslationLanguageModel):
    """
    This is a test model that subclasses the
    abstract model LanguageModel.
    """

    name = models.CharField(max_length=200, unique=True)

    class Meta(TranslationLanguageModel.Meta):
        db_table = "test_translation_language_model"
        app_label = test_app_label


class TranslationSourceTestModel(
    TranslationSourceModel,
):
    """
    A test model that subclasses TranslationSourceModel.
    """

    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True)

    class Meta:
        db_table = "test_translation_source_model"
        app_label = test_app_label


class TranslationTestModel(
    TranslationModel,
):
    """
    A test model that subclasses TranslationModel
    """

    source_model = TranslationSourceTestModel
    translation_fields = ["name", "slug"]

    class Meta(TranslationModel.Meta):
        db_table = "test_translation_model"
        app_label = test_app_label


# Tests
@pytest.mark.django_db(transaction=True)
class TestTranslationLanguageModel(ModelTestSetup):

    model = TranslationLanguageTestModel
    test_models = [model]

    def test_language_choices(self):
        """
        The language choices are from an enum in settings derived from LANGUAGES,
        and the default source language isn't a member.
        """
        assert (
            TranslationLanguageModel.LanguageChoices
            == settings.TRANSLATION_LANGUAGES_ENUM
        )
        assert (
            settings.LANGUAGE_CODE
            not in TranslationLanguageModel.LanguageChoices.values
        )

    def test_language_not_in_choices(self):
        """
        An exception is raised if a language code not included in
        the language choices is assigned.
        """
        invalid_language = "xx"
        source_language = settings.LANGUAGE_CODE

        obj = self.model.objects.create(name="hello", language="es")

        # A language code not in the translation-language choices
        error_message = f"Value '{invalid_language}' is not a valid choice."
        with pytest.raises(ValidationError) as excinfo:
            obj.language = invalid_language
            obj.full_clean()
        assert error_message in str(excinfo.value)

        # An integrity error at the db level with a "non-cleaned" save.
        with pytest.raises(IntegrityError):
            obj.language = invalid_language
            obj.save()

        # The default language isn't in the translation-language choices.
        error_message = f"Value '{source_language}' is not a valid choice."
        with pytest.raises(ValidationError) as excinfo:
            obj.language = source_language
            obj.full_clean()
        assert error_message in str(excinfo.value)

        # An integrity error at the db level with a "non-cleaned" save.
        with pytest.raises(IntegrityError):
            obj.language = source_language
            obj.save()


@pytest.mark.django_db(transaction=True)
class TestTranslationSourceModel(ModelTestSetup):
    """
    Tests for the abstract model TranslationSourceModel
    """

    source_model = TranslationSourceTestModel
    translation_model = TranslationTestModel

    test_models = [
        source_model,
        translation_model,
    ]

    def test_default_attrs(self):
        """
        The model has the expected attributes and default values.
        """
        assert TranslationSourceModel.SOURCE_LANGUAGE == app_settings.NUBLADO_TRANSLATION_SOURCE_LANGUAGE


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


@pytest.mark.django_db(transaction=True)
class TestTranslationModel(ModelTestSetup):
    """
    Tests for the abstract model TranslationSourceModel
    """

    source_model = TranslationSourceTestModel
    translation_model = TranslationTestModel

    test_models = [
        source_model,
        translation_model,
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
        assert ("language", "slug") in self.translation_model._meta.unique_together

    def test_meta(self):
        assert self.translation_model._meta.unique_together == (
            # Only one translation per language for each source instance
            ("language", "source"),
            # The slug is unique in the source model, and is made
            # unique with the translation language in the translation model.
            ("language", "slug"),
        )

    def test_generated_source_fk(self, language_es):
        source_obj = self.source_model.objects.create(
            name="foo foo",
            slug="foo-foo",
        )
        translation_obj = self.translation_model.objects.create(
            source=source_obj,
            language=language_es,
            name="fee fee",
            slug="fee-fee",
        )
        assert translation_obj.source == source_obj
