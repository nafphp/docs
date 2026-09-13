---
title: Dependency Injection
---

# Dependency Injection

A place to put the things your application needs, so a controller can ask for a mailer
without knowing how to build one. The container is PSR-11, so anything expecting a standard
container accepts it.

It also resolves constructors it has never been told about: ask for a class, and the
container builds it from the types in its signature. That keeps the wiring you write down
to the cases where a default would be wrong.

## The Container

The application container is reached through the `app()` helper, imported with
`use function Naf\app;`.

```php
use function Naf\app;

$container = app()->container();
```

The container follows the PSR-11 `ContainerInterface` standard.

---

## Registering Services

You can register services manually in the container, typically during application bootstrapping.

Example: Register a custom service:

```php
app()->container()->set('productService', function () {
    return new \App\Services\ProductService();
});
```

- The service is registered under a simple **string key** (e.g., `'productService'`).
- The value is a closure that returns the instance.
- Services are created lazily and cached as singletons.

---

## Using Services

You retrieve services manually from the container wherever you need them:

```php
$productService = app()->container()->get('productService');

$products = $productService->all();
```

There is no automatic constructor injection — you stay fully in control.

---

## Example: ProductService in a Controller

Register your service:

```php
app()->container()->set('productService', function () {
    return new \App\Services\ProductService();
});
```

Using it in a controller:

```php
namespace App\Controllers;

use function Naf\app;
use function Naf\View\render;

class ProductController
{
    public function list()
    {
        /** @var \App\Services\ProductService $productService */
        $productService = app()->container()->get('productService');

        $products = $productService->all();

        return render('products.list', ['products' => $products]);
    }
}
```

- Fetch your services **inside your methods**.
- The service is automatically cached after the first retrieval.
