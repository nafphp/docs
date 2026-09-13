---
title: Handling a POST request
requires:
  - naf/form
---

# Handling a POST request

Every form, every API call that changes something, arrives the same way: a request with a body,
which you read, check, act on, and answer. This page is the shape all the others on this page
follow.

## One route or two

A form that renders and submits at the same URL needs both methods registered:

```php
use function Naf\route;

route()->add('GET',  '/contact', [ContactController::class, 'show'],   'contact');
route()->add('POST', '/contact', [ContactController::class, 'submit'], 'contact.submit');
```

Two methods, two names, one path. Naming them separately matters because `route('contact')` is
what your form's `action` resolves to — you want the GET URL there, not the POST one.

You can also point both at one method and branch inside it with `is_post()`. Two methods is
usually easier to read; one method is easier when the form and its handling are three lines.

## Reading the body

`param()` is the one to reach for. It merges the query string, the form body and — when the
request says `Content-Type: application/json` — the decoded JSON body, in that order, so the
same controller reads a browser form and an API client without caring which it got:

```php
use function Naf\param;

$email = param()->get('email');
$city  = param()->get('address.city', 'unknown');   // dotted path into nested data
$all   = param()->all();
```

The default is returned when the key is absent, so `get()` never surprises you with a
notice.

`request()->getParsedBody()` is still there when you want the body and nothing else — no query
parameters merged in. Use it when a value arriving in the URL instead of the body would be
wrong.

## Checking it

```php
use function Naf\Form\validator;
use function Naf\param;

$check = validator()->validate(param()->all(), [
    'email'   => 'required|email',
    'message' => 'required|min:10',
]);

if (!$check->isValid()) {
    // $check->getErrorMessages() is ['email' => ['Please enter a valid email address.'], …]
}
```

Rules are a `|`-separated string, or an array. Five ship with `naf/form` — `required`, `email`,
`min`, `max` and `boolean` — and anything else you register yourself; see
[Forms and validation](../forms.md#your-own-rules).

**An unknown rule throws.** `validate()` does not skip a rule it does not recognise, which is
what you want: a typo in a rule name is a hole in your validation, and it should stop the
request rather than quietly pass everything.

## CSRF is already handled

With `naf/form` installed, a listener checks the token on every state-changing request before
your controller runs. You put the token in the form, and that is the whole of your part:

```php
<input type="hidden" name="_csrf" value="<?= csrf()->generate() ?>">
```

Requests that authenticate themselves some other way — a bearer token on an API route — need
exempting rather than a token they have no session to hold. [Forms and
validation](../forms.md#requests-that-carry-their-own-credentials) covers how.

## Answering

Do not render a page as the answer to a POST. Redirect:

```php
use function Naf\redirect;
use function Naf\route;

return redirect(route('contact'));
```

A rendered POST response is a page the browser will re-submit when somebody reloads it — the
double-charge, double-mail, double-comment bug. Redirecting means the reload re-runs a GET.

Failure is the exception: when validation fails you *do* render, because the page has to come
back with the errors and what was typed still in it. Nothing was changed, so there is nothing to
re-submit.

## Where to go next

- [A contact form](contact-form.md) — this, end to end, with mail.
- [A login form](login-form.md) — the same shape, with a session at the end of it.
- [A JSON API](json-api.md) — the same shape, answering machines.
