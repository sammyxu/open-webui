#!/usr/bin/env bash
# Run every verification check in the order the method prescribes (Phase 4), then rebuild
# the JSON indexes. Each check catches something the previous one cannot.
#
#   run_all_checks.sh            fast checks only
#   run_all_checks.sh --quotes   also run verify_quotes.py (minutes; set KB_CORPUS to cache)
#
# LC_ALL=C: a UTF-8 locale once made `tr` abort silently, so nothing matched and everything
# looked wrong. Byte-oriented text tools get the C locale here.
set -u
export LC_ALL=C
here=$(cd "$(dirname "$0")" && pwd)
status=0
run() { local name="$1"; shift; echo; echo "=================== $name"; "$@"; local rc=$?; echo "--- exit $rc"; [ $rc -ne 0 ] && status=1; return 0; }
run "reference sections complete"   python3 "$here/check_sections.py"
run "path and line citations"       python3 "$here/validate.py"
run "links and anchors"             python3 "$here/check_links.py"
run "scope coverage"                python3 "$here/check_coverage.py"
if [ "${1:-}" = "--quotes" ]; then
run "quoted messages exist"         python3 "$here/verify_quotes.py"
fi
run "PII grep"                      python3 "$here/pii_grep.py"
run "knowledge-transfer gap"        python3 "$here/transfer_gap.py"
run "absolute claims (guides)"      python3 "$here/audit_absolutes.py" --guides-only --summary
run "rebuild ai/*.json"             python3 "$here/build_index.py"
echo; echo "overall: $([ $status -eq 0 ] && echo clean || echo 'findings to review')"
exit $status
