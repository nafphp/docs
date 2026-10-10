<?php
// Read command definitions and configuration defaults without booting an application.
// Commands are created without their constructors, so injected services are not needed;
// configure() only declares the title, description, arguments and options.
putenv('APP_ENV=test');
$input = json_decode(stream_get_contents(STDIN), true, flags: JSON_THROW_ON_ERROR);
require $input['project'] . '/vendor/autoload.php';
// Configuration files may build paths from the application root.
define('BASE_PATH', '{BASE_PATH}');

$commands = [];
foreach ($input['commands'] as $class) {
    try {
        $reflection = new ReflectionClass($class);
        if ($reflection->isAbstract() || !$reflection->isSubclassOf('Naf\CLI\Core\AbstractCommand')) {
            continue;
        }
        $command = $reflection->newInstanceWithoutConstructor();
        $reflection->getMethod('configure')->invoke($command);
        $commands[$class::NAME] = [
            'class'       => $class,
            'title'       => $command->getTitle(),
            'description' => $command->getDescription(),
            'definition'  => $command->getDefinition(),
        ];
    } catch (Throwable $exception) {
        fwrite(STDERR, "Skipping {$class}: {$exception->getMessage()}\n");
    }
}

function flatten(array $values, string $prefix = ''): array
{
    $result = [];
    foreach ($values as $key => $value) {
        $path = $prefix === '' ? (string) $key : $prefix . ':' . $key;
        if (is_array($value) && $value !== [] && !array_is_list($value)) {
            $result += flatten($value, $path);
            continue;
        }
        $result[$path] = describe($value);
    }
    return $result;
}

function describe(mixed $value): string
{
    return match (true) {
        $value instanceof Closure => '(callback)',
        is_object($value)         => $value::class,
        is_array($value)          => $value === [] ? '[]' : json_encode($value, JSON_UNESCAPED_SLASHES),
        is_string($value)         => "'" . $value . "'",
        default                   => var_export($value, true),
    };
}

$config = [];
foreach ($input['config_files'] as $package => $file) {
    try {
        $values = require $file;
        $config[$package] = is_array($values) ? flatten($values) : [];
    } catch (Throwable $exception) {
        fwrite(STDERR, "Skipping {$file}: {$exception->getMessage()}\n");
    }
}

echo json_encode(['commands' => $commands, 'config' => $config],
    JSON_THROW_ON_ERROR | JSON_UNESCAPED_SLASHES | JSON_PARTIAL_OUTPUT_ON_ERROR);
