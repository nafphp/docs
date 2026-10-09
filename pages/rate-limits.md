---
title: Rate limits
requires:
  - naf/rate-limit
---

# Rate limits

`naf/rate-limit` counts attempts in a database using fixed time windows. Call it explicitly
before a protected operation such as login, verification mail or export. It returns a decision;
your handler decides whether to continue or return HTTP 429.

Configure a PDO connection and install the limiter table before using the guard. Installing
the plugin alone does not intercept requests.

## Check a limit { #asking }

The package registers a `rateLimit` guard on the `Naf\guard()` registry the framework already
provides. After the database setup below, call it from a handler:

```php-inline
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
    The result is a non-empty array for both outcomes. Read `$decision['allowed']` to
    decide whether the operation may continue.

`guard()->run('rateLimit', $key, $limit, $seconds)` does the same thing, and injecting
`PdoLimiter` directly shares the same buckets.

## Choosing a key

The key decides what is being limited, and it is yours to choose. Namespace it, so a limit on
exports cannot be spent by a limit on logins:

```php-inline
guard()->rateLimit('login:account:' . $accountId, 5, 300);
guard()->rateLimit('login:address:' . $peerAddress, 20, 300);
```

Keys are stored hashed rather than as raw account identifiers or addresses. Use the direct
peer address unless you have deliberately configured a trusted proxy policy — a client-supplied
header can be forged.

Rate limiting does not authenticate callers. Derive account identifiers from verified
application identities.

## Database setup { #wiring-it-to-a-database }

Installing the package intercepts nothing. Booting it creates no tables, opens no connection
and consumes no limit — the limiter is resolved on the first guard call, which is when your
connection has to be there. Install and configure `naf/database` 0.2.4+ as described in
[Database](database.md); it registers the configured connection under `PDO::class`.
For a connection managed outside NAF, bind your own `PDO::class` service before that first
guard call.

Create the table once, in an explicit migration using the configured connection:

```php-inline
use Naf\RateLimit\PdoLimiter;
use function Naf\Database\database;

$pdo = database() ?? throw new LogicException('Rate limiting requires a configured database.');
(new PdoLimiter($pdo))->install();
```

An existing `PDO::class` binding is left alone. Binding your own `PdoLimiter` works even
after the default one has already answered a call. MySQL, MariaDB, PostgreSQL and SQLite are
supported. Call `cleanup()` periodically — from a scheduled job, for instance — to delete
buckets that expired more than 24 hours ago.

## Window boundaries and failures { #what-a-fixed-window-cannot-promise }

This is a fixed window, not a sliding one, and the difference shows at the boundary:

For a limit of ten per minute, ten attempts at 12:00:59 and ten more at 12:01:00 are all
allowed. Twenty attempts can therefore occur in two seconds around the window boundary.

A fixed window permits bursts around window boundaries. Choose another algorithm when the
requirement is a strict rolling-window or burst limit.

Transaction and failure behavior:

- **Counting stays out of your transactions.** The limiter runs its own short transaction and
  refuses to join one you already opened, rather than counting inside work that might still
  roll back. Consume before you start the domain transaction.
- **Storage errors propagate.** Handle them as failures; do not continue the protected
  operation as though the limit had allowed it.
