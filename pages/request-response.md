---
title: Requests and responses
---

# Requests and responses

NAF exposes a PSR-7 server request and expects a PSR-7 response from every handler.
Import helpers in each PHP file that uses them.

## Read the request

```php
use function Naf\request;

$method = request()->getMethod();
$path = request()->getUri()->getPath();
$query = request()->getQueryParams();
$authorization = request()->getHeaderLine('Authorization');
$form = request()->getParsedBody() ?? [];
$rawBody = (string) request()->getBody();
```

`getParsedBody()` exposes parsed form data. It does **not** automatically decode JSON.
For a JSON-only endpoint, decode the body explicitly and reject invalid input:

```php
use function Naf\{json, request};

try {
    $data = json_decode((string) request()->getBody(), true, 512, JSON_THROW_ON_ERROR);
} catch (\JsonException) {
    return json(['error' => 'Invalid JSON'], 400);
}
if (!is_array($data)) {
    return json(['error' => 'Expected an object or array'], 400);
}
```

## Combined request parameters

```php
use function Naf\param;

$email = param()->get('email');
$city = param()->get('address.city', 'unknown');
$data = param()->all();
```

`param()` merges query parameters and parsed form data. If the parsed body is empty and
`Content-Type` contains `application/json`, it decodes JSON and merges those values instead.
Body values override query values at the top level. Invalid JSON contributes no values;
use explicit decoding when malformed JSON must be distinguished from missing fields.
A literal key containing a dot takes precedence over a nested lookup.

Use the body directly when a value from the query string should not be accepted.
[Handling a POST request](recipes/post-requests.md) applies this to forms.

## Uploaded files

```php
use function Naf\{json, request};

$file = request()->getUploadedFiles()['document'] ?? null;
if ($file === null || $file->getError() !== UPLOAD_ERR_OK) {
    return json(['error' => 'Upload failed'], 400);
}

// The application creates this private directory and decides which file types to accept.
$destination = BASE_PATH . '/storage/uploads/' . bin2hex(random_bytes(16));
$file->moveTo($destination);
```

Uploads are PSR-7 `UploadedFileInterface` objects. Do not use the client-supplied filename as
an unchecked filesystem path. Validate type and size according to your application's needs.

## Responses

```php
use function Naf\{json, response};

return response('Hello', 200, ['Content-Type' => 'text/plain; charset=UTF-8']);
```

`response($content = '', $status = 200, $headers = [])` accepts a PSR-7-compatible body.
The helper sets no default content type; state it explicitly when it matters.

```php
use function Naf\json;

return json(['message' => 'Created'], 201);
```

`json()` serializes the value and sets `Content-Type: application/json; charset=UTF-8`.
For a response with no body use `response('', 204)`, not `json(null, 204)`.

## HTML views

```php
use function Naf\View\render;

return render('home', ['name' => 'World']);
```

This needs `naf/view`. `render()` returns a response; `view()` returns a string.
Templates must escape untrusted values explicitly with `Naf\View\s()`.
See [Views and templates](views.md).

## Redirect and refresh

```php
use function Naf\{redirect, refresh};

return redirect('/login');       // 302
return redirect('/new-url', 301);
return refresh();               // 302 to the current URL path, without its query string
```

## Custom responses

```php
use Nyholm\Psr7\Response;

return new Response(202, ['Content-Type' => 'text/plain'], 'Accepted');
```

PSR-7 methods such as `withStatus()` and `withHeader()` return a new object. Return or assign
that new response. See [Events](events.md#change-a-response) for response-header listeners.

## Logging

```php
use function Naf\log;

log()->info('Import finished', ['count' => 12]);
```

The default PSR-3 logger writes to `logs/app.log` under the application root. The directory
must be writable. `log()` is the NAF helper; there is no `logger()` helper.

## Redirects on the PHP development server

Use `naf/framework` **0.2.2 or newer**. These releases create redirects with a valid HTTP/1.1
status line, including on PHP's development server. Framework 0.2.1 used HTTP/2 here, which
caused malformed responses with `php -S`. Update older installations using the
[installation guide](install.md#start-with-the-application-skeleton), then remove the old
protocol-normalization listener if you copied it from an earlier tutorial.

No manual protocol override is needed with the supported versions:

```php
use function Naf\redirect;

return redirect('/login');
```
