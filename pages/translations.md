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

## Translate

```php
echo t('welcome');
```

Assuming `app/Resources/lang/en.json` contains:

```json
{
  "welcome": "Welcome to our site!"
}
```

You’ll see:
`Welcome to our site!`

---

## With replacements

```php
echo t('greeting', ['name' => 'John']);
```

With this JSON entry:

```json
{
  "greeting": "Hello, :name!"
}
```

Result:
`Hello, John!`

---

## Switch language

```php
use Naf\I18n\Support\Language;

t()->setLanguage(Language::DE);
```

Make sure `app/Resources/lang/de.json` exists.

#### Through query parameter

```php
/index.php?lang=de
```

> An event listener will set the language based on the query parameter within a cookie.

---

## Fallback

If a key is missing, the key itself is returned:

```php
translator()->get('unknown_key');
// → "unknown_key"
```

This helps you spot missing translations during development.

---

## File structure

```
app/
└── Resources/
    └── lang/
        ├── en.json
        ├── de.json
        └── fr.json
```

Each file should be a flat key-value map using UTF-8 encoded JSON.

---
