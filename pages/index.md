---
title: NAF overview
---

# NAF overview { #what-naf-is }

NAF is a PHP microframework for HTTP applications and services. The core provides routing,
controller dispatch, a dependency injection container, configuration, events, logging and
error handling. Optional Composer packages add templates, forms, authentication, persistence
and background jobs.

Application code uses ordinary PHP classes and explicitly imported helper functions. Route
handlers return PSR-7 responses; controllers receive services through their constructors.
No base controller or application-wide ORM is required.

## Choose a starting point

| Goal | Guide |
|---|---|
| Pick a small, complete application to build | [Application scenarios](recipes/index.md) |
| Build a two-page website with a shared layout | [Small website](recipes/small-website.md) |
| Return JSON without configuring a database | [JSON API without a database](recipes/simple-json-api.md) |
| Build a website with templates and forms | [Install the starter](install.md#start-with-the-application-skeleton) |
| Build an HTTP service without templates or sessions | [Core-only installation](install.md#core-only-project) |
| Learn the layout and request handling | [Your first application](first-app.md) |
| Select packages for an existing application | [Choosing packages](choosing-packages.md) |

You need PHP 8.3 or newer and Composer. Individual packages require additional extensions;
the installation guide and package chapters name them.

## Target audience

The documentation assumes familiarity with PHP classes, namespaces, Composer and basic HTTP.
It explains NAF conventions as they are introduced. Start with the first application before
using reference fragments, which assume an application is already bootstrapped.

## Core features

| Capability | Responsibility | Guide |
|---|---|---|
| Routing and controllers | Match method/path pairs and invoke handlers | [Routing](routing.md), [Controllers](controllers.md) |
| HTTP messages | Read requests and create responses | [Requests and responses](request-response.md) |
| Services | Construct dependencies and share registered instances | [Dependency injection](dependency-injection.md) |
| Configuration | Load environment values and merge arrays | [Configuration](configuration.md) |
| Events and errors | Observe execution and customize failure responses | [Events](events.md), [Errors](errors.md) |
| Plugins | Discover installed packages and load their resources | [Plugins](plugins.md) |

The core uses PSR-7 messages, a PSR-11 container and PSR-3 logging. The optional `naf/client`
implements PSR-18. [Application lifecycle](lifecycle.md) explains boot and request handling.

## Design principles

NAF keeps application structure and optional capabilities separate from the HTTP core.
Install the packages needed for the application, configure their services and keep business
rules in application classes. Extend behavior through the container, events and plugin
interfaces rather than copying framework internals.

Your application defines validation rules, access policies, schemas, tests and deployment
settings. The [worked examples](recipes/index.md) show these responsibilities together.
