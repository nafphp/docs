---
title: File storage
requires:
  - naf/storage
---

# File storage

`naf/storage` exposes named disks for local files, S3-compatible buckets and WebDAV.
Use it for uploads, generated documents and exports. Each disk has its own adapter,
root or remote location, and optional public URL configuration.

Configure disks in the application before calling `storage()`. Authorization, upload policy
and file lifecycle remain application responsibilities.

## Disks

Select a disk by its configured name:

```php-inline
use function Naf\Storage\storage;

storage()->put('foo.txt', 'Hello World');
storage('documents')->put('invoices/2026/1234.pdf', $contents);
storage('public')->url('avatars/123.jpg');
```

`storage()` selects the configured default disk. `storage('documents')` selects that named
disk. Use separate disks for private documents and intentionally public assets.

The disk API supports these operations:

```php-inline
$disk = storage('documents');

$disk->put($path, $contents);
$disk->get($path);
$disk->exists($path);
$disk->delete($path);
$disk->url($path);        // public disks
```

## Configuration and visibility

Configure disks in the application's `app/config.php` or `src/config.php`:

```php-inline
use Naf\Storage\Adapters\LocalAdapter;

return [
    'storage' => [
        'default' => 'documents',
        'disks' => [
            'documents' => [
                'adapter' => LocalAdapter::class,
                'root' => BASE_PATH . '/storage/documents',
            ],
            'public' => [
                'adapter' => LocalAdapter::class,
                'root' => BASE_PATH . '/storage/public',
                'url' => '/storage',
            ],
        ],
    ],
];
```

A URL prefix generates a URL; it does not publish files. Map only the public disk's
root in the web server. Keep private roots outside `public/` and authorize each
private download before streaming it. Local directories/files default to `0700`/`0600`;
an intentionally public disk may set `directoryMode`/`fileMode` to `0755`/`0644`.

`copy()` and `move()` replace destinations and create parents. Missing reads/copies/moves
throw `FileNotFoundException`; deleting a missing file is a successful no-op.
`exists()` checks files. Local writes use a temporary file, preserve an old destination
on failure, and use last-completed-write semantics. Files and SQL are separate transactions.

## Large files

Use streams when files may exceed available memory:

```php-inline
$stream = $disk->readStream($path);
$disk->writeStream($path, $handle);
```

`readStream()` returns a native resource at its beginning; close it in `finally`.
`writeStream()` consumes the current position and leaves the caller's stream open.
It does not rewind it. `get()` still loads the entire file into memory. Transfers are
synchronous; bounded memory does not mean the network operation is asynchronous.

## Path validation and errors { #paths-are-checked-not-trusted }

Paths that escape a disk root are rejected. Invalid paths and failed operations raise
typed exceptions; handle them at the application boundary.

!!! note "This is not an upload lifecycle"
    Quotas, MIME policy, who may read what, and whether a file is allowed to exist at all
    remain application responsibilities. Validate uploads and authorize reads before
    invoking storage operations.

## S3 and WebDAV

Both adapter classes ship with Storage. Their runtime dependencies are opt-in:

```bash
composer require naf/client        # the streaming HTTP transport both need
composer require aws/aws-sdk-php   # S3 only
```

They are declared as suggestions rather than requirements, so a local-only installation pulls
in nothing extra. Additional adapters implement the package's adapter interface and are selected in the
disk configuration.

Remote transfers stream too, which means the temporary filesystem needs room for what is in
flight — that is disk, not memory.


Configure either adapter through the same disk map:

```php-inline
use Naf\Storage\Adapters\S3Adapter;
use Naf\Storage\Adapters\WebDavAdapter;

return [
    'storage' => [
        'disks' => [
            's3' => [
                'adapter' => S3Adapter::class,
                'bucket' => 'application-documents',
                'region' => 'eu-central-1',
                'accessKey' => 'ENV:STORAGE_S3_ACCESS_KEY',
                'secretKey' => 'ENV:STORAGE_S3_SECRET_KEY',
                'prefix' => 'documents',
            ],
            'dav' => [
                'adapter' => WebDavAdapter::class,
                'endpoint' => 'https://cloud.example.com/remote.php/dav/files/alice/',
                'username' => 'ENV:STORAGE_DAV_USERNAME',
                'password' => 'ENV:STORAGE_DAV_APP_PASSWORD',
            ],
        ],
    ],
];
```

S3 requires `aws/aws-sdk-php ^3.395.2`; WebDAV requires `ext-dom`. S3's optional
`endpoint` and `pathStyle` support compatible services. Create the bucket independently,
keep it private, and configure incomplete-multipart cleanup. Credentials are explicit;
IAM role discovery and automatic credential refresh are not provided. S3 `move()` is
copy then delete, so a failed delete can leave both copies.

WebDAV requires an existing authenticated collection supporting PROPFIND, MKCOL, GET,
PUT, DELETE, COPY and MOVE. Parent collections are created as needed. There is no
WebDAV locking; checking file type and mutating are separate requests. Interrupted-write
atomicity depends on the server. Use HTTPS and an application password.

Remote uploads snapshot the remaining input to a temporary file for replay/signing.
Downloads are spooled before `readStream()` returns and can briefly need a second
file-sized disk buffer. Encoded bytes are preserved. A custom PSR-18 client must retain
bounded streaming and disable redirects/retries for signed or credential-bearing transfers.
The native NAF client is resolved lazily; its per-transfer options do not mutate a shared client.

## If the result is different

| What you see | What to check |
|---|---|
| `Storage disk 'name' is missing or is not a configuration array.` | `storage:disks` contains that name, and `storage:default` names an existing disk |
| `Cannot configure storage disk 'name'.` | The previous exception explains the adapter option that failed, for example a missing S3 SDK |
| `The local storage root must be an absolute filesystem directory.` | Use an absolute `root`, such as `BASE_PATH . '/storage/documents'` |
| `FileNotFoundException` | The path is relative to the disk root and the file exists on that disk |
| A public URL returns 404 | The web server serves the public disk's root at its `url`; the URL prefix alone publishes nothing |
