---
title: WebSocket notifications
requires:
  - naf/websocket
---

# WebSocket notifications { #live-updates }

`naf/websocket` provides a supervised PHP WebSocket server for application notifications.
It uses PHP streams and runs as a separate process beside the HTTP application. Clients
receive change notifications and fetch authorized data through the application's HTTP routes.

`naf/cli` is optional for publishing but required for `websocket:serve`. The server is disabled
by default and needs a signing key. For local setup, generate a key with
`php -r 'echo bin2hex(random_bytes(32)), PHP_EOL;'`, put it in `.env` as
`WEBSOCKET_KEY=...`, then configure the server as shown below.


Add this fragment to `app/config.php`:

```php-inline
return ['websocket' => [
    'enabled'     => true,
    'key'         => 'ENV:WEBSOCKET_KEY',
    'address'     => '127.0.0.1:8091',
    'url'         => 'ws://127.0.0.1:8091',
    'origins'     => ['http://127.0.0.1:8000'],
    'certificate' => '',
]];
```

Merge the `websocket` key with existing configuration, install `naf/cli`, and run
`vendor/bin/naf websocket:serve`. The command exits when the feature is disabled or its signing
key is absent. The web process and server must use the same key and `websocket:control` socket.
For HTTPS, configure `websocket:certificate` and `websocket:key_file`, expose `wss://`, and
list allowed page origins explicitly. An empty origins list accepts any origin.

Before including live-update controls or issuing a page token, check whether the feature
is configured:

```php-inline
use function Naf\Websocket\live;

if (live()) {
    // Include this application's live-update controls.
}
```

`live()` requires an enabled flag and a nonempty signing key. It recognizes environment
strings such as `true` and `false`; it does not probe the server or guarantee message
delivery. A failed publication still needs the handling described below.

## Change notifications { #it-carries-that-something-changed-never-what }

A message says which channel and which revision. Whoever receives it fetches the new state
through the application's ordinary, already-authorised HTTP path — with the session and the
permissions it has always had.

Keep notification payloads limited to identifiers or revisions. The server transports the
payload the publisher supplies; it does not independently remove sensitive fields. Authorize
all subsequent HTTP reads and protect the local publishing socket.

```php-inline
use function Naf\Websocket\publisher;

publisher()->publish('project:4', ['revision' => '187']);
```

The publisher sends JSON through a Unix socket. `publish()` returns false if it is unavailable
and bounds connection attempts to 50 milliseconds. Protect that socket with filesystem access
controls and monitor failed publications if notification delivery matters.

## Why it has its own port

The server can handle TLS and origin checks on its own listener. A reverse proxy can also
terminate TLS; configure the externally visible URL and allowed origins for that deployment.

## Authorisation

The server does not load application sessions or account permissions. The HTTP application
must authorize the requested channels before issuing a short-lived signed token. This
fragment assumes `$userId` is the authenticated account and access to project 4 was checked:

```php-inline
use function Naf\Websocket\token;

$token = token((string) $userId, ['project:4']);
```

The token signs the subject, channels and expiry with HMAC. The server permits only the
channels listed in it. Permission changes do not rewrite an already issued token; use
short lifetimes and authorize token renewal.

The browser module `websocket.js` uses its page token once, then requests a new token before
each reconnect. The host supplies the renewal URL and checks the current session and channel
permissions there. Return an authorization failure when the account can no longer connect.
The module's `token.js` distinguishes retryable renewal failures from terminal denials.

## Presence

One channel prefix is the exception the server makes: a channel named `presence:…` is the only
one whose name it reads. Everywhere else a channel is an opaque string the application chose.

Presence is derived from current connections. It counts subjects rather than tabs, so
multiple connections for one subject appear as one member. Server restarts clear this
in-memory state and clients must reconnect.

A connection on such a channel is sent `presence.here` with the roster, and the others are
sent `presence.joined`. Departures are `presence.left`.

### The one thing a client may say

Clients can report a transient presence location. The page sends it through a browser event:

```js
document.dispatchEvent(new CustomEvent('naf:websocket-say', { detail: { at: 'board' } }));
```

The subject comes from the verified token, not client-supplied message fields. Messages
are bounded and sent only to the connection's authorized presence channels. They are not
persisted; do not use them as durable activity records.

## Hardening

The server limits handshake and frame sizes and rejects invalid framing. These checks do
not replace deployment access controls, TLS configuration or application authorization.
Supervise the process and verify reconnect behavior in the consuming application.
