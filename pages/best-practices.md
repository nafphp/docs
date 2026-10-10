---
title: Best practices
---

# Best practices

Start with the complete files in [Your first application](first-app.md). In reference chapters,
short snippets demonstrate one API and may belong inside an existing method; recipe blocks
with file titles contain complete files.

## Keep HTTP handling in controllers

Read and validate the request, call an application service, then return a response. A service
can own business rules and database operations without knowing about HTTP. Inject it through
the controller constructor; [the container](dependency-injection.md) can build concrete
classes with `make()` and resolve registered interfaces.

Prefer class or interface names as container keys when you want typed injection. String keys
are also supported, but you must retrieve them explicitly, for example inside a factory.
The [controller service example](controllers.md#dependencies) defines both classes and
shows successful lookups, invalid input and a missing resource.

## Use existing extension points

Use the container to select an implementation or configure a service. Use an
[event](events.md) when independent listeners should react to a completed application
operation, such as recording an audit entry after an import. A custom event needs both
a dispatch site and registered listeners; naming it alone does nothing. Keep an operation's
required business rules in the service that performs it so they cannot be skipped by a
missing listener.

Check the [existing packages](choosing-packages.md) and their configuration before adding
another renderer, mailer or dispatcher. If an application helper is useful, import it from
its own namespace and load its file explicitly or through Composer's `autoload.files`.
Putting a file at `app/functions.php` alone does not load it. Reuse `response()`,
`Naf\View\s()` and other existing helpers for the behavior they already provide.

## Read data deliberately

`param()` can combine body and query data. Use `request()->getParsedBody()` for form-body-only
input, or decode the raw JSON body when malformed JSON needs a distinct 400 response. Validate
both the type and the value before writing to storage. See [Handling a POST
request](recipes/post-requests.md).

`database()` returns PDO, so queries use prepared statements. Model finders belong to an
[ORM repository](orm.md), not to PDO. Keep credentials in the environment and configuration in
`app/config.php`; do not interpolate untrusted input into SQL or filenames.

## Return the right response

Use `abort(404)` for a missing HTML resource, or return `json(['error' => 'Not found'], 404)`
for an expected API failure. `abort()` throws; a custom JSON exception listener covers
unexpected API failures. See [Errors and aborting](errors.md).

After a successful browser form submission, redirect to a GET route. On validation failure,
render the submitted values and errors in the current request. `memory()` does not persist
values across a redirect.

## Escape at the output boundary

With `naf/view`, a template imports and calls `s()` explicitly:

```html+php
<?php use function Naf\View\s; ?>
<h1>Hello, <?= s($name) ?>!</h1>
```

Form values need escaping too. Print the CSRF token with `csrf()->token()` (Form 0.2.3+),
which reuses the session's token for every form and tab; `csrf()->generate()` replaces it.
See [Forms](forms.md).

## Keep deployment and local development distinct

Use `APP_ENV=dev` locally and `APP_ENV=prod` in production. The web root is `public/`.
Keep application files, environment files and storage outside that public directory. Add only
the packages needed for your feature and keep the Composer lock file for reproducible installs.

Run the example's verification steps after copying it. They check observable HTTP behavior,
including failure responses, rather than only whether PHP can parse a file.

Continue with [Application lifecycle](lifecycle.md), [Testing](testing.md) and [Deployment](deployment.md) for setup and operational procedures.
