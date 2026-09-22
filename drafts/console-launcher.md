# Console shortcuts

Draft: waits for the release of the `naf/cli` launcher installer (planned v0.2.3).
Do not move into `pages/console.md` until the package is published and the examples pass
against that release. The Nafinity-specific section also requires its launcher changes.

## Generic applications

Composer exposes the console as `vendor/bin/naf`. With the launcher installer available,
run the following once from the directory containing the application's `composer.json`:

```sh
vendor/bin/naf-install
bin/naf command:list
```

Setup creates an executable POSIX shell shortcut and appends a `post-autoload-dump` hook
without removing existing hooks. Commit `bin/naf` and the manifest changes with your app.
Later Composer installs and autoload dumps restore a missing shortcut automatically, unless
scripts are disabled. Merely requiring `naf/cli` in an unprepared application does not create
`bin/naf`: Composer executes dependency binaries on request, but not dependency install
scripts. No Composer plugin execution permission is required.

Setup does not boot the application or need a working database. Existing conflicting files
and symlinks at `bin/naf` are left untouched and reported; there is no force-overwrite option.
An existing identical generated launcher is accepted. After removing `naf/cli`, the hook
becomes a no-op; the remaining shortcut reports missing dependencies. Remove the shortcut
and its hook when no longer needed.

The launcher supports project-relative `config.vendor-dir` and `config.bin-dir`. With a
custom binary directory, invoke its `naf-install` proxy for setup. If Composer already uses
`bin` as its binary directory, it already provides `bin/naf` and this installer is unnecessary.
Absolute binary/vendor paths and environment-only directory overrides are outside the setup
utility's supported configuration. The generated launcher requires a POSIX shell; it is not
a Windows CMD launcher. The usual Composer binary remains available.

## Runtime integration belongs to the application

By default the launcher invokes local `php` and the Composer console proxy. It finds the
application relative to its own location, so it also works when invoked from another working
directory. Arguments, standard input and command exit codes are preserved.

If the host provides an executable `bin/naf-runtime`, the launcher delegates to it instead.
That script receives the original arguments and owns the runtime choice. A present but
non-executable/broken adapter is an error, never a reason to silently execute locally.
Keep runtime customizations in this adapter instead of changing the generated shortcut.
`naf/cli` does not guess Docker Compose services or write container configuration.

## Nafinity

The skeleton includes the shortcut and Composer hook plus its own runtime adapter:

```sh
# From the repository root:
bin/naf command:list
bin/naf db:migrate up

# From app/:
bin/naf command:list
```

On the host, the adapter selects Compose service `app`, using a running service through
`docker compose exec`, or a disposable `docker compose run --rm --no-deps` container when
the service is stopped. Docker/Compose and dependencies such as the database must be
available; the command does not start dependency services automatically.

Inside Docker/Podman (detected through their usual marker files), or in an installation
without the skeleton's parent `compose.yaml`, it uses local PHP. Explicit overrides handle
other container environments or a deliberate local PHP setup:

```sh
NAF_CLI_RUNTIME=local bin/naf command:list
NAF_CLI_RUNTIME=compose NAF_CLI_SERVICE=app-test bin/naf command:list
```

Runtime values are `auto`, `local`, and `compose`. Service defaults to `app`. Interactive
terminals keep TTY support; piped/CI invocations disable it. Docker failures propagate without
falling back to local PHP. Docker execution needs no PHP installation on the host.
`make naf ARGS='command:list'` uses the same launcher.

## Verified behavior

- CLI unit tests cover independent/idempotent installation, preserving owner files and
  existing hooks, JSON objects, argument/input/exit forwarding, missing dependencies,
  invalid runtime adapters, custom paths and harmless hooks after removal.
- `naf/cli/tests/composer-install.sh` builds a disposable real Composer host with nested
  vendor and custom binary directories, exercises setup with a deliberately failing app
  bootstrap, regenerates a deleted shortcut, runs the actual console, and removes the package.
- Nafinity's `tests/console_launcher_test.py` checks running/stopped Compose service dispatch,
  failed probes, alternate services, local execution, piped input, argument boundaries,
  interactive TTY handling and installation hints.

Composer reference: https://getcomposer.org/doc/articles/scripts.md and
https://getcomposer.org/doc/articles/vendor-binaries.md.
