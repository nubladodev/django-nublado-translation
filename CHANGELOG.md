## [0.2.2] - 2026-06-23

### Changed

- Updated dependency requirement to `django-nublado-core >=0.4.3, <0.5.0`.


## [0.2.1] - 2026-06-21

### Changed

- Updated dependency requirement to `django-nublado-core >=0.4.2, <0.5.0`.


## [0.2.0] – 2026-02-08

### Changed
- Cleaned up internal file structure.
- Updated README to reflect the new translation architecture and usage patterns.

### TranslationSourceModel
- Added `translated_fields` attribute as the single source of truth for translatable fields.
- Replaced `@cached_property` `translations_dict` with a manually cached `@property`.
- Added base-language fallback to `get_translation()` (e.g., `es-ar` → `es`).
- Added `_build_translations_dict()` internal helper.
- Added `clear_translations_dict_cache()` to explicitly invalidate cached translations.

### TranslationBase
- Updated constraint naming to use the **translation model name** instead of the source model name, avoiding potential database constraint collisions.

### TranslationModel
- Removed `translation_languages` attribute.

### Breaking Changes
- `TranslationBase` now copies translated fields exclusively from
  `TranslationSourceModel.translated_fields`.
- Translation models **must no longer** define their own translated field lists.


### Migration Notes
- Move any `translation_fields` definitions from translation models
  to `translated_fields` on the corresponding source model.

## [0.1.0]
- Initial release