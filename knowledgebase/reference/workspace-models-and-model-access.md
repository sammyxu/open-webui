# Workspace Models, Model Settings and Model Access

## At a Glance

- **Two kinds of model.** A **base model** comes from a connection (an OpenAI-compatible provider,
  Ollama, or a pipe function) and is listed live from that provider
  (`backend/open_webui/utils/models.py:57-66`). A **workspace model** (also called a custom model
  or preset) is a saved record in the `model` table that points at a base model through
  `base_model_id` and adds a name, picture, system prompt, parameters, knowledge, tools and
  capabilities (`backend/open_webui/models/models.py:111-124`). A record with **no**
  `base_model_id` is an admin's settings layer on top of the base model with the same id: its
  name, access, capabilities and hidden flag apply to that base model
  (`backend/open_webui/utils/models.py:178-207`).
- **Where people work.** Users with the **Models Access** permission (`workspace.models`, off in
  code) use **Workspace › Models** (`/workspace/models`); admins also use **Settings › Admin ›
  Models** (deep link `/admin/settings/models`, which opens `/?settings=admin:models`)
  (`src/routes/(app)/workspace/+layout.svelte:80-83`;
  `src/routes/(app)/admin/settings/[tab]/+page.svelte:6-9`;
  `src/lib/components/chat/SettingsModal.svelte:286-291`). Everyone picks models in the chat
  **model selector** and can keep favourites in the sidebar.
- **Who sees a model.** A non-admin sees a model when they own its record or a **read** grant
  reaches them (public, direct or through a group). A base model with **no record** is offered to
  admins only, so making a provider model available to users means an admin must make it public
  or share it (`backend/open_webui/utils/models.py:524-578`). Full rules and the chat-time checks
  are in `users-groups-roles-and-permissions.md`, section 3.7; this document adds the model-list
  view (section 3.3).
- **Hidden is not private; disabled is off for everyone.** **Hide** takes a model out of the
  selector, the sidebar pins and new-chat defaults, but it stays usable through a link or an
  existing chat (`src/lib/components/chat/ModelSelector/Selector.svelte:310`;
  `src/lib/components/chat/Chat.svelte:2046-2048`, `:2068-2091`, `:2311-2319`). The **Enabled**
  switch off removes the model from every user's model list
  (`backend/open_webui/utils/models.py:184-210`).
- **Creating a workspace model** needs a name, a base model, and an id. The id is generated from
  the name (lower case, spaces to hyphens, other symbols removed), may not contain spaces, may be
  at most 256 characters and must be unused (`src/lib/components/workspace/Models/ModelEditor.svelte:84-91`,
  `:290-316`; `backend/open_webui/routers/models.py:101-102`, `:301-337`). The id cannot be
  changed afterwards (`src/lib/components/workspace/Models/ModelEditor.svelte:834-840`).
- **Defaults and pins.** Admins choose the **Selected** model(s) for new chats
  (`ui.default_models`), the **Pinned** models shown in every sidebar (`ui.default_pinned_models`),
  the list **order** (`ui.model_order_list`), and **Model Defaults** (default capabilities,
  parameters and prompt suggestions) (`backend/open_webui/routers/configs.py:62-68`). A user who
  has once pressed **Set as default** or pinned or unpinned a model keeps their own choice and no
  longer follows the admin default (`src/lib/stores/index.ts:107-112`;
  `src/lib/components/chat/Chat.svelte:2102-2107`).
- **Deleting a model is permanent.** The record and all its access grants are removed
  (`backend/open_webui/models/models.py:575-584`). Chats keep the old model id; reopening one
  switches the selection to another available model, and old replies show the raw id
  (`src/lib/components/chat/Chat.svelte:2311-2331`;
  `src/lib/components/chat/Messages/ResponseMessage.svelte:194-195`).
- **A workspace model whose base model has gone** stays listed but every message to it fails with
  `Model not found`, admins included, unless the environment switch
  `ENABLE_CUSTOM_MODEL_FALLBACK` (off in code) sends it to the first default model
  (`backend/open_webui/main.py:1128-1147`, `:1179-1185`; `backend/open_webui/env.py:1033`).
- **Import and export** are JSON files, gated by **Import Models** and **Export Models**
  (`workspace.models_import`, `workspace.models_export`, both off in code). The server skips any
  entry it will not accept without reporting it (`backend/open_webui/routers/models.py:441-673`).
- **Settings › Admin › Models › Actions › Reset** deletes every model record, custom models
  included, with no undo (`src/lib/components/admin/Settings/Models.svelte:709-720`;
  `backend/open_webui/models/models.py:586-598`).
- **Fork status:** this area matches upstream Open WebUI v0.11.4. The fork's personal settings
  **Hide Processing Details** and **Inline Citations** combine with a model's **Status Updates**
  and **Citations** capabilities (section 12).
- Tier 1 is read-only: diagnose and escalate; never create, edit, share, hide, disable or delete
  a model, and never change model settings.

## 1. Purpose and Who Uses It

This area decides **which AI models a person can pick in MedIT GPT, what each one is called and
how it behaves**. It covers three things:

1. **Workspace models.** A saved "assistant" built on top of a provider model: for example a
   fictional "Demo Course Helper" that uses a provider model, carries its own instructions (system
   prompt), a knowledge base, some tools and a picture. Anyone with the Models Access permission can
   build one; the owner decides who else may use or edit it.
2. **Admin model management.** Admins switch provider models on or off, rename them, set who may
   use them, hide them, put them in order, choose the default model for new chats and the models
   pinned in everyone's sidebar, and set defaults that every model inherits.
3. **Choosing a model.** Every signed-in person uses the model selector in the message composer at
   the bottom right of a chat (`src/lib/components/chat/MessageInput.svelte:2576-2583`; and the
   sidebar pins) to pick from the models they are allowed to see. *Corrected 2026-10-08: an earlier
   version said "at the top of a chat".*

| Who | What they do here | Evidence |
|---|---|---|
| Any signed-in `user` or `admin` | Opens the model selector, searches and filters it, picks one or several models, sets a personal default, pins models to the sidebar, copies a model link | `src/lib/components/chat/ModelSelector.svelte:26-46`, `:83-84`; `src/lib/components/chat/ModelSelector/ModelItemMenu.svelte:105-145` |
| A `user` with **Models Access** (`workspace.models`) | Creates workspace models, edits the ones they own or may write, shares them within their sharing permissions | `src/routes/(app)/workspace/+layout.svelte:80-83`; `backend/open_webui/routers/models.py:293-299` |
| A `user` with **Import Models** or **Export Models** | Imports or exports workspace models as JSON | `src/lib/components/workspace/Models.svelte:107-120`; `backend/open_webui/routers/models.py:388-397`, `:448-457` |
| A `user` with a **Write** grant on someone else's model | Edits, hides, enables or disables, clones, exports (with the export permission) and **deletes** that model | `backend/open_webui/routers/models.py:887-897`, `:947-961`, `:1125-1139` |
| An `admin` | Everything above for every model (while `BYPASS_ADMIN_ACCESS_CONTROL` is on), plus **Settings › Admin › Models**: base-model settings, defaults, pins, order, import, export, reset, and model downloads on Ollama, llama.cpp or LM Studio servers | `src/lib/components/admin/Settings/Models.svelte:724-1301`; `src/lib/components/admin/Settings/Models/ManageModelsModal.svelte:34-80` |
| A `pending` user | Nothing: pending accounts cannot use the application until approved (`users-groups-roles-and-permissions.md`) | `src/routes/(app)/+layout.svelte:445-446` |
| Tier 1 support | Reads what the person sees, collects identifiers and escalates; makes no change | (house rule) |

Neighbouring documents: connections and how the provider list is fetched and cached
(`model-connections-openai-ollama-and-direct.md`); groups, grants and permission keys
(`users-groups-roles-and-permissions.md`); knowledge bases (`knowledge-bases.md`); tools and tool
servers (`workspace-tools-tool-servers-mcp-and-terminals.md`); filters, actions and pipe models
(`functions-pipes-filters-actions-and-pipelines.md`); skills (`prompts-and-skills.md`); arena
models (`evaluations-feedback-and-analytics.md`); every admin tab (`admin-settings-panels.md`);
what happens when a message is sent (`chat-completion-pipeline-and-generation-tasks.md`).

## 2. Navigation and URLs

All addresses are relative to the site root; the production host name is **TO BE CONFIRMED**.

### 2.1 Pages and Panels

| Place | Address | Who | What it shows | Source |
|---|---|---|---|---|
| Workspace › **Models** | `/workspace/models` (the bare `/workspace` opens it for admins and for users with Models Access) | `admin`; `user` with `workspace.models` (others are sent to `/`) | The workspace models the person can read, 30 per page, with search, a view filter, a tag filter and an **Actions** menu | `src/routes/(app)/workspace/+page.svelte:6-22`; `src/routes/(app)/workspace/+layout.svelte:80-83`; `src/routes/(app)/workspace/models/+page.svelte:7-23`; `src/lib/components/workspace/Models.svelte:522-951` |
| Create a model | `/workspace/models/create` | As above | Empty model editor, or a pre-filled one after **Clone** | `src/routes/(app)/workspace/models/create/+page.svelte:74-117` |
| Edit a model | `/workspace/models/edit?id=<model id>` | Owner, write-grant holder, admin | Model editor in edit mode; without write access the page shows `You do not have permission to edit this model` and returns to the list | `src/routes/(app)/workspace/models/edit/+page.svelte:18-37` |
| Settings › Admin › **Models** | `/admin/settings/models`, which forwards to `/?settings=admin:models`; listed in the **AI** group of the Settings window | `admin` only (other roles are moved to the General tab) | Every base and workspace model, **Model Defaults**, search, view and tag filters, **Actions**, drag-to-order and **Save** | `src/routes/(app)/admin/settings/[tab]/+page.svelte:6-9`; `src/lib/components/chat/SettingsModal.svelte:161`, `:286-291`, `:407-408`, `:486-488`, `:863-864`; `src/lib/components/admin/Settings/Models.svelte:724-1280` |
| Base-model editor | Inside Settings › Admin › Models, by clicking a base model (or **Edit** in the chat selector's menu for a base model) | `admin` | The same editor without the base-model picker, with **Read**-only sharing | `src/lib/components/admin/Settings/Models.svelte:627-635`, `:1282-1300`; `src/lib/components/chat/ModelSelector/ModelItemMenu.svelte:50-69` |
| **Manage Models** dialog | Settings › Admin › Models › **Actions** › **Manage** | `admin` | Pull, update, create, upload and delete models on Ollama servers; download, load, unload and delete on llama.cpp or LM Studio connections | `src/lib/components/admin/Settings/Models.svelte:877-888`; `src/lib/components/admin/Settings/Models/ManageModelsModal.svelte:83-137` |
| Chat **model selector** | In the message composer, bottom right, of every chat (corrected 2026-10-08 from "Top of every chat") | Every signed-in user | The models in the person's model list, minus hidden ones; search, connection and tag filters, **Compare**, **Set as default** | `src/lib/components/chat/ModelSelector.svelte:63-92`; `src/lib/components/chat/ModelSelector/Selector.svelte:906-1286` |
| Sidebar pinned models | Left sidebar, above chats | Every signed-in user | The person's pinned models they can still see; each opens a new chat with that model | `src/lib/components/layout/Sidebar/PinnedModelList.svelte:62-83`; `src/lib/components/layout/Sidebar/PinnedModelItem.svelte:21-78` |

**Deep links.** **Copy Link** (workspace list, admin list and chat selector) copies
`/?model=<model id>`; opening it starts a new chat with that model, or opens the selector with the
id typed into the search box when the person cannot see that model. `/?models=<id>,<id>` starts a
side-by-side chat (`src/lib/components/workspace/Models.svelte:275-284`;
`src/lib/components/chat/Chat.svelte:2068-2091`). The full list of chat URL parameters is in
`chat-composer-and-message-display.md`.

### 2.2 Models API (`/api/v1/models`)

The router is mounted at `/api/v1/models` (`backend/open_webui/main.py:865`). Model ids are passed
as a query parameter (`?id=`) so that ids containing `/` work (`backend/open_webui/routers/models.py:720`).

| Method and path | Who | Purpose | Source |
|---|---|---|---|
| `GET /list` | Signed in | Workspace list: models with a base model that the caller can read; filters `query`, `view_option` (`created`, `shared`), `tag`, `order_by` (`name`, `created_at`, `updated_at`), `direction`, `page` (30 per page); each item says whether the caller has `write_access`, and read-only items come back without their parameters | `backend/open_webui/routers/models.py:159-237` |
| `GET /all` | Admin | Every model record, base overrides included | `:245-247` |
| `GET /base`, `GET /base/tags` | Admin | Records without a base model (base overrides) and their tags | `:250-262` |
| `GET /tags` | Signed in | Tags used on workspace models the caller can read | `:270-277` |
| `POST /create` | Admin, or `user` with `workspace.models` | Create a workspace model | `:285-369` |
| `GET /export` | Admin, or `user` with `workspace.models_export` | Export the workspace models the caller may write (all of them for an admin under the bypass), optionally limited by `ids`; background images are embedded | `:381-429` |
| `POST /import` | Admin, or `user` with `workspace.models_import` | Create or update models from an exported list | `:441-673` |
| `POST /sync` | Admin | API only (no screen uses it): replaces the whole model table with the list sent; records missing from the list are deleted with their grants | `:685-708`; `backend/open_webui/models/models.py:600-649` |
| `GET /model?id=` | Owner, grant holder, admin | One model, with `write_access`; parameters stripped for read-only callers | `backend/open_webui/routers/models.py:721-767` |
| `GET /model/profile/image?id=` | Signed in | The model's picture; callers without read access get the default picture rather than an error | `:775-873` |
| `POST /model/toggle?id=` | Admin, owner, write grant | Flip **Enabled** / **Disabled** | `:881-924` |
| `POST /model/update` | Admin, owner, write grant | Save the editor | `:932-1021` |
| `POST /model/access/update` | Admin, owner, write grant | Replace a model's grants; for an admin it first creates a minimal record for a base model that has none | `:1035-1103` |
| `POST /model/delete` | Admin, owner, write grant | Delete one model | `:1111-1150` |
| `DELETE /delete/all` | Admin | Delete every model record (the admin **Reset** action) | `:1153-1160` |

### 2.3 Related Endpoints Outside This Router

| Method and path | Who | Purpose | Source |
|---|---|---|---|
| `GET /api/models` (also `/api/v1/models`) | Signed in | The caller's **model list**: every provider model, arena model and active workspace model, filtered for access, tags merged, sorted by `ui.model_order_list` | `backend/open_webui/main.py:897-943` |
| `GET /api/models/base` | Admin | The raw provider list, before workspace models and access filtering | `backend/open_webui/main.py:946-949` |
| `POST /api/models/unload` | Admin | Unload a running model on Ollama or llama.cpp (the selector's **Eject** button) | `backend/open_webui/main.py:956-1064` |
| `GET` / `POST /api/v1/configs/models` | Admin | Read or save `ui.default_models`, `ui.default_pinned_models`, `ui.model_order_list`, `models.default_metadata`, `models.default_params` | `backend/open_webui/routers/configs.py:62-68`, `:734-772` |
| `GET /api/v1/configs/models/defaults` | Signed in | The default capabilities, features and built-in tools (`models.default_metadata`) that the editor starts from | `backend/open_webui/routers/configs.py:742-746` |
| `POST /api/v1/configs/suggestions` | Admin | Default prompt suggestions (`ui.prompt_suggestions`, `ui.prompt_suggestions_i18n`) | `backend/open_webui/routers/configs.py:807-840` |

The Ollama and provider endpoints that the Manage Models dialog and the selector's download
options call are documented in `model-connections-openai-ollama-and-direct.md`.

## 3. Roles and Permissions

Roles, groups, grants and the evaluation of permission keys are documented in
`users-groups-roles-and-permissions.md` (sections 3, 5.16, 5.17 and 7.5); model access control in
chat is its section 3.7. This section covers what is specific to models.

### 3.1 Who Can Do What With a Model

"Admin" below means an admin while `BYPASS_ADMIN_ACCESS_CONTROL` is on (the code default). With it
off, admins see and use models like other users, except where noted in section 3.4.

| Action | Admin | Owner | Write grant | Read grant | Others | Source |
|---|---|---|---|---|---|---|
| See a workspace model in Workspace › Models | All | Yes | Yes | Yes, marked `Read Only` | No | `backend/open_webui/routers/models.py:198-204`; `src/lib/components/workspace/Models.svelte:772-774` |
| Open it in the editor | Yes | Yes | Yes | No (the row is not clickable; the edit page refuses) | No | `src/lib/components/workspace/Models.svelte:144-148`; `src/routes/(app)/workspace/models/edit/+page.svelte:30-33` |
| Create a workspace model | Yes | | | | `user` with `workspace.models` | `backend/open_webui/routers/models.py:293-299` |
| Save changes, hide or show | Yes | Yes | Yes | No | No | `backend/open_webui/routers/models.py:947-961` |
| Enable or disable (switch) | Yes | Yes | Yes | No | No | `backend/open_webui/routers/models.py:887-919` |
| Change who has access | Yes | Yes | Yes, within their own sharing permissions | No | No | `backend/open_webui/routers/models.py:988-1010`, `:1068-1090` |
| Delete | Yes | Yes | **Yes** | No | No | `backend/open_webui/routers/models.py:1125-1139` |
| Clone (menu item) | Yes | Yes | Yes | No | No; saving the clone also needs `workspace.models` | `src/lib/components/workspace/Models/ModelMenu.svelte:149-158` |
| Export one model | Yes | With `workspace.models_export` | With `workspace.models_export` | No | No | `src/lib/components/workspace/Models/ModelMenu.svelte:173-182`; `backend/open_webui/routers/models.py:388-406` |
| Copy link, pin to sidebar | Anyone who can see it | | | | | `src/lib/components/workspace/Models/ModelMenu.svelte:130-171` |
| Chat with it | See `users-groups-roles-and-permissions.md` section 3.7 (read access to the model and to every model in its base-model chain) | | | | | `backend/open_webui/utils/models.py:465-521` |
| Base-model settings, defaults, pins for everyone, order, reset, engine downloads | Admin only | | | | | `backend/open_webui/routers/models.py:245-262`, `:685-708`, `:1153-1160`; `backend/open_webui/routers/configs.py:749-772` |

Rules that apply to non-admins only:

- A new workspace model **must** have a base model, and its id may not be the id of a provider
  model (or, for Ollama, the model name without its `:tag`). Both refusals come back as errors
  (section 10.1) (`backend/open_webui/routers/models.py:317-337`).
- The base model of an existing workspace model cannot be cleared
  (`backend/open_webui/routers/models.py:975-979`).
- Knowledge items of type **file** must be files the person can read; otherwise the save is
  refused with `ACCESS_PROHIBITED` (`backend/open_webui/routers/models.py:126-149`, `:339-343`,
  `:963-967`).
- Sharing choices the person may not make are silently dropped on save (section 5.10).

The **base model picker** in the editor offers provider models only: no other workspace model
(except the current base on edit), no arena models, no models from a person's own direct
connections, and, for non-admins, no hidden models
(`src/lib/components/workspace/Models/ModelEditor.svelte:227-248`).

### 3.2 Permission Keys That Shape This Area

Labels, defaults and environment variables for every key are in
`users-groups-roles-and-permissions.md`, section 7.5. All the keys below are **off** in code except
the last three.

| Key | Effect here | Source |
|---|---|---|
| `workspace.models` (**Models Access**) | Workspace › Models section and creating models; any Workspace "Access" key makes the Workspace link appear | `src/routes/(app)/workspace/+layout.svelte:80-83`; `backend/open_webui/routers/models.py:293-299` |
| `workspace.models_import` (**Import Models**) | **Import JSON** action and the import endpoint | `src/lib/components/workspace/Models.svelte:107-112`; `backend/open_webui/routers/models.py:448-457` |
| `workspace.models_export` (**Export Models**) | **Export JSON** action, the row menu's **Export**, and the export endpoint | `src/lib/components/workspace/Models.svelte:113-120`; `src/lib/components/workspace/Models/ModelMenu.svelte:173`; `backend/open_webui/routers/models.py:388-397` |
| `sharing.models` (**Models Sharing**) | The access list (people and groups) in the model's **Access** dialog | `src/lib/components/workspace/Models/ModelEditor.svelte:604` |
| `sharing.public_models` (**Models Public Sharing**) | **Public** visibility for a model; enforced on save | `src/lib/components/workspace/Models/ModelEditor.svelte:605`; `backend/open_webui/routers/models.py:347-353` |
| `access_grants.allow_users`, `access_grants.allow_groups` (on) | Whether people and groups can be added to the access list | `src/lib/components/workspace/Models/ModelEditor.svelte:606-608` |
| `chat.multiple_models` (on) | The selector's **Compare** button (several models side by side) | `src/lib/components/chat/ModelSelector.svelte:83-84`; `src/lib/components/chat/ModelSelector/Selector.svelte:1000-1020` |
| `chat.file_upload` (on) | The **Upload** link in the editor's Knowledge section | `src/lib/components/workspace/Models/Knowledge.svelte:38-42`, `:208-219` |

### 3.3 Which Models Appear in a Person's Model List

The chat selector, the sidebar pins and the base-model picker all start from the person's model
list, built on each request to `GET /api/models`:

1. **Provider models** are gathered from the OpenAI-compatible connections (when `openai.enable`
   is on), Ollama (when `ollama.enable` is on) and active pipe functions
   (`backend/open_webui/utils/models.py:57-66`). How these lists are fetched and cached is in
   `model-connections-openai-ollama-and-direct.md`.
2. **Arena models** are added while `evaluation.arena.enable` is on: those configured in
   `evaluation.arena.models`, or the built-in **Arena Model** when none are configured
   (`backend/open_webui/utils/models.py:115-149`; `backend/open_webui/config.py:2067-2078`).
3. **Model records** are applied (`backend/open_webui/utils/models.py:167-264`):
   - a record with no base model renames and configures the provider model with the same id (a
     record whose id is an Ollama model name without its `:tag` applies to the first Ollama model
     of that name); if its **Enabled** switch is off, that provider model is removed from the
     list;
   - an active workspace model is added, borrowing the provider type and connection of its base
     model; it is added even when the base model is missing; a workspace model whose id equals a
     provider model's id is skipped;
   - an inactive (disabled) workspace model is left out.
4. Filter pipelines are dropped and duplicate ids collapse to one (`backend/open_webui/main.py:902-909`).
5. **Access filter** (`backend/open_webui/main.py:913`; `backend/open_webui/utils/models.py:524-578`).
   Nobody is filtered while `BYPASS_MODEL_ACCESS_CONTROL` is on, and admins are not filtered while
   `BYPASS_ADMIN_ACCESS_CONTROL` is on. Otherwise:
   - an arena model is kept when its own access list grants the person **read**;
   - a model with a record is kept when the person owns the record or a **read** grant reaches
     them (public, their user, or one of their groups);
   - a provider model with **no record** is kept for admins only.
6. Tags from the model and from its connection are merged, and the list is sorted by
   `ui.model_order_list` (section 5.14) (`backend/open_webui/main.py:915-937`).
7. In the browser, models from the person's own direct connections are added (when the admin has
   enabled direct connections), marked **Direct** (`src/lib/apis/index.ts:62-170`).
8. The selector leaves out **hidden** models; the sidebar pins leave out hidden models and models
   no longer in the list (`src/lib/components/chat/ModelSelector/Selector.svelte:310`;
   `src/lib/stores/index.ts:114-119`).

Consequences support should know:

- **A provider model is invisible to users until an admin gives it a record with a grant.**
  Switching it on in Settings › Admin › Models creates a record with no grants, which keeps it
  admin-only; **Make Public** or the **Access** dialog in the base-model editor is what opens it
  to users (`src/lib/components/admin/Settings/Models.svelte:514-538`, `:569-604`).
  *Precision (2026-10-08):* a provider model with no record already shows as enabled
  (`src/lib/components/admin/Settings/Models.svelte:304-311`); the **first** toggle switches it off
  and creates a disabled record with no access entries (`:514-525`), and switching it on again leaves
  it without them (section 5.11). The conclusion is unchanged: it stays admin-only until a read entry
  exists.
- **Arena models** need an access list in Settings › Admin › Evaluations; the built-in **Arena
  Model** has none, so only admins see it (`backend/open_webui/utils/access_control/__init__.py:111-148`;
  `evaluations-feedback-and-analytics.md`).
- The model list does **not** check the base-model chain, so a shared workspace model can appear
  while chatting with it is refused (`users-groups-roles-and-permissions.md`, section 3.7).

### 3.4 Admin Bypass Switches

Both switches are environment variables; live values are **TO BE CONFIRMED**. Details and every
call site are in `users-groups-roles-and-permissions.md`, section 3.7.

| Switch | Code default | Effect in this area | Source |
|---|---|---|---|
| `BYPASS_ADMIN_ACCESS_CONTROL` | on | Admins see every workspace model in Workspace › Models with write access, see every model in their model list, export all models and get every tag | `backend/open_webui/routers/models.py:198-204`, `:223-227`, `:274`, `:399-402`; `backend/open_webui/utils/models.py:526-528` |
| `BYPASS_MODEL_ACCESS_CONTROL` | off | When on, every signed-in user's model list contains every model, and chat-time model checks are skipped | `backend/open_webui/env.py:832`; `backend/open_webui/utils/models.py:524-528`; `backend/open_webui/main.py:1150` |

Admins keep the right to save, toggle, re-share and delete any model whatever the bypass switch
says, because those endpoints test the `admin` role directly
(`backend/open_webui/routers/models.py:887-889`, `:947-957`, `:1068-1078`, `:1125-1127`).

### 3.5 What a Read-Only User Can See of a Model

- Parameters, including the **system prompt**, are removed from every model in the model list
  (`backend/open_webui/utils/models.py:202-203`, `:247-248`) and from `GET /list` and
  `GET /model` for anyone without write access (`backend/open_webui/routers/models.py:228-231`,
  `:746-753`).
- The rest of the model's metadata is visible to anyone who can read the model: description,
  tags, capabilities, prompt suggestions, and the names and ids of attached knowledge, tools,
  skills, filters and actions (`backend/open_webui/utils/models.py:184-203`, `:241-251`).
- Files attached **directly** to a model (as knowledge) and its background image can be read by
  anyone who can read the model (`backend/open_webui/utils/access_control/files.py:85-100`).
  Attaching a personal file to a public model therefore makes it readable by all users.

### 3.6 What Sharing a Model Shares and What It Does Not

Sharing a workspace model gives people the model itself. The items attached to it are checked
separately, against the person who is chatting, every time the model is used:

| Attached item | What a person with read access to the model gets | Source |
|---|---|---|
| The base model | Nothing extra: they also need read access to the base model (and to every model in the chain), otherwise the shared model is listed but refused with `Model not found` | `users-groups-roles-and-permissions.md`, sections 3.7 and 5.17 (point 7); `backend/open_webui/utils/models.py:517-521` |
| A **knowledge base** (collection) | Searched only if the person can read that knowledge base (owner, read grant or admin). Sharing the model does not share the knowledge base | Legacy function calling: `backend/open_webui/retrieval/utils.py:1566-1580`; native function calling (the default): `backend/open_webui/tools/builtin.py:2199-2237` |
| A **file** attached directly (Upload in the editor's Knowledge section) | Readable through the model, without sharing the file separately | `backend/open_webui/utils/access_control/files.py:85-102`; `backend/open_webui/tools/builtin.py:105-123` |
| **Tools** | Pre-selected in a new chat only when the person can see the tool; the server also skips any tool the person cannot read and logs `Access denied to tool {tool_id} for user {user.id}` | `src/lib/components/chat/Chat.svelte:1029-1036`; `backend/open_webui/utils/tools.py:283-299` |
| **Skills** | Pre-selected only when the skill is active and visible to the person | `src/lib/components/chat/Chat.svelte:1063-1070` |
| **Default filters** | Switched on only for toggleable filters that are active on the server | `src/lib/components/chat/Chat.svelte:1076-1080`; `backend/open_webui/utils/models.py:393-441` |
| **Default features** (web search, image generation, code interpreter) | Switched on only when the model has the matching capability, the admin has the feature on, and the person has the matching `features.*` permission | `src/lib/components/chat/Chat.svelte:1083-1106` |
| **Terminal** | Selected only when that terminal server is available to the person | `src/lib/components/chat/Chat.svelte:1109-1115` |

These defaults are applied only when exactly one model is selected
(`src/lib/components/chat/Chat.svelte:1022-1024`). Everyone who can read a model also sees its
owner: Workspace › Models shows the owner's name and, on hover, their email, and its search box
matches owner names, emails and usernames (`src/lib/components/workspace/Models.svelte:798-812`;
`backend/open_webui/models/models.py:360-370`).

### 3.7 Permissions That Affect Personal Model Choices

| Personal choice | Permission involved | What happens without it | Source |
|---|---|---|---|
| **Set as default** in the model selector (personal default model for new chats) | `settings.interface` (**Interface Settings Access**, on in code) | The pop-up `Default model updated` still appears and the choice applies until the page is reloaded, but the server discards it, because the personal default (`models`) is one of the Interface fields it drops for people without this permission | `src/lib/components/chat/ModelSelector.svelte:26-36`; `backend/open_webui/routers/users.py:489-498`; `backend/open_webui/models/users.py:67-70`, `:129` |
| **Keep in Sidebar** / **Hide from Sidebar** (personal pins) | None | Pins (`pinnedModels`) are not an Interface field, so they are saved for everyone | `src/lib/components/chat/ModelSelector.svelte:38-46`; `backend/open_webui/models/users.py:67-135` |
| Several models side by side (**Compare**) | `chat.multiple_models` (on in code) | No **Compare** button; a chat that was started with several models reopens with only its first model | `src/lib/components/chat/ModelSelector.svelte:83-84`; `src/lib/components/chat/Chat.svelte:2323-2325` |
| A model's default features | `features.web_search`, `features.image_generation`, `features.code_interpreter` | The model's default feature stays off for that person | `src/lib/components/chat/Chat.svelte:1083-1106` |

The meaning and defaults of each key are in `users-groups-roles-and-permissions.md`, section 7.5.

## 4. Key Concepts and Terminology

| Term | Meaning in MedIT GPT | Source |
|---|---|---|
| **Base model** (provider model) | A model offered live by a connection: an OpenAI-compatible provider, an Ollama server or a pipe function. It exists only while the provider lists it; MedIT GPT does not store it | `backend/open_webui/utils/models.py:57-66` |
| **Workspace model** (custom model, preset) | A saved record that points at a base model (`base_model_id`) and adds its own name, picture, system prompt, parameters, knowledge, tools and capabilities. In the model list it is flagged `preset`; the admin list's view filter calls these **Workspace Models** | `backend/open_webui/models/models.py:111-124`; `backend/open_webui/utils/models.py:210-267`; `src/lib/components/admin/Settings/Models/AdminViewSelector.svelte:18` |
| **Base-model settings record** | A record with the same id as a base model and **no** `base_model_id`. It renames the base model and carries its access list, capabilities, hidden flag and Enabled switch. Admins create it from Settings › Admin › Models; the record is ignored while the provider does not list that model | `backend/open_webui/utils/models.py:178-208`; `src/lib/components/admin/Settings/Models.svelte:481-538` |
| **Model record** | Any row of the `model` table: a workspace model or a base-model settings record (section 6.1) | `backend/open_webui/models/models.py:111-124` |
| **Model ID** | The unique key of a model. It appears in links (`/?model=<id>`), is stored in every chat and reply that used the model, and cannot be changed after creation | `backend/open_webui/models/models.py:116`; `src/lib/components/workspace/Models/ModelEditor.svelte:834-840` |
| **Prefix ID** | A connection option that puts `<prefix>.` in front of every model id from that connection; the prefix is removed again before the provider is called. Set on the connection (`model-connections-openai-ollama-and-direct.md`) | `backend/open_webui/utils/model_ids.py:1-4`; `backend/open_webui/routers/openai.py:1556-1557` |
| **Name** (display name) | What people see in the selector and lists. A model may also carry translated names, descriptions and prompt suggestions per language (`meta.i18n`) | `src/lib/utils/localizedContent.ts:120-129`; `src/lib/components/workspace/Models/ModelEditor.svelte:137-171` |
| **Model list** | The list of models one person may use, rebuilt by the server on each request to `GET /api/models` (section 3.3) | `backend/open_webui/main.py:897-943` |
| **Model selector** | The model menu in the message composer, at the bottom right of the chat input (shortcut Cmd+Shift+M). It lists the person's model list minus hidden models | `src/lib/components/chat/MessageInput.svelte:2577-2585`; `src/lib/shortcuts.ts:89`; `src/lib/components/chat/ModelSelector/Selector.svelte:310` |
| **Base model picker** | **Base Model (From)** in the workspace model editor; it offers provider models only (section 3.1) | `src/lib/components/workspace/Models/ModelEditor.svelte:227-248`, `:853-870` |
| **Hidden** | `meta.hidden`. The model is left out of the selector, the sidebar pins and new-chat defaults, but stays usable through a link or an existing chat. It is a convenience, not an access control | `src/lib/components/workspace/Models.svelte:243-273`; `src/lib/stores/index.ts:116-120`; `src/lib/components/chat/Chat.svelte:2046-2048` |
| **Enabled / Disabled** | `is_active`. A disabled model is removed from every person's model list, admins included | `backend/open_webui/models/models.py:122`; `backend/open_webui/utils/models.py:184-210` |
| **Public / Shared / Private** | The admin list's label for a model's access list: **Public** when everyone may read it, **Shared** when it names people or groups, **Private** otherwise | `src/lib/components/admin/Settings/Models.svelte:114-137` |
| **Read / Write** grant | Read lets a person use and see the model; Write also lets them edit, hide, switch, re-share and delete it (section 3.1). Grants are rows of the `access_grant` table | `users-groups-roles-and-permissions.md`, section 6.3 |
| **Owner** | The account that created the record (`user_id`). For base-model settings records this is the admin who first configured the base model | `backend/open_webui/models/models.py:117`, `:205-220` |
| **Selected models** | The admin's default model(s) for new chats (`ui.default_models`); shown as **Selected** in the admin list | `src/lib/components/admin/Settings/Models.svelte:1054-1060`; `src/lib/components/chat/Chat.svelte:2050` |
| **Pinned models** | Models shown at the top of the sidebar. The admin's list (`ui.default_pinned_models`, shown as **Pinned**) applies to everyone who has never pinned or unpinned a model; after that the person's own list (`pinnedModels`) applies | `src/lib/stores/index.ts:108-113`; `src/lib/components/admin/Settings/Models.svelte:1062-1068` |
| **Personal default model** | The model(s) a person saved with **Set as default** in the selector. It takes precedence over the admin's Selected models (section 5.22) | `src/lib/components/chat/ModelSelector.svelte:26-36`; `src/lib/components/chat/Chat.svelte:2102-2108` |
| **Model order** | The admin's ordering of the model list (`ui.model_order_list`); models not in it follow, sorted by name | `backend/open_webui/main.py:928-937` |
| **Model Defaults** | Admin defaults applied to every model: default capabilities, default features and built-in tools (`models.default_metadata`), default parameters (`models.default_params`) and default prompt suggestions (`ui.prompt_suggestions`) | `src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:105-150` |
| **Capabilities** | Ticks that say what a model can do (vision, file upload, web search and so on); they decide which controls appear in the chat and what the server adds (section 5.4) | `src/lib/components/workspace/Models/Capabilities.svelte:12-61` |
| **Default features** | Web search, image generation or code interpreter switched on automatically when a new chat starts with the model | `src/lib/components/workspace/Models/DefaultFeatures.svelte:12-25`; `src/lib/components/chat/Chat.svelte:1083-1106` |
| **Built-in tools** | Tool groups the server can give a model in native function-calling mode (time, memory, chats, notes, knowledge, web search and others); each group is on unless unticked | `src/lib/components/workspace/Models/BuiltinTools.svelte:11-90`; `backend/open_webui/utils/tools.py:520-540` |
| **Knowledge** | Knowledge bases (shown as **Collections**), individual files and notes attached to a model so it can draw on them | `src/lib/components/workspace/Models/Knowledge/KnowledgeSelector.svelte:48-101` |
| **Tools / Skills** | Workspace tools (and tool-server tools) and skills pre-selected when the model is chosen | `src/lib/components/workspace/Models/ToolsSelector.svelte:30-100`; `src/lib/components/workspace/Models/SkillsSelector.svelte:30-100` |
| **Filters / Default Filters** | Filter functions that process messages for this model. A global filter applies to every model and cannot be unticked; a toggleable filter can be switched on by default with **Default Filters** | `src/lib/components/workspace/Models/FiltersSelector.svelte:22-25`; `src/lib/components/workspace/Models/ModelEditor.svelte:1217-1231` |
| **Actions** | Action functions that add buttons under the model's replies; global actions apply to every model | `src/lib/components/workspace/Models/ActionsSelector.svelte:22-25`; `backend/open_webui/utils/models.py:385-419` |
| **Prompt suggestions** | The example prompts shown on a new chat. **Default** uses the admin's suggestions; **Custom** uses the model's own list | `src/lib/components/workspace/Models/ModelEditor.svelte:1155-1192`; `src/lib/components/chat/Placeholder.svelte:98-106` |
| **Chat variables / User variables** | Placeholders in a model's system prompt: `{{chat.variables.<key>}}` values are asked for in each chat, `{{user.variables.<key>}}` values come from each person's settings. The pipeline document describes how they are filled | `src/lib/components/workspace/Models/ModelEditor.svelte:173-225`; `chat-completion-pipeline-and-generation-tasks.md` |
| **Background image** | An image shown behind the chat when the model is selected | `src/lib/components/workspace/Models/ModelEditor.svelte:872-956`; `src/lib/components/chat/Chat.svelte:180-188` |
| **Profile image** | The model's picture, served to anyone who can read the model; others get the default picture | `backend/open_webui/routers/models.py:775-873` |
| **Arena model** | A blind-comparison model that answers with a randomly chosen other model; configured under Evaluations | `backend/open_webui/utils/models.py:115-149`; `evaluations-feedback-and-analytics.md` |
| **Direct model** | A model from a person's own direct connection, added in their browser and marked **Direct** | `src/lib/apis/index.ts:62-70`; `src/lib/components/chat/ModelSelector/ModelItem.svelte:212-213` |
| **Compare** | Choosing several models in the selector so each answers side by side | `src/lib/components/chat/ModelSelector/Selector.svelte:419-454`, `:1000-1020` |
| **Custom-model fallback** | The environment switch `ENABLE_CUSTOM_MODEL_FALLBACK`: when a workspace model's base model is unavailable, the first Selected model answers instead (section 5.24) | `backend/open_webui/main.py:1137-1147`, `:1179-1185` |
| **Clone** | Opens the create page pre-filled from an existing model, with `-clone` added to the id and ` (Clone)` to the name | `src/lib/components/workspace/Models.svelte:211-219` |
| **Export / Import** | Download models as a JSON file, or create and update models from such a file (section 5.20) | `backend/open_webui/routers/models.py:381-673` |
| **Reset** | Admin action that deletes every model record (section 5.18) | `src/lib/components/admin/Settings/Models.svelte:709-720` |
| **Manage Models** | Admin dialog that downloads, loads and deletes models on Ollama, llama.cpp or LM Studio servers | `src/lib/components/admin/Settings/Models/ManageModelsModal.svelte:83-137` |
| **Eject** | Admin button in the selector that unloads a running local model from memory | `src/lib/components/chat/ModelSelector/ModelItem.svelte:282-298`; `backend/open_webui/main.py:956-1064` |
| **Community sharing** | When the admin's community sharing switch is on, model menus offer **Share** (sends the model to openwebui.com) and **Community Reviews**, and Workspace › Models shows **Discover a model** | `src/lib/components/workspace/Models.svelte:221-241`, `:945-951`; `src/lib/components/chat/ModelSelector/ModelItemMenu.svelte:148-169` |

## 5. Workflows (Step by Step)

Tier 1 does not perform these changes; they are described so support can follow what a person did
and recognize where it went wrong. Every save goes to the server, which applies its own checks
(section 5.2) whatever the screen allowed.

### 5.1 Create a Workspace Model

Needs the **Models Access** permission (`workspace.models`) or the `admin` role (section 3.2).

1. Open Workspace › Models and press **Create** at the top of the page
   (`src/lib/components/workspace/Models.svelte:100-106`). The editor opens at
   `/workspace/models/create` (`src/routes/(app)/workspace/models/create/+page.svelte:109-117`).
2. **Picture.** Click the square picture (`Upload profile image`) and choose an image. GIF and WebP
   files are kept as they are; JPEG, PNG and SVG are cropped to a 250 × 250 square and stored as
   WebP inside the model record. Other file types are ignored without a message. **Reset** returns to
   the default picture (`src/lib/components/workspace/Models/ModelEditor.svelte:626-701`, `:717-782`).
   A picture address the server does not accept is dropped on save, again without a message, and the
   default picture is shown (`backend/open_webui/models/models.py:86-96`).
3. **Name.** Type the display name in `Model Name` (required)
   (`src/lib/components/workspace/Models/ModelEditor.svelte:795-800`).
4. **ID.** The `Model ID` line under the name fills in from the name while you type; it can be
   overwritten, but typing in the name again regenerates it. The rules are in section 5.2
   (`src/lib/components/workspace/Models/ModelEditor.svelte:84-91`, `:834-840`).
5. **Access.** Press **Access** to choose who may use or edit the model (Private, Public, people
   and groups, Read or Write). Nothing is saved until the whole model is saved
   (`src/lib/components/workspace/Models/ModelEditor.svelte:600-609`, `:810-814`). The panel itself
   is described in `users-groups-roles-and-permissions.md`, section 5.16; see also section 5.10 here.
6. **Base Model (From).** Pick the provider model to build on (required). The picker
   (`Select a base model (e.g. llama3, gpt-4o)`, searchable) lists provider models only
   (`src/lib/components/workspace/Models/ModelEditor.svelte:853-870`; section 3.1).
7. **Background Image** (optional). **Upload** a PNG, JPEG, WebP or GIF file; the help line reads
   `PNG, JPEG, WebP, or GIF. Up to 5 MiB and 25 megapixels.` The file is uploaded when the model is
   saved and the server checks it again (`src/lib/components/workspace/Models/ModelEditor.svelte:872-956`,
   `:442-447`; `backend/open_webui/routers/models.py:105-123`; `backend/open_webui/utils/validate.py:99-120`).
   In a chat, a folder's background image takes precedence over the model's
   (`src/lib/components/chat/Chat.svelte:181-188`).
8. **Description.** **Custom** shows a text box (`Add a short description about what this model
   does`); **Default** saves no description. An empty box also saves none
   (`src/lib/components/workspace/Models/ModelEditor.svelte:958-1025`, `:330-335`). The description
   is shown in the selector and on the new-chat screen.
9. **Tags.** Type in `Add a tag...` and choose or confirm a tag; existing tags are suggested
   (`src/lib/components/workspace/Models/ModelEditor.svelte:1027-1044`;
   `src/lib/components/common/Tags.svelte:24-56`). Tags drive the tag filters in the selector and
   the lists.
10. **Translations** (optional). The language menu (`Editing language`) switches the name,
    description and prompt suggestions to a per-language version; **Copy default** and **Use
    default** manage each field (`src/lib/components/workspace/Models/ModelEditor.svelte:803-832`,
    `:961-1016`, `:1182-1188`; `src/lib/components/common/LanguageModeSelect.svelte:22-34`).
11. **System Prompt.** The instructions sent with every chat. When the prompt contains chat or user
    variables, a **Detected Variables** panel lists them, marks required chat variables, and shows
    warnings (section 10.2) (`src/lib/components/workspace/Models/ModelEditor.svelte:1053-1122`,
    `:173-225`). Read-only users never receive the system prompt (section 3.5).
12. **Advanced Params.** **Show** opens every generation parameter (section 5.3)
    (`src/lib/components/workspace/Models/ModelEditor.svelte:1125-1149`).
13. **Prompts.** **Default** keeps the admin's prompt suggestions; **Custom** opens a list with
    `Title`, `Subtitle` and `Content` per suggestion, **Import** and **Export** (JSON) and an add
    button. Suggestions with empty content are dropped when a model is created (not when an existing
    model is saved); a Custom list left empty shows no suggestions at all
    (`src/lib/components/workspace/Models/ModelEditor.svelte:1155-1192`;
    `src/lib/components/workspace/Models/PromptSuggestions.svelte:52-229`;
    `src/routes/(app)/workspace/models/create/+page.svelte:41-43`;
    `src/lib/components/chat/Placeholder.svelte:98-106`).
14. **Knowledge.** **Select Knowledge** searches the person's notes, knowledge bases
    (**Collections**) and files in knowledge bases; **Upload** adds files from the computer (needs
    file upload permission; images are refused) (`src/lib/components/workspace/Models/Knowledge.svelte:110-143`,
    `:172-300`; `src/lib/components/workspace/Models/Knowledge/KnowledgeSelector.svelte:48-101`). The
    model cannot be saved while an upload is still running (section 5.2).
15. **Tools** and **Skills.** **Select Tool** and **Select Skill** offer the tools and active skills
    the editor can see; **Enable all** in the list adds every match
    (`src/lib/components/workspace/Models/ToolsSelector.svelte:30-100`;
    `src/lib/components/workspace/Models/SkillsSelector.svelte:30-100`;
    `src/lib/components/workspace/Models/TypeaheadSelector.svelte:113`).
16. **Filters**, **Default Filters** and **Actions** appear only when filter or action functions
    exist (section 5.5) (`src/lib/components/workspace/Models/ModelEditor.svelte:1206-1242`).
17. **Capabilities**, then **Default Features** (shown when web search, image generation or code
    interpreter is ticked), **Builtin Tools** (shown when Builtin Tools is ticked) and **Terminal**
    (shown when Terminal is ticked and a terminal server exists) (section 5.4)
    (`src/lib/components/workspace/Models/ModelEditor.svelte:1246-1275`;
    `src/lib/components/workspace/Models/TerminalSelector.svelte:16-30`).
18. **TTS Voice.** A voice name for reading replies aloud (`e.g. alloy, echo, shimmer`); voices the
    server knows are suggested (`src/lib/components/workspace/Models/ModelEditor.svelte:1277-1288`;
    `src/lib/components/workspace/Models/TTSVoiceInput.svelte:31-41`).
19. Press **Save & Create**. **JSON Preview** shows what will be sent
    (`src/lib/components/workspace/Models/ModelEditor.svelte:1292-1346`). On success the pop-up
    `Model created successfully!` appears and the list opens
    (`src/routes/(app)/workspace/models/create/+page.svelte:51-62`).

Saving publishes a `model.created` event (section 9). The new model appears in other people's model
lists only once they are granted access and their page reloads its model list (section 8).

### 5.2 Model ID Rules and the Checks Made on Save

The ID is made from the name by replacing runs of spaces with hyphens, removing every character
other than unaccented letters, digits and hyphens, and lower-casing the result
(`src/lib/components/workspace/Models/ModelEditor.svelte:84-91`). A fictional "Clinic Notes Helper"
becomes `clinic-notes-helper`; accented letters are dropped, and a name written only in
non-Latin script produces an empty ID that must be typed by hand.

Checks in the order they run when **Save & Create** is pressed:

| # | Check | Where | What the person sees |
|---|---|---|---|
| 1 | ID is empty | `src/lib/components/workspace/Models/ModelEditor.svelte:290-295` | `Model ID is required.` |
| 2 | ID contains a space or other whitespace | `:297-302` | `Model ID cannot contain whitespace.` |
| 3 | Name is empty | `:304-309` | `Model Name is required.` |
| 4 | No base model (workspace models only) | `:311-316` | `Base Model is required.` |
| 5 | A knowledge file is still uploading | `:318-323` | `Please wait until all files are uploaded.` |
| 6 | The background image upload failed | `:442-447` | `Failed to upload background image.` |
| 7 | The ID is already in the person's own model list | `src/routes/(app)/workspace/models/create/+page.svelte:16-24` | `Error: A model with the ID '{modelId}' already exists. Please select a different ID to proceed.` |
| 8 | Server: the person may create models | `backend/open_webui/routers/models.py:293-299` | `401 Unauthorized` |
| 9 | Server: the ID is not empty and has no whitespace | `backend/open_webui/models/models.py:172` | A validation refusal (HTTP 422); the screen's own checks 1 and 2 normally stop this first |
| 10 | Server: the ID is at most 256 characters | `backend/open_webui/routers/models.py:101-102`, `:301-305` | `The model id is too long. Please make sure your model id is less than 256 characters long.` |
| 11 | Server: a model may not be its own base model (the base model is cleared silently) | `:306-308` | Nothing |
| 12 | Server: **no model record of any kind** has this ID, including private models of other people, disabled models and base-model settings records the person cannot see | `:310-315` | `Uh-oh! This model id is already registered. Please choose another model id string.` |
| 13 | Server, non-admins only: a base model is set | `:317-322` | `401 Unauthorized` |
| 14 | Server, non-admins only: the ID is not the ID of a provider model, nor an Ollama model's name without its `:tag` | `:324-337` | `Uh-oh! This model id is already registered. Please choose another model id string.` |
| 15 | Server, non-admins only: every attached knowledge file is readable by the person | `:126-149`, `:339-343` | `You do not have permission to access this resource. Please contact your administrator for assistance.` |
| 16 | Server: the background image is readable by the person and is a valid image | `:105-123`, `:345` | `Background image is not accessible.` or the image rule broken (section 10.1) |
| 17 | Server: sharing choices the person may not make are removed | `:347-353` | Nothing (section 5.10) |
| 18 | Server: the record is written | `:355-360` | `Something went wrong :/` if the write fails |

The create page shows the server's text in a red pop-up (`src/routes/(app)/workspace/models/create/+page.svelte:46-49`).
Check 7 only sees models in the person's own list, so check 12 can refuse an ID that the person
cannot see anywhere. The 256-character rule counts characters, so an ID of exactly 256 characters
is accepted although the message says "less than 256". Because an ID cannot be changed, the way to
get a different ID is to clone the model, adjust the ID before saving, and delete the original;
chats that used the old ID keep it (section 5.24).

### 5.3 Every Advanced Parameter

**Advanced Params** in the model editor shows the complete set below, whatever the editor's role
(`src/lib/components/workspace/Models/ModelEditor.svelte:1147`); the same component appears with
fewer rows in personal settings and chat controls. Each row starts at **Default**, which sends
nothing so the provider's own default applies; clicking it switches to **Custom** with the starting
value shown. Admin **Model Parameters** (section 5.17) are applied underneath: the model's own
values win key by key, then any non-empty value sent with the chat request
(`backend/open_webui/main.py:1169-1177`). Labels in lower case are shown exactly so in the
interface.

| Label | Key | Control and range | Starting value when switched to Custom | Source (`src/lib/components/chat/Settings/Advanced/AdvancedParams.svelte`) |
|---|---|---|---|---|
| Stream Chat Response | `stream_response` | Default, On, Off; a model value overrides the person's own setting (`backend/open_webui/main.py:1193-1194`) | On | `:113-146` |
| Stream Delta Chunk Size | `stream_delta_chunk_size` | Slider 1 to 128 | 1 | `:148-186` |
| Context Compaction Threshold | `compact_token_threshold` | Number, at least 1 | 80000 | `:188-236` |
| Function Calling | `function_calling` | Default, Native, Legacy | Native | `:239-270` |
| Reasoning Tags | `reasoning_tags` | Default, Enabled, Disabled, Custom (Start Tag, End Tag) | Custom with empty tags | `:274-336` |
| Seed | `seed` | Number | 0 | `:339-380` |
| Stop Sequence | `stop` | Text; several sequences separated by commas, saved as a list | empty | `:383-423`; `src/lib/components/workspace/Models/ModelEditor.svelte:427-431` |
| Temperature | `temperature` | 0 to 2, step 0.05 | 0.8 | `:426-460` |
| Reasoning Effort | `reasoning_effort` | Text (for example `medium`) | `medium` | `:463-502` |
| logit_bias | `logit_bias` | Text: comma-separated `token:bias` pairs, bias clamped to -100 to 100 | empty | `:505-548`; `backend/open_webui/utils/payload.py:123-130` |
| max_tokens | `max_tokens` | -2 to 131072 (sent to Ollama as `num_predict`) | 128 | `:551-590`; `backend/open_webui/utils/payload.py:217-225` |
| top_k | `top_k` | Whole number 0 to 1000 | 40 | `:61-71`, `:593-648` |
| top_p | `top_p` | 0 to 1 | 0.9 | `:651-688` |
| min_p | `min_p` | 0 to 1 | 0.0 | `:691-727` |
| frequency_penalty | `frequency_penalty` | -2 to 2 | 1.1 | `:730-767` |
| presence_penalty | `presence_penalty` | -2 to 2 | 0.0 | `:770-807` |
| mirostat | `mirostat` | 0, 1 or 2 | 0 | `:810-845` |
| mirostat_eta | `mirostat_eta` | 0 to 1 | 0.1 | `:848-884` |
| mirostat_tau | `mirostat_tau` | 0 to 10 | 5.0 | `:887-924` |
| repeat_last_n | `repeat_last_n` | -1 to 128 | 64 | `:927-963` |
| tfs_z | `tfs_z` | 0 to 2 | 1 | `:966-1003` |
| repeat_penalty | `repeat_penalty` | -2 to 2 | 1.1 | `:1006-1043` |
| use_mmap | `use_mmap` | Switch | on | `:1046-1088` |
| use_mlock | `use_mlock` | Switch | on | `:1090-1132` |
| think (Ollama) | `think` | Default, On, Custom (text such as `low`, `medium`, `high`), Off | On | `:1136-1189` |
| format (Ollama) | `format` | Default or JSON; text `json` or a JSON schema | `json` | `:1192-1229` |
| num_keep (Ollama) | `num_keep` | -1 to 10240000 | 24 | `:1232-1273` |
| num_ctx (Ollama) | `num_ctx` | -1 to 10240000 (context window) | 2048 | `:1276-1315` |
| num_batch (Ollama) | `num_batch` | 256 to 8192, step 256 | 512 | `:1318-1359` |
| num_thread (Ollama) | `num_thread` | 1 to 256 | 2 | `:1362-1403` |
| num_gpu (Ollama) | `num_gpu` | 0 to 256 | 0 | `:1406-1446` |
| keep_alive (Ollama) | `keep_alive` | Text such as `30s`, `10m`, `1h` | `5m` | `:1449-1489` |
| Custom parameters | `custom_params` | **Add Custom Parameter** adds name and value pairs; values that are valid JSON are sent as JSON | `custom_param_name` = `custom_param_value` | `:1492-1559`; `backend/open_webui/utils/payload.py:167-180` |

How they reach the provider: the first five rows and the system prompt are MedIT GPT settings and
are never sent (`backend/open_webui/utils/payload.py:145-158`). For OpenAI-compatible connections the
rest are added to the request, with `temperature`, `top_p`, `min_p`, `max_tokens`,
`frequency_penalty`, `presence_penalty`, `reasoning_effort`, `seed`, `stop` and `logit_bias`
converted to the expected type and any other key passed as it is
(`backend/open_webui/utils/payload.py:69-82`, `:164-195`). For Ollama they go into the request's
options, and `format`, `keep_alive` and `think` at the top level
(`backend/open_webui/utils/payload.py:198-270`). Whether a provider honours a given key is the
provider's behaviour, outside the repository. A model's own parameters are not shown to read-only
users (section 3.5).

### 5.4 Capabilities, Default Features and Built-In Tools

When the editor opens, every capability starts from the admin's **Model Capabilities** default,
falling back to on (Usage starts unset); a saved model then keeps its own explicit value for every
capability (Usage only once it has been set), so a later change to the admin default does not reach
models already saved in the editor (`src/lib/components/workspace/Models/ModelEditor.svelte:494-503`, `:568-571`, `:328`;
`src/lib/constants.ts:115-128`). In the model list, admin default capabilities are merged under the
model's own values (`backend/open_webui/utils/models.py:337-356`).

| Label | Key | What switching it off does | Source |
|---|---|---|---|
| Vision | `vision` | Image attachments are refused with `Selected model(s) do not support image inputs` | `src/lib/components/chat/MessageInput.svelte:1126-1130` |
| File Upload | `file_upload` | File attachments are refused with `Model(s) do not support file upload` (unless a terminal stores uploads); the File Context tick is hidden | `src/lib/components/chat/MessageInput.svelte:924-929`; `src/lib/components/workspace/Models/Capabilities.svelte:72-78` |
| File Context | `file_context` | Attached files are not extracted into the prompt | `backend/open_webui/utils/middleware.py:3206-3214` |
| Web Search | `web_search` | No **Web Search** control in the chat (every selected model must have it) | `src/lib/components/chat/MessageInput.svelte:824-828` |
| Image Generation | `image_generation` | No **Image** control | `src/lib/components/chat/MessageInput.svelte:830-834` |
| Code Interpreter | `code_interpreter` | No **Code Interpreter** control | `src/lib/components/chat/MessageInput.svelte:836-841`; `backend/open_webui/utils/middleware.py:4878-4882` |
| Terminal | `terminal` | Terminal tools are not loaded for the model | `backend/open_webui/utils/middleware.py:3036-3040` |
| Usage | `usage` | When on, streaming requests ask the provider for token usage | `backend/open_webui/main.py:1196-1198` |
| Citations | `citations` | Citation markers and the sources list are not shown | `src/lib/components/chat/Messages/ContentRenderer.svelte:128-130`; `backend/open_webui/utils/middleware.py:5840-5843` |
| Status Updates | `status_updates` | Progress lines (for example web search progress) are not shown | `src/lib/components/chat/Messages/ResponseMessage.svelte:198-199` |
| Memory | `memory` | Stored memories are not added to the conversation and memory tools are not offered | `backend/open_webui/utils/memory.py:286-292`; `backend/open_webui/utils/tools.py:656-663` |
| Builtin Tools | `builtin_tools` | No built-in tools in native function-calling mode; the Builtin Tools list is hidden | `backend/open_webui/utils/middleware.py:2809-2813`; `src/lib/components/workspace/Models/ModelEditor.svelte:1265-1269` |

The labels and tooltips are dotted keys whose English text is in
`src/lib/i18n/locales/en-US/translation.json:2573-2597`. Chat-screen effects are described in more
detail in `chat-composer-and-message-display.md`, section 3.2, and server effects in
`chat-completion-pipeline-and-generation-tasks.md`, section 7.6.

**Default Features** (Web Search, Image Generation, Code Interpreter) are offered for whichever of
those capabilities is ticked; a ticked feature starts switched on in a new chat with this model,
subject to the conditions in section 3.6 (`src/lib/components/workspace/Models/DefaultFeatures.svelte:29-75`;
`src/lib/components/chat/Chat.svelte:1083-1106`).

**Builtin Tools** lists sixteen groups, each ticked unless switched off for this model: Time &
Calculation, Ask User, Memory, Chat History, Notes, Knowledge Base, Files, Channels, Notifications,
Web Search, Image Generation, Code Interpreter, Task Management, Automations, Calendar and
Sub-agents (`src/lib/components/workspace/Models/BuiltinTools.svelte:11-90`;
`src/lib/i18n/locales/en-US/translation.json:2540-2572`). A group is offered only when the model's
Builtin Tools capability is on, the related admin feature is on and the person has the matching
permission (`backend/open_webui/utils/tools.py:520-560`). Which tools each group contains is in
`builtin-native-tools.md`.

### 5.5 Knowledge, Tools, Skills, Filters and Actions on a Model

| Item | Stored in the record as | What happens in a chat with the model | Source |
|---|---|---|---|
| Knowledge | `meta.knowledge`: a list of references (id, name, type and, for files, whether the whole document is used); extracted text is not stored in the model | In native function calling (the default) the model gets knowledge tools limited to the attached items; in legacy function calling the items are added to the chat's files and searched before the reply. Access rules are in section 3.6 | `src/lib/components/workspace/Models/ModelEditor.svelte:262-281`, `:337-343`; `backend/open_webui/models/models.py:33-62`; `backend/open_webui/utils/middleware.py:2604-2644`; `backend/open_webui/tools/builtin.py:2199-2237` |
| Whole document or focused retrieval | `context: 'full'` on a knowledge item | Clicking an attached item opens a dialog with the switch **Using Entire Document** / **Using Focused Retrieval** | `src/lib/components/workspace/Models/Knowledge.svelte:150-152`, `:228-241`; `src/lib/components/common/FileItemModal.svelte:346-371` |
| Tools | `meta.toolIds` | Pre-selected in a new chat. Tools from a tool server the person has not yet signed in to are not pre-selected; in a new chat the browser is sent to that server's sign-in | `src/lib/components/chat/Chat.svelte:951-968`, `:1028-1060` |
| Skills | `meta.skillIds` | Pre-selected in a new chat | `src/lib/components/chat/Chat.svelte:1062-1073` |
| Filters | `meta.filterIds` | The chosen filter functions run on messages to and from this model, together with every global filter; inactive filters are ignored | `src/lib/components/workspace/Models/FiltersSelector.svelte:19-31`; `backend/open_webui/utils/models.py:393-399` |
| Default Filters | `meta.defaultFilterIds` | Toggleable filters (those the person can switch in the chat) start switched on | `src/lib/components/workspace/Models/ModelEditor.svelte:1217-1231`; `src/lib/components/chat/Chat.svelte:1075-1080` |
| Actions | `meta.actionIds` | Buttons under the model's replies, together with every global action; inactive actions are ignored | `backend/open_webui/utils/models.py:385-419` |

Filters and actions are functions managed by admins; when plugins are switched off on the server
(`ENABLE_PLUGINS`, on in code) the editor shows neither section and models ignore them
(`backend/open_webui/routers/functions.py:48-53`; `backend/open_webui/utils/models.py:152-165`,
`:196-200`; `backend/open_webui/env.py:1186`). The editor lists inactive functions too, so a filter
can be attached that has no effect until an admin activates it
(`backend/open_webui/models/functions.py:210-217`). Function types and global functions are
described in `functions-pipes-filters-actions-and-pipelines.md`; knowledge bases in
`knowledge-bases.md`; tools in `workspace-tools-tool-servers-mcp-and-terminals.md`; skills in
`prompts-and-skills.md`.

### 5.6 Edit a Workspace Model

1. In Workspace › Models, click the model's row or choose **Edit** in its **More** menu. Rows of
   read-only models are not clickable (`src/lib/components/workspace/Models.svelte:144-148`,
   `:702-722`; `src/lib/components/workspace/Models/ModelMenu.svelte:68-76`). The owner can also use
   **Edit** in the chat selector's menu (section 5.21).
2. The edit page loads the full model. Without write access it shows `You do not have permission to
   edit this model` and returns to the list; a model that no longer exists returns to the list
   without a message (`src/routes/(app)/workspace/models/edit/+page.svelte:18-37`).
3. Change any field except the ID, which is greyed out
   (`src/lib/components/workspace/Models/ModelEditor.svelte:834-840`).
4. Press **Save & Update**. Success shows `Model updated successfully` and returns to the list;
   a refusal shows the server's text (`src/routes/(app)/workspace/models/edit/+page.svelte:39-60`;
   `src/lib/components/workspace/Models/ModelEditor.svelte:448-473`).

On the server: the person must own the model, hold a write grant or be an admin; a non-admin cannot
remove the base model; a picture or background left untouched is kept; grants that were already
on the model are kept and only newly added ones are checked against the person's sharing
permissions (`backend/open_webui/routers/models.py:932-1021`). Saving publishes `model.updated`.

### 5.7 Clone a Model

1. Choose **Clone** in the model's menu (Workspace › Models for owners and write-grant holders;
   Settings › Admin › Models for admins, offered only for enabled, non-arena models)
   (`src/lib/components/workspace/Models/ModelMenu.svelte:149-158`;
   `src/lib/components/admin/Settings/Models/ModelMenu.svelte:200-208`).
2. The create page opens pre-filled with the full model, the ID `<id>-clone` and the name
   `<name> (Clone)`. Cloning a base model from the admin list makes a new workspace model that uses
   that base model (`src/lib/components/workspace/Models.svelte:208-219`;
   `src/lib/components/admin/Settings/Models.svelte:637-647`).
3. Adjust anything, including the ID, and press **Save & Create** (section 5.1).

The clone starts with the original's access list (only entries the cloner may grant are kept) and
belongs to the person who saved it (`src/lib/components/workspace/Models/ModelEditor.svelte:575`;
`backend/open_webui/routers/models.py:347-355`). Saving it needs `workspace.models`.

### 5.8 Model Settings Pages Opened From Elsewhere

- A model page on the community site can open `/workspace/models/create` pre-filled with a model;
  the page accepts these only from the community site's origins
  (`src/routes/(app)/workspace/models/create/+page.svelte:74-96`).
- Clicking a workspace model in Settings › Admin › Models closes the settings window and opens the
  workspace editor for it (`src/lib/components/admin/Settings/Models.svelte:627-635`).

### 5.9 Hide or Show a Model

1. **Workspace › Models** (owner, write grant, admin): **Hide Model** / **Show Model** in the row's
   menu, or hold Shift and press the eye button on the row. The pop-up reads
   `Model {name} is now {status}`, where `{name}` is the model ID and `{status}` is the English word
   `hidden` or `visible` (`src/lib/components/workspace/Models.svelte:243-273`, `:815-833`;
   `src/lib/components/workspace/Models/ModelMenu.svelte:78-128`).
2. **Settings › Admin › Models**: the same menu item or Shift and the eye button; pop-ups
   `Model {name} is now hidden` and `Model {name} is now visible`. For a base model with no record,
   hiding creates one (`src/lib/components/admin/Settings/Models.svelte:481-512`, `:540-567`,
   `:1074-1089`).
3. **Actions › Show All / Hide All** applies to every model matching the current search and filters
   (in Workspace › Models across all pages) and ends with `All models are now visible` or `All
   models are now hidden` (`src/lib/components/workspace/Models.svelte:325-349`, `:377-415`;
   `src/lib/components/admin/Settings/Models.svelte:215-251`).

A hidden model is faded in both lists and left out of the selector (search included), the sidebar
pins and new-chat defaults. It keeps working through `/?model=<id>` links and in existing chats, and
admins still see it in the base model picker (`src/lib/components/workspace/Models.svelte:705-707`;
`src/lib/components/chat/ModelSelector/Selector.svelte:310`; `src/lib/stores/index.ts:116-120`;
`src/lib/components/chat/Chat.svelte:2046-2048`, `:2068-2091`, `:2311-2321`;
`src/lib/components/workspace/Models/ModelEditor.svelte:239-241`). To stop people using a model,
it must be disabled or its access removed, not hidden.

### 5.10 Share a Model

The **Access** panel, its options and the cases where a share silently does not take effect are
in `users-groups-roles-and-permissions.md`, sections 5.16 and 5.17. Model-specific points:

1. **Workspace models.** Entries can be **Read** or **Write**. Choices made in the panel are saved
   only when the model is saved with **Save & Create** or **Save & Update**
   (`src/lib/components/workspace/Models/ModelEditor.svelte:600-609`, `:327`).
2. **Write is powerful.** A write grant lets the holder edit, hide, switch off, re-share, export
   (with the export permission) and delete the model (section 3.1).
3. **Base models (admins).** The base-model editor offers **Read** only
   (`src/lib/components/workspace/Models/ModelEditor.svelte:603`). In the admin list, **Make
   Public** (globe) adds the public read entry at once and shows `Model is now public`; **Make
   Private** (lock) removes **every** entry, including people and groups, and shows `Model is now
   private` (`src/lib/components/admin/Settings/Models.svelte:569-604`). For a base model with no
   record, the server first creates a minimal record (`backend/open_webui/routers/models.py:1042-1066`).
4. **What recipients also need**: read access to the base model, and separate access to attached
   knowledge bases and tools (section 3.6).
5. **When recipients see it**: after their page reloads its model list (section 8).

Every access change publishes `model.updated` or `model.access_updated` (section 9).

### 5.11 Enable or Disable a Model

1. **Workspace › Models**: the switch at the end of each row the person can write (tooltip
   **Enabled** / **Disabled**). No message is shown, including when the server refuses
   (`src/lib/components/workspace/Models.svelte:889-916`).
2. **Settings › Admin › Models**: the switch at the end of each row. A base model with no record
   shows as enabled; switching it off creates a record that is disabled and has no access entries
   (`src/lib/components/admin/Settings/Models.svelte:295-313`, `:514-538`, `:1228-1241`).
3. **Actions › Enable All / Disable All** applies to every model matching the current filters
   (`src/lib/components/workspace/Models.svelte:351-375`;
   `src/lib/components/admin/Settings/Models.svelte:187-213`).

A disabled model disappears from every person's model list, admins included; a chat that still
names it gets `Model not found` (section 5.24) (`backend/open_webui/utils/models.py:184-210`;
`backend/open_webui/main.py:1128-1129`). Disabled workspace models stay in Workspace › Models with a
faded picture, so their owners can switch them back on
(`src/lib/components/workspace/Models.svelte:724`). Each change publishes `model.enabled` or
`model.disabled` (`backend/open_webui/routers/models.py:881-924`).

### 5.12 Delete a Model

1. **Workspace › Models** (owner, write grant, admin): **Delete** in the row's menu opens the
   standard confirmation `Confirm your action` / `This action cannot be undone. Do you wish to
   continue?`; confirming shows `Deleted {name}` with the model ID
   (`src/lib/components/workspace/Models.svelte:187-206`, `:465-470`, `:876-879`;
   `src/lib/components/common/ConfirmDialog.svelte:130-154`). **Holding Shift shows a delete button
   on each row that deletes at once, without confirmation** (`src/lib/components/workspace/Models.svelte:835-848`).
2. **Chat model selector** (admins): the **Delete** item appears for Ollama models and llama.cpp
   models, and for an admin's own workspace models built on them. It asks `Are you sure you want to
   delete **{modelName}**?`. For a workspace model it deletes the record; **for a base model it
   deletes the model from the first Ollama server that has it**. A llama.cpp base model is sent to
   the same Ollama endpoint, so its deletion is expected to fail with `Error deleting model:
   {error}` (read from code; to confirm in a test environment)
   (`src/lib/components/chat/ModelSelector/ModelItemMenu.svelte:50-100`;
   `src/lib/components/chat/ModelSelector/Selector.svelte:807-856`, `:893-902`;
   `backend/open_webui/routers/ollama.py:798-838`).

Deletion removes the record and all its access entries; nothing is kept for recovery
(`backend/open_webui/models/models.py:575-584`). Uploaded files, knowledge bases and tools the model
referred to are not deleted. Chats are covered in section 5.24. The event is `model.deleted`
(`backend/open_webui/routers/models.py:1111-1150`).

A base-model settings record has no **Delete** in the interface: the admin list's menu and the
base-model editor offer none (`src/lib/components/admin/Settings/Models/ModelMenu.svelte:63-221`).
It is removed only by **Reset** (section 5.18) or through the API, after which that base model
shows the provider's name and settings again and is admin-only.

### 5.13 Admin: The Settings › Admin › Models List

How to open it is in section 2.1. What the list holds and offers
(`src/lib/components/admin/Settings/Models.svelte:268-331`, `:724-1280`):

- **Contents.** Every model in the admin's own model list, plus every provider model the list
  dropped (for example because it is disabled), plus every stored record not otherwise listed (for
  example a disabled workspace model, or one whose base model has gone). The list therefore shows
  models that people cannot currently use. The heading `Models` carries the count of rows shown.
- **Search** (`Search Models`) matches model names only (`:155-156`).
- **View filter**: All, Base Models, Workspace Models, Enabled, Disabled, Visible, Hidden, Public,
  Private, Selected, Pinned (`src/lib/components/admin/Settings/Models/AdminViewSelector.svelte:15-27`;
  `src/lib/components/admin/Settings/Models.svelte:157-169`). A **tag filter** appears when records
  have tags (`:821-832`).
- **Actions**: **Import**, **Export**, **Manage**, **Reset**, **Enable All**, **Disable All**,
  **Show All**, **Hide All** (`:835-960`; labels `translation.json:2609-2616`).
- **Each row**: a drag handle (tooltip `Drag to reorder`, or `Clear filters to reorder` while a
  search or filter is active), the picture, the name, the access label (**Public**, **Shared** or
  **Private**), and **Selected** / **Pinned** labels when the model is an admin default. Hovering the
  name shows the description, or for Ollama models the digest and date, or the ID (`:972-1072`).
- **Holding Shift** shows quick buttons on every row: eye (hide or show), tick (`Set as Selected
  Model` / `Remove Selected Model`), pin (`Set as Pinned Model` / `Remove Pinned Model`) and globe or
  lock (`Make Public` / `Make Private`) (`:1074-1163`).
- **Edit** (pencil), the **More** menu (Hide or Show Model, Set or Remove Selected Model, Set or
  Remove Pinned Model, Make Public or Private, Keep in or Hide from Sidebar, Copy Link, Clone,
  Export) and the **Enabled** switch (`:1165-1241`;
  `src/lib/components/admin/Settings/Models/ModelMenu.svelte:63-221`).
- **Save** at the bottom is active only when the order or the Model Defaults have unsaved changes
  (`src/lib/components/admin/Settings/Models.svelte:1260-1278`). Every other action on this page
  saves at once.

### 5.14 Admin: Order the Model List

1. Clear the search, view filter and tag filter; the drag handles become active
   (`src/lib/components/admin/Settings/Models.svelte:183-185`, `:460-479`).
2. Drag rows into the order wanted.
3. Press **Save**; the pop-up `Model order saved successfully` confirms
   (`src/lib/components/admin/Settings/Models.svelte:333-374`, `:437-458`).

The saved order (`ui.model_order_list`) lists every model's ID. Each person's model list, and so the
selector, follows it; models missing from it come after, sorted by name
(`src/lib/components/admin/Settings/Models.svelte:316-322`; `backend/open_webui/main.py:928-937`).
With no saved order, models appear in the order the server assembles them: pipe, OpenAI-compatible
and Ollama models as the providers return them, then arena models, then workspace models
(`backend/open_webui/utils/models.py:57-66`, `:115-149`, `:267`).

### 5.15 Admin: Configure a Base Model

1. In Settings › Admin › Models, click a base model's row or its pencil. (From the chat selector,
   **Edit** on a base model opens the same page; section 5.21.) The page shows the model editor
   without the base-model picker or background image, with **Read**-only sharing
   (`src/lib/components/admin/Settings/Models.svelte:627-635`, `:1281-1300`;
   `src/lib/components/workspace/Models/ModelEditor.svelte:603`, `:853`, `:872`).
2. Change the name, access, description, tags, system prompt, parameters, prompt suggestions,
   knowledge, tools, skills, filters, actions, capabilities, default features, built-in tools,
   terminal or voice (section 5.1).
3. Press **Save & Update**. The first save creates the base-model settings record; later saves
   update it. Success shows `Model updated successfully`; any refusal shows only `Failed to save
   model`, without the server's reason, and the code shows that pop-up twice
   (`src/lib/components/admin/Settings/Models.svelte:481-512`, `:1286-1295`;
   `src/lib/components/workspace/Models/ModelEditor.svelte:448-449`, `:473`). **Back** leaves without
   saving (`src/lib/components/workspace/Models/ModelEditor.svelte:612-623`).

The record renames the base model for everyone, carries its access list, and its parameters and
system prompt are applied whenever that base model is used directly
(`backend/open_webui/utils/models.py:178-207`; `backend/open_webui/routers/openai.py:1515-1533`;
`backend/open_webui/routers/ollama.py:1136-1149`). A base model needs a record with a read entry
before non-admins can see it (section 3.3).

### 5.16 Admin: Default Models for New Chats and Pinned Models

1. In the admin list, use **Set as Selected Model** or **Set as Pinned Model** (Shift buttons or the
   **More** menu). Each click saves at once and shows `Model added to selected models`, `Model
   removed from selected models`, `Model added to pinned models` or `Model removed from pinned
   models` (`src/lib/components/admin/Settings/Models.svelte:376-435`;
   `src/lib/components/admin/Settings/Models/ModelMenu.svelte:119-150`).
2. The values are stored as comma-separated IDs in `ui.default_models` and
   `ui.default_pinned_models` (`src/lib/components/admin/Settings/Models.svelte:387-393`;
   `backend/open_webui/routers/configs.py:734-770`).

Effects for people:

- **Selected models** start every new chat for people who have no personal default; several
  Selected models start a side-by-side chat. Selected models that are hidden or not in the person's
  list are skipped (section 5.22) (`src/lib/components/chat/Chat.svelte:2050`, `:2105-2129`). Making a
  model Selected does not share it.
- The **first** Selected model is also the replacement used by the custom-model fallback
  (section 5.24).
- **Pinned models** appear in the sidebar of everyone who has never pinned or unpinned a model
  themselves; models a person cannot see, or hidden models, are left out
  (`src/lib/stores/index.ts:108-120`).

### 5.17 Admin: Model Defaults

1. At the top of the admin list, **Model Defaults** › **Configure** opens three parts, each with
   **Configure** / **Close**: **Model Capabilities** (capabilities, default features, built-in
   tools), **Model Parameters** (the full parameter set of section 5.3) and **Prompt Suggestions**
   (with an editing-language menu and **Reset to Defaults**)
   (`src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:157-310`).
2. Press the page's **Save**. The panel writes `models.default_metadata` and `models.default_params`,
   then the default prompt suggestions, and shows `Models configuration saved successfully` or
   `Failed to save models configuration` (`src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:105-150`;
   `backend/open_webui/routers/configs.py:754-770`, `:817-840`).

| Default | Effect | Source |
|---|---|---|
| Capabilities | Merged under each model's own capabilities in the model list, and the starting point of the editor (models already saved in the editor keep their own values, section 5.4) | `backend/open_webui/utils/models.py:337-356`; `src/lib/components/workspace/Models/ModelEditor.svelte:494-503` |
| Default features, built-in tools | Used by models that have none of their own | `backend/open_webui/utils/models.py:349-356` |
| Parameters | Applied underneath every model's own parameters when a chat is sent | `backend/open_webui/main.py:1169-1177` |
| Prompt suggestions | Shown on new chats with models whose prompts are set to **Default**. An empty list shows none; when nothing is stored, built-in English examples are shown, and **Reset to Defaults** returns to them | `src/lib/components/chat/Placeholder.svelte:98-106`; `src/lib/utils/localizedContent.ts:131-178`; `backend/open_webui/config.py:1678-1683` |

The panel always saves the capability defaults, even when only parameters or suggestions changed
(`src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:110-114`). Read from code: once
any default metadata is stored, every model in the list carries it, including base models without a
record; for admins with `BYPASS_ADMIN_ACCESS_CONTROL` off this takes record-less base models out of
their own list (`backend/open_webui/utils/models.py:341-347`, `:563-574`; section 14.4).

### 5.18 Admin: Reset All Models

1. **Actions** › **Reset** asks `Reset All Models` / `This will delete all models including custom
   models and cannot be undone.` (`src/lib/components/admin/Settings/Models.svelte:709-720`, `:890-901`).
2. Confirming deletes every model record and all their access entries, and shows `All models
   deleted successfully` (`backend/open_webui/models/models.py:586-598`;
   `backend/open_webui/routers/models.py:1153-1160`).

Effects: every person's workspace models are gone; every base model returns to the provider's name
and settings and becomes admin-only, because no records with read entries remain; chats keep their
model IDs (section 5.24). The admin defaults (Selected, Pinned, order, Model Defaults) are separate
settings and are not cleared. There is no undo; recovery would need a database backup, whose
existence is TO BE CONFIRMED.

### 5.19 Admin: Manage Models on Ollama, llama.cpp and LM Studio

**Actions** › **Manage** opens `Manage Models`. It manages Ollama when Ollama is on with at least
one server, otherwise llama.cpp and LM Studio connections; with both kinds it offers an engine menu
(**Ollama** / **Model providers**), and with neither it shows `No inference engine with management
support found` (`src/lib/components/admin/Settings/Models/ManageModelsModal.svelte:24-137`). Pulling,
updating, creating, uploading, loading, unloading and deleting models on those servers is described
in `model-connections-openai-ollama-and-direct.md`, sections 5.10 and 5.11; the dialog's messages
are listed in section 10.6. Admins can also download a model by typing its name into the chat
selector (`Pull "{searchValue}" from Ollama.com`, `Download "{searchValue}" from {provider}`) and
unload a running model with **Eject** (`src/lib/components/chat/ModelSelector/Selector.svelte:312-346`;
`src/lib/components/chat/ModelSelector/ModelItem.svelte:282-298`). These change the provider's
models, not MedIT GPT's model records.

### 5.20 Export and Import Models

| Action | Where | Who | Result | Source |
|---|---|---|---|---|
| **Export JSON** | Workspace › Models top actions | Admin, or `workspace.models_export` | `models-export-<timestamp>.json` with every workspace model the person may write (all of them for an admin while `BYPASS_ADMIN_ACCESS_CONTROL` is on) | `src/lib/components/workspace/Models.svelte:113-120`, `:286-300`; `backend/open_webui/routers/models.py:381-429` |
| **Export** (one model) | Workspace › Models row menu | Write access plus the export permission | `<model id>-<timestamp>.json` | `src/lib/components/workspace/Models.svelte:302-313`; `src/lib/components/workspace/Models/ModelMenu.svelte:173-182` |
| **Import JSON** | Workspace › Models top actions | Admin, or `workspace.models_import` | Creates or updates models; the list reloads, with no success message | `src/lib/components/workspace/Models.svelte:107-112`, `:472-520` |
| **Actions › Export** / row **Export** | Settings › Admin › Models | Admin | Every model in the admin list (workspace models through the export, base models from their record or the provider's entry) | `src/lib/components/admin/Settings/Models.svelte:253-266`, `:617-660`, `:863-874` |
| **Actions › Import** | Settings › Admin › Models | Admin | `Models imported successfully` or `Failed to import models` | `src/lib/components/admin/Settings/Models.svelte:736-771`, `:849-861` |

**What an export file contains.** For each model: the ID, the owner's user id, the base model ID,
the name, the parameters (including the system prompt), the metadata (description, tags,
capabilities, picture, knowledge references, tool, skill, filter and action ids and the rest), the
access list (user and group ids), the Enabled flag and timestamps. A background image is embedded as
image data (`backend/open_webui/routers/models.py:377-429`; `backend/open_webui/models/models.py:127-144`).
Knowledge content, tool code and functions are not included, only their ids, so on another site
those references may point at nothing. Treat export files as containing personal identifiers and
any confidential instructions written into system prompts.

**How the server imports** (`backend/open_webui/routers/models.py:441-673`):

- The file must be a JSON list (the workspace page also accepts entries wrapped in `info`)
  (`src/lib/components/workspace/Models.svelte:484-501`).
- Entries without an ID, or with an ID longer than 256 characters or containing whitespace, are
  ignored.
- An entry whose ID exists **updates** that model if the person owns it, holds a write grant or is
  an admin: its metadata is merged over the existing metadata, its parameters replace the old ones
  (an entry with no parameters therefore clears them, system prompt included), and the access list
  changes only if the entry contains one. A non-admin's entry that would remove the base model is
  skipped.
- An entry with a new ID **creates** a model owned by the importer; for non-admins it must name a
  base model and must not use a provider model's ID.
- Entries referring to knowledge files the person cannot read are skipped.
- Sharing entries the person may not grant are removed.
- An embedded background image must be a valid PNG, JPEG, WebP or GIF of at most 5 MiB; it is
  stored as a new file owned by the importer.
- Skipped entries are reported only as server log lines (section 10.7); the import still reports
  success and publishes `model.imported` with the count and IDs actually imported.
- Entries are saved one at a time, so an error part-way (for example an invalid background image)
  ends the import with an error but leaves the earlier entries imported.

### 5.21 Choose a Model in a Chat (the Model Selector)

The selector sits in the message composer at the bottom right; Cmd+Shift+M opens it
(`src/lib/components/chat/MessageInput.svelte:2577-2585`; `src/lib/shortcuts.ts:89`). Its button
shows the selected model's name, with `+N` when several are compared
(`src/lib/components/chat/ModelSelector/Selector.svelte:187-196`). Pointing at the button reloads
the person's model list from the server (`:922-938`).

| Feature | Behaviour | Source (`src/lib/components/chat/ModelSelector/`) |
|---|---|---|
| Search (`Search a model`) | Fuzzy match on model ID, name and tags | `Selector.svelte:227-290`, `:953-996` |
| Filter menu (`All`) | **Local**, **External**, **Direct** (connection types present) and each tag. The chosen filter stays in force when the menu is reopened; only the search text is cleared | `Selector.svelte:137-154`, `:200-202`, `:359-389`, `:1022-1039` |
| Hidden models | Never listed, even when searched for | `Selector.svelte:310` |
| **Compare** | Lets several models be ticked; each answers side by side. Needs `chat.multiple_models` (or admin). The last ticked model cannot be unticked | `Selector.svelte:419-454`, `:1000-1020`; `../ModelSelector.svelte:83-84` |
| A model row | Picture, name (pointing shows `name (id)`; admins also see the ID over the picture), size details for local engines, a dot for loaded local models (`Loaded` or `Unloads {FROM_NOW}`), tag, Direct or External and description icons | `ModelItem.svelte:56-260` |
| Row **More** menu | **Edit** (workspace models: only for their owner, opening the workspace editor; base models: admins, opening Settings › Admin › Models), **Delete** (admins, section 5.12), **Keep in Sidebar** / **Hide from Sidebar**, **Copy Link**, **Community Reviews** (when community sharing is on) | `ModelItemMenu.svelte:48-170` |
| **Eject** | Admins, on loaded local models: unloads the model from memory; `Model unloaded successfully` or `Error unloading model: {error}` | `ModelItem.svelte:282-298`; `Selector.svelte:791-805` |
| **Set as default** | Shown while the chat has no messages; saves the current selection as the person's default for new chats (`Default model updated`; with an empty selection `Choose a model before saving...`). Whether it persists depends on `settings.interface` (section 3.7) | `Selector.svelte:1263-1272`; `../ModelSelector.svelte:26-36`; `../MessageInput.svelte:2580` |
| Empty list | Admins with no models at all see `No models available`, `Connect to an AI provider to start chatting` and **Manage Connections**; otherwise `No results found` | `Selector.svelte:1046-1078` |
| Admin downloads | Typing a name offers download rows for Ollama and for llama.cpp or LM Studio connections (section 5.19) | `Selector.svelte:312-346`, `:1115-1260` |

If a model selected in the open chat is no longer in the person's list, the selector clears it and
shows `Select a model` (`src/lib/components/chat/ModelSelector.svelte:48-56`, `:67-70`). The `/model`
slash command and the chat address parameters are covered in `chat-composer-and-message-display.md`.

### 5.22 How a New Chat's Model Is Chosen

When a new chat opens, the code picks its model(s) in this order
(`src/lib/components/chat/Chat.svelte:2046-2133`):

1. **Address.** `?model=<id>` or `?models=<id>,<id>`: the listed models, unavailable ones dropped.
   A single ID the person cannot see opens the selector with that ID typed into its search box.
   Hidden models are accepted here (`:2068-2091`).
2. Otherwise, the first of: the models set on the **folder** the chat is started in (`:2093-2095`);
   the models of the chat last viewed in this browser tab, carried over once (`:2097-2100`, `:934-949`);
   the person's **personal default** (`:2102-2104`); the admin's **Selected models** (`:2105-2108`).
   Hidden models and models not in the person's list are then removed (`:2112-2113`).
3. If nothing is left: the admin's Selected models that the person can use, else the first
   non-hidden model in the person's list, else no model (`:2116-2132`).
4. The model's default tools, skills, filters, features and terminal are applied when exactly one
   model is selected (section 3.6).

A person whose personal default model was deleted, disabled, hidden or unshared therefore falls back
to the admin's Selected models without any message. No control in the model screens clears a
personal default; choosing **Set as default** again replaces it.

### 5.23 Sidebar Pinned Models

- The sidebar shows the person's pins that are in their model list and not hidden; pins for other
  models are kept but not shown (`src/lib/stores/index.ts:115-120`;
  `src/lib/components/layout/Sidebar/PinnedModelList.svelte:62-83`).
- Clicking a pin opens a new chat with that model (`/?model=<id>`)
  (`src/lib/components/layout/Sidebar/PinnedModelItem.svelte:33-38`).
- Holding Shift while pointing at a pin shows **Unpin**
  (`src/lib/components/layout/Sidebar/PinnedModelItem.svelte:60-76`).
- On a computer (not on mobile), pins can be dragged into a new order; pins for models not shown
  are kept at the end (`src/lib/components/layout/Sidebar/PinnedModelList.svelte:21-54`).
- **Keep in Sidebar** / **Hide from Sidebar** appear in the selector's row menu, the Workspace ›
  Models row menu and the admin list's menu (`src/lib/components/chat/ModelSelector/ModelItemMenu.svelte:105-130`;
  `src/lib/components/workspace/Models/ModelMenu.svelte:130-147`;
  `src/lib/components/admin/Settings/Models/ModelMenu.svelte:172-189`).
- Until a person first pins or unpins anything, their sidebar shows the admin's Pinned models. The
  first change saves that list, plus or minus the model, as their own, and later changes to the
  admin's list no longer reach them (`src/lib/stores/index.ts:108-113`;
  `src/lib/components/chat/ModelSelector.svelte:38-46`).

### 5.24 What Happens When a Model or Its Base Model Disappears

| Situation | Model lists | Existing chats | Sending a message | Source |
|---|---|---|---|---|
| A workspace model is **deleted** (or all records are **Reset**) | Gone for everyone | The chat keeps the model ID. Reopening it replaces the selection: personal default, then the admin's Selected models, then the first available model, with no message. Earlier replies show the raw model ID instead of the name, and the default picture | A page loaded before the deletion gets `Model not found` (shown as a pop-up and in the reply) | `src/lib/components/chat/Chat.svelte:204-222`, `:2311-2332`; `src/lib/components/chat/Messages/ResponseMessage.svelte:193-195`; `backend/open_webui/routers/models.py:867-873`; `backend/open_webui/main.py:1128-1129` |
| A model is **disabled** | Gone for everyone, admins included | As for a deleted model, until it is switched on again | `Model not found` | `backend/open_webui/utils/models.py:184-210` |
| A person **loses access** (grant removed, group changed) | Gone for that person | As above, for that person | `Model not found` | `users-groups-roles-and-permissions.md`, section 3.7 |
| A model is **hidden** | Still listed, but not in the selector | Keep working | Works | Section 5.9 |
| A **base model** stops being offered (removed or renamed at the provider, connection switched off, Prefix ID changed, or its connection fails while other connections still answer) | The base model and its settings record disappear. **Workspace models built on it stay listed** | Chats with the workspace model reopen normally | Every message to the workspace model fails with `Model not found`, admins included, unless the custom-model fallback is on (below) | `backend/open_webui/utils/models.py:178-183`, `:210-238`; `backend/open_webui/main.py:1133-1135`, `:1179-1182` |
| **Every** provider fails at once | The server keeps serving the last list it built, so models stay listed and fail only when used. On a server that has never built a list, the list is empty, workspace models included | | Failure comes from the provider (see the connections document) | `backend/open_webui/utils/models.py:99-113`; `model-connections-openai-ollama-and-direct.md`, section 5.7 |

**The custom-model fallback switch.** With the environment variable `ENABLE_CUSTOM_MODEL_FALLBACK`
on (off in code; live value TO BE CONFIRMED), a message to a workspace model whose base model is
missing is answered by the **first** model in the admin's Selected models, provided that model is
currently in the server's list (`backend/open_webui/env.py:1033`; `backend/open_webui/main.py:1137-1147`,
`:1179-1185`). The person must be able to read both the workspace model and the replacement
(`backend/open_webui/main.py:1149-1161`). The request keeps the workspace model's parameters
(`backend/open_webui/main.py:1169-1177`); the system prompt, however, is added by the provider
connection from the record of the model actually called (`backend/open_webui/routers/openai.py:1515-1533`;
`backend/open_webui/routers/ollama.py:1136-1149`), so, read from code, the workspace model's system
prompt is not expected to accompany the fallback (to confirm in a test environment; section 14.4).
With no Selected model, or one that is unavailable, the message still fails with `Model not found`.
Which model ID the chat records for a fallback reply was not established from the code (section 14.4).

## 6. Data Model

Tier 1 does not query the database. This section explains what is stored so that admins and the
platform maintainer can be asked precise questions. The full schema belongs to the database
reference documents.

### 6.1 The `model` Table

One row per model record, workspace models and base-model settings records alike
(`backend/open_webui/models/models.py:111-124`).

| Column | Type | Meaning |
|---|---|---|
| `id` | text, primary key | The model ID (section 5.2). For a base-model settings record it equals the provider's model ID |
| `user_id` | text | The owner's user id |
| `base_model_id` | text, may be empty | The base model's ID for a workspace model; empty for a base-model settings record. Not enforced as a link, so it can name a model that no longer exists |
| `name` | text | Display name |
| `params` | JSON | Parameters and system prompt (section 6.3) |
| `meta` | JSON | Everything else the editor sets (section 6.2) |
| `is_active` | boolean, default true | The **Enabled** switch |
| `updated_at`, `created_at` | epoch seconds | Last change (any save, switch, hide or access change) and creation |

History: the table was created by the initial migration; `is_active` and an `access_control` column
were added later, and access lists then moved to the `access_grant` table and the old column was
dropped (`backend/open_webui/migrations/versions/7e5b5dc7342b_init.py:106-119`;
`backend/open_webui/migrations/versions/922e7a387820_add_group_table.py:38-46`;
`backend/open_webui/migrations/versions/f1e2d3c4b5a6_add_access_grant_table.py:62-80`, `:223`).

### 6.2 Keys Stored in `meta`

| Key | Content | Source |
|---|---|---|
| `profile_image_url` | The picture: an image data URI, an internal path or an HTTP(S) address. Left out of list responses and served by `GET /api/v1/models/model/profile/image` | `backend/open_webui/models/models.py:77`, `:86-96`; `backend/open_webui/main.py:919-920`; `backend/open_webui/routers/models.py:217-222` |
| `background_image_url` | Only `/api/v1/files/<file id>/content` is accepted | `backend/open_webui/models/models.py:78`; `backend/open_webui/utils/validate.py:59-62` |
| `description` | Text, or empty for none | `backend/open_webui/models/models.py:79` |
| `i18n` | Per-language `name`, `description` and `suggestion_prompts` | `backend/open_webui/models/models.py:80`; `src/lib/components/workspace/Models/ModelEditor.svelte:401-404` |
| `capabilities` | Ticked capabilities (section 5.4) | `backend/open_webui/models/models.py:81` |
| `knowledge` | Attached knowledge references, without extracted text | `backend/open_webui/models/models.py:33-62`, `:82`, `:98-101` |
| `tags` | List of `{"name": ...}`; blank names are dropped | `backend/open_webui/models/models.py:21-30`, `:103-108` |
| `suggestion_prompts` | List of suggestions (`title` as title and subtitle, `content`), or empty for **Default** | `src/lib/components/workspace/Models/ModelEditor.svelte:1166-1170` |
| `toolIds`, `skillIds`, `filterIds`, `defaultFilterIds`, `actionIds`, `defaultFeatureIds` | Lists of ids; a key is removed when its list is empty | `src/lib/components/workspace/Models/ModelEditor.svelte:345-391` |
| `builtinTools` | Groups switched off (`false`); absent groups count as on | `src/lib/components/workspace/Models/ModelEditor.svelte:393-399`; `src/lib/components/workspace/Models/BuiltinTools.svelte:83-90` |
| `terminalId`, `tts.voice` | Default terminal server; text-to-speech voice | `src/lib/components/workspace/Models/ModelEditor.svelte:406-424` |
| `hidden` | `true` when hidden | `src/lib/components/workspace/Models.svelte:243-250` |
| `chat_variables_schema` | Worked out from the system prompt and added to responses when a model is read | `backend/open_webui/routers/models.py:60-67`; `backend/open_webui/utils/models.py:187-191` |

Other keys are accepted and kept (`backend/open_webui/models/models.py:84`).

### 6.3 Keys Stored in `params`

`system` (the system prompt), `stop` (a list) and any parameter from section 5.3, including
`custom_params`. Empty values are removed on save, and unknown keys are kept
(`src/lib/components/workspace/Models/ModelEditor.svelte:426-436`;
`backend/open_webui/models/models.py:68-71`).

### 6.4 Access Entries

A model's access list is a set of rows in `access_grant` with resource type `model` and the model ID
as resource id. Each row names a user id, a group id or `*` (everyone) and a permission (`read` or
`write`); "Public" is the `*` read row (`src/lib/components/admin/Settings/Models.svelte:114-118`).
Saving the model or its access replaces all its rows; deleting the model removes them
(`backend/open_webui/models/access_grants.py:443-478`; `backend/open_webui/models/models.py:575-584`).
The table itself is described in `users-groups-roles-and-permissions.md`, section 6.3.

### 6.5 Settings and Personal Choices

- Site-wide model settings are rows of the `config` table (section 7.1).
- Each person's **personal default** (`models`) and **pins** (`pinnedModels`) live in the `ui` part
  of the JSON `settings` column of their `user` row (`backend/open_webui/models/users.py:129`,
  `:138-141`, `:171`; `src/lib/components/chat/ModelSelector.svelte:32-45`).
- In the browser, `sessionStorage` holds the last viewed chat's models for the next new chat in the
  same tab, and a clone in progress (`src/lib/components/chat/Chat.svelte:934-949`;
  `src/lib/components/workspace/Models.svelte:211-218`).
- Chats store the IDs of the models they used, and each reply stores the model ID it was requested
  from (`src/lib/components/chat/Messages/ResponseMessage.svelte:193-195`). Neither is updated when a
  model is deleted (section 5.24).

### 6.6 Personal Data in This Area

- Model records hold the owner's user id; access entries hold user and group ids
  (`backend/open_webui/models/models.py:117`; section 6.4).
- Workspace › Models shows owners' names and emails to everyone who can read their models, and its
  search matches names, emails and usernames (section 3.6).
- Export files contain owner and grantee ids and system prompts (section 5.20).
- Model events carry the acting person's id, name, email and role to webhooks and event functions
  (section 9).
- System prompts, descriptions and knowledge attached to a model may contain whatever their authors
  wrote, including personal or confidential information; read-only users do not receive the system
  prompt, but anyone who can read the model can use its attached files (section 3.5).

## 7. Settings and Configuration

Live values of every setting below are data held in the `config` table or the environment and are
**TO BE CONFIRMED** for production. After first boot the stored value of a persistent setting wins
over its environment variable (`../tools/ground-truth.md`, Settings).

### 7.1 Persistent Settings

| Setting | Where admins change it | Seeded from | Code default | Effect | Source |
|---|---|---|---|---|---|
| `ui.default_models` | Selected models (section 5.16) | `DEFAULT_MODELS` (comma-separated IDs) | none | Models for new chats; first one is the custom-model fallback | `backend/open_webui/config.py:1674`, `:3087` |
| `ui.default_pinned_models` | Pinned models (section 5.16) | `DEFAULT_PINNED_MODELS` (comma-separated IDs) | none | Sidebar pins for people who never changed their own | `backend/open_webui/config.py:1676`, `:3088` |
| `ui.model_order_list` | Drag order and **Save** (section 5.14) | `MODEL_ORDER_LIST` (JSON list) | empty list | Order of every model list | `backend/open_webui/config.py:1687-1693`, `:3093` |
| `models.default_metadata` | Model Defaults › Model Capabilities | `DEFAULT_MODEL_METADATA` (JSON) | empty | Default capabilities, default features, built-in tools | `backend/open_webui/config.py:1695-1701`, `:3094` |
| `models.default_params` | Model Defaults › Model Parameters | `DEFAULT_MODEL_PARAMS` (JSON) | empty | Parameters under every model's own | `backend/open_webui/config.py:1703-1709`, `:3095` |
| `ui.prompt_suggestions` | Model Defaults › Prompt Suggestions | `DEFAULT_PROMPT_SUGGESTIONS` (JSON) | none, meaning the built-in examples; an empty list means no suggestions | Suggestions for models set to **Default** | `backend/open_webui/config.py:1678-1683`, `:3091` |
| `ui.prompt_suggestions_i18n` | Prompt Suggestions with an editing language | none | empty | Per-language suggestions | `backend/open_webui/config.py:1685`, `:3092` |
| `models.base_models_cache` | Connections tab (**Cache Base Model List**) | `ENABLE_BASE_MODELS_CACHE` | off | Caches the provider list (`model-connections-openai-ollama-and-direct.md`, section 5.8) | `backend/open_webui/config.py:374`, `:2832` |
| `evaluation.arena.enable`, `evaluation.arena.models` | Settings › Admin › Evaluations | `ENABLE_EVALUATION_ARENA_MODELS`, `EVALUATION_ARENA_MODELS` | on; none | Arena models in the model list (`evaluations-feedback-and-analytics.md`) | `backend/open_webui/config.py:2054`, `:2065`, `:3120` |
| `user.permissions` | Users › Groups › Default permissions | `USER_PERMISSIONS_*` | section 3.2 | The model permission keys | `backend/open_webui/config.py:1733-1791`, `:1895`, `:1940-1998` |

The first five are read and written together by `GET` / `POST /api/v1/configs/models`, and the
suggestions by `POST /api/v1/configs/suggestions` (`backend/open_webui/routers/configs.py:62-68`,
`:734-770`, `:807-840`). Read from code: the admin page sends the order, Selected and Pinned values
it loaded when it opened along with each change, so two admins working on this page at the same time
can overwrite each other's changes (`src/lib/components/admin/Settings/Models.svelte:333-345`,
`:376-396`). The browser receives `ui.default_models`, `ui.default_pinned_models` and the
suggestions through `/api/config` (`backend/open_webui/main.py:2288-2293`, `:2392-2397`).

### 7.2 Environment-Only Settings

| Variable | Code default | Effect here | Source |
|---|---|---|---|
| `BYPASS_ADMIN_ACCESS_CONTROL` (falls back to `ENABLE_ADMIN_WORKSPACE_CONTENT_ACCESS`) | on | Admins see and manage every model (section 3.4) | `backend/open_webui/config.py:2084-2092` |
| `BYPASS_MODEL_ACCESS_CONTROL` | off | Everyone sees and may use every model (section 3.4) | `backend/open_webui/env.py:832` |
| `ENABLE_CUSTOM_MODEL_FALLBACK` | off | Section 5.24 | `backend/open_webui/env.py:1033` |
| `ENABLE_PLUGINS` | on | Filters and actions on models (section 5.5) | `backend/open_webui/env.py:1186` |
| `ENABLE_PROFILE_IMAGE_URL_FORWARDING` | on | A model picture stored as an HTTP(S) address is fetched by the browser from that address; when off, the default picture is shown instead | `backend/open_webui/env.py:970`; `backend/open_webui/routers/models.py:818-827` |
| `PROFILE_IMAGE_ALLOWED_MIME_TYPES` | PNG, JPEG, GIF, WebP | Picture types served as stored; any other type shows the default picture | `backend/open_webui/env.py:971-978`; `backend/open_webui/routers/models.py:828-843` |
| `PROFILE_IMAGE_MAX_DATA_URI_SIZE` | no limit | Larger pictures are dropped on save without a message | `backend/open_webui/env.py:980-983`; `backend/open_webui/utils/validate.py:86-91`; `backend/open_webui/models/models.py:86-96` |

Connection-level settings that decide which base models exist (connections, Prefix ID, Model IDs
allow-lists, timeouts, `MODELS_CACHE_TTL`) are in `model-connections-openai-ollama-and-direct.md`.

### 7.3 Limits Fixed in Code

| Limit | Value | Source |
|---|---|---|
| Workspace › Models page size | 30 models per page | `backend/open_webui/routers/models.py:159`; `src/lib/components/workspace/Models.svelte:925-927` |
| Model ID length | 256 characters, no whitespace | `backend/open_webui/routers/models.py:101-102`; `backend/open_webui/models/models.py:172` |
| Background image | PNG, JPEG, WebP or GIF; 5 MiB; 25 megapixels | `backend/open_webui/utils/validate.py:99-120` |
| Picture uploaded in the editor | Stored as a 250 × 250 WebP (GIF and WebP kept as uploaded) | `src/lib/components/workspace/Models/ModelEditor.svelte:637-685` |
| Workspace search text | 500 characters | `src/lib/components/workspace/Models.svelte:533` |
| Simultaneous model downloads | 3 per browser | `src/lib/components/chat/ModelSelector/Selector.svelte:472`, `:605`; `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:45` |

## 8. Cron Jobs and Background Processes

No scheduled job, background loop or Redis listener in the repository touches model records; none
of the seven start-up loops in `../tools/inventory.md` concerns models. What happens instead:

- **Saves take effect at save time** on the server. Each request to `GET /api/models` rebuilds the
  model list from the providers and the stored records, unless the base-model cache is on, and
  replaces the server's model registry, which is kept in Redis when Redis is configured
  (`backend/open_webui/main.py:897-943`; `backend/open_webui/utils/models.py:69-106`, `:445-460`).
  With the cache on, the list is also built once at start-up; a failure logs `Failed to pre-fetch
  models at startup: {e}` (`backend/open_webui/main.py:407-429`).
- **Browsers are not told about changes.** A person's browser loads the model list when the app
  starts and again when the person points at the selector button or after their own actions on the
  Workspace and admin model pages. Nothing pushes a new or changed model to other people's open
  pages (`src/routes/(app)/+layout.svelte:213-229`; `src/lib/components/chat/ModelSelector/Selector.svelte:922-938`).
  The `models:refresh` handler exists only for events from the desktop app
  (`src/routes/+layout.svelte:979`, `:1019-1032`).
- **Events are dispatched as background tasks** after each change, to event webhooks and event
  functions (section 9) (`backend/open_webui/events.py:1062-1171`).
- **Downloads run from the admin's browser.** Pulls from Ollama stream progress to the admin's tab;
  llama.cpp and LM Studio downloads are polled every 1.5 seconds from it
  (`src/lib/components/chat/ModelSelector/Selector.svelte:486-562`, `:643-681`). Behaviour when the
  tab is closed is described in `model-connections-openai-ollama-and-direct.md`, section 5.10.

## 9. Notifications and Emails

The application sends no email (`../tools/ground-truth.md`, Contacts). Model changes produce no
in-app or browser notification for anyone else: the model events below are not in the notification
list (`backend/open_webui/events.py:669-675`, `:1083-1086`). The person acting sees pop-ups (section
10).

### 9.1 Events

Each change publishes an event to every configured event webhook whose filter matches and to every
active event function (`backend/open_webui/events.py:1034-1060`, `:1103-1171`;
`events.webhooks` setting, `backend/open_webui/events.py:20`, `:838-850`). The payload names the
acting person (id, name, email, role), the subject and the data below
(`backend/open_webui/events.py:704`, `:974-1031`). Webhook messages read like `Model created
(<model id>)` (`backend/open_webui/events.py:1041-1044`).

| Event | When | Data | Source |
|---|---|---|---|
| `model.created` | A model is created | Model name | `backend/open_webui/routers/models.py:362-368`; `backend/open_webui/events.py:432-434` |
| `model.updated` | A model is saved, hidden or shown | Model name | `backend/open_webui/routers/models.py:1014-1020`; `backend/open_webui/events.py:441-443` |
| `model.enabled` / `model.disabled` | The Enabled switch is flipped | Model name | `backend/open_webui/routers/models.py:901-908`; `backend/open_webui/events.py:447-452` |
| `model.access_updated` | Access is changed through the access endpoint (Make Public, Make Private) | None | `backend/open_webui/routers/models.py:1097-1102`; `backend/open_webui/events.py:453-455` |
| `model.deleted` | A model is deleted; also once, without a model ID, for **Reset** | Model name | `backend/open_webui/routers/models.py:1143-1149`, `:1159`; `backend/open_webui/events.py:444-446` |
| `model.imported` | An import finishes | Count and IDs actually imported | `backend/open_webui/routers/models.py:657-663`; `backend/open_webui/events.py:435-437` |
| `model.synced` | The API-only sync replaces the table | Count and IDs | `backend/open_webui/routers/models.py:701-707`; `backend/open_webui/events.py:438-440` |
| `config.models.updated` | Selected, Pinned, order or Model Defaults saved | Selected and Pinned IDs, number of ordered models | `backend/open_webui/routers/configs.py:758-769`; `backend/open_webui/events.py:88-90` |
| `config.suggestions.updated` | Default prompt suggestions saved | Number of suggestions | `backend/open_webui/routers/configs.py:832-839`; `backend/open_webui/events.py:94-98` |

Which webhooks and event functions are configured is TO BE CONFIRMED; because the payload carries
names and email addresses, their destinations matter for privacy. Provider-side events from the
Manage dialog and the selector's **Delete** (`model.provider_model.created`,
`model.provider_model.deleted` and others) are described in the connections document
(`backend/open_webui/events.py:456-475`; `backend/open_webui/routers/ollama.py:831-837`).

## 10. Error, Warning and Notice Messages (Verbatim)

Interpolated values are written as `{name}` using the source's variable name. Plain-key English text
is the key itself (`src/lib/i18n/locales/en-US/translation.json` holds empty values for them);
dotted keys are quoted from that file. Backend texts reach people as red pop-ups on the page that
made the request: the create page and the model editor print the server's text
(`src/routes/(app)/workspace/models/create/+page.svelte:46-49`;
`src/lib/components/workspace/Models/ModelEditor.svelte:473`), Workspace › Models prints it for
delete, export and import (`src/lib/components/workspace/Models.svelte:188-191`, `:292-307`,
`:502-504`), and the admin page mostly replaces it with its own text (section 10.4). Read from code:
where a page prints a whole error object instead of its text, the pop-up reads `[object Object]`
(for example list loading, `src/lib/components/workspace/Models.svelte:166-169`, and server
validation refusals on the create page). Rows marked "Log" are server log lines, not user messages;
several contain user ids, which are personal data.

### 10.1 Backend Messages

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `401 Unauthorized` | Error (HTTP 401) | `backend/open_webui/routers/models.py:293-299`, `:317-322`, `:388-397`, `:448-457`, `:915-919`, `:975-979`, `:1136-1139` | Creating without **Models Access**; a non-admin creating without a base model; exporting or importing without the permission; switching, or deleting, a model without write access; a non-admin saving a workspace model with its base model removed | Ask an admin about the permission, or the owner about write access | The person's role and group permissions (section 3.2); who owns the model |
| `The model id is too long. Please make sure your model id is less than 256 characters long.` | Error (HTTP 400) | `backend/open_webui/routers/models.py:101-102`, `:301-305` | Creating a model whose ID is longer than 256 characters | Shorten the ID | None |
| `Uh-oh! This model id is already registered. Please choose another model id string.` | Error (HTTP 401) | `backend/open_webui/routers/models.py:310-315`, `:324-337` | Any model record already uses the ID (including ones the person cannot see), or, for a non-admin, the ID is a provider model's ID or an Ollama model name without its tag | Choose a different ID | Section 5.2, checks 12 and 14 |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 403, 401 or 400) | `backend/open_webui/routers/models.py:146-149`, `:404-406`, `:758-762`, `:958-961`, `:1047-1051`, `:1079-1082` | Saving or importing with a knowledge file the person cannot read (403); exporting a list that includes models the person may not write (403); opening a model without read access (401); saving or re-sharing without write access (400); a non-admin changing access on a base model with no record (403) | Remove the file, or ask its owner to share it; ask the model owner for access | Who owns the model and the file; the person's grants |
| `Background image is not accessible.` | Error (HTTP 403) | `backend/open_webui/routers/models.py:105-113` | The background image file is missing or the person cannot read it | Upload the image again | Whether the file was deleted |
| `Background image must be at most 5 MiB.` | Error (HTTP 400) | `backend/open_webui/utils/validate.py:105-106` via `backend/open_webui/routers/models.py:114-120`; import `:609-613` | The background image (or the embedded image in an import file) is larger than 5 MiB | Use a smaller image | None |
| `Background image must be PNG, JPEG, WebP, or GIF.` | Error (HTTP 400) | `backend/open_webui/utils/validate.py:108-111` | The stored file is another image format | Use one of the four formats | None |
| `Background image must be at most 25 megapixels.` | Error (HTTP 400) | `backend/open_webui/utils/validate.py:112-113` | Width × height exceeds 25,000,000 pixels | Use a smaller image | None |
| `Invalid background image.` | Error (HTTP 400) | `backend/open_webui/utils/validate.py:114-119` | The file cannot be read as an image | Use another file | None |
| `Could not validate background image.` | Error (HTTP 500) | `backend/open_webui/routers/models.py:121-123` | The image's recorded type could not be corrected | Try again | Escalate with the time |
| `Invalid background image URL: must reference an internal file.` | Error (HTTP 422 on save; 400 on import) | `backend/open_webui/utils/validate.py:59-62`; `backend/open_webui/models/models.py:86-95` | A background image address other than an uploaded file, normally only from the API or an import file | Upload the image in the editor | The import file's `background_image_url` |
| `Invalid background image data URI.` | Error (HTTP 400) | `backend/open_webui/routers/models.py:614-618` | An import file's embedded image does not match its declared type | Re-export the model | None |
| `Could not export background for model {model.id}.` | Error (HTTP 400) | `backend/open_webui/routers/models.py:410-427` | Export: a model's background image file is missing or invalid | Remove or replace the model's background image, then export again | Which model ID is named |
| `Could not import model {model_id}.` | Error (HTTP 500) | `backend/open_webui/routers/models.py:640-646` | Import: the model could not be written | Entries before it were imported; check the list | Escalate with the time and the file |
| `Invalid JSON format` | Error (HTTP 400) | `backend/open_webui/routers/models.py:665-666` | Import body not a list (normally refused earlier as a validation error) | Use an exported file | None |
| `{error}` or `{e}` (unexpected import error text) | Error (HTTP 400 or 500) | `backend/open_webui/routers/models.py:667-673` | Any other failure during import, for example an invalid entry | Check the file | Server log has the exception |
| `Something went wrong :/` | Error (HTTP 401) | `backend/open_webui/routers/models.py:355-360`; `backend/open_webui/constants.py:16-18` | The new model could not be written | Try again | Log line `Failed to insert a new model: {e}` |
| `We could not find what you're looking for :/` | Error (HTTP 404 for opening; 401 for switching, saving and deleting) | `backend/open_webui/routers/models.py:763-767`, `:920-924`, `:941-945`, `:1119-1123` | The model no longer exists (deleted by someone else, or the page is stale) | Reload the list | Whether and when it was deleted (section 5.12) |
| `[ERROR: Error updating function]` | Error (HTTP 400) | `backend/open_webui/routers/models.py:910-914` | The Enabled switch could not be saved (the text says "function" although a model is meant) | Try again | Escalate with the time |
| `[ERROR: Error creating model entry]` | Error (HTTP 500) | `backend/open_webui/routers/models.py:1062-1066` | An admin changed access on a base model and its record could not be created | Try again | Escalate with the time |
| `Model not found` | Error (HTTP 400 when sending a chat) | `backend/open_webui/main.py:1128-1129`, `:1149-1161`, `:1180-1182`; `backend/open_webui/utils/models.py:480`, `:491`, `:515`, `:521` | The model is not in the server's current list (deleted, disabled, provider gone); the person lacks read access to it or to its base model; or a workspace model's base model is missing and no fallback applies | Choose another model; ask the owner or an admin | If colleagues and admins get it too, it is availability, not access. Full detail in `users-groups-roles-and-permissions.md`, sections 3.7 and 10.1 |

### 10.2 Model Editor (Create and Edit Pages)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Model ID is required.` | Error | `src/lib/components/workspace/Models/ModelEditor.svelte:290-295` | Save with an empty ID (for example a name in non-Latin script) | Type an ID | Section 5.2 |
| `Model ID cannot contain whitespace.` | Error | `src/lib/components/workspace/Models/ModelEditor.svelte:297-302` | The ID contains a space | Remove spaces (use hyphens) | None |
| `Model Name is required.` | Error | `src/lib/components/workspace/Models/ModelEditor.svelte:304-309` | Save with an empty name | Type a name | None |
| `Base Model is required.` | Error | `src/lib/components/workspace/Models/ModelEditor.svelte:311-316` | Save a workspace model without a base model | Choose a base model; if none is offered, see section 11.1 | Which base models the person can see |
| `Please wait until all files are uploaded.` | Error | `src/lib/components/workspace/Models/ModelEditor.svelte:318-323` | A knowledge upload is still running | Wait, then save | None |
| `Failed to upload background image.` | Error | `src/lib/components/workspace/Models/ModelEditor.svelte:442-447` | The background file upload returned nothing | Try again, or skip the background | `files-uploads-and-storage.md` |
| `Failed to save model` | Error | `src/lib/components/workspace/Models/ModelEditor.svelte:448-449`, `:473` | The save did not succeed (on the admin base-model page this replaces the server's reason, and appears twice) | Try again; report if repeated | Ask an admin to retry and note the time |
| `{error}` (server text) | Error | `src/lib/components/workspace/Models/ModelEditor.svelte:452-473` | Any server refusal on save (section 10.1) | Depends on the text | Section 10.1 |
| `Error: A model with the ID '{modelId}' already exists. Please select a different ID to proceed.` | Error | `src/routes/(app)/workspace/models/create/+page.svelte:16-24` | The ID is already in the person's model list | Choose another ID | None |
| `Error: Model ID cannot be empty. Please enter a valid ID to proceed.` | Error | `src/routes/(app)/workspace/models/create/+page.svelte:26-29` | Empty ID reaching the create page (the editor's own check normally fires first) | Type an ID | None |
| `Model created successfully!` | Success | `src/routes/(app)/workspace/models/create/+page.svelte:51-62` | The model was created | None | None |
| `Model updated successfully` | Success | `src/routes/(app)/workspace/models/edit/+page.svelte:52`; `src/lib/components/admin/Settings/Models.svelte:489-490`, `:506-507` | The model was saved | None | None |
| `You do not have permission to edit this model` | Error | `src/routes/(app)/workspace/models/edit/+page.svelte:30-33` | Opening the edit page without write access | Ask the owner for write access, or clone it (clone needs write access too) | Section 3.1 |
| `Background image must be PNG, JPEG, WebP, or GIF.` | Error | `src/lib/components/workspace/Models/ModelEditor.svelte:911-919` | Choosing another file type as background | Use one of the four formats | None |
| `Background image must be at most 5 MiB.` | Error | `src/lib/components/workspace/Models/ModelEditor.svelte:920-921` | Choosing a file over 5 MiB | Use a smaller file | None |
| `Background image must be at most 25 megapixels.` | Error | `src/lib/components/workspace/Models/ModelEditor.svelte:925-929` | Choosing an image over 25 megapixels | Use a smaller image | None |
| `Invalid background image.` | Error | `src/lib/components/workspace/Models/ModelEditor.svelte:933-939` | The chosen file could not be decoded | Use another file | None |
| `PNG, JPEG, WebP, or GIF. Up to 5 MiB and 25 megapixels.` | Notice | `src/lib/components/workspace/Models/ModelEditor.svelte:952-954` | Help line under Background Image | None | None |
| `{key} has conflicting duplicate definitions` | Warning (English only) | `src/lib/components/workspace/Models/ModelEditor.svelte:178-188` | The system prompt defines the same chat variable twice differently | Make the definitions match | None |
| `{key} uses metadata, but User Variables are configured by each user` | Warning (English only) | `src/lib/components/workspace/Models/ModelEditor.svelte:197-199` | A user variable has a type or options, which are ignored | Remove the definition after the `\|` | None |
| `{key} must be lowercase snake case` | Warning (English only) | `src/lib/components/workspace/Models/ModelEditor.svelte:201-206`, `:216-220` | A variable name is not lower case letters, digits and underscores starting with a letter | Rename the variable | None |
| `{key} select needs options=[...]` | Warning (English only) | `src/lib/components/workspace/Models/ModelEditor.svelte:208-213` | A select-type chat variable has no options | Add options | None |
| `You do not have permission to upload files.` | Error | `src/lib/components/workspace/Models/Knowledge.svelte:38-42` | Uploading knowledge without file upload permission | Ask an admin | `chat.file_upload` |
| `You cannot upload an empty file.` | Error | `src/lib/components/workspace/Models/Knowledge.svelte:59-62` | A zero-byte file | Choose another file | None |
| `File size should not exceed {maxSize} MB.` | Error | `src/lib/components/workspace/Models/Knowledge.svelte:121-134` | The file is over the site's upload limit | Use a smaller file | Upload limit (`files-uploads-and-storage.md`) |
| `Unsupported file type.` | Error | `src/lib/components/workspace/Models/Knowledge.svelte:137-141` | An image chosen as knowledge | Attach documents, not images | None |
| `File not found.` | Error | `src/lib/components/workspace/Models/Knowledge.svelte:160-166` | The file picker returned nothing | Try again | None |
| `{uploadedFile.error}` | Warning | `src/lib/components/workspace/Models/Knowledge.svelte:88-91` | The file uploaded but its processing reported a problem | Check the file | `rag-retrieval-embeddings-and-vector-stores.md` |
| `{e}` | Error | `src/lib/components/workspace/Models/Knowledge.svelte:104-107` | The upload failed | Try again | `files-uploads-and-storage.md` |
| `To attach knowledge base here, add them to the "Knowledge" workspace first.` | Notice | `src/lib/components/workspace/Models/Knowledge.svelte:298-300` | Help line under Knowledge | None | None |
| `No knowledge found` | Notice | `src/lib/components/workspace/Models/Knowledge/KnowledgeSelector.svelte:139-142` | Nothing matches the search, or the person has no notes, knowledge bases or files | None | Knowledge access |
| `To select toolkits here, add them to the "Tools" workspace or enable a tool server first.` | Notice | `src/lib/components/workspace/Models/ToolsSelector.svelte:95-99` | Help line under Tools | None | None |
| `To select skills here, add them to the "Skills" workspace first.` | Notice | `src/lib/components/workspace/Models/SkillsSelector.svelte:97-99` | Help line under Skills | None | None |
| `To select filters here, add them to the "Functions" workspace first.` | Notice | `src/lib/components/workspace/Models/FiltersSelector.svelte:113-115` | Help line under Filters | None | None |
| `To select default filters here, enable toggleable filters for this model first.` | Notice | `src/lib/components/workspace/Models/DefaultFiltersSelector.svelte:102-104` | Help line under Default Filters | None | None |
| `To select actions here, add them to the "Functions" workspace first.` | Notice | `src/lib/components/workspace/Models/ActionsSelector.svelte:105-107` | Help line under Actions | None | None |
| `No tools found`, `No skills found`, `No filters found`, `No actions found` | Notice | `src/lib/components/workspace/Models/ToolsSelector.svelte:41`; `src/lib/components/workspace/Models/SkillsSelector.svelte:41`; `src/lib/components/workspace/Models/FiltersSelector.svelte:49`; `src/lib/components/workspace/Models/DefaultFiltersSelector.svelte:43`; `src/lib/components/workspace/Models/ActionsSelector.svelte:49` | Nothing matches the search in a picker | None | None |
| `Invalid JSON file` | Error | `src/lib/components/workspace/Models/PromptSuggestions.svelte:72-102` | Importing prompt suggestions from a file that is not a list of suggestions | Use a file exported from this screen | None |
| `No suggestion prompts` | Notice | `src/lib/components/workspace/Models/PromptSuggestions.svelte:224-227` | A Custom suggestion list is empty | None | None |

Messages from the **Access** panel are listed in `users-groups-roles-and-permissions.md`, section 10.4.

### 10.3 Workspace › Models List

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{error}` | Error | `src/lib/components/workspace/Models.svelte:158-180` | Loading the list or its tags failed (may print as `[object Object]`) | Reload | Session state; server availability |
| `Deleted {name}` | Success | `src/lib/components/workspace/Models.svelte:187-198` | A model was deleted; `{name}` is the model ID | None | None |
| `{e}` | Error | `src/lib/components/workspace/Models.svelte:188-191` | Delete refused (for example `401 Unauthorized`) | Ask the owner | Section 10.1 |
| `Confirm your action` / `This action cannot be undone. Do you wish to continue?` | Notice (confirmation) | `src/lib/components/common/ConfirmDialog.svelte:130-154` via `src/lib/components/workspace/Models.svelte:465-470` | **Delete** in a row's menu | Confirm or cancel | Shift + trash skips this (section 5.12) |
| `Redirecting you to Open WebUI Community` | Success | `src/lib/components/workspace/Models.svelte:221-241` | **Share** to the community site (community sharing on) | None | Whether community sharing is allowed (TO BE CONFIRMED) |
| `Model {name} is now {status}` | Success | `src/lib/components/workspace/Models.svelte:252-262` | Hide or show; `{name}` is the model ID, `{status}` is `hidden` or `visible` | None | None |
| `Copied link to clipboard` / `Failed to copy link` | Success / Error | `src/lib/components/workspace/Models.svelte:275-284`; also `src/lib/components/admin/Settings/Models.svelte:606-615`, `src/lib/components/chat/ModelSelector/ModelItem.svelte:38-47` | **Copy Link**; the failure means the browser refused clipboard access | Copy the address manually | None |
| `{error?.detail ?? error}` | Error | `src/lib/components/workspace/Models.svelte:286-313` | Export refused, for example `401 Unauthorized`, `You do not have permission to access this resource. Please contact your administrator for assistance.` or `Could not export background for model {model.id}.` | Depends on the text | Section 10.1 |
| `All models are now visible` / `All models are now hidden` | Success | `src/lib/components/workspace/Models.svelte:377-415`; `src/lib/components/admin/Settings/Models.svelte:215-251` | **Show All** / **Hide All** finished | None | In Workspace › Models, read-only models in the selection make the action stop early without this message (read from code) |
| `Invalid JSON file` | Error | `src/lib/components/workspace/Models.svelte:483-496` | **Import JSON** with a file that is not JSON or not a list | Use an exported file | None |
| `{error?.detail ?? error}` | Error | `src/lib/components/workspace/Models.svelte:497-505` | Import refused (section 10.1) | Depends on the text | Section 5.20 |
| `Read Only` | Notice (badge) | `src/lib/components/workspace/Models.svelte:772-774` | The person can read but not write this model | None | Section 3.1 |
| `No description` | Notice | `src/lib/components/workspace/Models.svelte:778-794` | The model has no description (the base model ID is shown when there is one) | None | None |
| `Deleted User` | Notice | `src/lib/components/workspace/Models.svelte:798-812` | The model's owner account no longer exists | None | Ownership after offboarding (section 14.3) |
| `No models found` / `Try adjusting your search or filter to find what you are looking for.` | Notice | `src/lib/components/workspace/Models.svelte:928-936`; `src/lib/components/admin/Settings/Models.svelte:1245-1256` | No model matches, or the person can read no workspace models | Clear the search and filters | Section 11.1 |
| `Discover a model` / `Discover, download, and explore model presets` | Notice | `src/lib/components/workspace/Models.svelte:945-951` | Community sharing is on | None | None |

### 10.4 Settings › Admin › Models and Model Defaults

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Reset All Models` / `This will delete all models including custom models and cannot be undone.` | Warning (confirmation) | `src/lib/components/admin/Settings/Models.svelte:709-720` | **Actions › Reset** | Cancel unless every record is meant to go | Section 5.18 |
| `All models deleted successfully` | Success | `src/lib/components/admin/Settings/Models.svelte:714-718` | Reset finished | None | Section 5.18 |
| `Models imported successfully` | Success | `src/lib/components/admin/Settings/Models.svelte:752-756` | Import accepted (skipped entries are not reported) | Check the list | Server log for `import_models` lines |
| `Failed to import models` | Error | `src/lib/components/admin/Settings/Models.svelte:757-759` | The server answered without success | Try again | Server log |
| `{e?.detail}` or `Invalid JSON file` | Error | `src/lib/components/admin/Settings/Models.svelte:760-763` | The file is not JSON, or the server refused it (a refusal whose detail is a list prints as `[object Object]`) | Use an exported file | Section 10.1 |
| `Model order saved successfully` | Success | `src/lib/components/admin/Settings/Models.svelte:347-351` | **Save** after reordering | None | None |
| `{error}` | Error | `src/lib/components/admin/Settings/Models.svelte:342-345`, `:393-396` | Saving the order, Selected or Pinned models failed | Try again | None |
| `Model added to selected models` / `Model removed from selected models` | Success | `src/lib/components/admin/Settings/Models.svelte:407-420` | Selected model toggled | None | Section 5.16 |
| `Model added to pinned models` / `Model removed from pinned models` | Success | `src/lib/components/admin/Settings/Models.svelte:422-435` | Pinned model toggled | None | Section 5.16 |
| `Model {name} is now hidden` / `Model {name} is now visible` | Success | `src/lib/components/admin/Settings/Models.svelte:540-567` | Hide or show; `{name}` is the model ID | None | None |
| `Model is now public` / `Model is now private` | Success | `src/lib/components/admin/Settings/Models.svelte:569-604` | **Make Public** / **Make Private** (private removes every access entry) | None | Section 5.10 |
| `Failed to save model` | Error | `src/lib/components/admin/Settings/Models.svelte:1286-1291` | Saving the base-model editor failed; the server's reason is not shown | Try again | Note the time; the server log may show the cause |
| `{error?.detail ?? error}` | Error | `src/lib/components/admin/Settings/Models.svelte:253-260`, `:649-654` | Export failed | Depends on the text | Section 10.1 |
| `{error}` | Error | `src/lib/components/admin/Settings/Models.svelte:508`, `:1293` | Reloading the list after a save failed | Reopen the page | None |
| `Drag to reorder` / `Clear filters to reorder` | Notice (tooltip) | `src/lib/components/admin/Settings/Models.svelte:980-991` | Pointing at a row's drag handle | Clear search and filters to reorder | None |
| `Models configuration saved successfully` | Success | `src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:129-145` | Model Defaults saved | None | None |
| `Failed to save models configuration` | Error | `src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:146-149` | Model Defaults not saved (preceded by the error text) | Try again | None |
| `{error}` | Error | `src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:118-127` | The server refused the defaults | Depends on the text | None |

### 10.5 Chat Model Selector and Sidebar

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Select a model` | Notice | `src/lib/components/chat/ModelSelector.svelte:67-70`; `src/lib/components/chat/ModelSelector/Selector.svelte:65`, `:192-196` | No model selected, or the selected one is no longer available | Choose a model | Sections 5.22 and 5.24 |
| `Choose a model before saving...` | Error | `src/lib/components/chat/ModelSelector.svelte:26-31` | **Set as default** with an empty selection | Choose a model first | None |
| `Default model updated` | Success | `src/lib/components/chat/ModelSelector.svelte:32-35` | **Set as default** (shown even when the server discards it, section 3.7) | None | `settings.interface` permission |
| `No models available` / `Connect to an AI provider to start chatting` | Notice | `src/lib/components/chat/ModelSelector/Selector.svelte:1046-1069` | An admin's model list is empty | Check connections (**Manage Connections**) | `model-connections-openai-ollama-and-direct.md` |
| `No results found` | Notice | `src/lib/components/chat/ModelSelector/Selector.svelte:1070-1077` | Nothing matches the search or filter, or a non-admin's list is empty | Clear the search and the filter menu | Section 11.1 |
| `Model '{modelTag}' is already in queue for downloading.` | Error | `src/lib/components/chat/ModelSelector/Selector.svelte:464-470`, `:597-603` | An admin starts the same download twice | Wait | None |
| `Maximum of 3 models can be downloaded simultaneously. Please try again later.` | Error | `src/lib/components/chat/ModelSelector/Selector.svelte:472-476`, `:605-609` | A fourth download in the same browser | Wait | None |
| `Model '{modelName}' has been successfully downloaded.` | Success | `src/lib/components/chat/ModelSelector/Selector.svelte:564-569`, `:693-698` | A download finished | None | None |
| `Download canceled` | Error | `src/lib/components/chat/ModelSelector/Selector.svelte:577-579` | An Ollama pull ended without success | Retry | Provider |
| `{model} download has been canceled` | Success | `src/lib/components/chat/ModelSelector/Selector.svelte:764-789` | The admin cancelled a download | None | None |
| `{data.status}` | Success | `src/lib/components/chat/ModelSelector/Selector.svelte:538-540` | Each status line Ollama sends during a pull | None | None |
| `{error}`, `Download failed` or `Server connection failed` | Error | `src/lib/components/chat/ModelSelector/Selector.svelte:479-483`, `:552-560`, `:678-680`, `:706-709`; `src/lib/apis/openai/index.ts:3-14` | A download failed; the provider's text is shown when there is one | Retry; report if repeated | Provider and connection |
| `Pull "{searchValue}" from Ollama.com`, `Download "{searchValue}" from {provider}`, `Download "{searchValue}"`, `Downloading "{searchValue}"`, `Downloading "{name}"` | Notice | `src/lib/components/chat/ModelSelector/Selector.svelte:323`, `:338`, `:1136`, `:1194`, `:1220` | Admin download rows | None | Section 5.19 |
| `Model unloaded successfully` | Success | `src/lib/components/chat/ModelSelector/Selector.svelte:796-804` | **Eject** worked | None | None |
| `Error unloading model: {error}` | Error | `src/lib/components/chat/ModelSelector/Selector.svelte:791-794` | **Eject** failed | Retry | Provider |
| `Delete Model` / `Are you sure you want to delete **{modelName}**?` | Warning (confirmation) | `src/lib/components/chat/ModelSelector/Selector.svelte:893-902` | **Delete** in a row's menu | Cancel unless intended: for a base model this deletes it from the Ollama server | Section 5.12 |
| `Error deleting model: {error}` | Error | `src/lib/components/chat/ModelSelector/Selector.svelte:820-835` | The deletion failed, for example `Model '{model}' was not found` or `The Ollama API is disabled. Please enable it to use this feature.` | None | `backend/open_webui/routers/ollama.py:807-818`; `backend/open_webui/constants.py:89`, `:103` |
| `Model {modelName} deleted successfully` | Success | `src/lib/components/chat/ModelSelector/Selector.svelte:837-841` | The deletion worked | None | Section 5.12 |
| `Loaded` / `Unloads {FROM_NOW}` | Notice (tooltip) | `src/lib/components/chat/ModelSelector/ModelItem.svelte:167-176` | A local model is in memory | None | None |

### 10.6 Manage Models Dialog

The dialog's behaviour is described in `model-connections-openai-ollama-and-direct.md`, sections
5.10 and 5.11.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `No inference engine with management support found` | Notice | `src/lib/components/admin/Settings/Models/ManageModelsModal.svelte:101-106` | No Ollama server and no llama.cpp or LM Studio connection | None | Connections |
| `Failed to fetch models` | Error (in the dialog) | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:1143-1145` | The Ollama server's model list could not be read | Check the server | Connections |
| `Checking for model updates...` | Info (English only) | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:78-80` | **Update All Models** started | Wait | None |
| `Model update cancelled` / `All models are up to date` | Info / Success (English only) | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:153-157` | Update finished or was cancelled; individual failures are not reported | None | None |
| `Model '{modelTag}' is already in queue for downloading.` | Error | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:165-171` | Same pull started twice | Wait | None |
| `Maximum of 3 models can be downloaded simultaneously. Please try again later.` | Error | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:173-178` | Fourth pull in the same browser | Wait | None |
| `Model '{modelName}' has been successfully downloaded.` | Success | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:270-275` | Pull finished | None | None |
| `Download canceled` | Error | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:283-285` | Pull ended without success | Retry | None |
| `{model} download has been canceled` | Success | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:480-494` | Pull cancelled | None | None |
| `Deleted {deleteModelTag}` | Success | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:449-456` | Model deleted from the Ollama server | None | Records built on it now fail (section 5.24) |
| `{data.status}` | Success | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:403-410`, `:547-554` | Ollama status lines while creating or uploading | None | None |
| `{error}` / `{err}` | Error | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:90-96`, `:181-187`, `:253-261`, `:311-323`, `:366-367`, `:424-427`, `:450-452`, `:466-469`, `:501-506`, `:516-519`, `:569-572`, `:593-596` | Any Ollama or server error in the dialog | Depends on the text | Connections |
| `To access the available model names for downloading,` `click here.` | Notice | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:718-724` | Help line under the pull box (links to the Ollama library) | None | None |
| `Updating "{modelId}"` | Notice | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:728-731` | Update in progress | None | None |
| `To access the GGUF models available for downloading,` | Notice | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:1095-1101` | Help line under the upload box | None | None |
| `Model download started` | Success | `src/lib/components/admin/Settings/Models/Manage/ManageProviderModels.svelte:141-146` | llama.cpp or LM Studio download requested | None | None |
| `Model loaded successfully` / `Model unloaded successfully` | Success | `src/lib/components/admin/Settings/Models/Manage/ManageProviderModels.svelte:149-167` | Load or unload worked | None | None |
| `Delete Model` / `This will delete the cached model and cannot be undone.` | Warning (confirmation) | `src/lib/components/admin/Settings/Models/Manage/ManageProviderModels.svelte:185-190` | Delete on a llama.cpp model | Cancel unless intended | None |
| `Model deleted successfully` | Success | `src/lib/components/admin/Settings/Models/Manage/ManageProviderModels.svelte:172-175` | Deletion worked | None | None |
| `{error}` or `Server connection failed` | Error | `src/lib/components/admin/Settings/Models/Manage/ManageProviderModels.svelte:103-107`, `:126-131`, `:157-162`; `src/lib/apis/openai/index.ts:3-14` | A provider action failed | Depends on the text | Connections |
| `No models found` | Notice | `src/lib/components/admin/Settings/Models/Manage/ManageProviderModels.svelte:226-228` | The provider lists no models | None | None |

### 10.7 Server Log Lines

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `knowledge file access denied: user {user.id} cannot read file {file_id}` | Log (warning) | `backend/open_webui/routers/models.py:140-149` | Explains a save or import refusal for a knowledge file | n/a | Contains a user id |
| `import_models: user {user.id} skipped model {model_id} (knowledge file access denied)` | Log (warning) | `backend/open_webui/routers/models.py:505-511` | Import skipped an entry | n/a | The same pattern ends `(no write access)` (`:521-526`), `(cannot clear base model)` (`:533-538`), `(no base model set)` (`:568-573`) or `(id belongs to a base model)` (`:589-594`) |
| `Could not clean up failed model background upload` | Log (exception) | `backend/open_webui/routers/models.py:647-654` | An import failed and its uploaded background could not be removed | n/a | A stray file may remain |
| `Failed to insert a new model: {e}` | Log (exception) | `backend/open_webui/models/models.py:226-228` | Behind `Something went wrong :/` on create | n/a | Escalate with the time |
| `Skipping model {model.id} during get_all_models due to error: {exc}` | Log (error) | `backend/open_webui/models/models.py:238-241` | A damaged record is left out of the admin and model lists | n/a | The model ID named |
| `Failed to update the model by id {id}: {e}` | Log (exception) | `backend/open_webui/models/models.py:557-559` | A save failed | n/a | Escalate with the time |
| `Failed to update the model updated_at by id {id}: {e}` | Log (exception) | `backend/open_webui/models/models.py:571-573` | An access change could not touch the record | n/a | None |
| `Error syncing models for user {user_id}: {e}` | Log (exception) | `backend/open_webui/models/models.py:647-649` | The API-only sync failed | n/a | Contains a user id |
| `Action not found: {action_id}` / `Failed to load action module: {action_id}` | Log (info) | `backend/open_webui/utils/models.py:405-415` | A model refers to an action function that is missing or broken | n/a | Explains a missing message button |
| `Filter not found: {filter_id}` / `Failed to load filter module: {filter_id}` | Log (info) | `backend/open_webui/utils/models.py:425-435` | A model refers to a filter function that is missing or broken | n/a | Explains a missing filter toggle |
| `Failed to update Redis model cache, using in-process cache: {e}` | Log (warning) | `backend/open_webui/utils/models.py:453-458` | The shared model registry could not be written | n/a | With several server processes, lists can differ per process |
| `Access denied to tool {tool_id} for user {user.id}` | Log (warning) | `backend/open_webui/utils/tools.py:283-299` | A model's tool was skipped for a person without access | n/a | Section 3.6 |
| `Failed to pre-fetch models at startup: {e}` | Log (warning) | `backend/open_webui/main.py:407-429` | Start-up list build failed with the cache on | n/a | Connections |
| `Model access denied: user_id={user_id} model_id={model_id} reason=model_read_denied` and related reasons | Log (warning) | `backend/open_webui/utils/models.py:475-515` | A chat was refused for access reasons | n/a | `users-groups-roles-and-permissions.md`, section 10.1 |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it never creates, edits, shares, hides, switches, deletes, imports or exports a
model and never changes settings or permissions. "Ask an admin to confirm" below means asking someone
with the `admin` role to look without changing anything, and to make any change through the normal
admin process. Model owners can be asked the same about their own models. Support contacts and
escalation routes are TO BE CONFIRMED (`../tools/ground-truth.md`, Contacts). Export files contain
user ids and system prompts (section 5.20); do not ask people to send them through support channels
unless the escalation route says so.

### 11.1 "I can't find the model I'm supposed to use"

**Symptom.** The model is not in the chat selector (searching for it finds nothing), or not in
Workspace › Models.

**Likely causes, in order.**
1. It has not been shared with the person. A provider model is admin-only until an admin gives it a
   record with a read entry; a workspace model is private to its owner until shared with the person,
   one of their groups or everyone (section 3.3; `backend/open_webui/utils/models.py:524-578`).
2. It is **hidden**: hidden models never appear in the selector, even when searched for, though a
   link still opens them (section 5.9; `src/lib/components/chat/ModelSelector/Selector.svelte:310`).
3. It is **disabled** (section 5.11).
4. The person's page has not reloaded its model list since the model was shared or switched on
   (section 8).
5. The selector's filter menu is still set to a tag or connection type; reopening the selector does
   not reset it (`src/lib/components/chat/ModelSelector/Selector.svelte:137-154`, `:200-202`).
6. Its base model or connection is not currently offered (`model-connections-openai-ollama-and-direct.md`,
   section 5.9).
7. They are looking in Workspace › Models for a provider model: that page lists workspace models only
   (`backend/open_webui/models/models.py:356-357`).

**Diagnostic steps.** Ask for the model's exact name, or the link they were given (`/?model=<id>`).
Ask them to reload the page, set the selector's filter menu to **All** and search again. Ask whether
a colleague in the same team sees it. Ask an admin to confirm, in Settings › Admin › Models, whether
the model is listed, its **Enabled** switch, whether it is faded (hidden), and its **Public** /
**Shared** / **Private** label; and to use **Preview Access** for the person
(`users-groups-roles-and-permissions.md`, section 5.8).

**Resolution.** Explain which case applies. Access is granted by the model's owner or an admin; tier 1
cannot share a model.

**Escalation.** Model name or ID, the person's email, the groups they expect to have access through,
whether colleagues see it, and a screenshot of the selector with the search typed.

### 11.2 "The model is in the list but every message fails with 'Model not found'"

**Symptom.** The model can be selected, but sending shows `Model not found` as a pop-up and in the
reply.

**Likely causes, in order.**
1. **Availability**: the workspace model's base model is no longer offered by any connection.
   Workspace models stay listed without their base model, and everyone, admins included, gets this
   refusal unless the custom-model fallback is on (section 5.24;
   `backend/open_webui/main.py:1133-1135`, `:1179-1182`).
2. **Access**: the person can read the workspace model but not its base model
   (`users-groups-roles-and-permissions.md`, section 11.10).
3. The model was deleted, disabled or unshared after the page loaded
   (`backend/open_webui/main.py:1128-1129`).

**Diagnostic steps.** Ask for the model name and the time. Ask the person to reload and try again,
then to try the same model in a new chat. Ask whether colleagues get the same message with this
model: if admins get it too, cause 1 is likely. Ask an admin to confirm whether the model's base
model still appears in Settings › Admin › Models (the base model ID is the description line in
Workspace › Models when the model has no description, and is in the editor's **JSON Preview**).

**Resolution.** Suggest another model meanwhile. Fixing cause 1 needs the owner to choose a new base
model, or an admin to restore the connection or model.

**Escalation.** Model name and ID, base model ID if known, person's email, time, and whether admins
get the same refusal. An access refusal leaves a `Model access denied` server log line; an
availability refusal does not (section 10.7).

### 11.3 "I don't have Workspace › Models" or "I can't create a model"

**Symptom.** No Models section in Workspace; opening `/workspace/models` returns to the home page;
or saving a new model fails with `401 Unauthorized` or `Base Model is required.`

**Likely causes, in order.**
1. The person lacks **Models Access** (`workspace.models`, off in code)
   (`src/routes/(app)/workspace/+layout.svelte:80-83`; `backend/open_webui/routers/models.py:293-299`).
2. The permission was removed while the page was open (the server refuses with `401 Unauthorized`).
3. No base model is offered to them, so nothing can be chosen as base: the picker offers only
   provider models the person can see (section 3.1).

**Diagnostic steps.** Ask what they see under Workspace and what happens on save. Ask an admin to
confirm the person's group permissions (`users-groups-roles-and-permissions.md`, section 5.8).

**Resolution.** Explain that model creation is granted by admins through default permissions or a
group, and that a base model must also be shared with them.

**Escalation.** Person's email, the business reason, and which base model they need.

### 11.4 "It says the model ID is already registered"

**Symptom.** `Uh-oh! This model id is already registered. Please choose another model id string.`
or `Error: A model with the ID '{modelId}' already exists. Please select a different ID to proceed.`

**Likely causes, in order.**
1. A model record with that ID already exists, possibly one the person cannot see: someone else's
   private model, a disabled model, or a base-model settings record (section 5.2, check 12).
2. The ID equals a provider model's ID (or, for Ollama, the model name without its tag); non-admins
   may not use those IDs (check 14).
3. A clone kept the suggested `<id>-clone`, and a clone with that ID already exists.

**Diagnostic steps.** Ask for the ID exactly as typed and the name of the model they are creating.

**Resolution.** Advise choosing a different ID, for example by adding a course or team suffix. IDs
cannot be changed later, so a lasting choice is better (section 5.2).

**Escalation.** Only if that exact ID is needed: send the ID to an admin, who can see every record in
Settings › Admin › Models.

### 11.5 "The editor won't accept my model ID"

**Symptom.** `Model ID is required.`, `Model ID cannot contain whitespace.` or `The model id is too
long. Please make sure your model id is less than 256 characters long.`

**Likely causes, in order.**
1. The name contains only characters the ID cannot use (accented or non-Latin letters), so the ID
   came out empty (`src/lib/components/workspace/Models/ModelEditor.svelte:84-91`).
2. Spaces typed into the ID.
3. An ID over 256 characters.
4. The ID was typed by hand and then the name was changed, which regenerated it.

**Diagnostic steps.** Ask for the name and the ID shown under it.

**Resolution.** Guide them to type a short ID with letters, digits and hyphens after finishing the
name.

**Escalation.** Not normally needed.

### 11.6 "I shared my model, but my colleague can't see it"

**Symptom.** The owner set the model to Public or added a person or group, but the colleague does
not see it, or sees it and gets `Model not found`.

**Likely causes, in order.**
1. The Access dialog was closed without pressing **Save & Update**; access is saved only with the
   model (section 5.10).
2. The owner lacks the sharing permission for that choice, so the server dropped it on save without a
   message: Public needs `sharing.public_models`, people and groups need `sharing.models`
   (`users-groups-roles-and-permissions.md`, section 5.17).
3. The colleague's page has not reloaded its model list (section 8).
4. The colleague cannot read the base model (section 11.2).
5. The colleague is not in the group shared with, or group sync removed them.
6. The model is hidden.

**Diagnostic steps.** Ask the owner whether they pressed **Save & Update**, then to reopen the
**Access** dialog: entries the server removed are no longer there. Ask the colleague to reload. Ask
an admin to use **Preview Access** for the colleague.

**Resolution.** Guide the owner to save after changing access; explain the permission rules.

**Escalation.** Model name and ID, owner and colleague emails, the group intended, screenshots of the
Access dialog.

### 11.7 "The model ignores its knowledge base when other people use it"

**Symptom.** The model answers from its attached documents for its owner, but not for colleagues.

**Likely causes, in order.**
1. The attached **knowledge base** is not shared with the colleague; sharing the model does not share
   it (section 3.6; `backend/open_webui/retrieval/utils.py:1566-1580`;
   `backend/open_webui/tools/builtin.py:2199-2237`). Files uploaded directly into the model's
   Knowledge section do not need separate sharing.
2. In native function calling, attached knowledge is reached through built-in knowledge tools, so it
   is not used when the model's **Builtin Tools** capability is off or its **Knowledge Base** group is
   unticked (`backend/open_webui/utils/tools.py:603-630`; `backend/open_webui/utils/middleware.py:2809-2813`).
3. The base model does not use tools well in native mode (provider behaviour, outside the
   repository); the model's **Function Calling** parameter can be set to Legacy by its owner.
4. The knowledge base was deleted or emptied.

**Diagnostic steps.** Ask for the model name, the knowledge base name and a sample question. Ask the
colleague whether they can open that knowledge base under Workspace › Knowledge, if they have that
section.

**Resolution.** Explain that the knowledge base's owner must share it with the same people.

**Escalation.** Model name, knowledge base name, both emails, a screenshot of the answer.

### 11.8 "The model's tools or skills aren't switched on for my colleagues"

**Symptom.** A model set up with tools or skills starts without them for some people.

**Likely causes, in order.**
1. The tool or skill is not shared with them, or the skill is inactive; the browser skips it and the
   server skips unreadable tools (section 3.6).
2. The tool comes from a tool server they have not signed in to (section 5.5).
3. More than one model is selected: model defaults apply only to a single selected model
   (`src/lib/components/chat/Chat.svelte:1022-1024`).
4. The chat was not new: defaults apply when a chat starts.

**Diagnostic steps.** Ask which tool or skill is missing and whether one or several models were
selected.

**Resolution.** Explain; the tool or skill owner can share it.

**Escalation.** Model, tool or skill names, emails, screenshot of the chat's tool menu.

### 11.9 "We hid the model, but people are still using it"

**Symptom.** A hidden model is still being used, through links or old chats.

**Likely causes, in order.**
1. Hiding only removes the model from the selector, the sidebar pins and new-chat defaults; links
   and existing chats keep working (section 5.9).

**Diagnostic steps.** Ask what the goal is: tidy the list, or stop use.

**Resolution.** Explain that stopping use needs the model to be disabled or its access removed, by its
owner or an admin.

**Escalation.** Model name and the intended outcome.

### 11.10 "My chat switched to another model" or "Old replies show a code instead of the model name"

**Symptom.** Reopening a chat shows a different model selected, or earlier replies are labelled with a
raw ID and the default picture.

**Likely causes, in order.**
1. The chat's model was deleted, disabled, removed by **Reset**, or the person lost access; the chat
   falls back to their default model without a message (section 5.24).
2. The chat used several models and `chat.multiple_models` is off for the person, so only the first
   is kept (section 3.7).
3. A hidden model does not cause this: existing chats keep hidden models.

**Diagnostic steps.** Ask for the chat title, the model they expected and when it last worked. Ask
whether the expected model appears in the selector.

**Resolution.** Explain that the conversation is intact and they can pick another model. If the model
should exist, escalate.

**Escalation.** Chat title, expected model name or the ID shown on old replies, person's email.

### 11.11 "A model disappeared for everyone"

**Symptom.** A model everybody used is gone from every selector.

**Likely causes, in order.**
1. It was **disabled** (section 5.11).
2. For a provider model: the provider stopped offering it or its connection failed; its settings
   record is then ignored (section 5.24).
3. It was **deleted**, or every record was removed with **Reset** (sections 5.12, 5.18).
4. It was **hidden**, if the complaint is only about the selector (section 5.9).
5. With the base-model cache on, the list is out of date
   (`model-connections-openai-ollama-and-direct.md`, section 5.8).

**Diagnostic steps.** Note when it was last seen. Ask an admin to confirm, in Settings › Admin ›
Models, whether the model is listed and whether the **Disabled** or **Hidden** view filters show it.
If event webhooks are configured, an admin can check for `model.disabled`, `model.deleted` or
`model.updated` events at that time (section 9).

**Resolution.** Escalate; tier 1 cannot restore models.

**Escalation.** Model name and ID, time last seen, number of people affected.

### 11.12 "I deleted a model by mistake. Can it be restored?"

**Symptom.** A model was deleted, possibly with Shift and the row's delete button, which does not ask
for confirmation (section 5.12).

**Likely causes, in order.**
1. Deletion is permanent; no recycle bin exists (`backend/open_webui/models/models.py:575-584`).

**Diagnostic steps.** Ask for the model name and ID, the time, and whether the owner or anyone has an
exported JSON file of it.

**Resolution.** If an export file exists, importing it recreates the model under the same ID, owned by
whoever imports it, and existing chats then find it again (section 5.20). Otherwise recovery depends
on database backups, which are TO BE CONFIRMED. Access lists and attached items must be checked after
any restore.

**Escalation.** Model ID, owner, time of deletion, whether an export exists.

### 11.13 "New chats keep starting with the wrong model" or "Set as default doesn't stick"

**Symptom.** New chats start with an unexpected model, or a default chosen with **Set as default** is
gone after reloading.

**Likely causes, in order.**
1. The person has a personal default, which takes precedence over the admin's Selected models
   (section 5.22).
2. The personal default model is no longer available or is hidden, so the admin's Selected models are
   used without a message.
3. **Set as default** showed `Default model updated` but the person lacks **Interface Settings
   Access**, so the server discarded it (section 3.7).
4. The chat was started from a folder with its own models, or right after viewing another chat in the
   same tab, which carries that chat's models over once (section 5.22).
5. A link with `?model=` was used.

**Diagnostic steps.** Ask how they start new chats (the New Chat button, a folder, a link), what model
they expect, and whether the problem survives a reload.

**Resolution.** Guide them to choose the model and press **Set as default** in an empty chat; if it
does not survive a reload, escalate cause 3.

**Escalation.** Person's email, expected model, steps taken.

### 11.14 "My pinned models changed" or "I don't see the models the admin pinned"

**Symptom.** Sidebar pins differ from colleagues' or from what the admin set.

**Likely causes, in order.**
1. The person has pinned or unpinned a model at some point; from then on their own list applies and
   admin changes no longer reach them (section 5.23).
2. A pinned model is hidden, disabled or not shared with them, so it is left out.

**Diagnostic steps.** Ask which models they expect and whether they have ever pinned or unpinned one.

**Resolution.** Guide them to pin models themselves with **Keep in Sidebar** in the selector's row
menu. No control in the model screens returns a person to following the admin's list
(`src/lib/stores/index.ts:108-113`); whether that is wanted is TO BE CONFIRMED with the platform
maintainer.

**Escalation.** Only if a pinned model should be visible but is not (section 11.1).

### 11.15 "My import didn't do anything" or "Some models weren't imported"

**Symptom.** After **Import JSON** the list reloads with no message and some or all models are
missing; or the admin page says `Models imported successfully` but some are missing.

**Likely causes, in order.**
1. Entries were skipped without a message: no base model, an ID belonging to a provider model, an
   existing ID the person may not write, knowledge files they cannot read, or an invalid ID
   (section 5.20).
2. The file is from another site and refers to knowledge, tools or base models that do not exist here.
3. An error part-way stopped the import after some entries were saved.

**Diagnostic steps.** Ask for the number of models expected and which are missing, and any pop-up
text. Ask an admin to confirm the server log lines starting `import_models:` at that time
(section 10.7).

**Resolution.** Explain the skip rules; the importer may need a base model shared or a different ID.

**Escalation.** Person's email, time of import, model IDs missing.

### 11.16 "Export fails with 'Could not export background for model …'"

**Symptom.** `Could not export background for model {model.id}.` on **Export JSON** or **Export**.

**Likely causes, in order.**
1. The named model's background image file was deleted or is no longer a valid image
   (`backend/open_webui/routers/models.py:410-427`).

**Diagnostic steps.** Note the model ID in the message.

**Resolution.** The model's owner removes or replaces its background image (**Reset** or
**Replace** under Background Image) and exports again.

**Escalation.** If the owner cannot edit it: model ID and owner.

### 11.17 "I can't add a background image to my model"

**Symptom.** One of the background messages in sections 10.1 and 10.2, or `Failed to upload
background image.`

**Likely causes, in order.**
1. The file is not PNG, JPEG, WebP or GIF, is over 5 MiB, or is over 25 megapixels
   (`backend/open_webui/utils/validate.py:99-120`).
2. The upload itself failed (`files-uploads-and-storage.md`).
3. The image is attached to a base model: base models have no background image (section 5.15).

**Diagnostic steps.** Ask for the file type, size and pixel dimensions, and the exact message.

**Resolution.** Suggest converting or resizing the image.

**Escalation.** Only if a valid file still fails: the message, file type and size.

### 11.18 "I can't edit a model that was shared with me"

**Symptom.** The row is not clickable and shows `Read Only`, or `You do not have permission to edit
this model` appears.

**Likely causes, in order.**
1. The person has a **Read** grant only (section 3.1).

**Diagnostic steps.** Ask who owns the model (the owner's name is on the row).

**Resolution.** Explain that the owner can grant **Write**. Cloning also needs write access.

**Escalation.** Not needed unless the owner has left; then send the model ID to an admin (ownership
after offboarding is TO BE CONFIRMED, section 14.3).

### 11.19 "The model selector says 'No results found' or 'No models available'"

**Symptom.** The selector is empty or the search finds nothing.

**Likely causes, in order.**
1. A search text or filter menu choice hides everything (section 5.21).
2. Nothing is shared with the person (section 11.1).
3. No provider model is available and the server has no earlier list; admins see `No models
   available` and **Manage Connections** (`backend/open_webui/utils/models.py:99-113`).

**Diagnostic steps.** Ask them to clear the search, set the filter to **All** and reload. Ask whether
colleagues see models.

**Resolution.** Guidance; escalate if colleagues are also affected.

**Escalation.** Person's email, time, whether others are affected.

### 11.20 Admin: "I configured or shared a provider model, but users still can't see it"

**Symptom.** After switching a provider model on, renaming it or making it public in Settings › Admin
› Models, users still do not see it, or a change appears to save but is gone after reloading.

**Likely causes, in order.**
1. The model has a record but no read entry: it shows **Private** (section 3.3).
2. Users' pages have not reloaded their model lists (section 8).
3. Read from code: the admin page decides between creating and updating a base model's record using
   the list it loaded when it opened. For a base model that had no record then, the first switch,
   hide or **Make Public** creates the record without refreshing that list (an edit saved in the
   base-model editor does refresh it). Later switches, hides or edits of the same model before the
   page is reloaded can then do nothing on the server, while the switch or a success pop-up suggests
   otherwise, and an edit ends with `Failed to save model`
   (`src/lib/components/admin/Settings/Models.svelte:481-538`, `:540-567`, `:569-604`, `:1286-1294`).
4. The model is hidden, or its connection no longer offers it.

**Diagnostic steps.** Ask the admin to reload the page and check the model's **Enabled** switch,
faded state and access label as stored.

**Resolution.** Reload Settings › Admin › Models after the first switch, hide or **Make Public** on a
base model that had no record, then make further changes.

**Escalation.** To the platform maintainer if the behaviour persists after reloading; send the model
ID and the steps taken.

### 11.21 Admin: "I changed Model Defaults, but a model still behaves the old way"

**Symptom.** New default capabilities, parameters or suggestions do not reach some models.

**Likely causes, in order.**
1. The model was saved in the editor and keeps its own value for every capability (section 5.4).
2. The model's own parameters override the defaults key by key (section 5.3).
3. The model's **Prompts** are set to **Custom** (section 5.1, step 13).
4. People's pages have not reloaded (section 8).

**Diagnostic steps.** Ask which model and which setting, and compare with the model's editor (an
admin can open it).

**Resolution.** The model's owner changes the model itself.

**Escalation.** Model name and the setting concerned.

### 11.22 Admin: "Saving a base model only says 'Failed to save model'"

**Symptom.** The base-model editor shows `Failed to save model` (twice) and nothing is saved.

**Likely causes, in order.**
1. The record was created earlier in this page session by a switch, hide or **Make Public**
   (section 11.20, cause 3).
2. The server refused the change; this page does not show the server's reason
   (`src/lib/components/admin/Settings/Models.svelte:481-512`).

**Diagnostic steps.** Ask the admin to reload the page and try once more.

**Resolution.** Reload and retry.

**Escalation.** To the platform maintainer with the model ID and time; the server log may hold the
reason.

## 12. Local Customisations

Checked with read-only `git diff main...uoft` (fork commits) and `git diff` (uncommitted working tree)
over every file in section 13.1, plus `backend/open_webui/utils/models.py`,
`backend/open_webui/config.py` and `src/lib/components/chat/Settings/Advanced/AdvancedParams.svelte`.

- **No file in this area's scope differs from upstream Open WebUI v0.11.4**, in the fork commits or in
  the uncommitted working tree. Model records, the editor, sharing, the admin model list, the
  selector, pins, import and export behave as upstream.
- **Fork settings that combine with model capabilities.** The fork's per-person Interface settings
  **Hide Processing Details** and **Inline Citations** (commit `aeed1832c`;
  `backend/open_webui/models/users.py:99-100`) work alongside two model capabilities: status lines
  appear only when the model's **Status Updates** capability is on and Hide Processing Details is
  off, and citation markers only when the model's **Citations** capability is on and Inline
  Citations is on (`src/lib/components/chat/Messages/ResponseMessage.svelte:197-199`;
  `src/lib/components/chat/Messages/ContentRenderer.svelte:128-130`). When status lines or
  citations are missing, either the model or the person's setting can be the cause;
  `chat-composer-and-message-display.md` covers the person's side. `ResponseMessage.svelte` also has
  uncommitted changes in the working tree, which keep the same capability condition.
- **Branding.** Models without their own picture show `favicon.png`
  (`src/lib/components/workspace/Models/ModelEditor.svelte:99-102`;
  `backend/open_webui/routers/models.py:867-873`), and the fork replaced that file with the MedIT GPT
  image (`../tools/ground-truth.md`, Fork changes). The Workspace › Models browser tab reads
  `Models / {WEBUI_NAME}`, which shows the fork's product name
  (`src/lib/components/workspace/Models.svelte:455-462`; `backend/open_webui/env.py:951`).
- The uncommitted change in `src/lib/components/chat/Chat.svelte` (tool-approval resume, after line
  2846) and in `src/lib/i18n/locales/en-US/translation.json` (Hide Processing Details description)
  do not affect anything described here.

## 13. Source File Index

### 13.1 Files in Scope

| File | What it does in this area |
|---|---|
| `backend/open_webui/routers/models.py` | Models API: workspace list, all records, base records and tags, create (ID rules), export, import (skip rules), API-only sync, read one, picture, Enabled switch, save, access change, delete, delete all |
| `backend/open_webui/models/models.py` | `model` table; `ModelMeta`, `ModelParams`, `ModelForm`; tag tidying; removal of extracted knowledge text; workspace search (owner name, email and username included); tags; switch; save; delete; delete all; sync |
| `backend/open_webui/utils/model_ids.py` | Removes a connection's Prefix ID from a model ID before the provider is called |
| `backend/open_webui/config.py` | `ENABLE_BASE_MODELS_CACHE`, `DEFAULT_MODELS`, `DEFAULT_PINNED_MODELS`, `DEFAULT_PROMPT_SUGGESTIONS`, `MODEL_ORDER_LIST`, `DEFAULT_MODEL_METADATA`, `DEFAULT_MODEL_PARAMS`, the model permission variables, `DEFAULT_ARENA_MODEL`, `BYPASS_ADMIN_ACCESS_CONTROL` and their `DEFAULT_CONFIG` entries (`:374`, `:1674-1709`, `:1733-1791`, `:1895`, `:1940-1998`, `:2054-2092`, `:2832`, `:3087-3095`) |
| `src/lib/components/workspace/Models.svelte` | Workspace › Models: search, view and tag filters, Actions (Enable, Disable, Show, Hide All), Create, Import and Export JSON, rows with owner, Read Only badge, Shift actions, switch, menu handlers (clone, share, hide, copy link, export, pin, delete) |
| `src/lib/components/workspace/Models/ModelEditor.svelte` | The model editor for workspace and base models: picture, name, ID generation, access, base model, background, description, tags, translations, system prompt and variable checks, parameters, prompts, knowledge, tools, skills, filters, actions, capabilities, features, built-in tools, terminal, voice, save |
| `src/lib/components/workspace/Models/Capabilities.svelte` | Capability ticks (File Context hidden while File Upload is off) |
| `src/lib/components/workspace/Models/DefaultFeatures.svelte` | Default Features ticks |
| `src/lib/components/workspace/Models/BuiltinTools.svelte` | Built-in tool group ticks |
| `src/lib/components/workspace/Models/Knowledge.svelte` | Knowledge section: Select Knowledge, Upload, attached items, whole-document dialog |
| `src/lib/components/workspace/Models/Knowledge/KnowledgeSelector.svelte` | Search across the person's notes, knowledge bases and knowledge files |
| `src/lib/components/workspace/Models/ToolsSelector.svelte`, `SkillsSelector.svelte`, `FiltersSelector.svelte`, `DefaultFiltersSelector.svelte`, `ActionsSelector.svelte` | Pickers for tools, active skills, filters (global ones locked on), default toggleable filters and actions |
| `src/lib/components/workspace/Models/TypeaheadSelector.svelte` | Shared search-and-pick list with **Enable all** |
| `src/lib/components/workspace/Models/PromptSuggestions.svelte` | Prompt suggestion list with import and export |
| `src/lib/components/workspace/Models/LocalizedPromptSuggestions.svelte` | Per-language prompt suggestions with **Use default** |
| `src/lib/components/workspace/Models/TerminalSelector.svelte` | Default terminal server menu |
| `src/lib/components/workspace/Models/TTSVoiceInput.svelte` | Voice field with suggestions |
| `src/lib/components/workspace/Models/ModelMenu.svelte` | Workspace row menu (Edit, Hide or Show, Keep in or Hide from Sidebar, Clone, Copy Link, Export, Share, Delete) |
| `src/routes/(app)/workspace/models/+page.svelte` | Loads the model list, then the Workspace › Models page |
| `src/routes/(app)/workspace/models/create/+page.svelte` | Create page: duplicate-ID check, create call, clone and community pre-fill |
| `src/routes/(app)/workspace/models/edit/+page.svelte` | Edit page: write-access check, save call |
| `src/lib/components/admin/Settings/Models.svelte` | Settings › Admin › Models: list assembly, filters, Actions, order, Selected and Pinned, hide, privacy, switch, clone, export, import, reset, base-model editor |
| `src/lib/components/admin/Settings/Models/AdminViewSelector.svelte` | The admin list's view filter |
| `src/lib/components/admin/Settings/Models/ModelMenu.svelte` | The admin row menu |
| `src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte` | Model Defaults: capabilities, parameters, prompt suggestions, save |
| `src/lib/components/admin/Settings/Models/ManageModelsModal.svelte` | Manage Models dialog and engine choice |
| `src/lib/components/admin/Settings/Models/Manage/ManageMultipleOllama.svelte`, `ManageMultipleProviderModels.svelte` | Server pickers inside the Manage dialog (`Select an Ollama instance`, `Select an instance`) |
| `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte` | Ollama pull, update, delete, create and upload tools |
| `src/lib/components/admin/Settings/Models/Manage/ManageProviderModels.svelte` | llama.cpp and LM Studio download, load, unload and delete |
| `src/lib/components/chat/ModelSelector.svelte` | Selector wrapper: Set as default, pins, Compare permission, clearing unavailable selections |
| `src/lib/components/chat/ModelSelector/Selector.svelte` | The selector list: search, filters, hidden-model filter, Compare, downloads, Eject, Delete, empty states, Set as default |
| `src/lib/components/chat/ModelSelector/ModelItem.svelte` | One selector row: picture, name, details, loaded state, icons, Eject, menu |
| `src/lib/components/chat/ModelSelector/ModelItemMenu.svelte` | Selector row menu (Edit, Delete, sidebar, Copy Link, Community Reviews) |
| `src/lib/components/layout/Sidebar/PinnedModelList.svelte`, `PinnedModelItem.svelte` | Sidebar pins: visible pins, drag order, Unpin |
| `src/lib/apis/models/index.ts` | Front-end calls for the Models API. `createNewModel` and `deleteModelById` pass on the server's text; the others pass on the whole error object, which some pages print as `[object Object]` (`:10`, `:61`, `:231`, `:403`) |

### 13.2 Files Consulted Outside Scope

| File | Why |
|---|---|
| `backend/open_webui/utils/models.py` | Building each person's model list; base-model records; default metadata; actions and filters; access filtering; chat-time model access |
| `backend/open_webui/main.py` | `GET /api/models`, ordering, chat model resolution, custom-model fallback, parameter merging, `/api/config`, start-up pre-fetch |
| `backend/open_webui/routers/configs.py` | Model settings and prompt suggestion endpoints |
| `backend/open_webui/env.py`, `backend/open_webui/constants.py` | Environment switches; message text |
| `backend/open_webui/utils/validate.py` | Picture and background image rules |
| `backend/open_webui/utils/payload.py` | How parameters reach providers |
| `backend/open_webui/utils/middleware.py`, `backend/open_webui/utils/tools.py`, `backend/open_webui/tools/builtin.py`, `backend/open_webui/utils/memory.py` | Capability effects, model knowledge, built-in tools, tool access |
| `backend/open_webui/retrieval/utils.py`, `backend/open_webui/utils/access_control/files.py` | Knowledge base and file access when a model is used |
| `backend/open_webui/utils/access_control/__init__.py`, `backend/open_webui/models/access_grants.py` | Grant filtering and storage (cited in sections 3 and 6) |
| `backend/open_webui/models/users.py`, `backend/open_webui/routers/users.py` | Where personal defaults and pins are stored; the Interface settings rule |
| `backend/open_webui/routers/functions.py`, `backend/open_webui/models/functions.py` | Function lists offered to the editor |
| `backend/open_webui/routers/openai.py`, `backend/open_webui/routers/ollama.py` | System prompt and parameters applied per model; Ollama deletion |
| `backend/open_webui/events.py` | Event names, payloads, webhooks |
| `backend/open_webui/migrations/versions/7e5b5dc7342b_init.py`, `922e7a387820_add_group_table.py`, `f1e2d3c4b5a6_add_access_grant_table.py` | History of the `model` table |
| `src/lib/components/chat/Chat.svelte` | New-chat model choice, model defaults, chat reload fallback, background image |
| `src/lib/components/chat/MessageInput.svelte` | Where the selector sits; capability checks |
| `src/lib/components/chat/Messages/ResponseMessage.svelte`, `src/lib/components/chat/Messages/ContentRenderer.svelte` | Model names on replies; status and citation capabilities |
| `src/lib/components/chat/Placeholder.svelte` | Prompt suggestion choice |
| `src/lib/components/chat/Settings/Advanced/AdvancedParams.svelte` | Every parameter |
| `src/lib/components/chat/SettingsModal.svelte`, `src/routes/(app)/admin/settings/[tab]/+page.svelte` | The admin Models tab (sections 1 and 2) |
| `src/lib/components/common/ConfirmDialog.svelte`, `src/lib/components/common/Tags.svelte`, `src/lib/components/common/LanguageModeSelect.svelte`, `src/lib/components/common/FileItemModal.svelte` | Default confirmation text, tags, editing language, whole-document switch |
| `src/lib/stores/index.ts`, `src/lib/constants.ts`, `src/lib/shortcuts.ts`, `src/lib/utils/localizedContent.ts` | Pin stores, default capabilities, shortcut, translated names and suggestions |
| `src/lib/apis/index.ts`, `src/lib/apis/openai/index.ts` | Model list fetch and direct models; download error text |
| `src/routes/(app)/+layout.svelte`, `src/routes/+layout.svelte`, `src/routes/(app)/workspace/+layout.svelte`, `src/routes/(app)/workspace/+page.svelte` | When the model list loads; desktop refresh event; Workspace guards |
| `src/lib/i18n/locales/en-US/translation.json` | English text of the dotted keys quoted in sections 5.4 and 5.13 |

## 14. Open Questions

The code cannot settle the items below. Each heading says who can answer. Every item marked TO BE
CONFIRMED earlier in this document is repeated here, with the behaviours read from code that should
be confirmed in a test environment.

### 14.1 Live Data (Answered by an Admin or a Read-Only Database Query)

- Which provider models have a base-model settings record, and which of those are Public, shared with
  groups or Private (admin-only) (sections 3.3, 5.15).
- The workspace models in production: owners, sharing, which are hidden or disabled, and which have a
  base model that is no longer offered (sections 5.9, 5.11, 5.24).
- The live values of `ui.default_models`, `ui.default_pinned_models`, `ui.model_order_list`,
  `models.default_metadata`, `models.default_params`, `ui.prompt_suggestions` and
  `ui.prompt_suggestions_i18n`, including whether the built-in example prompt suggestions still show
  (sections 5.16, 5.17, 7.1).
- Whether arena models are on (`evaluation.arena.enable`), which arenas exist and their access lists
  (sections 3.3, 7.1).
- The live default and group values of `workspace.models`, `workspace.models_import`,
  `workspace.models_export`, `sharing.models`, `sharing.public_models`, `chat.multiple_models` and
  `settings.interface` (sections 3.2, 3.7).
- Which models attach knowledge bases that are not shared with the model's audience, and which have
  **Builtin Tools** or the **Knowledge Base** tool group switched off (sections 3.6, 11.7).
- Whether community sharing is on, which shows **Share** (sending a model to openwebui.com),
  **Community Reviews** and **Discover a model** (sections 4, 5.21, 10.3).
- Which event webhooks and event functions are configured and where they deliver; model events carry
  the acting person's name and email (section 9.1).
- Which models are owned by accounts that no longer exist (shown as `Deleted User`) (section 10.3).

### 14.2 Deployment Environment (Answered by the Platform Maintainer)

- The production host name; URLs in this document are relative to the site root.
- The live values of `BYPASS_ADMIN_ACCESS_CONTROL` (or `ENABLE_ADMIN_WORKSPACE_CONTENT_ACCESS`),
  `BYPASS_MODEL_ACCESS_CONTROL`, `ENABLE_CUSTOM_MODEL_FALLBACK`, `ENABLE_PLUGINS`,
  `ENABLE_PROFILE_IMAGE_URL_FORWARDING`, `PROFILE_IMAGE_ALLOWED_MIME_TYPES` and
  `PROFILE_IMAGE_MAX_DATA_URI_SIZE` (section 7.2).
- Whether the base-model cache is on, whether Redis is configured, and how many server processes run;
  these decide whether everyone sees the same model list at the same time (sections 8, 10.7).
- Which engines production uses (OpenAI-compatible providers, Ollama, llama.cpp, LM Studio), which
  decides what the Manage dialog and the selector's **Delete** and **Eject** act on (sections 5.12,
  5.19).
- Whether database backups exist, how often and how long they are kept: without an export file they
  are the only way to recover a deleted model or a **Reset** (sections 5.12, 5.18, 11.12).
- Whether `ENABLE_PERSISTENT_CONFIG` or `RESET_CONFIG_ON_START` change where the settings in section
  7.1 come from (`../tools/ground-truth.md`, Settings).
- Security-sensitive: how model access control and sharing restrictions are enforced on server paths
  beyond those described in section 3 and in `users-groups-roles-and-permissions.md`. Refer to the
  platform maintainer and U of T Information Security (security.utoronto.ca).

### 14.3 People and Process (Answered by the Service Owner)

- Support contacts, escalation routes and hours, and who acts as model administrators; none exist in
  the repository (`../tools/ground-truth.md`, Contacts).
- Who may be given **Models Access**, **Import Models**, **Export Models** and public sharing, and how
  requests are approved (sections 3.2, 11.3).
- The policy on public models, and on attaching personal or confidential files to shared models, since
  anyone who can read a model can read its attached files (section 3.5).
- What should happen to models owned by people who leave; the interface has no ownership transfer
  (sections 10.3, 11.18).
- Whether sending models to the community site and following community links is acceptable for this
  deployment (sections 4, 10.3).
- Who reviews event webhook destinations, given that model events carry personal data (section 9.1).
- Naming and ID conventions for shared models, since IDs cannot be changed (sections 5.2, 11.4).

### 14.4 Product Behaviour (Answered by the Platform Maintainer or Upstream Open WebUI)

Every behaviour in this document was read from the code; none was exercised against a running
instance. These in particular should be confirmed in a test environment:

- **Custom-model fallback**: whether the workspace model's system prompt reaches the replacement model
  (read from code: it is not expected to), and which model ID the chat records for a fallback reply
  (section 5.24).
- **Admin page after a first change to a record-less base model**: later switches, hides and edits of
  the same model before a reload appear to work but are not saved, and edits fail with
  `Failed to save model`, shown twice (sections 5.15, 11.20, 11.22).
- **Selector Delete on llama.cpp base models** calls the Ollama deletion endpoint and is expected to
  fail (section 5.12).
- **Workspace Actions (Enable, Disable, Show, Hide All)** include read-only models in the selection, so
  the action stops early without its message after changing only some models (section 10.3).
- **Workspace Enabled switch** shows nothing when the server refuses (section 5.11).
- **Shift + delete** in Workspace › Models deletes without confirmation; whether that is intended
  (section 5.12).
- **Set as default** reports `Default model updated` although the server discards it for people
  without **Interface Settings Access** (section 3.7).
- **`[object Object]` pop-ups** where pages print whole error objects (section 10).
- **Make Private** in the admin list removes every access entry, not only the public one (section 5.10).
- **Default metadata and admins without the bypass**: once Model Defaults are saved, record-less base
  models leave the model list of admins with `BYPASS_ADMIN_ACCESS_CONTROL` off (section 5.17).
- The ID-length message says "less than 256 characters" while exactly 256 is accepted (section 5.2);
  the Enabled-switch failure text says "function" (section 10.1).
- Import entries with no parameters clear an existing model's parameters, system prompt included
  (section 5.20).
- The unused message constants `MESSAGES.MODEL_ADDED` and `MESSAGES.MODEL_DELETED`
  (`backend/open_webui/constants.py:28-29`) have no caller.
- No control in the model screens clears a personal default model or returns a person's pins to the
  admin's list (sections 5.22, 11.14).
- Whether native function calling works with each production base model, which decides whether
  attached knowledge is used in the default mode (section 11.7); provider behaviour.

### 14.5 Knowledgebase Consistency (Answered by the Knowledgebase Maintainer)

- **Correction needed in this document's earlier sections (left unchanged on instruction):** sections
  1 and 2.1 say the model selector is at the top of the chat; the code places it in the message
  composer at the bottom right (`src/lib/components/chat/MessageInput.svelte:2577-2585`), as
  `chat-composer-and-message-display.md` also states. Section 4 and section 5.21 describe the correct
  location. *Resolved 2026-10-08: verified and corrected in place in sections 1 and 2.1; logged in
  `../tools/VERIFICATION.md`.*
- **Precision note on section 3.3:** it says switching a provider model on in Settings › Admin › Models
  creates a record with no grants. A base model with no record already shows as enabled; the first
  switch-off creates a disabled record with no access entries, and switching it on again (after a
  reload, section 11.20) leaves it without them (section 5.11;
  `src/lib/components/admin/Settings/Models.svelte:295-313`, `:514-538`).
  The conclusion (admin-only until a read entry exists) is unaffected. *Resolved 2026-10-08: added
  to section 3.3 as a precision note after verification.*
- `users-groups-roles-and-permissions.md`, section 3.7, says admins with `BYPASS_ADMIN_ACCESS_CONTROL`
  off still see base models that have no record; that holds only while no Model Defaults metadata is
  stored (section 5.17; `backend/open_webui/utils/models.py:341-347`, `:563-574`).
- `model-connections-openai-ollama-and-direct.md` currently ends after section 7; this document relies
  on its sections 5.7 to 5.11. *Resolved 2026-10-08: that document is now complete (14 sections).*
- Documents referred to here that are not yet written: `knowledge-bases.md`,
  `workspace-tools-tool-servers-mcp-and-terminals.md`, `functions-pipes-filters-actions-and-pipelines.md`,
  `prompts-and-skills.md`, `evaluations-feedback-and-analytics.md`, `admin-settings-panels.md`,
  `builtin-native-tools.md`, `files-uploads-and-storage.md`, `rag-retrieval-embeddings-and-vector-stores.md`.
  Their descriptions of models should be checked against this document when they exist.
- No contradiction with `../tools/ground-truth.md` was found.
