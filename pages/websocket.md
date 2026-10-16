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
Keep the control socket path short enough for the operating system's Unix-domain socket
limit. In particular, a deeply nested macOS temporary directory can exceed that limit.
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

In WebSocket 0.1.1, expiry is checked during the upgrade. An established connection can
outlive its token; a short lifetime alone does not end its subscription. Keep messages
limited to change identifiers and reauthorize HTTP reads. When access must end immediately,
close the affected connections or restart the supervised server, and refuse their renewal.

The browser module `websocket.js` uses its page token once, then requests a new token before
each reconnect. The host supplies the renewal URL and checks the current session and channel
permissions there. Return an authorization failure when the account can no longer connect.
The module's `token.js` distinguishes retryable renewal failures from terminal denials.

## Connect a browser

The browser module needs two published files and a JSON configuration element. Unlike
Flow's fixed runtime route, WebSocket does not automatically serve its browser assets.
Publish both `websocket.js` and its relative import `token.js` from the installed package.
This application-owned script uses a fixed source and destination; it exposes no vendor
directory through an HTTP route:

```php title="bin/publish-websocket-assets.php"
<?php

declare(strict_types=1);

$root   = dirname(__DIR__);
$source = $root . '/vendor/naf/websocket/src/Resources/public/assets';
$target = $root . '/public/plugins/naf/websocket/assets';

if (!is_dir($target)) {
    mkdir($target, 0755, true);
}

foreach (['websocket.js', 'token.js'] as $file) {
    if (!copy($source . '/' . $file, $target . '/' . $file)) {
        throw new RuntimeException('Unable to publish WebSocket asset: ' . $file);
    }
}
```

Run `php bin/publish-websocket-assets.php` after installation and whenever the package is
updated. Add it to existing Composer `post-install-cmd` and `post-update-cmd` scripts when
appropriate; preserve any scripts the application already runs.

The following controller and template fragments also use `naf/auth` and `naf/view`.
In a controller, authenticate the member and authorize each channel before preparing the
configuration. The following fragment assumes project 4 has already passed that check:

```php-inline
use function Naf\Auth\auth;
use function Naf\config;
use function Naf\route;
use function Naf\Websocket\live;
use function Naf\Websocket\token;

auth()->requireLogin();
$socket = live() ? [
    'url'     => config('websocket:url'),
    'token'   => token(auth()->id(), ['project:4']),
    'refresh' => route('project.connection', ['id' => '4']),
] : null;
```

Pass `$socket` to the full-page template. Render the JSON element before the external module,
and encode `<` and `&` so configuration cannot terminate its script element:

```html+php
<?php
use function Naf\View\asset;

if ($socket !== null) {
    asset()->add('/plugins/naf/websocket/assets/websocket.js', 'module');
}
?>
<?php if ($socket !== null): ?>
    <script type="application/json" data-naf-websocket><?= json_encode($socket, JSON_THROW_ON_ERROR | JSON_HEX_TAG | JSON_HEX_AMP) ?></script>
<?php endif ?>
<?= asset()->render('js') ?>
```

Render the asset collector once in the layout. The module reads the configuration when it
loads, opens the connection and manages reconnect delays. The named `project.connection`
route is application-owned: its GET handler must authenticate again, repeat the project
authorization and return `Naf\json(['url' => ..., 'token' => ...])` with a newly issued token.
Use HTTP 401 or 403 when access ends and `Cache-Control: private, no-store` on token responses.
Do not redirect that endpoint to a login page. Transient server/network failures are retried;
401, 403 and 404 stop renewal.

Allow the configured WebSocket origin in the host's CSP `connect-src`. For the local setup
above, that is `ws://127.0.0.1:8091`; an HTTPS deployment needs its own `wss://` origin.
Keep `script-src 'self'` for the external modules. The JSON element contains data, not code.

### Browser events and Flow

The shipped module dispatches document events. Application components listen to these events
without importing internal plugin modules:

| Event | `event.detail` | Application action |
| --- | --- | --- |
| `naf:websocket-open` | `{}` | Mark the connection active and fetch current state. |
| `naf:websocket-closed` | `{ retryIn: milliseconds or null }` | Show the fallback status; `null` means renewal stopped. |
| `naf:websocket-message` | The decoded message, including its `channel` when present | Match an authorized application channel and fetch its state. |

For example, add this lifecycle hook to an existing Flow component whose template defines
`flow-ref="results"` and whose props include the authorized channel and fragment URL:

```javascript
mount({ client, props, onCleanup }) {
    const refresh = async () => {
        try {
            await client.load(props.url, { target: 'results' });
        } catch (error) {
            if (error.name !== 'AbortError') {
                this.error = 'The latest results could not be loaded. Reload to retry.';
            }
        }
    };
    const changed = event => {
        if (event.detail.channel === props.channel) refresh();
    };

    document.addEventListener('naf:websocket-message', changed);
    document.addEventListener('naf:websocket-open', refresh);
    onCleanup(() => {
        document.removeEventListener('naf:websocket-message', changed);
        document.removeEventListener('naf:websocket-open', refresh);
    });
}
```

Declare `error = ''` before Flow mounts the component. Its PHP endpoint must use
[`Naf\Flow\page()`](flow.md#full-page-or-fragment) with an explicit fragment template and
authorize every read. Keep a manual refresh or periodic HTTP refresh for missed notifications
and unavailable sockets. A published revision is a hint to fetch; it is not proof the browser
received or applied a change. Stop timers and remove document listeners through `onCleanup()`.

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
