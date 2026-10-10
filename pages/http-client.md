---
title: HTTP client
requires:
  - naf/client
---

# HTTP client

`naf/client` implements PSR-18 for outbound HTTP calls. It selects the first available
transport: cURL, then PHP streams. cURL supports bounded-memory request and response bodies;
the stream-wrapper transport buffers bodies as strings.

Use this chapter in an existing [NAF application](first-app.md). The cURL transport requires
`ext-curl`; the fallback needs PHP URL streams enabled.

## Sending a request

```php-inline
use Nyholm\Psr7\Request;
use function Naf\Client\client;

$response = client()->sendRequest(new Request('GET', 'https://api.example.com/status'));
$status = $response->getStatusCode();
$body = (string) $response->getBody();
```

Inspect the status before using the body. HTTP 4xx and 5xx responses are returned to the
caller; they do not by themselves trigger an exception or retry. Transport failures raise
`Naf\Client\Exception\ClientException`. Casting the body to a string loads it into memory.

## Send JSON

```php-inline
use Nyholm\Psr7\Request;
use function Naf\Client\client;

$request = new Request('POST', 'https://api.example.com/orders', [
    'Content-Type' => 'application/json',
    'Accept'       => 'application/json',
], json_encode(['sku' => 'ABC-1', 'quantity' => 2], JSON_THROW_ON_ERROR));

// Creating an order is not safe to repeat, so this call must not be retried.
$response = client()->withOptions(['retries' => 0])->sendRequest($request);

if ($response->getStatusCode() !== 201) {
    throw new RuntimeException('Order rejected with HTTP ' . $response->getStatusCode());
}

$order = json_decode((string) $response->getBody(), true, flags: JSON_THROW_ON_ERROR);
```

Headers and the body belong to the PSR-7 request; the client sends them unchanged. Add an
`Authorization` header the same way, with a secret read from configuration. Check the
status and decode the body yourself: the client does not interpret JSON or throw for 4xx
and 5xx responses.

## Configuration

Add a `client` array to `app/config.php`. Per-call `withOptions()` values override that
configuration on a cloned client, leaving the shared instance unchanged.

| Key under `client` | Type | Default | Effect |
|---|---|---|---|
| `retries` | integer | `1` | Additional attempts for recognized transient transport failures |
| `retry_delay_ms` | integer | `150` | Delay between attempts in milliseconds |
| `timeout` | number | `20` | Transfer timeout in seconds |
| `connect_timeout` | number | `8` | cURL connection timeout in seconds |
| `ssl_verify` | boolean | `true` | TLS certificate verification |
| `cacert` | string or null | automatic | Explicit CA bundle file |
| `http_version` | string | `auto` | cURL negotiation: `auto`, `1.1` or `2` |
| `max_redirects` | integer | `5` | Redirect limit; `0` disables following |
| `decode_content` | boolean | `true` | cURL response content decoding |
| `streaming` | boolean | `false` | Require a streaming-capable transport |

Transport-specific options may not apply to the stream-wrapper fallback. Keep TLS verification
enabled and check the host's CA configuration when certificate verification fails.

## Retries are on by default

The client recognizes selected TLS/network error messages, including timeouts and connection
resets, for retry. It does not retry every failure. A timed-out POST may already have reached
the remote service; repeating it can duplicate an operation.

Disable retries for operations that must not be replayed unless the remote API provides an
appropriate idempotency mechanism:

```php-inline
$once = client()->withOptions(['retries' => 0]);
$response = $once->sendRequest($request);
```

## Transport selection { #two-transports-and-a-fallback }

Transports implement `Naf\Client\Transports\TransportInterface`. Its `send()` returns a pair:
a response body string and a list of raw response header lines, including the HTTP status
line. `isAvailable()` determines whether the client can select the transport.

Pass an ordered array of transport instances to `new Client($transports)` for custom
selection. Fallback is based on availability; a failed cURL request does not automatically
switch to the stream transport.

## Streaming large bodies { #large-bodies-do-not-go-through-memory }

The cURL transport reads the request body from its current position and spools the response
to a temporary file before `sendRequest()` returns. The operation is synchronous and requires
enough temporary disk space for the response. Close the body when finished:

```php-inline
$response = client()->sendRequest($request);
$body = $response->getBody();

try {
    while (!$body->eof()) {
        fwrite($target, $body->read(8192));
    }
} finally {
    $body->close();
}
```

This fragment assumes `$target` is an open writable resource owned by the caller. The client
does not close request streams opened by application code. `(string) $body` still reads the
entire response into memory.

| Situation | Behavior |
|---|---|
| Retried streaming request | Seek back to the original request-body position |
| Non-seekable streaming request | No automatic retry |
| `decode_content => false` | Preserve encoded response bytes |
| Redirect | Retain only the final response's headers and body |
| `streaming => true` | Reject a transport without streaming support |

A custom transport can implement `StreamingTransportInterface` in addition to the basic
interface. Set `streaming` when buffering is unacceptable.

## TLS and HTTP versions

Leave `cacert` unset to use automatic CA-bundle resolution. When the host needs an explicit
bundle, configure its readable file path. The bundle is resolved once per call. Keep
`http_version` on `auto` unless the remote service requires a specific version.

## Testing without the network

The following complete example supplies a fake transport, simulates one timeout and verifies
the retry and JSON response without making a network connection. Create the two files:

```php title="tests/FakeTransport.php"
<?php

declare(strict_types=1);

namespace Tests;

use Naf\Client\Transports\TransportInterface;

final class FakeTransport implements TransportInterface
{
    public int $attempts = 0;

    public function isAvailable(): bool
    {
        return true;
    }

    public function send(string $url, string $method, array $headerLines, string $body, array $config): array
    {
        $this->attempts++;
        if ($this->attempts === 1) {
            throw new \RuntimeException('Connection timed out (simulated).');
        }

        return ['{"ok":true}', ['HTTP/1.1 200 OK', 'Content-Type: application/json']];
    }
}
```

```php title="bin/http-client-demo.php"
<?php

declare(strict_types=1);

require dirname(__DIR__) . '/bootstrap.php';
require dirname(__DIR__) . '/tests/FakeTransport.php';

use Naf\Client\Core\Client;
use Nyholm\Psr7\Request;
use Tests\FakeTransport;

$transport = new FakeTransport();
$client = (new Client([$transport]))->withOptions(['retries' => 1, 'retry_delay_ms' => 0]);
$response = $client->sendRequest(new Request('GET', 'https://example.invalid/status'));

if ($transport->attempts !== 2 || $response->getStatusCode() !== 200
    || json_decode((string) $response->getBody(), true, flags: JSON_THROW_ON_ERROR) !== ['ok' => true]) {
    throw new RuntimeException('Unexpected transport result.');
}

echo "HTTP transport test passed.\n";
```

Run `php bin/http-client-demo.php` from the application root. Expect `HTTP transport test passed.`
See [Testing applications](testing.md) for service and HTTP tests.

## If the result is different

| What you see | What to check |
|---|---|
| `HTTP request failed: …` | The message comes from the transport: DNS, TLS, timeout or connection errors |
| `No HTTP transport available` | Every transport passed to `new Client([...])` reports `isAvailable() === false`; the default list always has the stream fallback |
| Requests fail without `ext-curl` | The stream fallback needs `allow_url_fopen`; enable it or install `ext-curl` |
| `The selected HTTP transport does not support streaming.` | `streaming => true` needs the cURL transport |
| A 404 or 500 response does not throw | Expected: inspect `getStatusCode()` yourself |
| A POST arrived twice | Set `retries` to `0` for operations that must not be repeated |
