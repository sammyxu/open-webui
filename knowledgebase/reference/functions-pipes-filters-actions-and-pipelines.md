# Functions (Pipes, Filters, Actions, Events) and Pipelines

## At a Glance

- Functions are administrator-managed Python plugins that run on the MedIT GPT server. There are
  four kinds: a **Pipe** appears to users as a model, a **Filter** changes requests and responses
  (globally or for chosen models), an **Action** is a button under an assistant message, and an
  **Event** function reacts to system events. (Provisional summary; refined at the end.)
- Functions are created, imported, enabled, made global and configured from the admin Functions
  page; users meet them only through models, buttons and their own user valves.
- Pipelines are a separate, external server added as an OpenAI-compatible connection; its filters
  and valves are managed from the admin Pipelines settings panel.
- *Added 2026-10-09 with sections 10 to 14:* failures reach people mainly as a grey error box in the
  chat (a pipe's or filter's own text), an action pop-up, or a model or button that has gone
  missing; several admin-screen failures show no message at all (the on/off switch, a blank name on
  save, an unreadable import file) (sections 10, 11).
- A function whose code fails to load is switched off automatically during ordinary use, and safe
  mode switches every function off at each start; start-up waits for `pip` to install the packages
  that switched-on functions list (sections 8, 11.2, 11.5, 11.15).
- This area matches upstream v0.11.4 apart from the product name; the fork's per-person **Hide
  Processing Details** setting hides the status lines functions send (section 12).
- Who handles escalations, whether production runs a Pipelines server, and which functions are
  installed are **TO BE CONFIRMED** (section 14).

## 1. Purpose and Who Uses It

**Functions** are small Python programs that an administrator installs into MedIT GPT. They are
stored in the database (the `function` table, section 6) and **run inside the MedIT GPT server
process**, with the server's own access. Because of that, every management screen and every
management API call for functions is restricted to administrators (section 3), and the interface
warns about it each time a function is created or imported: `Functions allow arbitrary code
execution.` and `Do not install functions from sources you do not fully trust.`
(`src/lib/components/admin/Functions/FunctionEditor.svelte:532-537`,
`src/lib/components/admin/Functions.svelte:826-831`).

The server decides what kind of function a piece of code is by the class it defines, checked in
this order: `Pipe`, `Filter`, `Action`, `Event` (`backend/open_webui/utils/plugin.py:296-306`).
Code with none of these classes is refused (`No Function class found in the module`,
`backend/open_webui/utils/plugin.py:305-306`).

| Type | What it does, in plain language | Where a user meets it |
|---|---|---|
| **Pipe** | Acts as a model. Instead of calling an AI provider, the chat request is handed to the function, which produces the answer itself (often by calling some other service). One pipe can offer several models at once (a "manifold"). | As one or more entries in the model picker; chatting with it looks like chatting with any other model (`backend/open_webui/functions.py:71-150`; `backend/open_webui/utils/chat.py:280-282`) |
| **Filter** | Changes or checks the conversation on the way to the model (`inlet`, `request`), each streamed piece of the answer (`stream`), or the finished answer (`outlet`). It can apply to every model ("global") or only to models an editor selected. Some filters are "toggleable": the user switches them on per chat. | Usually invisible. Toggleable filters appear as switches in the composer's **Integrations** menu and as pills beside the message box. A filter that rejects a message shows its error text under the reply (`backend/open_webui/utils/filter.py:59-106`, `:165-207`; `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:364-440`) |
| **Action** | A button under an assistant reply. Clicking it runs the function on that conversation; it can rewrite the message, show a pop-up, or add embedded content. | Icon buttons in the toolbar under replies of models that have the action (or under every model, when the action is global) (`src/lib/components/chat/Messages/ResponseMessage.svelte:1506-1545`; `backend/open_webui/utils/actions.py:19-153`) |
| **Event** | Reacts to system events (a function was enabled, a model was changed, a chat finished, and so on). It runs in the background on the server. | Nothing visible to users. Event types are listed in `notifications-webhooks-events-and-banners.md` (`backend/open_webui/events.py:1103-1171`) |

**Valves** are a function's settings form. Admin valves apply to everyone and are edited by an
administrator; **user valves** are per-person settings that a function may offer, which any
signed-in user can set for themselves (section 5.6).

**Pipelines** are a different mechanism with a similar purpose: a **separate Pipelines server**,
run outside MedIT GPT, which MedIT GPT reaches as an OpenAI-compatible connection. Its "pipe"
pipelines appear as ordinary models; its "filter" pipelines are called before and after chats with
the models they target. Administrators manage the pipelines on that server from **Admin Settings >
Pipelines** (`src/lib/components/admin/Settings/Pipelines.svelte`;
`backend/open_webui/routers/pipelines.py`). The code that runs there is outside MedIT GPT;
whether production uses a Pipelines server at all is **TO BE CONFIRMED** (section 14).

Who uses this area:

- **Administrators** install, edit, enable, disable, make global, configure, export and delete
  functions, and manage Pipelines servers.
- **Users** meet functions only through models (pipes), the composer (toggleable filters, valves
  buttons), the **Controls** panel (user valves) and reply toolbars (actions). They cannot see or
  change function code.
- **Tier 1 support** recognizes when a symptom comes from a function or pipeline (a model that is
  really a pipe, an error box raised by a filter, a missing action button) and escalates with the
  details listed in section 11. Tier 1 does not install, edit, toggle or configure functions.

Functions, tools and pipelines are three distinct things. Tools (and tool servers) are covered in
`workspace-tools-tool-servers-mcp-and-terminals.md`; the chat engine that calls filters and pipes
in `chat-completion-pipeline-and-generation-tasks.md`; models and their access in
`workspace-models-and-model-access.md`; connections (including how a Pipelines server is added) in
`model-connections-openai-ollama-and-direct.md`; event types, webhooks and notifications in
`notifications-webhooks-events-and-banners.md`.

## 2. Navigation and URLs

URLs are relative to the site root; the production host name is **TO BE CONFIRMED**.

### 2.1 Pages and Panels

| Where | URL or path in the interface | Who sees it | Evidence |
|---|---|---|---|
| **Admin Panel > Functions** (list of all functions) | `/admin/functions` | Administrators, and only when plugins are enabled on the server (`enable_plugins` in the configuration sent to the browser). Non-admins are sent to `/`; with plugins off the tab is hidden and the page redirects to `/admin` | `src/routes/(app)/admin/+layout.svelte:15-25`, `:87-95`; `src/routes/(app)/admin/functions/+page.svelte:9-13`; `backend/open_webui/main.py:2353` |
| **Create a function** (code editor) | `/admin/functions/create` | Administrators | `src/routes/(app)/admin/functions/create/+page.svelte:66-92` |
| **Edit a function** | `/admin/functions/edit?id={id}` | Administrators | `src/routes/(app)/admin/functions/edit/+page.svelte:65-83`; `src/lib/components/admin/Functions.svelte:151-153` |
| Old workspace link | `/workspace/functions/create` redirects to `/admin/functions/create` | Anyone who follows the old link; the target then applies the admin check | `src/routes/(app)/workspace/functions/create/+page.svelte:5-7` |
| **Admin Settings > Pipelines** | `/admin/settings/pipelines`, which opens the Settings window at `/?settings=admin:pipelines`; the tab sits in the **Tools** group of the administrator tabs | Administrators only (administrator tabs are added to the Settings window only for the `admin` role) | `src/routes/(app)/admin/settings/[tab]/+page.svelte:6-10`; `src/lib/components/chat/SettingsModal.svelte:169`, `:352-357`, `:407-409`, `:903-908` |
| **Workspace > Models > (model) > Filters, Default Filters, Actions** | The model editor | Whoever may edit the model; the selectors appear only when at least one filter or action function exists | `src/lib/components/workspace/Models/ModelEditor.svelte:1206-1242`; `workspace-models-and-model-access.md` |
| **Composer > Integrations** menu (toggleable filters, with a valves icon when the filter has user valves) | Chat page, icon button labelled `Integrations` | Every user, when the selected model has at least one toggleable filter | `src/lib/components/chat/MessageInput.svelte:811-814`, `:2295-2345`; `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:364-440` |
| **Composer > Valves** button (knobs icon) for a pipe model's user valves | Chat page, next to the Integrations button | Every user, when exactly one model is selected and it is a pipe model that offers user valves | `src/lib/components/chat/MessageInput.svelte:2347-2364` |
| **Chat > Controls > Valves** (user valves for any tool or function) | Chat page, **Controls** side panel, collapsible **Valves** section | Administrators, and users who have the `chat.controls` and `chat.valves` permissions (both default on) | `src/lib/components/chat/Controls/Controls.svelte:54`, `:93-106`; `backend/open_webui/config.py:1849-1851`, `:1979-1980` |
| **Action buttons** under a reply | Toolbar below each assistant message | Every user who can use the model; only actions that are active and either assigned to the model or global | `src/lib/components/chat/Messages/ResponseMessage.svelte:1506-1545`; `backend/open_webui/utils/models.py:385-419` |

The Functions list page title in the browser tab is `Functions / {WEBUI_NAME}`, which in this
deployment reads `Functions / MedIT GPT` unless `WEBUI_NAME` is set otherwise
(`src/lib/components/admin/Functions.svelte:314-316`; `backend/open_webui/env.py:951`).

### 2.2 Functions API (`/api/v1/functions`)

Mounted at `/api/v1/functions` (`backend/open_webui/main.py:876`).

| Method and path | Who may call it | Purpose | Evidence |
|---|---|---|---|
| `GET /api/v1/functions/` | Any signed-in user (`user` or `admin`) | List every function (id, name, type, description, active and global flags, dates; no code) | `backend/open_webui/routers/functions.py:48-53` |
| `GET /api/v1/functions/list` | Administrators | Same list plus each creator's name, email and role, newest first | `backend/open_webui/routers/functions.py:56-61`; `backend/open_webui/models/functions.py:234-260` |
| `GET /api/v1/functions/export?include_valves={true or false}` | Administrators | Full export including code; valves only when asked for | `backend/open_webui/routers/functions.py:69-78` |
| `POST /api/v1/functions/load/url` | Administrators | Fetch function code from a web address (GitHub page links are converted to raw-file links) | `backend/open_webui/routers/functions.py:86-151` |
| `POST /api/v1/functions/sync` | Administrators | Replace the whole function table with a supplied list (not used by the interface) | `backend/open_webui/routers/functions.py:159-192` |
| `POST /api/v1/functions/create` | Administrators | Create a function | `backend/open_webui/routers/functions.py:200-262` |
| `GET /api/v1/functions/id/{id}` | Administrators | Read one function including its code | `backend/open_webui/routers/functions.py:270-280` |
| `POST /api/v1/functions/id/{id}/toggle` | Administrators | Switch active on or off | `backend/open_webui/routers/functions.py:288-334` |
| `POST /api/v1/functions/id/{id}/toggle/global` | Administrators | Switch global on or off | `backend/open_webui/routers/functions.py:342-371` |
| `POST /api/v1/functions/id/{id}/update` | Administrators | Save new code, name or description | `backend/open_webui/routers/functions.py:379-424` |
| `DELETE /api/v1/functions/id/{id}/delete` | Administrators | Delete a function | `backend/open_webui/routers/functions.py:432-453` |
| `GET /api/v1/functions/id/{id}/valves`, `GET …/valves/spec`, `POST …/valves/update` | Administrators | Read, describe and save admin valves | `backend/open_webui/routers/functions.py:461-561` |
| `GET /api/v1/functions/id/{id}/valves/user`, `GET …/valves/user/spec`, `POST …/valves/user/update` | Any signed-in user, for their own values | Read, describe and save the caller's user valves | `backend/open_webui/routers/functions.py:569-668` |

### 2.3 Chat Endpoints That Run Functions

| Method and path | Who may call it | Purpose | Evidence |
|---|---|---|---|
| `POST /api/chat/actions/{action_id}` | Any signed-in user, for a chat they own (administrators for any chat; temporary chats are not checked; channel chats are refused) | Run an action button | `backend/open_webui/main.py:2071-2087`, `:2110-2124`; `backend/open_webui/utils/actions.py:19-153` |
| `POST /api/chat/completed` | Same ownership rule as above | **Deprecated**: runs outlet filters for older integrations; the chat engine now runs them itself | `backend/open_webui/main.py:2090-2107`; `backend/open_webui/utils/chat.py:311-375` |
| `POST /api/chat/completions` | Any signed-in user | Ordinary chat; pipes and filters run inside it | `chat-completion-pipeline-and-generation-tasks.md` |

### 2.4 Pipelines API (`/api/v1/pipelines`)

Mounted at `/api/v1/pipelines` (`backend/open_webui/main.py:847`). Every route is
administrator-only and, apart from `/list`, forwards the request to the Pipelines server chosen by
`urlIdx` (the position of that server in the OpenAI connection list).

| Method and path | Purpose | Evidence |
|---|---|---|
| `GET /api/v1/pipelines/list` | List the OpenAI connections that identify themselves as Pipelines servers | `backend/open_webui/routers/pipelines.py:204-220` |
| `POST /api/v1/pipelines/upload` | Upload a `.py` pipeline file to the chosen server | `backend/open_webui/routers/pipelines.py:223-308` |
| `POST /api/v1/pipelines/add` | Ask the chosen server to install a pipeline from a URL | `backend/open_webui/routers/pipelines.py:316-358` |
| `DELETE /api/v1/pipelines/delete` | Remove a pipeline from the chosen server | `backend/open_webui/routers/pipelines.py:366-408` |
| `GET /api/v1/pipelines/?urlIdx={n}` | List the pipelines installed on the chosen server | `backend/open_webui/routers/pipelines.py:411-443` |
| `GET /api/v1/pipelines/{pipeline_id}/valves?urlIdx={n}`, `GET …/valves/spec`, `POST …/valves/update` | Read, describe and save a pipeline's valves (held on the Pipelines server, not in MedIT GPT) | `backend/open_webui/routers/pipelines.py:446-573` |

## 3. Roles and Permissions

The roles are `admin`, `user` and `pending` (`tools/ground-truth.md`). Functions have **no
per-user or per-group permission key**: the default permission structure has `workspace.models`,
`workspace.tools` and similar keys but nothing for functions (`backend/open_webui/config.py:1940-2022`),
so only administrators manage them. Refusals from administrator-only routes answer HTTP 401 with
`You do not have permission to access this resource. Please contact your administrator for
assistance.` (`tools/ground-truth.md`, "Role checks answer 401, not 403").

### 3.1 What Each Role Can Do

| Capability | Admin | User | Pending | Evidence |
|---|---|---|---|---|
| Open **Admin Panel > Functions**, create, import, edit, clone, export, delete functions | Yes | No | No | `src/routes/(app)/admin/+layout.svelte:15-25`; every management route uses `get_admin_user` (`backend/open_webui/routers/functions.py:56-61`, `:69-78`, `:107-108`, `:163-169`, `:200-206`, `:270-271`, `:288-294`, `:342-348`, `:379-386`, `:432-438`) |
| Enable or disable a function; make a filter or action global | Yes | No | No | `backend/open_webui/routers/functions.py:288-371` |
| Set **admin valves** (apply to everyone) | Yes | No | No | `backend/open_webui/routers/functions.py:461-561` |
| See the list of functions (names, types, descriptions, flags; no code) | Yes | Yes | No | `backend/open_webui/routers/functions.py:48-53` (any `user` or `admin`) |
| Set **their own user valves** for an active function | Yes | Yes (interface shows it when `chat.controls` and `chat.valves` are on) | No | `backend/open_webui/routers/functions.py:569-668`; `src/lib/components/chat/Controls/Controls.svelte:54`, `:93` |
| Switch a toggleable filter on or off for a chat | Yes | Yes | No | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:364-440`; `backend/open_webui/utils/filter.py:76-85` |
| Click an action button | Yes, on any model the action is active for | Yes, when the action is active, assigned to the model (or global) and the user can use the model | No | `backend/open_webui/utils/actions.py:49-64` |
| Chat with a pipe model | Yes (a pipe model with no saved model settings is visible to administrators only) | When model access allows it (section 3.2) | No | `backend/open_webui/utils/models.py:524-575`; `workspace-models-and-model-access.md` |
| Attach filters and actions to a model in the model editor | Yes | Users who may edit that model (the editor lists every function, including ones that are switched off) | No | `src/lib/components/workspace/Models/ModelEditor.svelte:484-486`, `:1206-1242`; `workspace-models-and-model-access.md` |
| Manage **Pipelines** servers (upload, install from URL, delete, valves) | Yes | No | No | every route in `backend/open_webui/routers/pipelines.py` uses `get_admin_user` (`:205`, `:228`, `:317`, `:367`, `:412`, `:451`, `:498`, `:539`) |

### 3.2 How Functions Reach Users Through Models

- **Pipes.** A pipe becomes a base model (or several). Like any base model, it is shown to ordinary
  users only once it has a model record whose access settings include them, or through a custom
  model built on it; with no record, only administrators see it (unless model access control is
  bypassed by the environment) (`backend/open_webui/utils/models.py:524-575`;
  `tools/ground-truth.md`, admin visibility defaults). How records and access grants are set is in
  `workspace-models-and-model-access.md`.
- **Filters.** A filter runs for a model when it is **active** and either **global** or listed in
  the model's **Filters** (`meta.filterIds`) (`backend/open_webui/utils/filter.py:59-65`). It runs
  for every person who chats with that model; the filter's own code may treat people differently
  (the upstream example filter checks the role, `src/lib/components/admin/Functions/FunctionEditor.svelte:98-105`).
  A **toggleable** filter (one whose code sets `toggle`) runs only when the person has switched it on
  for the chat; the model's **Default Filters** decide which toggleable filters start switched on
  (`backend/open_webui/utils/filter.py:76-85`; `src/lib/components/chat/Chat.svelte:1075-1080`).
- **Actions.** An action button appears under replies when the action is **active** and either
  **global** or listed in the model's **Actions** (`meta.actionIds`)
  (`backend/open_webui/utils/models.py:385-419`).
- **Events.** Every active Event function receives every published event; the global switch does
  not apply to them (`backend/open_webui/events.py:1116`).
- **Global switch.** The admin menu offers **Global** only for filters and actions
  (`src/lib/components/admin/Functions/FunctionMenu.svelte:49-64`;
  `src/lib/components/admin/Functions.svelte:671-675`); the server does not check the type
  (`backend/open_webui/routers/functions.py:342-371`), and the flag has no effect on pipes and events.

### 3.3 Interface Checks Versus Server Checks

- The **Valves** section of the chat **Controls** panel and the valves icon beside toggleable
  filters are hidden for non-admins without the `chat.valves` permission
  (`src/lib/components/chat/Controls/Controls.svelte:93`;
  `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:415`;
  `src/lib/components/chat/MessageInput.svelte:2425-2433`). The composer's **Valves** button for a
  pipe model does not look at that permission (`src/lib/components/chat/MessageInput.svelte:2347-2364`).
  Whether the server enforces `chat.valves` on the user-valves routes is not described here
  (section 14).
- The **Import JSON** and **Export JSON** entries in the Functions page's create button are shown
  only to administrators (`src/lib/components/admin/Functions.svelte:375-386`), which matches the
  page being administrator-only.

## 4. Key Concepts and Terminology

| Term | Meaning in MedIT GPT | Evidence |
|---|---|---|
| **Function** | An administrator-installed Python plugin stored in the `function` table and run inside the server. Its type (pipe, filter, action, event) comes from the class its code defines | `backend/open_webui/models/functions.py:19-34`; `backend/open_webui/utils/plugin.py:296-306` |
| **Function ID** | The function's permanent identifier, chosen at creation. Letters, digits and underscores only, stored in lower case; it cannot be changed afterwards (the editor shows it read-only when editing) | `backend/open_webui/routers/functions.py:207-213`; `src/lib/components/admin/Functions/FunctionEditor.svelte:403-423` |
| **Pipe** | A function whose `pipe` method answers chat requests itself; it appears as a model whose id is the function id | `backend/open_webui/functions.py:125-145`, `:300-358` |
| **Manifold** | A pipe that lists several sub-models (its `pipes` list or method). Each sub-model's id is `{function id}.{sub id}`; an optional `name` on the pipe is put in front of each sub-model name | `backend/open_webui/functions.py:86-124` |
| **Filter** | A function with one or more hooks: `inlet` (before the request is built into the model call), `request` (just before each call to the model, including calls after tool use), `stream` (each streamed chunk), `outlet` (the finished messages) | `backend/open_webui/utils/filter.py:135-144`, `:165-207`; `backend/open_webui/utils/middleware.py:2655-2670`, `:3261-3272`, `:5101-5109`, `:4050-4208`, `:6285-6293` |
| **Global** | A flag on a filter or action that applies it to every model | `backend/open_webui/models/functions.py:30`; `backend/open_webui/utils/filter.py:59-65`; `backend/open_webui/utils/models.py:385-399` |
| **Active (enabled)** | A flag that turns a function on. New functions start **off**; an inactive function is ignored everywhere | `backend/open_webui/models/functions.py:29`, `:50`; `backend/open_webui/utils/filter.py:64-65` |
| **Toggleable filter** | A filter whose code sets `toggle`; the server then records `toggle` in the function's metadata. Users switch it on per chat; it runs only when switched on | `backend/open_webui/routers/functions.py:233-234`, `:400-401`; `backend/open_webui/utils/filter.py:76-82` |
| **Default Filters** | Toggleable filters a model starts with switched on in a new chat | `src/lib/components/workspace/Models/DefaultFiltersSelector.svelte:29-104`; `src/lib/components/chat/Chat.svelte:1075-1080` |
| **Filter priority** | A `priority` valve (number) that orders filters, lowest first, then by id; filters without one count as 0 | `backend/open_webui/utils/filter.py:88-103` |
| **File handler** | A filter flag (`file_handler`) telling the chat engine the filter deals with attached files itself, so the engine removes the files from the request after the inlet hooks | `backend/open_webui/utils/filter.py:184-186`, `:243-248` |
| **Action** | A function with an `action` method, shown as a button under assistant replies. An action can offer several buttons through an `actions` list (ids `{function id}.{sub id}`) | `backend/open_webui/utils/actions.py:23-26`, `:89-127`; `backend/open_webui/utils/models.py:280-298` |
| **Action priority** | A `priority` valve that orders action buttons, lowest first, then by id | `backend/open_webui/utils/models.py:368-392` |
| **Event function** | A function with an `event` method, called for every published system event while it is active | `backend/open_webui/events.py:1103-1156` |
| **Valves** | Settings defined by the function (a `Valves` class). Administrators edit them; values are saved in the function's `valves` column. Each field shows **Default** (use the function's own default) or **Custom** (a value is saved); a required field shows **None** until set | `backend/open_webui/routers/functions.py:461-561`; `src/lib/components/common/Valves.svelte:36-72` |
| **User valves** | Per-person settings defined by a `UserValves` class. Each person's values are kept in their own user settings, under `functions.valves.{function id}` | `backend/open_webui/models/functions.py:354-396`; `backend/open_webui/routers/functions.py:569-668` |
| **Valves spec** | The description of a function's valves (field names, types, descriptions, choices) that the server sends to the browser to draw the form. Special input types: drop-down (`select`), multi-select, password (hidden text), colour picker, and an experimental map picker | `backend/open_webui/routers/functions.py:487-509`; `backend/open_webui/utils/plugin.py:27-148`; `src/lib/components/common/Valves.svelte:79-226` |
| **Frontmatter (manifest)** | The opening comment block of a function's code (`"""` on the first line, then `key: value` lines). Recognized keys include `title`, `description`, `version`, `author`, `funding_url`, `icon_url`, `requirements` and `required_open_webui_version`. The server stores it as `meta.manifest` | `backend/open_webui/utils/plugin.py:151-184`; `backend/open_webui/routers/functions.py:223`, `:390`; `src/lib/components/admin/Functions.svelte:533-539`, `:600-616`; `backend/open_webui/utils/models.py:289-292` |
| **Requirements** | A comma-separated list of Python packages in the frontmatter. The server installs them with `pip` when the function is saved, when it is loaded, and for all active functions at startup | `backend/open_webui/utils/plugin.py:271-275`, `:422-450`, `:453-484`; `backend/open_webui/main.py:385-388` |
| **Safe mode** | An environment switch (`SAFE_MODE`) that switches **every** function off at startup | `backend/open_webui/env.py:965`; `backend/open_webui/main.py:280-282`, `:382-383` |
| **Plugins switch** | The environment switch `ENABLE_PLUGINS` (default on). When off, functions and workspace tools are not loaded or listed, and the Functions page is hidden | `backend/open_webui/env.py:1186`; `backend/open_webui/utils/plugin.py:260-261`; `src/routes/(app)/admin/+layout.svelte:87-95` |
| **Function cache** | Each server worker keeps loaded functions in memory and reloads one when its stored code changes | `backend/open_webui/utils/plugin.py:318-337`, `:375-416` |
| **Pipelines server** | An external service, added as an OpenAI-compatible connection, that answers its model list with a `pipelines` marker. MedIT GPT shows a Pipelines icon on that connection | `backend/open_webui/routers/pipelines.py:204-220`; `src/lib/components/admin/Settings/Connections.svelte:192-201`; `src/lib/components/admin/Settings/Connections/OpenAIConnection.svelte:68-89` |
| **Pipeline (pipe type)** | A pipeline on that server offered as a model | `src/lib/components/admin/Settings/Pipelines.svelte:378-381` |
| **Pipeline filter** | A pipeline of type `filter`. It is never offered as a chat model; it is called before (`inlet`) and after (`outlet`) chats with the models in its target list (`*` means all models), in order of its `priority` | `backend/open_webui/main.py:900-903`; `backend/open_webui/routers/pipelines.py:41-54`, `:63-192` |
| **`urlIdx`** | The position of a Pipelines server in the list of OpenAI connections; the Pipelines panel uses it to choose the server | `backend/open_webui/routers/pipelines.py:57-60` |
| **Community** | The upstream sharing site `openwebui.com`. **Share** in a function's menu opens it; a **Discover a function** link appears when community sharing is enabled. Whether MedIT GPT staff should use it is TO BE CONFIRMED | `src/lib/components/admin/Functions.svelte:158-186`, `:744-750` |

Plain-language reminder for support staff: **"function"** in this document always means one of
these administrator-installed plugins. The model's ability to call tools ("function calling") is a
different feature, documented in `chat-completion-pipeline-and-generation-tasks.md` and
`workspace-tools-tool-servers-mcp-and-terminals.md`.

## 5. Workflows (Step by Step)

Tier 1 is read-only: the administrator workflows below are described so support can tell a user
or an administrator what should have happened and what to check. Tier 1 does not perform them.

### 5.1 Create a Function (Administrator)

1. Open **Admin Panel > Functions** (`/admin/functions`). The create button offers **Create**,
   **Import From Link**, **Import JSON** and **Export JSON**
   (`src/lib/components/admin/Functions.svelte:361-388`). Choose **Create**.
2. The editor opens (`/admin/functions/create`) with starter code. A drop-down labelled
   `Function starter` offers **Filter** (the default) or **Event** starter code; there is no pipe or
   action starter (`src/lib/components/admin/Functions/FunctionEditor.svelte:159-172`, `:447-457`).
3. Fill **Function Name**, **Function ID** and **Function Description**. While creating, the ID
   follows the name until edited, and a `title` or `description` line in the code's opening
   comment fills an empty name or description
   (`src/lib/components/admin/Functions/FunctionEditor.svelte:45-47`, `:392-438`, `:477-488`).
4. Click **Save & Create** (or press Ctrl+S / Cmd+S in the editor). A confirmation dialog repeats
   the warnings (`Functions allow arbitrary code execution.`, `Do not install functions from sources
   you do not fully trust.`) and the acknowledgement text; confirm it
   (`src/lib/components/admin/Functions/FunctionEditor.svelte:368-378`, `:524-546`).
5. The browser sends the code to the server's Python formatter. On success a `Code formatted
   successfully` toast appears; on failure (usually a syntax error) the formatter's message is shown
   as a toast and the unformatted code is saved anyway
   (`src/lib/components/common/CodeEditor.svelte:181-208`;
   `src/lib/components/admin/Functions/FunctionEditor.svelte:347-364`;
   `backend/open_webui/routers/utils.py:30-38`).
6. If the code's opening comment sets `required_open_webui_version` higher than this version
   (0.11.4), an error toast names both versions and nothing is saved
   (`src/routes/(app)/admin/functions/create/+page.svelte:19-38`; `src/lib/utils/index.ts:660-668`).
7. The server checks the ID (`Only alphanumeric characters and underscores are allowed in the id`),
   lower-cases it, refuses an ID already in use, installs any `requirements` listed in the code,
   loads the code to find its type, stores the opening comment as the manifest, and records the
   toggle flag for toggleable filters. It also creates a cache folder for the function and
   publishes a `function.created` event (`backend/open_webui/routers/functions.py:200-262`).
8. On success the toast `Function created successfully` appears and the browser returns to the
   list (`src/routes/(app)/admin/functions/create/+page.svelte:50-63`). **The new function is
   switched off**; it does nothing until an administrator switches it on (section 5.5)
   (`backend/open_webui/models/functions.py:29`, `:50`).

### 5.2 Import a Function From a Link (Administrator)

1. Choose **Import From Link**. A dialog titled **Import** asks for a **URL**
   (`src/lib/components/ImportModal.svelte:67-113`).
2. On **Import**, the server downloads the code. GitHub page links are rewritten to raw-file links;
   a folder link gets `main.py` added. The function's name is taken from the file name, or from the
   folder name for `main.py`, `index.py` and `__init__.py`
   (`backend/open_webui/routers/functions.py:90-127`).
3. The toast `Function imported successfully` appears and the create editor opens with the code
   filled in (`src/lib/components/ImportModal.svelte:37-59`;
   `src/lib/components/admin/Functions.svelte:319-330`). **Nothing is saved yet**: the
   administrator must still click **Save & Create** and confirm (section 5.1, step 4 onward).

### 5.3 Import or Export Several Functions; Clone (Administrator)

- **Import JSON** opens a file picker for `.json` files, then a confirmation dialog with the same
  warnings. Each function in the file is created through the normal create route; a failure shows
  its error as a toast and the import continues. When the loop ends the toast `Functions imported
  successfully` appears **even if some or all functions failed** (`src/lib/components/admin/Functions.svelte:336-347`,
  `:786-840`). Only the id, name, code and metadata travel (the description, any translations of
  the name, description and valve labels, and other metadata keys; the manifest is re-read from the
  code): imported functions start switched off, not global, and with default valves
  (`backend/open_webui/models/functions.py:37-40`, `:98-102`; `backend/open_webui/routers/functions.py:223`).
  *Corrected 2026-10-09: the first version said only the description travelled with the code; the
  whole `meta` object is accepted, so translations are imported too.*
- **Export JSON** downloads `functions-export-{timestamp}.json` with every function's code and
  settings flags, without valves (`src/lib/components/admin/Functions.svelte:89-101`;
  `backend/open_webui/routers/functions.py:69-78`). A single function's **Export** (in its `...`
  menu) downloads `function-{id}-export-{timestamp}.json` (`src/lib/components/admin/Functions.svelte:204-216`).
- **Clone** (in the `...` menu) opens the create editor with the ID `{id}_clone` and the name
  `{name} (Clone)`; it is saved only when the administrator clicks **Save & Create**
  (`src/lib/components/admin/Functions.svelte:188-202`).

### 5.4 Edit a Function (Administrator)

1. Click a row in the list, or **Edit** in its `...` menu (`/admin/functions/edit?id={id}`)
   (`src/lib/components/admin/Functions.svelte:151-153`, `:498-513`).
2. Change the name, description or code and click **Save**. Editing has no confirmation dialog;
   the code is formatted first, and the required-version check applies (section 5.1, steps 5-6)
   (`src/lib/components/admin/Functions/FunctionEditor.svelte:371-377`;
   `src/routes/(app)/admin/functions/edit/+page.svelte:20-63`).
3. The server installs any requirements, loads the new code, and saves it with the type the code
   now declares (`backend/open_webui/routers/functions.py:379-424`).
   - **If the new code cannot be loaded, the server switches the function off and keeps the old
     code.** The administrator sees `[ERROR: Error updating function]`
     (`backend/open_webui/utils/plugin.py:307-313`; `backend/open_webui/routers/functions.py:418-424`).
4. On success the toast `Function updated successfully` appears and the page stays open
   (`src/routes/(app)/admin/functions/edit/+page.svelte:51-62`). Other server workers pick up the
   new code the next time they use the function, because they compare the stored code with what they
   hold in memory (`backend/open_webui/utils/plugin.py:382-403`).

### 5.5 Switch a Function On or Off; Make It Global (Administrator)

- **On or off.** Each row ends with a switch whose tooltip reads `Enabled` or `Disabled`
  (`src/lib/components/admin/Functions.svelte:694-719`). Changing it calls the server and reloads
  the model list. **No toast confirms the change and a failure is not reported**: the switch moves
  even if the server refused (`src/lib/components/admin/Functions.svelte:703-716`). Before the
  change is saved, the server sends a `function.enable_started` or `function.disable_started`
  event to Event functions (including the Event function being switched on) and to webhooks;
  after it, it publishes `function.enabled` or `function.disabled`
  (`backend/open_webui/routers/functions.py:288-334`).
- **Global.** For filters and actions, the `...` menu has a **Global** switch
  (`src/lib/components/admin/Functions/FunctionMenu.svelte:49-64`). The toasts read `Filter is now
  globally enabled`, `Filter is now globally disabled`, `Function is now globally enabled` or
  `Function is now globally disabled` (the last two are used for actions)
  (`src/lib/components/admin/Functions.svelte:240-266`). A global filter or action still does
  nothing while the function itself is switched off (`backend/open_webui/utils/models.py:385-399`).

### 5.6 Set Valves

**Admin valves (administrator).**

1. On the Functions list, click the gear icon (tooltip `Valves`) on a row
   (`src/lib/components/admin/Functions.svelte:618-650`).
2. A **Valves** dialog shows one entry per setting. Each entry shows **Default** (no value saved;
   the function's own default applies) or **Custom** (click to enter a value); a required setting
   shows **None** until set. Lists are typed as comma-separated text
   (`src/lib/components/common/Valves.svelte:24-240`;
   `src/lib/components/workspace/common/ValvesModal.svelte:52-155`).
3. Click **Save**. The server checks the values against the function's settings definition and
   stores only the ones that are set; the toast `Valves updated successfully` appears and the model
   list reloads (`backend/open_webui/routers/functions.py:517-561`;
   `src/lib/components/admin/Functions.svelte:768-784`).
4. A function without settings shows `No valves`; if the settings cannot be loaded, the toast
   `Error fetching valves` appears and the dialog closes
   (`src/lib/components/common/Valves.svelte:241-243`;
   `src/lib/components/workspace/common/ValvesModal.svelte:151-154`).
   *Corrected 2026-10-09: the toast appears only when the server answers with an error text. When
   the function's code cannot be loaded, the server answers without one, so the dialog shows
   `No valves` instead and the loader switches the function off
   (`src/lib/apis/functions/index.ts:356-386`; `backend/open_webui/utils/plugin.py:307-313`;
   section 10.3).*

**User valves (any signed-in user, for themselves).** Three places lead to the same settings:

| Entry point | How it saves | Evidence |
|---|---|---|
| Chat **Controls** panel > **Valves**: choose **Functions**, then the function (`Select a function`) | Automatically, half a second after each change; toast `Valves updated` | `src/lib/components/chat/Controls/Valves.svelte:41-117`, `:157-200` |
| Composer **Integrations** menu > knobs icon beside a toggleable filter, or a click on the filter's pill | **Save** button in the **Valves** dialog; toast `Valves updated successfully` | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:415-433`; `src/lib/components/chat/MessageInput.svelte:1643-1653`, `:2424-2433` |
| Composer **Valves** button (knobs) when a pipe model with user valves is selected | Same dialog | `src/lib/components/chat/MessageInput.svelte:2347-2364` |

The Controls drop-down lists **every** function, including ones that are switched off or have no
user settings; those show `No valves` (`src/lib/components/chat/Controls/Valves.svelte:189-198`;
`backend/open_webui/routers/functions.py:590-615`). Saving user valves for a switched-off function
is refused with `Function is not active` (`backend/open_webui/routers/functions.py:628-633`).
User valves are personal: they are stored in that person's own settings and apply only to their
chats (`backend/open_webui/models/functions.py:375-396`).

### 5.7 Delete a Function (Administrator)

1. In the `...` menu choose **Delete**. The dialog `Delete function?` says `This will delete
   {name}.`; confirm (`src/lib/components/admin/Functions.svelte:753-765`).
2. The toast `Function deleted successfully` appears and the function and model lists reload
   (`src/lib/components/admin/Functions.svelte:218-238`).
3. **Holding the Shift key** replaces each row's controls with a bin icon that deletes **at once,
   without the confirmation dialog** (`src/lib/components/admin/Functions.svelte:584-598`).
4. There is no undo; export first if the code may be needed again. The server removes the row and
   its in-memory copy and publishes `function.deleted` (`backend/open_webui/routers/functions.py:432-453`).
   People's saved user valves for the function and model settings that list it are left in place;
   the model list ignores ids it cannot find (`backend/open_webui/models/functions.py:431-439`;
   `backend/open_webui/utils/models.py:403-430`).

### 5.8 Share With the Community, Support a Function Author

- **Share** in the `...` menu shows `Redirecting you to Open WebUI Community` and opens
  `openwebui.com` in a new tab, passing the function's details (including its code) to that site
  (`src/lib/components/admin/Functions.svelte:158-186`). Whether MedIT GPT administrators may share
  functions publicly is **TO BE CONFIRMED**.
- When a function's opening comment has a `funding_url`, a heart button (tooltip `Support`) opens
  a dialog titled `Show your support!` with a link to that address
  (`src/lib/components/admin/Functions.svelte:600-616`;
  `src/lib/components/workspace/common/ManifestModal.svelte:19-61`).
- When community sharing is on, a **Discover a function** link to `openwebui.com/functions` appears
  at the bottom of the list (`src/lib/components/admin/Functions.svelte:744-750`).
- In the editor, a language selector switches the name, description and valve labels into
  translation mode for other interface languages; if the valve definitions cannot be read, the text
  `Failed to load valves` appears with a **Retry** button
  (`src/lib/components/admin/Functions/FunctionEditor.svelte:442-470`;
  `src/lib/components/workspace/common/PluginTranslations.svelte:25-64`).

### 5.9 Chat With a Pipe Model (User)

1. The person picks the pipe's model in the model picker. A single pipe appears under the
   function's name with the function ID as model id; a manifold appears as several models with ids
   `{function id}.{sub id}` (`backend/open_webui/functions.py:105-145`).
2. On **Send**, the chat engine does its usual preparation (filters, knowledge, tools; see
   `chat-completion-pipeline-and-generation-tasks.md`) and then hands the request to the pipe
   instead of to a provider (`backend/open_webui/utils/chat.py:280-282`).
3. When the pipe model has saved model settings, those settings (parameters and system prompt) are
   applied and the person's access to the model is checked again
   (`backend/open_webui/functions.py:284-298`).
4. The pipe receives the conversation, the person's account record (name, email, role and profile
   fields), its admin valves and the person's user valves, and the chat's context; it can send
   status lines and ask the browser for input while it works
   (`backend/open_webui/functions.py:52-68`, `:195-213`, `:233-282`). See section 6.4 on personal
   data.
5. The answer streams into the chat like any model's. If the pipe raises an error, the error text
   is sent as the answer's error (`backend/open_webui/functions.py:321-324`, `:348-350`); how it is
   displayed is described in section 11.1.

Pipes are also used for background work (titles, tags, follow-ups) when a pipe model is the chat's
model or the **Task Model**; the request then carries the task's name, so pipe code can tell
(`backend/open_webui/functions.py:242-243`, `:274-275`; `chat-completion-pipeline-and-generation-tasks.md`, section 5.10).

### 5.10 Filters During a Chat

The chat engine calls filters at fixed points of each turn. Within each point, filters run in
priority order (section 4). Pipelines filters (section 5.13) run before function filters on the
way in and before them on the way out.

| Point | When | If the filter fails | Evidence |
|---|---|---|---|
| `inlet` | After the message is received, before knowledge, web search, tools and features are added | The turn stops; the filter's error text appears in the reply's error box | `backend/open_webui/utils/middleware.py:2649-2670`; `backend/open_webui/main.py:1686-1713` |
| `request` | Just before the model is called, and again before each further call after tool use or code interpreter runs | First call: the turn stops with the error text. Later calls: the error text is shown and the tool loop ends | `backend/open_webui/utils/middleware.py:3261-3272`, `:3580-3601`, `:6285-6293`, `:6333-6337`, `:6506-6514`, `:6532-6536` |
| `stream` | For each streamed chunk of the answer | That chunk is dropped and streaming continues, so words can go missing; logged | `backend/open_webui/utils/middleware.py:5101-5109`, `:5727-5733`; `backend/open_webui/utils/filter.py:200-205` |
| `outlet` | After the answer is complete (and saved) | Nothing is shown; the answer stays as the model wrote it. A failure stops the remaining outlet filters too | `backend/open_webui/utils/middleware.py:4050-4208` |

- When an outlet filter changes a message, the new text is saved and the original is kept as
  `originalContent`; the browser receives a `chat:outlet` update
  (`backend/open_webui/utils/middleware.py:4173-4206`).
- **Toggleable filters**: the composer's **Integrations** menu lists the toggleable filters shared
  by all selected models, each with a switch; a switched-on filter also shows as a pill beside the
  message box. Clicking a pill opens the filter's user valves when it has some (and the person may
  edit valves); otherwise it switches the filter off. The model's **Default Filters** start
  switched on (`src/lib/components/chat/MessageInput.svelte:811-814`, `:2413-2480`;
  `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:364-440`;
  `src/lib/components/chat/Chat.svelte:1075-1080`). The chosen ids travel with the request as
  `filter_ids` (`src/lib/components/chat/Chat.svelte:3591`), and the server runs a toggleable filter
  only when its id is among them (`backend/open_webui/utils/filter.py:76-85`).
- Background tasks (titles, tags, follow-ups) pass through Pipelines inlet filters but **not**
  through function filters (`chat-completion-pipeline-and-generation-tasks.md`, section 5.10).
- Requests made through the API without a browser session also run stream filters and, when
  `ENABLE_API_OUTLET_FILTERS` is on (default), outlet filters at the end
  (`backend/open_webui/utils/middleware.py:4416-4423`, `:6644-6706`; `backend/open_webui/env.py:1052`).

### 5.11 Click an Action Button (User)

1. The person clicks an action's icon in the toolbar under a reply. Its tooltip is the action's
   name; actions without an icon show a sparkle icon
   (`src/lib/components/chat/Messages/ResponseMessage.svelte:1506-1545`).
2. The browser sends the conversation up to that reply (ids, roles, text, timestamps and sources),
   the model, the chat id and the reply id to `/api/chat/actions/{action id}`
   (`src/lib/components/chat/Chat.svelte:2571-2589`).
3. The server checks that the chat belongs to the person (administrators excepted), that plugins
   are on, that the function exists, is an action and is switched on, that the model is known, and,
   for non-administrators, that the person may use the model and that the action is assigned to it
   or global (`backend/open_webui/main.py:2110-2124`; `backend/open_webui/utils/actions.py:19-64`).
4. The action runs with its admin valves and the person's user valves. It can update the messages,
   show status lines, ask for input, or return embedded content
   (`backend/open_webui/utils/actions.py:66-148`).
5. If the action returns messages, the chat updates them (the old text is kept as
   `originalContent`) and saves the chat (`src/lib/components/chat/Chat.svelte:2595-2618`).
6. If it fails, a toast shows the error text and the error is attached to the reply
   (`src/lib/components/chat/Chat.svelte:2590-2594`; section 11.4).

The **Regenerate** button also prepares a `regenerate-response` notice for every action of the
model, but no component in this version listens for it, so actions do not run on regenerate
(`src/lib/components/chat/Messages/ResponseMessage.svelte:1399-1414`; no `on:action` handler exists
under `src/lib/components/chat/`).

### 5.12 Event Functions React to System Events

1. Whenever the server publishes an event (for example `function.enabled`, `model.updated`,
   `chat.finished`), it hands the event to several receivers: user-session handling, Event
   functions, webhooks and in-app notifications (`backend/open_webui/events.py:1166-1202`).
2. For Event functions, a background task calls the `event` method of **every active Event
   function** with the event's name, id, the acting person's id, name, email and role, the subject
   and the event data (`backend/open_webui/events.py:1103-1171`, `:704`, `:974-985`).
3. A failure is logged as `Event function failed for {id}` and has no effect on the person who
   caused the event (`backend/open_webui/events.py:1155-1156`).
4. Switching any function on or off sends a `function.enable_started` or `function.disable_started`
   event to Event functions **before** the change and waits for them, so a slow Event function
   slows the switch (`backend/open_webui/routers/functions.py:297-311`).

The list of event names and their payloads is documented in
`notifications-webhooks-events-and-banners.md`.

### 5.13 Add a Pipelines Server (Administrator)

1. A Pipelines server is added in **Admin Settings > Connections** as an OpenAI-compatible
   connection with its URL and key (`model-connections-openai-ollama-and-direct.md`).
2. When that connection's model list answers with the `pipelines` marker, the connection shows a
   Pipelines icon and the server appears in **Admin Settings > Pipelines**
   (`src/lib/components/admin/Settings/Connections.svelte:192-201`;
   `src/lib/components/admin/Settings/Connections/OpenAIConnection.svelte:68-89`;
   `backend/open_webui/routers/pipelines.py:204-220`).
3. With no such connection, the panel shows `Pipelines Not Detected`
   (`src/lib/components/admin/Settings/Pipelines.svelte:473-479`).

### 5.14 Manage Pipelines (Administrator)

In **Admin Settings > Pipelines** (`src/lib/components/admin/Settings/Pipelines.svelte:251-500`):

| Section and field (English labels) | What it does | Messages |
|---|---|---|
| **Source > Pipeline URL** (`Select the Pipelines server to manage.`) | Chooses which Pipelines server the rest of the panel manages; the first one is selected on opening | — |
| **Source > Upload Pipeline** (`Upload a local Python pipeline file to the selected server.`) | **Select a .py file**, then **Upload**. The server accepts only `.py` files, forwards the file to the Pipelines server and deletes its temporary copy | `{{COUNT}} pipeline(s) selected`, `Uploading`, success `Pipeline downloaded successfully`, failure `Something went wrong :/`, no file `No file selected` |
| **Source > GitHub URL** (description `Pipelines are a plugin system with arbitrary code execution.` `Don't fetch random pipelines from sources you don't trust.`) | Enter a raw file address (`Enter GitHub Raw URL`) and click **Install**; the Pipelines server downloads it | `Installing`, success `Pipeline downloaded successfully`, failure: the server's message or `Pipeline not found` |
| **Pipelines > Pipeline** (`Select an installed pipeline to configure or remove.`) | Lists installed pipelines as `{name} ({type})`; **Delete** removes the selected one | success `Pipeline deleted successfully`; failure: the server's message or `Pipeline not found` |
| **Valves** | The selected pipeline's settings, each with **None** or **Custom**; choices show as a drop-down, yes/no as a switch, anything else as a required text box; lists as comma-separated text. **Save** stores them on the Pipelines server | `Valves updated successfully` followed by `Settings saved successfully!`; `No valves to update`; `No valves` |

Every successful change reloads the model list (`src/lib/components/admin/Settings/Pipelines.svelte:75-87`,
`:149-160`, `:181-192`, `:224-235`). The labels resolve from dotted keys in
`src/lib/i18n/locales/en-US/translation.json:2618-2631`.

### 5.15 What a Pipelines Server Does in a Chat

- **Pipe pipelines** are models reached through the OpenAI connection. For them, MedIT GPT adds
  the person's name, id, email and role to the request (`backend/open_webui/routers/openai.py:1559-1566`).
- **Filter pipelines** are never offered as chat models (`backend/open_webui/main.py:900-903`).
  Before the model is called (inlet) and after the answer is complete (outlet), MedIT GPT sends the
  person's id, email, name and role with the request or the messages to each filter pipeline that
  targets the chat's model (or all models), in priority order. When the chat's model is itself a
  pipeline, it is also called as a filter: last on the way in, first on the way out
  (`backend/open_webui/routers/pipelines.py:41-54`, `:63-192`).
- A filter pipeline is **skipped without notice** when its connection has no key, and when the
  Pipelines server cannot be reached (only a `Connection error: …` log line is written); the message
  then goes on unfiltered (`backend/open_webui/routers/pipelines.py:77-87`, `:121-124`, `:143-153`,
  `:187-190`).
- When the Pipelines server answers an inlet call with an error status, the turn stops and the
  reply's error box shows the server's `detail` or the HTTP reason
  (`backend/open_webui/routers/pipelines.py:104-120`; `chat-completion-pipeline-and-generation-tasks.md`).
  Outlet errors are logged at debug level only (`backend/open_webui/utils/middleware.py:4144-4148`).

## 6. Data Model

### 6.1 The `function` Table

One row per function (`backend/open_webui/models/functions.py:19-34`; created by the initial
migration, `backend/open_webui/migrations/versions/7e5b5dc7342b_init.py:78-94`; index added by
`backend/open_webui/migrations/versions/018012973d35_add_indexes.py:44-46`).

| Column | Type | Meaning | Evidence |
|---|---|---|---|
| `id` | text, primary key | The function ID (lower case, letters, digits, underscores) | `backend/open_webui/models/functions.py:22`; `backend/open_webui/routers/functions.py:207-213` |
| `user_id` | text, indexed | The administrator who created it, or who last ran a bulk sync. May point to a deleted account; the list then shows `Deleted User` | `backend/open_webui/models/functions.py:23`, `:159-163`; `src/lib/components/admin/Functions.svelte:567-581` |
| `name` | text | Display name | `backend/open_webui/models/functions.py:24` |
| `type` | text | `pipe`, `filter`, `action` or `event`, decided by the code, not chosen by hand | `backend/open_webui/models/functions.py:25`; `backend/open_webui/utils/plugin.py:296-306` |
| `content` | text | The Python code | `backend/open_webui/models/functions.py:26` |
| `meta` | JSON | `description`; `manifest` (the parsed opening comment); `toggle` (set to true for toggleable filters); `i18n` (translations of name, description and valve labels) | `backend/open_webui/models/functions.py:27`, `:37-40`; `backend/open_webui/routers/functions.py:223`, `:233-234`, `:390`, `:400-401`; `src/lib/components/admin/Functions/FunctionEditor.svelte:336-341` |
| `valves` | JSON | The admin valve values (only the settings an administrator set). How valves are protected at rest is not described here (section 14) | `backend/open_webui/models/functions.py:28`, `:319-330` |
| `is_active` | boolean, default false | Switched on or off | `backend/open_webui/models/functions.py:29` |
| `is_global` | boolean, indexed (`is_global_idx`) | Applies to every model (filters and actions) | `backend/open_webui/models/functions.py:30`, `:34` |
| `updated_at`, `created_at` | integer (epoch seconds) | Times of last change and creation; any change to code, flags or valves updates `updated_at` | `backend/open_webui/models/functions.py:31-32`, `:326`, `:345`, `:408` |

Once set, `meta.toggle` is never set back to false by the code, even if a later version of the
filter stops being toggleable (`backend/open_webui/routers/functions.py:233-234`, `:400-401`;
`backend/open_webui/models/functions.py:332-352`).

### 6.2 Data Kept Elsewhere

| Data | Where | Evidence |
|---|---|---|
| Each person's user valves | The `settings` JSON of that person's `user` row, under `functions` > `valves` > `{function id}` | `backend/open_webui/models/functions.py:354-396`; `backend/open_webui/models/users.py:138-141` |
| Which filters, default filters and actions a model uses | The model record's `meta.filterIds`, `meta.defaultFilterIds`, `meta.actionIds` | `src/lib/components/workspace/Models/ModelEditor.svelte:361-382`; `workspace-models-and-model-access.md` |
| Toggleable filters chosen for a chat | Sent with each request as `filter_ids`; also kept in the browser's saved draft of the composer and restored from it | `src/lib/components/chat/Chat.svelte:760-768`, `:3591` |
| Loaded function code | Memory of each server worker (`FUNCTIONS`, `FUNCTION_CONTENTS`); reloaded when the stored code differs | `backend/open_webui/utils/plugin.py:318-337`, `:375-416` |
| A per-function folder | `{CACHE_DIR}/functions/{id}`, created at creation time for the function's own use (`CACHE_DIR` is `DATA_DIR/cache`) | `backend/open_webui/routers/functions.py:230-231`; `tools/ground-truth.md` (data stores) |
| Python packages a function requires | Installed into the server's Python environment (not the database), so they are lost when a container is rebuilt and reinstalled at the next startup | `backend/open_webui/utils/plugin.py:422-450`, `:453-484` |
| Pipelines, their code and their valves | On the Pipelines server, not in MedIT GPT. MedIT GPT stores only the connection (URL and key) among its OpenAI connection settings | `backend/open_webui/routers/pipelines.py:57-60`, `:446-573`; `model-connections-openai-ollama-and-direct.md` |
| Uploaded pipeline file | Copied briefly to `{CACHE_DIR}/pipelines/` and deleted after the upload, successful or not | `backend/open_webui/routers/pipelines.py:240-248`, `:305-308` |

### 6.3 Lifecycle

| Event | Effect on data | Evidence |
|---|---|---|
| Create | Row inserted with `is_active` false; manifest and toggle flag recorded | `backend/open_webui/routers/functions.py:200-262` |
| Edit (successful) | Code, name, description, type and manifest replaced | `backend/open_webui/routers/functions.py:379-424` |
| Edit or load fails | `is_active` set to false; code unchanged | `backend/open_webui/utils/plugin.py:307-313` |
| Switch on or off; Global | `is_active` or `is_global` flipped | `backend/open_webui/routers/functions.py:288-371` |
| Safe mode at startup | `is_active` set to false on **every** function | `backend/open_webui/models/functions.py:417-429`; `backend/open_webui/main.py:382-383` |
| Delete | Row removed (no soft delete); people's user valves and model references stay | `backend/open_webui/models/functions.py:431-439` |
| Bulk sync (API only) | Rows matching the supplied list are replaced or inserted; **every other function is deleted** | `backend/open_webui/models/functions.py:140-182` |
| Deleting a user account | Functions they created stay (ground truth: deletion does not remove workspace items) | `tools/ground-truth.md` (Accounts and Access) |

### 6.4 Personal Data

- **Account details reach function code.** Pipes, filters and actions receive the person's account
  record (`__user__`), which includes id, email, name, role and profile fields such as bio, gender,
  date of birth and time zone when filled in (`backend/open_webui/functions.py:277`;
  `backend/open_webui/utils/middleware.py:4153-4160`; `backend/open_webui/utils/actions.py:111-122`;
  `backend/open_webui/models/users.py:184-216`). Event functions receive the acting person's id,
  name, email, role and account dates (`backend/open_webui/events.py:704`, `:974-985`). Whatever a
  function then does with that data (for example sending it to an outside service) depends on its
  code; reviewing installed functions for privacy is **TO BE CONFIRMED**.
- **Pipelines servers receive personal data**: the person's id, email, name and role with every
  filter call and every pipe-pipeline request, together with the conversation
  (`backend/open_webui/routers/pipelines.py:64`, `:90-93`, `:130`, `:156-159`;
  `backend/open_webui/routers/openai.py:1559-1566`).
- **The starter code logs chat content.** The **Filter** starter prints the request body and the
  user record to the server log in each hook, and the **Event** starter prints each event payload
  (`src/lib/components/admin/Functions/FunctionEditor.svelte:94-96`, `:111-113`, `:121-123`,
  `:154-157`). A function saved from the starter without removing those lines writes message text,
  names and emails to the server's standard output.
- **Administrators' view.** The admin list shows each function creator's name and email
  (`backend/open_webui/models/functions.py:234-260`; `src/lib/components/admin/Functions.svelte:567-581`).
- **Exports** contain function code (which may embed addresses or keys written into it) but not
  valves (`backend/open_webui/routers/functions.py:69-78`; `src/lib/components/admin/Functions.svelte:89-101`).

## 7. Settings and Configuration

Values below are the **code defaults**. Live values are data (environment or the `config` table)
and are **TO BE CONFIRMED** for production (`tools/ground-truth.md`, "Settings: Where a Value Comes
From").

### 7.1 Environment-Only Switches (Read at Startup, Never Stored)

| Variable | Code default | Effect | Evidence |
|---|---|---|---|
| `ENABLE_PLUGINS` | `True` | Master switch for functions **and** workspace tools. When off: the function lists come back empty, the **Functions** admin tab and pages are hidden, pipe models are not listed, filters and Event functions are skipped, actions are refused with `Plugins are disabled by ENABLE_PLUGINS=false`, startup skips package installation, and workspace tools are not loaded | `backend/open_webui/env.py:1186`; `backend/open_webui/routers/functions.py:50-51`, `:58-59`, `:75-76`; `backend/open_webui/functions.py:72-73`; `backend/open_webui/utils/filter.py:69-70`, `:220-221`; `backend/open_webui/events.py:1106-1107`; `backend/open_webui/utils/actions.py:20-21`; `backend/open_webui/utils/plugin.py:207-208`, `:260-261`, `:461-463`; `backend/open_webui/routers/tools.py:81`, `:201-202`; `backend/open_webui/main.py:2353`; `src/routes/(app)/admin/+layout.svelte:18-23`, `:87-95` |
| `SAFE_MODE` | `False` | When on, prints `SAFE MODE ENABLED` at import and switches **every** function off at each startup. Functions stay off after safe mode is removed until an administrator switches them on again | `backend/open_webui/env.py:965`; `backend/open_webui/main.py:280-282`, `:382-383`; `backend/open_webui/models/functions.py:417-429` |
| `ENABLE_PIP_INSTALL_FRONTMATTER_REQUIREMENTS` | `True` | Allows the server to `pip install` the packages a function or tool lists under `requirements`. When off, nothing is installed and a log line says so | `backend/open_webui/env.py:1188-1190`; `backend/open_webui/utils/plugin.py:422-426` |
| `OFFLINE_MODE` | `false` | Among other effects, skips requirement installation (log `Offline mode enabled, skipping installation of requirements.`) | `backend/open_webui/env.py:1201-1205`; `backend/open_webui/utils/plugin.py:428-430` |
| `PIP_OPTIONS`, `PIP_PACKAGE_INDEX_OPTIONS` | empty | Extra options passed to every `pip install` of function and tool requirements (for example a private package index). Values are TO BE CONFIRMED | `backend/open_webui/env.py:1192-1193`; `backend/open_webui/utils/plugin.py:441-443` |
| `ENABLE_API_OUTLET_FILTERS` | `True` | Runs outlet filters (function and Pipelines) on replies to API callers that have no browser session | `backend/open_webui/env.py:1052`; `backend/open_webui/utils/middleware.py:4416-4423`, `:6653-6662` |
| `AIOHTTP_CLIENT_TIMEOUT` | unset (no overall limit; 300 seconds if the value cannot be read) | Time limit for **Import From Link** downloads. The Pipelines routes do not pass a time limit of their own | `backend/open_webui/env.py:608-612`; `backend/open_webui/routers/functions.py:130-132`; `backend/open_webui/routers/pipelines.py:75`, `:254`, `:324`, `:374`, `:417`, `:457`, `:504`, `:545` |
| `AIOHTTP_CLIENT_SESSION_SSL` | `True` | Certificate checking for **Import From Link** and every call to a Pipelines server | `backend/open_webui/env.py:631`; `backend/open_webui/routers/functions.py:133-135`; `backend/open_webui/routers/pipelines.py:100`, `:166`, `:273`, `:329`, `:379`, `:421`, `:461`, `:508`, `:549` |
| `AIOHTTP_FILE_STREAM_CHUNK_SIZE` | 1 MiB | Chunk size used to copy an uploaded pipeline file | `backend/open_webui/env.py:671-677`; `backend/open_webui/routers/pipelines.py:246-260` |
| `ENABLE_VALVE_ENCRYPTION` | Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca) | Governs how stored admin and user valve values are protected | `backend/open_webui/env.py:767`; `backend/open_webui/utils/valves.py:21-24` |
| `BYPASS_MODEL_ACCESS_CONTROL`, `BYPASS_ADMIN_ACCESS_CONTROL` | `False`, `True` | Decide who sees pipe models (as for every model) | `tools/ground-truth.md`; `backend/open_webui/functions.py:288-290`; `workspace-models-and-model-access.md` |

Changing any of these needs a restart of every server worker; they are read once when the server
starts (`backend/open_webui/env.py`, module level).

### 7.2 Stored Settings (the `config` Table)

| Key | Code default | Effect on this area | Evidence |
|---|---|---|---|
| `user.permissions` > `chat` > `controls` and `valves` | `True` and `True` (`USER_PERMISSIONS_CHAT_CONTROLS`, `USER_PERMISSIONS_CHAT_VALVES`) | Show the **Controls** panel and its **Valves** section, and the valves icons for toggleable filters, to non-admins | `backend/open_webui/config.py:1849-1851`, `:1979-1980`; `src/lib/components/chat/Controls/Controls.svelte:54`, `:93`; `users-groups-roles-and-permissions.md` |
| `ui.enable_community_sharing` | `True` (`ENABLE_COMMUNITY_SHARING`) | Shows the **Discover a function** link on the Functions page. The **Share** menu item is shown regardless | `backend/open_webui/config.py:2096`, `:3123`; `backend/open_webui/main.py:2369`; `src/lib/components/admin/Functions.svelte:744-750`; `src/lib/components/admin/Functions/FunctionMenu.svelte:91-100` |
| `openai.enable`, `openai.api_base_urls`, `openai.api_keys`, `openai.api_configs` | see connections document | A Pipelines server is one of these OpenAI connections. It is detected only when the OpenAI API is on, the connection is enabled and has **no** fixed model-id list, and the server's model list carries the `pipelines` marker. A Pipelines filter is called only when its connection has a key | `backend/open_webui/routers/openai.py:676-720`; `backend/open_webui/routers/pipelines.py:57-60`, `:84-87`, `:204-220`; `model-connections-openai-ollama-and-direct.md` |

### 7.3 Settings Held Elsewhere

- **Function valves** are held per function (section 6.1) and edited from the Functions page; **user
  valves** per person (section 6.2).
- **Which filters and actions a model uses** are model settings (section 6.2).
- **Pipeline valves** are held on the Pipelines server (section 5.14).
- What the Pipelines server itself is configured with (its key, its installed pipelines, where it
  runs) is outside this repository and **TO BE CONFIRMED**.

## 8. Cron Jobs and Background Processes

There is no crontab and no scheduled job in this area: nothing about functions or pipelines runs
on a timer. Work happens at four moments: when a server process starts, when an administrator
saves, during ordinary requests (building the model list, running a chat turn), and in short
background tasks that hand events to Event functions. Each uvicorn worker process does its own
start-up and keeps its own in-memory copies (`CLAUDE.md:85`; `backend/start.sh:99`, `:104`, one
worker by default). The start-up mechanics shared with workspace tools are described in
`workspace-tools-tool-servers-mcp-and-terminals.md` section 8.1; this section covers what is
specific to functions.

### 8.1 At Start-Up (Each Server Process)

| Order | Step | What happens | If it fails | Source |
|---|---|---|---|---|
| At import | Safe-mode notice | When `SAFE_MODE` is on, the process prints `SAFE MODE ENABLED` to standard output | — | `backend/open_webui/main.py:280-282` |
| 1 | `system.startup.started` event | Handed to Event functions (as a background task, section 8.3) and to event webhooks. This happens **before** safe mode and package installation | Logged per function (section 8.3) | `backend/open_webui/main.py:370`; `backend/open_webui/events.py:45-47`, `:1159-1171` |
| 2 | Safe mode | When `SAFE_MODE` is on, **every** function is switched off in the database, at every start of every process. Nothing switches them back on afterwards; an administrator must do it one by one (section 5.5) | A database error here is not logged | `backend/open_webui/main.py:382-383`; `backend/open_webui/models/functions.py:417-429` |
| 3 | Install packages (**blocking**) | Log `Installing external dependencies of functions and tools...`. The `requirements` lines of every **active** function and of every tool owned by an administrator are joined and installed with one `pip install`. The process does not serve requests until this finishes. The code's own comment gives the reason: so that functions are not switched off by the first model-list request (section 11.2). The code sets no time limit on `pip` | Log `Error installing packages: {packages}` followed by `Error installing requirements: {e}`; start-up **continues** without those packages | `backend/open_webui/main.py:385-388`; `backend/open_webui/utils/plugin.py:422-484` |
| 3 (skipped) | No installation | With `ENABLE_PLUGINS` off the log reads `ENABLE_PLUGINS is disabled, skipping tool and function dependencies.`; with `ENABLE_PIP_INSTALL_FRONTMATTER_REQUIREMENTS` off, `ENABLE_PIP_INSTALL_FRONTMATTER_REQUIREMENTS is disabled, skipping installation of requirements.`; with `OFFLINE_MODE` on, `Offline mode enabled, skipping installation of requirements.` | — | `backend/open_webui/utils/plugin.py:424-430`, `:461-463` |
| 4 | Optional model pre-fetch | Only when the stored setting `models.base_models_cache` is on (code default off, from `ENABLE_BASE_MODELS_CACHE`): the model list is built once, which loads every active pipe (asking manifolds for their sub-models) and every filter and action attached to a model or made global | Log `Failed to pre-fetch models at startup: {e}`; start-up continues | `backend/open_webui/main.py:407-429`; `backend/open_webui/config.py:374`, `:2832`; `backend/open_webui/utils/models.py:57-66`, `:314-335` |
| 5 | `system.startup.completed` event | Handed to Event functions and webhooks once the process has marked start-up complete (from then on `/ready` stops answering 503 for start-up reasons) | As step 1 | `backend/open_webui/main.py:471-472`; `CLAUDE.md` (Deployment, health) |
| Shutdown | `system.shutdown.started`, `system.shutdown.completed` events | Handed to Event functions and webhooks when the process stops | As step 1 | `backend/open_webui/main.py:476`, `:496` |

Points to note:

- **Safe mode also shortens step 3.** Functions are switched off before the installation step, so
  only administrators' tools have their packages installed (`backend/open_webui/main.py:382-388`;
  `backend/open_webui/utils/plugin.py:465`).
- **Switched-off functions are skipped at start-up.** Their packages are installed when the
  function is next loaded: usually on the model-list refresh that follows an administrator
  switching it on, or, for an Event function, during the switch itself
  (`backend/open_webui/utils/plugin.py:273-275`, `:465`;
  `backend/open_webui/routers/functions.py:305-310`; `src/lib/components/admin/Functions.svelte:705-715`).
- **Several workers repeat the work.** Every worker runs steps 1 to 5, so the package installation
  runs once per worker. How many workers production runs is **TO BE CONFIRMED**
  (`CLAUDE.md:85`; `backend/start.sh:99`).

### 8.2 The Per-Process Function Cache

| Behaviour | What it means | Source |
|---|---|---|
| What is kept | Each process keeps every function it has loaded in memory, together with the code it loaded | `backend/open_webui/utils/plugin.py:318-337` |
| When it refreshes | Each use (model-list build, inlet, request and outlet filter hooks, an action click, a valves form, an Event delivery) reads the function's row and reloads the function when the stored code differs from the copy in memory. An edit therefore takes effect in every process at its next use, without a restart | `backend/open_webui/utils/plugin.py:375-403`; `backend/open_webui/utils/filter.py:49-56`; `backend/open_webui/utils/actions.py:83`; `backend/open_webui/events.py:1129` |
| Stream hook | Reuses the copy already in memory (loaded earlier in the same turn) instead of re-reading the database, for speed | `backend/open_webui/utils/plugin.py:404-411`; `backend/open_webui/utils/filter.py:177-179` |
| Load failure | When the code cannot be loaded, the process switches the function off **in the database** (so for every process) and raises the error. This can happen during any ordinary request, such as a user's chat or a model-list refresh, so a function can be switched off without any administrator touching it | `backend/open_webui/utils/plugin.py:307-313` |
| Package memory | Each process remembers which `requirements` entries it has installed and installs each at most once. When it loads a function it has not loaded before (or whose code changed), it first installs that function's packages. A failed installation is raised as an error **without** switching the function off. A restart clears the memory | `backend/open_webui/utils/plugin.py:273-275`, `:419-447` |
| Old import paths | When stored code still uses outdated import lines (for example `from utils`), the server corrects them and saves the code back, which also moves the function's **Updated at** time although nobody edited it | `backend/open_webui/utils/plugin.py:187-201`, `:393-397`; `backend/open_webui/models/functions.py:398-415` |
| Delete | The process that handled the delete drops its copy; other processes find the row gone at their next lookup | `backend/open_webui/routers/functions.py:441-445`; `backend/open_webui/utils/plugin.py:387-390` |

### 8.3 Background Tasks That Deliver Events to Event Functions

| What | Detail | Source |
|---|---|---|
| Delivery | Each published event (section 9.3) starts one background task in the process that published it. The task calls the `event` method of each active Event function in turn, after loading the function's admin valves | `backend/open_webui/events.py:1103-1171` |
| Exception: switching a function on or off | The `function.enable_started` or `function.disable_started` event is delivered **inside** the request, and the switch waits for every Event function to finish (section 5.12) | `backend/open_webui/routers/functions.py:297-311` |
| Failures | A failing Event function is logged as `Event function failed for {id}` and the next one still runs. If the list of Event functions cannot be read the log says `Event functions could not be loaded for {event}`; if the task cannot be started, `Event functions could not be scheduled for {event}` | `backend/open_webui/events.py:1123-1125`, `:1155-1156`, `:1162-1163` |
| No queue, no retry | Delivery exists only in the memory of the running process. The code stores nothing and has no retry, so an event published just before a restart may never reach Event functions | `backend/open_webui/events.py:1159-1163` |

### 8.4 Work Done at Save Time or Per Request (Not in the Background)

| Moment | What happens | Source |
|---|---|---|
| Saving a function (create, update, API sync) | The administrator's request installs the code's packages and loads the code before it answers, so a save can take as long as `pip` takes | `backend/open_webui/routers/functions.py:170-176`, `:217-222`, `:387-389`; `backend/open_webui/utils/plugin.py:273-275` |
| Every model-list build | Every active pipe is loaded and each manifold is asked for its sub-models; every filter and action attached to a model or made global is loaded too. A slow or failing function therefore slows, or empties, that part of the model list for everyone | `backend/open_webui/functions.py:71-150`; `backend/open_webui/utils/models.py:314-335` |
| Model-list cache | With `models.base_models_cache` on, pipe models are reused from the cache (Redis when configured, otherwise each process's memory) until a refresh. The admin screens ask for a refresh after each function change | `backend/open_webui/utils/models.py:69-106`; `src/lib/components/admin/Functions.svelte:228-236`; `src/routes/(app)/admin/functions/create/+page.svelte:52-60` |
| Each chat turn | Function filters run at their points (section 5.10); Pipelines filters are called over the network (section 5.15) | `backend/open_webui/utils/filter.py:212-250`; `backend/open_webui/routers/pipelines.py:63-192` |
| Opening **Admin Settings > Pipelines** | MedIT GPT asks every OpenAI connection for its model list to find Pipelines servers, waiting up to the model-list time limit (`AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST`, default 10 seconds) per connection, in parallel | `backend/open_webui/routers/pipelines.py:204-220`; `backend/open_webui/routers/openai.py:79`, `:89-119`, `:676-720`; `backend/open_webui/env.py:656-663` |

What a Pipelines server runs on its own (its schedules, if any) is outside this repository and
**TO BE CONFIRMED**.

## 9. Notifications and Emails

MedIT GPT sends no email (`tools/ground-truth.md`, Contacts). In this area people are told things
in four ways: toasts and dialogs on the admin screens (catalogued in section 10); messages that a
running function sends to the person's open chat (9.2); platform events delivered to event
webhooks and Event functions (9.3, 9.4); and, for many failures, nothing except a server log line
(section 10). Function and pipeline changes never create in-app (bell) or browser notifications:
the only events that do are chat, channel, calendar and file-processing events, and none of the
function or pipeline events is among them (`backend/open_webui/events.py:669-675`, `:1083-1086`).

### 9.1 Feedback on the Admin Screens

| Administrator action | Feedback | Evidence |
|---|---|---|
| Create, update, delete, import, clone, export a function | A toast for success or failure (section 10) | `src/lib/components/admin/Functions.svelte:89-266`, `:786-840`; `src/routes/(app)/admin/functions/create/+page.svelte:19-64`; `src/routes/(app)/admin/functions/edit/+page.svelte:20-63` |
| Switch a function on or off | **No** toast, and a refusal is not reported (section 5.5) | `src/lib/components/admin/Functions.svelte:703-716` |
| Make a filter or action global | A toast naming the new state | `src/lib/components/admin/Functions.svelte:240-266` |
| Save valves | `Valves updated successfully`, or the server's error text | `src/lib/components/workspace/common/ValvesModal.svelte:52-103` |
| Pipelines panel: upload, install, delete, save valves | A toast for each; **Delete** removes the selected pipeline at once, with no confirmation dialog | `src/lib/components/admin/Settings/Pipelines.svelte:51-236`, `:385-392` |

### 9.2 Messages a Function Sends to the Open Chat

Pipes, filters and actions are given two channels to the person's browser: a one-way **event
emitter** and an **event call** that asks the browser something and waits for the answer
(`backend/open_webui/functions.py:233-282`; `backend/open_webui/utils/middleware.py:2544`;
`backend/open_webui/utils/actions.py:66-81`). Emitted events go to every open session of that
person (`backend/open_webui/socket/main.py:1139-1161`), but the chat page acts on an event only when
that chat is the one open and the reply exists (`src/lib/components/chat/Chat.svelte:1201-1217`).

| Event type | What the person sees | Kept in the saved chat? | Evidence |
|---|---|---|---|
| `status` | A progress line above the reply, in the function's words. Hidden when the person has **Hide Processing Details** switched on (section 12) | Yes | `src/lib/components/chat/Chat.svelte:1221-1226`; `backend/open_webui/socket/main.py:1166-1171`; `src/lib/components/chat/Messages/ResponseMessage.svelte:197-202`, `:720` |
| `notification` | A toast of the type the function chose (success, error, warning; anything else shows as information) with the function's text | No | `src/lib/components/chat/Chat.svelte:1354-1366` |
| `message` (or `chat:message:delta`) | Text added to the reply | Yes, when sent as `message` | `src/lib/components/chat/Chat.svelte:1265-1266`; `backend/open_webui/socket/main.py:1173-1190` |
| `replace` (or `chat:message`) | The reply's text replaced | Yes, when sent as `replace` | `src/lib/components/chat/Chat.svelte:1267-1268`; `backend/open_webui/socket/main.py:1191-1201` |
| `files`, `embeds` | Files or embedded content attached to the reply (an action's rich output arrives this way) | Yes | `src/lib/components/chat/Chat.svelte:1269-1283`; `backend/open_webui/socket/main.py:1202-1234`; `backend/open_webui/utils/actions.py:137-145` |
| `source` (or `citation`) | Sources listed under the reply | Yes | `src/lib/components/chat/Chat.svelte:1328-1353`; `backend/open_webui/socket/main.py:1235-1250` |
| `chat:message:error` | The reply's grey error box | Only when the server path that raised it saves it | `src/lib/components/chat/Chat.svelte:1284-1292` |
| `confirmation` | A dialog with the function's title and message and **Cancel** and **Confirm** buttons; the title reads `Confirm your action` when the function gives none. The function waits for the answer | No | `src/lib/components/chat/Chat.svelte:1367-1375`; `src/lib/components/common/ConfirmDialog.svelte:18-22`, `:138-153` |
| `input` | The same dialog with a text box or a list of choices | No | `src/lib/components/chat/Chat.svelte:1390-1401` |
| `execute` | Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca) | — | `src/lib/components/chat/Chat.svelte:1376-1389` |

For the asking channel (`confirmation`, `input`), the server asks only the browser tab that sent the
request. If that tab has gone, the function receives `Client session disconnected.`; if the tab does
not answer within `WEBSOCKET_EVENT_CALLER_TIMEOUT` (unset by default, so the code sets no limit; 300
seconds if the value cannot be read), it receives `Event call timed out. The browser tab may be
inactive or closed.` Whether the person then sees anything depends on the function's code
(`backend/open_webui/socket/main.py:1258-1281`; `backend/open_webui/env.py:534-542`).

The wording of every status line, toast and dialog in this table comes from the function's own
code, which is stored in the database rather than in this repository, so it cannot be catalogued
here (section 14). Automation runs mark their requests as internal, and the emitter drops
`notification` events for them (`backend/open_webui/socket/main.py:1146-1147`).

### 9.3 Platform Events From This Area

Each event below is handed to every active Event function (section 8.3) and to every event webhook
an administrator configured that matches it. The webhook post carries the event's message with the
subject id in brackets, for example `Function enabled (my_filter)`, sent under the deployment name
(`WEBUI_NAME`, MedIT GPT by default) (`backend/open_webui/events.py:1034-1060`;
`backend/open_webui/main.py:538`; `backend/open_webui/env.py:951`). How webhooks are configured is in
`notifications-webhooks-events-and-banners.md`.

| Event | Published when | Message | Evidence |
|---|---|---|---|
| `function.created` | After a function is created | `Function created` | `backend/open_webui/routers/functions.py:236-243`; `backend/open_webui/events.py:476-478` |
| `function.updated` | After code, name or description is saved, and after the **Global** switch is changed (the data then includes `is_global`) | `Function updated` | `backend/open_webui/routers/functions.py:353-360`, `:403-410`; `backend/open_webui/events.py:479-481` |
| `function.deleted` | After a delete | `Function deleted` | `backend/open_webui/routers/functions.py:446-451`; `backend/open_webui/events.py:482-484` |
| `function.enable_started`, `function.disable_started` | Before the on/off switch is saved. Event functions get it inside the request (including the function being switched on, when it is an Event function); webhooks get it from a background task | `Function enable started`, `Function disable started` | `backend/open_webui/routers/functions.py:297-311`; `backend/open_webui/events.py:491-500` |
| `function.enabled`, `function.disabled` | After the switch is saved | `Function enabled`, `Function disabled` | `backend/open_webui/routers/functions.py:315-323`; `backend/open_webui/events.py:485-490` |
| `function.valves_updated` | After admin valves are saved, and also each time **any person** saves their own user valves (the data then reads `scope: user`) | `Function valves updated` | `backend/open_webui/routers/functions.py:538-543`, `:645-651`; `backend/open_webui/events.py:501-503` |
| `pipeline.uploaded` | After the Pipelines server accepts an uploaded file | `Pipeline uploaded` | `backend/open_webui/routers/pipelines.py:278-284`; `backend/open_webui/events.py:555-557` |
| `pipeline.added` | After the Pipelines server installs a pipeline from a URL | `Pipeline added` | `backend/open_webui/routers/pipelines.py:334-340`; `backend/open_webui/events.py:558-560` |
| `pipeline.deleted` | After a pipeline is deleted | `Pipeline deleted` | `backend/open_webui/routers/pipelines.py:384-390`; `backend/open_webui/events.py:561-563` |
| `pipeline.valves_updated` | When an administrator **opens** (reads) a pipeline's valves. Saving pipeline valves publishes nothing, so this event does not mean that anything changed | `Pipeline valves updated` | `backend/open_webui/routers/pipelines.py:466-472`, `:533-555`; `backend/open_webui/events.py:564-566` |
| `system.startup.started`, `system.startup.completed`, `system.shutdown.started`, `system.shutdown.completed` | Section 8.1 | `Startup started`, `Startup completed`, `Shutdown started`, `Shutdown completed` | `backend/open_webui/main.py:370`, `:472`, `:476`, `:496`; `backend/open_webui/events.py:45-56` |

**Personal data in events.** Every event carries the acting person's id, name, email, role and
account dates. Keys that look like passwords, tokens, secrets or keys are removed from the event,
and long text is cut at 1,000 characters (`backend/open_webui/events.py:19`, `:689-704`, `:947-985`).
Event webhooks and Event functions therefore receive personal data; where they send it is
**TO BE CONFIRMED** (section 14).

### 9.4 Event Functions as Notification Hooks

- An Event function is the code-based way to react to any platform event, for example to pass
  selected events on to another system. It receives every event, not only those in 9.3 (chat,
  user, file and other events are listed in `notifications-webhooks-events-and-banners.md`)
  (`backend/open_webui/events.py:1103-1171`).
- Users see nothing when an Event function runs or fails; failures are only logged (section 8.3).
- The **Event** starter code only prints each event to the server log, including the actor's
  name and email (section 6.4; `src/lib/components/admin/Functions/FunctionEditor.svelte:127-158`).
- Which Event functions production has, and what they send where, is **TO BE CONFIRMED**.

### 9.5 Pipelines

The Pipelines router only makes outgoing calls to the Pipelines server; it defines no route that
the Pipelines server could call back, so a Pipelines server has no channel to notify MedIT GPT
users other than the text of its replies and the refusals it returns
(`backend/open_webui/routers/pipelines.py:63-192`, `:204-573`). Events from the Pipelines panel are
listed in 9.3.

## 10. Error, Warning and Notice Messages (Verbatim)

How messages reach people in this area:

- **Functions pages and valves dialogs.** Every call in `src/lib/apis/functions/index.ts` passes
  the server's `detail` on unchanged, and the pages show it as a red pop-up with exactly that text
  (`src/lib/apis/functions/index.ts:17-28`, the same pattern for every call;
  `src/lib/components/admin/Functions.svelte:219-222`). When the server's answer carries no
  `detail` (a dropped connection, a plain-text `Internal Server Error` from an unhandled failure, an
  error page from a proxy), these calls show **nothing** and the page simply does not change
  (`src/lib/apis/functions/index.ts:21-28`; `backend/open_webui/main.py:515` is the only custom
  error handler and it is unrelated). When the server rejects the request's format, its `detail` is
  a list and the pop-up reads `[object Object]` (10.2).
- **`[ERROR: …]` texts** come from one helper: an exception becomes `[ERROR: {fallback}]` with a
  fixed fallback per route, and storage errors become fixed storage texts
  (`backend/open_webui/constants.py:6-13`, `:16-23`). The real cause is only in the server log
  (10.7).
- **Pipelines panel.** Install, delete and valves save show the server's `detail` when there is one;
  upload always shows its own generic text; listing pipelines and reading their valves have no
  error handling in the panel, so a failure leaves a spinner (`src/lib/apis/index.ts:1151-1440`;
  `src/lib/components/admin/Settings/Pipelines.svelte:93-136`, `:165-179`).
- **Chats.** Failures of pipes, filters and actions appear in the reply's grey error box
  (`src/lib/components/chat/Messages/Error.svelte:1-48`), sometimes with a pop-up (10.5). Status
  lines, pop-ups and dialogs that a function sends on purpose are written in its own code and are
  not catalogued (section 9.2).

Placeholders are written `{name}` with the source's variable name. Severity is how the interface
presents the text.

### 10.1 Function Management: Messages From the Server

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Only alphanumeric characters and underscores are allowed in the id` | Error | `backend/open_webui/routers/functions.py:207-211` | **Save & Create**, a clone or an imported function whose ID is not a valid Python name: characters other than letters, digits and underscores, an empty ID, or an ID that starts with a digit (the check is Python's `isidentifier`) | Change the Function ID | None |
| `Uh-oh! This id is already registered. Please choose another id string.` | Error | `backend/open_webui/routers/functions.py:215-216`, `:258-262`; `backend/open_webui/constants.py:54` | Creating, importing or cloning a function whose ID (after lower-casing) is already used. A second clone of the same function reuses `{id}_clone` and hits this | Choose another ID; for an import, the function may already be installed | Search the Functions list by ID |
| `[ERROR: Error creating function]` | Error | `backend/open_webui/routers/functions.py:245-257`; `backend/open_webui/constants.py:16-23` | A new function could not be saved: its code fails to load (a Python error, none of the classes `Pipe`, `Filter`, `Action` or `Event`, a missing module), a package listed under `requirements` fails to install, or the database refused the row | Correct the code; the administrator checks the packages | Server log, same minute: `Failed to create a new function: {e}` with `Error loading module: {function_id}: {e}` (code), `Error installing packages: {packages}` (packages) or `Error creating a new function: {e}` (database). The text `No Function class found in the module` appears only in the log |
| `[ERROR: Error updating function]` | Error | `backend/open_webui/routers/functions.py:412-424` (save), `:325-329` (on/off switch), `:362-366` (**Global** switch); `backend/open_webui/constants.py:16-23` | Saving changed code that fails to load or whose packages fail to install, or a switch that could not be stored. When the new code fails to load, the loader also **switches the function off** and keeps the old code (`backend/open_webui/utils/plugin.py:307-313`) | Correct the code, save, then switch the function back on | Log `Error loading module: {function_id}: {e}`; the function's switch on the list. The on/off switch never shows this text (section 5.5) |
| `[ERROR: Error fetching function]` | Error | `backend/open_webui/routers/functions.py:129-151` | **Import From Link**: the server could not download the address (unknown host, refused connection, certificate problem, time limit). The download honours the server's standard proxy environment settings (`trust_env=True`) and its certificate checking (section 7.1) | Check the address opens in a browser; try later | Whether the server can reach that host |
| `Failed to fetch the function` | Error | `backend/open_webui/routers/functions.py:136-137` | The address answered with any status other than 200 (a missing file, a private repository, a rate limit); the browser receives that same status | Use a raw-file link the server can read | The HTTP status in the browser's developer tools |
| `No data received from the URL` | Error | `backend/open_webui/routers/functions.py:138-140` | The address answered with an empty file | Check the link | None |
| `Please enter a valid URL` | Error | `backend/open_webui/routers/functions.py:113-115`; `src/lib/components/ImportModal.svelte:25-29` | **Import** with an empty address. The box is marked required, so the browser's own "fill in this field" hint normally appears first (`src/lib/components/ImportModal.svelte:92-98`) | Enter the address | None |
| `We could not find what you're looking for :/` | Error | `backend/open_webui/routers/functions.py:276-280`, `:330-334`, `:367-371`, `:475-479`, `:505-509`, `:551-561`, `:583-587`, `:611-615`, `:659-668`; `backend/open_webui/constants.py:78` | The function no longer exists (deleted in another tab, an old bookmark of an edit page), or valves were saved for a function whose code declares no `Valves` (or `UserValves`) class. Answered with HTTP 401 | Go back to the list and refresh | Whether the function still exists. The edit page returns to the list after the pop-up (`src/routes/(app)/admin/functions/edit/+page.svelte:74-79`) |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error | `backend/open_webui/utils/auth.py:625-631`; `backend/open_webui/constants.py:70-72`; every administrator-only route in section 3.1 | A non-administrator's request reached an administrator-only function or Pipelines route. The interface does not offer these to non-admins, so this usually means a tab left open after a role change | None | The account's role |
| `[ERROR: Error loading function]` | Error | `backend/open_webui/routers/functions.py:163-192` | API-only bulk sync (`/api/v1/functions/sync`, not used by the interface): one supplied function failed to load or its valves failed to validate. Nothing is synced, but an existing function with that ID is switched off by the loader (`backend/open_webui/utils/plugin.py:307-313`) | — | Log `Failed to load a function: {e}` or `Error validating valves for function {id}: {e}` |
| `[ERROR: Error getting function valves]` | Error | `backend/open_webui/routers/functions.py:466-474`; `backend/open_webui/models/functions.py:294-301` | Reading admin valves failed. The database method catches its own errors and returns nothing, so this text is unlikely to appear; a read failure shows as empty settings instead | — | Log `Error getting function valves by id {id}: {e}` |
| `[ERROR: Error getting function user valves]` | Error | `backend/open_webui/routers/functions.py:574-582`; `backend/open_webui/models/functions.py:354-373` | As above, for a person's own valves | — | Log `Error getting user values by id {id} and user id {user_id}` (the code spells it "values") |
| `[ERROR: Error updating function valves]` | Error | `backend/open_webui/routers/functions.py:532-550` | Admin valve values do not fit the function's settings (a wrong type, a required value missing). Shown by the Valves dialog (`src/lib/components/workspace/common/ValvesModal.svelte:89-93`) | Correct the value | Log `Error updating function values by id {id}: {e}` names the setting |
| `[ERROR: Error updating function user valves]` | Error | `backend/open_webui/routers/functions.py:640-658` | A person's own valve values do not fit the function's definition | Correct the value | Log `Error updating function user valves by id {id}: {e}` |
| `Function is not active` | Error | `backend/open_webui/routers/functions.py:628-633` | Saving user valves for a function that is switched off. The valves forms load no settings for a switched-off function (`:599-600`), so this normally appears only when the function was switched off after the form opened | Ask whether the function should be on | The function's switch on the Functions page |
| `[ERROR: The server is out of storage space.]`, `[ERROR: Server storage quota exceeded.]`, `[ERROR: Server storage is not writable.]`, `[ERROR: File name is too long.]` | Error | `backend/open_webui/constants.py:6-13`, `:16-23` | Replace any `[ERROR: …]` text in this table when the underlying failure is a storage error, for example while creating the function's cache folder. That folder is made after the row is stored, so in that case the function usually exists despite the error (`backend/open_webui/routers/functions.py:228-231`) | Escalate; reload the list before saving again | Disk space and permissions on the server |

### 10.2 Function Management: Messages From the Browser

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Function created successfully` | Success | `src/routes/(app)/admin/functions/create/+page.svelte:50-51` | The new function was saved; the browser returns to the list | Switch the function on when ready: new functions start off (section 5.1) | None |
| `Function updated successfully` | Success | `src/routes/(app)/admin/functions/edit/+page.svelte:51-52` | Changed code, name or description saved; the page stays open | — | None |
| `Function deleted successfully` | Success | `src/lib/components/admin/Functions.svelte:218-226` | Delete confirmed, or the Shift-key bin clicked. The server answers success even when the function had already gone (`backend/open_webui/models/functions.py:431-439`) | — | None |
| `Function imported successfully` | Success | `src/lib/components/ImportModal.svelte:37-42` | **Import From Link** downloaded the code and opened the editor. **Nothing is saved yet** | Click **Save & Create** | If an "imported" function is missing, ask whether **Save & Create** was clicked |
| `Functions imported successfully` | Success | `src/lib/components/admin/Functions.svelte:794-806` | **Import JSON** finished its loop, **even if some or all functions failed** (each failure shows its own pop-up first) | Check the list; imported functions are switched off | Whether the expected functions now appear (section 11.11) |
| `Filter is now globally enabled` | Success | `src/lib/components/admin/Functions.svelte:245-249` | **Global** switched on for a filter | — | None |
| `Filter is now globally disabled` | Success | `src/lib/components/admin/Functions.svelte:250-253` | **Global** switched off for a filter | — | None |
| `Function is now globally enabled` | Success | `src/lib/components/admin/Functions.svelte:245-249` | **Global** switched on for an action | — | None |
| `Function is now globally disabled` | Success | `src/lib/components/admin/Functions.svelte:250-253` | **Global** switched off for an action | — | None |
| `Redirecting you to Open WebUI Community` | Information | `src/lib/components/admin/Functions.svelte:158-186` | **Share** chosen; a new tab opens the upstream community site and is sent the function's details, including its code. Shown even when reading the function failed (that error appears first) | Follow local policy on public sharing (TO BE CONFIRMED, section 14) | None |
| `Open WebUI version (v{OPEN_WEBUI_VERSION}) is lower than required version (v{REQUIRED_VERSION})` | Error | `src/routes/(app)/admin/functions/create/+page.svelte:22-38`; `src/routes/(app)/admin/functions/edit/+page.svelte:23-39` | The code's opening comment sets `required_open_webui_version` above this release (0.11.4, `package.json:3`); nothing is saved | Use a version of the function written for this release | The `required_open_webui_version` line in the code |
| `Name and description are required` | Error, **never displayed** | `src/lib/components/admin/Functions/FunctionEditor.svelte:328-333` | Name or description is empty after trimming (spaces only), or empty while the editor shows a translation (the required-field check is then off, `src/lib/components/common/LocalizedField.svelte:41`, `:51`). The editor file does not import the pop-up library (`src/lib/components/admin/Functions/FunctionEditor.svelte:1-16`), so this line fails with a script error instead: the editor switches back to the base language, and **nothing is saved and nothing is shown** | Type a real name and description, then save again | The browser console shows a reference error naming `toast` (section 11.10) |
| `Code formatted successfully` | Success | `src/lib/components/common/CodeEditor.svelte:181-202` | The code was formatted before saving (this happens on every save) | — | None |
| `{e}` (formatter) | Error | `src/lib/components/common/CodeEditor.svelte:182-190`; `backend/open_webui/routers/utils.py:30-38` | Formatting failed, usually because of a syntax error. The text is the Python formatter's own (the `black` package), not part of this repository. The save then continues with the unformatted code (`src/lib/components/admin/Functions/FunctionEditor.svelte:347-364`) | Fix the line the message names | None |
| `[object Object]` | Error | `src/lib/components/ImportModal.svelte:31-35`; `src/lib/components/admin/Functions.svelte:800-803`; `src/lib/apis/functions/index.ts:17-28`, `:110-124` | The server rejected the request's format and replied with a list of problems the pop-up cannot print: an address that is not `http` or `https` in **Import From Link**, or an entry in an **Import JSON** file without `id`, `name`, `content` or `meta` (`backend/open_webui/models/functions.py:98-102`) | Use an `https` link; use a file exported from MedIT GPT | None |
| `Delete function?` | Warning | `src/lib/components/admin/Functions.svelte:753-765` | **Delete** in the `...` menu (dialog title) | Confirm or cancel | None |
| `This will delete {name}.` | Warning | `src/lib/components/admin/Functions.svelte:760-764` | Body of the same dialog | Confirm or cancel | None |
| `Confirm your action` | Warning | `src/lib/components/common/ConfirmDialog.svelte:139-145`; used by `src/lib/components/admin/Functions.svelte:786-840` and `src/lib/components/admin/Functions/FunctionEditor.svelte:524-546` | Title of the dialog after choosing an **Import JSON** file and after **Save & Create** | Read the warnings below it | None |
| `Please carefully review the following warnings:` | Warning | `src/lib/components/admin/Functions.svelte:826`; `src/lib/components/admin/Functions/FunctionEditor.svelte:532` | Same two dialogs | — | None |
| `Functions allow arbitrary code execution.` | Warning | `src/lib/components/admin/Functions.svelte:829`; `src/lib/components/admin/Functions/FunctionEditor.svelte:535` | Same two dialogs | Install only reviewed code | None |
| `Do not install functions from sources you do not fully trust.` | Warning | `src/lib/components/admin/Functions.svelte:830`; `src/lib/components/admin/Functions/FunctionEditor.svelte:536` | Same two dialogs | — | None |
| `I acknowledge that I have read and I understand the implications of my action. I am aware of the risks associated with executing arbitrary code and I have verified the trustworthiness of the source.` | Warning | `src/lib/components/admin/Functions.svelte:834-838`; `src/lib/components/admin/Functions/FunctionEditor.svelte:540-544` | Same two dialogs | Confirm only after review | None |
| `Warning:`, `Functions can execute arbitrary code.`, `Only install functions from sources you trust.` | Warning | `src/lib/components/admin/Functions/FunctionEditor.svelte:499-507` | Footer of the code editor, always shown (three strings on one line) | — | None |
| `No functions found` | Notice | `src/lib/components/admin/Functions.svelte:726-734` | No function exists yet, or none matches the search, the type filter or the view filter | Clear the search and filters | None |
| `Try adjusting your search or filter to find what you are looking for.` | Notice | `src/lib/components/admin/Functions.svelte:730-732` | Shown under the previous row | — | None |
| `Deleted User` | Notice | `src/lib/components/admin/Functions.svelte:567-581` | The account that created the function (or last ran a bulk sync) no longer exists | — | None |

### 10.3 Valves Messages

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Valves updated successfully` | Success | `src/lib/components/workspace/common/ValvesModal.svelte:96-99` | Admin valves (gear icon on the Functions list), or a person's own valves (composer **Integrations** menu, composer **Valves** button) saved; the model list reloads | — | If the change seems not to stick, see section 11.12: a database failure is not reported |
| `Valves updated` | Success | `src/lib/components/chat/Controls/Valves.svelte:97-99`, `:111-113` | A person's valves in the chat **Controls** panel saved automatically, half a second after a change | — | As above |
| `Error fetching valves` | Error | `src/lib/components/workspace/common/ValvesModal.svelte:151-154` | The dialog could not read the valves or their definition (the function was deleted, or the server answered with an error text); the dialog closes. This literal text is not translated | Refresh and try again | Whether the function still exists |
| `No valves` | Notice | `src/lib/components/common/Valves.svelte:241-243` | The function declares no settings, it is switched off (for a person's own valves, `backend/open_webui/routers/functions.py:599-600`), or its code failed to load: the server then answers without a text, so no error is shown (`src/lib/apis/functions/index.ts:366-382`), and the loader switches the function off (`backend/open_webui/utils/plugin.py:307-313`) | — | Whether the function is on and loads (section 11.12) |
| `*required` | Notice | `src/lib/components/common/Valves.svelte:31-33` | The setting has no default and must be given a value | Enter a value | None |
| `Failed to load valves` | Error | `src/lib/components/workspace/common/PluginTranslations.svelte:25-45`, `:60-64` | In the editor's translation view for an existing function, its valve definitions could not be read; a **Retry** button follows | Click **Retry**; check the function still exists | None |

### 10.4 Pipelines Messages

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Pipelines Not Detected` | Notice | `src/lib/components/admin/Settings/Pipelines.svelte:473-479` (Source section), `:461-466` (Pipelines section) | Source section: no OpenAI connection identified itself as a Pipelines server (section 5.13). Pipelines section: the selected server answered but has nothing installed | Escalate if a Pipelines server is expected | **Admin Settings > Connections** shows the Pipelines icon on that connection (section 11.6) |
| `Pipeline downloaded successfully` | Success | `src/lib/components/admin/Settings/Pipelines.svelte:149-150` (install from a URL), `:181-182` (upload) | The Pipelines server accepted the pipeline; the same text is used for an upload | — | None |
| `Pipeline deleted successfully` | Success | `src/lib/components/admin/Settings/Pipelines.svelte:224-225` | **Delete** pressed; there is no confirmation dialog | — | None |
| `Valves updated successfully` | Success | `src/lib/components/admin/Settings/Pipelines.svelte:75-76` | **Save** stored the selected pipeline's valves on the Pipelines server; the next row follows | — | None |
| `Settings saved successfully!` | Success | `src/lib/components/chat/SettingsModal.svelte:903-908` | Shown after pipeline valves are saved | — | None |
| `No valves to update` | Error | `src/lib/components/admin/Settings/Pipelines.svelte:51-55`, `:88-90` | **Save** pressed before the pipeline list loaded, or the selected pipeline has no valves | — | None |
| `No valves` | Notice | `src/lib/components/admin/Settings/Pipelines.svelte:457-459` | The selected pipeline has no valves | — | None |
| `Something went wrong :/` | Error | `src/lib/components/admin/Settings/Pipelines.svelte:165-179` | **Upload** failed for any reason; the server's explanation goes only to the browser console | Check that the file is a pipeline `.py` file; escalate | Server log `Connection error: {e}` in the same minute |
| `No file selected` | Error | `src/lib/components/admin/Settings/Pipelines.svelte:193-195` | **Upload** pressed with no file chosen | Choose a file | None |
| `Only Python (.py) files are allowed.` | Error, **not shown** | `backend/open_webui/routers/pipelines.py:233-238` | Upload of a file whose name does not end in `.py`; the panel shows `Something went wrong :/` instead | Choose a `.py` file | None |
| `Pipeline not found` | Error | `backend/open_webui/routers/pipelines.py:286-304` (upload), `:342-358` (install), `:392-408` (delete), `:427-443` (list), `:474-490` (read valves), `:514-530` (valves definition), `:556-573` (save valves) | MedIT GPT could not complete the call to the Pipelines server and that server gave no explanation: it is unreachable, the address is wrong, the key was refused, the answer was unexpected, or the server's position in the connection list no longer exists. HTTP 404 when no answer came at all. Seen on install, delete and valves save | Escalate | Log `Connection error: {e}` gives the real cause |
| `{detail}` (Pipelines server) | Error | Same lines as the previous row | The Pipelines server refused and gave its own reason, which is not part of this repository | Read the text | The Pipelines server's own logs (outside MedIT GPT) |
| `Pipelines are a plugin system with arbitrary code execution.` | Warning | `src/lib/components/admin/Settings/Pipelines.svelte:333-336` | Description under **GitHub URL**, always shown | Install only reviewed pipelines | None |
| `Don't fetch random pipelines from sources you don't trust.` | Warning | `src/lib/components/admin/Settings/Pipelines.svelte:333-336` | Same description | — | None |
| `{COUNT} pipeline(s) selected` | Notice | `src/lib/components/admin/Settings/Pipelines.svelte:313-317` | A file was chosen for upload | — | None |

### 10.5 Messages Inside Chats When a Pipe, Filter or Action Fails

The `{e}` in these rows is written by the function's code (or by a Python library it uses), so it
cannot be catalogued; the rows say where it appears and what support can check.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Uh-oh! There was an issue with the response.`, then `{e}` on the next line | Error | `backend/open_webui/functions.py:308-324`; `backend/open_webui/utils/middleware.py:5226-5249`; `src/lib/components/chat/Chat.svelte:2799-2801`, `:3716-3747`; `src/lib/i18n/locales/en-US/translation.json:3324` | A **pipe** model raised an error when it was called, while the answer streams. A pop-up repeats `{e}`. After a reload the box shows `{e}` alone (`src/lib/components/chat/Messages/Error.svelte:6-37`) | Retry once; report the text | The model id (a function ID, or `{function id}.{sub id}` for a manifold), the text and the time; logs `Error: {e}` and `Provider returned error (streaming): {error}` |
| `{e}` (pipe, not streamed) | Error | `backend/open_webui/functions.py:345-350`; `backend/open_webui/utils/middleware.py:4230-4256`; `src/lib/components/chat/Chat.svelte:1284-1292` | The same failure when the answer is not streamed: the box shows the text without the prefix and without a pop-up | As above | Logs `Error: {e}` and `Provider returned error (non-streaming): {error}` |
| `{e}` (filter) | Error | `backend/open_webui/utils/middleware.py:2655-2670` (inlet), `:3261-3272` (request); `backend/open_webui/main.py:1686-1713`; `backend/open_webui/utils/filter.py:188-205` | An `inlet` or `request` **filter** refused the message with its own text, crashed, or could not be loaded. A loading error (for example a missing module) is shown as the text, and the loader switches that filter off, so the next message can go through without it (`backend/open_webui/utils/plugin.py:307-313`) | Read the text; retry once | The model's filters; log `Error processing chat payload: {error_detail}`; `Error in request filter {id}` for request filters (inlet failures are logged at debug level only, `backend/open_webui/utils/filter.py:201-202`) |
| `{detail}` or the HTTP reason (Pipelines inlet) | Error | `backend/open_webui/routers/pipelines.py:104-120`; `backend/open_webui/main.py:1686-1713` | A Pipelines filter, or a pipe pipeline called as a filter, answered with an error status | Retry; report the text | The Pipelines server's own logs |
| `{e}` (settings no longer fit the code) | Error | `backend/open_webui/functions.py:55-64` (pipes); `backend/open_webui/utils/filter.py:23-29`, `:188-205` (filters); `backend/open_webui/utils/actions.py:85-87` (actions) | Saved admin valves no longer match the function's settings after its code changed (a setting's type changed, or a new required setting was added); the text is the validation library's | Escalate | Log `Error loading valves for function {pipe_id}: {e}` for pipes; such a pipe also drops out of the model list (section 11.2) |
| `Model not found` | Error | `backend/open_webui/functions.py:288-290`; `backend/open_webui/utils/access_control/__init__.py:405`, `:409`, `:413`; `backend/open_webui/utils/actions.py:45-46`, `:59`; `backend/open_webui/utils/models.py:480`, `:491`, `:515`, `:521` | Chat with a pipe: the person may not use the pipe model's saved model record or its base model (`workspace-models-and-model-access.md`). Action: the reply's model is no longer in the model list, or the person lost access to it | Choose another model; reload the page | The model's access settings |
| `Function not found: {function_id}` | Error | `backend/open_webui/utils/plugin.py:387-390` | A pipe model whose function was deleted while a model list loaded earlier still offered it | Reload the page | Whether the function was deleted |
| `Error: {e}` | Error | `backend/open_webui/utils/actions.py:150-151`; `backend/open_webui/main.py:2110-2124`; `src/lib/components/chat/Chat.svelte:2590-2594` | An **action** raised an error while running. A pop-up shows the text and the error is attached to the reply | Retry; report the text | The action's name (its button tooltip) and the text |
| `Action not available: {action_id}` | Error | `backend/open_webui/utils/actions.py:53-54`, `:58-64` | The action was switched off or is no longer an action, or (for non-admins) it is no longer assigned to the model and not global; typically the page was loaded before an administrator changed it | Reload the page | The action's switch and the model's **Actions** |
| `Action not found: {action_id}` | Error | `backend/open_webui/utils/actions.py:28-30` | The action's function was deleted after the page loaded | Reload the page | None |
| `Plugins are disabled by ENABLE_PLUGINS=false` | Error | `backend/open_webui/utils/actions.py:20-21`; `backend/open_webui/utils/plugin.py:260-261` | Plugins were switched off on the server while an older page still showed the button | Reload the page | `ENABLE_PLUGINS` (section 7.1) |
| `Channel chats are not supported on this endpoint` | Error | `backend/open_webui/main.py:2076-2081` | An action was called for a channel conversation | — | None |
| `Something went wrong :/` | Error | `backend/open_webui/main.py:2083-2087`; `backend/open_webui/constants.py:16-18` | A non-administrator ran an action on a chat that is not theirs | — | Who owns the chat |
| `Error submitting message` | Error | `src/lib/components/chat/Messages/Error.svelte:37` | An error box with no text, for example after a reload when a pipe raised an error with an empty message | Retry | None |

### 10.6 Starter-Code Texts That Can Appear in Chats

The editor offers two starters, **Filter** and **Event** (section 5.1). The Event starter shows
nothing to people; it only prints each event to the server log
(`src/lib/components/admin/Functions/FunctionEditor.svelte:127-158`).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Conversation turn limit exceeded. Max turns: {max_turns}` | Error (in the reply's error box) | `src/lib/components/admin/Functions/FunctionEditor.svelte:90-107` | A function saved from the **Filter** starter without changes, switched on, and global or attached to the model. Its `inlet` refuses any request that carries more messages (the person's and the model's together) than the smaller of the person's `max_turns` (default 4) and the administrator's `max_turns` (default 8) (`:64-77`, `:101`), for users and administrators alike (`:98`). With the defaults the third question in a chat is refused | Start a new chat as a stopgap; escalate | Which filters are switched on and global (section 11.7) |
| ` - @@Modified from Filter Outlet` | Notice (appended text) | `src/lib/components/admin/Functions/FunctionEditor.svelte:174`, `:234-242` | Not offered by the editor: an older combined example is kept unused in the file (`_boilerplate`; the starter menu only switches between the Filter and Event starters, `:159-172`). A function copied from that example appends this to every message after the answer | Escalate | The installed function is based on the old example |
| `Could not fetch models from OpenAI, please update the API Key in the valves.` | Notice (model name) | `src/lib/components/admin/Functions/FunctionEditor.svelte:282-290` | The same old example's pipe lists a single model with this name when it cannot reach its provider | Escalate | That pipe's valves (address and key) |
| `Error: {e}` | Error (answer text) | `src/lib/components/admin/Functions/FunctionEditor.svelte:310-325` | The same old example's pipe answers with this text when its provider call fails | Escalate | As above |

### 10.7 Server Log Lines (Not Shown to Users)

Logs go to standard output (`tools/ground-truth.md`). `{e}` is the underlying error text.

| Log line | Level | Source | What it tells support |
|---|---|---|---|
| `Error loading module: {function_id}: {e}` | Error | `backend/open_webui/utils/plugin.py:307-308` | A function's code failed to load; the function has been **switched off** in the database |
| `Loaded module: function_{function_id}` | Info | `backend/open_webui/utils/plugin.py:294` | A function was (re)loaded in this worker |
| `Installing requirements: {packages}` | Info | `backend/open_webui/utils/plugin.py:440` | `pip` is installing packages a function or tool listed |
| `Error installing packages: {packages}` | Error | `backend/open_webui/utils/plugin.py:445-447` | That installation failed |
| `No requirements found in frontmatter.` | Info | `backend/open_webui/utils/plugin.py:449-450` | The code lists no packages |
| `ENABLE_PIP_INSTALL_FRONTMATTER_REQUIREMENTS is disabled, skipping installation of requirements.`, `Offline mode enabled, skipping installation of requirements.`, `ENABLE_PLUGINS is disabled, skipping tool and function dependencies.` | Info | `backend/open_webui/utils/plugin.py:424-430`, `:461-463` | Installation skipped (section 8.1) |
| `Installing external dependencies of functions and tools...` | Info | `backend/open_webui/main.py:385-388` | The blocking start-up installation has begun (section 8.1) |
| `Error installing requirements: {e}` | Error | `backend/open_webui/utils/plugin.py:483-484` | The start-up installation failed; start-up continues |
| `SAFE MODE ENABLED` | Printed | `backend/open_webui/main.py:280-282` | Safe mode is on; every function will be switched off at start-up |
| `Failed to extract frontmatter: {e}` | Error | `backend/open_webui/utils/plugin.py:180-182` | The opening comment could not be read; the manifest is empty |
| `options '{options}' not found or not callable on {class}`, `Method '{options}' did not return a list for {prop_name}`, `Failed to resolve options for {prop_name}: {e}` | Warning | `backend/open_webui/utils/plugin.py:108-135` | A drop-down setting's choices could not be built; the form shows it without them |
| `Failed to create a new function: {e}` | Error | `backend/open_webui/routers/functions.py:252-253` | Cause of `[ERROR: Error creating function]` |
| `Error creating a new function: {e}` | Error | `backend/open_webui/models/functions.py:136-138` | The database refused a new function |
| `Failed to load a function: {e}`, `Error validating valves for function {id}: {e}` | Error | `backend/open_webui/routers/functions.py:182-188` | Bulk sync failed |
| `Error syncing functions for user {user_id}: {e}` | Error | `backend/open_webui/models/functions.py:180-182` | Bulk sync failed in the database; the call returns an empty list |
| `Error updating function values by id {id}: {e}`, `Error updating function user valves by id {id}: {e}` | Error | `backend/open_webui/routers/functions.py:545-546`, `:653-654` | Valve values did not validate |
| `Error getting function valves by id {id}: {e}`, `Error batch-fetching function valves: {e}` | Error | `backend/open_webui/models/functions.py:299-301`, `:315-317` | Stored admin valves could not be read; defaults apply |
| `Error getting user values by id {id} and user id {user_id}` | Error | `backend/open_webui/models/functions.py:371-373` | A person's valves could not be read; defaults apply |
| `Error updating user valves by id {id} and user_id {user_id}: {e}` | Error | `backend/open_webui/models/functions.py:394-396` | A person's valves were **not** saved although the browser reported success (section 11.12) |
| `Error updating function metadata by id {id}: {e}` | Error | `backend/open_webui/models/functions.py:350-352` | The toggle flag could not be recorded |
| `Failed to decrypt valves: {type}` | Warning | `backend/open_webui/utils/valves.py:35-39` | Stored valves could not be read and defaults apply. Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca) |
| `Error loading valves for function {pipe_id}: {e}` | Error | `backend/open_webui/functions.py:62-64` | A pipe's saved valves no longer fit its code; the pipe drops out of the model list and its chats fail |
| `Error getting OAuth token: {e}` | Error | `backend/open_webui/functions.py:265-266` | A pipe could not be given the person's single sign-on token; the pipe still runs without it |
| `Error: {e}` | Error | `backend/open_webui/functions.py:322`, `:349` | A pipe raised an error (10.5) |
| `Provider returned error (streaming): {error}`, `Provider returned error (non-streaming): {error}` | Error | `backend/open_webui/utils/middleware.py:5229`, `:4238` | The answer carried an error, including a pipe's |
| `Failed to get user valves for filter {id}` | Error | `backend/open_webui/utils/filter.py:196-197` | A filter ran without the person's valves |
| `Error in inlet filter {id}` | Debug | `backend/open_webui/utils/filter.py:201-202` | An inlet filter failed (only visible with debug logging) |
| `Error in {type} filter {id}` | Error | `backend/open_webui/utils/filter.py:203-204` | A `request`, `stream` or `outlet` filter failed |
| `Error processing chat payload: {error_detail}` | Error | `backend/open_webui/main.py:1686-1688` | A chat turn stopped before the model was called, for example because of an inlet filter |
| `Pipeline outlet filter error: {e}`, `Error running outlet filters: {e}` | Debug | `backend/open_webui/utils/middleware.py:4146-4149`, `:4207-4208` | An outlet filter (Pipelines or function) failed; the answer stays unchanged |
| `Failed to get user values: {e}` | Error | `backend/open_webui/utils/actions.py:119-120` | An action ran without the person's valves |
| `Failed to load function module for {id}: {e}` | Debug | `backend/open_webui/utils/models.py:332-335` | While building the model list, a filter or action failed to load |
| `Action not found: {id}`, `Failed to load action module: {id}`, `Filter not found: {id}`, `Failed to load filter module: {id}` | Info | `backend/open_webui/utils/models.py:405-413`, `:425-433` | A model lists an action or filter that does not exist or did not load; its button or switch is left out |
| `Event functions could not be loaded for {event}`, `Event function failed for {id}`, `Event functions could not be scheduled for {event}` | Error | `backend/open_webui/events.py:1123-1125`, `:1155-1156`, `:1159-1163` | Event-function delivery problems (section 8.3) |
| `Event sink failed for {event}` | Error | `backend/open_webui/events.py:1199-1202` | One receiver of an event failed; the others still ran |
| `Connection error: {e}` | Error | `backend/open_webui/routers/pipelines.py:124`, `:190`, `:288`, `:344`, `:394`, `:429`, `:476`, `:516`, `:558` | A call to a Pipelines server failed; the text names the cause |
| `upload_pipeline: urlIdx={urlIdx}, filename={filename}` | Info | `backend/open_webui/routers/pipelines.py:230` | An administrator uploaded a pipeline file |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it gathers facts, gives guidance and escalates. It does not install, edit,
switch on or off, make global, configure or delete functions or pipelines, and does not change
valves, models, permissions or settings. Who receives escalations for functions and pipelines (the
"platform administrator" below) is **TO BE CONFIRMED**, and so is whether tier 1 can open the admin
Functions page or the server logs. Never ask anyone to send function code, exported function files
or valve values: they can contain keys. Do not copy chat content into a ticket, because chats can
contain personal or health information; send the chat's address (`/c/{id}`), the model name, the
time with its time zone, and the exact error text.

### 11.1 "The model answered with an error box instead of a reply"

**Symptom.** With one particular model, the reply is a grey box, often starting
`Uh-oh! There was an issue with the response.` with a second line of text, and a red pop-up
repeats that line. After a reload the box shows only the second line.

**Likely causes, in order.**
1. The model is a **pipe** and its code raised an error, often because the outside service it calls
   refused, timed out or is down. The second line is the pipe's own text
   (`backend/open_webui/functions.py:308-324`, `:345-350`; 10.5).
2. The pipe's saved settings no longer fit its code after an update; the text is then a validation
   message (`backend/open_webui/functions.py:55-64`).
3. A filter on that model refused or failed (11.3). The box then shows only the filter's text,
   without the `Uh-oh!` line (`backend/open_webui/main.py:1686-1713`).
4. The model is an ordinary provider model and the provider sent the error:
   `chat-completion-pipeline-and-generation-tasks.md` section 11.6.
5. The pipe failed after it had started streaming. The pipe wrapper catches only errors raised
   when the pipe is first called (`backend/open_webui/functions.py:308-324`), so what the person
   sees in that case is not established (section 14); see
   `chat-completion-pipeline-and-generation-tasks.md` section 11.2.

**Diagnostic steps.** Ask for the model name, the exact text in the box and the time. Ask whether
the same question works with another model (a failure limited to one model points to that model's
pipe or filters) and whether colleagues see it with the same model. In the administrator's view,
the Functions list labels each function with its type, so a pipe shows `pipe`
(`src/lib/components/admin/Functions.svelte:519-523`).

**Resolution.** Suggest another approved model for urgent work. Tier 1 cannot repair a pipe.

**Escalation.** Send the model name, the error text, the time, the chat's address and whether
everyone is affected. The platform administrator matches the time with the log lines `Error: {e}`
and `Provider returned error (streaming): {error}` (10.7).

### 11.2 "A function model disappeared from the model list"

**Symptom.** A model that a pipe provides is no longer in the model picker, for one person or for
everyone. Chats that used it may report that the model is not found.

**Likely causes, in order.**
1. The pipe's code failed to load during an ordinary request (after an edit, or when a package it
   needs is missing from a rebuilt container) and the loader switched it off
   (`backend/open_webui/utils/plugin.py:307-313`; section 8.2). Its **Updated at** time on the
   Functions list then moves to the moment of the failure although nobody edited it
   (`backend/open_webui/models/functions.py:398-415`; `src/lib/components/admin/Functions.svelte:541-547`).
   The code's own start-up comment gives this as the reason packages are installed before serving:
   `This should be blocking (sync) so functions are not deactivated on first /get_models calls`
   (`backend/open_webui/main.py:385-388`).
2. The pipe's saved settings no longer fit its code. The pipe is then left out of the list (skipped,
   not switched off) (`backend/open_webui/functions.py:55-64`, `:146-148`).
3. A manifold pipe could not list its sub-models (its provider was unreachable), so it offers none
   (`backend/open_webui/functions.py:86-103`).
4. Every function was switched off by safe mode at start-up (11.15), or plugins are switched off on
   the server (`ENABLE_PLUGINS`, section 7.1).
5. Only that person lost it: no model record gives them access, or their access was removed;
   administrators still see the model (section 3.2; `workspace-models-and-model-access.md`).
6. The model list is cached (`models.base_models_cache`) and was not refreshed after a change
   (section 8.4).
7. The function was deleted (event `function.deleted`, section 9.3).

**Diagnostic steps.** Ask whether colleagues still see the model: everyone affected points to
causes 1 to 4, 6 and 7; one person points to cause 5. In the administrator's view, check whether the
pipe is switched off and whether its **Updated at** time is recent.

**Resolution.** Explain that the model is provided by an administrator-managed function and suggest
another approved model meanwhile.

**Escalation.** Send the model name, when it was last seen, who is affected, and the person's
account email when only one person is affected. The platform administrator looks for
`Error loading module: {function_id}: {e}` or `Error loading valves for function {pipe_id}: {e}`
(10.7), fixes the code, its packages or its settings, and switches the pipe back on.

### 11.3 "A filter stopped working after an update"

**Symptom.** After an administrator changed a filter, or after a release or restart, either every
message with some models fails with an error box, or the filter's effect (for example text it used
to remove or add) silently stops.

**Likely causes, in order.**
1. The new code fails to load. The first message afterwards fails with the loading error as its
   text, the loader switches the filter off, and later messages go through **without** the filter
   (`backend/open_webui/utils/middleware.py:2655-2670`; `backend/open_webui/utils/plugin.py:307-313`).
2. The saved administrator settings no longer fit the new code (a changed type, a new required
   setting). Every message with that filter then fails with a validation text, and the filter stays
   on (`backend/open_webui/utils/filter.py:23-29`, `:188-205`).
3. A setting was renamed. The saved value is passed to the new code under its old name
   (`backend/open_webui/utils/filter.py:28`), and Pydantic, the settings library, ignores names a
   settings class does not declare unless the class says otherwise, so the new setting starts at
   its default.
4. The filter became toggleable, or is no longer global or attached to the model. A toggleable
   filter runs only when the person switches it on in the chat (`backend/open_webui/utils/filter.py:76-85`;
   section 3.2).
5. Its `stream` hook now fails, so chunks are dropped (11.13); a failing `outlet` hook leaves answers
   unchanged and is logged at debug level only (section 5.10).
6. Packages the new code needs did not install: the save showed `[ERROR: Error updating function]`
   (10.1), or a rebuilt container lost them and reinstalling failed (section 6.2).

**Diagnostic steps.** Ask when the change happened and what the person sees. Note the exact text
and time of the first failure. Ask whether a model without that filter works.

**Resolution.** Guidance only. Whether people may switch to a model without a particular filter
(some filters may be required, for example for privacy) is **TO BE CONFIRMED**.

**Escalation.** Send the model, the first error text and its time, and the filter's name if known.
The platform administrator compares the log lines `Error loading module: {function_id}: {e}`,
`Error in {type} filter {id}` and `Error processing chat payload: {error_detail}` (10.7) with the
filter's switch.

### 11.4 "The action button does nothing"

**Symptom.** A button under a reply (an icon whose tooltip is the action's name) is clicked and
nothing seems to happen, or an expected button is missing.

**Likely causes, in order.**
1. The action is still working. The button shows no progress indicator while the server runs the
   action (`src/lib/components/chat/Messages/ResponseMessage.svelte:1506-1545`;
   `src/lib/components/chat/Chat.svelte:2571-2594`).
2. The action finished but returned nothing to show. The reply changes only when the action
   returns messages or sends content (`src/lib/components/chat/Chat.svelte:2595-2606`;
   `backend/open_webui/utils/actions.py:124-148`).
3. The action asked a question and is waiting. Its dialog appears only in the tab that was clicked,
   and with no time limit set by default an unanswered question keeps the action waiting
   (section 9.2; `backend/open_webui/socket/main.py:1258-1281`; `backend/open_webui/env.py:534-542`).
4. It failed and the pop-up was missed. The error text is also attached to the reply
   (`src/lib/components/chat/Chat.svelte:2590-2594`; messages in 10.5).
5. The button is missing. On earlier replies the action buttons appear only while the pointer is
   over the reply, unless high-contrast mode is on
   (`src/lib/components/chat/Messages/ResponseMessage.svelte:1522-1524`). Otherwise the action is
   switched off, is neither attached to this model nor global, or failed to load and was left out
   (`backend/open_webui/utils/models.py:385-419`; log `Failed to load action module: {id}`, 10.7).
6. **Regenerate** does not run actions (section 5.11).

**Diagnostic steps.** Ask which reply and which button (its tooltip), whether a pop-up appeared,
whether an error now shows under the reply, and whether other actions or colleagues work. Ask the
person to wait a minute, keep a single tab open and look for a dialog.

**Resolution.** Reload the page, which refreshes the model's list of actions, and try again; hover
over earlier replies to reveal their buttons.

**Escalation.** Send the action's name, the model, the time, the chat's address and any error
text. The platform administrator checks the action's switch, its assignment to the model and the
log.

### 11.5 "The server takes ages to start" (Admins)

**Symptom.** After a restart or deployment MedIT GPT does not answer for a long time, or a monitor
reports it not ready although `/health` already answers.

**Likely causes, in order.**
1. Each worker installs, with `pip` and before serving, the packages listed by every switched-on
   function and every administrator's tool, with no time limit; a slow or unreachable package
   index stretches start-up (`backend/open_webui/main.py:385-388`;
   `backend/open_webui/utils/plugin.py:422-484`; section 8.1). Whether production servers can reach
   a package index is **TO BE CONFIRMED**.
2. With `models.base_models_cache` on, start-up also builds the model list, which loads every
   switched-on pipe and asks each manifold for its sub-models; a slow outside service delays
   readiness (`backend/open_webui/main.py:407-429`).
3. Several workers each repeat this work (section 8.1).
4. The container was rebuilt, so every package is downloaded again (section 6.2).

`/health` answers as soon as the web server runs, while `/ready` answers 503 until start-up is
complete (`backend/open_webui/main.py:2963-2976`, `:471`; `CLAUDE.md`, Deployment).

**Diagnostic steps.** Note when the problem started and ask the platform administrator whether a
restart or deployment happened.

**Resolution.** None for tier 1; tell users that the service is starting.

**Escalation.** Send the time and the symptom. The platform administrator reads the start-up log
for `Installing external dependencies of functions and tools...`,
`Installing requirements: {packages}`, `Error installing packages: {packages}` and
`Error installing requirements: {e}` (10.7). The settings that change this behaviour (`OFFLINE_MODE`,
`ENABLE_PIP_INSTALL_FRONTMATTER_REQUIREMENTS`, `PIP_OPTIONS`, `PIP_PACKAGE_INDEX_OPTIONS`, section
7.1) are platform decisions.

### 11.6 "The Pipelines server won't connect" or "It says 'Pipelines Not Detected'" (Admins)

**Symptom.** **Admin Settings > Pipelines** shows `Pipelines Not Detected` or keeps spinning, or a
pipeline model or Pipelines filter stops working.

**Likely causes, in order.**
1. The connection is not recognized as a Pipelines server: the OpenAI API is switched off, the
   connection is disabled or has a fixed model-id list, or its model list did not answer with the
   Pipelines marker within the model-list time limit (`AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST`, default
   10 seconds) (section 7.2; `backend/open_webui/routers/openai.py:676-720`;
   `backend/open_webui/routers/pipelines.py:204-220`; `backend/open_webui/env.py:656-663`).
2. The Pipelines server is down, has moved, or refuses the key. The panel then keeps spinning,
   because reading the list of pipelines has no error handling
   (`src/lib/components/admin/Settings/Pipelines.svelte:119-136`, `:468-472`), and install, delete
   and valves save answer `Pipeline not found` (10.4).
3. The Pipelines server's certificate cannot be verified. With the code default of
   `AIOHTTP_CLIENT_SESSION_SSL`, every call the Pipelines routes make checks the certificate
   (section 7.1). The fix belongs on the certificate; switching the check off is not a remedy.
4. `Pipelines Not Detected` under the **Pipelines** heading (rather than **Source**) means the
   server was found but has no pipelines installed
   (`src/lib/components/admin/Settings/Pipelines.svelte:461-466`).
5. In chats, a Pipelines filter is skipped without notice when its connection has no key or the
   server cannot be reached (section 5.15).

**Diagnostic steps.** Ask the administrator whether **Admin Settings > Connections** shows the
Pipelines icon on that connection
(`src/lib/components/admin/Settings/Connections/OpenAIConnection.svelte:68-89`) and when it last
worked.

**Resolution.** None for tier 1.

**Escalation.** Send the time and what the panel shows. The platform administrator checks the log
for `Connection error: {e}` (10.7) and the Pipelines server itself, which runs outside this
repository (where it runs is **TO BE CONFIRMED**).

### 11.7 "Every chat stops after a few questions with 'Conversation turn limit exceeded'"

**Symptom.** From the third question in any chat, the reply is an error box reading
`Conversation turn limit exceeded. Max turns: 4` (or another number).

**Likely causes, in order.**
1. A function saved from the **Filter** starter code without changes is switched on and is global
   or attached to the model (10.6; `src/lib/components/admin/Functions/FunctionEditor.svelte:90-107`).
2. A limit configured on purpose with that code's settings. Whether MedIT GPT intends any turn limit
   is **TO BE CONFIRMED**.

**Diagnostic steps.** Ask whether new chats work for the first two questions (they do with the
starter's defaults) and whether every model is affected.

**Resolution.** A new chat works around it for two questions. Tier 1 does not change valves; the
real fix is the administrator's.

**Escalation.** Send the exact text, the affected models and when it started. The platform
administrator finds the filter on the Functions list (type `filter`). Its code still begins with
the starter's opening comment (`title: Example Filter`, `version: 0.1`,
`src/lib/components/admin/Functions/FunctionEditor.svelte:51-57`), so the list shows `v0.1` beside
its name (`src/lib/components/admin/Functions.svelte:533-539`); the name itself is whatever the
administrator typed, or `Example Filter` when the name was empty and the code was edited first
(`src/lib/components/admin/Functions/FunctionEditor.svelte:477-483`). The administrator then
switches it off or corrects it.

### 11.8 "I can't find the Functions page" (Admins)

**Symptom.** An administrator does not see **Functions** in the Admin Panel, or `/admin/functions`
sends them elsewhere; or someone looks for functions in the Workspace.

**Likely causes, in order.**
1. The account is not an administrator; the Admin Panel sends it to `/`
   (`src/routes/(app)/admin/+layout.svelte:14-16`).
2. Plugins are switched off on the server (`ENABLE_PLUGINS`): the tab is hidden and the pages go to
   `/admin` (`src/routes/(app)/admin/+layout.svelte:17-22`, `:87-95`;
   `src/routes/(app)/admin/functions/+page.svelte:9-13`).
3. The wrong place: functions live only in the Admin Panel. **Workspace > Tools** holds tools, which
   are a different feature (section 1). The old address `/workspace/functions/create` forwards to
   the admin editor (section 2.1).

**Diagnostic steps.** Confirm the account's role and ask whether other administrators see the tab.

**Resolution.** Explain where functions live and that only administrators manage them.

**Escalation.** If no administrator sees the tab, tell the platform administrator that plugins may
be switched off (a platform decision).

### 11.9 "I switched a function on but nothing changed" (Admins)

**Symptom.** The switch on the Functions list was turned on, but the pipe model, filter, action
button or event behaviour does not appear, or the switch is off again later.

**Likely causes, in order.**
1. The change was not saved. This switch shows no confirmation and no error, and moves even when
   the server refused (section 5.5); reloading the page shows the stored state.
2. The model list was refreshed before the change was stored: the page asks for the new list
   without waiting for the switch to be saved (`src/lib/components/admin/Functions.svelte:705-716`).
   Reloading the page helps.
3. Switching on is not enough. A filter or action must also be global or attached to the model; a
   toggleable filter must also be switched on by the person in the chat; a pipe reaches users only
   through model access (section 3.2).
4. The code fails to load, so its first use switches it off again (section 8.2; 11.2, cause 1).
5. An Event function only reacts to events and shows nothing (section 9.4).

**Diagnostic steps.** Ask the administrator to reload the Functions page and check the switch and
the **Updated at** time.

**Resolution.** Guidance as above.

**Escalation.** If the switch does not stay on after a reload, send the function's name and the
time to the platform administrator (log lines in 10.7).

### 11.10 "I clicked Save & Create and nothing happened" (Admins)

**Symptom.** After **Save & Create** (and confirming), or **Save** when editing, no success pop-up
appears and the editor stays open; sometimes `Code formatted successfully` appears and then nothing.

**Likely causes, in order.**
1. The name or description contains only spaces, or the editor shows a translation language and the
   base name or description is empty. The editor then hits a script error instead of showing
   `Name and description are required` (10.2): it switches back to the base language and saves
   nothing.
2. The server's answer carried no text: the connection dropped, or something in front of MedIT GPT
   gave up while the server was still installing the function's packages (a save waits for `pip`,
   section 8.4). These calls show nothing in that case (section 10, introduction). Whether a proxy
   with a time limit sits in front of production is **TO BE CONFIRMED**.
3. The confirmation dialog was closed with **Cancel**.

Failures that do show a pop-up (an ID problem, a code problem, a version requirement) are in 10.1
and 10.2.

**Diagnostic steps.** Ask what the name and description fields contain and whether the language
selector beside the starter menu is set to another language. For cause 2, ask whether the function
appears on the list after a reload: the save may have completed, and saving again would then report
that the ID is taken.

**Resolution.** Enter real text in both fields with the base language selected, then save again.

**Escalation.** If it still fails, send the time and the Function ID to the platform administrator;
the log shows whether the request reached the server (10.7).

### 11.11 "It said 'Functions imported successfully' but the functions aren't there" (Admins)

**Symptom.** After **Import JSON** the success pop-up appeared, but some or all functions are
missing, or they are listed but do nothing.

**Likely causes, in order.**
1. Individual functions failed (an ID already used, code that does not load, missing fields). Each
   failure showed its own pop-up before the success message, which appears regardless
   (`src/lib/components/admin/Functions.svelte:794-806`; 10.1, 10.2).
2. They were imported but are switched off, not global and with default valves: imports never
   carry those over (section 5.3).
3. Nothing happened at all and no pop-up appeared: the file is not valid JSON or does not hold a
   list, and the import stopped with a script error before its first step
   (`src/lib/components/admin/Functions.svelte:789-794`).

**Diagnostic steps.** Ask which pop-ups appeared, in order, and whether the file came from
**Export JSON** on a MedIT GPT system.

**Resolution.** Explain that imported functions must be switched on, and made global or attached to
models, by an administrator.

**Escalation.** Send the pop-up texts and where the file came from, not the file itself (it holds
code and may hold keys).

### 11.12 "My valves settings don't stick"

**Symptom.** A person or an administrator changes a function's settings and sees `Valves updated`
or `Valves updated successfully`, but the function behaves as before; or the form shows `No valves`.

**Likely causes, in order.**
1. The setting was left at, or set back to, **Default**. Settings at **Default** are not stored, so
   the function's own default applies (`backend/open_webui/routers/functions.py:532-537`, `:640-643`).
2. The database write failed but the browser still reported success. The server does not check the
   result of saving, and a failed save of administrator valves leaves no log line at all
   (`backend/open_webui/routers/functions.py:536-544`, `:643-652`;
   `backend/open_webui/models/functions.py:319-330`, `:375-396`). A failed save of a person's valves
   is logged as `Error updating user valves by id {id} and user_id {user_id}: {e}` (10.7).
3. The function's code changed and the setting was renamed or retyped (11.3, causes 2 and 3).
4. `No valves`: the function declares no settings, is switched off, or its code fails to load
   (10.3).
5. Expectations about scope: a person's settings apply only to that person and administrators'
   settings to everyone, and the function's code decides how they combine (the Filter starter, for
   example, uses the smaller of the two limits,
   `src/lib/components/admin/Functions/FunctionEditor.svelte:101`).
6. Stored values cannot be read, so the defaults apply (log `Failed to decrypt valves: {type}`).
   Security-sensitive: refer to the platform maintainer and U of T Information Security
   (security.utoronto.ca).
7. The **Valves** section is missing from the chat **Controls** panel: the person lacks the
   `chat.controls` or `chat.valves` permission (section 3.3).

**Diagnostic steps.** Ask which function, where the setting was changed (Controls panel,
Integrations menu, composer Valves button, or the administrator's gear icon), whether a **Custom**
value was chosen, and whether reopening the form shows it.

**Resolution.** Guide the person to choose **Custom**, enter the value, save, and reopen the form to
confirm it was kept.

**Escalation.** Send the function's name, the time of the save and the person's account email. Do
not send the values themselves when they could be keys or passwords.

### 11.13 "Words are missing from answers" or "The answer changed after it finished"

**Symptom.** Streamed answers have gaps, a finished answer is replaced with different text, or text
such as ` - @@Modified from Filter Outlet` is added to messages.

**Likely causes, in order.**
1. A `stream` filter fails on some chunks, which are then dropped without notice (section 5.10;
   `backend/open_webui/utils/middleware.py:5098-5109`, `:5725-5733`).
2. An `outlet` filter rewrote the answer after it finished; the original is kept as
   `originalContent` (section 5.10; `backend/open_webui/utils/middleware.py:4173-4206`).
3. An action replaced the message (section 5.11).
4. A function based on the old example code adds its marker (10.6).
5. Causes unrelated to functions: `chat-completion-pipeline-and-generation-tasks.md` section 11.2.

**Diagnostic steps.** Ask whether it happens with every model or one, and since when.

**Resolution.** None for tier 1.

**Escalation.** Send the model, an example chat's address and the time. The platform administrator
checks that model's filters and the log line `Error in {type} filter {id}` (10.7).

### 11.14 "The filter switch I expect isn't in my Integrations menu"

**Symptom.** A person expects a switch for an optional feature provided by a filter in the
composer's **Integrations** menu and does not see it, or the knobs (valves) icon beside it is
missing.

**Likely causes, in order.**
1. Only **toggleable** filters that are switched on and either global or attached to the selected
   model appear (`backend/open_webui/utils/models.py:385-441`).
2. With several models selected, only filters shared by **all** of them appear
   (`src/lib/components/chat/MessageInput.svelte:811-814`).
3. The filter failed to load while the model list was built and was left out (log
   `Failed to load filter module: {id}`, 10.7).
4. The browser's model list is older than the change; reloading the page fetches it again.
5. The knobs icon is hidden for people without the `chat.valves` permission (section 3.3).

**Diagnostic steps.** Ask which model or models are selected and whether a colleague with the same
model sees the switch.

**Resolution.** Select only the model the filter belongs to and reload the page.

**Escalation.** Send the model, the expected filter and the person's account email.

### 11.15 "All our functions are switched off" (Admins)

**Symptom.** Every function on the Functions list is switched off, often all with the same recent
**Updated at** time.

**Likely causes, in order.**
1. Safe mode (`SAFE_MODE`) is on: every start of every worker switches all functions off and stamps
   them with that time (`backend/open_webui/main.py:382-383`;
   `backend/open_webui/models/functions.py:417-429`). They stay off after safe mode is removed until
   someone switches them on again, one by one (section 7.1).
2. Several functions failed to load (for example after a container rebuild without their packages)
   and each was switched off at its first use (section 8.2); their times then differ.

**Diagnostic steps.** Ask whether the times are identical and match a restart, and ask the platform
administrator whether safe mode was used (start-up prints `SAFE MODE ENABLED`, 10.7).

**Resolution.** None for tier 1. Switching functions back on is an administrator decision, after
safe mode has been removed.

**Escalation.** Send the time of the change and the names of the affected functions.

### 11.16 "Import From Link says 'Failed to fetch the function'" (Admins)

**Symptom.** **Import From Link** shows `Failed to fetch the function`,
`No data received from the URL`, `[ERROR: Error fetching function]` or `[object Object]`.

**Likely causes, in order.**
1. The link points to a web page rather than a raw file. Only GitHub file (`blob`) and folder
   (`tree`) links are converted to raw links, and a folder link is expected to contain `main.py`
   (`backend/open_webui/routers/functions.py:90-104`).
2. The file is private, missing or rate-limited, so it answers with a status other than 200 (10.1).
3. The server cannot reach the host, or certificate checking fails (10.1). Whether production
   servers have outbound internet access is **TO BE CONFIRMED**.
4. The address is not `http` or `https` (`[object Object]`, 10.2).

**Diagnostic steps.** Ask for the link and check that it opens a plain code file in a browser.

**Resolution.** Suggest the raw-file link, and remind the administrator that a successful import
still needs **Save & Create**.

**Escalation.** If a valid public raw link fails, send the link and the time to the platform
administrator.

### 11.17 "Uploading or installing a pipeline fails" (Admins)

**Symptom.** In **Admin Settings > Pipelines**, **Upload** shows `Something went wrong :/`, or
**Install** shows `Pipeline not found` or another text.

**Likely causes, in order.**
1. Upload: the file is not a `.py` file, or the Pipelines server refused it. The panel hides the
   reason behind its generic text (10.4).
2. Install: the Pipelines server could not download the address or rejected the code. Its own reason
   is shown when it gives one, otherwise `Pipeline not found` (10.4).
3. The Pipelines server is unreachable (11.6).

**Diagnostic steps.** Ask which action, which file or address, and the time.

**Resolution.** None for tier 1.

**Escalation.** Send the time and the action to the platform administrator, who reads the log line
`Connection error: {e}` (10.7) and the Pipelines server's own logs.

## 12. Local Customisations

**Files in scope.** Read-only comparison of the fork with upstream v0.11.4
(`git diff main...uoft`) over every file listed in section 13 shows one change: the default product
name in `backend/open_webui/env.py:951`. The function router, model, loader, filter, action, valves
and event-dispatch code, the Pipelines router, the admin Functions and Pipelines screens, the valves
forms and the functions API client match upstream v0.11.4. The working tree (`git diff`) has no
uncommitted change in any of these files.

**Effects of fork changes on this area.**

| Change | Effect here | Evidence |
|---|---|---|
| Default `WEBUI_NAME` is `MedIT GPT`, without upstream's " (Open WebUI)" suffix | The Functions page's browser tab reads `Functions / MedIT GPT` (section 2.1), and event webhook posts about functions and pipelines are sent under that name (section 9.3). `WEBUI_NAME` is an environment value, so the live name is TO BE CONFIRMED | `backend/open_webui/env.py:951`; `src/lib/components/admin/Functions.svelte:314-316`; `tools/ground-truth.md` (Version and Identity) |
| Upstream wording kept on purpose | Several administrator texts still name **Open WebUI**: `Open WebUI version (v{OPEN_WEBUI_VERSION}) is lower than required version (v{REQUIRED_VERSION})`, `Redirecting you to Open WebUI Community`, and the **Show your support!** dialog. Each sits beside a licence comment that forbids changing it, and the fork leaves them unchanged | `src/routes/(app)/admin/functions/create/+page.svelte:25-36`; `src/lib/components/admin/Functions.svelte:164-167`; `src/lib/components/workspace/common/ManifestModal.svelte:46-52`; `CLAUDE.md` (Conventions) |
| Per-person **Hide Processing Details** setting (fork) | When a person switches it on: status lines that pipes, filters and actions send (section 9.2) are not shown; `<status …>` tags a pipe writes into its answer are not shown; `<details>` blocks of type reasoning or code interpreter that a pipe writes are dropped (tool-call blocks stay); code-execution panels are hidden; and while no answer text is visible the reply shows `Thinking...`. Pop-ups (`notification`), confirmation and input dialogs, error boxes and an action's embedded content still appear. A model whose **status updates** capability is off hides status lines for everyone, as upstream does | `src/lib/components/chat/Messages/ResponseMessage.svelte:197-202`, `:214-221`, `:720`, `:748-753`, `:920-921`, `:944`; `src/lib/components/chat/Messages/Markdown/HTMLToken.svelte:89-93`; `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte:62-99`; `src/lib/components/common/InterfaceSettings.svelte:1361-1377`; `src/lib/i18n/locales/en-US/translation.json:2923-2924` |
| Per-person **Inline Citations** setting (fork) | When switched off, numbered markers such as `[1]` are removed from answer text, including text a pipe writes; sources that a function sends (`source` or `citation` events) are still listed below the reply | `src/lib/components/chat/Messages/ContentRenderer.svelte:128-136`; `src/lib/i18n/locales/en-US/translation.json:2935-2936` |

The English texts of the two settings (**Settings > Interface**):

| Label | Description | Evidence |
|---|---|---|
| `Hide Processing Details` | `Show "Thinking..." instead of status updates, tool calls, reasoning, and code analysis while a response is generated, and keep them hidden afterwards. Tool approval requests and images or embeds from tools still appear.` | `src/lib/i18n/locales/en-US/translation.json:2923-2924` |
| `Inline Citations` | `Show source links within responses. When off, sources are still listed below each response.` | `src/lib/i18n/locales/en-US/translation.json:2935-2936` |

**Working-tree note.** The uncommitted changes in `src/lib/components/chat/Messages/ResponseMessage.svelte`
reorganize the Hide Processing Details code without changing the behaviour described above; the
line numbers cited are those of the working tree. The uncommitted change in
`src/lib/components/chat/Chat.svelte` (a reply resuming after a tool approval, `:2847-2850`) does
not touch the action and event handlers this document cites, but it shifts every later line of that
file by five; citations to `Chat.svelte` in this document are to the working tree.

No database migration, setting or permission in this area is local to the fork.

## 13. Source File Index

Every file cited in this document, grouped by where it sits. "In scope" files are the area's own;
the others are cited for one behaviour and are documented in the reference noted in section 1.

### 13.1 Backend, in Scope

| File | What it holds | Sections |
|---|---|---|
| `backend/open_webui/routers/functions.py` | The `/api/v1/functions` routes: list, admin list, export, import from a link, bulk sync, create, read, switch on or off, Global, update, delete, admin valves and a person's own valves | 2.2, 3, 5, 9.3, 10.1 |
| `backend/open_webui/models/functions.py` | The `function` table, its Pydantic models and the `Functions` repository (create, sync, list, valves in the table and in user settings, switch everything off, delete) | 6, 8, 10.1, 10.7 |
| `backend/open_webui/functions.py` | Pipe models for the model list (including manifolds) and running a pipe for a chat | 3.2, 5.9, 10.5, 11.1, 11.2 |
| `backend/open_webui/utils/plugin.py` | Loading function and tool code, deciding the type, reading the opening comment, correcting old import paths, the per-process cache, installing `requirements`, drop-down choices for valves | 4, 8.1, 8.2, 10.7 |
| `backend/open_webui/utils/filter.py` | Choosing, ordering and running filters at each hook | 4, 5.10, 10.5, 11.3 |
| `backend/open_webui/utils/actions.py` | Running an action button | 5.11, 10.5, 11.4 |
| `backend/open_webui/utils/valves.py` | Reading and writing stored valve values (how they are protected is security-sensitive and not described) | 6.1, 7.1, 10.7 |
| `backend/open_webui/events.py` | Event names and messages, publishing, and Event-function dispatch (`:1103-1171`) | 5.12, 8.3, 9.3, 10.7 |
| `backend/open_webui/routers/pipelines.py` | Pipelines filters called during chats, and the `/api/v1/pipelines` management routes | 2.4, 5.13-5.15, 10.4, 11.6, 11.17 |
| `backend/open_webui/env.py` | Environment switches for this area (`ENABLE_PLUGINS`, `SAFE_MODE`, package installation, time limits, certificate checking) and the default product name | 7.1, 12 |
| `backend/open_webui/config.py` | Stored settings used here (`chat.controls`, `chat.valves`, community sharing, model-list cache) | 3, 7.2, 8.1 |

### 13.2 Backend, Cited From Other Areas

| File | Why it is cited |
|---|---|
| `backend/open_webui/main.py` | Start-up order (safe mode, blocking package installation, start-up events), router mounts, `/api/chat/actions/{action_id}` and `/api/chat/completed`, the chat error path, `/health` and `/ready` |
| `backend/open_webui/constants.py` | The `[ERROR: …]` helper, storage texts and fixed error texts |
| `backend/open_webui/utils/models.py` | The model list: attaching actions and toggleable filters, priorities, model access checks |
| `backend/open_webui/utils/middleware.py` | The chat engine's filter call points, Pipelines filters and error events |
| `backend/open_webui/utils/chat.py` | Handing a chat to a pipe; the deprecated outlet route |
| `backend/open_webui/utils/access_control/__init__.py` | The model access check used when chatting with a pipe |
| `backend/open_webui/utils/auth.py` | The administrator check and its refusal text |
| `backend/open_webui/routers/openai.py` | Connection model lists (how a Pipelines server is detected) and the person's details sent to pipe pipelines |
| `backend/open_webui/routers/utils.py` | The code formatter used before every save |
| `backend/open_webui/routers/tools.py` | Workspace tools, also governed by `ENABLE_PLUGINS` |
| `backend/open_webui/socket/main.py` | The event emitter and event call that functions use to reach the browser |
| `backend/open_webui/models/users.py` | User settings (where a person's valves live) and the account record functions receive |
| `backend/open_webui/migrations/versions/7e5b5dc7342b_init.py`, `backend/open_webui/migrations/versions/018012973d35_add_indexes.py` | Creation of the `function` table and its `is_global` index |
| `backend/start.sh` | Number of worker processes |

### 13.3 Front End, in Scope

| File | What it holds | Sections |
|---|---|---|
| `src/lib/components/admin/Functions.svelte` | The Functions list: search, type and view filters, sorting, switches, valves, the `...` menu, Import JSON and Export JSON, the delete dialog, community links | 2.1, 5, 9.1, 10.2 |
| `src/lib/components/admin/Functions/FunctionEditor.svelte` | The editor: name, ID and description, the Filter and Event starters (and an unused older example), formatting and saving, the confirmation dialog | 5.1, 6.4, 10.2, 10.6 |
| `src/lib/components/admin/Functions/FunctionMenu.svelte` | The `...` menu: Global, Edit, Share, Clone, Export, Delete | 3.2, 5.5 |
| `src/lib/components/admin/Functions/AddFunctionMenu.svelte` | A **New Function** and **Import From Link** menu. No component imports it in this version (searched `src/` for `AddFunctionMenu`); the list uses a split create button instead (`src/lib/components/admin/Functions.svelte:361-388`) | — |
| `src/routes/(app)/admin/functions/+page.svelte` | List route; sends the person to `/admin` when plugins are off | 2.1, 11.8 |
| `src/routes/(app)/admin/functions/create/+page.svelte` | Create route: version check, create call, hand-off from the community site | 5.1, 10.2 |
| `src/routes/(app)/admin/functions/edit/+page.svelte` | Edit route: loads the function, version check, update call | 5.4, 10.2 |
| `src/routes/(app)/workspace/functions/create/+page.svelte` | Old address; forwards to the admin editor | 2.1 |
| `src/lib/components/admin/Settings/Pipelines.svelte` | The **Admin Settings > Pipelines** panel | 5.14, 10.4, 11.6, 11.17 |
| `src/lib/components/common/Valves.svelte` | The valves form used by every valves dialog and the Controls panel | 4, 5.6, 10.3 |
| `src/lib/components/common/Valves/MapSelector.svelte` | Map input for the `map` valve type, which `Valves.svelte` marks `EXPERIMENTAL INPUT TYPE, DO NOT USE IN PRODUCTION` (`src/lib/components/common/Valves.svelte:189`). It loads map tiles from OpenStreetMap's servers in the browser (`src/lib/components/common/Valves/MapSelector.svelte:31-34`); prompt variables use it too (`src/lib/components/chat/MessageInput/InputVariablesModal.svelte:11`) | 4 |
| `src/lib/apis/functions/index.ts` | Browser calls for every functions route; each passes the server's `detail` on | 10 |

### 13.4 Front End, Cited From Other Areas

| File | Why it is cited |
|---|---|
| `src/lib/apis/index.ts` | Pipelines calls, the action call and the model list |
| `src/lib/components/ImportModal.svelte` | The **Import From Link** dialog |
| `src/lib/components/workspace/common/ValvesModal.svelte` | The **Valves** dialog (admin and personal valves) |
| `src/lib/components/workspace/common/ManifestModal.svelte` | The **Show your support!** dialog |
| `src/lib/components/workspace/common/PluginTranslations.svelte` | The editor's translation view |
| `src/lib/components/chat/Controls/Controls.svelte`, `src/lib/components/chat/Controls/Valves.svelte` | The chat **Controls** panel and its **Valves** section |
| `src/lib/components/chat/MessageInput.svelte`, `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte` | Toggleable filter switches, pills and valves buttons in the composer |
| `src/lib/components/chat/Chat.svelte` | Action calls, function events in an open chat, chat error handling |
| `src/lib/components/chat/Messages/ResponseMessage.svelte` | Action buttons, status lines, Hide Processing Details |
| `src/lib/components/chat/Messages/Error.svelte` | The reply's grey error box |
| `src/lib/components/chat/Messages/ContentRenderer.svelte`, `src/lib/components/chat/Messages/Markdown/HTMLToken.svelte`, `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte` | Inline Citations and Hide Processing Details in answer text |
| `src/lib/components/chat/SettingsModal.svelte` | The Settings window that hosts the Pipelines panel |
| `src/lib/components/common/CodeEditor.svelte` | The code editor and formatting before saving |
| `src/lib/components/common/ConfirmDialog.svelte` | Confirmation dialogs, including the default title |
| `src/lib/components/common/LocalizedField.svelte` | Name and description fields with translations |
| `src/lib/components/common/InterfaceSettings.svelte` | The fork's two Interface settings |
| `src/lib/components/admin/Settings/Connections.svelte`, `src/lib/components/admin/Settings/Connections/OpenAIConnection.svelte` | The Pipelines icon on a connection |
| `src/lib/components/workspace/Models/ModelEditor.svelte`, `src/lib/components/workspace/Models/DefaultFiltersSelector.svelte` | Attaching filters, default filters and actions to a model |
| `src/routes/(app)/admin/+layout.svelte` | The administrator check and the **Functions** tab |
| `src/routes/(app)/admin/settings/[tab]/+page.svelte` | Opening an admin settings tab in the Settings window |
| `src/lib/utils/index.ts` | The version comparison behind the required-version check |
| `src/lib/i18n/locales/en-US/translation.json` | English text of the dotted keys and of the fork's settings |

## 14. Open Questions

Everything below could not be settled from the repository. Items marked TO BE CONFIRMED earlier in
this document are all repeated here.

### 14.1 Possible Contradictions and Refinements

- **No contradiction with `tools/ground-truth.md` was found.** Its valves line (stored in the
  database, protected only when `ENABLE_VALVE_ENCRYPTION` is on) matches `backend/open_webui/utils/valves.py:21-24`;
  this document refers the detail to security (14.4).
- **Refinement of `CLAUDE.md` (Startup Order, item 3).** It says start-up installs the requirements
  "declared by stored tools and functions". The code installs those of **switched-on** functions and
  of tools **owned by administrators** only (`backend/open_webui/utils/plugin.py:465-480`); switched-off
  functions get their packages when next loaded (section 8.1).
- **Corrections made in this document** (rule 21): section 5.3 (an import carries the whole
  metadata, including translations) and section 5.6 step 4 (when `Error fetching valves` appears).

### 14.2 Live Configuration (Data, Not in the Repository)

All **TO BE CONFIRMED** for production:

- The production host name (section 2).
- Whether production uses a Pipelines server at all; where it runs, what it is configured with, its
  installed pipelines and anything it runs on a schedule (sections 1, 7.3, 8.4, 11.6).
- Which functions are installed, which are switched on or global, which Event functions exist and
  what they send where (sections 6.4, 9.4).
- The live values of `ENABLE_PLUGINS`, `SAFE_MODE`, `ENABLE_PIP_INSTALL_FRONTMATTER_REQUIREMENTS`,
  `OFFLINE_MODE`, `PIP_OPTIONS`, `PIP_PACKAGE_INDEX_OPTIONS`, `ENABLE_API_OUTLET_FILTERS`,
  `AIOHTTP_CLIENT_TIMEOUT`, `AIOHTTP_CLIENT_SESSION_SSL`, `AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST`,
  `WEBSOCKET_EVENT_CALLER_TIMEOUT` and `WEBUI_NAME`, and of the stored settings `chat.controls`,
  `chat.valves`, `ui.enable_community_sharing` and `models.base_models_cache` (sections 7, 12).
- How many worker processes production runs, and whether it uses Redis (sections 8.1, 8.4).
- Whether production servers can reach a Python package index or the internet at all (sections
  11.5, 11.16).
- Whether a proxy with its own time limit sits in front of MedIT GPT (section 11.10).
- Whether any conversation-turn limit is intended (section 11.7).

### 14.3 Governance and Contacts

All **TO BE CONFIRMED**:

- Who the "platform administrator" is for escalations about functions and pipelines, and how to
  reach them (section 11).
- Whether tier 1 can open the admin Functions page, the Pipelines panel or the server logs
  (section 11).
- Whether administrators may share functions publicly through **Share** (`openwebui.com`), and
  whether staff should use the **Discover a function** link (sections 4, 5.8, 10.2).
- Who reviews installed functions for privacy. Pipes, filters and actions receive account details,
  Event functions and event webhooks receive the acting person's details, Pipelines servers receive
  personal data with every call, and the starter code prints chat content and user records to the
  server log (sections 6.4, 9.3).
- Whether some filters are mandatory, so that people must not be steered to models without them
  (section 11.3).

### 14.4 Security-Sensitive Questions (Referred Without Detail)

Functions run Python on the MedIT GPT server with the server's own access and are governed by
administrators only; this document does not describe their execution internals. For each item
below: Security-sensitive: refer to the platform maintainer and U of T Information Security
(security.utoronto.ca).

- How stored admin and personal valve values are protected at rest (`ENABLE_VALVE_ENCRYPTION`,
  sections 6.1, 7.1), and what the log line `Failed to decrypt valves: {type}` implies for a
  deployment (sections 10.7, 11.12).
- The `execute` event type that functions can send to the browser (section 9.2).
- Whether the server enforces the `chat.valves` permission on the routes for a person's own valves
  (section 3.3).
- Outbound requests the server makes on an administrator's behalf (**Import From Link**, every
  Pipelines call) and the controls around them (sections 2.2, 2.4).

### 14.5 Behaviour Read From Code but Not Observed

The application was not run for this research (research instructions), so these follow from
reading the code only:

- What a person sees when a pipe fails after its answer has started streaming (section 11.1, cause
  5): the pipe wrapper does not catch such errors (`backend/open_webui/functions.py:308-341`).
- The script error behind `Name and description are required`, from the missing pop-up import
  (section 10.2; `src/lib/components/admin/Functions/FunctionEditor.svelte:1-16`, `:331`). The same
  line exists upstream at v0.11.4, so it is not a fork defect.
- `[object Object]` pop-ups for requests the server rejects by format (section 10.2).
- **Import JSON** stopping without any message on a file that is not valid JSON or not a list
  (section 11.11).
- The on/off switch and the model-list refresh racing each other (section 11.9).
- Whether action buttons can appear on channel messages, which the action route refuses (section
  10.5, `Channel chats are not supported on this endpoint`).
- `Function not found: {function_id}` reaching a chat, which needs a stale model list (section
  10.5).
- Renamed valve settings falling back to defaults, which depends on Pydantic's default handling of
  undeclared names rather than on repository code (section 11.3, cause 3).
- The wording a Pipelines server returns for its errors (section 10.4).

### 14.6 Outside This Area or Not Researched in Depth

- The status lines, pop-ups and dialogs that installed functions send are written in their own
  code, which is stored in the database, not in this repository (section 9.2).
- The Pipelines server is a separate product; its behaviour, messages and logs are outside this
  repository (sections 5.15, 10.4).
- The full list of platform events and their payloads, and how event webhooks are configured, belong
  to `notifications-webhooks-events-and-banners.md`, which is planned in `reference/_areas.md` but
  does not exist yet (2026-10-09); the references to it in sections 1, 5.12, 9.3 and 9.4 point
  ahead.
- The chat engine around filters and pipes (`chat-completion-pipeline-and-generation-tasks.md`),
  model records and access (`workspace-models-and-model-access.md`), connections
  (`model-connections-openai-ollama-and-direct.md`) and workspace tools
  (`workspace-tools-tool-servers-mcp-and-terminals.md`) are documented there, not re-verified here.
- The map input for valves loads tiles from OpenStreetMap's servers in the person's browser
  (section 13.3); whether that is acceptable for MedIT GPT, should any function use it, is **TO BE
  CONFIRMED**.
