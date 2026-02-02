from django.db import models
from django.db.models import Prefetch
from django.utils.translation import get_language


class TranslationSourceQuerySet(models.QuerySet):
    def prefetch_translations(self, queryset=None):
        """
        Prefetch translations using an optional queryset.
        """
        if queryset is None:
            return self.prefetch_related("translations")
            
        return self.prefetch_related(
            Prefetch("translations", queryset=queryset),
        )

    def prefetch_current_translation(self):
        """
        Prefetch translation in the current language.
        """
        language = get_language()
        TranslationModel = self.model.translations.rel.related_model
        translation_qs = TranslationModel.objects.filter(language=language)
        return self.prefetch_translations(queryset=translation_qs)


class TranslationSourceManager(models.Manager.from_queryset(TranslationSourceQuerySet)):
	pass
