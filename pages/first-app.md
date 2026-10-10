---
title: Your first application
requires:
  - naf/view
---

# Your first application

Build an HTML home page and a JSON endpoint in the NAF starter. By the end, `/` will display
**Hello, World!** and `/hello/Ada` will return a JSON greeting. You will connect a route to a
controller, pass data to a template and check both responses through HTTP.

## Before you begin

Complete [the starter installation](install.md#start-with-the-application-skeleton), then stop
its development server with Ctrl+C. Work from the `nafphp-demo/` project root. The starter
already includes `naf/view`; you can use it without another package installation.

This exercise replaces the starter's demonstration routes. Each titled code block is the
complete contents of that file. Create missing directories and keep the capital **C** in
`app/Controllers` so Composer can find the class on case-sensitive systems. Add all the files
below before starting the server again.

??? info "Continuing with an older starter"

    The tutorial requires `naf/framework` **0.2.2 or newer** and `naf/form` **0.2.1 or newer**.
    Starters 0.2.2 and 0.2.3 already include compatible dependencies. For an older
    application, follow the [dependency update](install.md#starter-versions-and-updates)
    before continuing. The later form recipes update `naf/form` to 0.2.3 themselves.

## Files and bootstrap

First, establish where the application starts and where its files belong:

```text
nafphp-demo/
├── app/
│   ├── Controllers/HomeController.php
│   ├── views/home.phtml
│   ├── config.php
│   └── routes.php
├── public/index.php
├── vendor/
├── .env
├── bootstrap.php
└── composer.json
```

The starter's `composer.json` maps `App\` to `app/`. Composer can therefore load
`App\Controllers\HomeController` from `app/Controllers/HomeController.php`.

```php title="bootstrap.php"
<?php

declare(strict_types=1);

use function Naf\app;

define('BASE_PATH', __DIR__);

require __DIR__ . '/vendor/autoload.php';

// Register application services here, before run() handles the request.
app()->run();
```

```php title="public/index.php"
<?php

declare(strict_types=1);

require dirname(__DIR__) . '/bootstrap.php';
```

```ini title=".env"
APP_ENV=dev
```

```php title="app/config.php"
<?php

declare(strict_types=1);

return [];
```

`public/index.php` loads `bootstrap.php`, which loads Composer and runs NAF. The empty
`app/config.php` replaces the demo configuration; you can add application settings later.
If a `.env.local` exists, NAF loads it instead of `.env`. Put `APP_ENV=dev` there too, or move
that file aside for this exercise so the environment matches the example.

## Register two named routes

With the entry point in place, tell NAF which action should answer each URL. The controller
comes in the next step; registering its class name here does not construct it yet.

```php title="app/routes.php"
<?php

declare(strict_types=1);

use App\Controllers\HomeController;

use function Naf\route;

route()->add('GET', '/', [HomeController::class, 'index'], 'home');
route()->add('GET', '/hello/{name}', [HomeController::class, 'hello'], 'hello');
```

Every route has a unique name. The `{name}` placeholder matches the controller argument `$name`.

## Write the controller

Now add the class referenced by the routes. Its `index()` action returns the home page;
`hello()` returns JSON using the name from the URL.

```php title="app/Controllers/HomeController.php"
<?php

declare(strict_types=1);

namespace App\Controllers;

use Psr\Http\Message\ResponseInterface;

use function Naf\json;
use function Naf\View\render;

final class HomeController
{
    public function index(): ResponseInterface
    {
        return render('home', ['name' => 'World']);
    }

    public function hello(string $name): ResponseInterface
    {
        return json(['hello' => $name]);
    }
}
```

## Render the page

The controller's `render('home', ...)` call needs this template. It receives `$name` from the
controller and uses the named `hello` route for its link to the JSON endpoint.

```html+php title="app/views/home.phtml"
<?php

declare(strict_types=1);

use function Naf\route;
use function Naf\View\s;

?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>My first NAF application</title>
</head>
<body>
    <h1>Hello, <?= s($name) ?>!</h1>
    <a href="<?= s(route('hello', ['name' => 'Ada'])) ?>">Try the JSON endpoint</a>
</body>
</html>
```

The `s()` call escapes text for HTML. Import each helper in the file that uses it, including
templates, and use `s()` where a dynamic value enters HTML. PHP templates do not escape
values automatically.

## Run and verify

The route, controller and template are now connected. From `nafphp-demo/`, refresh Composer's
autoload files and start the server:

```bash
composer dump-autoload
php -S 127.0.0.1:8000 -t public
```

Open **http://127.0.0.1:8000/**: the page says **Hello, World!**.
In another terminal:

```bash
curl -i http://127.0.0.1:8000/hello/Ada
```

Expect HTTP **200**, `Content-Type: application/json; charset=UTF-8` and a body containing
`"hello": "Ada"`. An unknown path, such as `/does-not-exist`, should return **404**.

These commands run the application through HTTP. Executing `php bootstrap.php` alone does
not serve a page: `app()->run()` returns immediately under CLI.

When these checks pass, you have followed a complete request through the application:
the route selects an action, the action creates a response and NAF sends it to the client.

## If the result is different

| What you see | What to check |
|---|---|
| The original welcome page | Check that you replaced `app/routes.php` in the project served by this terminal |
| A class-not-found error | Check `App\Controllers`, the capital `C` in `app/Controllers`, and run `composer dump-autoload` from the project root |
| A missing `home` view | Check that `app/views/home.phtml` exists and that its filename matches `render('home', ...)` |
| `/hello/Ada` returns 404 | Confirm the route uses `GET` and `/hello/{name}`, then restart the server from this project's root with `-t public` |
| The server reports that port 8000 is in use | Stop the earlier development server, or choose a free port and use it in the browser and curl commands |

For another failure, check the terminal running PHP and `logs/app.log` if it exists.
[Troubleshooting](troubleshooting.md#routing-and-bootstrap) explains how to narrow down
routing, autoload and bootstrap problems.

## Continue building

Choose the next feature you need; you can return to the reference chapters as questions arise.

- [A contact form](recipes/contact-form.md) adds validation, CSRF protection and a local mail outbox.
- [A login form](recipes/login-form.md) adds a protected account page and a browser session.
- [A JSON API with a database](recipes/json-api.md) adds persistent data and migrations.
- [Choose a scenario](recipes/index.md) compares these paths with the independent small website and storage-free API tutorials.

Use [Testing applications](testing.md) to automate verification and [Deployment](deployment.md)
when preparing the application for production. The optional cleanup below can wait until
you start adapting the project for your own application.

## Remove the starter demo

The tutorial works with the unused demo files still present. When you are ready to remove
them, use these steps after checking that your own pages no longer depend on them.

??? note "Optional cleanup steps"

    First replace the demo's routes and bootstrap, as this tutorial does, so they no longer
    reference `WebsiteController` or a `QuoteService` binding. Save any changes you want to
    keep, then run this from your project root:

    ```bash
    rm app/Controllers/WebsiteController.php app/Service/QuoteService.php \
      app/views/welcome.phtml app/views/contact.phtml app/Jobs/SendMailJob.php
    composer dump-autoload
    ```

    The quotes belong to `QuoteService`; remove that file only when your own pages no longer
    use it. `SendMailJob` is an unused example. The empty `app/config.php` above removes the
    demo's quote configuration.

    If your starter includes a shared contact-form template or interactive demo script,
    remove those unused files too:

    ```bash
    rm -f app/views/partials/contact-form.phtml public/js/demo.js
    ```

    Remove the script's `asset()->add()` registration from the shared layout if you keep that
    layout for your own pages. The `-f` allows this step to work with older starters that do
    not include these files.

    This tutorial's `home.phtml` is a complete HTML document. If your application also no
    longer uses the shared demo layout, you can remove `app/views/layout.phtml` and
    `public/css/naf.css`, then delete the unused starter artwork from `public/images/`.
    Keep any layouts, styles or images that your own views still reference.

    The starter's `tests/smoke.py` checks its demo routes. Replace it with tests for your own
    application, or remove it and the `test` entry in Composer's `scripts` object. Keep
    `composer.json`, `composer.lock`, `vendor/`, `bootstrap.php`, `public/index.php` and the
    `App\` autoload mapping. The framework and its installed plugins continue to work after
    the demonstration is gone.

### Start with a fresh directory

??? note "Create another starter project"

    To get a new copy of the starter, stop the development server with Ctrl+C and run this
    from the parent directory, choosing a name that does not already exist:

    ```bash
    composer create-project naf/app my-next-app
    cd my-next-app
    APP_ENV=dev php -S 127.0.0.1:8000 -t public
    ```

    Your old project stays available while you copy over anything you need. A fresh starter
    includes its demo again; use the steps above to replace it with your own pages. For an
    HTTP service that needs no templates or forms, start with the
    [core-only project](install.md#core-only-project).
