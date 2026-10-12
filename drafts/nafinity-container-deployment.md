# Nafinity container deployment

Publication gate: this guide waits for [Nafinity PR #11](https://github.com/nafphp/nafinity/pull/11)
to merge, its `Container` workflow to publish the first checked image, and an
anonymous pull of the public GHCR package to succeed. Move this guide to
`pages/built-with/nafinity-deployment.md`, add navigation and replace the container
section in `pages/built-with/nafinity.md` with a link after those checks. Do not
publish commands for an image that does not exist yet.

## What you deploy

The official image contains the Nafinity installation and the published Composer
packages recorded in `app/composer.lock`. It includes PHP, nginx, the queue worker,
the scheduler and published assets. Composer and development source mounts are
absent. `compose.production.yaml` adds MariaDB and separate persistent volumes
for the database and `storage/`. Use one application instance with this template.

The repository's default branch is `main`. Each merge builds and checks native
amd64 and arm64 images before publishing `ghcr.io/nafphp/nafinity:main` and a full
`sha-<commit>` tag. A stable GitHub release named `vX.Y.Z` publishes `X.Y.Z` and
`latest`. Pull requests run the same checks without publishing. Multi-platform
images include build provenance and an SBOM. High or critical Trivy findings
block publication; the build upgrades Alpine packages before installing PHP.

Use `main` for staging. For production, select a tested version or digest from
the package page. A digest identifies the exact image; version and branch tags
are registry pointers. A Board source merge alone does not update this image:
release the Board package, update the installation's lock in a reviewed PR, then
build the installation image.

GitHub initially creates container packages with private visibility. An owner
must change this package to public once, then verify an anonymous pull. The
workflow publishes with its own `GITHUB_TOKEN`; consumers of a public image need
no registry login. See [GitHub's container registry guide](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).

## Prepare a first installation

Start from a checkout of the Nafinity installation containing the production
Compose file and `bin/production` helpers. On the Docker host:

```bash
cp .env.production.example .env.production
chmod 600 .env.production
```

Set `NAFINITY_IMAGE` to the selected release tag or digest, `NAFINITY_APP_URL` to
the public HTTPS origin, and two different random database passwords. Configure
DNS and allow ports 80 and 443. The template publishes only nginx; MariaDB has
no host port. SMTP credentials belong in the private environment file. Verify
the actual SMTP provider before using invitations or password resets. Enable
Mail-to-Ticket only after configuring and testing its mailbox and actor account.

Provide a valid certificate chain as `deploy/tls/fullchain.pem` and its private
key as `deploy/tls/privkey.pem`. The container runs as uid/gid 1000. Give that
identity read access to both files and directory traversal, while keeping the
private key unavailable to other host users. Configure certificate renewal on
the host; after replacing the files, run
`bin/production exec -T app nginx -s reload`. The image does not issue or renew
certificates. HTTPS and `APP_ENV=prod` are required. The production CSP allows
same-origin connections; live WebSocket updates are disabled in this template.

`bin/production` always selects the production Compose file, environment and
project explicitly, even when the development `.env` contains `COMPOSE_FILE`.
It does not change or stop the development installation.

```bash
bin/production pull
bin/production up -d --wait db
bin/production run --rm --no-deps -T app php vendor/bin/naf db:migrate up
bin/production run --rm --no-deps -T app php vendor/bin/naf rbac:sync
```

Create the first account with a password read from the terminal. Run this block
in Bash; the password stays out of command arguments and shell history:

```bash
read -r -s -p 'Administrator password: ' admin_password
printf '\n'
printf '%s' "$admin_password" | bin/production run --rm --no-deps -T app \
    php vendor/bin/naf nafinity:user admin@example.com 'Administrator' --admin
unset admin_password
bin/production up -d --wait app
bin/production exec -T app php vendor/bin/naf nafinity:assets:check
```

Sign in at the public URL and create the first project. Production refuses demo
seeding. The health check verifies the web endpoint, database/schema, attachment
storage and worker/scheduler heartbeats. It tests TLS locally without validating
the public certificate name; separately check the public URL with certificate
verification enabled. Monitor that external check and unhealthy containers.

## Back up and verify restoration

The production helpers work with named storage volumes. The development backup
commands target the development bind mount and must not be used for this stack.

```bash
mkdir -m 700 -p /srv/nafinity-backups
bin/production-backup /srv/nafinity-backups/2026-10-13
bin/production-verify-restore /srv/nafinity-backups/2026-10-13
```

Choose a new directory for every backup. The backup stops the application and
its bundled writers, saves a consistent database/storage snapshot, hashes every
storage file and restarts only application containers that were running. Treat
any nonzero exit or missing `SHA256SUMS` as an incomplete backup. Files include
private attachments, OAuth state and sessions: encrypt and copy backups off the
host, restrict access and set a retention policy.

The verification command creates disposable database and storage volumes under
a separate Compose project. It imports the dump, compares all restored storage
hashes, checks readiness and assets, reports restored row counts and removes
only its temporary deployment. It uses the image configured in the current
environment: retain the corresponding image digest with each backup. The archive records
configured image names and the running app image ID/registry digests. It never
restores over production. Before go-live, practise switching to a separately
restored deployment and verify representative users, tickets and attachments.
Keep the private deployment environment and certificate provisioning recoverable
separately; they are deliberately excluded from the data archive.

## Update an installation

Stage the chosen release with a restored copy of production data first. Pulling
an image does not perform migrations or modify the running installation.

```bash
# Set NAFINITY_IMAGE in .env.production to the tested new release or digest.
bin/production pull
bin/production stop app
bin/production-backup /srv/nafinity-backups/before-update
bin/production run --rm --no-deps -T app php vendor/bin/naf db:migrate up
bin/production run --rm --no-deps -T app php vendor/bin/naf rbac:sync
bin/production up -d --wait app
bin/production exec -T app php vendor/bin/naf nafinity:assets:check
```

Use a new backup directory on each update. If migrations fail, keep the
application stopped and inspect the error. An old image can be incompatible
with a new schema; rollback means restoring the matching database and storage
snapshot as well as the previous image. Do not attach several independently
running application deployments to the same storage/database during recovery.

## If the result is different

| Symptom | Check |
| --- | --- |
| Pull returns unauthorized | The first GHCR package may still be private; check package visibility and the selected tag. |
| nginx does not start | Check certificate filenames, uid 1000 read permissions and `bin/production logs app`. |
| App remains unhealthy | Run migrations, inspect worker/scheduler logs and verify database/storage access. |
| Login works but account mail fails | Check SMTP credentials, sender-domain setup and the provider's delivery logs. |
| Restore verification fails | Check backup hashes, retain the backup, and verify with its recorded application image before attempting recovery. |

This template covers one application instance. Replicated deployments need
separate design and acceptance for sessions, shared storage, queue/scheduler
ownership and real client IP handling behind a trusted proxy.
