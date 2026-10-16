# Error Messages: Front End, Admin, Workspace and Settings

## At a Glance

- A catalogue of every toast, confirmation dialog and visible error string shown by the admin
  panel (`src/lib/components/admin/`), the Workspace (`src/lib/components/workspace/`), the
  personal Settings window (`src/lib/components/chat/Settings/`) and the top-level modal
  components in `src/lib/components/*.svelte`.
- Many red pop-ups print the server's own text (`${error}` or `error.detail`); those are marked
  "server text" and point to the two backend error catalogues.
- Messages already explained in another reference document carry a short trigger and a
  "See <document>.md section 10" pointer rather than a second explanation.
- The catalogue is complete: section 10 has one subsection per component folder (10.1 to 10.18),
  followed by triage (11), fork differences (12), the file index (13) and the gaps (14).
  *Corrected 2026-10-10: this bullet replaced "Provisional summary; refined when the catalogue is
  complete." once sections 10.3 to 14 were appended.*
- Many green pop-ups prove nothing on their own: admin **Connections** and **Interface**, personal
  **Audio** and **Personalization**, batch imports and several model actions report success before
  or regardless of the result (4.3, 11.1, 11.6).
- Many failures show no message at all (admin **Audio**, **Web Search**, **Code Execution**, parts
  of **Documents**, on/off switches); a few texts can never appear, notably the function editor's
  `Name and description are required` (11.2, 14.1).
- The fork changes one file in scope, the welcome screen's product name (section 12).

## 1. Purpose and Who Uses It

This catalogue lets tier-1 support take a message that a MedIT GPT user or administrator reports
from an admin screen, a Workspace screen, the Settings window or one of the shared connection,
automation, import and onboarding dialogs, and find the browser code that showed it, what usually
causes it and what to check. It lists **front-end text**: words written into the Svelte components
in scope. Where a pop-up only prints what the server answered, the row says **server text** and
points to the two backend catalogues,
[`error-messages-backend-identity-admin-and-platform.md`](error-messages-backend-identity-admin-and-platform.md)
and
[`error-messages-backend-chat-content-and-features.md`](error-messages-backend-chat-content-and-features.md).

| Reader | What they use it for |
|---|---|
| Tier-1 support (read-only) | Matching a reported text to a row in section 10, then following the row's support check or the pattern in section 11 |
| Platform maintainer | The source line behind an escalation; pop-ups that report success without checking; texts that can never appear |
| Writers of the numbered support guides | The verbatim wording, and which area document owns each message |

Scope, as assigned in `_areas.md` row 31 (150 source files):

| Folder | Files | What it is |
|---|---|---|
| `src/lib/components/admin/` | 64 | Admin panel: **Users** and **Groups**, **Evaluations**, **Functions**, the admin tabs of the Settings window (`admin/Settings/`), **Analytics** and the user preview window |
| `src/lib/components/workspace/` | 50 | Workspace: **Models**, **Knowledge**, **Prompts**, **Skills**, **Tools**, and shared pieces (`common/`: access control, member picker, valves, manifest) |
| `src/lib/components/chat/Settings/` | 27 | The personal tabs of the Settings window, the advanced-parameters block, and the community stats-sync window |
| `src/lib/components/*.svelte` | 9 | Top-level dialogs: `AddConnectionModal`, `AddToolServerModal`, `AddTerminalServerModal`, `AutomationModal`, `ChangelogModal`, `ImportModal`, `NotificationToast`, `OnBoarding`, `AddFilesPlaceholder` |

Bulk count over the 150 files: **461 pop-up calls** (326 red `toast.error`, 126 green
`toast.success`, 5 blue `toast.info`, 4 yellow `toast.warning`), **35 confirmation dialogs**, and
no browser `alert()`, `confirm()` or `window.prompt()` call. 176 of the red pop-ups print only the
error value they were handed (section 4.1).

Out of scope, and where to look instead:

- The Settings window itself (`src/lib/components/chat/SettingsModal.svelte`), which shows most
  `Settings saved successfully!` pop-ups on behalf of the tabs listed here, and the shared
  Interface settings component (`src/lib/components/common/InterfaceSettings.svelte`): see
  [`error-messages-frontend-chat-and-navigation.md`](error-messages-frontend-chat-and-navigation.md)
  section 10.1 and 10.11. Section 4.4 here explains how the two fit together.
- The create and edit **route pages** (`src/routes/(app)/workspace/*/create`, `.../edit`,
  `src/routes/(app)/admin/functions/create`, `.../edit`), which show the "created" and "updated"
  pop-ups for models, tools, functions, prompts and skills: see
  [`error-messages-frontend-chat-and-navigation.md`](error-messages-frontend-chat-and-navigation.md)
  section 10.15.
- Status lines inside a chat reply: the planned in-chat catalogue (area 32).

## 2. Navigation and URLs

### 2.1 Where These Messages Appear

| Surface | What the user sees | Evidence |
|---|---|---|
| **Pop-up (toast)** | A small card in the top-right corner with a close button, coloured by type: red `toast.error`, yellow `toast.warning`, green `toast.success`, blue `toast.info`. Nearly every message in this catalogue is a pop-up. | `src/routes/+layout.svelte:1435-1452` |
| **Confirmation dialog** | A centred window with a title, a text and **Cancel** / **Confirm** buttons (some screens relabel **Confirm** as **Delete**). With no title the window reads `Confirm your action`; with no text, `This action cannot be undone. Do you wish to continue?`. The text is rendered as Markdown. Screens import the same dialog under other names (`DeleteConfirmDialog`, `ModelDeleteConfirmDialog`, `ResetVectorDBConfirmDialog` and others). | `src/lib/components/common/ConfirmDialog.svelte:18-22`, `:139-154` |
| **Inline text** | A fixed sentence inside a screen: an empty list (`No models found`), a warning box (`Warning: Enabling this will allow users to upload arbitrary code on the server.`), a red notice (`Pipelines Not Detected`) or a tooltip | for example `src/lib/components/admin/Settings/Pipelines.svelte:465` |
| **Code-execution warning** | A yellow box at the top of the confirmation dialog that appears before a function or tool is saved or imported, followed by an acknowledgement sentence | `src/lib/components/admin/Functions/FunctionEditor.svelte:524-546`; `src/lib/components/workspace/Tools/ToolkitEditor.svelte:380-404` |
| **Notification card** | The clickable card that appears when a reply finishes in another chat or a channel message arrives (`NotificationToast.svelte`, in scope here; the events that raise it are in area 30 and 25) | `src/lib/components/NotificationToast.svelte`; `src/routes/+layout.svelte:608`, `:770` |

### 2.2 Which Screen Uses Which Folder

| Address | Screen | Who can open it | Section 10 |
|---|---|---|---|
| `/admin/users/overview`, `/admin/users/groups` | **Admin Panel › Users** (user list, add or import users, edit user, user's chats) and **Groups** (create, edit, permissions, members) | Admins | 10.1 |
| `/admin/evaluations/leaderboard`, `/admin/evaluations/feedback` | **Admin Panel › Evaluations** (leaderboard, feedback list) | Admins | 10.2 |
| `/?settings=admin:analytics` (opened from `/admin/analytics`) | **Analytics** tab of the Settings window | Admins, when analytics is switched on | 10.2 |
| `/admin/functions`, `/admin/functions/create`, `/admin/functions/edit?id={id}` | **Admin Panel › Functions** and the function editor | Admins, when plugins are switched on | 10.3 |
| `/?settings=admin:<tab>` (opened from `/admin/settings/<tab>`) | Admin tabs of the Settings window: General (with Events and UI translations), Authentication, Connections, Models, Subagents, Interface, Audio, Images, Evaluations, Integrations, Documents, Web Search (`web`), Code Execution (`code-execution`), Pipelines, Database (`db`) | Admins | 10.4 to 10.7 |
| `/workspace/models`, `/workspace/models/create`, `/workspace/models/edit?id={id}` | **Workspace › Models** and the model editor | Admins; users with the Models workspace permission | 10.8 |
| `/workspace/knowledge`, `/workspace/knowledge/create`, `/workspace/knowledge/{id}` | **Workspace › Knowledge** and one knowledge base | Admins; users with the Knowledge workspace permission | 10.9 |
| `/workspace/prompts`, `/workspace/prompts/create`, `/workspace/prompts/{id}`, `/workspace/skills`, `/workspace/skills/create`, `/workspace/skills/edit?id={id}` | **Workspace › Prompts** and **Skills** | Admins; users with the Prompts or Skills workspace permission | 10.10 |
| `/workspace/tools`, `/workspace/tools/create`, `/workspace/tools/edit?id={id}` | **Workspace › Tools** and the tool editor | Admins; users with the Tools workspace permission, when plugins are switched on | 10.11 |
| Any Workspace screen | Sharing (access control), member picker, valves, manifest windows | As the screen | 10.12 |
| `/?settings=<tab>` | Personal tabs of the Settings window: General, Interface, Notifications, Shortcuts, Connections, Integrations (`tools`), Personalization, Audio, Data Controls, Usage, Archived Chats, Account, About | Every signed-in user, subject to section 3 | 10.13, 10.14 |
| Admin **Connections** and personal **Connections** tabs | Add or edit a model connection (`AddConnectionModal`) | Admins; users when direct connections are on | 10.15 |
| Admin **Integrations** and personal **Integrations** tabs | Add or edit a tool server or terminal server (`AddToolServerModal`, `AddTerminalServerModal`) | Admins; users with the direct tool servers permission | 10.16 |
| `/automations`, `/automations/{id}`; Functions and Tools import; start-up; sign-in page; drag and drop | `AutomationModal`, `ImportModal`, `ChangelogModal`, `NotificationToast`, `OnBoarding`, `AddFilesPlaceholder` | As the screen | 10.17 |

Admin settings, analytics and personal settings all open inside the same Settings window
(`../tools/ground-truth.md`, Navigation Facts; `src/routes/(app)/admin/settings/[tab]/+page.svelte:6-10`).
The tab ids `db`, `web` and `code-execution` differ from their titles; see
[`admin-settings-panels.md`](admin-settings-panels.md) section 2. The tab list is built in
`src/lib/components/chat/SettingsModal.svelte:379-411`.

## 3. Roles and Permissions

The front end decides which of these messages a person can meet mostly by which screens, tabs and
buttons it shows. The server still makes the final decision; a refused request comes back as
server text (section 4.1), typically `You do not have permission to access this resource. Please
contact your administrator for assistance.` with HTTP 401 (`../tools/ground-truth.md`, Accounts
and Access).

| Who | What they can meet | Evidence |
|---|---|---|
| `pending` account | None of these screens: the account pending overlay replaces the app | `src/routes/(app)/+layout.svelte:445-446` |
| `user` | The personal Settings tabs (10.13, 10.14), the Workspace sections their permissions open (10.8 to 10.12), the personal connection and integration dialogs when switched on (10.15, 10.16), automations (10.17) | sections 2.2 and below |
| `admin` | Everything: the admin panel (10.1 to 10.3), the admin Settings tabs (10.4 to 10.7), every Workspace section, the changelog window | `src/routes/(app)/admin/+layout.svelte:16-17`; `src/lib/components/chat/SettingsModal.svelte:408-411` |

**Admin-only screens.** Every page under `/admin` sends a non-admin back to `/` without a message,
and `/admin/functions` sends an admin back to `/admin` when plugins are switched off
(`src/routes/(app)/admin/+layout.svelte:16-23`). `src/lib/components/admin/Users.svelte:61-63`
repeats the role check. The admin tabs are added to the Settings window only for admins, and the
Analytics tab only when `enable_admin_analytics` is on
(`src/lib/components/chat/SettingsModal.svelte:408-411`).

**Workspace sections.** For a non-admin, `/workspace/models`, `/knowledge`, `/prompts`, `/skills`
and `/tools` each require the matching `workspace` permission, and Tools also needs plugins on;
without it the page returns to `/` silently (`src/routes/(app)/workspace/+layout.svelte:81-100`).
Inside a section, items shared read-only show `Read Only` and their editors refuse to save with
texts such as `You do not have permission to edit this prompt.` (10.10).

**Personal Settings tabs.** All signed-in users see the Settings window, but four tabs are
conditional (`src/lib/components/chat/SettingsModal.svelte:379-404`):

| Tab | Shown when |
|---|---|
| Connections | Direct connections are switched on (`enable_direct_connections`) |
| Integrations (`tools`) | Direct integrations are on and the person is an admin or has the direct tool servers permission |
| Interface | Admin, or the `settings.interface` permission (default on) |
| Personalization | Memories are on and the person is an admin or has the memories permission |

Within tabs, API keys, notification targets, chat import, export and delete, temporary chats, the
system prompt and the advanced parameters are each gated by a permission or feature switch
(`src/lib/utils/settings-access.ts:3-21`); a hidden control cannot produce its messages.

**Permission sentences the front end shows itself.** A few screens explain a missing permission
without asking the server, for example `You do not have permission to upload files to this
knowledge base.` (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1068`) and
`You do not have permission to make this public` (`src/lib/components/workspace/common/AccessControl.svelte:520`).
The permission keys behind them are explained in
[`users-groups-roles-and-permissions.md`](users-groups-roles-and-permissions.md).

## 4. Key Concepts and Terminology

### 4.1 Server Text in a Pop-Up

Most red pop-ups in scope print whatever the API client handed back and add no words of their own.
Of the 326 `toast.error` calls in the 150 files, 176 pass only the error value (written
`${error}`, `${e}`, `${err}`, `err`, `error?.detail ?? error`, `getErrorMessage(error)` or
`String(error)`), and two more put `Row {n}: ` in front of it (bulk count). The API clients in
`src/lib/apis/` decide what that value is:

| How the client hands the error on | Example | What the pop-up shows |
|---|---|---|
| `error = err.detail` (most clients: configs, users, groups, knowledge, functions, tools, retrieval, auths, memories, evaluations) | `src/lib/apis/configs/index.ts:23`, `:27-28` | The server's `detail` text. A `detail` that is a list (a request the server could not validate) or an object prints as `[object Object]`; a failure with no `detail` (network failure, a proxy's HTML page) throws nothing, so the screen usually shows nothing |
| `error = err` (the whole answer: the models client, `getModels`, pipelines, webhooks, tool-server data, version and changelog look-ups) | `src/lib/apis/models/index.ts:53-62`; `src/lib/apis/index.ts:23-35` | When the server answered with JSON, `${error}` prints `[object Object]`; screens that write `${error?.detail ?? error}` print the `detail` instead |

So the wording of most red pop-ups lives in the backend: look it up in section 10 of
[`error-messages-backend-identity-admin-and-platform.md`](error-messages-backend-identity-admin-and-platform.md)
(users, groups, configuration, functions, evaluations, pipelines) or
[`error-messages-backend-chat-content-and-features.md`](error-messages-backend-chat-content-and-features.md)
(models, knowledge, files, prompts, skills, tools, memories, audio, images, automations,
terminals). In section 10 of this document such rows read **server text**.

### 4.2 `[object Object]`, Browser Error Texts and Silent Failures

These are not messages anyone wrote:

- **`[object Object]`**: the screen printed an object, typically the whole server answer from a
  client that uses `error = err` (4.1), or a `detail` that is a validation list. Rows where this is
  likely are marked in section 10.
- **A browser error text** (for example a `TypeError` naming a failed fetch): the request never
  reached the server, or the answer was not JSON. The wording comes from the browser, not from
  the code.
- **No message at all**: a client using `error = err.detail` whose failure carries no `detail`
  throws nothing; and a few screens call the server without any error handling, so a failure
  shows nothing and the screen simply does not change. Rows marked **(silent on failure)** in
  section 10 name them.
- **A blank red pop-up**: the value printed was empty.

The server log for the same minute names the real error (section 11.4).

### 4.3 Success Shown Before or Without the Result

Some green pop-ups do not prove that the action worked. Section 10 marks them **(unchecked
success)**: the code shows the pop-up without waiting for the server's answer, after an answer it
does not inspect, or once per batch even when items in the batch failed. Section 11.1 gives the
check.

### 4.4 The Settings Window Shows Most "Saved" Pop-Ups

The panels in `admin/Settings/` and `chat/Settings/` are shown inside the Settings window
(`src/lib/components/chat/SettingsModal.svelte`, outside this scope). For most tabs the panel
saves, then tells the window, and **the window** shows `Settings saved successfully!`
(`src/lib/components/chat/SettingsModal.svelte:460-464`, `:791-906`). Whether that pop-up proves
anything therefore depends on the panel: if the panel tells the window only after a successful
save, it does; if it tells the window regardless, the pop-up can follow a red error pop-up. Each
panel's behaviour is given in section 10 (rows for `Settings saved successfully!` cite the panel
line that triggers it). A few panels show their own pop-up instead (for example
`OpenAI API settings updated` in admin **Connections**, `Valves updated successfully` in
**Pipelines**).

### 4.5 Translation Keys, Dotted Keys and Untranslated Text

- **Plain keys.** `$i18n.t('Group created successfully')` shows `Group created successfully`.
  Placeholders are written `{{name}}` in the code; this catalogue keeps them as written.
- **Dotted keys.** The Settings panels use 902 dotted keys (`settings.admin.…`,
  `settings.personal.…`), almost all for labels and descriptions; each has English text in
  `src/lib/i18n/locales/en-US/translation.json` (checked: none is missing or empty). Only four
  dotted keys appear in a pop-up or dialog: `settings.admin.images.serverConnectionVerified.label`
  (`Server connection verified`, `src/lib/i18n/locales/en-US/translation.json:2469`),
  `settings.personal.dataControls.archiveAllChats.label` (`Archive All Chats`, `:2803`),
  `settings.personal.dataControls.deleteAllChats.label` (`Delete All Chats`, `:2805`) and
  `settings.personal.archivedChats.unarchiveAll.label` (`Unarchive All`, `:2770`).
- **Untranslated text.** A few pop-ups are written in English in the code and stay English in every
  language, for example `Checking for model updates...`
  (`src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:80`). Section 10 marks them
  **untranslated**.
- **Admin overrides.** **Admin Settings › General › UI Translations** lets an admin replace the
  wording of any key, per language (`src/lib/components/admin/Settings/General.svelte:421-422`;
  `src/lib/components/admin/Settings/I18nSettings.svelte:56-72`). The overrides are saved in the
  `ui.i18n` setting and apply to every browser (see
  [`error-messages-frontend-chat-and-navigation.md`](error-messages-frontend-chat-and-navigation.md)
  section 4.4). **If a reported text matches no row here, an override may have changed it**; the
  live overrides are data and are TO BE CONFIRMED.

### 4.6 Terms Used in Section 10

| Term | Meaning |
|---|---|
| Server text | The pop-up prints what the server or browser sent (4.1) |
| Unchecked success | A green pop-up that does not prove the action worked (4.3) |
| Silent on failure | A failure that shows no message (4.2) |
| Untranslated | Written in English in the code (4.5) |
| Inline | Text inside the screen, not a pop-up (including tooltips and empty-list texts) |
| Dialog | A confirmation window (title or text) |
| Thrown | Text a screen's own code raises and then shows in the pop-up named in the row |

## 5. Workflows (Step by Step)

### 5.1 Look Up a Message a User Reports

1. Get the exact wording (a screenshot is best), the screen or address (for the Settings window,
   the tab name), the time, the person's role and their interface language (**Settings ›
   General**). A pop-up disappears after a few seconds; ask the person to repeat the action and
   capture it.
2. Find the screen in section 2.2 and go to the matching part of section 10. Search for a
   distinctive phrase of four or five words; placeholders are written `{{name}}`, so search for
   the fixed words around them.
3. **Found here.** Read the row. The **Support check** column either gives the check or names the
   area document whose section 10 explains the message in depth.
4. **Not found here.** The pop-up is probably server text (4.1). Search section 10 of the two
   backend catalogues. Chat, sidebar, notes, channels and route pages are in
   [`error-messages-frontend-chat-and-navigation.md`](error-messages-frontend-chat-and-navigation.md).
5. **Found nowhere.** Check whether the person's language is not English (ask them to switch to
   English and repeat), whether an admin translation override changed the wording (4.5), or
   whether the text came from a function, tool, valve or model rather than from the application.
6. Follow the matching pattern in section 11 if one applies.

### 5.2 Tell Front-End Text From Server Text

| Clue | Usually means |
|---|---|
| The text matches a row in section 10 here | Written by the browser code; the trigger is in the row |
| The text mentions an HTTP status, a database, a provider, a file path, or ends with `:/` | Server text |
| `[object Object]`, a `TypeError`, or no message at all | Not a message; see 4.2 and section 11.4 |
| The text is in English while the rest of the screen is translated | Untranslated (4.5) or server text |

### 5.3 Check Whether a Save Really Worked (Read-Only)

1. Ask the person to close the Settings window or editor, reload the page and reopen it.
2. If the value is back to the old one, the save did not happen or was undone (section 11.1); a
   green pop-up seen at the time does not prove otherwise (4.3, 4.4).
3. For admin settings, also ask whether the value was set by an environment variable or an
   **OAuth** field that is not persisted (see
   [`admin-settings-panels.md`](admin-settings-panels.md) section 11.2 and 11.9).

### 5.4 Prepare an Escalation

Send: the exact text; the screen or Settings tab; date, time and time zone; browser and version;
the person's role; the steps to repeat; whether other people see it. For a Workspace item, give its
name or the id in the address (`/workspace/models/edit?id={id}`), never its content. For server
text, ask the platform maintainer for the server log lines at that minute (logs go to standard
output only; retention is TO BE CONFIRMED, see `../tools/ground-truth.md`).

### 5.5 Re-Harvest After a Release (Maintainer)

The catalogue was built by a bulk search of the 150 files for `toast.error(`, `toast.warning(`,
`toast.info(`, `toast.success(`, `toast(`, `ConfirmDialog` and its import aliases, `throw`, and
every `$i18n.t('…')` text that reads as an error, warning or notice, followed by reading each call
site. Repeat the same searches after a release and compare.

## 6. Data Model

Front-end messages are not stored: a pop-up exists only in the open browser tab. What the
messages in this catalogue act on is stored as follows, documented in the area documents:

| Trace | Where it is kept | Evidence or owner document |
|---|---|---|
| Admin settings saved from the admin tabs | Rows of the `config` table, one per dotted key (data; see `../tools/ground-truth.md`, Settings) | [`admin-settings-panels.md`](admin-settings-panels.md) section 6 |
| Personal settings | The `settings` of the person's account (and some only in the browser) | [`user-settings-and-personalisation.md`](user-settings-and-personalisation.md) section 6 |
| A failed upload into a knowledge base | The `error` text on the uploaded file item, shown as a yellow pop-up | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:377-378` |
| Admin translation overrides | Setting `ui.i18n` (data) | 4.5 |

## 7. Settings and Configuration

| Setting | Effect on messages | Evidence |
|---|---|---|
| **UI Translations** (`ui.i18n`, admin) | Replaces the wording of any message key | 4.5 |
| Interface language (per person) | Which translation is shown; English is the fallback | [`error-messages-frontend-chat-and-navigation.md`](error-messages-frontend-chat-and-navigation.md) section 7 |
| Maximum upload size (`file.max_size` in the start-up configuration) | The limit quoted in `File size should not exceed {{maxSize}} MB.` in a knowledge base and in the model editor's knowledge block | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:428`; `src/lib/components/workspace/Models/Knowledge.svelte:129` |
| `ENABLE_OAUTH_PERSISTENT_CONFIG` (environment) | When off, the OAuth section of **Authentication** shows `These settings are read from environment variables and cannot be edited here while {{ENV_VAR}} is disabled.` with `ENABLE_OAUTH_PERSISTENT_CONFIG` | `src/lib/components/admin/Settings/Authentication.svelte:549-557` |
| Version update check (`enable_version_update_check` feature) | Whether **General** (admin) and **About** show the version check, and `Could not check for updates` when the look-up fails | `src/lib/components/admin/Settings/General.svelte:54-58`, `:142-145`; `src/lib/components/chat/Settings/About.svelte:27-31`, `:71-73` |
| Community sharing (`enable_community_sharing` feature) | Whether the Workspace and Functions screens offer sharing to the upstream community (`Redirecting you to Open WebUI Community`) | 10.3, 10.8, 10.10, 10.11 |
| Licence seats (`license_metadata.seats` in the start-up configuration) | `License Error` banner on **Admin Panel › Users** when the user count exceeds the seats | `src/lib/components/admin/Users/UserList.svelte:163-175` |
| Feature switches and permissions | Which tabs, screens and buttons exist, and so which messages can appear | section 3 |

Live values of every setting are data and are TO BE CONFIRMED for production.

## 8. Cron Jobs and Background Processes

None for this area. Every message here is shown at the moment of an action (a save, a test, an
upload, a delete) or when a screen loads. Two browser-side waits matter:

| Wait | Effect | Evidence |
|---|---|---|
| Ollama model downloads | **Admin Settings › Models › Manage** reads the download progress as it streams; the success or failure pop-up arrives when the stream ends, which can be many minutes later | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:199-290` |
| Knowledge base uploads and directory sync | Each file's pop-up arrives when its upload and processing finish; sync shows one summary at the end | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:740-770` |

## 9. Notifications and Emails

No email (see `../tools/ground-truth.md`). In scope:

- `src/lib/components/NotificationToast.svelte` draws the clickable card used for chat and channel
  notifications; its text is the chat title or channel message, not fixed wording (10.17).
- **Settings › Notifications** sends a test notification (`Test notification sent.`) and manages
  notification targets (10.14); the events and webhooks are documented in
  [`notifications-webhooks-events-and-banners.md`](notifications-webhooks-events-and-banners.md).
- **Admin Settings › General › Events** manages event webhooks (10.4).

## 10. Error, Warning and Notice Messages (Verbatim)

How to read the tables:

- **Severity.** `Error` red pop-up; `Warning` yellow pop-up; `Success` green pop-up; `Info` blue
  pop-up; `Dialog` a confirmation window (title or text); `Inline` text inside the screen
  (including tooltips and empty-list texts); `Thrown` text the screen's own code raises, then shows
  in the pop-up named in the row. **Untranslated** means the text is written in English in the code.
- **Server text.** A row whose message is `{error}` (or `{e}`, `{err}`) prints what the server or the
  browser sent (4.1); the trigger names the action, and the wording is in the backend catalogues.
  **May show `[object Object]`** marks rows whose client hands over the whole server answer (4.1, 4.2).
- **Source.** The first citation is the full path; further lines in the same file are written
  `:line`. One row per distinct message per file.
- **Placeholders.** `{{name}}` is the code's own i18next placeholder; `{name}` is a value the code
  joins in directly (for example `Row {idx + 1}: …`).
- **Already documented.** When an area document's section 10 explains the message, the trigger is
  kept short and the support check reads `See <document>.md section 10`. Rows without such a
  pointer were established from the code for this catalogue.
- **(unchecked success)** and **(silent on failure)** are explained in 4.3 and 4.2.
- Labels, buttons and empty-list texts are listed only when a person might report them as a problem.

### 10.1 `admin/Users.svelte`, `admin/Users/` and `admin/UserPreviewModal.svelte` (Users and Groups)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{error}` (server text) | Error | `src/lib/components/admin/Users/UserList.svelte:61`, `:101` | Deleting a user (`:61`) or loading the user list (`:101`) failed | Retry; reload the page | See `users-groups-roles-and-permissions.md` section 10; the wording is in `error-messages-backend-identity-admin-and-platform.md` section 10 |
| `Confirm your action`; `This action cannot be undone. Do you wish to continue?` | Dialog (default texts) | `src/lib/components/admin/Users/UserList.svelte:136-141`; texts `src/lib/components/common/ConfirmDialog.svelte:143`, `:153` | **Delete User** (offered only for non-admin accounts, `:448`). A successful delete shows no pop-up; the list simply reloads (`:59-72`) | Confirm only if intended; deletion is permanent | See `users-groups-roles-and-permissions.md` section 10 and 11.16 |
| `License Error`; `Exceeded the number of seats in your license. Please contact support to increase the number of seats.` | Inline (red banner) | `src/lib/components/admin/Users/UserList.svelte:163-176` | Licence data with a seat count is present and the user total exceeds it | Report to the platform maintainer | See `users-groups-roles-and-permissions.md` section 10 |
| `Running Open WebUI for a team?` and the three sentences under it | Inline (notice) | `src/lib/components/admin/Users/UserList.svelte:479-512` | No licence data and more than 50 users; upstream wording protected by the licence comments | None | See `users-groups-roles-and-permissions.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/admin/Users/UserList/AddUserModal.svelte:57` | **Add User** (form tab) was refused, for example an email already in use | Correct the form | See `users-groups-roles-and-permissions.md` section 10 |
| `Row {idx + 1}: invalid format.` (untranslated) | Error | `src/lib/components/admin/Users/UserList/AddUserModal.svelte:88` | **CSV Import**: a line (numbered as in the file, header = line 1) does not have exactly four comma-separated values or its role is not `admin`, `user` or `pending` (`:79-89`). A file ending in a line break also gives one such pop-up for the empty last line; a name containing a comma breaks its line | Fix that line; ignore a pop-up for the empty last line | See `users-groups-roles-and-permissions.md` section 10 and 11.5 |
| `Row {idx + 1}: {error}` (server text) | Error | `src/lib/components/admin/Users/UserList/AddUserModal.svelte:108` | The server refused that line's account (lines are sent ten at a time, `:94-111`) | Fix that line and import it again | See `users-groups-roles-and-permissions.md` section 10 |
| `Successfully imported {{userCount}} users.` | Success | `src/lib/components/admin/Users/UserList/AddUserModal.svelte:121-123` | End of a CSV import; counts only accounts created, and is green even when it reads 0 | Compare the count with the number of data lines | See `users-groups-roles-and-permissions.md` section 10 |
| `File not found.` | Error | `src/lib/components/admin/Users/UserList/AddUserModal.svelte:136` | **Save** on the CSV tab with no file chosen | Choose a file | See `users-groups-roles-and-permissions.md` section 10 |
| `Ensure your CSV file includes 4 columns in this order: Name, Email, Password, Role.` | Inline | `src/lib/components/admin/Users/UserList/AddUserModal.svelte:286` | CSV tab | Follow the format | See `users-groups-roles-and-permissions.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/admin/Users/UserList/EditUserModal.svelte:48`, `:62` | Saving the user (`:48`; success shows no pop-up, the window closes) or loading the user's groups (`:62`) failed | Retry | See `users-groups-roles-and-permissions.md` section 10 |
| `No chats found for this user.` | Inline | `src/lib/components/admin/Users/UserList/UserChatsModal.svelte:115` | The user's chats window has no chats to list. **(silent on failure)**: the list is loaded without error handling, so a failed request also leaves it empty with no pop-up (`:57-58`, `:94-96`) | Retry once | See `users-groups-roles-and-permissions.md` section 10; if a user is known to have chats, escalate |
| `{error}` (server text, red line) | Inline | `src/lib/components/admin/UserPreviewModal.svelte:24-29`, `:59-60` | Loading the user preview failed | Close and reopen | See `users-groups-roles-and-permissions.md` section 10 |
| `No models accessible`; `No knowledge bases accessible`; `No tools accessible` | Inline | `src/lib/components/admin/UserPreviewModal.svelte:84`, `:116`, `:148` | The previewed user can reach none of that type | None | See `users-groups-roles-and-permissions.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/admin/Users/Groups.svelte:73`, `:89` | Creating a group (`:73`) or saving **Default permissions** (`:89`) failed | Retry | See `users-groups-roles-and-permissions.md` section 10 |
| `Group created successfully` | Success | `src/lib/components/admin/Users/Groups.svelte:78` | The new group was saved | Open it to add members | See `users-groups-roles-and-permissions.md` section 10 |
| `Default permissions updated successfully` | Success | `src/lib/components/admin/Users/Groups.svelte:95` | **Default permissions** saved | None | See `users-groups-roles-and-permissions.md` section 10 |
| `No groups found`; `Use groups to organize your users and assign permissions.` | Inline | `src/lib/components/admin/Users/Groups.svelte:199`, `:201` | No group exists or none matches the search | None | See `users-groups-roles-and-permissions.md` section 10 |
| `Confirm your action`; `This action cannot be undone. Do you wish to continue?` | Dialog (default texts) | `src/lib/components/admin/Users/Groups/EditGroupModal.svelte:116-122` | **Delete** in a group's window | Confirm only if intended | See `users-groups-roles-and-permissions.md` section 10 |
| `Reset to Defaults`; `Are you sure you want to reset all permissions to their default values? You will still need to save to apply the changes.` | Dialog | `src/lib/components/admin/Users/Groups/EditGroupModal.svelte:124-133` | **Reset to Defaults** in a group or in Default permissions | Confirm, then **Save** | See `users-groups-roles-and-permissions.md` section 10 |
| `Permissions reset to defaults` | Success (not saved yet) | `src/lib/components/admin/Users/Groups/EditGroupModal.svelte:79` | The defaults were copied into the form only (`:63-80`); nothing is stored until **Save** | Press **Save** | See `users-groups-roles-and-permissions.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/admin/Users/Groups/EditGroupModal.svelte:82` | Loading the defaults for **Reset to Defaults** failed | Retry | Server text |
| `{error}` (server text) | Error | `src/lib/components/admin/Users/Groups/GroupItem.svelte:31`, `:43` | Saving (`:31`) or deleting (`:43`) a group failed. The group window closes after **Save** whatever the outcome (`src/lib/components/admin/Users/Groups/EditGroupModal.svelte:47-60`), so unsaved edits are lost | Reopen and redo the change | See `users-groups-roles-and-permissions.md` section 10 |
| `Group updated successfully`; `Group deleted successfully` | Success | `src/lib/components/admin/Users/Groups/GroupItem.svelte:36`, `:48` | The group was saved or deleted | None | See `users-groups-roles-and-permissions.md` section 10 |
| `This is a default user permission and will remain enabled.` | Inline (under a switch) | `src/lib/components/admin/Users/Groups/Permissions.svelte:78` and 56 other lines | A group switch is off but the default permissions turn it on, so members keep it | Change **Default permissions** instead | See `users-groups-roles-and-permissions.md` section 10 and 11.6 |
| `Warning: Enabling this will allow users to upload arbitrary code on the server.` | Inline (warning) | `src/lib/components/admin/Users/Groups/Permissions.svelte:145`, `:190` | Tools or Skills workspace access | Admin decision | See `users-groups-roles-and-permissions.md` section 10 |
| `Warning: Enabling this will allow users to run scheduled prompts automatically.` | Inline (warning) | `src/lib/components/admin/Users/Groups/Permissions.svelte:1118` | Automations feature permission | Admin decision | See `users-groups-roles-and-permissions.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/admin/Users/Groups/Users.svelte:128`, `:147`, `:152`, `:201`, `:241` | Loading the member list (`:128`), adding (`:147`, `:201` during import) or removing (`:152`) a member, or the import as a whole (`:241`) failed | Retry | See `users-groups-roles-and-permissions.md` section 10 |
| `Row {idx + 1}: User not found.` (`Row` untranslated) | Error | `src/lib/components/admin/Users/Groups/Users.svelte:181` | Group **Import CSV**: no account has that line's email | Create the account first or fix the email | See `users-groups-roles-and-permissions.md` section 10 |
| `Row {idx + 1}: {error}` (server text) | Error | `src/lib/components/admin/Users/Groups/Users.svelte:185` | The account look-up for that line failed | Retry | See `users-groups-roles-and-permissions.md` section 10 |
| `Row {idx + 1}: Invalid format.` (`Row` untranslated) | Error | `src/lib/components/admin/Users/Groups/Users.svelte:224` | A non-blank line without exactly two values (`Name,Email`) or without an email (`:65-84`); blank lines are skipped | Fix that line | See `users-groups-roles-and-permissions.md` section 10 |
| `Successfully imported {{userCount}} users.` | Success | `src/lib/components/admin/Users/Groups/Users.svelte:232-237` | The import raised the member count. When nobody new was added (for example everyone listed is already a member) **no pop-up at all** appears | Check the member count | See `users-groups-roles-and-permissions.md` section 10 |
| `No users were found.` | Inline | `src/lib/components/admin/Users/Groups/Users.svelte:508` | The member search matched no account | Check the spelling | See `users-groups-roles-and-permissions.md` section 10 |
| `{error}` (server text, red line) | Inline | `src/lib/components/admin/Users/Groups/GroupPreviewPanel.svelte:20-25`, `:36-37` | Loading the group preview failed | Reopen | See `users-groups-roles-and-permissions.md` section 10 |
| `No models accessible`; `No knowledge bases accessible`; `No tools accessible` | Inline | `src/lib/components/admin/Users/Groups/GroupPreviewPanel.svelte:46`, `:79`, `:112` | The group reaches none of that type | None | See `users-groups-roles-and-permissions.md` section 10 |

`src/lib/components/admin/Users.svelte` itself shows no message: it sends a non-admin to `/`
(`:61-63`) and colours the user count red when the licence seats are exceeded (`:40-41`,
`:99-104`). `src/lib/components/admin/Users/Groups/General.svelte` has labels only.

### 10.2 `admin/Evaluations.svelte`, `admin/Evaluations/`, `admin/Analytics.svelte` and `admin/Analytics/` (Evaluations and Analytics)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{error}` (server text) | Error | `src/lib/components/admin/Evaluations/Feedbacks.svelte:86` | Loading the **Feedback** list failed | Reload | See `evaluations-feedback-and-analytics.md` section 10 |
| `{err}` (server text, printed as handed over) | Error | `src/lib/components/admin/Evaluations/Feedbacks.svelte:117`, `:192` | Deleting one feedback item (`:117`; **Delete** in the row's menu acts at once, without a confirmation, `:498-502`) or **Export** to JSON or CSV (`:192`) failed. A failure with no `detail` shows a blank pop-up or none | Retry | See `evaluations-feedback-and-analytics.md` section 10 |
| `Feedback deleted successfully` | Success | `src/lib/components/admin/Evaluations/Feedbacks.svelte:121` | The feedback item was deleted; the list returns to page 1 | None | See `evaluations-feedback-and-analytics.md` section 10 |
| `Redirecting you to Open WebUI Community` | Success | `src/lib/components/admin/Evaluations/Feedbacks.svelte:131` | **Never shown**: `shareHandler` (`:127`) is defined but nothing calls it | None | See `evaluations-feedback-and-analytics.md` section 10 |
| `No feedback found`; `Try adjusting your search or filter to find what you are looking for.` | Inline | `src/lib/components/admin/Evaluations/Feedbacks.svelte:306-314` | The list (with its model filter) is empty, or loading it failed after the red pop-up | Set the filter to all models | See `evaluations-feedback-and-analytics.md` section 10 |
| `No models found` | Inline | `src/lib/components/admin/Evaluations/Leaderboard.svelte:167-168` | No model to rank. **(silent on failure)**: a failed leaderboard load is only written to the browser console (`:88-89`), so it shows the same text | Reload; check model connections | See `evaluations-feedback-and-analytics.md` section 10 |
| `No activity data` | Inline | `src/lib/components/admin/Evaluations/ModelActivityChart.svelte:186-188` | The model's chart has no wins or losses in the chosen range | Choose a longer range | See `evaluations-feedback-and-analytics.md` section 10 |
| (no text) | (silent on failure) | `src/lib/components/admin/Evaluations/FeedbackModal.svelte:28-30`; `src/lib/components/admin/Evaluations/LeaderboardModal.svelte:37-38` | Opening one feedback item or a model's history failed: the window opens with nothing loaded | Close and reopen | Escalate with the time if it repeats |
| `No data` | Inline | `src/lib/components/admin/Analytics/Dashboard.svelte:512`, `:613` | No activity in the chosen period or group. **(silent on failure)**: a failed dashboard load is only written to the console (`:117-159`) and leaves the same empty tables | Widen the period; reload | See `evaluations-feedback-and-analytics.md` section 10 |
| `Token counts are estimates and may not reflect actual API usage` | Inline (tooltip) | `src/lib/components/admin/Analytics/Dashboard.svelte:294` | Hovering the token total | None | See `evaluations-feedback-and-analytics.md` section 10 |
| (no text) | (silent on failure) | `src/lib/components/admin/Analytics/AnalyticsModelModal.svelte:68-69`, `:109-110`, `:144-145` | A model's analytics window could not load its overview or chats | Close and reopen | Escalate if it repeats |

`src/lib/components/admin/Evaluations.svelte` loads the tab counters with every error swallowed
(`:50-56`) and shows no message; `src/lib/components/admin/Analytics.svelte` only sends a
non-admin to `/` and mounts the dashboard (`:12-24`). `src/lib/components/admin/Analytics/ChartLine.svelte` draws a chart and has no
text of its own.

### 10.3 `admin/Functions.svelte` and `admin/Functions/` (Admin Panel › Functions and the Function Editor)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{error}` (server text) | Error | `src/lib/components/admin/Functions.svelte:271`, `:91`, `:160`, `:190`, `:206`, `:220`, `:242`, `:801` | Loading the list failed (`:271`; the list then reads `No functions found`), or **Export JSON** (`:91`), **Share** (`:160`), **Clone** (`:190`), **Export** of one function (`:206`), **Delete** (`:220`), the **Global** switch (`:242`) or one entry of an **Import JSON** file (`:801`) was refused. A failure without a `detail` shows nothing; a validation list shows `[object Object]` | Retry; reload the page | See `functions-pipes-filters-actions-and-pipelines.md` section 10 (10.1 lists the server texts) |
| `Function deleted successfully` | Success | `src/lib/components/admin/Functions.svelte:225` | **Delete** confirmed, or the bin icon clicked while **Shift** is held, which deletes at once **without** a confirmation (`:584-596`) | None | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `Filter is now globally enabled`; `Filter is now globally disabled`; `Function is now globally enabled`; `Function is now globally disabled` | Success | `src/lib/components/admin/Functions.svelte:248`, `:252`, `:249`, `:253` | The **Global** switch in the `...` menu of a filter or an action was saved (`src/lib/components/admin/Functions/FunctionMenu.svelte:49-61`); actions get the "Function" wording. The switch moves before the save and stays moved when the save fails (`:240-243`) | Reload to see the stored state | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `Functions imported successfully` | Success **(unchecked success)** | `src/lib/components/admin/Functions.svelte:806` | End of an **Import JSON** run, shown even when every entry failed (each failure shows its own red pop-up first, `:794-805`). A file that is not valid JSON stops the import with no message at all (`:789-791`) **(silent on failure)** | Check that the expected functions now appear | See `functions-pipes-filters-actions-and-pipelines.md` section 10 and 11.11 |
| `Redirecting you to Open WebUI Community` | Success | `src/lib/components/admin/Functions.svelte:167` | **Share** in the `...` menu (offered whatever the community-sharing setting, `src/lib/components/admin/Functions/FunctionMenu.svelte:91-100`): a new tab opens the upstream community site and the function's details are passed to it (`:158-186`). Shown even when reading the function failed. Upstream wording beside a licence comment (`:164-166`) | Follow local policy on public sharing (TO BE CONFIRMED) | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `Delete function?`; `This will delete {name}.` | Dialog | `src/lib/components/admin/Functions.svelte:753-764` | **Delete** in the `...` menu; `{name}` is the function's name in the interface language | Confirm only if intended | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `Confirm your action`; `Please carefully review the following warnings:`; `Functions allow arbitrary code execution.`; `Do not install functions from sources you do not fully trust.`; `I acknowledge that I have read and I understand the implications of my action. I am aware of the risks associated with executing arbitrary code and I have verified the trustworthiness of the source.` | Dialog (default title, warning text) | `src/lib/components/admin/Functions.svelte:786-840` (texts `:826-838`); title `src/lib/components/common/ConfirmDialog.svelte:143` | A file was chosen with **Import JSON** (`:336-346`); **Confirm** starts the import | Confirm only for reviewed code | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `No functions found`; `Try adjusting your search or filter to find what you are looking for.` | Inline | `src/lib/components/admin/Functions.svelte:729`, `:731` | The filtered list is empty: no function yet, nothing matches the search, type or view filter, or loading failed (after the red pop-up) | Clear the search and filters | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `Deleted User` | Inline (owner column and tooltip) | `src/lib/components/admin/Functions.svelte:571`, `:577` | The account that owns the function no longer exists | None | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| (no text) | (silent on failure) | `src/lib/components/admin/Functions.svelte:701-720` | The on/off switch of a function: the request is sent without waiting for it and without error handling (`:706`), so a refusal shows nothing and the switch stays in its new position | Reload the page to see the stored state | See `functions-pipes-filters-actions-and-pipelines.md` section 5.5 and 11.9 |
| `Name and description are required` | Error, **never displayed** | `src/lib/components/admin/Functions/FunctionEditor.svelte:329-332` | The name or description is empty after trimming. The file never imports the pop-up library (its imports are `:2-16`), so this line stops with a script error: the editor switches back to the base language and **nothing is saved and nothing is shown** | Type a real name and description, then save again | See `functions-pipes-filters-actions-and-pipelines.md` section 10 and 11.10 |
| `Warning:`; `Functions can execute arbitrary code.`; `Only install functions from sources you trust.` | Inline (warning) | `src/lib/components/admin/Functions/FunctionEditor.svelte:502-506` | Footer of the code editor, always shown | None | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `Confirm your action` and the same four warning and acknowledgement texts as the import dialog | Dialog | `src/lib/components/admin/Functions/FunctionEditor.svelte:524-546` | **Save & Create** on a new function (`:371-377`); saving an existing function skips the dialog | Confirm only for reviewed code | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `Conversation turn limit exceeded. Max turns: {max_turns}` | Error (in a chat reply, not in the editor) | `src/lib/components/admin/Functions/FunctionEditor.svelte:101-104` | Text of the **Filter** starter code (`:51-126`). A function saved from the starter unchanged, switched on and global or attached to a model refuses chats with more messages than the smaller of the two `max_turns` values | Escalate to an admin | See `functions-pipes-filters-actions-and-pipelines.md` section 10 and 11.7 |

`src/lib/components/admin/Functions/FunctionMenu.svelte` has labels only (**Global**, **Edit**,
**Share**, **Clone**, **Export**, **Delete**). `src/lib/components/admin/Functions/AddFunctionMenu.svelte`
is not imported by any file in `src/`, so its labels never appear. The second starter in the editor,
`_boilerplate` (`src/lib/components/admin/Functions/FunctionEditor.svelte:174-326`), is never used,
so its texts (for example `Could not fetch models from OpenAI, please update the API Key in the
valves.`, `:288`) cannot appear (section 14).

### 10.4 `admin/Settings/`: General, Events, UI Translations, Authentication and Database

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Settings saved successfully!` | Success | `src/lib/components/chat/SettingsModal.svelte:461`, called from `src/lib/components/admin/Settings/General.svelte:94` | **Save** on **General**, after the admin settings, the UI translations and the banners were all stored and the configuration reloaded (`:80-94`). On this tab the pop-up proves the save | None | See `admin-settings-panels.md` section 10 |
| `Failed to update settings` | Thrown, shown as Error | `src/lib/components/admin/Settings/General.svelte:90`, shown at `:96-102` | The save came back with nothing: the request failed without a server text (a lost connection, a proxy's error page), so the client returned no data (`src/lib/apis/auths/index.ts:57-79`) | Retry once | See `admin-settings-panels.md` section 10 |
| `{error.message}` (server text; a list of problems is printed one per line) | Error | `src/lib/components/admin/Settings/General.svelte:96-102` | Any other failure of **Save**: the server refused the settings, a UI Translations row failed a check (next row), or storing the banners failed (`:92`) after the settings were already stored | Read the text | See `admin-settings-panels.md` section 10; server texts in `error-messages-backend-identity-admin-and-platform.md` section 10 |
| `Original text is required for translated rows.`; `Duplicate original text: {entry.content}`; `Invalid translation key: {key}`; `Interpolation placeholders do not match: {key}`; `Invalid language: {locale}` (untranslated) | Thrown, shown as Error | `src/lib/utils/translationDictionary.ts:60`, `:63`, `:17`, `:23`, `:31`; shown by `src/lib/components/admin/Settings/General.svelte:96` | A **UI Translations** row failed a check before anything was sent (`:84`): a value without a key, the same key twice, a blank or reserved key, different `{{…}}` placeholders, a blank or reserved language | Fix the row named | See `admin-settings-panels.md` section 10 |
| `Could not check for updates` | Inline | `src/lib/components/admin/Settings/General.svelte:143-146` | The upstream release look-up failed; shown only when the version check is switched on (`:142`) | None | See `admin-settings-panels.md` section 10 |
| `Checking for updates...`; `(v{version.latest} available!)`; `(latest)` | Inline | `src/lib/components/admin/Settings/General.svelte:153-157` | Look-up running; a newer **upstream** Open WebUI release exists; or this is the latest upstream release. The link opens the upstream release page | None: an upstream release is not a MedIT GPT release | See `admin-settings-panels.md` section 10 and 11.15 |
| `Upgrade to a licensed plan for enhanced capabilities, including custom theming and branding, and dedicated support.` | Inline | `src/lib/components/admin/Settings/General.svelte:266-268` | No licence data is loaded; upstream wording beside a licence comment (`:230-232`) | None | See `admin-settings-panels.md` section 10 |
| (no text) | (silent on failure) | `src/lib/components/admin/Settings/General.svelte:108-111` | Loading the panel failed (no error handling): only the title and **Save** show | Reload; do not press **Save** on an empty panel | Escalate with the time |
| `Use a valid event name or pattern like user.*` | Error | `src/lib/components/admin/Settings/Events.svelte:228` | **Add** in the webhook window with text that is not `*`, a listed event name or a `prefix.*` that matches listed names (`:209-219`) | Pick from the list or fix the pattern | See `notifications-webhooks-events-and-banners.md` section 10 |
| `Webhook saved` | Success | `src/lib/components/admin/Settings/Events.svelte:355` | The webhook was created or changed and the list reloaded | None | See `notifications-webhooks-events-and-banners.md` section 10 |
| `Failed to save webhook` | Error | `src/lib/components/admin/Settings/Events.svelte:357` | **Save** in the webhook window was refused. The server's reason is never shown: the request helper hands over the whole answer, not text (`src/lib/apis/index.ts:1695-1705`), so the panel prints its own words (`:357`). Also shown when the save worked but reloading the list failed (`:353`) | Check the address and the filters, save again | See `notifications-webhooks-events-and-banners.md` section 10 |
| `Failed to delete webhook`; `Failed to update webhook` | Error | `src/lib/components/admin/Settings/Events.svelte:372`, `:386` | **Delete** (`:372`) or a row's on/off switch (`:386`; the switch flips back, `:383-385`) was refused; as above, the server's reason is not shown | Reload and retry | See `notifications-webhooks-events-and-banners.md` section 10 |
| `Webhook deleted` | Success | `src/lib/components/admin/Settings/Events.svelte:370` | The webhook was deleted after the confirmation | None | See `notifications-webhooks-events-and-banners.md` section 10 |
| `Confirm your action`; `Are you sure you want to delete this webhook? This action cannot be undone.` | Dialog (default title) | `src/lib/components/admin/Settings/Events.svelte:683-690` | **Delete** inside the window of an existing webhook (`:658-668`) | Confirm only if intended | See `notifications-webhooks-events-and-banners.md` section 10 |
| `No event webhooks configured.` | Inline | `src/lib/components/admin/Settings/Events.svelte:758-761` | No admin webhook exists. **(silent on failure)**: the list is loaded without error handling (`:76-85`, `:390`), so a failed load shows the same text | Reload | See `notifications-webhooks-events-and-banners.md` section 10 |
| `Not configured` | Inline | `src/lib/components/admin/Settings/Events.svelte:180-186` | A webhook row whose address is empty (an address that is not a valid URL is shown as typed) | Edit the webhook | See `notifications-webhooks-events-and-banners.md` section 10 |
| `Event names may change as Open WebUI evolves. Use broad patterns like user.* for integrations that should continue across new related events.` | Inline (notice) | `src/lib/components/admin/Settings/Events.svelte:644-651` | The event list of the webhook window, when **All events** is off (`:581`); upstream wording beside a licence comment | None | See `notifications-webhooks-events-and-banners.md` section 10 |
| `Receives matching events across the instance, including system/config events and events associated with any user.`; `Receives matching events that are not associated with a user.`; `Receives matching user-associated events only when the actor, user subject, or user data matches these users or current group members. System/config events are not sent.` | Inline (help) | `src/lib/components/admin/Settings/Events.svelte:465-477` | Under **Send events for**, one per choice | None | See `notifications-webhooks-events-and-banners.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/admin/Settings/Authentication.svelte:92`, `:70`, `:80` | **Save** stores three parts in turn: the sign-in settings (`:92`), LDAP (`:70`, for example `Required field {name} is empty`) and OAuth when editable (`:80`). Each part is tried even when an earlier one failed, and the parts that succeeded stay stored. A refusal without a `detail` shows nothing; a list of problems shows `[object Object]` | Read the text, correct the field, save again | See `admin-settings-panels.md` section 10 and `sso-oauth-oidc-and-scim.md` section 10; server texts in `error-messages-backend-identity-admin-and-platform.md` section 10 |
| `Settings saved successfully!` | Success | `src/lib/components/admin/Settings/Authentication.svelte:104` | All three parts were stored (`:99-106`). The panel shows its own pop-up; the window passes it no handler (`src/lib/components/chat/SettingsModal.svelte:855-856`) | None | See `admin-settings-panels.md` section 10 |
| (no text) | (silent on failure) | `src/lib/components/admin/Settings/Authentication.svelte:59`, `:109-128` | Saving the LDAP on/off switch has no error handling (`:59`): a refusal stops **Save** with no message and OAuth is not saved. Loading the panel without error handling (`:109-128`) leaves it empty; a failed OAuth load only hides the **OAuth / OIDC** section (`:122-124`, `:546`) | Reload and retry | See `admin-settings-panels.md` section 11.3 |
| `No expiration can pose security risks.` | Inline (warning link) | `src/lib/components/admin/Settings/Authentication.svelte:243-251` | **JWT Expiration** is exactly `-1`; the link opens upstream documentation | Admin decision | See `admin-settings-panels.md` section 10 and `authentication-and-sign-in.md` |
| `These settings are read from environment variables and cannot be edited here while {{ENV_VAR}} is disabled.` (`ENV_VAR` is `ENABLE_OAUTH_PERSISTENT_CONFIG`) | Inline (warning) | `src/lib/components/admin/Settings/Authentication.svelte:550-559` | OAuth settings are not persisted, so the section is read-only and **Save** skips it (`:78`) | Changes need the environment and a restart | See `sso-oauth-oidc-and-scim.md` section 10 and `admin-settings-panels.md` section 11.8 |
| `Config imported successfully` | Success | `src/lib/components/admin/Settings/Database.svelte:77-79` | **Import Config** wrote the file's settings | Some settings need a re-save or a restart | See `admin-settings-panels.md` section 10 and 5.9 |
| `{error}` (server text) | Error | `src/lib/components/admin/Settings/Database.svelte:71-75`, `:130-134` | **Import Config** was refused (`:73`; may read `[object Object]` when the file is not a JSON object of settings) or the **Database** download was refused (`:133`), for example `This feature is only available with SQLite databases.` | Use an unmodified export file; never attach it to a ticket (it contains secrets) | See `admin-settings-panels.md` section 10; server texts in `error-messages-backend-identity-admin-and-platform.md` section 10 |
| (no text) | (silent on failure) | `src/lib/components/admin/Settings/Database.svelte:71`, `:109-115`, `:23-28`, `:30-51` | An import file that is not valid JSON (`:71`) stops with no message. **Export Config** (`:109-115`), **All Chats** (`:23-28`) and **Users** (`:30-51`) have no error handling, so a failure downloads nothing and shows nothing | Retry; escalate with the time | See `admin-settings-panels.md` section 11.4 |

`src/lib/components/admin/Settings/I18nSettings.svelte` (the **UI Translations** rows),
`AdminSettingField.svelte`, `AdminSettingRow.svelte`, `AdminSettingSection.svelte` and
`AdminTabIcon.svelte` in the same folder have labels or no text at all. The **Database** tab never
shows `Settings saved successfully!`: the window hands it a handler
(`src/lib/components/chat/SettingsModal.svelte:897-901`) that the panel accepts but never calls
(`src/lib/components/admin/Settings/Database.svelte:17`).

### 10.5 `admin/Settings/`: Connections, Models, Sub-agents, Evaluations and Pipelines

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Settings saved successfully!` | Success **(unchecked success)** | `src/lib/components/chat/SettingsModal.svelte:860`, triggered at `src/lib/components/admin/Settings/Connections.svelte:218` | **Save** on **Connections**: the OpenAI and Ollama saves are started without waiting for them (`:214-218`), so this appears at once, before either save has finished and even when both fail | Wait for the two messages in the next row, or reopen the tab | See `admin-settings-panels.md` section 10 and 11.3 |
| `OpenAI API settings updated`; `Ollama API settings updated` | Success | `src/lib/components/admin/Settings/Connections.svelte:87`, `:107` | The OpenAI or Ollama connection list was stored: after **Save**, the **OpenAI API** or **Ollama API** switch (`:246-247`, `:305-306`), or adding, editing or deleting a connection (`:138-154`, `:280-294`, `:338-349`) | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Connections settings updated` | Success | `src/lib/components/admin/Settings/Connections.svelte:119` | **Direct Connections** or **Cache Base Model List** was switched and stored (`:379-380`, `:412-413`) | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Model list refreshed` | Success | `src/lib/components/admin/Settings/Connections.svelte:130` | **Refresh**, offered while the base model cache is on (`:392-399`), reloaded the model list | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/admin/Settings/Connections.svelte:83`, `:103`, `:115`, `:132` | Storing the OpenAI list (`:83`) or the Ollama list (`:103`) was refused (without a server text these read `Server connection failed`, `src/lib/apis/openai/index.ts:3-13`; `src/lib/apis/ollama/index.ts:91-95`), storing the switches was refused (`:115`), or **Refresh** failed (`:132`; that client hands over the whole answer, so it may read `[object Object]`) | Read the text; check the connection's address and key | See `model-connections-openai-ollama-and-direct.md` section 10; server texts in `error-messages-backend-chat-content-and-features.md` section 10 |
| (no text) | (silent on failure) | `src/lib/components/admin/Settings/Connections.svelte:156-212`, `:420-424` | Loading the tab has no error handling: a failed load leaves the spinner (`:420-424`) | Reload | Escalate with the time |
| `Trouble accessing Ollama?` with `Click here for help.` | Inline (help link) | `src/lib/components/admin/Settings/Connections.svelte:355-363`; text `src/lib/i18n/locales/en-US/translation.json:2175` | Under the Ollama connection list; the link opens the upstream troubleshooting page | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `WebUI will make requests to "{{url}}/api/chat"`; `WebUI will make requests to "{{url}}/chat/completions"` | Inline (tooltip) | `src/lib/components/admin/Settings/Connections/OllamaConnection.svelte:51-53`; `src/lib/components/admin/Settings/Connections/OpenAIConnection.svelte:48-50` | Hovering a connection's address | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Model order saved successfully` | Success | `src/lib/components/admin/Settings/Models.svelte:350` | **Save** after dragging models into a new order (`:362-367`) | None | See `workspace-models-and-model-access.md` section 10 |
| `Model added to selected models`; `Model removed from selected models`; `Model added to pinned models`; `Model removed from pinned models` | Success | `src/lib/components/admin/Settings/Models.svelte:416-418`, `:431-433`, shown at `:400` | **Set as Selected Model**, **Set as Pinned Model** or their **Remove** forms in a model's `...` menu (`src/lib/components/admin/Settings/Models/ModelMenu.svelte:121`, `:136`) or the Shift-key buttons (`:1074-1131`) stored the defaults. A refusal shows the server text and restores the previous choice (`:401-404`) | None | See `workspace-models-and-model-access.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/admin/Settings/Models.svelte:343`, `:394`, `:508`, `:1293`, `:259`, `:653` | Saving the order (`:343`) or the defaults (`:394`) was refused; reloading the list after a save failed (`:508`, `:1293`); **Export** of all models (`:259`) or of one model (`:653`) failed | Retry; reload | See `workspace-models-and-model-access.md` section 10; server texts in `error-messages-backend-chat-content-and-features.md` section 10 |
| `Model updated successfully` | Success | `src/lib/components/admin/Settings/Models.svelte:490`, `:507` | The base-model editor (opened with the pencil) stored the model (`:1282-1294`) | None | See `workspace-models-and-model-access.md` section 10 |
| `Failed to save model` | Error | `src/lib/components/admin/Settings/Models.svelte:1289` | The base-model editor's save was refused. The server's reason is not shown: the save helper drops it (`:485-487`, `:502-504`) | Retry; note the time | See `workspace-models-and-model-access.md` section 10 and 11.22 |
| `All models are now visible`; `All models are now hidden` | Success **(unchecked success)** | `src/lib/components/admin/Settings/Models.svelte:229`, `:248` | **Actions** › **Show All** or **Hide All** finished. Refusals of single models are dropped without a message (`:223-227`, `:242-246`, `:485-487`), so this also follows a partial failure | Reopen the tab and check | See `workspace-models-and-model-access.md` section 10 |
| `Model {{name}} is now hidden`; `Model {{name}} is now visible` | Success **(unchecked success)** | `src/lib/components/admin/Settings/Models.svelte:558-566` | **Hide Model** or **Show Model** in the `...` menu (`src/lib/components/admin/Settings/Models/ModelMenu.svelte:71`) or the Shift-key eye button; `{{name}}` is the model's **ID**. Shown whether or not the save worked (`:549`) | Reopen and check | See `workspace-models-and-model-access.md` section 10 |
| `Model is now public`; `Model is now private` | Success | `src/lib/components/admin/Settings/Models.svelte:598-602` | **Make Public** or **Make Private** in the `...` menu stored the new access. A refusal shows nothing (`:586`) **(silent on failure)** | Reopen and check | See `workspace-models-and-model-access.md` section 10 |
| `Copied link to clipboard`; `Failed to copy link` | Success; Error | `src/lib/components/admin/Settings/Models.svelte:611`, `:613` | **Copy Link** in the `...` menu: the browser did or did not allow copying the `/?model={id}` address | Copy the address by hand | See `workspace-models-and-model-access.md` section 10 |
| `Reset All Models`; `This will delete all models including custom models and cannot be undone.` | Dialog | `src/lib/components/admin/Settings/Models.svelte:709-720` | **Actions** › **Reset** (`:894`) | Cancel unless every model record is meant to go | See `workspace-models-and-model-access.md` section 10 and 5.18 |
| `All models deleted successfully` | Success | `src/lib/components/admin/Settings/Models.svelte:716` | The reset was confirmed and done. A refusal is not caught (`:714`) and shows nothing | None | See `workspace-models-and-model-access.md` section 10 |
| `Models imported successfully` | Success | `src/lib/components/admin/Settings/Models.svelte:755` | **Actions** › **Import** (admins) stored the file's models | None | See `workspace-models-and-model-access.md` section 10 |
| `Failed to import models` | Error | `src/lib/components/admin/Settings/Models.svelte:758` | The import answered without success. The server answers either `true` or an error (`backend/open_webui/routers/models.py:441`, `:664`), so this text is not expected | Retry | See `workspace-models-and-model-access.md` section 10 |
| `{e.detail}` (server text) or `Invalid JSON file` | Error | `src/lib/components/admin/Settings/Models.svelte:760-761` | The import was refused (server text), or the file is not JSON. A request that failed without a server text also lands here, so `Invalid JSON file` can appear for a valid file | Use a file exported from MedIT GPT; retry | See `workspace-models-and-model-access.md` section 10 |
| `No models found`; `Try adjusting your search or filter to find what you are looking for.` | Inline | `src/lib/components/admin/Settings/Models.svelte:1250`, `:1253` | The filtered list is empty | Clear the search and filters | See `workspace-models-and-model-access.md` section 10 |
| (no text) | (silent on failure) | `src/lib/components/admin/Settings/Models.svelte:514-538`, `:187-213`, `:662-670`, `:268-331` | A model's on/off switch (`:514-538`), **Enable All** and **Disable All** (`:187-213`) and **Hide from Sidebar** / **Keep in Sidebar** (`:662-670`) show nothing, on success or failure. A failed load of the tab (`:268-331`, no error handling) leaves the spinner | Reload and check | See `workspace-models-and-model-access.md` section 11 |
| `Models configuration saved successfully` | Success | `src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:143` | **Save** with changed **Model Defaults** stored them (`:105-145`) | None | See `admin-settings-panels.md` section 10 |
| `{error}` (server text), then `Failed to save models configuration` | Error (two pop-ups) | `src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:125`, `:147` | The defaults were refused: the server text first, then this sentence | Retry; escalate | See `admin-settings-panels.md` section 10 |
| (no text) | (silent on failure) | `src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:116`, `:132-136` | Re-reading the model settings before the save (`:116`) or storing the prompt suggestions after it (`:132-136`) has no error handling; a failure stops with no message, possibly after the defaults were stored | Reopen and check | Escalate with the time |
| `No inference engine with management support found` | Inline | `src/lib/components/admin/Settings/Models/ManageModelsModal.svelte:101-105` | **Actions** › **Manage**: no Ollama connection is on, and no OpenAI-compatible connection is set to the `llama.cpp` or `lmstudio` provider (`:24`, `:34-79`) | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Checking for model updates...`; `Model update cancelled`; `All models are up to date` (untranslated) | Info; Info; Success **(unchecked success)** | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:80`, `:154`, `:156` | **Update All Models** (`:626-632`) started, was cancelled, or finished. The last also follows failed updates: errors in the download stream go only to the console (`:140-145`) | Check each model if in doubt | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Model '{{modelTag}}' is already in queue for downloading.` | Error | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:166-170` | The same tag is already downloading in this browser | Wait | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Maximum of 3 models can be downloaded simultaneously. Please try again later.` | Error | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:173-176` | Three downloads are already running in this browser (`:45`) | Wait | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Model '{{modelName}}' has been successfully downloaded.` | Success | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:271-275` | The pull finished | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Download canceled` | Error | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:284` | The pull ended unfinished: it was cancelled, or it failed (the failure text appears first, `:260`) | Retry | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `{{model}} download has been canceled` | Success | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:492` | **Cancel** on a running download | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Deleted {{deleteModelTag}}` | Success | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:455` | **Delete Model** confirmed and done | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Confirm your action`; `This action cannot be undone. Do you wish to continue?` | Dialog (default texts) | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:608-613` | **Delete Model** (`:846`) | Confirm only if intended | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `{error}` or `{err}` (server or Ollama text) | Error | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:93`, `:184`, `:260`, `:312`, `:320`, `:367`, `:426`, `:451`, `:467`, `:504`, `:517`, `:571`, `:594` | A pull (`:93` during **Update All Models**, `:184`, `:260` with Ollama's own text), an upload from a file or address (`:312`, `:320`, `:367`, `:426`), a delete (`:451`), loading the list (`:467`, `:594`), or **Create Model** (`:504`: the model description is not valid JSON; `:517`, `:571`) failed | Read the text | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `{data.status}` (Ollama text) | Success | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:409`, `:553` | Ollama reported a step, for example `success`, during an upload or **Create Model** | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Failed to fetch models` | Inline | `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:1142-1145` | Loading that Ollama server's models failed | Check the connection | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Model download started`; `Model loaded successfully`; `Model unloaded successfully`; `Model deleted successfully` | Success | `src/lib/components/admin/Settings/Models/Manage/ManageProviderModels.svelte:145`, `:150`, `:166`, `:174` (shown at `:134`) | A llama.cpp or LM Studio action was accepted | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `{error}` (server text, or `Server connection failed`) | Error | `src/lib/components/admin/Settings/Models/Manage/ManageProviderModels.svelte:106`, `:129`, `:160` | Loading the provider's catalogue (`:106`) or an action (`:129`, `:160`) failed; without any text the untranslated fallback `Server connection failed` is shown (`src/lib/apis/openai/index.ts:3-13`) | Check the connection | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Delete Model`; `This will delete the cached model and cannot be undone.` | Dialog | `src/lib/components/admin/Settings/Models/Manage/ManageProviderModels.svelte:185-190` | **Delete** on a provider model | Confirm only if intended | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `No models found` | Inline | `src/lib/components/admin/Settings/Models/Manage/ManageProviderModels.svelte:225-228` | The provider's catalogue is empty or could not be loaded | Check the connection | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Settings saved successfully!` | Success | `src/lib/components/admin/Settings/Subagents.svelte:50` | **Save** on **Sub-agents** stored the settings (`:38-50`) | None | See `admin-settings-panels.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/admin/Settings/Subagents.svelte:32`, `:52` | Loading (`:32`) or saving (`:52`) the sub-agent settings failed | Retry | See `admin-settings-panels.md` section 10; server texts in `error-messages-backend-identity-admin-and-platform.md` section 10 |
| `Settings saved successfully!` | Success | `src/lib/components/admin/Settings/Evaluations.svelte:32` | **Save**, or adding, editing or deleting an arena model, was stored (`:24-43`). The panel's own pop-up; the window attaches no handler (`src/lib/components/chat/SettingsModal.svelte:867-868`) | None | See `evaluations-feedback-and-analytics.md` section 10 |
| `{err}` (server text) | Error | `src/lib/components/admin/Settings/Evaluations.svelte:26`, `:78` | Saving (`:26`) or loading (`:78`; the tab then keeps its spinner, `:156-160`) failed. After a refused delete the arena model disappears from the list although it is still stored (`:61-66`) | Reload | See `evaluations-feedback-and-analytics.md` section 10 |
| `Message rating should be enabled to use this feature` | Inline (tooltip) | `src/lib/components/admin/Settings/Evaluations.svelte:106` | Hovering the **Arena Models** switch | Admin: message rating is switched on in **General** | See `evaluations-feedback-and-analytics.md` section 10 |
| `Using the default arena model with all models. Click the plus button to add custom models.` | Inline | `src/lib/components/admin/Settings/Evaluations.svelte:146-151` | Arena models are on and no custom arena model exists | None | See `evaluations-feedback-and-analytics.md` section 10 |
| `Name and ID are required, please fill them out` | Error | `src/lib/components/admin/Settings/Evaluations/ArenaModelModal.svelte:72-75` | **Save** in the arena model window with an empty name or ID | Fill in both | See `evaluations-feedback-and-analytics.md` section 10 |
| `Model name already exists, please choose a different one` | Error | `src/lib/components/admin/Settings/Evaluations/ArenaModelModal.svelte:78-83` | A new arena model has the same name as a model already in the model list | Choose another name | See `evaluations-feedback-and-analytics.md` section 10 |
| `{error}` | Error | `src/lib/components/admin/Settings/Evaluations/ArenaModelModal.svelte:100-104` | Only when the save handler throws. The panel catches a refused save itself (`src/lib/components/admin/Settings/Evaluations.svelte:24-28`), so in practice this means the arena model **was** stored but reloading the model list afterwards failed (`:33-40`); the text may read `[object Object]` | Reload the tab and check the arena model | See `evaluations-feedback-and-analytics.md` section 10 |
| `Confirm your action`; `This action cannot be undone. Do you wish to continue?` | Dialog (default texts) | `src/lib/components/admin/Settings/Evaluations/ArenaModelModal.svelte:152-158` | **Delete** in the arena model window (`:421`) | Confirm only if intended | See `evaluations-feedback-and-analytics.md` section 10 |
| `Leave empty to include all models or select specific models` | Inline (help) | `src/lib/components/admin/Settings/Evaluations/ArenaModelModal.svelte:379` | The model filter of an arena model | None | See `evaluations-feedback-and-analytics.md` section 10 |
| `No valves to update` | Error | `src/lib/components/admin/Settings/Pipelines.svelte:53`, `:89` | **Save** with no pipeline loaded (`:52-54`) or with a pipeline that declares no valves (`:88-89`) | None | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `Valves updated successfully`, then `Settings saved successfully!` | Success (two pop-ups) | `src/lib/components/admin/Settings/Pipelines.svelte:76`, `:86`; second text `src/lib/components/chat/SettingsModal.svelte:906` | The selected pipeline's valves were stored on the pipelines server | None | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `Pipeline downloaded successfully` | Success | `src/lib/components/admin/Settings/Pipelines.svelte:150`, `:182` | **Install** from a GitHub raw address (`:150`) or **Upload Pipeline** of a `.py` file (`:182`) succeeded | None | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `Something went wrong :/` | Error | `src/lib/components/admin/Settings/Pipelines.svelte:176` | **Upload Pipeline** failed; the reason goes only to the browser console (`:175`) | Retry; escalate | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `No file selected` | Error | `src/lib/components/admin/Settings/Pipelines.svelte:194` | **Upload** with no file chosen | Choose a `.py` file | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `Pipeline deleted successfully` | Success | `src/lib/components/admin/Settings/Pipelines.svelte:225` | **Delete** on the selected pipeline; it acts at once, without a confirmation (`:387-392`) | None | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/admin/Settings/Pipelines.svelte:72`, `:145`, `:220` | Saving valves (`:72`), **Install** (`:145`) or **Delete** (`:220`) was refused. Without a server `detail` the client hands over the whole answer, which prints as `[object Object]` (`src/lib/apis/index.ts:1428-1430`) | Read the text | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `Pipelines Not Detected` | Inline | `src/lib/components/admin/Settings/Pipelines.svelte:465`, `:478` | No model connection is a pipelines server (`:473-479`), or the selected one lists no pipeline (`:461-466`). Loading has no error handling (`:239`, `:126`, `:101-110`), so a failure shows a spinner that never ends instead **(silent on failure)** | Check the pipelines connection | See `functions-pipes-filters-actions-and-pipelines.md` section 10 and 11.6 |
| `No valves` | Inline | `src/lib/components/admin/Settings/Pipelines.svelte:457-458` | The selected pipeline declares no valves | None | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `Pipelines are a plugin system with arbitrary code execution.` `Don't fetch random pipelines from sources you don't trust.` | Inline (warning) | `src/lib/components/admin/Settings/Pipelines.svelte:335` | Description of **GitHub URL** | Install only reviewed code | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |

`src/lib/components/admin/Settings/Connections/ManageOllamaModal.svelte`,
`src/lib/components/admin/Settings/Models/ModelMenu.svelte`, `Models/AdminViewSelector.svelte`,
`Models/Manage/ManageMultipleOllama.svelte`, `Models/Manage/ManageMultipleProviderModels.svelte` and
`Evaluations/Model.svelte` have labels only. The **Evaluations** form also dispatches a `save` event
(`src/lib/components/admin/Settings/Evaluations.svelte:91`) that nothing listens to, so it adds no
second pop-up.

### 10.6 `admin/Settings/`: Interface, Banners, Audio and Images

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Settings saved successfully!` | Success **(unchecked success)** | `src/lib/components/chat/SettingsModal.svelte:882`, triggered at `src/lib/components/admin/Settings/Interface.svelte:166-169` | **Save** on **Interface**: the task and chat settings are sent without waiting (`:167`), so the window shows this at once. A refused save is not caught (`:70-73`) and shows nothing **(silent on failure)** | Reopen the tab and check the values | See `admin-settings-panels.md` section 10 and 11.3 |
| `This model is not publicly available. Please select another model.` | Error | `src/lib/components/admin/Settings/Interface.svelte:103-110` | Choosing a **Local Task Model**, **External Task Model** or **Context Compaction Model** (`:193-195`, `:212-216`, `:288-292`) whose access does not give read access to everyone. The choice is kept anyway (`:112`) and can be saved | Choose another model, or ask for the model's access to be widened | See `admin-settings-panels.md` section 10 and `chat-completion-pipeline-and-generation-tasks.md` section 10 |
| `{error.detail}` or `{error.message}` (server or browser text), otherwise `Failed to load Interface settings` | Error | `src/lib/components/admin/Settings/Interface.svelte:150-155` | Loading the task settings, chat settings or model list failed; the tab then keeps its spinner (`:163`, `:570-572`) | Reload the page | See `admin-settings-panels.md` section 10 |
| `Leave empty to use the default prompt, or enter a custom prompt`; `-1 for no limit, or a positive integer for a specific limit` | Inline (placeholder) | `src/lib/components/admin/Settings/Interface.svelte:351` and eight other lines; `:517` | An empty prompt template box; an empty autocomplete input length | None: empty means the built-in prompt | See `admin-settings-panels.md` section 10 |
| `Settings saved successfully!` | Success | `src/lib/components/chat/SettingsModal.svelte:888`, called from `src/lib/components/admin/Settings/Audio.svelte:183` | The audio settings were stored: **Save** (`:240-245`), choosing a **Text-to-Speech Engine**, which saves at once (`:489-510`), or the Whisper model update button (`:445-451`) | None | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Invalid JSON format for Parameters` | Error | `src/lib/components/admin/Settings/Audio.svelte:138-143` | The text-to-speech **Parameters** box is not valid JSON; nothing is saved | Correct the JSON | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `{e}` (server text) | Error | `src/lib/components/admin/Settings/Audio.svelte:96`, `:123` | Loading the model list (`:96`; that client hands over the whole answer, so it may read `[object Object]`) or the voice list (`:123`) for the chosen engine failed | Check the engine's address and key | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| (no text) | (silent on failure) | `src/lib/components/admin/Settings/Audio.svelte:146-185`, `:195` | A refused save is not caught, so no pop-up appears at all; the refusal text (for example the slim-image refusals in `admin-settings-panels.md` section 10.3) is only in the browser console. A failed load (`:195`) leaves the fields at their defaults | Reopen the tab and check | See `admin-settings-panels.md` section 11.3 |
| `Slim requires external speech providers. Local speech models and audio conversion are unavailable.` | Inline (notice) | `src/lib/components/admin/Settings/Audio.svelte:250-256` | The server runs the slim image (`features.slim`) | Choose external speech engines | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Settings saved successfully!` | Success | `src/lib/components/chat/SettingsModal.svelte:894`, after `src/lib/components/admin/Settings/Images.svelte:213-216` | **Save** stored the image settings | None | See `image-generation-and-editing.md` section 10 |
| `AUTOMATIC1111 Base URL is required.`; `ComfyUI Base URL is required.`; `OpenAI API Key is required.`; `Gemini API Key is required.` | Error | `src/lib/components/admin/Settings/Images.svelte:111-133` | **Save** with that engine chosen and its address or key empty; **Image Generation** is switched off in the form and nothing is sent | Fill in the field | See `image-generation-and-editing.md` section 10 |
| `Invalid JSON format for ComfyUI Workflow.`; `Invalid JSON format for ComfyUI Edit Workflow.` | Error | `src/lib/components/admin/Settings/Images.svelte:179-184`, `:196-201` | A ComfyUI workflow box is not a JSON object | Paste the workflow exported in API format | See `image-generation-and-editing.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/admin/Settings/Images.svelte:105`, `:148`, `:224`, `:451`, `:522`, `:835` | Loading the model list (`:105`), saving (`:148`), loading the settings (`:224`), or a connection check for AUTOMATIC1111 (`:451`), ComfyUI (`:522`) or the ComfyUI editing server (`:835`) failed | Read the text; check the address | See `image-generation-and-editing.md` section 10; server texts in `error-messages-backend-chat-content-and-features.md` section 10 |
| `Server connection verified` | Success | `src/lib/components/admin/Settings/Images.svelte:456-458`, `:527-529`, `:840-842`; text `src/lib/i18n/locales/en-US/translation.json:2469` | The connection check button beside the address (announced as `verify connection`) succeeded | None | See `image-generation-and-editing.md` section 10 |
| `*Prompt node ID(s) are required for image generation` | Inline | `src/lib/components/admin/Settings/Images.svelte:687-689`, `:989-991` | Under the ComfyUI node table (generation and editing) | Fill in the prompt node ID | See `image-generation-and-editing.md` section 10 |
| (no text) | (silent on failure) | `src/lib/components/admin/Settings/Images.svelte:136-146`, `:1026-1036` | An **AUTOMATIC1111** parameters or OpenAI API parameters box that is not valid JSON stops **Save** with a script error: nothing is sent, no message appears, and the **Save** button stays disabled until the page is reloaded (`:177`, `:1030`) | Correct the JSON, reload, save again | See `image-generation-and-editing.md` section 11 |

`src/lib/components/admin/Settings/Interface/Banners.svelte` (the banner rows shown under
**General** › **Banners**) has labels only: the banner types `Info`, `Warning`, `Error` and
`Success`, `Content` and `Remember Dismissal`. Banner wording itself is data written by an admin.

### 10.7 `admin/Settings/`: Integrations, External Knowledge, Documents, Web Search and Code Execution

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Connections saved successfully` | Success | `src/lib/components/admin/Settings/Integrations.svelte:86` | The tool server list was stored: **Save** (`:177-181`), adding a tool server (`:72-75`), or editing or deleting one (`:214-222`) | None | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Failed to save connections` | Error | `src/lib/components/admin/Settings/Integrations.svelte:81` | The tool server list was refused; the server's reason is dropped (`:80-83`) | Check the entry just changed; escalate | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Terminal servers saved` | Success | `src/lib/components/admin/Settings/Integrations.svelte:99` | The terminal server list was stored; each add, edit, delete and on/off switch saves at once (`:119-137`, `:311`) | None | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Failed to save terminal servers` | Error | `src/lib/components/admin/Settings/Integrations.svelte:94` | The terminal server list was refused; the reason is dropped (`:93-96`) | Escalate | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Connections settings updated` | Success | `src/lib/components/admin/Settings/Integrations.svelte:67` | The **Direct Integrations** switch (`:353`) was stored | None | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/admin/Settings/Integrations.svelte:63` | Storing the **Direct Integrations** switch was refused | Retry | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `No tool server connections configured.`; `No terminal connections configured.` | Inline | `src/lib/components/admin/Settings/Integrations.svelte:229`, `:322` | The list is empty | None | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| (no text) | (silent on failure) | `src/lib/components/admin/Settings/Integrations.svelte:139-143`, `:188`, `:361` | Loading the tab has no error handling: a failure leaves the spinner | Reload | Escalate with the time |
| `External connection not found.` | Error | `src/lib/components/admin/Settings/ExternalKnowledge.svelte:145-150` | Opening an external knowledge source whose connection is not in the connection list | Reload; escalate if it repeats | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Fill the source fields and test query first.` | Error | `src/lib/components/admin/Settings/ExternalKnowledge.svelte:274-278` | **Test** with the address, source name, content field, a required vector or table field, or the test query empty (`:263-270`) | Fill in the fields | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Test succeeded.`; `Test returned no results.` | Success; Error | `src/lib/components/admin/Settings/ExternalKnowledge.svelte:293-298` | The test query returned documents, or returned none | Check the field names and the query | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Fill the required fields first.` | Error | `src/lib/components/admin/Settings/ExternalKnowledge.svelte:303-306`, `:339-342` | Create or save with the name or another required field empty | Fill in the fields | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Test the source before creating it.`; `Test the source before saving it.` | Error | `src/lib/components/admin/Settings/ExternalKnowledge.svelte:308-311`, `:344-347` | Create or save without a successful test since the last change; editing a field clears the test result (`:180-182`, `:407`, `:449`) | Run **Test** again first | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Knowledge source created.`; `Knowledge source updated.` | Success | `src/lib/components/admin/Settings/ExternalKnowledge.svelte:328`, `:364` | The source was stored and the list reloaded | None | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/admin/Settings/ExternalKnowledge.svelte:188`, `:192`, `:289`, `:323`, `:359`, `:393` | Loading the connections (`:188`) or the external knowledge bases (`:192`), **Test** (`:289`), create (`:323`), save (`:359`) or the on/off switch (`:393`) failed | Read the text | See `rag-retrieval-embeddings-and-vector-stores.md` section 10; server texts in `error-messages-backend-chat-content-and-features.md` section 10 |
| `External vectors must be generated with the same embedding model configured in Open WebUI.` | Inline (notice) | `src/lib/components/admin/Settings/ExternalKnowledge.svelte:757-763` | In the source window; upstream wording beside a licence comment | Admin decision | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `No external knowledge sources configured.`; `Test must pass before a source is created.` | Inline | `src/lib/components/admin/Settings/ExternalKnowledge.svelte:877-881`, `:883-887` | No external source exists yet | None | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Settings saved successfully!` | Success **(unchecked success)** | `src/lib/components/chat/SettingsModal.svelte:461` (via `:874`), triggered at `src/lib/components/admin/Settings/Documents.svelte:298` | After **Save** on **Documents**. Also shown when the embedding part was refused or skipped (its own message appears first and the rest is still saved, `:82-162`, `:239-241`), and when the final save failed without a server text (`src/lib/apis/retrieval/index.ts:86-91`). A refusal **with** a server text is not caught (`:264`) and shows nothing | Reopen the tab and check | See `admin-settings-panels.md` section 10 and 11.3 |
| `Model filesystem path detected. Model shortname is required for update, cannot continue.` | Error | `src/lib/components/admin/Settings/Documents.svelte:83-107` | The local embedding model is a path with more than one `/`, or the Ollama or OpenAI embedding model is empty. Only the embedding change is skipped; **Save** carries on with the rest | Enter a model name | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `OpenAI URL/Key required.` | Error | `src/lib/components/admin/Settings/Documents.svelte:109-115` | Embedding engine **Azure OpenAI** with its key, URL or API version empty (plain OpenAI is not checked here, despite the wording) | Fill in all three | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/admin/Settings/Documents.svelte:153` | Updating the embedding model was refused; the form reloads the stored embedding settings (`:154`) | Read the text | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `External Document Loader URL required.`; `Headers must be a valid JSON object`; `Tika Server URL required.`; `Docling Server URL required.`; `Invalid JSON format in Additional Config`; `Document Intelligence endpoint required.`; `Mistral OCR API Key required.`; `PaddleOCR-vl API URL required.`; `MinerU API Key required for Cloud API mode.` | Error | `src/lib/components/admin/Settings/Documents.svelte:165-237` | **Save** with the chosen content extraction engine missing its address or key, or with its JSON box invalid; nothing is saved | Fill in or correct the field | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Invalid JSON format in {{NAME}}` (`NAME` is `Docling Parameters`); `Invalid JSON format in MinerU Parameters` | Error | `src/lib/components/admin/Settings/Documents.svelte:243-262` | A parameters box is not valid JSON. These checks run **after** the embedding update (`:239-241`), so an embedding change may already be stored | Correct the JSON | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Confirm your action`; `This action cannot be undone. Do you wish to continue?` | Dialog (default texts) | `src/lib/components/admin/Settings/Documents.svelte:354-366`, `:368-380` | **Reset Upload Directory** (`:1556`) or **Reset Vector Storage/Knowledge** (`:1570`) | Confirm only if intended | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Reindex Embedding Data`; `Rebuild knowledge file, knowledge search, and memory vectors using the current embedding model.` | Dialog | `src/lib/components/admin/Settings/Documents.svelte:382-387` | **Reindex** under **Reindex Knowledge and Memory Vectors** (`:1586`) | Confirm | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Success` | Success | `src/lib/components/admin/Settings/Documents.svelte:363`, `:377`, `:413` | The upload directory was reset (`:363`); the vector storage reset was **started** (`:377`, **(unchecked success)**: it is not awaited, `:371`, so this appears at once and a red pop-up may follow); all three reindex steps finished (`:413`) | After a vector reset, watch for a red pop-up | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/admin/Settings/Documents.svelte:358`, `:372`, `:390`, `:399`, `:408` | Resetting the upload directory (`:358`) or the vector storage (`:372`) failed, or a reindex step failed (`:390`, `:399`, `:408`; later steps are skipped) | Escalate with the time | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `After changing the embedding model, reindex knowledge, knowledge search, and memory vectors for changes to take effect.` | Inline (notice) | `src/lib/components/admin/Settings/Documents.svelte:1167-1171` | Under the embedding model | Run **Reindex** after a model change | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Slim requires external services for embeddings, vector storage, and document extraction. Basic text files can be read locally.` | Inline (notice) | `src/lib/components/admin/Settings/Documents.svelte:427-433` | The server runs the slim image | Choose external services | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `This template contains multiple context placeholders ([context] or {{CONTEXT}}). Context will be injected at each occurrence.` | Inline (notice) | `src/lib/components/admin/Settings/Documents.svelte:1443-1449` | The RAG template holds more than one context placeholder | Check the template | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| (no text) | (silent on failure) | `src/lib/components/admin/Settings/Documents.svelte:322-351`, `:435` | Loading the tab has no error handling: a failure leaves the tab empty under its title | Reload | Escalate with the time |
| `Settings saved successfully!` | Success **(unchecked success)** | `src/lib/components/chat/SettingsModal.svelte:461` (via `:876`), triggered at `src/lib/components/admin/Settings/WebSearch.svelte:162-165` | After **Save** on **Web Search**. A refusal with a server text is not caught (`:101-107`) and shows nothing; a failure without one still shows this (`src/lib/apis/retrieval/index.ts:86-91`); an invalid **Linkup** parameters box stops with a script error and no message (`:95-99`) | Reopen the tab and check | See `admin-settings-panels.md` section 10 and `web-search-and-web-loading.md` section 10 |
| `Your query will be sent to the configured web search provider.` | Inline (placeholder) | `src/lib/components/admin/Settings/WebSearch.svelte:200-202` | The confirmation text box is empty while **Web Search Confirmation** is on; chats then show this default sentence | None | See `web-search-and-web-loading.md` section 10 |
| (no text) | (silent on failure) | `src/lib/components/admin/Settings/WebSearch.svelte:118-157`, `:172` | Loading the tab has no error handling: a failure leaves it empty | Reload | Escalate with the time |
| `Settings saved successfully!` | Success **(unchecked success)** | `src/lib/components/chat/SettingsModal.svelte:461` (via `:878`), triggered at `src/lib/components/admin/Settings/CodeExecution.svelte:41-44` | After **Save** on **Code Execution**; the answer is not checked (`:26-28`). A refusal with a server text stops before this with no message; a failure without one still shows it (`src/lib/apis/configs/index.ts:623-633`) | Reopen the tab and check | See `admin-settings-panels.md` section 10 and `code-execution-and-interpreter.md` section 10 |
| `Warning: Jupyter execution enables arbitrary code execution, posing severe security risks—proceed with extreme caution.` | Inline (warning) | `src/lib/components/admin/Settings/CodeExecution.svelte:64-71`, `:178-185`; English key `src/lib/i18n/locales/en-US/translation.json:3446` (the code writes the dash as `—`) | **Jupyter** chosen as the code execution or the code interpreter engine | Admin decision | See `code-execution-and-interpreter.md` section 10 |
| (no text) | (silent on failure) | `src/lib/components/admin/Settings/CodeExecution.svelte:30-36`, `:51` | Loading the tab has no error handling: a failure leaves it empty | Reload | Escalate with the time |

Field help in these panels (for example `Leave empty to use the default prompt, or enter a custom
prompt`, `src/lib/components/admin/Settings/CodeExecution.svelte:288`, or the Yandex JSON hint,
`src/lib/components/admin/Settings/WebSearch.svelte:1026`) is description text, not a message, and
is covered in the owning area documents.

### 10.8 `workspace/Models.svelte` and `workspace/Models/` (Workspace › Models and the Model Editor)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{error}` (server text) | Error | `src/lib/components/workspace/Models.svelte:167`, `:178`, `:189`, `:293`, `:306`, `:503` | Loading the list (`:167`) or the tags (`:178`), deleting a model (`:189`), **Export** of the selection (`:293`) or of one model (`:306`), or **Import** (`:503`) failed; the last three print the `detail` when there is one | Retry; reload | See `workspace-models-and-model-access.md` section 10; server texts in `error-messages-backend-chat-content-and-features.md` section 10 |
| `Deleted {{name}}` | Success | `src/lib/components/workspace/Models.svelte:194` | The model was deleted; `{{name}}` is its **ID**. Reached through **Delete** in the `...` menu and the default confirmation (`:465-470`, `:878`), or the bin icon while **Shift** is held, which deletes at once without a confirmation (`:815-845`) | None | See `workspace-models-and-model-access.md` section 10 |
| `Confirm your action`; `This action cannot be undone. Do you wish to continue?` | Dialog (default texts) | `src/lib/components/workspace/Models.svelte:465-470` | **Delete** in a model's `...` menu | Confirm only if intended | See `workspace-models-and-model-access.md` section 10 |
| `Model {{name}} is now {{status}}` | Success | `src/lib/components/workspace/Models.svelte:256-261` | **Hide Model** or **Show Model** was stored; `{{name}}` is the model ID and `{{status}}` the English word `hidden` or `visible`, which is not translated. A refusal is not caught (`:252`) and shows nothing | None | See `workspace-models-and-model-access.md` section 10 |
| `All models are now visible`; `All models are now hidden` | Success | `src/lib/components/workspace/Models.svelte:394`, `:414` | **Actions** › **Show All** or **Hide All** stored every model in the current search, across all pages (`:325-349`). If any single save fails (for example a model shared read-only), the run stops with no message at all (`:387-392`, `:407-412`) **(silent on failure)**; nothing happens when no model needs changing (`:380`, `:400`) | Reload and check | See `workspace-models-and-model-access.md` section 10 |
| `Redirecting you to Open WebUI Community` | Success | `src/lib/components/workspace/Models.svelte:225` | **Share** in the `...` menu, offered only with write access and community sharing on (`src/lib/components/workspace/Models/ModelMenu.svelte:184-190`): a new tab opens the upstream community site and the model's details are passed to it (`:221-241`). Upstream wording beside a licence comment | Follow local policy on public sharing (TO BE CONFIRMED) | See `workspace-models-and-model-access.md` section 10 |
| `Copied link to clipboard`; `Failed to copy link` | Success; Error | `src/lib/components/workspace/Models.svelte:280`, `:282` | **Copy Link**: the browser did or did not allow copying the `/?model={id}` address | Copy the address by hand | See `workspace-models-and-model-access.md` section 10 |
| `Invalid JSON file` | Error | `src/lib/components/workspace/Models.svelte:489`, `:494` | **Import** with a file that is not JSON (`:489`) or not a list (`:494`). A successful import shows **no** pop-up; the list simply reloads (`:507-515`) | Use a file exported from MedIT GPT | See `workspace-models-and-model-access.md` section 10 |
| `Read Only`; `No description`; `Deleted User` | Inline | `src/lib/components/workspace/Models.svelte:772-773`, `:783`, `:792`, `:802`, `:808` | The model is shared without write access; it has no description; or its owner account no longer exists | None | See `workspace-models-and-model-access.md` section 10 |
| `No models found`; `Try adjusting your search or filter to find what you are looking for.` | Inline | `src/lib/components/workspace/Models.svelte:931`, `:933` | The search, view or tag filter matches nothing, or loading failed (after the red pop-up) | Clear the search and filters | See `workspace-models-and-model-access.md` section 10 |
| (no text) | (silent on failure) | `src/lib/components/workspace/Models.svelte:351-375`, `:902-904`, `:315-323`, `:421` | **Enable All**, **Disable All** (`:351-375`) and a model's on/off switch (`:902-904`, sent without waiting) show nothing on success or failure; **Hide from Sidebar** / **Keep in Sidebar** saves the person's own settings without a message (`:315-323`); a failed group look-up when the page opens leaves the spinner (`:421`) | Reload and check | See `workspace-models-and-model-access.md` section 11 |
| `Model ID is required.`; `Model ID cannot contain whitespace.`; `Model Name is required.`; `Base Model is required.` | Error | `src/lib/components/workspace/Models/ModelEditor.svelte:290-316` | **Save & Create** or **Save & Update** with an empty ID, an ID containing a space, an empty name, or (for a Workspace model) no base model | Fill in the field | See `workspace-models-and-model-access.md` section 10 |
| `Please wait until all files are uploaded.` | Error | `src/lib/components/workspace/Models/ModelEditor.svelte:318-323` | Saving while a file in the model's knowledge block is still uploading | Wait, then save | See `workspace-models-and-model-access.md` section 10 |
| `Failed to upload background image.`; `Failed to save model` | Thrown, shown as Error | `src/lib/components/workspace/Models/ModelEditor.svelte:444`, `:449`, shown at `:473` | The chosen background picture could not be uploaded, or the page that hosts the editor reported the save as failed. On **Admin Settings** › **Models** that page has already shown its own `Failed to save model`, so the text appears twice (10.5) | Retry; note the time | See `workspace-models-and-model-access.md` section 10 and 11.22 |
| `{error.detail}` or `{error.message}` (server text) | Error | `src/lib/components/workspace/Models/ModelEditor.svelte:473` | Any other failure of the save, for example a background picture the server refused | Read the text | See `workspace-models-and-model-access.md` section 10; server texts in `error-messages-backend-chat-content-and-features.md` section 10 |
| `Background image must be PNG, JPEG, WebP, or GIF.`; `Background image must be at most 5 MiB.`; `Background image must be at most 25 megapixels.` | Error | `src/lib/components/workspace/Models/ModelEditor.svelte:911-929`, shown at `:935-939` | The chosen background picture has another type, is larger than 5 MiB, or has more than 25 million pixels | Choose a smaller PNG, JPEG, WebP or GIF | See `workspace-models-and-model-access.md` section 10 |
| `Invalid background image.` | Error | `src/lib/components/workspace/Models/ModelEditor.svelte:935-939` | Fallback when the picture check fails without a normal error; a picture the browser cannot decode usually shows the browser's own text instead (`:924`) | Choose another picture | See `workspace-models-and-model-access.md` section 10 |
| `You do not have permission to upload files.` | Error | `src/lib/components/workspace/Models/Knowledge.svelte:39-42` | A non-admin without the file upload permission tried to upload into the model's knowledge block | Ask an admin about the permission | See `workspace-models-and-model-access.md` section 10 and `users-groups-roles-and-permissions.md` |
| `You cannot upload an empty file.` | Error | `src/lib/components/workspace/Models/Knowledge.svelte:59-62` | The chosen file has zero bytes | Choose another file | See `files-uploads-and-storage.md` section 10 |
| `File size should not exceed {{maxSize}} MB.` | Error | `src/lib/components/workspace/Models/Knowledge.svelte:121-135` | The file is larger than the maximum upload size (`file.max_size`) | Use a smaller file | See `files-uploads-and-storage.md` section 10 |
| `Unsupported file type.` | Error | `src/lib/components/workspace/Models/Knowledge.svelte:137-141` | A picture was chosen; the knowledge block accepts no `image/` files | Use a document | See `workspace-models-and-model-access.md` section 10 |
| `File not found.` | Error | `src/lib/components/workspace/Models/Knowledge.svelte:160-166` | The file picker closed without a file | Choose a file | See `files-uploads-and-storage.md` section 10 |
| `{uploadedFile.error}` (server text) | Warning | `src/lib/components/workspace/Models/Knowledge.svelte:88-91` | The file was stored but its processing reported a problem, for example no text could be extracted | Check the file; it may add nothing to answers | See `files-uploads-and-storage.md` section 10 |
| `{e}` (server text) | Error | `src/lib/components/workspace/Models/Knowledge.svelte:104-105` | The upload was refused; the file is removed from the block. A failure without a server text removes it with no message (`:101-103`) | Retry | See `files-uploads-and-storage.md` section 10; server texts in `error-messages-backend-chat-content-and-features.md` section 10 |
| `Invalid JSON file` | Error | `src/lib/components/workspace/Models/PromptSuggestions.svelte:72-102` | Importing prompt suggestions from a file that is not a list of suggestions with text `content` | Use a file exported from this block | See `workspace-models-and-model-access.md` section 10 |
| `No suggestion prompts` | Inline | `src/lib/components/workspace/Models/PromptSuggestions.svelte:224-227` | The model has no prompt suggestions | None | See `workspace-models-and-model-access.md` section 10 |
| `No actions found`; `No filters found`; `No skills found`; `No tools found`; `No knowledge found` | Inline | `src/lib/components/workspace/Models/ActionsSelector.svelte:49`; `FiltersSelector.svelte:49`; `DefaultFiltersSelector.svelte:43`; `SkillsSelector.svelte:41`; `ToolsSelector.svelte:41`; `Knowledge/KnowledgeSelector.svelte:141` | The picker has nothing to offer. The knowledge picker also shows its text when its searches fail, which it does silently (`Knowledge/KnowledgeSelector.svelte:55`, `:72`, `:87`) | None | See `workspace-models-and-model-access.md` section 10 |

The other files in `src/lib/components/workspace/Models/` (`BuiltinTools.svelte`,
`Capabilities.svelte`, `DefaultFeatures.svelte`, `LocalizedPromptSuggestions.svelte`,
`ModelMenu.svelte`, `TTSVoiceInput.svelte`, `TerminalSelector.svelte`, `TypeaheadSelector.svelte`)
have labels and descriptions only.

### 10.9 `workspace/Knowledge.svelte` and `workspace/Knowledge/` (Workspace › Knowledge and One Knowledge Base)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Knowledge deleted successfully.` | Success | `src/lib/components/workspace/Knowledge.svelte:186` | **Delete** in a knowledge base's `...` menu (`:516`), confirmed in the default dialog (`:297-302`) | None | See `knowledge-bases.md` section 10 |
| `Confirm your action`; `This action cannot be undone. Do you wish to continue?` | Dialog (default texts) | `src/lib/components/workspace/Knowledge.svelte:297-302` | **Delete** on a knowledge base | Confirm only if intended | See `knowledge-bases.md` section 10 |
| `Knowledge exported successfully` | Success | `src/lib/components/workspace/Knowledge.svelte:211` | **Export** downloaded the knowledge base as a `.zip` file (`:199-212`) | None | See `knowledge-bases.md` section 10 |
| `{e}` (server text) | Error | `src/lib/components/workspace/Knowledge.svelte:182`, `:214` | Deleting (`:182`) or exporting (`:214`) failed | Retry | See `knowledge-bases.md` section 10; server texts in `error-messages-backend-chat-content-and-features.md` section 10 |
| `Only collections can be edited, create a new knowledge base to edit/add documents.` | Error | `src/lib/components/workspace/Knowledge.svelte:218-226` | Opening an old single-document entry (`meta.document`) instead of a collection | Create a new knowledge base | See `knowledge-bases.md` section 10 |
| `Read Only`; `Deleted User` | Inline | `src/lib/components/workspace/Knowledge.svelte:461`, `:465`, `:494`, `:500` | The knowledge base is shared without write access; its owner account no longer exists | None | See `knowledge-bases.md` section 10 |
| `No knowledge found`; `Try adjusting your search or filter to find what you are looking for.` | Inline | `src/lib/components/workspace/Knowledge.svelte:543-546` | Nothing matches the search or filters. **(silent on failure)**: a failed load is swallowed (`:141-149`), so it shows the same text | Clear the search; reload | See `knowledge-bases.md` section 10 |
| `Please fill in all fields.` | Error | `src/lib/components/workspace/Knowledge/CreateKnowledgeBase.svelte:31-37` | **Create Knowledge** with the name or the description empty; **both** boxes are then cleared (`:33-34`) | Type both again | See `knowledge-bases.md` section 10 |
| `{e}` (server text) | Error | `src/lib/components/workspace/Knowledge/CreateKnowledgeBase.svelte:39-43` | Creating the knowledge base was refused | Read the text | See `knowledge-bases.md` section 10 |
| `Knowledge created successfully.` | Success | `src/lib/components/workspace/Knowledge/CreateKnowledgeBase.svelte:46` | The knowledge base was created | Add content | See `knowledge-bases.md` section 10 |
| `{e}` (server text) | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1116`, `:286`, `:359`, `:395`, `:451`, `:476`, `:702`, `:774`, `:818`, `:832`, `:856`, `:874`, `:889`, `:913`, `:925`, `:951`, `:987` | Opening the knowledge base failed (`:1116`; the page returns to the list, `:1126-1128`), or one action was refused: the external test query (`:286`), adding a webpage (`:359`, `:395`), uploading a file (`:451`, `:476`), a directory upload or sync (`:702`, `:774`), creating, renaming, deleting or moving a directory (`:818`, `:832`, `:856`, `:889`), moving, removing or renaming a file (`:874`, `:913`, `:925`), saving edited file content (`:951`) or saving the name and description (`:987`) | Read the text | See `knowledge-bases.md` section 10; server texts in `error-messages-backend-chat-content-and-features.md` section 10 |
| `Failed to load file content.` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:266-269` | Opening a file to read or edit its text failed | Retry | See `knowledge-bases.md` section 10 |
| `Knowledge base not found.` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:304-306` | **Add webpage** before the knowledge base finished loading | Wait and retry | See `knowledge-bases.md` section 10 |
| `{uploadedFile.error}` (server text) | Warning | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:376-379`, `:464-467` | A webpage or file was stored but its processing reported a problem; the item is taken off the list on screen | Check the file; see the knowledge document | See `knowledge-bases.md` section 10 |
| `File added successfully.` | Success | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:381`, `:469` | A webpage (`:381`) or a file, including **Add text content** (`:469`), was stored and processed | None | See `knowledge-bases.md` section 10 |
| `Failed to upload file.` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:385`, `:473` | A webpage's text could not be stored or linked (`:385`), or a file upload returned nothing (`:473`; a refusal shows the server text first, `:451`) | Retry | See `knowledge-bases.md` section 10 |
| `Failed to process URL: {{url}}` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:387-391` | **Add webpage**: reading the address returned nothing | Check the address opens in a browser | See `knowledge-bases.md` section 10 and `web-search-and-web-loading.md` |
| `You cannot upload an empty file.`; `File size should not exceed {{maxSize}} MB.` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:415-418`, `:420-434` | The file has zero bytes, or is larger than the maximum upload size (`file.max_size`) | Choose another or a smaller file | See `knowledge-bases.md` section 10 |
| `Directory selection was cancelled` | Info | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:494-495` | **Upload directory** or **Sync directory**: the folder picker was closed | None | See `knowledge-bases.md` section 10 |
| `Error accessing directory: {error.message}` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:496-497` | The browser could not read the chosen folder; the second part is the browser's own text | Try another browser or folder | See `knowledge-bases.md` section 10 |
| `Upload failed for {{failed}} of {{total}} files.` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:654-660` | Some files of a directory upload or sync failed; the reasons go only to the browser console (`:642-651`). In a sync, the old copies of changed files were removed before the uploads (`:733-742`), so a changed file that failed is now missing | Retry the failed files one by one to see each reason | See `knowledge-bases.md` section 10 and 11 |
| `Failed to compare files.` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:685-687`, `:728-730` | The server returned no comparison for a directory upload or sync | Retry; escalate | See `knowledge-bases.md` section 10 |
| `File uploaded successfully` | Success | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:696-697` | Every file of a directory upload succeeded | None | See `knowledge-bases.md` section 10 |
| `Sync complete: {{added}} added, {{modified}} modified, {{deleted}} deleted, {{unmodified}} unmodified` | Success | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:759-770` | **Sync directory** finished with no failed upload | Compare the counts with the folder | See `knowledge-bases.md` section 10 |
| `Confirm your action`; `{{count}} files selected. Only new and modified files will be uploaded. Deleted files will be removed. The folder structure will be mirrored. Continue?` | Dialog (default title) | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1158-1168` | A folder was chosen for **Sync directory** (`:1464`) | Confirm only if the folder is the right one: files missing from it are removed | See `knowledge-bases.md` section 10 |
| `Directory created.`; `Directory renamed.`; `Directory deleted.`; `Directory moved.`; `File moved.` | Success | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:823`, `:837`, `:861`, `:894`, `:879` | The directory or file action was stored | None | See `knowledge-bases.md` section 10 |
| `File removed successfully.`; `File renamed.`; `File content updated successfully.` | Success | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:908`, `:921`, `:956` | The file was removed from the knowledge base, renamed, or its edited text saved (`:1668`) | None | See `knowledge-bases.md` section 10 |
| `Please fill in all fields.` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:976-978` | The name or description at the top was emptied; these save automatically one second after typing stops (`:969-994`) | Type both | See `knowledge-bases.md` section 10 |
| `Knowledge updated successfully` | Success | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:991` | The automatic save of the name and description succeeded | None | See `knowledge-bases.md` section 10 |
| `You do not have permission to upload files to this knowledge base.` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1067-1069` | Files were dropped onto a knowledge base shared without write access | Ask the owner for write access | See `knowledge-bases.md` section 10 |
| `File not found.` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1107`, `:1213` | A drop (`:1107`) or the file picker (`:1213`) delivered no file | Choose the files again | See `knowledge-bases.md` section 10 |
| `Saved`; `{error}` (server text) | Success; Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1232`, `:1234` | The sharing window stored the knowledge base's access, or the change was refused | Read the text | See `knowledge-bases.md` section 10 and `users-groups-roles-and-permissions.md` |
| `ID copied to clipboard` | Success **(unchecked success)** | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1308-1314` | Clicking the knowledge base ID; shown without checking that the browser allowed the copy | Paste to confirm | See `knowledge-bases.md` section 10 |
| `Read Only`; `Not configured` | Inline | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1289`, `:1335`, `:1349` | No write access; an external knowledge base without a mapped source name | None | See `knowledge-bases.md` section 10 |
| `This knowledge base retrieves from a connected source. Open WebUI can query it, but cannot upload, sync, edit, delete, reset, or reindex its source data.` | Inline (notice) | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1361-1366` | An external knowledge base (set up under **Admin Settings** › **Integrations**, 10.7); upstream wording beside a licence comment | None | See `knowledge-bases.md` section 10 |
| `No content found` | Inline | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1606-1613` | The opened file has no extracted text | Check the original file | See `knowledge-bases.md` section 10 |
| `Delete directory?`; `Are you sure you want to delete this directory?`; `Delete all contents inside this directory` | Dialog | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1708-1729` | **Delete** on a directory (`:844`); with the box unticked the files are kept and moved to the parent directory (`:1712`; `backend/open_webui/routers/knowledge.py:2329`) | Tick the box only to delete the files too | See `knowledge-bases.md` section 10 |
| `Reset knowledge base?`; `This will remove all files and directories from this knowledge base. This action cannot be undone.` | Dialog | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1731-1745` | **Reset** in the **Add Content** menu (`:1468`) | Confirm only if intended | See `knowledge-bases.md` section 10 |
| `Knowledge base has been reset` | Success | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1736` | The reset succeeded. A refusal is not caught (`:1735`), so it shows nothing | Reload and check | See `knowledge-bases.md` section 10 |
| `Failed to add file.` | Error, **never displayed** | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:780-798` | Its handler is never called in this file (section 14) | None | See `knowledge-bases.md` section 10 |
| `Please fill in all fields.` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase/AddTextContentModal.svelte:38-43` | **Add text content** with the title or the text empty | Fill in both | See `knowledge-bases.md` section 10 |
| `Permission denied when accessing microphone: {{error}}`; `Permission denied when accessing microphone` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase/AddTextContentModal.svelte:103-112`, `:120-121` | **Voice Input** in that window: the browser refused the microphone (the first, with the browser's reason), or offers no microphone access at all (the second) | Allow the microphone in the browser | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Name is required` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase/NewDirectoryModal.svelte:19-22` | **New directory** with an empty name | Type a name | See `knowledge-bases.md` section 10 |
| `Sync a local directory with this knowledge base. Only new and modified files will be uploaded. The directory structure will be mirrored.` | Inline (tooltip) | `src/lib/components/workspace/Knowledge/KnowledgeBase/AddContentMenu.svelte:95-99` | Hovering **Sync directory** | None | See `knowledge-bases.md` section 10 |

Progress lines shown while a folder is uploaded or synced (`Computing checksums ({{count}} files)`,
`Comparing with knowledge base...`, `Uploading {{current}}/{{total}}: {{file}}`, `Removing {{count}}
stale files...`, `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:629-633`, `:670`,
`:673`, `:714-716`, `:721`, `:740`) are status, not messages. `ItemMenu.svelte`,
`KnowledgeBase/DirectoryRow.svelte`, `KnowledgeBase/Files.svelte` (which shows `Deleted User` for a
file whose owner is gone, `:182`, `:189`) and `KnowledgeBase/KnowledgeBreadcrumbs.svelte` have no
other text of note.

### 10.10 `workspace/Prompts.svelte`, `workspace/Prompts/`, `workspace/Skills.svelte` and `workspace/Skills/` (Prompts and Skills)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{error}` (server text) | Error | `src/lib/components/workspace/Prompts.svelte:184`, `:195`, `:113`, `:251`, `:296` | Loading the list (`:184`) or the tags (`:195`), **Export JSON** (`:113`), creating a prompt in the create window (`:251`) or deleting one (`:296`) failed | Retry | See `prompts-and-skills.md` section 10; server texts in `error-messages-backend-chat-content-and-features.md` section 10 |
| `Prompt created successfully` | Success | `src/lib/components/workspace/Prompts.svelte:256` | The create window stored the new prompt | None | See `prompts-and-skills.md` section 10 |
| `Deleted {{name}}` | Success | `src/lib/components/workspace/Prompts.svelte:301` | The prompt was deleted; `{{name}}` is its command. Reached through **Delete** and the dialog below (`:693`), or the bin icon while **Shift** is held, which deletes at once (`:641-650`) | None | See `prompts-and-skills.md` section 10 |
| `Delete prompt?`; `This will delete {command}.` | Dialog | `src/lib/components/workspace/Prompts.svelte:378-388` | **Delete** in a prompt's `...` menu | Confirm only if intended | See `prompts-and-skills.md` section 10 |
| `Redirecting you to Open WebUI Community` | Success | `src/lib/components/workspace/Prompts.svelte:210` | **Share** in the `...` menu, offered when community sharing is on (`src/lib/components/workspace/Prompts/PromptMenu.svelte:70-75`); opens the upstream community site in a new tab | Follow local policy on public sharing (TO BE CONFIRMED) | See `prompts-and-skills.md` section 10 |
| `{error}` (server text, or the error written out as JSON) | Error | `src/lib/components/workspace/Prompts.svelte:431` | **Import JSON**: one prompt of the file was refused; a refusal that is not plain text is printed as raw JSON (`:428-432`). A successful import shows **no** pop-up, and a file that is not valid JSON stops with no message (`:421`) **(silent on failure)** | Check the list after an import | See `prompts-and-skills.md` section 10 |
| `Read Only`; `Deleted User` | Inline | `src/lib/components/workspace/Prompts.svelte:607`, `:628`, `:634` | Shared without write access; the owner account no longer exists | None | See `prompts-and-skills.md` section 10 |
| `No prompts found`; `Try adjusting your search or filter to find what you are looking for.` | Inline | `src/lib/components/workspace/Prompts.svelte:750`, `:752` | The search or filter matches nothing, or loading failed (after the red pop-up) | Clear the search and filters | See `prompts-and-skills.md` section 10 |
| (no text) | (silent on failure) | `src/lib/components/workspace/Prompts.svelte:729`, `:282-290` | A prompt's on/off switch is sent without waiting and without error handling (`:729`); **Copy** shows only a brief tick, no pop-up (`:282-290`) | Reload to see the stored state | See `prompts-and-skills.md` section 11 |
| `You do not have permission to edit this prompt.` | Error | `src/lib/components/workspace/Prompts/PromptEditor.svelte:83-85`, `:178-180` | Saving (`:83-85`) or **Set as Production** (`:178-180`) on a prompt shared without write access | Ask the owner for write access | See `prompts-and-skills.md` section 10 |
| `Only alphanumeric characters and hyphens are allowed in the command string.` | Error | `src/lib/components/workspace/Prompts/PromptEditor.svelte:112-116`, `:232-238` | Saving, or the automatic save of the name, command and tags (500 ms after typing stops, `:224-259`), with a command containing characters other than letters, digits, `-` and `_` (`:121-124`); the automatic save restores the previous command (`:236`) | Use letters, digits and hyphens | See `prompts-and-skills.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/workspace/Prompts/PromptEditor.svelte:110`, `:195`, `:212`, `:254`, `:309` | Saving the prompt (`:110`), **Set as Production** (`:195`), deleting a version (`:212`), the automatic metadata save (`:254`; the name, command and tags are restored, typically after a command already in use) or the sharing change (`:309`) was refused | Read the text; choose another command | See `prompts-and-skills.md` section 10 |
| `Saved` | Success | `src/lib/components/workspace/Prompts/PromptEditor.svelte:252`, `:307` | The automatic save of the name, command and tags (`:252`) or a sharing change (`:307`) was stored | None | See `prompts-and-skills.md` section 10 |
| `Production version updated`; `Version deleted` | Success | `src/lib/components/workspace/Prompts/PromptEditor.svelte:193`, `:204` | A history version was made the live one, or deleted | None | See `prompts-and-skills.md` section 10 |
| `ID copied to clipboard` | Success **(unchecked success)** | `src/lib/components/workspace/Prompts/PromptEditor.svelte:465-470` | Clicking the prompt ID; shown without checking that the copy worked | Paste to confirm | See `prompts-and-skills.md` section 10 |
| `Read Only`; `No history available` | Inline | `src/lib/components/workspace/Prompts/PromptEditor.svelte:441`, `:735-738` | No write access; the prompt has no saved versions yet (or loading them failed) | None | See `prompts-and-skills.md` section 10 |
| `Only alphanumeric characters and hyphens are allowed - Activate this command by typing "/{{COMMAND}}" to chat input.` | Inline (tooltip) | `src/lib/components/workspace/Prompts/PromptEditor.svelte:574` | Hovering the command box (two keys joined with ` - `) | None | See `prompts-and-skills.md` section 10 |
| `Delete Version`; `Are you sure you want to delete this version? Child versions will be relinked to this version's parent.` | Dialog | `src/lib/components/workspace/Prompts/PromptHistoryMenu.svelte:21-31` | **Delete** in a history version's menu | Confirm only if intended | See `prompts-and-skills.md` section 10 |
| `Cannot delete the production version` | Inline (tooltip) | `src/lib/components/workspace/Prompts/PromptHistoryMenu.svelte:54-62` | Hovering the greyed-out **Delete** of the live version | Make another version live first | See `prompts-and-skills.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/workspace/Skills.svelte:120`, `:92`, `:178`, `:194`, `:208`, `:292` | Loading the list (`:120`), **Export** of all skills (`:92`), **Clone** (`:178`), **Export** of one (`:194`), **Delete** (`:208`) or one entry of an **Import** file (`:292`) failed | Retry | See `prompts-and-skills.md` section 10; server texts in `error-messages-backend-chat-content-and-features.md` section 10 |
| `Skill deleted successfully` | Success | `src/lib/components/workspace/Skills.svelte:213` | Deleted after `Delete skill?` (`:553`), or at once with the **Shift**-key bin (`:523-534`) | None | See `prompts-and-skills.md` section 10 |
| `Delete skill?`; `This will delete {name}.` | Dialog | `src/lib/components/workspace/Skills.svelte:618-630` | **Delete** in a skill's `...` menu; `{name}` is the skill's name in the interface language | Confirm only if intended | See `prompts-and-skills.md` section 10 |
| `Skill imported successfully` | Success **(unchecked success)** | `src/lib/components/workspace/Skills.svelte:296` | End of a `.json` **Import**, shown even when every entry failed (each failure shows its own pop-up first, `:290-294`). A `.md` file is not imported directly: it opens the create page with the file's content (`:305-327`) | Check the list | See `prompts-and-skills.md` section 10 |
| `Invalid JSON file` | Error | `src/lib/components/workspace/Skills.svelte:300-302` | A `.json` import file that cannot be read as JSON | Use a file exported from MedIT GPT | See `prompts-and-skills.md` section 10 |
| `Read Only`; `Deleted User`; `No skills found`; `Try adjusting your search or filter to find what you are looking for.` | Inline | `src/lib/components/workspace/Skills.svelte:484`, `:509`, `:515`, `:609`, `:611` | As for prompts | None | See `prompts-and-skills.md` section 10 |
| (no text) | (silent on failure) | `src/lib/components/workspace/Skills.svelte:587` | A skill's on/off switch is sent without waiting and without error handling | Reload to see the stored state | See `prompts-and-skills.md` section 11 |
| `You do not have permission to edit this skill.` | Error | `src/lib/components/workspace/Skills/SkillEditor.svelte:52-56` | Saving a skill shared without write access | Ask the owner for write access | See `prompts-and-skills.md` section 10 |
| (no text) | (silent on failure) | `src/lib/components/workspace/Skills/SkillEditor.svelte:58-62` | Saving with an empty name: the editor switches back to the base language and stops without a message | Type a name | See `prompts-and-skills.md` section 11 |
| `Saved`; `{error}` (server text) | Success; Error | `src/lib/components/workspace/Skills/SkillEditor.svelte:105`, `:107` | The sharing window stored the skill's access, or the change was refused | Read the text | See `prompts-and-skills.md` section 10 |
| `Read Only` | Inline | `src/lib/components/workspace/Skills/SkillEditor.svelte:187` | The skill is shared without write access | None | See `prompts-and-skills.md` section 10 |

`src/lib/components/workspace/Prompts/PromptMenu.svelte` and
`src/lib/components/workspace/Skills/SkillMenu.svelte` have labels only. The "created" and
"updated" pop-ups of the prompt and skill create and edit pages are shown by the route pages (see
`error-messages-frontend-chat-and-navigation.md` section 10.15).

### 10.11 `workspace/Tools.svelte` and `workspace/Tools/` (Workspace › Tools and the Tool Editor)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{error}` (server text) | Error | `src/lib/components/workspace/Tools.svelte:107`, `:187`, `:214`, `:230`, `:244`, `:676` | **Export JSON** (`:107`), **Share** (`:187`), **Clone** (`:214`), **Export** of one tool (`:230`), **Delete** (`:244`) or one entry of an **Import** file (`:676`) failed | Retry | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10; server texts in `error-messages-backend-chat-content-and-features.md` section 10 |
| `Tool deleted successfully` | Success | `src/lib/components/workspace/Tools.svelte:249` | Deleted after `Delete tool?` (`:599`), or at once with the bin icon while **Shift** is held (`:515-524`) | None | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Delete tool?`; `This will delete {name}.` | Dialog | `src/lib/components/workspace/Tools.svelte:645-656` | **Delete** in a tool's `...` menu; `{name}` is the tool's name in the interface language | Confirm only if intended | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Redirecting you to Open WebUI Community` | Success | `src/lib/components/workspace/Tools.svelte:194` | **Share**, offered when community sharing is on (`src/lib/components/workspace/Tools/ToolMenu.svelte:71-76`): a new tab opens the upstream community site and the tool's details, including its code, are passed to it (`:185-210`). Shown even when reading the tool failed | Follow local policy on public sharing (TO BE CONFIRMED) | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Confirm your action`; `Please carefully review the following warnings:`; `Tools have a function calling system that allows arbitrary code execution..`; `Do not install tools from sources you do not fully trust.`; `I acknowledge that I have read and I understand the implications of my action. I am aware of the risks associated with executing arbitrary code and I have verified the trustworthiness of the source.` | Dialog (default title, warning text) | `src/lib/components/workspace/Tools.svelte:666-713` (texts `:692-704`) | A file was chosen with **Import** (`:330`). The second sentence ends in two full stops on this screen, because the markup adds one after the translated text (`:696`) | Confirm only for reviewed code | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Tool imported successfully` | Success **(unchecked success)** | `src/lib/components/workspace/Tools.svelte:681` | End of an **Import** run, shown even when every entry failed (each failure shows its own pop-up first, `:674-679`). A file that is not valid JSON stops with no message at all (`:670`) **(silent on failure)** | Check the list | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Read Only`; `Deleted User` | Inline | `src/lib/components/workspace/Tools.svelte:476`, `:501`, `:507` | Shared without write access; the owner account no longer exists | None | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `No tools found`; `Try adjusting your search or filter to find what you are looking for.` | Inline | `src/lib/components/workspace/Tools.svelte:628`, `:630` | The search or view filter matches nothing | Clear the search and filters | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| (no text) | (silent on failure) | `src/lib/components/workspace/Tools.svelte:254-261` | Loading the list has no error handling: a failure leaves the spinner | Reload | Escalate with the time |
| `Name and description are required` | Error | `src/lib/components/workspace/Tools/ToolkitEditor.svelte:167-172` | **Save** or **Save & Create** with the name or description empty after trimming; the editor switches back to the base language (`:169`). Unlike the function editor (10.3) this file imports the pop-up library, so the message does appear | Type a name and description | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Saved`; `{error}` (server text) | Success; Error | `src/lib/components/workspace/Tools/ToolkitEditor.svelte:219`, `:221` | The sharing window stored the tool's access (existing tools only, `:216`), or the change was refused | Read the text | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Warning:`; `Tools can execute arbitrary code.`; `Only install tools from sources you trust.` | Inline (warning) | `src/lib/components/workspace/Tools/ToolkitEditor.svelte:357-363` | Footer of the code editor, always shown | None | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Confirm your action` and the four warning and acknowledgement texts (here the second sentence has one full stop) | Dialog | `src/lib/components/workspace/Tools/ToolkitEditor.svelte:380-404` | **Save & Create** on a new tool (`:231-237`); saving an existing tool skips the dialog | Confirm only for reviewed code | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 (the warnings) and `functions-pipes-filters-actions-and-pipelines.md` section 10 (`Confirm your action`) |
| `API key is not set in the environment variable 'OPENWEATHER_API_KEY'.`; `Invalid equation`; `Error fetching weather data: {message}` | Tool result (in a chat reply, not in the editor) | `src/lib/components/workspace/Tools/ToolkitEditor.svelte:137-141`, `:124`, `:155`, `:164` | Texts of the starter code (`:60-165`). A tool saved from the starter unchanged and attached to a model returns them to the model, which may repeat them in its answer | Escalate to the tool's owner | Not catalogued elsewhere; established from the code |

`src/lib/components/workspace/Tools/ToolMenu.svelte` has labels only; `AddToolMenu.svelte` is not imported by any file in `src/`, so its labels never appear. The
create and edit pages that show `Tool created successfully` and `Tool updated successfully` are
route pages (see `error-messages-frontend-chat-and-navigation.md` section 10.15).

### 10.12 `workspace/common/` (Sharing, Member Picker, Valves, Support Window, Translations)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Valves updated successfully` | Success | `src/lib/components/workspace/common/ValvesModal.svelte:96-98` | **Save** in a valves window stored the values: an admin's valves for a function (10.3) or tool (10.11), or a person's own valves | None | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/workspace/common/ValvesModal.svelte:75`, `:80`, `:87`, `:91` | Saving a person's own valves for a tool (`:75`) or function (`:80`), or an admin's valves for a tool (`:87`) or function (`:91`), was refused, for example a value of the wrong type | Correct the value | See `functions-pipes-filters-actions-and-pipelines.md` section 10 (10.1 and 10.3); `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Error fetching valves` (untranslated) | Error | `src/lib/components/workspace/common/ValvesModal.svelte:151-153` | Loading the valves or their definition failed; the window closes | Retry; escalate | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `Failed to load valves` with **Retry** | Inline (red line) | `src/lib/components/workspace/common/PluginTranslations.svelte:59-63` | The translation view of the function or tool editor could not read one of the two valve definitions (`:32-40`) | Press **Retry** | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `You do not have permission to make this public` | Inline (tooltip) | `src/lib/components/workspace/common/AccessControl.svelte:518-522` | The item is private and the person lacks the sharing or public-sharing permission for this item type | Ask an admin about sharing permissions | See `users-groups-roles-and-permissions.md` section 10 |
| `Only select users and groups with permission can access`; `Accessible to all users`; `Anyone with the link can view` | Inline (help) | `src/lib/components/workspace/common/AccessControl.svelte:541-548` | Under the visibility choice: **Private**, **Public** or **Open** | None | See `users-groups-roles-and-permissions.md` section 10 |
| `No access grants. Private to you.` | Inline | `src/lib/components/workspace/common/AccessControl.svelte:698-702` | Private, with no group and no person added | Add people or groups if sharing was intended | See `users-groups-roles-and-permissions.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/workspace/common/MemberSelector.svelte:61-67` | Searching for people in the member picker (also used by channels) failed | Retry | See `users-groups-roles-and-permissions.md` section 10 |
| `No users were found.` | Inline | `src/lib/components/workspace/common/MemberSelector.svelte:317-320` | The search matched no account, or it failed (after the red pop-up) | Check the spelling | See `users-groups-roles-and-permissions.md` section 10 |
| `Only invited users can access`; `Visible to all users` | Inline (help) | `src/lib/components/workspace/common/Visibility.svelte:45-50` | The **Private** or **Public** choice of the visibility selector, which only the channel window uses (`src/lib/components/layout/Sidebar/ChannelModal.svelte:18`) | None | See `users-groups-roles-and-permissions.md` section 10 and `channels-and-direct-messages.md` |
| `Show your support!`; `The developers behind this plugin are passionate volunteers from the community. If you find this plugin helpful, please consider contributing to its development.`; `Your entire contribution will go directly to the plugin developer; Open WebUI does not take any percentage. However, the chosen funding platform might have its own fees.`; `Support this plugin:` | Inline (window) | `src/lib/components/workspace/common/ManifestModal.svelte:19`, `:40-42`, `:46-51`, `:56` | The heart icon of a function or tool whose code declares a funding link; upstream wording beside a licence comment | None: the link leads to an outside site; follow local policy (TO BE CONFIRMED) | See `functions-pipes-filters-actions-and-pipelines.md` section 12 and `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |

`AccessControlModal.svelte`, `AddAccessModal.svelte`, `CommunityDiscover.svelte` (the **Made by Open
WebUI Community** link shown when community sharing is on), `TagSelector.svelte` and
`ViewSelector.svelte` in `src/lib/components/workspace/common/` have labels only. The look-ups
inside `AccessControl.svelte` that fill in names of people and groups already granted access drop
their errors (`:337`, `:387`, `:459`), so a failure only leaves a name missing.

### 10.13 `chat/Settings/`: General, Interface, Shortcuts, Connections, Integrations, Audio and Advanced Parameters

Every personal tab stores its values through the Settings window's own save function, which shows
a red `{error}` pop-up when the server refuses (`src/lib/components/chat/SettingsModal.svelte:439-450`;
see [`error-messages-frontend-chat-and-navigation.md`](error-messages-frontend-chat-and-navigation.md)
section 10.1). The rows below say, per tab, when the green pop-up appears.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Settings saved successfully!` | Success | `src/lib/components/chat/SettingsModal.svelte:796`, after `src/lib/components/chat/Settings/General.svelte:122-128` | **Save** on **General** stored the system prompt and the advanced parameters (`:77-128`); when the server refuses, the window's red pop-up appears instead and this one is skipped (`:126-128`) | None | See `user-settings-and-personalisation.md` section 10 |
| `Couldn't find your language?` with `Help us translate Open WebUI!` | Inline (link) | `src/lib/components/chat/Settings/General.svelte:264-277` | The interface is in English (US) and no licence data is loaded; the link opens the upstream translation guide | None | See `user-settings-and-personalisation.md` section 10 |
| `Settings saved successfully!` | Success | `src/lib/components/chat/SettingsModal.svelte:804`, after `src/lib/components/chat/Settings/Interface.svelte:17-20` | **Save** on **Interface**, once the shared Interface settings component has finished its own save (`:18`); that component's messages are catalogued in `error-messages-frontend-chat-and-navigation.md` section 10.11 | None | See `user-settings-and-personalisation.md` section 10 |
| `Default action buttons will be used.` | Inline | `src/lib/components/chat/Settings/Interface/ManageFloatingActionButtonsModal.svelte:124-128` | The **Quick Actions** window has no custom buttons | None | See `user-settings-and-personalisation.md` section 10 |
| (no text) | (silent on failure) | `src/lib/components/chat/Settings/Shortcuts.svelte:63-75`, `:135` | Recording a new shortcut or **Reset Defaults** stores the key bindings with no message either way: the request has no error handling (`:65`, `:75`). The **Enable Keyboard Shortcuts** switch saves through the window, which reports only a refusal (`:135`) | Reload the page and check the shortcut | See `user-settings-and-personalisation.md` section 11 |
| `Press keys...`; `Unassigned`; `Also bound to {{action}}` | Inline | `src/lib/components/chat/Settings/Shortcuts.svelte:216-221`, `:230-236`, `:239-245` | Recording a shortcut; an action with no keys; the tooltip of the amber `!` beside keys that another action also uses | Choose other keys | See `user-settings-and-personalisation.md` section 10 |
| `Settings saved successfully!` | Success | `src/lib/components/chat/SettingsModal.svelte:812-816`, after `src/lib/components/chat/Settings/Connections.svelte:52-54` | A personal (direct) connection was added, edited or deleted, or **Save** pressed, and the list was stored; a refusal shows the red pop-up instead | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Connections managed through the Admin Panel are recommended for everyday use. Direct connections provide convenient access to your own endpoints, but rely on your browser session to keep requests running, making them better suited to testing and temporary use.`; `CORS must be properly configured by the provider to allow requests from Open WebUI.` | Inline (notice) | `src/lib/components/chat/Settings/Connections.svelte:139-150`; `src/lib/components/chat/Settings/Integrations.svelte:171-182` | Under the personal connection list and the personal tool server list; upstream wording beside a licence comment | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `WebUI will make requests to "{{url}}/chat/completions"` | Inline (tooltip) | `src/lib/components/chat/Settings/Connections/Connection.svelte:46-48` | Hovering a personal connection's address | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Settings saved successfully!` | Success | `src/lib/components/chat/SettingsModal.svelte:819-823`, after `src/lib/components/chat/Settings/Integrations.svelte:44-47` | A personal tool server or terminal server was added, edited, deleted or switched (`:163`), or **Save** pressed: shown once the list is stored, **before** the servers are contacted | Watch for the next row | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Failed to connect to {{URL}} OpenAPI tool server` | Error | `src/lib/components/chat/Settings/Integrations.svelte:48-57` | After the save, a personal tool server could not be reached or read from this browser, so it is left out of the chat's tools. A personal terminal server that cannot be reached is dropped without a message (`:79`) | Check the address, key and the server's CORS settings | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `No tool server connections configured.`; `No terminal connections configured.` | Inline | `src/lib/components/chat/Settings/Integrations.svelte:147-151`; `src/lib/components/chat/Settings/Integrations/Terminals.svelte:93-97` | The personal list is empty | None | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Settings saved successfully!` | Success **(unchecked success)** | `src/lib/components/chat/SettingsModal.svelte:836`, triggered at `src/lib/components/chat/Settings/Audio.svelte:164-182` | **Save** on **Audio**: the save is started without waiting for it (`:165`), so this appears at once and a refusal follows as a red pop-up. The auto-playback and auto-send switches save on their own with no green pop-up (`:80-88`) | Reopen the tab if a red pop-up followed | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `{e}` (server text) | Error | `src/lib/components/chat/Settings/Audio.svelte:69-71` | Loading the voice list of the server's text-to-speech engine failed | Retry later | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Loading Kokoro.js...`; `Please do not close the settings page while loading the model.` | Inline | `src/lib/components/chat/Settings/Audio.svelte:335-347` | The in-browser Kokoro voice engine is downloading its model; a percentage follows the first text | Keep the window open until it finishes | See `audio-speech-to-text-and-text-to-speech.md` section 10 |

`src/lib/components/chat/Settings/Advanced/AdvancedParams.svelte` (the advanced-parameters block of
**General** and of the model editor) shows parameter descriptions only; its values are checked by
the server when a chat runs. `Interface/ManageImageCompressionModal.svelte`, `Integrations/Terminals/Connection.svelte`,
`Tools/Connection.svelte` (also used by the admin **Integrations** tab) and the layout helpers
`UserSettingField.svelte`, `UserSettingRow.svelte` and `UserSettingSection.svelte` have labels only.
The strings inside HTML comments in `Shortcuts.svelte` (`:185-205`) exist only so the translation
tool keeps them; they are not displayed from those lines.

### 10.14 `chat/Settings/`: Notifications, Personalization, Data Controls, Usage, Archived Chats, Account, About and the Stats Sync Window

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Response notifications cannot be activated as the website permissions have been denied. Please visit your browser settings to grant the necessary access.` | Error | `src/lib/components/chat/Settings/Notifications.svelte:60-73` | Switching browser notifications on while the browser refuses permission, or offers no notifications at all | Allow notifications for the site in the browser, then switch on again | See `notifications-webhooks-events-and-banners.md` section 10 |
| `Settings saved successfully!` | Success | `src/lib/components/chat/Settings/Notifications.svelte:159` | A notification target (webhook) was created or changed and the list reloaded (`:138-158`); this tab shows its own pop-up | None | See `notifications-webhooks-events-and-banners.md` section 10 |
| `Test notification sent.` | Success | `src/lib/components/chat/Settings/Notifications.svelte:176-179` | **Send Test** on a target was accepted by the server; the delivered text names the app (section 12) | Check the receiving system | See `notifications-webhooks-events-and-banners.md` section 10 |
| `{targetResult.reason}` or `{error}` (server text) | Error | `src/lib/components/chat/Settings/Notifications.svelte:99`, `:102`, `:161`, `:172`, `:181` | Loading the targets (`:99`, `:102`), saving one (`:161`), its on/off switch (`:172`) or **Send Test** (`:181`) failed, for example an address the server will not call | Read the text; check the address | See `notifications-webhooks-events-and-banners.md` section 10; server texts in `error-messages-backend-identity-admin-and-platform.md` section 10 |
| (no text) | (silent on failure) | `src/lib/components/chat/Settings/Notifications.svelte:298-301`, `:316-319` | **Make Default** and **Remove** act at once, without a confirmation, and have no error handling: a refusal shows nothing | Reload and check the list | See `notifications-webhooks-events-and-banners.md` section 11 |
| `No notification targets configured.`; `No chat alerts`; `Only when away` | Inline | `src/lib/components/chat/Settings/Notifications.svelte:242-246`, `:277`, `:278-281` | No target exists; a target follows no chat event; a target sends only while the person is away | None | See `notifications-webhooks-events-and-banners.md` section 10 |
| `Settings saved successfully!` | Success **(unchecked success)** | `src/lib/components/chat/SettingsModal.svelte:829`, triggered at `src/lib/components/chat/Settings/Personalization.svelte:108-109` | **Save** on **Personalization**. That button stores nothing: the memory switch saves when it is moved (`:137`) and memories are saved in their own window, so this pop-up confirms nothing | None | See `user-settings-and-personalisation.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/chat/Settings/Personalization.svelte:55`, `:73`, `:301` | Loading the memories (`:55`), **Clear Memory** (`:73`) or deleting one memory (`:301`) failed | Retry | See `memories.md` section 10 |
| `Clear Memory`; `Are you sure you want to clear all memories? This action cannot be undone.` | Dialog | `src/lib/components/chat/Settings/Personalization.svelte:284-292` | **Clear Memory** | Confirm only if intended | See `memories.md` section 10 |
| `Memory cleared successfully` | Success | `src/lib/components/chat/Settings/Personalization.svelte:77-79` | All memories were deleted; shown only when the list was not already empty | None | See `memories.md` section 10 |
| `Delete Memory?`; `Are you sure you want to delete this memory? This action cannot be undone.` | Dialog | `src/lib/components/chat/Settings/Personalization.svelte:294-322` | **Delete** on one memory; the dialog repeats the memory's text | Confirm only if intended | See `memories.md` section 10 |
| `Memory deleted successfully` | Success | `src/lib/components/chat/Settings/Personalization.svelte:306` | The memory was deleted | None | See `memories.md` section 10 |
| `Memories accessible by LLMs will be shown here.`; `No results found` | Inline | `src/lib/components/chat/Settings/Personalization.svelte:230-237`; first text `src/lib/i18n/locales/en-US/translation.json:3004` | No memory exists; or the search matches none | None | See `memories.md` section 10 |
| `Memory added successfully`; `Memory updated successfully` | Success | `src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:42-44` | The memory window stored a new or changed memory | None | See `memories.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:31-39` | Adding or changing the memory was refused | Read the text | See `memories.md` section 10 |
| `Successfully imported {res.length} chats.` (untranslated) | Success | `src/lib/components/chat/Settings/DataControls.svelte:86-88` | **Import Chats** stored the file's chats (files exported from ChatGPT are converted first, `:43-49`). A file that is not valid JSON (`:41`) or a refused import (`:59-85`, not caught) shows **no** message | Check the sidebar for the imported chats | See `chat-conversations-history-and-organisation.md` section 10 |
| `Archive All Chats`; `Are you sure you want to archive all chats? This action cannot be undone.` | Dialog | `src/lib/components/chat/Settings/DataControls.svelte:124-132`; title `src/lib/i18n/locales/en-US/translation.json:2803` | **Archive All**. Despite the wording, archived chats can be restored under **Archived Chats** › **Unarchive All** | Confirm only if intended | See `chat-conversations-history-and-organisation.md` section 10 |
| `Delete All Chats`; `Are you sure you want to delete all chats? This action cannot be undone.` | Dialog | `src/lib/components/chat/Settings/DataControls.svelte:134-142`; title `src/lib/i18n/locales/en-US/translation.json:2805` | **Delete All**, offered when chat deletion is allowed (`:227`) | Confirm only if intended; deletion is permanent | See `chat-conversations-history-and-organisation.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/chat/Settings/DataControls.svelte:103`, `:113` | Archiving (`:103`) or deleting (`:113`) all chats failed. Both first return to the home page (`:101`, `:111`); success shows no pop-up, only the refreshed sidebar | Retry | See `chat-conversations-history-and-organisation.md` section 10 |
| (no text) | (silent on failure) | `src/lib/components/chat/Settings/DataControls.svelte:93-98` | **Export Chats** has no error handling: a failure downloads nothing and shows nothing | Retry; escalate | See `chat-conversations-history-and-organisation.md` section 11 |
| `Failed to load usage`; `No usage data found`; `No model usage found`; `No model data`; `Token counts are estimates and may not reflect actual API usage` | Inline | `src/lib/components/chat/Settings/Usage.svelte:283-286` (after `:133-138`), `:413`, `:456`, `:251`, `:487` | Loading the person's usage failed; there is no usage yet; no model was used in the period; a chart point without a model; the note under the totals | Reload; choose a longer period | See `evaluations-feedback-and-analytics.md` section 10 and `user-settings-and-personalisation.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/chat/Settings/ArchivedChats.svelte:122`, `:135`, `:159` | Unarchiving one chat (`:122`), deleting one (`:135`) or **Unarchive All** (`:159`) failed. After the first two the chat is taken off the list anyway (`:125`, `:138`), so reload to see the truth | Reload and retry | See `chat-conversations-history-and-organisation.md` section 10 |
| `All chats have been unarchived.` | Success | `src/lib/components/chat/Settings/ArchivedChats.svelte:155` | **Unarchive All** finished | None | See `chat-conversations-history-and-organisation.md` section 10 |
| `Confirm your action`; `Are you sure you want to unarchive all archived chats?` | Dialog (default title) | `src/lib/components/chat/Settings/ArchivedChats.svelte:175-182` | **Unarchive All**; the confirm button reads `Unarchive All` (`src/lib/i18n/locales/en-US/translation.json:2770`) | Confirm | See `chat-conversations-history-and-organisation.md` section 10 |
| `Confirm your action`; `This action cannot be undone. Do you wish to continue?` | Dialog (default texts) | `src/lib/components/chat/Settings/ArchivedChats.svelte:168-173` | **Delete Chat** on an archived chat (offered when chat deletion is allowed, `:356`) | Confirm only if intended | See `chat-conversations-history-and-organisation.md` section 10 |
| `You have no archived conversations.` | Inline | `src/lib/components/chat/Settings/ArchivedChats.svelte:275-281` | No archived chat matches; the list is loaded without error handling (`:67-72`), so a failed load can also end here or leave the list empty | Reload | See `chat-conversations-history-and-organisation.md` section 10 |
| `Variable keys must use lowercase snake case.`; `Variable keys must be unique.` | Error | `src/lib/components/chat/Settings/Account.svelte:95-102`, `:126-131` (shown at `:142`) | A personal variable's key is not lowercase letters, digits and underscores, or repeats another key, in the variable window or when the tab is saved | Rename the key | See `user-settings-and-personalisation.md` section 10 |
| `Settings saved successfully!` | Success | `src/lib/components/chat/SettingsModal.svelte:848`, after `src/lib/components/chat/Settings/Account.svelte:243-246` | **Save** on **Account** stored both the profile and the personal variables (`:152-178`). They are two requests: when one is refused its red pop-up appears, the other may already be stored, and this pop-up is skipped | Reopen the tab and check both parts | See `user-settings-and-personalisation.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/chat/Settings/Account.svelte:159`, `:163`, `:171`, `:192`, `:204`, `:220` | Saving the profile (`:159`) or the variables (`:163`), reloading the account (`:171`, `:204`), deleting the API key (`:192`) or loading the variables (`:220`) failed | Read the text | See `user-settings-and-personalisation.md` section 10 and `authentication-and-sign-in.md` section 10 |
| `API Key created.`; `Failed to create API Key.` | Success; Error | `src/lib/components/chat/Settings/Account.svelte:181-188` | **Create new secret key** returned a key, or an answer without one. A refusal is not caught and shows **no** message (`:182`; `src/lib/apis/auths/index.ts:559-580`) | Retry; if nothing appears, escalate | See `authentication-and-sign-in.md` section 10 |
| `Delete API Key?`; `This will revoke the current API key.` | Dialog | `src/lib/components/chat/Settings/Account.svelte:583-591` | **Delete** beside the API key | Confirm only if the key is no longer used anywhere | See `authentication-and-sign-in.md` section 10 |
| `API Key deleted.` | Success | `src/lib/components/chat/Settings/Account.svelte:196-199` | The key was revoked | None | See `authentication-and-sign-in.md` section 10 |
| `No user variables configured.`; `Empty`; `Prefer not to say` | Inline | `src/lib/components/chat/Settings/Account.svelte:366-370`, `:359`, `:309` | No personal variable exists; a variable has no value; a choice of the gender list | None | See `user-settings-and-personalisation.md` section 10 |
| `The passwords you entered don't quite match. Please double-check and try again.` | Error | `src/lib/components/chat/Settings/Account/UpdatePassword.svelte:41-47` | **Change Password**: the new password and its confirmation differ; both boxes are cleared | Type them again | See `authentication-and-sign-in.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/chat/Settings/Account/UpdatePassword.svelte:18-23` | The password change was refused, for example a wrong current password | Read the text | See `authentication-and-sign-in.md` section 10 |
| `Password updated. Please sign in again.` | Success | `src/lib/components/chat/Settings/Account/UpdatePassword.svelte:25-35` | The password was changed; the browser then signs the person out and goes to the sign-in page | Sign in with the new password | See `authentication-and-sign-in.md` section 10 |
| `Fingerprint spoofing detected: Unable to use initials as avatar. Defaulting to default profile image.` | Info (ten seconds) | `src/lib/components/chat/Settings/Account/UserProfileImage.svelte:146-155`, `:220-229` | Choosing the initials picture while the browser blocks canvas drawing (anti-fingerprinting); the default picture is used instead | Use an uploaded picture, or allow canvas for the site | See `user-settings-and-personalisation.md` section 10 |
| `Could not check for updates`; `Checking for updates...`; `(v{version.latest} available!)`; `(latest)` | Inline | `src/lib/components/chat/Settings/About.svelte:71-84` | The **About** tab's upstream release check, shown when the version check is switched on: failed, running, newer upstream release, or up to date | None: an upstream release is not a MedIT GPT release | See `user-settings-and-personalisation.md` section 10 |
| `Sync Failed`; `{errorMessage}` or `There was an error syncing your stats. Please try again.` | Inline (window) and Error | `src/lib/components/chat/Settings/SyncStatsModal.svelte:346-351`, `:117-120`, `:309-310` | The **Sync Usage Stats** window, which opens only at the request of the upstream community site and when community sharing is on (`src/routes/+layout.svelte:1068-1075`, `:1352-1359`), could not collect or download the stats. `{errorMessage}` is the server's text or an untranslated fallback such as `Failed to export chat stats`, `Failed to fetch stats data`, `An unexpected error occurred`, `Download failed. Please try again.`, `Failed to connect to the server. Please check your connection.` or `Failed to start download. The server may be unavailable.` (`:174`, `:178`, `:203`, `:243-249`, `:309`) | Close the window; follow local policy on sharing usage data (TO BE CONFIRMED) | See `user-settings-and-personalisation.md` section 10 |
| `Do you want to sync your usage stats with Open WebUI Community?`; `Participate in community leaderboards and evaluations! Syncing aggregated usage stats helps drive research and improvements to Open WebUI. Your privacy is paramount: no message content is ever shared.` | Inline (window) | `src/lib/components/chat/Settings/SyncStatsModal.svelte:384-396` | The same window, before syncing; it then lists what is and is not shared (`:398-419`). Upstream wording | Follow local policy (TO BE CONFIRMED) | Established from the code here; the window is described in `user-settings-and-personalisation.md` |

`src/lib/components/chat/Settings/About.svelte` also shows the upstream copyright and licence lines
and, when licence data is loaded, its holder; those are not messages.

### 10.15 `AddConnectionModal.svelte` (Add or Edit a Model Connection)

Used by **Admin Settings** › **Connections** (OpenAI and Ollama lists, 10.5) and by the personal
**Connections** tab (direct connections, 10.13). Saving the window hands the connection to the tab,
whose own messages then follow.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Server connection verified` | Success | `src/lib/components/AddConnectionModal.svelte:87-89`, `:132-134` | **Verify Connection** (`:374`) reached the Ollama (`:76-90`) or OpenAI-compatible (`:92-135`) server with the address and key typed | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/AddConnectionModal.svelte:83-85`, `:128-130` | **Verify Connection** failed; the text is the server's or the provider's answer | Check the address and key | See `model-connections-openai-ollama-and-direct.md` section 10; server texts in `error-messages-backend-chat-content-and-features.md` section 10 |
| `Headers must be a valid JSON object` | Error | `src/lib/components/AddConnectionModal.svelte:98-109`, `:194-204` | The **Headers** box is not a JSON object, at **Verify Connection** (`:98-109`) or at **Save** (`:194-204`). After the **Save** case the busy state is never cleared, so the **Save** button stays disabled (`:795`) until the page is reloaded | Correct the JSON, reload the page, open the window again | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Model ID is already added` | Error | `src/lib/components/AddConnectionModal.svelte:152-155` | Adding a model ID that is already in the connection's list | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `URL is required` | Error | `src/lib/components/AddConnectionModal.svelte:164-168` | **Save** on a non-Ollama connection without an address | Enter the address | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `API Version is required`; `Key is required`; `Deployment names are required for Azure OpenAI` | Error | `src/lib/components/AddConnectionModal.svelte:170-191` | **Save** on an Azure OpenAI connection without an API version (the advanced options open, `:173`), without a key while key authentication is chosen (`:179-184`), or without any deployment name in the model list (`:186-191`) | Fill in the field | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Confirm your action`; `Are you sure you want to delete this connection? This action cannot be undone.` | Dialog (default title) | `src/lib/components/AddConnectionModal.svelte:812-822` | **Delete** in the window (`:785`) | Confirm only if intended | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Leave empty to include all models from "{{url}}/api/tags" endpoint`; `Leave empty to include all models from "{{url}}/models" endpoint`; `Deployment names are required for Azure OpenAI`; `Prefix ID is used to avoid conflicts with other connections by adding a prefix to the model IDs - leave empty to disable` | Inline (help, tooltip) | `src/lib/components/AddConnectionModal.svelte:700-717`, `:596-600` | Under the model ID list (Ollama, Azure, other) and on the prefix box | None | See `model-connections-openai-ollama-and-direct.md` section 10 |

### 10.16 `AddToolServerModal.svelte` and `AddTerminalServerModal.svelte` (Add or Edit a Tool Server or Terminal Server)

Used by **Admin Settings** › **Integrations** (10.7) and by the personal **Integrations** tab (10.13).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Please enter a valid URL` | Error | `src/lib/components/AddToolServerModal.svelte:110-113`, `:162-165` | **Register Client** (`:724`) or **Verify Connection** (`:656`) with no address | Enter the address | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Please enter a valid ID` | Error | `src/lib/components/AddToolServerModal.svelte:92-95`, `:115-118` | **Authorize OAuth** (`:706`) or **Register Client** with no ID | Enter an ID | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Please save the connection before authorizing OAuth` | Error; also a tooltip | `src/lib/components/AddToolServerModal.svelte:97-100`, `:697-701` | **Authorize OAuth** on a connection that has not been saved yet | Save first, then authorize | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Please enter Client ID and Client Secret` | Error | `src/lib/components/AddToolServerModal.svelte:120-123` | **Register Client** with the static OAuth 2.1 type and a missing client ID or secret | Enter both | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Registration failed` | Error | `src/lib/components/AddToolServerModal.svelte:143-146` | Registering the OAuth client with the MCP server failed; the server's reason is dropped (for example `Failed to register OAuth client: {e}` in `admin-settings-panels.md` section 10.4) | Check the address; escalate | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Please save the connection to persist the OAuth client information and do not change the ID`; `Registration successful` | Warning; Success | `src/lib/components/AddToolServerModal.svelte:148-155` | The client was registered; it is kept only once the connection is saved | Save without changing the ID | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Please enter a valid JSON spec`; `Please enter a valid path` | Error | `src/lib/components/AddToolServerModal.svelte:167-176`, `:352-360` | An OpenAPI server with the JSON spec box empty or not valid JSON (at **Verify Connection** or **Save**), or with an empty spec path | Fill in the spec or path | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Headers must be a valid JSON object` | Error | `src/lib/components/AddToolServerModal.svelte:179-190`, `:363-374` | The **Headers** box is not a JSON object | Correct the JSON | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Connection failed` | Error | `src/lib/components/AddToolServerModal.svelte:197-199`, `:229-231` | **Verify Connection** failed, from the browser for a personal (direct) server (`:193-199`) or from the MedIT GPT server for an admin one (`:205-231`); the reason is dropped | Check the address, key and authentication type | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Connection successful`; `OAuth discovery successful` | Success | `src/lib/components/AddToolServerModal.svelte:86-89`, `:201-203`, `:233-235` | **Verify Connection** succeeded; the second wording is used for OAuth authentication types | None | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Import successful`; `Please select a valid JSON file` | Success; Error | `src/lib/components/AddToolServerModal.svelte:285`, `:252-256`, `:286-288` | **Import** (`:509`) filled the form from a file (nothing is saved until **Save**); or the file is an empty list or cannot be read | Press **Save** after an import | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `ID cannot contain ":" or "\|" characters` | Error | `src/lib/components/AddToolServerModal.svelte:339-343` | **Save** with an ID containing a colon or a vertical bar | Change the ID | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Please register the OAuth client` | Error | `src/lib/components/AddToolServerModal.svelte:345-349` | **Save** on an MCP server with OAuth authentication before **Register Client** | Register the client first | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Not Registered` | Inline (badge) | `src/lib/components/AddToolServerModal.svelte:733-737` | OAuth authentication chosen and no client registered yet | Register the client | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Warning:` `MCP support is experimental and its specification changes often, which can lead to incompatibilities. OpenAPI specification support is directly maintained by the Open WebUI team, making it the more reliable option for compatibility.` | Inline (warning) | `src/lib/components/AddToolServerModal.svelte:1034-1050` | Type **MCP** chosen; upstream wording beside a licence comment, with an upstream documentation link | None | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Confirm your action`; `Are you sure you want to delete this connection? This action cannot be undone.` | Dialog (default title) | `src/lib/components/AddToolServerModal.svelte:1094-1104`; `src/lib/components/AddTerminalServerModal.svelte:1040-1050` | **Delete** in either window | Confirm only if intended | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Please enter a valid URL` | Error | `src/lib/components/AddTerminalServerModal.svelte:204-207`, `:338-341` | **Verify Connection** (`:515`) or **Save** with no address | Enter the address | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Connected ({{type}})` | Success | `src/lib/components/AddTerminalServerModal.svelte:220-226` | The server identified itself; `{{type}}` is the English word `Orchestrator` or `Terminal` (not translated) | None | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Server connection failed`; `Server connection verified` | Error; Success | `src/lib/components/AddTerminalServerModal.svelte:238-254`, `:244-246` | The check gave no server type, failed outright, or (for a personal server checked from the browser) failed or succeeded | Check the address and key | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `{{label}} must be a JSON object`; `{{label}} contains invalid JSON` | Error | `src/lib/components/AddTerminalServerModal.svelte:259-270` | **Save** on an orchestrator whose lifecycle box is not a JSON object; `{{label}}` is always the untranslated `Lifecycle JSON` (`:360`) | Correct the JSON | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Policy ID is required`; `Refresh requested: {{count}} terminal(s)`; `Failed to refresh terminals: {{error}}` | Error; Success; Error | `src/lib/components/AddTerminalServerModal.svelte:302-306`, `:321-325`, `:326-328` | **Refresh** on an orchestrator: without a policy ID; accepted, with the number of terminals refreshed; or refused (`{{error}}` is the error as handed back) | Enter a policy ID; retry | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Policy is still loading`; `Failed to load policy: {{error}}`; `Failed to save policy: {{error}}` | Error | `src/lib/components/AddTerminalServerModal.svelte:347-354`, `:382-385` | **Save** on an orchestrator while its policy is loading, after loading it failed, or when storing it on the orchestrator failed | Wait or retry; escalate a repeated failure | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Loading policy...`; `Failed to load policy: {{error}}` | Inline | `src/lib/components/AddTerminalServerModal.svelte:660-667` | Policy section of an orchestrator while loading, or after loading failed (red) | Wait; reopen | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |

### 10.17 `AutomationModal`, `ImportModal`, `ChangelogModal`, `NotificationToast`, `OnBoarding` and `AddFilesPlaceholder`

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Name, prompt, and model are required` | Error | `src/lib/components/AutomationModal.svelte:46-49` | Saving an automation (from `/automations` or the automation editor) with the name, prompt or model empty | Fill in all three | See `automations-calendar-and-timers.md` section 10 |
| `Channel is required` | Error | `src/lib/components/AutomationModal.svelte:50-53` | The target is a channel and none is chosen | Choose a channel | See `automations-calendar-and-timers.md` section 10 |
| `Scheduled time must be in the future` | Error | `src/lib/components/AutomationModal.svelte:54-60` | A one-time schedule whose date and time, in the browser's time zone, have already passed | Pick a later time | See `automations-calendar-and-timers.md` section 10 |
| `Automation updated`; `Automation created` | Success | `src/lib/components/AutomationModal.svelte:76-84` | The automation was stored | None | See `automations-calendar-and-timers.md` section 10 |
| `{e.detail}` or `{e}` (server text) | Error | `src/lib/components/AutomationModal.svelte:85-87` | The server refused the automation, for example a schedule that is too frequent or a limit reached. The coded fallback `Failed to save` can never appear, because the middle choice always yields text (section 14) | Read the text | See `automations-calendar-and-timers.md` section 10; server texts in `error-messages-backend-chat-content-and-features.md` section 10 |
| `Please enter a valid URL` | Error | `src/lib/components/ImportModal.svelte:25-29` | **Import From Link** (functions, 10.3; tools, 10.11) with an empty address; the box is required, so the browser's own hint usually appears first (`:94-97`) | Enter the address | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `{err}` (server text) | Error | `src/lib/components/ImportModal.svelte:31-35` | Downloading the address failed, for example `Failed to fetch the function`; a list of problems prints as `[object Object]` | Check the link opens in a browser | See `functions-pipes-filters-actions-and-pipelines.md` section 10 and `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Function imported successfully`; `Tool imported successfully` | Success | `src/lib/components/ImportModal.svelte:37-42`; tool wording `src/lib/components/workspace/Tools.svelte:317` | The code was downloaded and the create page opens with it. **Nothing is saved yet** | Review the code, then **Save & Create** | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `Could not load release notes.` with **Retry** | Inline | `src/lib/components/ChangelogModal.svelte:170-183` | The **What's New in** {name} window could not fetch the release notes (`:35-38`). It opens for admins after the version changed (`src/routes/(app)/+layout.svelte:355-357`) or from **See what's new** in **General** and **About**; closing it stores the version in the person's settings (`:41-46`) | Press **Retry**; the notes are upstream release notes | See `notifications-webhooks-events-and-banners.md` section 10 |
| `Loading release notes...` | Inline | `src/lib/components/ChangelogModal.svelte:185-190` | While fetching | Wait | See `notifications-webhooks-events-and-banners.md` section 10 |
| (calendar event, channel or chat title, then the time or message) | Notification card | `src/lib/components/NotificationToast.svelte:121-127`; raised by `src/routes/+layout.svelte:600-614`, `:770-777`, `:880-889` | A calendar event is about to start (`Starting now`, `Starting in {{count}} minutes`, `:601-606`), a channel message arrived, or a reply finished in another chat; apart from those time phrases the words are data, not fixed text. A sound plays when notification sounds are on and this is the last active tab (`:68-83`). The coded default title `HI` is never shown, because every caller passes a title | Click the card to open the item | See `notifications-webhooks-events-and-banners.md` section 10 |
| `Dismiss notification` | Inline (button label) | `src/lib/components/NotificationToast.svelte:108` | The close button of the card | None | See `notifications-webhooks-events-and-banners.md` section 10 |
| `{WEBUI_NAME}` (the product name, `MedIT GPT` by default); `Welcome to your AI home.`; `Run AI on your own terms. Connect any model, extend with code, and protect what matters without compromise. Your models, your data, your machine, wherever you open it.`; `Get started`; `Read the docs` | Inline (welcome screen) | `src/lib/components/OnBoarding.svelte:76-120` | The sign-in page when no account exists yet (`backend/open_webui/main.py:2250-2252`, `:2311`; `src/routes/auth/+page.svelte:202`, `:216-222`). **Get started** opens the first-account form; **Read the docs** opens upstream documentation | Only the first administrator sees this | See `authentication-and-sign-in.md` section 10; fork change in section 12 |
| `Add Files`; `Drop any files here to upload` | Inline (drop zone) | `src/lib/components/AddFilesPlaceholder.svelte:11-24` | Shown while files are dragged over an upload area that passes no title or text of its own | Drop the files | See `files-uploads-and-storage.md` section 10 |

### 10.18 Additions to 10.1 (Users and Groups Texts Quoted in Full)

Section 10.1 covers every file in `src/lib/components/admin/Users/` and
`src/lib/components/admin/UserPreviewModal.svelte`; a re-harvest found no missing pop-up or dialog.
These notices were summarized there and are quoted here verbatim.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Running Open WebUI for a team?`; `You have more than 50 users, which often means this workspace is supporting organizational use. Open WebUI is free to use as-is, with no restrictions or hidden limits, and we want to keep it that way.`; `By supporting the project through sponsorship or an enterprise license, you help us stay independent, ship new features faster, improve stability, and grow Open WebUI for the long haul.`; `Enterprise licenses also include dedicated support, customization options, and more, at a fraction of the cost of building and maintaining this stack internally.` | Inline (notice) | `src/lib/components/admin/Users/UserList.svelte:479-512` | **Admin Panel** › **Users** when no licence data is loaded and the user count is above 50; upstream wording beside licence comments | None: licensing questions go to the platform maintainer (TO BE CONFIRMED) | See `users-groups-roles-and-permissions.md` section 10 |
| `Reset group permissions to match the current default user permissions`; `Reset all permissions to their initial configuration values` | Inline (tooltip) | `src/lib/components/admin/Users/Groups/EditGroupModal.svelte:293-299` | Hovering **Reset to Defaults** in a group's permissions (first text) or in **Default permissions** (second) | Remember to **Save** afterwards (10.1) | See `users-groups-roles-and-permissions.md` section 10 |
| `No description`; `Custom permissions`; `Uses defaults` | Inline | `src/lib/components/admin/Users/Groups/GroupItem.svelte:96-111` | A group row without a description; a group whose permissions differ from, or match, the defaults | None | See `users-groups-roles-and-permissions.md` section 10 |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it never changes settings, roles, access or data. The steps below gather
facts and give guidance; anything that needs a change goes to an administrator or the platform
maintainer. Contacts and escalation routes are **TO BE CONFIRMED** (`../tools/ground-truth.md`,
Contacts).

### 11.1 "It said 'Settings saved successfully!' but nothing changed"

**Symptom.** A green pop-up appeared after **Save**, but after closing and reopening the tab the
old value is back, or the behaviour has not changed.

**Likely causes, in order.**

1. **The pop-up did not wait for the save** (unchecked success, 4.3). On admin **Connections**
   (10.5), admin **Interface** (10.6) and personal **Audio** (10.13) it appears before the save
   finishes; a refusal then shows as a red pop-up a moment later, or not at all on admin
   **Interface**. On **Documents**, **Web Search** and **Code Execution** it also appears when the
   save failed without a server text (10.7). **Save** on **Personalization** stores nothing at all
   (10.14).
2. **Only part of the save happened.** **Documents** skips only the embedding change when its own
   check fails and saves the rest (10.7); **Authentication** stores three parts separately (10.4);
   **Account** stores the profile and the personal variables separately (10.14). The part that was
   refused shows its own red pop-up.
3. **The value is controlled elsewhere.** OAuth settings that are not persisted are read-only and
   skipped by **Save** (10.4, `These settings are read from environment variables and cannot be
   edited here while {{ENV_VAR}} is disabled.`); some admin values come from the environment (see
   [`admin-settings-panels.md`](admin-settings-panels.md) section 11.1, 11.2 and 11.9).
4. **The change takes effect later.** A new embedding model needs **Reindex** (10.7); with
   **Cache Base Model List** on, the model list changes only after **Refresh** (10.5); other open
   browser tabs keep their old copy until reloaded.
5. **A personal save that failed without a server text** (for example a dropped connection): the
   save function receives no answer and no error, so the window still reports success and, until
   the page is reloaded, shows the administrator's interface defaults instead of the person's
   settings (read from code: `src/lib/apis/users/index.ts:320-330`;
   `src/lib/components/chat/SettingsModal.svelte:439-450`).

**Diagnostic steps.**

1. Ask for the tab, the setting and whether any red pop-up followed the green one (section 5.1).
2. Ask the person to close the Settings window, reload the page and reopen the tab (5.3).
3. Find the tab's row for `Settings saved successfully!` in section 10 and check whether it is
   marked **(unchecked success)**.
4. For admin settings, read whether the setting is one of the environment-controlled ones in
   [`admin-settings-panels.md`](admin-settings-panels.md) section 7.7 (read-only).

**Resolution.** Ask the person to make the change once more, wait a few seconds, reload and check.
If a red pop-up names a field, correct that field. If the value reverts again, escalate; tier 1
does not change settings.

**Escalation.** Send the tab and setting name, the intended value (never a key or secret), date,
time and time zone, the text of any red pop-up, the browser, and whether the person is an admin.

### 11.2 "I press Save and nothing happens"

**Symptom.** No pop-up at all, or the **Save** button stays greyed out or shows a spinner.

**Likely causes, in order.**

1. **The save was refused and the screen has no error handling** (silent on failure, 4.2): admin
   **Audio** (10.6), **Web Search** and **Code Execution** (10.7) when the server answers with a
   reason; the final update of **Documents** (10.7); the LDAP switch of **Authentication** (10.4);
   shortcut changes (10.13); **Reset knowledge base?** (10.9); several model list actions (10.5,
   10.8).
2. **A check in the browser stopped with a script error before anything was sent**: the function
   editor's `Name and description are required`, which can never be displayed (10.3); an
   **Images** parameters box that is not valid JSON (10.6); the **Linkup** parameters box on
   **Web Search** (10.7); an import file that is not valid JSON (10.3, 10.4, 10.10, 10.11, 10.14).
3. **The button is disabled.** **Images** keeps **Save** disabled after the script error above
   (10.6); the connection window keeps it disabled after `Headers must be a valid JSON object` on
   save (10.15); admin **Models** enables **Save** only after the order or the model defaults were
   changed (`src/lib/components/admin/Settings/Models.svelte:1264-1266`).
4. **The browser's own required-field check** stopped the form: a small bubble next to the empty
   field, not a pop-up (for example the address box of a webhook,
   `src/lib/components/admin/Settings/Events.svelte:440-443`, or of **Import From Link**,
   `src/lib/components/ImportModal.svelte:94-97`).
5. **The tab never finished loading** (its load has no error handling), so its values are missing:
   for example **General** (10.4), **Connections** (10.5), **Documents**, **Web Search**,
   **Code Execution** and **Integrations** (10.7).
6. **The skill editor** stops without a message when the name is empty (10.10).

**Diagnostic steps.**

1. Ask whether any pop-up or field bubble appeared, and which tab or editor it was.
2. Ask the person to reload the page and try once more; a disabled button from cause 3 is cleared
   by the reload.
3. Ask whether a JSON box, an import file or an empty name was involved (causes 2 and 6).
4. Ask whether the tab showed its usual values before **Save** (cause 5).

**Resolution.** Guidance only: correct the field named by the code (section 10 row), reload to
clear a stuck button, retry once. If nothing changes, escalate.

**Escalation.** Send the tab or editor, the field changed (never a secret), the time, the browser,
and whether the page was reloaded. The platform maintainer can reproduce the step with the
browser's developer tools, where these errors are printed.

### 11.3 "A red pop-up appeared but there was no text in it"

**Symptom.** An empty red card, or one that reads only `undefined` or `null`.

**Likely causes, in order.**

1. **The error carried no text.** Several screens hand the raw error value to the pop-up instead of
   a sentence: `src/lib/components/admin/Evaluations/Feedbacks.svelte:117`, `:192` (10.2),
   `src/lib/components/admin/Settings/Evaluations.svelte:26`, `:78` (10.5),
   `src/lib/components/workspace/Prompts.svelte:296` (10.10),
   `src/lib/components/admin/Settings/Models.svelte:761` and
   `src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:367` (10.5). When that value
   is empty or not text, the card can show no words (read from code, not tested).
2. **A proxy or gateway answered instead of MedIT GPT** with an empty or unusual body (the
   proxy layer is **TO BE CONFIRMED**).

**Diagnostic steps.** Ask which screen and action, and the time; ask the person to repeat the
action once and note whether the same happens; check whether other screens work.

**Resolution.** Retry once; if it repeats, escalate. See also
[`error-messages-frontend-chat-and-navigation.md`](error-messages-frontend-chat-and-navigation.md)
section 11.8.

**Escalation.** Screen, action, date, time and time zone, browser; the maintainer checks the
server log for that minute (logs go to standard output only; retention is TO BE CONFIRMED).

### 11.4 "The pop-up just says [object Object]" (or a browser message such as "Failed to fetch")

**Symptom.** A red pop-up reading `[object Object]`, or a browser wording such as a `TypeError`
naming a failed fetch.

**Likely causes, in order.**

1. **The screen printed the whole server answer.** Some API clients hand over the complete answer
   (4.1): the model list refresh on **Connections** (10.5), the model list on admin **Audio**
   (10.6), the **Pipelines** actions when the answer has no `detail` (10.5).
2. **The server's `detail` was a list of problems** (a field of the wrong type or a missing field)
   and the screen printed it as text: for example **Authentication** (10.4), **Import Config**
   (10.4), **Import From Link** and **Import JSON** of functions (10.3, 10.17). **General** is the
   exception: it prints each problem on its own line (10.4).
3. **A browser wording** usually means the request did not reach MedIT GPT or the answer was not JSON
   (network, VPN, a proxy's error page, the server restarting). Many screens show nothing at all in
   that case (4.2).

**Diagnostic steps.**

1. Ask for the screen, the action and the values typed (never a key or password).
2. Ask whether other pages load; if nothing loads, the problem is not this screen.
3. For a browser wording, ask whether the person is on an unusual network (the supported network
   set-up is TO BE CONFIRMED).

**Resolution.** Correct an obviously wrong value (a number box holding text, an empty required
field) and retry; otherwise escalate. See also
[`error-messages-frontend-chat-and-navigation.md`](error-messages-frontend-chat-and-navigation.md)
section 11.4.

**Escalation.** Screen, action, values typed, date, time and time zone, browser. The real reason is
in the server log for that minute or in the browser's network response, which the maintainer can
read.

### 11.5 "It says I don't have permission"

**Symptom.** One of: the server text `You do not have permission to access this resource. Please
contact your administrator for assistance.`; `You do not have permission to edit this prompt.` or
`You do not have permission to edit this skill.` (10.10); `You do not have permission to upload
files to this knowledge base.` (10.9); `You do not have permission to upload files.` (10.8); the
tooltip `You do not have permission to make this public` (10.12); a `Read Only` badge; or a page
that silently returns to the home page (section 3).

**Likely causes, in order.**

1. **The item is shared read-only** (`Read Only` badge): editors refuse to save (10.9 to 10.11).
2. **A missing permission** for the Workspace section, sharing, file upload or a feature. Defaults
   and group permissions add up, and a group cannot take a default away
   (`../tools/ground-truth.md`, Accounts and Access).
3. **An admin-only screen or action**: non-admins are sent back to `/` without a message (section 3).
4. **A role change while the page was open**: requests from the old page are refused with HTTP 401.

**Diagnostic steps.**

1. Ask for the role (`admin`, `user`), the screen, and the item's name or the ID in the address.
2. Ask whether the item shows `Read Only`.
3. Ask the person to reload the page and repeat the action once.

**Resolution.** Tier 1 cannot grant access. Explain read-only sharing and ask the item's owner for
write access, or route a permission request to an administrator. See
[`users-groups-roles-and-permissions.md`](users-groups-roles-and-permissions.md) section 11.6 to
11.8 and
[`error-messages-backend-identity-admin-and-platform.md`](error-messages-backend-identity-admin-and-platform.md)
section 11.2.

**Escalation.** The person's role, the screen, the item's ID (from the address, never its
content), the exact text, the time.

### 11.6 "It said it worked, and then an error appeared" (Success Shown Before the Save Finished)

**Symptom.** A green pop-up followed at once by a red one, or a green summary after a batch in
which some items clearly failed.

**Likely causes, in order.**

1. **The green pop-up is shown before or regardless of the result** (rows marked **(unchecked
   success)**): admin **Connections** and **Interface** **Save** (10.5, 10.6); personal **Audio**
   (10.13); `Success` after **Reset Vector Storage/Knowledge** (10.7); the personal
   **Integrations** save, shown before the servers are contacted, followed by `Failed to connect
   to {{URL}} OpenAPI tool server` (10.13); `All models are now visible`, `All models are now
   hidden` and `Model {{name}} is now hidden` on admin **Models** (10.5); `ID copied to clipboard`
   (10.9, 10.10).
2. **Batch imports report once at the end**, after a red pop-up per failed entry:
   `Functions imported successfully` (10.3), `Tool imported successfully` (10.11),
   `Skill imported successfully` (10.10), and `Successfully imported {{userCount}} users.` (10.1).
3. **A follow-up step failed after a successful save**, for example the arena model window after
   the model list reload (10.5), or `Failed to save webhook` when only the list reload failed
   (10.4).

**Diagnostic steps.** Ask for both texts and their order. The later red pop-up is the one that
counts; ask the person to reload and check what was actually stored, and for a batch, compare the
list with the file.

**Resolution.** Redo the failed part once, correcting any field the red text names. For imports,
re-import only the entries that are missing.

**Escalation.** Both texts, in order, the screen, the time, and for imports the number of entries
expected and found (never the file's content).

## 12. Local Customisations

Within the 150 files in scope, the fork changes **one** file. `git diff main...uoft` shows
`src/lib/components/OnBoarding.svelte` only: the small label above the welcome heading prints the
configured product name instead of the fixed words `Open WebUI`, and the licence comment above it
is kept (`src/lib/components/OnBoarding.svelte:3`, `:74-80`). No in-scope file has uncommitted
changes (`git status` lists none of them). Every other message in section 10 matches upstream
v0.11.4.

| Change | Effect on the messages in this catalogue | Evidence |
|---|---|---|
| Product name | Texts that insert the name show the configured name (default `MedIT GPT`; the live value is an environment setting, TO BE CONFIRMED): the welcome screen label (10.17), the `What's New in` {name} window (10.17), the **About** section title {name} `Version`, and the browser tab titles of the Functions, Models, Knowledge, Prompts, Skills and Tools pages, for example `Functions / MedIT GPT` | `backend/open_webui/env.py:951`; `src/lib/constants.ts:7`; `src/lib/components/ChangelogModal.svelte:100-101`; `src/lib/components/chat/Settings/About.svelte:61`; `src/lib/components/admin/Functions.svelte:315`; `src/lib/components/workspace/Models.svelte:460` |
| Upstream wording kept on purpose | Many fixed texts in scope still name **Open WebUI**, each beside a licence comment that forbids changing it, and the fork leaves them unchanged, for example `Redirecting you to Open WebUI Community` (10.3, 10.8, 10.10, 10.11), `Running Open WebUI for a team?` (10.18), `Help us translate Open WebUI!` (10.13), `Event names may change as Open WebUI evolves…` (10.4), `External vectors must be generated with the same embedding model configured in Open WebUI.` (10.7), `This knowledge base retrieves from a connected source. Open WebUI can query it…` (10.9), the MCP warning (10.16), `CORS must be properly configured by the provider to allow requests from Open WebUI.` (10.13) and the stats sync window (10.14) | `CLAUDE.md` (Conventions); the licence comments at each cited line |
| Test notification text | The message delivered by **Send Test** (`Test notification sent.`, 10.14) now names the app: `This is a test notification from {app_name}.`, where upstream's fixed sentence named Open WebUI | `backend/open_webui/utils/notifications.py:357-362` |
| Two personal Interface settings | **Hide Processing Details** and **Inline Citations** are drawn by `src/lib/components/common/InterfaceSettings.svelte`, outside this scope; the fork's four new `en-US` dotted keys are not used by any in-scope file | `git diff main...uoft -- src/lib/i18n/locales/en-US/translation.json` |
| Uncommitted language loading (working tree) | `src/lib/i18n/index.ts` now maps a browser's language code to the nearest bundled language and adds English after an administrator's default language as the last fallback, so the language in which a person sees these messages can differ from upstream. The uncommitted `en-US` change rewords only `settings.personal.interface.hideProcessingDetails.description`, which no in-scope file uses | `src/lib/i18n/index.ts:75-86`, `:93`, `:105`; `git diff -- src/lib/i18n/index.ts src/lib/i18n/locales/en-US/translation.json` |

## 13. Source File Index

### 13.1 In Scope (150 Files, All Read)

| Folder or files | What they hold | Section 10 |
|---|---|---|
| `src/lib/components/admin/Users.svelte`, `src/lib/components/admin/Users/` (11 files), `src/lib/components/admin/UserPreviewModal.svelte` | Users, groups, permissions, user preview | 10.1, 10.18 |
| `src/lib/components/admin/Evaluations.svelte`, `src/lib/components/admin/Evaluations/` (6 files: `FeedbackMenu`, `FeedbackModal`, `Feedbacks`, `Leaderboard`, `LeaderboardModal`, `ModelActivityChart`), `src/lib/components/admin/Analytics.svelte`, `src/lib/components/admin/Analytics/` (3 files) | Evaluations and analytics (`FeedbackMenu.svelte` has labels only) | 10.2 |
| `src/lib/components/admin/Functions.svelte`, `src/lib/components/admin/Functions/` (`AddFunctionMenu`, `FunctionEditor`, `FunctionMenu`) | Functions list and editor | 10.3 |
| `src/lib/components/admin/Settings/General.svelte`, `Events.svelte`, `I18nSettings.svelte`, `Authentication.svelte`, `Database.svelte`, `AdminSettingField.svelte`, `AdminSettingRow.svelte`, `AdminSettingSection.svelte`, `AdminTabIcon.svelte` | Admin tabs General (with Events and UI Translations), Authentication, Database; layout helpers | 10.4 |
| `src/lib/components/admin/Settings/Connections.svelte` and `Connections/` (3 files), `Models.svelte` and `Models/` (8 files, including `Manage/`), `Subagents.svelte`, `Evaluations.svelte` and `Evaluations/` (2 files), `Pipelines.svelte` | Admin tabs Connections, Models, Sub-agents, Evaluations, Pipelines | 10.5 |
| `src/lib/components/admin/Settings/Interface.svelte`, `Interface/Banners.svelte`, `Audio.svelte`, `Images.svelte` | Admin tabs Interface, Audio, Images | 10.6 |
| `src/lib/components/admin/Settings/Integrations.svelte`, `ExternalKnowledge.svelte`, `Documents.svelte`, `WebSearch.svelte`, `CodeExecution.svelte` | Admin tabs Integrations (with External Knowledge), Documents, Web Search, Code Execution | 10.7 |
| `src/lib/components/workspace/Models.svelte`, `src/lib/components/workspace/Models/` (17 files) | Workspace models and the model editor | 10.8 |
| `src/lib/components/workspace/Knowledge.svelte`, `src/lib/components/workspace/Knowledge/` (9 files) | Knowledge list and one knowledge base | 10.9 |
| `src/lib/components/workspace/Prompts.svelte`, `Prompts/` (3 files), `Skills.svelte`, `Skills/` (2 files) | Prompts, prompt history, skills | 10.10 |
| `src/lib/components/workspace/Tools.svelte`, `src/lib/components/workspace/Tools/` (`AddToolMenu`, `ToolMenu`, `ToolkitEditor`) | Tools list and editor | 10.11 |
| `src/lib/components/workspace/common/` (11 files) | Sharing, member picker, valves, support window, plugin translations, selectors | 10.12 |
| `src/lib/components/chat/Settings/General.svelte`, `Interface.svelte`, `Interface/` (2 files), `Shortcuts.svelte`, `Connections.svelte`, `Connections/Connection.svelte`, `Integrations.svelte`, `Integrations/` (2 files), `Tools/Connection.svelte`, `Audio.svelte`, `Advanced/AdvancedParams.svelte`, `UserSettingField.svelte`, `UserSettingRow.svelte`, `UserSettingSection.svelte` | Personal tabs, first group | 10.13 |
| `src/lib/components/chat/Settings/Notifications.svelte`, `Personalization.svelte`, `Personalization/MemoryModal.svelte`, `DataControls.svelte`, `Usage.svelte`, `ArchivedChats.svelte`, `Account.svelte`, `Account/` (2 files), `About.svelte`, `SyncStatsModal.svelte` | Personal tabs, second group, and the stats sync window | 10.14 |
| `src/lib/components/AddConnectionModal.svelte` | Model connection window | 10.15 |
| `src/lib/components/AddToolServerModal.svelte`, `src/lib/components/AddTerminalServerModal.svelte` | Tool server and terminal server windows | 10.16 |
| `src/lib/components/AutomationModal.svelte`, `ImportModal.svelte`, `ChangelogModal.svelte`, `NotificationToast.svelte`, `OnBoarding.svelte`, `AddFilesPlaceholder.svelte` | Other top-level dialogs | 10.17 |

### 13.2 Read for Context (Not in Scope)

| File | Why it was read |
|---|---|
| `src/lib/components/chat/SettingsModal.svelte` | Shows most `Settings saved successfully!` pop-ups for the tabs (4.4), the personal save function (10.13, 11.1) |
| `src/lib/components/common/ConfirmDialog.svelte` | Default dialog title and text |
| `src/lib/components/common/InterfaceSettings.svelte` | Saves the personal Interface tab (10.13); its messages are in the chat and navigation catalogue |
| `src/lib/components/layout/Sidebar/ChannelModal.svelte` | The only user of `Visibility.svelte` (10.12) |
| `src/lib/apis/auths/index.ts`, `configs/index.ts`, `index.ts`, `models/index.ts`, `ollama/index.ts`, `openai/index.ts`, `retrieval/index.ts`, `users/index.ts`, `audio/index.ts`, `evaluations/index.ts`, `notifications/index.ts`, `pipelines` (in `index.ts`), `chats/index.ts` | How each client hands an error to the screen (4.1, rows marked server text) |
| `src/lib/utils/translationDictionary.ts` | The UI Translations checks (10.4) |
| `src/lib/utils/settings-access.ts` | Which personal controls are shown (section 3) |
| `src/lib/i18n/index.ts`, `src/lib/i18n/locales/en-US/translation.json` | Dotted key resolution, fallback language, the uncommitted change (12) |
| `src/lib/constants.ts` | Product name in the front end (12) |
| `src/routes/+layout.svelte`, `src/routes/(app)/+layout.svelte`, `src/routes/(app)/admin/+layout.svelte`, `src/routes/(app)/admin/settings/[tab]/+page.svelte`, `src/routes/(app)/workspace/+layout.svelte`, `src/routes/auth/+page.svelte` | Toast rendering, page guards, changelog and onboarding triggers, notification cards |
| `src/routes/(app)/workspace/tools/create/+page.svelte`, `src/routes/(app)/workspace/tools/edit/+page.svelte` | Confirm the tool "created" and "updated" texts live on the route pages (10.11) |
| `backend/open_webui/main.py` | When onboarding is reported (10.17) |
| `backend/open_webui/routers/models.py` | What the model import answers (10.5) |
| `backend/open_webui/routers/knowledge.py` | Directory delete moves files to the parent (10.9) |
| `backend/open_webui/utils/notifications.py` | Fork change to the test notification (12) |
| `backend/open_webui/env.py` | Default product name (12) |

## 14. Open Questions

### 14.1 Texts That Can Never Be Shown (Read From Code)

| Text or element | Why | Evidence |
|---|---|---|
| `Name and description are required` (function editor) | The file never imports the pop-up library, so the line stops with a script error and nothing is shown or saved | `src/lib/components/admin/Functions/FunctionEditor.svelte:2-16`, `:329-332` |
| The second function starter (`_boilerplate`), including `Could not fetch models from OpenAI, please update the API Key in the valves.` and `Conversation turn limit exceeded. Max turns: {self.valves.max_turns}` | Defined but never used | `src/lib/components/admin/Functions/FunctionEditor.svelte:174-326`, `:213`, `:288` |
| `AddFunctionMenu.svelte` and `AddToolMenu.svelte` (labels such as `New Function`) | Not imported by any file in `src/` | `src/lib/components/admin/Functions/AddFunctionMenu.svelte:45`; `src/lib/components/workspace/Tools/AddToolMenu.svelte` |
| `Failed to add file.` (and that path's `File added successfully.`) | Its handler is never called; the same success text is shown by other paths | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:780-798` |
| `Failed to save` (automation window) | It is the last of three choices, and the middle one (the error written out as text) always yields something, so the last is never reached | `src/lib/components/AutomationModal.svelte:87` |
| `Failed to import models` | The model import answers `true` or an error, never a false value | `src/lib/components/admin/Settings/Models.svelte:757-759`; `backend/open_webui/routers/models.py:441`, `:664` |
| `HI` (default notification card title) | Every caller passes its own title text; a calendar event's title is a required field (`backend/open_webui/models/calendar.py:130`) | `src/lib/components/NotificationToast.svelte:15`; `src/routes/+layout.svelte:613`, `:776`, `:888` |
| `Leave empty to include all models from "{{url}}" endpoint` (Azure) | Inside an HTML comment | `src/lib/components/AddConnectionModal.svelte:711-713` |
| Strings inside HTML comments, for example the shortcut names and conditions in `Shortcuts.svelte`, `Enter the URL of the function to import` and `Admins have access to all tools at all times; users need tools assigned per model in the workspace.` | Kept only so the translation tool keeps the keys | `src/lib/components/chat/Settings/Shortcuts.svelte:185-205`; `src/lib/components/ImportModal.svelte:100`; `src/lib/components/admin/Functions.svelte:736-740` |
| `Expected a JSON object of translation keys and strings.`; `Translation must be a string: {key}` | Not reachable from the UI Translations rows of **General**, which always pass an object of strings (the first is reachable from a component outside this scope) | `src/lib/utils/translationDictionary.ts:15`, `:18`, `:52-70` |
| `Settings saved successfully!` for the **Database** tab | The handler is accepted but never called | `src/lib/components/admin/Settings/Database.svelte:17`; `src/lib/components/chat/SettingsModal.svelte:897-901` |
| A second pop-up from the `save` events of admin **Evaluations** and admin **Audio** | Nothing listens to them | `src/lib/components/admin/Settings/Evaluations.svelte:91`; `src/lib/components/admin/Settings/Audio.svelte:244`; `src/lib/components/chat/SettingsModal.svelte:867-868`, `:885-890` |

### 14.2 Behaviour Inferred From Code, Not Tested

- A personal save that fails without a server text shows `Settings saved successfully!` and the
  window falls back to the administrator's interface defaults until reload (11.1, cause 5).
- **Import Config** may not react when the same file is chosen twice in a row: the code tries to
  clear the file box but clears the file reader instead
  (`src/lib/components/admin/Settings/Database.svelte:66-80`); browsers usually fire no change
  event for the same file.
- **Images** **Save** staying disabled after a JSON error (10.6) and the connection window's
  **Save** staying disabled after a headers error (10.15) were read from the busy flags, not seen.
- What an empty or non-text value looks like in a red pop-up (11.3).
- A picture the browser cannot decode is expected to show the browser's own text rather than
  `Invalid background image.`, because the browser's decoding error counts as a normal error (10.8).
- The double full stop after `Tools have a function calling system that allows arbitrary code
  execution.` on the Tools list (10.11) was read from the markup.

### 14.3 Differences From Other Reference Documents (Not Edited Here)

- [`admin-settings-panels.md`](admin-settings-panels.md) section 10.3 describes `Failed to save
  webhook`, `Failed to delete webhook` and `Failed to update webhook` as "(or the server's text)".
  The code never shows the server's text there: the request helper hands over an object and the
  panel prints only plain strings (`src/lib/components/admin/Settings/Events.svelte:357`, `:372`,
  `:386`; `src/lib/apis/index.ts:1695-1705`).
  [`notifications-webhooks-events-and-banners.md`](notifications-webhooks-events-and-banners.md)
  section 10 agrees with this document.
- [`admin-settings-panels.md`](admin-settings-panels.md) section 10.3 says `OpenAI URL/Key
  required.` covers the "OpenAI or Azure embedding engine"; the code checks only **Azure OpenAI**
  (`src/lib/components/admin/Settings/Documents.svelte:109-115`), as
  [`rag-retrieval-embeddings-and-vector-stores.md`](rag-retrieval-embeddings-and-vector-stores.md)
  section 10 says.
- [`admin-settings-panels.md`](admin-settings-panels.md) section 5.2 lists **Web Search** and
  **Code Execution** as showing `Settings saved successfully!` "after success". A save that fails
  without a server text also shows it, because the clients then return nothing instead of an error
  (`src/lib/apis/retrieval/index.ts:86-91`; `src/lib/apis/configs/index.ts:623-633`; 10.7).
- Nothing found contradicts `../tools/ground-truth.md`.

### 14.4 To Be Confirmed (Organisational or Live Data)

- Support contacts, escalation routes and hours (`../tools/ground-truth.md`, Contacts).
- The production host and any proxy in front of it, which matter for blank pop-ups and browser
  error texts (11.3, 11.4).
- Live values of the switches that decide which messages can appear: community sharing (**Share**,
  **Discover**, the stats sync window), the version update check, OAuth persistence, message
  rating, admin export, direct connections and direct integrations, API keys, memories, code
  execution engines.
- Local policy on sharing functions, models, prompts and tools with the upstream community site,
  on the community stats sync, and on the plugin funding links (10.3, 10.8, 10.10 to 10.12, 10.14).
- Which `LICENSE` §4 exception applies, and whether the upstream licence notices in 10.4 and 10.18
  are expected to show (`../tools/ground-truth.md`, Version and Identity).
- Whether administrators have replaced any wording through **UI Translations** (`ui.i18n`, 4.5).
- Server log retention and how the maintainer is asked for log lines.
- Whether production runs more than one server process (affects OAuth settings that are not
  persisted, 11.1).
- The product name in production (`WEBUI_NAME` is an environment setting, section 12).

### 14.5 Security-Sensitive Items

None was found in the front-end messages in scope that needed to be withheld. Questions about
where shared or synced data goes once it leaves MedIT GPT (community sharing, stats sync) are
policy questions: refer them to the platform maintainer and U of T Information Security
(security.utoronto.ca).
