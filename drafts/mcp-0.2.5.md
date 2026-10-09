# MCP 0.2.5: Streamable HTTP and OAuth

Publication gate: wait for `naf/mcp` 0.2.5 on Packagist, then reconcile this draft into
`pages/mcp.md`. The published page must continue describing 0.2.4 until then.
Requires PHP 8.3+, `naf/framework` 0.2.8+ and the installed PDO driver when using OAuth.

## Transport settings

The existing `POST /mcp` endpoint implements stateless Streamable HTTP. Clients send
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
use Naf\MCP\Support\ToolResult;

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
The PSR-7 body reads lazily; the existing framework emitter and response-body event flush each
message. The plugin sends `X-Accel-Buffering: no` and `Cache-Control: no-cache, no-transform`.
Verify proxy/CDN buffering and compression on the deployed host; PHP's local emitter alone
does not prove Internet latency.

## Validation and results

Input schemas are enforced before calling handlers, using standard JSON Schema validation.
Empty schemas normalize to a closed object. Existing object schemas default to
`additionalProperties: false`. Use explicit allowances where tools accept extra keys;
previously tolerated arguments can now return JSON-RPC `-32602`. Keep domain validation
and data authorization in handlers.

Returning `ToolResult::text()` or another valid MCP result now preserves its content blocks.
Associative arrays and objects also populate `structuredContent`, with a JSON text block for
compatibility. Lists remain JSON text. Optional `ToolMetadataInterface::metadata()` can provide
`title`, `annotations`, `outputSchema` and `_meta`; core name, description and input schema
come from the tool contract. A declared output schema is validated against structured content.
Handler failures and invalid output are logged and return `isError: true` with the generic
message `The tool could not complete the request.` Internal exception messages are no longer
exposed to callers.

## OAuth integration

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
session. Scope matching otherwise retains the existing any-of and wildcard semantics.

The optional `mcp:auth:discovery_scope` (default `null`) lets an unlinked service identity
with that scope see tool definitions, including personal tools. It does not grant execution.
Use separate service and account-linking clients and never give a service registration user
scopes. `naf/alexa` supplies this profile and its setup checks.

The MCP POST route now contributes its own narrow CSRF exemption. Authentication remains
enabled. Removing a manual host exemption is safe only after this version is installed.

Source: [MCP Streamable HTTP specification](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports).
