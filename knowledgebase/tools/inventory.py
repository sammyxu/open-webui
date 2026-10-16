#!/usr/bin/env python3
"""Generate tools/inventory.md: the complete enumeration of everything countable (Phase 1).

Generated, not hand-written, so it can be regenerated after every release and so that every
count in the knowledgebase comes from a script. Every hand-typed count checked on the
original build was wrong three times out of the ones checked. Files are counted, not
directory entries, unless a scope says otherwise.

Scopes and counts come from kb.config.json ("scopes" and "counts"). Extend this script for
enumerations that need application knowledge, such as sub-pages per module or tables per
schema; keep the output shape so the coverage checker and the guides can rely on it.

Usage: inventory.py [--out PATH]      default: <kb>/tools/<inventory_file> (kb.config.json, "inventory.md")

Set "inventory_file" to another name when an existing inventory.md holds hand-built enumerations
(sub-pages per module, tables per schema) that this generic generator would not reproduce.
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kbconfig  # noqa: E402

cfg = kbconfig.load()
out_path = os.path.join(cfg["TOOLS"], cfg["inventory_file"])
if "--out" in sys.argv:
    out_path = sys.argv[sys.argv.index("--out") + 1]

lines = ["# Repository Inventory (generated %s from %s)" % (
    datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), cfg["ROOT"]), "",
    "Enumerated from the working tree. This is the authoritative list of what exists. Verify an",
    "individual path with `ls` before citing it in a document. Regenerate with",
    "`python3 tools/inventory.py` after every release.", ""]
summary = []
for scope in cfg["scopes"]:
    items = kbconfig.list_scope(cfg, scope)
    where = scope.get("dir") or ", ".join(scope.get("globs", []))
    unit = scope.get("unit", "items")
    lines.append("## %s (%s) — %d %s" % (scope["label"], where, len(items), unit))
    if scope.get("note"):
        lines.append("")
        lines.append(scope["note"])
    lines.append("")
    if not items:
        lines.append("(none found)")
    elif len(items) <= 40:
        lines.extend("- `%s`" % i for i in items)
    else:
        lines.append(", ".join("`%s`" % i for i in items))
    lines.append("")
    summary.append((scope["label"], len(items)))

if cfg["counts"]:
    lines.append("## Scale")
    lines.append("")
    lines.append("| What | Count |")
    lines.append("|---|---|")
    for c in cfg["counts"]:
        n = len(kbconfig.list_scope(cfg, c))
        lines.append("| %s | %d |" % (c["label"], n))
        summary.append((c["label"], n))
    lines.append("")

os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))
print("wrote %s" % out_path)
for label, n in summary:
    print("  %-44s %5d" % (label, n))
