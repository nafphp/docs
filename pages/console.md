---
title: Console commands
requires:
  - naf/cli
---

# Console commands

<div style="text-align: center;" align="center">

[![NAF CLI Plugin](https://github.com/nafphp/cli/actions/workflows/php.yml/badge.svg)](https://github.com/nafphp/cli/actions/workflows/php.yml)

</div>

[← Back to NAF](https://github.com/nafphp/framework)

---

> **A minimal, developer-friendly command-line interface for your NAF application.**

This plugin gives you a clean CLI system with colored output, argument parsing, and auto-discovered commands. All without external dependencies.

> 🧩 Part of the official NAF plugin collection. Install it if you want powerful CLI tools for development, deployment, and automation.

---

## Usage

### Run a command

```bash
vendor/bin/naf your:command
```

Commands are discovered automatically if placed in your app’s `app/Commands/` directory.

```bash
vendor/bin/naf
```

If you call the helper without arguments, it prints all available CLI commands.

---

### Create a custom command

To create your own CLI command, add a class in the `app/Commands/` folder:

```php
namespace App\Commands;

use Naf\CLI\Core\AbstractCommand;
use Naf\CLI\Core\Input;
use Naf\CLI\Core\Output;

class HelloCommand extends AbstractCommand
{
    public const NAME = 'hello:say';

    protected function configure(): void
    {
        $this->setTitle('Say Hello');
        $this->addArgument('name');
    }

    public function run(Input $input, Output $output): int
    {
        $name = $input->getArgument('name');
        $output->writeLine("Hello, {$name}!", 'ok');
        return static::SUCCESS;
    }
}
```

No registration needed — as long as the class resides in `app/Commands/`, it will be picked up automatically.

Then run:

```bash
vendor/bin/naf hello:say John
```

---

## Colored output

Use `$output->writeLine()` to print messages with color support:

| Type         | Appearance              |
| ------------ | ----------------------- |
| `'ok'`       | ✅ Green                 |
| `'error'`    | ❌ Red                   |
| `'warning'`  | ⚠️ Yellow               |
| `'title'`    | 💡 Light green on black |
| `'headline'` | 📢 Light blue on black  |

You can also draw horizontal lines:

```php
$output->drawStroke(30);
```

---

## Interactive input

You can prompt the user:

```php
$name = $input->ask('What is your name?');
```

---

## File structure

A typical CLI setup might look like this:

```text
app/
└── Commands/
    └── HelloCommand.php

vendor/
└── bin/
    └── nix

bootstrap.php
```

---
