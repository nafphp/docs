---
title: Your first application
requires:
  - naf/view
---

# Your first application

Start with [Installation](install.md#start-with-the-application-skeleton). The skeleton already
includes `naf/view`, so you do not need to run the package command above again.
The tutorial requires `naf/framework` **0.2.2 or newer** and `naf/form` **0.2.1 or newer**.
Starter 0.2.2 already includes compatible dependencies. For an older application, follow the
[dependency update](install.md#start-with-the-application-skeleton) before continuing.

This tutorial replaces the starter's demonstration routes with an HTML home page and a JSON
endpoint. Each titled code block is the complete contents of that file. Create missing
directories; keep the capital **C** in `app/Controllers` on every operating system.

## Files and bootstrap

Your application will use:

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

If a `.env.local` exists, NAF loads it instead of `.env`. Remove that ambiguity for this
exercise, or put `APP_ENV=dev` there too.

## Register two named routes

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

The `s()` call escapes text for HTML. PHP templates do not escape values automatically.
Functions must be imported in each PHP file that uses them, including templates.

## Run and verify

From `nafphp-demo/`:

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

## Remove the starter demo

Once the home page and `/hello/Ada` work, you can remove the original demonstration.
**Replace its routes and bootstrap first**, as this tutorial does, so they no longer reference
`WebsiteController` or a `QuoteService` binding. Save any changes you want to keep, then run
this from your project root:

```bash
rm app/Controllers/WebsiteController.php app/Service/QuoteService.php \
  app/views/welcome.phtml app/views/contact.phtml app/Jobs/SendMailJob.php
composer dump-autoload
```

The quotes belong to `QuoteService`; remove that file only when your own pages no longer use
it. `SendMailJob` is an unused example, not a mail integration. The empty `app/config.php`
above removes the demo's quote configuration.

If your starter includes a shared contact-form template or interactive demo script, remove
those unused files too:

```bash
rm -f app/views/partials/contact-form.phtml public/js/demo.js
```

Remove the script's `asset()->add()` registration from the shared layout if you keep that
layout for your own pages. The `-f` allows this step to work with older starters that do not
include these files.

This tutorial's `home.phtml` is a complete HTML document. If your application also no longer
uses the shared demo layout, you can remove `app/views/layout.phtml` and `public/css/naf.css`,
then delete the unused starter artwork from `public/images/`. Keep any layouts, styles or
images that your own views still reference.

The starter's `tests/smoke.py` checks its demo routes. Replace it with tests for your own
application, or remove it and the `test` entry in Composer's `scripts` object. Keep
`composer.json`, `composer.lock`, `vendor/`, `bootstrap.php`, `public/index.php` and the
`App\` autoload mapping. The framework and its installed plugins continue to work after
the demonstration is gone.

### Start with a fresh directory

To get a new copy of the starter, stop the development server with Ctrl+C and run this from
the parent directory, choosing a name that does not already exist:

```bash
composer create-project naf/app my-next-app
cd my-next-app
APP_ENV=dev php -S 127.0.0.1:8000 -t public
```

Your old project stays available while you copy over anything you need. After backing it up
and checking the new application, you can delete the old project directory. A fresh starter
includes its demo again; use the steps above to replace it with your own pages. For an HTTP
service that needs no templates or forms, start with the
[core-only project](install.md#core-only-project) instead.

## Continue building

- [Handling a POST request](recipes/post-requests.md) explains body data, validation and CSRF.
- [A contact form](recipes/contact-form.md) adds an HTML form.
- [A login form](recipes/login-form.md) signs in a user.
- [A JSON API](recipes/json-api.md) adds persistent data and JSON error responses.

See [Testing applications](testing.md) to automate verification and [Deployment](deployment.md) for production setup.
