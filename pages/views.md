---
title: Views and templates
requires:
  - naf/view
---

# Views and templates

`naf/view` renders PHP templates, layouts and named blocks. `render()` creates an HTML
response; `view()` returns an HTML string. Templates use `.phtml` files and ordinary PHP.
The package also provides asset collection and explicit HTML escaping.

Start with a bootstrapped [application](first-app.md). Create templates under `app/views/`.
Application templates can override plugin templates at the same relative path.
The complete files below use the starter's bootstrap. Try them in a disposable application:
the first route file replaces its demonstration routes.

## Render a template { #rendering-one }

Replace `app/routes.php` with a route that passes two variables to a template:

```php title="app/routes.php"
<?php

declare(strict_types=1);

use Psr\Http\Message\ResponseInterface;

use function Naf\route;
use function Naf\View\render;

route()->add('GET', '/hello', static fn(): ResponseInterface =>
    render('hello', ['name' => 'Ada & friends', 'pageTitle' => 'Greeting'])
        ->withHeader('Content-Type', 'text/html; charset=UTF-8'), 'hello');
```

### View files

Create `app/views/hello.phtml`. A `.phtml` file is ordinary PHP mixed with HTML:

```html+php title="app/views/hello.phtml"
<?php use function Naf\View\s; ?>
<h1><?= s($pageTitle) ?></h1>
<p>Hello, <?= s($name) ?>!</p>
```

Run `php -S 127.0.0.1:8000 -t public` from the project root and open
`http://127.0.0.1:8000/hello`. You should see **Greeting** and **Hello, Ada & friends!**.
The HTML source contains `Ada &amp; friends`, because the template escapes the value.

`render('hello', ...)` loads `app/views/hello.phtml` and wraps its HTML in a response.
For nested directories, dots become separators: `render('product.detail', ...)` looks for
`app/views/product/detail.phtml`. Template names may contain
only letters, digits, `_`, `-`, `.` and `/`; anything else, an absolute path or `..` throws
`InvalidArgumentException` before a file is read.

### Where templates are found

The first existing file wins, in this order:

1. The application paths from `config('view:paths')`. Since View 0.2.3, the defaults are
   `views`, `app/views` and `src/views`, in that order, relative to the project root;
   absolute paths are used as given.
2. Each installed plugin's view directory, in [plugin boot order](plugins.md#boot-order).
   A plugin uses the first of `src/views`, `views` or `app/views` that exists.
3. The templates shipped inside `naf/view` itself.

An application can therefore override a plugin template by creating a file with the same
relative name. [Configure view locations](#configurable-view-locations) to change the
application's search order. Configuration arrays merge by numeric position, so a shorter
list does not necessarily remove the remaining default paths.

## Variables in views

Keys in the second argument to `render()` or `view()` become variables inside that template.
In the example, `'name' => 'Ada & friends'` becomes `$name`, and `'pageTitle' => 'Greeting'`
becomes `$pageTitle`. Arrays and objects stay arrays and objects; a product passed as
`['product' => $product]` is read as `$product['name']` or `$product->name`, according to
the value the application supplied.

Load and validate the data in a controller or service before rendering. The template
receives only the values passed to it; it does not automatically inherit controller locals.
Use simple variable names and keep data keys distinct from block names such as `title` and
`content`, because blocks are stored in the same variable collection.

## render() or view()

```php-inline
use function Naf\View\{render, view};

render('mail.welcome', ['name' => $name]);  // → a PSR-7 ResponseInterface
view('mail.welcome', ['name' => $name]);    // → a string
```

`render()` is for a controller answering a request. `view()` returns the HTML as a string:
a partial inside another template, the body of an email, or a fragment for a JSON payload.
`render()` creates a 200 response with the rendered body. It does not add a `Content-Type`
header itself; the route above states HTML explicitly. Change the returned response with
`->withStatus(422)`, `->withHeader(...)` and other immutable PSR-7 methods.

For a JSON response containing a rendered fragment, add this route to your existing
`app/routes.php` after creating the [partial](#partials) below:

```php-inline
use function Naf\json;
use function Naf\View\view;

route()->add('GET', '/hello-fragment', static fn(): ResponseInterface =>
    json(['html' => view('partials.greeting', ['name' => 'Ada & friends'])]), 'hello.fragment');
```

`GET /hello-fragment` returns a JSON object whose `html` value contains the greeting
paragraph. Return `json(...)` from the handler; the inner `view(...)` supplies its string.

### Templates outside HTTP requests

Framework **0.2.9+** registers the core guard rules for every SAPI. After application boot,
`view()`, `render()` and `s()` work in commands, queue workers and the scheduler. A job can
use `view()` to build an email body with the same templates and escaping as an HTTP handler.

To try string rendering from the command line, create `bin/render-greeting.php` after
creating the partial below. Reuse the application's bootstrap so its plugins and guards
are available:

```php title="bin/render-greeting.php"
<?php

declare(strict_types=1);

use function Naf\View\view;

require dirname(__DIR__) . '/bootstrap.php';

$html = view('partials.greeting', ['name' => 'Ada & friends']);
echo $html;
```

Run `php bin/render-greeting.php`. It prints `<p class="greeting">Hello, Ada &amp; friends!</p>`
without creating or emitting an HTTP response. An email transport or another string consumer
can use the same `$html` value.

??? note "Framework 0.2.8 and older"

    `view()`, `render()` and `s()` rely on the core guard rules `safePath` and `safeOutput`,
    which these releases register only while handling an HTTP request. In a console command, a queue
    worker or the scheduler they throw `RuntimeException: Guard "safePath" not found.` or
    `Guard "safeOutput" not found.` (`naf/queue` registers `safePath`, so with Queue installed
    the `safeOutput` error appears first).

    To render a template in CLI code, for example an email body in a queued job, register the
    two rules in root `bootstrap.php` before `app()->run()`:

    ```php-inline
    use function Naf\guard;

    if (!guard()->has('safePath')) {
        guard()->register('safePath', static function (string $path): string {
            if ($path === '' || str_contains($path, '..') || str_starts_with($path, '/')
                || !preg_match('/^[A-Za-z0-9_\/.-]+$/', $path)) {
                throw new \InvalidArgumentException('Insecure template path.');
            }
            return $path;
        });
    }
    if (!guard()->has('safeOutput')) {
        guard()->register('safeOutput', static fn($value) => is_array($value)
            ? array_map(static fn($item) => htmlspecialchars((string) ($item ?? ''), ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'), $value)
            : htmlspecialchars((string) ($value ?? ''), ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'));
    }
    ```

    For HTTP requests the core rules already exist when `bootstrap.php` runs, so the `has()`
    checks keep them and web responses retain the core behaviour.

## Partials

A partial is an ordinary template rendered into another one with `view()`. Pass the
variables it needs explicitly. Create `app/views/partials/greeting.phtml`:

```html+php title="app/views/partials/greeting.phtml"
<?php use function Naf\View\s; ?>
<p class="greeting">Hello, <?= s($name) ?>!</p>
```

Inside another template, use:

```html+php
<?php use function Naf\View\view; ?>
<?= view('partials.greeting', ['name' => $name]) ?>
```

The partial receives `$name` because it was passed explicitly. Other variables of the
outer template are not shared automatically. The partial escapes its own data, so print
its rendered markup directly; wrapping the whole `view()` result in `s()` would display
the `<p>` tags as text. The starter's welcome and contact pages share a form partial in
the same way.

## Escaping

```html+php
<?php use function Naf\View\s; ?>

<h1><?= s($title) ?></h1>
```

`s()` escapes strings or flat arrays of strings for HTML text and quoted attributes. It is
not a JavaScript, CSS or URL sanitizer; use encoding appropriate to those contexts.

Templates do not escape values automatically. Use `s()` when inserting untrusted text or
attribute values. `<?= $title ?>` emits the value directly.

## Layouts and blocks

A view names its layout and fills the blocks the layout leaves open.
Replace `app/views/hello.phtml` with this complete version, reusing the greeting partial:

```html+php title="app/views/hello.phtml"
<?php
use function Naf\View\{s, view};
?>
<?php $this->setLayout('layouts.main') ?>

<?php $this->block('title') ?><?= s($pageTitle) ?><?php $this->endblock('title') ?>

<?php $this->block('content') ?>
    <h1><?= s($pageTitle) ?></h1>
    <?= view('partials.greeting', ['name' => $name]) ?>
<?php $this->endblock('content') ?>
```

Create the shared wrapper at `app/views/layouts/main.phtml`:

```html+php title="app/views/layouts/main.phtml"
<?php use function Naf\View\{asset, s}; ?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title><?= $this->renderBlock('title', 'NAF') ?></title>
    <?= asset()->render('css') ?>
</head>
<body>
    <?= $this->renderBlock('content') ?>
    <footer>Page: <?= s($pageTitle) ?></footer>
    <?= asset()->render('js') ?>
</body>
</html>
```

`renderBlock()` takes a default for the blocks a view did not fill — a title, a sidebar,
anything optional. Variables passed to the view reach the layout too.

The same `/hello` URL now has a document title, a shared wrapper and a footer as well as
the greeting. A second page can choose `layouts.main` and fill its own blocks without
duplicating that wrapper. `$this` is the `Naf\View\Core\View` instance executing the template;
its block and layout methods are available in both page templates and layouts.

`block('content')` starts output buffering; `endblock('content')` stores that output under
the same name. `renderBlock('content')` inserts it into the layout. It returns already
rendered markup, so escape values while writing the block, rather than escaping the whole
block in the layout.

When a layout is selected, only its output is returned. Put page content inside a named
block: text outside the blocks is not automatically inserted, and there is no implicit
`$content` variable containing the whole page. If a page does not define `title`, the
layout above uses `NAF` as its title.

## Assets

Add these registrations near the start of a page template, before its layout renders.
The paths illustrate files that your application supplies under `public/css/` and
`public/js/`; collecting an asset does not create the file or serve it:

```html+php
<?php use function Naf\View\asset; ?>

<?php asset()->add('/css/app.css') ?>
<?php asset()->add('/js/app.js') ?>
<?php asset()->add('/js/editor.js', 'module') ?>
```

Collect them anywhere — a view, a partial, a controller — and print them once in the layout:

```html+php
<?= asset()->render('css') ?>
<?= asset()->render('js') ?>
```

Register assets before the layout renders the corresponding collection. Duplicate
registrations of the same asset produce one tag. Paths are HTML-escaped when rendered.

The registrations above produce these tags at the layout's CSS and JavaScript positions:

```html
<link rel="stylesheet" href="/css/app.css">
<script src="/js/app.js"></script>
<script type="module" src="/js/editor.js"></script>
```

`asset()` returns the shared collector. `add()` registers a URL and returns no value;
`render('css')` and `render('js')` return the tags as strings. It does not bundle, minify
or copy files. A URL such as `/css/app.css` is served from `public/css/app.css` when the
web server's document root is `public/`.

JavaScript comes in two modes: `classic` renders a plain `<script src>`, `module` renders
`type="module"`. An unrecognised mode falls back to `classic`.

Since View 0.2.3, `add()` reads the extension from the URL path, preserving query strings
and fragments in the rendered tag. `.mjs` files always render as modules:

```php-inline
asset()->add('/css/app.css?v=2');
asset()->add('/js/editor.mjs#main');
```

An unknown extension is not collected and produces a warning in the application log.

??? note "View 0.2.2 and older"
    These releases ignore query-string URLs and `.mjs` files without a warning. Use a
    versioned filename such as `/css/app.2.css`, or update View. Their default application
    paths are `views` and `app/views`; add `src/views` explicitly if needed.

## Template responsibilities { #what-this-is-not }

Templates execute as PHP and are not compiled or automatically escaped. Keep queries and
business rules in services, and pass the resulting data to the view. Treat application and
plugin templates as trusted code.

## Interactive containers

[Flow](flow.md) connects JavaScript classes or object factories to individual HTML containers.
Use it when a view needs reactive fields, shared state or backend fragments without a page
reload. The Flow chapter covers the existing View asset collector and a complete example.

## Configuration

| Key | Type | Default | Effect |
|---|---|---|---|
| `view:paths` | directory string or list of directories | `['views', 'app/views', 'src/views']` | Application template directories, searched before plugin templates; relative to the project root unless absolute |

### Configurable view locations

For a custom directory searched before the conventional locations, replace the example's
empty `app/config.php` with:

```php title="app/config.php"
<?php

declare(strict_types=1);

return [
    'view' => [
        'paths' => ['templates', 'app/views', 'src/views', 'views'],
    ],
];
```

`templates/hello.phtml` now takes precedence over `app/views/hello.phtml`. Relative paths
use the application root, not the current working directory; absolute directories are
used as given. This changes template lookup, not the public web root.

NAF merges configuration with `array_replace_recursive()`. Lists replace entries at the
same numeric positions. For example, `['templates']` replaces only the first default
entry and leaves `app/views` and `src/views` in place. Specify the full intended order as
above. To search only `templates/`, use a string instead of a list:

```php-inline
return ['view' => ['paths' => 'templates']];
```

Plugin and View's own fallback templates are still searched after these application paths.
See [Configuration](configuration.md#merge-order) for the general merge rules.

## Helper comparison

Import these functions from `Naf\View`; the [function index](function-index.md) contains
their published signatures:

| Helper | Returns | Use |
|---|---|---|
| `render($template, $vars = [])` | `ResponseInterface` | A controller response with a rendered body |
| `view($template, $vars = [])` | `string` | A partial, an email body or a fragment inside another response |
| `s($value)` | Escaped string or array of strings | HTML text and quoted attributes |
| `asset()` | `Naf\View\Core\Asset` | Collect asset URLs; its `render()` method returns tags |

## How it works

`view()` creates a new `View` for each render, resolves the template file and exposes the
passed variables to it. PHP executes the file with output buffering. With no layout, that
buffer becomes the returned string. With a layout, the layout receives the variables and
captured blocks, renders in turn and supplies the returned string. `render()` wraps that
string in a response.

A partial rendered by `view()` has its own `View` and variable collection. The asset
collector is instead shared through the application's container, so a partial can register
assets for the outer layout. Register them before the corresponding `asset()->render()`
call; a stylesheet collected after the layout's CSS output cannot change tags already rendered.

## If the result is different

| What you see | What to check |
|---|---|
| `View x not found in any known paths.` | The file name and directory: dots in the name become `/`, and the file ends in `.phtml` under a directory from `view:paths` |
| `Insecure path detected!` | The template name contains characters other than letters, digits, `_`, `-`, `.` and `/` |
| `Guard "safePath" not found.` or `Guard "safeOutput" not found.` | Check the installed framework version; CLI needs Framework 0.2.9+ or the [older-version workaround](#templates-outside-http-requests) |
| A variable is undefined in a partial | Partials receive only the variables passed to `view()` |
| Page content disappears after adding a layout | Put it between matching `block('content')` and `endblock('content')` calls, and render that block in the layout |
| A stylesheet or script tag is missing | Check for an unknown-extension warning in the log and register assets before the layout renders them; query strings and `.mjs` need View 0.2.3+ |
| `Block name was not opened.` | Every `endblock('name')` needs a preceding `block('name')` with the same name |

Continue with [Controllers](controllers.md), [the small website tutorial](recipes/small-website.md)
and [Flow browser components](flow.md) for full applications using these pieces.
