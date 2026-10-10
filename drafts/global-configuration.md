# Nafinity global configuration

Waiting for `naf/board` v0.1.6 to be released and available on Packagist.
Keep this material outside `pages/` until then. Framework 0.2.10 configuration sources
and Mail 0.2.3 SMTP/provider metadata are documented in the published configuration,
plugin and mail guides.

## Configure the installation in Global settings

Nafinity keeps the host's `config.php` as its defaults. Global settings show the
merged configuration in the existing settings cards and field renderer. An explicit
administration value wins over server configuration, including an `ENV:NAME`
reference. Each field shows its source: Administration, Environment, Server
configuration or Default. Environment sources include the variable name.


The default view contains the standard settings. Enable **Advanced settings** to show
technical configuration cards in a separate section below them. Mixed cards retain
the standard fields first and add an **Advanced settings** section underneath. The
switch is a per-administrator view preference for the current browser tab, preserved
across saves. Turning it off hides and disables advanced fields, so saving standard
fields preserves advanced overrides. A direct link to an advanced card reveals it.

Add an entry to the host's `config.php` and it appears automatically on the next
request in the advanced view. Nested associative arrays produce colon-separated
fields; lists remain one JSON field. Existing definitions and explicit provider
labels take precedence. Unknown names become readable labels; a central glossary
retains the spelling of known acronyms such as MCP, RBAC, API, SMTP, IMAP and CSRF.
Literal configuration keys remain unchanged. New acronyms can be added centrally
or supplied through an explicit field label; they cannot be inferred reliably from
arbitrary words.


Edit a value to select an administration override. Choose **Server configuration**
and save to remove the override. Optional fields also offer **Clear value**, which
stores an explicit null. False, zero and empty strings remain values. Passwords
are write-only: leaving a password input blank keeps its current value, and a
reset restores its configured value. Secret values are excluded from HTML,
JSON reads and audit payloads.

The inventory includes startup values such as database, session, class and path
configuration. Lists and structured values use JSON. SMTP provider metadata supplies
field types, TLS/authentication choices, limits and secret flags. Extensions can
declare application settings with a `configKey` and replace generated definitions
through the existing registry. `SettingDefinition` also accepts `advanced: true`
(default false) to place contributed installation fields in the advanced section.

Only administrators with installation `settings.manage` can read/write the
global HTTP endpoint, `GET/POST /api/settings/application`. Native CSRF validation
protects writes. Personal settings remain separate. A stale form is refused with
409 instead of deleting another administrator's changes. Validation prevents an
invalid batch from being partially saved; database changes must connect to an
existing application database and preserve the current administrator's identity
and permission. Existing mail adapters validate mail configuration without sending.

### Storage and process lifetimes

The framework loads administration overrides before any plugin boots. Database,
session, auth and mail therefore see the same configuration. Overrides cannot
live only in the database: the database connection itself is configurable.

Nafinity writes `storage/configuration/values.enc` atomically under a lock, using
the existing authenticated token cipher. A generated key lives beside it in
`storage/configuration/key`. The directory uses 0700 and files use 0600. Encryption
protects a copied values file; protection of the key depends on filesystem access.
Keep this directory outside the web root, include both files in backups, and share
the same durable private storage among application replicas and workers.

New HTTP requests load the saved values. Restart already-running queue, schedule
and socket processes after changing configuration they hold.

If a startup override prevents access to the administration:

1. Set the process environment `NAFINITY_CONFIG_OVERRIDES=0` and restart the affected
   processes. This bypasses saved overrides and uses server configuration.
2. Restore a valid encrypted file with its matching key, or move
   `storage/configuration/values.enc` aside to remove all overrides.
3. Remove the recovery environment override and restart affected processes again.

The private storage location/key and recovery switch are outside editable config,
so changing a database or path setting cannot move the override store itself.

Before publication, update the Nafinity settings guide and regenerate the API inventory
for the released Board signatures.
