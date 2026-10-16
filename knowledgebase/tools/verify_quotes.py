#!/usr/bin/env python3
"""Check that quoted user-facing messages in the knowledgebase exist in the source (check 7.3).

Every reference document quotes messages "verbatim". This confirms that claim: it pulls each
backticked quote that looks like a message, breaks it into literal prose fragments at the
points where the source would interpolate a value, and searches the normalised source for
them. Anything never found is reported for human review.

Not every flag is an error. Legitimate causes: a quote deliberately abbreviated with an
ellipsis, a placeholder such as <username> standing in for an interpolated variable, or an
accurate summary of a longer string. Read each flag against the source before editing.

The seven lessons that made this check trustworthy are built in:
  1. code spans are taken by splitting on backticks and keeping odd indices;
  2. fragments split at HTML tags, printf placeholders and the documentation's placeholder
     notation (configurable);
  3. long fragments also try word-aligned head and tail chunks;
  4. quotes and backticks are normalised on both sides and \" is unescaped;
  5. entity-escaped and unescaped forms are both tried;
  6. first-party code under vendor/ is included via source.extra_first_party_dirs;
  7. matching is a plain substring test in Python, never grep -F with thousands of patterns.

Usage: verify_quotes.py [--baseline OUT.txt] [--diff BASELINE.txt] [doc.md ...]
  --baseline   also write this run's output (minus the environment-specific corpus line) to OUT.txt
  --diff       compare this run with a saved baseline and exit 1 if they differ
  KB_CORPUS=/path/to/corpus.txt   reuse a normalised corpus between runs (rebuilt if empty)
"""
import collections
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kbconfig  # noqa: E402

cfg = kbconfig.load()
ROOT, KB = cfg["ROOT"], cfg["KB"]
S, Q = cfg["source"], cfg["quotes"]
if not S["dirs"]:
    sys.exit("source.dirs is empty in kb.config.json; list the repository directories that hold "
             "first-party source")
SRC = list(S["dirs"]) + list(S["extra_first_party_dirs"])
SKIP = set(S["skip_dirs"])
EXT = tuple(S["extensions"])
PATHISH = re.compile("^(" + "|".join(re.escape(p) for p in Q["path_like_prefixes"]) + ")")
PLACEHOLDERS = [re.compile(p) for p in Q["placeholder_patterns"]]
STARTS = re.compile(Q["starts_with"])
FRAG_MIN, CHUNK, LONG = Q["fragment_min_len"], Q["chunk_len"], Q["long_fragment_len"]

OUT = []


def emit(line=""):
    print(line)
    OUT.append(line)


def norm(t):
    for ch in "`‘’“”":
        t = t.replace(ch, "'")
    return t.replace('"', "'").replace("\\'", "'")


def backticked(line):
    parts = line.split("`")
    return [parts[i] for i in range(1, len(parts), 2)] if len(parts) >= 3 else []


def fragments(msg, keep_entities=False):
    m = msg if keep_entities else (msg.replace("&quot;", '"').replace("&amp;", "&")
                                   .replace("&lt;", "<").replace("&gt;", ">"))
    m = norm(m.replace("\\|", "|"))  # Markdown table cells escape pipes as \|
    for pat in PLACEHOLDERS:
        m = pat.sub("\x01", m)
    runs = []
    for seg in m.split("\x01"):
        seg = re.sub(r"\s+", " ", seg).strip(" .,:;!?-")
        if len(seg) >= FRAG_MIN and re.search(r"[A-Za-z]{3}", seg):
            runs.append(seg)
    # A message may interpolate something the placeholder notation cannot see, e.g. a
    # translated term mid-sentence, so for long runs also try word-aligned head and tail
    # chunks: if either end survives verbatim in the source, that is confirmation enough.
    extra = []
    for r in runs:
        if len(r) < LONG:
            continue
        words = r.split(" ")
        head, tail = [], []
        for w in words:
            if len(" ".join(head + [w])) > CHUNK:
                break
            head.append(w)
        for w in reversed(words):
            if len(" ".join([w] + tail)) > CHUNK:
                break
            tail.insert(0, w)
        for chunk in (" ".join(head), " ".join(tail)):
            chunk = chunk.strip(" .,:;!?-")
            if len(chunk) >= FRAG_MIN and chunk != r:
                extra.append(chunk)
    runs.sort(key=len, reverse=True)
    return (runs + extra)[:6]


def build_corpus(path):
    """Normalise all first-party source into one file so the matcher sees the same shape as the quotes."""
    n = 0
    with open(path, "w", encoding="utf-8") as out:
        for base in SRC:
            for dp, dns, fns in os.walk(os.path.join(ROOT, base)):
                dns[:] = [d for d in dns if d not in SKIP]
                for fn in fns:
                    if not fn.endswith(EXT):
                        continue
                    try:
                        out.write(norm(kbconfig.read(os.path.join(dp, fn))))
                        out.write("\n")
                        n += 1
                    except Exception:
                        pass
    # Local extension: repository-root files (Dockerfile, compose files, Makefile, root scripts)
    # hold operator-facing messages but sit outside any source directory.
    for rel in S.get("extra_files", []):
        full = os.path.join(ROOT, rel)
        if os.path.isfile(full):
            with open(path, "a", encoding="utf-8") as out:
                out.write(norm(kbconfig.read(full)))
                out.write("\n")
            n += 1
    return n


def collect(targets):
    claims = []
    for md in sorted(targets):
        rel = os.path.relpath(md, ROOT)
        for ln, line in enumerate(open(md, encoding="utf-8", errors="replace"), 1):
            for q in backticked(line):
                q = q.strip()
                if not (Q["min_len"] <= len(q) <= Q["max_len"]):
                    continue
                if PATHISH.match(q) or q.count(" ") < Q["min_spaces"]:
                    continue
                if not STARTS.match(q):
                    continue
                frs = fragments(q) + (fragments(q, True) if "&" in q else [])
                if frs:
                    claims.append((rel, ln, q, frs))
    return claims


def take_opt(argv, name):
    if name in argv:
        i = argv.index(name)
        return argv[i + 1], argv[:i] + argv[i + 2:]
    return None, argv


def main(argv):
    baseline, argv = take_opt(argv, "--baseline")
    diff_against, argv = take_opt(argv, "--diff")
    targets = argv or kbconfig.md_files(KB)
    claims = collect(targets)
    pats = sorted({f for *_, frs in claims for f in frs})
    emit("claims: %d   distinct fragments: %d" % (len(claims), len(pats)))
    corpus = os.environ.get("KB_CORPUS") or tempfile.NamedTemporaryFile(suffix=".corpus", delete=False).name
    if not os.path.exists(corpus) or os.path.getsize(corpus) == 0:
        nfiles = build_corpus(corpus)
        emit("corpus: %d files, %.1f MB" % (nfiles, os.path.getsize(corpus) / 1e6))
    else:
        emit("corpus: reusing %s (%.1f MB)" % (corpus, os.path.getsize(corpus) / 1e6))
    # Plain substring tests: predictable linear cost. BSD grep -F with thousands of patterns
    # went quadratic and ran for seven and a half hours on the original build.
    text = kbconfig.read(corpus)
    found = {p for p in pats if p in text}
    if not os.environ.get("KB_CORPUS"):
        os.unlink(corpus)

    missing = [c for c in claims if not any(x in found for x in c[3])]
    emit("fragments matched: %d / %d" % (len(found), len(pats)))
    emit("quoted messages NOT found in source: %d" % len(missing))
    emit()
    by = collections.defaultdict(list)
    for rel, ln, q, _ in missing:
        by[rel].append((ln, q))
    for rel in sorted(by, key=lambda r: -len(by[r])):
        emit("%s  (%d)" % (rel, len(by[rel])))
        for ln, q in by[rel]:
            emit("   L%-5d %s" % (ln, q.replace("\n", " ")[:118]))
        emit()
    stable = [l for l in OUT if not l.startswith("corpus:")]
    if baseline:
        with open(baseline, "w", encoding="utf-8") as fh:
            fh.write("\n".join(stable) + "\n")
        print("baseline written: %s" % baseline)
    if diff_against:
        import difflib
        want = [l for l in kbconfig.read(diff_against).splitlines() if not l.startswith("corpus:")]
        d = list(difflib.unified_diff(want, stable, "baseline", "this run", lineterm=""))
        if d:
            print("\n".join(d[:200]))
            print("DIFFERS from baseline %s (%d diff lines); review each before updating the baseline" % (diff_against, len(d)))
            sys.exit(1)
        print("matches baseline: %s" % diff_against)


if __name__ == "__main__":
    main(sys.argv[1:])
