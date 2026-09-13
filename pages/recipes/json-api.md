---
title: A JSON API
---

# A JSON API

This is a separate, **local development API** with persistent articles in SQLite. Begin with
[the core-only installation](../install.md#core-only-project), not the website starter: this
exercise uses only `naf/framework` and PHP's `pdo_sqlite` extension. It has no login, session or
form plugin. Keep the development server bound to `127.0.0.1`.

Every titled block is a complete file. Keep `public/index.php`, `.env` and `composer.json` from
the core-only installation; add or replace the files below.

```bash
mkdir -p app/Controllers app/Repositories bin storage
```

## Bootstrap and JSON errors

```php title="bootstrap.php"
<?php

define('BASE_PATH', __DIR__);
require __DIR__ . '/vendor/autoload.php';

use Naf\Core\{ErrorHandler, Event};
use function Naf\{app, event, json, log};

app()->container()->set(PDO::class, static fn() => new PDO(
    'sqlite:' . BASE_PATH . '/storage/articles.sqlite', null, null,
    [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC],
));

event()->listen(Event::EXCEPTION, static function (Throwable $exception) {
    log()->error('API request failed', ['exception' => $exception]);
    $status = ErrorHandler::resolveStatusCode($exception);
    return json(['error' => $status >= 500 ? 'Internal server error' : 'Request refused'], $status);
});

app()->run();
```

The PDO factory is resolved by type when NAF builds the repository. The exception listener also
covers unknown routes, so a client receives JSON errors. Expected failures return JSON directly
from the controller. A bootstrap parse error can happen before the listener is registered.

## Create the table

```php title="bin/create-articles.php"
<?php

require dirname(__DIR__) . '/bootstrap.php';

use function Naf\app;

app()->container()->get(PDO::class)->exec('CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL
)');
echo "Articles table ready.\n";
```

```bash
composer dump-autoload
php bin/create-articles.php
```

Expect `Articles table ready.`. The database file lives outside the public directory and
survives requests and server restarts. This example uses PDO directly, without an ORM.

## The repository

```php title="app/Repositories/ArticleRepository.php"
<?php

namespace App\Repositories;

use PDO;

final class ArticleRepository
{
    public function __construct(private PDO $pdo) {}

    public function all(): array
    {
        return $this->pdo->query('SELECT id, title, body FROM articles ORDER BY id')->fetchAll();
    }

    public function find(string $id): ?array
    {
        $stmt = $this->pdo->prepare('SELECT id, title, body FROM articles WHERE id = ?');
        $stmt->execute([$id]);
        return $stmt->fetch() ?: null;
    }

    public function create(string $title, string $body): array
    {
        $stmt = $this->pdo->prepare('INSERT INTO articles (title, body) VALUES (?, ?)');
        $stmt->execute([$title, $body]);
        return $this->find($this->pdo->lastInsertId());
    }

    public function delete(string $id): bool
    {
        $stmt = $this->pdo->prepare('DELETE FROM articles WHERE id = ?');
        $stmt->execute([$id]);
        return $stmt->rowCount() > 0;
    }
}
```

## Routes and controller

```php title="app/routes.php"
<?php

use App\Controllers\ArticleController;
use function Naf\route;

route()->add('GET', '/api/articles', [ArticleController::class, 'index'], 'api.articles.index');
route()->add('GET', '/api/articles/{id}', [ArticleController::class, 'show'], 'api.articles.show');
route()->add('POST', '/api/articles', [ArticleController::class, 'store'], 'api.articles.store');
route()->add('DELETE', '/api/articles/{id}', [ArticleController::class, 'destroy'], 'api.articles.destroy');
```

Placeholder names must match method argument names: `{id}` becomes `$id`.

```php title="app/Controllers/ArticleController.php"
<?php

namespace App\Controllers;

use App\Repositories\ArticleRepository;
use JsonException;
use Psr\Http\Message\ResponseInterface;
use function Naf\{json, request, response};

final class ArticleController
{
    public function __construct(private ArticleRepository $articles) {}

    public function index(): ResponseInterface
    {
        return json(['data' => $this->articles->all()]);
    }

    public function show(string $id): ResponseInterface
    {
        $article = $this->articles->find($id);
        return $article === null
            ? json(['error' => 'No article with that id.'], 404)
            : json(['data' => $article]);
    }

    public function store(): ResponseInterface
    {
        $mediaType = strtolower(trim(explode(';', request()->getHeaderLine('Content-Type'))[0]));
        if ($mediaType !== 'application/json') {
            return json(['error' => 'Use Content-Type: application/json.'], 415);
        }
        try {
            $data = json_decode((string) request()->getBody(), false, 512, JSON_THROW_ON_ERROR);
        } catch (JsonException) {
            return json(['error' => 'Malformed JSON.'], 400);
        }
        if (!$data instanceof \stdClass) {
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

        $article = $this->articles->create($data->title, $data->body);
        return json(['data' => $article], 201, ['Location' => '/api/articles/' . $article['id']]);
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

Explicit decoding distinguishes malformed JSON (400) from invalid fields (422) and prevents
query parameters from supplying a missing body field. The limits here count bytes. Use an
explicit Unicode character rule if your application needs a character limit.
A 204 response has no body; `json(null, 204)` would try to encode `null` as content.

## Try it

```bash
php -S 127.0.0.1:8000 -t public
```

In another terminal:

```bash
curl -i http://127.0.0.1:8000/api/articles
curl -i -X POST http://127.0.0.1:8000/api/articles \
  -H 'Content-Type: application/json' \
  -d '{"title":"First article","body":"Hello from NAF."}'
curl -i http://127.0.0.1:8000/api/articles/1
curl -i -X DELETE http://127.0.0.1:8000/api/articles/1
```

On a fresh database expect 200 with an empty list, 201 with the saved article, 200 with that
article, then 204 with an empty body. Use the returned ID when repeating the exercise.
A subsequent GET for the deleted ID returns 404. POST `{}` gives 422, broken JSON gives 400,
and an unknown route returns a JSON 404.

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
