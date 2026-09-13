# Guard

NAF includes a central `Guard` class designed to simplify and secure common low-level operations like path validation, output escaping, and CSRF token handling.

The `Guard` focuses on security-by-default, helping to protect your application against common attack vectors such as Local File Inclusion (LFI), Cross-Site Scripting (XSS), and Cross-Site Request Forgery (CSRF).

You can access the `Guard` instance anywhere via the global helper:

```php
guard()
```

---

## Features

The `Guard` provides several safety-focused utilities:

| Method | Purpose |
|:-------|:--------|
| `guard()->safePath($path)` | Validate paths against traversal, stream wrappers, and illegal characters |
| `guard()->safeOutput($value)` | Escape strings or arrays for safe HTML output |
| `guard()->csrf()` | Access CSRF token generation and validation |

---

## Path Safety: `safePath()`

```php
guard()->safePath('user.profile');
```

Validates that a given path:
- Is non-empty
- Does not contain traversal (`..`)
- Is not an absolute path
- Does not contain stream wrappers (`://`)
- Only contains `[A-Za-z0-9_/.-]` characters

> ✅ If the path is unsafe, an `InvalidArgumentException` is thrown.

Typical usage includes view resolution, file loading, and any file system operation that relies on user-provided input.

---

## Output Escaping: `safeOutput()`

```php
guard()->safeOutput('Hello <script>alert("xss")</script>');
// Outputs: Hello &lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;

guard()->safeOutput(['title' => 'My <b>Title</b>']);
```

- If given a **string**, escapes it for safe HTML output using `htmlspecialchars()`.
- If given an **array**, recursively escapes each element.
- Always uses `UTF-8` encoding and `ENT_QUOTES` mode for maximum compatibility.

> ✅ Protects your templates and outputs against accidental XSS.

---

## CSRF Token Management: `csrf()`

The `Guard` also handles CSRF protection internally.  
You can generate and validate CSRF tokens easily:

```php
$token = guard()->csrf()->generate();
```

This:
- Starts the session (if not already started)
- Creates a CSRF token if none exists
- Returns the token for use in forms

When validating a submitted token:

```php
if (!guard()->csrf()->validate($_POST['_csrf'] ?? '')) {
    abort(419, 'Invalid CSRF token');
}
```

> ✅ The CSRF token stays valid across multiple forms and tabs, and only rotates manually (e.g., after login/logout).

---

## 🛠 Example Usage

**In a form:**

```php
<form method="POST" action="/submit">
    <input type="hidden" name="_csrf" value="<?= guard()->csrf()->generate() ?>">
    ...
</form>
```

**When processing the request:**

```php
if (!guard()->csrf()->validate($_POST['_csrf'] ?? '')) {
    abort(419, 'Invalid CSRF token');
}
```

---

## Summary

- The `Guard` protects your application at critical input/output boundaries.
- It validates file paths safely, preventing file inclusion vulnerabilities.
- It escapes output to prevent XSS without needing a full template engine.
- It handles CSRF token generation and validation automatically and securely.
- It is available globally via `guard()` for minimal boilerplate.

---

> ✅ Best practice: Always validate external input through `guard()` before using it in filesystem operations or rendering dynamic output.