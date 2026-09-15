# RC integration review — 15 September 2026

These are unreleased source candidates. This document is excluded from the published
MkDocs navigation. Merge package code through the maintainer, publish dependencies in
order, verify Packagist, and only then update the public guides and generated references.
No stable package release is made by this review.

## Scope and rationale

| Package | Candidate | Behavior reviewed |
| --- | --- | --- |
| framework | v0.2.4-rc | Null container bindings, retained exception causes, object event listeners, nullable escaping, detailed errors only in dev, bounded response emission |
| cli | v0.2.2-rc | Relative Composer proxies resolve the host bootstrap |
| client | v0.2.2-rc | Streamed upload/download, retry offsets, redirects and caller stream ownership |
| database | v0.2.2-rc | PostgreSQL DSNs, lazy PDO binding, global migration order, legacy history and CLI selection |
| form | v0.2.3-rc | Unsafe-method CSRF, stable tokens and scalar/date validation |
| mail | v0.2.2-rc | Configured transport classes, explicit transports, shared mailer and capturing DummyTransport |
| orm | v0.2.2-rc | Entity table contract, retained public `$table` overrides and caller-owned PDO transactions |
| queue | v0.2.3-rc | Durable PDO reservations, retries, fencing, recovery and worker exit status |
| schedule | v0.2.3-rc | Failed-enqueue recovery, locked state and actual child workers |
| session | v0.2.2-rc | Portable schema/upserts and repeatable PostgreSQL setup |
| storage | v0.1.0-rc | Named disks, local streams and optional S3/WebDAV adapters |

The changes belong in their owning packages and reuse existing NAF services and PSR
contracts. Application authorization and upload policy stay in the host. Queue delivery
remains at least once. Storage is a disk API, not an upload lifecycle subsystem.

## Additional regressions found and corrected

- `form`: a NUL byte in the new date rule caused DateTimeImmutable to throw instead of
  rejecting the submitted value. It is now a normal validation failure.
- `client`: cURL could not rewind the streamed request callback on a 307/308 redirect.
  Redirects now replay seekable input from its initial offset. POST 301/302 and non-HEAD
  303 redirects switch to GET and remove body headers. Cross-origin redirects remove
  Authorization/Cookie; redirect limits and disabled following remain available.
- `database`: `-n` was ignored and an empty/missing `--name` could run every migration,
  including rollback. Both spellings now select one migration; malformed, repeated or
  conflicting options fail before any migration. The actual command has PHPUnit coverage;
  naf/cli is a development dependency only.
- `session`: catching a duplicate-index exception did not restore a PostgreSQL transaction.
  PostgreSQL/SQLite now use CREATE INDEX IF NOT EXISTS. The database-host test repeats
  setup inside an active transaction and proves the transaction remains usable.
- `queue`: the legacy driver path reported success from --once after a failed job.
  It now returns nonzero while retaining retry/deadletter handling, like the lease driver.
- `schedule`: numeric CLI limits were passed as strings into strict integer parameters.
  Limits are validated and converted before starting workers. Child output uses the
  application's logs/queue directory without requiring non-PSR methods on its logger.
  Direct process arguments also let cleanup terminate the PHP child without a shell wrapper.
- `orm`: changing repository lookup to `getTableName()` dropped existing public `$table`
  overrides, including models used by the auth provider. Repository lookup now preserves
  those overrides before falling back to `getTableName()`. The regression and auth suites
  exercise both forms of table mapping.

Each correction includes regression coverage. Package READMEs describe the candidate
behavior; database/form AGENTS.md guidance was corrected where the existing text was stale.

## Guard integration follow-up

The guard registry and its four standard guards remain in `naf/framework`. Existing
`guard()->register()` support is sufficient for plugin extensions; no core change, new
guards package or framework 0.3 migration is part of this candidate.

The local, unpublished `naf/rate-limit` candidate registers `rateLimit` through its root
bootstrap. It lazily binds `PdoLimiter::class` to the host's `PDO::class`, preserving existing
bindings and later overrides. The host still migrates the counter table explicitly and
chooses the key, limit, window and HTTP response. Installation does not open a connection,
create tables or intercept requests. Direct limiter calls remain compatible.

After explicitly configuring PDO and migrating the table, a handler can call:

```php
$decision = \Naf\guard()->rateLimit('export:account:' . $accountId, 10, 60);
if (!$decision['allowed']) {
    return \Naf\json(['error' => 'Too many requests'], 429)
        ->withHeader('Retry-After', (string) $decision['retry_after']);
}
```

Here `$accountId` is an already verified identity's ID. The result retains the existing
`allowed`, `remaining` and `retry_after` fields; test `allowed`, not array truthiness.
Complete setup and contract-test instructions live in the local package README. Both
`naf/rate-limit` and `naf/auth-ldap` remain local as requested; do not publish installation
instructions for them yet.

Follow-up verification uses the original framework/plugin RCs, with no extraction prototype
installed. Limiter contract checks pass, including lazy boot, existing guards, binding
overrides, exhausted windows and transaction protection. ORM passes 33 tests / 92 assertions;
auth against the corrected ORM RC passes 99 tests / 290 assertions. A fresh demo test copy
passes all 29 existing HTTP checks plus three explicit guard calls (200, 200, 429 with
Retry-After), retaining CSRF and all four standard guards. Nafinity passes 29 scenarios each
on disposable MariaDB 11.4 and PostgreSQL 17 databases, including a shared direct/guard bucket.
Application source and data remain unchanged; these checks do not establish publication.

## Migration notes for public guides after release

Use csrf()->token() to reuse a session token across rendered pages; generate() explicitly
rotates it. PATCH and other unsafe methods require CSRF. A Bearer header does not exempt a
route: configure csrf_exempt_routes only for explicitly authenticated protocol endpoints.
The date rule accepts exact calendar dates in YYYY-MM-DD and rejects malformed input.

The database plugin now supplies a lazy PDO::class binding unless one already exists.
The helper remains nullable when configuration is absent; resolving required PDO without
configuration throws. Migration --name and -n require exactly one basename or fully qualified
identity. PostgreSQL and SQLite migrate atomically; MySQL/MariaDB DDL is not transactional.
Run migrations outside application transactions. Review ambiguous legacy names manually.

For HTTP redirects, 307/308 uploads require a seekable request body. Non-seekable bodies
cannot be replayed. max_redirects=0 returns the initial redirect for the caller to handle.
Remote storage disables redirects and automatic HTTP retries, preserving signed requests.
Release naf/client 0.2.2 before enabling the native remote-storage path. Keep optional SDK
requirements out of local-only storage installations.

Queue --once failure statuses are observable by scripts and supervisors. A lease must
outlast the job or be renewed explicitly. Run schedule:ticker and queue:consume in separate
services or use --workers with nonnegative integer --max-jobs/--max-runtime options.
--once runs one scheduling pass; it does not promise that embedded workers drain the queue.
Restart long-running workers when deploying updated source.

Mail's new transport option is a class name implementing TransportInterface. The shared
Mailer resolves it lazily; an explicit mailer($transport) remains independent. Captured
DummyTransport messages exist only in memory. Tests use captures/file outboxes, never real mail.

## Integration evidence

Package suites and composer validate --strict were rerun on PHP 8.5.4. The package suites
passed 713 tests and 1,643 assertions, plus the storage host-discovery check. Local limiter
and LDAP contract tests passed with the RC host; LDAP used a fake directory.

The actual nafphp-demo application was copied into a disposable directory. Its original
source and published dependency lock were preserved. Composer installed all 18 plugins
plus the framework using explicit development-only path versions. The combined application
passed 29 real HTTP checks for routing, JSON, CSRF, form input, escaping, local mail,
authentication, cookies, logout and suspended-user access. These are source compatibility
checks, not evidence that RC versions have been published.

Nafinity loaded its /workspace/packages sources in its existing Docker test service.
Both MariaDB 11.4 and PostgreSQL 17 passed 28 application scenarios; 28 additional HTTP
checks covered project/role isolation, CSRF including fake Bearer headers, concurrent
updates, private attachments and webroot boundaries. The real worker process survived a
SIGKILL/reclaim test without losing its reservation; the old token was fenced and a fresh
worker acknowledged the recovered job. Session upsert/repeated-migration checks passed
against both engines. All mutations were confined to nafinity_test and test storage.

Storage also passed real local MinIO and rclone WebDAV integration: nested/encoded paths,
overwrite/copy/move/delete, 32 MiB streams, bounded PHP memory and private URL behavior.
The runner removed its own containers and data. No customer bucket or directory was used.

The public documentation page checker and strict MkDocs build passed. The documented
examples passed 62 executable checks in fresh copies; the reused starter dependencies came
from the RC demo, while the separate core-only example used a published Composer install.
An actual embedded ticker worker executed a scheduled probe job in the disposable demo
and stopped at its runtime limit without worker stderr.

These tests establish the exercised compatibility paths, not an absence of every possible
bug or an acceptance test of real LDAP/OIDC/SMTP services. The package CI matrix must pass
for the exact pushed heads before merge.

## Related prepared documentation

Keep the existing storage/HTTP drafts on docs/storage, the integration guide on
[docs/nafinity-integration-rc](https://github.com/nafphp/docs/tree/docs/nafinity-integration-rc/drafts),
and the mail changes on docs/mail-transport. Apply the corrections above when promoting
those guides after release. Generated published package/function inventories remain tied
to released packages until Packagist verification, rather than advertising test aliases.
