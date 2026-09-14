# NAF documentation

The documentation source is `pages/`; `mkdocs.yml` defines navigation. The generated website
in `site/` is ignored. Read [the installation guide](pages/install.md) to build an application.
The current recipes target the published NAF 0.2 releases, not unreleased sibling checkouts.

## Preview and check

From this repository, with Python 3.9+, PHP 8.3+ (including `mbstring` and `pdo_sqlite`) and Composer:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python tools/check_pages.py
mkdocs build --strict
mkdocs serve
```

Navigation comes in three levels: installation and first app, complete worked examples,
then topic references. Each chapter declares optional packages in front matter; the hook
renders the install command and transitive dependencies. Previous/next links follow navigation.

## Test what readers copy

```sh
python tools/test_examples.py
```

The test creates a fresh `composer create-project naf/app` installation and a separate core-only
project in temporary directories. It extracts the **actual file-titled Markdown blocks**,
lints their PHP and tests them through local HTTP servers. It checks HTML and JSON, validation,
escaping, CSRF, a local mail outbox, login persistence/logout/suspension, ORM save/find and
SQLite API persistence and errors. It never sends mail externally. Temporary projects and
servers are cleaned up, including on test failure.

To reuse a starter that already has `naf/auth`, `naf/orm` and `naf/mail` installed:

```sh
python tools/test_examples.py --starter /absolute/path/to/nafphp-demo
```

That source directory is only read; tests run on copies. File-titled blocks are complete files;
untitled reference fragments are not automatically executable applications. Keep prerequisites,
file locations and expected results explicit when adding examples.

## Refresh generated references

```sh
python tools/gen_reference.py
python tools/check_pages.py
mkdocs build --strict
```

The generator installs published `naf/*` libraries and reflects function signatures, namespaces
and versions. It excludes `@internal` helpers. It writes `pages/function-index.md`,
`pages/packages.md` and `tools/packages.json`; review and commit them together. `--project`
accepts an existing installation containing all documented packages and requires no download.

`check_pages.py` recursively checks all chapters, including `pages/recipes/`, against that
snapshot: package names, helper imports, NAF class imports and CLI commands. The strict MkDocs
build checks links, anchors and navigation. CI refreshes the release inventory and runs the
HTTP checks on pull requests; deployment only runs on `main` after checks pass.

For a machine with a broken optional PHP extension configuration, the scripts accept command
overrides without changing application files:

```sh
export PHP_COMMAND='php -n'
export COMPOSER_COMMAND='php -n /absolute/path/to/composer'
```

Use `-n` only if the required extensions are compiled into that PHP binary; otherwise supply a
working INI configuration. The tutorial requires framework 0.2.2+ and form 0.2.1+; starter
0.2.2 already locks newer compatible versions. Redirects use the framework directly, without
the old protocol-normalization listener. The test runner exercises the untouched published
starter before adding recipe dependencies, so a broken starter lock cannot be hidden by an update.

## Contributor and agent guidance

Read [the shared workflow](AGENT_WORKFLOW.md) for NAF conventions and contribution permissions,
and [the release procedure](RELEASING.md) when preparing or publishing a package. Each plugin
repository provides its own `AGENTS.md` with its API, extension points and verification commands.
These contributor documents are maintained here so standalone plugin clones can link to one source.
