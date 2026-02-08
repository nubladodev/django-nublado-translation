# django-nublado-translation

**A simple, reliable model-field translation system for Django projects.**

Lightweight, focused, no bloat: translate model fields via a two-model contract (source model + translation model) without the tangles of GenericForeignKeys or automatic field injection. Source models stay fully intact.

## Features

- Abstract base models for translation:  
  - `TranslationSourceModel` — for models that can be translated. 
  - `TranslationModel` — for the translations of a source model. 
- Translation managers:  
  - `TranslationSourceManager` — helper methods for working with translations. 
- Guarantees:  
  - A source object can have at most one translation per language. 
  - Unique fields on the source model are unique per language in the translation model.  

## Installation

```bash
pip install django-nublado-translation 
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...,
    "django_nublado_translation",
]
```

## Abstract models

### `TranslationSourceModel`

An abstract base model for objects that can be translated.


```python
from django.db import models

from django_nublado_translation.models import TranslationSourceModel
from django_nublado_translation.managers import TranslationSourceManager


class Article(TranslationSourceModel):
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True)
    content = models.TextField()
    
    objects = TranslationSourceManager()

```

#### Notes

- Using `TranslationSourceManager` is optional but recommended. You can subclass it for app-specific translation requirements.

### `TranslationModel`

An abstract base model for the translations of a `TranslationSourceModel` subclass.
- A foreign key to the source model is generated automatically.
- The foreign key name (default `"source"`) and the reverse relation name (default `"translations"`) can be customized via
the `source_name` and `translations_name` attributes.

Subclasses must define:
- source_model: a subclass of TranslationSourceModel
- translation_fields: a list of fields from the source model to be translated.

```python
from django_nublado_translation.models import TranslationModel

class ArticleTranslation(TranslationModel):
    source_model = Article
    translation_fields = [
        "title",
        "slug",
        "content",
    ]

# Example usage
article  = Article(
    title="Hello everybody",
    slug="hello-everybody", 
    content="Hello, everybody."
)
article.save()

article_translation_es = ArticleTranslation(
    source=article,
    language="es",
    title="Hola a todos",
    slug="hola-a-todos",
    content="Hola a todos.",
)
article_translation_es.save()

```

#### Notes

- If `source_name` or `translations_name` is overridden, it must occur **before migration** for it to take effect.


## Working with translations

### From the source model:

```python
article.get_translation("es")
article.get_current_translation() # Uses currently active Django language.
```

### Using `TranslationSourceManager`

```python
# Prefetch all translations.
Article.objects.prefetch_translations()

# prefetch_translations() returns a QuerySet.
Article.objects.prefetch_translations().filter(slug="source-article-slug")

# Filter translations.
translation_qs =  ArticleTranslation.objects.filter(language="es")
Article.objects.prefetch_translations(queryset=translation_qs)
```

#### Notes

- The translation queryset can be freely customized.
- This is especially useful when subclassing managers with specific translation filters.

## App settings

Access app settings via:

```python
from django_nublado_translation.conf.app_settings import app_settings

# Example usage
print(app_settings.SOURCE_LANGUAGE)
```

### Available settings and default values:
- `SOURCE_LANGUAGE`: defaults to `django.config.settings.LANGUAGE_CODE`.

### Overriding settings

In your project's `settings.py`, define a dictionary named `DJANGO_NUBLADO_TRANSLATION`.

```python
DJANGO_NUBLADO_TRANSLATION = {
    "SOURCE_LANGUAGE": "en",
}
```

## Testing

```bash
pytest
```

#### Notes:
- Runs all tests for the app.
- Requires `pytest-django`.