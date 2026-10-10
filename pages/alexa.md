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

The example exposes one public `service_status` tool, authenticated with a service token.
It needs no customer account linking. The NAF setup and HTTP exchange are tested against
published packages by this documentation's example runner.

Amazon's [MCP Toolkit overview](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-toolkit-overview.html)
currently lists availability in the United States. Amazon registration requires access to
private developer tooling and a confirmed way to provision the service credentials. Read
[Connect to Alexa+](#connect-to-alexa) before planning deployment: the public Amazon docs
leave the service-secret provisioning step unspecified, so this guide cannot yet establish
an end-to-end Alexa connection. The plugin does not register or publish an add-on at Amazon.
This integration exposes tools and data; MCP Apps visual resources and category SDK APIs
are outside its scope.

## Prepare a host

Use PHP 8.3+, `mbstring`, `readline`, PDO and `pdo_sqlite` for this example. This guide
requires `naf/alexa` 0.1.0+, `naf/mcp` 0.2.5+ and `naf/oauth-server` 0.2.4+.
Create a host application; only its `public/` directory is the document root:

```bash
composer create-project naf/app alexa-demo
cd alexa-demo
composer require naf/alexa
mkdir -p storage
```

For an existing application, run the last two commands from its root instead.

Composer installs `naf/mcp`, `naf/oauth-server`, `naf/database` and `naf/cli`, with their
dependencies. Plugin boot order is automatic on the required framework 0.2.8+. Do not copy
vendor migrations or maintain a separate HTTP dispatcher.

Set these application environment values in `.env` (or the deployment environment).
If `.env.local` exists, set them there because that file replaces `.env`:

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

For this new application, replace root `bootstrap.php` with this complete file.
In an existing host, add the imports and tool registration after Composer autoloading and
before `app()->run()`, preserving its other registrations:

```php title="bootstrap.php"
<?php

declare(strict_types=1);

use App\Mcp\ServiceStatus;

use function Naf\app;
use function Naf\MCP\tool;

define('BASE_PATH', __DIR__);

require __DIR__ . '/vendor/autoload.php';

tool()->register(new ServiceStatus());

app()->run();
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
MCP audience. It prints the client id and secret once. Keep them in private credential storage
for [Amazon service authentication](#provision-the-service-client-at-amazon). Setup does not
send them to Amazon. Keep the secret out of source control, query strings and the manifest.

Repeated setup reuses a matching registration without rotating its secret or creating another
client. If registration and configuration differ, review the existing registration before
revoking and recreating it. Use `oauth:client:rotate-secret` for a deliberate secret rotation.

Doctor runs local diagnostics and exits; it does not start or stop an HTTP server.
It returns exit code 0 when its selected local checks pass, or 1 on failure. It checks
configuration, OAuth tables, discovery capabilities, client separation and tool scopes.
`--server-only` limits the checks to server configuration and skips the store listing.
Doctor without that option also validates the local
listing metadata. These checks do not verify public reachability, hosted image dimensions,
latency, login/consent UX, Amazon account access or certification.

## Verify HTTP

For local protocol checks, pass the existing web entry point as the development server's
router. PHP 8.3 otherwise treats some `/.well-known/` paths as missing static files:

```bash
php -S 127.0.0.1:8000 -t public public/index.php
```

Leave this terminal running and stop it with Ctrl+C. To connect Alexa, expose the application
through a public HTTPS host or tunnel and use that origin in both environment values above.
Restart the development server if you change the environment values. A local HTTP check alone
does not establish public reachability.

For public hosting, route these paths through the NAF front controller as described in
[Deployment](deployment.md#web-server-routing).

Public discovery documents must return JSON:

```bash
curl https://tools.example.com/.well-known/oauth-protected-resource/mcp
curl https://tools.example.com/.well-known/oauth-protected-resource
curl https://tools.example.com/.well-known/oauth-authorization-server
```

PRM names `https://tools.example.com/mcp` and the authorization server origin. The authorization
metadata advertises `client_credentials`, authorization code, refresh and `S256`. No signing key
is needed for OAuth-only usage. An unauthenticated MCP request returns 401 without a
`WWW-Authenticate` header, as required by the Alexa Toolkit.

Verify the service credentials independently of Amazon. Replace the client id below with
the service id from setup. Curl prompts for its secret as the HTTP Basic password:

```bash
ALEXA_SERVICE_CLIENT_ID='YOUR_SERVICE_CLIENT_ID'
curl --fail-with-body \
  --user "$ALEXA_SERVICE_CLIENT_ID" \
  --data-urlencode 'grant_type=client_credentials' \
  --data-urlencode 'scope=mcp:service' \
  --data-urlencode 'resource=https://tools.example.com/mcp' \
  'https://tools.example.com/oauth/token'
```

Expect an access token with `token_type: "Bearer"`, `scope: "mcp:service"` and no refresh
token. Treat the returned access token as a credential too. Request another service token
on expiry. Send the bearer in the Authorization header on every MCP request, with both
accepted response media types:

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

## Connect to Alexa+

Follow these steps after the public discovery and service-token checks pass. A successful
local exchange proves the NAF endpoint works; Amazon credential provisioning and simulator
testing remain separate steps.

### Obtain Amazon tooling access

Complete Amazon's [development-environment setup](https://developer.amazon.com/docs/alexaplus/add-ons/set-up-your-development-environment.html).
It requires Node.js 24+, an Alexa developer account and an AWS account admitted to Amazon's
developer-tools role. The CLI is distributed through Amazon's private CodeArtifact registry;
`npm install -g @alexa-ai/cli` requires that registry setup first. Contact your Amazon
onboarding representative if your account has not been granted access. Hosting this PHP
application on AWS is not required.

After the documented installation, check the installed CLI and authenticate:

```bash
alexa-ai --version
alexa-ai new mcp --help
alexa-ai configure
```

`configure` signs the developer into Amazon through Login with Amazon. It does not install
the NAF service client's credentials. Keep these identities separate:

| Credentials | Purpose | Configured by |
| --- | --- | --- |
| Amazon developer login | Manage add-ons at Amazon | `alexa-ai configure` |
| NAF service client | MCP discovery and public tools using `mcp:service` | `alexa:setup`, then Amazon service provisioning below |
| Optional NAF account-linking client | Act for a customer using user scopes | Separate setup under [Add account linking](#add-account-linking) |

### Create the add-on project

Run this in a directory for your Amazon add-on projects, separate from the PHP application.
Replace the URL and service client id:

```bash
alexa-ai new mcp \
  --name "NAF Demo" \
  --locale en-US \
  --mcp-server-url "https://tools.example.com/mcp" \
  --requires-auth \
  --auth-client-id "YOUR_SERVICE_CLIENT_ID" \
  --auth-scopes "mcp:service"
```

The [CLI reference](https://developer.amazon.com/docs/alexaplus/add-ons/alexa-ai-cli-reference.html)
documents these options. Check them against the installed version's help. This command
creates local files; it does not register credentials with Amazon. If asked about customer
account linking, leave it disabled for the public status tool.

Change into the generated project directory reported by the CLI. Complete its
`addon-package/addon.json` with descriptions, three or four example phrases, privacy and
terms URLs, and the required images. See [Prepare the Amazon package](#prepare-the-amazon-package)
for the listing fields and optional NAF export. Keep all OAuth secrets outside this package.

### Provision the service client at Amazon

Amazon's [authentication guide](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-toolkit-authentication.html)
requires Alexa to obtain a service token with these settings:

| Setting | Value for this host |
| --- | --- |
| MCP endpoint / canonical resource | `https://tools.example.com/mcp` |
| Authorization server | `https://tools.example.com` |
| Token endpoint | `https://tools.example.com/oauth/token` |
| Grant type | `client_credentials` |
| Client authentication | HTTP Basic with the service client id and secret from `alexa:setup` |
| Scope | `mcp:service` |
| Token-request `resource` | `https://tools.example.com/mcp` |

**Amazon provisioning is not yet verified.** As of 2026-10-10, the public authentication
guide describes the token exchange, but neither the CLI reference nor the
[Add-on API reference](https://developer.amazon.com/docs/alexaplus/add-ons/alexa-plus-addon-api-reference.html)
identifies a service-secret upload command, API operation or console field. The private CLI
was not available for verification. There is therefore no confirmed secret-entry instruction
in this guide yet; the `new mcp` command above is not sufficient to connect this protected host.

Ask your assigned Alexa+ Solutions Architect for the service-credential provisioning
procedure through [Amazon developer support](https://developer.amazon.com/docs/alexaplus/add-ons/get-support-from-amazon.html).
Provide the settings above and your CLI version, without including the secret. A specific
question to resolve is:

> How do I provision a confidential OAuth client for Tier 1 MCP service authentication?
> Which supported CLI command, API operation or Developer Hub field stores its client secret
> for the client_credentials grant, and at which step before the first authenticated deployment?

Use the credential channel Amazon confirms for that purpose. The masked prompt and
`ALEXA_CLIENT_SECRET` documented for `configure-account-linking` belong to the separate user
client; they do not establish a service-secret provisioning mechanism. Keep service and user
clients separate, and keep MCP authentication enabled while resolving this step.

### Deploy and verify the connection

Continue only after Amazon confirms the service credential provisioning and the add-on
listing is complete. From the generated Amazon project directory, run:

```bash
alexa-ai deploy
alexa-ai status
```

Deployment creates or updates the development-stage add-on and reports its add-on id.
Open it in Amazon's [web simulator](https://developer.amazon.com/docs/alexaplus/add-ons/test-with-web-simulator.html)
and ask, for example, "Is the NAF demo service available?" Use your host's request tracing
to verify the token request and a real `service_status` invocation; confirm the reply
reflects `{"status":"available"}`. Keep tracing free of Authorization headers, tokens and
client secrets. A successful deployment status alone does not prove a tool was called.

Re-deploy after tool/schema or authentication metadata changes: Amazon refreshes its cached
configuration on deployment. Test public latency and any SSE flushing through the actual
proxy before certification; the QuickStart specifies a round trip below 500 ms.

## Add account linking

This optional extension is for personal tools, after service authentication works. Use your
application's existing `naf/auth` provider and login page.
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

Amazon's [account-linking guide](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-toolkit-account-linking.html#step-3--configure-account-linking)
documents this command for the user client:

```bash
alexa-ai configure-account-linking \
  --addon-id "YOUR_ADDON_ID" \
  --stage development \
  --client-id "YOUR_ACCOUNT_LINKING_CLIENT_ID"
```

Enter the **account-linking client's** secret at the masked prompt. That guide also documents
`ALEXA_CLIENT_SECRET` as an alternative for this user-client configuration. The general CLI
reference instead shows a `--config-file` interface; inspect
`alexa-ai configure-account-linking --help` and follow the instructions matching your installed
version before proceeding. These public instructions have not been checked against the
private CLI. Neither variant is a verified way to provision the service client's secret.

Register all exact redirect URIs supplied by Amazon, review the discovered endpoints and
user scopes, then deploy again. Test a personal tool in the simulator: complete your host's
login and consent, verify the caller's identity and permissions, and test refresh and
revocation. See [OAuth authorization server](oauth-server.md) for the host login and consent flow.

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

This is the listing reference for the [add-on project](#create-the-add-on-project). You can
edit the CLI-generated package directly or prepare listing metadata in NAF and export it.

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
`addon-package/addon.json` before deployment. Follow the separate
[service credential provisioning](#provision-the-service-client-at-amazon) and optional
[account-linking](#add-account-linking) steps; the export does not transmit credentials.

After the connection and simulator checks pass, follow Amazon's certification procedure.

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
- **The service secret has no documented input:** resolve
  [Amazon service provisioning](#provision-the-service-client-at-amazon) with your onboarding
  contact; the account-linking secret prompt configures a different OAuth client.
- **CLI installation returns 404 or registry authentication fails:** check private CodeArtifact
  access and its registry login. The public npm registry does not provide the Alexa AI CLI.
- **Account-linking flags are rejected:** compare the installed command's help with the
  account-linking guide and CLI reference; their documented interfaces currently differ.

## Sources

- [Alexa+ MCP QuickStart](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-toolkit-quickstart.html)
- [Alexa+ MCP authentication](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-toolkit-authentication.html)
- [Alexa+ MCP account linking](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-toolkit-account-linking.html)
- [MCP Streamable HTTP](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
