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

A migration is a class with `up()` and `down()` methods that receive the PDO connection.
Application migrations may live in `app/Migrations` or `src/Migrations`; both directories
are discovered when present. The commands require the optional CLI package:

```bash
composer require naf/cli
```

### Create a migration

```bash
vendor/bin/naf db:migration:create
```

The command takes no name. It writes `app/Migrations/Migration<timestamp>.php` (always
under `app/`, even in a `src/` layout) with this skeleton:

```php
<?php

declare(strict_types=1);

namespace App\Migrations;

use Naf\Database\Core\AbstractMigration;
use PDO;

class Migration1760000000 extends AbstractMigration
{
    public function up(PDO $connection): void
    {
    }

    public function down(PDO $connection): void
    {
    }
}
```

Fill in both directions. `down()` must undo exactly what `up()` created:

```php-inline
public function up(PDO $connection): void
{
    $connection->exec('CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(200) NOT NULL,
        price_cents INTEGER NOT NULL
    )');
}

public function down(PDO $connection): void
{
    $connection->exec('DROP TABLE products');
}
```

You may rename the class and its file to something descriptive, such as
`CreateProductsTable`; keep the class name, file name and namespace consistent. Migrations
are tracked by fully qualified class name and run in file-name order, so keep a sortable
prefix (for example the timestamp) when you rename them. The SQL above uses SQLite syntax;
write the DDL your database expects. The [JSON API tutorial](recipes/json-api.md#create-the-schema-with-a-migration)
shows a complete, tested migration.

### Run and roll back

```bash
vendor/bin/naf db:migrate up       # apply every migration that has not run yet
vendor/bin/naf db:migrate up --name=CreateProductsTable
vendor/bin/naf db:migrate down --name=CreateProductsTable
```

Pass the direction as the positional argument `up` or `down`. `--name` (short `-n`) selects
exactly one migration by class name or file name without `.php`, or by fully qualified class
name; a name that matches nothing or several migrations fails without running anything.

!!! danger "`db:migrate down` without `--name` reverts every applied migration"
    Without `--name`, `down` runs `down()` for **all** applied migrations in reverse order,
    including the tables that plugins contributed (sessions, OAuth, RBAC and others). This
    usually deletes data. Roll back a single migration with `--name`, and take a backup
    before running `down` against a database that matters.

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

The `database` array in `app/config.php` selects the driver and connection:

| Key | Type | Default | Effect |
|---|---|---|---|
| `database:driver` | string | `mysql` | `mysql`, `pgsql` or `sqlite`; any other value throws `DatabaseException` |
| `database:host` | string | `127.0.0.1` | Server host (MySQL, PostgreSQL) |
| `database:port` | int | `3306` / `5432` | Server port; the default depends on the driver |
| `database:database` | string | `''`; SQLite `:memory:` | Database name, or the SQLite file path |
| `database:username` | string | `null` | Login name |
| `database:password` | string | `null` | Password; use an `ENV:` reference |
| `database:charset` | string | `utf8mb4` | MySQL connection character set |
| `database:migrationPaths` | list of directories | `[]` | Additional directories scanned for migrations |

Without a `database` array, `database()` returns `null` and migration commands report
`Database connection not found.`

=== "MySQL / MariaDB"

    ```php-inline
    'database' => [
        'driver'   => 'mysql',
        'host'     => '127.0.0.1',
        'database' => 'naf',
        'username' => 'naf',
        'password' => 'ENV:DB_PASSWORD',
        'charset'  => 'utf8mb4',
    ],
    ```

=== "PostgreSQL"

    ```php-inline
    'database' => [
        'driver'   => 'pgsql',
        'host'     => '127.0.0.1',
        'port'     => 5432,
        'database' => 'naf',
        'username' => 'naf',
        'password' => 'ENV:DB_PASSWORD',
    ],
    ```

=== "SQLite"

    ```php-inline
    'database' => [
        'driver'   => 'sqlite',
        'database' => BASE_PATH . '/storage/app.sqlite',   // or ':memory:'
    ],
    ```

Enable the matching PDO extension (`pdo_mysql`, `pdo_pgsql` or `pdo_sqlite`). SQLite takes a
file path instead of a host and defaults to an in-memory database when you give none; its
parent directory must be writable.

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
