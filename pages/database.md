---
title: Datenbank
requires:
  - naf/database
---

# Database

NAF provides a simple and flexible way to work with databases using native PDO.

You are free to build your own database layer or plug in any external ORM if needed.

---

## Accessing the Database

The global `database()` helper gives you access to the PDO instance:

```php
use function Naf\database;

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

## Summary

- Access the database via the `database()` helper.
- Configure database settings in `app/config.php` under the `database` key.
- NAF uses native PDO for maximum flexibility.
- You can integrate any external ORM if needed (e.g., Eloquent, Doctrine, etc.).