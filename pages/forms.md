---
title: Forms and validation
requires:
  - naf/form
---

# Forms and validation

`naf/form` provides validation, error display helpers and request-value helpers. It also
checks CSRF tokens before controllers handle POST, PUT and DELETE requests. The current
listener does not check PATCH.

Use the examples in a bootstrapped application. Template examples assume the starter's
`naf/view` package for HTML escaping; validation itself does not require View.

## Requirements and compatibility { #use-the-corrected-helper-release }

The template helpers in this guide require `naf/form` **0.2.1+**. Update an older
installation with:

```bash
composer require 'naf/form:^0.2.1'
```

Starter 0.2.2 includes compatible dependencies. See [Installation](install.md) for updating
an older application.

## Import helpers { #the-helpers-are-namespaced }

Every helper lives in `Naf\Form`. Templates import the ones they use:

```php
<?php
use function Naf\Form\{csrf, error, has_error, memory, validator};
```

Imports are local to each PHP file. Calling a helper without its namespace or import
produces an undefined-function error.

## Validation

Pass input and field rules to the shared validator. `param()->all()` combines body and
query data; use the request body accessor when the input source matters:

```php-inline
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

`min` and `max` permit empty values. Combine them with `required` when the field must be
present and nonempty. Validate input types before rules that expect text.

### Your own messages

```php-inline
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

```php-inline
use Naf\Form\Core\Validator;

Validator::register('starts_with', function ($value, $param) {
    return str_starts_with((string) $value, $param);
}, "Value must start with '%s'.");
```

Register it once, during boot, and use it like any built-in rule: `'ref' => 'starts_with:INV-'`.

## Display validation errors { #showing-what-went-wrong }

```html+php
<input name="email" class="<?= error_class('email', validator()) ?>">
<?php if (has_error('email', validator())): ?>
    <span class="error"><?= error('email', validator()) ?></span>
<?php endif ?>
```

- `error($field, $validator)` — an HTML `div.error-msg` containing the field messages on POST, or `null`
- `has_error($field, $validator)` — whether the field has one
- `error_class($field, $validator)` — the configured error class for a field
- `is_post()` — whether this request was a POST, for the usual `if (is_post())` branch

## Redisplay submitted values { #putting-back-what-was-typed }

A failed validation should not empty the form. `memory()` reads the **current request**
through `param()`. It neither escapes the value nor persists it across a redirect.
For HTML, escape it with `s()` from `naf/view`, or `htmlspecialchars()` yourself:

```html+php
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

Generate one token per rendered page and reuse it across forms. In a template:

```html+php
<?php
use function Naf\Form\csrf;
use function Naf\View\s;

$token = csrf()->generate();
?>
<form method="post">
    <input type="hidden" name="_csrf" value="<?= s($token) ?>">
    <!-- Application fields -->
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

Since Form 0.2.3, an `Authorization` header does not bypass CSRF validation. Protocol endpoints
that authenticate independently of browser cookies need an exact route exemption, as shown
below. The endpoint must still validate its credentials and reject invalid tokens even when
the caller has a valid browser session.

### Routes that authenticate some other way

For protocol endpoints that authenticate independently of browser cookies, configure
explicit exemptions in the array returned by `app/config.php`:

```php-inline
'csrf_exempt_routes' => [
    'oauth.token' => true,
],
```

It is a map rather than a list so that several plugins can contribute to it without one
overwriting another by position — and so an application can switch a plugin's exemption
back off with `false`.

OAuth Server contributes its protocol exemptions. MCP 0.2.5+ also contributes the exact
`mcp_server_rpc` POST route exemption, so those integrations need no duplicate host setting.

Exemptions match exact route names, not paths or prefixes. Review the endpoint's own
authentication before exempting it.

### Turning it off

```php-inline
'csrf_validation' => false,
```

This disables the listener globally. Use it only when the application does not rely on
browser-attached credentials. Prefer named exemptions for mixed browser/API applications.

## Services and request timing { #how-it-works }

The plugin registers the built-in validator rules through the container, extends the guard
with a CSRF service, hooks the check into `Event::CONTROLLER_CALLING`, and provides the view
helpers. CSRF tokens are stored in the session, which is why `naf/session` comes along.
Remembered input is read from the current request, not from the session.

Built-in validation rules and CSRF checking are registered automatically. Application
validation rules, tokens in forms and any exemptions still require application code.
