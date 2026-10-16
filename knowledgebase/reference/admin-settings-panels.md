# Admin Settings Panels

## At a Glance

- **Where.** Admin settings are sixteen extra tabs in the ordinary **Settings** window, shown only to
  the `admin` role. `/admin/settings/<tab>` redirects to `/?settings=admin:<tab>`; the tab ids are
  not always the titles (Database is `db`, Web Search is `web`), and an unknown id opens the
  personal General tab (section 2).
- **A map.** **General**, **Interface**, **Database**, the **UI Translations** editor, the shared
  building blocks and the settings search are covered in full (sections 4, 5, 7.1 to 7.4); every
  other panel has a compact table (section 7.5) and a pointer to its deep document.
- **Saving.** Each panel has its own **Save**; Connections switches save at once. Values go to the
  `config` table and the server reads them on the next request, but other users' screens change
  only after a reload. Interface shows its success toast before the save finishes, and Audio,
  Documents, Web Search and Code Execution show nothing when a save fails (section 5.2).
- **General and Authentication share one save.** General's **Save** also re-sends sign-up,
  default role, API key and token settings, so a stale tab can undo an Authentication change
  (section 5.3). Banners, UI translations and interface defaults for every account (including the
  fork's **Inline Citations** and **Hide Processing Details**) live on General › **UI**.
- **Reverting values.** OAuth values are not stored by default and vanish at restart;
  `RESET_CONFIG_ON_START` or a switched-off `ENABLE_PERSISTENT_CONFIG` loses everything; for a
  stored key, a changed environment variable does not override the value already stored
  (sections 4.1, 7.7, 11.2).
- **Sensitive files.** The settings export contains provider keys and other secrets; the database,
  all-chats and users downloads contain personal and possibly health data. Tier 1 never handles
  them. The database download works only on SQLite and only while `ENABLE_ADMIN_EXPORT` is on
  (sections 5.8 to 5.10).
- **Import writes rows only.** It accepts any keys, does not rebuild embedding, speech or tool-server
  state, and does not refresh open browsers; re-save the affected panels or restart (section 5.9).

## 1. Purpose and Who Uses It

The admin settings panels are the site-wide configuration screens of MedIT GPT (Open WebUI
v0.11.4). They are not a separate page any more: they are extra tabs in the same **Settings**
window every user opens from the user menu. Users see only a **Personal** list of tabs; an account
with the `admin` role also sees an **Admin** list below it, split into the groups **System**,
**AI**, **Experience**, **Quality**, **Tools** and **Data**
(`src/lib/components/chat/SettingsModal.svelte:157-174`, `:407-408`, `:748-779`).

This document is a **map**. For every admin panel it gives the address, what the panel is for, a
compact table of what it shows and where each value is stored, whether a change needs a restart,
and the reference document that covers the panel in depth. Four parts of the area have no other
home and are covered in full here:

- the **General** panel (feature switches, the WebUI URL, event webhooks, UI translations, default
  interface settings for every account, and banners);
- the **Interface** panel (task models, chat-wide switches and generation prompts);
- the **Database** panel (settings import and export, database download, all-chats and users
  exports);
- the **UI Translations** editor (`I18nSettings`), the shared panel building blocks
  (`AdminSettingField`, `AdminSettingRow`, `AdminSettingSection`, `AdminTabIcon`) and the
  settings search box.

Who uses it:

| Audience | What they do here | Evidence |
|---|---|---|
| Administrators (`admin` role) | Open any admin tab, change values and press **Save**; import and export settings; download the database | `src/lib/components/chat/SettingsModal.svelte:407-408`, `:486-488`; every save endpoint in section 6 requires the admin role (`get_admin_user`) |
| Users and pending users | Do not see the admin tabs; an admin deep link opens their personal **General** tab instead | `src/routes/(app)/+layout.svelte:181-185`; `src/lib/components/chat/SettingsModal.svelte:486-488` |
| Tier-1 support | Read-only: identify which panel and key holds a setting, explain when a change applies, collect evidence for escalation. Tier 1 does not change settings | `knowledgebase/reference/_research-prompt.md` rule 14 |

What the panels change is the **persistent configuration**: rows in the `config` table, one per
dotted key, which the server reads on every request (`backend/open_webui/models/config.py:140-147`).
The live values are data and are **TO BE CONFIRMED** for production; every default in this
document is the code default.

## 2. Navigation and URLs

### 2.1 Ways In

| Entry point | Where | Who | Result | Evidence |
|---|---|---|---|---|
| User menu › **Settings** | Click the account name at the bottom of the sidebar | Everyone | Opens the Settings window on the personal **General** tab; admins then pick a tab from the **Admin** list | `src/lib/components/layout/Sidebar/UserMenu.svelte:559-577`; `src/lib/components/chat/SettingsModal.svelte:116-124` |
| User menu › **Admin Panel**, then **Settings** in the top bar | `/admin` (which forwards to `/admin/users`), then the **Settings** link | Admins | Opens the Settings window on the admin **General** tab | `src/lib/components/layout/Sidebar/UserMenu.svelte:535-556`; `src/routes/(app)/admin/+page.svelte:5-7`; `src/routes/(app)/admin/+layout.svelte:97-107` |
| Keyboard shortcut "open settings" | Anywhere in the app | Everyone | Toggles the Settings window | `src/routes/(app)/+layout.svelte:297-300` |
| `/admin/settings` | Address bar or bookmark | Admins | Redirects to `/?settings=admin%3Ageneral` | `src/routes/(app)/admin/settings/+page.svelte:5-7` |
| `/admin/settings/<tab>` | Address bar or bookmark | Admins | Redirects to `/?settings=admin:<tab>`, keeping any other query parameters | `src/routes/(app)/admin/settings/[tab]/+page.svelte:6-10` |
| `?settings=<tab id>` on any app page | Address bar | Everyone | Opens the Settings window on that tab, then removes the parameter from the address; a non-admin asking for an `admin:` tab gets the personal **General** tab | `src/routes/(app)/+layout.svelte:166-195` |
| Shortcuts inside the app | Model selector, model menu, terminal menu | Admins | Open `admin:connections`, `admin:models` (with the chosen model) or `admin:integrations` directly | `src/lib/components/chat/ModelSelector/Selector.svelte:1064`; `src/lib/components/chat/ModelSelector/ModelItemMenu.svelte:61`; `src/lib/components/chat/MessageInput/TerminalMenu.svelte:246` |

Any page under `/admin` first checks the role: a non-admin is sent to `/`
(`src/routes/(app)/admin/+layout.svelte:15-17`). The browser tab title there is
`Admin Panel / {WEBUI_NAME}`, which reads "Admin Panel / MedIT GPT" with the fork's default name
(`src/routes/(app)/admin/+layout.svelte:32-34`; `backend/open_webui/env.py:951`).

### 2.2 The Sixteen Admin Tabs

The tab id is the part after `admin:`; it is also the `<tab>` in `/admin/settings/<tab>`. The order
and groups below are the order in which the tabs are listed
(`src/lib/components/chat/SettingsModal.svelte:157-174`, `:267-364`); icons come from
`AdminTabIcon` (`src/lib/components/admin/Settings/AdminTabIcon.svelte:22-90`).

| Group | Tab (English title) | Address | Component | Deep reference |
|---|---|---|---|---|
| System | **General** | `/admin/settings/general` | `src/lib/components/admin/Settings/General.svelte` | this document, section 7.1 |
| System | **Authentication** | `/admin/settings/authentication` | `src/lib/components/admin/Settings/Authentication.svelte` | `authentication-and-sign-in.md`, `sso-oauth-oidc-and-scim.md` |
| AI | **Connections** | `/admin/settings/connections` | `src/lib/components/admin/Settings/Connections.svelte` | `model-connections-openai-ollama-and-direct.md` |
| AI | **Models** | `/admin/settings/models` | `src/lib/components/admin/Settings/Models.svelte` | `workspace-models-and-model-access.md` |
| AI | **Sub-agents** | `/admin/settings/subagents` | `src/lib/components/admin/Settings/Subagents.svelte` | `chat-completion-pipeline-and-generation-tasks.md` |
| Experience | **Interface** | `/admin/settings/interface` | `src/lib/components/admin/Settings/Interface.svelte` | this document, section 7.2 |
| Experience | **Audio** | `/admin/settings/audio` | `src/lib/components/admin/Settings/Audio.svelte` | `audio-speech-to-text-and-text-to-speech.md` |
| Experience | **Images** | `/admin/settings/images` | `src/lib/components/admin/Settings/Images.svelte` | `image-generation-and-editing.md` |
| Quality | **Evaluations** | `/admin/settings/evaluations` | `src/lib/components/admin/Settings/Evaluations.svelte` | `evaluations-feedback-and-analytics.md` |
| Quality | **Analytics** | `/admin/settings/analytics` | `src/lib/components/admin/Analytics.svelte` (outside this folder) | `evaluations-feedback-and-analytics.md` |
| Tools | **Integrations** | `/admin/settings/integrations` | `src/lib/components/admin/Settings/Integrations.svelte` (embeds `ExternalKnowledge.svelte`) | `workspace-tools-tool-servers-mcp-and-terminals.md`; External Knowledge: `rag-retrieval-embeddings-and-vector-stores.md` |
| Tools | **Documents** | `/admin/settings/documents` | `src/lib/components/admin/Settings/Documents.svelte` | `rag-retrieval-embeddings-and-vector-stores.md` |
| Tools | **Web Search** | `/admin/settings/web` | `src/lib/components/admin/Settings/WebSearch.svelte` | `web-search-and-web-loading.md` |
| Tools | **Code Execution** | `/admin/settings/code-execution` | `src/lib/components/admin/Settings/CodeExecution.svelte` | `code-execution-and-interpreter.md` |
| Tools | **Pipelines** | `/admin/settings/pipelines` | `src/lib/components/admin/Settings/Pipelines.svelte` | `functions-pipes-filters-actions-and-pipelines.md` |
| Data | **Database** | `/admin/settings/db` | `src/lib/components/admin/Settings/Database.svelte` | this document, section 7.3 |

Tab titles: `src/lib/i18n/locales/en-US/translation.json:1976` (Analytics), `:2008` (Audio), `:2124`
(Authentication), `:2167` (Code Execution), `:2182` (Connections), `:2193` (Database), `:2350`
(Documents), `:2368` (Evaluations), `:2405` (General), `:2471` (Images), `:2483` (Integrations),
`:2523` (Interface), `:2617` (Models), `:2629` (Pipelines), `:2641` (Sub-agents), `:2710` (Web Search).

Points support staff get wrong:

- **The address segment is not always the title.** Web Search is `web`, Database is `db`, Code
  Execution is `code-execution`. A segment that is not a tab id (for example
  `/admin/settings/database`) opens the Settings window on the **personal General** tab, because
  any tab id that is not in the list falls back to `general`
  (`src/lib/components/chat/SettingsModal.svelte:422-425`, `:490-497`).
- **Analytics is hidden** when the environment variable `ENABLE_ADMIN_ANALYTICS` is off (code
  default on) (`src/lib/components/chat/SettingsModal.svelte:409-411`;
  `backend/open_webui/config.py:2094`).
- **Three inventory items are not tabs.** **Events** (event webhooks) and **UI Translations**
  (`I18nSettings`) are sections inside **General**, and **Banners** (`Interface/Banners.svelte`)
  also sits in General's **UI** section, not in Interface
  (`src/lib/components/admin/Settings/General.svelte:418`, `:420-423`, `:483-520`).
  **External Knowledge** is a section inside **Integrations**
  (`src/lib/components/admin/Settings/Integrations.svelte:340`).
- **Prompt suggestions and default models** are not on Interface or General in v0.11.4. Prompt
  suggestions are in **Models** › **Model Defaults**
  (`src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:9`, `:118-140`); default and
  pinned models are set from each model's menu in the **Models** list
  (`src/lib/components/admin/Settings/Models/ModelMenu.svelte:127-148`).
- **Sign-up, default role, default group, API keys, token lifetime and the pending-user overlay**
  are on **Authentication**, although General saves the same keys (section 5.3).

### 2.3 The Settings Window Layout

| Element | What it does | Evidence |
|---|---|---|
| **Back** | Closes the window | `src/lib/components/chat/SettingsModal.svelte:518-527` |
| **Search** box | Filters the tab list by setting names and descriptions (section 4.3); **Enter** opens the first match, **Escape** clears the search | `src/lib/components/chat/SettingsModal.svelte:427-436`, `:529-544` |
| **Personal** list | The personal tabs, grouped Basics, Services, Preferences, Data, Profile | `src/lib/components/chat/SettingsModal.svelte:142-156`, `:557-746` |
| **Admin** list | Shown only to admins and only when at least one admin tab matches the search | `src/lib/components/chat/SettingsModal.svelte:748-779` |
| Panel area | The selected tab's component; each admin panel has its own **Save** button at the bottom, except Database (actions only) and the Analytics dashboard | `src/lib/components/chat/SettingsModal.svelte:789-909`; `src/lib/components/admin/Settings/Database.svelte:54-162` |

## 3. Roles and Permissions

The admin panels have one gate: the `admin` role. There is no finer permission for them; any admin
can open and change every panel. The **Default permissions** and group permissions that shape what
users may do are edited elsewhere (Admin Panel › **Users** › **Groups**; see
`users-groups-roles-and-permissions.md`).

| What | Who | Evidence |
|---|---|---|
| See the **Admin** tab list in the Settings window | `admin` only; for other roles the admin tabs are not added to the list | `src/lib/components/chat/SettingsModal.svelte:407-408`, `:748` |
| Stay on an admin tab | A non-admin who ends up on an `admin:` tab is moved to the personal **General** tab | `src/lib/components/chat/SettingsModal.svelte:486-488`; `src/routes/(app)/+layout.svelte:181-185` |
| Open any page under `/admin` | `admin` only; others are redirected to `/` | `src/routes/(app)/admin/+layout.svelte:15-17` |
| Read or save the General and Authentication values (`/api/v1/auths/admin/config`) | `admin` | `backend/open_webui/routers/auths.py:1204-1205`, `:1269-1270` |
| Save Interface task settings (`/api/v1/tasks/config/update`) | `admin` | `backend/open_webui/routers/tasks.py:135-138` |
| Read Interface task settings (`GET /api/v1/tasks/config`) | any signed-in `user` or `admin` (it holds task model ids and prompt templates) | `backend/open_webui/routers/tasks.py:108-110` |
| Read or save Interface chat settings (`/api/v1/chats/config`) | `admin` | `backend/open_webui/routers/chats.py:836-857` |
| Import, export or read a namespace of settings (`/api/v1/configs/import`, `/export`, `/namespace/{namespace}`) | `admin` | `backend/open_webui/routers/configs.py:100-125` |
| Save connections, tool servers, terminal servers, code execution, model defaults, sub-agents, prompt suggestions and banners (`/api/v1/configs/...`) | `admin` | `backend/open_webui/routers/configs.py:139-160`, `:235-298`, `:326-352`, `:704-728`, `:749-770`, `:783-804`, `:817-840`, `:852-869` |
| Read the banner list and the model metadata defaults | any signed-in `user` or `admin` (the app needs them to draw the banner strip and the model editor) | `backend/open_webui/routers/configs.py:742-746`, `:872-877` |
| Download the database (`/api/v1/utils/db/download`) | `admin`, and only when the environment variable `ENABLE_ADMIN_EXPORT` is on (code default on) | `backend/open_webui/routers/utils.py:74-78`; `backend/open_webui/config.py:2082` |

When a role check fails the server answers HTTP 401 with the `ACCESS_PROHIBITED` text (see
`knowledgebase/tools/ground-truth.md`, Accounts and Access). The database download uses the same
text and status when `ENABLE_ADMIN_EXPORT` is off (`backend/open_webui/routers/utils.py:77-78`).

Two settings on these panels change other people's access and are worth flagging when an admin asks
about them: **Default User Role** offers `pending`, `user` and `admin`, and the server accepts any of
the three (`src/lib/components/admin/Settings/Authentication.svelte:147-154`;
`backend/open_webui/routers/auths.py:1283-1284`); and **New Sign Ups** decides whether strangers can
create accounts at all (see `authentication-and-sign-in.md`).

## 4. Key Concepts and Terminology

### 4.1 Terms

| Term | Meaning here | Evidence |
|---|---|---|
| Settings window | The full-screen dialog that holds both personal and admin tabs; opened by `showSettings` | `src/lib/components/chat/SettingsModal.svelte:508-513`; `src/routes/(app)/+layout.svelte:425` |
| Tab id | The internal name of a tab, such as `admin:general` or `admin:db`; used in `?settings=` and `/admin/settings/<tab>` | `src/lib/components/chat/SettingsModal.svelte:267-364` |
| Panel | The component shown for a tab, in `src/lib/components/admin/Settings/` | section 2.2 |
| Persistent setting | A row in the `config` table, one per dotted key such as `ui.enable_signup`; read from the database on every call | `backend/open_webui/models/config.py:101-108`, `:140-147` |
| Code default | The value in `DEFAULT_CONFIG`, usually taken from an environment variable at start-up; inserted into the database only for keys that have no row yet | `backend/open_webui/config.py:2822-3228`; `backend/open_webui/models/config.py:240-266` |
| Environment-only setting | A value read from the environment and not part of the stored settings, for example `WEBUI_NAME`, `ENABLE_ADMIN_EXPORT`, `ENABLE_ADMIN_ANALYTICS`, `ENABLE_VERSION_UPDATE_CHECK`; changing it needs a restart with the new environment | `backend/open_webui/env.py:951`, `:1200`; `backend/open_webui/config.py:2082`, `:2094` |
| Process-only value | A key the database is not authoritative for (every `oauth.*` key while `ENABLE_OAUTH_PERSISTENT_CONFIG` is off, or every key while `ENABLE_PERSISTENT_CONFIG` is off). Saving it changes only the memory of the server process that handled the request, and a restart loses it | `backend/open_webui/models/config.py:132-138`, `:197-206`; `backend/open_webui/config.py:3231-3232` |
| Read-only (environment) section | The OAuth / OIDC section of Authentication is greyed out and labelled as environment-controlled while `ENABLE_OAUTH_PERSISTENT_CONFIG` is off | `src/lib/components/admin/Settings/Authentication.svelte:52`, `:546-563` |
| Save button | Each form panel's own **Save** button; it saves only that panel | for example `src/lib/components/admin/Settings/General.svelte:525-533` |
| Instant switch | A switch that saves the moment it is flipped, with no **Save** needed (Connections, Integrations) | `src/lib/components/admin/Settings/Connections.svelte:243-306`, `:373-413`; `src/lib/components/admin/Settings/Integrations.svelte:347-352` |
| Default Interface Settings | Interface preferences an admin sets for every account; each user's own saved choice wins | `src/lib/components/admin/Settings/General.svelte:424-481`; `backend/open_webui/routers/users.py:57-69`, `:456-473` |
| "Default" marker | The small **Default** word next to a switch in a user's personal Interface tab when its value comes from the admin defaults | `src/lib/components/common/Switch.svelte:30-31`; `src/lib/components/common/InterfaceSettings.svelte:152-159` |
| UI Translations | Admin wording overrides: a replacement text per interface text key and language, stored in `ui.i18n` | `src/lib/components/admin/Settings/I18nSettings.svelte`; `backend/open_webui/routers/auths.py:116`, `:1242-1266` |
| Banner | An announcement strip shown to signed-in users, stored in `ui.banners` | `src/lib/components/admin/Settings/Interface/Banners.svelte`; `backend/open_webui/routers/configs.py:852-877` |
| Config export / import | A JSON file holding every stored setting, downloaded or uploaded on the Database tab | `src/lib/components/admin/Settings/Database.svelte:60-121`; `backend/open_webui/routers/configs.py:100-120` |

### 4.2 The Shared Building Blocks

Every admin panel is built from four small components, which is why the panels look alike. They
hold no settings themselves.

| Component | What it draws | Evidence |
|---|---|---|
| `AdminSettingSection` | A section with a small grey heading (an `h3`) and a stacked list of rows; the first section of a panel has no top margin | `src/lib/components/admin/Settings/AdminSettingSection.svelte:1-17` |
| `AdminSettingRow` | One line: the label on the left, the control (usually a switch or a drop-down) on the right, and an optional description underneath; it gives the label an id the control uses as its accessible name | `src/lib/components/admin/Settings/AdminSettingRow.svelte:1-26` |
| `AdminSettingField` | A label above a control (text box, text area, number box) with an optional description below; the label is tied to the control when the panel passes an id | `src/lib/components/admin/Settings/AdminSettingField.svelte:1-24` |
| `AdminTabIcon` | The icon beside each admin tab name, chosen by tab id; an unknown id draws no icon | `src/lib/components/admin/Settings/AdminTabIcon.svelte:17-90` |

Each panel also starts with an `h2` heading carrying the tab title, for example
`src/lib/components/admin/Settings/General.svelte:127-129` and
`src/lib/components/admin/Settings/Database.svelte:55-57`.

### 4.3 The Settings Search Box

The **Search** box at the top of the tab list filters tabs, not individual settings: typing narrows
the list to the tabs that contain a matching setting, and **Enter** opens the first one
(`src/lib/components/chat/SettingsModal.svelte:414-436`). How matching works:

- The index is built from every English text key that ends in `.label` or `.title`, plus the
  matching `.description`, for the key prefixes each tab declares
  (`src/lib/utils/settings-search.ts:47-63`; prefixes at
  `src/lib/components/chat/SettingsModal.svelte:267-364`). Both the English text and the text in
  the user's current language are indexed (`src/lib/utils/settings-search.ts:29-46`).
- Every tab also matches its own title and the word "Admin" (admin tabs) or "Personal"
  (`src/lib/utils/settings-search.ts:49-52`, `:64-65`).
- Matching ignores case, Latin accents and punctuation, and every typed word must appear
  (`src/lib/utils/settings-search.ts:13-21`, `:69-79`).
- Admin **General** also indexes the personal Interface labels, because its Default Interface
  Settings editor shows them; admin **Interface** and **Models** also index the model parameter
  labels (`src/lib/components/chat/SettingsModal.svelte:272`, `:290`, `:302`).
- Text that uses plain (non-dotted) keys, such as **Default Interface Settings** or the banner
  help line, is not in the index, so searching for it finds nothing beyond the tab title.
- Permission rules hide a few personal entries from users who cannot use them; for admins the only
  hidden entries are personal ones tied to a switched-off feature (notification targets while
  **User Webhooks** is off, API key entries while **API Keys** is off)
  (`src/lib/utils/settings-access.ts:13-18`, `:24-69`).
- A screen-reader status reports the number of matching tabs or "No matches"
  (`src/lib/components/chat/SettingsModal.svelte:546-552`, `:781-785`).

## 5. Workflows (Step by Step)

Tier 1 does not perform these steps; they are written so support staff can follow what an admin
did and spot where it went wrong.

### 5.1 Open an Admin Panel and Save a Change

1. Open the Settings window (user menu › **Settings**, or Admin Panel › **Settings**), or go
   straight to `/admin/settings/<tab>` (section 2).
2. Pick the tab in the **Admin** list. The panel loads its current values from the server when it
   opens; until they arrive some panels show a spinner or nothing at all
   (`src/lib/components/admin/Settings/General.svelte:108-118`, `:132`;
   `src/lib/components/admin/Settings/Interface.svelte:163`, `:570-573`).
3. Change values. Switches on **Connections** and the **Direct Integrations** switch on
   **Integrations** save at once; everything else waits for **Save** (section 5.2).
4. Press **Save** at the bottom of the panel. Most panels then show the toast
   `Settings saved successfully!` (`src/lib/components/chat/SettingsModal.svelte:460-464`,
   `:853-908`) and refresh the app's copy of the public configuration
   (`getBackendConfig`, which reads `/api/config`).
5. Leaving a tab without saving discards the edits: each panel keeps its values only while it is
   open and reloads them from the server the next time (`onMount` in every panel, for example
   `src/lib/components/admin/Settings/General.svelte:108-118`).

### 5.2 What Save Does on Each Panel

| Panel | Save trigger | Endpoint(s) called | Writes | Feedback | Waits for the server? | Evidence |
|---|---|---|---|---|---|---|
| General | **Save** | `POST /api/v1/auths/admin/config` (the whole admin form, see 5.3), then `POST /api/v1/configs/banners` | The 31 admin keys in section 6.2, plus `ui.banners` | `Settings saved successfully!`; on failure the error text | Yes; the button is disabled while saving | `src/lib/components/admin/Settings/General.svelte:80-106`, `:525-533` |
| Authentication | **Save** | `POST /api/v1/auths/admin/config`; `POST /api/v1/auths/admin/config/ldap` and, when LDAP is on, `/ldap/server`; `POST /api/v1/auths/admin/config/oauth` only when OAuth is editable | Admin keys, `ldap.*`, `oauth.*` | `Settings saved successfully!` only when all three succeed | Yes | `src/lib/components/admin/Settings/Authentication.svelte:58-107` |
| Connections | Each switch saves on change; **Save** re-sends the OpenAI and Ollama lists | `/openai/config/update`, `/ollama/config/update`, `/api/v1/configs/connections` | `openai.*`, `ollama.*`, `direct.enable`, `models.base_models_cache` | `OpenAI API settings updated`, `Ollama API settings updated`, `Connections settings updated`; **Save** also shows `Settings saved successfully!` straight away | **No** for the **Save** toast | `src/lib/components/admin/Settings/Connections.svelte:56-123`, `:213-220`; `src/lib/components/chat/SettingsModal.svelte:857-862` |
| Models | **Save** (only when the order or **Model Defaults** changed); model menu actions save at once | `POST /api/v1/configs/models`, `POST /api/v1/configs/suggestions` | `ui.default_models`, `ui.default_pinned_models`, `ui.model_order_list`, `models.default_metadata`, `models.default_params`, `ui.prompt_suggestions`, `ui.prompt_suggestions_i18n` | `Model order saved successfully`, `Models configuration saved successfully` | Yes | `src/lib/components/admin/Settings/Models.svelte:333-405`; `src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:105-150` |
| Sub-agents | **Save** | `POST /api/v1/configs/subagents` | `subagents.*` | `Settings saved successfully!` | Yes | `src/lib/components/admin/Settings/Subagents.svelte:41-52` |
| Interface | **Save** | `POST /api/v1/tasks/config/update` and `POST /api/v1/chats/config`, together | `task.*`, `chat.context_compaction.*`, `chat.tool_permissions.enable` | `Settings saved successfully!` | **No**: the toast appears before the save finishes and also when it fails | `src/lib/components/admin/Settings/Interface.svelte:64-86`, `:164-169` |
| Audio | **Save** | `POST /api/v1/audio/config/update` | `audio.*` | `Settings saved successfully!` after success | Yes; a failure shows no message | `src/lib/components/admin/Settings/Audio.svelte:136-185`, `:240-245` |
| Images | **Save** | `POST /api/v1/images/config/update` | `image_generation.*`, `images.edit.*` | Toast after success; missing URL or key messages before sending | Yes | `src/lib/components/admin/Settings/Images.svelte:110-160`, `:176-219`, `:296-300` |
| Evaluations | **Save**; adding, editing or deleting an arena model saves at once | `/api/v1/evaluations/config` | `evaluation.arena.*` | `Settings saved successfully!` | Yes | `src/lib/components/admin/Settings/Evaluations.svelte:24-73`, `:87-92` |
| Analytics | none (a dashboard) | — | nothing | — | — | `src/lib/components/chat/SettingsModal.svelte:869-870` |
| Integrations | **Save** re-sends tool servers; terminal servers save on each change; **Direct Integrations** saves on change; External Knowledge sources save in their own dialog | `/api/v1/configs/tool_servers`, `/terminal_servers`, `/connections`, `/api/v1/knowledge/external/...` | `tool_server.connections`, `terminal_server.connections`, `direct.integrations.enable`, `external_knowledge.connections` | `Connections saved successfully`, `Terminal servers saved`, `Connections settings updated` | Yes | `src/lib/components/admin/Settings/Integrations.svelte:57-125`, `:179-180`; `knowledge-bases.md` section 7 |
| Documents | **Save** | `POST /api/v1/retrieval/embedding/update` (unless retrieval is bypassed), then `POST /api/v1/retrieval/config/update` | `rag.*`, `file.*`, `google_drive.enable`, `onedrive.enable` | `Settings saved successfully!` after the update | Partly: the update is awaited inside the handler, but a failure of the final update shows no message | `src/lib/components/admin/Settings/Documents.svelte:239-241`, `:264-298`, `:418-423` |
| Web Search | **Save** | `POST /api/v1/retrieval/config/update` with a `web` block | `web.*` (and the YouTube loader keys) | `Settings saved successfully!` after success | Yes; a failure shows no message (*corrected 2026-10-10: only a failure the server explains; a failure without a server reason, for example a network error, still shows `Settings saved successfully!`*) | `src/lib/components/admin/Settings/WebSearch.svelte:60-112`, `:160-165` |
| Code Execution | **Save** | `POST /api/v1/configs/code_execution` | `code_execution.*`, `code_interpreter.*` | `Settings saved successfully!` after success | Yes; a failure shows no message (*corrected 2026-10-10: only a failure the server explains; a failure without a server reason, for example a network error, still shows `Settings saved successfully!`*) | `src/lib/components/admin/Settings/CodeExecution.svelte:26-28`, `:39-45` |
| Pipelines | **Save** (valves of the selected pipeline) | the external pipelines server through `/api/v1/pipelines/...` | the pipeline's valves on that server, not the `config` table | `Valves updated successfully`, then `Settings saved successfully!`; `No valves to update` when there is nothing to save | Yes | `src/lib/components/admin/Settings/Pipelines.svelte:51-90`, `:251-256` |
| Database | Action buttons only | `/api/v1/configs/import`, `/configs/export`, `/utils/db/download`, `/chats/all/db`, `/users/all` | Import writes any keys in the file | per action, section 5.8 to 5.10 | — | `src/lib/components/admin/Settings/Database.svelte:23-160` |

"A failure shows no message" means the panel's code does not catch the error from the save call,
so the toast is skipped and nothing else is shown; the error is only visible in the browser
console. This is the most common cause of "the Save button does nothing" (section 11.3).

### 5.3 The General Panel Save in Detail

1. The **UI Translations** rows are checked and turned into the stored shape; a bad row stops the
   save with a toast (section 7.4) (`src/lib/components/admin/Settings/General.svelte:84`;
   `src/lib/utils/translationDictionary.ts:54-71`).
2. The panel posts **every** admin value it loaded when it opened, including the sign-up, default
   role, default group, API key, token lifetime, admin details and pending-overlay values that the
   **Authentication** panel shows, plus the default interface settings and translations
   (`src/lib/components/admin/Settings/General.svelte:85-89`). The server maps each field to its
   key and stores them all in one write (`backend/open_webui/routers/auths.py:1269-1296`).
3. On the server: the login-form and translation keys are only written when the request carries
   them; `ui.default_interface_settings` is written on every save; empty folder and automation limits are
   stored as an empty value (no limit); a default role other than `pending`, `user` or `admin`, a
   channel response mode other than `thread` or `channel`, and a token lifetime that does not match
   the duration pattern are **silently not saved** (`backend/open_webui/routers/auths.py:1271-1293`).
4. The new translations are applied in the admin's own browser at once, the banner list is saved,
   the app reloads the public configuration and the success toast appears
   (`src/lib/components/admin/Settings/General.svelte:90-94`).

Because General and Authentication save the same set of keys, a panel left open in one browser tab
can undo a change made in another tab: whichever **Save** comes last writes all of these keys with
the values it loaded. The panels reload their values whenever they are opened, so working in one
tab at a time avoids this (`src/lib/components/admin/Settings/General.svelte:108-111`;
`src/lib/components/admin/Settings/Authentication.svelte:89-96`, `:109-113`).

### 5.4 Preset Interface Settings for Every Account

1. General › **UI** › **Default Interface Settings** › **Configure**. The help line reads
   `Set system-wide interface defaults for every account. Personal settings override these defaults.`
   (`src/lib/components/admin/Settings/General.svelte:424-450`).
2. The same controls as the personal **Interface** tab appear (`InterfaceSettings`), but changes
   only collect into a list; the number of collected settings is shown followed by
   `settings configured`, and **Clear** empties the list
   (`src/lib/components/admin/Settings/General.svelte:452-478`, `:71-73`).
3. Press **Save** on General. The list is stored as `ui.default_interface_settings`
   (`backend/open_webui/routers/auths.py:1276`).
4. Each user receives the defaults merged under their own saved choices whenever their settings
   are loaded (`backend/open_webui/routers/users.py:456-473`, `:57-69`), which happens when the app
   starts (`src/routes/(app)/+layout.svelte:67-71`). A value the user has saved wins over the default; a value
   inherited from the defaults shows the word **Default** beside the switch in their personal
   Interface tab (`src/lib/components/common/Switch.svelte:30-31`).
5. The fork's two switches are part of this list, so an admin can preset them for everyone:
   **Inline Citations** (`showInlineCitations`, code default on) and **Hide Processing Details**
   (`hideProcessingDetails`, code default off)
   (`src/lib/components/common/InterfaceSettings.svelte:79-80`, `:1334-1378`;
   `src/lib/i18n/locales/en-US/translation.json:2924`, `:2936`).
6. Users whose permissions do not include the Interface settings permission do not see the
   personal **Interface** tab, and the server discards any interface value they try to save, so for
   them the admin defaults apply to every interface option they had not saved before
   (`src/lib/components/chat/SettingsModal.svelte:393-395`;
   `backend/open_webui/routers/users.py:490-497`; the field list is `InterfaceSettings` in
   `backend/open_webui/models/users.py:67-100`). Permissions are covered in
   `users-groups-roles-and-permissions.md`.

### 5.5 Change the Wording of the Interface (UI Translations)

1. General › **UI** › **UI Translations** › the **+** button (**Add translation**)
   (`src/lib/components/admin/Settings/I18nSettings.svelte:28-50`).
2. Choose the language in the selector (it starts on the admin's current language; there is no
   "default" choice) (`src/lib/components/admin/Settings/I18nSettings.svelte:12-15`, `:34-38`).
3. In **Key**, type the exact text key: for most interface text this is the English wording exactly
   as written in the code, punctuation included (`Chat deleted.`); for settings-screen labels it is
   the dotted key name, such as `settings.admin.general.title`, not the English words (see
   section 4.1 and the i18n notes in `CLAUDE.md`).
4. In **Value**, type the replacement text for that language. Placeholders in double braces must
   match the key's placeholders exactly (section 7.4).
5. Press **Save** on General. The admin's browser shows the new wording at once
   (`src/lib/components/admin/Settings/General.svelte:91`); everyone else gets it the next time the
   app loads, because the overrides travel in the public configuration (`i18n` in `/api/config`,
   `backend/open_webui/main.py:2316`; loaded at start-up, `src/routes/+layout.svelte:1254`).
6. To remove an override, delete its row (the **×** button) and **Save**
   (`src/lib/components/admin/Settings/I18nSettings.svelte:73-82`).

### 5.6 Add, Reorder or Remove a Banner

General › **UI** › **Banners**: the **+** button (**Add banner**) adds a row (only when the last row
has content); each row has a type (Info, Warning, Error, Success), the content, a **Remember
Dismissal** switch and a delete button; rows can be dragged to reorder; a language selector lets
the admin type per-language content once banners exist
(`src/lib/components/admin/Settings/General.svelte:483-520`;
`src/lib/components/admin/Settings/Interface/Banners.svelte:37-99`). Banners are saved by General's
**Save**. Signed-in users see them in the chat top bar after their app next loads the banner list
(`src/routes/(app)/+layout.svelte:156-159`, `:225`; `src/lib/components/chat/Navbar.svelte:301-319`).
A dismissed banner with **Remember Dismissal** on stays hidden in that browser; with it off, it
comes back on the next page load (`src/lib/components/chat/Navbar.svelte:56-64`, `:304-316`).
Depth: `notifications-webhooks-events-and-banners.md`.

General's banner editor starts from the banner list the admin's browser loaded when the app
started, not a fresh copy (`src/lib/components/admin/Settings/General.svelte:113`), so saving
General after another admin changed banners can put the older list back.

### 5.7 Change Task Models and Generation Settings (Interface Panel)

1. Interface › **Tasks**: pick **Local Task Model** and **External Task Model**; `Current Model`
   means "use the model of the chat". Picking a model that is not public shows
   `This model is not publicly available. Please select another model.`
   (`src/lib/components/admin/Settings/Interface.svelte:93-113`, `:176-227`).
2. Optionally open **Task Model Parameters** › **Configure** to set parameters used for background
   tasks; empty values are not sent (`src/lib/components/admin/Settings/Interface.svelte:57-68`,
   `:229-254`).
3. **Chat** and **Generation** sections: switches and prompt templates (section 7.2). An empty
   prompt template means "use the built-in prompt" (placeholder text
   `Leave empty to use the default prompt, or enter a custom prompt`).
4. **Save**. The toast appears at once; to be sure the save worked, close and reopen the tab and
   check the values (section 11.3).

Depth: `chat-completion-pipeline-and-generation-tasks.md`.

### 5.8 Export the Settings

Database › **Config** › **Export Config** › **Export** downloads `config-<timestamp>.json`
(`src/lib/components/admin/Settings/Database.svelte:103-120`). The server returns every stored
setting, and while `ENABLE_OAUTH_PERSISTENT_CONFIG` is off it adds the single sign-on values the
server read from its environment (`backend/open_webui/routers/configs.py:118-120`;
`backend/open_webui/models/config.py:185-195`). **The file contains secrets** (provider API keys,
single sign-on client secrets, the LDAP bind password, web-search and other service keys) and can
contain personal data (for example the admin contact email). Handle it as a secret: do not attach
it to a ticket, chat or email, and tell anyone who has shared one to involve the platform
maintainer so the keys can be rotated.

### 5.9 Import Settings

1. Database › **Config** › **Import Config** › **Import**, then choose a `.json` file
   (`src/lib/components/admin/Settings/Database.svelte:60-101`).
2. The browser reads the file and sends its contents as `{"config": {...}}`
   (`src/lib/apis/configs/index.ts:4-32`).
3. The server writes **every key in the file**, as it is, in one go: there is no check that the
   keys are known or that values have the right shape, and keys absent from the file are left
   unchanged (`backend/open_webui/routers/configs.py:100-110`). Keys the database is not
   authoritative for (section 4.1) only change in the memory of the handling server process.
4. The server records a `config.imported` event listing the imported keys
   (`backend/open_webui/routers/configs.py:103-109`; `backend/open_webui/events.py:57-59`) and the
   panel shows `Config imported successfully`
   (`src/lib/components/admin/Settings/Database.svelte:77-79`).
5. Import only writes rows. It does not run the extra work some panels do on **Save**: rebuilding
   the embedding and reranking functions (`backend/open_webui/routers/retrieval.py:525-572`,
   `:1190-1248`), loading a local speech-to-text model
   (`backend/open_webui/routers/audio.py:305-310`), refreshing cached tool-server
   data and single sign-on clients for tool servers
   (`backend/open_webui/routers/configs.py:240-298`), and it does not refresh the open app's
   configuration. After an import, re-save the affected panels or restart the server; a restart
   rebuilds the embedding functions from stored values
   (`backend/open_webui/main.py:621-752`).

### 5.10 Download the Database and Export All Chats or Users

These rows sit in Database › **Export** and are shown only while `ENABLE_ADMIN_EXPORT` is on
(`src/lib/components/admin/Settings/Database.svelte:123-160`).

| Row | What it downloads | Server rule | Evidence |
|---|---|---|---|
| **Database** | The SQLite database file, saved as `webui.db` | Refused with `This feature is only available with SQLite databases.` when the database is not SQLite (for example PostgreSQL); refused with the `ACCESS_PROHIBITED` text when `ENABLE_ADMIN_EXPORT` is off | `backend/open_webui/routers/utils.py:74-90`; `src/lib/apis/utils/index.ts:98-132` |
| **All Chats** | Every user's chats as `all-chats-export-<timestamp>.json` | Admin only and `ENABLE_ADMIN_EXPORT` on | `src/lib/components/admin/Settings/Database.svelte:23-28`; `backend/open_webui/routers/chats.py:1049-1053` |
| **Users** | `users.csv` with the columns `id`, `name`, `email`, `role` | Admin only | `src/lib/components/admin/Settings/Database.svelte:30-51`; `backend/open_webui/routers/users.py:129-134` |

All three files hold personal data; the database and the chat export may hold health information,
because MedIT GPT chats can contain it. They must be stored and shared only as U of T data handling
rules allow (**TO BE CONFIRMED** with the data steward or Privacy Office). The **All Chats** and
**Users** buttons have no error handling, so a failure shows nothing
(`src/lib/components/admin/Settings/Database.svelte:23-51`).

### 5.11 Check the Version

General's first section shows **Version** (`v0.11.4`, with the build hash as a tooltip), a
**See what's new** button that opens the changelog, and, when `ENABLE_VERSION_UPDATE_CHECK` is on,
**Check for updates** (`src/lib/components/admin/Settings/General.svelte:133-185`). The check asks
the upstream Open WebUI release feed on GitHub, waiting at most one second, and shows
`(v{version.latest} available!)`, `(latest)` or `Could not check for updates`
(`backend/open_webui/main.py:2594-2613`; `src/lib/components/admin/Settings/General.svelte:142-158`). The version it reports is **upstream** Open WebUI, not a
MedIT GPT release; whether and how the fork is updated is **TO BE CONFIRMED**. `OFFLINE_MODE`
turns the check off (`backend/open_webui/env.py:1200-1205`).

### 5.12 Find a Setting

Type part of a setting's name into **Search** at the top of the tab list; the list shrinks to the
tabs that contain it; **Enter** opens the first. Section 4.3 explains what is and is not searchable.

## 6. Data Model

### 6.1 Where Admin Settings Live

| Store | What the admin panels keep there | Evidence |
|---|---|---|
| `config` table, one row per dotted key (`key` text primary key, `value` JSON, `updated_at` epoch **seconds**) | Almost every value on every panel | `backend/open_webui/models/config.py:101-108`, `:211-220` |
| Server process memory | `oauth.*` values while `ENABLE_OAUTH_PERSISTENT_CONFIG` is off, and every value while `ENABLE_PERSISTENT_CONFIG` is off; lost at restart and not shared between server processes | `backend/open_webui/models/config.py:132-147`, `:197-206` |
| Server process memory, derived | Objects built from settings: the embedding and reranking functions, a local speech-to-text model, cached tool-server data (also in Redis when configured) | `backend/open_webui/main.py:666-752`; `backend/open_webui/routers/audio.py:305-310`; `backend/open_webui/utils/tools.py:1170-1185` |
| Each user's `settings` (`ui` part) | Not written by the admin panels; the admin defaults are merged in when a user's settings are read | `backend/open_webui/routers/users.py:456-473` |
| The browser (`localStorage`) | Which banners a user dismissed (`dismissedBannerIds`) | `src/lib/components/chat/Navbar.svelte:58-64`, `:304-313` |
| The external pipelines server | Pipeline valves edited on the Pipelines tab | `src/lib/components/admin/Settings/Pipelines.svelte:66-71` |

Reads are direct database look-ups with no cache (`backend/open_webui/models/config.py:140-167`),
which is why most saved values apply to the next request without a restart. At start-up only the
keys without a row are inserted from the code defaults (`backend/open_webui/models/config.py:240-266`;
`backend/open_webui/config.py:42-45`), so after the first boot a changed environment variable does
not change a stored value. `RESET_CONFIG_ON_START=True` deletes every row at each start
(`backend/open_webui/main.py:363-364`; `backend/open_webui/config.py:48-49`).

### 6.2 Keys Saved by General and Authentication

The field names are what `/api/v1/auths/admin/config` sends and receives; the mapping is
`ADMIN_CONFIG_KEYS` (`backend/open_webui/routers/auths.py:104-136`). Code defaults come from
`DEFAULT_CONFIG` (`backend/open_webui/config.py:3082-3158`).

| Field | Config key | Shown on | Code default (environment variable) | Evidence for the default |
|---|---|---|---|---|
| `SHOW_ADMIN_DETAILS` | `auth.admin.show` | Authentication | on (`SHOW_ADMIN_DETAILS`) | `backend/open_webui/config.py:2170` |
| `ADMIN_EMAIL` | `auth.admin.email` | Authentication | none (`ADMIN_EMAIL`) | `backend/open_webui/config.py:2172` |
| `WEBUI_URL` | `webui.url` | General | empty (`WEBUI_URL`) | `backend/open_webui/config.py:1661` |
| `ENABLE_LOGIN_FORM` | `ui.enable_login_form` | Authentication | on (`ENABLE_LOGIN_FORM`) | `backend/open_webui/config.py:1666` |
| `ENABLE_SIGNUP` | `ui.enable_signup` | Authentication | on (`ENABLE_SIGNUP`; off when `WEBUI_AUTH` is off) | `backend/open_webui/config.py:1664` |
| `ENABLE_API_KEYS` | `auth.enable_api_keys` | Authentication | off (`ENABLE_API_KEYS`) | `backend/open_webui/config.py:2454` |
| `ENABLE_API_KEYS_ENDPOINT_RESTRICTIONS` | `auth.api_key.endpoint_restrictions` | Authentication | off | `backend/open_webui/config.py:2456-2462` |
| `API_KEYS_ALLOWED_ENDPOINTS` | `auth.api_key.allowed_endpoints` | Authentication | empty | `backend/open_webui/config.py:2464` |
| `DEFAULT_USER_ROLE` | `ui.default_user_role` | Authentication | `pending` (`DEFAULT_USER_ROLE`) | `backend/open_webui/config.py:1720` |
| `DEFAULT_GROUP_ID` | `ui.default_group_id` | Authentication | empty (none) (`DEFAULT_GROUP_ID`) | `backend/open_webui/config.py:1722` |
| `DEFAULT_INTERFACE_SETTINGS` | `ui.default_interface_settings` | General › UI | `{}` (`DEFAULT_INTERFACE_SETTINGS`, JSON) | `backend/open_webui/config.py:1712-1718` |
| `I18N` | `ui.i18n` | General › UI › UI Translations | `{}` | `backend/open_webui/config.py:3090` |
| `JWT_EXPIRES_IN` | `auth.jwt_expiry` | Authentication | `4w` (`JWT_EXPIRES_IN`) | `backend/open_webui/config.py:2466` |
| `ENABLE_COMMUNITY_SHARING` | `ui.enable_community_sharing` | General | on | `backend/open_webui/config.py:2096` |
| `ENABLE_MESSAGE_RATING` | `ui.enable_message_rating` | General | on | `backend/open_webui/config.py:2098` |
| `ENABLE_FOLDERS` | `folders.enable` | General | on | `backend/open_webui/config.py:2024` |
| `FOLDER_MAX_FILE_COUNT` | `folders.max_file_count` | General | empty (no limit) | `backend/open_webui/config.py:2026` |
| `AUTOMATION_MAX_COUNT` | `automations.max_count` | **not shown on any panel**; General re-sends the loaded value | empty | `backend/open_webui/config.py:2044` |
| `AUTOMATION_MIN_INTERVAL` | `automations.min_interval` | **not shown on any panel**; General re-sends the loaded value | empty | `backend/open_webui/config.py:2046` |
| `ENABLE_AUTOMATIONS` | `automations.enable` | General | on | `backend/open_webui/config.py:2034` |
| `ENABLE_CHANNELS` | `channels.enable` | General | **off** | `backend/open_webui/config.py:2028` |
| `CHANNEL_MODEL_RESPONSE_MODE` | `channels.model_response_mode` | General (when Channels is on) | `thread` | `backend/open_webui/config.py:2030` |
| `ENABLE_CALENDAR` | `calendar.enable` | General | on | `backend/open_webui/config.py:2032` |
| `ENABLE_MEMORIES` | `memories.enable` | General | on | `backend/open_webui/config.py:426` |
| `ENABLE_MEMORY_SYSTEM_CONTEXT` | `memories.system_context.enable` | General (when Memories is on) | on | `backend/open_webui/config.py:427` |
| `ENABLE_NOTES` | `notes.enable` | General | on | `backend/open_webui/config.py:2050` |
| `ENABLE_USER_WEBHOOKS` | `ui.enable_user_webhooks` | General | **off** | `backend/open_webui/config.py:2100` |
| `ENABLE_USER_STATUS` | `users.enable_status` | General | on | `backend/open_webui/config.py:2052` |
| `PENDING_USER_OVERLAY_TITLE` | `ui.pending_user_overlay_title` | Authentication | empty | `backend/open_webui/config.py:1724` |
| `PENDING_USER_OVERLAY_CONTENT` | `ui.pending_user_overlay_content` | Authentication | empty | `backend/open_webui/config.py:1726` |
| `RESPONSE_WATERMARK` | `ui.watermark` | General | empty | `backend/open_webui/config.py:1729` |

General also saves the banner list, `ui.banners` (code default from the `WEBUI_BANNERS` JSON
environment variable, otherwise an empty list), through `/api/v1/configs/banners`
(`backend/open_webui/config.py:2150-2167`, `:3126`; `backend/open_webui/routers/configs.py:852-869`).
Event webhooks, also on General, are stored under `events.webhooks`, which is not seeded and
appears on first save (`backend/open_webui/events.py:20`, `:838-841`).

### 6.3 Keys Saved by Interface

| Field | Config key | Code default (environment variable) | Evidence |
|---|---|---|---|
| `TASK_MODEL` | `task.model.default` | empty: the chat's model (`TASK_MODEL`) | `backend/open_webui/routers/tasks.py:42`; `backend/open_webui/config.py:2180` |
| `TASK_MODEL_EXTERNAL` | `task.model.external` | empty (`TASK_MODEL_EXTERNAL`) | `backend/open_webui/routers/tasks.py:43`; `backend/open_webui/config.py:2182` |
| `TASK_MODEL_PARAMS` | `task.model.params` | `{}` (`TASK_MODEL_PARAMS`, JSON) | `backend/open_webui/routers/tasks.py:44`; `backend/open_webui/config.py:2184-2190` |
| `ENABLE_TITLE_GENERATION` / `TITLE_GENERATION_PROMPT_TEMPLATE` | `task.title.enable` / `task.title.prompt_template` | on / empty | `backend/open_webui/routers/tasks.py:45`, `:54`; `backend/open_webui/config.py:2299`, `:2209` |
| `ENABLE_VOICE_MODE_PROMPT` / `VOICE_MODE_PROMPT_TEMPLATE` | `task.voice.prompt.enable` / `task.voice.prompt_template` | on / empty | `backend/open_webui/routers/tasks.py:59-60`; `backend/open_webui/config.py:2385`, `:2383` |
| `ENABLE_FOLLOW_UP_GENERATION` / `FOLLOW_UP_GENERATION_PROMPT_TEMPLATE` | `task.follow_up.enable` / `task.follow_up.prompt_template` | on / empty | `backend/open_webui/routers/tasks.py:51-52`; `backend/open_webui/config.py:2295`, `:2277` |
| `ENABLE_TAGS_GENERATION` / `TAGS_GENERATION_PROMPT_TEMPLATE` | `task.tags.enable` / `task.tags.prompt_template` | on / empty | `backend/open_webui/routers/tasks.py:50`, `:53`; `backend/open_webui/config.py:2297`, `:2234` |
| `ENABLE_RETRIEVAL_QUERY_GENERATION` | `task.query.retrieval.enable` | on | `backend/open_webui/routers/tasks.py:56`; `backend/open_webui/config.py:2304` |
| `ENABLE_SEARCH_QUERY_GENERATION` | `task.query.search.enable` | on | `backend/open_webui/routers/tasks.py:55`; `backend/open_webui/config.py:2302` |
| `QUERY_GENERATION_PROMPT_TEMPLATE` | `task.query.prompt_template` | empty | `backend/open_webui/routers/tasks.py:57`; `backend/open_webui/config.py:2307` |
| `ENABLE_AUTOCOMPLETE_GENERATION` / `AUTOCOMPLETE_GENERATION_INPUT_MAX_LENGTH` / `AUTOCOMPLETE_GENERATION_PROMPT_TEMPLATE` | `task.autocomplete.enable` / `.input_max_length` / `.prompt_template` | **off** / `-1` (no limit) / empty | `backend/open_webui/routers/tasks.py:47-49`; `backend/open_webui/config.py:2333-2337` |
| `IMAGE_PROMPT_GENERATION_PROMPT_TEMPLATE` | `task.image.prompt_template` | empty | `backend/open_webui/routers/tasks.py:46`; `backend/open_webui/config.py:2254` |
| `TOOLS_FUNCTION_CALLING_PROMPT_TEMPLATE` | `task.tools.prompt_template` | empty | `backend/open_webui/routers/tasks.py:58`; `backend/open_webui/config.py:2412` |
| `ENABLE_TOOL_PERMISSIONS` | `chat.tool_permissions.enable` | off | `backend/open_webui/routers/chats.py:58`; `backend/open_webui/config.py:2196` |
| `ENABLE_CONTEXT_COMPACTION` | `chat.context_compaction.enable` | off | `backend/open_webui/routers/chats.py:53`; `backend/open_webui/config.py:2194` |
| `CONTEXT_COMPACTION_MODEL` | `chat.context_compaction.model` | empty: the chat's model | `backend/open_webui/routers/chats.py:52`; `backend/open_webui/config.py:2192` |
| `CONTEXT_COMPACTION_TOKEN_THRESHOLD` | `chat.context_compaction.token_threshold` | 80000 | `backend/open_webui/routers/chats.py:54`; `backend/open_webui/config.py:2198` |
| `CONTEXT_COMPACTION_TOKEN_CAP` | `chat.context_compaction.token_cap` | none; shown as the threshold | `backend/open_webui/routers/chats.py:55`, `:220-221`; `backend/open_webui/config.py:2200-2201` |
| `CONTEXT_COMPACTION_RETENTION_PERCENTAGE` | `chat.context_compaction.retention_percentage` | 40, kept between 10 and 50 | `backend/open_webui/routers/chats.py:56`, `:845`; `backend/open_webui/config.py:2203-2205` |
| `CONTEXT_COMPACTION_PROMPT_TEMPLATE` | `chat.context_compaction.prompt_template` | empty | `backend/open_webui/routers/chats.py:57`; `backend/open_webui/config.py:2207` |

### 6.4 Other Keys Written Through `/api/v1/configs`

| Endpoint | Keys | Panel | Evidence |
|---|---|---|---|
| `POST /connections` | `direct.enable`, `direct.integrations.enable`, `models.base_models_cache` (only fields sent) | Connections, Integrations | `backend/open_webui/routers/configs.py:40-44`, `:144-160` |
| `POST /tool_servers` | `tool_server.connections` | Integrations | `backend/open_webui/routers/configs.py:240-298` |
| `POST /terminal_servers` | `terminal_server.connections` | Integrations | `backend/open_webui/routers/configs.py:331-352` |
| `POST /code_execution` | `code_execution.*`, `code_interpreter.*` (15 keys) | Code Execution | `backend/open_webui/routers/configs.py:45-61`, `:709-728` |
| `POST /models` | `ui.default_models`, `ui.default_pinned_models`, `ui.model_order_list`, `models.default_metadata`, `models.default_params` | Models | `backend/open_webui/routers/configs.py:62-68`, `:754-770` |
| `POST /subagents` | `subagents.enable`, `.background_enabled`, `.max_concurrent`, `.max_async`, `.max_iterations`, `.max_output`, `.system_prompt` | Sub-agents | `backend/open_webui/routers/configs.py:69-77`, `:788-804` |
| `POST /suggestions` | `ui.prompt_suggestions`, `ui.prompt_suggestions_i18n` | Models › Model Defaults | `backend/open_webui/routers/configs.py:807-840` |
| `POST /banners` | `ui.banners` | General | `backend/open_webui/routers/configs.py:848-869` |
| `POST /import` | any keys in the uploaded file | Database | `backend/open_webui/routers/configs.py:96-110` |

### 6.5 Endpoints in Scope

All paths below are under `/api/v1/configs` (`backend/open_webui/main.py:854`) unless written in
full.

| Method and path | Role | Purpose | Evidence |
|---|---|---|---|
| `POST /import` | admin | Write every key in the body | `backend/open_webui/routers/configs.py:100-110` |
| `GET /export` | admin | Return every stored setting | `backend/open_webui/routers/configs.py:118-120` |
| `GET /namespace/{namespace}` | admin | Return the keys under one dotted prefix, such as `ui`; no screen uses it | `backend/open_webui/routers/configs.py:123-125`; `backend/open_webui/models/config.py:169-183` |
| `GET` / `POST /connections` | admin | Direct connections, direct integrations, base model cache | `backend/open_webui/routers/configs.py:139-160` |
| `POST /oauth/clients/register` | admin | Register a single sign-on client for a tool server | `backend/open_webui/routers/configs.py:172-209` |
| `GET` / `POST /tool_servers`; `POST /tool_servers/verify` | admin | Tool server list and its connection test | `backend/open_webui/routers/configs.py:235-298`, `:551-680` |
| `GET` / `POST /terminal_servers`; `POST /terminal_servers/verify`, `/policy`, `/lifecycle`, `/refresh` | admin | Terminal server list and orchestrator actions | `backend/open_webui/routers/configs.py:326-548` |
| `GET` / `POST /code_execution` | admin | Code execution and interpreter settings | `backend/open_webui/routers/configs.py:704-728` |
| `GET /models/defaults` | any signed-in user | Default model metadata, for the model editor | `backend/open_webui/routers/configs.py:742-746` |
| `GET` / `POST /models` | admin | Default and pinned models, order, model defaults | `backend/open_webui/routers/configs.py:749-770` |
| `GET` / `POST /subagents` | admin | Sub-agent settings | `backend/open_webui/routers/configs.py:783-804` |
| `POST /suggestions` | admin | Default prompt suggestions | `backend/open_webui/routers/configs.py:817-840` |
| `GET /banners` | any signed-in user | Current banners | `backend/open_webui/routers/configs.py:872-877` |
| `POST /banners` | admin | Replace the banner list | `backend/open_webui/routers/configs.py:852-869` |
| `GET` / `POST /api/v1/auths/admin/config` | admin | General and Authentication values | `backend/open_webui/routers/auths.py:1204-1296` |
| `GET /api/v1/tasks/config`; `POST /api/v1/tasks/config/update` | read: signed-in user; save: admin | Interface task settings | `backend/open_webui/routers/tasks.py:108-138` |
| `GET` / `POST /api/v1/chats/config` | admin | Interface chat settings | `backend/open_webui/routers/chats.py:836-857` |
| `GET /api/v1/utils/db/download` | admin, with `ENABLE_ADMIN_EXPORT` | Database file | `backend/open_webui/routers/utils.py:74-90` |
| `GET /api/v1/chats/all/db` | admin, with `ENABLE_ADMIN_EXPORT` | All chats | `backend/open_webui/routers/chats.py:1049-1053` |
| `GET /api/v1/users/all` | admin | All users (used by the Users CSV) | `backend/open_webui/routers/users.py:129-134` |
| `GET /api/version/updates` | signed-in user | Upstream version check on General | `backend/open_webui/main.py:2594-2613` |

### 6.6 File and Value Shapes

| Item | Shape | Evidence |
|---|---|---|
| Settings export file | One JSON object: each property is a dotted key (for example `ui.enable_signup`), each value that key's stored value | `backend/open_webui/models/config.py:185-195`; `src/lib/components/admin/Settings/Database.svelte:109-115` |
| Import request | `{"config": <the export object>}` | `src/lib/apis/configs/index.ts:13-15`; `backend/open_webui/routers/configs.py:96-97` |
| `ui.i18n` | `{ "<language code>": { "<text key>": "<replacement>" } }`; empty replacements are dropped | `backend/open_webui/routers/auths.py:1221`, `:1252-1266`; `src/lib/utils/translationDictionary.ts:28-41` |
| `ui.banners` | A list of banners: `id`, `type`, optional `title`, `content`, `dismissible`, `timestamp` (epoch seconds) and optional per-language `i18n` | `backend/open_webui/config.py:2150-2157`; `src/lib/components/admin/Settings/General.svelte:498-508` |
| `ui.default_interface_settings` | An object of interface setting names and values, the same names a user's own `ui` settings use (for example `showInlineCitations`, `hideProcessingDetails`, `title.auto`) | `src/lib/components/common/InterfaceSettings.svelte:148-150`, `:357-358` |
| Users CSV | Header `id,name,email,role`; each present value in double quotes, a missing value left empty | `src/lib/components/admin/Settings/Database.svelte:33-47` |

## 7. Settings and Configuration

How to read the tables: **Label** is the English text from
`src/lib/i18n/locales/en-US/translation.json` (line given); **Key** is the `config` row the control
writes; **Code default** is what a new installation gets when the environment variable is unset
(live values are data, **TO BE CONFIRMED** for production); **Takes effect** uses the terms in
section 7.6.

### 7.1 General (`/admin/settings/general`)

Purpose: product information, site-wide feature switches, the public address of the site, event
webhooks, and the UI section (wording overrides, interface defaults for every account, banners).
Saved by the panel's **Save** (section 5.3).

#### 7.1.1 Information Rows (Not Settings)

| Label | What it shows | Evidence |
|---|---|---|
| **Version** (`:2412`) | `v0.11.4` and, on hover, the build hash; when the update check is on, the upstream check result | `src/lib/components/admin/Settings/General.svelte:133-161` |
| **See what's new** (`:2404`) | Opens the changelog window | `src/lib/components/admin/Settings/General.svelte:163-171` |
| **Check for updates** (`:2377`) | Runs the upstream check again; hidden when `ENABLE_VERSION_UPDATE_CHECK` is off | `src/lib/components/admin/Settings/General.svelte:174-184`; `backend/open_webui/env.py:1200` |
| **Help** (`:2388`) | "Discover how to use Open WebUI and seek support from the community." (`:2387`), with links to the upstream documentation, Discord, X and GitHub; these are upstream community links, not MedIT GPT support (see `knowledgebase/tools/ground-truth.md`, Contacts) | `src/lib/components/admin/Settings/General.svelte:187-227` |
| **License** (`:2389`) | Either the licence holder details from a licence file, or the upstream text `Upgrade to a licensed plan for enhanced capabilities, including custom theming and branding, and dedicated support.`; which licence exception MedIT GPT relies on is **TO BE CONFIRMED** | `src/lib/components/admin/Settings/General.svelte:229-271` |

The **Help** and **License** rows carry "Do not alter, remove, obscure, or replace" licence comments
and must stay as they are (`src/lib/components/admin/Settings/General.svelte:194-196`, `:230-232`).

#### 7.1.2 Features Section

Section title **Features** (`:2402`) (`src/lib/components/admin/Settings/General.svelte:274-416`).

| Label (line) | Description (line) | Key | Code default | Takes effect | Evidence (panel) |
|---|---|---|---|---|---|
| **Community Sharing** (`:2379`) | "Allow users to share chats with the Open WebUI community." (`:2378`) | `ui.enable_community_sharing` | on | Server at once; users' screens after reload | `General.svelte:275-284` |
| **Message Rating** (`:2395`) | "Let users rate assistant responses." (`:2394`) | `ui.enable_message_rating` | on | Users' screens after reload (the switch is read by the browser) | `General.svelte:285-291`; `backend/open_webui/main.py:2370` |
| **Folders** (`:2386`) | "Allow users to organize chats into folders." (`:2385`) | `folders.enable` | on | Server at once; screens after reload | `General.svelte:292-298` |
| **Folder Max File Count** (`:2384`), shown when Folders is on | "Maximum number of files allowed per folder." (`:2383`); placeholder `Leave empty for unlimited` | `folders.max_file_count` | empty (no limit) | Screens after reload | `General.svelte:300-313`; `src/lib/components/layout/Sidebar/Folders/FolderModal.svelte:47` |
| **Memories** (`:2391`) | "Allow users to save memories for more personalized responses." (`:2390`) | `memories.enable` | on | Server at once; screens after reload | `General.svelte:315-321` |
| **Memory System Context** (`:2393`), shown when Memories is on | "Include saved memories in the system context." (`:2392`) | `memories.system_context.enable` | on | Server at once (next message) | `General.svelte:322-334` |
| **Notes** (`:2399`) | "Allow users to create and manage notes." (`:2398`) | `notes.enable` | on | Screens after reload; the built-in notes tools for models follow it at once | `General.svelte:335-341`; `backend/open_webui/utils/tools.py:719` |
| **Channels** (`:2376`) | "Allow users to use channels for shared conversations." (`:2375`) | `channels.enable` | **off** | Server at once; screens after reload | `General.svelte:342-348` |
| **Model Response Mode** (`:2397`), shown when Channels is on | "Choose where model responses to root-level channel mentions are posted." (`:2396`); choices **Thread** or **Channel** | `channels.model_response_mode` | `thread` | Server at once | `General.svelte:349-364` |
| **Calendar** (`:2374`) | "Allow users to access calendar features." (`:2373`) | `calendar.enable` | on | Server at once; screens after reload | `General.svelte:365-371` |
| **Automations** (`:2371`) | "Allow users to create and run automations." (`:2370`) | `automations.enable` | on | Server at once; screens after reload | `General.svelte:372-378` |
| **User Webhooks** (`:2411`) | "Allow users to configure webhooks from their account." (`:2410`) | `ui.enable_user_webhooks` | **off** | Server at once; screens after reload | `General.svelte:379-385` |
| **User Status** (`:2409`) | "Show user status information in the app." (`:2408`) | `users.enable_status` | on | Server at once; screens after reload | `General.svelte:386-392` |
| **Response Watermark** (`:2401`) | "Append a watermark to assistant responses when configured." (`:2400`); placeholder `Enter a watermark for the response. Leave empty for none.` | `ui.watermark` | empty | Screens after reload | `General.svelte:394-403` |
| **WebUI URL** (`:2414`) | "Enter the public URL of your WebUI. This URL will be used to generate links in the notifications." (`:2413`); placeholder `e.g.) "http://localhost:3000"` | `webui.url` | empty (`WEBUI_URL`) | Server at once | `General.svelte:405-415` |

Notes on specific rows:

- **Response Watermark** is added only to the text a user copies with a response's copy button,
  after a blank line; it is not drawn in the chat itself
  (`src/lib/components/chat/Messages/ResponseMessage.svelte:237-247`).
- **WebUI URL** feeds links in channel notifications and in chat finished or failed events, the
  site's OpenSearch description, and the return address used when registering tool-server
  single sign-on clients (the request address is used when it is empty)
  (`backend/open_webui/routers/channels.py:941-943`; `backend/open_webui/utils/middleware.py:214`,
  `:4392`; `backend/open_webui/main.py:2920-2922`; `backend/open_webui/utils/oauth.py:514-515`). The
  production address is **TO BE CONFIRMED**.
- Each feature switch is documented in depth in its own document: Channels in
  `channels-and-direct-messages.md`, Memories in `memories.md`, Notes in `notes.md`, Calendar and
  Automations in `automations-calendar-and-timers.md`, Folders and Community Sharing in
  `chat-conversations-history-and-organisation.md`, Message Rating in
  `evaluations-feedback-and-analytics.md`, User Webhooks in
  `notifications-webhooks-events-and-banners.md`.

#### 7.1.3 Events Section (Event Webhooks)

Between **Features** and **UI**, General embeds the **Events** component: heading **Events**
(`:2380`), a **Webhooks** list (`:2382`) described as "Send product events as JSON to external
services. Chat destinations receive readable messages." (`:2381`)
(`src/lib/components/admin/Settings/General.svelte:418`;
`src/lib/components/admin/Settings/Events.svelte:692-705`). Webhooks are **not** saved by General's
**Save**: each webhook is created, changed or deleted in its own dialog straight away through
`/api/events/webhooks` (`src/lib/components/admin/Settings/Events.svelte:7-16`, `:355-386`;
`backend/open_webui/main.py:2499-2569`) and stored under `events.webhooks`. A legacy single
`webhook_url` value is turned into a webhook with id `default` at start-up
(`backend/open_webui/events.py:20-22`, `:854-862`; `backend/open_webui/main.py:369`). Depth:
`notifications-webhooks-events-and-banners.md`.

#### 7.1.4 UI Section

Section title **UI** (`:2403`) (`src/lib/components/admin/Settings/General.svelte:420-521`).

| Control | What it holds | Key | Code default | Takes effect | Evidence |
|---|---|---|---|---|---|
| **UI Translations** (`:2407`) with **Add translation** (`:2406`) | Rows of **Key** and **Value** per language (section 7.4) | `ui.i18n` | `{}` | The saving admin at once; everyone else on their next app load | `src/lib/components/admin/Settings/I18nSettings.svelte:28-85`; `General.svelte:421-423`, `:91` |
| **Default Interface Settings** (plain key) with **Configure** / **Close**; help line `Set system-wide interface defaults for every account. Personal settings override these defaults.` | Any of the personal Interface options, including **Inline Citations** and **Hide Processing Details** | `ui.default_interface_settings` | `{}` | Each user's next settings load (app start); a user's own saved choice wins | `General.svelte:424-481`; `backend/open_webui/routers/users.py:456-473` |
| **Banners** (`:2372`) with **Add banner** (`:2369`); help line `Create announcements shown to users in the app.` | Type, content (per language), **Remember Dismissal**, order | `ui.banners` | `[]` (`WEBUI_BANNERS`) | Users' next app load | `General.svelte:483-520`; `src/lib/components/admin/Settings/Interface/Banners.svelte:37-99` |

### 7.2 Interface (`/admin/settings/interface`)

Purpose: the models and prompts used for background tasks (titles, tags, follow-ups, search
queries, autocomplete, image prompts, tool calling, voice mode) and two chat-wide features (tool
approval modes and context compaction). It does **not** hold banners, prompt suggestions or user
interface defaults in v0.11.4 (see section 2.2). Saved by **Save** to two endpoints at once
(section 5.2). Depth: `chat-completion-pipeline-and-generation-tasks.md`.

| Section | Label (line) | Description (line) | Key | Code default |
|---|---|---|---|---|
| **Tasks** (`:2515`) | **Task Model** (`:2521`) | "Choose fallback models for background tasks. Current Model follows the active chat model." (`:2520`) | — (heading for the two below) | — |
| Tasks | **Local Task Model** (`:2504`) | — ; first choice `Current Model` | `task.model.default` | empty (chat's model) |
| Tasks | **External Task Model** (`:2497`) | — ; first choice `Current Model` | `task.model.external` | empty (chat's model) |
| Tasks | **Task Model Parameters** (`:2522`), **Configure** / **Close** | model parameter editor | `task.model.params` | `{}` |
| **Chat** (`:2513`) | **Tool Permissions** (`:2533`), marked experimental | "Show Full access and Ask for approval in the chat input menu." (`:2532`) | `chat.tool_permissions.enable` | off |
| Chat | **Context Compaction** (`:2492`) | "Summarize older chat history when the conversation context grows large." (`:2491`) | `chat.context_compaction.enable` | off |
| Chat (when on) | **Context Compaction Model** (`:2494`) | "Choose a dedicated model for context compaction summaries. Current Model follows the active chat model." (`:2493`) | `chat.context_compaction.model` | empty |
| Chat (when on) | **Token Threshold** (`:2531`) | "Older messages are summarized when estimated context exceeds this token limit." (`:2530`) | `chat.context_compaction.token_threshold` | 80000 |
| Chat (when on) | **Token Cap** (`:2529`) | "Model-specific context compaction thresholds cannot exceed this token limit." (`:2528`) | `chat.context_compaction.token_cap` | the threshold |
| Chat (when on) | **Retained Messages** (`:2510`), 10 to 50 | "Percentage of recent messages to keep after older messages are summarized." (`:2509`) | `chat.context_compaction.retention_percentage` | 40 |
| Chat (when on) | **Context Compaction Prompt** (`:2496`), variables listed under **Available variables** (`:2490`) | "Controls how older messages are rewritten into a running summary." (`:2495`) | `chat.context_compaction.prompt_template` | empty (built-in) |
| **Generation** (`:2514`) | **Title Generation** (`:2525`) | "Allow automatic names for new chats." (`:2524`) | `task.title.enable` | on |
| Generation (when on) | **Title Generation Prompt** (`:2527`) | "Shapes the short label generated for each chat." (`:2526`) | `task.title.prompt_template` | empty (built-in) |
| Generation | **Voice Mode Prompt** (`:2537`) | "Apply voice-specific instructions while voice mode is active." (`:2536`) | `task.voice.prompt.enable` | on |
| Generation (when on) | **Prompt Template** (`:2506`) | "Defines the behavior used for spoken conversations." (`:2505`) | `task.voice.prompt_template` | empty (built-in) |
| Generation | **Follow Up Generation** (`:2499`) | "Show suggested next questions after assistant responses." (`:2498`) | `task.follow_up.enable` | on |
| Generation (when on) | **Follow Up Generation Prompt** (`:2501`) | "Guides the suggestions shown after an assistant response." (`:2500`) | `task.follow_up.prompt_template` | empty (built-in) |
| Generation | **Tags Generation** (`:2517`) | "Create chat tags from conversation content." (`:2516`) | `task.tags.enable` | on |
| Generation (when on) | **Tags Generation Prompt** (`:2519`) | "Controls how chat tags are inferred." (`:2518`) | `task.tags.prompt_template` | empty (built-in) |
| Generation | **Retrieval Query Generation** (`:2512`) | "Rewrite user requests for knowledge retrieval." (`:2511`) | `task.query.retrieval.enable` | on |
| Generation | **Web Search Query Generation** (`:2539`) | "Rewrite user requests into web-search queries." (`:2538`) | `task.query.search.enable` | on |
| Generation | **Query Generation Prompt** (`:2508`) | "Shared prompt for retrieval and web-search query rewriting." (`:2507`) | `task.query.prompt_template` | empty (built-in) |
| Generation | **Autocomplete Generation** (`:2485`) | "Suggest completions while users type chat messages." (`:2484`) | `task.autocomplete.enable` | **off** |
| Generation (when on) | **Autocomplete Generation Input Max Length** (`:2487`); placeholder `-1 for no limit, or a positive integer for a specific limit` | "Limit how much draft text is sent for suggestion generation." (`:2486`) | `task.autocomplete.input_max_length` | -1 |
| Generation (when on) | **Autocomplete Generation Prompt** (`:2489`) | "Guides inline completions while users type a message." (`:2488`) | `task.autocomplete.prompt_template` | empty (built-in) |
| Generation | **Image Prompt Generation Prompt** (`:2503`) | "Rewrites user intent into an image-generation prompt." (`:2502`) | `task.image.prompt_template` | empty (built-in) |
| Generation | **Tools Function Calling Prompt** (`:2535`) | "Guides how the assistant formats tool and function calls." (`:2534`) | `task.tools.prompt_template` | empty (built-in) |

Panel evidence: `src/lib/components/admin/Settings/Interface.svelte:176-558`; keys and defaults in
section 6.3. Takes effect: server at once for every key (the task endpoints read the stored value on
each call, for example `backend/open_webui/routers/tasks.py:143`, `:173-177`); the admin's own
browser updates the Tool Permissions and Context Compaction flags immediately
(`src/lib/components/admin/Settings/Interface.svelte:74-85`); other users' screens (tool permission
menu, autocomplete) after reload (`backend/open_webui/main.py:2360-2361`, `:2368`).

The user-level counterparts, each user's own **Title Auto-Generation**, **Follow-Up
Auto-Generation** and **Chat Tags Auto-Generation** switches
(`src/lib/i18n/locales/en-US/translation.json:2987`, `:2919`, `:2893`), are personal settings in
`InterfaceSettings` and can be preset in General's Default Interface Settings; the admin switches
here turn the feature off for everyone (`src/lib/components/common/InterfaceSettings.svelte:30-33`).

### 7.3 Database (`/admin/settings/db`)

Purpose: move settings between installations and take admin exports. There is no **Save** button
and no "reset" action on this tab in v0.11.4; the destructive resets (upload directory, vector
storage) are in **Documents** › **Danger Zone** (`src/lib/components/admin/Settings/Documents.svelte:1547-1590`).

| Section | Label (line) | Description (line) | Button | What happens | Shown when | Evidence |
|---|---|---|---|---|---|---|
| **Config** (`:2191`) | **Import Config** (`:2190`) | "Import admin configuration from a JSON export file." (`:2189`) | **Import** | Section 5.9 | always | `src/lib/components/admin/Settings/Database.svelte:87-101` |
| Config | **Export Config** (`:2188`) | "Download the current admin configuration as JSON." (`:2187`) | **Export** | Section 5.8 | always | `src/lib/components/admin/Settings/Database.svelte:103-120` |
| **Export** (`:2192`) | **Database** (`:2186`) | "Download the application database when supported." (`:2185`) | **Database** | Section 5.10 | `ENABLE_ADMIN_EXPORT` on | `src/lib/components/admin/Settings/Database.svelte:123-140` |
| Export | **All Chats** (`:2184`) | "Download every user's chat history as JSON." (`:2183`) | **Export** | Section 5.10 | `ENABLE_ADMIN_EXPORT` on | `src/lib/components/admin/Settings/Database.svelte:142-149` |
| Export | **Users** (`:2195`) | "Download all users as CSV." (`:2194`) | **Export** | Section 5.10 | `ENABLE_ADMIN_EXPORT` on | `src/lib/components/admin/Settings/Database.svelte:151-158` |

Points to know:

- `ENABLE_ADMIN_EXPORT` is an environment variable (code default on); it is not stored and needs a
  restart to change (`backend/open_webui/config.py:2082`). The browser hides the **Export** section
  when the public configuration says it is off (`backend/open_webui/main.py:2373`).
- The database download works only for SQLite; on PostgreSQL the server answers with the
  `DB_NOT_SQLITE` text (`backend/open_webui/routers/utils.py:83-84`;
  `backend/open_webui/constants.py:97`). Which database production uses is **TO BE CONFIRMED**.
- Every file from this tab is sensitive: the settings export holds secrets; the database, chats
  and users files hold personal and possibly health data (sections 5.8 and 5.10).

### 7.4 UI Translations: Rules

| Rule | Message when broken | Checked by | Evidence |
|---|---|---|---|
| A row with a **Value** needs a **Key** | `Original text is required for translated rows.` | Browser, before saving | `src/lib/utils/translationDictionary.ts:58-61` |
| The same **Key** may appear only once | `Duplicate original text: {entry.content}` | Browser | `src/lib/utils/translationDictionary.ts:63-64` |
| A key cannot be blank or one of `__proto__`, `prototype`, `constructor` | `Invalid translation key: {key}` | Browser and server | `src/lib/utils/translationDictionary.ts:17`, `:73`; `backend/open_webui/routers/auths.py:1247`, `:1258-1259` |
| A language code cannot be blank or one of those words | `Invalid language: {locale}` | Browser and server | `src/lib/utils/translationDictionary.ts:31`; `backend/open_webui/routers/auths.py:1254-1255` |
| Placeholders in double braces (`{{count}}`) in the **Value** must be exactly those in the **Key** | `Interpolation placeholders do not match: {key}` (browser) or `Interpolation placeholders do not match: {locale}: {key}` (server) | Browser and server | `src/lib/utils/translationDictionary.ts:1-8`, `:19-23`; `backend/open_webui/routers/auths.py:1249-1250`, `:1260-1262` |
| Rows with an empty **Value** are dropped, and a language with no rows left is dropped | — | Browser and server | `src/lib/utils/translationDictionary.ts:33-36`; `backend/open_webui/routers/auths.py:1260-1265` |

How an override combines with the bundled text: for ordinary keys, the override for a language
replaces that language's bundled text; for settings-screen (dotted `settings.*`) keys the order is
this language's override, then this language's bundled text, then the English override, then the
English text (`src/lib/i18n/settings-translations.ts:4-19`; `src/lib/i18n/index.ts:16-22`). So an
override saved for one language does not change what users see in another language that has its own
translation of that text.

### 7.5 Map of the Other Panels

The tables below are deliberately compact: one row per setting or per group of provider-specific
fields. Each panel's deep document lists every field, its exact default and its behaviour. Label line
numbers refer to `src/lib/i18n/locales/en-US/translation.json`.

#### 7.5.1 Authentication (`/admin/settings/authentication`)

Purpose: who may sign up and how, default role and group, API keys, token lifetime, what pending
users see, LDAP and single sign-on. Depth: `authentication-and-sign-in.md` (password sign-in, sign-up,
pending accounts, API keys, tokens), `sso-oauth-oidc-and-scim.md` (OAuth / OIDC, LDAP group mapping).
Panel: `src/lib/components/admin/Settings/Authentication.svelte`.

| Section | Labels (lines) | Keys | Code default | Notes |
|---|---|---|---|---|
| **User Access** (`:2121`) | **Default User Role** (`:2061`), **Default Group** (`:2059`), **Login Form** (`:2085`), **New Sign Ups** (`:2089`), **API Keys** (`:2037`), **API Key Endpoint Restrictions** (`:2035`), **Allowed Endpoints** (`:2031`), **JWT Expiration** (`:2079`) | `ui.default_user_role`, `ui.default_group_id`, `ui.enable_login_form`, `ui.enable_signup`, `auth.enable_api_keys`, `auth.api_key.endpoint_restrictions`, `auth.api_key.allowed_endpoints`, `auth.jwt_expiry` | `pending`, none, on, on, off, off, empty, `4w` | `-1` shows `No expiration can pose security risks.` (`Authentication.svelte:243-251`) |
| **Pending Accounts** (`:2120`) | **Admin Details** (`:2025`), **Admin Contact Email** (`:2023`), **Pending User Overlay Title** (`:2097`), **Pending User Overlay Content** (`:2095`) | `auth.admin.show`, `auth.admin.email`, `ui.pending_user_overlay_title`, `ui.pending_user_overlay_content` | on, none, empty, empty | Shown to pending users in the activation overlay |
| **LDAP** (`:2118`) | **LDAP** (`:2083`), **Label** (`:2081`), **Host** (`:2077`), **Port** (`:2101`), **Application DN** (`:2039`), **Application DN Password** (`:2041`), **Attribute for Mail** (`:2043`), **Attribute for Username** (`:2045`), **Search Base** (`:2115`), **Search Filters** (`:2117`), **TLS** (`:2126`), **Certificate Path** (`:2051`), **Validate Certificate** (`:2136`), **Ciphers** (`:2053`), **Group Mapping** (`:2067`), **Auto-Create Groups** (`:2065`), **Group Attribute** (`:2073`) | `ldap.enable`, `ldap.server.*`, `ldap.group.enable_management`, `ldap.group.enable_creation` | LDAP off | Required fields are checked on save (`backend/open_webui/routers/auths.py:1325-1340`) |
| **OAuth / OIDC** (`:2119`) | **OAuth / OIDC** (`:2091`), **Provider Name** (`:2103`), **Provider URL** (`:2105`), **Client ID** (`:2055`), **Client Secret** (`:2057`), **Redirect URI** (`:2107`), **Scopes** (`:2113`), **Email Claim** (`:2063`), **Username Claim** (`:2134`), **Picture Claim** (`:2099`), **Sub Claim** (`:2123`), **OAuth Signup** (`:2093`), **Merge Accounts by Email** (`:2087`), **Auto Redirect** (`:2047`), **Allowed Domains** (`:2029`), **Role Mapping** (`:2109`), **Roles Claim** (`:2111`), **Admin Roles** (`:2027`), **Allowed Roles** (`:2033`), **Group Mapping** (`:2071`), **Auto-Create Groups** (`:2069`), **Group Claim** (`:2075`), **Blocked Groups** (`:2049`), **Update Email** (`:2128`), **Update Name** (`:2130`), **Update Picture** (`:2132`) | `oauth.*` (map at `backend/open_webui/routers/auths.py:1428-1463`) | from the environment | **Read-only while `ENABLE_OAUTH_PERSISTENT_CONFIG` is off** (code default), with the notice in section 10; provider registration always comes from the environment at start-up (`knowledgebase/tools/ground-truth.md`) |

#### 7.5.2 Connections (`/admin/settings/connections`)

Purpose: the model providers the server talks to. Depth: `model-connections-openai-ollama-and-direct.md`.

| Label (line) | Keys | Code default | Saves |
|---|---|---|---|
| **OpenAI API** (`:2179`) | `openai.enable` | on (`backend/open_webui/config.py:319`) | On change |
| **Manage OpenAI API Connections** (`:2177`), **Add Connection** (`:2168`) | `openai.api_base_urls`, `openai.api_keys`, `openai.api_configs` | `https://api.openai.com/v1` (`backend/open_webui/config.py:330-345`) | On add, edit or delete, and on **Save** |
| **Ollama API** (`:2178`) | `ollama.enable` | on (`backend/open_webui/config.py:237`) | On change |
| **Manage Ollama API Connections** (`:2176`) | `ollama.base_urls`, `ollama.api_configs` | derived from `OLLAMA_BASE_URL` (`backend/open_webui/config.py:238-262`) | On add, edit or delete, and on **Save** |
| **User Connections** (`:2181`) › **Direct Connections** (`:2172`) | `direct.enable` | off (`backend/open_webui/config.py:230`) | On change |
| **Cache Base Model List** (`:2170`), **Refresh** (`:2180`) | `models.base_models_cache` | off (`backend/open_webui/config.py:374`) | On change; **Refresh** reloads the model list |

Evidence: `src/lib/components/admin/Settings/Connections.svelte:56-123`, `:235-432`;
`backend/open_webui/routers/openai.py:305-310`; `backend/open_webui/routers/ollama.py:214-218`.

#### 7.5.3 Models (`/admin/settings/models`)

Purpose: the admin model list (visibility, access, order, import and export) and the defaults every
model inherits. Depth: `workspace-models-and-model-access.md`; built-in tool defaults also in
`builtin-native-tools.md`.

| Control (lines) | Keys or records | Code default | Saves |
|---|---|---|---|
| **Model Defaults** (`:2606`) › **Model Capabilities** (`:2605`), **Model Parameters** (`:2607`), **Prompt Suggestions** (`:2608`) | `models.default_metadata`, `models.default_params`, `ui.prompt_suggestions`, `ui.prompt_suggestions_i18n` | `{}`, `{}`, none (the app's built-in suggestions; an empty list turns suggestions off), `{}` (`backend/open_webui/config.py:1678-1709`) | **Save** |
| A model's menu › **Set as Selected Model** / **Set as Pinned Model** | `ui.default_models`, `ui.default_pinned_models` | none (`backend/open_webui/config.py:1674-1676`) | At once (`Model added to selected models` and similar) |
| Dragging models into order | `ui.model_order_list` | `[]` (`backend/open_webui/config.py:1687-1693`) | **Save** |
| **Import**, **Export**, **Manage**, **Reset**, **Enable All**, **Disable All**, **Show All**, **Hide All** (`:2609-2616`) | model records (the `model` table), not settings | — | At once |

Evidence: `src/lib/components/admin/Settings/Models.svelte:333-435`, `:859-955`;
`src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:105-150`;
`src/lib/components/admin/Settings/Models/ModelMenu.svelte:127-148`.

#### 7.5.4 Sub-agents (`/admin/settings/subagents`)

Purpose: whether models may delegate work to sub-agents, and their limits. Depth:
`chat-completion-pipeline-and-generation-tasks.md`.

| Label (line) | Key | Code default |
|---|---|---|
| **Enable sub-agents** (`:2634`) | `subagents.enable` | off |
| **Max concurrent** (`:2636`) | `subagents.max_concurrent` | 20 |
| **Enable background sub-agents** (`:2633`) | `subagents.background_enabled` | off |
| **Max background** (`:2635`) | `subagents.max_async` | 20 |
| **Max iterations** (`:2637`) | `subagents.max_iterations` | 30 |
| **Max output** (`:2638`) | `subagents.max_output` | 30000 |
| **System prompt** (`:2640`) | `subagents.system_prompt` | empty |

Evidence: `src/lib/components/admin/Settings/Subagents.svelte:59-194`;
`backend/open_webui/config.py:2036-2042`.

#### 7.5.5 Audio (`/admin/settings/audio`)

Purpose: speech-to-text and text-to-speech engines. Depth:
`audio-speech-to-text-and-text-to-speech.md`.

| Section | Labels (lines) | Keys | Code default |
|---|---|---|---|
| **Speech-to-Text** (`:1988`) | **Speech-to-Text Engine** (`:1991`), **Supported MIME Types** (`:2005`), **STT Model** (`:1999`, `:2003`) | `audio.stt.engine`, `audio.stt.supported_content_types`, `audio.stt.model`, `audio.stt.whisper_model` | engine empty (local Whisper), Whisper model `base` (`backend/open_webui/config.py:1562`, `:1586`) |
| Speech-to-Text, per engine | OpenAI, Deepgram, Azure, Mistral URL, key, region, locales, speakers and request format fields | `audio.stt.openai.*`, `audio.stt.deepgram.*`, `audio.stt.azure.*`, `audio.stt.mistral.*` | empty |
| **Text-to-Speech** (`:1989`) | **Text-to-Speech Engine** (`:2007`), **TTS Voice** (`:2018`), **TTS Model** (`:2015`), **Response Splitting** (`:1987`) | `audio.tts.engine`, `audio.tts.voice`, `audio.tts.model`, `audio.tts.split_on` | engine empty (shown as **Web API**, the browser's own speech), `alloy`, `tts-1`, `punctuation` (`backend/open_webui/config.py:1635-1642`; `src/lib/components/admin/Settings/Audio.svelte:511`) |
| Text-to-Speech, per engine | OpenAI, Azure, Mistral, ElevenLabs URL, key, region, output format and parameter fields | `audio.tts.openai.*`, `audio.tts.api_key`, `audio.tts.azure.*`, `audio.tts.mistral.*` | empty |

Evidence: `src/lib/components/admin/Settings/Audio.svelte:136-185`, `:259-735`;
`backend/open_webui/routers/audio.py:80-114`, `:290-325`. Saving with the local engine also loads the
Whisper model in the handling server process (`backend/open_webui/routers/audio.py:305-310`).

#### 7.5.6 Images (`/admin/settings/images`)

Purpose: image generation and image editing engines. Depth: `image-generation-and-editing.md`.

| Section | Labels (lines) | Keys | Code default |
|---|---|---|---|
| (top) | **Image Generation** (`:2442`) | `image_generation.enable` | off (`backend/open_webui/config.py:1351`) |
| **Create Image** (`:2467`) | **Image Generation Engine** (`:2444`), **Image Size** (`:2461`), **Steps** (`:2470`), **Image Prompt Generation** (`:2447`), model and per-engine URL, key, workflow fields | `image_generation.engine`, `.size`, `.steps`, `.prompt.enable`, `.model`, `image_generation.openai.*`, `.automatic1111.*`, `.comfyui.*`, `.gemini.*` | `openai`, `512x512`, 50, on (`backend/open_webui/config.py:1353-1367`) |
| **Edit Image** (`:2468`) | **Image Edit** (`:2436`), **Image Edit Engine** (`:2438`), model, size and per-engine fields | `images.edit.enable`, `images.edit.engine`, `images.edit.*` | off, `openai` (`backend/open_webui/config.py:1525-1527`) |

Evidence: `src/lib/components/admin/Settings/Images.svelte:110-219`, `:298-841`;
`backend/open_webui/routers/images.py:67-102`.

#### 7.5.7 Evaluations (`/admin/settings/evaluations`) and Analytics (`/admin/settings/analytics`)

Depth: `evaluations-feedback-and-analytics.md`.

| Control (lines) | Key | Code default |
|---|---|---|
| **Arena Models** switch (`:2366`) | `evaluation.arena.enable` | on (`backend/open_webui/config.py:2054`) |
| **Models** (`:2367`) › **Arena Models** list, **Add Arena Model** (`:2364`) | `evaluation.arena.models` | from `EVALUATION_ARENA_MODELS` (`backend/open_webui/config.py:2056-2065`) |

Evidence: `src/lib/components/admin/Settings/Evaluations.svelte:24-168`;
`backend/open_webui/routers/evaluations.py:33-36`, `:285-310`. **Analytics** is a dashboard with no
settings; it is listed only while `ENABLE_ADMIN_ANALYTICS` is on.

#### 7.5.8 Integrations (`/admin/settings/integrations`), Including External Knowledge

Depth: `workspace-tools-tool-servers-mcp-and-terminals.md` (tool and terminal servers);
`knowledge-bases.md` and `rag-retrieval-embeddings-and-vector-stores.md` (External Knowledge).

| Section (line) | Control (line) | Key or store | Saves |
|---|---|---|---|
| **Tools** (`:2482`) | **External Tool Servers** (`:2476`), **Add Connection** (`:2473`); types **OpenAPI** (`:2478`) and **MCP** (`:2477`) | `tool_server.connections` | On add, edit or delete, and on **Save** |
| **Terminal** (`:2481`) | **Open Terminal** (`:2479`) | `terminal_server.connections` | On each change |
| **Knowledge** (`:2480`) | **External Knowledge Sources** (`:2475`), **Add Connection** (`:2474`) | `external_knowledge.connections` and knowledge records | In the source dialog |
| **User Connections** (`:2181`) | **Direct Integrations** (`:2174`) | `direct.integrations.enable` (code default off, `backend/open_webui/config.py:231`) | On change |

Evidence: `src/lib/components/admin/Settings/Integrations.svelte:57-125`, `:179-370`;
`src/lib/components/admin/Settings/ExternalKnowledge.svelte:16-23`.

#### 7.5.9 Documents (`/admin/settings/documents`)

Purpose: how uploaded files are read, split, embedded and retrieved, upload limits, cloud pickers
and the danger-zone actions. Depth: `rag-retrieval-embeddings-and-vector-stores.md` (and
`files-uploads-and-storage.md` for the **Files** section).

| Section (line) | Main labels (lines) | Keys | Code default |
|---|---|---|---|
| **Content Extraction** (`:2332`) | **Content Extraction Engine** (`:2225`) and the engine's URL, key and parameter fields; **PDF Extract Images (OCR)** (`:2308`); **PDF Loader Mode** (`:2310`); **Supported Media MIME Types** (`:2343`); **Bypass Embedding and Retrieval** (`:2217`); **Text Splitter** (`:2345`); **Chunk Size** (`:2223`); **Chunk Overlap** (`:2221`); **Markdown Header Text Splitter** (`:2278`); **Chunk Min Size Target** (`:2219`); **Tokenizer Model** (`:2352`) | `rag.content_extraction_engine`, `rag.<engine>_*`, `rag.pdf_extract_images`, `rag.pdf_loader_mode`, `rag.content_extraction.supported_media_mime_types`, `rag.bypass_embedding_and_retrieval`, `rag.text_splitter`, `rag.chunk_size`, `rag.chunk_overlap`, `rag.enable_markdown_header_text_splitter`, `rag.chunk_min_size_target`, `rag.tokenizer_model` | engine empty (built-in loaders), bypass off, 1000, 100 (`backend/open_webui/config.py:868`, `:965`, `:1064`, `:1068`) |
| **Embedding** (`:2334`) | **Embedding Model Engine** (`:2251`), **Embedding Model** (`:2249`), the engine's API Base URL and API Key, **Embedding Batch Size** (`:2245`), **Async Embedding Processing** (`:2209`), **Embedding Concurrent Requests** (`:2247`) | `rag.embedding_engine`, `rag.embedding_model`, `rag.openai.*`, `rag.ollama.*`, `rag.azure_openai.*`, `rag.embedding_batch_size`, `rag.enable_async_embedding`, `rag.embedding_concurrent_requests` | engine empty (local), `sentence-transformers/all-MiniLM-L6-v2` (`backend/open_webui/config.py:1002`, `:1008`) |
| **Retrieval** (`:2337`) | **Full Context Mode** (`:2265`), **Hybrid Search** (`:2272`), **Enrich Hybrid Search Text** (`:2255`), **Reranking Engine** (`:2325`), **Reranking Model** (`:2327`), **Reranking Batch Size** (`:2323`), **Top K** (`:2354`), **Top K Reranker** (`:2356`), **Relevance Threshold** (`:2321`), **RAG Template** (`:2316`) | `rag.full_context`, `rag.enable_hybrid_search`, `rag.enable_hybrid_search_enriched_texts`, `rag.hybrid_bm25_weight`, `rag.reranking_*`, `rag.external_reranker_*`, `rag.top_k`, `rag.top_k_reranker`, `rag.relevance_threshold`, `rag.template` | off, off, 3, 3, 0.0 (`backend/open_webui/config.py:968-979`) |
| **Files** (`:2335`) | **Allowed File Extensions** (`:2199`), **Max Upload Size** (`:2282`), **Max Upload Count** (`:2280`), **Image Compression Width** (`:2276`), **Image Compression Height** (`:2274`) | `rag.file.allowed_extensions`, `rag.file.max_size`, `rag.file.max_count`, `file.image_compression_width`, `file.image_compression_height` | no size or count limit (`backend/open_webui/config.py:981-983`) |
| **Integration** (`:2336`) | **Google Drive** (`:2267`), **OneDrive** (`:2296`) | `google_drive.enable`, `onedrive.enable` | — |
| **Danger Zone** (`:2333`) | **Reset Upload Directory** (`:2329`), **Reset Vector Storage/Knowledge** (`:2331`), **Reindex Knowledge and Memory Vectors** (`:2319`) › **Reindex** (`:2317`) | actions, not settings; each asks for confirmation | — |

Changing the embedding engine or model shows the notice
`After changing the embedding model, reindex knowledge, knowledge search, and memory vectors for changes to take effect.`
(`src/lib/components/admin/Settings/Documents.svelte:1169`): saving is not enough; the reindex in
**Danger Zone** is also needed. Evidence: `src/lib/components/admin/Settings/Documents.svelte:110-298`,
`:438-1590`; keys at `backend/open_webui/routers/retrieval.py:254-427`.

#### 7.5.10 Web Search (`/admin/settings/web`)

Purpose: whether models may search the web, with which provider, and how pages are loaded. Depth:
`web-search-and-web-loading.md`.

| Section (line) | Main labels (lines) | Keys | Code default |
|---|---|---|---|
| **Search** (`:2696`) | **Web Search** (`:2718`), **Web Search Confirmation** (`:2720`), **Web Search Confirmation Content** (`:2722`), **Web Search Engine** (`:2724`), **Search Result Count** (`:2692`), **Concurrent Requests** (`:2651`), **Domain Filter List** (`:2655`), **Bypass Embedding and Retrieval** (`:2647`), **Bypass Web Loader** (`:2649`), **Trust Proxy Environment** (`:2712`) | `web.search.enable`, `web.search.confirmation.enable`, `web.search.confirmation.content`, `web.search.engine`, `web.search.result_count`, `web.search.concurrent_requests`, `web.search.domain.filter_list`, `web.search.bypass_embedding_and_retrieval`, `web.search.bypass_web_loader`, `web.search.trust_env` | off, off, —, none, 3, 0 (`backend/open_webui/config.py:1161-1196`) |
| Search, per provider | About 30 providers' API key, URL, engine and option fields, from **Bocha Search API Key** (`:2644`) to **You.com API Key** (`:2731`) | `web.search.<provider>_*` | empty |
| **Loader** (`:2695`) | **Web Loader Engine** (`:2716`), **Verify SSL Certificate** (`:2714`), **Timeout** (`:2709`), **Fetch URL Content Length Limit** (`:2662`), the loader's URL, key and timeout fields (Firecrawl, Tavily, Playwright, external loader), **Youtube Language** (`:2733`), **Youtube Proxy URL** (`:2735`) | `web.loader.engine`, `web.loader.ssl_verification`, `web.loader.timeout`, `web.loader.concurrent_requests`, `web.fetch.max_content_length`, `web.loader.*`, `rag.youtube_loader_language`, `rag.youtube_loader_proxy_url` | engine empty (`backend/open_webui/config.py:1202`) |

Evidence: `src/lib/components/admin/Settings/WebSearch.svelte:60-112`, `:173-1229`; keys at
`backend/open_webui/routers/retrieval.py:254-427`.

#### 7.5.11 Code Execution (`/admin/settings/code-execution`)

Depth: `code-execution-and-interpreter.md`.

| Section (line) | Labels (lines) | Keys | Code default |
|---|---|---|---|
| **Code Execution** (`:2165`) | **Enable Code Execution** (`:2162`), **Code Execution Engine** (`:2138`), **Jupyter URL** (`:2147`), **Jupyter Auth** (`:2140`), **Jupyter Token** (`:2143`) or **Jupyter Password** (`:2142`), **Code Execution Timeout** (`:2145`) | `code_execution.enable`, `code_execution.engine`, `code_execution.jupyter.*` | on, `pyodide` (`backend/open_webui/config.py:409-411`) |
| **Code Interpreter** (`:2166`) | **Enable Code Interpreter** (`:2164`), **Code Interpreter Engine** (`:2149`), the same Jupyter fields (`:2151-2158`), **Code Interpreter Prompt Template** (`:2160`) | `code_interpreter.enable`, `code_interpreter.engine`, `code_interpreter.jupyter.*`, `code_interpreter.prompt_template` | on, `pyodide` (`backend/open_webui/config.py:424-433`) |

Evidence: `src/lib/components/admin/Settings/CodeExecution.svelte:26-305`;
`backend/open_webui/routers/configs.py:45-61`.

#### 7.5.12 Pipelines (`/admin/settings/pipelines`)

Purpose: manage pipelines on an external pipelines server reached through an OpenAI-type connection.
Nothing here is stored in the `config` table. Depth: `functions-pipes-filters-actions-and-pipelines.md`.

| Section (line) | Controls (lines) | Stored |
|---|---|---|
| **Source** (`:2626`) | **Pipeline URL** (`:2624`), **Upload Pipeline** (`:2631`) with **Select a .py file** (`:2628`), **GitHub URL** (`:2618`) with **Install** (`:2619`) | on the pipelines server |
| **Pipelines** (`:2625`) | **Pipeline** (`:2622`) choice and delete | on the pipelines server |
| **Valves** (`:2627`) | The selected pipeline's valves, saved by **Save** | on the pipelines server |

Evidence: `src/lib/components/admin/Settings/Pipelines.svelte:51-494`.

### 7.6 When a Change Takes Effect

| Term used above | Meaning | Evidence |
|---|---|---|
| **Server at once** | The server reads the stored value on the next request that needs it; no restart | `backend/open_webui/models/config.py:140-167` |
| **The saving admin at once** | Panels that reload the public configuration after saving (General, Authentication, Connections, Images, Audio, Documents, Web Search, Code Execution, Model Defaults) update the admin's own screen immediately | `src/lib/components/chat/SettingsModal.svelte:460-464`; `src/lib/components/admin/Settings/General.svelte:93`; `src/lib/components/admin/Settings/Authentication.svelte:105` |
| **Users' screens after reload** | Every other open browser keeps the configuration it loaded at start-up; feature switches, banners, translations and similar appear or disappear after a page reload or a new sign-in | `src/routes/+layout.svelte:1238-1290` |
| **Next settings load** | Default interface settings reach a user when their settings are next read, which is at app start | `src/routes/(app)/+layout.svelte:67-71`; `backend/open_webui/routers/users.py:456-473` |
| **Process only** | A key the database is not authoritative for changes only in the server process that handled the save and reverts at restart (section 4.1) | `backend/open_webui/models/config.py:197-206` |
| **Rebuilt in the handling process** | Embedding and reranking functions and a local Whisper model are rebuilt only by their own panel's save, only in the process that handled it; other server processes keep the old one until restart, and an import does not rebuild them | `backend/open_webui/routers/retrieval.py:525-572`, `:1190-1248`; `backend/open_webui/routers/audio.py:305-310`; `backend/open_webui/main.py:621-752` |
| **Restart** | Environment-only settings (section 7.7) and anything read only at start-up | `knowledgebase/tools/ground-truth.md`, Settings |
| **Re-save and reindex** | A new embedding model also needs **Reindex Knowledge and Memory Vectors** | `src/lib/components/admin/Settings/Documents.svelte:1169`, `:1576-1590` |

### 7.7 Environment-Only Settings That Shape the Panels

None of these is stored or editable in the panels; each needs the environment changed and the
server restarted. Production values are **TO BE CONFIRMED**.

| Variable | Code default | Effect on the panels | Evidence |
|---|---|---|---|
| `ENABLE_PERSISTENT_CONFIG` | on | Off makes every panel's saves process-only and lost at restart | `backend/open_webui/config.py:3231`; `backend/open_webui/models/config.py:132-138` |
| `ENABLE_OAUTH_PERSISTENT_CONFIG` | off | Off makes Authentication › OAuth / OIDC read-only, and the export carries the environment's OAuth values | `backend/open_webui/config.py:3232`; `src/lib/components/admin/Settings/Authentication.svelte:52`, `:550-563`; `backend/open_webui/models/config.py:193-194` |
| `RESET_CONFIG_ON_START` | off | On wipes every stored setting at each start, so every panel returns to the code defaults after a restart | `backend/open_webui/env.py:368`; `backend/open_webui/main.py:363-364` |
| `ENABLE_ADMIN_EXPORT` | on | Off hides Database › **Export** and refuses the database and all-chats downloads | `backend/open_webui/config.py:2082`; `backend/open_webui/routers/utils.py:77-78`; `backend/open_webui/routers/chats.py:1051-1052` |
| `ENABLE_ADMIN_ANALYTICS` | on | Off removes the **Analytics** tab | `backend/open_webui/config.py:2094`; `src/lib/components/chat/SettingsModal.svelte:409-411` |
| `ENABLE_VERSION_UPDATE_CHECK`, `OFFLINE_MODE` | on, off | The update check on General; offline mode turns it off | `backend/open_webui/env.py:1200-1205` |
| `ENABLE_PLUGINS` | on | Off removes the **Functions** link from the Admin Panel top bar | `backend/open_webui/env.py:1186`; `src/routes/(app)/admin/+layout.svelte:18-23`, `:87-95` |
| `USE_SLIM_DOCKER` | off | On shows slim-image notices on Documents and Audio and refuses local engines on save | `backend/open_webui/env.py:45`; `src/lib/components/admin/Settings/Documents.svelte:427-433`; `backend/open_webui/routers/audio.py:292-297` |
| `WEBUI_NAME` | `MedIT GPT` (fork) | The name in the Admin Panel browser title | `backend/open_webui/env.py:951` |

## 8. Cron Jobs and Background Processes

There is no scheduled job for settings. Every panel write happens **at save time**, inside the
request that saves it. The settings-related work outside a save is all at start-up:

| When | What happens | Evidence |
|---|---|---|
| Module import, before serving | Database migrations run (they also created the per-key `config` layout) | `backend/open_webui/config.py:81-82`; `knowledgebase/tools/ground-truth.md`, Data Stores |
| Start-up, step 1 | If `RESET_CONFIG_ON_START` is on, every `config` row is deleted | `backend/open_webui/main.py:363-364`; `backend/open_webui/config.py:48-49` |
| Start-up | A legacy `config.json` is imported if present; then old `rag.web.*` keys are renamed to `web.*`, flattened rows are repaired, and missing keys are seeded from the code defaults | `backend/open_webui/main.py:366-367`; `backend/open_webui/config.py:42-45`; `backend/open_webui/models/config.py:240-382` |
| Start-up | Runtime objects are built from stored values: single sign-on clients for MCP tool servers, the embedding and reranking functions | `backend/open_webui/main.py:368`, `:621-752` |
| Start-up | A legacy single `webhook_url` becomes an event webhook with id `default` | `backend/open_webui/main.py:369`; `backend/open_webui/events.py:854-862` |
| After a save or import | Several saves publish a configuration event; event webhooks that subscribe to it are delivered in the background (an asyncio task), not in the save request | `backend/open_webui/routers/configs.py:103-109`, `:152-159`, `:290-297`, `:344-351`, `:715-727`, `:758-769`, `:796-803`, `:832-839`, `:861-868`; `backend/open_webui/events.py:1062-1071`, `:1174-1202` |

Saves through `/api/v1/auths/admin/config` (General, Authentication), the Interface endpoints and
the retrieval settings update (Documents, Web Search) publish no event
(`backend/open_webui/routers/auths.py:1269-1296`; `backend/open_webui/routers/tasks.py:135-138`;
`backend/open_webui/routers/chats.py:841-857`; `backend/open_webui/routers/retrieval.py:962-1400`).

## 9. Notifications and Emails

The application sends no email (`knowledgebase/tools/ground-truth.md`). For this area:

- **Toasts** in the admin's browser confirm or refuse a save (section 10).
- **Configuration events.** These saves publish an event that admin-configured event webhooks can
  receive: `config.imported` ("Configuration was imported."), `config.connections.updated`,
  `config.tool_servers.updated`, `config.terminal_servers.updated`,
  `config.code_execution.updated`, `config.models.updated`, `config.banners.updated`,
  `config.suggestions.updated`, `config.webhook.updated` for event webhook changes, and
  `config.updated` for the Sub-agents, Audio, Images and Evaluations saves
  (`backend/open_webui/events.py:57-97`; `backend/open_webui/routers/configs.py:103-109`, `:796-803`;
  `backend/open_webui/routers/audio.py:313-322`; `backend/open_webui/routers/images.py:309`;
  `backend/open_webui/routers/evaluations.py:315`; `backend/open_webui/main.py:2519-2577`). The import event carries the list of imported key
  names, not their values (`backend/open_webui/routers/configs.py:108`). Webhook set-up and
  delivery: `notifications-webhooks-events-and-banners.md`.
- **Banners** are the in-app announcement channel an admin controls from General (section 5.6).
- **WebUI URL** is what links in channel notifications and chat events point to (section 7.1.2).
- No socket event tells open browsers that a setting changed; they pick up new values on reload
  (section 7.6).

## 10. Error, Warning and Notice Messages (Verbatim)

Plain-key texts display as written. Dotted labels are resolved in section 7. "Console only" means
the panel does not catch the error, so the admin sees no toast and the text appears only in the
browser's developer console (section 5.2). Paths are repository-relative; `translationDictionary`
is `src/lib/utils/translationDictionary.ts`.

### 10.1 Settings Window, General, UI Translations

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Settings saved successfully!` | Success | `src/lib/components/chat/SettingsModal.svelte:461` (General, Documents, Web Search, Code Execution), `:860`, `:882`, `:888`, `:894`, `:900`, `:906`; `src/lib/components/admin/Settings/Authentication.svelte:104`; `src/lib/components/admin/Settings/Subagents.svelte:50`; `src/lib/components/admin/Settings/Evaluations.svelte:32` | A panel saved. On **Interface** and the **Connections** **Save** it appears before the save finishes, even if the save fails | None | For Interface or Connections, reopen the tab and check the values (11.3) |
| `Matching tabs: {count}` | Notice (screen reader) | `src/lib/components/chat/SettingsModal.svelte:546-552` | Text typed in **Search** and some tabs match | — | — |
| `No matches` | Notice | `src/lib/components/chat/SettingsModal.svelte:550`, `:781-785` | No tab matches the search | Try a setting's label words | Plain-key text is not indexed (4.3) |
| `Failed to update settings` | Error | `src/lib/components/admin/Settings/General.svelte:90` | General's save returned no data | Retry once | Escalate with the time; the server log shows the request |
| `{error.message}` | Error | `src/lib/components/admin/Settings/General.svelte:95-102` | Any failure while saving General: the error's text, or the server's validation messages one per line | Read the text; it is one of the rows below | — |
| `Original text is required for translated rows.` | Error | `translationDictionary:58-61`, shown by `General.svelte:96` | A UI Translations row has a **Value** but no **Key** | Fill in the key or delete the row | — |
| `Duplicate original text: {entry.content}` | Error | `translationDictionary:63` | Two rows have the same **Key** | Keep one row per key | — |
| `Invalid translation key: {key}` | Error | `translationDictionary:17`; `backend/open_webui/routers/auths.py:1258-1259` | A key is blank or a reserved word | Change the key | — |
| `Translation must be a string: {key}` | Error | `translationDictionary:18` | A translation is not text (not reachable from the editor in normal use) | — | Escalate if seen |
| `Interpolation placeholders do not match: {key}` | Error | `translationDictionary:19-23` | The **Value** has different `{{…}}` placeholders from the **Key** | Copy the placeholders exactly | — |
| `Interpolation placeholders do not match: {locale}: {key}` | Error | `backend/open_webui/routers/auths.py:1260-1262` | Same check made by the server | As above | — |
| `Invalid language: {locale}` | Error | `translationDictionary:31`; `backend/open_webui/routers/auths.py:1254-1255` | A language code is blank or reserved | Pick a language from the selector | — |
| `I18N must be a dictionary` | Error | `backend/open_webui/routers/auths.py:1245-1246` | The save carried an empty translations value (General always sends an object; possible after an import stored `ui.i18n` as `null`) | — | Escalate: check `ui.i18n` in a settings export |
| `Could not check for updates` | Notice | `src/lib/components/admin/Settings/General.svelte:143-146` | The upstream release check failed or timed out (one second) | None | Outbound access to GitHub is an infrastructure question, **TO BE CONFIRMED** |
| `Checking for updates...` | Notice | `src/lib/components/admin/Settings/General.svelte:153-154` | Check in progress | — | — |
| `(v{version.latest} available!)` | Notice | `src/lib/components/admin/Settings/General.svelte:155-156` | A newer **upstream** Open WebUI release exists | None; this is not a MedIT GPT release | Fork update process is **TO BE CONFIRMED** |
| `(latest)` | Notice | `src/lib/components/admin/Settings/General.svelte:157` | Running the latest upstream version | — | — |
| `Upgrade to a licensed plan for enhanced capabilities, including custom theming and branding, and dedicated support.` | Notice | `src/lib/components/admin/Settings/General.svelte:266-268` | No licence file is loaded | None (upstream text) | — |
| `Set system-wide interface defaults for every account. Personal settings override these defaults.` | Help | `src/lib/components/admin/Settings/General.svelte:435-437` | Always, under Default Interface Settings | — | — |
| `settings configured` (after a number) | Notice | `src/lib/components/admin/Settings/General.svelte:455-458` | Default Interface Settings is open | — | — |
| `Create announcements shown to users in the app.` | Help | `src/lib/components/admin/Settings/General.svelte:516-518` | Always, under Banners | — | — |
| `Leave empty for unlimited` | Placeholder | `src/lib/components/admin/Settings/General.svelte:309` | Folder Max File Count is empty | — | — |
| `Enter a watermark for the response. Leave empty for none.` | Placeholder | `src/lib/components/admin/Settings/General.svelte:400` | Response Watermark is empty | — | — |

### 10.2 Interface and Database

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `This model is not publicly available. Please select another model.` | Error | `src/lib/components/admin/Settings/Interface.svelte:103-110` | A task or compaction model was chosen whose access grants do not include read access for everyone | Choose another model, or widen that model's access (an admin decision) | The model's access in `workspace-models-and-model-access.md` |
| `Failed to load Interface settings` (or the server's message instead) | Error | `src/lib/components/admin/Settings/Interface.svelte:150-155` | Loading the task or chat settings or the model list failed | Reload the page | Escalate with the time and any message shown |
| `Leave empty to use the default prompt, or enter a custom prompt` | Placeholder | `src/lib/components/admin/Settings/Interface.svelte:352`, `:385`, `:408`, `:431`, `:454`, `:489`, `:531`, `:544`, `:555` | A prompt template is empty | — | Empty means the built-in prompt |
| `-1 for no limit, or a positive integer for a specific limit` | Placeholder | `src/lib/components/admin/Settings/Interface.svelte:517` | Autocomplete input length is empty | — | — |
| `Config imported successfully` | Success | `src/lib/components/admin/Settings/Database.svelte:77-79` | An import was written | Re-save panels with side effects or ask for a restart (5.9) | — |
| `{error}` | Error | `src/lib/components/admin/Settings/Database.svelte:71-75`; `src/lib/apis/configs/index.ts:21-29` | **Import** was refused; the server's text is shown, and it may read `[object Object]` when the file is not a JSON object of settings | Use an unmodified export file | Escalate; never attach the file (it contains secrets) |
| `This feature is only available with SQLite databases.` | Error | `backend/open_webui/routers/utils.py:83-84`; `backend/open_webui/constants.py:97`; shown by `src/lib/components/admin/Settings/Database.svelte:132-134` | **Database** download on a non-SQLite database | None; database backups are an infrastructure task, **TO BE CONFIRMED** | Which database production uses is **TO BE CONFIRMED** |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error | `backend/open_webui/routers/utils.py:77-78`; `backend/open_webui/routers/chats.py:1051-1052`; every admin-only endpoint in 6.5 | Database or all-chats download while `ENABLE_ADMIN_EXPORT` is off, or any admin endpoint called without the admin role | — | Check the role; ask the maintainer about `ENABLE_ADMIN_EXPORT` |

### 10.3 Other Panels' Save and Validation Messages

The remaining messages of these panels are catalogued in their deep documents.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `These settings are read from environment variables and cannot be edited here while {ENV_VAR} is disabled.` (`ENV_VAR` is `ENABLE_OAUTH_PERSISTENT_CONFIG`) | Notice | `src/lib/components/admin/Settings/Authentication.svelte:550-559` | OAuth settings are not persisted | Changes need the environment and a restart | `sso-oauth-oidc-and-scim.md` |
| `No expiration can pose security risks.` | Warning | `src/lib/components/admin/Settings/Authentication.svelte:243-251` | **JWT Expiration** is `-1` | — | `authentication-and-sign-in.md` |
| `Required field {name} is empty` | Error | `backend/open_webui/routers/auths.py:1332-1340`; `backend/open_webui/constants.py:131` | An LDAP save is missing a required field | Fill in the field | `sso-oauth-oidc-and-scim.md` |
| `OpenAI API settings updated` | Success | `src/lib/components/admin/Settings/Connections.svelte:87` | OpenAI connections saved | — | — |
| `Ollama API settings updated` | Success | `src/lib/components/admin/Settings/Connections.svelte:107` | Ollama connections saved | — | — |
| `Connections settings updated` | Success | `src/lib/components/admin/Settings/Connections.svelte:119`; `src/lib/components/admin/Settings/Integrations.svelte:67` | Direct connections, cache or direct integrations switch saved | — | — |
| `Model list refreshed` | Success | `src/lib/components/admin/Settings/Connections.svelte:130` | **Refresh** pressed | — | — |
| `Models configuration saved successfully` | Success | `src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:143` | Model Defaults saved | — | — |
| `Failed to save models configuration` | Error | `src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:146-147` | Model Defaults save refused | Retry; escalate | `workspace-models-and-model-access.md` |
| `Model order saved successfully` | Success | `src/lib/components/admin/Settings/Models.svelte:350` | Order saved | — | — |
| `Model added to selected models` | Success | `src/lib/components/admin/Settings/Models.svelte:416-417` | **Set as Selected Model** | — | — |
| `Model removed from selected models` | Success | `src/lib/components/admin/Settings/Models.svelte:416` | **Remove Selected Model** | — | — |
| `Model added to pinned models` | Success | `src/lib/components/admin/Settings/Models.svelte:431-432` | **Set as Pinned Model** | — | — |
| `Model removed from pinned models` | Success | `src/lib/components/admin/Settings/Models.svelte:431` | **Remove Pinned Model** | — | — |
| `Failed to save connections` | Error | `src/lib/components/admin/Settings/Integrations.svelte:80-82` | Tool server list save refused | Retry; escalate | `workspace-tools-tool-servers-mcp-and-terminals.md` |
| `Connections saved successfully` | Success | `src/lib/components/admin/Settings/Integrations.svelte:85-87` | Tool server list saved | — | — |
| `Failed to save terminal servers` | Error | `src/lib/components/admin/Settings/Integrations.svelte:93-95` | Terminal server list save refused | Retry; escalate | same |
| `Terminal servers saved` | Success | `src/lib/components/admin/Settings/Integrations.svelte:98-99` | Terminal server list saved | — | — |
| `Use a valid event name or pattern like user.*` | Error | `src/lib/components/admin/Settings/Events.svelte:228` | A webhook event filter is malformed | Correct the pattern | `notifications-webhooks-events-and-banners.md` |
| `Webhook saved` | Success | `src/lib/components/admin/Settings/Events.svelte:355` | Webhook created or changed | — | — |
| `Failed to save webhook` (or the server's text) | Error | `src/lib/components/admin/Settings/Events.svelte:357` | Webhook save refused. *Corrected 2026-10-10: the server's text is never shown; the API client throws the parsed response object (`src/lib/apis/index.ts:1656-1675`), so the `typeof error === 'string'` test fails and the generic text always appears.* | Retry; escalate | same |
| `Webhook deleted` | Success | `src/lib/components/admin/Settings/Events.svelte:370` | Webhook deleted | — | — |
| `Failed to delete webhook` (or the server's text) | Error | `src/lib/components/admin/Settings/Events.svelte:372` | Delete refused | Retry; escalate | same |
| `Failed to update webhook` (or the server's text) | Error | `src/lib/components/admin/Settings/Events.svelte:386` | Enable or disable switch refused | Retry; escalate | same |
| `Invalid JSON format for Parameters` | Error | `src/lib/components/admin/Settings/Audio.svelte:139-144` | Text-to-speech parameters are not valid JSON | Fix the JSON | `audio-speech-to-text-and-text-to-speech.md` |
| `Local Whisper is unavailable in slim. Select an external speech-to-text engine.` | Error (console only) | `backend/open_webui/routers/audio.py:293-295` | Choosing local Whisper on the slim image | Pick an external engine | same |
| `Local TTS is unavailable in slim. Select an external text-to-speech engine.` | Error (console only) | `backend/open_webui/routers/audio.py:296-297` | Choosing local text-to-speech on the slim image | Pick an external engine | same |
| `AUTOMATIC1111 Base URL is required.` | Error | `src/lib/components/admin/Settings/Images.svelte:111-118` | Engine AUTOMATIC1111 without a URL; Image Generation is switched off in the form | Enter the URL | `image-generation-and-editing.md` |
| `ComfyUI Base URL is required.` | Error | `src/lib/components/admin/Settings/Images.svelte:119-123` | Engine ComfyUI without a URL | Enter the URL | same |
| `OpenAI API Key is required.` | Error | `src/lib/components/admin/Settings/Images.svelte:124-128` | Engine OpenAI without a key | Enter the key | same |
| `Gemini API Key is required.` | Error | `src/lib/components/admin/Settings/Images.svelte:129-133` | Engine Gemini without a key | Enter the key | same |
| `Invalid JSON format for ComfyUI Workflow.` | Error | `src/lib/components/admin/Settings/Images.svelte:181` | Workflow text is not JSON | Fix the workflow | same |
| `Invalid JSON format for ComfyUI Edit Workflow.` | Error | `src/lib/components/admin/Settings/Images.svelte:198` | Edit workflow text is not JSON | Fix the workflow | same |
| `Model filesystem path detected. Model shortname is required for update, cannot continue.` | Error | `src/lib/components/admin/Settings/Documents.svelte:83-105` | Local embedding model given as a path, or an empty model for Ollama or OpenAI | Enter a model name | `rag-retrieval-embeddings-and-vector-stores.md` |
| `OpenAI URL/Key required.` | Error | `src/lib/components/admin/Settings/Documents.svelte:106-115` | OpenAI or Azure embedding engine without URL or key. *Corrected 2026-10-10: this text belongs to the **Azure OpenAI** engine only (`src/lib/components/admin/Settings/Documents.svelte:109-113`).* | Fill both | same |
| `External Document Loader URL required.` | Error | `src/lib/components/admin/Settings/Documents.svelte:169` | External loader chosen without a URL | Enter the URL | same |
| `Headers must be a valid JSON object` | Error | `src/lib/components/admin/Settings/Documents.svelte:183` | Loader headers are not a JSON object | Fix the JSON | same |
| `Tika Server URL required.` | Error | `src/lib/components/admin/Settings/Documents.svelte:188` | Tika chosen without a URL | Enter the URL | same |
| `Docling Server URL required.` | Error | `src/lib/components/admin/Settings/Documents.svelte:192` | Docling chosen without a URL | Enter the URL | same |
| `Invalid JSON format in Additional Config` | Error | `src/lib/components/admin/Settings/Documents.svelte:203` | Datalab Marker additional config is not JSON | Fix the JSON | same |
| `Document Intelligence endpoint required.` | Error | `src/lib/components/admin/Settings/Documents.svelte:212` | Document Intelligence chosen without an endpoint | Enter it | same |
| `Mistral OCR API Key required.` | Error | `src/lib/components/admin/Settings/Documents.svelte:219` | Mistral OCR chosen without a key | Enter it | same |
| `PaddleOCR-vl API URL required.` | Error | `src/lib/components/admin/Settings/Documents.svelte:222-227` | PaddleOCR-vl chosen without a URL | Enter it | same |
| `MinerU API Key required for Cloud API mode.` | Error | `src/lib/components/admin/Settings/Documents.svelte:230-236` | MinerU cloud mode without a key | Enter it | same |
| `Invalid JSON format in {NAME}` (`NAME` is `Docling Parameters`) | Error | `src/lib/components/admin/Settings/Documents.svelte:243-252` | Docling parameters are not JSON | Fix the JSON | same |
| `Invalid JSON format in MinerU Parameters` | Error | `src/lib/components/admin/Settings/Documents.svelte:256-260` | MinerU parameters are not JSON | Fix the JSON | same |
| `After changing the embedding model, reindex knowledge, knowledge search, and memory vectors for changes to take effect.` | Notice | `src/lib/components/admin/Settings/Documents.svelte:1169` | Embedding section | Run **Reindex** after saving | same |
| `Slim requires external services for embeddings, vector storage, and document extraction. Basic text files can be read locally.` | Notice | `src/lib/components/admin/Settings/Documents.svelte:427-433` | The server runs the slim image | — | same |
| `Transformers tokenization is unavailable in slim. Use character or token splitting.` | Error (console only) | `backend/open_webui/routers/retrieval.py:984-987` | Choosing that splitter on the slim image | Pick another splitter | same |
| `DDGS is unavailable in slim. Configure another web search provider in Admin Settings > Web Search.` | Error (console only) | `backend/open_webui/routers/retrieval.py:967-975` | Choosing DuckDuckGo on the slim image | Pick another provider | `web-search-and-web-loading.md` |
| `Playwright is unavailable in slim. Use basic HTTP fetching or an external web loader.` | Error (console only) | `backend/open_webui/routers/retrieval.py:976-983` | Choosing Playwright on the slim image | Pick another loader | same |
| `No valves to update` | Error | `src/lib/components/admin/Settings/Pipelines.svelte:52-54`, `:88-89` | **Save** with no pipeline or no valves | — | `functions-pipes-filters-actions-and-pipelines.md` |
| `Valves updated successfully` | Success | `src/lib/components/admin/Settings/Pipelines.svelte:76` | Valves saved on the pipelines server | — | — |
| `Pipeline downloaded successfully` | Success | `src/lib/components/admin/Settings/Pipelines.svelte:150`, `:182` | A pipeline was installed from a URL or uploaded | — | — |
| `Something went wrong :/` | Error | `src/lib/components/admin/Settings/Pipelines.svelte:173-177` | Pipeline upload failed | Retry; escalate | same |
| `No file selected` | Error | `src/lib/components/admin/Settings/Pipelines.svelte:194` | Upload pressed with no file | Choose a `.py` file | — |
| `Pipeline deleted successfully` | Success | `src/lib/components/admin/Settings/Pipelines.svelte:225` | Pipeline deleted | — | — |

### 10.4 Server Messages From `/api/v1/configs` (Integrations Endpoints)

These details are returned by the endpoints in scope and shown by the Integrations dialogs.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Failed to register OAuth client: {e}` | Error (HTTP 400) | `backend/open_webui/routers/configs.py:204-209` | Registering a single sign-on client for a tool server failed | Check the server address | `workspace-tools-tool-servers-mcp-and-terminals.md` |
| `Terminal server URL is required` | Error (400) | `backend/open_webui/routers/configs.py:365-367`, `:435-437`, `:472-474`, `:511-513` | Terminal server action without a URL | Enter the URL | same |
| `Failed to connect to the terminal server` | Error (400) | `backend/open_webui/routers/configs.py:401` | Neither the orchestrator nor the plain terminal check answered | Check URL and key | same |
| `Failed to access policy on terminal server` | Error (400) | `backend/open_webui/routers/configs.py:462-464` | Orchestrator policy call failed | — | same |
| `Failed to access lifecycle on terminal server` | Error (400) | `backend/open_webui/routers/configs.py:499-501` | Orchestrator lifecycle call failed | — | same |
| `Failed to refresh terminals` | Error (400) | `backend/open_webui/routers/configs.py:546-548` | Orchestrator refresh failed | — | same |
| `{detail}` | Error | `backend/open_webui/routers/configs.py:458-459`, `:495-496`, `:542-543` | The orchestrator refused the call; its own error text and status are passed on | — | same |
| `Failed to parse OAuth 2.1 discovery document from {discovery_url}` | Error (400) | `backend/open_webui/routers/configs.py:583-588` | MCP server's discovery document unreadable | — | same |
| `Failed to fetch OAuth 2.1 discovery document from {discovery_urls}` | Error (400) | `backend/open_webui/routers/configs.py:590-593` | No discovery document found | — | same |
| `Failed to create MCP client` | Error (400) | `backend/open_webui/routers/configs.py:632-637` | MCP connection test failed | Check URL and auth | same |
| `Failed to connect to the tool server` | Error (400) | `backend/open_webui/routers/configs.py:675-680` | OpenAPI tool server test failed | Check URL and auth | same |

### 10.5 Log Lines That Explain Symptoms

Log lines, not user messages; they appear in the server's standard output.

| Log line | Level | Source | Meaning |
|---|---|---|---|
| `Seeded {new_count} new config defaults` | Info | `backend/open_webui/models/config.py:264-266` | Start-up inserted keys that had no row (a new release added settings, or the table was reset) |
| `Renamed {moved_count} config keys from {old_prefix}.* to {new_prefix}.*; deleted {deleted_count} old duplicates` | Info | `backend/open_webui/models/config.py:294-300` | Old `rag.web.*` keys were moved to `web.*` at start-up |
| `Repaired flattened dict config rows for {repaired_keys}` | Info | `backend/open_webui/models/config.py:379-380` | Legacy flattened rows were folded back into one key |
| `Error loading DEFAULT_INTERFACE_SETTINGS: {e}` | Error | `backend/open_webui/config.py:1712-1716` | The environment variable is not valid JSON; `{}` is used |
| `Error loading WEBUI_BANNERS: {e}` | Error | `backend/open_webui/config.py:2160-2165` | The environment variable is not a valid banner list; no banners are seeded |
| `Version update check failed: {e}` | Warning | `backend/open_webui/main.py:2611-2613` | The upstream release check failed; General shows `Could not check for updates` |
| `Event sink failed for {event_payload.event}` | Error | `backend/open_webui/events.py:1198-1202` | Delivering a configuration event to a sink failed |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it never changes settings, roles or data. Resolutions are guidance for the
admin or an escalation to the platform maintainer. Never ask for, accept or forward a settings
export or database file (sections 5.8 and 5.10).

### 11.1 "I changed a setting and nothing happened"

**Symptom.** An admin saved a change, but users (or the admin) see no difference.

**Likely causes, in order.**
1. The other people's browsers still hold the configuration they loaded at start-up; switches,
   banners and wording change only after a reload or a new sign-in (section 7.6).
2. The save did not actually happen: Interface shows its success toast before the save finishes,
   and Audio, Documents, Web Search and Code Execution show nothing when the save fails
   (section 5.2).
3. The change needs an extra step: a new embedding model needs **Reindex Knowledge and Memory
   Vectors**; embedding, reranking and local Whisper changes reach other server processes only
   after a restart; imported values need the panels re-saved (sections 5.9, 7.5.9, 7.6).
4. A user's own saved preference overrides the admin's Default Interface Settings (section 5.4).
5. The setting is environment-only or process-only (OAuth while not persisted), so the panel cannot
   change it durably (sections 4.1, 7.7).
6. The feature is also controlled by user or group permissions, which are separate from the
   General switches (`users-groups-roles-and-permissions.md`).

**Diagnostic steps.**
1. Ask the admin to close the Settings window, reopen the same tab and confirm the saved value is
   shown (each panel reloads from the server when opened).
2. Ask an affected user to reload the page and try again.
3. Note which panel and setting, the time of the save, and whether more than one server process or
   replica is in use (**TO BE CONFIRMED** for production).

**Resolution.** If the value is saved and a reload fixes it, explain the reload rule. If the value
did not save, see 11.3. If it needs a reindex or restart, the admin or maintainer must do it.

**Escalation.** Panel name, setting label, expected and seen values, time of the save, whether a
reload helped, the user's role.

### 11.2 "My setting reverted after a restart"

**Symptom.** A value saved in a panel is back to an older or default value after the server
restarted or was redeployed.

**Likely causes, in order.**
1. The setting is an OAuth / OIDC value while `ENABLE_OAUTH_PERSISTENT_CONFIG` is off: it was only
   ever held in memory (section 4.1).
2. `RESET_CONFIG_ON_START` is on, so every stored setting is wiped at start-up (section 7.7).
3. `ENABLE_PERSISTENT_CONFIG` is off, so no panel save is stored (section 7.7).
4. Someone imported an older settings file after the change (section 5.9).
5. The server started with a different database (for example a recreated container without the
   data volume); then chats and users would also be missing, which is an incident, not a setting
   question (`knowledgebase/tools/ground-truth.md`, Data Stores).

**Diagnostic steps.**
1. Ask whether only this setting reverted or many (only OAuth values points to cause 1).
2. Ask whether chats, users or uploads also disappeared (cause 5).
3. Ask the maintainer whether the start-up log shows a large `Seeded {new_count} new config
   defaults` line after the restart, which happens when the table was emptied (section 10.5).

**Resolution.** Explain that environment variables do not override stored settings after the first
boot, and that OAuth values come from the environment by default. The fix is a maintainer change to
the environment or a re-save after the cause is removed.

**Escalation.** Setting, old and new values, restart time, whether other data vanished. If data
other than settings vanished, treat it as a possible incident and refer it as one
(security.utoronto.ca, privacy.utoronto.ca).

### 11.3 "The Save button does nothing"

**Symptom.** The admin presses **Save** and sees no toast, or sees a success toast but the value is
not kept.

**Likely causes, in order.**
1. The panel does not show save errors: Audio, Web Search, Code Execution and the final step of
   Documents fail silently (section 5.2).
2. A validation toast was shown and missed (missing URL or key, invalid JSON) (section 10.3).
3. On Interface, the success toast appears before the save finishes, and also when it fails
   (`src/lib/components/admin/Settings/Interface.svelte:164-169`).
4. On General, a value was silently not saved by the server: a default role other than `pending`,
   `user` or `admin`, a channel mode other than `thread` or `channel`, or a token lifetime such as
   `4 weeks` that does not match the duration pattern (`-1`, `0`, or a number followed by `ms`,
   `s`, `m`, `h`, `d` or `w`) (`backend/open_webui/routers/auths.py:1283-1293`).
5. The admin's session ended; the save is refused with the permission message (section 10.2).
6. On General the **Save** button stays disabled while an earlier save is still running
   (`src/lib/components/admin/Settings/General.svelte:81-82`, `:529`).

**Diagnostic steps.**
1. Close and reopen the tab and compare the values.
2. Ask the admin to reload the page and sign in again if needed, then retry once.
3. If the admin is comfortable doing so, ask for the text of any red error in the browser's
   developer console at the time of the save (it contains no secrets unless a key was typed into a
   field; ask them to blank any key before sharing).

**Resolution.** Correct the value (for example `4w` instead of `4 weeks`) or fill the missing field,
then save again. If the save still fails, escalate.

**Escalation.** Panel, setting, time, the console error text, the admin's role, whether the server
uses the slim image (**TO BE CONFIRMED**).

### 11.4 "I can't download the database"

**Symptom.** Database › **Export** › **Database** is missing, shows an error, or seems to do
nothing.

**Likely causes, in order.**
1. The database is not SQLite (for example PostgreSQL): the toast reads
   `This feature is only available with SQLite databases.`
2. `ENABLE_ADMIN_EXPORT` is off: the **Export** section is hidden, or the server answers with the
   permission message (sections 7.3, 10.2).
3. The database is large: the browser receives the whole file before the save prompt appears and
   shows no progress meanwhile (`src/lib/apis/utils/index.ts:108-122`).
4. The account is not an admin.

**Diagnostic steps.** Note which of the three outcomes the admin sees (no section, a toast, no
response). Do not ask for the file.

**Resolution.** On PostgreSQL, or when exports are switched off, the panel cannot provide the file;
backups are an infrastructure task for the maintainer (**TO BE CONFIRMED**). Remind the admin that
the file holds every user's personal data and possibly health information and may only be handled
as U of T rules allow (**TO BE CONFIRMED** with the data steward or Privacy Office).

**Escalation.** What was seen, the time, the purpose of the download (so the maintainer can judge
whether a database copy is appropriate at all).

### 11.5 "Users still see the old wording"

**Symptom.** An admin added a UI translation, but some or all users still see the original text.

**Likely causes, in order.**
1. Those users have not reloaded the app since the save (section 5.5).
2. The override was saved for one language and those users use another language that has its own
   translation of the text (section 7.4).
3. The **Key** does not match: ordinary text needs the exact English source string, punctuation
   and capitals included; settings-screen labels need the dotted key name, not the visible words.
4. The text does not come from the translation system: for example the Discord, X and GitHub links
   on General, the product name (`WEBUI_NAME`), or error text sent by the server
   (`src/lib/components/admin/Settings/General.svelte:210-226`; `backend/open_webui/env.py:951`).
5. The save failed with a translation toast (section 10.1).

**Diagnostic steps.**
1. Ask which language the affected user's interface uses and whether they reloaded.
2. Ask the admin to open General › **UI Translations**, set the language selector to that language
   and check the row exists for it.
3. Compare the **Key** character by character with the text on screen.

**Resolution.** Reload; add the override for each language users actually use; correct the key.

**Escalation.** The screen and text, the language, the key used, a screenshot.

### 11.6 "I can't find the setting for sign-up, banners or prompt suggestions"

**Symptom.** An admin looks for a setting where older versions or upstream guides put it.

**Likely causes, in order.** In v0.11.4: sign-up, default role, default group, API keys, token
lifetime, admin details and the pending overlay are on **Authentication**; banners and UI
translations are on **General** › **UI**; prompt suggestions and default models are on **Models**
› **Model Defaults** and the model menus; task models and title, tag and follow-up generation are on
**Interface**; event webhooks are on **General** (section 2.2).

**Diagnostic steps.** Use the **Search** box in the Settings window (section 4.3).

**Resolution.** Point the admin to the right tab and address from section 2.2.

**Escalation.** Not normally needed.

### 11.7 "The admin settings link opens my personal settings"

**Symptom.** A bookmark such as `/admin/settings/database` opens the personal **General** tab.

**Likely causes, in order.**
1. The address segment is not a tab id: the Database tab is `db`, Web Search is `web`, Code
   Execution is `code-execution` (section 2.2).
2. The account is not an admin, so admin tabs are replaced with the personal **General** tab.

**Diagnostic steps.** Check the address used and the user's role.

**Resolution.** Give the correct address from section 2.2. Role changes are an admin decision.

**Escalation.** Only if an admin account cannot see the **Admin** list at all.

### 11.8 "The OAuth settings are greyed out"

**Symptom.** Authentication › **OAuth / OIDC** fields cannot be edited and show a yellow notice.

**Likely causes, in order.** `ENABLE_OAUTH_PERSISTENT_CONFIG` is off (the code default), so the
values come from the server's environment (section 10.3).

**Diagnostic steps.** Confirm the notice text matches section 10.3.

**Resolution.** Single sign-on changes are made by the maintainer in the environment, followed by a
restart. See `sso-oauth-oidc-and-scim.md`.

**Escalation.** The setting the admin wants changed and why.

### 11.9 "A change I made on Authentication was undone"

**Symptom.** Sign-up, default role or another Authentication value went back to its earlier state
without a restart.

**Likely causes, in order.**
1. General was saved from another browser tab or by another admin who had opened it earlier;
   General re-sends all Authentication values it loaded (section 5.3).
2. An older settings file was imported (section 5.9).
3. The value was invalid and silently not saved (section 11.3, cause 4).

**Diagnostic steps.** Ask who else administers the site and whether General or an import was used
around that time. The `config.imported` event, when event webhooks are set up, records imports
(section 9).

**Resolution.** Advise admins to work in one tab at a time and re-save the value.

**Escalation.** The value, when it changed, which admins were active.

### 11.10 "Users don't get the interface default I set"

**Symptom.** Default Interface Settings were saved, but some users still have the old behaviour.

**Likely causes, in order.**
1. Those users had already chosen their own value, which wins over the default (section 5.4).
2. They have not reloaded the app.
3. The default was changed but General's **Save** was not pressed afterwards (the editor only
   collects changes).

**Diagnostic steps.** Ask the user to open their personal **Interface** tab: a switch inheriting the
admin default shows the word **Default** next to it (section 4.1).

**Resolution.** The user can change their own value; the defaults do not override a user's own
saved choice. Users without the Interface settings permission cannot save new interface values, so
the defaults apply to every option they had not already saved (section 5.4, step 6); whether to use
that is an admin decision.

**Escalation.** Not normally needed.

### 11.11 "The banner keeps coming back" or "Users don't see the banner"

**Symptom.** A banner reappears after being closed, or some users never see it.

**Likely causes, in order.**
1. **Remember Dismissal** is off for that banner, so closing it lasts only until the next page load
   (section 5.6).
2. Users dismissed it earlier in that browser, so it stays hidden there.
3. Users have not reloaded since it was added.
4. Saving General from an older session put back an older banner list (section 5.6).

**Diagnostic steps.** Ask the admin to check the banner's **Remember Dismissal** switch and that it
is still in the list.

**Resolution.** Guidance only; the banner content and switches are an admin decision. Depth:
`notifications-webhooks-events-and-banners.md`.

**Escalation.** The banner text (not personal data), the time it was added, affected users' count.

### 11.12 "The import said it worked but things don't match"

**Symptom.** `Config imported successfully` appeared, but some behaviour did not change, or a
second import of the same file did nothing.

**Likely causes, in order.**
1. The import writes rows only; embedding, reranking, speech-to-text and tool-server state are not
   rebuilt (section 5.9).
2. The admin's open app still shows the old configuration until reload.
3. Keys the database is not authoritative for changed only in one server process.
4. Choosing the same file a second time may not start a new import, because the code clears the file
   reader rather than the file picker after an import
   (`src/lib/components/admin/Settings/Database.svelte:66-81`); reloading the page clears it. This
   is inferred from the code (section 14).
5. A file that is not valid JSON fails in the browser without any message
   (`src/lib/components/admin/Settings/Database.svelte:70-71`).

**Diagnostic steps.** Ask the admin to reload, reopen the affected panels and compare values.

**Resolution.** Re-save the affected panels or ask the maintainer for a restart.

**Escalation.** Which panels differ, the import time. Never the file itself.

### 11.13 "The response watermark doesn't show"

**Symptom.** A **Response Watermark** is set, but responses in the chat do not show it.

**Likely causes, in order.** The watermark is added only to text copied with a response's copy
button; it is not drawn in the chat (section 7.1.2). Users also need a reload after the change.

**Diagnostic steps.** Copy a response with the copy button and paste it elsewhere.

**Resolution.** Explain the behaviour.

**Escalation.** Not normally needed.

### 11.14 "Someone wants a copy of the settings or the database"

**Symptom.** A person asks support for the settings export, the database, all chats or the users
list, or sends one.

**Likely causes, in order.** Migration, audit or troubleshooting requests.

**Diagnostic steps.** None; do not open such a file.

**Resolution.** Decline to handle the file. The settings export holds provider keys and other
secrets; the database and chat exports hold personal and possibly health information. If a file
was shared in a ticket or chat, ask the sender to delete it and refer it as a possible privacy or
security incident (privacy.utoronto.ca, security.utoronto.ca); keys in a shared export must be
rotated by the maintainer.

**Escalation.** Who asked, for what purpose, where any file was sent; not the file.

### 11.15 "General says an update is available"

**Symptom.** General shows `(v{version.latest} available!)`.

**Likely causes, in order.** The check compares against **upstream** Open WebUI releases
(section 5.11); MedIT GPT is a fork with its own changes.

**Diagnostic steps.** None.

**Resolution.** Tell the admin the message is about upstream; whether and when MedIT GPT is
updated is decided by the maintainer (**TO BE CONFIRMED**).

**Escalation.** Optional: pass the version number to the maintainer.

### 11.16 "The Analytics tab or the Database Export section is missing"

**Symptom.** An admin cannot see **Analytics**, or Database shows only **Config**.

**Likely causes, in order.** `ENABLE_ADMIN_ANALYTICS` or `ENABLE_ADMIN_EXPORT` is off in the
environment (section 7.7). Both are on in code by default.

**Diagnostic steps.** Confirm the account is an admin and which part is missing.

**Resolution.** These are deployment choices; only the maintainer can change them.

**Escalation.** Which part is missing and why the admin needs it.

## 12. Local Customisations

Checked with `git diff main...uoft` (the fork's three commits) and `git diff` (uncommitted
changes) on 2026-10-10.

**The admin panels themselves match upstream v0.11.4.** There is no fork change in
`src/lib/components/admin/Settings/` (any file), `src/routes/(app)/admin/`,
`src/lib/components/chat/SettingsModal.svelte`, `src/lib/apis/configs/`,
`backend/open_webui/routers/configs.py`, `backend/open_webui/routers/utils.py`,
`backend/open_webui/routers/auths.py`, `backend/open_webui/routers/tasks.py`,
`backend/open_webui/routers/chats.py`, `backend/open_webui/models/config.py`,
`backend/open_webui/config.py`, `src/lib/utils/settings-search.ts`,
`src/lib/utils/settings-access.ts` or `src/lib/utils/translationDictionary.ts`.

Fork changes that show up in this area:

| Change | Where it appears in the admin panels | Evidence |
|---|---|---|
| Two new interface switches, **Inline Citations** (`showInlineCitations`, default on) and **Hide Processing Details** (`hideProcessingDetails`, default off), added to the shared `InterfaceSettings` component | They appear in General › **UI** › **Default Interface Settings**, so admins can preset them for every account (section 5.4) | `src/lib/components/common/InterfaceSettings.svelte:79-80`, `:357-358`, `:1335-1378` (commit `aeed1832c`) |
| The same two fields declared in the server's `InterfaceSettings` model | Needed because that model lists the interface fields the server strips for users without the Interface permission (section 5.4) | `backend/open_webui/models/users.py:67-70`, `:99-100`; `backend/open_webui/routers/users.py:490-497` |
| Dotted label and description keys for the two switches, filled in `en-US` only | Their English text in the defaults editor and the settings search | `src/lib/i18n/locales/en-US/translation.json:2923-2924`, `:2935-2936`; the fork added four lines to every locale file (`git diff --stat main...uoft`), and per `CLAUDE.md` (i18n) empty values fall back to English; other locale files were not read |
| Default product name `MedIT GPT` without the upstream suffix | The Admin Panel browser title reads `Admin Panel / MedIT GPT` unless `WEBUI_NAME` is set | `backend/open_webui/env.py:951`; `src/routes/(app)/admin/+layout.svelte:32-34` |

Uncommitted working-tree changes that touch this area:

| Change | Effect here | Evidence |
|---|---|---|
| `src/lib/i18n/index.ts`: detected browser languages are mapped to a bundled language code (for example a regional code to its main bundle), English is always added as a final fallback, and the language list is loaded with the code instead of on demand | Decides which language a user's interface uses, and therefore which **UI Translations** language applies to them (section 7.4) | `src/lib/i18n/index.ts:75-86`, `:88-119`, `:124` |
| `en-US` description of **Hide Processing Details** reworded | Shown under that switch in the defaults editor | `src/lib/i18n/locales/en-US/translation.json:2923` |

Upstream licence comments in this area ("Do not alter, remove, obscure, or replace…") are intact
in General's **Help** and **License** rows and the Admin Panel title
(`src/lib/components/admin/Settings/General.svelte:194-196`, `:230-232`, `:280-282`;
`src/routes/(app)/admin/+layout.svelte:29-31`).

## 13. Source File Index

Depth: **full** (read end to end), **part** (the parts cited, located by search), **skim** (role
established from imports, props and messages only; the deep document covers it).

### 13.1 In Scope

| File | Role | Depth |
|---|---|---|
| `src/routes/(app)/admin/settings/+page.svelte` | `/admin/settings` redirect to the Settings window | full |
| `src/routes/(app)/admin/settings/[tab]/+page.svelte` | `/admin/settings/<tab>` redirect | full |
| `src/lib/components/admin/Settings/AdminSettingField.svelte` | Shared label-above field | full |
| `src/lib/components/admin/Settings/AdminSettingRow.svelte` | Shared label-and-control row | full |
| `src/lib/components/admin/Settings/AdminSettingSection.svelte` | Shared section with heading | full |
| `src/lib/components/admin/Settings/AdminTabIcon.svelte` | Tab icons | full |
| `src/lib/components/admin/Settings/General.svelte` | General panel | full |
| `src/lib/components/admin/Settings/Interface.svelte` | Interface panel | full |
| `src/lib/components/admin/Settings/Interface/Banners.svelte` | Banner editor used by General | full |
| `src/lib/components/admin/Settings/I18nSettings.svelte` | UI Translations editor used by General | full |
| `src/lib/components/admin/Settings/Database.svelte` | Database panel | full |
| `src/lib/components/admin/Settings/Authentication.svelte` | Authentication panel | part (script full; markup by label and binding) |
| `src/lib/components/admin/Settings/Connections.svelte` | Connections panel | part (script full; markup by label and binding) |
| `src/lib/components/admin/Settings/Connections/ManageOllamaModal.svelte`, `OllamaConnection.svelte`, `OpenAIConnection.svelte` | Connection rows and the Ollama management dialog | skim |
| `src/lib/components/admin/Settings/Models.svelte` | Models panel | part (saves, menus, messages) |
| `src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte` | Model Defaults, prompt suggestions | part (script full) |
| `src/lib/components/admin/Settings/Models/ModelMenu.svelte` | Per-model menu (selected and pinned defaults) | part |
| `src/lib/components/admin/Settings/Models/AdminViewSelector.svelte`, `ManageModelsModal.svelte`, `Manage/ManageOllama.svelte`, `Manage/ManageProviderModels.svelte`, `Manage/ManageMultipleOllama.svelte`, `Manage/ManageMultipleProviderModels.svelte` | Model list filter and model download or delete dialogs | skim |
| `src/lib/components/admin/Settings/Subagents.svelte` | Sub-agents panel | part |
| `src/lib/components/admin/Settings/Audio.svelte` | Audio panel | part (save handler, labels) |
| `src/lib/components/admin/Settings/Images.svelte` | Images panel | part (save handler, labels) |
| `src/lib/components/admin/Settings/Evaluations.svelte` | Evaluations panel | part (script full) |
| `src/lib/components/admin/Settings/Evaluations/Model.svelte`, `ArenaModelModal.svelte` | Arena model row and dialog | skim |
| `src/lib/components/admin/Settings/Integrations.svelte` | Integrations panel | part (script full; markup by label) |
| `src/lib/components/admin/Settings/ExternalKnowledge.svelte` | External Knowledge Sources section | skim (imports, state) |
| `src/lib/components/admin/Settings/Documents.svelte` | Documents panel | part (validation and save, labels) |
| `src/lib/components/admin/Settings/WebSearch.svelte` | Web Search panel | part (save handler, labels) |
| `src/lib/components/admin/Settings/CodeExecution.svelte` | Code Execution panel | part (script full, labels) |
| `src/lib/components/admin/Settings/Pipelines.svelte` | Pipelines panel | part (handlers, labels) |
| `src/lib/components/admin/Settings/Events.svelte` | Event webhooks section used by General | part (imports, messages, headings) |
| `src/lib/apis/configs/index.ts` | Client for `/api/v1/configs` | part (import, export, models, sub-agents, suggestions, banners, connections; error handling) |
| `backend/open_webui/routers/configs.py` | Config endpoints | full |
| `backend/open_webui/routers/utils.py` | Database download endpoint | full |
| `src/lib/utils/settings-search.ts` | Settings search index | full |
| `src/lib/utils/settings-access.ts` | Search permission rules | full |

### 13.2 Read for Context

| File | Why | Depth |
|---|---|---|
| `src/lib/components/chat/SettingsModal.svelte` | The Settings window: tabs, groups, search, save toasts | full |
| `src/routes/(app)/+layout.svelte` | `?settings=` handling, banners and settings loading | part (`:60-80`, `:150-195`, `:290-310`, `:425`) |
| `src/routes/(app)/admin/+layout.svelte`, `src/routes/(app)/admin/+page.svelte` | Admin Panel guard, title, Settings link | full |
| `src/routes/+layout.svelte` | Public configuration and translation loading at start-up | part (`:1236-1300`) |
| `src/lib/components/layout/Sidebar/UserMenu.svelte` | Admin Panel and Settings menu items | part |
| `src/lib/components/common/InterfaceSettings.svelte` | Defaults editor content, fork switches | part |
| `src/lib/components/common/Switch.svelte` | The **Default** marker | part |
| `src/lib/components/chat/Navbar.svelte` | Banner display and dismissal | part |
| `src/lib/components/chat/Messages/ResponseMessage.svelte` | Watermark on copy | part (`:232-250`) |
| `src/lib/utils/translationDictionary.ts` | UI Translations validation | full |
| `src/lib/i18n/index.ts`, `src/lib/i18n/settings-translations.ts` | How overrides combine; working-tree change | full |
| `src/lib/apis/auths/index.ts`, `src/lib/apis/utils/index.ts`, `src/lib/apis/users/index.ts`, `src/lib/apis/chats/index.ts`, `src/lib/apis/retrieval/index.ts`, `src/lib/apis/audio/index.ts`, `src/lib/apis/index.ts`, `src/lib/apis/knowledge/index.ts`, `src/lib/apis/evaluations/index.ts` | Client calls and error handling | part |
| `backend/open_webui/routers/auths.py` | `/admin/config`, LDAP and OAuth config endpoints, `ADMIN_CONFIG_KEYS` | part (`:95-165`, `:1100-1560`) |
| `backend/open_webui/routers/tasks.py` | Task config endpoints and keys | part (`:30-200`) |
| `backend/open_webui/routers/chats.py` | Chat config endpoints; all-chats export | part |
| `backend/open_webui/routers/users.py` | Default interface merge; users list; interface field stripping | part |
| `backend/open_webui/routers/retrieval.py`, `audio.py`, `images.py`, `openai.py`, `ollama.py`, `evaluations.py` | Key maps and save side effects of other panels | part |
| `backend/open_webui/models/config.py` | `Config` storage, persistence rules, export, seeding | full |
| `backend/open_webui/config.py` | Defaults (`DEFAULT_CONFIG` and the environment variables behind it) | part |
| `backend/open_webui/env.py` | Environment-only flags | part |
| `backend/open_webui/main.py` | Start-up order, runtime config, `/api/config`, version check, webhook endpoints | part |
| `backend/open_webui/events.py` | Configuration events and delivery | part |
| `backend/open_webui/utils/tools.py` | Tool-server cache refresh | part (`:1170-1207`) |
| `backend/open_webui/constants.py` | Error texts | part |
| `backend/open_webui/models/users.py` | `InterfaceSettings`, `UserSettings` | part |
| `src/lib/i18n/locales/en-US/translation.json` | English text of dotted keys | part (searched) |

## 14. Open Questions

Everything here could not be established from the repository, or was inferred from code without
being tested. Nothing in this list contradicts `knowledgebase/tools/ground-truth.md`.

### 14.1 To Be Confirmed (Organisational or Live Data)

1. **Live values** of every setting on every panel in production. They are rows in the `config`
   table (or the environment) and were not read; every value in this document is a code default.
2. **Production address** to put in General › **WebUI URL**, and whether it is set.
3. **Which database production uses.** The Database download works only on SQLite.
4. **Environment flags in production**: `ENABLE_PERSISTENT_CONFIG`, `ENABLE_OAUTH_PERSISTENT_CONFIG`,
   `RESET_CONFIG_ON_START`, `ENABLE_ADMIN_EXPORT`, `ENABLE_ADMIN_ANALYTICS`,
   `ENABLE_VERSION_UPDATE_CHECK`, `OFFLINE_MODE`, `ENABLE_PLUGINS`, `USE_SLIM_DOCKER`, `WEBUI_NAME`.
5. **How many server processes or replicas** run in production. With more than one, process-only
   values and the embedding, reranking and Whisper objects can differ between processes after a
   save (section 7.6).
6. **Data handling rules** for settings exports, database downloads, all-chats exports and the users
   CSV: who may take them, where they may be stored, and approval needed (data steward or Privacy
   Office). The code only gates them by the admin role and `ENABLE_ADMIN_EXPORT`.
7. **How MedIT GPT is updated.** General's update check reports upstream Open WebUI releases only.
8. **Which LICENSE §4 exception** the deployment relies on (also open in the ground truth); it bears
   on the **License** row of General.
9. **Database backups** when the download is unavailable (PostgreSQL, or exports switched off):
   who takes them and how.
10. Whether production uses event webhooks that receive the configuration events of section 9.
11. Whether production sets `AUTOMATION_MAX_COUNT` or `AUTOMATION_MIN_INTERVAL`; these have no
    control on any panel and can only come from the environment at first boot or from an import.

### 14.2 Inferred From Code, Not Tested

1. **Same-file import.** After an import the code clears the file reader instead of the file
   picker (`src/lib/components/admin/Settings/Database.svelte:66-81`), so choosing the same file
   again probably does not start a second import until the page is reloaded. Browser behaviour
   not tested.
2. **`[object Object]` after a malformed import.** When the server rejects the body shape, the
   client turns a list of validation entries into text with a template literal
   (`src/lib/components/admin/Settings/Database.svelte:71-74`;
   `src/lib/apis/configs/index.ts:21-29`); the exact text shown was not tested.
3. **Validation text on General.** Server validation errors for UI Translations arrive as a list;
   General shows each entry's `msg` (`src/lib/components/admin/Settings/General.svelte:96-102`).
   Whether the validation library adds a prefix (such as "Value error, ") before the messages in
   section 10.1 was not tested.
4. **Database download and the SQLite journal.** The endpoint sends only the main database file
   (`backend/open_webui/routers/utils.py:86-90`), while the ground truth records SQLite in WAL mode.
   Whether the most recent changes can be missing from a download was not checked.
5. **Concurrent admins.** The overwrite between General and Authentication (section 5.3) and the
   stale banner list (section 5.6) follow from the code; how often they happen is unknown.
6. **Silent save failures.** Panels named in section 5.2 as "a failure shows no message" were read,
   not exercised; some browsers may surface unhandled errors differently.

### 14.3 Differences Between the Brief and the Code

1. The research brief expected banners, prompt suggestions and default interface settings on the
   **Interface** panel and sign-up, default role and JWT expiry on **General**. In v0.11.4 banners
   and interface defaults are on General › **UI**, prompt suggestions on **Models** › **Model
   Defaults**, and the sign-up and token settings on **Authentication**, although General saves the
   same keys (sections 2.2, 5.3).
2. The brief expected a **reset** action on the Database tab. There is none; the resets are in
   **Documents** › **Danger Zone** (section 7.3).
3. The brief mentioned a webhook URL on General. The single `webhook_url` setting is legacy: it is
   converted into an event webhook at start-up, and General now shows the **Events** › **Webhooks**
   list (section 7.1.3).
4. The **Response Watermark** description says it is appended to assistant responses; the code adds
   it only to text copied with the copy button (section 7.1.2).

### 14.4 Security-Sensitive (Referred, No Detail)

1. How secrets inside stored settings are held, exported and protected, and which settings
   endpoints accounts other than admins can read. Security-sensitive: refer to the platform
   maintainer and U of T Information Security (security.utoronto.ca).
2. Whether the server enforces each General feature switch for every route, or some switches only
   hide the feature in the interface. Not investigated here; the feature documents cover their own
   checks. Security-sensitive: refer to the platform maintainer and U of T Information Security
   (security.utoronto.ca).

### 14.5 Not Covered Here

1. Field-by-field defaults and messages of the panels with their own documents (section 7.5 gives
   the map; the deep documents give the detail).
2. The Analytics dashboard (`src/lib/components/admin/Analytics.svelte`), outside this folder;
   see `evaluations-feedback-and-analytics.md`.
3. Personal (non-admin) settings tabs; see `user-settings-and-personalisation.md`.
