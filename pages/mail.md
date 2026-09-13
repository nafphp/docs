---
title: E-Mail versenden
requires:
  - naf/mail
---

# E-Mail versenden

<div style="text-align: center;" align="center">

[![NAF Mailer Plugin](https://github.com/nafphp/mailer/actions/workflows/php.yml/badge.svg)](https://github.com/nafphp/mailer/actions/workflows/php.yml)

</div>

[← Back to NAF](https://github.com/nafphp/framework)

---

> **A lightweight, extensible mailer system for NAF – with full transport abstraction and attachment support.**

This plugin provides a clean interface for sending emails in your NAF application. It includes a default `MailTransport` that uses PHP’s built-in `mail()` function, but can easily be swapped for SMTP, API-based services, or other custom transports.

> 🧩 Part of the official NAF plugin collection. Install it if you need flexible, framework-integrated email handling.

---

## Usage

### Basic mail sending

```php
$mail = mail()
    ->setFrom('hello@example.com')
    ->addTo('john@example.com')
    ->setSubject('Hello from NAF')
    ->setContent('<b>Welcome!</b>', true);

mailer()->send($mail);
```

---

### Add attachments

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

### Use a custom transport

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
