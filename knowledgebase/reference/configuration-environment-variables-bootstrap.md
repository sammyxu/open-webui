# Configuration: Environment Variables (Bootstrap and Runtime)

## At a Glance

- This is a catalogue of the environment variables that MedIT GPT (Open WebUI v0.11.4) reads
  **outside** `backend/open_webui/config.py`: in `env.py`, `__init__.py`, `internal/`, `utils/`,
  `routers/`, `retrieval/`, `socket/` and `storage/`, plus the `ENV` lines in `Dockerfile` and
  the variables `backend/start.sh` reads.
- These variables are **environment-only**: the code reads them when the process starts and they
  are not stored in the database `config` table, so changing one needs a restart of every worker.
- Persistent settings (the ones admins change on the Admin Settings screens) are covered by the
  two persistent-settings catalogues; for those, the environment only seeds the value on first
  boot and the database wins afterwards.
- Production values for MedIT GPT are not in the repository and are **TO BE CONFIRMED** with the
  platform maintainer.
- Section 7 catalogues 457 distinct variables, including all 238 in the inventory scope, with
  default, type, effect, restart need and the document that explains each feature; section 10
  lists the start-up stops and warnings that missing or malformed values cause.
- The usual support patterns: a malformed or missing value stops start-up (section 11.1); a
  variable that only seeds a persistent setting is ignored after first boot (section 11.2); workers
  or replicas with different values or no Redis behave differently (section 11.3); a secret key
  that is not kept across redeploys signs everyone out (section 11.4).

## 1. Purpose and Who Uses It

An **environment variable** is a named value handed to the server process when it starts, for
example in the container definition, a compose file, a `.env` file or the shell that launches
`start.sh`. MedIT GPT reads two different kinds, and support needs to know which kind a variable
is before saying anything about a change to it.

| Kind | Where it is read | Where the live value lives | What a change needs | Covered by |
|---|---|---|---|---|
| **Environment-only (bootstrap and runtime)** | `backend/open_webui/env.py` and a few other modules, at import time | Process memory only; not stored in the `config` table | Restart of every worker and replica | This document |
| **Seed of a persistent setting** | `backend/open_webui/config.py` | The `config` table row for the dotted key | Nothing: after first boot the stored value wins and the variable is ignored | `configuration-persistent-settings-a-to-o.md`, `configuration-persistent-settings-r-to-w.md` |
| **Seed of an `oauth.*` setting** | `backend/open_webui/config.py` | The environment, unless `ENABLE_OAUTH_PERSISTENT_CONFIG=True` | Restart (when not persisted) | `sso-oauth-oidc-and-scim.md` |

### 1.1 Precedence Rules

- **Environment-only variables.** The value is the one present in the process environment when the
  module was imported, otherwise the default written in code. For example `DATA_DIR` falls back to
  `backend/data` (`backend/open_webui/env.py:228`) and `ENV` to `dev`
  (`backend/open_webui/env.py:139`).
- **The repository-root `.env` file** is loaded first by `load_dotenv(find_dotenv(str(BASE_DIR / '.env')))`
  (`backend/open_webui/env.py:40`). The call does not pass `override`, and python-dotenv's default
  keeps any variable that is already set in the real environment (library behaviour in the
  installed python-dotenv; see section 14). So a value set by Docker or the shell beats the same
  name in `.env`.
- **Persistent settings.** At startup only keys missing from the `config` table are inserted from
  the environment-derived defaults; existing rows are left alone
  (`backend/open_webui/models/config.py:241-266`). This is why, after first boot, changing a
  variable such as `ENABLE_SIGNUP` has no effect (ground truth, "Settings: Where a Value Comes
  From").
- **`oauth.*` keys** are never read from or written to the database unless
  `ENABLE_OAUTH_PERSISTENT_CONFIG=True` (`backend/open_webui/config.py:3232`;
  `backend/open_webui/models/config.py:133-138`), so OAuth settings follow the environment by
  default.
- **`ENABLE_PERSISTENT_CONFIG=False`** (`backend/open_webui/config.py:3231`) makes every key
  environment-only; an admin edit then changes only the memory of the worker that handled the save
  (`backend/open_webui/models/config.py:196-206`).
- **`RESET_CONFIG_ON_START=True`** (`backend/open_webui/env.py:368`) wipes the stored settings at
  every boot (`backend/open_webui/main.py:363-364`), so the environment-derived defaults are
  seeded again each time.

### 1.2 Who Uses This Document

- **Tier 1 support**: to recognize that a reported behaviour is governed by deployment
  configuration (which tier 1 cannot see or change) and to escalate with the right variable name.
- **The platform maintainer**: as a catalogue of names, defaults and effects when changing the
  deployment. Production values for MedIT GPT are not in the repository and are
  **TO BE CONFIRMED**.

## 2. Navigation and URLs

There is no screen that lists or edits environment variables. Their values are set outside the
application, in one of these places.

| Place | What it sets | Source |
|---|---|---|
| Docker image `ENV` lines | `ENV=prod`, `PORT=8080`, the `USE_*_DOCKER` flags, `OLLAMA_BASE_URL`, `OPENAI_API_BASE_URL`, `OPENAI_API_KEY` (empty), `WEBUI_SECRET_KEY` (empty), telemetry opt-outs, model and cache paths, `HOME`, `WEBUI_BUILD_VERSION`, `DOCKER=true` | `Dockerfile:71-112`, `Dockerfile:121`, `Dockerfile:228-229` (see section 7.13) |
| `docker-compose.yaml` | `OLLAMA_BASE_URL=http://ollama:11434` and an empty `WEBUI_SECRET_KEY`; the data volume at `/app/backend/data` | `docker-compose.yaml:18`, `docker-compose.yaml:23-25` |
| Compose overlays | OpenTelemetry switches and endpoint; Playwright web loader | `docker-compose.otel.yaml:24-29`; `docker-compose.playwright.yaml:8-10` |
| `.env` at the repository root | Anything; loaded at import of `env.py` without overriding the real environment | `backend/open_webui/env.py:40` (the file itself was not opened) |
| `.env.example` | A tracked template listing a few variables | `.env.example:1-46` |
| `backend/start.sh` (the image's command) | Generates or loads the secret key file, sets defaults for `PORT`, `HOST`, `UVICORN_WORKERS`, and passes uvicorn options | `backend/start.sh:29-50`, `backend/start.sh:96-112`; `Dockerfile:231` |
| `backend/dev.sh` (local development) | `CORS_ALLOW_ORIGIN` for the Vite port, `PORT`; it does not create a secret key | `backend/dev.sh:1-3` |
| `open-webui serve` (pip install) | Sets `FROM_INIT_PY=true`, loads or creates `.webui_secret_key` in the current directory | `backend/open_webui/__init__.py:35-50` |

Which of these MedIT GPT production uses is **TO BE CONFIRMED** (ground truth, "Environments").

The only in-app places where an environment-only value shows indirectly are the product name
(`WEBUI_NAME`, shown in the browser title and sign-in page) and the version and build tooltip in
**Settings > About** (`src/lib/components/chat/Settings/About.svelte:67`) and **Admin Settings >
General** (`src/lib/components/admin/Settings/General.svelte:140`). The container health check
calls `/health` (`Dockerfile:212`).

## 3. Roles and Permissions

- **Only whoever controls the deployment** (the platform maintainer) can set or change environment
  variables. No screen in the application, including the admin screens, lists or edits them.
- **Admins** see the effects of some variables: for example `ENABLE_ADMIN_CHAT_ACCESS` decides
  whether admins can open other users' chats (`backend/open_webui/env.py:371`) and
  `BYPASS_MODEL_ACCESS_CONTROL` whether model access control applies to non-admins
  (`backend/open_webui/env.py:832`). The rules themselves are in
  `users-groups-roles-and-permissions.md`.
- **Tier 1** is read-only and cannot see environment values. The resolution for any problem traced
  to an environment variable is an escalation to the platform maintainer (section 11).

## 4. Key Concepts and Terminology

| Term | Meaning in this code base |
|---|---|
| Bootstrap variable | Read while the backend modules are being imported, before the web server accepts requests (for example `DATA_DIR`, `DATABASE_URL`, `WEBUI_SECRET_KEY`). |
| Runtime variable | Also read at import, but governs behaviour while serving requests (timeouts, feature switches, header names). The code reads it once; a change needs a restart. |
| Boolean parsing | Most switches use `.lower() == 'true'`, so only the word `true` in any letter case turns them on; `1`, `yes` and `on` count as off (for example `backend/open_webui/env.py:44`). |
| Silent fallback | Most numeric variables are parsed inside `try` blocks; an unparsable value falls back to the default without a message (for example `REDIS_RESPONSE_STREAM_TTL`, `backend/open_webui/env.py:386-389`). A few are parsed without a guard and stop start-up instead (section 10). |
| Alias (fallback name) | An older name read when the newer one is unset: `WEBUI_JWT_SECRET_KEY` for `WEBUI_SECRET_KEY` (`backend/open_webui/env.py:762-765`), `SCIM_ENABLED` for `ENABLE_SCIM` (`:907`), `CHAT_RESPONSE_MAX_TOOL_CALL_RETRIES` for `CHAT_RESPONSE_MAX_TOOL_CALL_ITERATIONS` (`:1083-1086`), `AIOHTTP_CLIENT_TIMEOUT_OPENAI_MODEL_LIST` for `AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST` (`:656-659`). |
| Chained default | A variable whose default is another variable's value, for example `WEBUI_AUTH_COOKIE_SAME_SITE` defaults to `WEBUI_SESSION_COOKIE_SAME_SITE` (`backend/open_webui/env.py:771`). |
| Worker | One uvicorn process. Each worker imports `env.py` itself, so each reads the environment at its own start (`backend/start.sh:99-112`). |
| Replica | Another container or host running the same application; it has its own environment, so values can differ between replicas unless the deployment keeps them identical. |
| `FROM_INIT_PY` | Set to `true` by `open-webui serve` (`backend/open_webui/__init__.py:40`); switches the version source and the default data and front-end directories (`backend/open_webui/env.py:143-151`, `:230-257`). |

## 5. Workflows (Step by Step)

Tier 1 does not perform any of these workflows; they describe what the platform maintainer does,
so that support can explain timing and side effects and collect the right details for an
escalation.

### 5.1 How a Value Reaches the Code

1. The process starts with the environment given by the container, compose file or shell.
2. `backend/open_webui/env.py` loads the repository-root `.env` file, adding only names that are
   not already set (`backend/open_webui/env.py:40`; section 1.1).
3. Each module-level `os.getenv(...)` line runs once, when the module is first imported, and
   stores the parsed value in a Python constant (for example
   `UVICORN_WORKERS = max(int(os.getenv('UVICORN_WORKERS', '1')), 1)`,
   `backend/open_webui/env.py:462`).
4. Other modules import those constants (`from open_webui.env import ...`), so the value is fixed
   for the life of the worker. The scheduler intervals in `backend/open_webui/utils/automations.py`
   are also read once, at import (`backend/open_webui/utils/automations.py:53-56`).
5. Every worker repeats steps 2 to 4 in its own process.

### 5.2 Changing an Environment-Only Variable Safely (Platform Maintainer)

1. Change the value where the deployment defines it (section 2). Production's mechanism is
   **TO BE CONFIRMED**.
2. Restart **every** worker and replica. A running worker keeps the old value.
3. Watch the start-up log for exits and warnings (section 10). Each worker reports the effective
   log level as `GLOBAL_LOG_LEVEL: {GLOBAL_LOG_LEVEL}` when its start-up begins
   (`backend/open_webui/utils/logger.py:223`, called from `backend/open_webui/main.py:361`).
   *Corrected 2026-10-10: this step said the line comes first from `env.py`
   (`backend/open_webui/env.py:127`). That earlier copy is printed only when `GLOBAL_LOG_LEVEL` is
   set to a valid level name; otherwise no log handler exists yet and Python's standard logging
   drops informational lines (`backend/open_webui/env.py:113-124`).*
4. Check that the service reports ready (`/ready` returns 503 until start-up finishes; see
   `backend-architecture-and-request-lifecycle.md`).
5. For multi-worker or multi-replica deployments, make the same change everywhere at once:
   `WEBUI_SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, `WEBSOCKET_MANAGER`, `VECTOR_DB`,
   `STORAGE_PROVIDER` and `DATA_DIR` must agree between workers (CLAUDE.md, "Deployment"), and
   only one instance should run migrations (`ENABLE_DB_MIGRATIONS=False` on the others,
   `backend/open_webui/config.py:81-82`).

### 5.3 Changing a Variable That Seeds a Persistent Setting

Changing the variable has no effect once the key exists in the `config` table (section 1.1). The
supported route is the matching Admin Settings screen; the catalogue of keys is in the two
persistent-settings documents. `RESET_CONFIG_ON_START=True` re-seeds every key from the
environment at each boot, which discards all admin edits (`backend/open_webui/main.py:363-364`).

### 5.4 Changing the Secret Key

`WEBUI_SECRET_KEY` signs sign-in tokens and the session cookie
(`backend/open_webui/utils/auth.py:51`; `backend/open_webui/main.py:2670`) and is the default for
the two OAuth encryption keys (`backend/open_webui/env.py:873-875`). A new value signs every user
out (CLAUDE.md, "Deployment"). In the Docker image, `start.sh` writes a generated key to
`backend/.webui_secret_key`, which is outside the data volume, so a recreated container gets a new
key unless the variable is set (`backend/start.sh:31-50`; `docker-compose.yaml:18`). Other
consequences for stored data are security-sensitive: refer to the platform maintainer and U of T
Information Security (security.utoronto.ca).

### 5.5 Bootstrapping the First Admin from the Environment

When `WEBUI_ADMIN_EMAIL` and `WEBUI_ADMIN_PASSWORD` are both set and no users exist, start-up
creates an admin account named `WEBUI_ADMIN_NAME` (default `Admin`) and turns sign-up off
(`backend/open_webui/env.py:798-800`; `backend/open_webui/main.py:377-380`). The details are in
`authentication-and-sign-in.md`.

## 6. Data Model

Environment variables are not stored in the database. They do decide where data lives and create
a few files:

| Item | Path or effect | Governed by | Source |
|---|---|---|---|
| Data directory | `backend/data` by default; `/app/backend/data` in the image (the volume) | `DATA_DIR` | `backend/open_webui/env.py:228`; `docker-compose.yaml:18` |
| Relational database | `sqlite:///{DATA_DIR}/webui.db` unless `DATABASE_URL` or the five `DATABASE_*` parts are set | `DATABASE_URL`, `DATABASE_TYPE`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME` | `backend/open_webui/env.py:271-301` |
| Legacy database rename | A `DATA_DIR/ollama.db` file is renamed to `webui.db` at import | `DATA_DIR` | `backend/open_webui/env.py:264-266` |
| Secret key file | `backend/.webui_secret_key` (`start.sh`) or `./.webui_secret_key` in the current directory (`open-webui serve`), created only when no key is set | `WEBUI_SECRET_KEY`, `WEBUI_JWT_SECRET_KEY`, `WEBUI_SECRET_KEY_FILE`, `WEBUI_SECRET_KEY_LENGTH` | `backend/start.sh:31-50`; `backend/open_webui/__init__.py:13`, `:41-50` |
| Audit log | `DATA_DIR/audit.log`, rotated at `10MB` by default; contains personal data | `AUDIT_LOG_LEVEL`, `ENABLE_AUDIT_LOGS_FILE`, `AUDIT_LOGS_FILE_PATH`, `AUDIT_LOG_FILE_ROTATION_SIZE` | `backend/open_webui/env.py:1219-1226`, `:1234` |
| Licence data file | Read from `DATA_DIR/l.data` when present | `LICENSE_BLOB_PATH` | `backend/open_webui/env.py:925-928` |
| Package data move (`open-webui serve` only) | When an old data directory exists beside the package, it is copied to the new location, zipped to `open_webui_data.zip` and removed | `FROM_INIT_PY`, `DATA_DIR` | `backend/open_webui/env.py:230-250` |
| Hugging Face offline flag | `OFFLINE_MODE=true` sets `HF_HUB_OFFLINE=1` in the process environment and turns off the version check | `OFFLINE_MODE` | `backend/open_webui/env.py:1200-1205` |

The `config` table, where persistent settings live, is described in
`database-schema-identity-chats-and-config.md`.

## 7. Settings and Configuration

This section is the catalogue. It lists every environment variable read outside
`backend/open_webui/config.py` (the 238 names in the inventory scope, plus 20 names the inventory's
pattern does not catch: 14 security-header variables read through a lookup table, five limits read
through a helper function, and `HF_HUB_OFFLINE`, which the code sets), then the variables the start
scripts and the Docker image use, then a cross-reference of the environment-only variables read in
`config.py`.

### 7.1 How to Read the Catalogue

- **Code default** is what the code uses when the variable is unset. It is not the MedIT GPT
  production value, which is **TO BE CONFIRMED** for every row.
- **Type** describes the parsing:
  - *Boolean*: the value is compared with `.lower() == 'true'`, so only `true` (any letter case)
    turns the switch on.
  - *Integer* or *Number*: parsed with `int()` or `float()`. "Silent fallback" means an unparsable
    value is replaced by the default without a message; "exits if invalid" means start-up stops
    (section 10).
  - *Text*, *List* (comma-separated unless stated), *JSON*, *Path*.
- **Read at** is the `os.getenv`/`os.environ` line, written without the `backend/open_webui/` prefix
  in the table to keep it readable (`env.py:228` means `backend/open_webui/env.py:228`).
- **Restart.** Every variable in this catalogue is read once, when its module is imported, and a
  running process cannot see a changed environment. **Every change needs a restart of every worker
  and replica.** Rows read inside a function say so; they still need a restart because the process
  environment does not change while it runs.
- **In depth** names the reference document that explains the feature. Documents not yet written on
  2026-10-10 are marked *(planned)*.
- **Secrets.** Rows for keys, passwords and tokens give the name only; their values are set per
  environment and are never reproduced here.

### 7.2 Paths, Platform and Installation Identity

| Variable | Code default | Type | Read at | Effect | In depth |
|---|---|---|---|---|---|
| `DATA_DIR` | `backend/data`; under `open-webui serve`, `data` inside the installed package | Path | `env.py:228`, `:231`, `:250` | Root for the SQLite database, uploads (`DATA_DIR/uploads`), caches (`DATA_DIR/cache`), the Chroma store (`DATA_DIR/vector_db`), the audit log and the licence file (`config.py:174`, `:182`, `:506`; `env.py:271`, `:925`, `:1224`). A legacy `DATA_DIR/config.json` is imported once and renamed `old_config.json` (`config.py:87-91`). In the image the default resolves to `/app/backend/data`, the volume. | `files-uploads-and-storage.md`, `deployment-operations-and-logging.md` *(planned)* |
| `STATIC_DIR` | `backend/open_webui/static` | Path | `env.py:252`; read again and resolved at `config.py:98` | Folder served at `/static` (logos, favicon, splash image) (`main.py:3023`). At import `config.py` removes the files at the top of the folder and copies in the front-end build's `static` files, favicon, splash and loader (`config.py:100-145`). | `local-customisations-uoft-fork.md` *(planned)* |
| `FRONTEND_BUILD_DIR` | `<repository>/build`; under `open-webui serve`, `frontend` inside the package | Path | `env.py:254`, `:257` | The built single-page app served at `/` (`main.py:3066-3075`). If the folder is missing the backend serves only the API and logs a warning (section 10). | `backend-architecture-and-request-lifecycle.md` *(planned)* |
| `FROM_INIT_PY` | `False` | Boolean | `env.py:141`; set to `true` by `__init__.py:40` | Set by `open-webui serve`. Takes the version from the installed package metadata instead of `package.json` and switches the data and front-end defaults to folders inside the package (`env.py:143-151`, `:230-257`). Not meant to be set by hand. | This document, section 4 |
| `DOCKER` | `False`; the image sets `true` (`Dockerfile:229`) | Boolean | `env.py:44` | Tells the ColBERT reranker it runs in the image, which applies a container workaround for its compiled extension (`routers/retrieval.py:201`; `retrieval/models/colbert.py:18-24`). | `rag-retrieval-embeddings-and-vector-stores.md` |
| `USE_SLIM_DOCKER` | `False`; the image passes the `USE_SLIM` build argument (`Dockerfile:79`) | Boolean | `env.py:45` (constant `USE_SLIM`) | Marks the slim image: local model features are off (embeddings, reranking, speech-to-text, tokenization), the default vector store becomes `pgvector`, only SQLite or PostgreSQL, pgvector and local file storage are accepted, and audio preprocessing is skipped (`config.py:503`; `internal/db.py:146-150`; `retrieval/vector/factory.py:20-24`; `storage/provider.py:339-342`; `env.py:857`). `start.sh` skips the Playwright browser install (`backend/start.sh:21`). | `rag-retrieval-embeddings-and-vector-stores.md`, `audio-speech-to-text-and-text-to-speech.md` |
| `USE_CUDA_DOCKER` | `false`; the image passes the `USE_CUDA` build argument (`Dockerfile:78`) | Boolean (compared as text) | `env.py:47`; `__init__.py:52` | When `true` (and not slim), local models run on the GPU if PyTorch finds one; otherwise the code logs an error, sets the variable back to `false` and uses the CPU (`env.py:51-61`). On macOS the Apple GPU (`mps`) is used when available (`env.py:63-69`). `start.sh` and `open-webui serve` extend `LD_LIBRARY_PATH` for the CUDA libraries (`backend/start.sh:61-64`; `__init__.py:52-74`). | `rag-retrieval-embeddings-and-vector-stores.md` |
| `ENV` | `dev`; the image sets `prod` (`Dockerfile:74`) | Text | `env.py:139` | `dev` serves the interactive API documentation and enables a developer-only retrieval route (`main.py:508-509`; `routers/retrieval.py:3320`). In `prod`, an `OLLAMA_BASE_URL` of `/ollama` is rewritten to a container address (`config.py:253-262`). | `backend-architecture-and-request-lifecycle.md` *(planned)*, `model-connections-openai-ollama-and-direct.md` |
| `DEPLOYMENT_ID` | empty | Text | `env.py:154` | Returned with the version number by the version endpoint (`main.py:2586-2591`). | `backend-architecture-and-request-lifecycle.md` *(planned)* |
| `INSTANCE_ID` | a new random identifier per process | Text | `env.py:155` | Stored at start-up (`main.py:360`) and stamped on every published system event, so event consumers can tell workers apart (`events.py:1010-1024`). Unset, each worker gets a different value. | `notifications-webhooks-events-and-banners.md` |
| `WEBUI_NAME` | `MedIT GPT` (fork change; upstream adds " (Open WebUI)") | Text | `env.py:951` | Product name in titles, the sign-in page, notifications and model prompts. Environment-only, so the live name is **TO BE CONFIRMED**. | `admin-settings-panels.md`, `local-customisations-uoft-fork.md` *(planned)* |
| `WEBUI_BUILD_HASH` | `dev-build` | Text | `env.py:958` | Printed as `Commit: {WEBUI_BUILD_HASH}` in the start-up banner when not `dev-build` (`main.py:331`). The image sets `WEBUI_BUILD_VERSION`, not this name (`Dockerfile:228`), and the front end's build hash comes from `APP_BUILD_HASH` at build time (`Dockerfile:45`; `vite.config.ts:26`). | Section 7.15 |

### 7.3 Identity, Sign-In and Security

Columns as in section 7.1, plus **Restart**, which says what a change needs. Three rows (`ENABLE_PASSWORD_AUTH`, `CORS_ALLOW_ORIGIN`, `CORS_ALLOW_CUSTOM_SCHEME`) are read in `config.py` but are environment-only and belong here by purpose; `config.py` rows are cited as `config.py:<line>`.

| Variable | Code default | Type | Read at | Effect | Restart | In depth |
|---|---|---|---|---|---|---|
| `WEBUI_SECRET_KEY` | none in code; set per environment (the start scripts generate one when unset, section 7.13) | Text (secret) | `env.py:762`; `__init__.py:41`, `:50` | Signs sign-in tokens and the session cookie (`utils/auth.py:51`; `main.py:2670`); default for the two OAuth encryption keys below (`env.py:873-875`); used for valves only when `ENABLE_VALVE_ENCRYPTION` is on (`utils/valves.py:14-24`). Empty while `WEBUI_AUTH` is on stops start-up (section 10; `env.py:780-788`). | Yes. Every worker and replica must use the same value; a new value signs everyone out (section 5.4) | `authentication-and-sign-in.md` |
| `WEBUI_JWT_SECRET_KEY` | empty | Text (secret) | `env.py:764` | Deprecated name, used only when `WEBUI_SECRET_KEY` is **absent** from the environment (`env.py:760-765`). Under `start.sh` it does not work on its own: the script skips key generation when this name is set, then starts the server with `WEBUI_SECRET_KEY` set to an empty value (`backend/start.sh:36`, `:107`), so the fallback is never reached and start-up stops (section 11.1). | Yes | Section 4 |
| `WEBUI_SECRET_KEY_LENGTH` | `24` | Integer | `__init__.py:44`; `backend/start.sh:32` | Length in bytes of a newly generated key file. A value below 1 stops `open-webui serve` with `WEBUI_SECRET_KEY_LENGTH must be a positive integer`; a non-numeric value stops it with a Python error; `start.sh` refuses anything that is not a positive whole number with `WEBUI_SECRET_KEY_LENGTH must be a positive integer.` (`__init__.py:43-48`; `backend/start.sh:41-44`). | Only matters when a new key file is generated | Section 7.13 |
| `ENABLE_VALVE_ENCRYPTION` | `False` | Boolean | `env.py:767` | When on, tool and function valves are saved encrypted (`utils/valves.py:21-24`). Values saved encrypted can be read back only while the secret key is unchanged; otherwise the log shows `Failed to decrypt valves: {error}` and the valves read as empty (`utils/valves.py:35-39`). | Yes | `functions-pipes-filters-actions-and-pipelines.md`, `workspace-tools-tool-servers-mcp-and-terminals.md` |
| `WEBUI_SESSION_COOKIE_SAME_SITE` | `lax` | Text | `env.py:769` | SameSite attribute of the `owui-session` cookie used during single sign-on (`main.py:2661`, `:2672`); also the default for `WEBUI_AUTH_COOKIE_SAME_SITE`. | Yes | `sso-oauth-oidc-and-scim.md` |
| `WEBUI_SESSION_COOKIE_SECURE` | `false` | Boolean | `env.py:770`, `:775` | Marks the `owui-session` cookie HTTPS-only (`main.py:2662`, `:2673`); also the default for `WEBUI_AUTH_COOKIE_SECURE`. | Yes | `sso-oauth-oidc-and-scim.md` |
| `WEBUI_AUTH_COOKIE_SAME_SITE` | the value of `WEBUI_SESSION_COOKIE_SAME_SITE` | Text | `env.py:771` | SameSite attribute of the `token` sign-in cookie and the single sign-on cookies (`routers/auths.py:204`, `:286`; `utils/oauth.py:2195`, `:2216`, `:2249`). | Yes | `authentication-and-sign-in.md` |
| `WEBUI_AUTH_COOKIE_SECURE` | the value of `WEBUI_SESSION_COOKIE_SECURE` | Boolean | `env.py:773` | Marks the `token` cookie and the single sign-on cookies HTTPS-only (`routers/auths.py:205`, `:287`; `utils/oauth.py:2196`). | Yes | `authentication-and-sign-in.md` |
| `ENABLE_STAR_SESSIONS_MIDDLEWARE` | `False` | Boolean | `env.py:967` | Keeps the `owui-session` data in Redis (`REDIS_URL`, key prefix `{REDIS_KEY_PREFIX}:session:`) instead of a signed cookie; if that set-up fails, or the switch is off, the signed-cookie session is used (`main.py:2649-2675`). | Yes | `sso-oauth-oidc-and-scim.md` |
| `WEBUI_AUTH` | `True` | Boolean | `env.py:751` | Sign-in required. When off, sign-up is forced off (`config.py:1664`) and the front end skips the sign-in form (`src/routes/auth/+page.svelte:199`); the code refuses this mode once users exist, with `EXISTING_USERS` (section 10; `routers/auths.py:788-801`). Running without sign-in is security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca). | Yes | `authentication-and-sign-in.md` |
| `ENABLE_PASSWORD_AUTH` | `True` | Boolean | `config.py:1670` | Server-side switch for email-and-password and LDAP sign-in; when off both answer HTTP 403 `ACTION_PROHIBITED` (`routers/auths.py:486-490`, `:724-728`). The admin "login form" setting only hides the form (ground truth). | Yes | `authentication-and-sign-in.md` |
| `ENABLE_INITIAL_ADMIN_SIGNUP` | `False` | Boolean | `env.py:753` | Lets the very first account be created through sign-up even when the login form is switched off (`routers/auths.py:912-914`). | Yes | `authentication-and-sign-in.md` |
| `ENABLE_SIGNUP_PASSWORD_CONFIRMATION` | `False` | Boolean | `env.py:754` | Adds a confirm-password field to the sign-up form (`main.py:2332`; `src/routes/auth/+page.svelte:83`, `:367`). | Yes | `authentication-and-sign-in.md` |
| `WEBUI_ADMIN_EMAIL` | empty | Text (personal data) | `env.py:798` | With `WEBUI_ADMIN_PASSWORD`, creates an admin at start-up when no users exist, then turns sign-up off (`main.py:377-380`; section 5.5). | Read at every start-up; acts only on an empty user table | `authentication-and-sign-in.md` |
| `WEBUI_ADMIN_PASSWORD` | empty; set per environment | Text (secret) | `env.py:799` | Password for the bootstrapped admin above. | As above | `authentication-and-sign-in.md` |
| `WEBUI_ADMIN_NAME` | `Admin` | Text | `env.py:800` | Display name of the bootstrapped admin. | As above | `authentication-and-sign-in.md` |
| `ENABLE_PASSWORD_VALIDATION` | `False` | Boolean | `env.py:814` | Checks new passwords against `PASSWORD_VALIDATION_REGEX_PATTERN` (`utils/auth.py:197-199`). | Yes | `authentication-and-sign-in.md` |
| `PASSWORD_VALIDATION_REGEX_PATTERN` | at least eight characters with a lower-case letter, an upper-case letter, a digit and a symbol | Text (regular expression) | `env.py:816` | The rule above. A pattern that does not compile is logged (`Invalid PASSWORD_VALIDATION_REGEX_PATTERN: {e}`) and the default is used (`env.py:822-827`). | Yes | `authentication-and-sign-in.md` |
| `PASSWORD_VALIDATION_HINT` | empty | Text | `env.py:829` | Message shown when a password fails the rule; empty shows `The password does not meet the required validation criteria.` (`utils/auth.py:199`; `constants.py:114`). | Yes | `error-messages-backend-identity-admin-and-platform.md` |
| `PASSWORD_HASH_ALGORITHM` | `bcrypt` | Text (`bcrypt` or `argon2`) | `env.py:815` | Algorithm for new password hashes (`utils/auth.py:177-187`). With `bcrypt`, passwords over 72 bytes are refused (`utils/auth.py:190-195`). Any other value makes every new password fail with `Unsupported PASSWORD_HASH_ALGORITHM: {PASSWORD_HASH_ALGORITHM}` (`utils/auth.py:187`); start-up does not check it. | Yes | `authentication-and-sign-in.md` |
| `WEBUI_AUTH_TRUSTED_EMAIL_HEADER` | unset | Text (header name) | `env.py:802` | Trusted-header sign-in: the email is taken from this request header set by a reverse proxy; a request without it is refused with `INVALID_TRUSTED_HEADER` (`routers/auths.py:732-737`); password changes are refused (`routers/auths.py:393-395`). Also reported to the front end as `auth_trusted_header` (`main.py:2331`). | Yes | `sso-oauth-oidc-and-scim.md` |
| `WEBUI_AUTH_TRUSTED_NAME_HEADER` | unset | Text (header name) | `env.py:803` | Display name header for trusted-header sign-in (`routers/auths.py:740-745`). | Yes | `sso-oauth-oidc-and-scim.md` |
| `WEBUI_AUTH_TRUSTED_GROUPS_HEADER` | unset | Text (header name) | `env.py:804` | Comma-separated group names for trusted-header sign-in; group membership is synchronized from it (`routers/auths.py:763-768`; ground truth, "Group sync replaces membership"). | Yes | `users-groups-roles-and-permissions.md` |
| `WEBUI_AUTH_TRUSTED_ROLE_HEADER` | unset | Text (header name) | `env.py:805` | Role header for trusted-header sign-in; an unknown value is logged as `Ignoring invalid trusted role header value: {trusted_role}` (`routers/auths.py:770-786`). | Yes | `users-groups-roles-and-permissions.md` |
| `CUSTOM_API_KEY_HEADER` | `x-api-key` | Text (header name) | `env.py:812` | Extra request header checked for a user API key when there is no `Authorization` header or `token` cookie (`utils/asgi_middleware.py:127-130`). | Yes | `public-api-and-integrations.md` *(planned)* |
| `WEBUI_AUTH_SIGNOUT_REDIRECT_URL` | unset | Text (URL) | `env.py:864` | Where the browser goes after sign-out; also passed to the identity provider's logout page after single sign-on (`routers/auths.py:1028-1033`, `:1049-1056`). | Yes | `sso-oauth-oidc-and-scim.md` |
| `ENABLE_OAUTH_EMAIL_FALLBACK` | `False` | Boolean | `env.py:869` | When the provider sends no email, builds a placeholder address from the provider name and subject instead of refusing the sign-in (`utils/oauth.py:1995-1999`). | Yes | `sso-oauth-oidc-and-scim.md` |
| `ENABLE_OAUTH_ID_TOKEN_COOKIE` | `True` | Boolean | `env.py:871` | Sets the legacy `oauth_id_token` cookie after single sign-on (`utils/oauth.py:2210-2219`). | Yes | `sso-oauth-oidc-and-scim.md` |
| `OAUTH_CLIENT_INFO_ENCRYPTION_KEY` | the value of `WEBUI_SECRET_KEY`; set per environment | Text (secret) | `env.py:873` | Protects stored OAuth client registrations for tool servers (`utils/oauth.py:252-259`). Details are security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca). | Yes; must match on every worker | `sso-oauth-oidc-and-scim.md` |
| `OAUTH_SESSION_TOKEN_ENCRYPTION_KEY` | the value of `WEBUI_SECRET_KEY`; set per environment | Text (secret) | `env.py:875` | Protects stored provider tokens in `oauth_session` rows (`models/oauth_sessions.py:68-70`). Security-sensitive as above. | Yes; must match on every worker | `sso-oauth-oidc-and-scim.md` |
| `OAUTH_MAX_SESSIONS_PER_USER` | `10` | Integer, exits if invalid | `env.py:879` | Stored single sign-on sessions kept per user and provider; older ones are deleted at the next sign-in (`utils/oauth.py:2233-2235`). | Yes | `sso-oauth-oidc-and-scim.md` |
| `ENABLE_OAUTH_TOKEN_EXCHANGE` | `False` | Boolean | `env.py:883` | Enables the endpoint that exchanges a provider token for a MedIT GPT token (`routers/auths.py:1634-1636`). | Yes | `sso-oauth-oidc-and-scim.md` |
| `OAUTH_TOKEN_EXCHANGE_RATE_LIMIT` | unset (no limit) | Integer or `none`, exits if invalid | `env.py:884-889` | Requests allowed per window on the token-exchange endpoint (`routers/auths.py:94-101`). | Yes | `sso-oauth-oidc-and-scim.md` |
| `OAUTH_TOKEN_EXCHANGE_RATE_LIMIT_WINDOW` | `180` (seconds) | Integer, exits if invalid | `env.py:890` | Window for the limit above (`routers/auths.py:97`). | Yes | `sso-oauth-oidc-and-scim.md` |
| `OAUTH_TOKEN_EXCHANGE_TRUSTED_CLIENT_IDS` | empty | List | `env.py:891-895` | When set, only tokens issued to these client ids are exchanged (`routers/auths.py:1667-1674`). | Yes | `sso-oauth-oidc-and-scim.md` |
| `ENABLE_OAUTH_BACKCHANNEL_LOGOUT` | `False` | Boolean | `env.py:901` | Enables `POST /oauth/backchannel-logout` for provider-initiated sign-out; when off the route answers 404 (`main.py:2858-2864`). It revokes tokens only where Redis is configured (`env.py:897-900`; ground truth). | Yes | `sso-oauth-oidc-and-scim.md` |
| `ENABLE_SCIM` | `False` (falls back to `SCIM_ENABLED`) | Boolean | `env.py:907` | Mounts the SCIM provisioning API at `/api/v1/scim/v2` (`main.py:886`). Without `SCIM_AUTH_PROVIDER` a start-up warning is logged (section 10; `env.py:911-916`). | Yes | `sso-oauth-oidc-and-scim.md` |
| `SCIM_ENABLED` | `False` | Boolean | `env.py:907` | Older name for `ENABLE_SCIM`, read only when `ENABLE_SCIM` is unset. | Yes | `sso-oauth-oidc-and-scim.md` |
| `SCIM_TOKEN` | empty; set per environment | Text (secret) | `env.py:908` | Bearer token the identity provider presents to the SCIM API (`main.py:604`; `routers/scim.py:270`). | Yes | `sso-oauth-oidc-and-scim.md` |
| `SCIM_AUTH_PROVIDER` | empty | Text (provider name) | `env.py:909` | Which single sign-on provider SCIM identities belong to; required for SCIM requests that store external ids (`routers/scim.py:309-316`). | Yes | `sso-oauth-oidc-and-scim.md` |
| `ENABLE_ADMIN_CHAT_ACCESS` | `True` | Boolean | `env.py:371` | Admins can open other users' chats (`models/chats.py:1767`; `routers/chats.py:116`, `:748`, `:1228`, `:1846`); also reported to the front end (`main.py:2374`; `src/lib/components/admin/Users/UserList.svelte:405`). | Yes | `users-groups-roles-and-permissions.md` |
| `BYPASS_MODEL_ACCESS_CONTROL` | `False` | Boolean | `env.py:832` | Turns model access control off for everyone (`main.py:1150`; `routers/models.py:785`; `routers/ollama.py:502`). | Yes | `workspace-models-and-model-access.md` |
| `BYPASS_RETRIEVAL_ACCESS_CONTROL` | `False` | Boolean | `env.py:833` | Skips the access checks on vector-store collections during retrieval (`retrieval/utils.py:1548`, `:1624`, `:1649`, `:1657`). | Yes | `rag-retrieval-embeddings-and-vector-stores.md` |
| `ENABLE_RETRIEVAL_UNSCOPED_COLLECTIONS` | `False` | Boolean | `env.py:839` | Lets non-admins query collection names that match no known file, memory, web-search or knowledge collection; off, such names are denied (`env.py:835-839`; `retrieval/utils.py:1354-1359`). | Yes | `knowledge-bases.md` |
| `DEFAULT_GROUP_SHARE_PERMISSION` | `members` | Text (`true`, `false` or `members`) | `env.py:1026` | Default "who can share to this group" for new groups: anyone, no one, or members only (`env.py:1024-1027`; `models/groups.py:137-145`, `:492-501`). Any value other than `true` or `members` means no one. | Yes; existing groups keep their setting | `users-groups-roles-and-permissions.md` |
| `ENABLE_FORWARD_USER_INFO_HEADERS` | `False` | Boolean | `env.py:989` | Sends the signed-in user's name, id, email and role (personal data) to model providers, tool servers and other external services with each request (`utils/headers.py:52-82`; `routers/openai.py:179-182`; `utils/tools.py:175-181`). | Yes | `model-connections-openai-ollama-and-direct.md` |
| `FORWARD_USER_INFO_HEADER_USER_NAME` | `X-OpenWebUI-User-Name` | Text (header name) | `env.py:991` | Header carrying the user's name when forwarding is on (`utils/headers.py:78`). | Yes | `model-connections-openai-ollama-and-direct.md` |
| `FORWARD_USER_INFO_HEADER_USER_ID` | `X-OpenWebUI-User-Id` | Text (header name) | `env.py:992` | Header carrying the user id (`utils/headers.py:79`). | Yes | As above |
| `FORWARD_USER_INFO_HEADER_USER_EMAIL` | `X-OpenWebUI-User-Email` | Text (header name) | `env.py:993` | Header carrying the email address (`utils/headers.py:80`). | Yes | As above |
| `FORWARD_USER_INFO_HEADER_USER_ROLE` | `X-OpenWebUI-User-Role` | Text (header name) | `env.py:994` | Header carrying the role (`utils/headers.py:81`). | Yes | As above |
| `FORWARD_USER_INFO_HEADER_AUTH_TYPE` | `X-OpenWebUI-Auth-Type` | Text (header name) | `env.py:995` | Header saying whether the incoming request used an API key or a sign-in token (`utils/headers.py:62-64`). | Yes | As above |
| `FORWARD_SESSION_INFO_HEADER_MESSAGE_ID` | `X-OpenWebUI-Message-Id` | Text (header name) | `env.py:996` | Header carrying the message id, sent to tool servers when forwarding is on (`utils/tools.py:181-182`). | Yes | `workspace-tools-tool-servers-mcp-and-terminals.md` |
| `FORWARD_SESSION_INFO_HEADER_CHAT_ID` | `X-OpenWebUI-Chat-Id` | Text (header name) | `env.py:997` | Header carrying the chat id (`routers/openai.py:181-182`; `routers/ollama.py:125`; `utils/tools.py:179-180`). The external web-search engine sends it, with the user headers, whenever it has a user (`retrieval/web/external.py:30-34`). | Yes | `web-search-and-web-loading.md` |
| `FORWARD_USER_INFO_HEADER_JWT_SECRET` | unset; set per environment | Text (secret) | `env.py:1001` | When set, the user details are sent as one signed token in the header below instead of separate headers (`utils/headers.py:66-73`). | Yes | `model-connections-openai-ollama-and-direct.md` |
| `FORWARD_USER_INFO_HEADER_JWT` | `X-OpenWebUI-User-Jwt` | Text (header name) | `env.py:1002` | Header that carries the signed token (`utils/headers.py:69`). | Yes | As above |
| `FORWARD_USER_INFO_HEADER_JWT_EXPIRES_SECONDS` | `300` | Integer, silent fallback | `env.py:1005` | Lifetime of that token (`utils/headers.py:47`). | Yes | As above |
| `TRUSTED_SIGNATURE_KEY` | empty; set per environment | Text (secret) | `env.py:959` | Key for a signature-check helper (`utils/auth.py:60-73`) that nothing in v0.11.4 calls (searched `backend/` for callers; section 14). | Yes | Section 14 |
| `CORS_ALLOW_ORIGIN` | `*` | List, **semicolon**-separated | `config.py:2134` | Origins the browser may call the API from (`main.py:831-837`). `*` logs a start-up warning; an origin without `http`, `https` or an allowed custom scheme, or without a host, stops start-up (section 10; `config.py:2114-2151`). `backend/dev.sh` sets the two local development origins (`backend/dev.sh:1`). | Yes | `backend-architecture-and-request-lifecycle.md` *(planned)* |
| `CORS_ALLOW_CUSTOM_SCHEME` | empty | List, semicolon-separated | `config.py:2139` | Extra URL schemes (for example a desktop client's `app`) accepted in `CORS_ALLOW_ORIGIN` (`config.py:2118`). | Yes | As above |
| `CACHE_CONTROL` | unset (no header) | Text (header value) | `utils/security_headers.py:36`, `:53` | Sets `Cache-Control` on the application's HTTP responses (`utils/asgi_middleware.py:134-141`); a value outside the allowed directives becomes `no-store, max-age=0` (`utils/security_headers.py:99-105`). The 14 header variables in this table are read once per worker when the middleware is built (`utils/asgi_middleware.py:93-95`). | Yes | `backend-architecture-and-request-lifecycle.md` *(planned)* |
| `HSTS` | unset | Text | `utils/security_headers.py:37` | `Strict-Transport-Security`; an invalid value becomes `max-age=31536000;includeSubDomains` (`utils/security_headers.py:63-68`). | Yes | As above |
| `PERMISSIONS_POLICY` | unset | Text | `utils/security_headers.py:38` | `Permissions-Policy`; an invalid value becomes `none` (`utils/security_headers.py:81-86`). | Yes | As above |
| `REFERRER_POLICY` | unset | Text | `utils/security_headers.py:39` | `Referrer-Policy`; an invalid value becomes `no-referrer` (`utils/security_headers.py:90-95`). | Yes | As above |
| `XCONTENT_TYPE` | unset | Text | `utils/security_headers.py:40` | `X-Content-Type-Options`, always sent as `nosniff` when set (`utils/security_headers.py:116-119`). | Yes | As above |
| `XDOWNLOAD_OPTIONS` | unset | Text | `utils/security_headers.py:41` | `X-Download-Options`, always sent as `noopen` when set (`utils/security_headers.py:109-112`). | Yes | As above |
| `XFRAME_OPTIONS` | unset | Text | `utils/security_headers.py:42` | `X-Frame-Options`: `DENY` or `SAMEORIGIN`; anything else becomes `DENY` (`utils/security_headers.py:72-77`). | Yes | As above |
| `XPERMITTED_CROSS_DOMAIN_POLICIES` | unset | Text | `utils/security_headers.py:43` | `X-Permitted-Cross-Domain-Policies`; an invalid value becomes `none` (`utils/security_headers.py:123-128`). | Yes | As above |
| `CONTENT_SECURITY_POLICY` | unset | Text | `utils/security_headers.py:44` | `Content-Security-Policy`, sent as given without checking (`utils/security_headers.py:132-133`). A strict policy can break the interface; test before production. | Yes | As above |
| `CONTENT_SECURITY_POLICY_REPORT_ONLY` | unset | Text | `utils/security_headers.py:45` | `Content-Security-Policy-Report-Only`, sent as given (`utils/security_headers.py:137-138`). | Yes | As above |
| `CROSS_ORIGIN_EMBEDDER_POLICY` | unset | Text | `utils/security_headers.py:46` | `Cross-Origin-Embedder-Policy`; an invalid value becomes `require-corp` (`utils/security_headers.py:142-147`). | Yes | As above |
| `CROSS_ORIGIN_OPENER_POLICY` | unset | Text | `utils/security_headers.py:47` | `Cross-Origin-Opener-Policy`; an invalid value becomes `same-origin` (`utils/security_headers.py:151-156`). | Yes | As above |
| `CROSS_ORIGIN_RESOURCE_POLICY` | unset | Text | `utils/security_headers.py:48` | `Cross-Origin-Resource-Policy`; an invalid value becomes `same-origin` (`utils/security_headers.py:160-165`). | Yes | As above |
| `REPORTING_ENDPOINTS` | unset | Text | `utils/security_headers.py:49` | `Reporting-Endpoints`, sent as given (`utils/security_headers.py:169-170`). | Yes | As above |

### 7.4 Database

The relational database holds users, chats and the persistent settings, so every row here changes where the application's data lives or how it is reached. All workers and replicas must point at the same database (section 5.2).

| Variable | Code default | Type | Read at | Effect | Restart | In depth |
|---|---|---|---|---|---|---|
| `DATABASE_URL` | `sqlite:///{DATA_DIR}/webui.db`; set per environment | Text (connection URL; may embed a password) | `env.py:271`, `:295` | The database to use. `postgres://` is rewritten to `postgresql://` (`env.py:300-301`). The value is replaced when the parts below are all set (`env.py:291-294`). The runtime engine supports SQLite and PostgreSQL; a `sqlite+sqlcipher://` URL stops start-up in v0.11.4 (ground truth; section 10). The slim image accepts only SQLite or PostgreSQL (`internal/db.py:146-150`). Also the default connection for the `pgvector` and `opengauss` vector stores (`config.py:648`, `:749`). | Yes; all workers and replicas must agree | `database-schema-identity-chats-and-config.md` *(planned)* |
| `DATABASE_TYPE` | unset | Text (URL scheme, for example `postgresql`) | `env.py:273` | First part of a URL composed from parts. When `DATABASE_TYPE`, `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME` and a user or password are **all** set, the composed URL `{type}://{user}:{password}@{host}:{port}/{name}` replaces `DATABASE_URL`, even when `DATABASE_URL` is also set (`env.py:283-294`). `sqlite+sqlcipher` with no `DATABASE_URL` selects an encrypted file at `DATA_DIR/webui.db` (`env.py:295-297`), which v0.11.4 cannot open (ground truth). | Yes | As above |
| `DATABASE_USER` | unset | Text | `env.py:274` | User part of the composed URL (`env.py:277-279`). | Yes | As above |
| `DATABASE_PASSWORD` | unset; set per environment | Text (secret) | `env.py:275`; `internal/db.py:290` | Password part of the composed URL (`env.py:280-281`); also required for a `sqlite+sqlcipher://` URL, otherwise start-up stops (`internal/db.py:289-292`). | Yes | As above |
| `DATABASE_HOST` | unset | Text | `env.py:286` | Host part of the composed URL. | Yes | As above |
| `DATABASE_PORT` | unset | Text | `env.py:287` | Port part of the composed URL. | Yes | As above |
| `DATABASE_NAME` | unset | Text | `env.py:288` | Database-name part of the composed URL. | Yes | As above |
| `DATABASE_SCHEMA` | unset (the database's default schema) | Text | `env.py:303` | Schema the application's tables belong to, for PostgreSQL deployments that do not use the default schema (`internal/db.py:423-424`). | Yes; changing it points the application at different tables | As above |
| `DATABASE_ENABLE_IAM_TOKEN_AUTH` | `False` | Boolean | `env.py:304` | PostgreSQL on Amazon RDS: connects with a short-lived token from the cloud provider instead of a stored password, refreshed after 14 minutes (`internal/db.py:165-202`, `:418`, `:497`). Needs a PostgreSQL URL with a host and user, and the standard image, otherwise start-up stops (section 10; `internal/db.py:151-154`, `:170-173`). | Yes | As above |
| `DATABASE_POOL_SIZE` | unset (SQLAlchemy's default pool) | Integer, silent fallback | `env.py:306-310` | Connection-pool size per worker. PostgreSQL: a positive value sets a fixed pool, `0` or a negative value turns pooling off (`internal/db.py:402-416`, `:475-495`). SQLite: the runtime pool is this value when positive, otherwise 512 (`internal/db.py:462`). | Yes | As above |
| `DATABASE_POOL_MAX_OVERFLOW` | `0` | Integer, silent fallback | `env.py:312-316` | Extra connections allowed above the pool size, applied only when `DATABASE_POOL_SIZE` is positive and the database is not SQLite (`internal/db.py:404-412`, `:477-484`). | Yes | As above |
| `DATABASE_POOL_TIMEOUT` | `30` (seconds) | Integer, silent fallback | `env.py:318-322` | How long a request waits for a free pooled connection (`internal/db.py:408`, `:467`, `:481`). | Yes | As above |
| `DATABASE_POOL_RECYCLE` | `3600` (seconds) | Integer, silent fallback | `env.py:324-328` | Age after which a pooled connection is replaced (`internal/db.py:409`, `:468`, `:482`). | Yes | As above |
| `DATABASE_ENABLE_SESSION_SHARING` | `False` | Boolean | `env.py:366` | When on, repository calls reuse the session the request already holds instead of opening a new one (`internal/db.py:528-535`). | Yes | As above |
| `DATABASE_ENABLE_SQLITE_WAL` | `True` | Boolean | `env.py:330` | SQLite journal mode: WAL when on, DELETE when off (`internal/db.py:377-380`). | Yes | As above |
| `DATABASE_SQLITE_PRAGMA_SYNCHRONOUS` | `NORMAL` | Text | `env.py:338` | SQLite `synchronous` setting on every new connection; an empty value skips it (`env.py:332-338`; `internal/db.py:382-384`). | Yes | As above |
| `DATABASE_SQLITE_PRAGMA_BUSY_TIMEOUT` | `5000` (milliseconds) | Text (number) | `env.py:342` | How long a SQLite connection waits for a write lock before failing (`internal/db.py:385-386`). | Yes | As above |
| `DATABASE_SQLITE_PRAGMA_CACHE_SIZE` | `-65536` (about 64 MB) | Text (number) | `env.py:345` | SQLite page cache size (`env.py:344`; `internal/db.py:387-388`). | Yes | As above |
| `DATABASE_SQLITE_PRAGMA_TEMP_STORE` | `MEMORY` | Text | `env.py:349` | Where SQLite keeps temporary tables (`internal/db.py:389-390`). | Yes | As above |
| `DATABASE_SQLITE_PRAGMA_MMAP_SIZE` | `268435456` (about 256 MB) | Text (number) | `env.py:353` | SQLite memory-mapped input and output size; `0` turns it off (`env.py:351-353`; `internal/db.py:391-392`). | Yes | As above |
| `DATABASE_SQLITE_PRAGMA_JOURNAL_SIZE_LIMIT` | `67108864` (about 64 MB) | Text (number) | `env.py:358` | Caps the WAL file size after a checkpoint; `-1` means no limit (`env.py:355-358`; `internal/db.py:393-394`). | Yes | As above |
| `DATABASE_USER_ACTIVE_STATUS_UPDATE_INTERVAL` | `60` (seconds) | Number, silent fallback | `env.py:361-364` | Minimum gap between "last active" writes for one user in one worker; `0` or less writes on every call (`models/users.py:771-775`; `utils/misc.py:1158-1170`). The code comment advises staying under the 180-second active-user window (`env.py:360`). | Yes | `users-groups-roles-and-permissions.md` |
| `ENABLE_DB_MIGRATIONS` | `True` | Boolean | `env.py:157` | Runs the Alembic migrations when `config.py` is imported, in every process (`config.py:81-82`; CLAUDE.md). With several instances, leave it on for one only (section 5.2). | Yes | `database-schema-identity-chats-and-config.md` *(planned)* |
| `RESET_CONFIG_ON_START` | `False` | Boolean | `env.py:368` | Wipes the `config` table at every start-up, so every persistent setting returns to its environment-derived default and admin edits are lost (`main.py:363-364`; section 5.3). | Yes; acts at every start while on | `admin-settings-panels.md` |

### 7.5 Redis and Websockets

Redis is optional. Without it each worker keeps its own task list, websocket session pool, usage pool and sign-in rate-limit counters, and sign-out does not revoke tokens (ground truth). More than one worker or replica needs `WEBSOCKET_MANAGER=redis` plus `REDIS_URL` (CLAUDE.md, "Deployment").

| Variable | Code default | Type | Read at | Effect | Restart | In depth |
|---|---|---|---|---|---|---|
| `REDIS_URL` | empty (no Redis) | Text (connection URL; may embed a password) | `env.py:381` | Redis for task tracking, token revocation, the shared model cache, Redis-backed sessions and, by default, websockets (`utils/redis.py:88-104`; `env.py:493`). If the connection cannot be set up the code carries on without Redis and logs only at debug level (`utils/redis.py:102-104`). Once a client exists, `/ready` answers 503 `Redis not ready` while Redis is unreachable (`main.py:2992-3004`). | Yes; all workers and replicas must agree | `websockets-realtime-and-redis.md` *(planned)* |
| `REDIS_CLUSTER` | `False` | Boolean | `env.py:382` | Treats `REDIS_URL` as a Redis Cluster (`utils/redis.py:100`); the default for `WEBSOCKET_REDIS_CLUSTER`. | Yes | As above |
| `REDIS_KEY_PREFIX` | `open-webui` | Text | `env.py:384` | Prefix of every key the application writes, for example `{REDIS_KEY_PREFIX}:session_pool`, `:usage_pool`, `:models` and `:ydoc:documents` (`socket/main.py:144-196`; `routers/openai.py:81`). Two deployments sharing one Redis need different prefixes. | Yes; a change orphans the old keys | As above |
| `REDIS_SENTINEL_HOSTS` | empty | List (comma-separated host names) | `env.py:399` | Redis Sentinel hosts; when set, the master named in `REDIS_URL` is found through them (`utils/redis.py:59-67`, `:93`). | Yes | As above |
| `REDIS_SENTINEL_PORT` | `26379` | Text (port number) | `env.py:400` | Port for every Sentinel host (`utils/redis.py:66`). A non-numeric value fails when Sentinel hosts are set. | Yes | As above |
| `REDIS_SENTINEL_MAX_RETRY_COUNT` | `2` | Integer, silent fallback (values below 1 become 2) | `env.py:403-409` | Attempts per Redis operation during a Sentinel fail-over; when exhausted the log shows `Redis operation failed after {REDIS_SENTINEL_MAX_RETRY_COUNT} retries: {exc}` (`utils/redis.py:155-174`). | Yes | As above |
| `REDIS_SOCKET_CONNECT_TIMEOUT` | unset | Number (seconds), silent fallback | `env.py:412-416` | Connection timeout for Redis clients, including the websocket manager's (`utils/redis.py:259-260`; `env.py:483-484`). | Yes | As above |
| `REDIS_SOCKET_TIMEOUT` | unset | Number (seconds), silent fallback | `env.py:418-422` | Read and write timeout for Redis commands (`utils/redis.py:261-262`). | Yes | As above |
| `REDIS_SOCKET_KEEPALIVE` | `False` | Boolean | `env.py:429` | TCP keep-alive on Redis sockets, so connections silently dropped by a firewall are detected (`env.py:424-429`; `utils/redis.py:263-264`). | Yes | As above |
| `REDIS_HEALTH_CHECK_INTERVAL` | unset | Integer (seconds), silent fallback | `env.py:437-443` | How often an idle pooled Redis connection is checked before reuse; `0` or less turns it off (`env.py:431-443`; `utils/redis.py:265-266`). | Yes | As above |
| `REDIS_RECONNECT_DELAY` | unset | Number (**milliseconds**), silent fallback | `env.py:445-455` | Pause between Sentinel fail-over retries (`utils/redis.py:195-196`, `:220-221`, `:242-243`). | Yes | As above |
| `REDIS_RESPONSE_STREAM_TTL` | `3600` (seconds) | Integer, silent fallback | `env.py:386-389` | How long a partly streamed answer is kept in Redis for reconnecting browsers; `0` keeps it until the task ends (`tasks.py:217-221`). | Yes | `chat-completion-pipeline-and-generation-tasks.md` |
| `REDIS_TASK_TTL` | `300` (seconds) | Integer, silent fallback (1 to 59 become 300) | `env.py:391-397` | Seconds a generation task survives in Redis without a heartbeat; the heartbeat loop renews it every quarter of this value; `0` disables expiry and the heartbeat (`main.py:394-395`; `tasks.py:69-80`, `:90`, `:113`; section 8). | Yes | As above |
| `ENABLE_WEBSOCKET_SUPPORT` | `True` | Boolean | `env.py:473` | Websocket transport for the live connection; off, the browser falls back to HTTP long-polling (`socket/main.py:102-103`, `:117-118`; `main.py:2336`; `src/routes/+layout.svelte:1277`). | Yes | `websockets-realtime-and-redis.md` *(planned)* |
| `WEBSOCKET_MANAGER` | empty (in-process) | Text (`redis`) | `env.py:476` | `redis` shares websocket rooms, the session and usage pools and the model list across workers and starts the Redis event listener (`socket/main.py:89-109`, `:133-185`; `main.py:397-398`). Anything else keeps them per worker. | Yes; all workers and replicas must agree | As above |
| `WEBSOCKET_REDIS_URL` | the value of `REDIS_URL` | Text (connection URL) | `env.py:493` | Redis used by the websocket manager and the shared pools (`socket/main.py:89-96`, `:136-179`). | Yes | As above |
| `WEBSOCKET_REDIS_CLUSTER` | the value of `REDIS_CLUSTER` | Boolean | `env.py:494` | Cluster mode for the websocket Redis (`socket/main.py:139-179`). | Yes | As above |
| `WEBSOCKET_REDIS_OPTIONS` | empty, meaning no read timeout plus `REDIS_SOCKET_CONNECT_TIMEOUT` when set | JSON | `env.py:478-491` | Extra options for the websocket manager's Redis client (`socket/main.py:96`). Invalid JSON logs `Invalid WEBSOCKET_REDIS_OPTIONS, defaulting to socket_timeout=None` and uses the default. | Yes | As above |
| `WEBSOCKET_REDIS_LOCK_TIMEOUT` | `60` (seconds) | Integer, silent fallback | `env.py:496-501` | Lifetime of the Redis locks that let only one worker run each pool clean-up; also sets the retry delay of those loops (`socket/main.py:163-178`, `:212-215`, `:267`; section 8). | Yes | As above |
| `WEBSOCKET_SENTINEL_HOSTS` | empty | List (comma-separated) | `env.py:503` | Sentinel hosts for the websocket Redis (`socket/main.py:90-94`, `:135`). | Yes | As above |
| `WEBSOCKET_SENTINEL_PORT` | `26379` | Text (port number) | `env.py:504` | Port for those Sentinel hosts. | Yes | As above |
| `WEBSOCKET_SERVER_PING_INTERVAL` | `25` (seconds) | Integer, silent fallback | `env.py:519-523` | How often the server pings each browser connection (`socket/main.py:107`, `:121`). | Yes | As above |
| `WEBSOCKET_SERVER_PING_TIMEOUT` | `20` (seconds) | Integer, silent fallback | `env.py:513-517` | How long the server waits for a ping reply before dropping the connection (`socket/main.py:108`, `:122`). | Yes | As above |
| `WEBSOCKET_HEARTBEAT_INTERVAL` | unset | Integer (seconds), clamped to 5 to 90; a non-number becomes 30 | `env.py:525-532` | Heartbeat interval sent to the front end (`main.py:2337-2341`); also sets how long an entry may go unseen before the session pool reaps it: four intervals, at least 120 seconds (`socket/main.py:129`). | Yes | As above |
| `WEBSOCKET_EVENT_CALLER_TIMEOUT` | unset (the socket library's default) | Integer (seconds); a non-number becomes 300 | `env.py:534-542` | How long the server waits for the browser to answer a request for input (`socket/main.py:1268-1282`); on time-out the caller receives `Event call timed out. The browser tab may be inactive or closed.` | Yes | `builtin-native-tools.md` |

### 7.6 Logging and Audit

Application logs go to standard output only (ground truth). The audit log is separate and off by default; when on it records user details, source IP addresses, user agents and (from level `REQUEST`) request bodies, so it is personal data and must be handled with care (CLAUDE.md, "Deployment"; `utils/logger.py:139-165`).

| Variable | Code default | Type | Read at | Effect | Restart | In depth |
|---|---|---|---|---|---|---|
| `GLOBAL_LOG_LEVEL` | `INFO` (an empty or unrecognized value becomes `INFO` without a message) | Text (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) | `env.py:113-124` | Level of the application log and of the uvicorn loggers (`utils/logger.py:182-196`, `:211-221`). `DEBUG` is verbose and can include request details. | Yes | `deployment-operations-and-logging.md` *(planned)* |
| `LOG_FORMAT` | empty (coloured text lines) | Text (`json`) | `env.py:110` | `json` writes one JSON object per line for log collectors (`utils/logger.py:50-90`, `:182-188`; `env.py:116-119`), also for the migration runner (`migrations/env.py:19-22`), and skips the ASCII start-up banner (`main.py:320`). | Yes | As above |
| `LOGURU_DIAGNOSE` | `False` | Boolean | `env.py:111` | Adds the values of local variables to logged tracebacks (`utils/logger.py:187`, `:195`, `:206`). Those values can include personal data or secrets; keep it off outside diagnosis. | Yes | As above |
| `WEBSOCKET_SERVER_LOGGING` | `False` | Boolean | `env.py:505` | Logging from the Socket.IO server (`socket/main.py:106`, `:120`). | Yes | `websockets-realtime-and-redis.md` *(planned)* |
| `WEBSOCKET_SERVER_ENGINEIO_LOGGING` | the value of `WEBSOCKET_SERVER_LOGGING` | Boolean | `env.py:506-512` | Logging from the underlying Engine.IO transport (`socket/main.py:109`, `:123`). | Yes | As above |
| `AUDIT_LOG_LEVEL` | `NONE` | Text (`NONE`, `METADATA`, `REQUEST`, `REQUEST_RESPONSE`) | `env.py:1234` | Turns the audit middleware on and sets how much it records (`utils/audit.py:53-57`; `main.py:796-813`). An unknown value logs `Invalid audit level: {AUDIT_LOG_LEVEL}. Error: {e}` and auditing stays off (`main.py:797-800`). | Yes | `deployment-operations-and-logging.md` *(planned)* |
| `ENABLE_AUDIT_LOGS_FILE` | `True` | Boolean | `env.py:1219` | Writes audit entries to `AUDIT_LOGS_FILE_PATH` when `AUDIT_LOG_LEVEL` is not `NONE`; if the file cannot be opened the log shows `Failed to initialize audit log file handler: {str(e)}` (`utils/logger.py:197-209`). | Yes | As above |
| `AUDIT_LOGS_FILE_PATH` | `{DATA_DIR}/audit.log` | Path (full file path) | `env.py:1224` | Audit log file (`env.py:1221-1224`; `utils/logger.py:199-200`). | Yes | As above |
| `AUDIT_LOG_FILE_ROTATION_SIZE` | `10MB` | Text (size) | `env.py:1226` | Size at which the audit file is rotated; rotated files are compressed to zip (`utils/logger.py:202-203`). Retention of rotated files is not configured in code. | Yes | As above |
| `ENABLE_AUDIT_STDOUT` | `False` | Boolean | `env.py:1218` | Also prints audit entries in the ordinary log (`utils/logger.py:181`). | Yes | As above |
| `AUDIT_UVICORN_LOGGER_NAMES` | `uvicorn.access` | List (comma-separated logger names) | `env.py:1231` | Server loggers whose lines are routed into the application log at `GLOBAL_LOG_LEVEL` (`utils/logger.py:218-221`). | Yes | As above |
| `MAX_BODY_LOG_SIZE` | `2048` (bytes) | Integer, silent fallback | `env.py:1235-1238` | Maximum request and response body captured per audit entry (`utils/audit.py:101-113`; `main.py:812`). | Yes | As above |
| `AUDIT_EXCLUDED_PATHS` | `/chats,/chat,/folders` | List (comma-separated API paths) | `env.py:1241-1247` | API paths under `/api` or `/api/v1` that are not audited (`utils/audit.py:150-153`, `:256-258`). | Yes | As above |
| `AUDIT_INCLUDED_PATHS` | empty | List | `env.py:1251-1253` | When set, only these paths are audited and the exclusions are ignored; setting both logs a warning (`utils/audit.py:156-160`, `:252-254`). Sign-in, sign-out and sign-up are audited whenever auditing is on (`utils/audit.py:229-245`). | Yes | As above |
| `ENABLE_AUDIT_GET_REQUESTS` | `False` | Boolean | `env.py:1256` | Audits GET requests too; by default only POST, PUT, PATCH and DELETE are audited (`utils/audit.py:120`, `:143-144`). | Yes | As above |

### 7.7 OpenTelemetry

Telemetry export is off unless `ENABLE_OTEL` is on; traces, metrics and logs then each need their own switch (`main.py:550-553`; `utils/telemetry/setup.py:27-57`; `utils/logger.py:117-123`). The repository's example overlay turns on metrics and an insecure local collector (`docker-compose.otel.yaml:24-29`). Whether MedIT GPT exports telemetry, and to where, is **TO BE CONFIRMED**.

| Variable | Code default | Type | Read at | Effect | Restart | In depth |
|---|---|---|---|---|---|---|
| `ENABLE_OTEL` | `False` | Boolean | `env.py:1263` | Master switch: loads the telemetry set-up at import (`main.py:550-553`) and adds trace ids to log records (`utils/logger.py:125-136`). | Yes | `deployment-operations-and-logging.md` *(planned)* |
| `ENABLE_OTEL_TRACES` | `False` | Boolean | `env.py:1264` | Exports request, database and outbound-call traces (`utils/telemetry/setup.py:30-53`; `utils/telemetry/instrumentors.py`). | Yes | As above |
| `ENABLE_OTEL_METRICS` | `False` | Boolean | `env.py:1265` | Exports metrics (`utils/telemetry/setup.py:56-57`; `utils/telemetry/metrics.py`). | Yes | As above |
| `ENABLE_OTEL_LOGS` | `False` | Boolean | `env.py:1266` | Also sends every log record to the collector (`utils/logger.py:117-123`; `utils/telemetry/logs.py`). Log records can contain personal data. | Yes | As above |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | Text (URL) | `env.py:1268` | Collector address for traces, and the default for metrics and logs (`utils/telemetry/setup.py:41-51`). | Yes | As above |
| `OTEL_METRICS_EXPORTER_OTLP_ENDPOINT` | the value of `OTEL_EXPORTER_OTLP_ENDPOINT` | Text (URL) | `env.py:1269` | Collector address for metrics (`utils/telemetry/metrics.py:103-118`). | Yes | As above |
| `OTEL_LOGS_EXPORTER_OTLP_ENDPOINT` | the value of `OTEL_EXPORTER_OTLP_ENDPOINT` | Text (URL) | `env.py:1270` | Collector address for logs (`utils/telemetry/logs.py:33-41`). | Yes | As above |
| `OTEL_EXPORTER_OTLP_INSECURE` | `False` | Boolean | `env.py:1271` | Sends traces over gRPC without TLS (`utils/telemetry/setup.py:47-51`); the default for the two below. The compose overlay notes this is to be removed in production (`docker-compose.otel.yaml:27`). | Yes | As above |
| `OTEL_METRICS_EXPORTER_OTLP_INSECURE` | the value of `OTEL_EXPORTER_OTLP_INSECURE` | Boolean | `env.py:1272-1274` | The same for metrics (`utils/telemetry/metrics.py:112-118`). | Yes | As above |
| `OTEL_LOGS_EXPORTER_OTLP_INSECURE` | the value of `OTEL_EXPORTER_OTLP_INSECURE` | Boolean | `env.py:1275-1277` | The same for logs (`utils/telemetry/logs.py:38-41`). | Yes | As above |
| `OTEL_SERVICE_NAME` | `open-webui` | Text | `env.py:1278` | Service name attached to exported data (`utils/telemetry/setup.py:29`). | Yes | As above |
| `OTEL_RESOURCE_ATTRIBUTES` | empty | Text (`key=value` pairs) | `env.py:1279` | Read into a constant that nothing else in the code uses; the OpenTelemetry library reads the same standard variable itself (`.venv` copy of `opentelemetry/sdk/resources/__init__.py`, version 1.42.1; library behaviour). | Yes | As above |
| `OTEL_TRACES_SAMPLER` | `parentbased_always_on` | Text | `env.py:1280` | As above: unused by the application code; the library reads the standard variable itself (library behaviour). | Yes | As above |
| `OTEL_BASIC_AUTH_USERNAME` | empty | Text | `env.py:1281` | User for basic authentication to the trace collector, sent only when a password is also set (`utils/telemetry/setup.py:34-38`); default for the metrics and logs users. | Yes | As above |
| `OTEL_BASIC_AUTH_PASSWORD` | empty; set per environment | Text (secret) | `env.py:1282` | Password for the above. | Yes | As above |
| `OTEL_METRICS_BASIC_AUTH_USERNAME` | the value of `OTEL_BASIC_AUTH_USERNAME` | Text | `env.py:1285` | Basic-authentication user for the metrics collector (`utils/telemetry/metrics.py:97-101`). | Yes | As above |
| `OTEL_METRICS_BASIC_AUTH_PASSWORD` | the value of `OTEL_BASIC_AUTH_PASSWORD` | Text (secret) | `env.py:1286` | Password for the above. | Yes | As above |
| `OTEL_LOGS_BASIC_AUTH_USERNAME` | the value of `OTEL_BASIC_AUTH_USERNAME` | Text | `env.py:1287` | Basic-authentication user for the logs collector (`utils/telemetry/logs.py:27-31`). | Yes | As above |
| `OTEL_LOGS_BASIC_AUTH_PASSWORD` | the value of `OTEL_BASIC_AUTH_PASSWORD` | Text (secret) | `env.py:1288` | Password for the above. | Yes | As above |
| `OTEL_METRICS_EXPORT_INTERVAL_MILLIS` | `10000` | Integer, exits if invalid | `env.py:1283` | How often metrics are pushed, in milliseconds (`utils/telemetry/metrics.py:107`, `:118`). | Yes | As above |
| `OTEL_OTLP_SPAN_EXPORTER` | `grpc` | Text (`grpc` or `http`) | `env.py:1290` | Protocol for traces; anything other than `http` means gRPC (`utils/telemetry/setup.py:41-51`); the default for the two below. | Yes | As above |
| `OTEL_METRICS_OTLP_SPAN_EXPORTER` | the value of `OTEL_OTLP_SPAN_EXPORTER` | Text | `env.py:1292-1294` | Protocol for metrics (`utils/telemetry/metrics.py:103`). | Yes | As above |
| `OTEL_LOGS_OTLP_SPAN_EXPORTER` | the value of `OTEL_OTLP_SPAN_EXPORTER` | Text | `env.py:1296-1298` | Protocol for logs (`utils/telemetry/logs.py:33`). | Yes | As above |

### 7.8 Process, Performance, Time-Outs and Outbound Connections

Outbound calls (to model providers, tool servers, web search, content extraction and so on) mostly share one connection pool per worker (`utils/session_pool.py:1-80`). Certificate checking is on by default; where an internal certificate authority is needed, the code accepts a CA bundle path rather than requiring checks to be turned off (`env.py:548-601`). `THREAD_POOL_SIZE` and `THREAD_POOL_THREAD_NAME_PREFIX` are read in `config.py` but are environment-only.

| Variable | Code default | Type | Read at | Effect | Restart | In depth |
|---|---|---|---|---|---|---|
| `UVICORN_WORKERS` | `1` (values below 1 become 1) | Integer, silent fallback | `env.py:461-464`; `backend/start.sh:99` | Number of server processes. `open-webui serve` reads the constant (`__init__.py:84-92`); `start.sh` reads the shell variable itself and passes `--workers` (`backend/start.sh:99-104`). More than one worker needs Redis (section 7.5). | Yes | `deployment-operations-and-logging.md` *(planned)* |
| `UVICORN_WS_PER_MESSAGE_DEFLATE` | `True` | Boolean | `env.py:467`; `backend/start.sh:104` | Per-message compression on websocket frames; the code comment says tiny streamed frames can make it CPU-bound (`env.py:466`; `__init__.py:90`, `:109`; `backend/dev.sh:3`). | Yes | As above |
| `THREAD_POOL_SIZE` | unset (library default) | Integer; an invalid value logs a warning and is ignored | `config.py:2103-2111` | Size of the worker thread pool used for blocking work, set at start-up (`main.py:350-358`). | Yes | As above |
| `THREAD_POOL_THREAD_NAME_PREFIX` | empty | Text | `config.py:2104` | Name prefix for those threads, visible in diagnostics (`main.py:356`). | Yes | As above |
| `ENABLE_COMPRESSION_MIDDLEWARE` | `True` | Boolean | `env.py:790` | Compresses HTTP responses (`main.py:816-817`). | Yes | `backend-architecture-and-request-lifecycle.md` *(planned)* |
| `ENABLE_ORJSON` | `False` | Boolean | `env.py:162` | Switches the application's JSON encoder from the standard library to orjson; faster but stricter (`env.py:159-162`; `utils/json_codec.py:1-20`; `main.py:499-501`). | Yes | As above |
| `AIOHTTP_CLIENT_TIMEOUT` | unset (**no** overall time-out); an invalid value becomes 300 | Integer (seconds) | `env.py:608-612` | Overall time limit for outbound requests through the shared pool and many direct calls, including chat completions (`utils/session_pool.py:43-47`; `routers/configs.py:376`; `retrieval/utils.py:947`). | Yes | `model-connections-openai-ollama-and-direct.md` |
| `AIOHTTP_CLIENT_STREAM_IDLE_TIMEOUT` | unset (no limit) | Integer (seconds), silent fallback; `0` or less means no limit | `env.py:614-625` | Longest allowed gap between two pieces of a streamed reply before the stream is abandoned (`utils/session_pool.py:44-47`). | Yes | `chat-completion-pipeline-and-generation-tasks.md` |
| `AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST` | `10` (seconds) | Integer, silent fallback; empty means no limit | `env.py:656-663` | Time limit when fetching model lists from Ollama, OpenAI-compatible, Anthropic and speech providers (`routers/openai.py:79`; `routers/ollama.py:60`; `utils/anthropic.py:45`; `routers/audio.py:1348`). A slow provider then contributes no models. | Yes | `model-connections-openai-ollama-and-direct.md` |
| `AIOHTTP_CLIENT_TIMEOUT_OPENAI_MODEL_LIST` | `10` | Integer | `env.py:658` | Older name, used only when `AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST` is unset. | Yes | As above |
| `AIOHTTP_CLIENT_TIMEOUT_TOOL_SERVER_DATA` | `10` (seconds) | Integer, silent fallback; empty means no limit | `env.py:665-669` | Time limit for fetching a tool server's description and for terminal-server data calls (`utils/tools.py:1484`; `utils/middleware.py:2865`; `utils/terminals.py:260`). | Yes | `workspace-tools-tool-servers-mcp-and-terminals.md` |
| `AIOHTTP_CLIENT_TIMEOUT_TOOL_SERVER` | the value of `AIOHTTP_CLIENT_TIMEOUT` | Integer (seconds), silent fallback | `env.py:686-694` | Time limit for tool-server calls and MCP connections (`utils/tools.py:1723`; `utils/mcp/client.py:22-38`). | Yes | As above |
| `MCP_INITIALIZE_TIMEOUT` | `10` (seconds) | Integer, silent fallback | `env.py:696-703` | Time limit for the opening handshake with an MCP server, which lists its tools (`utils/mcp/client.py:81`). | Yes | As above |
| `AIOHTTP_FILE_STREAM_CHUNK_SIZE` | `1048576` (1 MiB) | Integer, silent fallback; `0` or less becomes the default | `env.py:671-678` | Chunk size when streaming uploaded files to speech, Ollama and pipeline servers (`routers/audio.py:738`; `routers/ollama.py:1555`; `routers/pipelines.py:247`). | Yes | `audio-speech-to-text-and-text-to-speech.md` |
| `AIOHTTP_POOL_CONNECTIONS` | unset (unlimited) | Integer, silent fallback | `env.py:710-717` | Total connection limit of the shared outbound pool per worker (`utils/session_pool.py:62-65`). The module's comment says 100, but the code uses no limit when unset (`utils/session_pool.py:9`, `:65`). | Yes | `model-connections-openai-ollama-and-direct.md` |
| `AIOHTTP_POOL_CONNECTIONS_PER_HOST` | unset (unlimited) | Integer, silent fallback | `env.py:719-726` | Per-host connection limit of that pool (`utils/session_pool.py:66-69`); the module comment says 30 (`utils/session_pool.py:10`). | Yes | As above |
| `AIOHTTP_POOL_DNS_TTL` | `300` (seconds) | Integer, silent fallback; negative becomes 300 | `env.py:728-734` | How long the pool caches name lookups (`utils/session_pool.py:59`). | Yes | As above |
| `AIOHTTP_CLIENT_ASYNC_DNS_RESOLVER` | `False` | Boolean | `env.py:642` | Off, the code forces the threaded name resolver because the asynchronous one breaks name resolution in some environments (`env.py:639-649`). | Yes | As above |
| `AIOHTTP_CLIENT_ALLOW_REDIRECTS` | `False` | Boolean | `env.py:637` | Whether outbound requests (web loading, image and file fetches, the code interpreter) follow HTTP redirects (`env.py:636`; `retrieval/web/utils.py:765`, `:823`, `:952`; `routers/images.py:937`; `utils/files.py:80`). | Yes | `web-search-and-web-loading.md` |
| `AIOHTTP_CLIENT_SESSION_SSL` | `True` | Text (`True`, `False` or a CA bundle path) | `env.py:631` | Certificate checking for general outbound HTTPS (providers, single sign-on, web search). `True` uses `AIOHTTP_CLIENT_SSL_CERT_FILE` when set; a path loads that bundle; `False` turns checking off, which is not recommended (`env.py:578-601`). A path that does not exist logs `SSL CA bundle path does not exist: {path}, ignoring` and the default is used (`env.py:563-568`). | Yes | `model-connections-openai-ollama-and-direct.md` |
| `AIOHTTP_CLIENT_SESSION_TOOL_SERVER_SSL` | `True` | Text (as above) | `env.py:684` | The same for tool servers, MCP servers and terminals (`utils/mcp/client.py:47-71`; `utils/tools.py:1486`, `:1733`; `utils/terminals.py:205`). | Yes | `workspace-tools-tool-servers-mcp-and-terminals.md` |
| `AIOHTTP_CLIENT_SSL_CERT_FILE` | empty | Path (CA bundle) | `env.py:556` | Organization-wide CA bundle used wherever the two variables above are `True`; loading it logs `Using custom SSL CA bundle: {path}` (`env.py:548-575`; `retrieval/web/utils.py:723-733`). | Yes | `web-search-and-web-loading.md` |
| `REQUESTS_VERIFY` | `True` | Boolean | `env.py:604` | Certificate checking for the Tika content-extraction server and the external reranker (`retrieval/loaders/main.py:240`; `retrieval/models/external.py:54`). | Yes | `rag-retrieval-embeddings-and-vector-stores.md` |
| `MODELS_CACHE_TTL` | `1` (second) | Integer, silent fallback; empty turns caching off | `env.py:1035-1042` | How long each worker caches the combined model list from Ollama and OpenAI-compatible connections (`routers/ollama.py:384-390`; `routers/openai.py:791`). | Yes | `workspace-models-and-model-access.md` |
| `CHAT_RESPONSE_STREAM_DELTA_CHUNK_SIZE` | `1` | Integer, silent fallback | `env.py:1070-1078` | Minimum number of streamed pieces batched into one update to the browser; a model's own setting can raise it (`utils/middleware.py:4927-4930`). | Yes | `chat-completion-pipeline-and-generation-tasks.md` |
| `CHAT_STREAM_RESPONSE_CHUNK_MAX_BUFFER_SIZE` | unset (no limit) | Integer (bytes), silent fallback | `env.py:1108-1116` | A streamed line longer than this is dropped (`utils/misc.py:1272-1283`). | Yes | As above |
| `ENABLE_CHAT_RESPONSE_STREAM_INPLACE_APPEND` | `False` | Boolean | `env.py:1057-1059` | Memory optimization for long streamed replies, off by default for a staged roll-out (`env.py:1054-1056`; `utils/middleware.py:324`). | Yes | As above |
| `CHAT_RESPONSE_MAX_TOOL_CALL_ITERATIONS` | `256` (`-1` means unlimited) | Integer, silent fallback | `env.py:1081-1098` | Maximum rounds of tool calls in one reply (`utils/middleware.py:5830-5835`). | Yes | `builtin-native-tools.md` |
| `CHAT_RESPONSE_MAX_TOOL_CALL_RETRIES` | `256` | Integer | `env.py:1085` | Older name for the above, used only when the new name is unset. | Yes | As above |

### 7.9 Feature Switches Outside Persistent Config

These switches look like settings but have no Admin Settings control: they come only from the environment, so an admin cannot change them in the interface and tier 1 sees only their effects.

| Variable | Code default | Type | Read at | Effect | Restart | In depth |
|---|---|---|---|---|---|---|
| `SAFE_MODE` | `False` | Boolean | `env.py:965` | Prints `SAFE MODE ENABLED` at import and switches **every** function off at each start-up; functions stay off after safe mode is removed until an admin switches them on again (`main.py:280-281`, `:382-383`). | Yes | `functions-pipes-filters-actions-and-pipelines.md` |
| `ENABLE_PLUGINS` | `True` | Boolean | `env.py:1186` | Master switch for functions and workspace tools: off, their lists come back empty, pipes, filters, actions and event functions are skipped and the Functions pages are hidden (`functions.py:72-73`; `events.py:1106-1107`; `routers/functions.py:50-51`; `routers/tools.py:201-202`; `main.py:2353`). | Yes | As above |
| `ENABLE_PIP_INSTALL_FRONTMATTER_REQUIREMENTS` | `True` | Boolean | `env.py:1188-1190` | Lets the server install the Python packages that a tool or function lists in its header, at start-up and whenever a tool or function module is loaded, for example after it is created or edited (`utils/plugin.py:206-225`, `:255-275`, `:422-426`, `:453-482`; `main.py:385-388`). | Yes | As above |
| `PIP_OPTIONS` | empty | List (space-separated) | `env.py:1192` | Extra options for those installs (`utils/plugin.py:442`). | Yes | As above |
| `PIP_PACKAGE_INDEX_OPTIONS` | empty | List (space-separated) | `env.py:1193` | Package-index options for those installs, for example an internal mirror (`utils/plugin.py:442`). | Yes | As above |
| `ENABLE_KB_EXEC` | `False` | Boolean | `env.py:968` | Offers the knowledge-base command tool (with file querying) to models instead of the separate browsing tools (`utils/tools.py:606-618`). | Yes | `builtin-native-tools.md`, `knowledge-bases.md` |
| `KB_EXEC_MAX_OUTPUT_CHARS` | `30000` | Integer (values below 1 become 1; invalid becomes the default) | `env.py:1165-1173` | Maximum output of one knowledge-base command (`tools/knowledge_fs.py:1195`). Read through a helper, so the inventory pattern misses it. | Yes | `builtin-native-tools.md` |
| `KB_EXEC_MAX_GREP_FILES` | `200` | Integer (as above) | `env.py:1175` | Files one knowledge-base search may scan before asking for a narrower scope (`tools/knowledge_fs.py:802`). | Yes | As above |
| `KNOWLEDGE_GREP_MAX_MATCHES` | `50` | Integer (as above) | `env.py:1177` | Matching lines returned by knowledge searches (`tools/knowledge_fs.py:830`, `:849-850`; `tools/builtin.py:2393`, `:2408-2409`). | Yes | As above |
| `VIEW_FILE_MAX_CHARS` | `100000` | Integer (as above) | `env.py:1179` | Upper limit on characters returned when a model views a file (`tools/builtin.py:2791`, `:2903`). | Yes | As above |
| `VIEW_FILE_DEFAULT_MAX_CHARS` | `10000` | Integer (as above) | `env.py:1180` | Characters returned when the model does not ask for a size (`tools/builtin.py:2753`, `:2788`). | Yes | As above |
| `ENABLE_OPENAI_API_PASSTHROUGH` | `False` | Boolean | `env.py:862` | Allows the deprecated catch-all proxy to OpenAI-compatible APIs under `/openai/`; off, it answers 403 `Direct API passthrough is disabled. Set ENABLE_OPENAI_API_PASSTHROUGH=True to enable.` (`routers/openai.py:1994-2005`). | Yes | `model-connections-openai-ollama-and-direct.md` |
| `ENABLE_CUSTOM_MODEL_FALLBACK` | `False` | Boolean | `env.py:1033` | When a custom model's base model is gone, answers with the first default model instead of failing (`main.py:1132-1142`). | Yes | `chat-completion-pipeline-and-generation-tasks.md` |
| `ENABLE_API_OUTLET_FILTERS` | `True` | Boolean | `env.py:1052` | Runs outlet filters for API callers as well as the chat screen (`utils/middleware.py:4416`, `:6653-6654`). | Yes | As above |
| `ENABLE_RESPONSES_API_STATEFUL` | `False` | Boolean (experimental) | `env.py:1105` | Sends only new items with the previous response id to Responses-API endpoints; the code warns most proxies are stateless and break (`env.py:1101-1105`; `utils/middleware.py:5181`, `:6235`). | Yes | As above |
| `ENABLE_CHAT_RESPONSE_BASE64_IMAGE_URL_CONVERSION` | `False` | Boolean | `env.py:1049-1051` | Saves images that a model returns inline as files and links them instead (`utils/middleware.py:5567-5576`). | Yes | As above |
| `ENABLE_QUERIES_CACHE` | `False` | Boolean | `env.py:370` | Reuses the search queries generated for web search when retrieval runs in the same turn (`utils/middleware.py:1617-1618`; `routers/tasks.py:419-421`). | Yes | `web-search-and-web-loading.md` |
| `ENABLE_REALTIME_CHAT_SAVE` | `False` | Boolean | `env.py:369` | **No effect in v0.11.4**: imported by the chat pipeline but not used anywhere else (`utils/middleware.py:42`; searched `backend/open_webui` and `src`). | Yes | `chat-completion-pipeline-and-generation-tasks.md` |
| `ENABLE_IMAGE_CONTENT_TYPE_EXTENSION_FALLBACK` | `False` | Boolean | `env.py:1066-1068` | Guesses an image's type from its file extension when neither the system nor the stored metadata knows it, for minimal container images (`env.py:1061-1065`; `utils/files.py:233-234`). | Yes | `files-uploads-and-storage.md` |
| `BYPASS_PYDUB_PREPROCESSING` | `False`; always on in the slim image | Boolean | `env.py:857` | Skips audio conversion, compression and splitting before speech-to-text, and writes text-to-speech audio without transcoding (`routers/audio.py:185-187`, `:1019`, `:1138-1140`). | Yes | `audio-speech-to-text-and-text-to-speech.md` |
| `ENABLE_PYODIDE_FILE_PERSISTENCE` | `false` | Boolean | `env.py:1211` | Runs the in-browser Python sandbox as a worker whose files are kept in the browser's storage (`main.py:2348`; `src/lib/pyodide/createPyodideWorker.ts:7-10`). | Yes; users reload the page | `code-execution-and-interpreter.md` |
| `ENABLE_PUBLIC_ACTIVE_USERS_COUNT` | `True` | Boolean | `env.py:367` | Shows the count of active users to everyone; off, only admins see it and others get 403 `Access denied. Only administrators can view usage statistics.` (`main.py:2628-2633`; `src/lib/components/layout/Sidebar/UserMenu.svelte:91`). | Yes | `users-groups-roles-and-permissions.md` |
| `ENABLE_EASTER_EGGS` | `True` | Boolean | `env.py:966` | Offers the "Her" theme and the Doge language in personal settings (`main.py:2350`; `src/lib/components/chat/Settings/General.svelte:136-137`, `:241-243`). | Yes | `user-settings-and-personalisation.md` |
| `ENABLE_PROFILE_IMAGE_URL_FORWARDING` | `True` | Boolean | `env.py:970` | Profile and model pictures stored as external links are served by redirecting the browser to that address; off, the default picture is shown instead, which avoids exposing users' browsers to external sites (`routers/users.py:857-865`; `routers/models.py:820`; `routers/channels.py:1849`). | Yes | `users-groups-roles-and-permissions.md` |
| `PROFILE_IMAGE_ALLOWED_MIME_TYPES` | `image/png,image/jpeg,image/gif,image/webp` | List | `env.py:971-978` | Picture types accepted for embedded profile and model images; others show the default picture (`routers/users.py:875-876`; `routers/models.py:836`; `utils/validate.py:15-16`). | Yes | As above |
| `PROFILE_IMAGE_MAX_DATA_URI_SIZE` | unset (no limit) | Integer (bytes), exits if invalid | `env.py:982-983` | Largest embedded picture accepted; larger ones are refused with `Invalid profile image URL: data URI exceeds the {PROFILE_IMAGE_MAX_DATA_URI_SIZE}-byte limit.` (`utils/validate.py:87-89`). | Yes | As above |
| `EXTERNAL_PWA_MANIFEST_URL` | unset | Text (URL) | `env.py:1018` | Serves an external web-app manifest at `/manifest.json` instead of the generated one, which carries the product name (`main.py:541`, `:2868-2880`). Covered by the licence branding comments (`env.py:1014-1017`). | Yes | `local-customisations-uoft-fork.md` *(planned)* |

### 7.10 Retrieval, Embeddings, Web Search and Vector Stores

Most retrieval behaviour is persistent settings (`rag.*`, `web.*`), edited on the Documents and Web Search admin screens and catalogued in `configuration-persistent-settings-r-to-w.md` *(planned)*. The rows below are environment-only. The vector-store rows at the end are read in `config.py` but are not stored in the `config` table (`DEFAULT_CONFIG` has no vector-store keys, `config.py:2822-3230`); keys and passwords are named only.

| Variable | Code default | Type | Read at | Effect | Restart | In depth |
|---|---|---|---|---|---|---|
| `RAG_SYSTEM_CONTEXT` | `False` | Boolean | `env.py:372` | Puts retrieved sources in the system message instead of the user message (`utils/middleware.py:996`, `:6211`). | Yes | `rag-retrieval-embeddings-and-vector-stores.md` |
| `RAG_SOURCE_METADATA_KEYS` | empty | List | `env.py:374-375` | Extra chunk metadata fields passed to the model with each source; empty because chunk metadata also holds internal details (`env.py:374`; `retrieval/utils.py:1367`). | Yes | As above |
| `RAG_EMBEDDING_TIMEOUT` | unset (no limit) | Integer (seconds), silent fallback | `env.py:736-744` | Time limit for one embedding batch while a document is processed (`routers/retrieval.py:1879`). | Yes | As above |
| `RAG_METADATA_MAX_VALUE_CHARS` | derived from `RAG_FILE_MAX_SIZE` (megabytes times 1,048,576), otherwise no limit | Integer, exits if invalid | `env.py:841-848` | Longest list or object value kept in chunk metadata; the code comment says it guards against archives that expand enormously (`env.py:841-843`; `retrieval/vector/utils.py:28-30`, `:50-52`). | Yes | As above |
| `RAG_FILE_MAX_SIZE` | `0` here | Integer (megabytes), exits if invalid | `env.py:847` | Read in `env.py` only to derive the limit above. The upload size limit itself is the persistent setting `rag.file.max_size`, seeded from the same name (`config.py:983`, `:2907`). | Yes | `files-uploads-and-storage.md` |
| `MINERU_MAX_MARKDOWN_BYTES` | unset (no limit) | Integer, exits if invalid | `env.py:850-852` | Largest Markdown result accepted from the MinerU extraction engine (`retrieval/loaders/main.py:674`). | Yes | `rag-retrieval-embeddings-and-vector-stores.md` |
| `ENABLE_RAG_CSV_SUMMARY` | `False` | Boolean | `retrieval/loaders/main.py:182` | Adds a generated summary as the first chunk of each CSV file (`retrieval/loaders/main.py:182-185`). Read each time a CSV file is loaded. | Yes | As above |
| `SENTENCE_TRANSFORMERS_BACKEND` | `torch` (empty becomes `torch`) | Text | `env.py:1124-1126` | Runtime for the local embedding model (`routers/retrieval.py:163`). | Yes | As above |
| `SENTENCE_TRANSFORMERS_MODEL_KWARGS` | unset | JSON, silent fallback | `env.py:1129-1136` | Extra options for loading the local embedding model (`routers/retrieval.py:164`). | Yes | As above |
| `SENTENCE_TRANSFORMERS_CROSS_ENCODER_BACKEND` | `torch` | Text | `env.py:1139-1141` | Runtime for the local reranking model (`routers/retrieval.py:216`). | Yes | As above |
| `SENTENCE_TRANSFORMERS_CROSS_ENCODER_MODEL_KWARGS` | unset | JSON, silent fallback | `env.py:1144-1151` | Extra options for the local reranking model (`routers/retrieval.py:217`). | Yes | As above |
| `SENTENCE_TRANSFORMERS_CROSS_ENCODER_SIGMOID_ACTIVATION_FUNCTION` | `True` | Boolean | `env.py:1156-1158` | Scales reranking scores to 0 to 1 so the relevance threshold behaves as expected (`env.py:1153-1155`; `routers/retrieval.py:219`). | Yes | As above |
| `SENTENCE_TRANSFORMERS_HOME` | unset; the image sets `/app/backend/data/cache/embedding/models` (`Dockerfile:105`) | Path | `retrieval/utils.py:1725`; `routers/retrieval.py:1659` | Download cache for local models and the tokenizer (`retrieval/utils.py:1725-1735`; `routers/retrieval.py:1659-1668`). | Yes | As above |
| `HF_HUB_CACHE` | unset | Path | `routers/retrieval.py:1659` | Tokenizer cache, used only when `SENTENCE_TRANSFORMERS_HOME` is unset (`routers/retrieval.py:1659`). | Yes | As above |
| `AUXILIARY_EMBEDDING_MODEL` | `TaylorAI/bge-micro-v2` | Text (model name) | `routers/evaluations.py:68` | Small embedding model used to weight the evaluation leaderboard by topic; not loaded in the slim image (`routers/evaluations.py:60-84`). The image pre-downloads it (`Dockerfile:104`, `:176`). | Yes | `evaluations-feedback-and-analytics.md` |
| `TAVILY_API_BASE_URL` | `https://api.tavily.com` | Text (URL) | `env.py:606` | Address of the Tavily search and extraction service (`retrieval/web/tavily.py:29`; `retrieval/loaders/tavily.py:52`). | Yes | `web-search-and-web-loading.md` |
| `SEARXNG_CLIENT_CERT_FILE` | empty | Path | `env.py:633` | Client certificate presented to a SearXNG server that requires one (`retrieval/web/searxng.py:28-34`). | Yes | As above |
| `SEARXNG_CLIENT_KEY_FILE` | empty | Path (secret file) | `env.py:634` | Private key for that certificate (`retrieval/web/searxng.py:34`). | Yes | As above |
| `USER_AGENT` | empty (the library's default) | Text | `env.py:654` | User-Agent sent when fetching web pages; the code notes the default is widely blocked (`env.py:651-654`; `retrieval/web/utils.py:961`). | Yes | As above |
| `BING_SEARCH_V7_SUBSCRIPTION_KEY` | empty; set per environment | Text (secret) | `retrieval/web/bing.py:68` | Read here only by the module's command-line test (`retrieval/web/bing.py:48-75`). The application uses the persistent setting `web.search.bing_search_v7_subscription_key`, seeded from the same name (`config.py:1270`, `:2984`). | Seed only (section 1.1) | `web-search-and-web-loading.md` |
| `BING_SEARCH_V7_ENDPOINT` | `https://api.bing.microsoft.com/v7.0/search` | Text (URL) | `retrieval/web/bing.py:69` | As above; the application uses `web.search.bing_search_v7_endpoint` (`config.py:1268`, `:2983`). | Seed only | As above |
| `YANDEX_WEB_SEARCH_URL` | empty | Text (URL) | `retrieval/web/yandex.py:145` | Read here only by the module's command-line test (`retrieval/web/yandex.py:124-152`); the application uses `web.search.yandex_web_search_url` (`config.py:1329`, `:3013`). | Seed only | As above |
| `YANDEX_WEB_SEARCH_API_KEY` | empty; set per environment | Text (secret) | `retrieval/web/yandex.py:146` | As above; the application uses `web.search.yandex_web_search_api_key` (`config.py:1331`, `:3014`). | Seed only | As above |
| `YANDEX_WEB_SEARCH_CONFIG` | a JSON search-type default | JSON | `retrieval/web/yandex.py:147` | As above; the application uses `web.search.yandex_web_search_config` (`config.py:1333`, `:3015`). | Seed only | As above |
| `VECTOR_DB` | `chroma`; `pgvector` in the slim image | Text: `chroma`, `pgvector`, `qdrant`, `milvus`, `opensearch`, `elasticsearch`, `pinecone`, `s3vector`, `oracle23ai`, `weaviate`, `opengauss`, `mariadb-vector`, `valkey` | `config.py:503` | Which vector store holds document and memory embeddings (`retrieval/vector/type.py`; `retrieval/vector/factory.py:14-100`). An unknown value stops start-up with `Unsupported vector type: {vector_type}`; the slim image accepts only `pgvector` (section 10). The chosen store is logged as `VECTOR_DB: {VECTOR_DB}` (`config.py:822`). Nothing in `retrieval/vector` copies collections between stores; an admin can re-embed knowledge bases (`routers/knowledge.py:374-461`). | Yes; all workers and replicas must agree | `rag-retrieval-embeddings-and-vector-stores.md` |
| Chroma: `CHROMA_HTTP_HOST`, `CHROMA_HTTP_PORT`, `CHROMA_HTTP_SSL`, `CHROMA_HTTP_HEADERS`, `CHROMA_TENANT`, `CHROMA_DATABASE`, `CHROMA_CLIENT_AUTH_PROVIDER`, `CHROMA_CLIENT_AUTH_CREDENTIALS` (secret) | host empty; port `8000` (exits if not a number); SSL `false`; tenant and database the library defaults | Text, Integer, Boolean, comma-separated `header=value` pairs | `config.py:508-523` | Read only when `VECTOR_DB=chroma` outside the slim image. With no host, the embedded store in `DATA_DIR/vector_db` is used (`config.py:506`; `retrieval/vector/dbs/chroma.py:34-46`); otherwise the server at that host. | Yes | As above |
| pgvector: `PGVECTOR_DB_URL`, `PGVECTOR_INITIALIZE_MAX_VECTOR_LENGTH`, `PGVECTOR_USE_HALFVEC`, `PGVECTOR_CREATE_EXTENSION`, `PGVECTOR_PGCRYPTO`, `PGVECTOR_PGCRYPTO_KEY` (secret), `PGVECTOR_POOL_SIZE`, `PGVECTOR_POOL_MAX_OVERFLOW`, `PGVECTOR_POOL_TIMEOUT`, `PGVECTOR_POOL_RECYCLE`, `PGVECTOR_INDEX_METHOD`, `PGVECTOR_HNSW_M`, `PGVECTOR_HNSW_EF_CONSTRUCTION`, `PGVECTOR_IVFFLAT_LISTS`, `PGVECTOR_ITERATIVE_SCAN` | URL `DATABASE_URL`; length `1536`; half-vectors `false`; create extension `true`; pgcrypto `false`; pool as for the main database (`0`, `30`, `3600`); index method automatic; HNSW `16`/`64`; lists `100`; scan `relaxed_order` | URL, Integers (silent fallback except the length), Booleans, Text | `config.py:648-747` | PostgreSQL with the `vector` extension. Start-up stops when the URL is not PostgreSQL, when the length is over 2000 without half-vectors, or when pgcrypto is on without its key (`config.py:649-669`); changing the length after tables exist also stops it (section 10). | Yes | As above |
| Qdrant: `QDRANT_URI`, `QDRANT_API_KEY` (secret), `QDRANT_ON_DISK`, `QDRANT_PREFER_GRPC`, `QDRANT_GRPC_PORT`, `QDRANT_TIMEOUT`, `QDRANT_HNSW_M`, `ENABLE_QDRANT_MULTITENANCY_MODE`, `QDRANT_COLLECTION_PREFIX` | URI unset; on-disk `false`; gRPC `false`, port `6334`; time-out `5`; HNSW `16`; multitenancy `true`; prefix `open-webui` | Text, Booleans, Integers (exit if invalid) | `config.py:612-620` | Qdrant server; multitenancy mode selects the shared-collection client (`retrieval/vector/factory.py:37-47`). | Yes | As above |
| Milvus: `MILVUS_URI`, `MILVUS_DB`, `MILVUS_TOKEN` (secret), `MILVUS_INDEX_TYPE`, `MILVUS_METRIC_TYPE`, `MILVUS_HNSW_M`, `MILVUS_HNSW_EFCONSTRUCTION`, `MILVUS_IVF_FLAT_NLIST`, `MILVUS_DISKANN_MAX_DEGREE`, `MILVUS_DISKANN_SEARCH_LIST_SIZE`, `ENABLE_MILVUS_MULTITENANCY_MODE`, `MILVUS_COLLECTION_PREFIX` | URI `{DATA_DIR}/vector_db/milvus.db`; database `default`; `HNSW`, `COSINE`, `16`, `100`, `128`, `56`, `100`; multitenancy `false`; prefix `open_webui` | Text, Integers (exit if invalid), Boolean | `config.py:597-609` | Milvus (local file or server) (`retrieval/vector/factory.py:26-36`). | Yes | As above |
| Weaviate: `WEAVIATE_HTTP_HOST`, `WEAVIATE_GRPC_HOST`, `WEAVIATE_HTTP_PORT`, `WEAVIATE_GRPC_PORT`, `WEAVIATE_API_KEY` (secret), `WEAVIATE_HTTP_SECURE`, `WEAVIATE_GRPC_SECURE`, `WEAVIATE_SKIP_INIT_CHECKS` | hosts empty; ports `8080` and `50051`; secure `false`; skip checks `false` | Text, Integers (exit if invalid), Booleans | `config.py:622-629` | Weaviate server. | Yes | As above |
| OpenSearch: `OPENSEARCH_URI`, `OPENSEARCH_SSL`, `OPENSEARCH_CERT_VERIFY`, `OPENSEARCH_USERNAME`, `OPENSEARCH_PASSWORD` (secret) | `https://localhost:9200`; SSL `true`; certificate checking **`false`** | Text, Booleans | `config.py:632-636` | OpenSearch cluster. Certificate checking is off unless `OPENSEARCH_CERT_VERIFY=true`. | Yes | As above |
| Elasticsearch: `ELASTICSEARCH_URL`, `ELASTICSEARCH_CA_CERTS`, `ELASTICSEARCH_API_KEY` (secret), `ELASTICSEARCH_USERNAME`, `ELASTICSEARCH_PASSWORD` (secret), `ELASTICSEARCH_CLOUD_ID`, `SSL_ASSERT_FINGERPRINT`, `ELASTICSEARCH_INDEX_PREFIX` | `https://localhost:9200`; prefix `open_webui_collections` | Text | `config.py:639-646` | Elasticsearch cluster; `SSL_ASSERT_FINGERPRINT` pins the server certificate. | Yes | As above |
| openGauss: `OPENGAUSS_DB_URL`, `OPENGAUSS_INITIALIZE_MAX_VECTOR_LENGTH`, `OPENGAUSS_POOL_SIZE`, `OPENGAUSS_POOL_MAX_OVERFLOW`, `OPENGAUSS_POOL_TIMEOUT`, `OPENGAUSS_POOL_RECYCLE` | URL `DATABASE_URL`; length `1536`; pool `0`, `30`, `3600` | URL, Integers | `config.py:749-788` | openGauss database. | Yes | As above |
| MariaDB Vector: `MARIADB_VECTOR_DB_URL`, `MARIADB_VECTOR_INITIALIZE_MAX_VECTOR_LENGTH`, `MARIADB_VECTOR_DISTANCE_STRATEGY`, `MARIADB_VECTOR_INDEX_M`, `MARIADB_VECTOR_POOL_SIZE`, `MARIADB_VECTOR_POOL_MAX_OVERFLOW`, `MARIADB_VECTOR_POOL_TIMEOUT`, `MARIADB_VECTOR_POOL_RECYCLE` | URL empty; length `1536`; `cosine`; M `8`; pool `0`, `30`, `3600` | URL, Text, Integers | `config.py:528-593` | MariaDB with vector support; the URL must use the `mariadb+mariadbconnector` driver, otherwise the store is marked unavailable (`config.py:581-593`). | Yes | As above |
| Pinecone: `PINECONE_API_KEY` (secret), `PINECONE_ENVIRONMENT`, `PINECONE_INDEX_NAME`, `PINECONE_DIMENSION`, `PINECONE_METRIC`, `PINECONE_CLOUD` | index `open-webui-index`; dimension `1536`; `cosine`; cloud `aws` | Text, Integer | `config.py:792-797` | Pinecone hosted index. | Yes | As above |
| Oracle 23ai: `ORACLE_DB_USE_WALLET`, `ORACLE_DB_USER`, `ORACLE_DB_PASSWORD` (secret), `ORACLE_DB_DSN`, `ORACLE_WALLET_DIR`, `ORACLE_WALLET_PASSWORD` (secret), `ORACLE_VECTOR_LENGTH`, `ORACLE_DB_POOL_MIN`, `ORACLE_DB_POOL_MAX`, `ORACLE_DB_POOL_INCREMENT` | wallet `false`; length `768`; pool `2`, `10`, `1` | Boolean, Text, Integers | `config.py:801-820` | Oracle Database 23ai vector search; start-up stops when the user, password or DSN (or the wallet settings) are missing (`config.py:814-820`). | Yes | As above |
| S3 Vectors: `S3_VECTOR_BUCKET_NAME`, `S3_VECTOR_REGION` | unset | Text | `config.py:825-826` | Amazon S3 vector bucket. | Yes | As above |
| Valkey: `VALKEY_URL`, `VALKEY_COLLECTION_PREFIX`, `VALKEY_INDEX_TYPE`, `VALKEY_DISTANCE_METRIC`, `VALKEY_HNSW_M`, `VALKEY_HNSW_EF_CONSTRUCTION`, `VALKEY_HNSW_EF_RUNTIME` | URL empty; prefix `open_webui`; `HNSW`, `COSINE`, `16`, `200`, `10` | Text, Integers (exit if invalid) | `config.py:829-835` | Valkey search module. | Yes | As above |

### 7.11 Storage Providers

Uploaded files go to `DATA_DIR/uploads` by default; a cloud provider can hold them instead. These variables are read in `config.py` but are environment-only (no `DEFAULT_CONFIG` key), and the provider object is created when `storage/provider.py` is imported (`storage/provider.py:338-356`). Keys are named only.

| Variable | Code default | Type | Read at | Effect | Restart | In depth |
|---|---|---|---|---|---|---|
| `STORAGE_PROVIDER` | `local` | Text: `local`, `s3`, `gcs`, `azure` | `config.py:148` | Where uploaded files are stored (`storage/provider.py:344-354`). Any other value stops start-up with `Unsupported storage provider: {storage_provider}`; the slim image accepts only `local` (section 10). Nothing in the code moves existing files when the provider changes (`storage/provider.py`). | Yes; all workers and replicas must agree | `files-uploads-and-storage.md` |
| `STORAGE_LOCAL_CACHE` | `true` | Boolean | `config.py:149` | With a cloud provider, files are first written to `DATA_DIR/uploads`; `false` removes that local copy after processing (`storage/provider.py:147`; `routers/files.py:97-108`). | Yes | As above |
| `S3_BUCKET_NAME` | unset | Text | `config.py:154` | Bucket for `STORAGE_PROVIDER=s3` (`storage/provider.py:137`). | Yes | As above |
| `S3_KEY_PREFIX` | unset (no prefix) | Text | `config.py:155` | Folder-like prefix for object names (`storage/provider.py:138`). | Yes | As above |
| `S3_REGION_NAME` | unset | Text | `config.py:153` | Region of the bucket (`storage/provider.py:121`, `:132`). | Yes | As above |
| `S3_ENDPOINT_URL` | unset (Amazon's endpoint) | Text (URL) | `config.py:156` | Endpoint for S3-compatible storage (`storage/provider.py:122`, `:133`). | Yes | As above |
| `S3_ACCESS_KEY_ID` | unset; set per environment | Text (secret) | `config.py:151` | Access key id. When it or the secret key is missing, the cloud library's default credentials are used (`storage/provider.py:118-134`). | Yes | As above |
| `S3_SECRET_ACCESS_KEY` | unset; set per environment | Text (secret) | `config.py:152` | Secret for the key above. | Yes | As above |
| `S3_USE_ACCELERATE_ENDPOINT` | `false` | Boolean | `config.py:157` | Uses S3 Transfer Acceleration (`storage/provider.py:109`). | Yes | As above |
| `S3_ADDRESSING_STYLE` | unset | Text | `config.py:158` | Path-style or virtual-host-style bucket addressing (`storage/provider.py:110`). | Yes | As above |
| `S3_ENABLE_TAGGING` | `false` | Boolean | `config.py:159` | Adds object tags derived from the upload to each stored file (`storage/provider.py:151-157`). | Yes | As above |
| `GCS_BUCKET_NAME` | unset | Text | `config.py:161` | Bucket for `STORAGE_PROVIDER=gcs` (`storage/provider.py:214`, `:225`). | Yes | As above |
| `GOOGLE_APPLICATION_CREDENTIALS_JSON` | unset; set per environment | JSON (secret) | `config.py:162` | Service-account credentials; when unset the library's default credentials are used (`storage/provider.py:216-224`). | Yes | As above |
| `AZURE_STORAGE_ENDPOINT` | unset | Text (URL) | `config.py:164` | Storage account endpoint for `STORAGE_PROVIDER=azure` (`storage/provider.py:278`). | Yes | As above |
| `AZURE_STORAGE_CONTAINER_NAME` | unset | Text | `config.py:165` | Blob container (`storage/provider.py:279`, `:289`). | Yes | As above |
| `AZURE_STORAGE_KEY` | unset; set per environment | Text (secret) | `config.py:166` | Account key; when unset the platform's managed identity is used (`storage/provider.py:280-288`). | Yes | As above |

### 7.12 Licence and Offline Mode

Whether MedIT GPT holds an enterprise licence, and which `LICENSE` §4 exception the deployment relies on, is **TO BE CONFIRMED** (ground truth, "Version and Identity"). How licence data is checked is security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca).

| Variable | Code default | Type | Read at | Effect | Restart | In depth |
|---|---|---|---|---|---|---|
| `LICENSE_KEY` | empty; set per environment | Text (secret) | `env.py:922` | Enterprise licence key. When set, start-up checks it in the background against the upstream licence service at `openwebui.com` addresses, so the key leaves the deployment (`main.py:372-374`; `utils/auth.py:89-136`). Returned licence details can replace the running product name and write branding files into the static folder (`utils/auth.py:76-106`). | Yes | `local-customisations-uoft-fork.md` *(planned)* |
| `LICENSE_BLOB_PATH` | `{DATA_DIR}/l.data` | Path | `env.py:925-928` | Optional offline licence file, read at import when it exists and used when the online check does not succeed (`utils/auth.py:138-139`). | Yes | As above |
| `LICENSE_PUBLIC_KEY` | empty | Text (key material) | `env.py:930-940` | Verification key for the offline licence file. A value that is not a valid public key stops start-up at import (`env.py:933-940`). | Yes | As above |
| `OFFLINE_MODE` | `false` | Boolean | `env.py:1201` | For deployments without internet access: sets `HF_HUB_OFFLINE=1`, turns the version check off (`env.py:1203-1205`), stops automatic model downloads for embedding, reranking and Whisper (`config.py:1014`, `:1041`, `:1566`; `retrieval/utils.py:1729-1730`, `:1757-1758`) and skips installing tool and function requirements (`utils/plugin.py:428-430`). | Yes | `rag-retrieval-embeddings-and-vector-stores.md` |
| `HF_HUB_OFFLINE` | not read by the application; **set** to `1` by `OFFLINE_MODE` | Text | `env.py:1204` (written) | Tells the Hugging Face libraries not to download anything (library behaviour). Not matched by the inventory pattern because the code writes it. | Yes | As above |
| `ENABLE_VERSION_UPDATE_CHECK` | `true` (forced off by `OFFLINE_MODE`) | Boolean | `env.py:1200` | Lets **Settings > About** and **Admin Settings > General** ask GitHub for the latest release; off, the current version is reported as the latest (`main.py:2594-2611`; `src/lib/components/chat/Settings/About.svelte:45`; `src/lib/components/admin/Settings/General.svelte:115`). A failed check logs `Version update check failed: {e}`. | Yes | `admin-settings-panels.md` |

### 7.13 Start Scripts and the Docker Image

These variables are read by `backend/start.sh` (the image's command, `Dockerfile:231`), `backend/dev.sh`, `open-webui serve` (`backend/open_webui/__init__.py`) or set by `ENV` lines in the `Dockerfile`. Several image values only **seed** persistent settings (marked "seed"): they matter on the first boot of an empty database and are ignored afterwards (section 1.1). Which start method production uses is **TO BE CONFIRMED**.

| Variable | Value or code default | Type | Read or set at | Effect | Restart | In depth |
|---|---|---|---|---|---|---|
| `PORT` | `8080` (`start.sh`, `dev.sh`; the image sets it, `Dockerfile:75`) | Integer | `backend/start.sh:33`; `backend/dev.sh:2` | Port uvicorn listens on (`backend/start.sh:110`); the image health check uses it (`Dockerfile:212`). `open-webui serve` takes `--port` instead (`__init__.py:36-39`). | Yes | `deployment-operations-and-logging.md` *(planned)* |
| `HOST` | `0.0.0.0` | Text | `backend/start.sh:34` | Address uvicorn listens on (`backend/start.sh:109`). | Yes | As above |
| `WEBUI_SECRET_KEY_FILE` | `.webui_secret_key` in `backend/` (the script changes to its own folder first, `backend/start.sh:16-17`) | Path | `backend/start.sh:31` | Where `start.sh` keeps a generated key when neither `WEBUI_SECRET_KEY` nor `WEBUI_JWT_SECRET_KEY` is set (`backend/start.sh:36-50`). In the image this is outside the data volume, so a recreated container generates a new key (section 5.4). | Only when no key is set | Section 5.4 |
| `FORWARDED_ALLOW_IPS` | `*` | Text | `backend/start.sh:74`, `:111`; `backend/dev.sh:3` | Which proxy addresses uvicorn trusts for client-address headers; `open-webui serve` always trusts all (`__init__.py:88`). The client address feeds the audit log and rate limits; settings here are security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca). | Yes | `backend-architecture-and-request-lifecycle.md` *(planned)* |
| `WEB_LOADER_ENGINE` | empty | Text | `backend/start.sh:14`, `:21` | With `playwright` and no `PLAYWRIGHT_WS_URL`, `start.sh` installs the Chromium browser at every container start (not in the slim image) (`backend/start.sh:21-27`). Also the seed of the persistent setting `web.loader.engine`; changing that setting on the admin screen does not make `start.sh` install the browser. | Yes | `web-search-and-web-loading.md` |
| `PLAYWRIGHT_WS_URL` | unset | Text (URL) | `backend/start.sh:22` | A remote browser; when set, no local browser is installed. Seed of `web.loader.playwright_ws_url`. The Playwright overlay sets both values (`docker-compose.playwright.yaml:8-10`). | Yes | As above |
| `USE_OLLAMA_DOCKER` | `false`; the image copies the `USE_OLLAMA` build argument (`Dockerfile:77`) | Text (`true`) | `backend/start.sh:14`, `:54`; `config.py:248` | `true` starts the bundled `ollama serve` (`backend/start.sh:54-57`) and, with `ENV=prod`, points the default Ollama address at `http://localhost:11434` (`config.py:253-258`). | Yes | `model-connections-openai-ollama-and-direct.md` |
| `K8S_FLAG` | empty | Text | `config.py:247` | Any value, with `ENV=prod`, points the default Ollama address at a Kubernetes service name (`config.py:253-262`). Seed-time only. | Seed only | As above |
| `LD_LIBRARY_PATH` | inherited | Text (library path list) | `backend/start.sh:63`; `__init__.py:54-74` | With `USE_CUDA_DOCKER=true`, both start methods add the PyTorch and cuDNN library folders; `open-webui serve` removes them again and sets `USE_CUDA_DOCKER=false` if CUDA does not work (`backend/start.sh:61-64`; `__init__.py:52-74`). | Yes | `rag-retrieval-embeddings-and-vector-stores.md` |
| `SPACE_ID`, `SPACE_HOST`, `ADMIN_USER_EMAIL`, `ADMIN_USER_PASSWORD` (secret) | unset | Text | `backend/start.sh:68-94` | Hugging Face Spaces hosting only: with an admin email and password, `start.sh` starts the server once, registers that admin, restarts, and sets `WEBUI_URL` from `SPACE_HOST`. Not relevant to MedIT GPT unless hosted there (**TO BE CONFIRMED**). | Yes | `deployment-operations-and-logging.md` *(planned)* |
| `PYTHONUNBUFFERED` | `1` in the image | Text | `Dockerfile:71` | Python writes log output immediately (runtime behaviour, not read by application code). | Yes | As above |
| `USE_CUDA_DOCKER_VER`, `USE_EMBEDDING_MODEL_DOCKER`, `USE_RERANKING_MODEL_DOCKER`, `USE_AUXILIARY_EMBEDDING_MODEL_DOCKER` | from the build arguments `USE_CUDA_VER` (`cu128`), `USE_EMBEDDING_MODEL` (`sentence-transformers/all-MiniLM-L6-v2`), `USE_RERANKING_MODEL` (empty), `USE_AUXILIARY_EMBEDDING_MODEL` (`TaylorAI/bge-micro-v2`) | Text | `Dockerfile:80-83` | Build-time only: choose the PyTorch build and the models downloaded into the image (`Dockerfile:102-104`, `:165-178`). Not read by `backend/open_webui` (searched). | Rebuild the image | As above |
| `OLLAMA_BASE_URL`, `OPENAI_API_BASE_URL` | `/ollama` and empty in the image | Text | `Dockerfile:86-87`; `config.py:240`, `:323` | Seeds of the persistent connection settings `ollama.base_urls` and `openai.api_base_urls`. In `prod`, `/ollama` is rewritten to a container address and then probed on ports 11434 and 12434 (`config.py:253-262`, `:265-293`). `docker-compose.yaml` sets `http://ollama:11434` (`docker-compose.yaml:24`). | Seed only | `model-connections-openai-ollama-and-direct.md` |
| `OPENAI_API_KEY`, `WEBUI_SECRET_KEY` | empty placeholders in the image; set per environment | Text (secret) | `Dockerfile:90-91`; `docker-compose.yaml:25` | The empty secret key makes `start.sh` generate one (section 5.4). `OPENAI_API_KEY` seeds `openai.api_keys` (`config.py:322`, `:336`). | Seed only (API key); see 7.3 (secret key) | Section 7.3 |
| `SCARF_NO_ANALYTICS`, `DO_NOT_TRACK`, `ANONYMIZED_TELEMETRY` | `true`, `true`, `false` in the image | Text | `Dockerfile:92-94` | Opt-outs for usage analytics in third-party libraries; not read by application code (library behaviour). The image also writes a placeholder Chroma telemetry id (`Dockerfile:130-131`). | Yes | As above |
| `WHISPER_MODEL`, `WHISPER_MODEL_DIR` | `base`; `/app/backend/data/cache/whisper/models` | Text, Path | `Dockerfile:98-99`; `config.py:1562`, `:1565` | `WHISPER_MODEL` seeds `audio.stt.whisper_model` (`config.py:3052`); `WHISPER_MODEL_DIR` is environment-only and holds the local speech model. | Seed only; directory needs restart | `audio-speech-to-text-and-text-to-speech.md` |
| `RAG_EMBEDDING_MODEL`, `RAG_RERANKING_MODEL` | from the build arguments | Text | `Dockerfile:102-103`; `config.py:1008`, `:1035` | Seeds of `rag.embedding_model` and `rag.reranking_model` (`config.py:2914`, `:2920`). The `Dockerfile` warns that changing the embedding model requires re-embedding documents (`Dockerfile:13`). | Seed only | `rag-retrieval-embeddings-and-vector-stores.md` |
| `AUXILIARY_EMBEDDING_MODEL`, `SENTENCE_TRANSFORMERS_HOME` | as built; `/app/backend/data/cache/embedding/models` | Text, Path | `Dockerfile:104-105` | See section 7.10. | Yes | Section 7.10 |
| `TIKTOKEN_ENCODING_NAME`, `TIKTOKEN_CACHE_DIR` | `cl100k_base`; `/app/backend/data/cache/tiktoken` | Text, Path | `Dockerfile:108-109`; `config.py:1060-1061` | The encoding seeds `rag.tiktoken_encoding_name` (`config.py:2927`); the cache folder is environment-only. The build argument `USE_TIKTOKEN_ENCODING_NAME` is declared but not used: the `ENV` line hard-codes the value (`Dockerfile:19`, `:108`). | Seed only; directory needs restart | As above |
| `HF_HOME` | `/app/backend/data/cache/embedding/models` | Path | `Dockerfile:112` | Hugging Face download cache (library behaviour). | Yes | As above |
| `HOME` | `/root` | Path | `Dockerfile:121` | Home folder of the container user. | Yes | `deployment-operations-and-logging.md` *(planned)* |
| `UV_LINK_MODE` | `copy` | Text | `Dockerfile:156` | Build-tool setting used while installing packages (`Dockerfile:155-156`). | Rebuild the image | As above |
| `WEBUI_BUILD_VERSION` | the `BUILD_HASH` build argument, default `dev-build` | Text | `Dockerfile:227-228` | Set in the image but read by nothing in the repository (searched for the name); see section 7.15. | Not applicable | Section 7.15 |
| Build arguments `USE_CUDA`, `USE_OLLAMA`, `USE_SLIM`, `USE_PERMISSION_HARDENING`, `USE_CUDA_VER`, `USE_EMBEDDING_MODEL`, `USE_RERANKING_MODEL`, `USE_AUXILIARY_EMBEDDING_MODEL`, `USE_TIKTOKEN_ENCODING_NAME`, `BUILD_HASH`, `UID`, `GID` | `false`, `false`, `false`, `false`, `cu128`, the models above, `dev-build`, `0`, `0` | Build-time | `Dockerfile:4-24` | Not runtime environment variables: they shape the image (GPU, bundled Ollama, slim, OpenShift permissions, user id). A slim build that also asks for CUDA or Ollama fails with the message listed in section 10 (`Dockerfile:137-138`). | Rebuild the image | As above |

### 7.14 Development-Only Switches

These matter on a developer's machine or at build time, not in a running production server. `ENV`, `FROM_INIT_PY` and the diagnostic logging switches are in sections 7.2 and 7.6.

| Variable | Code default | Type | Read at | Effect | Restart | In depth |
|---|---|---|---|---|---|---|
| `ENV` (front-end build) | unset | Text (`dev`) | `vite.config.ts:61` | Only when the front end is **built** with `ENV=dev` are the application's `console.log`, `console.debug` and `console.error` calls kept; otherwise they are removed from the bundle, so a production browser console shows few application messages. The image's build stage does not set `ENV` (`Dockerfile:27-47`). | Rebuild the front end | `frontend-architecture-routes-stores-and-i18n.md` *(planned)* |
| `WEBUI_BACKEND_URL` | `http://localhost:8080` | Text (URL) | `vite.config.ts:6` | Where the Vite development server (`npm run dev`, port 5173) forwards `/api`, `/ollama`, `/openai`, `/oauth` and `/ws` (`vite.config.ts:31-56`). | Restart `npm run dev` | `developer-tools-scripts-and-tests.md` *(planned)* |
| `npm_package_version` | set by npm from `package.json` | Text | `vite.config.ts:25` | Version number compiled into the front end (`APP_VERSION`). | Rebuild the front end | As above |
| `USE_SLIM` (front-end build) | unset; the image's build stage receives the build argument (`Dockerfile:29`) | Text (`true`) | `scripts/prepare-pyodide.js:236` | Prepares the in-browser Python runtime without bundled packages for the slim image (`scripts/prepare-pyodide.js:236-245`). | Rebuild the front end | As above |
| `HTTPS_PROXY`, `HTTP_PROXY`, `ALL_PROXY` (and lower-case forms) | unset | Text (proxy URL) | `scripts/prepare-pyodide.js:53-55` | Proxy used when `npm run dev` or `npm run build` downloads the Python runtime packages; only `http` and `https` proxies are supported (`scripts/prepare-pyodide.js:48-62`). | Not applicable | As above |
| `NODE_OPTIONS` | unset; the wheel build adds a larger memory limit (`hatch_build.py:21-23`) | Text | `hatch_build.py:21` | Node.js options for front-end builds; CLAUDE.md notes a large build may need more memory. | Not applicable | As above |

`backend/dev.sh` itself sets `CORS_ALLOW_ORIGIN` to the two local development origins and starts uvicorn with automatic reload; unlike `start.sh` it does not create a secret key, so `WEBUI_SECRET_KEY` must be exported first (`backend/dev.sh:1-3`; CLAUDE.md, "Commands"). `open-webui dev` also starts with reload (`__init__.py:95-110`).

### 7.15 Build Values, Scheduler Intervals and Everything Else

| Variable | Code default | Type | Read at | Effect | Restart | In depth |
|---|---|---|---|---|---|---|
| `APP_BUILD_HASH` | `dev-build` | Text | `vite.config.ts:26`; `svelte.config.js:26-27`; set by `Dockerfile:45` and `hatch_build.py:20` | Front-end build identifier shown as the tooltip on the version in **Settings > About** and **Admin Settings > General** (`src/lib/constants.ts:28`; `src/lib/components/chat/Settings/About.svelte:67`; `src/lib/components/admin/Settings/General.svelte:140`). When git is unavailable at build time it also names the front-end version that browsers poll every 60 seconds to detect a new release (`svelte.config.js:20-41`). | Rebuild the front end | `frontend-architecture-routes-stores-and-i18n.md` *(planned)* |
| `WEBUI_BUILD_HASH` (backend) | `dev-build` | Text | `env.py:958` | Printed in the start-up banner when not `dev-build` (`main.py:331`). The image sets `WEBUI_BUILD_VERSION`, which nothing reads, so in a stock image the backend value stays `dev-build` unless `WEBUI_BUILD_HASH` is set separately (`Dockerfile:227-228`). | Yes | Section 7.2 |
| `SCHEDULER_POLL_INTERVAL` | `10` (seconds), falling back to `AUTOMATION_POLL_INTERVAL` | Integer, **exits if invalid** | `utils/automations.py:53` | How often each worker looks for due automations and calendar alerts, plus up to 2 seconds of random jitter (`utils/automations.py:98-102`); also widens the calendar alert grace window (`utils/automations.py:550`). Section 8. | Yes | `automations-calendar-and-timers.md` |
| `AUTOMATION_POLL_INTERVAL` | `10` | Integer | `utils/automations.py:53` | Older name for the above, used only when `SCHEDULER_POLL_INTERVAL` is unset. | Yes | As above |
| `TIMER_POLL_INTERVAL` | `1` (second) | Integer, exits if invalid | `utils/automations.py:54` | How often due chat timers are checked; values below 1 still wait one second (`utils/automations.py:88-96`, `:126`). | Yes | As above |
| `CALENDAR_ALERT_LOOKAHEAD_MINUTES` | `10` | Integer, exits if invalid | `utils/automations.py:55` | Default window for upcoming-event alerts (`utils/automations.py:547`). The module's comment says 5; the code uses 10 (`utils/automations.py:15`). | Yes | As above |
| `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY` (backend) | unset | Text | not read by application code | Outbound HTTP sessions are created with `trust_env=True` (for example `utils/session_pool.py:72-76`; `main.py:2601`), so the standard proxy variables apply to provider, web-search and update-check calls (library behaviour). Whether production uses a proxy is **TO BE CONFIRMED**. | Yes | `model-connections-openai-ollama-and-direct.md` |

### 7.16 Cross-Reference: Environment-Only Switches Read in `config.py`

Most of the 651 names read in `config.py` seed persistent settings and belong to `configuration-persistent-settings-a-to-o.md` and `configuration-persistent-settings-r-to-w.md` *(both planned)*. About 171 of them feed no `DEFAULT_CONFIG` key and so behave like the variables in this document: read once at import, never stored, a restart needed for every change (method in section 14). Those already catalogued here are `STATIC_DIR` (7.2), `ENABLE_PASSWORD_AUTH`, `CORS_ALLOW_ORIGIN` and `CORS_ALLOW_CUSTOM_SCHEME` (7.3), `THREAD_POOL_SIZE` and `THREAD_POOL_THREAD_NAME_PREFIX` (7.8), `VECTOR_DB` and every vector-store setting (7.10), the storage settings (7.11), and `K8S_FLAG`, `USE_OLLAMA_DOCKER`, `WHISPER_MODEL_DIR` and `TIKTOKEN_CACHE_DIR` (7.13). The rest follow.

| Variable | Code default | Type | Read at | Effect | Restart | In depth |
|---|---|---|---|---|---|---|
| `ENABLE_PERSISTENT_CONFIG` | `True` | Boolean | `config.py:3231` | Off, no setting is read from or written to the `config` table: every key follows the environment and an admin edit changes only the memory of the worker that saved it (`models/config.py:196-206`; section 1.1). | Yes | `configuration-persistent-settings-a-to-o.md` *(planned)* |
| `ENABLE_OAUTH_PERSISTENT_CONFIG` | `False` | Boolean | `config.py:3232` | On, the `oauth.*` keys are stored like other settings; off (the default) they follow the environment and admin edits to them last only until restart (`models/config.py:133-138`; ground truth). | Yes | `sso-oauth-oidc-and-scim.md` |
| `ENABLE_ADMIN_EXPORT` | `True` | Boolean | `config.py:2082` | Allows admins to export all chats and download the SQLite database file; off, those requests are refused with `ACCESS_PROHIBITED` (`routers/utils.py:73-78`; `routers/chats.py:1051`; `main.py:2373`). | Yes | `admin-settings-panels.md` |
| `BYPASS_ADMIN_ACCESS_CONTROL` | `True` (falls back to `ENABLE_ADMIN_WORKSPACE_CONTENT_ACCESS`) | Boolean | `config.py:2086-2092` | Admins see every workspace item regardless of sharing, and skip model access checks (ground truth; `functions.py:289`; `routers/skills.py:46`). | Yes | `users-groups-roles-and-permissions.md` |
| `ENABLE_ADMIN_WORKSPACE_CONTENT_ACCESS` | `True` | Boolean | `config.py:2084`, `:2089` | Older name, used as the default of `BYPASS_ADMIN_ACCESS_CONTROL`. | Yes | As above |
| `ENABLE_ADMIN_ANALYTICS` | `True` | Boolean | `config.py:2094` | Mounts the admin analytics API and shows the Analytics page (`main.py:878`, `:2375`; CLAUDE.md). | Yes | `evaluations-feedback-and-analytics.md` |
| `CUSTOM_NAME` | empty | Text | `config.py:193` | Legacy branding path: when set, start-up fetches a name, logo and splash image from the upstream `api.openwebui.com` service, writes them into the static folder and replaces the product name (`config.py:190-223`; `main.py:538`). On this fork it would override **MedIT GPT**; covered by the licence branding comments (`config.py:190-192`). | Yes | `local-customisations-uoft-fork.md` *(planned)* |
| `OAUTH_GROUPS_SEPARATOR` | `;` | Text | `config.py:2593` | Separator used to split a text groups claim from the identity provider (`utils/oauth.py:1666-1667`). | Yes | `sso-oauth-oidc-and-scim.md` |
| `OAUTH_AUTHORIZE_PARAMS`, `GOOGLE_OAUTH_AUTHORIZE_PARAMS` | empty | JSON object; anything else is ignored with a warning | `config.py:2623-2635`; `config.py:2503-2513` | Extra parameters added to the provider's sign-in redirect, for all providers and for Google (`utils/oauth.py:1867-1868`; `config.py:2665`). | Yes | As above |
| `OAUTH_ACCESS_TOKEN_REQUEST_INCLUDE_CLIENT_ID` | `False` | Boolean | `config.py:2617-2619` | Sends the client id in the token request, for providers that require it (`utils/oauth.py:1886`). | Yes | As above |
| `IFRAME_CSP` | empty | Text (content security policy) | `config.py:1731` | Policy injected into artifacts and file previews shown in frames (`main.py:2437`; `src/lib/components/chat/Artifacts.svelte:251`; `src/lib/components/chat/FileNav/FilePreview.svelte:403`). | Yes | `chat-composer-and-message-display.md` |
| `CODE_INTERPRETER_BLOCKED_MODULES` | empty | List | `config.py:462-464` | Python modules the code interpreter refuses to import (`tools/builtin.py:664-671`; `utils/middleware.py:6373`). | Yes | `code-execution-and-interpreter.md` |
| `TERMINAL_PROXY_HEADERS` | `{}` | JSON, silent fallback | `config.py:400-403` | Extra headers sent by the terminal proxy (`routers/terminals.py:214`). | Yes | `workspace-tools-tool-servers-mcp-and-terminals.md` |
| `ONEDRIVE_CLIENT_ID`, `ONEDRIVE_CLIENT_ID_PERSONAL`, `ONEDRIVE_CLIENT_ID_BUSINESS`, `ENABLE_ONEDRIVE_PERSONAL`, `ENABLE_ONEDRIVE_BUSINESS` | empty; the two switches `True` but effective only with a client id | Text, Boolean | `config.py:852-861` | Application ids and switches for the OneDrive personal and business file pickers (`main.py:2381-2382`, `:2427-2428`). The overall OneDrive switch is a persistent setting. | Yes | `files-uploads-and-storage.md` |
| `ENABLE_KNOWLEDGE_FILE_RETENTION` | `False` | Boolean | `config.py:985` | Keeps the underlying files when they are removed from a knowledge base or the knowledge base is deleted (`routers/knowledge.py:1618`, `:1825`, `:2014`). | Yes | `knowledge-bases.md` |
| `RAG_FILE_CONTENT_SEARCH_MAX_CHARS` | `67108864` | Integer, exits if invalid | `config.py:987` | Characters of each file searched when knowledge-base files are searched by content (`models/knowledge.py:407`). | Yes | As above |
| `RAG_EMBEDDING_MODEL_AUTO_UPDATE`, `RAG_RERANKING_MODEL_AUTO_UPDATE` | `True` (forced off by `OFFLINE_MODE`) | Boolean | `config.py:1013-1015`, `:1040-1042` | Download newer copies of the local embedding and reranking models when they load (`routers/retrieval.py:152`, `:1660`). | Yes | `rag-retrieval-embeddings-and-vector-stores.md` |
| `RAG_EMBEDDING_MODEL_TRUST_REMOTE_CODE`, `RAG_RERANKING_MODEL_TRUST_REMOTE_CODE` | `True` | Boolean | `config.py:1017`, `:1044` | Let those models run code shipped with the model download (`routers/retrieval.py:162`, `:1669`). Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca). | Yes | As above |
| `RAG_EMBEDDING_QUERY_PREFIX`, `RAG_EMBEDDING_CONTENT_PREFIX`, `RAG_EMBEDDING_PREFIX_FIELD_NAME` | unset | Text | `config.py:1027-1031` | Text prepended to queries and to document content before embedding, and the request field that carries it for external engines (`routers/retrieval.py:1884`, `:3110`; `retrieval/utils.py:909-910`). | Yes | As above |
| `ENABLE_LOCAL_WEB_FETCH`, `ENABLE_RAG_LOCAL_WEB_FETCH` (older name), `WEB_FETCH_FILTER_LIST` | `False`; empty | Boolean; List | `config.py:1109-1117`, `:1143-1147` | Off, fetching pages on non-public network addresses is refused; the filter list adds hosts to a built-in block list (`retrieval/web/utils.py:120-133`). Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca). | Yes | `web-search-and-web-loading.md` |
| `IMAGE_AUTO_SIZE_MODELS_REGEX_PATTERN`, `IMAGE_URL_RESPONSE_MODELS_REGEX_PATTERN`, `ENABLE_OPENAI_IMAGE_EDIT_NORMALIZATION` | `^gpt-image`, `^gpt-image`, `true` | Text (pattern), Boolean | `config.py:1358`, `:1361`, `:1533` | Which image models accept the automatic size and how their responses are read, and whether OpenAI image-edit uploads are normalized (`routers/images.py:279-284`, `:646`, `:995`, `:1005-1010`). | Yes | `image-generation-and-editing.md` |
| `WHISPER_COMPUTE_TYPE`, `WHISPER_MODEL_AUTO_UPDATE`, `WHISPER_VAD_FILTER`, `WHISPER_MULTILINGUAL`, `WHISPER_LANGUAGE` | `int8`, off (forced off by `OFFLINE_MODE`), `False`, `False`, empty | Text, Boolean | `config.py:1564-1572` | Local Whisper speech-to-text: numeric precision, model updates, silence filtering, multilingual mode and a fixed language (`routers/audio.py:227`, `:307`, `:682-684`, `:970`). | Yes | `audio-speech-to-text-and-text-to-speech.md` |
| `ELEVENLABS_API_BASE_URL` | `https://api.elevenlabs.io` | Text (URL) | `config.py:1578` | Address of the ElevenLabs text-to-speech service (`routers/audio.py:458`, `:1384`, `:1446`). | Yes | As above |

### 7.17 Coverage Summary

| Group | Names | Where |
|---|---|---|
| Inventory scope: `os.getenv`/`os.environ.get` reads outside `config.py` (`tools/inventory.md`) | 238 | Sections 7.2 to 7.15 |
| Reads the inventory pattern does not catch: 14 security-header names read through a lookup table, five knowledge-tool limits read through a helper, and `HF_HUB_OFFLINE`, which the code writes | 20 | Sections 7.3, 7.9, 7.12 |
| Environment-only names read in `config.py` (one, `STATIC_DIR`, is also in the inventory scope) | 171 (170 new) | Sections 7.3, 7.8, 7.10, 7.11, 7.13, 7.16 |
| Names used only by the start scripts, the image, the front-end build or outbound-proxy handling | 29 | Sections 7.13 to 7.15 |
| **Distinct variables catalogued** | **457** | |
| Docker build arguments (not runtime variables) | 12 | Section 7.13 |

`python3 knowledgebase/tools/check_coverage.py` reported the inventory scope complete (238 of 238) on 2026-10-10. Its `config.py` scope (651 names) is shared with the two persistent-settings catalogues, which own the seed variables and were not yet written on that date.

## 8. Cron Jobs and Background Processes

There is no crontab and no separate worker process: every periodic job is an asyncio task inside each uvicorn worker, started by `lifespan` (CLAUDE.md, "Startup Order and Background Jobs"). The table lists the background behaviour that environment variables control. Each worker runs its own copy of every loop; where a loop must run once across workers, a Redis lock or a database claim decides which worker does the work.

| Loop or task | Started when | How often | Variables that govern it | Source |
|---|---|---|---|---|
| Scheduler (`scheduler_worker_loop`) | Always, in every worker (`main.py:402-404`) | Due chat timers every `TIMER_POLL_INTERVAL` seconds (at least 1); due automations and calendar alerts every `SCHEDULER_POLL_INTERVAL` seconds plus 0 to 2 seconds of jitter, when the persistent switches `automations.enable` and `calendar.enable` are on. It logs `Scheduler worker started (timer poll interval: {TIMER_POLL_INTERVAL}s, scheduler poll interval: {SCHEDULER_POLL_INTERVAL}s)` at start. | `TIMER_POLL_INTERVAL`, `SCHEDULER_POLL_INTERVAL` (or `AUTOMATION_POLL_INTERVAL`), `CALENDAR_ALERT_LOOKAHEAD_MINUTES` | `utils/automations.py:53-55`, `:69-126`, `:537-553` |
| Usage-pool clean-up (`periodic_usage_pool_cleanup`) | Always (`main.py:400`) | Every 3 seconds removes "model in use" entries not refreshed for 3 seconds. With `WEBSOCKET_MANAGER=redis` only the worker holding the lock `{REDIS_KEY_PREFIX}:usage_cleanup_lock` works; the others retry after half to all of `WEBSOCKET_REDIS_LOCK_TIMEOUT`. | `WEBSOCKET_MANAGER`, `WEBSOCKET_REDIS_LOCK_TIMEOUT`, `REDIS_KEY_PREFIX` | `socket/main.py:128`, `:163-170`, `:266-308` |
| Session-pool clean-up (`periodic_session_pool_cleanup`) | Always (`main.py:401`) | Removes websocket session entries unseen for four heartbeat intervals (at least 120 seconds; 120 when `WEBSOCKET_HEARTBEAT_INTERVAL` is unset), sweeping at that same interval, and logs `Reaping {n} orphaned session(s) from the session pool`. One worker at a time under Redis. | `WEBSOCKET_HEARTBEAT_INTERVAL`, `WEBSOCKET_MANAGER`, `WEBSOCKET_REDIS_LOCK_TIMEOUT` | `socket/main.py:129`, `:174-181`, `:212-263` |
| Task command listener (`redis_task_command_listener`) | When a Redis client exists (`REDIS_URL` or Sentinel hosts) (`main.py:390-393`) | Listens on `{REDIS_KEY_PREFIX}:tasks:commands` so a "stop" pressed on one worker reaches the worker running the task; reconnects after 1 to 30 seconds. | `REDIS_URL`, `REDIS_SENTINEL_HOSTS`, `REDIS_KEY_PREFIX` | `tasks.py:23-66` |
| Task heartbeat (`redis_task_heartbeat`) | With Redis and `REDIS_TASK_TTL` above 0 (`main.py:394-395`) | Every `REDIS_TASK_TTL` / 4 seconds renews the expiry of this worker's running tasks to `REDIS_TASK_TTL`, so tasks of a crashed worker disappear. | `REDIS_TASK_TTL` | `tasks.py:69-80` |
| Websocket event listener (`redis_event_listener`) | Only with `WEBSOCKET_MANAGER=redis` (`main.py:397-398`) | Continuous; reconnects on failure. | `WEBSOCKET_MANAGER`, `WEBSOCKET_REDIS_URL` | `socket/main.py:963-990` |
| Socket.IO keep-alive | Library-managed, per connection | Ping every `WEBSOCKET_SERVER_PING_INTERVAL` seconds; drop after `WEBSOCKET_SERVER_PING_TIMEOUT` seconds without a reply. | As named | `socket/main.py:107-108`, `:121-122` |
| Licence check | Once per start-up, in the background, when `LICENSE_KEY` is set | One request to the upstream licence service. | `LICENSE_KEY` | `main.py:372-374` |
| Tool and function requirement installation | Once per start-up, **blocking** before the server is ready | Installs the packages listed by stored tools and functions; skipped with `ENABLE_PLUGINS` off, `ENABLE_PIP_INSTALL_FRONTMATTER_REQUIREMENTS` off or `OFFLINE_MODE` on. | `ENABLE_PLUGINS`, `ENABLE_PIP_INSTALL_FRONTMATTER_REQUIREMENTS`, `PIP_OPTIONS`, `PIP_PACKAGE_INDEX_OPTIONS`, `OFFLINE_MODE` | `main.py:385-388`; `utils/plugin.py:422-442`, `:461-463` |
| Start-up actions that repeat at **every** boot | Each start | `RESET_CONFIG_ON_START` wipes stored settings; `SAFE_MODE` switches every function off; the admin bootstrap runs while the user table is empty. | `RESET_CONFIG_ON_START`, `SAFE_MODE`, `WEBUI_ADMIN_EMAIL`, `WEBUI_ADMIN_PASSWORD` | `main.py:363-364`, `:377-383` |
| Metrics export | With `ENABLE_OTEL` and `ENABLE_OTEL_METRICS` | Every `OTEL_METRICS_EXPORT_INTERVAL_MILLIS` milliseconds (library-managed reader). | As named | `utils/telemetry/metrics.py:103-118` |
| Browser update check | In each open browser tab | Every 60 seconds the front end compares its build version with the server's and offers a reload. | `APP_BUILD_HASH` at build time | `svelte.config.js:20-41` |

Several variables act **at request time** rather than in the background: `DATABASE_USER_ACTIVE_STATUS_UPDATE_INTERVAL` throttles "last active" writes as requests arrive (`models/users.py:771`); `REDIS_RESPONSE_STREAM_TTL` is an expiry set on each streamed answer (`tasks.py:217-221`); the Amazon RDS token is refreshed only when a new database connection is opened after 14 minutes (`internal/db.py:166`, `:190-202`); the audit log rotates when it reaches `AUDIT_LOG_FILE_ROTATION_SIZE`, not on a schedule (`utils/logger.py:202`).

## 9. Notifications and Emails

None of the variables in this catalogue sends email; the backend has no mail-sending code (ground truth, "Contacts That Exist in the Repository"; searched `backend/open_webui` for SMTP and mail calls). Environment variables affect notifications only indirectly:

- **Product name in notifications and webhooks.** In-app notifications and outgoing webhook payloads are labelled with the running product name, `app.state.WEBUI_NAME` (`utils/notifications.py:398-402`; `events.py:1034-1038`), which comes from `WEBUI_NAME` (default `MedIT GPT`) unless `CUSTOM_NAME` or licence data replaces it (sections 7.12 and 7.16).
- **Delivery across workers.** Socket notifications reach a user only through the worker holding that user's connection unless `WEBSOCKET_MANAGER=redis` shares rooms between workers (section 7.5).
- **Calendar alerts.** `CALENDAR_ALERT_LOOKAHEAD_MINUTES` and `SCHEDULER_POLL_INTERVAL` set how early and how promptly event alerts are sent (section 8).
- **System events.** Every published system event carries the worker's `INSTANCE_ID` (section 7.2).
- Webhook addresses and notification targets are persistent settings or per-user data, not environment variables (`notifications-webhooks-events-and-banners.md`).

## 10. Error, Warning and Notice Messages (Verbatim)

Messages caused by missing or invalid environment values. "Start-up stop" means the process exits while importing, so the service never becomes ready and the container restarts or stays down; the text appears in the server log (standard output or standard error). Lines logged at INFO level while `env.py` and `config.py` are imported may be missing when `GLOBAL_LOG_LEVEL` is unset, because Python's logging is configured only later (`main.py:284`; section 5.2); WARNING and ERROR lines still appear. File paths are relative to `backend/open_webui/` unless they start with `backend/` or name a root file. End users cannot fix any of these; the user action is to report the problem.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `WEBUI_SECRET_KEY is not set. It is a hard requirement when authentication is enabled.` (followed by three lines naming `start.sh`, `start_windows.bat` and `open-webui serve`, and a link to the upstream documentation) | Start-up stop | `env.py:780-788` | `WEBUI_AUTH` on and the secret key empty: the server was started without the supported scripts, or `start.sh` was given only the deprecated `WEBUI_JWT_SECRET_KEY` (section 7.3) | Report that the service is down | Escalate to the platform maintainer with the time of the failed start |
| `WEBUI_SECRET_KEY_LENGTH must be a positive integer` | Start-up stop (`open-webui serve`) | `__init__.py:44-46` | `WEBUI_SECRET_KEY_LENGTH` below 1 when a key file must be generated | As above | As above |
| `WEBUI_SECRET_KEY_LENGTH must be a positive integer.` | Start-up stop (`start.sh`) | `backend/start.sh:41-43` | The same, under `start.sh`, for any value that is not a positive whole number | As above | As above |
| `DATABASE_PASSWORD is required when using sqlite+sqlcipher:// URLs` | Start-up stop | `internal/db.py:289-292` | An encrypted SQLite URL without `DATABASE_PASSWORD` | As above | As above; note SQLCipher is unusable in v0.11.4 anyway (next row) |
| `sqlite+sqlcipher:// URLs are not supported with async engine. Use standard sqlite:// or postgresql:// instead.` | Start-up stop | `internal/db.py:244-248` | Any `sqlite+sqlcipher://` database URL (ground truth) | As above | As above |
| `Slim requires SQLite or PostgreSQL for DATABASE_URL. Use the standard image for other databases.` | Start-up stop (slim image) | `internal/db.py:146-150` | Slim image with another database type | As above | As above |
| `AWS RDS IAM authentication requires the standard image. Slim supports PostgreSQL database credentials.` | Start-up stop (slim image) | `internal/db.py:151-154` | `DATABASE_ENABLE_IAM_TOKEN_AUTH=true` in the slim image | As above | As above |
| `DATABASE_ENABLE_IAM_TOKEN_AUTH is only supported for PostgreSQL databases` | Start-up stop | `internal/db.py:170-171` | Token authentication switched on for a non-PostgreSQL URL | As above | As above |
| `DATABASE_ENABLE_IAM_TOKEN_AUTH requires a database host and user` | Start-up stop | `internal/db.py:172-173` | Token authentication with a URL lacking host or user | As above | As above |
| `AWS RDS IAM token auth not applied to {url}: the token is issued for {user}@{host}:{port}, so this connection uses the password from its own URL` | Log warning | `internal/db.py:222-229` | A second database (for example a vector store) on another host while token authentication is on | None | Informational for the maintainer |
| `Invalid scheme in CORS_ALLOW_ORIGIN: '{origin}'. Only 'http' and 'https' and CORS_ALLOW_CUSTOM_SCHEME are allowed.` | Start-up stop | `config.py:2114-2122`, `:2146-2147` | An origin in `CORS_ALLOW_ORIGIN` with another scheme (often a typing error, or a comma used instead of `;`) | Report that the service is down | Escalate with the time of the failed start |
| `Invalid URL structure in CORS_ALLOW_ORIGIN: '{origin}'.` | Start-up stop | `config.py:2124-2126` | An origin without a host name | As above | As above |
| `WARNING: CORS_ALLOW_ORIGIN IS SET TO '*' - NOT RECOMMENDED FOR PRODUCTION DEPLOYMENTS.` | Start-up warning | `config.py:2141-2142` | `CORS_ALLOW_ORIGIN` left at its default | None | Confirm with the maintainer whether production restricts origins (section 14) |
| `THREAD_POOL_SIZE is not a valid integer: {THREAD_POOL_SIZE}. Defaulting to None.` | Start-up warning | `config.py:2106-2111` | A non-numeric `THREAD_POOL_SIZE` | None | Report to the maintainer |
| `Invalid WEBSOCKET_REDIS_OPTIONS, defaulting to socket_timeout=None` | Start-up warning | `env.py:486-491` | `WEBSOCKET_REDIS_OPTIONS` is not valid JSON | None | Report to the maintainer |
| `Invalid PASSWORD_VALIDATION_REGEX_PATTERN: {e}` | Start-up error (log); the default rule is used | `env.py:822-827` | A password pattern that does not compile | None | Report to the maintainer |
| `SSL CA bundle path does not exist: {path}, ignoring` | Start-up warning | `env.py:563-568` | `AIOHTTP_CLIENT_SSL_CERT_FILE` or a TLS variable names a missing file | Connections to internal services may then fail certificate checks | Report to the maintainer with the failing feature |
| `Using custom SSL CA bundle: {path}` | Log info | `env.py:569-570` | A CA bundle was loaded | None | Confirms the bundle is in use |
| `SCIM is enabled but SCIM_AUTH_PROVIDER is not set. Set SCIM_AUTH_PROVIDER to the OAuth provider name (e.g. 'microsoft', 'oidc') to enable externalId storage.` | Start-up warning | `env.py:911-916` | `ENABLE_SCIM` on without `SCIM_AUTH_PROVIDER` | None | Report to the maintainer if provisioning misbehaves |
| `SCIM_AUTH_PROVIDER environment variable is required when SCIM is enabled` | HTTP 500 to the identity provider's SCIM client | `routers/scim.py:306-316` | A SCIM request that needs the provider while `SCIM_AUTH_PROVIDER` is unset | None (machine-to-machine) | Escalate to the maintainer and the identity team |
| `OAUTH_SESSION_TOKEN_ENCRYPTION_KEY is not set` | Start-up stop | `models/oauth_sessions.py:66-70`, `:344` | The session-token key resolves to an empty value (for example, sign-in switched off and no secret key) | Report that the service is down | Escalate |
| `Error initializing Fernet with provided key: {e}` | Start-up error, then stop | `utils/oauth.py:252-262` | `OAUTH_CLIENT_INFO_ENCRYPTION_KEY` (or the secret key it defaults to) cannot be used as a key | As above | Escalate; security-sensitive |
| `Failed to decrypt valves: {error}` | Log warning; the valves read as empty | `utils/valves.py:27-39` | Valves saved with `ENABLE_VALVE_ENCRYPTION` on can no longer be read, for example after the secret key changed | A tool or function behaves as if unconfigured | Escalate to the maintainer; security-sensitive |
| `Pgvector requires setting PGVECTOR_DB_URL or using Postgres with vector extension as the primary database.` | Start-up stop | `config.py:649-652` | `VECTOR_DB=pgvector` without a PostgreSQL URL | Report that the service is down | Escalate |
| `PGVECTOR_INITIALIZE_MAX_VECTOR_LENGTH is set to {PGVECTOR_INITIALIZE_MAX_VECTOR_LENGTH}, which exceeds the 2000 dimension limit of the 'vector' type. Set PGVECTOR_USE_HALFVEC=true to enable the 'halfvec' type required for high-dimensional embeddings.` | Start-up stop | `config.py:656-663` | A vector length over 2000 without half-vectors | As above | As above |
| `PGVECTOR_PGCRYPTO is enabled but PGVECTOR_PGCRYPTO_KEY is not set. Please provide a valid key.` | Start-up stop | `config.py:668-669` | pgcrypto on without its key | As above | As above |
| `VECTOR_LENGTH {VECTOR_LENGTH} does not match existing vector column dimension {db_vector_length}. Cannot change vector size after initialization without migrating the data.` | Start-up stop, logged as `Error during initialization: {e}` | `retrieval/vector/dbs/pgvector.py:315-320`, `:167-170` | `PGVECTOR_INITIALIZE_MAX_VECTOR_LENGTH` changed after the pgvector table was created | As above | As above |
| `Oracle23ai requires setting ORACLE_DB_USER, ORACLE_DB_PASSWORD, and ORACLE_DB_DSN.` | Start-up stop | `config.py:814-816` | `VECTOR_DB=oracle23ai` with missing connection details | As above | As above |
| `Oracle23ai requires setting ORACLE_WALLET_DIR and ORACLE_WALLET_PASSWORD when using wallet authentication.` | Start-up stop | `config.py:817-820` | Wallet authentication without the wallet settings | As above | As above |
| `Unsupported vector type: {vector_type}` | Start-up stop | `retrieval/vector/factory.py:96-100` | `VECTOR_DB` is not one of the supported names | As above | As above |
| `Slim requires PostgreSQL/pgvector for vector storage. Set VECTOR_DB=pgvector and PGVECTOR_DB_URL, or use the standard image.` | HTTP 503 when documents or memories are used | `retrieval/vector/factory.py:20-24` | Slim image with another `VECTOR_DB` | Report the failing upload or search | Escalate |
| `Configure PGVECTOR_DB_URL for remote vector storage.` | HTTP 503 | `retrieval/vector/factory.py:113-114` | Slim image with pgvector but no PostgreSQL URL | As above | As above |
| `Unable to connect to configured vector database ({VECTOR_DB}): {exc}` | HTTP 503 | `retrieval/vector/factory.py:115-122` | Slim image whose vector store cannot be reached | As above | As above |
| `Configure CHROMA_HTTP_HOST: embedded Chroma is unavailable in slim.` | HTTP 503 | `retrieval/vector/dbs/chroma.py:34-35` | Slim image with Chroma and no server | As above | As above |
| `Unsupported storage provider: {storage_provider}` | Start-up stop | `storage/provider.py:351-356` | `STORAGE_PROVIDER` is not `local`, `s3`, `gcs` or `azure` | Report that the service is down | Escalate |
| `Slim requires local file storage. Set STORAGE_PROVIDER=local, or use the standard image to access cloud storage.` | Start-up stop (slim image) | `storage/provider.py:338-342` | Slim image with cloud storage | As above | As above |
| `invalid literal for int() with base 10: '{value}'` (Python's own text) | Start-up stop | for example `env.py:879`, `:890`, `:1283`; `utils/automations.py:53-55`; `config.py:514` | A non-numeric value in a variable marked "exits if invalid" in section 7 | As above | Escalate with the variable name if the log shows it |
| `CUDA unavailable (USE_CUDA_DOCKER=true), falling back to CPU: {exc}` | Start-up error (log); the server continues on the CPU | `env.py:51-61`, `:129-131` | The GPU image cannot use the GPU | Slower local models | Report to the maintainer |
| `Error when testing CUDA but USE_CUDA_DOCKER is true. Resetting USE_CUDA_DOCKER to false and removing LD_LIBRARY_PATH modifications: {e}` | Start-up notice (`open-webui serve`) | `__init__.py:62-74` | The same under `open-webui serve` | As above | As above |
| `Frontend build directory not found at '{FRONTEND_BUILD_DIR}'. Serving API only.` | Start-up warning | `main.py:3066-3076` | `FRONTEND_BUILD_DIR` points at a missing folder | The site shows no interface (API only) | Escalate |
| `Invalid audit level: {AUDIT_LOG_LEVEL}. Error: {e}` | Start-up error (log); auditing stays off | `main.py:796-800` | `AUDIT_LOG_LEVEL` is not `NONE`, `METADATA`, `REQUEST` or `REQUEST_RESPONSE` | None | Report to the maintainer if an audit trail is expected *Corrected 2026-10-11: auditing does not simply stay off; this log call itself fails, because `logger` in `backend/open_webui/main.py` is the module `open_webui.utils.logger` (`:211`), which has no `error` attribute, so loading the app stops with an `AttributeError` and the server does not start (verified in the main loop; confirm in a test environment).* |
| `Failed to initialize audit log file handler: {str(e)}` | Log error; no audit file is written | `utils/logger.py:197-209` | `AUDIT_LOGS_FILE_PATH` cannot be written | None | As above |
| `Both AUDIT_INCLUDED_PATHS and AUDIT_EXCLUDED_PATHS are set. AUDIT_INCLUDED_PATHS (whitelist) takes precedence.` | Start-up warning | `utils/audit.py:156-160` | Both audit path lists set | None | Informational |
| `GOOGLE_OAUTH_AUTHORIZE_PARAMS must be a JSON object, ignoring` / `GOOGLE_OAUTH_AUTHORIZE_PARAMS is not valid JSON, ignoring` | Start-up warning | `config.py:2505-2513` | Malformed Google sign-in parameters | Google sign-in may behave unexpectedly | Report to the maintainer |
| `OAUTH_AUTHORIZE_PARAMS must be a JSON object, ignoring` / `OAUTH_AUTHORIZE_PARAMS is not valid JSON, ignoring` | Start-up warning | `config.py:2625-2633` | Malformed sign-in parameters | Single sign-on may behave unexpectedly | Report to the maintainer |
| `ENABLE_PLUGINS is disabled, skipping tool and function dependencies.` | Log info | `utils/plugin.py:461-463` | `ENABLE_PLUGINS` off | Tools and functions are unavailable | Confirms the switch is off |
| `ENABLE_PIP_INSTALL_FRONTMATTER_REQUIREMENTS is disabled, skipping installation of requirements.` | Log info | `utils/plugin.py:424-425` | Requirement installation switched off | A tool may fail for a missing package | Report to the maintainer |
| `Offline mode enabled, skipping installation of requirements.` | Log info | `utils/plugin.py:428-429` | `OFFLINE_MODE` on | As above | As above |
| `Version update check failed: {e}` | Log warning | `main.py:2595-2612` | `ENABLE_VERSION_UPDATE_CHECK` on and GitHub unreachable | None | Informational |
| `You can't turn off authentication because there are existing users. If you want to disable WEBUI_AUTH, make sure your web interface doesn't have any existing users and is a fresh installation.` | HTTP 400 at sign-in | `routers/auths.py:788-801`; `constants.py:67` | `WEBUI_AUTH=False` on a database that already has users | Report it | Escalate; security-sensitive |
| `Your provider has not provided a trusted header. Please contact your administrator for assistance.` | HTTP 400 at sign-in | `routers/auths.py:732-735`; `constants.py:63-65` | `WEBUI_AUTH_TRUSTED_EMAIL_HEADER` set but the request arrived without that header (the proxy is bypassed or misconfigured) | Report it with the address used | Escalate with the time and the URL used |
| `The requested action has been restricted as a security measure.` | HTTP 403 (sign-in) or 400 (password change) | `routers/auths.py:486-490`, `:724-728`, `:393-395`; `constants.py:73` | `ENABLE_PASSWORD_AUTH` off, or a password change while trusted-header sign-in is on | Use the organization's sign-in method | Confirm the expected sign-in method with the maintainer |
| `An internal error occurred during signup.` (the log shows `Signup error: Unsupported PASSWORD_HASH_ALGORITHM: {PASSWORD_HASH_ALGORITHM}`) | HTTP 500 | `routers/auths.py:948-952`; `utils/auth.py:187` | `PASSWORD_HASH_ALGORITHM` is neither `bcrypt` nor `argon2` (other sign-up failures show the same text) | Report it | Escalate with the time of the attempt |
| `Uh-oh! The password you entered is too long. Please make sure your password is less than 72 bytes long.` | Error on sign-up or password change | `utils/auth.py:190-195`; `constants.py:48-50` | `PASSWORD_HASH_ALGORITHM=bcrypt` (the default) and a password over 72 bytes | Choose a shorter password | None |
| `The password does not meet the required validation criteria.` | Error on sign-up or password change | `utils/auth.py:197-199`; `constants.py:114` | `ENABLE_PASSWORD_VALIDATION` on, the password fails the rule, and no `PASSWORD_VALIDATION_HINT` is set | Choose a password that meets the local rule | Ask the maintainer for the rule's wording (`PASSWORD_VALIDATION_HINT`) |
| `Token exchange is disabled` | HTTP 403 | `routers/auths.py:1636-1640` | A token-exchange call while `ENABLE_OAUTH_TOKEN_EXCHANGE` is off | None (integration) | Refer integration owners to the maintainer |
| `Direct API passthrough is disabled. Set ENABLE_OPENAI_API_PASSTHROUGH=True to enable.` | HTTP 403 | `routers/openai.py:2001-2005` | A call to an unhandled `/openai/` path while passthrough is off | None (integration) | As above |
| `Access denied. Only administrators can view usage statistics.` | HTTP 403 | `main.py:2628-2633` | `ENABLE_PUBLIC_ACTIVE_USERS_COUNT` off and a non-admin asks for the active-user count | None | Expected behaviour |
| `Invalid profile image URL: data URI exceeds the {PROFILE_IMAGE_MAX_DATA_URI_SIZE}-byte limit.` | Error when saving a picture | `utils/validate.py:86-90` | An embedded picture larger than `PROFILE_IMAGE_MAX_DATA_URI_SIZE` | Use a smaller picture | None |
| `Event call timed out. The browser tab may be inactive or closed.` | Returned to the waiting tool or function | `socket/main.py:1268-1282` | The browser did not answer within `WEBSOCKET_EVENT_CALLER_TIMEOUT` | Keep the tab open and active, then retry | None |
| `This feature is only available with SQLite databases.` | HTTP 400 | `routers/utils.py:80-84`; `constants.py:97` | Database download while the database is not SQLite (`DATABASE_URL`) | None (admin feature) | Expected on PostgreSQL |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | HTTP 401 | `routers/utils.py:76-78`; `routers/chats.py:1050-1052`; `constants.py:70-72` | Admin export or database download while `ENABLE_ADMIN_EXPORT` is off (the same text has many other causes) | None | Confirm the switch with the maintainer |
| `Startup not complete` / `Database not ready` / `Redis not ready` | HTTP 503 from `/ready` | `main.py:2968-3006` | Start-up still running, or the database or a configured Redis unreachable | None | The maintainer's monitoring sees these; report the time users were affected *Precision 2026-10-11: under uvicorn the port opens only after start-up finishes (`.venv` uvicorn 0.51.0, `server.py:104` before `:142`), so a probe normally gets no connection or waits during start-up rather than seeing `Startup not complete`; see `backend-architecture-and-request-lifecycle.md` section 5.5.* |
| `SAFE MODE ENABLED` | Start-up notice (printed) | `main.py:280-281` | `SAFE_MODE` on | Functions are off | Confirm with the maintainer that safe mode is intended |
| `USE_SLIM cannot be combined with USE_CUDA or USE_OLLAMA` | Image build failure | `Dockerfile:136-138` | Contradictory build arguments | None | Maintainer's build issue |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 cannot see or change environment variables (section 3). Every resolution below is guidance to users plus an escalation to the platform maintainer. Never ask a user, or put in a ticket, the value of a secret (section 7.1); name the variable instead.

### 11.1 "The app won't start after the change"

**Symptom.** After a configuration change or redeploy the site does not load, shows a proxy or gateway error, or keeps restarting; the readiness check answers 503.

**Likely causes, in order.**
1. A required secret is missing: `WEBUI_SECRET_KEY` is empty while sign-in is on. Under `start.sh` this also happens when only the deprecated `WEBUI_JWT_SECRET_KEY` is set, because the script then starts the server with an empty `WEBUI_SECRET_KEY` (`backend/start.sh:36`, `:107`; `backend/open_webui/env.py:762-788`).
2. A value that fails a check while the modules are imported: a malformed `CORS_ALLOW_ORIGIN` (for example commas instead of semicolons, or a missing `https://`), an unknown `VECTOR_DB` or `STORAGE_PROVIDER`, incomplete pgvector or Oracle settings, or a `sqlite+sqlcipher://` database URL (section 10).
3. A non-numeric value in a variable that is parsed without a fallback (section 7 rows marked "exits if invalid"; Python's `invalid literal for int()` error).
4. The database cannot be reached or migrated: migrations run when `config.py` is imported and a failure aborts start-up (CLAUDE.md, "Config").
5. Not a failure but a delay: start-up installs the packages that stored tools and functions need before it reports ready (`backend/open_webui/main.py:385-388`).

**Diagnostic steps** (read-only).
1. Load the site root and note the exact error page text and the time.
2. Ask whether a deployment or configuration change happened just before, and which variable was changed (the name only).
3. If you have access to the service's monitoring (**TO BE CONFIRMED**), check whether `/ready` reports `Startup not complete`, `Database not ready` or `Redis not ready` (section 10). *Precision 2026-10-11: under uvicorn the port opens only after start-up finishes (`.venv` uvicorn 0.51.0, `server.py:104` before `:142`), so a probe normally gets no connection or waits during start-up rather than seeing `Startup not complete`; see `backend-architecture-and-request-lifecycle.md` section 5.5.*

**Resolution.** Tell users the service is unavailable and that the maintainer is working on it. Tier 1 cannot restart the service or change its configuration.

**Escalation.** Send the platform maintainer the time of the failed start, the variable that was changed (name, never the value), and ask them to compare the first error in the server log with section 10.

### 11.2 "The setting change has no effect"

**Symptom.** The maintainer or an admin changed a variable, but the application behaves as before.

**Likely causes, in order.**
1. The variable only **seeds** a persistent setting: after the first boot the value stored in the `config` table wins and the variable is ignored (section 1.1; ground truth, "Settings: Where a Value Comes From"). The change has to be made on the Admin Settings screen instead.
2. Not every worker or replica was restarted; a running process keeps the old value (section 5.2).
3. A switch was given a value other than `true`: `1`, `yes` and `on` count as off (section 4, "Boolean parsing").
4. A number that cannot be parsed was silently replaced by the default (section 4, "Silent fallback").
5. The value was put in the repository-root `.env` file, but the real environment already defines the same name, even as an empty value, and the real environment wins. The Docker image defines `WEBUI_SECRET_KEY` and `OPENAI_API_KEY` as empty values, so `.env` cannot supply them there (`Dockerfile:90-91`; section 1.1).
6. The older name of a variable was changed while the newer name is also present: the code reads the older name only when the newer one is absent, so the newer value is used even when it is empty (`WEBUI_SECRET_KEY` over `WEBUI_JWT_SECRET_KEY`, `ENABLE_SCIM` over `SCIM_ENABLED`, `SCHEDULER_POLL_INTERVAL` over `AUTOMATION_POLL_INTERVAL`; section 4).
7. The variable has no effect in v0.11.4: `ENABLE_REALTIME_CHAT_SAVE`, `TRUSTED_SIGNATURE_KEY`, `WEBUI_BUILD_VERSION` and the `USE_TIKTOKEN_ENCODING_NAME` build argument (sections 7.3, 7.9, 7.13).
8. An admin edited single sign-on settings on screen while `ENABLE_OAUTH_PERSISTENT_CONFIG` is off, so the edit lasted only until the next restart, and only in the worker that saved it (section 7.16).

**Diagnostic steps** (read-only).
1. Find the variable in section 7 and note whether it is environment-only or a seed (section 7.16 and the persistent-settings catalogues).
2. If it is a seed and you can view Admin Settings, compare the value shown on screen with the intended one.
3. Ask when the restart happened and whether every replica was restarted.

**Resolution.** Explain the precedence rule to the requester. For a seed, an admin changes the setting on the Admin Settings screen; for an environment-only variable, the maintainer changes it and restarts every worker.

**Escalation.** Send the variable name, the intended effect, where it was set (compose file, `.env`, secret store; **TO BE CONFIRMED** for production) and the restart time.

### 11.3 "Different workers behave differently"

**Symptom.** The same action gives different results on different attempts: replies or notifications sometimes never arrive, a stop button sometimes does nothing, a setting appears and disappears on refresh, files are visible only sometimes, or a user is signed out at random.

**Likely causes, in order.**
1. Several workers or replicas without Redis: each keeps its own task list, websocket rooms, rate-limit counters and token revocations (section 7.5; ground truth).
2. Environment values differ between replicas: a different `WEBUI_SECRET_KEY` makes sign-in tokens valid on one replica only; a different `DATA_DIR`, `DATABASE_URL`, `VECTOR_DB` or `STORAGE_PROVIDER` shows different data (section 5.2).
3. Settings edited while not persisted (`ENABLE_PERSISTENT_CONFIG` off, or single sign-on settings with `ENABLE_OAUTH_PERSISTENT_CONFIG` off) change only the worker that saved them (section 7.16).
4. Short per-worker caches, such as the model list (`MODELS_CACHE_TTL`, one second by default; section 7.8).

**Diagnostic steps** (read-only).
1. Record the times of several attempts and whether a page refresh changes the result.
2. Ask whether the problem is intermittent for one user or affects many users at once.

**Resolution.** None at tier 1; reassure the user that the cause is in the deployment, not their account.

**Escalation.** Send the times, the action, how often it fails, and ask the maintainer to confirm the number of workers and replicas, `WEBSOCKET_MANAGER`, `REDIS_URL` and that every replica uses the same `WEBUI_SECRET_KEY` (CLAUDE.md, "Deployment").

### 11.4 "Everyone got signed out after a redeploy"

**Symptom.** Right after a deployment every user is returned to the sign-in page at once.

**Likely causes, in order.**
1. The secret key changed. When `WEBUI_SECRET_KEY` is not supplied, `start.sh` generates a key file inside the container, outside the data volume, so a recreated container gets a new key; `docker-compose.yaml` passes an empty value, which has this effect (`backend/start.sh:31-50`; `docker-compose.yaml:18`, `:25`; CLAUDE.md, "Deployment").
2. A deliberate key rotation.
3. Replicas started with different keys (section 11.3).
4. Not a deployment issue: tokens expire after the persistent setting `auth.jwt_expiry` (default four weeks; ground truth).

**Diagnostic steps** (read-only).
1. Confirm the sign-outs coincided with a deployment and affected all users.
2. Confirm users can sign in again normally.
3. Note any later reports of tools or functions "losing their settings" (section 10, `Failed to decrypt valves: {error}`).

**Resolution.** Ask users to sign in again. Their chats and data are not affected by the sign-out itself.

**Escalation.** Send the deployment time and the number of users affected; recommend that the maintainer supply `WEBUI_SECRET_KEY` from the managed secret store so it survives redeploys (CLAUDE.md, "Deployment"). Other consequences of a key change for stored data are security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca).

### 11.5 "My chats, files or document answers are gone after an update"

**Symptom.** After a deployment, users report missing chats, missing uploaded files, or models that no longer find document content.

**Likely causes, in order.**
1. The data directory is not on persistent storage, or `DATA_DIR` changed: the default SQLite database, uploads and Chroma store all live under it (section 6).
2. `DATABASE_URL` (or the `DATABASE_*` parts) now points at a different or empty database (section 7.4).
3. `VECTOR_DB` or its connection settings changed: the new store is empty and nothing copies collections across (section 7.10).
4. `STORAGE_PROVIDER` or its bucket settings changed: files stored earlier are elsewhere (section 7.11).
5. The data volume was deleted: `docker-cleanup.sh` runs `docker compose down -v` (CLAUDE.md, "Deployment").

**Diagnostic steps** (read-only).
1. Establish what exactly is missing: chats and accounts (database), file downloads (storage) or document search results (vector store).
2. Note when the user last saw the data and the time of the deployment.

**Resolution.** Ask users not to re-upload or recreate anything until the maintainer confirms the cause, to avoid duplicates.

**Escalation.** Urgent. Send what is missing, since when, and the deployment time.

### 11.6 "The product name or logo is wrong after an update"

**Symptom.** The browser title, sign-in page or notifications show a name other than **MedIT GPT**, or upstream logos reappear.

**Likely causes, in order.**
1. `WEBUI_NAME` is set in the environment to another value; it is environment-only and overrides the fork's default (section 7.2).
2. `CUSTOM_NAME` or licence data replaced the name at start-up (sections 7.12 and 7.16).
3. The static folder was refreshed from a front-end build that does not contain the U of T images (`backend/open_webui/config.py:98-145`; section 7.2).
4. `EXTERNAL_PWA_MANIFEST_URL` serves another manifest to installed apps (section 7.9).

**Diagnostic steps** (read-only). Note where the wrong name appears (title, sign-in page, notification, installed app) and take a screenshot.

**Resolution.** None at tier 1.

**Escalation.** Send the screenshot and the time first noticed to the platform maintainer; branding changes are governed by `LICENSE` §4 (ground truth).

## 12. Local Customisations

Checked with `git diff main...uoft` and `git diff` (working tree) on 2026-10-10 for every file this catalogue reads: `backend/open_webui/env.py`, `backend/open_webui/__init__.py`, `backend/open_webui/config.py`, `backend/open_webui/internal/`, `backend/open_webui/utils/`, `backend/open_webui/routers/`, `backend/open_webui/retrieval/`, `backend/open_webui/socket/`, `backend/open_webui/storage/`, `backend/start.sh`, `backend/dev.sh`, `Dockerfile`, `docker-compose.yaml`, `vite.config.ts`, `svelte.config.js` and `src/lib/constants.ts`.

| Change | Upstream v0.11.4 | `uoft` branch | Effect for support | Source |
|---|---|---|---|---|
| Default product name | `WEBUI_NAME` defaults to `Open WebUI`, and any other value has ` (Open WebUI)` appended | Defaults to `MedIT GPT`; a custom value is used exactly as given, with no suffix | The name users see comes from `WEBUI_NAME` when it is set; otherwise **MedIT GPT**. `CUSTOM_NAME` and licence data can still replace it (sections 7.12, 7.16). The licence comment above the line is kept (`backend/open_webui/env.py:947-950`). | `backend/open_webui/env.py:951`; `git diff main...uoft -- backend/open_webui/env.py` |
| Test notification text | A fixed sentence naming Open WebUI | `This is a test notification from {app_name}.`, with the running product name | Follows `WEBUI_NAME` | `backend/open_webui/utils/notifications.py:360`; ground truth |
| Front-end application name | `APP_NAME` is `Open WebUI` | `MedIT GPT` | A build-time constant, not an environment variable | `src/lib/constants.ts:7` |

No other file in scope differs from upstream, and none of them has uncommitted changes, so every other variable, default and message in this document matches upstream v0.11.4. When upstream releases are merged, the lines around `backend/open_webui/env.py:947-953` are where a conflict is expected.

## 13. Source File Index

| File | What it contributes here |
|---|---|
| `backend/open_webui/env.py` | Almost every environment-only variable: paths, platform, logging, database, Redis, websockets, outbound HTTP, sign-in, cookies, OAuth, SCIM, licence, identity, feature switches, forwarded headers, chat streaming, local models, knowledge-tool limits, plugins, offline mode, audit, OpenTelemetry; the secret-key start-up check (read in full) |
| `backend/open_webui/__init__.py` | `open-webui serve` and `open-webui dev`: `FROM_INIT_PY`, key-file generation, CUDA library paths, workers (read in full) |
| `backend/open_webui/internal/db.py` | How the database variables build the engines and pools; SQLite pragmas; SQLCipher and slim checks; Amazon RDS token authentication; session sharing (read in full) |
| `backend/open_webui/config.py` | Environment-only switches read there (static folder, storage, vector stores, CORS, thread pool, admin visibility, OAuth extras, `ENABLE_PERSISTENT_CONFIG`, `ENABLE_OAUTH_PERSISTENT_CONFIG`) and the seeds the image sets (lines 81-300, 400-470, 496-861, 983-1061, 1106-1147, 1358-1361, 1533-1578, 1660-1731, 2082-2151, 2500-2635, 2822-3232) |
| `backend/open_webui/main.py` | Start-up order, middleware, security headers, sessions, public configuration flags, readiness, version check, manifest, front-end mounting (lines 280-410, 496-553, 600-605, 796-890, 1130-1150, 2310-2440, 2590-2680, 2858-2890, 2963-3076) |
| `backend/open_webui/utils/security_headers.py` | The 14 security-header variables (read in full) |
| `backend/open_webui/utils/asgi_middleware.py` | Where the headers and the API-key header are applied (lines 80-135) |
| `backend/open_webui/utils/automations.py` | Scheduler intervals and loop (lines 1-130, 537-553) |
| `backend/open_webui/utils/logger.py` | Log format, level, audit file (read in full) |
| `backend/open_webui/utils/audit.py` | Audit levels, methods and path filters (lines 53-160, 228-290) |
| `backend/open_webui/utils/redis.py` | Redis client options, Sentinel retries (lines 59-110, 150-295) |
| `backend/open_webui/utils/session_pool.py` | Shared outbound connection pool and time-outs (lines 1-80) |
| `backend/open_webui/utils/headers.py` | Forwarded user-information headers (lines 1-100) |
| `backend/open_webui/utils/auth.py` | Password hashing and validation, the unused signature helper, licence check (lines 51-200) |
| `backend/open_webui/utils/valves.py` | Valve encryption switch (lines 1-40) |
| `backend/open_webui/utils/oauth.py` | OAuth encryption key, email fallback, ID-token cookie, session cap, authorize parameters (lines 250-262, 1660-1670, 1860-1890, 1988-2000, 2205-2240) |
| `backend/open_webui/utils/telemetry/setup.py`, `backend/open_webui/utils/telemetry/metrics.py`, `backend/open_webui/utils/telemetry/logs.py`, `backend/open_webui/utils/telemetry/instrumentors.py` | OpenTelemetry exporters |
| `backend/open_webui/socket/main.py` | Websocket manager, pools, clean-up loops, event-call time-out (lines 60-320, 960-990, 1268-1282) |
| `backend/open_webui/tasks.py` | Task listener, heartbeat, stream expiry (lines 20-120, 200-225) |
| `backend/open_webui/storage/provider.py` | Storage providers (lines 100-356) |
| `backend/open_webui/retrieval/vector/factory.py`, `backend/open_webui/retrieval/vector/type.py`, `backend/open_webui/retrieval/vector/dbs/chroma.py`, `backend/open_webui/retrieval/vector/dbs/pgvector.py` | Vector-store selection and start-up checks |
| `backend/open_webui/retrieval/utils.py`, `backend/open_webui/retrieval/loaders/main.py`, `backend/open_webui/retrieval/web/bing.py`, `backend/open_webui/retrieval/web/yandex.py`, `backend/open_webui/retrieval/web/external.py`, `backend/open_webui/retrieval/web/utils.py` | Retrieval-side environment reads and their effects |
| `backend/open_webui/routers/auths.py`, `backend/open_webui/routers/scim.py`, `backend/open_webui/routers/utils.py`, `backend/open_webui/routers/openai.py`, `backend/open_webui/routers/evaluations.py`, `backend/open_webui/routers/retrieval.py`, `backend/open_webui/routers/knowledge.py`, `backend/open_webui/routers/users.py`, `backend/open_webui/routers/files.py`, `backend/open_webui/routers/chats.py` | Request-time effects and messages of individual variables |
| `backend/open_webui/models/groups.py`, `backend/open_webui/models/chats.py`, `backend/open_webui/models/users.py`, `backend/open_webui/models/oauth_sessions.py` | Group share default, admin chat access, presence throttle, OAuth session key |
| `backend/open_webui/constants.py` | Texts of `EXISTING_USERS`, `INVALID_TRUSTED_HEADER`, `ACTION_PROHIBITED`, `ACCESS_PROHIBITED`, `PASSWORD_TOO_LONG`, `INVALID_PASSWORD`, `DB_NOT_SQLITE` |
| `backend/start.sh`, `backend/dev.sh` | Start-script variables (read in full) |
| `Dockerfile` | Image `ENV` lines and build arguments (read in full) |
| `docker-compose.yaml`, `docker-compose.otel.yaml`, `docker-compose.playwright.yaml` | Compose environment entries |
| `vite.config.ts`, `svelte.config.js`, `hatch_build.py`, `scripts/prepare-pyodide.js` | Front-end build variables |
| `uv.lock` | Locked python-dotenv version (lines 4123-4126) |
| `knowledgebase/tools/ground-truth.md`, `knowledgebase/tools/inventory.md`, `CLAUDE.md` | Verified facts and the inventory scope |

## 14. Open Questions

Everything below could not be established from the repository, or was referred as security-sensitive. Production values are data held outside the repository and are **TO BE CONFIRMED** with the platform maintainer.

### 14.1 Production Values (All TO BE CONFIRMED)

1. **How MedIT GPT is started** (Docker image with `start.sh`, `open-webui serve`, or another method) and where its environment is defined (compose file, orchestrator, `.env`, secret store). The answer decides whether the `WEBUI_JWT_SECRET_KEY` pitfall (section 7.3) and the key-file behaviour (section 5.4) apply.
2. **`WEBUI_SECRET_KEY`**: whether it comes from a managed secret store and is identical on every worker and replica; whether `OAUTH_CLIENT_INFO_ENCRYPTION_KEY`, `OAUTH_SESSION_TOKEN_ENCRYPTION_KEY` and `ENABLE_VALVE_ENCRYPTION` are set.
3. **Topology**: `UVICORN_WORKERS`, the number of replicas, `REDIS_URL`, `WEBSOCKET_MANAGER`, `ENABLE_DB_MIGRATIONS` on each instance.
4. **Data stores**: `DATABASE_URL` type (SQLite or PostgreSQL) and pool settings, `DATA_DIR` and its volume, `VECTOR_DB`, `STORAGE_PROVIDER` (ground truth, "Data Stores").
5. **Identity**: `WEBUI_AUTH`, `ENABLE_PASSWORD_AUTH`, `PASSWORD_HASH_ALGORITHM`, `ENABLE_PASSWORD_VALIDATION` and its hint, trusted-header sign-in, SCIM, cookie `SameSite` and `Secure` flags, `WEBUI_AUTH_SIGNOUT_REDIRECT_URL`.
6. **Privacy-relevant switches**: `ENABLE_FORWARD_USER_INFO_HEADERS` (sends user names, ids, emails and roles to model providers and tool servers), `ENABLE_ADMIN_CHAT_ACCESS`, `BYPASS_ADMIN_ACCESS_CONTROL`, `BYPASS_MODEL_ACCESS_CONTROL`, `BYPASS_RETRIEVAL_ACCESS_CONTROL`, `ENABLE_PUBLIC_ACTIVE_USERS_COUNT`, `ENABLE_ADMIN_EXPORT`, `ENABLE_PROFILE_IMAGE_URL_FORWARDING`.
7. **Logging and audit**: `GLOBAL_LOG_LEVEL`, `LOG_FORMAT`, `LOGURU_DIAGNOSE`, `AUDIT_LOG_LEVEL`, the audit file location, and the shipping and retention of logs and rotated audit files (the code configures no retention).
8. **Outbound connections**: OpenTelemetry export (endpoint, whether logs are exported, which would carry personal data off the server), proxy variables, the CA bundle (`AIOHTTP_CLIENT_SSL_CERT_FILE`), `OFFLINE_MODE`, `ENABLE_VERSION_UPDATE_CHECK` (contacts GitHub), `LICENSE_KEY` (contacts the upstream licence service), `CUSTOM_NAME` (contacts the upstream branding service).
9. **Front door**: `CORS_ALLOW_ORIGIN` (the code default `*` logs a warning), the security-header variables, `FORWARDED_ALLOW_IPS`, and the reverse proxy in front of the service.
10. **Branding**: whether `WEBUI_NAME` is set (otherwise **MedIT GPT**) and which `LICENSE` §4 exception applies (ground truth).
11. Whether the Hugging Face Spaces variables (`SPACE_ID` and others) are ever used; nothing suggests it.

### 14.2 Security-Sensitive Items Referred

Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca). Listed without detail: running with `WEBUI_AUTH` off; the OAuth and valve encryption keys and the consequences of changing the secret key for stored data; trusted-header sign-in and `FORWARDED_ALLOW_IPS`; the local-network fetch switch and fetch filter list; the `*_TRUST_REMOTE_CODE` model switches; licence verification; the option to turn certificate checking off (`AIOHTTP_CLIENT_SESSION_SSL=False` and related), and the OpenSearch default of not checking certificates (`OPENSEARCH_CERT_VERIFY` defaults to `false`, `backend/open_webui/config.py:634`).

### 14.3 Findings and Limits of This Research

1. **python-dotenv precedence.** Section 1.1 relied on library behaviour. Checked 2026-10-10 in the project's local environment: python-dotenv 1.2.2 skips any name already present in the environment unless `override` is passed (`.venv/lib/python3.12/site-packages/dotenv/main.py:105-106`), and `uv.lock` locks 1.2.2 (`uv.lock:4123-4126`). The Docker image installs from `backend/requirements.txt` (`Dockerfile:153-173`), which does not list python-dotenv directly (it arrives as a dependency of other packages), so the production version is **TO BE CONFIRMED**.
2. **No-op or unused values in v0.11.4** (searched `backend/` and `src`): `ENABLE_REALTIME_CHAT_SAVE` is imported but unused; `TRUSTED_SIGNATURE_KEY` feeds a helper (`backend/open_webui/utils/auth.py:60-73`) that nothing calls, though a tool or function could; `WEBUI_BUILD_VERSION` is set by the image and read by nothing; the `USE_TIKTOKEN_ENCODING_NAME` build argument is never used; `OTEL_RESOURCE_ATTRIBUTES` and `OTEL_TRACES_SAMPLER` are read into constants the code never uses (the OpenTelemetry library reads the same names itself, checked only in the local `.venv`, version 1.42.1).
3. **Comments that disagree with code**: the session pool's module comment gives connection limits of 100 and 30, but unset means unlimited (`backend/open_webui/utils/session_pool.py:9-10`, `:62-69`); the scheduler module comment gives a calendar look-ahead of 5 minutes, but the code default is 10 (`backend/open_webui/utils/automations.py:15`, `:55`). The code is documented here.
4. **Classification of `config.py` reads.** The 171 environment-only names in section 7.16 come from two scripted classifications of which constants feed `DEFAULT_CONFIG` (kept in this document's scratch folder, not in the repository), reconciled by hand for the names on which they disagreed: `MARIADB_VECTOR_DB_URL` and `CUSTOM_NAME` were confirmed environment-only, and 22 names read through lower-case temporaries (for example `OAUTH_GROUP_DEFAULT_SHARE`) were confirmed to be seeds. The persistent-settings catalogues should confirm the boundary when they are written.
5. **Library behaviour not verified in this repository**: SQLAlchemy's default pool size when `DATABASE_POOL_SIZE` is unset; python-socketio's default time-out when `WEBSOCKET_EVENT_CALLER_TIMEOUT` is unset; the effect of `HF_HUB_OFFLINE`, `HF_HOME`, `SCARF_NO_ANALYTICS`, `DO_NOT_TRACK` and `ANONYMIZED_TELEMETRY` inside third-party libraries; the use of `HTTP_PROXY`, `HTTPS_PROXY` and `NO_PROXY` by HTTP clients created with `trust_env=True`.
6. **Not opened, by rule**: any `.env` file, including the repository-root `.env` loaded by `backend/open_webui/env.py:40`, and `backend/data/`. The tracked template cited in section 2 was not re-opened in this session, so that row rests on the earlier researcher's reading.
7. **Ground truth wording.** Ground truth speaks of "the six `DATABASE_*` parts" and section 6 of "the five `DATABASE_*` parts": both are right, since six variables form five URL parts (user and password make one credential part; `backend/open_webui/env.py:277-294`). No contradiction.
8. **Correction made**: section 5.2, step 3 (marked *Corrected 2026-10-10*): the `GLOBAL_LOG_LEVEL: {GLOBAL_LOG_LEVEL}` line that `env.py` logs is printed only when `GLOBAL_LOG_LEVEL` is set; the line every worker prints comes from `backend/open_webui/utils/logger.py:223`.
9. **Planned documents** referred to as *(planned)* did not exist on 2026-10-10: `backend-architecture-and-request-lifecycle.md`, `database-schema-identity-chats-and-config.md`, `websockets-realtime-and-redis.md`, `deployment-operations-and-logging.md`, `frontend-architecture-routes-stores-and-i18n.md`, `developer-tools-scripts-and-tests.md`, `public-api-and-integrations.md`, `local-customisations-uoft-fork.md`, `configuration-persistent-settings-a-to-o.md` and `configuration-persistent-settings-r-to-w.md`.
10. **Quote check.** `knowledgebase/tools/verify_quotes.py` flags the image-build message in section 10 (slim combined with CUDA or Ollama) as not found because its corpus does not include the `Dockerfile`; the text was checked by hand against `Dockerfile:138`. Short citations in this document's tables (relative to `backend/open_webui/`) are not checked by `validate.py`; they were checked with a one-off script on 2026-10-10 (all resolved).
11. **Not logged elsewhere.** Under the research instructions this document is the only file changed, so the correction in item 8 still needs an entry in `knowledgebase/tools/VERIFICATION.md`.
