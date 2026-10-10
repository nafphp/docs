# Pending security documentation

These are complete replacements for pages/alexa.md, pages/mcp.md and pages/oauth-server.md.
Do not publish before naf/oauth-server 0.2.5, naf/mcp 0.2.6 and naf/alexa 0.1.1 are released
and available on Packagist. Release the OAuth and MCP dependencies before Alexa, then move
these drafts into pages, refresh generated references and run the complete documentation
checks against the published versions. Follow the delegated documentation deployment workflow.

The detailed local audit report and raw test output are in ../../../audit-2026-10-10/ outside
this documentation repository. No public security disclosure is part of this change.

Local follow-up verification now includes actual overlapping HTTP refresh/revocation requests
in distinct PHP workers and a browser smoke test of login, consent, both decisions, keyboard
navigation, referrer suppression and framing protection. These checks use disposable local
accounts and a loopback callback; they do not verify Amazon onboarding or a deployed host.

Still verify the real host's ownership/tenant rules, login design and accessibility, trusted
proxy/TLS settings, rate and SSE budgets, logs, storage permissions and OAuth data retention.
Amazon's private developer access and confirmed service-secret provisioning remain external
prerequisites. Publish and retest against the stable dependency versions before moving these
drafts into the public guides.
