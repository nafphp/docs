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

For individual topics, start with [Routing](routing.md), [Controllers](controllers.md),
[Views and templates](views.md), [Forms and validation](forms.md) or
[Dependency injection](dependency-injection.md). The navigation lists the full set of chapters.

## A first route

```php title="app/routes.php"
<?php

use function Naf\{json, route};

route()->add('GET', '/hello/{name}', function (string $name) {
    return json(['hello' => $name]);
}, 'hello');
```

```bash
curl http://127.0.0.1:8000/hello/Ada
```

```text
{
    "hello": "Ada"
}
```

The placeholder `{name}` reaches the closure's `$name` argument, and `json()` returns a PSR-7
response with `Content-Type: application/json; charset=UTF-8`. [Your first
application](first-app.md) builds this endpoint and an HTML page step by step.

## Choose a starting point

You need PHP 8.3 or newer and Composer. Individual packages require additional extensions;
the installation guide and package chapters name them.

<div class="grid cards" markdown>

-   :material-download-outline:{ .lg .middle } **Install the starter**

    ---

    Create a project with a working welcome page, templates and forms.

    [:octicons-arrow-right-24: Installation](install.md)

-   :material-school-outline:{ .lg .middle } **Build your first application**

    ---

    An HTML page and a JSON endpoint, with every file and the expected results.

    [:octicons-arrow-right-24: Your first application](first-app.md)

-   :material-map-outline:{ .lg .middle } **Pick a scenario**

    ---

    Small website, JSON APIs, contact form or login: complete, tested examples.

    [:octicons-arrow-right-24: Application scenarios](recipes/index.md)

-   :material-package-variant:{ .lg .middle } **Choose packages**

    ---

    Find the optional package for templates, persistence, identity or jobs.

    [:octicons-arrow-right-24: Choosing packages](choosing-packages.md)

-   :material-console:{ .lg .middle } **HTTP service without templates**

    ---

    Start from the core alone for webhooks and JSON services.

    [:octicons-arrow-right-24: Core-only installation](install.md#core-only-project)

-   :material-book-open-variant:{ .lg .middle } **Look something up**

    ---

    Function signatures, published packages and their versions.

    [:octicons-arrow-right-24: Function index](function-index.md)

</div>

If this is your first time using NAF, install the starter and follow Your first application.
You can learn the core concepts as you use them; there is no need to read every reference
chapter first.

## Target audience

The documentation assumes familiarity with PHP classes, namespaces, Composer and basic HTTP.
It explains NAF conventions as they are introduced. Start with the first application before
using reference fragments, which assume an application is already bootstrapped. The small
website and JSON API tutorials also provide complete setup in their own directories.

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
