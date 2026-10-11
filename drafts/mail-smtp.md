# Direct SMTP in naf/mail

Implementation notes for **naf/mail v0.2.3**, now published. The maintained guide is
[Sending mail](../pages/mail.md); these notes remain alongside the Mail-to-Ticket draft.
The existing PHP `mail()` transport remains the library default.

Choose SMTP in the host's `config.php`, using native `ENV:NAME` references for secrets:

```php
use Naf\Mail\Core\Transport\SmtpTransport;

return [
    'mail' => [
        'transport' => SmtpTransport::class,
        'from' => 'support@operator.example',
        'reply_to' => 'support@operator.example',
        'username' => 'support@operator.example',
        'password' => 'ENV:MAIL_PASSWORD',
        'smtp' => ['host' => 'smtp.provider.example'],
    ],
];
```

`mailer()->createMail()` and `mail()` apply configured From and Reply-To defaults;
explicit `setFrom()` / `setReplyTo()` calls still override a message. A missing Reply-To
uses From. `new Mail()` remains an unconfigured message object. The SMTP transport is
resolved without opening a network connection or validating SMTP settings. Validation
occurs at the first send or connection check, so incomplete SMTP configuration does not
prevent unrelated pages from opening. Delivery failures raise `MailException`; there is
no fallback delivery method.

| `mail:smtp:` key | Default | Meaning |
|---|---|---|
| `host` | required | SMTP hostname. |
| `port` | automatic | 587 for STARTTLS, 465 for implicit TLS; local plaintext uses 25, `mailpit` uses 1025. |
| `security` | `auto` | External hosts use STARTTLS; port 465 selects `tls`; loopback and `mailpit` use `none`. Explicit values: `starttls`, `tls`, `none`. |
| `authentication` | `auto` | Shared/SMTP login or password enables authentication; otherwise off. Explicit `on`, `off`, `login`, `plain`, `cram-md5`, `xoauth2` / `oauth`. |
| `username` | shared username, then From | Optional SMTP-specific login. |
| `password` | shared password | Optional SMTP-specific password/app password or access token. |
| `timeout` | `15` | Seconds; greater than zero, at most 300. |
| `ca_file` | system trust | Optional readable private-CA bundle. Certificate and hostname verification stay enabled. |

Authentication always requires TLS. Set `authentication => 'off'` explicitly for a trusted
local Postfix relay when the shared mailbox credentials should not be used there.
OAuth uses an externally refreshed access token; this package does not implement provider
consent or token refresh.

For HTML mail, supply the text alternative through `setTextContent($plainText)`:

```php
use function Naf\Mail\mailer;
use function Naf\View\view;

$mailer = mailer();
$message = $mailer->createMail()
    ->addTo('reader@example.com')
    ->setSubject('Your update')
    ->setContent(view('mail/update', ['name' => 'Reader']))
    ->setTextContent('Your update is available.');
$mailer->send($message);
```

The SMTP transport uses Symfony Mailer for SMTP and MIME, including UTF-8 subjects,
CC/BCC envelopes, HTML/text alternatives and attachments. Attachments use the bytes
captured by `Mail::addAttachment()`. The PHP `mail()` transport also preserves the
HTML/text alternative. Views belong to the host or product, not this generic package;
escape dynamic values explicitly when rendering outside HTTP guards.

`SmtpTransport::checkConnection()` verifies connection, TLS and configured authentication
without submitting a message. It does not establish DNS authentication or prove delivery.
The operator's provider must approve From and supply the SPF and DKIM records. DNS setup
and DMARC alignment remain the operator's responsibility.

`composer test:smtp` starts local Mailpit fixtures with a temporary trusted test certificate.
It checks STARTTLS and implicit TLS, login, MIME delivery, rejection of wrong credentials
and rejection of untrusted certificates. No messages leave those fixtures. Stop them with
`docker compose -f tests/Smtp/compose.yaml down --volumes`. Generated test certificates
are ignored by Git.
