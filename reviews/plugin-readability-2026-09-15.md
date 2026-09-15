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
Only `auth-ldap` was changed as part of this cleanup. Other repositories were inspected
without formatting or modifying their working trees.

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
