---
title: MCP tools
requires:
  - naf/mcp
---

# MCP tools

An AI client — Claude, ChatGPT, an editor plugin — can call into your application, but only
through things you wrote and named. This plugin speaks the Model Context Protocol over one
route and offers whatever tools you registered. Nothing else is reachable: there is no generic
query endpoint, no table browser, no "run this SQL". A tool is a PHP class, and the only things
a model can do are the ones you gave it.

Tokens are files, so a plugin you install to let an agent read two counters does not cost you a
database table.

## The endpoint

Installing the plugin adds one route, under two methods:

| | |
| --- | --- |
| `POST /mcp` | the JSON-RPC endpoint — everything happens here |
| `GET /mcp` | returns 405 with `Allow: POST` after authentication; server-initiated streaming is not implemented |

That URL is what you hand a client. Everything below is what travels over it.

## A tool

Four methods: what it is called, what it is for, what it takes, and what it does.

```php
namespace App\Mcp;

use Naf\MCP\Support\Schema;
use Naf\MCP\Tools\ToolInterface;

final class GetFolderSize implements ToolInterface
{
    public function name(): string
    {
        return 'get_folder_size';
    }

    public function description(): string
    {
        return 'Returns the size of a folder.';
    }

    public function inputSchema(): array
    {
        return Schema::object()
            ->description($this->description())
            ->additionalProperties(false)
            ->prop('path', Schema::string()->description('Relative folder path'))
            ->required('path')
            ->toArray();
    }

    public function handle(array $args): mixed
    {
        $path  = (string) $args['path'];
        $bytes = 0;

        $it = new \RecursiveIteratorIterator(
            new \RecursiveDirectoryIterator($path, \FilesystemIterator::SKIP_DOTS)
        );

        foreach ($it as $file) {
            $bytes += $file->getSize();
        }

        return ['path' => $path, 'bytes' => $bytes, 'human' => round($bytes / 1024 / 1024, 1) . ' MB'];
    }
}
```

`description()` is not a comment. It is the sentence the model reads when it decides whether
this tool is the one for the job, and so is every `->description()` on a property. A tool
nobody can tell apart from another one gets called wrongly.

`Schema` builds the JSON Schema without writing it by hand — `object()`, `string()`,
`integer()`, `boolean()` and `array(Schema $items)` to start one, then `prop()`, `required()`,
`nullable()`, `enum()`, `min()`, `max()`, `default()`, `description()` and
`additionalProperties()`. Finish with `toArray()`.

**Say `additionalProperties(false)`.** Without it a model that invents an argument gets no
correction, and the call arrives looking valid.

## Registering it

A tool the registry has never seen does not exist. Register it in your `bootstrap.php`:

```php
use function Naf\MCP\tool;

tool()->register(new App\Mcp\GetFolderSize());
```

Nothing scans a directory for tools. What is registered is what `tools/list` answers with, in
the order it was registered. The registry is keyed by `name()`, so a second tool claiming a name
that is taken replaces the first without a word — worth knowing when two of them come from
different packages.

## What comes back

Whatever `handle()` returns is encoded as pretty-printed JSON and delivered as a text block —
return an array and you are done.

```json
{
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\n  \"path\": \"var/log\",\n  \"bytes\": 25500000,\n  \"human\": \"25.5 MB\"\n}"
      }
    ],
    "isError": false
  }
}
```

Throwing is how a tool reports failure. The exception is caught, logged, and returned as a
result with `isError` set — which means **its message is handed to the client**. Throw sentences
you would be happy to show a stranger, and let unexpected failures carry a message you wrote
rather than a stack of internals.

## Tokens

The endpoint wants a Bearer token:

```http
Authorization: Bearer mcp_...
```

Tokens live in `storage/mcp/tokens.json` — set `MCP_TOKEN_FILE` in the environment, or
`mcp:auth:token_file` in the configuration, to keep them somewhere else. Only a hash is stored,
so a stolen file is not a set of working tokens.

With `naf/cli` installed the plugin registers three commands:

```bash
vendor/bin/naf mcp:token:create "Local AI client" --scope "*"
vendor/bin/naf mcp:token:list
vendor/bin/naf mcp:token:revoke tok_...
```

Note the two prefixes. The secret a client sends starts with `mcp_` and is shown **once**, at
creation; the id you revoke by starts with `tok_` and is what `list` prints. Losing the secret
means issuing a new token, which is the point.

From application code:

```php
use function Naf\MCP\tokens;

$created = tokens()->create('Local AI client', ['*']);

echo $created->plainToken;      // mcp_… — shown once, only the hash is kept
echo $created->record->id;      // tok_… — what you revoke by
```

On a local-only project you can turn the whole check off, deliberately:

```php
return ['mcp' => ['auth' => ['enabled' => false]]];
```

That opens the endpoint to anything that can reach the URL. It belongs on a laptop, not on a
host with a public address.

### Scopes

A token carries scopes; a tool can demand them by implementing `ScopedToolInterface` alongside
`ToolInterface`:

```php
use Naf\MCP\Tools\ScopedToolInterface;

final class ArticleSearchTool implements ToolInterface, ScopedToolInterface
{
    public function requiredScopes(): array
    {
        return ['articles:read'];
    }

    // …the four ToolInterface methods
}
```

Three patterns are understood: `*` for everything, an exact scope like `articles:read`, and a
prefix wildcard like `articles:*`. A tool whose scopes a token does not hold is not merely
refused — it is left out of `tools/list` entirely, so a model never learns it exists.

## What a client sees

A client connects and asks what this server is:

```json
{ "jsonrpc": "2.0", "method": "initialize", "params": {} }
```

The answer announces capabilities, not tools:

```json
{
  "result": {
    "protocolVersion": "2025-06-18",
    "capabilities": { "tools": {} },
    "serverInfo": { "name": "naf-mcp", "version": "0.1.0" }
  }
}
```

Then it asks for the tools themselves, and gets back exactly what its token may see:

```json
{ "jsonrpc": "2.0", "id": 1, "method": "tools/list" }
```

```json
{
  "result": {
    "tools": [
      {
        "name": "get_folder_size",
        "description": "Returns the size of a folder.",
        "inputSchema": { "… JSON Schema …" }
      }
    ]
  }
}
```

And calls one:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "get_folder_size",
    "arguments": { "path": "var/log" }
  }
}
```

## Grouping behaviours in one tool

A tool may take an `action` argument and branch on it:

```php
->prop('action', Schema::string()->enum(['analyze', 'summary', 'details']))
```

This keeps related operations together instead of spreading five near-identical tools across
the list a model has to choose from. Use `enum()` when you do it: the alternatives then travel
in the schema, and the model picks from them rather than guessing a verb.

## Files a tool needs

`FilesystemStore` is a sandbox for tools that have to keep something on disk — a cache, a
scratch file. It resolves every path inside one root, refuses anything that escapes it through
`..`, and caps what a single write may be (5 MB unless you say otherwise):

```php
use Naf\MCP\Support\FilesystemStore;

$store = new FilesystemStore(BASE_PATH . '/storage/mcp/tools', maxBytes: 1_000_000);

$store->write('folder-size/cache.json', $json);
$entry = $store->read('folder-size/cache.json');
```

It is yours to construct — nothing registers one for you, and there is no default root. Its
`read()`, `write()`, `list()` and `delete()` all answer arrays describing what happened, and
they throw on a missing file, an oversized write or a path that points outside the root.

It is not reachable over MCP. A model cannot read or write a file through it; only your tool
can, at the paths your tool chose.

## Resources

This plugin implements tools, and not the resource half of MCP — no `resources/list`,
`resources/read` or `resources/write`. Tools cover what most clients actually use, and a
resource surface is a second way to expose data that would need its own permission story.
It may come later; nothing here changes when it does.
