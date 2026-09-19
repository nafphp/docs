---
title: File storage
requires:
  - naf/storage
---

# File storage

Files that belong to your application: an uploaded avatar, a generated invoice, an export
somebody downloads once. `naf/storage` gives them one API whether they sit on the local disk,
in an S3-compatible bucket or on a WebDAV server.

## Disks

A disk is a configured place with a name, and naming them is the point:

```php
use function Naf\Storage\storage;

storage()->put('foo.txt', 'Hello World');
storage('documents')->put('invoices/2026/1234.pdf', $contents);
storage('public')->url('avatars/123.jpg');
```

`storage()` without a name is the default disk. `storage('documents')` is somewhere else
entirely — its own root, its own visibility, possibly its own adapter. Public assets and
private documents stay apart because they are different disks, not because everybody
remembers which directory is which.

The everyday operations are what you would expect:

```php
$disk = storage('documents');

$disk->put($path, $contents);
$disk->get($path);
$disk->exists($path);
$disk->delete($path);
$disk->url($path);        // public disks
```

## Large files

Reading a 2 GB export into a string to write it somewhere else is how an application runs out
of memory. Streams avoid that in both directions:

```php
$stream = $disk->readStream($path);
$disk->writeStream($path, $handle);
```

Both ends of the transfer stay bounded, which is what makes a file bigger than the memory
limit possible at all.

## Paths are checked, not trusted

A path that climbs out of its disk's root is **refused**, not normalised into something
harmless-looking. Failures are typed exceptions rather than `false`, so a mistake is visible
where it happens instead of three lines later.

!!! note "This is not an upload lifecycle"
    Quotas, MIME policy, who may read what, and whether a file is allowed to exist at all
    remain your application's decisions. This package moves bytes and says plainly when it
    cannot.

## S3 and WebDAV

Both are opt-in, and neither is installed unless you ask for it:

```bash
composer require naf/client        # the streaming HTTP transport both need
composer require aws/aws-sdk-php   # S3 only
```

They are declared as suggestions rather than requirements, so a local-only installation pulls
in nothing extra. The adapter boundary is a single interface, so a service this package does
not ship is a class and a binding away.

Remote transfers stream too, which means the temporary filesystem needs room for what is in
flight — that is disk, not memory.
