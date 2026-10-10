---
title: Troubleshooting and logging
---

# Troubleshooting and logging

When an example behaves differently from the guide, begin with the smallest failing request.
Note its URL, method and HTTP status, then check the terminal running PHP or the web server
log. If `logs/app.log` exists, look for the corresponding application message.

The tutorials include an "If the result is different" section beside their verification steps.
Start there for a symptom specific to that example, then use the sections below to investigate
further. Reproduce the failure locally with the same dependencies and configuration.
Use `APP_ENV=dev` for detailed local errors and keep deployed applications on `APP_ENV=prod`.

A 400 or 422 response can be the expected rejection of invalid input. Compare it with the
guide's valid request before changing configuration. For an API that hides exception details,
read the server log rather than adding those details to the response.

## Logging

The core binds `Psr\Log\LoggerInterface` to a file logger at `logs/app.log` under `BASE_PATH`.
The runtime user needs write access. `Naf\log()` retrieves the registered logger; application
services can receive it through constructor injection.

```php-inline
use function Naf\log;

log()->info('Import completed: {count} records', ['count' => 12]);
log()->error('Import failed: {reference}', ['reference' => $reference]);
```

Include context that helps locate the failure, without passwords, bearer tokens or sensitive
request bodies. The default logger interpolates `{key}` placeholders; context fields without
placeholders are not written separately. Use a PSR-3 implementation suited to your deployment for structured context,
rotation or central collection. Bind it under `LoggerInterface::class` in `bootstrap.php`
before consumers are constructed.

## Routing and bootstrap

| Symptom | Check | Action |
|---|---|---|
| Web-server 404 on all routes | Document root and routing fallback | Serve `public/`; forward nonexistent files to `public/index.php` |
| NAF 404 on one route | Method and path | Inspect `vendor/bin/naf route:debug` with CLI installed |
| Unknown named argument | Placeholder and parameter names | Match `{id}` to `$id` |
| Class not found | Namespace, case and autoload mapping | Check `App\` maps to `app/`; run `composer dump-autoload` |
| Service missing while loading routes | Resolution timing | Register handlers in routes; resolve services after bootstrap bindings |
| `get()` cannot find a concrete class | Service registration | Use constructor injection or `make()` for autowiring |

`php bootstrap.php` does not process HTTP. Under CLI, `run()` returns without routing or
emission. Use a server and [HTTP tests](testing.md#test-http-behavior).

## Plugins and configuration

Plugins must be installed Composer packages of type `naf-plugin`. A cloned sibling directory
does not activate them. With CLI 0.2.3+, `vendor/bin/naf plugins:debug` shows resolved boot order
and prerequisites. Use lazy factories for cross-plugin services. See [Plugins](plugins.md).

For an ignored setting, check `.env.local`, the process environment, its colon-separated path
and merge order. Numeric arrays replace positions. `config()` reads cached configuration;
it is not a setter. `env()` returns the environment name, not an arbitrary variable. See
[Configuration](configuration.md).

## Forms and sessions

| Symptom | Cause to check | Action |
|---|---|---|
| 400 `CSRF token missing or malformed.` | No token field/header, or a non-string value | Include `_csrf` or `X-CSRF-Token` and retain cookies |
| 400 `CSRF token invalid.` | Replaced token or lost session | Render tokens with `csrf()->token()`; fetch a new form after `generate()` replaced the token |
| PATCH or other methods return 400 | Form 0.2.3 checks every method except GET, HEAD and OPTIONS | Send the token with these requests too |
| Undefined template helper | Missing import | Import from `Naf\Form` or `Naf\View` in that template |
| Input lost after redirect | Request-only `memory()` | Render validation errors in the current request or explicitly persist fields |
| Database sessions use files | Missing Database plugin | Inspect the warning, install/configure Database and migrate |

See [Forms](forms.md) and [Sessions](sessions.md) for exact behavior.

## Background work and integrations

For scheduled jobs that do not execute, check the ticker, worker and selected channels. Inspect
worker failures and deadletter storage before retrying. Check permissions, driver and lease
duration. See [Queues](queues.md) and [Scheduling](scheduling.md).

For mail, check the transport: PHP's `mail()` needs delivery configuration, while local capture
intentionally writes no external mail. For HTTP calls, inspect exceptions, CA configuration
and retries. HTTP 4xx/5xx responses must be inspected by the caller; transport failures raise
exceptions. See [Mail](mail.md) and [HTTP client](http-client.md).
