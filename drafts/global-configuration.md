# Global configuration and early configuration sources

Waiting for `naf/framework` v0.2.10, `naf/mail` v0.2.3 and `naf/board` v0.1.6 to be
released and available on Packagist. Keep this material outside `pages/` until then.

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

## Framework: load a configuration source before plugin boot

A plugin or host may provide `app/config_sources.php` or `src/config_sources.php`;
the first existing spelling wins. The file returns a list of classes implementing
`Naf\Contracts\ConfigurationSourceInterface`. All plugins are registered before
configuration sources load, and the host's source file is processed last.

A source has a no-argument constructor, a stable `name(): string`, and
`load(string $basePath): array`. It returns literal values under colon-separated
paths, such as `['mail:smtp:port' => 465]`. Source values are not expanded as
environment references. A source must not call `config()` or resolve services that
depend on configuration; doing so would create a boot cycle.

`Config::overlay($name, $values)` replaces a named layer. An empty layer resets it.
`base()` returns resolved server configuration, `raw()` retains environment
references, `source($key)` identifies the active source, and `overrides($name)`
returns one layer. Later layers win, and array-valued overrides replace whole lists.
These APIs do not update dependencies already held by instantiated services.

Nafinity supplies its own source and encrypted store; installations do not need to
copy that implementation or call a loader from their `config.php`.

## Mail: describe configurable provider fields

`Naf\Mail\Core\Transport\ConfigurableTransportInterface` optionally extends the
existing transport contract with `configurationFields(): array`. Each colon-separated
path maps to a field description with `label`, `type`, `default`, `index`,
`options` and `sensitive`. This is metadata only: it does not connect or send mail.

`TransportConfiguration::fields($class)` returns the selected provider's metadata,
including the built-in SMTP description. Existing transports continue to work
without the optional interface. Board converts the descriptions into its existing
typed setting definitions and renders them centrally. Providers must explicitly
mark secrets; unknown configuration also receives conservative name/structure
redaction, which cannot replace a provider's schema.

Before publication, update the Nafinity settings, configuration and plugin guides
and regenerate the API inventory for the released signatures.
