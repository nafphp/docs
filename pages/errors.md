# Error Handling

NAF provides a simple and flexible mechanism for handling errors like 404 (Not Found) and 500 (Internal Server Error).

By default, NAF uses internal error views located in the framework core.  
However, you can easily override these pages in your project.

---

## Default Error Pages

If an error occurs, NAF will:

1. First check for a custom error page in your `app/views/errors/` directory.
2. If no custom page exists, it falls back to the default built-in page.

Built-in default pages exist for:

- `404` — Not Found
- `500` — Internal Server Error

---

## Overriding Error Pages

You can override any default error page by creating a file in your project at:

- `app/views/errors/404.phtml`
- `app/views/errors/500.phtml`

Example: Custom 404 page:

```php
<?php use function Naf\s; ?>

<h1>Page not found</h1>
<p>The page <?= s($path) ?> does not exist.</p>
```

- NAF automatically passes basic information like the requested path into your error view.
- Use the `s()` helper to safely escape any output.

---

## Manually Aborting Requests

Sometimes you want to stop execution manually and send an error response.  
NAF provides the global `abort()` helper for this.

```php
use function Naf\abort;

abort(404, 'The requested page was not found.');
```

- Immediately stops execution.
- Sends the specified error page (e.g., 404, 500, etc.).
- Optionally pass a custom message.

### abort() Function

```php
function abort(int $statusCode = 404, string $message = ''): never
{
    $response = response(view('errors.' . $statusCode, [
        'statusCode' => $statusCode,
        'message' => s($message)
    ]), 500);
    send_response($response);
    exit(0);
}
```

- Renders the error view from `app/views/errors/{$statusCode}.phtml`.
- Sends the response immediately and exits the application.

---

## Handling Uncaught Exceptions

If an uncaught exception occurs during request processing, NAF:

1. Automatically catches the exception.
2. Sends a `500 Internal Server Error` response.
3. Uses the custom `app/views/errors/500.phtml` page if available.

You don't have to manually catch exceptions unless you want to customize behavior.

---

## Summary

- Create `app/views/errors/404.phtml` and/or `500.phtml` to override default error pages.
- Use the `abort()` helper to manually stop execution and send an error response.
- Uncaught exceptions automatically result in a 500 error page.
- Always use the `s()` helper to safely escape any dynamic content in error pages.