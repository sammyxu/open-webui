# User Settings and Personalisation

## At a Glance

- **What it is.** The **Settings** window is one full-screen dialogue with up to 13 personal tabs: General, Interface, Notifications, Keyboard (id `shortcuts`), Connections, Integrations (id `tools`), Personalization, Audio, Data Controls, Usage, Archived Chats, Account and About. Admins see an Admin half in the same window (`admin-settings-panels.md`). It opens from the sidebar user menu, with `Cmd+.` (`Ctrl+.`), with `/settings` in the composer, or from a link ending in `?settings=<tab id>` (section 2).
- **Where settings live.** Almost everything is saved to the account (`user.settings.ui` on the server) and follows the person to any device after a reload. **Theme** and **Language** are kept only in the browser; keyboard bindings live in `user.settings.keybindings` (section 6).
- **When they save.** Most switches save the moment they are clicked; General, Audio, Connections, Integrations and Account need their **Save** button (section 5.3). For non-admins the server silently drops fields they may not change, and the success toast still appears (section 3.3).
- **Who sees which tab.** Interface needs the permission `settings.interface` (default on); Connections and Integrations need site switches that are off by default; Personalization needs memories on (section 3).
- **Admin preset.** Admins can set **Default Interface Settings** for everyone (`ui.default_interface_settings`); a person's own choice wins, and preset values show a grey `Default` tag (section 5.6).
- **MedIT GPT switches.** **Hide Processing Details** (default off) and **Inline Citations** (default on) sit in Interface > Chat, are ordinary Interface fields, and show in English in every language. Their code is committed; the reworded Hide Processing Details description exists only in the working tree (sections 7.3.7, 12).
- **About.** Shows `v0.11.4`, checks GitHub for the newest **upstream** Open WebUI release (so "available!" is not a MedIT GPT update), and carries licence-protected copyright and credit lines (section 7.14).
- **Search.** The search box narrows the tab list using setting labels in English and the current language; it does not jump to the setting (section 5.2).

## 1. Purpose and Who Uses It

The personal **Settings** window is where each signed-in person changes how MedIT GPT looks and behaves for their own account: interface language and colour theme, a default system prompt, model parameters, dozens of chat-display switches, keyboard shortcuts, audio, optional personal connections and tool servers, memories, data controls (import, export, archive, delete), personal usage statistics, archived chats, profile and password, and an About page with the version and licence lines.

- **Who uses it.** Every account with the role `user` or `admin`. Pending accounts do not reach it: the app layout shows the "Account Activation Pending" overlay instead of the application for any role other than `user` or `admin`, and stops before setting up the shortcuts and links that open the window (`src/routes/(app)/+layout.svelte:213-220`, `:445-447`).
- **One window, two halves.** For ordinary users the window lists only **Personal** tabs. For admins the same window also lists an **Admin** half (General, Authentication, Connections, Models and others) after the personal tabs (`src/lib/components/chat/SettingsModal.svelte:407-408`, `:748-779`). The admin tabs are documented in `admin-settings-panels.md`; this document covers the personal half and the parts of admin settings that set defaults for users.
- **What a support agent needs from this document.** Where each setting lives, what it changes, whether it is saved to the account (and so follows the person to another computer) or only to the current browser, what its default is, which permission hides it, and which deep reference document explains the feature behind it.
- **MedIT GPT specifics.** The fork adds two Interface switches, **Hide Processing Details** and **Inline Citations** (section 12). Everything else in the window matches upstream Open WebUI v0.11.4.

The window is a map onto many features. The deep documents are:

| Tab (visible title) | Deep reference document |
|---|---|
| Account | `authentication-and-sign-in.md` |
| Archived Chats, Data Controls | `chat-conversations-history-and-organisation.md` |
| Audio | `audio-speech-to-text-and-text-to-speech.md` |
| Connections | `model-connections-openai-ollama-and-direct.md` |
| Integrations (tab id `tools`) | `workspace-tools-tool-servers-mcp-and-terminals.md` |
| Personalization | `memories.md` |
| Notifications | `notifications-webhooks-events-and-banners.md` |
| Usage | `evaluations-feedback-and-analytics.md` |
| General, Interface, Keyboard (tab id `shortcuts`), About | this document (sections 7.2, 7.3, 7.5 and 7.14) |
| Chat display effects of Interface switches | `chat-composer-and-message-display.md` |
| Admin tabs in the same window | `admin-settings-panels.md` |

## 2. Navigation and URLs

### 2.1 Ways to Open the Settings Window

The window is a full-screen dialogue (`Modal`, `size="full"`), not a page, so it has no URL of its own. It is mounted once by the authenticated layout and opened by setting the `showSettings` store (`src/routes/(app)/+layout.svelte:425`; `src/lib/stores/index.ts:136`).

| How the user gets there | Tab that opens | Source |
|---|---|---|
| Sidebar user menu (picture and name at the bottom of the sidebar), then **Settings** | General | `src/lib/components/layout/Sidebar/UserMenu.svelte:558-577` |
| Sidebar user menu, then the top row showing the user's own picture and name | Account | `src/lib/components/layout/Sidebar/UserMenu.svelte:119-140` |
| Typing `/settings` in the chat composer and choosing the command (tooltip `Open settings.`) | General | `src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte:69-70`, `:412-416`; `src/lib/components/chat/MessageInput/CommandSuggestionList.svelte:132-134`; `src/lib/components/chat/MessageInput.svelte:1478` |
| Keyboard shortcut **Open Settings**, default `Cmd+.` (shown as `Ctrl+.` outside macOS); pressing it again closes the window | General (toggles) | `src/lib/shortcuts.ts:94`, `:185`; `src/routes/(app)/+layout.svelte:297-300` |
| Keyboard shortcut **Show Shortcuts**, default `Cmd+/` | Keyboard | `src/lib/shortcuts.ts:95`; `src/routes/(app)/+layout.svelte:301-304` |
| A link ending in `?settings=<tab id>` on any signed-in page, for example `/?settings=interface` | the named tab | `src/routes/(app)/+layout.svelte:166-195`, `:407-409` |
| Terminal menu in the composer, link to personal terminal settings | Integrations | `src/lib/components/chat/MessageInput/TerminalMenu.svelte:178` |
| Admins only: `/admin/settings`, the **Settings** link in the admin panel header, model selector shortcuts | admin tabs | `src/routes/(app)/admin/settings/+page.svelte:6`; `src/routes/(app)/admin/+layout.svelte:98-106`; `src/lib/components/chat/ModelSelector/Selector.svelte:1064`; `src/lib/components/chat/ModelSelector/ModelItemMenu.svelte:61` |

Notes:

- The `?settings=` parameter is removed from the address bar once handled (`src/routes/(app)/+layout.svelte:187-194`). A non-admin who follows an `admin:` link gets the General tab instead (`:181-185`), and the window falls back to General whenever the requested tab is not available to the user (`src/lib/components/chat/SettingsModal.svelte:486-497`).
- The user menu also contains a **Keyboard** item that opens the Keyboard tab, but it sits inside a help block that is off unless the menu is given `help` (`src/lib/components/layout/Sidebar/UserMenu.svelte:43`, `:471`, `:511-529`). Neither place that renders the menu turns it on (`src/lib/components/layout/Sidebar.svelte:1078`, `:1710`), so users do not see that item in v0.11.4.
- The window is closed with the **Back** button at the top of the tab list (`src/lib/components/chat/SettingsModal.svelte:518-527`). Closing resets the selection, so the next plain open starts on General (`:121-124`, `:128-134`).

### 2.2 Tab List, Tab Ids and Group Headings

Tabs appear in this order. On medium and wider screens they are grouped under small headings (`Personal`, then `Basics`, `Services`, `Preferences`, `Data`, `Profile`); on narrow screens the headings are hidden and the tabs scroll horizontally (`src/lib/components/chat/SettingsModal.svelte:142-156`, `:180-183`, `:554-561`).

| Group | Tab id (for `?settings=`) | Visible title (`en-US`) | Title key and `translation.json` line | Component |
|---|---|---|---|---|
| Basics | `general` | General | `settings.personal.general.title`, line 2870 | `src/lib/components/chat/Settings/General.svelte` |
| Basics | `interface` | Interface | `settings.personal.interface.title`, line 2985 | `src/lib/components/chat/Settings/Interface.svelte`, which wraps `src/lib/components/common/InterfaceSettings.svelte` |
| Basics | `notifications` | Notifications | `settings.personal.notifications.title`, line 2999 | `src/lib/components/chat/Settings/Notifications.svelte` |
| Basics | `shortcuts` | Keyboard | `settings.personal.shortcuts.title`, line 3036 | `src/lib/components/chat/Settings/Shortcuts.svelte` |
| Services | `connections` | Connections | `settings.personal.connections.title`, line 2800 | `src/lib/components/chat/Settings/Connections.svelte` |
| Services | `tools` | Integrations | `settings.personal.tools.title`, line 3048 | `src/lib/components/chat/Settings/Integrations.svelte` |
| Preferences | `personalization` | Personalization | `settings.personal.personalization.title`, line 3007 | `src/lib/components/chat/Settings/Personalization.svelte` |
| Preferences | `audio` | Audio | `settings.personal.audio.title`, line 2796 | `src/lib/components/chat/Settings/Audio.svelte` |
| Data | `data_controls` | Data Controls | `settings.personal.dataControls.title`, line 2816 | `src/lib/components/chat/Settings/DataControls.svelte` |
| Data | `usage` | Usage | `settings.personal.usage.title`, line 3054 | `src/lib/components/chat/Settings/Usage.svelte` |
| Data | `archived_chats` | Archived Chats | `settings.personal.archivedChats.title`, line 2769 | `src/lib/components/chat/Settings/ArchivedChats.svelte` |
| Profile | `account` | Account | `settings.personal.account.title`, line 2766 | `src/lib/components/chat/Settings/Account.svelte` |
| Profile | `about` | About | `settings.personal.about.title`, line 2742 | `src/lib/components/chat/Settings/About.svelte` |

Tab definitions: `src/lib/components/chat/SettingsModal.svelte:186-265`; tab buttons: `:563-746`; panels: `:791-852`.

Two names differ from their ids and confuse tickets: the tab with id `shortcuts` is titled **Keyboard**, and the tab with id `tools` is titled **Integrations** (its component file is `Integrations.svelte`). `SyncStatsModal.svelte` is not a tab; it is a dialogue that opens only when the Open WebUI Community website asks for usage statistics (section 7.15).

For admins, the **Admin** half follows with ids `admin:general`, `admin:authentication`, `admin:connections`, `admin:models`, `admin:subagents`, `admin:interface`, `admin:audio`, `admin:images`, `admin:evaluations`, `admin:analytics`, `admin:integrations`, `admin:documents`, `admin:web`, `admin:code-execution`, `admin:pipelines` and `admin:db`, grouped under `System`, `AI`, `Quality`, `Tools`, `Experience` and `Data` (`src/lib/components/chat/SettingsModal.svelte:157-174`, `:266-364`). See `admin-settings-panels.md`.

### 2.3 Related API Endpoints

| Method and path | Purpose | Source |
|---|---|---|
| `GET /api/v1/users/user/settings` | The account's settings with the admin interface preset merged in; `?raw=true` returns only the account's own values | `backend/open_webui/routers/users.py:457-474` |
| `POST /api/v1/users/user/settings/update` | Saves a partial change to the account's settings | `backend/open_webui/routers/users.py:482-562` |
| `POST /api/v1/users/user/info/update` | Merges fields into the account's `info` (used by **Allow User Location**) | `backend/open_webui/routers/users.py:679-698` |
| `GET /api/config` | Delivers the feature flags, permissions and `ui.default_interface_settings` the window reads | `backend/open_webui/main.py:2351-2378`, `:2433` |

The front-end callers are `getUserSettings` and `updateUserSettings` in `src/lib/apis/users/index.ts:277-331`.

## 3. Roles and Permissions

### 3.1 Which Tabs a Person Sees

The window builds its tab list from the person's role, their permissions (the effective permissions delivered with the session user) and site-wide feature flags (`src/lib/components/chat/SettingsModal.svelte:379-412`, `:503-505`). Tabs not listed below are shown to every user and admin.

| Tab | Shown when | Code default | Source |
|---|---|---|---|
| Interface | admin, or the permission `settings.interface` is on (treated as on when absent) | permission on (`USER_PERMISSIONS_SETTINGS_INTERFACE`, `backend/open_webui/config.py:1937`) | `src/lib/components/chat/SettingsModal.svelte:393-395` |
| Connections | the site setting `direct.enable` (**Direct Connections**) is on, for admins as well as users | off (`ENABLE_DIRECT_CONNECTIONS`, `backend/open_webui/config.py:230`) | `src/lib/components/chat/SettingsModal.svelte:381-383`, `:624` |
| Integrations (`tools`) | the site setting `direct.integrations.enable` is on, and the person is an admin or has `features.direct_tool_servers` | site setting off (`backend/open_webui/config.py:231`); permission off (`backend/open_webui/config.py:1904-1906`) | `src/lib/components/chat/SettingsModal.svelte:385-391`, `:639` |
| Personalization | the site setting `memories.enable` is on, and the person is an admin or has `features.memories` (treated as on when absent) | site setting on (`backend/open_webui/config.py:426`); permission on (`:1926`) | `src/lib/components/chat/SettingsModal.svelte:397-402` |
| Admin half | role `admin`; the admin Analytics tab also needs `features.enable_admin_analytics` | not applicable | `src/lib/components/chat/SettingsModal.svelte:407-411` |

The flags reach the browser through `/api/config` as `features.enable_direct_connections`, `features.enable_direct_integrations` and `features.enable_memories` (`backend/open_webui/main.py:2351-2352`, `:2378`). Live values are data held in the `config` table and are **TO BE CONFIRMED** for production.

### 3.2 Settings Hidden or Refused Inside a Tab

Rules shared by the tabs and the settings search live in `src/lib/utils/settings-access.ts`. The server applies matching rules when saving (section 3.3).

| Setting | Visible to | Source |
|---|---|---|
| General: System Prompt | admin, or `chat.controls` and `chat.system_prompt` both on (each treated as on when absent) | `src/lib/utils/settings-access.ts:3-5` |
| General: Advanced Parameters | admin, or `chat.controls` and `chat.params` both on | `src/lib/utils/settings-access.ts:6-8` |
| General parameters `stream_delta_chunk_size`, context compaction threshold, `num_thread`, `num_gpu`, `use_mmap`, `use_mlock`, `keep_alive` | admins only (in search; the panel's own rule is in section 7.2) | `src/lib/utils/settings-access.ts:39-45` |
| Data Controls: Import Chats, Export Chats, Delete All Chats | admin, or `chat.import`, `chat.export`, `chat.delete` respectively (treated as on when absent) | `src/lib/utils/settings-access.ts:9-12`, `:46-50` |
| Account: API keys | the site setting **API keys** (`auth.enable_api_keys`) is on, and the person is an admin or has `features.api_keys` (treated as **off** when absent) | `src/lib/utils/settings-access.ts:13-15` |
| Account: JWT Token | admins only, and only where API keys are available | `src/lib/utils/settings-access.ts:56-63` |
| Notifications: Notification Targets | the site setting `ui.enable_user_webhooks` is on, and the person is an admin or has `features.webhooks` | `src/lib/utils/settings-access.ts:16-18`, `:51-55` |
| Interface: Toast Notifications for New Updates; Show "What's New" Modal on Login | admins only | `src/lib/utils/settings-access.ts:21`, `:64-65`; `src/lib/components/common/InterfaceSettings.svelte:715-761` |
| Interface: Temporary Chat by Default | admin, or `chat.temporary` on | `src/lib/utils/settings-access.ts:19-20`, `:66-67`; `src/lib/components/common/InterfaceSettings.svelte:942-965` |
| Interface: Prompt Autocompletion | the site setting `task.autocomplete.enable` is on (code default off, `backend/open_webui/config.py:2333`) | `src/lib/components/common/InterfaceSettings.svelte:1636-1659` |

How permissions add up across groups is in `users-groups-roles-and-permissions.md`; the ground truth is that a permission is on if any of the person's groups grants it, otherwise the default decides.

### 3.3 What the Server Enforces When Saving

`POST /api/v1/users/user/settings/update` accepts any user or admin (`get_verified_user`) and, for non-admins, quietly removes fields the person is not allowed to change before saving (`backend/open_webui/routers/users.py:489-547`):

| Removed field | Condition | Source |
|---|---|---|
| every Interface field (the 63 fields of the `InterfaceSettings` model, including `models`, `showInlineCitations` and `hideProcessingDetails`) | the person lacks `settings.interface` | `backend/open_webui/routers/users.py:492-498`; `backend/open_webui/models/users.py:67-135` |
| `ui.system` (system prompt) | the person lacks `chat.controls` or `chat.system_prompt` | `backend/open_webui/routers/users.py:500-508` |
| `ui.params` (advanced parameters) | the person lacks `chat.controls` or `chat.params` | `backend/open_webui/routers/users.py:510-518` |
| `ui.toolServers` | the person lacks `features.direct_tool_servers` | `backend/open_webui/routers/users.py:520-530` |
| top-level `notifications`, and `ui.notifications.webhook_url` | the person lacks `features.webhooks` | `backend/open_webui/routers/users.py:532-547` |

The removal is silent: the request still succeeds, and a tab that shows a success toast still shows it, so a refused change looks saved until the page is reloaded (section 11.1). Admins are never filtered. The ground-truth note that admins skip permission checks applies here.

## 4. Key Concepts and Terminology

| Term | Meaning in this application | Source |
|---|---|---|
| **Settings window** (also "settings modal") | The full-screen dialogue holding every personal tab and, for admins, the admin tabs | `src/lib/components/chat/SettingsModal.svelte:508-912` |
| **Tab id** | The internal name of a tab, used in `?settings=` links and by the code; differs from the visible title for `shortcuts` (Keyboard) and `tools` (Integrations) | `src/lib/components/chat/SettingsModal.svelte:186-265` |
| **Account settings** | The JSON object saved on the person's `user` row (column `settings`). Its `ui` part holds almost every preference in this window; other top-level parts hold keyboard bindings (`keybindings`) and notification targets (`notifications`) | `backend/open_webui/models/users.py:138-141`, `:171`; `src/lib/components/chat/Settings/Shortcuts.svelte:63-66`; `backend/open_webui/utils/notifications.py:102-129` |
| **`ui` settings** (`user.settings.ui`) | The preferences object the browser holds in the `settings` store while signed in; saved field by field | `src/lib/stores/index.ts:106`, `:222-303`; `backend/open_webui/models/users.py:836-844` |
| **Browser-only preference** | A choice kept in the browser's local storage and not saved to the account, so it does not follow the person to another browser or computer: the colour theme, the interface language and a few dismissals (section 6.3) | `src/lib/components/chat/Settings/General.svelte:210-214`; `src/lib/i18n/index.ts:100-105` |
| **Interface fields** | The 63 preferences the `InterfaceSettings` model lists as "owned by the Interface settings panel"; the permission `settings.interface` governs all of them on save | `backend/open_webui/models/users.py:67-135`; `backend/open_webui/routers/users.py:492-498` |
| **Default Interface Settings** (admin preset) | Admin-chosen values for Interface fields, stored in the persistent setting `ui.default_interface_settings`, applied to every account that has not chosen its own value | `src/lib/components/admin/Settings/General.svelte:433-480`; `backend/open_webui/config.py:1712-1718`, `:3089` |
| **"Default" tag** | Small grey `Default` text beside an Interface switch, meaning the value shown comes from the admin preset rather than the person's own choice | `src/lib/components/common/Switch.svelte:30-32`; `src/lib/components/common/InterfaceSettings.svelte:153-160` |
| **Save on change** | Most switches and cycling buttons save the moment they are clicked, without the **Save** button | for example `src/lib/components/common/InterfaceSettings.svelte:610-612` |
| **Field-level patch** | A save sends only the keys that changed; keys left out keep their stored value, and a key sent as `null` is removed so the default applies again | `backend/open_webui/models/users.py:836-844` |
| **Silent filtering** | For non-admins the server drops keys the person may not change (section 3.3) and still answers with success | `backend/open_webui/routers/users.py:489-557` |
| **Settings search** | The search box above the tab list; it narrows the list to tabs containing a matching setting | `src/lib/utils/settings-search.ts:23-80` |
| **Dotted key** | A translation key such as `settings.personal.interface.inlineCitations.label` whose English text lives only in `src/lib/i18n/locales/en-US/translation.json`; other languages fall back to that English text when they have no translation | `src/lib/i18n/settings-translations.ts:3-19` |
| **Processing details** (MedIT GPT term) | The status lines, reasoning, code analysis and tool-call cards that **Hide Processing Details** removes | `src/lib/i18n/locales/en-US/translation.json:2923-2924` |
| **Inline citations** (MedIT GPT switch) | The numbered source chips such as `[1]` inside an answer; **Inline Citations** off removes them while the **Sources** list stays | `src/lib/i18n/locales/en-US/translation.json:2935-2936`; `src/lib/components/chat/Messages/ContentRenderer.svelte:128-138` |
| **Direct connection** | A personal OpenAI-compatible endpoint the person adds in Connections; requests to it come from the person's browser | `src/lib/components/chat/Settings/Connections.svelte:136-150` |
| **Keybinding** (chord) | A keyboard combination such as `Cmd+Shift+O`; `Cmd` is the Ctrl key outside macOS | `src/lib/shortcuts.ts:85-106`, `:134-161`, `:185` |

## 5. Workflows (Step by Step)

### 5.1 Open Settings and Choose a Tab

1. Open the sidebar user menu (picture and name at the bottom of the sidebar) and choose **Settings**, or press `Cmd+.` (`Ctrl+.` on Windows and Linux), or type `/settings` in the composer (section 2.1).
2. The window opens on **General**. Tabs are listed down the left on wide screens and across the top on narrow ones (section 2.2).
3. Choose a tab. Tabs the person cannot use are not listed at all (section 3.1).
4. Close with **Back** at the top of the tab list. The next plain open starts on General again (`src/lib/components/chat/SettingsModal.svelte:121-124`, `:518-527`).

To send someone straight to a tab, give them a link ending in `?settings=<tab id>`, for example `/?settings=interface` or `/?settings=account` (`src/routes/(app)/+layout.svelte:166-195`).

### 5.2 Find a Setting With the Search Box

1. Type in **Search** at the top of the tab list (`src/lib/components/chat/SettingsModal.svelte:529-544`).
2. The tab list shrinks to tabs that contain a match. When nothing matches, the list shows `No matches` (`:781-785`). Screen readers hear `Matching tabs: {count}` or `No matches` (`:546-552`).
3. Press **Enter** to open the first matching tab; press **Escape** to clear the search (`:427-436`).
4. The search only narrows the tab list. It does not scroll to or highlight the setting inside the tab, so the person still reads down the tab to find it.

How matching works (`src/lib/utils/settings-search.ts:13-80`):

- The index is built from the `en-US` dotted keys ending in `.label` or `.title` whose key belongs to the tab, plus each one's `.description`, the tab title, and the word `Personal` or `Admin` (`:47-63`). Each text is indexed both in English and in the current interface language, so English words work whatever language is shown (`:29-46`; English is loaded when the window opens, `src/lib/components/chat/SettingsModal.svelte:371-377`).
- Case, punctuation and accents on Latin letters are ignored (`src/lib/utils/settings-search.ts:13-21`). A tab matches when one entry contains **every** word typed (`:69-79`).
- Settings the person is not allowed to see are left out of the index, using the rules in section 3.2 (`src/lib/utils/settings-access.ts:24-69`).
- Text written with plain English keys rather than dotted keys is not indexed. In the Interface tab that includes `Show "What's New" Modal on Login`, every description shown under **UI Scale**, **Haptic Feedback**, **Floating Quick Actions** and **Image Compression**, and the button texts such as `Enter to Send` (`src/lib/components/common/InterfaceSettings.svelte:554`, `:688`, `:742`, `:1555`, `:1603-1604`, `:1966`).
- For admins, the admin **General** tab also matches every Interface label (because it hosts the Default Interface Settings preset), and the admin **Models** and **Interface** tabs match the General tab's parameter names (`src/lib/components/chat/SettingsModal.svelte:272`, `:290`, `:302`). A search for an Interface setting therefore lists both Interface and the admin General tab for an admin.

### 5.3 Change a Setting: When Is It Saved?

There are three save behaviours. Knowing which applies answers most "it didn't save" questions.

| Behaviour | Where | What the person sees | Source |
|---|---|---|---|
| **Saved immediately on click** | Every Interface switch and cycling button (Chat Direction, Landing Page Mode, Web Search in Chat, Enter Key Behavior, Terminal File Display, Default Upload Mode), UI Scale, Chat Background Image; Notifications switches; Enable Keyboard Shortcuts and every key rebinding; the Memory switch; the two Audio switches; the enable switch on a connection or tool server row | No toast for most switches; the value is already saved | `src/lib/components/common/InterfaceSettings.svelte:162-271`, `:610-612`; `src/lib/components/chat/Settings/Notifications.svelte:60-78`, `:219-221`; `src/lib/components/chat/Settings/Shortcuts.svelte:63-76`, `:134-136`; `src/lib/components/chat/Settings/Personalization.svelte:136-138`; `src/lib/components/chat/Settings/Audio.svelte:81-89` |
| **Saved by the Save button** | General (System Prompt and Advanced Parameters); Audio (engines, language, voice, speed, Kokoro precision); Connections and Integrations lists; Account profile and user variables; on Interface, the default model (the Save button also re-sends Font Family, which already saves when its box loses focus, and the image compression size, which its own dialogue saves) | `Settings saved successfully!` | `src/lib/components/chat/Settings/General.svelte:77-129`, `:321-330`; `src/lib/components/chat/Settings/Audio.svelte:161-182`; `src/lib/components/chat/Settings/Connections.svelte:29-55`; `src/lib/components/chat/Settings/Integrations.svelte:43-86`; `src/lib/components/chat/Settings/Account.svelte:238-247`; `src/lib/components/common/InterfaceSettings.svelte:242-256` |
| **Applied in this browser only** | Theme and Language on General | The change shows at once; nothing is sent to the server | `src/lib/components/chat/Settings/General.svelte:210-214`, `:255-257` |

Points worth knowing:

- The Personalization tab's **Save** button saves nothing itself; it only shows the success toast, because the Memory switch has already saved (`src/lib/components/chat/Settings/Personalization.svelte:105-110`).
- On Interface and Audio the success toast is shown without waiting for the server, so a failed save can show `Settings saved successfully!` and an error toast together (`src/lib/components/chat/Settings/Interface.svelte:17-20`; `src/lib/components/common/InterfaceSettings.svelte:251-255`; `src/lib/components/chat/Settings/Audio.svelte:164-182`). General waits for the server and shows only the error when the save fails (`src/lib/components/chat/Settings/General.svelte:123-128`).
- Pressing **Save** on the Interface tab also re-saves the default model (`models`): the first of the admin's default models when the admin has set any, otherwise the person's current first default model (`src/lib/components/common/InterfaceSettings.svelte:242-256`, `:394-397`). The Interface tab has no visible control for it.
- Key rebindings and **Reset Defaults** on the Keyboard tab are sent straight to the server without a toast (`src/lib/components/chat/Settings/Shortcuts.svelte:63-76`).

### 5.4 What Happens When a Setting Is Saved

1. The tab calls the window's `saveSettings` with only the changed keys, for example `{ hideProcessingDetails: true }` (`src/lib/components/common/InterfaceSettings.svelte:1370-1372`).
2. The window sends `POST /api/v1/users/user/settings/update` with body `{ "ui": { … } }` (`src/lib/components/chat/SettingsModal.svelte:438-444`; `src/lib/apis/users/index.ts:303-331`).
3. For non-admins the server drops any key the person may not change (section 3.3), then patches the stored `ui` object key by key: a value replaces the stored one, `null` removes it (`backend/open_webui/routers/users.py:489-549`; `backend/open_webui/models/users.py:825-847`).
4. The server publishes the event `user.settings_updated` (section 9) and returns the saved settings (`backend/open_webui/routers/users.py:550-557`; `backend/open_webui/events.py:135-137`).
5. The browser rebuilds its `settings` store as the admin preset overlaid with the saved personal values, and reloads the model list (`src/lib/components/chat/SettingsModal.svelte:445-450`).
6. A failure shows the error text as a toast (`src/lib/components/chat/SettingsModal.svelte:441-443`). The only error this endpoint raises itself is `USER_NOT_FOUND` (section 10); sign-in failures come from the shared sign-in check.

Each key is saved whole. Tabs that send a nested object (General's `params`, Audio's `audio`, Connections' `directConnections`, Integrations' `toolServers` and `terminalServers`) replace that whole object, so the last save of a key wins, including a save from an out-of-date window on another device (`backend/open_webui/models/users.py:839-843`).

### 5.5 Return a Setting to Its Default

| Setting | How to return it to the default | What is saved | Source |
|---|---|---|---|
| UI Scale | Click the value (for example `1.2x`) so it reads `Default` | `textScale: null` | `src/lib/components/common/InterfaceSettings.svelte:481-493` |
| Font Family | Click `Custom` so it reads `Default` | `fontFamily: null` | `src/lib/components/common/InterfaceSettings.svelte:296-316` |
| Chat Background Image | Click `Reset` | `backgroundImageUrl: null` | `src/lib/components/common/InterfaceSettings.svelte:851-857` |
| Web Search in Chat | Click `Always` so it reads `Default` | `webSearch: null` | `src/lib/components/common/InterfaceSettings.svelte:258-261` |
| System Prompt | Empty the box and press **Save** | `system: null` | `src/lib/components/chat/Settings/General.svelte:79-81` |
| An advanced parameter | Click its value until it reads `Default`, then **Save** | the parameter is left out of `params` | `src/lib/components/chat/Settings/General.svelte:82-121` |
| Keyboard shortcuts | **Reset Defaults** on the Keyboard tab | every binding back to the built-in set | `src/lib/components/chat/Settings/Shortcuts.svelte:73-76`, `:112-117` |
| Any Interface **switch** | No reset control: clicking a switch saves an explicit `true` or `false`, which from then on overrides the admin preset for that person | the chosen value | `src/lib/components/common/InterfaceSettings.svelte:153-160`; `src/lib/components/common/Switch.svelte:30-32` |

There is no "reset all settings" control for users, and no admin screen that edits or clears another person's settings. The server paths that write `user.settings` are the person's own save, the notification-target code, and saving a person's own tool or function valves (`backend/open_webui/routers/users.py:549`; `backend/open_webui/utils/notifications.py:129-218`; `backend/open_webui/models/tools.py:304`; `backend/open_webui/models/functions.py:391`). Whether an admin may reset a person's settings by other means is **TO BE CONFIRMED** (section 14).

### 5.6 Admins: Preset Interface Settings for Everyone

1. An admin opens Settings and the admin **General** tab (`admin:general`), then **Default Interface Settings** and **Configure** (`src/lib/components/admin/Settings/General.svelte:425-447`). The help line reads `Set system-wide interface defaults for every account. Personal settings override these defaults.` (`:435-437`).
2. The same Interface panel appears, in preset mode, with a count such as `3 settings configured` and a **Clear** button that empties the preset (`:452-480`). In preset mode nothing is applied to the admin's own screen and **Allow User Location** and **Auto-Copy Response to Clipboard** do not ask the browser for permission (`src/lib/components/common/InterfaceSettings.svelte:167-171`, `:199-203`).
3. The admin presses the admin General tab's **Save**. The preset is saved with the other admin settings as `DEFAULT_INTERFACE_SETTINGS` and stored in `ui.default_interface_settings` (`src/lib/components/admin/Settings/General.svelte:80-106`; `backend/open_webui/routers/auths.py:1220`, `:1276`).
4. From then on every account sees those values wherever it has not chosen its own, on its next page load: the server merges the preset under the account's own values when settings are fetched (`backend/open_webui/routers/users.py:457-474`, `:57-69`).
5. A person who changes a preset switch saves their own value and stops following the preset for that switch.

The first-boot value comes from the environment variable `DEFAULT_INTERFACE_SETTINGS` (JSON; code default `{}`) (`backend/open_webui/config.py:1712-1718`); after that the stored value wins, as for every persistent setting. The live preset is data and **TO BE CONFIRMED**.

### 5.7 Settings on Another Computer or Browser

- **What follows the account.** At sign-in on any browser the app loads the account's settings from the server, applies UI scale, font and keyboard bindings, then loads models (`src/routes/(app)/+layout.svelte:67-81`, `:222-235`). Everything section 7 lists as stored under `ui.` (or in `keybindings`) therefore appears on every device.
- **What stays in one browser.** The colour theme, the interface language and the items in section 6.3 are kept in that browser's local storage only.
- **No live refresh.** A window already open on another device is not told about the change: the settings-updated event goes to webhooks and event functions, not to browsers (`backend/open_webui/events.py:1069-1171`). The other device shows the change after a page reload.
- **Admin preset changes** reach people on their next page load (step 4 of section 5.6).

## 6. Data Model

### 6.1 Where Each Kind of Personal Setting Lives

| What | Stored in | Saved through | Source |
|---|---|---|---|
| Interface; General's system prompt and parameters (not Theme or Language); Audio; Notifications switches; Memory switch; Connections; Integrations; Enable Keyboard Shortcuts | `user.settings` → `ui` (JSON column `settings` on the `user` table) | `POST /api/v1/users/user/settings/update` | `backend/open_webui/models/users.py:171`, `:825-847`; `backend/open_webui/routers/users.py:482-562` |
| Keyboard bindings | `user.settings` → `keybindings` (top level, not inside `ui`) | the same endpoint, called directly by the Keyboard tab | `src/lib/components/chat/Settings/Shortcuts.svelte:63-76`; loaded by `src/routes/(app)/+layout.svelte:73` |
| Notification targets (webhooks) | `user.settings` → `notifications` (top level) | the notifications API; see `notifications-webhooks-events-and-banners.md` | `backend/open_webui/utils/notifications.py:102-129` |
| A person's own tool and function valves | `user.settings` → `tools.valves` and `functions.valves` (top level); each save rewrites the whole settings object | the tools and functions APIs; see `workspace-tools-tool-servers-mcp-and-terminals.md` and `functions-pipes-filters-actions-and-pipelines.md` | `backend/open_webui/models/tools.py:270-304`; `backend/open_webui/models/functions.py:383-391` |
| Name, profile picture, bio, gender, birth date | columns `name`, `profile_image_url`, `bio`, `gender`, `date_of_birth` on the `user` row | `POST /api/v1/auths/update/profile` | `backend/open_webui/models/users.py:152-159`; `src/lib/apis/auths/index.ts:481-485`; `backend/open_webui/routers/auths.py:319` |
| User variables (Account tab) | column `variables` on the `user` row | `POST /api/v1/users/user/variables/update` | `backend/open_webui/models/users.py:170`; `backend/open_webui/routers/users.py:651-671` |
| Location shared by **Allow User Location** | `user.info` → `location` | `POST /api/v1/users/user/info/update` | `src/lib/components/common/InterfaceSettings.svelte:173-185`; `backend/open_webui/routers/users.py:679-698` |
| Memories | the `memory` table | the memories API; see `memories.md` | `src/lib/components/chat/Settings/Personalization.svelte:14`, `:51-59` |
| Chats, archived chats, shared chats, files | chat and file tables | see `chat-conversations-history-and-organisation.md` and `files-uploads-and-storage.md` | `src/lib/components/chat/Settings/DataControls.svelte:9`, `:14-15` |
| API keys | managed on the Account tab; see `authentication-and-sign-in.md` | not described here | `src/lib/components/chat/Settings/Account.svelte:180-200` |
| Admin interface preset | the `config` table, key `ui.default_interface_settings` | admin General tab | `backend/open_webui/config.py:3089`; `backend/open_webui/routers/auths.py:1276` |

Shape of `user.settings` (illustrative, invented values):

```json
{
  "ui": { "hideProcessingDetails": true, "showInlineCitations": false, "system": "Answer in Canadian English.", "params": { "temperature": 0.4 } },
  "keybindings": { "newChat": "Cmd+Shift+O" },
  "notifications": { "targets": [] }
}
```

The `UserSettings` model allows any top-level key and any content under `ui` (`backend/open_webui/models/users.py:138-141`). The `InterfaceSettings` model (`:67-135`) is used only for its list of field names when filtering a save (section 3.3); stored values are not validated against it, and the admin preset is accepted as a free-form object (`backend/open_webui/routers/auths.py:1220`).

### 6.2 Keys Written From Outside the Settings Window

These live in the same `ui` object, so they follow the account between devices, but they are changed elsewhere in the app:

| Key | Written by | Source |
|---|---|---|
| `models` (default model list) | **Set as default** in the model selector (toast `Default model updated`); also re-saved by the Interface tab's Save (section 5.3) | `src/lib/components/chat/ModelSelector.svelte:26-36` |
| `pinnedModels` | pinning models in the selector, sidebar and workspace | `src/lib/components/chat/ModelSelector.svelte:38-46`; `src/lib/components/layout/Sidebar/PinnedModelList.svelte:48`, `:79`; `src/lib/components/workspace/Models.svelte:322`; `src/lib/components/admin/Settings/Models.svelte:669` |
| `pinnedMenuItems`, `pinnedNotesOrder` | sidebar pins and note ordering | `src/lib/components/layout/Sidebar.svelte:234`; `src/lib/components/layout/Sidebar/UserMenu.svelte:71`; `src/lib/components/layout/Sidebar/PinnedNoteList.svelte:50` |
| `recentEmojis` | the emoji picker | `src/lib/components/common/EmojiPicker.svelte:53` |
| `params.tool_approval_mode` | the tool approval choice in chat | `src/lib/components/chat/Chat.svelte:436-455` |
| `version` | closing the "What's New" changelog window | `src/lib/components/ChangelogModal.svelte:41-46` |

Two `ui` keys are read by the app but have no control anywhere in v0.11.4: `splitLargeChunks` (read when streaming, `src/lib/components/chat/Chat.svelte:3924`; it is an Interface field, so an admin preset can set it) and `notificationSoundAlways` (read by `src/routes/+layout.svelte:745-748`). Their only possible sources are the admin preset or a direct API call; whether production sets them is **TO BE CONFIRMED**.

### 6.3 Browser Local Storage (Not Saved to the Account)

| Key | Holds | Default | Source |
|---|---|---|---|
| `theme` | Colour theme: `system`, `dark`, `oled-dark`, `light` (and `her` when the admin's easter-egg feature is on) | `system`, set on first page load | `src/app.html:52-54`; `src/lib/components/chat/Settings/General.svelte:132`, `:210-214` |
| `locale` | Interface language code, for example `fr-CA` | none: chosen at first visit (section 7.2.2) | `src/lib/i18n/index.ts:100-105`; `src/routes/+layout.svelte:1254-1265` |
| `dismissedUpdateToast` | Time an admin closed the update notice; the check is skipped for 24 hours afterwards | none | `src/routes/(app)/+layout.svelte:370-382`, `:433` |
| `version` | Last version whose changelog was closed (also saved to `ui.version`) | none | `src/lib/components/ChangelogModal.svelte:42` |
| `showControls` | Whether the chat controls panel was open | `false` | `src/routes/(app)/+layout.svelte:383-388` |
| `selectedTerminalId` | The terminal last selected in the composer | none | `src/routes/(app)/+layout.svelte:237`, `:390-397` |
| `chat-input…` | Unsent composer drafts; cleared each time the app loads | none | `src/routes/(app)/+layout.svelte:58-65`, `:222` |
| `settings` | Legacy: read only by the shared-chat page for visitors who are not signed in; nothing in v0.11.4 writes it | none | `src/routes/s/[id]/+page.svelte:77-89` |

Clearing the browser's site data resets everything in this table (theme back to System, language re-detected) but leaves the account settings on the server untouched.

### 6.4 How the Browser Copy Is Built

| Moment | The `settings` store becomes | Source |
|---|---|---|
| App load after sign-in | `GET /api/v1/users/user/settings`: the admin preset with the account's own `ui` values laid over it; the server skips the person's `null` values so the preset shows through | `src/routes/(app)/+layout.svelte:67-81`; `backend/open_webui/routers/users.py:57-69`, `:457-474` |
| Opening the Settings window | Unchanged; the window separately fetches the account's own values (`?raw=true`) to decide which switches show the `Default` tag | `src/lib/components/chat/SettingsModal.svelte:89-98`, `:100-126` |
| After any save from the window | The admin preset (from `/api/config`) with the saved personal values laid over it | `src/lib/components/chat/SettingsModal.svelte:72-87`, `:445-449` |

If the settings request fails at app load, the app shows `Failed to load Interface settings` and stops there, so the main area keeps showing the loading spinner until the page is reloaded successfully (`src/routes/(app)/+layout.svelte:231-235`, `:401`, `:450-462`).

## 7. Settings and Configuration

### 7.1 How to Read the Tab Tables

- **Label** is the English text shown in the window, resolved from the dotted key; the number is its line in `src/lib/i18n/locales/en-US/translation.json`. Labels written with plain English keys are marked "plain key".
- **Stored as** names where the value is kept: `ui.<key>` means the account's settings on the server (it follows the person to other devices); **browser** means the browser's local storage only (section 6.3).
- **Default** is the code default used when neither the person nor the admin preset has a value. For Interface fields, an admin preset value replaces the code default (section 5.6); the live preset is **TO BE CONFIRMED**.
- **Saves** is "click" (saved immediately) or "Save" (needs the tab's **Save** button), as described in section 5.3.

### 7.2 General (`general`)

**Purpose.** Look and language for this browser, the person's default system prompt, and default model parameters for their chats. **Who sees it.** Everyone; the System Prompt and Advanced Parameters sections are hidden by permissions (section 3.2). **Component.** `src/lib/components/chat/Settings/General.svelte`. Heading `General` (line 2870).

The task brief for this area mentions notifications under General; in v0.11.4 they have their own Notifications tab (section 7.4).

#### 7.2.1 WebUI Settings Section

Section heading `WebUI Settings` (line 2867; `src/lib/components/chat/Settings/General.svelte:223-226`).

| Label | What it does | Stored as | Default | Saves | Source |
|---|---|---|---|---|---|
| **Theme** (2869) | `Choose the color theme used by the interface.` (2868). Options `⚙️ System`, `🌑 Dark`, `🌃 OLED Dark`, `☀️ Light`, and `🌷 Her` when the easter-egg feature is on | browser `theme` | `system` | applied at once, this browser only | `src/lib/components/chat/Settings/General.svelte:227-245`, `:132`, `:210-214` |
| **Language** (2818) | `Choose the language used for interface text.` (2817). Lists the 64 entries of `src/lib/i18n/locales/languages.json`, without `Doge (🐶)` unless the easter-egg feature is on | browser `locale` | see 7.2.2 | applied at once, this browser only | `src/lib/components/chat/Settings/General.svelte:247-263`, `:134-138`; `src/lib/i18n/index.ts:124-128` |

Below the language list, while the interface is in English (US) and no enterprise licence is recorded, the tab shows `Couldn't find your language?` with the link `Help us translate Open WebUI!` to the upstream contribution guide (`src/lib/components/chat/Settings/General.svelte:264-278`). The link text is licence-protected branding and stays as written.

The easter-egg feature is the environment variable `ENABLE_EASTER_EGGS`, code default **on** (`backend/open_webui/env.py:966`; sent as `features.enable_easter_eggs`, `backend/open_webui/main.py:2350`), so by default the Her theme and the Doge language are offered. The production value is **TO BE CONFIRMED**.

#### 7.2.2 How the Interface Language Is Chosen

Language is a per-browser choice; it is not part of the account.

1. A `?lang=<code>` parameter in the address wins, then the language saved in this browser (`locale`) (`src/lib/i18n/index.ts:88-106`).
2. With no saved language, the language library detects one from the browser's own language preferences and, because it is configured to cache in local storage, saves it as `locale` while the app starts (`src/lib/i18n/index.ts:90-106`; library `i18next` with its browser language detector, `package.json:110-111`). The root layout then applies the site default language, or else the best match among the browser's preferred languages, only when `locale` is still empty (`src/routes/+layout.svelte:1254-1265`; `src/lib/utils/index.ts:1383-1391`). Reading the installed library, that saving happens before the check, so on an ordinary first visit the browser's language wins over the site default. This reading of library behaviour is **TO BE CONFIRMED** by a test in a fresh browser profile (section 14).
3. Choosing a language on the General tab switches immediately and saves it in this browser (`src/lib/components/chat/Settings/General.svelte:255-257`; `src/lib/i18n/index.ts:102`, `:125-128`).
4. The site default language comes from the environment variable `DEFAULT_LOCALE` (code default empty, `backend/open_webui/config.py:1672`), sent to the browser as `default_locale` (`backend/open_webui/main.py:2315`). A persistent key `ui.default_locale` is seeded from it (`backend/open_webui/config.py:3086`), but `/api/config` sends the environment value and no admin screen edits either, so a change needs the environment variable and a restart. The production value is **TO BE CONFIRMED**.
5. Settings labels (dotted keys) missing from a language fall back to an admin translation override, then to the bundled translation, then to an admin English override, then to the English text (`src/lib/i18n/settings-translations.ts:3-19`). This is why the two MedIT GPT switches show in English in every other language (section 12).

*Working tree only:* the uncommitted change to `src/lib/i18n/index.ts` maps a detected browser language to a bundled translation (for example a regional code to its main language when the regional one is not bundled) and adds `en-US` as the last fallback after the site default (`src/lib/i18n/index.ts:75-86`, `:93`, `:105`). Section 12.2 has the details.

#### 7.2.3 System Prompt Section

Shown when the person may edit the system prompt (section 3.2; `src/lib/components/chat/Settings/General.svelte:281-294`).

| Label | What it does | Stored as | Default | Saves | Source |
|---|---|---|---|---|---|
| **System Prompt** (section title, 2866) | `Set the default system prompt for new chats.` (2865). A text box with the placeholder `Enter system prompt here`. In a chat, a system prompt set in the chat's own controls wins; this one is used when the chat has none | `ui.system` (removed when emptied) | empty | Save | `src/lib/components/chat/Settings/General.svelte:79-81`, `:286-291`; `src/lib/components/chat/Chat.svelte:3495-3499` |

#### 7.2.4 Advanced Parameters Section

Shown when the person may edit parameters (section 3.2). The section title is `Advanced Parameters` (2864); the row **Model parameters** (2820), `Show or hide custom generation parameters.` (2819), has a **Show**/**Hide** button that opens the list (`src/lib/components/chat/Settings/General.svelte:296-318`). The list is `src/lib/components/chat/Settings/Advanced/AdvancedParams.svelte`; each row shows `Default` until a value is chosen, and **Save** stores the set as `ui.params` (`src/lib/components/chat/Settings/General.svelte:82-124`). Values left at `Default` are not saved.

How these personal values combine with a model's and a chat's own parameters is in `chat-completion-pipeline-and-generation-tasks.md` (section 7.5). In the browser, the chat's own controls override these personal values (`src/lib/components/chat/Chat.svelte:3583-3587`), and for **Stream Chat Response** a value set on the model wins over the personal one (`:3488-3492`).

| Label (line) | Key in `ui.params` | Control | Who sees it | Source (`AdvancedParams.svelte`) |
|---|---|---|---|---|
| **Stream Chat Response** (2853) | `stream_response` | `Default`, `On`, `Off` | everyone | `:114-146` |
| **Stream Delta Chunk Size** (2855) | `stream_delta_chunk_size` | `Default` or a number | admins | `:148-186` |
| **Context Compaction Threshold** (2822) | `compact_token_threshold` | `Default` or a number | admins | `:188-236` |
| **Function Calling** (2826) | `function_calling` | `Default`, native, legacy | everyone | `:239-270` |
| **Reasoning Tags** (2845) | `reasoning_tags` | `Default`, enabled, disabled, custom start and end tags | everyone | `:272-336` |
| **Seed** (2849) | `seed` | number | everyone | `:338-380` |
| **Stop Sequence** (2851) | `stop` | comma-separated text, saved as a list | everyone | `:382-423`; `src/lib/components/chat/Settings/General.svelte:92`, `:143` |
| **Temperature** (2857) | `temperature` | slider and number | everyone | `:425-460` |
| **Reasoning Effort** (2843) | `reasoning_effort` | text | everyone | `:462-502` |
| `logit_bias` (2828) | `logit_bias` | text | everyone | `:504-548` |
| `max_tokens` (2829) | `max_tokens` | slider and number | everyone | `:550-590` |
| `top_k` (2860), `top_p` (2861), `min_p` (2830) | same names | number; `top_k` accepts whole numbers 0 to 1000 | everyone | `:59-70`, `:592-727` |
| `frequency_penalty` (2824), `presence_penalty` (2841) | same names | slider and number | everyone | `:729-807` |
| `mirostat` (2831), `mirostat_eta` (2832), `mirostat_tau` (2833) | same names | slider and number | everyone | `:809-924` |
| `repeat_last_n` (2846), `tfs_z` (2858), `repeat_penalty` (2847) | same names | slider and number | everyone | `:926-1044` |
| `use_mmap` (2863), `use_mlock` (2862), shown with "(Ollama)" | same names | `Default` or a switch | admins | `:1046-1134` |
| `think` (2859) "(Ollama)" | `think` | cycles `Default`, `On`, `Custom` (a typed level, starting at `medium`), `Off` | everyone | `:1136-1190` |
| `format` (2823) "(Ollama)" | `format` | `Default` or `JSON`; `JSON` opens a box for `json` or a JSON schema | everyone | `:1192-1229` |
| `num_ctx` (2835), `num_batch` (2834), `num_keep` (2837) "(Ollama)" | same names | number | everyone | `:1276-1360` |
| `num_thread` (2838), `num_gpu` (2836), `keep_alive` (2827) "(Ollama)" | same names | number or text | admins | `:1362-1490` |
| **Add Custom Parameter** (plain key) | `custom_params` | name and value pairs | admins | `:1492-1561`; `src/lib/components/chat/Settings/General.svelte:118-120` |

The descriptions shown as tooltips include `The temperature of the model. Increasing the temperature will make the model answer more creatively.` (2856) and `Sets the random number seed to use for generation. Setting this to a specific number will make the model generate the same text for the same prompt.` (2848). The admin-only rows match the search rule in `src/lib/utils/settings-access.ts:39-45`.

**Save.** The tab's **Save** button sends the system prompt and parameters together and shows `Settings saved successfully!` only after the server accepts; on failure only the error toast appears (`src/lib/components/chat/Settings/General.svelte:77-129`, `:321-330`; `src/lib/components/chat/SettingsModal.svelte:792-798`).

### 7.3 Interface (`interface`)

**Purpose.** How chats look and behave for this person. **Who sees it.** Admins, and users with the permission `settings.interface` (default on); without it the tab is hidden and the server discards every Interface field the person sends, wherever it comes from (sections 3.1, 3.3). **Components.** The tab `src/lib/components/chat/Settings/Interface.svelte` (heading `Interface`, line 2985) wraps the shared panel `src/lib/components/common/InterfaceSettings.svelte`; the admin preset editor reuses the same panel (section 5.6).

**Saving.** Every switch and cycling button saves when clicked (section 5.3). The tab's **Save** button re-sends Font Family, the image compression size and the default model, then shows `Settings saved successfully!` (`src/lib/components/chat/Settings/Interface.svelte:14-37`; `src/lib/components/common/InterfaceSettings.svelte:242-256`). Font Family is also saved when its box loses focus (`:589`), and the compression size by its own dialogue (`:429-435`).

**"Default" tag.** A switch shows a grey `Default` beside it when the value comes from the admin preset because the person has not chosen one (`src/lib/components/common/InterfaceSettings.svelte:153-160`; `src/lib/components/common/Switch.svelte:30-32`). Each switch's tooltip reads `Enabled` or `Disabled` (`src/lib/components/common/Switch.svelte:19-27`).

All defaults below are from `src/lib/components/common/InterfaceSettings.svelte:318-409` unless stated. Every key is an Interface field stored as `ui.<key>` on the account.

#### 7.3.1 UI Section

Section heading `UI` (line 2971; `src/lib/components/common/InterfaceSettings.svelte:466-468`).

| Label (line) | What it does | Key | Default | Source |
|---|---|---|---|---|
| **UI Scale** (2990) | Plain-key description `Set a local zoom level for the app interface.` Click `Default` to show a slider from `1x` to `1.5x` with **Decrease UI Scale** (2898) and **Increase UI Scale** (2934) buttons in steps of 0.1; click the value to return to `Default`. Despite "local", the value is saved to the account and applied on every device at sign-in | `textScale` | none (`1x`) | `:470-556`; `src/routes/(app)/+layout.svelte:75` |
| **Font Family** (2921) | `Use a local font family for the app interface.` (2920). `Default` or `Custom`; the box (placeholder `Aptos`) names a font that must be installed on the device, previews as you type and saves when the box loses focus | `fontFamily` | none (app font) | `:558-596`, `:273-316` |
| **Accessibility Mode** (2872) | `Enable accessibility-focused visual enhancements.` (2871), for example stronger focus outlines on switches | `highContrastMode` | off | `:598-619`; `src/lib/components/common/Switch.svelte:39-42` |
| **Display Chat Title in Tab** (2904) | `Use the active chat title as the browser tab title.` (2903) | `showChatTitleInTab` | on | `:621-642`; `src/lib/components/chat/Chat.svelte:4171` |
| **Allow User Location** (2874) | `Share your current location with features that can use it.` (2873). Switching on asks the browser for the location, saves it to the account's `info` and shows `User location successfully retrieved.`; if the browser refuses, the switch turns itself off and the browser's error is shown | `userLocation` (plus `info.location`) | off | `:644-665`, `:167-188` |
| **Haptic Feedback (Android)** (2922, 2881) | Plain-key description `Use device vibration feedback on supported Android devices.` | `hapticFeedback` | off | `:667-690` |
| **Copy Formatted Text** (2897) | `Copy rich formatted content instead of plain text.` (2896) | `copyFormatted` | off | `:692-713` |
| **Toast Notifications for New Updates** (2989) | Admins only. `Show update toasts to admins when new versions are available.` (2988) | `showUpdateToast` | on | `:715-737`; `src/routes/(app)/+layout.svelte:428` |
| **Show "What's New" Modal on Login** (plain key) | Admins only. `Open the changelog modal after sign-in when enabled.` | `showChangelog` | on | `:739-760`; `src/routes/(app)/+layout.svelte:355-357` |

#### 7.3.2 Chat Section

Section heading `Chat` (line 2968; `:763-765`).

| Label (line) | What it does | Key | Default | Source |
|---|---|---|---|---|
| **Enable Message Queue** (2912) | `Queue outgoing messages instead of interrupting active responses.` (2911) | `enableMessageQueue` | on | `:767-788` |
| **Chat Direction** (2889) | `Choose automatic, left-to-right, or right-to-left text flow.` (2888). Cycles `Auto`, `LTR`, `RTL` | `chatDirection` (`auto`, `LTR`, `RTL`) | `Auto` | `:790-814`, `:226-235` |
| **Landing Page Mode** (2946) | `Choose whether the app opens to the default home or chat view.` (2945). Toggles `Default` and `Chat` | `landingPageMode` (`''` or `chat`) | `Default` | `:816-840`, `:162-165` |
| **Chat Background Image** (2885) | `Upload or reset the image shown behind chat content.` (2884). `Upload` accepts GIF, WebP, JPEG or PNG; `Reset` removes it. The picture itself is saved inside the account settings. A background set on the selected model wins over this one | `backgroundImageUrl` | none (an enterprise licence may supply one) | `:842-869`, `:437-463`; `src/lib/components/chat/Chat.svelte:185-188` |
| **Chat Bubble UI** (2887) | `Render messages in compact bubble containers.` (2886) | `chatBubble` | on | `:871-892` |
| **Display the Username Instead of You in the Chat** (2910) | Shown only while Chat Bubble UI is off. `Show your username label instead of You in chat bubbles.` (2909) | `showUsername` | off | `:894-917` |
| **Widescreen Mode** (2994) | `Use a wider chat layout on large displays.` (2993) | `widescreenMode` | off | `:919-940` |
| **Temporary Chat by Default** (2980) | Shown to admins and to users with `chat.temporary`. `Start new chats as temporary unless changed.` (2979) | `temporaryChatByDefault` | off | `:942-965` |
| **Fade Effect for Streaming Text** (2916) | `Fade streaming text as it arrives.` (2915) | `chatFadeStreamingText` | on | `:967-988` |
| **Render Markdown in User Messages** (2960) | `Format Markdown syntax in your own messages.` (2959) | `renderMarkdownInUserMessages` | on | `:990-1011` |
| **Render Markdown in Assistant Messages** (2956) | `Format Markdown syntax in assistant responses.` (2955) | `renderMarkdownInAssistantMessages` | on | `:1013-1034` |
| **Render Markdown in Previews** (2958) | `Format Markdown in previews and compact content surfaces.` (2957) | `renderMarkdownInPreviews` | on | `:1036-1057` |
| **Title Auto-Generation** (2987) | `Generate chat titles automatically from conversation content.` (2986) | `title.auto` (inside the `title` object) | on | `:1059-1080`, `:190-197` |
| **Follow-Up Auto-Generation** (2919) | `Generate suggested follow-up prompts after responses.` (2918) | `autoFollowUps` | on | `:1082-1103` |
| **Chat Tags Auto-Generation** (2893) | `Generate tags for chats automatically.` (2892) | `autoTags` | on | `:1105-1126` |
| **Auto-Copy Response to Clipboard** (2883) | `Copy the latest assistant response when it completes.` (2882). Switching on first checks clipboard access; if the browser refuses, the switch turns itself off with an error toast (section 10) | `responseAutoCopy` | off | `:1128-1149`, `:199-224` |
| **Response Auto-Scroll** (2962) | `Follow assistant responses as they are generated.` (2961) | `scrollOnResponseGeneration` | on | `:1151-1172` |
| **Scroll On Branch Change** (2966) | `Scroll to the active branch when switching response branches.` (2965) | `scrollOnBranchChange` | on | `:1174-1195` |
| **Insert Suggestion Prompt to Input** (2942) | `Place selected suggestion text into the composer.` (2941) | `insertSuggestionPrompt` | off | `:1197-1218` |
| **Keep Follow-Up Prompts in Chat** (2944) | `Keep generated follow-up prompts visible in the chat.` (2943) | `keepFollowUpPrompts` | off | `:1220-1241` |
| **Insert Follow-Up Prompt to Input** (2938) | `Insert selected follow-up prompts directly into the composer.` (2937) | `insertFollowUpPrompt` | off | `:1243-1264` |
| **Regenerate Menu** (2954) | `Show the regenerate action menu for assistant responses.` (2953) | `regenerateMenu` | on | `:1266-1287` |
| **Always Collapse Code Blocks** (2878) | `Collapse code blocks by default.` (2877) | `collapseCodeBlocks` | off | `:1289-1310` |
| **Always Expand Details** (2880) | `Open detail blocks by default.` (2879) | `expandDetails` | off | `:1312-1333` |
| **Inline Citations** (2936), MedIT GPT | See 7.3.7 | `showInlineCitations` | **on** | `:1335-1356` |
| **Hide Processing Details** (2924), MedIT GPT | See 7.3.7 | `hideProcessingDetails` | **off** | `:1358-1379` |
| **Chat Hover Previews** (2891) | `Show a floating preview of recent messages when hovering a chat in the sidebar.` (2890) | `chatHoverPreview` | on | `:1381-1402` |
| **Display Multi-model Responses in Tabs** (2908) | `Group multi-model responses into tabs.` (2907) | `displayMultiModelResponsesInTabs` | off | `:1404-1425` |
| **Terminal File Display** (2982) | `Choose where terminal display_file results appear by default.` (2981). Toggles `Sidebar` and `Inline` | `terminalFileDisplay` | `Sidebar` | `:1427-1450` |
| **Show Files on Terminal Select** (2974) | `Open the file browser after selecting a terminal.` (2973) | `showFilesOnTerminalSelect` | on | `:1452-1473` |
| **Terminal Preview Allow Same Origin** (2984) | `Allow terminal previews to access same-origin browser APIs.` (2983) | `terminalPreviewAllowSameOrigin` | off | `:1475-1496` |
| **Stylized PDF Export** (2978) | `Use styled formatting when exporting chats to PDF.` (2977) | `stylizedPdfExport` | on | `:1498-1519` |
| **Floating Quick Actions** (2917) | Plain-key description `Show the floating quick-action toolbar in chat.` While on, **Manage** (aria label **Open Modal To Manage Floating Quick Actions**, 2947) opens the Quick Actions dialogue (7.3.8) | `showFloatingActionButtons`; buttons in `floatingActionButtons` | on; built-in buttons | `:1521-1557`, `:421-427` |
| **Web Search in Chat** (2992) | `Set web search availability for new chats.` (2991). Toggles `Default` and `Always`; `Always` turns web search on by itself when the site offers web search, the person has `features.web_search`, and every selected model supports it | `webSearch` (`always` or none) | `Default` | `:1559-1581`, `:258-261`; `src/lib/components/chat/Chat.svelte:349-354` |

#### 7.3.3 Input Section

Section heading `Input` (line 2970; `:1583-1585`).

| Label (line) | What it does | Key | Default | Source |
|---|---|---|---|---|
| **Enter Key Behavior** (2914) | `Choose whether Enter sends immediately or uses Ctrl+Enter.` (2913). Toggles `Enter to Send` and `Ctrl+Enter to Send` | `ctrlEnterToSend` | `Enter to Send` | `:1587-1611`, `:237-240` |
| **Rich Text Input for Chat** (2964) | `Use the rich composer instead of a plain textarea.` (2963) | `richTextInput` | on | `:1613-1634` |
| **Prompt Autocompletion** (2952) | Shown only when the site setting `task.autocomplete.enable` is on. `Suggest completions while composing prompts.` (2951) | `promptAutocomplete` | off | `:1636-1659` |
| **Show Formatting Toolbar** (2976) | Shown only while Rich Text Input is on. `Show formatting controls in the rich text composer.` (2975) | `showFormattingToolbar` | off | `:1661-1683` |
| **Insert Prompt as Rich Text** (2940) | Shown only while Rich Text Input is on. `Paste inserted prompts as rich text when possible.` (2939) | `insertPromptAsRichText` | off | `:1685-1706` |
| **Paste Large Text as File** (2950) | `Convert long pasted text into a file attachment.` (2949) | `largeTextAsFile` | off | `:1709-1730` |

#### 7.3.4 Artifacts Section

Section heading `Artifacts` (line 2967; `:1732-1734`). These control what embedded content (artifacts and previews) may do inside its sandbox. Their security implications belong to the platform maintainer; this table records only what each switch is called and its default.

| Label (line) | What it does | Key | Default | Source |
|---|---|---|---|---|
| **Detect Artifacts Automatically** (2902) | `Detect generated artifacts and show them in the artifact workspace.` (2901) | `detectArtifacts` | on | `:1736-1757` |
| **iframe Sandbox Allow Scripts** (2932) | `Allow scripts inside sandboxed iframes.` (2931) | `iframeSandboxAllowScripts` | on | `:1759-1780` |
| **iframe Sandbox Allow Same Origin** (2930) | `Allow artifacts to access same-origin browser APIs inside the sandbox.` (2929) | `iframeSandboxAllowSameOrigin` | off | `:1782-1803` |
| **iframe Sandbox Allow Forms** (2928) | `Allow forms inside sandboxed artifact iframes.` (2927). The switch shows on by default, but embeds returned by tools treat a never-saved value as off (`src/lib/components/common/ToolCallDisplay.svelte:192`; `src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte:316`), while artifacts and other previews treat it as on (`src/lib/components/chat/Artifacts.svelte:258`) | `iframeSandboxAllowForms` | on (see note) | `:1805-1826` |
| **iframe Sandbox Allow Downloads** (2926) | `Allow downloads inside sandboxed iframes.` (2925) | `iframeSandboxAllowDownloads` | on | `:1828-1849` |

#### 7.3.5 Voice Section

Section heading `Voice` (line 2972; `:1851-1853`).

| Label (line) | What it does | Key | Default | Source |
|---|---|---|---|---|
| **Allow Voice Interruption in Call** (2876) | `Let speech interrupt the assistant during a voice call.` (2875) | `voiceInterruption` | off | `:1855-1876` |
| **Display Emoji in Call** (2906) | `Show emoji feedback in the call interface.` (2905) | `showEmojiInCall` | off | `:1878-1899` |

#### 7.3.6 File Section

Section heading `File` (line 2969; `:1901-1903`).

| Label (line) | What it does | Key | Default | Source |
|---|---|---|---|---|
| **Default Upload Mode** (2900) | `Attach files with full content or focused retrieval by default.` (2899). Toggles `Using Focused Retrieval` and `Using Entire Document` | `defaultUploadContext` (`focused`, `full`) | `Using Focused Retrieval` | `:1905-1930` |
| **Image Compression** (2933) | Plain-key description `Compress uploaded images before sending or storage.` While on, **Manage** (aria label **Open Modal To Manage Image Compression**, 2948) opens the size dialogue (7.3.8) | `imageCompression`; size in `imageCompressionSize` | off; no size | `:1932-1968` |
| **Compress Images in Channels** (2895) | Shown only while Image Compression is on. `Apply image compression to channel uploads too.` (2894). The switch shows on by default, but the channel composer compresses only when this has been saved as on (`src/lib/components/channel/MessageInput.svelte:383-384`) | `imageCompressionInChannels` | on (see note) | `:1970-1993` |

#### 7.3.7 The MedIT GPT Switches: Inline Citations and Hide Processing Details

Both sit in the **Chat** section between **Always Expand Details** and **Chat Hover Previews**, are ordinary Interface fields (so the permission `settings.interface` governs them and an admin can preset them), and save on click.

| | Inline Citations | Hide Processing Details |
|---|---|---|
| Label | `Inline Citations` (`src/lib/i18n/locales/en-US/translation.json:2936`) | `Hide Processing Details` (`:2924`) |
| Description (working tree) | `Show source links within responses. When off, sources are still listed below each response.` (`:2935`) | `Show "Thinking..." instead of status updates, tool calls, reasoning, and code analysis while a response is generated, and keep them hidden afterwards. Tool approval requests and images or embeds from tools still appear.` (`:2923`) |
| Key | `ui.showInlineCitations` (`backend/open_webui/models/users.py:99`; `src/lib/stores/index.ts:232`) | `ui.hideProcessingDetails` (`backend/open_webui/models/users.py:100`; `src/lib/stores/index.ts:233`) |
| Default | on (`src/lib/components/common/InterfaceSettings.svelte:79`, `:357`) | off (`:80`, `:358`) |
| Switch | `src/lib/components/common/InterfaceSettings.svelte:1335-1356` | `src/lib/components/common/InterfaceSettings.svelte:1358-1379` |
| Effect when changed from the default | Citation markers such as `[1]` are removed from answer text outside code, so no chips appear; the **Sources** list under the answer stays. A model whose `citations` capability is off has markers removed whatever this says (`src/lib/components/chat/Messages/ContentRenderer.svelte:128-138`) | While a response is generated, a single `Thinking...` line replaces status lines; status history, reasoning, code analysis, tool-call cards that need nothing from the user, code-execution chips and the task list above the composer stay hidden afterwards. Tool approval cards and images or embeds from tools still show (`src/lib/components/chat/Messages/ResponseMessage.svelte:197-221`, `:944`; `src/lib/components/chat/MessageInput.svelte:1792`; `src/lib/components/common/ToolCallDisplay.svelte:145`, `:181`, `:199`) |
| Scope | Display only; stored chats are unchanged and switching back restores every answer at once | Display only; switching off brings the details back on old and new chats |
| Deep reference | `chat-composer-and-message-display.md` section 5.23 | `chat-composer-and-message-display.md` section 5.22 |

In any language other than English (US) both labels and descriptions appear in English unless an admin has added translations (section 7.2.2, step 5). Section 12 records which parts are committed and which are only in the working tree.

#### 7.3.8 Interface Sub-Dialogues

| Dialogue | Opened by | Contents | Saved as | Source |
|---|---|---|---|---|
| **Quick Actions** | **Manage** beside Floating Quick Actions | The list of floating buttons shown when text is selected in a response. `Default` uses the built-in `Ask` and `Explain` buttons (`Default action buttons will be used.`); `Custom` lets the person add buttons with **Button Label**, **Button ID** and **Button Prompt**; **Save** applies | `ui.floatingActionButtons` (each with `id`, `label`, `input`, `prompt`) | `src/lib/components/chat/Settings/Interface/ManageFloatingActionButtonsModal.svelte:35-180`; `backend/open_webui/models/users.py:58-64` |
| **Manage** (image compression) | **Manage** beside Image Compression | **Image Max Compression Size** with **Width** and **Height** boxes; **Save** applies | `ui.imageCompressionSize` (`width`, `height`) | `src/lib/components/chat/Settings/Interface/ManageImageCompressionModal.svelte:31-107`; `backend/open_webui/models/users.py:51-55` |

The site also has an admin-wide image compression size (`file.image_compression_width` and `file.image_compression_height`, sent as `file.image_compression`). It acts as an upper bound on uploaded images whether or not the person switches compression on (`backend/open_webui/main.py:2416-2419`; `src/lib/components/chat/MessageInput.svelte:1134-1160`; `src/lib/components/channel/MessageInput.svelte:383-386`). See `files-uploads-and-storage.md`.

The Quick Actions buttons appear when the person selects text in a finished response (`src/lib/components/chat/Messages/ResponseMessage.svelte:867-869`; `src/lib/components/chat/Messages/ContentRenderer.svelte:196-204`, `:364-368`).

### 7.4 Notifications (`notifications`)

**Purpose.** How the person is told that a response finished while they were elsewhere. **Who sees it.** Everyone; the **Notification Targets** part only when personal webhooks are allowed (section 3.2). **Component.** `src/lib/components/chat/Settings/Notifications.svelte`, heading `Notifications` (line 2999). **Deep reference.** `notifications-webhooks-events-and-banners.md`.

| Label (line) | What it does | Stored as | Default | Saves | Source |
|---|---|---|---|---|---|
| **Browser Notifications** (2996) | Plain-key description `Allow browser notifications for completed responses.` Switching on asks the browser for permission; if refused, the switch stays off and an error toast explains (section 10) | `ui.notificationEnabled` | off | click | `src/lib/components/chat/Settings/Notifications.svelte:60-78`, `:198-210` |
| **Notification Sound** (2997) | Plays a sound with the in-app notification pop-up | `ui.notificationSound` | on | click | `:212-223`; `src/lib/components/NotificationToast.svelte:68-84` |
| **Notification Targets** (2998), **Add Notification Target** (2995) | Personal webhook targets for the notification events the server lists (chat finished or failed, channel message, calendar alert, failed file processing; the tab falls back to `Chat finished` and `Chat failed` if the list cannot be loaded), with `Send Test`, `Make Default`, `Edit`, `Remove` and an enable switch per target | the account's top-level `notifications` (managed by the notifications API) | none | each action saves | `:29-40`, `:88-95`, `:225-339`, `:344-439`; `backend/open_webui/utils/notifications.py:102-129`, `:223-231`; `backend/open_webui/events.py:669-675` |

This tab has no **Save** button; every control saves on its own. The in-app pop-up and the browser notification appear when a response finishes in a chat other than the one on screen, or while the tab is in the background (`src/routes/+layout.svelte:734-781`).

### 7.5 Keyboard (`shortcuts`)

**Purpose.** Lists every keyboard shortcut and lets the person rebind most of them. **Who sees it.** Everyone. **Component.** `src/lib/components/chat/Settings/Shortcuts.svelte`; the visible title is `Keyboard` (line 3036) although the tab id is `shortcuts`. The registry of shortcuts is `src/lib/shortcuts.ts`.

**Controls at the top.**

| Label (line) | What it does | Stored as | Default | Source |
|---|---|---|---|---|
| **Reset Defaults** (3031) | Puts every binding back to the built-in set and saves it | `keybindings` (top level of the account settings) | not applicable | `src/lib/components/chat/Settings/Shortcuts.svelte:73-76`, `:112-117` |
| **Enable Keyboard Shortcuts** (3019) | `When disabled, keyboard shortcuts will not trigger any actions.` (3018). Saves on click | `ui.keyboardShortcuts` | on | `:120-143`; `src/routes/(app)/+layout.svelte:251-254` |

**Rebinding.** The list has the columns **Command** (3013) and `Key` (`src/lib/components/chat/Settings/Shortcuts.svelte:146-153`). Click a configurable binding (tooltip `Click to rebind`), the badge reads `Press keys...`, then press the new combination; **Escape** cancels (`:86-101`, `:216-229`). An empty binding shows `Unassigned` and can be clicked to set one (`:230-236`). When two commands share a combination, an amber `!` appears with the tooltip `Also bound to {action}` (`:239-245`). Each rebinding saves immediately as `keybindings`, without a toast (`:63-71`). Bindings are loaded at sign-in on every device (`src/routes/(app)/+layout.svelte:73`; `src/lib/shortcuts.ts:114-126`).

**How combinations are written.** `Cmd` is the Command key on macOS and the Ctrl key elsewhere; on macOS the badge shows symbols such as `⌘⇧O`, elsewhere `Ctrl+Shift+O` (`src/lib/shortcuts.ts:132-194`).

**Every shortcut** (registry order; "configurable" means it can be rebound; a `*` beside a name marks a tooltip condition):

| Category | Command (line) | Default | Configurable | Condition shown as tooltip | Source (`src/lib/shortcuts.ts`) |
|---|---|---|---|---|---|
| Chat | **New Chat** (3025) | `Cmd+Shift+O` | yes | | `:86`, `:213-218` |
| Chat | **New Temporary Chat** (3026) | `Cmd+Shift+'` | yes | | `:87`, `:219-224` |
| Chat | **Delete Chat** (3016) | `Cmd+Shift+Backspace` | yes | | `:88`, `:225-230` |
| Chat | **Open Model Selector** (3027) | `Cmd+Shift+M` | yes | | `:89`, `:231-236` |
| Chat | **Toggle Dictation** (3038) | `Cmd+Shift+L` | yes | | `:90`, `:237-242` |
| Chat | **Navigate to Previous Chat** (3023) | unassigned | yes | | `:91`, `:243-248` |
| Chat | **Navigate to Next Chat** (3022) | unassigned | yes | | `:92`, `:249-254` |
| Global | **Search** (3032) | `Cmd+K` | yes | | `:93`, `:257-262` |
| Global | **Open Settings** (3028) | `Cmd+.` | yes | | `:94`, `:263-268` |
| Global | **Show Shortcuts** (3033) | `Cmd+/` | yes | | `:95`, `:269-274` |
| Global | **Toggle Sidebar** (3040) | `Cmd+Shift+S` | yes | | `:96`, `:275-280` |
| Global | **Toggle Controls** (3037) | unassigned | yes | | `:97`, `:281-286` |
| Global | **Close Modal** (3012) | `Escape` | yes | | `:98`, `:287-292` |
| Input | **Focus Chat Input** (3020) | `Shift+Escape` | yes | | `:99`, `:295-300` |
| Input | **Accept Autocomplete Generation / Jump to Prompt Variable** (3008) | `Tab` | no | | `:301-305` |
| Input | **Prevent File Creation** (3029) | `Cmd+Shift+V` | no | `Only active when "Paste Large Text as File" setting is toggled on.` | `:306-311` |
| Input | **Attach File From Knowledge** (3011) | `#` | no | | `:312-316` |
| Input | **Add Custom Prompt** (3009) | `/` | no | | `:317-321` |
| Input | **Talk to Model** (3035) | `@` | no | | `:322-326` |
| Message | **Generate Message Pair** (3021) | `Cmd+Shift+Enter` | yes | `Only active when the chat input is in focus.` | `:100`, `:329-335` |
| Message | **Regenerate Response** (3030) | `Cmd+R` | yes | (acts only while the chat input has focus, `src/routes/(app)/+layout.svelte:343-349`) | `:101`, `:336-341` |
| Message | **Allow Tool Call** (3010) | `Cmd+Alt+Enter` | yes | `Only active when a tool call is waiting for approval.` | `:102`, `:342-348` |
| Message | **Deny Tool Call** (3017) | `Cmd+Alt+Backspace` | yes | `Only active when a tool call is waiting for approval.` | `:103`, `:349-355` |
| Message | **Stop Generating** (3034) | `Escape` | no | `Only active when the chat input is in focus and an LLM is generating a response.` | `:356-361` |
| Message | **Edit Last Message** (3024) | `ArrowUp` | no | `Only can be triggered when the chat input is in focus.` | `:362-367` |
| Message | **Copy Last Response** (3015) | `Cmd+Shift+C` | yes | | `:105`, `:368-373` |
| Message | **Copy Last Code Block** (3014) | `Cmd+Shift+;` | yes | | `:104`, `:374-379` |
| Voice | **Toggle Mute** (3039) | `M` | no | `Only active during Voice Mode.` | `:382-387` |

What the configurable shortcuts do is wired in `src/routes/(app)/+layout.svelte:250-353` (most), `src/lib/components/chat/MessageInput.svelte:1333-1342` (Toggle Dictation) and the dialogue components (Close Modal, for example `src/lib/components/common/Modal.svelte:44-53`). **New Temporary Chat** toggles temporary mode and opens a new chat; for a non-admin whose permissions enforce temporary chats (`chat.temporary_enforced`) it always switches temporary mode on (`src/routes/(app)/+layout.svelte:309-320`).

Notes:

- **Escape** closes the top dialogue even when shortcuts are switched off or Close Modal is rebound, because dialogues also listen for the Escape key itself (`src/lib/components/common/Modal.svelte:44-53`). In the Settings window, the first Escape clears a search before a second closes the window (`src/lib/components/chat/SettingsModal.svelte:427-431`).
- **Regenerate Response** takes the key press only while the chat input has focus; otherwise the app leaves `Cmd+R` to the browser (`src/routes/(app)/+layout.svelte:343-349`). Which combinations a particular browser or operating system reserves for itself is outside the code and **TO BE CONFIRMED** case by case.

### 7.6 Connections (`connections`)

**Purpose.** Personal OpenAI-compatible model endpoints ("direct connections") whose models then appear in the person's model list. **Who sees it.** Everyone, but only when the site setting `direct.enable` is on (default off; section 3.1). **Component.** `src/lib/components/chat/Settings/Connections.svelte` and the row `src/lib/components/chat/Settings/Connections/Connection.svelte`. **Deep reference.** `model-connections-openai-ollama-and-direct.md`.

| Label (line) | What it does | Stored as | Saves | Source |
|---|---|---|---|---|
| **Direct Connections** (2799) section, **Add Connection** (2798) | `Connect to your own OpenAI compatible API endpoints.` (2797). The **+** button opens the connection dialogue; adding saves at once | `ui.directConnections` (three parallel lists of base URLs, keys and per-connection options) | on add | `src/lib/components/chat/Settings/Connections.svelte:21-27`, `:81-104` |
| Each connection row | The base URL (tooltip `WebUI will make requests to "{url}/chat/completions"`), a **Configure** cog and an enable switch. The switch and changes made in the Configure dialogue save at once; typing in the URL box and deleting a connection take effect only after **Save** | same | click or Save | `src/lib/components/chat/Settings/Connections/Connection.svelte:22-92`; `src/lib/components/chat/Settings/Connections.svelte:107-129` |
| **Save** | Removes trailing slashes, pads or trims the key list to match the URLs, saves and shows `Settings saved successfully!` | same | Save | `src/lib/components/chat/Settings/Connections.svelte:29-55`; `src/lib/components/chat/SettingsModal.svelte:811-817` |

Help text under the list: `Connections managed through the Admin Panel are recommended for everyday use. Direct connections provide convenient access to your own endpoints, but rely on your browser session to keep requests running, making them better suited to testing and temporary use.` and `CORS must be properly configured by the provider to allow requests from Open WebUI.` (`src/lib/components/chat/Settings/Connections.svelte:134-151`).

After every save from the window the model list is reloaded with these connections (`src/lib/components/chat/SettingsModal.svelte:450-458`). How the keys typed here are held and protected is security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca).

### 7.7 Integrations (`tools`)

**Purpose.** Personal external tool servers (OpenAPI) and personal Open Terminal connections. **Who sees it.** Admins, and users with `features.direct_tool_servers`, when the site setting `direct.integrations.enable` is on (both default off; section 3.1). **Components.** `src/lib/components/chat/Settings/Integrations.svelte`, its rows `src/lib/components/chat/Settings/Tools/Connection.svelte`, and the terminal block `src/lib/components/chat/Settings/Integrations/Terminals.svelte` with rows `src/lib/components/chat/Settings/Integrations/Terminals/Connection.svelte`. The visible title is `Integrations` (line 3048). **Deep reference.** `workspace-tools-tool-servers-mcp-and-terminals.md`.

| Label (line) | What it does | Stored as | Source |
|---|---|---|---|
| **External Tool Servers** (3044), **Add Connection** (3042) | `Connect to your own OpenAPI compatible external tool servers.` (3041). Rows show the server name or URL, an `OpenAPI` (3043) or MCP tooltip, a **Configure** cog and an enable switch. Empty list: `No tool server connections configured.` Link `Learn more about OpenAPI tool servers.` to the upstream project | `ui.toolServers` | `src/lib/components/chat/Settings/Integrations.svelte:109-160`; `src/lib/components/chat/Settings/Tools/Connection.svelte:36-94` |
| **Open Terminal** (3047), **Add Connection** (3046) | `Connect to Open Terminal instances to browse files and use them as always-on tools. Only one can be active at a time.` (3045). Switching one on switches the others off. Empty list: `No terminal connections configured.` Link `Learn more about Open Terminal` | `ui.terminalServers` | `src/lib/components/chat/Settings/Integrations/Terminals.svelte:32-104` |
| **Save** | Saves both lists, reconnects to each enabled server and shows `Settings saved successfully!`; a server that cannot be reached shows `Failed to connect to {URL} OpenAPI tool server` | both | `src/lib/components/chat/Settings/Integrations.svelte:43-86`; `src/lib/components/chat/SettingsModal.svelte:818-824` |

Adding, deleting or toggling a row saves at once through the same handler (`src/lib/components/chat/Settings/Integrations.svelte:38-41`, `:134-145`, `:163`). The server keeps `ui.toolServers` only for people with `features.direct_tool_servers` (section 3.3). The same help text as Connections appears at the bottom (`:166-184`). The composer's terminal menu also changes which terminal is enabled, in the browser copy of `terminalServers` (`src/lib/components/chat/MessageInput/TerminalMenu.svelte:70-110`).

### 7.8 Personalization (`personalization`)

**Purpose.** Switch memory on or off and manage saved memories. **Who sees it.** When the site setting `memories.enable` is on, admins and users with `features.memories` (both default on; section 3.1). **Components.** `src/lib/components/chat/Settings/Personalization.svelte` and `src/lib/components/chat/Settings/Personalization/MemoryModal.svelte`. Visible title `Personalization` (line 3007). **Deep reference.** `memories.md`.

| Label (line) | What it does | Stored as | Default | Source |
|---|---|---|---|---|
| **Memory** (3003), with an Experimental badge, in section `Memory` (3006) | The description reads `You can personalize your interactions with LLMs by adding memories through the 'Add Memory' button below, making them more helpful and tailored to you.`: the code takes line 3002 and replaces the word `Manage` (3001) with `Add Memory` (`:121-127`). Saves on click | `ui.memory` | the site's `memories.enable` value | `src/lib/components/chat/Settings/Personalization.svelte:99-102`, `:117-140` |
| **Saved Memories** (3005) | Shown while Memory is on: a count, `Search Memories`, an **Actions** menu with `Add Memory` and **Clear memory** (3000), and each memory with **Edit** and **Remove**. Empty list: `Memories accessible by LLMs will be shown here.` (3004); no search hits: `No results found` | the `memory` table | none | `:142-270` |

The tab's **Save** button saves nothing; it only shows `Settings saved successfully!` (`:105-110`; `src/lib/components/chat/SettingsModal.svelte:825-831`). The memory dialogue has a **Type** choice of `User` or `Context`, the text, and an optional **Path** (`src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:59-128`).

### 7.9 Audio (`audio`)

**Purpose.** Personal speech-to-text and text-to-speech choices. **Who sees it.** Everyone. **Component.** `src/lib/components/chat/Settings/Audio.svelte`, heading `Audio` (line 2796). **Deep reference.** `audio-speech-to-text-and-text-to-speech.md`.

| Label (line) | What it does | Stored as | Default | Saves | Source |
|---|---|---|---|---|---|
| **Speech-to-Text Engine** (2793) in `STT Settings` (2785) | `Choose the engine used to transcribe voice input.` (2792). `Default` (the admin's engine) or `Web API` (the browser's). Hidden when the admin's engine is already the browser's | `ui.audio.stt.engine` | `Default` | Save | `src/lib/components/chat/Settings/Audio.svelte:189-203` |
| **Language** (2784) | `Set a speech recognition language or leave it blank to detect automatically.` (2783); placeholder `e.g. en`; hidden with the engine row | `ui.audio.stt.language` | blank | Save | `:205-224` |
| **Instant Auto-Send After Voice Transcription** (2778) | `Send transcribed voice input immediately after speech recognition finishes.` (2777) | `ui.speechAutoSend` | off | click | `:226-241`, `:86-89` |
| **Text-to-Speech Engine** (2795) in `TTS Settings` (2786) | `Choose the engine used to read assistant responses aloud.` (2794). `Default` or `Kokoro.js (Browser)` | `ui.audio.tts.engine` | `Default` | Save | `:244-257` |
| **Kokoro.js Dtype** (2780) | Shown for Kokoro.js. `Select the local model precision used by Kokoro.js.` (2779); `fp32`, `fp16`, `q8`, `q4`. The model downloads into the browser; the panel shows `Loading Kokoro.js...` and `Please do not close the settings page while loading the model.` | `ui.audio.tts.engineConfig.dtype` | none | Save | `:259-276`, `:124-158`, `:331-347` |
| **Auto-Playback Response** (2774) | `Play assistant responses aloud automatically.` (2773) | `ui.responseAutoPlayback` | off | click | `:278-289`, `:81-84` |
| **Speech Playback Speed** (2791) | `Adjust how quickly spoken responses are played.` (2790); a number followed by `x` | `ui.audio.tts.playbackRate` | `1` | Save | `:291-306` |
| **Set Voice** (2776, 2782 or 2789) in `Voice` (2787) | One of three forms, depending on the engine: a Kokoro.js voice list (2781), the browser's voices with **Allow non-local voices** (2772, `Include voices that are not provided by a local speech service.`), or the admin service's voices (2788) | `ui.audio.tts.voice`; `ui.audio.tts.nonLocalVoices` | the admin's voice | Save | `:309-398` |

**Save** sends the whole `audio` object and shows `Settings saved successfully!` without waiting for the server (`:161-182`). It also records the admin's voice at that moment (`defaultVoice`); if the admin later changes the site voice, the person's saved voice is ignored and the new site voice is used until they choose again (`:103-107`, `:176`).

### 7.10 Data Controls (`data_controls`)

**Purpose.** Bulk actions on the person's own chats and files. Nothing on this tab is a stored preference. **Who sees it.** Everyone; three rows are hidden by permissions (section 3.2). **Component.** `src/lib/components/chat/Settings/DataControls.svelte` (heading `Data Controls`, line 2816). **Deep reference.** `chat-conversations-history-and-organisation.md` (and `files-uploads-and-storage.md` for files).

| Label (line) | Button | What it does | Shown when | Source |
|---|---|---|---|---|
| **Import Chats** (2809) in `Chats` (2812) | `Import` | `Import chat history from a JSON export file.` (2808). Reads a `.json` file (an OpenAI export is converted), sends it to `POST /api/v1/chats/import`, then shows `Successfully imported {res.length} chats.` | admin or `chat.import` | `:36-91`, `:163-178`; `src/lib/apis/chats/index.ts:171-174` |
| **Export Chats** (2807) | `Export` | `Download your chat history as a JSON export.` (2806). Downloads `chat-export-{timestamp}.json` from `GET /api/v1/chats/all` | admin or `chat.export` | `:93-98`, `:180-195` |
| **Shared Chats** (2815) | `Manage` | `Review and manage chats you have shared.` (2814); opens the shared-chats list | everyone | `:197-210` |
| **Archive All Chats** (2803) | **Archive All** (2801) | `Move every chat into the archive after confirmation.` (2802). Confirmation text `Are you sure you want to archive all chats? This action cannot be undone.`; archived chats can in fact be restored from Archived Chats with **Unarchive All** (7.12) | everyone | `:100-108`, `:124-132`, `:212-225` |
| **Delete All Chats** (2805) | `Delete All` | `Permanently delete every chat after confirmation.` (2804). Confirmation text `Are you sure you want to delete all chats? This action cannot be undone.` | admin or `chat.delete` | `:110-118`, `:134-142`, `:227-242` |
| **Manage Files** (2811) in `Files` (2813) | `Manage` | `Open the file manager for uploaded files.` (2810) | everyone | `:245-260` |

Archive and delete first return the person to the home page, then refresh the sidebar (`:100-118`). The Settings window does not offer the **Sync Usage Stats** dialogue from here (section 7.15).

### 7.11 Usage (`usage`)

**Purpose.** The person's own activity statistics. Nothing is stored by this tab. **Who sees it.** Everyone. **Component.** `src/lib/components/chat/Settings/Usage.svelte` (heading `Usage`, line 3054). **Deep reference.** `evaluations-feedback-and-analytics.md`.

- Data comes from `GET /api/v1/users/usage`, by default the last 730 days (`src/lib/components/chat/Settings/Usage.svelte:131-140`; `backend/open_webui/routers/users.py:706-720`).
- Sections: `Overview` (3052) with `Lifetime tokens`, `Peak tokens`, `Longest active chat`, `Current streak`, `Longest streak` and a `Token activity` chart that switches between `Daily`, `Weekly` and `Cumulative`; `Activity` (3049); `Activity insights` (3050); `Top models` (3053); `Most used tools` (3051) (`:289-485`).
- Footnote: `Token counts are estimates and may not reflect actual API usage` (`:487`). Errors show `Failed to load usage`; an empty history shows `No usage data found`, `No model usage found` (`:285`, `:413`, `:456`).

### 7.12 Archived Chats (`archived_chats`)

**Purpose.** List, search, open, restore, delete or export archived chats. **Who sees it.** Everyone. **Component.** `src/lib/components/chat/Settings/ArchivedChats.svelte` (heading `Archived Chats`, line 2769). **Deep reference.** `chat-conversations-history-and-organisation.md`.

- A search box and an **Actions** menu with **Unarchive All** (2770) and **Export** (2768) (`:204-265`). **Unarchive All** asks `Are you sure you want to unarchive all archived chats?` and then shows `All chats have been unarchived.` (`:150-160`, `:175-182`). Export downloads `archived-chat-export-{timestamp}.json` (`:112-118`).
- The list has `Title` and `Updated at` columns; each row has **Unarchive Chat** and **Delete Chat** buttons; an empty archive shows `You have no archived conversations.` (`:278-370`).
- Clicking a title closes the Settings window and opens the chat (`:315-326`).

### 7.13 Account (`account`)

**Purpose.** The person's profile, user variables, password and API keys. **Who sees it.** Everyone; the Password section only when the login form and the password-change form are enabled; the API keys section only where API keys are allowed (section 3.2). **Components.** `src/lib/components/chat/Settings/Account.svelte`, `src/lib/components/chat/Settings/Account/UserProfileImage.svelte`, `src/lib/components/chat/Settings/Account/UpdatePassword.svelte`. **Deep reference.** `authentication-and-sign-in.md`.

| Label (line) | What it does | Stored in | Source |
|---|---|---|---|
| Profile picture | **Upload Photo**, **Remove**, **Initials** or **Gravatar** | `user.profile_image_url` | `src/lib/components/chat/Settings/Account/UserProfileImage.svelte:120-247` |
| **Name** (2759) in `Profile` (2765) | `Set the display name shown across your account.` (2758) | `user.name` | `src/lib/components/chat/Settings/Account.svelte:263-276` |
| **Bio** (2746) | `Add optional profile context visible where profiles are shown.` (2745) | `user.bio` | `:277-288` |
| **Gender** (2755) | `Choose the gender value stored on your profile.` (2754); `Prefer not to say`, `Male`, `Female` or `Custom` with a free-text box | `user.gender` | `:290-326` |
| **Birth Date** (2748) | `Set the birth date saved with your profile.` (2747) | `user.date_of_birth` | `:327-338` |
| `User Variables` (plain key) | Key and value pairs usable in model system prompts; the help reads `Use these in model system prompts as {example}.` where the example is `{{user.variables.key_name}}` | `user.variables` | `:340-379`, `:596-657` |
| **Change Password** (2750) in `Password` (2764) | `Update the password used for email and password sign-in.` (2749); **Current Password**, **New Password**, **Confirm Password**, then **Update password** (2767). Success shows `Password updated. Please sign in again.` and signs the person out | the sign-in record | `src/lib/components/chat/Settings/Account.svelte:381-385`; `src/lib/components/chat/Settings/Account/UpdatePassword.svelte:18-48`, `:55-133` |
| **Secrets** (2762) in `API keys` (2763) | `Show or hide sensitive account secrets.` (2761); reveals **JWT Token** (admins only, 2757) and **API Key** (2744) with **Create new secret key** (2752) | see `authentication-and-sign-in.md` | `src/lib/components/chat/Settings/Account.svelte:387-570` |

**Save** sends the profile (`POST /api/v1/auths/update/profile`) and the user variables, refreshes the signed-in user and shows `Settings saved successfully!` only when both succeed (`src/lib/components/chat/Settings/Account.svelte:138-178`, `:238-247`; `src/lib/components/chat/SettingsModal.svelte:845-850`). Gender and birth date are personal information stored on the account; handle requests about them as personal data.

### 7.14 About (`about`)

**Purpose.** Shows the installed version, checks for a newer upstream release, opens the changelog, and carries the licence, copyright and credit lines. **Who sees it.** Everyone. **Component.** `src/lib/components/chat/Settings/About.svelte` (heading `About`, line 2742). Nothing on this tab is stored.

| Element (line) | What it shows | Shown when | Source |
|---|---|---|---|
| Section title `{WEBUI_NAME} Version` (2739) | For example `MedIT GPT Version`; the name is the server's `WEBUI_NAME` (default `MedIT GPT`) | always | `src/lib/components/chat/Settings/About.svelte:57-63`; `src/routes/+layout.svelte:1274`; `src/lib/constants.ts:7` |
| Version | `v0.11.4` (the version built into the front end); hovering shows the build hash, `dev-build` when none was set at build time | always | `src/lib/components/chat/Settings/About.svelte:66-69`; `src/lib/constants.ts:27-28`; `vite.config.ts:25-26` |
| Update status | `Checking for updates...`, then `(v{version.latest} available!)` linking to the upstream release page, or `(latest)`; `Could not check for updates` when the check failed | the version check is enabled | `:71-86` |
| **See what's new** (2741) | Opens the changelog window. Description `View the installed version and check release updates.` (2740) | always | `:64`, `:89-96` |
| **Check for updates** (2736) | Runs the check again | the version check is enabled | `:99-108`, `:25-38` |
| `Ollama Version` (2738) | The connected Ollama server's version | an Ollama version was returned | `:40-43`, `:112-118` |
| `Community` (2737) | With an enterprise licence: `{WEBUI_NAME} - {type} license purchased by {organization_name}` (the name part only when it does not contain "Open WebUI"). Without one: links to the upstream Discord, X and GitHub | always | `:120-152` |
| Emoji credit | `Emoji graphics provided by` Twemoji, `licensed under` CC-BY 4.0 | always | `:154-160` |
| Copyright line | `Copyright (c)` {current year} Open WebUI Inc. `All rights reserved.`, linking to the upstream site and LICENSE | always | `:162-172` |
| Credit line | `Created by` followed by the upstream project's creator, linking to their GitHub profile (the name is not reproduced in this knowledgebase, which records no personal names) | always | `:174-179` |

The Version title, the Community licence line and the Copyright line are each preceded by a comment reading "LICENSE covers this Open WebUI … Do not alter, remove, obscure, or replace it except as LICENSE permits" (`:57-59`, `:122-124`, `:163-165`). These lines are licence-protected and must stay as the code shows; the fork renamed the product but left them unchanged (section 12).

**How the update check works.** The tab calls `GET /api/version/updates` (`src/lib/apis/index.ts:1575-1600`), which needs a signed-in user (`backend/open_webui/main.py:2594-2613`).

- When the environment variable `ENABLE_VERSION_UPDATE_CHECK` is off (code default on; `OFFLINE_MODE=true` forces it off), the server answers with the installed version as the latest, and the browser hides the update text and button because `features.enable_version_update_check` is false (`backend/open_webui/env.py:1196-1205`; `backend/open_webui/main.py:2347`, `:2596-2598`).
- Otherwise the server asks GitHub for the latest **upstream Open WebUI** release, waiting at most one second, and returns `latest` without the leading `v`; any failure returns `latest: null`, which shows `Could not check for updates`, and writes the log line `Version update check failed: {e}` (`backend/open_webui/main.py:2599-2613`).
- "Available!" therefore means a newer upstream release exists, not that a newer MedIT GPT build is ready. How and when MedIT GPT adopts upstream releases is **TO BE CONFIRMED**.
- Admins also get a corner pop-up when a newer release exists, unless **Toast Notifications for New Updates** is off; closing it hides it in that browser for 24 hours (`src/routes/(app)/+layout.svelte:369-382`, `:428-438`).

**The changelog window.** **See what's new** opens the changelog built from the repository's `CHANGELOG.md` (the five most recent entries, `backend/open_webui/env.py:185-222`; `backend/open_webui/main.py:2616-2618`), which is the upstream changelog. Closing it records the version in the account (`ui.version`) and in the browser (`src/lib/components/ChangelogModal.svelte:41-46`). For admins it also opens by itself after sign-in when the recorded version differs from the running one, unless **Show "What's New" Modal on Login** is off (`src/routes/(app)/+layout.svelte:355-357`). See `notifications-webhooks-events-and-banners.md`.

### 7.15 SyncStatsModal (Sync Usage Stats Dialogue)

`src/lib/components/chat/Settings/SyncStatsModal.svelte` lives in the Settings folder but is not a tab and is not opened from the Settings window. The root layout opens it in two cases, both started by the Open WebUI Community website (origins `https://openwebui.com`, `https://www.openwebui.com`, and `http://localhost:9999`; `src/lib/constants.ts:19-23`):

- the app was opened by the community site with `?sync=true` and the site setting `ui.enable_community_sharing` is on (`src/routes/+layout.svelte:1352-1359`); or
- the community site sends the message `export:stats` (`src/routes/+layout.svelte:1067-1075`).

The dialogue, titled `Sync Usage Stats`, asks `Do you want to sync your usage stats with Open WebUI Community?` and lists `What is shared:` (`Open WebUI version`, `Model names and usage frequency`, `Message counts and response timestamps`, `Content lengths (character counts only)`, `User ratings (thumbs up/down)`) and `What is NOT shared:` (`Your message text or inputs`, `Model responses or outputs`, `Uploaded files or images`) (`src/lib/components/chat/Settings/SyncStatsModal.svelte:366-420`). Buttons: **Sync**, **Download as JSON**, **Cancel**; an option `Only sync new/updated chats` appears after an earlier sync (`:421-512`). Results: `Sync Complete!` with `Your usage stats have been successfully synced.`, or `Sync Failed` with the error or `There was an error syncing your stats. Please try again.` (`:326-364`).

The statistics come from the chat statistics export, which requires `ui.enable_community_sharing` (code default on) or an admin (see `chat-conversations-history-and-organisation.md`). Whether MedIT GPT users may send usage statistics to an external community site is a privacy question: **TO BE CONFIRMED** with the U of T Privacy Office (privacy.utoronto.ca) and the platform maintainer.

### 7.16 Shared Settings Components

| Component | Role | Source |
|---|---|---|
| `UserSettingSection` | A titled block (small grey `h3`) holding rows, with spacing between sections | `src/lib/components/chat/Settings/UserSettingSection.svelte:1-17` |
| `UserSettingRow` | A label on the left, a control on the right, and an optional description line beneath | `src/lib/components/chat/Settings/UserSettingRow.svelte:1-22` |
| `UserSettingField` | A label above a full-width control (text boxes, voice pickers) with an optional description | `src/lib/components/chat/Settings/UserSettingField.svelte:1-24` |
| `SettingsSelect` | The drop-down used for Theme, Language and the audio engines; its tooltip is the placeholder text | `src/lib/components/common/SettingsSelect.svelte:1-34` |
| `Switch` | The on/off switch used everywhere; tooltip `Enabled`/`Disabled`; shows the `Default` tag when told the value is inherited; thicker focus outline in Accessibility Mode | `src/lib/components/common/Switch.svelte:1-53` |
| `ShortcutItem` | Renders a shortcut name, its tooltip marker `*`, and the key badge using the keyboard layout where the browser supports it | `src/lib/components/chat/ShortcutItem.svelte:1-142` |
| `settings-access.ts` | Permission rules shared by the tabs and the search (section 3.2) | `src/lib/utils/settings-access.ts:1-69` |
| `settings-search.ts` | Builds and queries the search index (section 5.2) | `src/lib/utils/settings-search.ts:1-80` |

The Interface, General, Audio, Connections, Integrations, Personalization and Account tabs have a **Save** button at the bottom right; Notifications, Keyboard, Data Controls, Usage, Archived Chats and About do not.

### 7.17 Site Settings and Environment Variables That Shape This Window

Admin and environment settings decide which tabs and rows appear. Live values are data and **TO BE CONFIRMED** for production.

| Setting (persistent key or environment variable) | Effect here | Code default | Source |
|---|---|---|---|
| `ui.default_interface_settings` (seeded from `DEFAULT_INTERFACE_SETTINGS`) | Admin preset for Interface fields (section 5.6) | `{}` | `backend/open_webui/config.py:1712-1718`, `:3089` |
| `user.permissions` → `settings.interface` (`USER_PERMISSIONS_SETTINGS_INTERFACE`) | Interface tab and Interface saves | on | `backend/open_webui/config.py:1937`, `:2017-2018` |
| `user.permissions` → `chat.controls`, `chat.system_prompt`, `chat.params` | System Prompt and Advanced Parameters sections and saves | on | `backend/open_webui/config.py:1849`, `:1853`, `:1855` |
| `user.permissions` → `chat.import`, `chat.export`, `chat.delete`, `chat.temporary` | Data Controls rows; Temporary Chat by Default | on | `backend/open_webui/config.py:1861`, `:1885`, `:1887`, `:1897` |
| `user.permissions` → `features.memories`, `features.direct_tool_servers`, `features.api_keys`, `features.webhooks` | Personalization, Integrations, API keys, Notification Targets | on, off, off, off | `backend/open_webui/config.py:1904-1906`, `:1924-1926`, `:1932-1934` |
| `direct.enable` (`ENABLE_DIRECT_CONNECTIONS`) | Connections tab | off | `backend/open_webui/config.py:230`, `:2823` |
| `direct.integrations.enable` (`ENABLE_DIRECT_INTEGRATIONS`) | Integrations tab | off | `backend/open_webui/config.py:231`, `:2824` |
| `memories.enable` (`ENABLE_MEMORIES`) | Personalization tab and the Memory switch's default | on | `backend/open_webui/config.py:426`, `:2844` |
| `task.autocomplete.enable` (`ENABLE_AUTOCOMPLETE_GENERATION`) | Prompt Autocompletion row | off | `backend/open_webui/config.py:2333`, `:3149` |
| `ui.enable_user_webhooks` (`ENABLE_USER_WEBHOOKS`) | Notification Targets | off | `backend/open_webui/config.py:2100`, `:3125` |
| `ui.enable_community_sharing` (`ENABLE_COMMUNITY_SHARING`) | Sync Usage Stats dialogue | on | `backend/open_webui/config.py:2096`, `:3123` |
| `ui.enable_password_change_form`, `ui.enable_login_form` | Account Password section | see `authentication-and-sign-in.md` | `src/lib/components/chat/Settings/Account.svelte:381` |
| `ENABLE_VERSION_UPDATE_CHECK`, `OFFLINE_MODE` (environment only) | About update check and the admin update pop-up | on, off | `backend/open_webui/env.py:1200-1205` |
| `ENABLE_EASTER_EGGS` (environment only) | Her theme and Doge language | on | `backend/open_webui/env.py:966` |
| `DEFAULT_LOCALE` (environment) | Intended first language for a browser with no saved language; may be overridden by the browser's own language (section 7.2.2, step 2) | empty | `backend/open_webui/config.py:1672`; `backend/open_webui/main.py:2315` |
| `WEBUI_NAME` (environment only) | Name in the About version title | `MedIT GPT` | `backend/open_webui/env.py:951` |
| `features.enable_admin_analytics` | Admin Analytics tab in the admin half | on when absent | `src/lib/components/chat/SettingsModal.svelte:409-411` |

## 8. Cron Jobs and Background Processes

None found in code for this area. Searched the in-scope files and the backend for scheduled or periodic work that reads or writes personal settings; settings are read and written only when a request arrives. What happens and when:

| When | What happens | Source |
|---|---|---|
| Every page load of the signed-in app | The browser fetches the account settings (with the admin preset merged), applies UI scale, font and keyboard bindings, loads models, then connects to the person's enabled tool and terminal servers in the background | `src/routes/(app)/+layout.svelte:67-81`, `:213-248` |
| Every page load, admins only | One check for a newer upstream release, unless it was dismissed in this browser within the last 24 hours; the What's New window opens if the recorded version differs | `src/routes/(app)/+layout.svelte:355-382` |
| Opening the Settings window | The account's own settings are fetched again (`?raw=true`) to mark preset values; the English translations are loaded for the search | `src/lib/components/chat/SettingsModal.svelte:89-126`, `:371-377` |
| At save time | The server filters and patches the settings and publishes `user.settings_updated`, whose delivery to webhooks and event functions is scheduled as a background task in the same server process | `backend/open_webui/routers/users.py:482-562`; `backend/open_webui/events.py:1062-1171` |
| Reading notification targets | An old single webhook URL is converted into a target list and saved back the first time targets are read; see `notifications-webhooks-events-and-banners.md` | `backend/open_webui/utils/notifications.py:102-129` |
| Choosing Kokoro.js on the Audio tab | The speech model downloads into the browser, with progress shown; nothing runs on the server | `src/lib/components/chat/Settings/Audio.svelte:124-158` |

No Redis listener, startup loop or scheduler task reads or writes the `ui` settings (compare the loop list in the "Startup Order and Background Jobs" part of `CLAUDE.md`; the planned reference document `background-processes-and-scheduling.md` does not exist yet). The one background reader of the account settings is event-driven: when a notification event happens (a chat finishing or failing, a channel message, a calendar alert or a failed file processing), notification delivery reads the person's notification targets (`backend/open_webui/events.py:669-675`; `backend/open_webui/utils/notifications.py:97-129`, `:393`; see `notifications-webhooks-events-and-banners.md`). There is no crontab.

## 9. Notifications and Emails

The application sends no email (ground truth). For this area:

- **Event `user.settings_updated`** (description `A user settings object was updated.`, message `User settings updated`) is published on every successful save from the Settings window, with the person as actor and subject (`backend/open_webui/events.py:135-137`; `backend/open_webui/routers/users.py:550-556`). It reaches admin event webhooks that subscribe to it and event functions; it is not sent to browsers, and other open windows of the same person are not refreshed (section 5.7). Because most switches save on click, the event is frequent. Its webhook delivery is covered in `notifications-webhooks-events-and-banners.md` (section 9.2, Event Catalogue).
- **Browser notifications and the notification sound** are switched on and off on the Notifications tab (section 7.4); how they fire is in `notifications-webhooks-events-and-banners.md` section 5.8.
- **Personal notification targets** (webhooks) are managed on the Notifications tab; the test sends `Test notification sent.` on success (`src/lib/components/chat/Settings/Notifications.svelte:176-183`).
- **The admin update pop-up and the What's New window** are controlled by two admin-only Interface switches (section 7.3.1) and covered in `notifications-webhooks-events-and-banners.md` section 5.14.
- **In-app toasts** confirm saves (`Settings saved successfully!`) and report failures; they are listed in section 10.

## 10. Error, Warning and Notice Messages (Verbatim)

Toasts appear at the edge of the screen; "inline" messages appear inside the window. `{error}` means the window prints whatever error text the server or browser returned.

### 10.1 Saving and Loading Settings

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Settings saved successfully!` | Success toast | `src/lib/components/chat/SettingsModal.svelte:461`, `:796`, `:804`, `:815`, `:822`, `:829`, `:836`, `:848`; admin tabs `:860`, `:882`, `:888`, `:894`, `:900`, `:906`; `src/lib/components/chat/Settings/Notifications.svelte:159` | A tab's **Save** completed (on Interface, Audio and Personalization it is shown without waiting for the server; section 5.3) | None | If the person says the change did not stick, reload and look again; see 11.1 |
| `{error}` | Error toast | `src/lib/components/chat/SettingsModal.svelte:441-443` | The settings save request failed; the text is the server's `detail` | Try again; note the exact text | Match the text against this table and the backend catalogues |
| `We could not find what you're looking for :/` | Error toast (via the line above) | `USER_NOT_FOUND`, `backend/open_webui/constants.py:79`; raised by `backend/open_webui/routers/users.py:559-562`, `:666-670`, `:694-697` | The server could not find the signed-in account while saving settings, user variables or location | Sign out and back in | Escalate with the time and the account's email; an account deleted while signed in shows this |
| `Failed to load Interface settings` | Error toast; the app stays on a loading spinner | `src/routes/(app)/+layout.svelte:231-235` | Loading the account settings failed at page load | Reload the page; sign in again | Check whether other people are affected (server or database problem) before escalating |
| `Matching tabs: {count}` | Screen-reader status | `src/lib/components/chat/SettingsModal.svelte:546-552` | Typing in the settings search | None | Not an error |
| `No matches` | Inline notice | `src/lib/components/chat/SettingsModal.svelte:550`, `:781-785` | The search found no tab | Try another word or English; see 11.3 | Remember the tab may be hidden by permissions |
| `Failed to connect to {URL} OpenAPI tool server` | Error toast | `src/lib/components/chat/Settings/Integrations.svelte:51-55`; `src/routes/(app)/+layout.svelte:95-101` | A personal tool server on the Integrations tab could not be reached when saving or at page load | Check the server address, or switch the server off | See `workspace-tools-tool-servers-mcp-and-terminals.md` |
| `Failed to connect to {URL} terminal server` | Error toast | `src/routes/(app)/+layout.svelte:127-136` | An enabled personal terminal could not be reached at page load | Switch it off on the Integrations tab | As above |
| `Version update check failed: {e}` | Server log (warning), not shown to users | `backend/open_webui/main.py:2610-2612` | The About tab or admin load could not reach GitHub | None | Explains `Could not check for updates` |
| `Error loading DEFAULT_INTERFACE_SETTINGS: {e}` | Server log at start-up | `backend/open_webui/config.py:1712-1716` | The environment variable `DEFAULT_INTERFACE_SETTINGS` is not valid JSON; the preset seeds as empty | None | Matters only on first boot or with persistent config off; see 11.9 |

### 10.2 Interface Tab

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `User location successfully retrieved.` | Success toast | `src/lib/components/common/InterfaceSettings.svelte:179-182` | **Allow User Location** switched on and the browser returned a position | None | The approximate location is now stored on the account (personal data) |
| `{error.message}` (the browser's own location error) | Error toast | `src/lib/components/common/InterfaceSettings.svelte:174-177`; `src/lib/utils/index.ts:794-801` | The browser refused or could not get a location; the switch turns itself off | Allow location for the site in the browser, then try again | The wording comes from the browser |
| `Clipboard write permission denied. Please check your browser settings to grant the necessary access.` | Error toast | `src/lib/components/common/InterfaceSettings.svelte:205-223` | **Auto-Copy Response to Clipboard** switched on but the browser refused clipboard access; the switch turns itself off | Allow clipboard access for the site, then switch it on again | Browser permission, not an app fault |
| `Default action buttons will be used.` | Inline notice | `src/lib/components/chat/Settings/Interface/ManageFloatingActionButtonsModal.svelte:126` | Quick Actions dialogue set to `Default` | None | Not an error |

### 10.3 Notifications, Keyboard and General Tabs

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Response notifications cannot be activated as the website permissions have been denied. Please visit your browser settings to grant the necessary access.` | Error toast | `src/lib/components/chat/Settings/Notifications.svelte:60-73` | **Browser Notifications** switched on but the browser permission is denied or unsupported | Allow notifications for the site in the browser, then switch on again | Browser permission |
| `Test notification sent.` | Success toast | `src/lib/components/chat/Settings/Notifications.svelte:176-180` | **Send Test** on a notification target succeeded | Check the receiving service | See `notifications-webhooks-events-and-banners.md` |
| `No notification targets configured.` | Inline notice | `src/lib/components/chat/Settings/Notifications.svelte:243-246` | No personal targets yet | **Add Notification Target** if wanted | Not an error |
| `The notify tool always sends to an enabled target, regardless of automatic event settings.` | Inline notice | `src/lib/components/chat/Settings/Notifications.svelte:415-419` | Shown in the target dialogue | None | Not an error |
| `Press keys...` | Inline notice | `src/lib/components/chat/Settings/Shortcuts.svelte:216-221` | Waiting for a new key combination | Press the combination, or Escape to cancel | Not an error |
| `Also bound to {action}` | Tooltip on an amber `!` | `src/lib/components/chat/Settings/Shortcuts.svelte:239-245` | Two commands share a combination | Rebind one of them | Only one of the two will fire |
| `Couldn't find your language?` | Inline notice with a link | `src/lib/components/chat/Settings/General.svelte:264-278` | Interface in English (US) and no enterprise licence | None | Points to the upstream translation guide |

### 10.4 Personalization, Data Controls and Archived Chats

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Are you sure you want to clear all memories? This action cannot be undone.` (title `Clear Memory`) | Confirmation | `src/lib/components/chat/Settings/Personalization.svelte:284-292` | **Clear memory** chosen | Confirm or cancel | See `memories.md` |
| `Memory cleared successfully` | Success toast | `src/lib/components/chat/Settings/Personalization.svelte:71-82` | Memories cleared (shown only if there were some) | None | |
| `Are you sure you want to delete this memory? This action cannot be undone.` (title `Delete Memory?`) | Confirmation | `src/lib/components/chat/Settings/Personalization.svelte:294-323` | **Remove** on one memory | Confirm or cancel | |
| `Memory deleted successfully` | Success toast | `src/lib/components/chat/Settings/Personalization.svelte:305-308` | One memory deleted | None | |
| `Memory added successfully`, `Memory updated successfully` | Success toast | `src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:42-46` | Memory dialogue saved | None | |
| `Memories accessible by LLMs will be shown here.` | Inline notice | `src/lib/components/chat/Settings/Personalization.svelte:231-234`; `src/lib/i18n/locales/en-US/translation.json:3004` | No memories yet | None | Not an error |
| `Successfully imported {res.length} chats.` | Success toast (not translated) | `src/lib/components/chat/Settings/DataControls.svelte:86-88` | **Import Chats** finished | Check the sidebar | See `chat-conversations-history-and-organisation.md` |
| `Are you sure you want to archive all chats? This action cannot be undone.` | Confirmation | `src/lib/components/chat/Settings/DataControls.svelte:124-132` | **Archive All** | Confirm or cancel | Archiving can be reversed from Archived Chats despite the wording |
| `Are you sure you want to delete all chats? This action cannot be undone.` | Confirmation | `src/lib/components/chat/Settings/DataControls.svelte:134-142` | **Delete All** | Confirm only if sure | Deleted chats cannot be restored from the app |
| `Are you sure you want to unarchive all archived chats?` | Confirmation | `src/lib/components/chat/Settings/ArchivedChats.svelte:175-182` | **Unarchive All** | Confirm or cancel | |
| `All chats have been unarchived.` | Success toast | `src/lib/components/chat/Settings/ArchivedChats.svelte:150-160` | Unarchive All finished | None | |
| `This action cannot be undone. Do you wish to continue?` (title `Confirm your action`) | Confirmation | `src/lib/components/chat/Settings/ArchivedChats.svelte:168-173`; defaults in `src/lib/components/common/ConfirmDialog.svelte:143`, `:153` | **Delete Chat** on an archived chat | Confirm only if sure | |
| `You have no archived conversations.` | Inline notice | `src/lib/components/chat/Settings/ArchivedChats.svelte:278-281` | Archive is empty | None | Not an error |

### 10.5 Account, Audio, Integrations and Usage

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Variable keys must use lowercase snake case.` | Error toast | `src/lib/components/chat/Settings/Account.svelte:94-97`, `:125-128` | A user variable key is not like `key_name` | Rename the key | |
| `Variable keys must be unique.` | Error toast | `src/lib/components/chat/Settings/Account.svelte:98-101`, `:129-131` | Two user variables share a key | Rename one | |
| `API Key created.` | Success toast | `src/lib/components/chat/Settings/Account.svelte:180-187` | A new API key was made | Copy it | See `authentication-and-sign-in.md` |
| `Failed to create API Key.` | Error toast | `src/lib/components/chat/Settings/Account.svelte:180-187` | Creating the key failed | Try again | Check API keys are allowed (section 3.2) |
| `This will revoke the current API key.` (title `Delete API Key?`) | Confirmation | `src/lib/components/chat/Settings/Account.svelte:584-591` | Deleting the API key | Confirm or cancel | |
| `API Key deleted.` | Success toast | `src/lib/components/chat/Settings/Account.svelte:190-199` | Key deleted | None | |
| `Password updated. Please sign in again.` | Success toast; the person is signed out | `src/lib/components/chat/Settings/Account/UpdatePassword.svelte:25-36` | **Update password** succeeded | Sign in with the new password | |
| `The passwords you entered don't quite match. Please double-check and try again.` | Error toast | `src/lib/components/chat/Settings/Account/UpdatePassword.svelte:41-46` | New and confirmation passwords differ | Retype both | |
| `Fingerprint spoofing detected: Unable to use initials as avatar. Defaulting to default profile image.` | Information toast (10 seconds) | `src/lib/components/chat/Settings/Account/UserProfileImage.svelte:146-158`, `:220-232` | **Initials** chosen in a browser that blocks canvas drawing (privacy protection) | Upload a photo instead | Browser privacy setting, not an app fault |
| `No user variables configured.` | Inline notice | `src/lib/components/chat/Settings/Account.svelte:367-370` | No user variables | None | |
| `Loading Kokoro.js...` | Inline notice with progress | `src/lib/components/chat/Settings/Audio.svelte:331-343` | The Kokoro.js voice model is downloading into the browser | Wait | |
| `Please do not close the settings page while loading the model.` | Inline warning | `src/lib/components/chat/Settings/Audio.svelte:344-346` | Same | Keep the window open | |
| `{e}` (voice list error) | Error toast | `src/lib/components/chat/Settings/Audio.svelte:69-71` | Loading the site's text-to-speech voices failed | Try later | See `audio-speech-to-text-and-text-to-speech.md` |
| `No tool server connections configured.` | Inline notice | `src/lib/components/chat/Settings/Integrations.svelte:147-151` | No personal tool servers | None | |
| `No terminal connections configured.` | Inline notice | `src/lib/components/chat/Settings/Integrations/Terminals.svelte:93-97` | No personal terminals | None | |
| `Failed to load usage` | Inline error | `src/lib/components/chat/Settings/Usage.svelte:131-140`, `:283-286` | The usage request failed | Reopen the tab later | Escalate if it persists for everyone |
| `No usage data found` | Inline notice | `src/lib/components/chat/Settings/Usage.svelte:411-414` | No activity in the period | None | |
| `Token counts are estimates and may not reflect actual API usage` | Inline notice | `src/lib/components/chat/Settings/Usage.svelte:487` | Always on the Usage tab | None | Usage figures are estimates |

### 10.6 About Tab and Sync Usage Stats

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Checking for updates...` | Inline notice | `src/lib/components/chat/Settings/About.svelte:79-80` | The check is running | Wait | |
| `(v{version.latest} available!)` | Inline notice | `src/lib/components/chat/Settings/About.svelte:81-82` | A newer **upstream** Open WebUI release exists | None for users | It does not mean a MedIT GPT update is ready (section 7.14) |
| `(latest)` | Inline notice | `src/lib/components/chat/Settings/About.svelte:83` | The installed version matches the newest upstream release | None | |
| `Could not check for updates` | Inline notice | `src/lib/components/chat/Settings/About.svelte:72-73` | The server could not reach GitHub (or the browser could not reach the server) | None | Expected where the server has no internet access; log line in 10.1 |
| `Your usage stats have been successfully synced.` (title `Sync Complete!`) | Inline success | `src/lib/components/chat/Settings/SyncStatsModal.svelte:326-344` | Sync Usage Stats finished | None | See 7.15 for the privacy question |
| `There was an error syncing your stats. Please try again.` (title `Sync Failed`) | Inline error | `src/lib/components/chat/Settings/SyncStatsModal.svelte:346-364` | The sync failed without a specific message | Try again | |
| `An unexpected error occurred` | Inline error (in Sync Failed) | `src/lib/components/chat/Settings/SyncStatsModal.svelte:202-204` | The sync failed without detail | Try again | |
| `Download failed. Please try again.` | Inline error and error toast | `src/lib/components/chat/Settings/SyncStatsModal.svelte:304-311` | **Download as JSON** failed | Try again | |
| `Failed to connect to the server. Please check your connection.` | Inline error | `src/lib/components/chat/Settings/SyncStatsModal.svelte:239-245` | The statistics download could not start | Check the connection | |
| `Failed to start download. The server may be unavailable.` | Inline error | `src/lib/components/chat/Settings/SyncStatsModal.svelte:248-250` | Same, with no response | Try later | |
| `Failed to export chat stats`, `Failed to fetch stats data` | Inline error | `src/lib/components/chat/Settings/SyncStatsModal.svelte:173-179` | A page of statistics could not be fetched | Try again | The export needs community sharing on (7.15) |

### 10.7 Related Messages Outside the Window

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Default model updated` | Success toast | `src/lib/components/chat/ModelSelector.svelte:26-36` | **Set as default** in the model selector | None | Shown even when the server discarded the change for lack of `settings.interface` (11.1) |
| `Choose a model before saving...` | Error toast | `src/lib/components/chat/ModelSelector.svelte:27-31` | Set as default with an empty model slot | Choose a model first | |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it never changes a person's settings, roles, permissions or the admin preset. Most answers are guidance the person can follow in their own Settings window. Support contacts and escalation routes for MedIT GPT are **TO BE CONFIRMED** (ground truth). In escalations, identify the account by email (for example `jane.doe@example.com`), never paste chat content, and never ask for passwords, API keys or tokens.

### 11.1 "My settings didn't save"

**Symptom.** A change is back to its old value after a reload or on the next visit.

**Likely causes, in order.**
1. The setting is browser-only (Theme or Language) and the person is now in another browser, profile or device, or cleared site data (sections 6.3, 7.2).
2. The person lacks a permission and the server silently discarded the change: any Interface field without `settings.interface`, the system prompt or parameters without `chat.controls` plus `chat.system_prompt` or `chat.params`, tool servers without `features.direct_tool_servers` (section 3.3). The success toast still appears, and the change looks applied until reload. This includes the model selector's **Set as default** (`Default model updated`).
3. The value needs the tab's **Save** button and the person closed the window first (General's System Prompt and Advanced Parameters, Audio engines and voice, Connections URL edits and deletions; section 5.3).
4. A save failed; on Interface and Audio a failure can show `Settings saved successfully!` together with an error toast (section 5.3).
5. Another open window (another device or tab) saved an older copy of the same key afterwards (section 5.4).
6. On the Interface tab, the person's own default model was replaced by the admin's first default model when they pressed **Save** (section 5.3).

**Diagnostic steps.** Ask which tab and setting, and whether they saw any error toast (copy its exact text). Ask whether they use more than one browser or device. Ask them to reload the page, reopen Settings and read the value again. For Interface switches, ask whether a grey `Default` tag sits beside the switch (the value is the admin preset). Ask whether the Interface tab is visible at all; if it is not, cause 2 applies to every Interface field.

**Resolution.** For causes 1 and 3, explain where the value is kept and when to press **Save**. For cause 5, ask the person to reload other open windows before changing settings again. For causes 2, 4 and 6, escalate.

**Escalation.** Send the account email, the tab and setting, the time of the attempt, the exact toast text, the browser, and whether the Interface tab is visible. The platform maintainer can check the person's permissions and the server logs.

### 11.2 "My settings are different on my other computer"

**Symptom.** The app looks different on two devices for the same account.

**Likely causes, in order.**
1. Theme and Language are kept per browser (sections 6.3, 7.2.2).
2. The other device has a window open from before the change; open windows are not refreshed (section 5.7).
3. The other browser follows a different language because no language was ever chosen there, so it was detected from that browser's own preferences (section 7.2.2).
4. Different accounts are signed in on the two devices.

**Diagnostic steps.** Ask which settings differ. Ask the person to reload the page on the device that looks wrong. Ask them to compare the name shown on the Account tab on both devices.

**Resolution.** Explain that Theme and Language must be chosen once in each browser; everything else follows the account after a reload. A link ending in `?lang=<code>` (for example `?lang=fr-CA`) sets the language in that browser (`src/lib/i18n/index.ts:90-103`).

**Escalation.** Only if account-level settings (for example Interface switches) still differ after a reload on both devices: send the account email and the settings that differ.

### 11.3 "I can't find the Interface tab"

**Symptom.** The Settings window has no Interface tab (or no Connections, Integrations or Personalization tab, or a setting someone described is missing).

**Likely causes, in order.**
1. Interface: the person's groups and the default permissions do not grant `settings.interface` (section 3.1). Admins always see it.
2. Connections: **Direct Connections** (`direct.enable`) is off for the site; this hides the tab for admins too.
3. Integrations: the site setting `direct.integrations.enable` is off, or the person lacks `features.direct_tool_servers` (both off by default). The tab is called **Integrations**, not "Tools".
4. Personalization: memory is off for the site, or the person lacks `features.memories`.
5. A single setting: it is hidden by its own rule (section 3.2), or it appears only when another switch is set (for example **Display the Username Instead of You in the Chat** only while **Chat Bubble UI** is off).
6. The person is looking for "Shortcuts": the tab is titled **Keyboard**.

**Diagnostic steps.** Ask the person to list the tabs they see. Ask them to type the setting's name into the Settings search; if no tab matches, the setting is hidden for them or uses words the search does not index (section 5.2).

**Resolution.** Explain that the tab is controlled by the site's administrators. Tier 1 does not change permissions.

**Escalation.** Send the account email, the missing tab or setting and the tab list the person sees. Whether the person should have the permission is a decision for the platform owner (**TO BE CONFIRMED** who decides).

### 11.4 "The language didn't change"

**Symptom.** The interface stays in English (or another language) after choosing a language, or returns to a different language on the next visit.

**Likely causes, in order.**
1. The language was changed in a different browser or device; Language is per browser (section 7.2.2).
2. The browser's site data was cleared, so the language was detected again from the browser's preferences or the site default.
3. A link with `?lang=` set a different language.
4. Most of the screen changed but Settings labels, especially **Inline Citations** and **Hide Processing Details**, stayed in English: settings labels without a translation fall back to English by design (section 7.2.2, step 5).
5. Working tree only: a language detected from the browser is now mapped to the nearest bundled translation, so a regional browser language may be shown as its main language (section 12.2).

**Diagnostic steps.** Ask the person to open Settings, General, and read the **Language** value. Ask whether they use several browsers, and whether they followed a link containing `lang=`.

**Resolution.** Ask the person to choose the language again on the General tab in the browser they use; it applies at once. Explain that missing translations of individual settings labels are expected.

**Escalation.** Only if the chosen language does not apply at all in a browser that keeps site data: send the browser, the language chosen and a screenshot.

### 11.5 "Processing details are hidden and I want them back"

**Symptom.** Responses show only `Thinking...` while generating; no status lines, reasoning, tool cards or code analysis appear, on new and old chats.

**Likely causes, in order.**
1. **Hide Processing Details** is on for this person (MedIT GPT switch, default off).
2. The admin preset switches it on for everyone; the switch then shows the grey `Default` tag.
3. The model's `status_updates` capability is off, which hides the status line whatever the switch says (`src/lib/components/chat/Messages/ResponseMessage.svelte:198-199`).

**Diagnostic steps.** Ask the person to open Settings, Interface, Chat section, and read **Hide Processing Details**, and whether `Default` shows beside it.

**Resolution.** The person switches **Hide Processing Details** off; it saves at once and the details return on every chat. If the Interface tab is missing, they cannot change it themselves (11.3). Details: `chat-composer-and-message-display.md` section 5.22.

**Escalation.** If the switch is off and details are still hidden, send the account email, the model name and the time of a response, so the model's capabilities can be checked.

### 11.6 "The [1] source numbers disappeared from answers"

**Symptom.** Answers no longer show numbered citation chips, but the **Sources** list is still under the answer.

**Likely causes, in order.**
1. **Inline Citations** is off for this person (MedIT GPT switch, default on).
2. The admin preset switches it off (grey `Default` tag).
3. The model's `citations` capability is off; markers are then removed whatever the switch says (`src/lib/components/chat/Messages/ContentRenderer.svelte:128-130`).

**Diagnostic steps.** Ask the person to read **Inline Citations** in Settings, Interface, Chat section.

**Resolution.** The person switches **Inline Citations** on; answers already on screen update immediately. Details: `chat-composer-and-message-display.md` section 5.23.

**Escalation.** If it is on and the chips are still missing for one model only, send the model name.

### 11.7 "My theme keeps changing back"

**Symptom.** Dark or light mode is not kept.

**Likely causes, in order.** The theme is per browser (`theme` in local storage); a different browser, a private window or cleared site data starts again at **System**, which follows the computer's own light or dark setting (`src/app.html:50-58`).

**Diagnostic steps.** Ask which browser and whether it clears site data on exit or uses private windows.

**Resolution.** Choose the theme on the General tab in each browser used.

**Escalation.** Not normally needed.

### 11.8 "A setting changed by itself" or "A switch says Default"

**Symptom.** A switch shows a grey `Default` tag, or several people report the same new behaviour at once.

**Likely causes, in order.**
1. An admin changed the **Default Interface Settings** preset; everyone who never set that switch follows it from their next page load (section 5.6).
2. The person changed the setting on another device.

**Diagnostic steps.** Ask whether the `Default` tag is shown and whether colleagues see the same.

**Resolution.** The person can set the switch themselves; their choice then wins over the preset for that switch. There is no way to go back to "follow the preset" for a switch once it has been set, short of a change to the stored settings (section 5.5).

**Escalation.** If many people are affected, send the setting name and when it changed, so the platform maintainer can confirm a preset change.

### 11.9 "I set an interface default for everyone but people don't see it" (admins)

**Symptom.** An admin changed **Default Interface Settings**, but some people still see the old behaviour.

**Likely causes, in order.**
1. Those people chose their own value earlier; personal values win.
2. Their page has not been reloaded since the change.
3. The admin General tab's **Save** was not pressed after configuring the preset (section 5.6).
4. The value was set only in the environment variable `DEFAULT_INTERFACE_SETTINGS` after first boot; the stored setting wins over the environment (ground truth).

**Diagnostic steps.** Ask an affected person whether the switch shows `Default`. Ask them to reload.

**Resolution.** Explain causes 1 and 2. Tier 1 does not edit the preset.

**Escalation.** Send the setting, the expected value and an affected account email to the platform maintainer.

### 11.10 "Keyboard shortcuts don't work"

**Symptom.** A shortcut does nothing.

**Likely causes, in order.**
1. **Enable Keyboard Shortcuts** is off on the Keyboard tab (Escape still closes windows).
2. The shortcut was rebound, unassigned (for example **Navigate to Previous Chat** has no default) or clashes with another command (amber `!`).
3. The shortcut needs a condition (tooltip `*`), for example the chat input must have focus.
4. The browser or operating system reserves the combination for itself; which ones it reserves is outside the code (section 7.5).

**Diagnostic steps.** Ask the person to open Settings, Keyboard, read **Enable Keyboard Shortcuts** and the binding shown for the command.

**Resolution.** Switch shortcuts on, or click the binding and press a new combination, or use **Reset Defaults**.

**Escalation.** Not normally needed; include the browser and operating system if it persists.

### 11.11 "About says a new version is available"

**Symptom.** Settings, About shows `(v{version.latest} available!)`, or an admin sees an update pop-up.

**Likely causes, in order.** The check compares the installed version with the newest **upstream** Open WebUI release; MedIT GPT is a customized build that adopts upstream releases on its own schedule (section 7.14).

**Diagnostic steps.** None needed.

**Resolution.** Tell the person no action is needed on their side. The upgrade schedule is **TO BE CONFIRMED**.

**Escalation.** Optional: pass the version shown to the platform maintainer.

### 11.12 "The page is stuck loading and said Failed to load Interface settings"

**Symptom.** After sign-in the main area shows a spinner and the toast `Failed to load Interface settings` appeared.

**Likely causes, in order.** The request for the account settings failed (`src/routes/(app)/+layout.svelte:222-235`), for example because the server or its database is unavailable or the connection dropped; the code does not say which.

**Diagnostic steps.** Ask the person to reload; ask whether colleagues are affected; ask them to sign out and in again.

**Resolution.** If a reload or a fresh sign-in fixes it, no further action.

**Escalation.** If it persists or affects several people, escalate as a possible outage with the time, the number of people affected and the toast text.

### 11.13 "Browser notifications, auto-copy or location keep switching themselves off"

**Symptom.** **Browser Notifications**, **Auto-Copy Response to Clipboard** or **Allow User Location** flips back to off, with an error toast.

**Likely causes, in order.** The browser refused the permission the switch needs (notifications, clipboard, location) (sections 10.2, 10.3).

**Diagnostic steps.** Ask for the exact toast text and the browser.

**Resolution.** Guide the person to allow the permission for the site in the browser's site settings, then switch it on again. Allowing location stores an approximate location on the account; the person may prefer to leave it off.

**Escalation.** Not normally needed.

### 11.14 "I can't see the System Prompt or Advanced Parameters"

**Symptom.** The General tab shows only Theme and Language.

**Likely causes, in order.** The person lacks `chat.controls`, or `chat.system_prompt` (System Prompt) or `chat.params` (parameters) (section 3.2). Some parameters are admin-only by design (section 7.2.4).

**Diagnostic steps.** Ask which sections are visible on General.

**Resolution.** Explain that these sections are controlled by permissions.

**Escalation.** If the person believes they should have access, send the account email and the missing section.

### 11.15 "I archived all my chats. Are they gone?"

**Symptom.** The person used **Archive All** after the warning `This action cannot be undone.` and now sees an empty sidebar.

**Likely causes, in order.** The chats are archived, not deleted; the warning text overstates it (section 7.10).

**Diagnostic steps.** Ask whether they chose **Archive All** or **Delete All**.

**Resolution.** For Archive All: Settings, Archived Chats, **Actions**, **Unarchive All**, or restore chats one by one. For Delete All, the app has no way to restore them: the chats and their messages are removed from the database (`backend/open_webui/routers/chats.py:705-726`; `backend/open_webui/models/chats.py:2500-2515`).

**Escalation.** For Delete All, any recovery question goes to the platform maintainer; whether backups allow recovery is **TO BE CONFIRMED**.

## 12. Local Customisations

Compared with upstream Open WebUI v0.11.4 (`main`), the Settings window, its tabs, the search and access helpers, the shortcuts registry and the user settings endpoints are unchanged except for the items below. Checked with read-only `git diff main...uoft` and `git diff` on every file in scope.

### 12.1 Committed on the `uoft` Branch

| File | Change | Lines now |
|---|---|---|
| `backend/open_webui/models/users.py` | Adds `showInlineCitations` and `hideProcessingDetails` to the `InterfaceSettings` model, so the server treats them as Interface fields (governed by `settings.interface`, section 3.3) | `:99-100` |
| `src/lib/components/common/InterfaceSettings.svelte` | Adds the two switches to the Chat section, after **Always Expand Details**, with defaults on and off and the usual `Default` tag for admin presets (50 added lines) | `:79-80`, `:357-358`, `:1335-1379` |
| `src/lib/stores/index.ts` | Adds both keys to the `Settings` type | `:232-233` |
| `src/lib/i18n/locales/en-US/translation.json` | Adds the four English texts: `Hide Processing Details`, `Inline Citations`, and their descriptions | `:2923-2924`, `:2935-2936` |
| the 63 other locale files | Add the same four keys as empty strings (four added lines in each), so other languages fall back to English (section 7.2.2) | not cited (other locales are out of scope) |
| `src/lib/constants.ts` | `APP_NAME` is `MedIT GPT` instead of `Open WebUI`; it is the name shown in the About version title until the server's name arrives | `:7` |
| `backend/open_webui/env.py` | `WEBUI_NAME` defaults to `MedIT GPT` and no longer gains the " (Open WebUI)" suffix; this is the server name the About tab shows | `:951` |

The committed description of **Hide Processing Details** read: "Show "Thinking..." instead of status updates, tool calls, and reasoning while a response is generated, and keep them hidden afterwards. Tool approval requests and tool outputs such as images still appear." This text comes from `git diff main...uoft` and no longer exists in the working tree, which has the reworded version (section 12.2).

The licence comments and the copyright and credit lines on the About tab, and the licence-protected link text on the General tab, are unchanged by the fork (section 7.14).

### 12.2 Uncommitted Changes in the Working Tree (Not Yet on Any Branch)

| File | Change | Effect on this area |
|---|---|---|
| `src/lib/i18n/locales/en-US/translation.json` | Rewords the **Hide Processing Details** description to the text quoted in section 7.3.7 (adds "code analysis" and "images or embeds from tools") | The visible description differs between the committed build and the working tree (`:2923`) |
| `src/lib/i18n/index.ts` | Adds `toBundleCode`, which maps a detected browser language to a bundled translation (exact match, then the main language, then the first bundle of the same language); adds `en-US` after the site default as the final fallback; loads the language list once at start-up | Changes which language a browser without a saved choice gets, and what shows when a translation is missing (`:9`, `:75-86`, `:93`, `:105`, `:124`) |
| Message rendering files (`src/lib/components/chat/Chat.svelte`, `Messages/ResponseMessage.svelte`, `Messages/Markdown/HTMLToken.svelte`, `Messages/Markdown/MarkdownTokens.svelte`, `Messages/ResponseMessage/StatusHistory/StatusItem.svelte`, `Messages/StructuredOutputRenderer.svelte`, `Messages/structuredOutput.ts`, `src/lib/components/common/ToolCallDisplay.svelte`) | Refine what **Hide Processing Details** hides and when `Thinking...` shows | Covered in `chat-composer-and-message-display.md` section 12 |

Which of these the production build contains is **TO BE CONFIRMED** (section 14).

## 13. Source File Index

"Full" means read end to end; "parts" means read in the sections relevant here after a full scan for messages and controls.

### 13.1 In Scope

| File | Role | Read |
|---|---|---|
| `src/lib/components/chat/SettingsModal.svelte` | The Settings window: tab list, groups, availability rules, search box, save handler, admin half | Full |
| `src/lib/components/common/InterfaceSettings.svelte` | The Interface panel, shared with the admin preset editor; fork switches | Full |
| `src/lib/components/chat/Settings/Interface.svelte` | Interface tab wrapper and Save button | Full |
| `src/lib/components/chat/Settings/Interface/ManageFloatingActionButtonsModal.svelte` | Quick Actions dialogue | Parts |
| `src/lib/components/chat/Settings/Interface/ManageImageCompressionModal.svelte` | Image compression size dialogue | Parts |
| `src/lib/components/chat/Settings/General.svelte` | General tab: theme, language, system prompt, parameters | Full |
| `src/lib/components/chat/Settings/Advanced/AdvancedParams.svelte` | Parameter list used by General (and by model editors) | Parts (every row and admin gate) |
| `src/lib/components/chat/Settings/Notifications.svelte` | Notifications tab | Full |
| `src/lib/components/chat/Settings/Shortcuts.svelte` | Keyboard tab and rebinding | Full |
| `src/lib/components/chat/Settings/Connections.svelte`, `Connections/Connection.svelte` | Connections tab and rows | Full |
| `src/lib/components/chat/Settings/Integrations.svelte`, `Integrations/Terminals.svelte` | Integrations tab and terminal block | Full |
| `src/lib/components/chat/Settings/Integrations/Terminals/Connection.svelte`, `Tools/Connection.svelte` | Terminal and tool server rows | Parts |
| `src/lib/components/chat/Settings/Personalization.svelte` | Personalization tab | Full |
| `src/lib/components/chat/Settings/Personalization/MemoryModal.svelte` | Add and edit memory dialogue | Parts |
| `src/lib/components/chat/Settings/Audio.svelte` | Audio tab | Full |
| `src/lib/components/chat/Settings/DataControls.svelte` | Data Controls tab | Full |
| `src/lib/components/chat/Settings/Usage.svelte` | Usage tab | Parts |
| `src/lib/components/chat/Settings/ArchivedChats.svelte` | Archived Chats tab | Parts |
| `src/lib/components/chat/Settings/Account.svelte` | Account tab | Parts |
| `src/lib/components/chat/Settings/Account/UpdatePassword.svelte`, `Account/UserProfileImage.svelte` | Password change; profile picture | Parts |
| `src/lib/components/chat/Settings/About.svelte` | About tab | Full |
| `src/lib/components/chat/Settings/SyncStatsModal.svelte` | Sync Usage Stats dialogue | Parts (consent text, flow and every message) |
| `src/lib/components/chat/Settings/UserSettingField.svelte`, `UserSettingRow.svelte`, `UserSettingSection.svelte` | Shared layout pieces | Full |
| `src/lib/utils/settings-search.ts` | Search index and matching | Full |
| `src/lib/utils/settings-access.ts` | Permission rules for tabs and search | Full |
| `src/lib/shortcuts.ts` | Shortcut registry, default bindings, chord format | Full |
| `src/lib/stores/index.ts` | `settings` store and its type; `showSettings`; config type | Full |
| `backend/open_webui/routers/users.py` | `GET /user/settings`, `POST /user/settings/update`, info, variables, usage endpoints | Parts (lines 1-82, 455-720) |
| `backend/open_webui/models/users.py` | `InterfaceSettings`, `UserSettings`, `user` table, settings patch helper | Parts (lines 1-330, 815-870) |

### 13.2 Related Files Read for Evidence

| File | Used for |
|---|---|
| `src/routes/(app)/+layout.svelte` | Loading settings at sign-in, deep links, global shortcuts, update check, failure toast |
| `src/routes/+layout.svelte` | Language start-up, notification sound, Sync Usage Stats triggers, server name |
| `src/routes/s/[id]/+page.svelte`, `src/routes/(app)/admin/settings/+page.svelte`, `src/routes/(app)/admin/+layout.svelte` | Legacy local settings; admin deep links |
| `src/app.html` | Theme bootstrap |
| `src/lib/apis/users/index.ts`, `src/lib/apis/auths/index.ts`, `src/lib/apis/index.ts`, `src/lib/apis/ollama/index.ts`, `src/lib/apis/chats/index.ts` | API calls made by the tabs |
| `src/lib/i18n/index.ts`, `src/lib/i18n/settings-translations.ts`, `src/lib/i18n/locales/languages.json`, `src/lib/i18n/locales/en-US/translation.json` | Language detection and dotted-key fallback; labels |
| `src/lib/components/common/Switch.svelte`, `src/lib/components/common/SettingsSelect.svelte`, `src/lib/components/chat/ShortcutItem.svelte`, `src/lib/components/common/Modal.svelte`, `src/lib/components/common/ConfirmDialog.svelte` | Shared controls |
| `src/lib/components/admin/Settings/General.svelte`, `backend/open_webui/routers/auths.py` | Admin interface preset |
| `src/lib/components/layout/Sidebar/UserMenu.svelte`, `src/lib/components/layout/Sidebar.svelte`, `src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte`, `src/lib/components/chat/MessageInput/CommandSuggestionList.svelte`, `src/lib/components/chat/MessageInput/TerminalMenu.svelte` | Ways to open Settings |
| `src/lib/components/chat/Chat.svelte`, `src/lib/components/chat/MessageInput.svelte`, `src/lib/components/channel/MessageInput.svelte`, `src/lib/components/chat/ModelSelector.svelte`, `src/lib/components/chat/Messages/ContentRenderer.svelte`, `src/lib/components/chat/Messages/ResponseMessage.svelte`, `src/lib/components/common/ToolCallDisplay.svelte`, `src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte`, `src/lib/components/chat/Artifacts.svelte`, `src/lib/components/ChangelogModal.svelte`, `src/lib/components/NotificationToast.svelte`, `src/lib/components/common/EmojiPicker.svelte` | How settings take effect; other writers of `ui` |
| `src/lib/utils/index.ts`, `src/lib/utils/text-scale.ts`, `src/lib/constants.ts`, `vite.config.ts` | Location, language matching, text scale, version and name |
| `backend/open_webui/config.py`, `backend/open_webui/env.py`, `backend/open_webui/main.py`, `backend/open_webui/constants.py`, `backend/open_webui/events.py`, `backend/open_webui/utils/notifications.py`, `backend/open_webui/models/tools.py`, `backend/open_webui/models/functions.py` | Defaults, permissions, `/api/config`, update check, events, other writers of `user.settings` |

## 14. Open Questions

### 14.1 Live Values (Data, Not Code)

1. **The admin interface preset** `ui.default_interface_settings` in production, in particular whether it presets **Hide Processing Details**, **Inline Citations**, **Enable Message Queue**, **Enter Key Behavior** or `splitLargeChunks`. TO BE CONFIRMED (sections 5.6, 6.2).
2. **Permissions** in production: the default and group grants of `settings.interface`, `chat.controls`, `chat.system_prompt`, `chat.params`, `chat.import`, `chat.export`, `chat.delete`, `chat.temporary`, `features.memories`, `features.direct_tool_servers`, `features.api_keys` and `features.webhooks`. TO BE CONFIRMED (sections 3, 7.17).
3. **Site switches** in production: `direct.enable`, `direct.integrations.enable`, `memories.enable`, `task.autocomplete.enable`, `ui.enable_user_webhooks`, `ui.enable_community_sharing`, `auth.enable_api_keys`, `ui.enable_password_change_form`, and whether admin analytics is on. TO BE CONFIRMED (section 7.17).
4. **Environment variables** in production: `ENABLE_VERSION_UPDATE_CHECK`, `OFFLINE_MODE`, `ENABLE_EASTER_EGGS` (the Her theme and Doge language appear when it is on, the code default), `DEFAULT_LOCALE` and `WEBUI_NAME`. TO BE CONFIRMED (sections 7.2, 7.14).
5. Whether anything in production sets the control-less keys `splitLargeChunks` or `notificationSoundAlways` (section 6.2). TO BE CONFIRMED.

### 14.2 Build and Release

6. **Which build is live**: the committed `uoft` branch or a build that includes the uncommitted working-tree changes (the reworded Hide Processing Details description; the language-matching change in `src/lib/i18n/index.ts`; the message-rendering changes). TO BE CONFIRMED (section 12.2).
7. **How and when MedIT GPT adopts upstream releases**, so support can answer "About says a new version is available". TO BE CONFIRMED (sections 7.14, 11.11).
8. Whether the maintainer intends to translate the two MedIT GPT switches into other languages; today they fall back to English (sections 7.2.2, 12.1).

### 14.3 Support Process and Policy

9. **Who may look up a person's stored settings** (`user.settings` in the database) when diagnosing a ticket, and through what process. No screen shows another person's settings, so today support can only ask the person to read their own Settings window. TO BE CONFIRMED.
10. **Resetting a person's settings**: there is no user or admin control to reset all settings (section 5.5). Whether an admin may do it by other means, and who approves it, is TO BE CONFIRMED.
11. **Sync Usage Stats**: whether MedIT GPT users may send usage statistics to the external Open WebUI Community site (section 7.15). Privacy question for the U of T Privacy Office (privacy.utoronto.ca) and the platform maintainer. TO BE CONFIRMED.
12. Whether users should be pointed at the upstream links on the About tab (Discord, X, GitHub) and the "Help us translate Open WebUI!" link on General; the ground truth already marks upstream community links TO BE CONFIRMED.
13. Handling of personal data held as settings or profile fields: the approximate location saved by **Allow User Location**, gender, birth date, bio and user variables (sections 6.1, 7.13). Retention and who may see them are TO BE CONFIRMED.
14. Who decides whether a person should be granted a permission that unhides a tab (for example `settings.interface`). TO BE CONFIRMED (section 11.3).

### 14.4 Behaviour Found in Code That May Not Be Intended

These are what the code does today; whether each is intended is TO BE CONFIRMED with the platform maintainer.

15. Saves refused for lack of permission succeed silently, so the success toast appears and the change is lost on reload; this includes the model selector's `Default model updated` for people without `settings.interface` (sections 3.3, 11.1).
16. On the Interface and Audio tabs the success toast is shown before the server answers (section 5.3).
17. Pressing **Save** on the Interface tab re-saves the default model as the admin's first default model when one is set, replacing the person's own default (section 5.3).
18. **iframe Sandbox Allow Forms** shows on by default but embeds returned by tools treat a never-saved value as off; **Compress Images in Channels** shows on by default but the channel composer treats a never-saved value as off (sections 7.3.4, 7.3.6).
19. The **Archive All Chats** confirmation says `This action cannot be undone.`, although archived chats can be unarchived (section 7.10).
20. The **UI Scale** description says "local", but the value is saved to the account and applies on every device (section 7.3.1).
21. The user menu's **Keyboard** item is unreachable because no caller turns on the menu's help block (section 2.1).
22. The persistent key `ui.default_locale` is seeded but `/api/config` sends the environment value `DEFAULT_LOCALE`, so the stored key has no effect (section 7.2.2). This refines, and does not contradict, the ground-truth rule that the stored value wins: here nothing reads the stored value.
23. Saving a person's own tool or function valves rewrites the whole `user.settings` object from a copy read moments earlier, so a settings change saved at the same instant could be lost (section 6.1). Low impact; TO BE CONFIRMED whether it has been seen.
24. **Does the site default language ever apply?** The language library saves the browser's detected language during start-up, before the root layout checks for a saved language, so `DEFAULT_LOCALE` appears to apply only when no language can be detected (section 7.2.2, step 2). This comes from reading the installed library rather than running the app; TO BE CONFIRMED by a test in a fresh browser profile with `DEFAULT_LOCALE` set.

### 14.5 Security-Sensitive Questions (Referred, Not Documented)

For each item: Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca).

25. How the keys typed into personal direct connections and personal tool or terminal servers are held and protected (sections 7.6, 7.7).
26. The security implications of the iframe sandbox and same-origin switches in the Interface tab's Artifacts and Chat sections, and of their defaults (section 7.3.4).
27. The Account tab's JWT token and API key handling (section 7.13; see also `authentication-and-sign-in.md`).

### 14.6 Notes on the Brief and Other Documents

28. The brief for this area lists notifications under General; in v0.11.4 notifications have their own tab (section 7.4). No contradiction with `ground-truth.md`, `inventory.md` or `CLAUDE.md` was found; the fork fields are at `backend/open_webui/models/users.py:99-100` as recorded.
29. The tab inventory's `SyncStatsModal` is a dialogue, not a tab (section 7.15), and the `Advanced` and `Tools` sub-folders hold components used by General and Integrations (sections 7.2.4, 7.7).
30. The upstream creator named in the About tab's `Created by` line is not reproduced, under the knowledgebase's no-names rule (section 7.14).
