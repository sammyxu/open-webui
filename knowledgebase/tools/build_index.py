#!/usr/bin/env python3
"""Regenerate <kb>/ai/*.json: machine-readable indexes of the whole knowledgebase (Phase 5).

Intended for AI agents and search tooling. Emits every document with its headings and
anchors, every tier-1 symptom documented in the reference library (the headings of the
troubleshooting section), every verbatim message table row with its source file, the
glossary, and the module catalogue. The JSON is derived, never the source of truth: run this
after editing any document, and never edit the JSON by hand.

Usage: build_index.py [--out DIR]      default: <kb>/ai
"""
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kbconfig  # noqa: E402

cfg = kbconfig.load()
KB, REF = cfg["KB"], cfg["REF"]
IX = cfg["index"]
AI = cfg["AI"]
if "--out" in sys.argv:
    AI = sys.argv[sys.argv.index("--out") + 1]
slug = kbconfig.slug
SYM = int(IX["symptoms_section"])
SRC_RE = re.compile(r"\.[A-Za-z0-9]{1,6}:\d+")

idx = {"generated": datetime.date.today().isoformat(), "root": os.path.basename(KB) + "/",
       "documents": [], "symptoms": [], "messages": [], "terms": [], "modules": []}

for f in kbconfig.guide_docs(cfg) + kbconfig.reference_docs(cfg, include_notes=True):
    rel = os.path.relpath(f, KB)
    txt = kbconfig.read(f)
    lines = txt.split("\n")
    title = next((l[2:].strip() for l in lines if l.startswith("# ")), rel)
    purpose = next((l.strip() for l in lines[1:12]
                    if l.strip() and not l.startswith(("#", "**", "|", "-", "<", "`", ">"))), "")
    heads = [{"level": len(m.group(1)), "text": re.sub(r"[`*]", "", m.group(2)).strip(),
              "anchor": slug(m.group(2)), "line": ln}
             for ln, l in enumerate(lines, 1) for m in [re.match(r"^(#{2,3})\s+(.+)$", l)] if m]
    idx["documents"].append({"path": rel, "title": title, "purpose": purpose[:240], "lines": len(lines),
                             "kind": "reference" if f.startswith(REF) else "guide", "headings": heads})
    if f.startswith(REF):
        m = re.search(r"\n## %d\.(.*?)(?=\n## %d\.|\Z)" % (SYM, SYM + 1), txt, re.S)
        if m:
            for h in re.findall(r"\n#{3,4}\s*(?:%d\.\d+(?:\.\d+)?\s*)?(.{10,120})" % SYM, m.group(1)):
                idx["symptoms"].append({"symptom": re.sub(r'[`*"]', "", h).strip(), "doc": rel, "section": str(SYM)})
    for l in lines:
        if not l.startswith("| `"):
            continue
        cells = [c.strip() for c in l.strip("|").split("|")]
        if len(cells) < 2:
            continue
        msg = cells[0].strip("`").strip()
        src = next((c for c in cells if SRC_RE.search(c)), "")
        if 12 < len(msg) < 300 and " " in msg and re.match(r'^[A-Z"<%]', msg):
            idx["messages"].append({"message": msg, "doc": rel, "source": re.sub(r"[`*]", "", src)[:120]})

seen = set()
for g in IX["glossary_docs"]:
    src = os.path.join(KB, g)
    if not os.path.exists(src):
        continue
    for l in kbconfig.read(src).split("\n"):
        if not l.startswith("| "):
            continue
        cells = [re.sub(r"[`*]", "", c).strip() for c in l.strip("|").split("|")]
        if len(cells) < 2 or not (2 <= len(cells[0]) <= 60):
            continue
        if cells[0].lower() in ("term", "acronym", "label") or set(cells[0]) <= set("-: "):
            continue
        if cells[0].lower() in seen:
            continue
        seen.add(cells[0].lower())
        idx["terms"].append({"term": cells[0], "definition": cells[1][:300], "doc": os.path.relpath(src, KB)})

mt = IX["module_table"]
if mt.get("doc") and os.path.exists(os.path.join(KB, mt["doc"])):
    o = kbconfig.read(os.path.join(KB, mt["doc"]))
    for m in re.finditer(mt["regex"], o, re.M):
        cells = [c.strip() for c in m.group(3).strip("|").split("|")] if m.lastindex and m.lastindex >= 3 else [""]
        idx["modules"].append({"module": m.group(1), "url": m.group(2) if m.lastindex >= 2 else "",
                               "purpose": re.sub(r"[`*]", "", cells[-1])[:160]})

s = set()
uniq = []
for x in idx["messages"]:
    if x["message"][:80] in s:
        continue
    s.add(x["message"][:80])
    uniq.append(x)
idx["messages"] = uniq
os.makedirs(AI, exist_ok=True)
json.dump(idx, open(os.path.join(AI, "index.json"), "w"), indent=1, ensure_ascii=False)
for key in ("documents", "symptoms", "messages", "terms", "modules"):
    json.dump({"generated": idx["generated"], key: idx[key]},
              open(os.path.join(AI, "%s.json" % key), "w"), indent=1, ensure_ascii=False)
print("%s/index.json + split files:" % os.path.relpath(AI, KB),
      {k: len(v) for k, v in idx.items() if isinstance(v, list)})
