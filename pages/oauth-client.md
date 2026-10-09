---
title: OAuth client
requires:
  - naf/oauth-client
---

# OAuth client { #signing-in-with-a-provider }

`naf/oauth-client` integrates external OAuth 2.0 and OpenID Connect sign-in with NAF Auth.
It supplies protocol routes and verification; the application configures providers and maps
external identities to local accounts.

Before enabling a provider, configure the public URL, credentials, local account source and
link storage. Run the setup and migration steps below, then verify the complete redirect and
callback flow. Provider API access after login is a separate opt-in integration.

## Protocol verification { #what-this-plugin-is }

`ExternalIdentity` contains the verified issuer, subject and claims. Map that external
identity to a local account before completing sign-in.

The plugin applies these protocol checks:

| Check | Behavior |
| --- | --- |
| **PKCE** | S256, always, for confidential clients too |
| **`state`** | random, stored server-side, consumed once |
| **`nonce`** | issued and checked against the ID token |
| **Signature** | always verified against the provider's published keys, wherever there is an ID token |
| **Algorithm** | pinned to what the provider publishes, never read from the token's own header |
| **Claims** | `iss`, `aud`, `exp`, `iat`, `nonce`, `sub` are checked; `azp` is checked when present |
| **Metadata** | the document has to name the issuer you configured before anything in it is used |
| **Redirect URI** | derived from your public URL, sent exactly, never taken from a request |
| **Transport** | https only, and no redirects followed while credentials are in flight |
| **Key rotation** | an unknown key id reloads the key set, once, with a cooldown |

A provider whose keys cannot be read makes the login **fail**. It never makes the check optional.

The configured issuer establishes which provider is trusted. Discovery metadata must name
that issuer before its endpoints and keys are used. Unavailable keys do not disable token
verification; they cause the login to fail.

Provider tokens are not stored by default. Enable encrypted token storage only when the
application needs to call provider APIs after login; see
[Calling the provider afterwards](#calling-the-provider-afterwards).

---

## Configuration

### Google

Add these keys to the array returned by `app/config.php`:

```php-inline
// app/config.php
return [
    'public_url' => 'https://example.com',
    'auth' => [
        'users'  => ['model' => App\Models\User::class],
        'logins' => [
            'google' => [
                'client_id'     => $_ENV['GOOGLE_CLIENT_ID'],
                'client_secret' => $_ENV['GOOGLE_CLIENT_SECRET'],
            ],
        ],
    ],
];
```

The configuration selects the local account model, public URL and external login. The
plugin registers callback routes and uses the configured account and session services.
Create the link table using the migration steps in this chapter.

The diagnostic commands need `composer require naf/cli`.
For the API-call example later, also install `naf/client`.

Inspect the callback URL to register in the provider console:

```bash
vendor/bin/naf oauth:discover google
```

It reads the provider's metadata, proves the setup resolves, and prints the callback URL to
paste into their console.

**`public_url` is required and has no default.** Inside a request the only candidates are the
`Host` and `X-Forwarded-*` headers, and those are set by whoever is calling. Every redirect URI
is built from this one value, so it is stated once rather than guessed.

### One provider, several logins

The key names the login; `driver` says which provider is behind it. Keeping them apart is what
lets you offer the same provider twice under names of your choosing:

```php-inline
'logins' => [
    'staff'    => ['driver' => 'microsoft', 'tenant' => 'acme.example', 'client_id' => …, 'client_secret' => …],
    'partners' => ['driver' => 'microsoft', 'tenant' => 'partner.example', 'client_id' => …, 'client_secret' => …],
],
```

Each gets its own callback (`/auth/staff/callback`, `/auth/partners/callback`), its own button
and its own credentials. Without a `driver`, the key is the driver — which is why `google` above
needs nothing else.

### Microsoft

Microsoft needs one more thing: **which accounts may sign in.**

```php-inline
'microsoft' => [
    'client_id'     => $_ENV['MS_CLIENT_ID'],
    'client_secret' => $_ENV['MS_CLIENT_SECRET'],
    'tenant'        => '8f3a1c94-…',   // directory id, or a verified domain
],
```

A single named tenant pins the issuer by itself. The multi-tenant values — `common`,
`organizations`, `consumers` — mean *any* organisation in the world may sign in, so they will
not start without you saying who:

```php-inline
'tenant'          => 'common',
'allowed_tenants' => ['8f3a1c94-…', 'b21d…'],   // or ['*'] to accept everyone
```

Without `allowed_tenants` the setup raises a `ConfigurationException` naming the key. This is
deliberate: with `common`, Microsoft's discovery document gives its issuer as a *template*, and
the real issuer is only known from the token's own tenant id. Substituting it is safe **because**
the tenant is then checked against your list.

### Any other OpenID Connect provider

Configure the issuer. Endpoints and signing keys are obtained from its discovery document.

```php-inline
'keycloak' => [
    'issuer'        => 'https://id.example.com/realms/main',
    'client_id'     => …,
    'client_secret' => …,
],
```

### GitHub, and other providers without OpenID Connect

```php-inline
'github' => [
    'client_id'     => $_ENV['GITHUB_CLIENT_ID'],
    'client_secret' => $_ENV['GITHUB_CLIENT_SECRET'],
],
```

GitHub has no discovery document and issues no ID token, so its endpoints are named in the
preset rather than read from it. Its quirks are handled for you: the credentials go where GitHub
documents them, its API version header is sent, and an address the person has not made public is
fetched from their verified address list instead of coming back empty.

**Naming a profile endpoint does not make a provider plain OAuth2.** Protocol and profile are
separate: give an OpenID Connect provider a `userinfo_url` and it stays OpenID Connect — the ID
token is verified first, the profile is fetched afterwards, and it is only accepted if it
describes the same subject. It adds to a verified identity; it never establishes one.

A provider is plain OAuth2 when it has no issuer. Such a provider takes three URLs and, if it
does not call its identifier `sub`, the field that holds it:

```php-inline
'acme' => [
    'client_id'     => …,
    'client_secret' => …,
    'authorize_url' => 'https://acme.test/oauth/authorize',
    'token_url'     => 'https://acme.test/oauth/token',
    'userinfo_url'  => 'https://acme.test/api/me',
    'subject_field' => 'user_id',
],
```

For GitLab, select the OpenID Connect path with `issuer` set to `https://gitlab.com`,
together with the client credentials and application settings described above.

#### Two trust paths, and the difference between them

With OpenID Connect the provider signs a statement addressed to this application, and both the
signature and the address are verified. Without it there is nothing to sign: the identity comes
from an authenticated call to the provider's API with the access token just exchanged for the
code.

Plain OAuth 2.0 sign-in relies on the authorization-code exchange and an authenticated
profile request. It has no signed ID token with an audience and nonce to verify. Use
OpenID Connect where the provider supports it.

Plain OAuth 2.0 identities use `oauth:<provider key>` as their issuer key. Renaming that
configuration key detaches existing account links. OpenID Connect links use the verified issuer.

### When a provider rotates your client secret

Update the configured client secret and deploy it before the provider retires the old one.
Client IDs, callback URLs and account links remain associated with the same provider.

The secret is read from configuration when needed. Metadata and key caches do not store it.

Coordinate the change with the provider's rotation procedure. When the provider is a NAF
OAuth server, its overlap window allows the client deployment to switch credentials:

```bash
vendor/bin/naf oauth:client:rotate-secret <client-id>
```

Deploy the new secret within the overlap window. A server-side `--now` rotation invalidates
the old secret immediately; clients using it fail until their configuration is updated.

### Validate provider setup { #check-it-before-anybody-tries }

```bash
vendor/bin/naf oauth:doctor
```

It verifies the dependencies, the public URL, the user model and its contract, the link table,
and every configured login — including whether the provider's metadata is reachable and belongs
to the issuer you configured. It prints the callback URL to register, and never prints a secret.

### Explicit client configuration { #the-older-configuration }

`oauth:providers` is the previous spelling of `auth:logins` and still works; it is used when
`auth:logins` is absent, and the error messages then name the keys you actually wrote.
`auth:providers` likewise still names account sources explicitly. Nothing has to be migrated.

### Configuration defaults { #everything-else-has-a-default }

`callback_url`, `scope`, `label`, `after_login`, `error_route`, the table name and the cache
location are derived or defaulted. Set them when you actually need something else.

---

## Render a sign-in button { #the-button }

```php-inline
use function Naf\OAuth\Client\oauth_button;
```

```html+php
<?= oauth_button('google') ?>                          <!-- "Mit Google anmelden" -->
<?= oauth_button('google', 'Continue with Google') ?>  <!-- explicit text wins -->
<?= oauth_button('google', next: '/projects/7') ?>     <!-- land there afterwards -->
```

The wording is settled highest-first: what you pass in, then your own
`oauth/button.phtml` in the application's view directory, then
`oauth:providers:<key>:label`, then the provider's own name. Copy the shipped view to change
the markup — yours wins, and nothing in the central configuration has to change for it.

The button label affects display only; it does not change protocol identifiers or callback URLs.

---

## Registered routes { #the-routes }

Shipped, named, and off with `'oauth' => ['routes' => false]`:

| Route | Purpose |
| --- | --- |
| `GET /auth/{provider}` | start a login |
| `GET /auth/{provider}/callback` | what the provider sends back |
| `GET /auth/{provider}/connect` | attach this provider to the account already signed in |

All three take `?next=/somewhere` — always a local path. Anything else falls back to
`oauth:after_login`, and "anything else" includes embedded control characters: browsers strip
tabs and newlines while normalising a URL, so `/\r//evil.test` would otherwise arrive as
`//evil.test`.

A provider reporting a failure is treated like any other answer: its `state` is checked and
consumed. A cancelled login therefore ends rather than sitting pending until it expires, and
nobody can drive the callback by appending `?error=` to it.

A refused login redirects to `oauth:error_route` with the reason flashed into the session as
`oauth_error`, rather than raising an error page. A cancelled login is something a person did,
not a server fault:

```html+php
<?php if ($reason = session()->getFlash('oauth_error')): ?>
    <p><?= $reason === 'not_linked'
        ? 'No account is linked to that login yet.'
        : 'That login could not be completed.' ?></p>
<?php endif ?>
```

---

## Map an external identity to an account { #which-account-is-this }

External login maps an issuer/subject pair to an application account:

- An existing link loads and signs in the linked account.
- With auto-registration enabled, the configured callback creates an account and the plugin
  links it before signing in.
- Otherwise, login fails with `not_linked`. The user can sign in locally and connect the provider.

To enable auto-registration, configure the account creation callback:

```php-inline
'oauth' => ['accounts' => [
    'auto_register' => true,
    'create' => static fn(ExternalIdentity $external) => $users->create([
        'email' => $external->email,
        'name'  => $external->name,
    ]),
]],
```

With several account sources registered in `auth:providers`, name the one that owns external
logins in `oauth:accounts:provider`. With one, it is used without being named.

### Identity-link integrity { #two-rules-it-enforces-for-you }

**Identities are keyed on `(issuer, subject)`, never on `subject` alone.** A subject is only
unique within its issuer; two providers can hand you the same string. The link table's primary
key *is* that pair, so two simultaneous first logins cannot both create a link.

**Creating an account and linking it are one act.** They run in one transaction, so a failed
link takes the half-made account with it — otherwise every retry leaves another orphan beside
the last one. The new account is then read back through the configured source before it signs
in: what signs in has to be what the next request will load, and the source is what decides who
may sign in at all.

**A matching e-mail address is never a link.** Not even a verified one: anybody who can get a
provider to assert an address could then walk into the account that uses it. Attaching a second
provider is a separate act, performed by somebody already signed in — and the person who
finishes it must be the person who started it:

```html+php
<a href="<?= route('oauth.connect', ['provider' => 'github']) ?>">Connect GitHub</a>
```

---

## Custom login integration { #doing-it-yourself }

For application-owned routes, call `oauth()` to use the protocol flow directly:

```php-inline
use function Naf\Auth\auth;
use function Naf\OAuth\Client\oauth;

return redirect(oauth('google')->authorizationUrl());

$callback = oauth('google')->callback();   // throws unless everything verifies
$external = $callback->identity;

$user = $yourAccounts->findBySubject($external->issuer, $external->subject)
    ?? throw new RuntimeException('Not linked.');

auth()->setIdentity($user, 'database');

return redirect($callback->redirectTo);
```

A custom callback must call `Tokens::remember($callback)` after successful sign-in when
provider token storage is enabled. Do not retain credentials from a callback the application
refuses to complete.

---

## Concurrent login attempts { #several-tabs }

Logins are keyed by their own `state`, so a person with three tabs open finishes all three.
Each entry is consumed on use and expires after ten minutes, which is also what makes a
replayed callback fail.

---

## External identity data { #what-comes-back }

`Callback`: `identity`, `purpose` (`LOGIN` or `LINK`), `initiator`, `redirectTo`, `token`.

`ExternalIdentity`: `provider`, `issuer`, `subject`, `claims`, and `email` / `emailVerified` /
`name` for convenience. `emailVerified` is true only for a literal `true` — providers have sent
`"true"`, `1` and `"1"` there.

---

## Calling the provider afterwards

Local login needs no persistent provider token. Enable the following integration when the
application must call the provider on the user's behalf after the sign-in request.

Store the required access and refresh tokens encrypted, request the API's scopes and check
what the provider actually grants.

```php-inline
// app/config.php
'oauth' => [
    'tokens' => [
        'store' => true,
        'key'   => 'BASE64_OF_32_RANDOM_BYTES',
    ],
],
```

`vendor/bin/naf oauth:doctor` describes key generation. Keep the encryption key outside
the database and source repository. Losing it makes stored grants unreadable and requires
new consent from affected users.

Then, wherever the API call happens:

```php-inline
use function Naf\OAuth\Client\oauth;
use function Naf\OAuth\Client\oauth_token;
use function Naf\Auth\auth;
use function Naf\Client\client;
use function Naf\redirect;
use Nyholm\Psr7\Request;

$token = oauth_token('google');

if ($token === null || !$token->grants('https://www.googleapis.com/auth/calendar.readonly')) {
    return redirect(oauth('google')->grantUrl(
        ['https://www.googleapis.com/auth/calendar.readonly'],
        auth()->providerName(),
        (string) auth()->id(),
    ));
}

$response = client()->sendRequest(new Request(
    'GET',
    'https://www.googleapis.com/calendar/v3/calendars/primary/events',
    ['Authorization' => 'Bearer ' . $token->accessToken],
));
```

`oauth_token()` returns a usable token or null when no grant is available. Expired access
tokens are refreshed and stored. Provider outages raise an exception; they do not imply that
consent was withdrawn.

### Granted scopes { #without-consent-there-is-no-access-and-consent-is-not-what-you-asked-for }

What the application may do is decided entirely by the scopes on the consent screen. Ask for
nothing beyond `openid email profile` — the default — and there is no API access at all.

A provider may grant fewer scopes than requested. Inspect `$token->scope` and use
`$token->grants(...)` before an API operation that needs a specific grant.

### Incremental consent { #ask-when-the-feature-is-used-not-at-the-login }

`grantUrl()` requests additional scopes when a feature needs them and returns through the
normal callback. Explain the requested access to users at that point.

A grant replaces the stored token with what the provider issued for it. Google is asked with
`include_granted_scopes`, so its answer carries the earlier permissions too; a provider that does
not do this issues a token for the new scope alone, and the previous one is gone.

### Access-token lifetime and refresh { #two-things-that-catch-people-out }

Google may omit refresh tokens on later sign-ins. Enabling storage after users have already
signed in can therefore require renewed consent. `grantUrl()` forces consent for its request;
normal login does not.

**Unlinking is not revoking.** Deleting the link only makes the application forget; the permission
stays listed in the person's account at the provider, looking current. `Tokens::forget()` tells the
provider first and then deletes, and belongs wherever an account is unlinked.

---

## Verification failures { #when-it-does-not-verify }

Every failure is an `OAuthException` carrying a short, stable `reason` alongside its message, so
an error page can tell a cancelled login from an expired one without matching on prose:

`provider_error`, `state_missing`, `state_unknown`, `code_missing`, `provider_mismatch`,
`token_request_failed`, `id_token_missing`, `id_token_invalid`, `nonce_mismatch`,
`issuer_mismatch`, `audience_mismatch`, `tenant_not_allowed`, `subject_missing`, `no_keys`,
`metadata_unavailable`, `no_session`, `access_token_missing`, `userinfo_unavailable`,
`subject_mismatch`, `not_linked`, `already_linked`, `initiator_mismatch`, `no_initiator`,
`account_unavailable`, `registration_refused`, `consent_required`, `refresh_failed`, `no_scopes`.

`already_linked` means exactly that — an integrity violation and nothing else. A dropped
connection or a value too long for its column surfaces as the database error it is, rather than
hiding a broken installation behind a message that sounds like ordinary use.

A misconfiguration raises `ConfigurationException` instead, and is left to surface the way every
other bug in your application does — it is addressed to you, not to a visitor.

---

## Provider metadata

Discovery documents and signing keys are cached under `storage/oauth` for a day, so a login
costs no extra request. Point `oauth:cache_path` somewhere else when that directory is not
writable, or when several servers should share one cache. A token signed with a key id we have not seen reloads the key set once —
which is what a rotation looks like from here — and a cooldown keeps invented key ids from
turning into a stream of outbound requests. A failed reload keeps using what is cached and backs off before trying again, so a provider that
is down does not turn every login into another outbound request. It never degrades into
accepting an unverified token — and it does not lean on stale metadata forever either: once the
cache has been expired for a day without the provider answering, logins fail with something an
operator can act on.

---

## Application responsibilities { #what-this-is-not }

OAuth sign-in, local passwords and LDAP are separate credential verification mechanisms.
Use [naf/auth-ldap](auth-ldap.md) for directory credentials. They can all return identities
through the same NAF Auth contract; do not route LDAP verification through OAuth callbacks.

### Where credentials belong

| Credential | Storage |
| --- | --- |
| Local passwords | hashed, never recoverable — `PasswordHasher` |
| Directory passwords | verified against the directory, never stored locally |
| Provider secrets, bind accounts | server-side configuration, out of the repository |
| Account links | stable external ids — `(issuer, subject)`, never an e-mail address |
| Your own tokens | the token store, as hashes |
| Providers' refresh tokens | only when you actually call their APIs — `oauth_provider_tokens`, encrypted with `oauth:tokens:key` |
| Your own client secrets | server-side configuration; rotated by changing one line, see above |

---

## Current limitations { #a-known-limit }

Taking a pending login out of the session is read-modify-write, and what makes that indivisible
is the session backend holding a lock for the request. PHP's own file handler does;
`naf/session`'s database handler does not. Two callbacks arriving for the same `state` in the
same instant could therefore both find it there.

Every check after that still applies — the authorization code is single-use at the provider, and
the ID token still has to verify — so this narrows the replay guarantee rather than opening a way
through it. A locking session backend closes it.

---

## Unsupported integrations { #not-here-yet }

- **Rotating `oauth:tokens:key`.** Changing it makes every stored grant unreadable, and everybody
  affected has to grant access again. Re-encrypting in place would need both keys held at once.

---
