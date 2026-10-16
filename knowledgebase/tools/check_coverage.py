#!/usr/bin/env python3
"""Completeness check: does each reference document cover its enumerable scope? (check 7.4)

For every scope in kb.config.json that names owning documents, enumerate what exists in the
repository and report anything those documents never mention. A miss is not automatically a
defect (some items are deliberately covered elsewhere), but an unmentioned item is a gap
worth a human look. On the original build this found 70 undocumented tables, including an
entire learner-facing feature whose logic lived in a vendored first-party package.

Scope options (see kb.config.example.json): "docs" names the owning documents;
"require_heading": true also insists each item has its own heading, not just a mention;
"type": "tables" enumerates CREATE TABLE names from the "globs" instead of a directory.

Exit status 1 when any item is unmentioned.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kbconfig  # noqa: E402

cfg = kbconfig.load()
REF = cfg["REF"]


def text_of(docs):
    t = ""
    for d in docs:
        p = os.path.join(REF, d)
        if os.path.exists(p):
            t += kbconfig.read(p)
    return t


total_missing = total_no_heading = 0
for scope in cfg["scopes"]:
    docs = scope.get("docs")
    if not docs:
        continue
    items = kbconfig.list_scope(cfg, scope)
    if not items:
        print("%-46s %-30s no items found (check dir/pattern)" % (docs[0], scope["label"]))
        continue
    body = text_of(docs)
    if not body:
        print("%-46s DOCUMENT NOT FOUND" % ", ".join(docs))
        continue
    missing = [i for i in items if i not in body]
    total_missing += len(missing)
    status = "complete" if not missing else "%d not mentioned" % len(missing)
    no_heading = []
    if scope.get("require_heading"):
        no_heading = [i for i in items if i not in missing
                      and not re.search(r"^#{2,5}[^\n]*\b%s\b" % re.escape(i), body, re.M)]
        total_no_heading += len(no_heading)
        if no_heading:
            status += ", %d without own heading" % len(no_heading)
    print("%-46s %-30s %4d items  -> %s" % (docs[0], scope["label"], len(items), status))
    for m in missing:
        print("        missing: %s" % m)
    for m in no_heading:
        print("        no heading: %s" % m)

print("\ntotal unmentioned items: %d   items without own heading: %d" % (total_missing, total_no_heading))
sys.exit(1 if (total_missing or total_no_heading) else 0)
