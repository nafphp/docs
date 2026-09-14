---
title: Sending mail
requires:
  - naf/mail
---

# Sending mail

`naf/mail` builds messages with recipients, HTML or plain text, and attachments.
A `Mailer` delivers them through a `TransportInterface` implementation. The package includes
`MailTransport` for PHP's `mail()` and, since **0.2.2**, `DummyTransport` for local tests.

## Choosing the transport

**The transport is passed to `new Mailer($transport)`.** The plugin's default registration
creates `new Mailer(new MailTransport())`; PHP's `mail()` needs a server configured for delivery.

For the whole application, register your mailer in the root **`bootstrap.php`**, after
requiring `vendor/autoload.php` and before `app()->run()`:

```php
use Naf\Mail\Core\Mailer;
use Naf\Mail\Core\Transport\MailTransport;
use function Naf\app;

$transport = new MailTransport();
app()->container()->set(Mailer::class, static fn() => new Mailer($transport));
```

The `$transport` line selects delivery; the next line connects it to the shared `mailer()`
helper and constructor-injected `Mailer` services. Replace `new MailTransport()` with the
transport you want. Register it before application services receive their mailer.
Binding only `TransportInterface::class` does not change the default mailer.

For an individual operation, construct a separate `$mailer = new Mailer($transport)` and
call `$mailer->send($message)`. This leaves the application default in place.
The `mailer()` helper currently takes no transport argument.

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

The message stores one body; calling `setContent()` again replaces it. HTML and plain-text
alternatives cannot be supplied together with the current API. Escape user input before
including it in HTML, or use plain text. For an HTML template, pass the string returned by
[`Naf\View\view()`](views.md) to `setContent()`; this requires `naf/view`.

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

The `cid:` reference uses the name you gave, not the path. `addAttachment()` reads the file
immediately and stores its encoded contents in the message; a missing or unreadable file
throws `MailException`.

## When it does not go out

`send()` is typed to return `bool`, but `MailTransport` never returns `false` — it
throws `Naf\Mail\Exceptions\MailException` when PHP's `mail()` refuses the message.

```php
use Naf\Mail\Exceptions\MailException;
use function Naf\Mail\mailer;

try {
    if (!mailer()->send($message)) {
        // A custom transport reported failure.
    }
} catch (MailException $e) {
    // log it, queue a retry, tell somebody
}
```

Handle both paths when your application supports different transports. A successful return
means the transport accepted the message; it does not confirm arrival in the recipient's inbox.

## Testing without a mail server

`DummyTransport` is included in **naf/mail 0.2.2+**. It records messages in memory and returns
`true` without sending mail. In a bootstrapped application:

```php
use Naf\Mail\Core\Mailer;
use Naf\Mail\Core\Transport\DummyTransport;

$transport = new DummyTransport();
$mailer = new Mailer($transport);

$message = $mailer->createMail()
    ->setFrom('hello@example.com')
    ->addTo('reader@example.com')
    ->setSubject('A local test')
    ->setContent('Hello', false);

$mailer->send($message);

$messages = $transport->getMessages();
echo $messages[0]->getSubject(); // A local test
$transport->clear();
```

For application-wide testing, use `new DummyTransport()` in the
[bootstrap registration above](#choosing-the-transport). Calls to `mailer()->send($message)`
then use that instance, whose `getMessages()` you can inspect in the same process.

Captures are copies made at send time. `clear()` discards them between tests or worker jobs.
For previews that survive browser requests, use the contact form's
[file outbox recipe](recipes/contact-form.md#a-local-mail-outbox).

## Switching to real delivery

Select `new MailTransport()` in the same bootstrap registration to use PHP's `mail()`.
For SMTP or a provider API, supply an adapter implementing
`TransportInterface::sendMail(Mail $mail): bool`, and pass it to `new Mailer($transport)`
in that registration. The package does not include an SMTP or provider-specific transport.
Your message-building and sending calls stay the same.

## Not making somebody wait for it

An SMTP handshake takes as long as it takes, and the person who submitted the form is
watching a spinner for all of it. Hand the message to [a queue](queues.md) and let a worker
send it.
