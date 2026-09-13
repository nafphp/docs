---
title: Sending mail
requires:
  - naf/mail
---

# Sending mail

Sending a message. The shipped transport uses PHP's `mail()`, which is enough for a
contact form on a server that already sends mail, and wrong for almost everything else —
swap it for SMTP or a provider's API by replacing one object.

If the person who triggered it should not wait for the SMTP handshake, put it behind
[a queue](queues.md).

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
try {
    mailer()->send($message);
} catch (MailException $e) {
    // log it, queue a retry, tell somebody
}
```

Checking the return value instead will not catch a failure. A transport of your own may
return `false`, so if you write one, decide which of the two you mean and be consistent.

## Using a different transport

The shipped `MailTransport` calls PHP's `mail()`. That is enough for a contact form on a
server that already sends mail, and wrong for almost everything else: no authentication, no
TLS, no delivery feedback beyond "the local MTA accepted it".

A transport is one method:

```php
namespace App\Mail;

use Naf\Mail\Core\TransportInterface;
use Naf\Mail\Models\Mail;

final class SmtpTransport implements TransportInterface
{
    public function sendMail(Mail $mail): bool
    {
        // your SMTP client, your API call
    }
}
```

Swap it in your application's `bootstrap.php` by rebinding the `Mailer`:

```php
use Naf\Mail\Core\Mailer;
use function Naf\app;

app()->container()->set(Mailer::class, fn() => new Mailer(new SmtpTransport()));
```

Rebinding is the part that matters. Constructing a `new Mailer(...)` in a controller works
for that one call, but `mailer()` keeps handing everybody else the container's instance —
which is still the one using PHP's `mail()`.

## Not making somebody wait for it

An SMTP handshake takes as long as it takes, and the person who submitted the form is
watching a spinner for all of it. Hand the message to [a queue](queues.md) and let a worker
send it.
