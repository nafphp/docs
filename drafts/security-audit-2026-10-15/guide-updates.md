# Guide updates after the security releases

These sections are prepared for the releases named in the adjacent README. They describe the
RC implementations and must remain outside the published site until those releases exist.

## CMS requirements and upgrades

Add Fileinfo to the CMS runtime requirements. CMS 0.0.3 requires `ext-fileinfo` to verify
uploaded content; a client-supplied MIME header cannot replace content detection.

Replace the CMS 0.0.2 password-reset limitation and legacy-session restoration paragraph:

CMS 0.0.3 binds database authentication to the password hash that established the session.
Password changes and resets invalidate older sessions on their next authenticated request,
including PHP file sessions and database-backed sessions. A delayed write of an old session
payload cannot restore access. Authentication whose credentials change before publication
is rejected, and an automatic password rehash cannot overwrite a concurrent reset.

Upgrading requires every existing CMS session to sign in again, including legacy `userId`
sessions. No schema migration is needed for the credential binding. An automatic password
rehash also changes the binding, so other sessions authenticate again. Already executing
requests are not retroactively cancelled. Custom state stores must preserve equivalent
credential binding and fail closed on missing or changed credentials.

The login destination uses the CMS internal URL policy and rejects backslashes and control
characters. It preserves valid local paths and queries. A remembered absolute application
URL contributes only its local path and query.

Update the media allow-list explanation:

Both the extension and the server-detected MIME type must match the configured allow-list.
The client MIME type remains metadata only. Failed detection or incompatible content is
rejected before writing the file or its database row. This validation is not a malware
scanner and does not establish that a document or image is harmless.

Verify a reset using two independently authenticated browser sessions. Reset the password
through the authorized, CSRF-protected endpoint; the other session's next protected request
must redirect to login. The old password must fail, and a fresh login with the replacement
must succeed. Keep the tests on the configured production session backend as well.

## CMS contributor checks and article actions

The CMS 0.0.3 source quality follow-up removes the PHPStan baseline while retaining level 6
analysis of `src/` and `tests/`. EntityStorage's generic entity type is preserved across
single-entity and collection operations. Array contracts and PHPDoc tags describe the
actual metadata, schema and result records. Migration execution remains a separate check.
Contributor instructions live in the package's `docs/quality-checks.md`.

Article publish and delete handlers pass the normalised language string returned by
LanguageRegistry to the Content API. They do not read an enum property from that string.
The published-version deletion guard remains in place. Login and form handlers establish
the parsed body's array shape, and CMS HTTP paths check the PSR server-request capability
before reading server metadata, parsed input, uploads or query parameters.

The installed-host smoke check runs `install:database` twice against a disposable SQLite
database. Both runs must succeed, and the second must apply no new migrations. No schema
migration or new runtime dependency is introduced by this quality follow-up.
User list and edit-form queries also run on SQLite: they use the common GROUP_CONCAT syntax
and sort role and permission names in PHP, preserving distinct names and users without roles.

## HTTP client redirects

In Client 0.2.3 the PHP stream fallback returns the original 3xx response, its Location header,
headers and body. It never follows the redirect and therefore never forwards credentials to
its destination. `max_redirects` applies to the cURL transport; setting a positive limit does
not enable redirects in the stream fallback. Use the default cURL transport when redirects
are needed. The cURL behavior remains unchanged, including removal of Authorization and
Cookie on an origin change and explicit request-body replay rules.

Do not implement a consumer-specific automatic redirect loop that forwards all headers.
Applications with untrusted outbound URLs still need an allow-list or an appropriate SSRF
policy; the transport is not that policy.

## WebSocket subscription expiry

In WebSocket 0.1.2, token expiry ends the established subscription as well as denying new
upgrades. Expired connections cannot receive further publications, relay presence locations
or flush queued application payloads. The server checks expiry after waiting for I/O and
before flushing; publication and relay also reject expired authorization.

The existing browser module reconnects through the host's renewal URL. That URL must check
the current session, account state and channel authorization. Short token lifetimes therefore
bound a subscription without requiring the page to initiate a reconnect itself. Permission
changes are not an instantaneous push revocation: an unexpired token remains valid until
expiry. Explicitly close connections when immediate revocation is required.

## Nafinity remembered sign-ins

Board 0.1.9 serializes remembered sign-in with password, email and account-state changes using
the existing account-row lock. It re-reads the stored token after acquiring the lock and keeps
the account locked through validator rotation and session publication. Two callers cannot
both spend one validator. A password reset either invalidates the already published session
version or commits first and makes the old remembered credential unusable.

Existing sign-in and account-change events retain their timing: sign-in is announced after
the transaction commits. There is no schema change and no new configuration. Verify the
concurrency regression against both supported database families, MariaDB and MySQL; a serial
HTTP server or SQLite-only test does not demonstrate the locking guarantee.
