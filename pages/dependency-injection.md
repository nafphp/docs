---
title: Dependency Injection
---

# Dependency Injection

NAF supports constructor autowiring out of the box. The default container is
`AutoResolvingContainer`, wrapping the PSR-11 `Container`. It can build concrete classes
and recursively resolve their constructor dependencies without registering each class.

## Autowiring without registration

```php
use function Naf\app;

final class Clock
{
    public function now(): \DateTimeImmutable { return new \DateTimeImmutable(); }
}

final class ReportService
{
    public function __construct(public readonly Clock $clock) {}
}

$reports = app()->container()->make(ReportService::class);
// Both ReportService and its Clock dependency are constructed without set().
```

NAF calls `make()` automatically for [controller classes](controllers.md) and
[class-based event listeners](events.md). With `naf/cli`, application
[commands](console.md) are also built this way. Declare required services in their
constructors; concrete dependencies whose own constructors can be resolved need no
registration.

Autowiring applies to constructors. Controller action arguments and route closure arguments
come from route parameters; event handler arguments come from the event payload.

## Register and retrieve services

```php
use function Naf\app;

$container = app()->container();
$container->set('clock', fn() => new \DateTimeImmutable());
$clock = $container->get('clock');
```

A closure runs lazily on the first `get()`. Its result is cached; later calls return the same
instance. You can also register an already constructed object. Register services when you
need an interface binding, custom construction or a shared instance.

Use class or interface names as keys for constructor injection:

```php
use App\Mail\SmtpMailer;
use App\Mail\MailerInterface;
use function Naf\app;

// These are application-owned example classes.
$container = app()->container();
$container->set(MailerInterface::class, fn() => $container->make(SmtpMailer::class));
```

A constructor parameter typed as `MailerInterface` now receives the registered `SmtpMailer`.
Its own constructor dependencies are autowired by `make()`.

A factory closure may accept the wrapped base container as its first argument. That is
`Naf\Core\Container` in the default setup, which has no `make()` method. Capture the outer
container as above when a factory needs autowiring.

## get() versus make()

| Call | Behaviour |
|---|---|
| `get($id)` | Retrieve a registered or singleton-cached service. No autowiring fallback; missing services throw `ServiceNotFoundException`. |
| `make($class, $parameters = [], $singleton = false)` | Construct a concrete class and resolve constructor dependencies. |
| `has($id)` | Check registrations and cached instances. It does not mean any constructible class is registered. |
| `set($id, $factoryOrObject)` | Register or replace a service, clearing its old cached instance. |
| `reset($id)` | Remove a registration and its cached instance. |

Calling `make(ReportService::class)` does not register the resulting object. A subsequent
`get(ReportService::class)` still throws unless the service was registered or built with
`singleton: true`.

## Constructor parameters

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

Explicit values can be passed by parameter name, as above, or by zero-based position.
Named values take precedence over positional values. They apply to the class being built,
not recursively to its dependencies.

For each remaining parameter with a single class or interface type, the container:

1. Retrieves a registered or cached service under that exact type name.
2. Uses `null` if no service exists and the type is nullable, even for a concrete class.
3. Otherwise recursively builds an instantiable concrete class.
4. Throws `ServiceNotFoundException` if the required type cannot be resolved. Required
   interfaces and abstract classes need a binding or an explicitly supplied object.

Scalar and other built-in types use an explicit value, their default or `null` when allowed.
Registering a key such as `'prefix'` does not inject a `$prefix` constructor parameter.
Configure such values through `make()` parameters or a factory. Union and intersection
types are not autowired; supply an explicit value when no default or nullable fallback exists.
Circular constructor dependencies throw `ContainerException`.

## Instance lifetime

By default each `make()` creates a new object, including unregistered concrete dependencies.
Registered dependencies are shared through `get()`.

`make(ReportService::class, singleton: true)` caches and registers the result, making it
available to `get()` and future constructor injection. Later calls with `singleton: true`
reuse the cached instance; dependencies built along the way are not separately registered.
`make()` without that flag still constructs a new object, even if that class is registered.

`make()`, `set()` and `reset()` extend PSR-11. If you supply a custom container, NAF's
bootstrap still needs `set()`. With a container that is not an `AutoResolvingContainer`, the core
dispatcher and event manager instantiate controller and listener classes without arguments.

## Where registration belongs

Put any application service registrations in `bootstrap.php`, after requiring Composer's
autoloader and before `app()->run()`. The first `app()` call boots the framework and plugins.
Do not resolve an application service from a route file before its bootstrap registration exists.

Use constructor injection for required dependencies. String keys remain useful for explicitly
looked-up services, but do not automatically bind an interface or class of another name.
