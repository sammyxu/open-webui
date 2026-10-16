# Error Messages: Front End, Chat, Sidebar and Navigation

## At a Glance

- A cross-cutting catalogue of every toast, confirmation dialog and visible error string shown by
  the browser front end outside the settings, admin and workspace screens: the chat screen, the
  sidebar and navigation, channels, notes, common components, automations, calendar, playground,
  every route under `src/routes/`, and the shared utilities, API clients and web workers.
- Many front-end messages print text that came from the server; those rows say "server text" and
  point to the two backend catalogues.
- Messages already explained in an area document are listed briefly with a pointer to that
  document's section 10; messages no other document covers have their trigger written in full.
- Provisional summary; refined when the catalogue is complete.
- *Refined 2026-10-10 (catalogue complete):* section 10 has 374 rows in 18 subsections, one per
  component folder plus routes, utilities, API clients and workers, quoting 383 distinct fixed
  texts and 12 server-text patterns such as `{error}`. Of the 414 files in scope, 429 pop-up calls
  exist and 143 of them print server text unchanged (section 4.1).
- 34 of the distinct texts are documented nowhere else and were established from the code here;
  the rest point to the owning area document. Several green pop-ups appear without checking that
  the action worked (marked **unchecked success**), and some failures show nothing at all
  (section 11.5).
- Section 11 gives the cross-cutting patterns: connection lost, "Backend Required", session
  expired, `[object Object]`, silent failures, false success, tool-server pop-ups at every load,
  blank pop-ups and texts that match no row. Section 14 lists what the code cannot answer.

## 1. Purpose and Who Uses It

This catalogue lets tier-1 support take a message a MedIT GPT user reports from the chat screen,
the sidebar, channels, notes, automations, the calendar, the playground or a full-page route, and
find the browser code that showed it, what usually causes it and what to check. It lists
**front-end text**: words written into the Svelte components, routes, utilities and API clients.
Where a pop-up only prints what the server answered, the row says "server text" and points to the
two backend catalogues,
[`error-messages-backend-identity-admin-and-platform.md`](error-messages-backend-identity-admin-and-platform.md)
and
[`error-messages-backend-chat-content-and-features.md`](error-messages-backend-chat-content-and-features.md).

| Reader | What they use it for |
|---|---|
| Tier-1 support (read-only) | Matching a reported text to a row in section 10, then following the row's support check or the pattern in section 11 |
| Platform maintainer | The source line behind an escalation, and the messages no area document explains |
| Writers of the numbered support guides | The verbatim wording to quote, and which area document owns each message |

Scope, as assigned in `_areas.md` row 30 and the hand-over for this catalogue (414 source files):

| Folder | Files | Notes |
|---|---|---|
| `src/lib/components/chat/` | 120 | Chat screen, composer, messages, model picker, file navigator, chat controls; **excluding** `src/lib/components/chat/Settings/` (area 31) |
| `src/lib/components/layout/` | 58 | Sidebar, navbar, search, chats and files windows, overlays |
| `src/lib/components/common/` | 72 | Shared widgets: dialogs, editors, file items, tool-call display, interface settings |
| `src/lib/components/channel/` | 17 | Channels and direct messages |
| `src/lib/components/automations/`, `calendar/`, `notes/`, `playground/`, `app/` | 9, 5, 7, 5, 1 | Feature screens |
| `src/routes/` | 57 | Every page and layout, including `/auth`, `/error`, `/s/[id]`, `/watch` and the `(app)` group |
| `src/lib/utils/` | 30 | Shared helpers (copying, downloads, Markdown, audio, uploads) |
| `src/lib/apis/` | 30 | The API clients; they throw the server's answer to the caller |
| `src/lib/workers/` | 3 | Web workers (Pyodide, Kokoro voice) |

Admin, workspace and personal-settings screens, and the top-level `src/lib/components/*.svelte`
modals, belong to the sibling front-end catalogue planned as area 31
(`error-messages-frontend-admin-workspace-and-settings`). Status lines written inside a chat
response belong to the in-chat catalogue planned as area 32
(`in-chat-status-and-response-messages`); this document lists only the pop-ups and fixed texts
those components show.

## 2. Navigation and URLs

### 2.1 Where Front-End Messages Appear

| Surface | What the user sees | Evidence |
|---|---|---|
| **Pop-up (toast)** | A small card in the top-right corner with a close button, coloured by type: red for `toast.error`, yellow for `toast.warning`, green for `toast.success`, blue for `toast.info` (`richColors`). Most of the catalogue is toasts. | `src/routes/+layout.svelte:1435-1452` |
| **Notification card** | A larger clickable card (custom toast) when a reply finishes in another chat, a channel message arrives or a calendar reminder is due; clicking opens the chat, channel or calendar | `src/routes/+layout.svelte:608`, `:770`, `:880` |
| **Confirmation dialog** | A centred window with a title, a text and **Cancel** / **Confirm** buttons. Without a custom title it reads `Confirm your action`; without a custom text, `This action cannot be undone. Do you wish to continue?`. Several screens import the same dialog under the name `DeleteConfirmDialog`. The text is rendered as Markdown. | `src/lib/components/common/ConfirmDialog.svelte:21-22`, `:140-154`; `src/lib/components/chat/Chat.svelte:117` |
| **Inline text** | A fixed sentence inside a screen instead of a pop-up, for example the channel composer replaced by a permission sentence, or an empty file list | for example `src/lib/components/channel/Channel.svelte:410` |
| **Error box under a chat reply** | A grey box with an information icon below the reply, holding the stored error or, when the error is empty, `Error submitting message` (owned by the planned in-chat catalogue, area 32) | `src/lib/components/chat/Messages/Error.svelte:6-37` |
| **Banner** | A strip above the chat with a type label (`Info`, `Warning`, `Error`, `Success`) and text an admin wrote; the text is data | `src/lib/components/common/Banner.svelte:58-68`; `src/lib/components/chat/Navbar.svelte:277-310` |
| **Full-page error** | The SvelteKit error page: only `{status}: {message}`, for example a missing page | `src/routes/+error.svelte:8` |
| **"Backend Required" screen** | Shown at `/error` when the browser could not load the server's configuration at start-up: `{{webUIName}} Backend Required`, a sentence about serving the WebUI from the backend, upstream help links and a **Check Again** button that reloads `/` | `src/routes/+layout.svelte:1317`; `src/routes/error/+page.svelte:25-53` |
| **Account pending overlay** | Replaces the whole app for an account whose role is neither `user` nor `admin` | `src/routes/(app)/+layout.svelte:445-446`; `src/lib/components/layout/Overlay/AccountPending.svelte` |
| **Update card** (admins) | A blue card in the bottom-right corner, `A new version (v{{LATEST_VERSION}}) is now available.`, when the version check is on and a newer release exists | `src/routes/(app)/+layout.svelte:369-381`, `:428-437`; `src/lib/components/layout/UpdateInfoToast.svelte:20-25` |
| **Error passed in the address** | Opening `/?error=<text>` shows `<text>` as a red pop-up (fallback `An unknown error occurred.`); other screens redirect to such a URL | `src/routes/(app)/+page.svelte:8-12` |

The code in scope contains no browser `alert()`, `confirm()` or `window.prompt()` calls (bulk
search of the 414 files); every confirmation goes through `ConfirmDialog` or a screen's own
window.

### 2.2 Which Screen Uses Which Folder

| Address | Screen | Where its messages are written | Section 10 |
|---|---|---|---|
| `/`, `/c/{id}` | Chat | `src/lib/components/chat/` (`src/routes/(app)/c/[id]/+page.svelte:7`) | 10.1 to 10.7 |
| Every signed-in screen | Sidebar, search, chats and files windows, user menu | `src/lib/components/layout/` | 10.8 |
| `/channels/{id}` | Channels and direct messages | `src/lib/components/channel/` (`src/routes/(app)/channels/[id]/+page.svelte:7`) | 10.9 |
| `/notes`, `/notes/new`, `/notes/{id}` | Notes | `src/lib/components/notes/` (`src/routes/(app)/notes/[id]/+page.svelte:25`) | 10.10 |
| Any screen | Shared widgets (dialogs, file previews, editors, tool calls) | `src/lib/components/common/` | 10.11 |
| `/automations`, `/automations/{id}`, `/calendar` | Automations and calendar | `src/lib/components/automations/`, `calendar/` and the route pages | 10.12, 10.13, 10.15 |
| `/playground`, `/playground/completions`, `/playground/images` | Playground (admins) | `src/lib/components/playground/` | 10.14 |
| `/auth`, `/s/{id}`, `/error`, `/watch`, and the page files of every other route | Sign-in, shared chat, start-up and route-level pop-ups | `src/routes/` | 10.15 |
| None (helpers) | Copying, downloads, file reading, pickers, translations | `src/lib/utils/`, `src/lib/workers/` | 10.16, 10.18 |
| None (helpers) | Errors handed back to the screens | `src/lib/apis/` | 10.17 |

`/watch?v={id}` only forwards to `/?youtube={id}` (`src/routes/watch/+page.svelte:10-20`).

## 3. Roles and Permissions

The front end decides which messages a person can meet mostly by which screens and buttons it
shows. The server still makes the final decision; a refused request comes back as server text
(section 4.1).

| Who | What they can meet | Evidence |
|---|---|---|
| Signed-out visitor | The sign-in page pop-ups, shared-chat errors at `/s/{id}`, the "Backend Required" screen, `Session expired. Please sign in again.` after an expiry | `src/routes/auth/+page.svelte`; `src/routes/s/[id]/+page.svelte:150-157`; `src/routes/error/+page.svelte`; `src/routes/+layout.svelte:931-950` |
| `pending` account | Only the account pending overlay; the sidebar and chat are not loaded | `src/routes/(app)/+layout.svelte:445-446` |
| `user` | Every chat, sidebar, channel, notes, automation and calendar message, as far as the matching feature and permission are on | sections 10.1 to 10.14 |
| `admin` | Everything above plus the update card, the changelog window, model download and delete messages in the model picker, and the playground (its links are shown to admins only) | `src/routes/(app)/+layout.svelte:355-381`; `src/lib/components/layout/Sidebar.svelte:183-184`; `src/lib/components/layout/Sidebar/UserMenu.svelte:425` |

**A switched-off feature gives no message.** Opening `/notes`, `/automations`, `/admin` or a
workspace page without the feature or permission sends the person back to `/` without a pop-up
(`src/routes/(app)/notes/+layout.svelte:10-19`; `src/routes/(app)/automations/+layout.svelte:56-63`;
`src/routes/(app)/admin/+layout.svelte:16-17`; `src/routes/(app)/workspace/+layout.svelte:81-100`).
A user who says "the page just goes back to a new chat" is usually meeting one of these checks.

**Permission sentences shown by the front end.** Some screens explain a missing permission
themselves instead of waiting for the server, for example
`You do not have permission to upload files.` in the composer's attach menu
(`src/lib/components/chat/MessageInput/InputMenu.svelte:191`) or
`You do not have permission to send messages in this channel.`
(`src/lib/components/channel/Channel.svelte:410`). The permission keys behind them are explained
in [`users-groups-roles-and-permissions.md`](users-groups-roles-and-permissions.md).

## 4. Key Concepts and Terminology

### 4.1 Server Text in a Pop-Up

Most red pop-ups in scope print whatever the API client handed back. Of the 429 toast calls in
scope, 143 pass only the error value to `toast.error` (written `${error}`, `${err}` or `${e}`)
and add no words of their own (bulk count of the 414 files). The API clients in `src/lib/apis/` read the server's answer
and pass on its `detail` field:

| How the client hands the error on | Call sites in `src/lib/apis/` | What the pop-up shows |
|---|---|---|
| `error = err.detail` | 340 | The server's `detail` text. When `detail` is a list (a request the server could not validate, HTTP 422) or an object, the pop-up shows `[object Object]`; when it is missing, nothing is thrown and the screen usually shows no message (4.2) |
| `error = err` | 66 | The whole answer; a plain object prints as `[object Object]` |
| `error = getErrorDetail(err)` (chats client) | 33 | The `detail` text, or the `msg` parts of a validation list joined with commas (`src/lib/apis/chats/index.ts:4-10`) |
| `error = getErrorMessage(err)` | 9 | The client's own extraction of the answer |
| `error = 'Server connection failed'` | 13 | The literal text, when the failure carries no server `detail` (a network failure, or an answer that is not JSON) (section 10.17) |

So the text of most pop-ups lives in the backend: look it up in
[`error-messages-backend-identity-admin-and-platform.md`](error-messages-backend-identity-admin-and-platform.md)
or
[`error-messages-backend-chat-content-and-features.md`](error-messages-backend-chat-content-and-features.md)
section 10. In section 10 of this document such rows read **server text**.

### 4.2 `[object Object]`, Browser Error Texts and Silent Failures

These are not messages anyone wrote. They appear when a screen prints an error value that is not a
sentence, or when there is no value to print:

- `[object Object]`: the value is an object (the whole server answer, or a `detail` that is a list
  or a dictionary). Typical cause: a request the server rejected as malformed, or a proxy or
  identity layer in front of the server answering with its own JSON.
- **A browser error text** such as a `TypeError` naming a failed fetch: a client that passes the
  raw error on (`error = err`) and a request that never reached the server, or an answer that was
  not JSON (an HTML error page from a proxy). The wording comes from the browser, not from the
  code, so it differs between browsers.
- **No message at all**: every client throws only when the error value is not empty
  (`if (error)`, 431 call sites in `src/lib/apis/`). A client using `error = err.detail` whose
  failure has no `detail` (a network failure, an HTML page) therefore throws nothing and returns
  nothing, and most screens then do nothing visible.
- **An empty or odd red pop-up**: the screen was handed a value that is not plain text. For
  example, when a chat answer carries an error, the chat screen passes the answer's `detail`,
  `error.message` or `error` field to the pop-up unchanged
  (`src/lib/components/chat/Chat.svelte:3725-3742`); a field that is empty or is itself an object
  gives a blank or unreadable pop-up, while the error box under the reply still starts with
  `Uh-oh! There was an issue with the response.` (`:3744-3746`).

The fix is not in the browser; the server log for the same minute names the real error
(section 11.4).

### 4.3 Untranslated Strings

A few texts are written in English directly in the code rather than through `$i18n.t(...)`, so they
stay English in every language, for example `Error submitting message`
(`src/lib/components/chat/Messages/Error.svelte:37`) and `An unknown error occurred.`
(`src/routes/(app)/+page.svelte:10`). Section 10 marks them **untranslated**. Thrown texts in
`src/lib/utils/` and `src/lib/apis/` are mostly untranslated too.

### 4.4 Translation Keys, Dotted Keys and Admin Overrides

- **Plain keys.** `$i18n.t('Chat deleted.')` shows `Chat deleted.`; the key is the English text
  (`src/lib/i18n/index.ts:112`). Placeholders appear as `{{name}}` (the code's own i18next form)
  or `{name}` (a value the code joins in directly); see the section 10 preface.
- **Dotted keys.** In scope they are used only for the Settings window's tab titles
  (`src/lib/components/chat/SettingsModal.svelte:190-361`) and the Interface settings labels and
  descriptions (`src/lib/components/common/InterfaceSettings.svelte`); no pop-up or error in scope
  uses a dotted key. Their English text is in `src/lib/i18n/locales/en-US/translation.json`.
  Every `settings.` key falls back to English when the chosen language has no text
  (`src/lib/i18n/settings-translations.ts:3-19`). The Settings tabs this catalogue names resolve
  to **General** (`src/lib/i18n/locales/en-US/translation.json:2870`), **Interface** (`:2985`),
  **Audio** (`:2796`), **Connections** (`:2800`), **Personalization** (`:3007`) and
  **Integrations** (`:3048`, key `settings.personal.tools.title`).
- **Empty translations fall back.** `returnEmptyString: false` makes a language with an empty
  entry fall back to the default language (`src/lib/i18n/index.ts:93`, `:108-114`).
- **Admin overrides.** An administrator can replace the wording of any key; the replacements are
  stored in the `ui.i18n` setting and sent to every browser with the start-up configuration
  (`backend/open_webui/main.py:2316`; `src/routes/+layout.svelte:1254`;
  `src/lib/i18n/settings-translations.ts:10`). **If a reported text matches no row here, an override
  may have changed it**; the live overrides are data and are TO BE CONFIRMED.

### 4.5 Terms Used in Section 10

| Term | Meaning |
|---|---|
| Toast | The pop-up card (section 2.1) |
| Server text | The pop-up prints what the server sent; the wording is in the backend catalogues |
| Success shown although the action failed | A green pop-up the code shows without checking the result; called out where found |
| Inline | Text inside the screen, not a pop-up |
| Thrown | Text an API client or helper hands to the screen, which then shows it as a pop-up |

## 5. Workflows (Step by Step)

### 5.1 Look Up a Message a User Reports

1. Get the exact wording (a screenshot is best), the screen or address, the time, and the
   interface language (**Settings › General**). A pop-up disappears after a few seconds, so ask
   the user to repeat the action and capture it.
2. Search section 10 of this document for a distinctive phrase of four or five words. Placeholders
   are written `{{name}}` in the tables, so search for the fixed words around them.
3. **Found here.** Read the row: the **Support check** column either gives the check or names the
   area document whose section 10 explains the message.
4. **Not found here.** The pop-up is probably server text (section 4.1). Search section 10 of
   [`error-messages-backend-identity-admin-and-platform.md`](error-messages-backend-identity-admin-and-platform.md)
   and
   [`error-messages-backend-chat-content-and-features.md`](error-messages-backend-chat-content-and-features.md).
   Admin and workspace screens are in the sibling front-end catalogue (area 31).
5. **Found nowhere.** Check three things: the user's language is not English (the wording is a
   translation; ask them to switch to English and repeat), an admin translation override changed
   the wording (section 4.4), or the text came from a tool, function or model rather than from the
   application (a pop-up raised by a tool inside a chat, section 10.1).
6. Follow the matching pattern in section 11 if one applies.

### 5.2 Tell Front-End Text From Server Text

| Clue | Usually means |
|---|---|
| The text matches a row in section 10 here | Written by the browser code; the trigger is in the row |
| The text ends with `:/`, mentions an HTTP status, a model provider, a database or a file path | Server text |
| `[object Object]`, a `TypeError`, or no message at all | Not a message; see section 4.2 and 11.4 |
| The text is in English while the rest of the screen is translated | An untranslated string (section 4.3) or server text |

### 5.3 Prepare an Escalation

Send: the exact text; the address (for a chat, the `/c/{id}` address only; do not copy chat
content, which may hold personal or health information); date, time and time zone; browser and
version; the user's role; the steps to repeat; whether it happens for other users. For server text, ask the platform maintainer for the
server log lines at that minute (logs go to standard output only; retention is TO BE CONFIRMED,
see `../tools/ground-truth.md`).

### 5.4 Re-Harvest After a Release (Maintainer)

The catalogue was built by a bulk search of the 414 files in scope for `toast.error(`,
`toast.warning(`, `toast.info(`, `toast.success(`, `toast.message(`, `toast.loading(`,
`toast.custom(`, `ConfirmDialog` and its aliases, `throw`, and every `$i18n.t('...')` key whose
text reads as an error or notice. Repeat the same searches after a release and compare.

## 6. Data Model

Front-end messages are not stored anywhere: a pop-up exists only in the open browser tab.
Exceptions that leave a trace:

| Trace | Where | Evidence |
|---|---|---|
| A failed chat reply keeps its error | The `error` field of the reply in the chat's message history, shown as the error box | `src/lib/components/chat/Chat.svelte:3658-3660`, `:3744-3746` |
| A file whose processing failed keeps the reason | The server stores `status` `failed` and the `error` text on the file record; the browser shows it as the yellow pop-up of section 10.2 | `backend/open_webui/routers/files.py:259-268`; `src/lib/apis/files/index.ts:73-75`; `src/lib/components/chat/MessageInput.svelte:1025-1028` |
| Dismissed update card | Browser storage key `dismissedUpdateToast` (time of dismissal) | `src/routes/(app)/+layout.svelte:372-378`, `:433` |
| Session token removed on expiry | Browser storage key `token` and the `token` cookie are cleared | `src/routes/+layout.svelte:931-950` |
| Admin translation overrides | Setting `ui.i18n` (data) | `backend/open_webui/main.py:2316` |

## 7. Settings and Configuration

| Setting | Effect on messages | Evidence |
|---|---|---|
| `ui.i18n` (admin translation overrides) | Replaces the wording of any message key | section 4.4 |
| Interface language (per user, browser storage `locale`) | Which translation is shown; English is the fallback | `src/routes/+layout.svelte:1254-1266`; `src/lib/i18n/index.ts:88-118` |
| `WEBUI_NAME` (environment) | The name in `{{webUIName}} Backend Required` and in browser notifications | `src/routes/error/+page.svelte:25`; `src/routes/+layout.svelte:1274` |
| Maximum upload size (`file.max_size` in the start-up configuration) | The limit quoted in `File size should not exceed {{maxSize}} MB.` | `src/lib/components/channel/MessageInput.svelte:372` (and the chat composer, section 10.2) |
| Version update check (`enable_version_update_check` feature) and the personal `showUpdateToast` setting | Whether admins see the update card | `src/routes/(app)/+layout.svelte:370-381`, `:428` |
| Personal notification settings | Whether chat and channel notification cards are joined by a browser notification or sound | `src/routes/+layout.svelte:744-770`, `:865-880`; see [`notifications-webhooks-events-and-banners.md`](notifications-webhooks-events-and-banners.md) |
| Feature switches (notes, automations, calendar, channels) and permissions | Whether a screen, and so its messages, can be reached (section 3) | section 3 |

Live values of every setting are data and are TO BE CONFIRMED for production.

## 8. Cron Jobs and Background Processes

None on the server for this area. Three browser-side timers decide when some messages appear:

| Timer | Effect | Evidence |
|---|---|---|
| Disconnect delay | `Connection lost. Reconnecting...` waits 2 seconds after the live connection drops (8 seconds after the tab comes back from the background) and is skipped if the connection returns first | `src/routes/+layout.svelte:128-163` |
| Session check every 15 seconds | Ends the session with `Session expired. Please sign in again.` when the token is within 60 seconds of expiry | `src/routes/+layout.svelte:897`, `:965-977`, `:1231` |
| Heartbeat | Keeps the live connection open (`websocket_heartbeat_interval`, default 30 seconds) | `src/routes/+layout.svelte:217-225` |

## 9. Notifications and Emails

No email (see `../tools/ground-truth.md`). The in-app notification cards (a reply finished in
another chat, a channel message, a calendar reminder) and browser notifications are raised in
`src/routes/+layout.svelte:585-892` and are documented in
[`notifications-webhooks-events-and-banners.md`](notifications-webhooks-events-and-banners.md)
section 9.5. The only fixed texts they add are `Starting now`, `Starting in 1 minute`,
`Starting in {{count}} minutes` and the fallback title `New Chat`
(`src/routes/+layout.svelte:603-606`, `:741`).

## 10. Error, Warning and Notice Messages (Verbatim)

How to read the tables:

- **Severity.** `Error` red pop-up; `Warning` yellow pop-up; `Success` green pop-up; `Info` blue
  pop-up; `Message` plain pop-up (`toast.message`); `Loading` a pop-up with a spinner that later
  turns into another message; `Dialog` a confirmation window (title or text); `Inline` text inside
  the screen (including tooltips); `Thrown` text a helper hands to the screen, shown in the pop-up
  named in the row; `Terminal` text written into a terminal pane. **Untranslated** means the text
  is written in English in the code (section 4.3).
- **Server text.** A row whose message is `{error}` (or `{e}`, `{err}`) prints what the server or
  the browser sent (section 4.1); the trigger names the action, and the wording is in
  [`error-messages-backend-identity-admin-and-platform.md`](error-messages-backend-identity-admin-and-platform.md)
  and
  [`error-messages-backend-chat-content-and-features.md`](error-messages-backend-chat-content-and-features.md).
- **Source.** The first citation is the full path; further lines in the same file are written
  `:line`. One row per distinct message per file.
- **Placeholders.** `{{name}}` is the code's own placeholder (i18next); `{name}` is a value the code
  joins in directly.
- **Already documented.** When an area document's section 10 explains the message, the trigger is
  kept short and the support check reads `See <document>.md section 10`. Rows without such a
  pointer were established from the code for this catalogue.
- **Success shown although the action failed** is marked **(unchecked success)**.
- Labels, buttons and empty-list texts are listed only when a user might report them as a problem.

### 10.1 `chat/` Top-Level Files (Chat Screen, Top Bar, Share, Settings Window)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{error}` (server text) | Error | `src/lib/components/chat/Chat.svelte:496`, `:575`, `:593`, `:1861`, `:2590`, `:3085`, `:3657`, `:3768`, `:3774`, `:4098`, `:4161` | A request failed: approving a waiting tool call (`:496`), answering or dismissing a model's question (`:575`, `:593`), attaching a web page (`:1861`), a message action button (`:2590`), forking (`:3085`), sending the message (`:3657`, replaced by `Uh-oh! There was an issue with the response.` when the error is an object), stopping a reply (`:3768`, `:3774`), moving (`:4098`) or deleting the chat (`:4161`) | Retry once | See `chat-composer-and-message-display.md` section 10; the wording is in the backend catalogues |
| `{detail}`, `{error.message}` or `{error}` of the provider's answer (server text) | Error | `src/lib/components/chat/Chat.svelte:3725-3742` | The model provider or the server answered the chat request with an error; the same text is added to the error box under the reply | Regenerate; try another model | See `chat-composer-and-message-display.md` section 10; section 4.2 for blank pop-ups |
| `Uh-oh! There was an issue with the response.` | Error (pop-up) and Inline (first line of the error box) | `src/lib/components/chat/Chat.svelte:3654`, `:3745` | The chat request failed with an unreadable error, or the answer carried an error | Regenerate | See `chat-composer-and-message-display.md` section 10 |
| Any text sent by a tool, function or the server (`notification` event) | Success, Error, Warning or Info | `src/lib/components/chat/Chat.svelte:1354-1366` | A plugin or the server raised a pop-up during the reply; the text is the plugin's own | Depends on the plugin | See `chat-composer-and-message-display.md` section 10; ask which tool or function was on |
| Title and text chosen by a tool or function (`confirmation` or `input` event); `Confirm your action` and `This action cannot be undone. Do you wish to continue?` when the plugin sends none | Dialog | `src/lib/components/chat/Chat.svelte:1367-1375`, `:1390-1401`, `:4249-4257`; defaults in `src/lib/components/common/ConfirmDialog.svelte:143`, `:153` | A plugin asks the user to confirm or to type a value before it continues | Answer the dialog; the plugin waits for it | The tool or function that sent it (`functions-pipes-filters-actions-and-pipelines.md`) |
| `Confirm Prompt from Embed` | Dialog (title; the text is the prompt) | `src/lib/components/chat/Chat.svelte:1457`, `:1490` | A page embedded in the chat from another site asked to send the shown text | Confirm only if the text is expected | See `chat-composer-and-message-display.md` section 10 |
| `Please enter a prompt` | Error | `src/lib/components/chat/Chat.svelte:3135` | Sending with no text and no file | Type something | See `chat-composer-and-message-display.md` section 10 |
| `Model not selected` | Error; Message for `/model` | `src/lib/components/chat/Chat.svelte:2636`, `:3017-3021`, `:3139` | Sending, or **Generate message pair**, with no model chosen | Pick a model | See `chat-composer-and-message-display.md` section 10 |
| `Model not found` | Error | `src/lib/components/chat/Chat.svelte:2642` | **Generate message pair** with a model that no longer exists | Pick another model | See `chat-composer-and-message-display.md` section 10 |
| `Current model: {currentModels}` (untranslated) | Message | `src/lib/components/chat/Chat.svelte:3017-3021` | `/model` typed with no model id | None | See `chat-composer-and-message-display.md` section 10 |
| `Model not found: {modelId}` (untranslated) | Error | `src/lib/components/chat/Chat.svelte:3030` | `/model {id}` with an id the person cannot use | Check the id in the model picker | See `chat-composer-and-message-display.md` section 10 |
| `Model switched to: {id}` (untranslated) | Success | `src/lib/components/chat/Chat.svelte:3040` | `/model {id}` worked | None | See `chat-composer-and-message-display.md` section 10 |
| `Please connect all required integrations before sending a message` | Warning | `src/lib/components/chat/Chat.svelte:3131` | A default tool of the model needs a sign-in the user has not done | Click the amber chip and connect | See `chat-composer-and-message-display.md` section 10 |
| `Chat Variables have conflicting model definitions` | Error | `src/lib/components/chat/Chat.svelte:3145` | Two selected models define the same chat variable differently | Select one model | See `chat-composer-and-message-display.md` section 10 |
| `Selected models define incompatible Chat Variables.` | Dialog (window `Chat Variables`) | `src/lib/components/chat/Chat.svelte:4183`, `:4196` | Same conflict; the window lists the variables and models | Close and change models | See `chat-composer-and-message-display.md` section 10 |
| `Failed to save chat variables` | Error | `src/lib/components/chat/Chat.svelte:721` | Saving chat variables to the server failed | Retry | See `chat-composer-and-message-display.md` section 10 |
| `You can only chat with a maximum of {{maxCount}} file(s) at a time.` | Error | `src/lib/components/chat/Chat.svelte:3157-3160` | Files on the message plus files already in the chat exceed the admin limit | Remove files or start a new chat | See `chat-composer-and-message-display.md` section 10 |
| `Model {{modelName}} is not vision capable` | Error | `src/lib/components/chat/Chat.svelte:3351-3355` | An image is in the conversation and a chosen model has no vision capability (the message is still sent) | Use a vision model | See `chat-composer-and-message-display.md` section 10 |
| `Failed to create chat` | Error | `src/lib/components/chat/Chat.svelte:3310` | The chat embedded in a note could not create its chat | Retry | See `chat-composer-and-message-display.md` section 10 |
| `Parent message not found` | Error | `src/lib/components/chat/Chat.svelte:3849` | Regenerating a reply whose question is missing from the stored history | Reload the chat | See `chat-composer-and-message-display.md` section 10 |
| `You do not have permission to upload web content.` | Error | `src/lib/components/chat/Chat.svelte:1792` | Attaching a web page (address parameter, `#` or `@`) without the web-upload permission | Ask an admin | See `chat-composer-and-message-display.md` section 10 |
| `File uploaded successfully`; `Error uploading file: {{error}}` with `{{error}}` one of `Failed to fetch file ({status}): {errorText}`, `Retrieved file is empty`, `Created file is empty`, `Server returned null response for file upload` (untranslated) or `Unknown error` | Success; Error | `src/lib/components/chat/Chat.svelte:1776`, `:1782-1786`; inner texts `:1711`, `:1723`, `:1743`, `:1762`, `:1784` | A Google Drive upload path that no screen in v0.11.4 starts (only `Chat.svelte:1889` tests for its event type); `Invalid file data provided` (`:1675`) is thrown before the error handler and shows nothing | None | See `chat-composer-and-message-display.md` section 10 (unused path); the inner texts established here |
| `Context compaction is disabled` | Message | `src/lib/components/chat/Chat.svelte:2958`, `:2993` | `/compact` with the admin switch off | None | See `chat-composer-and-message-display.md` section 10 |
| `No chat to compact` | Message | `src/lib/components/chat/Chat.svelte:2963`, `:2991` | `/compact` on an empty or unsaved chat | None | See `chat-composer-and-message-display.md` section 10 |
| `Wait for the current response to finish before compacting.` | Warning | `src/lib/components/chat/Chat.svelte:2973` | `/compact` while a reply is running | Wait | See `chat-composer-and-message-display.md` section 10 |
| `Compacting context...` | Loading | `src/lib/components/chat/Chat.svelte:2978` | Manual compaction started | Wait | See `chat-composer-and-message-display.md` section 10 |
| `Compacting context` | Loading | `src/lib/components/chat/Chat.svelte:1197` | The server started compacting on its own | Wait | See `chat-composer-and-message-display.md` section 10 |
| `Context compacted` | Success | `src/lib/components/chat/Chat.svelte:1186`, `:2985` | Compaction finished | None | See `chat-composer-and-message-display.md` section 10 |
| `Chat is too short to compact` | Message | `src/lib/components/chat/Chat.svelte:2989` | Nothing old enough to shorten | None | See `chat-composer-and-message-display.md` section 10 |
| `Nothing to compact` | Message | `src/lib/components/chat/Chat.svelte:2994` | The server skipped compaction for another reason | None | See `chat-composer-and-message-display.md` section 10 |
| `Context compaction failed` (or the server's text) | Error | `src/lib/components/chat/Chat.svelte:1181`, `:3000-3001` | Compaction failed | Continue; start a new chat if the model runs out of room | See `chat-composer-and-message-display.md` section 10 |
| `No chat to fork` | Message | `src/lib/components/chat/Chat.svelte:3048` | `/fork` on an empty chat | None | See `chat-composer-and-message-display.md` section 10 |
| `Access prohibited` | Error | `src/lib/components/chat/Chat.svelte:3052` | Forking without the chat import permission | Ask an admin | See `chat-composer-and-message-display.md` section 10 |
| `Wait for the current response to finish before forking.` | Warning | `src/lib/components/chat/Chat.svelte:3062` | Forking while a reply is running | Wait or stop the reply | See `chat-composer-and-message-display.md` section 10 |
| `Forking chat...` | Loading | `src/lib/components/chat/Chat.svelte:3066` | Fork started | Wait | See `chat-composer-and-message-display.md` section 10 |
| `Chat forked` | Success | `src/lib/components/chat/Chat.svelte:3080` | The new chat was created and opened | None | See `chat-composer-and-message-display.md` section 10 |
| `Failed to fork chat` | Error | `src/lib/components/chat/Chat.svelte:3082` | The server returned no new chat | Retry | See `chat-composer-and-message-display.md` section 10 |
| `Chat moved successfully` | Success | `src/lib/components/chat/Chat.svelte:4107` | Move from the chat's menu worked | None | See `chat-composer-and-message-display.md` section 10 |
| `Failed to move chat` | Error | `src/lib/components/chat/Chat.svelte:4110` | Move attempted without a chat or folder | Retry | See `chat-composer-and-message-display.md` section 10 |
| `Chat archived.` | Success | `src/lib/components/chat/Chat.svelte:4121` | Archive from the chat's menu worked | None | See `chat-composer-and-message-display.md` section 10 |
| `Failed to archive chat.` | Error | `src/lib/components/chat/Chat.svelte:4124` | Archive failed (any error) | Retry | See `chat-composer-and-message-display.md` section 10 |
| `Delete chat?`; `This will delete {title}.` | Dialog | `src/lib/components/chat/Chat.svelte:4239`, `:4245` | Delete from the chat's menu or shortcut | Confirm or cancel | See `chat-composer-and-message-display.md` section 10 |
| `Chat deleted.` | Success | `src/lib/components/chat/Chat.svelte:4157` | The chat was deleted | None | See `chat-composer-and-message-display.md` section 10 |
| `Use Web Search?`; `Your query will be sent to the configured web search provider.` (or the admin's own text) | Dialog | `src/lib/components/chat/Chat.svelte:4222-4225` | Web search used while the admin requires confirmation | **Continue** or **Cancel** | See `web-search-and-web-loading.md` section 10 |
| `No conversation to save` | Error | `src/lib/components/chat/Chat.svelte:4349` | **Save Chat** on an empty temporary chat | None | See `chat-composer-and-message-display.md` section 10 |
| `Conversation saved successfully` | Success | `src/lib/components/chat/Chat.svelte:4377` | A temporary chat was saved | None | See `chat-composer-and-message-display.md` section 10 |
| `Failed to save conversation` | Error | `src/lib/components/chat/Chat.svelte:4381` | Saving a temporary chat failed | Copy the text out first, then retry | See `chat-composer-and-message-display.md` section 10 |
| `Read only` | Inline | `src/lib/components/chat/Chat.svelte:4436` | Viewing a chat that belongs to someone else | None | See `chat-composer-and-message-display.md` section 10 |
| `No HTML, CSS, or JavaScript content found.` | Inline | `src/lib/components/chat/Artifacts.svelte:274` | The artifacts panel was opened for an answer with nothing it can show | Close the panel | See `chat-composer-and-message-display.md` section 10 |
| `Trial License`; `You are currently using a trial license. Please contact support to upgrade your license.` | Inline (banner) | `src/lib/components/chat/Navbar.svelte:280-283` | The licence data in the start-up configuration says trial | Report to the platform maintainer | See `chat-composer-and-message-display.md` section 10 |
| `License Error`; `Exceeded the number of seats in your license. Please contact support to increase the number of seats.` | Inline (banner) | `src/lib/components/chat/Navbar.svelte:292-295` | More users than the licence's seats | Report to the platform maintainer | See `chat-composer-and-message-display.md` section 10 |
| `This chat won't appear in history and your messages will not be saved.` | Inline (tooltip) | `src/lib/components/chat/Placeholder.svelte:118`; `src/lib/components/chat/ChatPlaceholder.svelte:98` | Hovering the temporary-chat label | None | See `chat-composer-and-message-display.md` section 10 |
| `No chat history` | Inline | `src/lib/components/chat/EmbeddedChatHistoryDropdown.svelte:96` | The chat list beside a note has no chats yet | None | See `notes.md` section 10 |
| `Auth required` | Inline (badge) | `src/lib/components/chat/ToolServersModal.svelte:22` | A tool server in the list needs the user to sign in | Connect the server | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/chat/SettingsModal.svelte:442` | Saving a personal setting failed | Retry | See `user-settings-and-personalisation.md` section 10 |
| `Settings saved successfully!` | Success (unchecked success on some tabs) | `src/lib/components/chat/SettingsModal.svelte:461`, `:796`, `:804`, `:815`, `:822`, `:829`, `:836`, `:848`, `:860`, `:882`, `:888`, `:894`, `:900`, `:906` | A tab of the Settings window reported a save; on the personal Interface, Audio and Personalization tabs and the admin Interface tab it can appear although the save failed | Reopen the tab and check the value stuck | See `user-settings-and-personalisation.md` section 10 and `admin-settings-panels.md` section 10 |
| `Redirecting you to Open WebUI Community` | Success | `src/lib/components/chat/ShareChatModal.svelte:45` | **Share to Open WebUI Community** (only when community sharing is on) | None | See `chat-conversations-history-and-organisation.md` section 10; external sharing of chats is a privacy question |
| `Access updated` | Success | `src/lib/components/chat/ShareChatModal.svelte:81` | The share's access list was saved | None | See `chat-conversations-history-and-organisation.md` section 10 |
| `{e}` (server text) | Error | `src/lib/components/chat/ShareChatModal.svelte:83` | Saving the share's access list failed | Retry | See `chat-conversations-history-and-organisation.md` section 10 |
| `Messages you send after creating your link won't be shared. Users with the URL will be able to view the shared chat.` | Inline | `src/lib/components/chat/ShareChatModal.svelte:152-153` | Share dialog before a link exists | None | See `chat-conversations-history-and-organisation.md` section 10 |
| `Copied shared chat URL to clipboard!` | Success (unchecked success) | `src/lib/components/chat/ShareChatModal.svelte:223` | **Copy Link**. The pop-up does not wait for the copy: in Safari it appears before the link is created and also when creating it or copying fails (`:197-218`); elsewhere it appears whether or not the copy worked (`:220`) | Paste to check; if nothing pastes, retry | See `chat-conversations-history-and-organisation.md` section 10; this catalogue established the unchecked success |
| `{error}` (server text) | Error | `src/lib/components/chat/Tags.svelte:29` | Adding a tag to the chat failed | Retry | See `chat-conversations-history-and-organisation.md` section 10 |
| `[Connection closed]` (untranslated) | Terminal | `src/lib/components/chat/XTerminal.svelte:99` | The live terminal connection ended | Reopen the terminal | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `[Terminal connection failed]` (untranslated) | Terminal | `src/lib/components/chat/XTerminal.svelte:104` | The terminal connection could not be opened or broke | Check the terminal server in **Settings › Integrations** | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `[{error}]`, for example `[Error: Terminal request failed ({status})]` | Terminal | `src/lib/components/chat/XTerminal.svelte:106-110` | Starting the terminal session or its connection threw an error (the session request goes through `src/lib/apis/terminal/index.ts:130`) | Retry | Server log of the terminal server |
| `[Earlier output omitted]` (untranslated) | Terminal | `src/lib/components/chat/TerminalDock.svelte:79` | The terminal server reports that a running command's earlier output was cut (the dock asks for the last 1,000 entries, `:72`) | None | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `{cause}`, usually `Terminal request failed ({status})` after the word `Error:` | Inline (red line above the terminal) | `src/lib/components/chat/TerminalDock.svelte:95`, `:261-263`; text from `src/lib/apis/terminal/index.ts:130` | Polling the terminal's running commands failed | Check the terminal server | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |

### 10.2 `chat/MessageInput.svelte` and `chat/MessageInput/` (Composer, Attachments, Voice and Calls)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Failed to read clipboard contents` | Error | `src/lib/components/chat/MessageInput.svelte:286` | A prompt with the clipboard variable and clipboard access refused | Allow clipboard access in the browser | See `chat-composer-and-message-display.md` section 10 |
| `Location access not allowed` | Error | `src/lib/components/chat/MessageInput.svelte:316` | A prompt with the location variable and location refused | Allow location in the browser | See `chat-composer-and-message-display.md` section 10 |
| `You do not have permission to upload files.` | Error; Inline (tooltip) | `src/lib/components/chat/MessageInput.svelte:920`; `src/lib/components/chat/MessageInput/InputMenu.svelte:191`, `:217`, `:273`, `:306`, `:337`, `:367` | Adding a file without the file-upload permission, or hovering a greyed item of the **+** menu | Ask an admin | See `chat-composer-and-message-display.md` section 10 |
| `Model(s) do not support file upload` | Error; Inline (tooltip) | `src/lib/components/chat/MessageInput.svelte:927`; `src/lib/components/chat/MessageInput/InputMenu.svelte:189`, `:215`, `:271`, `:304`, `:335`, `:365` | A selected model lacks the file-upload capability | Choose another model | See `chat-composer-and-message-display.md` section 10 |
| `You do not have permission to upload web content.` | Inline (tooltip) | `src/lib/components/chat/MessageInput/InputMenu.svelte:248` | Hovering the greyed **Attach Webpage** | Ask an admin | See `chat-composer-and-message-display.md` section 10 |
| `You cannot upload an empty file.` | Error | `src/lib/components/chat/MessageInput.svelte:950` | A file of 0 bytes | Check the file | See `chat-composer-and-message-display.md` section 10 |
| `Failed to upload file.` | Error (terminal uploads); not shown for normal uploads | `src/lib/components/chat/MessageInput.svelte:987-988`, `:1041` | An upload returned nothing. For a terminal upload the pop-up appears; for a normal upload the file just disappears from the composer with no message (`:1039-1043`) | Retry | See `chat-composer-and-message-display.md` section 10; the silent case is section 11.5 |
| `{e}` (server text) | Error | `src/lib/components/chat/MessageInput.svelte:994`, `:1047` | Uploading a file failed (terminal or normal upload) | Retry; check size and type | See `files-uploads-and-storage.md` section 10 |
| `{uploadedFile.error}` (server text) | Warning | `src/lib/components/chat/MessageInput.svelte:1027` | The file was stored but its processing reported a problem; the file stays attached | Check the answer really uses the file | See `chat-composer-and-message-display.md` section 10 and `files-uploads-and-storage.md` section 10 |
| `Failed to extract content from the file: {{error}}` | Error | `src/lib/components/chat/MessageInput.svelte:1056-1058` | Temporary chat: the browser could not read the file itself; `{{error}}` is one of the reader texts in section 10.16 | Use a saved chat or another format | See `chat-composer-and-message-display.md` section 10 |
| `Failed to extract content from the file.` | Error | `src/lib/components/chat/MessageInput.svelte:1065` | Same, when the reader returned nothing | As above | See `chat-composer-and-message-display.md` section 10 |
| `You can only chat with a maximum of {{maxCount}} file(s) at a time.` | Error | `src/lib/components/chat/MessageInput.svelte:1094` | Attaching more files than the admin limit | Attach fewer | See `chat-composer-and-message-display.md` section 10 |
| `File size should not exceed {{maxSize}} MB.` | Error | `src/lib/components/chat/MessageInput.svelte:1118` | A file above the admin size limit | Use a smaller file | See `chat-composer-and-message-display.md` section 10 |
| `Selected model(s) do not support image inputs` | Error | `src/lib/components/chat/MessageInput.svelte:1128` | An image while no selected model has vision | Choose a vision model | See `chat-composer-and-message-display.md` section 10 |
| `Cannot create an empty note.` | Error | `src/lib/components/chat/MessageInput.svelte:1201` | A note-from-composer function that nothing calls in v0.11.4 | None | See `chat-composer-and-message-display.md` section 10 |
| `File not found.` | Error | `src/lib/components/chat/MessageInput.svelte:1728` | The file picker returned no file | Pick again | See `chat-composer-and-message-display.md` section 10 |
| `Error accessing Google Drive: {{error}}` | Error | `src/lib/components/chat/MessageInput.svelte:2255` | The Google Drive picker failed; `{{error}}` is one of the picker texts in section 10.16 | Retry; report if it repeats | See `chat-composer-and-message-display.md` section 10 and `files-uploads-and-storage.md` section 10 |
| `Permission denied when accessing microphone: {{error}}`; `Permission denied when accessing microphone` | Error | `src/lib/components/chat/MessageInput.svelte:2642-2644`, `:2660` | Starting dictation with the microphone blocked | Allow the microphone in the browser | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Select only one model to call` | Error | `src/lib/components/chat/MessageInput.svelte:2680` | Starting a voice call with several models selected | Select one model | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Call feature is not supported when using Web STT engine` | Error | `src/lib/components/chat/MessageInput.svelte:2686` | Starting a call while speech-to-text uses the browser engine | Change the engine in **Settings › Audio** | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Permission denied when accessing media devices` | Error | `src/lib/components/chat/MessageInput.svelte:2723` | Starting a call with microphone access blocked | Allow the microphone | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Please enter a valid URL.` | Error | `src/lib/components/chat/MessageInput/AttachWebpageModal.svelte:30` | **Attach Webpage** with an address that does not parse | Correct the address | See `chat-composer-and-message-display.md` section 10 |
| `Oops! Looks like the URL is invalid. Please double-check and try again.` | Error | `src/lib/components/chat/MessageInput/Commands/AtCommands.svelte:206`; `src/lib/components/chat/MessageInput/Commands/Knowledge.svelte:217`, `:245` | A typed `#` or `@` web address that is not valid | Correct the address | See `chat-composer-and-message-display.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/chat/MessageInput/CallOverlay.svelte:172`; `src/lib/components/chat/MessageInput/VoiceRecording.svelte:191` | Transcribing speech failed on the server (call or dictation) | Retry; check the audio settings | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `{error}` (browser voice engine) | Error | `src/lib/components/chat/MessageInput/CallOverlay.svelte:528` | The in-browser Kokoro voice could not speak a sentence during a call (for example `KokoroTTS Worker is not initialized yet.`, section 10.18) | Wait for the voice to load, or change the voice engine | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Error accessing media devices.` | Error | `src/lib/components/chat/MessageInput/VoiceRecording.svelte:235` | The microphone could not be opened for dictation | Allow the microphone | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Error starting recording.` | Error | `src/lib/components/chat/MessageInput/VoiceRecording.svelte:294` | Recording could not start | Retry | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Speech recognition error: {{error}}` | Error | `src/lib/components/chat/MessageInput/VoiceRecording.svelte:356` | The browser's speech recognition reported an error | Retry or change the engine | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `OAuth session disconnected` | Success | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:608` | **Disconnect OAuth** on a tool worked | None | See `chat-composer-and-message-display.md` section 10 |
| `Failed to disconnect` | Error | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:615` | Disconnecting a tool's sign-in failed | Retry | See `chat-composer-and-message-display.md` section 10 |
| `Empty message` | Inline | `src/lib/components/chat/MessageInput/QueuedMessageItem.svelte:70` | A queued message with no text and no files | None | See `chat-composer-and-message-display.md` section 10 |
| `Upload failed` | Inline | `src/lib/components/chat/MessageInput/QueuedMessageItem.svelte:76` | A queued message holds a file whose upload failed | Remove and re-attach the file | See `chat-composer-and-message-display.md` section 10 |
| `No files in this knowledge base.` | Inline | `src/lib/components/chat/MessageInput/InputMenu/Knowledge.svelte:273` | Opening a knowledge base with no files from the **+** menu | None | See `chat-composer-and-message-display.md` section 10 |
| `No knowledge bases found.` | Inline | `src/lib/components/chat/MessageInput/InputMenu/Knowledge.svelte:198` | The **+** menu's knowledge list is empty or matches nothing | Check that a knowledge base is shared with the person | See `chat-composer-and-message-display.md` section 10 |
| `No tools found`; `No skills found`; `No notes found`; `No chats found`; `No files found` | Inline | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:546`, `:678`; `src/lib/components/chat/MessageInput/InputMenu/Notes.svelte:120`; `src/lib/components/chat/MessageInput/InputMenu/Chats.svelte:119`; `src/lib/components/chat/MessageInput/InputMenu/Files.svelte:110` | Empty lists in the composer menus | None | See `chat-composer-and-message-display.md` section 10 |

### 10.3 `chat/Messages.svelte` and `chat/Messages/` (Questions, Answers, Code, Rendering)

Status lines, the error box text and tool-call cards inside an answer are owned by the planned
in-chat catalogue (area 32); the rows below are the pop-ups, dialogs and fixed texts these files
show.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Model not selected` | Error | `src/lib/components/chat/Messages.svelte:320` | Sending or saving an edited message while no model is chosen | Pick a model | See `chat-composer-and-message-display.md` section 10 |
| `Copying to clipboard was successful!` | Success | `src/lib/components/chat/Messages/UserMessage.svelte:74`; `src/lib/components/chat/Messages/ResponseMessage.svelte:247` | **Copy** under a question or an answer worked | None | See `chat-composer-and-message-display.md` section 10 |
| `Please enter a message or attach a file.` | Error | `src/lib/components/chat/Messages/UserMessage.svelte:99` | Saving or sending an edited question that is empty | Type text or keep a file | See `chat-composer-and-message-display.md` section 10 |
| `Delete message?` | Dialog | `src/lib/components/chat/Messages/UserMessage.svelte:125`; `src/lib/components/chat/Messages/ResponseMessage.svelte:684` | **Delete** under a question or an answer | Confirm; there is no undo | See `chat-composer-and-message-display.md` section 10 |
| `No content to speak` | Info | `src/lib/components/chat/Messages/ResponseMessage.svelte:275`, `:325` | **Read Aloud** on an answer with no plain text | None | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `{error}` (server text or the browser voice engine) | Error | `src/lib/components/chat/Messages/ResponseMessage.svelte:352`, `:371` | **Read Aloud** failed: the in-browser voice (`:352`) or the server's speech request (`:371`) | Retry; check **Settings › Audio** | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/chat/Messages/ResponseMessage.svelte:499`, `:561`, `:597` | Saving a thumbs rating failed: loading the chat (`:499`, typically `We could not find what you're looking for :/`), creating (`:561`) or updating the feedback | Reload and rate again | See `evaluations-feedback-and-analytics.md` section 10 |
| `Thanks for your feedback!` | Success (unchecked success) | `src/lib/components/chat/Messages/RateComment.svelte:101` | **Save** in the rating form; shown before the server answers (`:92-102`) | If an error pop-up follows, the rating was not saved | See `evaluations-feedback-and-analytics.md` section 10 |
| `This response was generated by "{{model}}"` | Success | `src/lib/components/chat/Messages/RateComment.svelte:77-81` | The rating form opens on an arena (blind comparison) answer | None | See `evaluations-feedback-and-analytics.md` section 10 |
| `Copied to clipboard` | Success (unchecked success) | `src/lib/components/chat/Messages/Markdown/KatexRenderer.svelte:58`; `src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens/CodespanToken.svelte:23` | Clicking a formula or inline code; the pop-up does not check whether the copy worked | Paste to check | See `chat-composer-and-message-display.md` section 10 |
| `{err}`, for example `Tool call has already been resolved.` (server text) | Error | `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte:136`; `src/lib/components/chat/Messages/StructuredOutputRenderer.svelte:60` | **Allow** or **Deny** on a tool call failed on the server | Reload the chat | See `chat-composer-and-message-display.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/chat/Messages/CodeBlock.svelte:150` | **Run** on a code block executed on the server (Jupyter) failed | Retry | See `code-execution-and-interpreter.md` section 10 |
| `Execution Time Limit Exceeded` (untranslated) | Inline (code output) | `src/lib/components/chat/Messages/CodeBlock.svelte:263` | In-browser **Run** took longer than 60 seconds (`:269`) | Simplify the code | See `code-execution-and-interpreter.md` section 10 |
| `Failed to render diagram`; `Failed to render visualization` | Inline (red box) | `src/lib/components/chat/Messages/CodeBlock.svelte:375`, `:387` | A Mermaid or Vega block the drawing library cannot draw | Ask the model to correct the diagram | See `chat-composer-and-message-display.md` section 10; for blocked outside resources see section 10.16 |
| `ERROR` | Inline (label) | `src/lib/components/chat/Messages/CodeExecutionModal.svelte:79` | The code-execution window shows a run's error output under this heading | Read the error text below it | See `code-execution-and-interpreter.md` section 10 |
| `Download failed` | Error | `src/lib/components/chat/Messages/TerminalOutputFile.svelte:220` | **Download** on a terminal file failed | Retry | See `chat-composer-and-message-display.md` section 10 |
| `Preview failed` | Inline | `src/lib/components/chat/Messages/TerminalOutputFile.svelte:139`, `:150`, `:155`, `:169`, `:174`, `:193`, `:204` | The terminal file could not be fetched or read | Retry | See `chat-composer-and-message-display.md` section 10 |
| `Terminal unavailable` | Inline | `src/lib/components/chat/Messages/TerminalOutputFile.svelte:280` | The terminal that produced the file is not selected or not reachable | Select that terminal | See `chat-composer-and-message-display.md` section 10 |
| `No preview available` | Inline | `src/lib/components/chat/Messages/TerminalOutputFile.svelte:313` | The file type cannot be previewed | Use **Download** | See `chat-composer-and-message-display.md` section 10 |
| `Must be a JSON array`; `Invalid JSON` | Inline | `src/lib/components/chat/Messages/OutputEditView.svelte:56`, `:59` | The JSON view of an answer's structured output holds something other than a valid list | Fix the JSON or cancel | See `chat-composer-and-message-display.md` section 10 |
| `No output items` | Inline | `src/lib/components/chat/Messages/OutputEditView.svelte:365` | Every block was removed in the answer's visual editor | **Cancel** to keep the original | See `chat-composer-and-message-display.md` section 10 |
| `Error submitting message` (untranslated) | Inline (error box) | `src/lib/components/chat/Messages/Error.svelte:37` | An answer's stored error has no readable text | Regenerate | See `chat-composer-and-message-display.md` section 10 |
| `No sources found`; `No source available`; `No distance available`; `No search query generated` | Inline (status history) | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:112`, `:117-118`, `:24` | A knowledge or web search step found nothing, or a source has no address or score | Rephrase or check the knowledge base | See `chat-completion-pipeline-and-generation-tasks.md` section 10 (`No sources found`, `No search query generated`); the other two established here |

### 10.4 `chat/ModelSelector.svelte` and `chat/ModelSelector/` (Model Picker)

Downloading, unloading and deleting models from the picker are offered to admins only.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Choose a model before saving...` | Error | `src/lib/components/chat/ModelSelector.svelte:29` | **Set as default** while one model slot is empty | Pick a model in every slot | See `user-settings-and-personalisation.md` section 10 |
| `Default model updated` | Success | `src/lib/components/chat/ModelSelector.svelte:35` | The default model list was saved | None | See `user-settings-and-personalisation.md` section 10 |
| `Copied link to clipboard`; `Failed to copy link` | Success; Error | `src/lib/components/chat/ModelSelector/ModelItem.svelte:44`, `:46` | **Copy link** on a model; the result of the copy decides which | None | See `workspace-models-and-model-access.md` section 10 |
| `Model '{{modelTag}}' is already in queue for downloading.` | Error | `src/lib/components/chat/ModelSelector/Selector.svelte:465-469`, `:598` | Starting a download of a model already downloading | Wait | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Maximum of 3 models can be downloaded simultaneously. Please try again later.` | Error | `src/lib/components/chat/ModelSelector/Selector.svelte:473-474`, `:606` | A fourth download while three run | Wait for one to finish | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/chat/ModelSelector/Selector.svelte:481` | Starting an Ollama download failed | Check the model name | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `{data.status}` (Ollama progress text, for example `success`) | Success | `src/lib/components/chat/ModelSelector/Selector.svelte:539` | Each progress step Ollama reports without a byte count | None | Text from Ollama, not from MedIT GPT |
| `{error}` or `Server connection failed` | Error | `src/lib/components/chat/ModelSelector/Selector.svelte:558`, `:708`; fallback in `src/lib/apis/openai/index.ts:3-14` | The download stream reported an error, or a provider download failed; `Download failed` (untranslated, `:679`) when the provider gives no reason | Retry; check the provider | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Model '{{modelName}}' has been successfully downloaded.` | Success | `src/lib/components/chat/ModelSelector/Selector.svelte:565-569`, `:694` | The download finished | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Download canceled` | Error | `src/lib/components/chat/ModelSelector/Selector.svelte:578` | The Ollama download stream ended without success: cancelled by the admin, **and also after any download error** (the error pop-up comes first) | Retry | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `{{model}} download has been canceled` | Success | `src/lib/components/chat/ModelSelector/Selector.svelte:776`, `:783-787` | Cancelling a running download | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Error unloading model: {{error}}`; `Model unloaded successfully` | Error; Success | `src/lib/components/chat/ModelSelector/Selector.svelte:793`, `:797` | **Unload** on a loaded model | Retry | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Delete Model`; `Are you sure you want to delete **{{modelName}}**?` | Dialog | `src/lib/components/chat/ModelSelector/Selector.svelte:893` | **Delete** on a model in the picker | Confirm or cancel | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Error deleting model: {{error}}`; `Model {{modelName}} deleted successfully` | Error; Success | `src/lib/components/chat/ModelSelector/Selector.svelte:824`, `:831`, `:838-840` | Deleting a workspace model (`:824`) or an Ollama model (`:831`) | Retry | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `No models available`; `Connect to an AI provider to start chatting` | Inline | `src/lib/components/chat/ModelSelector/Selector.svelte:1047-1057` | An admin opens the picker and no model exists at all; the **Manage Connections** link opens the admin connections tab | Admin: add a connection | See `model-connections-openai-ollama-and-direct.md` section 10 and section 11 there |
| `No results found` | Inline | `src/lib/components/chat/ModelSelector/Selector.svelte:1075` | The search matches no model, or (for a non-admin) no model is available to the person at all | Clear the search; if the list is always empty, report it | See `workspace-models-and-model-access.md` section 11 (model access) |
| `Downloading "{{searchValue}}"`; `Downloading "{{name}}"` | Inline | `src/lib/components/chat/ModelSelector/Selector.svelte:1136`, `:1220` | A download is offered or running | None | See `model-connections-openai-ollama-and-direct.md` section 10 |

### 10.5 `chat/FileNav.svelte`, `chat/FileNav/` and `chat/PyodideFileNav.svelte` (File Panels)

The terminal file panel works against an Open Terminal server; the Pyodide panel against the
browser's own Python file system.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Start the chat to use this terminal.` | Inline | `src/lib/components/chat/FileNav.svelte:1557` | The terminal needs a saved chat before files can be shown | Send a first message | See `files-uploads-and-storage.md` section 10 |
| `No Terminal connection configured.`; `Add your Open Terminal URL and API key in Settings → Integrations.` | Inline | `src/lib/components/chat/FileNav.svelte:1569`, `:1572` | No terminal is selected or set up | Set up the terminal, or ask an admin | See `files-uploads-and-storage.md` section 10 |
| `Failed to load directory. Check your Terminal connection in Settings → Integrations.` (untranslated) | Inline | `src/lib/components/chat/FileNav.svelte:742-743` | Listing the folder returned nothing | Check the terminal settings | See `files-uploads-and-storage.md` section 10 |
| `Failed to load folder` | Error | `src/lib/components/chat/FileNav.svelte:799` | Expanding a folder in the tree failed | Retry | See `files-uploads-and-storage.md` section 10 |
| `Failed to search files` | Inline | `src/lib/components/chat/FileNav.svelte:553` | Searching file contents returned no answer | Retry | See `files-uploads-and-storage.md` section 10 |
| `Error previewing file: {{error}}` (with `Unknown error` when there is no text) | Inline | `src/lib/components/chat/FileNav.svelte:939-941` | An Office file could not be shown in the preview; `{{error}}` can be the untranslated `Preview failed` (`:888`, `:929`) | Download the file instead | See `files-uploads-and-storage.md` section 10 |
| `Preparing download...` | Loading | `src/lib/components/chat/FileNav.svelte:983`, `:1361` | Download of one item or of a selection started | Wait | See `files-uploads-and-storage.md` section 10 |
| `Download failed` | Error | `src/lib/components/chat/FileNav.svelte:991`, `:1366` | The terminal returned no file | Retry | See `files-uploads-and-storage.md` section 10 |
| `Upload failed: {error}`, with `{error}` such as `Unable to read a dropped file or folder.` or `Invalid upload path: {path}` (untranslated) | Error | `src/lib/components/chat/FileNav.svelte:1102`; inner texts `:1037`, `:1087`, `:1099` | Dropping or uploading files into the terminal failed; when the terminal refuses a file the text is that file's path | Retry with fewer or smaller files | See `files-uploads-and-storage.md` section 10 |
| `Uploading...` | Inline | `src/lib/components/chat/FileNav.svelte:2003` | An upload is running | Wait | See `files-uploads-and-storage.md` section 10 |
| `{result.error}` (terminal server text) | Error | `src/lib/components/chat/FileNav.svelte:1227`, `:1269` | Moving or renaming an item failed on the terminal | Retry | See `files-uploads-and-storage.md` section 10 |
| `Moved {{name}}`; `Renamed to {{name}}` | Success | `src/lib/components/chat/FileNav.svelte:1230`, `:1271` | Move or rename worked | None | See `files-uploads-and-storage.md` section 10 |
| `Deleted {{ok}} of {{total}} items` | Success when at least one was deleted, otherwise Error | `src/lib/components/chat/FileNav.svelte:1339-1341` | Bulk delete finished; fewer than the total means some failed | Check what is left | See `files-uploads-and-storage.md` section 10 |
| `Confirm your action`; `This action cannot be undone. Do you wish to continue?` | Dialog (defaults) | `src/lib/components/chat/FileNav.svelte:1530-1542` | Deleting an item or a selection in the terminal panel | Confirm or cancel | See `files-uploads-and-storage.md` section 10 |
| `Copied to clipboard` | Success | `src/lib/components/chat/FileNav.svelte:1739` | Copying a path worked | None | See `files-uploads-and-storage.md` section 10 |
| `Path copied` | Success | `src/lib/components/chat/FileNav/FileEntryRow.svelte:411` | **Copy path** on an item worked | None | See `files-uploads-and-storage.md` section 10 |
| `This folder is empty` | Inline | `src/lib/components/chat/FileNav.svelte:2012` | The folder has no items | None | See `files-uploads-and-storage.md` section 10 |
| `No matches` | Inline | `src/lib/components/chat/FileNav.svelte:1891` | A search of file contents found nothing | Change the search | See `files-uploads-and-storage.md` section 10 |
| `No text differences` | Inline | `src/lib/components/chat/FileNav/FileCompare.svelte:249` | **Compare** found the two files identical (or identical apart from ignored spaces) | None | See `files-uploads-and-storage.md` section 10 |
| `Your browser does not support the video tag.`; `Your browser does not support the audio tag.` | Inline | `src/lib/components/chat/FileNav/FilePreview.svelte:316`, `:322` | The browser cannot play the media file in the preview | Download the file | See `files-uploads-and-storage.md` section 10 |
| `No kernel` | Inline (tooltip) | `src/lib/components/chat/FileNav/NotebookView.svelte:260` | A notebook preview has no running Jupyter kernel | None, unless the person expected to run cells | Established here |
| `No data` | Inline | `src/lib/components/chat/FileNav/SqliteView.svelte:247` | A SQLite table or query returned no rows | None | See `files-uploads-and-storage.md` section 10 |
| `Read-only` | Inline (badge) | `src/lib/components/chat/FileNav/FileEntryRow.svelte:323`; `src/lib/components/chat/FileNav/FileNavToolbar.svelte:138` | The item or folder cannot be changed | None | See `files-uploads-and-storage.md` section 10 |
| `JSON parse error: {{error}}` (`Invalid JSON` when there is no text); `Could not read file.` | Inline | `src/lib/components/chat/FileNav/FilePreview.svelte:245`, `:474`, `:509` | The preview of a JSON file or of any file failed | Download the file | See `files-uploads-and-storage.md` section 10 |
| `{error}`, or `Failed to open database` / `Query failed` | Inline | `src/lib/components/chat/FileNav/SqliteView.svelte:49`, `:85`, `:102` | A SQLite file could not be opened or a query failed | Check the query | See `files-uploads-and-storage.md` section 10 |
| `No servers detected` | Inline | `src/lib/components/chat/FileNav/PortList.svelte:93` | No web server is running on the terminal | None | See `files-uploads-and-storage.md` section 10 |
| `No files yet. Upload files or run Python code to create them.` | Inline | `src/lib/components/chat/PyodideFileNav.svelte:456` | The browser Python file system is empty | None | See `code-execution-and-interpreter.md` section 10 |
| `Failed to list directory`; `Failed to read file`; `[Binary file: {size} bytes]` (untranslated) | Inline | `src/lib/components/chat/PyodideFileNav.svelte:167`, `:197`, `:201` | The browser Python worker could not list or read; a binary file is shown by size only | Reload the page | See `code-execution-and-interpreter.md` section 10 |
| `Delete {{name}}`; `Are you sure you want to delete this?` | Dialog | `src/lib/components/chat/PyodideFileNav.svelte:351-356` | Deleting a file in the browser Python panel | Confirm or cancel | See `code-execution-and-interpreter.md` section 10 |

### 10.6 `chat/ChatControls.svelte`, `chat/ChatControls/` and `chat/Controls/` (Chat Controls Panel)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{error}` (server text) | Error | `src/lib/components/chat/Controls/Valves.svelte:92`, `:107` | Saving a tool's (`:92`) or a function's (`:107`) personal valves failed | Check the values; retry | See `functions-pipes-filters-actions-and-pipelines.md` section 10 and `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Valves updated` | Success | `src/lib/components/chat/Controls/Valves.svelte:98`, `:112` | Personal valves were saved | None | See `chat-composer-and-message-display.md` section 10 |

`ChatControls.svelte` and `ChatControls/` show no pop-up or error text of their own (bulk search;
only button labels such as `Close embed`).

### 10.7 `chat/Placeholder/`, `chat/Overview.svelte`, `chat/Overview/` and `chat/ContentRenderer/`

`Overview` and `ContentRenderer` show no pop-up or error text (bulk search). The folder landing
screen in `Placeholder/` does:

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Folder name cannot be empty.` | Error | `src/lib/components/chat/Placeholder/FolderTitle.svelte:47`, `:144` | Saving or creating a folder with no name | Type a name | See `chat-conversations-history-and-organisation.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/chat/Placeholder/FolderTitle.svelte:61`, `:76`, `:92`, `:102`, `:115`, `:128`, `:156` | Updating, reloading, changing the icon of, deleting, exporting or creating a folder failed | Retry | See `chat-conversations-history-and-organisation.md` section 10 |
| `Folder updated successfully` | Success | `src/lib/components/chat/Placeholder/FolderTitle.svelte:73`, `:99` | Folder name, settings or icon saved | None | See `chat-conversations-history-and-organisation.md` section 10 |
| `Folder deleted successfully` | Success | `src/lib/components/chat/Placeholder/FolderTitle.svelte:121` | Folder deleted | None | See `chat-conversations-history-and-organisation.md` section 10 |
| `Folder created successfully` | Success | `src/lib/components/chat/Placeholder/FolderTitle.svelte:161` | Sub-folder created | None | See `chat-conversations-history-and-organisation.md` section 10 |
| `Delete folder?`; `Are you sure you want to delete "{{NAME}}"?`; `Delete all contents inside this folder` (tick box) | Dialog | `src/lib/components/chat/Placeholder/FolderTitle.svelte:185`, `:195-197`, `:204` | **Delete** on the folder screen; with the box ticked the folder's chats are deleted too | Confirm only after checking the box choice | See `chat-conversations-history-and-organisation.md` section 10 |
| `No chats found` | Inline | `src/lib/components/chat/Placeholder/ChatList.svelte:172` | The folder screen's chat list is empty | None | See `chat-composer-and-message-display.md` section 10 |

### 10.8 `layout/` (Sidebar, Folders, Search, Chats and Files Windows, User Menu, Overlays)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{error}` (server text) | Error | `src/lib/components/layout/Sidebar.svelte:349`, `:471`, `:863`, `:1382`, `:1462`, `:1482`, `:1561` | Creating a folder (`:349`), **Mark all as read** (`:471`), creating a channel (`:863`), or dragging a folder or chat onto another place in the sidebar (`:1382`, `:1462`, `:1482`, `:1561`) failed | Retry | See `chat-conversations-history-and-organisation.md` section 10 (channels: `channels-and-direct-messages.md`) |
| `Folder name cannot be empty.` | Error | `src/lib/components/layout/Sidebar.svelte:312`; `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:462`, `:656` | Creating or renaming a folder with no name | Type a name | See `chat-conversations-history-and-organisation.md` section 10 |
| `Access prohibited` | Error | `src/lib/components/layout/Sidebar.svelte:488`, `:1434`, `:1537`; `src/lib/components/layout/Sidebar/ChatItem.svelte:226`; `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:247` | Importing chats, dropping a chat file, or cloning a chat without the chat import permission | Ask an admin | See `chat-conversations-history-and-organisation.md` section 10 |
| `Invalid file format.` | Error | `src/lib/components/layout/Sidebar.svelte:524` | **Import** with a file that is not a chat export | Use a JSON export from MedIT GPT | See `chat-conversations-history-and-organisation.md` section 10 |
| `Please select at least one user for Direct Message channel.` | Error | `src/lib/components/layout/Sidebar.svelte:845` | Creating a direct message with nobody chosen | Choose someone | See `channels-and-direct-messages.md` section 10 |
| `Channel name cannot be empty.` | Error | `src/lib/components/layout/Sidebar.svelte:850` | Creating a channel with no name | Type a name | See `channels-and-direct-messages.md` section 10 |
| `Channel name must be less than 128 characters` | Error | `src/lib/components/layout/Sidebar/ChannelModal.svelte:60` | A channel name of 128 characters or more | Shorten it | See `channels-and-direct-messages.md` section 10 |
| Empty red pop-up (`error.message` of a text) | Error | `src/lib/components/layout/Sidebar/ChannelItem.svelte:69`; `src/lib/components/layout/Sidebar/ChannelModal.svelte:117` | **Update** or **Delete** in **Edit Channel** failed; the code prints a part the server text does not have (section 4.2) | Retry; report the time | See `channels-and-direct-messages.md` section 10 |
| `Channel updated successfully` | Success | `src/lib/components/layout/Sidebar/ChannelItem.svelte:73` | **Edit Channel** saved | None | See `channels-and-direct-messages.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/layout/Sidebar/ChannelItem.svelte:222` | Changing a direct message's visibility in the sidebar failed | Retry | See `channels-and-direct-messages.md` section 10 |
| `Delete`; `Are you sure you want to delete this channel?` | Dialog | `src/lib/components/layout/Sidebar/ChannelModal.svelte:317` | **Delete** in **Edit Channel** | Confirm or cancel | See `channels-and-direct-messages.md` section 10 |
| `Channel deleted successfully` | Success | `src/lib/components/layout/Sidebar/ChannelModal.svelte:121` | The channel was deleted | None | See `channels-and-direct-messages.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/layout/Sidebar/ChatItem.svelte:191`, `:237`, `:255`, `:302`, `:497` | Marking a chat unread, cloning, deleting, moving, or generating a title failed | Retry | See `chat-conversations-history-and-organisation.md` section 10 |
| `Title cannot be an empty string.` | Error | `src/lib/components/layout/Sidebar/ChatItem.svelte:208`; `src/lib/components/layout/SearchModal.svelte:169` | Renaming a chat to nothing | Type a title | See `chat-conversations-history-and-organisation.md` section 10 |
| `Chat archived.`; `Chat unarchived.` | Success | `src/lib/components/layout/Sidebar/ChatItem.svelte:289`; `src/lib/components/layout/SearchModal.svelte:110` | Archiving from the sidebar or search; search also reports un-archiving | None | See `chat-conversations-history-and-organisation.md` section 10 |
| `Failed to archive chat.` | Error | `src/lib/components/layout/Sidebar/ChatItem.svelte:292`; `src/lib/components/layout/SearchModal.svelte:112` | Archiving failed (any error) | Retry | See `chat-conversations-history-and-organisation.md` section 10 |
| `Chat moved successfully`; `Failed to move chat` | Success; Error | `src/lib/components/layout/Sidebar/ChatItem.svelte:312`, `:315`; `src/lib/components/layout/SearchModal.svelte:147` | Moving a chat to a folder | Retry if it failed | See `chat-conversations-history-and-organisation.md` section 10 |
| `Delete chat?`; `This will delete {title}.` | Dialog | `src/lib/components/layout/Sidebar/ChatItem.svelte:565`; `src/lib/components/layout/SearchModal.svelte:560` | **Delete** on a chat in the sidebar or the search window | Confirm or cancel | See `chat-conversations-history-and-organisation.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/layout/SearchModal.svelte:77`, `:89`, `:118`, `:139`, `:238` | Cloning, marking unread, deleting, moving, or generating a title from the search window failed | Retry | See `chat-conversations-history-and-organisation.md` section 10 |
| `Failed to load chat` | Error | `src/lib/components/layout/SearchModal.svelte:196` | Generating a title in search when the chat cannot be loaded | Reload | See `chat-conversations-history-and-organisation.md` section 10 |
| `Failed to load chat preview` | Error (search); Inline (hover preview) | `src/lib/components/layout/SearchModal.svelte:384`; `src/lib/components/layout/Sidebar/ChatHoverPreview.svelte:75` | The preview of a chat could not be loaded | Open the chat directly | See `chat-conversations-history-and-organisation.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:135`, `:231`, `:261`, `:273`, `:449`, `:476`, `:493`, `:508`, `:565`, `:602`, `:640`, `:668` | A folder action failed: mark read, drop a folder, import or drop chats, delete, rename, reload, expand, list its chats, open, export, or create a sub-folder | Retry | See `chat-conversations-history-and-organisation.md` section 10 |
| `Folder deleted successfully`; `Folder updated successfully`; `Folder created successfully` | Success | `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:455`, `:489`, `:673` | Folder deleted, renamed, or sub-folder created | None | See `chat-conversations-history-and-organisation.md` section 10 |
| `Delete folder?`; `Are you sure you want to delete "{{NAME}}"?`; `Delete all contents inside this folder` | Dialog | `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:679` | **Delete** on a sidebar folder | Check the tick box choice, then confirm | See `chat-conversations-history-and-organisation.md` section 10 |
| `Please wait until all files are uploaded.` | Error | `src/lib/components/layout/Sidebar/Folders/FolderModal.svelte:41` | Saving folder settings while its files still upload | Wait | See `chat-conversations-history-and-organisation.md` section 10 |
| `Maximum number of files per folder is {{max}}.` | Error | `src/lib/components/layout/Sidebar/Folders/FolderModal.svelte:49` | More files than the limit on a folder | Remove files | See `chat-conversations-history-and-organisation.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/layout/Sidebar/Folders/FolderModal.svelte:69` | Loading the folder for its settings window failed | Retry | See `chat-conversations-history-and-organisation.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/layout/ChatsModal.svelte:77` | Deleting a chat from a chats window (for example **Shared Chats**) failed | Retry | See `chat-conversations-history-and-organisation.md` section 10 |
| `Confirm your action`; `This action cannot be undone. Do you wish to continue?` | Dialog (defaults) | `src/lib/components/layout/ChatsModal.svelte:88-96`; `src/lib/components/layout/FilesModal.svelte:191-199` | Deleting a chat from a chats window, or a file from the files window | Confirm or cancel | See `chat-conversations-history-and-organisation.md` and `files-uploads-and-storage.md` section 10 |
| `Share link copied to clipboard.` | Success | `src/lib/components/layout/ChatsModal.svelte:355` | **Copy Share Link** in the shared chats list | None | See `chat-conversations-history-and-organisation.md` section 10 |
| `No chats found.` (or the caller's own empty text) | Inline | `src/lib/components/layout/ChatsModal.svelte:538` | A chats window with an empty list | None | Established here: the window shows the caller's placeholder when given one |
| `{error}` (server text) | Error | `src/lib/components/layout/SharedChatsModal.svelte:92`, `:113` | Unsharing one chat (`:92`) or all chats (`:113`) failed | Retry | See `chat-conversations-history-and-organisation.md` section 10 |
| `Chat unshared successfully.`; `Failed to unshare chat.` | Success; Error | `src/lib/components/layout/SharedChatsModal.svelte:97`, `:101` | **Unshare** on one shared chat | Retry if it failed | See `chat-conversations-history-and-organisation.md` section 10 |
| `Unshare All`; `Are you sure you want to unshare all shared chats? This will remove all share links.` | Dialog | `src/lib/components/layout/SharedChatsModal.svelte:128-131` | **Unshare All Shared Chats** | Confirm only if every link should stop working | See `chat-conversations-history-and-organisation.md` section 10 |
| `All shared chats have been unshared.` | Success | `src/lib/components/layout/SharedChatsModal.svelte:109` | Unshare all finished | None | See `chat-conversations-history-and-organisation.md` section 10 |
| `File deleted successfully.`; `{error}` (server text) | Success; Error | `src/lib/components/layout/FilesModal.svelte:129`, `:134` | Deleting a file from the files window | Retry if it failed | See `files-uploads-and-storage.md` section 10 |
| `No files found` | Inline | `src/lib/components/layout/FilesModal.svelte:336` | The files window list is empty | None | See `files-uploads-and-storage.md` section 10 |
| `No results found`; `No chats`; `Empty` | Inline | `src/lib/components/layout/ChatsModal.svelte:242`; `src/lib/components/layout/SearchModal.svelte:646`; `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:947`; `src/lib/components/layout/Sidebar/SharedFolderItem.svelte:166` | A search in the chats or search window matches nothing; an open folder has no chats; a shared folder is empty | None | See `chat-conversations-history-and-organisation.md` section 10 |
| `Copied to clipboard` | Success | `src/lib/components/layout/Navbar/Menu.svelte:436` | Copying the chat from the top-bar menu worked | None | See `chat-conversations-history-and-organisation.md` section 10 |
| `Status cleared successfully`; `Failed to clear status` | Success; Error | `src/lib/components/layout/Sidebar/UserMenu.svelte:205`, `:208` | The clear button beside the person's status in the user menu. The error appears when the server returns nothing; a server error text shows no pop-up at all, because the call is not caught (`:199-202`) | Retry | Established here; the status is shown to other people in channels and direct messages (`src/lib/components/channel/Messages/Message/UserStatus.svelte:76-88`; `src/lib/components/layout/Sidebar/ChannelItem.svelte:177-186`) |
| `{error}` (server text), then `Failed to update status` | Error | `src/lib/components/layout/Sidebar/UserStatusModal.svelte:36`, `:45` | Saving a new status in **Update your status** failed; both pop-ups appear one after the other | Retry | Established here |
| `Status updated successfully` | Success | `src/lib/components/layout/Sidebar/UserStatusModal.svelte:42` | The new status was saved | None | Established here |
| `Account Activation Pending`; `Contact Admin for WebUI Access` (or the admin's own title) | Inline (overlay title) | `src/lib/components/layout/Overlay/AccountPending.svelte:31-36` | Signed in with the `pending` role | Wait for an admin; **Check Again** reloads | See `authentication-and-sign-in.md` section 10 |
| `Your account status is currently pending activation.`; `To access the WebUI, please reach out to the administrator. Admins can manage user statuses from the Admin Panel.` (or the admin's own text) | Inline (overlay text) | `src/lib/components/layout/Overlay/AccountPending.svelte:43-50` | Same overlay | As above | See `authentication-and-sign-in.md` section 10 |
| `A new version (v{{LATEST_VERSION}}) is now available.`; `Update for the latest features and improvements.` | Inline (update card, admins) | `src/lib/components/layout/UpdateInfoToast.svelte:20-25` | The version check found a newer upstream release | Platform maintainer decides on upgrades; the link goes to upstream release notes | See `notifications-webhooks-events-and-banners.md` section 10 |

### 10.9 `channel/` (Channels and Direct Messages)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{error}` (server text) | Error | `src/lib/components/channel/Channel.svelte:257`; `src/lib/components/channel/Thread.svelte:155` | Sending a message in the channel or in a thread failed | Retry; copy the text out first | See `channels-and-direct-messages.md` section 10 |
| `You do not have permission to send messages in this channel.` | Inline (composer replaced) | `src/lib/components/channel/Channel.svelte:410` | The person can read but not write in the channel | Ask an admin for write access | See `channels-and-direct-messages.md` section 10 |
| `You do not have permission to send messages in this thread.` | Inline | `src/lib/components/channel/Thread.svelte:253` | The same, in the thread panel | As above | See `channels-and-direct-messages.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/channel/Messages.svelte:146`, `:162`, `:187`, `:224`, `:250` | Deleting, editing, pinning a message, or adding or removing a reaction failed | Retry | See `channels-and-direct-messages.md` section 10 |
| `Delete Message`; `Are you sure you want to delete this message?` | Dialog | `src/lib/components/channel/Messages/Message.svelte:158` | **Delete** on a channel message | Confirm; deletion is permanent | See `channels-and-direct-messages.md` section 10 |
| `Unknown User` | Inline | `src/lib/components/channel/Messages/Message.svelte:354`, `:362` | A quoted message's sender has no name | None | See `channels-and-direct-messages.md` section 10 |
| `This channel was created on {{createdAt}}. This is the very beginning of the {{channelName}} channel.` | Inline | `src/lib/components/channel/Messages.svelte:106-107` | Shown above the oldest message | None | See `channels-and-direct-messages.md` section 10 |
| `Failed to read clipboard contents`; `Location access not allowed` | Error | `src/lib/components/channel/MessageInput.svelte:109`, `:137` | A saved prompt with the clipboard or location variable and the browser refused | Allow access, or type the text | See `channels-and-direct-messages.md` section 10 |
| `File size should not exceed {{maxSize}} MB.`; `You cannot upload an empty file.`; `File not found.` | Error | `src/lib/components/channel/MessageInput.svelte:372`, `:455`, `:703` | A file over the size limit, an empty file, or the picker returned nothing | Choose another file | See `channels-and-direct-messages.md` section 10 |
| `{uploadedFile.error}` (server text) | Warning | `src/lib/components/channel/MessageInput.svelte:486` | The file was stored but processing reported a problem | Check the file | See `files-uploads-and-storage.md` section 10 |
| `{e}` (server text) | Error | `src/lib/components/channel/MessageInput.svelte:502` | The upload failed | Retry | See `files-uploads-and-storage.md` section 10 |
| `Permission denied when accessing microphone: {{error}}`; `Permission denied when accessing microphone` | Error | `src/lib/components/channel/MessageInput.svelte:1033-1035`, `:1051` | Voice input with the microphone blocked | Allow the microphone | See `channels-and-direct-messages.md` section 10 |
| `{error}` (server text); `Member removed successfully`; `Failed to remove member` | Error; Success; Error | `src/lib/components/channel/ChannelInfoModal.svelte:48`, `:53`, `:56` | Removing a member of a group channel; the second error follows the server text, or appears alone when nobody was removed | Reopen the member list | See `channels-and-direct-messages.md` section 10 |
| `{error}` (server text); `Members added successfully`; `Failed to add members` | Error; Success; Error | `src/lib/components/channel/ChannelInfoModal/AddMembersModal.svelte:28`, `:33`, `:37` | **Add Members** | Retry if it failed | See `channels-and-direct-messages.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/channel/ChannelInfoModal/UserList.svelte:68` | Loading the member list failed | Reopen the window | See `channels-and-direct-messages.md` section 10 |
| `No users were found.` | Inline | `src/lib/components/channel/ChannelInfoModal/UserList.svelte:284` | The member search matched nobody, or the list could not load | Change the search | See `channels-and-direct-messages.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/channel/PinnedMessagesModal.svelte:33`, `:121` | Loading pinned messages, or unpinning from that window, failed | Retry | See `channels-and-direct-messages.md` section 10 |
| `No pinned messages` | Inline | `src/lib/components/channel/PinnedMessagesModal.svelte:102` | The channel has no pinned messages, or loading them failed after an error pop-up | None | See `channels-and-direct-messages.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/channel/WebhooksModal.svelte:55`, `:70`, `:83` | Creating, saving or deleting a channel webhook failed | Retry | See `channels-and-direct-messages.md` section 10 |
| `Saved`; `Deleted` | Success | `src/lib/components/channel/WebhooksModal.svelte:68`, `:81` | Webhook saved or deleted | None | See `channels-and-direct-messages.md` section 10 |
| `Confirm your action`; `This action cannot be undone. Do you wish to continue?` | Dialog (defaults) | `src/lib/components/channel/WebhooksModal.svelte:97` | **Delete** on a webhook | Confirm or cancel | See `channels-and-direct-messages.md` section 10 |
| `No webhooks yet` | Inline | `src/lib/components/channel/WebhooksModal.svelte:160` | No webhooks, or the list could not load (that error is not shown) | Escalate if webhooks were expected | See `channels-and-direct-messages.md` section 10 |
| `Copied` | Success (unchecked success) | `src/lib/components/channel/WebhookItem.svelte:77` | **Copy URL** on a webhook; the pop-up does not wait for the copy (`:73-77`) | Paste to check | See `channels-and-direct-messages.md` section 10; the address must be handled as a secret |

### 10.10 `notes/` (Notes List and Note Editor)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{error}` (server text) | Error | `src/lib/components/notes/NoteEditor.svelte:181`, `:217`, `:537`, `:551`, `:699`, `:740`, `:766`, `:783`, `:806`, `:813`, `:1007`, `:1236`; `src/lib/components/notes/Notes.svelte:94`, `:110`, `:117`, `:156`, `:393`; `src/lib/components/notes/utils.ts:125` | A note action failed: loading or saving the note, attaching a file, opening, creating or deleting its side chat, PDF download, deleting, sharing, copying, importing, or creating a note | Retry; for saving, copy the text out first | See `notes.md` section 10 |
| `Only txt and md files are allowed` (untranslated) | Error | `src/lib/components/notes/Notes.svelte:137` | Importing a file that is not `.txt` or `.md` | Convert the file | See `notes.md` section 10 |
| `Imported notes successfully` | Success (unchecked success) | `src/lib/components/notes/Notes.svelte:391` | The import finished, also when a file was refused or failed earlier | Check each note appears | See `notes.md` section 10 |
| `Delete note?`; `This will delete {title}.` | Dialog | `src/lib/components/notes/Notes.svelte:401`; `src/lib/components/notes/NoteEditor.svelte:1016` | **Delete** in a note's menu | Confirm or cancel | See `notes.md` section 10 |
| `Note deleted successfully`; `Failed to delete note` | Success; Error | `src/lib/components/notes/NoteEditor.svelte:819`, `:822` | Deleting from the editor; the error follows the server text | Ask the owner if read-only | See `notes.md` section 10 |
| `Copied link to clipboard`; `Failed to copy link` | Success; Error | `src/lib/components/notes/Notes.svelte:686`, `:688`, `:773`, `:775`; `src/lib/components/notes/NoteEditor.svelte:1225`, `:1227` | **Copy link**; the copy result decides which | Copy the address bar instead | See `notes.md` section 10 |
| `Copied to clipboard` | Success | `src/lib/components/notes/NoteEditor.svelte:1241` | **Copy to clipboard** worked | None | See `notes.md` section 10 |
| `Failed to generate title` | Error | `src/lib/components/notes/NoteEditor.svelte:422` | The model's answer to **Generate** title was not usable | Retry or type a title | See `notes.md` section 10 |
| `You cannot upload an empty file.`; `File size should not exceed {{maxSize}} MB.` | Error | `src/lib/components/notes/NoteEditor.svelte:506`, `:622` | Attaching an empty or too large file to a note | Choose another file | See `notes.md` section 10 |
| `{uploadedFile.error}` (server text) | Warning | `src/lib/components/notes/NoteEditor.svelte:532` | The file was stored but processing reported a problem | Read the warning | See `notes.md` section 10 |
| `Saved` | Success (unchecked success) | `src/lib/components/notes/NoteEditor.svelte:1005` | A change in the note's sharing was sent; shown also when the server dropped grants the person may not give | Reload the note to see what was kept | See `notes.md` section 10 |
| `Permission denied when accessing microphone: {{error}}`; `Permission denied when accessing microphone` | Error | `src/lib/components/notes/NoteEditor.svelte:1166`, `:1181` | **Record** with the microphone blocked | Allow the microphone | See `notes.md` section 10 |
| `Read-Only Access` | Inline | `src/lib/components/notes/NoteEditor.svelte:1270` | The person cannot edit this note | Ask the owner for write access | See `notes.md` section 10 |
| `No content` | Inline | `src/lib/components/notes/Notes.svelte:809` | A note card with an empty body | None | See `notes.md` section 10 |
| `No Notes`; `Create your first note from the Create menu.` | Inline | `src/lib/components/notes/Notes.svelte:863`, `:867` | No notes match the view, or the list failed to load (that error is not shown) | Check the view menu; reload | See `notes.md` section 10 |

### 10.11 `common/` (Shared Dialogs, Previews, Editors and Settings Widgets)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Confirm your action`; `This action cannot be undone. Do you wish to continue?` | Dialog (defaults) | `src/lib/components/common/ConfirmDialog.svelte:143`, `:153` | Any confirmation whose screen gives no title or text of its own (sections 10.5, 10.8, 10.9) | Read what was clicked before confirming | Section 2.1 |
| `{error}` (server text or the browser formatter) | Error | `src/lib/components/common/CodeEditor.svelte:188` | **Format** in a code editor failed: on the server for admins, in the browser's Python for others (`:183-186`); browser failures read `Pyodide worker error` or `Execution Time Limit Exceeded` (untranslated, `:159`, `:176`) or the formatter's own error output | Fix the code's syntax, then retry | See `code-execution-and-interpreter.md` section 10 |
| `Code formatted successfully` | Success | `src/lib/components/common/CodeEditor.svelte:201` | Formatting worked | None | See `code-execution-and-interpreter.md` section 10 |
| `Failed to download image` | Error | `src/lib/components/common/ImagePreview.svelte:163` | Downloading a remote image from the image viewer failed (the hidden reason, `Failed to download image: {status}`, `:141`, goes to the browser console) | Open the image and save it from the browser | See `files-uploads-and-storage.md` section 10 |
| `Failed to load PDF.` (untranslated) | Inline | `src/lib/components/common/PDFViewer.svelte:433`, `:476-478` | The PDF could not be fetched (an `HTTP {status}` answer, `:421`) or read | Download the file instead | See `files-uploads-and-storage.md` section 10 |
| `Failed to load DOCX file. Please try downloading it instead.` | Inline | `src/lib/components/common/DocxPreview.svelte:160`; `src/lib/components/common/FileItemModal.svelte:180` | A Word file preview failed | Download the file | See `files-uploads-and-storage.md` section 10 |
| `Failed to load Excel/CSV file. Please try downloading it instead.` | Inline | `src/lib/components/common/FileItemModal.svelte:157` | A spreadsheet preview failed | Download the file | See `files-uploads-and-storage.md` section 10 |
| `Failed to load PPTX file. Please try downloading it instead.` | Inline | `src/lib/components/common/FileItemModal.svelte:196` | A PowerPoint preview failed | Download the file | See `files-uploads-and-storage.md` section 10 |
| `No content available` | Inline | `src/lib/components/common/FileItemModal.svelte:548`, `:574`, `:586` | The file window has no extracted text to show | Check the file was processed | See `files-uploads-and-storage.md` section 10 |
| `Image unavailable` | Inline | `src/lib/components/common/Image.svelte:61` | A picture in a chat or note could not be loaded | Reload; the file may be gone or not shared with the person | See `files-uploads-and-storage.md` section 10 |
| `Copied to clipboard` | Success (unchecked success) | `src/lib/components/common/SVGPanZoom.svelte:71` | Copying a diagram from the zoom view; the pop-up does not check the copy | Paste to check | See `chat-composer-and-message-display.md` section 10 |
| `{error.message}` (the browser's location error) | Error | `src/lib/components/common/InterfaceSettings.svelte:175` | Turning on **Allow User Location** (dotted key, English text at `src/lib/i18n/locales/en-US/translation.json:2874`) while the browser refuses location; the switch turns itself off again | Allow location for the site | See `user-settings-and-personalisation.md` section 10 |
| `User location successfully retrieved.` | Success | `src/lib/components/common/InterfaceSettings.svelte:181` | The location was read and stored | None; the location is personal data | See `user-settings-and-personalisation.md` section 10 |
| `Clipboard write permission denied. Please check your browser settings to grant the necessary access.` | Error | `src/lib/components/common/InterfaceSettings.svelte:218-222` | Turning on **Auto-Copy Response to Clipboard** (`src/lib/i18n/locales/en-US/translation.json:2883`) without clipboard access; the switch turns itself off | Allow clipboard access | See `user-settings-and-personalisation.md` section 10 |
| `{error}`, one of the dictionary texts in section 10.16, or a JSON reading error | Error | `src/lib/components/common/TranslationTable.svelte:75` | An admin uploads a translation file that is not valid | Correct the file | See `admin-settings-panels.md` section 10 |
| `Allow {{NAME}}?`; `Input needed`; `Denied {{NAME}}` | Inline (tool card) | `src/lib/components/common/ToolCallDisplay.svelte:243-249` | A tool call waits for approval or an answer, or was denied | **Allow** or **Deny**; answer the card | See `chat-composer-and-message-display.md` section 10 (area 32 owns the card) |
| `*required` | Inline | `src/lib/components/common/Valves.svelte:32` | A tool or function setting must be filled in | Fill it in | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `No valves` | Inline | `src/lib/components/common/Valves.svelte:242` | The tool or function has no settings | None | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `Experimental`; `This is an experimental feature, it may not function as expected and is subject to change at any time.` | Inline (badge and tooltip) | `src/lib/components/common/ExperimentalBadge.svelte:12-14` | A setting marked experimental | Use with care | See `memories.md` section 10 |
| `No results found`; `No results` | Inline | `src/lib/components/common/Selector.svelte:83`; `src/lib/components/common/TranslationTable.svelte:168`; `src/lib/components/common/EmojiPicker.svelte:184` | A search in a list or emoji picker matches nothing | Change the search | None |

### 10.12 `automations/` (Automation Editor and Pickers)

The automations list page and the single-automation page are route files (section 10.15).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{err}` (server text) | Error | `src/lib/components/automations/AutomationEditor.svelte:152`, `:166`, `:178`, `:191` | Switching an automation on or off (`:152`), **Run now** (`:166`), reloading after a save (`:178`) or deleting (`:191`) failed; scheduling refusals such as a too-frequent schedule come from the server | Read the text; adjust the schedule | See `automations-calendar-and-timers.md` section 10 |
| `Automation triggered` | Success | `src/lib/components/automations/AutomationEditor.svelte:170` | **Run now** accepted; the run itself happens in the background | Check the run history after a moment | See `automations-calendar-and-timers.md` section 10 |
| `Deleted {{name}}` | Success | `src/lib/components/automations/AutomationEditor.svelte:195` | The automation was deleted | None | See `automations-calendar-and-timers.md` section 10 |
| `Delete automation?`; `This will delete {name}.` | Dialog | `src/lib/components/automations/AutomationEditor.svelte:269` | **Delete** in the editor | Confirm or cancel | See `automations-calendar-and-timers.md` section 10 |
| `No runs yet` | Inline | `src/lib/components/automations/AutomationEditor.svelte:367` | The automation has never run | Wait for the schedule or **Run now** | See `automations-calendar-and-timers.md` section 10 |
| `No results found` | Inline | `src/lib/components/automations/DestinationDropdown.svelte:260`, `:307`; `src/lib/components/automations/FolderDropdown.svelte:144`; `src/lib/components/automations/ModelDropdown.svelte:125` | A picker's search matches nothing | Change the search | None |

### 10.13 `calendar/` (Calendar Event and Calendar Windows)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Title is required`; `Date is required` | Error | `src/lib/components/calendar/CalendarEventModal.svelte:120`, `:125` | Saving an event without a title or a date | Fill them in | See `automations-calendar-and-timers.md` section 10 |
| `Event created`; `Event updated`; `Event deleted` | Success | `src/lib/components/calendar/CalendarEventModal.svelte:170`, `:152`, `:187` | The event was saved or deleted | None | See `automations-calendar-and-timers.md` section 10 |
| `{err}` (server text) | Error | `src/lib/components/calendar/CalendarEventModal.svelte:176`, `:191` | Saving (`:176`) or deleting (`:191`) an event failed | Retry | See `automations-calendar-and-timers.md` section 10 |
| `Delete Event`; `This action cannot be undone. Do you wish to continue?` | Dialog | `src/lib/components/calendar/CalendarEventModal.svelte:347` | **Delete** on an event | Confirm or cancel | See `automations-calendar-and-timers.md` section 10 |
| `Delete Calendar`; `This will permanently delete the calendar "{{name}}" and all its events. This action cannot be undone.` | Dialog | `src/lib/components/calendar/CalendarSidebar.svelte:94-98` | **Delete calendar** | Confirm only if every event should go | See `automations-calendar-and-timers.md` section 10 |
| `Name is required` | Error | `src/lib/components/calendar/CreateCalendarModal.svelte:41` | Creating a calendar without a name | Type a name | See `automations-calendar-and-timers.md` section 10 |
| `Calendar created`; `{err}` (server text) | Success; Error | `src/lib/components/calendar/CreateCalendarModal.svelte:52`, `:57` | Creating a calendar worked or failed | Retry if it failed | See `automations-calendar-and-timers.md` section 10 |

### 10.14 `playground/` and `app/` (Playground and App Sidebar)

The playground is linked for admins only (section 3). `app/AppSidebar.svelte` shows no message
(bulk search).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Please select a model.` | Error | `src/lib/components/playground/Chat.svelte:91` | **Run** in the playground chat without a model | Choose a model | See `model-connections-openai-ollama-and-direct.md` section 10 |
| No message (silent failure) | None | `src/lib/components/playground/Chat.svelte:106-140`; `src/lib/components/playground/Completions.svelte:42-57` | A playground chat or completion request that fails leaves an empty or unchanged answer and shows nothing; the client throws only on network errors, which the playground does not catch (`src/lib/apis/openai/index.ts:392-419`) | Check the model in the main chat, which does report errors | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Chat exported successfully` | Success | `src/lib/components/playground/Chat.svelte:282`, `:302` | **Download** as JSON or plain text | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Please enter a prompt` | Error | `src/lib/components/playground/Images.svelte:69` | **Run** in the playground images tab with no prompt | Type a prompt | See `image-generation-and-editing.md` section 10 |
| `{error}` (server text) | Error | `src/lib/components/playground/Images.svelte:94` | Generating or editing an image failed | Read the text; check the image settings | See `image-generation-and-editing.md` section 10 |
| `Failed to download image` | Error | `src/lib/components/playground/Images.svelte:111` | Clicking a generated image could not fetch it | Retry | See `image-generation-and-editing.md` section 10 |

### 10.15 `src/routes/` (Start-Up, Sign-In, Shared Chats and Route Pages)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Connection lost. Reconnecting...` | Warning | `src/routes/+layout.svelte:162` | The live connection dropped and did not come back within 2 seconds (longer after the tab returns from the background, section 8); replies, notes and channels stop updating meanwhile | Wait for `Reconnected`; if it repeats, check the network | See `authentication-and-sign-in.md` section 10 and `notes.md` section 10; pattern in section 11.1 |
| `Reconnected` | Success | `src/routes/+layout.svelte:194` | The live connection is back, only after the warning above was shown | Check the last change was kept | See `authentication-and-sign-in.md` section 10 |
| Notification card: the chat's title (or `New Chat`) with a preview of the reply; the sender and channel with the message; or the event title with `Starting now`, `Starting in 1 minute` or `Starting in {{count}} minutes` | Card | `src/routes/+layout.svelte:600-615`, `:741`, `:770`, `:865-892` | A reply finished in another chat or tab, a channel message arrived, or a calendar reminder is due | Click the card to open it | See `notifications-webhooks-events-and-banners.md` section 10 |
| `Session expired. Please sign in again.` | Error | `src/routes/+layout.svelte:948` | The sign-in token is within 60 seconds of expiry (checked every 15 seconds and when the tab becomes active), or a server request answered 401 and a re-check of the session also answered 401; the person is signed out | Sign in again | See `authentication-and-sign-in.md` section 10; pattern in section 11.3 |
| `{error}` (server text) | Error | `src/routes/+layout.svelte:1282` | Loading the signed-in user at start-up failed; the stored token is removed and the sign-in page follows | Sign in again | See `authentication-and-sign-in.md` section 10 |
| `{{webUIName}} Backend Required`; `Oops! You're using an unsupported method (frontend only). Please serve the WebUI from the backend.` | Inline (full screen) | `src/routes/error/+page.svelte:25`, `:29-31`; redirect from `src/routes/+layout.svelte:1317` | The browser could not load the server's start-up configuration (`/api/config`): server down, restarting, or a proxy problem. The help links point to upstream GitHub and Discord | Wait a minute and press **Check Again** | See `authentication-and-sign-in.md` section 10; pattern in section 11.2 |
| `{status}: {message}` | Inline (error page) | `src/routes/+error.svelte:8` | SvelteKit could not show a page, for example an address that does not exist | Go back to `/` | Pages and addresses: section 2.2 |
| `{error}` from the address, or `An unknown error occurred.` (untranslated) | Error | `src/routes/(app)/+page.svelte:8-12` | The home page was opened with an `error` parameter, typically after a failed single sign-on or a redirect from another screen | Note the text and the time | See `chat-composer-and-message-display.md` section 10 and `sso-oauth-oidc-and-scim.md` section 10 |
| `{error}` from the address | Error | `src/routes/auth/+page.svelte:168-171` | The sign-in page was opened with an `error` parameter (a sign-in method sends the person back with its reason) | Note the text; try again | See `sso-oauth-oidc-and-scim.md` section 10 |
| `{error}` (server text) | Error | `src/routes/auth/+page.svelte:75`, `:92`, `:102`, `:142` | Password sign-in (`:75`), sign-up (`:92`), LDAP sign-in (`:102`) or the single sign-on token check (`:142`) failed | Check the details; see the backend catalogue | See `authentication-and-sign-in.md` section 10 and `error-messages-backend-identity-admin-and-platform.md` section 10 |
| `Passwords do not match.` | Error | `src/routes/auth/+page.svelte:85` | Sign-up with two different passwords | Type them again | See `authentication-and-sign-in.md` section 10 |
| `You're now logged in.` | Success | `src/routes/auth/+page.svelte:50` | Sign-in finished | None | See `authentication-and-sign-in.md` section 10 |
| `{WEBUI_NAME} does not make any external connections, and your data stays securely on your locally hosted server.` (with `Get started with {{WEBUI_NAME}}`) | Inline | `src/routes/auth/+page.svelte:276`, `:286-292` | Shown only during first-run onboarding, before any account exists (`backend/open_webui/main.py:2250-2252`). It is upstream wording; whether it is accurate for this deployment is TO BE CONFIRMED | None | See `authentication-and-sign-in.md` section 10 |
| `Access prohibited` | Error | `src/routes/s/[id]/+page.svelte:150` | **Clone Chat** on a shared chat without the chat import permission | Ask an admin | See `chat-conversations-history-and-organisation.md` section 10 |
| `{error}` (server text) | Error | `src/routes/s/[id]/+page.svelte:157` | Cloning the shared chat failed | Retry | See `chat-conversations-history-and-organisation.md` section 10 |
| `Failed to connect to {{URL}} OpenAPI tool server` | Error | `src/routes/(app)/+layout.svelte:96-99` | At every app load, one of the person's own tool servers did not answer | Fix or switch off the server in **Settings › Integrations** | See `user-settings-and-personalisation.md` section 10; pattern in section 11.7 |
| `Failed to connect to {{URL}} terminal server` | Error | `src/routes/(app)/+layout.svelte:129-132` | The same for an enabled terminal server | As above | See `user-settings-and-personalisation.md` section 10 |
| `Failed to load Interface settings` | Error | `src/routes/(app)/+layout.svelte:233` | Loading the person's settings at start-up failed; the app stops loading further data | Reload; escalate if it repeats | See `user-settings-and-personalisation.md` section 10 |
| `Execution Time Limit Exceeded` (untranslated) | Code output | `src/routes/+layout.svelte:352` | Python the server asked the browser to run took longer than 60 seconds (`:373`); the text is sent back as the error output | Simplify the code | See `code-execution-and-interpreter.md` section 10 |
| `Tool Server Not Found` (untranslated) | Tool result | `src/routes/+layout.svelte:556` | The server asked the browser to call one of the person's tool servers that is not loaded | Check **Settings › Integrations** | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `An error occurred while fetching the completion` (untranslated) | Error box (direct connection) | `src/routes/+layout.svelte:716` | A request to a model the person connected directly from the browser returned nothing | Check the direct connection | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `{error}` or `{err}` (server text) | Error | `src/routes/(app)/automations/+page.svelte:134`, `:167`, `:177`, `:190`, `:197`, `:207`, `:270` | Loading the list, switching one or many automations on or off, **Run now**, deleting or exporting failed | Retry | See `automations-calendar-and-timers.md` section 10 |
| `Automation triggered`; `Deleted {{name}}` | Success | `src/routes/(app)/automations/+page.svelte:201`, `:211` | **Run now** accepted; automation deleted | None | See `automations-calendar-and-timers.md` section 10 |
| `Delete automation?`; `This will delete {name}.` | Dialog | `src/routes/(app)/automations/+page.svelte:414` | **Delete** in the list | Confirm or cancel | See `automations-calendar-and-timers.md` section 10 |
| `Imported automations successfully` | Success (unchecked success when the file holds no list) | `src/routes/(app)/automations/+page.svelte:438` | Import finished; also shown when the file contained no automations, so nothing was created | Check the list | See `automations-calendar-and-timers.md` section 10 |
| `{error}` (import), including `Error: Invalid JSON format` | Error | `src/routes/(app)/automations/+page.svelte:290`, `:440` | The import file could not be read, or creating one automation failed (earlier ones stay) | Correct the file | See `automations-calendar-and-timers.md` section 10 |
| `No automations found` | Inline | `src/routes/(app)/automations/+page.svelte:579` | The list is empty | None | See `automations-calendar-and-timers.md` section 10 |
| `{error}` (server text) | Error | `src/routes/(app)/automations/[id]/+page.svelte:29` | Opening one automation failed | Go back to the list | See `automations-calendar-and-timers.md` section 10 |
| `{err}` (server text) | Error | `src/routes/(app)/calendar/+page.svelte:98`, `:127` | Loading events, or deleting a calendar, failed | Retry | See `automations-calendar-and-timers.md` section 10 |
| `Calendar deleted`; `Failed to delete calendar` | Success; Error | `src/routes/(app)/calendar/+page.svelte:120`, `:124` | Deleting a calendar; the error when the server returned nothing | Retry | See `automations-calendar-and-timers.md` section 10 |
| `{error}` (server text) | Error | `src/routes/(app)/folders/[folderId]/+page.svelte:26` | Opening a folder page failed | Go back | See `chat-conversations-history-and-organisation.md` section 10 |
| `Open WebUI version (v{{OPEN_WEBUI_VERSION}}) is lower than required version (v{{REQUIRED_VERSION}})` | Error | `src/routes/(app)/admin/functions/create/+page.svelte:28-30`; `src/routes/(app)/admin/functions/edit/+page.svelte:29-31`; `src/routes/(app)/workspace/tools/create/+page.svelte:26-28`; `src/routes/(app)/workspace/tools/edit/+page.svelte:26-28` | Saving a function or tool whose header asks for a newer upstream version | Use a version made for 0.11.4 | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `{error}` (server text) | Error | `src/routes/(app)/admin/functions/create/+page.svelte:46`; `src/routes/(app)/admin/functions/edit/+page.svelte:47`, `:76` | Creating, saving or loading a function failed | Read the text | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `Function created successfully`; `Function updated successfully` | Success | `src/routes/(app)/admin/functions/create/+page.svelte:51`; `src/routes/(app)/admin/functions/edit/+page.svelte:52` | The function was saved | None | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `{error}` (server text) | Error | `src/routes/(app)/workspace/tools/create/+page.svelte:45`; `src/routes/(app)/workspace/tools/edit/+page.svelte:45`, `:63` | Creating, saving or loading a tool failed | Read the text | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Tool created successfully`; `Tool updated successfully` | Success | `src/routes/(app)/workspace/tools/create/+page.svelte:50`; `src/routes/(app)/workspace/tools/edit/+page.svelte:50` | The tool was saved | None | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `You do not have permission to edit this tool` | Error | `src/routes/(app)/workspace/tools/edit/+page.svelte:69` | Opening the editor of a tool without write access | Ask the owner | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Error: A model with the ID '{{modelId}}' already exists. Please select a different ID to proceed.` | Error | `src/routes/(app)/workspace/models/create/+page.svelte:17-22` | Creating a workspace model with an id already in use | Choose another id | See `workspace-models-and-model-access.md` section 10 |
| `Error: Model ID cannot be empty. Please enter a valid ID to proceed.` | Error | `src/routes/(app)/workspace/models/create/+page.svelte:27` | Creating a model with no id | Type an id | See `workspace-models-and-model-access.md` section 10 |
| `{error}` (server text) | Error | `src/routes/(app)/workspace/models/create/+page.svelte:47`, `:64`; `src/routes/(app)/workspace/models/edit/+page.svelte:55` | Creating the model failed, or reloading the model list afterwards failed | Read the text | See `workspace-models-and-model-access.md` section 10 |
| `Model created successfully!`; `Model updated successfully` | Success | `src/routes/(app)/workspace/models/create/+page.svelte:61`; `src/routes/(app)/workspace/models/edit/+page.svelte:52` | The model was saved | None | See `workspace-models-and-model-access.md` section 10 |
| `You do not have permission to edit this model` | Error | `src/routes/(app)/workspace/models/edit/+page.svelte:31` | Opening the editor of a model without write access | Ask the owner | See `workspace-models-and-model-access.md` section 10 |
| `{error}` (server text); `Prompt updated successfully` | Error; Success | `src/routes/(app)/workspace/prompts/[id]/+page.svelte:22`, `:45`, `:27` | Saving or loading a prompt | Retry if it failed | See `prompts-and-skills.md` section 10 |
| `{error}` (server text); `Skill created successfully`; `Skill updated successfully` | Error; Success | `src/routes/(app)/workspace/skills/create/+page.svelte:25`, `:30`; `src/routes/(app)/workspace/skills/edit/+page.svelte:22`, `:45`, `:28` | Creating, saving or loading a skill | Retry if it failed | See `prompts-and-skills.md` section 10 |

The route pages `/watch`, `/home`, `/notes/*`, `/playground/*`, `/channels/{id}`, `/c/{id}`, the
admin redirect pages and the workspace list pages add no message of their own; their screens'
messages are in the component subsections above.

### 10.16 `src/lib/utils/` (Helpers Whose Texts Reach the Screen)

The helpers show no pop-up themselves (no helper in `src/lib/utils/` imports the pop-up library);
they throw or return texts that the screens above display. All of these texts are untranslated.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `pdfjsLib is required for PDF extraction`; `content.xml not found`; `content.xml is not well-formed`; `Unsupported or non-text file type: {name}` | Thrown (shown inside `Failed to extract content from the file: {{error}}`, section 10.2) | `src/lib/utils/index.ts:1904`, `:1978`, `:1983`, `:2094` | Temporary chat only: the browser could not read a PDF, an OpenDocument file (missing or damaged `content.xml`), or a file that is not text | Use a normal chat (the server reads the file) or another format | See `files-uploads-and-storage.md` section 10 (the last text); the others established here |
| `External resource loading is disabled for rendered diagrams` | Thrown (shown as `Failed to render diagram: …`, section 10.3) | `src/lib/utils/index.ts:2299-2305` | A Mermaid diagram in an answer refers to an outside image or style sheet; the browser refuses to draw it | Ask the model for a diagram without outside images or styles | Established here; the block protects users from outside content in model answers |
| `External resource loading is disabled for rendered visualizations` | Thrown (shown as `Failed to render visualization: …`, section 10.3) | `src/lib/utils/index.ts:2338-2347` | A Vega chart in an answer tries to load data or images from another site | Ask the model to include the data in the chart itself | Established here |
| `Failed to fetch Google Drive credentials`; `Google Drive API credentials not configured`; `Please configure valid Google Drive API credentials`; `Failed to get access token`; `OAuth error occurred`; `Unable to get OAuth token`; `Required file details missing`; `Failed to download file ({status}): {errorText}` | Thrown (shown inside `Error accessing Google Drive: {{error}}`, section 10.2) | `src/lib/utils/google-drive-picker.ts:9`, `:16`, `:27`, `:30`, `:85`, `:89`, `:116`, `:143`, `:183` | The Google Drive picker failed: configuration missing, sign-in refused or blocked, or the download refused | Allow pop-ups; check access to the file in Drive; report configuration texts | See `files-uploads-and-storage.md` section 10 |
| `Failed to fetch OneDrive credentials`, `OneDrive client ID not configured`, `Failed to login: {message}`, `Failed to open OneDrive picker window` and the other OneDrive texts | None on screen (browser console only) | `src/lib/utils/onedrive-file-picker.ts:43-399`; caught and only logged at `src/lib/components/chat/MessageInput.svelte:2273-2275` | The OneDrive or SharePoint picker failed; **the user sees nothing happen** | Allow pop-ups and retry; report with the time | See `files-uploads-and-storage.md` section 10; pattern in section 11.5 |
| `Could not retrieve auth token`; `Failed to get token` | None on screen (sent to the Microsoft picker window) | `src/lib/utils/onedrive-file-picker.ts:336`, `:344` | The picker asked for a fresh token and none could be obtained | As above | Established here |
| `Error: Expected a JSON object of translation keys and strings.` and the other dictionary texts (`Invalid translation key: {key}`, `Translation must be a string: {key}`, `Interpolation placeholders do not match: {key}`, `Invalid language: {locale}`, `Original text is required for translated rows.`, `Duplicate original text: {content}`) | Thrown (shown as an error pop-up by the translation table, section 10.11, and by the admin translation settings) | `src/lib/utils/translationDictionary.ts:15`, `:17`, `:18`, `:23`, `:31`, `:60`, `:63` | An admin uploads or saves translation overrides that are not a JSON object of texts, use a forbidden key, change the `{{placeholders}}` of a message, or repeat an original text | Correct the file or the rows | See `admin-settings-panels.md` section 10; the first text established here |
| `Unsupported file type`, `Invalid PNG file`, `No PNG text chunk named "{textChunkKeyword}" found`, `Unable to parse "chara" field as base64`, `Invalid CRC for chunk type "{type}"` | Thrown | `src/lib/utils/characters/index.ts:9`, `:54`, `:60`, `:75`, `:92` | Character-card import helper; no screen in `src/` imports it in v0.11.4 (bulk search), so users cannot meet these texts | None | Established here |
| (no text) `copyToClipboard` returns `false` when the browser refuses the copy | None | `src/lib/utils/index.ts:524-658` | Screens that ignore the result show their success pop-up anyway (unchecked success rows in sections 10.1, 10.3, 10.9 and 10.11) | Paste to check | Section 11.6 |

### 10.17 `src/lib/apis/` (Errors the API Clients Hand Back)

The 30 client files in `src/lib/apis/` show nothing themselves; each function throws (or returns)
an error value that the calling screen prints, so the screen's row above names the action and
this table names the text. Section 4.1 explains the general pattern; most clients pass the
server's `detail` on unchanged, and the wording is then in the backend catalogues.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{detail}` (server text) | Thrown | 340 call sites written `error = err.detail`, for example `src/lib/apis/channels/index.ts:338`; 33 through `getErrorDetail` in `src/lib/apis/chats/index.ts:4-10` | Any refused request; validation lists (HTTP 422) are joined with commas only by the chats client and with `; ` by the profile update (`src/lib/apis/auths/index.ts:500-503`) | See the screen's row | See the two backend catalogues, section 10 |
| `Server connection failed` (untranslated) | Thrown | `src/lib/apis/images/index.ts:23`, `:58`, `:94`, `:126`, `:159`, `:191`, `:230`, `:282`; `src/lib/apis/ollama/index.ts:53`, `:94`, `:126`, `:158`, `:190`; fallback of `getErrorMessage` in `src/lib/apis/openai/index.ts:3-14` | The request failed without a server `detail`: the server or a proxy could not be reached, or answered with something other than the expected JSON. Seen in the playground images tab (section 10.14), the model picker downloads (section 10.4) and admin connection and image settings (area 31) | Retry; if it persists, report it as a server or network problem | See `model-connections-openai-ollama-and-direct.md` section 10 and `image-generation-and-editing.md` section 10 |
| `OpenAI: {message}` or `OpenAI: Network Problem`; `Ollama: {message}` or `Ollama: Network Problem` (untranslated) | Thrown | `src/lib/apis/openai/index.ts:98`, `:128`, `:354`, `:380`; `src/lib/apis/ollama/index.ts:22` | Listing or verifying a model connection failed; `Network Problem` when the provider sent no message. Shown by the connection settings windows (area 31) | Check the address and key of the connection | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `OpenAI: URL is required` (untranslated) | Thrown | `src/lib/apis/openai/index.ts:334` | Verifying a connection with an empty address | Fill in the address | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Connection to {url} timed out` (untranslated) | Thrown | `src/lib/apis/index.ts:419-420` | Loading a tool server's OpenAPI description took longer than 10 seconds (`src/lib/apis/index.ts:6`, `:398`). The app start-up replaces it with `Failed to connect to {{URL}} OpenAPI tool server` (section 10.15); the tool-server windows of the settings screens (area 31) can show it as is | Check the tool server is up | Established here |
| `Failed to parse JSON spec`; `Invalid OpenAPI spec` (untranslated) | Returned (`{ error, url }`) | `src/lib/apis/index.ts:473`, `:480` | A tool server set up with a pasted description that is not JSON, or a description without `paths`. At start-up the app shows only `Failed to connect to {{URL}} OpenAPI tool server`; the terminal menu drops such servers without a message (`src/lib/components/chat/MessageInput/TerminalMenu.svelte:51`) | Correct the tool server's description | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 (the second text); the first established here |
| `No matching route found for operationId: {name}`; `No matching method found for operationId: {name}`; `Request body expected for operation '{name}' but none found.`; `HTTP error! Status: {status}. Message: {resText}` (untranslated) | Tool result | `src/lib/apis/index.ts:564`, `:578`, `:656`, `:682`, returned as `{ error }` at `:711-714` | A model called one of the person's own tool servers from the browser and the call could not be matched or the server refused; the model receives the text and the tool card shows it | Check the tool server and its description | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Response body is not readable` (untranslated) | Thrown | `src/lib/apis/chats/index.ts:449-452` | **Export Chats** in **Settings › Data Controls** (dotted keys, English at `src/lib/i18n/locales/en-US/translation.json:2807` and `:2816`; call at `src/lib/components/chat/Settings/DataControls.svelte:94`) received an answer the browser cannot read as a stream | Retry in another browser; escalate | Established here (the screen is area 31) |
| `Failed to read policy`; `Failed to read lifecycle` (untranslated, or the server's `detail`) | Thrown | `src/lib/apis/configs/index.ts:336`, `:404` | The terminal-server window (`src/lib/components/AddTerminalServerModal.svelte:166-171`, area 31) could not read the orchestrator's policy or lifecycle | Check the terminal server address and key | Established here |
| `Failed to stream pending files` (untranslated) | Thrown | `src/lib/apis/knowledge/index.ts:597-598` | Defined for a knowledge-base progress stream; no screen in `src/` calls it in v0.11.4 (bulk search) | None | Established here |
| `Terminal request failed ({status})` (untranslated) | Thrown | `src/lib/apis/terminal/index.ts:130` | Any terminal request answered with an error status (sections 10.1 and 10.5) | Check the terminal server | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `File comparison is not available on this terminal. Update Open Terminal to use Compare.` (untranslated) | Inline (file comparison view) | `src/lib/apis/terminal/index.ts:745-751`; shown by `src/lib/components/chat/FileNav/FileCompare.svelte:47-48`, `:226-228` | **Compare** in the terminal file panel against a terminal server that does not offer comparison (answer 405, or 404 without a reason) | Ask the platform maintainer to update the terminal server | Established here |
| `{detail}`, `{error}` or `Comparison failed ({status})` (untranslated) | Inline (file comparison view) | `src/lib/apis/terminal/index.ts:753-758`; shown as above | The comparison was refused for another reason | Read the text | Established here |
| `{detail}` or the browser's error message; `{data.error}` from processing | Thrown; stored on the file (yellow pop-up) | `src/lib/apis/files/index.ts:37`, `:73-75` | The upload failed (`:37`), or the server's processing status stream reported an error for the file (`:73-75`), which becomes the `uploadedFile.error` warning (sections 10.2, 10.9, 10.10) | Check the file is usable in the answer | See `files-uploads-and-storage.md` section 10 |

### 10.18 `src/lib/workers/` (In-Browser Voice and Python)

The workers run inside the browser; their texts reach the user through the screens that called
them. All are untranslated.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `KokoroTTS Worker is not initialized yet.` | Thrown (shown as `Error: KokoroTTS Worker is not initialized yet.` by **Read Aloud** and calls, sections 10.2 and 10.3) | `src/lib/workers/KokoroWorker.ts:74-76` | The in-browser Kokoro voice was asked to speak before its model finished loading, or after loading failed (the load error goes to the console only, `:33-35`) | Wait for the voice to load; reload the page; or choose another voice engine in **Settings › Audio** | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `TTS model not initialized` | Thrown (as above) | `src/lib/workers/kokoro.worker.ts:34-37`; passed on at `src/lib/workers/KokoroWorker.ts:43-46` | The voice worker itself had no loaded model when asked to speak | As above | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `{error.message}` from the voice model | Thrown (as above) | `src/lib/workers/kokoro.worker.ts:48-49` | Generating speech for a sentence failed inside the voice model | Retry; change the voice | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `[processResult error]: {message}` | Code output | `src/lib/workers/pyodide.worker.ts:363-366` | In-browser Python finished but its result could not be converted for display | Return a simpler value from the code | See `code-execution-and-interpreter.md` section 10 |
| `{message}` of a Python error | Code output (error) | `src/lib/workers/pyodide.worker.ts:231-235`, `:284-289` | In-browser Python raised an error, or a file read in the browser Python file system failed | Fix the code; check the file exists | See `code-execution-and-interpreter.md` section 10 |

## 11. Common Tier-1 Issues and Troubleshooting

These are cross-cutting patterns. For a message tied to one feature, follow the row in section 10
to the area document's own section 11. Tier 1 is read-only: the diagnostic steps below only ask,
read and open public pages; nothing changes data, settings, roles or access.

### 11.1 "It keeps saying Connection lost. Reconnecting..."

**Symptom.** A yellow pop-up `Connection lost. Reconnecting...`, sometimes followed by a green
`Reconnected`. Replies may stop appearing until the page is reloaded, note edits and channel
messages stop updating (section 10.15).

**Likely causes, in order.**
1. The person's network dropped briefly (Wi-Fi, VPN change, laptop sleep). The browser waits
   2 seconds, longer after the tab returns from the background, before warning
   (`src/routes/+layout.svelte:128-163`).
2. The server restarted or was redeployed; after reconnecting, a changed version makes the page
   reload itself (`src/routes/+layout.svelte:201-214`).
3. Something between the browser and the server cuts long-lived connections (a proxy or firewall
   timeout). Whether production has such a layer is TO BE CONFIRMED.
4. A multi-worker or multi-server deployment without the shared live-connection setup (see
   `CLAUDE.md`, Deployment; how production runs is TO BE CONFIRMED).

**Diagnostic steps.**
1. Ask whether `Reconnected` follows and how often it happens; note the times.
2. Ask whether other people saw it at the same minute (points to the server, not the person).
3. Open `/health` in a browser: `{"status": true}` means the server process answers
   (`backend/open_webui/main.py:2963`). Open `/ready`: an error status means start-up has not
   finished or the database or Redis is down (`backend/open_webui/main.py:2968-3006`).

**Resolution.** If it is one person and `Reconnected` follows, advise a stable connection and a
reload after it reconnects; copy any long unsent text first. If many people are affected, escalate.

**Escalation.** To the platform maintainer: times (with time zone), number of people, the `/ready`
result, whether a deploy happened, and the person's network (on campus, VPN, home).

### 11.2 "The page says MedIT GPT Backend Required"

**Symptom.** A full-screen message `{{webUIName}} Backend Required` (shown with the site's name)
and `Oops! You're using an unsupported method (frontend only). Please serve the WebUI from the backend.`,
with a **Check Again** button (section 10.15). The links on that screen go to the upstream project,
not to MedIT GPT support.

**Likely causes, in order.**
1. The server was down or restarting when the page loaded, so the browser could not read
   `/api/config` (`src/routes/+layout.svelte:1239-1250`, `:1317`).
2. A proxy or gateway in front of the server answered with an error page instead of the
   configuration (deployment detail TO BE CONFIRMED).
3. The person's network blocked the request.

When a sign-in proxy in front of the server answers with a redirect, the app instead reloads
the site so the proxy's sign-in page can appear (`src/lib/apis/index.ts:1489-1509`;
`src/routes/+layout.svelte:1242-1248`).

**Diagnostic steps.** Open `/health` and `/ready` as in 11.1; ask whether others see the same
screen; press **Check Again** after a minute.

**Resolution.** Usually it clears once the server is back; **Check Again** reloads `/`. If the
page persists for several minutes or for many people, escalate. See also
`authentication-and-sign-in.md` section 11.21.

**Escalation.** Times, how many people, `/health` and `/ready` results, and whether a deploy or
maintenance was planned.

### 11.3 "It says Session expired. Please sign in again."

**Symptom.** A red pop-up `Session expired. Please sign in again.` and the sign-in page.

**Likely causes, in order.**
1. The sign-in token reached its lifetime (setting `auth.jwt_expiry`, code default four weeks,
   live value TO BE CONFIRMED; see `../tools/ground-truth.md`). The browser checks every 15
   seconds and ends the session 60 seconds before expiry (`src/routes/+layout.svelte:897`,
   `:965-977`, `:1231`).
2. The server stopped accepting the token: a request answered 401 and a second check of the
   session also answered 401 (`src/routes/+layout.svelte:1079-1091`). This happens when the
   person signed out elsewhere (only revoked when Redis is configured), the account was changed or
   removed, or the server's signing key changed; the last one signs **everyone** out at once
   (`../tools/ground-truth.md`, Accounts and Access and Secrets).

**Diagnostic steps.** Ask whether it happened to one person or many at the same time; ask when
they last signed in.

**Resolution.** Sign in again. For one person, nothing else is needed. Follow
`authentication-and-sign-in.md` sections 11.7 and 11.9 for repeated or site-wide cases.

**Escalation.** Many people at once: escalate with the time; the platform maintainer checks whether
the server was redeployed. Security-sensitive questions about tokens: refer to the platform
maintainer and U of T Information Security (security.utoronto.ca).

### 11.4 "I get a red pop-up that just says [object Object]"

**Symptom.** A red pop-up whose whole text is `[object Object]`, or a browser error text such as a
`TypeError` about a failed fetch (section 4.2).

**Likely causes, in order.**
1. The server rejected the request as malformed and answered with a list of problems instead of a
   sentence (HTTP 422); most screens print that list as `[object Object]` (section 4.1).
2. A proxy, gateway or sign-in layer answered instead of MedIT GPT, with its own JSON or an HTML
   page.
3. The request never reached the server (network failure).

**Diagnostic steps.**
1. Ask exactly which button was pressed, on which screen, and the time.
2. Ask the person to repeat once. If the browser's developer tools are available to them (and they
   are comfortable), the **Network** tab shows the failed request's status; do not ask for its
   contents if the request held chat text or personal data.

**Resolution.** Retry once; if it repeats, escalate. There is nothing to fix in the browser.

**Escalation.** Screen, action, time and, if known, the HTTP status. The platform maintainer reads
the server log for that minute (logs go to standard output only).

### 11.5 "I clicked and nothing happened" or "My file just disappeared"

**Symptom.** No pop-up at all: a file vanishes from the message box, a OneDrive pick does
nothing, a playground run leaves an empty answer.

**Likely causes, in order.**
1. The API client got a failure with no `detail` and handed nothing back (section 4.2), so the
   screen had nothing to show, for example a normal upload that returned nothing
   (`src/lib/components/chat/MessageInput.svelte:1039-1043`).
2. The screen catches the error and only writes it to the browser console: the OneDrive and
   SharePoint picker (`src/lib/components/chat/MessageInput.svelte:2273-2275`) and the playground
   (section 10.14).
3. The browser blocked a pop-up window (pickers and sign-in windows).

**Diagnostic steps.** Ask for the exact steps and time; ask whether pop-ups are allowed for the
site; ask whether the same works in the main chat or with another file.

**Resolution.** Allow pop-ups, retry, try a smaller or different file; for OneDrive see
`files-uploads-and-storage.md` section 11.15.

**Escalation.** Steps, time, browser, and whether it repeats; the server log for that minute is
the only record.

### 11.6 "It said Copied (or Saved), but it wasn't"

**Symptom.** A green pop-up, but the clipboard is empty or the change is not there.

**Likely causes, in order.**
1. The screen shows the pop-up without checking the result (rows marked **unchecked success**:
   `Copied shared chat URL to clipboard!`, `Copied to clipboard` on formulas, inline code and
   diagrams, the channel webhook `Copied`, `Thanks for your feedback!`, `Imported notes successfully`,
   the note sharing `Saved`, `Imported automations successfully`, and `Settings saved successfully!`
   on some tabs).
2. The browser refused clipboard access; the copy helper returns `false` without a message
   (`src/lib/utils/index.ts:524-658`).
3. The save itself failed afterwards; an error pop-up usually follows the green one.

**Diagnostic steps.** Ask whether a red pop-up followed; ask the person to paste right after
copying; reload the screen and look again.

**Resolution.** Allow clipboard access for the site, or copy the address from the browser's
address bar; redo the change and check it after a reload.

**Escalation.** Only if a change repeatedly does not stick after a reload: send the screen, the
setting or item, and the times.

### 11.7 "Every time I open MedIT GPT it says Failed to connect to … OpenAPI tool server"

**Symptom.** At every page load a red pop-up `Failed to connect to {{URL}} OpenAPI tool server`
(or `… terminal server`).

**Likely causes, in order.** A tool or terminal server that the person added under
**Settings › Integrations** is offline, has moved, needs a new key, or has an invalid description
(texts in section 10.17 are hidden behind this one); the check runs at every load
(`src/routes/(app)/+layout.svelte:92-133`).

**Diagnostic steps.** Ask which address the pop-up names; ask whether the person added it
themselves.

**Resolution.** The person switches the server off or corrects it in **Settings › Integrations**;
see `workspace-tools-tool-servers-mcp-and-terminals.md` section 11.9.

**Escalation.** Only when the address is a MedIT GPT-provided server (TO BE CONFIRMED which ones
exist): send the address and the time.

### 11.8 "A red pop-up appeared with no text"

**Symptom.** An empty or nearly empty red pop-up.

**Likely causes, in order.**
1. **Edit Channel** › **Update** or **Delete** failed: these two screens print a part of the error
   that does not exist (`src/lib/components/layout/Sidebar/ChannelItem.svelte:69`;
   `src/lib/components/layout/Sidebar/ChannelModal.svelte:117`).
2. A chat answer carried an error whose field is empty or not text (section 4.2,
   `src/lib/components/chat/Chat.svelte:3725-3742`); the error box under the reply then usually
   shows the readable part.
3. A tool or function raised a pop-up with no text (section 10.1, notification events).

**Diagnostic steps.** Ask what was clicked; for a chat, ask what the grey error box under the
reply says; for a channel, whether the change was kept after a reload.

**Resolution.** Reload and check; retry once.

**Escalation.** Screen, action and time; for chats, the text of the error box.

### 11.9 "The message I got isn't in your list" or "Part of the screen is in English"

**Symptom.** The reported wording matches no row, or one text stays English in another language.

**Likely causes, in order.**
1. The interface language is not English, so the text is a translation (section 5.1).
2. The text is untranslated in the code (section 4.3) or comes from the server.
3. An admin translation override replaced the wording (`ui.i18n`, section 4.4).
4. The text came from a tool, function, model or outside service (sections 10.1 and 10.17).

**Diagnostic steps.** Ask the person to switch to English in **Settings › General** and repeat;
search the backend catalogues; ask which tools were switched on.

**Resolution.** Use the English text to find the row; explain that some texts are English only.

**Escalation.** A text found nowhere, with a screenshot, the language and the time, to the
knowledgebase maintainer so this catalogue can be extended.

## 12. Local Customisations

Compared with upstream v0.11.4 (`git diff main...uoft` and the uncommitted `git diff`, both
limited to the folders in scope), **no toast, confirmation or error text was added, removed or
reworded** in the fork. The differences that change what users see around messages are:

| Change | Where | Effect on messages | Committed or uncommitted |
|---|---|---|---|
| The product name comes from the site name instead of the fixed text "Open WebUI" | `src/lib/constants.ts:7` (`APP_NAME`); browser notification titles `src/routes/+layout.svelte:622`, `:760`, `:873`; channel page titles `src/lib/components/channel/Channel.svelte:330-333` | Browser notifications read `{title} / MedIT GPT` (the live `WEBUI_NAME` is TO BE CONFIRMED); the "Backend Required" screen already used the site name upstream (`src/routes/error/+page.svelte:25`) | Committed |
| **Hide Processing Details** setting (`src/lib/i18n/locales/en-US/translation.json:2924`) | `src/lib/components/common/InterfaceSettings.svelte:1361-1377`; `src/lib/components/chat/Messages/ResponseMessage.svelte:214-221`, `:921`; `src/lib/components/chat/MessageInput.svelte:1792`; `src/lib/components/channel/Messages/Message.svelte:154-155` | While it is on, status lines, tool calls and the task list are hidden and `Thinking...` is shown instead; pop-ups and error boxes are unchanged. A user who "sees no progress at all" may have it switched on | Committed; the working tree moves `Thinking...` into a status line (`ResponseMessage.svelte:921`) and rewords the setting's description (`translation.json:2923`) |
| **Inline Citations** setting (`src/lib/i18n/locales/en-US/translation.json:2936`) | `src/lib/components/common/InterfaceSettings.svelte:1338-1354` | No message of its own | Committed |
| Language loading | `src/lib/i18n/index.ts:77-89`, `:93`, `:105` | When an admin sets a default language, a message missing from the person's language now falls back to that language and then to English (before: to that language only, after which the key itself was shown, which for plain keys is the same English text). A browser language such as `fr` or `de-AT` is now matched to an available translation | Uncommitted |
| Logo in the app sidebar | `src/lib/components/app/AppSidebar.svelte:39-40` | None | Committed |

The other uncommitted changes in scope (`Chat.svelte`, `HTMLToken.svelte`, `MarkdownTokens.svelte`,
`StructuredOutputRenderer.svelte`, `structuredOutput.ts`, `StatusItem.svelte`,
`ToolCallDisplay.svelte`) change how answers and tool calls are drawn and contain no message text
(bulk search of the diff for `$i18n.t(`, `toast.` and `throw`).

## 13. Source File Index

All paths are repository-relative. "Shows" lists the kinds of message each file produces.

### 13.1 Infrastructure Behind Every Message

| File | Role | Section |
|---|---|---|
| `src/routes/+layout.svelte` | Pop-up container (`Toaster`), live connection and its warnings, session expiry, start-up configuration and the redirect to `/error`, notification cards | 2.1, 8, 10.15 |
| `src/routes/(app)/+layout.svelte` | Signed-in shell: account pending overlay, update card, tool-server checks at load | 2.1, 10.15 |
| `src/lib/components/common/ConfirmDialog.svelte` | Every confirmation window and its default texts | 2.1, 10.11 |
| `src/lib/components/chat/Messages/Error.svelte` | The error box under a chat reply | 2.1, 10.3 |
| `src/routes/+error.svelte`, `src/routes/error/+page.svelte` | The error page and the "Backend Required" screen | 2.1, 10.15 |
| `src/lib/i18n/index.ts`, `src/lib/i18n/settings-translations.ts`, `src/lib/i18n/locales/en-US/translation.json` | Translation loading, fallbacks, admin overrides and the English text of dotted keys | 4.4, 12 |
| `src/lib/apis/*/index.ts` (30 files) | How server errors are handed to the screens | 4.1, 10.17 |

### 13.2 Files With Messages, by Section 10 Subsection

| Section | Files (under `src/lib/components/` unless a full path is given) |
|---|---|
| 10.1 | `chat/Chat.svelte`, `chat/Artifacts.svelte`, `chat/Navbar.svelte`, `chat/Placeholder.svelte`, `chat/ChatPlaceholder.svelte`, `chat/EmbeddedChatHistoryDropdown.svelte`, `chat/ToolServersModal.svelte`, `chat/SettingsModal.svelte`, `chat/ShareChatModal.svelte`, `chat/Tags.svelte`, `chat/XTerminal.svelte`, `chat/TerminalDock.svelte` |
| 10.2 | `chat/MessageInput.svelte`; `chat/MessageInput/` `InputMenu.svelte`, `AttachWebpageModal.svelte`, `Commands/AtCommands.svelte`, `Commands/Knowledge.svelte`, `CallOverlay.svelte`, `VoiceRecording.svelte`, `IntegrationsMenu.svelte`, `QueuedMessageItem.svelte`, `InputMenu/Knowledge.svelte`, `InputMenu/Notes.svelte`, `InputMenu/Chats.svelte`, `InputMenu/Files.svelte` |
| 10.3 | `chat/Messages.svelte`; `chat/Messages/` `UserMessage.svelte`, `ResponseMessage.svelte`, `RateComment.svelte`, `Markdown/KatexRenderer.svelte`, `Markdown/MarkdownInlineTokens/CodespanToken.svelte`, `Markdown/MarkdownTokens.svelte`, `StructuredOutputRenderer.svelte`, `CodeBlock.svelte`, `CodeExecutionModal.svelte`, `TerminalOutputFile.svelte`, `OutputEditView.svelte`, `Error.svelte`, `ResponseMessage/StatusHistory/StatusItem.svelte` |
| 10.4 | `chat/ModelSelector.svelte`, `chat/ModelSelector/ModelItem.svelte`, `chat/ModelSelector/Selector.svelte` |
| 10.5 | `chat/FileNav.svelte`; `chat/FileNav/` `FileEntryRow.svelte`, `FileNavToolbar.svelte`, `FilePreview.svelte`, `SqliteView.svelte`, `PortList.svelte`, `NotebookView.svelte`, `FileCompare.svelte` (also 10.17); `chat/PyodideFileNav.svelte` |
| 10.6, 10.7 | `chat/Controls/Valves.svelte`; `chat/Placeholder/FolderTitle.svelte`, `chat/Placeholder/ChatList.svelte` |
| 10.8 | `layout/Sidebar.svelte`; `layout/Sidebar/` `RecursiveFolder.svelte`, `ChatItem.svelte`, `ChannelModal.svelte`, `ChannelItem.svelte`, `ChatHoverPreview.svelte`, `Folders/FolderModal.svelte`, `SharedFolderItem.svelte`, `UserMenu.svelte`, `UserStatusModal.svelte`; `layout/SearchModal.svelte`, `layout/ChatsModal.svelte`, `layout/FilesModal.svelte`, `layout/SharedChatsModal.svelte`, `layout/Navbar/Menu.svelte`, `layout/Overlay/AccountPending.svelte`, `layout/UpdateInfoToast.svelte` |
| 10.9 | `channel/Channel.svelte`, `channel/Thread.svelte`, `channel/Messages.svelte`, `channel/Messages/Message.svelte`, `channel/MessageInput.svelte`, `channel/ChannelInfoModal.svelte`, `channel/ChannelInfoModal/AddMembersModal.svelte`, `channel/ChannelInfoModal/UserList.svelte`, `channel/PinnedMessagesModal.svelte`, `channel/WebhooksModal.svelte`, `channel/WebhookItem.svelte` |
| 10.10 | `notes/NoteEditor.svelte`, `notes/Notes.svelte`, `notes/utils.ts` |
| 10.11 | `common/` `ConfirmDialog.svelte`, `CodeEditor.svelte`, `ImagePreview.svelte`, `PDFViewer.svelte`, `DocxPreview.svelte`, `FileItemModal.svelte`, `Image.svelte`, `SVGPanZoom.svelte`, `InterfaceSettings.svelte`, `TranslationTable.svelte`, `ToolCallDisplay.svelte`, `Valves.svelte`, `ExperimentalBadge.svelte`, `Selector.svelte`, `EmojiPicker.svelte` |
| 10.12, 10.13 | `automations/AutomationEditor.svelte`, `automations/DestinationDropdown.svelte`, `automations/FolderDropdown.svelte`, `automations/ModelDropdown.svelte`; `calendar/CalendarEventModal.svelte`, `calendar/CalendarSidebar.svelte`, `calendar/CreateCalendarModal.svelte` |
| 10.14 | `playground/Chat.svelte`, `playground/Completions.svelte`, `playground/Images.svelte` (`app/AppSidebar.svelte` has none) |
| 10.15 | `src/routes/+layout.svelte`, `src/routes/error/+page.svelte`, `src/routes/+error.svelte`, `src/routes/(app)/+page.svelte`, `src/routes/auth/+page.svelte`, `src/routes/s/[id]/+page.svelte`, `src/routes/(app)/+layout.svelte`, `src/routes/(app)/automations/+page.svelte`, `src/routes/(app)/automations/[id]/+page.svelte`, `src/routes/(app)/calendar/+page.svelte`, `src/routes/(app)/folders/[folderId]/+page.svelte`, `src/routes/(app)/admin/functions/create/+page.svelte`, `src/routes/(app)/admin/functions/edit/+page.svelte`, `src/routes/(app)/workspace/tools/create/+page.svelte`, `src/routes/(app)/workspace/tools/edit/+page.svelte`, `src/routes/(app)/workspace/models/create/+page.svelte`, `src/routes/(app)/workspace/models/edit/+page.svelte`, `src/routes/(app)/workspace/prompts/[id]/+page.svelte`, `src/routes/(app)/workspace/skills/create/+page.svelte`, `src/routes/(app)/workspace/skills/edit/+page.svelte` |
| 10.16 | `src/lib/utils/index.ts`, `src/lib/utils/google-drive-picker.ts`, `src/lib/utils/onedrive-file-picker.ts`, `src/lib/utils/translationDictionary.ts`, `src/lib/utils/characters/index.ts` |
| 10.17 | `src/lib/apis/index.ts`, `src/lib/apis/channels/index.ts`, `src/lib/apis/chats/index.ts`, `src/lib/apis/auths/index.ts`, `src/lib/apis/images/index.ts`, `src/lib/apis/ollama/index.ts`, `src/lib/apis/openai/index.ts`, `src/lib/apis/configs/index.ts`, `src/lib/apis/knowledge/index.ts`, `src/lib/apis/terminal/index.ts`, `src/lib/apis/files/index.ts` |
| 10.18 | `src/lib/workers/KokoroWorker.ts`, `src/lib/workers/kokoro.worker.ts`, `src/lib/workers/pyodide.worker.ts` |

The bulk searches described in section 5.4 found no toast, confirmation or message text in the
other files in scope (of 414); the strings they hold are labels, buttons and placeholders, which
are not catalogued.

## 14. Open Questions

### 14.1 Not Determinable From the Code (TO BE CONFIRMED)

1. **How production is hosted** (host name, proxies or gateways in front of the server, number of
   workers, whether Redis is configured). It decides the likely causes in sections 11.1 to 11.3
   (`Connection lost. Reconnecting...`, the "Backend Required" screen,
   `Session expired. Please sign in again.`) and whether sign-out revokes tokens. TO BE CONFIRMED.
2. **Live admin translation overrides** (`ui.i18n`). Any message in this catalogue may read
   differently on the live site if an admin replaced it (section 4.4). TO BE CONFIRMED.
3. **Live values** of `WEBUI_NAME` (the name in `{{webUIName}} Backend Required` and in browser
   notifications), `auth.jwt_expiry` (when `Session expired` appears), the upload size and count
   limits quoted in messages, and the version update check (the admin update card). TO BE CONFIRMED.
4. **Upstream links shown to users.** The "Backend Required" screen links to the upstream GitHub
   read-me and a Discord invite (`src/routes/error/+page.svelte:35-43`); the update card links to
   upstream releases. Whether MedIT GPT users should be pointed there, and which MedIT GPT support
   contact should replace them, is TO BE CONFIRMED (no contact exists in the repository; see
   `../tools/ground-truth.md`).
5. **The onboarding sentence**
   `does not make any external connections, and your data stays securely on your locally hosted server.`
   is upstream wording shown before the first account exists; whether it is accurate for this
   deployment is TO BE CONFIRMED.
6. **Which tool and terminal servers, if any, MedIT GPT provides centrally** (section 11.7
   escalation). TO BE CONFIRMED.

### 14.2 Library and Browser Behaviour Not in the Repository

7. How long a pop-up stays on screen when the code sets no duration is a default of the
   `svelte-sonner` library, not of this repository; not established.
8. How the pop-up library draws a value that is not text (an object, `undefined`) was not verified;
   section 4.2 and 11.8 describe what the code passes, not the pixels.
9. The wording of browser network errors (a `TypeError` about a failed fetch) differs by browser
   and is not in the repository, so it is not quoted.

### 14.3 Findings for the Platform Maintainer (Established From the Code)

10. **Success shown although the action may have failed** (marked unchecked success in section 10):
    `Copied shared chat URL to clipboard!` (`src/lib/components/chat/ShareChatModal.svelte:197-223`;
    in Safari also before the link exists), `Copied to clipboard` on formulas, inline code and
    diagrams, the channel webhook `Copied`, `Thanks for your feedback!`,
    `Imported notes successfully`, the note sharing `Saved`, `Imported automations successfully`
    (also when nothing was imported) and `Settings saved successfully!` on some tabs.
11. **Failures that show nothing**: OneDrive and SharePoint picker errors are only logged
    (`src/lib/components/chat/MessageInput.svelte:2273-2275`); a normal upload that returns nothing
    removes the file without a message (`:1039-1043`); playground chat and completion failures show nothing
    (section 10.14); the terminal menu drops unreachable servers without a message
    (`src/lib/components/chat/MessageInput/TerminalMenu.svelte:51`); clearing the user status
    shows nothing when the server refuses (`src/lib/components/layout/Sidebar/UserMenu.svelte:199-202`).
12. **Blank or unreadable pop-ups**: **Edit Channel** update and delete print `error.message` of a
    text (`src/lib/components/layout/Sidebar/ChannelItem.svelte:69`;
    `src/lib/components/layout/Sidebar/ChannelModal.svelte:117`, already recorded in
    `channels-and-direct-messages.md`); 340 API call sites pass a validation list through as
    `[object Object]` (section 4.1).
13. **Two pop-ups for one failure**: saving a status shows the server text and then
    `Failed to update status` (`src/lib/components/layout/Sidebar/UserStatusModal.svelte:36-45`);
    a failed Ollama download shows the error and then `Download canceled`
    (`src/lib/components/chat/ModelSelector/Selector.svelte:558`, `:578`).
14. **Code with messages that no screen reaches in v0.11.4** (bulk search found no caller): the
    Google Drive upload path in `src/lib/components/chat/Chat.svelte:1663-1788`, the character-card
    helper `src/lib/utils/characters/index.ts`, `streamPendingKnowledgeFiles`
    (`src/lib/apis/knowledge/index.ts:588`) and `Cannot create an empty note.`
    (`src/lib/components/chat/MessageInput.svelte:1201`). Commented-out messages are not shown:
    `Please select a reason` (`src/lib/components/chat/Messages/RateComment.svelte:87-90`),
    `Folder name updated successfully`
    (`src/lib/components/layout/Sidebar/RecursiveFolder.svelte:488`) and the chat input disclaimer
    `LLMs can make mistakes. Verify important information.`
    (`src/lib/components/chat/Chat.svelte:4506`).
15. The untranslated tool-card summaries in `src/lib/components/chat/Messages/structuredOutput.ts:216-224`,
    `:312` (`Tool Approval Needed`, `Tool Executed`, `Executing...`, `Preparing...`) are passed as
    `title` to `ToolCallDisplay`, which declares no such property, so they appear not to be
    displayed (`src/lib/components/chat/Messages/StructuredOutputRenderer.svelte:131`;
    `src/lib/components/common/ToolCallDisplay.svelte:23-48`). To be confirmed by the planned
    in-chat catalogue (area 32).

### 14.4 Dependencies on Other Documents

16. The two backend catalogues this document points to for server text currently end at section 10
    (sections 11 to 14 not yet written); the pointers are to their section 10 and remain valid.
17. The sibling front-end catalogue for admin, workspace and settings screens (area 31) and the
    in-chat status catalogue (area 32) do not exist yet; rows that say "area 31" or "area 32" are
    forward references to `_areas.md` rows 31 and 32.
18. A few rows point to an area document's section 10 for a message that document lists in a
    different form (for example with `{name}` instead of `{{name}}`); the lookup used both forms.

### 14.5 Security-Sensitive Questions

19. Token lifetime, revocation without Redis and the effect of the server's signing key on
    sessions (section 11.3) were described only as far as users see them. Security-sensitive:
    refer to the platform maintainer and U of T Information Security (security.utoronto.ca).
20. The channel webhook address copied by `Copied` (section 10.9) works as a credential; how it is
    built is not described here. Security-sensitive: refer to the platform maintainer and U of T
    Information Security (security.utoronto.ca).

No contradiction with `CLAUDE.md`, `../tools/ground-truth.md` or `../tools/inventory.md` was found.
