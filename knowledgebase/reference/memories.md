# Memories

## At a Glance

- A memory is a short piece of text about a user (a preference, a fact, a standing instruction) that MedIT GPT stores per user and can add to future conversations so the model "remembers" it. *Provisional summary; refined at the end of research.*
- Memories can be created by the user in Settings › Personalization, by the model through the built-in memory tools, and by a background memory review that runs after chat turns.
- Admins control memory with global settings and the `features.memories` permission; users control it with a per-user switch.
- Memories can contain personal or health details captured from chats, so support staff must treat them as personal data.
- *Added 2026-10-09 when sections 10 to 14 were completed:* memory is on by default for everyone while the site switch is on; the background review is off by default and has no screen (sections 3.2 and 5.8).
- There is no limit on the number or length of memories and no "memory full" message; only the memory context sent to the model is capped, at 2,000 characters of User memories by default (sections 7.3 and 11.4).
- Deleting a memory is permanent and does not reach copies in chats, webhooks, logs or the model provider; deleting an account leaves its memories behind (sections 3.4 and 5.5).
- Several failures show no message at all, and a failed list load looks like having no memories; check section 10.6 before concluding that memories are gone (section 11.5).

## 1. Purpose and Who Uses It

A **memory** is one short piece of text saved against one person's account: a preference ("Prefers
answers in point form"), a fact about them, a standing instruction, or other lasting context. MedIT
GPT can add a person's memories to their later conversations, so the model behaves as if it
remembers them. Memories are not tied to a chat or a model; they follow the person.

Each memory is a row in the `memory` table holding the text, a **type** (`user` or `context`), an
optional **path** (a slash-separated label such as `work/teaching`), a small `meta` record and two
timestamps (`backend/open_webui/models/memories.py:15-28`). A searchable copy of each memory (an
embedding made by the site's embedding model) is kept in a per-person vector collection named
`user-memory-{user_id}` (`backend/open_webui/routers/memories.py:128-168`, `:171-173`). Every memory
route reads, changes or deletes only the signed-in person's own rows
(`backend/open_webui/routers/memories.py:65`, `:398`, `:416`, `:432`, `:524`, `:565-575`, `:619`;
`backend/open_webui/models/memories.py:90`, `:159`).

### 1.1 How Memories Are Created

| Way | Who starts it | When | Recorded in `meta.created_by` | Source |
|---|---|---|---|---|
| **Add Memory** in Settings › Personalization | The person | When they press **Add** | `manual` | `src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:30-51`; `backend/open_webui/routers/memories.py:183-205` |
| The model calls the `add_memory` tool | The model, during a reply | Whenever the model decides to (memory tools must be offered, see 3.2) | `manual` (indistinguishable from a typed memory) | `backend/open_webui/tools/builtin.py:923-960`; `backend/open_webui/routers/memories.py:204` |
| The model calls `update_memory` (add, replace, move, remove) | The model | As above | `tool`, plus the chat id, message id and model id | `backend/open_webui/tools/builtin.py:963-1001`; `backend/open_webui/routers/memories.py:243-253` |
| **Background memory review** | The server, after a reply | Every Nth message the person sends in a chat (default every 10th); **off by default** | `background_review`, plus the chat id, message id and model id | `backend/open_webui/utils/memory.py:410-471`, `:522-525`; `backend/open_webui/config.py:428-429` |

### 1.2 How Memories Reach the Model

1. **Memory system context.** Before a request goes to the model, the server appends a block
   wrapped in `<memory_context>` and `</memory_context>` to the system message. It holds every
   `user`-type memory plus `context`-type memories that relate to the person's recent messages,
   each part capped by a character limit (`backend/open_webui/utils/memory.py:290-407`;
   `backend/open_webui/utils/middleware.py:2686-2698`). Section 5.6 explains the selection.
2. **Memory tools.** In native function-calling mode the model can list, search, read, add,
   change and delete the person's memories itself. The eight tools are catalogued in
   `builtin-native-tools.md` (section 4.3, rows 9 to 16, and section 3.2) and are not repeated
   here.

### 1.3 Who Uses It

| Who | What they do here | Where described |
|---|---|---|
| Any signed-in person with the Memories permission | Turn memory on or off for themselves; view, search, add, edit, remove and clear their memories | 2.1, 5.1 to 5.5 |
| The model | Receives memories in the system context; uses memory tools when offered | 1.2, 5.6, 5.7 |
| Admins | Site switches **Memories** and **Memory System Context**; the **Memories** permission; **Reindex** after an embedding change | 3, 5.9, 7 |
| Tier-1 support | Explain what memory does, check the switches a person can see, escalate privacy requests and failures | 11 |

Because memories are text drawn from what people type (or from what the model or the background
review pick out of chats), they can hold personal or health details. Treat them as personal data
(section 3.4).

## 2. Navigation and URLs

### 2.1 Where People See and Control Memories

| Screen | How to reach it | Who sees it | What is there | Source |
|---|---|---|---|---|
| Settings › **Personalization** | User menu › **Settings**, "Preferences" group, **Personalization**; or `/?settings=personalization` | Only when the site switch **Memories** is on **and** the person is an admin or has the **Memories** permission. Otherwise the tab is absent and the link opens **General** instead | Heading **Personalization**; section **Memory**; the **Memory** switch with an "Experimental" badge (shown in capitals; tooltip in section 10); a description; **Saved Memories** with a count; a **Search Memories** box (only when at least one memory exists); an **Actions** menu (**Add Memory**, **Clear memory**); each memory's text with **Edit** and **Remove**; a **Save** button | `src/lib/components/chat/SettingsModal.svelte:144-156`, `:223-228`, `:397-402`, `:490-497`, `:653-665`, `:825-831`; `src/routes/(app)/+layout.svelte:165-194`; `src/lib/components/chat/Settings/Personalization.svelte:105-282`; `src/lib/i18n/locales/en-US/translation.json:3000-3007` |
| **Add Memory** / **Edit Memory** dialog | **Actions** › **Add Memory**, or **Edit** on a memory | As above | **Type** toggle (**User** or **Context**), a text box, **Path** (optional), **Add** or **Update** | `src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:54-142` |
| Admin Settings › **General** | `/admin/settings/general` | Admins | **Memories** switch and, while it is on, **Memory System Context** | `src/lib/components/admin/Settings/General.svelte:315-333`; `src/lib/i18n/locales/en-US/translation.json:2390-2393` |
| Admin Panel › Users › **Groups** › **Default permissions** or a group › "Features Permissions" | `/admin/users/groups` | Admins | **Memories** switch | `src/lib/components/admin/Users/Groups/Permissions.svelte:960`, `:1099-1112` |
| Admin Settings › **Documents** › "Danger Zone" | `/admin/settings/documents` | Admins | **Reindex Knowledge and Memory Vectors** › **Reindex** | `src/lib/components/admin/Settings/Documents.svelte:382-416`, `:1547`, `:1576-1590`; `src/lib/i18n/locales/en-US/translation.json:2317-2319`, `:2333` |
| Model editor › **Capabilities** and **Builtin Tools** | Workspace › Models (one model) or the admin model defaults (see `workspace-models-and-model-access.md`) | Model owners and admins | Capability **Memory** ("Inject stored memories into conversation context"); built-in tool group **Memory** ("Search and manage user memories") | `src/lib/components/workspace/Models/Capabilities.svelte:53-56`; `src/lib/components/workspace/Models/BuiltinTools.svelte:21-24`; `src/lib/i18n/locales/en-US/translation.json:2556-2557`, `:2585-2586` |

There is **no screen that lists another person's memories**, for admins or anyone else, and no
memory route takes a user id (section 3.4).

The Settings modal also has a search box; the Personalization tab is indexed under its own
`settings.personal.personalization.` keys, so searching for its labels finds it when the tab is
available (`src/lib/components/chat/SettingsModal.svelte:223-228`, `:414-417`).

### 2.2 API Endpoints

All memory routes are mounted under `/api/v1/memories` (`backend/open_webui/main.py:872`). Every
route except `/reindex` first runs the memory check in 3.1.

| Method and path | Who may call | What it does | Front-end caller | Source |
|---|---|---|---|---|
| `GET /api/v1/memories/` | Signed-in (`user` or `admin`) | Lists the caller's own memories | Personalization list | `backend/open_webui/routers/memories.py:57-65`; `src/lib/apis/memories/index.ts:3-29` |
| `POST /api/v1/memories/add` | Signed-in | Adds one memory and its search copy | Add Memory dialog | `backend/open_webui/routers/memories.py:183-231`; `src/lib/apis/memories/index.ts:31-62` |
| `POST /api/v1/memories/update` | Signed-in | Applies a batch of add, replace, move and remove operations (used by the `update_memory` tool and the background review) | none | `backend/open_webui/routers/memories.py:234-319` |
| `POST /api/v1/memories/query` | Signed-in | Similarity search over the caller's memories (used to build the memory system context) | none (a client function exists but nothing calls it) | `backend/open_webui/routers/memories.py:332-388`; `src/lib/apis/memories/index.ts:100-129` |
| `POST /api/v1/memories/search` | Signed-in | Word search by text, path, type or id (used by `search_memories`) | none | `backend/open_webui/routers/memories.py:391-406` |
| `POST /api/v1/memories/paths` | Signed-in | Lists path groups with counts (used by `list_memory_paths`) | none | `backend/open_webui/routers/memories.py:409-422` |
| `POST /api/v1/memories/path` | Signed-in | Reads memories under one path (used by `read_memory_path`) | none | `backend/open_webui/routers/memories.py:425-443` |
| `POST /api/v1/memories/reindex` | **Admin** | Rebuilds the search copies of every person's memories | Documents › Reindex | `backend/open_webui/routers/memories.py:449-480`; `src/lib/apis/memories/index.ts:131-157` |
| `POST /api/v1/memories/reset` | Signed-in | Rebuilds the caller's own search copies (despite the name, it deletes no memory) | none | `backend/open_webui/routers/memories.py:483-508` |
| `DELETE /api/v1/memories/delete/user` | Signed-in | Deletes all of the caller's memories and their collection | **Clear memory** | `backend/open_webui/routers/memories.py:516-540`; `src/lib/apis/memories/index.ts:191-221` |
| `POST /api/v1/memories/{memory_id}/update` | Signed-in | Edits one memory | Edit Memory dialog; `replace_memory_content` tool | `backend/open_webui/routers/memories.py:548-602`; `src/lib/apis/memories/index.ts:64-98` |
| `DELETE /api/v1/memories/{memory_id}` | Signed-in | Deletes one memory and its search copy | **Remove** | `backend/open_webui/routers/memories.py:610-631`; `src/lib/apis/memories/index.ts:159-189` |

Settings endpoints that carry memory values (admin only):

| Method and path | Memory keys | Source |
|---|---|---|
| `GET` and `POST /api/v1/auths/admin/config` | `ENABLE_MEMORIES` (`memories.enable`) and `ENABLE_MEMORY_SYSTEM_CONTEXT` (`memories.system_context.enable`) only | `backend/open_webui/routers/auths.py:104-136`, `:1204-1206`, `:1269-1296` |
| `GET /api/v1/configs/namespace/memories` | Reads all six `memories.*` keys | `backend/open_webui/routers/configs.py:123-125` |
| `GET /api/v1/configs/export`, `POST /api/v1/configs/import` | Export and import of every stored setting, including the four memory keys that have no screen | `backend/open_webui/routers/configs.py:100-120` |

The site-wide on/off value reaches the browser as `features.enable_memories` in `/api/config`, in
the part sent only to signed-in users (`backend/open_webui/main.py:2342-2378`).

## 3. Roles and Permissions

Memory is governed by four layers: the site switch **Memories** (`memories.enable`), the
**Memories** permission (`features.memories`), the person's own **Memory** switch, and, per
model, the **Memory** capability and built-in tool group. Admins skip the permission check but
not the site switch. Pending accounts cannot use any memory route: the routes require role `user`
or `admin` and refuse others with HTTP 401 and the `ACCESS_PROHIBITED` text (ground truth;
`backend/open_webui/utils/auth.py:567-576`).

### 3.1 The Memory Check on Every Route

Every memory route except `/reindex` starts with `check_memories_permission`
(`backend/open_webui/routers/memories.py:35-47`):

| Condition | Result | Applies to |
|---|---|---|
| Site switch **Memories** (`memories.enable`) is off | HTTP 404 with `We could not find what you're looking for :/` (`ERROR_MESSAGES.NOT_FOUND`, `backend/open_webui/constants.py:78`) | Everyone, **including admins** |
| The caller is not an admin and does not hold `features.memories` | HTTP 403 with `You do not have permission to access this resource. Please contact your administrator for assistance.` (`backend/open_webui/constants.py:70-72`) | Non-admins |
| Otherwise | The route runs, limited to the caller's own memories | |

`/reindex` instead requires the admin role and ignores the site switch
(`backend/open_webui/routers/memories.py:449-453`).

The permission is evaluated like every other permission: granted if any of the person's groups
grants it, otherwise the stored default decides, and a group cannot take away a default that is on
(ground truth; `backend/open_webui/utils/access_control/__init__.py:75-108`). The code default for
`features.memories` is **on** (`USER_PERMISSIONS_FEATURES_MEMORIES`, `backend/open_webui/config.py:1926`,
`:2012`; front-end default `src/lib/constants/permissions.ts:71`). When a group's **Memories**
switch is off while the default is on, the group editor shows "This is a default user permission
and will remain enabled." (`src/lib/components/admin/Users/Groups/Permissions.svelte:1106-1112`).
The live default and group values are data, **TO BE CONFIRMED**.

### 3.2 What Each Memory Path Requires

| Path | Site **Memories** on | **Memories** permission (or admin) | Person's **Memory** switch on | Other conditions | Source |
|---|---|---|---|---|---|
| See the **Personalization** tab | Yes | Yes (the browser treats a missing value as allowed) | No (the tab shows with the switch off, but the list is hidden) | none | `src/lib/components/chat/SettingsModal.svelte:397-402`; `src/lib/components/chat/Settings/Personalization.svelte:142` |
| List, add, edit, remove, clear in Settings | Yes | Yes | The list and **Actions** menu appear only while it is on | none | `backend/open_webui/routers/memories.py:35-47`; `src/lib/components/chat/Settings/Personalization.svelte:142-270` |
| Memories added to the system context | Yes | Yes | Yes (the browser then sends `features.memory`) | Site switch **Memory System Context** on (code default on); the model's **Memory** capability on (default on) | `src/lib/components/chat/Chat.svelte:3412-3414`; `backend/open_webui/utils/middleware.py:2686-2698`; `backend/open_webui/utils/memory.py:286-292` |
| Memory tools offered to the model | Yes | Yes | Yes | The model's **Memory** capability and **Memory** built-in tool group on; native function calling and the other conditions in `builtin-native-tools.md` section 3.1; inside a sub-agent the four changing tools are removed | `backend/open_webui/utils/tools.py:656-673`, `:766-769`; `backend/open_webui/utils/subagents.py:34-39` |
| Background memory review | Yes | Yes | Yes | **Background review** setting on (code default **off**, no screen); the reply is not empty; the person's message count in the chat is a multiple of the review interval; the model's **Memory** capability on | `backend/open_webui/utils/memory.py:410-471` |
| Reindex every person's memory copies | No | Admin role required | No | none | `backend/open_webui/routers/memories.py:449-480` |

**The personal switch.** The **Memory** switch in Settings › Personalization saves `memory` in
the person's interface settings at once when flipped (no toast on success)
(`src/lib/components/chat/Settings/Personalization.svelte:134-139`;
`src/lib/components/chat/SettingsModal.svelte:438-450`). If the person has never touched it, the
switch and the chat page both fall back to the site switch, so **memory is on by default for
everyone while the site switch is on** (`src/lib/components/chat/Settings/Personalization.svelte:100`;
`src/lib/components/chat/Chat.svelte:3412`). The personal switch is a browser-side choice: it
decides whether the chat page asks for memory (`features.memory`); the server re-checks the site
switch and the permission but does not read the personal switch
(`backend/open_webui/utils/middleware.py:2686-2698`; `backend/open_webui/utils/memory.py:449-451`).
Turning it off deletes nothing (section 5.3).

**Requests from outside the chat page.** Server-side automations build their own feature list,
which never includes memory, so automation runs get no memory context or memory tools
(`backend/open_webui/utils/automations.py:176-198`). A sub-agent run copies the parent request's
features, so it can receive memory context and the read-only memory tools
(`backend/open_webui/utils/subagents.py:310-326`). A program calling the chat API directly gets
memory only if it sends `features.memory` itself (`backend/open_webui/main.py:1281`;
`backend/open_webui/utils/middleware.py:2683-2698`).

### 3.3 What Each Role Sees When Memory Is Off

| Switched off | What people see | Source |
|---|---|---|
| Site switch **Memories** | The **Personalization** tab disappears for everyone (admins included); `/?settings=personalization` opens **General**; the chat page stops sending `features.memory` only if the person has never set their own switch (otherwise the server still refuses: injection, tools and review all check the site switch); any direct call to a memory route answers 404 | `src/lib/components/chat/SettingsModal.svelte:397-402`, `:490-497`; `src/lib/components/chat/Chat.svelte:3412`; `backend/open_webui/routers/memories.py:37-41`; `backend/open_webui/utils/middleware.py:2689`; `backend/open_webui/utils/tools.py:659`; `backend/open_webui/utils/memory.py:437-438` |
| **Memories** permission (non-admin) | The tab disappears for that person; memory routes answer 403; no injection, tools or review | `src/lib/components/chat/SettingsModal.svelte:400`; `backend/open_webui/routers/memories.py:43-47`; `backend/open_webui/utils/middleware.py:2692-2698`; `backend/open_webui/utils/tools.py:662`; `backend/open_webui/utils/memory.py:449-451` |
| **Memory System Context** only | Settings still works; memories are no longer added to every request; the memory tools (if offered) still let the model look memories up | `backend/open_webui/utils/middleware.py:2690`; `backend/open_webui/utils/tools.py:656-673` |
| The person's **Memory** switch | Only the switch and its description remain on the tab; saved memories are kept but hidden until it is turned back on; no injection, tools or review for that person's chats | `src/lib/components/chat/Settings/Personalization.svelte:142-270`; `src/lib/components/chat/Chat.svelte:3412-3414` |
| The model's **Memory** capability | No injection and no review for chats with that model; memory tools also withheld | `backend/open_webui/utils/memory.py:286-292`, `:420-421`; `backend/open_webui/utils/tools.py:661` |

Memories stored before the site switch or a permission was turned off stay in the database; none
of the switches deletes anything (no deletion code is attached to them; `backend/open_webui/routers/auths.py:1269-1296`).

### 3.4 Privacy: Who Can See a Person's Memories

- **The person.** Settings › Personalization shows their memories (text only; type and path are
  not displayed but are searchable) (`src/lib/components/chat/Settings/Personalization.svelte:84-97`, `:241-247`).
- **The model and its provider.** Memory text is sent to the chat model with each request while
  injection is on, and the background review sends the model up to 80 existing memories plus the
  last 16 messages of the chat (`backend/open_webui/utils/memory.py:405-406`, `:484-521`,
  `:569-591`). Memory text is also sent to the embedding engine each time a memory is added or
  changed (`backend/open_webui/routers/memories.py:207-209`, `:269-273`, `:578-580`). Which model
  providers and embedding engine production uses, and whether they are approved for health data,
  is **TO BE CONFIRMED** (see `model-connections-openai-ollama-and-direct.md` and
  `rag-retrieval-embeddings-and-vector-stores.md`).
- **Other users.** No memory route accepts another person's id; every query is filtered to the
  caller (section 1). The retrieval module also refuses non-admins access to any memory
  collection other than their own (`backend/open_webui/retrieval/utils.py:1342-1344`).
- **Admins.** There is no admin screen or memory route that lists another person's memories. The
  retrieval module's collection check exempts admins (`backend/open_webui/retrieval/utils.py:1330-1331`).
  Whether admins may look at memories, and under what policy, is **TO BE CONFIRMED**.
  Security-sensitive: refer to the platform maintainer and U of T Information Security
  (security.utoronto.ca).
- **People with database, vector-store or backup access.** The memory text is an ordinary text
  column (`backend/open_webui/models/memories.py:25`) and the search copy holds the same text
  (`backend/open_webui/routers/memories.py:159-163`).
- **Event destinations.** Creating, changing and deleting memories publishes `memory.created`,
  `memory.updated`, `memory.deleted` and `memory.reset` events; created and updated events carry
  the first 300 characters of the memory, its type and path, and the acting person's id, name,
  email and role. They go to every configured event webhook whose filter matches (a webhook with
  no filter receives all events) and to Event functions (`backend/open_webui/routers/memories.py:224-230`,
  `:292-317`, `:472-479`, `:500-507`, `:531-537`, `:595-601`, `:623-628`;
  `backend/open_webui/events.py:335-346`, `:704`, `:712-713`, `:1069-1071`, `:1171`, `:1198-1202`).
  Which webhooks production has is **TO BE CONFIRMED**.
- **Audit log.** When the audit log is on, it records request bodies (ground truth), which would
  include memory text sent to the add and edit routes.
- **Account deletion leaves memories behind.** Deleting a user removes group memberships, chats,
  the `user` row and the `auth` row only; neither the admin delete path nor SCIM deprovisioning
  touches the `memory` table or the `user-memory-{user_id}` collection (ground truth, verified:
  `backend/open_webui/models/users.py:849-863`; `backend/open_webui/models/auths.py:228-239`;
  `backend/open_webui/routers/users.py:1042-1075`; `backend/open_webui/routers/scim.py:857`; no
  other code deletes memories). The admin **Reindex** skips them too, because it walks the list
  of existing users (`backend/open_webui/routers/memories.py:460-470`). A person who wants their
  memories gone should use **Clear memory** before their account is deleted; afterwards removal
  needs database work (escalate).

## 4. Key Concepts and Terminology

### 4.1 Glossary

| Term | Meaning | Source |
|---|---|---|
| Memory | One saved piece of text belonging to one person, with a type, an optional path and timestamps | `backend/open_webui/models/memories.py:15-28` |
| **User** memory (type `user`) | A lasting fact, preference or instruction about the person. **Every** `user` memory goes into the memory context of every request while injection is on (subject to the character limit) | `backend/open_webui/utils/memory.py:321-326`, `:541-542`; `src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:96-97` |
| **Context** memory (type `context`) | Other lasting context for future chats. Included only when it looks related to the recent messages (by path or by similarity search) | `backend/open_webui/utils/memory.py:328-361`, `:543` |
| Path | An optional label with slash-separated parts (for example `teaching/fall-term`) used to group memories. Leading, trailing and repeated slashes and surrounding spaces are removed; parts `.` and `..` and control characters are refused | `backend/open_webui/utils/memory.py:28-35` |
| Memory context | The block `<memory_context>` … `</memory_context>` the server appends to the system message, with up to three headed parts: `[User Memory]`, `[Memory Neighborhood]`, `[Relevant Context]` | `backend/open_webui/utils/memory.py:17-18`, `:363-406` |
| Memory Neighborhood | `context` memories filed under a path whose name appears in the recent messages | `backend/open_webui/utils/memory.py:230-248`, `:328-338` |
| Relevant Context | Memories found by similarity search on the recent messages (up to 8) that are not already listed | `backend/open_webui/utils/memory.py:312-317`, `:340-361` |
| Search copy (memory vector) | The embedding of a memory's path and text, stored in the vector collection `user-memory-{user_id}` with the memory's id, type, path and dates | `backend/open_webui/routers/memories.py:119-125`, `:128-168`; `backend/open_webui/utils/memory.py:38-40` |
| Memory System Context | The admin switch that decides whether the memory context is added at all | `backend/open_webui/config.py:427`, `:2845`; `src/lib/components/admin/Settings/General.svelte:322-333` |
| Background memory review | After a reply, every Nth message the person sends, the chat model is asked privately whether long-term memory should change, and its answer is applied | `backend/open_webui/utils/memory.py:410-609` |
| Review interval | N in the line above: `memories.review_interval_turns`, code default 10, minimum 1 | `backend/open_webui/config.py:429`; `backend/open_webui/utils/memory.py:440-447` |
| User and context character limits | Caps on the length of the `[User Memory]` part and of the other two parts together, code default 2,000 characters each, never below 250 | `backend/open_webui/config.py:430-431`; `backend/open_webui/utils/memory.py:375-401` |
| `created_by` | Who last wrote the memory, kept in `meta`: `manual` (typed in Settings, the `add_memory` tool, or the `replace_memory_content` tool), `tool` (the `update_memory` tool) or `background_review`. Tool and review writes also keep the chat id, message id and model id. Not shown anywhere in the interface | `backend/open_webui/routers/memories.py:204`, `:245-253`, `:572` |
| Memory capability | A per-model switch ("Inject stored memories into conversation context"); off means no memory context, no review and no memory tools for that model. Default on | `src/lib/constants.ts:126`; `backend/open_webui/utils/memory.py:286-287`; `src/lib/i18n/locales/en-US/translation.json:2585-2586` |
| Memory built-in tool group | A per-model switch for the eight memory tools ("Search and manage user memories"). Default on | `backend/open_webui/utils/tools.py:538-540`, `:656-673`; `src/lib/i18n/locales/en-US/translation.json:2556-2557` |
| Reindex | Rebuilding every person's search copies with the current embedding model (admin) | `backend/open_webui/routers/memories.py:449-480` |
| Reset | Rebuilding one person's own search copies (route only, no button) | `backend/open_webui/routers/memories.py:483-508` |

### 4.2 Default Type Depends on Where a Memory Is Made

| Where | Default type | Source |
|---|---|---|
| Settings **Add Memory** dialog | **User** (the toggle starts on User) | `src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:20`, `:26` |
| `add_memory` tool | `user` | `backend/open_webui/tools/builtin.py:923-926` |
| `POST /api/v1/memories/add` without a type | `context` | `backend/open_webui/routers/memories.py:73-76` |
| Background review and `update_memory` | Whatever the model chose; a missing type is stored as `context`. *Corrected 2026-10-09: this cell said "anything other than `user` is stored as `context`". Only `user`, `context` or no type pass the batch form's check; any other value refuses the whole batch, so none of its operations is applied (the `update_memory` tool returns the validation error; the review logs it at debug level; section 10.3).* | `backend/open_webui/models/memories.py:46-48`; `backend/open_webui/utils/memory.py:262`; `backend/open_webui/routers/memories.py:85-95`; `backend/open_webui/tools/builtin.py:993-997`; `backend/open_webui/utils/memory.py:465-469`, `:525` |
| Memories that existed before the database gained the `type` column | `context` (the migration's default) | `backend/open_webui/migrations/versions/7b3f2a9c1d4e_add_memory_type.py:27-28` |

The last row matters to support: memories saved before the upgrade that introduced types (the
"Reworked memory system" entry, `CHANGELOG.md:987`) are `context` memories, so they are included
only when they look related to the conversation, not in every request. Opening one in **Edit** and
switching **Type** to **User** changes that (section 5.4).

### 4.3 What the Memory Context Looks Like

An invented example of the block the model receives (people never see it in the chat):

```
<memory_context>
[User Memory]
- Prefers short answers in point form.
- teaching: Teaches an undergraduate anatomy course.

[Memory Neighborhood]
- teaching/fall-term: Lab sections run on Thursday mornings.

[Relevant Context]
- Is preparing a curriculum review for next spring.
</memory_context>
```

Each part's entries are sorted alphabetically (by path, then text), so when a part is longer than
its character limit the entries that sort last are cut, possibly mid-sentence
(`backend/open_webui/utils/memory.py:363-401`). The block is added to the request only; it is not
saved in the chat and no status line reports it (`backend/open_webui/utils/memory.py:405-407`).

## 5. Workflows (Step by Step)

### 5.1 Turn Memory On or Off for Yourself

1. Open the user menu › **Settings** › **Personalization** (or go to `/?settings=personalization`).
   If the tab is missing, the site switch or the permission is off (section 3.3).
2. Flip the **Memory** switch. The choice is saved straight away as `memory` in the person's
   settings; nothing confirms success, and a failure shows the server's error text in a toast
   (`src/lib/components/chat/Settings/Personalization.svelte:134-139`;
   `src/lib/components/chat/SettingsModal.svelte:438-450`).
3. The **Save** button at the bottom only shows "Settings saved successfully!"; it saves nothing
   else (`src/lib/components/chat/Settings/Personalization.svelte:105-111`, `:274-281`;
   `src/lib/components/chat/SettingsModal.svelte:825-831`).

Effects: with the switch on, the chat page asks for memory on every message (injection, tools and
review, subject to section 3.2). With it off, the list of saved memories is hidden, but **nothing
is deleted**; turning it back on shows them again (`src/lib/components/chat/Settings/Personalization.svelte:142-270`;
`src/lib/components/chat/Chat.svelte:3412-3414`). A person who has never touched the switch
follows the site switch, which means on by default (section 3.2).

### 5.2 View and Search Your Memories

1. In Settings › Personalization with **Memory** on, **Saved Memories** shows the number of
   memories and lists them newest-changed first. Only each memory's text is shown, not its type,
   path or dates (`src/lib/components/chat/Settings/Personalization.svelte:95-97`, `:144-151`,
   `:241-265`).
2. Type in **Search Memories** (up to 500 characters) to filter by words in the text, the path or
   the type (`user` or `context`). The box appears only when at least one memory exists
   (`src/lib/components/chat/Settings/Personalization.svelte:84-93`, `:159-183`).
3. With no memories the area reads "Memories accessible by LLMs will be shown here."; with
   memories but no search match it reads "No results found"
   (`src/lib/components/chat/Settings/Personalization.svelte:231-238`;
   `src/lib/i18n/locales/en-US/translation.json:3004`).

The list loads each time the tab opens, from `GET /api/v1/memories/`; an error shows the server's
text in a toast and an empty list (`src/lib/components/chat/Settings/Personalization.svelte:51-59`, `:99-102`).

### 5.3 Add a Memory

1. **Actions** › **Add Memory**. The description above the switch says to use "the 'Add Memory'
   button below"; the button is inside the **Actions** menu (the component swaps "Manage" in the
   stored text for "Add Memory") (`src/lib/components/chat/Settings/Personalization.svelte:121-127`,
   `:188-211`; `src/lib/i18n/locales/en-US/translation.json:3001-3002`).
2. In the dialog, choose **Type** by clicking the word **User** or **Context** (it toggles), type
   the memory, and optionally a **Path**. The text box hint changes with the type: "Add a
   preference, fact, or instruction about you" or "Add durable context for future chats"
   (`src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:72-114`).
3. Press **Add**. The server trims the text (empty text is refused), cleans the path, saves the
   row with `created_by: manual`, embeds the path and text, stores the search copy and publishes a
   `memory.created` event (`backend/open_webui/routers/memories.py:183-231`).
4. On success "Memory added successfully" appears, the dialog closes and the list reloads
   (`src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:42-48`).

Read from code: the row is saved **before** the embedding is made, in its own transaction
(`backend/open_webui/models/memories.py:60-74`; `backend/open_webui/routers/memories.py:199-209`).
If the embedding engine fails, the server answers with an unhandled error, the dialog stays open
with no message (the browser cannot read a reason from it), and the memory exists without a search
copy; pressing **Add** again saves a second copy (`src/lib/apis/memories/index.ts:47-59`;
`src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:33-50`). A changed embedding
size is handled automatically: when the vector store reports a dimension mismatch, the person's
search copies are rebuilt (`backend/open_webui/routers/memories.py:171-180`).

There is no limit on how many memories a person can save, and no length limit on a memory, in the
code (no count or length check in `backend/open_webui/routers/memories.py:183-231`).

### 5.4 Edit a Memory

1. Click **Edit** next to the memory. The dialog opens titled **Edit Memory** with the current
   text, type and path (`src/lib/components/chat/Settings/Personalization.svelte:66-69`, `:249-255`;
   `src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:23-28`, `:57-63`).
2. Change the text, the type or the path and press **Update**. The dialog always sends the text,
   the type and the path; an emptied path removes the path
   (`src/lib/apis/memories/index.ts:64-82`; `backend/open_webui/routers/memories.py:561-573`).
3. The server updates the row (marking it `created_by: manual`), re-embeds the text and replaces
   the search copy, then publishes `memory.updated`
   (`backend/open_webui/routers/memories.py:548-602`; `backend/open_webui/models/memories.py:76-106`).
4. "Memory updated successfully" appears and the list reloads
   (`src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:42-48`).

If the memory no longer exists (for example the model deleted it meanwhile) the server answers 404
and the toast shows `We could not find what you're looking for :/`
(`backend/open_webui/routers/memories.py:574-575`). As in 5.3, an embedding failure leaves the new
text saved but the search copy holding the old text (read from code,
`backend/open_webui/routers/memories.py:565-593`).

### 5.5 Remove One Memory or Clear All Memories (Permanence)

**Remove one.** **Remove** › dialog **Delete Memory?** ("Are you sure you want to delete this
memory? This action cannot be undone." with the memory's text shown) › **Confirm**. The server
deletes the row, then deletes the search copy, then publishes `memory.deleted`; the toast reads
"Memory deleted successfully" and the list reloads
(`src/lib/components/chat/Settings/Personalization.svelte:61-64`, `:294-323`;
`backend/open_webui/routers/memories.py:610-631`).

**Clear all.** **Actions** › **Clear memory** (greyed out when there are no memories) › dialog
**Clear Memory** ("Are you sure you want to clear all memories? This action cannot be undone.") ›
**Confirm**. The server deletes every one of the person's rows and then the whole
`user-memory-{user_id}` collection; the toast reads "Memory cleared successfully"
(`src/lib/components/chat/Settings/Personalization.svelte:71-82`, `:213-225`, `:284-292`;
`backend/open_webui/routers/memories.py:516-540`).

What permanence means here:

| Question | Answer from the code | Source |
|---|---|---|
| Is there an undo, trash or soft delete? | No; rows are deleted outright | `backend/open_webui/models/memories.py:134-166` |
| Is the search copy deleted too? | Yes, in the same request, after the row. For **Clear memory** a failure to delete the collection is only logged, so the copies could survive; for **Remove** a failure makes the request fail after the row is already gone | `backend/open_webui/routers/memories.py:526-530`, `:619-622` |
| Can a stale copy still reach the model? | Read from code: the similarity search reads the vector store, so a surviving copy could still appear under `[Relevant Context]` once the person has any memory again (with no memories at all, the search is skipped). An admin **Reindex** removes such leftovers for existing users, because it deletes and rebuilds each person's collection from the table | `backend/open_webui/routers/memories.py:128-143`, `:344-354`; `backend/open_webui/utils/memory.py:340-361` |
| Are copies left elsewhere? | Yes, possibly: tool calls that listed or searched memories are recorded inside the replies of that chat (see `builtin-native-tools.md` section 6.2); event webhooks and Event functions received previews; the audit log (if on) holds request bodies; the model provider received the text with requests. None of these is touched by deleting a memory | `backend/open_webui/routers/memories.py:224-230`, `:306-317`; ground truth (audit log) |
| Can a deleted memory be restored? | Not from the application. Whether database backups exist and whether a single memory can be restored from them is **TO BE CONFIRMED** | none in repository |

The model can also delete memories (`delete_memory`, or a `remove` operation in `update_memory`)
with the same permanence; `delete_memory` publishes no event
(`backend/open_webui/tools/builtin.py:1053-1082`; `backend/open_webui/routers/memories.py:282-290`).

### 5.6 How Memories Are Added to a Conversation (System Context Injection)

This happens on every message (and every regeneration) while the conditions in 3.2 hold. The
person sees nothing in the chat.

1. The chat page adds `memory: true` to the request's features when the person's **Memory**
   switch is on, or unset while the site switch is on. It does this for temporary chats too
   (`src/lib/components/chat/Chat.svelte:3393-3417`).
2. On the server, after inlet filters and before web search and image generation, the payload
   step checks `features.memory`, the **Memories** and **Memory System Context** switches, and
   (for non-admins) the **Memories** permission (`backend/open_webui/utils/middleware.py:2396-2398`,
   `:2683-2698`).
3. If the model's **Memory** capability is off, nothing is added
   (`backend/open_webui/utils/memory.py:290-292`).
4. The search text is the person's last seven non-empty messages, joined, keeping the last 4,000
   characters (`backend/open_webui/utils/memory.py:294-308`).
5. All of the person's memories are read, and a similarity search returns up to 8 nearest search
   copies. If the site's RAG relevance threshold (`rag.relevance_threshold`, code default 0.0) is
   above zero, weaker matches are dropped; at 0.0 the 8 nearest are used however unrelated. Any
   error in the search is ignored (`backend/open_webui/utils/memory.py:310-317`;
   `backend/open_webui/routers/memories.py:332-388`; `backend/open_webui/config.py:970`, `:2901`).
6. The block is assembled: `[User Memory]` holds **all** `user` memories; `[Memory Neighborhood]`
   holds up to 4 `context` memories for each of up to 6 paths whose name appears in the search
   text; `[Relevant Context]` holds the similarity results not already listed. Each memory appears
   as `path: text` or just `text` (`backend/open_webui/utils/memory.py:43-44`, `:230-248`, `:319-371`).
7. The limits are read: `memories.user_char_limit` for the `[User Memory]` part and
   `memories.context_char_limit` for the other two parts together (code default 2,000 each; a
   value below 250 is raised to 250; 0, empty or unreadable means 2,000). Each part is cut to its
   limit (`backend/open_webui/utils/memory.py:375-401`).
8. Any earlier memory block is removed from the system message, and the new block is appended to
   the existing system message, or placed in a new system message at the top
   (`backend/open_webui/utils/memory.py:385-406`; `backend/open_webui/utils/misc.py:682-698`).

Points support should know: a person with many long `user` memories will have some of them cut
from every request once the total passes the limit (2,000 characters by default, which is, for
example, 40 memories of 50 characters each); `context` memories appear only when related; the block is rebuilt from
scratch for each request, so an edit or deletion takes effect from the next message.

### 5.7 How the Model Reads and Saves Memories Itself (Memory Tools)

When the memory tools are offered (section 3.2), the model may call them in the middle of a
reply. Each call appears in the reply as a tool-call entry, like any built-in tool (see
`builtin-native-tools.md` sections 4.2 and 5.6). The eight tools, their limits and results are
catalogued in `builtin-native-tools.md` section 4.3 (rows 9 to 16). Points specific to this area:

- The tool descriptions tell the model to save "enduring information" such as preferences,
  goals, projects, relationships, habits and standing instructions, and not one-off activity,
  meals, routine events or passing mood unless asked (`backend/open_webui/tools/builtin.py:930-936`,
  `:968-975`). Nothing in them mentions health or other sensitive details.
- A memory saved with `add_memory` is recorded as `manual`, exactly like one typed in Settings;
  one changed with `replace_memory_content` is also recorded as `manual`; `update_memory` records
  `tool` with the chat, message and model (`backend/open_webui/routers/memories.py:204`, `:245-253`, `:572`).
- If the person asks the model to forget something, the model can delete it with `delete_memory`
  or a `remove` operation; the person can always check the result in Settings › Personalization.
- With **Tool Permissions** on, these calls can be made to wait for **Allow** or **Deny** like
  other tools (see `builtin-native-tools.md` section 5.4).

### 5.8 Background Memory Review

Off by default (`memories.background_review.enable`, code default `False`,
`backend/open_webui/config.py:428`, `:2846`); there is no screen to turn it on (section 7). When
it is on:

1. After a reply finishes and is saved, the server runs outlet filters and the follow-up, title
   and tag tasks, then calls the review step (`backend/open_webui/utils/middleware.py:4378-4385`,
   `:6585-6590`, `:4038-4047`).
2. The review continues only if the model allows memory, the request carried `features.memory`,
   the reply has text, both **Memories** and the review setting are on, the number of messages
   the person has sent in this branch of the chat is a whole multiple of the review interval
   (default 10: the 10th, 20th, 30th …), and the person is an admin or holds the **Memories**
   permission (`backend/open_webui/utils/memory.py:420-451`). Regenerating a reply at such a
   message runs the review again (read from code: the count is of messages in the branch).
3. It then runs as a separate background task, so the reply is not delayed. A failure is logged
   only at debug level, as `Memory review failed: {e}` (`backend/open_webui/utils/memory.py:453-471`).
4. The review gathers up to 80 of the person's existing memories (id, type, path, text) and the
   last 16 messages of the chat (questions and replies only; any message over 1,600 characters is
   shortened to its first 1,000 and last 400), plus the final reply
   (`backend/open_webui/utils/memory.py:484-511`).
5. It asks **the same model the person is chatting with** (not the task model) for a JSON list of
   operations, with a system message naming it a "private memory reviewer" and rules: save
   enduring details; skip one-off activity, meals, temporary mood and routine events unless the
   person asked; "Do not save secrets, credentials, transient task steps, or unsupported
   guesses."; prefer replacing, moving or removing over duplicates
   (`backend/open_webui/utils/memory.py:513-591`). Like the tool descriptions, the rules say
   nothing about health details.
6. Anything that is not valid JSON is ignored. Valid operations are applied through the batch
   route with `created_by: background_review`, the chat id, message id and model id; search copies
   are updated and events published; an `add` identical to an existing memory (same text, type
   and path) is skipped (`backend/open_webui/utils/memory.py:593-609`, `:522-525`;
   `backend/open_webui/routers/memories.py:234-319`; `backend/open_webui/models/memories.py:181-198`).
7. The person is not told. New or changed memories simply appear in Settings › Personalization.

The review also runs for temporary chats: for chats that are not saved, the messages come from the
request itself (`backend/open_webui/utils/middleware.py:3880-3885`, `:4038-4047`).

### 5.9 Admin: Switch Memory On or Off and Set the Permission

1. **Site switch.** Admin Settings › **General** › **Memories** ("Allow users to save memories
   for more personalized responses."). While it is on, **Memory System Context** ("Include saved
   memories in the system context.") appears beneath it. Press **Save**; both are stored in the
   `config` table (`src/lib/components/admin/Settings/General.svelte:79-102`, `:315-333`;
   `backend/open_webui/routers/auths.py:1269-1296`; `src/lib/i18n/locales/en-US/translation.json:2390-2393`).
2. **Permission.** Admin Panel › Users › **Groups** › **Default permissions** (everyone with the
   `user` role) or a group › "Features Permissions" › **Memories** › **Save**
   (`src/lib/components/admin/Users/Groups/Permissions.svelte:960`, `:1099-1112`). To restrict
   memory to some people, turn it off in the defaults and on in a group (ground truth: a group
   cannot take away a default that is on).
3. **Per model.** In the model editor, **Capabilities** › **Memory** and **Builtin Tools** ›
   **Memory** (see `workspace-models-and-model-access.md`).

The change applies to the next request; open browser tabs pick up the site switch when they next
load the configuration (`backend/open_webui/main.py:2378`).

### 5.10 Admin: Reindex Memory Vectors

Needed after the site's embedding model changes, because old search copies were made with the old
model (the Documents screen says so: "After changing the embedding model, reindex knowledge,
knowledge search, and memory vectors for changes to take effect.").

1. Admin Settings › **Documents** › "Danger Zone" › **Reindex Knowledge and Memory Vectors**
   ("Rebuild vectors for existing knowledge files, knowledge search, and memories.") › **Reindex**.
2. Confirm the dialog **Reindex Embedding Data** ("Rebuild knowledge file, knowledge search, and
   memory vectors using the current embedding model.").
3. The browser reindexes knowledge files, then the knowledge search index, then memories; if an
   earlier step fails its error is shown and the memory step does not run. On success the toast
   reads "Success" (`src/lib/components/admin/Settings/Documents.svelte:382-416`, `:1160-1171`,
   `:1576-1590`).
4. For each existing user, the server deletes the person's memory collection and rebuilds it from
   the `memory` table, then publishes one `memory.reset` event with the totals
   (`backend/open_webui/routers/memories.py:449-480`, `:128-168`).

All embeddings for one person are requested at once, so a person with many memories means many
simultaneous embedding calls (`backend/open_webui/routers/memories.py:145-154`, `:488-495`).
Memories of deleted accounts are not touched (section 3.4).

### 5.11 Handling a Request to See or Remove Someone's Memories

- **The person themselves:** they can see, edit and delete everything in Settings ›
  Personalization (5.2 to 5.5). Tier 1 can walk them through it.
- **Before an account is deleted:** ask the person (or the admin deleting the account) to use
  **Clear memory** first, because deleting the account leaves memories behind (section 3.4).
- **Anyone else's memories, or memories of a deleted account:** there is no screen for this.
  Escalate to the platform maintainer; this is a privacy matter (U of T Privacy Office,
  privacy.utoronto.ca) and any database work is outside tier 1.
- **Copies outside the memory table** (chat tool entries, webhooks, logs, model provider):
  see the table in 5.5; include them in the escalation.

## 6. Data Model

### 6.1 The `memory` Table

One row per memory (`backend/open_webui/models/memories.py:15-28`):

| Column | Type | Meaning |
|---|---|---|
| `id` | text, primary key | A random UUID made when the memory is created (`:63`, `:201`) |
| `user_id` | text, indexed | The owner. A plain value with **no foreign key** to the `user` table, which is why deleting a user leaves the row (section 3.4) |
| `type` | text, indexed, default `context` | `user` or `context` (`:23`, `:46-48`) |
| `path` | text, may be empty | The optional grouping label, already cleaned (section 4.1) |
| `content` | text | The memory itself, as ordinary text |
| `meta` | JSON, may be empty | `created_by` (`manual`, `tool` or `background_review`) and, for tool and review writes, `chat_id`, `message_id` and `model` (the model id). Updates merge into the existing value (`:99-100`, `:228-229`) |
| `updated_at` | integer, epoch seconds | Set on every change |
| `created_at` | integer, epoch seconds | Set once |

Indexes: `ix_memory_id_user_id` on (`id`, `user_id`) (`backend/open_webui/models/memories.py:19`),
`ix_memory_user_id` and `ix_memory_type` (from the migrations below).

The list route returns `meta` to the person's own browser; the batch, path and tool results leave
it out (`backend/open_webui/routers/memories.py:57`, `:267`, `:442`; `CHANGELOG.md:173`).

### 6.2 The Search Copies (Vector Store)

| Item | Value | Source |
|---|---|---|
| Collection | `user-memory-{user_id}`, one per person | `backend/open_webui/routers/memories.py:134`, `:173` |
| Item id | The memory's id | `backend/open_webui/routers/memories.py:160`, `:216` |
| Item text | `path` + line break + text, or just the text when there is no path | `backend/open_webui/utils/memory.py:38-40` |
| Item metadata | `created_at`, `updated_at`, `type`, `path` | `backend/open_webui/routers/memories.py:119-125` |
| Embedding | Made by the site's embedding function with the content prefix (`RAG_EMBEDDING_CONTENT_PREFIX`); searches use the query prefix | `backend/open_webui/routers/memories.py:147-151`, `:348`; `backend/open_webui/config.py:1027-1029` |
| Shared-collection backends | The Qdrant and Milvus multitenancy backends store every person's memory copies in one collection named `{prefix}_memories`, keyed by the `user-memory-{user_id}` name | `backend/open_webui/retrieval/vector/dbs/qdrant_multitenancy.py:85`, `:114-118`; `backend/open_webui/retrieval/vector/dbs/milvus_multitenancy.py:72`, `:97-99` |

Which vector store production uses is **TO BE CONFIRMED** (ground truth). The admin **Reset
Upload Directory** and **Reset Vector Storage/Knowledge** actions in the Documents "Danger Zone"
affect the vector store as a whole: **Reset Vector Storage/Knowledge** resets the entire vector
store, memory copies included, and deletes all knowledge records
(`backend/open_webui/routers/retrieval.py:3271-3278`), and the upload reset is recorded as also
wiping memory vectors (`_research-notes.md`, product defect 9; detail in
`rag-retrieval-embeddings-and-vector-stores.md` and `files-uploads-and-storage.md`). Memory rows survive either reset; only the search copies go,
until a **Reindex** rebuilds them (section 5.10).

### 6.3 Where the Switches Are Stored

| Value | Stored in | Source |
|---|---|---|
| The person's **Memory** switch | `memory` inside the `ui` part of the user's `settings` JSON | `src/lib/components/chat/Settings/Personalization.svelte:137`; `src/lib/components/chat/SettingsModal.svelte:438-441`; `backend/open_webui/models/users.py:832-846` |
| Site switches, review settings and limits | Six rows in the `config` table (section 7) | `backend/open_webui/config.py:2844-2849` |
| The **Memories** permission | `features.memories` inside the `user.permissions` setting (defaults) and each group's `permissions` | `backend/open_webui/config.py:2012`; ground truth |
| The model's **Memory** capability and tool group | `meta.capabilities.memory` and `meta.builtinTools.memory` in the model's settings record | `backend/open_webui/utils/memory.py:286-287`; `backend/open_webui/utils/tools.py:533-540` |

### 6.4 Migrations That Shaped the Table

| Revision | Date in file | Change | Source |
|---|---|---|---|
| `7e5b5dc7342b` (initial schema) | n/a | `memory` with `id`, `user_id`, `content`, `updated_at`, `created_at` | `backend/open_webui/migrations/versions/7e5b5dc7342b_init.py:95-105` |
| `a0b1c2d3e4f5` | 2025-09-15 | Index `ix_memory_user_id` | `backend/open_webui/migrations/versions/a0b1c2d3e4f5_add_memory_user_id_index.py:1-28` |
| `3ff2c63645b8` | 2026-06-17 | Settings reshaped to one row per key; `memories.enable` carried over from `ENABLE_MEMORIES` | `backend/open_webui/migrations/versions/3ff2c63645b8_reshape_config_to_per_key_rows.py:142` |
| `7b3f2a9c1d4e` | 2026-06-25 | Column `type` (existing rows become `context`) and index `ix_memory_type` | `backend/open_webui/migrations/versions/7b3f2a9c1d4e_add_memory_type.py:21-31` |
| `42e2978c7933` | 2026-06-29 | Columns `path` and `meta` | `backend/open_webui/migrations/versions/42e2978c7933_add_memory_path_and_meta.py:21-29` |
| `55f1302ac17c` | 2026-07-24 | Covering index `ix_memory_id_user_id` | `backend/open_webui/migrations/versions/55f1302ac17c_add_memory_id_user_id_covering_index.py:21-27` |
| `461111b60977` | (see file) | Adds a primary key on `memory.id` where a legacy database lacked one | `backend/open_webui/migrations/versions/461111b60977_add_missing_primary_keys_to_legacy_.py:31` |

No migration in this area is local to the fork (section 12).

## 7. Settings and Configuration

### 7.1 Persistent Settings

Each is a row in the `config` table, seeded from the environment variable at first boot; after
that the stored value wins and changing the variable has no effect (ground truth). **Live values
are data, TO BE CONFIRMED.**

| Setting key | Environment variable (first boot) | Code default | Where an admin changes it | Effect | Source |
|---|---|---|---|---|---|
| `memories.enable` | `ENABLE_MEMORIES` | on | Admin Settings › General › **Memories** | Master switch for the whole area (3.3) | `backend/open_webui/config.py:426`, `:2844` |
| `memories.system_context.enable` | `ENABLE_MEMORY_SYSTEM_CONTEXT` | on | Admin Settings › General › **Memory System Context** | Whether memories are added to every request (5.6) | `backend/open_webui/config.py:427`, `:2845` |
| `memories.background_review.enable` | `ENABLE_MEMORY_BACKGROUND_REVIEW` | **off** | No screen; only through **Import Config** or database work | Whether the background review runs (5.8) | `backend/open_webui/config.py:428`, `:2846` |
| `memories.review_interval_turns` | `MEMORIES_REVIEW_INTERVAL_TURNS` | 10 | No screen | Review every Nth message the person sends (minimum 1) | `backend/open_webui/config.py:429`, `:2847`; `backend/open_webui/utils/memory.py:440-443` |
| `memories.user_char_limit` | `MEMORIES_USER_CHAR_LIMIT` | 2000 | No screen | Length cap of `[User Memory]` (minimum 250) | `backend/open_webui/config.py:430`, `:2848`; `backend/open_webui/utils/memory.py:376-379` |
| `memories.context_char_limit` | `MEMORIES_CONTEXT_CHAR_LIMIT` | 2000 | No screen | Length cap of the other two parts together (minimum 250) | `backend/open_webui/config.py:431`, `:2849`; `backend/open_webui/utils/memory.py:380-383` |
| `features.memories` inside `user.permissions` | `USER_PERMISSIONS_FEATURES_MEMORIES` | on | Users › Groups › **Default permissions** (and per group) | The **Memories** permission (3.1) | `backend/open_webui/config.py:1926`, `:2012` |
| `rag.relevance_threshold` (shared with document search) | `RAG_RELEVANCE_THRESHOLD` | 0.0 | Admin Settings › Documents (see `rag-retrieval-embeddings-and-vector-stores.md`) | Drops weak similarity matches from `[Relevant Context]` when above 0 | `backend/open_webui/config.py:970`, `:2901`; `backend/open_webui/routers/memories.py:362-386` |

The embedding model and engine (Admin Settings › Documents) decide how search copies are made;
changing them calls for a **Reindex** (5.10). They are documented in
`rag-retrieval-embeddings-and-vector-stores.md`.

**Reading and changing the four keys without a screen.** An admin can read all six keys with
Admin Settings › **Database** › **Export Config** ("Download the current admin configuration as
JSON.", `/admin/settings/db`) and change them with **Import Config** ("Import admin configuration
from a JSON export file."), which writes whatever keys the file contains
(`src/lib/components/admin/Settings/Database.svelte:60-120`;
`backend/open_webui/routers/configs.py:100-125`; `src/lib/i18n/locales/en-US/translation.json:2187-2190`).
The export contains every stored setting, including provider keys and other secrets (ground
truth), so the file must be handled as a secret. Tier 1 does neither.

The three numeric variables are read with `int(...)` when the settings module loads, so a
non-numeric value in one of them would stop the server from starting
(`backend/open_webui/config.py:429-431`; read from code).

### 7.2 Environment-Only Settings

None specific to memories. The general switches `ENABLE_PERSISTENT_CONFIG` and
`RESET_CONFIG_ON_START` change where all six keys come from (ground truth).
`ENABLE_RETRIEVAL_UNSCOPED_COLLECTIONS` does not affect memory collections, which are always
limited to their owner for non-admins (`backend/open_webui/env.py:835-839`;
`backend/open_webui/retrieval/utils.py:1342-1344`).

### 7.3 Limits Fixed in Code

| Limit | Value | Source |
|---|---|---|
| Number of memories per person | None | `backend/open_webui/routers/memories.py:183-231` |
| Length of one memory | None (empty text refused) | `backend/open_webui/utils/memory.py:21-25` |
| Search text for injection | Last 7 non-empty messages from the person, last 4,000 characters | `backend/open_webui/utils/memory.py:294-306` |
| Similarity results for injection | 8 | `backend/open_webui/utils/memory.py:315` |
| Neighbourhood | Up to 6 matching paths, up to 4 memories each | `backend/open_webui/utils/memory.py:230`, `:328-334` |
| Character limits | Minimum 250 each; 0 or unreadable means 2,000 | `backend/open_webui/utils/memory.py:375-383` |
| Review: existing memories shown to the model | First 80 | `backend/open_webui/utils/memory.py:484-488` |
| Review: conversation shown to the model | Last 16 messages; any over 1,600 characters cut to first 1,000 and last 400 | `backend/open_webui/utils/memory.py:494-511` |
| Event preview of a memory | First 300 characters | `backend/open_webui/routers/memories.py:229`, `:312`, `:600` |
| Word search route | Default 20, between 1 and 100 | `backend/open_webui/routers/memories.py:103`; `backend/open_webui/utils/memory.py:128` |
| Path list route | Default 100, at most 500 paths; 20 child paths each | `backend/open_webui/routers/memories.py:109`; `backend/open_webui/utils/memory.py:173`, `:176` |
| Path read route | Default 50, at most 100 memories; 50 child paths | `backend/open_webui/routers/memories.py:116`; `backend/open_webui/utils/memory.py:225-226` |
| Search box in Settings | 500 characters | `src/lib/components/chat/Settings/Personalization.svelte:167` |

Because there is no count limit, a very large collection affects only what fits in the memory
context and what the review sees (the first 80); nothing reports "memory full".

### 7.4 Per-Model and Per-Person Controls

| Control | Where | Default | Effect | Source |
|---|---|---|---|---|
| **Memory** capability | Model editor › Capabilities | on | Off: no memory context, no review, no memory tools for that model | `src/lib/constants.ts:126`; `backend/open_webui/utils/memory.py:286-287`; `backend/open_webui/utils/tools.py:661` |
| **Memory** built-in tool group | Model editor › Builtin Tools | on | Off: no memory tools for that model (context and review unaffected) | `backend/open_webui/utils/tools.py:538-540`, `:658` |
| Personal **Memory** switch | Settings › Personalization | follows the site switch until set | Off: the chat page stops asking for memory | `src/lib/components/chat/Settings/Personalization.svelte:100`, `:134-139`; `src/lib/components/chat/Chat.svelte:3412-3414` |

## 8. Cron Jobs and Background Processes

There is no scheduled job, startup loop or Redis listener for memories: none of the seven loops
started at startup concerns them (inventory, "Background loops started at startup"), and nothing
in the memory modules runs on a timer. Everything happens either at save time or right after a
reply:

| What | When it runs | Where it runs | How to tell it ran | Source |
|---|---|---|---|---|
| Making a search copy | At save time, inside the add, edit and batch requests | The worker that handled the request | The request succeeds; no separate signal | `backend/open_webui/routers/memories.py:207-222`, `:264-287`, `:577-593` |
| Automatic rebuild after an embedding-size mismatch | At save time, when the vector store reports a dimension mismatch | Same request | Log warning `Memory vector dimension mismatch for user {user_id}; reindexing memory vectors.` | `backend/open_webui/routers/memories.py:171-180` |
| Memory context for a request | Before each request goes to the model | The worker handling the chat | Nothing visible (5.6) | `backend/open_webui/utils/middleware.py:2683-2698` |
| Background memory review (off by default) | After a reply, every Nth message the person sends; started as a separate asyncio task so the reply is not delayed | The worker that handled the chat; no queue, no Redis | Only indirectly: new or changed memories (with `created_by: background_review` in the database) and `memory.*` events; failures logged at debug level as `Memory review failed: {e}` | `backend/open_webui/utils/memory.py:410-471` |
| Admin **Reindex** | When the admin confirms, as one long request | The worker that handled it | Toast "Success"; one `memory.reset` event with totals | `backend/open_webui/routers/memories.py:449-480` |

**Single worker versus several.** No memory step keeps state in a worker's memory between
requests: rows are in the database and copies in the vector store, so the behaviour is the same
with one worker or several. A review task that is running when its worker stops is lost (it is
an in-process task, `backend/open_webui/utils/memory.py:453`).

**A log line support may see.** For every new chat, the server's first title generation runs the
background-task step without the model in its context, so the memory review call fails with a
`KeyError` and the log shows `Error generating initial chat title`, even though the title was
saved (`backend/open_webui/main.py:1471-1492`; `backend/open_webui/utils/middleware.py:4038-4041`;
`_research-notes.md`, product defect 1). The review itself is not lost: the normal end-of-reply
step runs it with the model present (`backend/open_webui/utils/middleware.py:4378-4385`,
`:6582-6590`). Read from code; confirm in a test environment.

## 9. Notifications and Emails

The application sends no email (ground truth). Memory changes produce no in-app or browser
notification: the person learns of a change made by the model only from the tool-call entry in the
reply (5.7), and of a change made by the background review not at all until they open Settings ›
Personalization. The memory events are not in the notification list
(`backend/open_webui/events.py:669-675`).

### 9.1 Application Events

Memory routes publish events to every event sink: admin-configured event webhooks and Event
functions (and, for listed event types only, notifications) (`backend/open_webui/events.py:1069-1071`,
`:1083-1086`, `:1166-1171`, `:1198-1202`). A webhook with no event filter receives all events,
memory events included (`backend/open_webui/events.py:712-713`). The webhook message is the
event's message plus the subject id in brackets, for example `Memory created ({memory_id})`
(`backend/open_webui/events.py:1034-1056`).

| Event | Message | Published when | Subject | Data | Source |
|---|---|---|---|---|---|
| `memory.created` | `Memory created` | A memory is added in Settings, by `add_memory`, or by an `add` operation from `update_memory` or the review | The memory id | First 300 characters of the text, type, path (and `operation` for batch writes) | `backend/open_webui/events.py:335-337`; `backend/open_webui/routers/memories.py:224-230`, `:297-317` |
| `memory.updated` | `Memory updated` | A memory is edited in Settings or by `replace_memory_content`, or replaced or moved by a batch | The memory id | As above | `backend/open_webui/events.py:338-340`; `backend/open_webui/routers/memories.py:299-300`, `:595-601` |
| `memory.deleted` | `Memory deleted` | **Remove**, **Clear memory**, or a batch `remove` | The memory id; for **Clear memory**, the person's user id | None (batch removals carry an empty preview) | `backend/open_webui/events.py:341-343`; `backend/open_webui/routers/memories.py:301-317`, `:531-537`, `:623-628` |
| `memory.reset` | `Memory reset` | Admin **Reindex** (subject `all`, with memory and user counts) or a person's own reset route | `all` or the user id | Count of memories rebuilt; `reindex: true` | `backend/open_webui/events.py:344-346`; `backend/open_webui/routers/memories.py:472-479`, `:500-507` |

Every event also carries the acting person's id, name, email and role
(`backend/open_webui/events.py:704`, `:974-985`). The `delete_memory` tool publishes no event
(`backend/open_webui/tools/builtin.py:1068-1076`). Which webhooks and Event functions production
has configured is **TO BE CONFIRMED**; the event system is described in the events area.

### 9.2 Live Updates

There is no socket event for memories. Tool calls that touch memories stream into the reply like
any tool call (see `builtin-native-tools.md` section 9.2). The Settings list does not refresh by
itself; it reloads when the tab is opened or after an action in it
(`src/lib/components/chat/Settings/Personalization.svelte:51-59`, `:99-102`).

## 10. Error, Warning and Notice Messages (Verbatim)

How memory messages reach people:

- **Settings › Personalization and the memory dialog** show a refusal from the server as a red
  toast holding only the server's `detail` text (`src/lib/apis/memories/index.ts:14-26`;
  `src/lib/components/chat/Settings/Personalization.svelte:54-56`, `:72-75`, `:300-303`;
  `src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:37-40`). When the server
  fails without a readable reason (an unhandled error, a proxy error page or a network failure)
  the browser gets no text and shows nothing at all (10.6).
- **Memory tools** return text to the model, which the person can read in the tool-call entry's
  **Output** (hidden while **Hide Processing Details** is on, section 12). The tools call the
  route functions directly and return the exception's text, so a refusal from 10.3 arrives with
  its HTTP status in front, as `{"error": "{status_code}: {detail}"}`, for example
  `{"error": "400: Invalid memory path"}` (`backend/open_webui/tools/builtin.py:40-62`, `:827-828`,
  `:959-960`, `:1000-1001`, `:1049-1050`). That form comes from the web framework's exception
  text (FastAPI `0.136.3`, `pyproject.toml:9`, on Starlette `1.3.1`, `uv.lock:5016-5017`).
- **A program calling the API** receives JSON `{"detail": "<text>"}` with the status code.
- **The background review** shows nothing to anyone; its failures are debug-level log lines (10.7).

Already catalogued in `builtin-native-tools.md` and not repeated here: `Request context not
available` (every memory tool except `list_memory_paths` and `read_memory_path`), `Memory
{memory_id} deleted` and `Memory not found or access denied` (`delete_memory`) in its section
10.3, the **Memory** built-in tool group's label and description in its section 10.2, and the
raw-exception rule for crashes inside a tool (its section 10.3 introduction).

### 10.1 Screen Text in Settings › Personalization and the Memory Dialog

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Personalization` | Tab name and heading | `src/lib/components/chat/SettingsModal.svelte:149`, `:664`; `src/lib/components/chat/Settings/Personalization.svelte:113`; `src/lib/i18n/locales/en-US/translation.json:3007` | Listed in Settings under "Preferences" when the site switch and the permission allow it (3.2) | none | Tab missing: 11.3 |
| `Memory` | Section title and switch label | `src/lib/components/chat/Settings/Personalization.svelte:118`, `:130`; `src/lib/i18n/locales/en-US/translation.json:3003`, `:3006` | Shown whenever the tab is open | Flip it to turn memory on or off for yourself | 5.1 |
| `Experimental` / `This is an experimental feature, it may not function as expected and is subject to change at any time.` | Badge (shown in capitals) / tooltip | `src/lib/components/common/ExperimentalBadge.svelte:12-15`, `:19-22`; `src/lib/components/chat/Settings/Personalization.svelte:131` | Next to the **Memory** switch; the tooltip on hover | none | none |
| `You can personalize your interactions with LLMs by adding memories through the 'Manage' button below, making them more helpful and tailored to you.` | Description | `src/lib/components/chat/Settings/Personalization.svelte:121-127`; `src/lib/i18n/locales/en-US/translation.json:3001-3002` | Under the switch. The screen replaces the word `Manage` with `Add Memory`, so people read "… through the 'Add Memory' button below …"; that button is inside the **Actions** menu | Open **Actions** › **Add Memory** | none |
| `Saved Memories` (followed by a number) | Label | `src/lib/components/chat/Settings/Personalization.svelte:146-149`; `src/lib/i18n/locales/en-US/translation.json:3005` | The person's **Memory** switch is on | none | The number is how many memories loaded; it is also 0 after a failed load (10.6) |
| `Search Memories` | Placeholder | `src/lib/components/chat/Settings/Personalization.svelte:162-167` | At least one memory exists | Type to filter (500 characters at most) | none |
| `Clear search` | Button name (read by screen readers) | `src/lib/components/chat/Settings/Personalization.svelte:171-174` | Text is in the search box | none | none |
| `Actions` | Menu button and its tooltip | `src/lib/components/chat/Settings/Personalization.svelte:189`, `:194` | The person's **Memory** switch is on | Opens **Add Memory** and **Clear memory** | none |
| `Add Memory` | Menu item and dialog title | `src/lib/components/chat/Settings/Personalization.svelte:210`; `src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:60-61` | As above | none | none |
| `Clear memory` | Menu item, greyed out when there are no memories | `src/lib/components/chat/Settings/Personalization.svelte:213-224`; `src/lib/i18n/locales/en-US/translation.json:3000` | As above | Opens the **Clear Memory** confirmation | Permanent (5.5) |
| `Memories accessible by LLMs will be shown here.` | Empty state | `src/lib/components/chat/Settings/Personalization.svelte:231-234`; `src/lib/i18n/locales/en-US/translation.json:3004` | No memories were loaded: the person has none, **or the list failed to load** without a readable reason (10.6) | none | 11.5 |
| `No results found` | Empty state | `src/lib/components/chat/Settings/Personalization.svelte:235-236` | Memories exist but none matches the search text | Clear the search | none |
| `Edit` / `Remove` | Buttons beside each memory | `src/lib/components/chat/Settings/Personalization.svelte:249-262` | Each listed memory | none | none |
| `Save` | Button | `src/lib/components/chat/Settings/Personalization.svelte:274-281` | Bottom of the tab | It only shows a toast (10.2); the switch saves itself | none |
| `Clear Memory` / `Are you sure you want to clear all memories? This action cannot be undone.` | Confirmation | `src/lib/components/chat/Settings/Personalization.svelte:284-292` | **Actions** › **Clear memory** | **Confirm** deletes every memory; **Cancel** keeps them | Permanent (5.5) |
| `Delete Memory?` / `Are you sure you want to delete this memory? This action cannot be undone.` | Confirmation, with the memory's text shown beneath | `src/lib/components/chat/Settings/Personalization.svelte:294-323` | **Remove** | As above | Permanent (5.5) |
| `Cancel` / `Confirm` | Buttons of both confirmations | `src/lib/components/common/ConfirmDialog.svelte:21-22`, `:200`, `:209` | As above | none | none |
| `Edit Memory` | Dialog title | `src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:58-59` | **Edit** | none | none |
| `Type` / `User` / `Context` | Label / toggle | `src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:74-88` | In the dialog | Click the word to switch the type (4.2) | none |
| `Add a preference, fact, or instruction about you` | Placeholder | `src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:96-97` | Type is **User** | none | none |
| `Add durable context for future chats` | Placeholder | `src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:98` | Type is **Context** | none | none |
| `Path` / `optional` | Label shown as "Path (optional)", and placeholder | `src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:102-111` | In the dialog | An optional grouping label (4.1) | none |
| `Add` / `Update` | Button; a spinner shows and the button is disabled while saving | `src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:117-136` | Adding or editing | none | Spinner, then nothing: 10.6 |

### 10.2 Toasts on the Personalization Screens

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Memory added successfully` | Success | `src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:42-48` | The add request returned the new memory; the dialog closes and the list reloads | none | none |
| `Memory updated successfully` | Success | `src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:42-48` | The edit request returned the memory | none | none |
| `Memory deleted successfully` | Success | `src/lib/components/chat/Settings/Personalization.svelte:305-308` | The server deleted the memory (answered `true`); the list reloads | none | none |
| `Memory cleared successfully` | Success | `src/lib/components/chat/Settings/Personalization.svelte:77-80` | The server answered `true` and the list had memories in it | none | Copies outside the table remain (5.5) |
| `Settings saved successfully!` | Success | `src/lib/components/chat/SettingsModal.svelte:825-831`; `src/lib/components/chat/Settings/Personalization.svelte:105-111` | **Save** on the tab. Nothing is saved by it; the **Memory** switch was saved when flipped | none | none |

Flipping the **Memory** switch when the save fails shows the personal-settings route's own error
text in a red toast (`src/lib/components/chat/SettingsModal.svelte:438-444`); that route belongs to
`user-settings-and-personalisation.md` and `users-groups-roles-and-permissions.md`.

### 10.3 Server Messages from the Memory Routes

In Settings the toast shows the text alone; in a tool-call entry the **Output** shows it as
`{"error": "{status_code}: {detail}"}` (see the introduction to this section).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Memory content cannot be empty` | Error (400) | `backend/open_webui/utils/memory.py:21-25`, called from `backend/open_webui/routers/memories.py:197`, `:561` and `backend/open_webui/utils/memory.py:261`, `:267` | The text is empty or only spaces: **Add** or **Update** in the dialog, `add_memory`, `replace_memory_content`, or an `add` or `replace` operation in `update_memory` or the review | Type the memory's text | none |
| `Invalid memory path` | Error (400) | `backend/open_webui/utils/memory.py:28-35`, called from `backend/open_webui/routers/memories.py:198`, `:562` and `backend/open_webui/utils/memory.py:39`, `:108`, `:187`, `:263`, `:270`, `:274` | A part of the path is `.` or `..`, or the path contains a control character such as a tab. Extra, leading and trailing slashes are not errors; they are tidied away | Remove the `.` or `..` part | none |
| `Memory path is required` | Error (400) | `backend/open_webui/utils/memory.py:187-189` | `read_memory_path` (or `POST /api/v1/memories/path`) with an empty path | none (the model retries) | none |
| `No memory operations provided` | Error (400) | `backend/open_webui/utils/memory.py:251-253` | `update_memory` (or `POST /api/v1/memories/update`) with an empty list. The review skips the call when it has no operations (`backend/open_webui/utils/memory.py:522`) | none | none |
| `Memory id is required for replace` / `Memory id is required for move` / `Memory id is required for remove` | Error (400) | `backend/open_webui/utils/memory.py:264-277` | A batch operation names no memory id | none (the model retries) | none |
| `Unsupported memory operation: {action}` | Error (400); not reachable in practice | `backend/open_webui/utils/memory.py:278-279`; the same words as an internal error at `backend/open_webui/models/memories.py:260-261` | Only `add`, `replace`, `move` and `remove` pass the form check (`backend/open_webui/routers/memories.py:85-86`), so any other action is refused earlier with the validation error below | none | none |
| `Memory not found: {memory_id}` | Error (404) | `backend/open_webui/models/memories.py:219-221`, `:238-240`, `:253-255`; returned by `backend/open_webui/routers/memories.py:255-258` | A `replace`, `move` or `remove` operation names an id that is not one of the person's memories (deleted meanwhile, mistyped by the model, or someone else's). Read from code: the whole batch is then abandoned before its commit, so earlier operations in it are not saved either (`backend/open_webui/models/memories.py:263`; `backend/open_webui/internal/db.py:519-535`) | Ask the model to list the memories again | none |
| `No memory update provided` | Error (400) | `backend/open_webui/routers/memories.py:563-564` | `POST /api/v1/memories/{memory_id}/update` with no text, type or path. The dialog and `replace_memory_content` always send text, so people do not normally see it | none | none |
| `We could not find what you're looking for :/` | Error (404) | `backend/open_webui/constants.py:78`; raised at `backend/open_webui/routers/memories.py:37-41` and `:574-575` | (a) **Update** in the dialog, or `replace_memory_content`, for a memory that no longer exists or is not the person's (a database error during the update gives the same answer, `backend/open_webui/models/memories.py:105-106`); (b) any memory action after an admin switched **Memories** off while the person's page was still open (the tab disappears only after a reload, because the browser reads the site settings when the app loads, `src/routes/+layout.svelte:1269`, `:1281-1290`) | (a) Close the dialog and reopen the tab; (b) reload the page | For (b), memory is off for the whole site (3.3) |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (403) | `backend/open_webui/constants.py:70-72`; raised at `backend/open_webui/routers/memories.py:43-47` | A non-admin without the **Memories** permission uses a memory route; in Settings this happens when the permission was removed while the page was open (the tab is hidden after a reload, `src/routes/+layout.svelte:1281-1287`). The same text with HTTP 401 refuses accounts that are not `user` or `admin` (ground truth) | Reload; ask an admin whether memory should be available | The person's groups and the default permissions (3.1) |
| `No memories found for user` | Error (404); not shown to people | `backend/open_webui/routers/memories.py:344-346` | `POST /api/v1/memories/query` when the person has no memories. The memory context step ignores it (`backend/open_webui/utils/memory.py:312-317`) and no screen calls the route | none | none |
| `{count} validation error for UpdateMemoriesForm` (plural `errors` when several; framework-generated text listing the field and the accepted values) | Error (HTTP 422 for an API caller) | `backend/open_webui/routers/memories.py:73-116`; `backend/open_webui/tools/builtin.py:993-997`; `backend/open_webui/utils/memory.py:525` | A memory operation with a value the forms refuse, for example a `type` other than `user` or `context` in `update_memory` or in the review's answer. The whole batch is refused (4.2). Other forms give the same kind of text under their own names (`AddMemoryForm`, `SearchMemoriesForm`, …) | none (the model usually retries) | For the review, only the debug log shows it (10.7) |

### 10.4 Memory Tool Results Not Listed in the Built-In Tools Document

These are what a person sees in a memory tool-call entry's **Output** when the call worked; each
result also carries the memory's own values.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `"status": "success"` with the new memory's `id`, `type` and `path` | Success | `backend/open_webui/tools/builtin.py:948-957` | `add_memory` saved a memory | Check it in Settings › Personalization | none |
| `"status": "success"` with `id`, `type`, `path` and the new `content` | Success | `backend/open_webui/tools/builtin.py:1027-1047` | `replace_memory_content` changed a memory | As above | none |
| `"status": "created"`, `"status": "updated"`, `"status": "deleted"` (one entry per operation, with its `"action"`) | Success | `backend/open_webui/models/memories.py:212-258`; `backend/open_webui/routers/memories.py:264-284` | `update_memory` applied its operations | As above | none |
| `"status": "skipped"` with `"reason": "duplicate"` | Notice | `backend/open_webui/models/memories.py:185-198` | An `add` whose text, type and path match an existing memory; nothing new is saved | none | Not an error |
| `[]` | Notice | `backend/open_webui/tools/builtin.py:901-902`, `:1115-1116` | `search_memories` found nothing, or `list_memories` with no memories | none | none |

### 10.5 Admin and Model-Editor Text

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Memories` / `Allow users to save memories for more personalized responses.` | Label / description | `src/lib/components/admin/Settings/General.svelte:315-321`; `src/lib/i18n/locales/en-US/translation.json:2390-2391` | Admin Settings › General | Admin only | 7.1 |
| `Memory System Context` / `Include saved memories in the system context.` | Label / description | `src/lib/components/admin/Settings/General.svelte:322-333`; `src/lib/i18n/locales/en-US/translation.json:2392-2393` | Shown only while **Memories** is on | Admin only | 7.1 |
| `Features Permissions` / `Memories` | Section heading / switch label | `src/lib/components/admin/Users/Groups/Permissions.svelte:960`, `:1101-1104` | Default permissions and each group's permissions | Admin only | 3.1 |
| `This is a default user permission and will remain enabled.` | Notice | `src/lib/components/admin/Users/Groups/Permissions.svelte:1106-1112` | A group's **Memories** switch is off while the default permission is on | none | A group cannot take away a default (3.1) |
| `Reindex Knowledge and Memory Vectors` / `Rebuild vectors for existing knowledge files, knowledge search, and memories.` / `Reindex` | Label / description / button | `src/lib/components/admin/Settings/Documents.svelte:1576-1590`; `src/lib/i18n/locales/en-US/translation.json:2317-2319` | Admin Settings › Documents, "Danger Zone" | Admin only | 5.10 |
| `Reindex Embedding Data` / `Rebuild knowledge file, knowledge search, and memory vectors using the current embedding model.` | Confirmation | `src/lib/components/admin/Settings/Documents.svelte:382-387` | **Reindex** | **Confirm** starts the three steps | 5.10 |
| `After changing the embedding model, reindex knowledge, knowledge search, and memory vectors for changes to take effect.` | Notice | `src/lib/components/admin/Settings/Documents.svelte:1167-1171`; `src/lib/i18n/locales/en-US/translation.json:139` | Under the embedding model field | Reindex after changing the model | 5.10 |
| `Success` | Success toast | `src/lib/components/admin/Settings/Documents.svelte:412-414` | The memory step, the last of the three, finished | none | One `memory.reset` event (9.1) |
| `Memory` / `Inject stored memories into conversation context` | Capability label / description | `src/lib/components/workspace/Models/Capabilities.svelte:53-56`; `src/lib/i18n/locales/en-US/translation.json:2585-2586` | Model editor › Capabilities | Model owners and admins | 7.4 |

Errors while saving Admin Settings › General (for example `Failed to update settings`,
`src/lib/components/admin/Settings/General.svelte:90`) belong to the whole screen and are catalogued
with the admin settings panels (`admin-settings-panels.md`).

### 10.6 Outcomes with No Message

Read from code. These matter because the person sees nothing, or sees something misleading.

| What the person does | What happens | What they see | Source |
|---|---|---|---|
| **Add** or **Update** while the embedding engine or vector store fails | Add: the memory is saved without a search copy. Update: the new text is saved, the old search copy stays | The spinner stops, the dialog stays open, no toast. Pressing **Add** again saves a second copy | `backend/open_webui/routers/memories.py:199-222`, `:565-593`; `src/lib/apis/memories/index.ts:47-59`; `src/lib/components/chat/Settings/Personalization/MemoryModal.svelte:30-50` |
| Opens the tab while the list request fails without a readable reason | Nothing is lost | No toast; **Saved Memories** shows 0 and `Memories accessible by LLMs will be shown here.`, exactly as if the person had no memories | `src/lib/apis/memories/index.ts:14-28`; `src/lib/components/chat/Settings/Personalization.svelte:51-59`, `:231-234` |
| **Remove** when the server answers `false` (the memory is already gone or is not the person's) | Nothing is deleted | The dialog closes with no toast; the list is not reloaded, so the memory stays on screen until the tab is reopened | `backend/open_webui/routers/memories.py:619-631`; `src/lib/components/chat/Settings/Personalization.svelte:297-310` |
| **Remove** when the vector store reports an error after the row was deleted (the default Chroma store ignores delete errors, `backend/open_webui/retrieval/vector/dbs/chroma.py:184-194`) | The memory is deleted; its search copy may remain | As in the row above | `backend/open_webui/routers/memories.py:619-622` |
| **Clear memory** when the database delete fails | Nothing is deleted | The dialog closes with no toast; the list still shows the memories | `backend/open_webui/models/memories.py:145-153`; `backend/open_webui/routers/memories.py:524-540`; `src/lib/components/chat/Settings/Personalization.svelte:71-82` |
| **Clear memory** when the collection delete fails | The memories are deleted; their search copies remain (an error is logged) | `Memory cleared successfully`, as normal | `backend/open_webui/routers/memories.py:526-530` |
| Flips the **Memory** switch and the save fails | Not saved | An error toast; the switch keeps its new position until the tab is reopened, when it shows the saved value again | `src/lib/components/chat/Settings/Personalization.svelte:100`, `:134-139`; `src/lib/components/chat/SettingsModal.svelte:438-450` |
| Admin **Reindex** when the memory step fails without a readable reason | Some or none of the collections are rebuilt | Neither an error nor `Success` | `src/lib/components/admin/Settings/Documents.svelte:407-414`; `src/lib/apis/memories/index.ts:131-157` |
| The model saves, changes or deletes a memory | Done | Only the tool-call entry in the reply (hidden while **Hide Processing Details** is on); no toast or notification | section 9; section 12 |
| The background review changes memories, or fails | Changes are saved, or nothing happens | Nothing in the chat; the changes appear in Settings › Personalization | `backend/open_webui/utils/memory.py:453-471`, `:522-525` |

### 10.7 Server Log Lines (Not Shown to Users)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Memory vector dimension mismatch for user {user_id}; reindexing memory vectors.` | Warning | `backend/open_webui/routers/memories.py:171-180` | Saving a memory found search copies of another size (the embedding model changed); that person's copies are rebuilt at once | none | A site-wide **Reindex** is probably due (5.10) |
| `Memory review failed: {e}` | Debug, so hidden unless `GLOBAL_LOG_LEVEL` is `DEBUG` (when it is unset, the level is `INFO`, `backend/open_webui/env.py:113-124`) | `backend/open_webui/utils/memory.py:465-471` | The background review raised an error: the model could not answer, the batch was refused (a validation error or `Memory not found: {memory_id}`), or the embedding failed | none | Visible only in debug logs |
| `list_memory_paths error: {e}`, `read_memory_path error: {e}`, `search_memories error: {e}`, `add_memory error: {e}`, `update_memory error: {e}`, `replace_memory_content error: {e}`, `delete_memory error: {e}`, `list_memories error: {e}` | Error, with a traceback | `backend/open_webui/tools/builtin.py:827`, `:861`, `:919`, `:959`, `:1000`, `:1049`, `:1081`, `:1118` | Any failure inside that memory tool, including the refusals in 10.3 | none | Match the time of the tool-call entry |
| The vector store's own error text (no fixed wording) | Error | `backend/open_webui/routers/memories.py:529-530` | **Clear memory** could not delete the person's collection | none | Escalate: search copies may remain (5.5) |
| The error text alone, at debug level | Debug | `backend/open_webui/routers/memories.py:137-138` (collection delete before a rebuild); `backend/open_webui/utils/memory.py:316-317` (the similarity search for the memory context, including `404: No memories found for user`) | As stated | none | none |

The `Error generating initial chat title` line that the review step causes for new chats is
explained in section 8.

### 10.8 Event Texts Sent to Webhooks

The four memory event messages (`Memory created`, `Memory updated`, `Memory deleted`, `Memory
reset`) and when each is published are in 9.1. A webhook receives the message with the subject id
in brackets and, as its description, `A memory was created.`, `A memory was updated.`, `A memory
was deleted.` or `A memory was reset.` (`backend/open_webui/events.py:335-346`, `:1034-1056`).

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it explains, checks what the person can see, and escalates. It does not
change anyone's memories, settings, permissions or the site's switches; where a fix is needed, the
person changes their own memories themselves, or an admin acts. Memories can hold personal or
health details: **never copy a memory's text into a ticket, chat or email**; describe it in general
terms (for example "a memory about a medical appointment"). Useful evidence for any escalation:
the person's account (sign-in email), the model's name, the time, and the chat's id for anything
that happened in a chat (how to find it: `builtin-native-tools.md` section 11).

What tier 1 has no screen for: memory text, type or who created a memory (`created_by` is not shown
anywhere, section 4.1), the site's memory settings, and the server logs. Admins have no screen for
another person's memories either (section 3.4).

### 11.1 "It remembered something I didn't want saved"

**Symptom.** A later reply mentions something personal the person did not mean to keep, or they
find it in Settings › Personalization.

**Likely causes, in order.**
1. The model saved it with a memory tool (`add_memory` or `update_memory`) during an earlier reply.
   With the default **Full access** tool mode nothing asks first, and the tool descriptions say
   nothing about health or other sensitive details (section 5.7;
   `backend/open_webui/tools/builtin.py:930-936`, `:968-975`).
2. The background memory review saved it after a reply, if an admin has turned the review on (code
   default off; section 5.8). Nothing in the chat shows this.
3. The person typed it in **Add Memory**, or asked the model to "remember" it.
4. It was not saved at all: the model found it in another of the person's chats, a note or a file
   through other built-in tools (`builtin-native-tools.md` section 11.14).

**Diagnostic steps.**
1. Ask the person to open Settings › **Personalization** and search for a distinctive word. If it
   is not there, cause 4 applies.
2. Ask whether recent replies show memory tool-call entries (for example `add_memory`). If they
   have **Hide Processing Details** on, those entries are hidden; turning it off in Settings ›
   Interface shows them again in past chats too (section 12).
3. Memories follow the person into every chat, with every model that allows memory (section 1).

**Resolution.**
- The person can **Remove** the memory, or **Clear memory** to remove all of them (section 5.5),
  and can switch **Memory** off to stop memories being used or saved in their chats (section 5.1).
- They can tell the model "forget …"; the model can delete memories itself, and the result can be
  checked in Settings (section 5.7).
- Explain what deletion does and does not reach: earlier replies that listed the memory, webhooks,
  the audit log and the model provider keep their copies (section 5.5).

**Escalation.** If the person wants to know who or what created it, or the information is
sensitive (for example health details) and they want copies outside the memory list dealt with:
the platform maintainer, with the account and the approximate date, and the U of T Privacy Office
(privacy.utoronto.ca) for the privacy question. Whether the background review is on in production
is **TO BE CONFIRMED** (section 14).

### 11.2 "My memories aren't being used" or "It forgot what I told it"

**Symptom.** Replies ignore a saved preference or fact.

**Likely causes, in order.**
1. The person's **Memory** switch is off (the list is hidden too) (section 5.1).
2. The model in use has its **Memory** capability off: no memory context, no memory tools and no
   review for that model (section 7.4). Workspace models can be set this way by their owner.
3. The memory is a **Context** memory, which is added only when it looks related to the last
   seven messages; memories saved before the upgrade that introduced types are all Context
   memories (section 4.2).
4. The person has many or long **User** memories: the `[User Memory]` part is cut at 2,000
   characters by default, and entries are sorted alphabetically before the cut, so the ones that
   sort last are dropped, not the oldest (sections 4.3 and 5.6).
5. An admin has turned **Memory System Context** off: memories are kept and the tab works, but
   nothing is added to requests (the memory tools may still look them up) (section 3.3).
6. The memory's search copy is missing or stale (an embedding failure when it was saved, an
   embedding model change without **Reindex**, or a vector store reset), so a Context memory is
   not found, or found poorly, by similarity. **User** memories are read from the database and do
   not depend on search copies (`backend/open_webui/utils/memory.py:310-326`; sections 5.10 and 6.2).
7. The request did not come from the chat page: automation runs are built without memory, and API
   callers get it only when they ask for it (section 3.2).
8. The model received the memory but did not follow it.
9. Rare: none of the person's messages in the chat has any text (for example a chat whose only
   message is an image), so the memory step adds nothing (`backend/open_webui/utils/memory.py:294-308`).

**Diagnostic steps.**
1. Settings › **Personalization**: is the tab there, is **Memory** on, and is the memory listed?
2. Ask the person to open **Edit** on the memory to read its **Type**, then close the dialog
   without pressing **Update**. Typing `context` in **Search Memories** also lists Context
   memories (and any whose text or path contains that word)
   (`src/lib/components/chat/Settings/Personalization.svelte:84-93`).
3. Ask how many memories are listed and whether some are long.
4. Ask which model was used, and whether a different model (for example a base model rather than
   a workspace model) behaves the same way.
5. Ask whether it happens in a new chat too.

**Resolution.** Guide the person: switch **Memory** on; change an important memory's **Type** to
**User** in **Edit**; shorten, merge or remove outdated User memories; try another model. Each
change applies from the next message (section 5.6).

**Escalation.** To the model's owner (capability) or an admin (**Memory System Context**, the
character limits, a **Reindex** after an embedding change), with the model name and the account.

### 11.3 "I can't find Personalization"

**Symptom.** Settings has no **Personalization** tab, or `/?settings=personalization` opens
**General** instead.

**Likely causes, in order.**
1. The site switch **Memories** is off: the tab is hidden for everyone, admins included (section 3.3).
2. The person lacks the **Memories** permission (code default on; an admin may have turned it
   off in the defaults and granted it only to some groups) (section 3.1).
3. The change was made while the page was open: the browser reads settings and permissions when
   the app loads, so the tab appears or disappears only after a reload (`src/routes/+layout.svelte:1269`, `:1281-1290`).
4. Text in the Settings search box is filtering the tab list (`src/lib/components/chat/SettingsModal.svelte:418-419`, `:536-543`).
5. The person is looking in Admin Settings, or the account is still `pending` and cannot use the
   app (ground truth).

**Diagnostic steps.** Ask the person to reload the page, open the user menu › **Settings**, clear
the search box and look under "Preferences". Ask whether colleagues see the tab (if nobody does,
cause 1; if only some do, cause 2).

**Resolution.** Explain that memory is not available to them at the moment; tier 1 does not turn it
on.

**Escalation.** To an admin, with the account and whether others see the tab: the admin checks
Admin Settings › General › **Memories** and the person's groups and default permissions.

### 11.4 "Memory says it's full"

**Symptom.** The person reports a message saying memory is full, or believes they have reached a
limit.

**Likely causes, in order.**
1. The words came from the model's reply. The code has no "memory full" message, no limit on the
   number of memories and no limit on a memory's length (sections 7.3 and 10); a model can still
   write such a sentence on its own.
2. A screenshot or message from a different application.
3. What the person actually notices is the length cap on the memory context: past 2,000
   characters of User memories (by default) some stop being used (11.2, cause 4).

**Diagnostic steps.** Ask for a screenshot: text inside the reply is the model's own; a toast would
be one of the texts in section 10, none of which mentions a limit. Ask how many memories are
listed and how long they are.

**Resolution.** Explain that there is no storage limit; suggest merging or shortening User
memories, switching less important ones to Context, and removing outdated ones.

**Escalation.** Only if many people are affected by the cap: an admin may decide to change
`memories.user_char_limit` (no screen; section 7.1).

### 11.5 "My memories disappeared"

**Symptom.** Settings › Personalization shows fewer memories than expected, none, or no list at
all.

**Likely causes, in order.**
1. The person's **Memory** switch is off: only the switch and its description show; nothing is
   deleted (section 5.1).
2. The list failed to load and looks empty: no toast, a count of 0 and `Memories accessible by
   LLMs will be shown here.` (section 10.6).
3. The model deleted or replaced them (`delete_memory`, or `remove` or `replace` in
   `update_memory`), or the background review did, if it is on (sections 5.5, 5.7, 5.8).
4. Someone used **Clear memory** on this account (permanent; section 5.5).
5. The **Personalization** tab itself is gone: see 11.3; the memories are kept.
6. The person is in a different account from the one that holds the memories (for example an
   account that was deleted and re-created gets a new id, and the old memories stay attached to the
   old id) (`backend/open_webui/models/auths.py:118`; section 3.4).

**Diagnostic steps.**
1. Is **Memory** on? Reload the page and reopen the tab (rules out cause 2).
2. Ask whether recent chats show memory tool-call entries (turning **Hide Processing Details** off
   shows hidden ones).
3. Ask whether the account was recently deleted and re-created, or whether they have more than
   one account.

**Resolution.** Tier 1 does not restore memories, and the application has no undo (section 5.5).

**Escalation.** To the platform maintainer with the account, roughly when the memories were last
seen, and the ids of chats that showed memory tool calls. A count of the account's memory rows
(not their text) tells whether they still exist. Whether backups allow restoring them is **TO BE
CONFIRMED** (section 14).

### 11.6 "I deleted a memory but it still comes up"

**Symptom.** After **Remove** or **Clear memory**, a reply still uses the information.

**Likely causes, in order.**
1. The same chat still holds it: earlier messages, including memory tool entries that listed it,
   are sent with every new message in that chat (section 5.5; earlier tool calls and their
   results are turned back into messages for the model, `backend/open_webui/utils/middleware.py:2271-2294`).
2. Another copy exists (pressing **Add** twice, or a similar memory under another path or type).
3. The removal did not happen: a failed **Remove** closes the dialog with no message and leaves the
   memory on screen until the tab is reopened (section 10.6).
4. A leftover search copy can still reach the model as `[Relevant Context]` (section 5.5).
5. The information comes from somewhere else: another chat, a note or a file (11.1, cause 4).

**Diagnostic steps.** Reopen the tab and search for a distinctive word; ask the person to try a
new chat.

**Resolution.** Remove any remaining copy; continue in a new chat.

**Escalation.** If the information still appears in a new chat with no copy listed: the platform
maintainer, for an admin **Reindex**, which rebuilds every person's search copies from the table and
so removes leftovers (section 5.10).

### 11.7 "Add Memory just spins and nothing happens"

**Symptom.** After **Add** (or **Update**), the spinner stops, the dialog stays open and no message
appears.

**Likely causes, in order.**
1. The embedding service or the vector store failed. The memory itself was usually saved (an
   edit was saved too), only its search copy is missing or old (section 10.6).
2. The browser lost its connection to the server.

**Diagnostic steps.** Ask the person to close the dialog and reopen the tab, and check whether the
memory is there. Ask them not to press **Add** repeatedly, because each press can save another copy.

**Resolution.** If the memory is listed once, it is kept; as a User memory it is used normally
(section 11.2, cause 6). Duplicates can be removed.

**Escalation.** If it happens repeatedly or to several people: the platform maintainer, with the
time; the embedding set-up is in `rag-retrieval-embeddings-and-vector-stores.md`.

### 11.8 "It says 'Memory content cannot be empty'" or "'Invalid memory path'"

**Symptom.** A red toast when adding or editing a memory.

**Likely causes and resolution.**
- `Memory content cannot be empty`: the text box is empty or holds only spaces. Type the memory.
- `Invalid memory path`: the **Path** has a part that is `.` or `..`, or a hidden control character
  (for example a pasted tab). Retype the path, or leave it empty (the path is optional).
- `We could not find what you're looking for :/` when pressing **Update**: the memory no longer
  exists (for example the model deleted it meanwhile). Close the dialog and reopen the tab. If the
  whole tab reports it, memory has been switched off for the site (11.3).
- `You do not have permission to access this resource. Please contact your administrator for
  assistance.`: the person's **Memories** permission was removed (11.3).

All four are explained in section 10.3.

**Escalation.** Only for the last two, as in 11.3.

### 11.9 "I deleted my chats but it still knows things about me"

**Symptom.** After deleting chats (one by one, or all of them in Settings › Data Controls), replies
still use personal details.

**Likely causes, in order.**
1. Memories are separate from chats: deleting chats does not touch them. Only the memory routes,
   the memory tools and the memory step use the `memory` table (`backend/open_webui/routers/memories.py`,
   `backend/open_webui/tools/builtin.py:795-1119`, `backend/open_webui/utils/memory.py`).
2. The details are in notes, files or knowledge the person still has.

**Diagnostic steps.** Ask the person to check Settings › **Personalization**.

**Resolution.** **Remove** the memories concerned, or **Clear memory** (section 5.5). The chat
export in Data Controls does not include memories, so a person who wants a copy first must read
them on screen (`src/lib/components/chat/Settings/DataControls.svelte:93-94`).

**Escalation.** None normally; privacy questions as in 11.10.

### 11.10 "Who can see my memories?" or "Is it safe to keep health details in memory?"

**Symptom.** A privacy question rather than a fault.

**What the code shows** (section 3.4): only the person sees their memories in the interface; no
admin screen lists another person's memories; the memory text goes to the chat model's provider
with requests, to the embedding service when saved, to configured event webhooks (first 300
characters), and to the audit log when it records request bodies; people with database, vector
store or backup access can read it. In addition, an admin can download the whole database file
from Admin Settings › Database › **Database** ("Download the application database when
supported.") when the site uses SQLite and `ENABLE_ADMIN_EXPORT` is on (code default on); that
file holds every person's memories (`backend/open_webui/routers/utils.py:74-90`;
`src/lib/components/admin/Settings/Database.svelte:123-140`; `backend/open_webui/config.py:2082`;
`src/lib/i18n/locales/en-US/translation.json:2185-2186`).

**Diagnostic steps.** None.

**Resolution.** Explain what the code shows, without assurances beyond it. Whether health details
may be kept in memories, whether the model and embedding providers are approved for them, and who
may look at memories are **TO BE CONFIRMED** (section 14). Until confirmed, a cautious person can
leave **Memory** off or remove sensitive memories.

**Escalation.** The U of T Privacy Office (privacy.utoronto.ca) for policy questions; the platform
maintainer for which providers and stores the site uses. Security questions: refer to the platform
maintainer and U of T Information Security (security.utoronto.ca).

### 11.11 "Please delete my memories when my account is closed"

**Symptom.** A person who is leaving, or an admin closing an account, asks for the memories to go
too.

**Likely causes.** Deleting an account (the only account-deletion route requires an admin)
removes chats and the account, but **not** memories or their search copies (section 3.4;
`backend/open_webui/routers/users.py:1042-1044`).

**Diagnostic steps.** Ask whether the account still exists.

**Resolution.** While the account exists, the person can use **Clear memory** first (section 5.11).

**Escalation.** If the account is already deleted: the platform maintainer for database and vector
store work, and the U of T Privacy Office for the request itself. Include the deleted account's
email and the deletion date, never memory text.

## 12. Local Customisations

Compared on 2026-10-09 with read-only `git diff main...uoft` (the three fork commits) and
`git diff` (uncommitted working tree) for every file in scope: `backend/open_webui/routers/memories.py`,
`backend/open_webui/models/memories.py`, `backend/open_webui/utils/memory.py`,
`backend/open_webui/utils/middleware.py`, `backend/open_webui/retrieval/`, `backend/open_webui/config.py`,
`backend/open_webui/tools/builtin.py`, `backend/open_webui/utils/tools.py`,
`backend/open_webui/utils/subagents.py`, `backend/open_webui/events.py`, `backend/open_webui/migrations/`,
`src/lib/components/chat/Settings/Personalization.svelte` and `Personalization/`,
`src/lib/apis/memories/`, `src/lib/components/chat/SettingsModal.svelte`,
`src/lib/components/chat/Chat.svelte`, `src/lib/components/admin/Settings/General.svelte`,
`src/lib/components/admin/Settings/Documents.svelte`,
`src/lib/components/admin/Users/Groups/Permissions.svelte`,
`src/lib/components/workspace/Models/Capabilities.svelte`,
`src/lib/components/workspace/Models/BuiltinTools.svelte`, `src/lib/constants/permissions.ts`,
`src/lib/components/common/ExperimentalBadge.svelte` and `src/lib/components/common/ConfirmDialog.svelte`.

**Result: the memories area matches upstream v0.11.4.** No fork commit changes any of these files.
The fork's own `en-US` translation additions, committed and uncommitted, contain no memory text
(neither diff of `src/lib/i18n/locales/en-US/translation.json` has a line mentioning memory), and
no migration is local to the fork (ground truth). The only uncommitted change among the files above
is in `src/lib/components/chat/Chat.svelte` and does not concern memory (table below).

Fork changes elsewhere that affect this area indirectly:

| Fork change | Effect on memories | Source |
|---|---|---|
| **Hide Processing Details** (committed; a per-person Interface setting for which admins can also set a default) | Hides memory tool-call entries, which are the only sign in a chat that the model read, saved, changed or deleted a memory (section 9). Turning the setting off shows them again, also in past chats, because the entries are still saved | `src/lib/components/common/ToolCallDisplay.svelte:145`, `:199-200`; `backend/open_webui/models/users.py:100`; `builtin-native-tools.md` sections 5.6 and 12 |
| Product name **MedIT GPT** (committed) | No memory text uses the product name. The background review's system message keeps the upstream text `You are Open WebUI's private memory reviewer. Return only valid JSON.` with its licence comment; it is sent to the model, not shown in the interface, and is a licence-protected line to leave as it is | `backend/open_webui/utils/memory.py:576-579`; `backend/open_webui/env.py:951` |
| Uncommitted change in `Chat.svelte` | Concerns resuming a reply after a tool approval, not memory. It adds five lines above the memory feature code, so this document's `Chat.svelte` line numbers (for example `:3412-3414`) are working-tree numbers, five higher than in the committed file | `src/lib/components/chat/Chat.svelte:2847-2851`, `:3412-3414` |

Whether the uncommitted working-tree changes will be committed and deployed is **TO BE
CONFIRMED** (section 14).

## 13. Source File Index

Every file read for this document, with what it holds for memories. Line numbers are those of the
working tree on 2026-10-09.

### 13.1 Back End

| File | What it holds for memories | Sections |
|---|---|---|
| `backend/open_webui/routers/memories.py` | The twelve memory routes; the switch and permission check (`:35-47`); search copies, their rebuild and the dimension-mismatch rebuild (`:119-180`); event publishing | 2.2, 3.1, 5.2 to 5.5, 5.10, 9.1, 10.3 |
| `backend/open_webui/models/memories.py` | The `memory` table, `MemoryModel`, and the repository: insert, update, read, delete, delete all, and batch operations with duplicate skipping | 6.1, 5.5, 10.3 |
| `backend/open_webui/utils/memory.py` | Text and path cleaning (`:21-40`); word and path search helpers (`:85-248`); batch validation (`:251-283`); the memory context (`:286-407`); the background review (`:410-609`) | 4, 5.6, 5.8, 7.3, 10.3, 10.7 |
| `backend/open_webui/utils/middleware.py` | Where the memory context is added (`:2683-2698`) and where the review is called after a reply (`:4038-4047`, `:4378-4385`, `:6582-6590`) | 5.6, 5.8, 8 |
| `backend/open_webui/tools/builtin.py` | The eight memory tools (`:795-1119`) | 5.7, 10.4, 10.7 |
| `backend/open_webui/utils/tools.py` | When the memory tools are offered (`:528-540`, `:656-673`) and their removal inside sub-agents (`:766-769`) | 3.2, 7.4 |
| `backend/open_webui/utils/subagents.py` | The four memory-changing tools removed for sub-agents (`:34-39`); sub-agents copying the request's features (`:310-326`) | 3.2 |
| `backend/open_webui/utils/automations.py` | Automation runs built without the memory feature (`:176-198`) | 3.2 |
| `backend/open_webui/utils/misc.py` | Reading a message's text (`:228-238`) and adding to the system message (`:682-698`) | 5.6, 11.2 |
| `backend/open_webui/config.py` | The six memory settings (`:426-431`, `:2844-2849`); the permission default (`:1926`, `:2012`); the relevance threshold (`:970`, `:2901`); `ENABLE_ADMIN_EXPORT` (`:2082`) | 3.1, 7.1, 11.10 |
| `backend/open_webui/routers/auths.py` | Admin read and save of the two memory switches (`:104-136`, `:1204-1206`, `:1269-1296`) | 2.2, 5.9 |
| `backend/open_webui/routers/configs.py` | Reading the `memories` namespace, and settings export and import (`:100-125`) | 2.2, 7.1 |
| `backend/open_webui/main.py` | Mounting at `/api/v1/memories` (`:872`); `features.enable_memories` in `/api/config` (`:2342-2378`); the first title generation (`:1471-1492`) | 2.2, 8 |
| `backend/open_webui/events.py` | The four memory events (`:335-346`), the notification list (`:669-675`), webhook text (`:1034-1056`) | 9, 10.8 |
| `backend/open_webui/constants.py` | `ACCESS_PROHIBITED` (`:70-72`) and `NOT_FOUND` (`:78`) | 3.1, 10.3 |
| `backend/open_webui/retrieval/utils.py` | Owner-only access to `user-memory-` collections (`:1318-1344`) | 3.4 |
| `backend/open_webui/retrieval/vector/async_client.py`, `backend/open_webui/retrieval/vector/dbs/chroma.py`, `backend/open_webui/retrieval/vector/dbs/qdrant_multitenancy.py`, `backend/open_webui/retrieval/vector/dbs/milvus_multitenancy.py` | The vector store client used for search copies; the default store's tolerant delete (`chroma.py:177-194`); the shared memory collections of the multitenancy back ends | 6.2, 10.6 |
| `backend/open_webui/routers/retrieval.py` | **Reset Vector Storage/Knowledge**, which also removes memory search copies (`:3271-3278`) | 6.2 |
| `backend/open_webui/routers/users.py`, `backend/open_webui/models/users.py`, `backend/open_webui/models/auths.py`, `backend/open_webui/routers/scim.py` | Account deletion, which leaves memories behind; where the personal **Memory** switch is stored; new account ids | 3.4, 6.3, 11.5, 11.11 |
| `backend/open_webui/routers/utils.py` | The admin database download (`:74-90`) | 11.10 |
| `backend/open_webui/internal/db.py` | Database sessions; an unfinished batch is not committed (`:519-535`) | 10.3 |
| `backend/open_webui/env.py` | `GLOBAL_LOG_LEVEL` (`:113-124`); `ENABLE_RETRIEVAL_UNSCOPED_COLLECTIONS` (`:835-839`); the product name (`:951`) | 7.2, 10.7, 12 |
| `backend/open_webui/migrations/versions/7e5b5dc7342b_init.py`, `a0b1c2d3e4f5_add_memory_user_id_index.py`, `3ff2c63645b8_reshape_config_to_per_key_rows.py`, `7b3f2a9c1d4e_add_memory_type.py`, `42e2978c7933_add_memory_path_and_meta.py`, `55f1302ac17c_add_memory_id_user_id_covering_index.py`, `461111b60977_add_missing_primary_keys_to_legacy_.py` | The migrations that shaped the `memory` table | 6.4 |

### 13.2 Front End

| File | What it holds for memories | Sections |
|---|---|---|
| `src/lib/components/chat/Settings/Personalization.svelte` | The **Personalization** tab: switch, list, search, **Actions**, confirmations | 2.1, 5.1 to 5.5, 10.1, 10.2, 10.6 |
| `src/lib/components/chat/Settings/Personalization/MemoryModal.svelte` | The **Add Memory** and **Edit Memory** dialog | 5.3, 5.4, 10.1, 10.2 |
| `src/lib/apis/memories/index.ts` | The seven client functions and how they turn errors into toast text | 2.2, 10 |
| `src/lib/components/chat/SettingsModal.svelte` | When the tab shows; saving the switch; the **Save** toast | 2.1, 3.2, 10.2, 11.3 |
| `src/lib/components/chat/Chat.svelte` | Sends `features.memory` with each message (`:3393-3417`) | 3.2, 5.6 |
| `src/routes/+layout.svelte` | Loads the site settings and the person's permissions when the app starts (`:1269`, `:1281-1290`) | 10.3, 11.3 |
| `src/routes/(app)/+layout.svelte` | Opening Settings from `/?settings=` (`:165-194`) | 2.1 |
| `src/lib/components/admin/Settings/General.svelte` | **Memories** and **Memory System Context** (`:315-333`) | 5.9, 10.5 |
| `src/lib/components/admin/Settings/Documents.svelte` | **Reindex** and its confirmation (`:382-416`, `:1160-1171`, `:1576-1590`) | 5.10, 10.5 |
| `src/lib/components/admin/Settings/Database.svelte` | **Export Config** and **Import Config** (`:60-120`); the database download (`:123-140`) | 7.1, 11.10 |
| `src/lib/components/admin/Users/Groups/Permissions.svelte` | The **Memories** permission switch (`:960`, `:1099-1112`) | 3.1, 5.9, 10.5 |
| `src/lib/components/workspace/Models/Capabilities.svelte`, `src/lib/components/workspace/Models/BuiltinTools.svelte` | The model's **Memory** capability (`:53-56`) and **Memory** tool group (`:21-24`) | 2.1, 7.4, 10.5 |
| `src/lib/constants.ts`, `src/lib/constants/permissions.ts` | Default of the **Memory** capability (`:126`) and of the **Memories** permission (`:71`) | 3.1, 7.4 |
| `src/lib/components/common/ExperimentalBadge.svelte`, `src/lib/components/common/ConfirmDialog.svelte`, `src/lib/components/common/ToolCallDisplay.svelte` | The **Experimental** badge; the confirmation dialogs; tool-call entries and **Hide Processing Details** | 10.1, 12 |
| `src/lib/components/chat/Settings/DataControls.svelte` | The chat export, which has no memories (`:93-94`) | 11.9 |
| `src/lib/i18n/locales/en-US/translation.json` | English text of the dotted keys (`:2185-2186`, `:2317-2319`, `:2390-2393`, `:2556-2557`, `:2585-2586`, `:3000-3007`) | 10 |

Other documents this one relies on: `builtin-native-tools.md` (the memory tools),
`rag-retrieval-embeddings-and-vector-stores.md` (embeddings, vector stores, resets),
`users-groups-roles-and-permissions.md` (permission evaluation), `sso-oauth-oidc-and-scim.md`
(accounts created by single sign-on), `workspace-models-and-model-access.md` (the model editor) and
`model-connections-openai-ollama-and-direct.md` (where requests go).

## 14. Open Questions

Everything below could not be settled from the repository. Items marked with a section number
repeat a **TO BE CONFIRMED** or "read from code" point made there.

### 14.1 Live Configuration (Data, Not Code)

| Question | Why it matters | Where raised |
|---|---|---|
| The production values of the six `memories.*` settings: **Memories**, **Memory System Context**, background review (code default off), review interval, and the two character limits | They decide whether memory exists at all, whether it is injected, whether the review saves memories unseen, and how much is used | 7.1 |
| The stored default of `features.memories` and each group's value | Who sees **Personalization** | 3.1 |
| Which chat model providers and which embedding engine production uses | Memory text is sent to both | 3.4 |
| Which vector store production uses | Where search copies live; the delete behaviour in 10.6 is that of the default Chroma store | 6.2 |
| Which event webhooks and Event functions are configured, and where they deliver | They receive 300-character previews plus the acting person's name and email | 3.4, 9.1 |
| `rag.relevance_threshold` (code default 0.0) | At 0.0 the eight nearest memories are added however unrelated | 5.6 |
| Which models have the **Memory** capability or the **Memory** tool group off | Explains "memories aren't being used" for one model | 7.4, 11.2 |
| The tool approval mode and whether **Tool Permissions** is offered | With **Full access** the model saves and deletes memories without asking | 5.7, 11.1; `builtin-native-tools.md` 5.4 |
| The admin default for **Hide Processing Details** | When on, people do not see memory tool calls | 12 |
| `ENABLE_ADMIN_EXPORT` (code default on) and whether production uses SQLite | Together they allow an admin to download the whole database, memories included | 11.10 |
| `GLOBAL_LOG_LEVEL` and `AUDIT_LOG_LEVEL` | Review failures are logged only at debug level; the audit log may hold memory text from request bodies | 3.4, 10.7 |
| Whether the uncommitted working-tree changes will be committed and deployed | Line numbers and behaviour of `Chat.svelte` | 12 |

### 14.2 Privacy and Organisational Questions

- **Health details.** Memories are free text drawn from what people type, and from what the model
  and the review pick out of chats, so they can hold health or other sensitive personal details.
  Nothing in the tool descriptions or the review's rules mentions health information
  (sections 5.7 and 5.8). Whether such details may be kept in memories at all, whether people
  should be told so in the interface, and whether this experimental feature should be on for this
  deployment are **TO BE CONFIRMED** with the U of T Privacy Office (privacy.utoronto.ca).
- **Providers.** Whether the chat model providers and the embedding service that receive memory
  text are approved for that kind of data is **TO BE CONFIRMED** (section 3.4).
- **Retention.** The code has no expiry or retention rule for memories: a memory stays until the
  person, the model or the review deletes it (no scheduled job, section 8; no other code removes
  memories, section 3.4). Whether a retention period applies is **TO BE CONFIRMED**.
- **Account deletion.** Deleting an account (admin only) leaves the person's memory rows and their
  search copies in place, and an admin **Reindex** skips them (section 3.4). Who removes them,
  how, and whether off-boarding should include **Clear memory** first are **TO BE CONFIRMED**.
- **Admin access.** No screen shows another person's memories, but admins can download the whole
  database on SQLite sites (11.10), and people with database, vector store or backup access can
  read memory text. Whether admins may look at memories, and under what policy, is **TO BE
  CONFIRMED** (section 3.4).
- **Backups.** Whether backups exist, how long they are kept, whether one memory can be restored,
  and whether deleted memories survive in them are **TO BE CONFIRMED** (sections 5.5 and 11.5).
- **Copies outside the memory list.** Tool-call entries in chats, event webhooks, the audit log and
  the model provider keep copies that deleting a memory does not reach (section 5.5). How a
  deletion request should deal with them is **TO BE CONFIRMED**.
- **Access requests.** People can read their memories on screen, but no export includes them (the
  chat export has none, section 11.9). Whether that is enough for a request to see one's own
  personal information is **TO BE CONFIRMED** with the Privacy Office.
- **Background review.** If it is turned on, the chat model receives up to 80 existing memories and
  the last 16 messages every Nth message, with no notice to the person (section 5.8). Whether it
  should be on is **TO BE CONFIRMED**.
- **Support routes.** The repository names no support contact, queue or service level (ground
  truth); who handles memory privacy requests is **TO BE CONFIRMED**.

### 14.3 Behaviour Read from Code, to Confirm in a Test Environment

- A memory is saved before its embedding is made; if the embedding fails, the dialog stays open
  with no message and pressing **Add** again saves a second copy (sections 5.3 and 10.6).
- An edit whose embedding fails keeps the new text but the old search copy (section 5.4).
- A leftover search copy can still reach the model as `[Relevant Context]` (section 5.5).
- Regenerating a reply at a review message runs the review again (section 5.8).
- A non-numeric value in one of the three numeric memory variables stops the server from starting
  (section 7.1).
- The `Error generating initial chat title` log line for new chats (section 8).
- A memory tool sees a refusal as `{status_code}: {detail}` (section 10); a batch with one unknown
  id saves none of its operations (section 10.3); a `type` other than `user` or `context` refuses
  the whole batch (section 4.2, corrected).
- The review's prompt shows the operation format with the literal value `"type":"user|context"`
  (`backend/open_webui/utils/memory.py:553-559`); a model that copies that value exactly would have
  its whole answer refused, with only a debug-level log line. How often this happens is unknown.
- A failed list load looks exactly like having no memories; a failed **Remove** or **Clear memory**
  shows nothing; the memory step of an admin **Reindex** can fail with no message (section 10.6).
- No memory context at all is added when none of the person's messages in the request has text
  (section 11.2).

### 14.4 Discrepancies Noticed in the Code

- The Personalization description points to a 'Manage' button; the screen swaps in "Add Memory",
  and that item is inside the **Actions** menu (section 10.1).
- The menu item reads `Clear memory` while its confirmation is titled `Clear Memory` (section 10.1).
- `add_memory` and `replace_memory_content` record `created_by: manual`, so their changes are
  recorded exactly like memories typed in Settings (section 4.1).
- `delete_memory` publishes no event, unlike every other deletion path (section 9.1).
- The `/reset` route rebuilds search copies and deletes no memory; `/reindex` ignores the site
  switch; the browser's `queryMemory` function is not called anywhere in the front end (section 2.2).
- The `add_memory` tool turns an unknown type into `context`, while `update_memory` and the review
  refuse it (section 4.2).

No contradiction with `CLAUDE.md`, `ground-truth.md` or `inventory.md` was found; the ground-truth
statement that deleting a user leaves memories behind is confirmed (section 3.4).

### 14.5 Security-Sensitive Questions

- Admin and operator access to memory text (database download, vector store, backups, audit log),
  and whether it is logged or reviewed. Security-sensitive: refer to the platform maintainer and
  U of T Information Security (security.utoronto.ca).
- One question about how the memory tools re-check access compared with the memory routes.
  Security-sensitive: refer to the platform maintainer and U of T Information Security
  (security.utoronto.ca).

### 14.6 Corrections Made While Completing This Document

| Date | Section | Correction |
|---|---|---|
| 2026-10-09 | 4.2, table row "Background review and `update_memory`" | Said any type other than `user` is stored as `context`; in fact only `user`, `context` or no type are accepted, and any other value refuses the whole batch. Verified against `backend/open_webui/routers/memories.py:85-95` with an isolated check of the same form definition |
