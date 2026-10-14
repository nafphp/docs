---
title: API compatibility and support
---

# API compatibility and support

NAF packages have independent versions. Select compatible versions through Composer and
check the [package inventory](packages.md), each package's manifest and its release notes
before updating. The framework core and optional plugins do not need the same version number.

## Public API

The supported application and extension API consists of:

- Public namespaced helpers listed in the [function index](function-index.md).
- Services, methods, interfaces and exceptions documented in the topic guides.
- Configuration keys and their merge rules.
- Conventional application and plugin resource paths, plugin discovery and declared boot ordering.
- Dispatched lifecycle events, their payload order, listener priority and documented return handling.

Parameter names are part of the PHP API because callers can use named arguments. An event
constant alone does not establish a dispatch point or a consumed return value; use the
[event reference](events.md#request-lifecycle). The core does not dispatch `request.body`
or `request.end`.

Declarations marked `@internal`, private members and undocumented implementation details
are outside this contract. Use the application, container and plugin APIs rather than
calling file-loader, app-holder or boot-planning internals directly.

## Versioning and deprecation

NAF follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html). During the current
0.x phase, minor versions can change the public API. Patch releases aim to preserve
documented use while correcting defects; release notes identify observable behavior
changes and required migration steps. Review those notes even for patch updates.

Deprecated APIs are identified in source and documentation together with their replacement
or intended removal. Prefer the documented replacement when updating an application.
A future 1.0 establishes the supported public API for the 1.x series: additions remain
compatible, and incompatible public API removals require a new major version.

## Runtime and maintenance

The framework's 0.2 line supports PHP 8.3 and newer. Individual packages declare their
runtime, extension and dependency requirements in `composer.json`; development tools can
have additional requirements. Check the package's CI workflow for the combinations actually
tested. An application's optional integrations may require extensions beyond the core.

Maintenance targets the latest stable release of each package. Older release lines do not
have a guaranteed backport or fixed support period. Check release notes and update to a
compatible maintained version when a fix becomes available.

## Updating applications

Commit or back up application code and dependency files before an update. Review the
release notes between the installed and intended versions, resolve Composer's dependency
constraints and run the application's tests, including its HTTP and plugin integrations.
Restart persistent workers after deployment.

The starter's committed lock file describes its initial dependencies. Existing applications
receive library fixes by updating their own dependencies; installing a newer starter is a
separate operation. See [starter versions and updates](install.md#starter-versions-and-updates)
and [deployment](deployment.md).

## Upgrading to Framework 0.2.12

Existing applications continue to start with `app()->run()`. The additional
[`handle()` entry point](lifecycle.md#handle-a-supplied-request) is optional.
Update the dependency, commit the resulting lock file and run your application tests:

```bash
composer require 'naf/framework:^0.2.12' --with-all-dependencies
```

Review these observable corrections:

- An unsupported method on a known path returns 405 with `Allow`; an unknown path remains 404.
- HEAD can invoke a GET handler. Keep GET free of write side effects or register an explicit HEAD route.
- Automatic OPTIONS returns 204 for known paths without invoking a controller. Register an explicit route for application behavior.
- URL placeholders require strings or integers; missing or invalid values throw `InvalidArgumentException`.
- Custom writable containers implement [`MutableContainerInterface`](dependency-injection.md#custom-writable-containers). PHP rejects unsupported containers before boot.
- Handlers return PSR-7 responses. The undocumented `-1` exit sentinel now produces a dispatcher error; replace it with an ordinary response.

The core no longer requires PDO, but database integrations still require it and their drivers.
Composer also resolves Nyholm PSR-7 1.8.2 or newer, avoiding PHP 8.4/8.5 deprecations in
older versions. The release includes the [request authority correction](request-response.md#request-uri-and-host):
a container listen port no longer changes an authority supplied without a port in `Host`.

`Event::REQUEST_BODY` and `Event::REQUEST_END` remain defined as deprecated compatibility
constants and are not dispatched. AppHolder, CoreFileLoader, PluginBootOrder and Stopwatch
are internal implementation details; use documented application and plugin APIs.
