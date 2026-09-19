---
title: Signing in against a directory
requires:
  - naf/auth-ldap
---

# Signing in against a directory

An organisation that already has an LDAP directory does not want a second list of people.
`naf/auth-ldap` lets the directory verify the password while the local account stays where it
is, and stays the account.

## How it fits

`LdapProvider` implements the same `ProviderInterface` that NAF Auth already uses, so a
directory is one more named provider rather than a second login path beside the first. The
directory checks the credentials; your application decides which local account that person is.

That decision is two closures, and they are the only link between the two worlds:

```php
accountForSubject(string $subject): ?string     // who is this, locally?
subjectForAccount(string $identifier): ?string  // and which subject is that account?
```

Both return `null` when no link exists, and `null` means no sign-in.

!!! warning "Nothing is created, and nothing is matched by email"
    An unknown directory subject does not become an account. Two people with the same address
    do not become the same person. If you want a directory user to have an account here,
    something in your application has to link them on purpose.

The directory password is never forwarded to the local account provider. Restoring a session
checks the directory subject again, so revoking somebody in the directory ends their session
rather than leaving it valid until it expires. NAF Auth still enforces `isActive` and still
rotates the session on sign-in.

## Configuring the connection

`NativeDirectory` refuses an unsafe configuration at construction, before it opens anything:

- LDAPS, or StartTLS made mandatory, with a CA file that exists.
- Non-anonymous search credentials and a base DN.
- An immutable subject attribute — `entryUUID` by default.
- An allowed-account filter, parenthesised.
- A timeout between 1 and 30 seconds.

A URL carrying credentials, a base DN, a query string or a fragment is refused, as is an
attribute name that would break out of an LDAP filter. Values are escaped with
`LDAP_ESCAPE_FILTER`, referrals are disabled, an ambiguous search is refused rather than
guessed at, and a directory that cannot be reached fails closed instead of falling back to
local credentials.

!!! warning "Two things this package cannot decide for you"
    PHP and OpenLDAP keep TLS options **process-global**. Use one trust configuration per
    process; a second one does not override the first, it fights it.

    And nothing here knows how *your* directory marks an account as disabled. Put that in
    `allowedFilter` yourself, or a disabled account keeps signing in.

For Active Directory, set the account attribute, the stable subject representation and the
disabled-account filter to match your directory before enabling it. The shipped adapter
targets textual subjects such as OpenLDAP's `entryUUID`.

## Before you rely on it

The package's own tests use a fake directory: linked, missing and revoked accounts, rejected
credentials, mapping failures in both directions, outages, and the configurations that must be
refused. That is a contract check.

**It is not evidence that your directory works.** Test against a real, trusted TLS directory
before a deployment depends on it, and do not present the fixture tests as a live
verification.
