---
title: Serving files
---

# File Downloads

Sometimes you want to send files to the browser for download instead of displaying them.  
NAF gives you full control to stream files using a custom response.

---

## Downloading a File

You can manually create a response that forces a file download:

```php
use function Naf\response;

$filePath = BASE_PATH . '/storage/files/example.pdf';
$fileName = 'example.pdf';

$response = response(file_get_contents($filePath))
    ->withHeader('Content-Type', 'application/octet-stream')
    ->withHeader('Content-Disposition', 'attachment; filename="' . $fileName . '"');

return $response;
```

- `Content-Type` tells the browser this is a generic file download.
- `Content-Disposition: attachment` forces the download dialog.
- The file is loaded into the response body.

---

## Example: Download Controller

```php
namespace App\Controllers;

use function Naf\response;

class FileController
{
    public function download($filename)
    {
        $path = BASE_PATH . '/storage/files/' . basename($filename);

        if (!file_exists($path)) {
            abort(404, 'File not found.');
        }

        return response(file_get_contents($path))
            ->withHeader('Content-Type', 'application/octet-stream')
            ->withHeader('Content-Disposition', 'attachment; filename="' . basename($filename) . '"');
    }
}
```

- Always use `basename()` to prevent directory traversal attacks.
- Always check if the file actually exists before sending it.

---

## Notes

- For large files, you may want to implement streaming to avoid memory issues.
- You can adjust `Content-Type` based on the file type if needed (e.g., `application/pdf` for PDFs).

Example for PDF:

```php
return response(file_get_contents($pdfPath))
    ->withHeader('Content-Type', 'application/pdf')
    ->withHeader('Content-Disposition', 'attachment; filename="document.pdf"');
```
