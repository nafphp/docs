# Events

NAF includes a minimal yet powerful event system that allows you to hook into different parts of the application lifecycle.

You can register listeners for specific events and execute custom code when those events are fired.

---

## Listening for Events

You can listen to events by calling the `listen()` method via the `event()` helper.

```php
use function Naf\event;

event()->listen('user.registered', function ($user) {
    // Handle the user registration event
});
```

- The first argument is the event name (a string).
- The second argument is a callable that will be executed when the event is dispatched.

You can register multiple listeners for the same event.

---

## Dispatching Events

You can fire (dispatch) events using the `dispatch()` method:

```php
use function Naf\event;

event()->dispatch('user.registered', $user);
```

- The first argument is the event name.
- Additional arguments are passed to the listeners as parameters.
- All listener responses are collected into an array and returned.

---

## Example: Custom Event Flow

```php
use function Naf\event;

// Register a listener
event()->listen('product.created', function ($product) {
    logger()->info('Product created: ' . $product->id);
});

// Dispatch the event
$product = new Product();
event()->dispatch('product.created', $product);
```

---

## Built-in Events

NAF fires several built-in events during the request lifecycle.  
You can hook into these to customize behavior without modifying core code.

| Event Name | When it fires | Payload | Typical Use |
|:---|:---|:---|:---|
| `request.start` | At the very beginning of `run()` or `forward()` | `$_SERVER`, optional request objects | Logging, preprocessing global request data |
| `route.matching` | Before route matching starts | `$uri`, `$method` | URL rewriting, redirections, special cases |
| `route.matched` | After a route has been found | `$route` (array or object) | Auth checks, feature toggles |
| `route.not_found` | If no route is found | `$uri`, `$method` | Custom 404 handling, statistics |
| `controller.calling` | Before calling the controller action | `$controller`, `$method`, `$params` | Controller overloading, parameter manipulation |
| `controller.called` | After the controller action returns | `$controller`, `$method`, `$response` | Post-processing, adding headers |
| `response.sending` | Before sending the response | `$response` | Caching, injecting headers, modifying output |
| `request.end` | At the very end after sending response | Time measurement, memory usage | Logging, performance analysis |

---

## Summary

- Use `event()->listen(event, callback)` to register event listeners.
- Use `event()->dispatch(event, payload...)` to fire events.
- Multiple listeners can be registered per event.
- NAF fires several built-in events you can hook into for full control over the request flow.
- Event responses are collected and returned as an array.