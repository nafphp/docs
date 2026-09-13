---
title: ORM and repositories
requires:
  - naf/orm
---

# ORM and repositories

Rows as objects, and a place to put the queries that fetch them. You define a model,
ask a repository for it, and get instances back instead of associative arrays.

It sits on `naf/database` and does not hide it: when a query wants to be SQL, write SQL.
Reach for this when you would otherwise write the same mapping and the same finders by
hand for the fifth time — not because an object mapper is the correct way to talk to a
database.

## A model

```php
namespace App\Models;

use Naf\ORM\Core\AbstractModel;

final class Product extends AbstractModel
{
    protected ?int $id = null;
    protected string $name = '';
    protected ?Category $category = null;
    protected array $tags = [];

    // getters and setters
}
```

The table name follows from the class name, and the primary key is `id` unless the model
says otherwise. A constructor taking an array is inherited, so a row can be hydrated
straight into an instance.

## A repository

```php
namespace App\Repositories;

use Naf\ORM\Repository\AbstractRepository;

final class ProductRepository extends AbstractRepository
{
    protected function getEntityClass(): string
    {
        return Product::class;
    }
}
```

That is the whole of it for the common case. The finders below come with the base class.

## Reading

```php
use function Naf\ORM\repo;

$products = repo(ProductRepository::class);

$all     = $products->findAll();
$one     = $products->findOneBy('sku', 'ABC-1');            // ?EntityInterface
$active  = $products->findBy('status', 'active');
$recent  = $products->findBy(['status' => 'active'], null, ['created_at' => 'DESC'], 20);
```

`findBy()` and `findOneBy()` take either a field and a value, or an array of criteria.
`findBy()` also takes an order, a limit and an offset — enough for a listing page without
writing SQL, and no attempt to be a query builder for anything past that.

Columns are checked against the table's own columns before they reach the statement, so a
field name coming from a request cannot turn into SQL.

## Reading through a pivot

```php
$productsWithTag = repo(ProductRepository::class)->findByPivot(Tag::class, $tagId);
```

The pivot table name is derived from the two singular table names in alphabetical order —
`product_tag` for `Product` and `Tag`. When your table is called something else, say so on
either entity:

```php
public array $pivotTables = [
    Tag::class => 'article_tags',
];
```

## Find or create

```php
$category = repo(CategoryRepository::class)->findOrCreateBy('name', 'Books');
$tags     = repo(TagRepository::class)->findOrCreateManyBy('name', ['Bestseller', 'Limited']);
```

Useful exactly where you would otherwise write the same select-then-insert by hand — tags,
categories, anything keyed by a natural name.

## Saving

```php
use function Naf\ORM\em;

$product = new Product();
$product->setName('NAF for Beginners');
$product->setCategory($category);
$product->addTag($tagA);
$product->addTag($tagB);

em()->save($product);
```

One call saves the whole graph. The entity manager walks the object: properties holding an
entity become a foreign key on this row, following the `<parent>_id` convention; properties
holding an array of entities become pivot rows.

Saving is on the entity manager, not on the repository — the repository reads, the manager
writes. Two objects rather than one, because a save that touches four tables is not a
concern of the repository for any one of them.

## Transactions

```php
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

`save()` opens a transaction on its own when none is running, so a single save is already
atomic across all the tables it touches. `begin()` is for spanning several.

`em()->clear()` drops what the manager is holding — worth calling in a long-running worker
that saves thousands of entities and would otherwise keep every one of them.

## What this is not

There is no lazy loading and no proxy objects. A getter that returns related entities asks
its repository, which means you can see the query in your own code rather than discovering
it in a profiler.

There is also no migration generator: the ORM reads the schema, it does not write it. Use
[`naf/database`](database.md) migrations for that.

Reach for this when you would otherwise write the same mapping and the same finders by hand
for the fifth time — not because an object mapper is the correct way to talk to a database.
When a query wants to be SQL, `database()` is one import away.
