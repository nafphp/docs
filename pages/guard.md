---
title: Guard
---

# Guard

The guard is a registry of small validation functions. Core rules cover paths and HTML output;
plugins can add rules of their own.

```php
use function Naf\guard;

$path = guard()->safePath('user.profile');
$text = guard()->safeOutput('<script>'); // &lt;script&gt;
```

## Path validation

`safePath()` rejects empty paths, `..`, absolute paths, stream wrappers and characters outside
`[A-Za-z0-9_/.-]`. It throws `InvalidArgumentException` on rejection.

This is a lexical path check, not a filesystem sandbox: it does not resolve symlinks or prove
that an existing file is inside an allowed directory. Check that separately for file access.

## HTML escaping

`safeOutput()` uses `htmlspecialchars()` with `ENT_QUOTES` and UTF-8. It accepts a string or
a flat array of string values; nested arrays are not recursively supported. The view plugin's
`Naf\View\s()` helper delegates to it.

Core guard rules are registered for HTTP requests, not during normal CLI boot. If you render
HTML in a command, use an appropriate explicit escaping function or register the required rules.

## CSRF comes from naf/form

`guard()->csrf()` is registered by `naf/form`, which also installs `naf/session`. It is not
available in a core-only application. Prefer the form helper in templates:

```php
<?php use function Naf\Form\csrf; ?>
<input type="hidden" name="_csrf" value="<?= csrf()->generate() ?>">
```

Every `generate()` call creates a new token and replaces the session's previous one. If a
page contains multiple forms, generate once and reuse that value for the page. Generating a
new token in another tab invalidates the earlier tab's token.

See [Forms and validation](forms.md#csrf-protection) for the actual checked methods,
header support and named-route exemptions.

## Register a rule

```php
use function Naf\guard;

guard()->register('positiveId', function (int $id): int {
    if ($id < 1) {
        throw new \InvalidArgumentException('An ID must be positive.');
    }
    return $id;
});

$id = guard()->positiveId(42);
```
