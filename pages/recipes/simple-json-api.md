---
title: A JSON API without a database
---

# A JSON API without a database

Build a public, read-only product API with two endpoints: a list and a single product.
A plain PHP service supplies the example data, and the controller returns JSON responses.
There is no database, migration, template, form or session to configure.

| Result | Packages | Starting point |
|---|---|---|
| JSON list and detail endpoints with input checks and JSON errors | `naf/framework` | An empty directory, PHP 8.3+ and Composer |

Use this structure for public reference data or an existing application service. When you
need to save records, continue with the [JSON API with a database](json-api.md). For other
starting points, see [the scenario list](index.md).

## 1. Create the project

```bash
mkdir naf-catalog-api
cd naf-catalog-api
mkdir -p app/Controllers app/Services public
```

Every titled block is a complete file relative to `naf-catalog-api/`. PHP 8.3+ needs the
core's JSON and PDO extensions; no database driver or connection is used by this example.

```json title="composer.json"
{
    "name": "example/naf-catalog-api",
    "description": "A public JSON catalog built with NAF",
    "type": "project",
    "license": "MIT",
    "require": { "php": ">=8.3", "naf/framework": "^0.2.8" },
    "autoload": { "psr-4": { "App\\": "app/" } }
}
```

```gitignore title=".gitignore"
/vendor/
/.env
/.env.local
/logs/
/storage/
```

```ini title=".env"
APP_ENV=dev
```

```bash
composer install
```

Commit the generated `composer.lock` along with `composer.json`. Keep environment files
private and use `composer install` to reproduce the tested dependencies on deployment.

## 2. Bootstrap with JSON error handling

With the core installed, add the entry point and bootstrap. Set up JSON error responses here
so clients get the same response format when a later route lookup or controller fails.

```php title="public/index.php"
<?php

declare(strict_types=1);

require dirname(__DIR__) . '/bootstrap.php';
```

```php title="bootstrap.php"
<?php

declare(strict_types=1);

use Naf\Core\ErrorHandler;
use Naf\Core\Event;
use Psr\Http\Message\ResponseInterface;

use function Naf\app;
use function Naf\event;
use function Naf\json;
use function Naf\log;

define('BASE_PATH', __DIR__);

require __DIR__ . '/vendor/autoload.php';

event()->listen(Event::EXCEPTION, static function (Throwable $exception): ResponseInterface {
    $status = ErrorHandler::resolveStatusCode($exception);

    if ($status >= 500) {
        log()->error('Catalog API failed: {exception}', ['exception' => $exception]);
    }

    return json(['error' => $status >= 500 ? 'Internal server error' : 'Request refused'], $status);
});

event()->listen(Event::RESPONSE_HEADER, static function (ResponseInterface $response): ResponseInterface {
    return $response->withHeader('X-Content-Type-Options', 'nosniff');
});

app()->run();
```

The exception listener makes unknown-route and unexpected-error responses JSON too.
Unexpected exceptions are logged; the response hides their messages and stack traces, even
in this local example. Expected validation failures return a specific JSON error from the
controller. Failures before listener registration, such as a bootstrap parse error, still
depend on PHP and web server error configuration.

The default logger writes `logs/app.log` and expands message placeholders. `{exception}`
includes the exception details there; unused context entries are not written automatically.
Keep logs outside `public/` and restrict access to the application operator.

## 3. Put application data in a service

Next, give the API a source of product data. This service returns fixed records, which lets
you follow the HTTP flow before introducing a database or external integration.

```php title="app/Services/ProductCatalog.php"
<?php

declare(strict_types=1);

namespace App\Services;

final class ProductCatalog
{
    /** @return list<array{id: string, name: string, priceInCents: int}> */
    public function all(): array
    {
        return [
            ['id' => 'notebook', 'name' => 'Notebook', 'priceInCents' => 900],
            ['id' => 'pencil', 'name' => 'Pencil', 'priceInCents' => 150],
        ];
    }

    /** @return array{id: string, name: string, priceInCents: int}|null */
    public function find(string $id): ?array
    {
        foreach ($this->all() as $product) {
            if ($product['id'] === $id) {
                return $product;
            }
        }

        return null;
    }
}
```

These are deliberately fixed example records. Prices use integer cents; the API's currency
is EUR. No write endpoint is offered, and restarting PHP does not change the catalog.
The service has no HTTP dependency, so you can test or reuse it outside a controller.

## 4. Check input and return JSON

The catalog is ready to use. Add a controller to check HTTP input and turn the service's
results into responses, then register its two routes.

```php title="app/Controllers/ProductController.php"
<?php

declare(strict_types=1);

namespace App\Controllers;

use App\Services\ProductCatalog;
use Psr\Http\Message\ResponseInterface;

use function Naf\json;
use function Naf\request;

final class ProductController
{
    public function __construct(private ProductCatalog $catalog) {}

    public function index(): ResponseInterface
    {
        $input = request()->getQueryParams()['limit'] ?? '20';
        $limit = is_string($input)
            ? filter_var($input, FILTER_VALIDATE_INT, ['options' => ['min_range' => 1, 'max_range' => 100]])
            : false;

        if ($limit === false) {
            return json(['error' => 'limit must be an integer from 1 to 100.'], 400);
        }

        return json([
            'data'     => array_slice($this->catalog->all(), 0, $limit),
            'currency' => 'EUR',
        ]);
    }

    public function show(string $id): ResponseInterface
    {
        $product = $this->catalog->find($id);

        if ($product === null) {
            return json(['error' => 'Product not found.'], 404);
        }

        return json(['data' => $product, 'currency' => 'EUR']);
    }
}
```

The list endpoint reads the query string explicitly and accepts a bounded integer limit.
It rejects arrays and invalid values instead of casting them. The detail endpoint looks up
an exact catalog identifier; it does not turn the identifier into a file path or class name.
`json()` encodes the body and sets its content type. Return the response rather than echoing
JSON or calling `header()` yourself.

```php title="app/routes.php"
<?php

declare(strict_types=1);

use App\Controllers\ProductController;

use function Naf\route;

route()->add('GET', '/api/products', [ProductController::class, 'index'], 'api.products.index');
route()->add('GET', '/api/products/{id}', [ProductController::class, 'show'], 'api.products.show');
```

NAF constructs the controller and injects the concrete `ProductCatalog` automatically.
No container binding is needed for these classes. The placeholder `{id}` matches the action's
`$id` argument because route parameters are passed by name.

## 5. Run and check the result

Once the service, controller and routes are in place, start the application from its root:

```bash
composer dump-autoload
php -S 127.0.0.1:8000 -t public
```

In another terminal:

```bash
curl -i http://127.0.0.1:8000/api/products
curl -i 'http://127.0.0.1:8000/api/products?limit=1'
curl -i http://127.0.0.1:8000/api/products/notebook
curl -i 'http://127.0.0.1:8000/api/products?limit%5B%5D=1'
curl -i http://127.0.0.1:8000/api/products/missing
```

The list request returns status 200, `Content-Type: application/json`,
`X-Content-Type-Options: nosniff` and this body, apart from formatting:

```json
{
    "data": [
        {"id": "notebook", "name": "Notebook", "priceInCents": 900},
        {"id": "pencil", "name": "Pencil", "priceInCents": 150}
    ],
    "currency": "EUR"
}
```

| Request | Status | Result |
|---|---|---|
| `GET /api/products` | 200 | Both products |
| `GET /api/products?limit=1` | 200 | Only the notebook |
| `GET /api/products/notebook` | 200 | One product object |
| `limit=0`, `limit=101`, `limit=text` or `limit[]=1` | 400 | A JSON validation error |
| `GET /api/products/missing` | 404 | `{"error":"Product not found."}` |
| `GET /unknown` | 404 | `{"error":"Request refused"}` |
| Unexpected exception after bootstrap | 500 | `{"error":"Internal server error"}`; details stay in the log |

## If the result is different

| What you see | What to check |
|---|---|
| `/` returns a JSON 404 | This example registers `/api/products`, not a home route; request that URL instead |
| A product returns 404 | Use the exact identifier `notebook` or `pencil`; other identifiers are expected to fail |
| The list returns 400 | Remove the query string or use `?limit=1`; the parameter accepts integers from 1 to 100 |
| A response contains HTML | Confirm you replaced `bootstrap.php` with this example and are reaching the server for `naf-catalog-api/` |
| `Internal server error` | Read `logs/app.log` for the exception; check the service/controller paths and run `composer dump-autoload` after fixing them |

The error response deliberately keeps internal details out of the client output. Use the
local log for diagnosis rather than adding exception messages to the JSON response.
See [Troubleshooting](../troubleshooting.md) for more checks.

## Continue building

This API exposes public data and accepts no writes, so it needs no authentication or CSRF
token for these operations. Add access checks when introducing private data. When adding
writes, define authentication, authorization and input validation for those operations;
see [Handling POST requests](post-requests.md) and the [persistent API](json-api.md).

Keep HTTP input and status choices in the controller, and reusable data or business rules
in the injected service. To automate these checks, see [Testing applications](../testing.md).
Before deployment, use HTTPS, serve only `public/`, set **`APP_ENV=prod`** and configure
logging as described in [Deployment](../deployment.md).
