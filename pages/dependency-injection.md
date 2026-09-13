---
title: Dependency Injection
---

# Dependency Injection

NAF uses a PSR-11 container wrapped in `AutoResolvingContainer` by default. Registration,
retrieval and construction are distinct operations.

## Register and retrieve services

```php
use function Naf\app;

$container = app()->container();
$container->set('clock', fn() => new \DateTimeImmutable());
$clock = $container->get('clock');
```

A closure runs lazily on the first `get()`. Its result is cached; later calls return the same
instance. The closure may accept the container as its first argument. You can also register
an already constructed object.

Use class or interface names as keys for constructor injection:

```php
use App\Mail\SmtpMailer;
use App\Mail\MailerInterface;
use function Naf\app;

// These are application-owned example classes.
app()->container()->set(MailerInterface::class, fn() => new SmtpMailer());
```

## get() versus make()

| Call | Behaviour |
|---|---|
| `get($id)` | Retrieve a registered service. Missing registrations throw `ServiceNotFoundException`. |
| `make($class, $parameters = [], $singleton = false)` | Construct a concrete class and resolve constructor dependencies. |
| `has($id)` | Check registrations and cached instances. It does not mean any constructible class is registered. |
| `set($id, $factoryOrObject)` | Register or replace a service, clearing its old cached instance. |

```php
use function Naf\app;

final class GreetingService
{
    public function __construct(private string $prefix = 'Hello') {}
    public function greet(string $name): string { return $this->prefix . ', ' . $name; }
}

$service = app()->container()->make(GreetingService::class, ['prefix' => 'Welcome']);
echo $service->greet('Ada');
```

`make()` first uses registered dependencies, then recursively constructs suitable concrete
classes. Scalar parameters need explicit values or defaults. Interfaces need bindings.
By default each `make()` creates a new object; `singleton: true` caches it.

`make()` is NAF's extension, not part of PSR-11. A custom container may only support the
standard interface. NAF's dispatcher uses `make()` for controllers with the default container.

## Where registration belongs

Register application services in `bootstrap.php`, after requiring Composer's autoloader and
before `app()->run()`. The first `app()` call boots the framework and plugins. Do not resolve
an application service from a route file before its bootstrap registration exists.

Use constructor injection for required dependencies. String keys remain useful for explicitly
looked-up services, but do not automatically bind an interface or class of another name.
