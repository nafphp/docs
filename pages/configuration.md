# Configuration

NAF provides a simple yet flexible configuration system based on `.env` files, a lightweight environment service, and a powerful configuration loader.

You can manage different settings for local development, staging, and production environments.

---

## Using `.env` Files

NAF can automatically load environment variables from a `.env` file placed in the project root.

```dotenv
APP_ENV=local
APP_DEBUG=true
DB_HOST=localhost
DB_USER=root
DB_PASS=secret
```

- Each line defines a key-value pair.
- Lines starting with `#` are treated as comments.
- Values can be referenced inside configuration files or application code.

The `.env` file is loaded automatically during the bootstrap phase.

---

## Accessing Environment Variables

You can access environment variables anywhere in your code using the `env()` helper:

```php
$host = env('DB_HOST', 'localhost');
```

- The first argument is the environment variable name.
- The second argument is an optional default value if the variable is not set.

---

## Environment Detection

NAF includes a small `Environment` service to detect the current application environment.

It supports four predefined environments:

| Name | Typical Usage |
|:---|:---|
| `local` | Local development machine |
| `staging` | Preview system before going live |
| `production` | Live/real system |
| `testing` | Automated test environment |

You can check the environment using helper methods:

```php
if (env()->isLocal()) {
    ini_set('display_errors', '1');
}

if (env()->isProduction()) {
    ini_set('display_errors', '0');
}
```

Available methods:

- `isLocal()`
- `isStaging()`
- `isProduction()`
- `isTesting()`

---

## Application Configuration

NAF loads application settings through a lightweight `Config` class.

You can organize configuration into arrays and load them through the container.

A typical configuration file might look like this:

```php
return [
    'name' => 'My App',
    'api' => [
        'key' => 'ENV:API_KEY',
        'url' => 'https://api.example.com',
    ],
];
```

- Values prefixed with `ENV:` will be automatically resolved from environment variables.
- Nested arrays are supported.

---

## Accessing Configuration Values

You can access configuration values using the `config()` helper:

```php
// Get a full configuration array
$fullConfig = config();

// Get a single config value
$appName = config('name');

// Access nested configuration using "namespace" syntax
$apiKey = config('api:key');

// Provide a default value if the key is not found
$apiUrl = config('api:url', 'https://default.example.com');
```

- If the key contains a colon `:`, it is treated as a namespace separator.
- Nested configuration is traversed automatically.

---

## Internals: How Configuration Works

The `Config` class:

- Accepts an array on construction.
- Resolves all `ENV:` placeholders recursively.
- Provides `get($key, $default)` and `all()` methods for access.
- Supports simple "namespace" lookups via `:` syntax.

The `config()` helper fetches the instance from the container and allows quick access anywhere in your code.

---

## Example: Setting Error Display Based on Environment

You can configure error reporting inside `bootstrap.php` depending on the current environment:

```php
if (env()->isProduction()) {
    ini_set('display_errors', '0');
    error_reporting(E_ALL & ~E_DEPRECATED & ~E_NOTICE);
} else {
    ini_set('display_errors', '1');
    error_reporting(E_ALL);
}
```

---

## Summary

- Use `.env` files to store environment-specific settings.
- Use the `env()` helper to access variables with optional default values.
- The `Environment` service allows checking the current environment cleanly.
- Use configuration arrays with optional `ENV:` references.
- Access configuration values easily with the `config()` helper.
- Configuration supports nested access via "namespace" keys (e.g., `api:key`).
