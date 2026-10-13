# Nafinity followed tickets and image commands

Publication gates: move the ticket changes into `pages/built-with/nafinity-tickets.md`
after Board v0.1.8 is published on GitHub and Packagist. Move the image changes into
`pages/built-with/nafinity-deployment.md` after the Nafinity image-targets PR is merged
and the exact main commit has passed Container CI and published an anonymously
pullable `latest` tag. The two changes have independent publication gates.

## Personal ticket lists

Append to the personal list section:

Choose **Followed tickets** beside **My tickets** in the workspace menu to see
only tickets you follow. The list spans currently readable, active projects,
starts with open tickets and supports closed/all status, due-date/last-change
sorting and pages of 50 tickets. Archived tickets/projects and projects you can
no longer read are excluded. Assignments and subscriptions remain separate lists.

Replace the following instruction in the notification section:

Use the eye beside a ticket's number and status to follow or unfollow it. An
accent-colored eye with an outlined background means you follow the ticket; a
muted eye means you do not. Hover the button to identify its action;
screen readers receive its action label and pressed state. Readers can follow,
and following does not change the ticket version. With JavaScript, toggling the
eye preserves the open drawer, keyboard focus and unsaved ticket edits; native forms remain
available without JavaScript. Notification channels and the personal relevance
setting still determine whether following produces notifications.

## Container tags

Replace the deployment guide's tag description:

Each merge into `main` builds and checks native amd64 and arm64 images before
publishing `ghcr.io/nafphp/nafinity:main`, `latest` and a full `sha-<commit>` tag.
A stable GitHub release named `vX.Y.Z` also publishes `X.Y.Z` and updates `latest`.
`latest` follows the most recent successful main or stable-release publication;
it is a moving tag, not a promise of an immutable release. Use a tested digest
for a repeatable production deployment. Pull requests run checks without publishing.

Replace the manual build example under **Build your own installation**:

```bash
make image IMAGE=ghcr.io/YOUR_NAMESPACE/nafinity IMAGE_TAG=YOUR_TAG
bin/check-production-image ghcr.io/YOUR_NAMESPACE/nafinity:YOUR_TAG
docker login ghcr.io
make publish IMAGE=ghcr.io/YOUR_NAMESPACE/nafinity IMAGE_TAG=YOUR_TAG
```

Replace `YOUR_NAMESPACE` with your registry namespace and `YOUR_TAG` with the
version or build identifier you intend to publish. Authenticate with an account
that can push there, using Docker's password prompt. Both commands use the same
`IMAGE` and `IMAGE_TAG` values. Defaults are `ghcr.io/nafphp/nafinity` and
`sha-<current full Git commit>`.

`make image` builds the production Dockerfile target from the committed Composer
lock and tags the resulting local image with the chosen tag and `latest`.
`make publish` pushes those two existing tags without rebuilding. It refuses
missing tags or tags referring to different local images; rerun `make image`
with the same settings before publishing. A local build contains the working
tree at build time, so commit/review changes before using its default SHA tag.

Local builds target the Docker host's architecture. Official GitHub Actions
publishes the combined amd64/arm64 image after both native checks pass. A manual
push to the same moving tag replaces its manifest; use a separate namespace
for your own host image. Configure the checked registry digest in `NAFINITY_IMAGE`.
Runtime environment files and storage stay outside the image.
