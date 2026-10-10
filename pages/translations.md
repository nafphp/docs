---
title: Translations
requires:
  - naf/i18n
---

# Translations

`naf/i18n` loads translations from JSON files and replaces named placeholders. `t()` returns
the translation for the current language, or the key when a translation is unavailable.

Create one file per language under `app/Resources/lang/`, or configure another application
translation path. Language selection is described below.

## Translating a string

```php-inline
use function Naf\I18n\t;

echo t('welcome');
```

with `app/Resources/lang/en.json`:

```json
{
  "welcome": "Welcome to our site!"
}
```

Keys are flat strings — there is no nesting and no dot notation. `t('nav.home')` looks for
a key literally called `nav.home`; the dot is part of its name.

## Placeholder substitution { #putting-values-into-a-sentence }

```php-inline
echo t('greeting', ['name' => 'John']);
```

```json
{
  "greeting": "Hello, :name!"
}
```

Placeholders such as `:name` can appear anywhere in a translation. Keep complete sentences
in the translation file so each language can use its own word order.

Values that are neither scalar nor `Stringable` are skipped rather than converted, so an
array passed by accident leaves the placeholder standing instead of printing `Array`.

## Missing translations { #when-a-key-is-missing }

`t()` returns the key itself:

```php-inline
t('checkout.confirm');  // → "checkout.confirm" when the key is not in the file
```

Missing keys remain visible in the interface. Treat unexpected keys as missing translations
and check the language file and log.

An individual missing file is skipped when another directory provides that language. If no
directory has a file for the chosen language, or a file contains invalid JSON, the translator
logs the problem and has no translations for that language. `t()` then returns each requested
key. Check the application log if a page shows keys unexpectedly; it does not silently switch
to English.

## Choosing the language

For every HTTP request, the plugin selects the language at `request.start`, in this order:

1. the `lang` query parameter — `/page?lang=de`
2. a `lang` cookie
3. the browser's `Accept-Language` header, best match first

When a query parameter is present or no `lang` cookie exists yet, the selected language is
written back as a `lang` cookie (30 days, `SameSite=Lax`), so the choice survives the next
request without the query parameter.

Language codes are reduced to their base language: `de-AT`, `de_AT` and `de` all select
`de.json`. Regional files such as `de-AT.json` are therefore never loaded. A code that is
not two or three letters falls back to `fallback_language`.

To set it yourself:

```php-inline
use Naf\I18n\Support\Language;
use function Naf\I18n\translator;

translator()->setLanguage(Language::DE);
```

`translator()` is the object; `t()` is the shortcut for one translation and takes a key, not
a method call. `lang()` gives you the code currently in effect.

`Language` carries constants for the common ISO 639-1 codes — `EN`, `DE`, `FR`, `ES`, `IT`,
`PT`, `RU`, `ZH`, `JA`, `KO`, `AR`, `HI`, `TR` — but a plain string works just as well:
nothing validates the code against that list.

## Configuration

```php-inline
'language'          => null,        // starting language before detection
'fallback_language' => 'en',        // used when `language` is null and for invalid codes
'app' => [
    'translationPath' => '/app/Resources/lang',
],
```

| Key | Type | Default | Effect |
|---|---|---|---|
| `language` | string or null | `null` | Language the translator starts with. Detection on each HTTP request replaces it as soon as a query parameter, cookie or `Accept-Language` header is present |
| `fallback_language` | string | `en` | Starting language when `language` is `null`, and replacement for invalid codes |
| `app:translationPath` | string | `/app/Resources/lang` | Application translation directory, relative to the project root |

`language` does **not** force a language for web requests: browsers send `Accept-Language`,
and detection overrides the configured value. It mainly matters for CLI code and requests
without any language information. To force a language for a request, call
`translator()->setLanguage()` in your controller, which runs after detection.

## Translations from plugins

A plugin can register a directory of `<language>.json` files in its `bootstrap.php`:

```php-inline
use function Naf\I18n\translation_paths;

translation_paths()->add('acme/blog', __DIR__ . '/app/Resources/lang');
```

Registered directories are read by their `index` (default `100`), then id. Later files
replace matching keys from earlier files; the application's configured translation directory
is always read last. Use `remove('acme/blog')` to unregister a path or pass `replace: true`
to replace an existing id. Changes to the registry reload an already-created translator on
its next translation.

## If the result is different

| What you see | What to check |
|---|---|
| Keys appear instead of text | The language file exists in a translation directory and contains valid JSON; the application log names the problem |
| The configured `language` is ignored | Browsers send `Accept-Language`, which takes precedence; see [Choosing the language](#choosing-the-language) |
| `de-AT.json` is not used | Codes are reduced to their base language; name the file `de.json` |
| A placeholder stays visible | The parameter name matches `:name` and the value is a scalar or `Stringable` |
