# Model Connections: OpenAI-Compatible, Ollama and Direct

## At a Glance

- **What it is.** The plumbing between MedIT GPT and the services that actually run AI models.
  An admin adds **connections**: OpenAI-compatible APIs (OpenAI itself, Azure OpenAI, Anthropic's
  API, LiteLLM, llama.cpp, LM Studio, a Pipelines server or anything else that speaks the OpenAI
  format) and **Ollama** servers. The server asks every enabled connection for its model list,
  merges the lists, applies access rules and gives the result to the model picker. When someone
  chats, the server forwards the request to the connection that owns the chosen model
  (`backend/open_webui/utils/models.py:58-66`; `backend/open_webui/routers/openai.py:1486-1754`;
  `backend/open_webui/routers/ollama.py:1098-1172`).
- **Where it is managed.** Admins: **Settings > Admin > AI > Connections**; the old address
  `/admin/settings/connections` redirects there (`src/routes/(app)/admin/settings/[tab]/+page.svelte:5-10`;
  `src/lib/components/admin/Settings/Connections.svelte`). Ollama model downloads: the download
  icon on an Ollama connection row (**Manage Ollama**), or **Settings > Admin > AI > Models >
  Actions > Manage**. Users' own connections: **Settings > Personal > Services > Connections**, shown
  only when an admin has switched on **Direct Connections**
  (`src/lib/components/chat/SettingsModal.svelte:381-383`).
- **Code defaults** (live values are data in the `config` table, TO BE CONFIRMED): OpenAI API **on**,
  Ollama API **on**, Direct Connections **off**, Cache Base Model List **off**; first OpenAI URL
  `https://api.openai.com/v1`; Ollama URL `http://localhost:11434` outside Docker
  (`backend/open_webui/config.py:230`, `:237-300`, `:319-347`, `:374`).
- **How the list is built.** On every model-list request (normally once per page load) the server
  queries all enabled connections in parallel, waiting at most **10 seconds** each
  (`AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST`). A connection that fails or times out simply contributes no
  models; the only trace is a server log line (`backend/open_webui/routers/openai.py:89-119`;
  `backend/open_webui/routers/ollama.py:69-94`; `backend/open_webui/env.py:656-663`).
- **Why users do not see a model.** For non-admin users the list keeps only models that have a
  **model record** (created in Settings > Admin > AI > Models or the Workspace) **and** are shared
  with them. A model that has just appeared on a connection is visible to **admins only** until an
  admin configures and shares it (`backend/open_webui/utils/models.py:524-578`). Other causes are
  in section 5.9.
- **Caching.** With **Cache Base Model List** on, the merged provider list is fetched at startup
  or on a connection save and then reused (in Redis when configured, otherwise in each server
  process) until an admin presses **Refresh** (`backend/open_webui/utils/models.py:69-106`;
  `backend/open_webui/main.py:407-429`).
- **Verify Connection** asks the provider for its model list (OpenAI-compatible: `{url}/models`;
  Ollama: `{url}/api/version`) and shows `Server connection verified`, or `OpenAI: {message}` /
  `Ollama: Network Problem` (`backend/open_webui/routers/openai.py:1066-1151`;
  `backend/open_webui/routers/ollama.py:253-286`; `src/lib/apis/openai/index.ts:327-390`;
  `src/lib/apis/ollama/index.ts:3-31`).
- **Direct connections.** The user's **browser** lists the models and makes the provider call;
  the server relays the answer over the websocket. Without an open, connected tab the request
  fails with `Direct connection requires an active WebSocket session; cannot generate completion
  in this context (e.g. background task).` (`backend/open_webui/utils/chat.py:49-145`;
  `src/routes/+layout.svelte:646-731`).
- **Provider failures.** Users see the provider's own error text (invalid key, rate limit, model
  not found) in the grey error box; network failures show `Open WebUI: Server Connection Error`.
  Every provider error also writes a server log line `Upstream {provider} request failed: HTTP
  {status} ({error_type}) ...` that classifies it as `authentication_failed`, `rate_limited`,
  `model_not_found`, `server_failed` or `upstream_error` (`backend/open_webui/events.py:1205-1272`).
- **Playground** (`/playground`): admin-only test bench for chat, raw completions and images;
  nothing is saved (`src/lib/components/playground/Chat.svelte:305-308`).
- **This area matches upstream Open WebUI v0.11.4**: no file in scope differs on the `uoft` branch
  or in the working tree (section 12).

## 1. Purpose and Who Uses It

MedIT GPT does not run AI models itself. Every answer comes from an outside service, a
**provider**, reached through a **connection** that an admin (or, for direct connections, a user)
has configured. This area covers how those connections are set up, how the list of models that
users pick from is assembled, how the server forwards requests to the provider, and what happens
when a provider is slow, refuses a key or is unreachable. It is the first place to look when a
user says "my model is gone", "every answer fails" or "the model list is empty".

Who touches it:

| Who | What they do here | Evidence |
|---|---|---|
| Every signed-in user (role `user` or `admin`) | Picks models from the list this area builds; their chats are forwarded to the provider through it | `backend/open_webui/main.py:897-943`; `backend/open_webui/utils/chat.py:148-305` |
| Users, when **Direct Connections** is on | Add their own OpenAI-compatible endpoint and key in Settings > Personal > Services > Connections; their browser calls that provider | `src/lib/components/chat/Settings/Connections.svelte`; `src/lib/apis/index.ts:61-177` |
| Admins | Add, edit, switch off and remove OpenAI-compatible and Ollama connections; switch Direct Connections and the model-list cache on or off; verify connections | `src/lib/components/admin/Settings/Connections.svelte` |
| Admins | Download, update, create, upload and delete Ollama models; download, load, unload and delete llama.cpp and LM Studio models; unload models from memory | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte`; `src/lib/components/admin/Settings/Models/Manage/ManageProviderModels.svelte`; `backend/open_webui/main.py:952-1064` |
| Admins | Try models in the **Playground** (chat, raw completions, image generation and editing) | `src/routes/(app)/playground/`; `src/lib/components/playground/` |
| Scripts and integrations (API keys) | Call the model list, the embeddings endpoint and the `/openai` and `/ollama` proxy routes | `backend/open_webui/main.py:897-898`, `:1072-1073`; section 2.2 |

What tier 1 needs from this document: how to tell a missing model (list problem) from a failing
model (provider problem), the exact wording of the messages admins and users see, what the
switches on the Connections screen do, and what to collect before escalating. Neighbouring
documents:

- `workspace-models-and-model-access.md`: model records, sharing a model with groups, hiding,
  ordering and default models (the access rules that decide who sees a connection's models).
- `chat-completion-pipeline-and-generation-tasks.md`: everything between Send and the last token,
  including how errors are displayed in the chat.
- `admin-settings-panels.md`: the other admin panels and the settings export.
- `user-settings-and-personalisation.md`: the rest of the personal Settings window.
- `image-generation-and-editing.md`: the image engines behind the Images playground.
- `public-api-and-integrations.md`: API keys and the OpenAI- and Anthropic-compatible endpoints
  for scripts.

## 2. Navigation and URLs

URLs are relative to the site root; the production host name is TO BE CONFIRMED.

### 2.1 Screens

| Screen | How to get there | Who sees it | Evidence |
|---|---|---|---|
| **Connections** (admin) | User menu > **Settings** > **Admin** section > **AI** group > **Connections**. The address `/admin/settings/connections` redirects to `/?settings=admin%3Aconnections`, which opens the same tab | Admins; a non-admin following the link lands on the General tab instead | `src/lib/components/chat/SettingsModal.svelte:160`, `:281-284`, `:857-862`; `src/routes/(app)/admin/settings/[tab]/+page.svelte:5-10`; `src/routes/(app)/+layout.svelte:165-194` |
| **Add Connection / Edit Connection** pop-up | The **+** button (tooltip `Add Connection`) beside "Manage OpenAI API Connections" or "Manage Ollama API Connections"; the gear button (tooltip `Configure`) on a connection row | Admins | `src/lib/components/admin/Settings/Connections.svelte:257-270`, `:316-330`; `src/lib/components/admin/Settings/Connections/OpenAIConnection.svelte:95-105`; `src/lib/components/AddConnectionModal.svelte:288-294` |
| **Manage Ollama** pop-up | Download icon (tooltip `Manage`) on an Ollama connection row | Admins | `src/lib/components/admin/Settings/Connections/OllamaConnection.svelte:71-81`; `src/lib/components/admin/Settings/Connections/ManageOllamaModal.svelte:14-36` |
| **Manage Models** pop-up | Settings > Admin > AI > **Models** > **Actions** > **Manage** (label text `Manage`, key `settings.admin.models.manageModels.label`, `src/lib/i18n/locales/en-US/translation.json:2614`) | Admins | `src/lib/components/admin/Settings/Models.svelte:876-888`; `src/lib/components/admin/Settings/Models/ManageModelsModal.svelte:83-137` |
| Model picker download options | Type a model name in the chat model picker; admins see `Pull "{searchValue}" from Ollama.com` and `Download "{searchValue}" from {provider}` | Admins | `src/lib/components/chat/ModelSelector/Selector.svelte:312-346` |
| **Connections** (personal, direct connections) | User menu > **Settings** > **Personal** > **Services** > **Connections**, or `/?settings=connections` | Any signed-in user, but only when the admin switch **Direct Connections** is on | `src/lib/components/chat/SettingsModal.svelte:147`, `:212-215`, `:381-383`, `:811-817` |
| **Playground** | User menu > **Playground**, or a pinned sidebar entry; `/playground` (Chat), `/playground/completions`, `/playground/images` | Admins only; anyone else is sent to `/` | `src/lib/components/layout/Sidebar/UserMenu.svelte:425-447`; `src/lib/components/layout/Sidebar.svelte:183-184`, `:196`; `src/routes/(app)/playground/+layout.svelte:53-84`; `src/lib/components/playground/Chat.svelte:305-308` |
| **Ollama Version** line | Settings > Personal > About shows `Ollama Version` (key `settings.personal.about.sections.ollamaVersion.title`, `src/lib/i18n/locales/en-US/translation.json:2738`) when at least one enabled Ollama connection answers | Any signed-in user | `src/lib/components/chat/Settings/About.svelte:40-43`, `:112-118` |

The browser tab title in the Playground is `Playground / {WEBUI_NAME}`, so it reads
"Playground / MedIT GPT" with the fork's default name (`src/routes/(app)/playground/+layout.svelte:15-17`;
`tools/ground-truth.md`, Version and Identity).

### 2.2 Server Endpoints

The two provider routers are mounted at `/openai` and `/ollama`, not under `/api/v1`
(`backend/open_webui/main.py:843-844`). "Signed-in user" means role `user` or `admin`
(`get_verified_user`); `pending` accounts are refused (ground truth, Accounts and Access).
Endpoints with a `{url_idx}` choose a connection by its position in the list (0 is the first).

**Model list and helpers in `main.py`.**

| Method and path | Who may call | What it does | Evidence |
|---|---|---|---|
| `GET /api/models` (also `/api/v1/models`) | Signed-in user | The model list for the picker: all base models plus custom models, filtered by access, sorted by the admin's model order. `?refresh=true` rebuilds it, bypassing the cache | `backend/open_webui/main.py:897-943` |
| `GET /api/models/base` | Admin | The raw merged provider list (functions, OpenAI-compatible, Ollama) without custom models or access filtering | `backend/open_webui/main.py:946-949` |
| `POST /api/models/unload` | Admin | Unloads a model from memory on Ollama (every server that hosts it) or llama.cpp; resolves custom models to their base model first | `backend/open_webui/main.py:952-1064` |
| `POST /api/embeddings` (also `/api/v1/embeddings`) | Signed-in user | OpenAI-format embeddings for any model in the list, routed to Ollama or an OpenAI-compatible connection | `backend/open_webui/main.py:1072-1094`; `backend/open_webui/utils/embeddings.py:24-88` |

**`/openai` router.**

| Method and path | Who may call | What it does | Evidence |
|---|---|---|---|
| `GET /openai/config` | Admin | Reads the four `openai.*` settings | `backend/open_webui/routers/openai.py:544-546` |
| `POST /openai/config/update` | Admin | Saves them, clears the model caches, publishes `model.provider_config.updated` | `backend/open_webui/routers/openai.py:556-597` |
| `GET /openai/models` | Signed-in user | Merged list from all enabled OpenAI-compatible connections, access-filtered for role `user` | `backend/open_webui/routers/openai.py:864-941` |
| `GET /openai/models/{url_idx}` | Admin | The raw model list of one connection (used by the Connections screen) | `backend/open_webui/routers/openai.py:866-868`, `:879-936` |
| `GET /openai/models/{url_idx}/catalog`, `POST .../download`, `GET .../download/status/{job_id}`, `POST .../load`, `POST .../unload`, `GET .../sse`, `DELETE /openai/models/{url_idx}?model=` | Admin | Model management on connections whose **Provider** is `llama.cpp` or `lmstudio` | `backend/open_webui/routers/openai.py:949-1056` |
| `POST /openai/verify` | Admin | Verify Connection (section 5.6) | `backend/open_webui/routers/openai.py:1066-1151` |
| `POST /openai/chat/completions` | Signed-in user | Sends a chat request to the connection that owns the model | `backend/open_webui/routers/openai.py:1486-1754` |
| `POST /openai/responses` | Signed-in user | Forwards an OpenAI Responses API request | `backend/open_webui/routers/openai.py:1883-1991` |
| `POST /openai/audio/speech` | Signed-in user with the `chat.tts` permission (admins always) | Legacy text-to-speech through the `https://api.openai.com/v1` connection; the interface's read-aloud uses `/api/v1/audio` instead (`audio-speech-to-text-and-text-to-speech.md`) | `backend/open_webui/routers/openai.py:600-673` |
| Any other path under `/openai/` | Signed-in user | Generic pass-through, **switched off** unless the environment variable `ENABLE_OPENAI_API_PASSTHROUGH=True`; otherwise refused with HTTP 403 | `backend/open_webui/routers/openai.py:1994-2005`; `backend/open_webui/env.py:862` |

**`/ollama` router.**

| Method and path | Who may call | What it does | Evidence |
|---|---|---|---|
| `POST /ollama/verify` | Admin | Verify Connection: `GET {url}/api/version` | `backend/open_webui/routers/ollama.py:253-286` |
| `GET /ollama/config`, `POST /ollama/config/update` | Admin | Read and save the three `ollama.*` settings; saving clears caches and publishes `model.provider_config.updated` | `backend/open_webui/routers/ollama.py:289-352` |
| `GET /ollama/api/tags` | Signed-in user | Merged Ollama model list, access-filtered for role `user` | `backend/open_webui/routers/ollama.py:481-505` |
| `GET /ollama/api/tags/{url_idx}`, `GET /ollama/api/version/{url_idx}`, `GET /ollama/v1/models/{url_idx}` | Admin (others get HTTP 401 with the `ACCESS_PROHIBITED` text) | One server's raw list or version | `backend/open_webui/routers/ollama.py:489-490`, `:555-556`, `:1497-1498` |
| `GET /ollama/api/ps` | Admin | Models currently loaded in memory | `backend/open_webui/routers/ollama.py:508-544` |
| `GET /ollama/api/version` | Signed-in user | Lowest Ollama version among enabled servers; `{"version": false}` when Ollama is off | `backend/open_webui/routers/ollama.py:547-585` |
| `POST /ollama/api/pull`, `DELETE /ollama/api/push`, `POST /ollama/api/create`, `POST /ollama/api/copy`, `DELETE /ollama/api/delete`, `POST /ollama/api/unload` (each with optional `/{url_idx}`) | Admin | Model management (section 5.10) | `backend/open_webui/routers/ollama.py:595-838` |
| `POST /ollama/models/download`, `POST /ollama/models/upload` | Admin | GGUF model file from Hugging Face or GitHub, or uploaded from the admin's computer | `backend/open_webui/routers/ollama.py:1604-1723` |
| `POST /ollama/api/show`, `/api/embed`, `/api/embeddings`, `/api/generate`, `/api/chat`, `/v1/completions`, `/v1/embeddings`, `/v1/chat/completions`, `/v1/messages`, `/v1/responses`, `GET /ollama/v1/models` | Signed-in user | Native and OpenAI- or Anthropic-compatible calls forwarded to an Ollama server that hosts the model | `backend/open_webui/routers/ollama.py:841-1527` |

For non-admin callers, the chat, completion, embedding and model-information routes in both
routers check that the user may use the model: the model needs a model record that the user owns
or that is shared with them, otherwise the answer is HTTP 403 `Model not found`
(`backend/open_webui/utils/access_control/__init__.py:361-413`). Whether the generic pass-through
is switched on in production is TO BE CONFIRMED; questions about the security of these routes:
Security-sensitive: refer to the platform maintainer and U of T Information Security
(security.utoronto.ca).

**Settings endpoint shared with other areas.** `GET` and `POST /api/v1/configs/connections`
(admin) read and save **Direct Connections**, **Cache Base Model List** and **Direct
Integrations** together (`backend/open_webui/routers/configs.py:40-44`, `:133-160`).

## 3. Roles and Permissions

Roles are exactly `admin`, `user` and `pending` (ground truth). There is **no group permission**
for model connections: everything on the Connections screen is admin-only, and which models a
user may *use* is governed by sharing each model (model records and access grants, documented in
`workspace-models-and-model-access.md`). Role checks that fail answer HTTP 401 with
`You do not have permission to access this resource. Please contact your administrator for
assistance.` (ground truth, Accounts and Access).

### 3.1 Who Can Do What

| Action | Admin | User | Evidence |
|---|---|---|---|
| Open the admin Connections tab; read or save `openai.*`, `ollama.*`, Direct Connections and cache settings | Yes | No | `src/lib/components/admin/Settings/Connections.svelte:156-157`; `backend/open_webui/routers/openai.py:544-557`; `backend/open_webui/routers/ollama.py:289-311`; `backend/open_webui/routers/configs.py:139-149` |
| Verify a system connection | Yes | No | `backend/open_webui/routers/openai.py:1066-1071`; `backend/open_webui/routers/ollama.py:253-257` |
| Add, edit and verify **their own** direct connections | Yes, when Direct Connections is on | Yes, when Direct Connections is on | `src/lib/components/chat/SettingsModal.svelte:381-383`, `:624` |
| See the merged model list | All models (by default, see 3.2) | Only models shared with them | `backend/open_webui/main.py:897-943`; `backend/open_webui/utils/models.py:524-578` |
| Pull, update, create, upload, copy, push and delete Ollama models; see loaded models | Yes | No | `backend/open_webui/routers/ollama.py:508-512`, `:595-838`, `:1604-1638` |
| Download, load, unload and delete llama.cpp and LM Studio models | Yes | No | `backend/open_webui/routers/openai.py:949-1056` |
| Unload a model from memory (`/api/models/unload`) | Yes | No | `backend/open_webui/main.py:956-957` |
| Pull from the model picker (`Pull "{searchValue}" from Ollama.com`) | Yes | Option not shown | `src/lib/components/chat/ModelSelector/Selector.svelte:313-315` |
| Use the Playground | Yes | Sent back to `/` | `src/lib/components/playground/Chat.svelte:305-308`; `src/lib/components/playground/Completions.svelte:106-109`; `src/lib/components/playground/Images.svelte:115-119` |
| Call `/api/embeddings` | Yes | Yes, for models they may use | `backend/open_webui/main.py:1072-1094`; `backend/open_webui/utils/embeddings.py:68-71` |
| Read one connection's raw list or version (`.../{url_idx}`) | Yes | No (HTTP 401) | `backend/open_webui/routers/openai.py:867-868`; `backend/open_webui/routers/ollama.py:489-490`, `:555-556`, `:1497-1498` |

The Playground's admin check is in the browser; the endpoints it calls (`/api/chat/completions`,
`/api/v1/images/...`) are ordinary signed-in-user endpoints governed by their own areas.

### 3.2 How Access Filtering Shapes the Model List

`get_filtered_models` decides what `GET /api/models` returns
(`backend/open_webui/utils/models.py:524-578`):

1. If the environment variable `BYPASS_MODEL_ACCESS_CONTROL` is on (default **off**,
   `backend/open_webui/env.py:832`), nobody is filtered.
2. Admins are not filtered while `BYPASS_ADMIN_ACCESS_CONTROL` is on (environment-only, default
   **on**, `backend/open_webui/config.py:2086-2092`).
3. For everyone else, a model is kept when **any** of these holds:
   - it is an arena (evaluation) model whose own access list lets the user read it;
   - it has a model record and the user created that record;
   - it has a model record and an access grant gives the user (directly or through a group)
     **read** access.
4. A model **without** a model record (a base model nobody has configured yet) is kept **for
   admins only**: "No DB entry means no access control configured yet; only admins can see
   unconfigured models" (code comment, `backend/open_webui/utils/models.py:571-574`).

The per-provider lists `/openai/models` and `/ollama/api/tags` apply the same owner-or-grant
rule, but only to role `user` (`backend/open_webui/routers/openai.py:765-787`, `:938-939`;
`backend/open_webui/routers/ollama.py:460-478`, `:502-503`).

Practical consequence for support: **adding a connection never, by itself, makes its models
appear for ordinary users.** An admin must also give each model a record and share it (Public or
with groups) in Settings > Admin > AI > Models; see `workspace-models-and-model-access.md`.
Whether production overrides either bypass variable is TO BE CONFIRMED.

### 3.3 Access Checks When a Model Is Used

When a chat is sent, the pipeline checks access again before calling the provider (documented in
`chat-completion-pipeline-and-generation-tasks.md`, section 3). Calls made straight to the
`/openai` and `/ollama` routes by non-admins are checked with
`backend/open_webui/utils/access_control/__init__.py:361-413`: an unregistered model, a model the
user cannot read, or a custom model whose base model they cannot read all answer HTTP 403
`Model not found`, and the server log records `Model access denied: user_id=... model_id=...
reason=model_read_denied` or `reason=model_unregistered`.

## 4. Key Concepts and Terminology

| Term | Meaning in MedIT GPT | Evidence |
|---|---|---|
| **Provider** | The outside service that runs a model (OpenAI, Azure OpenAI, Anthropic, an Ollama server, a llama.cpp or LM Studio server, a LiteLLM proxy, a Pipelines server). Which providers production uses is TO BE CONFIRMED | `src/lib/components/AddConnectionModal.svelte:360-370`, `:625-635` |
| **Connection** | One configured endpoint: a base URL plus key and options. Connections are kept as ordered lists; a connection is identified internally by its **position** (`url_idx`, 0 for the first), not by a name | `backend/open_webui/routers/openai.py:338-343`; `backend/open_webui/routers/ollama.py:235-238` |
| **OpenAI-compatible connection** | A connection that speaks the OpenAI API (`/models`, `/chat/completions`, `/embeddings`, `/responses`). Models from it are labelled `owned_by: openai` whatever the real vendor | `backend/open_webui/routers/openai.py:833-853` |
| **Ollama connection** | A connection to an Ollama server, which lists models at `/api/tags` and chats at `/api/chat`. Its models are labelled `owned_by: ollama` | `backend/open_webui/utils/models.py:35-50` |
| **Direct connection** | An OpenAI-compatible connection a user adds in their own Settings. Their browser fetches its models and makes the chat call; the server only relays | `src/lib/apis/index.ts:61-177`; `src/routes/+layout.svelte:646-731` |
| **Base model** | A model exactly as a connection (or a pipe function) offers it, before any MedIT GPT customization | `backend/open_webui/utils/models.py:58-66` |
| **Model record / custom model** | A row in the `model` table. Either an override of a base model with the same id (name, access, settings) or a new model built on a base model. Required before ordinary users can see a model (section 3.2) | `backend/open_webui/utils/models.py:167-267` |
| **Model list** | What `GET /api/models` returns to the picker: base models + arena models + custom models, filtered by access and ordered by the admin's order list | `backend/open_webui/main.py:897-943` |
| **Model registry** | The server's in-memory index of the current model list (`app.state.MODELS`), kept in Redis when the websocket manager is Redis. Chat requests look models up here | `backend/open_webui/utils/models.py:445-460`; `backend/open_webui/socket/main.py:133-185` |
| **Prefix ID** | Optional text the server puts in front of every model id from one connection (`{prefix}.{model}`) so that two connections offering the same model name do not collide; removed again before the provider is called | `backend/open_webui/routers/openai.py:747-750`, `:1556-1557`; `backend/open_webui/utils/model_ids.py:1-4` |
| **Model IDs** (allow-list) | Per-connection list of model ids. OpenAI-compatible: when filled, the server does **not** ask the provider for its list and offers exactly these ids. Ollama: filters the server's own list down to these ids | `backend/open_webui/routers/openai.py:697-718`; `backend/open_webui/routers/ollama.py:428-431` |
| **Tags** | Labels attached to every model from a connection; they appear as filter chips in the model picker | `backend/open_webui/routers/openai.py:752-753`; `backend/open_webui/main.py:922-926` |
| **Connection Type** | `Local` or `External`. Decides which **Task Model** setting is used for background jobs (titles, tags) and which filter chip (`Local`, `External`) shows the model in the picker. Default `External` for OpenAI-compatible, `Local` for Ollama | `src/lib/components/AddConnectionModal.svelte:265-268`; `backend/open_webui/utils/task.py:15-25`; `src/lib/components/chat/ModelSelector/Selector.svelte:359-368` |
| **Auth** | How the server authenticates to the provider: `None`, `Bearer` (the API key), `Session`, `OAuth`, `Entra ID` (section 5.2) | `src/lib/components/AddConnectionModal.svelte:409-462`; `backend/open_webui/routers/openai.py:184-212` |
| **API Type** | `Chat Completions` (default) or `Responses` (OpenAI's newer Responses API) | `src/lib/components/AddConnectionModal.svelte:464-489`; `backend/open_webui/routers/openai.py:1589` |
| **Provider** (connection option) | `Default`, `Azure OpenAI`, `llama.cpp`, `LM Studio` or `LiteLLM`; switches on vendor-specific behaviour (Azure URLs and keys, model management, Anthropic pass-through) | `src/lib/components/AddConnectionModal.svelte:616-638`; `backend/open_webui/routers/openai.py:244-262`; `backend/open_webui/utils/anthropic.py:131-136` |
| **Pipelines server** | An external Pipelines service added as an OpenAI-compatible connection; its row shows a Pipelines icon. Documented in `functions-pipes-filters-actions-and-pipelines.md` | `src/lib/components/admin/Settings/Connections.svelte:192-201`; `src/lib/components/admin/Settings/Connections/OpenAIConnection.svelte:68-89` |
| **Cache Base Model List** | Admin switch that keeps the merged provider list instead of asking every connection on each request (section 5.8) | `backend/open_webui/utils/models.py:84-106` |
| **Verify Connection** | Button in the connection pop-up that asks the provider for its model list (or Ollama version) without saving anything | `src/lib/components/AddConnectionModal.svelte:76-143`, `:374-397` |
| **Pull** | Ollama's word for downloading a model by tag (for example `mistral:7b`) from the Ollama library | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:162-296` |
| **Load / Unload** | Putting a model into, or taking it out of, the provider's memory. Unloading frees memory; the next request loads it again | `backend/open_webui/main.py:952-1064`; `backend/open_webui/routers/openai.py:993-1022` |
| **Modelfile / GGUF** | Ollama's recipe format for creating a model, and the single-file model format accepted by the upload tool | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:63`, `:956-1137` |
| **Arena model** | A pseudo-model for blind side-by-side evaluation, added to the list when evaluations are on (`evaluations-feedback-and-analytics.md`) | `backend/open_webui/utils/models.py:115-149` |
| **Pipe function** | An admin-installed Python function that acts as a model; part of the base list (`functions-pipes-filters-actions-and-pipelines.md`) | `backend/open_webui/utils/models.py:62-66` |

## 5. Workflows (Step by Step)

Tier 1 is read-only: the admin steps below are documented so that support can follow what an
admin did or describe what to check, not to be performed by tier 1.

### 5.1 Add an OpenAI-Compatible Connection (Admin)

1. Open **Settings > Admin > AI > Connections**. The **OpenAI API** switch (label text `OpenAI
   API`, key `settings.admin.connections.openaiApi.label`, `src/lib/i18n/locales/en-US/translation.json:2179`)
   must be on; when it is off the connection list is hidden and every OpenAI-compatible model
   leaves the model list (`src/lib/components/admin/Settings/Connections.svelte:243-300`;
   `backend/open_webui/utils/models.py:58-66`).
2. Beside **Manage OpenAI API Connections** (`translation.json:2177`) press **+** (tooltip `Add
   Connection`, `translation.json:2168`). The pop-up is titled `Add Connection`
   (`src/lib/components/AddConnectionModal.svelte:288-294`).
3. Type the **URL**: the provider's API base, normally ending in `/v1`, for example
   `https://api.openai.com/v1`. The field offers suggestions for OpenAI, Anthropic, Google Gemini's
   OpenAI-compatible endpoint, Mistral, Groq, OpenRouter and xAI
   (`src/lib/components/AddConnectionModal.svelte:340-370`). The server appends `/models`,
   `/chat/completions` and so on; a trailing `/` is removed on save (`:207-208`).
4. Choose **Auth** and, for `Bearer`, paste the API key into the `API Key` field (section 5.2).
5. Optionally press **Verify Connection** (the circular-arrows button) to test before saving
   (section 5.6). Saving does **not** require a successful verification.
6. Optionally open **Advanced** for the remaining options (section 5.2).
7. Press **Save**. The connection is appended to the list and the whole OpenAI-compatible
   configuration is saved at once; the pop-up closes, the toast `OpenAI API settings updated`
   appears and the admin's model list reloads
   (`src/lib/components/admin/Settings/Connections.svelte:56-91`, `:138-144`). On the server the
   save clears every model cache and publishes the `model.provider_config.updated` event
   (`backend/open_webui/routers/openai.py:556-597`).

Checks made on Save (`src/lib/components/AddConnectionModal.svelte:161-205`): an empty URL gives
`URL is required`; headers that are not a JSON object give `Headers must be a valid JSON object`;
Azure connections have three extra checks (section 5.3). Nothing else is validated, so a wrong
URL or key can be saved and will simply contribute no models.

### 5.2 Connection Options Reference

"System" means a connection on the admin Connections tab; "direct" means a user's own connection.

| Option (as labelled) | Shown for | What it does | Default | Evidence |
|---|---|---|---|---|
| `Connection Type`: `Local` / `External` (click to toggle) | System OpenAI and Ollama | Picks the Local or External **Task Model** for background jobs and the picker filter chip | `External` (OpenAI), `Local` (Ollama) | `src/lib/components/AddConnectionModal.svelte:316-338`, `:265-268`; `backend/open_webui/routers/openai.py:732`; `backend/open_webui/routers/ollama.py:425` |
| `URL` | All | Provider base URL | none | `src/lib/components/AddConnectionModal.svelte:340-372` |
| Enabled switch (screen-reader label `Toggle whether current connection is active.`; tooltip `Enabled` / `Disabled`) | All | When off, the server makes no request to the connection and its models leave the list | on | `src/lib/components/AddConnectionModal.svelte:399-406`; `backend/open_webui/routers/openai.py:697-720`; `backend/open_webui/routers/ollama.py:403-410` |
| `Auth`: `None` | All | No `Authorization` header; the pop-up shows `No authentication` | | `src/lib/components/AddConnectionModal.svelte:422`, `:442-445`; `backend/open_webui/routers/openai.py:190-191` |
| `Auth`: `Bearer` + `API Key` | All | Sends the key as `Authorization: Bearer ...` (Azure: in the `api-key` header; Anthropic's API: in `x-api-key`) | `Bearer` | `src/lib/components/AddConnectionModal.svelte:423`, `:436-441`; `backend/open_webui/routers/openai.py:187-189`, `:484-489`, `:1605-1609` |
| `Auth`: `Session` | System OpenAI-compatible and direct | Pop-up text: `Forwards system user session credentials to authenticate` | | `src/lib/components/AddConnectionModal.svelte:426`, `:446-449`; `backend/open_webui/routers/openai.py:192-193` |
| `Auth`: `OAuth` | System OpenAI-compatible | Pop-up text: `Forwards system user OAuth access token to authenticate` (for users signed in through single sign-on) | | `src/lib/components/AddConnectionModal.svelte:427-429`, `:450-453`; `backend/open_webui/routers/openai.py:194-206` |
| `Auth`: `Entra ID` | System OpenAI-compatible | Pop-up text: `Uses DefaultAzureCredential to authenticate`; the server obtains a Microsoft Entra ID token for Azure AI services from its own Azure identity | | `src/lib/components/AddConnectionModal.svelte:429`, `:454-457`; `backend/open_webui/routers/openai.py:208-233` |
| `API Type`: `Chat Completions` / `Responses` | System OpenAI-compatible | `Responses` converts chats to OpenAI's Responses API (`/responses`) and converts the answer back | `Chat Completions` | `src/lib/components/AddConnectionModal.svelte:464-489`; `backend/open_webui/routers/openai.py:1589`, `:1632-1636`, `:1740-1742` |
| `Forward cookies` | System OpenAI-compatible (under Advanced) | Help text: `Forward cookies from your Open WebUI request to this server.` | off | `src/lib/components/AddConnectionModal.svelte:514-530`; `backend/open_webui/routers/openai.py:163` |
| `Headers` | System OpenAI and Ollama (Advanced) | Extra request headers as a JSON object (tooltip `Enter additional headers in JSON format (e.g. {"X-Custom-Header": "value"}`). Values may contain placeholders such as `{{CHAT_ID}}`, `{{MESSAGE_ID}}`, `{{USER_ID}}`, `{{USER_NAME}}`, `{{USER_EMAIL}}`, `{{USER_ROLE}}`, `{{USER_GROUPS}}`, `{{USER_AGENT}}`, which the server fills in per request | empty | `src/lib/components/AddConnectionModal.svelte:532-558`; `backend/open_webui/utils/headers.py:107-163` |
| `Passthrough params` | System OpenAI-compatible (Advanced) | Tooltip: `Comma-separated top-level request parameters this upstream may receive without translation. Use * to allow all captured passthrough params.` Used by the Anthropic-compatible `/api/v1/messages` endpoint (`public-api-and-integrations.md`) | empty | `src/lib/components/AddConnectionModal.svelte:560-587`; `backend/open_webui/main.py:2035-2048`; `backend/open_webui/utils/anthropic.py:385-398` |
| `Prefix ID` | All (Advanced) | Tooltip: `Prefix ID is used to avoid conflicts with other connections by adding a prefix to the model IDs - leave empty to disable` | empty | `src/lib/components/AddConnectionModal.svelte:589-614`; `backend/open_webui/routers/openai.py:747-750` |
| `Provider`: `Default`, `Azure OpenAI`, `llama.cpp`, `LM Studio`, `LiteLLM` | System OpenAI-compatible (Advanced) | Azure handling (5.3); model management for llama.cpp and LM Studio (5.11); `LiteLLM` makes `/api/v1/messages` pass Anthropic requests through natively | `Default` | `src/lib/components/AddConnectionModal.svelte:616-638`; `backend/open_webui/utils/anthropic.py:131-136` |
| `API Version` | Azure only | Azure OpenAI API version | none (required) | `src/lib/components/AddConnectionModal.svelte:640-662` |
| `Model IDs` (`Add a model ID`, **+**, **-** to remove) | All (Advanced) | Allow-list (section 4). Hint when empty: `Leave empty to include all models from "{url}/models" endpoint` (OpenAI), `Leave empty to include all models from "{url}/api/tags" endpoint` (Ollama), `Deployment names are required for Azure OpenAI` (Azure). Adding a duplicate gives `Model ID is already added` | empty | `src/lib/components/AddConnectionModal.svelte:145-159`, `:664-743` |
| `Tags` | All (Advanced) | Labels applied to every model of the connection | empty | `src/lib/components/AddConnectionModal.svelte:745-771`; `backend/open_webui/routers/openai.py:752-753` |

Hovering over a saved row shows where chats are sent: `WebUI will make requests to
"{url}/chat/completions"` (OpenAI-compatible and direct) or `WebUI will make requests to
"{url}/api/chat"` (Ollama) (`src/lib/components/admin/Settings/Connections/OpenAIConnection.svelte:46-51`;
`src/lib/components/admin/Settings/Connections/OllamaConnection.svelte:49-55`). The tooltip does
not change for the `Responses` API type.

What the Session, OAuth, Entra ID, Forward cookies and header-placeholder options send to a
provider, and whether that is acceptable for a given provider, is a privacy and security question:
Security-sensitive: refer to the platform maintainer and U of T Information Security
(security.utoronto.ca). Note that header placeholders such as `{{USER_EMAIL}}` and `{{USER_NAME}}`
send personal data to the provider when an admin uses them.

### 5.3 Azure OpenAI Connections

- **Recognized** when **Provider** is `Azure OpenAI`, or, for a system connection left on
  `Default`, when the URL contains `azure.` or `cognitive.microsoft.com` and does not end in
  `/openai/v1` (`src/lib/components/AddConnectionModal.svelte:41-46`).
- **Required on Save** (`src/lib/components/AddConnectionModal.svelte:170-192`): an API version
  (`API Version is required`; the Advanced section opens), a key unless Auth is `Entra ID`
  (`Key is required`), and at least one deployment name in Model IDs (`Deployment names are
  required for Azure OpenAI`).
- **Model list.** Azure connections are never asked for a model list; the deployment names
  entered as Model IDs are the list (`backend/open_webui/routers/openai.py:697-718`, `:890-894`).
- **Requests.** Classic Azure URLs are sent to
  `{url}/openai/deployments/{deployment}/chat/completions?api-version={version}` (or `/responses`);
  URLs ending in `/openai/v1` use the standard `/chat/completions` path. The key goes in the
  `api-key` header unless Auth is `Entra ID`. Parameters Azure does not accept are dropped; for
  o-series and GPT-5-or-later models `max_tokens` becomes `max_completion_tokens` and a temperature
  other than 1 is removed. If no version is stored the server uses `2023-03-15-preview`
  (`backend/open_webui/routers/openai.py:1154-1248`, `:1605-1630`).
- A deployment name that is empty or contains `/`, `\` or `..` is refused with `Invalid model
  name: must not be empty or contain path separators or traversal sequences`
  (`backend/open_webui/routers/openai.py:1206-1218`).

### 5.4 Edit, Switch Off, Re-Enable and Remove a Connection (Admin)

- **Edit.** The gear button (tooltip `Configure`) on the row opens `Edit Connection`. The URL on
  the row itself is read-only; change it in the pop-up. **Save** saves immediately with the toast
  `OpenAI API settings updated` or `Ollama API settings updated`
  (`src/lib/components/admin/Settings/Connections/OpenAIConnection.svelte:25-43`, `:58-66`;
  `src/lib/components/admin/Settings/Connections.svelte:280-282`, `:338-340`).
- **Switch one connection off or on.** The switch on the row saves immediately; a switched-off row
  is greyed out (`src/lib/components/admin/Settings/Connections/OpenAIConnection.svelte:53-57`,
  `:107-115`). Its models leave the list for everyone at the next list build.
- **Switch a whole provider type off.** The **OpenAI API** or **Ollama API** switch (`translation.json:2179`,
  `:2178`) saves immediately. All models of that type disappear, and calls made directly to that
  router answer `OpenAI API is disabled` or `The Ollama API is disabled. Please enable it to use
  this feature.` (HTTP 503) (`backend/open_webui/routers/openai.py:870-871`, `:1492-1493`;
  `backend/open_webui/routers/ollama.py:492-493`; `backend/open_webui/constants.py:103`).
- **Remove.** In the Edit pop-up press **Delete**, then confirm `Are you sure you want to delete
  this connection? This action cannot be undone.`; the removal is saved immediately
  (`src/lib/components/AddConnectionModal.svelte:776-787`, `:812-822`;
  `src/lib/components/admin/Settings/Connections.svelte:283-295`).
- **Positions shift.** Connections are identified by position, so removing one moves every later
  connection up one place, together with its options (`src/lib/components/admin/Settings/Connections.svelte:289-293`;
  `backend/open_webui/routers/openai.py:565-566`). Pop-ups that address a connection by number
  (Manage Ollama, Manage Models) should be reopened after a removal.
- **The Save button** at the bottom of the tab re-saves both lists and can show three toasts:
  `OpenAI API settings updated`, `Ollama API settings updated` and `Settings saved successfully!`
  (`src/lib/components/admin/Settings/Connections.svelte:214-221`;
  `src/lib/components/chat/SettingsModal.svelte:857-862`).
- **After removal or switch-off**, model records built on that connection's models stay in the
  database but their base model is gone, so chats using them fail with `Model not found` (unless
  the fallback setting described in `chat-completion-pipeline-and-generation-tasks.md` is on).
  Existing chat history is not changed (`backend/open_webui/main.py:1127-1182`).

### 5.5 Add and Configure an Ollama Connection (Admin)

1. Make sure **Ollama API** is on, then press **+** beside **Manage Ollama API Connections**
   (`translation.json:2176`) (`src/lib/components/admin/Settings/Connections.svelte:302-330`).
2. The pop-up is the same `Add Connection` form with fewer options: `Connection Type` (default
   `Local`), `URL`, Verify Connection, the Enabled switch, `Auth` (`None` or `Bearer` only) and,
   under Advanced, `Headers`, `Prefix ID`, `Model IDs` and `Tags`. There is no Provider, API Type,
   Forward cookies or Passthrough params (`src/lib/components/AddConnectionModal.svelte:409-432`,
   `:513-638`).
3. **Save** adds the server and saves at once (`Ollama API settings updated`); the key is kept
   with that connection's options (`src/lib/components/admin/Settings/Connections.svelte:146-154`;
   `src/lib/components/admin/Settings/Connections/OllamaConnection.svelte:26-44`).
4. Under the list the screen shows `Trouble accessing Ollama?` (`translation.json:2175`) with the
   link `Click here for help.` to the upstream project's troubleshooting page
   (`src/lib/components/admin/Settings/Connections.svelte:355-364`); whether users should be
   pointed at upstream resources is TO BE CONFIRMED (ground truth, Contacts).

How several Ollama servers behave together:

- The same model on two or more servers appears **once** in the list; each request picks one of
  the servers that have it **at random** (`backend/open_webui/routers/ollama.py:355-370`,
  `:1080-1095`). If one of those servers is broken, failures are intermittent.
- `Model IDs` on an Ollama connection filters that server's own list down to the listed ids
  (`backend/open_webui/routers/ollama.py:428-431`).
- Custom headers are sent on chat and OpenAI-compatible calls to Ollama, not on the model-list,
  version or management calls (`backend/open_webui/routers/ollama.py:127-129`, `:403-410`,
  `:1162-1172`).
- The model list also asks each server which models are loaded (`/api/ps`) so the picker can
  show them as loaded (`backend/open_webui/routers/ollama.py:445-454`;
  `backend/open_webui/utils/models.py:45`).

### 5.6 Verify Connection: What It Checks and What It Says

Verify does not save anything and only checks that the provider will list models (or, for
Ollama, report its version). A connection can verify successfully and still fail in chat (for
example a key with listing rights but no access to a particular model), and a provider that does
not offer a model list can fail Verify yet chat correctly when `Model IDs` are filled in.

| Connection | Request made | On success | On failure | Evidence |
|---|---|---|---|---|
| System OpenAI-compatible (Default, LiteLLM, llama.cpp, LM Studio) | Server: `GET {url}/models` with the chosen Auth and Headers, 10-second limit | `Server connection verified` | Provider answered with an error: the server passes the provider's status and body through and the pop-up shows `OpenAI: {provider message}` when the body is OpenAI-style (`error.message`), otherwise `OpenAI: Network Problem`. No answer, DNS, TLS or timeout: the server answers `Open WebUI: Server Connection Error` and the pop-up shows `OpenAI: Network Problem` | `backend/open_webui/routers/openai.py:1125-1151`; `src/lib/apis/openai/index.ts:361-387`; `src/lib/components/AddConnectionModal.svelte:112-134` |
| Azure | Server: `GET {url}/openai/models?api-version={version}` (or `{url}/models` for `/openai/v1` URLs) | `Server connection verified` | As above | `backend/open_webui/routers/openai.py:1084-1117` |
| URL containing `api.anthropic.com` | Server: Anthropic's paged model list with `x-api-key` | `Server connection verified` | `OpenAI: Network Problem` (the server's error detail is not shown) | `backend/open_webui/routers/openai.py:1118-1124`; `backend/open_webui/utils/anthropic.py:40-104` |
| Ollama | Server: `GET {url}/api/version` with `Bearer` key if given | `Server connection verified` | Always `Ollama: Network Problem`; the real reason is only in the server log (`Client error: ...` or `Unexpected error: ...`) | `backend/open_webui/routers/ollama.py:253-286`; `src/lib/apis/ollama/index.ts:17-28`; `src/lib/components/AddConnectionModal.svelte:76-90` |
| Direct (user) | The **browser** calls `GET {url}/models` with `Authorization: Bearer {key}` | `Server connection verified` | `OpenAI: {provider message}` or `OpenAI: Network Problem`; a provider that does not allow browser requests from MedIT GPT's address (CORS) shows `OpenAI: Network Problem` | `src/lib/apis/openai/index.ts:340-360` |

Other Verify messages: an empty URL gives `OpenAI: URL is required`
(`src/lib/apis/openai/index.ts:333-335`); headers that are not a JSON object give `Headers must be
a valid JSON object` before any request is made (`src/lib/components/AddConnectionModal.svelte:98-110`).

### 5.7 How the Model List Is Built

1. **The browser asks.** When the app loads, the browser calls `GET /api/models` once (and again
   after admin actions such as saving a connection). If that call fails, only the browser console
   records `Failed to load models:` (no message on screen)
   (`src/routes/(app)/+layout.svelte:83-90`, `:213-229`).
2. **Cache check.** If **Cache Base Model List** is on and a cached list exists, it is used and
   steps 3 to 5 are skipped (section 5.8) (`backend/open_webui/utils/models.py:84-98`).
3. **Base models are fetched in parallel** (`backend/open_webui/utils/models.py:58-66`): pipe
   functions, the OpenAI-compatible list (only if **OpenAI API** is on) and the Ollama list (only
   if **Ollama API** is on).
4. **OpenAI-compatible list** (`backend/open_webui/routers/openai.py:676-861`):
   - switched-off connections are skipped; connections with `Model IDs` are listed from those ids
     without contacting the provider; every other connection is asked for `{url}/models`
     (Anthropic's API through its own paged list) with a 10-second limit;
   - a connection that errors or times out returns nothing; the server log shows `Connection
     error: {e}` (`:116-119`);
   - prefix, tags, connection type and provider are applied to each model;
   - on connections whose host is `api.openai.com`, models whose id contains `babbage`, `dall-e`,
     `davinci`, `embedding`, `tts` or `whisper` are dropped (`:80`, `:813-831`);
   - **if two connections offer the same model id, the first connection in the list wins** and the
     later one's copy is dropped, unless a Prefix ID makes the ids different (`:833`).
5. **Ollama list** (`backend/open_webui/routers/ollama.py:384-457`): each enabled server's
   `/api/tags` (10-second limit), filtered by `Model IDs`, prefixed and tagged; the same model on
   several servers is merged into one entry; loaded state is added from `/api/ps`.
6. **Last good list.** If the fresh fetch produced nothing at all (for example every provider is
   down), the server keeps serving the last list it held in memory
   (`backend/open_webui/utils/models.py:99-106`). Models can therefore still be listed while their
   provider is unreachable; they fail only when used.
7. **Arena models** are added when evaluations are on (`backend/open_webui/utils/models.py:115-149`).
8. **Model records are applied** (`backend/open_webui/utils/models.py:167-267`): a record with the
   same id as a base model renames and configures it, and a record marked **inactive removes the
   base model from the list**; records built on a base model are added as their own entries (the
   base is found by exact id, or for Ollama by name without the `:tag`).
9. **Global model defaults** (`models.default_metadata`) fill in missing metadata, and
   capabilities are merged (`backend/open_webui/utils/models.py:337-356`).
10. **Actions and filters** (functions) are attached, and the model registry is replaced
    (`backend/open_webui/utils/models.py:385-460`).
11. **`/api/models` finishes** (`backend/open_webui/main.py:897-943`): filter pipelines are
    removed, duplicate ids collapse to the last entry, the access filter of section 3.2 runs, tags
    are combined, and models are sorted by the admin's order list (`ui.model_order_list`).
12. **The browser adds direct-connection models** when Direct Connections is on (section 5.12).

### 5.8 Caching and Refreshing the Model List

| Mechanism | What it holds | How long | Cleared by | Evidence |
|---|---|---|---|---|
| Per-provider result cache | Each user's OpenAI-compatible and Ollama lists | `MODELS_CACHE_TTL` seconds, default **1** | Expiry; connection saves; Refresh | `backend/open_webui/routers/openai.py:790-795`; `backend/open_webui/routers/ollama.py:384-389`; `backend/open_webui/env.py:1035-1043` |
| **Cache Base Model List** (`models.base_models_cache`, default **off**) | The merged base list (step 3 to 6 above), shared by all users | Until cleared | **Refresh** button (asks with `?refresh=true`); saving OpenAI or Ollama connections; llama.cpp or LM Studio download, load, unload or delete; restart | `backend/open_webui/utils/models.py:76-106`; `backend/open_webui/routers/openai.py:346-357`, `:966`, `:1005`, `:1021`, `:1048`; `backend/open_webui/routers/ollama.py:324-334` |
| Where the base list is kept | In Redis (key `{REDIS_KEY_PREFIX}:models:base`) when the server has a Redis connection, otherwise in each server process's memory | | | `backend/open_webui/utils/models.py:32`, `:84-106`; `backend/open_webui/main.py:390` |
| Startup pre-fetch | When the cache switch is on, the list is built during startup; failure logs `Failed to pre-fetch models at startup: {e}` and startup continues | | | `backend/open_webui/main.py:407-429` |
| Model registry | The current full list used to resolve chat requests | Replaced at every list build | | `backend/open_webui/utils/models.py:445-460` |

The admin screen describes the cache as `Base Model List Cache speeds up access by fetching base
models only at startup or on settings save—faster, but may not show recent base model changes.`
(label `Cache Base Model List`, `translation.json:2169-2170`). The **Refresh** button (tooltip
`Refresh`, `translation.json:2180`) is shown only while the cache is on; it rebuilds the list and
shows `Model list refreshed` (`src/lib/components/admin/Settings/Connections.svelte:125-136`,
`:386-418`).

Consequences read from the code (to confirm in a test environment):

- With the cache on, an Ollama model that was just **pulled, created or deleted** does not change
  the list until someone presses Refresh: the Ollama management endpoints do not clear the cache
  and the management screens reload the list without the refresh flag
  (`backend/open_webui/routers/ollama.py:652-838`;
  `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:277-282`, `:459-464`).
- With the cache on and **no Redis**, each server process keeps its own copy; a save or Refresh
  clears only the process that handled it, so with several processes users can see different
  lists until each process is refreshed or restarted (`backend/open_webui/utils/models.py:96-97`;
  `backend/open_webui/routers/openai.py:346-357`). Whether production runs several processes and
  Redis is TO BE CONFIRMED (ground truth).
- With the cache on, the shared list is built with the credentials of whichever request rebuilt it
  (or none at startup). Connections whose model list depends on the signed-in user (Auth
  `Session` or `OAuth`) can therefore show one person's view to everyone
  (`backend/open_webui/utils/models.py:100-104`; `backend/open_webui/routers/openai.py:184-206`).

### 5.9 Why a Model Can Be Missing From the List

Work down this list; most causes need an admin to confirm.

| # | Cause | Who it affects | How to recognize it | Evidence |
|---|---|---|---|---|
| 1 | The model was never **shared**: it has no model record, or the record is not Public or shared with the user's groups | Non-admin users only; admins still see it | Admin sees the model, user does not | `backend/open_webui/utils/models.py:524-578` |
| 2 | The model record is **switched off** (inactive) in Settings > Admin > AI > Models | Everyone | Model shows as disabled in the admin Models list | `backend/open_webui/utils/models.py:207-208` |
| 3 | The **connection** is switched off, or the whole **OpenAI API** / **Ollama API** type is off | Everyone | Row greyed out, or the switch is off | `backend/open_webui/routers/openai.py:697-720`; `backend/open_webui/utils/models.py:58-66` |
| 4 | The provider **did not answer within 10 seconds** or returned an error (wrong URL, expired key, outage, network or certificate problem) | Everyone, for that connection's models | Verify Connection fails; server log `Connection error: ...` | `backend/open_webui/routers/openai.py:89-119`; `backend/open_webui/routers/ollama.py:69-94`; `backend/open_webui/env.py:656-663` |
| 5 | **Model IDs** allow-list on the connection does not include the model | Everyone | The connection's Advanced section lists ids | `backend/open_webui/routers/openai.py:697-718`; `backend/open_webui/routers/ollama.py:428-431` |
| 6 | **Duplicate id**: an earlier OpenAI-compatible connection offers the same id, so this connection's copy is dropped | Everyone | Same model name on two connections without a Prefix ID | `backend/open_webui/routers/openai.py:833` |
| 7 | **OpenAI filter**: on `api.openai.com`, ids containing `babbage`, `dall-e`, `davinci`, `embedding`, `tts` or `whisper` are never listed | Everyone | Model id contains one of those words | `backend/open_webui/routers/openai.py:80`, `:829-831` |
| 8 | **Cache**: Cache Base Model List is on and nobody has pressed Refresh since the model appeared | Everyone | The model is on the provider but not in the list | Section 5.8 |
| 9 | The user's **page is stale**: the browser loads the list once per page load | One user | Reloading the page fixes it | `src/routes/(app)/+layout.svelte:213-229` |
| 10 | The model is a **filter pipeline**, which is never offered as a chat model | Everyone | Pipelines server | `backend/open_webui/main.py:902-905` |
| 11 | The model is **hidden** in the picker (hidden models are filtered by the picker, not the server) | Everyone | See `workspace-models-and-model-access.md` | `src/lib/components/chat/ModelSelector/Selector.svelte:310` |
| 12 | A **direct connection** failed (provider down, wrong key, CORS) or Direct Connections was switched off | That user | No `Direct` filter chip in the picker | `src/lib/apis/index.ts:61-177`; `src/lib/components/chat/ModelSelector/Selector.svelte:366-368` |
| 13 | The model was **removed at the provider** (deleted from Ollama, retired by the vendor, Azure deployment deleted) | Everyone | Provider no longer lists it | Provider behaviour, outside the repository |

### 5.10 Ollama Model Management (Admin)

**Where.** The **Manage** download icon on an Ollama connection row opens `Manage Ollama` for that
server; **Settings > Admin > AI > Models > Actions > Manage** opens `Manage Models`, where the admin
picks a server under `Select an Ollama instance`
(`src/lib/components/admin/Settings/Connections/OllamaConnection.svelte:46`, `:71-81`;
`src/lib/components/admin/Settings/Models/Manage/ManageMultipleOllama.svelte:13-31`). If the
server's model list cannot be read, the pop-up shows `Failed to fetch models`
(`src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:591-601`, `:1142-1145`).

| Task | Steps and what the admin sees | Evidence |
|---|---|---|
| **Pull a model** | Under `Pull a model from Ollama.com`, type a tag in `Enter model tag (e.g. mistral:7b)` and press `Pull Model`. A leading `ollama run` or `ollama pull` is removed. A progress bar shows the percentage and the layer digest, with a cancel (x) button. Success: `Model '{modelName}' has been successfully downloaded.` Failure: the error text as a pop-up, then `Download canceled`. The help line `To access the available model names for downloading, click here.` links to the Ollama library | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:162-296`, `:619-725`, `:764-820`; `backend/open_webui/routers/ollama.py:652-677` |
| Limits on pulling | The same tag twice: `Model '{modelTag}' is already in queue for downloading.` More than three at once: `Maximum of 3 models can be downloaded simultaneously. Please try again later.` Both limits are counted in the admin's browser, not on the server | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:45`, `:165-178` |
| Cancel a pull | The x button stops the download, asks the server to delete the partly downloaded model and shows `{model} download has been canceled` | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:480-494` |
| **Update all models** | The `Update All Models` button re-pulls every model on that server one after another. Pop-ups (English only, not translated): `Checking for model updates...`, then `All models are up to date`, or `Model update cancelled` after pressing cancel; progress shows `Updating "{modelId}"` with a percentage. Individual failures are not reported on screen | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:78-160`, `:727-762` |
| **Delete a model** | Under `Delete a model`, choose in `Select a model` (each entry shows the name and size in GB), press `Delete Model`, confirm `Confirm your action` / `This action cannot be undone. Do you wish to continue?`. Success: `Deleted {deleteModelTag}`. Only that Ollama server is affected; MedIT GPT model records built on the model remain and will fail with `Model not found` | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:449-470`, `:823-865`; `src/lib/components/common/ConfirmDialog.svelte:139-154`; `backend/open_webui/routers/ollama.py:798-838` |
| **Create a model** | Under `Create a model`, type a name in `Enter model tag (e.g. my-modelfile)` and a JSON body (placeholder `e.g. {"model": "my-modelfile", "from": "ollama:7b"})`), press `Create Model`. Text that is not valid JSON produces the browser's parse error as a pop-up; Ollama's status lines appear as success pop-ups, with a progress bar while layers are written | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:496-589`, `:867-941`; `backend/open_webui/routers/ollama.py:729-750` |
| **Upload a GGUF model** (marked Experimental; `Show` / `Hide`) | `Upload a GGUF model` in `File Mode` (a `.gguf` or `.safetensors` file from the admin's computer, `Click here to select`) or `URL Mode` (`Type Hugging Face Resolve (Download) URL`); the editable `Modelfile Content`; `Upload Model`; `Upload Progress`. URL mode accepts only addresses starting with `https://huggingface.co/` or `https://github.com/`, otherwise `Invalid file_url. Only URLs from allowed hosts are permitted.` The file passes through the server's upload folder and is removed after it reaches Ollama | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:298-447`, `:943-1137`; `backend/open_webui/routers/ollama.py:1550-1723` |
| Upload outcome | File mode: the server itself creates the model, named after the file without its extension; failures are `Ollama: Could not create blob, Please try again.` or `Failed to create model in Ollama. {resp_text}`. URL mode: the server only stores the file in Ollama; the follow-up "create" request the browser sends does not match the current API helper's parameters, so a URL-mode upload may end without a usable model and without an error (read from code, TO BE CONFIRMED in a test environment) | `backend/open_webui/routers/ollama.py:1590-1601`, `:1680-1721`; `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:370-376`; `src/lib/apis/ollama/index.ts:348-372` |
| **Unload a model** | The **Eject** button (tooltip `Eject`, screen-reader label `Eject model`) that appears beside a loaded model in the chat model picker, for admins only (`src/lib/components/chat/ModelSelector/ModelItem.svelte:281-297`); it calls `/api/models/unload`. Success: `Model unloaded successfully`; failure: `Error unloading model: {error}`. For Ollama the server asks every server hosting the model to unload it (`keep_alive` 0); for llama.cpp it calls `/models/unload`; other providers answer `Provider "{provider}" does not support model unloading` (`default` when no provider is set). Unknown model: `Model "{model_id}" not found`. Partial failure: `Failed to unload model on {n} node(s): {errors}` | `src/lib/components/chat/ModelSelector/Selector.svelte:791-806`; `src/lib/apis/index.ts:183-212`; `backend/open_webui/main.py:952-1064` |
| **Pull from the model picker** | An admin who types a name in the picker sees `Pull "{searchValue}" from Ollama.com`; it always pulls into the **first** Ollama connection. The same limits and messages as the Pull tool apply, and each Ollama status line appears as a success pop-up | `src/lib/components/chat/ModelSelector/Selector.svelte:312-326`, `:460-587` |
| Copy and push | Available only through the API (`/ollama/api/copy`, `/ollama/api/push`); no screen uses them | `backend/open_webui/routers/ollama.py:688-795` |

Whether a pull continues if the admin closes the browser tab depends on Ollama's behaviour when
the request is cut off and is TO BE CONFIRMED; the progress is only shown in the tab that started
it (`src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:190-266`).

### 5.11 llama.cpp and LM Studio Model Management (Admin)

These tools apply to OpenAI-compatible connections whose **Provider** is `llama.cpp` or
`LM Studio`. The management address is the connection URL with a trailing `/v1`, `/api/v1` or
`/api/v0` removed (`backend/open_webui/routers/openai.py:244-272`).

- **Open** Settings > Admin > AI > Models > Actions > Manage. With neither Ollama nor such a
  connection the pop-up shows `No inference engine with management support found`; with both,
  choose under `Select an engine` between `Ollama` and `Model providers`; then pick a server under
  `Select an instance` (shown as `{provider} - {url}`)
  (`src/lib/components/admin/Settings/Models/ManageModelsModal.svelte:24-137`;
  `src/lib/components/admin/Settings/Models/Manage/ManageMultipleProviderModels.svelte:31-55`).
- **List**: each model shows a status chip (`loaded`, `sleeping`, `loading`, `downloading`,
  `unloaded` or `available`); an empty list shows `No models found`; **Refresh** reloads it
  (`src/lib/components/admin/Settings/Models/Manage/ManageProviderModels.svelte:66-111`, `:192-300`).
- **Download**: type a reference in `Type a model ref` and press `Download Model`; the pop-up
  says `Model download started`. From the model picker, admins see `Download "{searchValue}" from
  {provider}`, and progress is polled every 1.5 seconds; a failed job reports the provider's error
  or `Download failed` (`src/lib/components/admin/Settings/Models/Manage/ManageProviderModels.svelte:141-147`;
  `src/lib/components/chat/ModelSelector/Selector.svelte:593-711`).
- **Load** (`Load Model`) gives `Model loaded successfully`; **Unload** (`Unload Model`) gives
  `Model unloaded successfully`; **Delete** (`Delete Model`, llama.cpp only) asks `Delete Model` /
  `This will delete the cached model and cannot be undone.` and then `Model deleted successfully`
  (`src/lib/components/admin/Settings/Models/Manage/ManageProviderModels.svelte:149-190`;
  `src/lib/components/admin/Settings/Models/Manage/ManageMultipleProviderModels.svelte:19`).
- **Errors** appear as a pop-up with the server's or provider's message (fallback `Server
  connection failed`) (`src/lib/apis/openai/index.ts:3-14`). Server messages: `Provider
  "{provider}" does not support model management` (HTTP 400; `default` when no provider is set),
  `Provider "{provider}" does not support {operation}` (for example `delete` on LM Studio),
  `Connection not found` (HTTP 404) and `OpenAI API is disabled` (HTTP 503)
  (`backend/open_webui/routers/openai.py:360-385`). Errors from the provider are passed through
  with its status code (`:426-431`).
- Each successful download, load, unload or delete clears the model caches and, for download and
  delete, publishes `model.provider_model.created` or `model.provider_model.deleted`
  (`backend/open_webui/routers/openai.py:954-1056`).

### 5.12 Direct Connections (Users' Own Providers)

**Admin switch.** Settings > Admin > AI > Connections > **User Connections** (`translation.json:2181`)
> **Direct Connections** (`translation.json:2172`), described as `Direct Connections allow users
to connect to their own OpenAI compatible API endpoints.` (`translation.json:2171`). It saves at
once with `Connections settings updated` (`src/lib/components/admin/Settings/Connections.svelte:113-123`,
`:369-384`). Setting `direct.enable`, environment seed `ENABLE_DIRECT_CONNECTIONS`, code default
**off** (`backend/open_webui/config.py:230`, `:2823`). The server tells signed-in browsers the value
as `features.enable_direct_connections` (`backend/open_webui/main.py:2351`).

**What the switch changes** (read from the code): the browser shows the personal Connections tab
and adds direct-connection models to the model list only while the feature flag is on
(`src/lib/components/chat/SettingsModal.svelte:381-383`;
`src/routes/(app)/+layout.svelte:83-90`). Switching it off does not delete anyone's saved
connections; they are simply no longer used.

**User steps.**

1. Settings > Personal > Services > **Connections** (`translation.json:2800`). The section
   `Direct Connections` (`translation.json:2799`) says `Connect to your own OpenAI compatible API
   endpoints.` (`translation.json:2797`), with two notes underneath: `Connections managed through
   the Admin Panel are recommended for everyday use. Direct connections provide convenient access
   to your own endpoints, but rely on your browser session to keep requests running, making them
   better suited to testing and temporary use.` and `CORS must be properly configured by the
   provider to allow requests from Open WebUI.` (`src/lib/components/chat/Settings/Connections.svelte:75-152`).
2. Press **+** (`Add Connection`, `translation.json:2798`). The pop-up has `URL`, Verify
   Connection, the Enabled switch, `Auth` (`None`, `Bearer`, `Session`) with `API Key`, and under
   Advanced `Prefix ID`, `Model IDs` and `Tags`; there is no Connection Type, API Type, Provider,
   Headers, Forward cookies or Passthrough params (`src/lib/components/AddConnectionModal.svelte:316`,
   `:425-431`, `:464`, `:514`, `:532`, `:560`, `:616`).
3. **Save** in the pop-up adds the connection and saves at once with `Settings saved successfully!`
   (`src/lib/components/chat/Settings/Connections.svelte:21-55`;
   `src/lib/components/chat/SettingsModal.svelte:811-817`). Edits made through the gear button and
   the Enabled switch also save at once.
4. **Deleting** a connection (Edit pop-up > `Delete` > confirm) removes it from the screen but does
   **not** save until the user presses the tab's **Save** button; leaving without saving brings it
   back next time (`src/lib/components/chat/Settings/Connections.svelte:115-128`, `:162-169`).

The connections are saved with the user's personal settings, so they follow the account to other
browsers (`src/lib/components/chat/SettingsModal.svelte:438-451`). How the saved key is protected
is security-sensitive (section 14).

**How models are listed.** After the server list arrives, the browser itself asks each enabled
direct connection for `{url}/models` (or uses its `Model IDs`), adds the prefix and tags, and marks
the models as direct; a connection that fails adds nothing and shows no message. Only connections
that have saved options are used. If a direct model has the same id as a server model, the two
entries are merged (`src/lib/apis/index.ts:61-177`). The picker then offers a `Direct` filter
chip (`src/lib/components/chat/ModelSelector/Selector.svelte:366-368`).

**How a chat is answered.** The browser sends the model's definition with the message; the server
marks the request as direct and asks the **same browser tab**, over the websocket, to call
`{url}/chat/completions` with the user's key (prefix removed). The tab streams the provider's reply
back line by line and the server passes it on as usual (`backend/open_webui/main.py:1097-1105`,
`:1161-1163`; `backend/open_webui/utils/chat.py:49-145`; `src/routes/+layout.svelte:646-731`). For
direct connections the browser always sends the key field as a `Bearer` token, whatever Auth was
chosen (`src/routes/+layout.svelte:654-670`; `src/lib/apis/openai/index.ts:392-419`).

**What breaks without a live browser tab.**

| Situation | Result | Evidence |
|---|---|---|
| Request made without a browser session (automation, timer, scheduled task, API script, some background jobs) | `Direct connection requires an active WebSocket session; cannot generate completion in this context (e.g. background task).` | `backend/open_webui/utils/chat.py:63-68`; `backend/open_webui/socket/main.py:1283-1286` |
| The tab that sent the message has closed or lost its connection | The error text contains `Client session disconnected.` | `backend/open_webui/socket/main.py:1263-1266`; `backend/open_webui/utils/chat.py:126-128` |
| `WEBSOCKET_EVENT_CALLER_TIMEOUT` is set and the tab does not answer in time | `Event call timed out. The browser tab may be inactive or closed.` | `backend/open_webui/socket/main.py:1277-1281`; `backend/open_webui/env.py:534-542` |
| Sub-agent delegation from a direct model | `Error: sub-agents are unavailable for direct connections.` (`chat-completion-pipeline-and-generation-tasks.md`) | `backend/open_webui/utils/subagents.py:334` |
| The provider refuses the browser's request (wrong key, CORS, outage) | The browser hands its error object back; the exact text shown is not established | `src/routes/+layout.svelte:718-726`; section 14 |

### 5.13 How a Chat Request Reaches the Provider

The pipeline that leads up to this point is documented in
`chat-completion-pipeline-and-generation-tasks.md`, section 5.4. What this area adds:

- **OpenAI-compatible** (`backend/open_webui/routers/openai.py:1486-1754`): the model is looked up
  in the server's list (refreshing it if missing); the prefix is removed; the model record's
  parameters and system prompt are applied; reasoning models (`o1`, `o3` and later, GPT-5 and
  later) get `max_tokens` renamed to `max_completion_tokens` and the system message turned into a
  developer message (`o1-mini` and `o1-preview`: a user message); other providers get
  `max_completion_tokens` renamed back to `max_tokens` unless the URL is `api.openai.com`; the
  request goes to `/chat/completions`, or `/responses` for the Responses API type, or the Azure
  paths of section 5.3. For llama.cpp, pressing **Continue** sends flags so the model continues
  its last message (`:1591-1603`).
- **Pipelines** connections receive the user's name, id, email and role in the request body
  (`backend/open_webui/routers/openai.py:1559-1566`); see `functions-pipes-filters-actions-and-pipelines.md`.
  This is personal data sent to the Pipelines server.
- **OpenRouter**: requests to `openrouter.ai` carry upstream identification headers that the
  licence protects (`backend/open_webui/routers/openai.py:163-177`).
- **Ollama** (`backend/open_webui/routers/ollama.py:1098-1172`): one of the servers hosting the
  model is chosen at random; the prefix is removed; the answer streams back as Ollama's own format
  and the pipeline converts it.
- **User information headers.** When the environment variable `ENABLE_FORWARD_USER_INFO_HEADERS`
  is on (default **off**), every provider call also carries the user's name, id, email and role
  (and the chat id) in `X-OpenWebUI-*` headers (`backend/open_webui/env.py:989-996`;
  `backend/open_webui/utils/headers.py:52-82`). The production value is TO BE CONFIRMED.
- **Timeouts.** Chat calls have **no overall time limit** unless `AIOHTTP_CLIENT_TIMEOUT` is set,
  and no limit on silence between streamed pieces unless `AIOHTTP_CLIENT_STREAM_IDLE_TIMEOUT` is set
  (`backend/open_webui/env.py:608-624`; `backend/open_webui/utils/session_pool.py:43-51`). Model
  lists and Verify use the 10-second `AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST`.
- **Network path.** Outbound provider calls honour the server's proxy environment settings and
  verify TLS certificates according to `AIOHTTP_CLIENT_SESSION_SSL` (default on)
  (`backend/open_webui/utils/session_pool.py:72-76`; `backend/open_webui/env.py:628-631`).

### 5.14 Provider Errors: How They Reach the User

When a provider answers with an error, the OpenAI-compatible route returns the provider's status
and body instead of raising; the pipeline turns that into a failure whose text is the provider's
own message (the first `error`, `message` or `detail` it finds), or `Provider returned HTTP
{status_code}` when the body cannot be read (`backend/open_webui/routers/openai.py:1671-1738`;
`backend/open_webui/main.py:1659-1665`; `backend/open_webui/utils/misc.py:43-65`). The chat shows it
as a pop-up and in the grey error box (`src/lib/components/chat/Chat.svelte:3716-3747`; display
details in `chat-completion-pipeline-and-generation-tasks.md`). At the same time the server logs
one line and publishes a `model.provider_request.failed` event (section 9).

| Situation | What the user sees | Server log classification (`error_type`) | Evidence |
|---|---|---|---|
| Provider rejects the key (HTTP 401 or 403) | The provider's message, for example an "invalid API key" sentence in the provider's words | `authentication_failed` | `backend/open_webui/events.py:1224-1229` |
| Rate limit or quota (HTTP 429) | The provider's rate-limit or quota message | `rate_limited` | `backend/open_webui/events.py:1230-1231` |
| Model unknown at the provider (HTTP 404 whose text mentions model not found, does not exist or no such model) | The provider's message | `model_not_found` | `backend/open_webui/events.py:1224-1227` |
| Provider failure (HTTP 500 and above) | The provider's message, or `Provider returned HTTP {status_code}` | `server_failed` | `backend/open_webui/events.py:1232-1233`; `backend/open_webui/utils/misc.py:43-46` |
| Other refusals (content filter, bad parameter, context too long) | The provider's message | `upstream_error` | `backend/open_webui/events.py:1234` |
| No answer at all: DNS, refused connection, TLS failure, or a configured timeout | `Open WebUI: Server Connection Error` | (no `Upstream` line; the exception is logged) | `backend/open_webui/routers/openai.py:1745-1751`; `backend/open_webui/constants.py:130` |
| Ollama answers with an error | Ollama's `error` text; if the body is not JSON, `Open WebUI: Server Connection Error`; a failure before any answer, `Ollama: {error}` | Ollama line from `publish_model_provider_request_failed` | `backend/open_webui/routers/ollama.py:140-194` |
| Provider type switched off | `OpenAI API is disabled` or `The Ollama API is disabled. Please enable it to use this feature.` | none | `backend/open_webui/routers/openai.py:1492-1493`; `backend/open_webui/routers/ollama.py:1107-1108` |
| Model no longer in the server's list | `Model not found` or `Model '' was not found` (`chat-completion-pipeline-and-generation-tasks.md`) | none | `backend/open_webui/routers/openai.py:1546-1552`; `backend/open_webui/main.py:1128-1129` |

The log line reads `Upstream {provider} request failed: HTTP {status} ({error_type}) url={base_url}
model={model} code={code} message={message}` at warning level, or error level for status 500 and
above (`backend/open_webui/events.py:1239-1249`). It contains the connection URL, the model and
the provider's message; it is the fastest way for an admin to tell a bad key from a rate limit.

### 5.15 The Embeddings Endpoint

`POST /api/embeddings` (alias `/api/v1/embeddings`) accepts an OpenAI-style body (`model`,
`input`) from any signed-in user, typically a script with an API key
(`backend/open_webui/main.py:1072-1094`; `backend/open_webui/utils/embeddings.py:24-88`):

1. The model must be in the server's current model list. If not, the code raises a plain error
   with the text `Model not found`, which reaches the caller as an unhandled server error
   (HTTP 500); the exact body is produced by the web framework and is TO BE CONFIRMED.
2. Role `user` callers need read access to the model, as in section 3.3.
3. Ollama models go to the server's `/api/embed` and the answer is converted to the OpenAI
   format; every other model goes to the OpenAI-compatible connection's `/embeddings` (Azure:
   `/openai/deployments/{deployment}/embeddings?api-version=...`)
   (`backend/open_webui/routers/openai.py:1757-1860`; `backend/open_webui/routers/ollama.py:886-925`).
4. Provider errors are returned with the provider's status and body; network failures give
   `Open WebUI: Server Connection Error`.

This endpoint is separate from the embedding model that indexes documents and knowledge bases
(the `rag.*` settings), which is documented in `rag-retrieval-embeddings-and-vector-stores.md`.
The Ollama router also offers `/ollama/api/embed`, `/ollama/api/embeddings` and
`/ollama/v1/embeddings` directly (section 2.2).

### 5.16 The Playground (Admin)

The Playground is a scratch pad for admins; nothing typed there is saved to chat history. It
opens on the **Chat** tab, with **Completions** and **Images** tabs at the top
(`src/routes/(app)/playground/+layout.svelte:49-85`). Anyone who is not an admin is sent to `/`.

| Tab | How it works | Messages | Evidence |
|---|---|---|---|
| **Chat** | Optional `System Instructions` (placeholder `You're a helpful assistant.`); a message box `Enter {role} message here` with a `User` / `Assistant` role toggle; `Add` appends the message without running; `Run` sends the whole conversation to `/api/chat/completions` with streaming on; `Cancel` stops reading the answer. A drop-down picks any model in the admin's list (default: the admin's first default model, or the site default). `Controls` opens the advanced parameters. The `...` menu > `Download` offers `Export chat (.json)` (a chat titled `Playground Chat` that can be imported) and `Plain text (.txt)`. Individual messages can be edited or removed | `Please select a model.` (no model chosen); `Chat exported successfully`. If the request fails, **no error is shown**: the assistant box simply stays empty | `src/lib/components/playground/Chat.svelte:89-190`, `:217-318`, `:321-561`; `src/lib/components/playground/Chat/Message.svelte:19-77` |
| **Completions** | A single text area (placeholder `You're a helpful assistant.`); `Run` sends the text as the start of an assistant message and appends the model's continuation; `Cancel` stops | No messages; failures leave the text unchanged | `src/lib/components/playground/Completions.svelte:39-179` |
| **Images** | Prompt box (`Describe the image...`, or `Describe the edit...` once source images are added); `Add Image` (or drag and drop) to edit existing images; `Run` (or Ctrl/Cmd+Enter); results appear in a grid (`Generated images will appear here` until then) and download when clicked | `Please enter a prompt`; the server's error text; `Failed to download image` | `src/lib/components/playground/Images.svelte:67-121`, `:124-281`; image engines in `image-generation-and-editing.md` |

The Chat and Completions tabs call the same `/api/chat/completions` endpoint as normal chats but
without a chat or websocket session, so the server answers directly in the HTTP response
(`src/lib/components/playground/Chat.svelte:106-123`; `chat-completion-pipeline-and-generation-tasks.md`,
section 5.5).

### 5.17 Desktop App Connection Events

When the interface runs inside the Open WebUI desktop application, the desktop app can add or
remove an OpenAI-compatible connection (and terminal connections) by sending a
`connections:openai` event; the browser applies it through the same settings endpoints, only for
admins, and skips a URL that is already in the list (`src/lib/utils/connections.ts:16-75`;
`src/routes/+layout.svelte:979-1061`). A `models:refresh` event reloads the model list
(`src/routes/+layout.svelte:1019-1031`). Whether anyone uses MedIT GPT through the desktop
application is TO BE CONFIRMED.

## 6. Data Model

This area has **no table of its own**. Connections are settings rows in the `config` table (one
row per dotted key, `backend/open_webui/models/config.py:101-108`); model records live in the
`model` table (documented in `workspace-models-and-model-access.md`); the merged model list exists
only in memory or Redis. Live values are data and are TO BE CONFIRMED.

### 6.1 Connection Settings (`config` Table)

| Key | Shape | Meaning | Evidence |
|---|---|---|---|
| `openai.enable` | true / false | The **OpenAI API** switch | `backend/open_webui/config.py:2828`; `backend/open_webui/routers/openai.py:305-310` |
| `openai.api_base_urls` | list of URLs | One entry per OpenAI-compatible connection, in display order | `backend/open_webui/config.py:2830` |
| `openai.api_keys` | list, same length as the URLs | The key for each connection (blank when none). A secret: never quote it | `backend/open_webui/config.py:2829`; `backend/open_webui/routers/openai.py:328-335` |
| `openai.api_configs` | object keyed by position (`"0"`, `"1"`, ...) | Per-connection options (6.2); older installations may key by URL, which the code still reads | `backend/open_webui/config.py:2831`; `backend/open_webui/routers/openai.py:338-343`, `:689-695` |
| `ollama.enable` | true / false | The **Ollama API** switch | `backend/open_webui/config.py:2825` |
| `ollama.base_urls` | list of URLs | One entry per Ollama server | `backend/open_webui/config.py:2826` |
| `ollama.api_configs` | object keyed by position | Per-server options (6.2), including that server's key | `backend/open_webui/config.py:2827`; `backend/open_webui/routers/ollama.py:200-203` |
| `direct.enable` | true / false | **Direct Connections** | `backend/open_webui/config.py:2823` |
| `direct.integrations.enable` | true / false | **Direct Integrations** (saved with the same form; documented in `workspace-tools-tool-servers-mcp-and-terminals.md`) | `backend/open_webui/config.py:2824`; `backend/open_webui/routers/configs.py:40-44` |
| `models.base_models_cache` | true / false | **Cache Base Model List** | `backend/open_webui/config.py:2832` |
| `models.default_metadata` | object | Global model defaults merged into every model's metadata (set in Settings > Admin > AI > Models) | `backend/open_webui/config.py:3094`; `backend/open_webui/utils/models.py:337-356` |
| `models.default_params` | object | Global default generation parameters, applied before each model's own parameters | `backend/open_webui/config.py:3095`; `backend/open_webui/main.py:1170-1175` |

Saving the OpenAI settings drops options for positions that no longer exist and pads or trims the
key list to match the URL list (`backend/open_webui/routers/openai.py:558-575`); the model-list
code also pads the stored key list if it ever gets out of step (`:684-685`). The admin settings
export includes these keys, secrets included (ground truth, Secrets).

### 6.2 Per-Connection Options (`*.api_configs` Entries)

The fields the code recognizes (`backend/open_webui/models/config.py:40-55`):

| Field | Set by | Used for |
|---|---|---|
| `enable` | Enabled switch | Skip the connection when false |
| `key` | Ollama connections only | The Ollama server's key |
| `prefix_id` | Prefix ID | Model id prefix |
| `tags` | Tags | Labels on every model |
| `model_ids` | Model IDs | Allow-list or Azure deployment names |
| `connection_type` | Connection Type | `local` or `external` |
| `provider` | Provider | `azure`, `llama.cpp`, `lmstudio`, `litellm`, or empty |
| `auth_type` | Auth | `none`, `bearer`, `session`, `system_oauth`, `microsoft_entra_id` (older entries may say `azure_ad`) |
| `headers` | Headers | Extra request headers |
| `azure` | Set automatically for Azure-style URLs | Azure handling |
| `api_type` | API Type | `responses`, or absent for Chat Completions |
| `api_version` | API Version | Azure API version |
| `extra_params` | Not set by any screen found | Recognized by the settings code only |
| `passthrough_params` | Passthrough params | Anthropic-compatible endpoint |
| `forward_cookies` | Forward cookies | Not in the recognized-field list but saved and read (`src/lib/components/AddConnectionModal.svelte:220`; `backend/open_webui/routers/openai.py:163`) |

### 6.3 Seeding From Environment Variables

The connection settings are seeded **once**, at first start, from environment variables; after
that the stored value wins (ground truth, Settings). `OLLAMA_API_CONFIGS` and
`OPENAI_API_CONFIGS` can be supplied as JSON; invalid JSON is ignored with the log warnings
`OLLAMA_API_CONFIGS is not valid JSON, ignoring` or `OPENAI_API_CONFIGS is not valid JSON,
ignoring` (`backend/open_webui/config.py:302-312`, `:349-359`). Details in section 7.2.

### 6.4 In-Memory and Redis State

| State | Holds | Shared between server processes? | Evidence |
|---|---|---|---|
| `app.state.OPENAI_MODELS` | OpenAI-compatible models by id, with the position of the connection that serves each | No (per process) | `backend/open_webui/main.py:572`; `backend/open_webui/routers/openai.py:860` |
| `app.state.OLLAMA_MODELS` | Ollama models by id, with the positions of all servers that have each | No | `backend/open_webui/main.py:563`; `backend/open_webui/routers/ollama.py:456` |
| `app.state.BASE_MODELS` | Last merged base list (cache and fallback) | No | `backend/open_webui/main.py:612`; `backend/open_webui/utils/models.py:96-106` |
| `{REDIS_KEY_PREFIX}:models:base` | Cached base list when the cache switch is on and Redis is configured | Yes | `backend/open_webui/utils/models.py:32`, `:88-104` |
| Model registry (`app.state.MODELS`) | Full model list used to resolve chats | Yes when `WEBSOCKET_MANAGER=redis` (key `{REDIS_KEY_PREFIX}:models`), otherwise per process | `backend/open_webui/socket/main.py:133-185`; `backend/open_webui/main.py:794` |

### 6.5 Browser-Side State

- **Direct connections** are part of the user's personal interface settings
  (`directConnections`: base URLs, keys and options in the same three-list shape as the admin
  settings) (`src/lib/components/chat/Settings/Connections.svelte:57-63`;
  `src/lib/components/chat/SettingsModal.svelte:438-451`). Their storage on the server belongs to
  `user-settings-and-personalisation.md`.
- **Downloads in progress** are tracked in the browser store `MODEL_DOWNLOAD_POOL`, which is why
  the three-download limit is per browser (`src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:6`,
  `:165-178`).

### 6.6 Files

Model files uploaded or downloaded through **Upload a GGUF model** are written to the server's
upload folder (`UPLOAD_DIR`) while they are hashed and sent to Ollama, then deleted
(`backend/open_webui/routers/ollama.py:1626`, `:1644-1652`, `:1598`, `:1691`). A failed transfer
can leave the file behind (read from code; section 14).

## 7. Settings and Configuration

All live values are data (the `config` table or the server environment) and are **TO BE
CONFIRMED** for production. Persistent settings take their environment value only at first
start; afterwards the stored value wins (ground truth, Settings).

### 7.1 Persistent Settings Edited on the Connections Tab

| On screen | Key | Environment seed | Code default | Evidence |
|---|---|---|---|---|
| `OpenAI API` switch | `openai.enable` | `ENABLE_OPENAI_API` | on | `backend/open_webui/config.py:319`, `:2828` |
| OpenAI-compatible connection URLs | `openai.api_base_urls` | `OPENAI_API_BASE_URLS` (several, separated by `;`) or `OPENAI_API_BASE_URL` | `https://api.openai.com/v1` (also used for any empty entry) | `backend/open_webui/config.py:322-347` |
| Their keys | `openai.api_keys` | `OPENAI_API_KEYS` (`;`-separated) or `OPENAI_API_KEY` | empty | `backend/open_webui/config.py:335-339` |
| Their options | `openai.api_configs` | `OPENAI_API_CONFIGS` (JSON object) | `{}` | `backend/open_webui/config.py:349-359` |
| `Ollama API` switch | `ollama.enable` | `ENABLE_OLLAMA_API` | on | `backend/open_webui/config.py:237`, `:2825` |
| Ollama server URLs | `ollama.base_urls` | `OLLAMA_BASE_URLS` (`;`-separated), else `OLLAMA_BASE_URL`, else `OLLAMA_API_BASE_URL` | `http://localhost:11434` (see below) | `backend/open_webui/config.py:239-300` |
| Their options and keys | `ollama.api_configs` | `OLLAMA_API_CONFIGS` (JSON object) | `{}` | `backend/open_webui/config.py:302-312` |
| `Direct Connections` | `direct.enable` | `ENABLE_DIRECT_CONNECTIONS` | off | `backend/open_webui/config.py:230`, `:2823` |
| `Cache Base Model List` | `models.base_models_cache` | `ENABLE_BASE_MODELS_CACHE` | off | `backend/open_webui/config.py:374`, `:2832` |
| (Settings > Admin > AI > Models) global model defaults | `models.default_metadata`, `models.default_params` | `DEFAULT_MODEL_METADATA`, `DEFAULT_MODEL_PARAMS` (JSON) | `{}` | `backend/open_webui/config.py:1695-1709`, `:3094-3095` |

**Default Ollama address.** Without any Ollama variable the first server is
`http://localhost:11434`. In the Docker image (`ENV=prod`, `OLLAMA_BASE_URL=/ollama`) it becomes
`http://host.docker.internal:11434`, or `http://localhost:11434` when the image bundles Ollama
(`USE_OLLAMA_DOCKER`); with `K8S_FLAG` set it is
`http://ollama-service.open-webui.svc.cluster.local:11434`. When no address was given at all, the
server checks at start-up whether port 11434 answers and switches to port 12434 if only that one
does (log `Ollama port 11434 unreachable on {host}, falling back to 12434`)
(`backend/open_webui/config.py:239-293`; `Dockerfile:86`). The bundled `docker-compose.yaml` sets
`OLLAMA_BASE_URL=http://ollama:11434` (`docker-compose.yaml:24`). Because the value is stored at
first start, these defaults only matter for a new installation.

### 7.2 Environment-Only Settings That Affect This Area

| Variable | Default | Effect | Evidence |
|---|---|---|---|
| `AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST` (older name `AIOHTTP_CLIENT_TIMEOUT_OPENAI_MODEL_LIST`) | 10 seconds | Time limit for each connection's model list, Verify and Anthropic listing | `backend/open_webui/env.py:656-663` |
| `AIOHTTP_CLIENT_TIMEOUT` | none (no limit); an invalid value means 300 | Overall time limit for chat, embedding and management calls | `backend/open_webui/env.py:608-612`; `backend/open_webui/utils/session_pool.py:43-51` |
| `AIOHTTP_CLIENT_STREAM_IDLE_TIMEOUT` | none | Longest silence allowed between streamed pieces | `backend/open_webui/env.py:614-624` |
| `AIOHTTP_CLIENT_SESSION_SSL` | `True` | Certificate checking for outbound calls; may name a CA bundle file | `backend/open_webui/env.py:628-631` |
| `AIOHTTP_POOL_CONNECTIONS`, `AIOHTTP_POOL_CONNECTIONS_PER_HOST`, `AIOHTTP_POOL_DNS_TTL` | unlimited, unlimited, 300 | Shared outbound connection pool | `backend/open_webui/env.py:710-728`; `backend/open_webui/utils/session_pool.py:54-76` |
| `AIOHTTP_FILE_STREAM_CHUNK_SIZE` | 1 MiB | Chunk size for model file uploads and downloads | `backend/open_webui/env.py:671-677` |
| `MODELS_CACHE_TTL` | 1 second | Per-provider list cache | `backend/open_webui/env.py:1035-1043` |
| `ENABLE_OPENAI_API_PASSTHROUGH` | `False` | Opens the generic `/openai/{path}` pass-through | `backend/open_webui/env.py:859-862` |
| `ENABLE_FORWARD_USER_INFO_HEADERS` (and the `FORWARD_USER_INFO_HEADER_*` names) | `False` | Sends the user's name, id, email and role to providers in headers | `backend/open_webui/env.py:989-1009` |
| `BYPASS_MODEL_ACCESS_CONTROL` | `False` | Turns model access filtering off for everyone | `backend/open_webui/env.py:832` |
| `BYPASS_ADMIN_ACCESS_CONTROL` | `True` | Admins see every model | `backend/open_webui/config.py:2086-2092` |
| `ENABLE_CUSTOM_MODEL_FALLBACK` | `False` | Custom models whose base model vanished fall back to the default model | `backend/open_webui/env.py:1033`; `backend/open_webui/main.py:1136-1147` |
| `WEBSOCKET_EVENT_CALLER_TIMEOUT` | none | How long the server waits for a browser relaying a direct connection | `backend/open_webui/env.py:534-542` |
| `WEBSOCKET_MANAGER`, `REDIS_URL`, `REDIS_KEY_PREFIX` (`open-webui`) | none, none, `open-webui` | Whether the model registry and base-list cache are shared through Redis, and their key names | `backend/open_webui/env.py:384`, `:476`; `backend/open_webui/socket/main.py:133-185` |

### 7.3 What Saving Does

| Save | Settings written | Side effects | Evidence |
|---|---|---|---|
| Any change to OpenAI-compatible connections | All four `openai.*` keys together | Clears the per-provider cache, the Redis base-list key, the in-process base list and the registry; publishes `model.provider_config.updated` | `backend/open_webui/routers/openai.py:556-597` |
| Any change to Ollama connections | All three `ollama.*` keys together | Same clearing; publishes `model.provider_config.updated` | `backend/open_webui/routers/ollama.py:306-352` |
| Direct Connections or Cache Base Model List switch | `direct.enable`, `direct.integrations.enable`, `models.base_models_cache` | Publishes `config.connections.updated`; reloads the admin's model list and site configuration; does **not** clear the model caches | `backend/open_webui/routers/configs.py:144-160`; `src/lib/components/admin/Settings/Connections.svelte:113-123` |

Because each save writes the whole list, two admins editing connections at the same time can
overwrite each other's changes (read from code: the browser sends its full copy of the lists,
`src/lib/components/admin/Settings/Connections.svelte:77-82`).

**Users' own connections.** Saving a direct connection writes only that user's personal settings
(`directConnections`, section 6.5); no server cache is touched. The user's browser then reloads its
own model list, which asks every enabled direct connection for its models again
(`src/lib/components/chat/SettingsModal.svelte:438-451`; `src/lib/apis/index.ts:61-177`).

**What other people notice after an admin save.** The change takes effect on the server at once, but
no other browser is told: everyone keeps the list loaded at their last page load until they reload
(section 9), while the server rebuilds its own list at the next request. Section 8.3 describes the
short window in which the server holds no model list at all.

## 8. Cron Jobs and Background Processes

This area has no scheduled job and no background loop of its own; there is no crontab (ground
truth; `CLAUDE.md`, Startup Order and Background Jobs). The model list is built **on demand**, kept
in caches, emptied **at save time** and, only when the cache switch is on, built **once at
start-up**. The background work tied to this area is event delivery, the Redis relay for
direct-connection replies, and the session-pool cleanup that those replies depend on.

### 8.1 What Runs When

| Process | Runs when | What it does | Evidence |
|---|---|---|---|
| Model-list build | Each `GET /api/models` (normally once per page load and after admin actions); a chat or embeddings request that finds the server's model registry empty; a provider route that cannot find the requested model in its own list | Asks every enabled connection for its models in parallel (10-second limit each) and replaces the registry (section 5.7); a provider route refreshes only its own provider type's list and map | `backend/open_webui/main.py:897-900`, `:1091-1092`, `:1115-1116`; `backend/open_webui/routers/openai.py:1539-1543`; `backend/open_webui/routers/ollama.py:1080-1092`; `backend/open_webui/utils/models.py:69-462` |
| Start-up pre-fetch | Once per server process during start-up, only while **Cache Base Model List** is on | Builds the list before the server reports ready (8.4) | `backend/open_webui/main.py:407-429`, `:471` |
| Save-time clearing | An admin saves OpenAI-compatible or Ollama connections, or downloads, loads, unloads or deletes a llama.cpp or LM Studio model | Empties the caches and the registry (8.3) | `backend/open_webui/routers/openai.py:346-357`, `:577`, `:966`, `:1005`, `:1021`, `:1048`; `backend/open_webui/routers/ollama.py:324-334` |
| Refresh | The **Refresh** button; also the admin's own browser straight after every successful save on the Connections tab (both send `?refresh=true`) | Empties the caches (not the registry) and rebuilds | `backend/open_webui/utils/models.py:76-82`; `src/lib/components/admin/Settings/Connections.svelte:28-36`, `:86-89`, `:106-109`, `:118-121`, `:125-136` |
| Event delivery | After a connection save, a provider-model change or a provider failure | Runs event functions and posts matching webhooks as background tasks (9.3) | `backend/open_webui/events.py:1062-1066`, `:1159-1171` |
| Direct-reply relay (`redis_event_listener`) | Continuously, only when `WEBSOCKET_MANAGER=redis` | Passes a direct-connection reply from the server process holding the user's websocket to the process handling the chat, over the Redis channel `{REDIS_KEY_PREFIX}:direct_completion` | `backend/open_webui/main.py:397-398`; `backend/open_webui/socket/main.py:199`, `:963-995`, `:998-1016` |
| Session-pool cleanup (`periodic_session_pool_cleanup`) | Always; one sweep every session timeout (at least 120 seconds) | Removes browser sessions that stopped sending heartbeats; a direct request for a removed session answers `Client session disconnected.` | `backend/open_webui/socket/main.py:129`, `:212-263`, `:1262-1266` |
| Browser polling | While an admin's tab follows a llama.cpp or LM Studio download started from the model picker | Asks the server for the job status every 1.5 seconds | `src/lib/components/chat/ModelSelector/Selector.svelte:643-681` |

The browser does **not** refresh the model list on a timer. It loads the list when the app opens and
after specific actions (saving settings, editing models, finishing a download)
(`src/routes/(app)/+layout.svelte:83-90`, `:227-229`; `src/lib/components/chat/SettingsModal.svelte:450`;
`src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:277-282`).

### 8.2 Caches and Redis Keys

| Layer | Holds | Key or location | Lifetime | Shared between server processes? | Evidence |
|---|---|---|---|---|---|
| Per-provider result cache | One user's OpenAI-compatible list; one user's Ollama list | In memory, keys `openai_all_models_{user.id}` and `ollama_all_models_{user.id}` (without the user part when there is no user, as at start-up) | `MODELS_CACHE_TTL` seconds, default 1; an empty value means no expiry | No | `backend/open_webui/routers/openai.py:790-796`; `backend/open_webui/routers/ollama.py:384-390`; `backend/open_webui/env.py:1035-1042` |
| Base-list cache (`models.base_models_cache`) | The merged base list: pipe functions, OpenAI-compatible and Ollama models | Redis key `{REDIS_KEY_PREFIX}:models:base` (prefix default `open-webui`) when `REDIS_URL` or Redis Sentinel is configured; otherwise `app.state.BASE_MODELS` in each process | No expiry; until a connection save, a llama.cpp or LM Studio model change, or a Refresh, or (in-process only) a restart | Yes with Redis | `backend/open_webui/utils/models.py:32`, `:84-106`; `backend/open_webui/utils/redis.py:88-105`; `backend/open_webui/main.py:390`, `:612` |
| Last good list | The previous base list, served when a fresh build returns nothing | `app.state.BASE_MODELS` | Until a save or a Refresh empties it | No | `backend/open_webui/utils/models.py:99-106` |
| Provider maps | Which connection serves each model (`urlIdx` for OpenAI-compatible, `urls` for Ollama) | `app.state.OPENAI_MODELS`, `app.state.OLLAMA_MODELS` | Replaced at each fetch from that provider type; emptied by that provider type's save | No | `backend/open_webui/routers/openai.py:351-352`, `:860`; `backend/open_webui/routers/ollama.py:329`, `:456` |
| Model registry | The full list used to resolve chats, tasks and embeddings | `app.state.MODELS`; with `WEBSOCKET_MANAGER=redis`, the Redis hash `{REDIS_KEY_PREFIX}:models` and the key `{REDIS_KEY_PREFIX}:models:signature`, with a per-process copy that is reread whenever the signature changes | Replaced at each build that finds at least one base model; emptied by a connection save or a llama.cpp or LM Studio model change | Yes with `WEBSOCKET_MANAGER=redis` | `backend/open_webui/socket/main.py:133-148`, `:185`; `backend/open_webui/socket/utils.py:140-188`, `:204-238`; `backend/open_webui/utils/models.py:445-460` |

Points that matter when reading a symptom:

- **Two different Redis settings.** The base-list cache uses the general Redis connection
  (`REDIS_URL`); the shared registry uses the websocket Redis settings (`WEBSOCKET_REDIS_URL`, which
  defaults to `REDIS_URL`) and exists only with `WEBSOCKET_MANAGER=redis`
  (`backend/open_webui/env.py:381`, `:476`, `:493`). A deployment can share one and not the other;
  what production uses is TO BE CONFIRMED.
- **Empty results are not cached.** A build that finds no base model is not written to Redis
  (`backend/open_webui/utils/models.py:101-104`), so the next request tries the providers again.
- **A restart does not refresh a Redis-held list.** The Redis key has no expiry and nothing deletes it
  at start-up; the only deletions happen on a connection save (including a llama.cpp or LM Studio
  model change) and on a Refresh (`backend/open_webui/routers/openai.py:350`; `backend/open_webui/routers/ollama.py:327`;
  `backend/open_webui/utils/models.py:81`, `:88-92`, `:104`). The "restart" entry in the table of
  section 5.8 therefore applies to the in-process cache only.
- **Switching the cache off does not delete the Redis key** (`backend/open_webui/routers/configs.py:144-160`).
  The admin's browser asks for a refresh straight after the switch is saved, which replaces the key
  (`src/lib/components/admin/Settings/Connections.svelte:113-123`, `:28-36`).

### 8.3 What a Connection Save Does to the Model List

This happens at save time, not in the background.

1. The settings rows are written (section 7.3).
2. In the server process that handled the save, the code empties: that provider type's per-provider
   cache, the Redis base-list key (when Redis is configured), the in-process base list, that
   provider type's map and the model registry (`backend/open_webui/routers/openai.py:346-357`, `:577`;
   `backend/open_webui/routers/ollama.py:324-334`). From this moment the server holds **no model
   list**, and the "last good list" fallback of section 5.7 (step 6) is gone as well.
3. The list is rebuilt by whichever comes first: the admin's own browser, which asks for
   `/api/models?refresh=true` as soon as the save succeeds
   (`src/lib/components/admin/Settings/Connections.svelte:28-36`, `:86-89`, `:106-109`); anyone's next
   model-list request; or a chat or embeddings request, which rebuilds when it finds the registry
   empty (`backend/open_webui/main.py:1091-1092`, `:1115-1116`). The rebuild asks every connection
   again, so it takes as long as the slowest one (up to the 10-second limit).
4. Background tasks that arrive in this window do not rebuild. Title, tag and follow-up generation
   answer `Model '' was not found` (`backend/open_webui/routers/tasks.py:163-167`;
   `chat-completion-pipeline-and-generation-tasks.md`).
5. If the rebuild finds **no base model at all** (every enabled provider unreachable, refusing its key
   or timing out, and no pipe function installed), the server returns an empty list. Arena and
   workspace models disappear too, because the build stops before adding them, and the registry
   stays empty, so every chat answers `Model not found` (`backend/open_webui/utils/models.py:99-113`;
   `backend/open_webui/main.py:1128-1129`). Because empty results are not cached, the list returns at
   the first request after a provider answers again.
6. **Several server processes without Redis.** Only the process that handled the save is emptied.
   The others keep their registry and provider maps, so removed or switched-off models keep
   resolving there until that process rebuilds: at its next model-list request or, while the
   base-list cache is on, only when a Refresh reaches that process or it restarts. Because connections are identified by position, a request handled by
   such a process after a removal can be sent to whichever connection now holds the old position, or
   fail (read from code, TO BE CONFIRMED in a test environment)
   (`backend/open_webui/routers/openai.py:338-343`, `:1539-1554`; `backend/open_webui/utils/models.py:96-97`).
   With `WEBSOCKET_MANAGER=redis` the shared registry is emptied for every process, and each process
   refreshes its own provider maps when it rebuilds.
7. **A Refresh differs in one respect:** it empties the caches but not the registry
   (`backend/open_webui/utils/models.py:76-82`). If every provider fails during a Refresh, the picker
   comes back empty while chats can still resolve models from the registry (and then fail at the
   provider).
8. Saving the **Direct Connections** or **Cache Base Model List** switch clears nothing (section 7.3).

### 8.4 Start-Up Pre-Fetch

- Runs only while `models.base_models_cache` is on, in each server process, with a stand-in request
  and no signed-in user (`backend/open_webui/main.py:407-427`).
- Connections whose Auth is `Session` or `OAuth` have no user credentials to forward at that point,
  so they contribute no models to the pre-fetched list: the `Session` branch reads a token the
  stand-in request does not carry (the error is caught and logged as `Connection error: {e}`), and
  the `OAuth` branch finds no single sign-on session (`backend/open_webui/routers/openai.py:96-119`,
  `:192-206`). With the cache on, those models stay missing until an admin presses Refresh or saves
  the connections (read from code; TO BE CONFIRMED in a test environment).
- A failure is logged as `Failed to pre-fetch models at startup: {e}` and start-up continues
  (`backend/open_webui/main.py:428-429`).
- The server reports itself ready only after this step (`backend/open_webui/main.py:471`; ground
  truth: `/ready` answers 503 until start-up finishes), so slow providers delay readiness by up to
  the model-list time limit.
- With Redis, a list cached before the restart is reused instead of fetched (8.2).

### 8.5 Long-Running Transfers

| Work | Where it runs | Time limits | If the admin's tab closes | Evidence |
|---|---|---|---|---|
| Ollama pull (Manage Ollama or the model picker) | One long request from the admin's tab, through the server, to Ollama; progress streams back in the same response. The options the server adds to the pull request are a security question (section 14.3) | No overall limit unless `AIOHTTP_CLIENT_TIMEOUT` is set; no limit on silence unless `AIOHTTP_CLIENT_STREAM_IDLE_TIMEOUT` is set; three at once per tab | TO BE CONFIRMED (depends on Ollama, section 5.10) | `backend/open_webui/routers/ollama.py:652-677`; `backend/open_webui/utils/session_pool.py:43-51`; `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:162-296` |
| **Update All Models** | A loop in the admin's tab that pulls each model in turn | As for a pull | The loop stops with the tab; the pull in progress as above | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:78-160` |
| GGUF download (URL mode) | The server downloads the file into the upload folder, then pushes it to Ollama | 600 seconds for the download; 30 seconds to push to Ollama | TO BE CONFIRMED | `backend/open_webui/routers/ollama.py:1550-1601` |
| GGUF upload (File mode) | The browser uploads the file; the server hashes it, pushes it to Ollama and creates the model | The general client limits above | TO BE CONFIRMED | `backend/open_webui/routers/ollama.py:1632-1723` |
| llama.cpp or LM Studio download | On the provider; the server only starts it | The picker polls every 1.5 seconds; the Manage Models list changes only on **Refresh** | The provider's behaviour, TO BE CONFIRMED | `backend/open_webui/routers/openai.py:954-990`; `src/lib/components/chat/ModelSelector/Selector.svelte:643-681`; `src/lib/components/admin/Settings/Models/Manage/ManageProviderModels.svelte:103-111` |
| Unload (**Eject**) | The server asks each Ollama server hosting the model, or llama.cpp | 30 seconds per server | Not applicable | `backend/open_webui/main.py:996-1013`, `:1037-1057` |

## 9. Notifications and Emails

The application sends no email (ground truth, Contacts That Exist in the Repository). Nothing in this
area creates an in-app notification, a browser (desktop) notification or a user-facing webhook
message. What people see are pop-ups (toasts) in the tab where they acted, listed in section 10:

- the model-provider events are not among the events that become notifications
  (`backend/open_webui/events.py:669-675`);
- the browser notifications created by the root layout are for chat and channel events only
  (`src/routes/+layout.svelte:622`, `:760`, `:873`).

**Nobody else is told about a connection change.** No socket event announces a connection save or a
new model list; the only `models:refresh` handler serves the Open WebUI desktop application
(`src/routes/+layout.svelte:1019-1031`, section 5.17). Each person's picker keeps the list loaded at
their last page load, and the server rebuilds its own list on the next request (section 8.3).

### 9.1 Socket Traffic Used by This Area

| Traffic | Direction | Purpose | Evidence |
|---|---|---|---|
| `events` call carrying `request:chat:completion` | Server to the user's tab | Asks the tab that sent the message to call the user's direct connection | `backend/open_webui/utils/chat.py:79-89`, `:130-140`; `backend/open_webui/socket/main.py:1258-1286`; `src/routes/+layout.svelte:646-731` |
| Per-request channel `{user_id}:{session_id}:{request_id}` | Tab to server | Carries the provider's reply lines and a final `done` marker | `backend/open_webui/utils/chat.py:70-125`; `src/routes/+layout.svelte:702-705`, `:726-729`; `backend/open_webui/socket/main.py:998-1016` |
| Redis channel `{REDIS_KEY_PREFIX}:direct_completion` | Between server processes | Forwards those lines when the tab's websocket is held by another process | `backend/open_webui/socket/main.py:199`, `:963-995`, `:1011-1016` |
| `chat:message:error` | Server to tab | Shows provider and connection failures in the chat's grey error box (display documented in `chat-completion-pipeline-and-generation-tasks.md`) | `backend/open_webui/main.py:1686-1710` |

### 9.2 Progress Shown Only in the Tab That Started It

- **Ollama pull, Update All Models and Create a model.** Ollama's progress lines arrive in the HTTP
  response itself, not over the websocket. Percentages fill a progress bar. In a pull started from
  the model picker and in **Create a model** (also the create step of an upload), status lines
  without a layer digest appear as green pop-ups in Ollama's own words (outside the repository); the
  Manage Ollama pull and **Update All Models** show only the progress
  (`backend/open_webui/routers/ollama.py:670-677`, `:743-750`;
  `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:110-146`, `:181-266`, `:403-421`, `:547-566`;
  `src/lib/components/chat/ModelSelector/Selector.svelte:479-562`).
- **GGUF upload.** Progress events (`progress`, `completed`, `total`) are streamed in the HTTP response
  (`backend/open_webui/routers/ollama.py:1577`, `:1669-1670`;
  `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:326-364`).
- **llama.cpp or LM Studio download from the picker.** Polled every 1.5 seconds (section 8.1).
- Other admins see none of this until their own list reloads. The download limit of three is kept in
  each tab (`src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:45`, `:173`).

### 9.3 Events for Event Functions and Webhooks

These events feed automation: active event functions, and webhooks an admin has configured under
the Events settings (documented in `notifications-webhooks-events-and-banners.md`). A webhook that
subscribes to every event (`'*'`, as the migrated legacy webhook does) receives them all
(`backend/open_webui/events.py:854-870`, `:1046-1059`, `:1171`). The message text a webhook carries is
the event's message, followed by the subject in brackets when there is one
(`backend/open_webui/events.py:1040-1044`).

| Event | Webhook message text | Published when | Data (summary) | Evidence |
|---|---|---|---|---|
| `model.provider_config.updated` | `Model Provider Config updated` | OpenAI-compatible or Ollama connections are saved | Provider, whether it is on, number of URLs | `backend/open_webui/routers/openai.py:579-590`; `backend/open_webui/routers/ollama.py:336-347`; `backend/open_webui/events.py:456-460` |
| `config.connections.updated` | `Config Connections updated` | **Direct Connections**, **Direct Integrations** or **Cache Base Model List** is saved | The three values | `backend/open_webui/routers/configs.py:152-159`; `backend/open_webui/events.py:68-72` |
| `model.provider_model.created` | `Provider model created` | A llama.cpp or LM Studio download request is accepted; an Ollama model is copied through the API | Model, provider, connection position, address | `backend/open_webui/routers/openai.py:965-973`; `backend/open_webui/routers/ollama.py:782-794`; `backend/open_webui/events.py:466-470` |
| `model.provider_model.deleted` | `Provider model deleted` | A llama.cpp model or an Ollama model is deleted | Model, provider, connection position | `backend/open_webui/routers/openai.py:1040-1055`; `backend/open_webui/routers/ollama.py:824-837`; `backend/open_webui/events.py:471-475` |
| `model.provider_request.failed` | `Model provider request failed` | A provider answered a chat, embeddings, Responses, token-count or pass-through request with HTTP 400 or above | Error type (`authentication_failed`, `rate_limited`, `model_not_found`, `server_failed`, `upstream_error`), status, provider, connection address, model, the provider's message | `backend/open_webui/events.py:1205-1273`; `backend/open_webui/routers/openai.py:1684-1734`; `backend/open_webui/routers/ollama.py:140-163` |

No event is published for an Ollama pull or create, or for a llama.cpp or LM Studio load or unload
(`backend/open_webui/routers/ollama.py:652-677`, `:729-750`; `backend/open_webui/routers/openai.py:993-1022`).
A chat that fails because of a provider can also lead to a `chat.failed` event; when that happens is
documented in `chat-completion-pipeline-and-generation-tasks.md`. What the provider-failure event
carries about the connection's key is security-sensitive (section 14).

## 10. Error, Warning and Notice Messages (Verbatim)

How to read these tables. Admin screens print a server's message in a red pop-up as it arrives (the
API helpers pass the server's `detail` through, `src/lib/apis/openai/index.ts:3-14`;
`src/lib/apis/ollama/index.ts:48-55`). Chat failures appear as a pop-up and in the chat's grey error
box (`chat-completion-pipeline-and-generation-tasks.md`). When a provider answers with its own error,
the user reads the **provider's words**, which are not in the repository (section 5.14). Placeholders
use the source's variable names; everything else is quoted as the code spells it.

### 10.1 Admin Connections Screen and the Connection Pop-Up

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `OpenAI API settings updated` | Success | `src/lib/components/admin/Settings/Connections.svelte:87` | OpenAI-compatible connections saved: a connection added, edited, switched or deleted, the **OpenAI API** switch changed, or the tab's **Save** pressed | None | The admin's model list reloads next (section 8.3) |
| `Ollama API settings updated` | Success | `src/lib/components/admin/Settings/Connections.svelte:107` | Ollama connections saved | None | As above |
| `Connections settings updated` | Success | `src/lib/components/admin/Settings/Connections.svelte:119` | **Direct Connections** or **Cache Base Model List** switched | None | Saving these switches clears no cache (7.3) |
| `Model list refreshed` | Success | `src/lib/components/admin/Settings/Connections.svelte:130` | **Refresh** finished (the button shows only while the cache is on) | None | — |
| `Settings saved successfully!` | Success | `src/lib/components/chat/SettingsModal.svelte:860` | The tab's **Save** button. It appears straight away, without waiting for the two saves it starts, so it can appear even when one of them fails (read from code, `src/lib/components/admin/Settings/Connections.svelte:214-221`) | Look for an error pop-up beside it | Did `OpenAI API settings updated` and `Ollama API settings updated` also appear? |
| `Server connection failed` | Error | `src/lib/apis/openai/index.ts:3`; `src/lib/apis/ollama/index.ts:53`, `:94`, `:126`, `:158`, `:190`; shown by `src/lib/components/admin/Settings/Connections.svelte:83`, `:103` | Fallback text when a save or read fails without a readable message; otherwise the pop-up shows the server's own text, for example the `ACCESS_PROHIBITED` sentence for an account that is no longer an admin | Reload the page; sign in again | Is the server reachable? Is the account still an admin? |
| `Trouble accessing Ollama?` | Info | `src/lib/components/admin/Settings/Connections.svelte:356` (key `settings.admin.connections.manageOllamaApiConnections.description`, `src/lib/i18n/locales/en-US/translation.json:2175`) | Always shown under the Ollama list, followed by the link `Click here for help.` to the upstream troubleshooting page (`:357-363`) | — | Whether to send people to upstream pages is TO BE CONFIRMED |
| `Base Model List Cache speeds up access by fetching base models only at startup or on settings save—faster, but may not show recent base model changes.` | Info | `src/lib/components/admin/Settings/Connections.svelte:388`; `src/lib/i18n/locales/en-US/translation.json:2169` | Description under **Cache Base Model List** | — | Section 8.2 |
| `Direct Connections allow users to connect to their own OpenAI compatible API endpoints.` | Info | `src/lib/components/admin/Settings/Connections.svelte:374`; `src/lib/i18n/locales/en-US/translation.json:2171` | Description under **Direct Connections** | — | Section 5.12 |
| `Server connection verified` | Success | `src/lib/components/AddConnectionModal.svelte:88`, `:133` | **Verify Connection** succeeded | Save if everything else is right | Verify proves only that the model list (or Ollama version) can be read (5.6) |
| `OpenAI: URL is required` | Error | `src/lib/apis/openai/index.ts:333-335`; shown by `src/lib/components/AddConnectionModal.svelte:128-130` | Verify pressed with an empty URL (OpenAI-compatible or direct) | Type the URL | — |
| `OpenAI: Network Problem` | Error | `src/lib/apis/openai/index.ts:354`, `:380`; shown by `src/lib/components/AddConnectionModal.svelte:128-130` | Verify failed without an OpenAI-style error message: no answer, DNS, TLS or timeout (the server answers `Open WebUI: Server Connection Error`); an error body that is not OpenAI-shaped or not JSON; any failure on an `api.anthropic.com` URL; for a direct connection, also the browser refusing the request (CORS) | Check that the URL is the API base (usually ending in `/v1`) and the key | System connection: server log `Client error: ...` or `Unexpected error: ...` (`backend/open_webui/routers/openai.py:1147`, `:1150`); direct: the browser's developer console |
| `OpenAI: {error.message}` | Error | `src/lib/apis/openai/index.ts:98`, `:128`, `:354`, `:380` | The provider answered Verify with an OpenAI-style error; the text after `OpenAI:` is the provider's own sentence (for example about an invalid key) | Correct the key, URL or provider account | The wording belongs to the provider |
| `Ollama: Network Problem` | Error | `src/lib/apis/ollama/index.ts:22`; shown by `src/lib/components/AddConnectionModal.svelte:80-85` | Any Ollama Verify failure: the server's error reply never carries `error.message`, so the reason is not shown | Check the URL (for example `http://ollama-host:11434`, without `/api`) | Server log `Client error: ...` or `Unexpected error: ...` (`backend/open_webui/routers/ollama.py:282`, `:285`) |
| `Headers must be a valid JSON object` | Error | `src/lib/components/AddConnectionModal.svelte:107`, `:202` | **Headers** is not a JSON object (on Verify or Save). After the Save-time check the **Save** button stays busy, because that path does not reset it; switching to another settings tab and back, or reloading, resets it (read from code, `:161-205`) | Enter headers as a JSON object | — |
| `Model ID is already added` | Error | `src/lib/components/AddConnectionModal.svelte:153` | The same id typed twice in **Model IDs** | — | — |
| `URL is required` | Error | `src/lib/components/AddConnectionModal.svelte:166` | Save with an empty URL. The URL field is marked required, so the browser's own prompt (worded by the browser) normally appears first (`:349-358`) | Type the URL | — |
| `API Version is required` | Error | `src/lib/components/AddConnectionModal.svelte:175` | Azure connection saved without **API Version**; **Advanced** opens | Fill in the Azure API version | Section 5.3 |
| `Key is required` | Error | `src/lib/components/AddConnectionModal.svelte:182` | Azure connection saved without a key while Auth is not `Entra ID` | — | — |
| `Deployment names are required for Azure OpenAI` | Error; also a hint | `src/lib/components/AddConnectionModal.svelte:189`; hint at `:710` | Azure connection saved with an empty **Model IDs** list | Add the deployment names | — |
| `Are you sure you want to delete this connection? This action cannot be undone.` | Warning (confirmation) | `src/lib/components/AddConnectionModal.svelte:812-822` | **Delete** in an Edit Connection pop-up | Confirm or cancel | Admin connections: the removal saves at once and shifts later positions (5.4); personal connections: kept until the tab's **Save** (5.12) |
| `No authentication` | Info | `src/lib/components/AddConnectionModal.svelte:444` | Auth `None` chosen | — | — |
| `Forwards system user session credentials to authenticate` | Info | `src/lib/components/AddConnectionModal.svelte:448` | Auth `Session` chosen | — | Privacy and security question: section 5.2 |
| `Forwards system user OAuth access token to authenticate` | Info | `src/lib/components/AddConnectionModal.svelte:452` | Auth `OAuth` chosen | — | As above |
| `Uses DefaultAzureCredential to authenticate` | Info | `src/lib/components/AddConnectionModal.svelte:456` | Auth `Entra ID` chosen | — | — |
| `Leave empty to include all models from "{url}/models" endpoint` | Info | `src/lib/components/AddConnectionModal.svelte:715-717` | **Model IDs** empty on an OpenAI-compatible or direct connection | — | — |
| `Leave empty to include all models from "{url}/api/tags" endpoint` | Info | `src/lib/components/AddConnectionModal.svelte:703-708` | **Model IDs** empty on an Ollama connection | — | — |
| `WebUI will make requests to "{url}/chat/completions"` | Info (tooltip) | `src/lib/components/admin/Settings/Connections/OpenAIConnection.svelte:48-50`; `src/lib/components/chat/Settings/Connections/Connection.svelte:46-48` | Hovering over an OpenAI-compatible or direct connection | — | The tooltip does not change for the `Responses` API type |
| `WebUI will make requests to "{url}/api/chat"` | Info (tooltip) | `src/lib/components/admin/Settings/Connections/OllamaConnection.svelte:51-53` | Hovering over an Ollama connection | — | — |

### 10.2 Server Messages: OpenAI-Compatible Router (`/openai`)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `OpenAI API is disabled` | Error (HTTP 503) | `backend/open_webui/routers/openai.py:362`, `:871`, `:1493` | The **OpenAI API** switch is off and a list, chat or model-management call reached the router | Ask an admin | State of the switch (5.4) |
| `Connection not found` | Error (HTTP 404) | `backend/open_webui/routers/openai.py:364-367` | Model management addressed a connection position that no longer exists (for example after a removal) | Close and reopen **Manage Models** | Positions shift on removal (5.4) |
| `Provider "{provider}" does not support model management` | Error (HTTP 400) | `backend/open_webui/routers/openai.py:369-374` | Model management on a connection whose **Provider** is not `llama.cpp` or `LM Studio`; `{provider}` reads `default` when none is set | — | The connection's Provider option |
| `Provider "{provider}" does not support {operation}` | Error (HTTP 400) | `backend/open_webui/routers/openai.py:379-383` | An operation the provider type lacks, for example `delete` on LM Studio | — | — |
| `Unexpected error: {e}` | Error (HTTP 500) | `backend/open_webui/routers/openai.py:933-936`; inner texts `HTTP Error: {r.status}` (`:907`), `External Error: {res["error"]}` (`:911`), `Failed to connect to Anthropic API` (`:898`) | One connection's own list was requested and the provider refused it, answered with a non-200 status, or failed. The Connections tab makes this request for every enabled connection when it opens and ignores failures, so nothing appears on screen (`src/lib/components/admin/Settings/Connections.svelte:192-201`) | — | Server log `Unexpected error: ...` (`:934`) |
| `Open WebUI: Server Connection Error` | Error (HTTP 500, or the provider's status) | `backend/open_webui/routers/openai.py:539`, `:669`, `:932`, `:1121`, `:1148`, `:1151`, `:1750`, `:1856`, `:1987`, `:2112` (text `backend/open_webui/constants.py:130`) | No usable answer from the provider: DNS failure, refused connection, TLS failure, a configured timeout, or an unexpected error while sending. In a chat it fills the error box; on Verify the pop-up shows `OpenAI: Network Problem` instead | Retry later; report if it persists | The server log shows the exception just before; no `Upstream` line is written (5.14) |
| `Model '' was not found` | Error (HTTP 404) | `backend/open_webui/routers/openai.py:474-476`, `:1546-1552` (text `backend/open_webui/constants.py:89`) | The model is not in the server's OpenAI-compatible list at the moment of use, even after a fresh fetch (removed, connection switched off, provider no longer listing it); the name is empty because the code passes none | Reload the page and choose a listed model | Section 5.9 |
| `Invalid model name: must not be empty or contain path separators or traversal sequences` | Error (HTTP 400) | `backend/open_webui/routers/openai.py:1206-1218` | Azure (classic URL): the deployment name is empty or contains `/`, `\` or `..` | An admin corrects **Model IDs** | Section 5.3 |
| `Direct API passthrough is disabled. Set ENABLE_OPENAI_API_PASSTHROUGH=True to enable.` | Error (HTTP 403) | `backend/open_webui/routers/openai.py:1994-2005` | A script called an `/openai/...` path that has no dedicated route while the pass-through is off (the default) | Use a supported endpoint (`public-api-and-integrations.md`) | Enabling it is a security decision (section 14) |
| `model is required` | Error (HTTP 400) | `backend/open_webui/routers/openai.py:454-458` | An Anthropic-format request routed through an OpenAI-compatible connection named no model (`public-api-and-integrations.md`) | The script must send a model | — |
| `Invalid token-count response from upstream provider` | Error (HTTP 502) | `backend/open_webui/routers/openai.py:530-532` | An Anthropic-format token count: the provider's answer had no valid `input_tokens` | — | Provider compatibility |
| `External: {res["error"]}` | Error | `backend/open_webui/routers/openai.py:655-662` | The legacy `/openai/audio/speech` route: the provider refused (or `External: {e}` when its answer could not be read) | — | `audio-speech-to-text-and-text-to-speech.md` |
| `OpenAI API was not found` | Error | `backend/open_webui/constants.py:90`, used at `backend/open_webui/routers/openai.py:672-673` | The legacy speech route when no connection uses exactly `https://api.openai.com/v1`. The code hands over the message function without calling it, so the response is probably a generic server error rather than this text (read from code; TO BE CONFIRMED) | — | Section 14 |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 401; 403 on the speech route) | `backend/open_webui/routers/openai.py:867-868`, `:602-606` | A non-admin asked for one connection's raw list, or used the legacy speech route without the text-to-speech permission | — | Role and permissions (section 3) |

### 10.3 Server Messages: Ollama Router (`/ollama`)

When Ollama itself answers with an error that has an `error` field (for example an unknown tag during
a pull), that text is passed to the caller unchanged and shown in the pop-up; its wording belongs to
Ollama (`backend/open_webui/routers/ollama.py:140-152`).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `The Ollama API is disabled. Please enable it to use this feature.` | Error (HTTP 503) | `backend/open_webui/routers/ollama.py:493`, `:661`, `:698`, `:738`, `:770`, `:808`, `:849`, `:896`, `:947`, `:1006`, `:1108`, `:1280`, `:1396`, `:1454` (text `backend/open_webui/constants.py:103`) | The **Ollama API** switch is off and a list, pull, push, create, copy, delete, show, embedding or chat call reached the router | Ask an admin | State of the switch |
| `WebUI could not connect to Ollama` | Error (HTTP 500) | `backend/open_webui/routers/ollama.py:575-579` (text `backend/open_webui/constants.py:91`) | No enabled Ollama server answered the version check. Not shown on screen: **About** simply omits the Ollama Version line and the picker omits the Pull option (`src/lib/components/chat/Settings/About.svelte:40-43`, `:112-118`; `src/lib/components/chat/ModelSelector/Selector.svelte:316`, `:589-591`) | — | Ollama reachable from the server? |
| `Model '{model}' was not found` | Error (HTTP 400) | `backend/open_webui/routers/ollama.py:612`, `:704`, `:776`, `:818`, `:861`, `:909`, `:960`, `:1016`, `:1088-1092` (text `backend/open_webui/constants.py:89`) | The model is not on any enabled Ollama server, even after a fresh fetch (deleted, server switched off or down, **Model IDs** filter) | Choose a listed model | Section 5.9 |
| `Ollama: {e}` | Error (HTTP 500, or the status received) | `backend/open_webui/routers/ollama.py:188-194` | Ollama could not be reached or the connection broke; the text after `Ollama:` is the network library's own description | Retry later | Ollama running and reachable from the server? |
| `Open WebUI: Server Connection Error` | Error | `backend/open_webui/routers/ollama.py:164-167`, `:193`, `:283` (text `backend/open_webui/constants.py:130`) | Ollama answered with an error whose body had no `error` field, or a request failed without any description; on Verify the pop-up shows `Ollama: Network Problem` instead | Retry later | Server log `Failed to parse error response: ...` (`:156`) |
| `Unexpected error: {exc}` | Error (HTTP 500) | `backend/open_webui/routers/ollama.py:284-286`; inner texts `HTTP Error: {r.status}` (`:274`), `External Error: {res["error"]}` (`:277`) | Ollama Verify: the server answered with a non-200 status, or another failure; the pop-up shows `Ollama: Network Problem` | — | Server log `Unexpected error: ...` (`:285`) |
| `Missing name of the model to unload.` | Error (HTTP 400) | `backend/open_webui/routers/ollama.py:601-605` | API unload call without a model name | — | — |
| `Failed to unload model on {len(errors)} nodes: {errors}` | Error (HTTP 500) | `backend/open_webui/routers/ollama.py:643-647` | API unload (`/ollama/api/unload`) failed on at least one server | — | Server log `Failed to unload model on node ...` (`:640`) |
| `Invalid file_url. Only URLs from allowed hosts are permitted.` | Error (HTTP 400) | `backend/open_webui/routers/ollama.py:1613-1618` | **Upload a GGUF model**, URL mode, with an address that does not start with `https://huggingface.co/` or `https://github.com/`; shown as a pop-up (`src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:365-367`) | Use a Hugging Face resolve URL | — |
| `Ollama: Could not create blob, Please try again.` | Error (inside the progress stream) | `backend/open_webui/routers/ollama.py:1600-1601`, `:1687-1688` | Ollama refused the uploaded model file. Not shown on screen: in File mode the Manage Ollama screen writes it only to the browser console; in URL mode the stream simply ends (read from code, `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:350-363`) | — | Ollama log and free disk space |
| `Failed to create model in Ollama. {resp_text}` | Error (inside the progress stream) | `backend/open_webui/routers/ollama.py:1716-1718` | File-mode upload: Ollama refused to create the model; `{resp_text}` is Ollama's reply. Shown only in the browser console, as above | — | As above |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 401; 403 for a server position) | `backend/open_webui/routers/ollama.py:489-490`, `:555-556`, `:1497-1498`, `:1076-1077` | A non-admin asked for one server's list or version, or named a server position that does not host the model | — | Role (section 3) |
| `At least one of 'content' or 'tool_calls' must be provided` | Error (HTTP 400, inside a validation message) | `backend/open_webui/routers/ollama.py:1045-1050`, `:1125-1129` | A script sent an Ollama chat message with neither content nor tool calls | Fix the script | — |

### 10.4 Server Messages: Model Resolution, Unload and Embeddings

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Model not found` | Error (HTTP 400) | `backend/open_webui/main.py:1128-1129`, `:1180-1182`, `:1640-1645`; `backend/open_webui/utils/models.py:480`, `:491`, `:515`, `:521` | A chat named a model that is not in the server's registry, a workspace model whose base model has gone (unless the fallback setting is on), or a model the user may not read. Access refusals are worded the same way on purpose | Reload and pick a listed model; ask an admin about sharing | Server log `Model access denied: ...` for the access case; sections 5.9 and 8.3 |
| `Model not found` | Error (HTTP 403) | `backend/open_webui/utils/access_control/__init__.py:405`, `:409`, `:413` | A non-admin called an `/openai` or `/ollama` route directly for a model without a model record or without read access | — | Section 3.3 |
| `Model not found` | Error (HTTP 500) | `backend/open_webui/utils/embeddings.py:63-65` | `/api/embeddings` with a model that is not in the registry; the exact body is produced by the web framework | Use a listed model | Section 5.15 |
| `Model '' was not found` | Error (HTTP 404) | `backend/open_webui/routers/tasks.py:163-167` | A title, tag or follow-up task arrived while the registry was empty, typically just after an admin saved connections | None; the next task normally works | Section 8.3; `chat-completion-pipeline-and-generation-tasks.md` |
| `Provider "{provider}" does not support model unloading` | Error (HTTP 400) | `backend/open_webui/main.py:1058-1062` | **Eject** on a model from an OpenAI-compatible connection whose Provider is not `llama.cpp`; `{provider}` reads `default` when none is set | — | Section 5.10 |
| `Model "{model_id}" not found` | Error (HTTP 404) | `backend/open_webui/main.py:1064` | **Eject**: neither the model nor its base model is in the server's Ollama or OpenAI-compatible maps | Reload the page | Map emptied by a recent save (8.3) |
| `Failed to unload model on {len(errors)} node(s): {errors}` | Error (HTTP 500) | `backend/open_webui/main.py:1014-1018` | **Eject**: at least one Ollama server refused or did not answer within 30 seconds; shown as `Error unloading model: {error}` (10.5) | — | Server log `Failed to unload model on Ollama node ...` (`:1011`) |
| `Provider returned HTTP {status_code}` | Error | `backend/open_webui/utils/misc.py:43-46` | A provider's error body could not be read, so only its status is known; shown in the chat's error box | Retry; report the status | Section 5.14 |
| `Provider returned an error` | Error | `backend/open_webui/utils/misc.py:43-46` | As above, when not even a status is known | — | — |

### 10.5 Model Management Screens and the Model Picker (Admin)

Besides the rows below, these screens show any server message from 10.2 to 10.4 as a red pop-up.
A pull started from the picker and the create steps of Manage Ollama also show Ollama's own status
lines (for example its success line) as green pop-ups
(`src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:409`, `:553`;
`src/lib/components/chat/ModelSelector/Selector.svelte:539`).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Checking for model updates...` | Info | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:80` | **Update All Models** pressed (English only, not translated) | Wait | — |
| `Model update cancelled` | Info | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:154` | The update loop was cancelled | — | — |
| `All models are up to date` | Success | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:156` | The update loop finished without being cancelled. Individual failures inside the loop are not reported, so this can appear after a failed update (`:110-146`) | — | Compare model dates on the Ollama server |
| `Model '{modelTag}' is already in queue for downloading.` | Error | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:165-171`; `src/lib/components/chat/ModelSelector/Selector.svelte:464-470`, `:597-603` | The same tag is already downloading in this browser tab | Wait for it | Downloads are tracked per tab (6.5) |
| `Maximum of 3 models can be downloaded simultaneously. Please try again later.` | Error | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:173-176`; `src/lib/components/chat/ModelSelector/Selector.svelte:472-475`, `:605-608` | Three downloads already running in this tab | Wait | As above |
| `Model '{modelName}' has been successfully downloaded.` | Success | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:270-275`; `src/lib/components/chat/ModelSelector/Selector.svelte:564-569`, `:693-698` | Ollama reported success, or the provider's download job completed | Configure and share the model so users can see it (3.2) | With the base-list cache on, press **Refresh** (5.8) |
| `Download canceled` | Error | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:283-285`; `src/lib/components/chat/ModelSelector/Selector.svelte:577-579` | The Ollama pull ended without Ollama's success status: cancelled, failed (its own error pop-up comes first) or cut off | Read the preceding pop-up; try again | Is the tag right? Is the Ollama server reachable and does it have disk space? |
| `{model} download has been canceled` | Success | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:480-494`; `src/lib/components/chat/ModelSelector/Selector.svelte:764-788` | The x on a download was pressed. For an Ollama pull the screen first asks the server to delete the partial model without naming a server; if that request fails (for example with `Model '{model}' was not found`, because a partial model is not listed), this confirmation does not appear (read from code; `backend/open_webui/routers/ollama.py:814-819`) | — | Check the Ollama server for a leftover partial model |
| `Deleted {deleteModelTag}` | Success | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:454-456` | **Delete Model** in Manage Ollama succeeded on that server | — | Workspace models built on it now fail (5.10) |
| `This action cannot be undone. Do you wish to continue?` | Warning (confirmation, title `Confirm your action`) | `src/lib/components/common/ConfirmDialog.svelte:143`, `:153`; used by `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:608-613` | **Delete Model** pressed in Manage Ollama | Confirm or cancel | — |
| `Uploading...` | Info | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:309`, `:1104-1114` | File-mode GGUF upload in progress, before percentages arrive | Wait | — |
| `Failed to fetch models` | Error | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:1142-1145` | That Ollama server's model list could not be read when the pop-up opened (a red pop-up with the reason comes first, `:591-596`) | — | Ollama reachable? Correct position after a removal? |
| `Model download started` | Success | `src/lib/components/admin/Settings/Models/Manage/ManageProviderModels.svelte:145` | llama.cpp or LM Studio download accepted by the provider | Press **Refresh** later | The download runs on the provider |
| `Model loaded successfully` | Success | `src/lib/components/admin/Settings/Models/Manage/ManageProviderModels.svelte:150` | **Load Model** succeeded | — | — |
| `Model unloaded successfully` | Success | `src/lib/components/admin/Settings/Models/Manage/ManageProviderModels.svelte:166`; `src/lib/components/chat/ModelSelector/Selector.svelte:797` | **Unload Model**, or **Eject** in the picker, succeeded | — | — |
| `Model deleted successfully` | Success | `src/lib/components/admin/Settings/Models/Manage/ManageProviderModels.svelte:174` | **Delete Model** (llama.cpp) succeeded | — | — |
| `This will delete the cached model and cannot be undone.` | Warning (confirmation, title `Delete Model`) | `src/lib/components/admin/Settings/Models/Manage/ManageProviderModels.svelte:185-190` | **Delete Model** pressed on a llama.cpp model | Confirm or cancel | — |
| `No models found` | Info | `src/lib/components/admin/Settings/Models/Manage/ManageProviderModels.svelte:225-228` | The provider listed no models, or its list could not be read (a red pop-up comes first) | — | — |
| `No inference engine with management support found` | Info | `src/lib/components/admin/Settings/Models/ManageModelsModal.svelte:102-105` | **Manage Models** opened with no Ollama connection and no llama.cpp or LM Studio connection | — | Section 5.11 |
| `Download failed` | Error | `src/lib/components/chat/ModelSelector/Selector.svelte:678-680` | A llama.cpp or LM Studio download job reported failure without its own error text | Try again | The provider's log |
| `Error unloading model: {error}` | Error | `src/lib/components/chat/ModelSelector/Selector.svelte:791-794` | **Eject** failed; `{error}` is the server's text from 10.4 | — | — |
| `Error deleting model: {error}` | Error | `src/lib/components/chat/ModelSelector/Selector.svelte:821-832` | **Delete** from a model's menu in the picker failed. For a base model the picker always uses the Ollama delete call, so deleting a llama.cpp model from the picker is expected to fail this way (read from code; `src/lib/components/chat/ModelSelector/ModelItemMenu.svelte:26`, `:71`) | Use **Manage Models** for llama.cpp | — |
| `Model {modelName} deleted successfully` | Success | `src/lib/components/chat/ModelSelector/Selector.svelte:837-840` | **Delete** from the picker succeeded | — | — |
| `Are you sure you want to delete **{modelName}**?` | Warning (confirmation, title `Delete Model`) | `src/lib/components/chat/ModelSelector/Selector.svelte:893-902` | **Delete** chosen from a model's menu in the picker (admins; Ollama models and llama.cpp models) | Confirm or cancel | — |
| `Pull "{searchValue}" from Ollama.com` | Info (option) | `src/lib/components/chat/ModelSelector/Selector.svelte:316-327` | An admin typed a name in the picker and at least one Ollama server answered the version check | — | Absent when no Ollama server answers |
| `Download "{searchValue}" from {provider}` | Info (option) | `src/lib/components/chat/ModelSelector/Selector.svelte:330-344` | As above, for each llama.cpp or LM Studio connection | — | — |
| `Downloading "{searchValue}"` | Info (progress) | `src/lib/components/chat/ModelSelector/Selector.svelte:1136`; also `Downloading "{name}"` with ` from {provider}` at `:1220-1224` | A download started from the picker is running in this tab | Wait | — |
| `No models available` | Info | `src/lib/components/chat/ModelSelector/Selector.svelte:1046-1055` | An admin's model list is completely empty | Use the **Manage Connections** link under it | Section 11.2 |
| `Connect to an AI provider to start chatting` | Info | `src/lib/components/chat/ModelSelector/Selector.svelte:1056-1068` | Shown with the previous row, above the **Manage Connections** link (opens the admin Connections tab) | — | — |
| `No results found` | Info | `src/lib/components/chat/ModelSelector/Selector.svelte:1070-1077` | A search matched nothing, or a **non-admin's** model list is empty (non-admins never see the two rows above) | Clear the search; otherwise report it | Section 11.2 |
| `Unloads {FROM_NOW}` | Info (tooltip) | `src/lib/components/chat/ModelSelector/ModelItem.svelte:167-175` | Hovering over the green dot of a loaded Ollama model; `Loaded` when no expiry is known | — | — |

### 10.6 Direct Connections (Users' Own Connections)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Direct connection requires an active WebSocket session; cannot generate completion in this context (e.g. background task).` | Error | `backend/open_webui/utils/chat.py:63-68` | A direct model was used without a live browser session: an automation, timer, scheduled task, API script or some background jobs | Use a system connection for unattended work | Section 5.12 |
| `Client session disconnected.` | Error | `backend/open_webui/socket/main.py:1262-1266` | The tab that sent the message closed, lost its websocket or was removed by the session cleanup (8.1). In a streaming chat the error box shows it inside braces, as `{'error': 'Client session disconnected.'}` (read from code, `backend/open_webui/utils/chat.py:126-128`) | Keep the tab open; resend | Was the tab closed or the laptop asleep? |
| `Event call timed out. The browser tab may be inactive or closed.` | Error | `backend/open_webui/socket/main.py:1279-1281` | Only when `WEBSOCKET_EVENT_CALLER_TIMEOUT` is set: the tab did not answer in time | Bring the tab to the front; resend | Value of `WEBSOCKET_EVENT_CALLER_TIMEOUT` (TO BE CONFIRMED) |
| `An error occurred while fetching the completion` | Error | `src/routes/+layout.svelte:715-717` | The browser's request to the user's provider produced no response object. With the current request helper a failed request raises an error before this check, so the text is not expected in practice (read from code, `src/lib/apis/openai/index.ts:392-419`) | Check the connection's URL | Browser console `chatCompletion` lines |
| `Error: sub-agents are unavailable for direct connections.` | Error (tool result) | `backend/open_webui/utils/subagents.py:334` | A direct model tried to delegate to a sub-agent | — | `chat-completion-pipeline-and-generation-tasks.md` |
| `Connect to your own OpenAI compatible API endpoints.` | Info | `src/lib/components/chat/Settings/Connections.svelte:88`; `src/lib/i18n/locales/en-US/translation.json:2797` | Personal Connections tab, under **Direct Connections** | — | — |
| `Connections managed through the Admin Panel are recommended for everyday use. Direct connections provide convenient access to your own endpoints, but rely on your browser session to keep requests running, making them better suited to testing and temporary use.` | Info | `src/lib/components/chat/Settings/Connections.svelte:138-141` | Always shown on the personal Connections tab | — | — |
| `CORS must be properly configured by the provider to allow requests from Open WebUI.` | Info | `src/lib/components/chat/Settings/Connections.svelte:143-149` | Always shown on the personal Connections tab | — | A provider that blocks browser requests cannot be used directly |
| `Settings saved successfully!` | Success | `src/lib/components/chat/SettingsModal.svelte:811-817` | A personal connection added, edited or switched, or the tab's **Save** pressed; a failed save shows the server's text instead (`:438-443`) | — | — |

When the user's provider refuses the browser's request (wrong key, quota, outage), the browser hands
the provider's error body back and the server raises it as text. Read from code, the error box then
shows a rendering of that body in braces containing the provider's message; after a network or CORS
failure the browser has nothing readable to hand back, and the box may show only `{}`
(`src/routes/+layout.svelte:672-676`, `:718-721`; `backend/open_webui/utils/chat.py:93-128`,
`:142-143`). The exact wording is TO BE CONFIRMED in a test environment (section 14).

### 10.7 Playground (Admin)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Please select a model.` | Error | `src/lib/components/playground/Chat.svelte:89-92` | **Run** in the Chat tab without a model | Choose a model | — |
| `Chat exported successfully` | Success | `src/lib/components/playground/Chat.svelte:282`, `:302` | **Download** > JSON or plain text | — | — |
| `Please enter a prompt` | Error | `src/lib/components/playground/Images.svelte:67-71` | **Run** in the Images tab with an empty prompt | Type a prompt | — |
| `Failed to download image` | Error | `src/lib/components/playground/Images.svelte:100-113` | Clicking a generated image could not fetch it | Try again | — |
| `Generated images will appear here` | Info | `src/lib/components/playground/Images.svelte:169` | Images tab before any result | — | — |
| `Running...` | Info | `src/lib/components/playground/Images.svelte:272` | Image request in progress | Wait | — |

The Chat and Completions tabs show nothing when a request fails (section 5.16); the Images tab shows
the server's text in a red pop-up (`src/lib/components/playground/Images.svelte:92-95`; engines in
`image-generation-and-editing.md`).

### 10.8 Server Log Lines and Browser Console Lines That Explain Symptoms

These are not shown to users. Server logs go to standard output (ground truth); reading them is an
admin or platform task.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Connection error: {e}` | Log (error) | `backend/open_webui/routers/openai.py:116-118`; `backend/open_webui/routers/ollama.py:92-93` | One connection failed or timed out while the model list was built; its models are missing until the next build | — | The URL in `{e}` points at the failing connection |
| `Anthropic connection error: {e}` | Log (error) | `backend/open_webui/utils/anthropic.py:97-99` | Anthropic's model list could not be fetched (network). An Anthropic connection that answers with an error status, such as a refused key, is dropped from the list without an error or warning line (`:70-78`) | — | Use **Verify Connection** on that connection |
| `Upstream {provider} request failed: HTTP {status} ({error_type}) url={base_url} model={model} code={code} message={message}` | Log (warning; error for HTTP 500 and above) | `backend/open_webui/events.py:1237-1249` | A provider answered a request with an error (section 5.14). For Ollama the `url` is the full request address and `model` is `-` (`backend/open_webui/routers/ollama.py:143-150`) | — | `error_type` separates a bad key, a rate limit, an unknown model and a provider outage |
| `Provider returned HTTP %d with SSE content-type: %s` | Log (error) | `backend/open_webui/routers/openai.py:1675-1681` | A provider sent an error status with a streaming content type | — | Followed by the `Upstream` line |
| `Client error: {e}` | Log (exception) | `backend/open_webui/routers/openai.py:928`, `:1147`; `backend/open_webui/routers/ollama.py:282` | Verify or one connection's list hit a network-level failure | — | The real reason behind `OpenAI: Network Problem` or `Ollama: Network Problem` |
| `Unexpected error: {e}` | Log (exception) | `backend/open_webui/routers/openai.py:934`, `:1150`; `backend/open_webui/routers/ollama.py:285` | Verify or one connection's list failed in another way (for example a non-200 answer from Ollama) | — | As above |
| `Error getting OAuth token: {e}` | Log (error) | `backend/open_webui/routers/openai.py:196-203` | Auth `OAuth`: the user's single sign-on token could not be read, so the request goes without one and the provider will usually refuse it | — | `sso-oauth-oidc-and-scim.md` |
| `Error getting Microsoft Entra ID access token: {e}` | Log (error) | `backend/open_webui/routers/openai.py:221-233` | Auth `Entra ID`: the server could not obtain a token from its Azure identity | — | Platform configuration (TO BE CONFIRMED) |
| `Failed to pre-fetch models at startup: {e}` | Log (warning) | `backend/open_webui/main.py:428-429` | The start-up pre-fetch failed (cache switch on) | — | Section 8.4 |
| `Failed to update Redis model cache, using in-process cache: {e}` | Log (warning) | `backend/open_webui/utils/models.py:453-458` | The shared registry could not be written to Redis; this process falls back to its own copy | — | Redis health; see 8.3 item 6 |
| `Model access denied: user_id=%r model_id=%r reason=model_read_denied` | Log (warning) | `backend/open_webui/utils/models.py:475-514`; `backend/open_webui/utils/access_control/__init__.py:333`, `:351`, `:401`, `:412` | The reason behind a `Model not found` for one user; other reasons are `arena_read_denied`, `model_unregistered`, `base_model_unregistered` and `base_model_read_denied` | — | Sharing of the model and its base model (3.2) |
| `Failed to parse error response: {e}` | Log (error) | `backend/open_webui/routers/ollama.py:155-156` | Ollama answered with an error that was not JSON | — | — |
| `Failed to unload model on node {idx}: {e}` | Log (exception) | `backend/open_webui/routers/ollama.py:639-641` | API unload failed on one Ollama server | — | — |
| `Failed to unload model on Ollama node {idx}: {e}` | Log (exception) | `backend/open_webui/main.py:1010-1012`; also `Failed to unload model via llama.cpp: {e}` at `:1055-1057` | **Eject** failed on one server | — | — |
| `OLLAMA_API_CONFIGS is not valid JSON, ignoring` | Log (warning) | `backend/open_webui/config.py:311-312`; also `OPENAI_API_CONFIGS is not valid JSON, ignoring` at `:358-359`, and `OLLAMA_API_CONFIGS must be a JSON object, ignoring` / `OPENAI_API_CONFIGS must be a JSON object, ignoring` at `:310`, `:357` | Invalid JSON, or JSON that is not an object, in the environment seed; logged at each start-up, although the seed is used only while the setting is not yet stored (6.3) | — | — |
| `Ollama port 11434 unreachable on %s, falling back to 12434` | Log (info) | `backend/open_webui/config.py:281-283`; also `Ollama ports 11434 and 12434 both unreachable on %s` at `:284-285` | No Ollama address was configured: only port 12434 answered at start-up, or neither port answered (7.1) | — | — |
| `Event caller: session {session_id} not owned by requesting user or disconnected` | Log (warning) | `backend/open_webui/socket/main.py:1262-1265` | A direct-connection request found no live tab (precedes `Client session disconnected.`) | — | — |
| `Event caller timed out for session {session_id}` | Log (warning) | `backend/open_webui/socket/main.py:1279-1280` | A direct-connection request timed out (precedes `Event call timed out. ...`) | — | — |
| `Failed to load models:` | Browser console | `src/routes/(app)/+layout.svelte:227-229` | The model list could not be loaded when the app opened; nothing is shown on screen | Reload | Browser developer console |
| `Desktop connection update failed:` | Browser console | `src/routes/+layout.svelte:1062-1064` | The desktop application asked to add or remove a connection and the save failed | — | Section 5.17 |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it does not change connections, keys, model sharing, roles or settings. Every
resolution below is guidance or an escalation. Support contacts and escalation routes are TO BE
CONFIRMED (ground truth, Contacts That Exist in the Repository).

**Standard escalation package** (referred to below as "the package"): the time of the problem with
time zone; the page address or chat link; the model name exactly as the picker shows it; the exact
message text or a screenshot; whether colleagues are affected; whether the model carries the
`Direct` label (the user's own connection). Do not collect passwords or API keys. If anyone pastes a
key into a ticket or chat, do not copy it anywhere and ask the key's owner to rotate it.

### 11.1 "A model disappeared from the list"

**Symptom.** A model the user chose before is no longer in the picker; older chats still show its
name.

**Likely causes, in order.**
1. An admin switched off, removed or edited the connection (or the whole **OpenAI API** or **Ollama
   API** type), or switched off or stopped sharing the model record (section 5.9, rows 1 to 3).
2. The provider did not answer within 10 seconds, or refused, at the last list build (5.9, row 4).
3. The model was removed at the provider: deleted from Ollama, retired by the vendor, or an Azure
   deployment deleted (5.9, row 13).
4. The base-list cache is on and holds an older list (5.8, 8.2).
5. A **Model IDs** allow-list or a duplicate id on another connection hides it (5.9, rows 5 and 6).
6. It is hidden in the picker (`workspace-models-and-model-access.md`).
7. It was one of the user's own direct models (go to 11.11).

**Diagnostic steps.**
1. Ask the user to reload the page: the browser loads the list only when the app opens (8.1).
2. Ask whether colleagues still see the model. Everyone affected points to the connection or the
   provider; only this user points to sharing (3.2).
3. Ask whether the model showed the `Direct` label (5.12).
4. Note when it was last seen working and whether an admin changed connections since.

**Resolution.** Suggest another listed model for now. Explain that model availability is set by the
admins.

**Escalation.** Send the package plus when the model was last seen working. The admin can check the
connection row, **Verify Connection**, the model record in **Settings > Admin > AI > Models**, and
server log lines `Connection error: ...` around the user's page load (section 10.8).

### 11.2 "My model list is empty" or "It says No results found"

**Symptom.** A non-admin opens the picker and sees `No results found` without typing anything; an
admin sees `No models available` and `Connect to an AI provider to start chatting` (section 10.5).

**Likely causes, in order.**
1. Only this user: no model is shared with them. Models without a model record, or not shared
   (Public or with one of their groups), are visible to admins only (3.2).
2. Everyone: every provider failed during the last list build (outage, network, expired keys). Just
   after an admin saved connections there is no fallback list, and workspace and arena models
   disappear too (8.3, items 2 and 5).
3. Both the **OpenAI API** and **Ollama API** switches are off and no pipe function is installed
   (5.7, step 3).
4. The list request failed when the page loaded (only the browser console shows
   `Failed to load models:`, 10.8).

**Diagnostic steps.**
1. Ask the user to reload.
2. Ask whether a colleague in the same group sees models, and whether an admin does.
3. Ask whether the empty list started just after a connection change (8.3).
4. If the user can open the browser's developer console, look for `Failed to load models:`.

**Resolution.** Only this user affected: escalate for sharing or group membership. Everyone affected:
treat as a service problem and escalate at once.

**Escalation.** The package, plus the user's role (not their name) and whether anyone else sees
models. For the admin: Connections tab state and the server log around the time
(`Connection error: ...`, `Failed to pre-fetch models at startup: ...`).

### 11.3 "It says the model isn't found"

**Symptom.** A pop-up and grey box reading `Model not found` right after Send; or
`Model '' was not found` under an answer (a background task); or, for a script, HTTP 403
`Model not found`.

**Likely causes, in order.**
1. The page is stale: the model was removed or switched off after the page loaded (5.4, 8.1).
2. An admin had just saved connections and the server's rebuild did not find the model (8.3).
3. It is a workspace model whose base model has gone (5.4, last bullet).
4. The user may not use the model: refusals are worded as `Model not found` (10.4; server log
   `Model access denied: ...`).
5. Under an answer, `Model '' was not found` from a title, tag or follow-up task in the seconds after
   a connection save; it is transient (10.4).
6. A provider's own "model not found" sentence is a different case (go to 11.5).

**Diagnostic steps.** Reload and retry; check whether the model is still in the picker; ask whether
the chat was shared by someone else or the call came from a script; note the time and any connection
change. Display details are in `chat-completion-pipeline-and-generation-tasks.md`.

**Resolution.** Reload and choose a listed model. If the model is listed and still refused, escalate
as a sharing question.

**Escalation.** The package. The admin checks the model record, its base model and the log line
`Model access denied: ...` with its `reason=` (10.8).

### 11.4 "Verify connection fails" (Admin)

**Symptom.** In the connection pop-up, **Verify Connection** shows `OpenAI: Network Problem`,
`OpenAI: {error.message}` or `Ollama: Network Problem`.

**Likely causes, in order.**
1. Wrong URL: an OpenAI-compatible URL without its `/v1` part, or an Ollama URL with `/api` or `/v1`
   added; a typo; `http` instead of `https`.
2. Wrong, expired or under-privileged key (the provider's sentence usually says so).
3. The server cannot reach the provider: network, proxy, DNS or certificate checking, or the
   10-second limit (5.6, 7.2).
4. The provider offers no model list; Verify fails although chat works once **Model IDs** are filled
   in (5.6).
5. A URL on `api.anthropic.com`: every failure reads `OpenAI: Network Problem`.
6. For a user's own connection: the provider does not accept requests from a browser (CORS).

**Diagnostic steps.** Read the message (the text after `OpenAI:` is the provider's); remember that
Verify checks only the model list; ask an admin for the server log lines `Client error: ...` or
`Unexpected error: ...` at that time (10.8).

**Resolution.** Guidance only. Saving does not require a successful Verify, so a connection can be
saved and still contribute nothing (5.1).

**Escalation.** The connection URL (never the key), the message, the time, and whether other
connections verify.

### 11.5 "Every answer fails with a message about the API key, quota or rate limit"

**Symptom.** The grey error box shows the provider's own sentence about an invalid key, exhausted
quota, too many requests or an unknown model.

**Likely causes, in order.**
1. The provider key was revoked, expired or ran out of credit (HTTP 401, 403 or 429 at the
   provider).
2. A rate limit at busy times (HTTP 429).
3. The key does not give access to that particular model (HTTP 404 that mentions the model).
4. Auth `OAuth` or `Entra ID`: the server could not get a token, so the provider refused the request
   (10.8).

**Diagnostic steps.** Note the exact sentence; ask whether all models from the same provider fail or
one; ask whether other people are affected. The admin's log line
`Upstream ... request failed: HTTP {status} ({error_type})` names the type (`authentication_failed`, `rate_limited`, `model_not_found`)
and the connection (5.14).

**Resolution.** For rate limits, wait and retry, or use another model. Key, quota and billing
questions go to the connection's owner (TO BE CONFIRMED).

**Escalation.** The package plus the provider's sentence.

### 11.6 "Answers fail with Open WebUI: Server Connection Error"

**Symptom.** The error box reads `Open WebUI: Server Connection Error`; for Ollama models it may read
`Ollama: ...` followed by a network description (10.3).

**Likely causes, in order.**
1. The provider or Ollama server is down or unreachable from the server (network, DNS, certificate).
2. A configured time limit (`AIOHTTP_CLIENT_TIMEOUT`) expired (5.13).
3. With several Ollama servers offering the same model, the randomly chosen one is broken (5.5).

**Diagnostic steps.** Ask whether every model fails or only one provider's; whether it fails every
time or sometimes; note the time. The admin finds the exception in the server log just before the
failure and can use **Verify Connection**.

**Resolution.** Retry later or use a model from another provider.

**Escalation.** The package, marked as possibly affecting everyone on that provider.

### 11.7 "Some answers fail and others work with the same model"

**Symptom.** The same model answers sometimes and fails at other times.

**Likely causes, in order.**
1. Ollama: the model is on several servers and each request picks one at random; one server is
   failing (5.5).
2. Several server processes without Redis after a connection change: some processes still hold the
   old connection positions (8.3, item 6).
3. Short rate-limit bursts at the provider (11.5).
4. Auth `Session` or `OAuth`: the result depends on each person's own session.

**Diagnostic steps.** Collect times of failures and successes and the exact messages; ask whether
an admin changed connections recently.

**Resolution.** Retry; escalate the pattern.

**Escalation.** The package with several failure and success times. The admin compares the
`Upstream ... url=` field across failures (10.8).

### 11.8 "The new model the admin added doesn't show up for me"

**Symptom.** An admin says a model was added, but the user does not see it.

**Likely causes, in order.**
1. The model has no model record or is not shared with the user's groups; until then only admins
   see it (3.2).
2. The base-list cache is on and nobody pressed **Refresh** since the model appeared; admins do not
   see it either (5.8, 8.2).
3. A connection with Auth `Session` or `OAuth` after a restart with the cache on (8.4).
4. The user's page is older than the change.
5. A **Model IDs** allow-list on the connection excludes it.

**Diagnostic steps.** Reload; ask whether the admin sees it in the picker.

**Resolution.** Escalate to the admin: create and share the model record, or press **Refresh**.

**Escalation.** The package plus the user's group names if known (no personal details beyond what
the ticket needs).

### 11.9 "Nobody can chat since the admin changed a connection"

**Symptom.** Right after a connection save, pickers are empty or chats fail with `Model not found`;
titles may fail with `Model '' was not found`.

**Likely causes, in order.**
1. The server rebuilt its list after the save and every provider failed, so no fallback list was
   left (8.3, item 5).
2. The changed connection is wrong (URL, key, Auth) and carried most models; saving does not check
   it (5.1).
3. The **OpenAI API** or **Ollama API** switch was turned off; switches save at once (5.4).
4. With several server processes and no Redis, positions shifted after a removal (8.3, item 6).

**Diagnostic steps.** Note the time of the change and of the first failure; ask users to reload once.

**Resolution.** Escalate at once to the admin who made the change (revert or correct it, then press
**Refresh** if the cache is on).

**Escalation.** The package, marked urgent, with the time of the connection change.

### 11.10 "Ollama download is stuck" (Admin)

**Symptom.** In **Manage Ollama** or the picker the progress bar stops moving, the download ends with
`Download canceled`, or a new pull is refused with
`Model '{modelTag}' is already in queue for downloading.` or
`Maximum of 3 models can be downloaded simultaneously. Please try again later.`

**Likely causes, in order.**
1. A large model on a slow link: progress is per layer, so the bar restarts for each layer and the
   digest line under it changes (5.10).
2. Ollama refused: unknown tag, no disk space, registry unreachable. Its error appears as a pop-up,
   followed by `Download canceled` (10.5).
3. Three downloads already run in this tab, or the same tag is already downloading (per tab, 6.5).
4. The tab was closed or reloaded; what Ollama does then is TO BE CONFIRMED (5.10).
5. **Update All Models** reported `All models are up to date` although a pull inside it failed
   (10.5).

**Diagnostic steps.** Watch whether the percentage or digest changes; read any red pop-up; check the
tag on the Ollama library page linked from the pop-up.

**Resolution.** Pulling models is an admin task. Keep the tab open; cancel and try again; escalate
if Ollama itself refuses.

**Escalation.** The tag, the Ollama connection's address, the time, the last percentage and any
error text. The platform maintainer checks the Ollama server's disk and log.

### 11.11 "My own connection in Settings doesn't work"

**Symptom.** Models from the user's own endpoint do not appear (no `Direct` filter chip),
**Verify Connection** shows `OpenAI: Network Problem`, or chats with a direct model fail with
`Client session disconnected.`, with the message beginning `Direct connection requires an active WebSocket session`
(full text in 10.6), with text in braces, or with `{}`.

**Likely causes, in order.**
1. The provider does not accept requests from a browser on MedIT GPT's address (CORS); the browser,
   not the server, makes these calls (5.12).
2. Wrong URL (the API base, usually ending in `/v1`) or key.
3. The tab was closed, asleep or offline while the answer was being produced.
4. The model was used by something that runs without the user's tab (automation, timer, scheduled
   task, script).
5. An admin switched **Direct Connections** off, so saved connections are ignored (go to 11.12).
6. A deleted connection came back: deleting needs the tab's **Save** (5.12, step 4).

**Diagnostic steps.** Ask the user to press **Verify Connection** in their pop-up; if they can open
the browser's developer console, CORS refusals are named there; check whether the failure happened
in an automation.

**Resolution.** Guide the user to correct their own URL or key (the user's own setting), keep the tab
open while answers are produced, and use admin-managed models for everyday or unattended work, as
the screen itself advises (10.6). Whether support assists with personal endpoints is TO BE
CONFIRMED.

**Escalation.** The package; never the user's key.

### 11.12 "I don't see Connections in my Settings"

**Symptom.** The user cannot find **Connections** under **Settings > Personal > Services**.

**Likely causes, in order.**
1. **Direct Connections** is off (the code default); the tab exists only while it is on (5.12;
   `src/lib/components/chat/SettingsModal.svelte:381-383`).
2. The user is looking for the admin Connections tab, which only admins have (2.1).

**Diagnostic steps.** None beyond confirming the user's role.

**Resolution.** Explain that the feature is switched off for this site; whether it should be offered
is an admin decision (TO BE CONFIRMED).

**Escalation.** Only if the user's work needs it: send the request to the admins.

### 11.13 "Answers take forever or never finish"

**Symptom.** After Send nothing arrives for a long time, or the answer stops mid-way and never
completes.

**Likely causes, in order.**
1. Chat calls have no overall time limit unless `AIOHTTP_CLIENT_TIMEOUT` is set (5.13), so a slow or
   stuck provider can keep a request open.
2. An Ollama model is being loaded into memory, because it was unloaded or not yet used (section 4,
   **Load / Unload**; the picker's green dot and its `Unloads {FROM_NOW}` tooltip show loaded models,
   10.5).
3. Provider-side queueing at busy times.
4. For a direct model, the tab went to sleep (11.11).

**Diagnostic steps.** Note the time to first word; ask whether another model answers quickly.

**Resolution.** Press Stop and retry, or switch model.

**Escalation.** The package with timings.

### 11.14 "The model list takes a long time to load"

**Symptom.** The picker or the whole page is slow to show models, often by about ten seconds.

**Likely causes, in order.**
1. A connection that is down but still switched on: each list build waits up to 10 seconds for it
   (5.7; 7.2).
2. The cache switch is off, so every page load asks every connection (5.8).
3. The first request after a connection save rebuilds the list (8.3).

**Diagnostic steps.** Ask whether the delay happens on every page load and for everyone.

**Resolution.** Escalate; switching off a dead connection or turning the cache on are admin
decisions.

**Escalation.** The package plus how long the delay lasts. The admin looks for
`Connection error: ...` at each page load (10.8).

### 11.15 "The Playground does nothing when I press Run" (Admin)

**Symptom.** In **Playground > Chat** or **Completions**, **Run** produces no answer and no message.

**Likely causes, in order.**
1. The request failed: these tabs show nothing on failure (5.16).
2. No model chosen (the Chat tab then says `Please select a model.`).
3. A non-admin following a link is sent back to the home page (2.1).

**Diagnostic steps.** Send the same text to the same model in a normal chat to read the error.

**Resolution.** Use the normal chat's error text with the relevant symptom above.

**Escalation.** The package from the normal chat attempt.

## 12. Local Customisations

**This area matches upstream Open WebUI v0.11.4.** The read-only comparisons
`git diff --stat main...uoft -- <paths>` and `git diff --stat -- <paths>` show no difference, on the `uoft` branch or
in the uncommitted working tree, for any file in this area's scope: the two provider routers, the
model-list utilities, the `main.py` model endpoints, the admin and personal Connections components,
the connection pop-up, the `openai` and `ollama` API clients, `src/lib/utils/connections.ts`, the
Playground routes and components, `backend/open_webui/config.py`, and the model-management screens
and model picker cited in sections 5 and 10.

Two neighbouring files that this document cites do differ on `uoft` (ground truth, Version and
Identity):

| File | Fork change | Effect in this area |
|---|---|---|
| `backend/open_webui/env.py:951` | Default `WEBUI_NAME` is `MedIT GPT`, without the upstream " (Open WebUI)" suffix | The Playground's browser tab reads "Playground / MedIT GPT" with the default name (section 2.1); the live name is environment data, TO BE CONFIRMED |
| `src/routes/+layout.svelte:622`, `:760`, `:873` | Browser notification titles use the site name instead of "Open WebUI" | None: these lines are outside the direct-connection relay (`:646-731`) and the desktop handler (`:979-1065`); each edit replaces one line, so the line numbers cited here are unchanged |

The uncommitted working-tree changes (ground truth) touch none of the files above, and the changes
in `src/lib/i18n/locales/en-US/translation.json` do not touch the connection keys cited in this
document.

**Upstream wording that users still see.** Some messages and texts in this area still say "Open
WebUI"; several are protected by licence comments and the fork leaves them unchanged (`CLAUDE.md`,
Conventions):

- `Open WebUI: Server Connection Error` (`backend/open_webui/constants.py:127-130`;
  `backend/open_webui/routers/openai.py:664-669`, `:929-932`, `:2107-2112`);
- `CORS must be properly configured by the provider to allow requests from Open WebUI.`
  (`src/lib/components/chat/Settings/Connections.svelte:144-149`);
- `Forward cookies from your Open WebUI request to this server.`
  (`src/lib/components/AddConnectionModal.svelte:521`);
- the identification headers sent to OpenRouter (`backend/open_webui/routers/openai.py:166-176`);
- the `Click here for help.` link under the Ollama list, which opens the upstream project's
  troubleshooting page (`src/lib/components/admin/Settings/Connections.svelte:357-363`).

Support should expect users to quote these "Open WebUI" texts although the site is branded MedIT GPT.

## 13. Source File Index

### 13.1 Backend

| File | What it holds for this area | Key lines |
|---|---|---|
| `backend/open_webui/routers/openai.py` | The `/openai` router: model-list fetch and merge, connection settings, cache clearing, llama.cpp and LM Studio management, Verify, Azure handling, Responses conversion, chat, embeddings, Responses route, pass-through | `:89-131`, `:155-233`, `:305-357`, `:360-452`, `:544-597`, `:676-941`, `:944-1056`, `:1059-1151`, `:1154-1248`, `:1251-1483`, `:1486-1754`, `:1757-1860`, `:1883-1991`, `:1994-2116` |
| `backend/open_webui/routers/ollama.py` | The `/ollama` router: request helpers, Verify, settings, list and merge, loaded models, version, unload, pull, push, create, copy, delete, show, embeddings, generate, chat and the OpenAI- and Anthropic-compatible proxies, GGUF transfer | `:69-197`, `:248-286`, `:289-352`, `:355-505`, `:508-585`, `:595-838`, `:841-1172`, `:1215-1527`, `:1550-1723` |
| `backend/open_webui/utils/models.py` | Base-list assembly, the base-list cache, model records, defaults, actions and filters, the registry, access checks and filtering | `:32-66`, `:69-113`, `:167-267`, `:337-356`, `:445-462`, `:465-521`, `:524-578` |
| `backend/open_webui/main.py` | Start-up pre-fetch; provider state; `/api/models`, `/api/models/base`, `/api/models/unload`, `/api/embeddings`; chat model resolution and its errors | `:390`, `:407-429`, `:471`, `:563`, `:572`, `:612`, `:794`, `:897-1094`, `:1097-1182`, `:1638-1722` |
| `backend/open_webui/routers/configs.py` | **Direct Connections**, **Direct Integrations** and **Cache Base Model List** settings | `:40-44`, `:128-160` |
| `backend/open_webui/config.py` | Environment seeds and defaults for `openai.*`, `ollama.*`, `direct.*`, `models.*`; the Ollama port fallback | `:230`, `:237-374`, `:1695-1709`, `:2823-2832`, `:3094-3095` |
| `backend/open_webui/env.py` | Time limits, cache lifetime, Redis settings, pass-through and forwarded-header switches, `WEBUI_NAME` | `:381-384`, `:476`, `:493`, `:534-542`, `:608-677`, `:832`, `:859-862`, `:951`, `:989-1009`, `:1033-1043` |
| `backend/open_webui/constants.py` | Texts of `MODEL_NOT_FOUND`, `OPENAI_NOT_FOUND`, `OLLAMA_NOT_FOUND`, `OLLAMA_API_DISABLED`, `SERVER_CONNECTION_ERROR`, `ACCESS_PROHIBITED` | `:70-72`, `:89-91`, `:103`, `:127-130` |
| `backend/open_webui/events.py` | Event definitions, the notification list, webhook matching and delivery, the provider-failure log line and event | `:68-72`, `:456-475`, `:669-675`, `:831-870`, `:1040-1066`, `:1159-1273` |
| `backend/open_webui/utils/chat.py` | Direct-connection completion through the user's tab | `:49-145` |
| `backend/open_webui/socket/main.py` | Shared registry, direct-reply channel, session-pool cleanup, Redis relay, catch-all handler, event caller | `:129-148`, `:185`, `:199`, `:212-263`, `:963-1016`, `:1258-1286` |
| `backend/open_webui/socket/utils.py` | Redis-backed dictionaries used for the registry | `:71-238` |
| `backend/open_webui/utils/redis.py` | The general Redis connection used by the base-list cache | `:88-105` |
| `backend/open_webui/utils/session_pool.py` | Outbound connection pool and time limits | `:43-76` |
| `backend/open_webui/utils/anthropic.py` | Anthropic model listing and URL detection | `:35-101`, `:131-136` |
| `backend/open_webui/utils/embeddings.py` | Embeddings dispatcher | `:24-88` |
| `backend/open_webui/utils/misc.py` | Provider error text for the chat | `:43-65` |
| `backend/open_webui/utils/access_control/__init__.py` | Access checks for direct `/openai` and `/ollama` calls | `:333`, `:351`, `:361-413` |
| `backend/open_webui/utils/headers.py` | User-information headers and header placeholders | `:52-82`, `:107-163` |
| `backend/open_webui/utils/model_ids.py` | Prefix ID removal | `:1-4` |
| `backend/open_webui/utils/task.py` | Connection type and the task model | `:15-25` |
| `backend/open_webui/routers/tasks.py` | Task model check that fails while the registry is empty | `:163-167` |
| `backend/open_webui/models/config.py` | The `config` table and the recognized connection option fields | `:40-55`, `:101-108` |
| `backend/open_webui/utils/subagents.py` | Sub-agent refusal for direct models | `:334` |

### 13.2 Front End

| File | What it holds for this area | Key lines |
|---|---|---|
| `src/lib/components/admin/Settings/Connections.svelte` | Admin Connections tab: switches, lists, saves, Refresh | whole file (`:28-221`, `:224-437`) |
| `src/lib/components/admin/Settings/Connections/OpenAIConnection.svelte` | One OpenAI-compatible row | whole file |
| `src/lib/components/admin/Settings/Connections/OllamaConnection.svelte` | One Ollama row, with the Manage button | whole file |
| `src/lib/components/admin/Settings/Connections/ManageOllamaModal.svelte` | The `Manage Ollama` pop-up | whole file |
| `src/lib/components/AddConnectionModal.svelte` | Add and Edit Connection pop-up for all three connection kinds | `:76-244`, `:285-822` |
| `src/lib/components/chat/Settings/Connections.svelte` | Personal Connections tab | whole file |
| `src/lib/components/chat/Settings/Connections/Connection.svelte` | One personal connection row | whole file |
| `src/lib/components/chat/SettingsModal.svelte` | Tab gating, personal settings save, save pop-ups | `:379-383`, `:438-451`, `:811-817`, `:857-862` |
| `src/lib/apis/openai/index.ts` | OpenAI-compatible API client: settings, lists, management, Verify, chat | whole file |
| `src/lib/apis/ollama/index.ts` | Ollama API client | whole file |
| `src/lib/apis/index.ts` | Model list with direct connections; unload | `:23-214` |
| `src/lib/apis/configs/index.ts` | Connections settings client | `:88-116` |
| `src/lib/utils/connections.ts` | Add and remove helpers used by desktop events | whole file |
| `src/routes/+layout.svelte` | Direct-connection relay; desktop events | `:646-731`, `:979-1065` |
| `src/routes/(app)/+layout.svelte` | Model list at app start | `:83-90`, `:212-229` |
| `src/routes/(app)/playground/+layout.svelte` | Playground frame, tabs and title | whole file |
| `src/routes/(app)/playground/+page.svelte`, `src/routes/(app)/playground/completions/+page.svelte`, `src/routes/(app)/playground/images/+page.svelte` | Mount the three Playground tabs | whole files |
| `src/lib/components/playground/Chat.svelte`, `src/lib/components/playground/Chat/Message.svelte`, `src/lib/components/playground/Chat/Messages.svelte` | Playground Chat tab | whole files |
| `src/lib/components/playground/Completions.svelte` | Playground Completions tab | whole file |
| `src/lib/components/playground/Images.svelte` | Playground Images tab | whole file |
| `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte` | Ollama pull, update, delete, create and upload (scope shared with `workspace-models-and-model-access.md`) | whole file |
| `src/lib/components/admin/Settings/Models/Manage/ManageProviderModels.svelte` | llama.cpp and LM Studio management | whole file |
| `src/lib/components/admin/Settings/Models/Manage/ManageMultipleOllama.svelte`, `src/lib/components/admin/Settings/Models/Manage/ManageMultipleProviderModels.svelte`, `src/lib/components/admin/Settings/Models/ManageModelsModal.svelte` | Instance and engine pickers for **Manage Models** | whole files |
| `src/lib/components/chat/ModelSelector/Selector.svelte` | Pull and download from the picker, Eject, delete, empty-list texts | `:312-346`, `:460-856`, `:893-902`, `:1046-1077`, `:1130-1240` |
| `src/lib/components/chat/ModelSelector/ModelItem.svelte`, `src/lib/components/chat/ModelSelector/ModelItemMenu.svelte` | Loaded indicator, Eject button, Delete menu entry | `:167-188`, `:282-297`; `:26`, `:71` |
| `src/lib/components/chat/Settings/About.svelte` | Ollama version line | `:40-43`, `:112-118` |
| `src/lib/components/common/ConfirmDialog.svelte` | Default confirmation texts | `:143`, `:153` |
| `src/lib/stores/index.ts` | `MODEL_DOWNLOAD_POOL` store | `:28` |
| `src/lib/i18n/locales/en-US/translation.json` | English text of the dotted keys used here | `:2168-2182`, `:2614`, `:2738`, `:2797-2800` |

## 14. Open Questions

Everything below could not be established from the repository, or was read from code and needs a
test environment. Items flagged in earlier sections are gathered here so this section is the
complete record.

### 14.1 Data and Deployment Facts (TO BE CONFIRMED)

1. **Live connection settings.** The values of `openai.enable`, `openai.api_base_urls`,
   `openai.api_configs`, `ollama.enable`, `ollama.base_urls`, `ollama.api_configs`, `direct.enable`,
   `direct.integrations.enable`, `models.base_models_cache`, `models.default_metadata` and
   `models.default_params` are data in the `config` table, which was not read (At a Glance; sections
   6 and 7). Keys are secrets and are not to be recorded anywhere.
2. **Providers in use.** Which providers production connects to (OpenAI, Azure OpenAI, Anthropic,
   Ollama, llama.cpp, LM Studio, LiteLLM, a Pipelines server) and which Auth type each connection
   uses (section 4).
3. **Environment values.** `AIOHTTP_CLIENT_TIMEOUT`, `AIOHTTP_CLIENT_STREAM_IDLE_TIMEOUT`,
   `AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST`, `AIOHTTP_CLIENT_SESSION_SSL`, `MODELS_CACHE_TTL`,
   `ENABLE_OPENAI_API_PASSTHROUGH`, `ENABLE_FORWARD_USER_INFO_HEADERS`, `BYPASS_MODEL_ACCESS_CONTROL`,
   `BYPASS_ADMIN_ACCESS_CONTROL`, `ENABLE_CUSTOM_MODEL_FALLBACK`, `WEBSOCKET_EVENT_CALLER_TIMEOUT`,
   `WEBSOCKET_MANAGER`, `REDIS_URL`, `WEBSOCKET_REDIS_URL`, `REDIS_KEY_PREFIX` and the number of server
   processes (`UVICORN_WORKERS`, replicas). These decide whether the multi-process behaviours in
   sections 5.8, 8.2 and 8.3 apply (sections 2.2, 3.2, 5.13, 7.2).
4. **Site identity.** The production host name (section 2) and the live `WEBUI_NAME` (section 12).
5. **Desktop application.** Whether anyone uses the Open WebUI desktop application with MedIT GPT
   (section 5.17).
6. **Upstream resources.** Whether users and admins should be sent to upstream pages such as the
   `Click here for help.` troubleshooting link (sections 5.5, 10.1, 12).
7. **Organisation.** Support contacts and escalation routes; who owns provider keys, quotas and
   billing; whether support helps with users' personal endpoints; whether **Direct Connections**
   should be offered (section 11).

### 14.2 Behaviour Read From Code, To Confirm in a Test Environment

1. Whether an Ollama pull continues after the admin's tab closes (sections 5.10, 8.5).
2. Whether a URL-mode GGUF upload ends without a usable model, because the browser's follow-up
   create request does not match the API helper's parameters (section 5.10).
3. Whether a failed GGUF transfer leaves its file in the upload folder (section 6.6).
4. **Refines section 5.10 (upload outcome).** The failure texts
   `Ollama: Could not create blob, Please try again.` and
   `Failed to create model in Ollama. {resp_text}` are written only to the
   browser console in File mode, and URL mode ends the stream without a message (section 10.3).
5. **Refines section 5.10 (cancel a pull).** The confirmation `{model} download has been canceled`
   appears only if the follow-up delete succeeds; the delete names no server and fails for a model
   that is not listed (section 10.5).
6. **Refines section 5.1.** An empty URL is normally caught by the browser's own required-field
   prompt before `URL is required` can appear (section 10.1).
7. After the Save-time headers check fails, the pop-up's **Save** button stays busy until the
   settings tab is changed or the page reloaded (section 10.1).
8. The admin tab's `Settings saved successfully!` appears without waiting for the saves it starts
   (section 10.1).
9. **Direct-connection failure wording.** When the user's provider refuses the browser's request, the
   error box is expected to show a rendering of the provider's error body in braces, and `{}` after a
   network or CORS failure (sections 5.12, 10.6). Not established beyond the code.
10. After a connection removal, server processes without a shared registry may send requests to the
    connection now holding the old position, or fail (section 8.3, item 6).
11. With the cache on, connections using Auth `Session` or `OAuth` contribute nothing to the
    start-up pre-fetch and stay missing until a Refresh or save (section 8.4).
12. **Refines section 5.8 ("restart").** A base list held in Redis survives a restart of MedIT GPT;
    only a connection save, a llama.cpp or LM Studio model change, or a Refresh replaces it
    (section 8.2).
13. The exact body returned by `/api/embeddings` for `Model not found` (HTTP 500), which the web
    framework produces (sections 5.15, 10.4).
14. The legacy speech route passes the uncalled message function `OPENAI_NOT_FOUND`, so its reply is
    probably a generic server error rather than `OpenAI API was not found` (section 10.2).
    *Resolved 2026-10-10: the backend content catalogue ran the error handler against the pinned
    FastAPI in the project environment (without starting the app) and confirmed callers get a bare
    server error; `OpenAI API was not found` is never sent
    (`error-messages-backend-chat-content-and-features.md` section 14.1).*
15. Deleting a llama.cpp model from the model picker is expected to fail with
    `Error deleting model: {error}`, because the picker uses the Ollama delete call (section 10.5).
16. **Update All Models** reports `All models are up to date` even when a pull inside it failed
    (section 10.5).
17. Two admins editing connections at the same time can overwrite each other, because each save
    sends the whole list (section 7.3).
18. The cache consequences listed in section 5.8: pulled, created or deleted Ollama models not
    appearing until **Refresh**; per-process copies without Redis; a shared list built with one
    person's credentials for `Session` and `OAuth` connections.
19. The wording Ollama, providers and browsers use in their own messages (progress lines, "model not
    found", invalid key, CORS refusals, the required-field prompt) is outside the repository.

### 14.3 Security-Sensitive Questions (Referred, Not Documented)

For each item: Security-sensitive: refer to the platform maintainer and U of T Information Security
(security.utoronto.ca).

1. How admin connection keys and users' direct-connection keys are stored and protected
   (sections 5.12, 6.1, 6.5).
2. What the `Session`, `OAuth`, `Entra ID` and `Forward cookies` options and the header placeholders
   send to providers, and which providers may receive them; personal data in header placeholders and
   in the user-information headers (sections 5.2, 5.13).
3. Personal data sent to Pipelines servers with each request (section 5.13).
4. Whether the generic `/openai` pass-through should ever be switched on, and the security of the
   proxy routes in general (sections 2.2, 10.2).
5. The options the server sets on Ollama pull requests (section 8.5).
6. What the `model.provider_request.failed` event and the webhooks that receive it carry about
   connections and their keys (section 9.3).
7. Desktop-application events that add or remove system connections through an admin's browser
   (section 5.17).
8. Certificate checking for outbound provider calls (`AIOHTTP_CLIENT_SESSION_SSL`) in production
   (section 7.2).

### 14.4 Consistency With Ground Truth

No statement in `knowledgebase/tools/ground-truth.md` or `knowledgebase/tools/inventory.md` was found
to be contradicted by the code read for this area. The refinements in 14.2 (items 4, 5, 6 and 12)
concern this document's own earlier sections, which were left unchanged as instructed; a later
correction pass should reconcile them and log the change in `tools/VERIFICATION.md`.
