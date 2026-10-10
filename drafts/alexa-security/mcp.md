---
title: MCP tools
requires:
  - naf/mcp
---

<!-- Unpublished draft: wait for naf/oauth-server 0.2.5, naf/mcp 0.2.6 and naf/alexa 0.1.1 on Packagist. -->

# MCP tools

`naf/mcp` exposes explicitly registered tools over a stateless MCP Streamable HTTP endpoint.
Tools are PHP classes with input schemas and handlers. Bearer tokens and tool scopes control access;
handlers must still authorize the application data and operations they expose.

This guide requires `naf/mcp` 0.2.5+, PHP 8.3+ and `naf/framework` 0.2.8+.
Start from a bootstrapped application. The default token store uses a file, not a database.
The example below measures files in one application-owned reports directory.

## The endpoint

The `POST /mcp` endpoint implements stateless Streamable HTTP. Clients send
`Content-Type: application/json` and `Accept: application/json, text/event-stream`.
The default response is JSON. Enable SSE responses in the host's `app/config.php` return array:

```php-inline
'mcp' => ['transport' => ['streaming' => true]],
```

Set `mcp:transport:streaming` back to `false` to return JSON and invoke ordinary `handle()`
methods. Both modes use the same Streamable HTTP endpoint. The setting controls response
streaming, not endpoint installation or authentication. Accepted notifications and client
responses receive an empty HTTP 202. Batches and non-object JSON are rejected. Authenticated
GET requests receive 405 with `Allow: POST`: there is no persistent GET event channel,
session id, replay or resumability support.

Initialize with a `protocolVersion`, `capabilities` object and `clientInfo`:

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"Example client","version":"1.0"}}}
```

The server negotiates 2025-11-25, 2025-06-18 and 2025-03-26. Send the negotiated
`MCP-Protocol-Version` header on later requests. An unsupported supplied version returns
400. A supplied `Origin` must match the configured `public_url` origin or an exact entry in
`mcp:transport:allowed_origins` (list of origin strings, default `[]`); otherwise it returns
403. Without either configuration, supplied Origins are rejected; the caller's Host header
does not establish a trusted origin. An absent Origin is accepted for non-browser clients. Bind local development servers
to loopback; use a configured public HTTPS origin in production.

`StreamingToolInterface` extends the ordinary tool contract with `stream(array $args): Generator`.
Keep a working `handle()` method for JSON mode. Yield `Progress` values and return the final result:

```php-inline
use Naf\MCP\Support\Progress;
use Naf\MCP\Tools\StreamingToolInterface;

// Add this method to a tool implementing StreamingToolInterface.
public function stream(array $args): \Generator
{
    yield new Progress(0, 1, 'Reading the report');
    $result = $this->handle($args);
    yield new Progress(1, 1, 'Report ready');
    return $result;
}
```

Progress values must be finite, non-negative and strictly increase. An optional total cannot
be smaller than progress. Notifications are sent only when the caller supplies a string or
integer `params._meta.progressToken`. The final JSON-RPC result follows on the same SSE stream.
The PSR-7 body reads lazily and the framework emitter sends each message as it becomes available.
The plugin sends `X-Accel-Buffering: no` and `Cache-Control: no-cache, no-transform`.
Verify proxy/CDN buffering and compression on the deployed host; PHP's local emitter alone
does not prove Internet latency.

MCP 0.2.5 supplies its own narrow `csrf_exempt_routes:mcp_server_rpc` exemption when
`naf/form` is installed. Keep MCP authentication enabled. A Bearer header alone does not
exempt a request from Form's CSRF listener. Older MCP installations with Form 0.2.3+ need
that exact route exemption in host configuration; it can be removed after upgrading.

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

Input schemas are enforced before handlers run. Empty schemas normalize to a closed object;
object schemas default to `additionalProperties: false`. Explicitly allow extra keys when
needed. Invalid arguments return JSON-RPC `-32602`. Keep domain validation and data access
checks in `handle()`; schema validation cannot decide which records a caller may access.

## Registering it

Register the tool in root `bootstrap.php`, after autoloading and before `app()->run()`:

```php-inline
use function Naf\MCP\tool;

tool()->register(new App\Mcp\GetFolderSize());
```

Tools are not discovered by directory scanning. Registration order determines list order;
a repeated `name()` replaces the previous registration. Use unique tool names.

## What comes back

Returning `Naf\MCP\Support\ToolResult::text()` or another valid MCP result preserves its content blocks.
Associative arrays and objects also populate `structuredContent`, with a JSON text block for
compatibility. Lists remain JSON text. Optional `ToolMetadataInterface::metadata()` can provide
`title`, `annotations`, `outputSchema` and `_meta`; core name, description and input schema
come from the tool contract. A declared output schema is validated against structured content.
Handler failures and invalid output are logged and return `isError: true` with the generic
message `The tool could not complete the request.` Internal exception messages are no longer
exposed to callers.

For the folder example, a successful result includes both representations:

```json
{
  "result": {
    "content": [{"type": "text", "text": "{\n    \"folder\": \"reports\",\n    \"bytes\": 14\n}"}],
    "structuredContent": {"folder": "reports", "bytes": 14},
    "isError": false
  }
}
```

## Tokens

The default `mcp:auth:driver` is `file`. The endpoint wants a Bearer token:

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

With the default File-Token driver, three patterns are understood: `*` for everything, an exact scope like `articles:read`, and a
prefix wildcard like `articles:*`. A scoped tool requires at least one of its declared scopes.
If a token matches none, the tool is omitted from `tools/list` and direct calls return HTTP 403.
Enforce stricter combinations inside the handler when an operation requires several grants.

## What a client sees

Initialize using the request above, then send `notifications/initialized` without an `id`.
The notification receives HTTP 202. The initialize response announces tools capability and
the negotiated protocol version; tool definitions follow in `tools/list`. Send
`MCP-Protocol-Version` with that version on subsequent requests and keep both Accept media types.

Request the tools themselves to receive the definitions this token may see:

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

## OAuth authentication and personal tools

Install `naf/oauth-server` and configure its database, scopes, public URL and canonical audience.
Set these fragments in the host configuration, replacing the example URLs:

```php-inline
'public_url' => 'https://tools.example.com',
'oauth_server' => [
    'name' => 'Example tools',
    'audience' => 'https://tools.example.com/mcp',
    'scopes' => ['account:read' => ['label' => 'Read your account', 'permission' => 'account.read']],
],
'mcp' => [
    'auth' => ['enabled' => true, 'driver' => 'oauth'],
    'oauth' => [
        'resource' => 'https://tools.example.com/mcp',
        'authorization_servers' => ['https://tools.example.com'],
        'scopes_supported' => ['account:read'],
    ],
],
```

`mcp:auth:driver` defaults to `file`; `oauth` delegates bearer validation to the existing
OAuth ResourceServer. Expired, revoked, wrong-audience and deleted-account tokens fail.
Current user permissions filter the token's usable scopes. A browser session never supplies
a missing bearer identity. PRM is public at `/.well-known/oauth-protected-resource` and
`/.well-known/oauth-protected-resource/mcp`; absent resource/server configuration returns 404.
`naf/oauth-server` 0.2.4 adds the conventional authorization-server metadata route and
resource-bound code exchange needed by Alexa.

Personal tools implement `UserToolInterface` in addition to the ordinary tool/scoped contracts.
Calling one without a linked user returns HTTP 401; a linked user missing the required scopes
receives 403. Neither response includes `WWW-Authenticate`, matching the Alexa requirement.
Get the authenticated user through `Naf\OAuth\Server\token()->user()`, not `auth()`'s browser
session. OAuth scope names are matched literally: `*` and `notes:*` do not grant any other
scope. The File-Token driver's documented wildcards remain available. A tool's scope list
keeps its any-of semantics for both drivers; marking a tool with `UserToolInterface` is an
additional linked-user requirement, not another scope alternative.

The optional `mcp:auth:discovery_scope` (default `null`) lets an unlinked service identity
with that scope see tool definitions, including personal tools. It does not grant execution.
Use separate service and account-linking clients and never give a service registration user
scopes. [Alexa+](alexa.md) supplies this profile and its setup checks.

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

## Request sizes and execution limits

MCP 0.2.6+ limits the JSON request body to 1 MiB before decoding. Set
`mcp:transport:max_request_bytes` to a positive integer in bytes below `PHP_INT_MAX`:

```php-inline
// In the array returned by app/config.php:
'mcp' => ['transport' => ['max_request_bytes' => 262144]],
```

A request exceeding the limit receives HTTP 413. The limit also applies without
`Content-Length`, and the controller reads at most the limit plus one byte before deciding.
It bounds the controller's input buffer; decoded objects, schemas and tool results consume
additional memory. Configure request limits at the proxy and PHP layer too, before PHP
accepts and parses input.

Streaming does not impose an application execution deadline. Bound work in the tool's
service, set PHP worker timeouts, and limit concurrent requests at the proxy. Verify progress
flushing and disconnect behavior through that deployed proxy. See the [Alexa deployment
checks](alexa.md#deployment-checks) for the authentication and streaming boundary.

## Resources

This plugin implements tools, not MCP resources. It does not register `resources/list`,
`resources/read` or `resources/write`. Add explicit tools for supported application operations.

The [MCP Streamable HTTP specification](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) describes the client transport contract.
