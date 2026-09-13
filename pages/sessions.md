---
title: Sessions
requires:
  - naf/session
---

# Sessions

Data that has to survive from one request to the next: who is signed in, what somebody
typed into the form that failed validation, the message that should appear once and then
not again.

Sessions start when you ask for one, not on every request. That is deliberate — a session
started for a visitor who never needed one is a cookie you have to explain and a file you
have to clean up.

## Starting a Session

To start the PHP session, use the `session()` helper:

```php
use function Naf\Session\session;

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

## Configuration

`src/config.php` exposes the following keys:

```php
return [
    'session' => [
        'storage'             => 'default', // switch to 'database' when using naf/database
        'trust_proxy_headers' => false,
        'trusted_proxies'     => [],
        'database_table'      => 'sessions',
    ],
];
```

To use the database handler:

1. Install [naf/database](https://github.com/nafphp/database) and configure its `database` settings.
2. Update the `session` config’s `storage` key to `database`.
3. Run `vendor/bin/nix migrate up` (requires `naf/cli`) to apply the migration that creates the sessions table.

---

## Optional Usage in Controllers

You can also access the session directly from the container:

```php
$session = app()->container()->get(Session::class);
```

But using the `session()` helper is the recommended way.

---

---

## How it works

* Automatically starts `session_start()` for web requests, with hardened cookie parameters and domain normalization.
* Offers `Session::regenerate()` so you can refresh the session ID during login flows without touching every request.
* Flash data is stored in a dedicated key and removed after access.
* Registers the `session()` helper and binds it in the service container.
* Provides `DatabaseSessionHandler` when the database plugin is configured.
* Registers the migration path with `naf/database` so `vendor/bin/nix migrate up/down` applies the session table changes.

---
