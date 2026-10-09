---
title: Controllers
---

# Controllers

A controller handles a matched request: it checks input, calls application logic and returns
a response. In NAF, the handler can be an ordinary class method or a closure returning
`Psr\Http\Message\ResponseInterface`. No base controller is required.

If you have completed [Your first application](first-app.md), you have already used both an
HTML action and a JSON action. This chapter explains how to add more actions and give them
the services they need. The snippets assume the same bootstrapped application.

## Controller classes

Save this as `app/Controllers/HelloController.php` in an application mapping `App\\` to `app/`:

```php
<?php
namespace App\Controllers;

use Psr\Http\Message\ResponseInterface;
use function Naf\json;

final class HelloController
{
    public function show(string $name): ResponseInterface
    {
        return json(['hello' => $name]);
    }
}
```

Register it in `app/routes.php`:

```php-inline
use App\Controllers\HelloController;
use function Naf\route;

route()->add('GET', '/hello/{name}', [HelloController::class, 'show'], 'hello');
```

The placeholder `{name}` matches the argument `$name`. These are **named arguments**, so
changing the method argument to `$person` without changing the route will fail.

## Closures

```php-inline
use function Naf\{response, route};

route()->add('GET', '/ping', fn() => response('Pong!'), 'ping');
```

Return a response even when the handler has no work to do. `response('', 204)` creates an
empty success response; `json($data)` creates JSON with the correct content type.
`Naf\View\render()` returns an HTML response when `naf/view` is installed.

## Dependencies

As an action grows, move reusable business rules into a service and declare it in the
controller's constructor. The action can then concentrate on HTTP input and its response.

With NAF's default `AutoResolvingContainer`, controllers are built through `make()`.
Declare services in the constructor; concrete classes with resolvable dependencies need no
container registration:

```php-inline
namespace App\Controllers;

use App\Services\ProductService;
use Psr\Http\Message\ResponseInterface;
use function Naf\json;

final class ProductController
{
    public function __construct(private ProductService $products) {}

    public function index(): ResponseInterface
    {
        return json($this->products->all());
    }
}
```

`ProductService` is your application class, with an `all()` method returning product data.
Register `[ProductController::class, 'index']` as the route handler. NAF constructs the
controller, the service and its resolvable concrete dependencies automatically.

Bind required interfaces to implementations in `bootstrap.php`. For dependencies needing
scalar configuration or custom setup, register a factory under the dependency's class or
interface name. Scalar constructor parameters are not looked up by name in the container.

Injection is into the constructor; action method arguments still come from route parameters.
See [Dependency Injection](dependency-injection.md) for resolution rules and the difference
between `get()` and `make()`.

See [Application lifecycle](lifecycle.md) for construction timing and [Testing](testing.md) for handler verification.
