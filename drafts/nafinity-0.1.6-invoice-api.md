# Direct invoice drafts through the core export adapters

Waiting for `naf/board` v0.1.6 to be merged, released and available on Packagist.
Do not publish this feature in `pages/` before then. This is Board core; no separate
Composer integration package is needed. After release, append this section to the
Nafinity chapter after the invoice-item downloads.

## Create a draft directly in your invoicing tool

Choose **Open invoice drafts** in the account modal or the installation's invoice
settings. Add an account for Lexware Office, sevdesk, easybill or FastBill. Enter a
company name and a company identifier to distinguish accounts. These are local labels;
the credentials select the actual issuer, whose address and tax details remain managed
in the provider account. A customer ID identifies the recipient, a separate company.
Multiple accounts per provider are supported. FastBill also requires the API account email.

Accounts have two billing scopes:

- **Personal:** your own settled hours, on a board you can currently read.
- **Company:** everyone's settled hours on the selected board. Managing/using shared
  accounts requires installation `settings.manage` and exporting another person's hours
  additionally requires the board's `export` permission. Installation rights alone do
  not bypass project access. Separate personal and company claims allow a contractor's
  submission and the employer's subsequent customer invoice for the same work.

Select the account, one board, optional inclusive UTC booking dates, the existing recipient's
provider ID, invoice title and date, explicit service dates, EUR net hourly rate and VAT
treatment. The API workflow currently supports standard German VAT at 7/19% and the
small-business treatment at 0%; other tax cases remain outside this workflow. sevdesk
uses system 2.0 and additionally requires the account's `Unity`, `SevUser` and invoice
address `StaticCountry` IDs. Its service period must not end after the invoice date.

The preview reads the existing customer from the provider and shows its returned name,
issuer labels, recipient ID, service dates and positions. Bookings already reserved or
handed over **in the selected billing scope** are omitted. Confirming the immutable preview
creates one draft. Editing a browser request cannot change the prepared positions or
recipient. The preview expires after one hour. API exports allow at most 300 positions
and 5000 unclaimed bookings; narrow the dates for larger selections. Exact minutes and
people remain in each position description; the provider computes totals and rounding.

| Provider | Draft operation | Authentication |
| --- | --- | --- |
| Lexware Office | `POST https://api.lexware.io/v1/invoices?finalize=false` | Bearer API key |
| sevdesk | `POST https://my.sevdesk.de/api/v1/Invoice/Factory/saveInvoice`, status `100`, `taxRule` 1/11 | API key in `Authorization` |
| easybill | `POST https://api.easybill.de/rest/v1/documents`, type `INVOICE` | Bearer API key |
| FastBill | `POST https://my.fastbill.com/api/1.0/api.php`, service `invoice.create` | Basic auth with email and API key |

No adapter finalizes, locks, sends or marks a document paid. easybill's `is_draft` is
read-only; creating the document makes a draft, and Board never calls `/done`. Review
and complete the resulting draft in your provider account before finalizing it there.
The provider account needs an API-enabled subscription and appropriate read/create rights.

### Configure encrypted account storage

The host must provide `nafinity:exports:key`, a base64-encoded random 32-byte key stored
outside the database, and PHP sodium/cURL must be available. In the skeleton this belongs
in `app/src/config.php` (a generic NAF host normally uses `app/config.php`):

```php
'nafinity' => [
    // Preserve the installation's other nafinity settings.
    'exports' => ['key' => 'ENV:NAFINITY_EXPORT_KEY'],
],
```

Generate the environment value with `php -r 'echo base64_encode(random_bytes(32)), PHP_EOL;'`.
Keep it with the installation's secrets and backups. XChaCha20-Poly1305 uses NAF's existing
OAuth-client `Cipher` and binds each credential to its account row, owner and provider.
Missing/changed keys refuse account storage or decryption; there is no plaintext fallback.
Never place keys in a settings field that can be read by browsers. Listing accounts and
rendering the page return only labels and scope, never the API key. Disconnect erases the
stored credential; separately revoke the key at the provider. An already started handover
may still finish. Reconnect after losing or deliberately rotating the encryption key.

### Duplicate prevention and uncertain results

Before the external write, Board commits unique booking claims and a `sending` state.
Within a billing scope a booking can be claimed once across all providers and accounts.
Concurrent confirmations of overlapping previews therefore cannot create two documents.
A repeated confirmation of a completed draft returns its receipt. The network request
uses native `naf/client` with retries disabled, verified HTTPS and no redirects; provider
URLs are fixed. A disconnected account or lost board/installation rights refuses a new send.

An interruption, rejected request or malformed response retains the claims and shows
**Check in invoicing tool**. A saved `sending` state also survives a process crash.
Board cannot know whether the remote server accepted a timed-out write, so it does not
retry automatically. Find the reference `Nafinity <preview-id>` in the correct provider
account. After at least 60 seconds, explicitly record either the existing draft ID or
that no draft exists. Only the latter releases the claims; prepare a new preview afterwards.
Check carefully before releasing: providers do not offer a shared transactional idempotency
contract. A rejection may originate at a proxy after the provider accepted the write.

Recent handovers remain available with their status and external ID. Personal history is
private; authorized installation operators share company history, still subject to current
board export rights. File downloads remain independent: they neither reserve bookings nor
establish that a downloaded file was actually billed. Do not mix manual file imports and
API handovers without checking your external account.

### Add an API adapter

The existing `ExporterDefinition` accepts optional `draftAdapter: YourAdapter::class`.
It appears in `ExporterRegistry::forDrafts()` only when the definition supports `invoice-items`.
The class implements `Contracts\InvoiceDraftAdapterInterface`: `fields()` declares additional
required invoice fields, `customer()` reads the existing recipient, `payload()` wraps the
existing writer's positions, and `create()` makes one external attempt and returns its ID.
Resolve transport through native NAF DI and keep credentials out of responses and exceptions.
Provider-specific payload, authentication and response checks belong in the adapter; account
ownership, encrypted storage, immutable previews and claims remain in the central services.

`InvoiceExportService::rows()` reuses `TimeExportService::bookings()` and `InvoiceItems`;
company grouping additionally separates the original author. `render()` passes rows through
the existing renderer/events/writers. Its optional observer captures transformed positions
for the preview after each writer succeeds. `ExportFinished` describes rendering a completed
position document; it does not claim a remote invoice was created. The durable draft state
and external ID establish the latter.

Verified against official provider documentation on 2026-10-10: [Lexware invoices](https://developers.lexware.io/docs/#create-an-invoice), [sevdesk API](https://api.sevdesk.de/), [easybill REST specification](https://api.easybill.de/rest/v1), [FastBill invoices](https://apidocs.fastbill.com/fastbill/de/invoice.html) and [customer lookup](https://apidocs.fastbill.com/fastbill/de/customer.html).

Regression coverage: Board `InvoiceDraftAdapterTest`, `InvoiceDraftServiceTest` and
`InvoiceDraftsOverHttpTest` verify fake provider contracts, encrypted storage, access
boundaries, separate billing scopes, durable reservations and simultaneous HTTP sends.
The browser workflow was verified with synthetic accounts; no live provider account
was contacted.
