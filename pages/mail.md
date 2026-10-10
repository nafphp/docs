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

`mail()` creates a message with configured sender defaults, and `mailer()` sends it. Both are imported from
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

With **naf/mail 0.2.3+**, add a text alternative to an HTML message:

```php-inline
->setContent('<b>Welcome!</b>')
->setTextContent('Welcome!')
```

Both built-in delivery transports send these as `multipart/alternative`. With
`setContent($body, false)`, the main body is plain text and a text alternative is ignored.
`getTextContent()` returns the supplied alternative or null.

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

`send()` returns `bool`. The PHP-mail transport throws
`Naf\Mail\Exceptions\MailException` when PHP's `mail()` refuses the message. The SMTP
transport wraps connection and delivery failures in the same exception, preserving the cause.

```php-inline
use Naf\Mail\Exceptions\MailException;
use function Naf\Mail\mailer;

try {
    mailer()->send($message);
} catch (MailException $e) {
    // log it, queue a retry, tell somebody
}
```

Checking the return value alone will not catch an exception. Custom transports, or a
cancelled SMTP send, may return `false`; callers that accept either should handle both.

## Configuration

| Key | Type | Default | Effect |
|---|---|---|---|
| `mail:transport` | class name | `Naf\Mail\Core\Transport\MailTransport` | Transport used by the shared `mailer()`; the class must implement `TransportInterface` |
| `mail:from` | string | empty | Default sender for `Mailer::createMail()` and `mail()` |
| `mail:reply_to` | string | empty | Default Reply-To; an unset message Reply-To falls back to its sender |
| `mail:username` | string | empty | Shared SMTP login; falls back to From when authentication is enabled |
| `mail:password` | string | empty | Shared SMTP password or OAuth access token |
| `mail:smtp:host` | string | empty | Required SMTP hostname or IP |
| `mail:smtp:port` | integer | automatic | 465 for TLS, 587 for STARTTLS, otherwise 25; `mailpit` defaults to 1025 |
| `mail:smtp:security` | string | `auto` | `auto`, `starttls`, `tls` or `none` |
| `mail:smtp:authentication` | string | `auto` | `auto`, `off`, `on`, `login`, `plain`, `cram-md5`, `xoauth2` or `oauth` |
| `mail:smtp:username` | string | inherited | Nonempty value overrides the shared username |
| `mail:smtp:password` | string | inherited | Nonempty value overrides the shared password/token |
| `mail:smtp:timeout` | number | `15` | Connection timeout in seconds; greater than zero and at most 300 |
| `mail:smtp:ca_file` | string | empty | Optional readable CA file; system trust is used otherwise |

The mailer takes the transport from the container when that class is registered there, and
otherwise builds it with `make()`, so the transport's constructor dependencies are autowired.
`mail:transport` and the shipped `DummyTransport` require `naf/mail` **0.2.2** or newer.
Sender defaults, text alternatives, SMTP and provider metadata require **0.2.3+**.
Explicit `setFrom()` and `setReplyTo()` calls override the configured defaults.

## Send through SMTP

The built-in `Naf\Mail\Core\Transport\SmtpTransport` uses Symfony Mailer. Composer installs
that dependency and requires OpenSSL alongside the existing fileinfo and mbstring extensions.
Merge this fragment into `app/config.php` and provide the environment values on the server:

```php-inline
use Naf\Mail\Core\Transport\SmtpTransport;

return [
    'mail' => [
        'transport' => SmtpTransport::class,
        'from' => 'support@example.com',
        'reply_to' => 'support@example.com',
        'username' => 'ENV:MAIL_USERNAME',
        'password' => 'ENV:MAIL_PASSWORD',
        'smtp' => [
            'host' => 'smtp.example.com',
            'port' => 587,
            'security' => 'starttls',
            'authentication' => 'on',
        ],
    ],
];
```

Authentication requires encryption, a username and a password/token. `on` negotiates a
supported mechanism; select `login`, `plain`, `cram-md5` or `xoauth2` to require one.
`oauth` is an alias for `xoauth2`; obtaining and refreshing the access token belongs to the
application. `auto` enables authentication when a shared or SMTP-specific login/password
is supplied. From alone does not enable it. An empty protocol-specific credential inherits
the shared value.

Automatic security selects implicit TLS for port 465, unencrypted delivery for `localhost`,
`127.0.0.1`, `::1` and `mailpit`, and STARTTLS for other hosts. TLS certificates and hostnames
are always verified. Explicit STARTTLS fails if the server cannot upgrade; use `ca_file`
for a private trusted CA. Unencrypted mode cannot send authentication credentials.

The transport validates configuration and opens a connection only when sending or checking.
An incomplete SMTP configuration therefore does not break unrelated pages. To check TLS and
login without sending a message, run this fragment after application bootstrap:

```php-inline
use Naf\Mail\Core\Transport\SmtpTransport;

(new SmtpTransport())->checkConnection();
```

Connection checks may throw configuration or Symfony transport exceptions. Catch `Throwable`
at an administrative boundary and show a suitable message without exposing credentials.

## Describe provider configuration fields

`ConfigurableTransportInterface` optionally extends `TransportInterface` with static
`configurationFields(): array`. A configuration renderer can request metadata without
constructing a transport:

```php-inline
use Naf\Mail\Core\Transport\{SmtpTransport, TransportConfiguration};

$fields = TransportConfiguration::fields(SmtpTransport::class);
```

Each key is a colon-separated configuration path. A description can contain `label`, `type`,
`default`, `index`, `options` and `sensitive`. The built-in SMTP metadata supplies choices,
port/time limits and a secret flag for its password. Existing transports without the optional
interface return an empty description. Mark credentials explicitly as sensitive; metadata
does not itself render, validate, persist or redact values.

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
    'mail' => [
        'transport' => DummyTransport::class,
        'from' => 'hello@example.com',
    ],
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
    ->addTo('reader@example.com')
    ->setSubject('Hello from NAF')
    ->setContent('<b>A local test message.</b>')
    ->setTextContent('A local test message.');

if (!mailer()->send($message)) {
    throw new RuntimeException('The transport reported a failure.');
}

$messages = $container->get(DummyTransport::class)->getMessages();
echo 'Stored messages: ' . count($messages) . PHP_EOL;
echo 'Subject: ' . $messages[0]->getSubject() . PHP_EOL;
echo 'Sender: ' . $messages[0]->getFrom() . PHP_EOL;
echo 'Text: ' . $messages[0]->getTextContent() . PHP_EOL;
```

```bash
php bin/mail-demo.php
```

Expected output:

```text
Stored messages: 1
Subject: Hello from NAF
Sender: hello@example.com
Text: A local test message.
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
the server. Use the built-in [SMTP transport](#send-through-smtp) for direct SMTP. For another provider, implement
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

Workers can render mail bodies with `naf/view` after application boot. Framework 0.2.9+
provides the required guards under CLI; older versions need the registration described in
[Templates outside HTTP requests](views.md#templates-outside-http-requests).

## If the result is different

| What you see | What to check |
|---|---|
| `mail:transport must name a class implementing …` | The value is a class name of a class that implements `TransportInterface` |
| `Unable to send mail using PHP mail()` | PHP's `mail()` needs a configured delivery program (`sendmail_path`); use a capture transport locally |
| `getMessages()` is empty in a test | The test reads a different `DummyTransport` instance; register one shared instance in the container |
| No file appears in `storage/mail/` | The [contact recipe](recipes/contact-form.md#a-local-mail-outbox) selects `FileTransport` in `mail:transport`, and the directory is writable |
