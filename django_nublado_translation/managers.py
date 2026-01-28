# from django.db import models

# class SourceQuerySet(models.QuerySet):
#     """
#     QuerySet for SourceManager
#     """

#     def preload_translations(self, prefetch_queryset=None):
#         """
#         Preload translations with source.
#         """
#         if not prefetch_queryset:
#             # Return all translations.
#             return self.prefetch_related("translations")
#         else:
#             # Return translations filtered by prefetch_queryset.
#             prefetch = models.Prefetch(
#                 "translations",
#                 queryset=prefetch_queryset,
#             )
#             return self.prefetch_related(prefetch)

#     def preload_translation_by_language(self, *, language_code, prefetch_queryset=None):
#         translation_model = self.model._meta.get_field("translations").related_model
#         translation_queryset = translation_model.objects.filter(
#             language=language_code,
#         )
        # if prefetch_queryset:
        #     translation_queryset = translation_queryset.filter()
        # prefetch = models.Prefetch(
        #     "translations",
        #     queryset=translation_queryset,
        #     to_attr=f"translation"
        # )
        # if not prefetch_queryset:
        #     translation_queryset = blog_models.PostTranslation.objects.filter(
        #         language=language_code,
        #     )
        # if not published_status:
        #     # Filter a translation, regardless of published status.

        # else:
        #     translation_queryset = blog_models.PostTranslation.objects.filter(
        #         language=language_code,
        #         published_status=published_status,
        #     )
        # prefetch = models.Prefetch(
        #     "translations",
        #     queryset=translation_queryset,
        #     to_attr="translation",
        # )
        # pass

# class SourceManagerBase(models.Manager):
#     """
#     A manager base for SourceManager.
#     """
#     pass 


# SourceManager = SourceManagerBase.from_queryset(SourceQuerySet)
