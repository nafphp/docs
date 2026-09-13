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

## Basic mail sending

```php
$mail = mail()
    ->setFrom('hello@example.com')
    ->addTo('john@example.com')
    ->setSubject('Hello from NAF')
    ->setContent('<b>Welcome!</b>', true);

mailer()->send($mail);
```

---

## Add attachments

```php
$mail = mail()
    ->setFrom('info@example.com')
    ->addTo('client@example.com')
    ->setSubject('Monthly Report')
    ->addAttachment('report.pdf', '/path/to/report.pdf')

mailer()->send($mail);
```

You can also attach images inline and reference them via `cid:`:

```php
->addAttachment('logo.png', '/path/to/logo.png', true)
->setContent('<img src="cid:logo.png">')
```

---

## Use a custom transport

To swap out the default `MailTransport`, inject your own:

```php
use Naf\Mail\Mailer;
use App\Mail\MyCustomTransport;

$mailer = new Mailer(new MyCustomTransport());
$mail   = mail()->addTo('john@example.com');
$mailer->send($mail);
```

Your transport must implement:

```php
Naf\Mail\Core\TransportInterface
```

---
