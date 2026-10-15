# Follow-up corrections awaiting stable packages

These additions belong in the named guides after their fixed versions are available on
Packagist. They describe the second audit pass of 15 October 2026. They must stay outside
`pages/` until publication; the original audit working files are not repository artifacts.

| Package | Prepared version | Release dependency |
|---|---|---|
| `naf/auth` | 0.2.4 | None |
| `naf/session` | 0.2.4 | None |
| `naf/client` | 0.2.3 | Extend the existing pending RC |
| `naf/oauth-server` | 0.2.6 | Run all required SQLite, PostgreSQL and MySQL concurrency checks before release |
| `naf/mcp` | 0.2.7 | OAuth Server 0.2.6 must be published first |
| `naf/cms` | 0.0.3 | Raise the Auth minimum to 0.2.4 and update the committed lock after Auth publication |

Before promoting this draft, confirm the final CMS RC version and review the final combined
RC diff. No package release or package-code merge is authorized by this fix request.

## Authentication and forms

Add to `pages/auth.md`, Sessions, and cross-reference from `pages/forms.md`:

Auth 0.2.4's session adapter removes secrets from the previous authentication state after
successful authentication or adoption of a verified identity, and on logout. The default
reset list contains `_csrf`. Form creates a fresh token the next time `csrf()->token()` is
called. Open forms from before the change must be reloaded. Other session data, such as
carts and language preferences, survives. Failed credential checks do not rotate the token.

Applications can extend the reset list in `app/config.php`; retain `_csrf` when using Form:

```php
<?php
return ['auth' => ['session_reset_keys' => ['_csrf', 'step_up']]];
```

| Key | Type | Default | Effect |
|---|---|---|---|
| `auth:session_reset_keys` | list of strings | `['_csrf']` | Session values removed at login, identity adoption and logout |

Custom `StateStoreInterface` implementations remain responsible for their own trust-boundary
cleanup. The explicit `csrf()->generate()` calls in the login recipe remain valid on both
old and new Auth releases.

## Session cookie scope and strict IDs

Add to `pages/sessions.md`:

Session 0.2.4 uses host-only cookies by default: it omits the `Domain` attribute, so the
browser does not send the cookie to subdomains. `HttpOnly`, `SameSite=Lax`, path `/` and the
existing HTTPS/trusted-proxy rules for `Secure` remain in effect. Share a cookie with
subdomains only when they belong to the same trust boundary:

```php
<?php
return ['session' => ['cookie_domain' => 'example.com']];
```

| Key | Type | Default | Effect |
|---|---|---|---|
| `session:cookie_domain` | string or null | `null` | Omit Domain by default; an explicit domain shares the cookie with its subdomains |

For a directly instantiated `Session`, call `configureCookieDomain()` before `start()`.
`clear()` expires the cookie with the same scope and flags used to create it.

Session startup enables `use_strict_mode` and `use_only_cookies`, and disables `use_trans_sid`.
Unknown client-supplied IDs are replaced. The database handler implements
`SessionUpdateTimestampHandlerInterface`: `validateId()` rejects missing and expired records,
while `updateTimestamp()` refreshes unchanged sessions and request metadata. Custom save
handlers must provide strict-ID validation as well; PHP cannot enforce strict mode with a
handler that lacks it.

For an upgrade from domain cookies, expire the previous cookie once using its original
Domain and Path, or change the session name. A domain cookie and a host-only cookie with the
same name can coexist. Verify the transition in a real browser and expect a fresh login when
changing the session name. Do not automatically derive a deletion domain from an untrusted
Host header.

## HTTP client schemes

Add to `pages/http-client.md`, Transport selection:

Client 0.2.3 accepts absolute HTTP and HTTPS URLs with a host. Other schemes and relative URLs
raise `ClientException` before transport selection or body consumption. Both shipped
transports enforce this rule for direct calls; cURL also restricts libcurl protocols and
redirect protocols to HTTP(S). A response without an HTTP status line is rejected.

This restriction does not decide which HTTP hosts, addresses or ports an application may
contact. Keep the application's destination allow-list or SSRF policy, including redirects
and DNS behavior.

## OAuth and MCP request lifetime

Add to `pages/oauth-server.md`, Bearer authentication, and `pages/mcp.md`, OAuth:

OAuth Server 0.2.6 resolves the current request when `token()` is called. A shared
`ResourceServer` caches a context only for the same immutable request instance. Successive
`App::handle()` calls therefore evaluate their own Authorization headers. A missing or
invalid token never reuses the preceding caller's identity or scopes.

Explicit integrations can call `ResourceServer::context($request)` with any PSR-7
`RequestInterface`. Existing constructor calls using the `request` argument remain valid.
Shared services can instead pass the `currentRequest` closure, which returns the active
request. Do not store a `TokenContext` across requests.

MCP 0.2.7 passes the authenticator's supplied request directly to the resource server,
including ordinary PSR-7 requests. Its Composer conflict excludes OAuth Server versions
before 0.2.6. Publish OAuth Server first, then verify the combination with a fresh Composer
resolution before publishing MCP.

## CMS permissions, profiles and scripts

Add to `pages/cms.md`, Authentication and upgrades:

`settings.manage` controls global and plugin settings; `translations.manage` controls
translation overrides. `admin.access` alone grants neither write operation. Settings sections
without an explicit permission require `settings.manage`. A dedicated section permission,
such as `ai.instructions.manage`, is required in addition to `settings.manage`.

Settings pages require `settings.manage`, the language/translation page requires
`translations.manage`, and its global-language form appears only with `settings.manage`.
Audit history requires `system.read`. API write endpoints enforce the corresponding
permission independently of the UI.

Run `vendor/bin/naf db:migrate up` during the upgrade. Migration202610150001 creates both
permissions and grants them to the existing `admin` role only. Grant the rights deliberately
to other trusted roles. Its rollback removes the added grants and permissions.

Profile changes use the same target privilege boundary as password resets. Use
`UserRepository::updateProfileByActor()` for actor-driven mutations. Custom
`UserPrivilegePolicyInterface` implementations must implement `assertProfileChange()` and
throw `PrivilegedActionDenied` to refuse a mutation. Refused API updates return 403 and record
the denied operation. Low-level `updateProfile()` remains available for trusted internal code.

New and edited usernames accept 3–64 Unicode letters/numbers and `.`, `_`, `@`, `-`.
Invitation registration applies the same validation. Existing display names are preserved;
embedded script data uses `Naf\CMS\Support\ScriptJson::encode()`, which escapes HTML
delimiters while preserving the decoded values. Use it for CMS JSON inside `<script>`
elements; keep HTML attribute escaping for data attributes. CSP remains an additional defense.

After all required package publications, refresh generated references with
`python tools/gen_reference.py`, review them, run `python tools/check_pages.py`,
`mkdocs build --strict` and `python tools/test_examples.py`, then publish the promoted guide
sections through the delegated documentation workflow.
