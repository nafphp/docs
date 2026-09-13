---
title: Sessions
requires:
  - naf/session
---

# Sessions

Data that has to survive from one request to the next: who is signed in, what somebody
typed into the form that failed validation, the message that should appear once and then
not again.

Installing this package means every web request gets a session. The plugin starts one
during boot — you do not call `start()` yourself, and there is no lazy mode that waits
until something is written.

## Reading and writing

```php
use function Naf\Session\session;

session()->set('user_id', 42);

$id       = session()->get('user_id');
$language = session()->get('language', 'en');   // default when the key is absent

session()->forget('user_id');
session()->clear();                              // everything
```

Keys are flat strings. `set()` writes straight into `$_SESSION`, so anything PHP can
serialise goes in — but a session is a file read and written on every request, which is an
argument for keeping it small.

## Messages that should appear once

```php
session()->flash('success', 'Your profile has been updated.');
```

```php
$message = session()->getFlash('success');       // returns it and deletes it
```

`getFlash()` removes the value as it reads it, so a refresh does not show the message
again. Read it once and put it in a variable — asking twice gives you the default the
second time.

## Regenerating the session id

```php
session()->regenerate();
```

Issues a new session id and discards the old one, which is what closes the door on session
fixation: an attacker who planted an id before sign-in no longer holds a valid one after.
Call it when the trust level changes — at sign-in, at sign-out, when somebody becomes an
administrator.

It is rate-limited. The default refuses to regenerate more than once every 300 seconds, so
calling it on every request is harmless rather than a way to lose sessions. Pass a different
interval if you want another rhythm:

```php
session()->regenerate(60);
```

## Storing sessions in the database

The default handler is PHP's own: files in whatever `session.save_path` points at. That
breaks the moment a second web server enters the picture, because request two lands on a
machine that cannot see request one's file.

```php
'session' => [
    'storage'        => 'database',
    'database_table' => 'sessions',
],
```

This needs `naf/database`, and the table needs creating — the plugin registers a migration
for it, so `naf db:migrate up` has one waiting.

**If `naf/database` is not installed, this fails quietly.** The plugin writes a warning to
the log and carries on with file storage. Your application works, your sessions are in
files, and the only sign is a line in a log nobody reads. Check the log after switching.

## Behind a proxy

A load balancer terminating TLS speaks plain HTTP to your application, which then believes
the connection was insecure and sets a cookie without the `Secure` flag.

```php
'session' => [
    'trust_proxy_headers' => true,
    'trusted_proxies'     => ['10.0.0.1'],
],
```

Both together, and never `trust_proxy_headers` alone: `X-Forwarded-Proto` is a header like
any other, and a client can send it. Trusting it without naming which addresses may set it
lets anybody claim their connection was encrypted.
