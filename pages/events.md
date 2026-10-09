---
title: Events
---

# Events

Listeners are callables registered during bootstrap. Custom events can carry any payload:

```php-inline
use function Naf\{event, log};

event()->listen('product.created', function (object $product) {
    log()->info('Product created', ['id' => $product->id]);
});

// After your application creates a product:
event()->dispatch('product.created', $product);
```

`listen($event, $listener, $priority = 0)` runs higher priorities first.
`dispatch()` returns an array of listener results. Use closures or `[ListenerClass::class, 'handle']`;
NAF constructs class-based listeners through the default container.

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

The last returned `ResponseInterface` is used. Every listener receives the original
response argument; returned replacements are not passed to subsequent listeners. Returning a response from `controller.called` or
`response.send` does not replace the response being sent. The `exception` hook also supports
returned responses; see [Errors and aborting](errors.md).

The response-body and response-end events are too late to change headers. Raw fatal-error
emission can bypass this normal event path; do not depend on these listeners for cleanup
that must run after every possible PHP failure.
