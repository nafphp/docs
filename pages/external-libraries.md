---
title: External libraries
---

# External libraries { #using-external-libraries }

NAF can use ordinary Composer libraries through configuration and container bindings.
Check whether an existing [NAF package](choosing-packages.md) meets the requirement first.
Register external services in root `bootstrap.php`, before their consumers are constructed.

The examples below are integration fragments. They assume a bootstrapped application and
the library-specific setup described in each section.

## Install a library { #installing-packages }

You can install any Composer package as usual:

```bash
composer require some/vendor-package
```

Composer loads the package according to its declared autoload configuration. Installation
does not configure its services or register a NAF plugin unless it declares `naf-plugin`.

---

## Example: Blade templates { #example-using-blade-templating }

Install Blade via Composer:

```bash
composer require jenssegers/blade
```

These are integration fragments, not a complete application. Create the views, writable cache
directory and library-specific configuration first. Put this registration in `bootstrap.php`
after the autoloader and before `app()->run()`:

```php-inline
use Jenssegers\Blade\Blade;
use function Naf\app;

app()->container()->set('blade', function () {
    return new Blade(BASE_PATH . '/app/views', BASE_PATH . '/storage/cache/views');
});
```

Now you can use Blade inside your controllers:

```php-inline
use function Naf\{app, response};

$blade = app()->container()->get('blade');

return response($blade->render('home', ['name' => 'World']));
```

---

## Example: Eloquent ORM { #example-using-eloquent-orm }

Install Eloquent via Composer:

```bash
composer require illuminate/database
```

Configure the `database` values shown below in `app/config.php` for your database, then register
Eloquent in `bootstrap.php` before `app()->run()`:

```php-inline
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

```php-inline
use App\Models\User; // Your Eloquent model, extending Illuminate\Database\Eloquent\Model.
use function Naf\app;

app()->container()->get('db'); // Resolve the lazy factory before calling a static model finder.
$user = User::find(1);
```

---

## Integration checklist { #tips-for-integration }

- Register services inside your container via `app()->container()->set()`.
- Load config values using `config('key')`.
- Keep external libraries isolated and modular.
- Test the integrated library against the PHP and dependency versions in your application lock.
- Keep template directories, cache permissions and database configuration explicit.
