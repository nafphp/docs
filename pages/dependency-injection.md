# Dependency Injection

NAF provides a simple and flexible PSR-11 compliant container to manage your services and dependencies.

However, NAF does **not** automatically inject constructor parameters.  
You manually retrieve and manage your dependencies.

---

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

---

## Summary

- Access the container via `app()->container()`.
- Register services using **string keys** like `'productService'`, `'db'`, `'log'`, etc.
- Fetch services manually when needed.
- NAF does **not** automatically inject constructor arguments.
- Services behave as singletons by default (one instance per request).