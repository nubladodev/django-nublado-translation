from django.db import models
from django.db.models import Prefetch

from .models import TranslationSourceModel, TranslationModel


class TranslationSourceQuerySet(models.QuerySet):
    def prefetch_translations(self, *, queryset=None):
        """
        Prefetch translations using an optional queryset for translation filtering.

        Note: prefetched translations using this method are accessed via the
        `prefetched_translations` attribute.

        Args:
            queryset: Optional queryset to filter the prefetched translations (e.g., by language).

        Returns:
            list: translations loaded and accessed with "prefetched_translations".
        """
        if queryset is None:
            translation_model = self.model._translation_model
            queryset = translation_model.objects.all()
        return self.prefetch_related(
            Prefetch(
                "translations", queryset=queryset, to_attr="prefetched_translations"
            )
        )


class TranslationSourceManager(models.Manager.from_queryset(TranslationSourceQuerySet)):
    """
    Must be used with a subclass of `TranslationSourceModel`.
    """

    def contribute_to_class(self, model, name):
        super().contribute_to_class(model, name)

        # Sanity check: enforce manager is attached to a TranslationSourceModel subclass.
        if not issubclass(model, TranslationSourceModel):
            raise TypeError(
                f"{self.__class__.__name__} must be used with a subclass of TranslationSourceModel."
            )


class TranslationQuerySet(models.QuerySet):

    def with_source(self):
        """
        Preload the source model.
        """
        source_field_name = TranslationModel.get_source_field_name()
        return self.select_related(source_field_name)

    def by_language(self, *, language_code):
        """
        Filter by language.
        """
        return self.filter(language=language_code)


class TranslationManager(models.Manager.from_queryset(TranslationQuerySet)):
    """
    Must be used with a subclass of `TranslationModel`.
    """

    def contribute_to_class(self, model, name):
        super().contribute_to_class(model, name)

        # Sanity check: enforce manager is attached to a TranslationModel subclass.
        if not issubclass(model, TranslationModel):
            raise TypeError(
                f"{self.__class__.__name__} must be used with a subclass of TranslationModel."
            )