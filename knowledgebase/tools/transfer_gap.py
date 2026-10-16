#!/usr/bin/env python3
"""The knowledge-transfer gap check (check 7.8).

Extracts every symptom heading from the troubleshooting section of every reference document
and asks whether the tier-1 guides give it any route: a link to its anchor, or enough of its
keywords appearing in a guide. Symptoms with no route are listed. On the original build 639
symptoms were documented and 23 were unreachable from the tier-1 layer, including two of the
most common tickets. The references were right; the knowledge just never reached the layer
where the ticket lands. Carry the high-value ones into the guides in full and give the rest a
pointer table.

Usage: transfer_gap.py [--ratio 0.6]
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kbconfig  # noqa: E402

cfg = kbconfig.load()
SYM = int(cfg["index"]["symptoms_section"])
ratio = float(cfg["transfer_gap"]["min_keyword_ratio"])
min_kw = int(cfg["transfer_gap"]["min_keywords"])
if "--ratio" in sys.argv:
    ratio = float(sys.argv[sys.argv.index("--ratio") + 1])

STOP = set("""the a an and or of to in on for with is are was were be been being it its this that these
those not no from by as at but if then than when what which who whom whose why how does do did have
has had can could would should will shall may might must user users someone something cannot does
into onto over under after before while still just also very more most some any all each every one
two three there their they them your you our we".""".split())


def keywords(s):
    return sorted({w for w in re.findall(r"[a-z][a-z0-9']{3,}", s.lower()) if w not in STOP})


guides = "\n".join(kbconfig.read(g) for g in kbconfig.guide_docs(cfg)).lower()
total = unreachable = 0
for d in kbconfig.reference_docs(cfg):
    txt = kbconfig.read(d)
    m = re.search(r"\n## %d\.(.*?)(?=\n## %d\.|\Z)" % (SYM, SYM + 1), txt, re.S)
    if not m:
        continue
    rel = os.path.relpath(d, cfg["KB"])
    misses = []
    for h in re.findall(r"^#{3,4}\s*(?:%d\.\d+(?:\.\d+)?\s*)?(.{6,160})$" % SYM, m.group(1), re.M):
        sym = re.sub(r'[`*"“”]', "", h).strip()
        total += 1
        if kbconfig.slug(h) in guides:
            continue
        kws = keywords(sym)
        if len(kws) < min_kw:
            continue
        hit = sum(1 for k in kws if k in guides)
        if hit / len(kws) < ratio:
            misses.append((sym, hit, len(kws)))
    if misses:
        unreachable += len(misses)
        print("%s  (%d unreachable)" % (rel, len(misses)))
        for sym, hit, n in misses:
            print("   %s   [%d/%d keywords]" % (sym[:120], hit, n))
        print()
print("symptoms: %d   unreachable from the tier-1 guides: %d   (keyword ratio %.2f)" % (total, unreachable, ratio))
