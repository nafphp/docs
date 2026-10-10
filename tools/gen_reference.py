#!/usr/bin/env python3
"""Builds the function index and the package overview from the PUBLISHED packages.

None of this is maintained by hand: the packages are installed fresh and read, so
the index describes what somebody actually gets.
"""
import argparse, html, json, os, re, shlex, subprocess, sys, tempfile, urllib.request
from pathlib import Path

PAGES = os.path.join(os.path.dirname(__file__), "..", "pages")
KAPITEL = {
    "framework": ("Fundamentals", "lifecycle.md"), "view": ("Views and templates", "views.md"),
    "flow": ("Flow", "flow.md"),
    "form": ("Forms and validation", "forms.md"), "session": ("Sessions", "sessions.md"),
    "database": ("Database", "database.md"), "orm": ("ORM and repositories", "orm.md"),
    "queue": ("Queues and workers", "queues.md"), "schedule": ("Scheduled jobs", "scheduling.md"),
    "mail": ("Sending mail", "mail.md"), "i18n": ("Translations", "translations.md"),
    "client": ("HTTP client", "http-client.md"),
    "storage": ("File storage", "file-storage.md"), "cli": ("Console commands", "console.md"),
    "alexa": ("Alexa+ MCP server", "alexa.md"),
    "mcp": ("MCP tools", "mcp.md"), "auth": ("Authentication and permissions", "auth.md"),
    "oauth-client": ("OAuth client", "oauth-client.md"),
    "oauth-server": ("OAuth authorization server", "oauth-server.md"),
    "rbac": ("Roles and permissions", "rbac.md"),
    "websocket": ("WebSocket notifications", "websocket.md"),
    "board": ("Nafinity", "built-with/nafinity.md"),
}

CORE_GUIDES = {
    "Naf\\app": ("Application lifecycle", "lifecycle.md"),
    "Naf\\abort": ("Abort a request", "errors.md#abort-a-request"),
    "Naf\\config": ("Read configuration", "configuration.md#read-configuration"),
    "Naf\\env": ("Application environment", "configuration.md#application-environment"),
    "Naf\\event": ("Events", "events.md"), "Naf\\guard": ("Guard rules", "guard.md"),
    "Naf\\log": ("Logging", "troubleshooting.md#logging"), "Naf\\route": ("Routing", "routing.md"),
    "Naf\\request": ("Read the request", "request-response.md#read-the-request"),
    "Naf\\param": ("Combined request parameters", "request-response.md#combined-request-parameters"),
    "Naf\\response": ("Responses", "request-response.md#responses"),
    "Naf\\json": ("Responses", "request-response.md#responses"),
    "Naf\\redirect": ("Redirect and refresh", "request-response.md#redirect-and-refresh"),
    "Naf\\refresh": ("Redirect and refresh", "request-response.md#redirect-and-refresh"),
    "Naf\\plugin": ("Plugin metadata", "plugins.md#accessing-plugin-metadata"),
}
LITERAL = re.compile(r"'[^']*'|\"[^\"]*\"|-?\d+(?:\.\d+)?|true|false|null|\[\]", re.I)
# Keys the framework reads through the Config service rather than the config() helper.
EXTRA_READS = {"framework": {"guard:ipBlacklist": "", "guard:userAgentBlacklist": ""}}
CONFIG_READ = re.compile(r"""config\(\s*'([A-Za-z_][\w:.-]*)'\s*(?:,\s*([^()]*?|\[\]|\w+\(\))\s*)?\)""")

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
    command_classes, config_files, config_reads = [], {}, {}
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
        for candidate in ("src/config.php", "app/config.php"):
            if os.path.isfile(os.path.join(root, candidate)):
                config_files[pkg] = os.path.join(root, candidate)
                break
        sources = [os.path.join(root, "bootstrap.php")] if os.path.isfile(os.path.join(root, "bootstrap.php")) else []
        for dirpath, _, files in os.walk(os.path.join(root, "src")):
            sources += [os.path.join(dirpath, f) for f in files if f.endswith(".php")]
        for source in sources:
            for key, default in CONFIG_READ.findall(open(source, encoding="utf-8", errors="replace").read()):
                config_reads.setdefault(pkg, {}).setdefault(key, default.strip())
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
                    declared = re.search(r'^(?:(?:abstract|final|readonly) )*class (\w+)', src, re.M)
                    if namespace and declared:
                        command_classes.append(namespace[1] + '\\' + declared[1])
    reflected = subprocess.run(
        [*shlex.split(os.environ.get('PHP_COMMAND', 'php')), str(Path(__file__).with_name('reflect_functions.php'))],
        input=json.dumps({'project': str(Path(into).resolve()), 'files': function_files}),
        capture_output=True, text=True, check=True)
    details = json.loads(reflected.stdout)
    fns = {name: pkg for name, pkg in fns.items() if name in details}
    extras = json.loads(subprocess.run(
        [*shlex.split(os.environ.get('PHP_COMMAND', 'php')), str(Path(__file__).with_name('reflect_extras.php'))],
        input=json.dumps({'project': str(Path(into).resolve()), 'commands': command_classes,
                          'config_files': config_files}),
        capture_output=True, text=True, check=True).stdout)
    for name, command in extras['commands'].items():
        # The most specific namespace owns the class: Naf\\Queue\\… belongs to naf/queue, not naf/framework.
        owners = [pkg for pkg in meta if command['class'].startswith(meta[pkg]['namespace'] + '\\')]
        command['package'] = max(owners, key=lambda pkg: len(meta[pkg]['namespace']), default='')
    for pkg, keys in EXTRA_READS.items():
        if pkg in meta:
            config_reads.setdefault(pkg, {}).update(keys)
    reference = {'commands': extras['commands'], 'config': extras['config'], 'config_reads': config_reads}
    return fns, meta, sorted(cmds), details, sorted(classes), reference

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
                "| Signature | Purpose | Namespace to import from | Guide |", "| --- | --- | --- | --- |"]
        for fn in names:
            signature = html.escape(details[fn]['signature']).replace('|', '&#124;')
            title, guide = CORE_GUIDES.get(fn, (chapter, link))
            summary = details[fn].get('summary', '').replace('|', '&#124;') or '—'
            out.append(f"| <code>{signature}</code> | {summary} | `{details[fn]['namespace']}` | [{title}]({guide}) |")
        out.append("")
    out += ["</div>", ""]
    out.append(f"*{len(fns)} public functions across {len(set(fns.values()))} packages.*")
    Path(PAGES, "function-index.md").write_text("\n".join(out) + "\n")
    return len(fns)

def command_options(definition):
    """Shortcuts are recorded right after their option; show them together."""
    parts, previous = [], None
    # PHP encodes an empty array as a JSON list.
    for name, mode in (definition.get('options') or {}).items():
        if len(name) == 1 and previous:
            parts[-1] += f" (`-{name}`)"
            continue
        parts.append(f"`--{name}{'=…' if mode == 'value' else ''}`")
        previous = name
    return ", ".join(parts) or "—"


def write_cli_reference(reference, meta):
    out = ["---", "title: CLI commands", "---", "", "# CLI commands", "",
           "Every command that the published packages register, read from the commands' own",
           "definitions. Run them from the application root with `vendor/bin/naf <command>`; install",
           "`naf/cli` and the package that provides the command first. `vendor/bin/naf command:list`",
           "shows the commands of your installation. Generated by `tools/gen_reference.py`.", ""]
    by_package = {}
    for name, command in reference['commands'].items():
        by_package.setdefault(command['package'], []).append((name, command))
    for pkg in sorted(by_package, key=lambda p: (p != "cli", p)):
        chapter, link = KAPITEL.get(pkg, (pkg, None))
        out += [f"## naf/{pkg}", "", f"Version **{meta[pkg]['version']}**" + (f" · [{chapter}]({link})" if link else ""), "",
                "| Command | Purpose | Arguments | Options |", "| --- | --- | --- | --- |"]
        for name, command in sorted(by_package[pkg]):
            arguments = ", ".join(f"`{a}`" + (" (optional)" if mode == "optional" else "")
                                  for a, mode in (command['definition'].get('arguments') or {}).items()) or "—"
            purpose = (command['description'] or command['title'] or '—').replace('|', '&#124;')
            out.append(f"| `{name}` | {purpose} | {arguments} | {command_options(command['definition'])} |")
        out.append("")
    Path(PAGES, "cli-commands.md").write_text("\n".join(out))
    return len(reference['commands'])


def write_config_reference(reference, meta):
    out = ["---", "title: Configuration keys", "---", "", "# Configuration keys", "",
           "Configuration keys that the published packages define or read, with their defaults.",
           "Set them in the array returned by `app/config.php`; nested keys are written with colons",
           "here and as nested arrays in PHP (`session:storage` is `['session' => ['storage' => …]]`).",
           "A key that a package reads without listing it in its own `config.php` shows the default",
           "from the reading code; `—` means the code passes no default and treats the key as absent.",
           "`{BASE_PATH}` stands for the project root. Generated by `tools/gen_reference.py` from the",
           "packages' `config.php` files and `config()` calls; see each guide for the effect.", ""]
    packages = sorted(set(reference['config']) | set(reference['config_reads']), key=lambda p: (p != "framework", p))
    for pkg in packages:
        defaults = reference['config'].get(pkg, {})
        reads = reference['config_reads'].get(pkg, {})
        keys = sorted(set(defaults) | {k for k in reads if not any(d == k or d.startswith(k + ':') for d in defaults)})
        if not keys:
            continue
        chapter, link = KAPITEL.get(pkg, (pkg, None))
        out += [f"## naf/{pkg}", "", f"Version **{meta[pkg]['version']}**" + (f" · [{chapter}]({link})" if link else ""), "",
                "| Key | Default | Defined in |", "| --- | --- | --- |"]
        for key in keys:
            if key in defaults:
                value, source = defaults[key], "`config.php`"
            else:
                value, source = reads[key], "code"
            value = value.replace('|', '&#124;').replace('`', "'")
            if len(value) > 80:
                value = value[:77] + "…"
            if not value:
                cell = "—"
            elif source == "code" and not LITERAL.fullmatch(value):
                cell = "computed in code"   # a variable or constant, not a value worth copying
            else:
                cell = f"`{value}`"
            out.append(f"| `{key}` | {cell} | {source} |")
        out.append("")
    Path(PAGES, "configuration-reference.md").write_text("\n".join(out))
    return sum(1 for line in out if line.startswith("| `"))


def write_packages(meta):
    out = ["---", "title: Package overview", "---", "", "# Package overview", "",
           "Published packages, their required dependencies and optional integrations. Generated from the",
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
        fns, meta, cmds, details, classes, reference = scan(args.project)
        missing = set(KAPITEL) - set(meta)
        if missing:
            sys.exit('Reference installation is missing: ' + ', '.join(sorted(missing)))
    else:
        names = vendor_packages()
        print(f"Reading {len(names)} published packages", flush=True)
        with tempfile.TemporaryDirectory() as tmp:
            install(names, tmp)
            fns, meta, cmds, details, classes, reference = scan(tmp)
    n = write_function_index(fns, details, meta)
    p = write_packages(meta)
    c = write_cli_reference(reference, meta)
    k = write_config_reference(reference, meta)
    with open(os.path.join(os.path.dirname(__file__), "packages.json"), "w") as target:
        json.dump({"functions": fns, "function_details": details, "packages": meta,
                   "commands": cmds, "classes": classes, "command_details": reference['commands'],
                   "config": reference['config'], "config_reads": reference['config_reads']},
                  target, indent=1, sort_keys=True)
        target.write("\n")
    print(f"Generated {n} functions, {p} packages, {len(cmds)} commands ({c} documented), "
          f"{k} configuration keys, {len(classes)} classes/interfaces/traits")
