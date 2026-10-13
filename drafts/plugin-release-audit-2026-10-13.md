# Plugin release audit — 13 October 2026

This audit compares fetched remote main, local and remote branches, stable GitHub releases and exact Packagist source references for every top-level Composer naf-plugin repository. It is a dated contributor snapshot, not a public API promise.

## Package decisions

| Package | Published version | Result |
|---|---|---|
| naf/alexa | v0.1.1 | Published source is current; no package release needed. |
| naf/auth | v0.2.3 | Released v0.2.3; exact GitHub/Packagist commit verified. |
| naf/auth-ldap | v0.1.0 | Only contributor/README documentation differs; no new package release needed. |
| naf/board | v0.1.8 | Published source is current; no package release needed. |
| naf/cli | v0.2.4 | Published source is current; no package release needed. |
| naf/client | v0.2.2 | Published source is current; no package release needed. |
| naf/cms | None | Draft: 493 unit tests pass, but locked CLI fails docs:check; full release gates incomplete. |
| naf/database | v0.2.4 | Published source is current; no package release needed. |
| naf/flow | v0.1.0 | Only contributor/README documentation differs; no new package release needed. |
| naf/form | v0.2.4 | Published source is current; no package release needed. |
| naf/i18n | v0.2.2 | Only contributor/README documentation differs; no new package release needed. |
| naf/mail | v0.2.3 | Published source is current; no package release needed. |
| naf/mcp | v0.2.6 | Published source is current; no package release needed. |
| naf/monitoring | None | Initial implementation and checks pass; maintainer merge and first Packagist registration gates pending. |
| naf/oauth-client | v0.2.4 | Published source is current; no package release needed. |
| naf/oauth-server | v0.2.5 | Published source is current; no package release needed. |
| naf/orm | v0.2.3 | Published source is current; no package release needed. |
| naf/queue | v0.2.4 | Published source is current; no package release needed. |
| naf/rate-limit | v0.1.0 | Only contributor/README documentation differs; no new package release needed. |
| naf/rbac | v0.1.3 | Reduced-motion bug found and fixed; tests and CI green; maintainer merge gate pending. |
| naf/sanity | None | Unfinished prototype: missing helper target, no runtime integration or behavioral test suite; not release-ready. |
| naf/schedule | v0.2.4 | Published source is current; no package release needed. |
| naf/session | v0.2.3 | Published source is current; no package release needed. |
| naf/storage | v0.1.0 | Only contributor/README documentation differs; no new package release needed. |
| naf/view | v0.2.3 | Published source is current; no package release needed. |
| naf/websocket | v0.1.1 | Published source is current; no package release needed. |

## Verified release and review candidates

- Auth v0.2.3: merged commit 44f392db0fe73765b683b177462351689301c785; GitHub and Packagist verified. 99 tests / 290 assertions, analysis, style and strict validation passed; exact merge CI covers PHP 8.3/8.4/8.5.
- RBAC v0.1.4: PR #4, cfa8063ac01ccdd77446e797f930ecab0f2b2f92. A real browser test found the reduced-motion specificity defect; the correction, negative regression and authenticated rendered host pass. PHP tests: 50 / 71 with the local MySQL acceptance skipped; PR CI covers MySQL 8.4 and the browser regression.
- Monitoring v0.1.0: PR #1, 68d0c9ffb1d09d0e4e40a63410d25eebd009b09a. 57 unit tests / 146 assertions, real HTTP/UDP and CLI-host checks, formatting, strict validation and PHP 8.3/8.4/8.5 PR CI pass.
- CMS: draft PR #2. 493 tests / 2455 assertions, analysis and style pass in an isolated install. The committed lock still resolves naf/cli 0.2.0 and vendor/bin/naf docs:check fails before dispatch. CLI/package/reference/asset/database release gates remain incomplete; no stable package is listed on Packagist.
- Sanity: draft PR #2 is explicitly unfinished. sanity() targets a missing class, the validator/converter traits are not integrated, and there is no behavioral suite or runtime contract ready for publication.

## Older branches

The Board event patch on feat/rbac-priorities-and-interface-pass has the same stable patch ID as the version already on main. Flow runtime, tests and manifests match the old RC; only newer contributor documentation differs. The CLI launcher installer in the old RC is byte-identical to main; main contains subsequent command/help/debug additions. Old i18n, Session and Storage branches do not contain missing runtime fixes. Framework plugin-completion experiments were withdrawn and are not release candidates.

## Related foundation packages

Framework main contains the untagged 0.2.11 authority corrections; the 0.2.12 request-handling work remains in PR #15. The current plugin audit does not merge that separate code PR. The starter v0.2.4 matches main and Packagist; no new starter code or lock is pending.

## Toward 1.0

The useful next gates are explicit supported runtime/dependency matrices, browser and real host checks for UI/protocol changes, current locks for operational commands, and separate handling of incomplete prototypes. Release only reviewed changes at the exact verified merge commit, then verify Packagist and publish matching documentation.
