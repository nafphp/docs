# Plugin release audit — 13 October 2026

This audit compares fetched remote main, local and remote branches, stable GitHub releases and exact Packagist source references for every top-level Composer naf-plugin repository. It is a dated contributor snapshot, not a public API promise.

Release follow-up: 14 October 2026.

## Package decisions

| Package | Published version | Result |
|---|---|---|
| naf/alexa | v0.1.1 | Published source is current; no package release needed. |
| naf/auth | v0.2.3 | Released v0.2.3; exact GitHub/Packagist commit verified. |
| naf/auth-ldap | v0.1.0 | Only contributor/README documentation differs; no new package release needed. |
| naf/board | v0.1.8 | Published source is current; no package release needed. |
| naf/cli | v0.2.4 | Published source is current; no package release needed. |
| naf/client | v0.2.2 | Published source is current; no package release needed. |
| naf/cms | None | RC release gates repaired and verified; maintainer merge and first Packagist registration remain pending. |
| naf/database | v0.2.4 | Published source is current; no package release needed. |
| naf/flow | v0.1.0 | Only contributor/README documentation differs; no new package release needed. |
| naf/form | v0.2.4 | Published source is current; no package release needed. |
| naf/i18n | v0.2.2 | Only contributor/README documentation differs; no new package release needed. |
| naf/mail | v0.2.3 | Published source is current; no package release needed. |
| naf/mcp | v0.2.6 | Published source is current; no package release needed. |
| naf/monitoring | v0.1.0 | Released on GitHub and Packagist; exact commit and published-package installation verified. |
| naf/oauth-client | v0.2.4 | Published source is current; no package release needed. |
| naf/oauth-server | v0.2.5 | Published source is current; no package release needed. |
| naf/orm | v0.2.3 | Published source is current; no package release needed. |
| naf/queue | v0.2.4 | Published source is current; no package release needed. |
| naf/rate-limit | v0.1.0 | Only contributor/README documentation differs; no new package release needed. |
| naf/rbac | v0.1.4 | Released; exact GitHub/Packagist commit and fresh authenticated UI installation verified. |
| naf/sanity | None | Unfinished prototype: missing helper target, no runtime integration or behavioral test suite; not release-ready. |
| naf/schedule | v0.2.4 | Published source is current; no package release needed. |
| naf/session | v0.2.3 | Published source is current; no package release needed. |
| naf/storage | v0.1.0 | Only contributor/README documentation differs; no new package release needed. |
| naf/view | v0.2.3 | Published source is current; no package release needed. |
| naf/websocket | v0.1.1 | Published source is current; no package release needed. |

## Verified release and review candidates

- Auth v0.2.3: merged commit 44f392db0fe73765b683b177462351689301c785; GitHub and Packagist verified. 99 tests / 290 assertions, analysis, style and strict validation passed; exact merge CI covers PHP 8.3/8.4/8.5.
- RBAC v0.1.4: [release](https://github.com/nafphp/rbac/releases/tag/v0.1.4) at merged commit 45be69f9ec04ba2b213ac9da7ea0c3d1351c1a47; exact Packagist reference verified. A real browser test found the reduced-motion specificity defect; the correction and negative regression pass. The merge CI covers MySQL 8.4 and browser accessibility checks. A fresh installation using only published packages renders the actual authenticated administration fragments and passes keyboard, checked-state, form-field, reduced-motion and forced-color checks. The matching UI guidance is published in the Roles and permissions chapter.
- Monitoring v0.1.0: [release](https://github.com/nafphp/monitoring/releases/tag/v0.1.0) at merged commit adea62f2277392f57500378f017f4724ec21aba9; exact Packagist reference verified after the maintainer registered the package. 57 unit tests / 146 assertions, real HTTP/UDP and CLI-host checks, formatting, strict validation and exact merge CI on PHP 8.3/8.4/8.5 pass. Fresh published-package host and HTTP/UDP checks pass. The Monitoring chapter, generated references and executable CLI/capture examples are published with the release. The user explicitly delegated the Monitoring and RBAC merges; that delegation does not include CMS.
- CMS: [PR #2](https://github.com/nafphp/cms/pull/2), commit 57ffdea1188adbe21ad693e35d05ffe26b132cd5. The RC now requires Framework 0.2.9, CLI 0.2.2 and PDO explicitly, and locks published packages. PHPStan scans helper symbols without booting runtime services; the argv baseline is stable across environments. Tailwind uses explicit package sources, source-map-js is patched to 1.2.2, and the fresh-host test checks preservation of starter-owned guides as well as managed-guide installation. The updated lock and minimum NAF versions both pass 493 tests / 2455 assertions; analysis, style, strict validation, docs and integrity commands, 25 builder tests, reproducible assets, archive inspection and the real host smoke pass. The host applies 16 SQLite migrations and verifies CLI rendering, scoped MCP, HTTP authentication redirect and vendor immutability. CI adds the PHP 8.3 minimum dependency job and npm audit; supported PHP jobs and MariaDB migration checks pass. Minimum ORM dependencies emit a known deprecation under local PHP 8.5; the supported PHP 8.3 minimum CI job passes. The package is not yet merged, tagged or registered on Packagist.
- Sanity: draft PR #2 is explicitly unfinished. sanity() targets a missing class, the validator/converter traits are not integrated, and there is no behavioral suite or runtime contract ready for publication.

## Older branches

The Board event patch on feat/rbac-priorities-and-interface-pass has the same stable patch ID as the version already on main. Flow runtime, tests and manifests match the old RC; only newer contributor documentation differs. The CLI launcher installer in the old RC is byte-identical to main; main contains subsequent command/help/debug additions. Old i18n, Session and Storage branches do not contain missing runtime fixes. The CMS ai-enhancement branch remains a separate, unmerged experiment based on an older application layout; it is not part of the prepared package RC. Framework plugin-completion experiments were withdrawn and are not release candidates.

## Related foundation packages

Framework main contains the untagged 0.2.11 authority corrections; the 0.2.12 request-handling work remains in PR #15. The current plugin audit does not merge that separate code PR. The starter v0.2.4 matches main and Packagist; no new starter code or lock is pending.

## Toward 1.0

The useful next gates are explicit supported runtime/dependency matrices, browser and real host checks for UI/protocol changes, current locks for operational commands, and separate handling of incomplete prototypes. Release only reviewed changes at the exact verified merge commit, then verify Packagist and publish matching documentation.
