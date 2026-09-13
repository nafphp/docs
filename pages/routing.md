# Routing

A route says which HTTP method and path lead to which piece of your code. There is no
annotation scanning and no route cache to rebuild: routes are a PHP file that runs at
startup, so a route is a line you can read.

Every route past the first needs a name. That is not decoration — the name is how you
generate URLs, how the active-navigation helper knows where it is, and how a route is
exempted from a CSRF check.

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

## Seeing what is registered

```bash
vendor/bin/naf route:debug
```

Prints every route the application knows, with its method, path and name. Useful when a
request hits a 404 you did not expect: either the route is not there, or it is there under
a path that differs from the one you are asking for.

It needs [`naf/cli`](console.md).
