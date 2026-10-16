#!/usr/bin/env python3
"""Confirm every reference document has all of its numbered sections, in order (Phase 2, step 5.4).

A file existing is not evidence it is complete. Four documents in the original build were
truncated mid-write and assumed complete for days. Run this after every batch of research
and after every repair. The heading number is what matters ("## 7. ..."), not its wording.

Reports, per document: OK, MISSING sections, OUT OF ORDER numbering, and a THIN last section
(fewer than three non-empty lines after the final heading, the usual sign of a truncated
write). Exit status 1 when any section is missing.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kbconfig  # noqa: E402

cfg = kbconfig.load()
N = int(cfg["reference_sections"])
docs = sys.argv[1:] or kbconfig.reference_docs(cfg)
problems = 0
for d in docs:
    txt = kbconfig.read(d)
    nums = [int(n) for n in re.findall(r"^## (\d+)\.", txt, re.M)]
    found = sorted(set(nums))
    missing = [i for i in range(1, N + 1) if i not in found]
    flags = []
    if missing:
        flags.append("MISSING " + ",".join(map(str, missing)))
    if nums != sorted(nums):
        flags.append("OUT OF ORDER")
    if found:
        tail = txt.split("\n## %d." % found[-1], 1)[-1]
        if len([l for l in tail.strip().split("\n") if l.strip()]) < 3:
            flags.append("THIN LAST SECTION")
    # Case-insensitive: the template's own heading is "## At a Glance" (Title Case with a
    # lower-case article), which the original two literal spellings did not match.
    if not re.search(r"^## At a Glance\s*$", txt, re.M | re.I):
        flags.append("no 'At a glance'")
    if missing:
        problems += 1
    print("%-58s %2d/%d  %s" % (os.path.basename(d), len(found), N, "; ".join(flags) or "OK"))
print("\n%d documents, %d incomplete" % (len(docs), problems))
sys.exit(1 if problems else 0)
