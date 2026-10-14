---
title: NafCMS
requires:
  - naf/cms
---

# NafCMS

`naf/cms` adds content administration to a NAF application: localized articles,
pages, forms, media, navigation, themes, users, permissions and audit history.
Its page, API, content and block registries let plugins extend those workflows.
The host owns configuration, runtime storage and the public webroot.

Use CMS 0.0.2 or newer with PHP 8.3 or 8.4, Composer 2, cURL, DOM, PDO and a PDO SQLite or MySQL driver.
Framework 0.2.9+ and CLI 0.2.2+ are required and installed as dependencies.
Node.js is needed only to rebuild CMS frontend assets.

## Quick start

Create a disposable application, then install the CMS:

```bash
composer create-project naf/app my-cms
cd my-cms
composer require naf/cms
```

Create `app/plugins.php` with the CMS after its dependencies. This file orders
installed plugins; it does not install them or exclude other installed plugins.

```php title="app/plugins.php"
<?php

declare(strict_types=1);

return [
    'naf/cli',
    'naf/database',
    'naf/session',
    'naf/auth',
    'naf/form',
    'naf/view',
    'naf/i18n',
    'naf/orm',
    'naf/queue',
    'naf/schedule',
    'naf/mail',
    'naf/mcp',
    'naf/cms',
];
```

For this SQLite example, replace the disposable application's `app/config.php`:

```php title="app/config.php"
<?php

declare(strict_types=1);

return [
    'database' => [
        'driver' => 'sqlite',
        'database' => BASE_PATH . '/storage/nafcms.sqlite',
    ],
];
```

Create storage, publish the shipped assets and apply migrations from the host root:

```bash
mkdir -p storage
vendor/bin/naf nafcms:assets:publish
vendor/bin/naf nafcms:assets:check
vendor/bin/naf db:migrate up
vendor/bin/naf user:create admin admin@example.com admin
php -S 127.0.0.1:8080 -t public
```

`user:create` prompts for the password twice without terminal echo. It creates the
first installation administrator only; create additional users in the protected
administration UI. For unattended setup, use `--password-file` pointing to a
temporary mode-`0600` file, then remove that file. Do not pass passwords as arguments.

Open `http://127.0.0.1:8080/admin`. Before login, it redirects to `/admin/login`.
Sign in with the administrator you created to reach the dashboard. The plugin
repository has no front controller and cannot be served directly.

For MySQL/MariaDB, configure `DB_DRIVER`, `DB_HOST`, `DB_PORT`, `DB_USERNAME`,
`DB_PASSWORD` and `DB_DATABASE` instead. `db:migrate up` applies pending migrations;
`install:database` may also create the configured database. Use the migration-only
command when infrastructure manages database creation.

## Add a protected page

In the example application, replace `app/routes.php` with this registration. In an
existing application, add it alongside the application's other routes.

```php title="app/routes.php"
<?php

declare(strict_types=1);

use Naf\CMS\Enums\Permission;
use Naf\CMS\Page\Page;

use function Naf\CMS\cms;
use function Naf\View\view;

cms()->pages()->add(
    Page::create('app.reports')
        ->setPath('/admin/reports')
        ->setTitle('Installation report')
        ->setLayout('admin')
        ->requirePermission(Permission::SYSTEM_READ)
        ->setAdminNavigation('Installation report', parent: 'system', icon: 'stats')
        ->setContent(static fn(): string => view('reports', [
            'message' => 'The CMS extension is running.',
        ])),
);

cms()->pages()->registerRoutes();
```

Create the host-owned template `app/views/reports.phtml`:

```html+php title="app/views/reports.phtml"
<?php
use function Naf\View\s;
?>
<h1>Installation report</h1>
<p><?= s($message) ?></p>
```

After login, visit `/admin/reports`. It displays the report inside the CMS admin
layout. The page requires `system.read`; hiding a navigation item alone does not
enforce authorization. A plugin can register the same `Page` from its bootstrap,
with `replace: true` for an intentionally idempotent registration.

Page content callbacks can return a string for the page layout or a PSR-7 response.
Use `Page::setDataHandler()` for a form posted back to a page; data handlers must
return a response. Register JSON/actions through `cms()->api()` and
`Naf\CMS\Api\ApiEndpoint`; keep workflow logic in handlers and application services.

## Content, blocks and extension points

Use the highest existing data-access layer that covers the operation:

| Layer | Purpose |
|---|---|
| `cms()->articles()` or `cms()->content(Model::class)` | Domain actions, validation, lifecycle rules and audit entries |
| A content API's `storage()` | Generic entity CRUD and criteria-based reads |
| A content API's repository, where exposed | Joins, aggregates and named queries |
| The configured NAF PDO connection | Migrations and SQL not covered by the higher layers |

Keep audit entries at the domain-action boundary so storage and repository calls do
not record the same action twice. `cms()->contentTypes()` registers content APIs.
`cms()->blockTypes()` describes editable PageBuilder fields; `cms()->blocks()` maps
saved block types to views. Unknown block types render the placeholder view.

Navigation defaults to the frontend scope. Use `cms()->scope(Scope::ADMIN)` with
`Naf\CMS\Enums\Scope` when contributing admin navigation directly. A registered
page can carry its own admin navigation metadata, as in the example above.

The [extension examples](https://github.com/nafphp/cms/tree/main/examples) cover
protected pages, content types, blocks, scoped MCP tools, a complete Composer plugin
and service replacement. Register integrations explicitly; placing a PHP file in
a directory does not activate a CMS feature.

## Runtime files and updates

Package defaults under `vendor/naf/cms` stay read-only. Installation-specific
prompts, memory, translation overrides, rate-limit counters and embedding caches
use `storage/nafcms` by default. Relative `cms:runtime_path` values resolve below
the host root and reject `..`; absolute paths support deliberate external volumes.
Reads prefer the host override and fall back to the package default.

The asset publisher copies the package's CSS, JavaScript, fonts and images into
the host public directory. `.nafcms-assets.json` records ownership and hashes.
Publishing updates unchanged owned files and rejects host-modified collisions;
removal preserves modified host files. Generated theme CSS is installation data.

Back up the database, runtime files, uploaded media and generated themes before
updating. Then run Composer, `nafcms:assets:publish`, `nafcms:assets:check` and
`db:migrate up`, and verify login and the workflows your installation uses.

`nafcms:agents:install` creates a CMS project guide only when the host has none.
It preserves user-owned files; the current starter's `AGENTS.md` therefore makes
the command exit with status 1. Review and combine the
[CMS guide template](https://github.com/nafphp/cms/blob/main/docs/templates/SHIPPED_AGENTS.md)
with that existing guide. `--update` refreshes only a CMS-managed guide.

## Authentication, MCP and local AI

CMS login uses `naf/auth` with a database provider and CMS session adapter.
Page/API permissions and domain privilege checks remain enforced in the CMS.
Anonymous HTML access redirects to login; API denials return JSON with 401 or 403.
Logout is a CSRF-protected POST. Existing legacy sessions can be restored through
the database provider; see the
[Auth integration notes](https://github.com/nafphp/cms/blob/main/docs/auth-migration.md).

MCP authentication is enabled with file-backed tokens by default. Create tokens
with `vendor/bin/naf mcp:token:create` and grant only the scopes the client needs.
Tools use the executable registry; `cms_system_health`, `cms_queue_status` and
`cms_article_status_counts` expose concrete read capabilities. See [MCP tools](mcp.md).

The optional local assistant is disabled by default and uses browser-local Ollama.
Its selected tools come from tool metadata, permissions and scopes. An optional
embedding model helps rank tools; failure falls back to keyword routing.
The first preview does not persist remote-provider API credentials. Confirmation
dialogs provide guidance; server-side permissions and scopes enforce access.

Server-side webhooks require public HTTPS targets. The outbound policy validates
and pins resolved addresses and rechecks redirects. Local development HTTP requires
both an explicit opt-in and an exact allowed hostname. Server-side Ollama embeddings
accept only loopback hosts and configured ports.

## Configuration

Add overrides to the array returned by host `app/config.php`. These are the CMS
and AI keys; the generated [configuration reference](configuration-reference.md#nafcms)
also lists shared application, database, session, view, schedule and MCP defaults.

| Key | Type | Default | Effect |
|---|---|---|---|
| `cms:runtime_path` | string | `storage/nafcms` | Host-owned runtime root |
| `cms:languages` | string list | `['en', 'de']` | Initial content languages |
| `cms:admin:accent_colors` | map | Colors by admin area | Admin navigation accents; see generated defaults |
| `cms:media:storage_path` | string | `{BASE_PATH}/storage/media` | Uploaded media storage |
| `cms:media:public_url` | string | `/media` | Media URL prefix |
| `cms:media:max_upload_size` | integer | `26214400` | Maximum upload bytes |
| `cms:media:allowed_extensions` | map | Shipped extension/MIME allow-list | Both extension and MIME must match; SVG is excluded |
| `cms:outbound_http:webhooks:allow_development_http` | boolean | `false` | Enables the explicit local HTTP exception |
| `cms:outbound_http:webhooks:development_hosts` | string list | `[]` | Exact hostnames allowed by that exception |
| `cms:outbound_http:webhooks:timeout` | number | `8.0` | Request timeout in seconds |
| `cms:outbound_http:webhooks:max_response_bytes` | integer | `65536` | Webhook response limit |
| `cms:outbound_http:ollama:allowed_ports` | integer list | `[11434]` | Allowed loopback embedding ports |
| `cms:outbound_http:ollama:max_response_bytes` | integer | `1048576` | Embedding response limit |
| `ai:enabled` | string | `'0'` | Local assistant enabled flag |
| `ai:type` | string | `local` | Local Ollama provider; remote mode is reserved |
| `ai:url` | string | `http://localhost:11434` | Ollama endpoint |
| `ai:model` | string | `llama3.1:8b` | Chat model; choose one supporting tools |
| `ai:embedding_model` | string | empty | Optional semantic tool-ranking model |
| `ai:routing_debug` | boolean | `false` | Allows capped query text in routing diagnostics |
| `ai:instructions` | string | empty | Installation-specific assistant guidance |

Session proxy trust is disabled by default. If TLS terminates at a proxy, configure
the session plugin's exact trusted proxy addresses together with its trust flag;
see [Sessions](sessions.md). Keep secrets in the host environment and runtime files
outside the public webroot. The PHP built-in server is for local development.

## API details

Import helpers explicitly from `Naf\CMS`:

```php-inline
use function Naf\CMS\cms;

$pages = cms()->pages();
$apis = cms()->api();
$contentTypes = cms()->contentTypes();
$blocks = cms()->blockTypes();
```

The facade also exposes settings, languages, navigation, themes, visualizations
and the content APIs. The generated [function index](function-index.md#nafcms)
contains helper signatures. Use `Naf\Auth\auth()` for authentication;
`Naf\CMS\user()` exposes the authenticated CMS user or null. Test-only overrides
and resets are not authentication mechanisms.

The [CLI reference](cli-commands.md#nafcms) lists installation and maintenance
commands, arguments and options. From a configured contributor checkout,
`vendor/bin/naf docs:check` verifies registry-derived reference blocks and
`vendor/bin/naf integrity:check` checks the CMS registrations and resources.

## If the result is different

| Symptom | Check |
|---|---|
| Bootstrap reports a missing dependency helper | Put CMS after its installed dependencies in `app/plugins.php`. Run commands from the host. |
| Database or migration command fails | Check the PDO driver, configured database and host storage permissions before `db:migrate up`. |
| The admin page has missing styles or scripts | Run `nafcms:assets:publish` and `nafcms:assets:check`; review modified-file collisions. |
| `/admin` redirects to login | This is the expected anonymous response. Create the first admin and sign in. |
| `user:create` refuses another user | It bootstraps the first admin only. Use the authenticated user administration afterwards. |
| The agent guide installer exits with 1 | An existing user-owned guide was preserved. Combine the CMS template with it manually. |
| A custom page remains unavailable | Register the page and its routes, check its path/name, then verify the required permission. |
| Embedding selection fails | Check the loopback endpoint and allowed port; keyword routing remains the fallback. |

??? note "Preview compatibility"
    Version 0.0.1 is the first CMS preview. Sitebuilder payloads, extension APIs and
    storage shapes may change before 0.1. The builder accepts `builderVersion: 1`,
    with bounded payload size, block counts and nesting. It has no undo/redo,
    collaborative editing or guaranteed autosave recovery. Local AI is Ollama-only,
    custom theme JavaScript is disabled, and PHP 8.5 is a compatibility target.

    Version 0.0.1 omitted template-only Tailwind utilities from the shipped CSS.
    Upgrade to 0.0.2 or newer and republish/check assets before using that installation.

## Related pages

- [Plugin development](plugins.md) for Composer discovery and extension boot order.
- [Authentication](auth.md), [forms](forms.md) and [sessions](sessions.md).
- [Database and migrations](database.md) and [ORM](orm.md).
- [Queues](queues.md), [scheduling](scheduling.md) and [MCP tools](mcp.md).
- [Release notes](https://github.com/nafphp/cms/releases/tag/v0.0.2) and
  [security reporting](https://github.com/nafphp/cms/blob/main/SECURITY.md).
