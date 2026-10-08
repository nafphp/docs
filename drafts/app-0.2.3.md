# Starter 0.2.3 documentation follow-up

Publish this version-specific update only after `naf/app` v0.2.3 is merged, released and
available on Packagist, and a fresh `composer create-project naf/app` passes its checks.
The demo-removal instructions in `pages/first-app.md` work with the existing published
starter and can be published independently.

For `pages/install.md`, add a short description of the updated starter:

> Starter 0.2.3 includes a charcoal and teal welcome page with the NAF logo mark, rotating
> quotes, links to the source files, and interactive form and JSON demonstrations. The examples
> use `fetch()` to show field errors, success feedback, JSON responses and HTTP status without
> leaving the page. The normal form submission remains available without JavaScript. Both
> examples use the form plugin's CSRF protection and share one token on the welcome page.
> The contact form validates only; it does not send or store a message. `Start fresh` opens
> the cleanup instructions with Copy buttons for terminal commands. `showQuote` in `app/config.php` toggles
> the entire quote panel and defaults to `true`.

When describing cleanup, include `app/views/partials/contact-form.phtml` with the demo PHP
files. Remove `public/js/demo.js` and its `asset()->add()` registration in the shared layout
once the interactive examples and Copy buttons are no longer needed. `Start fresh` guides
the owner through replacing routes and removing files; it does not delete project files
through a public HTTP endpoint.

Keep the existing 0.2.2 dependency-lock history accurate; no new dependency minimums or lock
update are needed for these examples. Refresh generated references if published package
versions have changed. Verify the updated untouched starter through `tools/test_examples.py`
and inspect the published installation and first-app pages after the documentation deploy.
