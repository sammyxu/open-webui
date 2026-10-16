# Notes

## At a Glance

- **What:** notes are rich-text documents (a title and a body kept as Markdown, HTML and editor
  JSON in one `note` row), opened from **Notes** in the sidebar or the user menu at `/notes`, and
  separate from chats (`backend/open_webui/models/notes.py:20-31`; section 2).
- **Who:** the admin switch `notes.enable` and the `features.notes` permission are both on in the
  code defaults; sharing needs **Notes Sharing** (`sharing.notes`, default **off**) and **Public**
  needs **Notes Public Sharing** (default off), so with the defaults only admins can share notes.
  Admins can open, edit and delete any note (section 3).
- **Saving:** there is no save button. The body is saved by the server half a second after the
  last edit, **only through the live websocket connection**; the title and attachments are saved
  separately. There is no version history, and deletion is permanent (holding **Shift** in the list
  deletes with no confirmation) (sections 5.4 and 5.13).
- **Sharing:** read or write grants to people and groups, or **Public**. A read-only share is hidden
  by the list's default **Write** filter; the recipient must choose **Read Only**. Sharing sends no
  notification (sections 3.3, 5.5 and 9).
- **Together:** people with write access edit live and see each other's named cursors; read-only
  viewers do not get live updates; across several server processes this needs the Redis websocket
  manager (section 5.9).
- **AI:** no **Enhance** button in this version. The **Chat** button opens a side chat (hidden chat
  per person per note) that can rewrite the note, with suggestions such as `Enhance this note and
  update it.`; **Generate** suggests a title. Both use the person's default model, then the admin's
  default, then the first available (sections 5.6 and 5.7). Model-side note tools are in
  [`builtin-native-tools.md`](builtin-native-tools.md).
- **Files and export:** uploaded attachments go to the file store; pasted images are kept inside the
  note row. Downloads are `.txt`, `.md` and an image-based `.pdf`, made in the browser
  (sections 5.8 and 5.10).
- **Fork:** the area matches upstream v0.11.4; only the product name in tab titles and the site icon
  differ (section 12).

## 1. Purpose and Who Uses It

**Notes** are free-standing documents that a person writes in MedIT GPT, separate from chats. Each
note has a title and a rich-text body; the body is kept in three forms at once (Markdown, HTML and
the editor's JSON document) inside one database row, the `note` table
(`backend/open_webui/models/notes.py:20-31`; `src/lib/components/notes/NoteEditor.svelte:101-115`).
A note can carry attached files and pasted images, can be pinned to the sidebar, shared with other
people or groups for reading or editing, edited by several people at the same time, downloaded as
text, Markdown or PDF, and discussed with an AI model in a side panel that can rewrite the note.

| Who | What they do with notes | Where it is decided |
|---|---|---|
| Any signed-in `user` | Create, edit, pin, export, import (`.txt`/`.md`) and delete their own notes; use the AI side chat | The instance switch `notes.enable` must be on for the interface to show Notes, and the person needs the `features.notes` permission (both code default on) (section 3) |
| A person a note is shared with | Open it read-only, or edit it when given **Write** | Access grants on the note (section 3.3) |
| Several people at once | Edit the same note live, seeing each other's cursors | The websocket collaboration channel (section 5.9) |
| Admins | Everything above for **any** note, plus the instance switch and the permissions | `backend/open_webui/routers/notes.py:273-285`; Admin Settings › General (section 7) |
| Models in ordinary chats | Search, read, create and rewrite notes through the built-in note tools | Documented in [`builtin-native-tools.md`](builtin-native-tools.md) (tools `search_notes`, `view_note`, `write_note`, `replace_note_content`) |

What notes are **not**:

- Not chats. A note's AI side chats are stored as hidden chats linked to the note (section 5.7);
  they do not appear in the chat list.
- Not knowledge bases. A note can be attached to a chat or a model as context
  ([`chat-composer-and-message-display.md`](chat-composer-and-message-display.md), section 5.6), but it
  is not indexed into the vector store by the notes code; search is a plain text match on the title
  and Markdown body (section 5.5).
- Not versioned on the server. The editor has local undo and redo only; deleting a note removes the
  row (section 5.13).

Personal data: notes are free text written by staff and may contain personal or health
information. Support staff should not ask users to paste note content into tickets; ask for the
note's address (`/notes/{id}`) and the time instead.

## 2. Navigation and URLs

All addresses are relative to the site root; the production host name is **TO BE CONFIRMED**.

### 2.1 Pages

| Address | What it shows | Source |
|---|---|---|
| `/notes` | The notes list: a **Notes** heading with the total count, a **Create** split button (**Create**, **Import txt/md**), a **Search Notes** box, three filter menus (view, permission, display) and the notes grouped by last-update period | `src/routes/(app)/notes/+page.svelte:36-52`; `src/lib/components/notes/Notes.svelte:436-554` |
| `/notes?title={title}&content={content}` | Creates a note from the query values (title defaults to today's date, `YYYY-MM-DD`) and opens it, replacing the address in the browser history | `src/routes/(app)/notes/+page.svelte:16-30` |
| `/notes/new` (optionally `?title=…&content=…`) | Creates a new note immediately and opens it; each visit creates another note | `src/routes/(app)/notes/new/+page.svelte:10-19` |
| `/notes/{id}` | The note editor for one note | `src/routes/(app)/notes/[id]/+page.svelte:20-27`; `src/lib/components/notes/NoteEditor.svelte` |

Every page under `/notes` first checks that the instance switch is on and that the person is an
admin or holds `features.notes`; otherwise it sends the browser to `/` (the home chat) without a
message (`src/routes/(app)/notes/+layout.svelte:10-19`). The browser tab title is `Notes /
{WEBUI_NAME}` on the list and `{note title, first 30 characters} / {WEBUI_NAME}` in the editor
(`src/routes/(app)/notes/+layout.svelte:29-31`; `src/lib/components/notes/NoteEditor.svelte:984-988`).

### 2.2 Ways In

| Entry point | Behaviour | Shown when | Source |
|---|---|---|---|
| Sidebar pinned item **Notes** (top of the sidebar) | Opens `/notes` | The switch and permission allow notes **and** `notes` is in the person's pinned menu items; the default pinned items are **Notes** and **Workspace** | `src/lib/components/layout/Sidebar.svelte:97`, `:155-163`, `:192`, `:1031`, `:1257` |
| User menu (click the profile picture or name) › **Notes** | Opens `/notes`; holding **Shift** shows a pin button whose tooltip is **Pin to Sidebar** or **Unpin from Sidebar** | The switch and permission allow notes | `src/lib/components/layout/Sidebar/UserMenu.svelte:55-72`, `:287-331` |
| Sidebar section **Notes** (list of pinned notes) | Each entry opens its note; the **×** button (accessible name **Unpin**) unpins it; the section's **+** button (label **New Note**) creates a note titled `New Note` and opens it; on a desktop the entries can be dragged into a new order | The switch and permission allow notes and at least one note is pinned | `src/lib/components/layout/Sidebar.svelte:1312-1328`; `src/lib/components/layout/Sidebar/PinnedNoteList.svelte:27-100` |
| Search dialog action **Create a new note** | Opens `/notes/new?content={search text}`, so the typed search text becomes the new note's body | The switch and permission allow notes | `src/lib/components/layout/SearchModal.svelte:524-541` |
| A link to `/notes/{id}` inside a chat answer | Shown as a **Note** card and opened inside the app | In chat answers; the rendering rules are in `chat-composer-and-message-display.md` | `src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens/NoteLinkToken.svelte` |
| Chat **+** menu › **Attach Notes** | Attaches a note to a chat message as context (not documented here) | `notes.enable` on | `chat-composer-and-message-display.md` section 5.6 |

The search dialog does not search note contents; only the notes list does (section 5.5).

### 2.3 Back-End Endpoints

The router is mounted at `/api/v1/notes` (`backend/open_webui/main.py:862`). Every endpoint needs a
signed-in, non-pending account (`get_verified_user`) and, for non-admins, the `features.notes`
permission (for example `backend/open_webui/routers/notes.py:71-77`).

| Method and path | Purpose | Extra check | Source |
|---|---|---|---|
| `GET /api/v1/notes/` | Notes the person can read, newest first; 60 per page when `page` is given; body text cut to 1,000 characters | none | `backend/open_webui/routers/notes.py:64-105` |
| `GET /api/v1/notes/pinned` | The person's pinned notes (sidebar) | none | `backend/open_webui/routers/notes.py:113-145` |
| `GET /api/v1/notes/search` | The notes list page: `query`, `view_option`, `permission`, `order_by`, `direction`, `page` (60 per page) | none | `backend/open_webui/routers/notes.py:148-198` |
| `POST /api/v1/notes/create` | Create a note | Grants the person may not make are removed (section 3.4) | `backend/open_webui/routers/notes.py:206-242` |
| `GET /api/v1/notes/{id}` | One note in full, with `write_access` and `is_pinned` | Owner, admin, or a read grant | `backend/open_webui/routers/notes.py:254-304` |
| `GET /api/v1/notes/{id}/chat` | Get (or create) the person's AI side chat for the note | Owner, admin, or a read grant | `backend/open_webui/routers/notes.py:307-395` |
| `GET /api/v1/notes/{id}/chats` | All of the person's side chats for the note | Owner, admin, or a read grant | `backend/open_webui/routers/notes.py:398-453` |
| `POST /api/v1/notes/{id}/chat` | Create a new side chat for the note | Owner, admin, or a read grant | `backend/open_webui/routers/notes.py:456-517` |
| `POST /api/v1/notes/{id}/update` | Save title, files or other data | Owner, admin, or a write grant | `backend/open_webui/routers/notes.py:525-594` |
| `POST /api/v1/notes/{id}/access/update` | Replace the note's sharing | Owner, admin, or a write grant | `backend/open_webui/routers/notes.py:606-657` |
| `POST /api/v1/notes/{id}/pin` | Pin or unpin (toggle) for the calling person only | Owner, admin, or a read grant | `backend/open_webui/routers/notes.py:665-706` |
| `DELETE /api/v1/notes/{id}/delete` | Delete the note | Owner, admin, or a write grant | `backend/open_webui/routers/notes.py:714-756` |

The front-end client for these is `src/lib/apis/notes/index.ts` (one function per endpoint, lines
11-474). There is **no export endpoint**: downloads are produced in the browser (section 5.10).
Live editing does not use these endpoints for the note body; it goes over the websocket (section
5.9).

## 3. Roles and Permissions

Roles are `admin`, `user` and `pending` (ground truth). Pending accounts cannot reach any notes
endpoint, because every endpoint requires `get_verified_user` (`backend/open_webui/routers/notes.py:68`
and the same dependency on every route). The rest of this section is about `user` and `admin`.

### 3.1 The Instance Switch and the Feature Permission

Two controls decide whether a person has notes at all. Both are on in the code defaults; the live
values are data and **TO BE CONFIRMED** for production.

| Control | Where an admin sets it | Code default | What it governs | Source |
|---|---|---|---|---|
| Instance switch `notes.enable` (environment seed `ENABLE_NOTES`) | Admin Settings › General › **Notes** ("Allow users to create and manage notes.") | on | Whether the interface offers Notes to anyone: the sidebar item, the user-menu row, the pinned-notes section, the search-dialog action, the `/notes` pages, the chat **Attach Notes** entry, and the note tools offered to models in chats | `backend/open_webui/config.py:2050`, `:3118`; `backend/open_webui/main.py:2359`; `src/lib/components/admin/Settings/General.svelte:335-341`; `src/lib/i18n/locales/en-US/translation.json:2398-2399`; `backend/open_webui/utils/tools.py:719` |
| Feature permission `features.notes` (environment seed `USER_PERMISSIONS_FEATURES_NOTES`) | Admin Panel › Users › Groups › **Default permissions** or a group › **Features Permissions** › **Notes** | on | Whether a non-admin may use notes. The interface hides the same entry points, and **every** notes endpoint refuses a non-admin without it with HTTP 401 `401 Unauthorized` | `backend/open_webui/config.py:1920`, `:2004`; `src/lib/components/admin/Users/Groups/Permissions.svelte:960`, `:978-992`; `backend/open_webui/routers/notes.py:71-77` |

How they combine in the interface: an entry point is shown when the switch is on **and** the person
is an admin or holds `features.notes` (for example `src/lib/components/layout/Sidebar.svelte:157-163`;
`src/routes/(app)/notes/+layout.svelte:11-19`). The interface treats a missing permission value as
granted (`?? true`). Permissions add up across groups, and a group cannot take away a permission the
defaults grant (ground truth); the editor says so under the switch: `This is a default user
permission and will remain enabled.` (`src/lib/components/admin/Users/Groups/Permissions.svelte:985-990`).

Points to note:

- **Admins skip the permission** on every notes endpoint (`user.role != 'admin'`,
  `backend/open_webui/routers/notes.py:71`), but the interface still hides notes from admins when the
  instance switch is off (`src/routes/(app)/notes/+layout.svelte:13`).
- **The switch is not a delete.** Turning `notes.enable` off removes the feature from view; the code
  path for the switch does not touch the `note` table. The server-side check on the notes endpoints
  is the `features.notes` permission (`backend/open_webui/routers/notes.py:71-77`); to stop a group of
  people using notes, the permission is the control that the notes router reads. Whether the switch
  is meant to block the endpoints too is listed in section 14.
- **Changes reach an open browser on reload.** The interface uses the permission object and settings
  loaded when the app starts (`src/routes/+layout.svelte:1279-1292`), so someone whose permission was
  just changed should reload the page (see `users-groups-roles-and-permissions.md`, section 3.5).
- The note tools for models (`search_notes` and the others) need the switch, the person's
  `features.notes` permission and the model's built-in tools capability; a note's own side chat gets
  them regardless (`backend/open_webui/utils/tools.py:717-721`; detailed in `builtin-native-tools.md`).

### 3.2 What Each Kind of Access Allows

A note has one owner (`note.user_id`, the creator). Everyone else reaches it through an access grant
(section 3.3) or the admin role.

| Action | Owner | Admin | Write grant | Read grant (including **Public**) | Source |
|---|---|---|---|---|---|
| See it in the notes list | Yes | Yes; with `BYPASS_ADMIN_ACCESS_CONTROL` on, an admin's list contains **every user's** notes | Only with the list's permission menu on **Write** (the default) | Only with the permission menu on **Read Only** (section 5.5) | `backend/open_webui/routers/notes.py:186-193`; `backend/open_webui/models/notes.py:238-249`; `backend/open_webui/models/access_grants.py:744-745`, `:832-934` |
| Open it at `/notes/{id}` | Yes | Yes | Yes | Yes | `backend/open_webui/routers/notes.py:273-285` |
| Edit the body (live) | Yes | Yes | Yes | No; the editor is not editable and the header shows `Read-Only Access` | `src/lib/components/notes/NoteEditor.svelte:1383`, `:1268-1272`; `backend/open_webui/socket/main.py:829-840` |
| Rename (title box) and **Generate** a title | Yes | Yes | No; the title box and its button are disabled | No | `src/lib/components/notes/NoteEditor.svelte:1069-1070`, `:1095-1096` |
| Undo and redo buttons | Yes | Yes | Yes | Not shown | `src/lib/components/notes/NoteEditor.svelte:1116-1144` |
| **Upload files**, remove attachments, **Record** audio | Yes | Yes | Yes | Not shown | `src/lib/components/notes/NoteEditor.svelte:1157-1216`, `:1345` |
| Open the AI side chat (**Chat** button) | Yes | Yes | Yes | Yes (their own side chats) | `src/lib/components/notes/NoteEditor.svelte:1146-1155`; `backend/open_webui/routers/notes.py:327-337` |
| **Insert into note** from a side-chat answer | Yes | Yes | Yes | No | `src/lib/components/notes/NoteEditor.svelte:1510` |
| Open the sharing dialog | Yes | Yes | The button is shown but disabled | Not shown (the `Read-Only Access` label appears instead) | `src/lib/components/notes/NoteEditor.svelte:1259-1272` |
| Pin or unpin (only for themselves) | Yes | Yes | Yes | Yes | `backend/open_webui/routers/notes.py:684-696` |
| **Download** (txt, md, pdf), **Copy link**, **Copy to clipboard** | Yes | Yes | Yes | Yes | `src/lib/components/notes/NoteEditor.svelte:1213-1243` |
| **Delete** | Yes | Yes | Yes: the server accepts a delete from anyone with write access | The menu item is shown, but the server refuses with HTTP 403 | `backend/open_webui/routers/notes.py:733-743`; `src/lib/components/notes/Notes/NoteMenu.svelte:171-179` |

Admins pass every ownership and grant check in the notes router and the collaboration handlers
(`backend/open_webui/routers/notes.py:273`, `:287-289`; `backend/open_webui/socket/main.py:538-541`,
`:672-674`). No setting narrows this for notes: the router imports `ENABLE_ADMIN_CHAT_ACCESS` and
`ENABLE_ADMIN_EXPORT` but does not use them, and `BYPASS_ADMIN_ACCESS_CONTROL` affects only the
list (`backend/open_webui/routers/notes.py:6-10`, `:186`).

Opening, editing or deleting another person's note as an admin is access to that person's
content, which may include personal or health information.

### 3.3 Access Grants on a Note

Sharing is stored as rows in the shared `access_grant` table with `resource_type` `note`
(`backend/open_webui/models/notes.py:140-141`; `backend/open_webui/models/access_grants.py:33`).
The sharing dialog (`Access Control`) is the shared workspace component, opened from the note's
access button with the roles **Read** and **Write** available
(`src/lib/components/notes/NoteEditor.svelte:991-1011`; its general behaviour is described in
`users-groups-roles-and-permissions.md`).

| Grant (principal, permission) | Shown in the dialog as | Effect | Source |
|---|---|---|---|
| a user, `read` | That person in the **Access List** with **Read** | They can open the note read-only | `src/lib/components/workspace/common/AccessControl.svelte:644-690` |
| a user, `read` and `write` | That person with **Write** | Choosing **Write** adds both a read and a write grant; switching back to **Read** removes only the write grant | `src/lib/components/workspace/common/AccessControl.svelte:312-325` |
| a group, `read` / `write` | The group, with its member count, and **Read** or **Write** | Every member of the group | `src/lib/components/workspace/common/AccessControl.svelte:590-630` |
| `user` `*`, `read` | Visibility **Public** ("Accessible to all users") | Every signed-in user who has notes can open it, and it appears in everyone else's **Read Only** list | `src/lib/components/workspace/common/AccessControl.svelte:223-236`, `:541-548`; `backend/open_webui/models/access_grants.py:840-843` |
| `user` `*`, `write` | **Allow public write access** switch (only while Public) | Every signed-in user who has notes can edit it, and it appears in everyone's default (**Write**) list | `src/lib/components/workspace/common/AccessControl.svelte:247-262`, `:553-565`; `backend/open_webui/routers/notes.py:297` |
| none | Visibility **Private** and `No access grants. Private to you.` | Only the owner and admins | `src/lib/components/workspace/common/AccessControl.svelte:531`, `:700` |

The **Open** visibility ("Anyone with the link can view") is not offered for notes: the note editor
does not pass the option, and the server removes any such grant when saving
(`src/lib/components/notes/NoteEditor.svelte:992-1000`;
`src/lib/components/workspace/common/AccessControlModal.svelte:23`;
`backend/open_webui/utils/access_control/__init__.py:239-251`).

### 3.4 Who May Share, and What the Server Keeps

| Permission | Label in the permissions editor | Code default | Effect | Source |
|---|---|---|---|---|
| `sharing.notes` | **Notes Sharing** (Sharing Permissions) | off | Shows the **Access List** and **Add Access** in a note's sharing dialog | `backend/open_webui/config.py:1828`, `:1967`; `src/lib/components/admin/Users/Groups/Permissions.svelte:425-439`; `src/lib/components/notes/NoteEditor.svelte:996`; `src/lib/components/workspace/common/AccessControl.svelte:568-585` |
| `sharing.public_notes` | **Notes Public Sharing** (shown only while Notes Sharing is on) | off | Offers **Public** in the visibility menu; without it the menu shows only **Private** and the tooltip `You do not have permission to make this public` | `backend/open_webui/config.py:1830-1832`, `:1968`; `src/lib/components/admin/Users/Groups/Permissions.svelte:441-460`; `src/lib/components/workspace/common/AccessControl.svelte:518-534` |
| `access_grants.allow_users` | (Sharing Permissions) | on | Lets the person add individual users | `backend/open_webui/config.py:1841-1843`, `:1975`; `src/lib/components/notes/NoteEditor.svelte:998` |
| `access_grants.allow_groups` | (Sharing Permissions) | on | Lets the person add groups | `backend/open_webui/config.py:1844-1846`, `:1976`; `src/lib/components/notes/NoteEditor.svelte:999-1000` |

Admins have all four in the interface regardless (`src/lib/components/notes/NoteEditor.svelte:996-1000`).
With the code defaults, therefore, an ordinary user's note can be shared only by an admin: the
**Notes Sharing** permission is off. Whether production grants it is **TO BE CONFIRMED**.

When sharing is saved (on creation, on update and from the dialog), the server quietly drops grants
the saver may not make: public grants without `sharing.public_notes`, individual-user grants without
`access_grants.allow_users`, group grants without `access_grants.allow_groups`, and any "anyone with
the link" grant. No error is returned; the dialog still shows `Saved`
(`backend/open_webui/routers/notes.py:221-228`, `:557-565`, `:638-646`;
`backend/open_webui/utils/access_control/__init__.py:223-301`;
`src/lib/components/notes/NoteEditor.svelte:1001-1010`). The dialog keeps showing what the person
chose until the note is reloaded, because the editor does not read back the saved grants.

## 4. Key Concepts and Terminology

| Term | Meaning in this application | Source |
|---|---|---|
| **Note** | One row in the `note` table: an id, the owner's user id, a title, a `data` object holding the body and attachments, an unused `meta` object, and created and updated times | `backend/open_webui/models/notes.py:20-31` |
| **Owner** | The person who created the note (`user_id`). Ownership never changes in the notes code | `backend/open_webui/models/notes.py:171-178` |
| **Title** | Free text. A note made from the notes page is titled with the date (`YYYY-MM-DD`); one made from the sidebar's **+** is titled `New Note`; one imported from a file takes the file name without `.md` or `.txt`. A blank title is saved as `Untitled` | `src/lib/components/notes/Notes.svelte:449-455`, `:141-145`; `src/lib/components/layout/Sidebar.svelte:1318-1323`; `src/lib/components/notes/NoteEditor.svelte:212` |
| **Body** (`data.content`) | Stored three ways: `md` (Markdown), `html`, and `json` (the editor's document). Search, the list preview, the `.txt` and `.md` downloads and the AI tools use `md`; the PDF uses `html`; the editor opens from `json`, falling back to `html`, then to Markdown converted to HTML (or from the live shared document when someone is already editing, section 5.9) | `src/lib/components/notes/NoteEditor.svelte:101-115`, `:172-175`, `:794-808`; `backend/open_webui/models/notes.py:34-57` |
| **Attachments** (`data.files`) | The list of files and images attached to the note, kept inside the note row. Files go to the file store; pasted or dropped images are kept inline as data addresses (section 5.8) | `src/lib/components/notes/NoteEditor.svelte:490-664` |
| **Versions** (`data.versions`) | A list of earlier body snapshots that the editor adds to in the browser when a side-chat answer is inserted. The editor's saves never send it, so it is not kept on the server, and the code that browsed versions is switched off in the undo and redo buttons | `src/lib/components/notes/NoteEditor.svelte:346-359`, `:872-875`, `:1122-1136`, `:210-218` |
| **Formatting** | The **Formatting** switch in the note's menu. On: Markdown typed or pasted becomes formatting (for example `# ` makes a heading) and links are detected. Off: Markdown characters stay as typed and pasting inserts plain text. Turning it off or on keeps existing formatting. It is not saved; it resets to on whenever a note is opened | `src/lib/components/notes/Notes/NoteMenu.svelte:50-66`; `src/lib/components/common/RichTextInput.svelte:811`, `:1040-1060`, `:1326-1327`; `src/lib/components/notes/NoteEditor.svelte:98`, `:177-178` |
| **Formatting buttons** | Select text, or place the cursor on an empty line, to get a small toolbar: **H1**, **H2**, **H3**, **Lift List**, **Sink List**, **Bullet List**, **Ordered List**, **Task List**, **Bold**, **Italic**, **Underline**, **Strikethrough**, **Code Block**, **Emoji** | `src/lib/components/common/RichTextInput.svelte:896-944`; `src/lib/components/common/RichTextInput/FormattingButtons.svelte:31-199` |
| **Write access** | The `write_access` flag the server returns with a note: true for the owner, an admin, a write grant or a public write grant. It switches the editor between editable and read-only | `backend/open_webui/routers/notes.py:287-298`; `src/lib/components/notes/NoteEditor.svelte:1383` |
| **Read-Only Access** | The label shown in the note header instead of the share button when the person cannot edit | `src/lib/components/notes/NoteEditor.svelte:1268-1272` |
| **Public** | Sharing with every signed-in user (an access grant for user `*`); **Allow public write access** lets all of them edit | section 3.3 |
| **Pinned note** | A note the person has pinned; it appears in the sidebar's **Notes** section. Pins are per person (`pinned_note` table); pinning a shared note does not pin it for anyone else | `backend/open_webui/models/notes.py:82-88`, `:369-394` |
| **Pinned menu item Notes** | The **Notes** shortcut at the top of the sidebar, separate from pinned notes. It is one of the person's pinned menu items (saved in their settings as `pinnedMenuItems`) | `src/lib/components/layout/Sidebar.svelte:97`, `:155`; `src/lib/components/layout/Sidebar/UserMenu.svelte:63-72` |
| **AI side chat** (note chat) | A chat panel opened with the note's **Chat** button. Each one is a hidden chat stored in the `chat` table with internal metadata linking it to the note; it is not listed among ordinary chats. Each person has their own side chats for a note | `backend/open_webui/routers/notes.py:339-395`; `src/lib/components/notes/NoteEditor.svelte:687-792`, `:1497-1538` |
| **Suggested prompts** | The four starters offered in an empty side chat: `Enhance this note and update it.`, `Summarize this note.`, `Extract action items from this note.`, `Rewrite the selected text.` | `src/lib/components/notes/NoteEditor.svelte:153-158`; `src/lib/components/chat/Chat.svelte:4510-4530` |
| **Insert into note** | A button on a finished side-chat answer that inserts the answer at the cursor in the note (people with write access only) | `src/lib/components/chat/Messages/ResponseMessage.svelte:972-986`; `src/lib/components/notes/NoteEditor.svelte:872-875`, `:1510` |
| **Generate** (title) | The sparkle button beside the title box: asks a model for a 2-4 word title from the note's Markdown | `src/lib/components/notes/NoteEditor.svelte:361-433`, `:1087-1113` |
| **Record**, **Capture Audio**, **Upload Audio** | The microphone menu: record from the microphone, capture audio from a shared screen or tab, or pick an audio file. The result is uploaded as an attachment | `src/lib/components/notes/RecordMenu.svelte:32-71`; `src/lib/components/notes/NoteEditor.svelte:1157-1211`, `:1470-1495` |
| **Live collaboration** | Several people editing the same note at once. Their browsers exchange edits through the server over the websocket using a shared document per note (`note:{id}`) and show each other's cursors with names | `src/lib/components/common/RichTextInput/Collaboration.ts:41-315`; `backend/open_webui/socket/main.py:655-940` |
| **Shared document** | The server's working copy of a note being edited, kept as a list of edits in memory, or in Redis when the websocket manager is Redis. It is discarded when the last editor leaves; the note row in the database is the lasting copy | `backend/open_webui/socket/utils.py:241-394`; `backend/open_webui/socket/main.py:194-197`, `:910-912` |
| **Note event** (`events:note`) | A websocket message telling everyone viewing a note that its title, attachments or body changed outside live typing (a save, or an AI rewrite) | `backend/open_webui/routers/notes.py:578-582`; `backend/open_webui/tools/builtin.py:94-95`; `src/lib/components/notes/NoteEditor.svelte:877-928` |
| **Time groups** | The list's headings: `Today`, `Yesterday`, `Previous 7 days`, `Previous 30 days`, then month names for this year and years before that, by last update | `src/lib/utils/index.ts:1308-1337`; `src/lib/components/notes/Notes.svelte:251-274`, `:604-607` |
| **Deleted User** | Shown as the owner's name on a list entry whose owner's account no longer exists | `src/lib/components/notes/Notes.svelte:645-653`, `:816-825` |

Timestamps on notes are whole numbers of **nanoseconds** since 1970 (`time.time_ns()`), unlike, for
example, the access-grant rows, which use seconds (`backend/open_webui/models/access_grants.py:472`);
the interface divides by 1,000,000 or 1,000,000,000 to display them
(`backend/open_webui/models/notes.py:176-177`, `:364`, `:387`;
`src/lib/components/notes/NoteEditor.svelte:1293-1310`; `src/lib/components/notes/Notes.svelte:261`).
When reading a note's times in an export or the database, divide by 1,000,000,000 to get seconds.

Words a user may use for the same things: "notebook" or "document" (a note), "share link" (the
**Copy link** address, which only works for people the note is shared with, section 5.11),
"autosave" (section 5.4), "AI assistant" or "enhance" (the side chat, section 5.7).

## 5. Workflows (Step by Step)

### 5.1 Opening the Notes List

1. Click **Notes** at the top of the sidebar, or open the user menu and choose **Notes**
   (section 2.2). The browser goes to `/notes`.
2. The page asks the server for the first 60 notes (`GET /api/v1/notes/search`) and shows them
   grouped under time headings (`Today`, `Yesterday`, `Previous 7 days`, and so on), newest update
   first. The number beside the **Notes** heading is the total that matches the current filters
   (`src/lib/components/notes/Notes.svelte:209-249`, `:436-442`; `backend/open_webui/routers/notes.py:168-172`).
3. Scrolling to the bottom loads the next 60, showing `Loading...` meanwhile
   (`src/lib/components/notes/Notes.svelte:841-856`).
4. With nothing to show, the page reads `No Notes` and `Create your first note from the Create menu.`
   (`src/lib/components/notes/Notes.svelte:859-870`). The same empty page appears when the list
   request fails, because the page discards the error (`src/lib/components/notes/Notes.svelte:216-226`).

Each list row shows the title, the time since the last update (hover for the full date), the
owner's name (hover for their email address, or `Deleted User`), and a **⋯** menu with the
accessible name `Note Menu` (`src/lib/components/notes/Notes.svelte:613-722`).

### 5.2 Creating a Note

Every way of creating a note writes the row straight away, before anything is typed, so abandoned
attempts leave empty notes behind.

| Way | Steps | Resulting title and body | Source |
|---|---|---|---|
| **Create** on the notes page | `/notes` › **Create** | Title is today's date (`YYYY-MM-DD`); empty body; the editor opens | `src/lib/components/notes/Notes.svelte:445-457`; `src/lib/components/notes/utils.ts:110-132` |
| Sidebar **+** | The **+** on the sidebar's **Notes** section (label **New Note**; the section exists only while a note is pinned) | Title `New Note`; empty body | `src/lib/components/layout/Sidebar.svelte:1312-1324` |
| Address | Open `/notes/new` or `/notes?title=…&content=…` | The `title` value or today's date; the `content` value as the body | `src/routes/(app)/notes/new/+page.svelte:10-19`; `src/routes/(app)/notes/+page.svelte:16-30` |
| Search dialog | Type in the search dialog, choose **Create a new note** | Today's date; the typed text as the body | `src/lib/components/layout/SearchModal.svelte:530-537` |
| **Import txt/md** | `/notes` › the arrow beside **Create** (accessible name `Open create menu`) › **Import txt/md**, pick one or more `.txt` or `.md` files; or drag such files onto the notes page | One note per file; title is the file name without the extension; body is the file's text, with Markdown converted for display | `src/lib/components/notes/Notes.svelte:127-168`, `:378-399`, `:458-462`; `src/lib/components/common/SplitCreateButton.svelte:77-79` |
| A model in an ordinary chat | The model calls `write_note` | A private note owned by the person; see `builtin-native-tools.md` | `backend/open_webui/tools/builtin.py:1286-1332` |

When a body arrives through an address or the search dialog, the same text is stored as both the
Markdown and the HTML body (`src/lib/components/notes/utils.ts:115-120`); how Markdown in such a
link displays is listed in section 14.

Import details:

- Only `.txt` and `.md` files are accepted. On the first other file the page shows
  `Only txt and md files are allowed` and stops; files after it are not imported
  (`src/lib/components/notes/Notes.svelte:130-139`).
- After choosing files with the picker, `Imported notes successfully` appears once the import stops,
  even when a file was refused or a note could not be created (each failure also shows its own
  message) (`src/lib/components/notes/Notes.svelte:386-398`, `:144-158`).
- Imported notes are private (no access grants) (`src/lib/components/notes/Notes.svelte:144-154`).

### 5.3 Writing and Formatting

1. Click in the body (placeholder `Write something...`) and type
   (`src/lib/components/notes/NoteEditor.svelte:1382`).
2. With **Formatting** on (the default), Markdown typed as you go becomes formatting, and pasted
   Markdown or rich text keeps its formatting. With it off, characters stay as typed and pastes are
   plain text (section 4; `src/lib/components/common/RichTextInput.svelte:1040-1060`, `:1326-1327`).
3. Select text to get the formatting toolbar, or put the cursor on an empty line to get the same
   buttons (section 4).
4. List items have drag handles for reordering, and web addresses become links
   (`src/lib/components/notes/NoteEditor.svelte:1378-1379`;
   `src/lib/components/common/RichTextInput.svelte:811`).
5. The header row shows the note's **created** date (for example `[Today at] h:mm A` rendered as
   "Today at 2:05 PM", or `DD/MM/YYYY` for older notes) and running counts `{COUNT} words` and
   `{COUNT} characters` (`src/lib/components/notes/NoteEditor.svelte:1290-1327`).
6. **Undo** and **Redo** arrows sit in the header for people who can edit; the keyboard shortcuts
   Ctrl or Cmd+Z, Ctrl or Cmd+Y and Ctrl or Cmd+Shift+Z work in the editor
   (`src/lib/components/notes/NoteEditor.svelte:1116-1144`;
   `src/lib/components/common/RichTextInput/Collaboration.ts:78-83`).

People with read access see the same body but cannot place edits; the editor shows a "not allowed"
cursor (`src/lib/components/common/RichTextInput.svelte:1425-1429`).

### 5.4 How Saving Works (Autosave)

There is no **Save** button and no "saved" indicator in the editor. Two separate mechanisms save
different parts of a note.

| What | How it is saved | When | Source |
|---|---|---|---|
| The body (text, formatting, and where images sit in the text) | Each edit is sent over the websocket together with a copy of the whole body (Markdown, HTML and JSON). The server waits half a second after the last such message for that note, then writes the body into the note row, provided the sender may edit the note | Continuously while typing, at save time on the server, 0.5 s after the last edit | `src/lib/components/common/RichTextInput/Collaboration.ts:235-257`; `backend/open_webui/socket/main.py:842-880`, `:735-758` |
| The merged body after someone else's edit | When a remote edit arrives, the receiving browser sends its own merged copy of the body half a second later, so the stored body includes everyone's changes | 0.5 s after the last remote edit | `src/lib/components/common/RichTextInput/Collaboration.ts:118-128`, `:153-168` |
| Title and attachment list | `POST /api/v1/notes/{id}/update` with the title and `data.files` only (not the body) | 0.2 s after leaving the title box, after a generated title, after adding or removing an attachment, and when leaving the page with such a save pending | `src/lib/components/notes/NoteEditor.svelte:210-248`, `:1075-1084`, `:555-565`, `:1351-1358` |
| Sharing | `POST /api/v1/notes/{id}/access/update` | Each change in the sharing dialog (section 5.11) | `src/lib/components/notes/NoteEditor.svelte:1001-1010` |
| Pin | `POST /api/v1/notes/{id}/pin` | Each pin or unpin (section 5.12) | `src/lib/components/notes/NoteEditor.svelte:1248-1252` |

Consequences for support:

- **The body is saved only through the live-editing connection.** If the websocket is down, typing
  continues in the browser but nothing reaches the database. The app shows
  `Connection lost. Reconnecting...` after a short delay and `Reconnected` when it is back
  (`src/routes/+layout.svelte:147-164`, `:184-196`). Edits made while disconnected are not sent at
  the time they are made (`src/lib/components/common/RichTextInput/Collaboration.ts:236`); what
  happens to them on reconnection is described in section 5.9.
- **Closing the tab right after typing is normally safe**, because each edit is sent immediately and
  the half-second wait happens on the server (`backend/open_webui/socket/main.py:865-880`).
- **The updated time** in the list changes only when a save actually changed something
  (`backend/open_webui/models/notes.py:358-366`).
- **Not saved anywhere:** the **Formatting** switch (resets to on), and the local `versions` list
  (section 4).
- The title box sends whatever title the browser holds. A blank title is stored as `Untitled`
  (`src/lib/components/notes/NoteEditor.svelte:212`).

### 5.5 Finding Notes: Search, Filters and Sorting

| Control | Options | Behaviour | Remembered | Source |
|---|---|---|---|---|
| **Search Notes** box | free text | Runs 0.3 s after typing stops. Every word must appear in the title or the Markdown body (in any order); upper and lower case are treated alike; hyphens are ignored in both the words and the notes, and spaces are ignored inside the notes, so `todo` finds "to-do" and "to do". The **×** clears it | No | `src/lib/components/notes/Notes.svelte:190-197`, `:475-494`; `backend/open_webui/models/notes.py:212-230` |
| View menu | `All`, `Created by you`, `Shared with you` | All notes the person can reach; only their own; only other people's | Yes, in this browser | `src/lib/components/notes/Notes.svelte:509-524`; `backend/open_webui/models/notes.py:232-236` |
| Permission menu (with **All** or **Shared with you**) | `Write` (default), `Read Only` | **Write** lists notes the person owns or can edit. **Read Only** lists notes shared with them for reading only, including notes made **Public**; it leaves out notes they own | No | `src/lib/components/notes/Notes.svelte:526-535`; `backend/open_webui/models/notes.py:238-249`; `backend/open_webui/models/access_grants.py:744-745`, `:832-934` |
| Display menu | `List`, `Grid` | Grid cards show up to three lines of the body (from a 1,000-character preview) or `No content` | Yes, in this browser | `src/lib/components/notes/Notes.svelte:537-551`, `:725-838`; `backend/open_webui/routers/notes.py:42-46` |
| Column headers (list view) | `Title`, `Updated at` | Click to sort; click again to reverse. **Updated at** starts newest first, **Title** A to Z | No | `src/lib/components/notes/Notes.svelte:276-283`, `:562-602`; `backend/open_webui/models/notes.py:251-270` |

Because **Write** is the default, **a note shared with someone for reading only does not appear in
their list until they choose Read Only** in the permission menu. This is the most likely
explanation when a person says a shared note is missing (section 11.3).

Admins: with `BYPASS_ADMIN_ACCESS_CONTROL` on (environment, code default on), the server applies no
sharing filter to an admin's list, so **All** shows every user's notes and **Shared with you**
shows every note owned by someone else (`backend/open_webui/routers/notes.py:186-193`;
`backend/open_webui/models/access_grants.py:747-781`; `backend/open_webui/config.py:2086-2092`).

The search covers only the notes list. The app-wide search dialog does not search notes
(section 2.2), and models search notes with their own tool (`search_notes`, see
`builtin-native-tools.md`).

### 5.6 Renaming a Note and Generating a Title

1. Click the title box at the top of the note (placeholder `Title`) and type
   (`src/lib/components/notes/NoteEditor.svelte:1062-1085`).
2. Click elsewhere. The title is saved 0.2 s later, or when leaving the page (section 5.4).
3. To have a model suggest a title, click in the title box and then the sparkle button (tooltip
   `Generate`). The box empties and shows `Generating...` while a model reads the note's Markdown
   with a built-in prompt asking for a 2-4 word title as JSON
   (`src/lib/components/notes/NoteEditor.svelte:361-433`, `:1087-1113`).
4. When the reply contains a title, it replaces the old one and is saved. When the reply has no
   usable title, the old title comes back; when the reply cannot be read, `Failed to generate title`
   appears (`src/lib/components/notes/NoteEditor.svelte:404-432`).

Which model writes the title: the first of the person's default models (Settings), otherwise the
first of the admin's default models, otherwise the first model in the person's model list; a model
that is hidden or not available to the person is skipped (`src/lib/components/notes/NoteEditor.svelte:930-954`).
The request goes to `POST /api/chat/completions` without streaming
(`src/lib/components/notes/NoteEditor.svelte:390-403`; `src/lib/apis/openai/index.ts:421-451`).

If the request itself fails (for example the model is unreachable or no model is available), the
code does not catch the error: no message appears, the title box stays empty and disabled showing
`Generating...`, and nothing is saved, so reloading the page brings back the stored title
(`src/lib/components/notes/NoteEditor.svelte:386-403`; `src/lib/apis/openai/index.ts:441-448`).

Only the owner and admins can rename or generate a title (section 3.2).

### 5.7 AI Assistance: the Note's Side Chat

There is no separate **Enhance** button in this version. AI help in a note comes from the side chat
(and the title generator, section 5.6). A small menu with **Enhance** and **Chat** items exists in
the code (`src/lib/components/notes/AIMenu.svelte:31-56`) but nothing in the application uses it.

1. In the note, click the speech-bubble button (tooltip and accessible name `Chat`)
   (`src/lib/components/notes/NoteEditor.svelte:1146-1155`). On a screen at least 1,000 pixels wide
   the chat opens as a resizable panel on the right (at least 350 pixels wide); on smaller screens
   as a drawer (`src/lib/components/notes/NotePanel.svelte:17-57`).
2. The first time, the server creates a hidden chat for this person and this note, titled `Chat`,
   with a fixed instruction telling the model the note's id and that, for requests such as "make
   this concise, rewrite, enhance, shorten, or update", it should call `view_note` and then
   `replace_note_content`, and not claim an edit is done unless that call succeeds. Later openings
   reuse the person's most recently updated side chat for the note
   (`backend/open_webui/routers/notes.py:339-395`; `backend/open_webui/models/chats.py:602-617`).
3. An empty side chat lists `Suggested prompts`: `Enhance this note and update it.`,
   `Summarize this note.`, `Extract action items from this note.` and `Rewrite the selected text.`
   Clicking one sends it at once (`src/lib/components/notes/NoteEditor.svelte:153-158`;
   `src/lib/components/chat/Chat.svelte:4510-4530`).
4. Text selected in the note when a message is sent is added to the message under the line
   `Selected note text for replace_note_content operations:` so the model can target it
   (`src/lib/components/chat/Chat.svelte:781-784`, `:4498`, `:4525`, `:4589`, `:4641`).
5. The note's attached files (not its images) are added to the side chat's context automatically
   (`backend/open_webui/utils/middleware.py:2784-2807`). The note tools are offered in a note's side
   chat even when the model's built-in tools are off (`backend/open_webui/utils/middleware.py:2809-2813`;
   `backend/open_webui/utils/tools.py:717-721`).
6. When the model rewrites the note (`replace_note_content`, write access required), the server
   saves the new Markdown and tells every open copy of the note to refresh. An editor that is
   being typed in waits until 0.8 s after the last keystroke before applying it
   (`backend/open_webui/tools/builtin.py:1335-1500`, `:94-102`;
   `src/lib/components/notes/NoteEditor.svelte:250-336`, `:877-928`). The rewrite replaces the
   stored body with Markdown only (the HTML and JSON forms are cleared)
   (`backend/open_webui/tools/builtin.py:1470-1485`). Details of the tool, its limits and its
   messages are in `builtin-native-tools.md`.
7. **Insert into note** on a finished answer inserts the answer at the cursor (write access only)
   (`src/lib/components/notes/NoteEditor.svelte:872-875`, `:1510`;
   `src/lib/components/chat/Messages/ResponseMessage.svelte:972-986`).
8. The panel header shows the chat title as a button (accessible name `Chat history`). Its menu
   offers `New chat` (once the open chat has messages), the person's side chats for this note (the
   open one marked `Current`), and for each a `More Options` button (tooltip `More`) with `Delete`.
   With no chats it reads `No chat history`. Delete acts without asking for confirmation
   (`src/lib/components/chat/EmbeddedChatHistoryDropdown.svelte:36-98`;
   `src/lib/components/chat/EmbeddedChatHistoryItem.svelte:30-95`).
9. A **New chat** is only a draft until its first message is sent; the server creates the hidden chat
   then (`src/lib/components/notes/NoteEditor.svelte:725-759`;
   `src/lib/components/chat/Chat.svelte:3305-3323`).
10. Close the panel with the **×** (tooltip `Close`) (`src/lib/components/chat/Chat.svelte:4312-4321`).

Which model answers: the side chat uses the normal chat composer, including its model selector. A
new side chat starts with no model, so the composer chooses the person's default models
(Settings), otherwise the admin's default models, otherwise the first model in the person's list,
skipping hidden or unavailable models (`backend/open_webui/routers/notes.py:373`;
`src/lib/components/chat/Chat.svelte:200-222`, `:2311-2332`;
`src/lib/components/chat/MessageInput.svelte:2577-2584`). Answers, failures and the composer are
documented in `chat-composer-and-message-display.md` and
`chat-completion-pipeline-and-generation-tasks.md`.

Side chats are ordinary rows in the `chat` table marked internal (`meta.internal`, `meta.type`
`note`, `meta.note_id`) and owned by the person who chatted. They are excluded from the chat list,
chat search and other chat listings (`backend/open_webui/routers/notes.py:388`;
`backend/open_webui/models/chats.py:1488-1501` (chat list), `:1963-2019` (chat search)).
Other people who can open the note do not see someone else's side chats (`backend/open_webui/models/chats.py:619-633`). Deleting a side chat
needs the `chat.delete` permission for non-admins; without it the server answers with the
`ACCESS_PROHIBITED` text (`backend/open_webui/routers/chats.py:1577-1585`).

### 5.8 Attachments and Images

| Item | How to add it | Where it is stored | Limits and checks | Source |
|---|---|---|---|---|
| A file (the picker does not restrict the type; the server's upload rules apply) | Note menu **⋯** › **Upload files** (several at once), or drop it into the note body | Uploaded to the file store through `POST /api/v1/files/` (text extraction and indexing as for any upload); the note's `data.files` list keeps an entry with the file's id, name, size, collection name, status and a copy of the file record as returned at upload | `File size should not exceed {maxSize} MB.` when larger than the admin's maximum upload size; `You cannot upload an empty file.` for a zero-byte file; any warning from processing appears as a warning toast | `src/lib/components/notes/NoteEditor.svelte:490-568`, `:606-628`, `:673-685`, `:1409-1429`; `files-uploads-and-storage.md` |
| Audio | Microphone menu (tooltip `Record`): `Record` (microphone), `Capture Audio` (audio from a shared screen or tab), `Upload Audio` (an audio file) | Uploaded as a file attachment, as above. The recording is attached, not transcribed into the note (`transcribe={false}`) | `Permission denied when accessing microphone: {error}` or `Permission denied when accessing microphone` when the browser refuses; `Error accessing media devices.` or `Error starting recording.` from the recorder | `src/lib/components/notes/RecordMenu.svelte:32-71`; `src/lib/components/notes/NoteEditor.svelte:1157-1211`, `:1470-1495`; `src/lib/components/chat/MessageInput/VoiceRecording.svelte:207-237`, `:290-297` |
| An image | Paste it into the body, or drop it on the body | **Not uploaded.** The picture is read in the browser, optionally shrunk, and kept inside the note row as a data address in `data.files` (type `image`); the body holds a reference `data://{id}` to it | Shrunk when the person's image-compression setting or the admin's image width or height limit applies; HEIC photos are converted to JPEG; the admin's maximum upload size applies | `src/lib/components/notes/NoteEditor.svelte:570-660`, `:1415-1455`; `src/lib/components/common/RichTextInput/Image/image.ts:120-168` |

How attachments appear and are removed:

- Files (not images) show as small cards above the body; people with write access can remove one
  with its dismiss button, which saves the attachment list 0.2 s later
  (`src/lib/components/notes/NoteEditor.svelte:150-152`, `:1336-1362`).
- Images show inside the body. An image whose entry is missing from the attachment list shows the
  placeholder `/image-placeholder.png`; an image whose address is on another website is not loaded
  and shows the site icon instead (`src/lib/components/common/RichTextInput/Image/image.ts:136-146`;
  `src/lib/utils/safeImageUrl.ts:22-37`).
- Removing an attachment from a note, or deleting the note, does not delete the uploaded file from
  the file store; the notes code has no such call (`src/lib/components/notes/NoteEditor.svelte:1351-1358`;
  `backend/open_webui/models/notes.py:420-429`).
- Dragging files over the note does not show the drop overlay: the handlers that would show it are
  commented out (`src/lib/components/notes/NoteEditor.svelte:956-960`), although drops into the body
  still work through the editor (`:1408-1429`).

Pasted images are kept inside the note row, so notes with many or large images make the row, each
opening of the note and each title or attachment save larger (the notes list itself carries only a
1,000-character text preview, `backend/open_webui/routers/notes.py:42-46`). Whether collaborators
can open a note's uploaded files is TO BE CONFIRMED (no file-access rule covers notes; see
`files-uploads-and-storage.md`, section 3.5, and section 14 here).

### 5.9 Editing Together (Live Collaboration)

What people see:

1. Two or more people with write access open the same note. Each person's cursor and selection
   appear in the others' editors labelled with their name, in a colour picked at random from ten
   (`src/lib/components/common/RichTextInput/Collaboration.ts:18-32`, `:130-149`, `:86-87`).
2. Typing appears in the other editors as it happens; edits merge rather than overwrite each other.
3. People with read-only access do **not** join the live session: the live connection is started
   only for an editable editor (`src/lib/components/common/RichTextInput.svelte:801-805`). They see
   the body as it was when they opened the note, plus title, attachment and AI-rewrite updates
   (section 4, "Note event"). Reloading the page shows the latest saved body.

How it works:

| Step | What happens | Source |
|---|---|---|
| Open | The editor loads the note over HTTP, then joins the note's room for note events (`join-note`, read access checked) | `src/lib/components/notes/NoteEditor.svelte:177-206`; `backend/open_webui/socket/main.py:519-552` |
| Join the shared document | The editor sends `ydoc:document:join` for `note:{id}`; the server checks read access, adds the session, and sends back the current shared document (`ydoc:document:state`) and the list of sessions in it; others get `ydoc:user:joined` | `src/lib/components/common/RichTextInput/Collaboration.ts:130-149`; `backend/open_webui/socket/main.py:655-732` |
| First editor | If the server has no shared document yet, the session whose id sorts first fills it from the note's stored body; others wait for it | `src/lib/components/common/RichTextInput/Collaboration.ts:171-205` |
| Each edit | `ydoc:document:update` with the change and a copy of the whole body; the server checks write access, appends the change to the shared document, forwards it to the other sessions, and schedules the database save (section 5.4) | `src/lib/components/common/RichTextInput/Collaboration.ts:235-257`; `backend/open_webui/socket/main.py:802-883` |
| Cursors | `ydoc:awareness:update`, forwarded only within the document's room with the sender's identity attached by the server | `src/lib/components/common/RichTextInput/Collaboration.ts:259-276`; `backend/open_webui/socket/main.py:918-940` |
| Leave | Leaving the page sends `ydoc:document:leave`; when the last session leaves (or disconnects), the server discards the shared document. The database row remains the lasting copy | `src/lib/components/common/RichTextInput/Collaboration.ts:293-314`; `backend/open_webui/socket/main.py:886-915`, `:943-957` |
| Size | The shared document is compacted after 500 stored changes (the older half merged into one) | `backend/open_webui/socket/utils.py:242`, `:254-294` |

When the connection drops: the editor stops sending (`isConnected` false) and keeps the edits
locally; the app shows `Connection lost. Reconnecting...`. On reconnection the editor rejoins
the shared document (`src/lib/components/common/RichTextInput/Collaboration.ts:283-291`;
`src/routes/+layout.svelte:147-164`, `:184-196`). If the server no longer holds the shared document
(for example the person was alone and their session ended), the editor sends its whole copy back,
but that resend carries no body copy, so the database is updated only by the next edit
(`src/lib/components/common/RichTextInput/Collaboration.ts:189-200`;
`backend/open_webui/socket/main.py:869-880`). If the shared document still exists because others
are in it, the editor merges the server's copy into its own; the code does not resend the edits
made while disconnected as separate changes. Exactly what other editors see in that case is
TO BE CONFIRMED by testing (section 14). Practical advice: after `Reconnected`, type one more
character (or reload and check) before closing a note that was edited while offline.

More than one server process: the shared document and the rooms live in each process's memory
unless the websocket manager is Redis (`WEBSOCKET_MANAGER=redis`), in which case both are shared
through Redis (`backend/open_webui/socket/main.py:89-125`, `:133-141`, `:194-197`;
`backend/open_webui/socket/utils.py:254-268`). Without it, two people whose connections land on
different processes do not see each other's typing or cursors, each process saves the body it
received, and the later save wins. The production websocket and Redis configuration is
**TO BE CONFIRMED**; see `websockets-realtime-and-redis.md`.

### 5.10 Exporting and Copying

From the note's **⋯** menu (or a row's **⋯** menu on the notes list):

| Item | What it produces | Notes | Source |
|---|---|---|---|
| **Download** › `Plain text (.txt)` | A `.txt` file named after the title, containing the Markdown body | Formatting characters (such as `#` or `**`) appear as typed | `src/lib/components/notes/Notes/NoteMenu.svelte:67-83`; `src/lib/components/notes/NoteEditor.svelte:796-798` |
| **Download** › `Plain text (.md)` | A `.md` file with the same Markdown body | | `src/lib/components/notes/Notes/NoteMenu.svelte:85-92`; `src/lib/components/notes/NoteEditor.svelte:799-801` |
| **Download** › `PDF document (.pdf)` | An A4 PDF made in the browser: the title, then the body rendered as a picture (JPEG at 70% quality), split across pages | The text in the PDF is an image, so it cannot be selected or searched; in dark mode the pages have a black background | `src/lib/components/notes/utils.ts:6-108` |
| **Share** › **Copy link** | Copies `{site}/notes/{id}` | Works only for people who can open the note (section 5.11) | `src/lib/components/notes/NoteEditor.svelte:1220-1229`; `src/lib/components/notes/Notes.svelte:681-690` |
| **Share** › **Copy to clipboard** | Copies the body as rich text with a plain-text alternative | Editor only | `src/lib/components/notes/NoteEditor.svelte:1230-1243` |

From the list, downloads fetch the full note first, because the list holds only a 1,000-character
preview (`src/lib/components/notes/Notes.svelte:91-113`). Downloads are generated in the browser;
nothing is recorded on the server. Images placed in a note are stored as references
(`data://{id}`) in the Markdown and HTML (section 5.8), so the downloaded files do not contain the
pictures themselves; whether the PDF shows them is TO BE CONFIRMED (section 14). There is no bulk
export of all notes in the notes screens.

### 5.11 Sharing a Note

Only the owner or an admin can change sharing in the interface, and only people with the sharing
permissions see the options (section 3.4).

1. Open the note and click the access button at the right of the header (shown to people with write
   access; enabled only for the owner and admins) (`src/lib/components/notes/NoteEditor.svelte:1259-1267`).
2. The `Access Control` dialog opens (`src/lib/components/workspace/common/AccessControlModal.svelte:30-59`).
3. Visibility menu: `Private` (`Only select users and groups with permission can access`) or, with
   **Notes Public Sharing**, `Public` (`Accessible to all users`). While **Public** is chosen, the
   `Allow public write access` switch lets every signed-in user edit
   (`src/lib/components/workspace/common/AccessControl.svelte:517-565`).
4. With **Notes Sharing**, the `Access List` shows who has access; **Add Access** opens a picker of
   users and groups, and **Add** grants them **Read**. Change a person or group to **Write** with
   the menu beside them (accessible name `Access level`), or remove them
   (`src/lib/components/workspace/common/AccessControl.svelte:40`, `:355-370`, `:568-700`;
   `src/lib/components/workspace/common/AddAccessModal.svelte:30-75`).
5. Every change is saved immediately and confirmed with `Saved`; there is no separate save button
   (`src/lib/components/notes/NoteEditor.svelte:1001-1010`).
6. Tell the people concerned. Sharing a note sends no notification (section 9); recipients find it in
   their notes list (a **Read** share only under **Read Only**, section 5.5) or through the link from
   **Share** › **Copy link** (section 5.10).

A person opening a link to a note they cannot reach sees the server's message (for example
`Something went wrong :/` when they have no access) and is taken to the home page
(`src/lib/components/notes/NoteEditor.svelte:180-203`; `backend/open_webui/routers/notes.py:273-285`).

### 5.12 Pinning and Unpinning

1. In the note's **⋯** menu (editor or list) choose `Pin to Sidebar`; on a pinned note the item reads
   `Unpin` (`src/lib/components/notes/Notes/NoteMenu.svelte:153-169`).
2. The note appears in the sidebar's **Notes** section, newest pin first, until the person drags the
   entries into their own order (desktop only); the order is saved in their settings as
   `pinnedNotesOrder`, and notes pinned after that go to the end
   (`backend/open_webui/models/notes.py:406-411`;
   `src/lib/components/layout/Sidebar/PinnedNoteList.svelte:16-53`).
3. The **×** on a sidebar entry unpins it (`src/lib/components/layout/Sidebar/PinnedNoteList.svelte:88-98`).

Pins belong to the person, not the note: pinning a shared note affects only the person who pinned
it, and anyone who can read a note may pin it (`backend/open_webui/models/notes.py:369-394`;
`backend/open_webui/routers/notes.py:684-696`). A pinned note that the person can no longer read
drops out of their sidebar, because the pinned list is filtered by access
(`backend/open_webui/models/notes.py:396-418`). Hiding the **Notes** shortcut at the top of the
sidebar is a different thing (section 2.2).

### 5.13 Deleting a Note

| Where | Steps | Confirmation | Messages | Source |
|---|---|---|---|---|
| Editor | **⋯** › **Delete** › confirm | Dialog `Delete note?` with `This will delete {title}.` | `Note deleted successfully`, then the notes list opens; on failure the server's message and `Failed to delete note` | `src/lib/components/notes/NoteEditor.svelte:811-824`, `:1016-1027`, `:1244-1246` |
| Notes list | Row **⋯** › **Delete** › confirm | Same dialog | No success message; the list reloads. On failure the server's message | `src/lib/components/notes/Notes.svelte:115-125`, `:401-412`, `:691-694` |
| Notes list, holding **Shift** | Hold Shift; each row's **⋯** becomes a bin button (tooltip `Delete`); click it | **None**: the note is deleted at once | As above | `src/lib/components/notes/Notes.svelte:328-347`, `:658-672`, `:746-760` |

What deletion does: it removes the note's access grants (saved first), then everyone's pins of it
and the `note` row itself (`backend/open_webui/models/access_grants.py:388-403`). There is no bin,
archive or soft delete in the notes code, so the note cannot be restored from the interface
(`backend/open_webui/models/notes.py:420-429`). Left behind:
the uploaded files that were attached (section 5.8) and the hidden side chats about the note, which
nothing deletes or lists afterwards (`backend/open_webui/routers/notes.py:714-756`;
`backend/open_webui/models/chats.py:602-633`). Recovery from a database backup, if backups exist,
is TO BE CONFIRMED.

Who can delete: the owner, an admin, or **anyone with write access** (section 3.2). The **Delete**
item is shown to read-only viewers too; the server refuses them
(`backend/open_webui/routers/notes.py:733-743`). Deleting a user account does not delete that
person's notes (ground truth); they remain, listed with `Deleted User` as owner where others can
still see them.

### 5.14 Notes Elsewhere in the Application

| Feature | What it does with notes | Documented in |
|---|---|---|
| Chat **+** › **Attach Notes** | Attaches a note to a chat message as context | `chat-composer-and-message-display.md`, section 5.6 |
| Dragging a pinned note from the sidebar into the chat composer | Adds the note as a reference in the message (the composer fetches the note's title first) | `src/lib/components/chat/MessageInput.svelte:1285-1297`; `chat-composer-and-message-display.md` |
| Links to `/notes/{id}` in answers | Shown as a **Note** card | `chat-composer-and-message-display.md`, section 5.15 |
| Note tools for models | `search_notes`, `view_note`, `write_note`, `replace_note_content` | `builtin-native-tools.md` |
| Notes attached to models or folders as knowledge | Offered to the model through the knowledge tools | `builtin-native-tools.md`; `knowledge-bases.md` |
| Folder files | A folder can list a note among its files; the note entry is shown only to people who can read the note | `backend/open_webui/utils/access_control/files.py:105-158` |

The composer also contains a "create a note from the message box" function that nothing calls in
this version, so its message `Cannot create an empty note.` cannot appear
(`src/lib/components/chat/MessageInput.svelte:1199-1216`).

### 5.15 Admin Tasks

| Task | Where | Effect | Source |
|---|---|---|---|
| Turn notes on or off for everyone | Admin Settings › General › **Notes** (`/admin/settings/general`) | Section 3.1; saved with the General panel's save | `src/lib/components/admin/Settings/General.svelte:335-341`; `backend/open_webui/routers/auths.py:130`, `:1235` |
| Allow or block notes for a group, or by default | Admin Panel › Users › Groups › a group or **Default permissions** › **Features Permissions** › **Notes** | Section 3.1 | `src/lib/components/admin/Users/Groups/Permissions.svelte:960-992` |
| Allow sharing | Same place › **Sharing Permissions** › **Notes Sharing** and **Notes Public Sharing** | Section 3.4 | `src/lib/components/admin/Users/Groups/Permissions.svelte:235`, `:425-460` |
| Open or fix someone's note | Open `/notes/{id}`; admins pass every access check | Section 3.2. This is access to personal content | `backend/open_webui/routers/notes.py:273-298` |

There is no admin screen that lists notes separately; with `BYPASS_ADMIN_ACCESS_CONTROL` on, an
admin's own **Notes** page lists everyone's notes (section 5.5).

## 6. Data Model

Support staff do not query the database (tier 1 is read-only and the database holds personal and
possibly health information). This section explains what is stored where so that escalations can
name the right records.

### 6.1 Table `note`

| Column | Type | Meaning | Source |
|---|---|---|---|
| `id` | text, primary key | A random UUID; it is the `{id}` in `/notes/{id}` | `backend/open_webui/models/notes.py:23`, `:173` |
| `user_id` | text | The owner's user id (not a foreign key; the row survives the user's deletion) | `backend/open_webui/models/notes.py:24` |
| `title` | text | The title | `backend/open_webui/models/notes.py:26` |
| `data` | JSON | Body and attachments (section 6.2) | `backend/open_webui/models/notes.py:27` |
| `meta` | JSON | Not used by the notes screens (sent as `null` when a note is created) | `backend/open_webui/models/notes.py:28`; `src/lib/components/notes/utils.ts:122` |
| `created_at`, `updated_at` | big integer | Nanoseconds since 1970. `updated_at` moves only when a save changes something | `backend/open_webui/models/notes.py:30-31`, `:176-177`, `:358-366` |

There is no index on `note` beyond the primary key in the models or migrations, and searching
compares text in the title and the Markdown body directly
(`backend/open_webui/models/notes.py:20-31`, `:212-230`).

### 6.2 The `data` Object

| Key | Contents | Written by | Source |
|---|---|---|---|
| `content.md` | Markdown version of the body | Live editing (each editor sends it); imports; AI tools | `src/lib/components/common/RichTextInput.svelte:963-993`; `backend/open_webui/tools/builtin.py:1312`, `:1470-1479` |
| `content.html` | HTML version of the body | Live editing; imports; cleared to empty by an AI rewrite | as above |
| `content.json` | The editor's document | Live editing; `null` for imported notes and after an AI rewrite | as above |
| `files` | List of attachments or `null`. File entries: `type` `file`, `id`, `name`, `size`, `url` (the file id), `collection_name`, `status`, `error`, a copy of the file record (`file`). Image entries: `type` `image`, `id`, and `url` holding the picture as a data address | Title-and-attachments saves | `src/lib/components/notes/NoteEditor.svelte:490-564`, `:630-650` |
| `versions` | Earlier snapshots; created in the browser but not sent by the editor's saves | Not normally present | `src/lib/components/notes/NoteEditor.svelte:101-111`, `:346-359` |

A save merges keys at the top level: saving `files` keeps `content`, and a body save replaces the
whole `content` object (`backend/open_webui/models/notes.py:353-354`). If stored `data` is
malformed, the server repairs it on read: a non-object becomes the Markdown text, and a Markdown
value that is a list or object is turned into a fenced JSON block
(`backend/open_webui/models/notes.py:34-57`, `:76-79`).

### 6.3 Related Tables and Stores

| Store | What it holds for notes | Key columns | Deletion | Source |
|---|---|---|---|---|
| `pinned_note` | One row per person per pinned note | `id`, `user_id`, `note_id` (foreign key to `note.id`, cascade on delete), `created_at` (nanoseconds); unique on (`user_id`, `note_id`) in the migration | Removed with the note | `backend/open_webui/models/notes.py:82-88`; `backend/open_webui/migrations/versions/4de81c2a3af1_add_pinned_note_table.py:34-43` |
| `access_grant` | Sharing rows with `resource_type` `note` | `resource_id` (note id), `principal_type` (`user` or `group`), `principal_id` (user id, group id, or `*` for everyone), `permission` (`read` or `write`), `created_at` (seconds) | Removed with the note | `backend/open_webui/models/access_grants.py:25-45`, `:443-478`; `backend/open_webui/models/notes.py:423` |
| `chat` | The side chats: ordinary chat rows with `meta` `{"internal": true, "type": "note", "note_id": …}`, owned by the person who chatted | `user_id`, `meta.note_id` | **Not** removed with the note | `backend/open_webui/routers/notes.py:388`, `:510`; `backend/open_webui/models/chats.py:602-633` |
| `file` and the file store | Uploaded (non-image) attachments, owned by the uploader | `file.id` = the attachment's `id` | **Not** removed with the note | `src/lib/components/notes/NoteEditor.svelte:525-545`; `files-uploads-and-storage.md` |
| `user.settings` (`ui`) | `pinnedMenuItems` (whether the **Notes** shortcut is in the sidebar) and `pinnedNotesOrder` | per user | With the user | `src/lib/components/layout/Sidebar/UserMenu.svelte:63-72`; `src/lib/components/layout/Sidebar/PinnedNoteList.svelte:42-51` |
| Browser storage | `noteViewOption`, `noteDisplayOption` (list view and display choices) | per browser | Cleared with browser data | `src/lib/components/notes/Notes.svelte:317-319`, `:517-523`, `:544-550` |
| Shared document (memory or Redis) | The live-editing copy: a list of changes and the sessions in it, under `{REDIS_KEY_PREFIX}:ydoc:documents:note_{id}:…` in Redis (prefix default `open-webui`) | — | Discarded when the last session leaves | `backend/open_webui/socket/utils.py:17`, `:241-394`; `backend/open_webui/env.py:384` |

### 6.4 Migration History

| Revision | Date in file | Change | Source |
|---|---|---|---|
| `9f0c9cd09105` | 2025-05-03 | Creates `note` with `id`, `user_id`, `title`, `data`, `meta`, `access_control` (JSON), `created_at`, `updated_at` | `backend/open_webui/migrations/versions/9f0c9cd09105_add_note_table.py:18-34` |
| `f1e2d3c4b5a6` | 2026-02-05 | Creates `access_grant`, copies each note's `access_control` JSON into grant rows, then drops `note.access_control` | `backend/open_webui/migrations/versions/f1e2d3c4b5a6_add_access_grant_table.py:28-60`, `:62-75`, `:215-223` |
| `e1f2a3b4c5d6` | 2026-04-14 | Adds `note.is_pinned` | `backend/open_webui/migrations/versions/e1f2a3b4c5d6_add_is_pinned_to_note.py:12-28` |
| `4de81c2a3af1` | 2026-05-09 | Creates `pinned_note`, turns each `is_pinned` note into a pin for its owner, drops `note.is_pinned` | `backend/open_webui/migrations/versions/4de81c2a3af1_add_pinned_note_table.py:26-75` |

The `is_pinned` value in API responses is computed per person from `pinned_note`
(`backend/open_webui/routers/notes.py:92-98`, `:300-303`).

### 6.5 Personal Data

A note's title, body and attachments are free text and files chosen by staff, and can hold personal
or health information. Owner names and email addresses are shown to everyone who can see a note in
the list (`src/lib/components/notes/Notes.svelte:645-653`). Side chats copy note text into chat
messages. Event webhooks receive note titles with the acting person's name and email (section 9).
Treat all of these as personal data; do not ask users to send note content in tickets.

## 7. Settings and Configuration

Persistent settings are rows in the `config` table; after first boot the stored value wins over the
environment variable (ground truth). Every live value below is data and **TO BE CONFIRMED** for
production.

### 7.1 Persistent Settings

| Key | Seeded from | Code default | Admin location | Effect on notes | Source |
|---|---|---|---|---|---|
| `notes.enable` | `ENABLE_NOTES` | `True` | Admin Settings › General › **Notes** | Section 3.1 | `backend/open_webui/config.py:2050`, `:3118`; `backend/open_webui/routers/auths.py:130`, `:1235`; `src/lib/components/admin/Settings/General.svelte:335-341` |
| `user.permissions` › `features.notes` | `USER_PERMISSIONS_FEATURES_NOTES` | `True` | Admin Panel › Users › Groups › **Default permissions** (and per group) › **Notes** | Section 3.1 | `backend/open_webui/config.py:1920`, `:2004`, `:3101` |
| `user.permissions` › `sharing.notes` | `USER_PERMISSIONS_NOTES_ALLOW_SHARING` | `False` | … › **Notes Sharing** | Section 3.4 | `backend/open_webui/config.py:1828`, `:1967` |
| `user.permissions` › `sharing.public_notes` | `USER_PERMISSIONS_NOTES_ALLOW_PUBLIC_SHARING` | `False` | … › **Notes Public Sharing** | Section 3.4 | `backend/open_webui/config.py:1830-1832`, `:1968` |
| `user.permissions` › `access_grants.allow_users`, `access_grants.allow_groups` | `USER_PERMISSIONS_ACCESS_GRANTS_ALLOW_USERS`, `…_ALLOW_GROUPS` | `True` | Sharing permissions | Section 3.4 | `backend/open_webui/config.py:1841-1846`, `:1974-1977` |
| `rag.file.max_size` | `RAG_FILE_MAX_SIZE` | none (no limit in the editor) | Admin Settings › Documents › Files › **Max Upload Size** (see `files-uploads-and-storage.md`) | Largest attachment or image, in MB | `backend/open_webui/config.py:983`, `:2907`; `backend/open_webui/main.py:2414`; `src/lib/components/notes/NoteEditor.svelte:614-628` |
| `file.image_compression_width`, `file.image_compression_height` | `FILE_IMAGE_COMPRESSION_WIDTH`, `…_HEIGHT` | none | Admin Settings › Documents › Files › **Image Compression Width** / **Image Compression Height** | Upper bound for pasted images | `backend/open_webui/config.py:989-995`, `:2908-2909`; `backend/open_webui/main.py:2416-2419`; `src/lib/components/notes/NoteEditor.svelte:570-604` |
| `ui.default_models` | `DEFAULT_MODELS` | none | Admin Settings › Models (see `workspace-models-and-model-access.md`) | Fallback model for the title generator and side chat | `backend/open_webui/config.py:1674`, `:3087`; `backend/open_webui/main.py:2394`; `src/lib/components/admin/Settings/Models.svelte:273`, `:337`; `src/lib/components/notes/NoteEditor.svelte:933-937` |

There is no other `notes.*` key: `DEFAULT_CONFIG` contains only `notes.enable` in that namespace
(`backend/open_webui/config.py:3118`). There is no setting for a size limit on notes, a maximum
number of notes, a retention period, the list's page size (60, fixed in code,
`backend/open_webui/routers/notes.py:82`, `:171`), or the save delay (0.5 s, fixed in code,
`backend/open_webui/socket/main.py:866`).

### 7.2 Environment-Only Settings That Affect Notes

| Variable | Code default | Effect on notes | Source |
|---|---|---|---|
| `BYPASS_ADMIN_ACCESS_CONTROL` | on | Admins' notes list shows every user's notes (section 5.5) | `backend/open_webui/config.py:2086-2092`; `backend/open_webui/routers/notes.py:186` |
| `WEBSOCKET_MANAGER` | empty (not Redis) | `redis` shares live-editing rooms and shared documents between server processes (section 5.9) | `backend/open_webui/env.py:476`; `backend/open_webui/socket/main.py:89-125`, `:133-141` |
| `WEBSOCKET_REDIS_URL` | `REDIS_URL` | The Redis used when the websocket manager is Redis | `backend/open_webui/env.py:493` |
| `ENABLE_WEBSOCKET_SUPPORT` | on | Websocket transport (on) or long-polling only (off) for the connection that carries live editing | `backend/open_webui/env.py:473`; `backend/open_webui/socket/main.py:102-103`; `src/routes/+layout.svelte:173` |
| `REDIS_KEY_PREFIX` | `open-webui` | Prefix of the shared-document keys in Redis | `backend/open_webui/env.py:384`; `backend/open_webui/socket/utils.py:17` |

### 7.3 Per-Person Settings

| Setting | Where the person sets it | Effect | Source |
|---|---|---|---|
| Default model(s) | Model selector › `Set as default` (stored as `models` in their settings) (`src/lib/components/chat/ModelSelector/Selector.svelte:1270`) | First choice for the title generator and side chats | `src/lib/components/notes/NoteEditor.svelte:933-934`; `src/lib/components/chat/Chat.svelte:211-213` |
| Image compression and size | Settings › Interface | Shrinks images pasted into notes | `src/lib/components/common/InterfaceSettings.svelte:88-93`; `src/lib/components/notes/NoteEditor.svelte:570-604` |
| Speech-to-text language | Settings › Audio | Sent with audio attachments for transcription by the file processing | `src/lib/components/notes/NoteEditor.svelte:513-525` |
| Sidebar shortcut **Notes** | User menu with **Shift** held: `Pin to Sidebar` / `Unpin from Sidebar` | Section 2.2 | `src/lib/components/layout/Sidebar/UserMenu.svelte:311-329` |
| Pinned notes order | Drag in the sidebar | Section 5.12 | `src/lib/components/layout/Sidebar/PinnedNoteList.svelte:42-51` |
| List view and display | Notes list menus | Remembered in the browser only | `src/lib/components/notes/Notes.svelte:317-319` |

## 8. Cron Jobs and Background Processes

No scheduled job touches notes; there is no crontab and no notes loop among the startup loops
(ground truth; `knowledgebase/tools/inventory.md`). Nothing cleans up empty notes, orphaned side
chats or the files of deleted notes.

What runs without a click, all at save time:

| Process | Trigger | What it does | Single process versus Redis | Source |
|---|---|---|---|---|
| Delayed body save | Each `ydoc:document:update` that carries a body copy | Cancels the note's pending save, then starts a task that waits 0.5 s and writes the body to the `note` row (if the sender may still edit) | The task runs in the process that received the edit. With the Redis websocket manager the task is also registered in Redis and cancellation reaches every process | `backend/open_webui/socket/main.py:865-880`, `:735-758`; `backend/open_webui/tasks.py:157-178`, `:259-309`, `:28-66` |
| Pending-save cancel on AI rewrite | `replace_note_content` | Stops any pending body save for the note so the rewrite is not overwritten | As above | `backend/open_webui/tools/builtin.py:1465-1468` |
| Shared-document compaction | The 500th stored change for a note | Merges the older half of the changes into one | Memory or Redis | `backend/open_webui/socket/utils.py:242`, `:254-294` |
| Shared-document clean-up | Last session leaves or disconnects | Deletes the shared document | Memory or Redis | `backend/open_webui/socket/main.py:886-915`, `:943-957`; `backend/open_webui/socket/utils.py:354-394` |
| Event delivery | Create, update, sharing change, pin, unpin, delete (section 9) | Sends the event to admin-installed event functions and event webhooks as background tasks | Per process | `backend/open_webui/events.py:1062-1086`, `:1166-1171`, `:1198-1202` |

Background loops listed in the inventory that indirectly matter: the session-pool clean-up removes
sessions that missed heartbeats, and a websocket disconnect removes the session from every shared
document (`backend/open_webui/socket/main.py:212`, `:943-957`).

## 9. Notifications and Emails

- **No email.** The application sends none (ground truth).
- **No in-app or browser notification for notes.** Sharing a note, editing a shared note or deleting
  one notifies nobody: note events are not in the list of events that produce notifications
  (`backend/open_webui/events.py:669-675`, `:1083-1086`).
- **Pop-up messages (toasts)** in the notes screens are listed in section 10.

Websocket messages (not visible as messages; they update open screens):

| Event | Sent to | When | Effect | Source |
|---|---|---|---|---|
| `events:note` | Everyone who opened the note (room `note:{id}`) | A title or attachment save through the API; an AI rewrite | Open editors take the new title, attachments, sharing or body | `backend/open_webui/routers/notes.py:572-582`; `backend/open_webui/tools/builtin.py:94-95`; `src/lib/components/notes/NoteEditor.svelte:877-928` |
| `ydoc:document:state` | The joining session | On joining or on request | Loads the shared document | `backend/open_webui/socket/main.py:704-713`, `:761-799` |
| `ydoc:document:update` | The other editors | Each edit | Applies the edit | `backend/open_webui/socket/main.py:852-863` |
| `ydoc:awareness:update` | The other editors | Cursor or selection moves | Shows cursors and names | `backend/open_webui/socket/main.py:918-940` |
| `ydoc:user:joined`, `ydoc:user:left` | The other editors | Join, leave | Sent, but the note editor does not listen for them | `backend/open_webui/socket/main.py:715-726`, `:903-908`; `src/lib/components/common/RichTextInput/Collaboration.ts:151-232` |
| `error` with `Failed to join document` | The joining session | Joining fails with an exception | The note editor does not listen for it; nothing is shown | `backend/open_webui/socket/main.py:730-732` |

Event bus (for admin-configured event webhooks and event functions):

| Event name | Description in the catalogue | Raised by | Extra data | Source |
|---|---|---|---|---|
| `note.created` | `A note was created.` | Creating through the API (not the `write_note` tool) | title | `backend/open_webui/events.py:317-318`; `backend/open_webui/routers/notes.py:232-238` |
| `note.updated` | `A note was updated.` | Title or attachment saves; AI rewrites. Live typing saves do **not** raise it | title | `backend/open_webui/events.py:320-321`; `backend/open_webui/routers/notes.py:584-590`; `backend/open_webui/tools/builtin.py:96-102`; `backend/open_webui/socket/main.py:735-758` |
| `note.access_updated` | `Note access was updated.` | Sharing changes in the dialog | none | `backend/open_webui/events.py:323-324`; `backend/open_webui/routers/notes.py:651-656` |
| `note.pinned`, `note.unpinned` | `A note was pinned.`, `A note was unpinned.` | Pin toggles | none | `backend/open_webui/events.py:326-330`; `backend/open_webui/routers/notes.py:699-705` |
| `note.deleted` | `A note was deleted.` | Deletion | none | `backend/open_webui/events.py:332-333`; `backend/open_webui/routers/notes.py:747-752` |

Each event carries the acting person's id, name, email and role
(`backend/open_webui/events.py:704`, `:974-985`), so webhook receivers get personal data. Whether
production has any event webhooks or event functions configured is **TO BE CONFIRMED**; see
`notifications-webhooks-events-and-banners.md`.

## 10. Error, Warning and Notice Messages (Verbatim)

Plain translation keys display as written (the `en-US` file leaves them empty or identical; checked
for every key below in `src/lib/i18n/locales/en-US/translation.json`). The only dotted keys in this
area are the admin switch's label and description, quoted in section 3.1. Placeholders use the
source's variable names. Back-end texts reach the user through the front end's `toast.error` of the
server's `detail` (for example `src/lib/components/notes/NoteEditor.svelte:180-183`).

### 10.1 Notes Screens (Front End)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Only txt and md files are allowed` | Error | `src/lib/components/notes/Notes.svelte:137` | Importing (picker or drop) a file that is not `.txt` or `.md`; the import stops there | Convert the file to `.txt` or `.md` | None |
| `Imported notes successfully` | Success | `src/lib/components/notes/Notes.svelte:391` | The picker import finished, even if a file was refused or failed | Check that each note appears | If notes are missing, look for the error shown before it |
| `Copied link to clipboard` | Success | `src/lib/components/notes/Notes.svelte:686`, `:773`; `src/lib/components/notes/NoteEditor.svelte:1225` | **Share** › **Copy link** worked | Paste the link to someone who has access | Sharing (section 5.11) |
| `Failed to copy link` | Error | `src/lib/components/notes/Notes.svelte:688`, `:775`; `src/lib/components/notes/NoteEditor.svelte:1227` | The browser refused clipboard access | Copy the address from the browser's address bar | Browser clipboard permission |
| `Copied to clipboard` | Success | `src/lib/components/notes/NoteEditor.svelte:1241` | **Share** › **Copy to clipboard** worked | None | None |
| `Failed to generate title` | Error | `src/lib/components/notes/NoteEditor.svelte:422` | The model's reply to **Generate** contained braces but not valid JSON | Try again or type a title | The model in use (section 5.6) |
| `You cannot upload an empty file.` | Error | `src/lib/components/notes/NoteEditor.svelte:505-508` | Attaching a zero-byte file | Check the file | None |
| `File size should not exceed {maxSize} MB.` | Error | `src/lib/components/notes/NoteEditor.svelte:614-628` | A file or image larger than the admin's **Max Upload Size** | Use a smaller file | `rag.file.max_size` (live value TO BE CONFIRMED) |
| `{error}` (warning from file processing) | Warning | `src/lib/components/notes/NoteEditor.svelte:530-533` | The upload succeeded but processing reported a problem; the attachment is kept | Read the warning | `files-uploads-and-storage.md` |
| `{error}` (server message) | Error | `src/lib/components/notes/NoteEditor.svelte:181`, `:217`, `:537`, `:551`, `:699`, `:740`, `:766`, `:783`, `:806`, `:813`, `:1007`, `:1236`; `src/lib/components/notes/Notes.svelte:94`, `:110`, `:117`, `:156`, `:393`; `src/lib/components/notes/utils.ts:125` | Any failed notes, file or chat request; the text is one of the server messages in 10.3 or a browser error | Depends on the text | Match the text in 10.3 |
| `Note deleted successfully` | Success | `src/lib/components/notes/NoteEditor.svelte:819` | Deleting from the editor worked; the notes list opens | None | None |
| `Failed to delete note` | Error | `src/lib/components/notes/NoteEditor.svelte:822` | Deleting from the editor failed; shown after the server's message | Ask the owner (read-only viewers cannot delete) | Access level (section 3.2) |
| `Saved` | Success | `src/lib/components/notes/NoteEditor.svelte:1005` | A change in the sharing dialog was sent; shown even when the server dropped grants the person may not make | Reload the note to see what was kept | Sharing permissions (section 3.4) |
| `Permission denied when accessing microphone: {error}` | Error | `src/lib/components/notes/NoteEditor.svelte:1163-1172` | **Record**: the browser refused the microphone | Allow microphone access for the site | Browser settings |
| `Permission denied when accessing microphone` | Error | `src/lib/components/notes/NoteEditor.svelte:1180-1182` | **Record**: the microphone request failed outright | As above | As above |
| `Delete note?` with `This will delete {title}.` and buttons `Cancel` / `Confirm` | Confirmation | `src/lib/components/notes/NoteEditor.svelte:1016-1027`; `src/lib/components/notes/Notes.svelte:401-412`; `src/lib/components/common/ConfirmDialog.svelte:21-22` | **Delete** in a note's menu | **Confirm** deletes permanently | None |
| `No Notes` / `Create your first note from the Create menu.` | Notice | `src/lib/components/notes/Notes.svelte:859-870` | No notes match, or the list failed to load (errors are not shown) | Check the view and permission menus; reload | Section 11.3 |
| `No content` | Notice | `src/lib/components/notes/Notes.svelte:806-810` | Grid card of a note with an empty body | None | None |
| `Deleted User` | Notice | `src/lib/components/notes/Notes.svelte:646`, `:652`, `:817`, `:823` | The note's owner account no longer exists | None | None |
| `Read-Only Access` | Notice | `src/lib/components/notes/NoteEditor.svelte:1268-1272` | The person cannot edit this note | Ask the owner for **Write** | Access grants |
| `Generating...` | Placeholder | `src/lib/components/notes/NoteEditor.svelte:1068` | **Generate** is waiting for the model (stays if the request failed, section 5.6) | Wait; if it stays, reload | The model's availability |
| `Loading...` | Notice | `src/lib/components/notes/Notes.svelte:849-854` | More notes are loading at the end of the list | None | None |
| `Format Markdown as you type and paste. Turn off to keep Markdown characters and paste plain text. Existing formatting is preserved.` | Tooltip | `src/lib/components/notes/Notes/NoteMenu.svelte:51-56` | Hovering **Formatting** | None | None |
| `{COUNT} words` / `{COUNT} characters` | Notice | `src/lib/components/notes/NoteEditor.svelte:1314-1327` | Note header | None | None |
| `Write something...` / `Title` | Placeholder | `src/lib/components/notes/NoteEditor.svelte:1382`, `:1068` | Empty body or title | None | None |
| `Untitled` | Stored title | `src/lib/components/notes/NoteEditor.svelte:212` | A blank title was saved | Rename | None |
| `New Note` | Stored title and button label | `src/lib/components/layout/Sidebar.svelte:1319`, `:1324` | Created with the sidebar **+** | Rename | None |
| `Enhance` / `Chat` | Menu labels (unused component) | `src/lib/components/notes/AIMenu.svelte:42`, `:55` | Never shown: nothing uses the component | None | None |

### 10.2 Shared Components as Used by Notes

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `You do not have permission to make this public` | Tooltip | `src/lib/components/workspace/common/AccessControl.svelte:518-521` | Hovering the visibility menu without **Notes Sharing** and **Notes Public Sharing** | Ask an admin | `sharing.notes`, `sharing.public_notes` |
| `No access grants. Private to you.` | Notice | `src/lib/components/workspace/common/AccessControl.svelte:700` | The note is shared with nobody | None | None |
| `Only select users and groups with permission can access` / `Accessible to all users` | Notice | `src/lib/components/workspace/common/AccessControl.svelte:541-548` | Visibility **Private** or **Public** | None | None |
| `Error accessing media devices.` | Error | `src/lib/components/chat/MessageInput/VoiceRecording.svelte:211-237` | **Record** or **Capture Audio** could not get the microphone, or the shared screen or tab gave no audio | Allow access; when capturing, share a tab or screen with audio | Browser settings |
| `Error starting recording.` | Error | `src/lib/components/chat/MessageInput/VoiceRecording.svelte:290-297` | The browser's recorder would not start | Try again or another browser | None |
| `Failed to create chat` | Error | `src/lib/components/chat/Chat.svelte:3305-3312` | Sending the first message of a new side chat, when the server could not create it | Retry; reload the note | Server log line `[note-chat] failed creating hidden chat …` |
| `Suggested prompts` | Notice | `src/lib/components/chat/Chat.svelte:4516` | Empty side chat | Pick a prompt or type | None |
| `No chat history` | Notice | `src/lib/components/chat/EmbeddedChatHistoryDropdown.svelte:94-97` | The person has no side chats for this note | None | None |
| `Connection lost. Reconnecting...` | Warning | `src/routes/+layout.svelte:154-163` | The websocket dropped and did not come back within a short delay; note edits are not being saved meanwhile (section 5.4) | Wait for `Reconnected`, then make one more edit | Network, proxy, `websockets-realtime-and-redis.md` |
| `Reconnected` | Success | `src/routes/+layout.svelte:190-195` | The websocket is back after the warning above | Continue; check the last edits | As above |
| `Cannot create an empty note.` | Error (unreachable) | `src/lib/components/chat/MessageInput.svelte:1199-1203` | Belongs to a composer function nothing calls in this version | None | None |
| `This is a default user permission and will remain enabled.` | Notice (admin) | `src/lib/components/admin/Users/Groups/Permissions.svelte:432-438`, `:452-457`, `:985-990` | Turning off **Notes**, **Notes Sharing** or **Notes Public Sharing** for a group while the default grants it | Change the default permissions instead | Ground truth: groups cannot remove a default |

### 10.3 Server Messages

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `401 Unauthorized` | Error (HTTP 401) | `backend/open_webui/routers/notes.py:74-77`, `:122-125`, `:163-166`, `:216-219`, `:264-267`, `:318-321`, `:408-411`, `:466-469`, `:536-539`, `:617-620`, `:675-678`, `:724-727`; text in `backend/open_webui/constants.py:69` | A non-admin without the `features.notes` permission calls any notes endpoint (for example after the permission was removed while their page was open) | Reload; ask an admin about access to notes | The person's groups and the default permissions |
| `We could not find what you're looking for :/` | Error (HTTP 404) | `backend/open_webui/routers/notes.py:271`, `:325`, `:415`, `:473`, `:543`, `:624`, `:682`, `:731`; `backend/open_webui/constants.py:78` | The note id does not exist (deleted, or a mistyped link) | Ask the sender for a fresh link | Whether the note was deleted (section 5.13) |
| `Something went wrong :/` | Error (HTTP 403 or 400) | 403: `backend/open_webui/routers/notes.py:285`, `:337`, `:427`, `:485`, `:555`, `:636`, `:694`, `:743`; 400: `:242`, `:392`, `:514`, `:594`, `:756`; `backend/open_webui/constants.py:16-18` | 403: the person lacks the read access (open, chat, pin) or write access (save, share, delete) the action needs. 400: creating, saving or deleting failed on the server, or the side chat could not be created | 403: ask the owner for access. 400: retry, then report | 403: access grants (section 3). 400: server log at the reported time |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 401) | `backend/open_webui/routers/chats.py:1577-1584`; `backend/open_webui/constants.py:70-72` | Deleting a side chat without the `chat.delete` permission | Ask an admin | `chat.delete` permission |
| `Failed to join document` | Socket error event | `backend/open_webui/socket/main.py:730-732` | An exception while joining live editing; the editor does not display it | Reload the note | Server log `Error in yjs_document_join: {e}` |

Sign-in failures (expired session, pending account) on any notes request use the platform's
standard texts; see `authentication-and-sign-in.md`. The note tools' own errors (`Note not found`,
`Write access denied`, `Failed to update note` and others) are catalogued in
`builtin-native-tools.md`, section 10.

### 10.4 Server Log Lines (Not Shown to Users)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `[note-chat] failed creating hidden chat note_id={note_id} user_id={user_id}` | Log error | `backend/open_webui/routers/notes.py:391`, `:513` | A side chat could not be created | None | Database health at that time |
| `Note {note_id} not found for user {user_id}` | Log error | `backend/open_webui/socket/main.py:535` | Joining the note room for a note that does not exist | None | Whether the note was deleted |
| `User {user_id} does not have access to note {note_id}` | Log error | `backend/open_webui/socket/main.py:548`, `:682` | Joining the room or live session without read access | None | Access grants |
| `Note {note_id} not found` | Log error | `backend/open_webui/socket/main.py:669`, `:742`, `:826` | Live editing for a note that no longer exists (for example deleted while open) | None | As above |
| `User {user_id} does not have write access to note {note_id}` | Log error | `backend/open_webui/socket/main.py:755` | A delayed body save from someone who lost write access | None | Access grants |
| `User {user_id} does not have write access to note {note_id}. Rejecting update.` | Log warning | `backend/open_webui/socket/main.py:839` | A live edit from someone without write access was refused | None | As above |
| `Session {sid} not in room {room}. Rejecting update.` | Log warning | `backend/open_webui/socket/main.py:814` | A live edit arrived from a session that had not (yet) joined the document; the edit is dropped | Reload | Section 5.9 |
| `Session {sid} not in room {room}. Cannot send state.` | Log warning | `backend/open_webui/socket/main.py:773` | A state request from a session outside the document | Reload | As above |
| `Error in yjs_document_join: {e}` / `Error in yjs_document_state: {e}` / `Error in yjs_document_update: {e}` / `Error in yjs_document_leave: {e}` | Log error | `backend/open_webui/socket/main.py:731`, `:799`, `:883`, `:915` | Unexpected failure in live editing | Reload | Server log detail |
| `Cleaning up document {document_id} as no users are left` | Log info | `backend/open_webui/socket/main.py:911` | The last editor left | None | None |

### 10.5 Event Texts (Webhooks and Event Functions)

Webhook posts use the event's message followed by the note id in brackets
(`backend/open_webui/events.py:1040-1057`).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Note created` | Event text | `backend/open_webui/events.py:317-318` | `note.created` | None | Event webhooks configuration |
| `Note updated` | Event text | `backend/open_webui/events.py:320-321` | `note.updated` | None | As above |
| `Note access updated` | Event text | `backend/open_webui/events.py:323-324` | `note.access_updated` | None | As above |
| `Note pinned` | Event text | `backend/open_webui/events.py:326-327` | `note.pinned` | None | As above |
| `Note unpinned` | Event text | `backend/open_webui/events.py:329-330` | `note.unpinned` | None | As above |
| `Note deleted` | Event text | `backend/open_webui/events.py:332-333` | `note.deleted` | None | As above |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it does not change data, settings, roles or access. Never ask a person to send
note content; ask for the note's address (`/notes/{id}`), the time and what they saw.

### 11.1 "My note didn't save"

**Symptom.** After reopening a note, recent text is missing, or the title has gone back to an
earlier one.

**Likely causes, in order.**

1. The live connection was down while they typed. The body is saved only through the websocket
   (section 5.4); edits made during a drop are kept in the browser and may never reach the database,
   especially if the note was closed soon after `Reconnected` without another edit (section 5.9).
2. A collaborator or an AI rewrite changed the note afterwards (section 11.2).
3. Their write access was removed while the note was open: the server silently refuses their edits
   (`backend/open_webui/socket/main.py:829-840`).
4. Title only: they are not the owner (the title box is disabled for others), or **Generate** failed
   and left the box on `Generating...`, which saves nothing (section 5.6).
5. Several server processes without the Redis websocket manager, so two editors' saves competed
   (section 5.9; production set-up TO BE CONFIRMED).

**Diagnostic steps.**

1. Ask whether `Connection lost. Reconnecting...` appeared, and when they last edited.
2. Ask them to reload the note: what they now see is what the database holds.
3. In the notes list, hover the note's update time to see the full date and time of the last save.
4. Ask whether anyone else edits the note or whether the side chat was asked to rewrite it.
5. Ask whether the header shows `Read-Only Access`.

**Resolution.** Explain that saving is automatic only while connected; after `Reconnected`, make one
more small edit and wait a second, or reload to check, before closing. When the connection is
unreliable, use **Share** › **Copy to clipboard** as a safety copy. Lost text cannot be restored
from the interface: there is no version history (section 5.13).

**Escalation.** Send the note id, the time window, the browser, whether the connection warning
appeared and whether others were editing. The platform maintainer can check the server log for
`Error in yjs_document_update`, `Rejecting update` and `does not have write access` lines around
that time, and confirm the websocket set-up. Whether a database backup could recover the text is
TO BE CONFIRMED.

### 11.2 "Someone else's changes overwrote mine"

**Symptom.** Text that a person wrote was replaced or removed by someone else's version.

**Likely causes, in order.**

1. Someone used the note's side chat to rewrite the note (for example `Enhance this note and update
   it.`); `replace_note_content` replaces the whole body or chosen ranges for everyone, and stores
   Markdown only (section 5.7).
2. The two people were not in the same live session (for example connected to different server
   processes without Redis), so they did not see each other and the later save won (section 5.9).
3. Ordinary collaborative editing: anyone with **Write** can change any part of the note, and
   there is no per-change history.
4. One editor's connection dropped and came back while the other kept editing (outcome
   TO BE CONFIRMED, section 14).

**Diagnostic steps.** Ask who has write access (the owner sees the list in the sharing dialog).
Ask whether, while both were editing, each could see the other's named cursor; if not, they were not
in the same live session. Ask whether either used the side chat to edit the note.

**Resolution.** Suggest that collaborators agree who uses the side chat for rewrites, and that the
owner changes people who only need to read to **Read** (if the owner has sharing rights, section 3.4).
Tier 1 cannot restore earlier text.

**Escalation.** Send the note id, the times and the people involved (as ticket metadata, not note
content), and whether cursors were visible. The maintainer checks the multi-process websocket
configuration (`WEBSOCKET_MANAGER`) and logs.

### 11.3 "I can't see the note someone shared with me"

**Symptom.** A colleague says they shared a note, but it is not in the person's Notes list.

**Likely causes, in order.**

1. It was shared for reading only, and the list's permission menu is on its default **Write**, which
   hides read-only notes. Choosing **Read Only** shows them (section 5.5).
2. The view menu is on **Created by you** (remembered in that browser), or a search is active.
3. The share never took effect: with the code defaults ordinary users have no sharing options in
   the interface (**Notes Sharing** is off), and the server quietly drops grants the sharer may not
   make even though the dialog said `Saved` (section 3.4).
4. It was shared with a group the person is not in.
5. The person cannot use notes at all (section 11.4), or the note was deleted.

**Diagnostic steps.**

1. Ask the person to set the view menu to **All**, the permission menu to **Read Only**, and clear
   the search box.
2. Ask the sharer to reload the note and open the sharing dialog: does it list the person (or their
   group) with **Read** or **Write**?
3. Ask the sharer for **Share** › **Copy link** and have the person open it.
   `Something went wrong :/` means no access; `We could not find what you're looking for :/` means
   the note no longer exists.

**Resolution.** Guide the person to the **Read Only** filter, or ask the sharer to share again with
the right person and level. If the sharer has no sharing options, only an admin can share the note
or grant **Notes Sharing**; whether MedIT GPT allows note sharing is TO BE CONFIRMED.

**Escalation.** Send the note id, both people's account identifiers as ticket metadata, and the
group names involved. An admin can check the note's sharing (admins can open any note).

### 11.4 "Notes is missing from the sidebar"

**Symptom.** The **Notes** shortcut at the top of the sidebar is gone.

**Likely causes, in order.**

1. The person unpinned it. It is still in the user menu (click the profile picture or name).
2. An admin turned notes off for everyone (`notes.enable`): it is then missing from the user menu
   too, and `/notes` returns to the home page.
3. The person's groups and the default permissions do not grant **Notes** (`features.notes`): same
   appearance as 2, but only for some people.
4. Their permission was changed while the app was open, and they have not reloaded.

Do not confuse the shortcut with the sidebar's **Notes** section, which lists pinned notes and
appears only when the person has pinned at least one note (section 5.12).

**Diagnostic steps.** Ask the person to open the user menu: if **Notes** is there, the shortcut was
only unpinned. If not, ask them to reload, then to open `/notes` directly; a silent return to the
home page means the switch or the permission is off. Ask whether colleagues still have Notes
(everyone missing points to the switch).

**Resolution.** For an unpinned shortcut: open the user menu, hold **Shift**, and click the pin
button beside **Notes** (`Pin to Sidebar`). Otherwise escalate; tier 1 does not change permissions.

**Escalation.** Send the person's role and groups and whether colleagues are affected. An admin
checks Admin Settings › General › **Notes** and the **Notes** feature permission (section 5.15).

### 11.5 "The AI button in notes does nothing"

**Symptom.** The person expected AI help in a note and nothing happened.

**Likely causes, in order.**

1. They are looking for an **Enhance** button. This version has none; AI help is the speech-bubble
   **Chat** button (the side chat) with the suggestion `Enhance this note and update it.`, plus the
   title **Generate** button (sections 5.6 and 5.7).
2. **Generate** is stuck on `Generating...`: the model request failed (no model available to them,
   or the model is unreachable) and the code shows no message (section 5.6).
3. **Generate** is greyed out: they are not the note's owner.
4. In the side chat the model answered but the note did not change: they have read-only access (the
   tool returns `Write access denied`), or the model did not call the note tool. The tool's input
   and output can be opened under the answer (see `builtin-native-tools.md`).
5. No model is available to them, so the side chat cannot answer (see
   `workspace-models-and-model-access.md`).

**Diagnostic steps.** Ask which button they used and what they saw. Ask whether a model is shown in
the side chat's message box and whether the same model works in an ordinary chat. Check whether the
note header shows `Read-Only Access`.

**Resolution.** Show the side chat and its suggested prompts; pick a working model in the side
chat's model selector; reload if the title box is stuck. For read-only notes, ask the owner for
**Write**.

**Escalation.** Send the model name, the time and the note id; the maintainer checks the model
connection logs (`model-connections-openai-ollama-and-direct.md`).

### 11.6 "It says Read-Only Access and I can't type"

**Symptom.** The note opens but cannot be edited; the header reads `Read-Only Access`.

**Likely causes, in order.** The person has a **Read** share or the note is **Public** without
**Allow public write access**; or their **Write** share was removed (section 3.3).

**Diagnostic steps.** Ask whether they should be an editor and who owns the note (the owner's name
shows in the notes list).

**Resolution.** Ask the owner to change them to **Write**. Read-only viewers can still download,
copy, pin and use their own side chat.

**Escalation.** Only if the owner cannot share (no sharing rights): send the note id and the
intended editors to an admin.

### 11.7 "I can't rename a note that's shared with me"

**Symptom.** The title box is greyed out although the person can edit the text.

**Likely causes, in order.** Renaming is limited to the owner and admins in this version, even for
people with **Write** (`src/lib/components/notes/NoteEditor.svelte:1069-1070`).

**Diagnostic steps.** Confirm the person is not the owner.

**Resolution.** Ask the owner to rename it.

**Escalation.** None needed.

### 11.8 "I can't share my note"

**Symptom.** The sharing dialog shows only **Private**, with no **Access List**, or the share
button is greyed out.

**Likely causes, in order.**

1. **Notes Sharing** is off for them (code default off), so the Access List is hidden; **Public**
   also needs **Notes Public Sharing** (tooltip `You do not have permission to make this public`).
2. They are not the owner: the share button is disabled for everyone except the owner and admins.

**Diagnostic steps.** Ask whether the note is theirs (the list shows the owner) and what the dialog
offers.

**Resolution.** Explain the permission; whether staff may share notes is an organizational decision
(TO BE CONFIRMED). As an alternative, they can download the note or copy its text into an approved
channel, keeping personal-data rules in mind.

**Escalation.** Requests for sharing rights go to the admins with the person's groups.

### 11.9 "My note disappeared"

**Symptom.** A note is no longer in the list, or its link fails.

**Likely causes, in order.**

1. It was deleted: by the person (holding **Shift** in the notes list turns each menu into a bin
   button that deletes **without confirmation**), by a collaborator with **Write** (who can
   delete), or by an admin (section 5.13).
2. A filter or search is hiding it (section 5.5).
3. For a note shared with them: the share was removed or reduced to **Read** (then it moves to the
   **Read Only** filter).
4. Notes were switched off or their permission changed (section 11.4).

**Diagnostic steps.** Ask for the link; `We could not find what you're looking for :/` means the
note no longer exists, `Something went wrong :/` means it exists but they have no access. Ask
whether they held Shift while clicking in the list. Ask them to reset the filters.

**Resolution.** Deleted notes cannot be restored from the interface. Explain the Shift shortcut.

**Escalation.** Send the note id and the approximate time. If event webhooks are configured
(TO BE CONFIRMED), a `note.deleted` event names the person who deleted it (section 9). Whether a
backup restore is possible is TO BE CONFIRMED.

### 11.10 "I don't see other people's changes until I reload"

**Symptom.** A colleague edits a shared note, but the person's open copy does not change.

**Likely causes, in order.**

1. The person has read-only access: read-only viewers do not join live editing and see the body as
   it was when they opened it (section 5.9).
2. Their connection is down (`Connection lost. Reconnecting...`).
3. The two are connected to different server processes without the Redis websocket manager
   (section 5.9).

**Diagnostic steps.** Check for `Read-Only Access` in the header; ask whether the connection warning
appeared; ask whether editors see each other's cursors.

**Resolution.** Reload to see the latest saved version; ask for **Write** if they need to co-edit.

**Escalation.** If two editors with **Write** never see each other's cursors, send the note id and
times; the maintainer checks the websocket and Redis configuration.

### 11.11 "A picture in my note shows a placeholder or the site logo"

**Symptom.** An image in the note shows a placeholder picture or the site icon (on this branch the
U of T favicon, section 12) instead of the picture.

**Likely causes, in order.**

1. The image was inserted by web address (for example pasted from a web page). Images from other
   websites are not loaded; the site icon is shown instead (section 5.8).
2. The note's text refers to an image that is no longer in the note's attachment list; the
   placeholder `/image-placeholder.png` is shown.
3. The note was rewritten by the AI side chat, which stores Markdown only; whether images survive
   that is TO BE CONFIRMED (section 14).

**Diagnostic steps.** Ask how the image was added and whether the AI was used on the note.

**Resolution.** Copy the image itself (not its link) and paste it, or save it and drop the file
into the note.

**Escalation.** If pasted images disappear without an AI rewrite, send the note id and time.

### 11.12 "The PDF of my note is just a picture"

**Symptom.** Text in the downloaded PDF cannot be selected or searched, or the pages are black.

**Likely causes, in order.** The PDF is made in the browser by taking a picture of the note
(section 5.10); in dark mode the background is black.

**Diagnostic steps.** Ask whether the app was in dark mode.

**Resolution.** Switch to light mode before downloading, or download **Plain text (.md)** or
**Plain text (.txt)**, or use **Copy to clipboard** and paste into a word processor.

**Escalation.** None needed.

### 11.13 "Opening a note link sends me back to the home page"

**Symptom.** Following a link to `/notes/{id}` shows a message (or nothing) and lands on the home
page.

**Likely causes, in order.**

1. `Something went wrong :/`: the note exists but is not shared with them.
2. `We could not find what you're looking for :/`: the note was deleted or the link is wrong.
3. `401 Unauthorized`: they lack the notes permission (their page had loaded before the change).
4. No message at all: notes are off or their loaded profile has no notes permission
   (`src/routes/(app)/notes/+layout.svelte:10-19`).

**Diagnostic steps.** Ask for the exact message.

**Resolution.** For 1, the owner shares the note (section 5.11); for 2, ask for a new link; for 3
and 4, see section 11.4.

**Escalation.** As in 11.3 or 11.4.

### 11.14 "The import said it worked, but my notes aren't there"

**Symptom.** `Imported notes successfully` appeared, but some files did not become notes.

**Likely causes, in order.** A file that was not `.txt` or `.md` stopped the import at that file
(after `Only txt and md files are allowed`); a note could not be created (an error message appears
first); or the list was not refreshed after the early stop (section 5.2).

**Diagnostic steps.** Ask which files were chosen and which messages appeared; ask them to reload
the notes page.

**Resolution.** Import the remaining `.txt` or `.md` files again; convert other formats first.

**Escalation.** If `.md` or `.txt` files fail with `Something went wrong :/`, send the time and the
file names (not their contents).

### 11.15 "I have lots of empty notes named with dates"

**Symptom.** The list holds many empty notes titled like `2026-10-09` or `New Note`.

**Likely causes, in order.** Every way of creating a note saves it immediately; a bookmark or
shortcut to `/notes/new` creates a new note on every visit; **Create a new note** in the search
dialog does too (section 5.2).

**Diagnostic steps.** Ask how they usually open notes.

**Resolution.** Suggest bookmarking `/notes` rather than `/notes/new`. Empty notes can be deleted
from the list (holding **Shift** shows instant-delete buttons; warn that there is no confirmation).

**Escalation.** None needed.

### 11.16 "I can't attach a file to my note"

**Symptom.** An upload fails, or **Upload files** is missing.

**Likely causes, in order.** The file is larger than the admin's maximum
(`File size should not exceed {maxSize} MB.`) or empty (`You cannot upload an empty file.`); the
server refused or failed the upload (its message appears; see `files-uploads-and-storage.md`); the
person has read-only access, so **Upload files** and **Record** are not offered.

**Diagnostic steps.** Ask for the exact message, the file type and size, and whether
`Read-Only Access` shows.

**Resolution.** Use a smaller file or ask the owner for **Write**.

**Escalation.** For server-side upload failures, follow `files-uploads-and-storage.md`.

### 11.17 "The AI changed my note and the formatting is different"

**Symptom.** After asking the side chat to improve the note, headings, tables, images or layout
changed.

**Likely causes, in order.** The rewrite tool replaces the stored body with Markdown only and
clears the HTML and editor forms; the editor then rebuilds the note from that Markdown
(`backend/open_webui/tools/builtin.py:1470-1485`; `src/lib/components/notes/NoteEditor.svelte:296-315`).
Anything the model left out of its Markdown is gone.

**Diagnostic steps.** Ask whether the change followed a side-chat request; the tool call under the
answer shows what was sent (see `builtin-native-tools.md`).

**Resolution.** Undo may help immediately afterwards in the same editor session (TO BE CONFIRMED);
otherwise reapply the formatting. Suggest asking the model to change only the selected text
(select it first, then ask).

**Escalation.** None unless content was lost unexpectedly; then as in 11.1.

### 11.18 "Can an admin read my notes?"

**Symptom.** A person asks who can see their notes.

**Likely causes, in order.** Admins can open, edit and delete any note, and with
`BYPASS_ADMIN_ACCESS_CONTROL` on (code default; live value TO BE CONFIRMED) an admin's notes list
shows every user's notes (sections 3.2 and 5.5). Otherwise only the people and groups the note is
shared with, or everyone if it is **Public**.

**Diagnostic steps.** Ask whether the note is shared (the owner can open the sharing dialog).

**Resolution.** Explain the rule above. If the person believes their note was accessed or changed
inappropriately, treat it as a possible privacy incident: do not investigate the content, and refer
it under the U of T privacy process (privacy.utoronto.ca); the internal MedIT GPT escalation route
is TO BE CONFIRMED.

**Escalation.** Send only the note id, the person's account identifier and the time window.

## 12. Local Customisations

The notes area matches upstream Open WebUI v0.11.4. Read-only checks on 2026-10-10:

- `git diff main...uoft` shows no change in `backend/open_webui/routers/notes.py`,
  `backend/open_webui/models/notes.py`, `backend/open_webui/socket/`, `src/lib/components/notes/`,
  `src/routes/(app)/notes/`, `src/lib/apis/notes/`, the rich-text editor
  (`src/lib/components/common/RichTextInput.svelte`, `src/lib/components/common/RichTextInput/`),
  `src/lib/components/layout/` or `src/lib/components/workspace/common/`, and no note-related key in
  the `en-US` translation file.
- `git diff` (uncommitted working-tree changes) shows none in those paths either. The uncommitted
  changes to `src/lib/components/chat/Chat.svelte` (a tool-approval resume fix) and
  `src/lib/components/chat/Messages/ResponseMessage.svelte` (status display) also apply to the
  note's side chat, but they do not touch the side-chat or **Insert into note** code; the
  **Insert into note** button is still at `src/lib/components/chat/Messages/ResponseMessage.svelte:972-986`.
  The uncommitted change to `src/lib/i18n/index.ts` changes language detection and fallback for
  every screen, notes included.

Fork changes that show up in notes indirectly:

| Fork change | Where it shows in notes | Source |
|---|---|---|
| Default product name `MedIT GPT` (`WEBUI_NAME`) | Browser tab titles `Notes / MedIT GPT` and `{title} / MedIT GPT` (the live name is environment data, TO BE CONFIRMED) | `backend/open_webui/env.py:951`; `src/routes/(app)/notes/+layout.svelte:29-31`; `src/lib/components/notes/NoteEditor.svelte:984-988` |
| Replaced site icon `static/favicon.png` (U of T) | Shown in place of images from other websites in a note (section 5.8) | `src/lib/utils/safeImageUrl.ts:6`, `:22-37`; `git diff --stat main...uoft -- static/favicon.png` |

The licence comments beside the tab titles ("LICENSE covers this Open WebUI browser-title
identifier") are upstream text and must stay (`src/routes/(app)/notes/+layout.svelte:26-28`;
`src/lib/components/notes/NoteEditor.svelte:981-983`; `src/lib/components/notes/Notes.svelte:366-368`).
See `local-customisations-uoft-fork.md` for the full list of fork changes.

## 13. Source File Index

"All" means the file was read in full; "parts" means the cited ranges were read.

### 13.1 Back End

| File | What it contributes | Read |
|---|---|---|
| `backend/open_webui/routers/notes.py` | Every notes endpoint, permission and access checks, side-chat creation, note events | All |
| `backend/open_webui/models/notes.py` | `note` and `pinned_note` tables, forms, search, pin and delete logic, data repair | All |
| `backend/open_webui/socket/main.py` | `join-note` and `ydoc:*` handlers, delayed body save, disconnect clean-up, Redis versus in-memory set-up | Parts (60-215, 330-352, 505-990) |
| `backend/open_webui/socket/utils.py` | Shared-document manager (memory or Redis), compaction | Parts (17, 241-394) |
| `backend/open_webui/models/access_grants.py` | Grant table, `has_access`, list filters for write and read-only | Parts (20-48, 443-478, 562-620, 723-934) |
| `backend/open_webui/utils/access_control/__init__.py` | Grant filtering on save | Parts (223-301) |
| `backend/open_webui/utils/access_control/files.py` | File access rules (no note rule; folder note entries) | Parts (1-40, 105-158) |
| `backend/open_webui/config.py` | `ENABLE_NOTES`, notes permissions, `DEFAULT_CONFIG` entries, file and model settings | Parts (983-995, 1674, 1820-1846, 1910-2060, 2086-2092, 2907-2909, 3087-3130) |
| `backend/open_webui/main.py` | Router mount; `/api/config` features and file limits | Parts (862, 2255-2422) |
| `backend/open_webui/routers/auths.py` | Admin config mapping of `ENABLE_NOTES` | Parts (104-135, 1225-1240) |
| `backend/open_webui/routers/chats.py` | Side-chat deletion permission | Parts (1568-1598) |
| `backend/open_webui/models/chats.py` | Hidden note chats and their exclusion from chat lists | Parts (602-633, function map of internal filters) |
| `backend/open_webui/routers/files.py`, `backend/open_webui/models/files.py` | File record returned at upload | Parts (605-621; 34-90) |
| `backend/open_webui/tools/builtin.py` | `write_note`, `replace_note_content`, note event emitter | Parts (80-102, 1286-1500) |
| `backend/open_webui/utils/middleware.py` | Side-chat detection, note files added to context, tools in side chats | Parts (2775-2830) |
| `backend/open_webui/utils/tools.py` | Note tools gating | Parts (717-721, via grep) |
| `backend/open_webui/tasks.py` | Background task creation and cancellation | Parts (28-68, 157-187, 259-312) |
| `backend/open_webui/events.py` | Note event definitions, sinks, actor fields, webhook text | Parts (317-333, 669-705, 974-1102, 1166-1202) |
| `backend/open_webui/constants.py` | Error texts | Parts (1-80) |
| `backend/open_webui/env.py` | `REDIS_KEY_PREFIX`, websocket settings | Parts (384, 473-493) |
| `backend/open_webui/migrations/versions/9f0c9cd09105_add_note_table.py` | Creates `note` | All |
| `backend/open_webui/migrations/versions/4de81c2a3af1_add_pinned_note_table.py` | Creates `pinned_note` | Parts (1-80) |
| `backend/open_webui/migrations/versions/e1f2a3b4c5d6_add_is_pinned_to_note.py` | Adds `is_pinned` | Parts (via grep) |
| `backend/open_webui/migrations/versions/f1e2d3c4b5a6_add_access_grant_table.py` | Moves note sharing into `access_grant` | Parts (28-80, 215-225) |

### 13.2 Front End

| File | What it contributes | Read |
|---|---|---|
| `src/lib/components/notes/Notes.svelte` | Notes list: create, import, search, filters, sort, grid, delete, download | All |
| `src/lib/components/notes/NoteEditor.svelte` | Editor: load, saves, title generation, attachments, images, recording, side chat, sharing, menu | All |
| `src/lib/components/notes/Notes/NoteMenu.svelte` | Note menu items | All |
| `src/lib/components/notes/utils.ts` | PDF export, create helper | All |
| `src/lib/components/notes/NotePanel.svelte` | Side-chat panel or drawer | All |
| `src/lib/components/notes/RecordMenu.svelte` | Microphone menu | All |
| `src/lib/components/notes/AIMenu.svelte` | Unused Enhance/Chat menu | All |
| `src/routes/(app)/notes/+layout.svelte`, `+page.svelte`, `new/+page.svelte`, `[id]/+page.svelte` | Routes and the feature gate | All |
| `src/lib/apis/notes/index.ts` | API client | All |
| `src/lib/components/common/RichTextInput/Collaboration.ts` | Live collaboration provider | All |
| `src/lib/components/common/RichTextInput.svelte` | Editor set-up, formatting, paste, Markdown conversion | Parts (200-360, 735-1060, 1320-1429) |
| `src/lib/components/common/RichTextInput/Image/image.ts` | Image node and `data://` references | Parts (60-198) |
| `src/lib/components/common/RichTextInput/FormattingButtons.svelte` | Formatting button labels | Parts (via grep) |
| `src/lib/utils/safeImageUrl.ts` | Blocking images from other sites | All |
| `src/lib/components/workspace/common/AccessControlModal.svelte` | Sharing dialog shell | All |
| `src/lib/components/workspace/common/AccessControl.svelte` | Visibility, access list, read and write | Parts (1-140, 196-330, 355-370, 440-705) |
| `src/lib/components/workspace/common/AddAccessModal.svelte` | Add people or groups | Parts (1-80) |
| `src/lib/components/layout/Sidebar.svelte` | Notes shortcut, pinned-notes section | Parts (95-240, 384-400, 1031, 1257, 1308-1330) |
| `src/lib/components/layout/Sidebar/UserMenu.svelte` | Notes in the user menu, pin toggle | Parts (40-80, 236-332) |
| `src/lib/components/layout/Sidebar/PinnedNoteList.svelte` | Pinned notes list | All |
| `src/lib/components/layout/SearchModal.svelte` | Create a new note action | Parts (515-545) |
| `src/lib/components/chat/Chat.svelte` | Embedded side chat: models, selected text, suggestions, header | Parts (129-240, 770-900, 2290-2340, 3300-3330, 4290-4330, 4508-4534) |
| `src/lib/components/chat/EmbeddedChatHistoryDropdown.svelte` | Side-chat history menu | All |
| `src/lib/components/chat/EmbeddedChatHistoryItem.svelte` | Side-chat entry and delete | Parts (30-95) |
| `src/lib/components/chat/MessageInput.svelte` | Model selector in the side chat; unused create-note function; note drops | Parts (180-192, 1196-1218, 1285-1297, 2565-2595, 2668-2675) |
| `src/lib/components/chat/Messages/ResponseMessage.svelte` | Insert into note | Parts (972-986) |
| `src/lib/components/chat/MessageInput/VoiceRecording.svelte` | Recording and screen-audio capture used by **Record** | Parts (17-18, 205-237, 280-300, 330-360) |
| `src/lib/components/chat/ModelSelector/Selector.svelte` | `Set as default` label | Parts (1270) |
| `src/lib/components/common/SplitCreateButton.svelte` | **Create** split button and its menu arrow | Parts (via grep, 59-79) |
| `src/lib/components/admin/Settings/Models.svelte` | Admin default models | Parts (273, 337, 388) |
| `src/lib/components/admin/Settings/General.svelte` | Notes switch | Parts (310-345) |
| `src/lib/components/admin/Users/Groups/Permissions.svelte` | Notes permissions | Parts (235, 420-462, 960-995) |
| `src/lib/components/common/ConfirmDialog.svelte` | Delete confirmation defaults | Parts (18-22, 130-160) |
| `src/lib/apis/openai/index.ts` | Title-generation request | Parts (421-451) |
| `src/lib/utils/index.ts` | Time groups | Parts (1308-1337) |
| `src/routes/+layout.svelte` | Socket set-up, connection warnings, session load | Parts (147-280, 1272-1292) |
| `src/lib/i18n/locales/en-US/translation.json` | English text of every key quoted here | Keys checked |

## 14. Open Questions

Everything below could not be established from the repository. Items marked "test" need a
read-only check in a test environment by the platform maintainer.

### 14.1 Live Configuration (Data, TO BE CONFIRMED)

1. The live values of `notes.enable`, `features.notes`, `sharing.notes`, `sharing.public_notes`,
   `access_grants.allow_users` and `access_grants.allow_groups` in the default permissions and in each
   group (sections 3 and 7). With the code defaults, notes are on for everyone and only admins can
   share them.
2. Whether MedIT GPT staff are meant to share notes at all, and whether **Public** sharing is
   acceptable for a deployment whose notes may hold health information (organizational policy).
3. `BYPASS_ADMIN_ACCESS_CONTROL` in production (decides whether an admin's notes list shows every
   user's notes, section 5.5).
4. The number of server processes or replicas, `WEBSOCKET_MANAGER`, `WEBSOCKET_REDIS_URL` and
   `ENABLE_WEBSOCKET_SUPPORT` in production (section 5.9). With more than one process and no Redis
   websocket manager, live editing does not work across processes.
5. `rag.file.max_size`, `file.image_compression_width`, `file.image_compression_height` and
   `ui.default_models` in production (section 7.1).
6. Whether event webhooks or event functions are configured; if so, they receive note titles and the
   acting person's name and email (section 9).
7. The production host name for note links (`{site}/notes/{id}`).

### 14.2 Behaviour to Confirm by Testing

8. **Offline edits** (test): what other editors and the database end up with when one editor's
   connection drops while others keep editing, and the edits typed during the drop (section 5.9).
   The code does not resend those edits as separate changes, and a resend after the server lost the
   shared document is not written to the database until the next edit.
9. **Body from an address** (test): `/notes/new?content=…`, `/notes?content=…` and the search
   dialog's **Create a new note** store the same text as both Markdown and HTML
   (`src/lib/components/notes/utils.ts:115-120`); confirm whether Markdown and line breaks in that
   text display as intended.
10. **Images after an AI rewrite** (test): `replace_note_content` stores Markdown only; the editor
    rebuilds the note from that Markdown, and its image rule does not read `data:`-style addresses
    from HTML (`src/lib/components/common/RichTextInput/Image/image.ts:105-111`); confirm whether
    inline images survive a rewrite.
11. **Images in downloads** (test): whether pictures appear in the PDF, given that the stored HTML
    refers to them as `data://{id}` (section 5.10).
12. **Undo after an AI rewrite** (test): whether **Undo** in the same editor session reverses a
    side-chat rewrite (section 11.17).
13. **Attachments for collaborators** (test): whether people a note is shared with can open its
    uploaded files; no file-access rule covers notes (`files-uploads-and-storage.md`, section 14
    item 21).
14. **Edits racing a rejoin** (test): whether edits made right after `Reconnected` can be dropped
    with the log line `Session {sid} not in room {room}. Rejecting update.` (section 10.4).
15. Whether long notes or large inline images slow the editor, the collaboration channel or the
    `note` row noticeably; no limit exists in code (section 7.1).

### 14.3 Security-Sensitive Questions

16. Security-sensitive: whether turning `notes.enable` off is meant to block the notes endpoints as
    well as the interface (the notes router checks the `features.notes` permission). Refer to the
    platform maintainer and U of T Information Security (security.utoronto.ca).
17. Security-sensitive: whether the interface and the server agree on what collaborators with write
    access may change (sharing, title, deletion) for notes. Refer to the platform maintainer and
    U of T Information Security (security.utoronto.ca).
18. Security-sensitive: how upload permissions apply to note attachments. Refer to the platform
    maintainer and U of T Information Security (security.utoronto.ca).

### 14.4 Organizational and Upstream Unknowns

19. Whether database backups exist, how long they are kept, and whether a deleted note (or lost
    text) can be restored from them (sections 5.13 and 11.1).
20. The internal MedIT GPT escalation route for privacy questions about notes (section 11.18), and
    support contacts in general (ground truth: none in the repository).
21. Whether the platform wants a clean-up of side chats and attachment files left behind by deleted
    notes; nothing removes them (section 5.13).
22. Upstream intent: `src/lib/components/notes/AIMenu.svelte` (an **Enhance** / **Chat** menu) is
    unused, the editor's `versions` list is never saved, and the composer's create-note function is
    never called; whether later releases restore them is unknown.
23. Clarification for the ground truth (not a contradiction): note and pinned-note timestamps are
    nanoseconds (`time.time_ns()`), while access-grant timestamps are seconds
    (`backend/open_webui/models/notes.py:176-177`; `backend/open_webui/models/access_grants.py:472`).
    The ground truth's "epoch integers" is correct but does not state the unit.
