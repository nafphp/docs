---
title: Console commands
example_commands: true    # this chapter invents command names on purpose
requires:
  - naf/cli
---

# Console commands

Commands you run yourself, or that cron runs for you: a deployment step, a one-off
import, a worker that needs to keep going. They run inside your application, so the
container, the configuration and every plugin are there — unlike a bare PHP script
sitting next to your project.

## Running one

```bash
vendor/bin/naf command:list
```

With no arguments at all, the binary prints the same list. Every installed plugin
contributes its commands, so what you see depends on what you have installed.

The binary works from any directory: it finds its autoloader through Composer rather than
through the directory you happen to be standing in.

With `naf/cli` 0.2.3+, an application can install a root-level shortcut. From the directory
containing its `composer.json`, run:

```sh
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

## Writing one

A command is a class extending `AbstractCommand`, with a name, a `configure()` that
declares its arguments, and a `run()` that does the work.

```php
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
            ->setDescription('Greets somebody by name')
            ->addArgument('name');
    }

    public function run(Input $input, Output $output): int
    {
        $output->writeLine('Hello, ' . $input->getArgument('name') . '!', 'ok');

        return static::SUCCESS;
    }
}
```

## Registering it

```php
use function Naf\CLI\command;

command()->add(\App\Commands\HelloCommand::class);
```

In your application's `bootstrap.php`. **There is no directory that gets scanned** — putting
a class in `app/Commands/` does nothing on its own. Plugins register theirs the same way,
which is why a command appears the moment its package is installed and not before.

```bash
vendor/bin/naf hello:say World
```

## Arguments and options

```php
protected function configure(): void
{
    $this->addArgument('name')                      // required
        ->addArgument('greeting', optional: true)   // optional
        ->addOption('shout', 's')                   // a flag
        ->addOption('repeat', 'r', expectsValue: true);
}
```

```php
$input->getArgument('name');      // ?string
$input->getOption('shout');       // true when present, null when not
$input->getOption('repeat');      // the value, or an array when given more than once
```

An option can come back as an array, so a command that only ever wants one value should say
so rather than assuming a string.

## Asking a question

```php
$name = $input->ask('What is your name? ');
```

Blocks until somebody types something and presses return — which means a command that calls
it cannot run from cron. Give anything scheduled its input as arguments.

## Writing output

```php
$output->writeLine('Done.', 'ok');        // green
$output->writeLine('Careful.', 'warning'); // yellow
$output->writeLine('Failed.', 'error');    // red
$output->writeLine('Report', 'title');     // light green background
$output->writeLine('Section', 'headline'); // light blue background
$output->writeLine('Plain text');          // no colour
$output->writeEmptyLine();
$output->drawStroke(40);                   // a line of dashes
```

## The exit status

`run()` returns an integer, and that integer becomes the process's exit status.
`static::SUCCESS` is 0, `static::ERROR` is 1.

That matters more than it looks: cron, CI and shell `&&` all decide what happens next by
reading it. A command that fails and returns SUCCESS is a deployment step that reports
green while doing nothing.
