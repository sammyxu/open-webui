# Maintenance Tools

Run these after a release, before trusting the knowledgebase again. Configuration for this
application is in `kb.config.json`; nothing else in this directory is application-specific.

| File | Purpose |
|---|---|
| `VERIFICATION.md` | **What was checked against the source and what it found.** Read this first |
| `ground-truth.md` | Facts verified directly against the source, with TO BE CONFIRMED gaps |
| `inventory.md` | Generated enumeration of everything countable (`inventory.py`) |
| `run_all_checks.sh` | Runs every check below in order; `--quotes` adds the slow one |
| `check_sections.py` | Every reference document has all fourteen sections |
| `validate.py` | Every repository path and `file:line` citation resolves |
| `check_links.py` | Every markdown link including `#section` anchors |
| `check_coverage.py` | Each reference document covers its enumerable scope, including every table |
| `verify_quotes.py` | Quoted user-facing messages really exist in the codebase (minutes) |
| `verification-baseline.txt` | Expected output of `verify_quotes.py`; after a release run `verify_quotes.py --diff tools/verification-baseline.txt` |
| `pii_grep.py` | No personal data anywhere, including generated JSON |
| `transfer_gap.py` | Every documented symptom is reachable from the tier-1 guides |
| `audit_absolutes.py` | Lists every "never/always/cannot" claim for review |
| `build_index.py` | Regenerates `../ai/*.json`. Run after editing any document |
| `db_select.sh` | Read-only query helper for database verification |

**Reading the output.** Some flags are correct: a document may deliberately cite a file to record
that it is *missing*. Review each flag; do not bulk-fix. A blanket find-and-replace once destroyed
a genuine finding.

**What the checks do not cover.** That a cited line still says what the document claims. Line
numbers drift on every release, so a citation can resolve and still be wrong. Only re-reading the
code catches that.
