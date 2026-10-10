---
title: Events
---

# Events

Listeners are callables registered during bootstrap. Custom events can carry any payload:

```php-inline
use function Naf\{event, log};

event()->listen('product.created', function (object $product) {
    log()->info('Product created: {id}', ['id' => $product->id]);
});

// After your application creates a product:
event()->dispatch('product.created', $product);
```

`listen($event, $listener, $priority = 0)` runs higher priorities first.
`dispatch()` returns an array of listener results. Use closures or `[ListenerClass::class, 'handle']`;
NAF constructs class-based listeners through the default container.

## A complete custom event flow

An event connects application work to optional reactions. The code doing the work must
dispatch it; registering a listener alone never causes it to run. This example records an
import result without a database or external delivery.

Start from [Your first application](first-app.md). Add these complete files, then run
`composer dump-autoload` and `php bin/events-demo.php` from the project root.

```php title="app/Listeners/RecordImport.php"
<?php

declare(strict_types=1);

namespace App\Listeners;

use Psr\Log\LoggerInterface;

final class RecordImport
{
    public function __construct(private LoggerInterface $logger) {}

    public function handle(string $source, int $count): string
    {
        $this->logger->info('Imported {count} records from {source}.', [
            'count' => $count,
            'source' => $source,
        ]);

        return 'logged';
    }
}
```

```php title="bin/events-demo.php"
<?php

declare(strict_types=1);

use App\Listeners\RecordImport;

use function Naf\event;

require dirname(__DIR__) . '/bootstrap.php';

event()->listen('app.catalog.imported', [RecordImport::class, 'handle'], priority: 10);
event()->listen('app.catalog.imported', static function (string $source, int $count): string {
    echo "Imported {$count} records from {$source}.", PHP_EOL;

    return 'reported';
});

$results = event()->dispatch('app.catalog.imported', 'catalog.csv', 3);
echo implode(', ', $results), PHP_EOL;
```

Expect `Imported 3 records from catalog.csv.` followed by `logged, reported`.
The class listener receives the configured PSR-3 logger through constructor injection and
writes to `logs/app.log`. Dispatch arguments become listener arguments in the same order.
Priority 10 runs before priority 0; results follow that execution order.
Choose event names with an application or package prefix and keep their payload contract
stable, so an unrelated plugin listener cannot accidentally receive different arguments.

Listeners run synchronously in the dispatching process. An exception stops dispatch and
propagates to the caller; the event manager does not undo earlier writes or deliveries.
Keep required business rules in the application service, dispatch after the relevant work
succeeds, and use [Queue](queues.md) when a reaction should run in a worker.

## Object events { #an-event-can-be-an-object }

Since **v0.2.6** the event may be an object, in which case its class is the name and the
object itself is the payload:

```php-inline
final class OrderShipped
{
    public function __construct(public string $order) {}
}

event()->listen(OrderShipped::class, fn(OrderShipped $shipped) => log()->info($shipped->order));
event()->dispatch(new OrderShipped('A-1'));
```

`listen()` accepts the class-name string. Event objects need no interface or base class;
existing string events can continue to be used alongside object events.

An event class defines the payload shape and supports IDE navigation and refactoring.
PHP does not verify class existence when evaluating `SomeClass::class`; a misspelled class
name there still produces a string. Static analysis can detect it, and constructing a
missing class with `new` fails. Keep listener names and dispatched classes consistent.

String names and event class names share one key space. Replacing a custom string name
with a class name changes the event key; update its listeners in the same change.

Priorities, class listeners, return values and `dispatchForResponse()` behave identically
either way.

## Request lifecycle

The following events describe the normal HTTP path. Payload order is part of the API.

| Event | Payload | When |
|---|---|---|
| `request.start` | `$request` | After creating and registering the request in `App::run()` |
| `route.matching` | `$uri, $method` | Before searching routes |
| `route.matched` | `$route` array | After finding a match |
| `route.not_found` | `$uri, $method` | When no route matches |
| `controller.calling` | `$request, $controller, $action` | Before invoking the handler; controller is null for a closure |
| `controller.called` | `$request, $controller, $action, $response` | After invoking the handler |
| `exception` | `$exception` | When request handling throws |
| `response.send` | `$response` | During response finalization |
| `response.header` | `$response` | Before sending HTTP headers |
| `response.body` | `$response` | Before writing the body, after headers |
| `response.end` | `$response` | After writing the body |

`request.end` and `request.body` are declared constants but are not dispatched by the current
request path. There is no `response.sending` event.

## Events used by the published plugins

Installed plugins register listeners on these events. Your own listeners run alongside
them; listeners with the same priority run in registration order.

| Package | Event | What the listener does |
|---|---|---|
| `naf/form` | `controller.calling` | Checks the CSRF token and aborts with 400; see [Forms](forms.md#csrf-protection) |
| `naf/i18n` | `request.start` | Selects the language from `?lang`, the `lang` cookie or `Accept-Language` |
| `naf/i18n` | `response.header` | Returns the response with a `lang` cookie when the language was chosen or changed |
| `naf/mcp` | `response.body` | Enables implicit flushing for `text/event-stream` responses |
| `naf/rbac` | dispatches `Naf\Rbac\Events\GrantsChanged` | An object event after grants change; see [RBAC](rbac.md#telling-a-host-what-moved) |

Framework 0.2.9+ chains `response.header` listeners through `EventManager::dispatchResponse()`.
Each listener receives the response returned by the previous listener. Application headers
and the language cookie from `naf/i18n` therefore survive together, provided listeners modify
the response they receive. A return value other than `ResponseInterface` leaves it unchanged.

??? note "Framework 0.2.8 and older"
    Every header listener receives the original response and only the last returned
    replacement survives. An application header listener can discard the i18n language
    cookie, or vice versa. Update the framework, or add those headers in controllers or
    through the web server.

## Change a response

PSR-7 responses are immutable: `withHeader()` returns a new response. Return it from a
`response.header` listener:

```php-inline
use Naf\Core\Event;
use Psr\Http\Message\ResponseInterface;
use function Naf\event;

event()->listen(Event::RESPONSE_HEADER, function (ResponseInterface $response) {
    return $response->withHeader('X-Application', 'My NAF app');
});
```

The returned response becomes the next header listener's argument. Listeners run in priority
order, with equal priorities preserving registration order. Returning a response from
`controller.called` or `response.send` does not replace the response being sent.
The `exception` hook uses `dispatchForResponse()`: it selects the last returned response
without chaining replacements. See [Errors and aborting](errors.md).

The response-body and response-end events are too late to change headers. Raw fatal-error
emission can bypass this normal event path; do not depend on these listeners for cleanup
that must run after every possible PHP failure.
