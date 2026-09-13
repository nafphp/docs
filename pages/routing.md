---
title: Routing
---

# Routing

Define routes in `app/routes.php`. Each maps an HTTP method and path to a callable returning
a PSR-7 response. Use a unique name for every route: a second unnamed route throws, and
reusing a name replaces the earlier registration.

## Defining routes

```php
use App\Controllers\HomeController;
use function Naf\{response, route};

route()->add('GET', '/', [HomeController::class, 'index'], 'home');
route()->add('GET', '/ping', fn() => response('Pong!'), 'ping');
```

The route name is the fourth argument. The methods `GET`, `POST`, `PUT`, `PATCH`, `DELETE`,
`OPTIONS` and `HEAD` can all be registered, but each needs its own matching registration.
A GET route does not automatically provide HEAD or OPTIONS.

## Route parameters

```php
use function Naf\{json, route};

route()->add('GET', '/users/{id}', function (string $id) {
    return json(['id' => $id]);
}, 'users.show');
```

**Parameter names must match the placeholders.** The dispatcher passes a named array:
`{id}` must reach `$id`, not `$userId`. The same rule applies to controller methods.
Values are URL path segments represented as strings; validate or convert them as needed.

Routes are matched in registration order. Put a literal route such as `/users/new` before
`/users/{id}` if both exist. Literal characters outside placeholders are escaped for matching.

## Generate a URL

```php
use function Naf\route;

$url = route('users.show', ['id' => 42]); // /users/42
```

Pass every placeholder. Values are substituted as given; encode user-controlled path segments
with `rawurlencode()` when generating a URL. Route names also identify CSRF exemptions and
active navigation:

```php
route()->current();                  // current route name, or null
route()->active('users.show');       // 'active' when it matches, otherwise ''
```

## See what is registered

```bash
composer require naf/cli
vendor/bin/naf route:debug
```

This prints method, path and name. A 404 often means the method or path differs from the
registration. An entirely empty application's GET `/` has a built-in welcome response;
register your own home route for application behaviour.
