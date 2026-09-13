---
title: Forms and validation
requires:
  - naf/form
---

# Forms and validation

The `naf/form` plugin adds form input helpers and CSRF protection to your NAF application.
It makes working with POST requests and form validation simpler and safer.

---

## CSRF Protection

The plugin adds a listener to all `POST`, `PUT`, and `DELETE` requests.
Unless the request contains an `Authorization` header (e.g. for APIs), a valid CSRF token is required.

### Adding the CSRF token to forms

Use the `csrf_token()` helper to insert a token into your form:

```php
<form method="post">
    <input type="hidden" name="_csrf" value="<?= csrf_token() ?>">
    <!-- your fields -->
</form>
```

### What happens automatically

* The plugin listens to the `controller.calling` event.
* It checks if a valid CSRF token is present.
* If the token is missing or invalid, the request is aborted with status code **400**.

You don’t need to register anything manually.

---

### Custom token generation (advanced)

In rare cases, you may want to **manually generate** a token, e.g. for an external JS request or API fallback:

```php
$token = guard()->csrf()->generate();
```

This ensures a valid token is created and stored in the session.

---

## Input Memory

If you want to repopulate form input after a failed submission (e.g. validation failed),
you can use the `memory()` helper:

```php
<input type="text" name="email" value="<?= memory('email') ?>">
```

This function checks if the user submitted a value for this field in the last request and fills it in.

---

## Form Errors

When using a validation system (e.g. the one provided by `naf/form`),
you can use the `formError()` helper to display validation messages:

```php
<?php if ($error = formError('email')): ?>
    <p class="error"><?= $error ?></p>
<?php endif; ?>
```

The helper will return the error message for the given field, if present.

---

## How it works under the hood

* The plugin hooks into the event system to run a CSRF check before each controller.
* The token is stored in the session using the `naf/session` plugin.
* Input data is preserved using the memory service (also session-based).
* Helpers like `memory()` and `csrf_token()` are globally available in views.

---

## Requirements

* `naf/session` must be installed and active
  (`naf/form` depends on it for CSRF and memory handling)

---

## Summary

* ✅ `csrf_token()` inserts a secure token in forms
* ✅ CSRF validation is automatic for all unsafe methods
* ✅ `memory()` restores previous user input after validation
* ✅ `formError()` shows error messages for specific fields