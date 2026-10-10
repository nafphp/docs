# Documentation follow-up for the pending package fixes

The 2026-10-10 documentation review found six package bugs. Their fixes are open as pull
requests and are **not released yet**, so the published guides describe the released
behaviour and its workarounds. After each release is on Packagist, apply the matching section
below, rerun `tools/gen_reference.py`, `tools/check_pages.py`, `mkdocs build --strict` and
`tools/test_examples.py`, refresh screenshots and console output with
`tools/capture_screenshots.py` where noted, and remove the section from this file.

## naf/framework 0.2.9 (nafphp/framework#11)

Core guard rules exist under CLI; `response.header` listeners are chained.

- `pages/views.md`, "Templates outside HTTP requests": replace the registration workaround with
  "Framework 0.2.9+ registers the rules for every SAPI"; keep the workaround in a collapsed
  note for 0.2.8 and older.
- `pages/guard.md`: change the "Core rules exist only for HTTP requests" warning accordingly;
  blocklist rules without configuration now return `true` instead of a `TypeError`.
- `pages/mail.md`, "Queued delivery": drop the guard-registration sentence for 0.2.9+.
- `pages/events.md`: describe `dispatchResponse()`: each `response.header` listener receives
  the previous listener's response. Replace the "Only one replacement survives" warning with a
  version note, and update "Change a response".
- `pages/lifecycle.md`: mention that guard rules are registered for CLI too.
- Workspace `AGENTS.md` ("Views under CLI" bullet) and `AGENT_EXAMPLES.md` section 5.

## naf/view 0.2.3 (nafphp/view#4)

Asset types come from the URL path; `.mjs` renders as a module; unknown types are logged.

- `pages/views.md`, "Assets": replace the "Only paths ending in .css or .js" warning; describe
  query strings, `.mjs` and the logged warning. The same release also searches `src/views`
  for application templates: update "Where templates are found" (default `view:paths`).

## naf/form 0.2.4 (nafphp/form#3)

`memory()` honours its default and returns the default for array input.

- `pages/forms.md`: replace the "Limits of memory()" note with the new behaviour; keep the
  0.2.3 limitation in the version notes.

## naf/cli 0.2.4 (nafphp/cli#4)

Plain help output with a `vendor/bin/naf` usage line.

- `pages/console.md`: replace the paragraph about literal markers with the new output; add the
  help output to `tools/capture_screenshots.py` (`hello:say --help`) and include it.

## naf/orm 0.2.3 (nafphp/orm#3)

A model's public `table` property is now used for writes as well as reads.

- `pages/orm.md`: mention the public `table` property as an alternative to overriding
  `getTableName()`, for 0.2.3+ (before, writes ignored it).

## naf/app 0.2.4 (nafphp/app#4)

The starter requires Form 0.2.3 and locks framework 0.2.8, form 0.2.3, session 0.2.3 and view 0.2.2.

- `pages/install.md`: update the "Versions included" box.
- `pages/forms.md`: remove the "Starter 0.2.3 still locks Form 0.2.2" warning.
- `pages/recipes/contact-form.md` and `recipes/login-form.md`: the extra `naf/form:^0.2.3`
  step becomes unnecessary for new projects; keep it as a note for older starters.
- `tools/test_examples.py`: the starter fixture no longer needs `naf/form:^0.2.3`.
- Workspace `AGENTS.md` ("Forms" bullet): drop "still locked by starter 0.2.3".
