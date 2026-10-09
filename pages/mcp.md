---
title: MCP tools
requires:
  - naf/mcp
---

# MCP tools

`naf/mcp` exposes explicitly registered tools over a JSON-RPC HTTP endpoint. Tools are PHP
classes with input schemas and handlers. Bearer tokens and tool scopes control access;
handlers must still authorize the application data and operations they expose.

Start from a bootstrapped application. The default token store uses a file, not a database.
The example below measures files in one application-owned reports directory.

## The endpoint

Installing the plugin adds one route, under two methods:

| Route | Behavior |
| --- | --- |
| `POST /mcp` | Authenticated JSON-RPC requests and responses |
| `GET /mcp` | returns 405 with `Allow: POST` after authentication; server-initiated streaming is not implemented |

Configure clients with the `/mcp` URL and a token created below.
Missing or invalid credentials produce 401 at the MCP authenticator. If Form is installed,
a POST without a Bearer header can fail its CSRF check first with 400. A Bearer header skips
that check, but still has to authenticate at MCP.

## A tool

Create the reports directory from the project root:

```bash
mkdir -p storage/reports
```

Create this tool file. Its handler accepts only the reports identifier and rejects unknown
arguments. Keep the directory application-owned and
perform account-specific access checks when adapting this example to private data.

```php title="app/Mcp/GetFolderSize.php"
<?php

declare(strict_types=1);

namespace App\Mcp;

use Naf\MCP\Support\Schema;
use Naf\MCP\Tools\ToolInterface;
use Naf\MCP\Tools\ScopedToolInterface;
use function Naf\log;

final class GetFolderSize implements ToolInterface, ScopedToolInterface
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
            ->prop('folder', Schema::string()->enum(['reports'])->description('Application folder identifier'))
            ->required('folder')
            ->toArray();
    }

    public function requiredScopes(): array
    {
        return ['folders:read'];
    }

    public function handle(array $args): mixed
    {
        if (($args['folder'] ?? null) !== 'reports' || array_diff(array_keys($args), ['folder']) !== []) {
            throw new \InvalidArgumentException('Expected only folder=reports.');
        }

        $path = BASE_PATH . '/storage/reports';
        if (!is_dir($path)) {
            throw new \RuntimeException('Reports directory is unavailable.');
        }
        $bytes = 0;

        try {
            $it = new \RecursiveIteratorIterator(
                new \RecursiveDirectoryIterator($path, \FilesystemIterator::SKIP_DOTS)
            );

            foreach ($it as $file) {
                if (!$file->isLink() && $file->isFile()) {
                    $bytes += $file->getSize();
                }
            }
        } catch (\RuntimeException $error) {
            log()->error('Reports tool failed: ' . $error->getMessage());
            throw new \RuntimeException('Unable to read reports.');
        }

        return ['folder' => 'reports', 'bytes' => $bytes];
    }
}
```

Tool and property descriptions are sent to clients. Describe the operation, accepted input
and relevant limits so an assistant can select it correctly.

`Schema` builds the JSON Schema without writing it by hand — `object()`, `string()`,
`integer()`, `boolean()` and `array(Schema $items)` to start one, then `prop()`, `required()`,
`nullable()`, `enum()`, `min()`, `max()`, `default()`, `description()` and
`additionalProperties()`. Finish with `toArray()`.

Use `additionalProperties(false)` to describe a closed argument object. The published plugin
advertises schemas but does not validate tool arguments against them. Validate types, allowed
values and extra fields in `handle()`, as above; clients can ignore the schema.

## Registering it

Register the tool in root `bootstrap.php`, after autoloading and before `app()->run()`:

```php-inline
use function Naf\MCP\tool;

tool()->register(new App\Mcp\GetFolderSize());
```

Tools are not discovered by directory scanning. Registration order determines list order;
a repeated `name()` replaces the previous registration. Use unique tool names.

## What comes back

Whatever `handle()` returns is encoded as pretty-printed JSON and delivered as a text block —
return an array for structured application results.

```json
{
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\n    \"folder\": \"reports\",\n    \"bytes\": 14\n}"
      }
    ],
    "isError": false
  }
}
```

Tool exceptions are logged and returned with `isError: true`. Their messages are exposed to
clients. Use safe messages for expected failures; catch internal exceptions in the handler,
log diagnostic details and rethrow with a message that omits secrets and private paths.

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
vendor/bin/naf mcp:token:create "Local AI client" --scope "folders:read"
vendor/bin/naf mcp:token:list
vendor/bin/naf mcp:token:revoke tok_...
```

Note the two prefixes. The secret a client sends starts with `mcp_` and is shown **once**, at
creation; the id you revoke by starts with `tok_` and is what `list` prints. Losing the secret
requires issuing a replacement token.

From application code:

```php-inline
use function Naf\MCP\tokens;

$created = tokens()->create('Local AI client', ['folders:read']);

echo $created->plainToken;      // mcp_… — shown once, only the hash is kept
echo $created->record->id;      // tok_… — what you revoke by
```

For an isolated local endpoint, authentication can be disabled in `app/config.php`:

```php-inline
return ['mcp' => ['auth' => ['enabled' => false]]];
```

This allows every caller that can reach the endpoint to invoke every registered tool,
including scoped tools. Keep authentication enabled for publicly reachable endpoints.

### Scopes

A token carries scopes; a tool can demand them by implementing `ScopedToolInterface` alongside
`ToolInterface`:

```php-inline
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
prefix wildcard like `articles:*`. A scoped tool requires at least one of its declared scopes.
If a token matches none, the tool is omitted from `tools/list` and direct calls are rejected.
Enforce stricter combinations inside the handler when an operation requires several grants.

## What a client sees

A client connects and asks what this server is:

```json
{ "jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {} }
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
        "inputSchema": {
          "type": "object",
          "properties": { "folder": { "type": "string", "enum": ["reports"] } },
          "required": ["folder"],
          "additionalProperties": false
        }
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
    "arguments": { "folder": "reports" }
  }
}
```

## Grouping behaviours in one tool

A tool may take an `action` argument and branch on it:

```php-inline
->prop('action', Schema::string()->enum(['analyze', 'summary', 'details']))
```

This keeps related operations together instead of spreading five near-identical tools across
the list a model has to choose from. Use `enum()` when you do it: the alternatives then travel
in the schema, and the model picks from them rather than guessing a verb.

## Files a tool needs

`FilesystemStore` provides local file operations relative to an application-owned root. It
rejects textual `..` traversal and unsupported path characters, and caps each write at
5,000,000 bytes by default:

```php-inline
use Naf\MCP\Support\FilesystemStore;

$store = new FilesystemStore(BASE_PATH . '/storage/mcp/tools', maxBytes: 1_000_000);

$store->write('folder-size/cache.json', $json);
$entry = $store->read('folder-size/cache.json');
```

Construct it explicitly; there is no default root or container binding. Methods return arrays:

| Method | Result and failures |
|---|---|
| `read()` | Path, encoding, content and bytes; throws if the file is missing or unreadable |
| `write()` | Success, path and bytes; throws on an oversized write or write failure |
| `list()` | Entries with path/type and file sizes; throws for a non-directory |
| `delete()` | Success, path and whether a file was deleted; a missing file is not an error |

Invalid paths and unsupported encodings throw. The default cap limits each write's bytes,
not total directory size or the resulting size of an appended file.

The store is not itself an MCP tool. Keep its root and parent directories under application
control, without caller-created symlinks. Its path checks are not a filesystem isolation
boundary for hostile local writers. Your tool must authorize operations and validate paths.

## Resources

This plugin implements tools, not MCP resources. It does not register `resources/list`,
`resources/read` or `resources/write`. Add explicit tools for supported application operations.
