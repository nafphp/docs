---
title: A login form
requires:
  - naf/auth
  - naf/form
  - naf/view
  - naf/session
---

# A login form

The same shape as [a contact form](contact-form.md), with one difference at the end: instead of
sending something, it starts a session that later requests recognise.

This page assumes accounts already exist and your model implements `UserInterface`. If it does
not yet, [Authentication and permissions](../auth.md) is the page that sets that up — one line
of configuration in the ordinary case.

## The routes

```php
use App\Controllers\SessionController;
use function Naf\route;

route()->add('GET',  '/login',  [SessionController::class, 'show'],   'login');
route()->add('POST', '/login',  [SessionController::class, 'submit'], 'login.submit');
route()->add('POST', '/logout', [SessionController::class, 'logout'], 'logout');
```

Name one of them `login`. Other packages look for a route by that name when they have to send
somebody to sign in — [`naf/oauth-server`](../oauth-server.md) finds its sign-in page that way,
and stops needing to be told where it is.

**Logging out is a POST.** A `GET /logout` can be triggered by any image tag on any page, which
means anybody can sign your users out by embedding a link. It changes state, so it takes a form
and a CSRF token like every other form.

## The controller

```php
namespace App\Controllers;

use Naf\Auth\Credentials\PasswordCredentials;
use Psr\Http\Message\ResponseInterface;
use function Naf\Auth\auth;
use function Naf\Form\validator;
use function Naf\Session\session;
use function Naf\View\render;
use function Naf\param;
use function Naf\redirect;
use function Naf\route;

final class SessionController
{
    public function show(): ResponseInterface
    {
        if (auth()->check()) {
            return redirect('/');
        }

        return render('login', ['check' => validator()]);
    }

    public function submit(): ResponseInterface
    {
        $check = validator()->validate(param()->all(), [
            'username' => 'required',
            'password' => 'required',
        ]);

        if (!$check->isValid()) {
            return render('login', ['check' => $check]);
        }

        $credentials = new PasswordCredentials(
            param()->get('username'),
            param()->get('password'),
        );

        if (!auth()->authenticate($credentials)) {
            session()->flash('error', 'Those details did not match an account.');

            return redirect(route('login'));
        }

        return redirect('/');
    }

    public function logout(): ResponseInterface
    {
        auth()->logout();

        return redirect(route('login'));
    }
}
```

**One message for every failure.** `authenticate()` answers `false` and never says which half was
wrong, and your page should not undo that: "no such user" and "wrong password" told apart is a
way to find out which addresses have accounts here. The same sentence covers an unknown
username, a wrong password and a suspended account.

**Do not validate the password's shape here.** A `min:8` on the login form tells somebody with a
seven-character password that they are not merely wrong but wrong in a specific way, and it
locks out every account created before you raised the rule. Length rules belong on the
registration form. Here, `required` is the whole of it.

**Nothing else has to happen for the session.** `authenticate()` writes the login itself, and
rotates the session id while doing it, so the id somebody arrived with is not the id they leave
signed in on. That is session fixation closed off, and it is not something you have to remember
to do.

## The template

```php
<?php
use function Naf\Form\csrf;
use function Naf\Form\error;
use function Naf\Form\memory;
use function Naf\Session\session;
use function Naf\route;
?>

<?php if ($error = session()->getFlash('error')): ?>
    <p class="error"><?= $error ?></p>
<?php endif; ?>

<form action="<?= route('login') ?>" method="post">

    <label for="username">Username</label>
    <input id="username" type="text" name="username" value="<?= memory('username') ?>">
    <?= error('username', $check) ?>

    <label for="password">Password</label>
    <input id="password" type="password" name="password">
    <?= error('password', $check) ?>

    <input type="hidden" name="_csrf" value="<?= csrf()->generate() ?>">

    <button type="submit">Sign in</button>
</form>
```

The username comes back through `memory()` after a failed attempt; the password deliberately
does not. Putting a password back into the HTML writes it into the page source, the browser's
back-forward cache and any proxy that logs bodies, to save one field of typing.

## Requiring a login elsewhere

In a controller that only signed-in people may reach:

```php
use function Naf\Auth\auth;

auth()->requireLogin();                     // 401 if nobody is signed in
auth()->requirePermission('posts.edit');    // 403 if they lack it
```

Both throw, and the framework turns them into responses — there is no `if` to forget. Who is
signed in is `auth()->user()`, which is your own model, exactly as your provider returned it.

## What happens on the next request

Only two values are kept: which source the account came from, and its identifier. Every request
reloads the account through that source, so a suspended or deleted account stops working at
once rather than whenever a cached copy happens to expire. [Authentication and
permissions](../auth.md#sessions) has the detail.
