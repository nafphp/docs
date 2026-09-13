#!/usr/bin/env python3
"""Fails the build on two mistakes the old documentation made for a year.

1. A page declaring a package that does not exist — how the old Requirements
   sections came to claim `naf/framework >= 1.0` and PHP 8.1.
2. A `use function` import naming the wrong namespace — fifteen of those were
   in the pages, every one of them a runtime error for anyone copying it.

Both are checked against the published packages, not against a list kept here.
"""
import glob, json, os, re, sys

HERE = os.path.dirname(__file__)
data = json.load(open(os.path.join(HERE, "packages.json"), encoding="utf-8"))
pkgs, fns = data["packages"], data["functions"]
ns_of = {f: pkgs[p]["namespace"] for f, p in fns.items() if p in pkgs}

PAT_BRACE  = re.compile(r'use function ([\w\\]+?)\\\{([\w, ]+)\}')
PAT_SINGLE = re.compile(r'use function ([\w\\]+?)\\(\w+)\s*;')
problems = []

for path in sorted(glob.glob(os.path.join(HERE, "..", "pages", "*.md"))):
    name = os.path.basename(path)
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

    imports = [(m.group(1), [n.strip() for n in m.group(2).split(",")]) for m in PAT_BRACE.finditer(text)]
    imports += [(m.group(1), [m.group(2)]) for m in PAT_SINGLE.finditer(text)]
    for ns, names in imports:
        for n in names:
            want = ns_of.get(n)
            if want is None:
                problems.append(f"{name}: imports {ns}\\{n}(), which no package provides")
            elif want != ns:
                problems.append(f"{name}: imports {ns}\\{n}(), but it lives in {want}")

if problems:
    print("Pages do not match the published packages:", file=sys.stderr)
    for p in problems:
        print("  " + p, file=sys.stderr)
    sys.exit(1)
print(f"  pages check: {len(pkgs)} packages, {len(fns)} functions, nothing out of step")
