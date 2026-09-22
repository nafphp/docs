# Automatic plugin boot order experiment

This draft describes the `codex/automatic-plugin-order` experiment. It is not a released
installation recipe. Framework support is targeted at 0.2.7; package code and metadata must
be reviewed and published before these instructions move into the public plugin guide.

## Contract

Installed `naf-plugin` packages declare ordering in their own `composer.json`:

```json
{
  "extra": {
    "naf": {
      "boot": {
        "before": ["naf/board"],
        "after": ["naf/schedule"]
      }
    }
  }
}
```

Both fields are optional lists of exact Composer package names. They apply only to installed
plugins: an absent optional target is reported and skipped, never installed by the boot
resolver. Mandatory package/API requirements belong in Composer `require`. That field is
not a bootstrap edge: a Board extension requires Board's classes but notes its providers
before Board initializes them. Both example manifests now declare their actual Board
requirement; the obsolete `fkde/nafinity` host metadata is removed in a separate prior commit.

The framework discovers all plugin paths through Composer, reads their static manifests,
and computes the full order before executing plugin code. No container lookup, listener,
new lifecycle event, or application-specific rule is used by the resolver. Invalid metadata,
invalid JSON, self-dependencies and cycles fail before the first plugin bootstrap. A cycle
message includes the actual cyclic path and the declarations that produced its edges;
packages merely blocked downstream are not falsely described as members of the cycle.

An optional `app/plugins.php` (preferred) or `src/plugins.php` returns the familiar list.
Installed listed packages keep their relative order and get priority among ready plugins.
Names of packages not installed are ignored as before; duplicates are collapsed.
A list that contradicts declared dependencies fails with a cycle naming `host plugins.php`.
It cannot silently force an unsafe order. Unconstrained ties use package names, so discovery
order does not change the result. Legacy plugins without metadata participate normally.

All plugins are still registered before any bootstrap runs. The computed registry order also
governs plugin configuration and view-resource precedence; it is not a separate hidden order.
Host configuration and host routes retain their existing override precedence. Providers in
Board retain their separate index/id ordering and finish before host extensions and routes.

## Diagnostics and migration

`naf plugins:debug` displays the order, incoming prerequisite edges with their source, and
absent optional targets. On an older framework it reports the unsupported capability with
exit code 1. `App::getPluginBootPlan()` exposes the same data without requiring the CLI plugin.
Malformed boot graphs fail before CLI startup; their exception already identifies the cause.

Plugins that register CLI commands during bootstrap declare `after: ["naf/cli"]`: database,
MCP, OAuth client, queue, RBAC, scheduler and WebSocket. Scheduler also declares queue.
Board declares its infrastructure prerequisites; both examples declare `before: ["naf/board"]`.
No plugin needs to know which other optional Board extensions are installed. The skeleton's
normal plugin-order file is removed. The manual-order acceptance phase creates a temporary
list of only the two examples and removes it afterwards.

Validation must cover resolver errors, isolated app boot, configuration and named-route
precedence, CLI diagnostics, both databases, HTTP, workers, extension installation, reversed
manual preference, host overrides and extension removal with no normal host plugin list.
