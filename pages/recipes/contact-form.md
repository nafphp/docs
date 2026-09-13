---
title: A contact form
requires:
  - naf/form
  - naf/view
  - naf/session
  - naf/mail
---

# A contact form

A page with a form, a message that arrives by mail, and a thank-you that survives a reload.
Everything here is the shape from [Handling a POST request](post-requests.md), filled in.

## The routes

```php
// app/routes.php
use App\Controllers\ContactController;
use function Naf\route;

route()->add('GET',  '/contact', [ContactController::class, 'show'],   'contact');
route()->add('POST', '/contact', [ContactController::class, 'submit'], 'contact.submit');
```

## The controller

```php
namespace App\Controllers;

use Psr\Http\Message\ResponseInterface;
use function Naf\Form\validator;
use function Naf\Mail\mail;
use function Naf\Mail\mailer;
use function Naf\Session\session;
use function Naf\View\render;
use function Naf\param;
use function Naf\redirect;
use function Naf\route;

final class ContactController
{
    public function show(): ResponseInterface
    {
        return render('contact', ['check' => validator()]);
    }

    public function submit(): ResponseInterface
    {
        $check = validator()->validate(param()->all(), [
            'name'    => 'required|max:80',
            'email'   => 'required|email',
            'message' => 'required|min:10|max:2000',
        ]);

        if (!$check->isValid()) {
            // Back to the form. What was typed is still in the request, so
            // memory() finds it — see the template below.
            return render('contact', ['check' => $check]);
        }

        $mail = mail()
            ->setFrom('website@example.com')
            ->addTo('office@example.com')
            ->setReplyTo(param()->get('email'))
            ->setSubject('Contact form: ' . param()->get('name'))
            ->setContent(nl2br(htmlspecialchars(param()->get('message'))));

        mailer()->send($mail);

        session()->flash('notice', 'Thank you — we will get back to you.');

        return redirect(route('contact'));
    }
}
```

Three things in that method are deliberate.

**`setFrom()` is your own address, not the visitor's.** A message claiming to come from an
address you do not control is what every receiving mail server treats as forgery, and it will
land your mail in a spam folder or nowhere at all. The visitor's address belongs in
`setReplyTo()`, which is what hitting Reply should use anyway.

**The message is escaped before it is sent.** `setContent()` defaults to HTML, so unescaped
input from a form is an HTML injection into your own inbox. Either escape it, as here, or pass
`false` as the second argument and send plain text.

**The success path redirects.** The thank-you lives in a flash message, which survives exactly
one request — the redirect's — and is gone on the next reload.

## The template

```php
<?php
use function Naf\Form\csrf;
use function Naf\Form\error;
use function Naf\Form\error_class;
use function Naf\Form\memory;
use function Naf\Session\session;
use function Naf\route;
?>

<?php if ($notice = session()->getFlash('notice')): ?>
    <p class="notice"><?= $notice ?></p>
<?php endif; ?>

<form action="<?= route('contact') ?>" method="post">

    <label for="name">Your name</label>
    <input id="name" type="text" name="name"
           class="<?= error_class('name', $check) ?>"
           value="<?= memory('name') ?>">
    <?= error('name', $check) ?>

    <label for="email">Your email address</label>
    <input id="email" type="email" name="email"
           class="<?= error_class('email', $check) ?>"
           value="<?= memory('email') ?>">
    <?= error('email', $check) ?>

    <label for="message">Message</label>
    <textarea id="message" name="message" rows="8"
              class="<?= error_class('message', $check) ?>"><?= memory('message') ?></textarea>
    <?= error('message', $check) ?>

    <input type="hidden" name="_csrf" value="<?= csrf()->generate() ?>">

    <button type="submit">Send</button>
</form>
```

`memory()` reads what was submitted, so a rejected form comes back filled in rather than blank —
the difference between fixing one field and typing everything again. `error()` renders the
message for one field, and `error_class()` gives you a class name to hang styling on. All three
take the validator the controller passed down, which is why `show()` passes an unused one: the
same template serves both requests, and on the first there is simply nothing to report.

## What it needs

`naf/form` for validation and CSRF, `naf/view` for the template, `naf/session` for the flash
message, and `naf/mail` to send it. Mail needs a transport configured before anything leaves the
machine — see [Sending mail](../mail.md).

For a form that arrives many times a minute, or a mail server that is slow, hand the sending to
a [queue](../queues.md) instead of making the visitor wait for it.
