---
title: Alexa+ MCP server
requires:
  - naf/alexa
---

# Alexa+ MCP server

`naf/alexa` prepares a NAF MCP endpoint for an Alexa+ add-on. It reuses the existing MCP
transport and tool registry, OAuth authorization server, database migrations and console.
It supplies configuration defaults, separate OAuth client setup, local diagnostics and an
optional Amazon manifest export. Application tools and business rules stay in the host.

Amazon's [QuickStart](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-toolkit-quickstart.html)
uses a US/en-US manifest. Its [CLI setup guide](https://developer.amazon.com/docs/alexaplus/add-ons/set-up-your-development-environment.html)
requires an Alexa developer account and access to Amazon's package registry. Confirm your
account's access before planning deployment. The plugin does not register or publish an add-on
at Amazon. This integration exposes tools and data; MCP Apps visual resources and category SDK
APIs are outside its scope.

## Prepare a host

Start from a working `naf/app` application with PHP 8.3+, `mbstring`, `readline`, PDO and the
PDO driver for your database. This guide requires `naf/alexa` 0.1.0+, `naf/mcp` 0.2.5+ and
`naf/oauth-server` 0.2.4+. Only `public/` is the document root:

```bash
composer require naf/alexa
mkdir -p storage
```

Composer installs `naf/mcp`, `naf/oauth-server`, `naf/database` and `naf/cli`, with their
dependencies. Plugin boot order is automatic on the required framework 0.2.8+. Do not copy
vendor migrations or maintain a separate HTTP dispatcher.

Set these application environment values in `.env` (or the deployment environment):

```ini
PUBLIC_URL=https://tools.example.com
ALEXA_MCP_RESOURCE=https://tools.example.com/mcp
ALEXA_NAME=Example tools
```

Replace the example domain with the host's public HTTPS origin. The canonical resource must
be that exact origin plus `/mcp`, without a trailing slash, query or fragment. This first
profile uses the authorization server in the same host. Keep these URLs stable and ensure
the proxy sends requests to the right application.

In a new minimal host, this is a complete `app/config.php`; extend existing configuration
instead if your application already has a database or authentication settings:

```php title="app/config.php"
<?php

declare(strict_types=1);

return [
    'database' => [
        'driver' => 'sqlite',
        'database' => BASE_PATH . '/storage/alexa.sqlite',
    ],
    'mcp' => ['transport' => ['streaming' => false]],
];
```

The plugin derives its OAuth issuer, MCP resource metadata and expected audience from the
environment values. Authentication uses OAuth and remains enabled. Service discovery uses
`mcp:service`; account linking is disabled until configured. POST responses default to JSON,
which is a Streamable HTTP response mode. Set `mcp:transport:streaming` to `true` for SSE progress
and final results, or `false` to use JSON. See [MCP tools](mcp.md#the-endpoint) for streaming tools,
client Accept headers and proxy buffering.

## Register a public tool

Create `app/Mcp/ServiceStatus.php`:

```php title="app/Mcp/ServiceStatus.php"
<?php

declare(strict_types=1);

namespace App\Mcp;

use Naf\MCP\Tools\ToolInterface;

final class ServiceStatus implements ToolInterface
{
    public function name(): string
    {
        return 'service_status';
    }

    public function description(): string
    {
        return 'Check whether the example service is available. No personal data is returned.';
    }

    public function inputSchema(): array
    {
        return ['type' => 'object', 'properties' => [], 'additionalProperties' => false];
    }

    public function handle(array $args): mixed
    {
        return ['status' => 'available'];
    }
}
```

Add this registration in the application's root `bootstrap.php`, after Composer autoloading
and before `app()->run()`:

```php-inline
use App\Mcp\ServiceStatus;
use function Naf\MCP\tool;

tool()->register(new ServiceStatus());
```

A service token can call this tool because it returns only public information. Implement
personal tools with `UserToolInterface` and `ScopedToolInterface`; never expose personal data
through an unscoped service tool.

## Set up and check

Run from the host root against the configured database:

```bash
vendor/bin/naf alexa:setup --migrate
vendor/bin/naf alexa:doctor --server-only
```

`--migrate` opts into the existing OAuth migration only. It does not run unrelated application
migrations. Omit it when your deployment already applies OAuth migrations through `db:migrate up`.
Setup registers a confidential client limited to `client_credentials`, `mcp:service` and this
MCP audience. It prints the client id and secret once. Store that secret in the Alexa service
authentication settings, not in source control, query strings or the manifest.

Repeated setup reuses a matching registration without rotating its secret or creating another
client. If registration and configuration differ, review the existing registration before
revoking and recreating it. Use `oauth:client:rotate-secret` for a deliberate secret rotation.

Doctor returns exit code 0 when its selected local checks pass, or 1 on failure. It checks
configuration, OAuth tables, discovery capabilities, client separation and tool scopes.
`--server-only` skips the store listing. Doctor without that option also validates the local
listing metadata. These checks do not verify public reachability, hosted image dimensions,
latency, login/consent UX, Amazon account access or certification.

## Verify HTTP

Public discovery documents must return JSON:

```bash
curl https://tools.example.com/.well-known/oauth-protected-resource/mcp
curl https://tools.example.com/.well-known/oauth-authorization-server
```

PRM names `https://tools.example.com/mcp` and the authorization server origin. The authorization
metadata advertises `client_credentials`, authorization code, refresh and `S256`. No signing key
is needed for OAuth-only usage. An unauthenticated MCP request returns 401 without a
`WWW-Authenticate` header, as required by the Alexa Toolkit.

Use a service token from `/oauth/token` with HTTP Basic client authentication and form fields
`grant_type=client_credentials`, `scope=mcp:service`, `resource=https://tools.example.com/mcp`.
It has no refresh token; request a new one on expiry. Send the bearer in the Authorization
header on every MCP request, with both accepted response media types:

```http
POST /mcp HTTP/1.1
Authorization: Bearer YOUR_SERVICE_ACCESS_TOKEN
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"Example test","version":"1.0"}}}
```

Send the negotiated `MCP-Protocol-Version` header on subsequent requests. Send
`notifications/initialized`, then `tools/list` and `tools/call` for `service_status`.
The result contains `structuredContent: {"status":"available"}` and a JSON text content block.
The server supports the documented 2025-03-26 client lifecycle as well as 2025-11-25.

## Add account linking

For personal tools, use your application's existing `naf/auth` provider and login page.
Obtain the exact HTTPS callback URIs from Amazon's account-linking setup; do not guess them.
Extend the host configuration with:

```php-inline
'oauth_server' => ['login_route' => '/login'],
'alexa' => [
    'account_linking' => true,
    'redirect_uris' => ['https://AMAZON_SUPPLIED_HOST/EXACT_CALLBACK'],
    'user_scopes' => ['mcp:tools'],
],
```

The default `mcp:tools` scope requires the current account's `mcp:tools` permission. Grant that
through your existing identity/provider, or define narrower application scopes and permissions
in `oauth_server:scopes`. If changing the user scope list, also set the same list in
`mcp:oauth:scopes_supported`; numeric configuration arrays merge by position.

Run setup again. It adds a second confidential client limited to authorization code and refresh
grants, exact callback URIs, user scopes and this audience. It never gives that client the
service grant. Configure this separate client in Amazon's account-linking settings.

A personal tool declares its user scope. Inside its handler, obtain the token's user:

```php-inline
use function Naf\OAuth\Server\token;

$account = token()->user();
// Pass this verified account to your existing application service.
```

Do not read the browser session as the Alexa caller. The OAuth resource server reloads the
token's account and rechecks current permissions. Service discovery can list personal tool
metadata, but invoking one without a linked account returns HTTP 401. A linked account lacking
the required scope/permission receives 403. Authorization code exchange requires PKCE S256;
the requested resource is checked against the code's authorized audience. Refresh keeps that
audience without requiring the resource parameter again.

## Prepare the Amazon package

Install and configure Amazon's Alexa AI CLI through the setup guide linked above. Generate
its project with `alexa-ai new mcp` and your MCP URL. The
[CLI reference](https://developer.amazon.com/docs/alexaplus/add-ons/alexa-ai-cli-reference.html)
documents `--name` and `--mcp-server-url`; check `alexa-ai new mcp --help` for the options in
your installed version.

Supply `alexa:listing` in host configuration using the en-US locale entry from the
[QuickStart's `addon.json` schema](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-toolkit-quickstart.html#addonjson-schema-reference).
The plugin's export validates:

| Field | Requirement |
| --- | --- |
| `name.value` | 1–30 characters |
| `shortDescription`, `fullDescription` | 1–123 and 1–4000 characters |
| `examplePhrases` | 3–4 nonempty phrases, each at most 200 characters |
| `privacyAndCompliance` URLs | HTTPS privacy policy and terms of use |
| `mediaAssets.icons.light` | Exactly 64, 72, 88, 126, 180 and 241 pixel square entries |
| `mediaAssets.icons.dark` | Optional; the same six sizes when supplied |
| `mediaAssets.carouselImages` | At least one 600x900 image with alt text |
| `mediaAssets.bannerImages` | Optional 1200x600 images with alt text |

Use `{size, uri}` objects for icons and `{size, uri, altText}` objects for other images.
Image URIs use HTTPS and PNG, JPG, JPEG or WEBP paths. Alt text is at most 250 characters.
The validator checks declared metadata, not remote image bytes or ownership.

Export to a new file and review it alongside the CLI-generated package:

```bash
vendor/bin/naf alexa:setup --manifest storage/alexa-addon.json
vendor/bin/naf alexa:doctor
```

The file uses manifest version 1.0, US distribution, the en-US listing and an MCP HTTPS
integration pointing at the canonical resource. It contains no OAuth credentials. Setup
refuses to overwrite an existing file. Transfer the reviewed metadata into the CLI project's
`addon-package/addon.json` before deployment. Credentials are configured separately through
the CLI's service-authentication and account-linking flows.

Use `alexa-ai deploy` to create/update the development add-on, test it in the simulator, and
submit only after the required testing and account review. Re-deploy after tool/schema changes:
Amazon refreshes its tool inventory on deployment. Verify the public response latency and
SSE flushing through the actual proxy; the QuickStart specifies a round trip below 500 ms.

## If the result is different

- **400, 406 or 415 before MCP handles a call:** check Content-Type, Accept, protocol version and that
  `csrf_exempt_routes:mcp_server_rpc` has not been disabled by host configuration.
- **401 with a service token on a personal tool:** account linking is needed; keep the service
  and user clients separate.
- **403 after linking:** check the token's user scopes and the reloaded account's permissions.
- **`invalid_grant` on code exchange:** check PKCE verifier, exact callback and canonical
  resource. A code attempted with mismatched bindings is spent; start authorization again.
- **Buffered SSE:** inspect reverse-proxy/CDN buffering and compression; verify that the
  supported framework emitter is installed.
- **Doctor passes but Amazon fails:** verify public HTTPS/discovery, credentials in the correct
  authentication tier, actual images, simulator login/consent and developer account access.

## Sources

- [Alexa+ MCP QuickStart](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-toolkit-quickstart.html)
- [Alexa+ MCP authentication](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-toolkit-authentication.html)
- [Alexa+ MCP account linking](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-toolkit-account-linking.html)
- [MCP Streamable HTTP](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
