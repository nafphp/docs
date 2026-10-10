---
title: Upgrading from NixPHP
---

# Upgrading from NixPHP

NixPHP is now **NAF**, short for *Not Another Framework*. The old name collided with
[NixOS](https://nixos.org) everywhere it mattered — in search results, in package listings,
and most concretely in the shell, where the CLI binary was literally `nix` and could not be
called at all on a machine with Nix installed.

## What changed

| | before | after |
|---|---|---|
| Composer vendor | `nixphp/…` | `naf/…` |
| PHP namespace | `NixPHP\` | `Naf\` |
| Base path constant | `NIXPHP_BASE_PATH` | `NAF_BASE_PATH` |
| Plugin package type | `nixphp-plugin` | `naf-plugin` |
| CLI binary | `nix` | `naf` |

The base-path rename above concerns the framework's internal core directory. Your application
bootstrap still defines `BASE_PATH` as its own project root before loading Composer, as in
[Installation](install.md). Do not replace that application constant with `NAF_BASE_PATH`.

## Plugins have to move with the framework

Plugins are discovered by their Composer package type, and that type is now `naf-plugin`.
A plugin still declaring `nixphp-plugin` is **not loaded** — silently, with no error and no
warning. Move the framework and every plugin you use in the same step.

## Upgrading

```bash
composer remove nixphp/framework
composer require naf/framework:^0.2
```

Then rewrite the references in your own code. The commands skip `vendor/`, which Composer
manages:

=== "macOS"

    ```bash
    grep -rl --exclude-dir=vendor -e 'NixPHP\\' -e 'nixphp/' --include='*.php' --include='composer.json' . \
      | xargs sed -i '' -e 's/NixPHP\\/Naf\\/g' -e 's#nixphp/#naf/#g'
    ```

=== "Linux"

    ```bash
    grep -rl --exclude-dir=vendor -e 'NixPHP\\' -e 'nixphp/' --include='*.php' --include='composer.json' . \
      | xargs sed -i -e 's/NixPHP\\/Naf\\/g' -e 's#nixphp/#naf/#g'
    ```

=== "Windows"

    Use your editor's project-wide search and replace on `*.php` files and `composer.json`,
    excluding `vendor/`: replace `NixPHP\` with `Naf\` and `nixphp/` with `naf/`.

## The old packages

The `nixphp/*` packages stay on Packagist, marked abandoned and pointing at their successors.
They receive no further releases. The repositories under `github.com/nixphp` stay where they
are, so every existing link keeps working.

After updating, run [application tests](testing.md) against the new lock and verify [deployment configuration](deployment.md).
