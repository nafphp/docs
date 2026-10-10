---
title: Sending mail
requires:
  - naf/mail
---

# Sending mail

`naf/mail` builds messages and delivers them through a transport. The default transport uses
PHP's `mail()` and requires a configured delivery system. In local development, first select
the shipped [capture transport](#testing-without-a-mail-server) or the
[contact form outbox](recipes/contact-form.md#a-local-mail-outbox).

Use a [queue](queues.md) when delivery should occur after the HTTP response. A successful
transport call does not prove that a recipient received the message.

## Sending a message

`mail()` hands you an empty message, `mailer()` sends it. Both are imported from
`Naf\Mail`.

```php-inline
use function Naf\Mail\{mail, mailer};

$message = mail()
    ->setFrom('hello@example.com')
    ->addTo('john@example.com')
    ->setSubject('Hello from NAF')
    ->setContent('<b>Welcome!</b>');

mailer()->send($message);
```

Every setter returns the message, so the calls chain in any order you like.

## Recipients

```php-inline
mail()
    ->addTo('john@example.com')
    ->addTo('jane@example.com')     // call it again for a second recipient
    ->addCc('archive@example.com')
    ->addBcc('audit@example.com')
    ->setFrom('hello@example.com')
    ->setReplyTo('support@example.com');
```

`addTo`, `addCc` and `addBcc` append; `setFrom` and `setReplyTo` replace. There is no
method to remove a recipient — build the message with the ones you want.

## HTML or plain text

`setContent()` treats its argument as HTML unless you say otherwise:

```php-inline
->setContent('<b>Welcome!</b>')          // HTML
->setContent('Welcome!', false)          // plain text
```

There is no multipart alternative: a message is one or the other. If your recipients need
both, that is a transport concern, not this object's.

## Attachments

```php-inline
->addAttachment('report.pdf', '/path/to/report.pdf');
```

The first argument is the filename the recipient sees, the second the file on disk. A third
argument marks the attachment as inline, which is how you reference an image from the HTML
body:

```php-inline
mail()
    ->addAttachment('logo.png', '/path/to/logo.png', true)
    ->setContent('<img src="cid:logo.png">');
```

The `cid:` reference uses the name you gave, not the path.

## Delivery failures { #when-it-does-not-go-out }

`send()` is typed to return `bool`, but the shipped transport never returns `false` — it
throws `Naf\Mail\Exceptions\MailException` when PHP's `mail()` refuses the message.

```php-inline
use Naf\Mail\Exceptions\MailException;
use function Naf\Mail\mailer;

try {
    mailer()->send($message);
} catch (MailException $e) {
    // log it, queue a retry, tell somebody
}
```

Checking the return value instead will not catch a failure. A transport of your own may
return `false`, so if you write one, decide which of the two you mean and be consistent.

## Configuration

| Key | Type | Default | Effect |
|---|---|---|---|
| `mail:transport` | class name | `Naf\Mail\Core\Transport\MailTransport` | Transport used by the shared `mailer()`; the class must implement `TransportInterface` |

The mailer takes the transport from the container when that class is registered there, and
otherwise builds it with `make()`, so the transport's constructor dependencies are autowired.
`mail:transport` and the shipped `DummyTransport` require `naf/mail` **0.2.2** or newer.

## Testing without a mail server

`naf/mail` ships `Naf\Mail\Core\Transport\DummyTransport`. It records a copy of every
message in memory, returns `true` and never connects to a mail server. Start from
[Your first application](first-app.md), install the package and create the directory for
the demo script:

```bash
composer require naf/mail
mkdir -p bin
```

### Select the transport

Select the transport in `app/config.php`. This is the complete file for the exercise; in an
existing application, merge the `mail` key into your configuration:

```php title="app/config.php"
<?php

declare(strict_types=1);

use Naf\Mail\Core\Transport\DummyTransport;

return [
    'mail' => ['transport' => DummyTransport::class],
];
```

!!! warning "This setting captures every message"
    With `DummyTransport` selected, nothing is delivered, in any environment. Choose the
    transport per environment, for example:

    ```php-inline
    use Naf\Mail\Core\Transport\{DummyTransport, MailTransport};

    'mail' => [
        'transport' => getenv('APP_ENV') === 'prod' ? MailTransport::class : DummyTransport::class,
    ],
    ```

### Read the captured messages

To inspect the messages, the code that sends and the code that checks must use the same
`DummyTransport` instance. Register one shared instance in the container; the mailer then
takes it from there. In root `bootstrap.php`, after requiring `vendor/autoload.php` and
before `app()->run()`, add:

```php-inline
use Naf\Mail\Core\Transport\DummyTransport;
use function Naf\app;

app()->container()->set(DummyTransport::class, static fn() => new DummyTransport());
```

The following script sends one message and reads it back. It registers the shared instance
itself when the bootstrap does not, so you can run it before changing `bootstrap.php`:

```php title="bin/mail-demo.php"
<?php

declare(strict_types=1);

require dirname(__DIR__) . '/bootstrap.php';

use Naf\Mail\Core\Transport\DummyTransport;
use function Naf\app;
use function Naf\Mail\{mail, mailer};

$container = app()->container();
if (!$container->has(DummyTransport::class)) {
    $container->set(DummyTransport::class, static fn() => new DummyTransport());
}

$message = mail()
    ->setFrom('hello@example.com')
    ->addTo('reader@example.com')
    ->setSubject('Hello from NAF')
    ->setContent('A local test message.', false);

if (!mailer()->send($message)) {
    throw new RuntimeException('The transport reported a failure.');
}

$messages = $container->get(DummyTransport::class)->getMessages();
echo 'Stored messages: ' . count($messages) . PHP_EOL;
echo 'Subject: ' . $messages[0]->getSubject() . PHP_EOL;
```

```bash
php bin/mail-demo.php
```

Expected output:

```text
Stored messages: 1
Subject: Hello from NAF
```

`getMessages()` returns the recorded `Mail` objects; `getRecipients()`, `getContent()`,
`isHtml()` and the other getters show what was submitted. `clear()` empties the list between
test cases. Returning `true` simulates successful transport acceptance; it does not establish
whether real mail would be delivered.

### Inspect messages after browser requests

The in-memory list belongs to the current PHP request/process. A subsequent browser request
cannot retrieve the previous request's list. For manual browser testing, use the
[`FileTransport` example](recipes/contact-form.md#a-local-mail-outbox): it writes a JSON
preview to `storage/mail/`, which remains available after the response or redirect.

## Real delivery and custom transports { #switching-to-real-delivery }

The default `MailTransport` uses PHP's `mail()`, which needs a configured delivery system on
the server. For SMTP or an external provider, implement
`TransportInterface::sendMail(Mail $mail): bool` with your chosen library and select the
class in `mail:transport`:

```php-inline
// app/config.php
'mail' => ['transport' => \App\Mail\SmtpTransport::class],
```

Constructor dependencies of the transport are autowired. When it needs scalar settings such
as a host or password, register a factory under the class name in `bootstrap.php`; the
mailer then uses that registration.

Keep test transports confined to development or tests: their successful return values mean
the simulation accepted the message. Constructing a separate `new Mailer(...)` or calling
`mailer($transport)` returns an independent mailer and does not change the shared `mailer()`.

## Queued delivery { #not-making-somebody-wait-for-it }

Delivery can delay the HTTP response. Push the message data to a [queue](queues.md) and let
a job build and send the message in the worker. Pass plain values such as addresses, a
subject and record identifiers rather than the `Mail` object, and make the job safe to run
twice: queue delivery is at least once.

Workers run under CLI. If the job renders its body with `naf/view`, register the guard
rules described in [Templates outside HTTP requests](views.md#templates-outside-http-requests).

## If the result is different

| What you see | What to check |
|---|---|
| `mail:transport must name a class implementing …` | The value is a class name of a class that implements `TransportInterface` |
| `Unable to send mail using PHP mail()` | PHP's `mail()` needs a configured delivery program (`sendmail_path`); use a capture transport locally |
| `getMessages()` is empty in a test | The test reads a different `DummyTransport` instance; register one shared instance in the container |
| No file appears in `storage/mail/` | The [contact recipe](recipes/contact-form.md#a-local-mail-outbox) selects `FileTransport` in `mail:transport`, and the directory is writable |
