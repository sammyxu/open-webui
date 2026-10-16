#!/usr/bin/env bash
# Read-only query helper for Phase 6 (database verification).
#
# Refuses anything that is not a single SELECT / WITH / SHOW / DESCRIBE / EXPLAIN statement
# and refuses any statement containing a write keyword, so that a slip can never modify the
# database. Credentials come from the environment only and are never echoed.
#
#   DB_CLIENT      mysql (default), psql, or sqlite (local extension; set DB_PATH)
#   DB_HOST        default 127.0.0.1   (a container hostname in the app config is usually
#                  reachable from the host only through the mapped port)
#   DB_PORT        default 3306 / 5432
#   DB_USER, DB_PASSWORD, DB_NAME
#   DB_EXTRA_ARGS  extra client flags, e.g. "--ssl-mode=DISABLED" (mysql 8 client) or
#                  "--skip-ssl" (mariadb client) when a dev server does not offer TLS
#
# usage: db_select.sh "SELECT organisation_id, title FROM organisations"        > out.tsv
set -euo pipefail
export LC_ALL=C
q="${1:-}"
if [ -z "$q" ]; then echo "usage: db_select.sh \"SELECT ...\"" >&2; exit 2; fi
upper=$(printf '%s' "$q" | sed -e 's/^[[:space:]]*//' | tr '[:lower:]' '[:upper:]')
case "$upper" in
  SHOW*|DESCRIBE*|DESC\ *) ;;
  SELECT*|WITH*|EXPLAIN*)
    if printf '%s' "$upper" | grep -qE '\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|GRANT|REVOKE|LOAD|CALL|LOCK|RENAME|OUTFILE|DUMPFILE|INTO|ANALYZE)\b'; then
      echo "refused: write keyword present in a read statement" >&2; exit 3
    fi ;;
  *) echo "refused: only SELECT, WITH, SHOW, DESCRIBE and EXPLAIN are allowed" >&2; exit 3 ;;
esac
if printf '%s' "$q" | sed 's/;[[:space:]]*$//' | grep -q ';'; then
  echo "refused: one statement per call" >&2; exit 3
fi
case "${DB_CLIENT:-mysql}" in
  sqlite)
    # Local extension for Open WebUI's default SQLite database. -readonly opens the file
    # read-only; PRAGMA is refused above, so use the pragma_* table-valued functions
    # (SELECT name FROM pragma_table_info('chat')). DB_PATH is the database file.
    sqlite3 -readonly -batch -header -separator "$(printf '\t')" "${DB_PATH:?DB_PATH unset}" "$q" ;;
  mysql)
    MYSQL_PWD="${DB_PASSWORD:-}" mysql --batch --raw \
      --host="${DB_HOST:-127.0.0.1}" --port="${DB_PORT:-3306}" --user="${DB_USER:?DB_USER unset}" \
      ${DB_EXTRA_ARGS:-} "${DB_NAME:?DB_NAME unset}" -e "$q" ;;
  psql)
    PGPASSWORD="${DB_PASSWORD:-}" psql -h "${DB_HOST:-127.0.0.1}" -p "${DB_PORT:-5432}" \
      -U "${DB_USER:?DB_USER unset}" -d "${DB_NAME:?DB_NAME unset}" -v ON_ERROR_STOP=1 \
      -A -F "$(printf '\t')" ${DB_EXTRA_ARGS:-} -c "$q" ;;
  *) echo "DB_CLIENT must be mysql, psql or sqlite" >&2; exit 2 ;;
esac
