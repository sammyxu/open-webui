#!/usr/bin/env python3
"""Per-document statistics for the reference library (local helper for harvesting research notes).

For each reference document prints its line count, the number of section-10 message rows (table
rows starting with a backticked message), the number of section-11 symptom headings and the
number of section-14 items (numbered or bulleted). Used when copying each document's status and
gaps into reference/_research-notes.md.

Usage: doc_stats.py [doc.md ...]      default: every reference document
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kbconfig  # noqa: E402

cfg = kbconfig.load()


def section(txt, n):
    m = re.search(r"\n## %d\.(.*?)(?=\n## %d\.|\Z)" % (n, n + 1), txt, re.S)
    return m.group(1) if m else ""


totals = [0, 0, 0, 0]
docs = sys.argv[1:] or kbconfig.reference_docs(cfg)
for p in docs:
    t = kbconfig.read(p)
    rows = [l for l in section(t, 10).splitlines() if l.startswith("| `")]
    syms = re.findall(r"^###\s+11\.\d+", section(t, 11), re.M)
    items = re.findall(r"^\s{0,3}(?:\d+\.|[-*])\s", section(t, 14), re.M)
    lines = t.count("\n") + 1
    for i, v in enumerate((lines, len(rows), len(syms), len(items))):
        totals[i] += v
    print("%-58s lines %5d  messages %4d  symptoms %3d  open-questions %3d" % (
        os.path.basename(p), lines, len(rows), len(syms), len(items)))
if len(docs) > 1:
    print("%-58s lines %5d  messages %4d  symptoms %3d  open-questions %3d" % ("TOTAL", *totals))
