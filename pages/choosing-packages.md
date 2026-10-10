---
title: Choosing packages
---

# Choosing packages { #what-do-i-actually-need }

Choose packages by the capabilities your application needs. Composer installs required
dependencies automatically; suggested packages are optional and must be installed explicitly.
The [package overview](packages.md) lists published versions and dependency relationships.

Start a website with `composer create-project naf/app my-app`. For an HTTP service without
templates or sessions, use the [core-only installation](install.md#core-only-project).
The commands below extend an existing Composer project; they do not create its bootstrap,
routes or configuration.

The [application scenarios](recipes/index.md) pair each result with its package set and a
worked guide. Start with [a small website](recipes/small-website.md)
or [a JSON API without a database](recipes/simple-json-api.md) in an empty directory.

## Package selection { #the-short-version }

| Capability | Install | Additional setup |
|---|---|---|
| HTTP routing and JSON | `naf/framework` | Bootstrap and web entry point |
| Templates and layouts | `naf/view` | PHP views and optional layout |
| Form validation and CSRF | `naf/form` | Validation rules and tokens; includes `naf/session` |
| SQL and migrations | `naf/database` | Database configuration and PDO driver; commands also need `naf/cli` |
| Entities and repositories | `naf/orm` | Models and schema; includes `naf/database` |
| Authentication | `naf/auth` | Identity and provider; add sessions for persistent browser login |
| Editable roles | `naf/rbac` | Migrations, permissions and role synchronization |
| Background jobs | `naf/queue` | Queue worker; includes `naf/cli` |
| Scheduled jobs | `naf/schedule` | Ticker and worker; includes Queue and CLI |
| External sign-in | `naf/oauth-client` | Provider credentials and local account mapping |
| OAuth authorization server | `naf/oauth-server` | Issuer, clients and scopes; login for user grants, keys for OIDC |
| Alexa+ MCP server | `naf/alexa` | Public HTTPS, OAuth database, separate clients and Amazon CLI access |

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
and checks CSRF tokens on POST, PUT and DELETE. Form installs Session for token storage.
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

| Capability | Package | Guide |
|---|---|---|
| HTTP requests | `naf/client` | [HTTP client](http-client.md) |
| Local, S3 and WebDAV files | `naf/storage` | [File storage](file-storage.md) |
| Database-backed limits | `naf/rate-limit` | [Rate limits](rate-limits.md) |
| LDAP authentication | `naf/auth-ldap` | [LDAP provider](auth-ldap.md) |
| WebSocket notifications | `naf/websocket` | [WebSockets](websocket.md) |
| Browser components | `naf/flow` | [Flow](flow.md) |

Each guide names optional dependencies and configuration. Continue with
[Application lifecycle](lifecycle.md) and [Deployment](deployment.md).
