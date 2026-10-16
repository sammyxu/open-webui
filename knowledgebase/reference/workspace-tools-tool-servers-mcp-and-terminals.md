# Workspace Tools, Tool Servers (OpenAPI and MCP) and Terminals

## At a Glance

- People meet three kinds of extension: **workspace tools** (Python code stored in the database
  and **run on the MedIT GPT server**), **tool servers** (external OpenAPI or MCP services, added by
  admins, or by a person as their own "direct" server) and **terminals** (Open Terminal services
  that give the model commands and files, with a shell dock in the chat). Sections 1 and 4.
- **Workspace tools are admin-governed.** Creating or editing tool code needs **Tools Access**
  (`workspace.tools`, off by default); saving a tool runs its code and installs the Python
  packages it lists. Using a shared tool needs only read access. Sections 3 and 5.3.
- In a chat, tools are switched on in the composer's **Integrations** menu (**Tools**); terminals
  have their own **Terminal** menu. Tools that use OAuth 2.1 show an amber `Click to connect` chip
  until the person connects (see `sso-oauth-oidc-and-scim.md` 5.13). Section 5.1.
- **Admin tool servers and terminals are admin-only until an admin adds access grants**, and a new
  admin terminal is saved **switched off**. Check both first when users cannot see a server.
  Sections 3.1, 5.7, 5.10, 11.6.
- A person's own tool servers and terminals need the admin switch **Direct Integrations** and the
  **Direct Tool Servers** permission (both off by default); the **browser** calls them, so they
  need CORS and an open tab. Section 5.9.
- MCP is supported over **Streamable HTTP** only; the server connects for each message with a
  10-second handshake limit, and failures show `Failed to connect to MCP server '{server_id}'`.
  OpenAPI specifications are cached; with Redis the code sets no expiry, so the cache changes only
  when an admin saves the list or the server restarts. Sections 5.8 and 8.2.
- **Valves** are a tool's shared settings (write access); **user valves** are each person's own,
  set from the Integrations menu or chat Controls. Sections 5.2 and 5.6.
- Terminal errors read `Terminal unavailable: …` in the reply or `[Connection closed]` in the
  shell; with the Shell tab open the model can read and type into it. Sections 5.12, 10, 11.13-11.14.
- No fork changes in scope; the fork's **Hide Processing Details** setting hides tool-call details
  (section 12). Ground-truth discrepancy on valve encryption recorded in section 14.1.

## 1. Purpose and Who Uses It

This area covers the ways MedIT GPT lets a model **do things** beyond writing text: call a
function written in Python, call an external web service, or run commands in a terminal. It does
**not** cover the built-in (native) tools that ship with the application, such as web search,
memory and knowledge tools (see `builtin-native-tools.md`), or Python *functions* (pipes, filters,
actions; see `functions-pipes-filters-actions-and-pipelines.md`).

A person meets three kinds of extension.

| Kind | What it is | Where it runs | Who adds it | Source |
|---|---|---|---|---|
| **Workspace tool** (also "toolkit") | Python code with a `Tools` class whose methods become functions the model may call. Stored in the database (`tool` table) | **On the MedIT GPT server, inside the application process.** Saving a tool loads (runs) its code on the server and may install Python packages | Admins, and users granted the `workspace.tools` (or `workspace.tools_import`) permission | `backend/open_webui/models/tools.py:21-33`; `backend/open_webui/utils/plugin.py:206-256`; `backend/open_webui/routers/tools.py:346-427` |
| **Tool server** (external) | A separate web service described by an **OpenAPI** specification or speaking the **MCP** (Model Context Protocol) | On its own host. Admin-configured servers are called by the MedIT GPT server; a user's own "direct" servers are called by the person's browser | Admins (Admin Settings > Integrations); users with the `features.direct_tool_servers` permission when the admin switch for direct integrations is on (Settings > Integrations) | `backend/open_webui/routers/configs.py:217-298`; `src/lib/components/chat/SettingsModal.svelte:385-391`; `src/routes/+layout.svelte:500-554` |
| **Terminal** (terminal server) | An "Open Terminal" service, or an orchestrator that hands out terminals by policy, giving the model commands, files and a working directory; the person can also open an interactive terminal dock | On its own host. Admin terminals are reached through the MedIT GPT server (`/api/v1/terminals/...`); a user's own terminals are reached from the browser | Admins (Admin Settings > Integrations > Terminal); users with direct integrations (Settings > Integrations > Open Terminal) | `backend/open_webui/routers/terminals.py:1-6`, `:87-103`; `backend/open_webui/utils/terminals.py:20-35`; `en-US` key `settings.personal.tools.terminals.addConnection.description` (`src/lib/i18n/locales/en-US/translation.json:3045`) |

**Workspace tools run Python on the MedIT GPT server and are admin-governed.** The permission to
create or edit them is off by default for users (`backend/open_webui/config.py:1745-1746`,
`:1945`), and only admins can import a tool from a web address
(`backend/open_webui/routers/tools.py:264-265`). Anyone allowed to create or change tool code can
make the server run code of their choosing, which is why the permission is off by default; whether
MedIT GPT grants it to anyone is **TO BE CONFIRMED** (section 14).

**Who uses this area.**

- **Everyday users** switch tools on for a chat from the integrations menu in the message composer,
  connect their own account to tools that need it (OAuth), fill in **user valves** (per-person
  settings a tool asks for), and open a terminal when one is offered.
- **Tool authors** (admins, or users granted the workspace permission) create, edit, share, import
  and export workspace tools in **Workspace > Tools**.
- **Admins** register external OpenAPI and MCP tool servers and terminal servers, decide which
  users and groups may use each, set admin **valves** on tools, and set the related permissions.
- **Tier 1 support** reads what a person sees (error pop-ups, a tool missing from the menu, an
  amber "connect" chip, a terminal that will not open) and escalates; tier 1 does not change tools,
  servers, valves or permissions.

The live list of tools, tool servers and terminals in MedIT GPT is data held in the database and is
**TO BE CONFIRMED**; nothing in the repository says which, if any, are configured in production.

## 2. Navigation and URLs

URLs are relative to the site root; the production host name is **TO BE CONFIRMED**. Settings
open in a single **Settings** window: a deep link such as `/admin/settings/integrations` forwards
to `/?settings=admin%3Aintegrations`, which opens that tab; a non-admin following an `admin:` link
lands on the General tab instead (`src/routes/(app)/admin/settings/[tab]/+page.svelte:5-10`;
`src/routes/(app)/+layout.svelte:165-194`).

### 2.1 Screens

| Screen | How to reach it | Who sees it | What is there | Source |
|---|---|---|---|---|
| **Workspace > Tools** (list) | Sidebar **Workspace**, then the **Tools** tab; or `/workspace/tools`. The browser tab reads `Tools / MedIT GPT` | Admins, and users with `workspace.tools`, and only when plugins are enabled (`enable_plugins`, from `ENABLE_PLUGINS`). Others are sent to `/` (or to `/workspace` when plugins are off) | Search box (`Search Tools`), view filter, sortable **Title** and **Updated at** columns, one row per tool with owner, version and a `Read Only` badge where the person cannot edit; actions **Create**, **Import From Link** (admins only), **Import JSON** (admins or `workspace.tools_import`), **Export JSON** (admins or `workspace.tools_export`) | `src/routes/(app)/workspace/tools/+page.svelte:8-16`; `src/routes/(app)/workspace/+layout.svelte:53-55`, `:94-98`, `:219-235`; `src/lib/components/workspace/Tools.svelte:81-121`, `:297-304`, `:340-346`, `:389-476`; `backend/open_webui/main.py:2353` |
| **New tool** editor | **Create** on the Tools list, or `/workspace/tools/create` | As above | Name, ID, description, language selector, **Access** button, Python code editor, the warning line and **Save & Create** | `src/routes/(app)/workspace/tools/create/+page.svelte:81-97`; `src/lib/components/workspace/Tools/ToolkitEditor.svelte:227-378` |
| **Edit tool** editor | Click a row the person can edit, or row menu **Edit**; `/workspace/tools/edit?id={id}` | People with write access to that tool | Same editor; the ID is fixed; button reads **Save** | `src/lib/components/workspace/Tools.svelte:177-179`, `:429-445`; `src/routes/(app)/workspace/tools/edit/+page.svelte:57-102` |
| Tool **Valves** (admin valves) | Gear icon (tooltip `Valves`) on a Tools list row | People with write access to the tool | A form generated from the tool's `Valves` class; **Save** | `src/lib/components/workspace/Tools.svelte:549-581`, `:658-663`; `src/lib/components/workspace/common/ValvesModal.svelte:162-213` |
| **Settings > Admin > Integrations** | User menu > **Settings**, admin list, **Tools** group, **Integrations**; or `/admin/settings/integrations` | Admins only | Sections **Tools** (list headed **External Tool Servers**, **+** to add), **Terminal** (list headed **Open Terminal**, **+** to add), **Knowledge** (external knowledge sources, another area) and **User Connections** (the **Direct Integrations** switch) | `src/lib/components/chat/SettingsModal.svelte:165`, `:329-332`, `:871-872`; `src/lib/components/admin/Settings/Integrations.svelte:183-357`; `src/lib/i18n/locales/en-US/translation.json:2173-2174`, `:2181`, `:2476-2483` |
| **Settings > Integrations** (personal) | User menu > **Settings**, **Services** group, **Integrations**; or `/?settings=tools` | Only when the admin switch **Direct Integrations** is on **and** the person is an admin or has `features.direct_tool_servers` | **External Tool Servers** (the person's own OpenAPI servers) and **Open Terminal** (the person's own terminals), with notes about browser sessions and CORS | `src/lib/components/chat/SettingsModal.svelte:148`, `:218-222`, `:385-391`, `:638-650`, `:818-824`; `src/lib/components/chat/Settings/Integrations.svelte:94-201`; `src/lib/components/chat/Settings/Integrations/Terminals.svelte:53-104` |
| Composer **Integrations** menu | The button with tooltip `Integrations` beside the **+** (`More`) button at the bottom left of the message box | Shown when at least one tool or tool server is listed for the person, or skills, filters, web search, image or code interpreter apply | **Tools** sub-list (switch per tool, search `Search tools`, a **Valves** knob for tools with user valves, a **Disconnect OAuth** button for connected OAuth tools), **Skills**, toggleable filters, **Web Search**, **Image**, **Code Interpreter** | `src/lib/components/chat/MessageInput.svelte:816-817`, `:2295-2344`; `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:293-735` |
| **Available Tools** window | The wrench chip showing a number (tooltip `{COUNT} Available Tools`) that appears once tools are switched on | Anyone with tools selected | The selected tools with `Auth required` or `Connected` for OAuth tools and their function names; the person's own tool servers under **Tool Servers** | `src/lib/components/chat/MessageInput.svelte:1634`, `:2366-2386`; `src/lib/components/chat/ToolServersModal.svelte:35-161` |
| Amber "connect" chips | Appear in the composer when the chosen model uses an OAuth tool the person has not connected; hover text `Click to connect` | The person concerned | Clicking starts the tool's sign-in (see `sso-oauth-oidc-and-scim.md` section 5.13) | `src/lib/components/chat/MessageInput.svelte:2546-2559`; `src/lib/components/chat/Chat.svelte:1029-1054` |
| **Terminal** selector | Cloud icon (tooltip `Terminal`) in the composer; shows the chosen terminal's name | Shown when a selected model has the terminal capability and an admin terminal is available to the person, or the person has direct access and their own terminals; disabled while a reply is being written | Lists **Direct** (own) and **System** (admin) terminals; **Add Terminal** opens Settings > Integrations or, for admins, Admin > Integrations | `src/lib/components/chat/MessageInput.svelte:801-808`, `:2563-2569`; `src/lib/components/chat/MessageInput/TerminalMenu.svelte:132-300` |
| **Files** panel and terminal dock | Choosing a terminal opens the side panel on the **Files** tab on wide screens (setting `showFilesOnTerminalSelect`, default on); the dock is a bar labelled **Terminal** at the bottom of the Files panel | People using a terminal whose server does not switch the terminal feature off | File browser (another area) and the dock with a **Shell** tab plus one read-only tab per command the model ran | `src/lib/components/chat/MessageInput/TerminalMenu.svelte:65-70`, `:89-94`; `src/lib/components/chat/ChatControls.svelte:102-110`, `:295-298`; `src/lib/components/chat/FileNav.svelte:2113-2135`; `src/lib/components/chat/TerminalDock.svelte:164-292` |
| Chat **Controls > Valves** | Chat controls side panel, **Valves** section | Admins, and users with `chat.valves` (default on) | Choose **Tools** or **Functions**, pick a workspace tool (`Select a tool`), edit its user valves; changes save automatically | `src/lib/components/chat/Controls/Controls.svelte:94-104`; `src/lib/components/chat/Controls/Valves.svelte:76-112`, `:175-187` |

### 2.2 Server Endpoints

All need a signed-in user; "admin" means `get_admin_user`. The tools router is mounted at
`/api/v1/tools`, the configs router at `/api/v1/configs` and the terminals router at
`/api/v1/terminals` (`backend/open_webui/main.py:854`, `:869`, `:881`).

| Method and path | Who | Purpose | Source |
|---|---|---|---|
| `GET /api/v1/tools/` | Any user | Tools the person may use: workspace tools (when plugins are on), admin OpenAPI servers as `server:{id}` and enabled admin MCP servers as `server:mcp:{id}` (with `authenticated` for OAuth ones), filtered by access; optional `query` | `backend/open_webui/routers/tools.py:67-191` |
| `GET /api/v1/tools/list` | Any user | Workspace tools for the Tools page, each with `write_access` | `backend/open_webui/routers/tools.py:199-235` |
| `POST /api/v1/tools/load/url` | Admin | Fetch tool code from a web address (GitHub links are converted to raw file links) for **Import From Link** | `backend/open_webui/routers/tools.py:243-308` |
| `GET /api/v1/tools/export` | Admin or `workspace.tools_export` | Tools the person can write, with code | `backend/open_webui/routers/tools.py:316-338` |
| `POST /api/v1/tools/create` | Admin, or `workspace.tools` or `workspace.tools_import` | Create a tool (loads its code) | `backend/open_webui/routers/tools.py:346-427` |
| `GET /api/v1/tools/id/{id}` | Owner, read grant, or admin | One tool; code only for people with write access | `backend/open_webui/routers/tools.py:435-476` |
| `POST /api/v1/tools/id/{id}/update` | Owner, write grant, or admin; changing code also needs `workspace.tools` or `workspace.tools_import` | Update a tool | `backend/open_webui/routers/tools.py:484-576` |
| `POST /api/v1/tools/id/{id}/access/update` | Owner, write grant, or admin | Replace the tool's sharing grants | `backend/open_webui/routers/tools.py:588-637` |
| `DELETE /api/v1/tools/id/{id}/delete` | Owner, write grant, or admin | Delete a tool | `backend/open_webui/routers/tools.py:645-689` |
| `GET .../id/{id}/valves`, `GET .../valves/spec`, `POST .../valves/update` | Owner, write grant, or admin | Read, describe and save admin valves | `backend/open_webui/routers/tools.py:697-842` |
| `GET .../id/{id}/valves/user`, `GET .../valves/user/spec`, `POST .../valves/user/update` | Owner, read grant, or admin | Read, describe and save the person's own user valves | `backend/open_webui/routers/tools.py:850-987` |
| `GET` / `POST /api/v1/configs/tool_servers` | Admin | Read or replace the admin tool-server list; saving refreshes the server list cache | `backend/open_webui/routers/configs.py:235-298` |
| `POST /api/v1/configs/tool_servers/verify` | Admin | The dialog's connection check (or OAuth discovery check) | `backend/open_webui/routers/configs.py:551-680` |
| `POST /api/v1/configs/oauth/clients/register` | Admin | **Register Client** for OAuth 2.1 MCP servers | `backend/open_webui/routers/configs.py:163-209` |
| `GET` / `POST /api/v1/configs/connections` | Admin | Includes the **Direct Integrations** switch (`ENABLE_DIRECT_INTEGRATIONS`) | `backend/open_webui/routers/configs.py:40-44`, `:133-160` |
| `GET` / `POST /api/v1/configs/terminal_servers` | Admin | Read or replace the admin terminal list | `backend/open_webui/routers/configs.py:326-352` |
| `POST /api/v1/configs/terminal_servers/verify`, `/policy`, `/lifecycle`, `/refresh` | Admin | Detect terminal type; read or save an orchestrator policy and lifecycle; refresh terminals | `backend/open_webui/routers/configs.py:355-548` |
| `GET /api/v1/terminals/` | Any user | Admin terminals the person may use (enabled and granted) | `backend/open_webui/routers/terminals.py:87-103` |
| Any method `/api/v1/terminals/{server_id}/{path}` | Any user with access | Pass-through to the admin terminal server (files, commands, working directory) | `backend/open_webui/routers/terminals.py:106-249` |
| WebSocket `/api/v1/terminals/{server_id}/api/terminals/{session_id}` | Any user with access | The interactive shell in the dock | `backend/open_webui/routers/terminals.py:322-471` |
| `/oauth/clients/{client_id}/authorize` and `/callback` | Any user | Per-person sign-in to OAuth 2.1 MCP servers; documented in `sso-oauth-oidc-and-scim.md` sections 2.2 and 5.13 | `backend/open_webui/main.py:2772-2825` |

A person's own (direct) tool servers and terminals are **not** reached through these endpoints: the
browser calls them directly (sections 5.9 and 5.13).

## 3. Roles and Permissions

Roles are `admin`, `user` and `pending` (`../tools/ground-truth.md`, Accounts and Access). Pending
users cannot use the application, so they meet nothing in this area. Permissions add up across
groups and a group cannot take away a permission the defaults grant (same source); the full
permission model is in `users-groups-roles-and-permissions.md`.

### 3.1 Who May Do What

| Action | Who may do it | What happens otherwise | Source |
|---|---|---|---|
| Use a workspace tool in a chat | Its owner, anyone with a read grant (a named person, a group they belong to, or public), or an admin when admin bypass is on | The tool is left out of the list in the integrations menu; if it is still requested, the server skips it silently and logs `Access denied to tool {tool_id} for user {user.id}` | `backend/open_webui/routers/tools.py:74-102`; `backend/open_webui/utils/tools.py:283-299` |
| Open **Workspace > Tools** | Admins, or users with `workspace.tools`, when plugins are enabled | Redirected to `/` | `src/routes/(app)/workspace/+layout.svelte:53-55`, `:81-98` |
| Create a tool | Admins, or users with `workspace.tools` or `workspace.tools_import` | `401 Unauthorized` | `backend/open_webui/routers/tools.py:354-366` |
| Change a tool's **code** | Owner, write grant or admin, **and** (admin, `workspace.tools` or `workspace.tools_import`) | `401 Unauthorized` | `backend/open_webui/routers/tools.py:500-526` |
| Change a tool's name, description or sharing without touching code | Owner, write grant or admin | `401 Unauthorized` | `backend/open_webui/routers/tools.py:500-515`, `:603-617` |
| Delete a tool | Owner, write grant or admin | `401 Unauthorized` | `backend/open_webui/routers/tools.py:659-673` |
| See a tool's code | People with write access (owner, write grant, or admin when admin bypass is on) | The code is withheld; the Tools list shows the row as `Read Only` and does not open it; opening the edit address directly shows `You do not have permission to edit this tool` | `backend/open_webui/routers/tools.py:451-466`; `src/lib/components/workspace/Tools.svelte:430-445`, `:475-477`; `src/routes/(app)/workspace/tools/edit/+page.svelte:68-72` |
| **Import From Link** | Admins only (menu item and server) | Not offered; the server answers 401 to anyone else | `src/lib/components/workspace/Tools.svelte:89-95`; `backend/open_webui/routers/tools.py:264-265` |
| **Import JSON** | Admins, or `workspace.tools_import` | Not offered | `src/lib/components/workspace/Tools.svelte:96-101` |
| **Export JSON** / row **Export** | Admins, or `workspace.tools_export` | Not offered; server answers `401 Unauthorized` | `src/lib/components/workspace/Tools.svelte:102-119`; `src/lib/components/workspace/Tools/ToolMenu.svelte:98-111`; `backend/open_webui/routers/tools.py:322-331` |
| Share a tool with people or groups | The **Access** dialog offers sharing to admins and to people with `sharing.tools`; **Public** needs `sharing.public_tools`; sharing with named people needs `access_grants.allow_users` and with groups `access_grants.allow_groups` (both on by default) | The server removes grants the person may not set when saving, without a message | `src/lib/components/workspace/Tools/ToolkitEditor.svelte:207-225`; `backend/open_webui/routers/tools.py:379-385`, `:539-545`, `:619-625`; `backend/open_webui/utils/access_control/__init__.py:223-301` |
| Set a tool's admin **valves** | Owner, write grant or admin | `You do not have permission to access this resource. Please contact your administrator for assistance.` | `backend/open_webui/routers/tools.py:697-842` |
| Set one's own **user valves** | Anyone who can read the tool; the knob in the integrations menu and the Controls **Valves** section also need admin or `chat.valves` (default on) | The knob and section are hidden | `backend/open_webui/routers/tools.py:850-987`; `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:625-644`; `src/lib/components/chat/Controls/Controls.svelte:94` |
| Add, edit, enable or delete **admin tool servers** and **terminal servers** | Admins only | The Admin Integrations tab is not offered; the endpoints answer 401 | `backend/open_webui/routers/configs.py:235-298`, `:326-352` |
| Use an **admin tool server** or **admin terminal** | Admins when admin bypass is on; otherwise only people matched by the server's access grants. **A server with no grants is private to admins** | The server does not appear in the menus; requests are refused (`Access denied` for terminals) | `backend/open_webui/utils/access_control/__init__.py:151-179`; `backend/open_webui/routers/tools.py:175-185`; `backend/open_webui/routers/terminals.py:87-103`, `:126-128` |
| Add **one's own (direct)** tool servers and terminals | Admins, or users with `features.direct_tool_servers` (default off). The **Integrations** tab is also hidden unless an admin turns on **Direct Integrations** (default off) | The tab is not offered. If the permission is missing, the server drops saved tool servers from the person's settings and ignores any sent with a chat message | `src/lib/components/chat/SettingsModal.svelte:385-391`; `backend/open_webui/routers/users.py:520-530`; `backend/open_webui/main.py:1242-1251` |
| Choose a terminal in the composer | Shown when a selected model has the `terminal` capability (default on) and a terminal is available; a person's own terminals also need admin or `features.direct_tool_servers` | The selector is hidden | `src/lib/components/chat/MessageInput.svelte:796-808`; `src/lib/components/chat/MessageInput/TerminalMenu.svelte:163-164` |

**Admin bypass.** With `BYPASS_ADMIN_ACCESS_CONTROL` on (the code default), admins see every
workspace tool and every admin tool server and terminal regardless of grants
(`backend/open_webui/config.py:2086-2092`; `backend/open_webui/routers/tools.py:75`;
`backend/open_webui/utils/access_control/__init__.py:166-167`). With it off, admins see what they
own or what is shared with them, but keep access to admin servers that have no grants
(`backend/open_webui/utils/access_control/__init__.py:169-174`). The live value is environment data
and **TO BE CONFIRMED**.

### 3.2 Permission Keys Used Here

Defaults are the code defaults; the live values are in the `user.permissions` setting and group
records and are **TO BE CONFIRMED**. Labels are those of the group permissions editor
(`src/lib/components/admin/Users/Groups/Permissions.svelte`).

| Key | Label | Code default | Environment variable | Effect in this area | Source |
|---|---|---|---|---|---|
| `workspace.tools` | `Tools Access` (tooltip `Warning: Enabling this will allow users to upload arbitrary code on the server.`); offered only when plugins are enabled | off | `USER_PERMISSIONS_WORKSPACE_TOOLS_ACCESS` | Workspace > Tools page; creating tools and changing tool code | `backend/open_webui/config.py:1745-1746`, `:1945`; `src/lib/components/admin/Users/Groups/Permissions.svelte:141-153` |
| `workspace.tools_import` | `Import Tools` (shown under Tools Access) | off | `USER_PERMISSIONS_WORKSPACE_TOOLS_IMPORT` | **Import JSON**; also lets the server accept create and code changes | `backend/open_webui/config.py:1769-1770`, `:1951`; `src/lib/components/admin/Users/Groups/Permissions.svelte:156-165` |
| `workspace.tools_export` | `Export Tools` | off | `USER_PERMISSIONS_WORKSPACE_TOOLS_EXPORT` | **Export JSON** and row **Export** | `backend/open_webui/config.py:1773-1774`, `:1952`; `src/lib/components/admin/Users/Groups/Permissions.svelte:166-174` |
| `sharing.tools` | `Tools Sharing` | off | `USER_PERMISSIONS_WORKSPACE_TOOLS_ALLOW_SHARING` | Sharing controls in the tool **Access** dialog | `backend/open_webui/config.py:1811-1812`, `:1963`; `src/lib/components/admin/Users/Groups/Permissions.svelte:354-356` |
| `sharing.public_tools` | `Tools Public Sharing` | off | `USER_PERMISSIONS_WORKSPACE_TOOLS_ALLOW_PUBLIC_SHARING` | **Public** for tools | `backend/open_webui/config.py:1815-1816`, `:1964`; `src/lib/components/admin/Users/Groups/Permissions.svelte:371-375` |
| `access_grants.allow_users`, `access_grants.allow_groups` | (access-grant section) | on | `USER_PERMISSIONS_ACCESS_GRANTS_ALLOW_USERS`, `..._ALLOW_GROUPS` | Whether a person may share with named people or groups | `backend/open_webui/config.py:1841-1846`, `:1975-1976` |
| `chat.valves` | `Allow Chat Valves` | on | `USER_PERMISSIONS_CHAT_VALVES` | User-valve knobs in a chat | `backend/open_webui/config.py:1851`, `:1980`; `src/lib/components/admin/Users/Groups/Permissions.svelte:644-646` |
| `features.direct_tool_servers` | `Direct Tool Servers` | off | `USER_PERMISSIONS_FEATURES_DIRECT_TOOL_SERVERS` | A person's own tool servers and terminals | `backend/open_webui/config.py:1904-1905`, `:2007`; `src/lib/components/admin/Users/Groups/Permissions.svelte:1029-1033` |

Note that the composer and terminal menu treat a missing `features.direct_tool_servers` value as
allowed (`?? true`), while the Settings tab requires it to be true; the server-side checks above
decide what is actually used (`src/lib/components/chat/MessageInput.svelte:801-802`;
`src/lib/components/chat/SettingsModal.svelte:385-391`).

## 4. Key Concepts and Terminology

| Term | Meaning in MedIT GPT | Source |
|---|---|---|
| **Tool** (workspace tool, "toolkit") | A row in the `tool` table holding Python code that defines a class named `Tools`. Each public method of that class becomes one **function** the model may call; its description comes from the method's docstring and its parameters from the method's signature. A tool with no `Tools` class cannot be saved | `backend/open_webui/models/tools.py:21-33`; `backend/open_webui/utils/plugin.py:246-250`; `backend/open_webui/utils/tools.py:998-1018` |
| **Function** (of a tool) | One callable action inside a tool or tool server, as offered to the model (also called a "tool spec"). Not the same as the separate **Functions** feature (pipes, filters, actions), which is another area | `backend/open_webui/utils/tools.py:1010-1018`; `functions-pipes-filters-actions-and-pipelines.md` |
| **Tool ID** | The tool's permanent identifier: letters, digits and underscores only, stored in lower case, unique; suggested from the name when creating and fixed afterwards | `backend/open_webui/routers/tools.py:368-374`, `:423-427`; `src/lib/components/workspace/Tools/ToolkitEditor.svelte:55-57`, `:264-283` |
| **Frontmatter** / **manifest** | An optional block at the very top of the code, between triple quotes, with `key: value` lines. The keys the application reads are `title` and `description` (prefill the editor), `version` (shown in the Tools list), `requirements` (Python packages to install), `required_open_webui_version` (minimum version) and `funding_url` (heart **Support** button). Saved as `meta.manifest` | `backend/open_webui/utils/plugin.py:151-184`; `src/lib/components/workspace/Tools/ToolkitEditor.svelte:333-345`; `src/lib/components/workspace/Tools.svelte:459-465`, `:531-547`; `src/routes/(app)/workspace/tools/create/+page.svelte:20-36` |
| **Requirements** | The comma-separated `requirements` frontmatter line. The server installs missing packages with `pip` when the tool is saved, when a server process first loads the tool, and, for tools owned by admins, at every start-up (section 8.1) | `backend/open_webui/utils/plugin.py:222-225`, `:422-450`, `:453-484` |
| **Valves** | Settings a tool author declares in a `Valves` class; set by people with write access, shared by everyone who uses the tool (for example an API address the tool calls). Stored in the tool's record; whether they are encrypted depends on a server setting (section 14) | `backend/open_webui/routers/tools.py:697-842`; `backend/open_webui/utils/tools.py:313-316` |
| **User valves** | Per-person settings declared in a `UserValves` class; each person sets their own in a chat. A tool that declares them shows a **Valves** knob in the integrations menu | `backend/open_webui/routers/tools.py:850-987`; `backend/open_webui/models/tools.py:270-309`; `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:625-644` |
| **Plugins** (`ENABLE_PLUGINS`) | Environment switch, default on. Off hides Workspace > Tools, stops workspace tools from loading or being listed, and skips dependency installation; admin tool servers are unaffected | `backend/open_webui/env.py:1186`; `backend/open_webui/routers/tools.py:81`, `:201-202`; `backend/open_webui/utils/plugin.py:207-208`, `:461-463`; `src/routes/(app)/workspace/tools/+page.svelte:8-16` |
| **Tool server** | A separate web service the model can call. **OpenAPI** servers publish a specification (by default `openapi.json`); every operation with an `operationId` becomes a function. **MCP** servers speak the Model Context Protocol over **Streamable HTTP** only (no other MCP transport is offered) | `backend/open_webui/utils/tools.py:1071-1167`; `backend/open_webui/utils/mcp/client.py:64-86`; `src/lib/components/AddToolServerModal.svelte:553-567` |
| **Admin (system) tool server** | Configured in Admin > Integrations and stored in the `tool_server.connections` setting. The MedIT GPT **server** calls it. Listed to users as `server:{id}` (OpenAPI) or `server:mcp:{id}` (MCP) | `backend/open_webui/routers/configs.py:217-298`; `backend/open_webui/routers/tools.py:104-173` |
| **Direct tool server** | A person's own OpenAPI server, added in Settings > Integrations and saved with their settings. The person's **browser** fetches its specification and calls it, so it must be reachable from the browser and allow cross-origin requests (CORS). Listed as `direct_server:{n}` | `src/lib/components/chat/Settings/Integrations.svelte:38-59`, `:166-183`; `src/routes/+layout.svelte:437-554`; `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:145-159` |
| **Server ID** | The admin-chosen identifier of a tool server (optional for OpenAPI, where the list position is used instead; required for MCP). It may not contain `:` or `\|`. MCP functions are offered to the model as `{server id}_{function name}` | `src/lib/components/AddToolServerModal.svelte:339-343`, `:594-614`; `backend/open_webui/utils/tools.py:1537-1539`; `backend/open_webui/utils/middleware.py:2994-3004` |
| **Function Name Filter List** | Optional comma-separated list on an admin tool server limiting which of its functions are offered (the placeholder shows `func1, !func2`, where `!` excludes) | `src/lib/components/AddToolServerModal.svelte:1013-1032`; `backend/open_webui/utils/tools.py:414-426`; `backend/open_webui/utils/middleware.py:2379-2385` |
| **Auth** (tool or terminal server) | How MedIT GPT proves itself to the server: **None**; **Bearer** (an API key the admin enters); **Session** (UI text: "Forwards system user session credentials to authenticate"); **OAuth** (UI text: "Forwards system user OAuth access token to authenticate", that is the person's single sign-on token); for MCP also **OAuth 2.1** ("Uses OAuth 2.1 Dynamic Client Registration") and **OAuth 2.1 (Static)** (admin-entered client ID and secret). Direct servers offer only None, Bearer and Session | `src/lib/components/AddToolServerModal.svelte:749-818`; `src/lib/components/AddTerminalServerModal.svelte:966-998`; `backend/open_webui/utils/tools.py:146-169` |
| **Headers** | Optional extra request headers for an admin tool server, entered as a JSON object | `src/lib/components/AddToolServerModal.svelte:984-1010`; `backend/open_webui/utils/tools.py:171-174` |
| **Specification cache** | The server's copy of every enabled admin OpenAPI server's specification. With Redis it is rebuilt at start-up and whenever an admin saves the tool-server list; without Redis it is fetched again whenever it is needed (section 8.2) | `backend/open_webui/utils/tools.py:1170-1206` |
| **Terminal server** | An **Open Terminal** service, or an **orchestrator** that creates terminals from named **policies** (container image, CPU, memory, storage, idle timeout, environment variables, lifecycle). It gives the model commands such as `run_command`, file tools, a working directory and, optionally, an instruction text | `backend/open_webui/utils/terminals.py:20-35`; `backend/open_webui/routers/configs.py:355-401`; `src/lib/components/AddTerminalServerModal.svelte:585-863` |
| **System terminal** / **direct terminal** | A system terminal is configured by an admin and reached through `/api/v1/terminals/{id}`; a direct terminal is a person's own and reached from the browser (the server only tries to read its `AGENTS.md` and skills). Only one terminal is active in a chat at a time | `src/lib/apis/terminal/index.ts:95-114`; `backend/open_webui/utils/terminals.py:168-186`; `src/lib/i18n/locales/en-US/translation.json:3045` |
| **Terminal contexts** | For orchestrator terminals, whether chats and automations get a **Shared** terminal, one **Per chat** / **Per automation**, or none (**Off**). Per-chat terminals need a saved chat | `backend/open_webui/utils/terminals.py:38-113`; `src/lib/components/AddTerminalServerModal.svelte:607-640` |
| **Chat Uploads** | Terminal setting: **Default** or **Filesystem**. With **Filesystem**, a file attached in the composer while that terminal is selected is copied into the terminal's working directory instead of MedIT GPT's file storage (a failure shows `Failed to upload file.`) | `backend/open_webui/utils/terminals.py:116-119`; `src/lib/components/AddTerminalServerModal.svelte:565-583`; `src/lib/components/chat/MessageInput.svelte:899-990` |
| **Working directory** | The terminal's current folder for this chat. For admin terminals the server reads it before each reply and adds it to the description of `run_command`; the Files panel uses the same per-chat folder | `backend/open_webui/utils/tools.py:1209-1229`, `:1426-1442`; `src/lib/apis/terminal/index.ts:186-203` |
| **AGENTS.md** | If the terminal user's home folder holds an `AGENTS.md` file (up to 32 KB), its text is added to the conversation each turn | `backend/open_webui/utils/terminals.py:15`, `:189-244`; `backend/open_webui/utils/middleware.py:3086-3091` |
| **Terminal dock** | The bar at the bottom of the Files panel: a **Shell** tab (interactive) and one read-only tab per command the model ran | `src/lib/components/chat/TerminalDock.svelte:164-292`; `src/lib/components/chat/XTerminal.svelte:50-111` |
| **Access grants** | The sharing list on a tool (rows in `access_grant`) or on an admin server (inside its connection settings). Empty means private: owner-only for a tool, admin-only for a server | `backend/open_webui/models/tools.py:101-102`; `backend/open_webui/utils/access_control/__init__.py:151-179` |
| **Community sharing** | When the `ui.enable_community_sharing` setting is on, the Tools page shows a **Discover a tool** link and the row menu offers **Share**, which opens openwebui.com and sends it the tool, code included (`Redirecting you to Open WebUI Community`) | `src/lib/components/workspace/Tools.svelte:185-210`, `:637-643`; `src/lib/components/workspace/Tools/ToolMenu.svelte:71-83`; `backend/open_webui/main.py:2369` |

## 5. Workflows (Step by Step)

### 5.1 Using Tools in a Chat (Any User)

1. **Open the menu.** In the message box, click the button with the tooltip `Integrations`. It is
   shown only when something can be switched on: at least one tool or tool server is listed for the
   person, or skills, filters, web search, image generation or the code interpreter apply
   (`src/lib/components/chat/MessageInput.svelte:816-817`, `:2295-2344`).
2. **Choose Tools.** The first row reads **Tools** with a count; it appears only when the person
   has at least one tool. Inside, a search box (`Search tools`) and one row per tool with a switch.
   The list combines, in this order, workspace tools the person can read, admin OpenAPI servers,
   enabled admin MCP servers (all filtered by access) and the person's own direct servers
   (`src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:126-166`, `:314-335`, `:523-654`;
   `backend/open_webui/routers/tools.py:67-191`). With nothing to show: `No tools found`.
3. **Switch tools on.** Each switch adds the tool to this chat's selection. A wrench chip with the
   number of selected tools appears beside the menu (tooltip `{COUNT} Available Tools`); clicking it
   opens **Available Tools**, listing each selected tool and its functions, with `Auth required` or
   `Connected` beside OAuth tools (`src/lib/components/chat/MessageInput.svelte:2366-2386`;
   `src/lib/components/chat/ToolServersModal.svelte:19-107`).
4. **Tools needing a sign-in.** An OAuth 2.1 MCP tool the person has not connected is shown dimmed;
   choosing it, or the amber chip `Click to connect`, starts that tool's sign-in instead of
   selecting it. The full flow, including errors, is in `sso-oauth-oidc-and-scim.md` section 5.13
   (`src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:244-258`, `:559-562`).
5. **Model defaults.** If the chosen model has default tools (set by whoever manages the model;
   see `workspace-models-and-model-access.md`), they are selected automatically in a new chat,
   except unconnected OAuth tools, which become amber chips and may send the browser to the
   tool's sign-in once (`src/lib/components/chat/Chat.svelte:1029-1054`, `:951-968`).
6. **Send.** The browser sends the selected workspace and admin server tools as `tool_ids` and the
   person's own servers as `tool_servers` (`src/lib/components/chat/Chat.svelte:3551-3605`). The
   server loads the tools the person may use, connects to any selected MCP servers, and offers
   all their functions to the model; the model decides whether to call them. How calls, approvals
   and the tool loop work, and how a call is displayed, is in
   `chat-completion-pipeline-and-generation-tasks.md` (sections 5.3 and 5.6)
   (`backend/open_webui/utils/middleware.py:2945-3094`).

The selection belongs to the composer, not to the account: it is reset for a new chat and
re-filled from the model's defaults (`src/lib/components/chat/Chat.svelte:969-975`, `:1029-1054`).

### 5.2 Setting Your Own User Valves

Some tools ask each person for their own settings (user valves), for example a personal key for a
service the tool calls.

1. In the composer, open **Integrations > Tools**. A tool that has user valves shows a knob icon
   (tooltip `Valves`) beside its switch, for admins and for users with `chat.valves` (default on)
   (`src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:625-644`).
2. Click the knob. The **Valves** window lists each setting with its description. A setting showing
   `Default` uses the tool author's default; click `Default` to switch it to `Custom` and type a
   value (required settings show `*required` and `None` instead of `Default`). Switches show
   `Enabled` or `Disabled`; secret fields are masked
   (`src/lib/components/common/Valves.svelte:24-243`).
3. Click **Save**: `Valves updated successfully`. If the tool has no user valves the window reads
   `No valves` (`src/lib/components/workspace/common/ValvesModal.svelte:96-99`, `:162-213`;
   `src/lib/components/common/Valves.svelte:241-243`).
4. Alternatively, open the chat **Controls** panel, **Valves** section: choose **Tools**, then
   `Select a tool`. Changes there save by themselves and show `Valves updated`
   (`src/lib/components/chat/Controls/Valves.svelte:76-100`, `:155-187`). Admin tool servers do not
   appear in that list (`:182-184`).

User valves are saved per person and per tool and are applied each time the tool runs for that
person (`backend/open_webui/models/tools.py:270-309`; `backend/open_webui/utils/tools.py:317-320`).
The values a person types (which may be personal keys) are stored with their settings; whether
they are encrypted depends on a server setting (section 14).

### 5.3 Creating a Workspace Tool (Tool Authors)

Only admins and users with `workspace.tools` reach this screen (section 3).

1. Go to **Workspace > Tools** and choose **Create** (`src/lib/components/workspace/Tools.svelte:83-87`).
2. Fill in **Tool Name**, **Tool ID** (suggested from the name; letters, digits and underscores)
   and **Tool Description**. Name and description are required: saving without them shows
   `Name and description are required`
   (`src/lib/components/workspace/Tools/ToolkitEditor.svelte:167-172`, `:250-301`).
3. Write or paste the Python code. A new tool starts from an example template. If the code begins
   with a frontmatter block, its `title` and `description` fill empty name and description fields
   (`src/lib/components/workspace/Tools/ToolkitEditor.svelte:60-165`, `:333-345`). Below the editor:
   `Warning:` `Tools can execute arbitrary code.` `Only install tools from sources you trust.`
   (`:355-363`).
4. Optionally click **Access** to share it (section 5.5).
5. Click **Save & Create**. A confirmation lists `Please carefully review the following warnings:`,
   `Tools have a function calling system that allows arbitrary code execution.` and
   `Do not install tools from sources you do not fully trust.`, followed by an acknowledgement
   paragraph; confirm to continue (`src/lib/components/workspace/Tools/ToolkitEditor.svelte:231-237`,
   `:380-404`). The editor tidies the Python formatting first; if that fails, the code is saved as
   typed (`:187-204`).
6. The browser checks `required_open_webui_version`: if the tool needs a newer version than this
   one, it stops with `Open WebUI version (v{OPEN_WEBUI_VERSION}) is lower than required version
   (v{REQUIRED_VERSION})` (`src/routes/(app)/workspace/tools/create/+page.svelte:17-36`).
7. **On the server** (`backend/open_webui/routers/tools.py:346-427`): the ID is checked and lower-cased;
   sharing grants the person may not set are removed; any `requirements` are installed with `pip`
   (this can take a long time); the code is **loaded and run** to find the `Tools` class; the list of
   functions is generated from the class; the tool is stored; a per-tool cache folder is created
   under `DATA_DIR/cache/tools/`; and the `tool.created` event is published
   (`backend/open_webui/utils/plugin.py:206-256`; `backend/open_webui/config.py:182`).
8. Success shows `Tool created successfully` and returns to the list
   (`src/routes/(app)/workspace/tools/create/+page.svelte:49-54`). A failure shows the server's
   message in a red pop-up (section 10).

### 5.4 Editing, Cloning, Importing, Exporting and Deleting Tools

| Task | Steps | Result and messages | Source |
|---|---|---|---|
| **Edit** | Click a tool row you can edit (or row menu **Edit**); change fields or code; **Save** | `Tool updated successfully`; the editor stays open. The server reloads the code on every save, reinstalls any new requirements and regenerates the function list | `src/routes/(app)/workspace/tools/edit/+page.svelte:17-55`; `backend/open_webui/routers/tools.py:528-563` |
| **Clone** | Row menu **Clone** | Opens the create editor pre-filled with ID `{id}_clone` and name `{name} (Clone)`; nothing is saved until **Save & Create** | `src/lib/components/workspace/Tools.svelte:212-226`; `src/lib/components/workspace/Tools/ToolMenu.svelte:85-96` |
| **Import From Link** (admins) | **Import From Link**, paste the address of a Python file (GitHub file and folder links are converted to the raw file), **Import** | `Tool imported successfully` appears as soon as the code is fetched, then the create editor opens pre-filled; the tool is **not saved** until the admin completes 5.3 | `src/lib/components/workspace/Tools.svelte:306-318`; `src/lib/components/ImportModal.svelte:22-61`; `backend/open_webui/routers/tools.py:247-308` |
| **Import JSON** | **Import JSON**, pick a `.json` export, confirm the warning dialog (same warnings as 5.3) | Each tool in the file is created in turn; a failing one shows its own red pop-up, and `Tool imported successfully` is shown at the end even if some failed | `src/lib/components/workspace/Tools.svelte:321-332`, `:666-708` |
| **Export JSON** / row **Export** | **Export JSON** (all tools you can write) or row menu **Export** (one tool) | Downloads `tools-export-{time}.json` or `tool-{id}-export-{time}.json`, **including the code** | `src/lib/components/workspace/Tools.svelte:102-119`, `:228-240`; `backend/open_webui/routers/tools.py:316-338` |
| **Delete** | Row menu **Delete**, confirm `Delete tool?` / `This will delete {name}.`; holding **Shift** shows a bin icon that deletes **without** confirmation | `Tool deleted successfully`. The tool row and its sharing grants are removed; nothing else is cleaned up (people's saved user valves for it stay in their settings) | `src/lib/components/workspace/Tools.svelte:242-252`, `:513-530`, `:645-656`; `backend/open_webui/models/tools.py:326-335`; `backend/open_webui/routers/tools.py:675-689` |
| **Share to the community** | Row menu **Share** (only when community sharing is on) | `Redirecting you to Open WebUI Community`; a new tab opens openwebui.com and receives the tool, code included | `src/lib/components/workspace/Tools.svelte:185-210`; `src/lib/components/workspace/Tools/ToolMenu.svelte:71-83` |

### 5.5 Sharing a Workspace Tool

1. In the tool editor click **Access**. The **Access Control** dialog offers **Private**, **Public**
   (`Accessible to all users`) and an **Access List** of people and groups with **Read** or
   **Write** (`src/lib/components/workspace/Tools/ToolkitEditor.svelte:207-225`, `:309-313`;
   `src/lib/components/workspace/common/AccessControl.svelte:520-700`).
2. For an existing tool the change is saved at once (`Saved`); for a new tool it is saved with the
   tool (`src/lib/components/workspace/Tools/ToolkitEditor.svelte:215-224`).
3. **Read** lets people use the tool in chats and set their own user valves; **Write** also lets
   them edit it, see its code, set its admin valves and delete it (section 3.1).
4. Grants the person is not allowed to set are dropped silently by the server (section 3.1).

### 5.6 Setting a Tool's Admin Valves

1. On **Workspace > Tools**, click the gear icon (tooltip `Valves`) on the tool's row
   (`src/lib/components/workspace/Tools.svelte:549-581`).
2. Fill in the form as in 5.2 and click **Save**: `Valves updated successfully`. If loading fails
   the window closes with `Error fetching valves`
   (`src/lib/components/workspace/common/ValvesModal.svelte:52-155`).
3. The server checks the values against the tool's `Valves` class; a value of the wrong kind
   is refused with `[ERROR: Error updating tool valves]` (`backend/open_webui/routers/tools.py:825-842`).
4. Admin valves are shared by everyone using the tool and are applied each time it runs
   (`backend/open_webui/utils/tools.py:313-316`).

### 5.7 Admin: Adding an OpenAPI Tool Server

1. Open **Settings > Admin > Integrations**. In the **Tools** section, next to **External Tool
   Servers**, click **+** (tooltip `Add Connection`)
   (`src/lib/components/admin/Settings/Integrations.svelte:189-210`).
2. The **Add Connection** dialog opens with **Type** `OpenAPI`. Fill in **Name**, optionally **ID**
   (placeholder `auto`; it may not contain `:` or `|`), **Description** and **URL** (placeholder
   `API Base URL`; a trailing slash is removed). The switch beside the URL enables or disables the
   server (`src/lib/components/AddToolServerModal.svelte:489-682`, `:330-343`).
3. Choose **Auth**: `None` (`No authentication`), `Bearer` (an **API Key** field), `Session`
   (`Forwards system user session credentials to authenticate`) or `OAuth`
   (`Forwards system user OAuth access token to authenticate`) (`:749-818`).
4. Under **Advanced** (optional): **Forward cookies** (`Forward cookies from your Open WebUI request
   to this server.`), **OpenAPI Spec** as **URL** (default `openapi.json`, relative to the URL or a
   full address; the dialog shows `WebUI will make requests to "{url}"`) or pasted **JSON**,
   **Headers** as a JSON object, and the **Function Name Filter List** (`:824-1032`).
5. Click the circular-arrows icon (tooltip `Verify Connection`). The server fetches the
   specification with the chosen auth and headers: `Connection successful` or `Connection failed`
   (`src/lib/components/AddToolServerModal.svelte:161-238`;
   `backend/open_webui/routers/configs.py:641-680`).
6. Click **Access Control** and add the people or groups (or public access) who should use it.
   **Without grants only admins can use the server** (section 3.1)
   (`src/lib/components/AddToolServerModal.svelte:845-853`, `:1092`).
7. Click **Save**. The whole list is saved at once (`Connections saved successfully`, or
   `Failed to save connections`) and the server immediately re-fetches every enabled OpenAPI
   specification (section 8) (`src/lib/components/admin/Settings/Integrations.svelte:72-88`;
   `backend/open_webui/routers/configs.py:240-298`).
8. Users see the server in **Integrations > Tools** after their page reloads its tool list. The
   dialog always sends the **Name** and **Description** fields, and the code uses them in place of
   the specification's own title and description even when they are empty, so a server saved with
   an empty Name is listed with a blank name (read from code, not observed)
   (`src/lib/components/AddToolServerModal.svelte:395-398`;
   `backend/open_webui/routers/tools.py:104-132`; `backend/open_webui/utils/tools.py:1596-1604`;
   `src/lib/utils/localizedContent.ts:35-44`).

Each saved connection appears as a row with a gear (tooltip `Configure`, opening **Edit
Connection**) and an `Enabled`/`Disabled` switch; a disabled row is dimmed. **Delete** in the edit
dialog asks `Are you sure you want to delete this connection? This action cannot be undone.`
(`src/lib/components/chat/Settings/Tools/Connection.svelte:21-94`;
`src/lib/components/AddToolServerModal.svelte:1055-1104`). The dialog's **Export** downloads
`tool-server-{id}.json`, which **includes the API key**; treat it as a secret and never attach it
to a ticket. **Import** reads such a file into the dialog (`Import successful`)
(`src/lib/components/AddToolServerModal.svelte:240-328`).

### 5.8 Admin: Adding an MCP Tool Server

As 5.7, with these differences.

1. Click the **Type** value to switch it to `MCP` (shown with `Streamable HTTP`). MCP over
   Streamable HTTP is the only MCP transport offered
   (`src/lib/components/AddToolServerModal.svelte:553-567`; `backend/open_webui/utils/mcp/client.py:64-86`).
2. **ID** is required for MCP. The URL keeps a trailing slash if typed, because some MCP servers
   need it (`src/lib/components/AddToolServerModal.svelte:333-338`, `:599-612`).
3. A yellow warning reads: `Warning:` `MCP support is experimental and its specification changes
   often, which can lead to incompatibilities. OpenAPI specification support is directly maintained
   by the Open WebUI team, making it the more reliable option for compatibility.`
   (`src/lib/components/AddToolServerModal.svelte:1035-1053`).
4. Auth adds `OAuth 2.1` (`Uses OAuth 2.1 Dynamic Client Registration`) and `OAuth 2.1 (Static)`
   (fields **Client ID**, **Client Secret**, **OAuth Server URL**). **Headers**, **OAuth Scopes**
   (placeholder `Use discovered scopes`) and **OAuth Resource Parameter** (`Automatic`, `Include`,
   `Omit`) are under **Advanced**; there is no specification field or cookie forwarding for MCP
   (`:756-818`, `:943-1010`).
5. **Verify** connects to the MCP server and lists its tools (`Connection successful` or
   `Connection failed`). For the OAuth 2.1 types the icon's tooltip is `Check OAuth Discovery` and it
   only fetches the sign-in service's discovery document (`OAuth discovery successful`)
   (`src/lib/components/AddToolServerModal.svelte:82-89`; `backend/open_webui/routers/configs.py:557-640`).
6. **OAuth 2.1 only: register before saving.** Click **Register Client**. Success shows
   `Registration successful` and the warning `Please save the connection to persist the OAuth client
   information and do not change the ID`; the badge changes from `Not Registered` to `Registered`.
   Failure shows only `Registration failed`. Saving an unregistered OAuth 2.1 server is refused with
   `Please register the OAuth client`. Static registration needs the client ID and secret first
   (`Please enter Client ID and Client Secret`) (`src/lib/components/AddToolServerModal.svelte:109-159`,
   `:345-349`, `:693-745`; `backend/open_webui/routers/configs.py:172-209`).
7. After saving, reopen the server: **Authorize OAuth** lets the admin test the sign-in with their
   own account (before saving its tooltip reads `Please save the connection before authorizing
   OAuth`) (`src/lib/components/AddToolServerModal.svelte:91-107`, `:695-711`).
8. Grant access (step 6 of 5.7) and save. Each person then connects their own account the first
   time they use the tool (`sso-oauth-oidc-and-scim.md` section 5.13).

Unlike OpenAPI servers, MCP servers are **not** cached: for every chat message that uses one, the
MedIT GPT server connects to it, lists its tools, and disconnects when the reply ends. The connect
handshake must finish within `MCP_INITIALIZE_TIMEOUT` seconds (default 10)
(`backend/open_webui/utils/middleware.py:2340-2387`, `:2959-3015`; `backend/open_webui/main.py:1723-1745`;
`backend/open_webui/env.py:696-703`).

### 5.9 A User Adding Their Own (Direct) Tool Server

Available only with the **Direct Integrations** switch on and the `features.direct_tool_servers`
permission (section 3.1).

1. Open **Settings > Integrations**. Under **External Tool Servers** (`Connect to your own OpenAPI
   compatible external tool servers.`) click **+** (`Add Connection`)
   (`src/lib/components/chat/Settings/Integrations.svelte:108-131`;
   `src/lib/i18n/locales/en-US/translation.json:3041-3044`).
2. The dialog is the OpenAPI dialog without ID, headers, cookie forwarding, filter list or access
   control; **Auth** offers `None`, `Bearer` and `Session` (`src/lib/components/AddToolServerModal.svelte:553-572`,
   `:594`, `:761-767`, `:845`, `:984`, `:1013`).
3. **Verify** is done by the browser itself: `Connection successful` or `Connection failed`
   (`src/lib/components/AddToolServerModal.svelte:193-204`).
4. **Save** stores the server in the person's settings (`Settings saved successfully!`), then the
   browser fetches its specification; a failure shows `Failed to connect to {URL} OpenAPI tool
   server` (`src/lib/components/chat/SettingsModal.svelte:818-824`;
   `src/lib/components/chat/Settings/Integrations.svelte:43-59`).
5. The tab reminds the person: `Connections managed through the Admin Panel are recommended for
   everyday use. Direct connections provide convenient access to your own endpoints, but rely on
   your browser session to keep requests running, making them better suited to testing and
   temporary use.` and `CORS must be properly configured by the provider to allow requests from
   Open WebUI.` (`src/lib/components/chat/Settings/Integrations.svelte:166-183`).

Because the browser makes the calls, a direct server works only while that browser tab is open and
connected, and only if the browser can reach it; no code path in this area has MedIT GPT's server
call a direct tool server (`src/routes/+layout.svelte:500-554`;
`backend/open_webui/utils/middleware.py:3360-3374`). A person's own **terminal** is the exception:
before each reply the server itself tries to read that terminal's `AGENTS.md`, and it can also
read the terminal's skills (another area); the `AGENTS.md` read fails silently if only the
browser can reach the terminal (`backend/open_webui/utils/terminals.py:168-186`, `:189-236`, `:247-268`;
`backend/open_webui/utils/middleware.py:2880-2890`, `:3086-3091`). Every time
the app loads, the browser re-fetches each direct server's specification and shows `Failed to
connect to {URL} OpenAPI tool server` for each one that fails (`src/routes/(app)/+layout.svelte:92-105`).

### 5.10 Admin: Adding a Terminal Server

1. **Settings > Admin > Integrations**, **Terminal** section, next to **Open Terminal**, click
   **+** (`src/lib/components/admin/Settings/Integrations.svelte:239-258`).
2. In **Add Terminal Connection** enter **Name** (placeholder `My Terminal`), optional **ID** and
   **URL** (placeholder `http://localhost:9900`) (`src/lib/components/AddTerminalServerModal.svelte:429-513`).
3. Click the verify icon (`Verify Connection`). The server probes the address and reports the type:
   `Connected (Orchestrator)` or `Connected (Terminal)`; otherwise `Server connection failed`
   (`src/lib/components/AddTerminalServerModal.svelte:202-257`; `backend/open_webui/routers/configs.py:355-401`).
4. Choose **Chat Uploads** (`Default` or `Filesystem`, section 4) and **Auth** (`None`, `Bearer`
   with **API Key**, `Session`, `OAuth`). **Advanced** holds **Forward cookies** and the **OpenAPI
   Spec** path (default `/openapi.json`) (`:565-583`, `:866-1001`).
5. **Orchestrator only** (an **Orchestrator** fold appears after a successful verify): **Terminal
   Contexts** for **Chat** and **Automation** (`Shared`, `Per chat` or `Per automation`, `Off`),
   **Policy ID**, **Image**, **CPU**, **Memory**, **Storage** (`Ephemeral` or `Persistent` with a
   size), **Idle Timeout** (`min`), **Environment Variables**, **Lifecycle JSON**, and **Refresh
   Terminals** with `Idle only` and `Reset persisted files`. The note reads `Policy changes apply to
   newly provisioned terminals. Refresh matching terminals to apply them to existing terminals.`
   Saving writes the policy to the orchestrator first (`:585-863`, `:356-386`).
6. Click **Access** and grant access; without grants only admins can use the terminal (section 3.1).
7. Click **Save**: `Terminal servers saved` (or `Failed to save terminal servers`)
   (`src/lib/components/admin/Settings/Integrations.svelte:90-117`).
8. **Turn it on.** A new terminal connection is saved **switched off**; flip its switch in the list
   to `Enabled` (`src/lib/components/AddTerminalServerModal.svelte:127-136`, `:406-415`;
   `src/lib/components/admin/Settings/Integrations.svelte:300-314`).

The list notes `Connect to Open Terminal instances. Admins and users granted access can use file
browsing and terminal tools through these servers.` (`src/lib/components/admin/Settings/Integrations.svelte:326-330`).

### 5.11 A User Adding Their Own Terminal

1. **Settings > Integrations**, **Open Terminal** (`Connect to Open Terminal instances to browse
   files and use them as always-on tools. Only one can be active at a time.`), **+**
   (`src/lib/components/chat/Settings/Integrations/Terminals.svelte:53-79`;
   `src/lib/i18n/locales/en-US/translation.json:3045-3047`).
2. Enter **Name**, **URL**, **Chat Uploads** and **Auth** (`None` or `Bearer`); **Verify** is done by
   the browser (`Server connection verified` or `Server connection failed`)
   (`src/lib/components/AddTerminalServerModal.svelte:242-250`, `:966-976`).
3. Turning one terminal's switch on turns the others off
   (`src/lib/components/chat/Settings/Integrations/Terminals.svelte:32-40`).

### 5.12 Using a Terminal in a Chat

1. Click the cloud icon (tooltip `Terminal`) in the composer. The menu lists the person's own
   terminals under **Direct** and admin terminals under **System**; a tick marks the active one;
   choosing it again deselects it. In a temporary chat, admin terminals set to **Per chat** are
   hidden, and admin terminals with the chat context **Off** are not listed
   (`src/lib/components/chat/MessageInput/TerminalMenu.svelte:26-34`, `:146-300`).
2. On wide screens the side panel opens on **Files**, showing the terminal's files
   (`src/lib/components/chat/MessageInput/TerminalMenu.svelte:65-70`, `:89-94`;
   `src/lib/components/chat/ChatControls.svelte:102-110`).
3. The choice is remembered in this browser (not the account) and a model can name a default
   terminal (`src/routes/(app)/+layout.svelte:237`, `:393-395`;
   `src/lib/components/chat/Chat.svelte:1108-1114`).
4. When the message is sent, the model is offered the terminal's functions. For an admin terminal
   the server reads the terminal's **working directory** for this chat before each reply and adds
   it to the description of `run_command`; for either kind, the terminal's own instructions and any
   `AGENTS.md` from the terminal user's home folder are added to the conversation
   (`backend/open_webui/utils/tools.py:1357-1470`; `backend/open_webui/utils/middleware.py:3036-3091`).
5. **Terminal dock.** At the bottom of the Files panel, a bar labelled **Terminal** (with the number
   of running commands) expands into tabs: **Shell** opens an interactive shell; each command the
   model ran appears as its own read-only tab (hover shows the command and `Running`,
   `Exit {code}` or `Unavailable`). Buttons: `Close terminal`, `Open terminal`, `Dismiss`,
   `Expand terminal` / `Collapse terminal` (`src/lib/components/chat/TerminalDock.svelte:164-292`).
6. **The model and the open shell.** If the terminal server provides the functions
   `read_user_terminal` and `send_user_terminal_input`, the model is offered them only while the
   person has the **Shell** tab open in that chat (the browser is asked first); with the shell open
   the model can therefore read it and type into it
   (`backend/open_webui/utils/middleware.py:3140-3182`; `src/routes/+layout.svelte:562-574`).
7. If the shell's connection ends, the shell prints `[Connection closed]`; if it cannot connect,
   `[Terminal connection failed]` or the error in square brackets
   (`src/lib/components/chat/XTerminal.svelte:96-110`).
8. For admin terminals, access is re-checked about every 10 seconds while a shell is open; disabling
   the terminal or removing the person's access closes it
   (`backend/open_webui/routers/terminals.py:431-447`).

The selector is disabled while a reply is being written (`src/lib/components/chat/MessageInput.svelte:2563-2569`).
If the selected terminal is no longer available (removed, disabled or access withdrawn), the
selection is cleared once the page has reloaded its terminal list
(`src/lib/components/chat/Chat.svelte:984-998`; `src/routes/(app)/+layout.svelte:107-147`).

### 5.13 What Happens When the Model Calls a Tool

| Kind | Who makes the call | Timeout | What the model receives on failure | Source |
|---|---|---|---|---|
| Workspace tool | The MedIT GPT server runs the tool's Python method in-process, with the tool's valves and the person's user valves | None set by this area | The error text, as the tool result | `backend/open_webui/utils/tools.py:283-370`; `backend/open_webui/utils/middleware.py:6016-6027` (native mode), `:1460-1466` (legacy mode), `:3376-3386` (a call resumed after approval) |
| Admin OpenAPI server | The MedIT GPT server sends an HTTP request built from the specification, with the connection's auth and headers | `AIOHTTP_CLIENT_TIMEOUT_TOOL_SERVER` (defaults to `AIOHTTP_CLIENT_TIMEOUT`, which is unset by default) | `HTTP error {status}: {text}` or the connection error | `backend/open_webui/utils/tools.py:1620-1782`; `backend/open_webui/env.py:608-612`, `:686-694` |
| Admin MCP server | The MedIT GPT server, over the MCP session opened for this message | The same tool-server timeout | The MCP error content | `backend/open_webui/utils/mcp/client.py:115-129`; `backend/open_webui/utils/middleware.py:2982-2992` |
| Direct (own) server or terminal | The person's **browser**, asked by the server over the live connection | 10 seconds to fetch a specification; none for calls | `Tool Server Not Found`, `HTTP error! Status: {status}. Message: {text}`, or, when a call paused for approval is resumed without a connected browser, `Error: Browser session is not connected for this direct tool.` | `src/routes/+layout.svelte:500-554`; `src/lib/apis/index.ts:6`, `:541-716`; `backend/open_webui/utils/middleware.py:6004-6015`, `:1448-1460`, `:3360-3374` |
| Admin terminal | The MedIT GPT server, through the terminal pass-through | As admin OpenAPI servers | As admin OpenAPI servers | `backend/open_webui/utils/tools.py:1434-1470` |

Results come back into the conversation and the model continues; how a call is shown on screen is
covered in `builtin-native-tools.md` and `chat-composer-and-message-display.md`.

## 6. Data Model

Support staff do not query these stores; this section explains where things live so an
escalation can name them. Timestamps are epoch seconds (`../tools/ground-truth.md`, Time).

### 6.1 The `tool` Table (Workspace Tools)

| Column | Type | Meaning | Source |
|---|---|---|---|
| `id` | text, primary key | The tool ID (lower case, letters, digits, underscores) | `backend/open_webui/models/tools.py:24`; `backend/open_webui/routers/tools.py:368-374` |
| `user_id` | text, indexed | The owner's user id. Deleting a user does not delete their tools (`../tools/ground-truth.md`, Accounts); the list then shows the owner as `Deleted User` | `backend/open_webui/models/tools.py:25`; `src/lib/components/workspace/Tools.svelte:497-511` |
| `name` | text | Display name | `backend/open_webui/models/tools.py:26` |
| `content` | text | The Python source code | `backend/open_webui/models/tools.py:27` |
| `specs` | JSON | The list of functions generated from the code at the last save | `backend/open_webui/models/tools.py:28`; `backend/open_webui/routers/tools.py:395-396`, `:537-550` |
| `meta` | JSON | `description`, `manifest` (frontmatter), `has_user_valves`, and `i18n` (translated name and description) | `backend/open_webui/models/tools.py:29`, `:36-40` |
| `valves` | JSON | The admin valves (encrypted only when a server setting enables it; section 14) | `backend/open_webui/models/tools.py:30`, `:248-268` |
| `updated_at`, `created_at` | integer | Modification and creation times; the list sorts by `updated_at` | `backend/open_webui/models/tools.py:32-33`, `:188` |

Sharing is held in the `access_grant` table with resource type `tool` (who: a user, a group or
everyone (`*`); permission `read` or `write`). Deleting a tool removes its grants
(`backend/open_webui/models/tools.py:101-102`, `:136`, `:326-335`). The table is created by the
migrations (`../tools/inventory.md`).

### 6.2 Data Kept With Each Person's Settings

| What | Where | Source |
|---|---|---|
| User valves for each tool | The person's settings record, under `tools.valves.{tool id}` (encrypted only when a server setting enables it; section 14) | `backend/open_webui/models/tools.py:270-309` |
| Their own (direct) tool servers | The person's interface settings, `toolServers` (removed by the server if the person lacks `features.direct_tool_servers`) | `src/lib/components/chat/Settings/Integrations.svelte:43-47`; `src/lib/components/chat/SettingsModal.svelte:438-444`; `backend/open_webui/routers/users.py:520-530` |
| Their own terminals | The person's interface settings, `terminalServers` | `src/lib/components/chat/Settings/Integrations.svelte:43-47` |
| Connections to OAuth 2.1 MCP tools | The `oauth_session` table, one row per person and tool server (`mcp:{server id}`); see `sso-oauth-oidc-and-scim.md` section 6.3 | `backend/open_webui/routers/tools.py:142-148` |
| Which terminal is selected | The browser only (`localStorage.selectedTerminalId`), not the account | `src/routes/(app)/+layout.svelte:237`, `:393-395` |

### 6.3 Settings Rows (the `config` Table)

| Key | What it holds | Source |
|---|---|---|
| `tool_server.connections` | The list of admin tool servers. Each entry has `type` (`openapi` or `mcp`), `url`, `path`, `spec_type` and `spec`, `auth_type`, `headers`, `forward_cookies`, `config` (`enable`, `function_name_filter_list`, `access_grants`) and `info` (`id`, `name`, `description`, and OAuth details for OAuth 2.1 servers). Entries also carry the server's credentials (an API key, or OAuth client information); these are secrets and are included in the admin settings export | `backend/open_webui/routers/configs.py:217-263`; `src/lib/components/AddToolServerModal.svelte:377-414`; `backend/open_webui/config.py:2833` |
| `terminal_server.connections` | The list of admin terminals: `id`, `name`, `enabled`, `url`, `path`, `auth_type`, `forward_cookies`, `config` (`access_grants`, `contexts`, `chat_uploads`), `server_type`, `policy_id`, and the credential (a secret) | `backend/open_webui/routers/configs.py:301-352`; `src/lib/components/AddTerminalServerModal.svelte:388-419`; `backend/open_webui/config.py:2835` |
| `direct.integrations.enable` | The **Direct Integrations** switch | `backend/open_webui/config.py:2824`; `backend/open_webui/routers/configs.py:40-44` |
| `user.permissions` | Default permissions, including the keys in section 3.2 | `../tools/ground-truth.md`, Accounts |

Older saves that used an `access_control` field are converted to `access_grants` at start-up
(`backend/open_webui/main.py:621-629`). An orchestrator's policies are stored on the orchestrator,
not in MedIT GPT (`backend/open_webui/routers/configs.py:430-501`).

### 6.4 Memory, Cache and Disk (Not in the Database)

| Store | Content | Lifetime | Source |
|---|---|---|---|
| Loaded tool code, per server process | Each workspace tool's loaded module and the code it was loaded from | Until the process restarts; reloaded whenever the stored code differs | `backend/open_webui/utils/plugin.py:318-372`; `backend/open_webui/utils/tools.py:301-307` |
| Tool-server specification cache | Every enabled admin OpenAPI server's specification and function list (`TOOL_SERVERS`), and the same for terminals (`TERMINAL_SERVERS`); with Redis also under `{REDIS_KEY_PREFIX}:tool_servers` and `:terminal_servers` | See section 8 | `backend/open_webui/main.py:580`, `:588`; `backend/open_webui/utils/tools.py:1170-1206`, `:1271-1354` |
| `DATA_DIR/cache/tools/{tool id}/` | A folder created for each tool when it is created (for the tool's own use); not removed when the tool is deleted | Permanent | `backend/open_webui/routers/tools.py:398-399`; `backend/open_webui/config.py:182` |
| Installed Python packages | Packages named in tools' `requirements`, installed into the server's Python environment | Until the environment is rebuilt (for example a new container) | `backend/open_webui/utils/plugin.py:422-450` |

### 6.5 Personal Data in This Area

- The Tools list shows each tool owner's name, with their email address on hover
  (`src/lib/components/workspace/Tools.svelte:497-511`).
- Tool code and exported tool files can contain anything an author typed, including keys; exported
  connection files include the server's API key (section 5.7).
- Workspace tools receive the person's user details when they run (the template's example function
  reads the name, ID and email), and admin valves and user valves can hold keys
  (`src/lib/components/workspace/Tools/ToolkitEditor.svelte:71-92`; `backend/open_webui/utils/tools.py:309-320`).
- Admin tool servers and terminals receive data about the person: the code sends admin terminals
  the person's MedIT GPT user ID on each request (`X-User-Id`) and the chat ID when there is one
  (`X-Session-Id`); custom headers can
  insert placeholders such as `{{USER_NAME}}`, `{{USER_EMAIL}}` and `{{USER_ID}}`; and with
  `ENABLE_FORWARD_USER_INFO_HEADERS` on (default off) tool servers receive the name, ID, email and
  role (`backend/open_webui/utils/tools.py:1397`, `:1415-1417`; `backend/open_webui/routers/terminals.py:152-156`;
  `backend/open_webui/utils/headers.py:52-80`, `:135-147`; `backend/open_webui/env.py:989-997`).
- Whatever the model sends to a tool (often parts of the conversation) leaves MedIT GPT when the
  tool is an external server or a terminal. The local data may contain personal and health
  information (`_research-prompt.md`, rule 8); which external servers are approved to receive
  such data is **TO BE CONFIRMED** with the Privacy Office.

## 7. Settings and Configuration

Code defaults are what the repository says; the live value of every setting below is data (the
`config` table or the environment) and is **TO BE CONFIRMED** for production. After first boot a
stored setting wins over its environment variable (`../tools/ground-truth.md`, Settings).

### 7.1 Settings Changed on Screens

| Setting | Screen | Stored as | Code default | Takes effect | Source |
|---|---|---|---|---|---|
| Admin tool servers (all fields in 5.7 and 5.8) | Admin > Integrations > Tools | `tool_server.connections` | from `TOOL_SERVER_CONNECTIONS`, else empty | At save: the specification cache is rebuilt by the process that handled the save; OAuth clients are re-registered in that process | `backend/open_webui/routers/configs.py:240-298`; `backend/open_webui/config.py:381-388`, `:2833` |
| Admin terminals (all fields in 5.10) | Admin > Integrations > Terminal | `terminal_server.connections` | from `TERMINAL_SERVER_CONNECTIONS`, else empty | At save (cache rebuilt); a new entry is saved disabled | `backend/open_webui/routers/configs.py:331-352`; `backend/open_webui/config.py:396-398`, `:2835` |
| **Direct Integrations** (`Show the Integrations tab for users with permission to manage their own tool and terminal connections, including admins. Hiding it does not disable existing connections.`) | Admin > Integrations > **User Connections** | `direct.integrations.enable` | off (`ENABLE_DIRECT_INTEGRATIONS`) | At once (`Connections settings updated`) | `src/lib/components/admin/Settings/Integrations.svelte:61-70`, `:343-357`; `backend/open_webui/config.py:231`, `:2824`; `src/lib/i18n/locales/en-US/translation.json:2173-2174`, `:2181` |
| Tool permissions (section 3.2) | Admin > Users > Groups and default permissions | `user.permissions` and group records | section 3.2 | At once | `users-groups-roles-and-permissions.md` |
| Tool valves / user valves | Workspace > Tools (gear) / composer or Controls | `tool.valves` / the person's settings | the tool author's defaults | Next time the tool runs | sections 5.2 and 5.6 |
| A person's own tool servers and terminals | Settings > Integrations | the person's settings (`toolServers`, `terminalServers`) | none | At save, in that person's browsers after reload | section 5.9 |
| A model's default tools, default terminal and `terminal` capability | Workspace > Models (another area) | the model record | capability `terminal` on | New chats | `src/lib/components/chat/Chat.svelte:1029-1054`, `:1108-1114`; `src/lib/components/chat/MessageInput.svelte:796-800`; `workspace-models-and-model-access.md` |
| **Show Files on Terminal Select** (`Open the file browser after selecting a terminal.`), **Terminal File Display** (`Choose where terminal display_file results appear by default.`; `Sidebar` or `Inline`) and **Terminal Preview Allow Same Origin** (`Allow terminal previews to access same-origin browser APIs.`) | Settings > Interface (see `user-settings-and-personalisation.md`) | the person's settings | Show Files on; display Sidebar | At once | `src/lib/components/common/InterfaceSettings.svelte:40-41`, `:1430-1494`; `src/lib/components/chat/MessageInput/TerminalMenu.svelte:68-70`; `src/lib/i18n/locales/en-US/translation.json:2973-2974`, `:2981-2984` |

### 7.2 Environment-Only Settings

| Variable | Code default | Effect | Source |
|---|---|---|---|
| `ENABLE_PLUGINS` | `True` | Off: Workspace > Tools is hidden, workspace tools are neither listed nor loaded, and start-up dependency installation is skipped | `backend/open_webui/env.py:1186`; `backend/open_webui/routers/tools.py:81`, `:201-202`; `backend/open_webui/utils/plugin.py:207-208`, `:461-463` |
| `ENABLE_PIP_INSTALL_FRONTMATTER_REQUIREMENTS` | `True` | Off: `requirements` lines are ignored (a tool needing a missing package then fails to load) | `backend/open_webui/env.py:1188-1190`; `backend/open_webui/utils/plugin.py:424-426` |
| `PIP_OPTIONS`, `PIP_PACKAGE_INDEX_OPTIONS` | empty | Extra options passed to `pip` (for example a package index) | `backend/open_webui/env.py:1192-1193`; `backend/open_webui/utils/plugin.py:441-443` |
| `OFFLINE_MODE` | `false` | On: requirement installation is skipped | `backend/open_webui/env.py:1201`; `backend/open_webui/utils/plugin.py:428-430` |
| `SAFE_MODE` | `False` | On: all **functions** are deactivated at start-up. Workspace tools are not affected | `backend/open_webui/env.py:965`; `backend/open_webui/main.py:382-383` |
| `TOOL_SERVER_CONNECTIONS` | `[]` | JSON seed for `tool_server.connections` (first boot only); invalid JSON is logged and ignored | `backend/open_webui/config.py:381-388` |
| `TERMINAL_SERVER_CONNECTIONS` | `[]` | JSON seed for `terminal_server.connections`. Unlike the tool-server seed, a parse error here is not caught (read from code; the effect on start-up was not observed) | `backend/open_webui/config.py:396-398` |
| `TERMINAL_PROXY_HEADERS` | `{}` | Extra response headers added to everything passed back from admin terminals; invalid JSON is ignored | `backend/open_webui/config.py:400-403`; `backend/open_webui/routers/terminals.py:214-215` |
| `AIOHTTP_CLIENT_TIMEOUT_TOOL_SERVER_DATA` | `10` (seconds) | Time limit for fetching an OpenAPI specification | `backend/open_webui/env.py:665-669`; `backend/open_webui/utils/tools.py:1484` |
| `AIOHTTP_CLIENT_TIMEOUT_TOOL_SERVER` | falls back to `AIOHTTP_CLIENT_TIMEOUT` (unset, so no limit) | Time limit for each call to an admin OpenAPI or MCP server | `backend/open_webui/env.py:608-612`, `:686-694`; `backend/open_webui/utils/tools.py:1722-1724`; `backend/open_webui/utils/mcp/client.py:35-38` |
| `MCP_INITIALIZE_TIMEOUT` | `10` (seconds) | Time limit for the MCP connect handshake | `backend/open_webui/env.py:696-703`; `backend/open_webui/utils/mcp/client.py:81-82` |
| `AIOHTTP_CLIENT_SESSION_TOOL_SERVER_SSL` | `True` | Certificate checking for tool-server specifications and calls, MCP and terminal `AGENTS.md` reads; accepts a CA bundle path. Keep verification on | `backend/open_webui/env.py:578-604`, `:681-684`; `backend/open_webui/utils/tools.py:1486`, `:1733`; `backend/open_webui/utils/mcp/client.py:46-52` |
| `AIOHTTP_CLIENT_SESSION_SSL` | `True` | Certificate checking for the admin dialogs' OAuth discovery check and terminal check, the terminal pass-through and the terminal working-directory and instruction reads (a different setting from the one above, so the two can disagree) | `backend/open_webui/env.py:631`; `backend/open_webui/routers/configs.py:381`, `:572`; `backend/open_webui/routers/terminals.py:204`; `backend/open_webui/utils/tools.py:1222`, `:1251` |
| `AIOHTTP_CLIENT_ALLOW_REDIRECTS` | `False` | Whether calls to OpenAPI tool servers follow redirects (the MCP client is set to follow them) | `backend/open_webui/env.py:637`; `backend/open_webui/utils/tools.py:1734`; `backend/open_webui/utils/mcp/client.py:31-34` |
| `ENABLE_FORWARD_USER_INFO_HEADERS` (and the `FORWARD_*` header names) | `False` | On: admin tool servers receive the person's name, ID, email and role, plus chat and message IDs | `backend/open_webui/env.py:989-997`; `backend/open_webui/utils/tools.py:176-182` |
| `BYPASS_ADMIN_ACCESS_CONTROL` | on | Admins see all tools and admin servers (section 3.1) | `backend/open_webui/config.py:2086-2092` |
| `ENABLE_VALVE_ENCRYPTION` | `False` | Whether tool and function valves (admin and user) are stored encrypted. Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca); see section 14 | `backend/open_webui/env.py:767`; `backend/open_webui/utils/valves.py:21-24` |
| `ENABLE_DIRECT_INTEGRATIONS`, `USER_PERMISSIONS_*` | see 7.1 and 3.2 | Seeds for the stored settings | `backend/open_webui/config.py:231`, `:1745-1905` |
| `REDIS_URL`, `REDIS_KEY_PREFIX` (default `open-webui`) | none | With Redis, the specification caches are shared between processes under `{REDIS_KEY_PREFIX}:tool_servers` and `:terminal_servers` | `backend/open_webui/env.py:384`; `backend/open_webui/utils/tools.py:1178-1183`, `:1325-1328` |
| `OAUTH_CLIENT_TIMEOUT` | empty | Time limit for OAuth 2.1 tool sign-in services; see `sso-oauth-oidc-and-scim.md` section 7.9 | `backend/open_webui/config.py:390` |

The terminal pass-through has its own fixed limits (300 seconds per request, 10 seconds to
connect), the working-directory read 5 seconds and the instruction read 3 seconds
(`backend/open_webui/routers/terminals.py:190-193`; `backend/open_webui/utils/tools.py:1218`, `:1246`).

## 8. Cron Jobs and Background Processes

There is no crontab and nothing in this area runs on a schedule on the server; the only
server-side timer is the access re-check on an open terminal shell (8.3). The rest of the work
below happens at start-up, at save time, or per request.

### 8.1 At Start-Up (Each Server Process)

| Step | What happens | If it fails | Source |
|---|---|---|---|
| Convert old sharing data, register OAuth clients | Old `access_control` entries in `tool_server.connections` become `access_grants`; each OAuth 2.1 MCP server's client is loaded so people can connect | Log `Error adding OAuth client for MCP tool server {server_id}: InvalidToken. Stored OAuth client data is invalid; reconnect this tool server.` or `Error adding OAuth client for MCP tool server {server_id}: {error}`; that server's sign-in fails until an admin re-registers it (`sso-oauth-oidc-and-scim.md` 11.17) | `backend/open_webui/main.py:621-661` |
| Install dependencies (**blocking**, before serving) | Log `Installing external dependencies of functions and tools...`. The `requirements` of every active function and of every tool **owned by an admin** are collected and installed with `pip` in one go. Tools owned by non-admins are skipped here | Log `Error installing packages: {packages}` and `Error installing requirements: {e}`; start-up **continues** | `backend/open_webui/main.py:384-388`; `backend/open_webui/utils/plugin.py:422-484` |
| Later, at first use | Each server process remembers which packages it has installed. The first time a process loads a tool (for example when it is first used in a chat after a restart), that tool's `requirements` are installed again if not yet done by that process, and the chat waits for `pip` | The reply's error box shows the error text, for example Python's own message about a missing module (section 11.4) | `backend/open_webui/utils/plugin.py:220-225`, `:419-447`; `backend/open_webui/utils/tools.py:301-307`; `backend/open_webui/main.py:1686-1713` |
| Pre-fetch specifications | Only when at least one admin tool server exists: log `Initializing tool servers...`, fetch every enabled OpenAPI specification (log `Initialized {n} tool server(s)`), then every enabled terminal's (log `Initialized {n} terminal server(s)`). When no tool server exists, terminals are fetched on first use instead | Log `Failed to initialize tool servers at startup: {e}` / `Failed to initialize terminal servers at startup: {e}`; a single unreachable server is just left out (log `Failed to connect to {url} OpenAPI tool server`) | `backend/open_webui/main.py:431-460`; `backend/open_webui/utils/tools.py:1519-1617` |

`SAFE_MODE` deactivates functions only; it does not stop tools from loading
(`backend/open_webui/main.py:382-383`). With `ENABLE_PLUGINS` off the dependency step logs
`ENABLE_PLUGINS is disabled, skipping tool and function dependencies.`
(`backend/open_webui/utils/plugin.py:461-463`).

### 8.2 The Tool-Server Specification Cache

| Situation | Behaviour | Source |
|---|---|---|
| **With Redis** | The list is kept in Redis under `{REDIS_KEY_PREFIX}:tool_servers` (and `:terminal_servers`), shared by all processes and kept **without expiry**. Each list is rebuilt only at start-up (when an admin tool server exists) and when an admin saves that list (the tool-server list or the terminal list); an empty terminal list is also refetched when enabled terminals exist. A change in a server's own specification (new or renamed functions) is therefore not seen until one of those happens | `backend/open_webui/utils/tools.py:1170-1206`, `:1325-1354`; `backend/open_webui/routers/configs.py:265`, `:342` |
| **Without Redis** | Each process keeps its own copy, but every request that needs the list (the tools list in the composer, and each `server:` tool in a chat message) fetches every enabled specification again, waiting up to the 10-second specification time limit per server (servers are fetched in parallel) | `backend/open_webui/utils/tools.py:1188-1206`, `:389-392`; `backend/open_webui/routers/tools.py:106` |
| A server cannot be reached or returns something that is not an OpenAPI document | It is left out of the list (logs `Failed to connect to {url} OpenAPI tool server` or `Invalid OpenAPI spec from {url}: missing 'paths'`); users simply no longer see it | `backend/open_webui/utils/tools.py:1578-1586` |
| Redis cannot be read or written | Logs `Error fetching tool_servers from Redis: {e}` or `Error caching tool_servers to Redis: {e}`; the process falls back to fetching | `backend/open_webui/utils/tools.py:1177-1183`, `:1191-1198` |

The background specification fetch sends only a **Bearer** key: it does not send custom headers,
session or OAuth tokens. A server whose specification requires those can pass **Verify** (which
does send them) yet be missing from users' menus (`backend/open_webui/utils/tools.py:1528-1554`;
`backend/open_webui/routers/configs.py:641-672`).

MCP servers are not cached: they are contacted for each chat message that uses them (section 5.8).
Workspace tools are reloaded in a process whenever their stored code differs from the copy that
process loaded (`backend/open_webui/utils/tools.py:301-307`).

### 8.3 Per Session and in the Browser

| Activity | Interval | Source |
|---|---|---|
| Re-checking a person's access to an open admin terminal shell | about every 10 seconds | `backend/open_webui/routers/terminals.py:431-447` |
| The terminal dock asking the terminal for the model's running commands | every second while the page is visible | `src/lib/components/chat/TerminalDock.svelte:45-99`, `:145-161` |
| Keep-alive message on an open shell | every 25 seconds | `src/lib/components/chat/XTerminal.svelte:87-89` |
| Fetching the person's own tool servers' specifications | at each app load and each save in Settings > Integrations | `src/routes/(app)/+layout.svelte:92-148`, `:239-242`; `src/lib/components/chat/Settings/Integrations.svelte:43-59` |
| OAuth token refresh for OAuth 2.1 tools | when a token is needed; see `sso-oauth-oidc-and-scim.md` section 8 | `backend/open_webui/routers/tools.py:146-148` |

## 9. Notifications and Emails

**No email** is sent by anything in this area; the application has no mail-sending code
(`../tools/ground-truth.md`, Contacts). People learn of results through pop-ups (section 10), the
reply's error box, and the tool-call display in the conversation.

### 9.1 Events Published (Webhooks and Event Functions)

Each action below publishes an event. Events go to admin **event webhooks** that subscribe to
them and to active **Event** functions; none of these events is sent to users' own notification
targets (only chat, channel, calendar and file-processing events are)
(`backend/open_webui/events.py:669-675`, `:1069-1087`, `:1166-1171`). A webhook message reads as
the event's message followed by the subject in brackets, for example `Tool created (my_tool)`
(`backend/open_webui/events.py:1034-1059`). Each payload names the person who acted (ID, name,
email and role), so webhook receivers handle personal data (`backend/open_webui/events.py:704`,
`:1027`). How webhooks are configured belongs to the notifications area.

| Event | Message | Published when | Source |
|---|---|---|---|
| `tool.created` | `Tool created` | A workspace tool is created (data: its name) | `backend/open_webui/events.py:504-505`; `backend/open_webui/routers/tools.py:401-408` |
| `tool.updated` | `Tool updated` | A tool is saved | `backend/open_webui/events.py:507-508`; `backend/open_webui/routers/tools.py:555-562` |
| `tool.deleted` | `Tool deleted` | A tool is deleted | `backend/open_webui/events.py:510-511`; `backend/open_webui/routers/tools.py:676-687` |
| `tool.access_updated` | `Tool access updated` | A tool's sharing is changed from the Access dialog | `backend/open_webui/events.py:513-514`; `backend/open_webui/routers/tools.py:627-636` |
| `tool.valves_updated` | `Tool valves updated` | Admin valves saved, or a person saved their user valves (data `scope: user`) | `backend/open_webui/events.py:516-517`; `backend/open_webui/routers/tools.py:830-835`, `:969-975` |
| `config.tool_servers.updated` | `Config Tool Servers updated` | The admin tool-server list is saved (data: count and types) | `backend/open_webui/events.py:73-77`; `backend/open_webui/routers/configs.py:290-297` |
| `config.terminal_servers.updated` | `Config Terminal Servers updated` | The admin terminal list is saved | `backend/open_webui/events.py:78-82`; `backend/open_webui/routers/configs.py:344-351` |
| `terminal.session.opened` / `terminal.session.closed` | `Terminal Session opened` / `Terminal Session closed` | An interactive shell to an admin terminal opens or closes (data: the terminal's ID) | `backend/open_webui/events.py:650-655`; `backend/open_webui/routers/terminals.py:391-399`, `:459-467` |

### 9.2 Socket Messages Used by This Area

| Message | Direction and purpose | Source |
|---|---|---|
| `execute:tool` | The server asks the person's browser to call one of their own (direct) tool servers or terminals and waits for the answer | `backend/open_webui/utils/middleware.py:6004-6015`; `src/routes/+layout.svelte:638-645` |
| `request:terminal:state` | Before a reply, the server asks (waiting up to 2 seconds) whether this browser has an open shell for the chat's terminal; only then does it offer the model the terminal's shell functions (section 5.12) | `backend/open_webui/utils/middleware.py:3140-3182`; `src/routes/+layout.svelte:562-574` |
| `chat:message:error` | Carries `Failed to connect to MCP server '{server_id}'` and terminal errors into the reply's error box | `backend/open_webui/utils/middleware.py:3005-3014`; `backend/open_webui/main.py:1702-1709` |

Browser (desktop) notifications are not raised by this area.

## 10. Error, Warning and Notice Messages (Verbatim)

How messages reach people: on the Tools pages and in the valves windows, a server `detail` is
shown as a red pop-up with exactly that text (`src/lib/apis/tools/index.ts:17-28` and the same
pattern for every call; `src/lib/components/workspace/Tools.svelte:106-108`). If the server's
answer carries no `detail` (for example a dropped connection or an error page from a proxy in
front of MedIT GPT), these calls show **nothing** and the page simply does not change. Errors
during a chat appear in the reply's grey error box (`chat-completion-pipeline-and-generation-tasks.md`
section 5.8). The admin tool-server and terminal dialogs replace most server texts with their own
generic messages (10.4). Placeholders are written `{name}`.

### 10.1 Messages From the Server Shown to People

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `401 Unauthorized` | Error | `backend/open_webui/routers/tools.py:328-331` (export), `:363-366` (create), `:512-515` and `:523-526` (update), `:614-617` (access), `:670-673` (delete); text `backend/open_webui/constants.py:69` | The person lacks the permission or the write access for that action (section 3.1) | Ask the tool's owner or an admin | Which permission applies (section 3.2); whether the person has write access |
| `Only alphanumeric characters and underscores are allowed in the id` | Error | `backend/open_webui/routers/tools.py:368-372` | Creating a tool whose ID contains other characters (spaces, hyphens, dots) | Change the Tool ID | None |
| `Uh-oh! This id is already registered. Please choose another id string.` | Error | `backend/open_webui/routers/tools.py:423-427`; `backend/open_webui/constants.py:54` | Creating a tool with an ID already used by any tool, including ones the person cannot see | Choose another ID | None |
| `[ERROR: Error creating tool]` | Error | `backend/open_webui/routers/tools.py:415-422`; `backend/open_webui/constants.py:16-23` | The code could not be loaded when saving a new tool: a Python error, no `Tools` class, a missing module, or a failed package installation | Author fixes the code; ask an admin about packages | Server log around the time: `Failed to load the tool by id {form_data.id}: {e}` and `Error loading module: {tool_id}: {e}` give the real cause |
| `[ERROR: Error creating tools]` | Error | `backend/open_webui/routers/tools.py:410-414` | The tool was checked but could not be stored | Retry once | Log `Error creating a new tool: {e}`; database health |
| `[ERROR: Error updating tool]` | Error | `backend/open_webui/routers/tools.py:570-576` | Saving changed code that cannot be loaded (same causes as creating) | Author fixes the code | As for creating |
| `[ERROR: Error updating tools]` | Error | `backend/open_webui/routers/tools.py:564-568` | The update could not be stored | Retry once | Database health |
| `[ERROR: The server is out of storage space.]`, `[ERROR: Server storage quota exceeded.]`, `[ERROR: Server storage is not writable.]`, `[ERROR: File name is too long.]` | Error | `backend/open_webui/constants.py:6-20` (used by every `[ERROR: …]` message above and below) | A storage error on the server while creating or saving a tool or valves | Escalate | Disk space and permissions of the server |
| `We could not find what you're looking for :/` | Error | `backend/open_webui/routers/tools.py:473-476`, `:494-498`, `:597-601`, `:653-657`, `:702-706`, `:747-751`, `:794-798`, `:818-822`, `:855-859`, `:895-899`, `:937-941`, `:984-987`; `backend/open_webui/constants.py:78` | The tool no longer exists (deleted, or a stale link), or valves were saved for a tool that declares none | Refresh the page | Whether the tool still exists |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error | `backend/open_webui/routers/tools.py:467-471`, `:719-722`, `:764-767`, `:811-814`, `:872-875`, `:912-915`, `:954-957`; `backend/open_webui/constants.py:70-72` | Opening a tool, or its valves, without the needed read or write access; also any admin-only address used by a non-admin (`../tools/ground-truth.md`) | Ask the owner or an admin for access | The tool's Access list |
| `[ERROR: Error getting tool valves]`, `[ERROR: Error getting tool user valves]` | Error | `backend/open_webui/routers/tools.py:724-731`, `:877-884` | Reading saved valves failed. The valves window itself shows `Error fetching valves` instead (10.2) | Retry | Log `Error getting tool valves by id {id}` |
| `[ERROR: Error updating tool valves]` | Error | `backend/open_webui/routers/tools.py:825-842` | A valve value is not of the kind the tool expects (for example text where a number is needed) | Correct the value | Log `Failed to update tool valves by id {id}: {e}` |
| `[ERROR: Error updating tool user valves]` | Error | `backend/open_webui/routers/tools.py:964-982` | As above, for a person's own valves | Correct the value | Log `Failed to update user valves by id {id}: {e}` |
| `Please enter a valid URL` | Error | `backend/open_webui/routers/tools.py:270-272` | **Import From Link** with an empty address (the dialog normally catches this first) | Enter the address | None |
| `Failed to fetch the tool` | Error | `backend/open_webui/routers/tools.py:290-294` | The web address answered with an error status (the status is passed on) | Check the link | Whether the address is reachable from the server |
| `No data received from the URL` | Error | `backend/open_webui/routers/tools.py:295-297` | The address returned an empty file | Check the link | None |
| `[ERROR: Error fetching tool]` | Error | `backend/open_webui/routers/tools.py:302-308` | Network failure or time-out fetching the address | Retry; check the link | Outbound access from the server |
| `Failed to connect to MCP server '{server_id}'` | Error | `backend/open_webui/utils/middleware.py:3005-3014` | During a chat, connecting to a selected MCP server or listing its tools failed (unreachable, handshake over `MCP_INITIALIZE_TIMEOUT`, refused sign-in). The reply continues without that server's tools. `{server_id}` is the server's ID, not its name | Retry later; reconnect the tool if it uses OAuth | Server reachable from MedIT GPT; for OAuth tools see `sso-oauth-oidc-and-scim.md` 11.17 |
| `Terminal unavailable: Terminal server '{terminal_id}' is disabled` | Error | `backend/open_webui/utils/middleware.py:3061-3063`; `backend/open_webui/utils/tools.py:1377-1378` | The chat's selected admin terminal was switched off | Choose another terminal | The terminal's switch in Admin > Integrations |
| `Terminal unavailable: Access denied to terminal {terminal_id}` | Error | `backend/open_webui/utils/tools.py:1380-1382` (shown through `backend/open_webui/utils/middleware.py:3061-3063`) | The person no longer has access to the selected admin terminal | Ask an admin | The terminal's Access list |
| `Terminal unavailable: Terminal server '{terminal_id}' is unavailable` | Error | `backend/open_webui/utils/tools.py:1384-1388` (as above) | The terminal's specification could not be loaded (server down or unreachable when the list was built) | Retry later | Terminal server health; section 8.2 |
| `Terminal unavailable: Terminal server '{terminal_id}' has no available tools` | Error | `backend/open_webui/utils/tools.py:1390-1392` (as above) | The terminal's specification lists no functions | Escalate | Terminal server version and specification path |
| `Terminal unavailable: Terminal server '{terminal_id}' is not available for {terminal_context}` | Error | `backend/open_webui/utils/tools.py:1410-1413` (as above) | An orchestrator terminal whose **Chat** (or **Automation**) context is **Off** | Choose another terminal | The terminal's Terminal Contexts |
| `Terminal unavailable: Terminal server '{terminal_id}' requires a saved {terminal_context} context` | Error | `backend/open_webui/utils/tools.py:1419-1422` (as above) | A **Per chat** terminal used where there is no saved chat (for example a temporary chat) | Use a normal (saved) chat | None |
| `Terminal unavailable: Terminal server '{terminal_id}' not found` | Error | `backend/open_webui/utils/tools.py:1371-1376` (as above) | The terminal was removed between choosing it and sending (rare: the pipeline checks the terminal list first) | Choose another terminal | Admin terminal list |

### 10.2 Messages From the Browser

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Name and description are required` | Error | `src/lib/components/workspace/Tools/ToolkitEditor.svelte:167-172` | Saving a tool with an empty name or description | Fill both in | None |
| `Please carefully review the following warnings:` / `Tools have a function calling system that allows arbitrary code execution.` / `Do not install tools from sources you do not fully trust.` / `I acknowledge that I have read and I understand the implications of my action. I am aware of the risks associated with executing arbitrary code and I have verified the trustworthiness of the source.` | Warning (confirmation) | `src/lib/components/workspace/Tools/ToolkitEditor.svelte:380-404`; `src/lib/components/workspace/Tools.svelte:690-707` (here the second line is followed by an extra full stop) | **Save & Create** on a new tool, or **Import JSON** | Confirm only for trusted code | None |
| `Warning:` `Tools can execute arbitrary code.` `Only install tools from sources you trust.` | Notice | `src/lib/components/workspace/Tools/ToolkitEditor.svelte:355-363` | Always shown under the code editor | None | None |
| `Open WebUI version (v{OPEN_WEBUI_VERSION}) is lower than required version (v{REQUIRED_VERSION})` | Error | `src/routes/(app)/workspace/tools/create/+page.svelte:20-36`; `src/routes/(app)/workspace/tools/edit/+page.svelte:20-36` | The tool's `required_open_webui_version` is newer than this installation (0.11.4); nothing is saved | Use a version of the tool that supports 0.11.4 | Current version (`../tools/ground-truth.md`) |
| `Tool created successfully` | Success | `src/routes/(app)/workspace/tools/create/+page.svelte:49-54` | New tool saved | None | None |
| `Tool updated successfully` | Success | `src/routes/(app)/workspace/tools/edit/+page.svelte:49-51` | Tool saved | None | None |
| `You do not have permission to edit this tool` | Error | `src/routes/(app)/workspace/tools/edit/+page.svelte:68-72` | Opening the edit address of a tool without write access; returns to the list | Ask the owner for write access | The tool's Access list |
| `Saved` | Success | `src/lib/components/workspace/Tools/ToolkitEditor.svelte:215-220` | Sharing changed on an existing tool | None | None |
| `Tool deleted successfully` | Success | `src/lib/components/workspace/Tools.svelte:242-252` | Tool deleted | None | None |
| `Delete tool?` / `This will delete {name}.` | Warning (confirmation) | `src/lib/components/workspace/Tools.svelte:645-656` | Row menu **Delete** | Confirm or cancel | None |
| `Tool imported successfully` | Success | `src/lib/components/workspace/Tools.svelte:317`, `:681`; `src/lib/components/ImportModal.svelte:37-42` | **Import From Link**: the code was fetched (not yet saved). **Import JSON**: the file was processed, even if some tools failed | Complete the save (link); check for red pop-ups (JSON) | None |
| `Please enter a valid URL` | Error | `src/lib/components/ImportModal.svelte:25-29`; `src/lib/components/AddToolServerModal.svelte:110-113`, `:162-165`; `src/lib/components/AddTerminalServerModal.svelte:204-207`, `:338-341` | An empty address in the import, tool-server or terminal dialog | Enter the address | None |
| `Redirecting you to Open WebUI Community` | Info | `src/lib/components/workspace/Tools.svelte:185-210` | Row menu **Share** (community sharing on); the tool, code included, is sent to openwebui.com | Make sure the tool may be published | Whether community sharing should be on is a governance question (section 14) |
| `No tools found` / `Try adjusting your search or filter to find what you are looking for.` | Notice | `src/lib/components/workspace/Tools.svelte:625-633`; `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:545-547` | No tools match, or the person can see none | Clear the search | Sharing and permissions |
| `Read Only` | Notice | `src/lib/components/workspace/Tools.svelte:475-477` | The person can use but not edit the tool | Ask for write access to edit | None |
| `Deleted User` | Notice | `src/lib/components/workspace/Tools.svelte:497-511` | The tool's owner account no longer exists | None | Ownership is not transferred (`../tools/ground-truth.md`) |
| `Warning: Enabling this will allow users to upload arbitrary code on the server.` | Warning (tooltip) | `src/lib/components/admin/Users/Groups/Permissions.svelte:141-153` | Hovering **Tools Access** in a permissions editor | Grant only to trusted people | None |
| `Valves updated successfully` | Success | `src/lib/components/workspace/common/ValvesModal.svelte:96-99` | Valves saved | None | None |
| `Error fetching valves` | Error | `src/lib/components/workspace/common/ValvesModal.svelte:151-154` | The valves could not be loaded; the window closes. This text is not translated | Retry; report | Whether the tool still loads (an author error in the code) |
| `Valves updated` | Success | `src/lib/components/chat/Controls/Valves.svelte:89-100` | User valves saved from chat Controls | None | None |
| `No valves` | Notice | `src/lib/components/common/Valves.svelte:241-243` | The tool declares no valves of that kind (or they could not be described) | None | None |
| `OAuth session disconnected` | Success | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:606-608` | **Disconnect OAuth** on a connected OAuth tool | None | None |
| `Failed to disconnect` | Error | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:614-616` | Disconnecting failed without an error text (otherwise that text is shown) | Retry | `sso-oauth-oidc-and-scim.md` |
| `Click to connect` | Notice (tooltip on an amber chip) | `src/lib/components/chat/MessageInput.svelte:2546-2559` | The model uses an OAuth tool the person has not connected | Click and sign in | `sso-oauth-oidc-and-scim.md` 11.17 |
| `Please connect all required integrations before sending a message` | Warning | `src/lib/components/chat/Chat.svelte:3130-3133` | Sending while an amber chip is still shown | Connect first | As above |
| `Auth required` / `Connected` | Notice | `src/lib/components/chat/ToolServersModal.svelte:19-32` | Status of a selected OAuth tool in **Available Tools** | Connect if required | None |
| `Failed to connect to {URL} OpenAPI tool server` | Error | `src/routes/(app)/+layout.svelte:93-104`; `src/lib/components/chat/Settings/Integrations.svelte:49-58` | One of the person's own tool servers could not be reached or returned something that is not an OpenAPI document (at app load or on saving) | Check that server; remove it if no longer used | It is the person's own server: support can only confirm the address works from that browser |
| `Failed to connect to {URL} terminal server` | Error | `src/routes/(app)/+layout.svelte:107-141` | One of the person's own enabled terminals could not be reached at app load | Check that terminal | As above |
| `Failed to upload file.` | Error | `src/lib/components/chat/MessageInput.svelte:984-990` | A file attached while a **Filesystem** terminal is selected could not be copied to the terminal | Retry; check the terminal | Terminal health; section 4 |
| `Settings saved successfully!` | Success | `src/lib/components/chat/SettingsModal.svelte:818-824` | Settings > Integrations saved | None | None |
| `Connections managed through the Admin Panel are recommended for everyday use. Direct connections provide convenient access to your own endpoints, but rely on your browser session to keep requests running, making them better suited to testing and temporary use.` / `CORS must be properly configured by the provider to allow requests from Open WebUI.` | Notice | `src/lib/components/chat/Settings/Integrations.svelte:166-183` | Always shown on Settings > Integrations | None | None |
| `No tool server connections configured.` / `No terminal connections configured.` | Notice | `src/lib/components/admin/Settings/Integrations.svelte:227-231`, `:320-324`; `src/lib/components/chat/Settings/Integrations.svelte:147-151`; `src/lib/components/chat/Settings/Integrations/Terminals.svelte:93-97` | Empty lists | None | None |
| `Connections settings updated` | Success | `src/lib/components/admin/Settings/Integrations.svelte:61-69` | **Direct Integrations** switched | None | None |
| `Connections saved successfully` / `Failed to save connections` | Success / Error | `src/lib/components/admin/Settings/Integrations.svelte:77-88` | Admin tool-server list saved / not saved | Retry on failure | Admin session; server log |
| `Terminal servers saved` / `Failed to save terminal servers` | Success / Error | `src/lib/components/admin/Settings/Integrations.svelte:90-99` | Admin terminal list saved / not saved | Retry on failure | As above |
| `Connection successful` / `Connection failed` | Success / Error | `src/lib/components/AddToolServerModal.svelte:193-237` | Tool-server **Verify** worked / did not (any cause; 10.4) | Check address, auth and path | Server log has the detail only at debug level (10.4) |
| `OAuth discovery successful` | Success | `src/lib/components/AddToolServerModal.svelte:86-89`, `:233-235` | **Check OAuth Discovery** found the sign-in service's discovery document | None | None |
| `Please enter a valid ID` | Error | `src/lib/components/AddToolServerModal.svelte:92-95`, `:115-118` | **Register Client** or **Authorize OAuth** without an ID | Enter the ID | None |
| `Please save the connection before authorizing OAuth` | Error / tooltip | `src/lib/components/AddToolServerModal.svelte:97-100`, `:697-701` | **Authorize OAuth** on an unsaved server | Save first | None |
| `Please enter Client ID and Client Secret` | Error | `src/lib/components/AddToolServerModal.svelte:120-123` | **Register Client** for OAuth 2.1 (Static) with an empty field | Fill both | None |
| `Registration failed` | Error | `src/lib/components/AddToolServerModal.svelte:143-146` | Registering with the tool's sign-in service failed; the real reason is hidden (10.4) | Check the URL and, for static, the credentials | `sso-oauth-oidc-and-scim.md` 10.1 |
| `Please save the connection to persist the OAuth client information and do not change the ID` | Warning | `src/lib/components/AddToolServerModal.svelte:148-153` | After a successful registration | Save without changing the ID | None |
| `Registration successful` | Success | `src/lib/components/AddToolServerModal.svelte:154` | As above | None | None |
| `Not Registered` / `Registered` | Notice (badge) | `src/lib/components/AddToolServerModal.svelte:732-744` | OAuth 2.1 registration state | Register if needed | None |
| `Please register the OAuth client` | Error | `src/lib/components/AddToolServerModal.svelte:345-349` | Saving an OAuth 2.1 MCP server that is not registered | Click **Register Client** | None |
| `ID cannot contain ":" or "\|" characters` | Error | `src/lib/components/AddToolServerModal.svelte:339-343` | Saving a tool server whose ID contains `:` or `\|` | Change the ID | None |
| `Please enter a valid JSON spec` | Error | `src/lib/components/AddToolServerModal.svelte:168-171`, `:352-360` | **JSON** specification empty (verify) or not valid JSON (save) | Fix the specification | None |
| `Please enter a valid path` | Error | `src/lib/components/AddToolServerModal.svelte:173-176` | Verifying with an empty specification path | Enter it (default `openapi.json`) | None |
| `Headers must be a valid JSON object` | Error | `src/lib/components/AddToolServerModal.svelte:179-191`, `:363-375` | **Headers** is not a JSON object | Fix the headers | None |
| `Please select a valid JSON file` / `Import successful` | Error / Success | `src/lib/components/AddToolServerModal.svelte:240-291` | Dialog **Import** of a connection file | Choose a valid export | None |
| `Warning:` `MCP support is experimental and its specification changes often, which can lead to incompatibilities. OpenAPI specification support is directly maintained by the Open WebUI team, making it the more reliable option for compatibility.` | Warning | `src/lib/components/AddToolServerModal.svelte:1035-1053` | Type **MCP** chosen | None | None |
| `Are you sure you want to delete this connection? This action cannot be undone.` | Warning (confirmation) | `src/lib/components/AddToolServerModal.svelte:1094-1104`; `src/lib/components/AddTerminalServerModal.svelte:1041-1051` | **Delete** in a tool-server or terminal dialog | Confirm or cancel | None |
| `WebUI will make requests to "{url}"` | Notice | `src/lib/components/AddToolServerModal.svelte:930-937`; `src/lib/components/AddTerminalServerModal.svelte:945-951` | Shows the full specification address | Check it | None |
| `Connected (Orchestrator)` / `Connected (Terminal)` | Success | `src/lib/components/AddTerminalServerModal.svelte:220-226` | Admin terminal **Verify** detected the type | None | None |
| `Server connection failed` | Error | `src/lib/components/AddTerminalServerModal.svelte:238-241`, `:247-249`, `:251-254` | Terminal **Verify** failed (admin or own) | Check the URL and key | Terminal reachable (from the server for admin terminals, from the browser for own ones) |
| `Server connection verified` | Success | `src/lib/components/AddTerminalServerModal.svelte:244-247` | A person's own terminal answered | None | None |
| `Lifecycle JSON must be a JSON object` / `Lifecycle JSON contains invalid JSON` | Error | `src/lib/components/AddTerminalServerModal.svelte:259-271`, `:360-361` | The orchestrator **Lifecycle JSON** is wrong | Fix it | None |
| `Policy ID is required` | Error | `src/lib/components/AddTerminalServerModal.svelte:302-306` | **Refresh Terminals** without a policy | Enter the Policy ID | None |
| `Refresh requested: {count} terminal(s)` / `Failed to refresh terminals: {error}` | Success / Error | `src/lib/components/AddTerminalServerModal.svelte:302-331` | **Refresh Terminals** result | Retry on failure | Orchestrator health |
| `Loading policy...` / `Policy is still loading` | Notice / Error | `src/lib/components/AddTerminalServerModal.svelte:662-663`, `:347-350` | The orchestrator policy is being read; saving is blocked meanwhile | Wait | None |
| `Failed to load policy: {error}` | Error | `src/lib/components/AddTerminalServerModal.svelte:351-354`, `:664-668` | Reading the orchestrator policy failed; saving is blocked | Retry; escalate | Orchestrator reachable from the server |
| `Failed to save policy: {error}` | Error | `src/lib/components/AddTerminalServerModal.svelte:365-385` | Writing the policy to the orchestrator failed; the connection is not saved | Retry; escalate | As above |
| `Policy changes apply to newly provisioned terminals. Refresh matching terminals to apply them to existing terminals.` | Notice | `src/lib/components/AddTerminalServerModal.svelte:849-853` | Orchestrator settings shown | Use **Refresh Terminals** to apply | None |
| `Connect to Open Terminal instances. Admins and users granted access can use file browsing and terminal tools through these servers.` | Notice | `src/lib/components/admin/Settings/Integrations.svelte:326-330` | Admin Terminal section | None | None |
| `Open WebUI can use tools provided by any OpenAPI server.` | Notice | `src/lib/components/chat/ToolServersModal.svelte:114-123` | **Available Tools** when the person has own tool servers | None | None |
| `Show your support!` / `The developers behind this plugin are passionate volunteers from the community. If you find this plugin helpful, please consider contributing to its development.` | Notice | `src/lib/components/workspace/common/ManifestModal.svelte:19`, `:39-43` | The heart **Support** button on a tool with a `funding_url` | None | None |

### 10.3 Text Shown in the Terminal Dock and Tool Results the Model Receives

Tool results are handed to the model, which usually explains the problem in its reply; the
raw text may also be visible in the tool call's details on screen (`builtin-native-tools.md`).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `[Connection closed]` | Notice (in the shell) | `src/lib/components/chat/XTerminal.svelte:96-100` | The shell's connection ended: the terminal closed it, the person's access was removed, the terminal was disabled, or the network dropped. The server's own reason (for example `Access denied`, `Terminal server disabled`, `A saved chat is required for this terminal`) is not displayed | Close and reopen the shell (**Open terminal**) | Terminal enabled and access granted; 10.4 lists the reasons |
| `[Terminal connection failed]` | Error (in the shell) | `src/lib/components/chat/XTerminal.svelte:101-105` | The shell's connection could not be opened | Retry | Terminal reachable |
| `[Error: Terminal request failed ({status})]` | Error (in the shell) | `src/lib/components/chat/XTerminal.svelte:106-110`; `src/lib/apis/terminal/index.ts:116-131` | Creating the shell session was refused; `{status}` is the HTTP status (for example 403, 409 or 502; see 10.4) | Retry; check the chat is saved for per-chat terminals | Status meaning in 10.4 |
| `Error: Terminal request failed ({status})` | Error (red line in the dock) | `src/lib/components/chat/TerminalDock.svelte:94-96`, `:261-264`; `src/lib/apis/terminal/index.ts:130` | Listing or reading the model's commands failed | As above | As above |
| `[Earlier output omitted]` | Notice | `src/lib/components/chat/TerminalDock.svelte:79` | A command's output was longer than the dock keeps | None | None |
| `Running`, `Exit {exit_code}`, `Unavailable` | Notice (hover on a command tab) | `src/lib/components/chat/TerminalDock.svelte:228` | State of a command the model ran | None | None |
| `HTTP error {status}: {text}` | Error (tool result) | `backend/open_webui/utils/tools.py:1736-1738`, `:1761-1763`, `:1779-1782` | An admin OpenAPI server or admin terminal answered with an HTTP error | Retry; report if repeated | The tool server's own logs; auth settings (an expired key shows 401) |
| `HTTP error! Status: {status}. Message: {resText}` | Error (tool result) | `src/lib/apis/index.ts:680-683`, `:711-715` | One of the person's own servers answered with an HTTP error | Check own server | Not MedIT GPT's server |
| `Tool Server Not Found` | Error (tool result) | `src/routes/+layout.svelte:500-557` | The browser could not match the requested own server (for example it was removed or failed to load at app load) | Reload the page; check Settings > Integrations | None |
| `Error: Browser session is not connected for this direct tool.` | Error (tool result) | `backend/open_webui/utils/middleware.py:3360-3362` | A call to an own server was resumed after approval but no browser tab was connected | Keep the chat open and retry | None |
| `No matching route found for operationId: {name}` / `No matching method found for operationId: {name}` | Error (tool result) | `backend/open_webui/utils/tools.py:1646-1662`; `src/lib/apis/index.ts:563-579` | The cached specification no longer contains that function | Retry after the list is refreshed | Section 8.2 (cache) |
| `Request body expected for operation '{name}' but none found.` | Error (tool result) | `src/lib/apis/index.ts:652-657` | The model called an own server's operation without its inputs | Retry | None |
| `Error: Tool "{name}" not found.` | Error (tool result) | `backend/open_webui/utils/middleware.py:3350-3351`, `:5995-5997` | The model asked for a function that is not in this message's tool list | Retry; check the tool is switched on | None |
| `Error: Tool call arguments must be a JSON object.` | Error (tool result) | `backend/open_webui/utils/middleware.py:3342-3346` | A resumed call had malformed inputs | Retry | None |
| `No result returned from MCP tool call.` | Error (tool result) | `backend/open_webui/utils/mcp/client.py:115-121` | An MCP server returned nothing | Retry | MCP server logs |

### 10.4 Server Texts the Dialogs and the Dock Do Not Show

These details exist in server responses but the page replaces them with the generic text named
in the Trigger column; the debug-level server log may hold the underlying error.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Failed to connect to the tool server` | Error | `backend/open_webui/routers/configs.py:673-680` | OpenAPI **Verify** failed; the dialog shows `Connection failed` | As 10.2 | Address, path, auth |
| `Failed to create MCP client` | Error | `backend/open_webui/routers/configs.py:632-637` | MCP **Verify** failed; shown as `Connection failed` | As 10.2 | Streamable HTTP address, auth, `MCP_INITIALIZE_TIMEOUT` |
| `Failed to fetch OAuth 2.1 discovery document from {discovery_urls}` / `Failed to parse OAuth 2.1 discovery document from {discovery_url}` | Error | `backend/open_webui/routers/configs.py:583-593` | **Check OAuth Discovery** failed; shown as `Connection failed` | Check the server or OAuth Server URL | `sso-oauth-oidc-and-scim.md` |
| `Failed to register OAuth client: {e}` | Error | `backend/open_webui/routers/configs.py:204-209` | **Register Client** failed; shown as `Registration failed` | As 10.2 | As above |
| `Failed to connect to the terminal server` / `Terminal server URL is required` | Error | `backend/open_webui/routers/configs.py:365-367`, `:398-401` | Terminal **Verify** failed; shown as `Server connection failed` | As 10.2 | Terminal reachable from the server |
| `Failed to access policy on terminal server` / `Failed to access lifecycle on terminal server` / `Failed to refresh terminals` | Error | `backend/open_webui/routers/configs.py:460-464`, `:497-501`, `:544-548` | Orchestrator calls failed; shown inside `Failed to load policy: {error}`, `Failed to save policy: {error}` or `Failed to refresh terminals: {error}` | As 10.2 | Orchestrator health |
| `Terminal server '{server_id}' not found` (404) | Error | `backend/open_webui/routers/terminals.py:117-121` | Pass-through to an admin terminal that no longer exists; the dock shows `Terminal request failed (404)` | Choose another terminal | Admin terminal list |
| `Terminal server disabled` (403) | Error | `backend/open_webui/routers/terminals.py:123-124`; WebSocket close reason at `:308-310` | The admin terminal is switched off | As above | Terminal switch |
| `Access denied` (403) | Error | `backend/open_webui/routers/terminals.py:126-128`; WebSocket close reason at `:312-314` | The person has no access to that admin terminal | Ask an admin | Terminal Access list |
| `Terminal server URL not configured` (503) | Error | `backend/open_webui/routers/terminals.py:130-132`; WebSocket close reason at `:341-344` | The admin terminal has no address | Escalate | Terminal settings |
| `Invalid path` (400) / `Path not allowed` (403) | Error | `backend/open_webui/routers/terminals.py:134-147` | A file or command request outside what the pass-through allows | Escalate if seen in normal use | Security-sensitive (section 14) |
| `Terminal server is not available in chats` (403) | Error | `backend/open_webui/routers/terminals.py:157-158`; WebSocket close reason at `:316-318` | The terminal's **Chat** context is **Off** | Choose another terminal | Terminal Contexts |
| `A saved chat is required for this terminal` (409) | Error | `backend/open_webui/routers/terminals.py:160-161`; WebSocket close reason at `:354-356` | A **Per chat** terminal used without a saved chat | Use a saved chat | None |
| `Terminal proxy error: {error}` (502) | Error | `backend/open_webui/routers/terminals.py:242-249` | The terminal could not be reached or timed out (300-second limit) | Retry later | Terminal server health; log `Terminal proxy error: %s` |
| `Expected auth message`, `Auth timeout or invalid payload`, `Invalid token`, `Terminal server not found` | Error (WebSocket close reasons) | `backend/open_webui/routers/terminals.py:266-306` | The shell connection was refused at sign-in; the shell shows `[Connection closed]` | Reload the page; sign in again | Session expiry |

### 10.5 Server Log Lines (Not Shown to Users)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Installing external dependencies of functions and tools...` | Info (log) | `backend/open_webui/main.py:387` | Every start-up | None | Start-up timing |
| `Installing requirements: %s` / `Error installing packages: {packages}` / `Error installing requirements: {e}` | Info / Error (log) | `backend/open_webui/utils/plugin.py:440`, `:446`, `:484` | Package installation started / failed | None | Package index reachable; `PIP_OPTIONS` |
| `ENABLE_PIP_INSTALL_FRONTMATTER_REQUIREMENTS is disabled, skipping installation of requirements.` / `Offline mode enabled, skipping installation of requirements.` / `ENABLE_PLUGINS is disabled, skipping tool and function dependencies.` | Info (log) | `backend/open_webui/utils/plugin.py:424-430`, `:461-463` | Installation switched off | None | Section 7.2 |
| `Error loading module: {tool_id}: {e}` | Error (log) | `backend/open_webui/utils/plugin.py:251-254` | A tool's code failed to load; `{e}` is the real cause (missing module, syntax error, `No Tools class found in the module`) | None | Give `{e}` to the tool author |
| `Failed to load the tool by id {form_data.id}: {e}` | Error (log) | `backend/open_webui/routers/tools.py:417-418` | Creating a tool failed | None | As above |
| `Access denied to tool {tool_id} for user {user.id}` | Warning (log) | `backend/open_webui/utils/tools.py:286-299` | A chat asked for a tool the person cannot read; it was skipped | None | Sharing of the tool |
| `Access denied to tool server {server_id} for user {user.id}` / `Access denied to MCP server {server_id} for user {user.id}` | Warning (log) | `backend/open_webui/utils/tools.py:408-411`; `backend/open_webui/utils/middleware.py:2360-2362` | Same for an admin server; skipped without a message to the person | None | The server's Access Control |
| `Tool server data not found for {server_id}` / `MCP server with id {server_id} not found` | Warning / Error (log) | `backend/open_webui/utils/tools.py:394-396`; `backend/open_webui/utils/middleware.py:2357-2358` | A chat asked for a server that is no longer configured or whose specification is not loaded; skipped silently | None | Admin list; section 8.2 |
| `Tool server index {tool_server_idx} out of range (have {n} connections), skipping server {server_id}` | Warning (log) | `backend/open_webui/utils/tools.py:400-405`; `backend/open_webui/routers/tools.py:109-114` | The cached specification list no longer matches the saved connections | None | Section 8.2 |
| `Tool {function_name} already exists in another tools!` | Warning (log) | `backend/open_webui/utils/tools.py:365-368`, `:468-471` | Two selected tools define a function with the same name; the later one is renamed with its tool or server ID in front | None | None |
| `Failed to connect to {url} OpenAPI tool server` / `Invalid OpenAPI spec from {url}: missing 'paths'` / `Could not fetch tool server spec from {url}: {error}` | Error / Warning (log) | `backend/open_webui/utils/tools.py:1503-1513`, `:1578-1586` | A specification could not be fetched or is not OpenAPI; the server is left out | None | Address and path; section 8.2 |
| `Error fetching tool server data: {e}` / `Failed to load tool servers, skipping: {e}` / `Error caching tool_servers to Redis: {e}` / `Error fetching tool_servers from Redis: {e}` / `Error fetching terminal_servers from Redis: {e}` | Error (log) | `backend/open_webui/utils/tools.py:1171-1206`, `:1336-1349` | Building or caching the list failed | None | Redis health |
| `Initializing tool servers...` / `Initialized %s tool server(s)` / `Initialized %s terminal server(s)` / `Failed to initialize tool servers at startup: {e}` / `Failed to initialize terminal servers at startup: {e}` | Info / Warning (log) | `backend/open_webui/main.py:449-460` | Start-up pre-fetch | None | Counts tell how many servers loaded |
| `Error adding OAuth client for MCP tool server %s: InvalidToken. Stored OAuth client data is invalid; reconnect this tool server.` | Error (log) | `backend/open_webui/main.py:647-651` | Stored OAuth registration unreadable at start-up | None | `sso-oauth-oidc-and-scim.md` 11.17 |
| `API Request Error: {error}` | Warning (log) | `backend/open_webui/utils/tools.py:1779-1782` | A call to an admin OpenAPI server failed | None | The tool server |
| `Error getting OAuth token: {e}` | Error (log) | `backend/open_webui/utils/tools.py:158-169`; `backend/open_webui/routers/terminals.py:171-181` | The person's OAuth token could not be read for a server call | None | `sso-oauth-oidc-and-scim.md` |
| `Failed to decrypt valves: %s` | Warning (log) | `backend/open_webui/utils/valves.py:35-39` | Saved valves could not be read (with valve encryption on, for example after the server's secret key changed); the tool then runs with its default valves | None | Whether the secret key changed (section 11.5) |
| `Failed to update tool valves by id {id}: {e}` / `Failed to update user valves by id {id}: {e}` | Error (log) | `backend/open_webui/routers/tools.py:837-838`, `:977-978` | Valve values rejected | None | `{e}` names the field |
| `Error creating a new tool: {e}` / `Error getting tool valves by id {id}` / `Error getting user values by id {id} and user_id {user_id}: {e}` / `Error updating user valves by id {id} and user_id {user_id}: {e}` | Error (log) | `backend/open_webui/models/tools.py:141-143`, `:253-255`, `:284-286`, `:307-309` | Database or settings read/write failures | None | Database health |
| `options '{options}' not found or not callable on {valves_class.__name__}` / `Method '{options}' did not return a list for {prop_name}` / `Failed to resolve options for {prop_name}: {e}` | Warning (log) | `backend/open_webui/utils/plugin.py:106-135` | A valve's drop-down list could not be built; the field shows without choices | None | Tool author |
| `Terminal proxy error: %s` / `Terminal WebSocket proxy error: %s` / `Terminal access recheck failed` | Error (log) | `backend/open_webui/routers/terminals.py:242-249`, `:436-440`, `:455-456` | Pass-through or shell failures | None | Terminal server health |
| `Skipping terminal AGENTS.md: exceeds %s bytes` | Warning (log) | `backend/open_webui/utils/terminals.py:230-232` | The terminal's `AGENTS.md` is over 32 KB and is ignored | None | None |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it gathers facts, gives guidance and escalates; it does not change tools,
servers, valves, permissions or settings. Who receives escalations for tools, tool servers and
terminals (the "tool-server admin" below) is **TO BE CONFIRMED**. Never ask a person to send an
API key, client secret, exported connection file or tool code that may contain keys.

### 11.1 "I can't find Tools in my Workspace"

**Symptom.** The Workspace has no **Tools** tab, or `/workspace/tools` sends the person to the home
page.

**Likely causes, in order.**
1. The person does not have **Tools Access** (`workspace.tools`), which is off by default; import
   permission alone is not enough for the page (`backend/open_webui/config.py:1745-1746`;
   `src/routes/(app)/workspace/+layout.svelte:94-98`).
2. Plugins are switched off on the server (`ENABLE_PLUGINS`), which hides the page for everyone
   including admins (`src/routes/(app)/workspace/tools/+page.svelte:8-16`).

**Diagnostic steps.** Ask whether the person can use tools in chats (using tools needs no workspace
permission). Ask whether any colleague, or an admin, sees the Tools tab.

**Resolution.** Explain that creating tools runs code on the server and is granted only on request
(section 1). Using tools that others share does not need this permission.

**Escalation.** Send the person's account email, the business reason and, if nobody sees the tab, a
note that plugins may be off. Granting **Tools Access** is an admin decision (section 14).

### 11.2 "A tool I expect isn't in my Integrations menu"

**Symptom.** In **Integrations > Tools** the tool or tool server is missing, the **Tools** row is
absent, or the menu shows `No tools found`.

**Likely causes, in order.**
1. **Not shared with the person.** Workspace tools are private to their owner until shared; admin
   tool servers and terminals with no access grants are visible to admins only
   (`backend/open_webui/utils/access_control/__init__.py:151-179`).
2. The admin tool server is switched off, or its specification could not be fetched (unreachable,
   or it needs headers or a session token that the background fetch does not send), so it is
   silently left out (section 8.2).
3. The person's page has not reloaded its tool list since the change (the list is loaded when the
   app opens) (`src/routes/(app)/+layout.svelte:160-163`).
4. The tool was deleted, or (for MCP) the server is not enabled
   (`backend/open_webui/routers/tools.py:135-136`).
5. An admin OpenAPI server saved with an empty **Name** appears as a blank row rather than missing
   (section 5.7).

**Diagnostic steps.** Ask for the exact tool name, whether colleagues see it, and whether a full
page reload helps. Note the time.

**Resolution.** Ask the person to reload the page. If it is still missing, the owner or an admin
must share it; tier 1 cannot.

**Escalation.** Send the tool or server name, the person's account email, whether others see it,
and the time. Ask the tool-server admin to check the server's **Access Control**, its switch, and
the server log for `Failed to connect to {url} OpenAPI tool server`.

### 11.3 "Saving my tool says '[ERROR: Error creating tool]'"

**Symptom.** **Save & Create** (or **Save**) on a tool shows `[ERROR: Error creating tool]` or
`[ERROR: Error updating tool]`.

**Likely causes, in order.**
1. The Python code has an error, or has no class named `Tools` (`backend/open_webui/utils/plugin.py:246-254`).
2. A package in the `requirements` line could not be installed (no access to the package index,
   installation switched off, or a package that does not exist) (`backend/open_webui/utils/plugin.py:422-447`).
3. The code imports a module that is not installed and not listed in `requirements`.
4. A storage problem on the server (the message would then name it, section 10.1).

**Diagnostic steps.** Ask whether the tool came from a trusted source, whether it worked before, and
whether it lists `requirements`. Record the time of the attempt.

**Resolution.** The author must correct the code; tier 1 does not debug tool code. If the tool
came from a colleague or an admin, refer the person to them.

**Escalation.** Send the tool ID, the time and the exact message to the platform maintainer, who can
read `Error loading module: {tool_id}: {e}` in the server log for the actual cause.

### 11.4 "A tool that used to work now fails"

**Symptom.** After a restart or update of MedIT GPT, using a workspace tool in a chat ends with an
error in the reply's error box (often naming a Python module or a `pip` command), or the first
reply with the tool is very slow.

**Likely causes, in order.**
1. The server's Python environment was rebuilt (for example a new container) and the tool's
   packages are installed again at first use; if that fails (no access to the package index,
   offline mode, installation switched off) the tool cannot load (section 8.1).
2. A newer MedIT GPT version changed something the tool relies on.
3. The tool's code was edited by someone with write access.

**Diagnostic steps.** Ask for the exact error text, the tool name, the time, and whether every
person using the tool is affected.

**Resolution.** Guidance only: try again once (the first use may have been installing packages);
otherwise escalate.

**Escalation.** Send the tool name and ID, the exact error text and the time to the platform
maintainer, mentioning any recent restart or update.

### 11.5 "The tool's settings went back to the defaults"

**Symptom.** A tool behaves as if its valves or the person's user valves were never set; the
**Valves** window shows `Default` everywhere.

**Likely causes, in order.**
1. Someone with write access changed the admin valves.
2. The author renamed or removed a valve in a new version of the tool.
3. Only where valve encryption is switched on (section 14): the server's secret key changed (for
   example during a redeployment), so saved valves can no longer be read and the tool falls back to
   its defaults; the log shows `Failed to decrypt valves: InvalidToken`
   (`backend/open_webui/utils/valves.py:21-41`).

**Diagnostic steps.** Ask whether one person or everyone is affected, and since when.

**Resolution.** The person can re-enter their own user valves (section 5.2). Admin valves need
someone with write access to the tool.

**Escalation.** If several tools or people are affected at once, escalate to the platform
maintainer with the time it started: a key change also affects sign-in sessions and OAuth tool
connections (`sso-oauth-oidc-and-scim.md` 11.17).

### 11.6 "Users can't see the tool server I added" (Admins)

**Symptom.** An admin added a tool server or terminal in Admin > Integrations, it works for the
admin, but users do not see it.

**Likely causes, in order.**
1. **No access grants.** A server or terminal without grants is admin-only
   (`backend/open_webui/utils/access_control/__init__.py:169-174`).
2. **A new terminal is saved switched off** (`src/lib/components/AddTerminalServerModal.svelte:127-136`).
3. The specification needs custom headers or a session/OAuth token to be fetched; **Verify** sends
   them but the background fetch does not, so the server is left out of everyone's list except
   where admin bypass shows it (section 8.2).
4. Users have not reloaded the page.
5. For terminals, the model chosen does not have the `terminal` capability, or (orchestrator) the
   **Chat** context is **Off** (section 3.1).

**Diagnostic steps.** Ask the admin to describe the Access Control setting and the switch state, and
whether a test user reloaded the page.

**Resolution.** Guidance to the admin: add grants (people, groups or public), switch the terminal
on, and save; ask users to reload.

**Escalation.** If grants are set and it still fails, send the server name, type (OpenAPI, MCP or
terminal), auth type (not the key) and the time to the platform maintainer to check the log for
`Failed to connect to {url} OpenAPI tool server` or `Invalid OpenAPI spec from {url}: missing 'paths'`.

### 11.7 "The model says the tool returned an error (for example 'HTTP error 401')"

**Symptom.** The reply explains that a tool failed; the tool call's details show text such as
`HTTP error 401: …`, `HTTP error 500: …` or a connection error.

**Likely causes, in order.**
1. The tool server's credentials expired or were withdrawn (401 or 403).
2. The tool server is down or overloaded (5xx, connection errors).
3. The server's functions changed and the cached specification is out of date (`No matching route
   found for operationId: {name}`; section 8.2).
4. For the person's own servers: the browser could not reach it (`Tool Server Not Found`, `HTTP
   error! Status: …`).

**Diagnostic steps.** Ask for the tool name, the exact error text from the tool call's details, the
time, and whether it fails every time.

**Resolution.** Suggest one retry. For the person's own server, they should check that server.

**Escalation.** For admin servers, send the server name, the exact text (status code), the time and
how often it happens to the tool-server admin.

### 11.8 "It says 'Failed to connect to MCP server …'"

**Symptom.** The reply's error box shows `Failed to connect to MCP server '{server_id}'`; the answer
continues without that server's tools.

**Likely causes, in order.**
1. The MCP server is down or unreachable from the MedIT GPT server.
2. The handshake took longer than `MCP_INITIALIZE_TIMEOUT` (default 10 seconds), common with
   servers that start slowly or have many tools (`backend/open_webui/env.py:696-703`).
3. The server refused MedIT GPT's credentials (expired key, or the person's OAuth connection is no
   longer valid).
4. The address is not a Streamable HTTP MCP endpoint (other MCP transports are not supported), or a
   required trailing slash was removed (`src/lib/components/AddToolServerModal.svelte:333-338`).

**Diagnostic steps.** Note the `{server_id}` shown, the time, and whether everyone or only this
person is affected (OAuth tools are per person).

**Resolution.** Retry once. For OAuth tools, disconnect and reconnect (section 5.1;
`sso-oauth-oidc-and-scim.md` 11.17).

**Escalation.** Send the server ID from the message, the time and how many people are affected to
the tool-server admin.

### 11.9 "Every time I open MedIT GPT it says 'Failed to connect to … OpenAPI tool server'"

**Symptom.** A red pop-up `Failed to connect to {URL} OpenAPI tool server` (or `… terminal server`)
appears at each page load.

**Likely causes, in order.**
1. The person added their own tool server or terminal that is now offline, moved, or reachable only
   from another network (`src/routes/(app)/+layout.svelte:92-148`).
2. The server does not allow requests from the MedIT GPT web address (CORS).
3. Its key changed.

**Diagnostic steps.** Ask the person to open **Settings > Integrations** and read out the address
(not the key) of each listed server.

**Resolution.** The person can switch the entry off or delete it in **Settings > Integrations**; it
is their own setting. Support cannot fix a server it does not run.

**Escalation.** Only if the address is a university-run service: send the address and time to its
owner (TO BE CONFIRMED).

### 11.10 "I can't add my own tool server" or "Settings > Integrations is missing"

**Symptom.** The **Integrations** tab is not in Settings, or tool servers the person added stop
working or disappear from their settings.

**Likely causes, in order.**
1. The admin switch **Direct Integrations** is off (default), which hides the tab for everyone,
   admins included (`src/lib/components/chat/SettingsModal.svelte:385-391`).
2. The person lacks **Direct Tool Servers** (`features.direct_tool_servers`, default off).
3. The permission was removed after servers were added: the server then drops them from saved
   settings and ignores them in chats (`backend/open_webui/routers/users.py:520-530`;
   `backend/open_webui/main.py:1242-1251`).

**Diagnostic steps.** Ask whether the tab ever existed for the person and whether colleagues have it.

**Resolution.** Explain that personal tool servers are an opt-in feature controlled by admins.

**Escalation.** Send the person's account email and the reason to the admins; enabling it is a
governance decision (section 14).

### 11.11 "Registering the OAuth client says 'Registration failed'" (Admins)

**Symptom.** In the MCP dialog, **Register Client** shows `Registration failed`; saving then says
`Please register the OAuth client`.

**Likely causes, in order.**
1. The MCP server or its sign-in service does not support automatic (dynamic) registration; use
   **OAuth 2.1 (Static)** with a client ID and secret from the service instead.
2. Wrong **URL** or **OAuth Server URL**, so the discovery document is not found (try **Check OAuth
   Discovery** first).
3. Wrong static client ID or secret.
4. The sign-in service is unreachable from the MedIT GPT server.

**Diagnostic steps.** Ask which auth type was chosen and whether **Check OAuth Discovery** shows
`OAuth discovery successful`. Do not ask for the secret.

**Resolution.** Guidance only; the admin retries with the corrected details.

**Escalation.** The dialog hides the reason (`backend/open_webui/routers/configs.py:204-209` is not
shown). Send the server URL, auth type and time to the platform maintainer; see also
`sso-oauth-oidc-and-scim.md` 11.18.

### 11.12 "There's no terminal option in the chat"

**Symptom.** The cloud **Terminal** selector is missing from the composer, or the wanted terminal is
not in its list.

**Likely causes, in order.**
1. The selected model has the `terminal` capability switched off
   (`src/lib/components/chat/MessageInput.svelte:796-808`).
2. No admin terminal is shared with the person, or it is switched off (a new terminal is saved off).
3. The terminal's **Chat** context is **Off**, or it is **Per chat** and this is a temporary chat
   (`src/lib/components/chat/MessageInput/TerminalMenu.svelte:28-33`).
4. For the person's own terminals: no direct access, or no terminal added.

**Diagnostic steps.** Ask which model is selected, whether this is a temporary chat, and the name of
the terminal expected.

**Resolution.** Suggest choosing another model or a normal chat. Access is for admins.

**Escalation.** Send the terminal name, model, account email and time to the tool-server admin.

### 11.13 "It says 'Terminal unavailable: …'"

**Symptom.** The reply's error box shows a message beginning `Terminal unavailable:`.

**Likely causes, in order.** Read the rest of the message (section 10.1): the terminal was switched
off (`is disabled`), access was withdrawn (`Access denied to terminal`), the terminal could not be
reached when the list was built (`is unavailable`), its chat context is off (`is not available
for chat`), or a per-chat terminal is used without a saved chat (`requires a saved chat context`).

**Diagnostic steps.** Record the full message, the terminal name and the time; ask whether this is a
temporary chat.

**Resolution.** Deselect the terminal (click it again in the Terminal menu) to keep chatting, or
use a saved chat for per-chat terminals.

**Escalation.** For `is unavailable` or `has no available tools`, send the full text and time to the
tool-server admin.

### 11.14 "The terminal says [Connection closed]"

**Symptom.** The **Shell** tab prints `[Connection closed]` or `[Terminal connection failed]`, or the
dock shows a red `Error: Terminal request failed ({status})` line.

**Likely causes, in order.**
1. The person's access was removed or the terminal was switched off while the shell was open (the
   server re-checks about every 10 seconds) (`backend/open_webui/routers/terminals.py:431-447`).
2. The MedIT GPT session expired (the shell sign-in is refused).
3. The terminal is unreachable or timed out (status 502 in the dock).
4. A per-chat terminal used without a saved chat (status 409).

**Diagnostic steps.** Note the status number if shown, the time, and whether reloading the page and
reopening the shell (**Open terminal**) works.

**Resolution.** Reload and reopen the shell; sign in again if the session expired.

**Escalation.** Send the terminal name, status number, time and account email to the tool-server
admin.

### 11.15 "It said 'Tool imported successfully' but the tool isn't there"

**Symptom.** After **Import From Link**, the pop-up said `Tool imported successfully`, but the Tools
list does not show the tool.

**Likely causes, in order.**
1. **Import From Link** only fetches the code and opens the editor; the tool is saved only after
   **Save & Create** and the confirmation (`src/lib/components/ImportModal.svelte:37-61`).
2. With **Import JSON**, the same message appears after the file is processed even when individual
   tools failed with their own red pop-ups (`src/lib/components/workspace/Tools.svelte:674-681`).

**Diagnostic steps.** Ask whether the editor opened and whether **Save & Create** was clicked; for
JSON imports, ask for any red messages shown before the success message.

**Resolution.** Repeat the import and complete the save; for JSON, handle the reported failures
(for example a duplicate ID, section 10.1).

**Escalation.** Rarely needed; send the messages seen and the time.

### 11.16 "I can't edit this tool" or "It shows Read Only"

**Symptom.** A tool row is greyed and labelled `Read Only`, or opening it shows `You do not have
permission to edit this tool`.

**Likely causes, in order.**
1. The tool is shared with the person for **Read** only (`src/lib/components/workspace/Tools.svelte:430-477`).
2. The person has write access but not **Tools Access**, so changing the code is refused with
   `401 Unauthorized` (`backend/open_webui/routers/tools.py:517-526`).

**Diagnostic steps.** Ask who owns the tool (shown on the row) and what the person needs to change.

**Resolution.** The owner can grant **Write**; code changes also need the permission.

**Escalation.** Usually none: refer the person to the owner shown on the row. If the owner shows as
`Deleted User`, escalate to an admin.

### 11.17 "I clicked Save & Create and nothing happened"

**Symptom.** After confirming the warning, the button stops spinning but no message appears and the
editor stays open.

**Likely causes, in order.**
1. The server took too long (for example installing packages) and a proxy in front of MedIT GPT
   ended the request with a page that carries no error text, which this page does not display
   (`src/lib/apis/tools/index.ts:17-31`; `src/routes/(app)/workspace/tools/create/+page.svelte:38-54`).
2. The connection dropped.

**Diagnostic steps.** Ask the person to check the Tools list: the tool may have been created after
all. Note the time.

**Resolution.** If the tool is listed, open it and check it. If not, retry once.

**Escalation.** Send the tool ID, the time and whether it has `requirements` to the platform
maintainer (proxy time limits are **TO BE CONFIRMED**).

### 11.18 "The tool server's new functions don't show up" (Admins)

**Symptom.** The external tool server was updated with new or renamed functions, but MedIT GPT still
offers the old list, or calls fail with `No matching route found for operationId: {name}`.

**Likely causes, in order.**
1. With Redis, the specification cache does not expire; it is refreshed only at start-up or when an
   admin saves the tool-server list (section 8.2).
2. MCP servers are not affected (they are listed afresh for each message).

**Diagnostic steps.** Ask whether Redis is used (TO BE CONFIRMED for production) and when the list
was last saved.

**Resolution.** Guidance to the admin: open **Admin > Integrations** and click **Save** (no change
needed) to rebuild the cache.

**Escalation.** If saving does not help, send the server name and time to the platform maintainer.

## 12. Local Customisations

**This area matches upstream Open WebUI v0.11.4.** Read-only `git diff main...uoft` and `git diff`
(working tree) over every file in scope (the tools and terminals routers, `routers/configs.py`,
`models/tools.py`, `utils/tools.py`, `utils/mcp/`, `utils/plugin.py`, `utils/valves.py`,
`utils/terminals.py`, the Workspace Tools components and routes, the tool-server and terminal
dialogs, the terminal dock and shell, the integrations and terminal menus, the admin and personal
Integrations panels, the valves components and the `tools`, `terminal` and `configs` API clients)
show no changes.

Two fork changes outside the scope affect what people see when tools run:

| Change | Effect in this area | Source |
|---|---|---|
| The per-person setting **Hide Processing Details** (fork commit; description in the working tree: `Show "Thinking..." instead of status updates, tool calls, reasoning, and code analysis while a response is generated, and keep them hidden afterwards. Tool approval requests and images or embeds from tools still appear.`) | With it on, tool calls and their error details are not displayed, except calls waiting for the person's approval or input. When troubleshooting a tool failure, ask whether it is on: the person may need to turn it off to read the tool's error text | `src/lib/components/common/ToolCallDisplay.svelte:145`, `:181`, `:199` (working tree); `src/lib/components/chat/MessageInput.svelte:1792` (task list hidden); `src/lib/i18n/locales/en-US/translation.json:2923-2924`; `../tools/ground-truth.md` (Fork changes); see `user-settings-and-personalisation.md` |
| Uncommitted change in `src/lib/components/chat/Chat.svelte` | Marks a reply as still running again when a tool call resumes after approval; it does not touch tool selection, OAuth chips or terminals | `src/lib/components/chat/Chat.svelte:2847-2851` (working tree) |

Branding: several messages in this area name the upstream product ("Open WebUI"), for example
`Redirecting you to Open WebUI Community`, the MCP warning, `CORS must be properly configured by
the provider to allow requests from Open WebUI.` and `Open WebUI version (v{OPEN_WEBUI_VERSION}) is
lower than required version (v{REQUIRED_VERSION})`. Their source lines carry licence comments and
were deliberately left unchanged by the fork (`CLAUDE.md`, Conventions;
`src/lib/components/workspace/Tools.svelte:191-194`; `src/lib/components/AddToolServerModal.svelte:1042-1047`;
`src/lib/components/chat/Settings/Integrations.svelte:176-181`;
`src/routes/(app)/workspace/tools/create/+page.svelte:23-34`).

## 13. Source File Index

"Read fully" means the whole file was read for this document; "partial" means only the parts
cited were read.

### 13.1 Backend

| File | Role in this area | Read |
|---|---|---|
| `backend/open_webui/routers/tools.py` | Tools API: list, create, update, share, delete, import from link, export, valves and user valves | Fully |
| `backend/open_webui/models/tools.py` | The `tool` table and its repository; user-valve storage in settings | Fully |
| `backend/open_webui/utils/tools.py` | Loading tools for a chat, tool-server headers, OpenAPI conversion, the specification caches, terminal tools, calling OpenAPI servers | Partial: lines 1-519 and 805-1797; built-in tools (520-804) belong to `builtin-native-tools.md` |
| `backend/open_webui/utils/mcp/client.py` | The MCP client (Streamable HTTP) | Fully |
| `backend/open_webui/utils/plugin.py` | Loading tool code, frontmatter, requirement installation, valve option lists | Fully |
| `backend/open_webui/utils/valves.py` | Valve storage helper (optional encryption) | Fully |
| `backend/open_webui/routers/terminals.py` | Admin terminal list, pass-through and shell connection | Fully |
| `backend/open_webui/utils/terminals.py` | Terminal routing, contexts, chat uploads, `AGENTS.md`, terminal skills | Fully |
| `backend/open_webui/routers/configs.py` | Tool-server, terminal-server, OAuth-client and direct-integration settings endpoints | Partial (lines 1-80, 133-690) |
| `backend/open_webui/config.py` | Tool and terminal settings, permission defaults, `DEFAULT_CONFIG` entries | Partial |
| `backend/open_webui/env.py` | Plugin, pip, time-out, certificate, MCP and forwarding variables | Partial |
| `backend/open_webui/main.py` | Router mounts, start-up steps, OAuth client endpoints, chat-request handling of `tool_servers` and errors | Partial |
| `backend/open_webui/utils/middleware.py` | MCP connection per message, tool resolution, terminal tools, tool execution paths | Partial (lines 1334-1470, 2330-2387, 2930-3200, 3322-3410, 5985-6030) |
| `backend/open_webui/utils/access_control/__init__.py` | Connection access and grant filtering | Partial |
| `backend/open_webui/constants.py` | Error texts | Partial |
| `backend/open_webui/events.py` | Event definitions and delivery | Partial |
| `backend/open_webui/utils/headers.py` | Custom header placeholders and user-info forwarding | Partial |
| `backend/open_webui/routers/users.py` | Dropping saved tool servers without permission | Partial (lines 505-540) |

### 13.2 Front End

| File | Role in this area | Read |
|---|---|---|
| `src/lib/components/workspace/Tools.svelte` | Workspace Tools list, import, export, share, delete | Fully |
| `src/lib/components/workspace/Tools/ToolkitEditor.svelte` | Tool editor and warnings | Fully |
| `src/lib/components/workspace/Tools/ToolMenu.svelte` | Row menu | Fully |
| `src/lib/components/workspace/Tools/AddToolMenu.svelte` | A create menu not used by any page in this version | Fully |
| `src/routes/(app)/workspace/tools/+page.svelte`, `create/+page.svelte`, `edit/+page.svelte` | Tools routes | Fully |
| `src/routes/(app)/workspace/+layout.svelte` | Workspace tab gating | Partial |
| `src/lib/components/AddToolServerModal.svelte` | Tool-server dialog (admin and direct) | Fully |
| `src/lib/components/AddTerminalServerModal.svelte` | Terminal dialog (admin and direct) | Fully |
| `src/lib/components/admin/Settings/Integrations.svelte` | Admin Integrations panel | Fully |
| `src/lib/components/chat/Settings/Integrations.svelte` | Personal Integrations tab | Fully |
| `src/lib/components/chat/Settings/Integrations/Terminals.svelte`, `.../Terminals/Connection.svelte` | Personal terminal list | Fully |
| `src/lib/components/chat/Settings/Tools/Connection.svelte` | Tool-server row | Fully |
| `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte` | Composer Integrations menu | Fully |
| `src/lib/components/chat/MessageInput/TerminalMenu.svelte` | Composer Terminal menu | Fully |
| `src/lib/components/chat/ToolServersModal.svelte` | Available Tools window | Fully |
| `src/lib/components/chat/TerminalDock.svelte`, `src/lib/components/chat/XTerminal.svelte` | Terminal dock and shell | Fully |
| `src/lib/components/common/Valves.svelte`, `src/lib/components/common/Valves/MapSelector.svelte` | Valves form (the map input is marked experimental in code) | Fully |
| `src/lib/components/workspace/common/ValvesModal.svelte` | Valves window | Fully |
| `src/lib/components/workspace/common/ManifestModal.svelte` | Support (funding) window | Partial |
| `src/lib/components/chat/Controls/Valves.svelte`, `Controls.svelte` | Chat Controls valves | Partial |
| `src/lib/components/ImportModal.svelte` | Import From Link dialog | Partial |
| `src/lib/apis/tools/index.ts` | Tools API client | Partial (outline and error handling) |
| `src/lib/apis/terminal/index.ts` | Terminal API client | Partial (lines 77-205 and error lines) |
| `src/lib/apis/configs/index.ts` | Settings API client (tool servers, terminals, OAuth registration) | Partial |
| `src/lib/apis/index.ts` | Direct tool-server fetching and calls | Partial (lines 380-716) |
| `src/routes/+layout.svelte` | Browser execution of direct tools; terminal state answers | Partial (lines 437-700) |
| `src/routes/(app)/+layout.svelte` | Loading tools and tool servers at app start; settings deep links | Partial |
| `src/lib/components/chat/MessageInput.svelte`, `src/lib/components/chat/Chat.svelte` | Composer buttons, chips, filesystem uploads; default tools, terminal selection, request fields | Partial |
| `src/lib/components/chat/SettingsModal.svelte` | Settings tabs and their visibility | Partial |
| `src/lib/components/admin/Users/Groups/Permissions.svelte` | Permission labels | Partial |
| `src/lib/components/chat/FileNav.svelte`, `src/lib/components/chat/ChatControls.svelte` | Files panel hosting the terminal dock | Partial |
| `src/lib/components/common/InterfaceSettings.svelte`, `src/lib/components/common/ToolCallDisplay.svelte` | Terminal interface settings; fork's Hide Processing Details | Partial |
| `src/lib/components/workspace/common/AccessControl.svelte` | Access dialog labels | Partial |
| `src/lib/utils/localizedContent.ts` | Name display fallback | Partial |
| `src/lib/i18n/locales/en-US/translation.json` | Dotted keys resolved | Partial (keys cited) |

## 14. Open Questions

### 14.1 Possible Contradiction With the Ground Truth

- **Valve encryption.** `../tools/ground-truth.md` (Secrets) states "Tool and function valves are
  stored encrypted in the database." In the code, encryption of valves is applied only when the
  environment variable `ENABLE_VALVE_ENCRYPTION` is on, and its code default is **off**
  (`backend/open_webui/env.py:767`; `backend/open_webui/utils/valves.py:21-24`). The production
  value is **TO BE CONFIRMED**. This document was written to the code (sections 4, 5.2, 6.1, 6.2,
  7.2, 11.5); the ground-truth line needs review by the knowledgebase owner. Security-sensitive:
  refer to the platform maintainer and U of T Information Security (security.utoronto.ca).
  *Resolved 2026-10-08: verified in the main loop; `../tools/ground-truth.md` and `CLAUDE.md` were
  corrected to match the code and the defect is logged in `../tools/VERIFICATION.md`. The
  production value of `ENABLE_VALVE_ENCRYPTION` remains TO BE CONFIRMED.*

### 14.2 Live Configuration (Data, Not in the Repository)

All **TO BE CONFIRMED** for production:

1. Which workspace tools exist, who owns them, and how they are shared.
2. Which admin tool servers (OpenAPI or MCP) and terminals are configured, their auth types, their
   access grants, and whether any use OAuth 2.1.
3. Whether **Direct Integrations** is on, and who holds `workspace.tools`, `workspace.tools_import`,
   `workspace.tools_export`, `sharing.tools`, `sharing.public_tools` and
   `features.direct_tool_servers`.
4. Environment values: `ENABLE_PLUGINS`, `ENABLE_PIP_INSTALL_FRONTMATTER_REQUIREMENTS`,
   `PIP_OPTIONS`, `PIP_PACKAGE_INDEX_OPTIONS`, `OFFLINE_MODE`, the tool-server time limits,
   `MCP_INITIALIZE_TIMEOUT`, both certificate settings, `AIOHTTP_CLIENT_ALLOW_REDIRECTS`,
   `ENABLE_FORWARD_USER_INFO_HEADERS`, `BYPASS_ADMIN_ACCESS_CONTROL`, `ENABLE_VALVE_ENCRYPTION`,
   `TERMINAL_PROXY_HEADERS`.
5. Whether production uses Redis (it changes how the specification cache behaves, section 8.2) and
   how many server processes run (tool code and package installation are per process).
6. Whether the production server can reach the internet or a package index for `pip`, and reach
   web addresses for **Import From Link**.
7. Whether `ui.enable_community_sharing` is on (it allows sending tool code to openwebui.com).
8. Time limits of any proxy in front of MedIT GPT (relevant to long tool saves, section 11.17).

### 14.3 Governance and Contacts

1. Who may be granted **Tools Access** (the right to run code on the server) and who reviews tool
   code and its `requirements` before use: **TO BE CONFIRMED**.
2. Which external tool servers and terminals are approved to receive chat content, which may
   include personal and health information; refer to the Privacy Office (privacy.utoronto.ca) and
   the data steward. **TO BE CONFIRMED**.
3. Who is the "tool-server admin" and the "platform maintainer" for escalations, and their contact
   routes and hours: **TO BE CONFIRMED** (no contact exists in the repository,
   `../tools/ground-truth.md`).
4. Whether people may add their own tool servers and terminals at all (Direct Integrations), given
   that those connect from the browser to arbitrary services: **TO BE CONFIRMED**.

### 14.4 Security-Sensitive Questions (Referred Without Detail)

Security-sensitive: refer to the platform maintainer and U of T Information Security
(security.utoronto.ca).

1. The risk posture of the **Session**, **OAuth** and **Forward cookies** options, which pass a
   person's credentials to external servers.
2. How the direct tool-server checks in the browser authenticate.
3. The terminal pass-through's path restrictions (`Invalid path`, `Path not allowed`) and the
   **Terminal Preview Allow Same Origin** interface setting.
4. Whether every sharing permission is enforced by the server as well as by the page.
5. Package installation from tool frontmatter by non-admin authors (supply-chain exposure).
6. Valve storage (14.1) and the content of exported connection files (which include keys).

### 14.5 Behaviour Read From Code but Not Observed

The application was not run for this research. These conclusions come from reading code only:
an admin tool server with an empty Name is listed with a blank name (section 5.7); a parse error
in `TERMINAL_SERVER_CONNECTIONS` is not caught (section 7.2; effect on start-up not observed);
**Import JSON** reports success after individual failures (section 5.4); a save with no error text
shows nothing (section 11.17); requirements are reinstalled lazily per process (section 8.1); the
Redis specification cache has no expiry (section 8.2); new admin terminals are saved switched off
(section 5.10).

### 14.6 Not Researched in Depth (Other Areas or External Products)

1. The terminal **Files** browser (`src/lib/components/chat/FileNav.svelte`), port previews
   (`PortList`), terminal notebooks and terminal skills (`src/lib/apis/terminal/index.ts:345-760`)
   were only skimmed; their messages are not catalogued here.
2. The tool-call display, tool approval and the tool loop belong to `builtin-native-tools.md` and
   `chat-completion-pipeline-and-generation-tasks.md`.
3. The **Open Terminal** and orchestrator ("Terminals") products are external: the meaning of
   policies, **Lifecycle JSON**, storage, idle time-outs and refresh is defined by them, not by this
   repository. **TO BE CONFIRMED** from their documentation.
4. The MCP client also has resource-reading functions (`list_resources`, `read_resource`), but no
   caller was found in the backend (`backend/open_webui/utils/mcp/client.py:131-153`); whether MCP
   resources are meant to be supported is unknown.
5. `src/lib/components/chat/Chat.svelte:1056-1057` reads a `tools` value from personal settings as
   default tools when the model has none, but no page in the front end writes that value; whether
   any account carries it is data, **TO BE CONFIRMED**.
6. The **Access Control** dialog internals (`src/lib/components/workspace/common/AccessControl.svelte`)
   are documented in `users-groups-roles-and-permissions.md`.
