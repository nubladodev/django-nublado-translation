from django.db import models, connection


from django_nublado_translation.models import (
    TranslationLanguageModel,
    TranslationSourceModel,
    TranslationModel,
)
from django_nublado_translation.managers import TranslationSourceManager

test_app_label = "test_django_nublado_translation"


class TestModelSetup:
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

    # To do: Test overridden source_name and translations_name attributes.
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True)

    objects = TranslationSourceManager()

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

# The following pair of test models are to demonstrate how you
# can set the names of the source model fk and its reverse-relation name
# via the source_name and translations_name attributes.

class CustomSourceTestModel(TranslationSourceModel):
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True)

    class Meta:
        db_table = "test_custom_translation_source_model"
        app_label = test_app_label


class CustomTranslationTestModel(TranslationModel):
    source_model = CustomSourceTestModel
    # Set custom source fk name.
    source_name = "parent"
    # Set custom translations name.
    translations_name = "localized"
    translation_fields = ["name", "slug"]

    class Meta:
        db_table = "test_custom_translation_model"
        app_label = test_app_label