---
title: Authentication architecture
requires:
  - naf/auth
---

# Authentication architecture { #why-auth-has-this-shape }

Auth separates credential verification, identity loading, authorization and persistence.
[Authentication](auth.md) explains usage; this chapter describes how its services cooperate
and which guarantees depend on the application provider.

## One implementation per question

`Auth` owns permission checks and the current identity. `auth()->user()` returns the
provider's identity object. `IdentityInterface` exposes the identifier, roles and permissions;
`UserInterface` adds activity and profile information.

`can('a', 'b')` requires both permissions; `canAny('a', 'b')` accepts either. Per-object
`allows($action, $resource)` checks a registered policy independently of global grants.
No policy means denial. Applications register providers and policies in their bootstrap.

## Provider responsibilities { #the-provider-is-the-seam }

`ProviderInterface` declares `authenticate()` and `find()`. Everything a backend needs — a PDO
connection, an LDAP handle, an HTTP client — is a constructor dependency of the provider, resolved
through the container when it is registered by class name.

- `PasswordProvider` verifies passwords and uses a decoy hash for unknown accounts to reduce
  timing differences between unknown-account and incorrect-password paths.
- `OrmProvider` is the ORM implementation. It maps a repository and three column names onto
  those two questions, and requires the model to implement `IdentityInterface` — that requirement is
  what keeps `auth()->user()` returning the application's own class instead of a wrapper.
- Providers registered by name are resolved lazily and cached, so registering five sources in
  `bootstrap.php` does not construct them until authentication or identity loading needs them.

## Persistence

`StateStoreInterface` reads, writes and clears exactly two values: the source name and the
identifier. Never the model, never the grants.

- Restoration reloads through `find()` and compares the returned identifier against the stored one,
  so a provider that hands back somebody else cannot silently swap the person. A missing account,
  an unregistered source or a malformed record clears the record instead of falling back.
- That comparison lives in `load()`, and `restore()` calls it. The public method exists because
  external logins and CLI tools need the same reload, and a second copy of the check is a second
  place for it to drift. `load()` returns null where restoration would clear the record; deciding
  what that means is the caller's job, so it touches no session state of its own.
- `SessionStateStore` rotates the session ID on login and verifies that it actually changed. A
  rotation that does not happen aborts the login rather than publishing a person onto the guest's ID.
- `SessionStateStore` receives its session through constructor injection. The bootstrap creates
  the store lazily when the manager needs persistence. No service starts a session in its constructor.
- The manager factory prefers a custom `StateStoreInterface` binding, then honours `auth:session`:
  false disables persistence, null enables it when `naf/session` is installed, true requires it.

## Wiring

`bootstrap.php` is the composition root. It registers `Auth`, `PasswordHasher`, `SessionStateStore`,
`DatabaseProvider` and `OrmProvider` as lazy container factories. The manager factory visibly calls
`addProvider()` for `auth:providers` and `policy()` for `auth:policies`. No source is enabled by default.
Custom bindings take precedence. `auth()` only gets the manager; it never registers services.

The providers receive their dependencies explicitly. The ORM repository is resolved or created by
`RepositoryFactory` in the bootstrap; neither the ORM provider nor the session adapter accesses
the global container. Providers registered by class name use the resolver injected into `Auth`,
which calls container `get()`. There is no implicit `new $class()` or `make()` fallback.

The PDO identity factory is also supplied by the bootstrap. It creates a fresh identity per lookup;
identities and credentials are data, not container singletons. Exceptions are created where errors
occur. Service construction and registration belong in the bootstrap, including application-owned
provider factories and any imperative policy/provider registrations.

Boot the auth plugin before using `auth()`, and resolve it after dependency plugins have booted.
Lazy factories allow registration before the session, PDO or ORM services exist. Missing or
incorrectly ordered dependencies fail when the manager is resolved.

Authorization exceptions expose
`getStatusCode()` so the framework error handler renders 401 and 403 instead of a generic 500; they
carry the same value as their exception code and stay usable outside HTTP.

## What the plugin guarantees

- With `SessionStateStore`, a login rotates the session ID or fails.
- Restoration distinguishes sources even when identifiers collide, and re-reads grants every request.
- A resource policy that denies — or the absence of one — is never bypassed by a global permission.
- Password providers verify a decoy hash for unknown usernames to reduce timing differences. Credentials are marked `#[\SensitiveParameter]` and
  `PasswordCredentials` redacts its debug output. Nothing but a source name and an identifier is
  persisted.
- A failed attempt leaves an existing login intact. Call `logout()` first if reauthentication should
  end the current session.

## What it leaves to the application

Password policy, rate limiting, lockout, MFA and invitation flows are account-lifecycle decisions.
Business rules such as last-admin protection or delegation caps belong in policies, next to the
mutation they guard. The session adapter inherits the storage and cookie guarantees of
`naf/session`; there is no token revocation store and no distributed limiter here.

## Plain PDO accounts

`DatabaseProvider` extends the existing password provider and accepts a PDO connection directly.
It provides parameterized lookup by username/identifier and password-hash upgrades without ORM
or database-plugin dependencies. A row mapper optionally creates the application identity or
rejects disabled accounts; the password hash stays out of the mapped row. The provider retains the hash of the current lookup for the synchronous PasswordProvider
verification flow, avoiding a second query. The mapper runs before that hash is assigned, so
a nested lookup from the mapper cannot replace the outer authentication's hash. Rehash updates
compare the original hash so concurrent resets are not overwritten. Table/column names are validated and quoted; ambiguous accounts fail.
