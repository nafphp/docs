---
title: Choose an application scenario
---

# Choose an application scenario

Start with the result you need. These examples show the packages, complete files and requests
needed to reach a working application. The two smallest projects start in empty directories;
the form examples build on the application starter.

For a guided introduction to NAF itself, start with [Your first application](../first-app.md).
If you know which result you want, you can follow the small website or storage-free API
directly. You do not need to complete every scenario or install every listed package.

## What do you want to build?

| Scenario | What you get | Packages you add | Start here |
|---|---|---|---|
| A small public website | Two HTML pages, a shared layout, CSS and an escaped greeting | `naf/framework`, `naf/view` | [Small website](small-website.md) |
| A public JSON API without storage | Product list and detail endpoints, bounded input and JSON errors | `naf/framework` | [JSON API without a database](simple-json-api.md) |
| A website that accepts messages | Validated form, CSRF protection, a local mail outbox and a success redirect | Starter, then `naf/mail` | [Contact form](contact-form.md) |
| An account area | Login, protected page, session and CSRF-protected logout | Starter, then `naf/auth` | [Login form](login-form.md) and its account setup |
| A JSON API that stores records | Article CRUD, SQLite, migrations and prepared statements | `naf/framework`, `naf/database`, `naf/cli` | [JSON API with a database](json-api.md) |
| Work outside the HTTP request | A queued job or a scheduled task, executed by a worker | `naf/queue`, optionally `naf/schedule` | [Queues](../queues.md), [Scheduling](../scheduling.md) |
| A command-line tool | A registered command with arguments and an exit status | `naf/framework`, `naf/cli` | [Console commands](../console.md) |

The starter installs `naf/framework`, `naf/view` and `naf/form`; the form package brings
`naf/session`. Queue and schedule packages bring their CLI dependencies. The login example
uses SQLite through PDO, so it also needs `pdo_sqlite`. See [Choosing packages](../choosing-packages.md)
for dependency details and additional integrations.

The contact and login tutorials replace files in the starter. Follow each in a separate
project first; when combining them, merge routes, configuration and service registrations.
Each guide names the files to keep and the ones to replace, so you can start from a known state.

## Follow the output through the application

The small website and storage-free API use the same request flow:

1. `public/index.php` loads the application bootstrap.
2. A named route selects a controller action.
3. The controller checks request input and calls application logic where needed.
4. The controller returns an HTML or JSON response.
5. You check successful requests and failure cases using the supplied URLs and commands.

The website keeps its page content in templates. The API injects a plain PHP catalog service
into its controller. Neither needs a base controller or an ORM. Add persistence when the
application actually needs to store data.

## What the examples protect

| Concern | Where you can see it working |
|---|---|
| HTML injection | The website escapes dynamic text and quoted attributes with `s()` |
| Unexpected input types | The website rejects `name[]=Ada`; the API rejects `limit[]=1` |
| Unbounded input | The website limits name length; the API accepts limits from 1 to 100 |
| Internal error details | The API logs exceptions and returns a generic JSON message for 500 errors |
| State-changing browser requests | The form tutorials validate input and check CSRF tokens |
| SQL values | The persistent API uses prepared statements and explicit fields |
| Maintainable application code | Named routes, explicit imports, constructor injection and returned PSR-7 responses |

The first two examples intentionally expose public, read-only data. They need no login or
session. The article API permits writes for local development; its authentication section
explains what to add before exposing those operations. Each tutorial states its own scope.

Once an example works locally, use [Testing applications](../testing.md) to automate its
checks and [Deployment](../deployment.md) for HTTPS, the public document root, production
configuration and runtime permissions.
