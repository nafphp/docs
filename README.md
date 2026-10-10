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

Read [DOCUMENTATION_STYLE.md](DOCUMENTATION_STYLE.md) before changing prose or examples.
The website has four tabs. **Learn** holds getting started and the tutorials; **Guides** groups
the chapters by reader task (fundamentals, web pages, data, background work, integrations,
security and identity, extending NAF, operating); **Reference** holds generated and lookup
pages; **Showcase** describes applications built with NAF. Each chapter declares package
requirements in front matter; the hook renders install commands and transitive dependencies
after its introduction. Keep existing page URLs and useful heading anchors when reorganizing
content: change `nav:` rather than moving files.

The Plugins section includes the [Flow chapter](pages/flow.md). Its complete PHP and
HTML-fragment example is copied into a fresh application and checked against the published
package by the example runner.

## Test what readers copy

```sh
python tools/test_examples.py
```

The test creates a fresh `composer create-project naf/app` installation and a separate core-only
project in temporary directories. The small website and storage-free JSON API each install
their own minimal dependency set in separate projects. It extracts the **actual file-titled Markdown blocks**,
lints their PHP and tests them through local HTTP servers. It checks HTML and JSON, validation,
escaping, CSRF, a local mail outbox, login persistence/logout/suspension, ORM save/find and
SQLite API persistence and errors, and database migrations (apply, repeat and roll back). It also exercises the documented
service/HTTP tests, plugin discovery, application commands, streamed downloads, queue failure/retry,
scheduling, MCP scopes and a fake HTTP transport. The small scenarios check shared layouts,
HTML escaping, bounded query input, response headers and sanitized JSON failures.
The Alexa example runs in its own minimal host and checks setup, doctor, OAuth discovery,
service tokens, JSON/SSE tool calls and revocation against the published packages.
It never sends mail externally. Temporary projects and servers are cleaned up, including on
test failure.

To reuse a starter that already has `naf/auth`, `naf/orm` and `naf/mail` installed:

```sh
python tools/test_examples.py --starter /absolute/path/to/nafphp-demo
```

That source directory is only read; tests run on copies. File-titled blocks are complete files;
untitled reference fragments are not automatically executable applications. Keep prerequisites,
file locations and expected results explicit when adding examples.

Give every fenced block a language: `php` for PHP files beginning with `<?php`, `php-inline`
for PHP fragments without an opening tag, and `html+php` for templates mixing HTML and PHP.
The configured `php-inline` lexer enables highlighting without adding a tag to the copied code.
Use `bash` for shell commands, `ini` for environment files and `text` for directory trees or
command output. Reserve file titles for complete files so the example runner can test them.

## Refresh screenshots and console output

```sh
pip install -r requirements-screenshots.txt
python -m playwright install chromium
python tools/capture_screenshots.py
```

The script builds the same fixtures as the example runner from the published starter and
packages, drives them with Playwright and writes WebP images to `pages/assets/screenshots/`
and command output to `snippets/output/`, which pages include with `--8<--`. Refresh both after
releases that change a visible page or a command's output, then review the images before
committing them. Screenshots show browser UI only; terminal output stays copyable text.
Every image needs alt text describing what the reader should notice.

## Refresh generated references

```sh
python tools/gen_reference.py
python tools/check_pages.py
mkdocs build --strict
```

The generator installs published `naf/*` libraries and reflects function signatures and
summaries, namespaces, versions, command definitions and configuration defaults. It excludes
`@internal` helpers. It writes `pages/function-index.md`, `pages/cli-commands.md`,
`pages/configuration-reference.md`, `pages/packages.md` and `tools/packages.json`; review and
commit them together. `--project`
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

[Code style](CODE_STYLE.md) defines the shared PER Coding Style 3.0 rules, readability
guidance and a formatter template for plugin repositories.
