# django-nublado-translation

**A simple, reliable model-field translation system for Django projects.**

## Overview
This app provides a lightweight system for translating model fields without adding bloat:
- There's no automatic field injection into source models.
- There's no Generic ForeignKey hacks
- It's focused on simple, per-field translations.

It’s designed to be reusable, clear, and predictable. Subclass two abstract models, specify the source model and 
fields to be translated, and you're good to go.

## What's included
- Abstract base models for translations
  - `TranslationSourceModel`: for models that's to be translated.
  - `TranslationModel`: for a model that specifies the fields to be translated and the source to link to.
- Automatic foreign key from translation to source.
  - Default names: `source` for the source model,  and `translations` for the reverse relation.
  - Customizable via`source_name` and `translations_name`.
- Unique fields in the source model are automatically made unique per language in the translation model.
- Enum-based language choices excluding the source language.

## Installation

```bash
pip install django-nublado-translation 
```

Add to `INSTALLED_APPS`

```python
INSTALLED_APPS = [
    ...,
    "django_nublado_translation",
]
```
## AbstractModels

## App settings

## Testing