# Backend Architecture and Request Lifecycle

## At a Glance

- MedIT GPT is one FastAPI application (`backend/open_webui/main.py`) that serves both the API and
  the built single-page front end from the same origin; there is no separate web server in the
  repository.
- Every browser request passes through a stack of middleware (CORS, compression, security
  headers, audit logging, an HTTP middleware that picks up the bearer token) before it reaches one
  of 31 routers mounted under `/api/v1/...` or one of the top-level endpoints defined directly in
  `main.py`. *Corrected 2026-10-11: the HTTP middleware only picks up the credential; the route's
  own dependency checks it (section 3.2). A session-cookie layer is also present, and the security
  headers are added by the same HTTP middleware (section 4.2). Two of the 31 routers are mounted at
  `/ollama` and `/openai`, and two (analytics, SCIM) only when switched on (section 2.2).*
- Start-up runs in a fixed order inside `lifespan` (migrations at import, configuration seeding,
  optional admin bootstrap, plugin requirement installs, background loops); `/health` answers as
  soon as the process serves, while `/ready` waits for start-up to finish. *Corrected 2026-10-11:
  migrations run while the configuration module is imported, before `lifespan` starts; and under
  uvicorn the port opens only after start-up, so neither probe answers before then. `/ready`
  additionally checks the database and, when configured, Redis (sections 5.4 and 5.5).*
- `/api/config` is the first call the front end makes; what it returns depends on whether the
  visitor is signed out, pending or signed in, and the front end shows "Backend Required" when it
  cannot get a valid answer.
- *Added 2026-10-11:* role refusals answer HTTP 401, not 403 (section 3); `/health` proves only
  that the process answers, `/ready` names a failing database or Redis (section 5.5).
- *Added 2026-10-11:* the pictures under `/static` are copied from the front-end build at every
  start-up, so the build decides whether users see U of T or upstream artwork (section 5.7).
- *Added 2026-10-11:* the update notice compares with **upstream** Open WebUI releases; security
  headers are added only when their environment variables are set; the shared outbound HTTP
  client has no connection limit or overall time-out unless configured (sections 5.6, 5.9, 5.11).
- *Added 2026-10-11:* read from code, an unknown `AUDIT_LOG_LEVEL` value is expected to stop
  start-up, which differs from the configuration document (section 14.3).

## 1. Purpose and Who Uses It

This document explains how the MedIT GPT server is put together and what happens to a request
between the browser and the code that answers it. It is the map that the feature documents hang
from: when a user reports that "nothing loads", "it says Backend Required" or "the health check is
green but nobody can sign in", the answer is usually in one of the layers described here rather
than in a single feature.

In plain terms:

- **One process serves everything.** The backend is a single FastAPI application created in
  `backend/open_webui/main.py:506-512`. The same process answers the API (`/api/...`), the model
  proxies (`/ollama`, `/openai`), the websocket (`/ws`, `backend/open_webui/main.py:840`), the
  static pictures (`/static`, `backend/open_webui/main.py:3023`) and, when a front-end build is
  present, the whole single-page front end (`/`, `backend/open_webui/main.py:3066-3075`). Without a
  build it logs a warning and serves the API only (`backend/open_webui/main.py:3076-3077`).
- **The browser and the API share one origin.** The front end calls relative URLs such as
  `/api/config` and sends its sign-in token with its calls (section 5.1), so there is no separate
  API host to configure.
- **A request passes several layers** (section 4.2): Starlette's error handler, the session
  cookie layer, CORS, the application's own HTTP middleware (security headers, token pick-up,
  legacy redirects, database session clean-up), optional compression and optional audit logging,
  then the route. The route's dependencies decide whether the caller is allowed in (section 3).
- **Start-up is a fixed sequence** (section 5.4): database migrations run while the configuration
  module is imported, then `lifespan` (`backend/open_webui/main.py:344-497`) seeds settings,
  optionally creates the first admin, installs plugin requirements, starts background loops and
  finally marks the instance ready.

Who uses this document:

| Reader | What they need from it |
|---|---|
| Tier-1 support | Which layer a symptom belongs to (sections 5, 10 and 11); which feature document to open next (the router table in section 2.2) |
| Platform maintainer | Start-up order and failure modes, health and readiness probes, security-header switches, static-file behaviour (sections 5, 7 and 8) |
| Feature researchers and writers | The authoritative list of mount prefixes and top-level endpoints (section 2) |

End users never see this layer directly; they see its effects (the loading splash, the "Backend
Required" page, sign-in failures, missing pictures). Chat-completion internals (filters, tools,
retrieval, streaming) are out of scope here and are described in
[`chat-completion-pipeline-and-generation-tasks.md`](chat-completion-pipeline-and-generation-tasks.md).

## 2. Navigation and URLs

All addresses below are relative to the site root; the production host name is **TO BE
CONFIRMED**. Users do not normally type API addresses; the front end calls them. Front-end pages
(`/`, `/c/{id}`, `/admin/...`, `/workspace/...`) are covered in
`frontend-architecture-routes-stores-and-i18n.md` (planned; not yet written).

### 2.1 URL Families

| Address family | What answers it | Defined at |
|---|---|---|
| `/api/v1/<router>/...` | One of the routers in `backend/open_webui/routers/` (section 2.2) | `backend/open_webui/main.py:843-887` |
| `/ollama/...`, `/openai/...` | The model-connection routers, which are reverse proxies to the configured providers | `backend/open_webui/main.py:843-844` |
| `/api/...` (no `v1`), `/api/v1/models`, `/api/v1/chat/completions`, `/api/v1/embeddings`, `/api/v1/messages...`, `/api/v1/chats/{id}/messages/{message_id}/resolve` | Endpoints written directly in `main.py` (section 2.3) | `backend/open_webui/main.py:897-2643` |
| `/oauth/...` | Single sign-on and tool-server OAuth endpoints in `main.py` | `backend/open_webui/main.py:2772-2865` |
| `/ws/socket.io` | The real-time websocket (socket.io), mounted as a sub-application at `/ws` | `backend/open_webui/main.py:840`; see `websockets-realtime-and-redis.md` (planned) |
| `/health`, `/ready`, `/health/db` | Liveness, readiness and database probes (section 5.5) | `backend/open_webui/main.py:2963-3013` |
| `/manifest.json`, `/opensearch.xml` | Installable-app manifest and browser search descriptor, generated from the product name | `backend/open_webui/main.py:2868-2936` |
| `/static/...` | Pictures, icons, `loader.js`, `custom.css` and the API-docs assets from `STATIC_DIR` (section 5.7) | `backend/open_webui/main.py:3023` |
| `/cache/{path}` | Files in `DATA_DIR/cache`, for signed-in users | `backend/open_webui/main.py:3026-3051` |
| `/pyodide/...` | The in-browser Python runtime files, only when the build contains them | `backend/open_webui/main.py:3066-3069` |
| `/` and every other address | The built single-page front end, with the fallback in section 5.8 | `backend/open_webui/main.py:3071-3075` |
| `/docs`, `/openapi.json` | Interactive API documentation, only when `ENV` is `dev` (code default; the Docker image sets `prod`) | `backend/open_webui/main.py:506-512`; `backend/open_webui/env.py:139`; `Dockerfile:74` |

Order matters. Starlette tries routes in the order they were registered: the websocket mount,
the routers, the `main.py` endpoints, then `/static`, `/cache`, `/pyodide` and finally the
catch-all `/` mount. So an address that matches no API route (for example a router that is
switched off) reaches the front-end mount: a `GET` receives the application page with HTTP 200 and
any other method receives HTTP 405 (`backend/open_webui/main.py:298-310`;
`.venv/lib/python3.12/site-packages/starlette/staticfiles.py:113-114`).

### 2.2 The 31 Routers

Every router file creates a plain `APIRouter()` with no prefix or dependencies of its own; the
prefix comes only from `main.py` (for example `backend/open_webui/routers/utils.py:18`,
`backend/open_webui/routers/ollama.py:212`, `backend/open_webui/routers/openai.py:242`). Access is
decided per endpoint (section 3).

| # | File (`backend/open_webui/routers/`) | Mount prefix | What it serves | Mounted at | Reference document |
|---|---|---|---|---|---|
| 1 | `analytics.py` | `/api/v1/analytics` | Admin usage analytics: models, users, messages, summary, daily counts, tokens, per-model chats and overview | `backend/open_webui/main.py:878-879`, **only when `ENABLE_ADMIN_ANALYTICS` is on** (code default on, `backend/open_webui/config.py:2094`) | [`evaluations-feedback-and-analytics.md`](evaluations-feedback-and-analytics.md) |
| 2 | `audio.py` | `/api/v1/audio` | Speech settings, text to speech, transcription, model and voice lists | `backend/open_webui/main.py:851` | [`audio-speech-to-text-and-text-to-speech.md`](audio-speech-to-text-and-text-to-speech.md) |
| 3 | `auths.py` | `/api/v1/auths` | The session user, password and LDAP sign-in, sign-up, sign-out, profile, password and time-zone updates, admin-added accounts, authentication settings, API keys, OAuth token exchange | `backend/open_webui/main.py:856` | [`authentication-and-sign-in.md`](authentication-and-sign-in.md); single sign-on parts in [`sso-oauth-oidc-and-scim.md`](sso-oauth-oidc-and-scim.md) |
| 4 | `automations.py` | `/api/v1/automations` | Scheduled automations: list, create, update, toggle, run now, delete, run history | `backend/open_webui/main.py:882` | [`automations-calendar-and-timers.md`](automations-calendar-and-timers.md) |
| 5 | `calendar.py` | `/api/v1/calendars` (plural; the file name is singular) | Calendars and events, search, replies to invitations, default calendar | `backend/open_webui/main.py:883` | [`automations-calendar-and-timers.md`](automations-calendar-and-timers.md) |
| 6 | `channels.py` | `/api/v1/channels` | Channels and direct messages: members, messages, threads, pins, reactions, channel webhooks (including the incoming-webhook address) | `backend/open_webui/main.py:860` | [`channels-and-direct-messages.md`](channels-and-direct-messages.md) |
| 7 | `chats.py` | `/api/v1/chats` | Chat list, search, import, archive, share, pin, fork and clone, tags, folder placement, usage statistics and export | `backend/open_webui/main.py:861` | [`chat-conversations-history-and-organisation.md`](chat-conversations-history-and-organisation.md) |
| 8 | `configs.py` | `/api/v1/configs` | Admin settings import and export, connections, tool and terminal servers, code execution, model defaults, sub-agents, prompt suggestions, banners | `backend/open_webui/main.py:854` | [`admin-settings-panels.md`](admin-settings-panels.md); keys in [`configuration-persistent-settings-a-to-o.md`](configuration-persistent-settings-a-to-o.md) and `configuration-persistent-settings-r-to-w.md` |
| 9 | `evaluations.py` | `/api/v1/evaluations` | Arena settings, leaderboard, message feedback and its export | `backend/open_webui/main.py:877` | [`evaluations-feedback-and-analytics.md`](evaluations-feedback-and-analytics.md) |
| 10 | `files.py` | `/api/v1/files` | Upload, list, search, count, content, processing status, rename, delete | `backend/open_webui/main.py:875` | [`files-uploads-and-storage.md`](files-uploads-and-storage.md) |
| 11 | `folders.py` | `/api/v1/folders` | Chat folders, nesting, sharing, the chats in a folder | `backend/open_webui/main.py:873` | [`chat-conversations-history-and-organisation.md`](chat-conversations-history-and-organisation.md) |
| 12 | `functions.py` | `/api/v1/functions` | Admin functions (pipes, filters, actions, events): load, sync, toggle, valves | `backend/open_webui/main.py:876` | [`functions-pipes-filters-actions-and-pipelines.md`](functions-pipes-filters-actions-and-pipelines.md) |
| 13 | `groups.py` | `/api/v1/groups` | User groups, membership, export | `backend/open_webui/main.py:874` | [`users-groups-roles-and-permissions.md`](users-groups-roles-and-permissions.md) |
| 14 | `images.py` | `/api/v1/images` | Image settings, connection check, models, generation, editing | `backend/open_webui/main.py:849` | [`image-generation-and-editing.md`](image-generation-and-editing.md) |
| 15 | `knowledge.py` | `/api/v1/knowledge` | Knowledge bases, their files and folders, re-indexing, external connections and sources, export | `backend/open_webui/main.py:867` | [`knowledge-bases.md`](knowledge-bases.md) |
| 16 | `memories.py` | `/api/v1/memories` | Personal memories: add, update, query, search, re-index, reset | `backend/open_webui/main.py:872` | [`memories.md`](memories.md) |
| 17 | `models.py` | `/api/v1/models` | Workspace (custom) models: create, import, export, sync, toggle, access, delete | `backend/open_webui/main.py:865` | [`workspace-models-and-model-access.md`](workspace-models-and-model-access.md) |
| 18 | `notes.py` | `/api/v1/notes` | Notes, pinning, chats about a note, access | `backend/open_webui/main.py:862` | [`notes.md`](notes.md) |
| 19 | `notifications.py` | `/api/v1/notifications` | A person's own notification targets (personal webhooks) and the list of events they can choose | `backend/open_webui/main.py:866` | [`notifications-webhooks-events-and-banners.md`](notifications-webhooks-events-and-banners.md) |
| 20 | `ollama.py` | `/ollama` | Ollama connection settings and a proxy to the Ollama API (model list, pull, create, chat, generate, embeddings, OpenAI-style `/v1/...` paths) | `backend/open_webui/main.py:843` | [`model-connections-openai-ollama-and-direct.md`](model-connections-openai-ollama-and-direct.md) |
| 21 | `openai.py` | `/openai` | OpenAI-compatible connection settings, model lists, chat completions, responses, speech, model management for compatible servers, and a catch-all proxy (`backend/open_webui/routers/openai.py:1994`) | `backend/open_webui/main.py:844` | [`model-connections-openai-ollama-and-direct.md`](model-connections-openai-ollama-and-direct.md) |
| 22 | `pipelines.py` | `/api/v1/pipelines` | The external Pipelines server: list, upload, add, delete, valves | `backend/open_webui/main.py:847` | [`functions-pipes-filters-actions-and-pipelines.md`](functions-pipes-filters-actions-and-pipelines.md) |
| 23 | `prompts.py` | `/api/v1/prompts` | Prompts, tags, versions and history, access | `backend/open_webui/main.py:868` | [`prompts-and-skills.md`](prompts-and-skills.md) |
| 24 | `retrieval.py` | `/api/v1/retrieval` | Embedding and retrieval settings, processing of files, text, web pages and videos, web search, queries, resets | `backend/open_webui/main.py:852` | [`rag-retrieval-embeddings-and-vector-stores.md`](rag-retrieval-embeddings-and-vector-stores.md); web endpoints in [`web-search-and-web-loading.md`](web-search-and-web-loading.md) |
| 25 | `scim.py` | `/api/v1/scim/v2` | SCIM 2.0 users and groups for an identity provider's provisioning client | `backend/open_webui/main.py:886-887`, **only when `ENABLE_SCIM` is on** (code default off, `backend/open_webui/env.py:907`) | [`sso-oauth-oidc-and-scim.md`](sso-oauth-oidc-and-scim.md) |
| 26 | `skills.py` | `/api/v1/skills` | Skills: create, update, access, toggle, export | `backend/open_webui/main.py:870` | [`prompts-and-skills.md`](prompts-and-skills.md) |
| 27 | `tasks.py` | `/api/v1/tasks` | Generation-task settings and the task endpoints (title, follow-ups, tags, image prompt, search queries, autocomplete, emoji, mixture of agents) | `backend/open_webui/main.py:848` | [`chat-completion-pipeline-and-generation-tasks.md`](chat-completion-pipeline-and-generation-tasks.md) |
| 28 | `terminals.py` | `/api/v1/terminals` | Terminal servers: list, a proxy to a server, the terminal websocket | `backend/open_webui/main.py:881` | [`workspace-tools-tool-servers-mcp-and-terminals.md`](workspace-tools-tool-servers-mcp-and-terminals.md) |
| 29 | `tools.py` | `/api/v1/tools` | Workspace tools: load from a URL, create, update, access, valves, export | `backend/open_webui/main.py:869` | [`workspace-tools-tool-servers-mcp-and-terminals.md`](workspace-tools-tool-servers-mcp-and-terminals.md) |
| 30 | `users.py` | `/api/v1/users` | User administration, search, groups, permissions and default permissions, a person's own settings, status, details and variables, usage, profile pictures, update, delete | `backend/open_webui/main.py:857` | [`users-groups-roles-and-permissions.md`](users-groups-roles-and-permissions.md); own settings in [`user-settings-and-personalisation.md`](user-settings-and-personalisation.md) |
| 31 | `utils.py` | `/api/v1/utils` | Gravatar address, server-side Python formatting, Jupyter code execution, raw database download | `backend/open_webui/main.py:880` | This document (section 2.4); `/code/execute` also in [`code-execution-and-interpreter.md`](code-execution-and-interpreter.md) |

The mount comment in `CLAUDE.md` describes these prefixes the same way; verified against
`backend/open_webui/main.py:843-887` on 2026-10-11.

### 2.3 The 39 Top-Level Endpoints in `main.py`

"Signed in" means `get_verified_user` (role `user` or `admin`); "Admin" means `get_admin_user`
(section 3). Paths that share a handler are listed separately because callers use both.

| Method | Path | Who may call | Purpose | Source | More in |
|---|---|---|---|---|---|
| GET | `/api/models` | Signed in | The models this person may use, after access filtering, with duplicates collapsed and the admin's order applied | `backend/open_webui/main.py:897-943` | `model-connections-openai-ollama-and-direct.md` |
| GET | `/api/v1/models` | Signed in | Same handler, OpenAI-compatible address | `backend/open_webui/main.py:898` | `public-api-and-integrations.md` (planned) |
| GET | `/api/models/base` | Admin | Every base model from every connection, unfiltered | `backend/open_webui/main.py:946-949` | `model-connections-openai-ollama-and-direct.md` |
| POST | `/api/models/unload` | Admin | Unload a model from memory on Ollama or llama.cpp | `backend/open_webui/main.py:956-1064` | `model-connections-openai-ollama-and-direct.md` |
| POST | `/api/embeddings` | Signed in | OpenAI-compatible embeddings through the configured models | `backend/open_webui/main.py:1072-1094` | `rag-retrieval-embeddings-and-vector-stores.md` |
| POST | `/api/v1/embeddings` | Signed in | Same handler, OpenAI-compatible address | `backend/open_webui/main.py:1073` | `public-api-and-integrations.md` (planned) |
| POST | `/api/chat/completions` | Signed in | The chat endpoint the front end uses for every reply | `backend/open_webui/main.py:1108-1885` | `chat-completion-pipeline-and-generation-tasks.md` |
| POST | `/api/v1/chat/completions` | Signed in | Same handler, OpenAI-compatible address | `backend/open_webui/main.py:1109` | `public-api-and-integrations.md` (planned) |
| POST | `/api/v1/chats/{id}/messages/{message_id}/resolve` | Signed in | Record an approval or answer for a paused tool call and resume the reply | `backend/open_webui/main.py:1893-1910` | `builtin-native-tools.md` |
| POST | `/api/message/count_tokens` | Signed in | Count input tokens for an Anthropic-style request | `backend/open_webui/main.py:1933-1940` | `public-api-and-integrations.md` (planned) |
| POST | `/api/v1/messages/count_tokens` | Signed in | Same handler, Anthropic-compatible address | `backend/open_webui/main.py:1934` | As above |
| POST | `/api/message` | Signed in | Anthropic Messages-compatible chat, converted to the internal format | `backend/open_webui/main.py:2002-2068` | As above |
| POST | `/api/v1/messages` | Signed in | Same handler, Anthropic-compatible address | `backend/open_webui/main.py:2003` | As above |
| POST | `/api/chat/completed` | Signed in | Deprecated hook that runs outlet filters after a reply | `backend/open_webui/main.py:2090-2107` | `chat-completion-pipeline-and-generation-tasks.md` |
| POST | `/api/chat/actions/{action_id}` | Signed in | Run an Action function (a message button) | `backend/open_webui/main.py:2110-2125` | `functions-pipes-filters-actions-and-pipelines.md` |
| POST | `/api/tasks/stop/{task_id}` | Admin | Stop one background task by id | `backend/open_webui/main.py:2128-2134` | `chat-completion-pipeline-and-generation-tasks.md` |
| GET | `/api/tasks` | Admin | List running background tasks | `backend/open_webui/main.py:2137-2139` | As above |
| GET | `/api/tasks/chat/{chat_id:path}` | Signed in; someone else's chat returns an empty list unless the caller is an admin | List the tasks running for a chat | `backend/open_webui/main.py:2142-2157` | As above |
| POST | `/api/tasks/chat/{chat_id:path}/stop` | Signed in; someone else's chat answers HTTP 404 unless the caller is an admin | Stop a chat's tasks (the **Stop** button) | `backend/open_webui/main.py:2160-2215` | As above |
| GET | `/api/config` | Anyone; the answer grows with the caller's role | Name, version, sign-in options and, for signed-in people, feature switches and defaults (section 5.3) | `backend/open_webui/main.py:2224-2472` | This document |
| GET | `/api/events` | Admin | The catalogue of system events that event webhooks can subscribe to | `backend/open_webui/main.py:2491-2496` | `notifications-webhooks-events-and-banners.md` |
| GET, POST | `/api/events/webhooks` | Admin | List or create event webhooks | `backend/open_webui/main.py:2499-2532` | As above |
| PUT, DELETE | `/api/events/webhooks/{webhook_id}` | Admin | Edit or delete an event webhook | `backend/open_webui/main.py:2535-2583` | As above |
| GET | `/api/version` | Anyone | The running version and the optional `DEPLOYMENT_ID` | `backend/open_webui/main.py:2586-2591` | Section 5.9 |
| GET | `/api/version/updates` | Signed in | Compare the running version with the latest **upstream** release | `backend/open_webui/main.py:2594-2613` | Section 5.9 |
| GET | `/api/changelog` | Anyone | The five newest entries of `CHANGELOG.md` | `backend/open_webui/main.py:2616-2618` | Section 5.9 |
| GET | `/api/usage` | Signed in; admins only when `ENABLE_PUBLIC_ACTIVE_USERS_COUNT` is off | Models in use now and the active-user count | `backend/open_webui/main.py:2621-2643` | `evaluations-feedback-and-analytics.md` |
| GET | `/oauth/clients/{client_id}/authorize` | Signed in | Start the OAuth sign-in for a tool-server (MCP) connection | `backend/open_webui/main.py:2772-2812` | `sso-oauth-oidc-and-scim.md` |
| GET | `/oauth/clients/{client_id}/callback` | Checked inside the OAuth client manager | Where the tool server's identity provider returns | `backend/open_webui/main.py:2815-2825` | As above |
| GET | `/oauth/{provider}/login` | Anyone (start of single sign-on) | Redirect to the identity provider | `backend/open_webui/main.py:2828-2830` | As above |
| GET | `/oauth/{provider}/login/callback` | Anyone (the provider's redirect) | Finish single sign-on and create the session | `backend/open_webui/main.py:2833-2851` | As above |
| GET | `/oauth/{provider}/callback` | As above | Legacy address for the same handler | `backend/open_webui/main.py:2834` | As above |
| POST | `/oauth/backchannel-logout` | The identity provider | OIDC back-channel sign-out; answers HTTP 404 unless `ENABLE_OAUTH_BACKCHANNEL_LOGOUT` is on | `backend/open_webui/main.py:2858-2865` | As above |
| GET | `/manifest.json` | Anyone | Web-app manifest for installing the site as an app (section 5.7) | `backend/open_webui/main.py:2868-2917` | `frontend-architecture-routes-stores-and-i18n.md` (planned) |
| GET | `/opensearch.xml` | Anyone | Browser search-engine descriptor built from `webui.url` | `backend/open_webui/main.py:2920-2936` | Section 5.7 |
| GET | `/health` | Anyone | Liveness: the process is serving | `backend/open_webui/main.py:2963-2965` | Section 5.5 |
| GET | `/ready` | Anyone | Readiness: start-up finished, database and Redis answer | `backend/open_webui/main.py:2968-3006` | Section 5.5 |
| GET | `/health/db` | Anyone | Database ping only | `backend/open_webui/main.py:3009-3013` | Section 5.5 |
| GET | `/cache/{path:path}` | Signed in | A file from the cache folder; pictures, audio and video open in the browser, anything else downloads | `backend/open_webui/main.py:3026-3051` | Section 5.7 |

### 2.4 The Utilities Router (`/api/v1/utils`)

`backend/open_webui/routers/utils.py` is small and has no other home, so it is described in full
here.

| Method and path | Who may call | What it does | Source |
|---|---|---|---|
| GET `/api/v1/utils/gravatar?email=...` | Signed in | Returns a Gravatar picture address built from a hash of the email; the browser then loads the picture from `gravatar.com`. Used by the **Gravatar** button beside the profile picture | `backend/open_webui/routers/utils.py:21-23`; `backend/open_webui/utils/misc.py:832-843`; `src/lib/components/chat/Settings/Account/UserProfileImage.svelte:162-168` |
| POST `/api/v1/utils/code/format` | Admin | Formats Python with the `black` formatter. The code editors (tools, functions) call it for admins; other people's editors format in the browser with Pyodide instead | `backend/open_webui/routers/utils.py:30-38`; `src/lib/components/common/CodeEditor.svelte:181-201` |
| POST `/api/v1/utils/code/execute` | Signed in | Runs code on the configured Jupyter server when code execution is on and its engine is `jupyter` | `backend/open_webui/routers/utils.py:41-71`; caller `src/lib/components/chat/Messages/CodeBlock.svelte:149` |
| GET `/api/v1/utils/db/download` | Admin, and only when `ENABLE_ADMIN_EXPORT` is on (code default on, `backend/open_webui/config.py:2082`) | Downloads the whole SQLite database file as `webui.db`; refused on PostgreSQL. The file holds every account, chat and setting, so it contains personal and possibly health information | `backend/open_webui/routers/utils.py:74-90`; button in `src/lib/components/admin/Settings/Database.svelte:123-138` |

### 2.5 Addresses Rewritten Before Routing

The application's HTTP middleware answers two legacy address shapes itself, for `GET` requests
only (`backend/open_webui/utils/asgi_middleware.py:164-206`):

| Incoming address | Redirects to | Why it exists |
|---|---|---|
| `.../watch?v={id}` (any path ending in `/watch`) | `/?youtube={id}` | Lets a YouTube-style link open a chat about that video |
| `/?shared={text}` | `/?youtube={id}` when the shared text starts with a YouTube link, `/?load-url={url}` for any other `https://` link, otherwise `/?q={text}` | The installed app's share target sends shared text here (`backend/open_webui/main.py:2912-2916`) |

A websocket handshake to `/ws/socket.io` with `transport=websocket` but without proper upgrade
headers is refused with HTTP 400 `Invalid WebSocket upgrade request` before it reaches socket.io
(`backend/open_webui/utils/asgi_middleware.py:145-162`); this usually means a proxy in front of the
service does not pass websocket upgrades (section 11.6).

## 3. Roles and Permissions

The backend knows three roles, `admin`, `user` and `pending` (ground truth). This layer does not
decide what a role may do inside a feature; it decides **who the caller is** and whether the
route lets that kind of caller in at all. Feature permissions (group grants, sharing, the
default permissions) are applied later by each endpoint and are described in
[`users-groups-roles-and-permissions.md`](users-groups-roles-and-permissions.md).

### 3.1 The Three Gatekeepers

Endpoints that need a signed-in caller declare one of three dependencies from
`backend/open_webui/utils/auth.py` (counts across `backend/open_webui/routers/` and `main.py`, from a search for each `Depends(...)`
on 2026-10-11):

| Dependency | Lets in | Refuses with | Used by | Source |
|---|---|---|---|---|
| `get_current_user` | Any account with a valid session token or API key, **including `pending`** | HTTP 401 (texts in section 3.3) | 7 endpoints, all in `auths.py` (session user, password and time-zone updates, admin contact details, the three API-key endpoints) | `backend/open_webui/utils/auth.py:393-506`; `backend/open_webui/routers/auths.py:253`, `:360`, `:390`, `:1173`, `:1531`, `:1556`, `:1573` |
| `get_verified_user` | Roles `user` and `admin` | HTTP 401 `You do not have permission to access this resource. Please contact your administrator for assistance.` for `pending` | About 310 endpoints: almost everything a person does | `backend/open_webui/utils/auth.py:567-576` |
| `get_admin_user` | Role `admin` | HTTP 401 with the same text for everyone else | About 160 endpoints: settings, user administration, connections, functions | `backend/open_webui/utils/auth.py:625-631` |

Endpoints with no gatekeeper are the public ones listed with "Anyone" in section 2.3, the sign-in
endpoints themselves, and the static and front-end mounts.

**The 401 rule.** A role refusal answers **401, not 403** (ground truth), so a browser tool or an
API client cannot tell "you are not signed in" from "your role is too low" by status alone; the
`detail` text tells them apart (section 3.3). Endpoint-level permission checks inside features
commonly answer 403 instead (for example `backend/open_webui/routers/notifications.py:34-41`).

### 3.2 How the Caller Is Identified

`get_current_user` looks for a credential in this order and uses the first one it finds
(`backend/open_webui/utils/auth.py:403-415`):

1. An `Authorization: Bearer ...` header (the front end sends the session token this way on most
   calls, for example `src/lib/apis/auths/index.ts:88-95`).
2. The `token` cookie, which sign-in sets alongside the token the page keeps
   (`backend/open_webui/routers/auths.py:196-207`).
3. A credential the HTTP middleware picked up for every request, which adds one more source: the
   header named by `CUSTOM_API_KEY_HEADER` (code default `x-api-key`) for API keys
   (`backend/open_webui/utils/asgi_middleware.py:126-132`; `backend/open_webui/env.py:812`).

No credential at all gives HTTP 401 `Not authenticated` (`backend/open_webui/utils/auth.py:415-416`).
Then:

- **API keys** are recognised by their `sk-` prefix (`backend/open_webui/utils/auth.py:419-436`).
  A key is accepted only when API keys are switched on (`auth.enable_api_keys`), the owner is an
  admin or holds the `features.api_keys` permission, and, when endpoint restrictions are on, the
  address is in the allowed list (`backend/open_webui/utils/auth.py:509-564`). The details belong
  to [`authentication-and-sign-in.md`](authentication-and-sign-in.md) and the planned
  `public-api-and-integrations.md`.
- **Session tokens** are decoded, checked against the revocation list when Redis is configured
  (ground truth), and the account is loaded; with trusted-header sign-in the header's email must
  still match the account (`backend/open_webui/utils/auth.py:438-493`). Each successful check
  records the person's last-active time in the background (`backend/open_webui/utils/auth.py:483`).
- The resolved person and the kind of credential (`jwt` or `api_key`) are kept on the request so
  that the audit log and outgoing user-information headers can use them
  (`backend/open_webui/utils/auth.py:433-435`, `:485-487`; `backend/open_webui/utils/headers.py:62-64`).

Websocket connections do not use these dependencies: the socket server checks the token sent in
the handshake with `get_verified_user_by_token`, which accepts only `user` and `admin`
(`backend/open_webui/utils/auth.py:579-589`; `backend/open_webui/socket/main.py:428`).

### 3.3 What Each Refusal Means

| Text (`detail`) | Status | Meaning | Source |
|---|---|---|---|
| `Not authenticated` | 401 | No credential was sent at all | `backend/open_webui/utils/auth.py:415-416` |
| `401 Unauthorized` | 401 | The token could not be read: expired, or signed with a different secret key | `backend/open_webui/utils/auth.py:246-251`, `:489-493`; `backend/open_webui/constants.py:69` |
| `Invalid token` | 401 | The token was revoked (only possible with Redis) | `backend/open_webui/utils/auth.py:448-453` |
| `Your session has expired or the token is invalid. Please sign in again.` | 401 | The token is readable but its account no longer exists; also an API key that matches no account | `backend/open_webui/utils/auth.py:455-460`, `:511-516`; `backend/open_webui/constants.py:59` |
| `User mismatch. Please sign in again.` | 401 | Trusted-header sign-in only: the proxy now names a different person | `backend/open_webui/utils/auth.py:462-468` |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | 401 from the role gatekeepers; 403 when an API key is used on an address outside the allowed list | Role too low (`pending` on a verified route, non-admin on an admin route) | `backend/open_webui/utils/auth.py:540-550`, `:570-575`, `:626-630`; `backend/open_webui/constants.py:70-72` |
| `Use of API key is not enabled in the environment.` | 403 | An API key was used while API keys are off, or by a non-admin without the API-key permission | `backend/open_webui/utils/auth.py:526-536`; `backend/open_webui/constants.py:81` |

The front end shows most of these as a toast with the text, or returns the person to the sign-in
page; see [`error-messages-frontend-chat-and-navigation.md`](error-messages-frontend-chat-and-navigation.md).

### 3.4 What Tier 1 Can Do Here

Nothing in this layer is adjustable by tier 1. Roles are changed by admins under
`/admin/users`; API-key settings and the environment switches named above belong to admins and
the platform maintainer. Tier 1 can observe: the role shown in the user menu, the exact refusal
text, and (with access to monitoring, **TO BE CONFIRMED**) the health and readiness probes.

## 4. Key Concepts and Terminology

### 4.1 Terms

| Term | Meaning here | Source |
|---|---|---|
| **App** | The single FastAPI application object created in `main.py`; its API title stays `Open WebUI` under the licence comment | `backend/open_webui/main.py:503-512` |
| **Router** | A file in `backend/open_webui/routers/` that groups the endpoints of one feature; mounted under a prefix (section 2.2) | `backend/open_webui/main.py:843-887` |
| **Top-level endpoint** | An endpoint written directly in `main.py` rather than in a router (section 2.3) | `backend/open_webui/main.py:897-3051` |
| **Mount** | A sub-application that owns every address under a prefix: `/ws`, `/static`, `/pyodide`, `/` | `backend/open_webui/main.py:840`, `:3023`, `:3069`, `:3071-3075` |
| **Middleware** | Code that wraps every request and response (section 4.2) | `backend/open_webui/main.py:796-837`, `:2649-2674` |
| **Dependency** | A function FastAPI runs before an endpoint, such as the gatekeepers `get_verified_user` and `get_admin_user` (section 3) | `backend/open_webui/utils/auth.py:393-631` |
| **Lifespan** | The start-up and shut-down routine that wraps the running server (sections 5.4 and 5.10) | `backend/open_webui/main.py:344-497` |
| **`app.state`** | Per-process memory shared by all requests: model lists, tool servers, the Redis client, the start-up flag, the product name and more (section 6.1) | `backend/open_webui/main.py:521-612`, `:776-794` |
| **Worker** | One server process. Each worker runs its own lifespan, background loops and `app.state`; workers share no memory, only the database, the data folder and, when configured, Redis | `backend/start.sh` (`--workers`); `CLAUDE.md` "Deployment" |
| **Liveness and readiness** | `/health` says "the process answers"; `/ready` says "start-up finished and the database (and Redis) answer" | `backend/open_webui/main.py:2963-3006` |
| **Single-page front end (SPA)** | The built Svelte application in `FRONTEND_BUILD_DIR`; every unknown address returns its `index.html` so the browser can route | `backend/open_webui/main.py:298-310`; `svelte.config.js:15-19` |
| **`STATIC_DIR`** | The folder served at `/static`; refreshed from the build at every start-up (section 5.7) | `backend/open_webui/config.py:98-145` |
| **Session token** | The signed sign-in token (a JWT) sent as a bearer header or the `token` cookie | `backend/open_webui/utils/auth.py:232-251` |
| **API key** | A personal key starting `sk-` that stands in for a session token | `backend/open_webui/utils/auth.py:378-380`, `:419-436` |
| **`owui-session` cookie** | A separate cookie that carries single sign-on state between the redirect to the identity provider and the return | `backend/open_webui/main.py:2660`, `:2671`; `backend/open_webui/utils/oauth.py:1244` |
| **Shared HTTP session pool** | One reusable outbound HTTP client per process for calls to model providers and other services (section 5.11) | `backend/open_webui/utils/session_pool.py:1-92` |
| **JSON codec** | The library used to read and write JSON everywhere: Python's standard one by default, `orjson` when `ENABLE_ORJSON` is on (section 7.4) | `backend/open_webui/utils/json_codec.py:1-84` |
| **Instance id** | A random identifier per process unless `INSTANCE_ID` is set; used in events and Redis coordination | `backend/open_webui/env.py:155`; `backend/open_webui/main.py:360` |
| **Deployment id** | An optional label from `DEPLOYMENT_ID`, returned by `/api/version` | `backend/open_webui/env.py:154`; `backend/open_webui/main.py:2586-2591` |
| **Safe mode** | `SAFE_MODE` deactivates every function at start-up, for recovering from a broken plugin | `backend/open_webui/main.py:280-281`, `:382-383` |

### 4.2 The Middleware Stack

Starlette runs the middleware added **last** as the **outermost** layer
(`.venv/lib/python3.12/site-packages/starlette/applications.py:98-101`; FastAPI's stack builder,
`.venv/lib/python3.12/site-packages/fastapi/applications.py:1018-1061`). Reading `main.py` in that
light gives this order for an incoming request, from the outside in:

| Order | Layer | What it does | When it is present | Source |
|---|---|---|---|---|
| 1 | Server error handler (Starlette) | Turns any unhandled exception into a plain-text HTTP 500 `Internal Server Error` | Always | `.venv/lib/python3.12/site-packages/fastapi/applications.py:1031-1033` |
| 2 | Session cookie layer | Reads and writes the `owui-session` cookie used during single sign-on. With `ENABLE_STAR_SESSIONS_MIDDLEWARE` on, the session lives in Redis (two layers are added); otherwise the cookie itself holds it | Always (one variant or the other) | `backend/open_webui/main.py:2649-2674`; `backend/open_webui/env.py:967` |
| 3 | CORS | Answers cross-origin checks for the origins in `CORS_ALLOW_ORIGIN` (code default `*`), with credentials, any method and any header | Always | `backend/open_webui/main.py:831-837`; `backend/open_webui/config.py:2134` |
| 4 | `AppHTTPMiddleware` | Refuses malformed websocket upgrades; picks up the credential for later use (section 3.2); answers the legacy redirects (section 2.5); adds `X-Process-Time` and the configured security headers to the responses that pass through it (section 5.6); commits or rolls back the per-request synchronous database session, skipping that step for the three health probes | Always | `backend/open_webui/main.py:828`; `backend/open_webui/utils/asgi_middleware.py:51-238` |
| 5 | Compression | Compresses responses for browsers that accept it | When `ENABLE_COMPRESSION_MIDDLEWARE` is on (code default on) | `backend/open_webui/main.py:816-817`; `backend/open_webui/env.py:790` |
| 6 | Audit logging | Writes request (and optionally response) details to the audit log; placed inside compression on purpose so it sees uncompressed bodies | When `AUDIT_LOG_LEVEL` is not `NONE` (code default `NONE`) | `backend/open_webui/main.py:796-813`; `backend/open_webui/env.py:1234`; see `deployment-operations-and-logging.md` (planned) |
| 7 | OpenTelemetry | Traces and request metrics | When `ENABLE_OTEL` (and its trace or metric switches) are on | `backend/open_webui/main.py:550-553`; `backend/open_webui/utils/telemetry/setup.py:27-57`; `backend/open_webui/utils/telemetry/metrics.py:225-227` |
| 8 | Exception handler (Starlette and FastAPI) | Turns `HTTPException` into JSON `{"detail": ...}`; a custom handler turns a recurrence-rule time-out into HTTP 400 | Always | `.venv/lib/python3.12/site-packages/fastapi/exception_handlers.py:11-17`; `backend/open_webui/main.py:515-517` |
| 9 | Route, dependencies, handler | The endpoint itself, after its gatekeeper (section 3) | Always | Sections 2 and 3 |

The comment above `AppHTTPMiddleware` explains why these layers are written as plain ASGI
middleware: the older style cancelled in-flight database calls when a browser disconnected and
filled the logs with tracebacks (`backend/open_webui/main.py:820-827`;
`backend/open_webui/utils/asgi_middleware.py:1-29`). The exact position of the OpenTelemetry
trace instrumentation inside this stack depends on the instrumentation library and was not
traced (section 14).

### 4.3 Asynchronous and Synchronous Database Sessions

Most endpoints use the asynchronous database session (`Depends(get_async_session)`); according to
the middleware's own description, the older synchronous session is used only by start-up and a
few helpers such as the pgvector and openGauss vector stores (the health probes use a raw
connection of their own, section 5.5). `AppHTTPMiddleware` commits that synchronous work after a
successful response and rolls it back after an error, so PostgreSQL connections are not left
"idle in transaction". Because the response has already been sent by then, a failed commit
cannot change what the browser saw; it is logged instead (section 10)
(`backend/open_webui/utils/asgi_middleware.py:63-89`, `:208-238`).

## 5. Workflows (Step by Step)

### 5.1 A Request from the Browser to a Router and Back

Example: a signed-in person opens their chat list, which calls `GET /api/v1/chats/list`.

1. **The browser sends the request to the same origin** that served the page, with the session
   token in an `Authorization: Bearer` header and the `token` cookie (`src/lib/constants.ts:10-11`;
   section 3.2). In local development Vite on port 5173 forwards `/api`, `/ollama`, `/openai`,
   `/oauth` and `/ws` to the backend (`vite.config.ts:6`, `:31-55`).
2. **The server process** (uvicorn, started by `backend/start.sh:107-112`) hands it to the
   application, and the layers in section 4.2 run from the outside in: error handler, session
   cookie, CORS, `AppHTTPMiddleware` (credential pick-up, timing and security headers),
   compression, audit log if switched on.
3. **Routing.** Starlette matches the path against the registered routes in order (section 2.1)
   and finds the `chats` router mounted at `/api/v1/chats`
   (`backend/open_webui/main.py:861`).
4. **Gatekeeper.** The endpoint's dependency (here `get_verified_user`) identifies the caller from
   the credential and checks the role; a refusal returns HTTP 401 with one of the texts in
   section 3.3 and the handler never runs.
5. **Handler.** The endpoint does its work, usually with an asynchronous database session, and
   applies feature permissions.
6. **The response travels back out** through the same layers: the audit layer records it (when
   on), compression shrinks it, `AppHTTPMiddleware` stamps `X-Process-Time` and the security
   headers and then commits any synchronous database work, CORS adds its headers, and the
   session layer updates the `owui-session` cookie if the session changed
   (`backend/open_webui/utils/asgi_middleware.py:105-124`, `:134-143`).
7. **Errors.** An `HTTPException` becomes JSON `{"detail": "<text>"}` with its status; any other
   unhandled error becomes a plain-text HTTP 500 `Internal Server Error` (section 4.2). The front
   end usually shows the `detail` text in a toast.

Streaming replies (chat completions) follow the same path; the middleware deliberately does not
buffer responses so that streaming keeps working (`backend/open_webui/utils/asgi_middleware.py:76-85`).

### 5.2 The First Page Load

What happens between typing the address and seeing the chat screen
(`src/routes/+layout.svelte:1078-1349`):

1. **The page shell.** Any front-end address returns the built `index.html`
   (section 5.8). It shows a splash screen at once and loads `/static/loader.js`,
   `/static/custom.css`, the icons and `/manifest.json` (`src/app.html:9-39`).
2. **Configuration.** The root layout installs a watcher that signs the person out when an
   authenticated call starts answering 401 (`src/routes/+layout.svelte:1079-1093`), then asks
   for `GET /api/config` with cookies but without a bearer header
   (`src/lib/apis/index.ts:1469-1518`).
   - If a sign-in proxy in front of the service intercepts that call with a redirect, the page
     reloads `/` so the browser can follow it (`src/lib/apis/index.ts:1490-1514`;
     `src/routes/+layout.svelte:1242-1248`).
   - Any other failure (no answer, an error status, an answer that is not JSON) leaves the
     configuration empty.
3. **Language.** The translations start, using the server's `default_locale` and any custom
   translations in `i18n` when the browser has no saved language
   (`src/routes/+layout.svelte:1254-1266`).
4. **No configuration means the error page.** The layout opens `/error`, which shows
   `{{webUIName}} Backend Required` (normally `MedIT GPT Backend Required`) and a **Check Again**
   button that reloads `/` (`src/routes/+layout.svelte:1315-1318`;
   `src/routes/error/+page.svelte:19-59`).
5. **With a configuration**, the product name is taken from it, the real-time connection opens
   (websocket only, or polling first when the server reports websockets off,
   `src/routes/+layout.svelte:166-175`), and if the browser holds a token the session user is
   fetched from `GET /api/v1/auths/`. That call also refreshes the `token` cookie, and the layout
   then asks for `/api/config` a second time so that it receives the signed-in variant
   (`src/routes/+layout.svelte:1268-1313`; `backend/open_webui/routers/auths.py:249-290`). A
   session that cannot be confirmed is forgotten and the person is sent to sign in.
6. **The splash is removed** only at the very end, after the steps above
   (`src/routes/+layout.svelte:1322-1349`). Anything that never finishes before that point leaves
   the splash on screen (section 11.2).

### 5.3 What `/api/config` Returns

`GET /api/config` needs no sign-in. It reads a token from the `Authorization` header or the
`token` cookie, and if the token decodes it looks up that account; a token that cannot be read
is treated as no token, because the decoder returns nothing instead of failing
(`backend/open_webui/main.py:2224-2248`; `backend/open_webui/utils/auth.py:246-251`). The answer
then depends on who the caller turned out to be (`backend/open_webui/main.py:2250-2472`):

| Part of the answer | Signed out | `pending` | `user` or `admin` |
|---|---|---|---|
| `status` (`true`), `name` (the product name), `version`, `default_locale`, `i18n` (custom translations) | Yes | Yes | Yes |
| `onboarding: true` | Only when **no accounts exist yet** (first visit to a fresh install) | No | No |
| `oauth.providers` (provider names for the sign-in buttons; empty when single sign-on is switched off) and `oauth.auto_redirect` | Yes | Yes | Yes |
| `features`, sign-in part: slim image, authentication on, trusted-header sign-in, password confirmation at sign-up, LDAP, sign-up, login form, websockets (and the heartbeat interval when set) | Yes | Yes | Yes |
| `features`, everything else: 34 entries, 36 when OneDrive is on (API keys, password change, version check, folders, channels, calendar, automations, notes, web search, code execution and interpreter, image generation, autocomplete, community sharing, message rating, personal webhooks, user status, admin export, admin chat access, analytics, Google Drive, OneDrive, memories and others) | No | **Yes** | Yes |
| Defaults and limits: default and pinned models, prompt suggestions, code engines, speech engines, file size, count and image compression, the default permissions, Google Drive and OneDrive picker identifiers, interface defaults, the pending-overlay texts, the response watermark, the iframe content policy, licence metadata | No | No | Yes |
| `ui.pending_user_overlay_title`, `ui.pending_user_overlay_content` | No | Yes (only these) | Yes (inside `ui`) |
| `user_count`, `active_entries` | No | No | Only with licence metadata; `active_entries` for admins only |
| `metadata.login_footer`, `metadata.auth_logo_position` | Only with licence metadata | Only with licence metadata | No |

Points to remember:

- **The values come from the database settings and the environment at the moment of the call**
  (`Config.get_many(...)`, `backend/open_webui/main.py:2256-2308`), so an admin's change shows up
  on the next page load or the next refresh of this answer, without a restart. Live values are
  **TO BE CONFIRMED** for production.
- **`pending` users already receive the full `features` list** because that block is gated on
  "a user was found", not on the role (`backend/open_webui/main.py:2342-2390`); only the
  defaults block requires `user` or `admin` (`:2392-2449`).
- **The product name comes from `WEBUI_NAME`** (fork default `MedIT GPT`,
  `backend/open_webui/env.py:951`), copied into `app.state.WEBUI_NAME` at import
  (`backend/open_webui/main.py:538`).
- The call also counts users when licence metadata is loaded
  (`backend/open_webui/main.py:2254-2255`); whether a licence key is used is **TO BE CONFIRMED**.

### 5.4 Start-Up Order and What Each Failure Looks Like

Start-up has three phases. **Nothing answers on the service port until all three finish**: the
installed uvicorn (0.51.0) runs the application's start-up routine before it opens its listening
socket (`.venv/lib/python3.12/site-packages/uvicorn/server.py:103-106`). With one worker (the
`start.sh` default, `backend/start.sh:99`, `:104`) a browser or probe gets "connection refused"
(or a proxy error page) during start-up; with several workers or the development reloader the
parent process holds the socket open, so requests wait instead
(`.venv/lib/python3.12/site-packages/uvicorn/main.py:603-621`).

**Phase A: the start script** (`backend/start.sh`) prepares the secret key, optional extras and
the uvicorn command line; see
[`configuration-environment-variables-bootstrap.md`](configuration-environment-variables-bootstrap.md)
section 7.13.

**Phase B: importing the application** (`open_webui.main` and everything it imports). A failure
here prints a Python traceback and the process exits; a container then restarts or stays down.

| Step | What happens | Source | If it fails |
|---|---|---|---|
| B1 | `env.py` loads the repository-root `.env`, reads the version from `package.json`, parses `CHANGELOG.md`, and checks that `WEBUI_SECRET_KEY` is set when sign-in is on | `backend/open_webui/env.py:37-41`, `:142-151`, `:184-222`, `:780-788` | Missing secret key: exit with `WEBUI_SECRET_KEY is not set. It is a hard requirement when authentication is enabled.` (section 10) |
| B2 | The database engines are created | `backend/open_webui/internal/db.py` (ground truth) | Bad `DATABASE_URL`, or any SQLCipher URL: exit (ground truth) |
| B3 | **Database migrations** run (`alembic upgrade head`) unless `ENABLE_DB_MIGRATIONS` is off | `backend/open_webui/config.py:64-82` | Log `Error running migrations: {e}` with the traceback, then exit |
| B4 | **The `/static` folder is refreshed from the front-end build** (section 5.7), then the legacy `CUSTOM_NAME` branding download runs if that variable is set | `backend/open_webui/config.py:98-145`, `:187-223` | Copy errors are logged as `An error occurred: {e}` and start-up continues |
| B5 | The rest of `config.py` reads settings; some values are validated here (for example `CORS_ALLOW_ORIGIN`) | `backend/open_webui/config.py` | See the configuration documents' section 10 |
| B6 | `main.py` itself: prints `SAFE MODE ENABLED` when safe mode is on, prints the banner, switches JSON to `orjson` if asked, creates the app, the single sign-on managers and OpenTelemetry, adds the middleware, mounts the routers and endpoints, mounts `/static`, and mounts the front-end build or logs that it is missing | `backend/open_webui/main.py:280-281`, `:320-341`, `:501-512`, `:521-553`, `:796-887`, `:3023`, `:3066-3077` | An unknown `AUDIT_LOG_LEVEL` value: see the note below. Missing build: warning `Frontend build directory not found at '{FRONTEND_BUILD_DIR}'. Serving API only.` and the site shows no pages |

*Note on `AUDIT_LOG_LEVEL` (read from code, not run).* When the value is not one of `NONE`,
`METADATA`, `REQUEST` or `REQUEST_RESPONSE` (any letter case), `main.py` tries to log
`Invalid audit level: {AUDIT_LOG_LEVEL}. Error: {e}` through `logger.error(...)`, but `logger`
there is the module `open_webui.utils.logger`, which defines no `error` function
(`backend/open_webui/main.py:211`, `:797-801`; `backend/open_webui/utils/logger.py:1-27`). The
call would then raise `AttributeError` and stop the import, so a mistyped value is expected to
prevent start-up rather than just leave auditing off. This differs from
`configuration-environment-variables-bootstrap.md` section 7.6 (section 14).

**Phase C: the `lifespan` start-up routine** (`backend/open_webui/main.py:344-472`). An exception
that escapes it makes uvicorn log `Application startup failed. Exiting.` and stop
(`.venv/lib/python3.12/site-packages/uvicorn/lifespan/on.py:58-59`;
`.venv/lib/python3.12/site-packages/uvicorn/server.py:104-106`).

| Step | What happens | Source | If it fails or is slow |
|---|---|---|---|
| C1 | Sizes the worker thread pool when `THREAD_POOL_SIZE` is set; records the instance id; starts the logger | `backend/open_webui/main.py:348-361` | Start-up stops |
| C2 | Wipes stored settings when `RESET_CONFIG_ON_START` is on | `backend/open_webui/main.py:363-364` | Start-up stops (database error) |
| C3 | Imports a legacy `DATA_DIR/config.json` into the database once and renames it `old_config.json`; seeds missing setting keys; loads runtime state (tool-server and arena access migration, MCP OAuth clients, the document embedding and reranking functions); converts the legacy webhook setting | `backend/open_webui/main.py:366-369`; `backend/open_webui/config.py:85-91`; `backend/open_webui/main.py:621-752` | MCP client errors are logged and skipped; embedding set-up errors are logged as `Error updating models: {e}`; database errors stop start-up |
| C4 | Publishes the `system.startup.started` event to event sinks | `backend/open_webui/main.py:370`; `backend/open_webui/events.py:45-47`, `:1199-1202` | A failing sink is logged as `Event sink failed for {event}` and start-up continues |
| C5 | Starts the licence lookup in the background when `LICENSE_KEY` is set | `backend/open_webui/main.py:372-374` | See C11 |
| C6 | Creates the first admin from `WEBUI_ADMIN_EMAIL` and `WEBUI_ADMIN_PASSWORD` when no accounts exist, then switches sign-up off | `backend/open_webui/main.py:377-380`; `backend/open_webui/utils/auth.py:634-665` | Logged; start-up continues |
| C7 | With `SAFE_MODE`, deactivates every function | `backend/open_webui/main.py:382-383` | Start-up stops (database error) |
| C8 | **Installs the Python packages that active functions and admins' tools declare**, blocking until pip finishes; skipped when `ENABLE_PLUGINS` or pip installs are off, or in offline mode | `backend/open_webui/main.py:385-388`; `backend/open_webui/utils/plugin.py:422-485` | Failures are logged (`Error installing requirements: {e}`) and start-up continues. **This step can take minutes**, during which the site does not answer |
| C9 | Creates the Redis client when Redis is configured, and starts the Redis listeners | `backend/open_webui/main.py:390-398`; `backend/open_webui/utils/redis.py:88-105` | Read from code: if the client cannot even be created (for example a malformed address), it is left empty, Redis is not used and `/ready` does not check it; a well-formed but unreachable address gives a client whose failures `/ready` reports as `Redis not ready` |
| C10 | Starts the background loops (section 8) and, when enabled, pre-fetches the model list and the tool and terminal server descriptions | `backend/open_webui/main.py:400-460` | Pre-fetch failures are logged as warnings and start-up continues |
| C11 | Waits up to two seconds for the licence lookup | `backend/open_webui/main.py:462-469` | Logged as a warning; start-up continues |
| C12 | **Marks the instance ready** (`app.state.startup_complete = True`) and publishes `system.startup.completed` | `backend/open_webui/main.py:471-472` | None |

After Phase C uvicorn logs `Application startup complete.` and begins serving
(`.venv/lib/python3.12/site-packages/uvicorn/lifespan/on.py:62`). `CLAUDE.md` lists the same
order; this table adds the import phase and the failure behaviour.

### 5.5 Health and Readiness

Three probes exist. None needs a sign-in, and `AppHTTPMiddleware` deliberately leaves them out
of its own database clean-up so that step cannot delay or fail them
(`backend/open_webui/utils/asgi_middleware.py:113-117`); `/ready` and `/health/db` still wait for
their own database ping.

| Probe | Checks | Healthy answer | Unhealthy answer | Source |
|---|---|---|---|---|
| `GET /health` | Nothing beyond "the process is serving" | HTTP 200 `{"status": true}` | No answer at all (the process is down or still starting) | `backend/open_webui/main.py:2963-2965` |
| `GET /ready` | 1. start-up finished; 2. a `SELECT 1` on the database; 3. a Redis `PING` when Redis is configured | HTTP 200 `{"status": true}` | HTTP 503 `{"detail": "Startup not complete"}`, `{"detail": "Database not ready"}` or `{"detail": "Redis not ready"}`, checked in that order | `backend/open_webui/main.py:2968-3006` |
| `GET /health/db` | A `SELECT 1` on the database only | HTTP 200 `{"status": true}` | Plain-text HTTP 500 `Internal Server Error` (no error handling in the endpoint) | `backend/open_webui/main.py:3009-3013` |

- The database ping uses a fresh connection from the pool rather than the per-thread session, so
  a broken session cannot make every later probe fail
  (`backend/open_webui/main.py:2939-2960`).
- `Startup not complete` is the answer of an instance that is serving before its start-up
  routine finished. Under uvicorn, as installed, requests are not served until start-up has
  finished (section 5.4), so during a normal start the probes get no answer rather than this
  text; it would appear if the server were run without the start-up routine (section 14).
- The Docker image's own health check calls `/health` and passes when `status` is `true`
  (`Dockerfile:212`). That check passes even when the database is down, which is why
  `/ready` exists. Which probe production's load balancer or orchestrator uses is
  **TO BE CONFIRMED**.
- A green `/health` therefore proves only that the process answers; it says nothing about the
  database, Redis, the model providers or sign-in (section 11.4).

### 5.6 Security Headers

`AppHTTPMiddleware` adds the same set of headers to every HTTP response that passes through it,
replacing any value an endpoint set for the same header
(`backend/open_webui/utils/asgi_middleware.py:134-143`). Answers produced outside it do not get
them: CORS pre-flight answers and the plain-text 500 from the outer error handler (both layers
sit outside it, section 4.2), and its own websocket-upgrade refusal, which is sent before the
header step is set up (`backend/open_webui/utils/asgi_middleware.py:102-108`). The
set is built once per process from environment variables read directly with `os.environ`, so
these are not admin settings and a change needs a restart
(`backend/open_webui/utils/asgi_middleware.py:91-95`; `backend/open_webui/utils/security_headers.py:6-59`).
**With none of the variables set, no security header is added**; only `X-Process-Time` (the
handling time in seconds) is added (`backend/open_webui/utils/asgi_middleware.py:138`).

| Environment variable | Header | Accepted values | Value used when the variable holds something else | Source |
|---|---|---|---|---|
| `CACHE_CONTROL` | `Cache-Control` | One or more of `public`, `private`, `no-cache`, `no-store`, `must-revalidate`, `proxy-revalidate`, `max-age=N`, `s-maxage=N`, `no-transform`, `immutable`, comma-separated | `no-store, max-age=0` | `backend/open_webui/utils/security_headers.py:98-105` |
| `HSTS` | `Strict-Transport-Security` | `max-age=N`, optionally `;includeSubDomains` and `;preload` | `max-age=31536000;includeSubDomains` | `backend/open_webui/utils/security_headers.py:62-68` |
| `PERMISSIONS_POLICY` | `Permissions-Policy` | A list of `feature=()` or `feature=(self)` for the 16 features named in the pattern (camera, microphone, geolocation, clipboard and others) | `none` | `backend/open_webui/utils/security_headers.py:80-86` |
| `REFERRER_POLICY` | `Referrer-Policy` | The eight standard policy names | `no-referrer` | `backend/open_webui/utils/security_headers.py:89-95` |
| `XCONTENT_TYPE` | `X-Content-Type-Options` | `nosniff` | `nosniff` | `backend/open_webui/utils/security_headers.py:115-119` |
| `XDOWNLOAD_OPTIONS` | `X-Download-Options` | `noopen` | `noopen` | `backend/open_webui/utils/security_headers.py:108-112` |
| `XFRAME_OPTIONS` | `X-Frame-Options` | `DENY` or `SAMEORIGIN` | `DENY` | `backend/open_webui/utils/security_headers.py:71-77` |
| `XPERMITTED_CROSS_DOMAIN_POLICIES` | `X-Permitted-Cross-Domain-Policies` | `none`, `master-only`, `by-content-type`, `by-ftp-filename` | `none` | `backend/open_webui/utils/security_headers.py:122-128` |
| `CONTENT_SECURITY_POLICY` | `Content-Security-Policy` | Passed through unchanged | (not checked) | `backend/open_webui/utils/security_headers.py:131-133` |
| `CONTENT_SECURITY_POLICY_REPORT_ONLY` | `Content-Security-Policy-Report-Only` | Passed through unchanged | (not checked) | `backend/open_webui/utils/security_headers.py:136-138` |
| `CROSS_ORIGIN_EMBEDDER_POLICY` | `Cross-Origin-Embedder-Policy` | `unsafe-none`, `require-corp`, `credentialless` | `require-corp` | `backend/open_webui/utils/security_headers.py:141-147` |
| `CROSS_ORIGIN_OPENER_POLICY` | `Cross-Origin-Opener-Policy` | `unsafe-none`, `same-origin-allow-popups`, `same-origin` | `same-origin` | `backend/open_webui/utils/security_headers.py:150-156` |
| `CROSS_ORIGIN_RESOURCE_POLICY` | `Cross-Origin-Resource-Policy` | `same-site`, `same-origin`, `cross-origin` | `same-origin` | `backend/open_webui/utils/security_headers.py:159-165` |
| `REPORTING_ENDPOINTS` | `Reporting-Endpoints` | Passed through unchanged | (not checked) | `backend/open_webui/utils/security_headers.py:168-170` |

Other headers set in this layer:

- Files served from `/cache/{path}` carry `X-Content-Type-Options: nosniff`, and anything that is
  not a picture, sound or video is sent as a download (`backend/open_webui/main.py:3046-3051`).
- `/pyodide/...` files carry `Access-Control-Allow-Origin: *` so the in-browser Python runtime can
  load them (`backend/open_webui/main.py:313-317`, `:3066-3069`).
- CORS headers come from the CORS layer (section 4.2).

Which of these variables production sets, and whether a proxy in front adds its own headers, is
**TO BE CONFIRMED**. Assessing whether the set is adequate is outside this document
(Security-sensitive: refer to the platform maintainer and U of T Information Security,
security.utoronto.ca).

### 5.7 Static Files, the `STATIC_DIR` Rewrite, the Manifest and the Cache

**What `/static` serves.** `/static/...` is served from `STATIC_DIR`, by default
`backend/open_webui/static` (`backend/open_webui/config.py:98`; `backend/open_webui/env.py:252`),
through Starlette's static-file server (`backend/open_webui/main.py:3023`). Every page loads
`/static/favicon.png`, `/static/favicon-96x96.png`, `/static/favicon.svg`, `/static/favicon.ico`,
`/static/apple-touch-icon.png`, `/static/loader.js` and `/static/custom.css`, and the splash uses
`/static/splash.png` or `/static/splash-dark.png` (`src/app.html:9-39`, `:78-83`, `:112-123`). The
API documentation page (development mode only) takes its script and style from
`/static/swagger-ui/` (`backend/open_webui/main.py:3054-3064`).

**The rewrite at every start-up** (`backend/open_webui/config.py:100-145`), while `config.py` is
imported (section 5.4, step B4):

1. Every **file** directly inside `STATIC_DIR` is deleted (sub-folders such as `swagger-ui/` are
   kept); errors are ignored.
2. Every file under `FRONTEND_BUILD_DIR/static` (the build's copy of the repository's
   `static/static/` folder) is copied into `STATIC_DIR`, keeping sub-folders.
3. `favicon.png`, `splash.png` and `loader.js` are copied from the build once more.
4. If the legacy `CUSTOM_NAME` variable is set, a logo and splash picture are downloaded from the
   upstream `api.openwebui.com` service and written over `favicon.png` and `splash.png`, and the
   product name is replaced by the downloaded name (`backend/open_webui/config.py:187-223`).

Consequences for support:

- **The pictures users see come from the front-end build, not from the files committed under
  `backend/open_webui/static/`.** The fork changed both copies (`static/static/` and
  `backend/open_webui/static/`; ground truth), so a build made from the `uoft` branch shows the
  U of T pictures. A build made from upstream sources, or a stale `build/` folder, puts the upstream
  pictures back at every start-up (section 11.5).
- **Edits made directly inside `STATIC_DIR` are lost at the next start-up** (step 1), including
  `custom.css` and `loader.js`, unless they are made in the build's `static/` folder.
- Read from code: when no front-end build exists (an API-only start), step 1 still deletes the
  files and step 2 has nothing to copy, so `STATIC_DIR` is left without its top-level files. In a
  development checkout that shows up as deleted files under `backend/open_webui/static/`.
- The Docker image copies the build to `/app/build` and the backend (including its `static`
  folder) to `/app/backend`, so the rewrite runs inside the container at each start
  (`Dockerfile:203-208`).
- When the backend is installed as a Python package and started with `open-webui serve`, the
  build folder is the package's own `frontend` folder (`backend/open_webui/env.py:256-257`), so the
  pictures are whatever that package was built with.

**`/manifest.json`** (`backend/open_webui/main.py:2868-2917`). With `EXTERNAL_PWA_MANIFEST_URL`
set, the server fetches that address and returns its JSON (an error there gives an HTTP 500).
Otherwise it generates a manifest named after `WEBUI_NAME`, with the description
`{name} is an open, extensible, user-friendly interface for AI that adapts to your workflow.`,
start address `/`, `/static/logo.png` as both icons, and a share target that sends shared text to
`/?shared=...` (section 2.5). Because this route is registered before the front-end mount, the
build's own `manifest.json` file (an empty object, `static/manifest.json`) is not what production
browsers receive.

**`/opensearch.xml`** (`backend/open_webui/main.py:2920-2936`) lets a browser add the site as a
search engine: the short name is `WEBUI_NAME`, the description `Search {name}`, and the search
address is `{webui.url}/?q={searchTerms}`. The `webui.url` setting comes from `WEBUI_URL`
(code default empty, `backend/open_webui/config.py:1661`, `:3082`); with it empty the addresses in
the file have no host. The repository also contains a static `static/opensearch.xml` with
`localhost` addresses, which the route overrides in production.

**`/cache/{path}`** (`backend/open_webui/main.py:3026-3051`) serves files from `DATA_DIR/cache`
to signed-in people only; an address outside the cache folder or a missing file answers HTTP 404
`File not found`.

**`/pyodide/...`** is mounted only when the build contains a `pyodide` folder; the build step
downloads it (`backend/open_webui/main.py:3066-3069`; `scripts/prepare-pyodide.js`; see
`code-execution-and-interpreter.md`).

### 5.8 The Single-Page Fallback and the `.js` Rule

The front-end build is mounted at `/` with HTML mode on (`backend/open_webui/main.py:3071-3075`),
through a small subclass of the static-file server (`backend/open_webui/main.py:298-310`):

1. If the address names a file in the build, that file is returned.
2. If it names a folder that has an `index.html`, that page is returned.
3. Otherwise the server would answer 404. The subclass catches that 404 and returns the build's
   `index.html` instead, so the browser loads the application and its router shows the right page
   (or the application's own error page, `src/routes/+error.svelte`).
4. **Except for addresses ending in `.js`**: a missing script answers a real HTTP 404, so a
   missing code file fails loudly instead of being answered with a web page
   (`backend/open_webui/main.py:303-306`).
5. Methods other than `GET` and `HEAD` on any address that reaches this mount answer HTTP 405
   (`.venv/lib/python3.12/site-packages/starlette/staticfiles.py:113-114`).

Why the `.js` rule matters: the built application's code files have content-hash names. After a
new version is deployed, a browser tab that was opened on the old version may ask for an old file
name; it now gets a 404 and that part of the page fails until the person reloads. SvelteKit is
configured to poll for a new version every 60 seconds (`svelte.config.js:20-41`); no handler for
that signal was found in `src/` (a search for `updated` and `version.json`), so what the page does
on a new version is the framework's default (section 14).

If the build folder is missing entirely, nothing is mounted at `/`: every page address answers
`{"detail":"Not Found"}` and the log shows the "Serving API only" warning
(`backend/open_webui/main.py:3076-3077`).

### 5.9 Version, Update Check and Changelog

- **The version** is read at import from the repository's `package.json` (`0.11.4`), or from the
  installed package when started with `open-webui serve`; `0.0.0` is used if it cannot be read
  (`backend/open_webui/env.py:142-151`; ground truth). `GET /api/version` returns it with
  `deployment_id` (empty unless `DEPLOYMENT_ID` is set) (`backend/open_webui/main.py:2586-2591`).
  The fork did not change the version number, so MedIT GPT reports the upstream version.
- **The update check reports upstream releases.** `GET /api/version/updates` (signed in) asks
  GitHub for the latest release of `open-webui/open-webui`, with a one-second time-out, and returns
  `{"current": "<running>", "latest": "<upstream tag without the v>"}`; on any failure it returns
  `"latest": null` and logs `Version update check failed: {e}`. With `ENABLE_VERSION_UPDATE_CHECK`
  off (forced off by `OFFLINE_MODE`) it returns the running version as the latest without calling
  out (`backend/open_webui/main.py:2594-2613`; `backend/open_webui/env.py:1200-1205`). A "new
  version" therefore means a new **upstream** release, not a new MedIT GPT build; whether and when
  the fork adopts it is **TO BE CONFIRMED** with the platform maintainer.
- **Who sees it.** Only admins, and only when the check is on. On entering the app (at most once
  a day after the notice was dismissed) a toast appears when the upstream version is newer and the
  admin's **Toast Notifications for New Updates** setting is on
  (`src/routes/(app)/+layout.svelte:369-382`, `:415-439`;
  `src/lib/components/common/InterfaceSettings.svelte:715-735`; label in
  `src/lib/i18n/locales/en-US/translation.json:2989`). The toast reads
  `A new version (v{{LATEST_VERSION}}) is now available.` followed by the link
  `Update for the latest features and improvements.` to the upstream releases page
  (`src/lib/components/layout/UpdateInfoToast.svelte:19-26`). The version line in
  **Settings > About** and in the admin **General** panel shows `Checking for updates...`,
  `(v{latest} available!)`, `(latest)` or `Could not check for updates`
  (`src/lib/components/chat/Settings/About.svelte:64-90`;
  `src/lib/components/admin/Settings/General.svelte:137-160`). The comparison treats a missing
  latest version, or a running version of `0.0.0`, as "no update" (`src/lib/utils/index.ts:660-668`).
- **The changelog.** At import `env.py` turns `CHANGELOG.md` into a dictionary keyed by version
  (`backend/open_webui/env.py:184-222`); `GET /api/changelog` (no sign-in) returns the first five
  entries, which are the newest because the file lists newest first
  (`backend/open_webui/main.py:2616-2618`). The **What's New** window opens by itself only for
  admins whose saved version differs from the running one (`src/routes/(app)/+layout.svelte:355-356`;
  `src/lib/components/ChangelogModal.svelte:30-46`). The text is the **upstream** changelog; the fork
  adds no entry. Read from code: the parser expects every second-level heading to look like
  `## [0.11.4] - 2026-09-21`; a heading without ` - ` would stop the import with an error, which
  matters only if someone edits `CHANGELOG.md` (all 172 headings in v0.11.4 match).

### 5.10 Shut-Down

When the process is asked to stop (a redeploy, a container stop), uvicorn first stops accepting
connections, asks open connections to finish and waits for them (with no time limit unless one is
configured), and only then runs the application's shut-down routine
(`.venv/lib/python3.12/site-packages/uvicorn/server.py:269-299`). The routine
(`backend/open_webui/main.py:476-496`):

1. publishes `system.shutdown.started`;
2. closes the shared outbound HTTP client (section 5.11);
3. cancels the Redis task listener, the task heartbeat and the websocket event listener, where
   they were started;
4. cancels the two pool-clean-up loops and the automation scheduler (section 8);
5. publishes `system.shutdown.completed`.

`app.state.startup_complete` is not reset, so `/ready` keeps answering 200 for as long as the
process still serves requests (`backend/open_webui/main.py:471`, `:2968-3006`). Work running in
that process's background tasks, such as a reply still being written, ends with the process; how
an interrupted reply looks afterwards is in
[`chat-completion-pipeline-and-generation-tasks.md`](chat-completion-pipeline-and-generation-tasks.md)
section 11.14. Without Redis, rate-limit counters live only in each process's memory and are lost
(section 5.12), and sign-out revocation is not stored at all (ground truth).

### 5.11 Outbound Calls: The Shared HTTP Client and Forwarded User Details

**The shared HTTP client** (`backend/open_webui/utils/session_pool.py`). Calls to model providers
and several other services (Ollama, OpenAI-compatible connections, audio, images, ComfyUI, several
web-search providers, the external manifest) reuse one long-lived HTTP client per process
instead of opening a new one per request (`backend/open_webui/utils/session_pool.py:1-24`,
`:54-83`). It is created on first use, logs
`Created shared aiohttp session pool (limit={limit}, per_host={per_host}, dns_ttl={dns_ttl})`, and
is closed at shut-down with `Closed shared aiohttp session pool` (`:77-82`, `:86-92`).

| Setting (environment) | What the docstring says | What the code does | Source |
|---|---|---|---|
| `AIOHTTP_POOL_CONNECTIONS` | Default 100 total connections | **Unset means no limit** (`limit=0`); a non-number also means no limit | `backend/open_webui/utils/session_pool.py:9`, `:62-65`; `backend/open_webui/env.py:710-717` |
| `AIOHTTP_POOL_CONNECTIONS_PER_HOST` | Default 30 per host | **Unset means no limit** | `backend/open_webui/utils/session_pool.py:10`, `:66-69`; `backend/open_webui/env.py:719-726` |
| `AIOHTTP_POOL_DNS_TTL` | Default 300 seconds | 300 seconds; a negative or non-number value also gives 300 | `backend/open_webui/utils/session_pool.py:11`, `:59`; `backend/open_webui/env.py:728-734` |
| `AIOHTTP_CLIENT_TIMEOUT` | (not mentioned) | Default total time limit per call in seconds (a caller may set its own); **unset means no limit**, a non-number gives 300 | `backend/open_webui/utils/session_pool.py:43-47`; `backend/open_webui/env.py:608-612` |
| `AIOHTTP_CLIENT_STREAM_IDLE_TIMEOUT` | (not mentioned) | For streaming calls, the longest silence allowed between chunks; unset, zero or negative means none | `backend/open_webui/utils/session_pool.py:44-47`; `backend/open_webui/env.py:615-625` |

So the module's own description of its limits is out of date: in v0.11.4 a default install has
no connection cap and no overall time limit on these calls. Production values are **TO BE
CONFIRMED**.

**Forwarded user details** (`backend/open_webui/utils/headers.py`). When
`ENABLE_FORWARD_USER_INFO_HEADERS` is on (code default off, `backend/open_webui/env.py:989`),
calls to model connections, tool servers, audio, image, retrieval and several web-search and
document services carry the person's name, id, email and role in `X-OpenWebUI-User-*` headers (the
names are configurable), or a single short-lived signed header instead when a signing secret is
configured, plus the kind of credential the request used (`backend/open_webui/utils/headers.py:52-82`;
`backend/open_webui/env.py:989-1008`). Separately, admins can define **custom headers** on a
connection whose values may contain placeholders such as `{{USER_EMAIL}}`, `{{USER_NAME}}`,
`{{USER_ID}}`, `{{USER_ROLE}}`, `{{USER_GROUPS}}`, `{{CHAT_ID}}`, `{{MESSAGE_ID}}`, `{{FILE_NAME}}`
and `{{USER_AGENT}}`, filled in per request (`backend/open_webui/utils/headers.py:107-163`).
Both mechanisms send **personal data to the provider**; whether production uses them is
**TO BE CONFIRMED**, and questions about them go to the platform maintainer and the
Privacy Office.

### 5.12 The Rate-Limit Helper

`RateLimiter` (`backend/open_webui/utils/rate_limit.py:8-114`) counts events per key in
one-minute buckets and refuses when the total over the window is exceeded:

- **Counting.** Each check adds one to the current bucket, then sums the current bucket and the
  previous `window ÷ bucket` buckets; the call is refused when the sum is **greater than** the
  limit (`:79-93`, `:101-109`). Every check counts, whether or not the attempt it guards succeeds.
- **Storage.** With Redis, buckets are Redis keys that expire after the window plus one bucket,
  shared by all workers (`:35-36`, `:83-85`). Without Redis, or if a Redis call fails, each worker
  counts in its own memory, so with several workers the effective limit is higher (`:55-61`).
- **Where it is used** (two places, `backend/open_webui/routers/auths.py:91-100`):
  - password sign-in, keyed by the lower-cased email, 15 attempts per 180 seconds, refused with
    HTTP 429 `API rate limit exceeded` (ground truth; `backend/open_webui/routers/auths.py:818-822`);
  - the OAuth token exchange, keyed by client address, only when
    `OAUTH_TOKEN_EXCHANGE_RATE_LIMIT` is set (`backend/open_webui/routers/auths.py:1642-1648`;
    `backend/open_webui/env.py:884-890`; see `sso-oauth-oidc-and-scim.md`).

There is no general request rate limit on the API in this code; any wider throttling would be in
a proxy in front of the service (**TO BE CONFIRMED**).

## 6. Data Model

This layer defines **no database table** of its own. What it keeps is per-process memory
(`app.state`), a few files on disk, two cookies and, with Redis, a few keys. Table definitions
belong to `database-schema-identity-chats-and-config.md` and
`database-schema-content-and-collaboration.md` (both planned).

### 6.1 Per-Process Memory (`app.state`)

Each worker process has its own copy; nothing here survives a restart. Only `MODELS` is shared
between workers, and only when `WEBSOCKET_MANAGER` is `redis`
(`backend/open_webui/socket/main.py:133-148`, `:185`).

| Attribute | Holds | Set at |
|---|---|---|
| `startup_complete` | `False` until the last start-up step, then `True`; read by `/ready` | `backend/open_webui/main.py:521`, `:471` |
| `main_loop`, `instance_id` | The event loop (for code that must schedule work on it) and this process's instance id | `backend/open_webui/main.py:348`, `:360`, `:531` |
| `redis` | The asynchronous Redis client, or nothing when Redis is not configured or unusable | `backend/open_webui/main.py:390`, `:532` |
| `redis_task_command_listener`, `redis_task_heartbeat`, `redis_event_listener` | Handles of the Redis background tasks, when started | `backend/open_webui/main.py:393-398` |
| `periodic_usage_pool_cleanup`, `periodic_session_pool_cleanup`, `scheduler_worker_loop` | Handles of the always-on background loops | `backend/open_webui/main.py:400-405` |
| `oauth_manager`, `oauth_client_manager` | Single sign-on and tool-server OAuth helpers | `backend/open_webui/main.py:524-529` |
| `WEBUI_NAME` | The product name (`MedIT GPT` by default on this fork) used by `/api/config`, the manifest and the search descriptor | `backend/open_webui/main.py:538` |
| `LICENSE_METADATA`, `USER_COUNT` | Licence details, filled in only when `LICENSE_KEY` is set | `backend/open_webui/main.py:539-540`; `backend/open_webui/utils/auth.py:99`, `:106` |
| `EXTERNAL_PWA_MANIFEST_URL` | Optional address of an external manifest | `backend/open_webui/main.py:541` |
| `OLLAMA_MODELS`, `OPENAI_MODELS`, `BASE_MODELS`, `MODELS` | Model lists fetched from the connections; `MODELS` is what chat requests resolve against | `backend/open_webui/main.py:563`, `:572`, `:612`, `:794` |
| `TOOL_SERVERS`, `TERMINAL_SERVERS` | Fetched tool-server and terminal-server descriptions | `backend/open_webui/main.py:580`, `:588` |
| `ENABLE_SCIM` | Whether SCIM is on (the SCIM credential is also held here and is not described) | `backend/open_webui/main.py:603` |
| `EMBEDDING_FUNCTION`, `RERANKING_FUNCTION`, `ef`, `rf`, `YOUTUBE_LOADER_TRANSLATION` | Document-search models and helpers, set up at start-up | `backend/open_webui/main.py:666-752` |
| `faster_whisper_model`, `speech_synthesiser`, `speech_speaker_embeddings_dataset` | Local speech models, loaded on first use | `backend/open_webui/main.py:776-778` |
| `CHAT_COMPLETION_HANDLER` | The chat endpoint itself, so automations can run the full pipeline | `backend/open_webui/main.py:1915` |

### 6.2 Tables This Layer Reads or Writes

| Table | Used for | Source |
|---|---|---|
| `config` | Every `Config.get`, `Config.get_many` and `Config.upsert` call: `/api/config`, start-up seeding, the admin bootstrap switching sign-up off, migrations of legacy settings | `backend/open_webui/main.py:366-380`, `:621-752`, `:2256-2308` |
| `user` | Identifying the caller, "are there any accounts yet" (onboarding), user counts, the last-active time on each authenticated call | `backend/open_webui/utils/auth.py:455`, `:483`, `:511`; `backend/open_webui/main.py:2248-2255`, `:2637` |
| `auth` (with `user`) | Creating the bootstrap admin | `backend/open_webui/utils/auth.py:644-656` (account check, then creation) |
| `function`, `tool` | Safe mode (deactivate all functions) and reading plugin requirements at start-up | `backend/open_webui/main.py:382-388`; `backend/open_webui/utils/plugin.py:465-480` |
| `chat`, `model` | Task endpoints (ownership checks) and the model-unload lookup | `backend/open_webui/main.py:2142-2215`, `:965-974` |

### 6.3 Files and Folders

| Path | Role | Source |
|---|---|---|
| `FRONTEND_BUILD_DIR` (default `<repository>/build`; in the image `/app/build`) | The built front end served at `/`, and the source of `/static` at each start-up | `backend/open_webui/env.py:254-257`; `Dockerfile:203` |
| `STATIC_DIR` (default `backend/open_webui/static`) | Served at `/static`; top-level files rewritten at each start-up (section 5.7) | `backend/open_webui/config.py:98-145` |
| `DATA_DIR/cache` | Served at `/cache/{path}` to signed-in people | `backend/open_webui/config.py:182-183`; `backend/open_webui/main.py:3026-3051` |
| `DATA_DIR/config.json` | Legacy settings file; imported once into the database and renamed `old_config.json` | `backend/open_webui/config.py:85-91` |
| `package.json`, `CHANGELOG.md` (repository root; in the image `/app/`) | Version number and the changelog | `backend/open_webui/env.py:142-151`, `:184-191`; `Dockerfile:204-205` |
| `DATA_DIR/audit.log` | The audit log, when switched on; contains personal data (ground truth) | `backend/open_webui/env.py:1234` |

`DATA_DIR` holds live data and is never opened for this documentation (research rule 8).

### 6.4 Cookies and Redis Keys

| Item | Purpose | Source |
|---|---|---|
| `token` cookie | Carries the session token; set at sign-in and refreshed by the session-user call | `backend/open_webui/routers/auths.py:196-207`, `:280-290` |
| `owui-session` cookie | Single sign-on state during the round trip to the identity provider; cleared at sign-out | `backend/open_webui/main.py:2660`, `:2671`; `backend/open_webui/routers/auths.py:987` |
| `{prefix}:ratelimit:{key}:{bucket}` (Redis) | Rate-limit buckets; for sign-in the key is the **lower-cased email address**, so these keys contain personal data | `backend/open_webui/utils/rate_limit.py:35-36`; `backend/open_webui/routers/auths.py:818` |
| `{prefix}:session:...` (Redis) | Single sign-on sessions when `ENABLE_STAR_SESSIONS_MIDDLEWARE` is on | `backend/open_webui/main.py:2651-2654` |

`{prefix}` is `REDIS_KEY_PREFIX` (`backend/open_webui/env.py`; see
[`configuration-environment-variables-bootstrap.md`](configuration-environment-variables-bootstrap.md)).

## 7. Settings and Configuration

Almost everything that shapes this layer is an **environment variable** read once when the
process starts; changing one needs a restart and is done by the platform maintainer, not in the
admin panels. The full catalogue, with parsing rules, is in
[`configuration-environment-variables-bootstrap.md`](configuration-environment-variables-bootstrap.md);
the rows below are the ones that change routing, start-up, probes, static files, headers or
outbound calls. Code defaults are what the repository says; **production values are
TO BE CONFIRMED**.

### 7.1 Environment-Only Switches That Shape This Layer

| Variable | Code default | Effect here | Source |
|---|---|---|---|
| `ENV` | `dev` (the Docker image sets `prod`) | `dev` serves the interactive API documentation at `/docs` and `/openapi.json` | `backend/open_webui/env.py:139`; `backend/open_webui/main.py:506-512`; `Dockerfile:74` |
| `WEBUI_NAME` | `MedIT GPT` (fork change) | Product name in `/api/config`, `/manifest.json`, `/opensearch.xml` and the front end | `backend/open_webui/env.py:951`; `backend/open_webui/main.py:538` |
| `FRONTEND_BUILD_DIR` | `<repository>/build` (`open_webui/frontend` when started with `open-webui serve`) | Where the front end and the source of `/static` come from | `backend/open_webui/env.py:254-257` |
| `STATIC_DIR` | `backend/open_webui/static` | Folder served at `/static`, rewritten at start-up | `backend/open_webui/config.py:98` |
| `CUSTOM_NAME` | empty | Legacy: downloads a logo, splash and name from the upstream service at start-up | `backend/open_webui/config.py:187-223` |
| `EXTERNAL_PWA_MANIFEST_URL` | unset | `/manifest.json` returns the JSON fetched from this address | `backend/open_webui/env.py:1018`; `backend/open_webui/main.py:2870-2882` |
| `CORS_ALLOW_ORIGIN` | `*` (semicolon-separated list) | Origins allowed by the CORS layer | `backend/open_webui/config.py:2134`; `backend/open_webui/main.py:831-837` |
| `ENABLE_COMPRESSION_MIDDLEWARE` | on | Response compression layer | `backend/open_webui/env.py:790`; `backend/open_webui/main.py:816-817` |
| `AUDIT_LOG_LEVEL` | `NONE` | Audit layer on when `METADATA`, `REQUEST` or `REQUEST_RESPONSE` (see the note in section 5.4 on other values) | `backend/open_webui/env.py:1234`; `backend/open_webui/main.py:796-813` |
| `ENABLE_STAR_SESSIONS_MIDDLEWARE` | off | Keeps single sign-on sessions in Redis instead of in the cookie | `backend/open_webui/env.py:967`; `backend/open_webui/main.py:2649-2674` |
| `WEBUI_SESSION_COOKIE_SAME_SITE`, `WEBUI_SESSION_COOKIE_SECURE` | `lax`, off | Flags on the `owui-session` cookie (and, unless overridden, on the `token` cookie) | `backend/open_webui/env.py:769-778` |
| `CUSTOM_API_KEY_HEADER` | `x-api-key` | Extra header from which an API key is accepted | `backend/open_webui/env.py:812`; `backend/open_webui/utils/asgi_middleware.py:130-131` |
| `ENABLE_ADMIN_ANALYTICS` | on | Mounts the analytics router | `backend/open_webui/config.py:2094`; `backend/open_webui/main.py:878-879` |
| `ENABLE_SCIM` | off | Mounts the SCIM router | `backend/open_webui/env.py:907`; `backend/open_webui/main.py:886-887` |
| `ENABLE_ADMIN_EXPORT` | on | Allows the raw database download in the utilities router | `backend/open_webui/config.py:2082`; `backend/open_webui/routers/utils.py:77-78` |
| `ENABLE_OAUTH_BACKCHANNEL_LOGOUT` | off | Without it, `/oauth/backchannel-logout` answers 404 | `backend/open_webui/env.py:901`; `backend/open_webui/main.py:2863-2864` |
| `ENABLE_VERSION_UPDATE_CHECK`, `OFFLINE_MODE` | on, off | Whether `/api/version/updates` calls GitHub; offline mode forces the check off | `backend/open_webui/env.py:1200-1205` |
| `DEPLOYMENT_ID`, `INSTANCE_ID` | empty, random per process | Labels returned by `/api/version` and used in events | `backend/open_webui/env.py:154-155` |
| `ENABLE_PUBLIC_ACTIVE_USERS_COUNT` | on | Off restricts `/api/usage` to admins | `backend/open_webui/env.py:367`; `backend/open_webui/main.py:2628-2633` |
| `ENABLE_DB_MIGRATIONS` | on | Runs migrations when the configuration module is imported | `backend/open_webui/env.py:157`; `backend/open_webui/config.py:81-82` |
| `RESET_CONFIG_ON_START` | off | Wipes stored settings at every start | `backend/open_webui/env.py:368`; `backend/open_webui/main.py:363-364` |
| `WEBUI_ADMIN_EMAIL`, `WEBUI_ADMIN_PASSWORD`, `WEBUI_ADMIN_NAME` | empty, empty, `Admin` | First-admin bootstrap when no accounts exist (values are secrets; never record them) | `backend/open_webui/env.py:798-800`; `backend/open_webui/main.py:377-380` |
| `SAFE_MODE` | off | Deactivates every function at start-up | `backend/open_webui/env.py:965`; `backend/open_webui/main.py:382-383` |
| `ENABLE_PLUGINS` | on | Off skips installing plugin requirements at start-up | `backend/open_webui/env.py:1186`; `backend/open_webui/utils/plugin.py:461-463` |
| `THREAD_POOL_SIZE` | unset | Size of the worker thread pool | `backend/open_webui/config.py:2103-2111`; `backend/open_webui/main.py:350-358` |
| `LICENSE_KEY` | empty | Starts the licence lookup at start-up | `backend/open_webui/env.py:922`; `backend/open_webui/main.py:372-374` |
| `ENABLE_OTEL` | off | OpenTelemetry instrumentation | `backend/open_webui/env.py:1263`; `backend/open_webui/main.py:550-553` |
| `ENABLE_ORJSON` | off | JSON library (section 7.4) | `backend/open_webui/env.py:162` |
| `REDIS_URL`, `WEBSOCKET_MANAGER`, `REDIS_TASK_TTL` | empty, empty, 300 | Redis client and listeners at start-up; readiness pings Redis when configured | `backend/open_webui/env.py:381`, `:393-397`, `:476`; `backend/open_webui/main.py:390-398` |
| `AIOHTTP_POOL_CONNECTIONS`, `AIOHTTP_POOL_CONNECTIONS_PER_HOST`, `AIOHTTP_POOL_DNS_TTL`, `AIOHTTP_CLIENT_TIMEOUT`, `AIOHTTP_CLIENT_STREAM_IDLE_TIMEOUT` | no limit, no limit, 300, no limit, none | Shared outbound HTTP client (section 5.11) | `backend/open_webui/env.py:608-625`, `:710-734` |
| `ENABLE_FORWARD_USER_INFO_HEADERS` and the `FORWARD_USER_INFO_HEADER_*` names | off | Forwarding of the person's details to providers (section 5.11) | `backend/open_webui/env.py:989-1008` |
| `CACHE_CONTROL`, `HSTS`, `PERMISSIONS_POLICY`, `REFERRER_POLICY`, `XCONTENT_TYPE`, `XDOWNLOAD_OPTIONS`, `XFRAME_OPTIONS`, `XPERMITTED_CROSS_DOMAIN_POLICIES`, `CONTENT_SECURITY_POLICY`, `CONTENT_SECURITY_POLICY_REPORT_ONLY`, `CROSS_ORIGIN_EMBEDDER_POLICY`, `CROSS_ORIGIN_OPENER_POLICY`, `CROSS_ORIGIN_RESOURCE_POLICY`, `REPORTING_ENDPOINTS` | all unset | Security headers (section 5.6) | `backend/open_webui/utils/security_headers.py:35-50` |

### 7.2 Persistent Settings Read by This Layer

These live in the `config` table and are edited in the admin panels; the stored value wins over
the environment after first boot (ground truth). This layer reads them at request time:

| Setting | Read by | Effect | Source |
|---|---|---|---|
| The 51 keys listed in `get_app_config` (sign-in options, feature switches, defaults, limits, pending overlay, watermark) | `/api/config` | What the front end shows (section 5.3) | `backend/open_webui/main.py:2256-2308` |
| `webui.url` | `/opensearch.xml` | Host in the search descriptor | `backend/open_webui/main.py:2922` |
| `ui.model_order_list` | `/api/models` | Order of the model list | `backend/open_webui/main.py:928-937` |
| `models.base_models_cache`, `tool_server.connections` | Start-up | Whether the model list and tool-server descriptions are fetched before serving | `backend/open_webui/main.py:407-460` |
| `ui.enable_signup` | Admin bootstrap | Set to off after the bootstrap admin is created | `backend/open_webui/main.py:378-380` |
| `auth.enable_api_keys`, `user.permissions`, `auth.api_key.endpoint_restrictions`, `auth.api_key.allowed_endpoints` | Every API-key request | Whether a key is accepted and where (section 3.2) | `backend/open_webui/utils/auth.py:519-550` |
| `code_execution.enable`, `code_execution.engine`, `code_execution.jupyter.*` | `/api/v1/utils/code/execute` | Whether and where code runs | `backend/open_webui/routers/utils.py:43-64` |

Key-by-key descriptions are in
[`configuration-persistent-settings-a-to-o.md`](configuration-persistent-settings-a-to-o.md) and
`configuration-persistent-settings-r-to-w.md`.

### 7.3 Where Each Kind of Setting Is Changed

| Kind | Changed by | Takes effect |
|---|---|---|
| Environment variables (section 7.1) | Platform maintainer, in the deployment's environment (location **TO BE CONFIRMED**) | At the next restart of every worker |
| Persistent settings (section 7.2) | Admins, in `/admin/settings/...` | At the next call that reads them; `/api/config` answers change on the next page load |
| Per-person settings that affect messages in this layer (for example **Toast Notifications for New Updates**) | Each admin, in **Settings > Interface** | Immediately in that browser |

### 7.4 JSON Encoding (`ENABLE_ORJSON`)

With `ENABLE_ORJSON` off (the code default) the application uses Python's standard JSON library,
and socket.io uses its own (`backend/open_webui/utils/json_codec.py:78-84`). With it on:

- request bodies are parsed and plain JSON responses are written with `orjson`; endpoints that
  declare a response model keep FastAPI's own encoder (`backend/open_webui/main.py:499-501`;
  `backend/open_webui/utils/json_response.py:14-55`);
- the shared `JSONCodec` used across the application and the socket.io codec switch to `orjson`
  (`backend/open_webui/utils/json_codec.py:19-77`).

Differences an operator might notice with it on (from the module's own description,
`backend/open_webui/utils/json_codec.py:25-40`, and `backend/open_webui/utils/json_response.py:20-23`):
output from the fast path is compact; dates, UUIDs and data classes are written instead of refused; `NaN` and
`Infinity` become `null` instead of causing an error; very large integers are read back as
decimals; anything `orjson` refuses falls back to the standard library. The three Unicode line
separators are escaped so streamed (server-sent event) frames are not split
(`backend/open_webui/utils/json_codec.py:52-56`).

## 8. Cron Jobs and Background Processes

There is no crontab and no separate worker process (ground truth). Everything below runs inside
**each** server process, started by the `lifespan` routine (section 5.4) and cancelled at shut-down
(section 5.10). Full behaviour belongs to `background-processes-and-scheduling.md` and
`websockets-realtime-and-redis.md` (both planned); this table records what this layer starts.

| What | Started when | How often | Source |
|---|---|---|---|
| `periodic_session_pool_cleanup` | Always | Removes websocket sessions not seen for `SESSION_POOL_TIMEOUT` (at least 120 seconds); with Redis only the instance holding a lock does it | `backend/open_webui/main.py:401`; `backend/open_webui/socket/main.py:128-129`, `:212-263` |
| `periodic_usage_pool_cleanup` | Always | Prunes the "models in use" pool (what `/api/usage` reports); lock-protected the same way | `backend/open_webui/main.py:400`; `backend/open_webui/socket/main.py:266-308` |
| `scheduler_worker_loop` | Always | Polls due automations every `SCHEDULER_POLL_INTERVAL` seconds (default 10, plus up to 2 seconds of jitter) and timers every `TIMER_POLL_INTERVAL` (default 1) | `backend/open_webui/main.py:403-405`; `backend/open_webui/utils/automations.py:53-54`, `:69-126` |
| `redis_task_command_listener` | Redis configured | Listens continuously for task commands from other instances (for example "stop this chat") | `backend/open_webui/main.py:392-393`; `backend/open_webui/tasks.py:28-65` |
| `redis_task_heartbeat` | Redis configured and `REDIS_TASK_TTL` above 0 (default 300) | Every `REDIS_TASK_TTL ÷ 4` seconds | `backend/open_webui/main.py:394-395`; `backend/open_webui/tasks.py:69-72` |
| `redis_event_listener` | `WEBSOCKET_MANAGER` is `redis` | Continuous; relays websocket events between instances | `backend/open_webui/main.py:397-398`; `backend/open_webui/socket/main.py:963-994` |

`automation_worker_loop` (listed in the inventory) is only a deprecated alias that calls
`scheduler_worker_loop`; `lifespan` does not start it separately
(`backend/open_webui/utils/automations.py:64-66`).

One-off work during start-up, not repeated: the licence lookup (only with `LICENSE_KEY`), the
plugin-requirement installation, and the optional model-list and tool-server pre-fetch (section
5.4, steps C5, C8 and C10).

Work done **at request time** rather than in the background:

- each authenticated call schedules a small update of the person's last-active time, without
  waiting for it (`backend/open_webui/utils/auth.py:483`);
- `/api/config`, `/api/version/updates` and the health probes do their work when called; nothing
  pre-computes them;
- in the browser, the built front end asks every 60 seconds whether a new version was deployed
  (`svelte.config.js:20-41`); each time the real-time connection (re)connects it also calls
  `/api/version` and reloads the page when the version or `deployment_id` changed
  (`src/routes/+layout.svelte:184-215`; section 11.7);
- the Docker image's health check calls `/health` at Docker's default interval (the Dockerfile
  sets none; `Dockerfile:212`).

## 9. Notifications and Emails

The application sends **no email** (ground truth). What this layer emits:

| Notification | Kind | When | Source |
|---|---|---|---|
| `system.startup.started`, `system.startup.completed` | System events delivered to the configured event sinks (for example admin event webhooks) | At the start and end of the start-up routine | `backend/open_webui/main.py:370`, `:472`; `backend/open_webui/events.py:45-50` |
| `system.shutdown.started`, `system.shutdown.completed` | As above | At the start and end of the shut-down routine | `backend/open_webui/main.py:476`, `:496`; `backend/open_webui/events.py:51-56` |
| `config.webhook.updated` | As above, with the action (`created`, `updated`, `deleted`) | When an admin changes an event webhook through `/api/events/webhooks` | `backend/open_webui/main.py:2519-2532`, `:2553-2566`, `:2576-2583`; `backend/open_webui/events.py:63-65` |
| `chat:completion`, `chat:tasks:cancel` | Websocket events to the chat's owner | When **Stop** finds no running task but an unfinished reply, which it then finalizes | `backend/open_webui/main.py:2201-2212` |
| The update toast and the **What's New** window | In-app notices for admins | Section 5.9 | `src/routes/(app)/+layout.svelte:355-356`, `:369-382`, `:428-439` |

Event sinks, event webhooks, personal notification targets and browser notifications are described
in [`notifications-webhooks-events-and-banners.md`](notifications-webhooks-events-and-banners.md).
A failing sink does not stop start-up; it is logged as `Event sink failed for {event}`
(`backend/open_webui/events.py:1199-1202`).

## 10. Error, Warning and Notice Messages (Verbatim)

Messages produced by this layer, grouped by where they appear. "Log" rows go to standard output
only (ground truth) and are seen by the platform maintainer, never by users. API texts reach users
as the `detail` of a JSON error, usually shown in a toast. Interpolated values are written as
`{name}`. Messages raised inside the chat pipeline are in
[`chat-completion-pipeline-and-generation-tasks.md`](chat-completion-pipeline-and-generation-tasks.md)
section 10; the platform catalogue
[`error-messages-backend-identity-admin-and-platform.md`](error-messages-backend-identity-admin-and-platform.md)
section 10.18 lists the same `main.py` texts from the error side.

### 10.1 Start-Up and Shut-Down (Operators Only)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `WEBUI_SECRET_KEY is not set. It is a hard requirement when authentication is enabled.` (followed by start-method advice and a link to the upstream documentation) | Start-up stop | `backend/open_webui/env.py:780-788` | Sign-in is on and the secret key is empty | Report that the site is down | Escalate to the platform maintainer; see `configuration-environment-variables-bootstrap.md` section 10 |
| `Running migrations` | Log (info) | `backend/open_webui/config.py:65` | Every start with `ENABLE_DB_MIGRATIONS` on | None | Confirms the import phase reached migrations |
| `Error running migrations: {e}` | Log (error), then start-up stop | `backend/open_webui/config.py:76-78` | A database migration failed | Report that the site is down | Escalate at once with the time; the database may need attention |
| `An error occurred: {e}` | Log (error); start-up continues | `backend/open_webui/config.py:118`, `:129`, `:137`, `:145` | Copying a file from the front-end build into `STATIC_DIR` failed (for example permissions or a full disk) | Pictures or `custom.css` may be missing or out of date | Report to the maintainer (section 5.7) |
| `SAFE MODE ENABLED` | Console line | `backend/open_webui/main.py:280-281` | `SAFE_MODE` is on | Functions (custom models, filters, actions) are switched off | Ask the maintainer whether safe mode is intended |
| `v{VERSION} - building the best AI user interface.` (inside the start-up banner, with the commit and the upstream repository address) | Console banner | `backend/open_webui/main.py:320-335` | Every start unless `LOG_FORMAT` is `json` | None | Shows the running version (upstream number; the fork does not change it) |
| `Open WebUI v{VERSION} - building the best AI user interface.` | Console line | `backend/open_webui/main.py:336-341` | As above, when the console cannot print the banner's box characters | None | As above |
| `Invalid audit level: {AUDIT_LOG_LEVEL}. Error: {e}` | Intended as a log error; read from code, the call itself is expected to fail and stop start-up (section 5.4) | `backend/open_webui/main.py:797-801` | `AUDIT_LOG_LEVEL` is not `NONE`, `METADATA`, `REQUEST` or `REQUEST_RESPONSE` | Report that the site is down | Escalate: the maintainer corrects the variable; see section 14 |
| `Installing external dependencies of functions and tools...` | Log (info) | `backend/open_webui/main.py:387` | Every start (step C8) | None | A long gap after this line means pip is installing plugin packages |
| `ENABLE_PLUGINS is disabled, skipping tool and function dependencies.` | Log (info) | `backend/open_webui/utils/plugin.py:462` | `ENABLE_PLUGINS` is off | None | Informational |
| `Error installing requirements: {e}` | Log (error); start-up continues | `backend/open_webui/utils/plugin.py:483-484` | Reading or installing plugin requirements failed | A tool or function may fail when used | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `Users already exist, skipping admin creation` | Log (debug) | `backend/open_webui/utils/auth.py:645` | `WEBUI_ADMIN_EMAIL` and `WEBUI_ADMIN_PASSWORD` are set but accounts exist | None | Normal after the first start |
| `Creating admin account from environment variables: {email}` | Log (info); **contains the admin's email** | `backend/open_webui/utils/auth.py:648` | First start with the bootstrap variables and no accounts | None | Treat the log line as personal data |
| `Admin account created successfully: {email}` | Log (info); contains the email | `backend/open_webui/utils/auth.py:658` | As above, on success | None | As above |
| `Failed to create admin account from environment variables` | Log (error) | `backend/open_webui/utils/auth.py:661` | The account could not be written | No one can sign in on a fresh install | Escalate |
| `Error creating admin account: {e}` | Log (error) | `backend/open_webui/utils/auth.py:664` | As above, with the reason | As above | Escalate |
| `Failed to pre-fetch models at startup: {e}` | Log (warning) | `backend/open_webui/main.py:429` | `models.base_models_cache` is on and the model list could not be fetched | The first model list may load slowly | See `model-connections-openai-ollama-and-direct.md` |
| `Initializing tool servers...` | Log (info) | `backend/open_webui/main.py:449` | Tool-server connections exist | None | Informational |
| `Initialized {count} tool server(s)` | Log (info) | `backend/open_webui/main.py:452` | As above, on success | None | Informational |
| `Failed to initialize tool servers at startup: {e}` | Log (warning) | `backend/open_webui/main.py:454` | Tool-server descriptions could not be fetched | Tools may be missing until the next refresh | See `workspace-tools-tool-servers-mcp-and-terminals.md` |
| `Initialized {count} terminal server(s)` | Log (info) | `backend/open_webui/main.py:458` | As above, for terminal servers | None | Informational |
| `Failed to initialize terminal servers at startup: {e}` | Log (warning) | `backend/open_webui/main.py:460` | As above | Terminals may be unavailable | As above |
| `License data retrieval is still pending; continuing startup without it` | Log (warning) | `backend/open_webui/main.py:467` | Only with `LICENSE_KEY`: the lookup took over two seconds | None | Whether a licence key is used is **TO BE CONFIRMED** |
| `License data retrieval failed during startup: {e}` | Log (warning) | `backend/open_webui/main.py:469` | As above, the lookup failed | None | As above |
| `Error adding OAuth client for MCP tool server {server_id}: InvalidToken. Stored OAuth client data is invalid; reconnect this tool server.` | Log (error) | `backend/open_webui/main.py:648-652` | A stored MCP OAuth registration cannot be decrypted, for example after the secret key changed | That tool server asks to be reconnected | See `sso-oauth-oidc-and-scim.md` section 10 |
| `Error adding OAuth client for MCP tool server {server_id}: {e}` | Log (error) | `backend/open_webui/main.py:654-658` | Any other failure loading that registration | As above | As above |
| `Error updating models: {e}` | Log (error) | `backend/open_webui/main.py:696` | The document embedding or reranking model could not be set up | Document search may fail | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Event sink failed for {event}` | Log (exception); start-up continues | `backend/open_webui/events.py:1199-1202` | An event sink (for example an event webhook) failed for a system event | None | See `notifications-webhooks-events-and-banners.md` |
| `Using Redis for session` | Log (info) | `backend/open_webui/main.py:2664` | `ENABLE_STAR_SESSIONS_MIDDLEWARE` is on and the Redis session store was set up | None | Informational |
| `No Redis URL provided` | Not shown or logged | `backend/open_webui/main.py:2666` | Raised and caught at once when Redis sessions are off, to fall back to cookie sessions | None | None |
| `Created shared aiohttp session pool (limit={limit}, per_host={per_host}, dns_ttl={dns_ttl})` | Log (info) | `backend/open_webui/utils/session_pool.py:77-82` | First outbound call of the process; `unlimited` is printed for unset limits | None | Confirms the pool limits in effect (section 5.11) |
| `Closed shared aiohttp session pool` | Log (info) | `backend/open_webui/utils/session_pool.py:91` | Shut-down | None | Informational |
| `Frontend build directory not found at '{FRONTEND_BUILD_DIR}'. Serving API only.` | Log (warning) | `backend/open_webui/main.py:3076-3077` | No front-end build at the expected folder | The site shows `{"detail":"Not Found"}` instead of pages | Escalate after a deployment (section 11.3) |
| `Waiting for application startup.` | Log (uvicorn) | `.venv/lib/python3.12/site-packages/uvicorn/lifespan/on.py:48` | The import phase finished; the start-up routine begins | None | The time between this line and the next shows how long Phase C took |
| `Application startup complete.` | Log (uvicorn) | `.venv/lib/python3.12/site-packages/uvicorn/lifespan/on.py:62` | The start-up routine finished; serving begins | None | The site should answer from now on |
| `Application startup failed. Exiting.` | Log (uvicorn), then stop | `.venv/lib/python3.12/site-packages/uvicorn/lifespan/on.py:58-59` | An error escaped the start-up routine | Report that the site is down | Escalate with the traceback above this line |
| `Shutting down`, `Waiting for application shutdown.`, `Application shutdown complete.` | Log (uvicorn) | `.venv/lib/python3.12/site-packages/uvicorn/server.py:270`; `.venv/lib/python3.12/site-packages/uvicorn/lifespan/on.py:67`, `:76` | A stop or restart (section 5.10) | None | Correlate with deployment times |

### 10.2 Health and Readiness

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{"status": true}` | Healthy answer | `backend/open_webui/main.py:2965`, `:3006`, `:3013` | `/health` whenever the process serves; `/ready` and `/health/db` when their checks pass | None | A green `/health` alone proves little (section 5.5) |
| `Startup not complete` | Readiness (HTTP 503) | `backend/open_webui/main.py:2975-2980` | `/ready` answered before the start-up flag was set (section 5.5); logged as `Readiness check failed: startup not complete` | None | Not expected under uvicorn; if seen, escalate |
| `Database not ready` | Readiness (HTTP 503) | `backend/open_webui/main.py:2983-2990` | The database did not answer `SELECT 1`; logged as `Readiness check DB ping failed: {e}` | Users see errors or "Backend Required" | Escalate at once: everyone is affected |
| `Redis not ready` | Readiness (HTTP 503) | `backend/open_webui/main.py:2993-3004` | Redis is configured and did not answer; logged as `Readiness check Redis ping failed: {e}`, where `{e}` may be `Redis PING returned False` | Sign-out, live updates and multi-worker features misbehave | Escalate at once |
| `Internal Server Error` (`/health/db`) | Probe failure (HTTP 500, plain text) | `backend/open_webui/main.py:3009-3013` | The database did not answer; this endpoint has no error handling | As `Database not ready` | As `Database not ready` |

### 10.3 Request Handling and the Sign-In Gate

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Invalid WebSocket upgrade request` | Error (HTTP 400) | `backend/open_webui/utils/asgi_middleware.py:145-162` | A websocket handshake arrived without the upgrade headers, typically because a proxy strips them | Live updates do not arrive (section 11.6) | Escalate to whoever runs the proxy (**TO BE CONFIRMED**) |
| `AppHTTPMiddleware: rollback failed after downstream error` | Log (exception) | `backend/open_webui/utils/asgi_middleware.py:120-122`, `:208-217` | A request failed and the clean-up of its synchronous database work also failed | The request already failed | Report repeated occurrences with times |
| `AppHTTPMiddleware: post-request commit failed; response was already sent to client` | Log (exception) | `backend/open_webui/utils/asgi_middleware.py:225-228` | Saving a request's synchronous database work failed after the answer was sent | The person may have seen success for something that was not saved | Escalate with the time; database health check |
| `AppHTTPMiddleware: rollback failed after commit failure` | Log (exception) | `backend/open_webui/utils/asgi_middleware.py:229-232` | As above, and the roll-back also failed | As above | As above |
| `Internal Server Error` | Error (HTTP 500, plain text) | Starlette's server error handler (section 4.2) | Any error an endpoint did not handle | Retry once; report if it repeats | Escalate with time and address |
| `Not Found`, `Method Not Allowed` | Error (HTTP 404, HTTP 405) | FastAPI and Starlette defaults; `backend/open_webui/main.py:298-310` | An address matching no route while no build is mounted (404), or a non-`GET` request that fell through to the front-end mount (405) | None | Often a switched-off router (section 11.10) |
| `Not authenticated` | Error (HTTP 401) | `backend/open_webui/utils/auth.py:415-416` | No credential sent | Sign in again | Section 3.3 |
| `401 Unauthorized` | Error (HTTP 401) | `backend/open_webui/utils/auth.py:489-493`; `backend/open_webui/constants.py:69` | Token expired or unreadable (for example after the secret key changed) | Sign in again | Section 3.3; many at once suggests a secret-key change |
| `Invalid token` | Error (HTTP 401) | `backend/open_webui/utils/auth.py:448-453` | Token revoked (Redis only) | Sign in again | Section 3.3 |
| `Your session has expired or the token is invalid. Please sign in again.` | Error (HTTP 401) | `backend/open_webui/utils/auth.py:455-460`, `:511-516`; `backend/open_webui/constants.py:59` | The token's account no longer exists, or an API key matches no account | Sign in again; if it repeats, the account may have been deleted | Check the account exists (admin) |
| `User mismatch. Please sign in again.` | Error (HTTP 401) | `backend/open_webui/utils/auth.py:462-468` | Trusted-header sign-in: the proxy now names another person | Sign in again | Escalate if persistent |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 401 from the gatekeepers; 403 for a restricted API key) | `backend/open_webui/utils/auth.py:570-575`, `:626-630`, `:546-550`; `backend/open_webui/constants.py:70-72` | Role too low (`pending`, or a non-admin on an admin address), or an API key used outside its allowed addresses | Ask an admin whether the role is right | Check the role in `/admin/users` (read-only) |
| `Use of API key is not enabled in the environment.` | Error (HTTP 403) | `backend/open_webui/utils/auth.py:526-536`; `backend/open_webui/constants.py:81` | API keys are off, or the key's owner lacks the API-key permission | Ask an admin | See `authentication-and-sign-in.md` |
| `API rate limit exceeded` | Error (HTTP 429) | `backend/open_webui/routers/auths.py:818-822`, `:1642-1648`; `backend/open_webui/constants.py:87` | The rate-limit helper refused (section 5.12) | Wait three to four minutes, then try once | Many reports at once may mean a script or attack; escalate |

### 10.4 Top-Level Endpoints in `main.py` (Outside the Chat Pipeline)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Invalid token` (`/api/config`) | Not expected | `backend/open_webui/main.py:2238-2246` | Guarded by a decode that never raises (`backend/open_webui/utils/auth.py:246-251`), so an unreadable token is treated as signed out instead | None | None |
| `Failed to unload model on {count} node(s): {errors}` | Error (HTTP 500) | `backend/open_webui/main.py:1014-1018`; per node logged as `Failed to unload model on Ollama node {idx}: {e}` (`:1011`) | Admin **Unload** of an Ollama model failed on one or more servers | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `{detail}` (llama.cpp's own answer) | Error (llama.cpp's status) | `backend/open_webui/main.py:1051` | Unload on a llama.cpp connection that answered with an error | None | As above |
| `{e}` (unload) | Error (HTTP 500) | `backend/open_webui/main.py:1055-1057`; logged as `Failed to unload model via llama.cpp: {e}` | The llama.cpp unload call itself failed | None | As above |
| `Provider "{provider}" does not support model unloading` | Error (HTTP 400) | `backend/open_webui/main.py:1059-1062` | Unload on an OpenAI-compatible connection that is not llama.cpp; `{provider}` reads `default` when none is set | None | As above |
| `Model "{model_id}" not found` | Error (HTTP 404) | `backend/open_webui/main.py:1064` | Unload of a model in neither model list | Reload the model list | As above |
| `{e}` (event-webhook rule text) | Error (HTTP 400) | `backend/open_webui/main.py:2516-2517`, `:2550-2551` | Saving an event webhook that a rule in `backend/open_webui/events.py` refused | Correct the webhook | See `notifications-webhooks-events-and-banners.md` section 10 |
| `Webhook not found` | Error (HTTP 404) | `backend/open_webui/main.py:2540`, `:2573` | Editing or deleting an event webhook that no longer exists | Reload | As above |
| `Version update check is disabled, returning current version as latest version` | Log (debug) | `backend/open_webui/main.py:2596-2598` | `/api/version/updates` with the check off | None | Informational |
| `Version update check failed: {e}` | Log (warning) | `backend/open_webui/main.py:2611-2613` | GitHub could not be reached within one second, or answered oddly | Admins see `Could not check for updates` | Normal on networks without outbound access to GitHub |
| `Access denied. Only administrators can view usage statistics.` | Error (HTTP 403) | `backend/open_webui/main.py:2628-2633` | A non-admin asked for `/api/usage` while `ENABLE_PUBLIC_ACTIVE_USERS_COUNT` is off | None (the count is simply not shown) | See `evaluations-feedback-and-analytics.md` section 10 |
| `Internal Server Error` (usage) | Error (HTTP 500) | `backend/open_webui/main.py:2641-2643`; logged as `Error getting usage statistics: {e}` | The active-user count could not be read | None | As above |
| `{e}` (stop one task) | Error (HTTP 404); not expected | `backend/open_webui/main.py:2128-2134` | Admin stop of a task id; the function called reports problems as a message rather than raising | None | See `chat-completion-pipeline-and-generation-tasks.md` |
| `We could not find what you're looking for :/` | Error (HTTP 404) | `backend/open_webui/main.py:2167`, `:2171`; `backend/open_webui/constants.py:78` | **Stop** on a chat that is not the person's or does not exist | None | As above |
| `Finalized pending approval message.` | Notice (API answer) | `backend/open_webui/main.py:2174-2200` | **Stop** found no running task but an unfinished or paused reply, and closed it | None | As above |
| `Channel chats are not supported on this endpoint` | Error (HTTP 400) | `backend/open_webui/main.py:2077-2081` | The deprecated completed-hook or an Action called for a channel message | None (integration issue) | As above |
| `Something went wrong :/` (chat ownership) | Error (HTTP 404) | `backend/open_webui/main.py:2083-2087`; `backend/open_webui/constants.py:16-18` | The completed-hook or an Action named a chat the person does not own | None | As above |
| `{e}` (completed-hook, Action) | Error (HTTP 400) | `backend/open_webui/main.py:2104-2107`, `:2122-2125` | The outlet filters or the Action failed | Retry; report the Action's name | See `functions-pipes-filters-actions-and-pipelines.md` |
| `Schedule took too long to evaluate; simplify its recurrence rule.` | Error (HTTP 400) | Handler `backend/open_webui/main.py:515-517`; text `backend/open_webui/utils/recurrence.py:103` | Working out an automation's or event's repeat rule took too long | Simplify the repeat rule | See `automations-calendar-and-timers.md` section 10 |
| `Not Found` (tool-server sign-in) | Error page (HTTP 404) | `backend/open_webui/main.py:2780-2783` | Starting a tool-server OAuth sign-in whose registration cannot be loaded | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `Failed to re-register OAuth client` | Error page (HTTP 500) | `backend/open_webui/main.py:2785-2796`; preceded by the log `Detected invalid OAuth client {client_id}; attempting re-registration` | The stored registration failed its pre-check and re-registration failed | None | As above |
| `OAuth client unavailable after re-registration` | Error page (HTTP 500) | `backend/open_webui/main.py:2798-2804` | Re-registration reported success but the registration still cannot be loaded | None | As above |
| `OAuth client registration is still invalid after re-registration` | Error page (HTTP 500) | `backend/open_webui/main.py:2806-2810` | The new registration also failed the pre-check | None | As above |
| `Unable to locate MCP tool server configuration for client {client_id} during re-registration` | Log (warning) | `backend/open_webui/main.py:2693` | Re-registration for a tool server that is no longer configured | None | As above |
| `No stored OAuth client info for static client {client_id}` | Log (error) | `backend/open_webui/main.py:2713` | A statically configured tool-server client has no stored registration | None | As above |
| `OAuth client re-registration failed for {client_id}: InvalidToken. Stored OAuth client data is invalid; reconnect this tool server.` | Log (error) | `backend/open_webui/main.py:2734-2740` | The stored registration cannot be decrypted | The tool server must be reconnected | As above |
| `OAuth client re-registration failed for {client_id}: {e}` | Log (error) | `backend/open_webui/main.py:2741-2747` | Any other re-registration failure | None | As above |
| `Failed to persist updated OAuth client info for tool server {client_id}: {e}` | Log (error) | `backend/open_webui/main.py:2759-2760` | Saving the new registration failed | None | As above |
| `Re-registered OAuth client {client_id} for tool server` | Log (info) | `backend/open_webui/main.py:2768` | Re-registration succeeded | None | Informational |
| `Not Found` (back-channel logout) | Error (HTTP 404) | `backend/open_webui/main.py:2863-2864` | The identity provider called back-channel logout while it is switched off | None | See `sso-oauth-oidc-and-scim.md` |
| `File not found` | Error (HTTP 404) | `backend/open_webui/main.py:3038-3044` | A `/cache/` address outside the cache folder or for a missing file | None | Usually a stale link |

### 10.5 The Utilities Router

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{e}` (the formatter's own error, for example a parse error) | Error (HTTP 400), shown as a toast in the code editor | `backend/open_webui/routers/utils.py:37-38`; toast `src/lib/components/common/CodeEditor.svelte:187-190` | An admin pressed format on code that `black` cannot parse | Fix the syntax error the message points to | None |
| `Code execution is disabled` | Error (HTTP 403) | `backend/open_webui/routers/utils.py:43-47`; text `backend/open_webui/constants.py:125` | **Run** on a code block while code execution is off | Ask an admin whether code execution should be on | See `code-execution-and-interpreter.md` |
| `[ERROR: Code execution engine not supported]` | Error (HTTP 400) | `backend/open_webui/routers/utils.py:67-71`; formatting `backend/open_webui/constants.py:16-23` | Server-side run requested while the engine is not `jupyter` | None | As above |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` (database download) | Error (HTTP 401) | `backend/open_webui/routers/utils.py:77-78` | **Download Database** while `ENABLE_ADMIN_EXPORT` is off | None | The button is normally hidden in that case (`src/lib/components/admin/Settings/Database.svelte:123`) |
| `This feature is only available with SQLite databases.` | Error (HTTP 400), shown as a toast | `backend/open_webui/routers/utils.py:83-84`; `backend/open_webui/constants.py:97`; toast `src/lib/components/admin/Settings/Database.svelte:132-134` | **Download Database** on a PostgreSQL deployment | None | Expected on PostgreSQL |

### 10.6 Outbound Helpers

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Failed to mint {header}; falling back to plain user-info headers.` | Log (exception) | `backend/open_webui/utils/headers.py:66-74` | Signing the forwarded user-details header failed, so separate plain headers were sent instead | None | Report to the maintainer; personal data is still forwarded (section 5.11) |
| `Failed to resolve user groups for custom headers` | Log (exception) | `backend/open_webui/utils/headers.py:100-104` | A connection's custom header uses a group placeholder and the groups could not be read | The provider receives an empty group list | Report to the maintainer |

### 10.7 Front-End Texts Tied to This Layer

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{{webUIName}} Backend Required` (normally `MedIT GPT Backend Required`) | Full-page error | `src/routes/error/+page.svelte:25` | The page loaded but `/api/config` gave no usable answer (section 5.2) | Press **Check Again**; if it persists, report | Section 11.1 |
| `Oops! You're using an unsupported method (frontend only). Please serve the WebUI from the backend.` | Text on the same page | `src/routes/error/+page.svelte:29-31` | As above | As above | The text assumes a developer set-up; for MedIT GPT it usually means the backend or database is failing |
| `See readme.md for instructions` and `join our Discord for help.` (joined by `or`) | Links on the same page | `src/routes/error/+page.svelte:35-43` | As above | Do not follow; they point to the **upstream** project | Whether users should be pointed at upstream resources is **TO BE CONFIRMED** (ground truth) |
| `Check Again` | Button on the same page | `src/routes/error/+page.svelte:47-54` | As above | Reloads `/` | None |
| `Session expired. Please sign in again.` | Toast | `src/routes/+layout.svelte:931-949` | The token is about to expire, or an authenticated call answered 401 and a fresh session check also answered 401 | Sign in again | See `authentication-and-sign-in.md` |
| `A new version (v{{LATEST_VERSION}}) is now available.` | Toast (admins only) | `src/lib/components/layout/UpdateInfoToast.svelte:20-22` | A newer **upstream** release exists (section 5.9) | Admins may close it (hidden for 24 hours) | Upgrades are decided by the platform maintainer |
| `Update for the latest features and improvements.` | Link in the same toast | `src/lib/components/layout/UpdateInfoToast.svelte:24-26` | As above | Links to the upstream releases page | As above |
| `Checking for updates...`, `(latest)`, `Could not check for updates` | Version line in **Settings > About** and the admin **General** panel | `src/lib/components/chat/Settings/About.svelte:72-84`; `src/lib/components/admin/Settings/General.svelte:142-158` | While checking, when current, and when the check failed or is unreachable | None | `Could not check for updates` is normal without outbound access to GitHub |
| `Code formatted successfully` | Toast | `src/lib/components/common/CodeEditor.svelte:201` | Formatting succeeded (admins through the server, others in the browser) | None | None |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it cannot restart the service, change environment variables or settings,
or change roles. Every resolution below is guidance plus, where needed, an escalation to the
platform maintainer (contact route **TO BE CONFIRMED**). Two read-only checks are useful
throughout:

- **Open `/api/config` in a browser tab.** It needs no sign-in. A healthy answer is JSON that
  starts with `"status": true` and `"name": "MedIT GPT"` (section 5.3). An error page, plain
  `Internal Server Error`, or an HTML page from a proxy means the backend or something in front of
  it is failing.
- **If you have access to the service's monitoring (TO BE CONFIRMED)**, look at `/ready`: it names
  the failing dependency (`Database not ready`, `Redis not ready`), unlike `/health` (section 5.5).

Never ask a user for, or paste into a ticket, a token, API key, cookie value or secret.

### 11.1 "The page loads but says Backend Required"

**Symptom.** The browser shows `MedIT GPT Backend Required` with the line
`Oops! You're using an unsupported method (frontend only). Please serve the WebUI from the backend.`
and a **Check Again** button (`src/routes/error/+page.svelte:19-59`).

**Likely causes, in order.**
1. **`/api/config` answered with an error**, most often because the **database is unavailable**:
   the endpoint reads settings and accounts on every call, an unhandled database error becomes a
   plain-text HTTP 500, and the front end cannot read that as JSON
   (`backend/open_webui/main.py:2247-2308`; `src/lib/apis/index.ts:1478-1487`).
2. **The backend stopped or is restarting** while the browser still had the page (an open tab
   that reloads, or a page kept by a cache or proxy in front of the service, **TO BE CONFIRMED**).
3. **Something in front of the service answers `/api/...` differently from `/`** (a proxy rule,
   a firewall page, a sign-in portal that does not redirect). A sign-in proxy that redirects is
   handled separately: the page reloads instead of showing this screen
   (`src/routes/+layout.svelte:1242-1248`).
4. A development set-up where the front end runs without the backend, which is what the
   message's own wording assumes (`vite.config.ts:6`, `:31-55`).

**Diagnostic steps** (read-only).
1. Ask whether it happens for everyone or one person, and note the time.
2. Open `/api/config` in a new tab and note the status (JSON, `Internal Server Error`, a proxy
   page, or nothing).
3. If `/api/config` shows healthy JSON for you but not for the user, ask the user to press **Check
   Again**, then to try a private window (which rules out a stale page or cached files).
4. If available, check `/ready`.

**Resolution.** If it affects everyone, tell users the service is temporarily unavailable. If
`/api/config` is healthy, **Check Again** usually recovers the page.

**Escalation.** Send the platform maintainer the time, how many users are affected, what
`/api/config` returned (status and first words, never cookies), and the `/ready` answer if known.
`Database not ready` is the most urgent case.

### 11.2 "It's stuck on the loading splash"

**Symptom.** The MedIT GPT splash picture stays on screen and the application never appears.

**Likely causes, in order.**
1. **The service is starting.** During start-up nothing is served (section 5.4); with several
   workers or the development reloader the browser's requests wait instead of failing. Start-up
   can take minutes when stored tools and functions declare Python packages that pip installs
   first (`backend/open_webui/main.py:385-388`).
2. **One of the start-up calls in the browser never finishes.** The splash is removed only after
   the configuration, language and session check have completed (section 5.2, step 6;
   `src/routes/+layout.svelte:1322-1349`); a request that hangs (for example a slow database or a
   proxy that holds the connection) holds the splash.
3. **A script failed to load** before the start-up code ran: a code file that no longer exists
   after a new deployment answers a real 404 (section 5.8), or a browser extension or network
   filter blocks a file. `/static/loader.js` and `/static/custom.css` load first on every page
   (`src/app.html:38-39`).

**Diagnostic steps** (read-only).
1. Ask the user to reload once, then to try a private window and another browser.
2. Check whether others are affected and whether a deployment or restart is in progress.
3. Open `/api/config` and, if available, `/ready`.

**Resolution.** If a deployment or restart is underway, ask users to wait a few minutes and
reload. If only one browser is affected and a private window works, a reload with a cleared cache
(or removing the blocking extension) usually fixes it.

**Escalation.** Time, browser and version, whether a private window helps, and the `/api/config`
and `/ready` answers. If the start-up is slow every time, ask the maintainer to review plugin
requirements and the start-up log between
`Installing external dependencies of functions and tools...` and `Application startup complete.`.

### 11.3 "The site doesn't load at all after a restart or update"

**Symptom.** The address gives a browser connection error, a proxy or gateway error page, or a
bare `{"detail":"Not Found"}` page.

**Likely causes, in order.**
1. **Start-up stopped with an error**: a missing secret key, a failed migration, a configuration
   value that fails a check, or a mistyped `AUDIT_LOG_LEVEL` (section 5.4 phase B; section 10.1).
2. **Start-up is still running** (section 11.2, cause 1).
3. **The front-end build is missing** from the image or folder: the API runs but every page
   answers `{"detail":"Not Found"}`, and the log shows
   `Frontend build directory not found at '{FRONTEND_BUILD_DIR}'. Serving API only.`
   (`backend/open_webui/main.py:3076-3077`).

**Diagnostic steps.** Note the exact page shown and the time; check `/health` (no answer means the
process is not serving) and, if available, `/ready`.

**Resolution.** Inform users of the outage; nothing for tier 1 to change.

**Escalation.** Send the time, the exact error page text, the `/health` and `/ready` answers, and
whether a deployment or configuration change happened just before (the variable name only, never
its value). Ask the maintainer to compare the first error in the start-up log with section 10.1 and
`configuration-environment-variables-bootstrap.md` section 10.

### 11.4 "The health check passes but users can't sign in"

**Symptom.** Monitoring shows `/health` green, yet people cannot sign in or are thrown out at once.

**Likely causes, in order.**
1. **`/health` checks nothing but the process** (`backend/open_webui/main.py:2963-2965`). The
   database may be down: sign-in needs it, and `/ready` would answer `Database not ready`.
2. **The secret key changed** (for example a recreated container that generated a new key, or
   several instances started with different keys): every existing token becomes unreadable, so calls answer
   `401 Unauthorized` and the page shows `Session expired. Please sign in again.` (section 3.3;
   `CLAUDE.md` "Deployment"; `configuration-environment-variables-bootstrap.md` section 11.4).
3. **Redis is configured but down**: `/ready` answers `Redis not ready`; single sign-on sessions
   stored in Redis, live updates and multi-worker coordination misbehave (section 5.5).
4. **Sign-in throttling**: after 15 attempts in about three minutes for one email the answer is
   `API rate limit exceeded` (section 5.12).
5. **A sign-in method is switched off or its provider is failing** (password sign-in, LDAP or
   single sign-on); see `authentication-and-sign-in.md` and `sso-oauth-oidc-and-scim.md`.
6. The person **can** sign in but is `pending` and sees the activation overlay; that is a role
   question, not an outage (ground truth).

**Diagnostic steps** (read-only).
1. Ask for the exact message on screen and the sign-in method used (password, LDAP, single sign-on).
2. Check whether one person or everyone is affected, and the time it started.
3. If available, check `/ready`; open `/api/config` to confirm the backend answers.

**Resolution.** For a single person hitting the rate limit, advise waiting three to four minutes.
For everyone, report an outage.

**Escalation.** Time, scope, sign-in method, exact text, `/ready` answer, and whether a deployment
happened. Mention if many users report `Session expired. Please sign in again.` at the same moment
(points to a secret-key change).

### 11.5 "Static pictures show the upstream logo"

**Symptom.** The favicon, splash, app icon, sign-in picture or installed-app icon shows the
upstream Open WebUI artwork instead of the U of T pictures.

**Likely causes, in order.**
1. **The front-end build in use was not made from the `uoft` branch** (an upstream image, a build
   from `main`, or a stale `build/` folder). At every start-up the build's `static/` files are
   copied over `STATIC_DIR`, so the build wins over the fork's committed copies (section 5.7;
   `backend/open_webui/config.py:100-145`).
2. **The legacy `CUSTOM_NAME` variable is set**: start-up downloads a logo and splash from the
   upstream service and writes them over `favicon.png` and `splash.png`, and also changes the
   product name (`backend/open_webui/config.py:187-223`).
3. **`STATIC_DIR` or `FRONTEND_BUILD_DIR` point somewhere else**, or the backend runs from the
   upstream Python package (`open-webui serve`), whose own `frontend` folder is used
   (`backend/open_webui/env.py:252-257`).
4. **The browser or the installed app kept old pictures**: icons and the manifest (whose icons are
   `/static/logo.png`, `backend/open_webui/main.py:2895-2911`) are often cached; an installed app may
   need reinstalling.
5. A picture the fork did not replace (the fork changed the files listed in ground truth; anything
   else under `static/` is upstream).

**Diagnostic steps** (read-only).
1. Ask which picture and where (tab icon, splash, sign-in page, installed app).
2. Open `/static/favicon.png` and `/static/logo.png` directly in a private window and compare.
3. Check whether the product name also changed (points to `CUSTOM_NAME`, cause 2).

**Resolution.** For one person, a private window or clearing the site's cached files usually
shows the right pictures; an installed app may need removing and reinstalling. If the direct
`/static/...` addresses show upstream artwork in a private window, it is a deployment issue.

**Escalation.** Send the maintainer the addresses checked, what they showed, and the time of the
last deployment. Ask them to confirm the image was built from `uoft` and that `CUSTOM_NAME` is not
set. The licence position on branding is covered in ground truth.

### 11.6 "Chats don't update live" or "the answer only appears after a refresh"

**Symptom.** Replies, titles or notifications appear only after reloading; the browser console
(if the user can see it) shows websocket errors.

**Likely causes, in order.**
1. **A proxy in front does not pass websocket upgrades**: the handshake reaches the server
   without upgrade headers and is refused with HTTP 400 `Invalid WebSocket upgrade request`
   (`backend/open_webui/utils/asgi_middleware.py:145-162`). The front end asks for a pure
   websocket connection unless the server switched websockets off
   (`src/routes/+layout.svelte:166-175`).
2. **Several workers or instances without Redis**: events raised in one process do not reach a
   browser connected to another (`CLAUDE.md` "Deployment"; see `websockets-realtime-and-redis.md`,
   planned).
3. **Redis down** while `WEBSOCKET_MANAGER` is `redis` (section 5.5).

**Diagnostic steps.** Ask whether reloading shows the missing content; check whether others are
affected; check `/ready` if available.

**Resolution.** Reloading the page shows saved content; tell users this is a service-side issue.

**Escalation.** Time, scope, and whether it started after a proxy or deployment change. Name the
`Invalid WebSocket upgrade request` message to the maintainer if they can search the logs.

### 11.7 "After an update, parts of the page are broken until I refresh"

**Symptom.** After a deployment, an already-open tab shows blank panels, buttons that do nothing,
or errors when opening a page; a reload fixes it.

**Likely causes, in order.**
1. **The tab is still running the previous build** and asks for code files whose names changed;
   missing `.js` files answer a real 404 by design (section 5.8;
   `backend/open_webui/main.py:303-306`).
2. **The automatic reload did not trigger.** When the websocket reconnects after a restart, the
   page compares `/api/version` (version and `deployment_id`) with what it loaded, and reloads
   itself only when one of them changed (`src/routes/+layout.svelte:184-215`). The fork keeps the
   upstream version number (section 5.9), so a redeploy of the same version reloads open tabs
   only if `DEPLOYMENT_ID` changes between deployments; whether production sets it is
   **TO BE CONFIRMED**.

**Diagnostic steps.** Ask whether a reload fixes it and when the page was first opened; check the
deployment time.

**Resolution.** Ask the user to reload the page (and close other open tabs of the site).

**Escalation.** Only if a reload does not help: send the time, the page address and a screenshot.
If this happens after every deployment, suggest to the maintainer that each deployment set a new
`DEPLOYMENT_ID`.

### 11.8 "Some features are missing although I'm signed in"

**Symptom.** A signed-in person does not see features colleagues see (for example Notes, Channels,
web search or image generation switches), while their role is `user` or `admin`.

**Likely causes, in order.**
1. **The feature is switched off, or the person's groups lack the permission**: the switches come
   from `/api/config` and permissions from the person's groups (section 5.3; see
   `users-groups-roles-and-permissions.md`).
2. **The browser did not keep the `token` cookie.** The second `/api/config` call relies on that
   cookie, not on a header, to receive the signed-in variant; without it the answer has only the
   sign-in features, so most switches read as off (`src/lib/apis/index.ts:1469-1477`;
   `src/routes/+layout.svelte:1286-1293`; `backend/open_webui/main.py:2232-2236`). This can happen when the
   browser blocks cookies for the site. Whether the cookie flags set by `WEBUI_AUTH_COOKIE_SECURE`
   and `WEBUI_AUTH_COOKIE_SAME_SITE` (`backend/open_webui/env.py:769-778`) can also cause it in
   production is **TO BE CONFIRMED** (section 14).
3. **The person is `pending`**: they receive the feature switches but not the defaults, and see the
   activation overlay (section 5.3).

**Diagnostic steps** (read-only).
1. Confirm the person's role and groups (an admin can look in `/admin/users`).
2. Ask whether a private window or another browser shows the features.
3. Ask whether the browser blocks cookies for the site.

**Resolution.** If another browser works, advise allowing cookies for the site. If the feature is
off or a permission is missing, it is an admin decision; tier 1 does not change it.

**Escalation.** Send the admin or maintainer the person's role (not their token), which features
are missing, and whether another browser shows them.

### 11.9 "It says a new version is available"

**Symptom.** An admin sees `A new version (v{{LATEST_VERSION}}) is now available.`, or the version
line shows `(v{latest} available!)`.

**Likely causes.** The check compares the running version with the latest **upstream** Open WebUI
release on GitHub (section 5.9; `backend/open_webui/main.py:2594-2613`). It does not know about
MedIT GPT builds, so the notice appears whenever upstream releases, whatever the fork's plans.

**Diagnostic steps.** None needed; note the versions shown.

**Resolution.** Explain that the notice refers to the upstream project and that upgrades of
MedIT GPT are scheduled by the platform maintainer (**TO BE CONFIRMED**). The admin can close
the toast (it stays hidden for 24 hours) or turn off **Toast Notifications for New Updates** in
**Settings > Interface** for themselves.

**Escalation.** Optional: forward the version numbers to the maintainer if an upgrade is wanted.
`Could not check for updates` on its own is normal where the server cannot reach GitHub.

### 11.10 "An integration gets the web page, or 'Method Not Allowed', instead of data"

**Symptom.** A script, monitoring check or external tool calling an `/api/...` address receives
HTML (the application page) with HTTP 200, or HTTP 405 `Method Not Allowed`, instead of JSON.

**Likely causes, in order.**
1. **The router is not mounted**: analytics (`ENABLE_ADMIN_ANALYTICS` off) or SCIM (`ENABLE_SCIM`
   off, the code default) (`backend/open_webui/main.py:878-879`, `:886-887`). Unmatched addresses
   fall through to the front-end mount: `GET` returns the page, other methods return 405
   (section 2.1).
2. **A wrong address**: a typing error, a missing `/v1`, or `/api/v1/calendar` instead of
   `/api/v1/calendars` (section 2.2).
3. **The wrong method** for an address that exists, which also falls through to the front-end
   mount.

**Diagnostic steps.** Compare the address with the tables in sections 2.2 and 2.3; ask which
method the integration uses.

**Resolution.** Correct the address or method. Switching a router on is a maintainer decision.

**Escalation.** Send the full address (without any key or token), the method and the status
received.

### 11.11 "It says I don't have permission to access this resource"

**Symptom.** A toast or API answer reads
`You do not have permission to access this resource. Please contact your administrator for assistance.`,
often with HTTP 401.

**Likely causes, in order.**
1. **The account is `pending`**: every address that needs a verified user refuses it (section 3.1).
2. **A non-admin opened an admin-only address or button** (section 3.1).
3. **An API key was used on an address outside the allowed list** (HTTP 403 in that case,
   section 3.2).
4. A feature permission check inside an endpoint uses the same text with HTTP 403; see the
   feature's document.

**Diagnostic steps.** Ask what the person was doing and their role (shown in the user menu; an
admin can confirm it in `/admin/users`). Note that 401 here does **not** mean the session expired
(section 3.1).

**Resolution.** Explain that access depends on the role and permissions an admin assigns. Tier 1
does not change roles.

**Escalation.** Send the admin the person's name, role, the action attempted, the address if
known, and the time.

## 12. Local Customisations

**The code in scope matches upstream v0.11.4.** A read-only `git diff main...uoft` over
`backend/open_webui/main.py`, the eight helper modules in scope and every file in
`backend/open_webui/routers/` shows no change, and `git diff` shows no uncommitted change in them
(checked 2026-10-11). The fork's changes reach this layer only through values and files it
serves:

| Fork change | Where this layer surfaces it | Source |
|---|---|---|
| Default `WEBUI_NAME` is `MedIT GPT` with no " (Open WebUI)" suffix | The `name` in `/api/config`, the `/manifest.json` name and description, the `/opensearch.xml` names, and the `{{webUIName}} Backend Required` page (which uses the front-end default `MedIT GPT` until a configuration arrives) | `backend/open_webui/env.py:951`; `backend/open_webui/main.py:538`, `:2313`, `:2889-2891`, `:2928-2929`; `src/lib/constants.ts:7`; `src/lib/stores/index.ts:14` |
| U of T favicons, logo, splash and app icons in `static/static/` and `backend/open_webui/static/` | `/static/...`; the copy that is served comes from the front-end build's `static/` folder, refreshed at each start-up (section 5.7) | `git diff --stat main...uoft -- static/ backend/open_webui/static/`; `backend/open_webui/config.py:100-145` |
| `static/opensearch.xml` renamed to MedIT GPT | Overridden in production by the generated `/opensearch.xml` route; the static file matters only to the development server | `static/opensearch.xml`; `backend/open_webui/main.py:2920-2936` |
| `site.webmanifest` renamed in both static folders | Served at `/static/site.webmanifest` but referenced by nothing in `src/` or the backend (a search for `site.webmanifest`); browsers use the generated `/manifest.json` | `backend/open_webui/static/site.webmanifest`; `src/app.html:30` |
| Splash picture changed to `splash-dark.png` in the page shell | Loaded from `/static/` during the first page load (section 5.2) | `src/app.html:160-170` |

Upgrade notes for the maintainer:

- Because no file in scope carries a fork edit, upstream changes to `main.py`, the middleware and
  the routers should merge without conflicts. The licence comments that guard the "Open WebUI"
  strings in `main.py` (the API title, the banner, the manifest, the search descriptor) are
  upstream text and stay as they are (`CLAUDE.md` "Conventions").
- After every upgrade, rebuild the front end from `uoft` so that the build's `static/` folder, which
  overwrites `STATIC_DIR` at start-up, carries the U of T pictures (section 11.5).
- The version number stays the upstream one, so the update notice keeps tracking upstream releases
  (section 5.9) and open tabs reload after a deployment only if `DEPLOYMENT_ID` changes
  (section 11.7).

## 13. Source File Index

**In scope, read in full or in the parts that matter here.**

| File | What it contributes |
|---|---|
| `backend/open_webui/main.py` | The app, `lifespan`, `app.state`, middleware, router mounts, the 39 top-level endpoints, health and readiness, static and front-end mounts (chat-pipeline internals at `:1108-1885` only skimmed for signatures) |
| `backend/open_webui/utils/asgi_middleware.py` | `AppHTTPMiddleware`: websocket upgrade check, credential pick-up, legacy redirects, `X-Process-Time` and security headers, synchronous session commit and roll-back |
| `backend/open_webui/utils/security_headers.py` | The 14 optional security headers and their fallbacks |
| `backend/open_webui/utils/headers.py` | Bearer helpers, forwarded user-detail headers, custom-header placeholders |
| `backend/open_webui/utils/rate_limit.py` | The bucketed rate limiter |
| `backend/open_webui/utils/json_response.py` | Optional `orjson` request and response JSON |
| `backend/open_webui/utils/json_codec.py` | The application-wide JSON codec switch |
| `backend/open_webui/utils/session_pool.py` | The shared outbound HTTP client |
| `backend/open_webui/utils/sanitize.py` | Clean-up of model-written code before execution (removes terminal colour codes and Markdown fences); used by `backend/open_webui/tools/builtin.py:71` and `backend/open_webui/utils/middleware.py:132`, and not an input-sanitising or security filter |
| `backend/open_webui/routers/utils.py` | The utilities router (section 2.4) |
| `backend/open_webui/routers/*.py` (all 31) | Each file's `APIRouter()` definition and its route decorators (searched, not read line by line) |

**Read for context outside the scope.**

| File | Why |
|---|---|
| `backend/open_webui/utils/auth.py` | The gatekeepers, token decoding, API-key checks, the bootstrap admin |
| `backend/open_webui/env.py` | Version, changelog parsing, secret-key check, directory defaults, switches in section 7.1 |
| `backend/open_webui/config.py` | Import-time migrations, the `STATIC_DIR` rewrite, `CUSTOM_NAME`, `CORS_ALLOW_ORIGIN`, analytics and export switches |
| `backend/open_webui/constants.py` | Message texts |
| `backend/open_webui/events.py` | System events and `publish_event` |
| `backend/open_webui/utils/plugin.py` | Plugin requirement installation at start-up |
| `backend/open_webui/utils/redis.py` | Redis client creation |
| `backend/open_webui/utils/logger.py` | Why `logger.error` in `main.py` is expected to fail (section 5.4) |
| `backend/open_webui/utils/telemetry/setup.py`, `backend/open_webui/utils/telemetry/metrics.py` | OpenTelemetry layers |
| `backend/open_webui/socket/main.py` | `MODELS`, the pool clean-up loops, the Redis event listener, `get_models_in_use` |
| `backend/open_webui/tasks.py` | Redis task listener and heartbeat |
| `backend/open_webui/utils/automations.py` | The scheduler loop and its intervals |
| `backend/open_webui/routers/auths.py` | The `token` cookie, the session-user call, the two rate-limited endpoints |
| `backend/open_webui/routers/notifications.py` | Example of an endpoint-level 403 |
| `backend/open_webui/utils/misc.py` | The Gravatar address |
| `backend/open_webui/utils/recurrence.py` | The recurrence time-out text |
| `backend/start.sh`, `backend/dev.sh`, `Dockerfile` | How uvicorn is started; the image layout and health check |
| `vite.config.ts`, `svelte.config.js` | Development proxy; build output, fallback page and version polling |
| `src/app.html` | Page shell, splash and static file references |
| `src/routes/+layout.svelte` | First page load, socket set-up and version-change reload, expired-session handling |
| `src/routes/(app)/+layout.svelte` | Update check and What's New for admins |
| `src/routes/error/+page.svelte` | The "Backend Required" page |
| `src/lib/apis/index.ts`, `src/lib/apis/auths/index.ts` | `getBackendConfig` and how the token is sent |
| `src/lib/constants.ts`, `src/lib/stores/index.ts` | Base addresses and the default product name |
| `src/lib/components/layout/UpdateInfoToast.svelte`, `src/lib/components/ChangelogModal.svelte`, `src/lib/components/chat/Settings/About.svelte`, `src/lib/components/admin/Settings/General.svelte`, `src/lib/components/common/InterfaceSettings.svelte`, `src/lib/utils/index.ts` | Version and changelog display |
| `src/lib/components/common/CodeEditor.svelte`, `src/lib/components/chat/Settings/Account/UserProfileImage.svelte`, `src/lib/components/admin/Settings/Database.svelte`, `src/lib/components/chat/Messages/CodeBlock.svelte` | Callers of the utilities router |
| `CHANGELOG.md`, `package.json` | Changelog format and version |

**Framework code consulted (installed packages, not part of the repository's source).**

| File | Why |
|---|---|
| `.venv/lib/python3.12/site-packages/starlette/applications.py` | Middleware order |
| `.venv/lib/python3.12/site-packages/starlette/staticfiles.py` | Static-file behaviour (methods, `html` mode, 404) |
| `.venv/lib/python3.12/site-packages/fastapi/applications.py`, `.venv/lib/python3.12/site-packages/fastapi/routing.py`, `.venv/lib/python3.12/site-packages/fastapi/exception_handlers.py` | Middleware stack, dependency handling, JSON error bodies |
| `.venv/lib/python3.12/site-packages/uvicorn/server.py`, `.venv/lib/python3.12/site-packages/uvicorn/main.py`, `.venv/lib/python3.12/site-packages/uvicorn/lifespan/on.py` | When the port opens, start-up and shut-down order and log lines |

## 14. Open Questions

### 14.1 Production Values (All TO BE CONFIRMED)

- The production host name, how the service is run (Docker image, `start.sh`, or
  `open-webui serve`), how many workers and instances, and whether a proxy or load balancer sits
  in front.
- Which probe the load balancer or orchestrator uses (`/health` or `/ready`), and whether tier 1
  has any view of it.
- Whether the proxy passes websocket upgrades, caches pages or static files, adds security
  headers, or applies its own rate limits.
- The live values of every environment variable in section 7.1, in particular `ENV`,
  `CORS_ALLOW_ORIGIN`, the security-header variables, `AUDIT_LOG_LEVEL`,
  `ENABLE_STAR_SESSIONS_MIDDLEWARE`, `REDIS_URL`, `WEBSOCKET_MANAGER`, `DEPLOYMENT_ID`,
  `ENABLE_VERSION_UPDATE_CHECK`, `OFFLINE_MODE`, `ENABLE_PUBLIC_ACTIVE_USERS_COUNT`,
  `ENABLE_ADMIN_EXPORT`, `ENABLE_ADMIN_ANALYTICS`, `ENABLE_SCIM`,
  `ENABLE_FORWARD_USER_INFO_HEADERS`, the `AIOHTTP_*` pool and time-out values, `ENABLE_ORJSON`,
  `CUSTOM_NAME`, `EXTERNAL_PWA_MANIFEST_URL`, `WEBUI_URL` and `LICENSE_KEY`.
- Whether any connection uses custom headers with user placeholders (section 5.11).
- Who decides and schedules upgrades to new upstream releases, and the support contact route for
  escalations (ground truth: none exists in the repository).
- Whether the cookie flags (`WEBUI_AUTH_COOKIE_SECURE`, `WEBUI_AUTH_COOKIE_SAME_SITE`) can make
  browsers drop the `token` cookie in production, which would produce section 11.8's symptom;
  browser cookie behaviour cannot be established from the repository.

### 14.2 Security-Sensitive Items Referred

Security-sensitive: refer to the platform maintainer and U of T Information Security
(security.utoronto.ca). The following were not assessed and are deliberately described only at
the level of what users and admins see:

- whether the configured security headers and the CORS settings are adequate for production;
- which of the public addresses (the probes, `/api/config`, `/api/version`, `/api/changelog`)
  should be reachable from outside the service's network;
- token handling beyond the user-visible refusal texts in section 3.3;
- the raw database download (`/api/v1/utils/db/download`), which exports every account and chat
  and therefore personal and possibly health information; its use and governance are also a
  question for the Privacy Office (privacy.utoronto.ca);
- the forwarding of people's names, emails and roles to model and tool providers (section 5.11),
  also a Privacy Office question.

### 14.3 Findings, Contradictions and Limits of This Research

1. **`AUDIT_LOG_LEVEL` with an unknown value is expected to stop start-up** (read from code, not
   run): `main.py` calls `logger.error(...)` on the imported module `open_webui.utils.logger`,
   which defines no `error` attribute (`backend/open_webui/main.py:211`, `:797-801`;
   `backend/open_webui/utils/logger.py:1-27`). This **contradicts**
   `configuration-environment-variables-bootstrap.md` sections 7.6 and 10, which say the value is
   logged and auditing stays off. Not a ground-truth fact; recommend the maintainer confirm in a
   test environment and record the outcome in `tools/VERIFICATION.md`.
2. **`Startup not complete` is not expected under uvicorn.** uvicorn runs the start-up routine
   before it serves (`.venv/lib/python3.12/site-packages/uvicorn/server.py:103-106`), so during a
   normal start probes get no answer (one worker) or wait (several workers or the reloader). The
   row in `error-messages-backend-identity-admin-and-platform.md` section 10.18 that calls this
   answer "normal while the server starts", the same document's list item "While the server is
   starting, `/ready` answers HTTP 503" (its line 275), and the start-up row and diagnostic step in
   `configuration-environment-variables-bootstrap.md` sections 10 and 11.1 appear inaccurate for
   the installed server; `CLAUDE.md`
   ("`/ready` returns 503 until startup finishes") is literally true but the 503 is not observable
   in that window. The text would be served only if the application ran without its start-up
   routine.
3. **Cookie deletion on a refused session.** `get_current_user` deletes the `token` and single
   sign-on cookies on the response object it was given before re-raising
   (`backend/open_webui/utils/auth.py:494-506`). In the installed FastAPI, headers set on that
   object are merged only into successful responses (`.venv/lib/python3.12/site-packages/fastapi/routing.py:457-467`,
   `:619`, `:652`, `:672`, `:718`), and error responses are built fresh from the exception
   (`.venv/lib/python3.12/site-packages/fastapi/exception_handlers.py:11-17`). Whether browsers
   actually receive the deletion is therefore doubtful; `authentication-and-sign-in.md` section 5.8
   states that every 401 deletes the cookie. Needs a live check by the maintainer.
4. **The shared HTTP client's docstring is out of date**: it promises 100 connections and 30 per
   host by default, but unset variables mean no limit (section 5.11).
5. **An API-only start empties `STATIC_DIR`** (read from code, not run): the top-level files are
   deleted even when no build exists to copy from (`backend/open_webui/config.py:100-118`).
6. **The changelog parser** stops the import if a second-level heading in `CHANGELOG.md` lacks
   ` - ` (`backend/open_webui/env.py:202-204`); all 172 headings in v0.11.4 match, so this matters
   only if the file is edited.
7. **Not traced:** where the OpenTelemetry trace instrumentation sits in the middleware stack (it
   is added by an external library); what SvelteKit does when its 60-second version poll detects a
   new build (no handler was found in `src/` for the `updated` signal); the Docker health check's
   interval (Docker's default, as the Dockerfile sets none).
8. **Coverage limits:** the 31 router files were searched for their router definitions and route
   decorators but not read line by line (their content belongs to the feature documents in
   section 2.2); chat-pipeline code in `main.py` (`:1108-1885`) was read only for endpoint
   signatures; `backend/data/` and `.env` files were not opened.
9. **Planned documents cited by name** that did not exist when this was written:
   `public-api-and-integrations.md`, `websockets-realtime-and-redis.md`,
   `background-processes-and-scheduling.md`, `deployment-operations-and-logging.md`,
   `frontend-architecture-routes-stores-and-i18n.md`, `database-schema-identity-chats-and-config.md`,
   `database-schema-content-and-collaboration.md`.
10. **Correction to this document's own At a Glance** (written by the previous researcher): the
    HTTP middleware picks up the credential but does not check it, and under the installed uvicorn
    the probes do not answer before start-up finishes; both bullets are corrected in place and
    marked.
11. **No contradiction with `tools/ground-truth.md` was found.** `CLAUDE.md`'s start-up order and
    mount list match the code (`backend/open_webui/main.py:345-472`, `:843-887`).
