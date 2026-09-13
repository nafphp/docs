---
title: Configuration
---

# Configuration

Configuration files return PHP arrays. NAF merges the core defaults, plugin configuration,
and finally `app/config.php`, so your application has the last word.

## Environment files

Place local values in `.env` at the project root:

```dotenv
APP_ENV=dev
DB_HOST=127.0.0.1
DB_USER=my_app
DB_PASS=change-me
```

If `.env.local` exists, it is loaded **instead of** `.env`; the two are not merged.
The loader runs when the application first boots. Existing `$_ENV` entries are preserved.
Values are simple strings: do not rely on shell interpolation, automatic boolean conversion
or stripping quotes. Keep secret files out of version control.

## Read environment values

Inside application configuration, which is loaded after the environment file:

```php
// app/config.php
return [
    'database' => [
        'host' => $_ENV['DB_HOST'] ?? '127.0.0.1',
        'username' => $_ENV['DB_USER'] ?? '',
        'password' => $_ENV['DB_PASS'] ?? '',
    ],
    'api' => ['key' => 'ENV:API_KEY'],
];
```

`ENV:API_KEY` resolves from `$_ENV`, recursively, when the configuration is built. An absent
value becomes `null`. For operating-system variables not populated into `$_ENV`, use
`getenv('NAME')` explicitly and handle its `false` result.

## Application environment

`env()` returns the **environment name as a string**. It does not read arbitrary keys and
it does not return an object with `isProduction()` methods.

```php
use Naf\Core\Environment;
use function Naf\env;

if (env() === Environment::PROD) {
    // Production-specific application behaviour.
}
```

| Value | Constant | Error output |
|---|---|---|
| `dev` | `Environment::DEV` | Detailed diagnostics for local development |
| `test` | `Environment::TEST` | Sanitized HTTP error output |
| `prod` | `Environment::PROD` | Sanitized HTTP error output |

Use **`APP_ENV=prod`** in production. Other nonempty values, including `production` and
`staging`, are treated as development-like values by the error renderer and can expose
diagnostics. If the value is absent, the error renderer uses sanitized output, but you
should still configure the environment explicitly before using `env()`.

## Read configuration

```php
use function Naf\config;

$all = config();
$name = config('name', 'My application');
$key = config('api:key');
$url = config('api:url', 'https://api.example.com');
```

Colons traverse nested arrays. The default is used when a value is absent or `null`.
Configuration is created lazily and cached; edit the files for the next request rather
than treating `config()` as a runtime setter.

## Merge order

The merge is `array_replace_recursive(core, plugins, app)`. Application values win.
Numeric arrays are replaced by position, not appended. This is why settings such as
`csrf_exempt_routes` use named keys:

```php
return ['csrf_exempt_routes' => ['oauth.token' => false]];
```

Use [plugin ordering](plugins.md#boot-order) when bootstraps depend on each other, and
[Errors and aborting](errors.md) for custom error responses.
