# Security corrections pending package releases

These guide updates wait for the four stable packages below. The maintainer requested RC
fixes and regression tests on 15 October 2026 and explicitly withheld release publication.
The published guides continue to describe current releases and their operational limits.
Do not promote these sections into `pages/` or raise installation minimums before Packagist
contains the verified release commits.

The four security pull requests were reviewed and merged on 15 October 2026:
[CMS #4](https://github.com/nafphp/cms/pull/4),
[Board #39](https://github.com/nafphp/board/pull/39),
[Client #3](https://github.com/nafphp/client/pull/3) and
[WebSocket #2](https://github.com/nafphp/websocket/pull/2).
Merging source does not publish these package versions. The subsequent CMS quality pass
also targets 0.0.3; review its final RC before promoting the corresponding guide text.

| Package | RC branch | Guide sections |
|---|---|---|
| `naf/cms` | `v0.0.3-rc` | CMS requirements, authentication, upgrades and uploads |
| `naf/client` | `v0.2.3-rc` | HTTP client transport selection and redirects |
| `naf/websocket` | `v0.1.2-rc` | WebSocket authorization and renewal |
| `naf/board` | `v0.1.9-rc` | Nafinity accounts and remembered sign-ins |

After publication, verify exact source references on Packagist, merge the corresponding
sections from `guide-updates.md`, refresh generated package/configuration/function references,
and run the documented page, strict build and executable-example checks. Remove superseded
operational limitations only when the fixed minimum versions are available.

Regression evidence belongs to each package: CMS AuthMigrationTest, password rehash and upload
checks plus the real package-smoke HTTP flow; Client StreamingTest; WebSocket ServerTest and
TokenTest; Board RememberedSignInConcurrencyTest with a separate database connection. Library
lockfiles are development snapshots; consuming installations must resolve the fixed packages
when they become available. No starter lock update is part of this unreleased correction.
