---
title: Database
requires:
  - naf/database
---

# Database

A PDO connection, configured in one place, with migrations to get the schema there.
You write SQL and get back what PDO gives you.

That is the whole of it. If you want rows to arrive as objects, [`naf/orm`](orm.md) sits
on top of this package; if you want somebody else's ORM, nothing here is in the way.

## Getting the connection

```php
use function Naf\Database\database;

$rows = database()->query('SELECT * FROM users')->fetchAll();
```

`database()` hands you a `PDO` instance — not a wrapper, not a query builder. Everything
PDO can do, you can do, and everything you already know about PDO applies.

It is typed `?PDO`: you get `null` if no database is configured, rather than an exception
from somewhere deeper.

## Two defaults that change how you write queries

The connection is created with:

```php
PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION
PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
```

**Errors throw.** A failed query raises `PDOException` instead of returning `false`, so
`if (!$stmt)` is a branch that never runs. Wrap what you want to handle and let the rest
reach the error handler.

**Rows arrive as associative arrays.** No `PDO::FETCH_ASSOC` on every call, and no numeric
duplicates of every column.

```php
$stmt = database()->prepare('SELECT * FROM users WHERE id = :id');
$stmt->execute(['id' => 1]);      // throws on failure; its bool return is not the row
$user = $stmt->fetch();
```

## Queries with values in them

```php
$stmt = database()->prepare('SELECT * FROM users WHERE email = :email');
$stmt->execute(['email' => $email]);
$user = $stmt->fetch();
```

Named placeholders or `?` — PDO accepts both, but not mixed in one statement. The reason to
prepare is not speed, it is that a prepared statement sends the query and the values
separately, so no value can end up read as SQL.

Do not build the other kind:

```php
database()->query("SELECT * FROM users WHERE email = '$email'");   // no
```

## Transactions

```php
$pdo = database();
$pdo->beginTransaction();

try {
    $pdo->prepare('UPDATE accounts SET balance = balance - :n WHERE id = :from')
        ->execute(['n' => 100, 'from' => 1]);
    $pdo->prepare('UPDATE accounts SET balance = balance + :n WHERE id = :to')
        ->execute(['n' => 100, 'to' => 2]);
    $pdo->commit();
} catch (\Throwable $e) {
    $pdo->rollBack();
    throw $e;
}
```

Because errors throw, the `catch` is the only place a failure can arrive — which is what
makes this shape safe. Rethrow after rolling back: swallowing the exception leaves the
caller believing the transfer happened.

## Migrations

A migration is a class with `up()` and `down()`, and it lives in `app/Migrations`.
The commands require the optional CLI package first:

```bash
composer require naf/cli
```

```bash
vendor/bin/naf db:migration:create
```

writes a skeleton there for you to fill in.

```bash
vendor/bin/naf db:migrate up       # apply what has not run
vendor/bin/naf db:migrate down     # roll back
```

The direction is an argument, given once. `db:migrate up up` is not a thing.

To run a single one:

```bash
vendor/bin/naf db:migrate up --name=CreateProductsTable
```

### Plugins bring their own

`app/Migrations` is not the only source. A plugin that needs a table registers its own
directory, so `naf/session` with database storage, `naf/oauth-client` and `naf/oauth-server`
all contribute migrations that `db:migrate up` runs alongside yours.

That is why a fresh install of one of those packages usually ends with a migration step, and
why you do not have to copy anybody's schema into your own migrations folder.

### Migrations and transactions

Migrations run in the order every registered path agrees on, are tracked by class name, and
roll back in the reverse of the order they were applied.

How much of that is transactional depends on the engine, and the difference matters when one
fails halfway:

| Engine | Behaviour |
|---|---|
| PostgreSQL, SQLite | schema changes and the tracking happen in one transaction — a failure leaves nothing behind |
| MySQL, MariaDB | DDL commits implicitly, so a failed migration can leave part of its work applied |

Write MySQL migrations so that running them again after a failure is safe. There is no
transaction to undo the statements that already committed.

!!! warning "Do not run migrations inside your own transaction"
    The runner manages its own, and nesting one inside an application transaction leaves the
    tracking and the schema able to disagree with each other.

## Configuration

```php
'database' => [
    'driver'   => 'mysql',
    'host'     => '127.0.0.1',
    'database' => 'naf',
    'username' => 'root',
    'password' => '',
    'charset'  => 'utf8mb4',
],
```

The port is filled in from the driver when you leave it out — 3306 for MySQL, 5432 for
PostgreSQL.

SQLite takes a path instead of a host, and defaults to an in-memory database when you give
it none:

```php
'database' => [
    'driver'   => 'sqlite',
    'database' => '/var/data/app.sqlite',   // or ':memory:'
],
```

An in-memory database is emptied when the process ends, which makes it right for tests and
wrong for everything else.

Credentials belong in `.env`. Read `$_ENV['DB_PASSWORD'] ?? ''` or use an
`ENV:DB_PASSWORD` config value; `env()` returns the application environment name.

## When the connection fails

A connection that cannot be made throws `Naf\Database\Exceptions\DatabaseException`,
wrapping the original `PDOException` message. It happens while the container builds the
connection — so a wrong password surfaces on the first query, not at boot.
