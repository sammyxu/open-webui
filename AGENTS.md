# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Overview

Open WebUI is a self-hosted AI chat platform: a SvelteKit SPA frontend (`src/`) and a FastAPI backend (`backend/open_webui/`). In production the backend serves the built frontend from `build/` (`SPAStaticFiles` in `main.py`); in dev they run as two processes with Vite proxying to the backend.

Requirements: Python 3.11–3.12, Node 18.13–22 (CI and Docker use Node 22). Frontend installs need `npm install --force`.

### This Checkout: the `uoft` Fork (MedIT GPT)

- `uoft` is the University of Toronto deployment, branded **MedIT GPT**. It is three commits (`402a737ba`, `146c436f8`, `aeed1832c`) on top of `main`, and `main` equals `upstream/main` at the v0.11.4 merge (`8bd8b4fac`). Remotes: `origin` is the fork, `upstream` is `open-webui/open-webui`. Inspect local changes with `git diff main...uoft`.
- Local changes: default `WEBUI_NAME` is `MedIT GPT` without the upstream " (Open WebUI)" suffix (`backend/open_webui/env.py:951`) and `APP_NAME` likewise (`src/lib/constants.ts`); U of T logos and favicons in `static/static/`, `static/favicon.png` and `backend/open_webui/static/`; two per-user Interface toggles, **Hide Processing Details** and **Inline Citations** (`showInlineCitations` and `hideProcessingDetails` in the `InterfaceSettings` model, `backend/open_webui/models/users.py:99-100`; UI in `src/lib/components/common/InterfaceSettings.svelte`; dotted i18n keys filled in `en-US`); the test-notification text uses the app name (`backend/open_webui/utils/notifications.py`).
- Keep fork edits narrow so upstream releases merge cleanly. The maintainer has confirmed the deployment qualifies for a LICENSE §4 branding exception, so renaming is allowed on this branch, but keep the licence comments and copyright lines.
- This `AGENTS.md` is gitignored (`.gitignore:18`); it is local guidance, not part of the fork's history.

## Commands

```bash
# Dev servers (two terminals)
cd backend && sh dev.sh        # uvicorn on :8080 with --reload
                               # NOTE: dev.sh does NOT auto-generate WEBUI_SECRET_KEY (start.sh does)
                               # and the app refuses to serve without it. Export it first, e.g.:
                               #   WEBUI_SECRET_KEY="$(cat .webui_secret_key)" sh dev.sh
npm run dev                    # Vite on :5173; proxies /api, /ollama, /openai, /oauth, /ws to :8080
                               # (override backend target with WEBUI_BACKEND_URL)

# Build
npm run build                  # may need NODE_OPTIONS=--max-old-space-size=8192

# Formatting (CI enforces both by failing on a dirty tree / ruff format --check)
npm run format                 # prettier over frontend + md/json
npm run format:backend         # ruff format

# i18n — REQUIRED after adding/changing any $i18n.t('...') string
npm run i18n:parse             # syncs every locale file; CI fails if this produces a diff

# Checks
npm run check                  # svelte-check (type checking)
npm run lint:frontend          # eslint --fix
ruff check --select=F --ignore=F401,F403,F405,F541,F811,F841 .   # backend logic-error check (matches CI)

# Tests
npm run test:frontend          # vitest --passWithNoTests — there are effectively no tests in this repo;
                               # the real regression suite lives in the external open-webui/tests repo
                               # and runs only on release PRs. Don't add tests unless asked.

# Database migrations (Alembic; run from backend/open_webui/)
DATABASE_URL=<url> alembic revision --autogenerate -m "description"
```

`npm run dev`/`build` first run `scripts/prepare-pyodide.js`, which downloads Pyodide into `static/pyodide`.

## Runtime and Tooling Caveats (Verified 2026-10-07 on the Maintainer's Mac)

- Local Node is v25.0.0, outside `engines` (`>=18.13.0 <=22.x.x`, `package.json:157-159`), yet `vitest` 1.6.1, `svelte-check` 4.4.5, `prettier` 3.8.1 and `eslint` 8.57.1 all run. npm is 11.6.2.
- System `python3` is 3.14; the project venv `.venv/` is 3.12.13 (`requires-python >= 3.11, < 3.13`, `pyproject.toml:119`). Use `.venv/bin/ruff` (0.15.18) and `.venv/bin/alembic` (1.18.4).
- There are no backend tests (no `test_*.py` under `backend/open_webui`) and no frontend `*.test.*`/`*.spec.*` files; `test/` holds only `test_files/`.
- `backend/data/` holds the live local SQLite database (`webui.db`), uploads, the Chroma vector store and caches. Treat it as personal data: do not read rows, do not commit it.
- `sqlite3` 3.43.2, Docker 29.2.0 and `uv` 0.11.6 are installed.

## Backend architecture (`backend/open_webui/`)

- **`main.py`** (~3k lines) builds the FastAPI app: mounts ~31 routers from `routers/` under `/api/v1/<name>`, plus `/ollama` and `/openai` which are **reverse proxies** to upstream LLM providers. It also defines top-level endpoints directly: `/api/chat/completions` (OpenAI-compatible), `/api/v1/messages` (Anthropic-compatible), `/api/models`, `/api/config`, `/oauth/*`, `/health`. OpenAPI docs at `/docs` only when `ENV=dev` (the default).
  - Mount exceptions (`main.py:843-887`): `calendar.py` mounts at `/api/v1/calendars` (plural); `scim.py` at `/api/v1/scim/v2` and only when `ENABLE_SCIM`; `analytics.py` only when `ENABLE_ADMIN_ANALYTICS`. The Docker image sets `ENV=prod` (`Dockerfile:74`), so `/docs` is off there.
- **Chat request flow**: `main.py:chat_completion` → `utils/middleware.py:process_chat_payload` (filters, tools, RAG, web search, memory) → `utils/chat.py:generate_chat_completion` (routes to Ollama / OpenAI / pipe function / direct connection) → `process_chat_response` (streaming, outlet filters, background tasks, socket emission).
- **Models pattern** (`models/`): each file pairs a SQLAlchemy table class with Pydantic models (`XModel`/`XForm`/`XResponse`) and an `XTable` repository class exported as a module singleton (`Tools = ToolsTable()`, `Chats`, `Users`, …). Repository methods are async, take an optional `db: AsyncSession`, and use `async with get_async_db_context(db)`. JSON columns use the custom `JSONField` (portable across SQLite/Postgres). Access control lives in the normalized `access_grant` table.
- **Database** (`internal/db.py`): sync engine only for startup/config/Alembic; async engine (aiosqlite / psycopg3) for all runtime queries. SQLite (default, `backend/data/webui.db`) or PostgreSQL; optional SQLCipher. Endpoints get sessions via `Depends(get_async_session)`; auth via `Depends(get_verified_user)` / `get_admin_user` from `utils/auth.py`.
- **Migrations** (`migrations/versions/`): run automatically on startup (`alembic upgrade head` unless `ENABLE_DB_MIGRATIONS=False`). Existing migrations are hand-edited and idempotent, guarding with `get_existing_tables()` from `migrations/util.py` — follow that style. (In practice only 3 of the 58 revisions call `get_existing_tables()`; most inspect inline with `sa.inspect(...)`/`get_table_names`/`get_columns`, and `856c5b02fb54` and the head `d4c1a8e37b62` have no guards. The chain is linear, root `7e5b5dc7342b`.) For `--autogenerate` to see a table, its model must be imported (directly or transitively) in `migrations/env.py`, which only imports a few.
- **Config**: `env.py` holds bootstrap/env-only settings (paths, `DATABASE_URL`, Redis, secret key); it loads `<repo>/.env`. `config.py` seeds a `DEFAULT_CONFIG` dict of dotted keys into the DB `config` table — **after first boot the DB value wins over the env var** (unless `ENABLE_PERSISTENT_CONFIG=False`). Runtime access is async: `await Config.get('openai.api_base_urls')`, `Config.get_many(...)`, `Config.upsert({...})`.
  - The `config` table holds one row per dotted key (`key`, JSON `value`, `updated_at`; `models/config.py:101-108`). `seed_defaults` inserts only missing keys at startup (`models/config.py:241-266`), which is why the DB wins. **Exception: `oauth.*` keys are never read from or written to the DB unless `ENABLE_OAUTH_PERSISTENT_CONFIG=True`** (default `False`, `config.py:3232`; `models/config.py:133-138`), so OAuth settings come from the environment by default. `DEFAULT_CONFIG` (`config.py:2822`) holds 405 keys: 404 dotted keys in 33 namespaces plus the undotted `webhook_url`.
  - Migrations run when `open_webui.config` is **imported** (`config.py:81-82`), before `lifespan`, in every process; a failure aborts startup. `RESET_CONFIG_ON_START=True` (`env.py:368`) wipes the `config` table on every boot.
  - **SQLCipher is broken in v0.11.4:** `_make_async_url` raises for `sqlite+sqlcipher://` (`internal/db.py:244-248`) and runs unconditionally at import (`internal/db.py:447`), so a SQLCipher `DATABASE_URL` stops startup despite the sync-engine support.
- **Plugin system** (user-supplied Python stored in the DB, `exec()`-loaded by `utils/plugin.py`):
  - **Tools** (`models/tools.py`): a `class Tools` whose methods become LLM-callable functions; specs generated from signatures/docstrings in `utils/tools.py`. Distinct from *tool servers* (external OpenAPI/MCP servers) and from built-in native tools (`tools/builtin.py`).
  - **Functions** (`models/functions.py`, `functions.py`): the top-level class sets the type — `Pipe` (custom model/provider), `Filter` (`inlet`/`outlet`/`stream` hooks), `Action` (message button), `Event` (system-event handler). `Valves`/`UserValves` are Pydantic config classes, stored in the DB and encrypted only when `ENABLE_VALVE_ENCRYPTION=True` (default `False`, `env.py:767`; `utils/valves.py:22-24`).
  - **Pipelines** (`routers/pipelines.py`): an *external* server reached as an OpenAI-compatible connection, not in-process.
- **RAG** (`retrieval/`): `loaders/main.py` picks a content-extraction engine; `web/` has ~30 search providers; `vector/factory.py` holds the `VECTOR_DB_CLIENT` singleton (chroma default, pgvector, qdrant, milvus, …); `utils.py` covers embeddings and hybrid (BM25 + vector) search. Ingestion endpoints are in `routers/retrieval.py`.
- **Websockets** (`socket/main.py`): python-socketio mounted at `/ws` (path `/ws/socket.io`); `WEBSOCKET_MANAGER=redis` enables multi-worker. `get_event_emitter`/`get_event_call` are how backend code (including plugins) pushes events to or requests input from the browser.
- **Storage** (`storage/provider.py`): `Storage` singleton — Local, S3, GCS, Azure, selected by `STORAGE_PROVIDER`.

## Startup Order and Background Jobs

There is no crontab and no separate worker process. Everything periodic runs as an asyncio task inside each uvicorn worker, started by `lifespan` in `main.py:345-472`, in this order:

1. Logger, optional `RESET_CONFIG_ON_START`, legacy `config.json` import, `seed_registered_defaults`, `initialize_runtime_config`, legacy webhook migration (`main.py:361-369`).
2. Optional admin bootstrap from `WEBUI_ADMIN_EMAIL`/`WEBUI_ADMIN_PASSWORD` when no users exist; it then turns sign-up off (`main.py:377-380`). `SAFE_MODE` deactivates every function (`main.py:382-383`).
3. Installs Python requirements declared by stored tools and functions, blocking, before serving (`main.py:387-388`). Precisely: only **active** functions and tools **owned by admins** (`utils/plugin.py:465-480`); other tools install theirs lazily the first time each process loads them. Skipped entirely when `ENABLE_PLUGINS` is off.
4. Redis listeners when Redis is configured: task command listener, task heartbeat (when `REDIS_TASK_TTL > 0`), and the websocket event listener when `WEBSOCKET_MANAGER == 'redis'` (`main.py:390-398`).
5. Always: `periodic_usage_pool_cleanup` and `periodic_session_pool_cleanup` (`socket/main.py:266`, `:212`) and the automations `scheduler_worker_loop` (`utils/automations.py:69`), which polls due automations every `SCHEDULER_POLL_INTERVAL` seconds (default 10), timers every `TIMER_POLL_INTERVAL` (default 1) and calendar alerts (`utils/automations.py:53-126`, `:537`).
6. Optional model-list and tool-server pre-fetch; then `app.state.startup_complete = True`, which `/ready` reports (`main.py:407-471`).

Per-chat background work (title, tags, follow-ups, memory review) is spawned from the request path, not on a schedule. The app sends **no email**: there is no SMTP code in `backend/open_webui`.

## Deployment

- The repository does not say how MedIT GPT is hosted: no production host, domain, registry or deploy recipe for it exists here, and no workflow in `.github/workflows/` triggers on `uoft` (only `docker.yaml` can be dispatched by hand). Ask before assuming one.
- Image (`Dockerfile`): Node 22 build stage, then `python:3.11-slim-bookworm`; `WORKDIR /app/backend`; `ENV=prod`; port 8080; `HEALTHCHECK` on `/health`; `CMD ["bash", "start.sh"]`. Build args `USE_CUDA`, `USE_OLLAMA`, `USE_SLIM`, `USE_PERMISSION_HARDENING`, `UID`/`GID` (root by default).
- `backend/start.sh` runs `uvicorn` with `--workers ${UVICORN_WORKERS:-1}`. If `WEBUI_SECRET_KEY` is unset it generates `.webui_secret_key` in `backend/`, which in the image is **outside** the `/app/backend/data` volume (`docker-compose.yaml:18`): a recreated container gets a new key and every session ends. Set `WEBUI_SECRET_KEY` from a secret store in any real deployment.
- Health: `/health` always returns `{"status": true}`; `/ready` returns 503 until startup finishes or when the database or configured Redis is down (`main.py:2963-3006`).
- More than one worker or replica needs `WEBSOCKET_MANAGER=redis` plus `REDIS_URL`, a shared `WEBUI_SECRET_KEY`, PostgreSQL, shared upload and vector storage, and migrations run by one instance (`ENABLE_DB_MIGRATIONS=False` elsewhere). Nothing warns when these are missing. Without Redis, sign-out does not revoke tokens server-side (`utils/auth.py:276-288`).
- Logs go to stdout only. The optional audit log (`AUDIT_LOG_LEVEL`, default `NONE`) writes `DATA_DIR/audit.log` and contains user names, emails, IPs and request bodies.
- `docker-cleanup.sh` runs `docker compose down -v`, which deletes the data volume. `make remove` and `make update` call scripts that are not in the repository.

## Frontend architecture (`src/`)

- SvelteKit SPA: `adapter-static` with `fallback: 'index.html'`, `ssr = false`. No server-side code.
- **Svelte 5 is installed, but the codebase uses legacy Svelte 4 syntax almost everywhere** (`export let`, `$:`, `on:click`, `createEventDispatcher`, slots). Match the surrounding file's style; don't introduce runes into legacy components.
- **API layer** (`src/lib/apis/<domain>/index.ts`): one folder per backend router. Plain `fetch` functions that take a `token` argument and send `Authorization: Bearer` to `${WEBUI_API_BASE_URL}/...` (base URLs in `src/lib/constants.ts`; same-origin, so the Vite proxy handles dev). Token lives in `localStorage.token`.
- **State**: ~100 global writable/derived stores in `src/lib/stores/index.ts` (`user`, `config`, `settings`, `models`, `socket`, …).
- **Routes**: root `+layout.svelte` does i18n init, socket.io connection, and config/session loading. `(app)/` is the authenticated group: `c/[id]` (chat), `channels/`, `notes/`, `workspace/{models,knowledge,prompts,tools,functions}`, `admin/`.
  - `admin/settings`, `admin/settings/[tab]` and `admin/analytics` are only redirect shims: admin settings and analytics live in the shared Settings window at `/?settings=admin:<tab>` (personal tabs at `/?settings=<tab>`).
- **Components**: `src/lib/components/` grouped by area (`chat/`, `admin/`, `workspace/`, `layout/`, `common/`, `icons/`).

## i18n

Translation keys are the English source strings themselves (`keySeparator: false`). In components: `const i18n = getContext('i18n')`, then `$i18n.t('Some text')` or `$i18n.t('Starting in {{count}} minutes', { count })`. After adding or changing strings, run `npm run i18n:parse` — it adds the key (as `""`) to all ~64 locale files, removes unused keys, and formats. Commit the result; CI fails otherwise.

**Exception: dotted keys.** Settings-screen copy uses dotted keys such as `settings.personal.interface.hideProcessingDetails.label`; their English text lives only in `src/lib/i18n/locales/en-US/translation.json` (1,079 such keys at v0.11.4). `i18n:parse` adds them as `""` everywhere, including `en-US`, so type the English label (Title Case) and description (sentence case) into `en-US` by hand afterwards. Other locales fall back to `en-US` because `returnEmptyString: false` (`src/lib/i18n/index.ts:114`).

## Conventions

- Python: ruff, line length 120, single quotes. Frontend: prettier — tabs, single quotes, printWidth 100.
- PRs target the `dev` branch, with title prefixes like `feat:`, `fix:`, `i18n:`, `refac:`.
- License-protected branding: comments reading "Do not alter, remove, obscure, or replace …" guard the "Open WebUI" name/logo strings — leave those strings and comments intact.

## Support Knowledgebase (`knowledgebase/`)

A tier-1 support knowledgebase for MedIT GPT is being built in `knowledgebase/` with the knowledgebase-builder method: numbered guides at the top level, a fourteen-section reference document per area in `reference/` (partition in `reference/_areas.md`, researcher instructions in `reference/_research-prompt.md`), verified facts in `tools/ground-truth.md`, a generated `tools/inventory.md`, and checkers in `tools/` driven by `tools/kb.config.json`.

- Run `bash knowledgebase/tools/run_all_checks.sh` after any edit (add `--quotes` before a hand-over) and `python3 knowledgebase/tools/inventory.py` after a release.
- Rules: edits are additive (correct wrong claims in place and log them in `tools/VERIFICATION.md`); no personal data or secrets anywhere; anything organisational the code cannot prove is written **TO BE CONFIRMED**; the reference layer wins over the guides.
- Local toolkit extensions: `regex` scope type in `tools/kbconfig.py`, `citations.root_files` and SvelteKit route characters in `tools/validate.py`, and a read-only `sqlite` mode in `tools/db_select.sh`.
