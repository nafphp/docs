---
title: Sessions
requires:
  - naf/session
---

# Sessions

`naf/session` stores data between HTTP requests and provides flash messages and session ID
regeneration. Installing it starts a session during HTTP boot; startup is not deferred until
the first write. CLI boot does not start a session automatically.

The default storage is PHP's session handler. Configure shared storage for multiple servers.
Form `memory()` values are separate: they come from the current request, not session storage.

## Reading and writing

```php-inline
use function Naf\Session\session;

session()->set('user_id', 42);

$id       = session()->get('user_id');
$language = session()->get('language', 'en');   // default when the key is absent

session()->forget('user_id');
session()->clear();                              // end the session
```

`clear()` empties the session, destroys it in the session store and expires the session
cookie. Values set later in the same request are not saved. It does nothing when no session
is active. To sign a user out but keep carts or flash messages, use `auth()->logout()`
from [Authentication](auth.md#sessions) instead.

Keys are flat strings. `set()` writes into `$_SESSION`; values must be serializable by PHP.
Keep session data small and avoid retaining stale entities or permission snapshots.

## Flash messages { #messages-that-should-appear-once }

```php-inline
session()->flash('success', 'Your profile has been updated.');
```

```php-inline
$message = session()->getFlash('success');       // returns it and deletes it
```

`getFlash()` removes the value as it reads it, so a refresh does not show the message
again. Read it once and put it in a variable — asking twice gives you the default the
second time.

## Regenerating the session id

```php-inline
session()->regenerate();
```

Requests a new session ID and deletes the old session when regeneration is permitted.
Regenerate when the trust level changes, such as login or privilege elevation. The Auth
session adapter performs and verifies its own rotation during login.

The helper normally permits regeneration at most once per 300 seconds. A call within the
interval can leave the ID unchanged; do not treat every call as proof that rotation occurred.
Pass another interval when the application needs different timing:

```php-inline
session()->regenerate(60);
```

## Storing sessions in the database

The default handler is PHP's own: files in whatever `session.save_path` points at. Configure shared storage when requests can reach
servers that do not share those files.

```php-inline
'session' => [
    'storage'        => 'database',
    'database_table' => 'sessions',
],
```

This needs `naf/database`, and the table needs creating — the plugin registers a migration
for it. Install `naf/cli` as well to run the migration with `vendor/bin/naf db:migrate up`;
see [Migrations](database.md#migrations).

If `naf/database` is absent, the plugin logs a warning and retains the default handler.
Verify the selected handler and application log after changing storage.

## Behind a proxy

A load balancer terminating TLS speaks plain HTTP to your application, which then believes
the connection was insecure and sets a cookie without the `Secure` flag.

```php-inline
'session' => [
    'trust_proxy_headers' => true,
    'trusted_proxies'     => ['10.0.0.1'],
],
```

Enable header trust only with an explicit list of trusted proxy addresses. Clients can
supply `X-Forwarded-Proto`; accept it only from the configured proxies.
