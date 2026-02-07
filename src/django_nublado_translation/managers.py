from django.db import models
from django.db.models import Prefetch


class TranslationSourceQuerySet(models.QuerySet):
    def prefetch_translations(self, *, queryset=None):
        """
        Prefetch translations using an optional queryset.

        Args:
            queryset:
                Optional queryset to filter the prefetched translations (e.g., by language).

        Returns:
            TranslationSourceQuerySet with translations prefetched.
        """
        if queryset is None:
            return self.prefetch_related("translations")

        return self.prefetch_related(
            Prefetch("translations", queryset=queryset),
        )


class TranslationSourceManager(models.Manager.from_queryset(TranslationSourceQuerySet)):
    pass
