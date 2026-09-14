---
title: HTTP streams (0.2.2 draft)
---

# HTTP streams

Contributor draft for unreleased `naf/client 0.2.2`; keep outside published pages until
Packagist availability is verified. Merge this information into `pages/http-client.md`
after release and rerun the documented checks.

The cURL transport consumes PSR-7 request bodies from their current position in bounded
chunks and returns responses backed by temporary files. Close response bodies when done;
the files are automatically removed. Caller-owned request streams remain open. The
transfer completes before `sendRequest()` returns; this is not an asynchronous API.
Casting a body to string still loads it into PHP memory.

```php
use Nyholm\Psr7\Request;
use Nyholm\Psr7\Stream;
use function Naf\Client\client;

$input = fopen(BASE_PATH . '/storage/export.zip', 'rb');
$body  = Stream::create($input);
$http  = client()->withOptions(['streaming' => true, 'retries' => 0]);

try {
    $request  = new Request('PUT', 'https://uploads.example.com/export.zip', [], $body);
    $response = $http->sendRequest($request);
    $status   = $response->getStatusCode();
    $response->getBody()->close();
} finally {
    $body->close(); // the PSR-7 wrapper owns the resource supplied to it
}
```

The existing `TransportInterface` and its string-based `send()` remain supported.
`StreamingTransportInterface` is an optional additional transport capability, implemented
by the default cURL transport. The PHP wrapper fallback and older custom transports still
buffer strings. `streaming => true` rejects such transports instead of silently buffering.

Retries of seekable streams restart at the original offset. Non-seekable streamed request
bodies are not retried. `decode_content => false` preserves compressed response bytes for
storage use cases. Redirects retain only the final header block/body; use `max_redirects
=> 0` for signed requests or credentials that must not be redirected. Existing `withOptions()`
cloning and NAF configuration/DI remain unchanged. Temporary disk space must accommodate
the downloaded response, and timeouts must suit the expected transfer size.
