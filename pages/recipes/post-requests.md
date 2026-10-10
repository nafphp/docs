---
title: Handling a POST request
requires:
  - naf/form
---

# Handling a POST request

A POST handler reads input, validates it, calls application logic and returns a response.
Follow that sequence here, then use a linked recipe to try it in a complete application. Start from
[Your first application](../first-app.md). The starter includes the form and session packages
used below. APIs can follow the same input flow with their own authentication and CSRF policy.

## Choose a worked scenario

| Task | Example | What to check |
|---|---|---|
| Accept a message from a browser | [Contact form](contact-form.md) | Invalid input stays on the page; valid input redirects; missing CSRF fails |
| Sign in or out | [Login form](login-form.md) | Credentials are checked; account access is protected; logout requires POST and CSRF |
| Create a record from JSON | [JSON API with a database](json-api.md) | Malformed JSON, media type, field validation and the saved record |

If you only need to display pages or return public JSON, start with the
[small website](small-website.md) or [storage-free API](simple-json-api.md). Neither needs a
state-changing POST. The [scenario list](index.md) shows the required packages for each path.

## One route or two

A form that renders and submits at the same URL needs both methods registered:

```php-inline
use App\Controllers\ContactController;
use function Naf\route;

route()->add('GET',  '/contact', [ContactController::class, 'show'],   'contact');
route()->add('POST', '/contact', [ContactController::class, 'submit'], 'contact.submit');
```

Both routes use the same path, with a separate method and name. `route('contact')` generates
the form URL; the incoming request method selects the action. Keeping display and submission
in separate actions makes the two responsibilities visible.

You can also register both routes to one action and branch with `is_post()` when that suits
the handler. The same input checks and response rules apply.

## Reading the body

With the routes registered, choose where the handler reads its input. Use `param()` when you
intend to accept combined sources: it merges the query string, form body and, when the request
has `Content-Type: application/json` and an empty parsed body, the decoded JSON body.

```php-inline
use function Naf\param;

$email = param()->get('email');
$city  = param()->get('address.city', 'unknown');   // dotted path into nested data
$all   = param()->all();
```

`get()` returns the supplied default when a key is absent. Check the type of a submitted value
before using it: a string default does not prevent the caller from sending an array.

Use `request()->getParsedBody()` for form-body-only input. For JSON endpoints that need to
distinguish malformed JSON from invalid fields, decode `(string) request()->getBody()` explicitly;
see [Requests and responses](../request-response.md#read-the-request).

## Checking it

After checking input types, validate the field values before calling application logic.
The following fragment shows the validator API; the [contact form](contact-form.md#the-controller)
includes the surrounding type checks and failure response.

```php-inline
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

Rules are a `|`-separated string, or an array. Form 0.2.3 ships nine — `required`, `string`,
`array`, `integer`, `email`, `min`, `max`, `boolean` and `date` — and anything else you
register yourself; see [Forms and validation](../forms.md#built-in-rules). Only `min` and
`max` accept a missing value; the other rules fail when the field is absent.

An unknown rule throws instead of being skipped. Correct misspelled or unregistered rule
names before treating a validation result as complete.

## Include a CSRF token { #csrf-is-already-handled }

With `naf/form` 0.2.3 installed, a listener checks every request method except GET, HEAD and
OPTIONS before your controller runs; Form 0.2.2 and older checked only POST, PUT and DELETE.
Print the session's token in every form:

```html+php
<?php use function Naf\Form\csrf; ?>
<input type="hidden" name="_csrf" value="<?= csrf()->token() ?>">
```

`csrf()->token()` (Form 0.2.3+) reuses the stored token across forms and tabs. On older
releases, call `csrf()->generate()` once per page and reuse its value.

Since Form 0.2.3, an `Authorization: Bearer` header no longer skips the check. An endpoint
that authenticates its callers with its own credentials needs an explicit named exemption
and must still verify those credentials. [Forms and
validation](../forms.md#requests-that-carry-their-own-credentials) covers how.

## Return a response { #answering }

After a successful browser form submission, redirect:

```php-inline
use function Naf\redirect;
use function Naf\route;

return redirect(route('contact'));
```

Redirecting after success makes a browser reload repeat the GET instead of submitting the
successful POST again. It does not prevent deliberate duplicate requests; operations such as
payments still need application-level idempotency.

On validation failure, return the form with errors and submitted values, usually with status
422. Validate before performing side effects so this response does not represent partial success.

## If the result is different

| What you see | What to check |
|---|---|
| POST returns 404 | Confirm you registered a POST route as well as the GET route and that the form action targets it |
| The browser form returns a CSRF error | Reload the GET form, retain cookies and include the generated token in the submission |
| The validator reports an unknown rule | Check the rule name and register custom rules before validating |
| Entered values disappear after validation fails | Return the form in the current request; `memory()` cannot carry input through a redirect |

Use the complete recipe's verification steps to distinguish expected validation responses
from an application failure. [Troubleshooting](../troubleshooting.md#forms-and-sessions)
has further checks for form and session behavior.

## Where to go next

- [A contact form](contact-form.md) — validation, a local mail outbox and a success redirect.
- [A login form](login-form.md) — credential checks, session persistence and protected account access.
- [A JSON API with a database](json-api.md) — JSON input, field validation and persistent records.
