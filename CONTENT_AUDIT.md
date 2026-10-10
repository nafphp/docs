# Documentation content audit — 2026-10-10

All 58 published Markdown pages were reviewed for explanations and examples lost during
the recent rewrites. Controllers and Views were restored in
[PR #51](https://github.com/nafphp/docs/pull/51); this follow-up checks the other chapters
and their relationship to those guides. An unchanged page below means its useful material
is still covered, sometimes by a corrected example or an explicit link to another chapter.

## Method and API authority

- Compare the original guide set (`ad2e2ab`), the renamed/expanded guides (`a2b224d`), the
  pre-style-rewrite content (`8cd64c0`), and the pre-correction content (`12534af`) with
  `e0b74db`, the deployed baseline for this audit. Check intermediate rewrites where the
  comparison shows removed examples, rather than treating every shorter paragraph as a loss.
- Follow helpers to services, bootstrap code and tests. Use released source, not an older
  or unreleased sibling checkout. The generated reference snapshot identifies exact
  published versions, including Framework 0.2.9, Form 0.2.4 and starter 0.2.4.
- Distinguish missing explanations from invalid API claims. Restore the explanation with
  current code; retain corrections to nonexistent helpers, namespaces, signatures, automatic
  behavior and unsupported security guarantees.
- Refresh all four generated reference pages from fresh published packages. The resulting
  inventory is unchanged: 24 packages, 64 public functions, 33 commands and 130 configuration
  keys. Generated tables are not replacements for the explanatory topic chapters.

## Chapter coverage

| Page | Review result |
|---|---|
| [Introduction](pages/index.md) | Current introduction preserves the framework's purpose and adds a runnable HTTP example and guide map. Plugin responsibilities are correctly distinguished from core features. |
| [Installation](pages/install.md) | Starter and core-only paths, bootstrap, document root and package prerequisites are more complete than the old installation. |
| [Choosing packages](pages/choosing-packages.md) | Correct the remaining obsolete Form 0.2.2 starter-lock statement; explain fresh starter 0.2.4 and older-project upgrades. |
| [First application](pages/first-app.md) | Complete project structure, services, routes, templates, verification and cleanup retain the earlier introductory material. |
| [Lifecycle](pages/lifecycle.md) | Request flow, lazy boot, plugin loading, CLI behavior and exception path remain covered; current guard behavior is already correct. |
| [Routing](pages/routing.md) | Methods, placeholders, named argument dispatch, URL generation, active routes and debugging remain covered. |
| [Controllers](pages/controllers.md) | PR #51 restored complete classes, services, route/response flow and the closure comparison with current constructor injection. |
| [Request and response](pages/request-response.md) | Input sources, merged parameters, JSON parsing, status/header handling, redirects and immutable PSR-7 responses retain the useful earlier coverage. |
| [Configuration](pages/configuration.md) | File/process environment precedence, exact environment names, colon paths, lazy loading and recursive/numeric merging are explicit. Invalid `env($key)` examples remain removed. |
| [Dependency injection](pages/dependency-injection.md) | `get()`/`make()`, factories, interfaces, scalar arguments, caching and override timing replace earlier incorrect autowiring descriptions. |
| [Events](pages/events.md) | Restore a complete custom dispatch/listener flow with constructor injection, log placeholders, argument order, priorities and results. Explain synchronous exceptions and distinct event names. |
| [Errors](pages/errors.md) | Current exception hook and complete error examples replace incorrect automatic application error-template overrides. No valid lost behavior found. |
| [Guard](pages/guard.md) | Custom rules, path/output constraints, blocklists and CLI version boundaries remain covered without unsupported recursive-sanitization promises. |
| [Views](pages/views.md) | PR #51 restored standalone templates, variables, partials, layouts/blocks, helpers, assets and path precedence, tested against released code. |
| [Forms](pages/forms.md) | All nine rules, custom rules, error helpers, request memory and current CSRF behavior are covered. Old rotating-token and Bearer-bypass guidance remains removed. |
| [Sessions](pages/sessions.md) | Restore the explicit flash default and POST/redirect/GET explanation; clarify read-once lifetime and the distinction from request memory. Storage and regeneration details remain. |
| [Scenario index](pages/recipes/index.md) | Current scenario/prerequisite comparison and request-flow explanation expand the previous recipe index. |
| [Small website](pages/recipes/small-website.md) | Complete minimal installation, controller, shared layout, assets, input checks and expected HTTP outcomes remain intact. |
| [JSON API without a database](pages/recipes/simple-json-api.md) | Complete service/controller flow, bounded input, JSON failures and operational prerequisites remain intact. |
| [POST requests](pages/recipes/post-requests.md) | Route names, body sources, type validation, failed-form rendering and success redirects remain explained with current Form/CSRF APIs. |
| [Contact form](pages/recipes/contact-form.md) | Preserve sender/reply-to, plain text, validation/memory and local outbox examples; correct the remaining claim that flash expires after one request. |
| [Login form](pages/recipes/login-form.md) | Account setup, generic failures, password handling, session rotation, POST logout, CSRF and protected routes remain covered. |
| [JSON API with a database](pages/recipes/json-api.md) | Complete PDO repository, migrations, HTTP errors and CRUD remain. Correct the residual Bearer-bypass claim and link exact-route CSRF exemptions. |
| [Database](pages/database.md) | PDO configuration, prepared statements, transactions, migrations and destructive rollback boundaries remain covered. |
| [ORM](pages/orm.md) | PR #51 restored the complete many-to-many tag/pivot example. Current protected-property mapping and `clear()` semantics remain accurate. |
| [Downloads](pages/file-downloads.md) | Current controlled identifier/stream example retains the download use case while replacing unsafe arbitrary paths and whole-file buffering. |
| [File storage](pages/file-storage.md) | Named disks, adapters, streams, permissions, errors and remote prerequisites remain covered. No useful removed example found. |
| [Console](pages/console.md) | Complete command class/registration, argument/options, help, output, interaction and exit statuses replace the old incorrect automatic discovery claim. |
| [Queues](pages/queues.md) | Restore the custom FileDriver binding and directory/consumer requirements. Keep worker retry/deadletter, channel, lease and one-off execution boundaries. |
| [Scheduling](pages/scheduling.md) | Restore job payload registration and use in the complete job. Explain named constructor arguments and default-before-array-fallback behavior. Add concrete coalescing choices; retain separate ticker/worker, no catch-up and duplicate-delivery limits. |
| [Mail](pages/mail.md) | The shipped DummyTransport example, explicit transport selection, recipients, attachments, local capture and queue guidance cover the earlier use cases with working APIs. |
| [HTTP client](pages/http-client.md) | PSR-18 requests, transport selection, configuration, retry/error semantics, streaming and a working fake transport preserve the old architecture/testing material. |
| [Translations](pages/translations.md) | Restore a complete pair of language files and executable bilingual example, including placeholders, dotted keys, missing keys and escaping context. Keep current detection semantics. |
| [MCP](pages/mcp.md) | Complete bounded tool, registration, schema, token scopes, transport and resource/progress explanations retain the valid earlier content. Unsafe arbitrary filesystem examples remain replaced. |
| [Alexa](pages/alexa.md) | Earlier setup, OAuth/MCP, diagnostics, manifest, service/user scopes and verification content remains; the rewrite adds a diagram. No removed explanation found. |
| [WebSocket](pages/websocket.md) | Restore `live()` and explain its exact configuration test. Retain qualified publishing, channel authorization, renewal, presence and supervision guidance. |
| [Authentication](pages/auth.md) | Preserve quickstart, provider contract, permission/policy, restore/session and identity-loading explanations. Replace the invalid one-argument LDAP factory with the matching application provider and link real LDAP setup. |
| [Auth architecture](pages/auth-architecture.md) | Provider ownership, compatibility, restoration and rotation remain covered; removed design rhetoric does not require obsolete API restoration. |
| [LDAP](pages/auth-ldap.md) | Restore the credential boundary: only the directory verifies the password; the local provider loads via `find()`. TLS, account links, directory failure and schema requirements remain explicit. |
| [OAuth client](pages/oauth-client.md) | Split the unreachable combined start/callback snippet into separate handlers and show the real Tokens instance method, resolved only when a token is present. Preserve issuer/subject linking, state, token renewal and concurrency boundaries. |
| [OAuth server](pages/oauth-server.md) | Restore practical scope-versus-permission examples and token lifetime tradeoffs. Keep current revocation, refresh-family, OIDC/key-retention and concurrency qualifications. |
| [RBAC](pages/rbac.md) | Restore Auth-versus-RBAC choice and synchronization context. Complete the scope-source constructor, map and imports; replace invalid role ellipses and explain stored role IDs. |
| [Rate limits](pages/rate-limits.md) | Atomic fixed windows, keys, decision handling, transaction constraints and status/header examples retain the useful material. |
| [Plugins](pages/plugins.md) | Keep complete Composer/plugin/controller/service examples, resource precedence and boot graph. Correct the diagram's obsolete CLI guard branch for Framework 0.2.9+. |
| [Flow](pages/flow.md) | Complete PHP/HTML example, reactive bindings, lists, stores, factories, lifecycle, fragments, CSP and verification retain and extend earlier content. |
| [External libraries](pages/external-libraries.md) | Composer, Blade/Eloquent integration fragments, service bindings and library ownership retain the earlier examples without inventing NAF APIs. |
| [Best practices](pages/best-practices.md) | PR #51 restored extension-point guidance. Current service/HTTP separation, output escaping, input, response and deployment guidance cover earlier recommendations accurately. |
| [Deployment](pages/deployment.md) | Production environment, public root, Apache/nginx, filesystem, migrations, workers and checks are retained and expanded. |
| [Testing](pages/testing.md) | Service tests, real HTTP PHPUnit smoke tests, state isolation and error/security checks provide more complete current guidance than the earlier snippets. |
| [Troubleshooting](pages/troubleshooting.md) | Bootstrap/routing, rendering, forms, data, logs and package checks remain explicit. |
| [Upgrade from NixPHP](pages/upgrading-from-nixphp.md) | Rename map, package type, platform commands and validation remain. `NAF_BASE_PATH` is the framework's internal core path; the application still defines `BASE_PATH`. |
| [Cheat sheet](pages/cheat-sheet.md) | Fix missing layout content capture and avoid collisions between data keys and block names. Preserve links to the complete explanatory guides. |
| [Function index](pages/function-index.md) | Regenerated from released function reflection; signatures, owning namespaces, purposes and guide links are unchanged. |
| [CLI reference](pages/cli-commands.md) | Regenerated from released command definitions; all 33 commands remain documented. |
| [Configuration reference](pages/configuration-reference.md) | Regenerated from released defaults/read sites; all 130 keys remain documented. |
| [Package overview](pages/packages.md) | Regenerated from published manifests; all 24 package versions, dependencies and runtime requirements are unchanged. |
| [Nafinity](pages/built-with/nafinity.md) | Installation/skeleton split, assets, operational commands, customization and package map remain covered. |
| [Extending Nafinity](pages/built-with/extending-nafinity.md) | Registries, provider lifecycle, transaction-aware events, export example, data ownership and removal behavior retain the useful earlier explanations. |

## Validation and boundaries

`tools/test_examples.py` extracts the new complete event/translation files and the changed
queue, schedule, RBAC and cheat-sheet fragments from Markdown. It exercises actual published
services, CLI commands and HTTP responses, including failure/retry paths and serialized job
payloads. Existing controller, view, forms, login, PDO/ORM, mail, Flow, MCP and Alexa fixtures
remain in the complete run. A local API fixture exercises the documented Auth provider and
its two-argument container factory. WebSocket configuration checks cover string flags and missing keys.

Local verification passed: 273 example checks, the 58-page inventory check and the strict
MkDocs build. Browser inspection covers all 17 changed topic pages at desktop and mobile
widths, including the new section anchors and absence of horizontal page overflow.

LDAP directory access, external OAuth provider consoles and a complete Nafinity installation
remain deployment-specific integrations. This audit checks their documented released contracts
and prerequisites; it does not claim a new live directory/provider/board deployment test.

Run the page inventory check, strict MkDocs build and complete example runner before merging.
Then verify CI and the `main` deployment for the merged commit and inspect the changed pages
on the published site. Keep this report outside user navigation: its purpose is contributor
traceability, while the restored explanations belong in the topic chapters themselves.
