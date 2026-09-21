---
external_classes: true
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
    plugins.php      the order plugins boot in
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

## Making it yours

**Your own code** goes in `app/src/` under the `Nafinity\` namespace. The namespace is
yours: nothing in `naf/board` refers to it, so rename it in `composer.json` if you would
rather call it something else.

**Overriding a template.** Copy the one you want from `vendor/naf/board/src/views/` into
`app/src/views/`, keeping the path. Host views win over the package's.

**Changing what the application offers.** `app/src/extensions.php` runs after the board
and every plugin has registered, so anything reachable there can be replaced or removed —
including a definition a plugin just added:

```php
use function Naf\Board\extensions;

extensions()->boardFilters()->remove('example.only-mine');
```

**Adding a plugin.** `composer require` it. A package of type `naf-plugin` is found
through Composer's installed-packages metadata, so there is nothing to register; list it
in `app/src/plugins.php` only when its position in the boot order matters.

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

Roles and permissions come from `naf/rbac`, live updates from `naf/websocket`. Both are
developed alongside the board rather than ahead of it, and each is documented with its own
source until it has a chapter here.

## Where the rest is written

The extension reference — every registry, every contract, what a plugin may declare and
what happens when it is removed — ships with the board itself, in `docs/Extensibility.md`
of `naf/board`. It is exhaustive and versioned with the code it describes, which a page
here could not be.

This chapter is the map. That file is the territory.
