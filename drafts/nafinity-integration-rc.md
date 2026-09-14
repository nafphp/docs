# Nafinity integration changes — release-gated documentation draft

This document describes tested **local RC sources**, not published package behavior. Keep it on `docs/nafinity-integration-rc` until the owning package releases are available. The existing public guides remain pinned to their published release inventory. After release, apply the sections below to the named guides, refresh the inventory, execute the examples, and complete the normal docs deployment workflow.

## Release map

| Package | RC branch | Documentation affected |
|---|---|---|
| framework | v0.2.4-rc | core container/events, errors, responses, output escaping |
| database | v0.2.2-rc | PDO wiring, PostgreSQL DSNs, migrations |
| session | v0.2.2-rc | MariaDB upsert and portable schema |
| form | v0.2.3-rc | CSRF and built-in validation rules |
| orm | v0.2.2-rc | explicit table names and transaction ownership |
| queue | v0.2.3-rc | optional PDO lease driver, worker failure/recovery |
| schedule | v0.2.3-rc | ticker command, state persistence and heartbeat |
| cli | v0.2.2-rc | Composer proxy bootstrap path |
| storage, rate-limit, auth-ldap | new 0.1.0 candidates | optional plugin guides after first publication |
| mail | existing v0.2.2-rc | existing configurable transport integration; no new mail implementation |

## Core guides

A registered factory may intentionally return `null`. Both the base container and auto-resolving decorator retain that cached result and report the registration through `has()`. An unregistered service remains an error. Required services can reject `null` in their own factory; this does not change the optional helper contract.

Object-method listeners retain the supplied object and its injected state. Existing static callables remain callable without unnecessary construction; class listeners are still resolved through the container.

Detailed error pages are limited to the exact `dev` environment. `test`, `prod` and unknown environment names use the generic error response. The View `s()` helper's accepted null value renders empty text rather than reaching `htmlspecialchars` as null. Escaping also substitutes malformed UTF-8 sequences.

The response emitter rewinds seekable streams and reads bounded chunks. For large downloads, return a PSR-7 stream created from an open file resource; do not cast the file to a string before building the response. The application remains responsible for authorization, safe disposition headers, MIME policy and private caching. A real FPM/nginx 64-MiB response was verified in the local integration harness.

## Database and migration guide

`Naf\Database\database()` remains nullable when the plugin is unconfigured. Installing an optional plugin must not turn this helper into a mandatory connection. The lazy `PDO::class` binding is the required-service entry point and reports absent configuration explicitly. Nafinity validates its own required database fields; it does not invent a different database helper.

PostgreSQL DSNs omit the MySQL-only charset component. The host controls PostgreSQL encoding at database creation. Original PDO connection exceptions remain chained for diagnosis.

The migration runner discovers one global order across application and plugin paths, ordered by filename and then fully qualified class name. The tracker stores fully qualified identities; an old basename is upgraded only when unambiguous. Missing/ambiguous history, duplicate identities and duplicate history fail explicitly. Down executes in reverse order of the actually applied history, rather than independently reversing each plugin directory.

PostgreSQL and SQLite apply each migration and its tracker change transactionally. MariaDB/MySQL DDL commits implicitly, so a failed migration remains untracked and its DDL must be restartable. MariaDB and PostgreSQL runners serialize through database advisory locks. Do not execute migrations inside domain transactions. Existing `db:migrate up`, `down` and `--name` remain the CLI interface.

## Session guide

The supplied sessions-table migration works on PostgreSQL and MariaDB. MariaDB writes use a native duplicate-key upsert with distinct update placeholders, including metadata fields. The application explicitly selects file sessions for the initial local prototype. Database sessions are compatibility-tested; the handler does not claim file-session-style request serialization.

## Forms and CSRF guide

Use `csrf()->token()` while rendering forms. It returns the current session token so opening another tab does not invalidate an earlier form. `generate()` remains an explicit rotation operation, useful after authentication changes.

All unsafe methods are protected, including PATCH. A Bearer header by itself no longer bypasses CSRF. The token can be a scalar `_csrf` form field or `X-CSRF-Token` header for JSON. Arrays and other malformed values are refused. Protocol endpoints that authenticate differently must be explicitly named in the existing `csrf_exempt_routes` map; a path or arbitrary header is not a route exemption.

Built-in rules cover required, string, array, integer, email, min/max, boolean and an exact calendar date in `Y-m-d`. Required accepts meaningful zero/false values and rejects null, empty text and an empty list. Project membership, role delegation and cross-project IDs remain application validation and policy concerns.

## ORM guide

Persistence and repositories use the entity's `getTableName()` contract. A model with an explicit snake_case table name can be saved and queried through the same repository without a second naming convention.

An EntityManager owns only transactions it started. If PDO already has an active transaction, the manager creates a savepoint. Nested commit releases its savepoint; rollback rolls back to it. Neither operation commits or aborts an external caller's transaction. Multiple managers on one connection use distinct savepoint names. End an externally owned transaction only after managers have completed their scopes.

Nafinity starts its transaction through the existing EntityManager and uses the same PDO connection for project-row locks, membership checks, sparse positions, pivots and activity records. Composite foreign keys enforce integrity; explicit project filters and policies authorize reads and writes.

## Queue guide

The default file and SQLite drivers remain available. The optional `PDODriver` implements `LeaseQueueDriverInterface` and the existing deadletter contract. It has one default channel. Use it where enqueue must participate in the host's existing PDO transaction.

Call `install()` from an explicit migration, then bind a `Queue` using that driver. Do not create schema from request bootstrap. A worker must reserve outside the request's transaction. `reserve()` persists a token, lease expiry and attempt count; `acknowledge()` deletes only the matching live reservation. `release()` either schedules a retry or keeps a failed row. An expired claim can be acquired by a different worker, and the old token cannot acknowledge it. `renew()` extends a live reservation. The ordinary `queue:consume` command recognizes this optional contract and acknowledges only after job success.

Choose a lease longer than the job's maximum runtime or renew explicitly. Delivery is at least once; jobs still need idempotent business effects. The PDO driver's low-level `dequeue()` returns a reservation and therefore requires acknowledgement from custom consumers. Missing job classes go through failure handling rather than silently disappearing. Use `queue:retry-failed` for deadletter recovery.

The host can set `queue:heartbeat_file` to a private writable file; the worker updates it while polling. Monitor the queue's failed rows as well as process liveness. Restart long-lived workers after source changes. A fresh HTTP request using new PHP source does not update a running worker's loaded classes.

## Scheduler guide

`ScheduleTickerCommand` starts the actual `queue:consume` command when optional embedded workers are requested. It also accepts `--once` for a real command-level smoke test. Separate ticker and worker services remain the preferred container arrangement.

Supply an installation-specific state path when constructing `Scheduler`. State is read under a lock for every tick and replaced atomically. Only an accepted enqueue advances minute suppression. An enqueue failure remains retryable. A crash between enqueue and state persistence may enqueue again; coalescing and idempotent jobs remain necessary. Malformed state is an explicit error. `schedule:heartbeat_file` exposes ticker polling liveness.

## Optional new plugins

Nafinity uses the current named-disk API: `Naf\Storage\storage('attachments')`. The configured private `Storage` instance delegates stream I/O, moves and deletion to the local adapter. The concurrently prepared plugin removed its obsolete upload lifecycle class; Nafinity now owns upload MIME/extension/size validation, opaque keys, retention enumeration and SQL/file lifecycle decisions in application services. The plugin remains provider-neutral. No public URL is configured for the attachment disk; controllers authorize and stream downloads. MIME checks are not malware scanning.


`naf/rate-limit` contains an atomic PDO fixed-window counter. The host supplies namespaced keys, limits and windows and owns the 429 response. Raw account/IP keys are hashed for persistence. Fixed windows permit a boundary burst. Counter consumption runs outside domain transactions. Nafinity uses direct peer addresses rather than trusting arbitrary forwarded headers.

`naf/auth-ldap` implements the existing Auth provider interface. Directory verification returns a stable subject; the host supplies explicit subject/account mappings and its ordinary account provider. No email matching or provisioning occurs. Native LDAP requires a trusted CA, LDAPS or mandatory StartTLS, a non-anonymous search account, bounded network/search timeouts, disabled referrals and an allowed-account filter. Session restoration rechecks the linked directory subject. Contract tests do not establish live-directory compatibility; configure the actual directory semantics and verify its TLS path before enabling it.

Nafinity uses the existing OAuth client for optional OIDC, including its state, nonce, PKCE, token verification and explicit account-link flow. Its chosen default is `auto_register=false`; users start locally and explicitly link a configured external provider. A real issuer/client is intentionally not invented for this local prototype.

## Notification and mail integration

Activity, notification records and enqueue happen in the domain transaction. Viewing and processing notifications rechecks membership and preferences. External delivery uses a per-notification channel ledger and idempotent job lookup. Mail remains disabled by default and is tested with the existing configurable Mailer/DummyTransport contract. A successful SMTP send followed by a database failure can still produce a duplicate on retry; no exactly-once mail guarantee is made.

## Evidence and publication checklist

The Nafinity checkout records the exact runtime, local source proof, database/HTTP tests and backup/restore probe. Changed package suites are run independently; the real app runs the combined stack on MariaDB and PostgreSQL. The local immutable candidate has no source mounts, vendor symlinks or Composer. It is explicitly an unreleased source snapshot and does not prove installation from published dependencies.

After the package maintainer merges and releases the RCs: refresh published metadata, create the distribution lock from a clean install, build the stable runtime, apply these changes to the corresponding guides, run `check_pages.py`, strict MkDocs and the documented HTTP examples, then publish and verify the docs deployment. Preserve the separate existing mail documentation branch.

The limiter and LDAP repositories remain local by explicit maintainer choice. Storage was independently advanced and pushed in a parallel maintainer task; this application uses its current Storage/StorageManager API. Existing package RC branches were pushed for review without merging or releasing them. The application integration passed 371 package tests (833 assertions), 28 real-engine cases per MariaDB/PostgreSQL and 28 HTTP cases; additional process tests exercised a killed worker, recovery and missing-class deadletters.
