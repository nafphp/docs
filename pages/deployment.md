---
title: Deploying applications
---

# Deploying applications

Deploy a tested application with its committed `composer.lock`, production configuration and
persistent runtime storage. Serve only `public/`. Use a production web server and supported
PHP runtime; PHP's development server is intended for local use.

## Install a tested release

Run [application tests](testing.md) against the lock file. Check PHP 8.3+ and package-specific
extensions on the target. From the deployed project root:

```bash
composer install --no-dev --prefer-dist --no-interaction --optimize-autoloader
composer check-platform-reqs --no-dev
```

Use `composer update` when intentionally changing dependencies in development. Deployment
uses `install` to reproduce the tested lock. Keep CLI in production dependencies when migrations
or workers need it. Attach protected configuration and persistent storage before starting PHP.

## Production configuration

Set `APP_ENV=prod`. NAF loads `.env.local` instead of `.env` when it exists. Use the exact
value `prod`; an unrecognized value such as `production` can enable diagnostic error output.

Framework 0.2.8+ preserves process environment values over file values. Use `ENV:NAME` references
when configuration may come from the process environment. See [Configuration](configuration.md).
Keep source, dependencies, environment files and private storage outside the document root.

Use HTTPS and configure public application URLs. Behind a TLS-terminating proxy, configure
both trusted addresses and header handling for [sessions](sessions.md#behind-a-proxy).

## Web server routing

This Nginx example assumes `/var/www/my-app/public` and PHP-FPM at `/run/php/php-fpm.sock`.
Replace the host, paths and socket with your server's values. Configure TLS separately.

```nginx
server {
    listen 80;
    server_name app.example.com;
    root /var/www/my-app/public;
    index index.php;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location = /index.php {
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root/index.php;
        fastcgi_pass unix:/run/php/php-fpm.sock;
    }

    location ~ \.php$ {
        return 404;
    }

    location ~ /\.(?!well-known/) {
        deny all;
    }
}
```

Static files are served directly; other paths reach the front controller. This includes dynamic
assets such as Flow's `/_flow/flow.js`. The dotfile rule permits `/.well-known/` for OAuth/OIDC
metadata while denying other hidden paths. Validate and reload Nginx using the server's normal
administration procedure. Consult Nginx's [request routing](https://nginx.org/en/docs/http/ngx_http_core_module.html#try_files)
and [FastCGI parameters](https://nginx.org/en/docs/http/ngx_http_fastcgi_module.html#fastcgi_param)
when adapting it. [Flow](flow.md#development-server) has a router for local PHP servers.

## Persistent storage and permissions

Give PHP and worker users write access to the runtime directories they use. Keep source and
dependencies read-only to them where practical. Preserve runtime data between deployments.

| Feature | Storage |
|---|---|
| Logging | `logs/`, or the configured PSR-3 logger |
| Sessions | PHP `session.save_path`, or database session storage |
| SQLite | Database file and writable parent directory |
| File queues | Queue and deadletter directories in [Queues](queues.md) |
| Scheduler | Shared scheduler state when tickers coordinate |
| MCP | `storage/mcp/`, or the configured token store |
| File storage | Configured local disk roots or remote storage |

Local files are not shared automatically across hosts. Choose shared storage or database-backed
services for features used by multiple application servers.

## Database migrations

Review migrations, take an appropriate backup, and run against the intended database. Requires
Database and CLI:

```bash
vendor/bin/naf db:migrate up
```

Do not run `db:migrate down` without `--name` in production: it reverts every applied
migration. MySQL/MariaDB DDL can commit implicitly, leaving partial work after a failure. A code rollback
does not reverse schema changes. Plan compatibility with the previous application release and
recovery using [migration transaction behavior](database.md#migrations-and-transactions).

## Background processes

Supervise [workers](queues.md#running-the-worker), [tickers](scheduling.md#running-the-ticker)
and [WebSocket servers](websocket.md). Restart them after deployments to load new code and
configuration. Scheduling needs a ticker and worker. Jobs must tolerate repeated delivery
when using a driver with at-least-once delivery.

## Verify and recover

Check a public route and unknown route, then exercise a critical flow with test data. Confirm
assets load, errors are sanitized, persistence works and queued jobs execute. Review application
and server logs, worker status and any configured heartbeat files.

Keep the previous release until verification passes. Restore it through the same deployment
mechanism if necessary, accounting for schema and data changes already applied. See
[Troubleshooting](troubleshooting.md) when checks fail.
