---
title: Rate limits (draft)
---

Contributor draft. `naf/rate-limit` v0.1.0 is tagged and its repository is public, but the
package has not been registered on Packagist yet, so `tools/check_pages.py` rejects a page
that requires it. Move this file to `pages/rate-limits.md`, restore the `requires:` front
matter below, add it to `mkdocs.yml` under "Doing work", regenerate the reference and rerun
the checks once the package resolves.

```yaml
requires:
  - naf/rate-limit
```

# Rate limits

Some things should not be attempted a thousand times a minute: signing in, sending a
verification mail, exporting a report. `naf/rate-limit` counts attempts in your database and
tells you whether this one is still within the line.

## Asking

The package registers a `rateLimit` guard on the `Naf\guard()` registry the framework already
provides, so there is nothing new to learn and nothing extra to install:

```php
use function Naf\guard;
use function Naf\json;

$decision = guard()->rateLimit('export:account:' . $accountId, 10, 60);

if (!$decision['allowed']) {
    return json(['error' => 'Too many requests'], 429)
        ->withHeader('Retry-After', (string) $decision['retry_after']);
}
```

Ten attempts per sixty seconds, counted against that key. The answer is three fields:

| Field | Meaning |
|---|---|
| `allowed` | whether this attempt is within the limit |
| `remaining` | how many are left in the current window |
| `retry_after` | seconds until the window resets |

!!! warning "Check the field, not the array"
    `if ($decision)` is always true — it is a non-empty array either way. The question you
    meant to ask is `$decision['allowed']`.

`guard()->run('rateLimit', $key, $limit, $seconds)` does the same thing, and injecting
`PdoLimiter` directly shares the same buckets.

## Choosing a key

The key decides what is being limited, and it is yours to choose. Namespace it, so a limit on
exports cannot be spent by a limit on logins:

```php
guard()->rateLimit('login:account:' . $accountId, 5, 300);
guard()->rateLimit('login:address:' . $peerAddress, 20, 300);
```

Keys are stored hashed rather than as raw account identifiers or addresses. Use the direct
peer address unless you have deliberately configured a trusted proxy policy — a client-supplied
header is a suggestion, not an identity.

A guard call limits; it does not authenticate. Whoever is asking is still whoever your
application decided they are.

## Wiring it to a database

Installing the package intercepts nothing. Booting it creates no tables, opens no connection
and consumes no limit — the limiter is resolved on the first guard call, which is when your
connection has to be there:

```php
use function Naf\app;
use function Naf\Database\database;

app()->container()->set(PDO::class, static fn() =>
    database() ?? throw new LogicException('Rate limiting requires a configured database.'));
```

Create the table once, in an explicit migration using that connection:

```php
(new Naf\RateLimit\PdoLimiter($pdo))->install();
```

An existing `PDO::class` binding from another plugin is left alone, and binding your own
`PdoLimiter` works even after the default one has already answered a call. MariaDB, PostgreSQL
and SQLite are supported. Call `cleanup()` periodically — from a scheduled job, for instance —
to drop buckets whose window has passed.

## What a fixed window cannot promise

This is a fixed window, not a sliding one, and the difference shows at the boundary:

> Ten per minute means ten between 12:00:00 and 12:00:59, and ten more from 12:01:00. Somebody
> who spends their allowance at 12:00:59 and again at 12:01:00 made twenty attempts in two
> seconds, and every one of them was within the limit.

That is fine for protecting a mailbox or an export. It is not fine if a burst is the thing you
are defending against, and no amount of tuning the numbers changes the shape.

Two more things worth knowing:

- **Counting stays out of your transactions.** The limiter runs its own short transaction and
  refuses to join one you already opened, rather than counting inside work that might still
  roll back. Consume before you start the domain transaction.
- **A broken database refuses the request.** Storage errors propagate instead of being
  swallowed, because a limiter that silently allows everything when it cannot reach its table
  is worse than no limiter at all.
