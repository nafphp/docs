---
title: HTTP client
requires:
  - naf/client
---

# HTTP client

Calling somebody else's HTTP service from inside your application — an internal API,
a payment provider, a webhook you have to deliver.

It implements PSR-18, so anything expecting a standard client accepts it, and it carries
no dependencies of its own. Two transports sit behind it, cURL and streams, and it falls
back when the first is unavailable — which matters on the shared hosting where cURL is a
question rather than a given.

## Sending a request

```php
use Nyholm\Psr7\Request;
use function Naf\Client\client;

$response = client()->sendRequest(new Request('GET', 'https://api.example.com/status'));

$response->getStatusCode();
(string) $response->getBody();
```

`client()` implements `Psr\Http\Client\ClientInterface`, so anything that accepts a
standard PSR-18 client accepts this one — including libraries that have never heard of NAF.

## Retries are on by default

```php
'client' => [
    'retries'        => 1,      // one additional attempt
    'retry_delay_ms' => 150,
],
```

**A failed request is sent again.** That is right for a GET and wrong for anything that
changes something on the other side: a POST that times out may well have arrived, and the
retry creates the order twice.

For a request that must not be repeated, take a copy of the client with retries off:

```php
$once = client()->withOptions(['retries' => 0]);
$once->sendRequest($request);
```

`withOptions()` returns a clone. The container holds one shared client, so switching
retries off for an OAuth code exchange does not switch it off for everybody else — which
is the whole reason it is a clone and not a setter.

## Two transports, and a fallback

The client tries cURL first and streams second, asking each whether it is available. On a
host without the cURL extension the request still goes out.

A transport is one class:

```php
interface TransportInterface
{
    public function send(string $url, string $method, array $headerLines, string $body, array $config): array;
    public function isAvailable(): bool;
}
```

`isAvailable()` is the part that matters: a transport that cannot run says so instead of
failing at the call, which is what makes the fallback work rather than just shifting the
error.

You can hand the client its transports directly, in the order you want them tried:

```php
new Client([new MyTransport(), new CurlTransport()]);
```

## Large bodies do not go through memory

The cURL transport streams. It transfers a PSR-7 request body in chunks from its current
position, and spools the response into a temporary file that is deleted for you. That is
what makes an upload or a download bigger than your memory limit possible at all.

Two things follow from it, and both bite quietly if you do not know them:

```php
$response = client()->sendRequest($request);
$body     = $response->getBody();

while (!$body->eof()) {
    fwrite($target, $body->read(8192));
}

$body->close();          // the temporary file goes away here
```

Close the body when you are done. And `(string) $response->getBody()` still loads the whole
thing into memory — casting undoes the streaming, which is fine for a JSON answer and not
for a 2 GB file. A request stream you opened yourself stays open; the client does not close
what it did not create.

!!! note "The temporary filesystem has to be big enough"
    The response is spooled before `sendRequest()` returns, so the network transfer is
    finished by then. What you need free is disk, not memory.

Existing `TransportInterface` implementations and string-based `send()` calls keep working
unchanged. A custom transport can additionally implement `StreamingTransportInterface`, and
if your code must not silently fall back to buffering, say so:

```php
$streaming = client()->withOptions(['streaming' => true]);
```

That requires a transport with the capability rather than accepting the buffering fallback.
The stream-wrapper transport remains string-based.

A few sharp edges worth knowing:

| Situation | Behaviour |
|---|---|
| A retry after a failure | seeks the request body back to where it started |
| A non-seekable streaming request | never retried automatically — it cannot be rewound |
| `'decode_content' => false` | keeps the encoded bytes, for passing straight to object or file storage |
| Redirects | only the final response's headers and body are kept |
| `'max_redirects' => 0` | do not follow redirects at all |

## TLS and HTTP versions

```php
'client' => [
    'cacert'       => '/etc/ssl/certs/ca-certificates.crt',
    'http_version' => 'auto',   // auto | 1.1 | 2
],
```

The CA bundle is resolved once per request rather than per attempt. Leave `cacert` out and
the system bundle is used; set it when PHP on that host cannot find one, which is the usual
cause of a certificate error that makes no sense on a machine where `curl` works fine from
the shell.

`http_version` stays on `auto` unless a server negotiates badly.

## Testing without the network

The constructor takes the transports, so a test hands it one that answers from memory:

```php
$client = new Client([new FakeTransport([
    'status' => 200,
    'body'   => '{"ok":true}',
])]);
```

No HTTP goes out, no test depends on somebody else's uptime, and the retry behaviour is
exercised the same way it will be in production.
