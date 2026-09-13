---
title: Umstieg von NixPHP
---

# Umstieg von NixPHP

NixPHP heißt jetzt **NAF**, kurz für *Not Another Framework*. Der alte Name kollidierte
mit [NixOS](https://nixos.org) überall dort, wo es zählte — in Suchergebnissen, in
Paketlisten, und am handfestesten in der Shell: Das CLI-Binary hieß buchstäblich `nix` und
war auf jeder Maschine mit Nix schlicht nicht aufrufbar.

## Was sich geändert hat

| | vorher | nachher |
|---|---|---|
| Composer-Vendor | `nixphp/…` | `naf/…` |
| PHP-Namespace | `NixPHP\` | `Naf\` |
| Konstante | `NIXPHP_BASE_PATH` | `NAF_BASE_PATH` |
| Plugin-Typ | `nixphp-plugin` | `naf-plugin` |
| CLI-Binary | `nix` | `naf` |

## Plugins müssen zusammen mit dem Framework umziehen

Plugins werden über ihren Composer-Pakettyp gefunden, und der heißt jetzt `naf-plugin`.
Ein Plugin, das noch `nixphp-plugin` deklariert, wird **nicht geladen** — ohne Fehler und
ohne Warnung. Framework und alle benutzten Plugins gehören deshalb in einen Schritt.

## Umstellen

```bash
composer remove nixphp/framework
composer require naf/framework:^0.2
```

Dann die Verweise im eigenen Code umschreiben. Unter macOS:

```bash
grep -rl -e 'NixPHP\\' -e 'nixphp/' --include='*.php' --include='composer.json' . \
  | xargs sed -i '' -e 's/NixPHP\\/Naf\\/g' -e 's#nixphp/#naf/#g'
```

Unter Linux nimmt `sed -i` kein Argument — dort entfällt das `''`.

## Die alten Pakete

Die `nixphp/*`-Pakete bleiben auf Packagist, als verwaist markiert und mit Verweis auf den
Nachfolger. Sie bekommen keine weiteren Releases. Die Repositories unter
`github.com/nixphp` bleiben stehen, wo sie sind — jeder bestehende Link funktioniert weiter.
