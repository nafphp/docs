---
title: Choosing packages
---

# Choosing packages { #what-do-i-actually-need }

Choose packages by the capabilities your application needs. Composer installs required
dependencies automatically; suggested packages are optional and must be installed explicitly.
The commands below extend an existing Composer project; they do not create its bootstrap,
routes or configuration. To start a project, see [Installation](install.md) or pick a
complete [application scenario](recipes/index.md).

## Package selection { #the-short-version }

| Capability | Install | Brings along | Additional setup | Guide |
|---|---|---|---|---|
| HTTP routing and JSON | `naf/framework` | — | Bootstrap and web entry point | [Routing](routing.md) |
| Templates and layouts | `naf/view` | — | PHP views and optional layout | [Views](views.md) |
| Form validation and CSRF | `naf/form` | `naf/session` | Validation rules and tokens | [Forms](forms.md) |
| Browser sessions | `naf/session` | — | Optional database storage | [Sessions](sessions.md) |
| Translated text | `naf/i18n` | — | JSON language files | [Translations](translations.md) |
| Browser components | `naf/flow` | `naf/view` | Module script in the layout | [Flow](flow.md) |
| SQL and migrations | `naf/database` | — | Database configuration and PDO driver; commands also need `naf/cli` | [Database](database.md) |
| Entities and repositories | `naf/orm` | `naf/database` | Models and schema | [ORM](orm.md) |
| Local, S3 and WebDAV files | `naf/storage` | — | Disk configuration; S3 needs `aws/aws-sdk-php`, WebDAV `ext-dom` | [File storage](file-storage.md) |
| Console commands | `naf/cli` | — | Command registration | [Console](console.md) |
| Background jobs | `naf/queue` | `naf/cli` | Queue worker | [Queues](queues.md) |
| Scheduled jobs | `naf/schedule` | `naf/queue`, `naf/cli` | Ticker and worker | [Scheduling](scheduling.md) |
| Mail delivery | `naf/mail` | — | Transport selection | [Mail](mail.md) |
| Outgoing HTTP requests | `naf/client` | — | Timeouts and retries | [HTTP client](http-client.md) |
| Database-backed limits | `naf/rate-limit` | — | Limiter table | [Rate limits](rate-limits.md) |
| WebSocket notifications | `naf/websocket` | — | Signing key and a supervised server | [WebSocket](websocket.md) |
| Authentication | `naf/auth` | — | Identity and provider; add sessions for persistent browser login | [Authentication](auth.md) |
| Editable roles | `naf/rbac` | `naf/auth`, `naf/database` | Migrations, permissions and role synchronization | [RBAC](rbac.md) |
| LDAP sign-in | `naf/auth-ldap` | `naf/auth` | Directory connection | [LDAP](auth-ldap.md) |
| External sign-in | `naf/oauth-client` | `naf/auth`, `naf/session` | Provider credentials and local account mapping | [OAuth client](oauth-client.md) |
| OAuth authorization server | `naf/oauth-server` | `naf/auth`, `naf/form`, `naf/session` | Issuer, clients and scopes; login for user grants, keys for OIDC | [OAuth server](oauth-server.md) |
| MCP tools | `naf/mcp` | — | Tools and scoped tokens | [MCP](mcp.md) |
| Alexa+ MCP server | `naf/alexa` | `naf/mcp`, `naf/oauth-server`, `naf/database`, `naf/cli` | Public HTTPS, OAuth database, separate clients and Amazon CLI access | [Alexa+](alexa.md) |

The starter (`composer create-project naf/app`) already includes `naf/framework`, `naf/view`,
`naf/form` and `naf/session`. The [package overview](packages.md) lists published versions
and complete dependency relationships.

The sections below add the decisions behind the most common choices.

## Webhooks and HTTP services { #one-endpoint-that-answers }

```bash
composer require naf/framework
```

The core provides routing, requests and responses, services, configuration, events and errors.
Templates and sessions are separate packages. See [Routing](routing.md) and
[Requests and responses](request-response.md).

For a webhook, implement the sender's signature or credential checks, validate the payload
and decide how retries are handled. Installing the core does not authenticate requests.

## Websites and forms { #a-small-website }

```bash
composer require naf/view naf/form
```

The starter already includes these packages. View renders PHP templates; Form validates input
and checks CSRF tokens for every method except GET, HEAD and OPTIONS (Form 0.2.3+).
Starter 0.2.4 locks Form 0.2.4, so a fresh installation already has this behavior. In an
older project, run `composer require 'naf/form:^0.2.4'`. Form installs Session for token storage.
The `memory()` helper reads the current request; it does not preserve input across redirects.

For two HTML pages without submissions, install only `naf/view` on top of the core and follow
[the small website](recipes/small-website.md). Add Form when you need validated submissions
and CSRF protection. Follow [Views](views.md), [Forms](forms.md) and the
[contact form](recipes/contact-form.md).
Add [`naf/i18n`](translations.md) for translated text.

## JSON APIs { #a-json-api }

The core implements JSON APIs without View, Form or Session. Use `json()` for responses and
configure [JSON error responses](errors.md#json-errors-for-an-api). Start with the
[storage-free product API](recipes/simple-json-api.md), which returns data from an injected
PHP service. The [JSON API with a database](recipes/json-api.md) adds SQLite persistence,
write operations and migrations when your application needs them.

Choose authentication separately. A bearer-authenticated endpoint must verify its token.
If Form 0.2.3+ is also installed, a Bearer header does not bypass CSRF validation. Exempt only
the exact protocol route names that authenticate their own callers. Cookie-authenticated APIs
still need CSRF protection. See [CSRF](forms.md#csrf-protection).

## Database access { #something-to-store-it-in }

```bash
composer require naf/database
```

Use Database for a configured PDO connection, SQL and migrations. Alternatively, install
ORM, which includes Database:

```bash
composer require naf/orm
```

ORM adds entity mapping and repositories. Neither package creates the application's schema.
See [Database](database.md) and [ORM](orm.md).

## User accounts { #people-with-accounts }

```bash
composer require naf/auth naf/orm naf/session
```

This combination supports the documented database-backed browser login. Auth itself requires
only the core and can use a PDO, ORM, LDAP or application-defined provider. The provider
verifies credentials and reloads identities; sessions retain verified logins between requests.
Registration and account recovery remain application responsibilities.

Follow [Authentication](auth.md#quickstart) and the [login form](recipes/login-form.md).
Add [RBAC](rbac.md) when administrators need to edit stored roles and grants.

## Background and scheduled work { #work-that-should-not-happen-during-the-request }

```bash
composer require naf/queue
```

Requests enqueue jobs; a running worker executes them. For cron schedules, install:

```bash
composer require naf/schedule
```

Schedule includes Queue and CLI. Run both a ticker and worker. See [Queues](queues.md) for
failures and delivery guarantees, and [Scheduling](scheduling.md) for missed and repeated runs.

## External sign-in { #sign-in-with-google }

```bash
composer require naf/oauth-client
```

This includes Auth and Session. Configure a provider and map external identities to local
accounts. Built-in pages render without View; add it for template overrides. See [OAuth client](oauth-client.md).

## OAuth authorization server { #being-the-provider }

```bash
composer require naf/oauth-server
```

Use this when other applications should obtain tokens for your API or sign in through your
accounts. It includes Auth, Session and Form. Configure and migrate the database, provide
local login and register clients. Review [OAuth server](oauth-server.md), including its
concurrency requirements, before deployment.

## Console applications { #a-tool-for-the-terminal }

```bash
composer require naf/cli
```

Commands use the application's configuration, container and plugins through `vendor/bin/naf`.
See [Console commands](console.md) for registration and execution.

## MCP tools { #something-a-language-model-can-call }

```bash
composer require naf/mcp
```

Register tools and issue scoped access tokens. Tools enforce application access rules for
their data and actions. See [MCP tools](mcp.md).

## Alexa+ MCP server

```bash
composer require naf/alexa
```

This installs MCP, OAuth Server, Database and CLI. Configure the public HTTPS resource,
register separate service and account-linking clients, and run local diagnostics. Amazon
onboarding and deployment use the Alexa AI CLI. Follow [Alexa+ MCP server](alexa.md).

## Mail delivery { #sending-mail }

```bash
composer require naf/mail
```

The default transport uses PHP's `mail()`. Configure local capture in development and tests.
See [Mail](mail.md), and use a queue when delivery should happen outside the HTTP request.

## Other integrations { #more-optional-capabilities }

HTTP requests, file storage, rate limits, LDAP, WebSocket notifications and Flow components
are listed in the [selection table](#the-short-version). Each guide names optional
dependencies and configuration. Continue with [Application lifecycle](lifecycle.md) and
[Deployment](deployment.md).
