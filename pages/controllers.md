---
title: Controllers
---

# Controllers

A controller is a class method or closure returning `Psr\Http\Message\ResponseInterface`.
No base controller is required. [Your first application](first-app.md) provides a complete example.

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

```php
use App\Controllers\HelloController;
use function Naf\route;

route()->add('GET', '/hello/{name}', [HelloController::class, 'show'], 'hello');
```

The placeholder `{name}` matches the argument `$name`. These are **named arguments**, so
changing the method argument to `$person` without changing the route will fail.

## Closures

```php
use function Naf\{response, route};

route()->add('GET', '/ping', fn() => response('Pong!'), 'ping');
```

Return a response even when the handler has no work to do. `response('', 204)` creates an
empty success response; `json($data)` creates JSON with the correct content type.
`Naf\View\render()` returns an HTML response when `naf/view` is installed.

## Dependencies

With NAF's default `AutoResolvingContainer`, controller constructors are built through
`make()`. Concrete dependencies can be constructed recursively; register interfaces,
scalar configuration and services needing custom factories in the container.

```php
// Application bootstrap, before app()->run(). ProductService is your own class.
use App\Services\ProductService;
use function Naf\app;

app()->container()->set(ProductService::class, fn() => new ProductService());
```

A controller may then declare `__construct(private ProductService $products)`.
See [Dependency Injection](dependency-injection.md) for the difference between `get()` and `make()`.
