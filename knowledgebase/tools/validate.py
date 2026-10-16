#!/usr/bin/env python3
"""Validate repository path and file:line citations across the knowledgebase (check 7.1).

Extracts every repository-relative path, optionally with :line, from every markdown document,
confirms the file exists under the repository root, and confirms any cited line number is
within the file.

Some flagged paths are correct: a document may deliberately cite a file to record that it is
missing. Review each flag against the document; never bulk-fix. A blanket find-and-replace
once destroyed a genuine finding.

What this does not check: that a cited line still says what the document claims. Line
numbers drift on every release, so a citation can resolve and still be wrong.

Usage: validate.py [doc.md ...]      default: every .md under the knowledgebase
Exit status is 1 only when a line number is past the end of its file.
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kbconfig  # noqa: E402

cfg = kbconfig.load()
ROOT, KB = cfg["ROOT"], cfg["KB"]
cit = cfg["citations"]
if not cit["path_prefixes"]:
    sys.exit("citations.path_prefixes is empty in kb.config.json; list the top-level repository "
             "directories that documents cite (for example \"src\", \"app\", \"www-root\")")
prefixes = "|".join(re.escape(p) for p in cit["path_prefixes"])
exts = "|".join(re.escape(e) for e in cit["extensions"])
# SvelteKit route paths contain ( ) [ ] + (src/routes/(app)/c/[id]/+page.svelte), so the path
# character class allows them; matching is lazy up to the first known extension.
PATH_RE = re.compile(r"(?<![\w/.-])((?:%s)/[A-Za-z0-9_./()\[\]+@-]+?\.(?:%s))(?::(\d+))?(?![\w/.-])"
                     % (prefixes, exts))
# Repository-root files (Dockerfile, package.json, ...) have no directory prefix to key on;
# kb.config.json lists them under citations.root_files so their citations are checked too.
ROOT_FILES = cit.get("root_files", [])
ROOT_RE = re.compile(r"(?<![\w/.-])(%s)(?::(\d+))?(?![\w/.-])" % "|".join(re.escape(f) for f in ROOT_FILES)) \
    if ROOT_FILES else None


def line_count(p, cache={}):
    if p not in cache:
        try:
            with open(p, "rb") as f:
                cache[p] = sum(1 for _ in f)
        except Exception:
            cache[p] = None
    return cache[p]


missing_file = collections.defaultdict(list)
bad_line = collections.defaultdict(list)
ok = 0
targets = sys.argv[1:] or kbconfig.md_files(KB)
for md in sorted(targets):
    rel = os.path.relpath(md, ROOT)
    with open(md, encoding="utf-8", errors="replace") as fh:
        for ln, text in enumerate(fh, 1):
            matches = list(PATH_RE.finditer(text)) + (list(ROOT_RE.finditer(text)) if ROOT_RE else [])
            for m in matches:
                path, lineno = m.group(1), m.group(2)
                full = os.path.join(ROOT, path)
                if not os.path.exists(full):
                    missing_file[rel].append((ln, path))
                    continue
                if lineno:
                    n = line_count(full)
                    if n is not None and int(lineno) > n:
                        bad_line[rel].append((ln, path, int(lineno), n))
                        continue
                ok += 1

print("citations resolved OK: %d" % ok)
print()
if missing_file:
    print("=== PATHS THAT DO NOT EXIST (%d docs) ===" % len(missing_file))
    for d, items in sorted(missing_file.items()):
        uniq = sorted(set(p for _, p in items))
        print("  %s  (%d refs, %d distinct)" % (d, len(items), len(uniq)))
        for p in uniq[:12]:
            print("      %s" % p)
        if len(uniq) > 12:
            print("      ... and %d more" % (len(uniq) - 12))
else:
    print("=== no missing paths ===")
print()
if bad_line:
    print("=== LINE NUMBERS PAST END OF FILE (%d docs) ===" % len(bad_line))
    for d, items in sorted(bad_line.items()):
        print("  %s  (%d)" % (d, len(items)))
        for ln, p, cited, n in items[:12]:
            print("      doc line %d: %s:%d but file has %d lines" % (ln, p, cited, n))
        if len(items) > 12:
            print("      ... and %d more" % (len(items) - 12))
else:
    print("=== no out-of-range line numbers ===")
sys.exit(1 if bad_line else 0)
