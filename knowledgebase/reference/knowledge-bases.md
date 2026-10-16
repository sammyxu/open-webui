# Knowledge Bases

## At a Glance

- **What a knowledge base is.** A named, shareable collection of documents (uploaded files, saved
  web pages and typed text, optionally arranged in directories) that MedIT GPT turns into searchable
  text and stores in the vector store under the knowledge base's own id, so models can draw on it in
  any chat (`backend/open_webui/models/knowledge.py:48-60`; `backend/open_webui/routers/knowledge.py:1480-1496`;
  `backend/open_webui/routers/files.py:199-254`). A file attached to a single chat is indexed only
  for itself and travels with that chat; a knowledge base lives on its own, can be shared with people
  and groups, and can be attached to custom models (section 4).
- **Where people work.** **Workspace › Knowledge** (`/workspace/knowledge`) is shown to admins and to
  people with the **Knowledge Access** permission (`workspace.knowledge`, off in code)
  (`src/routes/(app)/workspace/+layout.svelte:50`, `:84-88`, `:168-181`;
  `backend/open_webui/config.py:1737-1739`). Opening a knowledge base shows its files and directories at
  `/workspace/knowledge/{id}`.
- **Creating one** needs a name and a description (the form refuses either blank) and, optionally,
  sharing. Non-admins also need Knowledge Access on the server
  (`src/lib/components/workspace/Knowledge/CreateKnowledgeBase.svelte:28-51`;
  `backend/open_webui/routers/knowledge.py:328-334`).
- **Adding content.** The **+** (Add Content) menu offers **New directory**, **Upload files**, **Upload
  directory**, **Sync directory**, **Add webpage**, **Add text content** and **Reset**; files can also be
  dragged onto the page (`src/lib/components/workspace/Knowledge/KnowledgeBase/AddContentMenu.svelte:59-143`).
  Each upload is processed in the background: text is extracted, indexed for the file, indexed into the
  knowledge base, and only then linked to it. Until then the file shows a spinner; if processing fails
  the uploader sees a warning with the reason and the file is not added (section 5.6).
- **Sync directory mirrors a local folder.** Only new and changed files are uploaded, but anything in
  the knowledge base whose path and name are not in the chosen folder is removed, including files added
  another way (section 5.11).
- **Who can see and change it.** The owner, anyone given **Read** or **Write** access (directly, through
  a group, or **Public**), and admins, who see every knowledge base while `BYPASS_ADMIN_ACCESS_CONTROL`
  is on (its default) (`backend/open_webui/routers/knowledge.py:186-218`, `:1104-1138`;
  `backend/open_webui/config.py:2086-2092`). Write access is needed to add, remove, rename, move, reset,
  share or delete. Sharing rules are detailed in `users-groups-roles-and-permissions.md`.
- **Using it in conversation.** Attach it to a custom model (model editor › **Knowledge**) or mention it
  in a chat with `#` (also offered by `@` and by **+** › **Attach Knowledge**). With native function
  calling (the default), knowledge attached to a model is reached through built-in knowledge tools the
  model chooses to call, while knowledge mentioned in a chat is searched and added to the prompt before
  the reply. With nothing attached, the model's knowledge tools can search any knowledge base the person
  can read (section 5.21).
- **Removing a file deletes it by default.** When the person removing a file owns it (or is an admin)
  and `ENABLE_KNOWLEDGE_FILE_RETENTION` is off (its default), the file itself is deleted, not just
  unlinked, so it also disappears from any model or chat that used it
  (`backend/open_webui/routers/knowledge.py:1613-1675`; `backend/open_webui/config.py:985`).
- **Deleting a knowledge base** removes the record, its sharing, its search index and its entry in
  every custom model; it does not delete the files it contained, which stay in their owners' file lists.
  There is no undo or trash (`backend/open_webui/routers/knowledge.py:1702-1784`;
  `backend/open_webui/models/knowledge.py:798-806`).
- **Limits.** The code sets no limit on the number of knowledge bases or on files per knowledge base.
  Each file is subject to the site's **Max Upload Size** (`rag.file.max_size`) and **Allowed File
  Extensions** (`rag.file.allowed_extensions`); **Max Upload Count** applies only to chat uploads
  (`backend/open_webui/routers/files.py:353-401`; `src/lib/components/chat/MessageInput.svelte:1090-1100`).
- **Export and import.** Admins can export a knowledge base as a ZIP of extracted text (`.txt`), not
  the original files; there is no import (`backend/open_webui/routers/knowledge.py:2162-2202`).
- **Connected (external) knowledge bases** are read-only entries an admin creates over an existing
  collection in an external Qdrant, Milvus or pgvector database; they show **Connected** and **Read Only**
  badges, and the knowledge endpoints refuse to add files to, sync, reset or export them (section 5.26).
- **Fork status:** this area matches upstream Open WebUI v0.11.4. The fork's **Hide Processing Details**
  setting hides the model's knowledge tool calls from the person who turns it on (section 12).

## 1. Purpose and Who Uses It

A knowledge base gives a model a standing library to consult. Instead of attaching the same
documents to every chat, a person collects them once in Workspace › Knowledge, optionally shares the
collection with colleagues or groups, and then either builds a custom model around it or mentions it
in a chat with `#`. In this codebase a knowledge base is also called a **collection**: the chat
pickers and the file dialog label it `Collection`, and attached items carry the type `collection`
(`src/lib/components/chat/MessageInput/Commands/Knowledge.svelte:146-152`;
`src/lib/components/common/FileItem.svelte:111-123`, `:158-159`).

### 1.1 Knowledge Base Versus a File Attached to One Chat

| | File attached to a chat | Knowledge base |
|---|---|---|
| Where it is added | Chat composer (**+** › **Upload Files**, drag and drop, paste) | Workspace › Knowledge › a knowledge base › **+** |
| What is indexed | The file alone, in a vector collection named `file-{id}` | Every file in a collection named after the knowledge base id, plus each file's own `file-{id}` collection (`backend/open_webui/routers/retrieval.py:1946-1951`, `:1979-2017`) |
| Who can use it | The chat's owner, and people the chat is shared with | The owner, anyone it is shared with, and admins with the bypass on (section 3) |
| Reuse | Re-sent with later messages in the same chat only (`src/lib/components/chat/Chat.svelte:2908-2920`, `:3449-3468`) | Any chat, any custom model, any folder (project) that references it |
| Structure | Flat | Directories and sub-directories (`knowledge_directory`, section 6.4) |
| Size of the set | **Max Upload Count** per chat (`rag.file.max_count`) | No count limit in code (section 7.3) |
| When the model sees it | Retrieved into the prompt before the reply when the model's **File Context** capability is on | Depends on how it is attached and on the function-calling mode (section 5.21) |
| Lifecycle | Kept with the chat and the person's files | Kept until deleted by someone with write access; deleting it leaves the files in place (section 5.15) |

The two meet in one place: picking a single file from a knowledge base in the `#` list attaches that
file to the chat, not the whole knowledge base (`src/lib/components/chat/MessageInput/Commands/Knowledge.svelte:116-131`).

### 1.2 Who Uses It

| Who | What they do here | Evidence |
|---|---|---|
| People with **Knowledge Access** (`workspace.knowledge`) | Create knowledge bases, upload and organize content, share them | `backend/open_webui/routers/knowledge.py:328-334`; `src/routes/(app)/workspace/+layout.svelte:168-181` |
| Admins | Everything above for every knowledge base (while the bypass is on); export; rebuild indexes; reset the vector store; create connected knowledge bases | `backend/open_webui/routers/knowledge.py:374-384`, `:469-473`, `:894-899`, `:2162-2163`; `src/lib/components/admin/Settings/Documents.svelte:1547-1592` |
| People a knowledge base is shared with | Use it in chat with `#`, or through a custom model; open it in Workspace › Knowledge if they also have Knowledge Access; change it if they have Write | `backend/open_webui/routers/knowledge.py:221-283`; section 3 |
| Custom-model owners | Attach knowledge bases, single files and notes to a model so its users get them automatically | `src/lib/components/workspace/Models/Knowledge.svelte:172-300` |
| Every signed-in user | Mention knowledge bases they can read with `#`, `@` or **+** › **Attach Knowledge**, even without Knowledge Access | `backend/open_webui/routers/knowledge.py:221-231` (no workspace check); `src/lib/components/chat/MessageInput/Commands/Knowledge.svelte:101-114` |
| Tier-1 support | Explain behaviour, read error texts, collect identifiers; tier 1 does not change content, sharing or settings | `_research-prompt.md`, rule 14 |

Knowledge bases at MedIT GPT can hold sensitive documents. The admin export (section 5.16) and the
**File content** search contain the full extracted text of every file, and the list shows each owner's
name and email on hover (`src/lib/components/workspace/Knowledge.svelte:490-504`). Support should
identify a knowledge base by its name and id, not by opening or quoting its contents.

## 2. Navigation and URLs

URLs are relative to the site root; the production host name is TO BE CONFIRMED.

### 2.1 Pages, Panels and Entry Points

| Where | URL or path | What it shows | Who | Source |
|---|---|---|---|---|
| Workspace › Knowledge | `/workspace/knowledge` | The list of knowledge bases the person can read, with search, a view filter, a source filter and sorting | Admins; people with Knowledge Access. Others are sent to `/` | `src/routes/(app)/workspace/knowledge/+page.svelte:1-5`; `src/lib/components/workspace/Knowledge.svelte:287-560`; `src/routes/(app)/workspace/+layout.svelte:84-88` |
| Create dialog | `/workspace/knowledge/create` | The list with the **Create a knowledge base** dialog already open; closing it returns to `/workspace/knowledge` | Same | `src/routes/(app)/workspace/knowledge/create/+page.svelte:1-5`; `src/lib/components/workspace/Knowledge.svelte:191-197`, `:281-283` |
| A knowledge base | `/workspace/knowledge/{id}` | Name, description, file count, **Access** button, file and directory list, search, the **+** menu, a side drawer for one file's text | Anyone who can read it, if they can open the Workspace section | `src/routes/(app)/workspace/knowledge/[id]/+page.svelte:1-5`; `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1218-1706` |
| Workspace landing | `/workspace` | Redirects non-admins to the first section they may use (Models, then Knowledge, Prompts, Tools, Skills); admins to Models | Everyone | `src/routes/(app)/workspace/+page.svelte:6-24` |
| Chat composer `#` | Type `#` in the message box | `Folders`, `Collections` (knowledge bases) and `Files` (files inside knowledge bases) matching the typed text, plus a typed web or YouTube address | Every signed-in user | `src/lib/components/chat/MessageInput/Commands/Knowledge.svelte:84-131`, `:142-203`; `src/lib/components/chat/MessageInput.svelte:1515-1546` |
| Chat composer `@` | Type `@` | The same knowledge items listed above the models | Every signed-in user | `src/lib/components/chat/MessageInput/Commands/AtCommands.svelte:64-78`, `:172-213` |
| **+** › **Attach Knowledge** | Composer **+** menu | A searchable list of knowledge bases; the arrow (**Show Files**) lists the files inside one | Greyed, and attachments cleared, without upload rights (section 5.19) | `src/lib/components/chat/MessageInput/InputMenu.svelte:333-361`, `:594-611`; `src/lib/components/chat/MessageInput/InputMenu/Knowledge.svelte:187-300` |
| Model editor › **Knowledge** | Workspace › Models › a model (and Admin › Settings › Models) | **Select Knowledge** (notes, collections, files) and **Upload** | Model editors | `src/lib/components/workspace/Models/Knowledge.svelte:172-300`; `src/lib/components/workspace/Models/Knowledge/KnowledgeSelector.svelte:72-100` |
| Admin › Settings › Documents › **Danger Zone** | `/admin/settings/documents` (opens `/?settings=admin:documents`) | **Reset Vector Storage/Knowledge** and **Reindex Knowledge and Memory Vectors** | Admins | `src/lib/components/admin/Settings/Documents.svelte:1547-1592`; `src/routes/(app)/admin/settings/[tab]/+page.svelte:6-10`; `src/lib/i18n/locales/en-US/translation.json:2317-2319`, `:2330-2333` |
| Admin › Settings › Integrations › **Knowledge** | `/admin/settings/integrations` | **External Knowledge Sources**, where connected knowledge bases are created | Admins | `src/lib/components/admin/Settings/Integrations.svelte:338-340`; `src/lib/i18n/locales/en-US/translation.json:2475`, `:2480` |

The browser tab on the list reads `Knowledge / {WEBUI_NAME}`, which shows `Knowledge / MedIT GPT` with
the fork's default name (`src/lib/components/workspace/Knowledge.svelte:287-294`;
`backend/open_webui/env.py:951`). The Workspace tab shows a count next to **Knowledge**, which is the
number of knowledge bases the person can read (`src/routes/(app)/workspace/+layout.svelte:48-77`).

### 2.2 Knowledge API (`/api/v1/knowledge`)

The router is mounted at `/api/v1/knowledge` (`backend/open_webui/main.py:867`). "Verified" means any
signed-in user with role `user` or `admin`; the checks inside each endpoint are in section 3.1.

| Method and path | Guard | Purpose | Source |
|---|---|---|---|
| `GET /` | Verified | Page of 30 readable knowledge bases, each with `write_access` | `backend/open_webui/routers/knowledge.py:172-218` |
| `GET /search` | Verified | Same, filtered by `query` (name, description, owner name, email or username), `view_option` (`created` or `shared`), `source` (`local` or `external`), `order_by` (`name`, `created_at`, `updated_at`) and `direction`; used by the list page and the chat pickers | `backend/open_webui/routers/knowledge.py:221-283`; `backend/open_webui/models/knowledge.py:263-368` |
| `GET /search/files` | Verified | Files inside every readable knowledge base, by file name (or text with `include_content`) | `backend/open_webui/routers/knowledge.py:286-310`; `backend/open_webui/models/knowledge.py:370-468` |
| `POST /create` | Verified plus Knowledge Access (admins exempt) | Create a knowledge base with name, description and access grants | `backend/open_webui/routers/knowledge.py:318-366` |
| `POST /reindex` | Admin (checked inside) | Re-embed every file of every knowledge base | `backend/open_webui/routers/knowledge.py:374-461` |
| `POST /metadata/reindex` | Admin | Rebuild the knowledge-base search index (names and descriptions) | `backend/open_webui/routers/knowledge.py:469-494` |
| `GET`, `POST /external/connections`; `GET`, `PATCH`, `DELETE /external/connections/{id}`; `POST /external/connections/{id}/test`; `POST /external/connections/{id}/retrieve-test`; `POST /external/source/test`; `POST /external/knowledge/create`; `POST /external/source/create`; `PATCH /external/source/{id}` | Admin | Connected knowledge sources (section 5.26; configuration in `rag-retrieval-embeddings-and-vector-stores.md`) | `backend/open_webui/routers/knowledge.py:691-1086` |
| `GET /{id}` | Verified plus read access | One knowledge base and `write_access` | `backend/open_webui/routers/knowledge.py:1099-1138` |
| `POST /{id}/update` | Write access | Change name, description (and grants when sent) | `backend/open_webui/routers/knowledge.py:1146-1212` |
| `POST /{id}/access/update` | Write access | Replace the access grants | `backend/open_webui/routers/knowledge.py:1224-1276` |
| `GET /{id}/files/pending` | Read access | Files still being processed for this knowledge base and not yet linked; `stream=true` polls every 3 seconds for up to an hour | `backend/open_webui/routers/knowledge.py:1284-1343` |
| `GET /{id}/files` | Read access | Page of files in one directory (or the root), with sub-directories and breadcrumbs; 30 per page (admins may set `limit`) | `backend/open_webui/routers/knowledge.py:1351-1412` |
| `POST /{id}/file/add` | Write access plus read access to the file | Index an existing, already-processed file into the knowledge base and link it; the interface uses it only for **Add webpage** addresses that point to a file | `backend/open_webui/routers/knowledge.py:1425-1521` |
| `POST /{id}/file/update` | Write access | Re-index one linked file; not called by the interface | `backend/open_webui/routers/knowledge.py:1524-1605` |
| `POST /{id}/file/remove` | Write access | Unlink one file and remove its chunks; deletes the file when allowed (section 5.13) | `backend/open_webui/routers/knowledge.py:1613-1694` |
| `DELETE /{id}/delete` | Write access | Delete the knowledge base (section 5.15) | `backend/open_webui/routers/knowledge.py:1702-1784` |
| `POST /{id}/reset` | Write access | Remove every file link (and, by default, every directory) and the vector collection | `backend/open_webui/routers/knowledge.py:1792-1846` |
| `POST /{id}/sync/diff` | Write access | Compare a local folder manifest with the knowledge base | `backend/open_webui/routers/knowledge.py:1875-1967` |
| `POST /{id}/sync/cleanup` | Write access | Remove files and directories the sync found stale | `backend/open_webui/routers/knowledge.py:1980-2028` |
| `POST /{id}/files/batch/add` | Write access plus read access to each file | Add several existing files at once; not called by the interface | `backend/open_webui/routers/knowledge.py:2036-2154` |
| `GET /{id}/export` | Admin | ZIP of each file's extracted text | `backend/open_webui/routers/knowledge.py:2162-2202` |
| `POST /{id}/dirs/create` | Write access | New directory | `backend/open_webui/routers/knowledge.py:2253-2284` |
| `POST /{id}/dirs/{dir_id}/update` | Write access | Rename or move a directory | `backend/open_webui/routers/knowledge.py:2287-2321` |
| `DELETE /{id}/dirs/{dir_id}/delete` | Write access | Delete a directory, moving its files up (`move_files=true`) or deleting them | `backend/open_webui/routers/knowledge.py:2324-2373` |
| `POST /{id}/file/move` | Write access | Move a file to another directory or the root | `backend/open_webui/routers/knowledge.py:2376-2413` |

The front-end functions for these calls are in `src/lib/apis/knowledge/index.ts` (one function per
endpoint, lines 3-1158). Each reports the server's `detail` text as its error.

### 2.3 Related Endpoints Outside This Router

| Endpoint | Role in this area | Source |
|---|---|---|
| `POST /api/v1/files/` with `knowledge_id` and `directory_id` in its metadata | Every upload from a knowledge base page; the background task links the file once both indexing steps succeed | `backend/open_webui/routers/files.py:199-266`, `:435-446`; `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:438-450` |
| `GET /api/v1/files/{id}/process/status?stream=true` | The upload waits on this stream and turns a `failed` status into the warning the uploader sees | `backend/open_webui/routers/files.py:624-676`; `src/lib/apis/files/index.ts:46-89` |
| `POST /api/v1/files/{id}/rename`, `POST /api/v1/files/{id}/data/content/update`, `GET /api/v1/files/{id}/content` | **Rename**, editing a file's text in the drawer, and **Download** | `backend/open_webui/routers/files.py:965-1006`, `:714-786`, `:795`; `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:917-931`, `:938-967` |
| `DELETE /api/v1/files/{id}` | Deleting a file anywhere also unlinks it from every knowledge base and removes its chunks there | `backend/open_webui/routers/files.py:1013-1060` |
| `POST /api/v1/retrieval/process/url` | **Add webpage** | `backend/open_webui/routers/retrieval.py:2356-2427`; `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:303-398` |
| `POST /api/v1/retrieval/reset/db` | **Reset Vector Storage/Knowledge**: empties the vector store and deletes every knowledge base record | `backend/open_webui/routers/retrieval.py:3271-3284` |

## 3. Roles and Permissions

Three things decide what a person can do with a knowledge base: their role (`admin`, `user`; `pending`
accounts cannot use the application), their **permissions** (defaults plus groups, see
`users-groups-roles-and-permissions.md`), and the knowledge base's **access grants** (owner, Read,
Write, Public). The server checks grants on every request; the interface also hides controls based on
the `write_access` flag the server returns with each knowledge base
(`backend/open_webui/routers/knowledge.py:205-217`, `:1115-1128`).

### 3.1 Who Can Do What

"Write" means the person owns the knowledge base or holds a Write grant (directly, through a group, or
Public Write). "Read" means a Read grant, a group Read grant or Public. Admin rows assume
`BYPASS_ADMIN_ACCESS_CONTROL` is on, its default (section 3.4).

| Action | Owner | Write | Read | Admin | Anyone else | Source |
|---|---|---|---|---|---|---|
| See it in Workspace › Knowledge and the chat pickers | Yes | Yes | Yes | Yes (all) | No | `backend/open_webui/routers/knowledge.py:248-257`; `backend/open_webui/models/access_grants.py:741-800` |
| Open its page | Yes | Yes | Yes (marked `Read Only`) | Yes | `You do not have permission to access this resource. Please contact your administrator for assistance.` | `backend/open_webui/routers/knowledge.py:1099-1138`; `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1279-1291` |
| Use it in a chat or through a model | Yes | Yes | Yes | Yes | Skipped, with no message | `backend/open_webui/retrieval/utils.py:1566-1580`; `backend/open_webui/tools/builtin.py:3221-3237` |
| Create a knowledge base | Needs Knowledge Access | n/a | n/a | Yes | Needs Knowledge Access | `backend/open_webui/routers/knowledge.py:328-334` |
| Rename, edit description, change access | Yes | Yes | No | Yes | No | `backend/open_webui/routers/knowledge.py:1163-1177`, `:1239-1253` |
| Add files, web pages, text; directories; move; sync; reset | Yes | Yes | No | Yes | No | `backend/open_webui/routers/knowledge.py:1442-1456`, `:1809-1823`, `:2225-2250` |
| Remove a file from it | Yes | Yes | No | Yes | No | `backend/open_webui/routers/knowledge.py:1631-1645` |
| Removing also deletes the file itself | Only for files they own | Only for files they own | n/a | Yes, any file | n/a | `backend/open_webui/routers/knowledge.py:1673-1675` |
| Rename a file or edit its text in the drawer | Only files they own | Their own files, and files the knowledge base's owner owns | No | Yes | No (others see `We could not find what you're looking for :/`) | `backend/open_webui/routers/files.py:969-1005`, `:718-731`, `:783-787`; `backend/open_webui/utils/access_control/files.py:45-64` |
| Delete the knowledge base | Yes | Yes | No | Yes | No | `backend/open_webui/routers/knowledge.py:1716-1730` |
| Export as ZIP | No | No | No | Yes | No | `backend/open_webui/routers/knowledge.py:2162-2167`; `src/lib/components/workspace/Knowledge.svelte:509-513` |
| Rebuild indexes, reset the vector store, create connected knowledge bases | No | No | No | Yes | No | `backend/open_webui/routers/knowledge.py:380-384`, `:469-473`, `:894-899`; `backend/open_webui/routers/retrieval.py:3271-3275` |

Two details are easy to miss:

- **A shared Write grant is powerful.** A person with Write can delete the whole knowledge base, reset
  it, or remove files from it, not only add content (rows above). Removing someone else's file only
  unlinks it; the file stays with its owner (section 5.13).
- **Opening the page needs the Workspace section too.** A person without Knowledge Access is sent to
  `/` from any `/workspace/knowledge` address, even for a knowledge base shared with them with Write; they
  can still use it in chat (`src/routes/(app)/workspace/+layout.svelte:80-88`;
  `backend/open_webui/routers/knowledge.py:221-231`).

### 3.2 Permission Keys That Shape This Area

Labels are those on the group permission editor (`src/lib/components/admin/Users/Groups/Permissions.svelte`).
Defaults are code defaults seeded into the `user.permissions` setting; live values are data, TO BE
CONFIRMED (section 14.1).

| Key | Label | Code default | Seeded from | Effect here | Source |
|---|---|---|---|---|---|
| `workspace.knowledge` | Knowledge Access (`:87`) | off | `USER_PERMISSIONS_WORKSPACE_KNOWLEDGE_ACCESS` | Shows Workspace › Knowledge and allows creating knowledge bases | `backend/open_webui/config.py:1737-1739`, `:1943`; `backend/open_webui/routers/knowledge.py:328-330`; `src/routes/(app)/workspace/+layout.svelte:168` |
| `sharing.knowledge` | Knowledge Sharing (`:277`) | off | `USER_PERMISSIONS_WORKSPACE_KNOWLEDGE_ALLOW_SHARING` | Shows the Access List in the create form and the **Access** dialog | `backend/open_webui/config.py:1794-1796`, `:1959`; `src/lib/components/workspace/Knowledge/CreateKnowledgeBase.svelte:150`; `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1223` |
| `sharing.public_knowledge` | Knowledge Public Sharing (`:297`) | off | `USER_PERMISSIONS_WORKSPACE_KNOWLEDGE_ALLOW_PUBLIC_SHARING` | Offers **Public**; the server drops a Public grant from a non-admin without it | `backend/open_webui/config.py:1798-1800`, `:1960`; `backend/open_webui/routers/knowledge.py:336-342`, `:1179-1185`, `:1255-1261`; `backend/open_webui/utils/access_control/__init__.py:256-274` |
| `access_grants.allow_users` | Allow Sharing With Users (`:548`) | on | `USER_PERMISSIONS_ACCESS_GRANTS_ALLOW_USERS` | Sharing with named people; the server drops person grants from a non-admin without it | `backend/open_webui/config.py:1841-1843`; `backend/open_webui/utils/access_control/__init__.py:276-283` |
| `access_grants.allow_groups` | Allow Sharing With Groups (`:567`) | on | `USER_PERMISSIONS_ACCESS_GRANTS_ALLOW_GROUPS` | Sharing with groups; the server drops group grants from a non-admin without it | `backend/open_webui/config.py:1844-1846`; `backend/open_webui/utils/access_control/__init__.py:285-299` |
| `chat.file_upload` | Allow File Upload (`:592`) | on | `USER_PERMISSIONS_CHAT_FILE_UPLOAD` | Enables **+** › **Attach Knowledge**; without it the composer removes knowledge attachments (section 5.19); also gates the model editor's **Upload** | `backend/open_webui/config.py:1857`; `src/lib/components/chat/MessageInput/InputMenu.svelte:67-78`; `src/lib/components/workspace/Models/Knowledge.svelte:38-41`, `:207` |

No import or export permission exists for knowledge bases; export is admin-only. A permission is
granted if any of the person's groups grants it, otherwise the default decides, and a group cannot
remove a permission the defaults grant (`../tools/ground-truth.md`, Accounts and Access).

### 3.3 Which Knowledge Bases Appear in a Person's List

For a non-admin (and for an admin with the bypass off) the list and the chat pickers show a knowledge
base when any of these is true (`backend/open_webui/routers/knowledge.py:248-257`;
`backend/open_webui/models/access_grants.py:741-800`):

1. they own it;
2. it has a Public Read grant;
3. it has a Read grant naming them; or
4. it has a Read grant naming one of their groups.

Choosing **Write** in the share dialog stores both a Read and a Write grant, so Write holders also see
it (`users-groups-roles-and-permissions.md`, section 4, Read / Write). The **View** filter narrows the
list to **Created by you** (owner) or **Shared with you** (not owner), and the **All Sources** filter to
**Local** or **Connected** (`backend/open_webui/models/knowledge.py:288-303`;
`src/lib/components/workspace/Knowledge.svelte:355-377`). Both choices are remembered in the browser
(`src/lib/components/workspace/Knowledge.svelte:271-274`, `:358-376`).

A knowledge base whose owner account no longer exists still appears for anyone with access; its owner
column reads `Deleted User` (`src/lib/components/workspace/Knowledge.svelte:493-503`).

### 3.4 Admins and the Bypass Switch

`BYPASS_ADMIN_ACCESS_CONTROL` (environment only, default on; it falls back to
`ENABLE_ADMIN_WORKSPACE_CONTENT_ACCESS`) decides whether admins are treated as able to see and change
every knowledge base (`backend/open_webui/config.py:2086-2092`).

| | Bypass on (default) | Bypass off |
|---|---|---|
| Admin's list | Every knowledge base | Only those they own or that are shared with them (`backend/open_webui/routers/knowledge.py:186-192`) |
| `write_access` shown to the admin | Always true, so every control is shown | True only for their own or Write-shared knowledge bases; others open as `Read Only` (`:209-213`, `:1117-1127`) |
| Opening by address | Allowed | Allowed: the page check admits every admin (`:1104-1106`) |
| Row menu (**Delete**, **Export**) on the list | Shown | Still shown to every admin (`src/lib/components/workspace/Knowledge.svelte:506-520`) |
| Using any knowledge base in chat | Allowed | Allowed: retrieval and the knowledge tools admit every admin (`backend/open_webui/retrieval/utils.py:1566-1572`; `backend/open_webui/tools/knowledge_fs.py:319-330`) |

The live value of the switch is TO BE CONFIRMED.

### 3.5 Files Inside a Shared Knowledge Base

- **Reading.** Anyone who can read a knowledge base can read its files: open them in the drawer,
  download them through the file name link, and have models quote them
  (`backend/open_webui/utils/access_control/files.py:45-64`; `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:929-931`).
  The row menu with **Rename**, **Download** and **Delete** is shown only to people with write access
  to the knowledge base (`src/lib/components/workspace/Knowledge/KnowledgeBase/Files.svelte:198-245`).
- **Writing.** Write access to a knowledge base gives write access to a file inside it only when the
  knowledge base's owner also owns that file. A collaborator can therefore rename or edit files the
  owner uploaded, but not files another collaborator uploaded, and the owner cannot rename or edit files
  a collaborator uploaded; those attempts answer `We could not find what you're looking for :/`
  (`backend/open_webui/utils/access_control/files.py:45-64`; `backend/open_webui/routers/files.py:985-1005`,
  `:783-787`). The menu still offers **Rename** to everyone with write access to the knowledge base.
- **Adding someone else's file.** Adding an existing file requires read access to that file as well as
  write access to the knowledge base (`backend/open_webui/routers/knowledge.py:1472-1478`, `:2089-2096`).

### 3.6 Whose Access Counts When a Model Uses a Knowledge Base

The **person chatting** must be able to read the knowledge base. Sharing a custom model does not share
the knowledge bases attached to it; for people without read access those knowledge bases are skipped
with no message (`backend/open_webui/retrieval/utils.py:1566-1580`;
`backend/open_webui/tools/builtin.py:3221-3237`; `backend/open_webui/tools/knowledge_fs.py:334-346`).
Single files attached directly to a shared model are readable through the model share
(`backend/open_webui/utils/access_control/files.py:84-101`). `workspace-models-and-model-access.md`,
sections 3.6 and 11.7, covers the model side.

How each sharing restriction is enforced on the server beyond what is described here is
security-sensitive: refer to the platform maintainer and U of T Information Security
(security.utoronto.ca).

## 4. Key Concepts and Terminology

| Term | Meaning in this codebase | Source |
|---|---|---|
| Knowledge base / Knowledge / Collection | One row in the `knowledge` table: name, description, owner, `meta`, timestamps. The interface says "Knowledge" for the section, "knowledge base" in dialogs and "Collection" in chat pickers | `backend/open_webui/models/knowledge.py:48-60`; `src/lib/components/chat/MessageInput/Commands/Knowledge.svelte:148-152` |
| Knowledge file | A link (`knowledge_file` row) between a knowledge base and an uploaded file, recording who added it and which directory it sits in. The file itself is an ordinary `file` row that also appears in its owner's file list | `backend/open_webui/models/knowledge.py:99-115`; `backend/open_webui/routers/files.py:489-499` |
| Directory | A folder inside one knowledge base (`knowledge_directory` row) with an optional parent; purely organizational. Model tools see directories as paths such as `docs/api` | `backend/open_webui/models/knowledge.py:63-79`; `backend/open_webui/tools/knowledge_fs.py:211-269` |
| Local knowledge base | Content uploaded into MedIT GPT and indexed here; filter label **Local** | `src/lib/components/workspace/Knowledge.svelte:370`; `backend/open_webui/models/knowledge.py:297-303` |
| Connected knowledge base | A read-only knowledge base over an existing collection in an external vector database (`meta.source = 'external'`); label **Connected**, badge **Read Only**, auth mode "Admin-managed service account" | `backend/open_webui/routers/knowledge.py:143-151`, `:928-938`; `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1328-1399` |
| Read Only | Badge or label shown when the server reports no write access, and on every connected knowledge base | `src/lib/components/workspace/Knowledge.svelte:456-466`; `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1287-1291` |
| Processing / pending | A file uploaded from a knowledge base page whose `data.status` is still `pending` or `processing` and that is not yet linked; shown with a spinner and listed by `GET /{id}/files/pending` | `backend/open_webui/models/files.py:407-443`; `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:212-245` |
| Extracted content | The plain text pulled from a file, stored in `file.data.content`. Indexing, full-context mode, the drawer, the **File content** search, export and the model's grep and view tools all use this text, not the original file | `backend/open_webui/routers/retrieval.py:2064-2068`; `backend/open_webui/routers/knowledge.py:2183-2190` |
| Chunks and vector collection | The extracted text is split into chunks and embedded. A local knowledge base's chunks live in a vector collection named after its id; each file also keeps its own `file-{id}` collection | `backend/open_webui/routers/retrieval.py:1946-1951`, `:2101-2115` |
| Knowledge search index | A separate vector collection named `knowledge-bases` holding one embedding of each knowledge base's name and description, used by the model's `query_knowledge_bases` tool | `backend/open_webui/routers/knowledge.py:89-118`; `backend/open_webui/tools/builtin.py:3372-3469` |
| Content hash and duplicate content | Each file's extracted text has a SHA-256 hash; a knowledge base refuses a second file whose text hash matches a file already in it (`Duplicate content detected. Please provide unique content to proceed.`) | `backend/open_webui/routers/retrieval.py:2069`, `:1734-1753`; `backend/open_webui/constants.py:109` |
| File checksum | A SHA-256 of a file's raw bytes (`meta.file_hash`), computed in the browser for directory uploads and on the server otherwise; **Sync directory** compares it to spot changed files | `backend/open_webui/routers/files.py:402-406`; `src/lib/utils/hash.ts:1-19`; `backend/open_webui/routers/knowledge.py:1908-1916` |
| Attached knowledge | Knowledge items a model is told about for this chat: those on the custom model, those on the chat's folder, and those mentioned in the chat when the model's **File Context** capability is off | `backend/open_webui/utils/tools.py:480-516` |
| Model knowledge | The model editor's **Knowledge** list, stored as `meta.knowledge` on the model: references to knowledge bases (`collection`), single files (`file`) and notes (`note`) | `src/lib/components/workspace/Models/Knowledge.svelte:186-196`; `backend/open_webui/models/models.py:73-102` |
| Folder (project) knowledge | Knowledge bases, files and notes attached to a chat folder; chats in the folder use them | `backend/open_webui/utils/middleware.py:2585-2602`; `backend/open_webui/utils/access_control/files.py:16` |
| Using Entire Document / Using Focused Retrieval | The switch in an attached item's dialog. Entire Document (`context: 'full'`) sends every file's full text; Focused Retrieval (the default) sends only the best-matching chunks | `src/lib/components/common/FileItemModal.svelte:346-371`; `backend/open_webui/retrieval/utils.py:1592-1621` |
| Full Context Mode | Admin setting (`rag.full_context`) that makes every retrieval return whole documents | `src/lib/components/admin/Settings/Documents.svelte:1215-1224`; `backend/open_webui/utils/middleware.py:2108-2133` |
| Native and legacy function calling | Native (default): the model calls tools itself, including knowledge tools. Legacy: the pipeline retrieves from the model's knowledge before the reply | `src/lib/i18n/locales/en-US/translation.json:2825-2826`; `backend/open_webui/utils/middleware.py:2604-2643` |
| Knowledge tools | Built-in tools that let a model list, search, grep and read knowledge bases (section 5.22) | `backend/open_webui/utils/tools.py:603-642` |
| `kb_exec` | An optional built-in tool that answers shell-style commands (`ls`, `tree`, `cat`, `grep`, `find` and others) over knowledge bases; offered only when `ENABLE_KB_EXEC` is on (off in code) | `backend/open_webui/tools/knowledge_fs.py:1140-1203`; `backend/open_webui/env.py:968` |
| File retention | `ENABLE_KNOWLEDGE_FILE_RETENTION` (off in code). Off: removing a file from a knowledge base, resetting it, deleting a directory with its contents or a sync cleanup deletes the file itself where the person is allowed to. On: those actions only unlink | `backend/open_webui/config.py:985`; `backend/open_webui/routers/knowledge.py:1618`, `:1825`, `:2013-2018`, `:2359-2364` |
| Reset | Empties a knowledge base: every file link, by default every directory, and its vector collection | `backend/open_webui/routers/knowledge.py:1792-1846` |
| Reindex | Admin action that rebuilds every knowledge base's vectors from stored text, plus the knowledge search index and memory vectors | `src/lib/components/admin/Settings/Documents.svelte:382-417`; `backend/open_webui/routers/knowledge.py:374-494` |
| Sync directory | Mirrors a local folder into the knowledge base: uploads new and changed files, removes files and directories not in the folder | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:708-778` |
| Legacy document | A record migrated from the old single-document feature (`meta.document` true); clicking it shows `Only collections can be edited, create a new knowledge base to edit/add documents.` | `backend/open_webui/migrations/versions/6a39f3d8e55c_add_knowledge_table.py:65-80`; `src/lib/components/workspace/Knowledge.svelte:218-226` |

## 5. Workflows (Step by Step)

Workflows 5.1 to 5.17 happen in Workspace › Knowledge; 5.18 to 5.23 are about using knowledge bases in
models and chats; 5.24 to 5.26 are admin tasks. Every success and error text is listed in section 10.

### 5.1 Find and Browse Knowledge Bases

1. Open **Workspace** › **Knowledge** (`/workspace/knowledge`). The list loads 30 knowledge bases at a
   time and loads more as you scroll (`Loading...`) (`src/lib/components/workspace/Knowledge.svelte:139-176`,
   `:526-539`; `backend/open_webui/routers/knowledge.py:61`).
2. **Search Knowledge** filters as you type (after 300 ms). It matches the name, the description and the
   owner's name, email or username (`src/lib/components/workspace/Knowledge.svelte:88-93`, `:319-325`;
   `backend/open_webui/models/knowledge.py:276-286`).
3. The view filter offers **All**, **Created by you** and **Shared with you**; the source filter offers
   **All Sources**, **Local** and **Connected** (`src/lib/components/workspace/Knowledge.svelte:355-377`;
   `src/lib/components/workspace/common/ViewSelector.svelte:16-18`).
4. Click the **Title** or **Updated at** column heading to sort; clicking again reverses the order
   (`src/lib/components/workspace/Knowledge.svelte:109-116`, `:388-418`).
5. Each row shows the name (hover for the description), badges, how long ago it was updated (hover for
   the full date), a second line with the file count (`1 file` or `{count} files`) and description, and
   on wide screens the owner (hover for the email) (`src/lib/components/workspace/Knowledge.svelte:235-269`,
   `:422-504`).
6. Click a row to open it. People with write access, and every admin, also get a **…** menu with
   **Delete**; admins also get **Export** (`src/lib/components/workspace/Knowledge.svelte:506-520`;
   `src/lib/components/workspace/Knowledge/ItemMenu.svelte:51-77`).

What the list does not show: **Updated at** changes when the name, description or connected settings
change and when the knowledge base is reset, not when files are added or removed
(`backend/open_webui/models/knowledge.py:676-707`, `:731-777`). An empty result shows `No knowledge
found` and `Try adjusting your search or filter to find what you are looking for.`, even when no filter
is set (`src/lib/components/workspace/Knowledge.svelte:540-549`).

### 5.2 Create a Knowledge Base

Who: admins, and people with Knowledge Access.

1. On Workspace › Knowledge press **Create** (or open `/workspace/knowledge/create`). The **Create a
   knowledge base** dialog opens (`src/lib/components/workspace/Knowledge.svelte:76-86`, `:304-311`;
   `src/lib/components/workspace/Knowledge/CreateKnowledgeBase.svelte:54-68`).
2. Under **What are you working on?** type a name (placeholder `Name your knowledge base`).
3. Under **What are you trying to achieve?** type a description (placeholder `Describe your knowledge
   base and objectives`). The description is required here and is also what the model's knowledge
   search sees, so a clear purpose helps models pick the right knowledge base (section 5.22)
   (`src/lib/components/workspace/Knowledge/CreateKnowledgeBase.svelte:107-143`;
   `backend/open_webui/routers/knowledge.py:92-118`).
4. Optionally set access in the panel below (shown with Knowledge Sharing, or to admins) (section 5.4).
5. Press **Create Knowledge**. On success `Knowledge created successfully.` appears and the new
   knowledge base opens (`src/lib/components/workspace/Knowledge/CreateKnowledgeBase.svelte:39-48`).

Checks and side effects:

- A name or description that is blank, or only spaces, shows `Please fill in all fields.` and **clears
  both boxes** (`src/lib/components/workspace/Knowledge/CreateKnowledgeBase.svelte:31-37`).
- Names need not be unique; nothing in the table or the code prevents two knowledge bases with the same
  name (`backend/open_webui/models/knowledge.py:48-60`, `:203-229`).
- The server removes any share entry the creator is not allowed to make, without saying so
  (`backend/open_webui/routers/knowledge.py:336-342`).
- The name and description are embedded into the knowledge search index; if that fails the knowledge
  base is still created and the failure is only logged (`backend/open_webui/routers/knowledge.py:116-118`, `:346-353`).
- If the database insert fails the creator sees `Uh-oh! This file is already registered. Please choose
  another file.`, a misleading text reused from files (`backend/open_webui/routers/knowledge.py:362-366`;
  `backend/open_webui/models/knowledge.py:218-229`).

### 5.3 Rename It or Change Its Description

1. Open the knowledge base. People with write access can type in the name and description fields at the
   top; for others they are disabled and the page shows `Read Only`
   (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1255-1305`).
2. Changes save automatically one second after typing stops, with `Knowledge updated successfully`
   (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:969-994`).
3. Clearing either field shows `Please fill in all fields.` and nothing is saved.

The save also re-sends the current access list and re-embeds the name and description
(`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:981-986`;
`backend/open_webui/routers/knowledge.py:1179-1195`). A database failure shows `Uh-oh! This id is
already registered. Please choose another id string.`, which is also misleading
(`backend/open_webui/routers/knowledge.py:1208-1212`). On wide screens the id is shown beside the
description; clicking it copies it (`ID copied to clipboard`), which is the identifier to send with an
escalation (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1307-1319`).

### 5.4 Share a Knowledge Base

1. Open the knowledge base and press **Access** (shown only with write access)
   (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1279-1286`;
   `src/lib/components/common/AccessButton.svelte:22`).
2. The **Access Control** dialog offers Private or Public visibility (Public needs Knowledge Public
   Sharing) and an Access List of people and groups with **Read** or **Write**
   (`src/lib/components/workspace/common/AccessControlModal.svelte:34`;
   `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1220-1238`).
3. Each change is saved at once and shows `Saved`; a refusal shows the server's text
   (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1229-1236`).

The server keeps only the entries the sharer may make (section 3.2), and the open dialog keeps showing
what was chosen until it is reopened (`users-groups-roles-and-permissions.md`, section 5.17). Sharing
the knowledge base does not share any custom model that uses it, and sharing a model does not share its
knowledge bases (section 3.6).

### 5.5 Upload Files

Who: people with write access.

1. Open the knowledge base and, if needed, open the directory the files should go into.
2. Press **+** (Add Content) › **Upload files** and choose one or more files, or drag files from the
   computer onto the page (an **Add Files** overlay appears)
   (`src/lib/components/workspace/Knowledge/KnowledgeBase/AddContentMenu.svelte:74-82`;
   `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1048-1111`, `:1194-1216`;
   `src/lib/components/AddFilesPlaceholder.svelte:14`).
3. Files are sent one after another. Each appears at the top of the list with a spinner while it uploads
   and processes (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:400-478`,
   `:1199-1205`; `src/lib/components/workspace/Knowledge/KnowledgeBase/Files.svelte:111-125`).
4. When processing succeeds `File added successfully.` appears and the list refreshes. When it fails a
   warning shows the reason and the row disappears (section 5.6).

Checks, in the order they happen:

| Check | Where | Result |
|---|---|---|
| The person lacks write access (drag and drop) | Browser | `You do not have permission to upload files to this knowledge base.` (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1067-1070`) |
| The file is empty (0 bytes) | Browser | `You cannot upload an empty file.` (`:415-418`) |
| Larger than **Max Upload Size** | Browser, then server | `File size should not exceed {maxSize} MB.`; if it reaches the server, `Oops! The file you're trying to upload is too large. Please upload a file that is less than {size}.` (`:420-434`; `backend/open_webui/routers/files.py:394-400`; `backend/open_webui/constants.py:105-107`) |
| Extension not in **Allowed File Extensions** (when that list is set) | Server | `[ERROR: File type {file_extension} is not allowed]` (`backend/open_webui/routers/files.py:353-362`) |
| Image, or video, while the extraction engine is not set up for media | Server, background | Images: `File type {content_type} is not supported for processing`. Videos are stored without text, so the knowledge-base step then fails with `The content provided is empty. Please ensure that there is text or data present before proceeding.` (`backend/open_webui/routers/files.py:167-188`; `backend/open_webui/routers/retrieval.py:2014-2015`) |
| Extracted text duplicates a file already in this knowledge base | Server, background | `Duplicate content detected. Please provide unique content to proceed.` (`backend/open_webui/routers/retrieval.py:1734-1753`) |

Audio files are transcribed with speech-to-text (using the person's speech-to-text language when set)
and the transcript is indexed (`backend/open_webui/routers/files.py:152-166`;
`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:438-448`). Extraction engines, chunking
and embedding are described in `rag-retrieval-embeddings-and-vector-stores.md`; upload limits and
storage in `files-uploads-and-storage.md`.

### 5.6 Processing Status: What "Processing" Means

A file uploaded from a knowledge base page goes through these steps on the server, in a background
task that continues even if the page is closed (`backend/open_webui/routers/files.py:128-277`,
`:435-446`):

| Step | What happens | `file.data.status` | Visible on the page |
|---|---|---|---|
| 1. Stored | The file is saved to storage and a `file` row is created with the knowledge base and directory in its metadata | `pending` | Spinner row |
| 2. Extracted and indexed for the file | Text is extracted (or audio transcribed), saved as the file's extracted content, chunked and embedded into the file's own `file-{id}` collection | `completed` (briefly) | Spinner row |
| 3. Indexed into the knowledge base | The status returns to `processing`; the file's chunks are copied into the knowledge base's collection; the duplicate check runs here | `processing` | Spinner row |
| 4. Linked | A `knowledge_file` row is created; the file now belongs to the knowledge base | `completed` | Normal row |
| Failure at any step | The error is recorded and the file is not linked | `failed`, with `error` | Row removed; the uploader sees a warning with the error |

Details:

- **After a reload** the page asks the server for files still pending or processing for this knowledge
  base, shows them with a spinner, and checks again every 5 seconds until none remain
  (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:212-245`;
  `backend/open_webui/routers/knowledge.py:1284-1328`; `backend/open_webui/models/files.py:407-443`).
- **A failed file is not shown in the knowledge base.** It stays in the uploader's own file list with a
  failed status (`files-uploads-and-storage.md`). The warning reaches only the uploader, and only while
  the page is open; there is no in-app message later, apart from an optional personal notification
  webhook (section 9).
- **"File added successfully." is not proof of step 4.** The upload waits on the file's status stream,
  which ends at the first `completed` or `failed` it sees, polled once a second
  (`backend/open_webui/routers/files.py:644-668`; `src/lib/apis/files/index.ts:46-89`). Read from code,
  the stream can catch the brief `completed` of step 2, so a later failure in step 3 (for example a
  duplicate) would leave a success message and a file that does not appear. Confirm in a test environment
  (section 14.4).
- **Files already in a knowledge base have no visible status.** Re-indexing after a text edit, a
  reindex by an admin, or a failed reindex are not shown on the page (sections 5.12 and 5.24).

### 5.7 Add a Webpage

1. Press **+** › **Add webpage**. The **Attach Webpage** dialog asks for **Webpage URLs**; press **Add**.
   An invalid address shows `Please enter a valid URL.`
   (`src/lib/components/workspace/Knowledge/KnowledgeBase/AddContentMenu.svelte:111-119`;
   `src/lib/components/chat/MessageInput/AttachWebpageModal.svelte:28-34`, `:44`, `:68`, `:88`).
2. Each address appears with a spinner while the server fetches it
   (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:303-326`).
3. A web page or YouTube video becomes a text file named after the address (letters and digits kept,
   everything else turned into `_`, lower case, first 50 characters, `.txt` added) and is uploaded into
   the current directory like any file. An address that points to a downloadable file (for example a
   PDF) is downloaded, processed, and then added to the knowledge base
   (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:328-365`;
   `backend/open_webui/routers/retrieval.py:2356-2420`).
4. Success shows `File added successfully.`; failures show `Failed to process URL: {url}`, `Failed to
   upload file.` or the server's text, such as `[ERROR: Error processing URL]`
   (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:367-396`;
   `backend/open_webui/routers/retrieval.py:2421-2427`).

How pages are fetched (engine, YouTube language, proxies) is in `web-search-and-web-loading.md`.

### 5.8 Add Text Content

1. Press **+** › **Add text content**. A full-screen editor opens with a title (default `Untitled`) and a
   text area (`Write something...`); the microphone button dictates text
   (`src/lib/components/workspace/Knowledge/KnowledgeBase/AddTextContentModal.svelte:16-17`, `:54-128`).
2. Press **Save**. A blank title or text shows `Please fill in all fields.`
   (`src/lib/components/workspace/Knowledge/KnowledgeBase/AddTextContentModal.svelte:35-52`).
3. The text is saved as a file named `{title}.txt` and uploaded like any file (section 5.5)
   (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:295-301`, `:1179-1185`).

Microphone refusals show `Permission denied when accessing microphone: {error}` or `Permission denied
when accessing microphone` (`src/lib/components/workspace/Knowledge/KnowledgeBase/AddTextContentModal.svelte:101-122`).

### 5.9 Directories

Directories organize files inside one knowledge base. They are stored in `knowledge_directory`
(section 6.4) and affect only how files are listed and how the model's tools see paths; retrieval
searches the whole knowledge base regardless of directory (`backend/open_webui/retrieval/utils.py:1622-1636`).

| Task | Steps | Result and messages | Source |
|---|---|---|---|
| Create | **+** › **New directory**; type a name in **New Directory** (`Directory name`); **Create** or Enter | Created inside the directory you are in: `Directory created.` A blank name shows `Name is required`; a clash shows `Failed to create directory. A directory with this name may already exist at this level.` | `src/lib/components/workspace/Knowledge/KnowledgeBase/NewDirectoryModal.svelte:19-79`; `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:811-826`; `backend/open_webui/routers/knowledge.py:2253-2284` |
| Open | Click the directory | The list shows that level; breadcrumbs appear, starting with the knowledge base's name; click a crumb to go back up | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:801-809`, `:1533-1543`; `src/lib/components/workspace/Knowledge/KnowledgeBase/KnowledgeBreadcrumbs.svelte:55-89` |
| Rename | Double-click it, or **…** › **Rename**; Enter saves, Escape cancels | `Directory renamed.`; a clash shows `Failed to update directory. This may be caused by a naming conflict or circular move.` | `src/lib/components/workspace/Knowledge/KnowledgeBase/DirectoryRow.svelte:39-57`, `:164-195`; `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:828-840`; `backend/open_webui/routers/knowledge.py:2287-2321` |
| Move a file | Drag the file onto a directory row or a breadcrumb | `File moved.`; failure `Failed to move file.` | `src/lib/components/workspace/Knowledge/KnowledgeBase/Files.svelte:103-109`; `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:867-882`; `backend/open_webui/routers/knowledge.py:2376-2413` |
| Move a directory | Drag it onto another directory row or a breadcrumb | `Directory moved.`; moving a directory into itself or one of its own sub-directories is refused with the rename failure text | `src/lib/components/workspace/Knowledge/KnowledgeBase/DirectoryRow.svelte:66-105`; `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:884-897`; `backend/open_webui/models/knowledge.py:957-988` |
| Delete | **…** › **Delete**; the **Delete directory?** dialog asks `Are you sure you want to delete this directory?` with the box **Delete all contents inside this directory**, ticked by default | Ticked: the files in it and in all its sub-directories are removed from the knowledge base, their chunks deleted, and each file is deleted outright if retention is off, no other knowledge base uses it, and the person owns it (or is an admin). Unticked: its files, and those of its sub-directories, move up to the parent (or the root). Either way `Directory deleted.`; failure `Failed to delete directory.` | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:135-137`, `:842-865`, `:1708-1729`; `backend/open_webui/routers/knowledge.py:2324-2373`; `backend/open_webui/models/knowledge.py:1009-1075` |

The directory menu and drag targets are offered only with write access
(`src/lib/components/workspace/Knowledge/KnowledgeBase/DirectoryRow.svelte:70-72`, `:164`). Because the
**Delete all contents** box starts ticked, pressing **Confirm** without reading the dialog deletes the
files (section 11.12).

Directory names must be unique among siblings; the database enforces this with a unique key on
knowledge base, parent and name (`backend/open_webui/models/knowledge.py:75-79`). Read from code, two
directories with the same name directly at the root may still be accepted, because the root's empty
parent value does not count as equal in that key; confirm in a test environment (section 14.4).

### 5.10 Upload a Directory

1. Press **+** › **Upload directory** and choose a folder on the computer, or drag a folder onto the
   page (`src/lib/components/workspace/Knowledge/KnowledgeBase/AddContentMenu.svelte:84-92`;
   `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:480-485`, `:1080-1105`).
2. Hidden files and anything inside hidden folders (names starting with `.`) are skipped
   (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:487-490`, `:511-530`, `:544-548`).
   Browsers with the File System Access feature use a folder picker; others (for example Firefox) use a
   folder upload field (`:503-577`).
3. A progress line shows `Computing checksums ({count} files)`, then `Comparing with knowledge base...`
   (`:666-683`).
4. Directories that do not exist yet are created, mirroring the folder. The folder's own name becomes
   the top directory, placed inside the directory you are in (`:591-619`, `:690`).
5. Every file is uploaded in turn (`Uploading {current}/{total}: {file}`), each going through the
   processing steps of section 5.6 (`:621-664`, `:692-694`).
6. The result is `File uploaded successfully` when all succeed, otherwise `Upload failed for {failed}
   of {total} files.` (`:654-660`, `:696-698`). The reasons for individual failures are written only to
   the browser console (`:642-651`).

Upload directory does not skip files that are already in the knowledge base. Uploading the same folder
again therefore fails for every unchanged file as duplicate content, and those failures are counted in
the summary when the upload sees them (section 5.6 explains when it may not; section 11.9). To bring a
knowledge base up to date with a folder, use **Sync directory**.

### 5.11 Sync a Directory

**Sync directory** makes the knowledge base an exact copy of one local folder. The tooltip says `Sync a
local directory with this knowledge base. Only new and modified files will be uploaded. The directory
structure will be mirrored.` (`src/lib/components/workspace/Knowledge/KnowledgeBase/AddContentMenu.svelte:94-109`).

1. Press **+** › **Sync directory** and choose the folder (hidden files are skipped, as in 5.10).
2. Confirm the dialog: `{count} files selected. Only new and modified files will be uploaded. Deleted
   files will be removed. The folder structure will be mirrored. Continue?`
   (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1158-1170`, `:1461-1466`).
3. The browser computes a SHA-256 checksum of each file and sends the list of paths, names, checksums
   and sizes to the server (`:709-726`; `src/lib/utils/hash.ts:1-19`).
4. The server compares each entry with the knowledge base by directory path and file name
   (`backend/open_webui/routers/knowledge.py:1875-1967`):
   - not in the knowledge base: **added**;
   - in it with a different checksum, or with no stored checksum: **modified**;
   - in it with the same checksum: unmodified;
   - in the knowledge base but not in the folder: **deleted**;
   - directories that no file in the folder needs: removed.
5. Deleted files and the old versions of modified files are removed first (`Removing {count} stale
   files...`), missing directories are created, then added and modified files are uploaded
   (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:733-756`).
6. The result is `Sync complete: {added} added, {modified} modified, {deleted} deleted, {unmodified}
   unmodified`, or the failure count as in 5.10 (`:758-771`).

What support should know:

- **Everything else is removed.** Paths are compared from the knowledge base's root and include the
  chosen folder's own name, whichever directory is open. Files uploaded at the root, web pages, text
  content, and files in other directories are all "not in the folder", so the sync removes them
  (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:511-531`, `:722-726`;
  `backend/open_webui/routers/knowledge.py:1942-1957`).
- **Removed means deleted** for files the person owns (or any file, for an admin) when retention is off
  and no other knowledge base uses the file; other files are only unlinked
  (`backend/open_webui/routers/knowledge.py:1993-2018`).
- **Old versions go first.** A modified file's old version is removed before the new one uploads; if the
  upload fails, the file is missing until the next successful sync
  (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:733-756`).
- **Unchanged-looking files may re-upload.** Files uploaded before this version recorded checksums have
  no stored checksum and count as modified; every upload through this version records one
  (`backend/open_webui/routers/knowledge.py:1912`, `:1931`; `backend/open_webui/routers/files.py:402-406`).
- **Renaming is a delete plus an add.** A file renamed in MedIT GPT no longer matches the folder by name.
- **Sync is manual.** There is no scheduled or automatic sync; the person repeats the steps each time
  (section 8).

### 5.12 Browse, Search and Read Files Inside a Knowledge Base

| Task | How | Notes | Source |
|---|---|---|---|
| Browse | Directories are listed first, then files, 30 per page with page buttons beyond 30 | Each file shows its name, size, how long ago it changed and `By {name}`, the person who added it (`Deleted User` if that account is gone) | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1558-1615`; `src/lib/components/workspace/Knowledge/KnowledgeBase/Files.svelte:82-196`; `backend/open_webui/models/knowledge.py:537-541` |
| Count | The number beside the name | `{COUNT} files` counts the files at the level you are viewing that match the search, not the whole knowledge base; the list page's count covers the whole knowledge base | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1267-1276`; `backend/open_webui/models/knowledge.py:544-595`, `:338-345` |
| Search | **Search Collection** | Matches file names in the directory you are viewing only, not in its sub-directories | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:158-168`, `:192-202`, `:1406-1418`; `backend/open_webui/models/knowledge.py:544-571` |
| Search the text | Filter menu › **File content** | Also matches the extracted text, up to the first 64 Mi characters of each file (`RAG_FILE_CONTENT_SEARCH_MAX_CHARS`) | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1420-1443`; `backend/open_webui/models/knowledge.py:558-569`; `backend/open_webui/config.py:987` |
| Filter | **All**, **Created by you**, **Shared with you** | Here "Created by you" means files you added, whoever owns the knowledge base | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1489-1506`; `backend/open_webui/models/knowledge.py:573-577` |
| Sort | **Sort**: **Name**, **Created**, **Updated**, then **Asc** or **Desc** | Default is most recently changed first | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1508-1528`; `backend/open_webui/models/knowledge.py:552-591` |
| Read | Click a file | A side drawer shows its extracted text (`Failed to load file content.` if it cannot load); the name at the top opens the original file in a new tab | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:250-275`, `:929-931`, `:1620-1694` |
| Edit the text | Change the text in the drawer, press **Save** (write access) | `File content updated successfully.` The file's own index and every knowledge base containing it are re-indexed. Only the extracted text changes; the original file and its download stay as uploaded | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:938-967`, `:1662-1690`; `backend/open_webui/routers/files.py:718-786` |
| Rename | Double-click the name, or **…** › **Rename** | `File renamed.` Renames the file everywhere it is used. Chunks indexed earlier keep the old name, so citations may show it until the file is re-indexed (read from code) | `src/lib/components/workspace/Knowledge/KnowledgeBase/Files.svelte:64-80`, `:127-167`, `:210-219`; `backend/open_webui/models/files.py:394-405`; `backend/open_webui/routers/retrieval.py:2023-2050` |
| Download | **…** › **Download** | Opens the original file | `src/lib/components/workspace/Knowledge/KnowledgeBase/Files.svelte:220-230` |

An empty level shows `No content found` (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1607-1615`).

### 5.13 Remove a File

1. On the file's row press **…** › **Delete**. There is no confirmation
   (`src/lib/components/workspace/Knowledge/KnowledgeBase/Files.svelte:231-240`).
2. `File removed successfully.` appears and the list refreshes
   (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:899-915`).

What the server does (`backend/open_webui/routers/knowledge.py:1613-1694`):

1. Unlinks the file from this knowledge base and deletes its chunks from this knowledge base's
   collection.
2. Deletes the file itself (its row, its stored copy and its `file-{id}` collection) when retention is
   off (the default) and the person owns the file or is an admin
   (`backend/open_webui/routers/knowledge.py:64-80`, `:1673-1675`).

Read from code, step 2 does not check whether the file is also used elsewhere. A file that a model
attaches directly, or that was attached to a chat by picking it in the `#` list, stops being available
there too (section 11.10). When a collaborator removes a file they do not own, it is only unlinked and
stays in its owner's file list.

### 5.14 Reset a Knowledge Base

1. Press **+** › **Reset** (`src/lib/components/workspace/Knowledge/KnowledgeBase/AddContentMenu.svelte:133-142`).
2. The **Reset knowledge base?** dialog says `This will remove all files and directories from this
   knowledge base. This action cannot be undone.`; press **Confirm**
   (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1731-1745`).
3. `Knowledge base has been reset` appears. If the server refuses, no message appears at all, because
   the dialog does not catch the error (read from code, `:1734-1738`).

The server removes every file link and every directory, and deletes the knowledge base's vector
collection. With retention off, it deletes files the person owns (every file, for an admin); other
people's files are only unlinked. The knowledge base itself, its name, description, sharing and model
attachments remain (`backend/open_webui/routers/knowledge.py:1792-1846`;
`backend/open_webui/models/knowledge.py:731-752`).

### 5.15 Delete a Knowledge Base

1. On Workspace › Knowledge, open the row's **…** menu and press **Delete**.
2. The dialog shows the default `Confirm your action` and `This action cannot be undone. Do you wish to
   continue?`; press **Confirm** (`src/lib/components/workspace/Knowledge.svelte:297-302`;
   `src/lib/components/common/ConfirmDialog.svelte:140-153`).
3. `Knowledge deleted successfully.` appears and the list reloads (`src/lib/components/workspace/Knowledge.svelte:178-189`).

| Removed | Kept |
|---|---|
| The knowledge base from every custom model's **Knowledge** list (`backend/open_webui/routers/knowledge.py:1734-1750`) | The files: they stay in their owners' file lists, with their own `file-{id}` indexes |
| Its vector collection, for a local knowledge base (`:1752-1770`) | Files a model or chat attached directly by picking them from this knowledge base |
| Its entry in the knowledge search index (`:1772-1773`) | References in chats (the `Collection` chip) and in folders; they now find nothing and raise no error (`backend/open_webui/retrieval/utils.py:1566-1580`) |
| All its access grants and the `knowledge` row (`backend/open_webui/models/knowledge.py:798-806`) | For a connected knowledge base, the external data, which this code does not write to; an admin deleting the last knowledge base on a connection also removes the saved connection (`backend/open_webui/routers/knowledge.py:1753-1764`) |

The `knowledge_file` and `knowledge_directory` rows are removed by the database's cascade rules on
PostgreSQL. On SQLite those rules are not switched on (the app sets no `foreign_keys` pragma), so read
from code the rows remain, unseen, after the knowledge base is gone
(`backend/open_webui/models/knowledge.py:67`, `:104`; `backend/open_webui/internal/db.py:335-400`;
section 14.4). There is no trash and no undo; recovery would need a database and vector-store backup
(TO BE CONFIRMED, section 14.2).

### 5.16 Export a Knowledge Base (Admins)

1. On Workspace › Knowledge, open the row's **…** menu and press **Export**
   (`src/lib/components/workspace/Knowledge.svelte:506-513`).
2. The browser downloads `{name}.zip` and shows `Knowledge exported successfully`
   (`src/lib/components/workspace/Knowledge.svelte:199-216`).

The ZIP holds one `.txt` file per file, containing its **extracted text**, not the original document;
`.txt` is added to names that lack it, files with no text are left out, and directories are not
reproduced (all entries sit at the top level) (`backend/open_webui/routers/knowledge.py:2178-2202`).
Connected knowledge bases cannot be exported (`External knowledge bases are read-only.`). The export
contains the full text of every document and must be handled as personal data.

### 5.17 Import

None found in code. The knowledge router has no import endpoint and no knowledge screen offers import
(searched `backend/open_webui/routers/knowledge.py` and `src/lib/components/workspace/Knowledge/` for
import handlers). The only bulk route in is **Upload directory** or **Sync directory**.

### 5.18 Attach a Knowledge Base to a Custom Model

1. Open the model in Workspace › Models (or Admin › Settings › Models) and find **Knowledge**
   (`src/lib/components/workspace/Models/Knowledge.svelte:172-182`).
2. Press **Select Knowledge**. The picker lists **Notes**, **Collections** (knowledge bases) and
   **Files** (files inside knowledge bases) that the editor can read; pick one or more
   (`src/lib/components/workspace/Models/Knowledge/KnowledgeSelector.svelte:72-100`, `:141-190`).
   **Upload** (shown with Allow File Upload, or to admins) attaches a file straight to the model without
   putting it in any knowledge base (`src/lib/components/workspace/Models/Knowledge.svelte:37-110`,
   `:207-219`).
3. Each attached item appears as a chip. Clicking a chip opens its dialog with the **Using Entire
   Document** / **Using Focused Retrieval** switch; the **x** removes it; **Disable all** removes every item
   (`src/lib/components/workspace/Models/Knowledge.svelte:224-292`;
   `src/lib/components/common/FileItemModal.svelte:346-371`).
4. Save the model. The list is stored as `meta.knowledge` on the model record; only references are
   stored, not the documents' text (`backend/open_webui/models/models.py:73-102`).

The hint under the section reads `To attach knowledge base here, add them to the "Knowledge" workspace
first.` (`src/lib/components/workspace/Models/Knowledge.svelte:298-300`). People who use the model need
their own read access to each knowledge base (section 3.6). How a model uses its knowledge is in 5.21;
the model record and its sharing are in `workspace-models-and-model-access.md`, section 5.5.

### 5.19 Use a Knowledge Base in a Chat

Three entry points put a knowledge base (or one of its files) on the message being written:

| Entry point | What appears | Source |
|---|---|---|
| Type `#` | Sections `Folders`, `Collections` and `Files`, filtered by what follows `#`; a typed address starting with `http` also offers a web page or YouTube item | `src/lib/components/chat/MessageInput/Commands/Knowledge.svelte:30-131`, `:142-262` |
| Type `@` | The same knowledge items above the list of models | `src/lib/components/chat/MessageInput/Commands/AtCommands.svelte:64-78`, `:172-213` |
| **+** › **Attach Knowledge** | A searchable list of knowledge bases (`Search Knowledge`); the arrow (**Show Files**) lists files to attach one at a time | `src/lib/components/chat/MessageInput/InputMenu.svelte:333-361`, `:594-611`; `src/lib/components/chat/MessageInput/InputMenu/Knowledge.svelte:187-300` |

After picking:

1. A chip labelled `Collection` (or `File`) appears above the message box
   (`src/lib/components/common/FileItem.svelte:111-160`; `src/lib/components/chat/MessageInput.svelte:2001-2022`).
2. Clicking the chip opens a dialog with the **Using Entire Document** / **Using Focused Retrieval**
   switch (tooltips `Inject the entire content as context for comprehensive processing, this is
   recommended for complex queries.` and `Default to segmented retrieval for focused and relevant
   content extraction, this is recommended for most cases.`) (`src/lib/components/common/FileItemModal.svelte:346-371`).
   Read from code, the dialog tries to list the knowledge base's files but the server's reply to that
   request carries no file list, so the list stays empty (`src/lib/components/common/FileItemModal.svelte:204-214`,
   `:380-391`; `backend/open_webui/routers/knowledge.py:1094-1128`).
3. Send the message. The knowledge base stays attached to later messages in the same chat, as long as
   the message that carried it remains in the conversation (`src/lib/components/chat/Chat.svelte:2908-2920`,
   `:3449-3468`).

Conditions:

- **File upload must be allowed.** **Attach Knowledge** is greyed out when the person lacks Allow File
  Upload or any selected model has its **File Upload** capability off. Read from code, in that state the
  composer also clears every attachment, so a knowledge base picked with `#` or `@` disappears as soon as
  it is added (`src/lib/components/chat/MessageInput/InputMenu.svelte:67-78`, `:333-345`;
  `src/lib/components/chat/MessageInput.svelte:759-773`, `:2225-2234`; section 11.11).
- **Read access is checked when the message is sent.** A knowledge base the person cannot read (for
  example one deleted or unshared since it was attached) is skipped without a message
  (`backend/open_webui/retrieval/utils.py:1566-1580`).
- **A web address after `#`** attaches a web page, which needs the `chat.web_upload` permission
  (`You do not have permission to upload web content.`, `src/lib/components/chat/Chat.svelte:1790-1794`).
  An invalid address shows `Oops! Looks like the URL is invalid. Please double-check and try again.`
  (`src/lib/components/chat/MessageInput/Commands/Knowledge.svelte:210-219`, `:238-247`).

The composer and its pickers are described in `chat-composer-and-message-display.md`, sections 5.6 and
5.8.

### 5.20 Folder (Project) Knowledge

A chat folder can carry its own **Knowledge** list, edited with the same picker as the model editor;
every chat in the folder then uses it (`src/lib/components/layout/Sidebar/Folders/FolderModal.svelte:232-242`).
With native function calling the folder's knowledge is offered to the model's knowledge tools; with
legacy function calling it is retrieved before the reply (`backend/open_webui/utils/middleware.py:2585-2602`;
`backend/open_webui/retrieval/utils.py:1390-1405`). Folder limits and the dropping of unreadable items
are in `chat-conversations-history-and-organisation.md`.

### 5.21 How the Model Uses a Knowledge Base

What reaches the model depends on where the knowledge base is attached, on the model's **Function
Calling** parameter (native by default), and on three model settings: **File Context** capability
(`file_context`, default on), **Builtin Tools** capability (`builtin_tools`, default on) and the **Knowledge
Base** built-in tool group (`builtinTools.knowledge`, default on, `Browse and query knowledge bases`)
(`src/lib/i18n/locales/en-US/translation.json:2554-2555`, `:2573-2582`).

| Situation | What happens before or during the reply | Source |
|---|---|---|
| Attached to the custom model, native function calling, Builtin Tools and Knowledge Base on | The model is told which knowledge is attached (a list added to its system prompt) and is given knowledge tools limited to those items (5.22). Nothing is retrieved unless the model calls a tool; tool calls appear in the reply as expandable entries | `backend/open_webui/utils/middleware.py:3099-3123`; `backend/open_webui/utils/tools.py:480-516`, `:603-642` |
| Attached to the custom model, legacy function calling | The status `Searching Knowledge for "{searchQuery}"` appears and the items are searched like chat attachments (next row) before the reply | `backend/open_webui/utils/middleware.py:2604-2643`; `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:40-50` |
| Mentioned in the chat with `#`, File Context on | Retrieved before the reply in either mode: search phrases are generated (`Querying` with chips), the best chunks are found (**Top K**, default 3, with optional hybrid search and reranking), and the status reports `Retrieved {count} sources`, `Retrieved 1 source` or `No sources found`. The chunks are added to the prompt and shown as citations | `backend/open_webui/utils/middleware.py:2049-2165`, `:3206-3214`; `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:78-123`; `backend/open_webui/config.py:968` |
| Same, with **Using Entire Document**, **Full Context Mode** or **Bypass Embedding and Retrieval** | Every file's full text (under Full Context Mode, every chunk) is sent instead of the best chunks, which uses much more of the model's context window | `backend/open_webui/retrieval/utils.py:1592-1621`; `backend/open_webui/utils/middleware.py:2057-2063`, `:2133` |
| Mentioned in the chat, File Context off | Not retrieved; listed as attached knowledge for the model's knowledge tools instead (native mode only) | `backend/open_webui/utils/tools.py:499-514`; `backend/open_webui/utils/middleware.py:3206-3214` |
| Attached to the chat's folder | As for model knowledge: tools in native mode, retrieval in legacy mode | section 5.20 |
| Nothing attached anywhere, native mode, Builtin Tools and Knowledge Base on | The model can discover and search the knowledge bases the person can read, within the limits in 5.22, using the browsing tools | `backend/open_webui/utils/tools.py:631-642` |
| Builtin Tools or Knowledge Base off, or legacy mode without model knowledge | No knowledge tools; model-attached knowledge is unused in native mode. Chat-attached knowledge is still retrieved when File Context is on | `backend/open_webui/utils/middleware.py:2809-2813`; `backend/open_webui/utils/tools.py:607` |
| Request from the API rather than the chat page | Built-in tools are not added, so model knowledge is used only in legacy mode | `backend/open_webui/utils/middleware.py:3096-3099`, `:2809-2813` |
| Connected knowledge base | Retrieval asks the external source for the best matches; the Entire Document switch has no effect | `backend/open_webui/retrieval/utils.py:1581-1588`; `backend/open_webui/tools/builtin.py:3337-3360` |

In native mode the `Searching Knowledge for "{searchQuery}"` status is not shown, even when the model
has knowledge; only a hidden completion status is recorded (`backend/open_webui/utils/middleware.py:2608-2618`,
`:3248-3259`). Retrieval settings,
the prompt template, citations and reranking are in `rag-retrieval-embeddings-and-vector-stores.md`;
the order of these steps in the chat pipeline is in `chat-completion-pipeline-and-generation-tasks.md`,
section 5.

### 5.22 The Model's Knowledge Tools

These built-in tools are offered by `get_builtin_tools` under the **Knowledge Base** group. Their
outputs are visible to the person in the reply's tool-call entries. Full behaviour of every built-in
tool is in `builtin-native-tools.md`.

| Tool | Offered when | What it does | Limits | Source |
|---|---|---|---|---|
| `list_knowledge` | Knowledge is attached | Lists the attached knowledge bases (name, description, file count), files and notes; with a knowledge base id, pages through its files | Up to 200 files per call (default 50) | `backend/open_webui/tools/builtin.py:3009-3148` |
| `search_knowledge_files` | With or without attached knowledge (scoped to it when present) | Finds files by file name | Default 5 results; refuses a knowledge base that is not attached (`Knowledge base {knowledge_id} is not attached to this model`) or not readable (`Access denied to knowledge base {knowledge_id}`) | `backend/open_webui/tools/builtin.py:2164-2325` |
| `grep_knowledge_files` | With or without attached knowledge (scoped to it when present) | Exact text or pattern search through extracted text, returning matching lines | Up to 50 matching lines (`KNOWLEDGE_GREP_MAX_MATCHES`); without attachments, the first 200 readable knowledge bases | `backend/open_webui/tools/builtin.py:2629-2747`; `backend/open_webui/env.py:1177` |
| `query_knowledge_files` | With or without attached knowledge (scoped to it when present); also alongside `kb_exec` | Semantic search returning the best chunks with their source | Default 5 results; without attachments or named knowledge bases, the 50 most recently updated readable knowledge bases | `backend/open_webui/tools/builtin.py:3151-3369` |
| `view_knowledge_file` | When nothing is attached, or when files or knowledge bases are attached | Reads a file's extracted text in pages, by characters or lines | 10,000 characters by default, 100,000 at most (`VIEW_FILE_DEFAULT_MAX_CHARS`, `VIEW_FILE_MAX_CHARS`); `Access denied` without read access | `backend/open_webui/tools/builtin.py:2863-3006`; `backend/open_webui/env.py:1179-1180` |
| `view_file` | Files or knowledge bases are attached | Reads an attached file's text | As above | `backend/open_webui/tools/builtin.py:2750-2860` |
| `view_note` | Notes are attached | Reads an attached note | n/a | `backend/open_webui/tools/builtin.py:1224` |
| `list_knowledge_bases` | Nothing attached | Lists readable knowledge bases with file counts | Default 10 per call | `backend/open_webui/tools/builtin.py:2046-2101` |
| `search_knowledge_bases` | Nothing attached | Finds knowledge bases by words in name or description | Default 5 | `backend/open_webui/tools/builtin.py:2104-2161` |
| `query_knowledge_bases` | Nothing attached | Finds knowledge bases whose name and description are closest in meaning, using the knowledge search index | Default 5; scans up to 10,000 readable knowledge bases | `backend/open_webui/tools/builtin.py:75`, `:3372-3474` |
| `kb_exec` | Only when `ENABLE_KB_EXEC` is on; replaces the list, search, grep and view tools, keeping `query_knowledge_files` (and the two knowledge-base finders when nothing is attached) | Shell-style commands over knowledge bases (5.23) | Output cut at 30,000 characters | `backend/open_webui/utils/tools.py:607-620`; `backend/open_webui/env.py:968`, `:1173` |

Because the browsing tools reach the person's readable knowledge bases, a model with nothing attached can quote
a knowledge base the person did not mention, including ones shared with them or Public (section 11.13).

### 5.23 The Knowledge Filesystem Tool (`kb_exec`)

`kb_exec` (in `backend/open_webui/tools/knowledge_fs.py`) lets a model explore knowledge bases with
commands it already knows. It is off unless the environment variable `ENABLE_KB_EXEC` is `true`
(`backend/open_webui/env.py:968`). The model sends one command string; pipes (`|`) chain commands
(`backend/open_webui/tools/knowledge_fs.py:136-174`, `:1108-1132`).

| Command | What it returns | Source |
|---|---|---|
| `ls`, `ls <dir>/`, `ls -a` (flat list with paths), `-t` (newest first), `-S` (largest first), `-r` (reverse) | Each knowledge base's header (`Knowledge Base: {name} ({id})` and description), its directories and files with id, size and date; attached single files under `Attached Files:` | `backend/open_webui/tools/knowledge_fs.py:536-624` |
| `tree`, `tree <dir>/` | A directory tree per knowledge base with a count of directories and files | `:1026-1091` |
| `cat [-n] <file>` | The whole extracted text, optionally numbered | `:640-656` |
| `head -N`, `tail -N` (default 10 lines) | The first or last lines, with a `[showing …]` note when cut | `:659-714` |
| `sed -n 'M,Np' <file>` | A line range | `:971-1018` |
| `grep [-E] [-i] [-l] [-c] "pattern" [file] [dir/] [*.ext]` | Matching lines (or files, or counts), across all reachable files or a scope | `:721-851` |
| `find "*.md"`, `find docs/ "*.md"` | Files whose names match a pattern | `:854-891` |
| `wc [-l] <file>`, `stat <file>` | Line, word and character counts; file details including the knowledge base | `:894-968` |

Files can be named by id, by a path such as `policies/2026/handbook.md` (an invented example), or by file name; a name found in several
places returns `Ambiguous filename "{ref}". Use full path to disambiguate:` with the choices
(`backend/open_webui/tools/knowledge_fs.py:448-518`). Scope follows the same rule as the other tools:
attached knowledge when there is any, otherwise up to 50 readable knowledge bases
(`:307-361`). Limits: output is cut at 30,000 characters (`KB_EXEC_MAX_OUTPUT_CHARS`), a grep across
more than 200 files (`KB_EXEC_MAX_GREP_FILES`) asks for a narrower scope, at most 50 matching lines are
returned (`KNOWLEDGE_GREP_MAX_MATCHES`), patterns over 4,096 characters are refused, and pattern
matching stops after two seconds per command (`:31-36`, `:90-128`, `:802-803`, `:1192-1200`;
`backend/open_webui/env.py:1173-1177`). Patterns use RE2 syntax, without lookarounds or back-references
(`:1176`). Its messages are listed in section 10.8.

### 5.24 Admin: Reindex Knowledge and Memory Vectors

Use after changing the embedding model, as the hint under the model setting says: `After changing the
embedding model, reindex knowledge, knowledge search, and memory vectors for changes to take effect.`
(`src/lib/components/admin/Settings/Documents.svelte:1167-1171`).

1. Admin › Settings › **Documents** › **Danger Zone** › **Reindex Knowledge and Memory Vectors**
   (`Rebuild vectors for existing knowledge files, knowledge search, and memories.`) › **Reindex**
   (`src/lib/components/admin/Settings/Documents.svelte:1576-1591`;
   `src/lib/i18n/locales/en-US/translation.json:2317-2319`).
2. Confirm the **Reindex Embedding Data** dialog (`Rebuild knowledge file, knowledge search, and memory
   vectors using the current embedding model.`) (`src/lib/components/admin/Settings/Documents.svelte:382-388`).
3. Three requests run in turn; `Success` appears only after all three, and an error shows the server's
   text and stops the rest (`src/lib/components/admin/Settings/Documents.svelte:388-416`):
   1. every knowledge base's collection is deleted and each file is re-embedded from its stored
      extracted text, into both the knowledge base and the file's own collection
      (`backend/open_webui/routers/knowledge.py:374-461`; `backend/open_webui/routers/retrieval.py:1979-2017`);
   2. the knowledge search index is rebuilt from names and descriptions (`backend/open_webui/routers/knowledge.py:469-494`);
   3. memory vectors are rebuilt (`memories.md`).

The browser waits for the whole reindex in one request and shows no progress; the server log records
each file (`Reindexing knowledge base {kb_idx}/{n} file {i}/{total}{eta}: {filename}`) and the total
time (`backend/open_webui/routers/knowledge.py:396`, `:415-423`, `:453`). A file that fails is skipped
and logged; read from code it is marked failed and left linked without chunks in the knowledge base,
so it is listed but vector search of the knowledge base no longer returns it (`:438-441`, `:448-451`;
`backend/open_webui/routers/retrieval.py:2154-2166`). Whether a reverse proxy allows a request this long
is TO BE CONFIRMED.

### 5.25 Admin: Reset Vector Storage/Knowledge

Admin › Settings › **Documents** › **Danger Zone** › **Reset Vector Storage/Knowledge** (`Clear vector
storage and knowledge indexing data.`) › **Reset**, then confirm
(`src/lib/components/admin/Settings/Documents.svelte:1562-1575`;
`src/lib/i18n/locales/en-US/translation.json:2330-2331`). The server empties the whole vector store and
deletes **every knowledge base record of every person**, with their sharing
(`backend/open_webui/routers/retrieval.py:3271-3284`; `backend/open_webui/models/knowledge.py:808-820`).
Files stay in their owners' lists but lose their indexes. Unlike deleting one knowledge base, this does
not remove references from custom models, which then point at nothing. Read from code, the dialog shows
`Success` without waiting for the server, so a failure may go unreported
(`src/lib/components/admin/Settings/Documents.svelte:368-380`). The reset is described with the other
vector-store tasks in `rag-retrieval-embeddings-and-vector-stores.md`.

### 5.26 Connected (External) Knowledge Bases

Admins create these under Admin › Settings › **Integrations** › **Knowledge** › **External Knowledge
Sources** (**Add Connection**), choosing Qdrant, Milvus or pgvector, the collection and its field names,
and passing a test query that returns results (`Test must pass before a source is created.`)
(`src/lib/components/admin/Settings/ExternalKnowledge.svelte:797-888`;
`backend/open_webui/routers/knowledge.py:560`, `:944-1006`). Configuration is documented in
`rag-retrieval-embeddings-and-vector-stores.md`. From the knowledge-base side:

- **They are ordinary knowledge base records** with `meta.source = 'external'`, owned by the admin who
  created them and shareable like any other (`backend/open_webui/routers/knowledge.py:967-1004`).
- **In the list** they carry the provider name (or `Connected`) and `Read Only` badges; the second line
  shows the file count (0), provider, collection and auth mode (`src/lib/components/workspace/Knowledge.svelte:245-255`,
  `:456-462`).
- **Their page** shows `Connected`, `Read Only`, the provider and `Service Account`; **Mapped Source**;
  **Auth Mode** `Admin-managed service account`; and the note `This knowledge base retrieves from a
  connected source. Open WebUI can query it, but cannot upload, sync, edit, delete, reset, or reindex its
  source data.` A **Test Query** box (`Ask this knowledge source a test question`) with **Test** shows a
  **Preview** of up to five results (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1328-1399`).
  The test uses an admin-only endpoint, so for anyone else it returns the permission error
  (`backend/open_webui/routers/knowledge.py:879-891`; section 11.19).
- **Refused actions.** Adding, updating or removing files, resetting, syncing, directories and export
  answer `External knowledge bases are read-only.` (`backend/open_webui/routers/knowledge.py:143-151`,
  `:1439-1440`, `:1538-1539`, `:1628-1629`, `:1806-1807`, `:2053-2054`, `:2175-2176`, `:2233-2234`).
  Renaming, editing the description and sharing are allowed for people with write access.
- **Edge case read from code.** Dragging files onto a connected knowledge base's page checks only write
  access, and the upload path does not check the external flag, so such a file would be linked to it
  but ignored by retrieval, which asks only the external source; the grep and view tools could still
  read it (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1063-1070`;
  `backend/open_webui/routers/files.py:202-254`; `backend/open_webui/tools/builtin.py:2691-2712`; section 14.4).
- **Deleting** removes the record and, when an admin deletes the last knowledge base using a
  connection, the saved connection too; the external data is untouched
  (`backend/open_webui/routers/knowledge.py:1753-1764`).

Connection details, including any credentials, are kept in the persistent setting
`external_knowledge.connections` (`backend/open_webui/routers/knowledge.py:559`, `:629-634`). How they are
stored and protected is security-sensitive: refer to the platform maintainer and U of T Information
Security (security.utoronto.ca).

## 6. Data Model

Timestamps are epoch seconds. Ids are random UUIDs generated by the server
(`backend/open_webui/models/knowledge.py:203-216`, `:684-695`, `:834-843`). The schema of every table
is described in `database-schema-content-and-collaboration.md`; this section covers what support needs.

### 6.1 The `knowledge` Table

| Column | Meaning | Source |
|---|---|---|
| `id` | Knowledge base id; also the name of its vector collection | `backend/open_webui/models/knowledge.py:51`; `backend/open_webui/routers/knowledge.py:1484` |
| `user_id` | Owner (the creator); no code path found changes it | `:52`, `:210-211` |
| `name`, `description` | As typed; no uniqueness, no length limit in code | `:54-55`; `:165-168` |
| `meta` | JSON; empty for ordinary knowledge bases; see 6.2 | `:57` |
| `created_at`, `updated_at` | `updated_at` changes on name, description or `meta` updates and on reset, not on file changes | `:59-60`; `:731-796` |

Access is not stored on the row; it is in `access_grant` (6.6). A legacy `data` column may still exist in
the database without being used by the code (`_research-notes.md`, defect 7;
`backend/open_webui/migrations/versions/3e0e00844bb0_add_knowledge_file_table.py:127-128`; `backend/open_webui/migrations/versions/81cc2ce44d79_update_channel_file_and_knowledge_table.py:39-43`).

### 6.2 Keys Stored in `knowledge.meta`

| Key | When present | Meaning | Source |
|---|---|---|---|
| `source` = `external` | Connected knowledge bases | Switches the knowledge base to external retrieval and read-only behaviour | `backend/open_webui/routers/knowledge.py:143-144`, `:928-938` |
| `read_only` | Connected knowledge bases | Always `true` there | `:930` |
| `external` | Connected knowledge bases | `connection_id`, `source` (collection name and field mapping), `provider`, `auth_mode` (`service_account`), `capabilities` | `:931-937` |
| `legacy`, `document`, `tags` | Records migrated from the old document feature | Marks a migrated single document; clicking it in the list does not open it | `backend/open_webui/migrations/versions/6a39f3d8e55c_add_knowledge_table.py:65-80`; `src/lib/components/workspace/Knowledge.svelte:218-226` |

For any other `meta` content the list shows `key: value` pairs on the row's second line
(`src/lib/components/workspace/Knowledge.svelte:257-268`).

### 6.3 The `knowledge_file` Table

| Column | Meaning | Source |
|---|---|---|
| `id` | Link id | `backend/open_webui/models/knowledge.py:102` |
| `knowledge_id` | The knowledge base (cascade delete on PostgreSQL) | `:104` |
| `file_id` | The file (cascade delete on PostgreSQL) | `:105` |
| `directory_id` | The directory, or empty for the root. The code moves or removes these links itself before deleting a directory; on PostgreSQL the database would also empty the field | `:106`; `:1030-1039` |
| `user_id` | Who added the file (shown as `By {name}`); can differ from the file's owner | `:107`; `src/lib/components/workspace/Knowledge/KnowledgeBase/Files.svelte:180-194` |
| `created_at`, `updated_at` | When linked; `updated_at` changes when moved | `:109-110`; `:1097-1116` |

A file can be linked to a knowledge base once (unique key on knowledge base and file)
(`backend/open_webui/models/knowledge.py:112-115`). The same file can be linked to several knowledge
bases through the API; the interface links only files it has just uploaded (section 5.13).
These rows were created from the older `knowledge.data.file_ids` list by migration `3e0e00844bb0`
(`backend/open_webui/migrations/versions/3e0e00844bb0_add_knowledge_file_table.py:31-125`).

### 6.4 The `knowledge_directory` Table

| Column | Meaning | Source |
|---|---|---|
| `id` | Directory id | `backend/open_webui/models/knowledge.py:66` |
| `knowledge_id` | The knowledge base it belongs to | `:67` |
| `parent_id` | The parent directory, or empty for the root | `:68` |
| `name` | Directory name | `:69` |
| `user_id` | Who created it | `:70` |
| `created_at`, `updated_at` | `updated_at` changes on rename or move | `:72-73`; `:940-988` |

Unique on knowledge base, parent and name, with indexes on knowledge base and parent
(`backend/open_webui/models/knowledge.py:75-79`). Created by migration `3c9b0ca343fd`, which also added
`knowledge_file.directory_id` (`backend/open_webui/migrations/versions/3c9b0ca343fd_add_knowledge_directory_table.py:26-59`).
Every request that names a directory is checked to belong to the knowledge base in the address
(`backend/open_webui/routers/knowledge.py:154-169`).

### 6.5 File Fields This Area Relies On

| Field | Meaning | Source |
|---|---|---|
| `file.meta.data` | The metadata sent with the upload: `knowledge_id`, `directory_id`, `file_hash`, `source_url`, `language` | `backend/open_webui/routers/files.py:408-425`; `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:347-351`, `:438-448`, `:636-640` |
| `file.meta.file_hash` | SHA-256 of the raw bytes, compared by **Sync directory** | `backend/open_webui/routers/files.py:402-406`, `:422` |
| `file.meta.collection_name` | The last collection the file was indexed into (the knowledge base id after step 3) | `backend/open_webui/routers/retrieval.py:2122-2130` |
| `file.data.status`, `file.data.error` | `pending`, `processing`, `completed` or `failed`, and the failure text | `backend/open_webui/routers/files.py:259-269`; `backend/open_webui/routers/retrieval.py:2154-2166` |
| `file.data.content` | Extracted text: the source for indexing, reindexing, export, the drawer and the grep and view tools | `backend/open_webui/routers/retrieval.py:2064-2068` |
| `file.hash` | SHA-256 of the extracted text, used for the duplicate check and to delete chunks; cleared when processing fails | `backend/open_webui/routers/retrieval.py:2069`, `:2164-2166`; `backend/open_webui/routers/knowledge.py:1665-1667` |

### 6.6 Access Grants

Sharing is stored in `access_grant` rows with resource type `knowledge` and the knowledge base id:
principal `user` (a person, or `*` for Public) or `group`, permission `read` or `write`
(`backend/open_webui/models/knowledge.py:187-189`, `:223`, `:772-773`). Changing access replaces the
whole set (`backend/open_webui/routers/knowledge.py:1263`); deleting the knowledge base revokes all of
them (`backend/open_webui/models/knowledge.py:801`). The grant model is in
`users-groups-roles-and-permissions.md`, section 6.3.

### 6.7 Vector Store Collections

| Collection | Contents | Created | Removed | Source |
|---|---|---|---|---|
| `{knowledge id}` | Chunks of every file in a local knowledge base, each tagged with `file_id`, `name`, `source` and `hash` | When the first file is indexed into it | Reset, delete, or the start of a reindex; single files' chunks on remove or directory delete | `backend/open_webui/routers/retrieval.py:2101-2115`; `backend/open_webui/routers/knowledge.py:1665-1667`, `:1767`, `:1828` |
| `file-{file id}` | Chunks of one file | Step 2 of processing | When the file is deleted | `backend/open_webui/routers/retrieval.py:1946-1951`; `backend/open_webui/routers/knowledge.py:64-80` |
| `knowledge-bases` | One entry per knowledge base: name and description, used by `query_knowledge_bases` | On create, rename or description change, and by the metadata reindex | Entry removed on delete; whole collection rebuilt by the metadata reindex | `backend/open_webui/routers/knowledge.py:89-131`, `:469-494` |

Retrieval and the knowledge tools do not read the `knowledge-bases` collection on a non-admin's behalf
except through `query_knowledge_bases`, which filters to readable knowledge bases
(`backend/open_webui/retrieval/utils.py:1335-1337`; `backend/open_webui/tools/builtin.py:3427-3432`).
Which vector database production uses is TO BE CONFIRMED (`../tools/ground-truth.md`, Data Stores).

### 6.8 Settings Rows

Connected knowledge sources are a list stored in the `config` table under `external_knowledge.connections`
(not seeded by `DEFAULT_CONFIG`; written on first use). Each entry has an id, name, provider, endpoint,
authentication settings, field configuration, capabilities, health, enabled flag, creator and timestamps
(`backend/open_webui/routers/knowledge.py:559`, `:629-655`; `backend/open_webui/models/config.py:198-220`).
The interface does not receive the authentication settings, only whether they are set
(`backend/open_webui/routers/knowledge.py:622-626`).

### 6.9 What Deletions Leave Behind

| Action | Database rows left | Vector data left | Files left |
|---|---|---|---|
| Remove a file (owner or admin, retention off) | None for that file; on SQLite, links to it in other knowledge bases (read from code) | Its chunks in any other knowledge base that also held it (read from code) | None |
| Remove a file (collaborator, or retention on) | The file row | Its `file-{id}` collection | The file |
| Delete a directory with contents | Files used elsewhere, owned by others, or kept by retention | Their `file-{id}` collections | Those files |
| Reset | Directories only when not included (the interface includes them) | `file-{id}` collections of files not deleted | Files owned by others, or all files when retention is on |
| Delete a knowledge base | On SQLite, its `knowledge_file` and `knowledge_directory` rows (read from code) | Every file's `file-{id}` collection | Every file |
| Reset Vector Storage/Knowledge | All `knowledge_file` and `knowledge_directory` rows on SQLite; model references everywhere | None | Every file |

Sources: `backend/open_webui/routers/knowledge.py:64-80`, `:1613-1694`, `:1702-1846`, `:2324-2373`;
`backend/open_webui/models/knowledge.py:731-820`, `:1009-1075`; `backend/open_webui/routers/retrieval.py:3271-3284`;
`backend/open_webui/internal/db.py:335-400`.

### 6.10 Personal Data in This Area

- **Document text.** Extracted text sits in `file.data.content` and in vector chunks; exports and the
  **File content** search expose all of it (sections 5.12, 5.16).
- **People.** The list and file rows show owners' and contributors' names, with emails on hover; the
  API returns the owner's user record with each knowledge base (`backend/open_webui/models/knowledge.py:347-362`;
  `src/lib/components/workspace/Knowledge.svelte:490-504`).
- **Storage tags.** Uploaded files are stored with the uploader's email, id and name as storage tags
  (`backend/open_webui/routers/files.py:368-373`; see `files-uploads-and-storage.md`).
- **Events.** Knowledge events sent to webhooks and event functions identify the acting person
  (section 9).
- **Logs.** Reindex logs record file names, and the upload path logs file and user ids
  (`backend/open_webui/routers/knowledge.py:415-423`; `backend/open_webui/routers/files.py:222-225`).

## 7. Settings and Configuration

Code defaults are what the repository says; the live value of every persistent setting is data in the
`config` table, and environment-only values are set on the server. All live values are TO BE CONFIRMED
(section 14.1). After first boot a stored setting wins over its environment variable
(`../tools/ground-truth.md`, Settings).

### 7.1 Persistent Settings

| Key | Admin label | Code default (seeded from) | Effect on knowledge bases | Source |
|---|---|---|---|---|
| `user.permissions` › `workspace.knowledge`, `sharing.knowledge`, `sharing.public_knowledge`, `access_grants.*`, `chat.file_upload` | Group and default permissions | See section 3.2 | Who can open, create and share knowledge bases, and attach them in chat | `backend/open_webui/config.py:1940-2022`, `:3101` |
| `rag.file.max_size` | **Max Upload Size** (`Maximum file size in MB. Leave empty for unlimited.`) | none, unlimited (`RAG_FILE_MAX_SIZE`) | Largest file accepted, checked in the browser and on the server; also caps edited text in the drawer | `backend/open_webui/config.py:983`, `:2907`; `backend/open_webui/routers/files.py:394-400`, `:735-740`; `backend/open_webui/main.py:2414`; `src/lib/i18n/locales/en-US/translation.json:2281-2282` |
| `rag.file.allowed_extensions` | **Allowed File Extensions** (`Comma-separated upload extensions. Leave empty for all file types.`) | empty, all types (`RAG_ALLOWED_FILE_EXTENSIONS`) | Extensions accepted for upload | `backend/open_webui/config.py:998-1000`, `:2910`; `backend/open_webui/routers/files.py:354-362`; `src/lib/i18n/locales/en-US/translation.json:2198-2199` |
| `rag.file.max_count` | **Max Upload Count** (`Maximum number of files that can be used at once in chat.`) | none (`RAG_FILE_MAX_COUNT`) | Does not apply to knowledge bases; chat only | `backend/open_webui/config.py:981`, `:2906`; `src/lib/components/chat/MessageInput.svelte:1090-1100`; `src/lib/i18n/locales/en-US/translation.json:2279-2280` |
| `rag.top_k`, `rag.top_k_reranker`, `rag.relevance_threshold`, `rag.enable_hybrid_search`, `rag.hybrid_bm25_weight` | **Top K**, **Top K Reranker**, **Relevance Threshold**, **Hybrid Search** | 3, 3, 0.0, off, 0.5 | How many chunks are retrieved for knowledge attached in chat, and for model knowledge in legacy mode | `backend/open_webui/config.py:968-973`, `:2899-2903`; `backend/open_webui/utils/middleware.py:2108-2135` |
| `rag.full_context` | **Full Context Mode** (`Inject entire documents as context for comprehensive processing.`) | off (`RAG_FULL_CONTEXT`) | Whole documents instead of chunks for every retrieval | `backend/open_webui/config.py:979`, `:2905`; `src/lib/i18n/locales/en-US/translation.json:2264-2265` |
| `rag.bypass_embedding_and_retrieval` | **Bypass Embedding and Retrieval** | off (`BYPASS_EMBEDDING_AND_RETRIEVAL`) | No vectors are made; files are linked with their text only, the duplicate check does not run, and chats receive full text | `backend/open_webui/config.py:965`, `:2898`; `backend/open_webui/routers/retrieval.py:2071-2088`; `backend/open_webui/retrieval/utils.py:1592` |
| `rag.embedding_engine`, `rag.embedding_model`, `rag.chunk_size`, `rag.chunk_overlap` | Embedding and chunking settings | local engine, `sentence-transformers/all-MiniLM-L6-v2`, 1000, 100 | How knowledge base text is chunked and embedded; changes need the reindex in 5.24 | `backend/open_webui/config.py:1002`, `:1008`, `:1064`, `:1068`, `:2911`, `:2914`, `:2928`, `:2930` |
| `rag.content_extraction_engine` | Content extraction engine | default loader (`CONTENT_EXTRACTION_ENGINE`) | How text is pulled from uploaded documents | `backend/open_webui/config.py:868`, `:2863` |
| `rag.template` | RAG template | built-in template (`RAG_TEMPLATE`) | How retrieved chunks are presented to the model | `backend/open_webui/config.py:1096`, `:2931` |
| `task.query.retrieval.enable` | Retrieval query generation | on (`ENABLE_RETRIEVAL_QUERY_GENERATION`) | Generates the search phrases shown as `Querying` | `backend/open_webui/config.py:2304`, `:3147`; `backend/open_webui/utils/middleware.py:2061-2103` |
| `external_knowledge.connections` | **External Knowledge Sources** | not seeded; created on first use | Saved connections for connected knowledge bases | `backend/open_webui/routers/knowledge.py:559`, `:629-634` |

Each `rag.*` setting is described in full in `rag-retrieval-embeddings-and-vector-stores.md` and
`configuration-persistent-settings-r-to-w.md`.

### 7.2 Environment-Only Settings

Read once at startup; changing them needs a restart.

| Variable | Default | Effect | Source |
|---|---|---|---|
| `ENABLE_KNOWLEDGE_FILE_RETENTION` | `False` | `True` keeps files when they are removed from a knowledge base, a directory is deleted with contents, a sync removes them or the knowledge base is reset (they are only unlinked) | `backend/open_webui/config.py:985`; `backend/open_webui/routers/knowledge.py:1618`, `:1825`, `:2013-2018`, `:2359-2364` |
| `BYPASS_ADMIN_ACCESS_CONTROL` (falls back to `ENABLE_ADMIN_WORKSPACE_CONTENT_ACCESS`) | `True` | Admins see and can change every knowledge base (section 3.4) | `backend/open_webui/config.py:2084-2092` |
| `ENABLE_KB_EXEC` | `False` | Offers `kb_exec` instead of the list, search, grep and view knowledge tools | `backend/open_webui/env.py:968`; `backend/open_webui/utils/tools.py:607-620` |
| `KB_EXEC_MAX_OUTPUT_CHARS` | `30000` | Longest `kb_exec` output | `backend/open_webui/env.py:1173` |
| `KB_EXEC_MAX_GREP_FILES` | `200` | Files one `kb_exec` grep may scan | `backend/open_webui/env.py:1175` |
| `KNOWLEDGE_GREP_MAX_MATCHES` | `50` | Matching lines returned by `kb_exec` grep and `grep_knowledge_files` | `backend/open_webui/env.py:1177` |
| `VIEW_FILE_DEFAULT_MAX_CHARS`, `VIEW_FILE_MAX_CHARS` | `10000`, `100000` | Characters returned per call by `view_file` and `view_knowledge_file` | `backend/open_webui/env.py:1179-1180` |
| `RAG_FILE_CONTENT_SEARCH_MAX_CHARS` | 67,108,864 (64 Mi) | How much of each file's text the **File content** search examines | `backend/open_webui/config.py:987` |
| `USER_PERMISSIONS_WORKSPACE_KNOWLEDGE_ACCESS`, `USER_PERMISSIONS_WORKSPACE_KNOWLEDGE_ALLOW_SHARING`, `USER_PERMISSIONS_WORKSPACE_KNOWLEDGE_ALLOW_PUBLIC_SHARING` | `False` each | Seed the default permissions in 3.2 at first boot only | `backend/open_webui/config.py:1737-1800` |
| `ENABLE_RETRIEVAL_UNSCOPED_COLLECTIONS`, `BYPASS_RETRIEVAL_ACCESS_CONTROL` | `False` | Change how retrieval checks collection access. Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca) | `backend/open_webui/env.py:833`, `:839`; `backend/open_webui/retrieval/utils.py:1299-1319` |

The vector database and file storage back ends (`VECTOR_DB`, `STORAGE_PROVIDER`) are environment-only
and TO BE CONFIRMED for production (`../tools/ground-truth.md`, Data Stores).

### 7.3 Limits Fixed in Code

| Limit | Value | Source |
|---|---|---|
| Knowledge bases per person, files per knowledge base, directory depth | No limit found in code | `backend/open_webui/routers/knowledge.py` (no count checks); `backend/open_webui/models/knowledge.py` |
| Knowledge bases per page (list, search, pickers) | 30 | `backend/open_webui/routers/knowledge.py:61`, `:178-180` |
| Files per page on a knowledge base page | 30 (admins may request more through the API) | `backend/open_webui/routers/knowledge.py:1388-1395`; `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1604-1606` |
| Pending-file check | Page re-checks every 5 seconds while files are pending; the server's stream (not used by the page) polls every 3 seconds for up to an hour | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:227-239`; `backend/open_webui/routers/knowledge.py:1330-1338` |
| Upload status wait | Polls once a second for up to two hours | `backend/open_webui/routers/files.py:644-668` |
| Search debounce | 300 ms on the list and inside a knowledge base; 200 ms in chat pickers | `src/lib/components/workspace/Knowledge.svelte:88-93`; `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:158-168`; `src/lib/components/chat/MessageInput/Commands/Knowledge.svelte:73-78` |
| Name and description auto-save delay | 1 second | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:975-993` |
| Knowledge bases searched by tools when nothing is attached | 50 (`query_knowledge_files`, `kb_exec`), 200 (`grep_knowledge_files`), up to 10,000 (`query_knowledge_bases`) | `backend/open_webui/tools/builtin.py:3290-3299`, `:2717-2727`, `:75`; `backend/open_webui/tools/knowledge_fs.py:351-359` |
| `list_knowledge` files per call | 200 | `backend/open_webui/tools/builtin.py:3053` |
| `kb_exec` pattern length and matching time | 4,096 characters; 2 seconds per command | `backend/open_webui/tools/knowledge_fs.py:34-36` |

### 7.4 Per-Model Controls That Change How Knowledge Is Used

| Control | Where | Default | Effect | Source |
|---|---|---|---|---|
| **Function Calling** parameter | Model editor › Advanced Params (or chat controls) | Native | Native: tools; Legacy: retrieval of model knowledge before the reply | `src/lib/i18n/locales/en-US/translation.json:2825-2826`; `backend/open_webui/utils/middleware.py:2604-2643` |
| **Builtin Tools** capability | Model editor › Capabilities | On | Off removes every knowledge tool | `backend/open_webui/utils/middleware.py:2809-2813`; `src/lib/i18n/locales/en-US/translation.json:2573-2574` |
| **Knowledge Base** built-in tool group | Model editor › Builtin Tools | On | Off removes the knowledge tools and the attached-knowledge list | `backend/open_webui/utils/tools.py:607`; `backend/open_webui/utils/middleware.py:3104`; `src/lib/i18n/locales/en-US/translation.json:2554-2555` |
| **File Context** capability (shown only while **File Upload** is on) | Model editor › Capabilities | On | Off stops retrieval of chat attachments; knowledge mentioned in chat is offered to the tools instead | `backend/open_webui/utils/middleware.py:3206-3214`; `backend/open_webui/utils/tools.py:499-514`; `src/lib/components/workspace/Models/Capabilities.svelte:72-76` |
| **File Upload** capability | Model editor › Capabilities | On | Off greys **Attach Knowledge** and clears knowledge attachments in the composer (section 5.19) | `src/lib/components/chat/MessageInput.svelte:768-773`; `src/lib/components/chat/MessageInput/InputMenu.svelte:67-78` |

Capabilities and built-in tool groups are described in `workspace-models-and-model-access.md`,
section 5.4.

## 8. Cron Jobs and Background Processes

There is no scheduled job for knowledge bases: nothing syncs folders, re-indexes, or cleans up on a
timer, and **Sync directory** runs only when a person starts it (`backend/open_webui/main.py:345-472`
starts no knowledge task; `../tools/ground-truth.md`, Startup Order). What runs outside the click:

| Process | When | Where it runs | Notes | Source |
|---|---|---|---|---|
| Upload processing | After each upload from a knowledge base page | A background task in the web worker that received the upload, after the response is sent | Extracts, indexes and links the file (section 5.6). Read from code, no job resumes a task cut off by a restart; such a file stays `pending` or `processing` and keeps showing a spinner (section 11.6) | `backend/open_webui/routers/files.py:435-446`, `:128-277`; `backend/open_webui/models/files.py:407-443` |
| Pending-file polling | While a knowledge base page with pending files is open | The browser | Every 5 seconds until none remain | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:227-239` |
| Knowledge search index update | At save time (create, rename, description change), not in the background | The request itself | A failure is only logged | `backend/open_webui/routers/knowledge.py:346-353`, `:1188-1195` |
| Reindex | When an admin presses **Reindex** | Inside that one request, file by file | No browser progress; log lines per file | `backend/open_webui/routers/knowledge.py:374-461` |
| Event delivery | After each knowledge action | Background tasks per event | Webhooks, event functions and personal notifications (section 9) | `backend/open_webui/events.py:1062-1086`, `:1159-1174` |

With more than one worker or replica, uploads are processed by whichever worker received them; shared
storage, a shared vector store and PostgreSQL are needed for every worker to see the same knowledge bases
(`CLAUDE.md`, Deployment).

## 9. Notifications and Emails

The application sends no email (`../tools/ground-truth.md`, Contacts). Knowledge actions produce:

- **Toasts on the page** for the person acting (section 10).
- **No socket or in-app notification** of their own; a colleague viewing the same knowledge base sees
  changes only after reloading or navigating (no knowledge socket events exist in
  `backend/open_webui/socket/main.py`; the page reloads its list only after its own actions).
- **Events** published to every event sink: admin-configured event webhooks, active **Event** functions,
  and personal notification targets (`backend/open_webui/events.py:1171-1202`). Each carries the acting
  person's id, name, email and role (`backend/open_webui/events.py:704`), which is personal data.

| Event | Raised by | Source |
|---|---|---|
| `knowledge.created` | Create | `backend/open_webui/routers/knowledge.py:354-360`; `backend/open_webui/events.py:347-349` |
| `knowledge.updated` | Name or description change | `backend/open_webui/routers/knowledge.py:1200-1206`; `backend/open_webui/events.py:350-352` |
| `knowledge.access_updated` | Access change | `backend/open_webui/routers/knowledge.py:1269-1275`; `backend/open_webui/events.py:362-364` |
| `knowledge.file.added` | File linked through `file/add` (not the upload path) | `backend/open_webui/routers/knowledge.py:1509-1515`; `backend/open_webui/events.py:365-367` |
| `knowledge.file.updated` | File re-indexed through `file/update` | `backend/open_webui/routers/knowledge.py:1593-1599`; `backend/open_webui/events.py:368-370` |
| `knowledge.file.removed` | File removed (with whether it was deleted) | `backend/open_webui/routers/knowledge.py:1682-1688`; `backend/open_webui/events.py:371-375` |
| `knowledge.file.moved` | File moved between directories | `backend/open_webui/routers/knowledge.py:2406-2412`; `backend/open_webui/events.py:376-378` |
| `knowledge.directory.created`, `.updated`, `.deleted` | Directory actions | `backend/open_webui/routers/knowledge.py:2277-2283`, `:2314-2320`, `:2366-2372`; `backend/open_webui/events.py:379-393` |
| `knowledge.reset` | Reset | `backend/open_webui/routers/knowledge.py:1839-1845`; `backend/open_webui/events.py:356-358` |
| `knowledge.deleted` | Delete | `backend/open_webui/routers/knowledge.py:1777-1783`; `backend/open_webui/events.py:353-355` |
| `knowledge.reindexed` | Admin reindex of all knowledge bases | `backend/open_webui/routers/knowledge.py:454-460`; `backend/open_webui/events.py:359-361` |
| `knowledge.external_connection.created`, `.updated`, `.deleted` | Admin connection changes | `backend/open_webui/routers/knowledge.py:708-714`, `:745-751`, `:774-780`; `backend/open_webui/events.py:394-408` |
| `file.uploaded` | Every upload, including those into knowledge bases | `backend/open_webui/routers/files.py:314-320` |
| `retrieval.content.processed`, `retrieval.content.process_failed` | Each indexing step that succeeds or fails | `backend/open_webui/routers/retrieval.py:2074-2081`, `:2136-2143`, `:2167-2180`; `backend/open_webui/events.py:409-418` |

`retrieval.content.process_failed` is one of the five notification events: a person who has added a
personal notification target subscribed to it is told when one of their files fails to process, when
admins have enabled user webhooks (`ui.enable_user_webhooks`) and, for the default "away" delivery, only
while they are not active in the app (`backend/open_webui/events.py:669-675`;
`backend/open_webui/utils/notifications.py:393-419`). Personal notification targets are described in
`user-settings-and-personalisation.md`; admin event webhooks in `admin-settings-panels.md`.

## 10. Error, Warning and Notice Messages (Verbatim)

Interpolated values are written as `{name}` using the source's variable name. Plain-key English text is
the key itself; dotted keys are quoted from `src/lib/i18n/locales/en-US/translation.json`. Backend
texts reach people as red pop-ups on the page that made the request: the knowledge pages print the
server's `detail` text as it is (for example `src/lib/components/workspace/Knowledge.svelte:181-183`;
`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1115-1118`), and processing failures of
uploads arrive as yellow warnings (`:376-379`, `:464-467`). Rows marked "Log" are server log lines, not
user messages; several contain user or file ids.

### 10.1 Backend: Knowledge Router (`backend/open_webui/routers/knowledge.py`)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `We could not find what you're looking for :/` | Error (HTTP 404 on open, access change, pending list, export, directories and move; HTTP 400 elsewhere) | `:1134-1138`, `:1158-1162`, `:1233-1237`, `:1306-1310`, `:1366-1370`, `:1433-1438`, `:1460-1465`, `:1532-1569`, `:1622-1659`, `:1709-1714`, `:1800-1805`, `:2047-2052`, `:2169-2174`, `:2227-2232`, `:2386-2391`, `:161-169`; external `:723-725`, `:737-739`, `:762-764`, `:789-791`, `:886-888`, `:901-903`, `:1017-1019`; text `backend/open_webui/constants.py:78` | The knowledge base, file or directory no longer exists, the file is not in this knowledge base, or the page is out of date | Reload Workspace › Knowledge | Whether and when it was deleted (section 5.15); the id |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 401 on open; HTTP 403 for directories, moves, sync and adding a file the person cannot read; HTTP 400 for the file list, the pending list and other changes) | `:1129-1133`, `:1164-1177`, `:1239-1253`, `:1312-1325`, `:1372-1386`, `:1442-1456`, `:1472-1478`, `:1541-1555`, `:1631-1645`, `:1716-1730`, `:1809-1823`, `:2056-2070`, `:2089-2096`, `:2235-2249`; text `backend/open_webui/constants.py:70-72` | Opening a knowledge base without read access; changing one without write access; adding someone else's file without read access to it | Ask the owner for access | Who owns it and how it is shared (section 3) |
| `401 Unauthorized` | Error (HTTP 401) | `:328-334`, `:380-384`; text `backend/open_webui/constants.py:69` | Creating without Knowledge Access; a non-admin calling the reindex | Ask an admin about Knowledge Access | The person's permissions (section 3.2) |
| `External knowledge bases are read-only.` | Error (HTTP 400) | `:143-151`, used at `:1439-1440`, `:1538-1539`, `:1628-1629`, `:1806-1807`, `:2053-2054`, `:2175-2176`, `:2233-2234` | Adding, updating or removing files, resetting, syncing, directory actions, moving or exporting on a connected knowledge base | None; connected knowledge bases are managed at the source | Confirm the **Connected** badge |
| `Uh-oh! This file is already registered. Please choose another file.` | Error (HTTP 400) | `:362-366`, `:925-926`, `:988-991`; text `backend/open_webui/constants.py:52` | The new knowledge base could not be written to the database (the wording about files is misleading) | Try again | Escalate with the time; server log |
| `Uh-oh! This id is already registered. Please choose another id string.` | Error (HTTP 400) | `:1208-1212`; text `backend/open_webui/constants.py:54` | Saving a name or description failed in the database (misleading wording) | Try again | Escalate with the time |
| `Extracted content is not available for this file. Please ensure that the file is processed before proceeding.` | Error (HTTP 400) | `:1466-1470`; text `backend/open_webui/constants.py:110-112` | Adding an existing file that has no extracted content (API, or **Add webpage** for a file address) | Re-upload the file | The file's processing status |
| `{e}` (the processing error, prefixed with its status code, for example `400: Duplicate content detected. Please provide unique content to proceed.`) | Error (HTTP 400) | `:1497-1502`, `:1582-1586`, `:2123-2125` | Indexing failed while adding or re-indexing an existing file (see 10.2 for the underlying texts) | Depends on the text | Section 10.2 |
| `Target directory not found.` | Error (HTTP 404) | `:1458`, `:2073`, `:2393` | The chosen directory was deleted or belongs to another knowledge base | Reload the page | Directory still present? |
| `Parent directory not found.` | Error (HTTP 404) | `:2263`, `:2301` | Creating or moving into a directory that no longer exists | Reload the page | None |
| `Failed to create directory. A directory with this name may already exist at this level.` | Error (HTTP 400) | `:2272-2276` | Same name already used at that level, or a database error | Choose another name | None |
| `Failed to update directory. This may be caused by a naming conflict or circular move.` | Error (HTTP 400) | `:2309-2313` | Rename to a taken name, or a move into the directory's own sub-tree | Choose another name or target | None |
| `Failed to delete directory.` | Error (HTTP 500) | `:2344-2348` | The directory could not be removed | Try again | Escalate with the time |
| `Failed to move file.` | Error (HTTP 500) | `:2401-2405` | The move could not be saved | Try again | Escalate with the time |
| `File {missing_ids[0]} not found` | Error (HTTP 400) | `:2083-2087` | API batch add named a file that does not exist | n/a (API only) | None |
| `Some files failed to process` | Warning field | `:2139-2149` | API batch add with failures; read from code the response model has no `warnings` field, so this is dropped | n/a (API only) | Section 14.4 |
| `Unsupported external knowledge provider.`, `Knowledge source name is required.`, `Knowledge source endpoint is required.`, `Only collection sources are supported.`, `Collection name is required.`, `Content field is required.`, `Vector field is required.` | Error (HTTP 400) | `:564-575`, `:595-598`, `:613-616` | Admin connection or source form incomplete or unsupported | Admin completes the form | `rag-retrieval-embeddings-and-vector-stores.md` |
| `External connection is still used by knowledge bases.` | Error (HTTP 400) | `:766-770` | Admin deleting a connection that knowledge bases still use | Delete or re-point those knowledge bases first | Which knowledge bases use it |
| `Test query is required.`, `Test query returned no results.` | Error (HTTP 400) | `:816-817`, `:964-965`, `:1040-1041` | Admin creating or updating a source without a test query, or with one that finds nothing | Use a query the source can answer | Source configuration |
| `External connection not found.` | Error (HTTP 404) | `:862-864`, `:1026-1027` | The saved connection was removed | Recreate it | None |
| `Knowledge name is required.` | Error (HTTP 400) | `:904-905`, `:951-952`, `:1020-1021` | Admin left the connected knowledge base's name blank | Enter a name | None |
| `Something went wrong :/` | Error (HTTP 400) | `:1063-1066`, `:1080-1083`; text `backend/open_webui/constants.py:16-18` | Saving an edited connected source failed | Try again | Escalate with the time |

### 10.2 Backend: Other Files That Surface on Knowledge Pages

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Duplicate content detected. Please provide unique content to proceed.` | Warning on upload; error elsewhere | `backend/open_webui/routers/retrieval.py:1734-1753`; `backend/open_webui/constants.py:109` | A file whose extracted text matches a file already in this knowledge base (same text under another name, or the same folder uploaded twice) | None needed if the content is already there; otherwise change the file | Section 11.7 |
| `The content provided is empty. Please ensure that there is text or data present before proceeding.` | Warning | `backend/open_webui/routers/retrieval.py:1820`, `:2014-2015`; `backend/open_webui/constants.py:95` | No text could be extracted (scanned image-only PDF, video, empty file, unreadable format), or a reindex found no stored text | Upload a text-bearing version | Extraction engine (`rag-retrieval-embeddings-and-vector-stores.md`) |
| `File type {content_type} is not supported for processing` | Warning | `backend/open_webui/routers/files.py:186-187` | An image (or video) while the extraction engine is not set up for media | Use a document format | `rag.content_extraction_engine` |
| `[ERROR: File type {file_extension} is not allowed]` | Error (HTTP 400) | `backend/open_webui/routers/files.py:356-362`; `backend/open_webui/constants.py:16-23` | Extension not in **Allowed File Extensions** | Convert the file | `rag.file.allowed_extensions` |
| `Oops! The file you're trying to upload is too large. Please upload a file that is less than {size}.` | Error (HTTP 413) | `backend/open_webui/routers/files.py:394-400`, `:735-740`; `backend/open_webui/constants.py:105-107` | Over **Max Upload Size** (also when saving edited text that is too long) | Use a smaller file | `rag.file.max_size` |
| `Failed to link file {file_item.id} to knowledge {knowledge_id}` | Warning | `backend/open_webui/routers/files.py:245-257` | Both indexing steps succeeded but the link could not be saved | Upload again | Escalate with the time |
| `Pandoc is not installed on the server. Please contact your administrator for assistance.` | Warning | `backend/open_webui/routers/retrieval.py:2180-2184`; `backend/open_webui/constants.py:85` | Extraction needed Pandoc, which is missing | None | Escalate to the platform maintainer |
| `Error saving document to vector database` | Warning | `backend/open_webui/routers/retrieval.py:2150-2151` | The vector store refused the chunks | Try later | Vector store health (escalate) |
| `[ERROR: Error processing URL]` | Error (HTTP 400) | `backend/open_webui/routers/retrieval.py:2421-2427` | **Add webpage** could not fetch or process the address | Check the address | `web-search-and-web-loading.md` |
| `[ERROR: Could not read content from {url}]` | Error (HTTP 400) | `backend/open_webui/routers/retrieval.py:2450-2455` | The web page could not be read | Check the address | Same |
| `We could not find what you're looking for :/` | Error (HTTP 404) | `backend/open_webui/routers/files.py:1001-1005`, `:783-787` | **Rename** or a drawer **Save** on a file the person cannot write (for example the knowledge base's owner acting on a collaborator's file) | Ask the file's uploader | Section 3.5 |
| `[ERROR: Error renaming file]` | Error (HTTP 400) | `backend/open_webui/routers/files.py:995-1000` | The new name could not be saved | Try again | Escalate with the time |

Embedding-service errors and extraction-engine errors pass through as their own text in the warning;
they are listed in `rag-retrieval-embeddings-and-vector-stores.md`.

### 10.3 Workspace › Knowledge List and Create Dialog

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Knowledge created successfully.` | Success | `src/lib/components/workspace/Knowledge/CreateKnowledgeBase.svelte:45-47` | Create succeeded | None | None |
| `Please fill in all fields.` | Error | `src/lib/components/workspace/Knowledge/CreateKnowledgeBase.svelte:31-37` | Name or description blank or only spaces; both boxes are then cleared | Type both again | None |
| `Knowledge deleted successfully.` | Success | `src/lib/components/workspace/Knowledge.svelte:185-188` | Delete succeeded | None | Section 5.15 for what was kept |
| `Knowledge exported successfully` | Success | `src/lib/components/workspace/Knowledge.svelte:201-212` | Admin export downloaded | None | The ZIP holds extracted text only |
| `Only collections can be edited, create a new knowledge base to edit/add documents.` | Error | `src/lib/components/workspace/Knowledge.svelte:218-226` | Clicking a migrated legacy document (`meta.document`) | Create a new knowledge base and upload the document | Section 6.2 |
| `No knowledge found` and `Try adjusting your search or filter to find what you are looking for.` | Empty state | `src/lib/components/workspace/Knowledge.svelte:540-549` | Nothing readable matches (or nothing is shared with the person) | Clear the search and filters | Section 11.2 |
| `Confirm your action` and `This action cannot be undone. Do you wish to continue?` | Confirmation | `src/lib/components/workspace/Knowledge.svelte:297-302`; `src/lib/components/common/ConfirmDialog.svelte:140-153` | **Delete** on a row | Confirm or cancel | None |
| `Read Only` | Badge | `src/lib/components/workspace/Knowledge.svelte:456-466` | No write access, or a connected knowledge base | None | Section 3.1 |
| `Deleted User` | Label | `src/lib/components/workspace/Knowledge.svelte:493-503` | The owner's account no longer exists | None | Section 3.3 |
| `Create a knowledge base`, `What are you working on?`, `What are you trying to achieve?`, `Name your knowledge base`, `Describe your knowledge base and objectives`, `Create Knowledge` | Labels | `src/lib/components/workspace/Knowledge/CreateKnowledgeBase.svelte:57`, `:103`, `:110`, `:120`, `:128`, `:138`, `:180` | Create dialog | n/a | n/a |

### 10.4 Knowledge Base Page

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| Server text, then the page returns to the list | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1113-1128` | Opening a deleted or unreadable knowledge base (10.1) | Ask the owner, or check the address | Section 11.2 |
| `Read Only` | Label | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1287-1291`, `:1335` | No write access, or connected | Ask the owner for Write | Section 11.3 |
| `File added successfully.` | Success | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:380-382`, `:468-470` | Upload processed (see the caution in 5.6) | None | If the file is missing, section 11.5 |
| `{error}` (the processing failure text, for example `Duplicate content detected. Please provide unique content to proceed.`) | Warning | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:376-379`, `:464-467` | Processing failed; the file is not added | Act on the text (10.2) | Section 11.4 |
| `Failed to upload file.` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:384-386`, `:472-474`, `:647` | The upload returned nothing | Try again | Network or server availability |
| `You cannot upload an empty file.` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:415-418` | 0-byte file | Choose the right file | None |
| `File size should not exceed {maxSize} MB.` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:420-434` | Over **Max Upload Size** | Use a smaller file | `rag.file.max_size` |
| `You do not have permission to upload files to this knowledge base.` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1067-1070` | Dropping files without write access | Ask the owner for Write | Section 3.1 |
| `File not found.` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1106-1108`, `:1212-1214` | A drop or file picker produced no file | Try again | None |
| `Knowledge base not found.` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:304-307` | **Add webpage** before the page finished loading | Wait, then retry | None |
| `Failed to process URL: {url}` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:387-391` | The address returned nothing usable | Check the address | Section 5.7 |
| `Please enter a valid URL.` | Error | `src/lib/components/chat/MessageInput/AttachWebpageModal.svelte:28-31` | Invalid address in **Attach Webpage** | Correct it | None |
| `Failed to add file.` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:780-798` | Read from code, no control calls this handler | n/a | n/a |
| `File removed successfully.` | Success | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:907-909` | File removed (and possibly deleted, 5.13) | None | Section 11.10 |
| `File renamed.` | Success | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:917-927` | Rename saved | None | None |
| `File content updated successfully.` | Success | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:955-957` | Drawer **Save** returned | None | Section 11.16 if the change did not stick |
| `Failed to load file content.` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:266-269` | The drawer could not load the file | Reload | File still present? |
| `Please fill in all fields.` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:976-979` | Name or description cleared on the page | Type it back | None |
| `Knowledge updated successfully` | Success | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:990-992` | Name or description auto-saved | None | None |
| `Saved` | Success | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1229-1236` | An access change saved | Reopen the dialog to see what was kept | Section 5.4 |
| `ID copied to clipboard` | Success | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1308-1318` | Clicked the id | None | Use the id in escalations |
| `Reset knowledge base?` and `This will remove all files and directories from this knowledge base. This action cannot be undone.` | Confirmation | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1731-1745` | **+** › **Reset** | Confirm or cancel | Section 5.14 |
| `Knowledge base has been reset` | Success | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1734-1737` | Reset succeeded (nothing is shown on failure) | None | None |
| `No content found` | Empty state | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1607-1615` | Nothing at this level, or no search match | Check sub-directories; clear the search | Section 11.17 |
| `By {name}` | Label | `src/lib/components/workspace/Knowledge/KnowledgeBase/Files.svelte:180-194` | Who added the file | n/a | n/a |
| `This knowledge base retrieves from a connected source. Open WebUI can query it, but cannot upload, sync, edit, delete, reset, or reindex its source data.` | Notice | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1360-1367` | Connected knowledge base page (the upstream product name is kept under the licence rule) | None | Section 5.26 |
| `Admin-managed service account`, `Not configured`, `Ask this knowledge source a test question` | Labels | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1349`, `:1355`, `:1375` | Connected knowledge base page | n/a | n/a |
| `Please fill in all fields.` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase/AddTextContentModal.svelte:37-43` | **Add text content** with a blank title or text | Fill both | None |
| `Permission denied when accessing microphone: {error}` / `Permission denied when accessing microphone` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase/AddTextContentModal.svelte:101-122` | The browser refused the microphone | Allow the microphone in the browser | None |

### 10.5 Directories, Upload Directory and Sync

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Name is required` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase/NewDirectoryModal.svelte:19-23` | **New Directory** with a blank name | Type a name | None |
| `Directory created.` / `Directory renamed.` / `Directory deleted.` / `Directory moved.` / `File moved.` | Success | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:822-824`, `:836-838`, `:860-862`, `:893-895`, `:878-880` | The action succeeded | None | None |
| `Delete directory?`, `Are you sure you want to delete this directory?`, `Delete all contents inside this directory` | Confirmation | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1708-1729` | Deleting a directory; the box starts ticked | Untick to keep the files | Section 11.12 |
| `Directory selection was cancelled` | Info | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:493-496` | The folder picker was closed | None | None |
| `Error accessing directory: {message}` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:497` | The browser could not read the folder or a file in it | Check permissions on the computer, retry | The browser in use |
| `Computing checksums ({count} files)`, `Comparing with knowledge base...`, `Uploading {current}/{total}: {file}`, `Removing {count} stale files...` | Progress | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:629-633`, `:670`, `:673`, `:714-716`, `:721`, `:740`, `:1545-1556` | Upload directory or sync in progress | Keep the page open | None |
| `Failed to compare files.` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:685-688`, `:728-731` | The comparison request returned nothing | Retry | Server availability |
| `Upload failed for {failed} of {total} files.` | Error | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:654-660` | Some files in a folder upload or sync failed (reasons only in the browser console) | Retry the failed files singly to see each reason | Sections 11.7, 11.9 |
| `File uploaded successfully` | Success | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:696-698` | Every file in a folder upload succeeded | None | None |
| `Sync complete: {added} added, {modified} modified, {deleted} deleted, {unmodified} unmodified` | Success | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:758-771` | Sync finished with no failures | Check the deleted count | Section 11.8 |
| `{count} files selected. Only new and modified files will be uploaded. Deleted files will be removed. The folder structure will be mirrored. Continue?` | Confirmation | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1158-1170` | **Sync directory** after choosing a folder | Confirm or cancel | Section 5.11 |
| `Sync a local directory with this knowledge base. Only new and modified files will be uploaded. The directory structure will be mirrored.` | Tooltip | `src/lib/components/workspace/Knowledge/KnowledgeBase/AddContentMenu.svelte:94-99` | Hovering **Sync directory** | n/a | n/a |

### 10.6 Chat Composer, Model Editor and In-Chat Status

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Searching Knowledge for "{searchQuery}"` | Status | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:40-50`; `backend/open_webui/utils/middleware.py:2609-2618` | Model knowledge in legacy function calling | Wait | Section 5.21 |
| `Querying` | Status | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:78-100`; `backend/open_webui/utils/middleware.py:2093-2103` | Search phrases generated for attached knowledge | Wait | None |
| `No sources found` / `Retrieved 1 source` / `Retrieved {count} sources` | Status | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:104-123`; `backend/open_webui/utils/middleware.py:2155-2165` | Retrieval finished; `No sources found` also when retrieval failed or the knowledge base was skipped for lack of access | Rephrase, or check access | Section 11.14 |
| `No knowledge bases found.` | Empty state | `src/lib/components/chat/MessageInput/InputMenu/Knowledge.svelte:196-199` | **Attach Knowledge** finds nothing readable | None | Section 11.2 |
| `No files in this knowledge base.` | Empty state | `src/lib/components/chat/MessageInput/InputMenu/Knowledge.svelte:271-274` | **Show Files** on an empty knowledge base | None | None |
| `Oops! Looks like the URL is invalid. Please double-check and try again.` | Error | `src/lib/components/chat/MessageInput/Commands/Knowledge.svelte:210-219`, `:238-247` | Invalid address after `#` | Fix the address | None |
| `You do not have permission to upload files.` / `Model(s) do not support file upload` | Tooltip; error in the model editor | `src/lib/components/chat/MessageInput/InputMenu.svelte:333-339`; `src/lib/components/workspace/Models/Knowledge.svelte:38-41` | No Allow File Upload, or a selected model without File Upload | Ask an admin; choose another model | Section 11.11 |
| `You do not have permission to upload web content.` | Error | `src/lib/components/chat/Chat.svelte:1790-1794` | Web address attached without `chat.web_upload` | Ask an admin | Permissions |
| `Inject the entire content as context for comprehensive processing, this is recommended for complex queries.` / `Default to segmented retrieval for focused and relevant content extraction, this is recommended for most cases.` | Tooltip | `src/lib/components/common/FileItemModal.svelte:346-358` | Hovering the full-document switch | n/a | n/a |
| `To attach knowledge base here, add them to the "Knowledge" workspace first.` | Hint | `src/lib/components/workspace/Models/Knowledge.svelte:298-300` | Model editor **Knowledge** section | n/a | n/a |
| `No knowledge found` | Empty state | `src/lib/components/workspace/Models/Knowledge/KnowledgeSelector.svelte:139-142` | **Select Knowledge** finds nothing readable | None | None |
| `Unsupported file type.` / `File size should not exceed {maxSize} MB.` | Error | `src/lib/components/workspace/Models/Knowledge.svelte:121-141` | Model editor **Upload** with a refused file | Use another file | `workspace-models-and-model-access.md`, 10.2 |

### 10.7 Admin › Settings › Documents

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Reindex Knowledge and Memory Vectors` / `Rebuild vectors for existing knowledge files, knowledge search, and memories.` | Label and description | `src/lib/components/admin/Settings/Documents.svelte:1576-1591`; `src/lib/i18n/locales/en-US/translation.json:2318-2319` | Danger Zone row | n/a | n/a |
| `Reindex Embedding Data` / `Rebuild knowledge file, knowledge search, and memory vectors using the current embedding model.` | Confirmation | `src/lib/components/admin/Settings/Documents.svelte:382-388` | **Reindex** | Confirm or cancel | Section 5.24 |
| `Success` | Success | `src/lib/components/admin/Settings/Documents.svelte:407-415` | All three reindex steps returned | None | Server log for skipped files |
| `After changing the embedding model, reindex knowledge, knowledge search, and memory vectors for changes to take effect.` | Hint | `src/lib/components/admin/Settings/Documents.svelte:1167-1171` | Under the embedding model setting | n/a | n/a |
| `Reset Vector Storage/Knowledge` / `Clear vector storage and knowledge indexing data.` | Label and description | `src/lib/components/admin/Settings/Documents.svelte:1562-1575`; `src/lib/i18n/locales/en-US/translation.json:2330-2331` | Danger Zone row | n/a | Section 5.25 |
| `Success` | Success | `src/lib/components/admin/Settings/Documents.svelte:368-380` | Shown at once after confirming the reset, before the server answers (read from code) | Verify the knowledge list | Section 5.25 |

### 10.8 What the Model's Knowledge Tools Return

These appear inside a reply's tool-call details (hidden for people who turn on **Hide Processing
Details**, section 12). They are messages to the model, not errors the person must act on.

| Message | Tool | Source | Meaning |
|---|---|---|---|
| `No knowledge bases found.` | `kb_exec` `ls`, `tree` | `backend/open_webui/tools/knowledge_fs.py:564-565`, `:1034-1035` | Nothing attached or readable |
| `File not found: {ref}` | `kb_exec` file commands | `backend/open_webui/tools/knowledge_fs.py:645-647`, `:674-676`, `:703-705`, `:909-911`, `:930-932`, `:1007-1009` | Not reachable by this person and model |
| `Ambiguous filename "{ref}". Use full path to disambiguate:` | `kb_exec` | `backend/open_webui/tools/knowledge_fs.py:512-516` | Several reachable files share the name |
| `Too many files ({count}). Scope your search: grep "{pattern}" docs/ or grep "{pattern}" *.py` | `kb_exec` `grep` | `backend/open_webui/tools/knowledge_fs.py:802-803` | More than `KB_EXEC_MAX_GREP_FILES` files in scope |
| `No matches for "{pattern}" across {count} files` (also `No matches for "{pattern}"`, `No matches for "{pattern}" in {filename}`) | `kb_exec` `grep` | `backend/open_webui/tools/knowledge_fs.py:757-758`, `:775-778`, `:835`, `:842`, `:845-846` | No match |
| `No files found under "{dir_scope}/"` / `No files matching "{pattern}"{scope_str}` / `Directory not found: {dir_path}` | `kb_exec` | `backend/open_webui/tools/knowledge_fs.py:587`, `:793-797`, `:883-885`, `:1052` | Path or pattern matched nothing |
| `Search patterns over {MAX_SEARCH_PATTERN_LENGTH} characters are not supported` / `Invalid or unsupported regex (RE2 syntax): {e}` / `Search exceeded {MATCH_BUDGET_SECONDS}s, narrow the pattern` | `kb_exec`, `grep_knowledge_files` | `backend/open_webui/tools/knowledge_fs.py:92-93`, `:106-107`, `:120-121` | Pattern refused or too slow |
| `Unknown command: {cmd_name}. Available: {COMMAND_MAP}` (the ten command names) | `kb_exec` | `backend/open_webui/tools/knowledge_fs.py:1120-1122` | Unsupported command |
| `[output truncated at {KB_EXEC_MAX_OUTPUT_CHARS} chars — narrow the command with a path, glob, head/tail/sed or grep]` | `kb_exec` | `backend/open_webui/tools/knowledge_fs.py:1195-1199` | Output over the limit |
| `Usage: kb_exec("<command>"). Run kb_exec("ls") to start.` / `Could not parse command. Run kb_exec("ls") to start.` / `Error: {e}` / `Error: User context not available` | `kb_exec` | `backend/open_webui/tools/knowledge_fs.py:1181-1203` | Empty, malformed or failed command |
| `Knowledge base {knowledge_id} is not attached to this model` / `Access denied to knowledge base {knowledge_id}` | `search_knowledge_files` | `backend/open_webui/tools/builtin.py:2213-2216`, `:2278-2291` | Out-of-scope or unreadable knowledge base |
| `Pattern is required` / `No accessible files found` / `File not found` | `grep_knowledge_files` | `backend/open_webui/tools/builtin.py:2657-2658`, `:2674-2676`, `:2740-2741` | Nothing to search |
| `Access denied` / `File not found` | `view_knowledge_file` | `backend/open_webui/tools/builtin.py:2915-2917`, `:2940-2942` | The file is in no knowledge base the person can read |
| `Embedding function not configured` | `query_knowledge_files`, `query_knowledge_bases` | `backend/open_webui/tools/builtin.py:3206-3208`, `:3402-3404` | Embeddings unavailable on the server; escalate |

### 10.9 Server Log Lines

| Message | Severity | Source | Meaning |
|---|---|---|---|
| `Failed to embed knowledge base {knowledge_base_id}: {e}` | Log (error) | `backend/open_webui/routers/knowledge.py:116-118` | Knowledge search index not updated; `query_knowledge_bases` will miss it until a metadata reindex |
| `Starting reindexing for %s knowledge bases (%s files)` / `Reindexing knowledge base %s/%s file %s/%s%s: %s` / `Reindexing completed in %ss.` | Log (info) | `backend/open_webui/routers/knowledge.py:396`, `:415-423`, `:453` | Reindex progress |
| `Error processing file {file.filename} (ID: {file.id}): {str(e)}` / `Failed to process {len(failed_files)} files` / `File ID: {failed["file_id"]}, Error: {failed["error"]}` | Log (error, warning) | `backend/open_webui/routers/knowledge.py:438-441`, `:448-451` | Files skipped by the reindex |
| `Error deleting collection {knowledge_base.id}: {str(e)}` / `Error processing knowledge base {knowledge_base.id}: {str(e)}` | Log (error) | `backend/open_webui/routers/knowledge.py:403-405`, `:443-446` | A whole knowledge base skipped by the reindex |
| `Reindexing embeddings for %s knowledge bases` / `Embedding reindex complete: %s/%s` | Log (info) | `backend/open_webui/routers/knowledge.py:482`, `:493` | Metadata reindex |
| `Deleting knowledge base: %s (name: %s)` / `Updating model %s to remove knowledge base %s` | Log (info) | `backend/open_webui/routers/knowledge.py:1732`, `:1747` | Deletion and model clean-up |
| `This was most likely caused by bypassing embedding processing` | Log (debug) | `backend/open_webui/routers/knowledge.py:70`, `:1669`, `:2356` | Chunk deletion found no collection |
| `Refusing to auto-link file {file_item.id} to knowledge {knowledge_id}: user {user.id} lacks write access` | Log (warning) | `backend/open_webui/routers/files.py:221-225` | Upload tagged for a knowledge base the uploader cannot write; the file is kept but not linked |
| `Linked file %s to knowledge %s` / `Failed to link file {file_item.id} to knowledge {knowledge_id}: {e}` / `Error processing file: {file_item.id}` | Log | `backend/open_webui/routers/files.py:254-260` | Background linking result |
| `Document with hash %s already exists` | Log (info) | `backend/open_webui/routers/retrieval.py:1752` | Duplicate content refused |
| `kb_exec error: {e}` | Log (error) | `backend/open_webui/tools/knowledge_fs.py:1201-1202` | A `kb_exec` command failed |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it explains, gathers identifiers and escalates; it does not change content,
sharing, permissions or settings. Identify a knowledge base by its name and id (shown beside the
description on wide screens, section 5.3) and a file by its name; do not ask for or copy document
contents. Sections 3 and 5 hold the detail behind each cause.

### 11.1 "I don't see Knowledge in the Workspace" or "I can't create a knowledge base"

**Symptom.** No **Knowledge** tab under Workspace; opening `/workspace/knowledge` lands on the home page;
or **Create Knowledge** answers `401 Unauthorized`.

**Likely causes, in order.**
1. The person lacks **Knowledge Access** (`workspace.knowledge`), which is off in code and must come
   from the defaults or a group (`backend/open_webui/config.py:1737-1739`;
   `src/routes/(app)/workspace/+layout.svelte:84-88`, `:168`; `backend/open_webui/routers/knowledge.py:328-334`).
2. The permission was granted after their page loaded; menus reflect permissions loaded at sign-in.
3. The account is `pending`.

**Diagnostic steps.** Ask whether other Workspace sections appear, and whether reloading the page
changes anything. Ask which group they expect to grant access.

**Resolution.** Explain that admins grant Knowledge Access. Knowledge bases already shared with them
can still be used in chat by typing `#` (section 5.19).

**Escalation.** Email address, the group they expect to be in, a screenshot of the Workspace page.

### 11.2 "My colleague can't see the knowledge base I shared" or "I can't find a knowledge base shared with me"

**Symptom.** The knowledge base is missing from the recipient's list, from `#` and from **Attach
Knowledge**, or the list shows `No knowledge found`.

**Likely causes, in order.**
1. The share was not kept: the server drops entries the sharer may not make (people without **Allow
   Sharing With Users**, groups without **Allow Sharing With Groups**, Public without **Knowledge Public
   Sharing**), and the open dialog keeps showing them until reopened (section 5.4;
   `backend/open_webui/utils/access_control/__init__.py:223-301`).
2. The recipient is not in the group it was shared with, or single sign-on group sync removed them
   (`users-groups-roles-and-permissions.md`, section 4).
3. The recipient lacks Knowledge Access, so the Workspace page is unavailable to them even though `#`
   works (section 3.1).
4. A filter is set: **Created by you**, or **Connected** under the source filter
   (`src/lib/components/workspace/Knowledge.svelte:271-274`, `:355-377`).
5. The knowledge base was deleted.

**Diagnostic steps.** Ask the owner to reopen **Access** and send a screenshot of what is listed. Ask
the recipient to type `#` followed by part of the name, and to set the view filter to **All** and the
source filter to **All Sources**.

**Resolution.** If the owner can share, guide them to add the person or group again and reopen the
dialog to confirm it stayed. If the entry keeps disappearing, the owner lacks a sharing permission:
escalate.

**Escalation.** Knowledge base name and id, owner's and recipient's emails, intended group, the Access
dialog screenshot.

### 11.3 "The knowledge base says Read Only" or "I can't upload to it"

**Symptom.** `Read Only` beside the name; no **Access** button and no **+** menu; dropping files shows
`You do not have permission to upload files to this knowledge base.`

**Likely causes, in order.**
1. It is shared with the person as **Read** (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1279-1291`).
2. It is a connected knowledge base (badge with the provider name or `Connected`), which is read-only
   for everyone (section 5.26).
3. The person is an admin and `BYPASS_ADMIN_ACCESS_CONTROL` is off (section 3.4).

**Diagnostic steps.** Ask for a screenshot of the list row (badges) and the owner's name.

**Resolution.** Ask the owner to give Write access, or to upload the files themselves. For a connected
knowledge base, content is managed in the external system.

**Escalation.** Only if the owner reports giving Write and it still shows `Read Only`: name, id, both
emails.

### 11.4 "My file upload failed"

**Symptom.** A yellow warning or red pop-up appears after uploading and the file does not stay in the
list.

**Likely causes, in order (match the text in section 10).**
1. `Duplicate content detected. Please provide unique content to proceed.`: the same text is already in
   this knowledge base (section 11.7).
2. `The content provided is empty. Please ensure that there is text or data present before proceeding.`:
   no text could be extracted, typically a scanned PDF without a text layer, a video, or an empty
   document (`backend/open_webui/routers/retrieval.py:2014-2015`; `backend/open_webui/routers/files.py:168-188`).
3. `File type {content_type} is not supported for processing`: an image while media extraction is off.
4. `[ERROR: File type {file_extension} is not allowed]` or a size message: outside the site's upload
   rules (section 7.1).
5. `Pandoc is not installed on the server. Please contact your administrator for assistance.`,
   `Error saving document to vector database`, or an embedding or extraction-engine error: a server
   problem.

**Diagnostic steps.** Get the exact text (screenshot), the file name, type and size. Ask whether other
files upload to the same knowledge base.

**Resolution.** For causes 1 to 4, explain the rule (for scanned documents, a version with selectable
text is needed). For cause 5, escalate.

**Escalation.** Knowledge base id, file name, type and size, the exact message, the time.

### 11.5 "It said the file was added, but it isn't in the knowledge base"

**Symptom.** `File added successfully.` (or no message) but the file is not listed.

**Likely causes, in order.**
1. It is in another directory: uploads go into the directory that was open, and search covers only the
   level being viewed (sections 5.5, 5.12).
2. It is still processing; after a reload it shows with a spinner (section 5.6).
3. Processing failed after the success message, or after the person left the page (section 5.6; read
   from code). The file is then in their own file list with a failed status.
4. Someone with write access removed it, or a **Sync directory** removed it (section 5.11).
5. The person lost write access before processing finished, so the link was refused (log line
   `Refusing to auto-link file …`, `backend/open_webui/routers/files.py:206-226`).

**Diagnostic steps.** Ask them to open each directory, clear the search, and check their own file list
for the file and its status (`files-uploads-and-storage.md`). Note the upload time.

**Resolution.** Upload the file again; if the retry says the content is a duplicate, the file is
already in the knowledge base.

**Escalation.** Knowledge base id, file name, upload time, so the maintainer can search the server log
for `Failed to link file` or `Refusing to auto-link file`.

### 11.6 "A file has been processing for ages"

**Symptom.** A file row keeps its spinner, including after reloading.

**Likely causes, in order.**
1. A large file, or a slow extraction engine or embedding service; processing finishes in the
   background (section 5.6).
2. The server restarted during processing; read from code, nothing resumes or fails such a file, so it
   stays pending and the page keeps polling every 5 seconds (section 8;
   `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:227-239`).
3. The embedding or extraction service is down; other uploads then also stall or fail.

**Diagnostic steps.** Ask for the file size and type, when it was uploaded, and whether other people's
uploads work.

**Resolution.** Ask the person to wait. A pending file cannot be removed from the knowledge base page
(it is not linked yet, so removal answers `We could not find what you're looking for :/`); if it is
still pending after an hour, escalate.

**Escalation.** Knowledge base id, file name, size, upload time, and whether others are affected.

### 11.7 "It says 'Duplicate content detected'"

**Symptom.** `Duplicate content detected. Please provide unique content to proceed.` when adding a
file.

**Likely causes, in order.**
1. The same file, or a copy with another name, is already in this knowledge base; the check compares
   the extracted text, not the file name (`backend/open_webui/routers/retrieval.py:1734-1753`, `:2069`).
2. A folder was uploaded again with **Upload directory** (section 5.10).

**Diagnostic steps.** Ask them to search the knowledge base for the file (with **File content** if the
name differs).

**Resolution.** Nothing is wrong: the content is already there. To replace a document, remove the old
copy first, or keep the folder in step with **Sync directory**.

**Escalation.** Not normally needed.

### 11.8 "Sync directory deleted my files"

**Symptom.** After a sync, files or directories are gone; the summary showed a `deleted` count.

**Likely causes, in order.**
1. Sync mirrors the chosen folder: anything not under that folder's name, at the same path, is removed,
   including root-level uploads, web pages and text content (section 5.11).
2. The wrong folder, or a sub-folder, was chosen.
3. Files were renamed in MedIT GPT or on the computer, so names no longer matched.

**Diagnostic steps.** Ask which folder they chose, the summary text, and the time.

**Resolution.** Explain how sync works and suggest **Upload files** or **Upload directory** for content
that is not in the folder. Files the person owned were deleted (with retention off) and must be
uploaded again; files owned by others were only unlinked.

**Escalation.** If recovery is needed: knowledge base id, time of the sync, folder name, summary text.

### 11.9 "Uploading the folder again failed for almost every file"

**Symptom.** `Upload failed for {failed} of {total} files.` after **Upload directory** or a folder drop.

**Likely causes, in order.**
1. The files are already in the knowledge base: **Upload directory** does not skip them and each fails
   as duplicate content (section 5.10).
2. Some files have no extractable text or a refused type or size (section 11.4).

**Diagnostic steps.** Ask them to upload one failing file on its own to see its message (the summary
does not list reasons).

**Resolution.** Use **Sync directory** to bring an existing knowledge base up to date.

**Escalation.** Only for server errors seen on single uploads.

### 11.10 "I removed a file from the knowledge base and now it's gone from my model or chat"

**Symptom.** After **…** › **Delete** on a file, a custom model or chat that used that file no longer
has it.

**Likely causes, in order.**
1. Removing a file the person owns deletes the file itself while `ENABLE_KNOWLEDGE_FILE_RETENTION` is off
   (the default), wherever else it was used (section 5.13; read from code).

**Diagnostic steps.** Confirm who owned the file and where else it was attached.

**Resolution.** Upload the file again (into the knowledge base) and re-attach it where needed.

**Escalation.** If the file must be recovered: file name, knowledge base id, time of removal.

### 11.11 "When I pick a knowledge base with # it disappears from the message box"

**Symptom.** The `Collection` chip vanishes straight after picking, or **Attach Knowledge** is greyed
out with `You do not have permission to upload files.` or `Model(s) do not support file upload`.

**Likely causes, in order.**
1. The person lacks **Allow File Upload** (`chat.file_upload`); read from code, the composer then clears
   every attachment (section 5.19).
2. A selected model has its **File Upload** capability off (same effect).

**Diagnostic steps.** Ask which model is selected and whether **+** › **Upload Files** is also greyed out.
Try with another model if one is available.

**Resolution.** Choose a model that accepts files; otherwise escalate for the permission.

**Escalation.** Email, model name, screenshot of the greyed menu.

### 11.12 "Deleting a directory deleted my files"

**Symptom.** After deleting a directory, its files are gone, not moved.

**Likely causes, in order.**
1. **Delete all contents inside this directory** is ticked by default (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:137`,
   `:1722-1727`).

**Diagnostic steps.** Ask what the dialog looked like when they confirmed.

**Resolution.** Explain the option for next time (untick to move files up a level). Files the person
owned and that no other knowledge base used were deleted (retention off); others were only unlinked.

**Escalation.** If recovery is needed: knowledge base id, directory name, time.

### 11.13 "The model quoted a knowledge base I didn't attach"

**Symptom.** A reply cites a document from a knowledge base the person did not mention.

**Likely causes, in order.**
1. Nothing was attached, so the model's knowledge tools searched every knowledge base the person can
   read, including ones shared with them or Public (section 5.22).
2. The custom model or the chat's folder has knowledge attached (sections 5.18, 5.20).
3. The knowledge base was attached earlier in the same chat and is still sent (section 5.19).

**Diagnostic steps.** Ask for the model name, whether the chat is in a folder, and a screenshot of the
tool-call entry (if **Hide Processing Details** is off).

**Resolution.** Attach the intended knowledge base with `#` (or use a custom model with it attached) so
the tools are limited to it. A custom model's owner can switch off its **Knowledge Base** tool group.

**Escalation.** Not normally needed; if the source should not be readable by the person, escalate with
the knowledge base name and id (an access question).

### 11.14 "The model doesn't use my knowledge base" or "It says No sources found"

**Symptom.** Answers ignore the documents; status `No sources found`, or no knowledge status at all.

**Likely causes, in order.**
1. The attachment was cleared before sending (section 11.11), or the knowledge base was not attached.
2. With native function calling, model-attached knowledge is used only if the model calls its tools,
   and not at all when **Builtin Tools** or the **Knowledge Base** group is off (section 5.21).
3. The model's **File Context** capability is off, so `#` attachments are not retrieved.
4. The person cannot read the knowledge base (for example a shared model whose knowledge base is not
   shared); it is skipped without a message (section 3.6).
5. Retrieval found nothing relevant (**Top K**, **Relevance Threshold**), or the files failed processing.
6. The knowledge base was deleted or emptied.

**Diagnostic steps.** Ask which status lines appear, whether a `Collection` chip was visible when they
sent the message, which model they used, and whether a colleague gets the same result. Note that
**Hide Processing Details** hides tool calls (section 12).

**Resolution.** Suggest attaching with `#` and checking the chip; asking the model explicitly to search
the knowledge base; or, for a small knowledge base, switching the chip to **Using Entire Document**. See
also `chat-completion-pipeline-and-generation-tasks.md`, section 11.13, and
`workspace-models-and-model-access.md`, section 11.7.

**Escalation.** Model name, knowledge base name and id, time, screenshot of the reply and its status
lines (not the document text).

### 11.15 "I deleted (or reset) a knowledge base by mistake. Can it be restored?"

**Symptom.** A knowledge base is gone, or empty after **Reset**.

**Likely causes, in order.**
1. **Delete** removes the knowledge base, its sharing, its index and its model attachments; the files
   remain (section 5.15).
2. **Reset** removed every file link and directory and deleted the files the person owned (section 5.14).
3. An admin used **Reset Vector Storage/Knowledge**, which deletes every knowledge base (section 5.25).

**Diagnostic steps.** Ask what was pressed, the knowledge base name, and the time.

**Resolution.** There is no undo or trash. After a delete, the files are still in the owner's file list
and can be uploaded into a new knowledge base. Anything else needs a backup restore (TO BE CONFIRMED).

**Escalation.** Promptly: knowledge base name and id (from a chat chip, a model, or the event log), owner
email, time.

### 11.16 "I edited a file's text and the change didn't stick"

**Symptom.** `File content updated successfully.` appears, but reopening the file shows the old text.

**Likely causes, in order.**
1. The editor is a collaborator, not the file's owner: read from code, the server accepts the edit but
   re-processing runs only for the owner, so the stored text may stay unchanged
   (`backend/open_webui/routers/files.py:718-786`; `backend/open_webui/routers/retrieval.py:1938-1941`;
   section 14.4).
2. The text exceeded **Max Upload Size** (a size message appears instead).

If the save shows `We could not find what you're looking for :/` instead, the person cannot write that
file at all, for example the knowledge base's owner editing a file a collaborator uploaded (section 3.5).

**Diagnostic steps.** Ask who uploaded the file (`By {name}`) and who edited it.

**Resolution.** Ask the file's owner to make the edit. Explain that edits change only the searchable
text, not the original file.

**Escalation.** If the owner's own edit does not stick: knowledge base id, file name, time.

### 11.17 "Search doesn't find a file I know is there" or "The file count looks wrong"

**Symptom.** **Search Collection** returns `No content found`, or the number beside the name differs
from the list page.

**Likely causes, in order.**
1. Search covers only the directory being viewed, not its sub-directories (section 5.12).
2. **File content** is not ticked, and the word is in the text rather than the name.
3. The count beside the name is for the current level and search; the list page counts the whole
   knowledge base.

**Diagnostic steps.** Ask where they are in the breadcrumbs and whether **File content** is ticked.

**Resolution.** Open the likely directory first, or tick **File content**. Typing `#` and part of the
file name in a chat searches file names across all readable knowledge bases.

**Escalation.** Not normally needed.

### 11.18 "There's no Export option" or "The export only contains text files"

**Symptom.** The row menu has only **Delete**, or the ZIP holds `.txt` files rather than originals.

**Likely causes, in order.**
1. Export is offered only to admins (section 5.16).
2. Export is designed to contain extracted text, flattened, without directories.
3. Connected knowledge bases cannot be exported (`External knowledge bases are read-only.`).

**Diagnostic steps.** Ask what they need the export for.

**Resolution.** Originals can be downloaded one at a time (**…** › **Download** with write access, or the
file name link in the drawer). Bulk exports go through an admin.

**Escalation.** Requests for a bulk export, with the knowledge base id and the reason; the export
contains all document text.

### 11.19 "Testing a connected knowledge base gives a permission error"

**Symptom.** On a connected knowledge base, **Test** shows `You do not have permission to access this
resource. Please contact your administrator for assistance.`

**Likely causes, in order.**
1. The test uses an admin-only endpoint (section 5.26).

**Diagnostic steps.** Confirm the person is not an admin and that the knowledge base shows `Connected`.

**Resolution.** Explain that only admins can run the test; using the knowledge base in chat works for
anyone it is shared with.

**Escalation.** If chat retrieval from it also fails: knowledge base name and id, time.

### 11.20 "It won't let me create or rename a directory"

**Symptom.** `Failed to create directory. A directory with this name may already exist at this level.`
or `Failed to update directory. This may be caused by a naming conflict or circular move.`

**Likely causes, in order.**
1. A directory with that name already exists at that level.
2. A move into the directory's own sub-directory.

**Diagnostic steps.** Ask for the name and where they are in the breadcrumbs.

**Resolution.** Choose another name or target.

**Escalation.** Only if the name is free and it still fails: knowledge base id, directory names, time.

### 11.21 Admin: "We reindexed, but some documents are no longer found"

**Symptom.** After **Reindex**, some files are listed but no longer returned by search, or `Success` did
not appear.

**Likely causes, in order.**
1. Files with no stored extracted text failed during the reindex and were left without chunks (section
   5.24; read from code).
2. The request was cut off (for example by a proxy timeout) before all knowledge bases were processed.
3. The embedding service failed part-way.

**Diagnostic steps.** Ask for the time of the reindex and whether `Success` appeared.

**Resolution.** Escalate; the server log lists skipped files (`Error processing file …`).

**Escalation.** Time of the reindex, the embedding model in use, and any error text shown.

## 12. Local Customisations

Checked with read-only `git diff main...uoft` (fork commits) and `git diff` (uncommitted working tree)
over every file in section 13.1, plus `src/lib/components/chat/MessageInput.svelte`,
`src/lib/components/common/ToolCallDisplay.svelte`, `src/lib/components/chat/Messages/ResponseMessage.svelte`,
`src/lib/components/chat/Messages/ContentRenderer.svelte`,
`src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte` and
`src/lib/i18n/locales/en-US/translation.json`.

- **No file in this area's scope differs from upstream Open WebUI v0.11.4**, in the fork commits or in
  the uncommitted working tree. Knowledge bases, directories, sync, sharing, export, the knowledge tools
  and `kb_exec` behave as upstream.
- **Hide Processing Details** (fork commit `aeed1832c`; `backend/open_webui/models/users.py:99-100`). A
  person who turns on this Interface setting (`Hide Processing Details`, described as `Show "Thinking..."
  instead of status updates, tool calls, reasoning, and code analysis while a response is generated, and
  keep them hidden afterwards. Tool approval requests and images or embeds from tools still appear.`)
  no longer sees the knowledge tool calls (`query_knowledge_files`, `view_knowledge_file` and the rest)
  or the retrieval status lines (`Searching Knowledge for "{searchQuery}"`, `Querying`, `Retrieved
  {count} sources`, `No sources found`) (`src/lib/components/common/ToolCallDisplay.svelte:145`, `:181`,
  `:199`; `src/lib/components/chat/Messages/ResponseMessage.svelte:197-202`;
  `src/lib/i18n/locales/en-US/translation.json:2923-2924`). When someone reports that the model "never
  looks at" a knowledge base, ask whether this setting is on before assuming retrieval failed. In the
  working tree `ToolCallDisplay.svelte` reads the setting itself rather than receiving it from its parent;
  the effect is the same.
- **Inline Citations** (same commit). With it off, citation markers from knowledge sources are removed
  from the reply text, but the sources stay listed below the reply
  (`src/lib/components/chat/Messages/ContentRenderer.svelte:128-130`;
  `src/lib/i18n/locales/en-US/translation.json:2935-2936`).
- **Branding.** The Workspace › Knowledge browser tab reads `Knowledge / MedIT GPT` with the fork's
  default name (`src/lib/components/workspace/Knowledge.svelte:287-294`; `backend/open_webui/env.py:951`).
  The connected-source notice keeps the upstream product name `Open WebUI`, which is covered by the
  licence comment beside it (`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1360-1367`;
  `CLAUDE.md`, Conventions).
- The other uncommitted changes (chat message rendering, `structuredOutput.ts`, `src/lib/i18n/index.ts`)
  do not affect anything described here; the only change in `StatusItem.svelte` adds a type comment.

## 13. Source File Index

### 13.1 Files in Scope

| File | What it does in this area |
|---|---|
| `backend/open_webui/routers/knowledge.py` | Knowledge API: list and search, file search, create, reindex (files and metadata), connected sources, read, update, access, pending files, file listing, add, re-index, remove, delete, reset, sync diff and cleanup, batch add, export, directories, move |
| `backend/open_webui/models/knowledge.py` | Tables `knowledge`, `knowledge_file`, `knowledge_directory`; list search with access filter and file counts; file search across knowledge bases; directory tree, breadcrumbs, rename, move with cycle check, delete with move or delete of contents |
| `backend/open_webui/tools/knowledge_fs.py` | `kb_exec`: command parsing, pipes, directory tree, file resolution and access, `ls`, `tree`, `cat`, `head`, `tail`, `sed`, `grep`, `find`, `wc`, `stat`, RE2 matching budget, output limit |
| `src/lib/components/workspace/Knowledge.svelte` | Workspace › Knowledge list: search, view and source filters, sorting, rows and badges, export and delete, legacy-document guard |
| `src/lib/components/workspace/Knowledge/CreateKnowledgeBase.svelte` | Create dialog: name, description, access, validation |
| `src/lib/components/workspace/Knowledge/ItemMenu.svelte` | Row menu with **Export** (admins) and **Delete** |
| `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte` | Knowledge base page: load, name and description auto-save, access dialog, uploads, web pages, text, folder upload and sync, pending files, directories, moves, remove, rename, drawer edit, reset, connected-source view |
| `src/lib/components/workspace/Knowledge/KnowledgeBase/Files.svelte` | File and directory list rows, rename, download, delete, drag to move |
| `src/lib/components/workspace/Knowledge/KnowledgeBase/AddContentMenu.svelte` | The **+** menu |
| `src/lib/components/workspace/Knowledge/KnowledgeBase/DirectoryRow.svelte` | Directory row: open, rename, delete, drop targets |
| `src/lib/components/workspace/Knowledge/KnowledgeBase/NewDirectoryModal.svelte` | **New Directory** dialog |
| `src/lib/components/workspace/Knowledge/KnowledgeBase/AddTextContentModal.svelte` | **Add text content** editor with voice input |
| `src/lib/components/workspace/Knowledge/KnowledgeBase/KnowledgeBreadcrumbs.svelte` | Breadcrumbs and drop targets |
| `src/routes/(app)/workspace/knowledge/+page.svelte`, `create/+page.svelte`, `[id]/+page.svelte` | Routes for the list, the create dialog and one knowledge base |
| `src/lib/apis/knowledge/index.ts` | Front-end calls for every knowledge endpoint |
| `backend/open_webui/config.py` (knowledge settings) | Permission defaults, retention, content-search limit, retrieval settings, admin bypass |

### 13.2 Files Consulted Outside Scope

| File | Why |
|---|---|
| `backend/open_webui/routers/files.py` | Upload with knowledge metadata, background processing and auto-link, status stream, rename, content edit, delete |
| `backend/open_webui/models/files.py` | Pending files query, rename, delete |
| `backend/open_webui/routers/retrieval.py` | `process_file` paths, duplicate check, failure handling, process URL and web, vector store reset |
| `backend/open_webui/retrieval/utils.py` | How attached knowledge bases are retrieved in chat; collection access filter |
| `backend/open_webui/tools/builtin.py` | Knowledge tools |
| `backend/open_webui/utils/tools.py` | Which knowledge tools are offered; attached knowledge |
| `backend/open_webui/utils/middleware.py` | Legacy model knowledge, attached-knowledge list, file context, retrieval statuses |
| `backend/open_webui/utils/access_control/__init__.py`, `backend/open_webui/utils/access_control/files.py`, `backend/open_webui/models/access_grants.py` | Grant filtering on save; file access through knowledge bases; list filter |
| `backend/open_webui/routers/models.py`, `backend/open_webui/models/models.py` | Model knowledge field and save checks |
| `backend/open_webui/events.py`, `backend/open_webui/utils/notifications.py` | Knowledge events and notification delivery |
| `backend/open_webui/env.py`, `backend/open_webui/constants.py`, `backend/open_webui/internal/db.py`, `backend/open_webui/models/config.py`, `backend/open_webui/main.py` | Environment limits, message texts, SQLite pragmas, settings storage, router mount and config sent to the browser |
| `backend/open_webui/migrations/versions/6a39f3d8e55c_add_knowledge_table.py`, `3e0e00844bb0_add_knowledge_file_table.py`, `3c9b0ca343fd_add_knowledge_directory_table.py`, `81cc2ce44d79_update_channel_file_and_knowledge_table.py` | Schema history |
| `src/lib/components/chat/MessageInput.svelte`, `src/lib/components/chat/MessageInput/CommandSuggestionList.svelte`, `src/lib/components/chat/MessageInput/Commands/Knowledge.svelte`, `src/lib/components/chat/MessageInput/Commands/AtCommands.svelte`, `src/lib/components/chat/MessageInput/InputMenu.svelte`, `src/lib/components/chat/MessageInput/InputMenu/Knowledge.svelte`, `src/lib/components/chat/MessageInput/AttachWebpageModal.svelte` | Attaching knowledge in chat |
| `src/lib/components/chat/Chat.svelte` | Chat-level files carried between messages |
| `src/lib/components/common/FileItem.svelte`, `src/lib/components/common/FileItemModal.svelte`, `src/lib/components/common/ConfirmDialog.svelte`, `src/lib/components/common/AccessButton.svelte`, `src/lib/components/workspace/common/AccessControlModal.svelte`, `src/lib/components/workspace/common/ViewSelector.svelte`, `src/lib/components/AddFilesPlaceholder.svelte` | Chips, the full-document switch, dialogs |
| `src/lib/components/workspace/Models/Knowledge.svelte`, `src/lib/components/workspace/Models/Knowledge/KnowledgeSelector.svelte`, `src/lib/components/workspace/Models/Capabilities.svelte`, `src/lib/components/workspace/Models/BuiltinTools.svelte` | Model knowledge and capabilities |
| `src/lib/components/layout/Sidebar/Folders/FolderModal.svelte` | Folder knowledge |
| `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte`, `src/lib/components/chat/Messages/ResponseMessage.svelte`, `src/lib/components/chat/Messages/ContentRenderer.svelte`, `src/lib/components/common/ToolCallDisplay.svelte` | Status lines, citations, tool calls, fork settings |
| `src/lib/components/admin/Settings/Documents.svelte`, `src/lib/components/admin/Settings/Integrations.svelte`, `src/lib/components/admin/Settings/ExternalKnowledge.svelte`, `src/lib/components/admin/Users/Groups/Permissions.svelte` | Admin reindex and reset, connected sources, permission labels |
| `src/routes/(app)/workspace/+layout.svelte`, `src/routes/(app)/workspace/+page.svelte`, `src/routes/(app)/admin/settings/[tab]/+page.svelte` | Workspace gating and admin deep links |
| `src/lib/apis/files/index.ts`, `src/lib/apis/retrieval/index.ts`, `src/lib/utils/hash.ts` | Upload status wait, process URL, checksums |
| `src/lib/i18n/locales/en-US/translation.json` | English text of dotted keys |

## 14. Open Questions

The code cannot settle the items below. Each heading says who can answer. Every item marked TO BE
CONFIRMED or "read from code" earlier in this document is repeated here.

### 14.1 Live Data (Answered by an Admin or a Read-Only Database Query)

- The live default and group values of `workspace.knowledge`, `sharing.knowledge`,
  `sharing.public_knowledge`, `access_grants.allow_users`, `access_grants.allow_groups`,
  `chat.file_upload` and `chat.web_upload` (sections 3.2, 11.1, 11.11).
- How many knowledge bases exist, how many are Public, how many are owned by accounts that no longer
  exist (`Deleted User`), and the largest file counts (aggregate counts only; sections 3.3, 7.3).
- The live values of `rag.file.max_size`, `rag.file.allowed_extensions`, `rag.top_k`,
  `rag.top_k_reranker`, `rag.relevance_threshold`, `rag.enable_hybrid_search`, `rag.full_context`,
  `rag.bypass_embedding_and_retrieval`, `rag.embedding_engine`, `rag.embedding_model`,
  `rag.content_extraction_engine` and `task.query.retrieval.enable` (section 7.1).
- Whether any connected knowledge bases or `external_knowledge.connections` entries exist (section 5.26).
- How many files uploaded to knowledge bases are stuck in `pending` or `processing`, or ended `failed`
  (counts by status only; sections 5.6, 11.6).
- Which custom models attach knowledge bases that are not shared with the model's audience, and which
  have **Builtin Tools**, the **Knowledge Base** tool group, **File Context** or **File Upload** switched
  off (sections 3.6, 7.4, 11.14).
- Whether `ui.enable_user_webhooks` is on and whether admin event webhooks or Event functions subscribe
  to `knowledge.*` or `retrieval.content.process_failed` events, and where they deliver (section 9).
- On SQLite only: how many `knowledge_file` and `knowledge_directory` rows point at knowledge bases,
  files or parent directories that no longer exist (counts only; sections 5.15, 6.9).

### 14.2 Deployment Environment (Answered by the Platform Maintainer)

- The production host name; URLs here are relative to the site root.
- Whether production uses SQLite or PostgreSQL. This decides whether deleting a knowledge base, a file
  or a directory also removes the dependent rows (section 5.15).
- The vector database (`VECTOR_DB`) and file storage provider (`STORAGE_PROVIDER`) in use.
- The live values of `ENABLE_KNOWLEDGE_FILE_RETENTION`, `BYPASS_ADMIN_ACCESS_CONTROL`, `ENABLE_KB_EXEC`,
  `KB_EXEC_MAX_OUTPUT_CHARS`, `KB_EXEC_MAX_GREP_FILES`, `KNOWLEDGE_GREP_MAX_MATCHES`,
  `VIEW_FILE_DEFAULT_MAX_CHARS`, `VIEW_FILE_MAX_CHARS` and `RAG_FILE_CONTENT_SEARCH_MAX_CHARS` (section 7.2).
- Reverse-proxy and load-balancer timeouts: the admin reindex runs in one request, the upload status
  stream can stay open for up to two hours, and folder uploads make many sequential requests
  (sections 5.6, 5.10, 5.24).
- The number of workers or replicas, and whether storage and the vector store are shared between them
  (section 8).
- Backups: whether the database, vector store and uploads are backed up together, how often, how long
  they are kept, and whether a single deleted or reset knowledge base can be restored (sections 5.14,
  5.15, 11.15).
- Which extraction engine and embedding service are used, whether scanned PDFs are OCR'd, and whether
  Pandoc is installed (sections 5.5, 11.4).
- How long server logs are kept, since failed processing, refused auto-links and reindex skips are
  recorded only there (sections 10.9, 11.5, 11.21).

### 14.3 People and Process (Answered by the Service Owner)

- Who may be granted Knowledge Access and the sharing permissions, and how a person requests them
  (section 11.1).
- What kinds of documents may be placed in knowledge bases at MedIT GPT, and whether Public sharing is
  allowed (section 1.2).
- Who handles restore requests after an accidental delete, reset or sync, and the expected turnaround
  (sections 11.8, 11.15).
- Who may request an admin export, and what approval and handling apply, since exports contain the
  full text of every document (section 5.16).
- Whether connected (external) knowledge sources are used, who owns them, and who supports them
  (section 5.26).
- Support contacts and escalation routes (none exist in the repository; `../tools/ground-truth.md`,
  Contacts).

### 14.4 Product Behaviour (Answered by the Platform Maintainer or Upstream Open WebUI)

Each item was read from code and should be confirmed in a test environment.

1. **Success before failure.** `File added successfully.` may appear when the upload's status stream
   sees the brief `completed` between extraction and the knowledge-base step, so a later duplicate or
   link failure leaves no visible error (section 5.6; `backend/open_webui/routers/files.py:226-254`,
   `:644-668`).
2. **Removing a file deletes it everywhere.** With retention off, removing a file the person owns
   deletes the file even when a model, a chat or another knowledge base also uses it; chunks in other
   knowledge bases are not removed (sections 5.13, 6.9; `backend/open_webui/routers/knowledge.py:1673-1675`).
3. **SQLite cascades.** No `foreign_keys` pragma is set, so on SQLite the cascade rules do not run:
   rows for deleted knowledge bases remain, and sub-directories of a deleted directory remain with a
   missing parent. Read from code, the sync comparison would then treat such a sub-directory's name as
   a root-level path, and `kb_exec tree` could resolve it, although the page no longer shows it
   (sections 5.9, 5.15; `backend/open_webui/models/knowledge.py:1041-1043`;
   `backend/open_webui/routers/knowledge.py:1895-1906`; `backend/open_webui/tools/knowledge_fs.py:226-243`).
4. **Duplicate root directory names** may be accepted because the unique key treats empty parents as
   different (section 5.9).
5. **The composer clears knowledge attachments** whenever file upload is not allowed for the person or
   the selected model (sections 5.19, 11.11; `src/lib/components/chat/MessageInput/InputMenu.svelte:76-78`).
6. **The `Collection` chip dialog lists no files**, because `GET /api/v1/knowledge/{id}` returns none
   (section 5.19).
7. **Collaborator edits may not apply.** A Write collaborator editing the text of a file the knowledge
   base's owner uploaded gets a success message, but re-processing looks the file up as the editor's own
   and fails (section 11.16).
8. **Reindex failures** leave files linked, marked failed and without chunks in the knowledge base
   (section 5.24).
9. **Reset Vector Storage/Knowledge** shows `Success` before the server answers, and leaves knowledge
   references in custom models (section 5.25).
10. **Reset shows nothing on failure** (section 5.14).
11. **Batch-add warnings are dropped** from the API response (section 10.1).
12. **Dropping files onto a connected knowledge base** links them although retrieval does not use them
    (section 5.26).
13. **Interrupted processing is not recovered**, and a pending file cannot be removed from the
    knowledge base page (sections 8, 11.6).
14. **Misleading texts.** Database failures on create and update show `Uh-oh! This file is already
    registered. Please choose another file.` and `Uh-oh! This id is already registered. Please choose
    another id string.` (section 10.1).
15. **Search covers one directory level** inside a knowledge base, and the count beside the name is for
    that level (sections 5.12, 11.17). Whether this is intended is unknown.
16. **Renaming does not update indexed chunks**, so citations may show the old name until re-indexing
    (section 5.12).
17. **Upload directory re-uploads existing files**, which then fail as duplicates (section 5.10).
18. **Admins with the bypass off** see other people's knowledge bases as `Read Only`, yet keep the row
    menu and server-side write access (section 3.4). Whether this is intended is unknown.
19. **Tools search a subset when nothing is attached**: 50 knowledge bases for `query_knowledge_files` and
    `kb_exec`, 200 for `grep_knowledge_files`, ordered by last update, and file activity does not change
    that order (sections 5.1, 5.22).
20. **The knowledge search index can go stale without notice**: a failed embedding at create or rename is only
    logged (section 5.2).
21. **Security-sensitive, without detail:** how sharing restrictions are enforced on the server; the
    retrieval access-control environment switches; storage and protection of connected-source
    credentials. Refer to the platform maintainer and U of T Information Security
    (security.utoronto.ca) (sections 3.6, 5.26, 7.2).

### 14.5 Knowledgebase Consistency (Answered by the Knowledgebase Maintainer)

- Cross-references assume the slugs in `_areas.md` for documents not yet written when this was
  researched: `files-uploads-and-storage.md`, `builtin-native-tools.md`, `web-search-and-web-loading.md`,
  `memories.md`, `database-schema-content-and-collaboration.md`,
  `configuration-persistent-settings-r-to-w.md`, `user-settings-and-personalisation.md` and
  `admin-settings-panels.md`. `rag-retrieval-embeddings-and-vector-stores.md` was being written at the
  same time; its section numbers are not cited here.
- Nothing found contradicts `../tools/ground-truth.md` or `CLAUDE.md`. Consistent details: deleting a
  user leaves their knowledge bases in place (shown as `Deleted User`, section 3.3); admins skip
  knowledge permission checks at each call site (section 3.4).
- `users-groups-roles-and-permissions.md` (section 5.17, table of share panels) and this document agree
  that **Knowledge Sharing** controls the Access List and **Knowledge Public Sharing** the Public option.
- `chat-completion-pipeline-and-generation-tasks.md` (section 11.13) and
  `workspace-models-and-model-access.md` (section 11.7) cover the "model ignores knowledge" symptom from
  their side; section 11.14 here adds the composer-clearing cause (11.11), which those documents do not
  mention.
