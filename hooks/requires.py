"""Renders a page's requires declaration as a box, and names what comes along
transitively. The statement lives in the page's structure rather than in its
prose, where the next rewrite would forget it."""
import json, os

DATA = os.path.join(os.path.dirname(__file__), "..", "tools", "packages.json")
_meta = None

def _packages():
    global _meta
    if _meta is None:
        try:
            _meta = json.load(open(DATA, encoding="utf-8"))["packages"]
        except (OSError, ValueError):
            _meta = {}
    return _meta

def _transitive(pkg, seen):
    meta = _packages()
    for dep in meta.get(pkg, {}).get("requires", []):
        name = dep.split("/", 1)[1]
        if name in seen or name == "framework":
            continue
        seen.add(name)
        _transitive(name, seen)
    return seen

def on_page_markdown(markdown, page, config, files):
    req = page.meta.get("requires") or []
    if not req:
        return markdown

    lines = ['!!! info "Required packages"', "",
             '    In an existing NAF application:', "",
             "    ```bash", "    composer require " + " ".join(req), "    ```", ""]

    extra = set()
    for r in req:
        extra |= _transitive(r.split("/", 1)[1], set())
    extra -= {r.split("/", 1)[1] for r in req}
    if extra:
        names = ", ".join(f"`naf/{e}`" for e in sorted(extra))
        lines.append(f"    Also installs these transitive dependencies: {names}.")
        lines.append("")

    position = markdown.find("\n## ")
    if position == -1:
        position = len(markdown)
    return markdown[:position] + "\n" + "\n".join(lines) + markdown[position:]
