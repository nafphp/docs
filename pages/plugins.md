# Plugins

NAF includes a clean and lightweight plugin system that allows you to extend the framework with zero configuration.

Plugins can provide additional configuration, templates (views), and custom logic via a `bootstrap.php` file. Once a plugin is installed via Composer, it is automatically detected and integrated.

---

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
    "fkde/NAF": "dev-main"
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
plugin()->getMeta('viewPaths');
plugin()->getMeta('configPaths');
plugin()->getMeta('bootstraps');
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

class UserListener
{
    public function onUserRegistered($user)
    {
        // Log registration, send welcome email, etc.
        logger()->info('New user registered: ' . $user->email);
    }
}
```
**bootstrap.php:**
``` php
use MyEventPlugin\Listeners\UserListener;
use function Naf\event;

// Register the event listener
$listener = new UserListener();
event()->listen('user.registered', [$listener, 'onUserRegistered']);

// You can also use closure-based listeners
event()->listen('user.login', function($user) {
    logger()->info('User logged in: ' . $user->email);
});
```
Usage in the main application:
``` php
use function Naf\event;

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

route()->add('GET', '/plugin-hello', [HelloController::class, 'index']);
```

Visit: `http://yourapp.local/plugin-hello`

---

## View Resolution Order

1. App `app/views/`
2. Plugins `app/views/`

---

## Config Merge Order

1. App `app/config.php`
2. Plugins `app/config.php`
3. Framework `src/config.php`
