In NAF, a **controller** is anything that handles an incoming HTTP request.  
This can be either:

- a **controller class** method, or
- an **anonymous function (Closure)**.

This section explains both options.

## Controller Classes

You can define a controller as a simple PHP class with public methods.

```php
namespace App\Controllers;

use function Naf\render;

class HelloController
{
    public function index()
    {
        return render('hello', ['name' => 'World']);
    }
}
```

- **Namespace**: Controllers are typically placed in `App\Controllers`.
- **Method**: The method name should match the one you defined in your route.
- **Return**: The method must return a `Psr\Http\Message\ResponseInterface`.

### Defining a Route to a Controller

```php
// app/routes.php

route()->add('GET', '/hello', [HelloController::class, 'index']);
```

When a user visits `/hello`, NAF:

1. Instantiates the `HelloController`.
2. Calls the `index()` method.
3. Sends the returned Response to the browser.

## Closures as Controllers

Instead of using a class, you can define a route directly with a Closure:

```php
// app/routes.php

use function Naf\response;

route()->add('GET', '/ping', function () {
    return response('Pong!');
});
```

- Closures must also return a `Psr\Http\Message\ResponseInterface`.
- Useful for small endpoints, quick APIs, or simple prototyping.

## Route Parameters

If your route contains dynamic segments, NAF passes them automatically to your handler:

```php
// app/routes.php

route()->add('GET', '/user/{id}', [UserController::class, 'profile']);
```

Controller example:

```php
namespace App\Controllers;

use function Naf\render;

class UserController
{
    public function profile($id)
    {
        return render('user-profile', ['id' => $id]);
    }
}
```

Closure example:

```php
route()->add('GET', '/order/{orderId}', function ($orderId) {
    return response("Order ID: {$orderId}");
});
```

- Parameters are injected based on their **order**.
- Parameter names in methods or closures do not have to match the URL placeholders — only the **position** matters.

## Returning Responses

Every handler (whether class method or closure) must return a `Psr\Http\Message\ResponseInterface`.

Helper functions available:

| Helper | Description |
|:---|:---|
| `render($template, $variables = [])` | Renders a view and returns an HTML Response |
| `response($content)` | Creates a basic text response |

## When to use Controller Classes vs. Closures

| Use Case | Recommended Approach |
|:---|:---|
| Larger, structured application logic | Controller class |
| Handling multiple related routes (e.g., UserController, PostController) | Controller class |
| Small, isolated endpoints | Closure |
| Quick API prototypes or testing | Closure |
| You want to group logic and share methods | Controller class |
| You just need a quick one-off response | Closure |