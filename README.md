
# django-nublado-translation

A minimal, explicit model-field translation system for Django.

Translations are implemented via a strict two-model contract:
- a source model
- a translation model

No GenericForeignKeys.  
No automatic field injection on the source model.  
Source model remains unchanged.

---

## Features

- Abstract base models:
  - `TranslationSourceModel`:
  - `TranslationModel`: 
- Manager:
  - `TranslationSourceManager`: Manager for `TranslationSourceManager`
- Guarantees:
  - One translation per `(source, language)`.
  - Source-model unique fields are unique **per language** in the translation model.
- Base-language fallback support (e.g., `es-ar` → `es`).

---

## Installation

```bash
pip install django-nublado-translation
```

```python
INSTALLED_APPS = [
    ...,
    "django_nublado_translation",
]
```

---

## Abstract models

### TranslationSourceModel

Base model for translatable objects.

- Translations are stored and cached in a language-code-indexed dictionary
`translations_dict` for convenience.

```python
from django.db import models

from django_nublado_translation.models import TranslationSourceModel
from django_nublado_translation.managers import TranslationSourceManager


class Article(TranslationSourceModel):
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True)
    content = models.TextField()

    translated_fields = [
        "title",
        "slug",
        "content",
    ]

    objects = TranslationSourceManager()
```

#### Notes

- `translated_fields` is **required** for translations, and is the single source of truth for translated fields.
- `TranslationSourceManager` is optional, but recommended, to take advantage of its translation-filtering capability.

---

### TranslationModel

Base model for translations of a `TranslationSourceModel` subclass.

- A foreign key to the source model is generated automatically.
- Default foreign key name: `source`.
- Default reverse relation name: `translations`.
- Fields are derived from `translated_fields` in related source model.
- Constraint naming is derived from the **translation model name**.

Subclasses must define:
- `source_model`
- No translated field declarations are allowed on the translation model.

```python
from django_nublado_translation.models import TranslationModel


class ArticleTranslation(TranslationModel):
    source_model = Article


# Source object
article = Article.objects.create(
    title="Hello everybody",
    slug="hello-everybody",
    content="Hello, everybody.",
)

# Translation object
ArticleTranslation.objects.create(
    source=article,
    language="es",
    title="Hola a todos",
    slug="hola-a-todos",
    content="Hola a todos.",
)
```

#### Notes

- `source_name` may be overridden **before migrations**.
- Translated fields are copied from `TranslationSourceModel.translated_fields`.

---

## Working with translations

### Using a subclass of `TranslationSource`

#### Getting translations:

```python
# Assume the default language is "en", available translation languages are
# "es" and "de", and the object has a translation for "es".

# Fetching a translation.
article.get_translation("es")
article.get_translation("es-ar")   # Falls back to "es" if no translation found for "es-ar".
article.get_current_translation()  # Uses active Django language
```

- Returns `None` if no translation exists.

#### Getting translation information:

```python
# Find out if an object has a translation in a given language.
article.has_translation("es") # True
article.has_translation("de") # False

# Get translation-languages object doesn't have a translation for.
article.get_available_translation_languages() # ["de"]
```

#### Cache management for translation_dict.

```python
article.clear_translations_dict_cache()
```

- Invalidates the internal translation cache.
- Required when translations are modified outside the instance lifecycle.

---

### Using `TranslationSourceManager`

#### Prefetching translations

```python
Article.objects.prefetch_translations()

Article.objects.prefetch_translations().filter(slug="source-article-slug")

# Prefetch filtered translations.
translation_qs = ArticleTranslation.objects.filter(language="es", published_status="published")

Article.objects.prefetch_translations(queryset=translation_qs)
```

---

## App settings

```python
from django_nublado_translation.conf.app_settings import app_settings

app_settings.SOURCE_LANGUAGE
```

### Available settings

| Setting | Default |
|-------|---------|
| `SOURCE_LANGUAGE` | `django.conf.settings.LANGUAGE_CODE` |

### Override

```python
DJANGO_NUBLADO_TRANSLATION = {
    "SOURCE_LANGUAGE": "en",
}
```

---

## Testing

```bash
pytest
```

Requires `pytest-django`.
