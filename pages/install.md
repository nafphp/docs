# Installation

NAF is designed as a lightweight framework package.  
You install it into your own project using Composer.

---

## Install via Composer

```bash
composer require naf/framework
```

This will:

- Download the NAF core (framework logic inside `/src`)
- Make it available via Composer autoloading
- Allow you to use NAF components in your own project structure

---

## Set up your project structure

NAF leaves the project organization completely up to you.  
A typical structure could look like this:

```
/app
    /Controllers
    /Models
    /Views
    config.php
    routes.php
/public
    index.php
bootstrap.php
composer.json
```

But you are free to organize it however you like.

---

## First Steps

You typically:

- Create a `bootstrap.php` to initialize NAF
- Set up your `routes.php`
- Create a `public/index.php` as your web entry point

Example:

```php
// /bootstrap.php

define('BASE_PATH', __DIR__);

require __DIR__ . '/../vendor/autoload.php';

use function Naf\app;

app()->run(); // Start the application
```

---

## Requirements

- PHP 8.3 or higher
- Composer