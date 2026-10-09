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
the result in a response, which is what a controller returns.

Views are searched in your application's view directory and in every plugin's, so a plugin
can ship a template and your application can override it by putting a file at the same name.
`config('view:paths')` replaces the default application search paths (`views`, `app/views`).
Include those entries too if you want to keep them alongside custom directories; plugin
view paths are still searched afterwards.

## render() or view()

```php-inline
render('mail.welcome', ['name' => $name]);  // → a PSR-7 ResponseInterface
view('mail.welcome', ['name' => $name]);    // → a string
```

`render()` is for a controller answering a request. `view()` is for everywhere else: the
body of an email, a fragment for a JSON payload, a template rendered in a queue job where
there is no response to return.

Sending a `view()` result where a response belongs, or returning a `render()` result into an
email, is the mistake the two names exist to prevent.

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
registrations of the same asset produce one tag.

JavaScript comes in two modes: `classic` renders a plain `<script src>`, `module` renders
`type="module"`. An unrecognised mode falls back to `classic` rather than failing.

## Template responsibilities { #what-this-is-not }

Templates execute as PHP and are not compiled or automatically escaped. Keep queries and
business rules in services, and pass the resulting data to the view. Treat application and
plugin templates as trusted code.

## Interactive containers

[Flow](flow.md) connects JavaScript classes or object factories to individual HTML containers.
Use it when a view needs reactive fields, shared state or backend fragments without a page
reload. The Flow chapter covers the existing View asset collector and a complete example.
