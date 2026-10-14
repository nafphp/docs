---
title: Testing applications
---

# Testing applications

Test business rules independently of HTTP, then exercise request handling and the emitted
response. Calling a controller directly does not exercise routing, CSRF, sessions or
response emission.

The examples start from [Your first application](first-app.md). Run commands from its project
root. They use local data and do not require a database or external service.

## Test application services

Install PHPUnit as a development dependency and create the directories:

```bash
composer require --dev 'phpunit/phpunit:^12.1'
mkdir -p app/Services tests
```

Create the service:

```php title="app/Services/Greeting.php"
<?php

declare(strict_types=1);

namespace App\Services;

final class Greeting
{
    public function forName(string $name): string
    {
        $name = trim($name);
        if ($name === '') {
            throw new \InvalidArgumentException('Name must not be empty.');
        }

        return 'Hello, ' . $name . '!';
    }
}
```

Create a test that loads Composer without booting NAF:

```php title="tests/GreetingTest.php"
<?php

declare(strict_types=1);

use App\Services\Greeting;
use PHPUnit\Framework\TestCase;

final class GreetingTest extends TestCase
{
    public function testTrimsTheName(): void
    {
        self::assertSame('Hello, Ada!', (new Greeting())->forName(' Ada '));
    }

    public function testRejectsAnEmptyName(): void
    {
        $this->expectException(InvalidArgumentException::class);
        (new Greeting())->forName('   ');
    }
}
```

```bash
composer dump-autoload
vendor/bin/phpunit --bootstrap vendor/autoload.php tests/GreetingTest.php
```

Expect two passing tests. Use constructor dependencies so service tests can supply disposable
storage or capture transports. Application code does not need a NAF base test class.

## Test request handling without emission

Framework **0.2.12+** can process a supplied PSR-7 request with `app()->handle()` without
starting a server or emitting a response. The normal router, controller hooks and error
handling still run. Existing application bootstraps continue to use `app()->run()`.

Starting from the first-application files and the PHPUnit dependency above, update the
framework and create this complete test:

```bash
composer require 'naf/framework:^0.2.12' --with-all-dependencies
```

```php title="tests/RequestTest.php"
<?php

declare(strict_types=1);

use Nyholm\Psr7\ServerRequest;
use PHPUnit\Framework\TestCase;

use function Naf\app;

define('BASE_PATH', dirname(__DIR__));
require BASE_PATH . '/vendor/autoload.php';

final class RequestTest extends TestCase
{
    public function testHelloAndMissingRoute(): void
    {
        $application = app();
        $response = $application->handle(new ServerRequest('GET', '/hello/Ada'));
        self::assertSame(200, $response->getStatusCode());
        self::assertSame(['hello' => 'Ada'], json_decode((string) $response->getBody(), true));
        self::assertSame(404, $application->handle(new ServerRequest('GET', '/missing'))->getStatusCode());
    }
}
```

```bash
APP_ENV=test vendor/bin/phpunit tests/RequestTest.php
```

Expect one passing test with three assertions. Each `handle()` call replaces request and
parameter bindings and clears the current route; application and plugin singletons remain
shared. Keep request-specific data out of those services. This example tests the returned
response; keep the real HTTP tests below for emitted cookies, headers, streams and SAPI behavior.

## Test HTTP behavior

Service tests do not exercise routing, CSRF, sessions or response emission. Test those
through a running application. This PHPUnit test sends real HTTP requests to the server
named in `APP_URL` (default `http://127.0.0.1:8000`) and checks the tutorial's JSON endpoint
and a missing route:

```php title="tests/HttpSmokeTest.php"
<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class HttpSmokeTest extends TestCase
{
    public function testHelloReturnsJson(): void
    {
        [$status, $headers, $body] = $this->get('/hello/Ada');

        self::assertSame(200, $status);
        self::assertStringStartsWith('application/json', $headers['content-type'] ?? '');
        self::assertSame(['hello' => 'Ada'], json_decode($body, true, flags: JSON_THROW_ON_ERROR));
    }

    public function testUnknownRouteReturns404(): void
    {
        [$status] = $this->get('/does-not-exist');

        self::assertSame(404, $status);
    }

    /** @return array{int, array<string, string>, string} status, lower-case headers and body */
    private function get(string $path): array
    {
        $base    = rtrim(getenv('APP_URL') ?: 'http://127.0.0.1:8000', '/');
        $context = stream_context_create(['http' => ['ignore_errors' => true, 'timeout' => 5]]);
        $stream  = @fopen($base . $path, 'r', false, $context);
        if ($stream === false) {
            self::fail("No response from {$base}{$path}. Is the development server running?");
        }

        $lines = stream_get_meta_data($stream)['wrapper_data'];
        $body  = (string) stream_get_contents($stream);
        fclose($stream);

        preg_match('{^HTTP/\S+ (\d{3})}', $lines[0], $status);
        $headers = [];
        foreach (array_slice($lines, 1) as $line) {
            [$name, $value]                 = explode(':', $line, 2) + [1 => ''];
            $headers[strtolower(trim($name))] = trim($value);
        }

        return [(int) $status[1], $headers, $body];
    }
}
```

Start the server in one terminal:

=== "macOS / Linux"

    ```bash
    APP_ENV=test php -S 127.0.0.1:8000 -t public
    ```

=== "Windows (PowerShell)"

    ```powershell
    $env:APP_ENV = "test"; php -S 127.0.0.1:8000 -t public
    ```

In another terminal:

```bash
vendor/bin/phpunit --bootstrap vendor/autoload.php tests/HttpSmokeTest.php
```

Expect two passing tests. A connection failure, wrong status or incorrect JSON fails the
test. To test another address, set `APP_URL`, for example `APP_URL=http://127.0.0.1:8001`.
You can also inspect the responses manually:

```bash
curl -i http://127.0.0.1:8000/hello/Ada
curl -i http://127.0.0.1:8000/does-not-exist
```

## Forms, sessions and persistence

A form request needs the session cookie and the CSRF token from the page that rendered the
form. With the [contact form](recipes/contact-form.md) running, these commands keep the cookie
in `cookies.txt`, read the token from the form and check the three outcomes:

```bash
curl -s -c cookies.txt -o form.html http://127.0.0.1:8000/contact
token=$(grep -o 'name="_csrf" value="[^"]*"' form.html | cut -d'"' -f4)

curl -s -o /dev/null -w '%{http_code}\n' -b cookies.txt -d 'name=Ada' http://127.0.0.1:8000/contact
curl -s -o /dev/null -w '%{http_code}\n' -b cookies.txt --data-urlencode "_csrf=$token" \
  -d 'name=Ada' -d 'email=invalid' -d 'message=short' http://127.0.0.1:8000/contact
curl -s -o /dev/null -w '%{http_code}\n' -b cookies.txt --data-urlencode "_csrf=$token" \
  -d 'name=Ada' -d 'email=ada@example.com' -d 'message=A long enough message.' \
  http://127.0.0.1:8000/contact
```

Expected output: `400` without a token, `422` for invalid fields and `302` for the valid
message, which also writes one file to `storage/mail/`. Check an invalid token too, and
delete `cookies.txt` and `form.html` afterwards.

For login, verify persistence on the next request, logout and suspension. For storage, create
a disposable schema, run migrations and assert persisted results. Never use production data.
Use [mail capture](mail.md#testing-without-a-mail-server) and the
[HTTP fake transport](http-client.md#testing-without-the-network) to avoid external side effects.
Test jobs directly and through `queue:consume --once` when worker behavior matters.

## Continuous integration

Install the committed lock with development dependencies and run the same checks as locally.
Start the HTTP server before the HTTP tests, pass its address in `APP_URL`, and stop it even
when a check fails. Retain server logs for failures. Use `APP_ENV=test`; `testing` is not NAF's test environment value.

The starter's `composer test` checks its original demo. Replace that script after replacing
demo routes so it runs tests for your application.
