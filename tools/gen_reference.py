#!/usr/bin/env python3
"""Builds the function index and the package overview from the PUBLISHED packages.

None of this is maintained by hand: the packages are installed fresh and read, so
the index describes what somebody actually gets.
"""
import json, os, re, subprocess, sys, tempfile, urllib.request

PAGES = os.path.join(os.path.dirname(__file__), "..", "pages")
KAPITEL = {
    "framework": ("Core", None), "view": ("Views and templates", "views.md"),
    "form": ("Forms and validation", "forms.md"), "session": ("Sessions", "sessions.md"),
    "database": ("Database", "database.md"), "orm": ("ORM and repositories", "orm.md"),
    "queue": ("Queues and workers", "queues.md"), "schedule": ("Scheduled jobs", "scheduling.md"),
    "mail": ("Sending mail", "mail.md"), "i18n": ("Translations", "translations.md"),
    "client": ("HTTP client", "http-client.md"), "cli": ("Console commands", "console.md"),
    "mcp": ("MCP tools", "mcp.md"), "auth": ("Authentication and permissions", "auth.md"),
    "oauth-client": ("Signing in with a provider", "oauth-client.md"),
    "oauth-server": ("Being the provider", "oauth-server.md"),
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
    fns, meta, cmds = {}, {}, set()
    vendor = os.path.join(into, "vendor", "naf")
    for pkg in sorted(os.listdir(vendor)):
        root = os.path.join(vendor, pkg)
        cj = json.load(open(os.path.join(root, "composer.json")))
        meta[pkg] = {
            "requires": sorted(k for k in (cj.get("require") or {}) if k.startswith("naf/")),
            "suggests": sorted(k for k in (cj.get("suggest") or {}) if k.startswith("naf/")),
            "description": cj.get("description", ""),
            "php": (cj.get("require") or {}).get("php", ""),
            "namespace": next(iter((cj.get("autoload") or {}).get("psr-4", {})), "").rstrip("\\"),
        }
        for dirpath, _, files in os.walk(os.path.join(root, "src")):
            for f in files:
                if not f.endswith(".php"): continue
                src = open(os.path.join(dirpath, f), encoding="utf-8", errors="replace").read()
                for m in re.finditer(r'^function ([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', src, re.M):
                    fns[m.group(1)] = pkg
                for m in re.finditer(r"const string NAME = '([^']+)'", src):
                    cmds.add(m.group(1))
    return fns, meta, sorted(cmds)

def write_function_index(fns):
    by_pkg = {}
    for fn, pkg in sorted(fns.items()):
        by_pkg.setdefault(pkg, []).append(fn)
    out = ["---", "title: Function index", "---", "", "# Function index", "",
           "Every public function NAF ships, and the package it comes from. Generated from",
           "the published packages on every build, so it cannot go stale.", "",
           "| Package | Functions | Chapter |", "|---|---|---|"]
    for pkg in sorted(by_pkg, key=lambda p: (p != "framework", p)):
        kap, link = KAPITEL.get(pkg, (pkg, None))
        kaptxt = f"[{kap}]({link})" if link else kap
        fns_txt = " ".join(f"`{f}()`" for f in by_pkg[pkg])
        install = "" if pkg == "framework" else f"<br><span style=\"font-size:.85em;opacity:.7\">`composer require naf/{pkg}`</span>"
        out.append(f"| **`naf/{pkg}`**{install} | {fns_txt} | {kaptxt} |")
    out += ["", f"*{len(fns)} functions across {len(by_pkg)} packages.*"]
    open(os.path.join(PAGES, "function-index.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    return len(fns)

def write_packages(meta):
    out = ["---", "title: Package overview", "---", "", "# Package overview", "",
           "What there is, what it requires and what it suggests. Generated from the",
           "`composer.json` of the published packages.", "",
           "| Package | Requires | Suggests | PHP |", "|---|---|---|---|"]
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
        fns, meta, cmds = scan(tmp)
    n = write_function_index(fns)
    p = write_packages(meta)
    json.dump({"functions": fns, "packages": meta, "commands": cmds},
              open(os.path.join(os.path.dirname(__file__), "packages.json"), "w"), indent=1, sort_keys=True)
    print(f"  function-index.md: {n} functions · packages.md: {p} packages · {len(cmds)} commands · tools/packages.json written")
