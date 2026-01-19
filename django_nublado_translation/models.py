import copy

from django.db import models
from django.db.models.base import ModelBase
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from django_nublado_translation.conf import app_settings

"""
Simple model translation
"""

TranslationLanguageChoices = settings.TRANSLATION_LANGUAGES_ENUM


class TranslationLanguageModel(models.Model):
    """
    An abstract model that provides a language choices
    field populated by the project's translation language settings, typically
    omitting the default language.
    """

    LanguageChoices = TranslationLanguageChoices

    language = models.CharField(
        max_length=2,
        choices=LanguageChoices,
        default=LanguageChoices.ES,
    )

    class Meta:
        abstract = True
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_language_valid",
                # Hacky, since LanguageChoices can't be referred to in model.
                condition=models.Q(language__in=TranslationLanguageChoices.values),
            )
        ]


class TranslationSourceModel(models.Model):
    """
    An abstract model for subclassed models
    that are to be translated.
    """

    # The source language from which the translations are derived.
    SOURCE_LANGUAGE = app_settings.DJANGO_NUBLADO_TRANSLATION_SOURCE

    class Meta:
        abstract = True

    @property
    def translations_dict(self):
        """
        Return a dict of translations
        indexed by language.
        """
        trans_dict = {
            translation.language: translation for translation in self.translations.all()
        }
        return trans_dict


class TranslationBase(ModelBase):
    """
    A base for TranslationModel.
    Thanks to django-i18n-model (an older for the idea. I wanted to create a simple
    model-translation system without all the extra baggage of adding extra fields
    to the source model or getting hacky with Generic Foreign Keys. I should find a better
    way to do it, but this simple approach works. For now.
    """

    def __new__(cls, name, bases, attrs, **kwargs):
        super_new = super().__new__
        attr_meta = attrs.get("Meta", None)

        if not attr_meta:
            raise ImproperlyConfigured(
                "Subclasses of TranslationModel must have a Meta class."
            )

        if attr_meta.abstract:
            return super_new(cls, name, bases, attrs)

        if "TranslationModel" not in [b.__name__ for b in bases]:
            # This is not a TranslationModel subclass.
            raise ImproperlyConfigured("Model must be subclass of TranslationModel.")

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
            for field in source_model._meta.local_fields:
                if field.name in translation_fields:
                    # Copy field to translation model.
                    field_copy = copy.deepcopy(field)
                    if field._unique:
                        # If any fields are unique, "deuniqueify" them to
                        # later make them unique by language in the
                        # translation model.
                        field_copy._unique = False
                        unique_fields.append(field_copy.name)
                    attrs[field.name] = field_copy

        if hasattr(attr_meta, "unique_together"):
            attr_meta.unique_together += ("language", "source")
        else:
            attr_meta.unique_together = (("language", "source"),)

        # Make unique fields from source unique together with
        # language in translation.
        if unique_fields:
            for field in unique_fields:
                attr_meta.unique_together += (("language", field),)

        return super_new(cls, name, bases, attrs, **kwargs)


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
    # If any of the translatable fields in the source model are unique,
    # their copies are made unique by language in the translation model.
    translation_fields = []

    # The name of the reverse relation of the translations in the source model.
    translations_name = "translations"

    class Meta(TranslationLanguageModel.Meta):
        abstract = True
