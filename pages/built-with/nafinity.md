---
title: Nafinity
---

# Nafinity

Project-isolated Kanban boards, and the largest thing built with NAF so far. It is here
because it answers a question the rest of this documentation can only assert: what a real
application looks like when the framework stays small and everything else is a plugin.

A Nafinity installation loads twenty plugins. The application itself is one of them.

## The split

The repository you clone is a skeleton. The product is a dependency.

```
naf/nafinity     the installation you own
  └── naf/board  everything the application does
        └── naf/framework and eighteen other plugins
```

That is the point rather than a packaging detail: extending Nafinity must never mean
editing it. Everything the product does lives in `naf/board`; everything you decide lives
in the skeleton, which is small enough to read in a minute.

```
app/
  composer.json      what your installation requires
  bootstrap.php      nine lines: autoload, BASE_PATH, run
  .env               the application's own environment
  src/
    config.php       everything the application runs on, in one file
    routes.php       routes you add; a path here wins over the board's
    extensions.php   your last word on what the application offers
    Controllers/     your code, namespace Nafinity\
    views/           a template here wins over the board's
  public/index.php   the entry point; assets are published in beside it
  storage/           uploads, sessions, queue and scheduler state
docker/, Makefile    how it runs locally
```

There is deliberately almost nothing there. A fresh installation is a complete
application, and none of it is a file you could break by editing.

## Running it

Nafinity ships with Docker Compose and a Makefile. One command builds the image, installs
dependencies, migrates, writes the declared roles, publishes assets, seeds a demo project
and starts everything:

```sh
make first-install
```

It is then at `https://localhost`, with a locally trusted certificate the same command
issued. `make help` lists the rest; the ones you will want early are `make assets` after
updating a package, `make migrate`, and `make logs`.

The stylesheets and scripts live inside `naf/board` and every plugin, so they are copied
into `app/public/` rather than checked in. A package added later is registered and absent
at the same moment, which a browser reports as a 404 on a module tag — which is to say
silently. `make health` compares the two and turns that silence into a sentence.

## The commands it brings

`make` wraps the ones a development installation needs daily; these are what it wraps, and
what a deployment runs directly. From the repository root, `bin/naf command:list` selects
local PHP inside the container or the Compose `app` service on the host. From `app/`, use
`bin/naf command:list` as well. Docker failures remain errors rather than falling back
to another runtime. Set `NAF_CLI_RUNTIME=local` or `NAF_CLI_RUNTIME=compose` to
choose explicitly; `NAF_CLI_SERVICE` selects another Compose service.

| Command | What it does |
|---|---|
| `nafinity:seed` | Demo data, and only into a database that has none |
| `nafinity:assets:publish` | Copy every package's stylesheets and scripts into `app/public/` |
| `nafinity:assets:check` | Report registered assets that were never published — a 404 on a module tag is otherwise silent |
| `nafinity:assets:remove` | Take published files back out, from the record written when they went in; works after the package is gone, which is the point |
| `nafinity:user` | Create an account, reading its password from standard input |
| `nafinity:admin` | Grant the admin role to an existing account, while nobody holds it yet |
| `nafinity:grant-default` | Give accounts holding no role at all the one an ordinary account has |
| `nafinity:migrations:rename` | Rewrite the namespace recorded for applied migrations, after renaming your own |

The first four are what `make assets`, `make seed` and `make health` call. The rest are for
the moments an installation is being set up or repaired, which is why they are commands rather
than screens. `make health` checks pending migrations and the configured attachment
storage as well as database readiness.

## Exporting boards

Board settings export that board's tickets. Installation settings can export one board or
all active boards the current account may export. CSV, JSON and installed exporter formats
use the same selection; status, archive state and inclusive UTC update dates can narrow the
result. Each board's export and field permissions are checked separately, including in a
combined download. Managing installation settings does not grant access to another board.

## Making it yours

**Your own code** goes in `app/src/` under the `Nafinity\` namespace. The namespace is
yours: nothing in `naf/board` refers to it, so rename it in `composer.json` if you would
rather call it something else.

**Overriding a template.** Copy the one you want from `vendor/naf/board/src/views/` into
`app/src/views/`, keeping the path. Host views win over the package's.

**Changing what the application offers.** `app/src/extensions.php` runs after Board's
providers, so anything reachable there can be replaced or removed — including a definition
an extension just added:

```php
use function Naf\Board\extensions;

extensions()->boardFilters()->remove('example.only-mine');
```

**Adding a plugin.** `composer require` it. A package of type `naf-plugin` is found
through Composer's installed-packages metadata. Plugins declare boot prerequisites in their
own manifests, so a normal Nafinity installation has no `plugins.php`. An extension that
registers a Board provider requires `naf/board` and declares
`extra.naf.boot.before: ["naf/board"]`; Board runs the provider after its own defaults.
Use `bin/naf plugins:debug` to inspect the order.

For the mechanisms a plugin has once it is installed, see
[how Nafinity is extended](extending-nafinity.md).

## What it is made of

Nafinity uses most of the NAF ecosystem rather than a corner of it, which is the other
reason it is worth reading as an example.

| It needs | For |
|---|---|
| [`naf/view`](../views.md) | Templates, with host paths winning over package paths |
| [`naf/database`](../database.md), [`naf/orm`](../orm.md) | Schema migrations, repositories |
| [`naf/auth`](../auth.md), [`naf/session`](../sessions.md) | Signing in against its own user model |
| [`naf/form`](../forms.md) | Validation and CSRF |
| [`naf/queue`](../queues.md), [`naf/schedule`](../scheduling.md) | Notification mail, reminders |
| [`naf/storage`](../file-storage.md) | Ticket attachments |
| [`naf/i18n`](../translations.md) | German source strings, English translation |
| [`naf/cli`](../console.md) | `nafinity:seed`, `nafinity:assets:publish` and friends |
| [`naf/rate-limit`](../rate-limits.md) | Slowing down sign-in attempts |
| [`naf/mcp`](../mcp.md) | Exposing tools to a local model |
| [`naf/rbac`](../rbac.md) | Roles and permissions an installation can edit |
| [`naf/websocket`](../websocket.md) | Live updates, and who else is on a board |

## Where the rest is written

The extension reference — every registry, every contract, what a plugin may declare and
what happens when it is removed — ships with the board itself, in `docs/Extensibility.md`
of `naf/board`. It is exhaustive and versioned with the code it describes, which a page
here could not be.

This chapter is the map. That file is the territory.
