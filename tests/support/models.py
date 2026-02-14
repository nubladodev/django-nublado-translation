from django.db import models, connection


from django_nublado_translation.models import (
    TranslationLanguageModel,
    TranslationSourceModel,
    TranslationModel,
)
from django_nublado_translation.managers import TranslationSourceManager, TranslationManager
from.constants import TEST_APP_LABEL

TEST_APP_LABEL = "test_django_nublado_translation"


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


class TranslationLanguage(TranslationLanguageModel):
    """
    A test model that subclasses the
    abstract model LanguageModel.
    """

    name = models.CharField(max_length=200, unique=True)

    class Meta(TranslationLanguageModel.Meta):
        db_table = "test_translation_language"
        app_label = TEST_APP_LABEL


class Article(
    TranslationSourceModel,
):
    """
    A test model that subclasses TranslationSourceModel.
    """
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True)

    translated_fields = ["name", "slug"]

    objects = TranslationSourceManager()

    class Meta:
        db_table = "test_article"
        app_label = TEST_APP_LABEL


class ArticleTranslation(
    TranslationModel,
):
    """
    A test model that subclasses TranslationModel
    """

    source_model = Article

    translation_unique_fields = ["slug"]
    translation_scope_fields = []

    objects = TranslationManager()

    class Meta(TranslationModel.Meta):
        db_table = "test_article_translation"
        app_label = TEST_APP_LABEL


# The following pair of test models are to demonstrate how you
# can set the name of the source model fk before migrations to avoid possible collisions.
class CustomArticle(TranslationSourceModel):
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True)
    translated_fields = ["name", "slug"]

    class Meta:
        db_table = "test_custom_article"
        app_label = TEST_APP_LABEL


class CustomArticleTranslation(TranslationModel):
    """
    TranslationModel with "parent" as source fk.
    """

    source_model = CustomArticle
    # Set custom source fk name.
    source_name = "parent"

    translation_unique_fields = ["slug"]
    translation_scope_fields = []

    objects = TranslationManager()

    class Meta:
        db_table = "test_custom_article_translation"
        app_label = TEST_APP_LABEL


class ScopedArticle(TranslationSourceModel):
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True)
    translated_fields = ["name", "slug"]

    class Meta:
        db_table = "test_scoped_article"
        app_label = TEST_APP_LABEL


class ScopedArticleTranslation(TranslationModel):
    source_model = ScopedArticle
    # Set custom source fk name.
    source_name = "parent"

    test_scoped_field = models.CharField(max_length=250)

    translation_unique_fields = ["slug"]
    translation_scope_fields = ["test_scoped_field"]

    objects = TranslationManager()

    class Meta:
        db_table = "test_scoped_article_translation"
        app_label = TEST_APP_LABEL
