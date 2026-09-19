# Shared workflow for NAF contributors and coding agents

This is the maintained workflow for the `nafphp` repositories. Each plugin's `AGENTS.md`
explains its own API, extension points and checks; this file records the shared working
agreement. Use the repository's local instructions and actual source for package specifics.
Do not assume a parent workspace directory exists in a standalone clone.

## Framework conventions

NAF is a small PHP framework with optional Composer plugins. Keep business logic in the host,
optional reusable functionality in plugins and common HTTP/boot infrastructure in the core.
Use existing NAF functions and services where they fit, with explicit namespace imports.
Prefer configuration, constructor injection, interfaces, events and registries over copying
framework internals. Return PSR-7 responses from handlers and let NAF emit them.

The starter is `composer create-project naf/app`; plugins use Composer type `naf-plugin`.
A plugin repository is not a standalone application's web root. The host has `BASE_PATH`,
a Composer autoloader and service registrations before `app()->run()`; only its `public/`
directory is served. Constructor autowiring uses `make()`; `get()` retrieves registrations.
Read the [DI guide](pages/dependency-injection.md) and [plugin guide](pages/plugins.md).

Check manifests, configuration, bootstrap, public helpers and tests before adding APIs.
Respect each package's supported PHP versions/extensions. Keep optional dependencies optional.
Do not edit installed vendor files. Verify published package versions before documenting
behavior found only in a development checkout.

## Code style and readability

Follow [the shared code style](CODE_STYLE.md): PER Coding Style 3.0 with the readability
rules used in Nafinity. Separate logical steps, use descriptive local names and keep
simple operations in ordinary PHP. Formatting must preserve public signatures, evaluation
order, escaping and resource/transaction boundaries. Apply the shared formatter template
per package, run its style and behavior checks, and keep formatting commits separate
from behavioral changes. Existing packages adopt it incrementally on their RC branches.

## Working and publishing

- Inspect Git status and fetch the correct remote. Preserve other contributors' changes;
  stage only your task's files/hunks. Use an isolated checkout when needed.
- For a package behavior fix, determine the next version from current tags/releases and use
  `v<major>.<minor>.<patch>-rc` from current `origin/main`. Resume an existing intended RC;
  never overwrite a released version or somebody else's branch.
- Implement, add meaningful regression coverage, run declared package checks, commit and
  push. Use the existing `Preparations for vX.Y.Z - ...` subject convention for release work.
  Keep the configured author and attribute the actual contributing agent when applicable.
- Open the pull request for package code once the branch is pushed — that is where the
  maintainer reviews the diff and the checks — and then stop. The maintainer merges package
  code through GitHub. Do not merge source-code PRs or enable auto-merge for them unless the
  user explicitly delegates that step.
- Verified documentation-only work, including plugin `AGENTS.md` guidance, is delegated:
  commit, push, create or reuse a PR, review its full diff/current checks, merge using an
  allowed method, and verify publication. Do not request the same approval again. A mixed
  code/documentation PR remains subject to the package-code merge rule.
- Documentation-only changes can use a descriptive `docs/...` branch; no new Composer
  version is required just to update contributor guidance. Repository guidance becomes
  available on GitHub after merge and is included in later package releases.
- A user request to create a release authorizes tagging and publication after the merge and
  required checks. Follow [RELEASING.md](RELEASING.md) through GitHub and Packagist verification.
  A fix request alone does not authorize publication. Never move an existing release tag.

## Documentation is part of every change

Review affected guides, setup, configuration, API signatures, commands, examples and
navigation for every behavior change and release. Correct and extend them alongside the
implementation. If nothing needs updating, state why. Keep plugin `AGENTS.md` instructions
accurate when their public API, extension points, structure or test commands change.

A package `README.md` is shipped inside the Composer package, so whatever it says reaches
every installation of every later tag. Extend it only to describe what the code does. Never
write release state into it — no branch names, no "unreleased", no "not a published release
yet", no version that the text will outlive. Those belong in the pull request, the release
notes or the changelog, all of which stay attached to the moment they describe. A README
sentence that is true on a branch and false after the merge is a defect that ships.

What a package does, how it is configured and what it needs belongs in the documentation
repository, which every package README already links to. Prefer putting it there.

Follow [README.md](README.md) for documentation checks: check pages, build MkDocs strictly,
and execute the documented examples. Refresh generated package/function references when
releases or signatures change. New examples outside the automated runner need their own
behavior check. Use fresh test applications and a dummy/file mail transport for local tests.
Publish instructions requiring a new package only after it is on Packagist and those examples
pass against it. Remove obsolete workarounds only after verification.

After a docs-repository merge, verify the `NAF Docs` workflow for that merged commit and
inspect the changed live pages on https://nafphp.github.io/docs/. A successful PR check alone
is not proof of deployment. Contributor files such as this one are published in the repository;
they are not automatically website pages. Check their links/content on the merged GitHub revision.

## Verification and handover

Use the test/analysis scripts declared in `composer.json` and `composer validate --strict`.
Run changed CLI behavior through the real command harness and HTTP behavior through a host.
For documentation-only instruction changes, verify paths, namespaces/signatures, examples and
workflow consistency; do not claim unrelated runtime suites ran. Respect required repository CI.
Before an OAuth-server release, run both concurrency scripts on SQLite, PostgreSQL and MySQL
as described in that package's `tests/Concurrency/README.md`; PHPUnit does not run these.

Keep secrets and real external side effects out of examples and tests. Resolve actual failures;
do not suppress warnings to turn a failing check into an apparent pass. If local PHP has a
broken optional extension configuration, use a working INI or `php -n` only when all required
extensions are compiled in. Use available Git/gh authentication, without embedding credentials.

Finish with what changed and why, checks performed, commit/PR/release links and publication
status. Clearly identify an actual external blocker or any remaining maintainer action.
