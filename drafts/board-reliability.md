# Board reliability changes under review

This draft is outside the published MkDocs pages. It describes source candidates, not a
released installation recipe. Package code still needs maintainer review and publication;
release `naf/database` 0.2.4 before `naf/board` 0.1.3. Framework 0.2.6 already suffices. The database
0.2.3 candidate was already merged when this work started; 0.2.4 follows that commit.

## Completing plugin registration

The host orders infrastructure plugins first, all installed extensions next, and `naf/board`
last. The skeleton reads Composer's installed `naf-plugin` package names in `src/plugins.php`,
so a newly installed extension automatically boots before Board. Custom hosts must preserve
that order. No new framework event or framework DI access is needed.

Extension bootstraps only note providers. During its own bootstrap Board registers lazy
services and built-in definitions, then initializes the collected providers by index/id,
declares RBAC definitions and loads the host's optional `app/extensions.php` or
`src/extensions.php`. Host routes load afterwards. Board service resolution and replacements
belong in providers; early extension bootstraps and conventional route files precede Board.

The skeleton integration runner installs Board as a Composer plugin and resolves the published
framework without a local override. It also boots with reversed extension order (Board still
last), and checks that host overrides and routes win in both CLI and real HTTP requests.
Local aliases for Board and unpublished dependencies use `-dev`.

To replace a board route, reuse its existing route name as well as method/path, for example
`route()->add('GET', '/projects', $handler, 'projects')`. A different name does not displace
an earlier matching path.

## Inspecting migrations without applying them

`MigrationRunner::pending(array $paths): array` returns the fully qualified names of
unapplied migrations whose `shouldRun()` is true, in the runner's global order. It uses the
same discovery and identity rules as `run()`. It requires the existing migration tracker;
a missing tracker or database error propagates. It never creates tables, executes migrations
or rewrites legacy names. Unambiguous legacy names are matched in memory; an ambiguous legacy
identity fails explicitly. Applied records for removed packages remain untouched.

```php
use Naf\Database\Core\MigrationRunner;
use Naf\Database\Support\MigrationRegistry;
use function Naf\Database\database;

$pdo = database() ?? throw new LogicException('Database is not configured.');
$pending = (new MigrationRunner($pdo))->pending(MigrationRegistry::getPaths());
```

Board readiness now uses all registered migration paths, including extensions and host
migrations. It also writes, promotes, reads and deletes a temporary file on the configured
attachment disk. It returns 503 for pending migrations or failed storage and no longer
advertises a hard-coded schema version. Liveness and worker heartbeats remain separate;
operators should run `make health` to verify readiness and published assets.

## Project rights and concurrent editing

The new `ProjectAccessInterface` resolves an explicit user's active account, membership,
installation-wide administration and effective RBAC grants without consulting a session.
`forUser($projectId, $userId)` returns a `ProjectScope`; the caller checks `allows($action)`.
HTTP access and attachment finalization share this resolver. A worker reads fresh grants
instead of relying on a request cache. Revoked access, inactive accounts and archived
projects still prevent finalization. Extensions needing common request/job authorization
should replace this interface; session-only Auth policies remain request-specific.

Transfer destinations use actual project write authorization. Role assignment checks read
configured role grants rather than hard-coded defaults. Existing `AccessInterface` signatures
remain intact.

A ticket content/metadata update checks its own version inside the project lock. Updates to
another ticket no longer cause false conflicts. Structural creation/move checks still require
a board revision. A real conflict preserves the editor and offers a JSON download of its
current draft, without CSRF or version fields, before reloading.

Live notifications are queued transactionally on the existing PDO queue. A rollback removes
the job. A separate worker sees it only after commit and reads the committed board revision
before publishing. A running worker is therefore needed for live updates. Socket delivery
remains best effort; reconnect still refreshes the board. Older fetch responses cannot lower
the displayed revision.

Short inline buttons expose field, current value and action in their accessible name. Rich
text stays separate document content, with its own edit button, preserving links and headings.

## Validation and publication

Regression coverage includes authentic Composer plugin boot, both database engines, explicit
user rights, revoke-after-stage recovery, independent tickets, real conflicts, a second PDO
connection and a real publication socket, pending migration detection, failing attachment
storage, named route replacement and HTTP accessibility markup. Board integration checks boot
ordering on the published framework; database unit tests cover read-only pending inspection
and legacy names.

After package publication, move the database material into its public guides and regenerate references from published packages. Board-specific documentation is
updated alongside its source in `docs/Extensibility.md` and `docs/Tickets.md`.
