<?php
// Inspect declarations without booting an application or running plugin bootstraps.
putenv('APP_ENV=test');
$input = json_decode(stream_get_contents(STDIN), true, flags: JSON_THROW_ON_ERROR);
require $input['project'] . '/vendor/autoload.php';
foreach ($input['files'] as $file) {
    require_once $file;
}
$result = [];
foreach (get_defined_functions()['user'] as $name) {
    if (!str_starts_with(strtolower($name), 'naf\\')) {
        continue;
    }
    $fn = new ReflectionFunction($name);
    if (str_contains($fn->getDocComment() ?: '', '@internal')) {
        continue;
    }
    $params = [];
    foreach ($fn->getParameters() as $param) {
        $text = ($param->hasType() ? $param->getType() . ' ' : '')
            . ($param->isPassedByReference() ? '&' : '')
            . ($param->isVariadic() ? '...' : '') . '$' . $param->getName();
        if ($param->isDefaultValueAvailable()) {
            $default = $param->getDefaultValue();
            $text .= ' = ' . ($default === [] ? '[]' : ($default === null ? 'null' : var_export($default, true)));
        }
        $params[] = preg_replace('/\s+/', ' ', $text);
    }
    // Keyed by the fully qualified name. Two packages may both offer a
    // `token()`, and keying by the short one silently drops whichever was
    // read second -- from the index as well as from the checker.
    // The first sentence of the docblock, if there is one, describes the function.
    $summary = '';
    foreach (preg_split('/\R/', (string) $fn->getDocComment()) as $line) {
        $line = trim(trim($line), '/* ');
        if ($line === '' || str_starts_with($line, '@')) {
            if ($summary !== '') {
                break;
            }
            continue;
        }
        $summary .= ($summary === '' ? '' : ' ') . $line;
    }
    $result[$fn->getName()] = [
        'summary'   => rtrim(preg_split('/(?<=\.)\s/', $summary)[0] ?? '', '.'),
        'namespace' => $fn->getNamespaceName(),
        'signature' => $fn->getShortName() . '(' . implode(', ', $params) . ')'
            . ($fn->hasReturnType() ? ': ' . $fn->getReturnType() : ''),
    ];
}
echo json_encode($result, JSON_THROW_ON_ERROR);
