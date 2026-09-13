---
title: External libraries
---

# Using External Libraries

NAF is designed to be minimal and flexible.  
You are free to integrate any external library you need without fighting against hidden internals.

Thanks to the PSR-4 structure and Composer, adding new tools is simple and clean.

---

## Installing Packages

You can install any Composer package as usual:

```bash
composer require some/vendor-package
```

The package will be autoloaded automatically according to PSR-4 standards.

---

## Example: Using Blade Templating

Install Blade via Composer:

```bash
composer require jenssegers/blade
```

These are integration fragments, not a complete application. Create the views, writable cache
directory and library-specific configuration first. Put this registration in `bootstrap.php`
after the autoloader and before `app()->run()`:

```php
use Jenssegers\Blade\Blade;
use function Naf\app;

app()->container()->set('blade', function () {
    return new Blade(BASE_PATH . '/app/views', BASE_PATH . '/storage/cache/views');
});
```

Now you can use Blade inside your controllers:

```php
use function Naf\{app, response};

$blade = app()->container()->get('blade');

return response($blade->render('home', ['name' => 'World']));
```

---

## Example: Using Eloquent ORM

Install Eloquent via Composer:

```bash
composer require illuminate/database
```

Configure the `database` values shown below in `app/config.php` for your database, then register
Eloquent in `bootstrap.php` before `app()->run()`:

```php
use Illuminate\Database\Capsule\Manager as Capsule;
use function Naf\{app, config};

app()->container()->set('db', function () {
    $capsule = new Capsule;
    $config = config('database');

    $capsule->addConnection([
        'driver'    => $config['driver'],
        'host'      => $config['host'],
        'database'  => $config['database'],
        'username'  => $config['username'],
        'password'  => $config['password'],
        'charset'   => $config['charset'],
        'collation' => 'utf8mb4_unicode_ci',
        'prefix'    => '',
    ]);

    $capsule->setAsGlobal();
    $capsule->bootEloquent();

    return $capsule;
});
```

Use models as usual:

```php
use App\Models\User; // Your Eloquent model, extending Illuminate\Database\Eloquent\Model.
use function Naf\app;

app()->container()->get('db'); // Resolve the lazy factory before calling a static model finder.
$user = User::find(1);
```

---

## Tips for Integration

- Register services inside your container via `app()->container()->set()`.
- Load config values using `config('key')`.
- Keep external libraries isolated and modular.
- You are free to build your own architecture around NAF without restrictions.
