---
title: Forms and validation
requires:
  - naf/form
---

# Forms and validation

`naf/form` validates submitted values, displays field errors, refills form fields and
protects state-changing browser requests with CSRF tokens. Since Form **0.2.3**, the CSRF
check runs for every request method except GET, HEAD and OPTIONS, including PATCH.

Use the examples in a bootstrapped application. Template examples assume the starter's
`naf/view` package for HTML escaping; validation itself does not require View.

Starter 0.2.4 includes Form 0.2.4 and the CSRF behaviour described here. For older
applications, see the [version notes](#use-the-corrected-helper-release).

## Quick start

A controller validates the request body and returns the form again with its errors:

```php-inline
use function Naf\Form\validator;
use function Naf\View\render;
use function Naf\request;

$check = validator()->validate((array) request()->getParsedBody(), [
    'email'   => 'required|string|email',
    'message' => 'required|string|min:10|max:2000',
]);

if (!$check->isValid()) {
    return render('contact', ['check' => $check])->withStatus(422);
}
```

The template prints a CSRF token, refills the fields and shows the errors:

```html+php
<?php
use function Naf\Form\{csrf, error, error_class, memory};
use function Naf\View\s;
?>
<form method="post">
    <input type="hidden" name="_csrf" value="<?= s(csrf()->token()) ?>">

    <input name="email" class="<?= error_class('email', $check) ?>"
           value="<?= s(memory('email') ?? '') ?>">
    <?= error('email', $check) ?>

    <textarea name="message"><?= s(memory('message') ?? '') ?></textarea>
    <?= error('message', $check) ?>

    <button type="submit">Send</button>
</form>
```

The [contact form](recipes/contact-form.md) builds a complete, tested version of this flow.

## Import helpers { #the-helpers-are-namespaced }

Every helper lives in `Naf\Form`. Templates import the ones they use:

```php
<?php
use function Naf\Form\{csrf, error, error_class, has_error, is_post, memory, validator};
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
    'password' => 'required|string|min:8',
]);

if (validator()->isValid()) {
    // continue
}
```

Rules are a `|`-separated string or an array of rule strings. A parameter follows a colon:
`min:8`. `validate()` clears earlier errors, checks every rule of every field and returns the
validator, so `validator()->validate(...)->isValid()` also works.

`validator()` returns the same instance for the whole request, so the view can ask it about
errors later without you passing it around. `getErrorMessages()` returns all messages by
field; `getErrorMessage('email')` returns one field's list or `null`.

An unknown rule name throws `InvalidArgumentException` ("Validator 'name' not found.")
instead of being skipped.

### Built-in rules

| Rule | Passes when | Default message |
|---|---|---|
| `required` | the value is not `null`, `''` or `[]` (`"0"` passes) | Field is required. |
| `string` | the value is a string | Must be text. |
| `array` | the value is an array | Must be an array. |
| `integer` | an integer, or a string that `FILTER_VALIDATE_INT` accepts | Must be an integer. |
| `email` | a string that `FILTER_VALIDATE_EMAIL` accepts | Please enter a valid email address. |
| `min:n` | the value is missing or `''`, or a scalar with at least `n` characters | At least %d characters. |
| `max:n` | the value is missing or `''`, or a scalar with at most `n` characters | Maximum of %d characters. |
| `boolean` | a scalar that `FILTER_VALIDATE_BOOLEAN` recognises (`1`, `true`, `on`, `yes`, `0`, `false`, `off`, `no`) | Is not a boolean value. |
| `date` | a string in `YYYY-MM-DD` form that is a real calendar date | Must be a valid date (YYYY-MM-DD). |

`string`, `array`, `integer` and `date` require Form 0.2.3 or newer. Older releases ship only
`required`, `email`, `min`, `max` and `boolean`, and their `required` uses PHP's `empty()`,
which also rejects `"0"`.

**Only `min` and `max` accept a missing or empty value.** Every other rule fails for a missing
field, so `'website' => 'email'` rejects an empty optional field. Validate optional fields
only when they were submitted, or combine `min`/`max` with your own presence check.

`min` and `max` count characters with `mb_strlen()`, not bytes, and reject arrays. Add
`string` before them when a field must be text: a submitted `name[]=x` is then reported as a
validation error instead of reaching code that expects a string.

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

Messages are passed through `sprintf()` with the rule parameter, so `%s` or `%d` inserts it.

### Your own rules

```php-inline
use Naf\Form\Core\Validator;

Validator::register('starts_with', function ($value, $param) {
    return is_string($value) && str_starts_with($value, (string) $param);
}, "Value must start with '%s'.");
```

Register it once in root `bootstrap.php`, before `app()->run()`, and use it like any
built-in rule: `'ref' => 'starts_with:INV-'`. A rule receives the value (or `null`), the
parameter after the colon (or `null`) and the complete input array. It passes only when it
returns exactly `true`. Use a new name: the built-in rules are registered when the validator
is first resolved and replace registrations with the same name.

## Display validation errors { #showing-what-went-wrong }

```html+php
<input name="email" class="<?= error_class('email', validator()) ?>">
<?php if (has_error('email', validator())): ?>
    <span class="error"><?= error('email', validator()) ?></span>
<?php endif ?>
```

| Helper | Returns |
|---|---|
| `error($field, $validator)` | `<div class="error-msg">` with the field's messages, or `null` |
| `has_error($field, $validator)` | whether `error()` would return markup |
| `error_class($field, $validator)` | the fixed class name `error`, or an empty string |
| `is_post()` | whether the current request method is POST |

The error helpers only report errors for **POST** requests. For a form submitted with PUT or
PATCH (for example through JavaScript), read `$validator->getErrorMessages()` directly.
The class name `error` is not configurable; style it, or use `has_error()` to print your own.
`error()` does not escape the message text. Keep messages under application control.

## Redisplay submitted values { #putting-back-what-was-typed }

A failed validation should not empty the form. `memory()` reads the **current request**
through `param()`. It neither escapes the value nor persists it across a redirect.
For HTML, escape it with `s()` from `naf/view`, or `htmlspecialchars()` yourself:

```html+php
<?php
use function Naf\Form\{memory, memory_checked, memory_selected};
use function Naf\View\s;
?>
<input name="email" value="<?= s(memory('email') ?? '') ?>">
<input type="checkbox" name="agree" <?= memory_checked('agree') ?>>
<option value="de" <?= memory_selected('country', 'de') ?>>Germany</option>
```

`memory_checked()` and `memory_selected()` return the whole attribute or an empty string,
so they can be dropped into the tag without a conditional. `memory_checked($key, $value)`
compares strictly with `$value` (default `'on'`).

Since Form 0.2.4, `memory($key, $default)` returns submitted strings unchanged and integers
or floats as strings. A missing field, array or other unsupported value returns the default;
a scalar default is converted to a string, and a non-scalar default produces `null`.
For example, `memory('country', 'de')` returns `'de'` for a missing field or `country[]=x`.
For fields that legitimately contain arrays, read the parsed body or `param()` directly.

## CSRF protection

The plugin rejects state-changing browser requests that do not carry the session's token.
Render the token in every form:

```html+php
<?php
use function Naf\Form\csrf;
use function Naf\View\s;
?>
<form method="post">
    <input type="hidden" name="_csrf" value="<?= s(csrf()->token()) ?>">
    <!-- Application fields -->
</form>
```

`csrf()->token()` returns the token already stored in the session and creates one only when
none exists. Several forms on one page and several open tabs therefore share one valid
token. `csrf()->generate()` always creates a new token and replaces the stored one; forms
rendered earlier, including those in other tabs, stop validating. Use `generate()` only when
you deliberately rotate the token. `csrf()->token()` needs Form 0.2.3 or newer; on older
versions call `generate()` once per page and reuse its value for every form on that page.

### What is checked, and when

The plugin listens on `Event::CONTROLLER_CALLING`, so the check runs after a route matched
and before the controller or closure is called.

| Form version | Checked methods |
|---|---|
| 0.2.3 and newer | every method except GET, HEAD and OPTIONS, including PATCH |
| 0.2.2 and older | POST, PUT and DELETE only |

The token is read from the `_csrf` body field. When the parsed body has no `_csrf` field,
the plugin reads the `X-CSRF-Token` header instead, which suits `fetch()` requests that send
JSON:

```js
fetch('/api/notes', {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json', 'X-CSRF-Token': token},
    body: JSON.stringify({title: 'Updated'}),
});
```

| Request | Response |
|---|---|
| No token, an empty token, a non-string value or more than 1024 characters | **400** `CSRF token missing or malformed.` |
| A token that does not match the session's token | **400** `CSRF token invalid.` |

Both responses are raised with `abort()` before your controller runs, so they reach the
normal [error handling](errors.md). A request whose route does not exist is answered with
404 before the check.

### Requests that carry their own credentials

Since Form 0.2.3, an `Authorization` header does not bypass CSRF validation. In 0.2.2 and
older, a header starting with `Bearer ` skipped the check. Protocol endpoints that
authenticate independently of browser cookies need an exact route exemption, as shown
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
back off with `false`. Only the value `true` exempts a route.

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

## Configuration

| Key | Type | Default | Effect |
|---|---|---|---|
| `csrf_validation` | bool | `true` | `false` disables the CSRF listener for every route |
| `csrf_exempt_routes` | map of route name → bool | `[]` | Routes whose value is `true` skip the CSRF check |

## Services and request timing { #how-it-works }

The plugin registers the validator (`Naf\Form\Core\Validator`) in the container, adds the
built-in rules when the validator is first resolved, extends the guard with a `csrf` rule,
hooks the check into `Event::CONTROLLER_CALLING` and provides the template helpers. CSRF
tokens are stored in the session under `_csrf`, which is why `naf/session` comes along.
Remembered input is read from the current request, not from the session.

Built-in validation rules and CSRF checking are registered automatically. Application
validation rules, tokens in forms and any exemptions still require application code.

## If the result is different

| What you see | What to check |
|---|---|
| 400 `CSRF token missing or malformed.` | The form has a `_csrf` field (or the request an `X-CSRF-Token` header) and the client keeps the session cookie |
| 400 `CSRF token invalid.` | Another page called `csrf()->generate()` and replaced the token; use `token()`, or reload the form |
| PATCH requests suddenly return 400 | Form 0.2.3 checks PATCH; send the token in `_csrf` or `X-CSRF-Token` |
| `Validator 'x' not found.` | Check the rule name and register custom rules before validating |
| An optional empty field reports an error | Only `min` and `max` accept empty values; skip the other rules when the field is absent |
| `error()` prints nothing for a PUT form | The error helpers report errors for POST only; use `getErrorMessages()` |

[Troubleshooting](troubleshooting.md#forms-and-sessions) has further checks for tokens,
cookies and form values.

## Version notes { #use-the-corrected-helper-release }

??? note "Older Form releases"

    The template helpers in this guide require `naf/form` **0.2.1+**; `csrf()->token()`, the
    `string`, `array`, `integer` and `date` rules, the type-safe `required`/`min`/`max` checks
    and the PATCH check require **0.2.3+**.
    `memory()` honours defaults and handles array input without a `TypeError` in **0.2.4+**.
    In 0.2.3 and older, the default is ignored and array input can cause a 500 response.
    Starters 0.2.2 and 0.2.3 lock Form 0.2.2, which lacks `token()` and checks only
    POST/PUT/DELETE; it also lets a Bearer header bypass CSRF. Update an older installation with:

    ```bash
    composer require 'naf/form:^0.2.4'
    ```

    See [Installation](install.md#starter-versions-and-updates) for updating an older
    application.
