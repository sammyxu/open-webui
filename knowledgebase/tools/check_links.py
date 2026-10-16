#!/usr/bin/env python3
"""Check every markdown link in the knowledgebase, including #section anchors (check 7.2).

Reports links whose target file does not exist and links whose anchor does not match any
heading in the target. Anchors are computed the way GitHub-flavoured markdown does, which is
the rule most renderers follow. Non-markdown targets (JSON, scripts) count as valid when the
file exists.

Exit status 1 when anything is broken.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kbconfig  # noqa: E402

cfg = kbconfig.load()
KB = cfg["KB"]
slug = kbconfig.slug

anchors = {}
for p in kbconfig.md_files(KB):
    a = set()
    for l in open(p, errors="replace"):
        m = re.match(r"^#{1,6}\s+(.+)$", l)
        if m:
            a.add(slug(m.group(1)))
    anchors[os.path.relpath(p, KB)] = a

bad_file = bad_anchor = ok = 0
for p in kbconfig.md_files(KB):
    rel = os.path.relpath(p, KB)
    for i, l in enumerate(open(p, errors="replace"), 1):
        for m in re.finditer(r"\[[^\]]*\]\(([^)]+)\)", l):
            t = m.group(1).strip()
            if t.startswith(("http://", "https://", "mailto:")):
                continue
            path, _, anc = t.partition("#")
            target = rel if not path else os.path.normpath(os.path.join(os.path.dirname(rel), path))
            if target not in anchors:
                if os.path.exists(os.path.join(KB, target)):
                    ok += 1
                    continue
                bad_file += 1
                print("  BROKEN FILE   %s:%d -> %s" % (rel, i, t))
                continue
            if anc and anc not in anchors[target]:
                bad_anchor += 1
                print("  BROKEN ANCHOR %s:%d -> %s" % (rel, i, t))
            else:
                ok += 1
print("links ok: %d   broken files: %d   broken anchors: %d" % (ok, bad_file, bad_anchor))
sys.exit(1 if (bad_file or bad_anchor) else 0)
