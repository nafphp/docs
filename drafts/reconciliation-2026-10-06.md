# Draft reconciliation — 6 October 2026

Each note has been checked against package code and the published guide. Old branch drafts
are read-only source material; their release gates do not become new product work.

| Source | Resolution |
|---|---|
| `drafts/storage.md` | Incorporated into `pages/file-storage.md`, including missing disk configuration, stream ownership and remote adapter limits. Storage 0.1.0 is published. |
| `drafts/http-client-streams.md` | `pages/http-client.md` already contains the current-position, temporary-file, retry, redirect and fallback contracts. Reconciled pointer replaces the duplicate draft. Client 0.2.2 is published. |
| `drafts/rc-validation.md` | Retained as dated historical evidence; reviewed dependencies are published. |
| `reviews/plugin-readability-2026-09-15.md` | Historical inventory; no blanket formatting task or current failure count. |
| `codex/automatic-plugin-order:drafts/automatic-plugin-order.md` | Published in the plugin guide and console reference. Framework 0.2.7 already includes ordering and diagnostics; no repeated implementation. |
| `docs/board-reliability:drafts/board-reliability.md` | Board implementation/reference contains bounded cards, revision/version conflicts, private files, staged recovery and confirmed AI writes. Native Chrome/Firefox drag remains a concrete desktop-tool acceptance blocker. |
| `codex/console-launcher-docs:drafts/console-launcher.md` | Console guide and Nafinity command guide describe Composer launcher and the host-owned runtime. Runtime argument/exit-code and no-fallback probes passed. |
| `docs/nafinity-integration-rc:drafts/nafinity-integration-rc.md` | Published package integration is recorded in Board; outdated namespaces, skeleton test commands and distribution-lock request were reconciled with the actual package suite and owner-controlled updates. |
| `drafts/auth-ldap:drafts/auth-ldap.md` | LDAP guide describes the released package. Actual external directory acceptance needs deployment credentials/configuration. No automatic email-based linking. |
| `drafts/auth-ldap:drafts/pages-after-the-releases.md` | Client, Storage, LDAP, limiter and framework release prerequisites are satisfied. Public guides and generated references describe published packages. |
| Nafinity `drafts/optional-core-cache.md` | Conditional measurement decision, retained outside the public site. No cache package is required by a historical idea. |

Board 0.1.4 and Framework 0.2.8 have been verified on Packagist at their exact release
commits. The Board package acceptance record now documents current tests, English UI,
async disposer regressions, drawer drafts, mobile/keyboard moves and account appearance.
External LDAP/OIDC/SMTP and physical-device/native-drag acceptance are clearly separated
from completed package work. Saved filters, WIP, multiple boards, inbound mail and a full
public API remain new scope.
