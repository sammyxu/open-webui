# Configuration: Persistent Settings (audio to openai)

## At a Glance

- MedIT GPT keeps most admin-editable settings in the database `config` table, one row per dotted
  key (for example `audio.tts.engine`); this document catalogues every key whose namespace sorts
  from `audio` to `openai` in `DEFAULT_CONFIG` (`backend/open_webui/config.py`).
- Each key is seeded from an environment variable on first boot only; after that the stored value
  wins over the environment, except for `oauth.*` keys, which follow the environment unless
  `ENABLE_OAUTH_PERSISTENT_CONFIG` is on.
- Section 7 holds one table per namespace: the key, the environment variable that seeds it, the
  code default, the admin screen that edits it, its effect and notes.
- Live values are data, not code: they are TO BE CONFIRMED by an administrator viewing the admin
  screen, never by requesting a configuration export (exports contain secrets).
- Not every key does something: 27 are inert rows the code never reads (the Google, Microsoft,
  GitHub and Feishu sign-in keys, four OAuth timing and method keys, and the Google Drive and
  OneDrive picker keys), five OAuth fields are shown but not used for sign-in, and 39 keys have no
  screen at all; section 7 marks each, and sections 8 to 11 explain what a save does and does not
  reach.

## 1. Purpose and Who Uses It

This document is a catalogue. For every persistent setting whose namespace (the part of the key
before the first dot) sorts from `audio` to `openai`, it records where the value comes from on a
new installation, what the code uses when nothing is set, which admin screen edits it, what it
changes, and anything unusual about it. The other half of the catalogue (`rag` to `webui`, plus
`webhook_url`) is a separate reference document, `configuration-persistent-settings-r-to-w.md`.
Environment variables that are never stored are in
[`configuration-environment-variables-bootstrap.md`](configuration-environment-variables-bootstrap.md).

| Reader | What they use it for |
|---|---|
| Tier-1 support | Answering "where does this value come from?", explaining why an environment change had no effect, and knowing which screen an admin should open. Tier 1 is read-only: it never changes a setting. |
| MedIT GPT administrators | Finding the screen and label for a key, and knowing which saves take effect at once, which need a page reload, and which last only until a restart. |
| The platform maintainer | Knowing which environment variable seeds each key, which keys are read from the environment instead of the store, and what a restart does. |

Scope in numbers: `DEFAULT_CONFIG` (`backend/open_webui/config.py:2822-3228`) holds 405 keys;
**199 of them** are in the 23 namespaces covered here (`audio` 30, `auth` 6, `automations` 4,
`calendar` 1, `channels` 2, `chat` 7, `code_execution` 7, `code_interpreter` 8, `direct` 2,
`evaluation` 2, `file` 2, `folders` 2, `google_drive` 3, `image_generation` 20, `images` 13,
`ldap` 17, `memories` 6, `models` 3, `notes` 1, `oauth` 53, `ollama` 3, `onedrive` 3, `openai` 4).
The counts come from a script run over `DEFAULT_CONFIG` and agree with a second, independent count
(section 14 records the method).

## 2. Navigation and URLs

Admin screens open inside the shared Settings window; `/admin/settings/<tab>` redirects to
`/?settings=admin:<tab>` (`src/routes/(app)/admin/settings/[tab]/+page.svelte:6-10`). The
production host is **TO BE CONFIRMED**, so addresses below are relative to the site root.

### 2.1 Screens That Edit Keys in This Scope

| Screen (address) | Namespaces it edits | Panel component | Section of this document |
|---|---|---|---|
| **General** (`/admin/settings/general`) | `folders`, `channels`, `calendar`, `automations` (switch only), `memories` (two switches), `notes` | `src/lib/components/admin/Settings/General.svelte` | 7.12, 7.5, 7.4, 7.3, 7.17, 7.19 |
| **Authentication** (`/admin/settings/authentication`) | `auth`, `ldap`, `oauth` | `src/lib/components/admin/Settings/Authentication.svelte` | 7.2, 7.16, 7.20 |
| **Connections** (`/admin/settings/connections`) | `openai`, `ollama`, `direct` (direct connections), `models` (base model cache) | `src/lib/components/admin/Settings/Connections.svelte` | 7.23, 7.21, 7.9, 7.18 |
| **Models** › **Model Defaults** (`/admin/settings/models`) | `models` (default metadata and parameters) | `src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte` | 7.18 |
| **Interface** (`/admin/settings/interface`) | `chat` | `src/lib/components/admin/Settings/Interface.svelte` | 7.6 |
| **Audio** (`/admin/settings/audio`) | `audio` | `src/lib/components/admin/Settings/Audio.svelte` | 7.1 |
| **Images** (`/admin/settings/images`) | `image_generation`, `images` | `src/lib/components/admin/Settings/Images.svelte` | 7.14, 7.15 |
| **Evaluations** (`/admin/settings/evaluations`) | `evaluation` | `src/lib/components/admin/Settings/Evaluations.svelte` | 7.10 |
| **Integrations** (`/admin/settings/integrations`) | `direct` (direct integrations) | `src/lib/components/admin/Settings/Integrations.svelte` | 7.9 |
| **Documents** (`/admin/settings/documents`) | `file`, `google_drive` (switch only), `onedrive` (switch only) | `src/lib/components/admin/Settings/Documents.svelte` | 7.11, 7.13, 7.22 |
| **Code Execution** (`/admin/settings/code-execution`) | `code_execution`, `code_interpreter` | `src/lib/components/admin/Settings/CodeExecution.svelte` | 7.7, 7.8 |
| **Database** › **Import** / **Export** (`/admin/settings/db`) | any key (whole-store import and export) | `src/lib/components/admin/Settings/Database.svelte` | 5.6 |

Every admin screen and its labels are described in
[`admin-settings-panels.md`](admin-settings-panels.md); this document gives each key's label only.

### 2.2 API Endpoints That Read or Write Keys in This Scope

All are admin-only unless the Role column says otherwise. They are listed so support can match a
browser network trace or a log line to a key; tier 1 does not call them.

| Method and path | Role | Keys in scope | Evidence |
|---|---|---|---|
| `GET` / `POST /api/v1/auths/admin/config` | admin | all six `auth.*` keys, `folders.*`, `channels.*`, `calendar.enable`, `automations.enable`, `automations.max_count`, `automations.min_interval`, `memories.enable`, `memories.system_context.enable`, `notes.enable` (plus `ui.*`, `webui.url`, `users.enable_status` outside this scope) | `backend/open_webui/routers/auths.py:104-136`, `:1204-1296` |
| `GET` / `POST /api/v1/auths/admin/config/ldap` | admin | `ldap.enable` | `backend/open_webui/routers/auths.py:1349-1361` |
| `GET` / `POST /api/v1/auths/admin/config/ldap/server` | admin | the other 16 `ldap.*` keys | `backend/open_webui/routers/auths.py:139-155`, `:1318-1346` |
| `GET` / `POST /api/v1/auths/admin/config/oauth` | admin | 34 `oauth.*` keys (map at `:1428-1463`) | `backend/open_webui/routers/auths.py:1428-1514` |
| `GET /api/v1/audio/config`; `POST /api/v1/audio/config/update` | admin | 29 `audio.*` keys (all but `audio.stt.allowed_extensions`, which the screen never sends). *Corrected 2026-10-11: the endpoint itself reads and accepts all 30 `audio.*` keys, `audio.stt.allowed_extensions` included (`backend/open_webui/routers/audio.py:96-114`, `:264`, `:298-303`); only the screen leaves that one out (section 7.1).* | `backend/open_webui/routers/audio.py:80-114`, `:282-325` |
| `GET /api/v1/images/config`; `POST /api/v1/images/config/update` | admin | all 33 `image_generation.*` and `images.*` keys | `backend/open_webui/routers/images.py:67-102`, `:271-320` |
| `GET /openai/config`; `POST /openai/config/update` | admin | `openai.*` | `backend/open_webui/routers/openai.py:305-310`, `:544-595` |
| `GET /ollama/config`; `POST /ollama/config/update` | admin | `ollama.*` | `backend/open_webui/routers/ollama.py:213-218`, `:289-350` |
| `GET` / `POST /api/v1/configs/connections` | admin | `direct.enable`, `direct.integrations.enable`, `models.base_models_cache` | `backend/open_webui/routers/configs.py:40-44`, `:139-160` |
| `GET` / `POST /api/v1/configs/code_execution` | admin | the 15 `code_execution.*` and `code_interpreter.*` keys | `backend/open_webui/routers/configs.py:45-61`, `:704-728` |
| `GET` / `POST /api/v1/configs/models` | admin | `models.default_metadata`, `models.default_params` (plus three `ui.*` keys) | `backend/open_webui/routers/configs.py:62-68`, `:749-770` |
| `GET /api/v1/configs/models/defaults` | any signed-in user | `models.default_metadata` (read only) | `backend/open_webui/routers/configs.py:742-746` |
| `GET /api/v1/retrieval/config`; `POST /api/v1/retrieval/config/update` | admin | `google_drive.enable`, `onedrive.enable`, `file.image_compression_width`, `file.image_compression_height` | `backend/open_webui/routers/retrieval.py:291`, `:293`, `:309-310`, `:629`, `:962` |
| `GET` / `POST /api/v1/chats/config` | admin | the 7 `chat.*` keys | `backend/open_webui/routers/chats.py:50-58`, `:836-857` |
| `GET` / `POST /api/v1/evaluations/config` | admin | `evaluation.*` | `backend/open_webui/routers/evaluations.py:32-35`, `:285-325` |
| `GET /api/v1/configs/export`; `POST /api/v1/configs/import` | admin | every key | `backend/open_webui/routers/configs.py:100-120` |
| `GET /api/v1/configs/namespace/{namespace}` | admin | every key under one namespace (no screen uses it) | `backend/open_webui/routers/configs.py:123-125` |
| `GET /api/config` | anyone; more fields for signed-in users | a read-only subset the browser needs (feature switches, engines, picker IDs) | `backend/open_webui/main.py:2224-2472` |

`/api/config` is how most switches in this scope reach users' screens. Visitors who are not signed
in receive only the sign-in essentials (`oauth.enable` gates the provider list, plus
`oauth.auto_redirect` and `ldap.enable`); signed-in users with the `user` or `admin` role also
receive the feature switches and engine names (`backend/open_webui/main.py:2256-2308`, `:2310-2390`,
`:2392-2448`). *Corrected 2026-10-11: the feature switches (`features.enable_*`, lines 2343-2390)
go to every signed-in account, `pending` included; only the engine names and the other blocks at
lines 2392-2447 are limited to the `user` and `admin` roles (`backend/open_webui/main.py:2388`,
`:2448`).*

## 3. Roles and Permissions

| Action | Who | Evidence |
|---|---|---|
| View or change any key in this scope on an admin screen | `admin` only; every endpoint in section 2.2 except two depends on `get_admin_user` | for example `backend/open_webui/routers/configs.py:101`, `:119`; `backend/open_webui/routers/auths.py:1205` |
| Read `models.default_metadata` | any signed-in `user` or `admin` (the model editor needs it) | `backend/open_webui/routers/configs.py:742-746` |
| Receive the browser subset (`/api/config`) | everyone; signed-in users get more | `backend/open_webui/main.py:2224-2472` |
| Change a seeding environment variable, restart, or change `ENABLE_PERSISTENT_CONFIG`, `ENABLE_OAUTH_PERSISTENT_CONFIG` or `RESET_CONFIG_ON_START` | the platform maintainer (whoever runs the server; **TO BE CONFIRMED**) | `backend/open_webui/config.py:3231-3232`; `backend/open_webui/env.py:368` |
| Tier-1 support | read-only: may ask an admin to open a screen and read a value aloud, never to export the settings | rule of this knowledgebase |

There is no per-setting permission: an admin can change every key, and a non-admin can change
none. Non-admins refused by `get_admin_user` receive HTTP 401 with the `ACCESS_PROHIBITED` text
(`knowledgebase/tools/ground-truth.md`, Accounts and Access).

## 4. Key Concepts and Terminology

| Term | Meaning in this codebase | Evidence |
|---|---|---|
| **Persistent setting** (or **key**) | One entry of `DEFAULT_CONFIG`, stored as one row of the `config` table whose primary key is the dotted name, for example `audio.tts.engine` | `backend/open_webui/config.py:2822`; `backend/open_webui/models/config.py:101-108` |
| **Namespace** | The part of the key before the first dot (`audio`, `oauth`, …); this document covers 23 of the 33 | `backend/open_webui/config.py:2822-3228` |
| **Seeding variable** | The environment variable a key's code default is read from when the server process starts; some keys read two (a preferred name and a fallback), a few read none | definitions in `backend/open_webui/config.py:229-2820` |
| **Code default** | What the key holds when its seeding variable is unset; it is computed when `config.py` is imported, in every server process | `backend/open_webui/config.py:3234-3238`; `backend/open_webui/models/config.py:116-130` |
| **Seed** | At start-up, insert a row for every key that has none, using the environment-derived value; rows that exist are left alone | `backend/open_webui/models/config.py:240-266` |
| **Stored value** | The row's JSON value. After the first start it is what the server uses, so later environment changes do not reach it | `backend/open_webui/models/config.py:140-147` |
| **Process-only value** | A value held in the memory of one server process instead of the database. It applies to `oauth.*` keys unless `ENABLE_OAUTH_PERSISTENT_CONFIG` is on, and to every key when `ENABLE_PERSISTENT_CONFIG` is off; saves change only the process that handled them and are lost at restart | `backend/open_webui/models/config.py:132-138`, `:197-206` |
| **Inert row** | A key that is seeded and editable or exportable, but that the running code never reads from the store: the server uses the environment constant instead. Section 7 marks each one | for example `backend/open_webui/main.py:2422-2431` |
| **Field name** | The upper-case name an admin endpoint uses for a key (for example `ENABLE_CODE_EXECUTION` for `code_execution.enable`). It often matches the seeding variable but not always (section 4.1) | `backend/open_webui/routers/configs.py:45-61` |
| **Derived runtime state** | Objects built from settings and kept in a server process: the local Whisper model, the embedding and reranking functions, the model list cache. Saving through the right screen rebuilds them in the process that handled the save | `backend/open_webui/routers/audio.py:305-310`; `backend/open_webui/main.py:621-752` |
| **Legacy names** | Before v0.11.4 the whole configuration was one JSON row; migration `3ff2c63645b8` split it into per-key rows and renamed some keys (for example `oauth.oidc.client_id` became `oauth.client_id`) | `backend/open_webui/migrations/versions/3ff2c63645b8_reshape_config_to_per_key_rows.py:414-436`, `:462-540` |

### 4.1 Field Names That Differ From the Seeding Variable

Support staff sometimes set an environment variable named after the field an admin screen sends.
These pairs differ, so that does not work:

| Key | Field name used by the admin API | Seeding variable actually read | Evidence |
|---|---|---|---|
| `oauth.group_claim` | `OAUTH_GROUP_CLAIM` | `OAUTH_GROUPS_CLAIM`, then `OAUTH_GROUP_CLAIM` as a fallback | `backend/open_webui/routers/auths.py:1441`; `backend/open_webui/config.py:2570` |
| `image_generation.openai.params` | `IMAGES_OPENAI_API_PARAMS` | `IMAGES_OPENAI_PARAMS` | `backend/open_webui/routers/images.py:77`; `backend/open_webui/config.py:1510` |
| `ldap.server.search_filter` | `search_filters` | `LDAP_SEARCH_FILTER`, then `LDAP_SEARCH_FILTERS` | `backend/open_webui/routers/auths.py:147`; `backend/open_webui/config.py:2806` |
| `ldap.server.users_dn` | `search_base` | `LDAP_SEARCH_BASE` | `backend/open_webui/routers/auths.py:146`; `backend/open_webui/config.py:2804` |
| `audio.stt.*`, `audio.tts.*` | short names such as `ENGINE`, `MODEL`, `OPENAI_API_KEY` inside `stt` and `tts` objects | `AUDIO_STT_ENGINE`, `AUDIO_TTS_MODEL`, `AUDIO_STT_OPENAI_API_KEY` and so on | `backend/open_webui/routers/audio.py:80-114`; `backend/open_webui/config.py:1562-1654` |
| `auth.api_key.endpoint_restrictions`, `auth.api_key.allowed_endpoints` | `ENABLE_API_KEYS_ENDPOINT_RESTRICTIONS`, `API_KEYS_ALLOWED_ENDPOINTS` | the same names, or the older singular `ENABLE_API_KEY_ENDPOINT_RESTRICTIONS` and `API_KEY_ALLOWED_ENDPOINTS` as fallbacks | `backend/open_webui/config.py:2456-2464` |
| `ollama.base_urls` | `OLLAMA_BASE_URLS` | `OLLAMA_BASE_URLS`, otherwise a single URL derived from `OLLAMA_BASE_URL` or `OLLAMA_API_BASE_URL` | `backend/open_webui/config.py:239-300` |
| `openai.api_keys`, `openai.api_base_urls` | `OPENAI_API_KEYS`, `OPENAI_API_BASE_URLS` | the plural names, otherwise the single `OPENAI_API_KEY` and `OPENAI_API_BASE_URL` | `backend/open_webui/config.py:322-347` |

## 5. Workflows (Step by Step)

### 5.1 How a Key Gets Its First Value

1. When any server process imports `open_webui.config`, database migrations run first unless
   `ENABLE_DB_MIGRATIONS` is off (`backend/open_webui/config.py:81-82`).
2. The module then evaluates each variable definition, reading its environment variable or
   falling back to the code default, and builds `DEFAULT_CONFIG` from them
   (`backend/open_webui/config.py:2822-3228`).
3. `Config.configure` keeps those values in memory as the defaults, together with the two
   persistence switches (`backend/open_webui/config.py:3231-3238`;
   `backend/open_webui/models/config.py:116-126`).
4. At start-up the `lifespan` handler calls `seed_registered_defaults`, which inserts a row for
   every key that has none (`backend/open_webui/main.py:367`; `backend/open_webui/config.py:42-45`;
   `backend/open_webui/models/config.py:240-266`). A first start therefore copies the environment
   into the database once.

### 5.2 What Every Later Start Does

The `lifespan` handler runs these steps in each server process, in this order
(`backend/open_webui/main.py:363-369`):

| Step | What happens to stored settings | Evidence |
|---|---|---|
| 1. Reset (only when `RESET_CONFIG_ON_START=True`) | Every `config` row is deleted, not only keys in this scope; event webhooks (`events.webhooks`) and tool-server connections are rows too | `backend/open_webui/main.py:363-364`; `backend/open_webui/config.py:48-49`; `backend/open_webui/models/config.py:233-238` |
| 2. Legacy import | If `DATA_DIR/config.json` exists, each top-level property in it is written as a row, then the file is renamed `old_config.json` | `backend/open_webui/config.py:85-91` |
| 3. Rename | Rows under `rag.web.` move to `web.` (outside this scope) | `backend/open_webui/models/config.py:268-300` |
| 4. Repair | Rows that an older version saved as flattened pieces of an object (for example `openai.api_configs.0.enable`) are folded back into the object key; in this scope that covers `openai.api_configs`, `ollama.api_configs`, `image_generation.automatic1111.api_params`, `image_generation.openai.params`, `audio.tts.openai.params`, `models.default_metadata` and `models.default_params` | `backend/open_webui/models/config.py:24-38`, `:302-382` |
| 5. Seed | Missing keys are inserted from the environment-derived defaults; existing rows are not touched | `backend/open_webui/models/config.py:240-266` |
| 6. Runtime set-up | Tool-server and arena-model access lists in an old format are migrated, and the embedding and reranking functions are built | `backend/open_webui/main.py:621-752` |

Steps 3 to 5 do nothing while `ENABLE_PERSISTENT_CONFIG` is off, and step 5 skips `oauth.*` keys
while `ENABLE_OAUTH_PERSISTENT_CONFIG` is off (`backend/open_webui/models/config.py:254-257`,
`:271-272`, `:305-306`).

### 5.3 An Admin Saves a Setting

1. The admin changes a control and presses **Save** (some switches save on change; see each
   table's Notes column).
2. The browser posts the screen's fields to its endpoint (section 2.2), which maps field names to
   keys and calls `Config.upsert` (`backend/open_webui/models/config.py:197-220`).
3. For each key the database is authoritative for, the row is updated or created and
   `updated_at` is set to the current time in epoch seconds. For a key it is not authoritative for
   (`oauth.*` with OAuth persistence off, or every key with persistence off), the value replaces
   the in-memory default of **that process only** (`backend/open_webui/models/config.py:200-206`).
4. Reads go straight to the database on each use, with no cache
   (`backend/open_webui/models/config.py:140-167`), so the server applies most changes on the next
   request. Browsers that are already open keep the switches they loaded from `/api/config` until
   they reload (`src/routes/+layout.svelte:1238-1290`, as established in
   [`admin-settings-panels.md`](admin-settings-panels.md) section 7.6).
5. Some endpoints also rebuild derived state or clear caches, and several publish an event
   (sections 8 and 9).

### 5.4 Read a Live Value Safely

1. Ask an admin to open the screen named in the key's row in section 7 and read the value; for a
   key marked "none (API or import only)", the value can only be seen in an export, so escalate to
   the platform maintainer instead.
2. **Never ask for a settings export.** `GET /api/v1/configs/export` returns every stored row,
   including provider API keys, OAuth client secrets, the LDAP bind password and Jupyter
   credentials (`backend/open_webui/routers/configs.py:118-120`;
   `backend/open_webui/models/config.py:185-195`).
3. For a key marked "inert row" or "environment" in section 7, the screen may not show what the
   server uses; the platform maintainer has to check the environment of the running server.
4. Write down the key, the value read, the time and the screen; live values are data, not code,
   and every one of them is **TO BE CONFIRMED** for production.

### 5.5 Make an Environment Change Take Effect After the First Start

Tier 1 does none of this; it is listed so an escalation can say what is needed.

| Option | Effect | Evidence |
|---|---|---|
| Change the value on its admin screen | Updates the stored row at once; the environment variable stays different but no longer matters | `backend/open_webui/models/config.py:197-220` |
| Remove the key's row (database change by the maintainer) | Running processes fall back to their environment-derived default at once, and the next start re-inserts it from the environment | `backend/open_webui/models/config.py:146-147`, `:258-262` |
| Start with `RESET_CONFIG_ON_START=True` | Deletes **every** stored setting on every start, including event webhooks and tool-server connections, then re-seeds from the environment | `backend/open_webui/main.py:363-364` |
| Run with `ENABLE_PERSISTENT_CONFIG=False` | Every key follows the environment; admin saves last only until a restart and only in one process | `backend/open_webui/models/config.py:132-138` |

Keys marked "inert row" in section 7 are different: the server already reads their environment
variable, so they need only a restart.

### 5.6 Export and Import

Both are on **Database** (`/admin/settings/db`); the steps and messages are in
[`admin-settings-panels.md`](admin-settings-panels.md) sections 5.8 and 5.9. Points that matter for
this scope:

- The export carries secrets (section 5.4) and, while OAuth persistence is off, the
  environment's OAuth values rather than any stored `oauth.*` rows
  (`backend/open_webui/models/config.py:193-194`).
- The import writes whatever keys the file contains without checking their names or values
  (`backend/open_webui/routers/configs.py:100-110`). A misspelt key becomes a row nothing reads;
  `oauth.*` keys in the file change only the importing process while OAuth persistence is off.
- An import does not rebuild derived state: a different Whisper model or embedding engine takes
  effect only after that screen's own save or a restart
  ([`admin-settings-panels.md`](admin-settings-panels.md) section 7.6).

### 5.7 Turning On OAuth Persistence

When the maintainer starts the server with `ENABLE_OAUTH_PERSISTENT_CONFIG=True`:

1. The Authentication screen's **OAuth / OIDC** section becomes editable
   (`src/lib/components/admin/Settings/Authentication.svelte:52`, `:550-563`).
2. At start-up any `oauth.*` key without a row is seeded from the environment; an `oauth.*` row
   that already exists (for example one copied from the pre-v0.11.4 configuration by migration
   `3ff2c63645b8`, which does not look at this switch) wins over the environment
   (`backend/open_webui/models/config.py:240-266`;
   `backend/open_webui/migrations/versions/3ff2c63645b8_reshape_config_to_per_key_rows.py:513-540`).
   *Inferred from code, not tested:* turning the switch on can therefore bring back old OAuth
   values that were stored before.
3. Provider registration still reads the environment constants, not the store, so client ID,
   secret, provider URL, redirect URI and scopes keep following the environment
   (`backend/open_webui/config.py:2653-2782`; `knowledgebase/tools/ground-truth.md`).

## 6. Data Model

### 6.1 The `config` Table

| Column | Type | Meaning | Evidence |
|---|---|---|---|
| `key` | text, primary key | The dotted key, for example `oauth.enable_signup` | `backend/open_webui/models/config.py:106` |
| `value` | JSON, not null | The stored value: a boolean, string, number, list, object or JSON `null` | `backend/open_webui/models/config.py:107` |
| `updated_at` | big integer, nullable | Epoch **seconds** of the last insert or update | `backend/open_webui/models/config.py:108`, `:212-219` |

There is one row per key, no history and no record of who changed it; who saved a change is
visible only in an event (section 9) or the optional audit log
([`configuration-environment-variables-bootstrap.md`](configuration-environment-variables-bootstrap.md)).
Rows outside `DEFAULT_CONFIG` can exist: `events.webhooks` (event webhooks), rows from an import,
and legacy rows from the migration that kept unknown names
(`backend/open_webui/events.py:20`;
`backend/open_webui/migrations/versions/3ff2c63645b8_reshape_config_to_per_key_rows.py:517-534`).

### 6.2 Value Shapes in This Scope

| Shape | Keys (examples) | Evidence |
|---|---|---|
| Boolean | every `*.enable` key, `ldap.server.use_tls`, `oauth.update_*_on_login` | `backend/open_webui/config.py:230`, `:2808`, `:2611-2615` |
| String | URLs, model names, engine names, claims; duration strings such as `auth.jwt_expiry` (`4w`) and `automations.auth_token_expires_in` (`1h`) | `backend/open_webui/config.py:2466`, `:2048` |
| Integer | `code_execution.jupyter.timeout`, `ldap.server.port`, `image_generation.steps`, the `memories.*` limits, the compaction token values | `backend/open_webui/config.py:422`, `:2794`, `:1365`, `:429-431`, `:2198` |
| Empty string meaning "no limit" | `folders.max_file_count`, `automations.max_count`, `automations.min_interval` | `backend/open_webui/config.py:2026`, `:2044-2046`; `backend/open_webui/routers/auths.py:1277-1281` |
| JSON `null` meaning "not set" | `auth.admin.email`, `file.image_compression_width`, `file.image_compression_height`, `chat.context_compaction.token_cap`, `oauth.sub_claim`, `oauth.code_challenge_method`, `oauth.token_endpoint_auth_method` | `backend/open_webui/config.py:2172`, `:989-995`, `:2200-2201`, `:2555-2561` |
| List of strings | `openai.api_base_urls`, `openai.api_keys`, `ollama.base_urls`, `audio.stt.supported_content_types`, `audio.stt.allowed_extensions`, `oauth.allowed_domains`, `oauth.allowed_roles`, `oauth.admin_roles` | `backend/open_webui/config.py:299`, `:338`, `:344-346`, `:1590-1603`, `:2599-2609` |
| List of objects | `evaluation.arena.models`, `image_generation.comfyui.nodes`, `images.edit.comfyui.nodes` | `backend/open_webui/config.py:2055-2065`, `:1497-1503`, `:1549-1555` |
| Object | `openai.api_configs` and `ollama.api_configs` (keyed by connection position `"0"`, `"1"`, …), `audio.tts.openai.params`, `image_generation.openai.params`, `image_generation.automatic1111.api_params`, `models.default_metadata`, `models.default_params` | `backend/open_webui/routers/openai.py:566-567`; `backend/open_webui/routers/ollama.py:313-314`; `backend/open_webui/models/config.py:24-38` |
| A JSON array held as a string | `oauth.blocked_groups` (code default `'[]'`) | `backend/open_webui/config.py:2591`; `backend/open_webui/routers/auths.py:1466-1469` |
| Boolean or the string `members` | `oauth.group_default_share` | `backend/open_webui/config.py:2587-2588` |

### 6.3 Legacy Tables and Renames

- Migration `3ff2c63645b8` read the newest row of the old single-row `config` table, renamed that
  table `config_old`, created the per-key table and copied each value across
  (`backend/open_webui/migrations/versions/3ff2c63645b8_reshape_config_to_per_key_rows.py:462-540`).
  `config_old` is kept for rollback; the downgrade path restores it (`:543-552`).
- Renames applied by that migration in this scope: `oauth.refresh_token_include_scope` →
  `oauth.refresh_token.include_scope`, and fifteen `oauth.oidc.*` names → `oauth.*` (for example
  `oauth.oidc.avatar_claim` → `oauth.picture_claim`, `oauth.oidc.oauth_timeout` → `oauth.timeout`)
  (`:414-436`).
- The database schema, migration history and the other tables are covered by the planned
  reference document `database-schema-identity-chats-and-config.md`.

## 7. Settings and Configuration

This section is the catalogue itself: one table per namespace, in alphabetical order and numbered
as in section 2.1, covering all 199 keys in scope. Live values are data held in the `config` table
(or, for process-only values, in each server process's memory, seeded from the environment) and
every one of them is **TO BE CONFIRMED** for production; the tables give only what the repository
says.

| Column | Meaning |
|---|---|
| Key | The dotted key, as stored in `config.key` |
| Seeded from | The environment variable or variables that the referenced variable's definition reads, in the order the code tries them; "none" when the definition reads no variable |
| Code default | What the key is seeded with when its variable is unset |
| Admin screen | The tab (addresses in section 2.1) and the visible label, with the component line and, for dotted i18n keys, the `en-US` translation line; "none (API or import only)" when no screen edits the key |
| Effect | What the running code does with the stored value |
| Notes | Definition line, where the value is read, how the screen saves it, and anything unusual |

Conventions used in every table:

- **secret (set per environment)** marks a key that holds an API key, password, token or client
  secret. Neither its value nor any default that could be a copied credential is written here.
- A screen saves its keys when the admin presses **Save** unless the Notes say **saves on change**;
  each "saves on change" was checked in the component cited.
- **Inert row** means the server reads an environment constant instead of the key (section 4).
- **Process-only** means the key is held in server memory, not the database, while its persistence
  switch is off (section 4; it applies to every `oauth.*` key by default).

### 7.1 `audio` (30 Keys)

Area document: [`audio-speech-to-text-and-text-to-speech.md`](audio-speech-to-text-and-text-to-speech.md)
(sections 5.7 to 5.10 and 7). Definitions are at `backend/open_webui/config.py:1561-1654`; the
`DEFAULT_CONFIG` lines are `:3052-3081`. The screen is **Audio**
(`src/lib/components/admin/Settings/Audio.svelte`); its labels are dotted keys under
`settings.admin.audio.*` (`src/lib/i18n/locales/en-US/translation.json:1977-2021`). The endpoint
maps field names to keys at `backend/open_webui/routers/audio.py:80-114` and saves only the fields
the browser sends (`:298-303`). The screen sends every field except `ALLOWED_EXTENSIONS`
(`src/lib/components/admin/Settings/Audio.svelte:146-180`).

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `audio.stt.engine` | `AUDIO_STT_ENGINE` | empty (local Whisper) | **Audio** › **Speech-to-Text Engine**: `Whisper (Local)`, `OpenAI`, `Web API`, `Deepgram`, `Azure AI Speech`, `MistralAI` (`src/lib/components/admin/Settings/Audio.svelte:261-273`; `src/lib/i18n/locales/en-US/translation.json:1991`) | Chooses who transcribes recordings; `web` leaves dictation to the browser | Def `backend/open_webui/config.py:1586`; dispatch `backend/open_webui/routers/audio.py:974-985`; sent to browsers (`backend/open_webui/main.py:2410`). Saving with local Whisper selected loads the Whisper model in the process that handled the save (`backend/open_webui/routers/audio.py:305-310`). In the slim image, switching to local Whisper is refused (`:292-295`) |
| `audio.stt.whisper_model` | `WHISPER_MODEL` | `base` | **Audio** › **STT Model** with **Update model**, shown for `Whisper (Local)` (`src/lib/components/admin/Settings/Audio.svelte:436-452`; `src/lib/i18n/locales/en-US/translation.json:2003`, `:2019`) | faster-whisper model used for local transcription | Def `backend/open_webui/config.py:1562`. **Update model** saves the whole screen (`src/lib/components/admin/Settings/Audio.svelte:188-192`). Other processes keep the model they loaded until restart; a process that has none loads it on first use (`backend/open_webui/routers/audio.py:671-676`) |
| `audio.stt.model` | `AUDIO_STT_MODEL` | empty | **Audio** › **STT Model**, shown for `OpenAI`, `Deepgram` and `MistralAI` (`src/lib/components/admin/Settings/Audio.svelte:318`, `:339`, `:413`; `src/lib/i18n/locales/en-US/translation.json:1999`, `:1982`) | Model name sent to the transcription service | Def `backend/open_webui/config.py:1588`; read `backend/open_webui/routers/audio.py:713`, `:782`; MistralAI falls back to `voxtral-mini-latest` (`:1005`) |
| `audio.stt.supported_content_types` | `AUDIO_STT_SUPPORTED_CONTENT_TYPES` (comma list) | empty list (treated as `audio/*`, `video/webm`) | **Audio** › **Supported MIME Types**, hidden for `Web API` (`src/lib/components/admin/Settings/Audio.svelte:276-286`; `src/lib/i18n/locales/en-US/translation.json:2005`) | Which file types are transcribed, for dictation and for attached files | Def `backend/open_webui/config.py:1590-1594`; empty fallback `backend/open_webui/utils/misc.py:1204-1208`; read `backend/open_webui/routers/audio.py:1264-1270`, `backend/open_webui/routers/files.py:146-160`. A blank field is saved as a list holding one empty string, which the matcher treats as empty (`src/lib/components/admin/Settings/Audio.svelte:168`) |
| `audio.stt.allowed_extensions` | `AUDIO_STT_ALLOWED_EXTENSIONS` (comma list) | `mp3`, `wav`, `m4a`, `webm`, `ogg`, `flac`, `mp4`, `mpga`, `mpeg` | none (API or import only) | File-name extensions the transcription endpoint accepts; others get `Invalid audio file extension` | Def `backend/open_webui/config.py:1596-1603`; read `backend/open_webui/routers/audio.py:1276-1281`. The screen never sends the field, so a save leaves it unchanged |
| `audio.stt.openai.api_base_url` | `AUDIO_STT_OPENAI_API_BASE_URL` | `https://api.openai.com/v1` | **Audio** › **API Base URL**, shown for `OpenAI` (`src/lib/components/admin/Settings/Audio.svelte:291`; `src/lib/i18n/locales/en-US/translation.json:2000`) | Address of the OpenAI-compatible transcription service | Def `backend/open_webui/config.py:1580`; the fallback constant is fixed to OpenAI's address (`:367`); read `backend/open_webui/routers/audio.py:705` |
| `audio.stt.openai.api_key` | `AUDIO_STT_OPENAI_API_KEY`; otherwise the key paired with OpenAI's address in `OPENAI_API_KEYS` or `OPENAI_API_KEY` | secret (set per environment) | **Audio** › **API Key**, shown for `OpenAI` (`src/lib/components/admin/Settings/Audio.svelte:299`; `src/lib/i18n/locales/en-US/translation.json:2001`) | Credential for that service | Def `backend/open_webui/config.py:1582`, fallback `:361-366`; read `backend/open_webui/routers/audio.py:704` |
| `audio.stt.openai.api_request_format` | `AUDIO_STT_OPENAI_API_REQUEST_FORMAT` | `multipart` | **Audio** › **Request Format**: `Multipart Upload` or `JSON Base64`, shown for `OpenAI` (`src/lib/components/admin/Settings/Audio.svelte:309-314`; `src/lib/i18n/locales/en-US/translation.json:1985`) | How the recording is sent | Def `backend/open_webui/config.py:1584`; read `backend/open_webui/routers/audio.py:706` (empty means `multipart`) |
| `audio.stt.deepgram.api_key` | `DEEPGRAM_API_KEY` | secret (set per environment) | **Audio** › **API Key**, shown for `Deepgram` (`src/lib/components/admin/Settings/Audio.svelte:330`; `src/lib/i18n/locales/en-US/translation.json:1995`) | Deepgram credential | Def `backend/open_webui/config.py:1575`; read `backend/open_webui/routers/audio.py:781` |
| `audio.stt.azure.api_key` | `AUDIO_STT_AZURE_API_KEY` | secret (set per environment) | **Audio** › **API Key**, shown for `Azure AI Speech` (`src/lib/components/admin/Settings/Audio.svelte:354`; `src/lib/i18n/locales/en-US/translation.json:1992`) | Azure credential; transcription is refused without it | Def `backend/open_webui/config.py:1605`; read `backend/open_webui/routers/audio.py:852`, `:878-879` |
| `audio.stt.azure.region` | `AUDIO_STT_AZURE_REGION` | empty (`eastus` at use) | **Audio** › **Azure Region** (`src/lib/components/admin/Settings/Audio.svelte:364`; `src/lib/i18n/locales/en-US/translation.json:1994`) | Azure region | Def `backend/open_webui/config.py:1607`; read `backend/open_webui/routers/audio.py:853` |
| `audio.stt.azure.locales` | `AUDIO_STT_AZURE_LOCALES` (comma list in a string) | empty (13 built-in locales at use) | **Audio** › **Language Locales** (`src/lib/components/admin/Settings/Audio.svelte:371`; `src/lib/i18n/locales/en-US/translation.json:1979`) | Languages Azure listens for | Def `backend/open_webui/config.py:1609`; read `backend/open_webui/routers/audio.py:854-876` |
| `audio.stt.azure.base_url` | `AUDIO_STT_AZURE_BASE_URL` | empty (the regional public address) | **Audio** › **Endpoint URL** (`src/lib/components/admin/Settings/Audio.svelte:378`; `src/lib/i18n/locales/en-US/translation.json:1993`) | Alternative Azure address | Def `backend/open_webui/config.py:1611`; read `backend/open_webui/routers/audio.py:855`, `:887-889` |
| `audio.stt.azure.max_speakers` | `AUDIO_STT_AZURE_MAX_SPEAKERS` | empty (3 at use) | **Audio** › **Max Speakers** (`src/lib/components/admin/Settings/Audio.svelte:385`; `src/lib/i18n/locales/en-US/translation.json:1980`) | Speaker separation limit | Def `backend/open_webui/config.py:1613`; read `backend/open_webui/routers/audio.py:856`, `:883`. Stored as text, not a number |
| `audio.stt.mistral.api_key` | `AUDIO_STT_MISTRAL_API_KEY` | secret (set per environment) | **Audio** › **API Key**, shown for `MistralAI` (`src/lib/components/admin/Settings/Audio.svelte:403`; `src/lib/i18n/locales/en-US/translation.json:1997`) | MistralAI credential; transcription is refused without it | Def `backend/open_webui/config.py:1615`; read `backend/open_webui/routers/audio.py:996`, `:1000-1001` |
| `audio.stt.mistral.api_base_url` | `AUDIO_STT_MISTRAL_API_BASE_URL` | `https://api.mistral.ai/v1` | **Audio** › **API Base URL**, shown for `MistralAI` (`src/lib/components/admin/Settings/Audio.svelte:395`; `src/lib/i18n/locales/en-US/translation.json:1996`) | MistralAI address | Def `backend/open_webui/config.py:1617`; read `backend/open_webui/routers/audio.py:997` (empty falls back to the same address) |
| `audio.stt.mistral.use_chat_completions` | `AUDIO_STT_MISTRAL_USE_CHAT_COMPLETIONS` (`true` to enable) | off | **Audio** › **Use Chat Completions API** (`src/lib/components/admin/Settings/Audio.svelte:425-429`; `src/lib/i18n/locales/en-US/translation.json:2021`) | Transcribes through a chat request instead of the transcription endpoint | Def `backend/open_webui/config.py:1619`; read `backend/open_webui/routers/audio.py:998` |
| `audio.tts.engine` | `AUDIO_TTS_ENGINE` | empty (`Web API`, the browser speaks) | **Audio** › **Text-to-Speech Engine**: `Web API`, `Transformers (Local)`, `OpenAI`, `ElevenLabs`, `Azure AI Speech`, `MistralAI` (`src/lib/components/admin/Settings/Audio.svelte:486-518`; `src/lib/i18n/locales/en-US/translation.json:2007`) | Chooses who speaks answers; with the empty value the server's speech endpoint answers 404 | Def `backend/open_webui/config.py:1635`; read `backend/open_webui/routers/audio.py:603-610`; sent to browsers (`backend/open_webui/main.py:2405`). **Saves on change**, and the change first resets **TTS Voice** and **TTS Model** to the engine's defaults (`alloy` and `tts-1` for OpenAI; empty and `voxtral-mini-tts-2603` for MistralAI; both empty otherwise) (`src/lib/components/admin/Settings/Audio.svelte:492-509`) |
| `audio.tts.model` | `AUDIO_TTS_MODEL` | `tts-1` | **Audio** › **TTS Model**, shown for every engine except `Web API` and `Azure AI Speech` (`src/lib/components/admin/Settings/Audio.svelte:613`, `:646`, `:675`; `src/lib/i18n/locales/en-US/translation.json:2015`) | Model for OpenAI, ElevenLabs and MistralAI; the speaker-embedding name for `Transformers (Local)` | Def `backend/open_webui/config.py:1638`; read `backend/open_webui/routers/audio.py:399`, `:461`, `:526-532`, `:567`. Part of the speech-cache file name, so a new model produces new audio (`:619-624`) |
| `audio.tts.voice` | `AUDIO_TTS_VOICE` | `alloy` | **Audio** › **TTS Voice**, shown for every engine except `Transformers (Local)` (`src/lib/components/admin/Settings/Audio.svelte:596`, `:638`, `:667`, `:686`; `src/lib/i18n/locales/en-US/translation.json:2018`) | Default voice for everyone; users and models can override it | Def `backend/open_webui/config.py:1640`; read `backend/open_webui/routers/audio.py:401`, `:484`; sent to browsers (`backend/open_webui/main.py:2406`) |
| `audio.tts.split_on` | `AUDIO_TTS_SPLIT_ON` | `punctuation` | **Audio** › **Response Splitting** (`src/lib/components/admin/Settings/Audio.svelte:719-724`; `src/lib/i18n/locales/en-US/translation.json:1987`) | How answers are cut into pieces before they are spoken | Def `backend/open_webui/config.py:1642`. Used only by the browser (`backend/open_webui/main.py:2407`; `src/lib/components/chat/Messages/ResponseMessage.svelte:321`; `src/lib/components/chat/Chat.svelte:1915`), so open pages apply a change after a reload |
| `audio.tts.api_key` | `AUDIO_TTS_API_KEY` | secret (set per environment) | **Audio** › **API Key**, shown for `ElevenLabs` and `Azure AI Speech` (`src/lib/components/admin/Settings/Audio.svelte:541`, `:550`; `src/lib/i18n/locales/en-US/translation.json:2009`) | ElevenLabs or Azure speech credential | Def `backend/open_webui/config.py:1633`; read `backend/open_webui/routers/audio.py:467`, `:500` |
| `audio.tts.openai.api_base_url` | `AUDIO_TTS_OPENAI_API_BASE_URL` | `https://api.openai.com/v1` | **Audio** › **API Base URL**, shown for `OpenAI` (`src/lib/components/admin/Settings/Audio.svelte:524`; `src/lib/i18n/locales/en-US/translation.json:2016`) | Address of the OpenAI-compatible speech service; voice and model lists are asked of it | Def `backend/open_webui/config.py:1621`, fallback `:367`; read `backend/open_webui/routers/audio.py:404`, `:1351`, `:1425` |
| `audio.tts.openai.api_key` | `AUDIO_TTS_OPENAI_API_KEY`; otherwise the key paired with OpenAI's address (as for speech-to-text) | secret (set per environment) | **Audio** › **API Key**, shown for `OpenAI` (`src/lib/components/admin/Settings/Audio.svelte:532`; `src/lib/i18n/locales/en-US/translation.json:2017`) | Credential for that service | Def `backend/open_webui/config.py:1622`; read `backend/open_webui/routers/audio.py:403` |
| `audio.tts.openai.params` | `AUDIO_TTS_OPENAI_PARAMS` (JSON object; invalid JSON gives `{}`) | `{}` | **Audio** › **Additional Parameters**, shown for `OpenAI` (`src/lib/components/admin/Settings/Audio.svelte:656-661`; `src/lib/i18n/locales/en-US/translation.json:1978`) | Extra fields merged into every OpenAI speech request, after the model and voice, so they can override them | Def `backend/open_webui/config.py:1624-1630`; read `backend/open_webui/routers/audio.py:402`. Invalid JSON on the screen stops the save with `Invalid JSON format for Parameters` (`src/lib/components/admin/Settings/Audio.svelte:137-144`) |
| `audio.tts.azure.speech_region` | `AUDIO_TTS_AZURE_SPEECH_REGION` | empty (`eastus` at use) | **Audio** › **Azure Region**, shown for `Azure AI Speech` (`src/lib/components/admin/Settings/Audio.svelte:560`; `src/lib/i18n/locales/en-US/translation.json:2011`) | Azure speech region | Def `backend/open_webui/config.py:1644`; read `backend/open_webui/routers/audio.py:482`, `:1463` |
| `audio.tts.azure.speech_base_url` | `AUDIO_TTS_AZURE_SPEECH_BASE_URL` | empty (the regional public address) | **Audio** › **Endpoint URL** (`src/lib/components/admin/Settings/Audio.svelte:567`; `src/lib/i18n/locales/en-US/translation.json:2010`) | Alternative Azure speech address | Def `backend/open_webui/config.py:1646`; read `backend/open_webui/routers/audio.py:483`, `:498` |
| `audio.tts.azure.speech_output_format` | `AUDIO_TTS_AZURE_SPEECH_OUTPUT_FORMAT` | `audio-24khz-160kbitrate-mono-mp3` | **Audio** › **Output format** (`src/lib/components/admin/Settings/Audio.svelte:694-697`; `src/lib/i18n/locales/en-US/translation.json:1983`) | Audio format Azure returns | Def `backend/open_webui/config.py:1648-1650`; read `backend/open_webui/routers/audio.py:486`, `:502` |
| `audio.tts.mistral.api_key` | `AUDIO_TTS_MISTRAL_API_KEY` | secret (set per environment) | **Audio** › **API Key**, shown for `MistralAI` (`src/lib/components/admin/Settings/Audio.svelte:585`; `src/lib/i18n/locales/en-US/translation.json:2013`) | MistralAI speech credential; speech is refused without it | Def `backend/open_webui/config.py:1652`; read `backend/open_webui/routers/audio.py:554-558` |
| `audio.tts.mistral.api_base_url` | `AUDIO_TTS_MISTRAL_API_BASE_URL` | `https://api.mistral.ai/v1` | **Audio** › **API Base URL**, shown for `MistralAI` (`src/lib/components/admin/Settings/Audio.svelte:577`; `src/lib/i18n/locales/en-US/translation.json:2012`) | MistralAI speech address | Def `backend/open_webui/config.py:1654`; read `backend/open_webui/routers/audio.py:555` |

Saving the screen publishes `config.updated` with the two engine names (section 9). Signed-in users
with the `user` or `admin` role receive only the two engines, the voice and the splitting mode
(`backend/open_webui/main.py:2403-2412`, `:2448`).

### 7.2 `auth` (6 Keys)

Area documents: [`authentication-and-sign-in.md`](authentication-and-sign-in.md) (sign-in, tokens,
API keys) and [`users-groups-roles-and-permissions.md`](users-groups-roles-and-permissions.md) (the
`features.api_keys` permission). The screen is **Authentication**
(`src/lib/components/admin/Settings/Authentication.svelte`), labels under
`settings.admin.authentication.*` (`src/lib/i18n/locales/en-US/translation.json:2022-2136`). It
saves through `POST /api/v1/auths/admin/config`, whose field map also holds `webui.url`, `ui.*`,
`folders.*`, `channels.*`, `calendar.enable`, `automations.*`, `memories.*`, `notes.enable` and
`users.enable_status` (`backend/open_webui/routers/auths.py:104-136`). Both **Authentication** and
**General** post the whole set as they loaded it (`src/lib/components/admin/Settings/Authentication.svelte:89-96`;
`src/lib/components/admin/Settings/General.svelte:80-89`), so saving one screen also re-saves the
other's keys as they were when the screen was opened.

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `auth.admin.show` | `SHOW_ADMIN_DETAILS` (`true` unless set otherwise) | on | **Authentication** › **Pending Accounts** › **Admin Details** (`src/lib/components/admin/Settings/Authentication.svelte:259-263`; `src/lib/i18n/locales/en-US/translation.json:2025`) | Whether accounts awaiting approval are shown an admin's name and email; when off, `GET /api/v1/auths/admin/details` refuses with `ACTION_PROHIBITED` | Def `backend/open_webui/config.py:2170`; read `backend/open_webui/routers/auths.py:1175-1196` |
| `auth.admin.email` | `ADMIN_EMAIL` | JSON `null` (the first account's email and name are shown) | **Authentication** › **Admin Contact Email**, shown when **Admin Details** is on (`src/lib/components/admin/Settings/Authentication.svelte:266-275`; `src/lib/i18n/locales/en-US/translation.json:2023`) | The contact shown to pending accounts; the name is looked up from the account with that email | Def `backend/open_webui/config.py:2172`; read `backend/open_webui/routers/auths.py:1176-1189`. The live value is a person's or mailbox's email address: personal data, not to be copied into tickets |
| `auth.enable_api_keys` | `ENABLE_API_KEYS` (`true` to enable) | off | **Authentication** › **User Access** › **API Keys** (`src/lib/components/admin/Settings/Authentication.svelte:189-193`; `src/lib/i18n/locales/en-US/translation.json:2037`) | Whether personal API keys can be created and used; non-admins also need the `features.api_keys` permission | Def `backend/open_webui/config.py:2454`; read `backend/open_webui/routers/auths.py:1517-1525`, `backend/open_webui/utils/auth.py:519-536`; sent to signed-in browsers (`backend/open_webui/main.py:2345`) |
| `auth.api_key.endpoint_restrictions` | `ENABLE_API_KEYS_ENDPOINT_RESTRICTIONS`, then `ENABLE_API_KEY_ENDPOINT_RESTRICTIONS` | off | **Authentication** › **API Key Endpoint Restrictions**, shown when **API Keys** is on (`src/lib/components/admin/Settings/Authentication.svelte:196-205`; `src/lib/i18n/locales/en-US/translation.json:2035`) | When on, a request made with an API key outside the allowed paths is refused with `ACCESS_PROHIBITED` | Def `backend/open_webui/config.py:2456-2462`; read `backend/open_webui/utils/auth.py:541-550` |
| `auth.api_key.allowed_endpoints` | `API_KEYS_ALLOWED_ENDPOINTS`, then `API_KEY_ALLOWED_ENDPOINTS` | empty | **Authentication** › **Allowed Endpoints**, shown when the restriction is on (`src/lib/components/admin/Settings/Authentication.svelte:210-219`; `src/lib/i18n/locales/en-US/translation.json:2031`) | Comma-separated API paths that API keys may call (a path and everything below it) | Def `backend/open_webui/config.py:2464`; read `backend/open_webui/utils/auth.py:542-545`. With the restriction on and this empty, the code allows no path |
| `auth.jwt_expiry` | `JWT_EXPIRES_IN` | `4w` | **Authentication** › **JWT Expiration** (`src/lib/components/admin/Settings/Authentication.svelte:233-240`; `src/lib/i18n/locales/en-US/translation.json:2079`) | Lifetime of sign-in tokens issued after the change (`-1` or `0` for none); also how long a sign-out revocation marker is kept in Redis | Def `backend/open_webui/config.py:2466`; read `backend/open_webui/routers/auths.py:186-189`, `:1146`, `backend/open_webui/utils/auth.py:361`; `-1` and `0` mean no expiry (`backend/open_webui/utils/misc.py:1012-1014`). A value not matching the pattern at `backend/open_webui/routers/auths.py:1289-1293` is dropped from the save without any message. `-1` shows `No expiration can pose security risks.` under the field (`src/lib/components/admin/Settings/Authentication.svelte:243-250`) |

### 7.3 `automations` (4 Keys)

Area document: [`automations-calendar-and-timers.md`](automations-calendar-and-timers.md) (sections
3 and 7). Only the switch has a field, on **General** (`src/lib/components/admin/Settings/General.svelte`,
labels under `settings.admin.general.*`). The two limits are in the shared admin field map
(`backend/open_webui/routers/auths.py:122-124`) but no screen shows them; **General** and
**Authentication** send them back as loaded, so a save leaves them unchanged.

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `automations.enable` | `ENABLE_AUTOMATIONS` (`true` unless set otherwise) | on | **General** › **Features** › **Automations** (`src/lib/components/admin/Settings/General.svelte:373-377`; `src/lib/i18n/locales/en-US/translation.json:2371`) | Gates the automation pages and API for everyone (refusal: HTTP 403 `401 Unauthorized`), the automation tools offered to models, and whether the scheduler claims due runs at all | Def `backend/open_webui/config.py:2034`; read `backend/open_webui/routers/automations.py:45-58`, `backend/open_webui/utils/tools.py:744-751`, `backend/open_webui/utils/automations.py:104-112`, `backend/open_webui/routers/calendar.py:52-59`; sent to signed-in browsers (`backend/open_webui/main.py:2358`). Non-admins also need `features.automations` |
| `automations.max_count` | `AUTOMATION_MAX_COUNT` | empty (no limit) | none (API or import only); field `AUTOMATION_MAX_COUNT` of `POST /api/v1/auths/admin/config` | Most automations a non-admin may own; checked when creating, refusal `Automation limit reached ({max_count})` | Def `backend/open_webui/config.py:2044`; saved as a whole number or empty (`backend/open_webui/routers/auths.py:1278`); read `backend/open_webui/routers/automations.py:74-83`. Admins are not limited |
| `automations.min_interval` | `AUTOMATION_MIN_INTERVAL` | empty (no limit) | none (API or import only); field `AUTOMATION_MIN_INTERVAL` | Shortest gap in seconds between runs of a non-admin's schedule, on create and update; refusal `Schedule too frequent. Minimum interval is {min_interval} seconds.` | Def `backend/open_webui/config.py:2046`; saved at `backend/open_webui/routers/auths.py:1279-1281`; read `backend/open_webui/routers/automations.py:85-95` |
| `automations.auth_token_expires_in` | `AUTOMATION_AUTH_TOKEN_EXPIRES_IN` | `1h` | none (API or import only); not in any admin field map | Lifetime of the credential an automation run uses on its owner's behalf; an unreadable value, `-1` or `0` falls back to one hour | Def `backend/open_webui/config.py:2048`; read `backend/open_webui/utils/automations.py:384-391`. Only an import or a database change alters it after first boot. Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca) |

### 7.4 `calendar` (1 Key)

Area document: [`automations-calendar-and-timers.md`](automations-calendar-and-timers.md).

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `calendar.enable` | `ENABLE_CALENDAR` (`true` unless set otherwise) | on | **General** › **Features** › **Calendar** (`src/lib/components/admin/Settings/General.svelte:366-370`; `src/lib/i18n/locales/en-US/translation.json:2374`) | Gates the calendar API for everyone (refusal: HTTP 403 `401 Unauthorized`), the calendar tools offered to models, and whether the scheduler sends event reminders | Def `backend/open_webui/config.py:2032`; read `backend/open_webui/routers/calendar.py:37-49`, `backend/open_webui/utils/tools.py:753-757`, `backend/open_webui/utils/automations.py:116-121`; sent to signed-in browsers (`backend/open_webui/main.py:2357`). Non-admins also need `features.calendar` |

### 7.5 `channels` (2 Keys)

Area document: [`channels-and-direct-messages.md`](channels-and-direct-messages.md) (sections 3.1,
5.6 and 7).

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `channels.enable` | `ENABLE_CHANNELS` (`true` to enable) | **off** | **General** › **Features** › **Channels** (`src/lib/components/admin/Settings/General.svelte:343-347`; `src/lib/i18n/locales/en-US/translation.json:2376`) | The whole channels feature; while off every channel request, admins' included, is refused with HTTP 403 `Channels is disabled`, and channel tools and channel-targeted automations are unavailable | Def `backend/open_webui/config.py:2028`; read `backend/open_webui/routers/channels.py:141-156`, `backend/open_webui/utils/tools.py:723-732`, `backend/open_webui/routers/automations.py:109-118`, `backend/open_webui/utils/automations.py:259-261`; sent to signed-in browsers (`backend/open_webui/main.py:2356`) |
| `channels.model_response_mode` | `CHANNEL_MODEL_RESPONSE_MODE` | `thread` | **General** › **Model Response Mode**: `Thread` or `Channel`, shown while **Channels** is on (`src/lib/components/admin/Settings/General.svelte:349-361`; `src/lib/i18n/locales/en-US/translation.json:2397`) | Whether a model's answer to a top-level channel message is posted in a thread under it or in the channel itself; also applies to channel automations | Def `backend/open_webui/config.py:2030`; read `backend/open_webui/routers/channels.py:1015-1021`, `backend/open_webui/utils/automations.py:280-284`. A value other than `thread` or `channel` is dropped from the save without a message (`backend/open_webui/routers/auths.py:1286-1287`) |

### 7.6 `chat` (7 Keys)

Area documents: [`chat-completion-pipeline-and-generation-tasks.md`](chat-completion-pipeline-and-generation-tasks.md)
(context compaction) and [`chat-composer-and-message-display.md`](chat-composer-and-message-display.md)
(tool approval in the input menu). The screen is **Interface**
(`src/lib/components/admin/Settings/Interface.svelte`, section **Chat**, labels under
`settings.admin.interface.*`); **Save** posts these keys to `POST /api/v1/chats/config` together with
the `task.*` keys (`src/lib/components/admin/Settings/Interface.svelte:64-86`, `:164-169`). The
endpoint's map is `backend/open_webui/routers/chats.py:51-59`; it corrects numbers before storing
them (`:841-857`).

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `chat.tool_permissions.enable` | `ENABLE_TOOL_PERMISSIONS` (`true` to enable) | off | **Interface** › **Chat** › **Tool Permissions** (`src/lib/components/admin/Settings/Interface.svelte:260-268`; `src/lib/i18n/locales/en-US/translation.json:2533`) | When on, the chat input menu offers full access or approval before tools run, and the server honours the choice; when off, tools run with full access | Def `backend/open_webui/config.py:2196`; read `backend/open_webui/main.py:1255-1264` (automations and channel messages always run with full access); sent to signed-in browsers (`:2361`) |
| `chat.context_compaction.enable` | `ENABLE_CONTEXT_COMPACTION` (`true` to enable) | off | **Interface** › **Context Compaction** (`src/lib/components/admin/Settings/Interface.svelte:272-276`; `src/lib/i18n/locales/en-US/translation.json:2492`) | Summarizes older chat history when the estimated context grows past the threshold | Def `backend/open_webui/config.py:2194`; read `backend/open_webui/utils/context_compaction.py:198-213`; sent to signed-in browsers (`backend/open_webui/main.py:2360`) |
| `chat.context_compaction.model` | `CONTEXT_COMPACTION_MODEL` | empty (`Current Model`, the chat's own model) | **Interface** › **Context Compaction Model**, shown while compaction is on (`src/lib/components/admin/Settings/Interface.svelte:280-301`; `src/lib/i18n/locales/en-US/translation.json:2494`) | Model that writes the summaries; a model that is not available falls back to the chat's model | Def `backend/open_webui/config.py:2192`; read `backend/open_webui/utils/context_compaction.py:348-355`. Choosing a model that is not public shows `This model is not publicly available. Please select another model.` (`src/lib/components/admin/Settings/Interface.svelte:103-110`) |
| `chat.context_compaction.token_threshold` | `CONTEXT_COMPACTION_TOKEN_THRESHOLD` (a whole number) | `80000` | **Interface** › **Token Threshold** (`src/lib/components/admin/Settings/Interface.svelte:305-313`; `src/lib/i18n/locales/en-US/translation.json:2531`) | Estimated token count above which older messages are summarized | Def `backend/open_webui/config.py:2198`; saved as at least 1 (`backend/open_webui/routers/chats.py:843`); read `backend/open_webui/utils/context_compaction.py:206` |
| `chat.context_compaction.token_cap` | `CONTEXT_COMPACTION_TOKEN_CAP` (read into a helper variable) | JSON `null` (the threshold is used) | **Interface** › **Token Cap** (`src/lib/components/admin/Settings/Interface.svelte:318-326`; `src/lib/i18n/locales/en-US/translation.json:2529`) | Upper limit for per-model compaction thresholds | Def `backend/open_webui/config.py:2200-2201`; a save stores the threshold when the field is empty (`backend/open_webui/routers/chats.py:844`); read `backend/open_webui/utils/context_compaction.py:210` |
| `chat.context_compaction.retention_percentage` | `CONTEXT_COMPACTION_RETENTION_PERCENTAGE` (a whole number, kept between 10 and 50) | `40` | **Interface** › **Retained Messages** (`src/lib/components/admin/Settings/Interface.svelte:331-340`; `src/lib/i18n/locales/en-US/translation.json:2510`) | Percentage of recent messages kept after older ones are summarized | Def `backend/open_webui/config.py:2203-2205`; clamped to 10 to 50 on save and on use (`backend/open_webui/routers/chats.py:845`; `backend/open_webui/utils/context_compaction.py:224-229`) |
| `chat.context_compaction.prompt_template` | `CONTEXT_COMPACTION_PROMPT_TEMPLATE` | empty (the built-in prompt) | **Interface** › **Context Compaction Prompt** (`src/lib/components/admin/Settings/Interface.svelte:345-351`; `src/lib/i18n/locales/en-US/translation.json:2496`) | Instructions used to rewrite older messages into a running summary | Def `backend/open_webui/config.py:2207`; read `backend/open_webui/utils/context_compaction.py:212`, `:357` |

### 7.7 `code_execution` (7 Keys)

Area document: [`code-execution-and-interpreter.md`](code-execution-and-interpreter.md). The screen
is **Code Execution** (`src/lib/components/admin/Settings/CodeExecution.svelte`, address
`/admin/settings/code-execution`), section **Code Execution**, labels under
`settings.admin.codeExecution.*` (`src/lib/i18n/locales/en-US/translation.json:2137-2167`). **Save**
posts all 15 `code_execution.*` and `code_interpreter.*` fields at once
(`src/lib/components/admin/Settings/CodeExecution.svelte:26-28`, `:39-44`) to
`POST /api/v1/configs/code_execution` (`backend/open_webui/routers/configs.py:45-61`, `:709-728`).
These keys drive the **Run** button on Python code blocks in answers.

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `code_execution.enable` | `ENABLE_CODE_EXECUTION` (`true` unless set otherwise) | on | **Code Execution** › **Enable Code Execution** (`src/lib/components/admin/Settings/CodeExecution.svelte:56-61`; `src/lib/i18n/locales/en-US/translation.json:2162`) | Shows the **Run** button on Python code blocks; the server's execution endpoint refuses with HTTP 403 `Code execution is disabled` while off | Def `backend/open_webui/config.py:409`; read `backend/open_webui/routers/utils.py:41-47`, `src/lib/components/chat/Messages/CodeBlock.svelte:498`; sent to signed-in browsers (`backend/open_webui/main.py:2365`) |
| `code_execution.engine` | `CODE_EXECUTION_ENGINE` | `pyodide` | **Code Execution** › **Code Execution Engine**: `pyodide` or `jupyter (Legacy)`, shown while enabled (`src/lib/components/admin/Settings/CodeExecution.svelte:64-82`; `src/lib/i18n/locales/en-US/translation.json:2138`) | `pyodide` runs code in the user's browser; `jupyter` sends it through the server to a Jupyter server | Def `backend/open_webui/config.py:411`; the browser decides (`src/lib/components/chat/Messages/CodeBlock.svelte:148`) from `/api/config` (`backend/open_webui/main.py:2400`); the server endpoint runs only `jupyter` (`backend/open_webui/routers/utils.py:49-71`). Choosing `jupyter` replaces the description with a security warning (`src/lib/components/admin/Settings/CodeExecution.svelte:67-71`) |
| `code_execution.jupyter.url` | `CODE_EXECUTION_JUPYTER_URL` | empty | **Code Execution** › **Jupyter URL**, shown for `jupyter` (`src/lib/components/admin/Settings/CodeExecution.svelte:85-96`; `src/lib/i18n/locales/en-US/translation.json:2147`) | Jupyter server used by the **Run** button | Def `backend/open_webui/config.py:413`; read `backend/open_webui/routers/utils.py:51`. Also the fallback seed for `code_interpreter.jupyter.url` |
| `code_execution.jupyter.auth` | `CODE_EXECUTION_JUPYTER_AUTH` | empty (`None`) | **Code Execution** › **Jupyter Auth**: `None`, `Token` or `Password` (`src/lib/components/admin/Settings/CodeExecution.svelte:105-116`; `src/lib/i18n/locales/en-US/translation.json:2140`) | Which credential is sent to Jupyter | Def `backend/open_webui/config.py:415`; read `backend/open_webui/routers/utils.py:55`, `:60` |
| `code_execution.jupyter.auth_token` | `CODE_EXECUTION_JUPYTER_AUTH_TOKEN` | secret (set per environment) | **Code Execution** › **Jupyter Token**, shown for `Token` (`src/lib/components/admin/Settings/CodeExecution.svelte:124`, `:137-142`; `src/lib/i18n/locales/en-US/translation.json:2143`) | Jupyter token | Def `backend/open_webui/config.py:417`; read `backend/open_webui/routers/utils.py:54` |
| `code_execution.jupyter.auth_password` | `CODE_EXECUTION_JUPYTER_AUTH_PASSWORD` | secret (set per environment) | **Code Execution** › **Jupyter Password**, shown for `Password` (`src/lib/components/admin/Settings/CodeExecution.svelte:123`, `:129-134`; `src/lib/i18n/locales/en-US/translation.json:2142`) | Jupyter password | Def `backend/open_webui/config.py:420`; read `backend/open_webui/routers/utils.py:59` |
| `code_execution.jupyter.timeout` | `CODE_EXECUTION_JUPYTER_TIMEOUT` (a whole number of seconds) | `60` | **Code Execution** › **Code Execution Timeout**, shown for `jupyter` (`src/lib/components/admin/Settings/CodeExecution.svelte:150-158`; `src/lib/i18n/locales/en-US/translation.json:2145`) | Longest a run may take on Jupyter | Def `backend/open_webui/config.py:422`; read `backend/open_webui/routers/utils.py:63` |

### 7.8 `code_interpreter` (8 Keys)

Area document: [`code-execution-and-interpreter.md`](code-execution-and-interpreter.md). Same
screen, section **Code Interpreter**, same save as 7.7. These keys drive the **Code Interpreter**
feature, in which the model itself runs code during a chat. Each `jupyter.*` key falls back to the
matching `CODE_EXECUTION_JUPYTER_*` variable when its own variable is unset.

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `code_interpreter.enable` | `ENABLE_CODE_INTERPRETER` (`true` unless set otherwise) | on | **Code Execution** › **Code Interpreter** › **Enable Code Interpreter** (`src/lib/components/admin/Settings/CodeExecution.svelte:171-175`; `src/lib/i18n/locales/en-US/translation.json:2164`) | Offers the code interpreter in the chat input and as the `execute_code` tool; non-admins also need `features.code_interpreter` | Def `backend/open_webui/config.py:424`; read `backend/open_webui/utils/tools.py:706-715`, `backend/open_webui/utils/middleware.py:4877-4890`; sent to signed-in browsers (`backend/open_webui/main.py:2366`; `src/lib/components/chat/MessageInput.svelte:840`) |
| `code_interpreter.engine` | `CODE_INTERPRETER_ENGINE` | `pyodide` | **Code Execution** › **Code Interpreter Engine**: `pyodide` or `jupyter (Legacy)` (`src/lib/components/admin/Settings/CodeExecution.svelte:178-196`; `src/lib/i18n/locales/en-US/translation.json:2149`) | `pyodide` runs the model's code in the user's open browser tab; `jupyter` runs it on the Jupyter server | Def `backend/open_webui/config.py:433`; read `backend/open_webui/tools/builtin.py:688-735`, `backend/open_webui/utils/middleware.py:6393-6423`. Background sub-agents drop the interpreter unless the engine is `jupyter` (`backend/open_webui/utils/subagents.py:311-316`). Sent to signed-in browsers (`backend/open_webui/main.py:2401`) |
| `code_interpreter.prompt_template` | `CODE_INTERPRETER_PROMPT_TEMPLATE` | empty (the built-in prompt) | **Code Execution** › **Code Interpreter Prompt Template** (`src/lib/components/admin/Settings/CodeExecution.svelte:280-288`; `src/lib/i18n/locales/en-US/translation.json:2160`) | Instructions added to the chat when the interpreter is used with legacy function calling | Def `backend/open_webui/config.py:435`; read `backend/open_webui/utils/middleware.py:2722-2733` (not used with native function calling) |
| `code_interpreter.jupyter.url` | `CODE_INTERPRETER_JUPYTER_URL`, then `CODE_EXECUTION_JUPYTER_URL` | empty | **Code Execution** › **Jupyter URL**, shown for `jupyter` (`src/lib/components/admin/Settings/CodeExecution.svelte:199-210`; `src/lib/i18n/locales/en-US/translation.json:2158`) | Jupyter server for the interpreter | Def `backend/open_webui/config.py:437`; read `backend/open_webui/tools/builtin.py:730`, `backend/open_webui/utils/middleware.py:6408` |
| `code_interpreter.jupyter.auth` | `CODE_INTERPRETER_JUPYTER_AUTH`, then `CODE_EXECUTION_JUPYTER_AUTH` | empty (`None`) | **Code Execution** › **Jupyter Auth** (`src/lib/components/admin/Settings/CodeExecution.svelte:219-230`; `src/lib/i18n/locales/en-US/translation.json:2151`) | Which credential is sent | Def `backend/open_webui/config.py:439-442`; read `backend/open_webui/tools/builtin.py:727`, `backend/open_webui/utils/middleware.py:6412`, `:6417` |
| `code_interpreter.jupyter.auth_token` | `CODE_INTERPRETER_JUPYTER_AUTH_TOKEN`, then `CODE_EXECUTION_JUPYTER_AUTH_TOKEN` | secret (set per environment) | **Code Execution** › **Jupyter Token** (`src/lib/components/admin/Settings/CodeExecution.svelte:238`, `:251-256`; `src/lib/i18n/locales/en-US/translation.json:2154`) | Jupyter token | Def `backend/open_webui/config.py:444-447`; read `backend/open_webui/tools/builtin.py:732`, `backend/open_webui/utils/middleware.py:6411` |
| `code_interpreter.jupyter.auth_password` | `CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD`, then `CODE_EXECUTION_JUPYTER_AUTH_PASSWORD` | secret (set per environment) | **Code Execution** › **Jupyter Password** (`src/lib/components/admin/Settings/CodeExecution.svelte:237`, `:243-248`; `src/lib/i18n/locales/en-US/translation.json:2153`) | Jupyter password | Def `backend/open_webui/config.py:450-453`; read `backend/open_webui/tools/builtin.py:733`, `backend/open_webui/utils/middleware.py:6416` |
| `code_interpreter.jupyter.timeout` | `CODE_INTERPRETER_JUPYTER_TIMEOUT`, then `CODE_EXECUTION_JUPYTER_TIMEOUT` | `60` | **Code Execution** › **Code Execution Timeout** (`src/lib/components/admin/Settings/CodeExecution.svelte:264-272`; `src/lib/i18n/locales/en-US/translation.json:2156`) | Longest an interpreter run may take on Jupyter | Def `backend/open_webui/config.py:455-460`; read `backend/open_webui/tools/builtin.py:734`, `backend/open_webui/utils/middleware.py:6420` |

Saving the screen publishes `config.code_execution.updated` with the two switches and two engines
(`backend/open_webui/routers/configs.py:715-727`; section 9).

### 7.9 `direct` (2 Keys)

Area documents: [`model-connections-openai-ollama-and-direct.md`](model-connections-openai-ollama-and-direct.md)
(direct connections) and
[`workspace-tools-tool-servers-mcp-and-terminals.md`](workspace-tools-tool-servers-mcp-and-terminals.md)
(direct integrations). Both keys are saved through `POST /api/v1/configs/connections`, which stores
only the fields sent (`backend/open_webui/routers/configs.py:40-44`, `:144-160`). The server reads
them only to report them to browsers (`backend/open_webui/main.py:2264-2265`, `:2351-2352`): what
they show or hide happens in the browser.

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `direct.enable` | `ENABLE_DIRECT_CONNECTIONS` (`true` to enable) | off | **Connections** › **User Connections** › **Direct Connections** (`src/lib/components/admin/Settings/Connections.svelte:372-383`; `src/lib/i18n/locales/en-US/translation.json:2172`) | Lets users add their own OpenAI-compatible endpoints in their personal settings | Def `backend/open_webui/config.py:230`. **Saves on change** (`src/lib/components/admin/Settings/Connections.svelte:379-381`, `:113-123`) |
| `direct.integrations.enable` | `ENABLE_DIRECT_INTEGRATIONS` (`true` to enable) | off | **Integrations** › **User Connections** › **Direct Integrations** (`src/lib/components/admin/Settings/Integrations.svelte:344-353`; `src/lib/i18n/locales/en-US/translation.json:2174`) | Shows the personal **Integrations** tab to users allowed to manage their own tool and terminal connections; the screen's description says hiding it does not disable existing connections | Def `backend/open_webui/config.py:231`. **Saves on change** (`src/lib/components/admin/Settings/Integrations.svelte:61-70`, `:352-353`) |

### 7.10 `evaluation` (2 Keys)

Area document: [`evaluations-feedback-and-analytics.md`](evaluations-feedback-and-analytics.md).
The screen is **Evaluations** (`src/lib/components/admin/Settings/Evaluations.svelte`, labels under
`settings.admin.evaluations.*`); it posts to `POST /api/v1/evaluations/config`, which stores only
the fields sent and publishes `config.updated` (`backend/open_webui/routers/evaluations.py:300-324`).

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `evaluation.arena.enable` | `ENABLE_EVALUATION_ARENA_MODELS` (`true` unless set otherwise) | on | **Evaluations** › **Arena Models** switch (`src/lib/components/admin/Settings/Evaluations.svelte:101-111`; `src/lib/i18n/locales/en-US/translation.json:2366`) | Adds the arena models to the model list; with none configured, a single built-in `Arena Model` is added | Def `backend/open_webui/config.py:2054`; read `backend/open_webui/utils/models.py:69-75`, `:115-149`; built-in model `backend/open_webui/config.py:2067-2078`. Saved by **Save**. The description reads `Message rating should be enabled to use this feature` |
| `evaluation.arena.models` | `EVALUATION_ARENA_MODELS` (a JSON list of objects; anything else gives an empty list) | `[]` | **Evaluations** › **Models** › **Arena Models** list and **Add Arena Model**, shown while the switch is on (`src/lib/components/admin/Settings/Evaluations.svelte:115-145`; `src/lib/i18n/locales/en-US/translation.json:2364`) | The arena models offered (name, picture, description, which models they draw from, and who may use them) | Def `backend/open_webui/config.py:2055-2065`; read `backend/open_webui/utils/models.py:118-133`, `backend/open_webui/routers/models.py:806-816`. Adding, editing or deleting an arena model **saves at once** (`src/lib/components/admin/Settings/Evaluations.svelte:45-73`). At start-up, entries in the old access-control format are converted and written back (`backend/open_webui/main.py:660-664`) |

### 7.11 `file` (2 Keys)

Area document: [`files-uploads-and-storage.md`](files-uploads-and-storage.md). The screen is
**Documents** (`src/lib/components/admin/Settings/Documents.svelte`), section **Files**, labels under
`settings.admin.documents.*`; it saves through `POST /api/v1/retrieval/config/update`, where an
empty field means "clear" and a missing one "leave unchanged"
(`backend/open_webui/routers/retrieval.py:1280-1293`; `src/lib/components/admin/Settings/Documents.svelte:264-271`).
Both keys are applied in the browser, which resizes pictures before upload
(`backend/open_webui/main.py:2413-2419`).

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `file.image_compression_width` | `FILE_IMAGE_COMPRESSION_WIDTH` (a whole number) | JSON `null` (no compression) | **Documents** › **Files** › **Image Compression Width** (`src/lib/components/admin/Settings/Documents.svelte:1499-1506`; `src/lib/i18n/locales/en-US/translation.json:2276`) | Largest width, in pixels, of pictures attached in chats, channels and notes; a user's own compression size can only be smaller | Def `backend/open_webui/config.py:989-991`; applied at `src/lib/components/chat/MessageInput.svelte:1132-1159`, `src/lib/components/channel/MessageInput.svelte:385-386`, `src/lib/components/notes/NoteEditor.svelte:573-574` |
| `file.image_compression_height` | `FILE_IMAGE_COMPRESSION_HEIGHT` (a whole number) | JSON `null` (no compression) | **Documents** › **Files** › **Image Compression Height** (`src/lib/components/admin/Settings/Documents.svelte:1512-1519`; `src/lib/i18n/locales/en-US/translation.json:2274`) | Largest height, in pixels, on the same terms | Def `backend/open_webui/config.py:993-995`; applied at the same places |

### 7.12 `folders` (2 Keys)

Area document: [`chat-conversations-history-and-organisation.md`](chat-conversations-history-and-organisation.md).
Both keys are on **General** and are saved through the shared admin endpoint described in 7.2.

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `folders.enable` | `ENABLE_FOLDERS` (`true` unless set otherwise) | on | **General** › **Features** › **Folders** (`src/lib/components/admin/Settings/General.svelte:293-297`; `src/lib/i18n/locales/en-US/translation.json:2386`) | Chat folders; while off, folder requests are refused with `ACCESS_PROHIBITED` (HTTP 403). Non-admins also need `features.folders` | Def `backend/open_webui/config.py:2024`; read `backend/open_webui/routers/folders.py:66-82`; sent to signed-in browsers (`backend/open_webui/main.py:2354`) |
| `folders.max_file_count` | `FOLDER_MAX_FILE_COUNT` | empty (no limit) | **General** › **Folder Max File Count**, shown while **Folders** is on (`src/lib/components/admin/Settings/General.svelte:300-310`; `src/lib/i18n/locales/en-US/translation.json:2384`) | Most files a folder may hold; saving a folder with more shows `Maximum number of files per folder is {max}.` | Def `backend/open_webui/config.py:2026`; saved as a whole number or empty (`backend/open_webui/routers/auths.py:1277`). Checked in the browser (`src/lib/components/layout/Sidebar/Folders/FolderModal.svelte:46-54`) from `/api/config` (`backend/open_webui/main.py:2355`); no server-side check was found (section 14) |

### 7.13 `google_drive` (3 Keys)

Area document: [`files-uploads-and-storage.md`](files-uploads-and-storage.md) (attaching from cloud
drives). Only the switch has a field, on **Documents** › **Integration**. The browser's Google Drive
picker receives the client ID and API key from the **environment** constants, not from these keys
(`backend/open_webui/main.py:2422-2425`; `backend/open_webui/config.py:845-847`).

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `google_drive.enable` | `ENABLE_GOOGLE_DRIVE_INTEGRATION` (`true` to enable) | off | **Documents** › **Integration** › **Google Drive** (`src/lib/components/admin/Settings/Documents.svelte:1529-1534`; `src/lib/i18n/locales/en-US/translation.json:2267`) | Offers Google Drive as a source for attachments | Def `backend/open_webui/config.py:843`; saved at `backend/open_webui/routers/retrieval.py:1302-1306`; read only to tell browsers (`backend/open_webui/main.py:2285`, `:2376`) |
| `google_drive.client_id` | `GOOGLE_DRIVE_CLIENT_ID` | empty | none (API or import only) | **Inert row**: no code reads the key | Def `backend/open_webui/config.py:845`. Change the environment variable and restart instead |
| `google_drive.api_key` | `GOOGLE_DRIVE_API_KEY` | secret (set per environment) | none (API or import only) | **Inert row**: no code reads the key | Def `backend/open_webui/config.py:847`. As above |

### 7.14 `image_generation` (20 Keys)

Area document: [`image-generation-and-editing.md`](image-generation-and-editing.md). The screen is
**Images** (`src/lib/components/admin/Settings/Images.svelte`), section **Create Image**, labels
under `settings.admin.images.*` (`src/lib/i18n/locales/en-US/translation.json:2415-2472`). **Save**
checks the form in the browser (`src/lib/components/admin/Settings/Images.svelte:110-134`,
`:176-211`) and posts all 33 `image_generation.*` and `images.*` fields to
`POST /api/v1/images/config/update`, which checks size and steps, stores everything, sets the model
and publishes `config.updated` (`backend/open_webui/routers/images.py:67-102`, `:276-319`). The
generation code reads the keys through that field map (`backend/open_webui/routers/images.py:110-111`).

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `image_generation.enable` | `ENABLE_IMAGE_GENERATION` (`true` to enable) | off | **Images** › **Image Generation** (`src/lib/components/admin/Settings/Images.svelte:311-315`; `src/lib/i18n/locales/en-US/translation.json:2442`) | Image creation from chats, the `generate_image` tool and the generation endpoint (refusal: HTTP 403 `ACCESS_PROHIBITED`); non-admins also need `features.image_generation` | Def `backend/open_webui/config.py:1351`; read `backend/open_webui/routers/images.py:562-577`, `backend/open_webui/utils/tools.py:689-696`, `backend/open_webui/utils/middleware.py:1865-1868`, `:1935-1946`; sent to signed-in browsers (`backend/open_webui/main.py:2367`). A save with the engine's required field empty shows a message and turns the switch off on the screen without saving (section 10) |
| `image_generation.engine` | `IMAGE_GENERATION_ENGINE` | `openai` | **Images** › **Create Image** › **Image Generation Engine**: `Default (Open AI)`, `ComfyUI`, `Automatic1111`, `Gemini` (`src/lib/components/admin/Settings/Images.svelte:321-331`; `src/lib/i18n/locales/en-US/translation.json:2444`) | Which service creates pictures; an empty value is treated as Automatic1111 | Def `backend/open_webui/config.py:1353`; read `backend/open_webui/routers/images.py:621`, `:681`, `:739`, `:794` |
| `image_generation.model` | `IMAGE_GENERATION_MODEL` | empty (`dall-e-2` for OpenAI, `imagen-3.0-generate-002` for Gemini, the server's current checkpoint for Automatic1111) | **Images** › **Model**, shown while generation is on (`src/lib/components/admin/Settings/Images.svelte:337-346`; `src/lib/i18n/locales/en-US/translation.json:2445`) | Model sent to the service | Def `backend/open_webui/config.py:1355`; read `backend/open_webui/routers/images.py:202-225`. Saving with Automatic1111 also switches that server's checkpoint (`:172-199`) |
| `image_generation.size` | `IMAGE_SIZE` | `512x512` | **Images** › **Image Size** (`src/lib/components/admin/Settings/Images.svelte:355-359`; `src/lib/i18n/locales/en-US/translation.json:2461`) | Picture size `WIDTHxHEIGHT`; `auto` is allowed only for models matching `IMAGE_AUTO_SIZE_MODELS_REGEX_PATTERN` (code default `^gpt-image`) | Def `backend/open_webui/config.py:1363`; checked at `backend/open_webui/routers/images.py:278-293`; read `:607-614`, `:639-640` |
| `image_generation.steps` | `IMAGE_STEPS` (a whole number) | `50` | **Images** › **Steps**, shown for `ComfyUI` and `Automatic1111` (`src/lib/components/admin/Settings/Images.svelte:363-370`; `src/lib/i18n/locales/en-US/translation.json:2470`) | Sampling steps | Def `backend/open_webui/config.py:1365`; a negative value is refused (`backend/open_webui/routers/images.py:295-299`); read `:747-748`, `:809-810` |
| `image_generation.prompt.enable` | `ENABLE_IMAGE_PROMPT_GENERATION` (`true` unless set otherwise) | on | **Images** › **Image Prompt Generation**, shown while generation is on (`src/lib/components/admin/Settings/Images.svelte:376-381`; `src/lib/i18n/locales/en-US/translation.json:2447`) | Asks the chat model to write the image prompt before the picture is requested | Def `backend/open_webui/config.py:1367`; read `backend/open_webui/utils/middleware.py:1950-1956` |
| `image_generation.openai.api_base_url` | `IMAGES_OPENAI_API_BASE_URL` | `https://api.openai.com/v1` | **Images** › **API Base URL**, shown for `Default (Open AI)` (`src/lib/components/admin/Settings/Images.svelte:390-395`; `src/lib/i18n/locales/en-US/translation.json:2462`) | Address of the OpenAI-compatible image service | Def `backend/open_webui/config.py:1505`, fallback `:367`; read `backend/open_webui/routers/images.py:630` |
| `image_generation.openai.api_key` | `IMAGES_OPENAI_API_KEY`; otherwise the key paired with OpenAI's address in `OPENAI_API_KEYS` or `OPENAI_API_KEY` | secret (set per environment) | **Images** › **API Key** (`src/lib/components/admin/Settings/Images.svelte:399-403`; `src/lib/i18n/locales/en-US/translation.json:2463`) | Credential for that service; the screen requires it for this engine | Def `backend/open_webui/config.py:1508`, fallback `:361-366`; read `backend/open_webui/routers/images.py:623` |
| `image_generation.openai.api_version` | `IMAGES_OPENAI_API_VERSION` | empty | **Images** › **API Version** (`src/lib/components/admin/Settings/Images.svelte:410-415`; `src/lib/i18n/locales/en-US/translation.json:2466`) | When set, added to the request address as `api-version` (Azure-style services) | Def `backend/open_webui/config.py:1506`; read `backend/open_webui/routers/images.py:631-632` |
| `image_generation.openai.params` | `IMAGES_OPENAI_PARAMS` (JSON object; invalid JSON gives `{}`) | `{}` | **Images** › **Additional Parameters** (`src/lib/components/admin/Settings/Images.svelte:420-425`; `src/lib/i18n/locales/en-US/translation.json:2465`) | Extra fields merged last into each OpenAI image request | Def `backend/open_webui/config.py:1510-1517`; read `backend/open_webui/routers/images.py:651`. Field name and variable differ (section 4.1) |
| `image_generation.automatic1111.base_url` | `AUTOMATIC1111_BASE_URL` | empty | **Images** › **Base URL** with **verify connection**, shown for `Automatic1111` (`src/lib/components/admin/Settings/Images.svelte:430-444`; `src/lib/i18n/locales/en-US/translation.json:2418`) | Address of the stable-diffusion-webui server; the screen requires it for this engine | Def `backend/open_webui/config.py:1369`; read `backend/open_webui/routers/images.py:820` |
| `image_generation.automatic1111.api_auth` | `AUTOMATIC1111_API_AUTH` | secret (set per environment) | **Images** › **API Auth String** (`src/lib/components/admin/Settings/Images.svelte:479-485`; `src/lib/i18n/locales/en-US/translation.json:2416`) | Sign-in sent to that server | Def `backend/open_webui/config.py:1370`; read `backend/open_webui/routers/images.py:322-329` |
| `image_generation.automatic1111.api_params` | `AUTOMATIC1111_PARAMS` (JSON object; invalid JSON gives `{}`) | `{}` | **Images** › **Additional Parameters**, shown for `Automatic1111` (`src/lib/components/admin/Settings/Images.svelte:491-496`; `src/lib/i18n/locales/en-US/translation.json:2420`) | Extra fields merged into each Automatic1111 request | Def `backend/open_webui/config.py:1372-1378`; read `backend/open_webui/routers/images.py:815-816` |
| `image_generation.comfyui.base_url` | `COMFYUI_BASE_URL` | empty | **Images** › **Base URL** with **verify connection**, shown for `ComfyUI` (`src/lib/components/admin/Settings/Images.svelte:501-515`; `src/lib/i18n/locales/en-US/translation.json:2425`) | Address of the ComfyUI server; the screen requires it for this engine | Def `backend/open_webui/config.py:1380`; trailing slashes removed on save (`backend/open_webui/routers/images.py:302`); read `:768` |
| `image_generation.comfyui.api_key` | `COMFYUI_API_KEY` | secret (set per environment) | **Images** › **API Key**, shown for `ComfyUI` (`src/lib/components/admin/Settings/Images.svelte:550-556`; `src/lib/i18n/locales/en-US/translation.json:2423`) | ComfyUI credential, sent only when set | Def `backend/open_webui/config.py:1382`; read `backend/open_webui/routers/images.py:769`, `:777-778` |
| `image_generation.comfyui.workflow` | `COMFYUI_WORKFLOW` | a built-in workflow (JSON text) | **Images** › **ComfyUI Workflow** (upload or edit) (`src/lib/components/admin/Settings/Images.svelte:580-635`; `src/lib/i18n/locales/en-US/translation.json:2427`) | The ComfyUI workflow used for generation | Def `backend/open_webui/config.py:1495`, built-in text `:1384-1492`; read `backend/open_webui/routers/images.py:757`. Invalid JSON stops the save with `Invalid JSON format for ComfyUI Workflow.` (`src/lib/components/admin/Settings/Images.svelte:179-184`) |
| `image_generation.comfyui.nodes` | `COMFYUI_WORKFLOW_NODES` (JSON list; invalid JSON gives `[]`) | `[]` | **Images** › **ComfyUI Workflow Nodes**, shown when a workflow is present (`src/lib/components/admin/Settings/Images.svelte:642-690`; `src/lib/i18n/locales/en-US/translation.json:2434`) | Which workflow nodes receive the prompt, size, steps and other inputs | Def `backend/open_webui/config.py:1497-1503`; rebuilt from the screen's node table on each save while a workflow is present (`src/lib/components/admin/Settings/Images.svelte:186-193`); read `backend/open_webui/routers/images.py:758` |
| `image_generation.gemini.api_base_url` | `IMAGES_GEMINI_API_BASE_URL`, then `GEMINI_API_BASE_URL` | empty | **Images** › **Base URL**, shown for `Gemini` (`src/lib/components/admin/Settings/Images.svelte:694-700`; `src/lib/i18n/locales/en-US/translation.json:2458`) | Gemini image address | Def `backend/open_webui/config.py:1520`, fallback `:326`; read `backend/open_webui/routers/images.py:708` |
| `image_generation.gemini.api_key` | `IMAGES_GEMINI_API_KEY`, then `GEMINI_API_KEY` | secret (set per environment) | **Images** › **API Key**, shown for `Gemini` (`src/lib/components/admin/Settings/Images.svelte:705-711`; `src/lib/i18n/locales/en-US/translation.json:2460`) | Gemini credential; the screen requires it for this engine | Def `backend/open_webui/config.py:1521`, fallback `:325`; read `backend/open_webui/routers/images.py:684` |
| `image_generation.gemini.endpoint_method` | `IMAGES_GEMINI_ENDPOINT_METHOD` | empty (`predict`) | **Images** › **Gemini Endpoint Method**: `predict` or `generateContent` (`src/lib/components/admin/Settings/Images.svelte:717-726`; `src/lib/i18n/locales/en-US/translation.json:2432`) | Which Gemini call is used | Def `backend/open_webui/config.py:1523`; read `backend/open_webui/routers/images.py:689-704` |

### 7.15 `images` (13 Keys)

Area document: [`image-generation-and-editing.md`](image-generation-and-editing.md). Same screen,
section **Edit Image** (`src/lib/components/admin/Settings/Images.svelte:731-1018`), same save as
7.14. All 13 keys are `images.edit.*`; each `openai.*` and `gemini.*` key falls back to the general
OpenAI or Gemini variables like its 7.14 counterpart.

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `images.edit.enable` | `ENABLE_IMAGE_EDIT` (`true` to enable) | off | **Images** › **Edit Image** › **Image Edit** (`src/lib/components/admin/Settings/Images.svelte:733-737`; `src/lib/i18n/locales/en-US/translation.json:2436`) | Editing of pictures attached to a chat, the `edit_image` tool and the edit endpoint (refusal: HTTP 403 `ACCESS_PROHIBITED`); uses the `features.image_generation` permission | Def `backend/open_webui/config.py:1525`; read `backend/open_webui/routers/images.py:865-877`, `backend/open_webui/utils/tools.py:697-704`, `backend/open_webui/utils/middleware.py:1866` |
| `images.edit.engine` | `IMAGE_EDIT_ENGINE` | `openai` | **Images** › **Image Edit Engine**: `Default (Open AI)`, `ComfyUI`, `Gemini` (`src/lib/components/admin/Settings/Images.svelte:741-751`; `src/lib/i18n/locales/en-US/translation.json:2438`) | Which service edits pictures | Def `backend/open_webui/config.py:1527`; read `backend/open_webui/routers/images.py:978`, `:1059`, `:1116` |
| `images.edit.model` | `IMAGE_EDIT_MODEL` | empty | **Images** › **Model**, shown while both generation and editing are on (`src/lib/components/admin/Settings/Images.svelte:754-760`; `src/lib/i18n/locales/en-US/translation.json:2439`) | Model sent with edit requests | Def `backend/open_webui/config.py:1529`; read `backend/open_webui/routers/images.py:913` |
| `images.edit.size` | `IMAGE_EDIT_SIZE` | empty (the service's default) | **Images** › **Image Size**, same condition (`src/lib/components/admin/Settings/Images.svelte:771-775`; `src/lib/i18n/locales/en-US/translation.json:2440`) | Size of edited pictures | Def `backend/open_webui/config.py:1531`; read `backend/open_webui/routers/images.py:907-910` |
| `images.edit.openai.api_base_url` | `IMAGES_EDIT_OPENAI_API_BASE_URL` | `https://api.openai.com/v1` | **Images** › **API Base URL**, shown for `Default (Open AI)` (`src/lib/components/admin/Settings/Images.svelte:784-789`; `src/lib/i18n/locales/en-US/translation.json:2454`) | Address for OpenAI-compatible edits | Def `backend/open_webui/config.py:1535`; read `backend/open_webui/routers/images.py:1035` |
| `images.edit.openai.api_key` | `IMAGES_EDIT_OPENAI_API_KEY`; otherwise the key paired with OpenAI's address | secret (set per environment) | **Images** › **API Key** (`src/lib/components/admin/Settings/Images.svelte:794-799`; `src/lib/i18n/locales/en-US/translation.json:2455`) | Credential for edits | Def `backend/open_webui/config.py:1538`; read `backend/open_webui/routers/images.py:980` |
| `images.edit.openai.api_version` | `IMAGES_EDIT_OPENAI_API_VERSION` | empty | **Images** › **API Version** (`src/lib/components/admin/Settings/Images.svelte:806-811`; `src/lib/i18n/locales/en-US/translation.json:2456`) | `api-version` added to the edit address when set | Def `backend/open_webui/config.py:1536`; read `backend/open_webui/routers/images.py:1015-1016` |
| `images.edit.gemini.api_base_url` | `IMAGES_EDIT_GEMINI_API_BASE_URL`, then `GEMINI_API_BASE_URL` | empty | **Images** › **Base URL**, shown for `Gemini` (`src/lib/components/admin/Settings/Images.svelte:998-1003`; `src/lib/i18n/locales/en-US/translation.json:2452`) | Gemini edit address | Def `backend/open_webui/config.py:1540`; read `backend/open_webui/routers/images.py:1092` |
| `images.edit.gemini.api_key` | `IMAGES_EDIT_GEMINI_API_KEY`, then `GEMINI_API_KEY` | secret (set per environment) | **Images** › **API Key**, shown for `Gemini` (`src/lib/components/admin/Settings/Images.svelte:1008-1013`; `src/lib/i18n/locales/en-US/translation.json:2453`) | Gemini edit credential | Def `backend/open_webui/config.py:1541`; read `backend/open_webui/routers/images.py:1062` |
| `images.edit.comfyui.base_url` | `IMAGES_EDIT_COMFYUI_BASE_URL` | empty | **Images** › **Base URL** with **verify connection**, shown for `ComfyUI` (`src/lib/components/admin/Settings/Images.svelte:816-828`; `src/lib/i18n/locales/en-US/translation.json:2451`) | ComfyUI server for edits | Def `backend/open_webui/config.py:1544`; trailing slashes removed on save (`backend/open_webui/routers/images.py:303`); read `:1130`, `:1161` |
| `images.edit.comfyui.api_key` | `IMAGES_EDIT_COMFYUI_API_KEY` | secret (set per environment) | **Images** › **API Key**, shown for `ComfyUI` (`src/lib/components/admin/Settings/Images.svelte:863-869`; `src/lib/i18n/locales/en-US/translation.json:2449`) | ComfyUI edit credential, sent only when set | Def `backend/open_webui/config.py:1545`; read `backend/open_webui/routers/images.py:1131`, `:1181-1182` |
| `images.edit.comfyui.workflow` | `IMAGES_EDIT_COMFYUI_WORKFLOW` | empty (no built-in edit workflow) | **Images** › **ComfyUI Workflow** (`src/lib/components/admin/Settings/Images.svelte:893-926`; `src/lib/i18n/locales/en-US/translation.json:2427`) | The ComfyUI workflow used for edits | Def `backend/open_webui/config.py:1547`; read `backend/open_webui/routers/images.py:1150`. Invalid JSON stops the save with `Invalid JSON format for ComfyUI Edit Workflow.` (`src/lib/components/admin/Settings/Images.svelte:196-201`) |
| `images.edit.comfyui.nodes` | `IMAGES_EDIT_COMFYUI_WORKFLOW_NODES` (JSON list; invalid JSON gives `[]`) | `[]` | **Images** › **ComfyUI Workflow Nodes**, shown when an edit workflow is present (`src/lib/components/admin/Settings/Images.svelte:945-994`; `src/lib/i18n/locales/en-US/translation.json:2429`) | Which edit-workflow nodes receive the inputs | Def `backend/open_webui/config.py:1549-1555`; rebuilt from the node table on save (`src/lib/components/admin/Settings/Images.svelte:203-210`); read `backend/open_webui/routers/images.py:1151` |

### 7.16 `ldap` (17 Keys)

Area document: [`authentication-and-sign-in.md`](authentication-and-sign-in.md) (LDAP sign-in and
group mapping). The screen is **Authentication** › **LDAP**
(`src/lib/components/admin/Settings/Authentication.svelte:310-543`). **Save** first stores the
switch (`POST /api/v1/auths/admin/config/ldap`) and then, only while LDAP is on, the server fields
(`POST /api/v1/auths/admin/config/ldap/server`) (`src/lib/components/admin/Settings/Authentication.svelte:58-75`;
`backend/open_webui/routers/auths.py:1323-1361`). The server save refuses an empty **Label**,
**Host**, **Attribute for Mail**, **Attribute for Username** or **Search Base** with
`Required field {name} is empty` (`backend/open_webui/routers/auths.py:1325-1335`). Every key is
read at each LDAP sign-in (`backend/open_webui/routers/auths.py:501-546`), which also needs the
environment variable `ENABLE_PASSWORD_AUTH` (`:486-490`).

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `ldap.enable` | `ENABLE_LDAP` (`true` to enable) | off | **Authentication** › **LDAP** switch (`src/lib/components/admin/Settings/Authentication.svelte:312-316`; `src/lib/i18n/locales/en-US/translation.json:2083`) | Offers LDAP sign-in on the sign-in page; while off the LDAP endpoint answers `LDAP authentication is not enabled` | Def `backend/open_webui/config.py:2788`; read `backend/open_webui/routers/auths.py:483-484`; sent to every visitor, signed in or not (`backend/open_webui/main.py:2333`) |
| `ldap.server.label` | `LDAP_SERVER_LABEL` | `LDAP Server` | **Authentication** › **Label** (`src/lib/components/admin/Settings/Authentication.svelte:322-329`; `src/lib/i18n/locales/en-US/translation.json:2081`) | Display name of the connection on the admin screen | Def `backend/open_webui/config.py:2790`; read at `backend/open_webui/routers/auths.py:501` but not used afterwards; the sign-in page does not show it |
| `ldap.server.host` | `LDAP_SERVER_HOST` | `localhost` | **Authentication** › **Host** (`src/lib/components/admin/Settings/Authentication.svelte:336-343`; `src/lib/i18n/locales/en-US/translation.json:2077`) | Directory server address | Def `backend/open_webui/config.py:2792`; read `backend/open_webui/routers/auths.py:502`, `:527-533` |
| `ldap.server.port` | `LDAP_SERVER_PORT` (a whole number) | `389` | **Authentication** › **Port** (`src/lib/components/admin/Settings/Authentication.svelte:347-361`; `src/lib/i18n/locales/en-US/translation.json:2101`) | Directory server port; the tooltip reads `Default to 389 or 636 if TLS is enabled` | Def `backend/open_webui/config.py:2794`; may be saved empty (`backend/open_webui/routers/auths.py:1302`); read `:503` |
| `ldap.server.attribute_for_mail` | `LDAP_ATTRIBUTE_FOR_MAIL` | `mail` | **Authentication** › **Attribute for Mail** (`src/lib/components/admin/Settings/Authentication.svelte:398-411`; `src/lib/i18n/locales/en-US/translation.json:2043`) | Directory attribute used as the account's email | Def `backend/open_webui/config.py:2796`; read `backend/open_webui/routers/auths.py:504`, `:548-552` |
| `ldap.server.attribute_for_username` | `LDAP_ATTRIBUTE_FOR_USERNAME` | `uid` | **Authentication** › **Attribute for Username** (`src/lib/components/admin/Settings/Authentication.svelte:417-430`; `src/lib/i18n/locales/en-US/translation.json:2045`) | Directory attribute matched against what the user types | Def `backend/open_webui/config.py:2798`; read `backend/open_webui/routers/auths.py:505`, `:561` |
| `ldap.server.app_dn` | `LDAP_APP_DN` | empty (anonymous bind) | **Authentication** › **Application DN** (`src/lib/components/admin/Settings/Authentication.svelte:368-378`; `src/lib/i18n/locales/en-US/translation.json:2039`) | Account the server binds with to search the directory | Def `backend/open_webui/config.py:2800`; read `backend/open_webui/routers/auths.py:508`, `:534-542`; a failed bind answers `Application account bind failed` |
| `ldap.server.app_password` | `LDAP_APP_PASSWORD` | secret (set per environment) | **Authentication** › **Application DN Password** (`src/lib/components/admin/Settings/Authentication.svelte:384-391`; `src/lib/i18n/locales/en-US/translation.json:2041`) | Password for that account | Def `backend/open_webui/config.py:2802`; read `backend/open_webui/routers/auths.py:509`. Field name `app_dn_password` (section 4.1 pattern) |
| `ldap.server.users_dn` | `LDAP_SEARCH_BASE` | empty | **Authentication** › **Search Base** (`src/lib/components/admin/Settings/Authentication.svelte:437-445`; `src/lib/i18n/locales/en-US/translation.json:2115`) | Where in the directory users are searched for | Def `backend/open_webui/config.py:2804`; read `backend/open_webui/routers/auths.py:506`, `:558-561`. Field name `search_base` (section 4.1) |
| `ldap.server.search_filter` | `LDAP_SEARCH_FILTER`, then `LDAP_SEARCH_FILTERS` | empty | **Authentication** › **Search Filters** (`src/lib/components/admin/Settings/Authentication.svelte:451-457`; `src/lib/i18n/locales/en-US/translation.json:2117`) | Extra filter added to the user search | Def `backend/open_webui/config.py:2806`; read `backend/open_webui/routers/auths.py:507`, `:561`. Field name `search_filters` (section 4.1) |
| `ldap.server.use_tls` | `LDAP_USE_TLS` (`true` unless set otherwise) | on | **Authentication** › **TLS** (`src/lib/components/admin/Settings/Authentication.svelte:469-473`; `src/lib/i18n/locales/en-US/translation.json:2126`) | Connects to the directory over TLS | Def `backend/open_webui/config.py:2808`; read `backend/open_webui/routers/auths.py:510`, `:531` |
| `ldap.server.ca_cert_file` | `LDAP_CA_CERT_FILE` | empty | **Authentication** › **Certificate Path**, shown while **TLS** is on (`src/lib/components/admin/Settings/Authentication.svelte:476-484`; `src/lib/i18n/locales/en-US/translation.json:2051`) | Certificate file on the server used to check the directory's certificate | Def `backend/open_webui/config.py:2810`; read `backend/open_webui/routers/auths.py:511`, `:516-524`; a bad TLS set-up answers `Failed to configure TLS for LDAP connection.` |
| `ldap.server.validate_cert` | `LDAP_VALIDATE_CERT` (`true` unless set otherwise) | on | **Authentication** › **Validate Certificate**, shown while **TLS** is on (`src/lib/components/admin/Settings/Authentication.svelte:489-493`; `src/lib/i18n/locales/en-US/translation.json:2136`) | Whether the directory's certificate must be valid | Def `backend/open_webui/config.py:2812`; read `backend/open_webui/routers/auths.py:512`. Turning it off weakens the connection: Security-sensitive, refer to the platform maintainer and U of T Information Security (security.utoronto.ca) |
| `ldap.server.ciphers` | `LDAP_CIPHERS` | `ALL` | **Authentication** › **Ciphers**, shown while **TLS** is on (`src/lib/components/admin/Settings/Authentication.svelte:497-504`; `src/lib/i18n/locales/en-US/translation.json:2053`) | TLS cipher list; empty means `ALL` | Def `backend/open_webui/config.py:2814`; read `backend/open_webui/routers/auths.py:513` |
| `ldap.group.enable_management` | `ENABLE_LDAP_GROUP_MANAGEMENT` (`true` to enable) | off | **Authentication** › **Group Mapping** (`src/lib/components/admin/Settings/Authentication.svelte:514-518`; `src/lib/i18n/locales/en-US/translation.json:2067`) | Replaces an LDAP user's group memberships with the groups the directory lists, at each sign-in | Def `backend/open_webui/config.py:2816`; read `backend/open_webui/routers/auths.py:544`, `:553-555`, `:591-592`, `:693`. Group sync behaviour: `knowledgebase/tools/ground-truth.md` (Accounts and Access) |
| `ldap.group.enable_creation` | `ENABLE_LDAP_GROUP_CREATION` (`true` to enable) | off | **Authentication** › **Auto-Create Groups**, shown while **Group Mapping** is on (`src/lib/components/admin/Settings/Authentication.svelte:521-527`; `src/lib/i18n/locales/en-US/translation.json:2065`) | Creates groups named in the directory that do not exist yet | Def `backend/open_webui/config.py:2818`; read `backend/open_webui/routers/auths.py:545`, `:695` |
| `ldap.server.attribute_for_groups` | `LDAP_ATTRIBUTE_FOR_GROUPS` | `memberOf` | **Authentication** › **Group Attribute**, shown while **Group Mapping** is on (`src/lib/components/admin/Settings/Authentication.svelte:531-538`; `src/lib/i18n/locales/en-US/translation.json:2073`) | Directory attribute that lists a user's groups | Def `backend/open_webui/config.py:2820`; read `backend/open_webui/routers/auths.py:546`, `:591-592`. The screen fills in `memberOf` when it is left empty with mapping on (`src/lib/components/admin/Settings/Authentication.svelte:62-67`); the server refuses it empty with mapping on (`backend/open_webui/routers/auths.py:1339-1340`) |

### 7.17 `memories` (6 Keys)

Area document: [`memories.md`](memories.md) (sections 5 and 7). Only the two switches have fields,
on **General** (saved through the shared admin endpoint, 7.2); the other four keys are in no field
map, so only an import or a database change alters them after first boot.

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `memories.enable` | `ENABLE_MEMORIES` (`true` unless set otherwise) | on | **General** › **Features** › **Memories** (`src/lib/components/admin/Settings/General.svelte:316-320`; `src/lib/i18n/locales/en-US/translation.json:2391`) | The whole memories feature: the memories API (HTTP 404 with `We could not find what you're looking for :/` while off), the memory tools and the memory context in chats. Non-admins also need `features.memories` | Def `backend/open_webui/config.py:426`; read `backend/open_webui/routers/memories.py:35-47`, `backend/open_webui/utils/tools.py:656-663`, `backend/open_webui/utils/middleware.py:2686-2690`, `backend/open_webui/utils/memory.py:437`; sent to signed-in browsers (`backend/open_webui/main.py:2378`) |
| `memories.system_context.enable` | `ENABLE_MEMORY_SYSTEM_CONTEXT` (`true` unless set otherwise) | on | **General** › **Memory System Context**, shown while **Memories** is on (`src/lib/components/admin/Settings/General.svelte:322-330`; `src/lib/i18n/locales/en-US/translation.json:2393`) | Adds the person's saved memories to the system context of chats that use memory | Def `backend/open_webui/config.py:427`; read `backend/open_webui/utils/middleware.py:2686-2698` |
| `memories.background_review.enable` | `ENABLE_MEMORY_BACKGROUND_REVIEW` (`true` to enable) | off | none (API or import only); not in any admin field map | After some answers, a background task reviews the conversation for memories to save | Def `backend/open_webui/config.py:428`; read `backend/open_webui/utils/memory.py:431-438` |
| `memories.review_interval_turns` | `MEMORIES_REVIEW_INTERVAL_TURNS` (a whole number) | `10` | none (API or import only) | The review runs on every Nth message the person sends (at least 1) | Def `backend/open_webui/config.py:429`; read `backend/open_webui/utils/memory.py:440-447` |
| `memories.user_char_limit` | `MEMORIES_USER_CHAR_LIMIT` (a whole number) | `2000` | none (API or import only) | Character cap on the `[User Memory]` part of the memory context (at least 250) | Def `backend/open_webui/config.py:430`; read `backend/open_webui/utils/memory.py:375-379`, `:394-398` |
| `memories.context_char_limit` | `MEMORIES_CONTEXT_CHAR_LIMIT` (a whole number) | `2000` | none (API or import only) | Character cap on the other parts of the memory context (`[Memory Neighborhood]`, `[Relevant Context]`; at least 250) | Def `backend/open_webui/config.py:431`; read `backend/open_webui/utils/memory.py:380-383`, `:394-400` |

### 7.18 `models` (3 Keys)

Area document: [`workspace-models-and-model-access.md`](workspace-models-and-model-access.md)
(model defaults) and
[`model-connections-openai-ollama-and-direct.md`](model-connections-openai-ollama-and-direct.md)
(the base model cache).

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `models.base_models_cache` | `ENABLE_BASE_MODELS_CACHE` (`true` to enable) | off | **Connections** › **User Connections** › **Cache Base Model List**, with a **Refresh** button while on (`src/lib/components/admin/Settings/Connections.svelte:386-412`; `src/lib/i18n/locales/en-US/translation.json:2170`) | Keeps the list of provider models instead of asking the providers on every model-list request; the list is fetched at start-up and when connections are saved or refreshed | Def `backend/open_webui/config.py:374`; read `backend/open_webui/utils/models.py:69-106`; start-up fetch `backend/open_webui/main.py:407-420`; connection saves clear the cache (`backend/open_webui/routers/openai.py:347-350`; `backend/open_webui/routers/ollama.py:324-328`) and the screen reloads the list with a refresh (`src/lib/components/admin/Settings/Connections.svelte:28-36`). **Saves on change** (`src/lib/components/admin/Settings/Connections.svelte:411-412`). With Redis the cached list is shared between processes (`backend/open_webui/utils/models.py:88-104`) |
| `models.default_metadata` | `DEFAULT_MODEL_METADATA` (JSON object, read into a helper variable; invalid JSON gives `{}`) | `{}` | **Models** › **Model Defaults** › **Model Capabilities** (`src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:194`; `src/lib/i18n/locales/en-US/translation.json:2605`) | Default capabilities, default features and built-in tool choices applied to every model; a model's own settings win | Def `backend/open_webui/config.py:1695-1701`; read `backend/open_webui/utils/models.py:337-356`; readable by any signed-in user (`backend/open_webui/routers/configs.py:742-746`). Saved by the **Models** screen's **Save** (`src/lib/components/admin/Settings/Models.svelte:362-374`; `src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:105-127`) |
| `models.default_params` | `DEFAULT_MODEL_PARAMS` (JSON object, read into a helper variable; invalid JSON gives `{}`) | `{}` | **Models** › **Model Defaults** › **Model Parameters** (`src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:233`; `src/lib/i18n/locales/en-US/translation.json:2607`) | Default generation parameters for every chat request; a model's own parameters and the request's win | Def `backend/open_webui/config.py:1703-1709`; read `backend/open_webui/main.py:1169-1177`. Saved as above |

Saving through `POST /api/v1/configs/models` publishes `config.models.updated`
(`backend/open_webui/routers/configs.py:754-770`); the connections save publishes
`config.connections.updated` (`:152-159`).

### 7.19 `notes` (1 Key)

Area document: [`notes.md`](notes.md) (sections 3 and 7).

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `notes.enable` | `ENABLE_NOTES` (`true` unless set otherwise) | on | **General** › **Features** › **Notes** (`src/lib/components/admin/Settings/General.svelte:336-340`; `src/lib/i18n/locales/en-US/translation.json:2399`) | Whether the interface offers Notes, and whether note tools are offered to models outside note chats | Def `backend/open_webui/config.py:2050`; read `backend/open_webui/utils/tools.py:717-721`; sent to signed-in browsers (`backend/open_webui/main.py:2359`). The server's note endpoints check the `features.notes` permission rather than this switch (`backend/open_webui/routers/notes.py:72`) |

### 7.20 `oauth` (53 Keys)

Area document: [`sso-oauth-oidc-and-scim.md`](sso-oauth-oidc-and-scim.md) (sections 5 and 7, which
describe every field in depth).

**These keys follow the environment unless `ENABLE_OAUTH_PERSISTENT_CONFIG` is on** (code default
off, `backend/open_webui/config.py:3232`). While it is off, no `oauth.*` row is read, seeded or
written: each server process holds the environment-derived value in memory, and any save or import
changes only the process that handled it until the next restart
(`backend/open_webui/models/config.py:132-147`, `:197-206`, `:254-257`). The **OAuth / OIDC**
section of **Authentication** is then read-only, shows
`These settings are read from environment variables and cannot be edited here while {ENV_VAR} is disabled.`
(with `{ENV_VAR}` filled in as `ENABLE_OAUTH_PERSISTENT_CONFIG`), and its **Save** skips the section (`src/lib/components/admin/Settings/Authentication.svelte:52`,
`:77-87`, `:550-564`; `src/lib/i18n/locales/en-US/translation.json:3220`). While it is on, the
section saves through `POST /api/v1/auths/admin/config/oauth` (map at
`backend/open_webui/routers/auths.py:1428-1463`, save `:1511-1514`), and the stored value wins as
for any other key.

Four kinds of key are mixed in this namespace:

- **Read at each use** (25 keys): sign-in, the sign-in page and sign-out read them every time,
  through `get_oauth_runtime_config` (`backend/open_webui/utils/oauth.py:131-205`) or directly.
- **Shown on the screen but not used for sign-in** (5 keys: `oauth.provider_name`,
  `oauth.client_id`, `oauth.client_secret`, `oauth.redirect_uri`, `oauth.scopes`): providers are
  registered once, at start-up, from the environment constants
  (`backend/open_webui/config.py:2636-2782`), so editing these keys changes nothing until the
  environment changes and the server restarts.
- **Inert rows in the API field map** (4 keys: `oauth.client.timeout`, `oauth.timeout`,
  `oauth.token_endpoint_auth_method`, `oauth.code_challenge_method`): no control, no reader; the
  environment constants are used instead.
- **Inert rows outside any field map** (19 keys, `oauth.google.*`, `oauth.microsoft.*`,
  `oauth.github.*`, `oauth.feishu.*`): read by no code; only the environment matters.

Labels below are under `settings.admin.authentication.*`; every field after the first switch
appears only while **OAuth / OIDC** is on (`src/lib/components/admin/Settings/Authentication.svelte:573`).

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `oauth.client.timeout` | `OAUTH_CLIENT_TIMEOUT` (seconds) | empty | none (API or import only); field `OAUTH_CLIENT_TIMEOUT` has no control | **Inert row**: the timeout for tool servers' OAuth clients is taken from the environment constant | Def `backend/open_webui/config.py:390`; the constant is used at `backend/open_webui/utils/oauth.py:842` |
| `oauth.enable` | `ENABLE_OAUTH` (`true` unless set otherwise) | on | **Authentication** › **OAuth / OIDC** switch (`src/lib/components/admin/Settings/Authentication.svelte:565-570`; `src/lib/i18n/locales/en-US/translation.json:2091`) | Master switch: off hides every single sign-on button and makes provider sign-in and its callback answer 404, without clearing provider settings | Def `backend/open_webui/config.py:2481`; read `backend/open_webui/main.py:2320-2324`, `backend/open_webui/utils/oauth.py:1850-1853`, `:1872-1875` |
| `oauth.enable_signup` | `ENABLE_OAUTH_SIGNUP` (`true` to enable) | off | **Authentication** › **OAuth Signup** (`src/lib/components/admin/Settings/Authentication.svelte:696-700`; `src/lib/i18n/locales/en-US/translation.json:2093`) | Whether a first single sign-on may create an account; otherwise unknown people are refused with `ACCESS_PROHIBITED` | Def `backend/open_webui/config.py:2483`; read `backend/open_webui/utils/oauth.py:2093-2099`, `:2148-2152` |
| `oauth.auto_redirect` | `OAUTH_AUTO_REDIRECT` (`true` to enable) | off | **Authentication** › **Auto Redirect** (`src/lib/components/admin/Settings/Authentication.svelte:717-721`; `src/lib/i18n/locales/en-US/translation.json:2047`) | The sign-in page sends people straight to the provider | Def `backend/open_webui/config.py:2485`; sent to every visitor (`backend/open_webui/main.py:2325`) |
| `oauth.refresh_token.include_scope` | `OAUTH_REFRESH_TOKEN_INCLUDE_SCOPE` (`true` to enable) | off | none (API or import only); round-tripped by the screen | Sends the scopes again when a provider token is refreshed | Def `backend/open_webui/config.py:2487`; read `backend/open_webui/utils/oauth.py:1158-1164`, `:1495-1501`. Renamed from `oauth.refresh_token_include_scope` (section 6.3) |
| `oauth.merge_accounts_by_email` | `OAUTH_MERGE_ACCOUNTS_BY_EMAIL` (`true` to enable) | off | **Authentication** › **Merge Accounts by Email** (`src/lib/components/admin/Settings/Authentication.svelte:704-711`; `src/lib/i18n/locales/en-US/translation.json:2087`) | Links a single sign-on to an existing account with the same email | Def `backend/open_webui/config.py:2490`; read `backend/open_webui/utils/oauth.py:2012-2019`, `backend/open_webui/routers/auths.py:1735-1740`. Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca) |
| `oauth.google.client_id` | `GOOGLE_CLIENT_ID` | empty | none (API or import only) | **Inert row** | Def `backend/open_webui/config.py:2494`; Google registration `:2655-2671` |
| `oauth.google.client_secret` | `GOOGLE_CLIENT_SECRET` | secret (set per environment) | none (API or import only) | **Inert row** | Def `backend/open_webui/config.py:2496` |
| `oauth.google.scope` | `GOOGLE_OAUTH_SCOPE` | `openid email profile` | none (API or import only) | **Inert row** | Def `backend/open_webui/config.py:2499` |
| `oauth.google.redirect_uri` | `GOOGLE_REDIRECT_URI` | empty | none (API or import only) | **Inert row** | Def `backend/open_webui/config.py:2501` |
| `oauth.microsoft.client_id` | `MICROSOFT_CLIENT_ID` | empty | none (API or import only) | **Inert row** | Def `backend/open_webui/config.py:2515`; Microsoft registration `:2673-2689` |
| `oauth.microsoft.client_secret` | `MICROSOFT_CLIENT_SECRET` | secret (set per environment) | none (API or import only) | **Inert row** | Def `backend/open_webui/config.py:2517` |
| `oauth.microsoft.tenant_id` | `MICROSOFT_CLIENT_TENANT_ID` | empty | none (API or import only) | **Inert row** | Def `backend/open_webui/config.py:2519` |
| `oauth.microsoft.login_base_url` | `MICROSOFT_CLIENT_LOGIN_BASE_URL` | `https://login.microsoftonline.com` | none (API or import only) | **Inert row** | Def `backend/open_webui/config.py:2521` |
| `oauth.microsoft.picture_url` | `MICROSOFT_CLIENT_PICTURE_URL` | the Microsoft Graph photo address | none (API or import only) | **Inert row** | Def `backend/open_webui/config.py:2523-2526` |
| `oauth.microsoft.scope` | `MICROSOFT_OAUTH_SCOPE` | `openid email profile` | none (API or import only) | **Inert row** | Def `backend/open_webui/config.py:2529` |
| `oauth.microsoft.redirect_uri` | `MICROSOFT_REDIRECT_URI` | empty | none (API or import only) | **Inert row** | Def `backend/open_webui/config.py:2531` |
| `oauth.github.client_id` | `GITHUB_CLIENT_ID` | empty | none (API or import only) | **Inert row** | Def `backend/open_webui/config.py:2533`; GitHub registration `:2691-2710` |
| `oauth.github.client_secret` | `GITHUB_CLIENT_SECRET` | secret (set per environment) | none (API or import only) | **Inert row** | Def `backend/open_webui/config.py:2535` |
| `oauth.github.scope` | `GITHUB_CLIENT_SCOPE` | `user:email` | none (API or import only) | **Inert row** | Def `backend/open_webui/config.py:2537` |
| `oauth.github.redirect_uri` | `GITHUB_CLIENT_REDIRECT_URI` | empty | none (API or import only) | **Inert row** | Def `backend/open_webui/config.py:2539` |
| `oauth.client_id` | `OAUTH_CLIENT_ID` | empty | **Authentication** › **Client ID** (`src/lib/components/admin/Settings/Authentication.svelte:600-606`; `src/lib/i18n/locales/en-US/translation.json:2055`) | Shown only; the OIDC registration uses the environment value | Def `backend/open_webui/config.py:2541`; registration `:2712-2735` |
| `oauth.client_secret` | `OAUTH_CLIENT_SECRET` | secret (set per environment) | **Authentication** › **Client Secret** (`src/lib/components/admin/Settings/Authentication.svelte:611-618`; `src/lib/i18n/locales/en-US/translation.json:2057`) | Shown only, as above | Def `backend/open_webui/config.py:2543` |
| `oauth.provider_url` | `OPENID_PROVIDER_URL` | empty | **Authentication** › **Provider URL** (`src/lib/components/admin/Settings/Authentication.svelte:587-593`; `src/lib/i18n/locales/en-US/translation.json:2105`) | Not used for sign-in (the environment value is); read at sign-out as the discovery address when a provider has none of its own | Def `backend/open_webui/config.py:2545`; read `backend/open_webui/routers/auths.py:1010-1013` |
| `oauth.end_session_endpoint` | `OPENID_END_SESSION_ENDPOINT` | empty | none (API or import only); round-tripped by the screen | A fixed provider sign-out address; when set, signing out of a single sign-on session redirects there | Def `backend/open_webui/config.py:2547`; read `backend/open_webui/routers/auths.py:997-1008` |
| `oauth.redirect_uri` | `OPENID_REDIRECT_URI` | empty | **Authentication** › **Redirect URI** (`src/lib/components/admin/Settings/Authentication.svelte:625-631`; `src/lib/i18n/locales/en-US/translation.json:2107`) | Shown only; the registration uses the environment value | Def `backend/open_webui/config.py:2549` |
| `oauth.scopes` | `OAUTH_SCOPES` | `openid email profile` | **Authentication** › **Scopes** (`src/lib/components/admin/Settings/Authentication.svelte:636-642`; `src/lib/i18n/locales/en-US/translation.json:2113`) | Shown only, as above | Def `backend/open_webui/config.py:2551` |
| `oauth.timeout` | `OAUTH_TIMEOUT` (seconds) | empty | none (API or import only) | **Inert row**: the registrations use the environment constant | Def `backend/open_webui/config.py:2553`; constant used at `:2640`, `:2750` |
| `oauth.token_endpoint_auth_method` | `OAUTH_TOKEN_ENDPOINT_AUTH_METHOD` | JSON `null` | none (API or import only) | **Inert row**: the OIDC registration uses the environment constant | Def `backend/open_webui/config.py:2555`; constant used at `:2722-2726` |
| `oauth.code_challenge_method` | `OAUTH_CODE_CHALLENGE_METHOD` (`S256` or unset) | JSON `null` | none (API or import only) | **Inert row**: the registrations use the environment constant | Def `backend/open_webui/config.py:2557`; constant used at `:2643-2648` |
| `oauth.provider_name` | `OAUTH_PROVIDER_NAME` | `SSO` | **Authentication** › **Provider Name** (`src/lib/components/admin/Settings/Authentication.svelte:576-582`; `src/lib/i18n/locales/en-US/translation.json:2103`) | Shown only; the button label is the environment value | Def `backend/open_webui/config.py:2559`; label source `:2732-2735`, `backend/open_webui/main.py:2321` |
| `oauth.sub_claim` | `OAUTH_SUB_CLAIM` | JSON `null` (each provider's usual claim: `sub`, `id` for GitHub, `user_id` for Feishu) | **Authentication** › **Sub Claim** (`src/lib/components/admin/Settings/Authentication.svelte:684-690`; `src/lib/i18n/locales/en-US/translation.json:2123`) | Claim used as the account's stable identifier with the provider | Def `backend/open_webui/config.py:2561`; read `backend/open_webui/utils/oauth.py:1945-1953`, `backend/open_webui/routers/auths.py:1702-1703`. Changing it affects existing account links (area document section 5.3) |
| `oauth.username_claim` | `OAUTH_USERNAME_CLAIM` | `name` | **Authentication** › **Username Claim** (`src/lib/components/admin/Settings/Authentication.svelte:660-666`; `src/lib/i18n/locales/en-US/translation.json:2134`) | Claim used as the display name | Def `backend/open_webui/config.py:2563`; read `backend/open_webui/utils/oauth.py:1927-1932`, `:2038-2039`, `:2110` |
| `oauth.picture_claim` | `OAUTH_PICTURE_CLAIM` | `picture` | **Authentication** › **Picture Claim** (`src/lib/components/admin/Settings/Authentication.svelte:673-679`; `src/lib/i18n/locales/en-US/translation.json:2099`) | Claim used as the profile picture | Def `backend/open_webui/config.py:2566`; read `backend/open_webui/utils/oauth.py:2065-2071`, `:2101-2107` |
| `oauth.email_claim` | `OAUTH_EMAIL_CLAIM` | `email` | **Authentication** › **Email Claim** (`src/lib/components/admin/Settings/Authentication.svelte:649-655`; `src/lib/i18n/locales/en-US/translation.json:2063`) | Claim used as the email address | Def `backend/open_webui/config.py:2568`; read `backend/open_webui/utils/oauth.py:1961-1965`, `backend/open_webui/routers/auths.py:1699` |
| `oauth.group_claim` | `OAUTH_GROUPS_CLAIM`, then `OAUTH_GROUP_CLAIM` | `groups` | **Authentication** › **Group Claim**, shown while **Group Mapping** is on (`src/lib/components/admin/Settings/Authentication.svelte:818-824`; `src/lib/i18n/locales/en-US/translation.json:2075`) | Claim listing the person's groups (a dotted path is allowed) | Def `backend/open_webui/config.py:2570`; read `backend/open_webui/utils/oauth.py:1650-1671`. Field name differs from the variable (section 4.1) |
| `oauth.feishu.client_id` | `FEISHU_CLIENT_ID` | empty | none (API or import only) | **Inert row** | Def `backend/open_webui/config.py:2572`; Feishu registration `:2737-2759` |
| `oauth.feishu.client_secret` | `FEISHU_CLIENT_SECRET` | secret (set per environment) | none (API or import only) | **Inert row** | Def `backend/open_webui/config.py:2574` |
| `oauth.feishu.scope` | `FEISHU_OAUTH_SCOPE` | `contact:user.base:readonly` | none (API or import only) | **Inert row** | Def `backend/open_webui/config.py:2576` |
| `oauth.feishu.redirect_uri` | `FEISHU_REDIRECT_URI` | empty | none (API or import only) | **Inert row** | Def `backend/open_webui/config.py:2578` |
| `oauth.enable_role_mapping` | `ENABLE_OAUTH_ROLE_MANAGEMENT` (`true` to enable) | off | **Authentication** › **Role Mapping** (`src/lib/components/admin/Settings/Authentication.svelte:739-744`; `src/lib/i18n/locales/en-US/translation.json:2109`) | Sets the role from the provider's roles claim at each sign-in, and refuses people whose roles match neither list | Def `backend/open_webui/config.py:2580`; read `backend/open_webui/utils/oauth.py:1546-1617` |
| `oauth.enable_group_mapping` | `ENABLE_OAUTH_GROUP_MANAGEMENT` (`true` to enable) | off | **Authentication** › **Group Mapping** (`src/lib/components/admin/Settings/Authentication.svelte:790-797`; `src/lib/i18n/locales/en-US/translation.json:2071`) | Replaces group memberships with the provider's groups at each sign-in | Def `backend/open_webui/config.py:2582`; read `backend/open_webui/utils/oauth.py:2158-2165`, `backend/open_webui/routers/auths.py:1762-1769`. Behaviour: `knowledgebase/tools/ground-truth.md` (Accounts and Access) |
| `oauth.enable_group_creation` | `ENABLE_OAUTH_GROUP_CREATION` (`true` to enable) | off | **Authentication** › **Auto-Create Groups**, shown while **Group Mapping** is on (`src/lib/components/admin/Settings/Authentication.svelte:804-811`; `src/lib/i18n/locales/en-US/translation.json:2069`) | Creates groups named by the provider that do not exist yet | Def `backend/open_webui/config.py:2584`; read `backend/open_webui/utils/oauth.py:1676-1697` |
| `oauth.group_default_share` | `OAUTH_GROUP_DEFAULT_SHARE` (read into a helper variable: `members`, `true`, anything else off) | on (`true`, which the group screen calls **Anyone**) | none (API or import only); round-tripped by the screen | The **Who can share to this group** setting given to groups that sign-in creates | Def `backend/open_webui/config.py:2587-2588`; read `backend/open_webui/utils/oauth.py:1694`. Value meanings: [`users-groups-roles-and-permissions.md`](users-groups-roles-and-permissions.md) |
| `oauth.blocked_groups` | `OAUTH_BLOCKED_GROUPS` | `[]` held as text | **Authentication** › **Blocked Groups**, shown while **Group Mapping** is on (`src/lib/components/admin/Settings/Authentication.svelte:829-835`; `src/lib/i18n/locales/en-US/translation.json:2049`) | Groups that group mapping never removes the person from; despite the description it blocks nobody | Def `backend/open_webui/config.py:2591`; read `backend/open_webui/utils/oauth.py:1652`; saved as a JSON list in text (`backend/open_webui/routers/auths.py:1466-1469`) |
| `oauth.roles_claim` | `OAUTH_ROLES_CLAIM` | `roles` | **Authentication** › **Roles Claim**, shown while **Role Mapping** is on (`src/lib/components/admin/Settings/Authentication.svelte:752-758`; `src/lib/i18n/locales/en-US/translation.json:2111`) | Claim listing the person's provider roles | Def `backend/open_webui/config.py:2595`; read `backend/open_webui/utils/oauth.py:1548-1574` |
| `oauth.allowed_roles` | `OAUTH_ALLOWED_ROLES` (split on `OAUTH_ROLES_SEPARATOR`, code default `,`) | `user`, `admin` | **Authentication** › **Allowed Roles** (`src/lib/components/admin/Settings/Authentication.svelte:775-781`; `src/lib/i18n/locales/en-US/translation.json:2033`) | Provider roles that may sign in (as `user`); `*` allows any | Def `backend/open_webui/config.py:2597-2603`; read `backend/open_webui/utils/oauth.py:1586-1593`; an emptied field is saved as an empty list (`backend/open_webui/routers/auths.py:1475-1477`) |
| `oauth.admin_roles` | `OAUTH_ADMIN_ROLES` (split as above) | `admin` | **Authentication** › **Admin Roles** (`src/lib/components/admin/Settings/Authentication.svelte:763-769`; `src/lib/i18n/locales/en-US/translation.json:2027`) | Provider roles that make the account an admin | Def `backend/open_webui/config.py:2605-2607`; read `backend/open_webui/utils/oauth.py:1594-1599` |
| `oauth.allowed_domains` | `OAUTH_ALLOWED_DOMAINS` (comma list) | `*` (every domain) | **Authentication** › **Allowed Domains** (`src/lib/components/admin/Settings/Authentication.svelte:725-731`; `src/lib/i18n/locales/en-US/translation.json:2029`) | Email domains allowed to sign in by single sign-on; others see the password message | Def `backend/open_webui/config.py:2609`; read `backend/open_webui/utils/oauth.py:2002-2008`, `backend/open_webui/routers/auths.py:1721-1730` |
| `oauth.update_picture_on_login` | `OAUTH_UPDATE_PICTURE_ON_LOGIN` (`true` to enable) | off | **Authentication** › **Update Picture** (`src/lib/components/admin/Settings/Authentication.svelte:864-869`; `src/lib/i18n/locales/en-US/translation.json:2132`) | Refreshes the profile picture from the provider at each sign-in | Def `backend/open_webui/config.py:2611`; read `backend/open_webui/utils/oauth.py:2064-2072` |
| `oauth.update_name_on_login` | `OAUTH_UPDATE_NAME_ON_LOGIN` (`true` to enable) | off | **Authentication** › **Update Name** (`src/lib/components/admin/Settings/Authentication.svelte:853-858`; `src/lib/i18n/locales/en-US/translation.json:2130`) | Refreshes the account name at each sign-in | Def `backend/open_webui/config.py:2613`; read `backend/open_webui/utils/oauth.py:2038-2047` |
| `oauth.update_email_on_login` | `OAUTH_UPDATE_EMAIL_ON_LOGIN` (`true` to enable) | off | **Authentication** › **Update Email** (`src/lib/components/admin/Settings/Authentication.svelte:842-847`; `src/lib/i18n/locales/en-US/translation.json:2128`) | Refreshes the account email at each sign-in, unless another account already uses it | Def `backend/open_webui/config.py:2615`; read `backend/open_webui/utils/oauth.py:2049-2062` |
| `oauth.audience` | `OAUTH_AUDIENCE` | empty | none (API or import only); round-tripped by the screen | Adds an `audience` parameter to the sign-in request | Def `backend/open_webui/config.py:2621`; read `backend/open_webui/utils/oauth.py:1864-1866` |

An export taken while OAuth persistence is off contains the environment's OAuth values, secrets
included (section 5.6).

### 7.21 `ollama` (3 Keys)

Area document: [`model-connections-openai-ollama-and-direct.md`](model-connections-openai-ollama-and-direct.md).
The screen is **Connections** (`src/lib/components/admin/Settings/Connections.svelte`), labels under
`settings.admin.connections.*` (`src/lib/i18n/locales/en-US/translation.json:2168-2182`). The
**Ollama API** switch **saves on change**, and adding, editing or deleting a connection saves at
once (`src/lib/components/admin/Settings/Connections.svelte:93-111`, `:146-154`, `:302-351`). The
endpoint `POST /ollama/config/update` stores all three keys together, drops connection settings
whose position no longer exists, clears the model caches and publishes
`model.provider_config.updated` (`backend/open_webui/routers/ollama.py:306-347`). Connections are
identified by their **position** in the list (`"0"`, `"1"`, …), so deleting one renumbers the
others (`src/lib/components/admin/Settings/Connections.svelte:341-349`).

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `ollama.enable` | `ENABLE_OLLAMA_API` (`true` unless set otherwise) | on | **Connections** › **Ollama API** (`src/lib/components/admin/Settings/Connections.svelte:302-309`; `src/lib/i18n/locales/en-US/translation.json:2178`) | Whether Ollama models are listed and Ollama requests are served; while off the model list is empty and the other Ollama endpoints answer HTTP 503 `The Ollama API is disabled. Please enable it to use this feature.` | Def `backend/open_webui/config.py:237`; read `backend/open_webui/utils/models.py:59-61` and at the top of each Ollama endpoint (for example `backend/open_webui/routers/ollama.py:394-397`, `:492-493`); text `backend/open_webui/constants.py:103` |
| `ollama.base_urls` | `OLLAMA_BASE_URLS` (separated by `;`); otherwise one address from `OLLAMA_BASE_URL` or `OLLAMA_API_BASE_URL` | `http://localhost:11434`, with rewrites for the Docker image and Kubernetes and, when no address was given, a start-up check that moves to port `12434` if only that port answers | **Connections** › **Manage Ollama API Connections** list and **Add Connection** (`src/lib/components/admin/Settings/Connections.svelte:312-352`; `src/lib/i18n/locales/en-US/translation.json:2176`) | The Ollama servers MedIT GPT talks to | Def `backend/open_webui/config.py:239-300` (the Docker image sets `OLLAMA_BASE_URL` to `/ollama`, `Dockerfile:86`); read through `backend/open_webui/routers/ollama.py:226-238` and in `backend/open_webui/main.py:977-989` |
| `ollama.api_configs` | `OLLAMA_API_CONFIGS` (a JSON object, read into a helper variable; anything else is ignored with a log warning) | `{}` | Each connection's settings dialog in that list (`src/lib/components/admin/Settings/Connections.svelte:333-340`) | Per-connection settings keyed by position: on or off, tags, model prefix, model list, connection type, authentication and headers, and the connection's key | Def `backend/open_webui/config.py:302-312`; read `backend/open_webui/routers/ollama.py:235-238`; the key is stored inside the object (`src/lib/components/admin/Settings/Connections.svelte:146-151`), so treat the value as **secret (set per environment)**. Repaired at start-up if an old version flattened it (section 5.2) |

### 7.22 `onedrive` (3 Keys)

Area document: [`files-uploads-and-storage.md`](files-uploads-and-storage.md). Only the switch has a
field, on **Documents** › **Integration** (saved as in 7.11). The browser's OneDrive picker receives
the client IDs, the SharePoint address and the tenant from the **environment** constants, not from
these keys, and the personal and business choices only while the switch is on
(`backend/open_webui/main.py:2379-2386`, `:2426-2431`; `backend/open_webui/config.py:849-865`).

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `onedrive.enable` | `ENABLE_ONEDRIVE_INTEGRATION` (`true` to enable) | off | **Documents** › **Integration** › **OneDrive** (`src/lib/components/admin/Settings/Documents.svelte:1539-1543`; `src/lib/i18n/locales/en-US/translation.json:2296`) | Offers OneDrive as a source for attachments | Def `backend/open_webui/config.py:849`; saved at `backend/open_webui/routers/retrieval.py:1307-1311`; read only to tell browsers (`backend/open_webui/main.py:2377`, `:2384`). Which OneDrive types appear also depends on the environment-only `ENABLE_ONEDRIVE_PERSONAL` and `ENABLE_ONEDRIVE_BUSINESS` and their client IDs (`backend/open_webui/config.py:852-861`) |
| `onedrive.sharepoint_url` | `ONEDRIVE_SHAREPOINT_URL` | empty | none (API or import only) | **Inert row**: no code reads the key | Def `backend/open_webui/config.py:863`. Change the environment variable and restart instead |
| `onedrive.sharepoint_tenant_id` | `ONEDRIVE_SHAREPOINT_TENANT_ID` | empty | none (API or import only) | **Inert row**: no code reads the key | Def `backend/open_webui/config.py:865`. As above |

### 7.23 `openai` (4 Keys)

Area document: [`model-connections-openai-ollama-and-direct.md`](model-connections-openai-ollama-and-direct.md).
Same screen as 7.21. The **OpenAI API** switch **saves on change**, and adding, editing or deleting
a connection saves at once (`src/lib/components/admin/Settings/Connections.svelte:56-91`,
`:138-144`, `:243-296`). The endpoint `POST /openai/config/update` stores all four keys together,
pads or trims the key list to the number of addresses, drops connection settings whose position no
longer exists, clears the model caches and publishes `model.provider_config.updated`
(`backend/open_webui/routers/openai.py:556-597`). Connections are identified by position, as for
Ollama.

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `openai.enable` | `ENABLE_OPENAI_API` (`true` unless set otherwise) | on | **Connections** › **OpenAI API** (`src/lib/components/admin/Settings/Connections.svelte:243-250`; `src/lib/i18n/locales/en-US/translation.json:2179`) | Whether models from OpenAI-compatible connections are listed and answered; while off their endpoints answer HTTP 503 `OpenAI API is disabled` | Def `backend/open_webui/config.py:319`; read `backend/open_webui/utils/models.py:59-60`, `backend/open_webui/routers/openai.py:870-871`, `:1486-1493` |
| `openai.api_base_urls` | `OPENAI_API_BASE_URLS` (separated by `;`); otherwise `OPENAI_API_BASE_URL` | `https://api.openai.com/v1` (an empty entry also becomes that address) | **Connections** › **Manage OpenAI API Connections** list and **Add Connection** (`src/lib/components/admin/Settings/Connections.svelte:253-298`; `src/lib/i18n/locales/en-US/translation.json:2177`) | The OpenAI-compatible services MedIT GPT talks to | Def `backend/open_webui/config.py:323-347`; trailing slashes removed by the screen (`src/lib/components/admin/Settings/Connections.svelte:59`); read `backend/open_webui/routers/openai.py:318-343`, `backend/open_webui/routers/pipelines.py:57-60`, `backend/open_webui/main.py:1022-1032` |
| `openai.api_keys` | `OPENAI_API_KEYS` (separated by `;`); otherwise `OPENAI_API_KEY` | secret (set per environment) | The key field of each connection in that list (`src/lib/components/admin/Settings/Connections.svelte:274-278`) | One key per address, matched by position | Def `backend/open_webui/config.py:335-339`; kept the same length as the address list (`backend/open_webui/routers/openai.py:328-335`, `:558-563`) |
| `openai.api_configs` | `OPENAI_API_CONFIGS` (a JSON object, read into a helper variable; anything else is ignored with a log warning) | `{}` | Each connection's settings dialog (`src/lib/components/admin/Settings/Connections.svelte:275-282`; fields in `src/lib/components/AddConnectionModal.svelte:213-225`) | Per-connection settings keyed by position: on or off, tags, model prefix, model list, connection type, authentication type, headers and API version | Def `backend/open_webui/config.py:349-359`; read `backend/open_webui/routers/openai.py:338-343`. Custom headers can carry credentials, so treat the value as **secret (set per environment)**. Repaired at start-up if an old version flattened it (section 5.2); the screen also reads older entries keyed by address (`src/lib/components/admin/Settings/Connections.svelte:183-190`) |

That completes the 199 keys in scope: 30 + 6 + 4 + 1 + 2 + 7 + 7 + 8 + 2 + 2 + 2 + 2 + 3 + 20 + 13 +
17 + 6 + 3 + 1 + 53 + 3 + 3 + 4 (section 1).

## 8. Cron Jobs and Background Processes

There is no crontab and no job that reloads, checks or rewrites these settings on a schedule.
Ordinary reads go to the database each time a value is needed (section 5.3), so most saves apply
at the next request. What matters for support is the state that is **built once and kept in a
server process**, and the few loops that consult keys in scope. The start-up steps that touch
stored settings are in section 5.2.

### 8.1 State Built at Start-Up or on Save

| State kept in a server process | Built from | When it is built | What rebuilds it | Evidence |
|---|---|---|---|---|
| The environment-derived default of every key (`Config.DEFAULTS`) | `DEFAULT_CONFIG` | When `open_webui.config` is imported, in each process | A restart only. For process-only keys a save overwrites the value in the saving process alone | `backend/open_webui/config.py:3234-3238`; `backend/open_webui/models/config.py:116-126`, `:197-206` |
| Single sign-on provider clients | The environment constants, not the `oauth.*` keys | At start-up | A restart only | `backend/open_webui/config.py:2653-2782`; `backend/open_webui/main.py:524-525`; `backend/open_webui/utils/oauth.py:1330-1343` |
| The local Whisper model (`audio.stt.whisper_model`) | The stored key | Not at start-up; on the first local transcription in each process | An **Audio** save with `Whisper (Local)` selected, in the process that handled the save; other processes keep their model until restart | `backend/open_webui/main.py:776`; `backend/open_webui/routers/audio.py:305-310`, `:671-676` |
| The local speech pipeline (`Transformers (Local)`) | Fixed model names in code | On first use in each process | A restart only; the speaker name in `audio.tts.model` is read per request | `backend/open_webui/routers/audio.py:326-338`, `:526-532` |
| The base model list (`models.base_models_cache` on) | The OpenAI and Ollama connections | At start-up, and again whenever the list is requested with a refresh | OpenAI or Ollama connection saves clear it in the saving process and in Redis; without Redis each process keeps its own copy | `backend/open_webui/main.py:407-420`; `backend/open_webui/utils/models.py:76-106`; `backend/open_webui/routers/openai.py:346-357`; `backend/open_webui/routers/ollama.py:324-334` |
| Arena models in the old access-control format | `evaluation.arena.models` | At start-up | Converted and written back once (section 7.10) | `backend/open_webui/main.py:660-664` |
| The browser's copy of `/api/config` | The keys sent to browsers (section 2.2) | When a page loads | The saving admin's page reloads it after most saves; everyone else's open pages keep the old switches until they reload | `src/routes/+layout.svelte:1238-1290`; for example `src/lib/components/admin/Settings/Audio.svelte:182-185` |

### 8.2 Loops and Background Tasks That Read Keys in Scope

| Loop or task | Keys read | Behaviour | Evidence |
|---|---|---|---|
| `scheduler_worker_loop`, every `SCHEDULER_POLL_INTERVAL` seconds (environment, code default 10) plus up to 2 seconds of jitter | `automations.enable`, `calendar.enable` | Claims due automations and sends calendar reminders only while the switch is on; a change applies at the next pass | `backend/open_webui/main.py:403-405`; `backend/open_webui/utils/automations.py:53`, `:98-121` |
| Each automation run | `automations.auth_token_expires_in`, `image_generation.enable`, `channels.enable`, `channels.model_response_mode` | Read when the run starts | `backend/open_webui/utils/automations.py:186-189`, `:259-261`, `:280-284`, `:384-391` |
| Memory review after an answer (per chat, not scheduled) | `memories.enable`, `memories.background_review.enable`, `memories.review_interval_turns` | Read each time an answer completes | `backend/open_webui/utils/middleware.py:4039`; `backend/open_webui/utils/memory.py:431-447` |

Area documents describe the loops themselves:
[`automations-calendar-and-timers.md`](automations-calendar-and-timers.md) section 8 and
[`memories.md`](memories.md).

## 9. Notifications and Emails

The application sends no email (`knowledgebase/tools/ground-truth.md`, Contacts). A settings change
produces no in-app notice for other people and no socket message to their browsers: the event sinks
notify users only for chat, channel, calendar and file-processing events, and act on sessions only
for user deletion and role changes (`backend/open_webui/events.py:669-675`, `:1083-1100`,
`:1171`). What a save can produce is an **event**, delivered to Event functions and to admin event
webhooks whose filters match (`backend/open_webui/events.py:1034-1060`, `:1103-1171`, `:1174-1202`).
Webhook set-up and filters are in
[`notifications-webhooks-events-and-banners.md`](notifications-webhooks-events-and-banners.md)
sections 5.1, 5.2 and 5.15.

### 9.1 Which Saves Publish Which Event

| Save | Event | `subject` | `data` | Evidence |
|---|---|---|---|---|
| **Audio** | `config.updated` | `audio` | `tts_engine`, `stt_engine` | `backend/open_webui/routers/audio.py:312-322` |
| **Images** | `config.updated` | `images` | `image_generation_enabled`, `image_edit_enabled`, `image_generation_engine`, `image_edit_engine` | `backend/open_webui/routers/images.py:306-318` |
| **Evaluations** | `config.updated` | `evaluation` | `keys` (the keys saved), `arena_enabled`, `arena_model_count` | `backend/open_webui/routers/evaluations.py:312-323` |
| **Code Execution** | `config.code_execution.updated` | `code_execution` | the two switches and the two engines | `backend/open_webui/routers/configs.py:715-727` |
| **Connections** › **Direct Connections**, **Cache Base Model List**; **Integrations** › **Direct Integrations** | `config.connections.updated` | `connections` | the three values | `backend/open_webui/routers/configs.py:152-159` |
| **Models** (including **Model Defaults**) | `config.models.updated` | `models` | default and pinned models, number of ordered models (not the metadata or parameters) | `backend/open_webui/routers/configs.py:758-769` |
| **Connections** › OpenAI or Ollama | `model.provider_config.updated` | `openai` or `ollama` | `provider`, `enabled`, `base_url_count` | `backend/open_webui/routers/openai.py:579-590`; `backend/open_webui/routers/ollama.py:336-347` |
| **Database** › **Import** | `config.imported` | `import` | `keys` (the names imported) | `backend/open_webui/routers/configs.py:100-109` |
| **General**, **Authentication** (including LDAP and OAuth), **Interface** (chat keys), **Documents** | none | | | `backend/open_webui/routers/auths.py:1269-1296`, `:1323-1361`, `:1511-1514`; `backend/open_webui/routers/chats.py:841-857`; `backend/open_webui/routers/retrieval.py:962-1398` |

`config.updated` also comes from the sub-agent settings, outside this scope
(`backend/open_webui/routers/configs.py:798`). The event names and default messages are defined at
`backend/open_webui/events.py:57-98`, `:456-460`.

### 9.2 What an Event Contains

Each event carries the acting admin as `actor` with their id, name, email, role and account
timestamps (`backend/open_webui/events.py:704`, `:974-985`), so webhook deliveries and Event functions receive personal
data and must be handled with care. Values whose names look like secrets (for example ending in
`_key`, `_secret` or `_token`) are removed from `subject` and `data` before delivery
(`backend/open_webui/events.py:689-702`, `:947-955`, `:1028-1029`). Who changed a setting is
otherwise recorded only in the optional audit log (section 6.1). Because General, Authentication,
Interface and Documents saves publish nothing, an event history shows changes to the `auth`,
`ldap`, `oauth`, `folders`, `channels`, `calendar`, `automations`, `memories`, `notes`, `chat`,
`file`, `google_drive` and `onedrive` keys only when they arrive through an import, whose
`config.imported` event lists the key names but not the values.

## 10. Error, Warning and Notice Messages (Verbatim)

Scope here is what an admin sees when **saving** keys in this document. Messages caused by a
setting at the time of use (for example `Channels is disabled` or
`The Ollama API is disabled. Please enable it to use this feature.`) are quoted in that key's row
in section 7 and catalogued with triggers in each area document's section 10 and in
[`error-messages-frontend-admin-workspace-and-settings.md`](error-messages-frontend-admin-workspace-and-settings.md)
and [`admin-settings-panels.md`](admin-settings-panels.md). Toasts appear in the corner of the
Settings window; the HTTP 400 texts reach the admin through the screen's error toast.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Settings saved successfully!` | Success toast | `src/lib/components/chat/SettingsModal.svelte:461`, `:860`, `:882`, `:888`, `:894`; `src/lib/components/admin/Settings/Authentication.svelte:104`; `src/lib/components/admin/Settings/Evaluations.svelte:32` | A save on General, Connections, Interface, Audio, Images, Documents, Code Execution, Authentication or Evaluations finished | None | Process-only keys (section 7.20) can show this and still be lost at restart |
| `Connections settings updated` | Success toast | `src/lib/components/admin/Settings/Connections.svelte:119`; `src/lib/components/admin/Settings/Integrations.svelte:67` | **Direct Connections**, **Cache Base Model List** or **Direct Integrations** switched | None | |
| `OpenAI API settings updated` | Success toast | `src/lib/components/admin/Settings/Connections.svelte:87` | OpenAI switch or connection list saved | None | |
| `Ollama API settings updated` | Success toast | `src/lib/components/admin/Settings/Connections.svelte:107` | Ollama switch or connection list saved | None | |
| `Models configuration saved successfully` | Success toast | `src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:143` | **Model Defaults** saved | None | |
| `Failed to save models configuration` | Error toast | `src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:147` | The **Model Defaults** save returned nothing | Try again; escalate if it repeats | Server log at the time |
| `Model order saved successfully` | Success toast | `src/lib/components/admin/Settings/Models.svelte:350` | Model order saved (same endpoint as the model defaults) | None | |
| `Failed to update settings` | Error toast | `src/lib/components/admin/Settings/General.svelte:90` | The **General** save returned nothing | Try again; escalate if it repeats | Server log at the time |
| `Invalid JSON format for Parameters` | Error toast; nothing saved | `src/lib/components/admin/Settings/Audio.svelte:137-144` | **Additional Parameters** (OpenAI text-to-speech) is not valid JSON | Correct the JSON | |
| `Local Whisper is unavailable in slim. Select an external speech-to-text engine.` | HTTP 400; nothing saved | `backend/open_webui/routers/audio.py:292-295` | Slim image, switching speech-to-text to `Whisper (Local)` | Choose another engine | Which image production runs is TO BE CONFIRMED |
| `Local TTS is unavailable in slim. Select an external text-to-speech engine.` | HTTP 400; nothing saved | `backend/open_webui/routers/audio.py:296-297` | Slim image, switching text-to-speech to `Transformers (Local)` | Choose another engine | As above |
| `AUTOMATIC1111 Base URL is required.` | Error toast; nothing saved, the **Image Generation** switch flips off on the screen | `src/lib/components/admin/Settings/Images.svelte:111-118` | Engine `Automatic1111` with an empty **Base URL** | Fill in the address, switch generation on again, save | |
| `ComfyUI Base URL is required.` | As above | `src/lib/components/admin/Settings/Images.svelte:119-123` | Engine `ComfyUI` with an empty **Base URL** | As above | |
| `OpenAI API Key is required.` | As above | `src/lib/components/admin/Settings/Images.svelte:124-128` | Engine `Default (Open AI)` with an empty **API Key** | As above | |
| `Gemini API Key is required.` | As above | `src/lib/components/admin/Settings/Images.svelte:129-133` | Engine `Gemini` with an empty **API Key** | As above | |
| `Invalid JSON format for ComfyUI Workflow.` | Error toast; nothing saved | `src/lib/components/admin/Settings/Images.svelte:179-184` | The generation workflow is not a JSON object | Re-export the workflow in API format | |
| `Invalid JSON format for ComfyUI Edit Workflow.` | Error toast; nothing saved | `src/lib/components/admin/Settings/Images.svelte:196-201` | The edit workflow is not a JSON object | As above | |
| `Invalid format. Please use the correct format  (auto is only allowed with models matching {IMAGE_AUTO_SIZE_MODELS_REGEX_PATTERN}).` | HTTP 400; nothing saved | `backend/open_webui/routers/images.py:278-286`; `backend/open_webui/constants.py:86` | **Image Size** `auto` with a model the pattern does not match (code default `^gpt-image`) | Enter a size such as `1024x1024` | |
| `Invalid format. Please use the correct format  (e.g., 512x512).` | HTTP 400; nothing saved | `backend/open_webui/routers/images.py:288-293` | **Image Size** not empty, not `auto` and not `WIDTHxHEIGHT` | Correct the size | |
| `Invalid format. Please use the correct format  (e.g., 50).` | HTTP 400; nothing saved | `backend/open_webui/routers/images.py:295-299` | **Steps** below zero | Correct the number | |
| `Required field {name} is empty` | HTTP 400; LDAP server fields not saved | `backend/open_webui/routers/auths.py:1325-1340`; `backend/open_webui/constants.py:131` | Saving with LDAP on and an empty `label`, `host`, `attribute_for_mail`, `attribute_for_username` or `search_base` (or `attribute_for_groups` with group mapping on) | Fill in the field | The other Authentication keys may already have been saved: the screen saves the general settings first (`src/lib/components/admin/Settings/Authentication.svelte:98-107`) |
| `This model is not publicly available. Please select another model.` | Warning toast; the choice is kept | `src/lib/components/admin/Settings/Interface.svelte:103-110` | A **Context Compaction Model** that not every user may read | Choose a public model, or accept | |
| `No expiration can pose security risks.` | Notice under the field | `src/lib/components/admin/Settings/Authentication.svelte:243-250` | **JWT Expiration** is `-1` | Use a duration | Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca) |
| `These settings are read from environment variables and cannot be edited here while {ENV_VAR} is disabled.` | Notice; section read-only | `src/lib/components/admin/Settings/Authentication.svelte:550-558` | OAuth persistence is off (`{ENV_VAR}` is `ENABLE_OAUTH_PERSISTENT_CONFIG`) | None on screen | Section 11.3 |
| `Warning: Jupyter execution enables arbitrary code execution, posing severe security risks—proceed with extreme caution.` | Notice replacing the field description | `src/lib/components/admin/Settings/CodeExecution.svelte:67-71`, `:181-185`; `src/lib/i18n/locales/en-US/translation.json:3446` | An engine set to `jupyter` | None | Security-sensitive: refer as above |
| `Message rating should be enabled to use this feature` | Description and tooltip | `src/lib/components/admin/Settings/Evaluations.svelte:101-111`; `src/lib/i18n/locales/en-US/translation.json:2365` | Always shown beside **Arena Models** | Check `ui.enable_message_rating` (second half of the catalogue) | |

Saves that are refused **without any message**: a **JWT Expiration** that does not match the
duration pattern, a **Default User Role** other than `pending`, `user` or `admin`, and a
**Model Response Mode** other than `thread` or `channel` are dropped from the save while everything
else is stored (`backend/open_webui/routers/auths.py:1283-1293`). *Inferred from code, not
tested:* on **Code Execution**, a request that fails without an error body (for example a network
failure) still ends in `Settings saved successfully!`, because the screen does not check the result
(`src/lib/components/admin/Settings/CodeExecution.svelte:26-28`, `:41-44`;
`src/lib/apis/configs/index.ts:619-633`).

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it never changes a setting, never asks for a settings export and never
handles a secret value. Resolutions below are explanations or escalations.

### 11.1 "I changed the environment variable but nothing changed"

**Symptom.** The platform maintainer set or changed a variable (for example `ENABLE_CHANNELS=true`)
and restarted, but the screen and the behaviour still show the old value.

**Likely causes, in order.**

1. The key already has a stored row. After the first start the stored value wins and the variable
   is only a seed (section 5.1; `backend/open_webui/models/config.py:140-147`, `:240-266`).
2. The variable is not the one the key reads, or a preferred name is also set (section 4.1; for
   example `OAUTH_GROUPS_CLAIM` beats `OAUTH_GROUP_CLAIM`, `LDAP_SEARCH_FILTER` beats
   `LDAP_SEARCH_FILTERS`). The "Seeded from" column in section 7 lists the order.
3. Not every server process was restarted; each computes its defaults when it starts
   (`backend/open_webui/config.py:3234-3238`). How many processes production runs is
   **TO BE CONFIRMED**.
4. For an `oauth.*` key with `ENABLE_OAUTH_PERSISTENT_CONFIG` on, a stored row wins (section 5.7).
5. The setting is environment-only and the key is an inert row (section 7 marks each one); then a
   restart is all that is needed, so cause 3 applies.

**Diagnostic steps.**

1. Find the key in section 7 and note its screen. Ask an admin to open that screen and read the
   value (section 5.4). Never request an export.
2. If the screen value differs from what the maintainer set, cause 1 or 2 applies.
3. If the key is marked "none (API or import only)", the stored value cannot be seen on a screen;
   escalate.

**Resolution.** Explain that the value is now stored and that the screen is the place to change
it. An admin may change it on the screen; tier 1 does not.

**Escalation.** To the platform maintainer: the key, the variable that was set (name only), the
value the admin sees on the screen, and the time of the restart. Never include a secret value.

### 11.2 "My admin change disappeared after a restart"

**Symptom.** An admin saved a setting, it worked, and after a restart or redeployment the old value
is back.

**Likely causes, in order.**

1. The key is `oauth.*` and OAuth persistence is off, so the change lived only in one process's
   memory (section 7.20; `backend/open_webui/models/config.py:132-138`, `:197-206`).
2. `ENABLE_PERSISTENT_CONFIG=False`: every key behaves that way (section 5.5).
3. `RESET_CONFIG_ON_START=True`: every stored setting is deleted at each start and re-seeded from
   the environment (`backend/open_webui/main.py:363-364`).
4. Another save overwrote it: **General** and **Authentication** each send back the other's keys
   as they were when the screen was opened (section 7.2), and an import writes whatever the file
   holds (section 5.6).
5. The database itself was replaced, for example a new container without the data volume
   (`CLAUDE.md`, Deployment). Production storage is **TO BE CONFIRMED**.

**Diagnostic steps.**

1. Ask which screen and field, and when it was saved and when the restart happened.
2. Check the key's namespace in section 7: `oauth.*` points to cause 1.
3. Ask whether anyone else had **General** or **Authentication** open, or imported settings, at
   the time.
4. For Audio, Images, Evaluations, Code Execution, Connections and Models, an admin event webhook
   (if production has one, **TO BE CONFIRMED**) would show the save (section 9.1); General and
   Authentication saves leave no event.

**Resolution.** The admin re-applies the change once the cause is known; tier 1 does not.

**Escalation.** To the platform maintainer: the key, the screen, the save time, the restart time,
and whether the three switches in causes 1 to 3 are set (they decide, and only the maintainer can
see them).

### 11.3 "OAuth settings won't stick"

**Symptom.** The **OAuth / OIDC** section of **Authentication** is greyed out, or an OAuth change
saves but single sign-on behaves as before, or the change is gone after a restart.

**Likely causes, in order.**

1. `ENABLE_OAUTH_PERSISTENT_CONFIG` is off (the code default). The section is read-only and shows
   `These settings are read from environment variables and cannot be edited here while {ENV_VAR} is disabled.`
   Any change made another way lasts only in one process until restart (section 7.20).
2. Persistence is on, but the field is one sign-in does not read: **Provider Name**, **Client ID**,
   **Client Secret**, **Redirect URI**, **Scopes**, and **Provider URL** for sign-in all come from
   the environment registration made at start-up (section 7.20).
3. Persistence was switched on and an old `oauth.*` row (for example one copied by migration
   `3ff2c63645b8` when the configuration was split into rows) now wins over the environment
   (section 5.7).
4. The field is one of the Google, Microsoft, GitHub or Feishu keys, which nothing reads; only the
   environment counts (section 7.20).

**Diagnostic steps.**

1. Ask the admin whether the yellow notice is shown at the top of **OAuth / OIDC**: yes means
   cause 1.
2. Note the field label and find its key in section 7.20: its Effect cell says whether sign-in
   reads it.
3. Ask whether the problem began after a restart or after persistence was switched on.

**Resolution.** Explain which kind of setting it is. Changing provider registration or the
persistence switch is a maintainer task and security-relevant: Security-sensitive, refer to the
platform maintainer and U of T Information Security (security.utoronto.ca).

**Escalation.** To the platform maintainer: the field label and key, whether the notice is shown,
what should change, and the time it was noticed. Never include the client secret or any token.
Single sign-on symptoms beyond settings are in
[`sso-oauth-oidc-and-scim.md`](sso-oauth-oidc-and-scim.md) section 11.

## 12. Local Customisations

**This area matches upstream v0.11.4.** `git diff main...uoft` changes, among the files this
document cites, only `backend/open_webui/env.py` (the default `WEBUI_NAME`, an environment-only
setting), `backend/open_webui/utils/notifications.py` (the test-notification text),
`src/lib/constants.ts` (`APP_NAME`), `src/lib/components/common/InterfaceSettings.svelte` and four
strings in `src/lib/i18n/locales/en-US/translation.json` (the personal **Hide Processing Details**
and **Inline Citations** settings). The uncommitted working-tree change in that translation file
rewords one of those descriptions. None of these touches `DEFAULT_CONFIG`, the `Config` class, the
admin screens or the endpoints in section 2.2, so the 199 keys, their seeds, defaults and screens
are upstream's.

| Fork change | Relation to this catalogue | Evidence |
|---|---|---|
| The two personal Interface settings | They are per-user `InterfaceSettings` fields, not keys here. An admin could preset them for everyone through `ui.default_interface_settings`, which the browser merges under each person's own choices (second half of the catalogue) | `backend/open_webui/models/users.py:99-100`; `src/lib/components/chat/SettingsModal.svelte:447-449` |
| Four added `en-US` strings | Translation lines after 2920 sit four lines later than upstream, so citations such as `src/lib/i18n/locales/en-US/translation.json:3220` and `:3446` differ from an upstream checkout; the admin labels cited in section 7 (lines 1977 to 2608) are unaffected | `git diff main...uoft -- src/lib/i18n/locales/en-US/translation.json` |
| Default `WEBUI_NAME` `MedIT GPT` | Environment-only, not stored; it names the sender of event webhooks (section 9) | `backend/open_webui/env.py:951`; `backend/open_webui/events.py:1038` |

## 13. Source File Index

| File | What it provides here |
|---|---|
| `backend/open_webui/config.py` | Every seeding variable (`:229-2821`), `DEFAULT_CONFIG` (`:2822-3228`), the persistence switches and `Config.configure` (`:3231-3238`), single sign-on registration (`:2636-2782`) |
| `backend/open_webui/models/config.py` | The `config` table and the `Config` class: reads, saves, process-only values, seeding, repairs (`:101-382`) |
| `backend/open_webui/main.py` | Start-up (`:345-472`), state built at start-up (`:524-529`, `:660-664`, `:776-778`), `/api/config` (`:2224-2472`), model defaults and tool approval in chats (`:1166-1177`, `:1255-1264`) |
| `backend/open_webui/routers/audio.py` | Audio field map, save, Whisper rebuild and every audio read |
| `backend/open_webui/routers/auths.py` | General and Authentication field maps and saves, LDAP sign-in, OAuth field map and save, sign-out, admin details, API key creation |
| `backend/open_webui/routers/configs.py` | Connections, Code Execution and Models saves, import, export, namespace read |
| `backend/open_webui/routers/images.py` | Images field map, checks, save and every image read |
| `backend/open_webui/routers/evaluations.py`, `backend/open_webui/routers/chats.py`, `backend/open_webui/routers/retrieval.py` | Evaluations, chat and Documents saves |
| `backend/open_webui/routers/openai.py`, `backend/open_webui/routers/ollama.py`, `backend/open_webui/routers/pipelines.py` | Connection saves, cache clearing and connection reads |
| `backend/open_webui/routers/automations.py`, `backend/open_webui/routers/calendar.py`, `backend/open_webui/routers/channels.py`, `backend/open_webui/routers/folders.py`, `backend/open_webui/routers/memories.py`, `backend/open_webui/routers/notes.py`, `backend/open_webui/routers/utils.py`, `backend/open_webui/routers/files.py`, `backend/open_webui/routers/models.py` | Feature gates and limits |
| `backend/open_webui/utils/oauth.py` | The OAuth runtime map and every sign-in use of `oauth.*` keys; tool-server OAuth clients |
| `backend/open_webui/utils/auth.py`, `backend/open_webui/utils/misc.py` | API key checks, token lifetime, MIME matching, duration parsing |
| `backend/open_webui/utils/models.py`, `backend/open_webui/utils/tools.py`, `backend/open_webui/utils/middleware.py` | Model list, defaults and cache; built-in tool gates; chat-time gates |
| `backend/open_webui/utils/memory.py`, `backend/open_webui/utils/automations.py`, `backend/open_webui/utils/context_compaction.py`, `backend/open_webui/utils/subagents.py`, `backend/open_webui/tools/builtin.py` | Memory limits and review, scheduler and runs, compaction, code interpreter engine |
| `backend/open_webui/events.py`, `backend/open_webui/constants.py` | Event names, sinks and payloads; message texts |
| `src/lib/components/admin/Settings/Audio.svelte`, `Authentication.svelte`, `General.svelte`, `Interface.svelte`, `CodeExecution.svelte`, `Connections.svelte`, `Integrations.svelte`, `Evaluations.svelte`, `Documents.svelte`, `Images.svelte`, `Models.svelte`, `Models/ModelDefaultsPanel.svelte` (all under `src/lib/components/admin/Settings/`) | Fields, labels, save behaviour and on-screen messages |
| `src/lib/components/chat/SettingsModal.svelte`, `src/lib/components/common/Switch.svelte`, `src/lib/components/common/SettingsSelect.svelte`, `src/lib/components/AddConnectionModal.svelte`, `src/lib/apis/configs/index.ts`, `src/lib/apis/index.ts` | Save toasts, change events, connection fields, API calls |
| `src/lib/components/chat/Messages/CodeBlock.svelte`, `src/lib/components/chat/MessageInput.svelte`, `src/lib/components/channel/MessageInput.svelte`, `src/lib/components/notes/NoteEditor.svelte`, `src/lib/components/layout/Sidebar/Folders/FolderModal.svelte`, `src/lib/components/chat/Chat.svelte`, `src/lib/components/chat/Messages/ResponseMessage.svelte`, `src/routes/auth/+page.svelte` | Browser-side use of keys sent in `/api/config` |
| `src/lib/i18n/locales/en-US/translation.json` | English text of every dotted label |
| `Dockerfile` | The image's `OLLAMA_BASE_URL` default |

## 14. Open Questions

Live values are data, not code: **every one of the 199 keys' live values is TO BE CONFIRMED** for
production, and so is whether each key has a stored row at all.

### 14.1 How the Counts Were Made

- A read-only script parsed `backend/open_webui/config.py`: it took every line of the
  `DEFAULT_CONFIG` block (`:2822-3228`) of the form `'key': VARIABLE,`, found each variable's
  top-level assignment by parsing the module, and collected every `os.getenv` and
  `os.environ.get` name in that assignment. It found 405 entries, 199 in the 23 namespaces here
  (per-namespace counts in section 1). Where a definition reads its variable through a helper
  variable (for example `_CONTEXT_COMPACTION_TOKEN_CAP` or `audio_tts_openai_params`), the helper
  was read by hand and the variable named in section 7.
- Independent checks: the coverage checker's own pattern over the same block also gives 405 keys
  (`knowledgebase/tools/kb.config.json`, persistent-keys scope; `knowledgebase/tools/inventory.md`),
  and a second script confirmed that section 7 has exactly 199 rows, one per key, each with a
  definition citation that overlaps the variable's assignment, a "Seeded from" cell naming every
  variable the assignment reads, and translation citations whose English text equals the bold
  label beside them. The scripts are working files, not part of the repository.
- The figure of "about 197 keys" in the brief for this continuation does not match; the verified
  number is 199.

### 14.2 Gaps and Items TO BE CONFIRMED

1. **Live values** of all 199 keys, and whether rows exist for them: **TO BE CONFIRMED** (data in
   the `config` table, or in process memory for process-only keys).
2. **Persistence switches in production**: the values of `ENABLE_PERSISTENT_CONFIG`,
   `ENABLE_OAUTH_PERSISTENT_CONFIG`, `RESET_CONFIG_ON_START` and `ENABLE_DB_MIGRATIONS` are
   environment data: **TO BE CONFIRMED**.
3. **Process count and Redis**: how many server processes or replicas run, and whether Redis is
   configured. This decides how far a process-only change, a Whisper model reload or a cleared
   model cache reaches (sections 7.20 and 8.1): **TO BE CONFIRMED**.
4. **Single sign-on provider** used by MedIT GPT and which provider variables are set:
   **TO BE CONFIRMED** (see [`sso-oauth-oidc-and-scim.md`](sso-oauth-oidc-and-scim.md)).
5. **Legacy rows**: whether the production database still holds rows copied from the pre-v0.11.4
   single-row configuration, including `oauth.*` rows or names nothing reads (sections 5.7 and
   6.3): **TO BE CONFIRMED**.
6. **Image variant**: whether production runs the slim image, which changes the audio save
   refusals in section 10: **TO BE CONFIRMED**.
7. **Event consumers**: whether production has admin event webhooks or Event functions that
   receive the events in section 9 (and the admin's personal data in them): **TO BE CONFIRMED**.
8. **Folder file limit**: no server-side check of `folders.max_file_count` was found. A search of
   `backend/open_webui` for the key, `FOLDER_MAX_FILE_COUNT` and `folder_max_file_count` finds only
   the seed, the admin field map and `/api/config`; the only check is in the browser
   (`src/lib/components/layout/Sidebar/Folders/FolderModal.svelte:46-54`). Not tested.
9. **Code Execution success message**: the inference in section 10 that a request failing without
   an error body still shows `Settings saved successfully!` was not tested.
10. **Non-numeric seeds**: `AUTOMATION_MAX_COUNT`, `AUTOMATION_MIN_INTERVAL` and
    `FOLDER_MAX_FILE_COUNT` are seeded as raw text, and every **General** or **Authentication**
    save passes the stored value through a whole-number conversion
    (`backend/open_webui/routers/auths.py:1277-1281`). What an admin sees if a non-numeric value
    was seeded was not tested.
11. **Security-sensitive, referred without detail** (platform maintainer and U of T Information
    Security, security.utoronto.ca): `oauth.merge_accounts_by_email`; turning off
    `ldap.server.validate_cert`; `auth.jwt_expiry` of `-1`; the `jupyter` code engines;
    `automations.auth_token_expires_in`; changes to single sign-on registration or to
    `ENABLE_OAUTH_PERSISTENT_CONFIG`.
12. **Corrections made by this continuation** (in place, marked, section 2.2): the audio endpoint
    handles all 30 `audio.*` keys, not 29; and `/api/config` sends the feature switches to every
    signed-in account, `pending` included. They still need entering in
    `knowledgebase/tools/VERIFICATION.md`, which this researcher was instructed not to edit.
13. **No contradiction with the ground truth** was found: the 405-key total, the seeding rule, the
    `oauth.*` exception and the environment-only provider registration all match
    `knowledgebase/tools/ground-truth.md` ("Settings: Where a Value Comes From"; Accounts and
    Access).
