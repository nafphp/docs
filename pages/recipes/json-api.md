---
title: A JSON API
requires:
  - naf/database
  - naf/cli
---

# A JSON API

Build a small **local development API** that lists, creates, reads and deletes articles.
[`naf/database`](../database.md) provides the configured SQLite connection and tracks schema
changes; [`naf/cli`](../console.md) runs the migrations. The repository uses ordinary PDO
prepared statements, and the controller returns JSON through NAF's response helpers.

Begin with [the core-only installation](../install.md#core-only-project), then stop its
development server while adding the files below. You need PHP 8.3+ with `pdo_sqlite` and
**`naf/database` 0.2.4+** for constructor injection of the configured PDO connection.

Every titled block is a complete file. Keep `public/index.php`, `.env` and `composer.json` from
the core-only installation; add or replace the files below.

```bash
composer require 'naf/database:^0.2.4' 'naf/cli:^0.2'
mkdir -p app/Controllers app/Migrations app/Repositories storage
```

This project has no login, session or form plugin. Keep the development server bound to
`127.0.0.1`; [authentication](#adding-authentication) is a separate step before deployment.

## Configure the database

```php title="app/config.php"
<?php

declare(strict_types=1);

return [
    'database' => [
        'driver'   => 'sqlite',
        'database' => BASE_PATH . '/storage/articles.sqlite',
    ],
];
```

The `storage/` directory must exist and be writable by PHP. The database file stays outside
`public/` and survives requests and server restarts. The plugin enables exception error mode
and associative fetches, and binds this same connection as `PDO::class` in the container.
NAF can therefore inject it into the repository without a custom connection factory.

## Return JSON errors

```php title="bootstrap.php"
<?php

declare(strict_types=1);

use Naf\Core\ErrorHandler;
use Naf\Core\Event;
use Psr\Http\Message\ResponseInterface;

use function Naf\app;
use function Naf\event;
use function Naf\json;
use function Naf\log;

define('BASE_PATH', __DIR__);

require __DIR__ . '/vendor/autoload.php';

event()->listen(Event::EXCEPTION, static function (Throwable $exception): ResponseInterface {
    log()->error('API request failed', ['exception' => $exception]);

    $status = ErrorHandler::resolveStatusCode($exception);

    return json(['error' => $status >= 500 ? 'Internal server error' : 'Request refused'], $status);
});

app()->run();
```

The exception listener also covers unknown routes, so a client receives JSON errors. Expected
failures return JSON directly from the controller. Unexpected failures are logged while the
response hides internal details. A bootstrap parse error can happen before the listener is
registered.

## Create the schema with a migration

```php title="app/Migrations/CreateArticlesTable.php"
<?php

declare(strict_types=1);

namespace App\Migrations;

use Naf\Database\Core\AbstractMigration;
use PDO;

final class CreateArticlesTable extends AbstractMigration
{
    public function up(PDO $connection): void
    {
        $connection->exec(
            <<<'SQL'
            CREATE TABLE articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT NOT NULL
            )
            SQL,
        );
    }

    public function down(PDO $connection): void
    {
        $connection->exec('DROP TABLE articles');
    }
}
```

```bash
composer dump-autoload
vendor/bin/naf db:migrate up
```

The plugin discovers `app/Migrations` automatically. Expect `up App\Migrations\CreateArticlesTable`
and `1 migration(s) successfully executed.`. It records the migration in its `migrations`
table; running `db:migrate up` again executes zero migrations and keeps existing articles.

To undo this example on a disposable database:

```bash
vendor/bin/naf db:migrate down --name=CreateArticlesTable
vendor/bin/naf db:migrate up
```

`down()` drops the table **and its articles**; the following `up` recreates an empty table.
For later schema changes, use `vendor/bin/naf db:migration:create` to generate a new migration
and fill in its `up()` and `down()` methods. Keep applied migrations unchanged.

## The repository

Keep SQL in the repository so the controller can concentrate on HTTP and input validation.
All values use named placeholders; PDO sends them separately from the SQL.

```php title="app/Repositories/ArticleRepository.php"
<?php

declare(strict_types=1);

namespace App\Repositories;

use PDO;
use RuntimeException;

final class ArticleRepository
{
    public function __construct(private readonly PDO $connection)
    {
    }

    /** @return list<array{id: int, title: string, body: string}> */
    public function all(): array
    {
        $statement = $this->connection->query(
            'SELECT id, title, body FROM articles ORDER BY id',
        );

        return $statement->fetchAll();
    }

    /** @return array{id: int, title: string, body: string}|null */
    public function find(string $id): ?array
    {
        $statement = $this->connection->prepare(
            'SELECT id, title, body FROM articles WHERE id = :id',
        );
        $statement->execute(['id' => $id]);
        $article = $statement->fetch();

        return $article === false ? null : $article;
    }

    /** @return array{id: int, title: string, body: string} */
    public function create(string $title, string $body): array
    {
        $statement = $this->connection->prepare(
            <<<'SQL'
            INSERT INTO articles (title, body)
            VALUES (:title, :body)
            SQL,
        );
        $statement->execute([
            'title' => $title,
            'body'  => $body,
        ]);

        return $this->find($this->connection->lastInsertId())
            ?? throw new RuntimeException('The saved article could not be read.');
    }

    public function delete(string $id): bool
    {
        $statement = $this->connection->prepare('DELETE FROM articles WHERE id = :id');
        $statement->execute(['id' => $id]);

        return $statement->rowCount() > 0;
    }
}
```

## Routes and controller

```php title="app/routes.php"
<?php

declare(strict_types=1);

use App\Controllers\ArticleController;

use function Naf\route;

route()->add(
    'GET',
    '/api/articles',
    [ArticleController::class, 'index'],
    'api.articles.index',
);
route()->add(
    'GET',
    '/api/articles/{id}',
    [ArticleController::class, 'show'],
    'api.articles.show',
);
route()->add(
    'POST',
    '/api/articles',
    [ArticleController::class, 'store'],
    'api.articles.store',
);
route()->add(
    'DELETE',
    '/api/articles/{id}',
    [ArticleController::class, 'destroy'],
    'api.articles.destroy',
);
```

Placeholder names must match method argument names: `{id}` becomes `$id`.

```php title="app/Controllers/ArticleController.php"
<?php

declare(strict_types=1);

namespace App\Controllers;

use App\Repositories\ArticleRepository;
use JsonException;
use Psr\Http\Message\ResponseInterface;
use stdClass;

use function Naf\json;
use function Naf\request;
use function Naf\response;
use function Naf\route;

final class ArticleController
{
    public function __construct(private readonly ArticleRepository $articles)
    {
    }

    public function index(): ResponseInterface
    {
        return json(['data' => $this->articles->all()]);
    }

    public function show(string $id): ResponseInterface
    {
        $article = $this->articles->find($id);
        if ($article === null) {
            return json(['error' => 'No article with that id.'], 404);
        }

        return json(['data' => $article]);
    }

    public function store(): ResponseInterface
    {
        $contentType = request()->getHeaderLine('Content-Type');
        $mediaType   = strtolower(trim(explode(';', $contentType)[0]));

        if ($mediaType !== 'application/json') {
            return json(['error' => 'Use Content-Type: application/json.'], 415);
        }

        try {
            $data = json_decode((string) request()->getBody(), false, 512, JSON_THROW_ON_ERROR);
        } catch (JsonException) {
            return json(['error' => 'Malformed JSON.'], 400);
        }

        if (!$data instanceof stdClass) {
            return json(['error' => 'Expected a JSON object.'], 422);
        }

        $fields = [];

        foreach (['title' => 200, 'body' => 10000] as $field => $maxBytes) {
            $value = $data->$field ?? null;
            if (!is_string($value) || trim($value) === '' || strlen($value) > $maxBytes) {
                $fields[$field] = ["Use a non-empty string of at most {$maxBytes} bytes."];
            }
        }

        if ($fields !== []) {
            return json(['error' => 'The article could not be saved.', 'fields' => $fields], 422);
        }

        $article  = $this->articles->create($data->title, $data->body);
        $location = route('api.articles.show', ['id' => $article['id']]);

        return json(['data' => $article], 201, ['Location' => $location]);
    }

    public function destroy(string $id): ResponseInterface
    {
        if (!$this->articles->delete($id)) {
            return json(['error' => 'No article with that id.'], 404);
        }

        return response('', 204);
    }
}
```

NAF builds the controller and repository through constructor injection. The database plugin
supplies their PDO dependency. The `Location` header uses the named route, so it follows the
route definition when the URL changes.

Explicit decoding distinguishes malformed JSON (400) from invalid fields (422) and prevents
query parameters from supplying a missing body field. The limits here count bytes. Use an
explicit Unicode character rule if your application needs a character limit.
Only `title` and `body` are passed to the repository; extra JSON properties are ignored.
A 204 response has no body; `json(null, 204)` would try to encode `null` as content.

## Try it

```bash
php -S 127.0.0.1:8000 -t public
```

In another terminal:

```bash
curl -i http://127.0.0.1:8000/api/articles
```

Create an article:

```bash
curl -i -X POST http://127.0.0.1:8000/api/articles \
  -H 'Content-Type: application/json' \
  -d '{"title":"First article","body":"Hello from NAF."}'
```

Expect status **201**, a `Location: /api/articles/1` header and this JSON body on a fresh database:

```json
{
    "data": {
        "id": 1,
        "title": "First article",
        "body": "Hello from NAF."
    }
}
```

Read it, then delete it. Use the returned `Location` when repeating the exercise:

```bash
curl -i http://127.0.0.1:8000/api/articles/1
curl -i -X DELETE http://127.0.0.1:8000/api/articles/1
```

| Request | Status | Result |
| --- | --- | --- |
| `GET /api/articles` | 200 | `data` contains the articles, or `[]` on an empty database |
| `POST /api/articles` with a valid article | 201 | Saved article and its `Location` header |
| `GET /api/articles/{id}` | 200 | Saved article |
| `DELETE /api/articles/{id}` | 204 | Empty body |
| Read or delete a missing article | 404 | JSON error |
| `POST` with malformed JSON | 400 | `Malformed JSON.` |
| `POST` without `Content-Type: application/json` | 415 | JSON error |
| `POST` with `{}`, an array or invalid fields | 422 | JSON error, with `fields` for invalid article fields |
| Unknown route | 404 | JSON error |

## Adding authentication

This local demo lets any caller read and change its articles. Before exposing it, add an
appropriate authentication and authorization policy to each operation:

| Use case | Starting point |
| --- | --- |
| A browser using your login session | [Auth](../auth.md) and [forms/CSRF](../forms.md) |
| An API accessed with OAuth access tokens | [OAuth server](../oauth-server.md) |
| Tools called by a language model | [MCP](../mcp.md) |

If you adapt this code into the website starter, `naf/form` also runs: POST and DELETE require
CSRF protection. Keep that protection for requests authenticated by cookies. A header beginning
with `Bearer` bypasses the form plugin's CSRF check, but **does not authenticate the request**.
Validate credentials independently and never fall back to cookie authentication after an
invalid bearer token. See [requests that carry their own credentials](../forms.md#requests-that-carry-their-own-credentials).
