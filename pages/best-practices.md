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

```php
<?php use function Naf\View\s; ?>
<h1>Hello, <?= s($name) ?>!</h1>
```

Form values need escaping too. Call `csrf()->generate()` once per rendered page and reuse the
token for multiple forms: each call replaces the stored token. See [Forms](forms.md).

## Keep deployment and local development distinct

Use `APP_ENV=dev` locally and `APP_ENV=prod` in production. The web root is `public/`.
Keep application files, environment files and storage outside that public directory. Add only
the packages needed for your feature and keep the Composer lock file for reproducible installs.

Run the example's verification steps after copying it. They check observable HTTP behavior,
including failure responses, rather than only whether PHP can parse a file.
