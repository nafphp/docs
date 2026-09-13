---
title: A contact form
requires:
  - naf/form
  - naf/view
  - naf/session
  - naf/mail
---

# A contact form

Start from [Your first application](../first-app.md), then run `composer require naf/mail`.
The starter already supplies the other packages listed above. Each titled block is a complete
file; create missing directories and replace the tutorial's corresponding files. If you combine
recipes, merge their routes and service bindings instead of discarding the existing ones.

This local exercise writes messages to `storage/mail/` and shows a thank-you after redirecting.
It works without a mail server and sends nothing externally. For automated tests that only
need an in-memory list, see [the dummy transport](../mail.md#testing-without-a-mail-server). [Handling a POST
request](post-requests.md) explains the underlying request flow.

## A local mail outbox

```bash
mkdir -p app/Mail storage/mail
```

```php title="app/Mail/FileTransport.php"
<?php

namespace App\Mail;

use Naf\Mail\Core\TransportInterface;
use Naf\Mail\Models\Mail;

final class FileTransport implements TransportInterface
{
    public function sendMail(Mail $mail): bool
    {
        $data = json_encode([
            'from' => $mail->getFrom(), 'to' => $mail->getRecipients(),
            'replyTo' => $mail->getReplyTo(), 'subject' => $mail->getSubject(),
            'content' => $mail->getContent(), 'isHtml' => $mail->isHtml(),
        ], JSON_PRETTY_PRINT | JSON_THROW_ON_ERROR);
        $file = BASE_PATH . '/storage/mail/' . bin2hex(random_bytes(12)) . '.json';
        return file_put_contents($file, $data, LOCK_EX) !== false;
    }
}
```

```php title="bootstrap.php"
<?php

define('BASE_PATH', __DIR__);
require __DIR__ . '/vendor/autoload.php';

use App\Mail\FileTransport;
use Naf\Mail\Core\Mailer;
use Naf\Core\Event;
use Psr\Http\Message\ResponseInterface;
use function Naf\{app, event, request};

app()->container()->set(Mailer::class, static fn() => new Mailer(new FileTransport()));
// naf/framework 0.2.1 redirects carry HTTP/2; PHP's local server needs HTTP/1.x.
event()->listen(Event::RESPONSE_HEADER, static fn(ResponseInterface $response) =>
    $response->withProtocolVersion(request()->getProtocolVersion()));

app()->run();
```

## The routes

```php title="app/routes.php"
<?php
use App\Controllers\HomeController;
use App\Controllers\ContactController;
use function Naf\route;

route()->add('GET', '/', [HomeController::class, 'index'], 'home');
route()->add('GET', '/hello/{name}', [HomeController::class, 'hello'], 'hello');
route()->add('GET',  '/contact', [ContactController::class, 'show'],   'contact');
route()->add('POST', '/contact', [ContactController::class, 'submit'], 'contact.submit');
```

## The controller

```php title="app/Controllers/ContactController.php"
<?php

namespace App\Controllers;

use Psr\Http\Message\ResponseInterface;
use function Naf\Form\validator;
use function Naf\Mail\mail;
use function Naf\Mail\mailer;
use function Naf\Session\session;
use function Naf\View\render;
use function Naf\{abort, param};
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
        foreach (['name', 'email', 'message'] as $field) {
            if (!is_string(param()->get($field, ''))) {
                abort(400, 'Form fields must be strings.');
            }
        }

        $check = validator()->validate(param()->all(), [
            'name'    => 'required|max:80',
            'email'   => 'required|email',
            'message' => 'required|min:10|max:2000',
        ]);

        if (!$check->isValid()) {
            // Back to the form. What was typed is still in the request, so
            // memory() finds it — see the template below.
            return render('contact', ['check' => $check])->withStatus(422);
        }

        $mail = mail()
            ->setFrom('website@example.com')
            ->addTo('office@example.com')
            ->setReplyTo(param()->get('email'))
            ->setSubject('New contact message')
            ->setContent('From: ' . param()->get('name') . "\n\n" . param()->get('message'), false);

        if (!mailer()->send($mail)) {
            throw new \RuntimeException('Could not write the local mail preview.');
        }

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

**The body is plain text.** Passing `false` to `setContent()` avoids interpreting submitted
text as HTML. The subject is fixed; visitor text belongs in the body.

**The success path redirects.** The thank-you lives in a flash message, which survives exactly
one request — the redirect's — and is gone on the next reload.

## The template

```php title="app/views/contact.phtml"
<?php
use function Naf\Form\csrf;
use function Naf\Form\error;
use function Naf\Form\error_class;
use function Naf\Form\memory;
use function Naf\View\s;
use function Naf\Session\session;
use function Naf\route;
?>

<?php if ($notice = session()->getFlash('notice')): ?>
    <p class="notice"><?= s($notice) ?></p>
<?php endif; ?>

<form action="<?= route('contact') ?>" method="post">

    <label for="name">Your name</label>
    <input id="name" type="text" name="name"
           class="<?= error_class('name', $check) ?>"
           value="<?= s(memory('name') ?? '') ?>">
    <?= error('name', $check) ?>

    <label for="email">Your email address</label>
    <input id="email" type="email" name="email"
           class="<?= error_class('email', $check) ?>"
           value="<?= s(memory('email') ?? '') ?>">
    <?= error('email', $check) ?>

    <label for="message">Message</label>
    <textarea id="message" name="message" rows="8"
              class="<?= error_class('message', $check) ?>"><?= s(memory('message') ?? '') ?></textarea>
    <?= error('message', $check) ?>

    <input type="hidden" name="_csrf" value="<?= csrf()->generate() ?>">

    <button type="submit">Send</button>
</form>
```

`memory()` reads what was submitted, so a rejected form comes back filled in rather than blank —
the difference between fixing one field and typing everything again. `error()` renders the
message for one field, and `error_class()` gives you a class name to hang styling on. `error()` and `error_class()`
take the validator the controller passed down, which is why `show()` passes an unused one: the
same template serves both requests, and on the first there is simply nothing to report.

## Try it

```bash
composer dump-autoload
php -S 127.0.0.1:8000 -t public
```

Open **http://127.0.0.1:8000/contact**. Invalid fields return HTTP 422 with errors and the
submitted values. A valid name, email and message of at least ten characters redirects back
with a thank-you. Inspect the new JSON file in `storage/mail/`; it contains the message.
Reloading removes the flash message. A POST without a valid `_csrf` token returns 400.

The local outbox is application code for development, not a built-in NAF transport. To deliver
real mail, replace its `Mailer` binding with a configured transport from [Sending mail](../mail.md)
and use sender/recipient addresses you control. Check the boolean result before reporting
success. Use a [queue](../queues.md) when delivery should happen outside the request.
