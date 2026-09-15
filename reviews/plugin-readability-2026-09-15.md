# Plugin readability review — 2026-09-15

## Scope and method

The inventory covers all 22 immediate workspace packages whose Composer type is
`naf-plugin`: 1,102 PHP/PHTML files, including tests and examples. Git-tracked files and
non-ignored untracked source were included; vendor dependencies and generated caches were
excluded. Core, starter, Studio and native code are outside this plugin inventory.

PHP CS Fixer 3.95.25 ran read-only against Nafinity's PER-CS 3.0 rules with a finder
restricted to that inventory. 883 files would change. These are differences from the full
project rule set, including additional readability preferences, **not 883 bugs or proof
that every file violates PSR-12**. No package exposed a Composer style-check script in the
initial manifest inventory. The manual review sampled entry points and representative
services; this was not a complete semantic or security audit of every plugin.

The snapshot is from local worktrees, which include unreleased RC changes. `guards` and
`sanity` also contained untracked source; their counts do not describe a released version.
The initial pass changed only `auth-ldap`. The maintainer then requested the same cleanup
for all remaining plugins; the completed rollout is recorded below.

## Initial formatter inventory

| Plugin | Local HEAD before cleanup | Files checked | Files with changes |
|---|---|---:|---:|
| `auth` | `3b72133` | 40 | 30 |
| `auth-ldap` | `35a539d` | 4 | 0 |
| `cli` | `76df414` | 19 | 17 |
| `client` | `e30b346` | 15 | 10 |
| `cms` | `f0cd7e1` | 623 | 542 |
| `database` | `635e2f7` | 21 | 10 |
| `form` | `326d623` | 12 | 6 |
| `guards` | `85a0266` | 16 | 8 |
| `i18n` | `f2ffaa8` | 12 | 12 |
| `mail` | `7f6ad24` | 19 | 14 |
| `mcp` | `71d3b95` | 30 | 22 |
| `monitoring` | `f8fc4ad` | 34 | 23 |
| `oauth-client` | `2260203` | 58 | 42 |
| `oauth-server` | `62c1985` | 62 | 56 |
| `orm` | `06a5233` | 30 | 24 |
| `queue` | `d7a6f1f` | 25 | 18 |
| `rate-limit` | `048924a` | 4 | 2 |
| `sanity` | `1745036` | 8 | 6 |
| `schedule` | `26084a4` | 13 | 8 |
| `session` | `8fa2509` | 10 | 7 |
| `storage` | `be2093a` | 31 | 18 |
| `view` | `d3414d3` | 16 | 8 |

## Concrete improvements, in order

1. **Make the rules repeatable.** Adopt the [shared configuration](../CODE_STYLE.md) per
   package and run it in CI. Small plugins such as `form`, `view`, `i18n`, `mail`, `cli`
   and `session` are useful first migrations. Separate imports, expand methods containing
   statements on one line, and normalize casts and concatenation. For example,
   `auth/src/Identity/Identity.php` has three single-line getters; `form/src/Core/Validator.php`
   and `i18n/src/Core/Translator.php` mix imported and fully qualified exception names.
   Existing small classes already have clear responsibilities and need no new layers.

2. **Improve SQL and names in `rate-limit`.** `src/PdoLimiter.php::consume()` combines long
   dialect-specific UPSERT strings, transaction handling and result mapping in one block.
   Use indented SQL, a `$statement` instead of `$q`, and blank lines around preparation,
   execution and commit. Keep the current bound values, conflict handling and transaction
   order. Similar long tracker SQL appears in `database/src/Core/MigrationRunner.php`.
   A query builder or extra repository is unnecessary for this work.

3. **Expose the steps in HTTP and OAuth flows.** In `client/src/Core/Client.php`, local names
   such as `$cfg`, `$msg`, `$respBody`, `$last` and `$t` conceal configuration, retry and
   transport roles. In `oauth-server/src/Core/TokenEndpoint.php::fromCode()` and
   `fromRefreshToken()`, nested `identify(forLivingAccount(redeem/rotate(...)))` calls would
   read more clearly as named intermediate results. Preserve token consumption, account
   checks and exception order; do not split the atomic token-store operation. The existing
   OAuth service/store boundaries already fit the framework.

4. **Group long-running worker phases.** `queue/src/Commands/QueueConsumeCommand.php::run()`
   interleaves heartbeat, stop conditions, acquisition, execution, acknowledgement and logging.
   Name `$q` for its queue role, group the steps visibly and combine adjacent identical
   verbosity guards where safe. `schedule/src/Support/CronParser.php` mainly needs spacing
   and readable local names. Keep worker reset, lease and shutdown behavior covered by
   the command harness; do not introduce another worker abstraction.

5. **Keep comments useful and templates deliberate.** `cli/src/Core/Input.php`,
   `i18n/src/Core/Translator.php` and `mail/src/Models/Mail.php` contain PHPDoc that repeats
   native types. Trim redundant prose while retaining array shapes, side effects and
   protocol explanations. `mcp/src/Core/MCPRouter.php` can use `$message` and `$arguments`
   instead of `$msg` and `$args` for local values, but public parameter names need compatibility
   review. `guards/src/DefaultGuards.php` benefits from blank lines between registrations.
   `monitoring` and `storage` already use focused types; concentrate on consistency, not
   further class splitting. CMS accounts for 623 files and mixes repositories with templates:
   migrate it by area with rendered-output checks. ORM transaction/snapshot handling and
   OAuth concurrency logic require their existing behavior suites during any later cleanup.

6. **Treat prototype work separately.** `sanity/src/Runtime.php` still prints `var_dump()`
   and dynamically discovers actions, and the manifest has no declared test script.
   Clarify that package's intended API and maturity before treating formatting as production
   readiness. Preserve the existing untracked traits and helpers.

## Completed example: auth-ldap

`auth-ldap` already had zero formatter differences in the initial inventory, demonstrating
why a formatter alone is insufficient. Its cleanup separates validation and I/O, names the
TLS and connection options, makes account mapping explicit, shortens filter construction
with an escaped intermediate value, and documents callback signatures. The existing three
production types and public signatures remain intact.

The package now has a pinned development formatter, `composer style:check` and
`composer style:fix`, and provider/configuration tests in separate files. Regression cases
cover unsupported/empty credentials, missing or malformed links, deleted accounts,
directory revocation, propagated directory failures and configuration boundaries.
The tests use a fake directory and a temporary CA file; they do not verify a live LDAP server.

The package remains a local `v0.1.0-rc` with no remote, as required by its existing instructions.
No package release or remote creation is implied by this review.

## Completed rollout

All 22 workspace plugins now use the same PER-CS 3.0 rules and pinned PHP CS Fixer 3.95.25,
with `composer style:check`, `composer style:fix` and a dedicated CI workflow. Source,
tests, examples and mixed PHP/PHTML templates are covered; `cli` also includes `bin/naf`.
The formatter remains a development dependency. Existing runtime dependency constraints
and locked runtime package versions were preserved.

The manual changes cover the review's main readability findings:

- HTTP configuration, response and retry values have descriptive local names.
- OAuth code redemption and refresh rotation expose the existing account-check and
  ID-token steps without changing their order or the atomic store operations.
- Queue workers use readable queue/channel names, separate execution and acknowledgement,
  and combine adjacent verbosity conditions.
- Rate-limit SQL is laid out by clause, with the same bound values and transaction order.
- CLI, translation and mail PHPDoc retain useful behavior/array information and drop
  repeated native types. Translation placeholders use descriptive local names.
- Generated database migrations follow the same import order and method formatting.
- CMS chart translation had an invalid namespaced import in its global fallback. The
  corrected import is covered by a standalone regression case that fails before the fix;
  the two obsolete PHPStan baseline entries were removed.

### Verification and limits

- All 22 manifests pass `composer validate --strict`; all 22 formatter checks pass.
- All 21 declared test scripts pass both locally on PHP 8.5 and in an isolated PHP 8.3.33
  container. Existing suites retain their conditional integration skips.
- All four declared static-analysis scripts pass: auth, CMS, OAuth client and OAuth server.
- `sanity` has no declared test suite. Its existing discovery smoke check passes on PHP 8.5;
  its PHPUnit 13 development dependency requires PHP 8.4.1 or newer.
- CMS has 25 passing JavaScript builder tests and passes the package archive check.
- Storage passes the isolated MinIO and WebDAV integration runner, including encoded paths,
  32 MiB streaming transfers, bounded memory and private URLs.
- The database command was exercised through the real NAF container and command input/output.
  The generated migration passes the formatter, loads and executes both empty directions.
- A syntax-tree comparison covered the mechanical PHP/PHTML changes, including literal
  HTML output. The few structural differences (nullable type spelling, explicit constant
  visibility and `elseif`) were reviewed, as were all intentional readability changes.
  This is not a browser-based visual review or a full security audit.
- All 19 remote packages pass their new GitHub style workflow at the cleanup head.
  The other triggered package workflows pass except the existing CMS workflow. Its
  [baseline run](https://github.com/nafphp/cms/actions/runs/34779222185) and
  [cleanup run](https://github.com/nafphp/cms/actions/runs/35024701833) fail on the same
  published CLI bootstrap path, parallel bootstrap directory race and stale generated CSS.
  Even the CSS rebuild diff has the same before/after blob IDs in both runs. The CLI fix
  already awaits merge/release on `naf/cli`'s RC branch; this cleanup does not publish it or
  add a dependency workaround. CMS's local tests, analysis and new style CI pass.

These are RC changes, not new package releases. Package code remains for the maintainer to
merge. No public API signatures or configuration contracts were changed, so user recipes and
generated API references need no version-dependent update. The CMS fallback correction is
also recorded in its unreleased changelog.

`auth-ldap` and `rate-limit` remain committed local RCs without a remote, as previously
requested. `guards` consists of existing untracked work and has no remote: its formatted
working tree and style setup are deliberately left uncommitted. Existing untracked source
in `sanity` was formatted but not included in the package commits. Original working copies
were backed up before formatting; this rollout does not turn either prototype into a release.

### Branches and review links

| Plugin | RC branch | Cleanup head | Review |
|---|---|---|---|
| `auth` | `v0.2.2-rc` | [10220ce2](https://github.com/nafphp/auth/commit/10220ce216ecd9431af3e8c5dd5ec8ce50a59234) | [Compare](https://github.com/nafphp/auth/compare/main...v0.2.2-rc) |
| `auth-ldap` | `v0.1.0-rc` | `1212d624` | Local only |
| `cli` | `v0.2.2-rc` | [df3231ca](https://github.com/nafphp/cli/commit/df3231ca8c40712921992eb95f7c47be861f1a5b) | [PR #2](https://github.com/nafphp/cli/pull/2) |
| `client` | `v0.2.2-rc` | [c6638ea8](https://github.com/nafphp/client/commit/c6638ea8f4f9526cbb5d68d58995f0687ad95864) | [PR #2](https://github.com/nafphp/client/pull/2) |
| `cms` | `v0.0.1-rc` | [2bc03d88](https://github.com/nafphp/cms/commit/2bc03d88519229cec7391303e29f44cf8cfdaa89) | [Compare](https://github.com/nafphp/cms/compare/main...v0.0.1-rc) |
| `database` | `v0.2.2-rc` | [3ad991d0](https://github.com/nafphp/database/commit/3ad991d0f6bc6a5329bcb90d55acaa28d0243498) | [PR #2](https://github.com/nafphp/database/pull/2) |
| `form` | `v0.2.3-rc` | [46837d8f](https://github.com/nafphp/form/commit/46837d8fa5fa2cb32ea4b5ff8ef9f84c8428a8eb) | [PR #2](https://github.com/nafphp/form/pull/2) |
| `i18n` | `v0.2.2-rc` | [34ec5fab](https://github.com/nafphp/i18n/commit/34ec5fab991b166dc5ab415928aed3e3c770d5d8) | [Compare](https://github.com/nafphp/i18n/compare/main...v0.2.2-rc) |
| `mail` | `v0.2.2-rc` | [3a94c6d1](https://github.com/nafphp/mail/commit/3a94c6d12b624f2b0ac483023bea7a137e23234f) | [PR #2](https://github.com/nafphp/mail/pull/2) |
| `mcp` | `v0.2.3-rc` | [de247816](https://github.com/nafphp/mcp/commit/de247816c007357613c7fa842933c5a1d24ceb92) | [Compare](https://github.com/nafphp/mcp/compare/main...v0.2.3-rc) |
| `monitoring` | `v0.1.0-rc` | [a9d01678](https://github.com/nafphp/monitoring/commit/a9d01678b342320440928ccf567bb93f2b6c433d) | [Compare](https://github.com/nafphp/monitoring/compare/main...v0.1.0-rc) |
| `oauth-client` | `v0.2.3-rc` | [c2c36549](https://github.com/nafphp/oauth-client/commit/c2c36549f72e3bcde59d34a73c4ca177664cb319) | [Compare](https://github.com/nafphp/oauth-client/compare/main...v0.2.3-rc) |
| `oauth-server` | `v0.2.3-rc` | [7260c8ea](https://github.com/nafphp/oauth-server/commit/7260c8ea68e4285e105dd713b4d93a2313d27ff9) | [Compare](https://github.com/nafphp/oauth-server/compare/main...v0.2.3-rc) |
| `orm` | `v0.2.2-rc` | [33fcc15b](https://github.com/nafphp/orm/commit/33fcc15b4dddb5f4a033340268f4f7a9eda8da58) | [PR #2](https://github.com/nafphp/orm/pull/2) |
| `queue` | `v0.2.3-rc` | [25bfc984](https://github.com/nafphp/queue/commit/25bfc984e56115c3ac59fc91611a3b84222db582) | [PR #2](https://github.com/nafphp/queue/pull/2) |
| `rate-limit` | `v0.1.0-rc` | `ba924964` | Local only |
| `sanity` | `v0.2.1-rc` | [3fc12463](https://github.com/nafphp/sanity/commit/3fc1246360963f378c083da3da32c67a9c1868fb) | [Compare](https://github.com/nafphp/sanity/compare/main...v0.2.1-rc) |
| `schedule` | `v0.2.3-rc` | [1ccaaa86](https://github.com/nafphp/schedule/commit/1ccaaa86eb4745e9a683eabe02eb19965ab70291) | [PR #2](https://github.com/nafphp/schedule/pull/2) |
| `session` | `v0.2.2-rc` | [b4980e02](https://github.com/nafphp/session/commit/b4980e02d64fde2815d93d40f06b6a9575b72562) | [PR #2](https://github.com/nafphp/session/pull/2) |
| `storage` | `v0.1.0-rc` | [0e600b86](https://github.com/nafphp/storage/commit/0e600b86fc6be7ce995ccdcdd098a1aa12782eb8) | [PR #1](https://github.com/nafphp/storage/pull/1) |
| `view` | `v0.2.2-rc` | [133070c1](https://github.com/nafphp/view/commit/133070c1803355099f56aeedca2691e856896f89) | [Compare](https://github.com/nafphp/view/compare/main...v0.2.2-rc) |
| `guards` | `v0.1.0-rc` | Uncommitted working tree | Local only |
