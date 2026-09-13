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

## Accessing the Database

The `database()` helper gives you access to the PDO instance. Import it first:

```php
use function Naf\Database\database;

$pdo = database();
```

You can use standard PDO methods:

```php
$stmt = database()->query('SELECT * FROM users');
$users = $stmt->fetchAll();
```

---

## Database Configuration

Database settings are stored inside your application's `app/config.php` file under the `database` key.

Example `app/config.php`:

```php
<?php

return [
    'database' => [
        'driver'   => 'mysql',
        'host'     => '127.0.0.1',
        'database' => 'NAF',
        'username' => 'root',
        'password' => 'root',
        'charset'  => 'utf8mb4',
    ]
];
```

NAF builds the PDO connection dynamically based on this configuration.

- `driver`: e.g., `mysql`, `pgsql`, `sqlite`
- `host`: database server hostname or IP
- `database`: database name
- `username`: database user
- `password`: database password
- `charset`: character set (default `utf8mb4`)

---

## Example: Prepared Statements

You can use prepared statements with bound parameters:

```php
$stmt = database()->prepare('SELECT * FROM users WHERE id = :id');
$stmt->execute(['id' => 1]);
$user = $stmt->fetch();
```

- Prepared statements help protect against SQL injection.
- Use named parameters (`:name`) or question marks (`?`).

---

## Using Transactions

Transactions are fully supported:

```php
$pdo = database();
$pdo->beginTransaction();

try {
    $pdo->exec('INSERT INTO users (name) VALUES ("John")');
    $pdo->exec('INSERT INTO profiles (user_id) VALUES (LAST_INSERT_ID())');
    $pdo->commit();
} catch (\Exception $e) {
    $pdo->rollBack();
    throw $e;
}
```

- Transactions ensure atomic database operations.
- Always use try/catch blocks when working with transactions.

---

## Defaults applied

The PDO instance comes with these options:

```php
[
    PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
]
```

---

---

## How it works

* Loads config from `/app/config.php` from the key `database`
* Builds DSN based on a given driver (`mysql`, `sqlite`)
* Wraps PDO creation in a factory, handles exceptions gracefully
* Registers `database` in the container and provides the `database()` helper
