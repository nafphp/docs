# Routing

NAF provides a simple and powerful routing system based on HTTP methods and URIs.  
Routes map incoming requests to controller methods or closures with minimal configuration.

---

## Defining Routes

Routes are defined inside the `app/routes.php` file.

Example:

```php
// app/routes.php

route()->add('GET', '/hello', [HelloController::class, 'index']);
```

- `'GET'` → HTTP method (`'POST'`, `'PUT'`, `'DELETE'`, etc. are also supported)
- `'/hello'` → URL path
- `[HelloController::class, 'index']` → Controller and method to handle the request

---

## Using Closures

You can also define a route with a closure instead of a controller:

```php
// app/routes.php

route()->add('GET', '/ping', function () {
    // Handle the request here
});
```

- Useful for small endpoints, prototypes, or quick tests.

---

## Route Parameters

Dynamic URL segments can be defined using `{}`:

```php
// app/routes.php

route()->add('GET', '/user/{id}', [UserController::class, 'show']);
```

In the controller:

```php
namespace App\Controllers;

class UserController
{
    public function show($id)
    {
        // $id contains the value from the URL
    }
}
```

- Route parameters are automatically passed to your controller method or closure.
- The order of placeholders matches the method's parameters.

---

## Supported HTTP Methods

NAF supports all standard HTTP methods:

- `GET`
- `POST`
- `PUT`
- `PATCH`
- `DELETE`
- (others like `OPTIONS` or `HEAD` are also possible)
