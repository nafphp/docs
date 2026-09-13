---
title: What NAF is
---

# What NAF is

NAF is a PHP microframework: routing, a container, configuration, events and error
handling, and nothing else. Everything past that — templates, forms, sessions, a database,
a queue — is a separate package you install when you need it and never think about when
you do not.

That is the whole idea, and it has a cost worth naming: a fresh NAF application cannot
render an HTML page until you decide how you want to. In exchange, an application that
only answers JSON never carries a template engine, and one that has no forms never starts
a session.

If you are not sure which pieces your project needs,
[start with the scenarios](choosing-packages.md).

## Target Audience

NAF is designed for developers who need:

- Full control over their application's structure
- Minimal dependencies and maximum flexibility
- Native PHP capabilities with PSR compliance (PSR-3, PSR-4, PSR-7, PSR-11, PSR-18)
- A framework that stays out of the way while providing necessary functionality

## Core Features

NAF includes:

- **Routing** for URL handling and HTTP method mapping
- **Controllers** for organizing request handling logic
- **Response helpers** for explicit HTML, JSON and redirects
- **Dependency injection**, configuration, events and error handling
- **Plugin System** for extending functionality
- **PSR Compatibility** for integration with the PHP ecosystem

Templates (`naf/view`), database access (`naf/database`) and sessions (`naf/session`)
are optional plugins, described in [Choosing packages](choosing-packages.md).
PSR-18 support comes from the optional `naf/client` package.

## Design Principles

NAF focuses on providing just enough structure without imposing architectural decisions. The framework:

- Uses plain PHP wherever possible
- Avoids complex abstractions and magic methods
- Keeps dependencies to a minimum
- Follows PSR standards for interoperability

Use NAF as a foundation for APIs, web applications, or any PHP project that values **clarity**, **speed**, and **simplicity**.

