---
title: ORM and repositories
requires:
  - naf/orm
---

# ORM and repositories

Repositories read rows as model objects; the entity manager saves them. `naf/orm` installs
`naf/database`, which supplies the PDO connection. It does not create tables for your models.

## A complete small example

Start from [Your first application](first-app.md), install the package above and enable PHP's
`pdo_sqlite` extension. Create `app/Models`, `app/Repositories`, `bin` and `storage` directories.
Use this config, or merge its `database` key into your existing config:

```php title="app/config.php"
<?php

return ['database' => [
    'driver' => 'sqlite',
    'database' => BASE_PATH . '/storage/app.sqlite',
]];
```

```php title="app/Models/Product.php"
<?php

namespace App\Models;

use Naf\ORM\Model\AbstractModel;

final class Product extends AbstractModel
{
    protected string $name = '';
    protected string $sku = '';
    protected string $status = 'active';
    protected string $created_at = '';

    public function getName(): string { return $this->name; }
}
```

`AbstractModel` inherits an array constructor and the nullable `id` property. The default table
name is the lowercase class name plus `s`: `Product` uses `products`, with primary key `id`.

```php title="app/Repositories/ProductRepository.php"
<?php

namespace App\Repositories;

use App\Models\Product;
use Naf\ORM\Repository\AbstractRepository;

final class ProductRepository extends AbstractRepository
{
    protected function getEntityClass(): string { return Product::class; }
}
```

```php title="bin/products-demo.php"
<?php

require dirname(__DIR__) . '/bootstrap.php';

use App\Models\Product;
use App\Repositories\ProductRepository;
use function Naf\Database\database;
use function Naf\ORM\{em, repo};

database()->exec('CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, sku TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL, created_at TEXT NOT NULL
)');
$products = repo(ProductRepository::class);
if ($products->findOneBy('sku', 'ABC-1') === null) {
    em()->save(new Product([
        'name' => 'NAF for Beginners', 'sku' => 'ABC-1',
        'status' => 'active', 'created_at' => gmdate('Y-m-d H:i:s'),
    ]));
}
$product = $products->findOneBy('sku', 'ABC-1');
echo $product->getName() . "\n";
```

```bash
composer dump-autoload
php bin/products-demo.php
```

Expect `NAF for Beginners`. Running it again finds the existing product.
For deployed applications, manage schema changes through [migrations](database.md#migrations).

## Finders

With the `$products` repository above:

```php
$all = $products->findAll();
$one = $products->findOneBy('sku', 'ABC-1');
$active = $products->findBy('status', 'active');
$recent = $products->findBy(['status' => 'active'], null, ['created_at' => 'DESC'], 20);
```

`findBy()` and `findOneBy()` accept a field/value pair or an array of criteria. `findBy()`
also accepts order, limit and offset. Column names are checked against the model's scalar
fields and primary key, or a repository's explicit `$allowedColumns` override. This whitelist
is derived from the model, not queried from the database schema. Parameter values use prepared
statements.

`findOrCreateBy()` and `findOrCreateManyBy()` fill a single named field when inserting.
Use them only when the other required fields have suitable model defaults.

## Related entities

To extend the example with categories or tags, first add their models, repositories and SQL
tables. The entity manager walks entity-valued properties to save foreign keys, and arrays
of entities to save pivot rows. These relations need application-defined accessors.

For a `Product` and `Tag`, the default pivot table is `product_tag`; its keys are `product_id`
and `tag_id`. A repository's `findByPivot(Tag::class, $tagId)` reads through that pivot. A
public `$pivotTables` mapping on either entity can override the pivot table name.

There is no lazy loading or proxy object. Write a repository query explicitly when you need
to load a relationship. For queries beyond the finders, use PDO through `database()`.

## Transactions

A single `em()->save()` opens a transaction when none is active. To span several saves:

```php
use function Naf\ORM\em;

// $order and $invoice are your already-created entities.
em()->begin();
try {
    em()->save($order);
    em()->save($invoice);
    em()->commit();
} catch (\Throwable $e) {
    em()->rollback();
    throw $e;
}
```

`em()->clear()` releases the manager's tracked state; call it periodically in long-running
workers. Define and migrate your schema yourself: the ORM does not generate it.
