# Files, Uploads and Storage

## At a Glance

- **What a "file" is.** Every upload is one row in the `file` table plus the file's bytes in storage.
  By default the bytes live on the server's disk in `DATA_DIR/uploads`, named `{id}_{original name}`
  (`backend/open_webui/config.py:150`, `:174-175`; `backend/open_webui/routers/files.py:364-375`). Cloud
  storage (S3, Google Cloud Storage, Azure Blob) is selected with the environment variable
  `STORAGE_PROVIDER`; even then the server writes a local copy first (section 5.20, 6.5).
- **Ways in.** In a chat: the **+** menu (**Upload Files**, **Capture**, **Attach Files** for earlier
  uploads, **Google Drive**, **Microsoft OneDrive**), dragging files onto the chat, and pasting. Knowledge
  bases, channels and notes upload through the same server endpoint, `POST /api/v1/files/`
  (`backend/open_webui/main.py:875`; `backend/open_webui/routers/files.py:280-321`).
- **What the server does.** It saves the bytes, records the file with status `pending`, then in the
  background extracts the text (or transcribes audio), stores that text on the row, embeds it into the
  vector store collection `file-{id}` unless the admin bypassed embedding, and finally marks the file
  `completed` or `failed` with an error (`backend/open_webui/routers/files.py:128-277`, `:408-457`;
  `backend/open_webui/routers/retrieval.py:1926-2196`). The browser watches a status stream; a processing
  failure appears as a **yellow warning pop-up while the file stays attached** (section 5.5).
- **Limits.** None by default. An admin can set **Allowed File Extensions** (lower case, no dots),
  **Max Upload Size** in MB and **Max Upload Count** in **Admin Settings > Documents > Files**
  (`backend/open_webui/config.py:981-1000`; `src/lib/components/admin/Settings/Documents.svelte:1454-1523`).
  Messages: `File size should not exceed {maxSize} MB.`,
  `You can only chat with a maximum of {maxCount} file(s) at a time.`, `[ERROR: File type {file_extension} is not allowed]` (sections 5.6, 10).
- **Who can open a file.** The uploader, any admin, and people who can read a knowledge base, channel,
  shared chat or workspace model that contains it; everyone else gets
  `We could not find what you're looking for :/` (`backend/open_webui/utils/access_control/files.py:19-102`;
  `backend/open_webui/routers/files.py:605-621`).
- **The Files manager.** **Settings > Data Controls > Manage Files > Manage** lists the user's uploads
  (an admin sees everyone's while `BYPASS_ADMIN_ACCESS_CONTROL` is on), with search, sort, a viewer and
  a delete button; **Shift**-clicking the bin deletes without asking
  (`src/lib/components/chat/Settings/DataControls.svelte:245-259`;
  `src/lib/components/layout/FilesModal.svelte:361-373`).
- **Deleting is permanent.** The row, the stored bytes and the file's vectors are removed, and the file
  is taken out of every knowledge base (`backend/open_webui/routers/files.py:1013-1068`). Chats keep
  showing the attachment, but images then read `Image unavailable` and the file's text is no longer
  sent to the model. Deleting a chat or a user does **not** delete files.
- **Admin "Reset Upload Directory" deletes far more than its label says.** The button in
  **Admin Settings > Documents > Danger Zone** calls the delete-all endpoint, which removes every file
  record, every stored file and resets the whole vector store, including knowledge-base and memory
  vectors (`src/lib/components/admin/Settings/Documents.svelte:354-366`;
  `backend/open_webui/routers/files.py:575-597`).
- **Previews run in the browser:** PDF, Word (`.docx`), PowerPoint (`.pptx`, drawn approximately),
  Excel and CSV (as tables), images (pan and zoom), audio, code and Markdown
  (`src/lib/components/common/FileItemModal.svelte:69-139`, `:392-593`).
- **Cloud pickers** (Google Drive, OneDrive) are off by default and need admin switches plus
  environment-only client identifiers; OneDrive failures are not shown to the user (section 5.15, 5.16).
- **Storage full.** An upload that cannot be written fails with `[ERROR: {strerror}]`, the operating
  system's own wording; the friendlier `[ERROR: The server is out of storage space.]` texts in
  `backend/open_webui/constants.py:6-13` appear only on paths that pass the error itself, such as audio
  transcription (section 5.20).
- **Local customisations:** none in this area; it matches upstream Open WebUI v0.11.4 (section 12).
- **Neighbouring documents.** Extraction engines, chunking, embedding and retrieval:
  `rag-retrieval-embeddings-and-vector-stores.md`. Knowledge bases: `knowledge-bases.md`. The composer
  and how attachments appear in messages: `chat-composer-and-message-display.md`. Permissions and groups:
  `users-groups-roles-and-permissions.md`. Hosting, volumes and logs:
  `deployment-operations-and-logging.md`.

## 1. Purpose and Who Uses It

Files are how people bring their own material into MedIT GPT: a PDF to summarize, a spreadsheet to
analyse, a photo for a vision model, a recording to transcribe, or a set of documents for a knowledge
base. This area covers the life of a file from the moment it is picked to the moment it is deleted:
the upload, what the server stores, how the text is extracted and made searchable, who can open it,
how it is previewed, and what deleting it does. Tier 1 meets this area through upload errors, yellow
warnings after an upload, files that "the AI can't see", missing previews and questions about where
files are kept and who can see them.

Who uses it:

- **Every signed-in account with the role `user` or `admin`.** The upload endpoint accepts any
  verified account (`backend/open_webui/routers/files.py:280-289`; `get_verified_user` admits `user`
  and `admin`, ground truth). Accounts with the role `pending` cannot reach the chat screen.
- **Users who lack upload rights** (the `chat.file_upload` permission, on by default) see the upload
  items greyed out in the chat composer (section 3.1).
- **Admins** additionally set the limits and integrations in **Admin Settings > Documents**, see every
  user's files in the Files manager while `BYPASS_ADMIN_ACCESS_CONTROL` is on, can open or delete any
  file, and can delete all files at once (section 3.4).
- **Knowledge-base editors, channel members and note writers** upload through the same endpoint;
  those screens are documented in their own areas and are cross-referenced here only for what happens
  to the file.

Files contain whatever people upload. On a medical deployment that can include personal health
information in the file content **and in the file name**, which is kept in the database, in the stored
object's name (`{id}_{original name}`) and, with S3 tagging on, next to the uploader's email in the
cloud provider's object tags (section 6.5). Support staff should treat file names, previews and the
Files manager as personal data.

What this area does **not** cover in depth: extraction engines, chunking, embedding models and
retrieval (`rag-retrieval-embeddings-and-vector-stores.md`); the knowledge-base screens
(`knowledge-bases.md`); the composer's buttons and how attachments render in messages
(`chat-composer-and-message-display.md`); files inside a terminal server beyond the side-panel browser
(`workspace-tools-tool-servers-mcp-and-terminals.md`); code-interpreter files
(`code-execution-and-interpreter.md`).

## 2. Navigation and URLs

### 2.1 Screens and Entry Points

URLs are relative to the site root; the production host is **TO BE CONFIRMED**.

| Where | How to get there | What it offers | Source |
|---|---|---|---|
| Chat composer **+** menu | `/` (new chat) or `/c/{id}`; the **+** button (accessible name `More`) left of the input | **Upload Files**, **Capture**, **Attach Files** (earlier uploads), **Google Drive**, **Microsoft OneDrive** and other attachment types | `src/lib/components/chat/MessageInput/InputMenu.svelte:126-720`; `src/lib/components/chat/MessageInput.svelte:2223-2290` |
| Drop zone | Drag files over the chat; a blurred overlay reads `Add Files` / `Drop any files here to upload` | Drag-and-drop upload | `src/lib/components/chat/Chat.svelte:4295`; `src/lib/components/chat/MessageInput/FilesOverlay.svelte:10-27`; `src/lib/components/AddFilesPlaceholder.svelte:9-27` |
| Files manager | **Settings > Data Controls > Files > Manage Files > Manage**; deep link `/?settings=data_controls` | List, search, sort, open and delete uploads | `src/lib/components/chat/Settings/DataControls.svelte:245-259`; `src/lib/components/layout/FilesModal.svelte:203-409`; `src/routes/(app)/+layout.svelte:165-193`; `src/lib/components/chat/SettingsModal.svelte:100-115` |
| File viewer | Click a file chip in the composer or in a sent message, or a row in the Files manager | Extracted text, previews, download link | `src/lib/components/common/FileItem.svelte:54-81`; `src/lib/components/common/FileItemModal.svelte:257-601` |
| Admin file settings | `/admin/settings/documents`, which redirects to `/?settings=admin:documents`; in Settings it is **Documents** in the admin group | **Files** (limits, compression), **Integration** (Google Drive, OneDrive), **Danger Zone** | `src/routes/(app)/admin/settings/[tab]/+page.svelte:6-10`; `src/lib/components/chat/SettingsModal.svelte:335-338`, `:873-874`; `src/lib/components/admin/Settings/Documents.svelte:1454-1589` |
| Personal file settings | **Settings > Interface**: section **File** (**Default Upload Mode**, **Image Compression**, **Compress Images in Channels**), section **Chat** (**Render Markdown in Previews**), section **Input** (**Paste Large Text as File**) | Per-user upload behaviour | `src/lib/components/common/InterfaceSettings.svelte:1039`, `:1712`, `:1901-1994` |
| Side panel **Files** tab | In a chat, open the controls panel; the **Files** tab appears when a terminal is selected (terminal file browser) or the code interpreter is on with the browser engine (Pyodide files) | Browse, preview, upload into a terminal's file system | `src/lib/components/chat/ChatControls.svelte:76-85`, `:238-247`, `:295-298` |

The English names above resolve from dotted keys in `src/lib/i18n/locales/en-US/translation.json`:
`Data Controls` (`:2816`), `Files` (`:2813`), `Manage Files` (`:2811`), `Documents` (`:2350`),
section `Files` (`:2335`), `Integration` (`:2336`), `Danger Zone` (`:2333`), `File` (`:2969`),
`Default Upload Mode` (`:2900`), `Image Compression` (`:2933`), `Compress Images in Channels` (`:2895`),
`Render Markdown in Previews` (`:2958`), `Paste Large Text as File` (`:2950`).

### 2.2 Server Endpoints

All are mounted under `/api/v1/files` (`backend/open_webui/main.py:875`) and require a signed-in `user`
or `admin` account. "Read" and "write" access are defined in section 3.

| Method and path | What it does | Who may call it | Source |
|---|---|---|---|
| `POST /api/v1/files/` | Upload one file (form fields `file`, optional `metadata`; query `process`, default true, and `process_in_background`, default true) | Any signed-in user | `backend/open_webui/routers/files.py:280-478` |
| `GET /api/v1/files/?page={n}` | List files, 50 per page, newest change first | Own files; admins see all while `BYPASS_ADMIN_ACCESS_CONTROL` is on | `backend/open_webui/routers/files.py:486-506`; `backend/open_webui/models/files.py:254-272` |
| `GET /api/v1/files/search?filename={pattern}` | Search names with `*` and `?` wildcards, newest upload first (up to 1,000 per page) | As above | `backend/open_webui/routers/files.py:514-553`; `backend/open_webui/models/files.py:274-329` |
| `GET /api/v1/files/count` | Number of files | As above | `backend/open_webui/routers/files.py:561-567` |
| `DELETE /api/v1/files/all` | Delete every file and reset the vector store | Admins only | `backend/open_webui/routers/files.py:575-597` |
| `GET /api/v1/files/{id}` | The file record, including extracted text | Read access | `backend/open_webui/routers/files.py:605-621` |
| `GET /api/v1/files/{id}/process/status` | Processing status; `?stream=true` sends updates every second until `completed` or `failed` (at most two hours) | Read access | `backend/open_webui/routers/files.py:624-680` |
| `GET /api/v1/files/{id}/data/content` | Extracted text only | Read access | `backend/open_webui/routers/files.py:688-706` |
| `POST /api/v1/files/{id}/data/content/update` | Replace the extracted text and re-embed it, including in knowledge bases | Write access | `backend/open_webui/routers/files.py:714-787` |
| `GET /api/v1/files/{id}/content` | The file itself; `?attachment=true` forces a download | Read access | `backend/open_webui/routers/files.py:795-855` |
| `GET /api/v1/files/{id}/content/html` | The file served raw for embedding as HTML; refused unless the file's owner is an admin | Read access and an admin-owned file | `backend/open_webui/routers/files.py:858-904` |
| `GET /api/v1/files/{id}/content/{file_name}` | Download as an attachment; if no stored bytes exist, the extracted text as plain text | Read access | `backend/open_webui/routers/files.py:907-957` |
| `POST /api/v1/files/{id}/rename` | Rename | Write access | `backend/open_webui/routers/files.py:965-1005` |
| `DELETE /api/v1/files/{id}` | Delete one file | Write access | `backend/open_webui/routers/files.py:1013-1068` |

Related endpoints outside this router: `POST /api/v1/retrieval/process/file` re-processes a file (the
owner, or any file for an admin; `backend/open_webui/routers/retrieval.py:1925-1941`);
`POST /api/v1/retrieval/config/update` saves the admin limits (`:962`, `:1279-1310`);
`POST /api/v1/retrieval/reset/uploads` empties the upload folder only, and no screen calls it
(`backend/open_webui/routers/retrieval.py:3287-3316`; its client `resetUploadDir` in
`src/lib/apis/retrieval/index.ts:533` has no caller). The browser client for the files router is
`src/lib/apis/files/index.ts`; its `uploadDir` function calls `POST /api/v1/files/upload/dir`, which does
not exist on the server, and nothing calls it (`src/lib/apis/files/index.ts:122-146`).

## 3. Roles and Permissions

Every check below is made on the server unless it says "in the browser". Refusals of read or write
access answer HTTP 404 with the `NOT_FOUND` text `We could not find what you're looking for :/`, the
same answer as for a file that does not exist (`backend/open_webui/constants.py:78`;
`backend/open_webui/routers/files.py:609-621`), so support cannot tell "deleted" from "not yours" by
the message alone.

### 3.1 Who Can Upload

| Rule | Where enforced | Source |
|---|---|---|
| Any signed-in `user` or `admin` account may call the upload endpoint | Server | `backend/open_webui/routers/files.py:280-289` |
| In the chat composer, a non-admin needs the `chat.file_upload` permission (default on, `USER_PERMISSIONS_CHAT_FILE_UPLOAD`); without it the upload items are greyed and dropped or pasted files are refused with `You do not have permission to upload files.` | Browser | `backend/open_webui/config.py:1857`, `:1983`; `src/lib/components/chat/MessageInput.svelte:918-922`; `src/lib/components/chat/MessageInput/InputMenu.svelte:67-70`, `:188-192` |
| Every selected model must have the `file_upload` capability (a capability that is not set counts as on); otherwise `Model(s) do not support file upload` | Browser | `src/lib/components/chat/MessageInput.svelte:759-773`, `:924-929` |
| Images additionally need every selected model to have the `vision` capability: `Selected model(s) do not support image inputs` | Browser | `src/lib/components/chat/MessageInput.svelte:1126-1130` |
| The **Google Drive** and **Microsoft OneDrive** items are shown only when uploads are allowed and the admin switches are on | Browser | `src/lib/components/chat/MessageInput/InputMenu.svelte:393-437` |
| An upload sent from a knowledge base is linked to it only if the uploader owns the knowledge base, is an admin or has write access; otherwise the file is stored but left unlinked and a log warning is written | Server | `backend/open_webui/routers/files.py:201-225` |
| An upload sent from a channel is linked to the channel only if the uploader can access that channel | Server | `backend/open_webui/routers/files.py:430-433`; `backend/open_webui/models/channels.py:778-790` |

On the server, the `chat.file_upload` permission is otherwise used only to decide whether the model is
offered the built-in chat-file tools (`list_chat_files`, `query_chat_files`, `grep_chat_files`,
`view_file`; `backend/open_webui/utils/tools.py:585-600`; see `builtin-native-tools.md`). Whether the
upload endpoint itself should enforce the permission is a security question listed in section 14.

### 3.2 Who Can Open, Preview or Download a File (Read Access)

A person may read a file (see its record and extracted text, its status, preview it or download it)
when any of these is true (`backend/open_webui/routers/files.py:615`, `:642`, `:700`, `:810`, `:877`,
`:919`; `backend/open_webui/utils/access_control/files.py:19-102`):

1. **They uploaded it.**
2. **They are an admin.** Any admin passes every per-file check, whatever `BYPASS_ADMIN_ACCESS_CONTROL`
   says.
3. **A knowledge base contains it** and they own that knowledge base or have read access to it (shared
   with them, a group they are in, or everyone) (`backend/open_webui/utils/access_control/files.py:45-64`).
4. **It was posted in a channel they can read**: an active member of a group or direct-message channel,
   or anyone with read permission on a standard channel; deleted and archived channels do not count
   (`backend/open_webui/utils/access_control/files.py:66-69`; `backend/open_webui/models/channels.py:715-776`).
5. **It was attached in a chat that has an active share link** and they have read access to that share
   (`backend/open_webui/utils/access_control/files.py:71-83`; `backend/open_webui/models/chats.py:2656-2664`).
   Only files recorded in the `chat_file` table count (section 6.3).
6. **A workspace model lists it directly in its knowledge, or uses it as its background image**, and they
   own that model or have read access to it (`backend/open_webui/utils/access_control/files.py:85-102`;
   `backend/open_webui/models/models.py:290-309`).

In a chat, a file that belongs to a project folder can also be used for answers by anyone who can read
the folder, provided the folder's owner can read the file; this grants use in answers, not download
(`backend/open_webui/retrieval/utils.py:1389-1406`, `:1522-1561`;
`backend/open_webui/utils/access_control/files.py:176-186`). Folders are covered in
`chat-conversations-history-and-organisation.md`.

### 3.3 Who Can Rename, Replace the Text or Delete (Write Access)

Write access (rename, replace extracted text, delete) is narrower
(`backend/open_webui/routers/files.py:734`, `:985`, `:1025`;
`backend/open_webui/utils/access_control/files.py:45-102`):

1. The uploader.
2. Any admin.
3. Someone with write access to a knowledge base containing the file, **only if the knowledge base's
   owner is also the person who uploaded the file**.
4. Someone who owns, or has write access to, a workspace model that lists the file directly, **only if
   the model's owner is also the uploader**.

Channel membership and shared chats never give write access
(`backend/open_webui/utils/access_control/files.py:68`, `:73`).

### 3.4 Admins

| What admins can do | Source |
|---|---|
| Open, preview, download, rename, replace the text of and delete **any** file by its id | `backend/open_webui/routers/files.py:615`, `:642`, `:700`, `:734`, `:810`, `:877`, `:919`, `:985`, `:1025` |
| See **every user's** files in the Files manager, the count and the composer's **Attach Files** list while `BYPASS_ADMIN_ACCESS_CONTROL` is on (default on; environment-only, live value TO BE CONFIRMED); with it off they see only their own | `backend/open_webui/routers/files.py:497`, `:531`, `:566`; `backend/open_webui/config.py:2086-2092`; `src/lib/components/chat/MessageInput/InputMenu/Files.svelte:61-82` |
| Delete all files at once (**Reset Upload Directory**, section 5.13) | `backend/open_webui/routers/files.py:575-577`; `src/lib/components/admin/Settings/Documents.svelte:354-366` |
| Re-process any file | `backend/open_webui/routers/retrieval.py:1938-1941` |
| Change the upload limits, compression and cloud-picker switches | `backend/open_webui/routers/retrieval.py:962`, `:1279-1310` |

Because the Files manager shows everyone's file names to an admin, and file names can identify
patients or staff, admin use of that screen is itself access to personal data.

### 3.5 What the Rules Do Not Cover

- **Notes.** The access module has no rule for notes. A note keeps its attachments in its own
  `data.files` list (`src/lib/components/notes/NoteEditor.svelte:489-564`), but sharing a note grants
  nothing on those files through `backend/open_webui/utils/access_control/files.py:19-102`. Whether a
  note's collaborators can open its attachments is TO BE CONFIRMED (section 14).
- **Files of deleted users.** Deleting a user leaves their files in place (ground truth); afterwards
  only admins, and the knowledge-base, channel, model and shared-chat paths above, reach them.
- **Folder entries** are filtered by `get_accessible_folder_files`, which drops any entry the caller
  cannot read (`backend/open_webui/utils/access_control/files.py:105-158`).

## 4. Key Concepts and Terminology

| Term | Meaning in MedIT GPT | Source |
|---|---|---|
| **File (record)** | One row in the `file` table: id, owner, name, storage path, extracted text and status (`data`), and descriptive metadata (`meta`) | `backend/open_webui/models/files.py:18-31` |
| **Stored object** | The uploaded bytes, kept by the storage provider; the row's `path` says where | `backend/open_webui/storage/provider.py:62-356` |
| **Storage provider** | Where bytes are kept: `local` (default), `s3`, `gcs` or `azure`, chosen by the environment variable `STORAGE_PROVIDER` at startup | `backend/open_webui/config.py:150`; `backend/open_webui/storage/provider.py:338-356` |
| **Local copy (cache)** | Cloud providers first write the file to `DATA_DIR/uploads` and keep it there unless `STORAGE_LOCAL_CACHE` is false | `backend/open_webui/config.py:151`; `backend/open_webui/routers/files.py:97-108` |
| **Processing** | What happens after an upload: extract text (or transcribe audio), save the text on the row, embed it, set the status. Skipped for uploads sent with `process=false` (images from the chat composer, generated images and audio) | `backend/open_webui/routers/files.py:128-277`, `:435-465` |
| **Extracted text** (content) | The plain text taken from the file, stored in `data.content`; it is what the model reads when the whole document is used | `backend/open_webui/routers/retrieval.py:2063-2068` |
| **Embedding** and **collection `file-{id}`** | The extracted text split into chunks and stored in the vector store under a collection named after the file, used for focused retrieval | `backend/open_webui/routers/retrieval.py:1946-1950`, `:2091-2128` |
| **Bypass embedding** | Admin switch (`rag.bypass_embedding_and_retrieval`) that stops processing after text extraction; the file is marked `completed` without vectors | `backend/open_webui/routers/retrieval.py:2070-2090`; `backend/open_webui/config.py:965`, `:2898` |
| **Processing status** | `data.status` on the row: `pending`, `processing`, `completed` or `failed` (section 5.5) | `backend/open_webui/routers/files.py:416`, `:238`, `:259-268` |
| **Chip** | The small tile for an attachment in the composer or a message. Its own browser-side states are `uploading` (spinner), `uploaded`, `error` (the chip is removed) and `processed` (references such as knowledge bases or chats) | `src/lib/components/chat/MessageInput.svelte:931-947`, `:2002-2011`; `src/lib/components/chat/MessageInput/InputMenu.svelte:92-104` |
| **Focused Retrieval / Entire Document** | Per-file choice shown as `Using Focused Retrieval` or `Using Entire Document`: send only the passages that match the question, or the whole extracted text (`context: 'full'`). The personal default is **Default Upload Mode** | `src/lib/components/common/FileItemModal.svelte:347-373`; `src/lib/components/chat/MessageInput.svelte:943-945`; `src/lib/components/common/InterfaceSettings.svelte:1904-1928` |
| **Allowed File Extensions** | Admin list of permitted extensions; empty means all. Compared with the file's lower-case extension without the dot | `backend/open_webui/routers/files.py:350-362` |
| **Max Upload Size** | Admin limit in megabytes, checked in the browser before upload and on the server after the bytes are written | `src/lib/components/chat/MessageInput.svelte:1106-1124`; `backend/open_webui/routers/files.py:394-400` |
| **Max Upload Count** | Admin limit on files attached to one message, checked in the composer only | `src/lib/components/chat/MessageInput.svelte:1087-1101` |
| **Image compression** | Shrinking images in the browser before upload: by the user's own choice and capped by the admin's maximum width and height | `src/lib/components/chat/MessageInput.svelte:1132-1170` |
| **Files manager** | The window opened from **Settings > Data Controls > Manage Files** listing uploads | `src/lib/components/layout/FilesModal.svelte` |
| **File viewer** | The window that opens when a file chip or Files-manager row is clicked: **Content** and **Preview** tabs | `src/lib/components/common/FileItemModal.svelte` |
| **Temporary chat** | A chat that is not saved; its attachments are read in the browser and not sent to MedIT GPT's file storage (a terminal set to receive chat uploads still receives them) | `src/lib/components/chat/MessageInput.svelte:1050-1083`, `:1172-1183` |
| **Cloud picker** | The Google Drive or Microsoft OneDrive window that downloads a chosen file into the browser and then uploads it as a normal file | `src/lib/utils/google-drive-picker.ts:107-212`; `src/lib/utils/onedrive-file-picker.ts:285-452` |
| **`chat_file` link** | A row recording that a file was attached to a message in a chat; used for shared-chat access | `backend/open_webui/models/chats.py:217-230` |
| **Content hash** | `file.hash`: SHA-256 of the extracted text, set after processing and cleared on failure. Separate from `meta.file_hash`, the SHA-256 of the raw bytes taken at upload | `backend/open_webui/routers/retrieval.py:2069`, `:2164-2165`; `backend/open_webui/routers/files.py:402-406` |
| **Terminal file browser** | The side panel's **Files** tab when a terminal is selected: a browser for the terminal server's own file system, not for MedIT GPT's stored files | `src/lib/components/chat/FileNav.svelte` |

## 5. Workflows (Step by Step)

### 5.1 Ways to Upload (What the User Does)

| Method | What the user does | What happens next | Source |
|---|---|---|---|
| **Upload Files** | **+** > **Upload Files**, then pick one or more files in the system dialogue (any type; several at once) | Each file goes through the checks in 5.2. If the dialogue returns nothing: `File not found.` | `src/lib/components/chat/MessageInput/InputMenu.svelte:195-210`; `src/lib/components/chat/MessageInput.svelte:1716-1730` |
| **Drag and drop** | Drag files over the chat; a blurred overlay reads `Add Files` and `Drop any files here to upload`; drop them | Same checks as **Upload Files**. Chats, folders and notes dragged from the sidebar become references instead of uploads | `src/lib/components/chat/MessageInput.svelte:1218-1326`; `src/lib/components/AddFilesPlaceholder.svelte:9-27` |
| **Paste** | Paste a copied image or file into the message box | Same checks. Pasted plain text longer than 1,000 characters becomes a file named `Pasted_Text_{timestamp}.txt`, sent as **Entire Document**, when **Paste Large Text as File** is on (default off); holding Shift while pasting keeps it as text | `src/lib/components/chat/MessageInput.svelte:2180-2214`; `src/lib/constants.ts:130`; `src/lib/components/common/InterfaceSettings.svelte:58`, `:1712` |
| **Capture** | **+** > **Capture**. On a computer the browser asks which screen to share and one frame is taken; on a phone the camera opens | The frame becomes `screen-capture-{timestamp}.png`; a camera photo keeps its own name. Both go through the image checks | `src/lib/components/chat/MessageInput/InputMenu.svelte:116-123`, `:221-243`; `src/lib/components/chat/MessageInput.svelte:861-897` |
| **Attach Files** | **+** > **Attach Files**, search earlier uploads (listed 50 at a time) and pick one | Nothing is uploaded again; the existing file is added to the message | `src/lib/components/chat/MessageInput/InputMenu.svelte:92-104`, `:270-298`; `src/lib/components/chat/MessageInput/InputMenu/Files.svelte:61-82` |
| **Google Drive** / **Microsoft OneDrive** | **+** > **Google Drive**, or **Microsoft OneDrive** > **Microsoft OneDrive (personal)** or **Microsoft OneDrive (work/school)** | The chosen file is downloaded into the browser, then uploaded as a normal file (sections 5.15, 5.16) | `src/lib/components/chat/MessageInput.svelte:2242-2276` |
| Prompt with `{{CLIPBOARD}}` | Use a saved prompt that contains the clipboard variable | Images found on the clipboard are added as `clipboard-image.{type}` | `src/lib/components/chat/MessageInput.svelte:288-305` |

Other screens use the same server endpoint: knowledge bases (with `knowledge_id` in the metadata,
`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:347-351`, `:636-640`), channels
(`src/lib/components/channel/MessageInput.svelte:475`) and notes
(`src/lib/components/notes/NoteEditor.svelte:525`). Their screens are documented in their own areas.

### 5.2 What the Browser Checks Before Uploading (Chat Composer)

For **Upload Files**, drag and drop, paste and **Capture**, the composer applies these steps in order
(`src/lib/components/chat/MessageInput.svelte:1087-1197`, `:918-1084`):

1. **Count** (whole batch): if the admin set **Max Upload Count** and the files already attached plus
   the new ones exceed it, nothing is added:
   `You can only chat with a maximum of {maxCount} file(s) at a time.` (`:1089-1101`).
2. **Size** (each file): above **Max Upload Size**: `File size should not exceed {maxSize} MB.`
   (`:1106-1124`).
3. **Raster images** (any `image/` type except SVG, `src/lib/utils/index.ts:972-975`): every selected
   model needs vision (`Selected model(s) do not support image inputs`); the image is shrunk if
   compression applies (5.7); iPhone HEIC photos are converted to JPEG first; then the image goes to
   the upload step below, but **without processing** (`process=false`) (`:1126-1192`). In a temporary
   chat it is kept inside the message instead (5.8).
4. **Everything else** goes to the upload step:
   - permission check (`You do not have permission to upload files.`, `:919-922`);
   - capability check (`Model(s) do not support file upload`, `:924-929`);
   - empty file check (`You cannot upload an empty file.`, `:949-952`);
   - if the selected terminal is set to receive chat uploads, the file is written to the terminal's
     working folder instead of MedIT GPT storage (`:899-916`, `:956-999`);
   - in a temporary chat the text is read in the browser instead (5.8);
   - otherwise the file is uploaded with processing on, the chip shows a spinner, and for audio or
     video the user's speech-to-text language is sent along (`:1002-1016`).

**Exceptions.** Cloud-picker files and pasted long text go straight to the upload step
(`src/lib/components/chat/MessageInput.svelte:2203`, `:2249`, `:2269`), so the browser's count and size checks and the image path are skipped for
them; the server's size check still applies (5.3). Sending a message while a chip is still uploading
queues the message until the upload finishes (`src/lib/components/chat/Chat.svelte:3175-3188`; the
queue is described in `chat-composer-and-message-display.md`). Removing a chip with its **x** only
takes it off the message; the uploaded file stays in the Files manager
(`src/lib/components/chat/MessageInput.svelte:2012-2016`).

### 5.3 What the Server Does With an Upload

`upload_file_handler` (`backend/open_webui/routers/files.py:324-478`):

1. **Reads the metadata** sent with the file (for example `language`, `knowledge_id`, `directory_id`,
   `channel_id`, `source_url`, `file_hash`). Unreadable metadata: `[ERROR: Invalid metadata format]`
   (`:336-344`).
2. **Checks the extension** against **Allowed File Extensions**, only when processing was requested
   (`:350-362`), so images from the composer and generated files are never refused by this list.
3. **Names the stored object** `{new id}_{original name}` (the code comment prefers "readable storage
   names for admins") and prepares storage tags with the uploader's email, user id, name and the file id (`:364-373`).
4. **Writes the bytes** through the storage provider (`:374-393`). If the operating system says the name
   is too long, it retries once as `{id}.{extension}`; any other operating-system error ends the upload
   with `[ERROR: {strerror}]` (section 5.20). A zero-byte file is refused with the `EMPTY_CONTENT` text
   (`backend/open_webui/storage/provider.py:64-67`; `backend/open_webui/routers/files.py:469-478`).
5. **Checks the size** against **Max Upload Size** after writing; an oversized file is deleted again and
   refused with HTTP 413 and
   `Oops! The file you're trying to upload is too large. Please upload a file that is less than {max_size} MB.` (`:394-400`; `backend/open_webui/constants.py:105-107`).
6. **Fingerprints the bytes** with SHA-256 unless the browser already supplied one (`:402-406`).
7. **Creates the row**: display name, storage path, `data.status = 'pending'` when processing, and
   `meta` with name, content type, size, the fingerprint and the browser's metadata (`:408-428`).
8. **Links channel uploads** to the channel when the uploader can access it (`:430-433`).
9. **Starts processing** (5.4), by default as a background task after the response is sent, returning
   the new row at once; callers may ask for it to run before the response (`:435-457`). Uploads with
   `process=false` return the row with no status (`:458-465`).
10. **Publishes the `file.uploaded` event** with the file name and content type (`:314-320`; section 9).

Any other unexpected error ends with `[ERROR: Error uploading file]` (`:469-478`).

### 5.4 Processing: Extraction, Transcription and Embedding

`process_uploaded_file` (`backend/open_webui/routers/files.py:128-277`) decides what to do from the
file's content type:

| Kind of file | What happens | Source |
|---|---|---|
| Labelled as image or video but actually text (for example a `.ts` source file the browser calls `video/mp2t`) | The first 8 KB are inspected; no NUL bytes means it is treated as plain text and processed as a document | `backend/open_webui/routers/files.py:66-94`, `:141-144` |
| Audio, and `video/webm`, matching **speech-to-text supported content types** (when that admin list is empty the code uses `audio/*` and `video/webm`) | Transcribed with the configured speech-to-text engine; the transcript is then processed as the file's text | `backend/open_webui/routers/files.py:146-166`; `backend/open_webui/utils/misc.py:1204-1208`; `backend/open_webui/config.py:1590-1594` |
| Video not enabled for the extraction engine | Stored as is and marked `completed` with no text, for tools and vision models to use | `backend/open_webui/routers/files.py:168-185` |
| Image not enabled for the extraction engine (only reached when an image is uploaded **with** processing, for example from a cloud picker or a knowledge base) | Marked `failed` with `File type {content_type} is not supported for processing` | `backend/open_webui/routers/files.py:186-187`, `:259-268` |
| Everything else (documents, text, code, spreadsheets, presentations, and media the admin enabled for the extraction engine) | `process_file` loads the file with the configured extraction engine, stores the text, then embeds it into collection `file-{id}` unless embedding is bypassed, and marks it `completed` | `backend/open_webui/routers/files.py:189-199`; `backend/open_webui/routers/retrieval.py:2017-2153` |

When the upload came from a knowledge base the uploader may write to, the server then sets the status
back to `processing`, adds the file's chunks to the knowledge base's collection and records the link,
before the file counts as finished (`backend/open_webui/routers/files.py:201-257`). Any failure marks
the file `failed` with the error text (`:259-268`); the retrieval step's own failure handler also clears
the content hash so the same file can be uploaded again after the cause is fixed, and publishes
`retrieval.content.process_failed` (`backend/open_webui/routers/retrieval.py:2155-2186`). Finally the
local copy is removed when cloud storage is used with `STORAGE_LOCAL_CACHE` off (`:270-277`).

The extraction engines (built-in loaders, Tika, Docling, document intelligence services and others),
chunk sizes, embedding models and the **Bypass Embedding and Retrieval** switch are documented in
`rag-retrieval-embeddings-and-vector-stores.md`.

### 5.5 Processing Status Values

| Value | Meaning | Where it is set | What the user sees |
|---|---|---|---|
| `pending` | Uploaded and waiting for, or in the middle of, processing. Also what the non-streaming status call reports when a file has no status at all | `backend/open_webui/routers/files.py:416`, `:675` | Spinner on the chip |
| `processing` | Text extracted; now being added to a knowledge base | `backend/open_webui/routers/files.py:236-238` | Spinner (knowledge-base screens show pending files separately, `backend/open_webui/models/files.py:407-443`) |
| `completed` | Text extracted and, unless bypassed, embedded; or a video stored without extraction | `backend/open_webui/routers/retrieval.py:2072`, `:2129-2133`; `backend/open_webui/routers/files.py:181-185` | Chip finishes; the file is usable |
| `failed` | Processing stopped; `data.error` holds the reason | `backend/open_webui/routers/files.py:259-268`; `backend/open_webui/routers/retrieval.py:2159-2163` | A **yellow warning pop-up** with the reason; the chip still finishes and stays attached |
| (none) | Uploaded with `process=false`: composer images, generated images and audio, model background images | `backend/open_webui/routers/files.py:416`, `:458-460` | Nothing to wait for |
| `not_found` | Sent only by the status stream if the file disappears while being watched | `backend/open_webui/routers/files.py:664-666` | The stream ends |

**How the browser follows it.** After the upload returns, the browser opens
`/api/v1/files/{id}/process/status?stream=true` and reads one update per second until `completed` or
`failed`, for at most 7,200 updates (about two hours) (`src/lib/apis/files/index.ts:46-89`;
`backend/open_webui/routers/files.py:643-673`). If the last update carries an error, the composer shows
it with `toast.warning` and still marks the chip `uploaded` (`src/lib/components/chat/MessageInput.svelte:1018-1037`).
The model may then have little or nothing to read from that file. A file with no status ends the
stream at once (`backend/open_webui/routers/files.py:661-663`).

No background job resumes or retries processing: work runs as a task inside the server process that
received the upload (section 8). What a user sees if that process restarts mid-processing is
TO BE CONFIRMED (section 14).

### 5.6 Allowed Types and Size and Count Limits

There is no built-in list of permitted types: any file may be uploaded, and what text can be extracted
depends on the extraction engine (`rag-retrieval-embeddings-and-vector-stores.md`). Three admin limits
exist, all empty (unlimited) in code; live values are data in the `config` table and are
**TO BE CONFIRMED**.

| Limit | Admin field and setting | Checked where | Message | Source |
|---|---|---|---|---|
| Allowed extensions | **Allowed File Extensions** (help text `Comma-separated upload extensions. Leave empty for all file types.`, placeholder `e.g. pdf, docx, txt`); `rag.file.allowed_extensions`, seeded from `RAG_ALLOWED_FILE_EXTENSIONS` | Server, at upload, only when processing is requested | `[ERROR: File type {file_extension} is not allowed]` | `backend/open_webui/routers/files.py:350-362`; `backend/open_webui/config.py:998-1000`, `:2910`; `src/lib/components/admin/Settings/Documents.svelte:1455-1466`; `src/lib/i18n/locales/en-US/translation.json:2198-2199` |
| Size | **Max Upload Size** (`Maximum file size in MB. Leave empty for unlimited.`); `rag.file.max_size`, seeded from `RAG_FILE_MAX_SIZE` | Browser, for files picked, dropped, pasted or captured; server, for every upload and for replacing a file's extracted text | Browser: `File size should not exceed {maxSize} MB.` Server: `Oops! The file you're trying to upload is too large. Please upload a file that is less than {max_size} MB.` | `src/lib/components/chat/MessageInput.svelte:1106-1124`; `backend/open_webui/routers/files.py:394-400`, `:735-740`; `backend/open_webui/config.py:983`, `:2907`; `src/lib/i18n/locales/en-US/translation.json:2281-2282` |
| Count | **Max Upload Count** (`Maximum number of files that can be used at once in chat.`); `rag.file.max_count`, seeded from `RAG_FILE_MAX_COUNT` | Chat composer only, counting files already attached to the message plus the new ones; the files router has no count check | `You can only chat with a maximum of {maxCount} file(s) at a time.` | `src/lib/components/chat/MessageInput.svelte:1087-1101`; `backend/open_webui/config.py:981`, `:2906`; `src/lib/i18n/locales/en-US/translation.json:2279-2280` |

Points that explain odd refusals:

- **The extension list must be lower case without dots.** The server lower-cases the file's extension
  and drops the dot, then looks for an exact match in the list as entered; the admin screen only trims
  spaces (`backend/open_webui/routers/files.py:350-358`;
  `src/lib/components/admin/Settings/Documents.svelte:272-274`). An entry such as `PDF` or `.pdf` blocks
  every PDF. A file with no extension is refused whenever a list is set, and the message then shows
  nothing where the type belongs.
- **The extension list does not apply to uploads without processing**: images from the chat composer,
  generated images and audio, and model background images (`backend/open_webui/routers/files.py:355`).
- **The size limit also applies elsewhere**: images fetched from a web address to show a model are
  silently skipped above it (`backend/open_webui/utils/files.py:60-66`, `:90-93`), and web-address
  attachments are refused above it (`backend/open_webui/routers/retrieval.py:2245-2310`; see
  `web-search-and-web-loading.md`).
- The server checks size **after** the whole file has been written to storage, then deletes it, so a
  very large upload still travels to the server first (`backend/open_webui/routers/files.py:374-400`).

### 5.7 Image Compression

Images can be shrunk **in the browser** before they are uploaded. Personal and admin settings combine
(`src/lib/components/chat/MessageInput.svelte:1132-1170`):

| Setting | Where | Default | Effect |
|---|---|---|---|
| **Image Compression** | **Settings > Interface > File**; **Manage** opens `Image Max Compression Size` with width and height boxes | Off | Shrinks the user's images to their chosen size |
| **Compress Images in Channels** (`Apply image compression to channel uploads too.`) | Same section, shown only while **Image Compression** is on | On | Applies the user's choice to channel uploads too |
| **Image Compression Width** / **Image Compression Height** (`Width in pixels to compress images to. Leave empty for no compression.`) | **Admin Settings > Documents > Files**; `file.image_compression_width` and `file.image_compression_height`, seeded from `FILE_IMAGE_COMPRESSION_WIDTH` and `FILE_IMAGE_COMPRESSION_HEIGHT` | Empty | A cap for everyone: applied even when a user's own compression is off, and it wins when the user's size is larger |

Sources: `src/lib/components/common/InterfaceSettings.svelte:88-93`, `:1931-1994`;
`src/lib/components/chat/Settings/Interface/ManageImageCompressionModal.svelte:62-107`;
`src/lib/components/admin/Settings/Documents.svelte:1497-1523`; `backend/open_webui/config.py:989-995`,
`:2908-2909`; `src/lib/i18n/locales/en-US/translation.json:2273-2276`, `:2894-2895`, `:2933`.

The shrink keeps the aspect ratio, leaves images that already fit untouched and keeps the image type
(`src/lib/utils/index.ts:401-450`). The same rules run in channels (where the user's part needs both
switches) and in notes (`src/lib/components/channel/MessageInput.svelte:380-415`;
`src/lib/components/notes/NoteEditor.svelte:566-600`). iPhone HEIC photos are converted to JPEG before
compression (`src/lib/components/chat/MessageInput.svelte:1192`; `src/lib/utils/index.ts:2110-2120`).
No server code in this area resizes images; a search of `backend/open_webui` finds none.

### 5.8 Temporary Chats: Nothing Is Uploaded

In a temporary chat the composer never calls the upload endpoint
(`src/lib/components/chat/MessageInput.svelte:1002`, `:1050-1083`, `:1172-1183`). The one exception is a
selected terminal set to receive chat uploads, which is checked first and still receives the file
(`:956-999`):

- **Images** are kept inside the message as data (after compression, 5.7).
- **Other files** are read in the browser: PDF text (pdf.js), Word `.docx`, OpenDocument text,
  spreadsheet and presentation files, and anything text-like; other types are tried as text and
  otherwise fail with `Unsupported or non-text file type: {name}`
  (`src/lib/utils/index.ts:1910-2095`). A failure shows
  `Failed to extract content from the file: {error}` and `Failed to extract content from the file.`, and the chip is removed.
- Such files never appear in the Files manager and are not stored on the server.

### 5.9 The Files Manager

Opened from **Settings > Data Controls > Files > Manage Files > Manage**
(`src/lib/components/chat/Settings/DataControls.svelte:245-259`); the description reads
`Open the file manager for uploaded files.` (`src/lib/i18n/locales/en-US/translation.json:2810`).

| Part | Behaviour | Source |
|---|---|---|
| Title | `Files` and a number: the total from the server (for an admin with `BYPASS_ADMIN_ACCESS_CONTROL` on, every user's files), or while searching the number of matches loaded so far | `src/lib/components/layout/FilesModal.svelte:205-217`, `:75-77` |
| **Search Files** box | Finds names containing the typed text (case-insensitive), 300 ms after typing stops; up to 500 characters | `src/lib/components/layout/FilesModal.svelte:62-83`, `:149-155`, `:258-263`; `backend/open_webui/models/files.py:318-329` |
| **Filename** and **Created at** headings | Click to sort; sorting re-orders only the rows already loaded. The server sends newest uploads first | `src/lib/components/layout/FilesModal.svelte:52-60`, `:108-124`, `:285-328` |
| Rows | Name, size (B, KB, MB or GB), upload date (hover for date and time). There is no owner column, so an admin cannot see from this screen whose file a row is | `src/lib/components/layout/FilesModal.svelte:340-381` |
| Loading | 50 rows at a time; scrolling to the end shows `Loading...` and fetches more | `src/lib/components/layout/FilesModal.svelte:85-106`, `:383-398` |
| Empty | `No files found`, also shown when a search fails | `src/lib/components/layout/FilesModal.svelte:78-82`, `:332-338` |
| Click a row | Opens the file viewer in read-only mode (no focused or entire-document switch) | `src/lib/components/layout/FilesModal.svelte:138-147`, `:201` |
| Bin button (tooltip `Delete File`) | Asks `Confirm your action` / `This action cannot be undone. Do you wish to continue?`, then shows `File deleted successfully.`; with **Shift** held the bin turns red and deletes **without asking**. A refusal shows the server's text | `src/lib/components/layout/FilesModal.svelte:126-136`, `:191-199`, `:361-373`; `src/lib/components/common/ConfirmDialog.svelte:139-154` |

There is no rename, bulk delete or download button in this window; downloading is done from the file
viewer (5.11), and renaming exists only in the knowledge-base screen (`knowledge-bases.md`).

### 5.10 The File Viewer and Previews

Clicking a file chip (composer or message) or a Files-manager row opens the viewer
(`src/lib/components/common/FileItem.svelte:54-81`; `src/lib/components/common/FileItemModal.svelte`).
It reloads the file's record from the server each time it opens (`:200-247`).

| Part | Behaviour | Source |
|---|---|---|
| Title | The file name, a link that opens the file itself in a new tab (5.11); `File` when no name is known | `src/lib/components/common/FileItemModal.svelte:262-281` |
| Information line | Size; `{COUNT} extracted lines` (or `{COUNT} Rows` for a spreadsheet on the **Preview** tab); `Formatting may be inconsistent from source.`; `Knowledge Base` for knowledge-base items | `src/lib/components/common/FileItemModal.svelte:296-345` |
| Focused or entire switch | Composer chips only: `Using Focused Retrieval` / `Using Entire Document`, with the tooltips `Default to segmented retrieval for focused and relevant content extraction, this is recommended for most cases.` and `Inject the entire content as context for comprehensive processing, this is recommended for complex queries.` | `src/lib/components/common/FileItemModal.svelte:347-373` |
| **Content** tab | The extracted text, formatted as Markdown when **Render Markdown in Previews** is on (default on); long text stops at 10,000 characters with `Show all ({COUNT} characters)`; `No content` when there is none | `src/lib/components/common/FileItemModal.svelte:18`, `:440-505` |
| **Preview** tab | Offered for audio, PDF, Excel and CSV, code, Markdown, Word and PowerPoint files (decided by content type or extension) | `src/lib/components/common/FileItemModal.svelte:69-139`, `:392-416` |
| Images | Shown directly, with pan and zoom and a `Reset view` button | `src/lib/components/common/FileItemModal.svelte:418-439` |

What each preview does (all in the browser; nothing is converted on the server):

| Type | Preview | Failure text | Source |
|---|---|---|---|
| PDF | Pages drawn with pdf.js after downloading the file with the user's sign-in; scroll through pages; zoom with Ctrl or Cmd and the wheel, or the `Zoom out`, `Reset zoom` (shows the percentage) and `Zoom in` buttons; text can be selected | `Failed to load PDF.` (not translated) | `src/lib/components/common/PDFViewer.svelte:395-437`, `:470-600` |
| Word (`.docx`) | Page layout with headers, footers, footnotes and endnotes; links other than web, email and telephone links are removed; embedded HTML parts are not shown. If that fails, a simpler conversion without page layout is tried | `Failed to load DOCX file. Please try downloading it instead.` | `src/lib/components/common/DocxPreview.svelte:30`, `:104-158`; `src/lib/utils/docxToHtml.ts:13-30`; `src/lib/components/common/FileItemModal.svelte:174-182` |
| PowerPoint (`.pptx`) | Each slide is drawn as a picture in the browser: text, pictures (except EMF and WMF), tables, bar and line charts, backgrounds and connectors. Themes are only partly applied and SmartArt and animations are not drawn ("preview only"). Thumbnails beside the slide (hidden in windows narrower than 720 px); arrow keys or the wheel change slides; zoom buttons | `Failed to load PPTX file. Please try downloading it instead.` | `src/lib/utils/pptxToHtml.ts:1-9`, `:925-1075`; `src/lib/components/common/PptxPreview.svelte:1-60`, `:140-200`; `src/lib/components/common/FileItemModal.svelte:184-198` |
| Excel (`.xls`, `.xlsx`) and CSV | One table per sheet with column letters and row numbers, and sheet tabs when there are several | `Failed to load Excel/CSV file. Please try downloading it instead.`; `No content available` | `src/lib/utils/excelToTable.ts:40-88`; `src/lib/components/common/FileItemModal.svelte:141-172`, `:519-550` |
| Audio | A player for the stored file | None | `src/lib/components/common/FileItemModal.svelte:507-513` |
| Code (`.py`, `.js`, `.ts`, `.java`, `.html`, `.css`, `.json`, `.sql` and others) | Syntax-highlighted, read-only | None | `src/lib/components/common/FileItemModal.svelte:77-98`, `:551-561` |
| Markdown | Formatted | None | `src/lib/components/common/FileItemModal.svelte:562-567` |
| Anything else | The extracted text | `No content` | `src/lib/components/common/FileItemModal.svelte:588-592` |

**Images in messages** use their own viewer: clicking opens a full-screen preview with pan and zoom
and a **Download** button; **Escape** closes it (`src/lib/components/common/Image.svelte:64-81`;
`src/lib/components/common/ImagePreview.svelte:22-188`). The download is always named after the
"Generated Image" label, so an uploaded photo is saved as `generated_image.{type}`
(`src/lib/components/common/ImagePreview.svelte:92-95`, `:153-156`); a failed download shows
`Failed to download image`.

### 5.11 Downloading and the Content Endpoints

- **From the viewer**, the title link opens `/api/v1/files/{id}/content` in a new tab
  (`src/lib/components/common/FileItemModal.svelte:263-281`). A chip whose file details are not loaded
  opens the same address directly (`src/lib/components/common/FileItem.svelte:66-77`). The
  knowledge-base screens do the same (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:930`;
  `src/lib/components/workspace/Knowledge/KnowledgeBase/Files.svelte:225`).
- **How the browser receives it** (`backend/open_webui/routers/files.py:811-835`): PDFs open in the
  browser; plain text (`text/plain`) is shown in the browser; every other type downloads under its
  original name. Adding `?attachment=true` forces a download.
- **`/content/{file_name}`** always downloads; for a record with no stored bytes it returns the
  extracted text as plain text (`backend/open_webui/routers/files.py:907-957`).
- **`/content/html`** serves a file for embedding as a web page inside a response, and only when the
  file's owner is an admin; any other file answers `We could not find what you're looking for :/`
  (`backend/open_webui/routers/files.py:858-904`). Responses embed such files through a
  `{{HTML_FILE_ID_{id}}}` token, shown in a sandboxed frame; a `{{VIDEO_FILE_ID_{id}}}` token embeds a
  video player for `/content` (`src/lib/utils/index.ts:58-71`;
  `src/lib/components/chat/Messages/Markdown/HTMLToken.svelte:106-125`).
- **Extracted text** is available as JSON from `/api/v1/files/{id}/data/content`
  (`backend/open_webui/routers/files.py:688-706`).
- **Failures.** If the stored bytes cannot be found the answer is the `NOT_FOUND` text; if fetching
  them from cloud storage fails, `[ERROR: Error getting file content]`
  (`backend/open_webui/routers/files.py:836-850`).

### 5.12 Deleting One File

Who may delete: the uploader, any admin, and the narrow knowledge-base and model cases in 3.3. The
Files manager is the usual place (5.9). The server then (`backend/open_webui/routers/files.py:1013-1068`):

1. Removes the file from **every knowledge base** that contains it and deletes its chunks from each
   knowledge base's collection, by file id and by content hash; a failure here is logged at debug level
   and ignored (`:1026-1037`).
2. Deletes the **row** (`:1039`; `backend/open_webui/models/files.py:445-453`).
3. Deletes the **stored object**; cloud providers also delete the local copy; a missing local file only
   writes a log warning (`:1042`; `backend/open_webui/storage/provider.py:78-86`, `:176-185`, `:249-259`,
   `:313-323`).
4. Deletes the file's **vector collection** `file-{id}` (`:1043`).
5. Publishes the `file.deleted` event and answers `File deleted successfully`; the Files manager shows
   `File deleted successfully.` (`:1051-1058`; `src/lib/components/layout/FilesModal.svelte:129`).

**It is a hard delete.** There is no recycle bin, soft-delete flag or undo in the code; recovery would
need a backup, and whether backups exist is **TO BE CONFIRMED**. If step 3 or 4 fails, the user sees
`[ERROR: Error deleting files]` even though the row is already gone (`:1040-1050`); if step 2 fails,
`[ERROR: Error deleting file]` (`:1059-1063`).

**Other ways a file is deleted** (documented in their own areas):

- Removing a file from a knowledge base, or deleting a knowledge base, deletes the file itself when
  `ENABLE_KNOWLEDGE_FILE_RETENTION` is off (the default) and the person removing it owns the file or is
  an admin; on removal, only once no other knowledge base still holds it
  (`backend/open_webui/routers/knowledge.py:64-80`, `:1613-1618`, `:1825-1838`, `:2010-2018`,
  `:2357-2362`; `backend/open_webui/config.py:985`). See `knowledge-bases.md`.
- A new model background image is deleted again when saving the model fails and the model does not use
  that image, and a failed model import removes its background upload
  (`src/lib/components/workspace/Models/ModelEditor.svelte:437-470`;
  `backend/open_webui/routers/models.py:645-652`).

**Things that do not delete files:** removing a chip from a message
(`src/lib/components/chat/MessageInput.svelte:2012-2016`), deleting or archiving a chat (the chats router
never calls a file delete; `backend/open_webui/routers/chats.py` only reads files at `:2598`), and
deleting a user (ground truth).

### 5.13 Deleting All Files (Admin "Reset Upload Directory")

**Admin Settings > Documents > Danger Zone > Reset Upload Directory** (description
`Delete uploaded files from the upload directory.`) > **Reset** opens the generic confirmation (`Confirm your action` /
`This action cannot be undone. Do you wish to continue?`); confirming shows `Success`
(`src/lib/components/admin/Settings/Documents.svelte:25`, `:354-366`, `:1546-1561`;
`src/lib/i18n/locales/en-US/translation.json:2328-2329`).

Despite the label, the button calls `DELETE /api/v1/files/all`, which
(`backend/open_webui/routers/files.py:575-597`):

1. deletes **every row** in the `file` table, for every user (`backend/open_webui/models/files.py:455-463`);
2. deletes **every stored object** (below);
3. **resets the whole vector store**, which removes every collection: every file's, every knowledge
   base's and every user's memories (`backend/open_webui/retrieval/vector/async_client.py:141-142`;
   `backend/open_webui/retrieval/vector/dbs/chroma.py:196-198`;
   `backend/open_webui/retrieval/vector/dbs/pgvector.py:764-772`;
   `backend/open_webui/routers/memories.py:156-173`);
4. publishes `file.deleted_all` and answers `All files deleted successfully`.

What "every stored object" means depends on the provider
(`backend/open_webui/storage/provider.py:88-102`, `:187-202`, `:261-273`, `:325-335`):

| Provider | What is deleted |
|---|---|
| `local` | Every file and sub-folder in `DATA_DIR/uploads` |
| `s3` | Objects whose key starts with `S3_KEY_PREFIX` (every object when no prefix is set), from a single listing call, then the local folder |
| `gcs` | Every object in the bucket named by `GCS_BUCKET_NAME`, then the local folder |
| `azure` | Every blob in the container named by `AZURE_STORAGE_CONTAINER_NAME`, then the local folder |

Knowledge-base records survive but are left without files or vectors; the **Reindex Knowledge and
Memory Vectors** action rebuilds vectors only for content that still exists
(`src/lib/i18n/locales/en-US/translation.json:2318-2319`). Failure answers
`[ERROR: Error deleting files]`. A separate server endpoint, `POST /api/v1/retrieval/reset/uploads`, would empty only the local
upload folder, but no screen calls it (section 2.2). The neighbouring **Reset Vector Storage/Knowledge**
button resets the vector store and deletes all knowledge bases
(`backend/open_webui/routers/retrieval.py:3270-3284`; `rag-retrieval-embeddings-and-vector-stores.md`).

### 5.14 What Happens to Things That Reference a Deleted File

| Place | After the file is deleted | Source |
|---|---|---|
| Chat messages | The attachment stays in the message, because the chat's stored conversation is not edited. An image then shows `Image unavailable`; a file chip opens a viewer with little or no content; and later answers in that chat no longer include the file's text, because retrieval silently skips a file it cannot find | `src/lib/components/chat/Messages/UserMessage.svelte:176-200`; `src/lib/components/common/Image.svelte:40-63`; `backend/open_webui/retrieval/utils.py:1522-1561` |
| `chat_file` links | Declared to be removed with the file (`ON DELETE CASCADE`). The code never switches on SQLite's foreign-key enforcement, so on SQLite the link rows may remain; on PostgreSQL the database removes them | `backend/open_webui/models/chats.py:217-230`; `backend/open_webui/internal/db.py:335-395` |
| Knowledge bases | The file is removed from each one and its chunks deleted | `backend/open_webui/routers/files.py:1026-1037` |
| Channels | Messages keep the attachment reference; `channel_file` links are declared to cascade (same SQLite caveat) | `backend/open_webui/models/channels.py:157-170` |
| Workspace models | A model whose knowledge lists the file keeps listing it; the delete path does not touch models | `backend/open_webui/routers/files.py:1013-1068` |
| Notes | The note's own list of attachments keeps the entry | `src/lib/components/notes/NoteEditor.svelte:557-561` |

### 5.15 Google Drive Picker

**Switching it on** needs three things: **Admin Settings > Documents > Integration > Google Drive**
(`Allow Google Drive as a document source.`; setting `google_drive.enable`, default off, seeded from
`ENABLE_GOOGLE_DRIVE_INTEGRATION`), and the environment variables `GOOGLE_DRIVE_CLIENT_ID` and
`GOOGLE_DRIVE_API_KEY` (`src/lib/components/admin/Settings/Documents.svelte:1527-1537`;
`backend/open_webui/config.py:843-847`, `:2857-2859`; `backend/open_webui/routers/retrieval.py:1302-1306`).
The browser is given the **environment** values; the stored keys `google_drive.client_id` and
`google_drive.api_key` exist in the settings table but nothing reads them, so changing them has no
effect (`backend/open_webui/main.py:2376`, `:2422-2425`).

**What the user sees** (`src/lib/utils/google-drive-picker.ts:6-212`;
`src/lib/components/chat/MessageInput.svelte:2242-2261`):

1. **+** > **Google Drive** (shown only when the switch is on and uploads are allowed).
2. The browser reads the picker settings from `/api/config` using the user's sign-in, loads Google's
   scripts from `apis.google.com` and `accounts.google.com`, and a Google sign-in pop-up asks for
   access to Drive (scopes `drive.readonly` and `drive.file`).
3. The picker lists PDFs, plain text, Word `.docx`, Google Docs, Google Sheets and Google Slides; folders
   are hidden. Several files can be ticked, but **only the first is used**.
4. Google Docs and Slides arrive as plain text and Sheets as CSV; other files arrive as they are. The
   file is then uploaded through the normal upload step with processing, skipping the browser's size and
   count checks (5.2).
5. Cancelling does nothing. Any failure shows `Error accessing Google Drive: {error}` with one of the
   texts in section 10.4.

Whether users' networks and Google Workspace policies allow these Google services is **TO BE
CONFIRMED**.

### 5.16 Microsoft OneDrive Picker

**Switching it on**: **Admin Settings > Documents > Integration > OneDrive**
(`Allow OneDrive as a document source.`; `onedrive.enable`, default off, seeded from `ENABLE_ONEDRIVE_INTEGRATION`). The two
kinds of account depend on environment-only settings: **personal** needs `ONEDRIVE_CLIENT_ID_PERSONAL`
and **work or school** needs `ONEDRIVE_CLIENT_ID_BUSINESS` (both fall back to `ONEDRIVE_CLIENT_ID`), and
each can be switched off with `ENABLE_ONEDRIVE_PERSONAL` or `ENABLE_ONEDRIVE_BUSINESS` (both default on);
work or school also needs `ONEDRIVE_SHAREPOINT_URL` and optionally `ONEDRIVE_SHAREPOINT_TENANT_ID`
(`backend/open_webui/config.py:849-865`, `:2860-2862`; `backend/open_webui/main.py:2377-2386`,
`:2426-2431`). As with Google Drive, the browser receives the environment values, not the stored
`onedrive.sharepoint_url` and `onedrive.sharepoint_tenant_id` keys.

**What the user sees** (`src/lib/utils/onedrive-file-picker.ts:22-452`;
`src/lib/components/chat/MessageInput/InputMenu.svelte:437-445`, `:670-716`;
`src/lib/components/chat/MessageInput.svelte:2262-2276`):

1. **+** > **Microsoft OneDrive** > **Microsoft OneDrive (personal)** or **Microsoft OneDrive
   (work/school)** (each shown only when that kind is available).
2. A Microsoft sign-in pop-up appears (Microsoft consumer accounts for personal; the organization's
   tenant, or `common`, for work or school). The sign-in returns to the site's own address, which must be
   registered with the Microsoft application (**TO BE CONFIRMED** for production).
3. A picker window (800 by 600) opens: OneDrive files for personal accounts, the organization's SharePoint
   picker for work or school.
4. The first picked file is downloaded into the browser and uploaded through the normal upload step.
5. **Failures are not shown to the user.** Every error, including a blocked pop-up, is only written to
   the browser console (`src/lib/components/chat/MessageInput.svelte:2273-2275`); the texts are listed in
   section 10.4 for console screenshots.

### 5.17 Files Created Without an Upload

These appear in the Files manager of the person whose action created them:

| Name | Created by | Processed? | Source |
|---|---|---|---|
| `generated-image` plus an extension such as `.png` | Image generation and large images returned in a response; also linked to the chat | No | `backend/open_webui/routers/images.py:520-559`; `backend/open_webui/utils/files.py:108-124` |
| `generated-` plus an audio extension | Audio returned inside a response | No | `backend/open_webui/utils/files.py:164-198` |
| `Pasted_Text_{timestamp}.txt` | Pasting long text with **Paste Large Text as File** on | Yes, sent as **Entire Document** | `src/lib/components/chat/MessageInput.svelte:2190-2203` |
| `screen-capture-{timestamp}.png` | **Capture** on a computer | No (image) | `src/lib/components/chat/MessageInput.svelte:889-891` |
| `clipboard-image.{type}` | A prompt using `{{CLIPBOARD}}` | No (image) | `src/lib/components/chat/MessageInput.svelte:296-303` |
| `background.{type}` | Importing a model that carries a background image | No | `backend/open_webui/routers/models.py:605-632` |
| The remote file's own name | **Attach Webpage** with an address that turns out to be a file (recorded with `source_url`) | Yes, unless it is an image | `backend/open_webui/routers/retrieval.py:2388-2419` |

### 5.18 How Images Are Displayed

- Images in the composer and in sent messages load from `/api/v1/files/{id}/content`, so the viewer
  needs read access (`src/lib/components/chat/Messages/UserMessage.svelte:181-188`;
  `src/lib/components/chat/MessageInput.svelte:1935-1950`).
- An image that fails to load (deleted, no access, storage problem) is replaced by a small box reading
  `Image unavailable` (`src/lib/components/common/Image.svelte:22-63`).
- Image addresses that are not on this site, not embedded data and not Gravatar are replaced with the
  site icon (`/favicon.png`, a U of T icon on this fork) unless the place allows outside images; images
  written in Markdown inside responses are allowed, while profile pictures and images in the rich-text
  editor are not (`src/lib/utils/safeImageUrl.ts:22-38`; `src/lib/components/common/Image.svelte:28`;
  `src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens.svelte:101`;
  `src/lib/components/chat/Messages/ProfileImage.svelte:16`;
  `src/lib/components/common/RichTextInput/Image/image.ts:141-157`).
- When a model reads an image the server loads it from storage and sends it inline, after checking the
  user may read it (`backend/open_webui/utils/files.py:209-241`).

### 5.19 The Side Panel Files Tab (Terminal File Browser)

When a terminal is selected for the chat, the controls panel shows a **Files** tab that browses **the
terminal server's own file system**, not MedIT GPT's file storage; files handled here never appear in the
Files manager (`src/lib/components/chat/ChatControls.svelte:66-85`, `:295-296`;
`src/lib/components/chat/FileNav.svelte`). Terminals themselves, including who may use them, are
documented in `workspace-tools-tool-servers-mcp-and-terminals.md`. With the code interpreter's browser
engine the same tab shows Pyodide files instead (`code-execution-and-interpreter.md`).

| Part | Behaviour | Source |
|---|---|---|
| Empty states | `Start the chat to use this terminal.` when the terminal works per saved chat and the chat has not started; `No Terminal connection configured.` with `Add your Open Terminal URL and API key in Settings → Integrations.` | `src/lib/components/chat/FileNav.svelte:1546-1574` |
| Listing | Breadcrumbs, **Back**, **Forward**, **Refresh**, **Sort** by **Name**, **Size** or **Date Modified**, show or hide hidden files (remembered in the browser), `Read-only` marks; `This folder is empty`; on failure `Failed to load directory. Check your Terminal connection in Settings → Integrations.` | `src/lib/components/chat/FileNav.svelte:735-747`, `:2009-2015`; `src/lib/components/chat/FileNav/FileNavToolbar.svelte:59-310` |
| Search | `Search files and contents`, grouped into `Filename matches` and `Content matches`; `No matches`; `Failed to search files` | `src/lib/components/chat/FileNav.svelte:494-560`, `:1760-1781`, `:1883-1999` |
| Actions | **New File**, **New Folder**, **Upload**, **Upload Folder**, **Download** (folders as a ZIP), drag-and-drop upload (`Drop to upload`), drag to move, double-click to rename, **Copy Path**, **Delete** with confirmation | `src/lib/components/chat/FileNav.svelte:977-1191`, `:2155-2239`; `src/lib/components/chat/FileNav/FileEntryRow.svelte:350-450` |
| Selecting several | Ctrl, Cmd or Shift-click, or a long press on touch screens; the bar shows `{count} selected` with **Compare** (two files), **Select All**, **Download**, **Delete**, **Deselect** | `src/lib/components/chat/FileNav.svelte:1280-1373`; `src/lib/components/chat/FileNav/BulkActionBar.svelte:24-77` |
| Compare | Text differences between two files: `Extracting text and comparing…`, added and removed counts, `No text differences`; **Unified** or **Split**, **Hide whitespace**, **Swap** | `src/lib/components/chat/FileNav/FileCompare.svelte:31-260` |
| Previews | Images (zoom), video, audio, PDF with page thumbnails, SQLite databases (tables and a query box with **Run**), Word and PowerPoint (a preview from the terminal when it offers one, otherwise drawn in the browser), Excel, notebooks (cells can run on the terminal), JSON as a tree, CSV as a table, Markdown, HTML in a sandboxed frame, SVG, and an editor with **Save** for writable text files; `Could not read file.` or `Error previewing file: {error}` on failure | `src/lib/components/chat/FileNav.svelte:803-955`; `src/lib/components/chat/FileNav/FilePreview.svelte:282-512` |
| Ports and terminal | A **Ports** list of servers running in the terminal (`No servers detected`) with preview and open-in-new-tab, and the terminal dock below | `src/lib/components/chat/FileNav/PortList.svelte:60-110`; `src/lib/components/chat/FileNav.svelte:2098-2136` |

### 5.20 When Storage Is Full or Not Writable

| Situation | What the user sees | Source |
|---|---|---|
| The server cannot write an upload (disk full, quota exceeded, permission or read-only file system) | A red pop-up with `[ERROR: {strerror}]`, where `{strerror}` is the operating system's own wording (on Linux for example "No space left on device"); the upload is refused. The code passes the text rather than the error, so the friendlier wording below is **not** used here | `backend/open_webui/routers/files.py:374-393`; `backend/open_webui/constants.py:16-23` |
| The file name is too long for the file system | No error: the server retries once with a short name (`{id}.{extension}`) | `backend/open_webui/routers/files.py:376-387` |
| Cloud storage refuses the upload | `[ERROR: Error uploading file]` (the provider's message goes only to the log). The local copy is written first, so a full local disk also blocks cloud uploads | `backend/open_webui/storage/provider.py:145-164`, `:227-235`, `:291-299`; `backend/open_webui/routers/files.py:469-478` |
| The disk fills while an audio upload is being transcribed | The yellow warning reads `[ERROR: The server is out of storage space.]` (or `[ERROR: Server storage quota exceeded.]`, `[ERROR: Server storage is not writable.]`, `[ERROR: File name is too long.]`); other audio failures read `[ERROR: Error processing audio file]` | `backend/open_webui/constants.py:6-23`; `backend/open_webui/routers/audio.py:1157-1164`; `backend/open_webui/routers/files.py:259-268` |
| Extraction or embedding fails for lack of space | The yellow warning shows whatever text the failing step produced; it is not mapped | `backend/open_webui/routers/retrieval.py:2155-2163` |
| Opening a file whose stored bytes are gone | `We could not find what you're looking for :/` | `backend/open_webui/routers/files.py:836-841` |

The friendlier `[ERROR: …]` texts also appear in other areas (tools, functions, groups, skills, retrieval
settings, images) wherever the code passes the error itself; search `ERROR_MESSAGES.DEFAULT(e` to find
them. By default the database and vector store share the same `DATA_DIR` volume as the uploads (ground
truth), so a full disk affects far more than uploads; see `deployment-operations-and-logging.md`.

## 6. Data Model

Tier 1 does not query the database; this section explains what is stored so that escalations can name
the right records. Never open `backend/data/` (it holds the live database, uploads and vector store).

### 6.1 The `file` Table

Defined in `backend/open_webui/models/files.py:18-31`; created by the initial migration and reshaped by
later ones (`backend/open_webui/migrations/versions/7e5b5dc7342b_init.py:67-77`,
`7826ab40b532_update_file_table.py`, `c0fbf31ca0db_update_file_table.py`,
`c29facfe716b_update_file_table_path.py`, all under `backend/open_webui/migrations/versions/`).

| Column | Holds | Source |
|---|---|---|
| `id` | Random identifier generated at upload; also the prefix of the stored object's name | `backend/open_webui/models/files.py:20`; `backend/open_webui/routers/files.py:365` |
| `user_id` | The uploader (indexed) | `backend/open_webui/models/files.py:21` |
| `hash` | SHA-256 of the extracted text, set after processing and cleared when processing fails | `backend/open_webui/models/files.py:22`; `backend/open_webui/routers/retrieval.py:2069`, `:2165` |
| `filename` | The display name; renaming changes it | `backend/open_webui/models/files.py:24`, `:394-405` |
| `path` | Where the bytes are (section 6.5); empty for records that only hold text | `backend/open_webui/models/files.py:25`; `backend/open_webui/routers/files.py:939-952` |
| `data` | JSON: `status`, `error`, `content` (6.2) | `backend/open_webui/models/files.py:27` |
| `meta` | JSON: `name`, `content_type`, `size`, `file_hash`, `data`, `collection_name` (6.2) | `backend/open_webui/models/files.py:28` |
| `created_at`, `updated_at` | Epoch seconds; `updated_at` changes on every update, including status changes | `backend/open_webui/models/files.py:30-31`, `:348`, `:376` |

### 6.2 Keys Inside `data` and `meta`

| Key | Meaning | Source |
|---|---|---|
| `data.status` | Processing status (5.5) | `backend/open_webui/routers/files.py:416` |
| `data.error` | Why processing failed; shown to the uploader as the yellow warning | `backend/open_webui/routers/files.py:264-265`; `backend/open_webui/routers/retrieval.py:2161` |
| `data.content` | The extracted text (may be large, and may contain personal information) | `backend/open_webui/routers/retrieval.py:2064-2068` |
| `meta.name` | Original name; kept in step with `filename` on rename | `backend/open_webui/routers/files.py:419`; `backend/open_webui/models/files.py:399-400` |
| `meta.content_type` | Type reported by the browser at upload (corrected for model background images) | `backend/open_webui/routers/files.py:420`; `backend/open_webui/routers/models.py:120-122` |
| `meta.size` | Size in bytes | `backend/open_webui/routers/files.py:421` |
| `meta.file_hash` | SHA-256 of the raw bytes | `backend/open_webui/routers/files.py:402-406`, `:422` |
| `meta.data` | The metadata the browser sent: for example `language`, `knowledge_id`, `directory_id`, `channel_id`, `source_url` | `backend/open_webui/routers/files.py:423`, `:204`, `:227`, `:430` |
| `meta.collection_name` | The vector collection the text was embedded into (`file-{id}`) | `backend/open_webui/routers/retrieval.py:2118-2125` |

Older rows may hold a content type stored as a list; the response model tidies it
(`backend/open_webui/models/files.py:52-74`).

### 6.3 The `chat_file` Link Table

`backend/open_webui/models/chats.py:217-243`; migration
`backend/open_webui/migrations/versions/c440947495f3_add_chat_file_table.py:21-55`.

| Column | Holds |
|---|---|
| `id` | Row identifier |
| `user_id` | Who attached the file |
| `chat_id` | The chat (foreign key, `ON DELETE CASCADE`) |
| `message_id` | The message it was attached to |
| `file_id` | The file (foreign key, `ON DELETE CASCADE`) |
| `created_at`, `updated_at` | Epoch seconds |

One row per file per chat (unique on `chat_id` and `file_id`). Rows are written when a chat request
saves the user's message, for every attached item of type `file` that the sender may read
(`backend/open_webui/main.py:1452-1469`, `:1560-1575`; `backend/open_webui/models/chats.py:2571-2635`),
and when a generated image is linked to a chat (`backend/open_webui/routers/images.py:539-551`). Apart
from its own duplicate check, the only code that reads it is the shared-chat access rule (3.2;
`backend/open_webui/models/chats.py:2637-2664`); a helper to delete one link exists but nothing calls it
(`:2647-2654`). Two code observations, both to confirm in a test
environment (section 14): the duplicate check in `insert_chat_files` compares link-row ids with file
ids, so a message that re-attaches a file already linked to the chat fails the whole insert for that
message, which is caught and ignored (`:2582-2586`, `:2611-2635`); and the cascades are not enforced on
SQLite as configured (5.14).

The chat's stored conversation keeps its own copy of each message's attachment list; that copy is the
one the chat screen shows (`chat-composer-and-message-display.md`).

### 6.4 Other Places That Point at Files

| Where | How | Source |
|---|---|---|
| `knowledge_file` | Link table: knowledge base, file, optional folder inside the knowledge base, who added it | `backend/open_webui/models/knowledge.py:99-115` |
| `channel_file` | Link table: channel, message, file | `backend/open_webui/models/channels.py:157-170` |
| Workspace models | `meta.knowledge` entries of type `file`, and `meta.background_image_url` of the form `/api/v1/files/{id}/content` | `backend/open_webui/models/models.py:290-309` |
| Notes | The note's `data.files` list | `src/lib/components/notes/NoteEditor.svelte:557-561` |
| Folders | The folder's `data.files` entries of type `file`, `collection` or `note` | `backend/open_webui/utils/access_control/files.py:16`, `:105-158` |
| Chats | Each message's `files` list in the stored conversation | `backend/open_webui/main.py:1452-1469` |

### 6.5 Where the Bytes Live

| Provider (`STORAGE_PROVIDER`) | Value of `path` | Source |
|---|---|---|
| `local` (default) | `DATA_DIR/uploads/{id}_{name}` | `backend/open_webui/storage/provider.py:62-71` |
| `s3` | `s3://{bucket}/{key prefix}/{id}_{name}` | `backend/open_webui/storage/provider.py:145-162` |
| `gcs` | `gs://{bucket}/{id}_{name}` | `backend/open_webui/storage/provider.py:227-235` |
| `azure` | `{endpoint}/{container}/{id}_{name}` | `backend/open_webui/storage/provider.py:291-299` |

- **A local copy is always written first.** Each cloud provider saves the upload into `DATA_DIR/uploads`
  before sending it on (`backend/open_webui/storage/provider.py:147`, `:229`, `:293`). The copy stays
  unless `STORAGE_LOCAL_CACHE` is `false`, and even then it is removed only at the end of processing,
  so uploads without processing keep theirs (`backend/open_webui/routers/files.py:97-108`, `:270-277`).
  Every later read from cloud storage downloads a fresh copy into the same folder and leaves it there
  (`backend/open_webui/storage/provider.py:166-174`, `:237-247`, `:301-311`). Whether this matters for
  data-residency rules is **TO BE CONFIRMED** with the platform maintainer.
- **Object tags with personal data.** With `S3_ENABLE_TAGGING` on (default off), each S3 object is tagged
  with the uploader's email, user id, name and the file id (`OpenWebUI-User-Email`, `OpenWebUI-User-Id`,
  `OpenWebUI-User-Name`, `OpenWebUI-File-Id`), keeping only characters S3 allows
  (`backend/open_webui/routers/files.py:368-373`; `backend/open_webui/storage/provider.py:140-158`).
- **File names are in storage names.** The original name is part of the stored object's name
  (`backend/open_webui/routers/files.py:364-367`).
- **Slim image.** The slim build supports only `local`; starting it with another provider stops the
  server with
  `Slim requires local file storage. Set STORAGE_PROVIDER=local, or use the standard image to access cloud storage.` An unknown provider stops it with
  `Unsupported storage provider: {storage_provider}` (`backend/open_webui/storage/provider.py:338-356`; `backend/open_webui/env.py:45`).
- **Vectors** live in the vector store, not with the files: one collection `file-{id}` per processed file,
  one per knowledge base, and `user-memory-{id}` per user's memories
  (`backend/open_webui/routers/retrieval.py:1946`; `backend/open_webui/routers/memories.py:173`).
- `DATA_DIR` defaults to `backend/data`, and to `/app/backend/data` in the Docker image (ground truth);
  the uploads folder is created at startup (`backend/open_webui/config.py:174-175`). Which provider,
  bucket or volume production uses is **TO BE CONFIRMED**.

### 6.6 Kept Only in the Browser

| Item | Where | Source |
|---|---|---|
| Show or hide hidden files in the terminal browser | `localStorage` key `fileNav:showHidden` | `src/lib/components/chat/FileNav.svelte:471`, `:1405` |
| File-compare view mode and whitespace choice | `localStorage` keys `fileCompare:mode`, `fileCompare:ignoreWhitespace` | `src/lib/components/chat/FileNav/FileCompare.svelte:57`, `:66`, `:104-105` |
| Attachments of a temporary chat | Inside the unsaved message only | `src/lib/components/chat/MessageInput.svelte:1050-1083`, `:1172-1183` |

## 7. Settings and Configuration

Persistent settings live in the `config` table; after first boot the stored value wins over the
environment variable that seeded it (ground truth). Live values are **TO BE CONFIRMED** for production.

### 7.1 Admin Settings (Admin Settings > Documents)

Saved with the tab's **Save** button through `POST /api/v1/retrieval/config/update`; an emptied number
box means "no limit" (`src/lib/components/admin/Settings/Documents.svelte:264-298`;
`backend/open_webui/routers/retrieval.py:1279-1310`). Saving shows `Settings saved successfully!`
(`src/lib/components/chat/SettingsModal.svelte:460-464`).

| Field (section) | Setting key | Seeded from | Code default | Effect | Source |
|---|---|---|---|---|---|
| **Allowed File Extensions** (Files) | `rag.file.allowed_extensions` | `RAG_ALLOWED_FILE_EXTENSIONS` | empty (all types) | 5.6 | `backend/open_webui/config.py:998-1000`, `:2910` |
| **Max Upload Size** (Files) | `rag.file.max_size` | `RAG_FILE_MAX_SIZE` | none | 5.6 | `backend/open_webui/config.py:983`, `:2907` |
| **Max Upload Count** (Files) | `rag.file.max_count` | `RAG_FILE_MAX_COUNT` | none | 5.6 | `backend/open_webui/config.py:981`, `:2906` |
| **Image Compression Width** (Files) | `file.image_compression_width` | `FILE_IMAGE_COMPRESSION_WIDTH` | none | 5.7 | `backend/open_webui/config.py:989-991`, `:2908` |
| **Image Compression Height** (Files) | `file.image_compression_height` | `FILE_IMAGE_COMPRESSION_HEIGHT` | none | 5.7 | `backend/open_webui/config.py:993-995`, `:2909` |
| **Google Drive** (Integration) | `google_drive.enable` | `ENABLE_GOOGLE_DRIVE_INTEGRATION` | off | 5.15 | `backend/open_webui/config.py:843`, `:2857` |
| **OneDrive** (Integration) | `onedrive.enable` | `ENABLE_ONEDRIVE_INTEGRATION` | off | 5.16 | `backend/open_webui/config.py:849`, `:2860` |
| **Reset Upload Directory** (Danger Zone) | none (action) | none | none | 5.13 | `src/lib/components/admin/Settings/Documents.svelte:1546-1561` |

The browser receives the size and count limits and the compression sizes in the `file` section of
`/api/config` (`backend/open_webui/main.py:2413-2420`). Also seeded but without effect on the pickers:
`google_drive.client_id`, `google_drive.api_key`, `onedrive.sharepoint_url` and
`onedrive.sharepoint_tenant_id` (`backend/open_webui/config.py:2858-2862`; 5.15, 5.16). Extraction,
embedding and speech-to-text settings that change processing (`rag.content_extraction_engine`,
`rag.content_extraction.supported_media_mime_types`, `rag.bypass_embedding_and_retrieval`,
`audio.stt.supported_content_types`) are documented in `rag-retrieval-embeddings-and-vector-stores.md`
and `audio-speech-to-text-and-text-to-speech.md` (`backend/open_webui/config.py:2863-2864`, `:2898`,
`:3059`).

### 7.2 Storage Environment Variables (Names Only)

All are environment-only and read once at startup. Values, especially keys and credentials, are
secrets and are not reproduced here.

| Variable | Purpose | Code default | Source |
|---|---|---|---|
| `STORAGE_PROVIDER` | `local`, `s3`, `gcs` or `azure` | `local` | `backend/open_webui/config.py:150` |
| `STORAGE_LOCAL_CACHE` | Keep the local copy of cloud-stored files after processing | `true` | `backend/open_webui/config.py:151` |
| `DATA_DIR` | Base folder; uploads go to its `uploads` sub-folder | `backend/data` | `backend/open_webui/env.py:228`; `backend/open_webui/config.py:174` |
| `S3_BUCKET_NAME`, `S3_REGION_NAME`, `S3_ENDPOINT_URL`, `S3_KEY_PREFIX`, `S3_ADDRESSING_STYLE` | Where S3 objects go | none | `backend/open_webui/config.py:155-160` |
| `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` | S3 credentials; when not both set the platform's default identity is used | none | `backend/open_webui/config.py:153-154`; `backend/open_webui/storage/provider.py:117-135` |
| `S3_USE_ACCELERATE_ENDPOINT` | S3 transfer acceleration | `false` | `backend/open_webui/config.py:159` |
| `S3_ENABLE_TAGGING` | Tag objects with uploader details (6.5) | `false` | `backend/open_webui/config.py:161` |
| `GCS_BUCKET_NAME`, `GOOGLE_APPLICATION_CREDENTIALS_JSON` | Google Cloud Storage bucket and credentials (otherwise the environment's default identity) | none | `backend/open_webui/config.py:163-164`; `backend/open_webui/storage/provider.py:212-225` |
| `AZURE_STORAGE_ENDPOINT`, `AZURE_STORAGE_CONTAINER_NAME`, `AZURE_STORAGE_KEY` | Azure Blob storage account, container and key (otherwise managed identity) | none | `backend/open_webui/config.py:166-168`; `backend/open_webui/storage/provider.py:276-289` |
| `USE_SLIM_DOCKER` | Slim build; only local storage allowed | `False` | `backend/open_webui/env.py:45` |

(`S3_VECTOR_BUCKET_NAME` and `S3_VECTOR_REGION` belong to the S3 vector store, not file storage;
`backend/open_webui/config.py:825-826`.)

### 7.3 Cloud Picker Environment Variables

| Variable | Purpose | Code default | Source |
|---|---|---|---|
| `GOOGLE_DRIVE_CLIENT_ID`, `GOOGLE_DRIVE_API_KEY` | Google application identity for the picker; both required | empty | `backend/open_webui/config.py:845-847`; `backend/open_webui/main.py:2422-2425` |
| `ONEDRIVE_CLIENT_ID` | Fallback Microsoft application id for both account kinds | empty | `backend/open_webui/config.py:852` |
| `ONEDRIVE_CLIENT_ID_PERSONAL`, `ONEDRIVE_CLIENT_ID_BUSINESS` | Application id per account kind | `ONEDRIVE_CLIENT_ID` | `backend/open_webui/config.py:853-854` |
| `ENABLE_ONEDRIVE_PERSONAL`, `ENABLE_ONEDRIVE_BUSINESS` | Offer each account kind (only when its id is set) | `True` | `backend/open_webui/config.py:856-861` |
| `ONEDRIVE_SHAREPOINT_URL`, `ONEDRIVE_SHAREPOINT_TENANT_ID` | Organization SharePoint address and tenant for work or school accounts | empty | `backend/open_webui/config.py:863-865`; `backend/open_webui/main.py:2426-2431` |

### 7.4 Other Environment Variables That Affect Files

| Variable | Effect | Code default | Source |
|---|---|---|---|
| `BYPASS_ADMIN_ACCESS_CONTROL` | Admins list everyone's files (3.4) | `True` | `backend/open_webui/config.py:2086-2092` |
| `USER_PERMISSIONS_CHAT_FILE_UPLOAD` | Seeds the default `chat.file_upload` permission | `True` | `backend/open_webui/config.py:1857`, `:1983` |
| `ENABLE_KNOWLEDGE_FILE_RETENTION` | Keep files when they are removed from knowledge bases | `False` | `backend/open_webui/config.py:985` |
| `ENABLE_IMAGE_CONTENT_TYPE_EXTENSION_FALLBACK` | Guess an image's type from its extension when sending it to a model | `False` | `backend/open_webui/env.py:1066-1067`; `backend/open_webui/utils/files.py:232-236` |
| `RAG_FILE_CONTENT_SEARCH_MAX_CHARS` | How much of each file's text knowledge-base search scans | 67,108,864 characters (64 × 1024 × 1024) | `backend/open_webui/config.py:987`; `backend/open_webui/models/knowledge.py:407` |

### 7.5 Per-User Settings

Saved per user from **Settings > Interface** (`src/lib/components/common/InterfaceSettings.svelte`):

| Setting | Default | Effect | Source |
|---|---|---|---|
| **Default Upload Mode** (`defaultUploadContext`) | `Using Focused Retrieval` | Whether new attachments are sent whole or by passages | `src/lib/components/common/InterfaceSettings.svelte:103`, `:408`, `:1904-1928` |
| **Image Compression** (`imageCompression`, `imageCompressionSize`) | Off | 5.7 | `src/lib/components/common/InterfaceSettings.svelte:88-92`, `:390-391`, `:1931-1968` |
| **Compress Images in Channels** (`imageCompressionInChannels`) | On | 5.7 | `src/lib/components/common/InterfaceSettings.svelte:93`, `:392`, `:1970-1993` |
| **Render Markdown in Previews** (`renderMarkdownInPreviews`) | On | Content tab formatting (5.10) | `src/lib/components/common/InterfaceSettings.svelte:82`, `:360`, `:1036-1057` |
| **Paste Large Text as File** (`largeTextAsFile`) | Off | 5.1 | `src/lib/components/common/InterfaceSettings.svelte:58`, `:350`, `:1709-1730` |

### 7.6 Permissions and Model Capabilities

| Control | Effect here | Source |
|---|---|---|
| `chat.file_upload` permission (default on) | Upload controls in the composer; offering built-in chat-file tools | 3.1 |
| `chat.web_upload` permission (default on) | **Attach Webpage**; see `web-search-and-web-loading.md` | `backend/open_webui/config.py:1859`, `:1984` |
| Model capability `file_upload` | Composer refuses uploads when a selected model lacks it | `src/lib/components/chat/MessageInput.svelte:759-773`, `:924-929` |
| Model capability `vision` | Composer refuses images when a selected model lacks it | `src/lib/components/chat/MessageInput.svelte:1126-1130` |
| Model capability `file_context` | Whether attached files are given to the model as context or through tools; see `workspace-models-and-model-access.md` | `backend/open_webui/utils/tools.py:594-600` |

## 8. Cron Jobs and Background Processes

There is no scheduled job for files. Of the seven loops started at startup none concerns files
(`knowledgebase/tools/inventory.md`, "Background loops started at startup"). What runs outside the
request is:

| What | When and where | Source |
|---|---|---|
| **Upload processing** | A background task in the same server process, started after the upload response is sent; some callers (for example web-address attachments) run it before answering | `backend/open_webui/routers/files.py:435-457`; `backend/open_webui/routers/retrieval.py:2397-2404` |
| **Status stream** | Each browser waiting on an upload has the server read the file's status once a second, for at most 7,200 reads (about two hours); the stream deliberately holds no long-lived database session | `backend/open_webui/routers/files.py:624-673` |
| **Local-copy clean-up** | At the end of processing, only for cloud storage with `STORAGE_LOCAL_CACHE` off | `backend/open_webui/routers/files.py:97-108`, `:270-277` |
| **Event delivery** | Each file event is handed to admin event webhooks, active Event functions and (for processing failures) users' notification webhooks as separate tasks | `backend/open_webui/events.py:1060-1171` |

Everything else happens at request time: deletion (one file or all) runs inside the request
(`backend/open_webui/routers/files.py:575-597`, `:1013-1068`), and admin limits take effect as soon as
they are saved. Nothing retries a failed or interrupted processing run, and nothing removes orphaned
stored objects or files whose owner was deleted.

## 9. Notifications and Emails

The application sends no email (ground truth). File activity produces:

**Pop-ups in the browser** (toasts): the red, yellow and green messages in section 10. Processing
results reach the uploader's browser through the status stream (5.5), not through websocket events.

**Events** on the platform event bus (`backend/open_webui/events.py:287-301`, `:409-431`). Each event
carries the acting user's id, name, email and role (`backend/open_webui/events.py:704`, `:974-995`), so
event payloads are personal data:

| Event | Published when | Extra data | Source |
|---|---|---|---|
| `file.uploaded` | An upload is accepted | File name, content type | `backend/open_webui/routers/files.py:314-320` |
| `file.content_updated` | Extracted text is replaced | The first 300 characters of the new text | `backend/open_webui/routers/files.py:775-781` |
| `file.renamed` | A file is renamed | New name | `backend/open_webui/routers/files.py:988-994` |
| `file.deleted` | One file is deleted | File name | `backend/open_webui/routers/files.py:1051-1057` |
| `file.deleted_all` | All files are deleted | None | `backend/open_webui/routers/files.py:591` |
| `retrieval.content.processed` | Processing finished | Collection name, file name | `backend/open_webui/routers/retrieval.py:2073-2080`, `:2136-2143` |
| `retrieval.content.process_failed` | Processing failed | Collection name, file name, and the message `{filename}: {error}` | `backend/open_webui/routers/retrieval.py:2167-2178` |
| `retrieval.uploads.reset` | The unused upload-folder reset endpoint runs | None | `backend/open_webui/routers/retrieval.py:3310-3316` |

Where events go (`backend/open_webui/events.py:1067-1171`):

- **Admin event webhooks** configured in the admin events settings receive them (see
  `public-api-and-integrations.md`).
- **Event functions** that are active receive them (`functions-pipes-filters-actions-and-pipelines.md`).
- **Personal notification webhooks.** `retrieval.content.process_failed` is one of the five events a
  user can subscribe to (shown as `Retrieval Content process failed`;
  `backend/open_webui/utils/notifications.py:223-231`; `src/lib/components/chat/Settings/Notifications.svelte:391`).
  When the admin has user webhooks
  on (`ui.enable_user_webhooks`) and the uploader subscribed, a failed processing run posts the file name
  and error to the uploader's own webhook; with the default "away" delivery only while they are not
  active in the app (`backend/open_webui/events.py:669-675`, `:780-799`;
  `backend/open_webui/utils/notifications.py:389-411`). See `user-settings-and-personalisation.md`.

**Browser (system) notifications** are raised only for calendar alerts, finished chats and channel
messages (`src/routes/+layout.svelte:610-623`, `:740-761`, `:865-874`); none concerns files.

## 10. Error, Warning and Notice Messages (Verbatim)

Severity: **Error** is a red pop-up, **Warning** a yellow pop-up, **Success** a green pop-up, **Inline**
text inside a window, **Tooltip** hover text, **Console** appears only in the browser's developer
console, **API** is a server answer that the screens in this area replace with their own text, and
**Log** is a server log line. Server texts reach the chat composer and the Files manager as red pop-ups
that print the server's text (`src/lib/components/chat/MessageInput.svelte:1044-1049`;
`src/lib/components/layout/FilesModal.svelte:133-135`). Placeholders use the source's variable names.

### 10.1 Server: Files API and Storage

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `[ERROR: Invalid metadata format]` | Error | `backend/open_webui/routers/files.py:336-343` | The metadata sent with an upload is not valid JSON (an integration or script, not the normal screens) | Report the tool used | Which client sent it |
| `[ERROR: File type {file_extension} is not allowed]` | Error | `backend/open_webui/routers/files.py:354-362` | The extension is not in **Allowed File Extensions** (also a file with no extension, shown with an empty type) | Convert to an allowed type | The live `rag.file.allowed_extensions`; entries must be lower case without dots (5.6) |
| `[ERROR: {strerror}]` | Error | `backend/open_webui/routers/files.py:376-382`, `:388-393` | The server's disk refused the write; the text is the operating system's (for example "No space left on device") | Try again later | Escalate as a storage incident with the time and text (5.20) |
| `[ERROR: Error uploading file]` | Error | `backend/open_webui/routers/files.py:381`, `:392`, `:462-465`, `:469-478` | Cloud storage refused the upload, the record could not be created, or another unexpected failure | Try again | Server log at that time |
| `Oops! The file you're trying to upload is too large. Please upload a file that is less than {max_size} MB.` | Error (HTTP 413) | `backend/open_webui/routers/files.py:394-400`, `:735-740`; `backend/open_webui/constants.py:105-107` | Above **Max Upload Size**: an upload (including cloud-picker files) or replacing a file's text | Use a smaller file or split it | `rag.file.max_size` |
| `The content provided is empty. Please ensure that there is text or data present before proceeding.` | Error | `backend/open_webui/storage/provider.py:64-67`; `backend/open_webui/routers/files.py:469-478`; `backend/open_webui/constants.py:95` | A zero-byte file reached the server (the composer normally stops it first) | Check the file | None |
| `No files found matching the pattern.` | API (HTTP 404) | `backend/open_webui/routers/files.py:542-546` | A file search with no results; the Files manager shows `No files found` | None | None |
| `We could not find what you're looking for :/` | Error | `backend/open_webui/routers/files.py:609-621`, `:636-640`, `:676-680`, `:694-706`, `:728-732`, `:783-787`, `:804-808`, `:836-841`, `:851-855`, `:864-875`, `:886-890`, `:900-904`, `:913-917`, `:934-938`, `:953-957`, `:979-983`, `:1001-1005`, `:1019-1023`, `:1064-1068`; `backend/open_webui/constants.py:78` | The file does not exist, the person may not read or change it, its stored bytes are gone, or (HTML embedding) its owner is not an admin | Ask the owner to share it through a knowledge base, channel or shared chat | File id, owner, how it was shared (3.2) |
| `[ERROR: Error getting file content]` | Error | `backend/open_webui/routers/files.py:842-850`, `:891-899` | Reading the stored bytes failed, for example a cloud download error | Try again | Server log; storage provider |
| `[ERROR: Error renaming file]` | Error | `backend/open_webui/routers/files.py:996-1000` | The rename could not be saved | Try again | Server log |
| `[ERROR: Error deleting files]` | Error | `backend/open_webui/routers/files.py:584-597`, `:1040-1050` | Delete-all failed, or after a single file's record was removed its stored bytes or vectors could not be deleted | None (the record may already be gone) | Server log; possible leftover object in storage |
| `[ERROR: Error deleting file]` | Error | `backend/open_webui/routers/files.py:1059-1063` | The record could not be deleted | Try again | Server log |
| `File deleted successfully` | API | `backend/open_webui/routers/files.py:1058` | One file deleted (the Files manager shows its own text, 10.3) | None | None |
| `All files deleted successfully` | API | `backend/open_webui/routers/files.py:592` | Delete-all finished (the admin screen shows `Success`) | None | None |
| `Slim requires local file storage. Set STORAGE_PROVIDER=local, or use the standard image to access cloud storage.` | Log (startup stops) | `backend/open_webui/storage/provider.py:339-342` | Slim build started with a cloud provider | None | Deployment settings |
| `Unsupported storage provider: {storage_provider}` | Log (startup stops) | `backend/open_webui/storage/provider.py:351-352` | `STORAGE_PROVIDER` is not `local`, `s3`, `gcs` or `azure` | None | Deployment settings |

### 10.2 Processing Failures Shown After an Upload

Each of these is stored as `data.error` and shown to the uploader as a **Warning** pop-up while the file
stays attached (`src/lib/components/chat/MessageInput.svelte:1025-1028`;
`src/lib/components/notes/NoteEditor.svelte:529-532`). Failures inside the extraction and embedding
step (`process_file`) also publish a `retrieval.content.process_failed` event carrying the same text
(`backend/open_webui/routers/retrieval.py:2167-2178`; section 9); failures before that step (unsupported
image, audio transcription, knowledge-base link) do not.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `File type {content_type} is not supported for processing` | Warning | `backend/open_webui/routers/files.py:186-187` | An image uploaded with processing (cloud picker, knowledge base) when the extraction engine is not set up for images | Attach the image in the chat composer instead, or ignore if only storage is needed | `rag.content_extraction.supported_media_mime_types`, extraction engine |
| `The content provided is empty. Please ensure that there is text or data present before proceeding.` | Warning | `backend/open_webui/routers/retrieval.py:1819-1820`, `:2015` | No text could be extracted (for example a scanned PDF without text recognition) | Provide a text-based version | Extraction engine and OCR settings (`rag-retrieval-embeddings-and-vector-stores.md`) |
| `Duplicate content detected. Please provide unique content to proceed.` | Warning | `backend/open_webui/routers/retrieval.py:1735-1753` | The same text is already in the target collection from another file (mostly knowledge bases) | Use the existing copy | Knowledge base contents |
| `Pandoc is not installed on the server. Please contact your administrator for assistance.` | Warning | `backend/open_webui/routers/retrieval.py:2180-2184`; `backend/open_webui/constants.py:85` | The extraction step needed Pandoc and it is missing | None | Escalate to the platform maintainer |
| `Error saving document to vector database` | Warning | `backend/open_webui/routers/retrieval.py:2150-2151` | The vector store did not accept the chunks | Try again later | Vector store health |
| `[ERROR: Invalid text splitter]` | Warning | `backend/open_webui/routers/retrieval.py:1816-1817` | The admin's text splitter setting is not recognised | None | RAG settings |
| `Audio conversion failed. The audio file may be corrupted or empty.` | Warning | `backend/open_webui/routers/audio.py:1143-1148` | An audio upload could not be converted for transcription | Check the recording | None |
| `[ERROR: Error processing audio file]` | Warning | `backend/open_webui/routers/audio.py:1157-1164` | Splitting an audio upload into pieces failed | Try again | Server log |
| `[ERROR: The server is out of storage space.]` | Warning | `backend/open_webui/constants.py:8`, `:16-23`; `backend/open_webui/routers/audio.py:1157-1164` | The disk filled while an audio upload was being prepared for transcription | Try again later | Escalate as a storage incident |
| `[ERROR: Server storage quota exceeded.]` | Warning | `backend/open_webui/constants.py:9`, `:16-23` | As above, disk quota | As above | As above |
| `[ERROR: Server storage is not writable.]` | Warning | `backend/open_webui/constants.py:10-12`, `:16-23` | As above, permission or read-only disk | As above | As above |
| `[ERROR: File name is too long.]` | Warning | `backend/open_webui/constants.py:7`, `:16-23` | As above, name too long for the disk | Rename the file shorter | None |
| `Failed to link file {file_item.id} to knowledge {knowledge_id}` | Warning | `backend/open_webui/routers/files.py:252-253` | A knowledge-base upload was processed but the link could not be saved | Add the file to the knowledge base again | Knowledge base and file ids |
| `Error downloading file from S3: {e}` | Warning | `backend/open_webui/storage/provider.py:166-174` | Processing could not fetch the file back from S3 | Try again | Storage provider |
| `Error downloading file from GCS: {e}` | Warning | `backend/open_webui/storage/provider.py:237-247` | As above, Google Cloud Storage | Try again | Storage provider |
| `Error downloading file from Azure Blob Storage: {e}` | Warning | `backend/open_webui/storage/provider.py:301-311` | As above, Azure | Try again | Storage provider |

Other extraction and embedding errors are passed through with the engine's own wording
(`backend/open_webui/routers/retrieval.py:2185-2188`); see `rag-retrieval-embeddings-and-vector-stores.md`.

### 10.3 Composer, Files Manager, Viewer and Previews

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `You can only chat with a maximum of {maxCount} file(s) at a time.` | Error | `src/lib/components/chat/MessageInput.svelte:1089-1101` | Attached plus new files exceed **Max Upload Count** | Attach fewer files per message | `rag.file.max_count` |
| `File size should not exceed {maxSize} MB.` | Error | `src/lib/components/chat/MessageInput.svelte:1106-1124` | A picked, dropped, pasted or captured file exceeds **Max Upload Size** | Use a smaller file | `rag.file.max_size` |
| `You do not have permission to upload files.` | Error; Tooltip | `src/lib/components/chat/MessageInput.svelte:918-922`; `src/lib/components/chat/MessageInput/InputMenu.svelte:188-192` | No `chat.file_upload` permission | None | Permissions (`users-groups-roles-and-permissions.md`) |
| `Model(s) do not support file upload` | Error; Tooltip | `src/lib/components/chat/MessageInput.svelte:924-929`; `src/lib/components/chat/MessageInput/InputMenu.svelte:186-190` | A selected model lacks the `file_upload` capability | Choose another model | Model capabilities |
| `Selected model(s) do not support image inputs` | Error | `src/lib/components/chat/MessageInput.svelte:1126-1130` | An image with a model that lacks vision | Choose a vision model | Model capabilities |
| `You cannot upload an empty file.` | Error | `src/lib/components/chat/MessageInput.svelte:949-952`; `src/lib/components/notes/NoteEditor.svelte:505-508` | A zero-byte file | Check the file | None |
| `Failed to upload file.` | Error (terminal uploads) or silent removal | `src/lib/components/chat/MessageInput.svelte:985-989`, `:1039-1043` | The upload returned nothing | Try again | Server log |
| `File not found.` | Error | `src/lib/components/chat/MessageInput.svelte:1723-1729` | The file dialogue returned no file | Pick again | None |
| `Failed to extract content from the file: {error}` | Error | `src/lib/components/chat/MessageInput.svelte:1052-1060` | Temporary chat: the browser could not read the file | Use a saved chat or another format | None |
| `Failed to extract content from the file.` | Error | `src/lib/components/chat/MessageInput.svelte:1062-1068` | Same, follow-up message | As above | None |
| `Unsupported or non-text file type: {name}` | Shown inside the message above | `src/lib/utils/index.ts:2089-2094` | Temporary chat with a file the browser cannot read as text | As above | None |
| `Add Files` / `Drop any files here to upload` | Inline | `src/lib/components/AddFilesPlaceholder.svelte:11-25` | Dragging files over the chat, a knowledge base, a channel or a note | Drop the files | None |
| `File deleted successfully.` | Success | `src/lib/components/layout/FilesModal.svelte:126-131` | A file deleted from the Files manager | None | None |
| `No files found` | Inline | `src/lib/components/layout/FilesModal.svelte:332-338`, `:78-82` | No uploads, no search matches, or the search failed | Clear the search | None |
| `Loading...` | Inline | `src/lib/components/layout/FilesModal.svelte:383-398` | More rows are being fetched | Wait | None |
| `Confirm your action` / `This action cannot be undone. Do you wish to continue?` | Inline (dialogue) | `src/lib/components/common/ConfirmDialog.svelte:139-154`; `src/lib/components/layout/FilesModal.svelte:191-199` | Deleting a file without Shift; also **Reset Upload Directory** and deleting in the terminal browser | Confirm or cancel | None |
| `Success` | Success | `src/lib/components/admin/Settings/Documents.svelte:354-366` | **Reset Upload Directory** finished (5.13) | None | Expect empty Files manager and knowledge bases |
| `Settings saved successfully!` | Success | `src/lib/components/chat/SettingsModal.svelte:460-464` | Admin saved the Documents tab | None | None |
| `Formatting may be inconsistent from source.` | Inline | `src/lib/components/common/FileItemModal.svelte:335-337` | The viewer shows extracted text | None | None |
| `{COUNT} extracted lines` / `{COUNT} Rows` | Inline | `src/lib/components/common/FileItemModal.svelte:322-333` | Size of the extracted text, or rows of a spreadsheet preview | None | A very low count suggests poor extraction |
| `Using Focused Retrieval` / `Using Entire Document` | Inline | `src/lib/components/common/FileItemModal.svelte:347-373` | The per-file switch on composer chips | Choose | None |
| `Default to segmented retrieval for focused and relevant content extraction, this is recommended for most cases.` | Tooltip | `src/lib/components/common/FileItemModal.svelte:354-356` | Hovering the switch while focused | None | None |
| `Inject the entire content as context for comprehensive processing, this is recommended for complex queries.` | Tooltip | `src/lib/components/common/FileItemModal.svelte:351-353` | Hovering the switch while entire | None | None |
| `Show all ({COUNT} characters)` | Inline | `src/lib/components/common/FileItemModal.svelte:456-467`, `:488-499` | Extracted text longer than 10,000 characters | Click to expand | None |
| `No content` | Inline (not translated) | `src/lib/components/common/FileItemModal.svelte:442`, `:474`, `:590` | The file has no extracted text available (images, failed processing, deleted file) | None | Processing status |
| `No content available` | Inline | `src/lib/components/common/FileItemModal.svelte:547-549`, `:573-575`, `:585-587` | A spreadsheet, Word or PowerPoint preview produced nothing | Download the file | None |
| `Failed to load Excel/CSV file. Please try downloading it instead.` | Inline | `src/lib/components/common/FileItemModal.svelte:155-158` | The spreadsheet could not be read in the browser (also when the file cannot be fetched) | Download it | Whether the file still exists |
| `Failed to load DOCX file. Please try downloading it instead.` | Inline | `src/lib/components/common/FileItemModal.svelte:178-181`; `src/lib/components/common/DocxPreview.svelte:151-155` | The Word file could not be fetched or drawn | Download it | As above |
| `Failed to load PPTX file. Please try downloading it instead.` | Inline | `src/lib/components/common/FileItemModal.svelte:194-197` | The PowerPoint file could not be fetched or drawn | Download it | As above |
| `Failed to load PDF.` | Inline (not translated) | `src/lib/components/common/PDFViewer.svelte:430-434` | The PDF could not be fetched or drawn | Download it | As above |
| `Reset view` | Tooltip | `src/lib/components/common/FileItemModal.svelte:421` | Image pan and zoom | None | None |
| `Image unavailable` | Inline | `src/lib/components/common/Image.svelte:52-63` | An image could not be loaded (deleted, no access, storage problem) | Re-attach if needed | Whether the file exists and who owns it |
| `Failed to download image` | Error | `src/lib/components/common/ImagePreview.svelte:161-164` | Downloading from the full-screen image preview failed | Try again | None |
| `Collection`, `Note`, `Chat`, `File`, `Document` | Tooltip | `src/lib/components/common/FileItem.svelte:111-121` | Hovering a small chip's icon | None | None |

### 10.4 Cloud Pickers

Google Drive failures are shown as `Error accessing Google Drive: {error}`
(`src/lib/components/chat/MessageInput.svelte:2252-2260`), where `{error}` is one of the Google texts
below. OneDrive failures are **Console** only (`:2273-2275`).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Error accessing Google Drive: {error}` | Error | `src/lib/components/chat/MessageInput.svelte:2252-2260` | Any Google Drive picker failure | See the inner text | Integration settings |
| `Failed to fetch Google Drive credentials` | Inside the error above | `src/lib/utils/google-drive-picker.ts:7-10` | Reading `/api/config` failed | Reload the page | Server availability |
| `Google Drive API credentials not configured` | Inside the error above | `src/lib/utils/google-drive-picker.ts:15-17`, `:25-28` | `GOOGLE_DRIVE_CLIENT_ID` or `GOOGLE_DRIVE_API_KEY` missing (or the page could not identify the user) | None | Environment variables (5.15) |
| `Please configure valid Google Drive API credentials` | Inside the error above | `src/lib/utils/google-drive-picker.ts:29-31` | Empty identifiers | None | As above |
| `Failed to get access token` | Inside the error above | `src/lib/utils/google-drive-picker.ts:80-86` | Google returned no access | Sign in again and allow access | None |
| `OAuth error occurred` | Inside the error above | `src/lib/utils/google-drive-picker.ts:88-90` | The Google sign-in pop-up failed without its own text (for example closed or blocked) | Allow pop-ups and retry | Browser pop-up settings |
| `Unable to get OAuth token` | Inside the error above | `src/lib/utils/google-drive-picker.ts:113-117` | No token after sign-in | Retry | None |
| `Required file details missing` | Inside the error above | `src/lib/utils/google-drive-picker.ts:142-144` | Google returned an incomplete selection | Pick again | None |
| `Failed to download file ({status}): {errorText}` | Inside the error above | `src/lib/utils/google-drive-picker.ts:176-184` | Google refused the download (for example no permission on the file) | Check access in Drive | None |
| `Failed to fetch OneDrive credentials` | Console | `src/lib/utils/onedrive-file-picker.ts:42-44` | Reading `/api/config` failed | Reload | Server availability |
| `OneDrive personal or business client ID not configured` | Console | `src/lib/utils/onedrive-file-picker.ts:53-55` | No OneDrive application id in the environment | None | Environment variables (5.16) |
| `OneDrive client ID not configured` | Console | `src/lib/utils/onedrive-file-picker.ts:74-76` | The chosen account kind has no application id | None | As above |
| `Sharepoint URL not configured` | Console | `src/lib/utils/onedrive-file-picker.ts:109-112` | Work or school chosen without `ONEDRIVE_SHAREPOINT_URL` | None | As above |
| `Failed to login: {message}` | Console | `src/lib/utils/onedrive-file-picker.ts:155-160` | The Microsoft sign-in pop-up failed | Allow pop-ups; retry | Application registration |
| `Failed to acquire access token` | Console | `src/lib/utils/onedrive-file-picker.ts:163-165`, `:392-395` | No access token after sign-in | Retry | As above |
| `Unable to retrieve OneDrive access token.` | Console | `src/lib/utils/onedrive-file-picker.ts:248-251` | As above, while downloading | Retry | As above |
| `Failed to fetch file information: {status} {statusText}` | Console | `src/lib/utils/onedrive-file-picker.ts:256-264` | Microsoft refused the file details | Check access | None |
| `Download URL not found in file data` | Console | `src/lib/utils/onedrive-file-picker.ts:266-271` | No download address for the item | Pick another file | None |
| `Failed to download file: {status} {statusText}` | Console | `src/lib/utils/onedrive-file-picker.ts:273-279` | The download failed | Retry | None |
| `Failed to open OneDrive picker window` | Console | `src/lib/utils/onedrive-file-picker.ts:397-400` | The browser blocked the picker pop-up | Allow pop-ups for the site | Browser settings |
| `Not in browser environment` | Console | `src/lib/utils/onedrive-file-picker.ts:288-290` | Not reachable from the normal screens | None | None |

### 10.5 Side Panel File Browser (Terminal Files)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Start the chat to use this terminal.` | Inline | `src/lib/components/chat/FileNav.svelte:1548-1559` | The terminal works per saved chat and the chat has not been sent yet | Send a first message | None |
| `No Terminal connection configured.` / `Add your Open Terminal URL and API key in Settings → Integrations.` | Inline | `src/lib/components/chat/FileNav.svelte:1560-1574` | No usable terminal | Configure or select a terminal | `workspace-tools-tool-servers-mcp-and-terminals.md` |
| `Failed to load directory. Check your Terminal connection in Settings → Integrations.` | Inline (not translated) | `src/lib/components/chat/FileNav.svelte:741-745` | Listing the folder failed | Check the terminal | Terminal server |
| `Failed to load folder` | Error | `src/lib/components/chat/FileNav.svelte:793-800` | Expanding a sub-folder failed | Retry | Terminal server |
| `Failed to search files` | Inline | `src/lib/components/chat/FileNav.svelte:552-555` | The terminal's search failed | Retry | Terminal server |
| `No matches` | Inline | `src/lib/components/chat/FileNav.svelte:1888-1892` | Search found nothing | Change the search | None |
| `This folder is empty` | Inline | `src/lib/components/chat/FileNav.svelte:2009-2014` | Empty folder | None | None |
| `Uploading...` | Inline | `src/lib/components/chat/FileNav.svelte:2000-2004` | Upload into the terminal in progress | Wait | None |
| `Drop to upload` | Inline | `src/lib/components/chat/FileNav.svelte:1585-1594` | Dragging files over a writable folder | Drop | None |
| `Upload failed: {error}` | Error | `src/lib/components/chat/FileNav.svelte:1100-1103` | A file or folder could not be uploaded; `{error}` may be `Invalid upload path: {path}` or `Unable to read a dropped file or folder.` | Rename the item or retry | Terminal server |
| `Preparing download...` | Inline (loading pop-up) | `src/lib/components/chat/FileNav.svelte:983`, `:1361` | A download or ZIP is being prepared | Wait | None |
| `Download failed` | Error | `src/lib/components/chat/FileNav.svelte:989-992`, `:1364-1367` | The terminal did not return the file or ZIP | Retry | Terminal server |
| `Folder created` / `Failed to create folder` | Success / Error | `src/lib/components/chat/FileNav.svelte:1147-1149` | **New Folder** | Retry with another name | None |
| `File created` / `Failed to create file` | Success / Error | `src/lib/components/chat/FileNav.svelte:1174` | **New File** | As above | None |
| `{name} deleted` / `Failed to delete {name}` | Success / Error | `src/lib/components/chat/FileNav.svelte:1185-1187` | **Delete** on one item | None | Read-only folder |
| `Deleted {ok} of {total} items` | Success or Error | `src/lib/components/chat/FileNav.svelte:1339-1341` | Bulk delete | Check what remains | None |
| `Moved {name}` | Success | `src/lib/components/chat/FileNav.svelte:1229-1231` | Drag to move succeeded (a refusal shows the terminal's own text) | None | None |
| `Renamed to {name}` | Success | `src/lib/components/chat/FileNav.svelte:1268-1272` | Rename succeeded (a refusal shows the terminal's own text) | None | None |
| `File saved` / `Failed to save file` | Success / Error | `src/lib/components/chat/FileNav.svelte:1875-1877` | **Save** in the file editor | Retry | Read-only file |
| `Copied to clipboard` | Success | `src/lib/components/chat/FileNav.svelte:1737-1740` | **Copy** of a file's text | None | None |
| `Path copied` | Success | `src/lib/components/chat/FileNav/FileEntryRow.svelte:409-412` | **Copy Path** | None | None |
| `Read-only` | Inline | `src/lib/components/chat/FileNav/FileNavToolbar.svelte:136-140`; `src/lib/components/chat/FileNav/FileEntryRow.svelte:322-324` | The terminal marks the folder or item read-only | None | Terminal permissions |
| `Error previewing file: {error}` | Inline | `src/lib/components/chat/FileNav.svelte:937-942` | A Word, Excel or PowerPoint preview failed (`{error}` may be `Preview failed` or `Unknown error`) | Download instead | None |
| `Could not read file.` | Inline | `src/lib/components/chat/FileNav/FilePreview.svelte:507-510` | The terminal returned nothing readable | Download instead | None |
| `JSON parse error: {error}` | Inline | `src/lib/components/chat/FileNav/FilePreview.svelte:470-476` | A JSON file is not valid | Fix the file | None |
| `Your browser does not support the video tag.` / `Your browser does not support the audio tag.` | Inline | `src/lib/components/chat/FileNav/FilePreview.svelte:313-324` | The browser cannot play the file | Download instead | None |
| `Extracting text and comparing…` | Inline | `src/lib/components/chat/FileNav/FileCompare.svelte:222-225` | **Compare** in progress (a failure shows the terminal's text with **Retry**) | Wait | None |
| `No text differences` | Inline | `src/lib/components/chat/FileNav/FileCompare.svelte:248-249` | The two files have the same text | None | None |
| `Failed to open database` / `Query failed` | Inline | `src/lib/components/chat/FileNav/SqliteView.svelte:49`, `:85`, `:102` | A SQLite file could not be opened or a query failed | Check the query | None |
| `No servers detected` | Inline | `src/lib/components/chat/FileNav/PortList.svelte:91-94` | No server is listening inside the terminal | None | None |

### 10.6 Log Lines That Explain Symptoms

Server log lines (not shown to users); they may include file ids and user ids, which are personal data.

| Log line | Meaning | Source |
|---|---|---|
| `Error processing file: {file_item.id}` | Processing failed; the reason is in `data.error` | `backend/open_webui/routers/files.py:259-260` |
| `Refusing to auto-link file {file_item.id} to knowledge {knowledge_id}: user {user.id} lacks write access` | A knowledge-base upload by someone without write access was stored but not linked | `backend/open_webui/routers/files.py:221-225` |
| `Failed to link file {file_item.id} to knowledge {knowledge_id}: {e}` | Knowledge-base link failed after processing | `backend/open_webui/routers/files.py:255-256` |
| `Video file detected (%s), skipping text extraction` | A video was stored without extraction | `backend/open_webui/routers/files.py:180` |
| `Failed to clean up local cache for {file_path}: {e}` | The local copy of a cloud file could not be removed | `backend/open_webui/routers/files.py:107-108` |
| `Failed to update knowledge {knowledge.id} after content change for file {id}: {e}` | Replacing a file's text did not reach a knowledge base | `backend/open_webui/routers/files.py:772-773` |
| `Error deleting files` / `Error getting file content` | Delete or download failures (10.1) | `backend/open_webui/routers/files.py:586`, `:846`, `:895`, `:1046` |
| `File {file_path} not found in local storage.` | Deleting a file whose local bytes were already gone | `backend/open_webui/storage/provider.py:83-86` |
| `Error uploading file to S3: {e}` (also `GCS` and `Azure Blob Storage` forms) | The cloud upload failed; the user saw `[ERROR: Error uploading file]` | `backend/open_webui/storage/provider.py:163-164`, `:234-235`, `:298-299` |
| `Error deleting file from S3: {e}` (also GCS and Azure forms) and `Error deleting all files from S3: {e}` (also GCS and Azure forms) | Cloud deletions failed; the user saw `[ERROR: Error deleting files]` | `backend/open_webui/storage/provider.py:181-182`, `:198-199`, `:255-256`, `:269-270`, `:319-320`, `:331-332` |
| `Error inserting a new file: {e}` | The record could not be created | `backend/open_webui/models/files.py:149-151` |
| `Error fetching pending files for knowledge {knowledge_id}: {e}` | Pending-file list for a knowledge base failed | `backend/open_webui/models/files.py:441-443` |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it never changes settings, permissions, files or data. File names and contents can
be personal or health information; when escalating, prefer the **file id** and the time over the name.
The id appears in the address bar when the file is opened in a new tab from the viewer's title link
(`/api/v1/files/{id}/content`; `src/lib/components/common/FileItemModal.svelte:263-281`).

### 11.1 "It says my file type is not allowed"

**Symptom.** A red pop-up `[ERROR: File type {file_extension} is not allowed]`, sometimes with nothing
where the type belongs (a file without an extension).

**Likely causes, in order.**
1. The admin set **Allowed File Extensions** and this extension is not in it
   (`backend/open_webui/routers/files.py:354-362`).
2. The list contains upper-case entries or dots (`PDF`, `.pdf`), which never match (5.6).
3. The file has no extension.

**Diagnostic steps.** Read the type in the message. Check the file name ends in an extension. Ask an
administrator for the current **Allowed File Extensions** value (Admin Settings > Documents > Files).

**Resolution.** Use or convert to an allowed type. Images attached through the chat composer are not
subject to the list.

**Escalation.** To the MedIT GPT administrators: the message, the extension, the time; point out the
lower-case, no-dot rule if the list looks wrong.

### 11.2 "It says my file is too large"

**Symptom.** `File size should not exceed {maxSize} MB.` before anything uploads, or after a cloud-picker
upload
`Oops! The file you're trying to upload is too large. Please upload a file that is less than {max_size} MB.`

**Likely causes, in order.** The admin's **Max Upload Size** (`rag.file.max_size`) is lower than the file
(`src/lib/components/chat/MessageInput.svelte:1106-1124`; `backend/open_webui/routers/files.py:394-400`).

**Diagnostic steps.** Compare the file size with the number in the message.

**Resolution.** Compress or split the file, or attach only the needed part. For images, **Image
Compression** (Settings > Interface > File) reduces size before upload.

**Escalation.** Requests to raise the limit go to the administrators with the business reason.

### 11.3 "I can only attach a few files at a time"

**Symptom.** `You can only chat with a maximum of {maxCount} file(s) at a time.`

**Likely causes, in order.** **Max Upload Count** is set; the count includes files already attached to
the message being written (`src/lib/components/chat/MessageInput.svelte:1089-1101`).

**Diagnostic steps.** Count the chips already above the message box.

**Resolution.** Remove some chips or send in several messages; for a large set of documents, a
knowledge base is the intended tool (`knowledge-bases.md`).

**Escalation.** Only if the limit blocks normal work.

### 11.4 "I got a yellow warning after uploading" or "The AI says it can't see my document"

**Symptom.** A yellow pop-up right after the upload finishes, and the file chip is still attached; or the
answer says the document is empty or unreadable.

**Likely causes, in order.**
1. No text could be extracted:
   `The content provided is empty. Please ensure that there is text or data present before proceeding.` (scanned PDFs and photos of documents without text recognition)
   (`backend/open_webui/routers/retrieval.py:1819-1820`).
2. An image went through processing: `File type {content_type} is not supported for processing`
   (`backend/open_webui/routers/files.py:186-187`).
3. A server-side component failed (Pandoc missing, vector store unavailable, extraction engine error)
   (section 10.2).
4. The file was set to **Using Focused Retrieval** and the question did not match the passages; or the
   model lacks a needed capability (5.10; `chat-composer-and-message-display.md`).

**Diagnostic steps.** Ask for the exact warning text. Open the chip: a low `{COUNT} extracted lines`
figure or `No content` confirms poor extraction (`src/lib/components/common/FileItemModal.svelte:322-333`,
`:440-505`). Try a text-based copy of the same document.

**Resolution.** Provide a text-based PDF or Word file; switch the chip to **Using Entire Document** for
short documents; for images, use a vision model and attach the image directly.

**Escalation.** Failures of type 3, or the same warning for many users, go to the platform maintainer
with the warning text, file type, approximate size and time.

### 11.5 "My file is stuck with a spinner"

**Symptom.** The chip keeps spinning; a message sent meanwhile waits in the queue.

**Likely causes, in order.**
1. Processing a large file, audio transcription or a slow embedding service takes time; the browser
   waits up to about two hours (`backend/open_webui/routers/files.py:643-673`).
2. The server restarted during processing; nothing resumes it (section 8).
3. The network connection to the server dropped.

**Diagnostic steps.** Ask the size and type. Ask the user to refresh and look at the chip again in the
message, or reopen the file viewer.

**Resolution.** Wait a few minutes for large files; otherwise remove the chip and attach the file again.

**Escalation.** If uploads of ordinary files stay pending for many users, escalate to the platform
maintainer (server health, embedding service, extraction engine) with times.

### 11.6 "My upload fails with [ERROR: …]"

**Symptom.** A red pop-up such as `[ERROR: No space left on device]`-style operating-system text,
`[ERROR: Error uploading file]`, or after an audio upload `[ERROR: The server is out of storage space.]`.

**Likely causes, in order.** The server's storage is full or not writable, or the cloud storage service
refused the file (section 5.20).

**Diagnostic steps.** Record the exact text and time; check whether other users are affected.

**Resolution.** None at tier 1 beyond asking the user to try later.

**Escalation.** Treat as a platform incident: send the message, time, and whether it affects everyone, to
the platform maintainer. Do not delete files to "make space".

### 11.7 "My old chat says 'Image unavailable'" or "The file in my chat is empty now"

**Symptom.** An image in an older message shows `Image unavailable`; a file chip opens with `No content`
or a preview error; answers ignore the file.

**Likely causes, in order.**
1. The file was deleted (by the user in the Files manager, through a knowledge-base removal, or by an
   administrator's **Reset Upload Directory**) (5.12-5.14).
2. The person viewing the chat may not read the file (for example someone opening a shared chat whose
   file was not recorded in `chat_file`) (3.2, 6.3).
3. The stored bytes are missing from storage.

**Diagnostic steps.** Ask whether the user deleted files recently and whether they own the chat. Ask an
administrator whether a reset was performed.

**Resolution.** Attach the file again in a new message.

**Escalation.** If many users report it at once, escalate as possible data loss with times.

### 11.8 "A file vanished from my knowledge base"

**Symptom.** A document is no longer listed in a knowledge base.

**Likely causes, in order.** The file was deleted from someone's Files manager (deletion removes it from
every knowledge base, `backend/open_webui/routers/files.py:1026-1037`); an administrator deleted all
files; or it was removed in the knowledge base itself (`knowledge-bases.md`).

**Diagnostic steps.** Ask who uploaded it and whether they cleaned up their Files list.

**Resolution.** Upload it to the knowledge base again.

**Escalation.** Repeated disappearances go to the administrators.

### 11.9 "My colleague can't open a file I attached"

**Symptom.** The colleague sees `We could not find what you're looking for :/`, `Image unavailable` or
an empty preview.

**Likely causes, in order.** Files are private to the uploader; a colleague can open one only through a
knowledge base, channel, shared chat link or workspace model they can read (3.2). Files in shared notes
are not covered by any rule (3.5).

**Diagnostic steps.** Ask how the file was shared. A chat simply viewed together, or a note, does not
share the file.

**Resolution.** Share through a knowledge base or channel, or share the chat with a link.

**Escalation.** If the file should be visible under these rules but is not, send the file id, the
sharing route and both users' roles (no file contents) to the administrators.

### 11.10 "My Files list shows files I never uploaded"

**Symptom.** Entries such as `generated-image.png`, `screen-capture-{timestamp}.png`,
`Pasted_Text_{timestamp}.txt` or `clipboard-image.png`; for an administrator, other people's files.

**Likely causes, in order.** Files created by the user's own actions (5.17); for administrators, the list
includes every user's files while `BYPASS_ADMIN_ACCESS_CONTROL` is on (3.4).

**Diagnostic steps.** Match the names against 5.17; check the user's role.

**Resolution.** Explain; the user may delete their own generated files.

**Escalation.** None, unless a non-admin sees files that are not theirs (security: refer to the platform
maintainer).

### 11.11 "The preview says it failed to load"

**Symptom.** `Failed to load PDF.`, `Failed to load DOCX file. Please try downloading it instead.`,
`Failed to load PPTX file. Please try downloading it instead.` or
`Failed to load Excel/CSV file. Please try downloading it instead.`

**Likely causes, in order.** The file is gone or unreadable to this user (5.14, 3.2); the file is damaged
or uses features the in-browser previewer cannot read; the file is protected with a password.

**Diagnostic steps.** Try the **Content** tab and the title link (download).

**Resolution.** Download and open locally; the model can still use the extracted text if processing
succeeded.

**Escalation.** Only if every preview of a type fails for everyone (possible front-end problem).

### 11.12 "My PowerPoint preview looks wrong"

**Symptom.** Fonts, layout or graphics differ from PowerPoint; SmartArt or animations are missing.

**Likely causes, in order.** The preview is drawn approximately in the browser: no full theme support,
SmartArt or animations, and EMF or WMF pictures are skipped (`src/lib/utils/pptxToHtml.ts:1-9`,
`:1038-1056`).

**Resolution.** Explain that the preview is approximate; download for an exact view.

**Escalation.** None.

### 11.13 "There's no Google Drive or OneDrive option"

**Symptom.** The **+** menu lacks **Google Drive** or **Microsoft OneDrive**, or OneDrive offers only one
account kind.

**Likely causes, in order.** The admin switches are off (default); the environment identifiers are not
set; uploads are not allowed for this user or model (5.15, 5.16;
`src/lib/components/chat/MessageInput/InputMenu.svelte:393-437`, `:687-716`).

**Diagnostic steps.** Check whether **Upload Files** is available; if it is greyed, see
`chat-composer-and-message-display.md`.

**Resolution.** Explain that the integrations are an administrator decision.

**Escalation.** Requests go to the administrators; whether the integrations should be offered at all is
TO BE CONFIRMED (section 14).

### 11.14 "Google Drive says 'Error accessing Google Drive: …'"

**Symptom.** A red pop-up starting `Error accessing Google Drive:`.

**Likely causes, in order.** By inner text (section 10.4): `Google Drive API credentials not configured`
(environment identifiers missing); `OAuth error occurred` or `Failed to get access token` (pop-up
blocked or closed, or access refused); `Failed to download file ({status}): {errorText}` (no permission
on that Drive file).

**Diagnostic steps.** Ask for the full text; check the browser allows pop-ups for the site; try another
file the user owns.

**Resolution.** Allow pop-ups and sign in again; or download the file from Drive and use **Upload Files**.

**Escalation.** Configuration texts go to the administrators.

### 11.15 "Nothing happens when I pick a file in OneDrive"

**Symptom.** The picker closes, or never opens, and no file appears.

**Likely causes, in order.** OneDrive errors are not shown to the user (5.16): pop-up blocked
(`Failed to open OneDrive picker window`), sign-in failure, missing configuration
(`Sharepoint URL not configured`), or a download refusal.

**Diagnostic steps.** Ask the user to allow pop-ups and retry; if comfortable, ask for a screenshot of the
browser console messages, which use the texts in section 10.4.

**Resolution.** Download the file from OneDrive and use **Upload Files**.

**Escalation.** Configuration texts go to the administrators with the console text.

### 11.16 "My image came out smaller or blurry"

**Symptom.** An attached image is reduced in size.

**Likely causes, in order.** The user's **Image Compression** is on, or the administrator set a maximum
width or height, which applies to everyone (5.7).

**Diagnostic steps.** Check Settings > Interface > File > **Image Compression** and its **Manage** sizes.

**Resolution.** Turn personal compression off or enlarge its sizes; the administrator cap cannot be
lifted by the user.

**Escalation.** Requests to change the cap go to the administrators.

### 11.17 "I removed the file from my message but it's still in my Files"

**Symptom.** After pressing the chip's **x**, the file still appears in the Files manager.

**Likely causes, in order.** Removing a chip only detaches it from the message being written
(`src/lib/components/chat/MessageInput.svelte:2012-2016`).

**Resolution.** Delete it in **Settings > Data Controls > Manage Files** if it should go.

**Escalation.** None.

### 11.18 "An image from a website shows the MedIT GPT icon instead"

**Symptom.** An image that should come from another site shows the site icon.

**Likely causes, in order.** Outside images are replaced with the site icon except where allowed
(Markdown images in responses) (5.18; `src/lib/utils/safeImageUrl.ts:22-38`).

**Resolution.** Explain; download the image and attach it if needed.

**Escalation.** None.

### 11.19 "All my files and knowledge bases are empty"

**Symptom.** The Files manager is empty for everyone; knowledge bases exist but have no documents;
memories may no longer be used.

**Likely causes, in order.** An administrator used **Reset Upload Directory**, which deletes every file
and resets the vector store (5.13); or a storage or vector-store outage.

**Diagnostic steps.** Ask the administrators whether a reset was done and when; note when users first
noticed.

**Resolution.** None at tier 1.

**Escalation.** Urgent: to the platform maintainer as possible data loss, with times; recovery depends on
backups (TO BE CONFIRMED).

### 11.20 "Can you restore a file I deleted?"

**Symptom.** A user deleted a file and wants it back.

**Likely causes, in order.** Deletion is permanent in the application (5.12).

**Resolution.** Ask the user to upload their own copy again.

**Escalation.** Only if no copy exists and the file is important: the platform maintainer, with the time
of deletion; whether backups allow recovery is TO BE CONFIRMED.

### 11.21 "I deleted a file without being asked"

**Symptom.** A file disappeared from the Files manager on one click.

**Likely causes, in order.** Shift was held while clicking the bin, which skips the confirmation
(`src/lib/components/layout/FilesModal.svelte:361-373`).

**Resolution.** Explain; see 11.20.

**Escalation.** None.

### 11.22 "Clicking the file downloads it instead of opening it"

**Symptom.** Opening a file from the viewer title link downloads it.

**Likely causes, in order.** Only PDFs and plain-text files open in the browser; other types download
(`backend/open_webui/routers/files.py:826-835`).

**Resolution.** Use the viewer's **Preview** tab to look at it inside MedIT GPT.

**Escalation.** None.

### 11.23 "My downloaded image is called generated_image.png"

**Symptom.** Downloading an image from the full-screen preview saves it as `generated_image.{type}`.

**Likely causes, in order.** The preview names every download after the "Generated Image" label
(`src/lib/components/common/ImagePreview.svelte:92-95`).

**Resolution.** Rename the downloaded file.

**Escalation.** None.

### 11.24 "My file won't attach in a temporary chat"

**Symptom.** `Failed to extract content from the file: {error}` in a temporary chat.

**Likely causes, in order.** Temporary chats read files in the browser and support only PDFs, Word
`.docx`, OpenDocument files and text-like files (5.8).

**Resolution.** Use a saved chat, or convert the file.

**Escalation.** None.

### 11.25 "The side panel Files tab says 'No Terminal connection configured.'"

**Symptom.** The **Files** tab shows that text, or `Start the chat to use this terminal.`

**Likely causes, in order.** No usable terminal is selected, or the terminal works per saved chat and the
chat has not started (5.19).

**Resolution.** Send a first message, or select a terminal; this tab is not where MedIT GPT uploads are
kept (those are in the Files manager).

**Escalation.** Terminal questions follow `workspace-tools-tool-servers-mcp-and-terminals.md`.

## 12. Local Customisations

**This area matches upstream Open WebUI v0.11.4.** A read-only `git diff main...uoft` and `git diff`
(working tree, 2026-10-08) over every in-scope path (the files router and model, `chats.py`, the storage
provider, `utils/files.py`, the files access-control module, `config.py`, `constants.py`, the Files
manager, file item and viewer, the six preview components, `FileNav.svelte` and `FileNav/`, the drop
overlay and placeholder, `src/lib/apis/files/`, and the seven utilities) show no differences.

Indirect points:

- The fork replaced `static/favicon.png` with a U of T icon. That image is also the stand-in for blocked
  outside images (5.18; `src/lib/utils/safeImageUrl.ts:3-6`, whose licence comment marks it as covered
  by the licence's branding terms).
- The uncommitted change in `src/lib/components/chat/Messages/Markdown/HTMLToken.svelte` affects only
  status lines (the fork's **Hide Processing Details**); the HTML file embedding block cited in 5.11 is
  unchanged.
- The uncommitted changes to `src/lib/i18n/locales/en-US/translation.json` do not touch any key quoted
  in this document.

## 13. Source File Index

### 13.1 Server Files in Scope

| File | Role here |
|---|---|
| `backend/open_webui/routers/files.py` | Every `/api/v1/files` endpoint: upload, processing hand-off, listing, search, count, status stream, content, rename, delete, delete all |
| `backend/open_webui/models/files.py` | The `file` table, response models and repository methods |
| `backend/open_webui/models/chats.py` | The `chat_file` link table and its helpers (`:217-243`, `:2571-2664`) |
| `backend/open_webui/storage/provider.py` | Local, S3, Google Cloud Storage and Azure storage providers |
| `backend/open_webui/utils/files.py` | Image and audio helpers: images sent to models, response images and audio saved as files |
| `backend/open_webui/utils/access_control/files.py` | Read and write rules for files and folder entries |
| `backend/open_webui/config.py` | Storage variables, upload limits, compression, cloud-picker switches, permission defaults |
| `backend/open_webui/constants.py` | Message texts (`NOT_FOUND`, `EMPTY_CONTENT`, `FILE_TOO_LARGE`, storage `[ERROR: …]` texts) |

### 13.2 Server Files Cited for Context

| File | Why cited |
|---|---|
| `backend/open_webui/main.py` | Router mount, `/api/config` file and picker fields, `chat_file` writes |
| `backend/open_webui/env.py` | `DATA_DIR`, `USE_SLIM_DOCKER`, image type fallback |
| `backend/open_webui/events.py` | File events, actor fields, event sinks |
| `backend/open_webui/internal/db.py` | SQLite connection settings (no foreign-key enforcement) |
| `backend/open_webui/migrations/versions/7e5b5dc7342b_init.py` | Initial `file` table |
| `backend/open_webui/migrations/versions/c440947495f3_add_chat_file_table.py` | `chat_file` migration |
| `backend/open_webui/models/channels.py` | `channel_file` table and channel access for files |
| `backend/open_webui/models/knowledge.py` | `knowledge_file` table; knowledge bases by file |
| `backend/open_webui/models/models.py` | Models that reference a file |
| `backend/open_webui/retrieval/utils.py` | How attached files are used in answers; folder files |
| `backend/open_webui/retrieval/vector/async_client.py`, `backend/open_webui/retrieval/vector/dbs/chroma.py`, `backend/open_webui/retrieval/vector/dbs/pgvector.py` | What a vector-store reset removes |
| `backend/open_webui/routers/audio.py` | Transcription during upload processing and its messages |
| `backend/open_webui/routers/chats.py` | Confirms chat deletion does not delete files |
| `backend/open_webui/routers/images.py` | Generated images saved as files and linked to chats |
| `backend/open_webui/routers/knowledge.py` | File deletion through knowledge bases; retention switch |
| `backend/open_webui/routers/memories.py` | Memory vectors live in the vector store |
| `backend/open_webui/routers/models.py` | Model background images; failed-import clean-up |
| `backend/open_webui/routers/retrieval.py` | `process_file`, limits saving, web-address files, reset endpoints, processing messages |
| `backend/open_webui/utils/misc.py` | Content-type matching and the speech-to-text default types |
| `backend/open_webui/utils/notifications.py` | Personal notification webhooks for processing failures |
| `backend/open_webui/utils/tools.py` | Built-in chat-file tools and the `file_upload` permission |

### 13.3 Front-End Files in Scope

| File | Role here |
|---|---|
| `src/lib/apis/files/index.ts` | Browser client for the files router, including the status stream reader |
| `src/lib/components/layout/FilesModal.svelte` | The Files manager |
| `src/lib/components/common/FileItem.svelte` | File chips |
| `src/lib/components/common/FileItemModal.svelte` | The file viewer with **Content** and **Preview** tabs |
| `src/lib/components/common/PDFViewer.svelte` | PDF preview |
| `src/lib/components/common/DocxPreview.svelte` | Word preview |
| `src/lib/components/common/PptxPreview.svelte` | Slide viewer for PowerPoint previews |
| `src/lib/components/common/PdfPagesPreview.svelte` | PDF with page thumbnails, used by the terminal browser (`:1-60`, `:140-170`) |
| `src/lib/components/common/ImagePreview.svelte` | Full-screen image preview and download |
| `src/lib/components/common/Image.svelte` | Image display, `Image unavailable`, outside-image filter |
| `src/lib/components/chat/FileNav.svelte` | Side-panel terminal file browser |
| `src/lib/components/chat/FileNav/FileNavToolbar.svelte` | Breadcrumbs, sort, actions menu |
| `src/lib/components/chat/FileNav/FileEntryRow.svelte` | One row: open, download, copy path, rename, delete, drag to move |
| `src/lib/components/chat/FileNav/BulkActionBar.svelte` | Multi-select bar |
| `src/lib/components/chat/FileNav/FileCompare.svelte` | Text comparison of two files |
| `src/lib/components/chat/FileNav/FilePreview.svelte` | Terminal file previews and editor |
| `src/lib/components/chat/FileNav/FileCodeEditor.svelte`, `src/lib/components/chat/FileNav/CellEditor.svelte` | Code editors for files and notebook cells (`:1-30`) |
| `src/lib/components/chat/FileNav/NotebookView.svelte` | Notebook preview with cell execution (`:1-30`, `:220-315`) |
| `src/lib/components/chat/FileNav/SqliteView.svelte` | SQLite database preview |
| `src/lib/components/chat/FileNav/JsonTreeView.svelte` | JSON tree preview (`:1-30`) |
| `src/lib/components/chat/FileNav/PortList.svelte`, `src/lib/components/chat/FileNav/PortPreview.svelte` | Servers listening in the terminal and their preview (`:1-30`, `:125-240`) |
| `src/lib/components/chat/FileNav/Icon.svelte`, `src/lib/components/chat/FileNav/FileTypeIcon.svelte`, `src/lib/components/chat/FileNav/fileIcon.ts` | Icons only; no messages (`:1-25`, `:1-15`, `:1-30`) |
| `src/lib/components/chat/MessageInput/FilesOverlay.svelte` | The drop overlay |
| `src/lib/components/AddFilesPlaceholder.svelte` | `Add Files` / `Drop any files here to upload` |
| `src/lib/utils/documentPreview.ts` | Page-number helpers for previews (`:1-21`) |
| `src/lib/utils/docxToHtml.ts` | Fallback Word conversion |
| `src/lib/utils/excelToTable.ts` | Spreadsheet to table |
| `src/lib/utils/pptxToHtml.ts` | PowerPoint slides drawn as pictures |
| `src/lib/utils/google-drive-picker.ts` | Google Drive picker |
| `src/lib/utils/onedrive-file-picker.ts` | OneDrive picker |
| `src/lib/utils/safeImageUrl.ts` | Outside-image filter |

### 13.4 Front-End Files Cited for Context

| File | Why cited |
|---|---|
| `src/lib/components/chat/MessageInput.svelte` | The composer's upload flow, limits, compression, paste, capture, pickers |
| `src/lib/components/chat/MessageInput/InputMenu.svelte`, `src/lib/components/chat/MessageInput/InputMenu/Files.svelte` | **+** menu items and **Attach Files** |
| `src/lib/components/chat/Chat.svelte` | Drop overlay placement; message queue while uploading |
| `src/lib/components/chat/ChatControls.svelte` | When the side panel shows the **Files** tab |
| `src/lib/components/chat/Messages/UserMessage.svelte` | How attachments show in sent messages |
| `src/lib/components/chat/Messages/Markdown/HTMLToken.svelte`, `src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens.svelte`, `src/lib/components/chat/Messages/ProfileImage.svelte`, `src/lib/components/common/RichTextInput/Image/image.ts` | Embedded HTML files and image filtering |
| `src/lib/components/chat/Settings/DataControls.svelte` | **Manage Files** entry point |
| `src/lib/components/chat/Settings/Interface/ManageImageCompressionModal.svelte`, `src/lib/components/common/InterfaceSettings.svelte` | Personal file settings |
| `src/lib/components/chat/Settings/Notifications.svelte` | Notification event labels |
| `src/lib/components/chat/SettingsModal.svelte`, `src/routes/(app)/+layout.svelte`, `src/routes/(app)/admin/settings/[tab]/+page.svelte` | Settings tabs and deep links |
| `src/lib/components/admin/Settings/Documents.svelte` | Admin file limits, integrations, Danger Zone |
| `src/lib/components/common/ConfirmDialog.svelte` | Default confirmation texts |
| `src/lib/components/channel/MessageInput.svelte`, `src/lib/components/notes/NoteEditor.svelte` | Channel and note uploads and compression |
| `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte`, `src/lib/components/workspace/Knowledge/KnowledgeBase/Files.svelte`, `src/lib/components/workspace/Models/ModelEditor.svelte` | Knowledge-base and model uploads |
| `src/lib/apis/retrieval/index.ts` | The unused upload-folder reset client |
| `src/lib/utils/index.ts` | Image compression, raster check, browser extraction, HEIC conversion, embed tokens |
| `src/lib/constants.ts` | Paste-as-file threshold |
| `src/routes/+layout.svelte` | Browser notifications (none for files) |
| `src/lib/i18n/locales/en-US/translation.json` | English text of dotted keys |
| `knowledgebase/tools/inventory.md` | Background loops list |

## 14. Open Questions

Everything below could not be established from the repository, or is a code behaviour that should be
confirmed in a test environment before support relies on it.

### 14.1 Live Data and Settings (TO BE CONFIRMED)

1. **Upload limits in production:** the stored values of `rag.file.allowed_extensions`,
   `rag.file.max_size`, `rag.file.max_count`, `file.image_compression_width` and
   `file.image_compression_height` (code defaults: none). If an extension list is set, whether its
   entries are lower case without dots (5.6).
2. **Cloud pickers:** the stored values of `google_drive.enable` and `onedrive.enable`, and whether the
   environment identifiers (`GOOGLE_DRIVE_CLIENT_ID`, `GOOGLE_DRIVE_API_KEY`, `ONEDRIVE_CLIENT_ID*`,
   `ONEDRIVE_SHAREPOINT_URL`, `ONEDRIVE_SHAREPOINT_TENANT_ID`, `ENABLE_ONEDRIVE_PERSONAL`,
   `ENABLE_ONEDRIVE_BUSINESS`) are set.
3. **Permissions and capabilities:** the live default and group values of `chat.file_upload` and
   `chat.web_upload`, and the `file_upload`, `vision` and `file_context` capabilities of each production
   model.
4. **Admin visibility:** the production value of `BYPASS_ADMIN_ACCESS_CONTROL` (whether admins' Files
   manager lists every user's files).
5. **Knowledge-base retention:** the production value of `ENABLE_KNOWLEDGE_FILE_RETENTION` (whether
   removing a file from a knowledge base deletes it).
6. **Event consumers:** whether admin event webhooks, Event functions or users' notification webhooks
   (`ui.enable_user_webhooks`) are configured; file events carry the actor's name and email, file names
   and up to 300 characters of replaced text (section 9).
7. **Processing settings** that decide what is extracted and whether files are embedded (extraction
   engine, bypass embedding, speech-to-text supported types); documented in
   `rag-retrieval-embeddings-and-vector-stores.md`.

### 14.2 Deployment and Storage (TO BE CONFIRMED)

8. **Which storage provider production uses** (`STORAGE_PROVIDER`), with which bucket, container or
   volume (names only), whether `STORAGE_LOCAL_CACHE` is off, and whether `S3_ENABLE_TAGGING` is on
   (which writes uploaders' emails and names into object tags).
9. **Refinement of the Phase 0 note** ("cloud providers keep a local copy unless
   `STORAGE_LOCAL_CACHE=false`"): the code removes the local copy only at the end of processing, so
   unprocessed uploads keep it, and every later read from cloud storage leaves a fresh local copy
   (6.5). Whether this matters for data residency needs the platform maintainer.
10. **Disk capacity and monitoring** for `DATA_DIR`, which by default also holds the database and vector
    store; who is alerted when it fills (5.20).
11. **Backups** of uploads, database and vector store, their retention and the restore procedure;
    deletion in the application is permanent (5.12, 5.13).
12. **Retention:** the code has no automatic expiry or clean-up of uploaded files, orphaned objects or
    files of deleted users; whether an organisational retention rule applies.
13. **Database engine:** SQLite or PostgreSQL in production; on SQLite the declared cascades from files to
    `chat_file`, `channel_file` and `knowledge_file` are not enforced as configured (5.14).
14. **Server operating system**, which decides the wording inside `[ERROR: {strerror}]` upload errors.
15. **Slim image:** whether production runs the slim build (local storage only).
16. **Identity-provider registrations** for the pickers: the Google and Microsoft applications, the
    Microsoft tenant, the registered sign-in return address (the site's own address), and whether users'
    networks and organisational policies allow the Google and Microsoft services the pickers load.

### 14.3 Product Behaviour to Confirm in a Test Environment

17. **Interrupted processing:** what users see if the server restarts while a file is processing
    (expected: the status stays `pending` or `processing` and the chip spins up to about two hours; no
    retry exists) (5.5, 8).
18. **`chat_file` duplicate check:** `insert_chat_files` compares link-row ids with file ids, so a message
    that re-attaches a file already linked to the chat may fail to link that message's other files;
    confirm the effect on shared-chat recipients opening files
    (`backend/open_webui/models/chats.py:2582-2586`, `:2611-2635`).
19. **After Reset Upload Directory:** the state of knowledge bases (link rows on SQLite), of memories
    (vectors removed), and whether **Reindex Knowledge and Memory Vectors** restores memory vectors.
20. **S3 delete-all** makes a single listing call without paging; whether large buckets are fully emptied
    (`backend/open_webui/storage/provider.py:187-202`).
21. **Notes:** whether collaborators on a shared note can open the note's attachments (no access rule
    covers notes, 3.5).
22. **HEIC photos:** the converted JPEG is uploaded under the original name and `image/heic` type
    (`src/lib/components/chat/MessageInput.svelte:1184-1192`); confirm display in common browsers.
23. **Images from cloud pickers or knowledge bases** go through processing and end with
    `File type {content_type} is not supported for processing` unless the extraction engine handles images; confirm
    the user experience.
24. **Google Drive multi-select:** the picker allows several files but only the first is uploaded.
25. **Unused code paths:** the browser client `uploadDir` targets a server route that does not exist, and
    `POST /api/v1/retrieval/reset/uploads` has no caller (2.2); the composer's Google Drive upload path in
    `Chat.svelte` is unreachable (`chat-composer-and-message-display.md`).
26. **Status for unprocessed files:** the non-streaming status call reports `pending` for files uploaded
    without processing (`backend/open_webui/routers/files.py:675`); relevant only to API users.
27. **Interface defects worth reporting upstream (unconfirmed):** the **Reset Upload Directory** label and
    description understate what it deletes (5.13); OneDrive failures are not shown to users (5.16);
    Files-manager sorting re-orders only loaded rows (5.9); image downloads from the preview are always
    named `generated_image` (5.10); `Failed to load PDF.`, `No content` and the terminal browser's
    directory error are not translated.

### 14.4 People and Process (TO BE CONFIRMED)

28. Who may use **Reset Upload Directory** in production, under what change control, and whether it
    should be used at all.
29. The escalation route and on-call contact for storage incidents and suspected data loss.
30. Who decides requests to raise upload limits or enable the cloud pickers.
31. Policy on administrators viewing other users' files in the Files manager (names and contents may be
    health information), and on support asking users for screenshots of previews.
32. Whether tier 1 may ask users for browser-console screenshots (needed for OneDrive failures).

### 14.5 Security-Sensitive Items

Security-sensitive: refer to the platform maintainer and U of T Information Security
(security.utoronto.ca). Recorded here without detail:

33. Server-side enforcement of the upload permission and of the file-count limit.
34. Personal information in stored object names, S3 object tags, persisting local copies and event
    payloads (privacy review; see also privacy.utoronto.ca).
35. Administrators' access to every file by id regardless of the bypass switch.
36. The HTML-file embedding endpoint and the sandbox settings of embedded frames.
37. How the cloud pickers handle access tokens in the browser.
