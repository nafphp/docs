---
title: File storage (0.1.0 draft)
---

# File storage

**Contributor draft for the unreleased `naf/storage 0.1.0`.** Keep this file outside
`pages/` and the public navigation until the package is released and available on
Packagist. The package README describes the full adapter contract and limitations.
No package release is authorized by preparing this guide.

## Installation and configuration

After release, install with `composer require naf/storage`. PHP 8.3+ and
`naf/framework ^0.2` are required. Storage adds no runtime libraries or extension
requirements beyond the framework.

Storage uses NAF's normal plugin discovery, config and container. The default private
disk uses `BASE_PATH . '/storage'`. Directories are created on first write. No manual
plugin registration or directory setup is needed.

Merge this into **`app/config.php`**:

```php
<?php

use Naf\Storage\Adapters\LocalAdapter;

return [
    'storage' => [
        'default' => 'local',
        'disks'   => [
            'local' => [
                'adapter' => LocalAdapter::class,
                'root'    => BASE_PATH . '/storage',
            ],
            'documents' => [
                'adapter' => LocalAdapter::class,
                'root'    => BASE_PATH . '/storage/documents',
            ],
            'public' => [
                'adapter' => LocalAdapter::class,
                'root'    => BASE_PATH . '/storage/public',
                'url'     => '/storage',
            ],
        ],
    ],
];
```

Plugin defaults and application config merge recursively; application values win.
Use `null` to remove an inherited public `url` prefix. Read settings through NAF's
`config('storage:default')`; it is not a configuration setter.

Configuring the adapter is enough; NAF wires the rest. Internally, `StorageManager`
selects the disk, `Storage` provides the returned object's `put()`/`get()`/`url()`
API, and `LocalAdapter` performs local file I/O. `Storage` holds no second backend.
Applications use `storage()` without constructing these classes themselves.

## Store and retrieve files

After the normal application bootstrap, import the helper from `Naf\Storage`:

```php
use function Naf\Storage\storage;

storage()->put('foo.txt', 'Hello World');
$contents = storage()->get('foo.txt');

storage('documents')->put('invoices/2026/1234.pdf', $contents);
$exists = storage('documents')->exists('invoices/2026/1234.pdf');
storage('documents')->copy('invoices/2026/1234.pdf', 'archive/1234.pdf');
storage('documents')->move('archive/1234.pdf', 'archive/2026/1234.pdf');
storage('documents')->delete('archive/2026/1234.pdf');
```

Disks are logical names: backend selection belongs in config. Writes, copies and
moves replace existing files and create parent directories. Missing-file deletion
is a successful no-op; missing read/copy/move sources throw `FileNotFoundException`.
`exists()` checks files, not directories. Same-path copy/move requires an existing
source. No recursive deletion or directory listing is included in this first version.

## Streams for large files

`get()` returns the whole file in memory. Prefer streams for large exports, attachments
or backups. Here is a copy between disks:

```php
use function Naf\Storage\storage;

$stream = storage('documents')->readStream('invoices/2026/1234.pdf');
try {
    storage()->writeStream('backups/1234.pdf', $stream);
} finally {
    fclose($stream);
}
```

The stream is a native PHP resource. `writeStream()` starts at its current position,
never rewinds/closes it, and supports non-seekable input. `readStream()` returns a
readable stream at its beginning; the caller closes it. Stalled/non-blocking streams
with no available data fail the write instead of silently storing partial contents.

Local writes/copies use bounded buffers and a temporary file before replacement.
Failed writes preserve the previous destination and remove temporary files. Concurrent
writes use last-completed-write semantics. These file operations do not form a
transaction with application database records.

## Public URLs and private downloads

```php
use function Naf\Storage\storage;

$url = storage('public')->url('avatars/123.jpg'); // /storage/avatars/123.jpg
```

A disk must have a public URL prefix or an adapter that explicitly provides public
URLs. Otherwise `url()` throws `StorageException`. Prefixes may be root-relative
paths or HTTP(S) URLs without credentials/query/fragment. File name segments are
encoded. URL generation does not check existence or make a file public.

Keep private roots outside `public/`. Explicitly map `/storage` in the web server to
**only** `BASE_PATH . '/storage/public'`. Do not expose the parent storage root,
which also contains the private disks. Authorize private downloads in application
code before streaming them; see the existing file-download guide after publication.

Local permissions default to directories `0700` and files `0600`. When the deployment
requires it, set `directoryMode`/`fileMode` on an intentionally public disk, for example
`0755`/`0644`. Existing directory permissions are preserved. Moves preserve source
permissions; writes/copies apply the disk's file mode. A permission mode does not
configure application authorization or a public URL.

## Security and errors

The package validates paths in HTTP, CLI and workers, even with direct `LocalAdapter`
usage. Traversal, absolute paths, schemes, null/control bytes, backslashes, dot/empty
segments, trailing dots/spaces and Windows device names are rejected. Nested relative
paths such as `attachments/tickets/42/error.png` and ordinary Unicode names work.
Percent escapes are literal filename characters, never URL-decoded by storage.

Local roots and their contents cannot be symlinks; dangling and destination links
and non-regular files are rejected too. Root ancestors are trusted deployment paths.
Keep roots and ancestors protected against hostile local writers, since portable
PHP cannot prevent races with another process replacing directories during I/O.

Catch `Naf\Storage\Exceptions\StorageException` for disk failures. Its subclasses
`FileNotFoundException` and `UnableToWriteException` distinguish missing sources and
write failures. Native errors are preserved as previous exceptions and do not emit
PHP warnings from the local adapter. NAF may wrap service-factory errors in its
`ContainerException`.

## DI and extending storage

Inject `Naf\Storage\Storage` for the default disk or `StorageManager` for named
disks. `storage()` uses `StorageManager::disk(?string $name = null)`. The manager and
disks are lazy and cached. Register application service overrides before first use.

A backend implements `StorageAdapterInterface`, using only paths, strings and PHP
stream resources. Disk options except `adapter`/`url` become named constructor
arguments via NAF's `make()`; other dependencies use normal DI. Each disk constructs
its own adapter, so same-class disks can have different roots or credentials.
Optional `PublicUrlProviderInterface` supports backend-generated public URLs; a
configured prefix takes precedence.

Only `LocalAdapter` is included. A future S3-compatible implementation must be called
`S3Adapter`. HTTP adapters should first reuse `naf/client` and PSR-18, with NAF config,
DI and PSR-3 logging. Flysystem was evaluated and is not needed for the initial local
backend; any future use must stay internal to a NAF adapter.

HTTP upload validation, quotas, MIME rules and application metadata are not adapter
responsibilities. The disk facade currently has no `UploadedFileInterface` overload.
There is no separate upload-staging service in this package.

## Publication checklist

After release, verify the exact package commit on Packagist, execute these examples
against that published version, move this guide to `pages/storage.md` and add
`requires: [naf/storage]`. Add navigation, package selection and file-download links;
refresh the function/package inventory. Run the page checker, strict MkDocs build
and example runner, then complete the delegated documentation merge/deployment.
