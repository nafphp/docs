# Personal hours export

Waiting for `naf/board` v0.1.6 to be merged, released and available on Packagist.
Do not publish this feature in `pages/` before then.

After release, extend `pages/built-with/nafinity.md` after "Exporting boards":

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

Implementation and verification: see the package's `docs/Profile.md`, `docs/Extensibility.md`
and regression tests `TimeExportTest`, `PersonalExportOverHttpTest`, `ExportFormatsTest`.
