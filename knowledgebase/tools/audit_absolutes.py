#!/usr/bin/env python3
"""The absolute-claim audit (check 7.7).

Lists every sentence in the knowledgebase containing "never", "always", "cannot", "only
ever", "silently" and similar words. These are the most falsifiable statements and the most
consequential if wrong. On the original build every absolute checked in the reference
library was correct, and two were contradicted by the summaries; so audit the tier-1 guides
against the reference documents, and both against the source.

Usage: audit_absolutes.py [--guides-only | --reference-only] [--summary]
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kbconfig  # noqa: E402

cfg = kbconfig.load()
words = cfg["absolutes"]["words"]
RX = re.compile(r"\b(" + "|".join(re.escape(w) for w in words) + r")\b", re.I)
argv = sys.argv[1:]
docs = []
if "--reference-only" not in argv:
    docs += kbconfig.guide_docs(cfg)
if "--guides-only" not in argv:
    docs += kbconfig.reference_docs(cfg)
summary_only = "--summary" in argv

total = 0
for d in docs:
    rel = os.path.relpath(d, cfg["KB"])
    hits = []
    for ln, line in enumerate(open(d, encoding="utf-8", errors="replace"), 1):
        if set(line.strip()) <= set("|-: "):
            continue
        if RX.search(line):
            hits.append((ln, line.strip()))
    total += len(hits)
    if not hits:
        continue
    print("%s  (%d)" % (rel, len(hits)))
    if not summary_only:
        for ln, text in hits:
            print("   L%-5d %s" % (ln, text[:150]))
        print()
print("absolute claims to verify: %d" % total)
