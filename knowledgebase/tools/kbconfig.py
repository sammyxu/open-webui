#!/usr/bin/env python3
"""Shared configuration loader for the knowledgebase tools.

Every tool reads one JSON file, kb.config.json, so nothing about the application (where the
source lives, which paths count as citations, which directories are enumerable scopes) is
hard-coded in a script. Adapting the toolkit to a new application means editing that one file.

Look-up order for the config file:
  1. $KB_CONFIG
  2. kb.config.json next to the running script
  3. ./kb.config.json, then ./tools/kb.config.json

Relative paths inside the file resolve against the directory that holds it, so the
conventional layout is <repo>/knowledgebase/tools/kb.config.json with
"repo_root": "../.." and "kb_dir": "..".
"""
import glob as _glob
import json
import os
import re
import sys

DEFAULTS = {
    "repo_root": "../..",
    "kb_dir": "..",
    "reference_dir": "reference",
    "ai_dir": "ai",
    "reference_sections": 14,
    "source": {
        "dirs": [],
        "extra_first_party_dirs": [],
        "skip_dirs": ["vendor", "node_modules", ".git", "dist", "build"],
        "extensions": [".php", ".js", ".ts", ".tsx", ".jsx", ".vue", ".py", ".rb", ".java", ".cs",
                       ".go", ".txt", ".xml", ".html", ".sh", ".tpl", ".twig", ".json", ".yml", ".yaml"],
    },
    "citations": {
        "path_prefixes": [],
        "extensions": ["php", "sql", "js", "ts", "py", "rb", "md", "txt", "xml", "yml", "yaml",
                       "ini", "conf", "sh", "css", "html", "json", "vue", "twig", "tpl"],
    },
    "quotes": {
        "min_len": 20, "max_len": 400, "min_spaces": 4,
        "starts_with": "^[A-Z\"'<(]",
        "path_like_prefixes": ["/", "$", "SELECT ", "UPDATE ", "INSERT ", "DELETE ", "php ",
                               "grep ", "cd ", "git ", "composer ", "mysql ", "npm ", "python"],
        "placeholder_patterns": ["<[^>]{1,60}>", "%\\d*\\$?[sd]", "«[^»]*»", "\\{[^}]*\\}",
                                 "\\[[^\\]]*\\]", "…", "\\.\\.\\."],
        "fragment_min_len": 28, "chunk_len": 42, "long_fragment_len": 46,
    },
    "scopes": [],
    "counts": [],
    "index": {
        "symptoms_section": 11,
        "glossary_docs": [],
        "module_table": {"doc": "", "regex": "^\\| `([A-Za-z0-9_-]+)` \\| `(/[^`]*)` \\|(.*)$"},
    },
    "absolutes": {"words": ["never", "always", "cannot", "can't", "only ever", "silently",
                            "impossible", "guaranteed", "every time", "no way"]},
    "transfer_gap": {"min_keyword_ratio": 0.6, "min_keywords": 2},
    "pii": {"allowed_emails": ["git@github.com"], "allowed_values": [], "allowed_domains": ["example.com", "example.org", "example.net",
            "example.edu", "example.ca", "localhost", "invalid", "test", "example"],
            "extra_patterns": [],
            "organisation_words": ["University", "Organisation", "Organization", "Department", "Institute",
                                   "College", "Faculty", "Consortium", "Commons", "Inc", "Ltd", "LLC", "Team",
                                   "Group", "School", "Hospital", "Centre", "Center", "Project", "Foundation"]},
    "inventory_file": "inventory.md",
}


def _merge(base, override):
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            out[k] = _merge(base[k], v)
        else:
            out[k] = v
    return out


def load():
    path = os.environ.get("KB_CONFIG")
    if not path:
        here = os.path.dirname(os.path.abspath(sys.argv[0]))
        for cand in (os.path.join(here, "kb.config.json"),
                     os.path.join(os.getcwd(), "kb.config.json"),
                     os.path.join(os.getcwd(), "tools", "kb.config.json")):
            if os.path.exists(cand):
                path = cand
                break
    if not path or not os.path.exists(path):
        sys.exit("kb.config.json not found. Copy kb.config.example.json next to the scripts, edit it "
                 "for this application, or set KB_CONFIG=/path/to/kb.config.json")
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    cfg = _merge(DEFAULTS, raw)
    base = os.path.dirname(os.path.abspath(path))

    def resolve(p):
        return os.path.normpath(p if os.path.isabs(p) else os.path.join(base, p))

    cfg["_path"] = path
    cfg["TOOLS"] = base
    cfg["ROOT"] = resolve(cfg["repo_root"])
    cfg["KB"] = resolve(cfg["kb_dir"])
    cfg["REF"] = os.path.join(cfg["KB"], cfg["reference_dir"])
    cfg["AI"] = os.path.join(cfg["KB"], cfg["ai_dir"])
    return cfg


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def md_files(kb):
    """Every markdown file under the knowledgebase, skipping dot-directories."""
    out = []
    for dp, dns, fns in os.walk(kb):
        dns[:] = [d for d in dns if not d.startswith(".")]
        out.extend(os.path.join(dp, f) for f in fns if f.endswith(".md"))
    return sorted(out)


def guide_docs(cfg):
    """The numbered tier-1 guides: markdown files directly under the knowledgebase root."""
    kb = cfg["KB"]
    return sorted(os.path.join(kb, f) for f in os.listdir(kb) if f.endswith(".md"))


def reference_docs(cfg, include_notes=False):
    """The reference library. Files starting with '_' (research notes) are not documents."""
    ref = cfg["REF"]
    if not os.path.isdir(ref):
        return []
    return sorted(os.path.join(ref, f) for f in os.listdir(ref)
                  if f.endswith(".md") and (include_notes or not f.startswith("_")))


def slug(heading):
    """GitHub-flavoured markdown anchor for a heading."""
    s = re.sub(r"[`*_]", "", heading).strip().lower()
    return re.sub(r"\s+", "-", re.sub(r"[^\w\s-]", "", s))


def list_scope(cfg, scope):
    """Enumerate one scope from the repository.

    scope keys: dir (repo-relative), pattern (regex, full match on the name), strip (suffix to
    remove), kind ("files" default | "dirs" | "any"), recurse (bool), relative (bool: report the
    path relative to dir when recursing). Counts files, not directory entries, unless asked.
    """
    if scope.get("type") == "tables":
        return create_table_names(cfg, scope.get("globs", []))
    if scope.get("type") == "regex":
        return regex_names(cfg, scope.get("globs", []), scope["regex"], scope.get("within"))
    base = os.path.join(cfg["ROOT"], scope["dir"])
    if not os.path.isdir(base):
        return []
    pat = re.compile(scope.get("pattern", ".*"))
    kind = scope.get("kind", "files")
    strip = scope.get("strip")
    skip = set(cfg["source"]["skip_dirs"])
    names = []
    if scope.get("recurse"):
        for dp, dns, fns in os.walk(base):
            dns[:] = [d for d in dns if d not in skip and not d.startswith(".")]
            cands = fns if kind == "files" else dns if kind == "dirs" else fns + dns
            for f in cands:
                if f.startswith("."):
                    continue
                if pat.fullmatch(f):
                    names.append(os.path.relpath(os.path.join(dp, f), base) if scope.get("relative") else f)
    else:
        for f in sorted(os.listdir(base)):
            if f.startswith("."):
                continue
            full = os.path.join(base, f)
            if kind == "files" and not os.path.isfile(full):
                continue
            if kind == "dirs" and not os.path.isdir(full):
                continue
            if pat.fullmatch(f):
                names.append(f)
    if strip:
        names = [n[:-len(strip)] if n.endswith(strip) else n for n in names]
    return sorted(set(names))


def regex_names(cfg, globs, regex, within=None):
    """Every first matched capture group of `regex` (one regex or a list; multiline) in files matching the globs.

    Added for Open WebUI, where enumerable sets do not live one per file: SQLAlchemy
    `__tablename__` and Alembic `op.create_table(...)` names, persistent config keys in
    DEFAULT_CONFIG, environment variables read with os.getenv, ERROR_MESSAGES members.
    Files under source.skip_dirs (for example backend/data, which holds live uploads) are
    never read. `within` is an optional [start_regex, end_regex] pair that limits the search
    to the text from the first start match to the next end match (one dict literal, say).
    """
    rxs = [re.compile(r, re.M) for r in (regex if isinstance(regex, list) else [regex])]
    skip = set(cfg["source"]["skip_dirs"])
    names = set()
    for g in globs:
        for p in _glob.glob(os.path.join(cfg["ROOT"], g), recursive=True):
            parts = os.path.relpath(p, cfg["ROOT"]).split(os.sep)
            if not os.path.isfile(p) or any(part in skip for part in parts[:-1]):
                continue
            text = read(p)
            if within:
                start = re.search(within[0], text, re.M)
                if not start:
                    continue
                end = re.compile(within[1], re.M).search(text, start.end())
                text = text[start.start():end.end() if end else len(text)]
            for rx in rxs:
                for m in rx.finditer(text):
                    names.add(next(g for g in m.groups() if g is not None))
    return sorted(names)


_CREATE = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([^(\n]{1,160})", re.I)


def create_table_names(cfg, globs):
    """Every table name created by any file matching the globs (installer SQL, migrations).

    Takes the first whitespace-delimited token after CREATE TABLE and its last identifier, so
    `db`.`name`, "name", [name] and PHP-interpolated prefixes such as `".DB."`.`name` all
    resolve to name. CREATE TEMPORARY TABLE is deliberately not matched: a temporary table
    in a migration is not part of the schema.
    """
    names = set()
    for g in globs:
        for p in _glob.glob(os.path.join(cfg["ROOT"], g), recursive=True):
            try:
                for tok in _CREATE.findall(read(p)):
                    first = tok.strip().split()[0] if tok.strip() else ""
                    ids = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", first)
                    if ids and ids[-1].upper() not in ("IF", "NOT", "EXISTS", "TEMPORARY"):
                        names.add(ids[-1])
            except Exception:
                pass
    return sorted(names)
