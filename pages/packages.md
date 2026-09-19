---
title: Package overview
---

# Package overview

What there is, what it requires and what it suggests. Generated from the
`composer.json` of the published packages.

| Package | Version | Requires | Suggests | PHP |
|---|---|---|---|---|
| **`naf/framework`**<br><span style="font-weight:400">NAF - the ultra-light, functional PHP framework for fast microservices and APIs.</span> | `v0.2.5` | — | — | `>=8.3` |
| **`naf/auth`**<br><span style="font-weight:400">Authentication and permission checks for NAF, with your own user model.</span> | `v0.2.2` | `naf/framework` | `naf/orm`, `naf/session` | `>=8.3` |
| **`naf/auth-ldap`**<br><span style="font-weight:400">Optional TLS LDAP provider using the existing NAF Auth contract.</span> | `v0.1.0` | `naf/auth` | — | `>=8.3` |
| **`naf/cli`**<br><span style="font-weight:400">NAF CLI Plugin for console applications.</span> | `v0.2.2` | `naf/framework` | — | `>=8.3` |
| **`naf/client`**<br><span style="font-weight:400">NAF Client Plugin to make simple http requests.</span> | `v0.2.2` | `naf/framework` | — | `>=8.3` |
| **`naf/database`**<br><span style="font-weight:400">NAF Database Plugin to work with various storage solutions.</span> | `v0.2.2` | `naf/framework` | — | `>=8.3` |
| **`naf/form`**<br><span style="font-weight:400">NAF Form Plugin to make form handling easier.</span> | `v0.2.3` | `naf/framework`, `naf/session` | — | `>=8.3` |
| **`naf/i18n`**<br><span style="font-weight:400">NAF Internationalization Plugin</span> | `v0.2.2` | `naf/framework` | — | `>=8.3` |
| **`naf/mail`**<br><span style="font-weight:400">NAF Mail Plugin for quick email communication.</span> | `v0.2.2` | `naf/framework` | — | `>=8.3` |
| **`naf/mcp`**<br><span style="font-weight:400">NAF MCP Plugin for basic AI driven workflows.</span> | `v0.2.3` | `naf/framework` | — | `>=8.3` |
| **`naf/oauth-client`**<br><span style="font-weight:400">Sign in with external OAuth2 and OpenID Connect providers, keeping your own user model.</span> | `v0.2.3` | `naf/auth`, `naf/framework`, `naf/session` | `naf/cli`, `naf/client`, `naf/database`, `naf/view` | `>=8.3` |
| **`naf/oauth-server`**<br><span style="font-weight:400">Run your application as an OAuth2 authorization server and protect its APIs.</span> | `v0.2.2` | `naf/auth`, `naf/form`, `naf/framework`, `naf/session` | `naf/cli`, `naf/database`, `naf/view` | `>=8.3` |
| **`naf/orm`**<br><span style="font-weight:400">NAF ORM Plugin.</span> | `v0.2.2` | `naf/database`, `naf/framework` | — | `>=8.3` |
| **`naf/queue`**<br><span style="font-weight:400">NAF Queue Plugin for asynchronous jobs.</span> | `v0.2.3` | `naf/cli`, `naf/framework` | — | `>=8.3` |
| **`naf/schedule`**<br><span style="font-weight:400">NAF Schedule Plugin for recurring Tasks.</span> | `v0.2.3` | `naf/framework`, `naf/queue` | — | `>=8.3` |
| **`naf/session`**<br><span style="font-weight:400">NAF Session Plugin for storing data across requests.</span> | `v0.2.2` | `naf/framework` | `naf/database` | `>=8.3` |
| **`naf/storage`**<br><span style="font-weight:400">Provider-independent file storage with named disks and streams for NAF.</span> | `v0.1.0` | `naf/framework` | `naf/client` | `>=8.3` |
| **`naf/view`**<br><span style="font-weight:400">NAF View Plugin with simple templating.</span> | `v0.2.2` | `naf/framework` | — | `>=8.3` |
