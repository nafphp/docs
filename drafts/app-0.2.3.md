# Starter 0.2.3 documentation follow-up

Publish this version-specific update only after `naf/app` v0.2.3 is merged, released and
available on Packagist, and a fresh `composer create-project naf/app` passes its checks.
The demo-removal instructions in `pages/first-app.md` work with the existing published
starter and can be published independently.

For `pages/install.md`, add a short description of the updated starter:

> Starter 0.2.3 includes a charcoal and teal welcome page with the NAF logo mark, rotating
> quotes, links to the source files, and working form and JSON demonstrations. Its welcome
> page explains how to remove the demos or create a fresh project. The contact form validates
> and redirects; it does not send or store a message. `showQuote` in `app/config.php` toggles
> the entire quote panel and defaults to `true`.

Keep the existing 0.2.2 dependency-lock history accurate; no new dependency minimums or lock
update are needed for these examples. Refresh generated references if published package
versions have changed. Verify the updated untouched starter through `tools/test_examples.py`
and inspect the published installation and first-app pages after the documentation deploy.
