---
title: Database
requires:
  - naf/database
---

# Database

`naf/database` provides a configured PDO connection and a migration runner. Query results,
prepared statements and transactions use PDO directly. The optional [ORM](orm.md) adds
entity mapping and repositories.

Configure a connection in `app/config.php` and enable the PDO driver for your database.
Migration commands additionally require `naf/cli`.

## Getting the connection

```php-inline
use function Naf\Database\database;

$rows = database()->query('SELECT * FROM users')->fetchAll();
```

`database()` returns the configured `PDO` connection. Its query and transaction APIs are
standard PDO methods.

It is typed `?PDO` and returns `null` when database configuration is absent.

Since `naf/database` 0.2.4, the plugin also registers the configured connection as
`PDO::class` in the container for constructor injection. Resolving that binding without
database configuration throws `DatabaseException`; the `database()` helper remains nullable.

## PDO defaults { #two-defaults-that-change-how-you-write-queries }

The connection is created with:

```php-inline
PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION
PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
```

**Errors throw.** A failed query raises `PDOException` instead of returning `false`, so
`if (!$stmt)` is a branch that never runs. Wrap what you want to handle and let the rest
reach the error handler.

**Rows arrive as associative arrays.** No `PDO::FETCH_ASSOC` on every call, and no numeric
duplicates of every column.

```php-inline
$stmt = database()->prepare('SELECT * FROM users WHERE id = :id');
$stmt->execute(['id' => 1]);      // throws on failure; its bool return is not the row
$user = $stmt->fetch();
```

## Prepared statements { #queries-with-values-in-them }

```php-inline
$stmt = database()->prepare('SELECT * FROM users WHERE email = :email');
$stmt->execute(['email' => $email]);
$user = $stmt->fetch();
```

Named placeholders or `?` — PDO accepts both, but not mixed in one statement. Bind values through prepared statements so user input is not concatenated into SQL.
Placeholders represent values, not table names or SQL syntax; allow-list dynamic identifiers.

Do not interpolate untrusted values into a query:

```php-inline
database()->query("SELECT * FROM users WHERE email = '$email'");   // no
```

## Transactions

```php-inline
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

PDO exceptions enter the `catch` block, which rolls back and rethrows. Production transfer
logic must also validate amounts, authorization and affected rows; a transaction alone does
not enforce those business rules.

## Migrations

A migration is a class with `up()` and `down()`. Application migrations may live in
`app/Migrations` or `src/Migrations`; both directories are discovered when present.
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

Pass the direction once, as the positional argument `up` or `down`.

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

To inspect what would run without applying it, use database 0.2.4+ with an existing migration
tracker:

```php-inline
use Naf\Database\Core\MigrationRunner;
use Naf\Database\Support\MigrationRegistry;
use function Naf\Database\database;

$pdo = database() ?? throw new RuntimeException('Database is not configured.');
$pending = (new MigrationRunner($pdo))->pending(MigrationRegistry::getPaths());
```

`$pending` is a list of fully qualified migration class names in the runner's global order.
Inspection uses the same `shouldRun()` rules as execution. It does not create the tracker,
run migrations or rewrite legacy names; a missing tracker or database error is reported.

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

```php-inline
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

```php-inline
'database' => [
    'driver'   => 'sqlite',
    'database' => '/var/data/app.sqlite',   // or ':memory:'
],
```

An in-memory database lasts only for the connection. Use a persistent file path for data
that must survive requests or process restarts.

Keep credentials in protected environment values. Use `ENV:DB_PASSWORD` in configuration
with framework 0.2.8+ when values may come from the process environment. Direct `$_ENV` reads
only see values in that array. `env()` returns the application environment name.

## Connection errors { #when-the-connection-fails }

A connection that cannot be made throws `Naf\Database\Exceptions\DatabaseException`,
wrapping the original `PDOException` message. It happens while the container builds the
connection. The failure appears when a consumer first resolves it; eager resolution during
boot can therefore fail before the first query.
