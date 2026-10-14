# Framework 0.2.12: HTTP contracts and testable request handling

Pending `naf/framework` 0.2.12 on Packagist. Keep this draft outside `pages/` until the
release is available. Apply the guide updates below, refresh generated references against
the published packages, verify the new example and run all documentation checks.
The separate 0.2.11 authority draft also needs publication after its release.

## Routing guide updates

For `pages/routing.md`, replace the method paragraph with:

> Register methods in upper case. An explicit matching HEAD route takes precedence;
> otherwise HEAD uses the first matching GET route and sends its metadata without content.
> Explicit OPTIONS routes run normally. Without one, OPTIONS for a known path returns
> 204 and `Allow` without invoking a controller. This does not configure CORS; applications
> must configure their own cross-origin policy.
>
> Known paths requested with an unsupported method return 405 and `Allow`; unknown paths
> return 404. `Allow` includes implicit HEAD for GET and automatic OPTIONS.

State minimum Framework 0.2.12 and retain older explicit HEAD/OPTIONS behavior in a
collapsed note. The built-in welcome response exists only when no routes are registered,
for GET and HEAD `/`.

Replace the URL parameter paragraph with:

> Pass every placeholder as a string or integer. Missing or invalid values throw
> `InvalidArgumentException` identifying the route and parameter. Values are substituted
> once, exactly as supplied. Encode each dynamic segment with `rawurlencode()` before
> calling `route()`; the framework does not encode or decode it again. Extra parameter
> keys are ignored. These values are path segments, not an appended query string.

```php-inline
$url = \Naf\route('files.show', ['name' => rawurlencode('annual report.pdf')]);
```

For `/files/{name}` this produces `/files/annual%20report.pdf`.

## Requests and responses guide updates

Add a "Responses without content" section to `pages/request-response.md`:

Framework 0.2.12+ suppresses content for HEAD, informational statuses, 204, 205 and 304
without reading the original stream. HEAD preserves an explicit Content-Length or uses
the known body size when none was supplied. Unknown sizes remain unspecified.
Informational statuses and 204 remove Content-Length; 205 uses zero; 304 retains supplied
representation metadata. Transfer-Encoding is removed for responses without content.
The emitter reapplies these rules after response-header listeners.

## Lifecycle and testing guide updates

Document `App::handle(ServerRequestInterface $request): ResponseInterface` in
`pages/lifecycle.md` and `pages/testing.md`, with minimum Framework 0.2.12:

It replaces request and parameter bindings, clears the matched route, runs request/controller
events, converts exceptions through the normal error path, normalizes content rules and
dispatches `response.send` during finalization. It returns without emitting or exiting.
The emitter owns `response.header`, `response.body` and `response.end`; `handle()` does not
run them. Keep real HTTP tests for emitted cookies, headers, streams and SAPI behavior.

Existing applications continue to start with `app()->run()`. It creates the server request,
delegates handling and emits the response. `handle()` is an additional entry point for a
supplied request; adopting it is not required for existing application bootstraps.

Sequential calls share application and plugin services. This does not guarantee isolation
for persistent HTTP workers; keep request-specific state out of shared services. Concurrent
or reentrant handling on one App is rejected.

Complete `tests/RequestTest.php`, assuming the first-application files and PHPUnit:

```php
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

Run `APP_ENV=test vendor/bin/phpunit tests/RequestTest.php`.

## Dependency injection guide updates

Framework 0.2.12+ adds `Naf\Contracts\MutableContainerInterface`, extending PSR-11 with
`set(string $id, callable|object $factory): void` and `reset(string $id): void`.
Both built-in containers implement it. `App::__construct(MutableContainerInterface $container)`
and `AutoResolvingContainer::__construct(MutableContainerInterface $container)` require the
contract directly in their native parameter types. PHP rejects a read-only PSR-11 container
with `TypeError` before either constructor body runs. Custom writable containers must
implement the new interface; ordinary applications using the built-in containers and
`app()->run()` do not need bootstrap changes.

`App::container()` retains its return type; its PHPDoc exposes the writable contract.
Factories still receive the base container; autowiring belongs to `make()` on the decorator.

## Event guide updates

Mark Event::REQUEST_BODY and Event::REQUEST_END as deprecated compatibility constants.
They remain defined and are not dispatched. No replacement body/end event is introduced.
Use `request.start` to observe the registered request and response hooks at their actual
dispatch points. State which events run during `handle()` and which belong to emission.

## Installation and migration

In `pages/install.md`, state that Framework 0.2.12+ requires JSON and no longer requires PDO.
Keep the PDO requirement for older releases. Database-backed features need PDO and their
driver; forms use mbstring. A current starter may still lock an older framework and therefore
require PDO until updated.

The core now requires Nyholm PSR-7 1.8.2 or newer. The lowest-dependency matrix exposed
implicit-nullable deprecations in earlier versions on PHP 8.4/8.5. Composer resolves
this minimum automatically when updating the framework.

Upgrade with `composer require 'naf/framework:^0.2.12' --with-all-dependencies`.
Run application tests for these observable corrections:

- Wrong-method requests become 405 with Allow.
- HEAD can invoke a GET handler. Keep GET handlers free of write side effects.
- OPTIONS can return 204 without a controller. Register an explicit route for application behavior.
- Missing or non-string/non-integer URL placeholders throw instead of producing invalid URLs.
- Custom writable containers implement MutableContainerInterface.
- Handlers return PSR-7 responses. The undocumented `-1` exit sentinel now produces a
  dispatcher error; replace it with an ordinary response. A returned sentinel must not
  terminate in-process request handling.

## Contributor verification

The package declares `composer test`, `composer analyse` (PHPStan level 5, PHP 8.3,
no baseline), `composer test:http` and `composer test:plugins`.
CI checks PHP 8.3/8.4/8.5 with lowest/latest dependencies, the locked set on 8.3,
and a production installation with PDO disabled. Plugin tests install published Form,
Session, View and i18n in a disposable host and verify CSRF, session cookies, templates,
locale selection and composed response headers.

AppHolder, CoreFileLoader, PluginBootOrder and Stopwatch are marked internal.
The public API and support policy is documented in `pages/compatibility.md`.
