import copy
import logging

from django.db import models
from django.db.models.base import ModelBase
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import get_language, gettext_lazy as _
from django.utils.functional import cached_property

from .utils import (
    get_translation_languages,
    get_translation_languages_enum,
)

logger = logging.getLogger("django")


def clone_field_without_unique(field):
    assert not field.is_relation
    name, path, args, kwargs = field.deconstruct()
    kwargs.pop("unique", None)
    return field.__class__(*args, **kwargs)


class TranslationLanguageModel(models.Model):
    """
    An abstract base model that provides a language field for translations.

    The language choices are populated from the project's translation
    language settings, excluding the source language.

    Note:
        Language choices are not enforced at the database level.
        Developers may add constraints if needed.
    """

    LanguageChoices = get_translation_languages_enum()

    language = models.CharField(
        max_length=8,
        choices=LanguageChoices,  # No default. Must be provided.
    )

    class Meta:
        abstract = True


class TranslationSourceModel(models.Model):
    """
    An abstract base model for objects that can be translated.
    """

    _TRANSLATIONS_DICT_CACHE_KEY = "_translations_dict"

    # Fields to be translated
    translated_fields = []

    class Meta:
        abstract = True

    def _build_translations_dict(self):
        """
        Build translations dict indexed by language key from fetched translations queryset.
        """
        return {
            translation.language: translation for translation in self.translations.all()
        }

    @property
    def translations_dict(self):
        """
        Return translations indexed by language code.

        The translations dict is cached to reduce database hits, and
        can be uncached manually if the dict needs to be refreshed.

        Returns:
            dict[str, TranslationModel]: Mapping of language codes to
            translation instances.
        """
        cache = self.__dict__.get(self._TRANSLATIONS_DICT_CACHE_KEY)

        if cache is None:
            cache = self._build_translations_dict()
            self.__dict__[self._TRANSLATIONS_DICT_CACHE_KEY] = cache

        return cache

    def clear_translations_dict_cache(self):
        """
        Manually clear the translations_dict cache.
        """
        self.__dict__.pop(self._TRANSLATIONS_DICT_CACHE_KEY, None)

    def get_translation(self, language):
        """
        Resolve a translation for a given language code, with fallback.

        Args:
            language (str): The language code (e.g., en, en-au, es, es-ar)

        Returns:
            TranslationModel | None: The translation instance or None if not found.
        """
        if not language:
            return None

        language = language.lower()

        # Get an exact match.
        translation = self.translations_dict.get(language)
        if translation:
            return translation

        # Base language fallback.
        # For example, if a translation isn't found for "en-au",
        # attempt to get the translation for "en".
        base_language = language.split("-", 1)[0]
        if base_language != language:
            logger.info(
                f"Language code {language} not found. Attempting to fall back to {base_language}."
            )
            return self.translations_dict.get(base_language)

        # No translation found.
        logger.info(
            f"No translation found for base language {base_language}. Returning None."
        )
        return None

    def get_current_translation(self):
        """
        Return the translation for the current language.

        Returns:
            TranslationModel | None: The translation instance or None if missing.
        """
        language = get_language()
        return self.get_translation(language)

    def has_translation(self, language) -> bool:
        """
        Check whether a translation exists for a given language.

        Args:
            language (str): Language code

        Returns:
            True if a translation exists, False otherwise.
        """

        return language in self.translations_dict

    def get_available_translation_languages(self):
        """
        Get translation languages that haven't
        been used for this source object.

        Returns:
            list[str]: A list of language codes from the allowed
            translation languages that haven't been used for this object.
        """
        used_languages = set(
            self.translations.values_list("language", flat=True)
        )
        allowed_languages = set(get_translation_languages())

        return sorted(allowed_languages - used_languages)


class TranslationBase(ModelBase):
    """
    A metaclass for translation models (base for TranslationModel).

    Automatically:
    - Validates model inheritance.
    - Adds a foreign key to the source model.
    - Copies translatable fields from the source model.
    - Applies language-scoped uniqueness constraints.
    - Registers the translation model on the source model as `_translation_model`
    """

    def __new__(mcls, name, bases, attrs, **kwargs):
        super_new = super().__new__

        # Inner Meta class from the model body (not Model._meta).
        meta_class = attrs.setdefault("Meta", type("Meta", (), {}))

        # Exit if subclass is an abstact model.
        if getattr(meta_class, "abstract", False):
            return super_new(mcls, name, bases, attrs, **kwargs)

        # Make sure the translation model subclasses TranslationModel.
        if not any(
            isinstance(base, type) and issubclass(base, TranslationModel)
            for base in bases
        ):
            raise ImproperlyConfigured(
                f"{name} must subclass TranslationModel directly or indirectly."
            )

        source_model = attrs.get("source_model", None)

        if not source_model:
            raise ImproperlyConfigured("attr: source_model is required.")
        if not issubclass(source_model, TranslationSourceModel):
            raise ValueError("Source model must subclass TranslationSourceModel.")

        # Resolve source_name.
        source_name = attrs.get("source_name")
        if source_name is None:
            source_name = getattr(TranslationModel, "_DEFAULT_SOURCE_NAME", None)
        if source_name is None:
            raise ImproperlyConfigured(
                f"{name} must define 'source_name' or TranslationModel._DEFAULT_SOURCE_NAME"
            )

        attrs[source_name] = models.ForeignKey(
            source_model,
            related_name="translations",
            editable=False,
            on_delete=models.CASCADE,
            verbose_name=_(source_name),
        )

        translation_fields = getattr(source_model, "translated_fields", [])

        if translation_fields:
            source_fields = {f.name: f for f in source_model._meta.concrete_fields}
            unique_fields = []

            for field_name in translation_fields:
                # Raise an exception if the translation model has an attribute
                # with the same name as a field that's to be translated from the source model.
                if field_name in attrs:
                    raise ImproperlyConfigured(
                        f"Field '{field_name}' on translation model '{name}' "
                        f"would overwrite an existing attribute. Rename it."
                    )

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

                field_copy = clone_field_without_unique(source_field)

                if source_field.unique:
                    unique_fields.append(field_name)

                # Add the copied field to the translation model attributes.
                attrs[field_name] = field_copy

        # Make language and source unique together
        constraints = list(getattr(meta_class, "constraints", []))

        # One translation per language per source
	app_label = source_model._meta.app_label
        translation_model_name = name.lower()
        constraints.append(
            models.UniqueConstraint(
                fields=["language", source_name],
                name=f"{app_label}_{translation_model_name}_language_source_unique",
            )
        )

        # Unique fields from source unique per language
        for field in unique_fields:
            constraints.append(
                models.UniqueConstraint(
                    fields=["language", field],
                    name=f"{app_label}_{translation_model_name}_language_{field}_unique",
                )
            )
        meta_class.constraints = constraints

        new_cls = super_new(mcls, name, bases, attrs, **kwargs)

        # Register the translation model on the source model
        source_model._translation_model = new_cls

        return new_cls

class TranslationModel(TranslationLanguageModel, metaclass=TranslationBase):
    """
    An abstract base model for translated fields of a subclass of TranslationSourceModel.

    A foreign key to the source model is automatically generated by the
    metaclass. Its name can be customized with the source_name attribute before migrations.

    Subclasses must define:
    - source_model: a subclass of TranslationSourceModel
    """

    # Do NOT change these.
    _DEFAULT_SOURCE_NAME = "source"

    # The source model to be translated.
    # It must subclass the abstract model TranslationSourceModel.
    source_model = None

    # The name of the generated foreign key referring to the source model.
    # If this is changed, it must be done so BEFORE migrations are made.
    source_name = _DEFAULT_SOURCE_NAME

    class Meta:
        abstract = True

    @classmethod
    def get_source_field_name(cls):
        """
        Return the name of the source foreign key for this translation model.
        Defaults to _DEFAULT_SOURCE_NAME if not overridden.
        """
        return getattr(cls, "source_name", cls._DEFAULT_SOURCE_NAME)
