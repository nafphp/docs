# Mail replies to Nafinity tickets

Pending **naf/board v0.1.6** and the corresponding Nafinity deployment changes.
SMTP uses the published **naf/mail v0.2.3**.
Keep this draft outside `pages/` until the board release is published and the installation
example passes against Packagist.

Nafinity natively polls an existing IMAP mailbox and appends authorized replies as comments
to existing tickets. An incoming message never creates a ticket. The installation sends
outgoing mail through its configured SMTP provider; Postfix can supply that relay but is
not required in the application image. Receiving through an existing mailbox needs no
incoming port, public MX record or additional mail server on the Nafinity host.

## Set up the mailbox

Update the board in the application and migrate its tables:

```sh
bin/composer update naf/board naf/mail --with-dependencies
bin/naf db:migrate up
```

The functionality is part of `naf/board`; no additional package is required. In source
mode the normal Board checkout supplies it through the existing development manifest.

Use a dedicated Nafinity integration account. Its email address does not need a mailbox:

```sh
openssl rand -hex 32 | bin/naf nafinity:user mailbot@operator.example 'Mail import'
```

Add that account to each participating project with permission to read tickets and add
comments. Import checks its current permissions each time. The comment author is this
account; the comment text identifies the original sender as `E-Mail von …`.

Configure the skeleton's private `.env`:

```dotenv
NAFINITY_MAIL_FROM=support@operator.example
NAFINITY_SMTP_HOST=smtp.provider.example
NAFINITY_MAIL_PASSWORD=replace-with-provider-credential

NAFINITY_IMAP_ENABLED=true
NAFINITY_IMAP_HOST=imap.provider.example
NAFINITY_MAIL_ACTOR=mailbot@operator.example
```

One `mail` section in `app/src/config.php` configures outgoing mail and the incoming
mailbox. SMTP and IMAP inherit `NAFINITY_MAIL_PASSWORD` and use `NAFINITY_MAIL_FROM`
as their login. Set `NAFINITY_MAIL_USER` when the login differs from the sender address.
`NAFINITY_MAIL_REPLY_TO` defaults to the sender and should receive replies in the polled
mailbox. Optional `NAFINITY_SMTP_USER` / `NAFINITY_SMTP_PASSWORD` and
`NAFINITY_IMAP_USER` / `NAFINITY_IMAP_PASSWORD` override the shared credentials.
Enable ordinary project notifications and emailed invitations with
`NAFINITY_MAIL_ENABLED=true`. Account-security mail and enabled Mail-to-Ticket
confirmations use the same sender independently of that notification switch.

Apply the environment and check both connections:

```sh
make run
make mail-check
make mail-imap-check
```

The SMTP check verifies connection, TLS policy and login without sending mail.
The IMAP check verifies TLS, login, folder and the existence of the integration account.
It neither imports messages nor sends mail. Project membership is configured separately.
The existing scheduler queues one poll each minute; each poll examines up to 50 new UIDs.

Password authentication works with providers that enable it, including providers requiring
an app password. `NAFINITY_IMAP_AUTH=oauth` uses the password value as an XOAUTH2 access
token. The operator must refresh that token externally and reload the worker environment;
the board does not implement a provider-specific OAuth consent or refresh flow. SMTP
and IMAP may require different credentials and permissions at the same provider.

## Create a case and receive a reply

Create a ticket in Nafinity, or open an existing one. Set **Anfragende E-Mail-Adresse** to
the address permitted to reply. That authorized ticket change creates a random public
reference, visible as **Vorgangsnummer** under Information, and queues a generic confirmation
to the requester. It contains no internal ticket key, title, description or comment text.

The confirmation subject and body contain:

```text
Vorgangsnummer: V-0123456789ABCDEF01234567
```

The token shown here is an example, not a case created by an installation. Actual tokens
contain 96 bits of randomness and do not encode the internal ticket ID. `Ticket-Nr:` is
accepted as an alternative label only when followed by the same kind of public token;
numeric ticket IDs and keys such as `ULX-15` are not accepted.

A reply must contain exactly one distinct public reference in its subject or decoded body
and exactly one From address matching the ticket's current requester. Repeated occurrences
of the same reference are allowed. Domain comparison is case insensitive; local parts,
plus tags and aliases remain exact. Changing or clearing the requester revokes the old
reference. A replacement requester receives a new one.

An accepted reply adds a plain text comment through Board's existing comment service,
including its authorization, activity and notification behavior. The message is marked
seen only after the comment and import receipt commit together. Mailbox identity,
UIDVALIDITY and UID prevent repeat imports; an identical message with the same Message-ID
also stays deduplicated after copying or mailbox recreation. SMTP confirmations can be
delivered again if a process stops after delivery but before recording it.

Unknown or ambiguous references, unmatched senders, automatic replies, empty messages and
oversized messages stay in the mailbox with their existing flags. Invalid date headers and
header conflicts detected as sender spoofing are skipped in the same way. The importer advances
past these messages so they cannot block later replies. To revisit them after correcting
the ticket configuration, run one bounded rescan and then continue normal polling:

```sh
bin/naf nafinity:mail:poll --rescan
bin/naf nafinity:mail:poll
```

MIME and character sets are decoded. HTML-only mail is converted to text. The whole text,
including quoted conversation, is retained; the resulting comment must fit Board's 20,000
character limit. Attachments remain in the mailbox, with a note in the comment. Nothing is
deleted or expunged. Internal comments are not automatically forwarded to the requester.

Matching From and a random reference checks the requested routing rule; it is not a
cryptographic proof of the sender's identity. Keep the receiving provider's spam and mail
authentication controls enabled. The importer does not trust arbitrary
`Authentication-Results` headers as proof.

## Configuration

IMAP keys live under `mail:imap:`. The skeleton maps them from environment variables;
another host supplies its own configuration with NAF's `ENV:NAME` references. Shared
keys are `mail:from`, `mail:reply_to`, `mail:username` and `mail:password`. SMTP lives
under `mail:smtp:` and uses `Naf\Mail\Core\Transport\SmtpTransport` as `mail:transport`.
See [Sending mail](../pages/mail.md#send-through-smtp) for the reusable transport's PHP configuration.

| Key | Skeleton variable | Default | Effect |
|---|---|---|---|
| `enabled` | `NAFINITY_IMAP_ENABLED` | `false` | Enables polling, case generation and confirmation mail. |
| `host` | `NAFINITY_IMAP_HOST` | empty | IMAP server hostname. |
| `port` | `NAFINITY_IMAP_PORT` | automatic | 993 for SSL, 143 for STARTTLS. |
| `security` | `NAFINITY_IMAP_SECURITY` | `ssl` | `ssl` or `starttls`; certificate verification is required. |
| `username` | `NAFINITY_IMAP_USER` | shared login | Optional mailbox login override. |
| `password` | `NAFINITY_IMAP_PASSWORD` | shared password | Optional password/app password or access-token override. |
| `authentication` | `NAFINITY_IMAP_AUTH` | `password` | Password login or `oauth` for XOAUTH2. |
| `folder` | `NAFINITY_IMAP_FOLDER` | `INBOX` | One folder to poll. |
| `ca_file` | `NAFINITY_IMAP_CA_FILE` | system trust | Optional readable CA bundle inside the container, for a private CA. |
| `actor` | `NAFINITY_MAIL_ACTOR` | empty | Active Nafinity integration account email. |
| `batch_size` | host config | `50` | UIDs examined per poll; 1–200. |
| `max_bytes` | host config | `1048576` | Maximum complete message size; 1 KiB–10 MiB. |

## Sending with the operator's domain

Use the provider's approved sender as `NAFINITY_MAIL_FROM`; SMTP defaults to STARTTLS/587
for an external host and implicit TLS when port 465 is selected. `naf/mail` sends directly
from PHP; the image needs no sendmail/msmtp configuration. Its message factory applies the
shared sender and Reply-To to all Board mail. Symfony Mailer handles SMTP, MIME and TLS
inside `naf/mail`. Postfix remains an optional relay configured as the SMTP host, normally
with explicit `NAFINITY_SMTP_AUTH=off` for a trusted local relay.
This does not create DNS records or guarantee that every provider preserves alignment.

Publish the provider's SPF authorization in the domain's existing single SPF record, enable
the provider's DKIM signing and check DMARC alignment using a delivered test message. The
provider supplies the required values. SMTP credentials cannot authorize DNS changes;
automatic DNS setup requires a DNS-provider integration and explicit access. See the
skeleton's `docker/mail/smtp.env.example` for the configuration example.

## Mail views

Board renders every email with native `view('mail/...')` and sends both HTML and a
plain-text alternative. Its shared layout supplies the application name, heading, optional
reference or verification code, action button and a visible fallback URL. There are views
for invitations, notifications, email verification, account-security notices and case
confirmations. Dynamic values are escaped inside the layout, including in queue workers.

Override `app/src/views/mail/layout.phtml` to change the common design, or override an
individual view with the same name. PHP and template changes need no image rebuild.
Environment changes need `make run`. The global mail settings show the effective
notification switch, sender and registered transport configuration. Administrators can
override server values or select **Serverkonfiguration** to inherit them again. These
settings apply to the installation; changes affect new requests, and running workers
need restarting.

## If the result is different

| Symptom | Check |
|---|---|
| The IMAP command is unknown | Update `naf/board` to a release containing the native mail commands. |
| TLS/login fails | Check provider IMAP support, hostname, app password/OAuth permissions and trusted CA. |
| No confirmation | Enable IMAP, configure SMTP, set the requester through a ticket change, and check the queue. |
| Reply stays in the mailbox | Check the public reference, exact From address, automatic-mail headers and message size. |
| Worker reports permission failure | Add the active integration account to the ticket's current project with comment permission. |
| Old skipped mail is not retried | Use `--rescan` once, then normal polling to continue through the folder. |
| SMTP connects but delivery fails | Confirm the provider permits the sender, then inspect delivered mail authentication and DNS. |
