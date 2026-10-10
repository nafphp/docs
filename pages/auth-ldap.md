---
title: LDAP authentication
requires:
  - naf/auth-ldap
---

# LDAP authentication { #signing-in-against-a-directory }

`naf/auth-ldap` verifies credentials against an LDAP directory through the existing Auth
provider contract. The application maps a verified directory entry to its own local identity.
Use it when an organization manages credentials in a directory but application accounts and
permissions remain local.

## How it fits

`LdapProvider` implements Auth's `ProviderInterface`. The directory verifies credentials;
explicit mapping callbacks associate a stable directory subject with a local account ID.
The local account provider supplies the identity and permissions.

| Callback | Input | Return |
|---|---|---|
| `accountForSubject` | Directory subject string | Local account ID, or `null` if unlinked |
| `subjectForAccount` | Local account ID string | Directory subject, or `null` if unlinked |

The plugin does not create accounts or link by email. Store links in application-owned
persistence and use the immutable directory subject, rather than a changeable username.
A missing link prevents authentication.

The directory alone verifies the submitted password. After a successful bind, the local
account provider is called through `find()` to load the linked identity; its `authenticate()`
method never receives the directory password. Keep local account loading separate from
directory credential verification when adapting this integration.

Session restoration calls the directory again through `find()`. A missing or disallowed
subject prevents restoration; directory outages throw instead of falling back to local
credentials. Auth also checks local account activity. With session persistence enabled,
successful login rotates the session ID.

## Configuring the connection

Install PHP's `ext-ldap` and provide a readable trusted CA file. `NativeDirectory` validates
these constructor settings before opening a connection:

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

!!! warning "TLS trust and disabled accounts"
    PHP/OpenLDAP TLS options are process-global. Use a consistent trust configuration for
    directories accessed by the same process.

    Configure `allowedFilter` to exclude disabled accounts according to your directory's
    schema. The default object-class filter alone does not enforce that rule.

For Active Directory, set the account attribute, the stable subject representation and the
disabled-account filter to match your directory before enabling it. The shipped adapter
targets textual subjects such as OpenLDAP's `entryUUID`.

## Register the provider

This reference fragment belongs in root `bootstrap.php`, before `app()->run()`. It assumes:

- `$accounts` implements `ProviderInterface` for existing local accounts.
- `$accountForSubject` and `$subjectForAccount` are closures implementing the mappings above.
- `ldap:url`, `ldap:base_dn`, `ldap:bind_dn`, `ldap:bind_password`, `ldap:ca_file` and
  `ldap:allowed_filter` are application configuration strings.

Keep the service password in a protected environment value. These application configuration
keys are read by this fragment; the plugin does not discover or register a provider from them.

```php-inline
use Naf\Auth\Ldap\LdapProvider;
use Naf\Auth\Ldap\NativeDirectory;
use function Naf\config;
use function Naf\Auth\auth;

$directory = new NativeDirectory(
    url: config('ldap:url'),
    baseDn: config('ldap:base_dn'),
    bindDn: config('ldap:bind_dn'),
    bindPassword: config('ldap:bind_password'),
    caFile: config('ldap:ca_file'),
    allowedFilter: config('ldap:allowed_filter'),
);

$provider = new LdapProvider($directory, $accountForSubject, $subjectForAccount, $accounts);
auth()->addProvider('directory', $provider);
```

Pass `'directory'` as the provider name when calling `auth()->authenticate()` with
`PasswordCredentials`. See [multiple account sources](auth.md#several-sources). Optional
`NativeDirectory` arguments default to `usernameAttribute: 'uid'`,
`subjectAttribute: 'entryUUID'` and `timeout: 5` seconds.

## Verify the directory integration { #before-you-rely-on-it }

Before deployment, test a linked active account, an unlinked account, an incorrect password,
a disabled directory subject, a disabled local account and a directory outage against your
actual trusted TLS directory. Verify that restoration after disabling a subject fails on the
next request. Do not log submitted passwords.

The package's fake-directory tests verify provider contracts and configuration rejection.
They do not verify your network, certificate trust, directory schema or account mappings.
