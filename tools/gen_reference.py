#!/usr/bin/env python3
"""Erzeugt Funktionsindex und Paketübersicht aus den VERÖFFENTLICHTEN Paketen.

Nichts hiervon wird von Hand gepflegt: Die Pakete werden frisch installiert und
ausgelesen, damit der Index das beschreibt, was jemand tatsächlich bekommt.
"""
import json, os, re, subprocess, sys, tempfile, urllib.request

PAGES = os.path.join(os.path.dirname(__file__), "..", "pages")
KAPITEL = {
    "framework": ("Kern", None), "view": ("Views und Templates", "views.md"),
    "form": ("Formulare und Validierung", "forms.md"), "session": ("Sessions", "sessions.md"),
    "database": ("Datenbank", "database.md"), "orm": ("ORM und Repositories", "orm.md"),
    "queue": ("Queues und Worker", "queues.md"), "schedule": ("Zeitgesteuerte Jobs", "scheduling.md"),
    "mail": ("E-Mail versenden", "mail.md"), "i18n": ("Übersetzungen", "translations.md"),
    "client": ("HTTP-Client", "http-client.md"), "cli": ("Konsolenbefehle", "console.md"),
    "mcp": ("MCP-Werkzeuge", "mcp.md"), "auth": ("Anmeldung und Rechte", "auth.md"),
    "oauth-client": ("Mit fremdem Konto anmelden", "oauth-client.md"),
    "oauth-server": ("Selbst Provider sein", "oauth-server.md"),
}

def vendor_packages():
    url = "https://packagist.org/packages/list.json?vendor=naf"
    with urllib.request.urlopen(url, timeout=30) as r:
        names = json.load(r)["packageNames"]
    return sorted(n for n in names if n.split("/")[1] not in ("app", "sanity"))

def install(names, into):
    subprocess.run(["composer", "init", "--no-interaction", "--name=naf/docs-reference"],
                   cwd=into, check=True, capture_output=True)
    subprocess.run(["composer", "require", "--no-interaction", "--no-progress", *names],
                   cwd=into, check=True, capture_output=True)

def scan(into):
    """Funktion -> Paket, und Paket -> (requires, suggests)."""
    fns, meta = {}, {}
    vendor = os.path.join(into, "vendor", "naf")
    for pkg in sorted(os.listdir(vendor)):
        root = os.path.join(vendor, pkg)
        cj = json.load(open(os.path.join(root, "composer.json")))
        meta[pkg] = {
            "requires": sorted(k for k in (cj.get("require") or {}) if k.startswith("naf/")),
            "suggests": sorted(k for k in (cj.get("suggest") or {}) if k.startswith("naf/")),
            "description": cj.get("description", ""),
            "php": (cj.get("require") or {}).get("php", ""),
        }
        for dirpath, _, files in os.walk(os.path.join(root, "src")):
            for f in files:
                if not f.endswith(".php"): continue
                src = open(os.path.join(dirpath, f), encoding="utf-8", errors="replace").read()
                for m in re.finditer(r'^function ([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', src, re.M):
                    fns[m.group(1)] = pkg
    return fns, meta

def write_function_index(fns):
    by_pkg = {}
    for fn, pkg in sorted(fns.items()):
        by_pkg.setdefault(pkg, []).append(fn)
    out = ["---", "title: Funktionsindex", "---", "", "# Funktionsindex", "",
           "Jede öffentliche Funktion, die NAF mitbringt, und das Paket, aus dem sie kommt.",
           "Diese Seite wird bei jedem Build aus den veröffentlichten Paketen erzeugt — sie",
           "kann nicht veralten.", "",
           "| Funktion | Paket | Installieren | Kapitel |", "|---|---|---|---|"]
    for pkg in sorted(by_pkg, key=lambda p: (p != "framework", p)):
        kap, link = KAPITEL.get(pkg, (pkg, None))
        kaptxt = f"[{kap}]({link})" if link else kap
        inst = "— im Kern enthalten" if pkg == "framework" else f"`composer require naf/{pkg}`"
        for fn in by_pkg[pkg]:
            out.append(f"| `{fn}()` | `naf/{pkg}` | {inst} | {kaptxt} |")
    open(os.path.join(PAGES, "function-index.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    return len(fns)

def write_packages(meta):
    out = ["---", "title: Paketübersicht", "---", "", "# Paketübersicht", "",
           "Was es gibt, was es voraussetzt und was es empfiehlt. Aus den `composer.json`",
           "der veröffentlichten Pakete erzeugt.", "",
           "| Paket | Braucht | Empfiehlt | PHP |", "|---|---|---|---|"]
    for pkg in sorted(meta, key=lambda p: (p != "framework", p)):
        m = meta[pkg]
        req = ", ".join(f"`{r}`" for r in m["requires"]) or "—"
        sug = ", ".join(f"`{s}`" for s in m["suggests"]) or "—"
        out.append(f"| **`naf/{pkg}`**<br><span style=\"font-weight:400\">{m['description']}</span> | {req} | {sug} | `{m['php']}` |")
    open(os.path.join(PAGES, "packages.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    return len(meta)

if __name__ == "__main__":
    names = vendor_packages()
    print(f"  {len(names)} Pakete auf Packagist: {', '.join(n.split('/')[1] for n in names)}")
    with tempfile.TemporaryDirectory() as tmp:
        install(names, tmp)
        fns, meta = scan(tmp)
    n = write_function_index(fns)
    p = write_packages(meta)
    json.dump({"functions": fns, "packages": meta},
              open(os.path.join(os.path.dirname(__file__), "packages.json"), "w"), indent=1, sort_keys=True)
    print(f"  function-index.md: {n} Funktionen · packages.md: {p} Pakete · tools/packages.json geschrieben")
