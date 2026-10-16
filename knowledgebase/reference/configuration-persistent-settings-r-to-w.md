# Configuration: Persistent Settings (rag to webui)

## At a Glance

- This is a catalogue of every persistent setting (one row per dotted key in the database `config` table) in the namespaces `rag`, `subagents`, `task`, `terminal_server`, `tool_server`, `ui`, `user`, `users`, `web`, `webui`, plus the undotted `webhook_url`, as seeded by `DEFAULT_CONFIG` in `backend/open_webui/config.py`.
- Each key is seeded from an environment variable the first time the application starts; after that the stored value wins over the environment unless `ENABLE_PERSISTENT_CONFIG=False`.
- Most keys are edited on an admin settings screen under `/admin/settings/...`; the "Admin screen" column says which, or "none (API or import only)".
- Live values are data in the database or environment and are TO BE CONFIRMED for MedIT GPT; this document gives only what the code seeds.
- *Added 2026-10-11:* section 7 catalogues all **206 keys** in 14 tables; 9 keys have no admin
  screen, and four of those (`rag.tiktoken_encoding_name`, the three Azure AI Search keys) have no
  save path at all. `ui.default_locale` is an inert row: the environment constant is used instead.
- Saving **Documents** also re-saves every `web.*` key with the values it loaded, and silently
  switches hybrid search off when the reranker fails to load (section 5.3).
- The embedding model, the reranker and the tool-server data are rebuilt only at start-up or when
  their screen is saved, in the server process that handled the save (section 8).

## 1. Purpose and Who Uses It

This document is the second half of the persistent-settings catalogue. For every key in
`DEFAULT_CONFIG` whose namespace sorts from `rag` to `webui`, plus the undotted `webhook_url`, it
records the environment variable that seeds the key on a new installation, the code default, the
admin screen that edits it, what it changes, and anything unusual. The first half (`audio` to
`openai`) is [`configuration-persistent-settings-a-to-o.md`](configuration-persistent-settings-a-to-o.md),
whose sections 1 to 6 explain how persistence works; this document points to them rather than
repeating them. Readers are the same: tier-1 support (read-only), MedIT GPT administrators and the
platform maintainer ([`configuration-persistent-settings-a-to-o.md`](configuration-persistent-settings-a-to-o.md)
section 1). Environment variables that are never stored are in
[`configuration-environment-variables-bootstrap.md`](configuration-environment-variables-bootstrap.md).

Scope in numbers: **206 of the 405 keys** in `DEFAULT_CONFIG`
(`backend/open_webui/config.py:2822-3228`): `rag` 76, `web` 78, `ui` 20, `task` 19, `subagents` 7,
and one each for `tool_server`, `terminal_server`, `user`, `users`, `webui` and `webhook_url`. Added
to the 199 keys of the first half this gives 405. A script over `DEFAULT_CONFIG` and an independent
line count agree (section 14 records the method).

| Namespace | What it holds | Area document with the behaviour |
|---|---|---|
| `rag` | Document extraction, chunking, embedding, reranking, retrieval, upload limits, YouTube loading | [`rag-retrieval-embeddings-and-vector-stores.md`](rag-retrieval-embeddings-and-vector-stores.md) |
| `web` | Web search engine, provider credentials, web loader | [`web-search-and-web-loading.md`](web-search-and-web-loading.md) |
| `task`, `subagents` | Background generation tasks (titles, tags, follow-ups, queries, autocomplete) and sub-agents | [`chat-completion-pipeline-and-generation-tasks.md`](chat-completion-pipeline-and-generation-tasks.md) |
| `ui`, `user`, `users`, `webui` | Sign-up and sign-in switches, defaults for new accounts, default models and suggestions, banners, interface defaults, default permissions, the site address | [`admin-settings-panels.md`](admin-settings-panels.md), [`user-settings-and-personalisation.md`](user-settings-and-personalisation.md), [`users-groups-roles-and-permissions.md`](users-groups-roles-and-permissions.md) |
| `tool_server`, `terminal_server` | Tool server and terminal server connection lists | [`workspace-tools-tool-servers-mcp-and-terminals.md`](workspace-tools-tool-servers-mcp-and-terminals.md) |
| `webhook_url` | The legacy single admin webhook address | [`notifications-webhooks-events-and-banners.md`](notifications-webhooks-events-and-banners.md) |

## 2. Navigation and URLs

Admin screens open inside the shared Settings window; `/admin/settings/<tab>` redirects to
`/?settings=admin:<tab>` (`src/routes/(app)/admin/settings/[tab]/+page.svelte:6-10`). The production
host is **TO BE CONFIRMED**, so addresses are relative to the site root.

### 2.1 Screens That Edit Keys in This Scope

| Screen (address) | Keys it edits | Panel component | Section |
|---|---|---|---|
| **Documents** (`/admin/settings/documents`) | most `rag.*` keys; `rag.tiktoken_encoding_name` and `rag.external_reranker_timeout` have no field (sections 7.1 and 7.3) and the two YouTube keys are on Web Search (section 7.4) | `src/lib/components/admin/Settings/Documents.svelte` | 7.1 to 7.4 |
| **Web Search** (`/admin/settings/web`) | every `web.*` key that has a field, plus `rag.youtube_loader_language` and `rag.youtube_loader_proxy_url` | `src/lib/components/admin/Settings/WebSearch.svelte` | 7.4 to 7.7 |
| **Interface** (`/admin/settings/interface`) | the 19 `task.*` keys | `src/lib/components/admin/Settings/Interface.svelte` | 7.8 |
| **Sub-agents** (`/admin/settings/subagents`) | the 7 `subagents.*` keys | `src/lib/components/admin/Settings/Subagents.svelte` | 7.9 |
| **Integrations** (`/admin/settings/integrations`) | `tool_server.connections`, `terminal_server.connections` | `src/lib/components/admin/Settings/Integrations.svelte` | 7.10 |
| **General** (`/admin/settings/general`) | `webui.url`, `users.enable_status`, `ui.enable_community_sharing`, `ui.enable_message_rating`, `ui.enable_user_webhooks`, `ui.watermark`, `ui.default_interface_settings`, `ui.i18n`, `ui.banners`; its **Events** section edits `events.webhooks`, which replaced `webhook_url` | `src/lib/components/admin/Settings/General.svelte` | 7.11, 7.12, 7.14 |
| **Authentication** (`/admin/settings/authentication`) | `ui.enable_signup`, `ui.enable_login_form`, `ui.default_user_role`, `ui.default_group_id`, `ui.pending_user_overlay_title`, `ui.pending_user_overlay_content` | `src/lib/components/admin/Settings/Authentication.svelte` | 7.11 |
| **Models** (`/admin/settings/models`), including **Model Defaults** | `ui.default_models`, `ui.default_pinned_models`, `ui.model_order_list`, `ui.prompt_suggestions`, `ui.prompt_suggestions_i18n` | `src/lib/components/admin/Settings/Models.svelte`; `src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte` | 7.11 |
| **Users** › **Groups** › **Default permissions** (`/admin/users/groups`) | `user.permissions` | `src/lib/components/admin/Users/Groups.svelte:83-98` | 7.13 |
| **Database** › **Import** / **Export** (`/admin/settings/db`) | any key (whole-store import and export) | `src/lib/components/admin/Settings/Database.svelte` | [`configuration-persistent-settings-a-to-o.md`](configuration-persistent-settings-a-to-o.md) 5.6 |

Every admin screen and its labels are described in [`admin-settings-panels.md`](admin-settings-panels.md);
the Documents and Web Search fields are described one by one in the area documents named in
section 1. This document gives each key's label only.

### 2.2 API Endpoints That Read or Write Keys in This Scope

Listed so support can match a browser network trace or a log line to a key; tier 1 does not call
them. All are admin-only unless the Role column says otherwise.

| Method and path | Role | Keys in scope | Evidence |
|---|---|---|---|
| `GET /api/v1/retrieval/config`; `POST /api/v1/retrieval/config/update` | admin | `rag.*` and `web.*` through the field map `RETRIEVAL_CONFIG_KEYS` (also `webui.url` and `user.permissions` are in that map for reading) | `backend/open_webui/routers/retrieval.py:254-415`, `:629-789`, `:962-1551` |
| `GET /api/v1/retrieval/embedding`; `POST /api/v1/retrieval/embedding/update` | admin | the 12 embedding keys (`rag.embedding_engine`, `rag.embedding_model`, `rag.embedding_batch_size`, `rag.embedding_concurrent_requests`, `rag.enable_async_embedding`, `rag.openai.*`, `rag.ollama.*`, `rag.azure_openai.*`) | `backend/open_webui/routers/retrieval.py:468-491`, `:537-626` |
| `GET /api/v1/tasks/config` | any signed-in user | the 19 `task.*` keys (field map `TASK_CONFIG_KEYS`) | `backend/open_webui/routers/tasks.py:41-61`, `:108-110` |
| `POST /api/v1/tasks/config/update` | admin | the 19 `task.*` keys | `backend/open_webui/routers/tasks.py:113-138` |
| `GET` / `POST /api/v1/configs/subagents` | admin | the 7 `subagents.*` keys | `backend/open_webui/routers/configs.py:69-77`, `:783-804` |
| `GET` / `POST /api/v1/configs/tool_servers` | admin | `tool_server.connections` | `backend/open_webui/routers/configs.py:235-298` |
| `GET` / `POST /api/v1/configs/terminal_servers` | admin | `terminal_server.connections` | `backend/open_webui/routers/configs.py:326-352` |
| `GET` / `POST /api/v1/configs/models` | admin | `ui.default_models`, `ui.default_pinned_models`, `ui.model_order_list` | `backend/open_webui/routers/configs.py:62-68`, `:749-770` |
| `POST /api/v1/configs/suggestions` | admin | `ui.prompt_suggestions`, `ui.prompt_suggestions_i18n` | `backend/open_webui/routers/configs.py:817-840` |
| `POST /api/v1/configs/banners` | admin | `ui.banners` | `backend/open_webui/routers/configs.py:852-869` |
| `GET /api/v1/configs/banners` | any signed-in user | `ui.banners` (read only) | `backend/open_webui/routers/configs.py:872-877` |
| `GET` / `POST /api/v1/auths/admin/config` | admin | `webui.url`, `ui.enable_login_form`, `ui.enable_signup`, `ui.default_user_role`, `ui.default_group_id`, `ui.default_interface_settings`, `ui.i18n`, `ui.enable_community_sharing`, `ui.enable_message_rating`, `ui.enable_user_webhooks`, `users.enable_status`, `ui.pending_user_overlay_title`, `ui.pending_user_overlay_content`, `ui.watermark` (field map `ADMIN_CONFIG_KEYS`) | `backend/open_webui/routers/auths.py:104-136`, `:1204-1296` |
| `GET` / `POST /api/v1/users/default/permissions`; `GET /api/v1/users/default/permissions/defaults` | admin | `user.permissions` (the last returns the code defaults, not the stored value) | `backend/open_webui/routers/users.py:411-449` |
| `DELETE /api/events/webhooks/{webhook_id}` | admin | empties `webhook_url` when the **Default webhook** is deleted | `backend/open_webui/main.py:2569`; `backend/open_webui/events.py:911-922` |
| `GET /api/v1/configs/export`; `POST /api/v1/configs/import`; `GET /api/v1/configs/namespace/{namespace}` | admin | every key | `backend/open_webui/routers/configs.py:100-125` |
| `GET /api/config` | anyone; more for signed-in users | a read-only subset (below) | `backend/open_webui/main.py:2224-2472` |

What `/api/config` gives out from this scope:

| Audience | Keys | Evidence |
|---|---|---|
| Everyone, signed in or not | `ui.enable_signup`, `ui.enable_login_form`, `ui.i18n` | `backend/open_webui/main.py:2316`, `:2334-2335` |
| Any signed-in account, including `pending` | `ui.enable_password_change_form`, `web.search.enable`, `web.search.confirmation.enable`, `web.search.confirmation.content`, `task.autocomplete.enable`, `ui.enable_community_sharing`, `ui.enable_message_rating`, `ui.enable_user_webhooks`, `users.enable_status` | `backend/open_webui/main.py:2343-2390` |
| Role `user` or `admin` | `ui.default_models`, `ui.default_pinned_models`, `ui.prompt_suggestions`, `ui.prompt_suggestions_i18n`, `rag.file.max_size`, `rag.file.max_count`, `user.permissions`, `ui.default_interface_settings`, `ui.pending_user_overlay_title`, `ui.pending_user_overlay_content`, `ui.watermark` | `backend/open_webui/main.py:2392-2448` |
| Role `pending` | `ui.pending_user_overlay_title`, `ui.pending_user_overlay_content` | `backend/open_webui/main.py:2449-2459` |

The `default_locale` value in the same response comes from the environment constant
`DEFAULT_LOCALE`, not from the stored `ui.default_locale` (`backend/open_webui/main.py:2315`; section 7.11).

## 3. Roles and Permissions

The rules are those of [`configuration-persistent-settings-a-to-o.md`](configuration-persistent-settings-a-to-o.md)
section 3: only an `admin` can change a key, there is no per-setting permission, and changes to
seeding variables and restarts belong to the platform maintainer (**TO BE CONFIRMED** who that is).
Differences for this scope:

| Action | Who | Evidence |
|---|---|---|
| Read the 19 task settings, including the prompt templates | any signed-in `user` or `admin` | `backend/open_webui/routers/tasks.py:108-110` |
| Read the banner list | any signed-in `user` or `admin` | `backend/open_webui/routers/configs.py:872-877` |
| Read the sign-up and login-form switches and the interface wording overrides (`ui.i18n`) | everyone, before signing in | `backend/open_webui/main.py:2316`, `:2334-2335` |
| Edit the default permissions (`user.permissions`) | `admin`, from **Users** › **Groups**; the page sends non-admins back to `/` | `src/lib/components/admin/Users/Groups.svelte:100-104`; `backend/open_webui/routers/users.py:424-435` |
| Tier-1 support | read-only: may ask an admin to read a value from a screen, never to export the settings | rule of this knowledgebase |

Several keys in this scope **are** permissions or govern who may sign up: `user.permissions` (the
default permission set), `ui.default_user_role`, `ui.default_group_id`, `ui.enable_signup` and
`ui.enable_login_form`. How they combine with groups is in
[`users-groups-roles-and-permissions.md`](users-groups-roles-and-permissions.md) and
`knowledgebase/tools/ground-truth.md` (Accounts and Access).

## 4. Key Concepts and Terminology

The general terms (persistent setting, namespace, seeding variable, code default, seed, stored
value, process-only value, inert row, field name, derived runtime state, legacy names) are defined
in [`configuration-persistent-settings-a-to-o.md`](configuration-persistent-settings-a-to-o.md)
section 4 and mean the same here. Terms that matter for this half:

| Term | Meaning in this codebase | Evidence |
|---|---|---|
| **Sub-prefix** | The second part of a key, which groups related keys: `web.search.*` (engine and providers), `web.loader.*` and `web.fetch.*` (page loading), `rag.file.*`, `rag.openai.*`, `rag.azure_openai.*`, `rag.ollama.*`, `task.<task>.*`. Section 7 has one table per group | `backend/open_webui/config.py:2863-3018`, `:3129-3154` |
| **Retrieval field map** | `RETRIEVAL_CONFIG_KEYS`: 160 upper-case field names mapped to keys, 156 of them in this scope. The Documents and Web Search screens send and receive these names; assigning a field on the server's `RetrievalConfig` object queues that key for saving | `backend/open_webui/routers/retrieval.py:254-415`, `:418-434` |
| **`rag.web` rename** | Earlier releases kept web-search keys under `rag.web.`. Every start moves such rows to `web.`; when both rows exist the `web.` row is kept and the old one deleted | `backend/open_webui/config.py:42-45`; `backend/open_webui/models/config.py:268-300` |
| **Folded object key** | Six keys here hold one JSON object: `rag.mineru_params`, `rag.docling_params`, `web.search.linkup_search_params`, `task.model.params`, `ui.default_interface_settings`, `user.permissions`. A flattened row such as `user.permissions.chat.delete`, or one under the upper-case alias (`USER_PERMISSIONS.`, `TASK_MODEL_PARAMS.` and so on), is folded into the object at start-up and then deleted | `backend/open_webui/models/config.py:24-38`, `:314-366` |
| **Default model string** | `ui.default_models` and `ui.default_pinned_models` hold one comma-separated string of model IDs; a list found at start-up is joined into that string | `backend/open_webui/models/config.py:368-375` |
| **Runtime-only setting** | The YouTube translation value (`YOUTUBE_LOADER_TRANSLATION`) travels with the web-search settings but is not a key and has no field on the Web Search screen: it is kept in the memory of the server process that received it and reset to none at every start | `backend/open_webui/main.py:670`; `backend/open_webui/routers/retrieval.py:781`, `:1390` |
| **Slim refusal** | In the slim Docker image (`USE_SLIM`) the server refuses to save a local embedding engine, DuckDuckGo, Playwright, the Transformers splitter or a new local reranker | `backend/open_webui/routers/retrieval.py:539-540`, `:966-1003` |
| **No save path** | Four keys are seeded and read but no screen or settings endpoint writes them: `rag.tiktoken_encoding_name` and the three `web.search.azure_ai_search_*` keys. After the first start only an import, or a database change by the maintainer, changes them | `backend/open_webui/routers/retrieval.py:256-258`, `:392`, `:792-959`, `:2775-2789` |

### 4.1 Field Names That Differ From the Seeding Variable

Setting an environment variable named after the field does not seed these keys:

| Key | Field name used by the admin API | Seeding variable actually read | Evidence |
|---|---|---|---|
| `rag.top_k` | `TOP_K` | `RAG_TOP_K` | `backend/open_webui/routers/retrieval.py:393`; `backend/open_webui/config.py:968` |
| `rag.top_k_reranker` | `TOP_K_RERANKER` | `RAG_TOP_K_RERANKER` | `backend/open_webui/routers/retrieval.py:394`; `backend/open_webui/config.py:969` |
| `rag.relevance_threshold` | `RELEVANCE_THRESHOLD` | `RAG_RELEVANCE_THRESHOLD` | `backend/open_webui/routers/retrieval.py:368`; `backend/open_webui/config.py:970` |
| `rag.hybrid_bm25_weight` | `HYBRID_BM25_WEIGHT` | `RAG_HYBRID_BM25_WEIGHT` | `backend/open_webui/routers/retrieval.py:318`; `backend/open_webui/config.py:971` |
| `rag.text_splitter` | `TEXT_SPLITTER` | `RAG_TEXT_SPLITTER` | `backend/open_webui/routers/retrieval.py:389`; `backend/open_webui/config.py:1055` |
| `rag.file.allowed_extensions` | `ALLOWED_FILE_EXTENSIONS` | `RAG_ALLOWED_FILE_EXTENSIONS` | `backend/open_webui/routers/retrieval.py:255`; `backend/open_webui/config.py:998-1000` |
| `rag.file.max_count` | `FILE_MAX_COUNT` | `RAG_FILE_MAX_COUNT` | `backend/open_webui/routers/retrieval.py:311`; `backend/open_webui/config.py:981` |
| `rag.file.max_size` | `FILE_MAX_SIZE` | `RAG_FILE_MAX_SIZE` | `backend/open_webui/routers/retrieval.py:312`; `backend/open_webui/config.py:983` |
| `web.search.ollama_cloud_api_key` | `OLLAMA_CLOUD_WEB_SEARCH_API_KEY` | `OLLAMA_CLOUD_API_KEY` | `backend/open_webui/routers/retrieval.py:337`; `backend/open_webui/config.py:1215` |
| `rag.embedding_batch_size` | `RAG_EMBEDDING_BATCH_SIZE` | that name, or the older `RAG_EMBEDDING_OPENAI_BATCH_SIZE` | `backend/open_webui/config.py:1019-1021` |
| `web.search.youcom_api_key` | `YOUCOM_API_KEY` | that name, or `YDC_API_KEY` | `backend/open_webui/config.py:1335` |
| `rag.openai.api_base_url`, `rag.openai.api_key`, `rag.ollama.base_url` | `RAG_OPENAI_API_BASE_URL`, `RAG_OPENAI_API_KEY`, `RAG_OLLAMA_BASE_URL` | those names; when unset, the main connection's `OPENAI_API_BASE_URL`, `OPENAI_API_KEY` and `OLLAMA_BASE_URL` values | `backend/open_webui/config.py:1098-1099`, `:1105` |
| `user.permissions` | `USER_PERMISSIONS` (read only); the Groups screen posts the permission object | one `USER_PERMISSIONS_*` variable per permission (section 7.13) | `backend/open_webui/routers/retrieval.py:395`; `backend/open_webui/config.py:1733-2022` |
| `ui.banners` | `banners` (body of `POST /api/v1/configs/banners`) | `WEBUI_BANNERS` | `backend/open_webui/routers/configs.py:848-859`; `backend/open_webui/config.py:2160-2167` |
| `ui.prompt_suggestions` | `suggestions` (body of `POST /api/v1/configs/suggestions`) | `DEFAULT_PROMPT_SUGGESTIONS` | `backend/open_webui/routers/configs.py:812-829`; `backend/open_webui/config.py:1679-1683` |

## 5. Workflows (Step by Step)

### 5.1 How Persistence Works (Shared With the First Half)

Seeding, later starts, saving, reading a live value safely, and making an environment change take
effect are described once, in
[`configuration-persistent-settings-a-to-o.md`](configuration-persistent-settings-a-to-o.md)
sections 5.1 to 5.5. In short: a key's environment variable is copied into the database on the
first start only; afterwards the stored row wins, saves update the row at once, and reads go to the
database on every use (`backend/open_webui/models/config.py:140-147`, `:197-220`, `:240-266`).
**Never ask for a settings export to read a value**: it contains every provider key and token in
this scope.

### 5.2 What Each Start Does to Keys in This Scope

| Step | Effect on keys in this scope | Evidence |
|---|---|---|
| 1. Reset (only with `RESET_CONFIG_ON_START=True`) | Deletes every row, including the tool and terminal server lists and the event webhook list (`events.webhooks`), then everything is re-seeded from the environment | `backend/open_webui/main.py:363-364`; `backend/open_webui/models/config.py:233-238` |
| 2. Legacy `config.json` import | Writes each property of `DATA_DIR/config.json` as a row, then renames the file `old_config.json` | `backend/open_webui/config.py:85-91` |
| 3. Rename | `rag.web.*` rows become `web.*` | `backend/open_webui/config.py:43`; `backend/open_webui/models/config.py:268-300` |
| 4. Repair | Flattened rows of the six folded object keys are folded back; list-valued `ui.default_models` and `ui.default_pinned_models` become comma-separated strings | `backend/open_webui/models/config.py:302-382` |
| 5. Seed | Keys without a row are inserted from the environment-derived defaults | `backend/open_webui/models/config.py:240-266` |
| 6. Runtime set-up | Old-style access lists inside `tool_server.connections` are migrated and saved; single sign-on clients are registered for MCP tool servers that use OAuth 2.1; the embedding and reranking functions are built from the `rag.*` keys (section 8) | `backend/open_webui/main.py:621-752` |
| 7. Legacy webhook | If `webhook_url` holds an address and no webhook with the id `default` exists, a **Default webhook** for every event is added to `events.webhooks` | `backend/open_webui/main.py:369`; `backend/open_webui/events.py:854-878` |
| 8. Admin bootstrap | When `WEBUI_ADMIN_EMAIL` and `WEBUI_ADMIN_PASSWORD` create the first admin, `ui.enable_signup` is set to `False` | `backend/open_webui/main.py:377-380` |
| 9. Pre-fetch | Tool server specifications are fetched when `tool_server.connections` is not empty; terminal servers are initialized inside the same condition, so with no tool server they are not prepared at start-up | `backend/open_webui/main.py:431-460` |

### 5.3 Saving the Documents Screen

The step-by-step save is in
[`rag-retrieval-embeddings-and-vector-stores.md`](rag-retrieval-embeddings-and-vector-stores.md)
section 7.10. What it means for the stored keys:

1. Unless bypass mode is on, the browser first posts the embedding settings to
   `/api/v1/retrieval/embedding/update`. The server unloads a local embedding model, builds the new
   embedding function, and **only then** saves the 12 embedding keys
   (`backend/open_webui/routers/retrieval.py:537-599`). If building fails, the reply is HTTP 500 and
   none of the embedding keys is saved (`:621-626`).
2. The browser then posts the whole loaded configuration to `/api/v1/retrieval/config/update`
   (`src/lib/components/admin/Settings/Documents.svelte:264-297`, `:325-350`). That object is the
   full `GET /api/v1/retrieval/config` reply, **including its `web` part**, so the server also
   rewrites every `web.*` key with the values that were loaded when the Documents screen was opened
   (`backend/open_webui/routers/retrieval.py:709-788`, `:1313-1396`). *Inferred from code, not
   tested:* a Web Search change saved in another window after the Documents screen was opened is
   undone when Documents is saved.
3. If hybrid search is on and the reranking model fails to load, the server switches
   `rag.enable_hybrid_search` off and saves that, without an error to the browser; only a log line
   records it (`backend/open_webui/routers/retrieval.py:1235-1253`).
4. Cleared number fields for the upload limits are saved as "no limit" (`null`), not left unchanged
   (`backend/open_webui/routers/retrieval.py:1279-1293`;
   `src/lib/components/admin/Settings/Documents.svelte:266-271`).

### 5.4 Saving the Web Search Screen

[`web-search-and-web-loading.md`](web-search-and-web-loading.md) section 7.7 has the steps. The
screen sends only the `web` object, so it does not touch Documents settings, but every `web.*` key
is set to exactly what that object holds (only **Context Tokens** is skipped when absent), and the
two YouTube keys in it (`rag.youtube_loader_language`, `rag.youtube_loader_proxy_url`) are saved
too (`src/lib/components/admin/Settings/WebSearch.svelte:101-107`;
`backend/open_webui/routers/retrieval.py:1313-1396`).

### 5.5 Saving the Other Screens

| Screen | What one save writes | Evidence |
|---|---|---|
| **Interface** (tasks) | All 19 `task.*` keys at once. Every field except `TASK_MODEL_PARAMS` is required, so a request missing one is refused before anything is saved; a request without `TASK_MODEL_PARAMS` saves `task.model.params` as `null`. The screen sends all of them | `backend/open_webui/routers/tasks.py:113-138`; `src/lib/components/admin/Settings/Interface.svelte:64-73` |
| **Sub-agents** | All 7 `subagents.*` keys; every field required | `backend/open_webui/routers/configs.py:773-804` |
| **Models** (default and pinned models, order) | The three `ui.*` keys, plus `models.default_metadata` and `models.default_params` (first half), from one form | `backend/open_webui/routers/configs.py:734-770` |
| **Model Defaults** (prompt suggestions) | Replaces `ui.prompt_suggestions` and `ui.prompt_suggestions_i18n` (the latter becomes `{}` when not sent) | `backend/open_webui/routers/configs.py:817-840` |
| **General** (banners) | Replaces the whole `ui.banners` list | `backend/open_webui/routers/configs.py:852-869` |
| **General** and **Authentication** | The fields each screen sends through `/api/v1/auths/admin/config`; the detail is in [`admin-settings-panels.md`](admin-settings-panels.md) section 5.3 | `backend/open_webui/routers/auths.py:1269-1296` |
| **Integrations** (tool servers) | Replaces `tool_server.connections`, removes and re-registers single sign-on clients for MCP servers, and refreshes the cached tool-server data in that process | `backend/open_webui/routers/configs.py:240-298` |
| **Integrations** (terminal servers) | Replaces `terminal_server.connections` and refreshes the terminal servers in that process | `backend/open_webui/routers/configs.py:331-352` |
| **Users** › **Groups** › **Default permissions** | Replaces the whole `user.permissions` object with the one submitted | `backend/open_webui/routers/users.py:424-435` |

### 5.6 Export and Import in This Scope

The general rules are in
[`configuration-persistent-settings-a-to-o.md`](configuration-persistent-settings-a-to-o.md)
section 5.6. For this half:

- The export contains every web-search provider key, the embedding and reranker API keys, the
  document-loader keys and tokens, the YaCy password and the tool and terminal server connection
  lists with their credentials (`backend/open_webui/routers/configs.py:118-120`). Treat it as a
  secret.
- An import writes keys without checking them (`backend/open_webui/routers/configs.py:100-110`) and
  rebuilds nothing: a different embedding engine, reranker or tool-server list takes effect for the
  cached objects only after that screen's own save or a restart (section 8). *Inferred from code:*
  `rag.web.*` keys in an old file are stored as given and renamed to `web.*` at the next start
  (`backend/open_webui/models/config.py:268-300`).

## 6. Data Model

### 6.1 Storage

Every key in this scope is one row of the `config` table (`key`, JSON `value`, `updated_at` in epoch
seconds), described in
[`configuration-persistent-settings-a-to-o.md`](configuration-persistent-settings-a-to-o.md)
section 6.1. Rows in this area that are **not** in `DEFAULT_CONFIG`, so are never seeded:

| Row | Holds | Evidence |
|---|---|---|
| `events.webhooks` | The admin event-webhook list that replaced `webhook_url` (section 7.14) | `backend/open_webui/events.py:20`, `:854-878` |
| `external_knowledge.connections` | External knowledge connections (Integrations › Knowledge) | `backend/open_webui/routers/knowledge.py:559`; `backend/open_webui/retrieval/external.py:13` |

### 6.2 Value Shapes in This Scope

| Shape | Keys (examples) | Evidence |
|---|---|---|
| Boolean | every `*.enable` key, `rag.full_context`, `rag.pdf_extract_images`, the `rag.datalab_marker_*` switches, `web.loader.ssl_verification`, `web.search.trust_env`, `ui.enable_signup` | `backend/open_webui/config.py:883-897`, `:979`, `:1004`, `:1210-1212`, `:1664` |
| Integer | `rag.top_k`, `rag.chunk_size`, `rag.reranking_batch_size`, `web.search.result_count`, `web.loader.playwright_timeout` (milliseconds), `task.autocomplete.input_max_length`, the `subagents.max_*` limits | `backend/open_webui/config.py:968`, `:1064`, `:1046`, `:1179`, `:1313`, `:2335`, `:2038-2041` |
| Decimal number | `rag.relevance_threshold`, `rag.hybrid_bm25_weight` | `backend/open_webui/config.py:970-971` |
| JSON `null` meaning "no limit" or "not set" | `rag.file.max_size`, `rag.file.max_count`, `web.fetch.max_content_length`, `web.search.exa_max_content_length`, `rag.content_extraction.supported_media_mime_types`, `ui.default_models`, `ui.default_pinned_models`, `ui.prompt_suggestions` | `backend/open_webui/config.py:981-983`, `:1198-1200`, `:1279`, `:870-875`, `:1674-1683` |
| Number held as text | `rag.mineru_api_timeout` (seeded as the text `'300'`), `rag.tika_server_version`, `rag.external_reranker_timeout`, `web.loader.timeout`, `web.loader.firecrawl_timeout` | `backend/open_webui/config.py:905`, `:935`, `:1052`, `:1207`, `:1319` |
| Comma-separated text | `ui.default_models`, `ui.default_pinned_models` | `backend/open_webui/models/config.py:368-375` |
| List of text | `rag.file.allowed_extensions`, `rag.mineru_file_extensions`, `rag.youtube_loader_language`, `web.search.domain.filter_list`, `ui.model_order_list` | `backend/open_webui/config.py:998-1000`, `:917`, `:1152`, `:1182-1194`, `:1687-1693` |
| JSON text (a string, not an object) | `rag.datalab_marker_additional_config`, `web.search.yandex_web_search_config` | `backend/open_webui/config.py:881`, `:1333` |
| Object | `rag.docling_params`, `rag.mineru_params`, `rag.external_document_loader_headers`, `web.search.linkup_search_params`, `task.model.params`, `ui.default_interface_settings`, `ui.i18n`, `ui.prompt_suggestions_i18n`, `user.permissions` | `backend/open_webui/config.py:941-947`, `:909-915`, `:923-931`, `:1339-1345`, `:2185-2190`, `:1712-1718`, `:3090`, `:1685`, `:1940-2022` |
| List of objects | `tool_server.connections`, `terminal_server.connections`, `ui.prompt_suggestions` (when set), `ui.banners` | `backend/open_webui/config.py:381-398`, `:1679-1683`, `:2150-2167` |

### 6.3 Legacy Names and Renames

- Migration `3ff2c63645b8` (the move to one row per key) wrote web-search values under `rag.web.*`
  names, which the start-up rename then moves to `web.*`, and renamed four embedding keys:
  `rag.openai_api_base_url` → `rag.openai.api_base_url`, `rag.openai_api_key` →
  `rag.openai.api_key`, `rag.ollama.url` → `rag.ollama.base_url`, `rag.ollama.key` →
  `rag.ollama.api_key`
  (`backend/open_webui/migrations/versions/3ff2c63645b8_reshape_config_to_per_key_rows.py:312-313`, `:414-419`).
- `webhook_url` is itself a legacy key: v0.11.4 uses the `events.webhooks` list and only copies the
  old address into it (section 7.14).

## 7. Settings and Configuration

One table per namespace, with `rag` and `web` split by screen section and sub-prefix. Columns:

- **Key**: the dotted key, the primary key of its `config` row.
- **Seeded from**: the environment variable read when the server process starts, with the line of
  its definition in `backend/open_webui/config.py`; "then" marks a fallback variable. After the
  first start the stored value wins (section 5.1).
- **Code default**: what the key holds when the variable is unset. For keys, tokens and passwords
  the cell says "secret (set per environment)": no value is reproduced here.
- **Admin screen**: screen › section › **label** (with the condition under which the field is
  shown), citing the panel line and the English label in
  `src/lib/i18n/locales/en-US/translation.json`; "none (API or import only)" when no screen edits it.
- **Effect** and **Notes**: what the key changes, and anything unusual (inert rows, missing save
  paths, folded object keys, start-up-only effects).

**Live values are data, TO BE CONFIRMED** for MedIT GPT; read them only as section 5.1 describes.
The production values of the seeding variables are equally **TO BE CONFIRMED**.

### 7.1 `rag`: Documents › Content Extraction (45 Keys)

Area document: [`rag-retrieval-embeddings-and-vector-stores.md`](rag-retrieval-embeddings-and-vector-stores.md) section 7.1 (field descriptions, when each field is shown). Every key here is sent and received under the field name in `RETRIEVAL_CONFIG_KEYS` (`backend/open_webui/routers/retrieval.py:254-415`) and read by the loaders through `LOADER_CONFIG_KEYS` when a file is processed (`backend/open_webui/retrieval/utils.py:82-144`). The engine-specific fields are shown only while that engine is selected.

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `rag.content_extraction_engine` | `CONTENT_EXTRACTION_ENGINE` (`backend/open_webui/config.py:868`) | empty: the built-in loaders ("Default"; "Basic text only" in the slim image) | Documents › Content Extraction › **Content Extraction Engine** (`src/lib/components/admin/Settings/Documents.svelte:442-445`; `src/lib/i18n/locales/en-US/translation.json:2225`) | Which service extracts text from uploaded files: built-in, `external`, `tika`, `docling`, `datalab_marker`, `document_intelligence`, `mistral_ocr`, `paddleocr_vl` or `mineru` (`src/lib/components/admin/Settings/Documents.svelte:446-458`) | Read for every file processed (`backend/open_webui/retrieval/utils.py:103`, `:142-144`; `backend/open_webui/routers/files.py:147`); the seed is lower-cased (`backend/open_webui/config.py:868`) |
| `rag.content_extraction.supported_media_mime_types` | `CONTENT_EXTRACTION_SUPPORTED_MEDIA_MIME_TYPES` (`backend/open_webui/config.py:870-875`) | `null` (unset) | Documents › Content Extraction › **Supported Media MIME Types** (`src/lib/components/admin/Settings/Documents.svelte:463-469`; `src/lib/i18n/locales/en-US/translation.json:2343`) | Which image and video upload types are sent to the extraction engine | `null` sends media only to the External engine; a list sends matching types to whichever engine is set; an empty list sends none (`backend/open_webui/routers/files.py:111-125`, `:147-150`) |
| `rag.pdf_extract_images` | `PDF_EXTRACT_IMAGES` (`backend/open_webui/config.py:1004`) | off | Documents › Content Extraction › **PDF Extract Images (OCR)** (built-in engine) (`src/lib/components/admin/Settings/Documents.svelte:475-479`; `src/lib/i18n/locales/en-US/translation.json:2308`) | Extracts images from PDFs so OCR can read image-only pages | Also passed to Tika (`backend/open_webui/retrieval/loaders/main.py:568`, `:716`) |
| `rag.pdf_loader_mode` | `PDF_LOADER_MODE` (`backend/open_webui/config.py:1006`) | `page` | Documents › Content Extraction › **PDF Loader Mode** (built-in engine) (`src/lib/components/admin/Settings/Documents.svelte:483-486`; `src/lib/i18n/locales/en-US/translation.json:2310`) | `page` makes one document per PDF page; `single` keeps pages together for chunking | `backend/open_webui/retrieval/loaders/main.py:717` |
| `rag.datalab_marker_api_key` | `DATALAB_MARKER_API_KEY` (`backend/open_webui/config.py:877`) | secret (set per environment); empty in code | Documents › Content Extraction › **API Key** (Datalab Marker API engine) (`src/lib/components/admin/Settings/Documents.svelte:504-511`; `src/lib/i18n/locales/en-US/translation.json:2229`) | API key for Datalab Marker | Without it the built-in loaders are used (`backend/open_webui/retrieval/loaders/main.py:570-594`) |
| `rag.datalab_marker_api_base_url` | `DATALAB_MARKER_API_BASE_URL` (`backend/open_webui/config.py:879`) | empty | Documents › Content Extraction › **API Base URL** (Datalab Marker API engine) (`src/lib/components/admin/Settings/Documents.svelte:493-499`; `src/lib/i18n/locales/en-US/translation.json:2227`) | Datalab Marker endpoint | Empty means the loader uses its own default address (`backend/open_webui/retrieval/loaders/main.py:595-597`) |
| `rag.datalab_marker_additional_config` | `DATALAB_MARKER_ADDITIONAL_CONFIG` (`backend/open_webui/config.py:881`) | empty | Documents › Content Extraction › **Additional Config** (Datalab Marker API engine) (`src/lib/components/admin/Settings/Documents.svelte:516-528`; `src/lib/i18n/locales/en-US/translation.json:2197`) | Extra Marker options as JSON text | Stored as text, not an object; the screen checks it is valid JSON before saving (`src/lib/components/admin/Settings/Documents.svelte:196-206`) |
| `rag.datalab_marker_use_llm` | `DATALAB_MARKER_USE_LLM` (`backend/open_webui/config.py:883`) | off | Documents › Content Extraction › **Use LLM** (Datalab Marker API engine) (`src/lib/components/admin/Settings/Documents.svelte:535-539`; `src/lib/i18n/locales/en-US/translation.json:2361`) | Lets Marker use a language model to improve tables, forms, maths and layout |  |
| `rag.datalab_marker_skip_cache` | `DATALAB_MARKER_SKIP_CACHE` (`backend/open_webui/config.py:885`) | off | Documents › Content Extraction › **Skip Cache** (Datalab Marker API engine) (`src/lib/components/admin/Settings/Documents.svelte:542-546`; `src/lib/i18n/locales/en-US/translation.json:2339`) | Ignores cached Marker results and reprocesses |  |
| `rag.datalab_marker_force_ocr` | `DATALAB_MARKER_FORCE_OCR` (`backend/open_webui/config.py:887`) | off | Documents › Content Extraction › **Force OCR** (Datalab Marker API engine) (`src/lib/components/admin/Settings/Documents.svelte:549-553`; `src/lib/i18n/locales/en-US/translation.json:2261`) | Runs OCR on every PDF page, even pages with embedded text |  |
| `rag.datalab_marker_paginate` | `DATALAB_MARKER_PAGINATE` (`backend/open_webui/config.py:889`) | off | Documents › Content Extraction › **Paginate** (Datalab Marker API engine) (`src/lib/components/admin/Settings/Documents.svelte:556-560`; `src/lib/i18n/locales/en-US/translation.json:2306`) | Separates the output by page |  |
| `rag.datalab_marker_strip_existing_ocr` | `DATALAB_MARKER_STRIP_EXISTING_OCR` (`backend/open_webui/config.py:891`) | off | Documents › Content Extraction › **Strip Existing OCR** (Datalab Marker API engine) (`src/lib/components/admin/Settings/Documents.svelte:563-568`; `src/lib/i18n/locales/en-US/translation.json:2341`) | Removes existing OCR text and reruns OCR when Force OCR is off |  |
| `rag.datalab_marker_disable_image_extraction` | `DATALAB_MARKER_DISABLE_IMAGE_EXTRACTION` (`backend/open_webui/config.py:893-895`) | off | Documents › Content Extraction › **Disable Image Extraction** (Datalab Marker API engine) (`src/lib/components/admin/Settings/Documents.svelte:573-578`; `src/lib/i18n/locales/en-US/translation.json:2231`) | Stops Marker extracting images from PDFs |  |
| `rag.datalab_marker_format_lines` | `DATALAB_MARKER_FORMAT_LINES` (`backend/open_webui/config.py:897`) | off | Documents › Content Extraction › **Format Lines** (Datalab Marker API engine) (`src/lib/components/admin/Settings/Documents.svelte:583-587`; `src/lib/i18n/locales/en-US/translation.json:2263`) | Formats lines to detect inline maths and styles |  |
| `rag.datalab_marker_output_format` | `DATALAB_MARKER_OUTPUT_FORMAT` (`backend/open_webui/config.py:899`) | `markdown` | Documents › Content Extraction › **Output Format** (Datalab Marker API engine) (`src/lib/components/admin/Settings/Documents.svelte:590-593`; `src/lib/i18n/locales/en-US/translation.json:2302`) | Output format returned by Marker (Markdown, JSON or HTML) |  |
| `rag.external_document_loader_url` | `EXTERNAL_DOCUMENT_LOADER_URL` (`backend/open_webui/config.py:919`) | empty | Documents › Content Extraction › **Document Loader URL** (External engine) (`src/lib/components/admin/Settings/Documents.svelte:602-608`; `src/lib/i18n/locales/en-US/translation.json:2243`) | Address of the external document loader | The loader is used only when this and the API key are both set (`backend/open_webui/retrieval/loaders/main.py:541-545`) |
| `rag.external_document_loader_api_key` | `EXTERNAL_DOCUMENT_LOADER_API_KEY` (`backend/open_webui/config.py:921`) | secret (set per environment); empty in code | Documents › Content Extraction › **API Key** (External engine) (`src/lib/components/admin/Settings/Documents.svelte:612-621`; `src/lib/i18n/locales/en-US/translation.json:2257`) | API key sent to the external document loader | If it is empty the built-in loaders are used instead |
| `rag.external_document_loader_headers` | `EXTERNAL_DOCUMENT_LOADER_HEADERS` (`backend/open_webui/config.py:923-931`) | `{}` (an invalid or non-object value becomes `{}`) | Documents › Content Extraction › **Headers** (External engine) (`src/lib/components/admin/Settings/Documents.svelte:627-637`; `src/lib/i18n/locales/en-US/translation.json:2269`) | Extra JSON headers sent to the external loader | May carry credentials; treat as secret (`backend/open_webui/config.py:923-931`) |
| `rag.tika_server_url` | `TIKA_SERVER_URL` (`backend/open_webui/config.py:933`) | `http://tika:9998` | Documents › Content Extraction › **Tika Server URL** (Tika engine) (`src/lib/components/admin/Settings/Documents.svelte:671-677`; `src/lib/i18n/locales/en-US/translation.json:2347`) | Tika server address | If it is empty the built-in loaders are used instead (`backend/open_webui/retrieval/loaders/main.py:560`) |
| `rag.tika_server_version` | `TIKA_SERVER_VERSION` (`backend/open_webui/config.py:935`) | `3`, stored as text | Documents › Content Extraction › **Tika Server Version** (Tika engine) (`src/lib/components/admin/Settings/Documents.svelte:681-684`; `src/lib/i18n/locales/en-US/translation.json:2349`) | Tika API version the loader speaks | `backend/open_webui/retrieval/loaders/main.py:567` |
| `rag.docling_server_url` | `DOCLING_SERVER_URL` (`backend/open_webui/config.py:937`) | `http://docling:5001` | Documents › Content Extraction › **Docling Server URL** (Docling engine) (`src/lib/components/admin/Settings/Documents.svelte:693-699`; `src/lib/i18n/locales/en-US/translation.json:2237`) | Docling server address | If it is empty the built-in loaders are used instead (`backend/open_webui/retrieval/loaders/main.py:613`) |
| `rag.docling_api_key` | `DOCLING_API_KEY` (`backend/open_webui/config.py:939`) | secret (set per environment); empty in code | Documents › Content Extraction › **API Key** (Docling engine) (`src/lib/components/admin/Settings/Documents.svelte:703-709`; `src/lib/i18n/locales/en-US/translation.json:2233`) | API key sent to Docling |  |
| `rag.docling_params` | `DOCLING_PARAMS` (`backend/open_webui/config.py:941-947`) | `{}` (invalid JSON becomes `{}`) | Documents › Content Extraction › **Parameters** (Docling engine) (`src/lib/components/admin/Settings/Documents.svelte:716-721`; `src/lib/i18n/locales/en-US/translation.json:2235`) | Extra Docling parameters as a JSON object | Folded object key (section 4); the screen refuses invalid JSON (`src/lib/components/admin/Settings/Documents.svelte:243-254`) |
| `rag.document_intelligence_endpoint` | `DOCUMENT_INTELLIGENCE_ENDPOINT` (`backend/open_webui/config.py:949`) | empty | Documents › Content Extraction › **Endpoint** (Document Intelligence engine) (`src/lib/components/admin/Settings/Documents.svelte:729-735`; `src/lib/i18n/locales/en-US/translation.json:2253`) | Azure Document Intelligence endpoint | If it is empty the built-in loaders are used instead (`backend/open_webui/retrieval/loaders/main.py:633-635`) |
| `rag.document_intelligence_key` | `DOCUMENT_INTELLIGENCE_KEY` (`backend/open_webui/config.py:951`) | secret (set per environment); empty in code | Documents › Content Extraction › **Key** (Document Intelligence engine) (`src/lib/components/admin/Settings/Documents.svelte:739-745`; `src/lib/i18n/locales/en-US/translation.json:2239`) | Credential for Document Intelligence |  |
| `rag.document_intelligence_model` | `DOCUMENT_INTELLIGENCE_MODEL` (`backend/open_webui/config.py:953`) | `prebuilt-layout` | Documents › Content Extraction › **Document Intelligence Model** (Document Intelligence engine) (`src/lib/components/admin/Settings/Documents.svelte:752-758`; `src/lib/i18n/locales/en-US/translation.json:2241`) | Document Intelligence model name |  |
| `rag.mistral_ocr_api_base_url` | `MISTRAL_OCR_API_BASE_URL` (`backend/open_webui/config.py:955`) | `https://api.mistral.ai/v1` | Documents › Content Extraction › **API Base URL** (Mistral OCR engine) (`src/lib/components/admin/Settings/Documents.svelte:764-770`; `src/lib/i18n/locales/en-US/translation.json:2288`) | Mistral OCR endpoint |  |
| `rag.mistral_ocr_api_key` | `MISTRAL_OCR_API_KEY` (`backend/open_webui/config.py:957`) | secret (set per environment); empty in code | Documents › Content Extraction › **API Key** (Mistral OCR engine) (`src/lib/components/admin/Settings/Documents.svelte:774-780`; `src/lib/i18n/locales/en-US/translation.json:2290`) | API key for Mistral OCR | Without it the built-in loaders are used (`backend/open_webui/retrieval/loaders/main.py:676-678`) |
| `rag.mistral_ocr_use_base64` | `MISTRAL_OCR_USE_BASE64` (`backend/open_webui/config.py:959`) | off | Documents › Content Extraction › **Use Base64** (Mistral OCR engine) (`src/lib/components/admin/Settings/Documents.svelte:785-789`; `src/lib/i18n/locales/en-US/translation.json:2359`) | Sends PDFs as base64 data instead of uploading them first |  |
| `rag.paddleocr_vl_base_url` | `PADDLEOCR_VL_BASE_URL` (`backend/open_webui/config.py:961`) | `http://localhost:8080` | Documents › Content Extraction › **API Base URL** (PaddleOCR-vl engine) (`src/lib/components/admin/Settings/Documents.svelte:794-800`; `src/lib/i18n/locales/en-US/translation.json:2304`) | PaddleOCR-vl endpoint | The engine is used only when this and the token are both set (`backend/open_webui/retrieval/loaders/main.py:688-691`) |
| `rag.paddleocr_vl_token` | `PADDLEOCR_VL_TOKEN` (`backend/open_webui/config.py:963`) | secret (set per environment); empty in code | Documents › Content Extraction › **API Token** (PaddleOCR-vl engine) (`src/lib/components/admin/Settings/Documents.svelte:804-810`; `src/lib/i18n/locales/en-US/translation.json:2205`) | API token for PaddleOCR-vl |  |
| `rag.mineru_api_mode` | `MINERU_API_MODE` (`backend/open_webui/config.py:901`) | `local` | Documents › Content Extraction › **API Mode** (MinerU engine) (`src/lib/components/admin/Settings/Documents.svelte:817-821`; `src/lib/i18n/locales/en-US/translation.json:2201`) | `local` or `cloud` MinerU API | Switching mode on the screen swaps the API URL between the local and cloud addresses (`src/lib/components/admin/Settings/Documents.svelte:821-834`) |
| `rag.mineru_api_url` | `MINERU_API_URL` (`backend/open_webui/config.py:903`) | `http://localhost:8000` | Documents › Content Extraction › **API URL** (MinerU engine) (`src/lib/components/admin/Settings/Documents.svelte:843-851`; `src/lib/i18n/locales/en-US/translation.json:2207`) | MinerU API address |  |
| `rag.mineru_api_key` | `MINERU_API_KEY` (`backend/open_webui/config.py:907`) | secret (set per environment); empty in code | Documents › Content Extraction › **API Key** (MinerU engine) (`src/lib/components/admin/Settings/Documents.svelte:856-863`; `src/lib/i18n/locales/en-US/translation.json:2284`) | API key for MinerU cloud mode | The screen requires it in cloud mode (`src/lib/components/admin/Settings/Documents.svelte:231-236`) |
| `rag.mineru_api_timeout` | `MINERU_API_TIMEOUT` (`backend/open_webui/config.py:905`) | `300` seconds, seeded as text | Documents › Content Extraction › **API Timeout** (MinerU engine) (`src/lib/components/admin/Settings/Documents.svelte:868-875`; `src/lib/i18n/locales/en-US/translation.json:2203`) | Longest wait for a MinerU response | A value that is not a whole number falls back to 300 (`backend/open_webui/retrieval/loaders/main.py:661-666`) |
| `rag.mineru_params` | `MINERU_PARAMS` (`backend/open_webui/config.py:909-915`) | `{}` (invalid JSON becomes `{}`) | Documents › Content Extraction › **Parameters** (MinerU engine) (`src/lib/components/admin/Settings/Documents.svelte:881-886`; `src/lib/i18n/locales/en-US/translation.json:2286`) | Advanced MinerU parameters as a JSON object | Folded object key (section 4) |
| `rag.mineru_file_extensions` | `MINERU_FILE_EXTENSIONS` (`backend/open_webui/config.py:917`) | `["pdf"]` | Documents › Content Extraction › **File Extensions** (MinerU engine) (`src/lib/components/admin/Settings/Documents.svelte:893-899`; `src/lib/i18n/locales/en-US/translation.json:2259`) | File extensions MinerU handles | Other files use the built-in loaders (`backend/open_webui/retrieval/loaders/main.py:660`) |
| `rag.bypass_embedding_and_retrieval` | `BYPASS_EMBEDDING_AND_RETRIEVAL` (`backend/open_webui/config.py:965`) | off | Documents › Content Extraction › **Bypass Embedding and Retrieval** (`src/lib/components/admin/Settings/Documents.svelte:905-912`; `src/lib/i18n/locales/en-US/translation.json:2217`) | Skips chunking, embedding and search: whole documents are passed to the model | While on, the screen hides the chunking, Embedding and most Retrieval fields and does not save the embedding settings (`src/lib/components/admin/Settings/Documents.svelte:239-241`, `:917`, `:1004`); it also suppresses loading the reranker (`backend/open_webui/main.py:685`) |
| `rag.text_splitter` | `RAG_TEXT_SPLITTER` (`backend/open_webui/config.py:1055`) | empty, shown as the character splitter | Documents › Content Extraction › **Text Splitter** (`src/lib/components/admin/Settings/Documents.svelte:919-922`; `src/lib/i18n/locales/en-US/translation.json:2345`) | How extracted text is split: character (empty or `character`), `token` (Tiktoken) or `token_transformers` | Read at each file processed (`backend/open_webui/routers/retrieval.py:1686-1800`); the slim image refuses a switch to `token_transformers` (`:984-987`) |
| `rag.tokenizer_model` | `RAG_TOKENIZER_MODEL` (`backend/open_webui/config.py:1011`) | empty: the local embedding model's tokenizer | Documents › Content Extraction › **Tokenizer Model** (Token (Transformers) splitter) (`src/lib/components/admin/Settings/Documents.svelte:933-939`; `src/lib/i18n/locales/en-US/translation.json:2352`) | Tokenizer used by the Transformers splitter | Saved with surrounding spaces removed (`backend/open_webui/routers/retrieval.py:1273-1277`, `:1652-1655`) |
| `rag.enable_markdown_header_text_splitter` | `ENABLE_MARKDOWN_HEADER_TEXT_SPLITTER` (`backend/open_webui/config.py:1057`) | on | Documents › Content Extraction › **Markdown Header Text Splitter** (`src/lib/components/admin/Settings/Documents.svelte:947-952`; `src/lib/i18n/locales/en-US/translation.json:2278`) | Splits documents at Markdown headings before the main splitter | `backend/open_webui/routers/retrieval.py:1756` |
| `rag.tiktoken_encoding_name` | `TIKTOKEN_ENCODING_NAME` (`backend/open_webui/config.py:1061`) | `cl100k_base` | none (API or import only) | Tiktoken encoding used by the `token` splitter | **No save path** (section 4): not in the settings form, so after the first start only an import or a database change alters it (`backend/open_webui/routers/retrieval.py:392`, `:1686-1687`) |
| `rag.chunk_size` | `CHUNK_SIZE` (`backend/open_webui/config.py:1064`) | `1000` | Documents › Content Extraction › **Chunk Size** (`src/lib/components/admin/Settings/Documents.svelte:959-966`; `src/lib/i18n/locales/en-US/translation.json:2223`) | Largest chunk, in characters or tokens depending on the splitter |  |
| `rag.chunk_overlap` | `CHUNK_OVERLAP` (`backend/open_webui/config.py:1068`) | `100` | Documents › Content Extraction › **Chunk Overlap** (`src/lib/components/admin/Settings/Documents.svelte:972-979`; `src/lib/i18n/locales/en-US/translation.json:2221`) | Overlap kept between neighbouring chunks |  |
| `rag.chunk_min_size_target` | `CHUNK_MIN_SIZE_TARGET` (`backend/open_webui/config.py:1066`) | `0` (no merging) | Documents › Content Extraction › **Chunk Min Size Target** (Markdown header splitter on) (`src/lib/components/admin/Settings/Documents.svelte:988-995`; `src/lib/i18n/locales/en-US/translation.json:2219`) | Merges chunks smaller than this when possible | `backend/open_webui/routers/retrieval.py:1590-1591`, `:1784` |

### 7.2 `rag`: Documents › Embedding (12 Keys)

Area document: [`rag-retrieval-embeddings-and-vector-stores.md`](rag-retrieval-embeddings-and-vector-stores.md) section 7.2. The whole section is hidden while **Bypass Embedding and Retrieval** is on (`src/lib/components/admin/Settings/Documents.svelte:1004`). These 12 keys are written only by `POST /api/v1/retrieval/embedding/update` (`backend/open_webui/routers/retrieval.py:537-626`). How they are used: new documents are embedded with a function built from the stored keys at that moment, reusing the local model already loaded in the process (`backend/open_webui/routers/retrieval.py:1846-1875`); searches use the function built at start-up or at the last save in that process (`backend/open_webui/main.py:699-745`; section 8).

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `rag.embedding_engine` | `RAG_EMBEDDING_ENGINE` (`backend/open_webui/config.py:1002`) | empty: local SentenceTransformers model (disabled in the slim image) | Documents › Embedding › **Embedding Model Engine** (`src/lib/components/admin/Settings/Documents.svelte:1007-1011`; `src/lib/i18n/locales/en-US/translation.json:2251`) | Which service turns text into vectors: local (empty), `ollama`, `openai` or `azure_openai` | Saved only through `/api/v1/retrieval/embedding/update`, which rebuilds the embedding function first (section 5.3). Changing it does not re-embed existing knowledge (`settings.admin.documents.embeddingModel.description`, `src/lib/i18n/locales/en-US/translation.json:2248`) |
| `rag.embedding_model` | `RAG_EMBEDDING_MODEL` (`backend/open_webui/config.py:1008`) | `sentence-transformers/all-MiniLM-L6-v2` | Documents › Embedding › **Embedding Model** (`src/lib/components/admin/Settings/Documents.svelte:1122-1133`; `src/lib/i18n/locales/en-US/translation.json:2249`) | The embedding model name for the chosen engine | Saved with surrounding spaces removed (`backend/open_webui/routers/retrieval.py:546`); logged at start-up (`backend/open_webui/config.py:1009`) |
| `rag.embedding_batch_size` | `RAG_EMBEDDING_BATCH_SIZE`, then `RAG_EMBEDDING_OPENAI_BATCH_SIZE` (`backend/open_webui/config.py:1019-1021`) | `1` | Documents › Embedding › **Embedding Batch Size** (`src/lib/components/admin/Settings/Documents.svelte:1175-1179`; `src/lib/i18n/locales/en-US/translation.json:2245`) | Number of texts sent per embedding request | Seeded from the older `RAG_EMBEDDING_OPENAI_BATCH_SIZE` when `RAG_EMBEDDING_BATCH_SIZE` is unset |
| `rag.enable_async_embedding` | `ENABLE_ASYNC_EMBEDDING` (`backend/open_webui/config.py:1023`) | on | Documents › Embedding › **Async Embedding Processing** (Ollama, OpenAI or Azure OpenAI engine) (`src/lib/components/admin/Settings/Documents.svelte:1190-1194`; `src/lib/i18n/locales/en-US/translation.json:2209`) | Sends embedding batches concurrently | Field shown only for the remote engines (`src/lib/components/admin/Settings/Documents.svelte:1188`) |
| `rag.embedding_concurrent_requests` | `RAG_EMBEDDING_CONCURRENT_REQUESTS` (`backend/open_webui/config.py:1025`) | `0` (unlimited) | Documents › Embedding › **Embedding Concurrent Requests** (`src/lib/components/admin/Settings/Documents.svelte:1197-1203`; `src/lib/i18n/locales/en-US/translation.json:2247`) | Cap on simultaneous embedding requests |  |
| `rag.openai.api_base_url` | `RAG_OPENAI_API_BASE_URL`, then the main connection's `OPENAI_API_BASE_URL` (`backend/open_webui/config.py:1098`, `:323`, `:329-330`) | `https://api.openai.com/v1` when neither variable is set | Documents › Embedding › **API Base URL** (OpenAI engine) (`src/lib/components/admin/Settings/Documents.svelte:1037-1043`; `src/lib/i18n/locales/en-US/translation.json:2300`) | OpenAI-compatible embeddings endpoint | Renamed from `rag.openai_api_base_url` by the per-key migration (section 6.3) |
| `rag.openai.api_key` | `RAG_OPENAI_API_KEY`, then the main connection's `OPENAI_API_KEY` (`backend/open_webui/config.py:1099`, `:322`) | secret (set per environment); empty in code | Documents › Embedding › **API Key** (OpenAI engine) (`src/lib/components/admin/Settings/Documents.svelte:1048-1054`; `src/lib/i18n/locales/en-US/translation.json:2298`) | API key for embedding requests | Renamed from `rag.openai_api_key` (section 6.3) |
| `rag.azure_openai.base_url` | `RAG_AZURE_OPENAI_BASE_URL` (`backend/open_webui/config.py:1101`) | empty | Documents › Embedding › **API Base URL** (Azure OpenAI engine) (`src/lib/components/admin/Settings/Documents.svelte:1087-1093`; `src/lib/i18n/locales/en-US/translation.json:2213`) | Azure OpenAI endpoint for embeddings |  |
| `rag.azure_openai.api_key` | `RAG_AZURE_OPENAI_API_KEY` (`backend/open_webui/config.py:1102`) | secret (set per environment); empty in code | Documents › Embedding › **API Key** (Azure OpenAI engine) (`src/lib/components/admin/Settings/Documents.svelte:1098-1104`; `src/lib/i18n/locales/en-US/translation.json:2211`) | Azure OpenAI API key |  |
| `rag.azure_openai.api_version` | `RAG_AZURE_OPENAI_API_VERSION` (`backend/open_webui/config.py:1103`) | empty | Documents › Embedding › **Version** (Azure OpenAI engine) (`src/lib/components/admin/Settings/Documents.svelte:1108-1114`; `src/lib/i18n/locales/en-US/translation.json:2363`) | Azure OpenAI API version | Used only with the Azure engine (`backend/open_webui/routers/retrieval.py:592-594`) |
| `rag.ollama.base_url` | `RAG_OLLAMA_BASE_URL`, then the main `OLLAMA_BASE_URL` (itself derived from `OLLAMA_API_BASE_URL` when unset) (`backend/open_webui/config.py:1105`, `:239-262`) | the main Ollama address; `http://localhost:11434` when nothing is set outside Docker or Kubernetes | Documents › Embedding › **API Base URL** (Ollama engine) (`src/lib/components/admin/Settings/Documents.svelte:1062-1068`; `src/lib/i18n/locales/en-US/translation.json:2294`) | Ollama endpoint used for embeddings | Renamed from `rag.ollama.url` (section 6.3) |
| `rag.ollama.api_key` | `RAG_OLLAMA_API_KEY` (`backend/open_webui/config.py:1107`) | secret (set per environment); empty in code | Documents › Embedding › **API Key** (Ollama engine) (`src/lib/components/admin/Settings/Documents.svelte:1073-1079`; `src/lib/i18n/locales/en-US/translation.json:2292`) | Optional API key for Ollama embedding requests | Renamed from `rag.ollama.key` (section 6.3) |

### 7.3 `rag`: Documents › Retrieval (14 Keys)

Area document: [`rag-retrieval-embeddings-and-vector-stores.md`](rag-retrieval-embeddings-and-vector-stores.md) sections 7.3 and 5.8. Search-time keys are read from the store on every chat request, so a save applies to the next message in every server process; the reranker keys instead build an object per process (section 8).

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `rag.full_context` | `RAG_FULL_CONTEXT` (`backend/open_webui/config.py:979`) | off | Documents › Retrieval › **Full Context Mode** (bypass off) (`src/lib/components/admin/Settings/Documents.svelte:1217-1223`; `src/lib/i18n/locales/en-US/translation.json:2265`) | Puts whole attached documents into the prompt instead of the best-matching chunks | Read for every chat request (`backend/open_webui/utils/middleware.py:2113`, `:2133`); an attachment set to full mode forces it for that request |
| `rag.enable_hybrid_search` | `ENABLE_RAG_HYBRID_SEARCH` (`backend/open_webui/config.py:973`) | off (the seed treats only `true` as on) | Documents › Retrieval › **Hybrid Search** (full context off) (`src/lib/components/admin/Settings/Documents.svelte:1228-1232`; `src/lib/i18n/locales/en-US/translation.json:2272`) | Combines keyword (BM25) and semantic search, then reranks | Read for every chat request (`backend/open_webui/utils/middleware.py:2112`, `:2132`). **The server switches it off and saves that** when the reranker fails to load during a Documents save (`backend/open_webui/routers/retrieval.py:1251-1253`; section 11.1) |
| `rag.enable_hybrid_search_enriched_texts` | `ENABLE_RAG_HYBRID_SEARCH_ENRICHED_TEXTS` (`backend/open_webui/config.py:975-977`) | off | Documents › Retrieval › **Enrich Hybrid Search Text** (hybrid search on) (`src/lib/components/admin/Settings/Documents.svelte:1237-1242`; `src/lib/i18n/locales/en-US/translation.json:2255`) | Adds file names, titles, sections and snippets to the keyword index to improve recall |  |
| `rag.reranking_engine` | `RAG_RERANKING_ENGINE` (`backend/open_webui/config.py:1033`) | empty: local SentenceTransformers cross-encoder (disabled in the slim image) | Documents › Retrieval › **Reranking Engine** (hybrid search on) (`src/lib/components/admin/Settings/Documents.svelte:1248-1252`; `src/lib/i18n/locales/en-US/translation.json:2325`) | Which reranker is used: local (empty) or `external` | Loaded into the reranker object at start-up and at each Documents save, per process (`backend/open_webui/main.py:672-697`; `backend/open_webui/routers/retrieval.py:1235-1250`) |
| `rag.external_reranker_url` | `RAG_EXTERNAL_RERANKER_URL` (`backend/open_webui/config.py:1048`) | empty | Documents › Retrieval › **API Base URL** (External reranking engine) (`src/lib/components/admin/Settings/Documents.svelte:1272-1280`; `src/lib/i18n/locales/en-US/translation.json:2314`) | External reranker endpoint | Loaded into the reranker object at start-up and at each Documents save, per process (`backend/open_webui/main.py:672-697`; `backend/open_webui/routers/retrieval.py:1235-1250`) |
| `rag.external_reranker_api_key` | `RAG_EXTERNAL_RERANKER_API_KEY` (`backend/open_webui/config.py:1050`) | secret (set per environment); empty in code | Documents › Retrieval › **API Key** (External reranking engine) (`src/lib/components/admin/Settings/Documents.svelte:1285-1295`; `src/lib/i18n/locales/en-US/translation.json:2312`) | API key sent to the external reranker | Loaded into the reranker object at start-up and at each Documents save, per process (`backend/open_webui/main.py:672-697`; `backend/open_webui/routers/retrieval.py:1235-1250`) |
| `rag.external_reranker_timeout` | `RAG_EXTERNAL_RERANKER_TIMEOUT` (`backend/open_webui/config.py:1052`) | empty (no timeout), stored as text | none (API or import only) | Request timeout for the external reranker, in seconds, converted to a whole number when the reranker is built | No field on the screen; writable only through `/api/v1/retrieval/config/update` or an import (`backend/open_webui/routers/retrieval.py:937`, `:1216-1220`; `:182`) |
| `rag.reranking_model` | `RAG_RERANKING_MODEL` (`backend/open_webui/config.py:1035`) | empty: no reranking model is loaded | Documents › Retrieval › **Reranking Model** (hybrid search on) (`src/lib/components/admin/Settings/Documents.svelte:1303-1311`; `src/lib/i18n/locales/en-US/translation.json:2327`) | Reranking model name for the chosen engine | An empty name loads no reranker (`backend/open_webui/routers/retrieval.py:183-194`); the slim image refuses a new local model (`:988-1003`). Loaded into the reranker object at start-up and at each Documents save, per process (`backend/open_webui/main.py:672-697`; `backend/open_webui/routers/retrieval.py:1235-1250`) |
| `rag.reranking_batch_size` | `RAG_RERANKING_BATCH_SIZE` (`backend/open_webui/config.py:1046`) | `32` | Documents › Retrieval › **Reranking Batch Size** (full context off) (`src/lib/components/admin/Settings/Documents.svelte:1317-1321`; `src/lib/i18n/locales/en-US/translation.json:2323`) | Results scored per reranker batch | Built into the reranking function at start-up and save (`backend/open_webui/main.py:747-752`) |
| `rag.top_k` | `RAG_TOP_K` (`backend/open_webui/config.py:968`) | `3` | Documents › Retrieval › **Top K** (full context off) (`src/lib/components/admin/Settings/Documents.svelte:1331-1338`; `src/lib/i18n/locales/en-US/translation.json:2354`) | Number of chunks returned per search | Read for every chat request (`backend/open_webui/utils/middleware.py:2108`, `:2123`); the knowledge tool for models uses 5 when it is empty (`backend/open_webui/tools/builtin.py:2572`) |
| `rag.top_k_reranker` | `RAG_TOP_K_RERANKER` (`backend/open_webui/config.py:969`) | `3` | Documents › Retrieval › **Top K Reranker** (hybrid search on) (`src/lib/components/admin/Settings/Documents.svelte:1346-1353`; `src/lib/i18n/locales/en-US/translation.json:2356`) | Number of hybrid results kept after reranking | The screen text says "sent to the reranker"; in code it is the number kept (`backend/open_webui/retrieval/utils.py:581-586`) |
| `rag.relevance_threshold` | `RAG_RELEVANCE_THRESHOLD` (`backend/open_webui/config.py:970`) | `0.0` | Documents › Retrieval › **Relevance Threshold** (hybrid search on) (`src/lib/components/admin/Settings/Documents.svelte:1360-1368`; `src/lib/i18n/locales/en-US/translation.json:2321`) | Minimum relevance score (0.0 to 1.0) a result needs to be used |  |
| `rag.hybrid_bm25_weight` | `RAG_HYBRID_BM25_WEIGHT` (`backend/open_webui/config.py:971`) | `0.5` | Documents › Retrieval › **BM25 Weight** (hybrid search on) (`src/lib/components/admin/Settings/Documents.svelte:1376-1402`; `src/lib/i18n/locales/en-US/translation.json:2215`) | Weight of keyword (BM25) results against semantic results; higher favours keywords | `backend/open_webui/retrieval/utils.py:575-579`. Choosing **Default** on the screen sends no value, so a stored weight is kept (`backend/open_webui/routers/retrieval.py:1031-1033`) |
| `rag.template` | `RAG_TEMPLATE` (`backend/open_webui/config.py:1096`) | the built-in template (`backend/open_webui/config.py:1070-1094`) | Documents › Retrieval › **RAG Template** (`src/lib/components/admin/Settings/Documents.svelte:1427-1437`; `src/lib/i18n/locales/en-US/translation.json:2316`) | Prompt wrapper used when retrieved content is added to a chat | Read for every chat request (`backend/open_webui/utils/middleware.py:998`, `:1004`); an empty template falls back to the built-in one (`backend/open_webui/utils/task.py:265-267`) |

### 7.4 `rag`: Documents › Files and the YouTube Loader (5 Keys)

Areas: [`files-uploads-and-storage.md`](files-uploads-and-storage.md) for how the limits act on uploads, and [`web-search-and-web-loading.md`](web-search-and-web-loading.md) for YouTube loading. The two YouTube keys keep their `rag.` names but are edited on **Web Search** and sent inside its `web` object (`backend/open_webui/routers/retrieval.py:779-780`, `:1388-1389`). Clearing a limit on the screen saves `null`, meaning no limit (section 5.3).

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `rag.file.allowed_extensions` | `RAG_ALLOWED_FILE_EXTENSIONS` (`backend/open_webui/config.py:998-1000`) | `[]` (every type allowed) | Documents › Files › **Allowed File Extensions** (`src/lib/components/admin/Settings/Documents.svelte:1456-1463`; `src/lib/i18n/locales/en-US/translation.json:2199`) | File extensions accepted for uploads that are processed for retrieval | Checked by the server at upload (`backend/open_webui/routers/files.py:354-362`); the screen edits it as comma-separated text |
| `rag.file.max_size` | `RAG_FILE_MAX_SIZE` (`backend/open_webui/config.py:983`) | `null` (no limit) | Documents › Files › **Max Upload Size** (`src/lib/components/admin/Settings/Documents.svelte:1470-1477`; `src/lib/i18n/locales/en-US/translation.json:2282`) | Largest upload, in megabytes | Checked by the server at upload and for fetched URLs (`backend/open_webui/routers/files.py:394-400`; `backend/open_webui/routers/retrieval.py:2376`) and sent to browsers (`backend/open_webui/main.py:2414`). The same variable also sets an environment-only metadata limit that keeps following the environment (`backend/open_webui/env.py:841-848`) |
| `rag.file.max_count` | `RAG_FILE_MAX_COUNT` (`backend/open_webui/config.py:981`) | `null` (no limit) | Documents › Files › **Max Upload Count** (`src/lib/components/admin/Settings/Documents.svelte:1483-1490`; `src/lib/i18n/locales/en-US/translation.json:2280`) | Most files that can be attached at once in a chat | Enforced only in the browser, from `/api/config` (`backend/open_webui/main.py:2415`; `src/lib/components/chat/MessageInput.svelte:1091-1096`; `src/lib/components/chat/Chat.svelte:3154-3155`) |
| `rag.youtube_loader_language` | `YOUTUBE_LOADER_LANGUAGE` (`backend/open_webui/config.py:1152`) | `["en"]` | Web Search › Loader › **Youtube Language** (`src/lib/components/admin/Settings/WebSearch.svelte:1467-1474`; `src/lib/i18n/locales/en-US/translation.json:2733`) | Preferred YouTube transcript languages, in order | Saved by both the Web Search and the Documents screens (section 5.3); read by the loader per URL (`backend/open_webui/retrieval/utils.py:84`) |
| `rag.youtube_loader_proxy_url` | `YOUTUBE_LOADER_PROXY_URL` (`backend/open_webui/config.py:1154`) | empty | Web Search › Loader › **Youtube Proxy URL** (`src/lib/components/admin/Settings/WebSearch.svelte:1480-1487`; `src/lib/i18n/locales/en-US/translation.json:2735`) | Proxy used for YouTube transcript requests | Read by the loader per URL (`backend/open_webui/retrieval/utils.py:85`) |

### 7.5 `web.search`: General Search Settings (10 Keys)

Area document: [`web-search-and-web-loading.md`](web-search-and-web-loading.md) sections 7.1 and 7.7. Every key in sections 7.5 to 7.7 is read from the store at each search or page load, so a save applies to the next search in every server process. Saving **Documents** re-saves all of them with the values loaded when that screen was opened (section 5.3).

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `web.search.enable` | `ENABLE_WEB_SEARCH` (`backend/open_webui/config.py:1161`) | off | Web Search › Search › **Web Search** (`src/lib/components/admin/Settings/WebSearch.svelte:175-179`; `src/lib/i18n/locales/en-US/translation.json:2718`) | Master switch for web search in chats, automations and the web-search tool | The server refuses searches while it is off (`backend/open_webui/routers/retrieval.py:2882-2889`); browsers learn it from `/api/config` and need a reload (`backend/open_webui/main.py:2362`; `backend/open_webui/utils/middleware.py:2700`) |
| `web.search.confirmation.enable` | `ENABLE_WEB_SEARCH_CONFIRMATION` (`backend/open_webui/config.py:1163`) | off | Web Search › Search › **Web Search Confirmation** (`src/lib/components/admin/Settings/WebSearch.svelte:183-188`; `src/lib/i18n/locales/en-US/translation.json:2720`) | Asks users to confirm before a web search runs | Sent to browsers through `/api/config` (`backend/open_webui/main.py:2363`) |
| `web.search.confirmation.content` | `WEB_SEARCH_CONFIRMATION_CONTENT` (`backend/open_webui/config.py:1165-1168`) | `Your query will be sent to the configured web search provider.` | Web Search › Search › **Web Search Confirmation Content** (confirmation on) (`src/lib/components/admin/Settings/WebSearch.svelte:195-203`; `src/lib/i18n/locales/en-US/translation.json:2722`) | The message shown in that confirmation | Sent to browsers through `/api/config` (`backend/open_webui/main.py:2364`) |
| `web.search.engine` | `WEB_SEARCH_ENGINE` (`backend/open_webui/config.py:1170`) | empty (no provider chosen); the list is a required field, so the screen cannot be saved until one is chosen (`src/lib/components/admin/Settings/WebSearch.svelte:212-215`) | Web Search › Search › **Web Search Engine** (`src/lib/components/admin/Settings/WebSearch.svelte:209-213`; `src/lib/i18n/locales/en-US/translation.json:2724`) | Which search provider is used; selects which provider fields in section 7.6 apply | Read for every search (`backend/open_webui/routers/retrieval.py:2901-2927`); the slim image refuses a switch to DuckDuckGo (`backend/open_webui/routers/retrieval.py:966-975`) |
| `web.search.bypass_embedding_and_retrieval` | `BYPASS_WEB_SEARCH_EMBEDDING_AND_RETRIEVAL` (`backend/open_webui/config.py:1172-1174`) | off | Web Search › Search › **Bypass Embedding and Retrieval** (`src/lib/components/admin/Settings/WebSearch.svelte:1198-1205`; `src/lib/i18n/locales/en-US/translation.json:2647`) | Passes search results straight to the model instead of embedding and searching them | `backend/open_webui/routers/retrieval.py:2995` |
| `web.search.bypass_web_loader` | `BYPASS_WEB_SEARCH_WEB_LOADER` (`backend/open_webui/config.py:1177`) | off | Web Search › Search › **Bypass Web Loader** (`src/lib/components/admin/Settings/WebSearch.svelte:1211-1215`; `src/lib/i18n/locales/en-US/translation.json:2649`) | Uses the search results' snippets without fetching the pages | `backend/open_webui/routers/retrieval.py:2960` |
| `web.search.result_count` | `WEB_SEARCH_RESULT_COUNT` (`backend/open_webui/config.py:1179`) | `3` | Web Search › Search › **Search Result Count** (under Search Limits, while web search is on) (`src/lib/components/admin/Settings/WebSearch.svelte:1138-1144`; `src/lib/i18n/locales/en-US/translation.json:2692`) | Number of results requested per query |  |
| `web.search.concurrent_requests` | `WEB_SEARCH_CONCURRENT_REQUESTS` (`backend/open_webui/config.py:1196`) | `0` (unlimited; 1 runs queries one at a time) | Web Search › Search › **Concurrent Requests** (under Search Limits, while web search is on) (`src/lib/components/admin/Settings/WebSearch.svelte:1155-1162`; `src/lib/i18n/locales/en-US/translation.json:2651`) | Cap on simultaneous search requests | `backend/open_webui/routers/retrieval.py:2903-2934`; also passed to the DuckDuckGo engine (`:2694`) |
| `web.search.domain.filter_list` | `WEB_SEARCH_DOMAIN_FILTER_LIST` (`backend/open_webui/config.py:1183-1194`) | `[]` (an invalid value also gives `[]`) | Web Search › Search › **Domain Filter List** (while web search is on) (`src/lib/components/admin/Settings/WebSearch.svelte:1184-1192`; `src/lib/i18n/locales/en-US/translation.json:2655`) | Domains to keep, or to exclude when prefixed with `!` | Seeded from a JSON list (`backend/open_webui/config.py:1182-1194`); edited as comma-separated text |
| `web.search.trust_env` | `WEB_SEARCH_TRUST_ENV` (`backend/open_webui/config.py:1212`) | on | Web Search › Search › **Trust Proxy Environment** (`src/lib/components/admin/Settings/WebSearch.svelte:1219-1225`; `src/lib/i18n/locales/en-US/translation.json:2712`) | Uses the server's proxy environment variables when fetching pages | The proxy variables themselves are environment-only |

### 7.6 `web.search`: Provider Settings (56 Keys)

Area document: [`web-search-and-web-loading.md`](web-search-and-web-loading.md) section 7.3 (what each provider is). A provider's fields appear only while its engine is selected in **Web Search Engine** (`src/lib/components/admin/Settings/WebSearch.svelte:230-1100`). Each engine branch of the server's search function reads its keys at every search (`backend/open_webui/routers/retrieval.py:2511-2879`); the engine names below are the values stored in `web.search.engine`.

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `web.search.ollama_cloud_api_key` | `OLLAMA_CLOUD_API_KEY` (`backend/open_webui/config.py:1215`) | secret (set per environment); empty in code | Web Search › Search › **Ollama Cloud API Key** (`ollama_cloud` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:235-243`; `src/lib/i18n/locales/en-US/translation.json:2678`) | API key for Ollama Cloud web search | Used by the `ollama_cloud` engine (`backend/open_webui/routers/retrieval.py:2521`); seeded from `OLLAMA_CLOUD_API_KEY`, not from its field name (section 4.1) |
| `web.search.searxng_query_url` | `SEARXNG_QUERY_URL` (`backend/open_webui/config.py:1217`) | empty | Web Search › Search › **Searxng Query URL** (`searxng` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:291-300`; `src/lib/i18n/locales/en-US/translation.json:2693`) | SearXNG query address | Used by the `searxng` engine (`backend/open_webui/routers/retrieval.py:2543`); required on the screen for this engine |
| `web.search.searxng_language` | `SEARXNG_LANGUAGE` (`backend/open_webui/config.py:1220`) | `all` | Web Search › Search › **Searxng search language (all, en, es, de, fr, etc.)** (`searxng` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:309-318`; `src/lib/i18n/locales/en-US/translation.json:2694`) | SearXNG search language | Used by the `searxng` engine (`backend/open_webui/routers/retrieval.py:2543`) |
| `web.search.openserp_base_url` | `OPENSERP_BASE_URL` (`backend/open_webui/config.py:1218`) | `http://localhost:7000` | Web Search › Search › **OpenSERP URL** (`openserp` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:1085-1093`; `src/lib/i18n/locales/en-US/translation.json:2679`) | OpenSERP address | Used by the `openserp` engine (`backend/open_webui/routers/retrieval.py:2555`) |
| `web.search.yacy_query_url` | `YACY_QUERY_URL` (`backend/open_webui/config.py:1222`) | empty | Web Search › Search › **Yacy Instance URL** (`yacy` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:330-339`; `src/lib/i18n/locales/en-US/translation.json:2725`) | YaCy instance address | Used by the `yacy` engine (`backend/open_webui/routers/retrieval.py:2565`) |
| `web.search.yacy_username` | `YACY_USERNAME` (`backend/open_webui/config.py:1224`) | empty | Web Search › Search › **Yacy Username** (`yacy` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:350-356`; `src/lib/i18n/locales/en-US/translation.json:2727`) | YaCy user name | Used by the `yacy` engine (`backend/open_webui/routers/retrieval.py:2565`) |
| `web.search.yacy_password` | `YACY_PASSWORD` (`backend/open_webui/config.py:1226`) | secret (set per environment); empty in code | Web Search › Search › **Yacy Password** (`yacy` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:363-369`; `src/lib/i18n/locales/en-US/translation.json:2726`) | YaCy password | Used by the `yacy` engine (`backend/open_webui/routers/retrieval.py:2565`) |
| `web.search.google_pse_api_key` | `GOOGLE_PSE_API_KEY` (`backend/open_webui/config.py:1228`) | secret (set per environment); empty in code | Web Search › Search › **Google PSE API Key** (`google_pse` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:378-384`; `src/lib/i18n/locales/en-US/translation.json:2666`) | Google Programmable Search API key | Used by the `google_pse` engine (`backend/open_webui/routers/retrieval.py:2578`) |
| `web.search.google_pse_engine_id` | `GOOGLE_PSE_ENGINE_ID` (`backend/open_webui/config.py:1230`) | empty | Web Search › Search › **Google PSE Engine Id** (`google_pse` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:389-398`; `src/lib/i18n/locales/en-US/translation.json:2667`) | Google Programmable Search engine ID | Used by the `google_pse` engine (`backend/open_webui/routers/retrieval.py:2578`) |
| `web.search.brave_search_api_key` | `BRAVE_SEARCH_API_KEY` (`backend/open_webui/config.py:1232`) | secret (set per environment); empty in code | Web Search › Search › **Brave Search API Key** (`brave` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:409-415`; `src/lib/i18n/locales/en-US/translation.json:2645`) | Brave Search API key | Used by the `brave` engine (`backend/open_webui/routers/retrieval.py:2590`); the same key serves `brave_llm_context` (`backend/open_webui/routers/retrieval.py:2600`) |
| `web.search.brave_search_context_tokens` | `BRAVE_SEARCH_CONTEXT_TOKENS` (`backend/open_webui/config.py:1234`) | `8192` | Web Search › Search › **Context Tokens** (`brave_llm_context` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:434-446`; `src/lib/i18n/locales/en-US/translation.json:2652`) | Context size requested from Brave LLM Context | Used by the `brave_llm_context` engine (`backend/open_webui/routers/retrieval.py:2600`); the only web field kept when a request leaves it out (`backend/open_webui/routers/retrieval.py:1337-1338`) |
| `web.search.kagi_search_api_key` | `KAGI_SEARCH_API_KEY` (`backend/open_webui/config.py:1236`) | secret (set per environment); empty in code | Web Search › Search › **Kagi Search API Key** (`kagi` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:457-463`; `src/lib/i18n/locales/en-US/translation.json:2670`) | Kagi Search API key | Used by the `kagi` engine (`backend/open_webui/routers/retrieval.py:2612`) |
| `web.search.mojeek_search_api_key` | `MOJEEK_SEARCH_API_KEY` (`backend/open_webui/config.py:1238`) | secret (set per environment); empty in code | Web Search › Search › **Mojeek Search API Key** (`mojeek` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:471-477`; `src/lib/i18n/locales/en-US/translation.json:2677`) | Mojeek Search API key | Used by the `mojeek` engine (`backend/open_webui/routers/retrieval.py:2623`) |
| `web.search.bocha_search_api_key` | `BOCHA_SEARCH_API_KEY` (`backend/open_webui/config.py:1240`) | secret (set per environment); empty in code | Web Search › Search › **Bocha Search API Key** (`bocha` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:485-491`; `src/lib/i18n/locales/en-US/translation.json:2644`) | Bocha Search API key | Used by the `bocha` engine (`backend/open_webui/routers/retrieval.py:2634`) |
| `web.search.serpstack_api_key` | `SERPSTACK_API_KEY` (`backend/open_webui/config.py:1242`) | secret (set per environment); empty in code | Web Search › Search › **Serpstack API Key** (`serpstack` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:499-505`; `src/lib/i18n/locales/en-US/translation.json:2703`) | Serpstack API key | Used by the `serpstack` engine (`backend/open_webui/routers/retrieval.py:2645`) |
| `web.search.serpstack_https` | `SERPSTACK_HTTPS` (`backend/open_webui/config.py:1244`) | on | none (API or import only) | Whether Serpstack is called over HTTPS | No field on the screen; the screen sends back the value it loaded, so only an import or a direct API call changes it (`backend/open_webui/routers/retrieval.py:737`, `:1343`; `backend/open_webui/routers/retrieval.py:2645`) |
| `web.search.serper_api_key` | `SERPER_API_KEY` (`backend/open_webui/config.py:1246`) | secret (set per environment); empty in code | Web Search › Search › **Serper API Key** (`serper` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:513-519`; `src/lib/i18n/locales/en-US/translation.json:2699`) | Serper API key | Used by the `serper` engine (`backend/open_webui/routers/retrieval.py:2656`) |
| `web.search.serphouse_api_key` | `SERPHOUSE_API_KEY` (`backend/open_webui/config.py:1250`) | secret (set per environment); empty in code | Web Search › Search › **SERPHouse API Key** (`serphouse` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:527-533`; `src/lib/i18n/locales/en-US/translation.json:2700`) | SERPHouse API key | Used by the `serphouse` engine (`backend/open_webui/routers/retrieval.py:2666`) |
| `web.search.serphouse_domain` | `SERPHOUSE_DOMAIN` (`backend/open_webui/config.py:1252`) | `google.com` | Web Search › Search › **SERPHouse Domain** (`serphouse` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:538-547`; `src/lib/i18n/locales/en-US/translation.json:2701`) | Search domain SERPHouse queries | Used by the `serphouse` engine (`backend/open_webui/routers/retrieval.py:2666`) |
| `web.search.serply_api_key` | `SERPLY_API_KEY` (`backend/open_webui/config.py:1248`) | secret (set per environment); empty in code | Web Search › Search › **Serply API Key** (`serply` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:558-564`; `src/lib/i18n/locales/en-US/translation.json:2702`) | Serply API key | Used by the `serply` engine (`backend/open_webui/routers/retrieval.py:2677`) |
| `web.search.ddgs_backend` | `DDGS_BACKEND` (`backend/open_webui/config.py:1254`) | `auto` | Web Search › Search › **DDGS Backend** (`duckduckgo` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:1106-1111`; `src/lib/i18n/locales/en-US/translation.json:2653`) | Which backend the DDGS library queries (auto, Bing, Brave, DuckDuckGo, Google, Grokipedia, Mojeek, Wikipedia, Yahoo, Yandex) | Used by the `duckduckgo` engine (`backend/open_webui/routers/retrieval.py:2688`); the engine is listed as "DDGS" and disabled in the slim image (`src/lib/components/admin/Settings/WebSearch.svelte:219-220`, `:1102-1122`) |
| `web.search.searchapi_api_key` | `SEARCHAPI_API_KEY` (`backend/open_webui/config.py:1260`) | secret (set per environment); empty in code | Web Search › Search › **SearchApi API Key** (`searchapi` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:630-636`; `src/lib/i18n/locales/en-US/translation.json:2687`) | SearchApi API key | Used by the `searchapi` engine (`backend/open_webui/routers/retrieval.py:2733`) |
| `web.search.searchapi_engine` | `SEARCHAPI_ENGINE` (`backend/open_webui/config.py:1262`) | empty | Web Search › Search › **SearchApi Engine** (`searchapi` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:641-650`; `src/lib/i18n/locales/en-US/translation.json:2688`) | SearchApi engine name | Used by the `searchapi` engine (`backend/open_webui/routers/retrieval.py:2733`) |
| `web.search.serpapi_api_key` | `SERPAPI_API_KEY` (`backend/open_webui/config.py:1264`) | secret (set per environment); empty in code | Web Search › Search › **SerpApi API Key** (`serpapi` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:661-667`; `src/lib/i18n/locales/en-US/translation.json:2697`) | SerpApi API key | Used by the `serpapi` engine (`backend/open_webui/routers/retrieval.py:2745`) |
| `web.search.serpapi_engine` | `SERPAPI_ENGINE` (`backend/open_webui/config.py:1266`) | empty | Web Search › Search › **SerpApi Engine** (`serpapi` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:672-681`; `src/lib/i18n/locales/en-US/translation.json:2698`) | SerpApi engine name | Used by the `serpapi` engine (`backend/open_webui/routers/retrieval.py:2745`) |
| `web.search.jina_api_key` | `JINA_API_KEY` (`backend/open_webui/config.py:1256`) | secret (set per environment); empty in code | Web Search › Search › **Jina API Key** (`jina` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:710-716`; `src/lib/i18n/locales/en-US/translation.json:2669`) | Jina Search API key | Used by the `jina` engine (`backend/open_webui/routers/retrieval.py:2757`) |
| `web.search.jina_api_base_url` | `JINA_API_BASE_URL` (`backend/open_webui/config.py:1258`) | empty | Web Search › Search › **Jina API Base URL** (`jina` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:692-701`; `src/lib/i18n/locales/en-US/translation.json:2668`) | Jina Search address | Used by the `jina` engine (`backend/open_webui/routers/retrieval.py:2757`) |
| `web.search.bing_search_v7_endpoint` | `BING_SEARCH_V7_ENDPOINT` (`backend/open_webui/config.py:1268`) | `https://api.bing.microsoft.com/v7.0/search` | Web Search › Search › **Bing Search V7 Endpoint** (`bing` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:724-733`; `src/lib/i18n/locales/en-US/translation.json:2642`) | Bing Search v7 endpoint | Used by the `bing` engine (`backend/open_webui/routers/retrieval.py:2765`) |
| `web.search.bing_search_v7_subscription_key` | `BING_SEARCH_V7_SUBSCRIPTION_KEY` (`backend/open_webui/config.py:1270`) | secret (set per environment); empty in code | Web Search › Search › **Bing Search V7 Subscription Key** (`bing` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:742-748`; `src/lib/i18n/locales/en-US/translation.json:2643`) | Bing Search v7 subscription key | Used by the `bing` engine (`backend/open_webui/routers/retrieval.py:2765`) |
| `web.search.azure_ai_search_api_key` | `AZURE_AI_SEARCH_API_KEY` (`backend/open_webui/config.py:1272`) | secret (set per environment); empty in code | none (API or import only) | Azure AI Search API key | **No save path** (section 4). Used by the `azure` engine, which the screen does not offer (`src/lib/components/admin/Settings/WebSearch.svelte:20-52`; `backend/open_webui/routers/retrieval.py:2775-2789`) |
| `web.search.azure_ai_search_endpoint` | `AZURE_AI_SEARCH_ENDPOINT` (`backend/open_webui/config.py:1274`) | empty | none (API or import only) | Azure AI Search endpoint | **No save path**; `azure` engine only (`backend/open_webui/routers/retrieval.py:2775-2789`) |
| `web.search.azure_ai_search_index_name` | `AZURE_AI_SEARCH_INDEX_NAME` (`backend/open_webui/config.py:1276`) | empty | none (API or import only) | Azure AI Search index name | **No save path**; `azure` engine only (`backend/open_webui/routers/retrieval.py:2775-2789`) |
| `web.search.exa_api_key` | `EXA_API_KEY` (`backend/open_webui/config.py:1278`) | secret (set per environment); empty in code | Web Search › Search › **Exa API Key** (`exa` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:756-762`; `src/lib/i18n/locales/en-US/translation.json:2656`) | Exa API key | Used by the `exa` engine (`backend/open_webui/routers/retrieval.py:2721`) |
| `web.search.exa_max_content_length` | `EXA_MAX_CONTENT_LENGTH` (`backend/open_webui/config.py:1279`) | `null` (no limit) | Web Search › Search › **Max Content Length** (`exa` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:767-778`; `src/lib/i18n/locales/en-US/translation.json:2674`) | Most characters kept per Exa result | Must be a whole number above 0: the screen refuses 0 (`backend/open_webui/routers/retrieval.py:839`), and a seeding value of 0 or less **stops the server from starting** (`backend/open_webui/config.py:1279-1281`) |
| `web.search.perplexity_api_key` | `PERPLEXITY_API_KEY` (`backend/open_webui/config.py:1283`) | secret (set per environment); empty in code | Web Search › Search › **Perplexity API Key** (`perplexity` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:786-792`; `src/lib/i18n/locales/en-US/translation.json:2681`) | Perplexity API key | Used by the `perplexity` engine (`backend/open_webui/routers/retrieval.py:2790`); the same key serves `perplexity_search` (`backend/open_webui/routers/retrieval.py:2530`) |
| `web.search.perplexity_model` | `PERPLEXITY_MODEL` (`backend/open_webui/config.py:1285`) | `sonar` | Web Search › Search › **Perplexity Model** (`perplexity` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:800-805`; `src/lib/i18n/locales/en-US/translation.json:2682`) | Perplexity model | Used by the `perplexity` engine (`backend/open_webui/routers/retrieval.py:2790`) |
| `web.search.perplexity_search_context_usage` | `PERPLEXITY_SEARCH_CONTEXT_USAGE` (`backend/open_webui/config.py:1287`) | `medium` | Web Search › Search › **Perplexity Search Context Usage** (`perplexity` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:821-824`; `src/lib/i18n/locales/en-US/translation.json:2684`) | How much search context Perplexity uses | Used by the `perplexity` engine (`backend/open_webui/routers/retrieval.py:2790`) |
| `web.search.perplexity_search_api_url` | `PERPLEXITY_SEARCH_API_URL` (`backend/open_webui/config.py:1289`) | `https://api.perplexity.ai/search` | Web Search › Search › **Perplexity Search API URL** (`perplexity_search` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:253-262`; `src/lib/i18n/locales/en-US/translation.json:2683`) | Perplexity Search API address | Used by the `perplexity_search` engine (`backend/open_webui/routers/retrieval.py:2530`) |
| `web.search.microsoft_web_iq_api_base_url` | `MICROSOFT_WEB_IQ_API_BASE_URL` (`backend/open_webui/config.py:1291`) | `https://api.microsoft.ai/v3` | Web Search › Search › **Microsoft Web IQ API Base URL** (`microsoft_web_iq` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:837-846`; `src/lib/i18n/locales/en-US/translation.json:2675`) | Microsoft Web IQ address | Used by the `microsoft_web_iq` engine (`backend/open_webui/routers/retrieval.py:2800`); also used by the `microsoft_web_iq` web loader, where the screen shows it again (`src/lib/components/admin/Settings/WebSearch.svelte:1372-1416`; `backend/open_webui/retrieval/utils.py:98`) |
| `web.search.microsoft_web_iq_api_key` | `MICROSOFT_WEB_IQ_API_KEY` (`backend/open_webui/config.py:1293`) | secret (set per environment); empty in code | Web Search › Search › **Microsoft Web IQ API Key** (`microsoft_web_iq` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:855-861`; `src/lib/i18n/locales/en-US/translation.json:2676`) | Microsoft Web IQ API key | Used by the `microsoft_web_iq` engine (`backend/open_webui/routers/retrieval.py:2800`); also used by the web loader (`backend/open_webui/retrieval/utils.py:99`) |
| `web.search.microsoft_web_iq_language` | `MICROSOFT_WEB_IQ_LANGUAGE` (`backend/open_webui/config.py:1295`) | `en` | Web Search › Search › **Language** (`microsoft_web_iq` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:867-874`; `src/lib/i18n/locales/en-US/translation.json:2671`) | Microsoft Web IQ language | Used by the `microsoft_web_iq` engine (`backend/open_webui/routers/retrieval.py:2800`); also used by the web loader (`backend/open_webui/retrieval/utils.py:100`) |
| `web.search.sougou_api_sid` | `SOUGOU_API_SID` (`backend/open_webui/config.py:1297`) | secret (set per environment); empty in code | Web Search › Search › **Sougou Search API sID** (`sougou` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:883-889`; `src/lib/i18n/locales/en-US/translation.json:2704`) | Sogou search API ID (credential) | Used by the `sougou` engine (`backend/open_webui/routers/retrieval.py:2814`) |
| `web.search.sougou_api_sk` | `SOUGOU_API_SK` (`backend/open_webui/config.py:1299`) | secret (set per environment); empty in code | Web Search › Search › **Sougou Search API SK** (`sougou` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:896-902`; `src/lib/i18n/locales/en-US/translation.json:2705`) | Sogou search API secret key | Used by the `sougou` engine (`backend/open_webui/routers/retrieval.py:2814`) |
| `web.search.tavily_api_key` | `TAVILY_API_KEY` (`backend/open_webui/config.py:1301`) | secret (set per environment); empty in code | Web Search › Search › **Tavily API Key** (`tavily` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:572-578`; `src/lib/i18n/locales/en-US/translation.json:2706`) | Tavily API key | Used by the `tavily` engine (`backend/open_webui/routers/retrieval.py:2697`); also used by the `tavily` web loader (`backend/open_webui/retrieval/utils.py:96`) |
| `web.search.tavily_extract_depth` | `TAVILY_EXTRACT_DEPTH` (`backend/open_webui/config.py:1303`) | `basic` | Web Search › Loader › **Tavily Extract Depth** (`tavily` web loader) (`src/lib/components/admin/Settings/WebSearch.svelte:1342-1351`; `src/lib/i18n/locales/en-US/translation.json:2707`) | How deeply Tavily extracts page content | Read by the web loader, not the search (`backend/open_webui/retrieval/utils.py:97`) |
| `web.search.staan_api_key` | `STAAN_API_KEY` (`backend/open_webui/config.py:1305`) | secret (set per environment); empty in code | Web Search › Search › **Staan API Key** (`staan` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:586-592`; `src/lib/i18n/locales/en-US/translation.json:3123`) | Staan API key | Used by the `staan` engine (`backend/open_webui/routers/retrieval.py:2708`) |
| `web.search.staan_market` | `STAAN_MARKET` (`backend/open_webui/config.py:1307`) | `en-us` | Web Search › Search › **Market** (`staan` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:597-605`; `src/lib/i18n/locales/en-US/translation.json:1312`) | Region and language of Staan results | Used by the `staan` engine (`backend/open_webui/routers/retrieval.py:2708`) |
| `web.search.staan_max_snippets` | `STAAN_MAX_SNIPPETS` (`backend/open_webui/config.py:1309`) | `0` | Web Search › Search › **Max Snippets** (`staan` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:610-622`; `src/lib/i18n/locales/en-US/translation.json:1315`) | Most snippets per Staan result | Used by the `staan` engine (`backend/open_webui/routers/retrieval.py:2708`) |
| `web.search.external_web_search_url` | `EXTERNAL_WEB_SEARCH_URL` (`backend/open_webui/config.py:1321`) | empty | Web Search › Search › **External Web Search URL** (`external` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:960-969`; `src/lib/i18n/locales/en-US/translation.json:2660`) | Address of an external search service | Used by the `external` engine (`backend/open_webui/routers/retrieval.py:2835`) |
| `web.search.external_web_search_api_key` | `EXTERNAL_WEB_SEARCH_API_KEY` (`backend/open_webui/config.py:1323`) | secret (set per environment); empty in code | Web Search › Search › **External Web Search API Key** (`external` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:978-984`; `src/lib/i18n/locales/en-US/translation.json:2659`) | API key for the external search service | Used by the `external` engine (`backend/open_webui/routers/retrieval.py:2835`) |
| `web.search.yandex_web_search_url` | `YANDEX_WEB_SEARCH_URL` (`backend/open_webui/config.py:1329`) | empty | Web Search › Search › **Yandex Web Search URL** (`yandex` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:992-1001`; `src/lib/i18n/locales/en-US/translation.json:2730`) | Yandex search address | Used by the `yandex` engine (`backend/open_webui/routers/retrieval.py:2846`) |
| `web.search.yandex_web_search_api_key` | `YANDEX_WEB_SEARCH_API_KEY` (`backend/open_webui/config.py:1331`) | secret (set per environment); empty in code | Web Search › Search › **Yandex Web Search API Key** (`yandex` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:1010-1016`; `src/lib/i18n/locales/en-US/translation.json:2728`) | Yandex search API key | Used by the `yandex` engine (`backend/open_webui/routers/retrieval.py:2846`) |
| `web.search.yandex_web_search_config` | `YANDEX_WEB_SEARCH_CONFIG` (`backend/open_webui/config.py:1333`) | empty (treated as `{}`) | Web Search › Search › **Yandex Web Search config** (`yandex` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:1022-1033`; `src/lib/i18n/locales/en-US/translation.json:2729`) | Extra Yandex request settings as JSON text | Used by the `yandex` engine (`backend/open_webui/routers/retrieval.py:2846`); parsed as JSON at each search (`backend/open_webui/retrieval/web/yandex.py:58`) |
| `web.search.youcom_api_key` | `YOUCOM_API_KEY`, then `YDC_API_KEY` (`backend/open_webui/config.py:1335`) | secret (set per environment); empty in code | Web Search › Search › **You.com API Key** (`youcom` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:1045-1051`; `src/lib/i18n/locales/en-US/translation.json:2731`) | You.com API key | Used by the `youcom` engine (`backend/open_webui/routers/retrieval.py:2858`); seeded from `YOUCOM_API_KEY`, then `YDC_API_KEY` |
| `web.search.linkup_api_key` | `LINKUP_API_KEY` (`backend/open_webui/config.py:1337`) | secret (set per environment); empty in code | Web Search › Search › **Linkup API Key** (`linkup` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:1059-1065`; `src/lib/i18n/locales/en-US/translation.json:2672`) | Linkup API key | Used by the `linkup` engine (`backend/open_webui/routers/retrieval.py:2866`) |
| `web.search.linkup_search_params` | `LINKUP_SEARCH_PARAMS` (`backend/open_webui/config.py:1339-1345`) | `{}` (invalid JSON becomes `{}`) | Web Search › Search › **Parameters** (`linkup` engine) (`src/lib/components/admin/Settings/WebSearch.svelte:1071-1076`; `src/lib/i18n/locales/en-US/translation.json:2680`) | Extra Linkup search parameters as a JSON object | Used by the `linkup` engine (`backend/open_webui/routers/retrieval.py:2866`); folded object key (section 4); invalid JSON on the screen stops the save without a message ([`web-search-and-web-loading.md`](web-search-and-web-loading.md) 7.7) |

### 7.7 `web.loader` and `web.fetch`: Page Loading (12 Keys)

Area document: [`web-search-and-web-loading.md`](web-search-and-web-loading.md) section 7.2. The loader reads its keys through `LOADER_CONFIG_KEYS` for each set of pages (`backend/open_webui/retrieval/utils.py:86-102`). **Exception to "the stored value wins":** when one of these loader keys is stored as JSON `null`, the loader uses the environment value instead (`backend/open_webui/retrieval/web/utils.py:1065-1068`).

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `web.fetch.max_content_length` | `WEB_FETCH_MAX_CONTENT_LENGTH` (`backend/open_webui/config.py:1198-1200`) | `null` (no limit) | Web Search › Search › **Fetch URL Content Length Limit** (while web search is on) (`src/lib/components/admin/Settings/WebSearch.svelte:1171-1177`; `src/lib/i18n/locales/en-US/translation.json:2662`) | Most characters returned when a model fetches a web page with the URL-fetch tool | Read at each fetch (`backend/open_webui/tools/builtin.py:350-353`) |
| `web.loader.engine` | `WEB_LOADER_ENGINE` (`backend/open_webui/config.py:1202`) | empty: the built-in safe loader | Web Search › Loader › **Web Loader Engine** (`src/lib/components/admin/Settings/WebSearch.svelte:1231-1235`; `src/lib/i18n/locales/en-US/translation.json:2716`) | How result pages are fetched: built-in (empty or `safe_web`), `playwright`, `firecrawl`, `tavily`, `microsoft_web_iq` or `external` | Read at each page load; a stored `null` falls back to the environment value (`backend/open_webui/retrieval/web/utils.py:1065-1068`); an unknown name fails every load (`backend/open_webui/retrieval/web/utils.py:1148-1152`); the slim image refuses Playwright (`backend/open_webui/routers/retrieval.py:976-983`) |
| `web.loader.concurrent_requests` | `WEB_LOADER_CONCURRENT_REQUESTS` (`backend/open_webui/config.py:1205`) | `10` | Web Search › Loader › **Concurrent Requests** (`src/lib/components/admin/Settings/WebSearch.svelte:1455-1461`; `src/lib/i18n/locales/en-US/translation.json:2651`) | Cap on pages fetched in parallel | `backend/open_webui/retrieval/utils.py:87` |
| `web.loader.timeout` | `WEB_LOADER_TIMEOUT` (`backend/open_webui/config.py:1207`) | empty (no timeout), stored as text | Web Search › Loader › **Timeout** (built-in loader) (`src/lib/components/admin/Settings/WebSearch.svelte:1249-1255`; `src/lib/i18n/locales/en-US/translation.json:2709`) | Longest wait per page, in seconds | A value that is not a number is ignored (`backend/open_webui/retrieval/web/utils.py:1086-1094`); a stored `null` falls back to the environment value (`backend/open_webui/retrieval/web/utils.py:1065-1068`) |
| `web.loader.ssl_verification` | `ENABLE_WEB_LOADER_SSL_VERIFICATION` (`backend/open_webui/config.py:1210`) | on | Web Search › Loader › **Verify SSL Certificate** (built-in loader) (`src/lib/components/admin/Settings/WebSearch.svelte:1260-1265`; `src/lib/i18n/locales/en-US/translation.json:2714`) | Checks certificates of fetched pages | `backend/open_webui/retrieval/utils.py:86` |
| `web.loader.playwright_ws_url` | `PLAYWRIGHT_WS_URL` (`backend/open_webui/config.py:1311`) | empty | Web Search › Loader › **Playwright WebSocket URL** (`playwright` loader) (`src/lib/components/admin/Settings/WebSearch.svelte:1273-1282`; `src/lib/i18n/locales/en-US/translation.json:2686`) | Address of a remote Playwright browser service | `backend/open_webui/retrieval/web/utils.py:1099-1105`; a stored `null` falls back to the environment value (`backend/open_webui/retrieval/web/utils.py:1065-1068`) |
| `web.loader.playwright_timeout` | `PLAYWRIGHT_TIMEOUT` (`backend/open_webui/config.py:1313`) | `10000` (milliseconds) | Web Search › Loader › **Playwright Timeout (ms)** (`playwright` loader) (`src/lib/components/admin/Settings/WebSearch.svelte:1291-1299`; `src/lib/i18n/locales/en-US/translation.json:2685`) | Playwright page timeout | `backend/open_webui/retrieval/web/utils.py:1101` |
| `web.loader.firecrawl_api_key` | `FIRECRAWL_API_KEY` (`backend/open_webui/config.py:1315`) | secret (set per environment); empty in code | Web Search › Loader › **Firecrawl API Key** (`firecrawl` loader) (`src/lib/components/admin/Settings/WebSearch.svelte:1328-1334`; `src/lib/i18n/locales/en-US/translation.json:2664`) | Firecrawl API key | Also used by the `firecrawl` search engine, where the screen shows it in the Search section (`src/lib/components/admin/Settings/WebSearch.svelte:906-951`; `backend/open_webui/routers/retrieval.py:2826`) |
| `web.loader.firecrawl_api_url` | `FIRECRAWL_API_BASE_URL` (`backend/open_webui/config.py:1317`) | `https://api.firecrawl.dev` | Web Search › Loader › **Firecrawl API Base URL** (`firecrawl` loader) (`src/lib/components/admin/Settings/WebSearch.svelte:1310-1319`; `src/lib/i18n/locales/en-US/translation.json:2663`) | Firecrawl address | Seeded from `FIRECRAWL_API_BASE_URL`; also used by the `firecrawl` search engine |
| `web.loader.firecrawl_timeout` | `FIRECRAWL_TIMEOUT` (`backend/open_webui/config.py:1319`) | empty, stored as text | Web Search › Search › **Firecrawl Timeout (s)** (`firecrawl` search engine) (`src/lib/components/admin/Settings/WebSearch.svelte:940-949`; `src/lib/i18n/locales/en-US/translation.json:2665`) | Firecrawl timeout, in seconds | The field appears only in the Search section; the screen converts the number to text before saving (`src/lib/components/admin/Settings/WebSearch.svelte:87-89`; `backend/open_webui/retrieval/web/utils.py:1110`) |
| `web.loader.external_web_loader_url` | `EXTERNAL_WEB_LOADER_URL` (`backend/open_webui/config.py:1325`) | empty | Web Search › Loader › **External Web Loader URL** (`external` loader) (`src/lib/components/admin/Settings/WebSearch.svelte:1424-1433`; `src/lib/i18n/locales/en-US/translation.json:2658`) | Address of an external page loader | `backend/open_webui/retrieval/web/utils.py:1133-1136` |
| `web.loader.external_web_loader_api_key` | `EXTERNAL_WEB_LOADER_API_KEY` (`backend/open_webui/config.py:1327`) | secret (set per environment); empty in code | Web Search › Loader › **External Web Loader API Key** (`external` loader) (`src/lib/components/admin/Settings/WebSearch.svelte:1442-1448`; `src/lib/i18n/locales/en-US/translation.json:2657`) | API key for the external page loader |  |

### 7.8 `task`: Background Generation Tasks (19 Keys)

Area document: [`chat-completion-pipeline-and-generation-tasks.md`](chat-completion-pipeline-and-generation-tasks.md) sections 7.1 and 7.3; screen detail in [`admin-settings-panels.md`](admin-settings-panels.md) section 7.2. All 19 keys are saved together by **Interface** through `POST /api/v1/tasks/config/update` (section 5.5) and are read from the store each time a task runs. Every field name equals its seeding variable (`backend/open_webui/routers/tasks.py:41-61`).

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `task.model.default` | `TASK_MODEL` (`backend/open_webui/config.py:2180`) | empty: the chat's own model | Interface › Tasks › **Local Task Model** (`src/lib/components/admin/Settings/Interface.svelte:188-190`; `src/lib/i18n/locales/en-US/translation.json:2504`) | Model that runs background tasks when the chat uses a local (Ollama) model | Ignored unless the named model exists (`backend/open_webui/utils/task.py:16-27`) |
| `task.model.external` | `TASK_MODEL_EXTERNAL` (`backend/open_webui/config.py:2182`) | empty: the chat's own model | Interface › Tasks › **External Task Model** (`src/lib/components/admin/Settings/Interface.svelte:207-209`; `src/lib/i18n/locales/en-US/translation.json:2497`) | Model that runs background tasks when the chat uses any other connection | Ignored unless the named model exists (`backend/open_webui/utils/task.py:16-27`) |
| `task.model.params` | `TASK_MODEL_PARAMS` (`backend/open_webui/config.py:2185-2190`) | `{}` (invalid JSON becomes `{}`) | Interface › Tasks › **Task Model Parameters** (`src/lib/components/admin/Settings/Interface.svelte:238-250`; `src/lib/i18n/locales/en-US/translation.json:2522`) | Model parameters (for example temperature) applied to task requests | Empty values are dropped before use (`backend/open_webui/routers/tasks.py:80-98`); folded object key (section 4) |
| `task.title.enable` | `ENABLE_TITLE_GENERATION` (`backend/open_webui/config.py:2299`) | on | Interface › Generation › **Title Generation** (`src/lib/components/admin/Settings/Interface.svelte:369-373`; `src/lib/i18n/locales/en-US/translation.json:2525`) | Generates chat titles | `backend/open_webui/routers/tasks.py:143` |
| `task.title.prompt_template` | `TITLE_GENERATION_PROMPT_TEMPLATE` (`backend/open_webui/config.py:2209`) | empty: the built-in template | Interface › Generation › **Title Generation Prompt** (title generation on) (`src/lib/components/admin/Settings/Interface.svelte:378-383`; `src/lib/i18n/locales/en-US/translation.json:2527`) | Prompt used to generate titles | `backend/open_webui/routers/tasks.py:173-177` |
| `task.voice.prompt.enable` | `ENABLE_VOICE_MODE_PROMPT` (`backend/open_webui/config.py:2385`) | on | Interface › Generation › **Voice Mode Prompt** (`src/lib/components/admin/Settings/Interface.svelte:392-396`; `src/lib/i18n/locales/en-US/translation.json:2537`) | Adds the voice-mode system prompt to chats held in voice mode | `backend/open_webui/utils/middleware.py:2674-2682` |
| `task.voice.prompt_template` | `VOICE_MODE_PROMPT_TEMPLATE` (`backend/open_webui/config.py:2383`) | empty: the built-in template | Interface › Generation › **Prompt Template** (voice mode prompt on) (`src/lib/components/admin/Settings/Interface.svelte:401-406`; `src/lib/i18n/locales/en-US/translation.json:2506`) | The voice-mode system prompt | `backend/open_webui/utils/middleware.py:2677-2679` |
| `task.follow_up.enable` | `ENABLE_FOLLOW_UP_GENERATION` (`backend/open_webui/config.py:2295`) | on | Interface › Generation › **Follow Up Generation** (`src/lib/components/admin/Settings/Interface.svelte:415-419`; `src/lib/i18n/locales/en-US/translation.json:2499`) | Suggests follow-up questions after answers | `backend/open_webui/routers/tasks.py:216` |
| `task.follow_up.prompt_template` | `FOLLOW_UP_GENERATION_PROMPT_TEMPLATE` (`backend/open_webui/config.py:2277`) | empty: the built-in template | Interface › Generation › **Follow Up Generation Prompt** (follow-up generation on) (`src/lib/components/admin/Settings/Interface.svelte:424-429`; `src/lib/i18n/locales/en-US/translation.json:2501`) | Prompt used for follow-up suggestions | `backend/open_webui/routers/tasks.py:241-245` |
| `task.tags.enable` | `ENABLE_TAGS_GENERATION` (`backend/open_webui/config.py:2297`) | on | Interface › Generation › **Tags Generation** (`src/lib/components/admin/Settings/Interface.svelte:438-442`; `src/lib/i18n/locales/en-US/translation.json:2517`) | Generates chat tags | `backend/open_webui/routers/tasks.py:281` |
| `task.tags.prompt_template` | `TAGS_GENERATION_PROMPT_TEMPLATE` (`backend/open_webui/config.py:2234`) | empty: the built-in template | Interface › Generation › **Tags Generation Prompt** (tags generation on) (`src/lib/components/admin/Settings/Interface.svelte:447-452`; `src/lib/i18n/locales/en-US/translation.json:2519`) | Prompt used for tags | `backend/open_webui/routers/tasks.py:306-310` |
| `task.query.retrieval.enable` | `ENABLE_RETRIEVAL_QUERY_GENERATION` (`backend/open_webui/config.py:2304`) | on | Interface › Generation › **Retrieval Query Generation** (`src/lib/components/admin/Settings/Interface.svelte:461-466`; `src/lib/i18n/locales/en-US/translation.json:2512`) | Lets a model write the search queries used for knowledge retrieval | `backend/open_webui/routers/tasks.py:413` |
| `task.query.search.enable` | `ENABLE_SEARCH_QUERY_GENERATION` (`backend/open_webui/config.py:2302`) | on | Interface › Generation › **Web Search Query Generation** (`src/lib/components/admin/Settings/Interface.svelte:472-477`; `src/lib/i18n/locales/en-US/translation.json:2539`) | Lets a model write the web-search queries | `backend/open_webui/routers/tasks.py:407` |
| `task.query.prompt_template` | `QUERY_GENERATION_PROMPT_TEMPLATE` (`backend/open_webui/config.py:2307`) | empty: the built-in template | Interface › Generation › **Query Generation Prompt** (`src/lib/components/admin/Settings/Interface.svelte:483-488`; `src/lib/i18n/locales/en-US/translation.json:2508`) | Prompt used to write those queries | `backend/open_webui/routers/tasks.py:442-446` |
| `task.autocomplete.enable` | `ENABLE_AUTOCOMPLETE_GENERATION` (`backend/open_webui/config.py:2333`) | off | Interface › Generation › **Autocomplete Generation** (`src/lib/components/admin/Settings/Interface.svelte:494-499`; `src/lib/i18n/locales/en-US/translation.json:2485`) | Suggests completions while users type | Sent to browsers through `/api/config`, so open pages need a reload (`backend/open_webui/main.py:2368`; `backend/open_webui/routers/tasks.py:481`) |
| `task.autocomplete.input_max_length` | `AUTOCOMPLETE_GENERATION_INPUT_MAX_LENGTH` (`backend/open_webui/config.py:2335`) | `-1` (no limit) | Interface › Generation › **Autocomplete Generation Input Max Length** (autocomplete on) (`src/lib/components/admin/Settings/Interface.svelte:506-516`; `src/lib/i18n/locales/en-US/translation.json:2487`) | Longest input, in characters, that is sent for autocompletion | Longer input is refused with HTTP 400 (`backend/open_webui/routers/tasks.py:491-497`) |
| `task.autocomplete.prompt_template` | `AUTOCOMPLETE_GENERATION_PROMPT_TEMPLATE` (`backend/open_webui/config.py:2337`) | empty: the built-in template | Interface › Generation › **Autocomplete Generation Prompt** (autocomplete on) (`src/lib/components/admin/Settings/Interface.svelte:522-529`; `src/lib/i18n/locales/en-US/translation.json:2489`) | Prompt used for autocompletion | `backend/open_webui/routers/tasks.py:518-522` |
| `task.image.prompt_template` | `IMAGE_PROMPT_GENERATION_PROMPT_TEMPLATE` (`backend/open_webui/config.py:2254`) | empty: the built-in template | Interface › Generation › **Image Prompt Generation Prompt** (`src/lib/components/admin/Settings/Interface.svelte:538-543`; `src/lib/i18n/locales/en-US/translation.json:2503`) | Prompt used to turn a chat into an image-generation prompt | `backend/open_webui/routers/tasks.py:365-369` |
| `task.tools.prompt_template` | `TOOLS_FUNCTION_CALLING_PROMPT_TEMPLATE` (`backend/open_webui/config.py:2412`) | empty: the built-in template | Interface › Generation › **Tools Function Calling Prompt** (`src/lib/components/admin/Settings/Interface.svelte:549-554`; `src/lib/i18n/locales/en-US/translation.json:2535`) | Prompt used for tool calling in the default (non-native) mode | `backend/open_webui/utils/middleware.py:1398-1402` |

### 7.9 `subagents`: Sub-Agents (7 Keys)

Area document: [`chat-completion-pipeline-and-generation-tasks.md`](chat-completion-pipeline-and-generation-tasks.md) section 7.4; screen map in [`admin-settings-panels.md`](admin-settings-panels.md) section 7.5.4. All seven keys are saved together through `POST /api/v1/configs/subagents` (section 5.5) and read each time a sub-agent starts (`backend/open_webui/utils/subagents.py:290-301`). The labels on this screen are in sentence case in the code.

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `subagents.enable` | `ENABLE_SUBAGENTS` (`backend/open_webui/config.py:2036`) | off | Sub-agents › **Enable sub-agents** (`src/lib/components/admin/Settings/Subagents.svelte:71-73`; `src/lib/i18n/locales/en-US/translation.json:2634`) | Offers models the built-in tools that delegate work to sub-agents (`delegate_task`, `timer`) | Checked when the tool list is built for a chat (`backend/open_webui/utils/tools.py:648-654`) |
| `subagents.max_concurrent` | `SUBAGENTS_MAX_CONCURRENT` (`backend/open_webui/config.py:2038`) | `20`; `-1` means unlimited | Sub-agents › **Max concurrent** (sub-agents on) (`src/lib/components/admin/Settings/Subagents.svelte:84-90`; `src/lib/i18n/locales/en-US/translation.json:2636`) | Most sub-agents running at once in the foreground | A stored `0` is treated as 20, other values below 1 as 1 (`backend/open_webui/utils/subagents.py:298-303`); the screen also shows 20 for a stored 0 (`src/lib/components/admin/Settings/Subagents.svelte:26`) |
| `subagents.background_enabled` | `SUBAGENTS_BACKGROUND_ENABLED` (`backend/open_webui/config.py:2037`) | off | Sub-agents › **Enable background sub-agents** (sub-agents on) (`src/lib/components/admin/Settings/Subagents.svelte:103-105`; `src/lib/i18n/locales/en-US/translation.json:2633`) | Lets delegated sub-agents keep running while the chat continues | When off, a background request returns an error text to the model (`backend/open_webui/utils/subagents.py:307-308`) |
| `subagents.max_async` | `SUBAGENTS_MAX_ASYNC` (`backend/open_webui/config.py:2039`) | `20`; `-1` means unlimited | Sub-agents › **Max background** (background sub-agents on) (`src/lib/components/admin/Settings/Subagents.svelte:115-121`; `src/lib/i18n/locales/en-US/translation.json:2635`) | Most background sub-agents running at once | Same `0` and minimum handling as Max concurrent (`backend/open_webui/utils/subagents.py:299-305`, `:364-367`) |
| `subagents.max_iterations` | `SUBAGENTS_MAX_ITERATIONS` (`backend/open_webui/config.py:2040`) | `30` | Sub-agents › **Max iterations** (sub-agents on) (`src/lib/components/admin/Settings/Subagents.svelte:134-140`; `src/lib/i18n/locales/en-US/translation.json:2637`) | Most steps one sub-agent may take | The screen allows 1 to 100 (`src/lib/components/admin/Settings/Subagents.svelte:141-142`); a stored `0` is treated as 30 (`backend/open_webui/utils/subagents.py:300`) |
| `subagents.max_output` | `SUBAGENTS_MAX_OUTPUT` (`backend/open_webui/config.py:2041`) | `30000` | Sub-agents › **Max output** (sub-agents on) (`src/lib/components/admin/Settings/Subagents.svelte:153-159`; `src/lib/i18n/locales/en-US/translation.json:2638`) | Largest result a sub-agent may return, in characters | The screen allows 1,000 to 100,000 (`src/lib/components/admin/Settings/Subagents.svelte:160-161`); a stored `0` is treated as 30,000 (`backend/open_webui/utils/subagents.py:301`) |
| `subagents.system_prompt` | `SUBAGENTS_SYSTEM_PROMPT` (`backend/open_webui/config.py:2042`) | empty: the built-in prompt | Sub-agents › **System prompt** (sub-agents on) (`src/lib/components/admin/Settings/Subagents.svelte:171-175`; `src/lib/i18n/locales/en-US/translation.json:2640`) | System prompt given to sub-agents | `backend/open_webui/utils/subagents.py:454` |

### 7.10 `tool_server` and `terminal_server`: Connection Lists (2 Keys)

Area document: [`workspace-tools-tool-servers-mcp-and-terminals.md`](workspace-tools-tool-servers-mcp-and-terminals.md) section 7.1. Both keys are lists of objects, saved whole by `POST /api/v1/configs/tool_servers` and `POST /api/v1/configs/terminal_servers` (section 5.5). Tool servers that users add for themselves are stored in their own settings (`toolServers`), not here (`src/lib/components/chat/Settings/Integrations.svelte:45`).

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `tool_server.connections` | `TOOL_SERVER_CONNECTIONS`, a JSON list (`backend/open_webui/config.py:381-388`) | `[]`; invalid JSON is logged and becomes `[]` | Integrations › Tools › **External Tool Servers** (`src/lib/components/admin/Settings/Integrations.svelte:189-196`; `src/lib/i18n/locales/en-US/translation.json:2476`, `:2482`) | The admin-configured OpenAPI and MCP tool servers: address, path, type, authentication type, key, headers, access settings (`config`) and server details (`info`) | Holds connection credentials: treat as secret. Read from the store for every chat request (`backend/open_webui/utils/middleware.py:2352`); the fetched server specifications are cached per process and in Redis, refreshed on each save and at start-up (`backend/open_webui/utils/tools.py:1170-1203`; `backend/open_webui/main.py:431-454`). Saving replaces the whole list; adding a connection saves at once (`src/lib/components/admin/Settings/Integrations.svelte:72-88`). Old access lists inside it are migrated at each start (`backend/open_webui/main.py:625-629`) |
| `terminal_server.connections` | `TERMINAL_SERVER_CONNECTIONS`, a JSON list (`backend/open_webui/config.py:396-398`) | `[]`. **Invalid JSON in the variable stops the server from starting**: unlike the tool-server list it is parsed without a fallback | Integrations › Terminal › **Open Terminal** (`src/lib/components/admin/Settings/Integrations.svelte:239-243`; `src/lib/i18n/locales/en-US/translation.json:2479`, `:2481`) | The terminal server connections: address, path, key, authentication type, enabled flag, policy and server type | Holds connection credentials: treat as secret. Read from the store when terminals are listed or used (`backend/open_webui/routers/terminals.py:90`, `:117`); specifications are cached like the tool servers and refreshed on save (`backend/open_webui/utils/tools.py:1271-1354`). At start-up they are prepared only when at least one tool server exists, otherwise on first use (section 5.2) |

### 7.11 `ui`: Sign-Up, Defaults and Interface (20 Keys)

Areas: [`admin-settings-panels.md`](admin-settings-panels.md) (sections 5.3, 6.2, 7.1), [`user-settings-and-personalisation.md`](user-settings-and-personalisation.md) (interface defaults), [`users-groups-roles-and-permissions.md`](users-groups-roles-and-permissions.md) (sign-up, role and group). Twelve of these keys travel through `/api/v1/auths/admin/config`, which **General** and **Authentication** both save in full, so a screen left open in another tab can undo a change ([`admin-settings-panels.md`](admin-settings-panels.md) 5.3). Most `ui` keys reach browsers through `/api/config` (section 2.2), so open pages see a change only after a reload.

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `ui.enable_signup` | `ENABLE_SIGNUP`, then `WEBUI_AUTH` (`backend/open_webui/config.py:1664`) | on; off when `WEBUI_AUTH` is off | Authentication › User Access › **New Sign Ups** (`src/lib/components/admin/Settings/Authentication.svelte:181-185`; `src/lib/i18n/locales/en-US/translation.json:2089`) | Allows new accounts to register themselves | The server refuses sign-up while it or the login form is off and users exist (`backend/open_webui/routers/auths.py:908-911`). Switched off automatically after the first account signs up and after an admin is bootstrapped from the environment (`backend/open_webui/routers/auths.py:874-879`; `backend/open_webui/main.py:377-380`). Public in `/api/config` |
| `ui.enable_login_form` | `ENABLE_LOGIN_FORM` (`backend/open_webui/config.py:1666`) | on | Authentication › User Access › **Login Form** (`src/lib/components/admin/Settings/Authentication.svelte:173-177`; `src/lib/i18n/locales/en-US/translation.json:2085`) | Shows the email and password form on the sign-in page | Hides the form only; the server-side switch for password sign-in is the environment variable `ENABLE_PASSWORD_AUTH` (`knowledgebase/tools/ground-truth.md`). Written only when a save includes it (`backend/open_webui/routers/auths.py:1272-1273`) |
| `ui.enable_password_change_form` | `ENABLE_PASSWORD_CHANGE_FORM` (`backend/open_webui/config.py:1668`) | on | none (API or import only) | Shows the change-password form in personal **Account** settings (only while the login form is also on) | No admin field; seeded once from `ENABLE_PASSWORD_CHANGE_FORM`, so after the first start only an import changes it. Browser-side only (`src/lib/components/chat/Settings/Account.svelte:381`; `backend/open_webui/main.py:2346`) |
| `ui.default_locale` | `DEFAULT_LOCALE` (`backend/open_webui/config.py:1672`) | empty | none (API or import only) | None: **inert row** | Seeded and exportable, but nothing reads the stored key. The default interface language sent to browsers and the language passed to some search engines come from the environment constant `DEFAULT_LOCALE` (`backend/open_webui/main.py:2315`; `backend/open_webui/routers/retrieval.py:2770`), so a change needs a restart with the new environment value |
| `ui.default_models` | `DEFAULT_MODELS` (`backend/open_webui/config.py:1674`) | `null` (none) | Models › model menu › **Set as Selected Model** / **Remove Selected Model** (`src/lib/components/admin/Settings/Models/ModelMenu.svelte:127-129`; `src/lib/i18n/locales/en-US/translation.json:1957`, `:1791`) | Comma-separated model IDs preselected in new chats for users who have not chosen their own | A list stored by an older release is joined into text at start-up (`backend/open_webui/models/config.py:368-375`). Precedence and filtering in the browser: section 11.2 (`src/lib/components/chat/Chat.svelte:2093-2120`). browsers pick up a change on their next reload of `/api/config` |
| `ui.default_pinned_models` | `DEFAULT_PINNED_MODELS` (`backend/open_webui/config.py:1676`) | `null` (none) | Models › model menu › **Set as Pinned Model** / **Remove Pinned Model** (`src/lib/components/admin/Settings/Models/ModelMenu.svelte:146-148`; `src/lib/i18n/locales/en-US/translation.json:1955`) | Comma-separated model IDs pinned in the sidebar by default | Same start-up repair as `ui.default_models`; saved with it (`src/lib/components/admin/Settings/Models.svelte:380-396`) |
| `ui.default_interface_settings` | `DEFAULT_INTERFACE_SETTINGS` (`backend/open_webui/config.py:1713-1718`) | `{}` (invalid JSON, or a value that is not an object, becomes `{}`) | General › UI › **Default Interface Settings** › **Configure** (`src/lib/components/admin/Settings/General.svelte:429-476`; `src/lib/i18n/locales/en-US/translation.json:561`) | Interface settings applied to every account that has not set them itself | Merged under each user's own `ui` settings when they are read; the user's value wins (`backend/open_webui/routers/users.py:57-69`, `:466-474`). Every General or Authentication save writes it, and a save without it stores `{}` (`backend/open_webui/routers/auths.py:1276`). Folded object key (section 4). Detail: [`admin-settings-panels.md`](admin-settings-panels.md) 5.4 |
| `ui.i18n` | none: code default `{}` (`backend/open_webui/config.py:3090`) | `{}` | General › UI › **UI Translations** (`src/lib/components/admin/Settings/General.svelte:420-422`; `src/lib/components/admin/Settings/I18nSettings.svelte:31`; `src/lib/i18n/locales/en-US/translation.json:2407`) | Admin replacements for interface wording, per language | Validated on save: languages and keys must be safe names and placeholders must match (`backend/open_webui/routers/auths.py:1242-1266`); written only when a save includes it (`backend/open_webui/routers/auths.py:1274-1275`). Public in `/api/config` (`backend/open_webui/main.py:2316`). Rules: [`admin-settings-panels.md`](admin-settings-panels.md) 7.4 |
| `ui.prompt_suggestions` | `DEFAULT_PROMPT_SUGGESTIONS` (`backend/open_webui/config.py:1680, :1680-1683`) | `null`: the interface's built-in suggestions; an empty list shows none | Models › Model Defaults › **Prompt Suggestions** (`src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:261`; `src/lib/i18n/locales/en-US/translation.json:2608`) | The prompt suggestions shown on a new chat | "Use default" on the screen stores `null` (`src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:132-136`); seeded from the JSON variable `DEFAULT_PROMPT_SUGGESTIONS` (`backend/open_webui/config.py:1678-1683`). browsers pick up a change on their next reload of `/api/config` |
| `ui.prompt_suggestions_i18n` | none: code default `{}` (`backend/open_webui/config.py:1685`) | `{}` | Models › Model Defaults › **Prompt Suggestions** (per-language versions) (`src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:132-136`) | Translated prompt suggestions per language | Saved with `ui.prompt_suggestions`; `{}` when not sent (`backend/open_webui/routers/configs.py:824-829`) |
| `ui.model_order_list` | `MODEL_ORDER_LIST` (`backend/open_webui/config.py:1688-1693`) | `[]` (invalid JSON is logged and becomes `[]`) | Models › drag handle on each model (tooltip "Drag to reorder"), then save (`src/lib/components/admin/Settings/Models.svelte:981-984`, `:362-367`, `:333-346`) | Order of models in the model lists | Applied when the model list is built (`backend/open_webui/main.py:928-935`); models not in the list follow, by name |
| `ui.default_user_role` | `DEFAULT_USER_ROLE` (`backend/open_webui/config.py:1720`) | `pending` | Authentication › User Access › **Default User Role** (`src/lib/components/admin/Settings/Authentication.svelte:144-148`; `src/lib/i18n/locales/en-US/translation.json:2061`) | Role given to new accounts | A value other than `pending`, `user` or `admin` is silently not saved (`backend/open_webui/routers/auths.py:1283-1284`); used for password, LDAP and single sign-on sign-ups (`backend/open_webui/routers/auths.py:656`, `:868`; `backend/open_webui/utils/oauth.py:132`) |
| `ui.default_group_id` | `DEFAULT_GROUP_ID` (`backend/open_webui/config.py:1722`) | empty (no group) | Authentication › User Access › **Default Group** (`src/lib/components/admin/Settings/Authentication.svelte:158-162`; `src/lib/i18n/locales/en-US/translation.json:2059`) | Group new accounts are added to | Used for password, LDAP, trusted-header and single sign-on sign-ups (`backend/open_webui/routers/auths.py:670`, `:882`, `:1133`; `backend/open_webui/utils/oauth.py:2137`) |
| `ui.pending_user_overlay_title` | `PENDING_USER_OVERLAY_TITLE` (`backend/open_webui/config.py:1724`) | empty: the built-in title | Authentication › Pending Accounts › **Pending User Overlay Title** (`src/lib/components/admin/Settings/Authentication.svelte:281-289`; `src/lib/i18n/locales/en-US/translation.json:2097`) | Replaces the title of the "Account Activation Pending" overlay | `src/lib/components/layout/Overlay/AccountPending.svelte:31-32` |
| `ui.pending_user_overlay_content` | `PENDING_USER_OVERLAY_CONTENT` (`backend/open_webui/config.py:1726`) | empty: the built-in text | Authentication › Pending Accounts › **Pending User Overlay Content** (`src/lib/components/admin/Settings/Authentication.svelte:294-304`; `src/lib/i18n/locales/en-US/translation.json:2095`) | Replaces the text of that overlay | Sent to pending accounts through `/api/config` (`backend/open_webui/main.py:2449-2459`) |
| `ui.watermark` | `RESPONSE_WATERMARK` (`backend/open_webui/config.py:1729`) | empty (none) | General › Features › **Response Watermark** (`src/lib/components/admin/Settings/General.svelte:395-401`; `src/lib/i18n/locales/en-US/translation.json:2401`) | Text appended when a user copies a response | Browser-side (`src/lib/components/chat/Messages/ResponseMessage.svelte:241-242`); detail in [`admin-settings-panels.md`](admin-settings-panels.md) 11.13 |
| `ui.enable_community_sharing` | `ENABLE_COMMUNITY_SHARING` (`backend/open_webui/config.py:2096`) | on | General › Features › **Community Sharing** (`src/lib/components/admin/Settings/General.svelte:276-283`; `src/lib/i18n/locales/en-US/translation.json:2379`) | Allows non-admins to share chats to the community | Checked by the server (`backend/open_webui/routers/chats.py:618`, `:667`) |
| `ui.enable_message_rating` | `ENABLE_MESSAGE_RATING` (`backend/open_webui/config.py:2098`) | on | General › Features › **Message Rating** (`src/lib/components/admin/Settings/General.svelte:286-290`; `src/lib/i18n/locales/en-US/translation.json:2395`) | Shows the rating buttons under responses | Browser-side only (`src/lib/components/chat/Messages/ResponseMessage.svelte:1279`); browsers pick up a change on their next reload of `/api/config` |
| `ui.enable_user_webhooks` | `ENABLE_USER_WEBHOOKS` (`backend/open_webui/config.py:2100`) | off | General › Features › **User Webhooks** (`src/lib/components/admin/Settings/General.svelte:380-384`; `src/lib/i18n/locales/en-US/translation.json:2411`) | Lets users receive notifications through their own webhooks | Checked by the server (`backend/open_webui/routers/notifications.py:35`; `backend/open_webui/utils/notifications.py:394`); see [`notifications-webhooks-events-and-banners.md`](notifications-webhooks-events-and-banners.md) |
| `ui.banners` | `WEBUI_BANNERS` (`backend/open_webui/config.py:2161-2167`) | `[]`; each entry of the JSON variable `WEBUI_BANNERS` must be a valid banner, otherwise the whole list becomes `[]` (logged) | General › UI › **Banners** (`src/lib/components/admin/Settings/General.svelte:483-519`; `src/lib/i18n/locales/en-US/translation.json:2372`) | Banners shown at the top of the chat page | Saved whole through `POST /api/v1/configs/banners` (`backend/open_webui/routers/configs.py:852-869`); dismissals are remembered per browser. Detail: [`notifications-webhooks-events-and-banners.md`](notifications-webhooks-events-and-banners.md), [`admin-settings-panels.md`](admin-settings-panels.md) 5.6 |

### 7.12 `webui` and `users`: Site Address and User Status (2 Keys)

Areas: [`admin-settings-panels.md`](admin-settings-panels.md) 7.1.2 and [`users-groups-roles-and-permissions.md`](users-groups-roles-and-permissions.md) 7.4. Both are saved with the other General and Authentication values (section 7.11).

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `webui.url` | `WEBUI_URL` (`backend/open_webui/config.py:1661`) | empty | General › Features › **WebUI URL** (`src/lib/components/admin/Settings/General.svelte:406-413`; `src/lib/i18n/locales/en-US/translation.json:2414`) | The public address of MedIT GPT, used where the server builds absolute links | Read by the OpenSearch descriptor, chat-finished events, channel webhooks, single sign-on redirects for MCP tool servers (falling back to the address of the request when empty) and one search engine's referrer (`backend/open_webui/main.py:2920-2922`; `backend/open_webui/utils/middleware.py:214-215`; `backend/open_webui/routers/channels.py:942`; `backend/open_webui/utils/oauth.py:514-515`; `backend/open_webui/routers/retrieval.py:2586`). The production value is **TO BE CONFIRMED** |
| `users.enable_status` | `ENABLE_USER_STATUS` (`backend/open_webui/config.py:2052`) | on | General › Features › **User Status** (`src/lib/components/admin/Settings/General.svelte:387-391`; `src/lib/i18n/locales/en-US/translation.json:2409`) | Lets users set a personal status shown in the user menu | The server refuses status reads and changes while it is off (`backend/open_webui/routers/users.py:575-579`, `:596`); the sidebar hides the control (`src/lib/components/layout/Sidebar.svelte:1094`) |

### 7.13 `user`: Default Permissions (1 Key)

Area document: [`users-groups-roles-and-permissions.md`](users-groups-roles-and-permissions.md) sections 7.5 and 7.6, and the permission rules in `knowledgebase/tools/ground-truth.md` (Accounts and Access).

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `user.permissions` | 65 `USER_PERMISSIONS_*` variables, one per permission, assembled into one object (`backend/open_webui/config.py:1733-2022`) | the structure `DEFAULT_USER_PERMISSIONS` with sections `workspace`, `sharing`, `access_grants`, `chat`, `features`, `settings` (`backend/open_webui/config.py:1940-2020`) | Users › Groups › **Default permissions** (subtitle `applies to all users with the "user" role`) (`src/lib/components/admin/Users/Groups.svelte:220-224`; `src/lib/i18n/locales/en-US/translation.json:564`, `:205`) | The permissions every `user`-role account has before group permissions are added | A group can add a permission but cannot remove one granted here; where a call site does not pass the stored object, the code and environment defaults apply instead, and keys a later release adds are filled from them (`backend/open_webui/utils/access_control/__init__.py:75-108`; `knowledgebase/tools/ground-truth.md`). Saved whole (`backend/open_webui/routers/users.py:424-435`); sent to browsers (`backend/open_webui/main.py:2421`). Folded object key (section 4). Every permission: [`users-groups-roles-and-permissions.md`](users-groups-roles-and-permissions.md) 7.5 |

The 65 seeding variables, by section of the permission object. Each is read as `True` or `False`; the line numbers are in `backend/open_webui/config.py` and the structure is `DEFAULT_USER_PERMISSIONS` (`:1940-2020`). Like any seed, they matter only until `user.permissions` is first stored; the code defaults also fill permissions missing from the stored object (`backend/open_webui/utils/access_control/__init__.py:107`). What each permission does is in [`users-groups-roles-and-permissions.md`](users-groups-roles-and-permissions.md) 7.5.

| Section | Permission path, seeding variable and code default (`on`/`off`) |
|---|---|
| `workspace` | `workspace.models` ← `USER_PERMISSIONS_WORKSPACE_MODELS_ACCESS` (off, `:1733`); `workspace.knowledge` ← `USER_PERMISSIONS_WORKSPACE_KNOWLEDGE_ACCESS` (off, `:1737`); `workspace.prompts` ← `USER_PERMISSIONS_WORKSPACE_PROMPTS_ACCESS` (off, `:1741`); `workspace.tools` ← `USER_PERMISSIONS_WORKSPACE_TOOLS_ACCESS` (off, `:1745`); `workspace.skills` ← `USER_PERMISSIONS_WORKSPACE_SKILLS_ACCESS` (off, `:1749`); `workspace.models_import` ← `USER_PERMISSIONS_WORKSPACE_MODELS_IMPORT` (off, `:1753`); `workspace.models_export` ← `USER_PERMISSIONS_WORKSPACE_MODELS_EXPORT` (off, `:1757`); `workspace.prompts_import` ← `USER_PERMISSIONS_WORKSPACE_PROMPTS_IMPORT` (off, `:1761`); `workspace.prompts_export` ← `USER_PERMISSIONS_WORKSPACE_PROMPTS_EXPORT` (off, `:1765`); `workspace.tools_import` ← `USER_PERMISSIONS_WORKSPACE_TOOLS_IMPORT` (off, `:1769`); `workspace.tools_export` ← `USER_PERMISSIONS_WORKSPACE_TOOLS_EXPORT` (off, `:1773`); `workspace.skills_import` ← `USER_PERMISSIONS_WORKSPACE_SKILLS_IMPORT` (off, `:1777`); `workspace.skills_export` ← `USER_PERMISSIONS_WORKSPACE_SKILLS_EXPORT` (off, `:1781`) |
| `sharing` | `sharing.models` ← `USER_PERMISSIONS_WORKSPACE_MODELS_ALLOW_SHARING` (off, `:1786`); `sharing.public_models` ← `USER_PERMISSIONS_WORKSPACE_MODELS_ALLOW_PUBLIC_SHARING` (off, `:1790`); `sharing.knowledge` ← `USER_PERMISSIONS_WORKSPACE_KNOWLEDGE_ALLOW_SHARING` (off, `:1794`); `sharing.public_knowledge` ← `USER_PERMISSIONS_WORKSPACE_KNOWLEDGE_ALLOW_PUBLIC_SHARING` (off, `:1798`); `sharing.prompts` ← `USER_PERMISSIONS_WORKSPACE_PROMPTS_ALLOW_SHARING` (off, `:1802`); `sharing.public_prompts` ← `USER_PERMISSIONS_WORKSPACE_PROMPTS_ALLOW_PUBLIC_SHARING` (off, `:1806`); `sharing.tools` ← `USER_PERMISSIONS_WORKSPACE_TOOLS_ALLOW_SHARING` (off, `:1811`); `sharing.public_tools` ← `USER_PERMISSIONS_WORKSPACE_TOOLS_ALLOW_PUBLIC_SHARING` (off, `:1815`); `sharing.skills` ← `USER_PERMISSIONS_WORKSPACE_SKILLS_ALLOW_SHARING` (off, `:1819`); `sharing.public_skills` ← `USER_PERMISSIONS_WORKSPACE_SKILLS_ALLOW_PUBLIC_SHARING` (off, `:1823`); `sharing.notes` ← `USER_PERMISSIONS_NOTES_ALLOW_SHARING` (off, `:1828`); `sharing.public_notes` ← `USER_PERMISSIONS_NOTES_ALLOW_PUBLIC_SHARING` (off, `:1830`); `sharing.folders` ← `USER_PERMISSIONS_FOLDERS_ALLOW_SHARING` (off, `:1834`); `sharing.public_chats` ← `USER_PERMISSIONS_CHAT_ALLOW_PUBLIC_SHARING` (off, `:1877`); `sharing.open_chats` ← `USER_PERMISSIONS_CHAT_ALLOW_OPEN_SHARING` (off, `:1881`); `sharing.public_calendars` ← `USER_PERMISSIONS_CALENDAR_ALLOW_PUBLIC_SHARING` (off, `:1837`) |
| `access_grants` | `access_grants.allow_users` ← `USER_PERMISSIONS_ACCESS_GRANTS_ALLOW_USERS` (on, `:1841`); `access_grants.allow_groups` ← `USER_PERMISSIONS_ACCESS_GRANTS_ALLOW_GROUPS` (on, `:1844`) |
| `chat` | `chat.controls` ← `USER_PERMISSIONS_CHAT_CONTROLS` (on, `:1849`); `chat.valves` ← `USER_PERMISSIONS_CHAT_VALVES` (on, `:1851`); `chat.system_prompt` ← `USER_PERMISSIONS_CHAT_SYSTEM_PROMPT` (on, `:1853`); `chat.params` ← `USER_PERMISSIONS_CHAT_PARAMS` (on, `:1855`); `chat.file_upload` ← `USER_PERMISSIONS_CHAT_FILE_UPLOAD` (on, `:1857`); `chat.web_upload` ← `USER_PERMISSIONS_CHAT_WEB_UPLOAD` (on, `:1859`); `chat.delete` ← `USER_PERMISSIONS_CHAT_DELETE` (on, `:1861`); `chat.delete_message` ← `USER_PERMISSIONS_CHAT_DELETE_MESSAGE` (on, `:1863`); `chat.continue_response` ← `USER_PERMISSIONS_CHAT_CONTINUE_RESPONSE` (on, `:1865`); `chat.regenerate_response` ← `USER_PERMISSIONS_CHAT_REGENERATE_RESPONSE` (on, `:1867`); `chat.rate_response` ← `USER_PERMISSIONS_CHAT_RATE_RESPONSE` (on, `:1871`); `chat.edit` ← `USER_PERMISSIONS_CHAT_EDIT` (on, `:1873`); `chat.share` ← `USER_PERMISSIONS_CHAT_SHARE` (on, `:1875`); `chat.export` ← `USER_PERMISSIONS_CHAT_EXPORT` (on, `:1885`); `chat.import` ← `USER_PERMISSIONS_CHAT_IMPORT` (on, `:1887`); `chat.stt` ← `USER_PERMISSIONS_CHAT_STT` (on, `:1889`); `chat.tts` ← `USER_PERMISSIONS_CHAT_TTS` (on, `:1891`); `chat.call` ← `USER_PERMISSIONS_CHAT_CALL` (on, `:1893`); `chat.multiple_models` ← `USER_PERMISSIONS_CHAT_MULTIPLE_MODELS` (on, `:1895`); `chat.temporary` ← `USER_PERMISSIONS_CHAT_TEMPORARY` (on, `:1897`); `chat.temporary_enforced` ← `USER_PERMISSIONS_CHAT_TEMPORARY_ENFORCED` (off, `:1899`) |
| `features` | `features.api_keys` ← `USER_PERMISSIONS_FEATURES_API_KEYS` (off, `:1924`); `features.notes` ← `USER_PERMISSIONS_FEATURES_NOTES` (on, `:1920`); `features.folders` ← `USER_PERMISSIONS_FEATURES_FOLDERS` (on, `:1918`); `features.channels` ← `USER_PERMISSIONS_FEATURES_CHANNELS` (on, `:1922`); `features.direct_tool_servers` ← `USER_PERMISSIONS_FEATURES_DIRECT_TOOL_SERVERS` (off, `:1904`); `features.web_search` ← `USER_PERMISSIONS_FEATURES_WEB_SEARCH` (on, `:1908`); `features.image_generation` ← `USER_PERMISSIONS_FEATURES_IMAGE_GENERATION` (on, `:1910`); `features.code_interpreter` ← `USER_PERMISSIONS_FEATURES_CODE_INTERPRETER` (on, `:1914`); `features.memories` ← `USER_PERMISSIONS_FEATURES_MEMORIES` (on, `:1926`); `features.automations` ← `USER_PERMISSIONS_FEATURES_AUTOMATIONS` (off, `:1928`); `features.calendar` ← `USER_PERMISSIONS_FEATURES_CALENDAR` (on, `:1930`); `features.webhooks` ← `USER_PERMISSIONS_FEATURES_USER_WEBHOOKS` (off, `:1932`) |
| `settings` | `settings.interface` ← `USER_PERMISSIONS_SETTINGS_INTERFACE` (on, `:1937`) |

### 7.14 `webhook_url`: Legacy Admin Webhook (1 Key)

Area document: [`notifications-webhooks-events-and-banners.md`](notifications-webhooks-events-and-banners.md) sections 5.3 and 5.4. It is the only key in `DEFAULT_CONFIG` without a namespace.

| Key | Seeded from | Code default | Admin screen | Effect | Notes |
|---|---|---|---|---|---|
| `webhook_url` | `WEBHOOK_URL` (`backend/open_webui/config.py:2080`) | empty | none (API or import only) | Legacy single admin webhook address. At each start, if it holds an address and no webhook with the id `default` exists, a **Default webhook** subscribed to every event is added to `events.webhooks` | No field of its own: General › Events edits `events.webhooks`, and deleting the **Default webhook** empties this key so it is not re-created (`backend/open_webui/events.py:854-878`, `:911-922`; `backend/open_webui/main.py:369`). Also loaded into the single sign-on runtime map, where nothing uses it (`backend/open_webui/utils/oauth.py:169`, `:201-205`). A webhook address can embed a token: treat it as secret |

## 8. Cron Jobs and Background Processes

There is no crontab and no background loop that maintains these keys. Almost every key is read
from the database each time it is needed, so a save applies to the next request in every server
process (section 5.1). The exceptions are objects that a server process builds from the keys and
keeps in memory; they change only at start-up or when the matching screen is saved, and only in the
process that handled the save.

### 8.1 Runtime State Built Only at Start-Up or on Save

| Runtime state | Built from | Built when | Shared between processes? | Evidence |
|---|---|---|---|---|
| Local embedding model (`app.state.ef`) and the search-time embedding function (`app.state.EMBEDDING_FUNCTION`) | The 12 embedding keys (section 7.2) | At start-up; when **Documents** saves the embedding settings (`/api/v1/retrieval/embedding/update`) | No: each process holds its own | `backend/open_webui/main.py:666-668`, `:699-745`; `backend/open_webui/routers/retrieval.py:543-599` |
| Reranker (`app.state.rf`, `app.state.RERANKING_FUNCTION`) | `rag.enable_hybrid_search`, `rag.bypass_embedding_and_retrieval`, `rag.reranking_*`, `rag.external_reranker_*` (section 7.3) | At start-up, only while hybrid search is on and bypass is off; when **Documents** is saved | No | `backend/open_webui/main.py:672-697`, `:747-752`; `backend/open_webui/routers/retrieval.py:1188-1253` |
| Tool-server specifications (`app.state.TOOL_SERVERS`, and the Redis key `tool_servers` when Redis is configured) | `tool_server.connections` | At start-up when the list is not empty; on each **Integrations** save; whenever the cache is empty. Without Redis the specifications are fetched again on each use | Yes, through Redis when it is configured | `backend/open_webui/main.py:431-454`; `backend/open_webui/routers/configs.py:265`; `backend/open_webui/utils/tools.py:1170-1203` |
| Single sign-on clients for MCP tool servers that use OAuth 2.1 (`app.state.oauth_client_manager`) | `tool_server.connections` entries with an OAuth 2.1 authentication type | At start-up; on each tool-server save | No | `backend/open_webui/main.py:528-529`, `:631-658`; `backend/open_webui/routers/configs.py:246-288` |
| Terminal-server specifications (`app.state.TERMINAL_SERVERS`, Redis `terminal_servers`) | `terminal_server.connections` | At start-up only when at least one tool server exists; on each save; on first use | Yes, through Redis when it is configured | `backend/open_webui/main.py:456-460`; `backend/open_webui/routers/configs.py:342`; `backend/open_webui/utils/tools.py:1271-1354` |
| YouTube translation value (`app.state.YOUTUBE_LOADER_TRANSLATION`) | Not a key (section 4) | Reset to none at start-up; set by a retrieval-settings save | No | `backend/open_webui/main.py:670`; `backend/open_webui/routers/retrieval.py:1390` |
| **Default webhook** in `events.webhooks` | `webhook_url` | At start-up (section 5.2, step 7) | Stored in the database | `backend/open_webui/main.py:369`; `backend/open_webui/events.py:854-878` |

*Inferred from code, not tested:* with more than one server process (`UVICORN_WORKERS` above 1, or
several replicas), a save of the embedding settings, the reranker or an OAuth 2.1 tool server
changes only the process that handled it. Other processes keep their old objects until they
restart, so searches can use the old embedding model or reranker while the screen shows the new one.
An import (section 5.6) changes none of these objects in any process. How many processes MedIT GPT
runs is **TO BE CONFIRMED** (`CLAUDE.md`, Deployment).

### 8.2 Background Work That Reads These Keys

| Work | Keys it reads | When | Evidence |
|---|---|---|---|
| Processing an upload (extract, chunk, embed, store) | Section 7.1 keys, the chunking keys and the embedding keys | As a background task right after the upload, with the values stored at that moment | `backend/open_webui/routers/files.py:436-446`, `:147-150`; `backend/open_webui/routers/retrieval.py:1846-1875` |
| Running an automation | `web.search.enable` (whether the automation may search) | When the scheduler runs it | `backend/open_webui/utils/automations.py:187` |
| A sub-agent, including a background one | The `subagents.*` limits | When it starts | `backend/open_webui/utils/subagents.py:290-308` |
| Pre-fetching models at start-up | `ui.model_order_list` (order applied when the model list is built) | At start-up when the base-model cache is on, and whenever the list is rebuilt | `backend/open_webui/main.py:407-429`, `:928-935` |

Background processing in general is described in
[`rag-retrieval-embeddings-and-vector-stores.md`](rag-retrieval-embeddings-and-vector-stores.md)
section 8 and `CLAUDE.md` (Startup Order and Background Jobs).

## 9. Notifications and Emails

The application sends **no email** (`knowledgebase/tools/ground-truth.md`, Contacts). Saving a
setting can publish an **event**, which is delivered to Event functions, admin event webhooks and
the other sinks described in
[`notifications-webhooks-events-and-banners.md`](notifications-webhooks-events-and-banners.md)
sections 4 and 9.2. Events name the admin who saved (the actor), so webhook receivers get personal
data and must be handled with care.

| Event (`name`) | Published when, in this scope | Extra data | Evidence |
|---|---|---|---|
| `config.updated` | **Sub-agents** is saved (also Audio, Images and Evaluations, outside this scope) | `enabled` | `backend/open_webui/routers/configs.py:796-803`; `backend/open_webui/events.py:60-62` |
| `config.tool_servers.updated` | Tool-server list saved | `count`, `types` | `backend/open_webui/routers/configs.py:290-297` |
| `config.terminal_servers.updated` | Terminal-server list saved | `count` | `backend/open_webui/routers/configs.py:344-351` |
| `config.models.updated` | Default models, pinned models or model order saved (Models and Model Defaults) | `default_models`, `default_pinned_models`, `model_order_count` | `backend/open_webui/routers/configs.py:758-769` |
| `config.suggestions.updated` | Prompt suggestions saved | `count` | `backend/open_webui/routers/configs.py:832-839` |
| `config.banners.updated` | Banners saved | `count` | `backend/open_webui/routers/configs.py:861-868` |
| `user.permissions_updated` | Default permissions saved | none | `backend/open_webui/routers/users.py:428-434` |
| `config.imported` | Settings imported on **Database** | see the events document | `backend/open_webui/routers/configs.py:100-110` |
| `config.webhook.updated` | An admin event webhook is added, changed or deleted (the successor of `webhook_url`) | see the events document | `backend/open_webui/main.py:2504-2580` |

**No event** is published when **Documents** (including its embedding save), **Web Search**,
**Interface** (tasks) or **General** and **Authentication** are saved
(`backend/open_webui/routers/retrieval.py:537-626`, `:962-1551`;
`backend/open_webui/routers/tasks.py:135-138`; `backend/open_webui/routers/auths.py:1269-1296`), so
for most keys in this scope there is no record of who changed them other than the optional audit
log ([`configuration-environment-variables-bootstrap.md`](configuration-environment-variables-bootstrap.md)).
The `config` row keeps only the time of the last change (`updated_at`, section 6.1).

Some keys in this scope switch notification features on or off rather than notifying:
`ui.enable_user_webhooks` (personal notification webhooks, section 7.11) and `webhook_url`
(section 7.14).

## 10. Error, Warning and Notice Messages (Verbatim)

This section lists the messages that come from **saving** keys in this scope, or that a wrong stored
value produces. Messages about using the features are catalogued in the area documents' section 10:
[`rag-retrieval-embeddings-and-vector-stores.md`](rag-retrieval-embeddings-and-vector-stores.md),
[`web-search-and-web-loading.md`](web-search-and-web-loading.md),
[`admin-settings-panels.md`](admin-settings-panels.md) (save toasts, UI Translations rules),
[`chat-completion-pipeline-and-generation-tasks.md`](chat-completion-pipeline-and-generation-tasks.md)
and [`workspace-tools-tool-servers-mcp-and-terminals.md`](workspace-tools-tool-servers-mcp-and-terminals.md).
Server texts built with the error helper are shown as `[ERROR: …]` (`backend/open_webui/constants.py:16-23`).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Settings saved successfully!` | Success toast | `src/lib/components/chat/SettingsModal.svelte:461`; `src/lib/i18n/locales/en-US/translation.json:1974` | Any admin settings panel saved without an error reaching the shared handler | none | A success toast does not prove the server stored every value (rows below) |
| `Slim requires an external embedding engine (openai, ollama, azure_openai).` | Error (HTTP 400) | `backend/open_webui/routers/retrieval.py:539-540` | Saving the local embedding engine in the slim image | Choose Ollama, OpenAI or Azure OpenAI | Which image production runs is TO BE CONFIRMED |
| `[ERROR: Error updating embedding configuration]` | Error (HTTP 500) | `backend/open_webui/routers/retrieval.py:621-626` | Building the new embedding function failed (for example the model could not be loaded); none of the embedding keys was saved (section 5.3) | Report it | Server log line `Problem updating embedding model: {e}` (`:622`); in that process the local model may already be unloaded |
| `DDGS is unavailable in slim. Configure another web search provider in Admin Settings > Web Search.` | Error (HTTP 400) | `backend/open_webui/routers/retrieval.py:966-975` | Switching `web.search.engine` to DuckDuckGo in the slim image | Choose another engine | The panel may show no message ([`web-search-and-web-loading.md`](web-search-and-web-loading.md) 7.7) |
| `Playwright is unavailable in slim. Use basic HTTP fetching or an external web loader.` | Error (HTTP 400) | `backend/open_webui/routers/retrieval.py:976-983` | Switching `web.loader.engine` to Playwright in the slim image | Choose another loader | As above |
| `Transformers tokenization is unavailable in slim. Use character or token splitting.` | Error (HTTP 400) | `backend/open_webui/routers/retrieval.py:984-987` | Switching `rag.text_splitter` to `token_transformers` in the slim image | Choose another splitter | Documents shows no message for this refusal ([`rag-retrieval-embeddings-and-vector-stores.md`](rag-retrieval-embeddings-and-vector-stores.md) 7.10) |
| `Slim requires an external reranker, or an empty reranking model for cosine scoring.` | Error (HTTP 400) | `backend/open_webui/routers/retrieval.py:988-1003` | A new local reranking model in the slim image | Use the External engine or leave the model empty | As above |
| `[ERROR: Error updating reranking configuration]` | Error (HTTP 500) | `backend/open_webui/routers/retrieval.py:1254-1259` | An unexpected failure while applying the reranking settings | Report it | Log line `Problem updating reranking model: {e}` (`:1255`) |
| `Error loading reranking model: {e}` | Log error | `backend/open_webui/routers/retrieval.py:1251-1253` | The reranker failed to load during a Documents save; the server then **saves hybrid search as off** | none (not shown to the admin) | Explains "hybrid search switched itself off" (section 11.1) |
| `Error updating models: {e}` | Log error | `backend/open_webui/main.py:695-697` | Building the embedding model or reranker failed at start-up | none | The reranker stays off in that process until a successful save or restart |
| `Invalid JSON format in {{NAME}}` | Error toast | `src/lib/components/admin/Settings/Documents.svelte:243-252`; `src/lib/i18n/locales/en-US/translation.json:1207` | Docling parameters are not valid JSON on Save (`{{NAME}}` is the field name) | Fix the JSON | Nothing was sent to the server |
| `Invalid JSON format in MinerU Parameters` | Error toast | `src/lib/components/admin/Settings/Documents.svelte:255-260`; `src/lib/i18n/locales/en-US/translation.json:1209` | MinerU parameters are not valid JSON | Fix the JSON | As above |
| `Interpolation placeholders do not match: {locale}: {key}` | Error (validation) | `backend/open_webui/routers/auths.py:1260-1262` | A UI translation's `{{...}}` placeholders differ from the original text | Make them match | The panel checks this first ([`admin-settings-panels.md`](admin-settings-panels.md) 7.4) |
| `Invalid language: {locale}` / `Invalid translation key: {key}` | Error (validation) | `backend/open_webui/routers/auths.py:1254-1259` | An empty or reserved language code or key in `ui.i18n` | Correct the row | As above |
| `Connections saved successfully` / `Failed to save connections` | Success / error toast | `src/lib/components/admin/Settings/Integrations.svelte:77-87`; `src/lib/i18n/locales/en-US/translation.json:454`, `:988` | Saving `tool_server.connections` | none / retry | A failure leaves the stored list unchanged |
| `Terminal servers saved` / `Failed to save terminal servers` | Success / error toast | `src/lib/components/admin/Settings/Integrations.svelte:90-99`; `src/lib/i18n/locales/en-US/translation.json:3196`, `:993` | Saving `terminal_server.connections` | none / retry | As above |
| `Default permissions updated successfully` | Success toast | `src/lib/components/admin/Users/Groups.svelte:95`; `src/lib/i18n/locales/en-US/translation.json:565` | Saving `user.permissions` | none | — |
| `Models configuration saved successfully` | Success toast | `src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:143`; `src/lib/i18n/locales/en-US/translation.json:1402` | Saving Model Defaults (also writes the three `ui` model keys and the prompt suggestions) | none | — |
| `EXA_MAX_CONTENT_LENGTH must be a positive integer or unset` | Start-up failure | `backend/open_webui/config.py:1279-1281` | The seeding variable is 0 or negative; the configuration module refuses to load, so the server does not start | Platform maintainer fixes the variable | Seen in the start-up log |
| `Error loading TOOL_SERVER_CONNECTIONS: {e}` | Log error | `backend/open_webui/config.py:381-385` | The variable is not valid JSON; the code default becomes `[]` (matters only before the key is first stored) | none | Similar lines exist for `MODEL_ORDER_LIST`, `DEFAULT_PROMPT_SUGGESTIONS`, `DEFAULT_INTERFACE_SETTINGS` and `WEBUI_BANNERS` (`:1689-1690`, `:1681-1682`, `:1714-1715`, `:2163-2164`); invalid `TERMINAL_SERVER_CONNECTIONS` has no such fallback and stops start-up (`:396`) |
| `[ERROR: Something went wrong while searching the web.]` | Error (HTTP 400) | `backend/open_webui/routers/retrieval.py:2946-2951`; `backend/open_webui/constants.py:101` | A search failed, including when the selected engine's stored key or address is empty | Report it | The log line names the missing value, for example `No SEARXNG_QUERY_URL found in environment variables` (`backend/open_webui/routers/retrieval.py:2554`); despite the wording, the value comes from the stored setting (section 7.6), not the environment |
| `No search engine API key found in environment variables` | Log text of the error above | `backend/open_webui/routers/retrieval.py:2878-2879` | `web.search.engine` is empty or not a known engine | — | Check **Web Search Engine** |
| `[ERROR: File type {file_extension} is not allowed]` | Error (HTTP 400) | `backend/open_webui/routers/files.py:354-362` | An upload's extension is not in `rag.file.allowed_extensions` | Use an allowed type | Read the Allowed File Extensions value |
| `Oops! The file you're trying to upload is too large. Please upload a file that is less than {size}.` | Error (HTTP 413) | `backend/open_webui/routers/files.py:394-400`; `backend/open_webui/constants.py:105-107` | An upload is larger than `rag.file.max_size` megabytes | Use a smaller file | Read the Max Upload Size value |
| `Input prompt exceeds maximum length of {size}` | Error (HTTP 400) | `backend/open_webui/routers/tasks.py:491-497`; `backend/open_webui/constants.py:126` | Autocompletion input longer than `task.autocomplete.input_max_length` | none | Where the browser shows it is TO BE CONFIRMED |
| `Error: background sub-agents are disabled in settings.` | Tool result (to the model) | `backend/open_webui/utils/subagents.py:307-308` | A model asked for a background sub-agent while `subagents.background_enabled` is off | none | The model may repeat it in its answer |
| `Error: Async subagent capacity reached ({max_async} running). Wait for one to finish or increase subagents.max_async.` | Tool result (to the model) | `backend/open_webui/utils/subagents.py:364-367` | The background limit `subagents.max_async` is reached | Wait | The message names the key |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it never changes a setting, never asks for a settings export, and never
queries the database. Related symptoms are in
[`admin-settings-panels.md`](admin-settings-panels.md) section 11 (for example 11.1 "I changed a
setting and nothing happened" and 11.2 "My setting reverted after a restart"); this section covers
what is specific to the keys in this half.

### 11.1 "Retrieval settings reverted"

**Symptom.** An admin saved Documents or Web Search settings, saw `Settings saved successfully!`,
and later finds some values back as they were, or retrieval still behaves the old way.

**Likely causes, in order.**

1. **Hybrid search was switched off by the server.** If the reranking model fails to load while
   Documents is saved, the server stores `rag.enable_hybrid_search` as off; the browser is not told
   (`backend/open_webui/routers/retrieval.py:1235-1253`). A reranker timeout that is not a whole
   number makes loading fail the same way (`:182`).
2. **Another window saved older values.** Saving Documents re-saves every `web.*` key with the
   values loaded when that screen was opened, so a Web Search change made meanwhile in another tab
   or by another admin is undone (section 5.3; inferred from code). General and Authentication have
   the same effect on each other ([`admin-settings-panels.md`](admin-settings-panels.md) 5.3).
3. **Part of the save was refused.** The embedding step can fail on its own (HTTP 500, or the slim
   refusal) while the rest is saved; a slim-image refusal of the main save shows no message at all
   (sections 5.3 and 10; [`rag-retrieval-embeddings-and-vector-stores.md`](rag-retrieval-embeddings-and-vector-stores.md) 7.10).
4. **More than one server process.** The embedding model and the reranker are rebuilt only in the
   process that handled the save; other processes keep the old ones until they restart (section 8.1;
   inferred from code).
5. **Stored settings were reset or replaced.** `RESET_CONFIG_ON_START=True` deletes every stored
   setting at each start; an import or a database restore replaces them; with
   `ENABLE_PERSISTENT_CONFIG=False` saves last only until a restart
   ([`configuration-persistent-settings-a-to-o.md`](configuration-persistent-settings-a-to-o.md) 5.2 and 5.5).

**Diagnostic steps** (read-only).

1. Ask the admin which screen, which fields, the values expected and the time of the save, and
   whether anyone else had an admin settings window open.
2. Ask the admin to reopen the screen and read the current values aloud, starting with **Hybrid
   Search** on Documents › Retrieval (section 7.3).
3. Ask whether a pop-up appeared during the save, and whether the deployment uses the slim image
   (**TO BE CONFIRMED** for MedIT GPT).
4. For the platform maintainer: look in the server log at the time of the save for
   `Error loading reranking model:`, `Problem updating embedding model:` or `Error updating models:`
   (section 10), and check `RESET_CONFIG_ON_START`, `ENABLE_PERSISTENT_CONFIG` and the number of
   workers or replicas.

**Resolution.** Tier 1 gives guidance only: the admin re-applies the change with a single admin
settings window open, saving Documents and Web Search one after the other rather than in parallel.
If hybrid search keeps switching off, the reranker has to be fixed first (platform maintainer).

**Escalation.** Send the screen and field names, the keys from section 7, the expected and observed
values, the save time, and any pop-up text. Never include API keys or a settings export.

### 11.2 "The default model setting is ignored"

**Symptom.** An admin set a default model (Models › model menu › **Set as Selected Model**), but a
user's new chats open with a different model.

**Likely causes, in order.** A new chat picks its model in this order: a model named in the address
(`?model=` or `?models=`), the folder's own model, the choice remembered by that browser tab, the
user's own default, and only then the admin default; any model the user cannot use is dropped
(`src/lib/components/chat/Chat.svelte:2068-2120`).

1. **The user has their own default.** **Set as default** in the model selector saves it in the
   user's settings, and it wins over the admin default
   (`src/lib/components/chat/ModelSelector/Selector.svelte:1270`;
   `src/lib/components/chat/ModelSelector.svelte:26-36`; `src/lib/components/chat/Chat.svelte:2102-2107`).
2. **The chat was opened from a link with a model, from a folder that has its own model, or in a tab
   that remembers an earlier choice** (`src/lib/components/chat/Chat.svelte:2068-2100`).
3. **The default model is not available to that user**: no access to it, hidden, or its connection
   is unavailable, so it is filtered out (`src/lib/components/chat/Chat.svelte:200-201`, `:2113-2120`).
4. **The browser has not reloaded.** The default reaches browsers through `/api/config`
   (`backend/open_webui/main.py:2394`).
5. **It was set with `DEFAULT_MODELS` after the first start.** The stored value wins (section 5.1).
6. **Pinned is not selected.** **Set as Pinned Model** writes `ui.default_pinned_models` (sidebar),
   not the default selection (section 7.11).

**Diagnostic steps** (read-only).

1. Ask the user to start a new chat from the sidebar's new-chat button (not from a link or folder)
   after reloading the page, and say which model appears.
2. Ask whether they ever used **Set as default** in the model selector.
3. Ask the admin to confirm the model is still marked as selected in the Models list and that the
   user's groups can use it ([`workspace-models-and-model-access.md`](workspace-models-and-model-access.md)).

**Resolution.** Explain the order above. A user who wants the admin default can choose that model
and use **Set as default** themselves. Tier 1 does not change model access or defaults.

**Escalation.** Send the model ID shown in the selector (not personal data), the user's role and
groups as shown to the admin, and the result of the reload test.

### 11.3 "I changed the environment variable but nothing changed"

**Symptom.** The platform maintainer changed an environment variable such as `RAG_TOP_K`,
`WEB_SEARCH_ENGINE` or `DEFAULT_USER_ROLE`, restarted, and the screen still shows the old value.

**Likely causes, in order.**

1. **The key was already stored.** The variable seeds the key only when it has no row; after the
   first start the stored value wins (`backend/open_webui/models/config.py:240-266`; section 5.1).
2. **The variable is not the one that seeds the key.** Field names on the admin API differ from
   some seeding variables (section 4.1), for example `TOP_K` versus `RAG_TOP_K`.
3. **Not every process restarted**, or open browsers have not reloaded `/api/config`.
4. **The key is inert or has no save path.** No feature reads the stored `ui.default_locale` (only
   the export shows it; the environment constant is used, so a restart with the new value does work); `rag.tiktoken_encoding_name`
   and the Azure AI Search keys can only change by import or a database change (section 4).
5. **The setting is not a persistent key at all.** Environment-only variables are described in
   [`configuration-environment-variables-bootstrap.md`](configuration-environment-variables-bootstrap.md).

Two cases work the other way: a web-loader key stored as JSON `null` falls back to the environment
(`backend/open_webui/retrieval/web/utils.py:1065-1068`), and a key whose row has been deleted reads
its environment-derived default (`backend/open_webui/models/config.py:146-147`).

**Diagnostic steps** (read-only).

1. Find the key in section 7 and compare its **Seeded from** column with the variable that was set.
2. Ask an admin to read the value on the screen named in the **Admin screen** column.
3. For the platform maintainer: confirm the running process sees the new variable and when it
   restarted; whether the key has a stored row is a database question for the maintainer, not tier 1.

**Resolution.** The usual fix is for an admin to change the value on its screen. The other options
(removing the row, `RESET_CONFIG_ON_START`, `ENABLE_PERSISTENT_CONFIG=False`) are the platform
maintainer's and are listed in
[`configuration-persistent-settings-a-to-o.md`](configuration-persistent-settings-a-to-o.md) 5.5.

**Escalation.** Send the key, the variable name (never its value when it is a key, token or
password), the restart time and what the screen shows.

## 12. Local Customisations

Checked with read-only `git diff main...uoft` and `git diff` over the files this document cites
(the configuration module, the persistence model, the retrieval, task, configs, auths, users and
files routers, events, `main.py`, the retrieval and utility packages, the admin settings
components, the chat and model-selector components, the personal settings components and the
`en-US` translation file).

| Difference | Where | Effect on keys in this scope |
|---|---|---|
| **None in the catalogue itself.** `DEFAULT_CONFIG`, every seeding variable and code default, the persistence code (`backend/open_webui/models/config.py`) and every endpoint that saves these keys match upstream v0.11.4 | `git diff main...uoft` shows no change to `backend/open_webui/config.py`, `backend/open_webui/models/config.py` or the routers above | The 206 keys behave as upstream |
| Two fork interface settings, **Inline Citations** (`showInlineCitations`) and **Hide Processing Details** (`hideProcessingDetails`) | `backend/open_webui/models/users.py:99-100`; `src/lib/components/common/InterfaceSettings.svelte`; `src/lib/i18n/locales/en-US/translation.json` (dotted keys `settings.personal.interface.inlineCitations.*` and `.hideProcessingDetails.*`) | The same component is used by General › UI › **Default Interface Settings** (`src/lib/components/admin/Settings/General.svelte:474-476`), so an admin can preset both for every account inside `ui.default_interface_settings`; a user's own choice still wins (section 7.11) |
| Uncommitted working-tree change to the Hide Processing Details description text | `src/lib/i18n/locales/en-US/translation.json` (working tree) | Wording only; no key in this scope changes |
| Uncommitted working-tree change in chat message handling | `src/lib/components/chat/Chat.svelte` (working tree, five added lines about tool approval) | None on settings; the line numbers cited from this file in sections 7.4 and 11.2 are those of the working tree |
| Product name `MedIT GPT` | `backend/open_webui/env.py:951` (environment-only `WEBUI_NAME`) | Not a persistent key; outside this catalogue (`knowledgebase/tools/ground-truth.md`) |

## 13. Source File Index

| File | What this document takes from it | Main lines |
|---|---|---|
| `backend/open_webui/config.py` | `DEFAULT_CONFIG` entries in scope; every seeding variable and code default; seeding helpers; persistence switches | `:42-49`, `:85-91`, `:378-398`, `:862-1154`, `:1157-1345`, `:1661-2022`, `:2036-2052`, `:2080-2100`, `:2150-2167`, `:2180-2412`, `:2822-3238` |
| `backend/open_webui/models/config.py` | The `config` table; reads, upserts, seeding, the `rag.web` rename, folded object keys, the default-model repair | `:23-39`, `:101-147`, `:197-220`, `:240-382` |
| `backend/open_webui/main.py` | Start-up order, runtime set-up of embedding, reranker and tool servers, `/api/config`, OpenSearch, model order | `:345-472`, `:528-529`, `:621-752`, `:928-935`, `:2224-2472`, `:2504-2580`, `:2920-2922` |
| `backend/open_webui/routers/retrieval.py` | `RETRIEVAL_CONFIG_KEYS`; embedding and retrieval settings endpoints; slim refusals; hybrid-search switch-off; document embedding; search engines | `:178-194`, `:254-443`, `:468-1551`, `:1590-1875`, `:2511-2958` |
| `backend/open_webui/retrieval/utils.py` | `LOADER_CONFIG_KEYS`; hybrid search weights and reranker limit | `:82-144`, `:575-586` |
| `backend/open_webui/retrieval/loaders/main.py` | Which extraction engine runs and which keys it needs | `:541-720` |
| `backend/open_webui/retrieval/web/utils.py` | Web loader selection and the `null` fallback to the environment | `:1062-1152` |
| `backend/open_webui/retrieval/web/yandex.py` | Yandex settings parsed as JSON | `:58` |
| `backend/open_webui/retrieval/models/external.py` | External reranker request and its timeout (seconds) | `:19-55` |
| `backend/open_webui/retrieval/external.py`; `backend/open_webui/routers/knowledge.py` | `external_knowledge.connections`, a row outside `DEFAULT_CONFIG` | `:13`; `:559` |
| `backend/open_webui/routers/tasks.py` | `TASK_CONFIG_KEYS`, task settings endpoints, template fallbacks, autocomplete limit | `:41-138`, `:143-522` |
| `backend/open_webui/routers/configs.py` | Tool, terminal, models, sub-agents, suggestions and banners endpoints and their events; import, export | `:62-77`, `:100-125`, `:212-352`, `:734-877` |
| `backend/open_webui/routers/auths.py` | `ADMIN_CONFIG_KEYS`, the General and Authentication save and its validation; sign-up checks | `:104-136`, `:656-670`, `:868-911`, `:1204-1296` |
| `backend/open_webui/routers/users.py` | Default permissions endpoints; interface-defaults merge; user status checks | `:57-69`, `:411-474`, `:570-596` |
| `backend/open_webui/routers/files.py` | Upload extension and size checks; media types; background processing | `:111-150`, `:354-400`, `:436-446` |
| `backend/open_webui/events.py` | Event definitions; legacy webhook migration and deletion; sinks | `:20-22`, `:55-98`, `:141-144`, `:854-922`, `:1171-1202` |
| `backend/open_webui/utils/subagents.py` | Sub-agent limits and messages | `:285-308`, `:364-367`, `:454`, `:511-512` |
| `backend/open_webui/utils/tools.py` | Built-in tool gates; tool and terminal server caches | `:645-654`, `:1170-1354` |
| `backend/open_webui/utils/middleware.py` | Per-request reads of retrieval, template, voice and tool-server keys | `:214`, `:998-1004`, `:1383-1404`, `:2108-2133`, `:2352`, `:2674-2700` |
| `backend/open_webui/utils/task.py` | Task model choice; RAG template fallback | `:16-27`, `:265-267` |
| `backend/open_webui/utils/oauth.py` | Single sign-on runtime map (including `webhook_url`); `webui.url` for MCP redirects; default group | `:131-205`, `:514-515`, `:2137` |
| `backend/open_webui/utils/access_control/__init__.py` | How default permissions are applied | `:75-108` |
| `backend/open_webui/constants.py` | Error helper and texts | `:16-23`, `:101`, `:105-107`, `:126` |
| `backend/open_webui/migrations/versions/3ff2c63645b8_reshape_config_to_per_key_rows.py` | Renames of embedding keys; `rag.web.*` names | `:312-313`, `:414-419` |
| Other backend files cited once: `backend/open_webui/routers/chats.py`, `backend/open_webui/routers/channels.py`, `backend/open_webui/routers/notifications.py`, `backend/open_webui/routers/terminals.py`, `backend/open_webui/tools/builtin.py`, `backend/open_webui/utils/automations.py`, `backend/open_webui/utils/notifications.py`, `backend/open_webui/env.py`, `backend/open_webui/models/users.py` | Single readers of a key, cited in its row | see the rows |
| `src/lib/components/admin/Settings/Documents.svelte` | Every Documents field, its label line and the save code | `:164-350`, `:438-1547` |
| `src/lib/components/admin/Settings/WebSearch.svelte` | Every Web Search field, engine lists, load and save code | `:20-157`, `:173-1492` |
| `src/lib/components/admin/Settings/Interface.svelte` | Task fields and the save | `:64-73`, `:176-558` |
| `src/lib/components/admin/Settings/Subagents.svelte` | Sub-agent fields and value handling | `:24-48`, `:61-184` |
| `src/lib/components/admin/Settings/Integrations.svelte` | Tool and terminal server sections and their toasts | `:72-99`, `:184-337` |
| `src/lib/components/admin/Settings/General.svelte`; `src/lib/components/admin/Settings/I18nSettings.svelte` | Features and UI sections: WebUI URL, switches, watermark, interface defaults, translations, banners | `:274-519`; `:31` |
| `src/lib/components/admin/Settings/Authentication.svelte` | User Access and Pending Accounts fields; the save | `:89-96`, `:139-307` |
| `src/lib/components/admin/Settings/Models.svelte`; `src/lib/components/admin/Settings/Models/ModelMenu.svelte`; `src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte` | Default and pinned models, model order, prompt suggestions | `:333-396`, `:981-984`; `:127-148`; `:110-145`, `:261` |
| `src/lib/components/admin/Users/Groups.svelte` | Default permissions entry and save | `:83-104`, `:220-224` |
| `src/lib/components/chat/Chat.svelte`; `src/lib/components/chat/ModelSelector.svelte`; `src/lib/components/chat/ModelSelector/Selector.svelte` | How a new chat picks its model; the user's own default (working tree) | `:200-215`, `:2068-2120`, `:3154-3155`; `:26-36`; `:1270` |
| Other front-end files cited once (`src/lib/components/chat/MessageInput.svelte`, `src/lib/components/chat/Messages/ResponseMessage.svelte`, `src/lib/components/chat/Settings/Account.svelte`, `src/lib/components/chat/Settings/Integrations.svelte`, `src/lib/components/chat/SettingsModal.svelte`, `src/lib/components/common/InterfaceSettings.svelte`, `src/lib/components/layout/Overlay/AccountPending.svelte`, `src/lib/components/layout/Sidebar.svelte`, `src/routes/(app)/admin/settings/[tab]/+page.svelte`, `src/lib/components/admin/Settings/Database.svelte`) | Browser-side use of a key, cited in its row | see the rows |
| `src/lib/i18n/locales/en-US/translation.json` | English label of every field cited in section 7 and of the toasts in section 10 | cited per row |
| `knowledgebase/tools/ground-truth.md`; `CLAUDE.md` | Verified facts on persistence, permissions, contacts and deployment | Settings; Accounts and Access; Deployment |

## 14. Open Questions

### 14.1 Method and Counts

- Keys were listed by a script that parses `backend/open_webui/config.py` with Python's `ast`
  module (never importing it), takes every `DEFAULT_CONFIG` entry whose namespace is in scope, and
  follows each variable to its definition and its `os.getenv` or `os.environ` reads. It found
  **206 keys**: `rag` 76, `web` 78, `ui` 20, `task` 19, `subagents` 7 and one each for
  `tool_server`, `terminal_server`, `user`, `users`, `webui` and `webhook_url`. An independent
  line count of `DEFAULT_CONFIG` by namespace gives the same figures, and 199 + 206 = 405 matches
  `knowledgebase/tools/ground-truth.md`.
- A second script compared section 7 with that list: every key has exactly one row. Field names
  were taken from the five field maps (`RETRIEVAL_CONFIG_KEYS`, `TASK_CONFIG_KEYS`,
  `ADMIN_CONFIG_KEYS`, `MODELS_CONFIG_KEYS`, `SUBAGENTS_CONFIG_KEYS`); 198 keys have a field name,
  and 9 keys have no admin screen: `rag.tiktoken_encoding_name`, `rag.external_reranker_timeout`,
  `web.search.serpstack_https`, the three `web.search.azure_ai_search_*` keys,
  `ui.enable_password_change_form`, `ui.default_locale` and `webhook_url`.
- Labels were located by finding each field's binding in the panel and the nearest label before
  it, then resolving dotted keys in `en-US`; every row was checked by eye, and description texts
  that the locator picked by mistake were corrected before or right after appending.

### 14.2 To Be Confirmed (Not Determinable From the Repository)

1. **Live values** of all 206 keys, and which seeding variables production sets. Live values are
   data in the database or environment.
2. Whether production runs the **slim** image, how many **worker processes or replicas** it runs,
   and whether **Redis** is configured. These decide whether the slim refusals (section 10) and the
   per-process staleness (section 8.1) apply.
3. The production values of `ENABLE_PERSISTENT_CONFIG`, `ENABLE_OAUTH_PERSISTENT_CONFIG` and
   `RESET_CONFIG_ON_START`.
4. The production value of `webui.url` (the public address) and of `DEFAULT_LOCALE`.
5. Who the **platform maintainer** is (the person who changes environment variables and restarts).
6. Whether a legacy `WEBHOOK_URL` was ever set, so that a **Default webhook** exists in
   `events.webhooks` (section 7.14).

### 14.3 Inferred From Code, Not Tested

The application was not started (research rule), so these follow from reading the code only:

1. Saving **Documents** overwrites Web Search settings changed in another window after Documents
   was opened (section 5.3).
2. With several server processes, the embedding model, the reranker and OAuth 2.1 tool-server
   clients stay stale in processes that did not handle the save (section 8.1).
3. A non-numeric `rag.external_reranker_timeout` makes the reranker fail to load and so switches
   hybrid search off on the next Documents save (section 11.1).
4. `rag.web.*` keys in an imported file are renamed to `web.*` only at the next start (section 5.6).
5. A list-valued `ui.default_models` written by an import, rather than a comma-separated string, is
   repaired only at the next start; how the chat page behaves before then was not established.
6. If `web.search.engine` holds `azure` (possible only through the environment at the first start
   or an import), the Web Search screen offers no matching engine and its engine list is a required
   field; whether that screen can then be saved was not established.
7. Where the browser shows the autocompletion length error (section 10) was not established.

### 14.4 Discrepancies and Refinements for Other Documents

1. **Refinement of `knowledgebase/tools/ground-truth.md`** ("after first boot the stored value wins
   and changing an environment variable has no effect"): three exceptions exist in this scope.
   no feature reads the stored `ui.default_locale` (the environment constant `DEFAULT_LOCALE` is
   used); a web-loader key stored as JSON `null` falls back to its environment value
   (`backend/open_webui/retrieval/web/utils.py:1065-1068`); and `RAG_FILE_MAX_SIZE` also sets an
   environment-only metadata limit (`backend/open_webui/env.py:841-848`). None contradicts the
   general rule; they are recorded here for `VERIFICATION.md`.
2. **Addition for `web-search-and-web-loading.md` section 7.7**, which says the Web Search panel
   always sends every field so a missing field "matters only to scripts": the **Documents** panel
   also sends the whole `web` object it loaded, which re-saves every `web.*` key (section 5.3).
3. **Addition for `rag-retrieval-embeddings-and-vector-stores.md` section 7.10**: a failed reranker
   load during the Documents save silently stores hybrid search as off
   (`backend/open_webui/routers/retrieval.py:1251-1253`).
4. The Documents screen's description of **Top K Reranker** ("sent to the reranker") differs from
   the code, where it is the number kept after reranking; already noted in the rag document and
   repeated in section 7.3.
5. The search-engine errors say a value was not "found in environment variables" although it is
   read from the stored settings (section 10); this is wording in the code, not an error in the
   knowledgebase.

### 14.5 Not Covered Here

- The behaviour of each feature is in the area documents named in section 1; this catalogue gives
  the key-level facts only.
- Security-sensitive detail (how provider credentials, tool-server credentials and webhook tokens
  are protected) is not described. Security-sensitive: refer to the platform maintainer and U of T
  Information Security (security.utoronto.ca).
- Events outside this scope and the full event catalogue are in
  [`notifications-webhooks-events-and-banners.md`](notifications-webhooks-events-and-banners.md).
