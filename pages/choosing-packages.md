---
title: What do I actually need?
---

# What do I actually need?

NAF is a small core with plugins around it. Nothing is installed that you did not ask for,
which is the point — and it means the first question is always *which pieces*.

These are the starting points people actually have. Find the one closest to yours, run the
command, and skip the rest.

---

## One endpoint that answers

A webhook receiver. A health check. A tiny service that takes JSON and gives JSON back.

```bash
composer require naf/framework
```

**That is the whole list.** Routing, the container, configuration, events, error handling
and the request and response objects are all in the core. There is no template engine to
switch off and no session being started behind your back.

```php
use function Naf\{json, request, route};

route()->add('POST', '/webhook', function () {
    $payload = request()->getParsedBody();
    // do the thing
    return json(['ok' => true]);
}, 'webhook');
```

Read [Routing](routing.md) and [Requests and responses](request-response.md). You are done.

---

## A small website

Pages people look at, a contact form that posts back, a layout you do not want to repeat.

```bash
composer require naf/view naf/form
```

`naf/form` brings `naf/session` with it, because CSRF tokens and remembered input both
need somewhere to live. You do not install it separately.

```php
use function Naf\route;
use function Naf\View\render;

route()->add('GET', '/contact', fn() => render('contact'), 'contact');
route()->add('POST', '/contact', [ContactController::class, 'submit'], 'contact.submit');
```

Read [Views and templates](views.md) and [Forms and validation](forms.md). If the site has
more than one language, add [`naf/i18n`](translations.md).

---

## A JSON API

No templates, no forms, no browser. Clients send a token and expect JSON.

```bash
composer require naf/framework
```

Again just the core. `json()` is a core helper, and so is `abort()` for the error cases.
You do **not** want `naf/form` here: it adds a CSRF check to every POST, PUT and DELETE,
which for a token-authenticated API is a check that protects nothing and refuses
legitimate requests. If you end up installing it for other reasons, a request with a
`Bearer` token passes anyway — see [CSRF protection](forms.md#csrf-protection).

For storage, add one of the two below.

---

## Something to store it in

Two answers, and which one depends on how much structure you want.

```bash
composer require naf/database      # PDO, prepared statements, migrations
composer require naf/orm           # entities and repositories — brings naf/database
```

`naf/orm` pulls `naf/database` in, so asking for the ORM is asking for both. Take
`naf/database` alone when you want to write SQL and have it stay SQL; take `naf/orm` when
you would otherwise write the same mapping code by hand.

Read [Database](database.md) or [ORM and repositories](orm.md).

---

## People with accounts

Sign-in, permissions, "this belongs to that user".

```bash
composer require naf/auth naf/orm naf/session
```

`naf/auth` requires only the core — it can work against anything you write a provider for.
But the ordinary case is a user model in a database and a session to stay signed in, which
is why the two are suggested alongside it rather than required.

```php
use function Naf\Auth\auth;

if (auth()->attempt(new PasswordCredentials($email, $password))) {
    // signed in
}
```

Read [Authentication and permissions](auth.md), and
[Why auth has this shape](auth-architecture.md) if you want the reasoning.

---

## Work that should not happen during the request

Sending mail, resizing images, anything that makes somebody wait for no reason.

```bash
composer require naf/queue        # brings naf/cli for the worker command
composer require naf/schedule     # brings naf/queue and naf/cli
```

`naf/queue` runs jobs when a worker picks them up. `naf/schedule` runs them at a time you
name, and needs the queue underneath — so asking for the scheduler gives you all three.

Read [Queues and workers](queues.md) and [Scheduled jobs](scheduling.md).

---

## "Sign in with Google"

Let people in with an account they already have, and keep your own user model.

```bash
composer require naf/oauth-client
```

Brings `naf/auth` and `naf/session`. Add `naf/view` if you want the ready-made button and
callback pages rather than building your own.

Read [Signing in with a provider](oauth-client.md).

---

## Being the provider

Other applications sign their users in through *you*, and your API checks their tokens.

```bash
composer require naf/oauth-server
```

Brings `naf/auth`, `naf/session` and `naf/form` — the consent screen is a form, and it needs
CSRF protection like any other.

Read [Being the provider](oauth-server.md). Before you put it in front of anyone, read the
concurrency notes in that chapter: the guarantees it makes about simultaneous requests are
properties of your database, and SQLite cannot demonstrate them.

---

## A tool for the terminal

No web server at all. Commands you run yourself or from cron.

```bash
composer require naf/cli
```

The core still does the wiring — configuration, the container, events — you just never
route an HTTP request through it.

Read [Console commands](console.md).

---

## Something a language model can call

Exposing part of your application as tools an assistant can use.

```bash
composer require naf/mcp
```

Read [MCP tools](mcp.md).

---

## Sending mail

Not a starting point on its own, but the thing everything eventually needs.

```bash
composer require naf/mail
```

Read [Sending mail](mail.md). If it should not block the response, put it behind
[a queue](queues.md).

---

## The short version

| You are building | Install |
|---|---|
| one endpoint, a webhook, an API | `naf/framework` |
| a website with pages and forms | `naf/view naf/form` |
| anything that stores data | `naf/database` or `naf/orm` |
| anything with accounts | `naf/auth naf/orm naf/session` |
| work that happens later | `naf/queue` or `naf/schedule` |
| sign-in through Google, GitHub, … | `naf/oauth-client` |
| your own OAuth provider | `naf/oauth-server` |
| a command-line tool | `naf/cli` |
| tools for a language model | `naf/mcp` |

Every package's own dependencies come along automatically. The
[package overview](packages.md) lists what pulls in what.
