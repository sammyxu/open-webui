# Public API, API Keys and Integrations

## At a Glance

- *Provisional; refined at the end of research.* External scripts and tools call MedIT GPT over
  the same HTTP API the browser uses, with a site-relative base URL (`/api/...`) and an
  `Authorization: Bearer` header carrying either a session token (JWT) or a personal API key.
- `/api/chat/completions` and `/api/v1/chat/completions` are OpenAI-compatible; `/api/v1/messages`
  and `/api/message` are Anthropic-compatible and are translated to the OpenAI shape internally.
- API keys are personal (one per user), are created under **Settings > Account**, and only work
  when an administrator has enabled them globally and the user's role or group has the API keys
  permission.
- Administrators can restrict API keys to a list of allowed endpoints.

## 1. Purpose and Who Uses It

MedIT GPT has no separate "public API product". The web page itself talks to the server over an
HTTP API, and any program that presents a valid credential can call the same addresses. A few of
those addresses deliberately imitate two well-known AI services so that tools written for them can
be pointed at MedIT GPT instead:

- **OpenAI-compatible addresses**: chat completions, model list and embeddings
  (`backend/open_webui/main.py:897-899`, `:1072-1073`, `:1108-1109`; the source labels the `/api/v1`
  versions "Experimental: Compatibility with OpenAI API").
- **Anthropic-compatible addresses**: the Messages API and its token counter
  (`backend/open_webui/main.py:1933-1934`, `:2002-2003`). Requests are converted to the OpenAI shape,
  run through the normal chat pipeline and converted back (`backend/open_webui/main.py:2009-2021`;
  `backend/open_webui/utils/anthropic.py:138-469`).

A call made with someone's credential runs **as that person**: the same model access rules,
permissions, filters, knowledge access checks and logging apply as if they had typed the request in
the browser (section 3). What changes is that a plain API call has no browser connection, so the
answer comes back in the HTTP response instead of over the live websocket, nothing is saved as a
chat unless the caller asks, and the built-in tools are not offered (section 5.4).

| Who | What they do here | Evidence |
|---|---|---|
| People with scripts, notebooks, desktop or editor plug-ins, or other services | Call MedIT GPT with a personal API key (or, for admins, a copied session token) | `backend/open_webui/utils/auth.py:393-436`; `src/lib/components/chat/Settings/Account.svelte:386-462` |
| Admins | Switch API keys on or off for the whole site, grant the **API Keys** permission, optionally limit which addresses keys may call | `src/lib/components/admin/Settings/Authentication.svelte:188-230`; `src/lib/components/admin/Users/Groups/Permissions.svelte:959-975` |
| Tier 1 support | Triage "my script fails" tickets: read the status code and `detail` text, check whether the person should have a key, escalate | Sections 10 and 11 |
| Platform maintainer | Owns the environment-only settings (custom API-key header, `ENV`, timeouts, outlet filters for API callers) | Section 7 |

In code, API keys are **off by default** (`ENABLE_API_KEYS`, `backend/open_webui/config.py:2454`)
and the per-user permission is off by default (`USER_PERMISSIONS_FEATURES_API_KEYS`,
`backend/open_webui/config.py:1924`). Whether MedIT GPT production has API keys switched on, and the
policy on who may hold one, are **TO BE CONFIRMED** (section 14).

Neighbouring documents: signing in and the key's place in the account screen
(`authentication-and-sign-in.md`), what happens inside a chat turn
(`chat-completion-pipeline-and-generation-tasks.md`), provider connections and the `/ollama` and
`/openai` proxies (`model-connections-openai-ollama-and-direct.md`), the router map and how every
request is authenticated (`backend-architecture-and-request-lifecycle.md`), and the server error
catalogue (`error-messages-backend-identity-admin-and-platform.md`).

## 2. Navigation and URLs

All addresses below are relative to the site root. The production host is **TO BE CONFIRMED**, so
this document writes `https://<site>` where a full address is needed.

### 2.1 Screens

| Screen | Where | Who sees it | What it holds | Evidence |
|---|---|---|---|---|
| **Settings > Account**, section **API keys** | `/?settings=account` | Admins, and users holding the **API Keys** permission, when the site-wide switch is on | Show or hide the key; create, copy, replace or delete it; admins also see their **JWT Token** | `src/lib/components/chat/Settings/Account.svelte:386-462`; `src/lib/utils/settings-access.ts:13-15`; `src/lib/i18n/locales/en-US/translation.json:2763` |
| **Settings > Admin > Authentication**, section **User Access** | `/?settings=admin:authentication` | Admins | **API Keys** switch; when on, **API Key Endpoint Restrictions** switch; when that is on, **Allowed Endpoints** text box | `src/lib/components/admin/Settings/Authentication.svelte:188-230`; `src/lib/i18n/locales/en-US/translation.json:2030-2037`, `:2121` |
| **Admin > Users > Groups**, **Default permissions** or a group's **Permissions** | `/admin/users` (Groups tab) | Admins | **Features Permissions > API Keys** switch | `src/lib/components/admin/Users/Groups/Permissions.svelte:959-975`; `src/lib/components/admin/Users/Groups.svelte:220` |
| Interactive API documentation | `/docs` (and the machine-readable `/openapi.json`) | Only exists when the server runs with `ENV=dev` | Every route and its request shape | `backend/open_webui/main.py:506-511`; section 5.16 |

The screens are described click by click in `authentication-and-sign-in.md` sections 5.12 to 5.14;
this document covers what happens after the key leaves the screen.

### 2.2 Base Address for Programs

- The server answers on two families of paths: addresses defined directly in `main.py` start with
  `/api/` (for example `/api/chat/completions`), and the feature routers are mounted under
  `/api/v1/<router>` (for example `/api/v1/files/`) (`backend/open_webui/main.py:843-887`; the
  router list is in `backend-architecture-and-request-lifecycle.md` section 2.2).
- The OpenAI-compatible addresses exist under **both** prefixes: `/api/chat/completions` and
  `/api/v1/chat/completions`, `/api/models` and `/api/v1/models`, `/api/embeddings` and
  `/api/v1/embeddings` are the same handlers (`backend/open_webui/main.py:897-898`, `:1072-1073`,
  `:1108-1109`). A client that adds `/chat/completions`, `/models` and `/embeddings` to a base
  address therefore works with a base of `https://<site>/api` or `https://<site>/api/v1`.
- The Anthropic-compatible address is `/api/v1/messages` (alias `/api/message`), with the token
  counter at `/api/v1/messages/count_tokens` (alias `/api/message/count_tokens`)
  (`backend/open_webui/main.py:1933-1934`, `:2002-2003`). Which base address a given Anthropic
  client needs depends on how that client builds its paths, which is outside this repository
  (section 14).
- The browser itself uses an empty host, so every call is same-site: `WEBUI_API_BASE_URL` is
  `/api/v1` (`src/lib/constants.ts:9-11`).
- `/ollama/...` and `/openai/...` are separate reverse proxies to the providers, not the
  compatibility layer described here; see `model-connections-openai-ollama-and-direct.md`.

### 2.3 Endpoints in This Area

| Method and path | Who | Purpose | Evidence |
|---|---|---|---|
| `GET /api/models`, `GET /api/v1/models` | Verified user (`user` or `admin`) | List the models this person may use; `?refresh=true` rebuilds the list | `backend/open_webui/main.py:897-943` |
| `POST /api/chat/completions`, `POST /api/v1/chat/completions` | Verified user | OpenAI-style chat completion through the full pipeline | `backend/open_webui/main.py:1108-1885` |
| `POST /api/embeddings`, `POST /api/v1/embeddings` | Verified user | OpenAI-style embeddings from a chat connection's model | `backend/open_webui/main.py:1072-1094`; `backend/open_webui/utils/embeddings.py` |
| `POST /api/v1/messages`, `POST /api/message` | Verified user | Anthropic-style Messages request (converted, or passed straight through for some connections) | `backend/open_webui/main.py:2002-2068` |
| `POST /api/v1/messages/count_tokens`, `POST /api/message/count_tokens` | Verified user | Anthropic-style token count, forwarded to the model's connection | `backend/open_webui/main.py:1933-1940`; `backend/open_webui/routers/openai.py:494-541` |
| `POST /api/chat/completed` | Verified user (chat owner or admin when a chat id is sent) | **Deprecated**: run a model's outlet filters on a finished answer, for older integrations | `backend/open_webui/main.py:2090-2107` |
| `POST /api/chat/actions/{action_id}` | Verified user (chat owner or admin when a chat id is sent) | Run an Action function on a message | `backend/open_webui/main.py:2110-2125` |
| `GET /api/tasks` | Admin | List running generation tasks | `backend/open_webui/main.py:2137-2139` |
| `POST /api/tasks/stop/{task_id}` | Admin | Stop one task | `backend/open_webui/main.py:2128-2134` |
| `GET /api/tasks/chat/{chat_id}` | Verified user (owner or admin; others get an empty list) | Task ids running for one chat | `backend/open_webui/main.py:2142-2157` |
| `POST /api/tasks/chat/{chat_id}/stop` | Verified user (owner or admin) | Stop every task of one chat | `backend/open_webui/main.py:2160-2214` |
| `GET /api/v1/auths/api_key` | Signed-in person allowed to use keys | Read one's own key | `backend/open_webui/routers/auths.py:1572-1581` |
| `POST /api/v1/auths/api_key` | As above | Create (or replace) one's own key | `backend/open_webui/routers/auths.py:1529-1550` |
| `DELETE /api/v1/auths/api_key` | As above | Delete one's own key | `backend/open_webui/routers/auths.py:1554-1568` |
| `GET /api/v1/auths/admin/config`, `POST /api/v1/auths/admin/config` | Admin | Read or save the API-key switches with the rest of the authentication settings | `backend/open_webui/routers/auths.py:1204-1296` |
| `POST /api/v1/auths/oauth/{provider}/token/exchange` | External program holding an identity-provider token | Swap that token for a MedIT GPT session token; off unless `ENABLE_OAUTH_TOKEN_EXCHANGE=True` | `backend/open_webui/routers/auths.py:1624-1771`; detail in `sso-oauth-oidc-and-scim.md` section 5.12 |
| `GET /oauth/clients/{client_id}/authorize`, `GET /oauth/clients/{client_id}/callback` | Signed-in person in a browser | MedIT GPT signing in to an external tool server on the person's behalf (`OAuthClientManager`), not a way for programs to sign in to MedIT GPT | `backend/open_webui/main.py:2772-2825`; section 5.17 |

### 2.4 Other Endpoints Integrators Commonly Call

These exist, need the same `Authorization: Bearer` credential, and are documented in their own
areas. Only their existence and owner are recorded here.

| Purpose | Method and path | Area document |
|---|---|---|
| Upload a file (then use its id in `files`) | `POST /api/v1/files/` | `files-uploads-and-storage.md` |
| Check a file's processing status | `GET /api/v1/files/{id}/process/status` | `files-uploads-and-storage.md` |
| List or read files | `GET /api/v1/files/`, `GET /api/v1/files/{id}`, `GET /api/v1/files/{id}/content` | `files-uploads-and-storage.md` |
| List, create or read knowledge bases | `GET /api/v1/knowledge/`, `POST /api/v1/knowledge/create`, `GET /api/v1/knowledge/{id}` | `knowledge-bases.md` |
| Add an uploaded file to a knowledge base | `POST /api/v1/knowledge/{id}/file/add` | `knowledge-bases.md` |
| List, create or read saved chats | `GET /api/v1/chats/` (alias `/api/v1/chats/list`), `POST /api/v1/chats/new`, `GET /api/v1/chats/{id}` | `chat-conversations-history-and-organisation.md` |
| Resolve a paused tool call | `POST /api/v1/chats/{id}/messages/{message_id}/resolve` | `chat-completion-pipeline-and-generation-tasks.md` section 5.15 |
| Generation tasks (titles, follow-ups and others) | `POST /api/v1/tasks/.../completions` | `chat-completion-pipeline-and-generation-tasks.md` section 2.3 |

Evidence for the paths: `backend/open_webui/routers/files.py:280`, `:489`, `:605`, `:624`, `:795`;
`backend/open_webui/routers/knowledge.py:172`, `:318`, `:1099`, `:1425`;
`backend/open_webui/routers/chats.py:248-249`, `:774`, `:1325`; `backend/open_webui/main.py:1893`.

### 2.5 The Remaining Top-Level Endpoints in `main.py`

For completeness against the inventory (39 routes), the top-level endpoints not described above are
owned by other areas: `/api/models/base` and `/api/models/unload` (admin model management,
`model-connections-openai-ollama-and-direct.md`); `/api/config`, `/api/version`,
`/api/version/updates`, `/api/changelog`, `/manifest.json`, `/opensearch.xml`, `/cache/{path:path}`,
`/health`, `/health/db` and `/ready` (`backend-architecture-and-request-lifecycle.md`);
`/api/events`, `/api/events/webhooks` and `/api/events/webhooks/{webhook_id}`
(`notifications-webhooks-events-and-banners.md`); `/api/usage`
(`evaluations-feedback-and-analytics.md`); `/oauth/{provider}/login`,
`/oauth/{provider}/login/callback`, `/oauth/{provider}/callback` and `/oauth/backchannel-logout`
(`sso-oauth-oidc-and-scim.md`); `/api/v1/chats/{id}/messages/{message_id}/resolve`
(`chat-completion-pipeline-and-generation-tasks.md`). Route list: `knowledgebase/tools/inventory.md`.

## 3. Roles and Permissions

### 3.1 What a Program Needs Before Any Call Succeeds

| Requirement | Applies to | What happens if it fails | Evidence |
|---|---|---|---|
| A credential in the request: `Authorization: Bearer <token or key>`, the `token` cookie, or (for keys) the header named by `CUSTOM_API_KEY_HEADER` | Every protected address | HTTP 401 `Not authenticated` | `backend/open_webui/utils/auth.py:403-416`; `backend/open_webui/utils/asgi_middleware.py:126-132` |
| For an API key: the key belongs to an existing account | Keys only | HTTP 401 `Your session has expired or the token is invalid. Please sign in again.` | `backend/open_webui/utils/auth.py:511-517` |
| For an API key: the site-wide **API Keys** switch is on (`auth.enable_api_keys`) | Keys only, admins included | HTTP 403 `Use of API key is not enabled in the environment.` | `backend/open_webui/utils/auth.py:526-527` |
| For an API key: the owner is an admin or holds `features.api_keys` | Keys only | HTTP 403, same text | `backend/open_webui/utils/auth.py:529-536` |
| For an API key, when **API Key Endpoint Restrictions** is on: the address equals an **Allowed Endpoints** entry or lies below it | Keys only, admins included | HTTP 403 `You do not have permission to access this resource. Please contact your administrator for assistance.` | `backend/open_webui/utils/auth.py:541-550` |
| The account's role is `user` or `admin` (not `pending`) | Every address in section 2.3 except the key-management and token-exchange ones | HTTP 401 with the same "do not have permission" text | `backend/open_webui/utils/auth.py:567-576` |
| The account is an admin | `/api/tasks`, `/api/tasks/stop/{task_id}`, `/api/v1/auths/admin/config` | HTTP 401, same text | `backend/open_webui/utils/auth.py:625-631`; `backend/open_webui/main.py:2128-2139` |
| The person may use the requested model | Chat completions, Messages, token counting, embeddings | Chat: HTTP 400 `Model not found`; Messages passthrough and token counting: HTTP 403 `Model not found` (section 5.3) | `backend/open_webui/main.py:1149-1161`, `:1638-1645`; `backend/open_webui/utils/access_control/__init__.py:361-413` |

Key facts:

- **Admins bypass the permission check but not the switch or the restrictions.** With the
  site-wide switch off, nobody's key works, an admin's included; endpoint restrictions apply to
  admins' keys too (`backend/open_webui/utils/auth.py:526-550`).
- **The permission adds up across groups.** `features.api_keys` is granted if the defaults or any
  of the person's groups grant it; a group cannot take it away when the defaults grant it (ground
  truth; `src/lib/components/admin/Users/Groups/Permissions.svelte:969-975` shows the note
  `This is a default user permission and will remain enabled.`).
- **Removing access does not delete the key.** The key stays stored; it simply fails the checks
  above and would work again if access were restored (`backend/open_webui/utils/auth.py:509-536`).
- **A session token (JWT) is not subject to the API-key rules.** A copied session token passes the
  role checks like the browser does, ignores the API-key switch, permission and endpoint
  restrictions, and stops working when it expires or (with Redis) is revoked
  (`backend/open_webui/utils/auth.py:438-493`; ground truth on revocation). Only admins see their
  session token in **Settings > Account** (`src/lib/components/chat/Settings/Account.svelte:401-456`).
- **Managing one's own key** (`/api/v1/auths/api_key`) needs the same switch and permission; a
  refusal there reads `API key creation is not allowed in the environment.` (HTTP 403)
  (`backend/open_webui/routers/auths.py:1517-1525`).

### 3.2 Feature Permissions Still Apply

An API call is checked against the same feature permissions as the browser. Examples relevant to
integrators (detail in `chat-completion-pipeline-and-generation-tasks.md` section 3.2):

| Request field | Re-checked permission | Evidence |
|---|---|---|
| `features.memory` | `features.memories` (and the memory switches) | `backend/open_webui/utils/middleware.py:2686-2698` |
| `features.web_search` | `features.web_search` (and `web.search.enable`) | `backend/open_webui/utils/middleware.py:2700-2709` |
| `features.image_generation` | `features.image_generation` | `backend/open_webui/utils/middleware.py:2711-2720` |
| `tool_servers` (user-supplied tool servers) | `features.direct_tool_servers`; silently dropped otherwise | `backend/open_webui/main.py:1240-1252` |
| Items in `files` (files, knowledge bases, notes, chats, folders) | Read access to each item; an item the person cannot read contributes nothing, without an error | `backend/open_webui/retrieval/utils.py:1505-1604` |

### 3.3 What Tier 1 Can Do Here

Tier 1 is read-only: confirm what the caller sees (status code, `detail` text, address), whether
the **API keys** section appears in the person's **Settings > Account**, and escalate. Tier 1 does
not switch API keys on, grant permissions, change the allowed list or handle anyone's key or token.

## 4. Key Concepts and Terminology

| Term | Meaning here | Evidence |
|---|---|---|
| **API key** | A personal, long-lived secret that begins with `sk-`. One per account; creating a new one replaces the old. It has no expiry date in code and works only while the site-wide switch and the owner's permission allow it | `backend/open_webui/utils/auth.py:378-380`, `:419-420`; `backend/open_webui/routers/auths.py:1529-1550`; `authentication-and-sign-in.md` section 6.3 |
| **Session token (JWT)** | The token the browser receives at sign-in; it expires after `auth.jwt_expiry` (code default `4w`). Programs can send it like a key, but it is tied to a sign-in, not created for programs | `backend/open_webui/utils/auth.py:438-493`; ground truth |
| **Bearer header** | `Authorization: Bearer <credential>`, the usual way to send either credential | `backend/open_webui/utils/auth.py:175`, `:405-406` |
| **Custom API-key header** | An alternative header for keys, named by `CUSTOM_API_KEY_HEADER` (code default `x-api-key`). It is read only when there is no `Authorization` header and no `token` cookie | `backend/open_webui/env.py:806-812`; `backend/open_webui/utils/asgi_middleware.py:126-132` |
| **Site-wide switch** | **API Keys** (`auth.enable_api_keys`): whether keys work at all | `backend/open_webui/config.py:2454`, `:3155` |
| **API Keys permission** | `features.api_keys`: whether a non-admin may create and use a key | `backend/open_webui/config.py:1924`, `:2003` |
| **Endpoint restrictions / Allowed Endpoints** | Optional allow-list of address prefixes for keys (`auth.api_key.endpoint_restrictions`, `auth.api_key.allowed_endpoints`) | `backend/open_webui/config.py:2456-2464`, `:3156-3157` |
| **OpenAI-compatible** | Accepts the request shape of OpenAI's Chat Completions, Models and Embeddings APIs; extra Open WebUI fields are optional | `backend/open_webui/main.py:897-899`, `:1072-1094`, `:1108-1120` |
| **Anthropic-compatible** | Accepts Anthropic's Messages request shape and answers in that shape | `backend/open_webui/main.py:2002-2068`; `backend/open_webui/utils/anthropic.py` |
| **Passthrough** | For a model whose connection is Anthropic's own service or a LiteLLM connection, a Messages request is forwarded unchanged instead of being converted | `backend/open_webui/utils/anthropic.py:131-135`; `backend/open_webui/main.py:2041-2044` |
| **Model id** | The exact `id` value from `/api/models`; for a connection with a **Prefix ID** it reads `<prefix>.<provider model id>`; for a workspace (custom) model it is the id chosen when the model was created | `backend/open_webui/routers/openai.py:733-750`; `backend/open_webui/utils/models.py:227-238` |
| **Custom (workspace) model** | A saved model with its own name, system prompt, knowledge, tools and access list, built on a base model | `backend/open_webui/utils/models.py:178-260`; `workspace-models-and-model-access.md` |
| **Session id** | The id of a browser's websocket connection, sent by the web page. Its absence marks a request as an API call | `backend/open_webui/main.py:1274`, `:1803`, `:1882-1885` |
| **Chat id** | The id of a saved chat. API calls that send none are not saved | `backend/open_webui/main.py:1232`; `backend/open_webui/utils/chat_id.py:15-16` |
| **Background tasks** | The optional `background_tasks` object (`title_generation`, `tags_generation`, `follow_up_generation`) asking the server to generate a title, tags or follow-ups after the answer | `backend/open_webui/main.py:1120`; `backend/open_webui/constants.py:135-145`; `backend/open_webui/utils/middleware.py:3832-3951` |
| **Filters (inlet, stream, outlet)** | Admin-installed functions that can change a request before it goes out, each streamed piece, and the finished answer | `backend/open_webui/utils/middleware.py:2650-2670`, `:6646-6706`; `functions-pipes-filters-actions-and-pipelines.md` |
| **Server-sent events (SSE)** | The streaming format: lines beginning `data:` and ending with `data: [DONE]` (OpenAI style) or `event:`/`data:` pairs (Anthropic style) | `backend/open_webui/utils/middleware.py:6646-6711`; `backend/open_webui/utils/anthropic.py:595-983` |
| **OpenAPI docs** | The automatically generated `/docs` page and `/openapi.json` schema, present only when `ENV=dev` | `backend/open_webui/main.py:506-511`; `backend/open_webui/env.py:139` |
| **`OAuthClientManager`** | The part of MedIT GPT that signs in to external MCP tool servers on a person's behalf (MedIT GPT as the client). It does not let outside programs sign in to MedIT GPT | `backend/open_webui/utils/oauth.py:829-1327`; section 5.17 |
| **Token exchange** | An optional address that swaps a token from the site's identity provider for a MedIT GPT session token | `backend/open_webui/routers/auths.py:1624-1771`; `sso-oauth-oidc-and-scim.md` section 5.12 |

## 5. Workflows (Step by Step)

### 5.1 Getting a Program Ready to Call MedIT GPT

1. **An admin switches API keys on** under **Settings > Admin > Authentication > User Access >
   API Keys** (description `Allow users to create API keys for programmatic access.`) and saves;
   the page confirms with `Settings saved successfully!`
   (`src/lib/components/admin/Settings/Authentication.svelte:188-194`, `:98-107`;
   `src/lib/i18n/locales/en-US/translation.json:2036-2037`). With persistent settings on (the code
   default), the saved value is read from the database on every key request, so it applies from
   the next request in every worker (`backend/open_webui/utils/auth.py:519-524`;
   `backend/open_webui/models/config.py:150-167`).
2. **The person is allowed keys**: they are an admin, or **Features Permissions > API Keys** is on
   in **Default permissions** or in one of their groups
   (`src/lib/components/admin/Users/Groups/Permissions.svelte:959-975`).
3. **The person creates a key** in **Settings > Account > API keys**: press **Show** on the
   **Secrets** row, then **Create new secret key**; the pop-up says `API Key created.` and the key
   appears masked with a copy button (`src/lib/components/chat/Settings/Account.svelte:181-188`,
   `:386-400`; `src/lib/i18n/locales/en-US/translation.json:2752`). The full click path, the
   **Create new key** and **Delete** menu, and what happens when creation is refused are in
   `authentication-and-sign-in.md` section 5.12.
4. **The program stores the key** like a password and sends it with every request (section 5.2).
   The owner can view and copy the current key again later in the same section; deleting it, or
   creating a new one, ends the old key at once (`src/lib/components/chat/Settings/Account.svelte:225-235`;
   `backend/open_webui/routers/auths.py:1529-1568`).

The key is personal. Every call made with it is recorded against the owner, uses the owner's model
access, permissions, groups, memories and knowledge access, and updates the owner's last-active
time (`backend/open_webui/utils/auth.py:509-564`). Whether keys may be shared with a team, used by
service accounts, or put in shared code is a policy question that is **TO BE CONFIRMED**.

### 5.2 Sending the Credential

| Way | Header or cookie | Accepted credentials | Notes | Evidence |
|---|---|---|---|---|
| Bearer header (usual) | `Authorization: Bearer sk-…` | API key or session token | Use the usual form: the word `Bearer`, a space, then the credential | `backend/open_webui/utils/auth.py:175`, `:383-390`, `:403-406` |
| Custom header | Header named by `CUSTOM_API_KEY_HEADER`, code default `x-api-key: sk-…` | Intended for API keys | Read only when the request has no `Authorization` header and no `token` cookie. Lets a program sit behind a gateway that uses `Authorization` for itself, and lets Anthropic-style clients send their usual `x-api-key` header | `backend/open_webui/utils/asgi_middleware.py:126-132`; `backend/open_webui/env.py:806-812`; `backend/open_webui/main.py:2019-2020` |
| Cookie | `token` | Session token | What the browser uses; not meant for programs | `backend/open_webui/utils/auth.py:408-409` |

A first test that changes nothing is listing models:

```bash
curl -s https://<site>/api/models -H "Authorization: Bearer sk-EXAMPLE-NOT-A-REAL-KEY"
```

A JSON reply beginning `{"data": [` means the key, switch, permission and any endpoint
restriction all allowed the call (`backend/open_webui/main.py:897-943`). Section 10 lists what the
refusals look like.

### 5.3 Choosing the Model Id

1. **Ask the server.** `GET /api/models` returns `{"data": [ … ]}` with one entry per model the
   person may use; each entry has `id`, `name`, `object: "model"`, `created` and `owned_by`, plus
   Open WebUI extras such as `info` (the workspace record, without its parameters), `tags`,
   `actions` and `filters` (`backend/open_webui/main.py:897-943`;
   `backend/open_webui/utils/models.py:178-260`, `:401-441`). There is no top-level `object` field
   in the reply (`backend/open_webui/main.py:943`).
2. **Use the `id`, not the display name.** Ids are case- and spelling-exact.
   - A model from a connection with a **Prefix ID** has the id `<prefix>.<provider id>`; MedIT GPT
     removes the prefix before calling the provider (`backend/open_webui/routers/openai.py:733-750`,
     `:1556-1557`; `backend/open_webui/utils/model_ids.py:1-4`).
   - A workspace (custom) model has the id chosen when it was created, and brings its system
     prompt, knowledge, tools, filters and parameters with it (`backend/open_webui/utils/models.py:210-260`;
     `backend/open_webui/routers/openai.py:1518-1535`).
   - An **Arena** model picks a real model at random per request; the reply carries
     `selected_model_id` (an extra first stream event, or an extra JSON field)
     (`backend/open_webui/utils/chat.py:205-278`).
3. **What the list leaves out or changes.**
   - Filter pipelines are removed; duplicate ids collapse to the last one, which is also the one a
     chat request would use (`backend/open_webui/main.py:902-909`).
   - The list is access-filtered: a non-admin sees a model only if it has a workspace record they
     own or may read; models with no workspace record are listed for admins only
     (`backend/open_webui/utils/models.py:524-575`; detail in
     `model-connections-openai-ollama-and-direct.md` section 3.2).
   - A model hidden from the chat page's model picker is still listed and usable here: hiding is a
     display choice made in the browser, not an access rule
     (`src/lib/components/chat/ModelSelector/Selector.svelte:310`; `backend/open_webui/main.py:897-943`).
   - The order follows the admin's model order list when one is set
     (`backend/open_webui/main.py:928-937`).
   - `?refresh=true` rebuilds the list from the providers instead of the cache
     (`backend/open_webui/main.py:899-900`; caching in
     `model-connections-openai-ollama-and-direct.md` section 5.8).
4. **Direct connections are not usable from a script.** A person's own browser-side connections
   need a live browser session; a plain API call that names one fails with
   `Direct connection requires an active WebSocket session; cannot generate completion in this context (e.g. background task).`
   (`backend/open_webui/utils/chat.py:63-68`).

### 5.4 Sending a Chat Completion (OpenAI Format)

**The minimum.** `POST /api/chat/completions` (or `/api/v1/chat/completions`) with a JSON body
holding `model` and `messages` in the OpenAI shape; `stream` is optional:

```bash
curl -s https://<site>/api/chat/completions \
  -H "Authorization: Bearer sk-EXAMPLE-NOT-A-REAL-KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "example-model-id", "messages": [{"role": "user", "content": "Hello"}]}'
```

**What the server does with it** (`backend/open_webui/main.py:1108-1885`;
`backend/open_webui/utils/middleware.py:2391-3276`):

1. Rebuilds the model list if empty, then refuses an unknown model or one the person may not use
   with HTTP 400 `Model not found` (`backend/open_webui/main.py:1115-1161`, `:1638-1645`). A
   custom model whose base model has gone also fails with `Model not found` unless the maintainer
   set `ENABLE_CUSTOM_MODEL_FALLBACK` (`backend/open_webui/main.py:1133-1147`, `:1179-1185`).
2. Merges parameters: global default parameters, then the model's own, then the request's
   `params` object (`backend/open_webui/main.py:1169-1177`). Standard OpenAI fields at the top
   level (for example `temperature`, `max_tokens`, `tools`, `response_format`) are passed on in the
   request body to an OpenAI-compatible provider (`backend/open_webui/routers/openai.py:1511-1557`);
   for an Ollama model the body is first converted to Ollama's format
   (`backend/open_webui/utils/chat.py:283-285`).
3. **The model's Stream Chat Response setting wins over the caller's `stream` value** when the
   model (or the global default parameters) sets it (`backend/open_webui/main.py:1192-1194`).
4. Runs the pipeline as for the browser: arena choice, system prompt with variables, inlet filters,
   optional memory, legacy-mode web search and image generation, tools, files and knowledge
   (sections 5.6 to 5.8), then calls the provider. Ollama models are converted to and from the
   OpenAI format, so the caller always sees the OpenAI shape
   (`backend/open_webui/utils/chat.py:280-305`).
5. Returns the provider's answer in the HTTP response, because a plain API call carries no
   `session_id` and no `chat_id` (`backend/open_webui/main.py:1882-1885`).

**What a plain API call does not get** (no `session_id`, no `chat_id`):

| Feature | For a plain API call | Evidence |
|---|---|---|
| Saving as a chat | Nothing is saved; the chat id is empty | `backend/open_webui/utils/middleware.py:2392-2394`; `backend/open_webui/utils/chat_id.py:15-16` |
| Built-in tools (web search, knowledge, memory, notes, code tools and others) | Not offered: the server adds them only for requests from the app | `backend/open_webui/utils/middleware.py:2809-2813`, `:3096-3099`; `builtin-native-tools.md` section 11.16 |
| Server-side tool loop in native mode | Not run: tool specs from `tool_ids` are sent to the model, and any tool calls the model makes come back to the caller unexecuted (read from code, not exercised; section 14) | `backend/open_webui/utils/middleware.py:3184-3195`, `:4413-4428`, `:6644-6717` |
| Title, tags, follow-up suggestions | Not generated, even with `background_tasks` (section 5.9) | `backend/open_webui/utils/middleware.py:4228-4411`, `:6644-6717` |
| Live status lines and websocket events | None reach the caller; the HTTP response is the only channel | `backend/open_webui/main.py:1882-1885` |
| Task id, **Stop** button, `/api/tasks*` | No task is created; the work runs inside the HTTP request | `backend/open_webui/main.py:1802-1885` |

**Open WebUI fields a program may add** (all optional):

| Field | Effect | Evidence |
|---|---|---|
| `files` | List of items to search (RAG): uploaded files, knowledge bases and more (section 5.6) | `backend/open_webui/main.py:1280`; `backend/open_webui/utils/middleware.py:2049-2167` |
| `tool_ids` | Workspace tools (or `server:mcp:<id>` MCP servers) to offer to the model, subject to tool access (section 5.7) | `backend/open_webui/utils/middleware.py:2962-3032`; `backend/open_webui/utils/tools.py:267-300` |
| `features` | `memory`, `web_search`, `image_generation`, `code_interpreter`, `voice`; each re-checked against permissions; web search and image generation act only in legacy function-calling mode | `backend/open_webui/utils/middleware.py:2672-2751` |
| `variables` | Values for `{{…}}` placeholders in system prompts | `backend/open_webui/utils/payload.py:34-38` |
| `params` | Open WebUI parameters (for example `system`, `function_calling`) merged over the model's | `backend/open_webui/main.py:1175-1177`, `:1290-1294` |
| `filter_ids` | Extra filter functions to apply | `backend/open_webui/main.py:1277` |
| `background_tasks` | Title, tags and follow-ups; effective only with a saved chat (section 5.9) | `backend/open_webui/main.py:1120` |
| `chat_id`, `id`, `parent_id`, `user_message`, `session_id` | Fields the web page uses to manage a saved chat; see section 5.9 before using them | `backend/open_webui/main.py:1209-1297` |

### 5.5 Reading the Answer: JSON and Streaming

**Non-streaming** (`stream` false or absent, unless the model forces streaming): the provider's
OpenAI-style JSON comes back, with one addition when files or knowledge were searched: a top-level
`sources` list holding the retrieved passages and their origin
(`backend/open_webui/utils/middleware.py:3238-3246`, `:3679-3692`, `:4425-4428`).

**Streaming** (`"stream": true`): an event stream of `data: {…}` lines ending with
`data: [DONE]` (`backend/open_webui/utils/middleware.py:6644-6717`).

- When retrieval ran, the **first** event is `data: {"sources": [ … ]}` before the provider's own
  chunks; a strict OpenAI client may need to skip lines that have no `choices`
  (`backend/open_webui/utils/middleware.py:6664-6675`).
- An Arena model adds a first event `data: {"selected_model_id": "…"}`
  (`backend/open_webui/utils/chat.py:245-267`).
- Admin-installed **stream filters** may change each chunk before it is sent
  (`backend/open_webui/utils/middleware.py:6677-6702`).
- If something fails mid-stream, the stream ends with
  `data: {"error": {"message": "Chat completion stream failed"}}` and then `data: [DONE]`; the server
  log reads `Chat completion stream failed mid-response: …`
  (`backend/open_webui/utils/middleware.py:6707-6711`).
- The stream is the provider's own stream passed through. MedIT GPT's compression layer
  (`ENABLE_COMPRESSION_MIDDLEWARE`, default on) wraps all responses
  (`backend/open_webui/env.py:790`; `backend/open_webui/main.py:816-817`); the installed compression
  library's list of compressible types does not include event streams (read from the library, not
  from this repository; section 14). Nothing in the code adds a header telling an intermediate proxy
  not to buffer, so a buffering proxy between the caller and MedIT GPT can hold the stream back
  until it ends (no such header found in `backend/open_webui`; section 11.4).

**Token usage.** When streaming, the server asks the provider to include usage only if the model's
**usage** capability is on; otherwise many providers send no counts
(`backend/open_webui/main.py:1196-1198`). Ollama models always end with a usage block that has both
OpenAI names (`prompt_tokens`, `completion_tokens`) and standard names (`input_tokens`,
`output_tokens`, `total_tokens`) (`backend/open_webui/utils/response.py:163-207`, `:230-270`).
Non-streaming replies carry whatever usage the provider returned. Usage reporting is summarized in
section 5.18.

**Errors.** For a plain API call, any failure while preparing or running the turn, including a
provider's own refusal (bad key, quota, rate limit, content filter), comes back as **HTTP 400**
with the reason in `detail`; the provider's original status code is not kept
(`backend/open_webui/main.py:1659-1665`, `:1686-1722`). When the provider's error body cannot be
read, `detail` is `Provider returned HTTP {status_code}` or `Provider returned an error`
(`backend/open_webui/utils/misc.py:43-65`). Section 10 lists the texts.

### 5.6 Using Files and Knowledge Bases from a Program

1. Upload with `POST /api/v1/files/` and wait for processing to finish
   (`GET /api/v1/files/{id}/process/status`); see `files-uploads-and-storage.md` section 2.2.
2. Send the items to search in the top-level `files` list of the chat request. The retrieval step
   reads only that list (`backend/open_webui/main.py:1280`;
   `backend/open_webui/utils/middleware.py:2055`). Item shapes the server understands include
   `{"type": "file", "id": "…"}` for an uploaded file and `{"type": "collection", "id": "…"}` for a
   knowledge base; notes, chats, folders, plain text and web addresses are also accepted
   (`backend/open_webui/retrieval/utils.py:1370-1610`). Adding `"context": "full"` to an item asks
   for the whole document instead of the best-matching passages
   (`backend/open_webui/utils/middleware.py:2057-2061`; `backend/open_webui/retrieval/utils.py:1506`).
3. Unless every item is in full-context mode, the server first asks the task model for search
   queries, then searches with the admin's retrieval settings (top K, relevance threshold, hybrid
   search, reranking) (`backend/open_webui/utils/middleware.py:2060-2135`; settings in
   `rag-retrieval-embeddings-and-vector-stores.md`).
4. Each item is checked against the person's access: their own file or knowledge base, one shared
   with them, or (admins) anything. An item they cannot read, an unknown id or an unprocessed file
   contributes nothing, and **no error is returned** (`backend/open_webui/retrieval/utils.py:1522-1604`).
5. The passages are added to the prompt with the admin's RAG template, and the reply carries
   `sources` (section 5.5) (`backend/open_webui/utils/middleware.py:3234-3246`).
6. Retrieval is skipped altogether when the model's **File Context** capability is off
   (`backend/open_webui/utils/middleware.py:3206-3214`).

**A custom model's own attached knowledge** behaves differently for programs. In the default
(native) function-calling mode, attached knowledge is reached through built-in tools, which plain
API calls do not get; the server adds it to the search list itself only when the model's
**Function Calling** parameter is **Legacy** (`backend/open_webui/utils/middleware.py:2604-2644`,
`:2809-2813`, `:3099-3123`; `src/lib/i18n/locales/en-US/translation.json:2825-2826`). A program that
needs a model's knowledge can name the knowledge base in `files` instead (read from code, not
exercised; section 14).

### 5.7 Tools from a Program

- **No hidden tools.** Built-in tools are added only for requests from the app; the source comment
  reads "API callers don't expect hidden tools; they can explicitly request tools via tool_ids."
  (`backend/open_webui/utils/middleware.py:3096-3099`).
- **Naming tools.** `tool_ids` lists workspace tools (and `server:mcp:<id>` MCP servers) to offer.
  Each tool is checked against the person's access; a tool they may not use is skipped with only a
  server log line `Access denied to tool {tool_id} for user {user.id}`
  (`backend/open_webui/utils/tools.py:283-299`). An MCP server that cannot be reached is skipped too
  (`backend/open_webui/utils/middleware.py:2962-3014`).
- **Who runs the tool.** In **Legacy** function-calling mode the server picks and runs the tools
  before the main answer and feeds their results in, which works for programs
  (`backend/open_webui/utils/middleware.py:3196-3205`). In the default **Native** mode the tool
  definitions go to the model, but for a plain API call the server's tool loop does not run, so the
  model's tool calls are returned to the caller (read from code, not exercised; section 14)
  (`backend/open_webui/utils/middleware.py:3189-3195`, `:4413-4428`, `:6644-6717`).
- **Bringing one's own tools.** A request that includes its own `tools` list skips all server-side
  tool resolution and passes the list through unchanged; `"tools": []` turns tools off
  (`backend/open_webui/utils/middleware.py:2945-2948`). The caller then runs the tools itself, as
  with any OpenAI-compatible service.
- **User-supplied tool servers** (`tool_servers`) are dropped unless the person holds
  `features.direct_tool_servers`, and in any case need a browser to run
  (`backend/open_webui/main.py:1240-1252`; `backend/open_webui/utils/middleware.py:3360-3363`).

Tools in general are documented in `workspace-tools-tool-servers-mcp-and-terminals.md` and
`builtin-native-tools.md`.

### 5.8 Filters, Pipes and Pipelines for API Callers

| Stage | Runs for a plain API call? | Evidence |
|---|---|---|
| Pipelines-server inlet filters and function **inlet** filters | Yes, before the provider call | `backend/open_webui/utils/middleware.py:2649-2670` |
| Function **stream** filters | Yes, on every streamed chunk | `backend/open_webui/utils/middleware.py:6664-6702` |
| **Outlet** filters | Yes when `ENABLE_API_OUTLET_FILTERS` is on (code default on), after the answer. Changes they make are not sent back to the caller, who already has the answer; failures are logged at debug level only | `backend/open_webui/env.py:1052`; `backend/open_webui/utils/middleware.py:4413-4423`, `:6653-6706`, `:4050-4210` |
| **Pipe** models (functions that act as a model) | Yes; the reply is whatever the pipe returns | `backend/open_webui/utils/chat.py:280-282` |
| Pipeline models (external Pipelines server) | Yes; the request sent there includes the person's name, id, email and role | `backend/open_webui/routers/openai.py:1559-1566` |

`POST /api/chat/completed` (deprecated) still lets an older integration run outlet filters on a
finished exchange; it needs `model`, `id` (message id), `chat_id` and `session_id` in the body and
answers HTTP 400 `Missing message id` or `Model not found` when they are wrong
(`backend/open_webui/main.py:2090-2107`; `backend/open_webui/utils/chat.py:311-374`). Filters are
documented in `functions-pipes-filters-actions-and-pipelines.md`.

### 5.9 Saving to a Chat and the `background_tasks` Field

The web page manages chats by sending extra fields. A program can send them too, but the result
depends on the combination (`backend/open_webui/main.py:1209-1235`, `:1299-1633`, `:1802-1885`;
`backend/open_webui/utils/middleware.py:3279-3294`, `:4228-4411`, `:6467-6642`):

| Request contains | What runs | What the caller gets back |
|---|---|---|
| Neither `chat_id` nor `session_id` (an ordinary OpenAI-style request) | The pipeline, without saving | The answer (JSON or stream). `background_tasks` has no effect |
| `parent_id: null` and no `chat_id` | A new chat titled `New Chat` is created and saved with the `user_message` and any assistant placeholder ids sent; the request then continues as in the first row, unless a message `id` was also sent (then as in the next row) | As in the first or next row |
| An existing `chat_id` the person owns plus the message `id`, no `session_id` | The answer is saved into that chat, websocket events go to the owner's open browser tabs, outlet filters and requested background tasks run | Non-streaming: the JSON answer. Streaming: the code path returns no stream body (read from code, not exercised; section 14) |
| `chat_id` and `session_id` | Runs as a background task exactly like the web page | At once: `{"status": true, "task_ids": [ … ], "chat_id": "…"}`; the answer arrives only over the websocket |

- Posting into a chat the person does not own answers HTTP 404 `Something went wrong :/`
  (admins excepted) (`backend/open_webui/main.py:1494-1499`).
- `background_tasks` is an object such as
  `{"title_generation": true, "tags_generation": true, "follow_up_generation": true}`
  (`backend/open_webui/constants.py:135-145`). Titles and tags are generated only for saved chats;
  follow-ups also for unsaved ones, but only on the paths that run background tasks
  (`backend/open_webui/utils/middleware.py:3832-3951`). The chat-pipeline document describes the
  tasks themselves (`chat-completion-pipeline-and-generation-tasks.md` section 5.10).
- A program that only wants answers should leave all of these fields out.

### 5.10 Sending an Anthropic Messages Request

`POST /api/v1/messages` (alias `/api/message`) accepts the Anthropic Messages body (`model`,
`messages`, optional `system`, `max_tokens`, `stream` and so on). An Anthropic-style client can send
its key in `x-api-key`, which the custom-header rule in section 5.2 accepts when the header name has
not been changed (`backend/open_webui/main.py:2002-2021`; `backend/open_webui/env.py:812`).

**Step by step** (`backend/open_webui/main.py:2022-2068`):

1. The server first tries to count the input tokens through the model's connection; a failure is
   ignored apart from the server log line `Unable to count Anthropic input tokens for model {model}`
   (`backend/open_webui/main.py:2024-2028`). Each failed count is also published as a
   `model.provider_request.failed` event (section 9) (`backend/open_webui/routers/openai.py:517-528`).
2. A custom model is looked up so its base model can be found (`backend/open_webui/main.py:2030-2040`).
3. **Passthrough.** If that base model belongs to a connection whose address contains
   `api.anthropic.com`, or whose provider type is LiteLLM, the request is forwarded **unchanged** to
   the connection's `/messages` address and the provider's answer, stream or error is returned as it
   came (`backend/open_webui/utils/anthropic.py:131-135`; `backend/open_webui/main.py:1943-1999`,
   `:2041-2044`). Model access is still checked, but none of the MedIT GPT pipeline runs: no
   filters, no system prompt, knowledge, memory or tools from a custom model, and a custom model
   is sent as its plain base model (read from code, not exercised; section 14)
   (`backend/open_webui/routers/openai.py:454-491`).
4. **Conversion.** Otherwise the body is converted to the OpenAI format, sent through
   `/api/chat/completions` internally (section 5.4) and the answer converted back
   (`backend/open_webui/main.py:2047-2068`).

**What the conversion keeps** (`backend/open_webui/utils/anthropic.py:17-32`, `:138-469`):

| Anthropic request part | Becomes | Notes |
|---|---|---|
| `system` (text or text blocks) | A system message | Cache markers on blocks are kept |
| `messages` text blocks | Text content | |
| Image blocks (base64 or URL) | Image parts | |
| `tool_use` blocks | Assistant tool calls | |
| `tool_result` blocks | Tool messages | Text, images, `document` (as text) and `search_result` (as text) inside a result are kept; `is_error` adds `Error: ` in front |
| `thinking` / `redacted_thinking` blocks | Kept only when signed or redacted | Unsigned thinking is dropped |
| `max_tokens`, `temperature`, `top_p`, `top_k`, `stream`, `metadata`, `service_tier`, `reasoning_effort` | Same names | |
| `stop_sequences` | `stop` | |
| `tools` | OpenAI function tools (`input_schema` becomes `parameters`) | |
| `tool_choice` `auto` / `any` / `tool` | `auto` / `required` / the named function | Other choices are dropped |
| `output_config.effort` | `reasoning_effort` (unless given directly) | |
| `output_config.format` (`json_schema`, `json_object`) | `response_format` | |
| Any other top-level field | **Dropped**, unless the model's connection lists it under **Passthrough params** (or `*`) | This includes Open WebUI fields such as `files` and `tool_ids`; see `model-connections-openai-ollama-and-direct.md` section 5.2 |
| Other content block types at message level (for example a top-level `document` block) | **Dropped** without a message | Only the types above are handled |

**What comes back** (`backend/open_webui/utils/anthropic.py:472-592`, `:595-983`):

- Non-streaming: `{"type": "message", "role": "assistant", "content": [ … ], "model": "<requested id>", "stop_reason": …, "usage": {…}}`
  with `thinking`, `text` and `tool_use` blocks. `stop_reason` maps `stop` to `end_turn`, `length`
  to `max_tokens`, `tool_calls` to `tool_use`, and anything else to `end_turn`. Usage takes the
  provider's counts, falling back to the earlier token count for input.
- Streaming: Anthropic-style events (`message_start`, `content_block_start`,
  `content_block_delta` with `thinking_delta`, `text_delta` or `input_json_delta`,
  `content_block_stop`, `message_delta`, `message_stop`). Text that arrives after a tool call has
  started is not forwarded, to keep Anthropic's ordering (`backend/open_webui/utils/anthropic.py:747-751`).
- `sources` and `selected_model_id` extras are not carried into the Anthropic shapes (lines without
  `choices` are skipped, `backend/open_webui/utils/anthropic.py:707-709`).
- **Errors are not converted.** A refusal comes back in the Open WebUI form `{"detail": "…"}` with
  the status of section 10 (usually HTTP 400), not as an Anthropic error object
  (`backend/open_webui/main.py:2051`, `:2066-2068`). A failure in the middle of a converted stream
  is logged (`Error in Anthropic stream conversion: {e}`) and the stream is closed normally, and the
  error frame of section 5.5 has no `choices`, so the client sees what looks like a short,
  complete answer (read from code, not exercised; section 14) (`backend/open_webui/utils/anthropic.py:652-709`,
  `:907-983`).

**Token counting** (`POST /api/v1/messages/count_tokens`, alias `/api/message/count_tokens`)
forwards the request to the model connection's `/messages/count_tokens` address and returns
`{"input_tokens": N}` (`backend/open_webui/main.py:1933-1940`;
`backend/open_webui/routers/openai.py:454-541`). It works only for models from an OpenAI-compatible
connection whose provider offers that address; refusals are `model is required` (400),
`Model not found` (403), `Model '' was not found` (404, for example an Ollama model), the provider's
own status and body, `Invalid token-count response from upstream provider` (502) or
`Open WebUI: Server Connection Error` (502).

### 5.11 Embeddings

`POST /api/embeddings` (alias `/api/v1/embeddings`) takes an OpenAI-style body (`model`, `input`),
checks access to the named **chat-connection** model, and forwards the request to Ollama (answer
converted to the OpenAI shape) or to the OpenAI-compatible connection (`backend/open_webui/main.py:1072-1094`;
`backend/open_webui/utils/embeddings.py:24-88`). It is unrelated to the embedding model used for
documents and knowledge bases. An unknown model raises a plain `Model not found` error that is not
turned into a tidy reply, so the caller sees an HTTP 500 server error; provider errors keep the
provider's status and body; network failures give `Open WebUI: Server Connection Error`
(`backend/open_webui/routers/openai.py:1757-1860`). Detail: `model-connections-openai-ollama-and-direct.md`
section 5.15 and `rag-retrieval-embeddings-and-vector-stores.md` section 5.18.

### 5.12 Running an Action Function from a Program

`POST /api/chat/actions/{action_id}` runs an admin-installed Action function on a message, as the
button under an answer does. The body must carry `model`, `chat_id`, `id` (message id) and
`session_id`; channel chats are refused (`Channel chats are not supported on this endpoint`), and a
chat the person does not own answers 404 `Something went wrong :/`
(`backend/open_webui/main.py:2071-2087`, `:2110-2125`; `backend/open_webui/utils/actions.py:19-160`).
Other refusals arrive as HTTP 400: `Plugins are disabled by ENABLE_PLUGINS=false`,
`Action not found: {action_id}`, `Model not found`, `Action not available: {action_id}` (the action
is not an active Action, or for non-admins is not attached to the model), or `Error: {e}` when the
action itself fails. Actions are documented in `functions-pipes-filters-actions-and-pipelines.md`.

### 5.13 Watching and Stopping Generation Tasks

These endpoints concern background tasks started by the web page (and by the "chat id plus session
id" combination in section 5.9). A plain API call has no task to list or stop.

| Call | Answer | Evidence |
|---|---|---|
| `GET /api/tasks` (admin) | `{"tasks": [ … ]}` | `backend/open_webui/main.py:2137-2139` |
| `POST /api/tasks/stop/{task_id}` (admin) | A `status` and a `message` such as `Task {task_id} stopped.` (with Redis), `Task {task_id} successfully stopped.`, `Task {task_id} successfully cancelled.`, `Cancellation requested for {task_id}.` or, unknown id without Redis, `Task with ID {task_id} not found.` | `backend/open_webui/main.py:2128-2134`; `backend/open_webui/tasks.py:263-293` |
| `GET /api/tasks/chat/{chat_id}` | `{"task_ids": [ … ]}`; an empty list for someone else's chat | `backend/open_webui/main.py:2142-2157` |
| `POST /api/tasks/chat/{chat_id}/stop` | `All tasks for item {item_id} stopped.`, `No tasks found for item {item_id}.` or, when only a reply paused for tool approval was waiting, `Finalized pending approval message.`; someone else's chat gives 404 `We could not find what you're looking for :/` | `backend/open_webui/main.py:2160-2214`; `backend/open_webui/tasks.py:296-309` |

The Stop button and its behaviour are described in `chat-completion-pipeline-and-generation-tasks.md`
section 5.9.

### 5.14 Admin: Switching Keys On, Granting Them and Restricting Them

1. **Site-wide switch.** **Settings > Admin > Authentication > User Access > API Keys** (section 5.1).
   Off means no key works, an admin's included (`backend/open_webui/utils/auth.py:526-527`).
2. **Who may hold a key.** Admins always may. For everyone else, turn on **API Keys** under
   **Features Permissions** in **Default permissions** (everyone) or in specific groups
   (`src/lib/components/admin/Users/Groups/Permissions.svelte:959-975`; how groups combine:
   `users-groups-roles-and-permissions.md`).
3. **Optional restriction.** With **API Keys** on, the row **API Key Endpoint Restrictions**
   (description `Limit API keys to configured endpoints.`) appears; turning it on shows
   **Allowed Endpoints** (description `Comma-separated API paths that API keys can access.`,
   placeholder `e.g.) /api/v1/messages, /api/v1/channels`) and a link reading
   `To learn more about available endpoints, visit our documentation.` that opens the upstream
   documentation site (`src/lib/components/admin/Settings/Authentication.svelte:196-230`;
   `src/lib/i18n/locales/en-US/translation.json:2030-2035`, `:3266`).
4. **How the list is matched** (`backend/open_webui/utils/auth.py:541-550`):
   - entries are split on commas and trimmed; empty entries are ignored;
   - a request is allowed when its path **equals** an entry or **begins with the entry followed by
     `/`**; there are no wildcards, the comparison is exact (upper and lower case matter), and the
     query string is not part of the path;
   - so `/api/v1/files` allows `/api/v1/files/` and `/api/v1/files/{id}/content`, but an entry
     written with a trailing slash (`/api/v1/files/`) allows only that exact path;
   - the aliases are separate paths: allowing `/api/v1/chat/completions` does not allow
     `/api/chat/completions`, and a client that lists models needs `/api/models` or `/api/v1/models`
     as well;
   - with restrictions on and the list empty, every key request is refused;
   - the rule applies to admins' keys too, and does not apply to session tokens.
5. **Save.** The page shows `Settings saved successfully!`; a server refusal shows the server's text
   in a pop-up (`src/lib/components/admin/Settings/Authentication.svelte:89-107`).

The policy MedIT GPT applies (who gets keys, which endpoints are allowed) is **TO BE CONFIRMED**.

### 5.15 Replacing, Revoking and Removing Access

| Goal | Who | How | Effect | Evidence |
|---|---|---|---|---|
| Replace a key (rotate) | The owner | **Settings > Account > API keys**, **More** menu, **Create new key** | The old key stops working at once; the new key must be put into every program | `src/lib/components/chat/Settings/Account.svelte:464-550`; `backend/open_webui/routers/auths.py:1529-1550` |
| Delete a key | The owner | **More** menu, **Delete**, confirm `Delete API Key?` / `This will revoke the current API key.`; pop-up `API Key deleted.` | The key stops working at once | `src/lib/components/chat/Settings/Account.svelte:190-200`, `:583-592`; `backend/open_webui/routers/auths.py:1554-1568` |
| Stop one person's key | An admin | No screen or endpoint deletes another person's key. Remove the person's **API Keys** permission (non-admins), change their role to `pending`, or delete the account | The key fails the checks of section 3.1 but stays stored, and works again if access returns (except after deletion) | `backend/open_webui/routers/auths.py:1529-1581`; `backend/open_webui/utils/auth.py:509-576` |
| Stop every key | An admin | Switch **API Keys** off | All keys refused with `Use of API key is not enabled in the environment.` | `backend/open_webui/utils/auth.py:526-527` |

- Signing out and changing the password do not touch the key; they concern session tokens only
  (`backend/open_webui/routers/auths.py:386-474`, `:955-1064`; no API-key call in either).
- A key has no expiry date in code; it lasts until replaced or deleted
  (`backend/open_webui/routers/auths.py:1529-1550`; `authentication-and-sign-in.md` section 6.3).
- A key that may have been exposed is a suspected security incident: see section 11.10.

### 5.16 The Interactive API Documentation

When the server runs with `ENV=dev`, FastAPI publishes an interactive page at `/docs` and the
machine-readable description at `/openapi.json`; with any other value both are absent, and there is
no `/redoc` page in either case (`backend/open_webui/main.py:506-511`; `backend/open_webui/env.py:139`).
`ENV` defaults to `dev` outside Docker and the Docker image sets `prod` (ground truth). Whether the
production deployment publishes these pages is **TO BE CONFIRMED**; a test environment is the place
for integrators to read them. The admin screen's documentation link points to the upstream site
(section 5.14).

### 5.17 OAuth Client Integrations and Token Exchange

Two OAuth features are easy to confuse with the API:

- **`OAuthClientManager` (MedIT GPT as the client).** When an admin adds an MCP tool server that
  needs each person to sign in (types **OAuth 2.1** and **OAuth 2.1 (Static)**), MedIT GPT registers
  itself with that server and keeps a per-person connection. The browser starts it at
  `/oauth/clients/mcp:<server id>/authorize` (signed-in `user` or `admin` only) and returns to
  `/oauth/clients/mcp:<server id>/callback` (`backend/open_webui/main.py:2772-2825`;
  `backend/open_webui/utils/oauth.py:829-1327`). This lets MedIT GPT call the tool on the person's
  behalf; it does not give outside programs a way into MedIT GPT. The person's view is in
  `sso-oauth-oidc-and-scim.md` section 5.13, the admin set-up in
  `workspace-tools-tool-servers-mcp-and-terminals.md`.
- **Token exchange (programs into MedIT GPT).** Off unless the maintainer sets
  `ENABLE_OAUTH_TOKEN_EXCHANGE=True` (`backend/open_webui/env.py:883`). A program that already holds
  an access token from the site's identity provider sends it to
  `POST /api/v1/auths/oauth/{provider}/token/exchange` and receives a MedIT GPT session token; the
  account must already exist and the exchange may be rate-limited
  (`backend/open_webui/routers/auths.py:1624-1771`). Steps and messages:
  `sso-oauth-oidc-and-scim.md` section 5.12. The resulting session token behaves like a browser
  session for API purposes (section 3.1).

### 5.18 Usage Reporting

- **Per request.** Token counts come in the reply's `usage` (OpenAI shape) or `usage` (Anthropic
  shape), as described in sections 5.5 and 5.10. Whether a provider reports them depends on the
  provider and, for streaming, on the model's **usage** capability
  (`backend/open_webui/main.py:1196-1198`).
- **Per key.** There is no usage counter, quota or rate limit for API keys in the code. The only
  request throttles in the backend are on password sign-in and token exchange (ground truth;
  `backend/open_webui/routers/auths.py:91-101`, `:818-822`, `:1642-1648`). The key's schema has
  fields for an expiry and a last-used time that no code fills in (`backend/open_webui/models/users.py:248-249`).
  Each successful key request does update the owner's last-active time, which admins see in the user
  list (`backend/open_webui/utils/auth.py:563`).
- **Dashboards.** The admin analytics count saved chat messages
  (`backend/open_webui/routers/analytics.py:67-98`), so plain API calls, which save nothing, are not
  expected to appear there (inferred; section 14). `GET /api/usage` reports models in use and active
  users, not tokens (`backend/open_webui/main.py:2621-2640`; `evaluations-feedback-and-analytics.md`).
- **Provider limits.** The model provider may enforce its own quotas; its refusal reaches the
  caller as HTTP 400 with the provider's text (section 5.5; `model-connections-openai-ollama-and-direct.md`
  section 11.5).
