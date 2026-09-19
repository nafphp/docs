---
title: LDAP sign-in (naf/auth-ldap draft)
---

# Signing in against an LDAP directory

Contributor draft for `naf/auth-ldap`, which has no published release yet. Keep it out of
`pages/` until the package is on Packagist, then fold it into `pages/auth.md` as its own
section and rerun the documented checks.

## What it does

`LdapProvider` implements the `ProviderInterface` that NAF Auth already uses, so a directory
is one more named provider rather than a parallel login path. `DirectoryInterface` verifies
the credentials and checks an immutable subject; the host supplies the local account provider
it already has.

**No identity is created, and nothing is linked by email address.** The host supplies two
closures and they are the only link between a directory subject and a local account:

```php
accountForSubject(string $subject): ?string     // who is this, locally?
subjectForAccount(string $identifier): ?string  // and which subject is that account?
```

Both return `null` when no link exists, and `null` means no sign-in. The directory password
is never forwarded to the local account provider. Restoring a session checks the directory
subject again, so revoking someone in the directory ends their session rather than waiting
for it to expire. NAF Auth still enforces `isActive` and still rotates the session.

## What the connection requires

`NativeDirectory` refuses to be configured unsafely, at construction, before it opens
anything:

- LDAPS or mandatory StartTLS, with a trusted CA file that exists.
- Non-anonymous search credentials and a base DN.
- An immutable subject attribute, `entryUUID` by default.
- An allowed-account filter, wrapped in parentheses.
- A timeout between 1 and 30 seconds.

A URL carrying credentials, a base DN, a query string or a fragment is refused, as is an
attribute name that would break out of an LDAP filter. Filter values are escaped with
`LDAP_ESCAPE_FILTER`, referrals are disabled, an ambiguous search is refused rather than
guessed at, and a directory failure fails closed instead of falling back to local credentials.

!!! warning "Two things the plugin cannot decide for you"
    PHP and OpenLDAP keep TLS options **process-global**, so use one trust configuration per
    process. And the plugin cannot know how your directory marks an account disabled — put
    that in `allowedFilter` yourself, or a disabled account keeps signing in.

For Active Directory, configure the account attribute, the stable subject representation and
the disabled-account filter for your actual directory before enabling it. The adapter targets
textual subjects such as OpenLDAP's `entryUUID`.

## Before you enable it

The package's own tests use a fake directory: they cover linked, missing and revoked accounts,
rejected credentials, mapping failures and outages, and they check the configuration
boundaries without connecting to anything. That is a contract check, **not** evidence that
your directory works. Test against a real, trusted TLS directory before a deployment relies on
it, and do not present the fixture tests as a live verification.
