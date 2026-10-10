---
title: Guard
---

# Guard

The guard is a registry of small validation functions. Core rules cover paths, HTML output and
simple blocklists; plugins can add rules of their own, such as `csrf` (`naf/form`) and
`rateLimit` (`naf/rate-limit`).

```php-inline
use function Naf\guard;

$path = guard()->safePath('user.profile');
$text = guard()->safeOutput('<script>'); // &lt;script&gt;
```

## Path validation

`safePath()` rejects empty paths, `..`, absolute paths, stream wrappers and characters outside
`[A-Za-z0-9_/.-]`. It throws `InvalidArgumentException` on rejection.

This is a lexical path check, not a filesystem sandbox: it does not resolve symlinks or prove
that an existing file is inside an allowed directory. Check that separately for file access.

## HTML escaping

`safeOutput()` uses `htmlspecialchars()` with `ENT_QUOTES | ENT_SUBSTITUTE` and UTF-8; `null`
becomes an empty string. It accepts a string or a flat array of string values; nested arrays
are not recursively supported. The view plugin's
`Naf\View\s()` helper delegates to it.

Framework 0.2.9+ registers `safePath`, `safeOutput`, `ipBlacklist` and `userAgentBlacklist`
for every SAPI. Commands, queue workers and the scheduler can use them and View's helpers
after application boot.

??? note "Framework 0.2.8 and older under CLI"
    Core rules are registered only for HTTP. View rendering and escaping can throw
    `RuntimeException: Guard "safeOutput" not found.` Register the rules explicitly or
    update the framework; see [Views](views.md#templates-outside-http-requests).

## CSRF comes from naf/form

`guard()->csrf()` is registered by `naf/form`, which also installs `naf/session`. It is not
available in a core-only application. Prefer the form helper in templates:

```html+php
<?php use function Naf\Form\csrf; ?>
<input type="hidden" name="_csrf" value="<?= csrf()->token() ?>">
```

`token()` (Form 0.2.3+) reuses the session's token, so several forms and tabs stay valid.
Every `generate()` call creates a new token and replaces the previous one; forms rendered
earlier stop validating.

See [Forms and validation](forms.md#csrf-protection) for the checked methods (every method
except GET, HEAD and OPTIONS since Form 0.2.3), header support and named-route exemptions.

## Blocklists

`ipBlacklist($ip, $list = [])` and `userAgentBlacklist($userAgent, $list = [])` throw
`InvalidArgumentException` when the value is in the list and return `true` otherwise. The
comparison is exact. NAF does not call them for you; call them where you want the check:

```php-inline
use function Naf\guard;
use function Naf\request;

guard()->ipBlacklist(request()->getServerParams()['REMOTE_ADDR'] ?? '', ['203.0.113.7']);
```

Without a list argument they read `guard:ipBlacklist` and `guard:userAgentBlacklist` from the
configuration when the rule runs. In Framework 0.2.9+, a missing key means an empty list,
so the rule returns `true`. Define the lists as arrays in `app/config.php` to block values.
For anything beyond a short static list, use a firewall, the web server or
[rate limits](rate-limits.md).

??? note "Blocklists in Framework 0.2.8 and older"
    Define both configuration keys before calling the rules without a list; a missing
    key causes a `TypeError` in these releases.

## Register a rule

```php-inline
use function Naf\guard;

guard()->register('positiveId', function (int $id): int {
    if ($id < 1) {
        throw new \InvalidArgumentException('An ID must be positive.');
    }
    return $id;
});

$id = guard()->positiveId(42);
```

Apply checks at the application boundary and verify rejected inputs in [application tests](testing.md).
