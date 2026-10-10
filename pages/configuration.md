---
title: Configuration
---

# Configuration

Configuration files return PHP arrays. NAF merges the core defaults, plugin configuration,
and finally `app/config.php`. Optional named sources can then override these server defaults
before plugins use configuration.

## Environment files

Place local values in `.env` at the project root:

```ini
APP_ENV=dev
DB_HOST=127.0.0.1
DB_USER=my_app
DB_PASS=change-me
```

If `.env.local` exists, it is loaded **instead of** `.env`; the two are not merged.
The loader runs when the application first boots and only fills gaps: a variable the process
already has — in `$_ENV`, or in its environment as `getenv()` sees it — keeps its value, so
what Docker or the shell sets wins over the file. naf/framework before 0.2.8 checked `$_ENV`
only; with PHP's default `variables_order`, the file then overrode the environment.
Values are simple strings: do not rely on shell interpolation, automatic boolean conversion
or stripping quotes. Keep secret files out of version control.

## Read environment values

Inside application configuration, which is loaded after the environment file:

```php-inline
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

`ENV:API_KEY` resolves recursively when the configuration is built: from `$_ENV` first, then
from the process environment. An absent value becomes `null`. The fallback needs
naf/framework 0.2.8 or newer; earlier versions read `$_ENV` alone, which PHP only fills when
`variables_order` contains `E` — the `php.ini` files PHP ships with set `GPCS`.

Reading `$_ENV` directly, as for the database values above, sees only what `$_ENV` holds.
Where the value may come from the process environment, use an `ENV:` reference or
`getenv('NAME')` and handle its `false` result.

## Application environment

`env()` returns the **environment name as a string**. It does not read arbitrary keys and
it does not return an object with `isProduction()` methods.

```php-inline
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

```php-inline
use function Naf\config;

$all = config();
$name = config('name', 'My application');
$key = config('api:key');
$url = config('api:url', 'https://api.example.com');
```

Colons traverse nested arrays. The default is used when a value is absent or `null`.
Configuration is created lazily and cached. `config()` reads values; use the named-layer API
below when an application needs overrides.

## Merge order

The merge is `array_replace_recursive(core, plugins, app)`. Application values win.
Numeric arrays are replaced by position, not appended. This is why settings such as
`csrf_exempt_routes` use named keys:

```php-inline
return ['csrf_exempt_routes' => ['oauth.token' => false]];
```

Use [plugin ordering](plugins.md#boot-order) when bootstraps depend on each other, and
[Errors and aborting](errors.md) for custom error responses.

## Load overrides before plugin boot

With **naf/framework 0.2.10+**, a host or plugin can supply `app/config_sources.php` or
`src/config_sources.php`; the first existing path wins. The file returns classes implementing
`Naf\Contracts\ConfigurationSourceInterface`. Each class has a no-argument constructor,
`name(): string` and `load(string $basePath): array`. The returned array maps colon-separated
paths to literal values. Sources run when configuration is first read, after all plugins are
registered. Plugin sources follow plugin order; the host's sources load last.

A source must read its storage directly. Calling `config()` or resolving a service that
depends on configuration would create a boot cycle. Store startup overrides outside the
database if they can change the database connection itself.

### Read a local override file

Start from the [core-only installation](install.md#core-only-project), whose Composer
autoload maps `App\` to `app/`. Update the framework and create the directories:

```bash
composer require naf/framework:^0.2.10
mkdir -p app/Configuration storage bin
```

For this isolated example, create these complete files. In an existing application, merge the
configuration entries and use private storage appropriate to its deployment.

```php title="app/config.php"
<?php

return ['feature' => true, 'servers' => ['primary', 'backup']];
```

```json title="storage/configuration.json"
{
    "feature": false,
    "servers": []
}
```

```php title="app/Configuration/StoredConfiguration.php"
<?php

declare(strict_types=1);

namespace App\Configuration;

use InvalidArgumentException;
use Naf\Contracts\ConfigurationSourceInterface;

final class StoredConfiguration implements ConfigurationSourceInterface
{
    public function name(): string
    {
        return 'stored-json';
    }

    public function load(string $basePath): array
    {
        $path = $basePath . '/storage/configuration.json';
        if (!is_file($path)) {
            return [];
        }

        $values = json_decode(file_get_contents($path), true, flags: JSON_THROW_ON_ERROR);
        if (!is_array($values)) {
            throw new InvalidArgumentException('Stored configuration must be a JSON object.');
        }

        return $values;
    }
}
```

```php title="app/config_sources.php"
<?php

use App\Configuration\StoredConfiguration;

return [StoredConfiguration::class];
```

```php title="bin/configuration-demo.php"
<?php

require dirname(__DIR__) . '/bootstrap.php';

use Naf\Core\Config;
use function Naf\app;

$configuration = app()->container()->get(Config::class);
echo json_encode([
    'feature' => $configuration->get('feature'),
    'servers' => $configuration->get('servers'),
    'source' => $configuration->source('feature'),
    'default' => $configuration->base('feature'),
], JSON_THROW_ON_ERROR) . PHP_EOL;

$configuration->overlay('stored-json', []);
echo json_encode(['reset' => $configuration->get('feature')], JSON_THROW_ON_ERROR) . PHP_EOL;
```

```bash
composer dump-autoload
php bin/configuration-demo.php
```

Expected output:

```text
{"feature":false,"servers":[],"source":"stored-json","default":true}
{"reset":true}
```

### Inspect and replace layers

| Method on `Naf\Core\Config` | Result |
| --- | --- |
| `overlay($name, $values)` | Replace the complete named layer; an empty array removes its overrides |
| `overrides($name)` | Literal path/value pairs in that layer, or an empty array |
| `base($key = null, $default = null)` | Resolved server defaults, without layers; no key returns the complete array |
| `raw($key = null)` | Server defaults retaining `ENV:NAME` references; no key returns the complete array |
| `source($key)` | The winning layer's name, `environment` for a server `ENV:` reference, otherwise `configuration` |

Later layers win. Replacing an existing layer retains its position. Values such as false,
zero, null and empty strings are preserved; `get()` still uses its fallback for null.
Array-valued overrides replace the whole array, unlike the recursive server-file merge.
An override containing `ENV:NAME` stays that literal string. These APIs change the current
configuration object; they do not persist files or rebuild services that already hold values.
Restart long-running workers after changing the storage they read at startup.

If the example fails to boot, check that the source class is autoloadable, the JSON parses,
and its keys are nonempty colon-separated paths. A missing override file returns server defaults.

See [Deployment](deployment.md#production-configuration) for production setup and [Troubleshooting](troubleshooting.md#plugins-and-configuration) for ignored values.
