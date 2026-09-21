#!/usr/bin/env python3
"""Builds the function index and the package overview from the PUBLISHED packages.

None of this is maintained by hand: the packages are installed fresh and read, so
the index describes what somebody actually gets.
"""
import argparse, html, json, os, re, shlex, subprocess, sys, tempfile, urllib.request
from pathlib import Path

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
    "rbac": ("Roles and permissions", "rbac.md"),
    "websocket": ("Live updates", "websocket.md"),
    "board": ("Nafinity", "built-with/nafinity.md"),
}

def vendor_packages():
    url = "https://packagist.org/packages/list.json?vendor=naf"
    with urllib.request.urlopen(url, timeout=30) as r:
        names = json.load(r)["packageNames"]
    return sorted(n for n in names if n.split("/")[1] not in ("app", "sanity"))

def install(names, into):
    subprocess.run([*shlex.split(os.environ.get("COMPOSER_COMMAND", "composer")), "init", "--no-interaction", "--name=naf/docs-reference"],
                   cwd=into, check=True, capture_output=True)
    subprocess.run([*shlex.split(os.environ.get("COMPOSER_COMMAND", "composer")), "require", "--no-interaction", "--no-progress", *names],
                   cwd=into, check=True, capture_output=True)

def scan(into):
    """Funktion -> Paket, und Paket -> (requires, suggests)."""
    fns, meta, cmds, classes, function_files = {}, {}, set(), set(), []
    installed = json.loads(Path(into, 'vendor/composer/installed.json').read_text())
    versions = {p['name']: p['version'] for p in installed['packages']}
    vendor = os.path.join(into, "vendor", "naf")
    for pkg in sorted(os.listdir(vendor)):
        root = os.path.join(vendor, pkg)
        cj = json.load(open(os.path.join(root, "composer.json")))
        meta[pkg] = {
            "version": versions.get("naf/" + pkg, "unknown"),
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
                namespace = re.search(r'^namespace ([\w\\]+);', src, re.M)
                if namespace:
                    for declaration in re.finditer(r'^(?:(?:abstract|final|readonly) )*(?:class|interface|trait|enum) (\w+)', src, re.M):
                        classes.add(namespace[1] + '\\' + declaration[1])
                # Indented too: a helper guarded by `if (!function_exists(...))`
                # is the ordinary way to ship one, and anchoring to the margin
                # missed every such function a package has. A class method can
                # match this as well, which costs nothing -- the reflection below
                # lists functions only, and anything it does not know is dropped.
                if re.search(r'^\s*function ', src, re.M):
                    function_files.append(os.path.join(dirpath, f))
                for m in re.finditer(r'^\s*function ([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', src, re.M):
                    if namespace:
                        fns[namespace[1] + '\\' + m.group(1)] = pkg
                for m in re.finditer(r"const string NAME = '([^']+)'", src):
                    cmds.add(m.group(1))
    reflected = subprocess.run(
        [*shlex.split(os.environ.get('PHP_COMMAND', 'php')), str(Path(__file__).with_name('reflect_functions.php'))],
        input=json.dumps({'project': str(Path(into).resolve()), 'files': function_files}),
        capture_output=True, text=True, check=True)
    details = json.loads(reflected.stdout)
    fns = {name: pkg for name, pkg in fns.items() if name in details}
    return fns, meta, sorted(cmds), details, sorted(classes)

def write_function_index(fns, details, meta):
    out = ["---", "title: Function index", "---", "", "# Function index", "",
           "Generated from the installed releases listed below. Regenerate this snapshot after a",
           "release; function signatures and namespaces are read through PHP reflection.",
           "Functions marked `@internal` are excluded. Import helpers with `use function` in each",
           "PHP file, including templates. See [Dependency Injection](dependency-injection.md)",
           'for services exposed through these helpers.', "", '<div class="function-reference" markdown="1">', ""]
    for pkg in sorted(meta, key=lambda p: (p != "framework", p)):
        names = sorted(fn for fn, owner in fns.items() if owner == pkg)
        if not names:
            continue
        chapter, link = KAPITEL.get(pkg, (pkg, None))
        link = link or "first-app.md"
        out += [f"## naf/{pkg}", "", f"Version **{meta[pkg]['version']}** · [{chapter}]({link})", "",
                "| Signature | Namespace to import from |", "| --- | --- |"]
        for fn in names:
            signature = html.escape(details[fn]['signature']).replace('|', '&#124;')
            out.append(f"| <code>{signature}</code> | `{details[fn]['namespace']}` |")
        out.append("")
    out += ["</div>", ""]
    out.append(f"*{len(fns)} public functions across {len(set(fns.values()))} packages.*")
    Path(PAGES, "function-index.md").write_text("\n".join(out) + "\n")
    return len(fns)

def write_packages(meta):
    out = ["---", "title: Package overview", "---", "", "# Package overview", "",
           "What there is, what it requires and what it suggests. Generated from the",
           "`composer.json` of the published packages.", "",
           "| Package | Version | Requires | Suggests | PHP |", "|---|---|---|---|---|"]
    for pkg in sorted(meta, key=lambda p: (p != "framework", p)):
        m = meta[pkg]
        req = ", ".join(f"`{r}`" for r in m["requires"]) or "—"
        sug = ", ".join(f"`{s}`" for s in m["suggests"]) or "—"
        out.append(f"| **`naf/{pkg}`**<br><span style=\"font-weight:400\">{m['description']}</span> | `{m['version']}` | {req} | {sug} | `{m['php']}` |")
    open(os.path.join(PAGES, "packages.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    return len(meta)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', help='Read an existing installation of all documented packages')
    args = parser.parse_args()
    if args.project:
        fns, meta, cmds, details, classes = scan(args.project)
        missing = set(KAPITEL) - set(meta)
        if missing:
            sys.exit('Reference installation is missing: ' + ', '.join(sorted(missing)))
    else:
        names = vendor_packages()
        print(f"Reading {len(names)} published packages", flush=True)
        with tempfile.TemporaryDirectory() as tmp:
            install(names, tmp)
            fns, meta, cmds, details, classes = scan(tmp)
    n = write_function_index(fns, details, meta)
    p = write_packages(meta)
    with open(os.path.join(os.path.dirname(__file__), "packages.json"), "w") as target:
        json.dump({"functions": fns, "function_details": details, "packages": meta,
                   "commands": cmds, "classes": classes}, target, indent=1, sort_keys=True)
        target.write("\n")
    print(f"Generated {n} functions, {p} packages, {len(cmds)} commands, {len(classes)} classes/interfaces/traits")
