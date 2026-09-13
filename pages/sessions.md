---
title: Sessions
requires:
  - naf/session
---

# Session

NAF provides a minimal but powerful session management system.  
You can easily work with session data, flash messages, and session control.

Sessions are only started manually when you actually need them.

---

## Starting a Session

To start the PHP session, use the `session()` helper:

```php
use function Naf\session;

session()->start();
```

- This starts `$_SESSION` if not already active.
- You control exactly when session management begins.

---

## Setting and Getting Session Data

Set a session value:

```php
session()->set('user_id', 42);
```

Retrieve a session value:

```php
$userId = session()->get('user_id');
```

Retrieve a value with a default fallback:

```php
$language = session()->get('language', 'en');
```

---

## Flash Messages

Flash messages are stored temporarily and removed after the next access.  
Useful for one-time notifications like success or error messages.

Set a flash message:

```php
session()->flash('success', 'Your profile has been updated.');
```

Retrieve and automatically delete a flash message:

```php
$successMessage = session()->getFlash('success');
```

- After calling `getFlash()`, the flash value is deleted automatically.
- If no flash message is found, the optional default value is returned.

---

## Forgetting Session Data

To manually remove a value from the session:

```php
session()->forget('user_id');
```

- Useful for logging out users or cleaning up session data manually.

---

## Summary

- Sessions are manually started via `session()->start()`.
- Set and retrieve session data easily.
- Flash messages are built in via `flash()` and `getFlash()`.
- Sessions remain under your full control — only active when you want them.
