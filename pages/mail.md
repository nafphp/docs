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

Transport selection through configuration and the helper argument requires **naf/mail 0.2.2+**.
The plugin supplies this default, which an application can override in **`app/config.php`**:

```php
use Naf\Mail\Core\Transport\MailTransport;

return [
    'mail' => [
        'transport' => MailTransport::class,
    ],
];
```

`MailTransport` calls PHP's `mail()` and needs a server configured for delivery. The value of
`mail.transport` is a **class name implementing `TransportInterface`**, never an instance.
NAF reads the nested setting as `config('mail:transport')`.

`mailer()` retrieves the shared mailer. On first use, that mailer resolves the selected
transport: it uses the class's container registration when present, otherwise it constructs
the class with NAF's `make()`, including constructor autowiring. A simple transport therefore
needs no registration. Constructor-injected `Mailer` services use the same shared mailer.

If your transport needs scalar configuration, register a factory under **that transport's
class name** in the root `bootstrap.php`, after requiring `vendor/autoload.php` and before
`app()->run()`. Its required interface dependencies also need bindings. Register these before
any application service resolves the mailer. A generic `TransportInterface::class` binding
does not override the class selected by the config.

For an individual operation, pass a transport instance:

```php
use function Naf\Mail\mailer;

$mailer = mailer($transport);
$mailer->send($message);
```

**The argument wins.** It creates a separate mailer and bypasses config and the shared mailer;
neither is changed. Without an argument, the configured shared mailer is used. There is no
fallback transport: invalid configuration, a wrong container result or failed construction
raises an exception. `MailTransport` is the explicit plugin default, not an error fallback.

The same resolution works with `new Mailer()`; `new Mailer($transport)` uses the supplied
instance directly. Existing application overrides of `Mailer::class` continue to work,
though selecting the transport in config usually removes the need for such an override.

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
use Naf\Mail\Core\Transport\DummyTransport;
use function Naf\Mail\mailer;

$transport = new DummyTransport();
$mailer = mailer($transport);

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

For application-wide testing, set `mail.transport` to `DummyTransport::class` in
[the config above](#choosing-the-transport). To inspect captures outside the sending code,
register your dummy instance under `DummyTransport::class` in bootstrap; the configured
mailer and the test then use that same instance.

Captures are copies made at send time. `clear()` discards them between tests or worker jobs.
For previews that survive browser requests, use the contact form's
[file outbox recipe](recipes/contact-form.md#a-local-mail-outbox).

## Switching to real delivery

Set `mail.transport` to `MailTransport::class` to use PHP's `mail()`. For SMTP or a provider
API, select the class of your adapter implementing `TransportInterface::sendMail(Mail $mail): bool`
and register its factory if needed. The package does not include an SMTP or provider-specific
transport. Your message-building and sending calls stay the same.

## Not making somebody wait for it

An SMTP handshake takes as long as it takes, and the person who submitted the form is
watching a spinner for all of it. Hand the message to [a queue](queues.md) and let a worker
send it.
