---
title: How plugins work
---

# Plugins

A plugin is an ordinary Composer package that declares `"type": "naf-plugin"`. That type
is the whole discovery mechanism: the framework asks Composer which installed packages have
it and boots them. There is nothing to register and no list to maintain.

It also means the type has to be right. A package that installs correctly but declares a
different type is not loaded — silently, without an error — which is exactly what happens
to a `nixphp-plugin` under NAF 0.2.

## Plugin Structure

A NAF plugin mimics the structure of a full app:

```
your-plugin/
├── app/
│   ├── config.php         // Plugin-specific configuration
│   └── views/             // Plugin-specific templates
│       └── example.phtml
├── bootstrap.php          // Bootstrap logic (routes, events, services, etc.)
└── composer.json
```

- `app/config.php` is merged into the global config.
- `app/views/` is added to the view resolver.
- `bootstrap.php` is automatically executed when the plugin is discovered.

---

## Example `composer.json`

Below is a minimal but complete `composer.json` for a NAF plugin:

```json
{
  "name": "vendor/naf-plugin-example",
  "description": "Skeleton for your first plugin when using NAF",
  "type": "naf-plugin",
  "license": "MIT",
  "authors": [
    {
      "name": "Your Name",
      "email": "your@mail.com"
    }
  ],
  "require": {
    "php": ">=8.3",
    "naf/framework": "^0.2"
  },
  "autoload": {
    "psr-4": {
      "MyPlugin\\": "app/"
    }
  },
  "minimum-stability": "stable",
  "prefer-stable": true
}
```

> ✅ Important:
> - `"type": "naf-plugin"` is required for discovery.
> - The namespace (e.g. `MyPlugin\\`) must match your plugin classes location.

Run:

```bash
composer dump-autoload
```

To ensure your classes are properly registered.

---

## Automatic Discovery

Plugins are discovered via Composer using the package `"type": "naf-plugin"`. Once installed, NAF will:

- Load `bootstrap.php`
- Merge `app/config.php`
- Register all `app/views/` templates

No manual registration is needed.

---

## Accessing Plugin Metadata

```php
use function Naf\plugin;

$plugins = plugin(); // array<string, Naf\Support\Plugin>
$view = plugin('naf/view'); // Plugin; ask only for an installed package
$view->getViewPaths();
$view->getConfigPaths();
$view->getBootstrapFile();
```

For internal use or debugging only – no need to register anything yourself.

---
## Example Plugin: Event Listener
``` plaintext
my-event-plugin/
├── app/
│   └── Listeners/
│       └── UserListener.php
└── bootstrap.php
```
**UserListener.php:**
``` php
namespace MyEventPlugin\Listeners;

use function Naf\log;

class UserListener
{
    public function onUserRegistered($user)
    {
        // Log registration, send welcome email, etc.
        log()->info('New user registered: ' . $user->email);
    }
}
```
**bootstrap.php:**
``` php
use MyEventPlugin\Listeners\UserListener;
use function Naf\{event, log};

// Register the event listener
$listener = new UserListener();
event()->listen('user.registered', [$listener, 'onUserRegistered']);

// You can also use closure-based listeners
event()->listen('user.login', function($user) {
    log()->info('User logged in: ' . $user->email);
});
```
Usage in the main application:
``` php
use function Naf\{event, log};

// After successful user registration:
$user = new User(); // Your user object
event()->dispatch('user.registered', $user);
```

---

## Example Plugin: Routing to a Controller

**Structure:**

```
my-hello-plugin/
├── app/
│   └── Controllers/
│       └── HelloController.php
├── bootstrap.php
└── composer.json
```

**HelloController.php:**

```php
namespace MyHelloPlugin\Controllers;

use Psr\Http\Message\ResponseInterface;
use function Naf\response;

class HelloController
{
    public function index(): ResponseInterface
    {
        return response('Hello from the plugin controller!');
    }
}
```

**bootstrap.php:**

```php
use MyHelloPlugin\Controllers\HelloController;
use function Naf\route;

route()->add('GET', '/plugin-hello', [HelloController::class, 'index'], 'plugin.hello');
```

Visit: `http://yourapp.local/plugin-hello`

---

## View Resolution Order

1. App `app/views/`
2. Plugins `app/views/`

---

## Config Merge Order

1. Framework defaults
2. Plugin configuration, in plugin order
3. Application configuration (`app/config.php`, or `src/config.php` as a fallback)

Later values override earlier values recursively. See [Configuration](configuration.md).

## Boot order

All discovered plugins are registered before any bootstrap runs. `hasPlugin()` says that a
plugin is registered; it does not say that its bootstrap has already run. Prefer lazy service
factories so a dependency is resolved after registration has finished.

When boot order matters, create `app/plugins.php` returning the package names to load first:

```php
<?php

return ['naf/session', 'naf/form'];
```

Other installed plugins follow. This orders installed plugins; it does not install packages or
act as an allow-list. Application routes load after plugin bootstraps. Application service
bindings belong in the root `bootstrap.php`, after the autoloader and before `app()->run()`.

The loader also accepts `src/config.php`, `src/routes.php` and `src/functions.php` when their
`app/` counterparts are absent. Keep one layout per package to avoid competing files.

## Code style and readability

For plugin contributions, follow the shared
[NAF code style](https://github.com/nafphp/docs/blob/main/CODE_STYLE.md): PER Coding Style 3.0
with descriptive local names, separate logical steps and locally aligned assignments.
The guide includes a formatter configuration and Composer commands for individual packages.
Adoption is incremental; check the package's own scripts and instructions.

Keep ordinary PHP operations simple. Add a helper or service when it has a useful
responsibility, and preserve the package's public API, evaluation order and cleanup behavior
when improving readability.
