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

## Rendering a View

You can render a view file using the `render()` helper function:

```php
use function Naf\View\render;

return render('hello', ['name' => 'World']);
```

- The first argument is the view name (relative to the `app/views/` folder, using dot notation).
- The second argument is an optional array of variables to pass into the view.
- `render()` automatically wraps the view in a proper Response object.

This will load `app/views/hello.phtml`.

---

## View Files

View files are simple PHP templates with `.phtml` extension.

Example: `app/views/hello.phtml`

```php
<?php use function Naf\View\s; ?>

<h1>Hello, <?= s($name) ?>!</h1>
```

- Use the `s()` helper to safely escape variables for HTML output.

---

## Layouts

You can create a layout and attach it to your view using `setLayout()`.

Example: `app/views/layouts/main.phtml`

```php
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title><?= $this->renderBlock('title', 'NAF App') ?></title>
</head>
<body>
    <?= $this->renderBlock('content') ?>
</body>
</html>
```

In your view:

```php
<?php use function Naf\View\s; ?>

<?php $this->setLayout('layouts.main') ?>

<?php $this->block('title') ?>
Hello Page
<?php $this->endblock('title') ?>

<?php $this->block('content') ?>
<h1>Hello, <?= s($name) ?>!</h1>
<?php $this->endblock('content') ?>
```

- `setLayout('layouts.main')` specifies the layout file (dot notation).
- `block('name')` and `endblock('name')` define a section.
- `renderBlock('name')` renders the defined blocks into the layout.

---

## Variables in Views

All variables passed to `render()` are automatically extracted into the view.

Example:

```php
return render('profile', ['user' => $user]);
```

In `app/views/profile.phtml`:

```php
<?php use function Naf\View\s; ?>

<h2>Welcome, <?= s($user['name']) ?>!</h2>
```

---

## Rendering Views without a Response

Sometimes you only need the raw HTML output of a view without wrapping it in a full Response object.  
For this, you can use the `view()` helper:

```php
use function Naf\View\view;

$html = view('hello', ['name' => 'World']);
```

- `view()` returns the **rendered HTML** as a plain string.
- It does not create a Response object.
- Useful for building custom responses or templates manually.

---

## Asset Management (CSS & JS)

The plugin includes a small, flexible asset collector used inside layouts to include CSS and JavaScript files.

Assets are added inside views or controllers using the `asset()` helper:

```php
asset()->add('/assets/style.css');            // CSS
asset()->add('/assets/app.js');               // JavaScript (classic)
asset()->add('/assets/main.js', 'module');    // JavaScript ES module
```

### Output in layout files

Use `asset()->render('css')` or `asset()->render('js')` inside your layout:

```php
<!doctype html>
<html>
<head>
    <?= asset()->render('css') ?>
</head>
<body>
    <?= $this->renderBlock('content') ?>
    <?= asset()->render('js') ?>
</body>
</html>
```

### What gets generated?

**CSS:**

```html
<link rel="stylesheet" href="/assets/style.css">
```

**Classic JS:**

```html
<script src="/assets/app.js"></script>
```

**Module JS:**

```html
<script type="module" src="/assets/main.js"></script>
```

### Internals

**All paths are automatically HTML-escaped via `s()`.**

---

---

## Helper Comparison

| Helper     | Returns             | Use case                                |
| ---------- | ------------------- | --------------------------------------- |
| `render()` | `ResponseInterface` | Ideal for controller return values   |
| `view()`   | `string`            | For manual output or further processing |
| `asset()` | `string`            | Include CSS & JS files in layouts       |
| `s()`      | `string`            | Escape output                           |

---

---

## How it works

* `view()` resolves and loads `.phtml` templates from the directories listed in `view:paths` (defaults to `views/` first with `app/views/` as a fallback) before checking any registered plugin or framework views.
* `setLayout()` nests the rendered content into a wrapper view.
* Blocks are buffered and stored internally until rendered.

### Configurable view locations

Set the `view:paths` configuration to control where templates are resolved inside your application. This plugin ships with `src/config.php`, which defaults to:

```php
return [
    'view' => [
        'paths' => [
            'views',
            'app/views',
        ],
    ],
];
```

The entries are resolved relative to `BASE_PATH` when they are not absolute paths, so you can place templates anywhere and order them however you need. The plugin checks each directory in order before falling back to registered plugin or framework view paths.
