---
title: Routing
---

# Routing

Define routes in `app/routes.php`. Each maps an HTTP method and path to a callable returning
a PSR-7 response. Use a unique name for every route: a second unnamed route throws, and
reusing a name replaces the earlier registration.

## Defining routes

```php-inline
use App\Controllers\HomeController;
use function Naf\{response, route};

route()->add('GET', '/', [HomeController::class, 'index'], 'home');
route()->add('GET', '/ping', fn() => response('Pong!'), 'ping');
```

The route name is the fourth argument. Register methods in upper case: `GET`, `POST`, `PUT`,
`PATCH`, `DELETE`, `OPTIONS` or `HEAD`. Request methods are compared in upper case, so a
route registered as `'get'` never matches.

With Framework **0.2.12+**, an explicit matching HEAD route takes precedence; otherwise HEAD
uses the first matching GET route and sends its metadata without content. GET handlers can
therefore also run for HEAD; keep them free of write side effects.

Explicit OPTIONS routes run normally. Without one, OPTIONS for a known path returns 204
and `Allow` without invoking a controller. This does not configure CORS; applications
configure their own cross-origin policy.

Known paths requested with an unsupported method return 405 and `Allow`; unknown paths
return 404. `Allow` includes implicit HEAD for GET and automatic OPTIONS.

??? note "Framework 0.2.10 and older"

    Each method needs its own matching registration. GET does not automatically provide
    HEAD or OPTIONS, and an unsupported method returns 404. The current starter's lock may
    still contain an older framework; see [updating the framework](compatibility.md#upgrading-to-framework-0212).

`route()->remove('name')` removes a registration and returns whether one existed. Registering
a route under an existing name replaces it in its original position.
Framework 0.2.12+ also preserves numeric string names, including `'0'`, during matching,
URL generation and removal.

## Route parameters

```php-inline
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

```php-inline
use function Naf\route;

$url = route('users.show', ['id' => 42]); // /users/42
```

Pass every placeholder as a string or integer. Framework 0.2.12+ throws
`InvalidArgumentException` for a missing or invalid value, identifying the route and parameter.
Values are substituted once, exactly as supplied. Encode each dynamic segment with
`rawurlencode()` before calling `route()`; the framework does not encode or decode it again.
Extra parameter keys are ignored; these values are path segments, not an appended query string.

```php-inline
$url = \Naf\route('files.show', ['name' => rawurlencode('annual report.pdf')]);
```

For a registered `/files/{name}` route named `files.show`, this produces
`/files/annual%20report.pdf`. Route names also identify CSRF exemptions and active navigation:

```php-inline
route()->current();                                  // current route name, or null
route()->active('users.show');                       // 'active' when it matches, otherwise ''
route()->active(['users.index', 'users.show']);      // any of several names
route()->active('users.show', 'is-current');         // a custom class name
```

## See what is registered

```bash
composer require naf/cli
vendor/bin/naf route:debug
```

This prints each route's name, method, path and handler. For the routes of
[Your first application](first-app.md):

```text
--8<-- "output/route-debug.txt"
```

A 404 means no path matched; a 405 means the path exists but does not accept the requested
method (Framework 0.2.12+). An entirely empty application's GET or HEAD `/` has a built-in
welcome response. Register your own home route for application behaviour.

See [HTTP tests](testing.md#test-http-behavior) to verify status and content through the running application.
