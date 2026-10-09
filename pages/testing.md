---
title: Testing applications
---

# Testing applications

Test business rules independently of HTTP, then test routes through a running application.
Calling a controller directly does not exercise routing, CSRF, sessions or response emission.

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

## Test HTTP behavior

Create this smoke test. It requires Python 3.9+ and uses its standard library. It accepts the
URL of an already running application and checks the tutorial's JSON endpoint and a missing
route:

```python title="tests/http_smoke.py"
import json
import sys
import urllib.error
import urllib.request

base = (sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8000').rstrip('/')

for path, expected in [('/hello/Ada', 200), ('/does-not-exist', 404)]:
    try:
        response = urllib.request.urlopen(base + path, timeout=5)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        status = response.status
        body = response.read().decode()
        if status != expected:
            raise AssertionError(f'{path}: expected {expected}, received {status}')
        if path == '/hello/Ada':
            if json.loads(body) != {'hello': 'Ada'}:
                raise AssertionError('Unexpected greeting response')
            if response.headers.get_content_type() != 'application/json':
                raise AssertionError('Expected JSON content type')

print('HTTP smoke tests passed.')
```

Start the server in one terminal:

```bash
APP_ENV=test php -S 127.0.0.1:8000 -t public
```

In another terminal:

```bash
python3 tests/http_smoke.py http://127.0.0.1:8000
```

Expect `HTTP smoke tests passed.` A connection failure, wrong status or incorrect JSON fails
the test. You can also inspect the responses manually:

```bash
curl -i http://127.0.0.1:8000/hello/Ada
curl -i http://127.0.0.1:8000/does-not-exist
```

## Forms, sessions and persistence

Fetch a form and retain its cookies and CSRF token before submitting. Check valid input,
invalid input, a missing token and an invalid token. Submit with the same cookie jar and
generate one token per page. See [Forms](forms.md#csrf-protection).

For login, verify persistence on the next request, logout and suspension. For storage, create
a disposable schema, run migrations and assert persisted results. Never use production data.
Use [mail capture](mail.md#testing-without-a-mail-server) and the
[HTTP fake transport](http-client.md#testing-without-the-network) to avoid external side effects.
Test jobs directly and through `queue:consume --once` when worker behavior matters.

## Continuous integration

Install the committed lock with development dependencies and run the same checks as locally.
Start the HTTP server before smoke tests and stop it even when a check fails. Retain server
logs for failures. Use `APP_ENV=test`; `testing` is not NAF's test environment value.

The starter's `composer test` checks its original demo. Replace that script after replacing
demo routes so it runs tests for your application.
