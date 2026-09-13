---
title: Translations
requires:
  - naf/i18n
---

# Translations

Text in more than one language, kept in JSON files rather than in the code. A key goes
in, the string for the current language comes out, and a missing key falls back rather
than breaking the page.

Variables are substituted into the string, so a translator moves them around the sentence
instead of you concatenating fragments in the order English happens to use.

## Translating a string

```php
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
a key literally called `nav.home`, which is a perfectly good way to organise a flat file.

## Putting values into a sentence

```php
echo t('greeting', ['name' => 'John']);
```

```json
{
  "greeting": "Hello, :name!"
}
```

The placeholder is `:name`, and it can sit anywhere in the sentence. That is the point:
a translator moves it to where their language wants it instead of you concatenating
fragments in the order English happens to use.

Values that are neither scalar nor `Stringable` are skipped rather than converted, so an
array passed by accident leaves the placeholder standing instead of printing `Array`.

## When a key is missing

`t()` returns the key itself:

```php
t('checkout.confirm')   // → "checkout.confirm" when the key is not in the file
```

Untranslated text shows up in the interface rather than as an empty space, which is what
you want while a translation is still being written.

A missing **file** is a different matter: asking for a language whose JSON does not exist
throws a `LogicException`, and so does a file that is not valid JSON. That is deliberate —
a typo in a language code should fail at once, not silently serve English to everybody.

## Choosing the language

The language is detected once per request, in this order:

1. the `lang` query parameter — `/page?lang=de`
2. a `lang` cookie
3. the browser's `Accept-Language` header, best match first

Whatever is found is written back as a cookie, so the choice survives the next request
without the query parameter.

To set it yourself:

```php
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

```php
'language'          => null,        // forced language; null means detect
'fallback_language' => 'en',        // used when nothing was detected
'app' => [
    'translationPath' => '/app/Resources/lang',
],
```

`translationPath` is relative to your application's base path. One JSON file per language,
named by its code.
