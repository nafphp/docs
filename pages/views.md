---
title: Views and templates
requires:
  - naf/view
---

# Views and templates

PHP templates with layouts and blocks. There is no template language: a view is a
`.phtml` file, `<?= ?>` is the syntax, and your editor already understands it.

What you get beyond a plain `include` is inheritance — a layout with named blocks a view
fills in — plus asset collection and an escaping helper. What you do not get is a compiler,
a cache directory, or a syntax to learn.

## Rendering one

```php
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

```php
render('mail.welcome', ['name' => $name]);  // → a PSR-7 ResponseInterface
view('mail.welcome', ['name' => $name]);    // → a string
```

`render()` is for a controller answering a request. `view()` is for everywhere else: the
body of an email, a fragment for a JSON payload, a template rendered in a queue job where
there is no response to return.

Sending a `view()` result where a response belongs, or returning a `render()` result into an
email, is the mistake the two names exist to prevent.

## Escaping

```php
<?php use function Naf\View\s; ?>

<h1><?= s($title) ?></h1>
```

`s()` escapes for HTML. It takes an array as well as a string and escapes every value, which
saves a loop when you are dumping a row into a table.

Nothing escapes automatically — this is PHP, not a template language, and `<?= $title ?>`
puts exactly what is in `$title` on the page. Wrap anything that came from outside.

## Layouts and blocks

A view names its layout and fills the blocks the layout leaves open.

```php
<?php $this->setLayout('layouts.main') ?>

<?php $this->block('title') ?>Products<?php $this->endblock('title') ?>

<?php $this->block('content') ?>
    <h1>Everything we sell</h1>
<?php $this->endblock('content') ?>
```

```php
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

```php
<?php use function Naf\View\asset; ?>

<?php asset()->add('/css/app.css') ?>
<?php asset()->add('/js/app.js') ?>
<?php asset()->add('/js/editor.js', 'module') ?>
```

Collect them anywhere — a view, a partial, a controller — and print them once in the layout:

```php
<?= asset()->render('css') ?>
<?= asset()->render('js') ?>
```

The point is that a partial can require its own stylesheet without knowing whether the
layout has already been sent. Duplicates are removed, so two partials asking for the same
file produce one tag.

JavaScript comes in two modes: `classic` renders a plain `<script src>`, `module` renders
`type="module"`. An unrecognised mode falls back to `classic` rather than failing.

## What this is not

There is no compiler, no cache directory to clear and no syntax to learn — a view is a PHP
file, and a PHP error in a template is a PHP error with the right line number.

The price is that nothing is escaped for you and nothing stops a template from doing more
than it should. A `.phtml` file can open a database connection. It should not, and the only
thing preventing it is you.
