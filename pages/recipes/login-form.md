---
title: A login form
requires:
  - naf/auth
  - naf/form
  - naf/view
  - naf/session
---

# A login form

Build a browser login with a protected account page and a logout form. You will use NAF's
authentication and session services to check credentials and keep a verified user signed in
across requests.

| Result | Packages | Starting point |
|---|---|---|
| Login, protected account page and CSRF-protected logout | Starter + `naf/auth`; `pdo_sqlite` for demo accounts | [Authentication quickstart](../auth.md#quickstart) |

Choose this scenario for browser sessions and private pages. Public websites and read-only
public APIs can start without accounts; [compare the scenarios](index.md).

First complete [the authentication quickstart](../auth.md#quickstart), including its SQLite
config, user model and seed command. It builds on [Your first
application](../first-app.md). These steps provide the account **demo** with password
**local-demo-password** for local use. The starter supplies Form and Session; update Form to
0.2.3 or newer, which the templates need for `csrf()->token()`:

```bash
composer require 'naf/form:^0.2.3'
```

Each titled block below is a complete file. Keep the authentication bootstrap and config.
Replace the routes, or merge the named routes when combining recipes.

## The routes

With the quickstart's account source and demo user in place, register the login, account and
logout actions. The controller below supplies the actions named here.

```php title="app/routes.php"
<?php

use App\Controllers\HomeController;
use App\Controllers\SessionController;
use function Naf\route;

route()->add('GET', '/', [HomeController::class, 'index'], 'home');
route()->add('GET', '/hello/{name}', [HomeController::class, 'hello'], 'hello');
route()->add('GET', '/account', [SessionController::class, 'account'], 'account');
route()->add('GET',  '/login',  [SessionController::class, 'show'],   'login');
route()->add('POST', '/login',  [SessionController::class, 'submit'], 'login.submit');
route()->add('POST', '/logout', [SessionController::class, 'logout'], 'logout');
```

Keep the sign-in route named `login`. Packages such as [`naf/oauth-server`](../oauth-server.md)
use that name to find the application's sign-in page.

**Logging out changes session state**, so it uses POST and a CSRF token. Visiting a link
should not perform that operation; the logout form below makes the intended action explicit.

## The controller

The controller connects the routes to authentication. It validates field types first, checks
credentials through `authenticate()` and requires a verified login before returning the
account page.

```php title="app/Controllers/SessionController.php"
<?php

namespace App\Controllers;

use Naf\Auth\Credentials\PasswordCredentials;
use Psr\Http\Message\ResponseInterface;
use function Naf\Auth\auth;
use function Naf\Form\validator;
use function Naf\View\render;
use function Naf\{abort, param};
use function Naf\redirect;
use function Naf\route;

final class SessionController
{
    public function show(): ResponseInterface
    {
        if (auth()->check()) {
            return redirect(route('account'));
        }

        return render('login', ['check' => validator(), 'loginError' => null]);
    }

    public function submit(): ResponseInterface
    {
        foreach (['username', 'password'] as $field) {
            if (!is_string(param()->get($field, ''))) {
                abort(400, 'Credentials must be strings.');
            }
        }

        $check = validator()->validate(param()->all(), [
            'username' => 'required',
            'password' => 'required',
        ]);

        if (!$check->isValid()) {
            return render('login', ['check' => $check, 'loginError' => null])->withStatus(422);
        }

        $credentials = new PasswordCredentials(
            param()->get('username'),
            param()->get('password'),
        );

        if (!auth()->authenticate($credentials)) {
            return render('login', [
                'check' => $check, 'loginError' => 'Those details did not match an account.',
            ])->withStatus(422);
        }

        return redirect(route('account'));
    }

    public function account(): ResponseInterface
    {
        auth()->requireLogin();
        return render('account', ['user' => auth()->user()]);
    }

    public function logout(): ResponseInterface
    {
        auth()->logout();

        return redirect(route('login'));
    }
}
```

Use one failure message for unknown accounts, incorrect passwords and suspended accounts,
so the response does not reveal which usernames exist. `authenticate()` returns `false` for
these credential failures; infrastructure and configuration failures can still throw.

Require a password at login, but enforce new length or complexity rules during registration
and password changes. Applying them here could reject an otherwise valid existing password.

With the Session plugin configured, successful authentication stores the provider and
identifier and rotates the session ID. The controller does not need to modify `$_SESSION`.

## The template

Next, add the form used by `show()` and failed login attempts. It displays field errors and
one credential-failure message while keeping the password field empty.

```html+php title="app/views/login.phtml"
<?php
use function Naf\Form\csrf;
use function Naf\Form\error;
use function Naf\Form\memory;
use function Naf\View\s;
use function Naf\route;
?>

<?php if ($loginError !== null): ?>
    <p class="error"><?= s($loginError) ?></p>
<?php endif; ?>

<form action="<?= route('login') ?>" method="post">

    <label for="username">Username</label>
    <input id="username" type="text" name="username" value="<?= s(memory('username') ?? '') ?>">
    <?= error('username', $check) ?>

    <label for="password">Password</label>
    <input id="password" type="password" name="password">
    <?= error('password', $check) ?>

    <input type="hidden" name="_csrf" value="<?= s(csrf()->token()) ?>">

    <button type="submit">Sign in</button>
</form>
```

`memory()` keeps the username available in the failed request so the visitor can correct it.
Leave the password field empty after a failed attempt to keep credentials out of the returned
HTML. The visitor can enter it again or use their password manager.

## The protected page and logout form

The account action checks access on the server, including direct requests to `/account`.
Its template can therefore show the verified username and a CSRF-protected logout button.

```html+php title="app/views/account.phtml"
<?php
use function Naf\Form\csrf;
use function Naf\View\s;
use function Naf\route;
?>
<h1>Signed in as <?= s($user->getUsername()) ?></h1>
<form action="<?= route('logout') ?>" method="post">
    <input type="hidden" name="_csrf" value="<?= s(csrf()->token()) ?>">
    <button type="submit">Sign out</button>
</form>
```

```bash
composer dump-autoload
php -S 127.0.0.1:8000 -t public
```

Check the complete flow in the browser:

1. Open **http://127.0.0.1:8000/login** and submit incorrect credentials. Expect 422, a failure
   message and the username you entered, with an empty password field.
2. Sign in with **demo** and **local-demo-password**. Expect a redirect to `/account`; reload
   that page to check that the session keeps you signed in.
3. Use the logout button. Expect to return to `/login`; a direct visit to `/account` now returns 401.

Submissions without a valid CSRF token return 400. `csrf()->token()` reuses the session's
token, so additional forms and open tabs remain valid.

## If the result is different

| What you see | What to check |
|---|---|
| The demo credentials are refused | Check that you completed the authentication quickstart, including its seed command, and are using the exact demo credentials |
| A submission returns 400 | Reload `/login` for a fresh form and retain the session cookie; avoid resubmitting an old form after the session changes |
| Reloading loses the login | Use the same host for each request and check browser cookies and the Session configuration |
| `/account` returns 401 after logout | This is the expected access check; return to `/login` to sign in again |
| A request returns 500 | Inspect the PHP server terminal and `logs/app.log` if it exists; check the quickstart's provider, database configuration and file permissions |

Keep CSRF protection enabled while diagnosing form errors. [Troubleshooting](../troubleshooting.md#forms-and-sessions)
has more checks for session cookies and tokens.

## Requiring a login elsewhere

To protect another action, make the access requirement part of that controller action:

```php-inline
use function Naf\Auth\auth;

auth()->requireLogin();                     // 401 if nobody is signed in
auth()->requirePermission('posts.edit');    // 403 if they lack it
```

Both checks throw an HTTP exception when access is denied; the framework turns it into an
error response before the action continues. `auth()->user()` returns your provider's identity
object for the signed-in user.

## What happens on the next request

The session stores the account source and identifier. Each request reloads the account through
that source, so a suspended or deleted account loses access on the next request.
[Authentication and permissions](../auth.md#sessions) explains this lifecycle.

See [Testing applications](../testing.md) to automate verification and [Deployment](../deployment.md) for production setup.
