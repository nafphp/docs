# OAuth server 0.2.4: MCP resource discovery and code exchange

Publication gate: wait for `naf/oauth-server` 0.2.4 on Packagist, then reconcile this draft
into `pages/oauth-server.md` and the Alexa guide. No database migration is required.

When conventional routes are enabled, `GET /.well-known/oauth-authorization-server` exposes
the same verified metadata service as OIDC discovery. OAuth-only installations need no signing
key. It advertises authorization code, refresh and client credentials grants, and PKCE S256.
Set `public_url` to the stable public HTTPS origin used in endpoint URLs.

Authorization-code token requests can now supply `resource`. The PDO store compares it with
the audience recorded when authorization was approved, inside the existing atomic code claim.
A mismatch returns `invalid_grant`, spends the attempted code and issues no tokens. A malformed
empty or non-string parameter returns `invalid_request` before spending the code. An omitted
parameter preserves the previous API behavior. Refresh requests need no resource parameter;
the originally authorized audience is retained.

Custom token adapters can implement the additive `ResourceTokenStoreInterface`, which extends
`TokenStoreInterface` with `redeemForResource(...)`. The existing `redeem()` signature remains
unchanged. A request supplying a resource to an adapter without that contract fails closed
with `invalid_target` rather than silently ignoring the target. Do not check and redeem in
separate transactions; the binding must be verified while atomically claiming the code.

Configure `oauth_server:audience` to the canonical MCP URI, and register that exact URI in
the client's allowed audiences. Service clients use only `client_credentials` and service
scopes. Account-linking clients use only `authorization_code` and `refresh_token`, with exact
Amazon-supplied callback URIs and the user scopes offered in protected-resource metadata.
`naf/alexa` automates these separate registrations.

Verify positive and mismatched code exchanges, PKCE, refresh without resource and revoked
tokens. Before release, run both concurrency scripts on SQLite, PostgreSQL and MySQL as
documented in the package's concurrency guide.
