#!/usr/bin/env python3
"""PII grep over the knowledgebase, including generated JSON (Definition of Done).

Reports every email address, @author attribution that names a person, phone number and configured extra pattern
in every .md, .json and .txt file under the knowledgebase. Functional mailboxes that are part
of the product are configuration, not PII: list them in pii.allowed_emails. Other known
institutional values (a switchboard number quoted from the code) go in pii.allowed_values. Example domains
(example.com, .invalid, .test, ...) and 555-exchange phone numbers are ignored so fictional
examples pass.

Run after any database-driven update and before every hand-over. Exit status 1 on any hit.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kbconfig  # noqa: E402

cfg = kbconfig.load()
P = cfg["pii"]
allowed_emails = {e.lower() for e in P["allowed_emails"]}
allowed_domains = [d.lower() for d in P["allowed_domains"]]
allowed_values = [v.lower() for v in P.get("allowed_values", [])]
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?<![\w.])(?:\+?\d{1,2}[ .-])?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?![\w.])")
# An @author is flagged only when a Firstname Lastname phrase follows it (optionally after a
# "Developer:" label) and that phrase is not an organisation; "@author Organisation: X" and
# prose about the tag pass.
AUTHOR = re.compile(r"@author\b[^A-Za-z\n]*(?:[A-Za-z]+:\s*)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)")
ORG_WORDS = {w.lower() for w in P["organisation_words"]}
EXTRA = [re.compile(p) for p in P["extra_patterns"]]


def domain_allowed(addr):
    dom = addr.split("@", 1)[1].lower()
    return any(dom == d or dom.endswith("." + d) for d in allowed_domains)


files = []
for dp, dns, fns in os.walk(cfg["KB"]):
    dns[:] = [d for d in dns if not d.startswith(".")]
    files.extend(os.path.join(dp, f) for f in fns if f.endswith((".md", ".json", ".txt")))

hits = 0
for f in sorted(files):
    rel = os.path.relpath(f, cfg["KB"])
    for ln, line in enumerate(open(f, encoding="utf-8", errors="replace"), 1):
        found = []
        for e in EMAIL.findall(line):
            if e.lower() in allowed_emails or domain_allowed(e):
                continue
            found.append("email " + e)
        for m in AUTHOR.finditer(line):
            if not any(w.lower() in ORG_WORDS for w in m.group(1).split()):
                found.append("@author " + m.group(1))
        for ph in PHONE.findall(line):
            if any(v in ph.lower() for v in allowed_values):
                continue
            if re.search(r"555[ .-]?\d{4}$", ph.strip()):   # North American fictional exchange
                continue
            found.append("phone-like " + ph.strip())
        for rx in EXTRA:
            for m in rx.findall(line):
                found.append("pattern " + (m if isinstance(m, str) else str(m)))
        found = [w for w in found if not any(v in w.lower() for v in allowed_values)]
        for what in found:
            hits += 1
            print("%s:%d  %s   | %s" % (rel, ln, what, line.strip()[:110]))
print("\nPII-like hits: %d" % hits)
sys.exit(1 if hits else 0)
