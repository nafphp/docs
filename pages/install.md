---
title: Installation
---

# Installation

Use the starter for a website, or install only the core for a small HTTP service.
The Composer vendor is **`naf`**; `nafphp` is the GitHub organisation.

## Requirements

- PHP 8.3 or newer and Composer.
- PHP's JSON and PDO extensions. Forms also use `mbstring`; database access needs the PDO driver for your database.
- A writable project directory. Sessions and logs need writable storage at runtime.

## Start with the application skeleton

Run this from the directory in which you keep your projects:

```bash
composer create-project naf/app nafphp-demo
cd nafphp-demo
APP_ENV=dev php -S 127.0.0.1:8000 -t public
```

Open **http://127.0.0.1:8000/**. You should see the NAF welcome page. Stop the development
server with Ctrl+C. Keep it bound to localhost; on a deployed site, configure the web server's
document root as this project's `public/` directory.

The starter installs `naf/framework`, `naf/view` and `naf/form`; `naf/session` arrives through
the form package. It also registers the `App\` namespace with Composer.

Starter **0.2.2** ships a working dependency lock: framework 0.2.3, form 0.2.2, session 0.2.1
and view 0.2.1. It also excludes Nyholm PSR-7 below 1.8.2 to avoid PHP 8.4+ deprecation errors.
The welcome page, `/contact` form and POST `/api` demonstration work directly
after installation; no extra Composer update or response listener is needed. The contact
example validates input and redirects; it does not send or store a message.

For an application created from an older starter, update the required minimum versions:

```bash
composer require 'naf/framework:^0.2.2' 'naf/form:^0.2.1' --with-all-dependencies
```

For later compatible updates, run `composer update` and test your application before
deploying it. Commit `composer.lock`; deployments should use `composer install` to reproduce
that tested dependency set.

Continue with [Your first application](first-app.md). It replaces the starter demonstration
with complete files you can copy, then verifies both an HTML page and a JSON endpoint.

## Core-only project

For a service without templates or browser forms, create an empty directory and these files.
This is a separate starting point; do not replace the starter's Composer file with this one.

```bash
mkdir naf-api
cd naf-api
mkdir -p app public
```

```json title="composer.json"
{
    "name": "example/naf-api",
    "require": { "php": ">=8.3", "naf/framework": "^0.2" },
    "autoload": { "psr-4": { "App\\": "app/" } }
}
```

```bash
composer install
```

```php title="bootstrap.php"
<?php

define('BASE_PATH', __DIR__);
require __DIR__ . '/vendor/autoload.php';

use function Naf\app;

app()->run();
```

```php title="public/index.php"
<?php

require dirname(__DIR__) . '/bootstrap.php';
```

```php title="app/routes.php"
<?php

use function Naf\{json, route};

route()->add('GET', '/', fn() => json(['ok' => true]), 'home');
```

```dotenv title=".env"
APP_ENV=dev
```

```bash
php -S 127.0.0.1:8000 -t public
```

In another terminal, `curl http://127.0.0.1:8000/` should return `{"ok": true}`
(with whitespace for readability). This path needs no view, form, session or database plugin.

## Environment and next steps

Use `APP_ENV=dev` locally, `APP_ENV=test` for tests and **`APP_ENV=prod`** in production.
Use these exact values: `production` is not the production constant. Keep `.env` and
`.env.local` out of version control. See [Configuration](configuration.md).

- [Your first application](first-app.md) — a website and a JSON endpoint.
- [Choosing packages](choosing-packages.md) — add only what your application needs.
- [Requests and responses](request-response.md) — read incoming data and return a response.
