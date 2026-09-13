---
title: A JSON API
requires:
  - naf/form
---

# A JSON API

The same shape as the forms — read, check, act, answer — with two differences: the body arrives
as JSON, and the answer has to be JSON too, including when it goes wrong.

Nothing here needs a plugin for the API itself. `naf/form` is listed because the validation is
worth having; drop it and you write the checks by hand.

## The routes

```php
// app/routes.php
use App\Controllers\ArticleController;
use function Naf\route;

route()->add('GET',    '/api/articles',      [ArticleController::class, 'index'],   'api.articles.index');
route()->add('GET',    '/api/articles/{id}', [ArticleController::class, 'show'],    'api.articles.show');
route()->add('POST',   '/api/articles',      [ArticleController::class, 'store'],   'api.articles.store');
route()->add('DELETE', '/api/articles/{id}', [ArticleController::class, 'destroy'], 'api.articles.destroy');
```

Path parameters arrive as arguments, in the order they appear in the path. See
[Routing](../routing.md) for the full set of patterns.

## Reading a JSON body

`param()` decodes it for you when the request says `Content-Type: application/json`, and the same
call reads a form body when it does not:

```php
use function Naf\param;

$title = param()->get('title');
$tags  = param()->get('meta.tags', []);     // dotted path into nested JSON
```

So a controller written against `param()` serves `curl -d` and `fetch()` without branching.

## Answering

`json()` takes the payload, a status, and headers:

```php
use function Naf\json;

return json(['data' => $articles]);                       // 200
return json(['data' => $article], 201);                   // created
return json(null, 204);                                   // deleted, nothing to say
```

**Say the status with the body, not instead of it.** A client that gets `200` with
`{"error": "..."}` has to parse the body to find out it failed; a client that gets `404` with an
empty body has to guess why. Both halves carry information, so send both.

## The controller

```php
namespace App\Controllers;

use Psr\Http\Message\ResponseInterface;
use function Naf\Form\validator;
use function Naf\json;
use function Naf\param;

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

        if ($article === null) {
            return json(['error' => 'No article with that id.'], 404);
        }

        return json(['data' => $article]);
    }

    public function store(): ResponseInterface
    {
        $check = validator()->validate(param()->all(), [
            'title' => 'required|max:200',
            'body'  => 'required|min:1',
        ]);

        if (!$check->isValid()) {
            return json([
                'error'  => 'The article could not be saved.',
                'fields' => $check->getErrorMessages(),
            ], 422);
        }

        $article = $this->articles->create(param()->get('title'), param()->get('body'));

        return json(['data' => $article], 201);
    }

    public function destroy(string $id): ResponseInterface
    {
        if (!$this->articles->delete($id)) {
            return json(['error' => 'No article with that id.'], 404);
        }

        return json(null, 204);
    }
}
```

`getErrorMessages()` is already shaped for this — field name to a list of messages — so a client
can put each one next to the input it belongs to instead of showing one sentence for the whole
form.

**Return the failure, do not `abort()`.** `abort()` raises an error for the framework to render,
which is what you want on a web page and not what you want here: an endpoint that answers JSON
nine times and HTML on the tenth breaks the client that was parsing it. Return `json()` with the
status yourself and every answer has the same shape.

## Authentication

A request whose `Authorization` header starts with `Bearer` passes the CSRF check without a
token — nothing attaches a bearer token by itself, so a request carrying one was built
deliberately by whoever holds it. That is the one exemption you get for free; see
[Forms and validation](../forms.md#requests-that-carry-their-own-credentials).

Issuing and checking the tokens themselves is a separate job, and there is a package for the
shape you need:

| | |
| --- | --- |
| Your own clients, your own API | [`naf/oauth-server`](../oauth-server.md) — OAuth2 and OpenID Connect, scopes tied to permissions |
| A language model calling in | [`naf/mcp`](../mcp.md) — tools you name, with scoped bearer tokens |
| An API on top of the session | [`naf/auth`](../auth.md) — `auth()->requirePermission()` in each method |

Rolling your own bearer check is the one to avoid. It is a short piece of code and a long list
of things to get right — constant-time comparison, hashing at rest, expiry, revocation — all of
which the packages above already did.

## Errors you did not plan for

An uncaught exception on an API route renders through the framework's error handling, which is
built for pages. Decide what your endpoints should say in that case and handle it in one place
rather than per method — [Errors and aborting](../errors.md) is where that lives.
