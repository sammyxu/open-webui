# Chat History, Folders, Tags, Sharing and Archive

## At a Glance

- **What this covers.** Everything a person does with conversations *after* they exist: the
  sidebar chat list, search, renaming, pinning, read and unread markers, archiving, deleting,
  temporary chats, share links, folders (including shared folders and the `/folders/<id>` page),
  tags, import, export and cloning. Typing and reading messages is in
  `chat-composer-and-message-display.md`; what the server does with a message, and how titles and
  tags are generated, is in `chat-completion-pipeline-and-generation-tasks.md`.
- **Where chats live.** One row per conversation in the `chat` table, with the whole conversation
  tree stored as JSON in its `chat` column; every message is also mirrored as a row in
  `chat_message`. Share links are snapshot rows in `shared_chat`; tags are `tag` rows plus a list
  in the chat's `meta`; folders are `folder` rows (`backend/open_webui/models/chats.py:129-179`;
  `backend/open_webui/models/chat_messages.py:127-172`; `backend/open_webui/models/shared_chats.py:18-29`;
  `backend/open_webui/models/tags.py:18-31`; `backend/open_webui/models/folders.py:22-33`).
- **Chat ids.** A saved chat has a random UUID and lives at `/c/<id>`. Ids starting `temporary:`
  (legacy `local:`) are temporary chats and ids starting `channel:` belong to channels; the server
  treats both as "not saved" (`backend/open_webui/utils/chat_id.py:4-16`).
- **Archive hides, delete destroys.** Archiving is reversible and keeps everything. Deleting is a
  hard delete of the chat row and its `chat_message` rows, with no trash and no restore
  (`backend/open_webui/models/chats.py:2476-2498`); no scheduled clean-up of chats was found
  either (section 8). A deleted chat can come back only from a database backup (backups are TO BE
  CONFIRMED).
- **Archiving one chat takes it out of its folder** for good: unarchiving returns it to the main
  list, not to the folder (`backend/open_webui/models/chats.py:1389-1400`).
- **A share link is a frozen snapshot.** Later messages are not shared until the owner presses
  **Update and Copy Link** (`backend/open_webui/models/shared_chats.py:61-112`).
- **A new share link is private to its owner.** Nobody else (admins aside, section 3.4) can open it
  until the owner adds people or groups, or picks **Public** or **Open**, in the share dialog's
  access panel, even though
  the dialog says `Users with the URL will be able to view the shared chat.`
  (`src/lib/components/chat/ShareChatModal.svelte:151-171`; `backend/open_webui/routers/chats.py:113-126`).
  Public and Open sharing of chats are **off** by default (`sharing.public_chats`,
  `sharing.open_chats`; `backend/open_webui/config.py:1877-1883`).
- **Search** looks at chat titles and message text, and understands `tag:`, `folder:`,
  `pinned:`, `shared:` and `archived:` filters; `tag:none` finds untagged chats
  (`backend/open_webui/models/chats.py:1963-2151`).
- **Folders need two switches**: the admin **Folders** feature (`folders.enable`, on by default)
  and the per-user `features.folders` permission (on by default). When either is off, the Folders
  section disappears **and chats inside folders drop out of the sidebar list** (they are still
  found by search) (`backend/open_webui/routers/folders.py:66-83`;
  `src/lib/components/layout/Sidebar.svelte:1363`; `backend/open_webui/models/chats.py:1561-1562`).
- **Sharing a folder shares every chat in it.** Anyone with read access to a folder can open all
  chats inside it, read-only (`backend/open_webui/models/chats.py:1779-1784`).
- **Export and import** are JSON (export also plain text and PDF per chat). The `chat.export` and
  `chat.import` permissions hide the menus; import also accepts ChatGPT exports
  (`src/lib/components/chat/Settings/DataControls.svelte:36-98`; `src/lib/utils/index.ts:784-792`).
- **Fork status:** this area matches upstream Open WebUI v0.11.4; nothing in scope differs on the
  `uoft` branch or in the working tree (section 12).
- **Tier 1 is read-only:** diagnose and escalate; never change chats, folders, shares, settings or
  permissions on a user's behalf.

## 1. Purpose and Who Uses It

Every conversation a person has with MedIT GPT is kept, unless it was a temporary chat. This area
is how people find those conversations again, keep them tidy, hand them to colleagues and get rid
of them. Support meets it in questions such as "where did my chat go?", "who can see my shared
chat?" and "can I get a deleted chat back?".

Who uses it, as coded:

| Who | What they do here | Evidence |
|---|---|---|
| Every signed-in `user` or `admin` | Browse, search, rename, pin, archive, delete, tag, export, import, clone and share their **own** chats; create and manage their own folders | Chat endpoints other than the share page require a signed-in `user` or `admin` (for example `backend/open_webui/routers/chats.py:248-259`, `:1568-1585`); folder endpoints add the folder checks (`backend/open_webui/routers/folders.py:66-83`) |
| `pending` accounts | Nothing: they see the Account Activation Pending screen; the share page also refuses them | `backend/open_webui/routers/chats.py:113-115`; ground truth (Accounts and Access) |
| People a chat or folder is shared with | Open a share link (`/s/<id>`) or a shared folder's chats, read-only; clone a shared chat into their own history if allowed | `src/routes/s/[id]/+page.svelte:46-48`, `:206-240`; `backend/open_webui/routers/folders.py:562-625` |
| Anyone holding an **Open** link | View the snapshot; the access panel describes Open as `Anyone with the link can view` | `src/lib/components/workspace/common/AccessControl.svelte:547`; `backend/open_webui/routers/chats.py:104-110`, `:1214-1219` |
| Admins | Everything above, plus: list and open other users' chats when admin chat access is on, delete any chat, change any shared chat's access, export every user's chats, set the global switches and permissions | `backend/open_webui/routers/chats.py:736-766`, `:1049-1053`, `:1577-1606`, `:2037-2040`; `src/lib/components/admin/Settings/General.svelte:274-312` |

What this area does **not** cover (see the named documents):

- Writing, editing, regenerating and deleting individual messages, the top bar and the composer:
  `chat-composer-and-message-display.md`.
- Title and tag generation, forking a chat at a message, and how a folder's system prompt and
  knowledge are applied to replies: `chat-completion-pipeline-and-generation-tasks.md`.
- Access grants in general, group permissions and the admin "view a user's chats" screen:
  `users-groups-roles-and-permissions.md`.
- Table definitions beyond this area and migrations: `database-schema-identity-chats-and-config.md`.
- Channels and direct messages (their sidebar items live in the same sidebar):
  `channels-and-direct-messages.md`.

## 2. Navigation and URLs

The production host name is TO BE CONFIRMED; addresses below are relative to the site root.

### 2.1 Pages and Places in the Interface

| Place | How to get there | What it shows | Source |
|---|---|---|---|
| Sidebar | Left of every app page; **Open Sidebar** / **Close Sidebar** button; its landmark is named `Chat history` | **New Chat**, **Search**, pinned menu items, then sections **Models** (pinned models), **Notes** (pinned notes), **Channels**, **Folders** and **Chats** | `src/lib/components/layout/Sidebar.svelte:1118-1124`, `:1211-1701` |
| Chats section | Bottom of the sidebar | A **Pinned** group, then chats grouped by last update (`Today`, `Yesterday`, `Previous 7 days`, `Previous 30 days`, month names, years); 60 more load as you scroll | `src/lib/components/layout/Sidebar.svelte:1416-1701`; `src/lib/utils/index.ts:1308-1337`; `backend/open_webui/routers/chats.py:261-263` |
| Folders section | Sidebar, when folders are allowed | Your folders (A to Z), then a `Shared` heading with folders others shared with you | `src/lib/components/layout/Sidebar.svelte:1363-1414`; `src/lib/components/layout/Sidebar/Folders.svelte:19-94` |
| A chat | `/c/<chat id>` | The conversation; the top bar's `...` **Chat actions** menu holds share, download, copy, move, archive, delete and tags | `src/lib/components/chat/Navbar.svelte:146`; `src/lib/components/layout/Navbar/Menu.svelte:280-510` |
| Search | Sidebar **Search**, or the Search shortcut (default Cmd/Ctrl+K) | Search box, actions `Start a new conversation` and `Create a new note`, results with a preview pane | `src/lib/components/layout/SearchModal.svelte:254-264`, `:525-541`, `:572-919`; `src/lib/shortcuts.ts:257-262` |
| A folder page | Click a folder name in the sidebar: `/folders/<folder id>` | Folder title and menu, the composer (unless the folder is shared with you read-only) and a paged list of the folder's chats | `src/routes/(app)/folders/[folderId]/+page.svelte:14-52`; `src/lib/components/chat/Placeholder.svelte:108-112`, `:128-145`, `:242`, `:285-288` |
| A shared chat | `/s/<share id>` | Read-only snapshot with title and date, and **Clone Chat** for signed-in people allowed to import | `src/routes/s/[id]/+page.svelte:179-243` |
| Archived Chats | User menu › **Settings** › **Archived Chats** (in the "Data" group) | Archived chats with search, sort, **Unarchive All**, **Export** | `src/lib/components/chat/SettingsModal.svelte:151-153`, `:248-250`, `:843-844`; `src/lib/components/chat/Settings/ArchivedChats.svelte:184-392` |
| Data Controls | User menu › **Settings** › **Data Controls** | **Import Chats**, **Export Chats**, **Shared Chats** (Manage), **Archive All Chats**, **Delete All Chats**, **Manage Files** | `src/lib/components/chat/SettingsModal.svelte:236-238`, `:839-840`; `src/lib/components/chat/Settings/DataControls.svelte:144-262` |
| Shared Chats list | Data Controls › **Shared Chats** › **Manage** | Your share links: copy, unshare, **Unshare All Shared Chats** | `src/lib/components/layout/SharedChatsModal.svelte:139-174` |
| Admin switches | Admin Panel › Settings › **General** › **Features** (`/admin/settings/general`) | **Community Sharing**, **Folders**, **Folder Max File Count** | `src/lib/components/admin/Settings/General.svelte:274-312` |
| Admin export | Admin Panel › Settings › **Database** › **Export** › **All Chats** | Downloads every user's chats as one JSON file | `src/lib/components/admin/Settings/Database.svelte:23-28`, `:124-149` |
| Admin view of a user's chats | Admin Panel › Users › the **Chats** button on a non-admin's row (shown only when admin chat access is on) | `{{user}}'s Chats` list; each title opens `/s/<chat id>` | `src/lib/components/admin/Users/UserList.svelte:405-412`; `src/lib/components/admin/Users/UserList/UserChatsModal.svelte:107-124`; details in `users-groups-roles-and-permissions.md` |

### 2.2 Chats API (`/api/v1/chats`)

Mounted at `/api/v1/chats` (`backend/open_webui/main.py:861`). Every route needs a signed-in
`user` or `admin` unless noted. "Owner" means the route only finds chats whose `user_id` is the
caller.

| Method and path | Who | What it does | Source |
|---|---|---|---|
| `GET /` and `GET /list` | Owner | Sidebar list: unarchived chats not in a folder and not pinned (unless asked); 60 per page when a page number is sent, which the sidebar does | `backend/open_webui/routers/chats.py:248-287`; `src/lib/stores/chatList.ts:39-44` |
| `POST /read` | Owner | Mark every chat read; returns folder unread counts | `:290-298` |
| `GET /pinned` | Owner | Pinned, unarchived chats | `:962-967` |
| `GET /search?text=` | Owner | Search titles and message text with filters (section 5.3); 60 per page | `:865-904` |
| `POST /tags` | Owner | Chats carrying one tag; deletes the tag row when none are found | `:1250-1263` |
| `GET /all` | Owner | Every chat as a stream (used by **Export Chats**) | `:974-1013` |
| `GET /all/archived` | Owner | Every archived chat (used by archived **Export**) | `:1021-1026` |
| `GET /all/tags` | Owner | All of the caller's tag rows | `:1034-1041` |
| `GET /all/db` | Admin, and only when `ENABLE_ADMIN_EXPORT` is on | Every chat of every user | `:1049-1053` |
| `GET /archived`, `GET /archived/count` | Owner | Archived list (title search, sort, 60 per page) and count | `:1061-1105` |
| `POST /archive/all`, `POST /unarchive/all` | Owner | Archive or unarchive every chat | `:1113-1135` |
| `GET /shared` | Owner | The caller's share links (title search, sort, 60 per page) | `:1171-1200` |
| `DELETE /share/all` | Owner | Remove every share link the caller made | `:1143-1168` |
| `GET /share/{share id}` | See section 3.5 | Read a share snapshot | `:1208-1233` |
| `POST /new` | Any | Create a chat (optionally in a folder the caller can write to) | `:774-799` |
| `POST /import` | `chat.import` or admin | Create chats from an import file | `:807-828` |
| `GET /{id}` | Owner, or see section 3.5 | Read a chat | `:1325-1347` |
| `POST /{id}` | Owner | Save changes to the chat JSON (title, messages, tags list) | `:1355-1396` |
| `DELETE /{id}` | Owner with `chat.delete`, or any admin | Permanently delete a chat (section 5.10) | `:1568-1616` |
| `GET /{id}/pinned`, `POST /{id}/pin` | Owner | Read or toggle the pin | `:1624-1656` |
| `POST /{id}/archive` | Owner | Toggle archive | `:1909-1939` |
| `POST /{id}/clone` | Owner with `chat.import`, or admin | Copy a chat | `:1775-1826` |
| `POST /{id}/clone/shared` | `chat.import` or admin, plus read access to the share | Copy a share snapshot into your chats | `:1834-1901` |
| `POST /{id}/fork` | Owner with `chat.import`, or admin | Copy one branch up to a message (pipeline document) | `:1672-1772` |
| `POST /{id}/share`, `DELETE /{id}/share` | Owner (`chat.share` needed to create) | Create or refresh, or remove, the share snapshot | `:1945-2017` |
| `GET /shared/{id}/access`, `POST /shared/{id}/access/update` | Owner, or any admin | Read or replace who may open the share (`{id}` is the chat id) | `:2029-2092` |
| `POST /{id}/unread` | Owner | Mark a chat unread | `:2104-2123` |
| `POST /{id}/folder` | Owner, with write access to the target folder | Move a chat into a folder, or out of all folders | `:2126-2153` |
| `GET /folder/{folder id}` | Owner | The caller's chats in a folder and its sub-folders (used by folder **Export**) | `:912-924` |
| `GET /folder/{folder id}/list` | Owner | The caller's chats in one folder, 10 per page | `:927-954` |
| `GET /{id}/tags`, `POST /{id}/tags`, `DELETE /{id}/tags` | Read: owner or see 3.5; change: owner | Read, add or remove a chat's tags | `:2161-2248` |
| `POST /{id}/messages/{message id}`, `DELETE /{id}/messages/{message id}` | Owner or admin | Edit one message's text, or delete one message (composer document) | `:1406-1504` |
| `POST /{id}/compact` | Owner | Context compaction (pipeline document) | `:1271-1317` |
| `GET /stats/usage`, `GET /stats/export`, `GET /stats/export/{chat id}` | Owner; the export routes also need `ui.enable_community_sharing` or admin | Per-chat statistics without message text, used by the community **Sync Usage Stats** dialog | `:307-704` |
| `GET /config`, `POST /config` | Admin | Context compaction and tool permission settings (pipeline document) | `:836-857` |
| `GET /list/user/{user id}` | Admin, and only when `ENABLE_ADMIN_CHAT_ACCESS` is on | A user's chats including archived | `:736-766` |
| `DELETE /` | `chat.delete` for role `user`; admins always | Delete all of the caller's chats | `:707-728` |

### 2.3 Folders API (`/api/v1/folders`)

Mounted at `/api/v1/folders` (`backend/open_webui/main.py:873`). Every route first runs the
folders check: the admin **Folders** switch must be on (for admins too) and a non-admin needs
`features.folders`; otherwise HTTP 403 (`backend/open_webui/routers/folders.py:66-83`).

| Method and path | Who | What it does | Source |
|---|---|---|---|
| `GET /` | Owner | Your folders with unread counts; repairs folders whose parent is missing or looped, and drops knowledge files you can no longer read | `backend/open_webui/routers/folders.py:91-139` |
| `POST /` | Owner; in someone else's folder, write access | Create a folder or sub-folder | `:147-231` |
| `GET /shared` | Any | Folders others shared with you, and their sub-folders | `:239-282` |
| `GET /{id}` | Owner, read access, or admin | One folder with its access list and whether you can write | `:295-322` |
| `POST /{id}/update` | Owner, write access, or admin | Rename, or change settings, icon or background | `:330-390` |
| `POST /{id}/update/parent` | Owner | Move a folder under another folder or to the top level | `:402-452` |
| `POST /{id}/update/expanded` | Owner (others: no change) | Remember whether the folder is open in the sidebar | `:464-496` |
| `POST /{id}/access/update` | Owner, write access, or admin | Replace the folder's access list | `:508-554` |
| `GET /{id}/shared/chats` | Owner, read access, or admin | The folder's chats from **all** users, 10 per page, flagged read-only when not yours | `:562-625` |
| `POST /{id}/read` | Owner, read access, or admin | Mark the folder's chats read | `:628-663` |
| `DELETE /{id}?delete_contents=` | Owner or admin | Delete the folder and its sub-folders, with or without the owner's chats (section 5.21) | `:671-752` |

### 2.4 Related Endpoints Outside These Routers

| Endpoint | Relevance | Source |
|---|---|---|
| `POST /api/chat/completions` | Creates the saved chat on the first message of a new conversation and refuses a new chat in a folder you cannot write to | `backend/open_webui/main.py:1213`, `:1299-1300`, `:1352-1400`; pipeline document |
| `POST /api/v1/tasks/title/completions` | The **Generate** title button | `chat-completion-pipeline-and-generation-tasks.md` |
| Socket event `events:chat` with type `last_read_at` | Marks a chat read when it is opened | `src/lib/components/chat/Chat.svelte:1146-1151`; `backend/open_webui/socket/main.py:601-640` |

## 3. Roles and Permissions

### 3.1 Who Can Do What

Roles are `admin`, `user` and `pending` (ground truth). Admins skip the permission checks below
at each call site; a `user` needs the permission from the defaults or from any of their groups
(ground truth: permissions only add up).

| Action | `user` | `admin` | Source |
|---|---|---|---|
| See, search, rename, pin, archive, tag own chats | Yes | Yes | `backend/open_webui/routers/chats.py:1355-1396`, `:1640-1656`, `:1909-1939`, `:2181-2248` |
| Delete a chat, delete all chats | With `chat.delete` | Yes, and any user's chat by id | `backend/open_webui/routers/chats.py:707-728`, `:1577-1606` |
| Create a share link | With `chat.share` | Yes | `backend/open_webui/routers/chats.py:1952-1953` |
| Make a share **Public** (all signed-in users) | With `sharing.public_chats` | Yes | `backend/open_webui/routers/chats.py:2047-2055`; `backend/open_webui/utils/access_control/__init__.py:256-274` |
| Make a share **Open** (anyone with the link) | With `sharing.open_chats` | Yes | `backend/open_webui/utils/access_control/__init__.py:239-251` |
| Add named people or groups to a share or folder | With `access_grants.allow_users` / `access_grants.allow_groups` | Yes | `backend/open_webui/utils/access_control/__init__.py:276-299` |
| Change who can open **another user's** share | No | Yes | `backend/open_webui/routers/chats.py:2037-2045` |
| Import, clone, clone a shared chat, fork | With `chat.import` | Yes | `backend/open_webui/routers/chats.py:231-238`, `:814`, `:1680`, `:1783`, `:1841` |
| Export | Menus shown with `chat.export` | Yes | `src/lib/components/layout/Sidebar/ChatMenu.svelte:324`; `src/lib/components/layout/Navbar/Menu.svelte:382`; `src/lib/components/chat/Settings/DataControls.svelte:180` |
| Start temporary chats | With `chat.temporary` | Yes | `src/lib/components/chat/Navbar.svelte:180` |
| Forced into temporary chats | When `chat.temporary_enforced` is on | No | `src/lib/components/layout/Sidebar.svelte:818-822`; `src/lib/components/chat/Chat.svelte:2025-2027` |
| Use folders | With `features.folders`, and only while **Folders** is on | Only while **Folders** is on | `backend/open_webui/routers/folders.py:66-83` |
| Share a folder | Panel offers it with `sharing.folders` | Yes | `src/lib/components/layout/Sidebar/Folders/FolderShareModal.svelte:74-84` |
| Delete a folder owned by someone else | No (HTTP 403) | Yes | `backend/open_webui/routers/folders.py:682-694` |
| List or open another user's chats | Only chats in a folder shared with them, and share snapshots granted to them (section 3.5) | Only when `ENABLE_ADMIN_CHAT_ACCESS` is on | `backend/open_webui/routers/chats.py:748-749`; `backend/open_webui/models/chats.py:1767-1784` |
| Export every user's chats | No | Only when `ENABLE_ADMIN_EXPORT` is on | `backend/open_webui/routers/chats.py:1049-1053` |

### 3.2 Permission Keys Used in This Area

Code defaults are shown; the live values are in the `user.permissions` setting and each group's
permissions (data, TO BE CONFIRMED). Labels are those in Admin Panel › Users › Groups ›
permissions (`src/lib/components/admin/Users/Groups/Permissions.svelte`).

| Key | Admin label | Code default | Effect in this area | Source |
|---|---|---|---|---|
| `chat.delete` | `Allow Chat Delete` | on | **Delete** in every chat menu, Shift-hover quick delete, archived-list delete and **Delete All Chats**; also needed to delete a folder together with its chats | `backend/open_webui/config.py:1861`; `Permissions.svelte:712`; `backend/open_webui/routers/folders.py:699-707` |
| `chat.share` | `Allow Chat Share` | on | **Share** in chat menus; creating a share link | `backend/open_webui/config.py:1875`; `Permissions.svelte:804`; `src/lib/components/layout/Sidebar/ChatMenu.svelte:311` |
| `chat.export` | `Allow Chat Export` | on | **Download** submenu and **Export Chats** | `backend/open_webui/config.py:1885`; `Permissions.svelte:820` |
| `chat.import` | `Allow Chat Import` | on | **Import Chats**, drag-and-drop import, **Clone**, **Clone Chat** on share pages, fork | `backend/open_webui/config.py:1887`; `Permissions.svelte:836`; `src/lib/components/layout/Sidebar.svelte:42` |
| `chat.temporary` | `Allow Temporary Chat` | on | **Temporary Chat** button and `/temporary` command | `backend/open_webui/config.py:1897`; `Permissions.svelte:919` |
| `chat.temporary_enforced` | `Enforce Temporary Chat` (shown only when temporary chat is allowed) | **off** | Every new chat starts temporary; the toggle and **Save Chat** are hidden | `backend/open_webui/config.py:1899-1900`; `Permissions.svelte:935-943`; `src/lib/components/chat/Navbar.svelte:180-226` |
| `chat.system_prompt` | `Allow Chat System Prompt` | on | The **System Prompt** box in the folder dialog | `backend/open_webui/config.py:1853`; `Permissions.svelte:660`; `src/lib/components/layout/Sidebar/Folders/FolderModal.svelte:216` |
| `features.folders` | `Folders` | on | Folders section and every folder endpoint | `backend/open_webui/config.py:1918`; `Permissions.svelte:1013` |
| `sharing.folders` | `Folders Sharing` | **off** | Lets the folder share panel add people and groups | `backend/open_webui/config.py:1834`; `Permissions.svelte:465` |
| `sharing.public_chats` | `Chats Public Sharing` (shown only when chat sharing is on) | **off** | **Public** option for share links | `backend/open_webui/config.py:1877-1879`; `Permissions.svelte:478-482` |
| `sharing.open_chats` | `Chats Open Sharing` (shown only when chat sharing is on) | **off** | **Open** option for share links | `backend/open_webui/config.py:1881-1883`; `Permissions.svelte:478`, `:501` |
| `access_grants.allow_users` | `Allow Sharing With Users` | on | Adding named people to a share or folder | `backend/open_webui/config.py:1841-1843`; `Permissions.svelte:548` |
| `access_grants.allow_groups` | `Allow Sharing With Groups` | on | Adding groups to a share or folder | `backend/open_webui/config.py:1844-1846`; `Permissions.svelte:567` |

How the server enforces `chat.export`, `chat.temporary`, `chat.temporary_enforced` and
`sharing.folders` beyond what the interface shows is security-sensitive: refer to the platform
maintainer and U of T Information Security (security.utoronto.ca). The screen a person sees
reflects the permissions loaded when their app started; a reload refreshes them
(`users-groups-roles-and-permissions.md`, section 3.5).

### 3.3 Global Switches Above the Permissions

| Switch | Where | Code default | Effect | Source |
|---|---|---|---|---|
| **Folders** (`folders.enable`) | Admin Settings › General › Features | on (`ENABLE_FOLDERS`) | Off hides the Folders section for everyone and refuses every folder request with HTTP 403, admins included | `backend/open_webui/config.py:2024`, `:3102`; `backend/open_webui/routers/folders.py:68-73`; `src/lib/components/layout/Sidebar.svelte:1363` |
| **Folder Max File Count** (`folders.max_file_count`) | Same section, under Folders | empty = unlimited (`FOLDER_MAX_FILE_COUNT`) | The folder dialog refuses more knowledge items than this | `backend/open_webui/config.py:2026`, `:3103`; `src/lib/components/layout/Sidebar/Folders/FolderModal.svelte:46-54` |
| **Community Sharing** (`ui.enable_community_sharing`) | Same section | on (`ENABLE_COMMUNITY_SHARING`) | Shows **Share to Open WebUI Community** in the share dialog and allows the usage-stats export | `backend/open_webui/config.py:2096`, `:3123`; `src/lib/components/chat/ShareChatModal.svelte:175-188`; `backend/open_webui/routers/chats.py:618-622` |
| `ENABLE_ADMIN_CHAT_ACCESS` | Environment only | on | Admins may list and open users' chats | `backend/open_webui/env.py:371`; ground truth |
| `ENABLE_ADMIN_EXPORT` | Environment only | on | Admin **All Chats** export and the database export section | `backend/open_webui/config.py:2082`; `src/lib/components/admin/Settings/Database.svelte:124` |

The live values of the three admin switches are data in the `config` table and the environment
values are deployment settings; all are TO BE CONFIRMED for production. Whether U of T policy
allows **Community Sharing** (it sends a chat to the external `openwebui.com` site, section 5.26)
is TO BE CONFIRMED.

### 3.4 Admin Visibility

With `ENABLE_ADMIN_CHAT_ACCESS` on (the code default), an admin can open any user's chat by its id,
and list a user's chats from the Users page and open them read-only
(`backend/open_webui/models/chats.py:1767-1768`; `backend/open_webui/routers/chats.py:736-766`,
`:1226-1233`). Deleting another user's chat by id, and changing who can open any user's share, do
not depend on that switch (`backend/open_webui/routers/chats.py:1577-1578`, `:1603-1604`,
`:2037-2040`). The full picture of admin access
to chats, including system-created chats, is security-sensitive: refer to the platform maintainer
and U of T Information Security (security.utoronto.ca). For "can an admin read my chats?" see
`users-groups-roles-and-permissions.md`, 11.15.

### 3.5 Who Can Open What

A **chat** (`/c/<id>`) opens for its owner, for an admin under section 3.4, and for anyone with
read access to the folder it sits in (owner of that folder, or a grant on it or on any folder
above it) (`backend/open_webui/models/chats.py:1753-1786`;
`backend/open_webui/utils/access_control/folders.py:6-26`). Everyone else is sent back to the home
page without a message (`src/lib/components/chat/Chat.svelte:2272-2281`).

A **share link** (`/s/<share id>`) opens when (`backend/open_webui/routers/chats.py:104-126`,
`:1208-1233`):

- the share is **Open** — for anyone holding the link; or
- the viewer is signed in, not `pending`, and is the person who shared it, an admin under section
  3.4, a named person or a member of a named group on the share's access list, or any signed-in
  user when the share is **Public**.

Otherwise the share page sends the viewer to the home page, which in turn sends a signed-out
viewer to the sign-in page (section 5.13). How share access is enforced on the server beyond what
is described here is security-sensitive: refer to the platform maintainer and U of T Information
Security (security.utoronto.ca).

## 4. Key Concepts and Terminology

| Term | Meaning in MedIT GPT | Source |
|---|---|---|
| **Chat** (conversation) | One `chat` row: title, owner, the conversation tree as JSON, flags (pinned, archived), folder, tags and timestamps | `backend/open_webui/models/chats.py:129-179` |
| **Chat id** | Random UUID created by the server (`/api/v1/chats/new`, first completion, import, clone, fork); it is the `<id>` in `/c/<id>` | `backend/open_webui/routers/chats.py:788`; `backend/open_webui/main.py:1299-1300`; `backend/open_webui/models/chats.py:636` |
| **Saved chat id** | Any id that does not start with `temporary:`, `local:` or `channel:`; only these are written to the database | `backend/open_webui/utils/chat_id.py:12-16`; `src/lib/utils/chatId.ts:13-14` |
| **Temporary chat** | A chat kept only in the open browser tab; its id is `temporary:` plus the tab's live-connection id (legacy `local:`) | `backend/open_webui/utils/chat_id.py:4-11`, `:19-27`; `src/lib/utils/chatId.ts:1-11`; `src/lib/components/chat/Chat.svelte:3325`, `:3994` |
| **Internal chat** | A system-created chat (a note's built-in chat, a sub-agent or a timer run) marked `meta.internal`; left out of lists, search, counts and exports of the chat list | `backend/open_webui/routers/notes.py:388`; `backend/open_webui/utils/subagents.py:147`, `:163`; `backend/open_webui/models/chats.py:182-183`, `:1501`, `:1559`, `:2019` |
| **Conversation tree** | Messages linked by `parentId` and `childrenIds`; `currentId` marks the branch on screen. Regenerating or editing creates branches | `backend/open_webui/models/chats.py:470-532`; composer document |
| **Message rows** | Each message is also stored as a `chat_message` row (`{chat id}-{message id}`); reads prefer these rows and repair gaps from the JSON | `backend/open_webui/models/chat_messages.py:270-292`; `backend/open_webui/models/chats.py:1048-1099` |
| **Pinned** | Kept in the **Pinned** group at the top of **Chats**, outside folders and the dated list | `backend/open_webui/models/chats.py:1564-1565`, `:1932-1953`; `src/lib/components/layout/Sidebar.svelte:1519-1613` |
| **Archived** | Hidden from the sidebar, folder lists, pinned list, search and tag counts; still opens by address and from **Archived Chats** | `backend/open_webui/models/chats.py:1567-1568`, `:2021-2024`, `:2390` |
| **Unread** | A blue dot and darker title: the chat changed after its owner last opened it and no reply is still being written | `src/lib/components/layout/Sidebar/ChatItem.svelte:133-136`, `:540-544`; `backend/open_webui/models/chats.py:105-126` |
| **Active** | A small spinner on a chat whose reply is still being generated | `backend/open_webui/routers/chats.py:129-139`; `src/lib/components/layout/Sidebar/ChatItem.svelte:533-537` |
| **Time group** | Heading in the chat list from the last-update time in the browser's local time: `Today`, `Yesterday`, `Previous 7 days`, `Previous 30 days`, a month name (this year) or a year | `src/lib/utils/index.ts:1308-1337` |
| **Folder** | A named group of chats with optional settings (system prompt, knowledge, background image, icon); folders can contain folders | `backend/open_webui/models/folders.py:22-33`; `src/lib/components/layout/Sidebar/Folders/FolderModal.svelte:27-33` |
| **Shared folder** | A folder another person shared with you, listed under `Shared` with an eye icon when you may only read | `backend/open_webui/routers/folders.py:239-282`; `src/lib/components/layout/Sidebar/Folders.svelte:69-94` |
| **Read-only** (in a folder) | Chats you do not own in a shared folder: no menu, no rename, no drag | `backend/open_webui/routers/folders.py:620`; `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:961`; `src/lib/components/layout/Sidebar/ChatItem.svelte:688` |
| **Tag** | A label on a chat. Its id is the name in lower case with spaces turned into underscores; `none` is reserved | `backend/open_webui/models/tags.py:61`; `backend/open_webui/routers/chats.py:2192-2198` |
| **Untagged** | The search suggestion for `tag:none`, which finds chats without tags | `src/lib/components/layout/Sidebar/SearchInput.svelte:69-75`; `backend/open_webui/models/chats.py:2076-2084` |
| **Share link** | `/s/<share id>`: a read-only **snapshot** of the chat taken when the link was made or last updated | `backend/open_webui/models/shared_chats.py:18-29`, `:61-112` |
| **Private / Public / Open** | Share visibility: `Only select users and groups with permission can access`, `Accessible to all users`, `Anyone with the link can view` | `src/lib/components/workspace/common/AccessControl.svelte:218-222`, `:541-548` |
| **Clone** | A full copy of a chat into your own chats, titled `Clone of {TITLE}` | `src/lib/components/layout/Sidebar/ChatItem.svelte:224-246`; `backend/open_webui/routers/chats.py:1775-1826` |
| **Fork** | A copy of one branch up to a chosen message, titled `{title} (fork)` | `backend/open_webui/routers/chats.py:1672-1772`; pipeline document 5.16 |
| **Community sharing** | Sending a chat to the external Open WebUI Community site | `src/lib/components/chat/ShareChatModal.svelte:38-66` |

## 5. Workflows (Step by Step)

Menus referred to below:

- **Sidebar chat menu**: the `...` button on a chat row (tooltip `More`, label `Chat Menu`). Items,
  in order: **Share**, **Download** (`Export chat (.json)`, `Plain text (.txt)`,
  `PDF document (.pdf)`), **Rename**, **Mark as unread**, **Pin**/**Unpin**, **Clone**, **Move**,
  **Archive**/**Unarchive**, **Delete** (`src/lib/components/layout/Sidebar/ChatMenu.svelte:305-478`).
  The same menu appears on search results (`src/lib/components/layout/SearchModal.svelte:813-859`).
- **Top-bar menu**: the `...` **Chat actions** button of an open chat. Items: **Scroll to Top**,
  **Artifacts** (when present), **Share**, **Download**, **Copy**, **Move**, **Archive**, **Delete**,
  then the chat's tags (`src/lib/components/chat/Navbar.svelte:146`;
  `src/lib/components/layout/Navbar/Menu.svelte:322-507`).
- **Shift shortcuts**: holding Shift while pointing at a chat row shows instant **Archive** and
  **Delete** icons in place of the menu (`src/lib/components/layout/Sidebar/ChatItem.svelte:716-745`;
  `src/lib/components/layout/SearchModal.svelte:783-810`).

### 5.1 Start a Chat and How It Is Saved

1. Press **New Chat** in the sidebar, or the New Chat shortcut (default Cmd/Ctrl+Shift+O). The
   address becomes `/` (`src/lib/components/layout/Sidebar.svelte:813-823`, `:1212-1230`;
   `src/lib/shortcuts.ts:213-218`; `src/routes/(app)/+layout.svelte:261-264`).
2. Send the first message. For a normal send the server creates the chat row titled `New Chat`
   with a new UUID; a few browser paths create it through `POST /api/v1/chats/new` instead. The
   address changes to `/c/<id>` (`backend/open_webui/main.py:1213`, `:1299-1300`, `:1365-1400`;
   `src/lib/components/chat/Chat.svelte:3953-3980`).
3. The title is then generated, or taken from the first message (pipeline document, 5.12).
4. Started from a folder page (section 5.19), the chat is created inside that folder; without
   write access to the folder the server refuses with `We could not find what you're looking for :/` (`backend/open_webui/main.py:1352-1360`; `backend/open_webui/routers/chats.py:781-785`).
5. If the person is forced into temporary chats, or turned one on, nothing is saved (section 5.11).

### 5.2 Find a Chat in the Sidebar

- **Where a chat appears.** Exactly one of: the **Pinned** group (pinned and not archived), under
  its folder (in a folder, not pinned, not archived), or the dated **Chats** list (everything else
  that is not archived) (`backend/open_webui/models/chats.py:1543-1591`, `:1932-1953`,
  `:2153-2191`). Archived chats appear only under **Archived Chats** and in search with
  `archived:true` (section 5.7).
- **Order.** Newest update first, grouped by time (section 4, Time group); 60 chats load at a time
  and more load as you scroll (`Loading...`) (`src/lib/components/layout/Sidebar.svelte:1615-1698`).
  Folder contents show 10 at a time with **Show more**, unread first
  (`src/lib/components/layout/Sidebar/RecursiveFolder.svelte:523-590`, `:970-991`;
  `backend/open_webui/routers/folders.py:567`, `:592-603`).
- **Row details.** A short age such as `3d` or `5m` shows when the row is not hovered; a blue dot
  marks unread chats; a spinner marks a reply in progress
  (`src/lib/components/layout/Sidebar/ChatItem.svelte:85-102`, `:533-560`).
- **Hover preview.** Resting the pointer on a row for about 0.3 seconds opens a preview of the
  latest messages (desktop only), unless the person turned off **Chat Hover Previews**
  (`src/lib/components/layout/Sidebar/ChatItem.svelte:660-685`;
  `src/lib/components/layout/Sidebar/ChatHoverPreview.svelte:51-79`, `:94-150`). If the chat
  cannot be loaded the preview says `Failed to load chat preview`.
- **Section state.** Whether each sidebar section is open, and the sidebar width, are remembered
  in this browser only (`src/lib/components/layout/Sidebar/Section.svelte:27-31`;
  `src/lib/components/layout/Sidebar.svelte:625-639`). Whether each folder is open is remembered
  on the server (`backend/open_webui/routers/folders.py:464-496`).
- **Pinned shortcuts** above the sections: **Notes**, **Workspace**, **Automations**, **Calendar**,
  **Playground** can be pinned or unpinned by holding Shift in the user menu (**Pin to Sidebar** /
  **Unpin from Sidebar**); the defaults are Notes and Workspace. Pinned **Models** and pinned
  **Notes** sections list items pinned elsewhere (model and notes documents)
  (`src/lib/components/layout/Sidebar.svelte:97`, `:155-199`, `:1301-1328`;
  `src/lib/components/layout/Sidebar/UserMenu.svelte:263-270`).

### 5.3 Search Chats

1. Press **Search** in the sidebar or the Search shortcut (default Cmd/Ctrl+K)
   (`src/lib/components/layout/Sidebar.svelte:1233-1252`; `src/routes/(app)/+layout.svelte:257-260`).
2. With an empty box the dialog lists recent chats from the main list (chats in folders and pinned
   chats are not in this unfiltered list) (`src/lib/components/layout/SearchModal.svelte:404-405`;
   `backend/open_webui/models/chats.py:1561-1565`).
3. Type up to 500 characters. Half a second after typing stops, the server searches
   (`src/lib/components/layout/Sidebar/SearchInput.svelte:207-213`;
   `src/lib/components/layout/SearchModal.svelte:406-415`).
4. Results show the title, a snippet with the match highlighted, and the date. Moving to a result
   with the arrow keys or the pointer previews it on the right on wider screens; until then the
   pane says `Select a conversation to preview`. Enter or a click opens the chat
   (`src/lib/components/layout/SearchModal.svelte:320-322`, `:650-916`).

What the server matches (`backend/open_webui/models/chats.py:1963-2151`;
`backend/open_webui/routers/chats.py:865-904`):

| Rule | Detail |
|---|---|
| Whose chats | Only the searcher's own chats. Other people's chats in shared folders are not searched. |
| Fields | The chat title and message content. On SQLite the content comes from the chat JSON; on PostgreSQL from the chat JSON and the `chat_message` rows, and only content stored as plain text is compared. Attachments, tag names and folder names are not searched as text. |
| Matching | Case-insensitive. A chat matches when the title or any message contains the whole phrase, or when every word (letters and digits) appears somewhere in the title or messages. Whole-phrase matches are listed first, then newest first. |
| Archived | Left out unless `archived:true` (or `archived:false`) is given. |
| Pinned and folders | Included (unlike the unfiltered list). |
| Page size | 60 per page; more load as you scroll. |

Filters, typed as words in the search box (`backend/open_webui/models/chats.py:47`, `:1984-2036`,
`:2074-2131`; suggestions in `src/lib/components/layout/Sidebar/SearchInput.svelte:25-186`):

| Filter | Meaning | Notes |
|---|---|---|
| `tag:<tag id>` | Chats carrying that tag | Several `tag:` words must all match. Tag ids are lower case with underscores. Typing `tag:` suggests your tags and `Untagged`. |
| `tag:none` | Chats with no tags | |
| `folder:<name>` | Chats in that folder or any of its sub-folders | Your own folders only; case-insensitive; write spaces as underscores (`folder:lab_notes`). |
| `pinned:true` / `pinned:false` | Pinned or not | |
| `shared:true` / `shared:false` | Has a share link or not | |
| `archived:true` / `archived:false` | Archived or not | |

Side effect: when the whole search is a single `tag:` word and the first page finds nothing, that
tag is removed from the person's tag list (`backend/open_webui/routers/chats.py:895-902`).

The dialog's **Actions** list offers `Start a new conversation` (opens a new chat with the search
text pre-filled) and, when notes are enabled, `Create a new note`
(`src/lib/components/layout/SearchModal.svelte:254-264`, `:524-541`).

### 5.4 Rename a Chat

1. Double-click the chat's title in the sidebar, or choose **Rename** in the sidebar chat menu or
   on a search result (`src/lib/components/layout/Sidebar/ChatItem.svelte:172-179`, `:424-438`;
   `src/lib/components/layout/SearchModal.svelte:152-187`).
2. Type the new title. Enter saves, Escape cancels; clicking elsewhere also saves. An empty title is
   refused with `Title cannot be an empty string.`
   (`src/lib/components/layout/Sidebar/ChatItem.svelte:206-222`, `:366-377`, `:402-422`).
3. Or press the sparkle **Generate** button beside the field: the placeholder reads `Generating...`
   while the title model writes a title from the active branch, which is then saved; a failure
   shows the error text and keeps the old title (`src/lib/components/layout/Sidebar/ChatItem.svelte:440-513`,
   `:699-715`; how generation works is in the pipeline document).

The new title is saved in both the `title` column and the chat JSON
(`backend/open_webui/models/chats.py:733-740`). Renaming does not change the chat's last-updated
time, so it stays in the same time group (`backend/open_webui/routers/chats.py:1365-1366`). A share
link keeps its old title until the share is updated (section 5.15).

### 5.5 Pin and Unpin

- **Pin** or **Unpin** in the sidebar chat menu toggles the pin
  (`src/lib/components/layout/Sidebar/ChatMenu.svelte:57-60`, `:393-408`).
- Dragging a chat onto the **Pinned** group pins it and takes it out of its folder; dragging it onto
  the **Chats** heading unpins it and takes it out of its folder
  (`src/lib/components/layout/Sidebar.svelte:1425-1474`, `:1528-1576`).
- Pinning or unpinning counts as an update: the chat moves to `Today` and is marked read
  (`backend/open_webui/models/chats.py:1377-1387`).
- Moving a chat into a folder unpins it (`backend/open_webui/models/chats.py:2266-2275`). A pinned
  chat that is later archived disappears from **Pinned** (`backend/open_webui/models/chats.py:1936-1938`).

### 5.6 Read and Unread

- Opening a chat marks it read for its owner, and other open tabs update
  (`src/lib/components/chat/Chat.svelte:1146-1151`; `backend/open_webui/socket/main.py:601-640`).
- **Mark as unread** in the sidebar chat menu brings the blue dot back
  (`src/lib/components/layout/Sidebar/ChatItem.svelte:189-199`; `backend/open_webui/models/chats.py:792-810`).
- **Mark all as read**: the `More` button on the **Chats** heading marks every chat read; the same
  item in a sidebar folder's menu marks that folder (and, for the owner, its sub-folders) read
  (`src/lib/components/layout/Sidebar.svelte:469-484`, `:1493-1517`;
  `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:133-159`;
  `backend/open_webui/routers/folders.py:628-663`). In the folder page's menu the item does nothing
  (no handler is passed) (`src/lib/components/chat/Placeholder/FolderTitle.svelte:250-266`;
  `src/lib/components/layout/Sidebar/Folders/FolderMenu.svelte:23`).
- Your own folders show a count badge (`Unread`) that includes sub-folders; shared folders show none
  (`backend/open_webui/routers/chats.py:142-157`;
  `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:850-857`).
- Read state belongs to the chat's owner only; other people's chats in a shared folder are listed as
  already read (`backend/open_webui/models/chats.py:776-790`; `backend/open_webui/routers/folders.py:614-615`).

### 5.7 Archive and Unarchive

Archive one chat:

1. Choose **Archive** in the sidebar chat menu, on a search result or in the top-bar menu, or use
   the Shift shortcut icon (`src/lib/components/layout/Sidebar/ChatMenu.svelte:453-464`;
   `src/lib/components/layout/Navbar/Menu.svelte:478-487`).
2. The pop-up says `Chat archived.` (a failure says `Failed to archive chat.`). If that chat was
   open you are taken to a new chat (`src/lib/components/layout/Sidebar/ChatItem.svelte:276-296`;
   `src/lib/components/chat/Chat.svelte:4114-4126`).
3. On the server: the archive flag is set, **the chat is taken out of its folder**, its time is
   updated, any reply still being generated is stopped, and tags used only by archived chats drop
   out of the tag list (`backend/open_webui/models/chats.py:1389-1400`;
   `backend/open_webui/routers/chats.py:1916-1925`).

Unarchive one chat:

1. User menu › **Settings** › **Archived Chats**, then the **Unarchive Chat** button on the row; or
   search with `archived:true` and choose **Unarchive** in the result's menu, which says
   `Chat unarchived.` (`src/lib/components/chat/Settings/ArchivedChats.svelte:120-128`, `:343-355`;
   `src/lib/components/layout/SearchModal.svelte:98-114`, `:815`).
2. The chat returns to the dated list, **not** to its old folder, and its tags return to the tag
   list (`backend/open_webui/routers/chats.py:1926-1928`).
3. Moving an archived chat into a folder (from a search result's **Move**) also unarchives it
   (`backend/open_webui/models/chats.py:2276-2280`).

Archive or unarchive everything:

- Settings › **Data Controls** › **Archive All Chats** › **Archive All** asks `Are you sure you want to archive all chats? This action cannot be undone.` Despite that wording it can be undone with
  **Unarchive All** (`src/lib/components/chat/Settings/DataControls.svelte:100-108`, `:124-132`,
  `:212-225`).
- Settings › **Archived Chats** › **Actions** › **Unarchive All** asks `Are you sure you want to unarchive all archived chats?` and then says `All chats have been unarchived.`
  (`src/lib/components/chat/Settings/ArchivedChats.svelte:150-182`, `:224-253`).
- Archive All and Unarchive All only flip the flag on every one of the person's chats: folders are
  kept, running replies are not stopped and the tag list is not tidied
  (`backend/open_webui/models/chats.py:1356-1363`, `:1402-1409`; `backend/open_webui/routers/chats.py:1113-1135`).
  So chats archived with **Archive All** go back into their folders on **Unarchive All**, but chats
  archived one at a time do not.

The Archived Chats panel searches titles only, sorts by **Title** or **Updated at**, loads 60 at a
time and shows a count; opening a title closes Settings and opens the chat
(`backend/open_webui/models/chats.py:1411-1473`; `src/lib/components/chat/Settings/ArchivedChats.svelte:184-392`).
Archived chats keep their share links (section 5.15).

### 5.8 Delete a Chat

Deleting is permanent (section 5.10). Ways to start it:

| Where | Confirmation | Source |
|---|---|---|
| Sidebar chat menu › **Delete**, or **Delete** on a search result | Dialog `Delete chat?` with `This will delete {title}.` | `src/lib/components/layout/Sidebar/ChatItem.svelte:565-575`, `:761-763`; `src/lib/components/layout/SearchModal.svelte:560-570` |
| Shift shortcut trash icon (sidebar or search results) | **None**: the chat is deleted at once | `src/lib/components/layout/Sidebar/ChatItem.svelte:731-744`; `src/lib/components/layout/SearchModal.svelte:797-808` |
| Top-bar menu › **Delete**, or the Delete Chat shortcut (default Cmd/Ctrl+Shift+Backspace) | Dialog `Delete chat?`; success says `Chat deleted.` | `src/lib/components/chat/Chat.svelte:4142-4163`, `:4237-4247`; `src/lib/shortcuts.ts:225-230`; `src/routes/(app)/+layout.svelte:293-296` |
| Settings › **Archived Chats** › **Delete Chat** on a row | Generic dialog `Confirm your action` / `This action cannot be undone. Do you wish to continue?` | `src/lib/components/chat/Settings/ArchivedChats.svelte:130-148`, `:168-173`, `:356-370`; `src/lib/components/common/ConfirmDialog.svelte:139-154` |
| Admin › Users › **Chats** list › **Delete Chat** | Generic dialog | `src/lib/components/layout/ChatsModal.svelte:75-96`, `:363-400` |

Every **Delete** control is hidden from a `user` without `chat.delete`
(`src/lib/components/layout/Sidebar/ChatMenu.svelte:466`; `src/lib/components/layout/Navbar/Menu.svelte:489`;
`src/lib/components/chat/Navbar.svelte:153`). If the deleted chat was open, the browser goes to a
new chat (`src/lib/components/layout/Sidebar/ChatItem.svelte:259-266`).

### 5.9 Delete All Chats

1. User menu › **Settings** › **Data Controls** › **Delete All Chats** › **Delete All** (shown only
   with `chat.delete` or to admins) (`src/lib/components/chat/Settings/DataControls.svelte:227-242`).
2. Confirm `Are you sure you want to delete all chats? This action cannot be undone.` under the
   title `Delete All Chats` (`src/lib/components/chat/Settings/DataControls.svelte:134-142`).
3. The browser goes to a new chat and the sidebar empties. Archived chats and system-created chats
   are deleted too (`backend/open_webui/models/chats.py:2500-2519`). Folders are kept, now empty of
   this person's chats.

### 5.10 What Each Deletion Removes

"Removed" means rows are deleted from the database; nothing is moved to a trash.

| Item | Delete one chat | Delete all chats | Delete a folder with its contents | Delete a folder, keep contents |
|---|---|---|---|---|
| The chat row | Removed (`backend/open_webui/models/chats.py:2476-2498`) | Removed, including archived and system-created chats (`:2500-2519`) | The **folder owner's** chats in the folder and its sub-folders are removed; other people's chats there are moved out (`:2521-2536`; `backend/open_webui/routers/folders.py:715-721`) | Not removed; moved to the main list (`backend/open_webui/routers/folders.py:721`) |
| Its `chat_message` rows | Removed (`backend/open_webui/models/chats.py:2480`, `:2492`) | Removed (`:2511-2513`) | Removed for the deleted chats (`:2530`) | Kept |
| Share snapshot (`shared_chat`) | Removed; the link stops working (`:2484`, `:2496`; `backend/open_webui/models/shared_chats.py:194-202`) | Removed, and share ids cleared (`backend/open_webui/models/chats.py:2503`, `:2553-2569`) | Not removed by this code path; see the note below | Kept |
| The share's access list (`access_grant`) | Left in place, naming a chat that no longer exists (no call in `backend/open_webui/routers/chats.py:1568-1616`) | Left in place (`:707-728`) | Left in place for the chats; the folders' own access lists are removed (`backend/open_webui/routers/folders.py:724`) | Folder access lists removed |
| Tags | Tag names no longer used by any other unarchived chat are removed from the tag list (`backend/open_webui/routers/chats.py:1596`) | Not tidied; leftover tag names stay in the suggestions | Not tidied | Unchanged |
| Links to attached files (`chat_file`) | Depend on the database's delete cascade (`backend/open_webui/models/chats.py:217-230`); the SQLite connection set-up does not switch on SQLite's foreign-key enforcement, so on SQLite these rows can remain (`backend/open_webui/internal/db.py:335-394`) | Same | Same | Unchanged |
| The uploaded files themselves | **Kept** in the person's files (Settings › Data Controls › **Manage Files**); these deletion paths do not delete files | Kept | Kept | Kept |
| Rating snapshots (`feedback.snapshot`) | **Kept**; feedback rows hold their own copy of the chat (`backend/open_webui/models/feedbacks.py:28`) | Kept | Kept | Kept |
| Automation runs pointing at the chat | Link cleared (`backend/open_webui/models/chats.py:2479`, `:2491`) | Links cleared (`:2506-2510`) | Links cleared (`:2527-2529`); automations' folder links cleared (`backend/open_webui/routers/folders.py:726`) | Folder links cleared |
| A reply still being generated | Stopped first (`backend/open_webui/routers/chats.py:1593-1595`) | Not stopped | Not stopped | Not affected |
| System-created child chats | Removed with their parent (`backend/open_webui/routers/chats.py:1598-1601`) | Removed | Not specifically handled | Not affected |
| Usage figures | Analytics and usage summaries read `chat_message` rows, so removed messages stop counting (`backend/open_webui/models/chat_messages.py:520-545`, `:683-751`) | Same | Same | Unchanged |

Note on share links after a folder deletion: whether share links of chats removed through **Delete
folder** stop working is security-sensitive: refer to the platform maintainer and U of T
Information Security (security.utoronto.ca). Treat any report that a deleted chat's link still
opens as a possible privacy incident (section 11.18).

Deleting a **user** removes their chats with their messages and share snapshots, but not their
folders or files (ground truth, Accounts and Access).

### 5.11 Temporary Chats

A temporary chat is not saved as a chat: its id starts `temporary:`, every server step that saves,
titles or tags a chat skips it, and it is gone when the tab is closed or reloaded
(`backend/open_webui/utils/chat_id.py:4-16`; `backend/open_webui/utils/middleware.py:3939`;
`chat-composer-and-message-display.md`, section 6). The controls (the dotted-bubble **Temporary
Chat** button on a new chat, the `/temporary` command, `?temporary-chat=true`, the New Temporary
Chat shortcut and the **Temporary Chat by Default** setting) are described in the composer
document, section 5.24. What matters for history:

- **Label.** A `Temporary Chat` label shows above the composer and under the top bar; its tooltip
  reads `This chat won't appear in history and your messages will not be saved.`
  (`src/lib/components/chat/Placeholder.svelte:116-127`; `src/lib/components/chat/Navbar.svelte:264-268`).
- **Not available while temporary.** **Share**, **Move**, **Archive**, **Delete** and tags are left out
  of the top-bar menu; **Download** still works from the copy in the browser
  (`src/lib/components/layout/Navbar/Menu.svelte:241-256`, `:368`, `:444`).
- **Keep it after all.** Press **Save Chat** (the check-bubble button that replaces Temporary Chat
  once messages exist). The conversation becomes a normal saved chat titled with the first message
  (cut to 50 characters plus `...`), outside any folder, and the address changes to `/c/<id>`. The
  pop-up says `Conversation saved successfully`; with nothing to save it says `No conversation to save`; on failure `Failed to save conversation`
  (`src/lib/components/chat/Navbar.svelte:214-226`; `src/lib/components/chat/Chat.svelte:4346-4383`).
- **Enforced.** With **Enforce Temporary Chat** (`chat.temporary_enforced`) on for a `user`, every
  new chat starts temporary and both the toggle and **Save Chat** are hidden, so that person keeps
  no chat history. Admins are not forced (`src/lib/components/layout/Sidebar.svelte:813-823`;
  `src/lib/components/chat/Chat.svelte:2025-2027`; `src/lib/components/chat/Navbar.svelte:180`).

### 5.12 Share a Chat

1. Open the sidebar chat menu or the top-bar menu and choose **Share**. It is offered to admins and
   to users with `chat.share`, but not for temporary chats or read-only views
   (`src/lib/components/layout/Sidebar/ChatMenu.svelte:311-322`;
   `src/lib/components/layout/Navbar/Menu.svelte:368-380`).
2. The **Share Chat** dialog opens. Before any link exists it explains: `Messages you send after creating your link won't be shared. Users with the URL will be able to view the shared chat.`
   (`src/lib/components/chat/ShareChatModal.svelte:115-156`).
3. Press **Copy Link**. The server takes a snapshot of the chat as it is now, gives it a new share
   id, and the browser copies `<site>/s/<share id>`; the pop-up says `Copied shared chat URL to clipboard!` (`src/lib/components/chat/ShareChatModal.svelte:27-36`, `:190-233`;
   `backend/open_webui/routers/chats.py:1945-1989`).
4. Once a link exists the dialog instead shows one sentence built from the strings
   `You have shared this chat`, `before`, `Click here to`, `delete this link` and
   `and create a new shared link.` ("delete this link" is a button), and an access panel
   (`src/lib/components/chat/ShareChatModal.svelte:132-171`). **A new link starts Private**: with
   no entries the panel shows `No access grants. Private to you.`, and only the sharer (and admins,
   section 3.4) can open it (`src/lib/components/workspace/common/AccessControl.svelte:218-222`,
   `:698-702`; `backend/open_webui/routers/chats.py:113-126`).
5. Decide who may open it:
   - **Add Access** to pick people (search by name or email) or groups; recipients get read
     access (the only role offered) (`src/lib/components/chat/ShareChatModal.svelte:160-170`;
     `users-groups-roles-and-permissions.md`, 5.16).
   - **Public** (`Accessible to all users`): every signed-in MedIT GPT user. Offered only with
     `sharing.public_chats` or to admins.
   - **Open** (`Anyone with the link can view`): anyone who obtains the link. Offered only with
     `sharing.open_chats` or to admins.
   Each change is saved at once and shows `Access updated`; entries the sharer is not allowed to
   make are dropped on save without an error (`src/lib/components/chat/ShareChatModal.svelte:78-85`;
   `backend/open_webui/routers/chats.py:2029-2059`; `users-groups-roles-and-permissions.md`, 5.17).
6. Send the link to the recipients by your usual means; MedIT GPT does not notify them (section 9).

### 5.13 What the Recipient Sees

- **With access:** a page without the sidebar showing the chat title, a date and time (when the
  original chat was started), and the messages read-only. The browser tab shows the title (cut to
  30 characters), a slash and the site name, which is `MedIT GPT` unless `WEBUI_NAME` is set
  otherwise (ground truth). Search engines are told not to index it
  (`src/routes/s/[id]/+page.svelte:118-131`, `:167-224`; `backend/open_webui/main.py:1396`).
- **Clone Chat** appears for signed-in viewers allowed to import (`chat.import`, or admins); it
  copies the snapshot into their own chats as `Clone of {title}` (section 5.25)
  (`src/routes/s/[id]/+page.svelte:46-48`, `:148-164`, `:227-240`).
- **Without access, or when the link no longer exists:** no message; the page sends the viewer to
  the home page. A signed-out viewer is then sent to the sign-in page, and after signing in lands
  on the home page, **not** back on the link, so they must open the link again
  (`src/routes/s/[id]/+page.svelte:50-58`, `:105-108`; `src/routes/(app)/+layout.svelte:197-200`,
  `:411-413`).
- **What the snapshot holds:** the whole chat JSON as it was when the link was made or last
  updated, including other branches of the conversation, and only references to attached files
  (`backend/open_webui/models/shared_chats.py:61-89`). Whether recipients can open the attached
  files themselves depends on file access rules (`files-uploads-and-storage.md`).

### 5.14 Update, Revoke and Manage Share Links

| Task | Steps | Result | Source |
|---|---|---|---|
| Update the shared content | Open **Share** again, press **Update and Copy Link** | Same link; the snapshot is replaced with the chat as it is now; the link is copied | `src/lib/components/chat/ShareChatModal.svelte:228-232`; `backend/open_webui/routers/chats.py:1959-1971` |
| Revoke one link from the chat | **Share** › click `delete this link` | Snapshot and its access list are removed; the old link stops working. A later **Copy Link** makes a **different** link that starts Private | `src/lib/components/chat/ShareChatModal.svelte:138-150`; `backend/open_webui/routers/chats.py:1995-2017` |
| See all your links | Settings › **Data Controls** › **Shared Chats** › **Manage** | Dialog `Shared Chats` listing each link by its snapshot title with a count, searchable and sortable; the title opens the original chat. With no links it shows `No results found` (the dialog's own `You have no shared conversations.` text is passed in but only used by commented-out markup) | `src/lib/components/layout/SharedChatsModal.svelte:139-156`; `src/lib/components/layout/ChatsModal.svelte:101-111`, `:238-244`, `:435-545`; `backend/open_webui/models/shared_chats.py:133-182` |
| Copy a link again | In that list, **Copy Share Link** | Pop-up `Share link copied to clipboard.` | `src/lib/components/layout/ChatsModal.svelte:346-361` |
| Revoke one link from the list | **Unshare Chat** on the row | `Chat unshared successfully.` (or `Failed to unshare chat.`) | `src/lib/components/layout/SharedChatsModal.svelte:90-103` |
| Revoke every link | **Unshare All Shared Chats** › confirm `Are you sure you want to unshare all shared chats? This will remove all share links.` with **Unshare All** | `All shared chats have been unshared.`; every snapshot, share id and share access list of yours is removed | `src/lib/components/layout/SharedChatsModal.svelte:105-137`, `:157-173`; `backend/open_webui/routers/chats.py:1143-1168` |

### 5.15 What Happens to a Share When the Chat Changes

| Event on the original chat | Effect on the link | Source |
|---|---|---|
| New messages, edits, regenerated replies | None until the owner presses **Update and Copy Link** | `backend/open_webui/models/shared_chats.py:91-112` |
| Renamed | The link keeps the old title until updated | `backend/open_webui/models/shared_chats.py:106` |
| Archived, unarchived, pinned, moved to a folder | None; the link keeps working | `backend/open_webui/models/chats.py:1377-1400`, `:2266-2284` (no share changes) |
| Unshared | Snapshot and access list removed | `backend/open_webui/routers/chats.py:1995-2017` |
| Deleted (one chat, or **Delete All Chats**) | Snapshot removed; the link stops working | Section 5.10 |
| Removed by **Delete folder** with contents | Security-sensitive (section 5.10 note) | Section 5.10 |
| Owner's account deleted | Snapshots removed (ground truth) | Ground truth, Accounts and Access |

Links created before the `shared_chat` table existed were converted during the database upgrade and
given **Public** access (all signed-in users) to keep them working
(`backend/open_webui/migrations/versions/c1d2e3f4a5b6_add_shared_chat_table.py:91-143`). Whether
the production database had such older links is TO BE CONFIRMED.

### 5.16 Create and Organize Folders

Folders are available only while the admin **Folders** switch is on and the person has
`features.folders` (section 3.3).

| Task | Steps | Result and messages | Source |
|---|---|---|---|
| Create a folder | Folders heading › **+** (`New Folder`) › dialog `Create Folder` › **Folder Name** (`Enter folder name`) › **Save** | The folder appears at the top level. An empty name gives `Folder name cannot be empty.` If a folder at the same level already has that name (ignoring case), the sidebar adds a number, so `Lab` becomes `Lab 1` | `src/lib/components/layout/Sidebar.svelte:309-358`, `:1363-1371`; `src/lib/components/layout/Sidebar/Folders/FolderModal.svelte:111-152` |
| Create a sub-folder | Folder `...` menu (tooltip `More`) › **Create Folder** | `Folder created successfully`; here a duplicate name is not renumbered and gives `[ERROR: Folder already exists]` | `src/lib/components/layout/Sidebar/Folders/FolderMenu.svelte:50-58`; `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:654-676` |
| Rename | Double-click the folder name, type, press Enter or click away | `Folder updated successfully`; an existing name at that level gives `[ERROR: Folder already exists]` | `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:460-503`, `:751-758`, `:819-844`; `backend/open_webui/routers/folders.py:350-359` |
| Nest or move a folder | Drag it onto another folder; drag it onto the **Folders** or **Chats** heading to move it to the top level | A folder cannot go inside itself or its own sub-folders: `[ERROR: Cannot move a folder into itself or one of its subfolders]` | `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:223-238`; `src/lib/components/layout/Sidebar.svelte:1372-1391`, `:1475-1490`; `backend/open_webui/routers/folders.py:402-452` |
| Open or close | Chevron beside the folder | Remembered on the server for next time | `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:505-521`, `:782-816` |

Folders are listed A to Z (numbers in natural order) in the sidebar, and newest first in **Move**
menus (`src/lib/components/layout/Sidebar/Folders.svelte:30-35`;
`src/lib/components/layout/Sidebar/ChatMenu.svelte:435`). No limit on nesting depth was found in
the code. A folder whose parent is missing or that sits in a loop is put back at the top level the
next time the list loads (`backend/open_webui/routers/folders.py:102-120`). Folders shared with you
cannot be dragged (`src/lib/components/layout/Sidebar/RecursiveFolder.svelte:728`).

### 5.17 Folder Settings

Folder `...` menu › **Edit** opens `Edit Folder` with the same fields as `Create Folder`
(`src/lib/components/layout/Sidebar/Folders/FolderModal.svelte:111-265`):

| Field | What it does | Source |
|---|---|---|
| **Folder Name** | The name | `FolderModal.svelte:140-153` |
| **Folder Background Image** (**Upload** / **Reset**) | A GIF, WebP, JPEG or PNG picture shown behind chats opened from this folder; stored inside the folder record | `FolderModal.svelte:155-212`; `src/lib/components/chat/Chat.svelte:181-188` |
| **System Prompt** | Instructions added to every chat in the folder (how it is applied: pipeline document). Shown to admins and to users with `chat.system_prompt` | `FolderModal.svelte:216-230` |
| **Knowledge** | Files and knowledge bases used for every chat in the folder. Saving waits for uploads (`Please wait until all files are uploaded.`) and enforces **Folder Max File Count** (`Maximum number of files per folder is {max}.`) | `FolderModal.svelte:37-64`, `:232-242` |
| Icon | Click the folder icon on the folder page (`Change folder icon`) to pick an emoji | `src/lib/components/chat/Placeholder/FolderTitle.svelte:86-110`, `:222-240` |
| Remembered models | The models selected while working in the folder are saved with it and preselected next time | `src/lib/components/chat/Chat.svelte:1503-1520`, `:2093-2095` |

Knowledge items the person can no longer read are dropped from the folder, without a message, when
the folder list loads (`backend/open_webui/routers/folders.py:110-130`). Saving knowledge items the
person cannot read is refused with HTTP 403 (`backend/open_webui/routers/folders.py:361-372`).

### 5.18 Put a Chat in a Folder or Take It Out

1. Sidebar chat menu or top-bar menu › **Move** › pick a folder. The list shows only the person's
   own folders, and **Move** is hidden when they have none
   (`src/lib/components/layout/Sidebar/ChatMenu.svelte:424-451`;
   `src/lib/components/layout/Navbar/Menu.svelte:447-476`; `src/lib/components/layout/Sidebar.svelte:255`).
   Success says `Chat moved successfully` (`src/lib/components/layout/Sidebar/ChatItem.svelte:298-317`).
2. Or drag the chat onto a folder, including a folder shared with you with write access
   (`src/lib/components/layout/Sidebar/RecursiveFolder.svelte:161-302`).
3. To take a chat out of folders, drag it onto the **Chats** heading
   (`src/lib/components/layout/Sidebar.svelte:1425-1474`).

Moving into a folder also unpins the chat, unarchives it, marks it read and counts as an update
(`backend/open_webui/models/chats.py:2266-2284`). The server refuses a folder the person cannot
write to with `We could not find what you're looking for :/`
(`backend/open_webui/routers/chats.py:2126-2141`). **Privacy:** a chat moved into a shared folder
can be opened by everyone the folder is shared with (section 5.20).

### 5.19 The Folder Page (`/folders/<id>`)

Clicking a folder's name opens `/folders/<id>` (`src/lib/components/layout/Sidebar/RecursiveFolder.svelte:600-615`,
`:761-780`). If the folder cannot be loaded the error text appears in a pop-up and the browser goes
to the home page (`src/routes/(app)/folders/[folderId]/+page.svelte:24-36`). The page shows:

1. The folder icon and name, and a `...` (`Folder options`) menu with the same items as the sidebar
   folder menu, unless the folder is shared with you read-only
   (`src/lib/components/chat/Placeholder/FolderTitle.svelte:209-279`).
2. The composer. A chat started here is created in the folder. The composer is hidden when the
   folder is someone else's and you only have read access
   (`src/lib/components/chat/Placeholder.svelte:108-112`, `:242`;
   `src/lib/components/chat/Chat.svelte:3619`).
3. The folder's chats from all users who keep chats there, 10 per page, sortable by **Title** or
   **Updated at**, with each owner's picture when the folder is shared; `No chats found` when empty
   (`src/lib/components/chat/Placeholder/FolderPlaceholder.svelte:28-130`, `:199-221`;
   `src/lib/components/chat/Placeholder/ChatList.svelte:125-172`, `:241-250`).

### 5.20 Share a Folder and Work in a Shared Folder

Owner:

1. Folder `...` menu › **Share** opens `Share: {folder name}` with the access panel. There is no
   Public or Open option; new entries default to **Write**; adding people or groups needs
   `sharing.folders` (code default off) or the admin role
   (`src/lib/components/layout/Sidebar/Folders/FolderShareModal.svelte:57-84`).
2. Each change is saved at once and the panel reloads what the server kept
   (`src/lib/components/layout/Sidebar/Folders/FolderShareModal.svelte:44-54`;
   `backend/open_webui/routers/folders.py:508-554`).

Recipients:

| Access | They can | They cannot | Source |
|---|---|---|---|
| Read | See the folder under `Shared` (with an eye icon) together with its sub-folders; open every chat in it, read-only | Add chats, rename, change settings, share, delete | `backend/open_webui/routers/folders.py:239-282`, `:562-625`; `backend/open_webui/models/chats.py:1779-1784`; `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:161`, `:861` |
| Write | All of Read, plus start chats in it, move their own chats into it, create sub-folders (owned by the folder's owner), edit its settings and change who it is shared with | Delete it (HTTP 403); edit other people's chats in it | `backend/open_webui/routers/folders.py:165-203`, `:330-347`, `:508-530`, `:682-694`; `backend/open_webui/routers/chats.py:2137-2141` |

Things to know:

- **Everything in a shared folder is visible to everyone it is shared with**, including chats other
  members put there (`backend/open_webui/routers/folders.py:594-602`, `:619-621`).
- A member's chat in someone else's folder still belongs to the member; the folder owner sees it
  read-only (`backend/open_webui/routers/folders.py:620`).
- **Export** from a folder menu downloads only your own chats in it (section 5.23).
- Shared folders show no unread badge (section 5.6).
- Sharing is by access grant (users document); removing a person or group from the folder's list
  removes their access to all chats in it.

### 5.21 Delete a Folder

1. Folder `...` menu › **Delete** (sidebar or folder page). The dialog `Delete folder?` asks `Are you sure you want to delete "{NAME}"?` with a checkbox `Delete all contents inside this folder`,
   **ticked by default** (`src/lib/components/layout/Sidebar/RecursiveFolder.svelte:679-703`;
   `src/lib/components/chat/Placeholder/FolderTitle.svelte:183-207`).
2. Confirm. Success says `Folder deleted successfully`
   (`src/lib/components/layout/Sidebar/RecursiveFolder.svelte:446-458`).

What happens (`backend/open_webui/routers/folders.py:671-752`):

- Only the folder's owner or an admin may delete it; anyone else gets HTTP 403 with the
  `ACCESS_PROHIBITED` text.
- The folder and **all its sub-folders** are deleted.
- **Ticked:** the folder owner's chats in all of them are **permanently deleted** (section 5.10). If
  there are any, a `user` without `chat.delete` is refused with HTTP 403. Other people's chats in a
  shared folder are not deleted; they move to their owners' main lists.
- **Unticked:** all chats in them move to the main list.
- The folders' access lists are removed, and automations that pointed at them lose that folder.
- There is no undo.

### 5.22 Tags

| Task | Steps | Notes | Source |
|---|---|---|---|
| Add a tag | Open the chat › top-bar `...` › the tag field at the bottom (`Add a tag...`) › type › Enter or Space | Up to 8 of your existing tags are suggested as you type. Space finishes the tag, so typed tags are single words. Tags cannot be edited from the sidebar menu | `src/lib/components/layout/Navbar/Menu.svelte:502-506`; `src/lib/components/common/Tags.svelte:19-59`, `:88-152`; `src/lib/components/chat/Tags.svelte:27-45` |
| Remove a tag | Click the tag (it shows a small cross) | No confirmation | `src/lib/components/common/Tags/TagItem.svelte:20-30`; `src/lib/components/chat/Tags.svelte:47-58` |
| Filter by tag | Search with `tag:<tag id>`, or `tag:none` for untagged chats | Section 5.3 | `backend/open_webui/models/chats.py:1985-1987`, `:2074-2131` |
| Automatic tags | After the first reply in a new chat, when the admin **Tags Generation** setting and the person's **Chat Tags Auto-Generation** setting are both on | The generated list **replaces** the chat's tags; temporary chats get none | `backend/open_webui/models/chats.py:865-889`; pipeline document |

Rules (`backend/open_webui/models/tags.py:52-135`; `backend/open_webui/routers/chats.py:2181-2248`):

- Tags belong to one person: each tag is a `tag` row with that person's id, and a chat stores the
  list of tag ids in `meta.tags`.
- The tag id is the name in lower case with spaces turned into underscores, so `Grant` and `grant`
  are the same tag. The name `none` is refused with `[ERROR: Tag name cannot be 'None']`.
- The tag list tidies itself: a tag disappears from suggestions when no unarchived chat of yours
  still uses it after a removal, a deletion or an archive; unarchiving brings it back
  (`backend/open_webui/models/chats.py:2410-2430`; `backend/open_webui/routers/chats.py:1596`,
  `:1920-1928`, `:2241-2242`).
- Import does not create tag rows (`backend/open_webui/models/chats.py:655-710`): imported chats
  keep their tag ids, and `tag:` searches find them, but the chips appear on a chat only once the
  same tag exists in your tag list (`backend/open_webui/routers/chats.py:2161-2171`).

### 5.23 Export Chats

| What | Where | File | Contents | Source |
|---|---|---|---|---|
| One chat, JSON | Sidebar chat menu or top-bar menu › **Download** › `Export chat (.json)` | `chat-export-<time>.json` | A list holding one chat record: title, the full conversation tree, tags and other metadata, folder id, pinned and archived flags, timestamps | `src/lib/components/layout/Sidebar/ChatMenu.svelte:257-266`; `src/lib/components/layout/Navbar/Menu.svelte:241-256`; `backend/open_webui/models/chats.py:275-297` |
| One chat, text | **Download** › `Plain text (.txt)` | `chat-<title>.txt` | The visible branch only; each message under `### USER` or `### ASSISTANT` | `src/lib/components/layout/Sidebar/ChatMenu.svelte:66-89` |
| One chat, PDF | **Download** › `PDF document (.pdf)` | `chat-<title>.pdf` | With **Stylized PDF Export** on (default), an A4 picture of the messages (black background in dark mode); off, plain text | `src/lib/components/layout/Sidebar/ChatMenu.svelte:91-255`; `src/lib/components/common/InterfaceSettings.svelte:1501-1517` |
| Copy as text | Top-bar menu › **Copy** | Clipboard | The plain-text version; `Copied to clipboard` | `src/lib/components/layout/Navbar/Menu.svelte:426-442` |
| A folder | Folder menu › **Export** | `folder-<name>-export-<time>.json` | **Your own** chats in the folder and its sub-folders, excluding pinned and archived chats | `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:638-652`; `backend/open_webui/models/chats.py:2249-2264` |
| All your chats | Settings › **Data Controls** › **Export Chats** › **Export** | `chat-export-<time>.json` | Every chat you own, including archived and pinned ones; system-created chats excluded | `src/lib/components/chat/Settings/DataControls.svelte:93-98`, `:180-195`; `backend/open_webui/routers/chats.py:977-1013`; `backend/open_webui/models/chats.py:1882-1929` |
| Archived chats | Settings › **Archived Chats** › **Actions** › **Export** | `archived-chat-export-<time>.json` | Every archived chat you own | `src/lib/components/chat/Settings/ArchivedChats.svelte:112-118`, `:255-265` |
| Every user's chats (admin) | Admin Settings › **Database** › **All Chats** › **Export** | `all-chats-export-<time>.json` | All chats of all users | `src/lib/components/admin/Settings/Database.svelte:23-28`, `:143-149` |

Notes:

- Exports contain the chat records only. Uploaded files are stored separately and are not included;
  the chat JSON only refers to them (`backend/open_webui/routers/chats.py:977-1013`).
- Every export contains whatever people typed and received, which may include personal or health
  information; handle the files accordingly.
- The `<time>` in file names is the browser's clock in milliseconds; `<title>` is the chat title as
  is (`src/lib/components/layout/Sidebar/ChatMenu.svelte:88`, `:264`).

### 5.24 Import Chats

1. Settings › **Data Controls** › **Import Chats** › **Import**, then choose a `.json` file (shown
   only with `chat.import` or to admins) (`src/lib/components/chat/Settings/DataControls.svelte:150-178`).
2. The browser reads the file and decides its kind (`src/lib/components/chat/Settings/DataControls.svelte:36-91`;
   `src/lib/utils/index.ts:784-792`, `:832-965`):
   - **MedIT GPT / Open WebUI export** (items with a `chat` key): the conversation, tags, variables,
     pinned and archived flags, folder (kept only if that folder exists and is yours) and the
     original created and updated times are kept (`backend/open_webui/models/chats.py:635-685`).
   - **ChatGPT export** (any item has a `mapping` key): each conversation becomes one linear chat;
     system and tool messages are skipped; the model name comes from ChatGPT or defaults to
     `gpt-3.5-turbo`; entries that are not conversations and conversations that fail validation
     are skipped without a message.
   - **Anything else** is treated as an older format, one chat per item.
3. On success the pop-up says `Successfully imported {count} chats.` (this text is not translated).
   Imported chats get new ids; share links and tag rows are not carried over (section 5.22), and
   because no read time is recorded they show the unread dot until opened
   (`backend/open_webui/models/chats.py:635-653`; `src/lib/components/layout/Sidebar/ChatItem.svelte:131-136`).
   Clones are created the same way.
4. Shortcut: drag an exported `.json` file onto the sidebar. Dropped on the **Chats** section it
   imports into the main list, on the **Pinned** group as pinned chats, on a folder into that
   folder (`src/lib/components/layout/Sidebar.svelte:486-530`, `:1416-1424`, `:1522-1527`;
   `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:182-207`). Invalid JSON dropped on the
   sidebar gives `Invalid file format.`; without the permission the pop-up is `Access prohibited`.

No size or count limit for imports was found in the code; limits in front of the application (for
example a proxy's request-size limit) are TO BE CONFIRMED. A failed import through Data Controls
shows no message (`src/lib/components/chat/Settings/DataControls.svelte:58-91`). Without
`chat.import` the server refuses with HTTP 403 and the `ACCESS_PROHIBITED` text
(`backend/open_webui/routers/chats.py:231-238`, `:807-814`).

### 5.25 Clone a Chat

| Kind | Steps | Result | Source |
|---|---|---|---|
| Clone your chat | Sidebar chat menu or search result › **Clone** | A new chat titled `Clone of {TITLE}` with the same messages, tags, pinned state and variables, in the same folder when that folder is one of yours (`backend/open_webui/models/chats.py:662-673`); the sidebar opens it | `src/lib/components/layout/Sidebar/ChatItem.svelte:224-246`; `backend/open_webui/routers/chats.py:1775-1826` |
| Clone a shared chat | Share page › **Clone Chat** | A copy of the snapshot in your own chats, titled `Clone of {title}`, not pinned, in no folder and without tags | `src/routes/s/[id]/+page.svelte:148-164`; `backend/open_webui/routers/chats.py:1834-1901`; `backend/open_webui/models/chats.py:1711-1730` |
| Fork at a message | **Fork chat** under a reply, or `/fork` | A copy of one branch titled `{title} (fork)` | Pipeline document, 5.16 |

All three need `chat.import` (or the admin role); without it the browser shows `Access prohibited`
and the server answers HTTP 403 (`backend/open_webui/routers/chats.py:231-238`).

### 5.26 Community Sharing

When the admin **Community Sharing** switch is on (code default on), the **Share Chat** dialog
also offers **Share to Open WebUI Community**. Pressing it shows `Redirecting you to Open WebUI Community`, opens `https://openwebui.com/chats/upload` in a new tab and hands that page the chat
and the details of the models it used (`src/lib/components/chat/ShareChatModal.svelte:38-66`,
`:175-188`). The conversation then leaves MedIT GPT for a site outside U of T. Whether this switch is
on in production, and whether its use is permitted, are TO BE CONFIRMED. The same switch also allows
the usage-statistics export used by the **Sync Usage Stats** dialog, which describes what it shares
and what it does not (`backend/open_webui/routers/chats.py:609-704`;
`src/lib/components/chat/Settings/SyncStatsModal.svelte:385-418`).

## 6. Data Model

All timestamps are epoch seconds unless noted (ground truth, Time). The full schema is in
`database-schema-identity-chats-and-config.md`; this section covers the columns this area uses.
Everything below is personal data: chat titles and messages can contain anything a person typed.

### 6.1 The `chat` Table

`backend/open_webui/models/chats.py:129-179`:

| Column | Holds | Changed by |
|---|---|---|
| `id` | Chat UUID | Set at creation |
| `user_id` | Owner | Not changed by this area |
| `title` | Title shown in lists (also kept in the JSON) | Rename, title generation, any save of the JSON (`:740`) |
| `chat` | The conversation JSON (6.2) | Message saves, rename, tag editor |
| `created_at` | Creation time; import can keep the original | Creation, import (`:649`) |
| `updated_at` | Last change; drives sorting and time groups | New or saved messages, pin, archive, move to a folder; **not** a rename or tag change (`backend/open_webui/routers/chats.py:1365-1366`; `:1377-1400`, `:2266-2284`) |
| `share_id` | Current share link id, or empty | Share, unshare, unshare all, delete all (unique) |
| `archived` | Archived flag | Archive, archive all, unarchive all, move to a folder |
| `pinned` | Pinned flag | Pin, move to a folder (clears it) |
| `meta` | `tags` (list of tag ids) plus markers such as `internal`, `type`, `forked_from`, `forked_from_message_id` | Tags, fork, system features |
| `variables` | Chat variables (pipeline document) | Composer |
| `folder_id` | Folder, or empty | Move, single archive (clears it), folder deletion |
| `tasks`, `summary`, `current_message_id` | Task list, compaction summary, the message shown on screen | Pipeline features (`:2666-2686`) |
| `last_read_at` | When the owner last opened it; `0` after **Mark as unread**; empty for imported and cloned chats | Creation, opening, mark read or unread (`:560`, `:776-844`) |
| `timer_at` | Due time while a timer chat waits | Timers (automations document) |

### 6.2 The Chat JSON (`chat.chat`)

A dictionary written mostly by the browser and the completion pipeline. Keys this area relies on
(`backend/open_webui/main.py:1385-1397`; `src/lib/components/chat/Chat.svelte:3957-3971`;
`backend/open_webui/routers/chats.py:1726-1736`, `:1787-1792`):

| Key | Meaning |
|---|---|
| `id`, `title` | Chat id and title |
| `models` | Models chosen for the chat |
| `history.messages` | Every message by id, with `parentId`, `childrenIds`, `role`, `content`, `model`, `timestamp`, files and more (composer document, 6.1) |
| `history.currentId` | The message at the end of the visible branch |
| `messages` | An older flat list kept for compatibility |
| `files` | Files attached to the chat as a whole |
| `tags` | A copy of the tag list written by the tag editor; the authoritative list is `meta.tags` (`src/lib/components/chat/Tags.svelte:36-39`, `:49-52`) |
| `timestamp` | Creation time in **milliseconds**; shown on share pages |
| `originalChatId`, `branchPointMessageId` | Set on clones and forks |

Saves merge rather than replace the stored history, so messages saved by another writer are not
lost, and the server repairs a missing or broken `currentId` when it reads a chat
(`backend/open_webui/models/chats.py:712-751`, `:911-932`, `:470-532`, `:1688-1709`). Null bytes are
stripped from titles and JSON on save and read (`backend/open_webui/models/chats.py:397-437`).

### 6.3 The `chat_message` Table

One row per message, id `{chat id}-{message id}` (`backend/open_webui/models/chat_messages.py:127-172`,
`:270-292`):

| Column | Holds |
|---|---|
| `id`, `chat_id`, `user_id` | Row id, chat (declared to cascade on chat deletion), chat owner |
| `role`, `parent_id` | `user`, `assistant` or `system`; the parent message |
| `content`, `output` | Text or blocks; structured output |
| `model_id` | Model of an assistant message |
| `files`, `sources`, `embeds`, `meta` | Attachments, citations, embeds, extra data |
| `done`, `status_history`, `error` | Whether a reply finished; status lines; error |
| `usage` | Token counts |
| `context_summary` | Compaction checkpoint |
| `created_at`, `updated_at` | `created_at` comes from the message's own timestamp |

How it relates to the JSON:

- **Written alongside the JSON** when a chat is created, imported or cloned, and when a message is
  saved (`backend/open_webui/models/chats.py:568-587`, `:686-708`, `:1181-1190`).
- **Reconciled** on every full save of the chat (`POST /api/v1/chats/{id}`): rows are added or
  updated but not deleted; the code comment notes that message deletion has its own endpoint
  (`backend/open_webui/routers/chats.py:1378-1382`, `:1468-1504`).
- **Read first** when the server needs a chat's messages; if no rows exist, or links between rows
  are missing, the JSON fills the gaps and the rows are back-filled
  (`backend/open_webui/models/chats.py:1048-1099`).
- **Used by analytics** and usage summaries, so deleting chats lowers those figures (section 5.10).
- The JSON stays the source for the screen, exports and share snapshots
  (`backend/open_webui/models/shared_chats.py:76-84`; `backend/open_webui/routers/chats.py:977-1013`).

### 6.4 The `shared_chat` Table

`backend/open_webui/models/shared_chats.py:18-29`:

| Column | Holds |
|---|---|
| `id` | The share id used in `/s/<id>` (a UUID) |
| `chat_id` | The original chat (declared to cascade on chat deletion) |
| `user_id` | Who shared it |
| `title`, `chat` | Snapshot of the title and the chat JSON |
| `created_at`, `updated_at` | When shared; when last updated |

The original chat's `share_id` points at its current snapshot. Re-sharing updates the same row; a
new row (and new link) is made only after the old one was removed
(`backend/open_webui/models/chats.py:1307-1345`; `backend/open_webui/routers/chats.py:1959-1980`).

### 6.5 Access Grants for Shares and Folders

Who may open a share or a folder is stored in `access_grant` rows
(`users-groups-roles-and-permissions.md`, 6.3):

| Resource | `resource_type` | `resource_id` | Principals | Permissions | Source |
|---|---|---|---|---|---|
| Share link | `shared_chat` | The **chat id** (not the share id) | A user, a group, all users (`user` `*`, shown as Public) or anyone (`anyone` `*`, shown as Open) | `read` | `backend/open_webui/routers/chats.py:2057`; `backend/open_webui/models/access_grants.py:14-17`, `:540-560` |
| Folder | `folder` | The folder id; applies to its sub-folders too | Users and groups | `read`, `write` | `backend/open_webui/routers/folders.py:541`; `backend/open_webui/utils/access_control/folders.py:6-26` |

### 6.6 The `folder` Table

`backend/open_webui/models/folders.py:22-33`:

| Column | Holds |
|---|---|
| `id`, `parent_id`, `user_id` | Folder, parent folder (empty at the top level), owner |
| `name` | Name; duplicates at one level are refused by the API, not by the database |
| `meta` | `icon` (emoji code) and `background_image_url` (the picture itself, as a data URL) |
| `data` | `system_prompt`, `files` (knowledge items) and `model_ids` (remembered models) |
| `is_expanded` | Open in the sidebar |
| `items` | Defined but not used by the folder code read for this document |
| `created_at`, `updated_at` | Times |

### 6.7 The `tag` Table

`backend/open_webui/models/tags.py:18-39`: `id` (normalized name), `name` (as typed), `user_id`,
`meta`; the key is (`id`, `user_id`), so each person has their own tags. Chats point at tags only
through `chat.meta.tags`.

### 6.8 Other Rows That Point at Chats

| Table | Link | On chat deletion | Source |
|---|---|---|---|
| `chat_file` | `chat_id`, `message_id`, `file_id`: which files were attached where | Declared to cascade; depends on the database (section 5.10) | `backend/open_webui/models/chats.py:217-230`, `:2571-2664` |
| `feedback` | `meta.chat_id` and a full `snapshot` of the rated chat | Untouched | `backend/open_webui/models/feedbacks.py:28`, `:200-207` |
| `automation_run` | `chat_id` | Set to empty | `backend/open_webui/models/automations.py:47`; `backend/open_webui/models/chats.py:2479` |
| `access_grant` (`shared_chat`) | `resource_id` = chat id | Left in place (section 5.10) | Section 6.5 |

The `shared_chat` and `chat_file` tables and `chat_message.chat_id` declare `ON DELETE CASCADE`
(`backend/open_webui/models/shared_chats.py:22`; `backend/open_webui/models/chats.py:223`;
`backend/open_webui/models/chat_messages.py:132`). Whether the production database enforces such
cascades depends on whether it is SQLite or PostgreSQL (TO BE CONFIRMED; ground truth, Data Stores).

### 6.9 What Lives in the Browser or in User Settings

| Item | Where | Source |
|---|---|---|
| Temporary chats | Browser memory only | Section 5.11 |
| Sidebar width, which sidebar sections are open | This browser's local storage | `src/lib/components/layout/Sidebar.svelte:638`; `src/lib/components/layout/Sidebar/Section.svelte:30` |
| Pinned sidebar shortcuts, pinned models, pinned-notes order | The person's settings on the server (`ui.pinnedMenuItems`, `ui.pinnedModels`, `ui.pinnedNotesOrder`) | `src/lib/components/layout/Sidebar.svelte:233-234`; `src/lib/components/layout/Sidebar/PinnedModelList.svelte:41-50`; `src/lib/components/layout/Sidebar/PinnedNoteList.svelte:49-50` |
| Interface choices (section 7.4) | The person's settings on the server | `src/lib/components/common/InterfaceSettings.svelte` |

## 7. Settings and Configuration

Code defaults are shown. Live values of persistent settings are data in the `config` table and
are TO BE CONFIRMED; after the first start the stored value wins over the environment variable
(ground truth, Settings).

### 7.1 Admin Settings (Admin Settings › General › Features)

| Label (English) | Description shown | Key | Environment seed | Default | Source |
|---|---|---|---|---|---|
| `Community Sharing` | `Allow users to share chats with the Open WebUI community.` | `ui.enable_community_sharing` | `ENABLE_COMMUNITY_SHARING` | on | `src/lib/components/admin/Settings/General.svelte:275-283`; `src/lib/i18n/locales/en-US/translation.json:2378-2379`; `backend/open_webui/config.py:2096`, `:3123` |
| `Folders` | `Allow users to organize chats into folders.` | `folders.enable` | `ENABLE_FOLDERS` | on | `General.svelte:292-297`; `translation.json:2385-2386`; `backend/open_webui/config.py:2024`, `:3102` |
| `Folder Max File Count` (shown when Folders is on; placeholder `Leave empty for unlimited`) | `Maximum number of files allowed per folder.` | `folders.max_file_count` | `FOLDER_MAX_FILE_COUNT` | empty (unlimited) | `General.svelte:300-312`; `translation.json:2383-2384`; `backend/open_webui/config.py:2026`, `:3103`; `backend/open_webui/routers/auths.py:1277` |

The section heading is `Features` (`src/lib/i18n/locales/en-US/translation.json:2402`). The browser
reads these through `/api/config` as `enable_folders`, `folder_max_file_count` and
`enable_community_sharing` (`backend/open_webui/main.py:2354-2355`, `:2369`).

### 7.2 Permissions

The permission keys and their defaults are in section 3.2. They are edited in Admin Panel › Users ›
Groups (default permissions and per group); see `users-groups-roles-and-permissions.md`, 5.11 and
5.14.

### 7.3 Environment-Only Settings

| Variable | Default | Effect here | Source |
|---|---|---|---|
| `ENABLE_ADMIN_CHAT_ACCESS` | `True` | Admin listing and opening of users' chats (section 3.4) | `backend/open_webui/env.py:371` |
| `ENABLE_ADMIN_EXPORT` | `True` | Admin **All Chats** export | `backend/open_webui/config.py:2082` |
| `USER_PERMISSIONS_CHAT_DELETE`, `_SHARE`, `_EXPORT`, `_IMPORT`, `_TEMPORARY`, `_TEMPORARY_ENFORCED`, `_ALLOW_PUBLIC_SHARING`, `_ALLOW_OPEN_SHARING`; `USER_PERMISSIONS_FEATURES_FOLDERS`; `USER_PERMISSIONS_FOLDERS_ALLOW_SHARING` | Section 3.2 | Seed the default permissions on first start only | `backend/open_webui/config.py:1834`, `:1861-1900`, `:1918` |

Production values are TO BE CONFIRMED.

### 7.4 Per-Person Interface Settings (Settings › Interface)

| Label | Description shown | Stored as | Default | Source |
|---|---|---|---|---|
| `Title Auto-Generation` | `Generate chat titles automatically from conversation content.` | `title.auto` | on | `src/lib/components/common/InterfaceSettings.svelte:319`, `:1062`, `:1078`; `src/lib/i18n/locales/en-US/translation.json:2986-2987` |
| `Chat Tags Auto-Generation` | `Generate tags for chats automatically.` | `autoTags` | on | `InterfaceSettings.svelte:320`, `:1108`, `:1124`; `translation.json:2892-2893` |
| `Temporary Chat by Default` | `Start new chats as temporary unless changed.` | `temporaryChatByDefault` | off | `InterfaceSettings.svelte:371`, `:946`, `:962`; `translation.json:2979-2980` |
| `Chat Hover Previews` | `Show a floating preview of recent messages when hovering a chat in the sidebar.` | `chatHoverPreview` | on | `InterfaceSettings.svelte:359`, `:1384`, `:1400`; `translation.json:2890-2891` |
| `Stylized PDF Export` | `Use styled formatting when exporting chats to PDF.` | `stylizedPdfExport` | on | `InterfaceSettings.svelte:382`, `:1501`, `:1517`; `translation.json:2977-2978` |

**Temporary Chat by Default** is offered only to people who may use temporary chats
(`src/lib/utils/settings-access.ts:19-20`, `:66-67`). Title and tag generation also need the admin
switches described in the pipeline document.

### 7.5 Keyboard Shortcuts

Shortcuts can be changed per person and switched off with `Enable Keyboard Shortcuts`
(`When disabled, keyboard shortcuts will not trigger any actions.`)
(`src/lib/components/chat/Settings/Shortcuts.svelte:42`, `:126`, `:135`;
`src/lib/i18n/locales/en-US/translation.json:3018-3019`; `src/routes/(app)/+layout.svelte:250-254`).

| Label | Default keys | Action | Source |
|---|---|---|---|
| `Search` | Cmd/Ctrl+K | Opens or closes the search dialog | `src/lib/shortcuts.ts:257-262`; `translation.json:3032` |
| `New Chat` | Cmd/Ctrl+Shift+O | Starts a new chat | `src/lib/shortcuts.ts:213-218`; `translation.json:3025` |
| `New Temporary Chat` | Cmd/Ctrl+Shift+' | Starts a temporary chat | `src/lib/shortcuts.ts:219-224`; `translation.json:3026` |
| `Delete Chat` | Cmd/Ctrl+Shift+Backspace | Opens the delete dialog for the open chat | `src/lib/shortcuts.ts:225-230`; `translation.json:3016` |
| `Navigate to Previous Chat` / `Navigate to Next Chat` | None | Moves through the chat list | `src/lib/shortcuts.ts:243-254`; `translation.json:3022-3023` |

### 7.6 Fixed Values in the Code

| Value | Where | Source |
|---|---|---|
| 60 chats per page | Sidebar list, search, archived list, shared list, admin user list | `backend/open_webui/routers/chats.py:262`, `:752`, `:876`, `:1074`, `:1183` |
| 10 chats per page | Folder contents in the sidebar and on the folder page | `backend/open_webui/routers/folders.py:592`; `backend/open_webui/routers/chats.py:938` |
| 100 chats per batch | **Export Chats** streaming | `backend/open_webui/routers/chats.py:974` |
| 500 characters | Search boxes | `src/lib/components/layout/Sidebar/SearchInput.svelte:212`; `src/lib/components/chat/Settings/ArchivedChats.svelte:205` |
| 0.5 s / 0.3 s | Search delay in the search dialog / in the archived list | `src/lib/components/layout/SearchModal.svelte:407-415`; `src/lib/components/chat/Settings/ArchivedChats.svelte:83` |
| 50 characters | Title of a saved temporary chat | `src/lib/components/chat/Chat.svelte:4360` |
| 8 | Tag suggestions shown | `src/lib/components/common/Tags.svelte:28` |

## 8. Cron Jobs and Background Processes

**None found in code for this area.** There is no crontab (ground truth). The seven startup loops
listed in the inventory (`knowledgebase/tools/inventory.md`) run automations, schedulers, Redis
listeners and connection-pool clean-ups; none of the code read for this document archives,
deletes or expires chats, folders, tags or share links. A search of `backend/open_webui` for
retention, purge and age-based clean-up found nothing for chats, so chats, archived chats and share
links do not expire on their own.

Work that happens at the moment of a request rather than in the background:

| When | What happens | Source |
|---|---|---|
| A chat is deleted or archived | Replies still being generated for that chat are stopped first (archive: only when archiving, not unarchiving) | `backend/open_webui/routers/chats.py:1593-1601`, `:1921-1923`; `backend/open_webui/tasks.py:296-315` |
| A tag is removed, or a chat deleted or archived | Unused tag names are removed from the person's tag list | Section 5.22 |
| A single-word `tag:` search finds nothing | That tag name is removed | `backend/open_webui/routers/chats.py:895-902` |
| The folder list is loaded | Folders with a missing or looping parent move to the top level; unreadable knowledge items are dropped | `backend/open_webui/routers/folders.py:102-130` |
| A chat is read by the server | A broken visible-branch marker is repaired; missing `chat_message` rows are back-filled from the JSON | `backend/open_webui/models/chats.py:1048-1099`, `:1688-1709` |
| A chat is shared or the share updated | The snapshot is copied then, and only then | `backend/open_webui/models/shared_chats.py:61-112` |
| A chat is opened | It is marked read and the person's other tabs are told | `backend/open_webui/socket/main.py:601-640` |
| **Export Chats** runs | Chats are streamed in batches of 100, each batch with its own short database session so a long export does not block other requests on SQLite | `backend/open_webui/routers/chats.py:974-1013` |
| A folder is opened or closed | The browser waits half a second, then saves the open state | `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:514-521` |
| Any event in section 9.4 | Delivery to event webhooks and event functions is scheduled as a separate background task, so a slow receiver does not delay the person | `backend/open_webui/events.py:1069-1171` |

Title and tag generation run after replies; they belong to the pipeline document.

## 9. Notifications and Emails

### 9.1 No Email, No Notice to Recipients

The application sends no email (ground truth). **Sharing a chat or a folder tells nobody**: the
share and folder-access endpoints only save access entries and publish an event (section 9.4);
none of this area's events is in the list that creates in-app notifications
(`backend/open_webui/routers/chats.py:1945-2059`; `backend/open_webui/routers/folders.py:508-554`;
`backend/open_webui/events.py:669-675`). The sharer has to send the link or tell colleagues.

### 9.2 Pop-ups

Every pop-up (toast) and dialog in this area is catalogued in section 10.

### 9.3 Live Updates in the Browser (Websocket Events)

| Event type | Sent when | Effect | Source |
|---|---|---|---|
| `chat:list` | A saved chat is created or changed by a reply, or a chat is marked read | Sidebar and folder lists refresh; read markers and folder counts update in every open tab | `backend/open_webui/main.py:288-295`; `backend/open_webui/utils/middleware.py:235`; `backend/open_webui/socket/main.py:601-632`; `src/lib/components/layout/Sidebar.svelte:791-810` |
| `chat:active` | A reply starts or finishes | Spinner on the chat row; folder contents refresh | `backend/open_webui/main.py:1764`, `:1875`; `src/lib/components/layout/Sidebar.svelte:777-790`; `src/lib/components/chat/Placeholder/FolderPlaceholder.svelte:132-144` |
| `chat:title`, `chat:tags` | Generated title or tags saved | Title and tag list refresh (pipeline document) | `backend/open_webui/utils/middleware.py:3985-3999`, `:4029-4034` |

Without a working websocket these updates do not arrive and the sidebar catches up on the next
reload or reconnect (`src/lib/components/layout/Sidebar.svelte:716-718`). Websocket set-up is in
`websockets-realtime-and-redis.md`.

### 9.4 Events for Webhooks and Event Functions

Each action below publishes an event. Events go to any admin-configured event webhook whose filter
matches and to active Event functions (`backend/open_webui/events.py:1034-1060`, `:1103-1171`;
configuration in `notifications-webhooks-events-and-banners.md`). Every event carries the acting
person's id, name, email and role (`backend/open_webui/events.py:704`, `:974-985`), so webhook
receivers hold personal data.

| Event | Sent by | Extra data | Source |
|---|---|---|---|
| `chat.created` | `POST /chats/new` and the first completion | Title (plus folder id for `POST /chats/new`) | `backend/open_webui/routers/chats.py:789-795`; `backend/open_webui/main.py:1418-1424` |
| `chat.imported` | Import | Count and new chat ids | `:818-824` |
| `chat.updated` | Any save of the chat JSON, including rename | Title | `:1384-1390` |
| `chat.deleted`, `chat.deleted_all` | Delete one, delete all | Owner id | `:720-727`, `:1608-1615` |
| `chat.pinned`, `chat.unpinned` | Pin toggle | | `:1647-1653` |
| `chat.cloned` | Clone and fork (not clone of a shared chat) | Original chat id | `:1765-1771`, `:1812-1818`, `:1894-1896` |
| `chat.archived`, `chat.unarchived` | Archive toggle, archive all, unarchive all | | `:1119`, `:1134`, `:1930-1936` |
| `chat.shared` | Share created or updated | Share id | `:1964-1970`, `:1982-1988` |
| `chat.unshared` | Unshare one, unshare all | Share id, or count and chat ids | `:1159-1167`, `:2010-2016` |
| `chat.folder_updated` | Move to or out of a folder | Folder id | `:2144-2150` |
| `chat.tag_added`, `chat.tag_removed` | Tag added or removed by hand | Tag name | `:2203-2208`, `:2233-2239` |
| `message.updated` | One message's text edited through the API | Chat id and the first 300 characters of the new text | `:1458-1464` |
| `folder.created`, `folder.updated`, `folder.parent_updated`, `folder.access_updated`, `folder.deleted` | Folder actions | Names, parent ids, number of access entries, deleted folder ids | `backend/open_webui/routers/folders.py:190-196`, `:217-223`, `:376-382`, `:433-439`, `:544-550`, `:728-734` |

Changing who may open a share, and marking chats read or unread, publish no event
(`backend/open_webui/routers/chats.py:2029-2059`, `:2104-2123`). Whether any event webhook or Event
function is configured in production is TO BE CONFIRMED.

## 10. Error, Warning and Notice Messages (Verbatim)

Interpolated values are written as `{name}`. Plain keys are shown as the English text itself (their
`en-US` values are empty); dotted keys are resolved from `src/lib/i18n/locales/en-US/translation.json`.
Most screens in this area print a server refusal as a pop-up containing the server's text
unchanged (for example `src/lib/components/layout/Sidebar/ChatItem.svelte:254-256`,
`src/lib/components/layout/Sidebar/RecursiveFolder.svelte:447-451`), so the backend rows below are
what people see in those pop-ups. Some actions show nothing on failure; those are listed in 10.11.
Rows marked "Log" are server log lines, not user messages; several contain user or chat ids, which
are personal data.

### 10.1 Backend Messages

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 401 or 403) | `backend/open_webui/routers/chats.py:237` (403), `:621`, `:670`, `:686`, `:716`, `:749`, `:1052`, `:1223`, `:1395`, `:1420`, `:1426`, `:1481`, `:1487`, `:1494`, `:1529`, `:1535`, `:1583`, `:1868`, `:1953`, `:1957`, `:2001` (401); `backend/open_webui/constants.py:70-72` | Import, clone, clone of a share or fork without `chat.import` (403); delete or delete all without `chat.delete`; share without `chat.share`; sharing, unsharing or saving a chat that is not yours, or editing or deleting a message in it; reading or cloning a share you were not given (signed in); admin chat list or export with the admin switch off; usage-stats export with Community Sharing off | Ask an admin about the permission, or ask the chat's owner | Effective permissions (section 3.2); for shares, the share's access list (section 5.12) |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 403) | `backend/open_webui/routers/folders.py:72`, `:82`, `:173`, `:185`, `:212`, `:371`, `:529`, `:589`, `:648`, `:693`, `:706` | Any folder action while the admin **Folders** switch is off (admins too) or without `features.folders`; a sub-folder, settings change or sharing change in someone else's folder without write access; knowledge items you cannot read; opening a shared folder's chats without read access; deleting a folder you do not own; deleting a folder with its chats without `chat.delete` | Ask the folder owner or an admin | Live `folders.enable` and permissions (TO BE CONFIRMED); the folder's access list |
| `We could not find what you're looking for :/` | Error (HTTP 404, or 401 where noted) | `backend/open_webui/routers/chats.py:679`, `:784`, `:1233` (401), `:1281` (401), `:1347` (401), `:1590`, `:1852` (401), `:2044`, `:2080`, `:2114`, `:2140`, `:2173` (401), `:2248` (401); `backend/open_webui/main.py:1352-1360`; `backend/open_webui/constants.py:78` | The chat or share no longer exists or is not reachable by you; a new chat or a move into a folder you cannot write to; deleting a chat that is gone | Reload; check the chat or folder still exists; ask the owner for access | Was the chat or folder deleted (time)? Is the person on the folder's access list with write? |
| `We could not find what you're looking for :/` | Error (HTTP 404) | `backend/open_webui/routers/folders.py:180`, `:321`, `:346`, `:366`, `:451`, `:495`, `:521`, `:578`, `:640`, `:688`, `:751` | The folder no longer exists, or you have no access to it; renaming or moving a folder you do not own or cannot write to | Reload the sidebar | Folder deleted? Access list? |
| `Something went wrong :/` | Error (HTTP 400, 401 or 500) | `backend/open_webui/routers/chats.py:287`, `:409`, `:647`, `:704`, `:799`, `:828`, `:954`, `:1041` (400); `:1632`, `:1656`, `:1684`, `:1826`, `:1939`, `:2153`, `:2214` (401); `:1760`, `:1823`, `:1900`, `:1976`, `:1980` (500); `backend/open_webui/constants.py:16-18` | 401: pin, fork, clone, archive, move or tag a chat that is not yours (for example one opened from a shared folder); 400/500: an unexpected failure listing, importing, cloning, forking or sharing | Retry; if it repeats, escalate | Server log at that time (an exception is logged before most 400s) |
| `[ERROR: Tag name cannot be 'None']` | Error (HTTP 400) | `backend/open_webui/routers/chats.py:2194-2198` | Adding a tag named `none` (any case or spacing) | Choose another tag name | None |
| `[ERROR: Folder already exists]` | Error (HTTP 400) | `backend/open_webui/routers/folders.py:159-163`, `:355-359`, `:417-421` | Creating, renaming or moving a folder where a folder with the same name (ignoring case) already exists at that level | Pick another name | None |
| `[ERROR: Cannot move a folder into itself or one of its subfolders]` | Error (HTTP 400) | `backend/open_webui/routers/folders.py:423-429` | Dragging a folder into one of its own sub-folders | Move it elsewhere | None |
| `[ERROR: Error creating folder]` | Error (HTTP 400) | `backend/open_webui/routers/folders.py:198-203`, `:225-231` | Unexpected failure creating a folder | Retry | Log lines `Error creating folder` (`:227`) and `Error inserting a new folder: {e}` (`backend/open_webui/models/folders.py:130`) |
| `[ERROR: Error updating folder]` | Error (HTTP 400) | `backend/open_webui/routers/folders.py:384-390`, `:441-447`, `:485-491` | Unexpected failure renaming, moving or saving a folder | Retry | Log line `Error updating folder: {id}` (`:386`, `:443`, `:487`) |
| `[ERROR: Error deleting folder]` | Error (HTTP 400) | `backend/open_webui/routers/folders.py:736-742` | Unexpected failure deleting a folder | Do not retry blindly; some chats may already be gone | Log line `Error deleting folder: {id}` (`:738`); which chats remain |
| `Your session has expired or the token is invalid. Please sign in again.` | Error (HTTP 401), not displayed | `backend/open_webui/routers/chats.py:1221-1224`; `backend/open_webui/constants.py:59` | A signed-out visitor opens a share that is not Open; the share page redirects instead of showing it | Sign in, then open the link again | Section 5.13 |
| `Failed to process chat stats` | Error (HTTP 400) | `backend/open_webui/routers/chats.py:692-696` | One chat's statistics could not be computed for the community stats sync | Retry | Log line `Error exporting stats for chat {chat.id}: {e}` (`:548`) |
| `Wait for the current response to finish before compacting.` / `Wait for the current response to finish before forking.` | Error (HTTP 409) | `backend/open_webui/routers/chats.py:1283-1287`, `:1686-1690` | Compacting or forking while a reply is running | Wait for the reply | Pipeline document |
| `No model found for context compaction.` / `chat has no messages to fork` | Error (HTTP 400) | `backend/open_webui/routers/chats.py:1305`, `:1699` | Compacting with no model, or forking an empty chat | None | Pipeline document (fork errors from `backend/open_webui/utils/chat_fork.py` are listed there) |
| `Import: cleared %d dangling folder_id(s) for user %s` | Log (info) | `backend/open_webui/models/chats.py:675` | Imported chats pointed at folders the person does not have; they were imported outside folders | None | Contains a user id |
| `Failed to write initial messages to chat_message table: {e}` / `Failed to write imported message {message_id} for chat {chat_id}: {e}` / `Failed to write to chat_message table: {e}` / `Backfill failed for chat %s: %s` | Log (warning) | `backend/open_webui/models/chats.py:587`, `:706-708`, `:1190`, `:1035` | The message mirror could not be written; the JSON still holds the messages and later reads repair the rows | None | Repeated lines suggest a database problem; escalate |
| `Chat %s: %d unresolved parent reference(s) in chat_message — enriching from legacy history` | Log (info) | `backend/open_webui/models/chats.py:1066-1070` | Message rows were incomplete and were repaired from the JSON | None | Informational |
| `Error inserting tag %r: %s` / `delete_tag: {e}` / `delete_tags_by_ids: {e}` | Log (error) | `backend/open_webui/models/tags.py:68`, `:104`, `:119` | Tag rows could not be written or removed | None | Contains the tag name |
| `get_folder_by_parent_id_and_user_id_and_name: {e}` / `update_folder: {e}` / `delete_folder: {e}` | Log (error) | `backend/open_webui/models/folders.py:253`, `:308`, `:358`, `:379`, `:416` | Folder database errors behind the folder messages above | None | Escalate with the time |

### 10.2 Sidebar Chat List and Chat Menus

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Access prohibited` | Error | `src/lib/components/layout/Sidebar.svelte:487-489`, `:1433-1435`, `:1536-1538`; `src/lib/components/layout/Sidebar/ChatItem.svelte:225-227`; `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:246-248` | Importing by drag-and-drop or cloning without `chat.import` | Ask an admin about the permission | Section 3.2 |
| `Invalid file format.` | Error | `src/lib/components/layout/Sidebar.svelte:519-525` | A file dropped on the sidebar is not valid JSON | Drop a MedIT GPT or ChatGPT JSON export | Section 5.24 |
| `Title cannot be an empty string.` | Error | `src/lib/components/layout/Sidebar/ChatItem.svelte:207-208`; `src/lib/components/layout/SearchModal.svelte:167-170` | Saving an empty title | Type a title | None |
| `Generating...` | Notice (placeholder) | `src/lib/components/layout/Sidebar/ChatItem.svelte:628`; `src/lib/components/layout/SearchModal.svelte:696` | The **Generate** title button is working | Wait | Pipeline document if it never finishes |
| `Chat archived.` | Success | `src/lib/components/layout/Sidebar/ChatItem.svelte:289`; `src/lib/components/chat/Chat.svelte:4121`; `src/lib/components/layout/SearchModal.svelte:110` | A chat was archived | Find it under Settings › Archived Chats | None |
| `Chat unarchived.` | Success | `src/lib/components/layout/SearchModal.svelte:110` | **Unarchive** on an archived search result | None | None |
| `Failed to archive chat.` | Error | `src/lib/components/layout/Sidebar/ChatItem.svelte:290-292`; `src/lib/components/chat/Chat.svelte:4122-4124`; `src/lib/components/layout/SearchModal.svelte:111-112` | The archive request failed (the server's own text is not shown) | Reload and retry | Browser console holds `Error archiving chat:`; usually the chat is not the person's own (section 10.1, `Something went wrong :/`) |
| `Chat moved successfully` | Success | `src/lib/components/layout/Sidebar/ChatItem.svelte:312`; `src/lib/components/chat/Chat.svelte:4107`; `src/lib/components/layout/SearchModal.svelte:147` | A chat was moved into a folder | None | None |
| `Failed to move chat` | Error | `src/lib/components/layout/Sidebar/ChatItem.svelte:314-315`; `src/lib/components/chat/Chat.svelte:4109-4110` | No chat or folder was identified for the move | Retry from the menu | None |
| `Clone of {TITLE}` | Notice (title of the copy) | `src/lib/components/layout/Sidebar/ChatItem.svelte:230-235`; `src/lib/components/layout/SearchModal.svelte:70-76` | A chat was cloned | None | None |
| `Delete chat?` with `This will delete {title}.` | Dialog | `src/lib/components/layout/Sidebar/ChatItem.svelte:565-575`; `src/lib/components/chat/Chat.svelte:4237-4247`; `src/lib/components/layout/SearchModal.svelte:560-570` | **Delete** from a chat menu or the shortcut | Confirm or cancel; deletion is permanent | Section 5.10 |
| `Chat deleted.` | Success | `src/lib/components/chat/Chat.svelte:4157` | Deleted from the top-bar menu or shortcut | None | None |
| `Failed to load chat preview` | Error (inline and pop-up) | `src/lib/components/layout/Sidebar/ChatHoverPreview.svelte:75`; `src/lib/components/layout/SearchModal.svelte:384` | The hovered or selected chat could not be loaded | Reload | Was it deleted? |
| `Failed to load chat` | Error | `src/lib/components/layout/SearchModal.svelte:193-198` | **Generate** title from search for a chat that could not be loaded | Reload | As above |
| `Loading...` | Notice | `src/lib/components/layout/Sidebar.svelte:1683-1697` | More chats are loading | Wait | Slow responses: escalate with time |
| `No chats` | Empty state | `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:945-948` | An open folder holds no chats you can see | None | Archived chats never show in folders (section 5.7) |
| `Show more` | Notice (button) | `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:970-990` | A folder holds more than 10 chats | Press it | None |
| `Unread` | Notice (badge tooltip) | `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:850-857` | The folder holds unread chats | Open them or **Mark all as read** | Section 5.6 |
| `Shared` | Notice (heading) | `src/lib/components/layout/Sidebar/Folders.svelte:69-72` | Folders shared with the person exist | None | None |
| `{error}` | Error | `src/lib/components/layout/Sidebar/ChatItem.svelte:190-192`, `:236-238`, `:254-256`, `:301-303`, `:496-498`; `src/lib/components/layout/Sidebar.svelte:349`, `:471`, `:1382`, `:1462`, `:1482` | The server refused a mark-unread, clone, delete, move, title generation, folder creation, mark-all-read or drag move; the text is the server's (section 10.1) | Depends on the text | Section 10.1 |

### 10.3 Search

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `No results found` | Empty state | `src/lib/components/layout/SearchModal.svelte:644-648` | Nothing matched | Check filters; remember archived chats need `archived:true` and others' chats are not searched | Section 5.3 |
| `Select a conversation to preview` | Notice | `src/lib/components/layout/SearchModal.svelte:892-897` | No result selected yet | Arrow down or hover a result | None |
| `Search options` | Notice (heading) | `src/lib/components/layout/Sidebar/SearchInput.svelte:357-360` | Typing the start of a filter word | Pick one | None |
| `search for tags` / `search for folders` / `search for pinned chats` / `search for shared chats` / `search for archived chats` | Notice (help) | `src/lib/components/layout/Sidebar/SearchInput.svelte:25-46` | Descriptions beside `tag:`, `folder:`, `pinned:`, `shared:`, `archived:` | None | None |
| `Untagged` | Notice (suggestion) | `src/lib/components/layout/Sidebar/SearchInput.svelte:69-75` | Suggestion for `tag:none` | None | None |

### 10.4 Share Dialog and Share Page

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Messages you send after creating your link won't be shared. Users with the URL will be able to view the shared chat.` | Notice | `src/lib/components/chat/ShareChatModal.svelte:151-155` | Share dialog before a link exists | Read section 5.12: the link starts Private | The second sentence is only true once access is given |
| `You have shared this chat` `before` `.` `Click here to` `delete this link` `and create a new shared link.` (shown as one sentence) | Notice with link and button | `src/lib/components/chat/ShareChatModal.svelte:133-150` | Share dialog once a link exists | **delete this link** revokes it | Section 5.14 |
| `Copied shared chat URL to clipboard!` | Success | `src/lib/components/chat/ShareChatModal.svelte:223` | **Copy Link** or **Update and Copy Link** | Paste it to the recipients; give them access | Section 5.12 step 4 |
| `Access updated` | Success | `src/lib/components/chat/ShareChatModal.svelte:78-82` | Any change in the share's access panel | Reopen the dialog to see what was kept | `users-groups-roles-and-permissions.md`, 5.17 |
| `{e}` | Error | `src/lib/components/chat/ShareChatModal.svelte:83` | Saving the access list failed | Retry | Section 10.1 |
| `No access grants. Private to you.` | Empty state | `src/lib/components/workspace/common/AccessControl.svelte:698-702` | Share access list empty and visibility Private | Add people or groups, or widen visibility | Section 5.12 |
| `Only select users and groups with permission can access` / `Accessible to all users` / `Anyone with the link can view` | Notice | `src/lib/components/workspace/common/AccessControl.svelte:541-548` | Visibility Private / Public / Open | None | Open means anyone holding the link |
| `You do not have permission to make this public` | Tooltip | `src/lib/components/workspace/common/AccessControl.svelte:516-521` | Hovering the visibility menu without public-sharing permission | Ask an admin | Section 3.2 |
| `Redirecting you to Open WebUI Community` | Notice | `src/lib/components/chat/ShareChatModal.svelte:42-45` | **Share to Open WebUI Community** | None | Section 5.26 |
| `Clone Chat` | Button | `src/routes/s/[id]/+page.svelte:227-240` | Signed-in viewer with `chat.import` on a share page | Press to copy | None |
| `Access prohibited` | Error | `src/routes/s/[id]/+page.svelte:148-152` | **Clone Chat** without `chat.import` | Ask an admin | Section 3.2 |
| `{error}` | Error | `src/routes/s/[id]/+page.svelte:156-159` | Cloning the share was refused | Depends on text | Section 10.1 |

### 10.5 Shared Chats List (Settings › Data Controls)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Shared Chats` | Dialog title | `src/lib/components/layout/SharedChatsModal.svelte:144` | **Manage** beside Shared Chats | None | None |
| `No results found` | Empty state | `src/lib/components/layout/ChatsModal.svelte:238-244` | No share links (or none matching the search) | None | The `You have no shared conversations.` text is not displayed (section 5.14) |
| `Share link copied to clipboard.` | Success | `src/lib/components/layout/ChatsModal.svelte:346-356` | **Copy Share Link** | None | None |
| `Chat unshared successfully.` | Success | `src/lib/components/layout/SharedChatsModal.svelte:96-97` | **Unshare Chat** | None | None |
| `Failed to unshare chat.` | Error | `src/lib/components/layout/SharedChatsModal.svelte:100-101` | The server answered "false"; the current endpoint answers true or an error (`backend/open_webui/routers/chats.py:1995-2017`), so this is not expected | Retry | Escalate if seen |
| `{error}` | Error | `src/lib/components/layout/SharedChatsModal.svelte:91-93`, `:112-114` | Unshare or unshare-all was refused by the server | Retry; if one row cannot be unshared, report it | Section 10.1 and 11.18 |
| `Are you sure you want to unshare all shared chats? This will remove all share links.` (button `Unshare All`) | Dialog | `src/lib/components/layout/SharedChatsModal.svelte:128-137` | **Unshare All Shared Chats** | Confirm or cancel | None |
| `All shared chats have been unshared.` | Success | `src/lib/components/layout/SharedChatsModal.svelte:109` | Unshare all finished | None | None |

### 10.6 Folders

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Folder name cannot be empty.` | Error | `src/lib/components/layout/Sidebar.svelte:310-313`; `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:461-463`, `:655-657`; `src/lib/components/chat/Placeholder/FolderTitle.svelte:46-48`, `:144-146` | Saving or creating a folder with no name | Type a name | None |
| `Folder created successfully` | Success | `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:672-674`; `src/lib/components/chat/Placeholder/FolderTitle.svelte:160-162` | A sub-folder was created | None | None |
| `Folder updated successfully` | Success | `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:489`; `src/lib/components/chat/Placeholder/FolderTitle.svelte:73`, `:99` | Rename, settings or icon saved | None | None |
| `Folder deleted successfully` | Success | `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:454-456`; `src/lib/components/chat/Placeholder/FolderTitle.svelte:120-122` | Folder deleted | None | Section 5.21 for what went with it |
| `Delete folder?` with `Are you sure you want to delete "{NAME}"?` and the checkbox `Delete all contents inside this folder` | Dialog | `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:679-703`; `src/lib/components/chat/Placeholder/FolderTitle.svelte:183-207` | **Delete** in a folder menu | Untick the box to keep the chats; ticked deletes them permanently | Section 5.21 |
| `Please wait until all files are uploaded.` | Error | `src/lib/components/layout/Sidebar/Folders/FolderModal.svelte:40-44` | Saving the folder dialog while knowledge files are still uploading | Wait, then save | None |
| `Maximum number of files per folder is {max}.` | Error | `src/lib/components/layout/Sidebar/Folders/FolderModal.svelte:46-54` | More knowledge items than **Folder Max File Count** | Remove some items | Live `folders.max_file_count` (TO BE CONFIRMED) |
| `No chats found` | Empty state | `src/lib/components/chat/Placeholder/ChatList.svelte:170-173` | Folder page with no chats | None | None |
| `{error}` | Error | `src/lib/components/layout/Sidebar/RecursiveFolder.svelte:135`, `:231`, `:261`, `:273`, `:449`, `:476`, `:493`, `:508`, `:565`, `:602`, `:640`, `:668`; `src/lib/components/chat/Placeholder/FolderTitle.svelte:61`, `:76`, `:92`, `:102`, `:115`, `:128`, `:156`; `src/lib/components/layout/Sidebar/Folders/FolderModal.svelte:69`; `src/routes/(app)/folders/[folderId]/+page.svelte:25-27` | Any folder action refused by the server | Depends on the text (section 10.1) | Section 10.1 |

### 10.7 Tags

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Add a tag...` | Notice (placeholder) | `src/lib/components/common/Tags.svelte:96` | The tag field in the top-bar menu | Type a tag and press Enter | None |
| `{error}` | Error | `src/lib/components/chat/Tags.svelte:27-34` | Adding a tag was refused, for example `[ERROR: Tag name cannot be 'None']` | Choose another name | Section 10.1 |

### 10.8 Archived Chats (Settings)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Archived Chats` (dotted key `settings.personal.archivedChats.title`) | Heading | `src/lib/components/chat/Settings/ArchivedChats.svelte:186-193`; `src/lib/i18n/locales/en-US/translation.json:2769` | Panel opened | None | None |
| `You have no archived conversations.` | Empty state | `src/lib/components/chat/Settings/ArchivedChats.svelte:276-281` | No archived chats (or none matching the title search) | None | None |
| `Are you sure you want to unarchive all archived chats?` (button `Unarchive All`, dotted key `settings.personal.archivedChats.unarchiveAll.label`) | Dialog | `src/lib/components/chat/Settings/ArchivedChats.svelte:175-182`; `translation.json:2770` | **Actions** › **Unarchive All** | Confirm or cancel | Section 5.7 |
| `All chats have been unarchived.` | Success | `src/lib/components/chat/Settings/ArchivedChats.svelte:155` | Unarchive all finished | None | Chats archived one by one return to the main list, not their folders |
| `Export` (dotted key `settings.personal.archivedChats.exportArchivedChats.label`) | Menu item | `src/lib/components/chat/Settings/ArchivedChats.svelte:255-265`; `translation.json:2768` | Downloads `archived-chat-export-<time>.json` | None | Section 5.23 |
| `Confirm your action` with `This action cannot be undone. Do you wish to continue?` | Dialog | `src/lib/components/chat/Settings/ArchivedChats.svelte:168-173`; `src/lib/components/common/ConfirmDialog.svelte:139-154` | **Delete Chat** on an archived row | Confirm or cancel; deletion is permanent | None |
| `{error}` | Error | `src/lib/components/chat/Settings/ArchivedChats.svelte:121-123`, `:134-136`, `:158-160` | Unarchive, delete or unarchive all refused | Reload: the row is removed from the panel even when the request failed | Section 10.1 |

### 10.9 Data Controls (Settings)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Data Controls`; section `Chats` | Headings | `src/lib/components/chat/Settings/DataControls.svelte:145-147`, `:159-162`; `translation.json:2816`, `:2812` | Panel opened | None | None |
| `Import Chats` / `Import chat history from a JSON export file.` | Row (shown with `chat.import`) | `DataControls.svelte:163-178`; `translation.json:2808-2809` | Panel opened | None | Section 5.24 |
| `Export Chats` / `Download your chat history as a JSON export.` | Row (shown with `chat.export`) | `DataControls.svelte:180-195`; `translation.json:2806-2807` | Panel opened | None | Section 5.23 |
| `Shared Chats` / `Review and manage chats you have shared.` | Row | `DataControls.svelte:197-210`; `translation.json:2814-2815` | Panel opened | None | Section 5.14 |
| `Archive All Chats` / `Move every chat into the archive after confirmation.` (button `Archive All`) | Row | `DataControls.svelte:212-225`; `translation.json:2801-2803` | Panel opened | None | Section 5.7 |
| `Delete All Chats` / `Permanently delete every chat after confirmation.` (button `Delete All`) | Row (shown with `chat.delete`) | `DataControls.svelte:227-242`; `translation.json:2804-2805` | Panel opened | None | Section 5.9 |
| `Are you sure you want to archive all chats? This action cannot be undone.` (title `Archive All Chats`) | Dialog | `src/lib/components/chat/Settings/DataControls.svelte:124-132` | **Archive All** | Confirm or cancel. It **can** be undone with **Unarchive All** | Section 5.7 |
| `Are you sure you want to delete all chats? This action cannot be undone.` (title `Delete All Chats`) | Dialog | `src/lib/components/chat/Settings/DataControls.svelte:134-142` | **Delete All** | Confirm only if every chat should go | Section 5.10 |
| `Successfully imported {count} chats.` | Success (English only) | `src/lib/components/chat/Settings/DataControls.svelte:86-88` | Import finished | Check the sidebar | Section 5.24 |
| `{error}` | Error | `src/lib/components/chat/Settings/DataControls.svelte:102-104`, `:112-114` | Archive all or delete all refused | Depends on the text | Section 10.1 |

### 10.10 Temporary Chats and the Top-Bar Menu

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Temporary Chat` | Notice (label) | `src/lib/components/chat/Placeholder.svelte:116-127`; `src/lib/components/chat/Navbar.svelte:264-268` | A temporary chat is on | None | Section 5.11 |
| `This chat won't appear in history and your messages will not be saved.` | Tooltip | `src/lib/components/chat/Placeholder.svelte:117-119` | Hovering the label | Press **Save Chat** to keep it | None |
| `No conversation to save` | Error | `src/lib/components/chat/Chat.svelte:4347-4350` | **Save Chat** with no messages | None | None |
| `Conversation saved successfully` | Success | `src/lib/components/chat/Chat.svelte:4377` | **Save Chat** worked | The chat is now in the sidebar | None |
| `Failed to save conversation` | Error | `src/lib/components/chat/Chat.svelte:4379-4382` | **Save Chat** failed | Copy or download the conversation before closing the tab | Escalate with the time |
| `Copied to clipboard` | Success | `src/lib/components/layout/Navbar/Menu.svelte:430-437` | Top-bar **Copy** | None | None |

### 10.11 Actions That Fail Without a Message

| Action | What the person sees | Source |
|---|---|---|
| Opening a share link without access, or one that no longer exists | Silently sent to the home page (or sign-in) | `src/routes/s/[id]/+page.svelte:50-58`, `:105-108` |
| Opening `/c/<id>` for a chat that is gone or not theirs | Silently sent to a new chat | `src/lib/components/chat/Chat.svelte:2272-2281` |
| **Copy Link** in the share dialog refused (for example no `chat.share`) | Nothing in most browsers; in Safari the success pop-up appears even though no link was made | `src/lib/components/chat/ShareChatModal.svelte:194-224` |
| Pin or unpin refused | Nothing changes | `src/lib/components/layout/Sidebar/ChatMenu.svelte:57-60` |
| Removing a tag refused | The chip may come back on reload | `src/lib/components/chat/Tags.svelte:47-58` |
| Data Controls import fails or the file is not valid JSON | Nothing | `src/lib/components/chat/Settings/DataControls.svelte:36-91` |
| Saving a folder's sharing fails | The panel keeps showing the change | `src/lib/components/layout/Sidebar/Folders/FolderShareModal.svelte:44-54` |
| **Mark all as read** in the folder page's menu | Nothing (no handler) | Section 5.6 |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it never changes chats, folders, shares, settings, roles or permissions, and
never opens a person's chats. "Ask an admin to confirm" means asking someone with the `admin` role
to look without changing anything. Support contacts and escalation routes are TO BE CONFIRMED
(ground truth, Contacts). Chats can hold personal and health information: ask for chat **ids**,
folder **names**, times and screenshots of the **error only**, never for chat content or exports.
A chat id is the part after `/c/` in the address bar; a share id is the part after `/s/`.

### 11.1 "I sent my colleague a share link but it just takes them to the home page"

**Symptom.** The recipient opens `/s/<id>` and lands on a new chat (or the sign-in page) with no
message.

**Likely causes, in order.**
1. The link is still **Private**: a new link opens only for its owner until people, groups, Public
   or Open are added in the share dialog, whatever the dialog's first sentence says (section 5.12).
2. The colleague was added, but the entry was dropped on save because the sharer lacks
   `access_grants.allow_users` / `allow_groups`, or chose Public without `sharing.public_chats`
   (`users-groups-roles-and-permissions.md`, 5.17).
3. The colleague was signed out: after signing in they land on the home page and must open the link
   again (section 5.13).
4. The link was revoked, re-created (a new link has a new id) or the chat was deleted (section 5.14).
5. The colleague's account is `pending`.

**Diagnostic steps.** Ask the sharer to open **Share** on that chat and read out the visibility
(`Private`, `Public` or `Open`) and the Access List names (or send a screenshot of the panel). Ask
whether they pressed `delete this link` or **Copy Link** again after sending. Ask the recipient
whether they were signed in.

**Resolution.** Guide the sharer to add the colleague (or a group) under **Add Access**, then the
colleague opens the link again while signed in. If the option to add people is missing, see 11.11.

**Escalation.** Sharer's account email, the share id, the recipient's account email, the time tried,
and a screenshot of the access panel, to the admin team (TO BE CONFIRMED).

### 11.2 "Who can see the chat I shared?"

**Symptom.** A privacy question about a share link.

**Likely causes, in order.** Not a fault: the answer depends on the share's access panel.

**Diagnostic steps.** Ask the person to open **Share** and read the visibility and Access List.

**Resolution.** Explain (section 3.5): **Private** with an empty list = only them (and admins under
the admin chat access setting); named people and groups = those people; **Public** = every
signed-in MedIT GPT user; **Open** = anyone who has the link, signed in or not. Recipients see the
snapshot taken when the link was made or last updated, including all branches of the
conversation. A chat placed in a **shared folder** is visible to everyone the folder is shared
with, independently of any share link (section 5.20). To stop sharing, use `delete this link` or
Settings › Data Controls › Shared Chats (section 5.14).

**Escalation.** If the person believes information reached the wrong people, treat it as a possible
privacy incident (11.18).

### 11.3 "The person I shared with sees an old version of the chat"

**Symptom.** New messages or a new title are missing on the share page.

**Likely causes, in order.**
1. Share links are snapshots; changes after sharing are not shown until the owner presses **Update
   and Copy Link** (section 5.15).

**Diagnostic steps.** Ask whether **Update and Copy Link** was pressed after the latest messages.

**Resolution.** The owner opens **Share** and presses **Update and Copy Link**; the link stays the
same.

**Escalation.** Not normally needed.

### 11.4 "My chat has disappeared from the sidebar"

**Symptom.** A chat no longer appears under **Chats**.

**Likely causes, in order.**
1. It is pinned (top **Pinned** group) or inside a folder (chats in folders are listed only under
   their folder) (section 5.2).
2. It was archived (Settings › Archived Chats).
3. Folders were switched off for the person, hiding every chat that sits in a folder (11.5).
4. It is further down: only 60 chats load until you scroll.
5. It was deleted (by the person, by **Delete All Chats**, with a folder, or by an admin).
6. It was never saved because it was a temporary chat.

**Diagnostic steps.** Ask the person to open **Search** and type words from the chat; then try
`archived:true` plus words. Search covers pinned, foldered and (with the filter) archived chats.
Ask whether they recently deleted a folder or used **Delete All Chats**, and whether the chat showed
the `Temporary Chat` label.

**Resolution.** Show them where the chat is (Pinned, folder, Archived). If it was temporary or
deleted, explain that it cannot be recovered from the application (11.8).

**Escalation.** If it should exist but no search finds it: account email, approximate title and
time last seen, and whether folders were involved.

### 11.5 "The Folders section is gone, and so are the chats that were in my folders"

**Symptom.** No **Folders** section; chats that were in folders are missing from **Chats**.

**Likely causes, in order.**
1. The admin **Folders** switch was turned off (affects everyone) (section 3.3).
2. The person lost `features.folders` (their groups changed, or the defaults changed) (section 3.2).
3. The person's app loaded old permissions; a reload fixes stale menus.

**Diagnostic steps.** Ask whether colleagues still see **Folders**. Ask the person to reload. Ask
an admin to confirm the **Folders** switch and the person's effective `features.folders`.

**Resolution.** The chats are not deleted: they are still found by **Search**, by words in the chat
or by typing `folder:<folder name>` in full (no folder suggestions appear while folders are off,
but the search itself does not check the switch), and they open by address
(`backend/open_webui/models/chats.py:1989-1992`; `src/lib/components/layout/Sidebar.svelte:242-245`).
Folders and their chats reappear when the switch or permission is restored, which only an admin
can do.

**Escalation.** Account email, whether colleagues are affected, time first noticed.

### 11.6 "I archived a chat and now I can't find it"

**Symptom.** An archived chat is not in the sidebar or in normal search.

**Likely causes, in order.**
1. Archived chats are hidden everywhere except Settings › **Archived Chats** and search with
   `archived:true` (section 5.7).
2. **Archive All Chats** was used; its dialog wrongly says it `cannot be undone`.

**Diagnostic steps.** Ask the person to open User menu › Settings › Archived Chats and search the
title.

**Resolution.** Use **Unarchive Chat** on the row, or **Actions** › **Unarchive All**. Everything
archived comes back.

**Escalation.** Not normally needed.

### 11.7 "I unarchived a chat but it didn't go back into its folder"

**Symptom.** After unarchiving, the chat is in the dated list, not its folder.

**Likely causes, in order.**
1. Archiving a single chat removes it from its folder; unarchiving does not restore that
   (`backend/open_webui/models/chats.py:1389-1400`). (**Archive All** keeps folders.)

**Diagnostic steps.** Ask how it was archived (one chat, or Archive All).

**Resolution.** Move it back with the chat menu › **Move** or by dragging it onto the folder.

**Escalation.** Not needed.

### 11.8 "I deleted a chat by mistake. Can you get it back?"

**Symptom.** A deleted chat is wanted back.

**Likely causes, in order.** Deletion is permanent in the application (section 5.10). There is no
trash. Possible partial sources: the person's own exports, a share recipient's **Clone**, or a
rating snapshot if they rated a reply (held by admins).

**Diagnostic steps.** Ask when it was deleted and how (one chat, all chats, with a folder), and
whether they ever exported it or shared it with someone who cloned it.

**Resolution.** Explain that the application cannot restore it. If they have an export file, they
can import it (section 5.24).

**Escalation.** Restoring from a database backup, if backups exist, is a platform decision (backup
arrangements TO BE CONFIRMED). Send account email, approximate title, deletion time and how it was
deleted.

### 11.9 "I deleted a folder and the chats inside it are gone"

**Symptom.** After deleting a folder, its chats are missing.

**Likely causes, in order.**
1. The **Delete all contents inside this folder** box is ticked by default; with it ticked, the
   folder owner's chats in the folder and all sub-folders are permanently deleted (section 5.21).
2. If the box was unticked, the chats moved to the main **Chats** list.

**Diagnostic steps.** Ask whether they unticked the box. Ask them to search for a known chat.

**Resolution.** If unticked, show them the chats in the main list. If ticked, treat as 11.8. Other
people's chats in a shared folder were moved to their owners' lists, not deleted.

**Escalation.** As 11.8, with the folder name.

### 11.10 "There's no Delete option" or "It says I don't have permission to delete"

**Symptom.** **Delete** is missing from chat menus and **Delete All Chats** is missing, or deleting
shows the `ACCESS_PROHIBITED` text.

**Likely causes, in order.**
1. The person lacks `chat.delete` (code default on; an admin may have turned it off) (section 3.2).
2. Deleting a folder with its chats also needs `chat.delete`.
3. The chat is not theirs (for example opened from a shared folder).

**Diagnostic steps.** Ask an admin to confirm the person's effective `chat.delete`.

**Resolution.** Explain the setting. Archiving remains available as a way to hide chats. Only an
admin can change the permission, through the normal process.

**Escalation.** Account email and screenshot of the menu.

### 11.11 "There's no Share option" or "I can't make my link Public"

**Symptom.** **Share** is missing from chat menus, or the share panel offers only **Private**, or
**Add Access** finds nobody.

**Likely causes, in order.**
1. `chat.share` is off for the person (Share hidden) (section 3.2).
2. The chat is temporary or read-only (Share hidden) (section 5.11).
3. `sharing.public_chats` and `sharing.open_chats` are **off by default**, so only Private (with
   named people and groups) is offered (section 3.2).
4. `access_grants.allow_users` or `allow_groups` is off, so people or groups cannot be added.

**Diagnostic steps.** Ask for a screenshot of the menu or panel; ask an admin to confirm the
person's effective permissions.

**Resolution.** Explain which option is allowed. Whether Public or Open sharing should be allowed at
U of T is a policy decision (TO BE CONFIRMED); tier 1 does not change permissions.

**Escalation.** Account email, what they want to share with whom, and the screenshot.

### 11.12 "Search doesn't find my chat"

**Symptom.** A known chat does not appear in search results.

**Likely causes, in order.**
1. It is archived: add `archived:true` (section 5.3).
2. It is someone else's chat in a shared folder: search covers only your own chats; open it from
   the folder instead.
3. The words are only in an attachment, a tag or a folder name: those are not searched as text; use
   `tag:` or `folder:` filters.
4. A filter is mistyped: tag ids are lower case with underscores (`tag:grant_report`); folder names
   use underscores for spaces.
5. On PostgreSQL, the text sits in a message whose content is stored as blocks rather than plain text, which that comparison skips (section 5.3).
6. The chat was deleted or was temporary.

**Diagnostic steps.** Ask for the exact search typed (no chat content needed beyond the search
words they choose to share) and try the variations above with them.

**Resolution.** Guide them through the filters. Results show 60 at a time and load more on
scrolling.

**Escalation.** If a chat that should match never appears: account email, the search used, the
chat id if known.

### 11.13 "My tags disappeared" or "My imported chats lost their tags"

**Symptom.** Tag chips or tag suggestions are missing.

**Likely causes, in order.**
1. Automatic tag generation replaced the chat's tags after its first reply (pipeline document).
2. The tag was used only by archived or deleted chats, so it was tidied out of the suggestions; it
   returns when such a chat is unarchived (section 5.22).
3. A search consisting only of that `tag:` found nothing, which removes the tag name.
4. Imported chats keep their tag ids, but tag rows are not created by import, so chips do not show
   until the same tag exists in the person's list (section 5.22).

**Diagnostic steps.** Ask whether the chats are archived or imported, and whether `tag:<name>`
search still finds them (it reads the chat's own list).

**Resolution.** Re-adding the tag by hand on any chat restores the name. For imported chats, adding
the tag once to one chat makes the chips appear on all chats that carry it.

**Escalation.** Not normally needed.

### 11.14 "My chat import didn't do anything"

**Symptom.** After choosing a file in Data Controls › Import Chats, nothing appears and no
message shows, or dropping a file shows `Invalid file format.`

**Likely causes, in order.**
1. The file is not valid JSON, or not a MedIT GPT, Open WebUI or ChatGPT export (section 5.24).
2. The person lacks `chat.import` (the Import row is hidden; drag-and-drop shows `Access prohibited`).
3. ChatGPT conversations that fail validation are skipped without notice.
4. The file was refused before reaching the application (size limits in front of the application
   are TO BE CONFIRMED).

**Diagnostic steps.** Ask for the file's origin (which product exported it), its size, and a
screenshot. Do not ask for the file itself: it contains chat content.

**Resolution.** Suggest re-exporting from the source and importing again; if it still fails,
escalate.

**Escalation.** Account email, file origin and size, time tried.

### 11.15 "I can see the chats in a shared folder but I can't change anything"

**Symptom.** In a folder under `Shared`, chats have no menu, cannot be renamed or dragged; or the
folder shows an eye icon and no composer on its page.

**Likely causes, in order.**
1. Other people's chats in a shared folder are always read-only to you (section 5.20).
2. The folder was shared with **Read** access: no new chats, no moves into it, no settings.
3. Even with **Write** access, only the owner (or an admin) can delete the folder.

**Diagnostic steps.** Ask whether the folder shows the eye icon (read-only) and who owns it.

**Resolution.** Explain the access level. The folder owner can change the person's access to Write
in the folder's **Share** dialog. To work on someone else's chat, the person can ask for it to be
shared and use **Clone Chat**.

**Escalation.** Not normally needed.

### 11.16 "Clicking a link to my chat just opens a new chat"

**Symptom.** A `/c/<id>` bookmark or link opens a blank new chat.

**Likely causes, in order.**
1. The chat was deleted (by the person, with a folder, by **Delete All Chats**, or by an admin).
2. The link points at someone else's chat that the person cannot open (section 3.5).
3. The person is signed in to a different account.

**Diagnostic steps.** Ask for the chat id and when the link last worked; ask them to search for the
chat.

**Resolution.** If it is in **Archived Chats** it still opens from there. Otherwise see 11.8.

**Escalation.** Account email, chat id, time last worked.

### 11.17 "A chat keeps showing a blue dot or a spinner"

**Symptom.** The unread dot does not clear, or a spinner stays on a chat.

**Likely causes, in order.**
1. The dot clears when the chat is opened; it returns whenever the chat changes again (for example
   a background reply or automation finished) (section 5.6).
2. **Mark as unread** was used, or the chat was imported or cloned (section 5.24).
3. A spinner means a reply is still being generated for that chat; it clears when the reply
   finishes (section 9.3).
4. Live updates are not reaching the browser (websocket problems): the list catches up on reload.

**Diagnostic steps.** Ask them to open the chat, then reload the page.

**Resolution.** **Mark all as read** (the `More` button on the **Chats** heading) clears every dot.

**Escalation.** If spinners persist across reloads for many people, escalate as a platform issue
with times (`websockets-realtime-and-redis.md`).

### 11.18 "I deleted the chat but the share link still opens" or "My chat reached the wrong people"

**Symptom.** A share link keeps working after the person believes the chat or folder was deleted,
or a chat was shared more widely than intended.

**Likely causes, in order.** Security-sensitive: refer to the platform maintainer and U of T
Information Security (security.utoronto.ca). Do not test the link further or look for workarounds.

**Diagnostic steps.** Record only: the share id, what was deleted and how (one chat, all chats,
folder with contents), and the time.

**Resolution.** Treat it as a possible privacy incident and refer it (Escalation). Tier 1 does not
attempt a fix.

**Escalation.** Refer immediately, per U of T guidance, to the University's privacy office
(privacy.utoronto.ca) and Information Security (security.utoronto.ca); the internal escalation route
for MedIT GPT is TO BE CONFIRMED.

### 11.19 "Every new chat is temporary and nothing is saved"

**Symptom.** New chats show `Temporary Chat`; there is no toggle or **Save Chat** button; nothing
appears in history.

**Likely causes, in order.**
1. **Enforce Temporary Chat** (`chat.temporary_enforced`) is on for the person through the defaults
   or a group (section 3.2).
2. The person turned on **Temporary Chat by Default** (then the toggle and **Save Chat** are still
   available).

**Diagnostic steps.** Ask whether the dotted-bubble button is visible on a new chat. If it is,
check Settings › Interface › **Temporary Chat by Default**. If it is not, ask an admin to confirm the
permission.

**Resolution.** For the personal setting, the person can switch it off. For the enforced permission,
explain it is an admin choice; chats made under it cannot be recovered.

**Escalation.** Account email and screenshot.

### 11.20 "Can people I share a folder with, or admins, read my chats?"

**Symptom.** A privacy question.

**Likely causes, in order.** Not a fault.

**Diagnostic steps.** None needed.

**Resolution.** Explain: everyone a folder is shared with can read **every** chat in that folder,
including chats other members put there (section 5.20); share-link recipients see the snapshot
(11.2). For admins, see section 3.4 and `users-groups-roles-and-permissions.md`, 11.15. The live
value of the admin chat access setting is TO BE CONFIRMED.

**Escalation.** Questions about whether a specific person accessed a chat need the platform
maintainer; the audit log is off by default (ground truth, Time, Storage and Logs).

### 11.21 "I can't move a chat into a folder"

**Symptom.** **Move** is missing from the chat menu, the wanted folder is not listed, or dropping a
chat on a folder does nothing or shows `We could not find what you're looking for :/`.

**Likely causes, in order.**
1. The person has no folders of their own (**Move** is hidden) or folders are off (11.5).
2. **Move** lists only the person's own folders; to put a chat in a folder shared with them, they
   must drag it there, and need **Write** access (section 5.18).
3. The chat is temporary or read-only (no Move in the top-bar menu).

**Diagnostic steps.** Ask whether the target folder is under `Shared` and whether it shows the eye
icon.

**Resolution.** Explain dragging and access levels; the folder owner can grant Write.

**Escalation.** Not normally needed.

## 12. Local Customisations

**This area matches upstream Open WebUI v0.11.4.** Read-only checks on 2026-10-07:

- `git diff main...uoft` over every path in section 13.1 (plus `src/lib/components/layout/Navbar/`,
  `src/lib/components/chat/Placeholder/` and `src/lib/utils/chatId.ts`) shows no changes.
- `git diff` (uncommitted working-tree changes) over the same paths shows no changes.
- Two files cited here from outside the scope have uncommitted changes that do not touch this
  area: `src/lib/components/chat/Chat.svelte` (five lines about resuming a reply after a tool
  approval, at `:2847-2851`) and `src/lib/i18n/locales/en-US/translation.json` (the description of
  the fork's **Hide Processing Details** setting). Line numbers in this document are those of the
  working tree.

Fork-wide changes visible here: the product name **MedIT GPT** appears in the sidebar header and in
share-page tab titles through `WEBUI_NAME` (ground truth; `src/lib/components/layout/Sidebar.svelte:1165-1173`;
`src/routes/s/[id]/+page.svelte:171-175`); the logos are the U of T ones (ground truth). Licence
comments around the "Open WebUI" name and logo strings in these files are unchanged.

## 13. Source File Index

### 13.1 Files in Scope

| File | Role |
|---|---|
| `backend/open_webui/routers/chats.py` | Chats API: lists, search, CRUD, pin, archive, share, access, tags, import, clone, fork, export, stats |
| `backend/open_webui/routers/folders.py` | Folders API: folders, shared folders, access, folder chats, read state, deletion |
| `backend/open_webui/models/chats.py` | `chat` and `chat_file` tables; search, listing, deletion, archive, tags, snapshots, history repair |
| `backend/open_webui/models/chat_messages.py` | `chat_message` table, message mirror, analytics queries |
| `backend/open_webui/models/folders.py` | `folder` table and folder queries |
| `backend/open_webui/models/tags.py` | `tag` table |
| `backend/open_webui/models/shared_chats.py` | `shared_chat` snapshot table |
| `backend/open_webui/utils/chat_id.py` | Saved, temporary and channel chat ids |
| `backend/open_webui/utils/access_control/folders.py` | Folder access with inheritance from parent folders |
| `src/lib/components/layout/Sidebar.svelte` | Sidebar sections, chat list, drag-and-drop, import by drop, folder creation |
| `src/lib/components/layout/Sidebar/ChatItem.svelte` | Chat row: unread, active, rename, generate title, clone, archive, delete, move, hover preview |
| `src/lib/components/layout/Sidebar/ChatMenu.svelte` | Sidebar chat menu, downloads (JSON, TXT, PDF) |
| `src/lib/components/layout/Sidebar/ChatHoverPreview.svelte` | Hover preview |
| `src/lib/components/layout/Sidebar/Folders.svelte` | Owned and `Shared` folder lists |
| `src/lib/components/layout/Sidebar/RecursiveFolder.svelte` | Folder row: contents, drag targets, rename, export, delete, unread badge |
| `src/lib/components/layout/Sidebar/Folders/FolderMenu.svelte` | Folder menu |
| `src/lib/components/layout/Sidebar/Folders/FolderModal.svelte` | Create and edit folder dialog |
| `src/lib/components/layout/Sidebar/Folders/FolderShareModal.svelte` | Folder sharing dialog |
| `src/lib/components/layout/Sidebar/SharedFolderItem.svelte` | Shared-folder row; imported by the sidebar but not rendered in v0.11.4 |
| `src/lib/components/layout/Sidebar/SearchInput.svelte` | Search box with filter suggestions |
| `src/lib/components/layout/Sidebar/Section.svelte` | Collapsible sidebar section, drop target |
| `src/lib/components/layout/Sidebar/PinnedModelList.svelte`, `PinnedModelItem.svelte`, `PinnedNoteList.svelte` | Pinned models and notes sections |
| `src/lib/components/layout/Sidebar/UserMenu.svelte` | Pin-to-sidebar shortcuts (rest belongs to other areas) |
| `src/lib/components/layout/Sidebar/ChannelItem.svelte`, `ChannelModal.svelte`, `UserStatusModal.svelte`, `icons/` | Not covered: channels, user status and icons belong to other areas |
| `src/lib/components/layout/ChatsModal.svelte` | Generic chat list dialog (Shared Chats, admin user chats) |
| `src/lib/components/layout/SearchModal.svelte` | Search dialog |
| `src/lib/components/layout/SharedChatsModal.svelte` | Shared Chats dialog |
| `src/lib/components/chat/ShareChatModal.svelte` | Share dialog and access panel |
| `src/lib/components/chat/Tags.svelte` | Chat tag editor (top-bar menu) |
| `src/lib/components/chat/TagChatModal.svelte` | Tag dialog; not used anywhere in v0.11.4 |
| `src/lib/components/common/ChatList.svelte` | Chat list used by the admin analytics model dialog |
| `src/routes/(app)/folders/[folderId]/+page.svelte` | Folder page |
| `src/routes/s/[id]/+page.svelte` | Share page |
| `src/lib/components/chat/Settings/ArchivedChats.svelte` | Archived Chats panel |
| `src/lib/components/chat/Settings/DataControls.svelte` | Data Controls panel |
| `src/lib/stores/chatList.ts` | Chat list paging and folder refresh bridge |
| `src/lib/apis/chats/index.ts` | Chats API client |
| `src/lib/apis/folders/index.ts` | Folders API client |

### 13.2 Files Consulted Outside Scope

| File | Why |
|---|---|
| `src/lib/components/layout/Navbar/Menu.svelte`, `src/lib/components/chat/Navbar.svelte` | Top-bar chat actions, temporary chat and Save Chat buttons |
| `src/lib/components/chat/Placeholder.svelte`, `src/lib/components/chat/Placeholder/{FolderTitle,FolderPlaceholder,ChatList}.svelte` | Folder page content |
| `src/lib/components/chat/Chat.svelte` | Archive, delete, move and save-temporary handlers; chat loading; read marker; folder background and models |
| `src/lib/components/common/{Tags,ConfirmDialog}.svelte`, `src/lib/components/common/Tags/{TagItem,TagList}.svelte` | Tag widget; default dialog text |
| `src/lib/components/workspace/common/AccessControl.svelte` | Visibility and access list behaviour |
| `src/lib/components/admin/Settings/{General,Database}.svelte`, `src/lib/components/admin/Users/Groups/Permissions.svelte`, `src/lib/components/admin/Users/UserList.svelte`, `src/lib/components/admin/Users/UserList/UserChatsModal.svelte` | Admin switches, export, permission labels, admin chat list |
| `src/lib/components/common/InterfaceSettings.svelte`, `src/lib/components/chat/Settings/Shortcuts.svelte`, `src/lib/components/chat/SettingsModal.svelte`, `src/lib/components/chat/Settings/SyncStatsModal.svelte` | Personal settings, shortcuts, Settings tabs, stats sync text |
| `src/lib/utils/index.ts`, `src/lib/utils/chatId.ts`, `src/lib/utils/settings-access.ts`, `src/lib/shortcuts.ts` | Time groups, import conversion, chat ids, permission helpers, shortcuts |
| `src/routes/(app)/+layout.svelte`, `src/routes/+layout.svelte` | Shortcut handling, sign-in redirect, stats sync opening |
| `src/lib/i18n/locales/en-US/translation.json` | Dotted-key English text |
| `backend/open_webui/main.py` | Router mounts, chat creation on first completion, `/api/config` flags, chat list events |
| `backend/open_webui/config.py`, `backend/open_webui/env.py`, `backend/open_webui/constants.py` | Defaults, switches, message constants |
| `backend/open_webui/utils/access_control/__init__.py`, `backend/open_webui/models/access_grants.py` | Share and folder access filtering |
| `backend/open_webui/events.py`, `backend/open_webui/socket/main.py`, `backend/open_webui/tasks.py` | Events, read-state socket handler, task stopping |
| `backend/open_webui/internal/db.py` | SQLite connection settings |
| `backend/open_webui/migrations/versions/c1d2e3f4a5b6_add_shared_chat_table.py` | Conversion of older share links |
| `backend/open_webui/models/feedbacks.py`, `backend/open_webui/models/automations.py`, `backend/open_webui/routers/notes.py`, `backend/open_webui/utils/subagents.py`, `backend/open_webui/utils/timers.py` | Rows and features that point at chats |
| `backend/open_webui/routers/auths.py` | Admin config keys for folders and community sharing |

## 14. Open Questions

No contradiction with `knowledgebase/tools/ground-truth.md` was found. The ground-truth statement
that deleting a user removes their chats with messages and share snapshots matches
`backend/open_webui/models/chats.py:2500-2569`.

### 14.1 Live Values and Deployment Facts (TO BE CONFIRMED)

1. Live values of `folders.enable`, `folders.max_file_count` and `ui.enable_community_sharing` in
   the `config` table.
2. Live default permissions (`user.permissions`) and group permissions for every key in section 3.2,
   especially `chat.delete`, `chat.share`, `chat.export`, `chat.import`, `chat.temporary_enforced`,
   `features.folders`, `sharing.folders`, `sharing.public_chats` and `sharing.open_chats`.
3. Production values of `ENABLE_ADMIN_CHAT_ACCESS` and `ENABLE_ADMIN_EXPORT`.
4. Whether production uses SQLite or PostgreSQL, which decides whether the declared delete cascades
   for `chat_file` and `shared_chat` are enforced (section 6.8).
5. Whether the production database contains share links created before the `shared_chat` table and
   converted to **Public** by migration `c1d2e3f4a5b6` (section 5.15).
6. Whether any event webhook or Event function is configured; this area's events carry the actor's
   name and email, and `message.updated` carries up to 300 characters of message text (section 9.4).
7. Whether database backups exist and whether restoring individual deleted chats is ever offered
   (section 11.8).
8. Request-size limits in front of the application that would affect chat imports (section 5.24).
9. The production host name (all addresses here are relative).

### 14.2 Policy Questions (TO BE CONFIRMED)

10. Whether **Community Sharing** (sending a chat to `openwebui.com`) is permitted for MedIT GPT, and
    whether the switch is on (section 5.26).
11. Whether Public and Open chat sharing, and folder sharing, should be granted to anyone.
12. Whether a chat retention or clean-up policy applies; the code has none (section 8).
13. Support contacts and escalation routes for this area. The privacy-office and Information
    Security referral points in 11.18 come from U of T guidance, not from the repository.

### 14.3 Security-Sensitive Items (Detail Withheld)

Security-sensitive: refer to the platform maintainer and U of T Information Security
(security.utoronto.ca). Each was noted during research; the detail is deliberately not recorded
here.

14. Whether share links of chats removed through **Delete folder** with contents stop working
    (sections 5.10, 5.15, 11.18).
15. The scope of access that a chat share's access list confers outside the share page (section 3.5).
16. Server-side enforcement of `chat.export`, `chat.temporary`, `chat.temporary_enforced`,
    `sharing.folders` and **Folder Max File Count** (sections 3.2, 3.3).
17. Admin access to system-created (internal) chats in relation to `ENABLE_ADMIN_CHAT_ACCESS`
    (section 3.4).

### 14.4 Behaviour Not Established from the Code Read

18. Whether a share page lets viewers switch between branches (alternative replies); the snapshot
    holds them (section 5.13), but the read-only display behaviour was not traced.
19. Whether share recipients can open files and images referenced in a snapshot; this depends on the
    file access rules in `files-uploads-and-storage.md`.
20. How the share page labels the sharer's own messages (it looks up the owner's profile for
    signed-in viewers, `src/routes/s/[id]/+page.svelte:111-116`); not traced into the message
    components.
21. Whether a spinner can remain on a chat whose reply task ended abnormally (section 11.17).
22. How faithfully the ChatGPT importer represents branched ChatGPT conversations: it builds a single
    chain in the export's key order (`src/lib/utils/index.ts:832-909`); not tested.
23. Whether live list updates reach other members of a shared folder when someone adds a chat to it.
24. The purpose of the `folder.items` column, which the folder code does not use.
25. Whether the duplicate `tags` list written into the chat JSON by the tag editor is read by any
    feature (section 6.2).
26. How the age labels such as `3d` render in every language: they rely on translation fallback for
    keys with empty English values (`src/lib/components/layout/Sidebar/ChatItem.svelte:96-101`).

### 14.5 Interface Defects and Unused Code Worth Reporting Upstream

These are recorded for the maintainer; they do not change what support should advise.

27. The share dialog says `Users with the URL will be able to view the shared chat.` although a new
    link is Private (section 5.12).
28. The **Archive All Chats** dialog says `This action cannot be undone.` although **Unarchive All**
    reverses it (section 5.7).
29. **Mark all as read** in the folder page's menu does nothing (section 5.6).
30. In Safari, **Copy Link** shows `Copied shared chat URL to clipboard!` even when no link was made
    (section 10.11).
31. Failed imports from Data Controls, failed pin changes, failed tag removals and failed folder
    sharing saves show no message (section 10.11).
32. The Shared Chats and admin user-chat dialogs pass empty-state texts (`You have no shared conversations.`, `No chats found for this user.`) that are only used in commented-out markup
    (section 5.14).
33. `SharedFolderItem.svelte` is imported by the sidebar but never rendered, and `TagChatModal.svelte`
    is not used anywhere (section 13.1).
34. Deleting a chat leaves its share access entries behind (harmless, but untidy), and **Delete All
    Chats** neither stops running replies nor tidies tag names (section 5.10).
