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

## Plugins have to move with the framework

Plugins are discovered by their Composer package type, and that type is now `naf-plugin`.
A plugin still declaring `nixphp-plugin` is **not loaded** — silently, with no error and no
warning. Move the framework and every plugin you use in the same step.

## Upgrading

```bash
composer remove nixphp/framework
composer require naf/framework:^0.2
```

Then rewrite the references in your own code. On macOS:

```bash
grep -rl -e 'NixPHP\\' -e 'nixphp/' --include='*.php' --include='composer.json' . \
  | xargs sed -i '' -e 's/NixPHP\\/Naf\\/g' -e 's#nixphp/#naf/#g'
```

On Linux, `sed -i` takes no argument — drop the `''`.

## The old packages

The `nixphp/*` packages stay on Packagist, marked abandoned and pointing at their successors.
They receive no further releases. The repositories under `github.com/nixphp` stay where they
are, so every existing link keeps working.
