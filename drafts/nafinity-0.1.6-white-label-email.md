# White-label identity and email design

Waiting for `naf/board` v0.1.6 to be released and available on Packagist.
Keep this draft outside `pages/` until then. After release, add the administrator
steps to the Nafinity chapter and link the mail template contract from its extension guide.

## Use one public identity

Open **Global settings → General → Appearance & landing page** to choose the application
name and upload a PNG, JPEG or WebP logo. The same identity appears in navigation,
sign-in, public account pages, browser titles and favicon, the local AI assistant,
notification preferences and outgoing email. The branding wordmark's chosen font
and color also apply to the email header. A logo in email uses the public application
URL; configure `app:url` to an HTTP or HTTPS address that recipients can reach.

New invoice drafts use the application name in their external reference. The
reference is frozen with the provider payload when the draft is prepared. Renaming
the application does not change a prepared or previously submitted reference.
Older drafts display the reference from their stored provider payload so a person
can still find an uncertain submission in the external invoicing account.

Technical names such as Composer packages, namespaces, commands, configuration
paths, browser storage keys and AI tool identifiers retain their existing names.
Demo board names and the documented demo password identify fixture data; changing
the application branding does not rename projects or change credentials.

## Design outgoing email

An administrator with `settings.manage` opens **Global settings → General → Email design**.
Choose the background, surface, text, secondary text, border and accent colors,
then adjust font family, base size, corner radius and spacing. The design is global;
a recipient's personal application theme does not change sent email.

The live preview uses sample data. Switch between invitation, password reset,
email verification, security notice and notification, and choose Desktop or Mobile
width. Previewing sends no email and does not save the draft. **Save email design**
applies it to subsequent messages; **Reset email design** restores server defaults.
An outdated configuration revision is rejected rather than overwriting a newer edit.

Click **Send a test email to me** to send the selected sample with the current unsaved
design through the configured mail transport. The server resolves the signed-in account's
current email address; the action cannot send to another recipient. It does not save the
design, create a real invitation/reset code or change notification preferences. Automatic
preview updates never send mail. Three test emails per account per minute are allowed.
A transport failure keeps the draft intact and asks you to check email configuration.

The preview and sender use the same HTML renderer and CSS inliner. Colors and scale
variables are resolved to literal values before CSS is embedded into the elements.
Email clients support different CSS features; check important layouts in the intended
clients as well as in the browser preview. No remote fonts are loaded.

## Grouped settings and modal navigation

**General** contains branding and landing page, interface themes, email design
and advanced display options. Technical application values and activity-log retention appear
under **Application & activity log** when advanced settings are enabled. Opening a child
settings card keeps its parent underneath.
The parent moves upward and leaves a named navigation header. Each ancestor header stays
operable through the active dialog, while background forms remain inert. Clicking its title
returns to that dialog by closing only its descendants, newest first. The separate close
button also closes the chosen dialog; the oldest close button closes the whole stack.
A dirty or busy dialog can stop the cascade through its normal cancel guard. Deep stacks
keep all ancestor names available in a scrollable strip. Closing a child restores its
parent's position, scroll and focused trigger.
Unsaved form fields stay in their original DOM nodes. The native stack has no fixed logical
depth; the visual offset is bounded to fit the screen. Reduced motion skips animations.
Direct links such as `#themes` and `#email-design` restore the same parent hierarchy.

Project and installation role lists open their existing edit/create forms in child dialogs.
Columns, swimlanes and labels use those same editors for existing entries and additions,
while reorder controls stay in the parent list.
Board members open **Add member** or **Invite a new person** over the unchanged list and
pending invitations. The theme library and installation default stay in the parent; choosing
or importing a theme opens its editor with the live preview. Closing an editor preserves
its draft and returns focus to the trigger; saving uses the existing endpoints and restores
the containing settings card. Without JavaScript these forms remain native disclosures.

The installation's people directory also uses the shared settings shell for account details,
inviting a person and bulk changes. Search and selection remain in the parent list; children
share its stacking, ancestor navigation, close controls and focus restoration. Invitation and
bulk forms retain their existing authorization and submission paths.

Extensions can set `parent: 'application'` or another same-scope section id on
`Naf\Board\Definition\SettingSection`. The generic renderer handles child cards and
modal shells without feature-specific JavaScript. Authorized children of a removed or
hidden parent appear at the root; cyclic parent definitions are rejected. New dialogs
opened through the existing `data-dialog` controls or shared `assets/dialog.js` receive
stacking, parent suspension, focus restoration and animated exit automatically.

Theme and email previews use sandboxed inline HTML documents with no scripts. Theme
samples no longer load a separate page into the frame, so the installation can retain
`X-Frame-Options: DENY` and `frame-ancestors 'none'`. Both previews keep their styles
isolated from settings and use the modal body as their scroll container. Theme samples
allow local stylesheets, icons and fonts from the exact HTTP origin, including the port,
so Firefox also renders their inline documents. The installation does not need to relax
its frame protection. Hosts that map an internal web-server port to a different public
port need the request-authority correction prepared for `naf/framework` v0.2.11.

## Add custom email CSS

Custom CSS is applied after the shared base styles and before inlining. Use the
stable layout classes `.email-header`, `.email-brand-name`, `.email-title`,
`.email-content`, `.email-intro`, `.email-paragraph`, `.email-button`,
`.email-highlight` and `.email-footer`.

```css
.email-title {
  color: var(--accent);
  padding-bottom: var(--space-16);
}

.email-button {
  border-radius: var(--radius-8);
}
```

The designer uses the same semantic names and scale catalog as interface themes:
`--bg`, `--surface`, `--text`, `--muted`, `--line`, `--accent`, `--on-accent`,
`--font-family`, `--font-size`, `--radius`, `--density`, `--space-*`, `--font-*`
and `--radius-*`. Font stacks use the shared System, Serif and Monospace choices.
Use simple `var(--name)` references to these known tokens. The validator rejects
unknown variables, invalid values, imports, resource URLs and active CSS. Custom CSS
is limited to 32 KiB. Email layout is table based and does not require scripts.

## Host defaults and template overrides

The typed installation setting `appearance.email` maps to `nafinity:email_design`.
It holds `common`, `colors` and `css`; omitted common and color entries inherit the
shared email defaults. Only installation administrators can read or write the
preview and save endpoints. Generic settings API writes run the same validator.

Board message producers use `Naf\Board\Mail\Messages` and native `mail/...` views.
The shared `mail/layout` contains the branding and stable CSS classes. Messages
have HTML and a plain-text alternative with their action URLs. A host can override
an individual view or the shared layout through its existing view paths. A custom
layout without `data-email-layout` is left intact and is responsible for its own
styles; layouts retaining that marker participate in the shared design inliner.

## If the result is different

| Symptom | Check |
| --- | --- |
| Changes appear only in the preview | Save the email design; drafts do not change outgoing messages. |
| A newer edit is reported | Reload global settings and apply the edit to the latest revision. |
| A custom rule is rejected | Check CSS syntax, token names, the 32 KiB limit and resource URL restrictions. |
| A test email does not arrive | Check the configured mail transport and recipient account address; a successful send means the transport accepted the message, not a guarantee of inbox placement. |
| A logo is missing in a recipient's client | Check the public `app:url` and whether that client blocks remote images. |
| A host template ignores the design | Keep `data-email-layout` on the layout body to use the shared inliner, or maintain the override's own styles. |
