---
title: Cheat sheet
---

# Cheat sheet

The calls you need most often, one line each. Every snippet is a fragment for an existing,
bootstrapped application: import the functions it uses at the top of your PHP file. Each
section links to the chapter with the complete behaviour.

## Routes and responses

```php-inline
use function Naf\{abort, json, redirect, response, route};

route()->add('GET', '/products/{id}', [ProductController::class, 'show'], 'products.show');
route('products.show', ['id' => 42]);               // '/products/42'

return response('Plain text', 200, ['Content-Type' => 'text/plain; charset=UTF-8']);
return json(['id' => 42], 201);                     // application/json; charset=UTF-8
return redirect(route('products.show', ['id' => 42]));
abort(404, 'Product not found.');                   // throws; renders the error page
```

[Routing](routing.md) · [Requests and responses](request-response.md) · [Errors](errors.md)

## Request input

```php-inline
use function Naf\{param, request};

$name  = param()->get('name', '');                  // query, form body or JSON body
$city  = param()->get('address.city');              // dot path into nested input
$body  = request()->getParsedBody();                // form fields only
$query = request()->getQueryParams();
$token = request()->getHeaderLine('Authorization');
```

Check the type of every value before using it; a field can arrive as an array.
[Requests and responses](request-response.md)

## Views

```html+php
<?php use function Naf\View\{asset, s, view}; ?>
<?php $this->setLayout('layouts.main') ?>
<h1><?= s($title) ?></h1>
<?= view('partials.card', ['item' => $item]) ?>
<?php asset()->add('/css/app.css') ?>
```

```php-inline
use function Naf\View\render;

return render('products.show', ['product' => $product]);   // app/views/products/show.phtml
```

[Views and templates](views.md)

## Forms and CSRF

```php-inline
use function Naf\Form\validator;
use function Naf\View\render;
use function Naf\request;

$check = validator()->validate((array) request()->getParsedBody(), [
    'email' => 'required|string|email',
    'age'   => 'integer',
]);
if (!$check->isValid()) {
    return render('signup', ['check' => $check])->withStatus(422);
}
```

```html+php
<?php use function Naf\Form\{csrf, error, memory}; use function Naf\View\s; ?>
<input type="hidden" name="_csrf" value="<?= s(csrf()->token()) ?>">
<input name="email" value="<?= s(memory('email') ?? '') ?>"> <?= error('email', $check) ?>
```

[Forms and validation](forms.md)

## Sessions

```php-inline
use function Naf\Session\session;

session()->set('cart', [42, 7]);
$cart = session()->get('cart', []);
session()->flash('notice', 'Saved.');
$notice = session()->getFlash('notice');            // read once, then gone
```

[Sessions](sessions.md)

## Database

```php-inline
use function Naf\Database\database;

$statement = database()->prepare('SELECT * FROM products WHERE id = :id');
$statement->execute(['id' => $id]);
$product = $statement->fetch();                     // associative array or false
```

```bash
vendor/bin/naf db:migration:create
vendor/bin/naf db:migrate up
```

[Database and migrations](database.md) · [ORM](orm.md)

## Authentication

```php-inline
use Naf\Auth\Credentials\PasswordCredentials;
use function Naf\Auth\auth;

auth()->authenticate(new PasswordCredentials($username, $password));   // bool
auth()->user();                                     // your user model, or null
auth()->requirePermission('products.edit');         // 401 for guests, 403 without the grant
auth()->logout();
```

[Authentication and permissions](auth.md)

## Background work

```php-inline
use function Naf\Queue\queue;

queue()->push(SendInvoice::class, ['invoice_id' => 42]);
```

```bash
vendor/bin/naf queue:consume
vendor/bin/naf schedule:ticker
```

[Queues and workers](queues.md) · [Scheduled jobs](scheduling.md) · [CLI commands](cli-commands.md)

## Mail and HTTP

```php-inline
use Nyholm\Psr7\Request;
use function Naf\Client\client;
use function Naf\Mail\{mail, mailer};

mailer()->send(mail()->setFrom('shop@example.com')->addTo($email)
    ->setSubject('Your order')->setContent($text, false));

$response = client()->sendRequest(new Request('GET', 'https://api.example.com/status'));
```

[Mail delivery](mail.md) · [HTTP client](http-client.md)

## Configuration, services and logging

```php-inline
use function Naf\{app, config, env, log};

$timeout = config('client:timeout', 20);            // colon path into app/config.php
if (env() === \Naf\Core\Environment::PROD) { /* … */ }
app()->container()->set(PaymentGateway::class, fn() => new StripeGateway(config('stripe:key')));
log()->info('Order {id} placed', ['id' => 42]);
```

[Configuration](configuration.md) · [Configuration keys](configuration-reference.md) ·
[Dependency injection](dependency-injection.md) · [Function index](function-index.md)
