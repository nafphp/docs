---
title: Controllers
---

# Controllers

A controller handles a matched request: it checks input, calls application logic and returns
a response. In NAF, the handler can be an ordinary class method or a closure returning
`Psr\Http\Message\ResponseInterface`. No base controller is required.

The examples assume the bootstrap from [Your first application](first-app.md) and the
starter's Composer mapping of `App\` to `app/`. Use a disposable project: the complete
`app/routes.php` below replaces its demonstration routes. The controller examples need only
the core; the HTML response helper mentioned later needs `naf/view`.

## Controller classes

Create `app/Controllers/HelloController.php`. The namespace and file path must match
Composer's mapping, including the capital **C** in `Controllers`:

```php title="app/Controllers/HelloController.php"
<?php

declare(strict_types=1);

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

Replace `app/routes.php` with these named routes. The first points to a public controller
method; the second uses a closure:

```php title="app/routes.php"
<?php

declare(strict_types=1);

use App\Controllers\HelloController;
use Psr\Http\Message\ResponseInterface;

use function Naf\{json, response, route};

route()->add('GET', '/hello/{name}', [HelloController::class, 'show'], 'hello');
route()->add('GET', '/ping', static fn(): ResponseInterface =>
    response('Pong!', 200, ['Content-Type' => 'text/plain; charset=UTF-8']), 'ping');
```

Start the server from the project root with `php -S 127.0.0.1:8000 -t public`, then request:

```bash
curl http://127.0.0.1:8000/hello/Ada
curl http://127.0.0.1:8000/ping
```

The first returns `{"hello": "Ada"}` as JSON; the second returns `Pong!` as plain text.

## From a route to a response

Registering `[HelloController::class, 'show']` stores a class name and method name; it does
not construct the controller while loading the route file. For a matching request, NAF:

1. Matches the request method and path and collects the route parameters.
2. Retrieves a controller registered under its class name, or builds an unregistered
   controller through the default container's `make()`. Constructor dependencies are
   resolved at this point.
3. Calls the public action with the route parameters as named arguments.
4. Checks that the result implements `ResponseInterface`, then passes it to the response
   pipeline for headers and body emission.

The `controller.calling` and `controller.called` [events](events.md#request-lifecycle) surround
the action call. A closure follows the same request and response path without controller
construction. Application service registrations belong in `bootstrap.php`, before
`app()->run()` handles the request.

## Closures

The `/ping` route above has no state or dependencies, so its response fits in a closure.
A closure can also call application services, validate input and return JSON or HTML. It
has the same response contract as a class method.

## Choose a class or closure { #when-to-use-controller-classes-vs-closures }

| Situation | Useful starting point |
|---|---|
| A small endpoint with one response | A closure beside its route |
| Several related actions, such as listing and showing products | A controller class with public action methods |
| Required services shared by those actions | A controller with constructor injection |
| Reusable business rules | An application service called by either kind of handler |

Move a growing closure into a class when grouping actions or declaring dependencies makes
it easier to read and test. The route's method, path and name can stay the same. Keep HTTP
input and response decisions in the handler and reusable business rules in services.

## Route parameters

The placeholder `{name}` in `/hello/{name}` reaches `$name` in `HelloController::show()`.
Names must match: changing the method argument to `$person` without changing the
placeholder fails. The dispatcher uses **named arguments**, not positional injection.
This applies to closures too; declaration order can differ:

Add this route to your existing `app/routes.php` to try two placeholders:

```php-inline
route()->add('GET', '/teams/{team}/members/{member}',
    static function (string $member, string $team): ResponseInterface {
        return json(['team' => $team, 'member' => $member]);
    }, 'teams.member');
```

`GET /teams/alpha/members/ada` returns `{"team": "alpha", "member": "ada"}`. Both values
are path segments represented as strings. Validate their format and look up any referenced
resource; a route match alone does not prove that a product or user exists.

Query parameters, form fields and JSON data are read through `request()` or `param()`,
not supplied as extra action arguments. An action parameter typed as a service is not
method injection. See [Requests and responses](request-response.md) for input sources.

## Dependencies

As an action grows, move reusable business rules into a service and declare it in the
controller's constructor. The action can then concentrate on HTTP input and its response.

This complete example groups two product actions around a shared service. Create
`app/Services/ProductService.php`; its sample catalogue is in memory and needs no database:

```php title="app/Services/ProductService.php"
<?php

declare(strict_types=1);

namespace App\Services;

final class ProductService
{
    private const array PRODUCTS = [
        'notebook' => ['id' => 'notebook', 'name' => 'Notebook'],
        'pencil' => ['id' => 'pencil', 'name' => 'Pencil'],
    ];

    public function all(): array
    {
        return array_values(self::PRODUCTS);
    }

    public function find(string $id): ?array
    {
        return self::PRODUCTS[$id] ?? null;
    }
}
```

Create `app/Controllers/ProductController.php`. The constructor declares the required
service; the actions handle HTTP input and responses:

```php title="app/Controllers/ProductController.php"
<?php

declare(strict_types=1);

namespace App\Controllers;

use App\Services\ProductService;
use Psr\Http\Message\ResponseInterface;

use function Naf\json;

final class ProductController
{
    public function __construct(private ProductService $products)
    {
    }

    public function index(): ResponseInterface
    {
        return json(['products' => $this->products->all()]);
    }

    public function show(string $id): ResponseInterface
    {
        if (preg_match('/^[a-z0-9-]{1,40}$/D', $id) !== 1) {
            return json(['error' => 'Invalid product identifier'], 400);
        }

        $product = $this->products->find($id);
        if ($product === null) {
            return json(['error' => 'Product not found'], 404);
        }

        return json($product);
    }
}
```

Add the product routes to `app/routes.php`:

```php-inline
use App\Controllers\ProductController;

route()->add('GET', '/products', [ProductController::class, 'index'], 'products.index');
route()->add('GET', '/products/{id}', [ProductController::class, 'show'], 'products.show');
```

`GET /products` lists two products, `/products/notebook` returns one, `/products/missing`
returns JSON with status 404, and `/products/INVALID` returns JSON with status 400.
The default `AutoResolvingContainer` builds both classes without a `set()` registration
because they are concrete and their constructors can be resolved.

Bind required interfaces to implementations in `bootstrap.php`. For dependencies needing
scalar configuration or custom setup, register a factory under the dependency's class or
interface name. Scalar constructor parameters are not looked up by name in the container.

Injection is into the constructor; action method arguments still come from route parameters.
See [Dependency Injection](dependency-injection.md) for resolution rules and the difference
between `get()` and `make()`.

## Returning responses

Every action and closure returns a `ResponseInterface`. Choose the helper by the response
you need and import it from its owning namespace:

| Helper | Result and use |
|---|---|
| `Naf\response($body, $status, $headers)` | A response with the body, status and headers you specify; set `Content-Type` explicitly when it matters |
| `Naf\json($data, $status = 200)` | JSON with `Content-Type: application/json; charset=UTF-8` |
| `Naf\View\render($template, $variables = [])` | A rendered HTML body in a response; requires `naf/view` |
| `Naf\redirect($url, $status = 302)` | A redirect; generate internal URLs with `route('name', $parameters)` |

`response('', 204)` creates an empty success response. Returning a string, an array or
`Naf\View\view()` directly does not satisfy the response contract. Use `json()` for an
array and `render()` for a template. `abort(404, 'Product not found.')` throws into the
[error handler](errors.md); it does not return a response to the action.

PSR-7 responses are immutable. Return the new object when changing a header or status:

```php-inline
return json(['accepted' => true], 202)->withHeader('X-Application', 'Catalogue');
```

The framework emits the returned response. Handlers do not need to echo a body, call
`header()` or exit the process.

## If the result is different

| What you see | What to check |
|---|---|
| Controller class not found | The namespace, Composer's `App\` mapping and the case of `app/Controllers`; run `composer dump-autoload` after changing mappings |
| `Unknown named parameter` | Match every route placeholder to the action's argument name |
| A required service cannot be resolved | Put it in the constructor; bind interfaces and scalar configuration before `app()->run()` |
| `Controller … has no callable action …` | The route names the correct public method |
| `No valid response returned.` | Every action path returns a `ResponseInterface`, including validation failures |

Continue with [Routing](routing.md), [Views and templates](views.md),
[Application lifecycle](lifecycle.md) and [Testing](testing.md) for related behavior and
HTTP verification.
