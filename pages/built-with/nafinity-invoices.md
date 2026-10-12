---
title: Nafinity hours and invoice drafts
---

# Nafinity hours and invoice drafts

With `naf/board` 0.1.6 or newer, export settled personal hours, download invoice positions or prepare a draft in a supported invoicing account. Direct draft creation requires your provider credentials and a separate encryption key in the host configuration.

## Exporting personal hours

Open your account modal and choose **Data export**. Select a board or all boards you can
currently read, an optional UTC booking-date range and PDF, CSV, text or JSON. The download
contains only your booked minutes. Running and paused clocks are not included until settled.

The per-person time journal begins when the new migration is applied. Existing ticket totals
and manual edits have no reliable author and booking date and are not included. Bookings keep
the original ticket key/title after a transfer or ticket deletion; deleting a project removes
its time journal. Read access to the original project is still required.

Export formats use the existing registry. CSV, JSON and text support both tickets and hours;
PDF currently supports hours. Plugin formats opt into datasets using `ExporterDefinition::sources`.
All sources share `ExportRenderer` and the export events; listeners distinguish the `source`.

The hours file is a neutral time report. Creating an invoice additionally needs customer,
seller, prices, taxes and invoice details. EN 16931 is the shared invoice model; XRechnung
and ZUGFeRD/Factur-X are relevant invoice formats. Importing time-based invoice lines into
an accounting application still needs its own verified adapter or API integration.

## Exporting invoice items

Open your account modal and choose **Export invoice items**. Select one board you
can currently read, an optional inclusive UTC booking-date range and the format.
Enter the EUR net hourly rate and tax percentage explicitly; decimal commas and
points are accepted with at most two decimals. Zero is accepted when entered
explicitly. For sevdesk, also enter the hourly `Unity` id from your own account.

The export includes only your settled minutes and groups them by original ticket
id, key and title snapshot. Changed titles remain separate. Minutes are summed
before conversion to decimal hours. Running timers, manual totals and bookings
belonging to other accounts are excluded. The booking dates describe when time
was settled and are not a confirmed service period for the invoice.

| Format | Contents and receiving workflow |
| --- | --- |
| Neutral CSV | Semicolon-separated UTF-8 with BOM, stable headers, exact minutes, hours, `HUR`, EUR net rate and tax percentage; use a mapped importer or manual preparation |
| Lexware Office JSON | Merge `lineItems` into an invoice draft request; add customer/address, invoice date, currency, tax conditions and service/shipping data |
| sevdesk JSON | Merge `invoicePosSave` into `Invoice/Factory/saveInvoice`; add the invoice, contact, currency, net pricing and appropriate tax rule |
| easybill JSON | Merge `items` into a document request; net unit prices use cents; add the customer and remaining document details |
| FastBill JSON | Merge `ITEMS` into `invoice.create`; unit prices use EUR; add `CUSTOMER_ID`, currency and the correct net/tax settings |

The JSON downloads contain API position fragments. They are not complete invoice
requests and cannot be uploaded through the tools' web CSV import screens. The
receiving integration must authenticate, supply invoice details and handle duplicate
submissions. File downloads store no provider credentials and make no provider API calls. For direct
draft creation, see [direct invoice drafts](#create-a-draft-directly-in-your-invoicing-tool).
Downloading does not mark hours as billed; overlapping exports repeat bookings.

The destination computes the invoice totals. Review rounding before finalizing:
neutral hours have six decimal places and Lexware quantities have four, while exact
minutes remain in the description. Lexware exports with more than 300 positions are
refused; narrow the booking-date range when this happens. FastBill's documented item fields have no unit
field; the description includes minutes and hours, and the receiving application
configures the unit display. A percentage alone does not establish a tax case;
the receiving invoice needs the appropriate invoice-level treatment.

### Choosing an import route

The providers' documented CSV imports primarily populate contacts or article/service
catalogues. They do not carry worked quantities into a particular invoice. The core
adapters therefore follow the documented invoice-position APIs:

- [Lexware Office imports](https://help.lexware.de/de-form/articles/548268-welche-daten-kann-ich-in-lexware-office-importieren) and [Invoices API](https://developers.lexware.io/docs/#invoices-endpoint).
- [sevdesk imports](https://hilfe.sevdesk.de/de/articles/9382293-importmoglichkeiten-in-sevdesk) and [API](https://api.sevdesk.de/).
- [easybill service imports](https://support.easybill.de/hc/de/articles/15010075418012-Dienstleistungen-hochladen) and [REST specification](https://api.easybill.de/rest/v1).
- [FastBill product imports](https://support.fastbill.com/hc/de/articles/201715677-Produkte-und-Leistungen), [invoice API](https://apidocs.fastbill.com/fastbill/de/invoice.html) and [item fields](https://apidocs.fastbill.com/fastbill/de/item.html).

### Handing invoices to DATEV

The [DATEV format](https://developer.datev.de/de/file-format/details/datev-format/importexport)
handles accounting data; [Rechnungsdatenservice 1.0](https://www.datev.de/web/de/berufsgruppenuebergreifend/mydatev/datenservices/rechnungsdatenservice-1_0-einrichten)
transfers structured voucher data and/or documents. Neither accepts raw hours as
invoice draft positions. Create and review the invoice in the billing tool, then use
its supported DATEV handover. A direct DATEV adapter would need a complete invoice or
accounting dataset, including the accounting context required by the chosen interface.

### Extending the export

Register an `ExporterDefinition` with `sources: ['invoice-items']` to add a format to
the invoice card. The source reuses `TimeExportService::bookings()` and the existing
`ExportRenderer`, exporter registry and `ExportStarted`, `ExportLine`, `ExportFinished`
events. Writers map normalized position data and have no database or network work.
Original booking ids remain available to export listeners.

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

```php-inline
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

## Extend invoice formats and adapters

The versioned [invoice extension reference](https://github.com/nafphp/board/blob/main/docs/Invoice-Exports.md#extending-the-adapters) describes `ExporterDefinition::sources`, `draftAdapter` and the shared export events. Provider adapters map existing normalized positions; central services retain account authorization, encrypted storage, immutable previews and booking claims.

## If the result is different

| Symptom | Check |
| --- | --- |
| Old ticket totals are absent from an hours report | The journal begins at migration and contains settled bookings, not historical or manually entered totals. |
| An invoicing account cannot be saved or opened | Check PHP sodium/cURL and the unchanged host export encryption key. |
| A draft says Check in invoicing tool | Reconcile the external result before releasing claims or preparing another preview; do not blindly repeat the write. |
| A selection exceeds the position limit | Narrow the board and booking-date range. |
