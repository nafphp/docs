#!/usr/bin/env python3
"""Check all documentation pages, including nested recipes, against the release snapshot.

Validate package requirements, helper namespaces, imported NAF classes and command names.
Use gen_reference.py to refresh the snapshot; test_examples.py exercises complete recipes.
"""
import glob, json, os, re, sys

HERE = os.path.dirname(__file__)
data = json.load(open(os.path.join(HERE, "packages.json"), encoding="utf-8"))
pkgs, fns = data["packages"], data["functions"]
cmds = set(data.get("commands", []))
ns_of = {f: pkgs[p]["namespace"] for f, p in fns.items() if p in pkgs}

PAT_BRACE  = re.compile(r'use function ([\w\\]+?)\\\{([\w, ]+)\}')
PAT_SINGLE = re.compile(r'use function ([\w\\]+?)\\(\w+)\s*;')
problems = []

for path in sorted(glob.glob(os.path.join(HERE, "..", "pages", "**", "*.md"), recursive=True)):
    name = os.path.relpath(path, os.path.join(HERE, "..", "pages"))
    text = open(path, encoding="utf-8").read()

    if text.startswith("---"):
        inside, req = False, []
        for line in text.split("---", 2)[1].split("\n"):
            if line.strip() == "requires:":
                inside = True; continue
            if inside:
                if line.startswith("  - "): req.append(line[4:].strip())
                elif line.strip(): inside = False
        for r in req:
            if not r.startswith("naf/") or r.split("/", 1)[1] not in pkgs:
                problems.append(f"{name}: requires '{r}', which does not exist")

    for m in re.finditer(r'composer require ((?:naf/[\w-]+ ?)+)', text):
        for pkg in m.group(1).split():
            if pkg.split("/", 1)[1] not in pkgs:
                problems.append(f"{name}: 'composer require {pkg}' names a package that does not exist")

    for m in re.finditer(r'composer create-project ([\w-]+/[\w-]+)', text):
        if m.group(1) != 'naf/app':
            problems.append(f"{name}: unknown starter package '{m.group(1)}'")

    known_classes = set(data.get('classes', []))
    if known_classes:
        class_imports = []
        for m in re.finditer(r'^use (Naf\\[\w\\]+)\s*;', text, re.M):
            class_imports.append(m.group(1))
        for m in re.finditer(r'^use (Naf\\[\w\\]+)\\\{([\w, ]+)\};', text, re.M):
            class_imports.extend(m.group(1) + '\\' + n.strip() for n in m.group(2).split(','))
        for imported in class_imports:
            if imported not in known_classes:
                problems.append(f"{name}: imports unknown class/interface/trait {imported}")

    invented = re.search(r'^example_commands:\s*true\b', text, re.M) is not None
    for m in re.finditer(r'bin/naf ([a-z][a-z:_-]+)', text):
        if cmds and not invented and m.group(1) not in cmds:
            problems.append(f"{name}: 'naf {m.group(1)}' is not a registered command")

    imports = [(m.group(1), [n.strip() for n in m.group(2).split(",")]) for m in PAT_BRACE.finditer(text)]
    imports += [(m.group(1), [m.group(2)]) for m in PAT_SINGLE.finditer(text)]
    for ns, names in imports:
        for n in names:
            want = ns_of.get(n)
            if want is None:
                problems.append(f"{name}: imports {ns}\\{n}(), which no package provides")
            elif want != ns:
                problems.append(f"{name}: imports {ns}\\{n}(), but it lives in {want}")

# The other direction: a command nobody wrote about. The old documentation drifted
# because nothing noticed; a build that fails is the only thing that demonstrably did.
documented = set()
for path in glob.glob(os.path.join(HERE, "..", "pages", "**", "*.md"), recursive=True):
    text = open(path, encoding="utf-8").read()
    for c in cmds:
        if c in text:
            documented.add(c)
for c in sorted(cmds - documented):
    problems.append(f"command '{c}' is registered by a package but appears in no chapter")

if problems:
    print("Pages do not match the published packages:", file=sys.stderr)
    for p in problems:
        print("  " + p, file=sys.stderr)
    sys.exit(1)
pages_count = len(glob.glob(os.path.join(HERE, "..", "pages", "**", "*.md"), recursive=True))
print(f"  pages check: {pages_count} pages, {len(pkgs)} packages, {len(fns)} functions, {len(cmds)} commands, nothing out of step")
