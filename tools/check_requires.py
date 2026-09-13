#!/usr/bin/env python3
"""Prüft jede requires-Deklaration gegen die echten composer.json der
veröffentlichten Pakete. Bricht ab, wenn eine Seite ein Paket nennt, das es
nicht gibt — der Fehler, den die handgeschriebenen Requirements-Abschnitte
hatten, kann damit nicht zurückkommen."""
import glob, json, os, sys

HERE = os.path.dirname(__file__)
known = set(json.load(open(os.path.join(HERE, "packages.json"), encoding="utf-8"))["packages"])
problems = []

for path in sorted(glob.glob(os.path.join(HERE, "..", "pages", "*.md"))):
    text = open(path, encoding="utf-8").read()
    if not text.startswith("---"):
        continue
    fm = text.split("---", 2)[1]
    inside, req = False, []
    for line in fm.split("\n"):
        if line.strip() == "requires:":
            inside = True; continue
        if inside:
            if line.startswith("  - "):
                req.append(line[4:].strip())
            elif line.strip():
                inside = False
    for r in req:
        if not r.startswith("naf/") or r.split("/", 1)[1] not in known:
            problems.append(f"{os.path.basename(path)}: '{r}' gibt es nicht")

if problems:
    print("requires-Deklarationen stimmen nicht:", file=sys.stderr)
    for p in problems:
        print("  " + p, file=sys.stderr)
    sys.exit(1)
print(f"  requires-Deklarationen geprüft, {len(known)} bekannte Pakete, keine Abweichung")
