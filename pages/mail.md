---
title: Sending mail
requires:
  - naf/mail
---

# Sending mail

The default transport uses PHP's `mail()` and needs a server configured to deliver mail.
For local development, first configure [the dummy transport](#testing-without-a-mail-server)
or use [the contact form's file outbox](recipes/contact-form.md#a-local-mail-outbox).
Both let you exercise the application without a mail server or external delivery.

If the person who triggered real delivery should not wait for it, use [a queue](queues.md).

## Sending a message

`mail()` hands you an empty message, `mailer()` sends it. Both are imported from
`Naf\Mail`.

```php
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

```php
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

```php
->setContent('<b>Welcome!</b>')          // HTML
->setContent('Welcome!', false)          // plain text
```

There is no multipart alternative: a message is one or the other. If your recipients need
both, that is a transport concern, not this object's.

## Attachments

```php
->addAttachment('report.pdf', '/path/to/report.pdf');
```

The first argument is the filename the recipient sees, the second the file on disk. A third
argument marks the attachment as inline, which is how you reference an image from the HTML
body:

```php
mail()
    ->addAttachment('logo.png', '/path/to/logo.png', true)
    ->setContent('<img src="cid:logo.png">');
```

The `cid:` reference uses the name you gave, not the path.

## When it does not go out

`send()` is typed to return `bool`, but the shipped transport never returns `false` — it
throws `Naf\Mail\Exceptions\MailException` when PHP's `mail()` refuses the message.

```php
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

## Testing without a mail server

Start from [Your first application](first-app.md), then install `naf/mail`. Create the
following files; each titled block contains the complete file contents:

```bash
composer require naf/mail
mkdir -p app/Mail bin
```

### Create a dummy transport

`DummyTransport` below is application code you add yourself. Its `sendMail()` method records
a copy of the message and returns `true`; it does not connect to a mail server or send mail.
The copy lets a test inspect what was submitted even if the original message is changed later.

```php title="app/Mail/DummyTransport.php"
<?php

namespace App\Mail;

use Naf\Mail\Core\TransportInterface;
use Naf\Mail\Models\Mail;

final class DummyTransport implements TransportInterface
{
    /** @var list<Mail> */
    public array $messages = [];

    public function sendMail(Mail $mail): bool
    {
        $this->messages[] = clone $mail;
        return true;
    }
}
```

### Register it once

Register both the dummy and the mailer so application code and tests retrieve the same
transport instance. Rebinding `Mailer::class` makes the normal `mailer()` helper use it.

```php title="app/mail-dummy.php"
<?php

use App\Mail\DummyTransport;
use Naf\Mail\Core\Mailer;
use function Naf\app;

$container = app()->container();
$container->set(DummyTransport::class, static fn() => new DummyTransport());
$container->set(Mailer::class, static fn() => new Mailer(
    $container->get(DummyTransport::class),
));
```

In the root **`bootstrap.php`**, after requiring `vendor/autoload.php` and before
`app()->run()`, add:

```php
require_once BASE_PATH . '/app/mail-dummy.php';
```

Keep the other bootstrap code from your application. Choose one mailer binding: if you
previously added the contact recipe's `FileTransport` binding, replace it with this include.
A later binding would replace the dummy again. Register the transport before application
services resolve the mailer.

### Run a local check

This CLI script uses the same registration. `require_once` also makes it safe to run before
you add the include to the web bootstrap; it always selects the dummy before sending.

```php title="bin/mail-demo.php"
<?php

require dirname(__DIR__) . '/bootstrap.php';
require_once BASE_PATH . '/app/mail-dummy.php';

use App\Mail\DummyTransport;
use function Naf\app;
use function Naf\Mail\{mail, mailer};

$message = mail()
    ->setFrom('hello@example.com')
    ->addTo('reader@example.com')
    ->setSubject('Hello from NAF')
    ->setContent('A local test message.', false);

if (!mailer()->send($message)) {
    throw new RuntimeException('The transport reported a failure.');
}

$dummy = app()->container()->get(DummyTransport::class);
echo 'Stored messages: ' . count($dummy->messages) . PHP_EOL;
echo 'Subject: ' . $dummy->messages[0]->getSubject() . PHP_EOL;
```

```bash
composer dump-autoload
php bin/mail-demo.php
```

Expected output:

```text
Stored messages: 1
Subject: Hello from NAF
```

A test can inspect `$dummy->messages[0]->getRecipients()`, `getContent()` and the other
message getters on the recorded `Mail` object. Returning `true` simulates
successful transport acceptance; it does not establish whether real mail would be delivered.

### Inspect messages after browser requests

The in-memory list belongs to the current PHP request/process. A subsequent browser request
cannot retrieve the previous request's list. For manual browser testing, use the
[complete `FileTransport` example](recipes/contact-form.md#a-local-mail-outbox): it writes a
JSON preview to `storage/mail/`, which remains available after the response or redirect.

Neither transport is built into the package. Both implement `TransportInterface` and can be
replaced without changing calls to `mailer()->send($message)` in your controllers.

## Switching to real delivery

Remove the `app/mail-dummy.php` include when you want actual delivery. If there is no other
application binding, the package's default `MailTransport` uses PHP's `mail()`. For SMTP or
an external provider, implement `TransportInterface::sendMail(Mail $mail): bool` using your
chosen library and register a `Mailer` with that transport in the same place in bootstrap.

Keep test transports confined to development or tests: their successful return values mean
the simulation accepted the message. Constructing a separate `new Mailer(...)` in one
controller does not change the shared `mailer()` helper; replace the container binding.

## Not making somebody wait for it

An SMTP handshake takes as long as it takes, and the person who submitted the form is
watching a spinner for all of it. Hand the message to [a queue](queues.md) and let a worker
send it.
