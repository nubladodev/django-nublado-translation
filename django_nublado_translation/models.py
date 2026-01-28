import copy

from django.db import models
from django.db.models.base import ModelBase
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property

from django_nublado_translation.conf import app_settings

"""
Simple model translation
"""
# Translation languages (without source language)
source_language = app_settings.NUBLADO_TRANSLATION_SOURCE_LANGUAGE
translation_languages_members = [
    (key.replace("-", "_").upper(), (key, label)) 
    for key, label in settings.LANGUAGES
    if key != source_language
]
translation_languages_enum = models.TextChoices(
    "TranslationLanguagesEnum",
    translation_languages_members,
)


class TranslationLanguageModel(models.Model):
    """
    An abstract model that provides a language choices
    field populated by the project's translation language settings, typically
    omitting the default language.
    """

    LanguageChoices = translation_languages_enum

    language = models.CharField(
        max_length=8,
        choices=LanguageChoices, # No default. Must be provided.
    )

    class Meta:
        abstract = True
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_language_valid",
                # Hacky, since LanguageChoices can't be referred to in model.
                condition=models.Q(language__in=list(translation_languages_enum.values)),
            )
        ]


class TranslationSourceModel(models.Model):
    """
    An abstract model for subclassed models
    that are to be translated.
    """

    class Meta:
        abstract = True

    @cached_property
    def translations_dict(self):
        """
        Return a dict of translations
        indexed by language.
        """
        trans_dict = {
            translation.language: translation for translation in self.translations.all()
        }
        return trans_dict

    def get_translation(self, language, fallback=True):
        """
        Return the translation object for the given language,
        If not found, optionally fall back to source object.
        """
        translation = self.translations_dict.get(language)
        if translation:
            return translation
        if fallback:
            return self
        return None


class TranslationBase(ModelBase):
    """
    A base for TranslationModel.
    Thanks to django-i18n-model (an older for the idea. I wanted to create a simple
    model-translation system without all the extra baggage of adding extra fields
    to the source model or getting hacky with Generic Foreign Keys. I should find a better
    way to do it, but this simple approach works. For now.
    """

    def __new__(mcls, name, bases, attrs, **kwargs):
        super_new = super().__new__
        attr_meta = attrs.get("Meta", None)

        if not attr_meta:
            raise ImproperlyConfigured(
                "Subclasses of TranslationModel must have a Meta class."
            )

        if attr_meta.abstract:
            return super_new(mcls, name, bases, attrs)

        # Make sure the translation model subclasses TranslationModel.
        if not any(issubclass(base, TranslationModel) for base in bases if isinstance(base, type)):
            raise ImproperlyConfigured("Model must subclass TranslationModel.")

        source_model = attrs.get("source_model", None)

        if not source_model:
            raise ImproperlyConfigured("Source model is required.")
        if not issubclass(source_model, TranslationSourceModel):
            raise ValueError("Source model must subclass TranslationSourceModel.")

        # Add foreign key that references the source model.
        source_name = attrs.get("source_name", "source")
        translations_name = attrs.get("translations_name", "translations")

        attrs[source_name] = models.ForeignKey(
            source_model,
            related_name=translations_name,
            editable=False,
            on_delete=models.CASCADE,
            verbose_name=_(source_name),
        )

        translation_fields = attrs.get("translation_fields", [])
        unique_fields = []

        if translation_fields:
            source_fields = {
                f.name: f
                for f in source_model._meta.concrete_fields
            }

            for field_name in translation_fields:
                # Make sure values in translation_fields have corresponding fields
                # in source_model.
                source_field = source_fields.get(field_name)
                if not source_field:
                    raise ImproperlyConfigured(
                        f"Field '{field_name}' does not exist in source model '{source_model.__name__}'"
                    )
                if source_field.primary_key:
                    raise ImproperlyConfigured(
                        "Primary key fields cannot be translated."
                    )
                if source_field.is_relation:
                    raise ImproperlyConfigured(
                        f"Relational field '{field_name}' cannot be translated."
                    )

                # Copy field to translation model.
                field_copy = copy.deepcopy(source_field)

                # Handle unique fields by making them unique per language.
                if getattr(field_copy, "_unique", False):
                    field_copy._unique = False
                    unique_fields.append(field_copy.name)

                # Add the copied field to the translation model attributes.
                attrs[field_name] = field_copy

        # Make language and source unique together
        if not hasattr(attr_meta, "constraints") or attr_meta.constraints is None:
            attr_meta.constraints = []

        # One translation per language per source
        attr_meta.constraints.append(
            models.UniqueConstraint(
                fields=["language", "source"],
                name=f"{source_model._meta.db_table}_language_source_unique",
            )
        )

        # Unique fields from source unique per language
        for field in unique_fields:
            attr_meta.constraints.append(
                models.UniqueConstraint(
                    fields=['language', field],
                    name=f"{source_model._meta.db_table}_language_{field}_unique",
                )
            )

        return super_new(mcls, name, bases, attrs, **kwargs)


class TranslationModel(TranslationLanguageModel, metaclass=TranslationBase):
    """
    An abstract model for model field translations.

    A foreign key named "source" is automatically generated and refers to the the
    source model, a subclass of TranslationSourceModel. The reverse relation is
    named "translations."

    Subclasses of TranslationModel must have a Meta class.
    """

    # The source model to be translated.
    # It must subclass the abstract model TranslationSourceModel.
    source_model = None

    # The name of the foreign key referring to the source model.
    source_name = "source"

    # The names of the fields in the source model to be copied and translated.
    translation_fields = []

    # The name of the reverse relation of the translations in the source model.
    translations_name = "translations"

    class Meta(TranslationLanguageModel.Meta):
        abstract = True
