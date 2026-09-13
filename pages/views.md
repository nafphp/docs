---
title: Views und Templates
requires:
  - naf/view
---

NAF comes with a lightweight native view system.  
It provides simple template inheritance, layout usage, and reusable content blocks — without needing a heavy engine like Blade or Twig.

## Rendering a View

You can render a view file using the `render()` helper function:

```php
use function Naf\render;

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
<?php use function Naf\s; ?>

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
<?php use function Naf\s; ?>

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
<?php use function Naf\s; ?>

<h2>Welcome, <?= s($user['name']) ?>!</h2>
```

---

## Rendering Views without a Response

Sometimes you only need the raw HTML output of a view without wrapping it in a full Response object.  
For this, you can use the `view()` helper:

```php
use function Naf\view;

$html = view('hello', ['name' => 'World']);
```

- `view()` returns the **rendered HTML** as a plain string.
- It does not create a Response object.
- Useful for building custom responses or templates manually.

---

## Summary

- Views are located in `app/views/`.
- Use dot notation when referencing views (e.g., `layouts.main`).
- Use `setLayout()` to attach layouts inside views.
- Use `s()` to escape variables.
- Use `render()` for full responses and `view()` for raw HTML output.