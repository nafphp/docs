---
title: Serving files
---

# Serving files { #file-downloads }

Return a PSR-7 response with a stream body to serve a file. Set its content type and disposition
explicitly. The core emitter reads the stream in chunks, so the application does not need to
load the complete file into a string.

The following example starts from [Your first application](first-app.md) and exposes one
application-owned text file publicly. For private files, perform authorization before opening
the stream. See [File storage](file-storage.md) for named local or remote disks.

## Create a file and controller { #downloading-a-file }

From the project root:

```bash
mkdir -p storage/files
php -r 'file_put_contents("storage/files/example.txt", "Example download\n");'
```

Create the controller:

```php title="app/Controllers/DownloadController.php"
<?php

declare(strict_types=1);

namespace App\Controllers;

use Nyholm\Psr7\Stream;
use Psr\Http\Message\ResponseInterface;
use function Naf\{abort, response};

final class DownloadController
{
    public function show(string $id): ResponseInterface
    {
        $files = ['example' => ['example.txt', 'text/plain; charset=UTF-8']];
        if (!isset($files[$id])) {
            abort(404, 'File not found.');
        }

        [$name, $type] = $files[$id];
        $path = BASE_PATH . '/storage/files/' . $name;
        if (!is_file($path) || !is_readable($path)) {
            abort(404, 'File not found.');
        }

        $handle = fopen($path, 'rb');
        if ($handle === false) {
            abort(500, 'Unable to open file.');
        }

        return response('', 200, [
            'Content-Type' => $type,
            'Content-Disposition' => 'attachment; filename="' . $name . '"',
        ])->withBody(Stream::create($handle));
    }
}
```

The route identifier selects a fixed file and download name. It is not concatenated into a
filesystem path or header. Keep this directory application-owned; do not allow uploads to
replace its files or create symlinks in it.

## Register and verify { #example-download-controller }

Add this fragment to the existing `app/routes.php`:

```php-inline
use App\Controllers\DownloadController;
use function Naf\route;

route()->add('GET', '/downloads/{id}', [DownloadController::class, 'show'], 'downloads.show');
```

With the development server running:

```bash
curl -i http://127.0.0.1:8000/downloads/example
curl -i http://127.0.0.1:8000/downloads/unknown
```

Expect 200, the attachment header and `Example download` for the first request; 404 for the
second. A successful handler response does not guarantee a completed client download: the
connection can fail after headers are sent.

## Download behavior { #notes }

`Content-Disposition: attachment` asks the browser to download the response. Use a MIME type
matching the selected content. This example serves the full file; it does not implement
Range requests or resumable downloads. Configure the web server or a suitable file service
when those features are required.
