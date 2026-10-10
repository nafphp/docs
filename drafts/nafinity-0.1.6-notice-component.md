# Nafinity reusable notices

Publication gate: this draft waits for `naf/board` v0.1.6. Keep it outside `pages/`
until that release is published and verified on Packagist. Then fold it into the
Nafinity extension reference.

Invitations, user administration, settings, exports and invoice drafts use the
shared `src/views/components/notice.phtml` component. Invitation forms separate
introductory guidance, form fields and delivery notices with consistent spacing.

Render reusable notices through the native partial helper:

```html+php
<?= \Naf\Board\partial('components/notice', [
    'severity' => 'warning',
    'title'    => \Naf\I18n\t('Check before saving'),
    'message'  => \Naf\I18n\t('This change ends existing sessions.'),
]) ?>
```

`message` and the optional `title` are translated plain text; the component escapes both.
There is no raw HTML argument. `severity` accepts `notice`, `info` (the default), `warning`
and `error`. Unknown values fall back to `info`. Each variant has a local Material Symbols
icon, its own colour and an accessible severity label. Errors use `role="alert"`; other
variants use `role="note"`. Use errors for actual failures rather than general guidance.

For a dynamic message, `messageAttributes` can carry trusted view attributes such as
`['data-account-status' => true, 'role' => 'status']`. The hook is on the message paragraph,
so replacing its `textContent` preserves the icon. An empty notice without a title is hidden.
Keep attribute names in application code; message and attribute values remain escaped.
Shared styling lives in `app.css`, icons in `icons.css`. The ordinary application layout
loads both. A standalone page using this component must also load those stylesheets.

Notice partials use the same override lookup as other views. Existing `field()` and
`choice()` components remain the entry points for form controls; this component does not
change form submission or introduce a second rendering layer.
