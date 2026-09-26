---
title: Live updates
requires:
  - naf/websocket
---

# Live updates

A WebSocket server for NAF hosts, written with PHP's stream functions and no event loop
library. `stream_socket_server` and `stream_select` do the socket work.

```sh
composer require naf/cli
```

Meant to be a supervised program beside a queue worker. It keeps no state, so a restart costs
its clients a reconnect and nothing else.

`naf/cli` is optional for the publisher, but required for `websocket:serve`. The server is
disabled by default and has no signing key. For a local HTTP application, generate a key
with `php -r 'echo bin2hex(random_bytes(32)), PHP_EOL;'`, put it in `.env` as
`WEBSOCKET_KEY=...`, and add this to `app/config.php`:

```php
return ['websocket' => [
    'enabled'     => true,
    'key'         => 'ENV:WEBSOCKET_KEY',
    'address'     => '127.0.0.1:8091',
    'url'         => 'ws://127.0.0.1:8091',
    'origins'     => ['http://127.0.0.1:8000'],
    'certificate' => '',
]];
```

Merge the `websocket` key with any existing configuration, then run
`vendor/bin/naf websocket:serve`. `Naf\Websocket\live()` returns true only when the feature
is enabled and a signing key is present. Without both, the command reports that it is off
and exits. The web process and server must use the same key and `websocket:control` socket
path. For HTTPS, configure `websocket:certificate` and `websocket:key_file` and expose a
`wss://` URL; list the allowed page origins explicitly. The shipped certificate path is
environment-specific and the empty origins list accepts any origin.

## It carries that something changed, never what

A message says which channel and which revision. Whoever receives it fetches the new state
through the application's ordinary, already-authorised HTTP path — with the session and the
permissions it has always had.

So the server holds no authority. There is nothing in it to leak, a bug in it cannot become a
disclosure, and an installation that switches it off loses live updates and nothing else.

```php
use function Naf\Websocket\publisher;

publisher()->publish('project:4', ['revision' => '187']);
```

One line of JSON into a Unix socket. Not a port, so it needs no secret; not a queue, so there
is nothing to drain. `publish()` returns `false` if the socket is unavailable and bounds the
connection attempt to 50 milliseconds, so a restarting server does not fail a request.

## Why it has its own port

Behind a reverse proxy, TLS and origin checks are somebody else's job. On its own port they
are nobody's unless they are here, so the server does both. An installation that would rather
proxy it still can.

## Authorisation

The server has no session and no database. It cannot ask whether somebody may listen to a
channel, so it does not: the application answers that while it still has a request, and writes
the answer into a short-lived signed token.

```php
use function Naf\Websocket\token;

$token = token((string) $userId, ['project:4']);
```

A connection may join what its token names, and nothing else. The token is an HMAC over the
subject, the channels and an expiry, so the server verifies it without asking anybody.

Short-lived means a reconnect needs a new one, and the client asks the host for it over HTTP,
where a session still exists. The host decides what that costs: somebody who has been signed
out or removed from a board is simply not given another token, and the client stops asking.
Where to ask is in the page, because only the host knows its own routes.

The browser module `websocket.js` spends the token in its page once and asks for a new one
before every reconnect. `token.js` holds the rule for which answer means *retry* and which
means *give up*, with tests of its own — that distinction is easy to get subtly wrong and
impossible to notice.

## Presence

One channel prefix is the exception the server makes: a channel named `presence:…` is the only
one whose name it reads. Everywhere else a channel is an opaque string the application chose.

The exception buys a great deal. The server already knows who is connected and to what, so a
roster needs no heartbeat from the page, no endpoint to poll and nothing stored anywhere:
joining is the whole subscription and closing the tab is the whole unsubscribe. It counts
people rather than connections, so three tabs are one colleague and closing two of them is not
leaving.

A connection on such a channel is sent `presence.here` with the roster, and the others are
sent `presence.joined`. Departures are `presence.left`.

### The one thing a client may say

Where somebody is looking exists only in their own browser, so that half is said rather than
observed. It is the only message a client may send, and a page sends it by dispatching an
event rather than importing anything:

```js
document.dispatchEvent(new CustomEvent('naf:websocket-say', { detail: { at: 'board' } }));
```

What that buys a liar is nothing. The subject comes from the token and never from the message,
so nobody can speak as somebody else; it reaches only presence channels the connection already
holds; it is capped; and it is not stored. A test sends a message claiming somebody else's
subject and asserts it arrives as its own.

## Hardening

The handshake and the frame reader are written against what a hostile client sends rather than
what a friendly one does: a head that never ends, a frame announcing a gigabyte, a client that
stops mid-frame, a masked frame from a server, an unmasked frame from a client. Each has a
test and a close code.
