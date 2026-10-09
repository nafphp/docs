---
title: Console commands
example_commands: true    # this chapter invents command names on purpose
requires:
  - naf/cli
---

# Console commands

`naf/cli` runs named commands inside the application's bootstrapped environment. Commands
can use configured services, plugins and logging for imports, maintenance and workers.
Run the examples from the application root unless another directory is specified.

## List and run commands { #running-one }

```bash
vendor/bin/naf command:list
```

With no arguments at all, the binary prints the same list. Every installed plugin
contributes its commands, so what you see depends on what you have installed.

The binary works from any directory: it finds its autoloader through Composer rather than
through the directory you happen to be standing in.

With `naf/cli` 0.2.3+, an application can install a root-level shortcut. From the directory
containing its `composer.json`, run:

```bash
vendor/bin/naf-install
bin/naf command:list
```

The installer creates `bin/naf` and adds a `post-autoload-dump` hook to restore it after
later Composer installs. Commit the shortcut and manifest change with your application.
It leaves a conflicting existing file or symlink untouched. If the application provides
an executable `bin/naf-runtime`, the shortcut delegates runtime selection to that file;
otherwise it runs the Composer binary with local PHP. A missing or non-executable adapter
is an error. The usual `vendor/bin/naf` remains available.

To inspect plugin startup, run `vendor/bin/naf plugins:debug` (or `bin/naf plugins:debug`
when the shortcut is installed). It shows the order, declared prerequisites and optional
targets that are not installed. This command requires framework 0.2.7+.

## Define a command { #writing-one }

A command is a class extending `AbstractCommand`, with a name, a `configure()` that
declares its arguments, and a `run()` that does the work. In a starter application,
create this file:

```php title="app/Commands/HelloCommand.php"
<?php

declare(strict_types=1);

namespace App\Commands;

use Naf\CLI\Core\AbstractCommand;
use Naf\CLI\Core\Input;
use Naf\CLI\Core\Output;

final class HelloCommand extends AbstractCommand
{
    public const string NAME = 'hello:say';

    protected function configure(): void
    {
        $this->setTitle('Say hello')
            ->setDescription('Greets a person by name')
            ->addArgument('name');
    }

    public function run(Input $input, Output $output): int
    {
        if ($input->getOption('help')) {
            $this->showHelp($output);
            return static::SUCCESS;
        }

        $name = $input->getArgument('name');
        if (!is_string($name) || trim($name) === '') {
            $output->writeLine('A name is required.', 'error');
            return static::ERROR;
        }

        $output->writeLine('Hello, ' . trim($name) . '!', 'ok');

        return static::SUCCESS;
    }
}
```

## Register a command { #registering-it }

```php-inline
use function Naf\CLI\command;

command()->add(\App\Commands\HelloCommand::class);
```

Add this registration to root `bootstrap.php`, before `app()->run()`. Commands are not
discovered by scanning `app/Commands/`; application and plugin bootstraps register them
explicitly.

```bash
vendor/bin/naf hello:say World
```

Expect `Hello, World!` and exit status 0. The command explicitly rejects a missing or empty
name; validate inputs in `run()` rather than relying on argument metadata alone. Run
`vendor/bin/naf hello:say --help` for the generated usage information.

## Arguments and options

```php-inline
protected function configure(): void
{
    $this->addArgument('name')                      // required
        ->addArgument('greeting', optional: true)   // optional
        ->addOption('shout', 's')                   // a flag
        ->addOption('repeat', 'r', expectsValue: true);
}
```

```php-inline
$input->getArgument('name');      // ?string
$input->getOption('shout');       // true when present, null when not
$input->getOption('repeat');      // the value, or an array when given more than once
```

Repeated options can return an array. Validate option types and reject repeats when a
command accepts only one value.

## Interactive input { #asking-a-question }

```php-inline
$name = $input->ask('What is your name? ');
```

This blocks for interactive input. Commands used by cron or CI should receive required
values as arguments or options and must not depend on an interactive terminal.

## Writing output

```php-inline
$output->writeLine('Done.', 'ok');        // green
$output->writeLine('Careful.', 'warning'); // yellow
$output->writeLine('Failed.', 'error');    // red
$output->writeLine('Report', 'title');     // light green background
$output->writeLine('Section', 'headline'); // light blue background
$output->writeLine('Plain text');          // no colour
$output->writeEmptyLine();
$output->drawStroke(40);                   // a line of dashes
```

## Exit status { #the-exit-status }

`run()` returns an integer, and that integer becomes the process's exit status.
`static::SUCCESS` is 0, `static::ERROR` is 1.

Return a nonzero status on failure so cron, CI and shell conditionals can detect it.
Test commands through `vendor/bin/naf` as well as their underlying services.
