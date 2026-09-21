---
title: Events
---

# Events

Listeners are callables registered during bootstrap. Custom events can carry any payload:

```php
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

## An event can be an object

Since **v0.2.6** the event may be an object, in which case its class is the name and the
object itself is the payload:

```php
final class OrderShipped
{
    public function __construct(public string $order) {}
}

event()->listen(OrderShipped::class, fn(OrderShipped $shipped) => log()->info($shipped->order));
event()->dispatch(new OrderShipped('A-1'));
```

`listen()` needs nothing for this — `::class` is a string like any other name — so an
application converts one event at a time or none. Nothing is required of the class: no
interface, no base class, no marker.

What it buys is what a string cannot. A misspelled class is an error where it is written,
while a misspelled event name is a listener that never runs and never says so. An IDE can find
every listener of an event and rename one as a refactoring. And the payload has a declared
shape instead of a docblock describing variadic arguments — which matters most for events a
listener is meant to change something in, where the shape of what may be edited *is* the
contract.

One thing to know before converting an event that already exists: names and class names share
one key space, so converting is a **rename**. A listener registered on the old string stops
hearing it, silently. Convert the listeners in the same change.

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

```php
use Naf\Core\Event;
use Psr\Http\Message\ResponseInterface;
use function Naf\event;

event()->listen(Event::RESPONSE_HEADER, function (ResponseInterface $response) {
    return $response->withHeader('X-Application', 'My NAF app');
});
```

The last returned response is used. Returning a response from `controller.called` or
`response.send` does not replace the response being sent. The `exception` hook also supports
returned responses; see [Errors and aborting](errors.md).

The response-body and response-end events are too late to change headers. Raw fatal-error
emission can bypass this normal event path; do not depend on these listeners for cleanup
that must run after every possible PHP failure.
