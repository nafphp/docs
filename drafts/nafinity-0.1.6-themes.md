# Nafinity themes

Waiting for `naf/board` v0.1.6 to be released and available on Packagist.
Keep this draft outside `pages/` until then. After release, add the user-facing
sections to the Nafinity chapter and the token contract to its extension guide.

## Manage themes

An administrator with `settings.manage` opens **Global settings → Themes**.
Choose a built-in palette as a template, enter a name, adjust typography,
corner radius, spacing and the separate light and dark colors, then save.
The isolated preview updates while typing and uses the same compiler as the
saved stylesheet. Changes in the preview do not affect the installation.

**Publish for all users** makes a saved theme selectable in personal settings.
Leave it off to keep a draft. Choose any published theme as the installation
default; anonymous pages, including sign-in, use that default. Each person
selects their theme in the account's personal settings, independently of the
Light, Dark or System brightness setting. **Installation default** follows
future administrator changes. Existing explicit Classic or Anthracite choices
remain explicit after migration; new preferences follow the installation default.

Copy a theme to edit a separate variant. Built-in palettes remain available.
Deleting or unpublishing a personally selected theme falls back to the installation
default without rewriting that person's stored selection. A theme currently used
as the installation default must be replaced before it can be deleted or unpublished.
Theme names and definitions are installation data, not project-specific settings.

## Custom CSS, import and recovery

**Custom CSS** is loaded after the application's component styles and generated
variables. Reuse semantic variables and the shared scales instead of repeating
literal colors or spacing. For example:

```css
.ticket-detail {
    border-top: 2px solid var(--accent);
    padding-top: var(--space-16);
}
```

The example assumes a Nafinity ticket view. It changes the existing
`.ticket-detail` component without changing its stored content.
Use `html[data-theme='dark']` for dark-only rules, and
`@media (prefers-color-scheme: dark)` with `html[data-theme='system']`
for System mode.

CSS is limited to 32 KiB of UTF-8 and checked with a strict CSS parser.
Imports, resource URLs, image resource functions and active legacy CSS syntax
are rejected, including escaped forms. Themes support local CSS customization;
they do not install remote fonts or fetch third-party stylesheets. Custom CSS
can still hide controls or affect readability. The editor's sample runs in a
sandboxed iframe without scripts or form submissions, so an unsaved rule cannot
hide the surrounding editor.

**Export** downloads a versioned JSON document. **Import theme** validates it
before replacing the editor draft; save to persist it. Theme files can be up to
64 KiB, including their JSON envelope. The installation supports up to 16 custom
themes plus its built-ins. Theme configuration is stored through the existing
encrypted installation configuration store, with the same revision conflict
checks and audit trail as other global settings.

If saved CSS prevents normal use, open `/settings?appearance=default#themes`.
That request uses the built-in standard stylesheet and skips custom theme CSS.
The bypass does not change anyone's preferences. Theme saves return to this
safe editor address. **Restore server defaults** removes the administration
override for `nafinity:themes`; host configuration remains the default source.

Published theme CSS is public, including custom CSS and literal text inside it.
Keep credentials and private data out of theme definitions.

## Shared token contract

`src/Resources/public/assets/theme-tokens.json` is the canonical catalog for
built-in palettes, editable tokens and numeric bounds. `Themes::compile()`
builds saved and preview CSS from it. `tools/build-themes.php` generates
`tokens.css` as the shipped fallback. After changing the catalog, run:

```sh
php tools/build-themes.php
npx prettier --write src/Resources/public/assets/tokens.css
```

Components use the same semantic colors (`--bg`, `--surface`, `--text`,
`--muted`, `--line`, `--accent` and status colors) and the derived scales:
`--font-N`, `--space-N` and `--radius-N`. The common `--font-size`,
`--density` and `--radius` values determine those scales. Use
`--radius-full` for pills. Structural dimensions, such as panel widths,
icon geometry and image aspect ratios, remain component dimensions.

Extensions should consume these tokens in their own stylesheets. User-supplied
ticket colors remain ticket data. Explicit branding font/color settings apply
to the brand word only and continue to take precedence there.

Stylesheet addresses contain a SHA-256 content version and can be cached for
one year. A saved edit creates a new URL. An old uncached version returns 404;
an already cached file may remain available until its cache expires.
Theme definitions and revision state are read on the next request.

Verification: `ThemesTest` checks generated token drift, component token use,
light/dark/system compilation and invalid or network-capable CSS.
`ThemesOverHttpTest` covers admin/CSRF boundaries, independent personal choices,
global defaults, drafts, deletion fallback, safe appearance, immutable stylesheet
versions, export and atomic revision conflicts. `themes.test.js` covers preview
races, invalid CSS, base changes and import races.
