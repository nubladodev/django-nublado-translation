import copy

from django.db import models
from django.db.models.base import ModelBase
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import get_language, gettext_lazy as _
from django.utils.functional import cached_property

from django_nublado_translation.utils import (
    get_translation_languages,
    get_translation_languages_enum,
)


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

    class Meta:
        abstract = True

    @cached_property
    def translations_dict(self):
        """
        Return translations indexed by language code.

        Returns:
            dict[str, TranslationModel]: Mapping of language codes to
            translation instances.
        """
        return {
            translation.language: translation for translation in self.translations.all()
        }

    def get_translation(self, language):
        """
        Return the translation for the given language.

        Args:
            language (str): Language code

        Returns:
            TranslationModel | None: The translation instance or None if missing.
        """
        return self.translations_dict.get(language)

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
        used_languages = list(self.translations_dict.keys())
        allowed_languages = get_translation_languages()

        return [
            language_code
            for language_code in allowed_languages
            if language_code not in used_languages
        ]


class TranslationBase(ModelBase):
    """
    A metaclass for translation models (base for TranslationModel).

    Automatically:
    - Validates model inheritance.
    - Adds a foreign key to the source model.
    - Copies translatable fields from the source model.
    - Applies language-scoped uniqueness constraints.
    """

    def __new__(mcls, name, bases, attrs, **kwargs):
        super_new = super().__new__

        # Inner Meta class from the model body (not Model._meta).
        meta_class = attrs.setdefault("Meta", type("Meta", (), {}))

        # Exit if subclass is an abstact model.
        if getattr(meta_class, "abstract", False):
            return super_new(mcls, name, bases, attrs)

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

        # Add foreign key that references the source model.
        source_name = attrs.get("source_name", "source")
        # Related name
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
            source_fields = {f.name: f for f in source_model._meta.concrete_fields}

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
                if field_copy.unique:
                    field_copy.unique = False
                    unique_fields.append(field_copy.name)

                # Add the copied field to the translation model attributes.
                attrs[field_name] = field_copy

        # Make language and source unique together
        constraints = list(getattr(meta_class, "constraints", []))

        # One translation per language per source
        constraints.append(
            models.UniqueConstraint(
                fields=["language", source_name],
                name=f"{source_model._meta.db_table}_language_source_unique",
            )
        )

        # Unique fields from source unique per language
        for field in unique_fields:
            constraints.append(
                models.UniqueConstraint(
                    fields=["language", field],
                    name=f"{source_model._meta.db_table}_language_{field}_unique",
                )
            )
        meta_class.constraints = constraints

        return super_new(mcls, name, bases, attrs, **kwargs)


class TranslationModel(TranslationLanguageModel, metaclass=TranslationBase):
    """
    An abstract base model for translated fields of a subclass of TranslationSourceModel.

    A foreign key to the source model is automatically generated by the
    metaclass. Its name and related name can be customized with the source_name
    and translations_name attributes.

    Subclasses must define:
    - source_model: a subclass of TranslationSourceModel
    - translation_fields
    """

    # The source model to be translated.
    # It must subclass the abstract model TranslationSourceModel.
    source_model = None

    # The name of the generated foreign key referring to the source model.
    source_name = "source"

    # The related name of the source foreign key.
    translations_name = "translations"

    # The names of the fields in the source model to be copied and translated.
    translation_fields = []

    class Meta:
        abstract = True
