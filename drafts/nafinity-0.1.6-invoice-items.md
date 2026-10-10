# Personal hours as invoice items

Waiting for `naf/board` v0.1.6 to be merged, released and available on Packagist.
Do not publish this feature in `pages/` before then. This is part of Board core;
there is no additional Composer integration package.

After release, extend `pages/built-with/nafinity.md` after the personal hours export
section drafted in `nafinity-0.1.6-personal-hours.md`:

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
draft creation, see [the API workflow draft](nafinity-0.1.6-invoice-api.md).
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

Implementation and verification: Board's `docs/Invoice-Exports.md`, `InvoiceExportTest`,
`InvoiceExportServiceTest` and `InvoiceExportOverHttpTest`. Provider formats were checked
against the official documentation on 2026-10-10; tests need no provider accounts.
