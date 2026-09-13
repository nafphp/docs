---
title: Forms and validation
requires:
  - naf/form
---

# Forms and validation

`naf/form` covers the three things a form needs beyond HTML: validating what came in,
showing what went wrong, and putting back what the person already typed. It also protects
POST, PUT and DELETE requests with a CSRF token, without you registering anything.
PATCH is not checked by the current listener.

## Use the corrected helper release

Use `naf/form` **0.2.1 or newer**. Version 0.2.0's `is_post()` asked the container for a
removed string service key, which also broke `error()` and `error_class()`. Upgrade an older
installation with:

```bash
composer require 'naf/form:^0.2.1'
```

No compatibility alias is needed with 0.2.1. Starter 0.2.2 already includes a newer compatible
version; see [Installation](install.md) when updating an older starter.

## The helpers are namespaced

Every helper lives in `Naf\Form`. Templates import the ones they use:

```php
<?php
use function Naf\Form\{csrf, error, has_error, memory, validator};
```

They are not global. A template that calls `memory()` without importing it will fail with
an undefined-function error, and that is the single most common surprise with this plugin.

## Validation

Hand the request body and a set of rules to the validator:

```php
use function Naf\Form\validator;
use function Naf\param;

validator()->validate(param()->all(), [
    'email'    => 'required|email',
    'password' => 'required|min:8',
]);

if (validator()->isValid()) {
    // continue
}
```

`validator()` returns the same instance for the whole request, so the view can ask it about
errors later without you passing it around.

### Built-in rules

| Rule | Passes when | Default message |
|---|---|---|
| `required` | the value is not empty | Field is required. |
| `email` | `FILTER_VALIDATE_EMAIL` accepts it | Please enter a valid email address. |
| `min:n` | the value is empty, or at least `n` characters | At least %d characters. |
| `max:n` | the value is empty, or at most `n` characters | Maximum of %d characters. |
| `boolean` | it reads as a boolean | Is not a boolean value. |

`min` and `max` pass on an empty value on purpose: whether a field may be empty at all is
`required`'s question, and answering it twice produces two messages for one mistake.

### Your own messages

```php
use function Naf\Form\validator;
use function Naf\param;

validator()->validate(param()->all(), [
    'name' => 'required|min:3',
], [
    'name' => [
        'required' => 'Please enter your name.',
        'min'      => 'At least %s characters.',
    ],
]);
```

### Your own rules

```php
use Naf\Form\Core\Validator;

Validator::register('starts_with', function ($value, $param) {
    return str_starts_with((string) $value, $param);
}, "Value must start with '%s'.");
```

Register it once, during boot, and use it like any built-in rule: `'ref' => 'starts_with:INV-'`.

## Showing what went wrong

```php
<input name="email" class="<?= error_class('email', validator()) ?>">
<?php if (has_error('email', validator())): ?>
    <span class="error"><?= error('email', validator()) ?></span>
<?php endif ?>
```

- `error($field, $validator)` — an HTML `div.error-msg` containing the field messages on POST, or `null`
- `has_error($field, $validator)` — whether the field has one
- `error_class($field, $validator)` — a class name to hang styling on
- `is_post()` — whether this request was a POST, for the usual `if (is_post())` branch

## Putting back what was typed

A failed validation should not empty the form. `memory()` reads the **current request**
through `param()`. It neither escapes the value nor persists it across a redirect.
For HTML, escape it with `s()` from `naf/view`, or `htmlspecialchars()` yourself:

```php
<?php
use function Naf\Form\{memory, memory_checked, memory_selected};
use function Naf\View\s;
?>
<input name="email" value="<?= s(memory('email')) ?>">
<input type="checkbox" name="agree" <?= memory_checked('agree') ?>>
<option value="de" <?= memory_selected('country', 'de') ?>>Germany</option>
```

`memory_checked()` and `memory_selected()` return the whole attribute or an empty string,
so they can be dropped into the tag without a conditional.

## CSRF protection

Put a token in every form that changes something:

```php
<form method="post">
    <input type="hidden" name="_csrf" value="<?= csrf()->generate() ?>">
    <!-- your fields -->
</form>
```

The check runs before your controller. Every `generate()` replaces the previous session
token. Generate once and reuse the result for multiple forms on one page; opening another
form page can invalidate the earlier token.

### What is checked, and when

The plugin listens on `Event::CONTROLLER_CALLING` and inspects **POST, PUT and DELETE**
requests. Anything else passes untouched. The token is read from the `_csrf` body field, or
from an `X-CSRF-Token` header for requests that send JSON rather than a form.

A missing token aborts with **400 CSRF token missing**, an invalid one with
**400 CSRF token invalid** — in both cases before the controller runs.

### Requests that carry their own credentials

A request whose `Authorization` header begins with `Bearer ` is let through by the CSRF
listener. This does **not** validate the token or authenticate the caller: the endpoint
must perform its own bearer authentication and must not fall back to a cookie login.

Only `Bearer`. A browser attaches cookies and Basic credentials by itself, so a request
carrying those is exactly the kind CSRF exists to stop — the header was never proof of
anything, and treating *any* `Authorization` header as a pass made the header itself the
bypass. Nothing attaches a Bearer token automatically, so a request that has one was built
deliberately by whoever holds it.

### Routes that authenticate some other way

A protocol endpoint called by a program carries no session to ride on and no form to put a
token in. A CSRF check there refuses legitimate requests while protecting nothing. Name
such routes one at a time:

```php
'csrf_exempt_routes' => [
    'oauth.token' => true,
],
```

It is a map rather than a list so that several plugins can contribute to it without one
overwriting another by position — and so an application can switch a plugin's exemption
back off with `false`.

Routes are named, never guessed from a path. There is no pattern matching here, and that is
deliberate: a prefix rule exempts endpoints nobody remembered adding.

### Turning it off

```php
'csrf_validation' => false,
```

For a service with no browser clients at all. If some of your endpoints need it and others
do not, exempt those routes instead.

## How it works

The plugin registers the built-in validator rules through the container, extends the guard
with a CSRF service, hooks the check into `Event::CONTROLLER_CALLING`, and provides the view
helpers. CSRF tokens are stored in the session, which is why `naf/session` comes along.
Remembered input is read from the current request, not from the session.

None of it needs configuration.
