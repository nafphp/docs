# Security release guide status

These sections were prepared for the security corrections of 15 October 2026.
Published sections have been integrated into the guides after verifying their source
commits on Packagist. The remaining WebSocket text stays outside `pages/` until its
fixed stable package is published and verified.

| Package | Version | Guide status |
|---|---|---|
| `naf/cms` | 0.0.3 published | Requirements, authentication, upgrades and uploads promoted to `pages/cms.md` |
| `naf/client` | 0.2.3 published | Transport selection and redirects promoted to `pages/http-client.md` |
| `naf/board` | 0.1.9 published | Remembered sign-ins and revoked sessions promoted to `pages/built-with/nafinity-accounts.md` |
| `naf/websocket` | 0.1.2 pending | Authorization and renewal remain in `guide-updates.md` |

Board 0.1.9 is published at `e225646373b6e0abec27723cb41941b0194402e6`.
The PHP 8.3/8.5 matrix passed on MariaDB 11.4 and MySQL 8.4 for that exact commit,
including IMAP integration. The timer-dialog guide is in
`pages/built-with/nafinity-tickets.md`. No new migration or runtime dependency was added.

The original security pull requests were merged before publication:
[CMS #4](https://github.com/nafphp/cms/pull/4),
[Board #39](https://github.com/nafphp/board/pull/39),
[Client #3](https://github.com/nafphp/client/pull/3) and
[WebSocket #2](https://github.com/nafphp/websocket/pull/2).
Board's final release also includes [#40](https://github.com/nafphp/board/pull/40)
and [#41](https://github.com/nafphp/board/pull/41).

Before promoting WebSocket guidance, verify its exact release commit on Packagist,
refresh generated references and run the page, strict build and executable-example
checks. Merging source alone does not publish a package. The CMS Auth minimum
follow-up remains tracked separately in `follow-up.md`.

Regression evidence remains in the packages: CMS `AuthMigrationTest`, password rehash,
upload checks and the real package-smoke HTTP flow; Client `StreamingTest`;
WebSocket `ServerTest` and `TokenTest`; Board `RememberedSignInConcurrencyTest`
with a separate database connection and `AccountSecurityOverHttpTest`. Library
lockfiles are development snapshots; consumers resolve the fixed published
packages. These corrections do not update a starter's committed lock.
