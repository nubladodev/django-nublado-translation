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

    def test_language_fixtures_valid(self, language_es, language_de):
        # Get all allowed languages
        allowed = TranslationLanguageModel.LanguageChoices.values
        assert language_es in allowed
        assert language_de in allowed

    def test_language_choices(self):
        """
        The language choices are from an enum,
        and the source language isn't a member.
        """
        for language_code, label in TranslationLanguageModel.LanguageChoices.choices:
            assert language_code != app_settings.NUBLADO_TRANSLATION_SOURCE_LANGUAGE.upper().replace("-", "_")

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

        translation = source.get_translation("xx", fallback=False)
        assert translation is None

        translation = source.get_translation("xx", fallback=True)
        assert translation == source


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
        constraints = self.translation_model._meta.constraints
        assert any(
            isinstance(c, models.UniqueConstraint) and set(c.fields) == {"language", "slug"}
            for c in constraints
        )

    def test_meta(self):
        constraints = self.translation_model._meta.constraints
        assert any(
            isinstance(c, models.UniqueConstraint) and set(c.fields) == {"language", "slug"}
            for c in constraints
        )
        assert any(
            isinstance(c, models.UniqueConstraint) and set(c.fields) == {"language", "source"}
            for c in constraints
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


    def test_unique_constraints_applied(self):
        translation_model = TranslationTestModel
        table_name = translation_model._meta.db_table

        # Collect all unique constraints
        unique_constraints = [
            c for c in translation_model._meta.constraints
            if isinstance(c, models.UniqueConstraint)
        ]

        # Check that there is a language + source constraint
        expected_name = f"{TranslationSourceTestModel._meta.db_table}_language_source_unique"
        assert any(c.name == expected_name for c in unique_constraints), \
            f"Missing expected UniqueConstraint: {expected_name}"

        # Check that there is a language + slug constraint
        expected_name = f"{TranslationSourceTestModel._meta.db_table}_language_slug_unique"
        assert any(c.name == expected_name for c in unique_constraints), \
            f"Missing expected UniqueConstraint: {expected_name}"

        # Optionally, verify the fields for each constraint
        for c in unique_constraints:
            if c.name.endswith("language_source_unique"):
                assert set(c.fields) == {"language", "source"}
            if c.name.endswith("language_slug_unique"):
                assert set(c.fields) == {"language", "slug"}