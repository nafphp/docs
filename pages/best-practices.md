---
title: Best practices
---

# Best Practices

NAF gives you a lot of flexibility and freedom.  
Following a few simple best practices can help keep your project clean, scalable, and maintainable.

---

## Keep Controllers Thin

Controllers should focus on handling HTTP-specific logic:  
**Receiving requests, calling services, and returning responses.**

Move heavy business logic into separate service classes.

Example:

```php
// Good: Controller is only responsible for flow control
public function create()
{
    $productService = app()->container()->get('productService');
    $product = $productService->create($_POST);

    return redirect('/products');
}
```

---

## Use Services for Business Logic

Complex operations (e.g., creating users, processing orders) should be done inside dedicated service classes.

Example:

```php
namespace App\Services;

class ProductService
{
    public function create(array $data)
    {
        // Validation, database operations, etc.
    }
}
```

- Keeps your code modular.
- Makes testing and maintenance easier.

---

## Use Events to Decouple Features

Instead of hardcoding everything, use `event()->dispatch()` and `event()->listen()`  
to make your application more flexible and extensible.

Example:

```php
event()->dispatch('user.registered', $user);
```

- Other parts of your app can react to events **without** changing the core code.

---

## Handle Errors Cleanly

Always use the `abort()` helper when something goes wrong.

Example:

```php
$product = database()->find('products', $id);

if (!$product) {
    abort(404, 'Product not found.');
}
```

- Makes sure that the user sees proper error pages.
- Keeps your controller flow clean and predictable.

---

## Organize Config and Services

- Keep all important configuration in `app/config.php`.
- Use the container (`app()->container()`) to manage your services centrally.
- Prefer **string keys** like `'productService'`, `'userRepository'` instead of full class names.

Good example:

```php
app()->container()->set('userRepository', function () {
    return new \App\Repositories\UserRepository();
});
```

---

## Write Custom Helpers if Needed

If you find yourself repeating common tasks (like escaping output or creating responses),  
feel free to add your own global helpers.

NAF encourages building **small, reusable tools** that fit your needs.

Example:

```php
use function Naf\View\s;

<h1>Hello, <?= s($user->name) ?>!</h1>
```
