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

## Render a template { #rendering-one }

```php-inline
use function Naf\View\render;

return render('product.detail', ['product' => $product]);
```

That loads `app/views/product/detail.phtml` — dots become directory separators — and wraps
the result in a response, which is what a controller returns. Template names may contain
only letters, digits, `_`, `-`, `.` and `/`; anything else, an absolute path or `..` throws
`InvalidArgumentException` before a file is read.

### Where templates are found

The first existing file wins, in this order:

1. The application paths from `config('view:paths')`. The default is `views` and
   `app/views`, relative to the project root; absolute paths are used as given.
2. Each installed plugin's view directory, in [plugin boot order](plugins.md#boot-order).
   A plugin uses the first of `src/views`, `views` or `app/views` that exists.
3. The templates shipped inside `naf/view` itself.

An application can therefore override a plugin template by creating a file with the same
relative name. Setting `view:paths` replaces the default application paths; include
`app/views` again if you want to keep it alongside custom directories.

## render() or view()

```php-inline
render('mail.welcome', ['name' => $name]);  // → a PSR-7 ResponseInterface
view('mail.welcome', ['name' => $name]);    // → a string
```

`render()` is for a controller answering a request. `view()` returns the HTML as a string:
a partial inside another template, the body of an email, or a fragment for a JSON payload.
`render()` always creates a 200 response; change it with `->withStatus(422)` and similar
PSR-7 methods.

Sending a `view()` result where a response belongs, or returning a `render()` result into an
email, is the mistake the two names exist to prevent.

### Templates outside HTTP requests

`view()`, `render()` and `s()` rely on the core guard rules `safePath` and `safeOutput`,
which NAF registers only while handling an HTTP request. In a console command, a queue
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
variables it needs explicitly:

```html+php
<?php use function Naf\View\view; ?>
<section class="contact">
    <?= view('partials.contact-form', ['check' => $check, 'token' => $token]) ?>
</section>
```

`app/views/partials/contact-form.phtml` receives only `$check` and `$token`; variables of
the outer template are not shared automatically. The partial escapes its own output, as any
template does. The starter's welcome and contact pages share their form this way.

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

```html+php
<?php $this->setLayout('layouts.main') ?>

<?php $this->block('title') ?>Products<?php $this->endblock('title') ?>

<?php $this->block('content') ?>
    <h1>Everything we sell</h1>
<?php $this->endblock('content') ?>
```

```html+php
<?php use function Naf\View\asset; ?>
<!-- app/views/layouts/main.phtml -->
<!DOCTYPE html>
<html>
<head>
    <title><?= $this->renderBlock('title', 'NAF') ?></title>
    <?= asset()->render('css') ?>
</head>
<body>
    <?= $this->renderBlock('content') ?>
    <?= asset()->render('js') ?>
</body>
</html>
```

`renderBlock()` takes a default for the blocks a view did not fill — a title, a sidebar,
anything optional. Variables passed to the view reach the layout too.

## Assets

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

JavaScript comes in two modes: `classic` renders a plain `<script src>`, `module` renders
`type="module"`. An unrecognised mode falls back to `classic` rather than failing.

!!! warning "Only paths ending in `.css` or `.js` are collected"
    `add()` decides the type from the path's file extension. A path with a query string or
    fragment, such as `/css/app.css?v=2`, and other extensions such as `.mjs` are **ignored
    without an error**. Put a version into the file name (`/css/app.2.css`) instead of a
    query string, or print such tags directly in the layout.

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
| `view:paths` | list of directories | `['views', 'app/views']` | Application template directories, searched before plugin templates; relative to the project root unless absolute |

## If the result is different

| What you see | What to check |
|---|---|
| `View x not found in any known paths.` | The file name and directory: dots in the name become `/`, and the file ends in `.phtml` under a directory from `view:paths` |
| `Insecure path detected!` | The template name contains characters other than letters, digits, `_`, `-`, `.` and `/` |
| `Guard "safePath" not found.` or `Guard "safeOutput" not found.` | The code runs under CLI; see [Templates outside HTTP requests](#templates-outside-http-requests) |
| A variable is undefined in a partial | Partials receive only the variables passed to `view()` |
| A stylesheet or script tag is missing | The path ends in `.css` or `.js` without a query string, and `add()` runs before the layout renders that collection |
| `Block name was not opened.` | Every `endblock('name')` needs a preceding `block('name')` with the same name |
