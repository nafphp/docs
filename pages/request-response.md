# Response Handling

In NAF, every route must return a valid HTTP response that implements `Psr\Http\Message\ResponseInterface`.

To make this easy, NAF provides global helper functions for generating different types of responses.

---

## The response() Helper

The `response()` function creates a simple HTTP response with a body.

```php
use function Naf\response;

return response('Hello World');
```

- Accepts a **string** for plain text or HTML content.
- Sets the `Content-Type` header to `text/html; charset=UTF-8` by default.

**Important:**  
If you want to send JSON data, you must use the `json()` helper explicitly.

---

## The json() Helper

Use the `json()` helper to create a proper JSON HTTP response:

```php
use function Naf\json;

return json(['message' => 'Success']);
```

- Serializes the given array or object to JSON.
- Sets the `Content-Type` header to `application/json; charset=UTF-8`.
- Allows you to optionally set a custom status code.

Example with a custom status:

```php
return json(['error' => 'Unauthorized'], 401);
```

---

## The render() Helper

Use the `render()` helper to render a view and return it wrapped in a response:

```php
use function Naf\render;

return render('home', ['name' => 'World']);
```

- Loads the specified view from `app/views/` using dot notation.
- Escapes variables safely using `s()`.
- Wraps the output into a `text/html` response.

---

## Redirect Responses

You can create a redirect response using the `redirect()` helper:

```php
use function Naf\redirect;

return redirect('/login');
```

- Sends a 302 redirect by default.
- Optionally, you can specify a different HTTP status code (e.g., 301).

Example:

```php
return redirect('/dashboard', 301);
```

---

## Custom Responses

For full control, you can manually create responses:

```php
$response = new \Naf\Http\Response();
$response->getBody()->write('Custom content');
return $response->withStatus(202);
```

- Set custom headers, status codes, and body manually.
- Useful for advanced use cases or non-standard responses.

---

## Summary

- Use `response(string)` for plain text or HTML.
- Use `json(array|object)` for JSON API responses.
- Use `render(view, variables)` to return rendered HTML views.
- Use `redirect(url, status)` to redirect users to another page.
- Always return a valid PSR-7 Response.