# Document Processing, Retrieval (RAG), Embeddings and Vector Stores

## At a Glance

- **What it is.** The machinery that lets a model answer from documents. When a file is uploaded (to
  a chat or a knowledge base) the server extracts its text, cuts the text into chunks, turns each
  chunk into an embedding (a list of numbers that captures meaning) and stores the chunks and
  embeddings in a vector store. When the user later asks a question, the server searches those
  chunks, adds the best matches to the prompt using the RAG template, and the answer shows the
  matching passages as source chips and `[1]`-style citations. "RAG" means retrieval-augmented
  generation.
- **Where it lives.** The admin and processing endpoints are in
  `backend/open_webui/routers/retrieval.py`, mounted at `/api/v1/retrieval`
  (`backend/open_webui/main.py:852`). Search, embeddings and the prompt sources are built in
  `backend/open_webui/retrieval/utils.py`; text extraction is in `backend/open_webui/retrieval/loaders/`;
  the vector store layer is `backend/open_webui/retrieval/vector/`. The chat pipeline calls retrieval
  from `chat_completion_files_handler` (`backend/open_webui/utils/middleware.py:2049-2167`).
- **Code defaults** (the live values are rows in the `config` table, **TO BE CONFIRMED** for
  production): built-in extraction (`rag.content_extraction_engine` empty, the PDF reader is pypdf);
  chunks of 1,000 characters with 100 overlapping, Markdown heading splitting on; local
  SentenceTransformers embeddings with `sentence-transformers/all-MiniLM-L6-v2`; Top K 3; hybrid search
  off; no reranking model; relevance threshold 0.0; full context mode off; bypass embedding and
  retrieval off (`backend/open_webui/config.py:868`, `:965-1068`). The vector store is Chroma in
  `DATA_DIR/vector_db` (`backend/open_webui/config.py:503-506`); which store production uses is
  **TO BE CONFIRMED** (see `tools/ground-truth.md`, Data Stores).
- **Admin screen.** Admin Settings > **Documents** (`/admin/settings/documents`, which opens
  `/?settings=admin:documents`) has five sections, **Content Extraction**, **Embedding**,
  **Retrieval**, **Files** and **Integration**, plus a **Danger Zone**
  (`src/lib/components/admin/Settings/Documents.svelte:437-1592`). External vector collections are
  connected under Admin Settings > **Integrations** > **Knowledge**
  (`src/lib/components/admin/Settings/Integrations.svelte:338-340`).
- **Changing the embedding model needs a reindex.** Old chunks keep the old model's embeddings. The
  Danger Zone **Reindex** button rebuilds knowledge-base files, the knowledge search index and memories
  (`src/lib/components/admin/Settings/Documents.svelte:382-416`). The code does **not** re-embed
  files that were only attached to chats (section 5.13).
- **What fails most often, and what users see.** A file that cannot be read still attaches to the
  message, with a yellow warning pop-up carrying the reason (for example
  `The content provided is empty. Please ensure that there is text or data present before proceeding.`)
  (`src/lib/components/chat/MessageInput.svelte:1025-1028`). Questions about documents then answer
  without sources and the status line reads `No sources found`. In the default Chroma store, any error
  during a search is swallowed and the search returns nothing, so chunks made with a different
  embedding model should simply stop being found, with nothing in the log
  (`backend/open_webui/retrieval/vector/dbs/chroma.py:106-107`; section 14). If a reranking model fails to load
  when an admin saves, hybrid search is switched off without a message
  (`backend/open_webui/routers/retrieval.py:1251-1253`).
- **This area matches upstream Open WebUI v0.11.4**: no file in scope differs on the `uoft` branch or
  in the working tree. The fork's per-user **Inline Citations** and **Hide Processing Details**
  settings change how sources and retrieval status lines are displayed (section 12).

## 1. Purpose and Who Uses It

Retrieval is how MedIT GPT answers questions about material outside the model's training: a PDF a
user drops into a chat, a knowledge base an instructor shares with a group, a note, an earlier chat,
or a web page. It is not a screen of its own. It runs behind the chat composer, behind knowledge
bases, behind memories, and behind the built-in knowledge tools, and it is configured on one admin
tab.

Who touches it:

- **Every signed-in user** (role `user` or `admin`) uses it when they attach a file, a knowledge base,
  a note, a chat or a web page to a message, and when they chat with a custom model that has
  knowledge attached. The processing and query endpoints require a verified user
  (`backend/open_webui/routers/retrieval.py:1925-1930`, `:2201-2206`, `:3076-3081`, `:3142-3147`),
  so `pending` accounts cannot use them (see `tools/ground-truth.md`, Accounts and Access).
- **Users choose per file** between **Using Focused Retrieval** (search the chunks) and **Using Entire
  Document** (send the whole text) in the file preview window
  (`src/lib/components/common/FileItemModal.svelte:343-370`), and set their default under Settings >
  Interface > **Default Upload Mode** (`src/lib/components/common/InterfaceSettings.svelte:1905-1927`).
- **Admins** control the whole pipeline on Admin Settings > **Documents**: the extraction engine, the
  chunking rules, the embedding engine and model, hybrid search and reranking, the RAG template, upload
  limits, cloud pickers, and the destructive Danger Zone actions
  (`src/lib/components/admin/Settings/Documents.svelte:418-1608`). Every settings endpoint requires the
  `admin` role (`backend/open_webui/routers/retrieval.py:468-469`, `:537-538`, `:629-630`, `:962-963`).
- **Admins** also register external vector collections (Qdrant, Milvus or pgvector databases that
  already hold embeddings) as read-only knowledge bases on Admin Settings > **Integrations**
  (`src/lib/components/admin/Settings/ExternalKnowledge.svelte:797-888`).
- **Built-in tools** reuse the same search code when a model uses native function calling:
  `query_chat_files` calls the same source builder as the chat pipeline, `query_knowledge_files` calls
  the collection search, and `query_knowledge_bases` searches the knowledge-base descriptions
  (`backend/open_webui/tools/builtin.py:2509`, `:2564-2602`, `:3151-3161`, `:3372-3420`); see
  `builtin-native-tools.md`.
- **Memories** are embedded with the same embedding model into a per-user collection
  (`backend/open_webui/routers/memories.py:128-168`); see `memories.md`.

Tier 1's interest is mostly diagnostic: telling "the file never became searchable" apart from "the
search found nothing relevant" and from "the model was never given the document", and knowing which of
those needs an administrator.

## 2. Navigation and URLs

The production host name is **TO BE CONFIRMED**; paths below are relative to the site root.

### 2.1 Where Users Meet Retrieval

| Place | What the user sees | Source |
|---|---|---|
| Chat composer, after attaching a file | The file chip shows a spinner until the upload call returns, which (with the default streaming status check) is after processing finishes; a processing failure shows a yellow warning pop-up with the server's reason, and the chip stays attached | `src/lib/components/chat/MessageInput.svelte:939`, `:1009-1043`, `:2007`; `src/lib/components/common/FileItem.svelte:87-105`; `src/lib/apis/files/index.ts:46-87` |
| File chip > preview window | A switch reading **Using Focused Retrieval** or **Using Entire Document** (only where the item can be edited) | `src/lib/components/common/FileItemModal.svelte:343-370` |
| Settings > Interface | **Default Upload Mode**: "Attach files with full content or focused retrieval by default." | `src/lib/components/common/InterfaceSettings.svelte:1905-1927`; `src/lib/i18n/locales/en-US/translation.json:2899-2900` |
| Status line above a reply | `Querying` (with the search phrases as chips), then `Retrieved {count} sources`, `Retrieved 1 source` or `No sources found`; for knowledge on a custom model in legacy mode, `Searching Knowledge for "{searchQuery}"` | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:40-124` |
| Under a reply | The **Sources** button (`1 Source` or `{COUNT} Sources`) and the citation window with each retrieved passage | `src/lib/components/chat/Messages/Citations.svelte:171-249`; `src/lib/components/chat/Messages/Citations/CitationModal.svelte:99-271` |

The composer, the status lines and the citation window are documented screen by screen in
`chat-composer-and-message-display.md` (sections 5.16 and 5.17); upload limits and file storage in
`files-uploads-and-storage.md`; knowledge-base screens in `knowledge-bases.md`.

### 2.2 Admin Screens

| Screen | URL | Notes | Source |
|---|---|---|---|
| Admin Settings > **Documents** | `/admin/settings/documents`, which redirects to `/?settings=admin:documents` and opens the settings window on that tab | Listed under the **Tools** group of the admin tabs. Heading `settings.admin.documents.title` reads "Documents" | `src/routes/(app)/admin/settings/[tab]/+page.svelte:6-10`; `src/lib/components/chat/SettingsModal.svelte:165-166`, `:334-339`, `:873-874`; `src/lib/i18n/locales/en-US/translation.json:2350` |
| Admin Settings > **Integrations** > **Knowledge** | `/admin/settings/integrations` | Holds the **External Knowledge Sources** list, marked Experimental | `src/lib/components/admin/Settings/Integrations.svelte:338-340`; `src/lib/components/admin/Settings/ExternalKnowledge.svelte:797-812`; `src/lib/i18n/locales/en-US/translation.json:2474-2475`, `:2480` |

The other admin panels are catalogued in `admin-settings-panels.md`.

### 2.3 API Endpoints in This Area

Retrieval router endpoints are under `/api/v1/retrieval` (`backend/open_webui/main.py:852`). "Verified"
means role `user` or `admin`.

| Method and path | Role | What it does | Source |
|---|---|---|---|
| `GET /api/v1/retrieval/embedding` | Admin | Reads the embedding engine, model, batch size and connection settings | `backend/open_webui/routers/retrieval.py:468-491` |
| `POST /api/v1/retrieval/embedding/update` | Admin | Saves the embedding settings and reloads the embedding model in the worker that handled the request | `backend/open_webui/routers/retrieval.py:537-626` |
| `GET /api/v1/retrieval/config` | Admin | Reads every retrieval, extraction, file and web-search setting | `backend/open_webui/routers/retrieval.py:629-789` |
| `POST /api/v1/retrieval/config/update` | Admin | Saves those settings; reloads the reranking model | `backend/open_webui/routers/retrieval.py:962-1551` |
| `POST /api/v1/retrieval/process/file` | Verified | Extracts, chunks and embeds one uploaded file (or re-embeds supplied text, or adds the file to a knowledge base) | `backend/open_webui/routers/retrieval.py:1925-2192` |
| `POST /api/v1/retrieval/process/text` | Verified | Embeds a piece of text into a collection | `backend/open_webui/routers/retrieval.py:2201-2242` |
| `POST /api/v1/retrieval/process/files/batch` | Verified | Embeds several already-extracted files into one collection | `backend/open_webui/routers/retrieval.py:3343-3459` |
| `POST /api/v1/retrieval/query/doc` | Verified | Searches one collection | `backend/open_webui/routers/retrieval.py:3076-3128` |
| `POST /api/v1/retrieval/query/collection` | Verified | Searches several collections | `backend/open_webui/routers/retrieval.py:3142-3196` |
| `POST /api/v1/retrieval/delete` | Admin | Deletes one file's chunks from a collection, matched by the file's content hash | `backend/open_webui/routers/retrieval.py:3211-3268` |
| `POST /api/v1/retrieval/reset/db` | Admin | Empties the whole vector store and deletes every knowledge base record | `backend/open_webui/routers/retrieval.py:3271-3284` |
| `POST /api/v1/retrieval/reset/uploads` | Admin | Deletes everything in the upload folder; the current Documents panel does not call it | `backend/open_webui/routers/retrieval.py:3287-3317` |
| `POST /api/v1/retrieval/process/url`, `/process/web`, `/process/youtube`, `/process/web/search` | Verified | Web pages, YouTube transcripts and web search; documented in `web-search-and-web-loading.md` | `backend/open_webui/routers/retrieval.py:2356-2508`, `:2882` |
| `POST /api/v1/knowledge/reindex` | Admin (checked inside) | Re-embeds every knowledge-base file; used by the Documents **Reindex** button | `backend/open_webui/routers/knowledge.py:374-462` |
| `POST /api/v1/knowledge/metadata/reindex` | Admin | Rebuilds the knowledge-base search index (names and descriptions) | `backend/open_webui/routers/knowledge.py:469-494` |
| `POST /api/v1/memories/reindex` | Admin | Re-embeds every user's memories | `backend/open_webui/routers/memories.py:449-480` |
| `DELETE /api/v1/files/all` | Admin | Deletes every file record and stored file and empties the vector store; used by **Reset Upload Directory** | `backend/open_webui/routers/files.py:575-597` |
| `/api/v1/knowledge/external/...` (connections, source test, create, update) | Admin | External knowledge sources (section 5.15) | `backend/open_webui/routers/knowledge.py:691-1088` |
| `POST /api/embeddings`, `POST /api/v1/embeddings` | Verified | OpenAI-compatible embeddings for API callers. **Not** the RAG embedding model: it routes to a chat connection's model with model access checks (section 5.18) | `backend/open_webui/main.py:1072-1094`; `backend/open_webui/utils/embeddings.py:24-88` |

The front-end client `src/lib/apis/retrieval/index.ts` also defines `getQuerySettings`,
`updateQuerySettings`, `getRerankingConfig` and `updateRerankingConfig`, which call
`/query/settings`, `/query/settings/update`, `/reranking` and `/reranking/update`
(`src/lib/apis/retrieval/index.ts:97-306`). The backend router defines no such paths, and the Documents
panel imports these functions without calling them
(`src/lib/components/admin/Settings/Documents.svelte:9-19`). They are leftovers, not a fault to chase.

## 3. Roles and Permissions

### 3.1 Who May Do What

| Action | Who | Rule in code | Source |
|---|---|---|---|
| Change any Documents setting, reload models, reset or reindex | `admin` only | `get_admin_user`; the knowledge reindex endpoint accepts any verified user and then refuses non-admins with `ERROR_MESSAGES.UNAUTHORIZED` | `backend/open_webui/routers/retrieval.py:469`, `:538`, `:630`, `:963`, `:3215`, `:3274`, `:3288`; `backend/open_webui/routers/knowledge.py:374-384` |
| Process a file (`/process/file`) | Verified users for their **own** files; admins for any file | Non-admins look the file up by id **and** owner; an unknown or foreign file gives HTTP 404 `We could not find what you're looking for :/` | `backend/open_webui/routers/retrieval.py:1938-1941`, `:2191-2192` |
| Write into a named collection (`collection_name` supplied) | Users with **write** access to that collection | Checked by `_validate_collection_access(..., access_type='write')`; refusal is HTTP 403 with the `ACCESS_PROHIBITED` text | `backend/open_webui/routers/retrieval.py:1950-1951`, `:2210-2211`, `:3050-3063`, `:3362-3363` |
| Search a collection (`/query/doc`, `/query/collection`) | Users with **read** access to every named collection | Same check with `access_type='read'` | `backend/open_webui/routers/retrieval.py:3083`, `:3149` |
| Batch-embed files | Owner of each file, or an admin | Other users' files are skipped with `Permission denied: not file owner` in the result list | `backend/open_webui/routers/retrieval.py:3374-3393` |
| Manage external knowledge connections and sources | `admin` only | `get_admin_user` on every `/knowledge/external/...` endpoint | `backend/open_webui/routers/knowledge.py:691-1088` |

### 3.2 Which Collections a User Can Search

At chat time each attached item is checked before its chunks are read
(`backend/open_webui/retrieval/utils.py:1299-1362`, `:1407-1677`):

- **Admins** may read any collection whose name is well formed.
- A **file** (`file-{id}`) is readable when the user owns the file, is an admin, has been granted read
  access to it, or reached it through a shared folder.
- A **knowledge base** (collection named after the knowledge-base id) is readable when the user owns
  it, is an admin, or has a read grant; access grants are explained in
  `users-groups-roles-and-permissions.md`.
- A user's **memories** (`user-memory-{user id}`) are readable only by that user.
- A **web-search** collection (`web-search-{user id}-...`) is readable only by the user who ran the
  search.
- The **knowledge-base search index** (`knowledge-bases`) is not readable by non-admins.
- **Attached notes and chats** are read only when the user owns them, is an admin, or has a read grant
  (for chats, also through a readable folder).
- Any other collection name is refused unless the environment switch
  `ENABLE_RETRIEVAL_UNSCOPED_COLLECTIONS` is on (default off, `backend/open_webui/env.py:839`).

When a check fails the item is skipped quietly: the answer simply has fewer or no sources, and the
server log has a debug line (`backend/open_webui/retrieval/utils.py:1673-1677`).

### 3.3 Feature Permissions That Gate Retrieval Inputs

Uploading files and attaching web content are governed by per-user feature permissions checked in the
composer and the files router (for example `You do not have permission to upload web content.` in
`src/lib/components/chat/Chat.svelte:1791-1793`). The permission keys and their defaults are in
`users-groups-roles-and-permissions.md`; upload rules are in `files-uploads-and-storage.md`.

### 3.4 Environment Switches That Change Access

`BYPASS_RETRIEVAL_ACCESS_CONTROL` (default off, `backend/open_webui/env.py:833`) makes the chat
pipeline use file and collection names without the checks in 3.2
(`backend/open_webui/retrieval/utils.py:1548-1552`, `:1624-1625`, `:1649-1650`, `:1657-1658`).
`ENABLE_RETRIEVAL_UNSCOPED_COLLECTIONS` is described above. Both are environment-only; their production
values are **TO BE CONFIRMED**. Any question about relaxing them is security-sensitive: refer to the
platform maintainer and U of T Information Security (security.utoronto.ca).

## 4. Key Concepts and Terminology

| Term | Meaning in this code | Source |
|---|---|---|
| **RAG** (retrieval-augmented generation) | Finding relevant passages in the user's documents and adding them to the prompt before the model answers | `backend/open_webui/utils/middleware.py:2049-2167`, `:972-1008` |
| **Content extraction** | Turning an uploaded file into plain text. Done by a **loader** chosen from the configured **Content Extraction Engine** and the file type | `backend/open_webui/retrieval/loaders/main.py:332-818` |
| **Chunk** | A piece of the extracted text, at most **Chunk Size** long, stored with its own embedding. Retrieval returns chunks, not whole files | `backend/open_webui/routers/retrieval.py:1755-1820` |
| **Chunk Overlap** | How much text neighbouring chunks share, so a sentence cut at a boundary still appears whole in one of them | `backend/open_webui/routers/retrieval.py:1788-1792` |
| **Text Splitter** | How chunk length is measured: characters (default), Tiktoken tokens, or tokens of a Hugging Face tokenizer ("Transformers") | `backend/open_webui/routers/retrieval.py:1787-1817` |
| **Markdown Header Text Splitter** | A first pass that cuts documents at Markdown headings before the length-based split | `backend/open_webui/routers/retrieval.py:1756-1785` |
| **Chunk Min Size Target** | Merges chunks shorter than this into neighbours from the same file, when the heading splitter is on | `backend/open_webui/routers/retrieval.py:1574-1646`, `:1784-1785` |
| **Embedding** | A list of numbers representing the meaning of a text; similar meanings give nearby lists | `backend/open_webui/retrieval/utils.py:1115-1206` |
| **Embedding engine / model** | Who computes embeddings: the server itself with SentenceTransformers (engine empty, labelled "Default (SentenceTransformers)"), or an Ollama, OpenAI-compatible or Azure OpenAI service, using the named model | `backend/open_webui/routers/retrieval.py:149-169`; `src/lib/components/admin/Settings/Documents.svelte:1025-1030` |
| **Dimension** | How many numbers an embedding has; fixed by the model. Chunks made with one model cannot be compared reliably with a question embedded by another | `backend/open_webui/retrieval/vector/dbs/pgvector.py:288-333` |
| **Vector store** (vector database) | Where chunks and embeddings are kept and searched. Chosen once by the `VECTOR_DB` environment variable | `backend/open_webui/config.py:503`; `backend/open_webui/retrieval/vector/factory.py:14-100` |
| **Collection** | A named group of chunks in the vector store: one per uploaded file (`file-{id}`), one per knowledge base (its id), one per user's memories, and so on (section 6.2) | `backend/open_webui/retrieval/utils.py:1299-1362` |
| **Top K** | How many chunks are returned for each attached file or knowledge base | `backend/open_webui/retrieval/utils.py:699-787`; `backend/open_webui/config.py:968` |
| **Hybrid search** | Combining meaning-based (vector) search with keyword search (BM25), then rescoring the combined list | `backend/open_webui/retrieval/utils.py:493-615` |
| **BM25** | A classic keyword-matching score. **BM25 Weight** sets the balance: 0 is purely "semantic", 1 purely "lexical" | `backend/open_webui/retrieval/utils.py:547-579`; `src/lib/components/admin/Settings/Documents.svelte:1375-1421` |
| **Enrich Hybrid Search Text** | Adds file names, titles, section headings, source and snippet text to the keyword index | `backend/open_webui/retrieval/utils.py:372-403` |
| **Reranking** (reranker) | A second model that rescores candidate chunks against the question. Without a reranking model, hybrid search rescores by cosine similarity of embeddings | `backend/open_webui/retrieval/utils.py:1780-1851` |
| **Top K Reranker** | How many rescored chunks are kept; the final count is the smaller of Top K and Top K Reranker | `backend/open_webui/retrieval/utils.py:581-606` |
| **Relevance Threshold** | Minimum rescored score a chunk needs to be kept. Applied only in hybrid search | `backend/open_webui/retrieval/utils.py:1835-1836` |
| **Full Context Mode** | Admin switch: return every chunk of each attached item instead of searching | `backend/open_webui/retrieval/utils.py:1680-1683` |
| **Using Entire Document / Using Focused Retrieval** | Per-item switch in the file window: send the file's whole extracted text, or search its chunks | `src/lib/components/common/FileItemModal.svelte:343-370`; `backend/open_webui/retrieval/utils.py:1506-1541` |
| **Bypass Embedding and Retrieval** | Admin switch: uploaded files are not embedded, and attached files and knowledge bases are sent as their whole extracted text | `backend/open_webui/routers/retrieval.py:2071-2087`; `backend/open_webui/retrieval/utils.py:1386`, `:1506`, `:1592` |
| **RAG Template** | The instruction text wrapped around the retrieved passages; `{{CONTEXT}}` or `[context]` marks where they go | `backend/open_webui/utils/task.py:265-301`; `backend/open_webui/config.py:1070-1096` |
| **Source** | One retrieved item as the answer shows it: the passages from one file, page or web address, grouped under one chip | `src/lib/components/chat/Messages/Citations.svelte:108-153` |
| **Retrieval queries** | Search phrases written by the task model from the conversation; the user's last message is used when this is off or fails | `backend/open_webui/utils/middleware.py:2061-2101` |
| **External knowledge** | A read-only knowledge base backed by someone else's Qdrant, Milvus or pgvector collection | `backend/open_webui/retrieval/external.py:292-379` |
| **Slim image** | A Docker build (`USE_SLIM`) without local models or document tools; it needs external embedding, pgvector and an external extractor | `backend/open_webui/env.py:45`; `backend/open_webui/retrieval/vector/factory.py:20-24` |
| **Offline mode** | `OFFLINE_MODE`: the code loads models from the local cache only, so the embedding model must already be there | `backend/open_webui/env.py:1201-1205`; `backend/open_webui/retrieval/utils.py:1729-1730` |
| **Reindex** | Re-chunking and re-embedding existing content from its stored extracted text with the current embedding model; files are not extracted again | `backend/open_webui/routers/knowledge.py:374-462`; `backend/open_webui/routers/retrieval.py:1999-2013` |

## 5. Workflows (Step by Step)

### 5.1 From Upload to Answer (Overview)

1. **Upload.** The browser sends the file to `POST /api/v1/files/`. The files router checks the
   allowed extensions and the size limit, stores the file, marks it `pending` and processes it in the
   background (`backend/open_webui/routers/files.py:354-400`, `:416`, `:436-446`); see
   `files-uploads-and-storage.md`.
2. **Routing by type.** Audio is transcribed by speech-to-text and the transcript is processed instead
   (`backend/open_webui/routers/files.py:153-166`). Pictures attached in a chat are uploaded without
   processing and go to vision-capable models as images
   (`src/lib/components/chat/MessageInput.svelte:1188`). Images and videos uploaded **with** processing
   (for example into a knowledge base) are not extracted unless the admin has listed their media type
   for the extraction engine: videos are stored as they are, and images fail with
   `File type {content_type} is not supported for processing`
   (`backend/open_webui/routers/files.py:110-125`, `:168-188`). Everything else goes to
   `process_file` (`backend/open_webui/routers/files.py:190-200`).
3. **Extraction.** A loader chosen from the extraction engine and the file type turns the file into
   text, which is then cleaned of character-encoding mistakes (`backend/open_webui/routers/retrieval.py:2019-2047`;
   `backend/open_webui/retrieval/loaders/main.py:340-347`, `:517-818`). Sections 5.2 and 5.3.
4. **Text saved.** The whole extracted text is written to the file record (`data.content`) and its
   SHA-256 hash is calculated (`backend/open_webui/routers/retrieval.py:2061-2069`). This stored text
   is what **Using Entire Document**, bypass mode and reindexing use later.
5. **Bypass.** If **Bypass Embedding and Retrieval** is on, the file is marked `completed` here with
   no chunks or embeddings (`backend/open_webui/routers/retrieval.py:2071-2087`).
6. **Chunk, embed, store.** Otherwise the text is checked for duplicates, split into chunks, embedded
   and inserted into the collection `file-{id}`; the file is marked `completed` and its collection name
   recorded (`backend/open_webui/routers/retrieval.py:1705-1912`, `:2089-2149`). Sections 5.4 to 5.6.
7. **Failure.** Any error marks the file `failed` with the error text, clears its hash so the same file
   can be uploaded again after the cause is fixed, and publishes a `retrieval.content.process_failed`
   event (`backend/open_webui/routers/retrieval.py:2155-2189`).
8. **Browser waits.** The composer follows a status stream that the server checks once a second for up
   to two hours; a `failed` status becomes a yellow warning pop-up with the error, and the file stays
   attached (`backend/open_webui/routers/files.py:645-668`;
   `src/lib/components/chat/MessageInput.svelte:1022-1043`).
9. **Question time.** When the user sends a message, the chat pipeline gathers the attached items,
   asks the task model for search phrases, and calls `get_sources_from_items`
   (`backend/open_webui/utils/middleware.py:2049-2135`). Section 5.7.
10. **Per item**, the code sends the whole text, all chunks, or the best-matching chunks
    (`backend/open_webui/retrieval/utils.py:1407-1700`). Sections 5.7 to 5.9.
11. **Status.** A `sources_retrieved` status reports how many distinct sources were found
    (`backend/open_webui/utils/middleware.py:2137-2165`).
12. **Prompt.** The passages are wrapped in `<source>` tags, put into the RAG template and placed in
    front of the user's message (`backend/open_webui/utils/middleware.py:972-1008`, `:3234-3236`).
    Section 5.10.
13. **Answer and citations.** The model answers; the same sources go to the browser for the Sources
    button and the `[1]` chips (`backend/open_webui/utils/middleware.py:3238-3246`). Section 5.11.

### 5.2 Content Extraction Engines

The engine is the **Content Extraction Engine** setting (`rag.content_extraction_engine`, code default
empty, which is the built-in "Default") (`backend/open_webui/config.py:868`, `:2863`). For every
engine the code first refuses Office and e-book archives (`docx`, `epub`, `odt`, `pptx`, `xlsx`) that
would expand beyond the smaller of the upload size limit (100 MB when none is set) and the larger of
10 MB and 100 times the file's own size, with `Document archive is too large after decompression`
(`backend/open_webui/retrieval/loaders/main.py:520-539`).

An engine is used only when its required settings are present and the file type is one it handles;
**otherwise the built-in loaders of 5.3 are used without any message**
(`backend/open_webui/retrieval/loaders/main.py:541-699`).

| Engine (value) | Panel label | Used when | What it does | Failure behaviour | Source |
|---|---|---|---|---|---|
| (empty) | **Default** ("Basic text only" in the slim image) | Always available | Built-in loaders by file type (5.3) | Loader errors become the file's error | `backend/open_webui/retrieval/loaders/main.py:699-818`; `src/lib/components/admin/Settings/Documents.svelte:446-450` |
| `external` | **External** | Both **Document Loader URL** and its **API Key** are set (the panel itself only insists on the URL) | Sends the file with HTTP `PUT` to `{url}/process`, with the file name, optional custom headers (variables `{{FILE_ID}}`, `{{FILE_NAME}}`, `{{FILE_CONTENT_TYPE}}`) and the requesting user's identity | Raises `Error connecting to endpoint: {e}`, `Error loading document: {response.status_code} {response.text}`, `Error loading document: No content returned` or `Error loading document: Unable to parse content` | `backend/open_webui/retrieval/loaders/main.py:541-559`; `backend/open_webui/retrieval/loaders/external_document.py:38-95`; `src/lib/components/admin/Settings/Documents.svelte:165-171`, `:650-665` |
| `tika` | **Tika** | **Tika Server URL** is set (code default `http://tika:9998`) | Text-like files are read locally; others are sent to Apache Tika (`tika/text` for 3.x, `tika/json/md` for 4.x) | `Error calling Tika: {r.reason}`; a document with no text comes back as the literal text `<No text content found>` | `backend/open_webui/retrieval/loaders/main.py:215-253`, `:560-569`; `backend/open_webui/config.py:933-935` |
| `docling` | **Docling** | **Docling Server URL** is set (code default `http://docling:5001`) | Text-like files locally; others to Docling `v1/convert/file` with the JSON **Parameters**; page breaks produce one document per page | `Error calling Docling: ...`; no Markdown comes back as `<No text content found>` | `backend/open_webui/retrieval/loaders/main.py:256-329`, `:613-632`; `backend/open_webui/config.py:937-947` |
| `datalab_marker` | **Datalab Marker API** | An **API Key** is set and the file is `pdf`, `xls`, `xlsx`, `ods`, `doc`, `docx`, `odt`, `ppt`, `pptx`, `odp`, `html`, `epub`, `png`, `jpeg`, `jpg`, `webp`, `gif` or `tiff` | Posts to the Marker API (default `https://www.datalab.to/api/v1/marker` when the base URL is blank), polls every 2 seconds for up to 300 polls, returns Markdown, JSON or HTML | `Marker processing timed out`, `Marker returned empty content` and other messages in 10.2 | `backend/open_webui/retrieval/loaders/main.py:570-612`; `backend/open_webui/retrieval/loaders/datalab_marker.py:68-245` |
| `document_intelligence` | **Document Intelligence** | An endpoint is set and the file is `pdf`, `docx`, `ppt` or `pptx` | Azure AI Document Intelligence, Markdown output, model default `prebuilt-layout`; with no key it uses the server's Azure identity | Errors from the Azure library become the file's error | `backend/open_webui/retrieval/loaders/main.py:633-659`; `backend/open_webui/retrieval/loaders/local.py:99-121`; `backend/open_webui/config.py:949-953` |
| `mistral_ocr` | **Mistral OCR** | An **API Key** is set and the file is a `pdf` | Uploads to Mistral, gets a signed link, runs `mistral-ocr-latest`, deletes the upload (or sends the PDF inline with **Use Base64**); retries network errors, 5xx and 429 up to 3 attempts | **Does not fail the file**: errors become the document text `Error during processing: {e}` | `backend/open_webui/retrieval/loaders/main.py:676-687`; `backend/open_webui/retrieval/loaders/mistral.py:145-167`, `:234-263`, `:357-411` |
| `paddleocr_vl` | **PaddleOCR-vl** | Base URL **and** token are set (the panel itself only insists on the URL) and the file is `pdf`, `png`, `jpg`, `jpeg`, `bmp`, `tiff` or `webp` | Sends the file to the PaddleOCR-vl `layout-parsing` service | **Does not fail the file**: errors become the text `Error during OCR processing: {e}` | `backend/open_webui/retrieval/loaders/main.py:688-698`; `backend/open_webui/retrieval/loaders/paddleocr_vl.py:14-127` |
| `mineru` | **MinerU** | The extension is in **File Extensions** (code default `pdf`) | **local** mode posts to `{url}/file_parse` with the **API Timeout** (code default 300 seconds); **cloud** mode needs a key, uploads, and polls for up to 10 minutes | Messages in 10.2, for example `MinerU Local API request timed out` | `backend/open_webui/retrieval/loaders/main.py:660-675`; `backend/open_webui/retrieval/loaders/mineru.py:58-519`; `backend/open_webui/config.py:901-917` |

Notes:

- **Data leaving the server.** Every engine except Default (and the local parts of Tika and Docling)
  sends the file to another service. The **External** loader always adds the requesting user's
  identity (name, user id, email and role, or a signed token when one is configured), whatever the
  `ENABLE_FORWARD_USER_INFO_HEADERS` switch says (`backend/open_webui/retrieval/loaders/external_document.py:56-57`;
  `backend/open_webui/utils/headers.py:52-83`). Mistral OCR receives the identity only when that switch
  is on (`backend/open_webui/env.py:989`; `backend/open_webui/retrieval/loaders/mistral.py:83-84`).
  Which services production uses, and whether they are approved for the data involved, is **TO BE
  CONFIRMED** (MedIT GPT chats may hold health information).
- **Marker keeps a copy.** The Datalab Marker loader also writes the extracted text to
  `/app/backend/data/uploads/marker_output/` (`backend/open_webui/retrieval/loaders/datalab_marker.py:211-224`),
  and no code in the repository removes those copies.
- **Web loaders.** `external_web.py`, `tavily.py`, `youtube.py` and `microsoft_web_iq.py` in the same
  folder load web pages and YouTube transcripts; they are documented in
  `web-search-and-web-loading.md`.

### 5.3 The Built-In Loaders (Default Engine)

| File type | Loader | Notes | Source |
|---|---|---|---|
| `pdf` | pypdf | **PDF Loader Mode** `page` (code default) makes one document per page with page numbers; `single` joins pages so chunks can cross page boundaries. With **PDF Extract Images (OCR)** on, images inside each page are read with RapidOCR | `backend/open_webui/retrieval/loaders/pdf.py:12-101`; `backend/open_webui/retrieval/loaders/main.py:713-718` |
| `csv` | Built-in CSV reader | One document per row, written as `column: value` lines; with `ENABLE_RAG_CSV_SUMMARY=true` a first summary row gives the row and column counts | `backend/open_webui/retrieval/loaders/main.py:129-186`, `:719-724` |
| `docx` | docx2txt | Plain text only | `backend/open_webui/retrieval/loaders/local.py:38-47` |
| `doc`, `epub`, `msg`, `odt` | unstructured | Fail with "Processing .doc files requires the 'unstructured' package..." (and the same for `.epub`, `.msg`, `.odt`) when that package is missing; `.msg` accepts Outlook and plain e-mail files only | `backend/open_webui/retrieval/loaders/main.py:749-812`; `backend/open_webui/retrieval/loaders/local.py:50-96` |
| `xls`, `xlsx` | unstructured, else pandas | One text block per sheet in the fallback | `backend/open_webui/retrieval/loaders/main.py:107-126`, `:770-782` |
| `ppt`, `pptx` | unstructured, else python-pptx | Slide text only in the fallback | `backend/open_webui/retrieval/loaders/main.py:189-212`, `:783-795` |
| `rst`, `xml` | unstructured, else plain text | | `backend/open_webui/retrieval/loaders/main.py:725-744` |
| `htm`, `html` | BeautifulSoup | Page text and title | `backend/open_webui/retrieval/loaders/local.py:26-35`; `backend/open_webui/retrieval/loaders/main.py:745-746` |
| `md`, source code, `json`, `yaml`, `svg` and any other type | Plain text | Encoding detected (UTF-8 first, then Chinese, Japanese and Korean encodings, then latin-1) | `backend/open_webui/retrieval/loaders/main.py:39-95`, `:376-476`, `:747-748`, `:813-816` |

In the **slim** image only CSV, HTML and text-like files are read locally; anything else fails with
`This file type requires an external document extractor in slim. Configure one that supports it.`
(`backend/open_webui/retrieval/loaders/main.py:700-712`).

**Temporary chats** are different: the browser extracts the text itself (PDF.js and similar) and does not
send the file to these loaders (`src/lib/components/chat/MessageInput.svelte:1052-1084`;
`src/lib/utils/index.ts:1910-1990`); see `files-uploads-and-storage.md`.

### 5.4 Chunking

1. **Duplicate check.** If the target collection already holds chunks with the same content hash from a
   **different** file, processing stops with
   `Duplicate content detected. Please provide unique content to proceed.`; the same file being
   re-added is allowed (`backend/open_webui/routers/retrieval.py:1734-1753`). In practice this happens
   when two files with identical extracted text go into one knowledge base; each chat upload gets its
   own collection.
2. **Heading split.** With **Markdown Header Text Splitter** on (code default on), text is cut at
   Markdown headings `#` to `######`, keeping the heading in the chunk
   (`backend/open_webui/routers/retrieval.py:1756-1783`; `backend/open_webui/config.py:1057`).
3. **Merge small pieces.** If **Chunk Min Size Target** is above 0 (code default 0), pieces smaller
   than it are merged with neighbours from the same file without exceeding **Chunk Size**
   (`backend/open_webui/routers/retrieval.py:1574-1646`, `:1784-1785`; `backend/open_webui/config.py:1066`).
   The panel shows this field only while the heading splitter is on
   (`src/lib/components/admin/Settings/Documents.svelte:986-1000`).
4. **Length split.** The **Text Splitter** decides the unit (`backend/open_webui/routers/retrieval.py:1787-1817`):
   - Default (Character): pieces of at most **Chunk Size** characters (code default 1,000) with **Chunk
     Overlap** characters shared (code default 100) (`backend/open_webui/config.py:1064-1068`);
   - Token (Tiktoken): the same numbers counted in tokens of `TIKTOKEN_ENCODING_NAME` (code default
     `cl100k_base`, `backend/open_webui/config.py:1061`);
   - Token (Transformers): counted with the **Tokenizer Model**, or with the local embedding model's own
     tokenizer when that field is empty; unavailable in the slim image
     (`backend/open_webui/routers/retrieval.py:1649-1694`).
5. **Empty result.** No chunks at all (for example a scanned PDF with no text layer and OCR off) stops
   with `The content provided is empty. Please ensure that there is text or data present before proceeding.`
   (`backend/open_webui/routers/retrieval.py:1819-1820`; `backend/open_webui/constants.py:95`).
6. Chunk text is cleaned of characters databases cannot store, and each chunk's metadata records the
   file id, name, source, page (for PDFs), the content hash and the embedding engine and model that
   made it (`backend/open_webui/routers/retrieval.py:1822-1833`, `:2034-2047`, `:2108-2112`).

### 5.5 Embedding

- **Local (engine empty, "Default (SentenceTransformers)").** The model is loaded into each server
  process at startup and whenever an admin saves embedding settings (`backend/open_webui/main.py:684`;
  `backend/open_webui/routers/retrieval.py:149-169`, `:564-567`). It runs on the CPU, or on CUDA or Apple
  MPS when available (`backend/open_webui/env.py:44-73`). The files come from the Hugging Face cache
  (`SENTENCE_TRANSFORMERS_HOME`); the code downloads or updates them only when
  `RAG_EMBEDDING_MODEL_AUTO_UPDATE` is on (code default on) and `OFFLINE_MODE` is off
  (`backend/open_webui/retrieval/utils.py:1721-1759`; `backend/open_webui/config.py:1013-1015`). A short
  name such as `all-MiniLM-L6-v2` is treated as `sentence-transformers/all-MiniLM-L6-v2`
  (`backend/open_webui/retrieval/utils.py:1744-1746`).
- **If the local model cannot be loaded**, startup continues, the log has
  `Error loading SentenceTransformer: {e}`, and every embedding request then fails with
  `No embedding model is loaded. Set RAG_EMBEDDING_MODEL to a valid SentenceTransformer model name, or configure an external RAG_EMBEDDING_ENGINE (ollama, openai, azure_openai).`
  (`backend/open_webui/routers/retrieval.py:166-167`; `backend/open_webui/retrieval/utils.py:1131-1137`).
- **Ollama.** `POST {url}/api/embed`, long inputs truncated by Ollama; errors read
  `Ollama embed error ({r.status}): {error_detail}` (`backend/open_webui/retrieval/utils.py:1078-1112`).
- **OpenAI-compatible.** `POST {url}/embeddings` (`backend/open_webui/retrieval/utils.py:929-960`).
  The base URL and key default to the main OpenAI connection's environment values when the embedding
  ones are not set (`backend/open_webui/config.py:1098-1099`).
- **Azure OpenAI.** `POST {url}/openai/deployments/{model}/embeddings?api-version={version}`; the model
  field is the deployment name (`backend/open_webui/retrieval/utils.py:1005-1042`).
- **Batching.** Texts are sent in batches of **Embedding Batch Size** (code default 1); with **Async
  Embedding Processing** on (code default on) the batches run in parallel, limited by **Embedding
  Concurrent Requests** (code default 0, meaning no limit) (`backend/open_webui/retrieval/utils.py:1162-1200`;
  `backend/open_webui/config.py:1019-1025`). One failed batch fails the whole file; provider rate-limit
  answers are not retried by these calls (`backend/open_webui/retrieval/utils.py:955`, `:1037`,
  `:1104-1107`, `:1188-1193`).
- **Time limits.** Each HTTP call uses the server-wide `AIOHTTP_CLIENT_TIMEOUT`
  (`backend/open_webui/retrieval/utils.py:946-948`); the whole file's embedding waits up to
  `RAG_EMBEDDING_TIMEOUT` seconds, which is unset (no limit) by default
  (`backend/open_webui/routers/retrieval.py:1879-1889`; `backend/open_webui/env.py:736-743`).
- **Prefixes.** Some models expect "query:" and "passage:" style prefixes. `RAG_EMBEDDING_QUERY_PREFIX`,
  `RAG_EMBEDDING_CONTENT_PREFIX` and `RAG_EMBEDDING_PREFIX_FIELD_NAME` (environment-only, unset by default)
  add them (`backend/open_webui/config.py:1027-1031`; `backend/open_webui/retrieval/utils.py:1220-1224`).
- **Identity forwarding.** With `ENABLE_FORWARD_USER_INFO_HEADERS` on, embedding and reranking requests
  carry the user's identity to the provider (`backend/open_webui/retrieval/utils.py:943-944`;
  `backend/open_webui/retrieval/models/external.py:46-47`).

### 5.6 Saving to the Vector Store

- **Where chunks go.** A chat upload goes to its own collection `file-{id}`
  (`backend/open_webui/routers/retrieval.py:1945-1949`). Adding a file to a knowledge base copies the
  file's chunks into the knowledge base's collection and embeds them again with the current model
  (`backend/open_webui/routers/retrieval.py:1979-1998`, `:2100-2115`). If the file's own chunks are
  missing but its text is stored, both collections are rebuilt from the stored text
  (`backend/open_webui/routers/retrieval.py:1999-2013`).
- **Existing collections.** Re-processing a file whose collection already exists does nothing unless the
  call asks to add or overwrite (`backend/open_webui/routers/retrieval.py:1836-1844`). Editing a file's
  text (`/files/{id}/data/content/update`) deletes the file's collection and re-embeds the new text
  (`backend/open_webui/routers/retrieval.py:1954-1978`).
- **Ids.** Each chunk gets a random id; the vector store client is called once for the whole batch
  (`backend/open_webui/routers/retrieval.py:1892-1906`).
- **File status** moves from `pending` to `completed` or `failed`; while a file is being linked to a
  knowledge base it shows `processing` (`backend/open_webui/routers/files.py:237-238`, `:416`;
  `backend/open_webui/routers/retrieval.py:2129-2134`, `:2158-2165`).

### 5.7 Retrieval at Question Time

**When it runs.** For every message, unless the model's **file context** capability is switched off
(it is on unless set), the pipeline runs `chat_completion_files_handler` over the items attached to the
message (`backend/open_webui/utils/middleware.py:3206-3213`). Knowledge attached to a custom model and
folder files join those items only in legacy function-calling mode (section 5.12).

**Search phrases.** Unless every item is in full-context mode, the task model is asked to write search
phrases from the conversation (setting `task.query.retrieval.enable`, code default on) and a `Querying`
status shows them; when generation is off or fails, the user's last message is the search phrase
(`backend/open_webui/utils/middleware.py:2058-2104`; `backend/open_webui/routers/tasks.py:412-416`).
The task model is described in `chat-completion-pipeline-and-generation-tasks.md`.

**Settings are read on every message.** Top K, Top K Reranker, the threshold, the BM25 weight, hybrid
search and full context mode are fetched from the `config` table each time, so an admin's change applies
from the next message (`backend/open_webui/utils/middleware.py:2105-2114`). The embedding and reranking
**models**, by contrast, live in each server process (section 6.5).

**Each attached item** is turned into passages (`backend/open_webui/retrieval/utils.py:1407-1700`):

| Item | What the model gets | Source |
|---|---|---|
| Uploaded file (`file`) | With **Using Entire Document** or bypass mode: the stored extracted text. Otherwise the file's collection `file-{id}` is searched, or all its chunks are taken in Full Context Mode | `backend/open_webui/retrieval/utils.py:1505-1564`, `:1679-1691` |
| Knowledge base (`collection`) | External knowledge base: the external store is searched (5.15). With **Using Entire Document** or bypass: the stored text of every file in it. Otherwise the knowledge base's collection is searched, or all its chunks are taken in Full Context Mode | `backend/open_webui/retrieval/utils.py:1566-1636` |
| Pasted or browser-extracted text, web page or YouTube attachment (`text`) | The whole text in full-context mode (web attachments are added that way), else its collection if it has one, else its text | `backend/open_webui/retrieval/utils.py:1411-1439`; `src/lib/components/chat/Chat.svelte:1801-1809` |
| Note (`note`) | The note's Markdown, if the user may read it | `backend/open_webui/retrieval/utils.py:1441-1459` |
| Chat (`chat`) | The referenced chat's whole conversation, if the user may read it | `backend/open_webui/retrieval/utils.py:1461-1496` |
| Link (`url`) | The fetched page text | `backend/open_webui/retrieval/utils.py:1498-1504` |
| Folder (`folder`, legacy mode) | Expanded into the folder's files | `backend/open_webui/retrieval/utils.py:1393-1405`; `backend/open_webui/utils/middleware.py:2591-2602` |

**The search itself** (focused retrieval, hybrid search off):

1. All search phrases are embedded in one call with the current embedding model
   (`backend/open_webui/retrieval/utils.py:753-761`).
2. Each collection is searched with each phrase in parallel; a collection whose search raises is skipped
   and logged (`backend/open_webui/retrieval/utils.py:739-785`).
3. Results are merged; a chunk found twice keeps its best score; the list is sorted by score and cut to
   **Top K** (code default 3) **for that item**, so three attached files can contribute up to nine
   chunks (`backend/open_webui/retrieval/utils.py:639-679`, `:787`; `backend/open_webui/config.py:968`).
4. No relevance threshold is applied in this path; the threshold belongs to hybrid search (5.8).

**Status.** After retrieval a `sources_retrieved` status counts the distinct sources; the browser
shows `Retrieved {count} sources`, `Retrieved 1 source` or `No sources found`
(`backend/open_webui/utils/middleware.py:2137-2165`;
`src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:104-124`). If
retrieval raises an error, the error goes to the server log and the user sees the same
`No sources found` as when nothing matched (`backend/open_webui/utils/middleware.py:2115-2137`). The
search of an external knowledge base is not wrapped separately, so an unreachable external source can
empty the sources of the whole message (`backend/open_webui/retrieval/utils.py:1581-1589`).

### 5.8 Hybrid Search, BM25 and Reranking

With **Hybrid Search** on (code default off, `backend/open_webui/config.py:973`), each collection is
searched like this (`backend/open_webui/retrieval/utils.py:493-615`, `:699-733`, `:790-896`):

1. **Native hybrid (pgvector only).** When the store can do it and **Enrich Hybrid Search Text** is off,
   the database runs a full-text search and a vector search and merges them by weighted rank; only the
   pgvector backend implements this (`backend/open_webui/retrieval/utils.py:423-490`;
   `backend/open_webui/retrieval/vector/dbs/pgvector.py:579-640`;
   `backend/open_webui/retrieval/vector/utils.py:91-148`).
2. **Otherwise, in the server.** Every chunk of the collection is fetched to build a BM25 keyword index
   (with the enrichment text when that switch is on), the vector search fetches Top K candidates, and
   the two lists are fused with the **BM25 Weight** (0 gives vector only, 1 gives keyword only, code
   default 0.5) (`backend/open_webui/retrieval/utils.py:520-579`; `backend/open_webui/config.py:971`).
   Fetching every chunk makes hybrid search heavier on large knowledge bases.
3. **Rescoring.** The candidates are scored by the reranking model if one is loaded, otherwise by the
   cosine similarity between the question's and the chunks' embeddings, which embeds the candidates
   again (`backend/open_webui/retrieval/utils.py:1809-1826`).
4. **Threshold and count.** Candidates scoring below **Relevance Threshold** (code default 0.0) are
   dropped; the best **Top K Reranker** (code default 3) are kept, and if Top K is smaller the list is
   cut to Top K (`backend/open_webui/retrieval/utils.py:1835-1847`, `:598-606`;
   `backend/open_webui/config.py:969-970`).
5. **Fallbacks.** A failing native search falls back to the in-server method; if hybrid search fails for
   every collection, plain vector search is used (`backend/open_webui/retrieval/utils.py:488-490`,
   `:893-894`, `:732-733`). If an external reranker errors, all candidates are returned unscored
   with the log line `No valid scores found, check your reranking function. Returning original documents.`
   (`backend/open_webui/retrieval/models/external.py:67-69`;
   `backend/open_webui/retrieval/utils.py:1849-1851`).

**Reranking models** (`backend/open_webui/routers/retrieval.py:172-242`):

| Reranking engine | Model | How scores are made | Source |
|---|---|---|---|
| Default (SentenceTransformers), engine empty | Any cross-encoder name; the panel suggests `BAAI/bge-reranker-v2-m3` when the engine is switched; code default empty (no reranker) | Cross-encoder scores, squashed to 0-1 by a sigmoid unless `SENTENCE_TRANSFORMERS_CROSS_ENCODER_SIGMOID_ACTIVATION_FUNCTION` is off | `backend/open_webui/routers/retrieval.py:207-224`; `backend/open_webui/env.py:1156-1158`; `src/lib/components/admin/Settings/Documents.svelte:1254-1260`; `backend/open_webui/config.py:1035` |
| Default, model `jinaai/jina-colbert-v2` | ColBERT | Scores normalized across the candidates so they add up to 1 | `backend/open_webui/routers/retrieval.py:195-206`; `backend/open_webui/retrieval/models/colbert.py:35-74` |
| External | Model name sent to the service | `POST` to the **API Base URL** with the model, question and passages; reads `relevance_score` per passage | `backend/open_webui/retrieval/models/external.py:13-69` |

A reranking model is loaded only while hybrid search is on and bypass mode is off, at startup and
whenever the Documents settings are saved (`backend/open_webui/main.py:685-697`;
`backend/open_webui/routers/retrieval.py:1235-1250`). Section 5.14 covers what happens when loading
fails.

### 5.9 Full Context Mode, Entire Document and Bypass Embedding and Retrieval

| Mode | Set by | What the model receives | Embedded at upload? | Scores shown? | Source |
|---|---|---|---|---|---|
| **Focused retrieval** (default) | Nothing | The best chunks per item (5.7, 5.8) | Yes | Yes | `backend/open_webui/retrieval/utils.py:1684-1691` |
| **Using Entire Document** | The user, per file or knowledge base in the file window; Settings > Interface > **Default Upload Mode**; or a model's knowledge marked full context | The file's whole stored text (for a knowledge base, every file's text) | Yes | No | `src/lib/components/common/FileItemModal.svelte:343-370`; `src/lib/components/chat/MessageInput.svelte:945`; `src/lib/components/workspace/Models/Knowledge.svelte:56`; `backend/open_webui/retrieval/utils.py:1506-1541`, `:1592-1621` |
| **Full Context Mode** | Admin, Documents > **Retrieval** (`rag.full_context`, code default off) | Every chunk of every attached item | Yes | No | `backend/open_webui/retrieval/utils.py:1680-1683`; `backend/open_webui/config.py:979` |
| **Bypass Embedding and Retrieval** | Admin, Documents > **Content Extraction** (`rag.bypass_embedding_and_retrieval`, code default off) | The whole stored text of attached files and knowledge-base files | **No**: files are not chunked or embedded | No | `backend/open_webui/routers/retrieval.py:2071-2087`; `backend/open_webui/retrieval/utils.py:1386`, `:1506`, `:1592`; `backend/open_webui/config.py:965` |

Things to know:

- When every attached item is in full-context mode, no search phrases are generated
  (`backend/open_webui/utils/middleware.py:2058-2061`).
- Whole documents can exceed the model's context window; the provider's error then appears in the
  reply as described in `chat-completion-pipeline-and-generation-tasks.md`.
- While bypass mode is on, nothing is embedded, so files uploaded during that time have no chunks. If
  bypass is later switched off, the Reindex button rebuilds knowledge-base files from their stored
  text, but chat-only uploads stay unsearchable until uploaded again (inferred from
  `backend/open_webui/routers/knowledge.py:374-438` and `backend/open_webui/retrieval/utils.py:1542-1564`;
  section 14).
- The panel hides hybrid search, reranking and Top K while Full Context Mode is on, and hides the whole
  Embedding section and most Retrieval controls while bypass mode is on
  (`src/lib/components/admin/Settings/Documents.svelte:1004`, `:1215`, `:1226`).

### 5.10 How Retrieved Text Is Added to the Prompt (RAG Template)

1. Each passage is wrapped as `<source id="N" name="...">passage</source>`. The number `N` is given per
   distinct source (the passage's `source` metadata, usually the file name or web address) in the order
   first met; `name` is the attached item's name (`backend/open_webui/utils/middleware.py:940-969`).
   Extra metadata attributes are added only for keys listed in `RAG_SOURCE_METADATA_KEYS`
   (environment-only, empty by default, `backend/open_webui/env.py:375`;
   `backend/open_webui/retrieval/utils.py:1365-1367`).
2. The passages replace `{{CONTEXT}}` or `[context]` in the **RAG Template**; `{{QUERY}}` or `[query]`
   becomes the user's message. An empty template means the built-in default
   (`backend/open_webui/utils/task.py:265-301`). The panel warns when a custom template has more than
   one context placeholder: "This template contains multiple context placeholders..."
   (`src/lib/components/admin/Settings/Documents.svelte:1444-1450`).
3. The filled template is placed **before the user's latest message** in the same turn; with
   `RAG_SYSTEM_CONTEXT=true` it is appended to the system prompt instead
   (`backend/open_webui/utils/middleware.py:996-1008`; `backend/open_webui/utils/misc.py:658-671`,
   `:701-717`; `backend/open_webui/env.py:372`).
4. The built-in template (`backend/open_webui/config.py:1070-1094`) tells the model to answer from the
   context, to say when it does not know, to answer in the user's language, to use its own knowledge
   when the context lacks the answer (and say so), and to cite with `[id]` only when a source carries an
   id. That instruction is why answers contain `[1]`, `[2]` markers.

### 5.11 How Citations and Source Chips Relate to Retrieved Chunks

- **What the browser receives.** One entry per attached item, holding the list of passages, the
  passages' metadata and, for searched items, their scores (`backend/open_webui/retrieval/utils.py:1702-1718`;
  `backend/open_webui/utils/middleware.py:3238-3246`).
- **Grouping.** The Sources list regroups passages by their `source` metadata (for uploaded files the
  file name, for web pages the address), so the count reads distinct sources, not chunks; the status
  line counts the same way (`src/lib/components/chat/Messages/Citations.svelte:108-148`;
  `backend/open_webui/utils/middleware.py:2141-2156`). Two different files with the same name would
  share one chip and one number (inferred, section 14).
- **Numbering.** The prompt numbers sources by the same key in the same order, so `[2]` in the answer
  normally opens the second entry of the Sources list (sources with neither a name nor an id are left
  out of the list sent to the browser, which could shift the numbers) (`backend/open_webui/utils/middleware.py:947-950`,
  `:3238-3243`; `src/lib/components/chat/Messages/Citations.svelte:27-76`).
- **What the score means.** The citation window shows each passage's score
  (`src/lib/components/chat/Messages/Citations/CitationModal.svelte:181-206`). Its meaning depends on the
  path: plain vector search in Chroma or pgvector reports a rescaled similarity where about 0.5 means
  unrelated (`backend/open_webui/retrieval/vector/dbs/chroma.py:91-95`;
  `backend/open_webui/retrieval/vector/dbs/pgvector.py:566-568`); a cross-encoder reranker gives 0 to 1;
  ColBERT shares 1 across the candidates; hybrid search without a reranker gives cosine similarity;
  passages sent whole have no score. Percentages are therefore comparable only within one answer.
- **Display switches.** If the model's **citations** capability is off, no Sources button appears and
  the markers are removed; the fork's **Inline Citations** setting removes only the markers
  (`src/lib/components/chat/Messages/ResponseMessage.svelte:934-941`;
  `src/lib/components/chat/Messages/ContentRenderer.svelte:128-137`). Screen details are in
  `chat-composer-and-message-display.md` (5.16).

### 5.12 When Documents Are Not Searched Automatically

| Situation | What happens instead | Source |
|---|---|---|
| A custom model has knowledge attached and uses **native** function calling (the default) | The knowledge is listed to the model as `<attached_knowledge>` and reached only if the model calls the built-in knowledge tools; no automatic search, no `Searching Knowledge for ...` status | `backend/open_webui/utils/middleware.py:2604-2644`, `:3099-3123`, `:2809-2813` |
| The same model in **legacy** function calling | Its knowledge bases are added as items and searched as in 5.7, with the `Searching Knowledge for "{searchQuery}"` status | `backend/open_webui/utils/middleware.py:2604-2644` |
| Chat inside a folder with files, native mode | Folder files are offered to the built-in tools instead of being searched | `backend/open_webui/utils/middleware.py:2591-2602` |
| The model's **file context** capability is off | Attached files are not searched into the prompt | `backend/open_webui/utils/middleware.py:3206-3213` |

Built-in tool results also produce source chips when the model's citations capability is on
(`backend/open_webui/utils/middleware.py:5836-5842`, `:6089-6111`). Function-calling modes and model
capabilities are explained in `chat-completion-pipeline-and-generation-tasks.md` and
`workspace-models-and-model-access.md`.

### 5.13 Changing the Embedding Model and Reindexing

What an admin does, and what the code does at each step:

1. **Change the engine or model** in Documents > **Embedding**. Switching the engine pre-fills a model:
   empty for Ollama, `text-embedding-3-small` for OpenAI and Azure OpenAI,
   `sentence-transformers/all-MiniLM-L6-v2` for the default engine
   (`src/lib/components/admin/Settings/Documents.svelte:1010-1031`).
2. **Apply it**, with the download button next to the model (default engine only) or with **Save**,
   which applies embedding settings first unless bypass mode is on
   (`src/lib/components/admin/Settings/Documents.svelte:1137-1165`, `:239-241`). The panel refuses a
   filesystem path, an empty Ollama or OpenAI model, or incomplete Azure settings (10.3)
   (`src/lib/components/admin/Settings/Documents.svelte:82-115`).
3. **The server** unloads the old local model, saves the settings and loads the new model in the
   process that received the request (`backend/open_webui/routers/retrieval.py:521-535`, `:537-599`). A
   failure returns `[ERROR: Error updating embedding configuration]`
   (`backend/open_webui/routers/retrieval.py:621-626`; `backend/open_webui/constants.py:16-24`).
4. **New uploads** use the new model straight away: each upload builds its embedding function from the
   saved settings (`backend/open_webui/routers/retrieval.py:1846-1875`). Questions use the process's
   loaded embedding function, which only the process that handled the save has replaced (section 6.5).
5. **Old chunks keep old embeddings.** What users then see depends on the store:
   - **Chroma** (default): a size mismatch should make the Chroma library raise an error, which the
     search code swallows, returning nothing and logging nothing, so affected files and knowledge bases
     give `No sources found` (`backend/open_webui/retrieval/vector/dbs/chroma.py:74-107`). Adding a new
     file to an existing knowledge-base collection built with the old model is expected to fail with the
     library's own dimension error (both inferred, section 14).
   - **pgvector**: every vector is padded or cut to a fixed length (`PGVECTOR_INITIALIZE_MAX_VECTOR_LENGTH`,
     code default 1,536), so searches run but compare unlike embeddings and return poor matches
     (`backend/open_webui/retrieval/vector/dbs/pgvector.py:324-333`; `backend/open_webui/config.py:653`).
   - **Elasticsearch** keeps one index per embedding size, so old and new chunks sit in different indexes
     (`backend/open_webui/retrieval/vector/dbs/elasticsearch.py:59-60`).
   - **Memories** are re-embedded automatically for a user the next time a memory write hits a size
     mismatch (`backend/open_webui/routers/memories.py:171-180`).
6. **Reindex.** Danger Zone > **Reindex Knowledge and Memory Vectors** > **Reindex** asks
   `Reindex Embedding Data` / `Rebuild knowledge file, knowledge search, and memory vectors using the current embedding model.`
   and then calls three endpoints in order, stopping at the first error, and shows `Success` when all
   three return (`src/lib/components/admin/Settings/Documents.svelte:382-416`, `:1576-1591`):
   - **knowledge files** (`/api/v1/knowledge/reindex`): for each knowledge base, its collection is
     deleted, then for each file the file's own collection is deleted and both are rebuilt from the
     file's stored text with the current model. It runs inside the request, one file at a time; progress
     appears only in the server log (one `Reindexing knowledge base ...` line per file, 10.7), and a
     file that fails is logged and skipped while the endpoint still reports success
     (`backend/open_webui/routers/knowledge.py:374-462`);
   - **knowledge search** (`/api/v1/knowledge/metadata/reindex`): rebuilds the `knowledge-bases`
     collection of names and descriptions (`backend/open_webui/routers/knowledge.py:469-494`);
   - **memories** (`/api/v1/memories/reindex`): deletes and re-embeds every user's memories
     (`backend/open_webui/routers/memories.py:128-168`, `:449-480`).
7. **Not covered by Reindex:** files attached only to chats (their `file-{id}` collections), and
   collections made from pasted text or web pages. They keep the old model's embeddings; users can
   upload the file again or switch it to **Using Entire Document** (inferred from the endpoints above;
   section 14).

### 5.14 Changing the Reranking Model

- Reranking controls appear only while **Hybrid Search** is on
  (`src/lib/components/admin/Settings/Documents.svelte:1235-1314`).
- On **Save**, the old local reranker is unloaded, the new settings are stored, and the new model is
  loaded if hybrid search is on and bypass mode is off
  (`backend/open_webui/routers/retrieval.py:1187-1250`).
- **If loading fails** (wrong name, no network for the download, offline mode without a cached copy),
  the server logs `Error loading reranking model: {e}`, switches **Hybrid Search off** and saves that,
  and the admin still sees `Settings saved successfully!`
  (`backend/open_webui/routers/retrieval.py:1251-1253`, `:1398`;
  `src/lib/components/chat/SettingsModal.svelte:460-464`). Reopening the panel shows hybrid search off.
- At startup the same load happens; a failure there is logged as `Error updating models: {e}` and the
  server runs without a reranker (`backend/open_webui/main.py:685-697`).
- The external reranker's timeout (`rag.external_reranker_timeout`) has no field on the panel; it comes
  from `RAG_EXTERNAL_RERANKER_TIMEOUT` (empty means the library default)
  (`backend/open_webui/config.py:1052`; `backend/open_webui/routers/retrieval.py:181-182`).

### 5.15 External Knowledge Sources

External knowledge connects MedIT GPT to a vector collection that someone else filled, in Qdrant,
Milvus or PostgreSQL with pgvector, and presents it as a read-only knowledge base. The panel is marked
Experimental (`src/lib/components/admin/Settings/ExternalKnowledge.svelte:797-802`).

1. Admin Settings > **Integrations** > **Knowledge**: the **Add Connection** button (+) opens **Add
   Knowledge Connection** (`src/lib/components/admin/Settings/ExternalKnowledge.svelte:413-418`,
   `:804-812`).
2. The admin fills **Name**, **Provider** (Qdrant, Milvus or pgvector), **Description**, **Endpoint**,
   **Timeout** (30 seconds by default), **API Key / Token** (not for pgvector), **Database** (Milvus),
   **Collection**, **Table** and **Collection Field** (pgvector), **Content Field**, **Vector Field**,
   **Metadata Field**, **Document ID Field** and a **Test Query**, plus read access for users, groups or
   everyone (`src/lib/components/admin/Settings/ExternalKnowledge.svelte:436-776`). Choosing a provider
   fills the field names it usually uses (`src/lib/components/admin/Settings/ExternalKnowledge.svelte:90-119`).
   The form notes `External vectors must be generated with the same embedding model configured in Open WebUI.`
   (`src/lib/components/admin/Settings/ExternalKnowledge.svelte:761-763`).
3. **Verify Connection** runs the test query (`POST /api/v1/knowledge/external/source/test`) and
   reports `Test succeeded.` or `Test returned no results.`
   (`src/lib/components/admin/Settings/ExternalKnowledge.svelte:274-300`).
4. **Create** (or **Save** when editing) is allowed only after a successful test; the server repeats the
   test, stores the connection in the `external_knowledge.connections` setting and creates a knowledge
   base marked external and read-only (`src/lib/components/admin/Settings/ExternalKnowledge.svelte:302-370`;
   `backend/open_webui/routers/knowledge.py:944-1006`, `:1009-1088`).
5. The list shows each source with its provider and collection, a **Configure** button and an
   **Enabled** switch that turns the connection on or off
   (`src/lib/components/admin/Settings/ExternalKnowledge.svelte:815-871`).
6. **At question time**, when the knowledge base is attached, the question is embedded with MedIT GPT's
   own embedding model and sent to the external store; the top results become sources directly, without
   hybrid search, reranking or the threshold (`backend/open_webui/retrieval/utils.py:1581-1589`;
   `backend/open_webui/retrieval/external.py:292-379`). A disabled connection raises
   `External knowledge connection is disabled` (`backend/open_webui/retrieval/external.py:320-321`).

Using, sharing and attaching external knowledge bases is covered in `knowledge-bases.md`.

### 5.16 Danger Zone Actions

| Action | Confirmation shown | What the code actually removes | Source |
|---|---|---|---|
| **Reset Upload Directory** ("Delete uploaded files from the upload directory.") | `Confirm your action` / `This action cannot be undone. Do you wish to continue?` | Calls `DELETE /api/v1/files/all`, which deletes **every user's** file records and stored files and then **empties the whole vector store** (all files, knowledge bases, memories and web-search collections) | `src/lib/components/admin/Settings/Documents.svelte:354-366`, `:1548-1561`; `backend/open_webui/routers/files.py:575-597`; `src/lib/components/common/ConfirmDialog.svelte:143-153`; `src/lib/i18n/locales/en-US/translation.json:2328-2329` |
| **Reset Vector Storage/Knowledge** ("Clear vector storage and knowledge indexing data.") | The same default confirmation | Empties the whole vector store and deletes **every knowledge base record**; uploaded files remain | `src/lib/components/admin/Settings/Documents.svelte:368-380`, `:1562-1575`; `backend/open_webui/routers/retrieval.py:3271-3284`; `src/lib/i18n/locales/en-US/translation.json:2330-2331` |
| **Reindex Knowledge and Memory Vectors** | `Reindex Embedding Data` | Rebuilds, does not delete content (5.13) | `src/lib/components/admin/Settings/Documents.svelte:382-416`, `:1576-1591` |

The panel shows `Success` for **Reset Vector Storage/Knowledge** as soon as the request is sent, without
waiting for the server's answer, so the pop-up is not proof that the reset worked
(`src/lib/components/admin/Settings/Documents.svelte:370-379`). Tier 1 does not use these buttons.

### 5.17 Startup, Model Downloads and Offline Mode

- At startup each server process loads the local embedding model (when the engine is empty) and the
  reranker (when hybrid search is on), then builds its embedding and reranking functions
  (`backend/open_webui/main.py:368`, `:621-752`).
- The vector store client is created when the code is first imported in the standard image, so a
  misconfigured or unreachable store can stop the server from starting
  (`backend/open_webui/retrieval/vector/factory.py:100`;
  `backend/open_webui/retrieval/vector/dbs/pgvector.py:186-189`). The configuration also refuses to start
  with `VECTOR_DB=pgvector` and no PostgreSQL address, or with more than 2,000 dimensions without
  `PGVECTOR_USE_HALFVEC` (`backend/open_webui/config.py:648-663`).
- The Docker image downloads the default embedding model at build time into
  `/app/backend/data/cache/embedding/models` (`Dockerfile:14`, `:102-112`, `:160-180`); without Docker,
  the first start downloads it (`backend/open_webui/config.py:524`).
- With `OFFLINE_MODE=true` no model is ever downloaded (`backend/open_webui/env.py:1201-1205`;
  `backend/open_webui/config.py:1013-1015`). A model missing from the cache then fails to load, and
  every upload and every document search fails with the `No embedding model is loaded...` message of 5.5
  (`backend/open_webui/retrieval/utils.py:1729-1730`, `:1755-1758`, `:1131-1137`).
- The slim image refuses a local embedding engine (`Slim requires an external embedding engine (openai, ollama, azure_openai).`),
  local rerankers and Chroma, and needs `PGVECTOR_DB_URL`
  (`backend/open_webui/routers/retrieval.py:539-540`, `:988-1003`;
  `backend/open_webui/retrieval/vector/factory.py:20-24`, `:113-114`). Whether production runs the slim
  image is **TO BE CONFIRMED**.

### 5.18 The Public Embeddings Endpoint Is Separate

`POST /api/embeddings` (and `/api/v1/embeddings`) is an OpenAI-compatible service for API callers. It
looks up the requested **chat model** among the connected providers, applies model access control, and
forwards the request to Ollama or the OpenAI-compatible connection
(`backend/open_webui/main.py:1072-1094`; `backend/open_webui/utils/embeddings.py:42-88`). It does not use
the Documents embedding settings, so a problem with one says nothing about the other. See
`public-api-and-integrations.md`.

## 6. Data Model

This area keeps data in two places: rows in the relational database (file records, knowledge-base
records, settings) and chunks in the vector store. Table layouts are documented in
`database-schema-content-and-collaboration.md`; this section lists what retrieval reads and writes.

### 6.1 Relational Records Used Here

| Record | Fields this area uses | Meaning | Source |
|---|---|---|---|
| `file` | `hash` | SHA-256 of the extracted text; set on success, cleared on failure | `backend/open_webui/models/files.py:18-31`; `backend/open_webui/routers/retrieval.py:2069`, `:2134`, `:2165` |
| `file` | `data.content` | The whole extracted text (what full-text modes and reindexing use) | `backend/open_webui/routers/retrieval.py:2064-2068` |
| `file` | `data.status`, `data.error` | `pending`, `processing`, `completed` or `failed`, and the error text shown to the user | `backend/open_webui/routers/files.py:237-238`, `:262-268`, `:416`; `backend/open_webui/routers/retrieval.py:2129-2134`, `:2158-2163` |
| `file` | `meta.collection_name`, `meta.content_type`, `path` | Which collection holds the chunks; the type used to pick a loader; where the stored file is | `backend/open_webui/routers/retrieval.py:2021-2032`, `:2121-2127` |
| `knowledge` | `meta.source`, `meta.read_only`, `meta.external` | Marks an external knowledge base and records its connection id, collection and field names, provider and capabilities | `backend/open_webui/routers/knowledge.py:991-1006` |
| `config` | every `rag.*` key, `file.image_compression_width`, `file.image_compression_height`, `google_drive.enable`, `onedrive.enable` | The Documents settings (section 7) | `backend/open_webui/config.py:2857-2940` |
| `config` | `external_knowledge.connections` | The list of external connections; not in the seeded defaults, created on first save | `backend/open_webui/routers/knowledge.py:559`, `:629-634` |
| Chat history (assistant message) | `sources` | The sources of a reply, **including the passage text**, saved with the message | `backend/open_webui/utils/middleware.py:4900-4917`; `backend/open_webui/socket/main.py:1235-1250` |
| User settings | `defaultUploadContext` | `full` or `focused` for the Default Upload Mode | `src/lib/components/common/InterfaceSettings.svelte:1911-1915` |

Because passages are saved inside replies, text from a document stays readable in old chats after the
file or knowledge base is deleted (inferred from the storage above; section 14). File and chat
deletion rules are in `files-uploads-and-storage.md` and
`chat-conversations-history-and-organisation.md`.

### 6.2 Collections in the Vector Store

| Collection name | Holds | Created by | Source |
|---|---|---|---|
| `file-{file id}` | The chunks of one uploaded file | Processing the upload | `backend/open_webui/routers/retrieval.py:1945-1949` |
| `{knowledge base id}` | The chunks of every file in one knowledge base | Adding files to the knowledge base | `backend/open_webui/routers/retrieval.py:1979-2017`; `backend/open_webui/routers/files.py:236-244` |
| `knowledge-bases` | One entry per knowledge base (name and description) for knowledge-base search | Creating or editing a knowledge base; metadata reindex | `backend/open_webui/routers/knowledge.py:89-115`, `:469-494` |
| `user-memory-{user id}` | One user's memories | Adding memories | `backend/open_webui/routers/memories.py:134`, `:171-180` |
| `web-search-{user id}-{hash}` | Web search results for one search | Web search (see `web-search-and-web-loading.md`) | `backend/open_webui/routers/retrieval.py:3013` |
| SHA-256 of the text or of the web address | Pasted text or a web page processed without a named collection | `/process/text`, `/process/web` | `backend/open_webui/routers/retrieval.py:2207-2209`, `:2461-2463` |
| A bare file id | Older ("legacy") items | Earlier versions | `backend/open_webui/retrieval/utils.py:1549-1550`, `:1561-1562` |

How names map onto stores: Chroma keeps one collection per name
(`backend/open_webui/retrieval/vector/dbs/chroma.py:144-148`); pgvector keeps every chunk in one table,
`document_chunk`, with a `collection_name` column (`backend/open_webui/retrieval/vector/dbs/pgvector.py:72-83`);
Milvus prefixes names with `open_webui_` (`backend/open_webui/retrieval/vector/dbs/milvus.py:73`, `:196`);
the Milvus and Qdrant multitenancy modes fold everything into five shared collections (memories,
knowledge, files, web search and hash-based) (`backend/open_webui/retrieval/vector/dbs/milvus_multitenancy.py:68-107`;
`backend/open_webui/retrieval/vector/dbs/qdrant_multitenancy.py:85-90`); OpenSearch uses one index per
name (`backend/open_webui/retrieval/vector/dbs/opensearch.py:33-42`); Elasticsearch uses one index per
embedding size (`backend/open_webui/retrieval/vector/dbs/elasticsearch.py:44`, `:59-60`).

### 6.3 What One Chunk Holds

| Part | Content | Source |
|---|---|---|
| `id` | A random identifier | `backend/open_webui/routers/retrieval.py:1892-1900` |
| `text` | The chunk text, cleaned for storage | `backend/open_webui/routers/retrieval.py:1822` |
| `vector` | The embedding | `backend/open_webui/routers/retrieval.py:1896` |
| `metadata` | `name` and `source` (the file name), `file_id`, `created_by` (the uploader's user id), `hash`, the splitter's `start_index`, page fields for PDFs, filtered file metadata, and `embedding_config` with the engine and model that made the vector | `backend/open_webui/routers/retrieval.py:1788-1792`, `:1823-1833`, `:2034-2047`, `:2108-2112`; `backend/open_webui/retrieval/loaders/pdf.py:40-51` |

Large metadata values (whole tables, page structures) are dropped before storage
(`backend/open_webui/retrieval/vector/utils.py:8-61`; `backend/open_webui/env.py:841-848`). Chunk
metadata holds a personal identifier (`created_by`), so the vector store is personal data like the main
database.

### 6.4 Vector Store Backends

The backend is chosen by the environment variable `VECTOR_DB` (code default `chroma`, or `pgvector` in
the slim image); it is not a persistent setting (`backend/open_webui/config.py:503`;
`tools/ground-truth.md`). Every backend except Chroma and pgvector carries the source note
"community-supported and maintained on a best-effort basis" (first lines of each file in
`backend/open_webui/retrieval/vector/dbs/`).

| `VECTOR_DB` | What it is | Settings (environment) | Notes | Source |
|---|---|---|---|---|
| `chroma` (default) | Chroma, embedded in the server with files in `DATA_DIR/vector_db`, or a Chroma server when `CHROMA_HTTP_HOST` is set | `CHROMA_HTTP_HOST`, `CHROMA_HTTP_PORT` (8000), `CHROMA_HTTP_SSL`, `CHROMA_HTTP_HEADERS`, `CHROMA_TENANT`, `CHROMA_DATABASE`, `CHROMA_CLIENT_AUTH_PROVIDER`, `CHROMA_CLIENT_AUTH_CREDENTIALS` | Scores rescaled to 0-1; a failing search returns no results and logs nothing | `backend/open_webui/config.py:505-523`; `backend/open_webui/retrieval/vector/dbs/chroma.py:32-107` |
| `pgvector` | PostgreSQL with the pgvector extension, table `document_chunk` | `PGVECTOR_DB_URL` (defaults to the main `DATABASE_URL`), `PGVECTOR_INITIALIZE_MAX_VECTOR_LENGTH` (1536), `PGVECTOR_USE_HALFVEC`, `PGVECTOR_INDEX_METHOD`, `PGVECTOR_HNSW_M`, `PGVECTOR_HNSW_EF_CONSTRUCTION`, `PGVECTOR_IVFFLAT_LISTS`, `PGVECTOR_ITERATIVE_SCAN`, `PGVECTOR_CREATE_EXTENSION`, `PGVECTOR_PGCRYPTO`, pool settings | The only backend with native hybrid search; vectors padded or cut to the fixed length; a changed length or index method stops startup with an explanation | `backend/open_webui/config.py:647-746`; `backend/open_webui/retrieval/vector/dbs/pgvector.py:89-333`, `:579-640` |
| `qdrant` | Qdrant server | `QDRANT_URI`, `QDRANT_API_KEY`, `QDRANT_ON_DISK`, `QDRANT_PREFER_GRPC`, `QDRANT_GRPC_PORT` (6334), `QDRANT_TIMEOUT` (5), `QDRANT_HNSW_M`, `ENABLE_QDRANT_MULTITENANCY_MODE` (**on**), `QDRANT_COLLECTION_PREFIX` (`open-webui`) | Multitenancy mode is the code default | `backend/open_webui/config.py:611-620`; `backend/open_webui/retrieval/vector/factory.py:37-47` |
| `milvus` | Milvus, or a local Milvus Lite file `DATA_DIR/vector_db/milvus.db` by default | `MILVUS_URI`, `MILVUS_DB`, `MILVUS_TOKEN`, `MILVUS_INDEX_TYPE` (HNSW), `MILVUS_METRIC_TYPE` (COSINE), index tuning values, `ENABLE_MILVUS_MULTITENANCY_MODE` (off), `MILVUS_COLLECTION_PREFIX` | | `backend/open_webui/config.py:596-609`; `backend/open_webui/retrieval/vector/factory.py:26-36` |
| `opensearch` | OpenSearch | `OPENSEARCH_URI` (`https://localhost:9200`), `OPENSEARCH_SSL`, `OPENSEARCH_CERT_VERIFY`, `OPENSEARCH_USERNAME`, `OPENSEARCH_PASSWORD` | | `backend/open_webui/config.py:631-636` |
| `elasticsearch` | Elasticsearch | `ELASTICSEARCH_URL`, `ELASTICSEARCH_CA_CERTS`, `ELASTICSEARCH_API_KEY`, `ELASTICSEARCH_USERNAME`, `ELASTICSEARCH_PASSWORD`, `ELASTICSEARCH_CLOUD_ID`, `SSL_ASSERT_FINGERPRINT`, `ELASTICSEARCH_INDEX_PREFIX` | One index per embedding size | `backend/open_webui/config.py:638-646` |
| `pinecone` | Pinecone cloud index | `PINECONE_API_KEY`, `PINECONE_ENVIRONMENT`, `PINECONE_INDEX_NAME` (`open-webui-index`), `PINECONE_DIMENSION` (1536), `PINECONE_METRIC` (cosine), `PINECONE_CLOUD` (aws) | Fixed dimension; missing settings stop startup | `backend/open_webui/config.py:791-797`; `backend/open_webui/retrieval/vector/dbs/pinecone.py:85-128` |
| `s3vector` | Amazon S3 Vectors | `S3_VECTOR_BUCKET_NAME`, `S3_VECTOR_REGION` | | `backend/open_webui/config.py:824-826` |
| `weaviate` | Weaviate | `WEAVIATE_HTTP_HOST`, `WEAVIATE_GRPC_HOST`, `WEAVIATE_HTTP_PORT` (8080), `WEAVIATE_GRPC_PORT` (50051), `WEAVIATE_API_KEY`, `WEAVIATE_HTTP_SECURE`, `WEAVIATE_GRPC_SECURE`, `WEAVIATE_SKIP_INIT_CHECKS` | | `backend/open_webui/config.py:622-629` |
| `oracle23ai` | Oracle Database 23ai vector search | `ORACLE_DB_USE_WALLET`, `ORACLE_DB_USER`, `ORACLE_DB_PASSWORD`, `ORACLE_DB_DSN`, `ORACLE_WALLET_DIR`, `ORACLE_WALLET_PASSWORD`, `ORACLE_VECTOR_LENGTH` (768), pool sizes | | `backend/open_webui/config.py:799-811` |
| `opengauss` | openGauss | `OPENGAUSS_DB_URL` (defaults to `DATABASE_URL`), `OPENGAUSS_INITIALIZE_MAX_VECTOR_LENGTH` (1536), pool settings | | `backend/open_webui/config.py:748-781` |
| `mariadb-vector` | MariaDB with vector support (implemented in `mariadb_vector.py`) | `MARIADB_VECTOR_DB_URL`, `MARIADB_VECTOR_INITIALIZE_MAX_VECTOR_LENGTH` (1536), `MARIADB_VECTOR_DISTANCE_STRATEGY` (cosine), `MARIADB_VECTOR_INDEX_M` (8), pool settings | | `backend/open_webui/config.py:527-581`; `backend/open_webui/retrieval/vector/type.py:6`; `backend/open_webui/retrieval/vector/dbs/mariadb_vector.py:1-3` |
| `valkey` | Valkey with the valkey-search module (Valkey 9.0.1 or newer, valkey-search 1.2.0 or newer) | `VALKEY_URL`, `VALKEY_COLLECTION_PREFIX`, `VALKEY_INDEX_TYPE` (HNSW), `VALKEY_DISTANCE_METRIC` (COSINE), `VALKEY_HNSW_M`, `VALKEY_HNSW_EF_CONSTRUCTION`, `VALKEY_HNSW_EF_RUNTIME` | | `backend/open_webui/config.py:828-835`; `backend/open_webui/retrieval/vector/dbs/valkey.py:1-2` |

Credentials for these stores are environment values; never copy them into a ticket.

### 6.5 Running State Held in Each Server Process

Each server process keeps its own loaded local embedding model (`app.state.ef`), reranker
(`app.state.rf`), embedding and reranking functions (`EMBEDDING_FUNCTION`, `RERANKING_FUNCTION`), a
cached tokenizer for the Transformers splitter, and one vector store client
(`backend/open_webui/main.py:666-752`; `backend/open_webui/routers/retrieval.py:1661-1672`;
`backend/open_webui/retrieval/vector/factory.py:100-123`). An admin save replaces them only in the
process that handled the request (`backend/open_webui/routers/retrieval.py:564-597`, `:1235-1250`), and
no code in this area tells other processes to reload. With several workers or replicas, the other
processes would keep answering with the previous embedding or reranking model until they restart
(inferred; section 14). The deployment shape is **TO BE CONFIRMED** (see `tools/ground-truth.md`).

## 7. Settings and Configuration

Every Documents setting is a persistent setting: a row in the `config` table seeded from an
environment variable at first boot, after which the stored value wins over the environment
(`tools/ground-truth.md`, Settings). The **live values are data, TO BE CONFIRMED** for production. The
complete key catalogue is `configuration-persistent-settings-r-to-w.md`; environment variables are in
`configuration-environment-variables-bootstrap.md`. Labels below are the English text of the dotted
keys `settings.admin.documents.*` in `src/lib/i18n/locales/en-US/translation.json` (lines cited per
row); the panel is `src/lib/components/admin/Settings/Documents.svelte`.

### 7.1 Documents > Content Extraction

| Label | Description (English text) | Config key and seeding variable | Code default | Shown when | Source |
|---|---|---|---|---|---|
| Content Extraction Engine | "Choose how uploaded documents are parsed before indexing." | `rag.content_extraction_engine` (`CONTENT_EXTRACTION_ENGINE`) | empty (Default) | Always; options Default, External, Tika, Docling, Datalab Marker API, Document Intelligence, Mistral OCR, PaddleOCR-vl, MinerU | `src/lib/components/admin/Settings/Documents.svelte:441-460`; `src/lib/i18n/locales/en-US/translation.json:2224-2225`; `backend/open_webui/config.py:868`, `:2863` |
| Supported Media MIME Types | "Media upload MIME types the content extraction engine may process." | `rag.content_extraction.supported_media_mime_types` (`CONTENT_EXTRACTION_SUPPORTED_MEDIA_MIME_TYPES`) | unset: only the External engine receives images and videos; a list sends matching media to whichever engine is set; an emptied list sends none | Always (placeholder `image/*, video/*`) | `src/lib/components/admin/Settings/Documents.svelte:462-471`, `:284-289`; `src/lib/i18n/locales/en-US/translation.json:2342-2343`; `backend/open_webui/config.py:870-875`; `backend/open_webui/routers/files.py:110-125` |
| PDF Extract Images (OCR) | "Extract images from PDFs so OCR can process image-only pages." | `rag.pdf_extract_images` (`PDF_EXTRACT_IMAGES`) | off | Default engine (the value is also passed to Tika) | `src/lib/components/admin/Settings/Documents.svelte:473-480`; `src/lib/i18n/locales/en-US/translation.json:2307-2308`; `backend/open_webui/config.py:1004`; `backend/open_webui/retrieval/loaders/main.py:233-234` |
| PDF Loader Mode | "Page mode creates one document per page. Single mode keeps pages together for chunking across boundaries." | `rag.pdf_loader_mode` (`PDF_LOADER_MODE`) | `page` | Default engine; options Page, Single | `src/lib/components/admin/Settings/Documents.svelte:482-490`; `src/lib/i18n/locales/en-US/translation.json:2309-2310`; `backend/open_webui/config.py:1006` |
| API Base URL (Datalab Marker) | "Datalab Marker service endpoint used for document parsing." | `rag.datalab_marker_api_base_url` | empty (the loader then uses `https://www.datalab.to/api/v1/marker`) | Datalab Marker API | `src/lib/components/admin/Settings/Documents.svelte:492-501`; `src/lib/i18n/locales/en-US/translation.json:2226-2227`; `backend/open_webui/config.py:879`; `backend/open_webui/retrieval/loaders/main.py:595-597` |
| API Key (Datalab Marker) | "API key used to authenticate with Datalab Marker." | `rag.datalab_marker_api_key` | empty | Datalab Marker API | `src/lib/components/admin/Settings/Documents.svelte:503-513`; `src/lib/i18n/locales/en-US/translation.json:2228-2229`; `backend/open_webui/config.py:877` |
| Additional Config | "JSON options passed to Marker for advanced parsing behavior." | `rag.datalab_marker_additional_config` | empty | Datalab Marker API | `src/lib/components/admin/Settings/Documents.svelte:515-532`; `src/lib/i18n/locales/en-US/translation.json:2196-2197`; `backend/open_webui/config.py:881` |
| Use LLM, Skip Cache, Force OCR, Paginate, Strip Existing OCR, Disable Image Extraction, Format Lines | See the descriptions at the cited lines (for example Force OCR: "Run OCR on all PDF pages, even pages with embedded text.") | `rag.datalab_marker_use_llm`, `_skip_cache`, `_force_ocr`, `_paginate`, `_strip_existing_ocr`, `_disable_image_extraction`, `_format_lines` | all off | Datalab Marker API | `src/lib/components/admin/Settings/Documents.svelte:534-588`; `src/lib/i18n/locales/en-US/translation.json:2230-2231`, `:2260-2263`, `:2305-2306`, `:2338-2341`, `:2360-2361`; `backend/open_webui/config.py:883-897` |
| Output Format | "Text output format returned by Marker." | `rag.datalab_marker_output_format` | `markdown` (Markdown, JSON, HTML) | Datalab Marker API | `src/lib/components/admin/Settings/Documents.svelte:589-598`; `src/lib/i18n/locales/en-US/translation.json:2301-2302`; `backend/open_webui/config.py:899` |
| Document Loader URL | "External service endpoint used to load document content." | `rag.external_document_loader_url` | empty | External | `src/lib/components/admin/Settings/Documents.svelte:600-610`; `src/lib/i18n/locales/en-US/translation.json:2242-2243`; `backend/open_webui/config.py:919` |
| API Key (external loader) | "API key sent to the external document loader." | `rag.external_document_loader_api_key` | empty; **required by the loader**, although the panel does not insist | External | `src/lib/components/admin/Settings/Documents.svelte:611-623`; `src/lib/i18n/locales/en-US/translation.json:2256-2257`; `backend/open_webui/config.py:921`; `backend/open_webui/retrieval/loaders/main.py:541-545` |
| Headers | "Additional JSON headers sent to the external document loader." | `rag.external_document_loader_headers` | none; a **Header variables** hint lists `{{FILE_ID}}`, `{{FILE_NAME}}`, `{{FILE_CONTENT_TYPE}}` | External | `src/lib/components/admin/Settings/Documents.svelte:626-667`; `src/lib/i18n/locales/en-US/translation.json:2268-2270`; `backend/open_webui/config.py:923-931` |
| Tika Server URL | "Tika server endpoint used for content extraction." | `rag.tika_server_url` (`TIKA_SERVER_URL`) | `http://tika:9998` | Tika | `src/lib/components/admin/Settings/Documents.svelte:670-679`; `src/lib/i18n/locales/en-US/translation.json:2346-2347`; `backend/open_webui/config.py:933` |
| Tika Server Version | "Select the Tika server API version." | `rag.tika_server_version` | `3` (Tika 3.x or 4.x) | Tika | `src/lib/components/admin/Settings/Documents.svelte:680-688`; `src/lib/i18n/locales/en-US/translation.json:2348-2349`; `backend/open_webui/config.py:935` |
| Docling Server URL, API Key, Parameters | "Docling service endpoint used for parsing."; "API key sent to Docling."; "Additional Docling parameters in JSON format." | `rag.docling_server_url`, `rag.docling_api_key`, `rag.docling_params` | `http://docling:5001`, empty, `{}` | Docling | `src/lib/components/admin/Settings/Documents.svelte:690-725`; `src/lib/i18n/locales/en-US/translation.json:2232-2237`; `backend/open_webui/config.py:937-947` |
| Endpoint, Key, Document Intelligence Model | "Document Intelligence endpoint used for parsing."; "Credential used for Document Intelligence."; "Model name used by Document Intelligence." | `rag.document_intelligence_endpoint`, `rag.document_intelligence_key`, `rag.document_intelligence_model` | empty, empty, `prebuilt-layout` | Document Intelligence | `src/lib/components/admin/Settings/Documents.svelte:726-760`; `src/lib/i18n/locales/en-US/translation.json:2238-2241`, `:2252-2253`; `backend/open_webui/config.py:949-953` |
| API Base URL, API Key, Use Base64 (Mistral) | "Mistral OCR service endpoint."; "API key sent to Mistral OCR."; "Send PDFs as base64 data URLs instead of uploading first." | `rag.mistral_ocr_api_base_url`, `rag.mistral_ocr_api_key`, `rag.mistral_ocr_use_base64` | `https://api.mistral.ai/v1`, empty, off | Mistral OCR | `src/lib/components/admin/Settings/Documents.svelte:761-790`; `src/lib/i18n/locales/en-US/translation.json:2287-2290`, `:2358-2359`; `backend/open_webui/config.py:955-959` |
| API Base URL, API Token (PaddleOCR-vl) | "PaddleOCR-vl service endpoint."; "API token sent to PaddleOCR-vl." | `rag.paddleocr_vl_base_url`, `rag.paddleocr_vl_token` | `http://localhost:8080`, empty | PaddleOCR-vl | `src/lib/components/admin/Settings/Documents.svelte:791-814`; `src/lib/i18n/locales/en-US/translation.json:2204-2205`, `:2303-2304`; `backend/open_webui/config.py:961-963` |
| API Mode, API URL, API Key, API Timeout, Parameters, File Extensions (MinerU) | "Choose the local or cloud MinerU API mode." and the texts at the cited lines | `rag.mineru_api_mode`, `rag.mineru_api_url`, `rag.mineru_api_key`, `rag.mineru_api_timeout`, `rag.mineru_params`, `rag.mineru_file_extensions` | `local`, `http://localhost:8000`, empty, `300` (the field's placeholder shows 60), `{}`, `pdf`; switching mode swaps in `https://mineru.net/api/v4` or `http://localhost:8000` | MinerU | `src/lib/components/admin/Settings/Documents.svelte:815-901`; `src/lib/i18n/locales/en-US/translation.json:2200-2203`, `:2206-2207`, `:2258-2259`, `:2283-2286`; `backend/open_webui/config.py:901-917` |
| Bypass Embedding and Retrieval | "Inject the entire content as context for comprehensive processing." (when on); "Use segmented retrieval for focused and relevant context." (when off) | `rag.bypass_embedding_and_retrieval` (`BYPASS_EMBEDDING_AND_RETRIEVAL`) | off | Always | `src/lib/components/admin/Settings/Documents.svelte:904-915`; `src/lib/i18n/locales/en-US/translation.json:2216-2217`; `backend/open_webui/config.py:965` |
| Text Splitter | "Choose how extracted text is split before indexing." | `rag.text_splitter` (`RAG_TEXT_SPLITTER`) | empty, shown as Default (Character); also Token (Tiktoken) and Token (Transformers), the last disabled in slim | Bypass off | `src/lib/components/admin/Settings/Documents.svelte:918-929`; `src/lib/i18n/locales/en-US/translation.json:2344-2345`; `backend/open_webui/config.py:1055` |
| Tokenizer Model | "Tokenizer model used for transformer token splitting." | `rag.tokenizer_model` (`RAG_TOKENIZER_MODEL`) | empty (uses the local embedding model's tokenizer); required on the form when the embedding engine is not local | Token (Transformers) | `src/lib/components/admin/Settings/Documents.svelte:931-944`; `src/lib/i18n/locales/en-US/translation.json:2351-2352`; `backend/open_webui/config.py:1011` |
| Markdown Header Text Splitter | "Split documents by markdown headers before character or token splitting." | `rag.enable_markdown_header_text_splitter` | on | Bypass off | `src/lib/components/admin/Settings/Documents.svelte:946-955`; `src/lib/i18n/locales/en-US/translation.json:2277-2278`; `backend/open_webui/config.py:1057` |
| Chunk Size | "Maximum size for each text chunk." | `rag.chunk_size` (`CHUNK_SIZE`) | 1000 | Bypass off | `src/lib/components/admin/Settings/Documents.svelte:958-970`; `src/lib/i18n/locales/en-US/translation.json:2222-2223`; `backend/open_webui/config.py:1064` |
| Chunk Overlap | "Overlap preserved between neighboring chunks." | `rag.chunk_overlap` (`CHUNK_OVERLAP`) | 100 | Bypass off | `src/lib/components/admin/Settings/Documents.svelte:971-983`; `src/lib/i18n/locales/en-US/translation.json:2220-2221`; `backend/open_webui/config.py:1068` |
| Chunk Min Size Target | "Merge chunks smaller than this threshold when possible. Set to 0 to disable merging." | `rag.chunk_min_size_target` (`CHUNK_MIN_SIZE_TARGET`) | 0 | Heading splitter on | `src/lib/components/admin/Settings/Documents.svelte:986-1000`; `src/lib/i18n/locales/en-US/translation.json:2218-2219`; `backend/open_webui/config.py:1066` |

### 7.2 Documents > Embedding (Hidden While Bypass Is On)

| Label | Description (English text) | Config key and seeding variable | Code default | Source |
|---|---|---|---|---|
| Embedding Model Engine | "Provider used to generate document embeddings." | `rag.embedding_engine` (`RAG_EMBEDDING_ENGINE`) | empty, shown as Default (SentenceTransformers), disabled in slim; also Ollama, OpenAI, Azure OpenAI | `src/lib/components/admin/Settings/Documents.svelte:1006-1032`; `src/lib/i18n/locales/en-US/translation.json:2250-2251`; `backend/open_webui/config.py:1002` |
| API Base URL, API Key (OpenAI) | "OpenAI-compatible embeddings endpoint."; "API key for embedding requests." | `rag.openai.api_base_url` (`RAG_OPENAI_API_BASE_URL`), `rag.openai.api_key` (`RAG_OPENAI_API_KEY`) | the main OpenAI connection's environment values | `src/lib/components/admin/Settings/Documents.svelte:1034-1058`; `src/lib/i18n/locales/en-US/translation.json:2297-2300`; `backend/open_webui/config.py:1098-1099` |
| API Base URL, API Key (Ollama) | "Ollama endpoint used for embeddings."; "Optional API key for Ollama requests." | `rag.ollama.base_url` (`RAG_OLLAMA_BASE_URL`), `rag.ollama.api_key` | the main `OLLAMA_BASE_URL`; empty | `src/lib/components/admin/Settings/Documents.svelte:1059-1083`; `src/lib/i18n/locales/en-US/translation.json:2291-2294`; `backend/open_webui/config.py:1105-1107` |
| API Base URL, API Key, Version (Azure OpenAI) | "Azure OpenAI endpoint used for embeddings."; "Azure OpenAI API key."; "Azure OpenAI API version." | `rag.azure_openai.base_url`, `rag.azure_openai.api_key`, `rag.azure_openai.api_version` | empty | `src/lib/components/admin/Settings/Documents.svelte:1084-1118`; `src/lib/i18n/locales/en-US/translation.json:2210-2213`, `:2362-2363`; `backend/open_webui/config.py:1101-1103` |
| Embedding Model | "Model used to generate embeddings. Reindex knowledge after changing this." | `rag.embedding_model` (`RAG_EMBEDDING_MODEL`) | `sentence-transformers/all-MiniLM-L6-v2` (the Docker build argument `USE_EMBEDDING_MODEL` has the same default) | `src/lib/components/admin/Settings/Documents.svelte:1121-1172`; `src/lib/i18n/locales/en-US/translation.json:2248-2249`; `backend/open_webui/config.py:1008`; `Dockerfile:14`, `:102` |
| Embedding Batch Size | "Number of items processed per embedding batch." | `rag.embedding_batch_size` (`RAG_EMBEDDING_BATCH_SIZE`, or the older `RAG_EMBEDDING_OPENAI_BATCH_SIZE`) | 1 | `src/lib/components/admin/Settings/Documents.svelte:1174-1186`; `src/lib/i18n/locales/en-US/translation.json:2244-2245`; `backend/open_webui/config.py:1019-1021` |
| Async Embedding Processing | "Run embedding tasks concurrently to speed up processing." | `rag.enable_async_embedding` (`ENABLE_ASYNC_EMBEDDING`) | on; shown for Ollama, OpenAI and Azure OpenAI | `src/lib/components/admin/Settings/Documents.svelte:1188-1195`; `src/lib/i18n/locales/en-US/translation.json:2208-2209`; `backend/open_webui/config.py:1023` |
| Embedding Concurrent Requests | "Maximum concurrent embedding requests. Set to 0 for unlimited." | `rag.embedding_concurrent_requests` (`RAG_EMBEDDING_CONCURRENT_REQUESTS`) | 0 | `src/lib/components/admin/Settings/Documents.svelte:1196-1209`; `src/lib/i18n/locales/en-US/translation.json:2246-2247`; `backend/open_webui/config.py:1025` |

### 7.3 Documents > Retrieval

| Label | Description (English text) | Config key and seeding variable | Code default | Shown when | Source |
|---|---|---|---|---|---|
| Full Context Mode | "Inject entire documents as context for comprehensive processing." (on); "Use segmented retrieval for focused context." (off) | `rag.full_context` (`RAG_FULL_CONTEXT`) | off | Bypass off | `src/lib/components/admin/Settings/Documents.svelte:1216-1224`; `src/lib/i18n/locales/en-US/translation.json:2264-2265`; `backend/open_webui/config.py:979` |
| Hybrid Search | "Combine semantic and keyword retrieval." | `rag.enable_hybrid_search` (`ENABLE_RAG_HYBRID_SEARCH`) | off | Full context off | `src/lib/components/admin/Settings/Documents.svelte:1227-1233`; `src/lib/i18n/locales/en-US/translation.json:2271-2272`; `backend/open_webui/config.py:973` |
| Enrich Hybrid Search Text | "Add filenames, titles, sections, and snippets to improve lexical recall." | `rag.enable_hybrid_search_enriched_texts` | off | Hybrid on | `src/lib/components/admin/Settings/Documents.svelte:1236-1245`; `src/lib/i18n/locales/en-US/translation.json:2254-2255`; `backend/open_webui/config.py:975-977` |
| Reranking Engine | "Provider used to rerank hybrid search results." | `rag.reranking_engine` (`RAG_RERANKING_ENGINE`) | empty (Default (SentenceTransformers), disabled in slim) or External | Hybrid on | `src/lib/components/admin/Settings/Documents.svelte:1247-1267`; `src/lib/i18n/locales/en-US/translation.json:2324-2325`; `backend/open_webui/config.py:1033` |
| API Base URL, API Key (reranker) | "External reranker endpoint."; "API key sent to the external reranker." | `rag.external_reranker_url`, `rag.external_reranker_api_key` | empty | Engine External | `src/lib/components/admin/Settings/Documents.svelte:1269-1300`; `src/lib/i18n/locales/en-US/translation.json:2311-2314`; `backend/open_webui/config.py:1048-1050` |
| Reranking Model | "Model used to rerank retrieved results." | `rag.reranking_model` (`RAG_RERANKING_MODEL`) | empty (no reranker; hybrid search then rescores by cosine similarity) | Hybrid on | `src/lib/components/admin/Settings/Documents.svelte:1302-1313`; `src/lib/i18n/locales/en-US/translation.json:2326-2327`; `backend/open_webui/config.py:1035` |
| Reranking Batch Size | "Number of results processed per reranking batch." | `rag.reranking_batch_size` (`RAG_RERANKING_BATCH_SIZE`) | 32 | Full context off (also visible with hybrid off, where it has no effect) | `src/lib/components/admin/Settings/Documents.svelte:1316-1328`; `src/lib/i18n/locales/en-US/translation.json:2322-2323`; `backend/open_webui/config.py:1046` |
| Top K | "Maximum number of retrieved chunks returned to the model." | `rag.top_k` (`RAG_TOP_K`) | 3 (applies per attached item) | Full context off | `src/lib/components/admin/Settings/Documents.svelte:1330-1342`; `src/lib/i18n/locales/en-US/translation.json:2353-2354`; `backend/open_webui/config.py:968` |
| Top K Reranker | "Maximum number of hybrid results sent to the reranker." | `rag.top_k_reranker` (`RAG_TOP_K_RERANKER`) | 3. In the code it is the number **kept after** rescoring, not the number sent (5.8) | Hybrid on | `src/lib/components/admin/Settings/Documents.svelte:1344-1357`; `src/lib/i18n/locales/en-US/translation.json:2355-2356`; `backend/open_webui/config.py:969`; `backend/open_webui/retrieval/utils.py:581-586` |
| Relevance Threshold | "Only return documents with a score greater than or equal to this value." | `rag.relevance_threshold` (`RAG_RELEVANCE_THRESHOLD`) | 0.0; tooltip `The score should be a value between 0.0 (0%) and 1.0 (100%).` | Hybrid on | `src/lib/components/admin/Settings/Documents.svelte:1359-1373`; `src/lib/i18n/locales/en-US/translation.json:2320-2321`; `backend/open_webui/config.py:970` |
| BM25 Weight | "Balance semantic and lexical weighting for hybrid search." | `rag.hybrid_bm25_weight` (`RAG_HYBRID_BM25_WEIGHT`) | 0.5. A **Default**/**Custom** button reveals a slider from "semantic" to "lexical"; choosing **Default** sends no value, so it does not reset a stored weight | Hybrid on | `src/lib/components/admin/Settings/Documents.svelte:1375-1421`; `src/lib/i18n/locales/en-US/translation.json:2214-2215`; `backend/open_webui/config.py:971`; `backend/open_webui/routers/retrieval.py:1031-1033` |
| RAG Template | "Prompt template used when retrieved context is injected." | `rag.template` (`RAG_TEMPLATE`) | the built-in template (5.10); placeholder `Leave empty to use the default prompt, or enter a custom prompt` | Always | `src/lib/components/admin/Settings/Documents.svelte:1426-1451`; `src/lib/i18n/locales/en-US/translation.json:2315-2316`; `backend/open_webui/config.py:1070-1096` |

### 7.4 Documents > Files

| Label | Description (English text) | Config key and seeding variable | Code default | Source |
|---|---|---|---|---|
| Allowed File Extensions | "Comma-separated upload extensions. Leave empty for all file types." | `rag.file.allowed_extensions` (`RAG_ALLOWED_FILE_EXTENSIONS`) | empty (all types); enforced only for uploads that are processed | `src/lib/components/admin/Settings/Documents.svelte:1455-1466`; `src/lib/i18n/locales/en-US/translation.json:2198-2199`; `backend/open_webui/config.py:998-1000`; `backend/open_webui/routers/files.py:354-361` |
| Max Upload Size | "Maximum file size in MB. Leave empty for unlimited." | `rag.file.max_size` (`RAG_FILE_MAX_SIZE`) | none | `src/lib/components/admin/Settings/Documents.svelte:1469-1481`; `src/lib/i18n/locales/en-US/translation.json:2281-2282`; `backend/open_webui/config.py:983`; `backend/open_webui/routers/files.py:394-400` |
| Max Upload Count | "Maximum number of files that can be used at once in chat." | `rag.file.max_count` (`RAG_FILE_MAX_COUNT`) | none | `src/lib/components/admin/Settings/Documents.svelte:1482-1494`; `src/lib/i18n/locales/en-US/translation.json:2279-2280`; `backend/open_webui/config.py:981` |
| Image Compression Width, Image Compression Height | "Width in pixels to compress images to. Leave empty for no compression." (and the same for height) | `file.image_compression_width`, `file.image_compression_height` | none | `src/lib/components/admin/Settings/Documents.svelte:1497-1524`; `src/lib/i18n/locales/en-US/translation.json:2273-2276`; `backend/open_webui/config.py:989-995` |

Clearing one of these number fields saves "no limit" rather than leaving the old value
(`src/lib/components/admin/Settings/Documents.svelte:264-271`;
`backend/open_webui/routers/retrieval.py:1279-1293`). How the limits act on uploads is in
`files-uploads-and-storage.md`.

### 7.5 Documents > Integration

| Label | Description (English text) | Config key and seeding variable | Code default | Source |
|---|---|---|---|---|
| Google Drive | "Allow Google Drive as a document source." | `google_drive.enable` (`ENABLE_GOOGLE_DRIVE_INTEGRATION`) | off | `src/lib/components/admin/Settings/Documents.svelte:1528-1537`; `src/lib/i18n/locales/en-US/translation.json:2266-2267`; `backend/open_webui/config.py:843` |
| OneDrive | "Allow OneDrive as a document source." | `onedrive.enable` (`ENABLE_ONEDRIVE_INTEGRATION`) | off | `src/lib/components/admin/Settings/Documents.svelte:1538-1544`; `src/lib/i18n/locales/en-US/translation.json:2295-2296`; `backend/open_webui/config.py:849` |

The pickers' client registrations are environment values described in `files-uploads-and-storage.md`.

### 7.6 Documents > Danger Zone

Three action rows, **Reset Upload Directory**, **Reset Vector Storage/Knowledge** and **Reindex
Knowledge and Memory Vectors** (`src/lib/i18n/locales/en-US/translation.json:2317-2319`, `:2328-2333`;
`src/lib/components/admin/Settings/Documents.svelte:1547-1592`). They change data immediately and are
not saved settings; what each removes is in section 5.16.

### 7.7 External Knowledge Sources (Admin Settings > Integrations > Knowledge)

| Field | Stored where | Notes | Source |
|---|---|---|---|
| Connection: name, provider (`qdrant`, `milvus` or `pgvector`), endpoint, authentication, timeout, Milvus database, enabled flag | The `external_knowledge.connections` setting | Authentication values are not sent back to the browser; the list only says whether one is configured. Only `timeout` (and `db_name` for Milvus) are kept as extra options | `backend/open_webui/routers/knowledge.py:563-583`, `:618-621`, `:637-655` |
| Source: collection name and field names (content, vector, metadata, document id; table and collection field for pgvector) | The external knowledge base's `meta.external.source` | Content field required for every provider; vector field required for Milvus and pgvector | `backend/open_webui/routers/knowledge.py:591-617` |
| Access | The knowledge base's access grants (read only) | Public sharing is filtered by the sharing permission | `backend/open_webui/routers/knowledge.py:967-973`; `src/lib/components/admin/Settings/ExternalKnowledge.svelte:770-776` |

Provider field defaults filled by the form: Qdrant `payload.text` and `payload.metadata`; Milvus
`data.text`, `vector`, `metadata`; pgvector `document_chunk`, `collection_name`, `text`, `vector`,
`vmetadata` (`src/lib/components/admin/Settings/ExternalKnowledge.svelte:90-119`). The pgvector defaults
match the layout of this application's own pgvector store
(`backend/open_webui/retrieval/vector/dbs/pgvector.py:72-83`).

### 7.8 Personal and Per-Item Settings

| Setting | Where | Effect | Source |
|---|---|---|---|
| **Default Upload Mode** | Settings > Interface | New attachments start as **Using Entire Document** (`full`) or **Using Focused Retrieval** (`focused`, the default) | `src/lib/components/common/InterfaceSettings.svelte:1905-1927`; `src/lib/components/chat/MessageInput.svelte:945`; `src/lib/i18n/locales/en-US/translation.json:2899-2900` |
| Per-item switch | File preview window | Overrides the default for that attachment | `src/lib/components/common/FileItemModal.svelte:343-370` |
| Model capabilities **file context**, **citations**, **builtin tools** | Workspace > Models (model editor) | Whether attachments are searched into the prompt, whether sources are shown, whether built-in tools (and so native knowledge access) are offered; each is on unless switched off | `backend/open_webui/utils/middleware.py:3206-3213`, `:2809-2813`; `src/lib/components/chat/Messages/ResponseMessage.svelte:934`; see `workspace-models-and-model-access.md` |

### 7.9 Environment-Only Settings

These are read at startup and cannot be changed in the interface; production values are **TO BE
CONFIRMED**.

| Variable | Code default | Effect | Source |
|---|---|---|---|
| `VECTOR_DB` and the backend variables | `chroma` | Which vector store is used (6.4) | `backend/open_webui/config.py:503-835` |
| `OFFLINE_MODE` | off | No model downloads; also turns off update checks | `backend/open_webui/env.py:1201-1205` |
| `RAG_EMBEDDING_MODEL_AUTO_UPDATE`, `RAG_RERANKING_MODEL_AUTO_UPDATE` | on (forced off in offline mode) | Whether models may be downloaded or refreshed when loaded | `backend/open_webui/config.py:1013-1015`, `:1040-1042` |
| `RAG_EMBEDDING_MODEL_TRUST_REMOTE_CODE`, `RAG_RERANKING_MODEL_TRUST_REMOTE_CODE` | see source | Whether a model repository's own code may run when loading. Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca) | `backend/open_webui/config.py:1017`, `:1044` |
| `SENTENCE_TRANSFORMERS_HOME`, `HF_HOME` | `/app/backend/data/cache/embedding/models` in the Docker image | Where local models are cached | `Dockerfile:105`, `:112`; `backend/open_webui/retrieval/utils.py:1725` |
| `SENTENCE_TRANSFORMERS_BACKEND`, `SENTENCE_TRANSFORMERS_MODEL_KWARGS`, `SENTENCE_TRANSFORMERS_CROSS_ENCODER_BACKEND`, `SENTENCE_TRANSFORMERS_CROSS_ENCODER_MODEL_KWARGS` | `torch`, none, `torch`, none | How local models run | `backend/open_webui/env.py:1124-1153` |
| `SENTENCE_TRANSFORMERS_CROSS_ENCODER_SIGMOID_ACTIVATION_FUNCTION` | on | Squashes cross-encoder scores to 0-1 so the threshold behaves | `backend/open_webui/env.py:1153-1158` |
| `RAG_EMBEDDING_TIMEOUT` | unset (no limit) | Longest wait for one file's embeddings | `backend/open_webui/env.py:736-743` |
| `RAG_EMBEDDING_QUERY_PREFIX`, `RAG_EMBEDDING_CONTENT_PREFIX`, `RAG_EMBEDDING_PREFIX_FIELD_NAME` | unset | Prefixes some embedding models need | `backend/open_webui/config.py:1027-1031` |
| `RAG_SYSTEM_CONTEXT` | off | Put retrieved context in the system prompt instead of the user message | `backend/open_webui/env.py:372` |
| `RAG_SOURCE_METADATA_KEYS` | empty | Metadata keys copied into the `<source>` tags | `backend/open_webui/env.py:374-375` |
| `RAG_METADATA_MAX_VALUE_CHARS` | the environment `RAG_FILE_MAX_SIZE` in bytes, or none | Drops oversized metadata values | `backend/open_webui/env.py:841-848` |
| `MINERU_MAX_MARKDOWN_BYTES` | none | Largest MinerU cloud result accepted | `backend/open_webui/env.py:850-852` |
| `ENABLE_RAG_CSV_SUMMARY` | off | Adds a summary row to CSV extraction | `backend/open_webui/retrieval/loaders/main.py:182-185` |
| `ENABLE_FORWARD_USER_INFO_HEADERS` | off | Sends the user's identity to embedding, reranking and Mistral OCR services (the External document loader sends it regardless, 5.2) | `backend/open_webui/env.py:989` |
| `BYPASS_RETRIEVAL_ACCESS_CONTROL`, `ENABLE_RETRIEVAL_UNSCOPED_COLLECTIONS` | off, off | Access switches (3.4) | `backend/open_webui/env.py:833`, `:839` |
| `REQUESTS_VERIFY` | on | Certificate checking for Tika and the external reranker | `backend/open_webui/env.py:604`; `backend/open_webui/retrieval/loaders/main.py:240`; `backend/open_webui/retrieval/models/external.py:54` |
| `USE_SLIM_DOCKER` (set by the image) | off | The slim image's restrictions (5.17) | `backend/open_webui/env.py:45` |
| `USE_CUDA_DOCKER` (set by the image) | off | Runs local models on a GPU when available | `backend/open_webui/env.py:47-62` |

Two keys are persistent but have **no field on the panel**: `rag.tiktoken_encoding_name` (seeded from
`TIKTOKEN_ENCODING_NAME`, `cl100k_base`) and `rag.external_reranker_timeout` (seeded from
`RAG_EXTERNAL_RERANKER_TIMEOUT`). After the first boot, changing their environment variables has no
effect. The reranker timeout can still be changed through `/config/update`; the Tiktoken encoding is
not part of that form at all, so only a change to the stored setting alters it
(`backend/open_webui/config.py:1061`, `:1052`, `:2924`, `:2927`;
`backend/open_webui/routers/retrieval.py:873-959`, `:937`).

### 7.10 How Saving the Documents Panel Works

*Precision 2026-10-11:* if the reranking model fails to load during the save, the server stores `rag.enable_hybrid_search` as off and records only a log line, while the admin still sees the success pop-up (see sections 5.14 and 10, and `configuration-persistent-settings-r-to-w.md` section 8). The save also re-posts the `web` block it loaded (`src/lib/components/admin/Settings/Documents.svelte:264-265`).

1. **Save** first runs the panel's own checks for the chosen engine (10.3); a failed check stops the save
   (`src/lib/components/admin/Settings/Documents.svelte:164-237`).
2. Unless bypass mode is on, it then applies the embedding settings (`/embedding/update`). That step's
   own errors appear as pop-ups but **do not stop** the rest of the save
   (`src/lib/components/admin/Settings/Documents.svelte:239-241`, `:82-162`).
3. It checks the JSON fields, sends everything to `/config/update`, and shows
   `Settings saved successfully!` (`src/lib/components/admin/Settings/Documents.svelte:243-298`;
   `src/lib/components/chat/SettingsModal.svelte:460-464`).
4. If `/config/update` itself fails (for example a slim-image refusal), the panel code has no error
   handler for it, so the admin sees no pop-up at all (inferred from
   `src/lib/components/admin/Settings/Documents.svelte:264-298`; section 14).
5. A changed reranking model is loaded during step 3 (5.14); a changed embedding model during step 2
   (5.13). Neither reindexes anything.

## 8. Cron Jobs and Background Processes

There is no scheduled job in this area and nothing here uses Redis. What runs without a click:

| What | When | How long it can take | Source |
|---|---|---|---|
| Processing an upload (extract, chunk, embed, store) | As a background task straight after the upload, by default | Unbounded in code; the browser's status stream checks once a second for up to two hours | `backend/open_webui/routers/files.py:436-446`, `:645-668`; `backend/open_webui/routers/retrieval.py:2089-2115` |
| Parsing and embedding work | In worker threads, so the server stays responsive | Embedding waits up to `RAG_EMBEDDING_TIMEOUT` (no limit by default) | `backend/open_webui/retrieval/loaders/main.py:349-366`; `backend/open_webui/routers/retrieval.py:1877-1889`, `:2096-2115` |
| Polling Datalab Marker or MinerU cloud for a result | Inside the processing task | Up to about 10 minutes each | `backend/open_webui/retrieval/loaders/datalab_marker.py:127-169`; `backend/open_webui/retrieval/loaders/mineru.py:325-417` |
| Loading the local embedding model and the reranker | At startup, and whenever an admin saves the relevant settings | Seconds to minutes depending on download and hardware | `backend/open_webui/main.py:368`, `:672-697`; `backend/open_webui/routers/retrieval.py:564-597`, `:1235-1250` |
| Reindexing (Danger Zone) | **Not** in the background: inside the admin's request, one file at a time | Proportional to the number of knowledge-base files; progress only in the log | `backend/open_webui/routers/knowledge.py:374-462` |
| Automatic memory re-embedding | When a memory write hits a size mismatch | One user's memories | `backend/open_webui/routers/memories.py:171-180` |

Settings changes take effect at save time for the next message (5.7); model changes take effect in the
process that handled the save (6.5). Background processing in general is in
`background-processes-and-scheduling.md`.

## 9. Notifications and Emails

**No email is sent** by this area or anywhere in the application (see `tools/ground-truth.md`, Contacts).

### 9.1 Status Events Shown in the Chat

| Event action | Text the user sees | When | Source |
|---|---|---|---|
| `queries_generated` | `Querying`, with each search phrase as a chip | Before searching, unless every item is in full-context mode | `backend/open_webui/utils/middleware.py:2090-2100`; `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:78-103` |
| `sources_retrieved` | `No sources found`, `Retrieved 1 source` or `Retrieved {count} sources` | After retrieval | `backend/open_webui/utils/middleware.py:2157-2165`; `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:104-124` |
| `knowledge_search` | `Searching Knowledge for "{searchQuery}"` | Custom-model knowledge in legacy function calling | `backend/open_webui/utils/middleware.py:2609-2618`, `:3249-3259`; `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:40-51` |

The fork's **Hide Processing Details** setting hides these lines (section 12).

### 9.2 Platform Events

Events are published for webhooks and event functions (`notifications-webhooks-events-and-banners.md`):

| Event | Message | Published when | Source |
|---|---|---|---|
| `retrieval.content.processed` | Retrieval Content processed | A file, text or batch was processed | `backend/open_webui/events.py:409-413`; `backend/open_webui/routers/retrieval.py:2074-2081`, `:2136-2143`, `:2225-2232`, `:3448-3458` |
| `retrieval.content.process_failed` | Retrieval Content process failed | Processing failed; the event data carries the file name and the error | `backend/open_webui/events.py:414-418`; `backend/open_webui/routers/retrieval.py:2167-2178` |
| `retrieval.collection.deleted` | Retrieval Collection deleted | `/delete` removed a file's chunks | `backend/open_webui/events.py:419-423`; `backend/open_webui/routers/retrieval.py:3252-3258` |
| `retrieval.vector_db.reset` | Retrieval Vector Db reset | **Reset Vector Storage/Knowledge** | `backend/open_webui/events.py:424-428`; `backend/open_webui/routers/retrieval.py:3279-3284` |
| `retrieval.uploads.reset` | Retrieval Uploads reset | `/reset/uploads` | `backend/open_webui/events.py:429-431`; `backend/open_webui/routers/retrieval.py:3310-3316` |
| `file.deleted_all` | File deleted all | **Reset Upload Directory** | `backend/open_webui/events.py:299-301`; `backend/open_webui/routers/files.py:591` |
| `knowledge.reindexed` | Knowledge reindexed | Knowledge reindex finished | `backend/open_webui/events.py:359-361`; `backend/open_webui/routers/knowledge.py:454-460` |
| `memory.reset` | Memory reset | Memory reindex finished | `backend/open_webui/events.py:344-346`; `backend/open_webui/routers/memories.py:472-479` |
| `knowledge.external_connection.created`, `.updated`, `.deleted` | Knowledge External Connection created (updated, deleted) | External connection changes | `backend/open_webui/events.py:394-408`; `backend/open_webui/routers/knowledge.py:707-713`, `:744-750`, `:775-781` |

`retrieval.content.process_failed` is one of the five events a user can route to their own
notification targets (Settings > Notifications), labelled "Retrieval Content process failed"
(`backend/open_webui/events.py:669-675`; `backend/open_webui/utils/notifications.py:222-230`). File
names in these events can themselves be personal or health information; webhook destinations are
**TO BE CONFIRMED**.

## 10. Error, Warning and Notice Messages (Verbatim)

How these texts reach people:

- **Upload processing errors** are stored on the file and shown in the chat composer as a **yellow
  warning pop-up** after the upload, while the file stays attached
  (`backend/open_webui/routers/files.py:260-268`; `src/lib/components/chat/MessageInput.svelte:1025-1028`).
  Knowledge-base screens show them in their own way (`knowledge-bases.md`).
- When an extraction engine raised an HTTP-style error, the stored text is that error converted to
  text, which starts with its status code, for example `400: MinerU returned empty results`
  (`backend/open_webui/routers/retrieval.py:2155-2189`; the conversion is the web framework's, see
  section 14).
- Messages built with `ERROR_MESSAGES.DEFAULT(...)` appear as `[ERROR: {text}]`; with no text they read
  `Something went wrong :/` (`backend/open_webui/constants.py:16-24`, `:41`).
- **Admin panel errors** appear as red pop-ups printing the server's message
  (`src/lib/components/admin/Settings/Documents.svelte:152-156`, `:357-410`).
- Placeholders are written `{name}` using the source's variable name. Plain i18n keys display their own
  text (their `en-US` values are empty, for example `src/lib/i18n/locales/en-US/translation.json:36`,
  `:1521`); dotted keys are resolved in section 7.

### 10.1 Processing, Search and Settings Messages From the Server

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `The content provided is empty. Please ensure that there is text or data present before proceeding.` | Warning pop-up after upload; the file is marked failed | `backend/open_webui/constants.py:95`; `backend/open_webui/routers/retrieval.py:1819-1820`, `:2014-2015` | Extraction produced no text (for example a scanned PDF with no text layer and OCR off), or a file with no stored text was added to a knowledge base | Try a text-based copy of the document, or ask whether OCR extraction is available | Admin: extraction engine and **PDF Extract Images (OCR)**; file status `failed` |
| `Duplicate content detected. Please provide unique content to proceed.` | Error | `backend/open_webui/constants.py:109`; `backend/open_webui/routers/retrieval.py:1734-1753` | The same extracted text is already in that collection from a different file | Keep the existing copy or remove it first | Knowledge base's file list |
| `Pandoc is not installed on the server. Please contact your administrator for assistance.` | Error | `backend/open_webui/constants.py:85`; `backend/open_webui/routers/retrieval.py:2180-2184` | A loader reported that the pandoc program is missing | Escalate | Server build (the standard image installs pandoc, `Dockerfile:145-147`) |
| `We could not find what you're looking for :/` | Error (HTTP 404) | `backend/open_webui/constants.py:78`; `backend/open_webui/routers/retrieval.py:2191-2192`, `:3221-3225` | The file does not exist or does not belong to the requester | Upload again | Does the file still exist |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 403) | `backend/open_webui/constants.py:70-72`; `backend/open_webui/routers/retrieval.py:3050-3063` | Writing to or searching a collection the user cannot access | Ask the knowledge base's owner to share it | Access grants (3.2) |
| `401 Unauthorized` | Error (HTTP 401) | `backend/open_webui/constants.py:69`; `backend/open_webui/routers/knowledge.py:378-382` | A non-admin called the knowledge reindex | None | Expected |
| `[ERROR: Invalid text splitter]` | Error | `backend/open_webui/routers/retrieval.py:1816-1817` | The stored **Text Splitter** value is not one the code knows | Escalate | `rag.text_splitter` |
| `Tokenizer model required for Token (Transformers) text splitter` | Error | `backend/open_webui/routers/retrieval.py:1675-1679` | Token (Transformers) splitter, no **Tokenizer Model**, and no local embedding model to borrow one from | Escalate | Documents > Tokenizer Model |
| `Transformers tokenization is unavailable in slim. Use character or token splitting.` | Error | `backend/open_webui/routers/retrieval.py:984-987`, `:1650-1651` | Slim image with the Transformers splitter | Escalate | Image type |
| `No embedding model is loaded. Set RAG_EMBEDDING_MODEL to a valid SentenceTransformer model name, or configure an external RAG_EMBEDDING_ENGINE (ollama, openai, azure_openai).` | Error on every upload and document question | `backend/open_webui/retrieval/utils.py:1131-1137` | The local embedding model failed to load (wrong name, no download allowed, offline mode without a cached copy) | Escalate | Log line `Error loading SentenceTransformer: {e}` at startup or after a save |
| `Configure an external embedding engine (openai, ollama, azure_openai).` | Error (HTTP 503) | `backend/open_webui/retrieval/utils.py:1129-1130` | Slim image with the local engine | Escalate | Embedding engine |
| `Ollama embed error ({r.status}): {error_detail}` | Error | `backend/open_webui/retrieval/utils.py:1104-1107` | The Ollama embedding call was refused (for example the model is not pulled) | Escalate | Ollama URL and model |
| `Unexpected OpenAI embeddings response: missing 'data' key` | Error | `backend/open_webui/retrieval/utils.py:957-960` | The OpenAI-compatible service answered without embeddings | Escalate | Embedding URL and model |
| `Unexpected Azure OpenAI embeddings response: missing 'data' key` | Error | `backend/open_webui/retrieval/utils.py:1039-1042` | The Azure service answered without embeddings | Escalate | Deployment name, API version |
| `Unexpected Ollama embeddings response: missing 'embeddings' key` | Error | `backend/open_webui/retrieval/utils.py:1109-1112` | Ollama answered without embeddings | Escalate | Ollama version and model |
| `Embedding generation failed for batch {i + 1}/{len(batches)}` | Error | `backend/open_webui/retrieval/utils.py:1188-1193` | A batch returned nothing | Escalate | Provider logs |
| `Unknown embedding engine: {embedding_engine}` | Error | `backend/open_webui/retrieval/utils.py:1205-1206` | The stored engine value is not empty, `ollama`, `openai` or `azure_openai` | Escalate | `rag.embedding_engine` |
| `[ERROR: Error updating embedding configuration]` | Admin pop-up | `backend/open_webui/routers/retrieval.py:621-626` | Saving or loading the new embedding settings failed | Escalate | Log line `Problem updating embedding model: {e}` |
| `[ERROR: Error updating reranking configuration]` | Admin pop-up (rare) | `backend/open_webui/routers/retrieval.py:1254-1259` | An unexpected failure while storing the reranking model; load failures are handled separately (5.14) | Escalate | Log line `Problem updating reranking model: {e}` |
| `Slim requires an external embedding engine (openai, ollama, azure_openai).` | Admin pop-up (HTTP 400) | `backend/open_webui/routers/retrieval.py:539-540` | Slim image, local engine chosen | Choose an external engine | Image type |
| `Slim requires an external reranker, or an empty reranking model for cosine scoring.` | Admin save refused (HTTP 400) | `backend/open_webui/routers/retrieval.py:996-1003` | Slim image, local reranker chosen | Use External or clear the model | Image type |
| `Configure an external reranker, or clear the reranking model to use cosine scoring.` | Error (HTTP 503) during hybrid search | `backend/open_webui/retrieval/utils.py:1264-1271` | Slim image with a local reranking model stored | Escalate | Reranking settings |
| `DDGS is unavailable in slim. Configure another web search provider in Admin Settings > Web Search.` | Admin save refused (HTTP 400) | `backend/open_webui/routers/retrieval.py:966-975` | Web search settings in the slim image (see `web-search-and-web-loading.md`) | | |
| `Playwright is unavailable in slim. Use basic HTTP fetching or an external web loader.` | Admin save refused (HTTP 400) | `backend/open_webui/routers/retrieval.py:976-983` | Web loader settings in the slim image | | |
| `[ERROR: Error querying knowledge base]` | Error | `backend/open_webui/routers/retrieval.py:3121-3128`, `:3189-3196` | The search endpoints failed | Retry; escalate if repeated | Log around the time |
| `[ERROR: File has no hash; cannot delete vector entries by hash.]` | Admin error (HTTP 400) | `backend/open_webui/routers/retrieval.py:3228-3239` | `/delete` for a file that never processed successfully | None | File status |
| `Error saving document to vector database` | Error | `backend/open_webui/routers/retrieval.py:2150-2151` | The store reported no success | Escalate | Vector store health |
| `Something went wrong :/` | Error (HTTP 500) | `backend/open_webui/routers/retrieval.py:2238-2242`; `backend/open_webui/constants.py:16-18` | `/process/text` could not save | Retry | Log |
| `File not found`, `Permission denied: not file owner` | Per-file result of a batch | `backend/open_webui/routers/retrieval.py:3374-3393` | Batch processing of a missing or foreign file | None | |
| `File type {content_type} is not supported for processing` | Warning (file failed) | `backend/open_webui/routers/files.py:168-188` | An image uploaded with processing while its type is not listed for extraction | Upload text documents to knowledge bases; attach images in chat instead | **Supported Media MIME Types** |
| `Document archive is too large after decompression` | Warning (file failed) | `backend/open_webui/retrieval/loaders/main.py:520-539` | An Office or e-book file that expands beyond the limits in 5.2 | Split or simplify the document | **Max Upload Size** |
| `This file type requires an external document extractor in slim. Configure one that supports it.` | Error (HTTP 503) | `backend/open_webui/retrieval/loaders/main.py:700-712` | Slim image, Default engine, a file type that needs a parser | Escalate | Extraction engine |
| `Slim requires PostgreSQL/pgvector for vector storage. Set VECTOR_DB=pgvector and PGVECTOR_DB_URL, or use the standard image.` | Error (HTTP 503) | `backend/open_webui/retrieval/vector/factory.py:20-24` | Slim image with another vector store | Escalate | `VECTOR_DB` |
| `Configure PGVECTOR_DB_URL for remote vector storage.` | Error (HTTP 503) | `backend/open_webui/retrieval/vector/factory.py:113-114` | Slim image without a PostgreSQL address | Escalate | `PGVECTOR_DB_URL` |
| `Unable to connect to configured vector database ({VECTOR_DB}): {exc}` | Error (HTTP 503) | `backend/open_webui/retrieval/vector/factory.py:115-122` | Slim image, store unreachable on first use | Escalate | Store health |
| `Configure CHROMA_HTTP_HOST: embedded Chroma is unavailable in slim.` | Error (HTTP 503) | `backend/open_webui/retrieval/vector/dbs/chroma.py:34-35` | Slim image with Chroma and no Chroma server. *Corrected 2026-10-10: in practice never shown; in the slim image the vector factory refuses every store except pgvector first, with `Slim requires PostgreSQL/pgvector for vector storage. Set VECTOR_DB=pgvector and PGVECTOR_DB_URL, or use the standard image.` (`backend/open_webui/retrieval/vector/factory.py:20-24`).* | Escalate | `VECTOR_DB` |

### 10.2 Extraction Engine Messages

These become the file's error (10, introduction). Engine names are the panel labels.

| Message | Engine | Source | Trigger |
|---|---|---|---|
| `Error connecting to endpoint: {e}` | External | `backend/open_webui/retrieval/loaders/external_document.py:63-67` | The loader service could not be reached |
| `Error loading document: {response.status_code} {response.text}` | External | `backend/open_webui/retrieval/loaders/external_document.py:94-95` | The loader service returned an error status |
| `Error loading document: No content returned` | External | `backend/open_webui/retrieval/loaders/external_document.py:92-93` | Empty answer |
| `Error loading document: Unable to parse content` | External | `backend/open_webui/retrieval/loaders/external_document.py:89-90` | Answer was neither an object nor a list |
| `Error calling Tika: {r.reason}` | Tika | `backend/open_webui/retrieval/loaders/main.py:252-253` | Tika returned an error status |
| `Error calling Docling: conversion status {conversion_status} - {error_details}` | Docling | `backend/open_webui/retrieval/loaders/main.py:294-301` | Docling reported `failure` or `skipped` |
| `Error calling Docling API: {r.reason}`, shown after the prefix "Error calling Docling: " and followed by Docling's detail when it gives one | Docling | `backend/open_webui/retrieval/loaders/main.py:320-329` | Docling returned an error status |
| `File not found: {self.file_path}` | Datalab Marker, MinerU | `backend/open_webui/retrieval/loaders/datalab_marker.py:105-106`; `backend/open_webui/retrieval/loaders/mineru.py:111-112`, `:305-306` | The stored file was missing when processing began |
| `Datalab Marker request failed: {e}` | Datalab Marker | `backend/open_webui/retrieval/loaders/datalab_marker.py:107-111` | The Marker service returned an error status |
| `Invalid JSON response: {e}` | Datalab Marker, MinerU cloud | `backend/open_webui/retrieval/loaders/datalab_marker.py:112-113`; `backend/open_webui/retrieval/loaders/mineru.py:262-267` | Unreadable answer |
| `Datalab Marker request failed: {error}` (Marker's own error text, or `Unknown error`) | Datalab Marker | `backend/open_webui/retrieval/loaders/datalab_marker.py:117-121` | Marker answered without success |
| `Polling failed: {e}` | Datalab Marker | `backend/open_webui/retrieval/loaders/datalab_marker.py:135-138` | A status check failed |
| `Marker processing failed: {error_msg}` | Datalab Marker | `backend/open_webui/retrieval/loaders/datalab_marker.py:158-164` | Marker reported failure (`Marker returned failure without error message` when it gave no reason) |
| `Marker processing timed out` | Datalab Marker | `backend/open_webui/retrieval/loaders/datalab_marker.py:165-169` | No result after 300 status checks two seconds apart |
| `Final processing failed: {error_msg}` | Datalab Marker | `backend/open_webui/retrieval/loaders/datalab_marker.py:171-176` | Completed without success (`Unknown processing error` when no reason) |
| `Custom Marker endpoint returned success but no 'output' field found. Available fields: {available_fields}. Expected either 'request_check_url' for polling or 'output' field for direct response.` | Datalab Marker (self-hosted) | `backend/open_webui/retrieval/loaders/datalab_marker.py:188-193` | A self-hosted Marker answered in an unexpected shape |
| `Unsupported output format: {self.output_format}` | Datalab Marker | `backend/open_webui/retrieval/loaders/datalab_marker.py:199-203` | Output format not Markdown, JSON or HTML |
| `Marker returned empty content` | Datalab Marker | `backend/open_webui/retrieval/loaders/datalab_marker.py:205-209` | Marker found no text |
| `Provide exactly one of api_key or azure_credential.` | Document Intelligence | `backend/open_webui/retrieval/loaders/local.py:101-102` | The key setting is absent altogether rather than empty (inferred from `backend/open_webui/retrieval/loaders/main.py:646-659`) |
| `MinerU Local API request timed out` | MinerU (local) | `backend/open_webui/retrieval/loaders/mineru.py:113-117` | No answer within **API Timeout** |
| `MinerU Local API request failed: {e}` (followed by MinerU's detail) | MinerU (local) | `backend/open_webui/retrieval/loaders/mineru.py:118-126` | MinerU returned an error status |
| `Error calling MinerU Local API: {str(e)}` | MinerU (local) | `backend/open_webui/retrieval/loaders/mineru.py:127-131` | Connection or other failure |
| `Invalid JSON response from MinerU Local API: {e}` | MinerU (local) | `backend/open_webui/retrieval/loaders/mineru.py:134-140` | Unreadable answer |
| `MinerU Local API response missing 'results' field` | MinerU (local) | `backend/open_webui/retrieval/loaders/mineru.py:143-147` | Unexpected answer |
| `MinerU returned empty results` | MinerU (local) | `backend/open_webui/retrieval/loaders/mineru.py:150-154` | Nothing parsed |
| `MinerU returned empty markdown content` | MinerU (local) | `backend/open_webui/retrieval/loaders/mineru.py:160-164` | No text |
| `Invalid API mode: {self.api_mode}. Must be 'local' or 'cloud'` | MinerU | `backend/open_webui/retrieval/loaders/mineru.py:51-52` | Bad stored mode |
| `API key is required for Cloud API mode` | MinerU (cloud) | `backend/open_webui/retrieval/loaders/mineru.py:55-56` | Cloud mode without a key |
| `Failed to request upload URL: {e}` (with MinerU's message), `Error requesting upload URL: {str(e)}` | MinerU (cloud) | `backend/open_webui/retrieval/loaders/mineru.py:246-259` | The upload request failed |
| `MinerU Cloud API error: {msg}` (MinerU's message or `Unknown error`) | MinerU (cloud) | `backend/open_webui/retrieval/loaders/mineru.py:270-274`, `:371-375` | MinerU reported an error code |
| `MinerU Cloud API response missing batch_id or file_urls` | MinerU (cloud) | `backend/open_webui/retrieval/loaders/mineru.py:280-284` | Unexpected answer |
| `File upload to presigned URL timed out`, `Failed to upload file to presigned URL: {e}`, `Error uploading file: {str(e)}` | MinerU (cloud) | `backend/open_webui/retrieval/loaders/mineru.py:307-321` | Uploading the file failed |
| `Failed to poll batch status: {e}`, `Error polling batch status: {str(e)}`, `Invalid JSON response while polling: {e}` | MinerU (cloud) | `backend/open_webui/retrieval/loaders/mineru.py:347-368` | A status check failed |
| `File {filename} not found in batch results` | MinerU (cloud) | `backend/open_webui/retrieval/loaders/mineru.py:387-391` | Result list did not include the file |
| `MinerU processing failed: {error_msg}` | MinerU (cloud) | `backend/open_webui/retrieval/loaders/mineru.py:398-403` | MinerU reported failure |
| `MinerU processing timed out after 10 minutes` | MinerU (cloud) | `backend/open_webui/retrieval/loaders/mineru.py:413-417` | 300 status checks without a result |
| `Failed to download results ZIP: {e}`, `Error downloading results: {str(e)}`, `Invalid ZIP file received: {e}`, `Error extracting ZIP: {str(e)}` | MinerU (cloud) | `backend/open_webui/retrieval/loaders/mineru.py:426-438`, `:491-502` | Fetching or opening the result failed |
| `Markdown file in results ZIP is too large: {member.filename}` | MinerU (cloud) | `backend/open_webui/retrieval/loaders/mineru.py:458-466` | Over `MINERU_MAX_MARKDOWN_BYTES` |
| `Found .md files but couldn't read them: {read_errors}`, `No .md files found in ZIP. Available files: {all_files}` | MinerU (cloud) | `backend/open_webui/retrieval/loaders/mineru.py:481-490` | Result had no usable Markdown |
| `Extracted markdown content is empty` | MinerU (cloud) | `backend/open_webui/retrieval/loaders/mineru.py:512-516` | Empty result |
| `Processing .doc files requires the 'unstructured' package. Install it with: pip install unstructured` (also `.epub`, `.msg`, `.odt`) | Default | `backend/open_webui/retrieval/loaders/main.py:749-812` | The server lacks the optional parser |
| `Unsupported email file type: {detected}` | Default | `backend/open_webui/retrieval/loaders/local.py:72-78` | A `.msg` file that is neither Outlook nor plain e-mail |
| `Error loading {self.file_path}` | Default | `backend/open_webui/retrieval/loaders/local.py:13-17`; `backend/open_webui/retrieval/loaders/main.py:180-181` | A text or CSV file could not be read; the message shows the server's storage path |
| `PDF mode must be 'single' or 'page'` | Default | `backend/open_webui/retrieval/loaders/pdf.py:14-15` | Bad stored **PDF Loader Mode** |
| `PaddleOCR-vl API URL and Token are required.` | PaddleOCR-vl | `backend/open_webui/retrieval/loaders/paddleocr_vl.py:27-28` | Missing settings |
| `File not found at {file_path}` | Mistral OCR, PaddleOCR-vl | `backend/open_webui/retrieval/loaders/mistral.py:54-55`; `backend/open_webui/retrieval/loaders/paddleocr_vl.py:29-30` | The stored file was missing |

### 10.3 Admin Documents Panel Messages

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Model filesystem path detected. Model shortname is required for update, cannot continue.` | Error pop-up | `src/lib/components/admin/Settings/Documents.svelte:83-107` | Default engine with a model value containing more than one "/", **and also** Ollama or OpenAI with an empty model field (the wording is misleading there) | Enter a model name | Embedding Model field |
| `OpenAI URL/Key required.` | Error pop-up | `src/lib/components/admin/Settings/Documents.svelte:109-115` | Azure OpenAI chosen with the key, URL or version empty | Fill all three | |
| `External Document Loader URL required.` | Error pop-up; save stopped | `src/lib/components/admin/Settings/Documents.svelte:165-171` | External engine without a URL | | |
| `Headers must be a valid JSON object` | Error pop-up; save stopped | `src/lib/components/admin/Settings/Documents.svelte:172-186` | External loader headers are not a JSON object | | |
| `Tika Server URL required.` | Error pop-up; save stopped | `src/lib/components/admin/Settings/Documents.svelte:187-190` | Tika without a URL | | |
| `Docling Server URL required.` | Error pop-up; save stopped | `src/lib/components/admin/Settings/Documents.svelte:191-194` | Docling without a URL | | |
| `Invalid JSON format in Additional Config` | Error pop-up; save stopped | `src/lib/components/admin/Settings/Documents.svelte:195-206` | Marker's Additional Config is not JSON | | |
| `Document Intelligence endpoint required.` | Error pop-up; save stopped | `src/lib/components/admin/Settings/Documents.svelte:208-214` | | | |
| `Mistral OCR API Key required.` | Error pop-up; save stopped | `src/lib/components/admin/Settings/Documents.svelte:215-221` | | | |
| `PaddleOCR-vl API URL required.` | Error pop-up; save stopped | `src/lib/components/admin/Settings/Documents.svelte:222-228` | | | |
| `MinerU API Key required for Cloud API mode.` | Error pop-up; save stopped | `src/lib/components/admin/Settings/Documents.svelte:230-237` | | | |
| `Invalid JSON format in {NAME}`, shown as "Invalid JSON format in Docling Parameters" | Error pop-up; save stopped | `src/lib/components/admin/Settings/Documents.svelte:243-254` | Docling Parameters are not JSON | | |
| `Invalid JSON format in MinerU Parameters` | Error pop-up; save stopped | `src/lib/components/admin/Settings/Documents.svelte:255-262` | | | |
| `Settings saved successfully!` | Success pop-up | `src/lib/components/chat/SettingsModal.svelte:460-464`; `src/lib/components/admin/Settings/Documents.svelte:298` | Save finished (appears even when the embedding step showed an error, 7.10) | Reopen the panel to confirm values | |
| `Success` | Success pop-up | `src/lib/components/admin/Settings/Documents.svelte:362-364`, `:376-378`, `:412-414` | A Danger Zone action returned (for the vector reset, as soon as it was sent) | | Server log for the real outcome |
| `Reindex Embedding Data` / `Rebuild knowledge file, knowledge search, and memory vectors using the current embedding model.` | Confirmation | `src/lib/components/admin/Settings/Documents.svelte:382-388` | Reindex pressed | | |
| `Confirm your action` / `This action cannot be undone. Do you wish to continue?` | Confirmation | `src/lib/components/common/ConfirmDialog.svelte:143`, `:153` | Either reset pressed | | |
| `Slim requires external services for embeddings, vector storage, and document extraction. Basic text files can be read locally.` | Notice | `src/lib/components/admin/Settings/Documents.svelte:427-433` | Server runs the slim image | | |
| `After changing the embedding model, reindex knowledge, knowledge search, and memory vectors for changes to take effect.` | Notice | `src/lib/components/admin/Settings/Documents.svelte:1167-1171` | Always under the model field | | |
| `This template contains multiple context placeholders ([context] or {{CONTEXT}}). Context will be injected at each occurrence.` | Notice | `src/lib/components/admin/Settings/Documents.svelte:1444-1450` | Custom template with more than one placeholder | | |
| `The score should be a value between 0.0 (0%) and 1.0 (100%).` | Tooltip | `src/lib/components/admin/Settings/Documents.svelte:1371` | Hovering the threshold | | |
| `No additional headers are sent unless configured.` | Hint | `src/lib/components/admin/Settings/Documents.svelte:650-665` | **Header variables** opened | | |

Server errors during a panel action print the server's text in a red pop-up, for example the
embedding errors of 10.1 (`src/lib/components/admin/Settings/Documents.svelte:152-156`).

### 10.4 External Knowledge Messages

| Message | Severity | Source | Trigger |
|---|---|---|---|
| `External connection not found.` | Error pop-up or HTTP 404 | `src/lib/components/admin/Settings/ExternalKnowledge.svelte:145-150`; `backend/open_webui/routers/knowledge.py:862-864`, `:1025-1027` | The source's connection record is missing |
| `Fill the source fields and test query first.` | Error pop-up | `src/lib/components/admin/Settings/ExternalKnowledge.svelte:274-278` | **Verify Connection** with required fields empty |
| `Test succeeded.` / `Test returned no results.` | Success / error pop-up | `src/lib/components/admin/Settings/ExternalKnowledge.svelte:293-298` | Test query answered with or without passages |
| `Fill the required fields first.` | Error pop-up | `src/lib/components/admin/Settings/ExternalKnowledge.svelte:302-306`, `:339-342` | Create or Save with fields missing |
| `Test the source before creating it.` / `Test the source before saving it.` | Error pop-up | `src/lib/components/admin/Settings/ExternalKnowledge.svelte:308-311`, `:344-347` | No successful test yet |
| `Knowledge source created.` / `Knowledge source updated.` | Success pop-up | `src/lib/components/admin/Settings/ExternalKnowledge.svelte:327-332`, `:363-368` | Saved |
| `No external knowledge sources configured.` / `Test must pass before a source is created.` | Notice | `src/lib/components/admin/Settings/ExternalKnowledge.svelte:877-887` | Empty list |
| `External vectors must be generated with the same embedding model configured in Open WebUI.` | Notice | `src/lib/components/admin/Settings/ExternalKnowledge.svelte:757-764` | Always in the form |
| `This is an experimental feature, it may not function as expected and is subject to change at any time.` | Tooltip | `src/lib/components/common/ExperimentalBadge.svelte:12-15` | Hovering **Experimental** |
| `Unsupported external knowledge provider.` | HTTP 400 | `backend/open_webui/routers/knowledge.py:563-569` | Provider not Qdrant, Milvus or pgvector |
| `Knowledge source name is required.` / `Knowledge source endpoint is required.` | HTTP 400 | `backend/open_webui/routers/knowledge.py:571-575` | |
| `Only collection sources are supported.` / `Collection name is required.` | HTTP 400 | `backend/open_webui/routers/knowledge.py:595-598` | |
| `Content field is required.` / `Vector field is required.` | HTTP 400 | `backend/open_webui/routers/knowledge.py:613-616` | Vector field required for Milvus and pgvector |
| `External connection is still used by knowledge bases.` | HTTP 400 | `backend/open_webui/routers/knowledge.py:765-770` | Deleting a connection in use |
| `Test query is required.` | HTTP 400 | `backend/open_webui/routers/knowledge.py:816-817` | |
| `Knowledge name is required.` | HTTP 400 | `backend/open_webui/routers/knowledge.py:904-905`, `:951-952`, `:1020-1021` | |
| `Test query returned no results.` | HTTP 400 | `backend/open_webui/routers/knowledge.py:964-965`, `:1040-1041` | The server's own test at save time found nothing |
| `Uh-oh! This file is already registered. Please choose another file.` | HTTP 400 | `backend/open_webui/constants.py:52`; `backend/open_webui/routers/knowledge.py:925-926`, `:990-991` | The knowledge base record could not be created |
| `External knowledge connection is disabled` | Raised during retrieval | `backend/open_webui/retrieval/external.py:320-321` | The source's **Enabled** switch is off |
| `External knowledge connection is not configured` / `External knowledge connection not found` | Raised during retrieval | `backend/open_webui/retrieval/external.py:299-306` | Broken link between knowledge base and connection |
| `Unsupported external knowledge provider: {provider}` | Raised during retrieval | `backend/open_webui/retrieval/external.py:361-362` | Stored provider unknown |
| `qdrant-client is not installed` / `pymilvus is not installed` / `psycopg and pgvector are required for pgvector retrieval` | Raised during retrieval | `backend/open_webui/retrieval/external.py:90-93`, `:137-140`, `:208-214` | The server lacks the provider's library |
| `Embedding function is not configured` | Raised during retrieval | `backend/open_webui/retrieval/external.py:95-96`, `:142-143`, `:216-217` | No embedding function in this process |
| `External source collection is not configured` / `Milvus collection is not configured` / `pgvector collection is not configured` | Raised during retrieval | `backend/open_webui/retrieval/external.py:101-103`, `:148-150`, `:222-224` | Source without a collection name |
| `Invalid {label}` (for example "Invalid table name") | Raised during retrieval | `backend/open_webui/retrieval/external.py:83-86`, `:238-248` | A pgvector table or field name with unusual characters |

The "Raised during retrieval" errors are not turned into readable HTTP errors. In a chat they end as
`No sources found` (5.7); during **Verify Connection** the panel most likely shows no pop-up at all
(inferred from `src/lib/apis/knowledge/index.ts:223-250`; section 14).

### 10.5 Chat Status Lines, Sources and File Window Texts

| Message | Where | Source |
|---|---|---|
| `Querying` | Status line while search phrases are shown | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:78-103` |
| `No sources found` / `Retrieved 1 source` / `Retrieved {count} sources` | Status line after retrieval | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:104-124` |
| `Searching Knowledge for "{searchQuery}"` | Status line, legacy-mode model knowledge | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:40-51` |
| `1 Source` / `{COUNT} Sources` | Sources button | `src/lib/components/chat/Messages/Citations.svelte:209-217` |
| `Toggle 1 source` / `Toggle {COUNT} sources`, `View source: {name}` | Screen-reader labels | `src/lib/components/chat/Messages/Citations.svelte:176-178`, `:228-230` |
| `Open link` / `Open file`, `Citation`, `Content`, `Relevance`, `page`, `Parameters` | Citation window | `src/lib/components/chat/Messages/Citations/CitationModal.svelte:108-110`, `:130`, `:153`, `:172-178`, `:184`, `:210` |
| `Show all ({COUNT} characters)` | Citation window, long passage | `src/lib/components/chat/Messages/Citations/CitationModal.svelte:248-260` |
| `Using Entire Document` / `Using Focused Retrieval` | File window switch and Default Upload Mode | `src/lib/components/common/FileItemModal.svelte:358-363`; `src/lib/components/common/InterfaceSettings.svelte:1921-1923` |
| `Inject the entire content as context for comprehensive processing, this is recommended for complex queries.` | Tooltip, switch on | `src/lib/components/common/FileItemModal.svelte:349-353` |
| `Default to segmented retrieval for focused and relevant content extraction, this is recommended for most cases.` | Tooltip, switch off | `src/lib/components/common/FileItemModal.svelte:354-356` |
| `File size should not exceed {maxSize} MB.` / `You can only chat with a maximum of {maxCount} file(s) at a time.` | Composer, from **Max Upload Size** and **Max Upload Count** (see `files-uploads-and-storage.md`) | `src/lib/components/chat/MessageInput.svelte:1093-1099`, `:1117-1122` |

### 10.6 Text That Becomes Document Content Instead of an Error

Some engines do not fail a file they could not read; they return a short text as if it were the
document. The file then shows as processed, the text is embedded, and the model may quote it.

| Text stored as the document | Engine | Source |
|---|---|---|
| `<No text content found>` | Tika (no text in Tika's answer), Docling (no Markdown) | `backend/open_webui/retrieval/loaders/main.py:244`, `:305` |
| `No text content found` | Mistral OCR (no pages in the answer) | `backend/open_webui/retrieval/loaders/mistral.py:286-293` |
| `No valid text content found in document` | Mistral OCR, PaddleOCR-vl (pages without text) | `backend/open_webui/retrieval/loaders/mistral.py:341-353`; `backend/open_webui/retrieval/loaders/paddleocr_vl.py:101-112` |
| `Error during processing: {e}` | Mistral OCR (any failure, including a refused key) | `backend/open_webui/retrieval/loaders/mistral.py:391-403` |
| `Error during OCR processing: {e}` | PaddleOCR-vl (any failure) | `backend/open_webui/retrieval/loaders/paddleocr_vl.py:116-127` |

### 10.7 Server Log Lines That Explain Symptoms

Log lines are not shown to users. Some contain user ids and file names (personal data).

| Log line (format as in the source) | Meaning | Source |
|---|---|---|
| `Error loading SentenceTransformer: {e}` | The local embedding model did not load; uploads and document questions will fail | `backend/open_webui/routers/retrieval.py:166-167` |
| `Cannot determine model snapshot path: {e}` | The model could not be found or downloaded; in offline mode this becomes a load failure | `backend/open_webui/retrieval/utils.py:1755-1759` |
| `Error loading reranking model: {e}` | The reranker did not load after a save; hybrid search was switched off | `backend/open_webui/routers/retrieval.py:1251-1253` |
| `Error updating models: {e}` | The reranker (or local model setup) failed at startup | `backend/open_webui/main.py:695-697` |
| `Problem updating embedding model: {e}` / `Problem updating reranking model: {e}` | The admin save failed (10.1) | `backend/open_webui/routers/retrieval.py:622`, `:1255` |
| `query_collection: %s collection(s) had failing queries: %s` | Some collections could not be searched (for example the store is down) | `backend/open_webui/retrieval/utils.py:779-785` |
| `query_collection_with_hybrid_search: %s collection(s) had failing queries: %s` | The same in hybrid search | `backend/open_webui/retrieval/utils.py:885-891` |
| `No valid scores found, check your reranking function. Returning original documents.` | The external reranker failed; results were not rescored | `backend/open_webui/retrieval/utils.py:1849-1851` |
| `Error in external reranking: {e}` / `No results found in external reranking response` | The external reranker call failed or answered oddly | `backend/open_webui/retrieval/models/external.py:63-69` |
| `Document with hash %s already exists` | The duplicate check fired (10.1) | `backend/open_webui/routers/retrieval.py:1751-1753` |
| `Starting reindexing for %s knowledge bases (%s files)`, `Reindexing knowledge base %s/%s file %s/%s%s: %s`, `Reindexing completed in %ss.` | Reindex progress | `backend/open_webui/routers/knowledge.py:396`, `:415-423`, `:453` |
| `Failed to process {len(failed_files)} files` and `File ID: {failed["file_id"]}, Error: {failed["error"]}` | Files the reindex could not rebuild, although the panel said `Success` | `backend/open_webui/routers/knowledge.py:440-443` |
| `Memory vector dimension mismatch for user %s; reindexing memory vectors.` | A memory write found old-size vectors and re-embedded that user's memories | `backend/open_webui/routers/memories.py:171-180` |
| `external_knowledge_retrieval knowledge_id=%s connection_id=%s provider=%s user_id=%s latency_ms=%s result_count=%s` | One external knowledge search (includes the user id) | `backend/open_webui/retrieval/external.py:365-373` |
| `Error loading document with MinerU: {e}`, `Error calling PaddleOCR-vl: {e}`, `An error occurred during the loading process after {total_time:.2f}s: {e}` | Engine failures (the last two engines then store the error text as content, 10.6) | `backend/open_webui/retrieval/loaders/mineru.py:68-70`; `backend/open_webui/retrieval/loaders/paddleocr_vl.py:116-117`; `backend/open_webui/retrieval/loaders/mistral.py:391-393` |
| `Invalid DOCLING_PARAMS format, expected JSON object` | Docling parameters ignored | `backend/open_webui/retrieval/loaders/main.py:619-624` |
| `Pgvector requires setting PGVECTOR_DB_URL or using Postgres with vector extension as the primary database.` | Startup refused: pgvector chosen without PostgreSQL | `backend/open_webui/config.py:648-652` |
| `VECTOR_LENGTH {VECTOR_LENGTH} does not match existing vector column dimension {db_vector_length}. Cannot change vector size after initialization without migrating the data.` | Startup refused: the pgvector length setting changed after data existed | `backend/open_webui/retrieval/vector/dbs/pgvector.py:315-320` |
| `Existing pgvector index '{index_name}' uses method '{existing_method}' but configuration now requires '{index_method}'. Automatic rebuild is disabled to prevent long-running maintenance. Drop the index manually (optionally after tuning maintenance_work_mem/max_parallel_maintenance_workers) and recreate it with the new method before restarting Open WebUI.` | Startup refused: the pgvector index method changed | `backend/open_webui/retrieval/vector/dbs/pgvector.py:218-226` |
| `Required configuration missing: {missing_vars}` / `Failed to initialize Pinecone index: {e}` | Startup refused: Pinecone settings missing or index unavailable | `backend/open_webui/retrieval/vector/dbs/pinecone.py:100-102`, `:126-128` |
| `QDRANT_URI is not set. Please configure it in the environment variables.` | Startup refused: Qdrant multitenancy without an address | `backend/open_webui/retrieval/vector/dbs/qdrant_multitenancy.py:59-60` |

## 11. Common Tier-1 Issues and Troubleshooting

Before anything else, collect: the chat id (the user types `/status` in the chat and copies the id it
shows; see `chat-completion-pipeline-and-generation-tasks.md`, section 11), the time with time zone,
the model name, the exact text of any pop-up or status line, and the document's **type and size**.
Do not ask for the document itself or its contents: MedIT GPT documents may contain personal or health
information. Tier 1 changes nothing; every setting below is changed only by an administrator, and the
escalation contact for MedIT GPT is **TO BE CONFIRMED** (none exists in the repository).

### 11.1 "I attached a file, got a yellow warning, and the AI says it can't see the document"

**Symptom.** A yellow pop-up appears after the upload; the file chip stays in the message; answers
ignore the file and the status reads `No sources found`.

**Likely causes, in order.**
1. Extraction failed or found no text; the warning carries the reason (10.1, 10.2), and the file was
   marked failed with no chunks (`backend/open_webui/routers/retrieval.py:2155-2189`;
   `src/lib/components/chat/MessageInput.svelte:1025-1028`).
2. The embedding step failed (provider unreachable, model not loaded) (10.1).
3. An external extraction service (Tika, Docling, Marker, MinerU, External) is down or refusing
   requests (5.2).

**Diagnostic steps.** Read the warning text with the user and match it in section 10. Ask whether other
files of the same type work, and whether a small plain-text file works (that isolates extraction from
embedding).

**Resolution.** Ask the user to remove the failed file and try a text-based copy (for example a PDF
exported from a word processor rather than a scan). If plain text also fails, the problem is embedding
or storage; escalate.

**Escalation.** Chat id, time, the warning text verbatim, file type and size, whether plain text works.

### 11.2 "It says 'The content provided is empty. Please ensure that there is text or data present before proceeding.'"

**Symptom.** That text in a warning pop-up after an upload, or when adding a file to a knowledge base.

**Likely causes, in order.**
1. The file has no text layer (a scanned PDF or a photo of a page) and OCR is off: the default PDF
   reader only reads text, and **PDF Extract Images (OCR)** is off by default
   (`backend/open_webui/retrieval/loaders/pdf.py:43-49`; `backend/open_webui/config.py:1004`).
2. A file type read as plain text that contains no readable text (5.3).
3. The file was being added to a knowledge base but has no stored text from an earlier failed upload
   (`backend/open_webui/routers/retrieval.py:1999-2015`).

**Diagnostic steps.** Ask whether the user can select and copy text in the document in their own
viewer. If not, it is an image-only document.

**Resolution.** Suggest a text-based version, or pasting the needed passage into the chat. Whether OCR
extraction (built-in OCR or an OCR engine) should be enabled is an administrator decision.

**Escalation.** File type, whether text is selectable, chat id, time.

### 11.3 "It says 'Duplicate content detected. Please provide unique content to proceed.'"

**Symptom.** Adding a file to a knowledge base is refused with that text.

**Likely causes, in order.**
1. Another file with the same extracted text is already in that knowledge base
   (`backend/open_webui/routers/retrieval.py:1734-1753`).

**Diagnostic steps.** Ask the user to check the knowledge base's file list for a copy under another
name.

**Resolution.** Use the copy that is already there, or remove it before adding the new one (owner or
users with write access, see `knowledge-bases.md`).

**Escalation.** Only if no duplicate is visible: knowledge base name, file type, time.

### 11.4 "The AI ignores my document or knowledge base and the status says 'No sources found'"

**Symptom.** A `No sources found` status line, no Sources button, and an answer that does not use the
material.

**Likely causes, in order.**
1. The file never became searchable (11.1, 11.2).
2. The search ran but nothing matched well enough: wording differs from the document, or with hybrid
   search a **Relevance Threshold** above 0 dropped everything (`backend/open_webui/retrieval/utils.py:1835-1836`).
3. Retrieval failed inside the server (store unreachable, embedding provider down, an external
   knowledge base unreachable); the same status is shown (`backend/open_webui/utils/middleware.py:2115-2137`).
4. The embedding model was changed and old chunks no longer match (11.5).
5. The user cannot read the attached knowledge base or file, so it was skipped (3.2).

If there is **no retrieval status at all**, the document was not searched: knowledge attached to a
custom model in native mode, or the model's file context capability is off (5.12).

**Diagnostic steps.** Ask the user to rephrase with words that appear in the document. Ask whether a
freshly uploaded small file is found (that tests the whole pipeline). Ask whether colleagues see the
same with the same knowledge base.

**Resolution.** For a single document, suggest switching it to **Using Entire Document** in the file
window (5.9) so no search is needed. Otherwise escalate.

**Escalation.** Chat id, time, knowledge base or file name as the user sees it, whether a new upload
works, and whether the problem started after a known settings change.

### 11.5 "Search stopped finding things (or got worse) after the admin changed something"

**Symptom.** Documents that used to be found now give `No sources found` or irrelevant passages, for
everyone, starting at a known time.

**Likely causes, in order.**
1. The embedding engine or model changed and the content was not reindexed. In Chroma, old chunks
   stop matching without any error; in pgvector they match poorly (5.13).
2. The reindex ran, but the affected files were chat uploads, which reindexing does not cover (5.13,
   step 7).
3. With several server processes, some still use the old model until restarted (6.5, inferred).
4. Hybrid search was switched off by a failed reranker load (11.14).

**Diagnostic steps.** Establish when it started and whether knowledge bases, chat files or both are
affected.

**Resolution.** Escalate. The fix (Reindex, re-uploading chat files, or restarting all processes) is
administrator work; users can meanwhile use **Using Entire Document** for single files.

**Escalation.** Start time, which items are affected (knowledge base or chat upload), and one chat id.

### 11.6 "Every upload fails with 'No embedding model is loaded...'"

**Symptom.** Warning pop-ups quoting `No embedding model is loaded. Set RAG_EMBEDDING_MODEL to a valid SentenceTransformer model name, or configure an external RAG_EMBEDDING_ENGINE (ollama, openai, azure_openai).`,
for all users.

**Likely causes, in order.**
1. The server runs offline (or with automatic model updates off) and the embedding model is not in its
   cache (`backend/open_webui/retrieval/utils.py:1721-1759`; `backend/open_webui/config.py:1013-1015`).
2. The model name was changed to one that does not exist (5.5).
3. The model files in the cache are damaged or the cache location changed (`Dockerfile:105`, `:112`).

**Diagnostic steps.** None for tier 1 beyond confirming it affects everyone.

**Resolution.** Escalate immediately; uploads and document searches fail until the model loads (whole-document modes still work for files already processed).

**Escalation.** Time it started, any recent deployment or settings change, one example time stamp so the
log line `Error loading SentenceTransformer: {e}` can be found.

### 11.7 "The answer quotes text like 'Error during processing' or '<No text content found>'"

**Symptom.** The model's answer or the citation window shows a short error-like text instead of the
document.

**Likely causes, in order.**
1. The Mistral OCR or PaddleOCR-vl engine failed and stored its error text as the document (10.6).
2. Tika or Docling found no text and stored `<No text content found>` (10.6).

**Diagnostic steps.** Open the source in the citation window and note the exact text.

**Resolution.** Ask the user to try a text-based copy. Escalate so an administrator can check the OCR
service.

**Escalation.** The exact stored text, file type, time, chat id.

### 11.8 "The AI only uses a small part of my long document"

**Symptom.** Answers draw on a few passages and miss content elsewhere in the document.

**Likely causes, in order.**
1. Focused retrieval returns only **Top K** chunks per attached item, three by default
   (`backend/open_webui/config.py:968`; `backend/open_webui/retrieval/utils.py:639-679`).
2. The question is broad (a summary of the whole document), which chunk search handles poorly.

**Diagnostic steps.** Ask whether the question needs the whole document.

**Resolution.** Show the user the file window switch **Using Entire Document**, or the personal
**Default Upload Mode** (5.9, 7.8). Very large documents may then exceed the model's limit (11.20).

**Escalation.** Not normally needed. If many users need longer answers, pass the request on so an
administrator can review Top K.

### 11.9 "It says the file is too large, or my file type isn't allowed"

**Symptom.** `File size should not exceed {maxSize} MB.`, a pop-up about the file being too large, or a
`[ERROR: File type {file_extension} is not allowed]` refusal (`backend/open_webui/routers/files.py:354-361`).

**Likely causes, in order.**
1. **Max Upload Size**, **Max Upload Count** or **Allowed File Extensions** on the Documents panel (7.4).
2. An archive-type document that expands too much (`Document archive is too large after decompression`, 10.1).

**Diagnostic steps.** Note the file size and type.

**Resolution.** Suggest splitting the document or converting it. Limits are an administrator's
decision; their live values are **TO BE CONFIRMED**. Details are in `files-uploads-and-storage.md`.

**Escalation.** Only for a business need: file type, size, purpose.

### 11.10 "My upload spins for a very long time"

**Symptom.** The file chip keeps its spinner for minutes.

**Likely causes, in order.**
1. A large document being parsed or OCR'd; Marker and MinerU cloud wait up to about 10 minutes, MinerU
   local up to its timeout (5.2).
2. Slow embedding: batch size 1 by default and no overall time limit (5.5).
3. The extraction or embedding service is slow or hanging; the browser keeps waiting for up to two
   hours (`backend/open_webui/routers/files.py:645-668`).

**Diagnostic steps.** Ask for file size and page count, and whether small files finish quickly.

**Resolution.** Suggest waiting, or splitting the document. If small files are also slow, escalate.

**Escalation.** File size, start time, whether small files are affected, chat id.

### 11.11 "The sources list shows the wrong document, or two of my files appear as one"

**Symptom.** One source chip seems to mix passages from two files, or `[2]` opens a file the user did
not expect.

**Likely causes, in order.**
1. Two attached files have the same file name; sources are grouped and numbered by name, so they share
   one chip and one number (5.11; inferred, section 14).
2. The passages genuinely came from that file: retrieval picked the closest chunks, which may not be the
   ones the user had in mind.

**Diagnostic steps.** Ask whether the attached files share a name. Open the source and read the passage
shown.

**Resolution.** Suggest renaming one copy before uploading. Otherwise explain that sources show the
passages actually given to the model.

**Escalation.** Only if names differ and the passage clearly belongs to another file: chat id, time.

### 11.12 "I don't see any sources or [1] numbers under the answer"

**Symptom.** No Sources button, or a Sources button but no numbered markers in the text.

**Likely causes, in order.**
1. Nothing was retrieved (11.4).
2. The user switched off **Inline Citations** (fork setting): markers are removed but the Sources button
   stays (`src/lib/components/chat/Messages/ContentRenderer.svelte:128-137`;
   `src/lib/i18n/locales/en-US/translation.json:2935-2936`).
3. The model's **citations** capability is off: no button and no markers
   (`src/lib/components/chat/Messages/ResponseMessage.svelte:934-941`).
4. The model chose not to cite; the RAG template asks for `[id]` markers but cannot force them
   (`backend/open_webui/config.py:1070-1094`).
5. **Hide Processing Details** is on, which hides the status lines (not the sources) (section 12).

**Diagnostic steps.** Ask whether Settings > Interface > **Inline Citations** is on; ask whether other
models show sources.

**Resolution.** Point the user to their own Inline Citations setting. Model capabilities are changed by
administrators.

**Escalation.** Model name, chat id.

### 11.13 "The relevance percentage on a source looks low"

**Symptom.** A red or orange percentage in the citation window for a passage that looks right.

**Likely causes, in order.**
1. The score's meaning depends on the search path (5.11). ColBERT spreads one total across candidates,
   so each looks small; plain vector search rarely goes far below 50 %.
2. A genuinely weak match.

**Diagnostic steps.** Compare the passages within the same answer rather than with other answers.

**Resolution.** Explain that the percentage ranks passages within one answer and is not an absolute
quality score.

**Escalation.** Not needed.

### 11.14 "(Admin) I turned on hybrid search and it switched itself off"

**Symptom.** After Save, `Settings saved successfully!` appears, but on reopening the panel **Hybrid
Search** is off.

**Likely causes, in order.**
1. The reranking model could not be loaded (wrong name, no download allowed, offline without a cached
   copy), so the server turned hybrid search off and saved that
   (`backend/open_webui/routers/retrieval.py:1235-1253`).
2. In the slim image, a local reranker is refused outright with a pop-up (10.1).

**Diagnostic steps.** Note the reranking engine and model shown on the panel.

**Resolution.** Escalate to the platform maintainer with the model name; the server log line
`Error loading reranking model: {e}` gives the reason. Clearing the reranking model (cosine rescoring)
is an administrator's choice.

**Escalation.** Reranking engine and model name, time of the save.

### 11.15 "(Admin) I pressed Save on the Documents page and nothing happened, or got an error and a success together"

**Symptom.** No pop-up at all after Save, or a red embedding error followed by `Settings saved successfully!`.

**Likely causes, in order.**
1. The panel's embedding step failed (for example `Model filesystem path detected. Model shortname is required for update, cannot continue.`
   for an empty Ollama model) while the rest of the settings were saved (7.10).
2. The main settings call failed, and the panel has no handler for that failure, so nothing is shown
   (7.10, inferred).

**Diagnostic steps.** Reopen the panel and compare the values with what was entered.

**Resolution.** Re-enter the missing values; if values do not stick, escalate.

**Escalation.** Which fields were changed, time, any pop-up text.

### 11.16 "(Admin) Reindex said Success but some documents still aren't found"

**Symptom.** `Success` after **Reindex**, yet some items still give `No sources found`.

**Likely causes, in order.**
1. Those items are chat uploads, which the reindex does not touch (5.13).
2. Individual knowledge-base files failed during the reindex; failures are only logged as
   `Failed to process {len(failed_files)} files` (`backend/open_webui/routers/knowledge.py:440-443`).
3. Files with no stored text (earlier failed uploads) cannot be rebuilt (`backend/open_webui/routers/retrieval.py:2014-2015`).
4. Other server processes still hold the old embedding model (6.5, inferred).

**Diagnostic steps.** Establish whether the missing items are knowledge-base files or chat uploads.

**Resolution.** Users can re-upload chat files. Escalate for the rest.

**Escalation.** Time of the reindex, names of a few affected knowledge bases.

### 11.17 "(Admin) After 'Reset Upload Directory' everything is gone"

**Symptom.** Files, knowledge-base contents and memories search no longer work for anyone.

**Likely causes, in order.**
1. The button deletes every user's file records and stored files **and empties the whole vector
   store**, which is far more than its description says (5.16;
   `backend/open_webui/routers/files.py:575-597`).

**Diagnostic steps.** Confirm the time the button was pressed (the platform event `file.deleted_all` is
published, 9.2).

**Resolution.** Escalate at once as a data-loss incident; recovery depends on backups, which are
**TO BE CONFIRMED** (see `deployment-operations-and-logging.md`). If personal or health data handling is
affected, also follow the U of T privacy incident process (privacy.utoronto.ca).

**Escalation.** Time of the action, who performed it (role only in the ticket), what is missing.

### 11.18 "(Admin) The external knowledge test does nothing, or says 'Test returned no results.'"

**Symptom.** **Verify Connection** spins and stops without a pop-up, or reports `Test returned no results.`

**Likely causes, in order.**
1. The external store is unreachable or refused the request; that error is not turned into a readable
   message, so the panel shows nothing (10.4, inferred).
2. The collection exists but its vectors were made with a different embedding model, so nothing
   matches (`src/lib/components/admin/Settings/ExternalKnowledge.svelte:757-764`).
3. Wrong field names (content, vector, metadata) for that collection (7.7).
4. The server lacks the provider's library (`qdrant-client is not installed` and similar, 10.4).

**Diagnostic steps.** Note the provider, endpoint (host only) and collection name.

**Resolution.** Escalate; connection details and credentials are handled by the platform maintainer.

**Escalation.** Provider, collection name, time; never the API key or connection password.

### 11.19 "It says 'Pandoc is not installed on the server. Please contact your administrator for assistance.'"

**Symptom.** That text when uploading certain document types.

**Likely causes, in order.**
1. The server environment lacks the pandoc program used by a document parser
   (`backend/open_webui/routers/retrieval.py:2180-2184`). The standard Docker image installs it
   (`Dockerfile:145-147`), so this points to a different build or host.

**Diagnostic steps.** Note the file type.

**Resolution.** Suggest converting to PDF or plain text meanwhile; escalate.

**Escalation.** File type, time.

### 11.20 "The model gives an error when I use 'Using Entire Document' with a big file"

**Symptom.** With **Using Entire Document**, Full Context Mode or bypass mode, the reply fails or is cut
short on large documents.

**Likely causes, in order.**
1. The whole text plus the RAG template exceeds the model's context window; the provider's error
   appears in the reply (`chat-completion-pipeline-and-generation-tasks.md`).
2. Several large documents attached at once.

**Diagnostic steps.** Ask for the document's size and how many are attached.

**Resolution.** Switch the file back to **Using Focused Retrieval**, attach fewer documents, or choose a
model with a larger context window.

**Escalation.** Model name, approximate size, chat id, the error text.

## 12. Local Customisations

**This area matches upstream Open WebUI v0.11.4.** `git diff main...uoft` and `git diff` (working tree)
show no change in any file in scope: `backend/open_webui/routers/retrieval.py`, everything under
`backend/open_webui/retrieval/` (loaders, vector stores, reranker models, `external.py`, `utils.py`),
`backend/open_webui/utils/embeddings.py`, the `rag.*` parts of `backend/open_webui/config.py`,
`initialize_runtime_config` in `backend/open_webui/main.py`,
`src/lib/components/admin/Settings/Documents.svelte`,
`src/lib/components/admin/Settings/ExternalKnowledge.svelte`, `src/lib/apis/retrieval/index.ts`,
`src/lib/components/chat/Messages/Citations.svelte` and `src/lib/components/chat/Messages/Citations/`.
None of the `settings.admin.documents.*` texts is changed in `en-US`.

Fork and working-tree changes in neighbouring files change what users **see** of retrieval:

| Change | Where | Effect on this area | Status |
|---|---|---|---|
| Per-user **Inline Citations** (`showInlineCitations`, on by default): "Show source links within responses. When off, sources are still listed below each response." | `src/lib/components/chat/Messages/ContentRenderer.svelte:128-137`; `src/lib/components/common/InterfaceSettings.svelte:79`, `:357`, `:1338-1354`; `backend/open_webui/models/users.py:99-100`; `src/lib/i18n/locales/en-US/translation.json:2935-2936` | When off, the `[1]` markers produced by the RAG template's citation instruction are stripped from the answer; the Sources button and citation window are unchanged. Upstream strips markers only when the model's citations capability is off | Fork commit on `uoft` |
| Per-user **Hide Processing Details** (`hideProcessingDetails`, off by default) | `src/lib/components/chat/Messages/ResponseMessage.svelte:197-221`; `src/lib/i18n/locales/en-US/translation.json:2923-2924` | Hides the retrieval status lines of 9.1 (`Querying`, `Retrieved {count} sources`, `No sources found`), showing `Thinking...` until answer text arrives. Sources still appear. Tier 1 should ask about this setting before concluding that "nothing was searched" | Fork commit, refined by uncommitted working-tree edits |
| Type annotation only | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:8` | None (shifts later line numbers by one relative to upstream) | Uncommitted working-tree edit |

Status lines are also hidden when a model's **status updates** capability is off
(`src/lib/components/chat/Messages/ResponseMessage.svelte:198-199`). The fork's settings are documented
in `user-settings-and-personalisation.md` and `chat-composer-and-message-display.md`.

Nothing in the repository configures retrieval specifically for MedIT GPT: no extraction engine,
embedding model, vector store, reranker or template differs from upstream defaults in code. Whether
production overrides any section 7 default is data, **TO BE CONFIRMED**.

## 13. Source File Index

### 13.1 In Scope (Read in Full or by Section)

| File | What it holds |
|---|---|
| `backend/open_webui/routers/retrieval.py` | Embedding and reranker loading (`:149-242`), the settings key map (`:254-415`), settings endpoints (`:468-1551`), chunk merging and splitting (`:1561-1694`), saving to the vector store (`:1705-1912`), file and text processing (`:1925-2242`), query, delete, reset and batch endpoints (`:3050-3459`). The web-search block (`:2245-3047`) was read only for collection naming and slim refusals |
| `backend/open_webui/retrieval/utils.py` | Loader settings, URL content, vector and hybrid search, result merging, embedding providers, reranking, collection access, source building, model paths, rescoring (read in full) |
| `backend/open_webui/retrieval/external.py` | External knowledge retrieval for Qdrant, Milvus and pgvector (read in full) |
| `backend/open_webui/retrieval/loaders/main.py` | Engine selection and built-in loaders (read in full) |
| `backend/open_webui/retrieval/loaders/local.py`, `pdf.py`, `external_document.py`, `datalab_marker.py`, `mineru.py`, `mistral.py`, `paddleocr_vl.py` | The individual loaders (read in full) |
| `backend/open_webui/retrieval/loaders/external_web.py`, `tavily.py`, `youtube.py`, `microsoft_web_iq.py` | Web loaders, skimmed; owned by `web-search-and-web-loading.md` |
| `backend/open_webui/retrieval/vector/factory.py`, `type.py`, `main.py`, `async_client.py`, `utils.py` | Backend selection, the common interface, the thread-offloading client, metadata filtering and hybrid result merging (read in full) |
| `backend/open_webui/retrieval/vector/dbs/chroma.py` | Chroma backend (read in full) |
| `backend/open_webui/retrieval/vector/dbs/pgvector.py` | pgvector backend: setup, length and index checks, search, native hybrid search, reset (read by section) |
| `backend/open_webui/retrieval/vector/dbs/` (the other 13 files) | Settings, constructors, naming and startup errors of each community backend |
| `backend/open_webui/retrieval/models/base_reranker.py`, `colbert.py`, `external.py` | Reranker implementations (read in full) |
| `backend/open_webui/utils/embeddings.py` | The public embeddings dispatcher (read in full) |
| `backend/open_webui/config.py` | Vector store settings (`:499-835`), retrieval settings (`:838-1107`), the seeded `rag.*` keys (`:2857-2940`) |
| `backend/open_webui/main.py` | Lifespan start (`:344-369`), `initialize_runtime_config` (`:621-752`), router mount (`:852`), `/api/embeddings` (`:1068-1094`) |
| `src/lib/components/admin/Settings/Documents.svelte` | The Documents admin panel (read in full) |
| `src/lib/components/admin/Settings/ExternalKnowledge.svelte` | The External Knowledge Sources panel (read in full) |
| `src/lib/apis/retrieval/index.ts` | Front-end client for the retrieval router (every function mapped) |
| `src/lib/components/chat/Messages/Citations.svelte`, `Citations/CitationModal.svelte`, `Citations/CitationsModal.svelte` | Sources button, citation window, and a list window that no other component uses (read in full) |
| `src/lib/i18n/locales/en-US/translation.json` | English text of `settings.admin.documents.*` (`:2196-2363`) and the other dotted keys cited |

### 13.2 Read for Context (Owned by Other Areas)

| File | Why |
|---|---|
| `backend/open_webui/utils/middleware.py` | Source tags and RAG template placement (`:935-1008`), file context tags (`:1771-1825`), retrieval step (`:2049-2167`), folder and model knowledge (`:2555-2644`), metadata files (`:2925-2945`), native knowledge (`:3080-3123`), file context switch and sources event (`:3206-3246`), saving sources (`:4895-4917`) |
| `backend/open_webui/utils/task.py`, `backend/open_webui/utils/misc.py` | `rag_template` (`:265-301`); message merging (`:658-717`) |
| `backend/open_webui/routers/files.py` | Upload checks, background processing, status stream, delete-all (`:96-280`, `:350-460`, `:575-680`) |
| `backend/open_webui/routers/knowledge.py` | Knowledge-base search index, reindex endpoints, external knowledge endpoints (`:60-151`, `:365-1088`) |
| `backend/open_webui/routers/memories.py` | Memory reindexing (`:125-190`, `:440-510`) |
| `backend/open_webui/routers/tasks.py` | Retrieval query generation switch (`:400-440`) |
| `backend/open_webui/tools/builtin.py` | Built-in knowledge and chat-file tools (`:2509-2620`, `:3151-3240`, `:3372-3440`) |
| `backend/open_webui/events.py`, `backend/open_webui/utils/notifications.py` | Event definitions and notification events (`:290-432`, `:650-700`, `:1070-1090`; `:200-260`) |
| `backend/open_webui/socket/main.py` | Saving tool sources (`:1230-1255`) |
| `backend/open_webui/env.py` | Environment-only settings cited in 7.9 |
| `backend/open_webui/constants.py` | Error texts (`:1-112`) |
| `backend/open_webui/models/files.py`, `backend/open_webui/utils/headers.py` | File record columns; identity forwarding |
| `Dockerfile` | Model pre-download and cache paths (`:6-19`, `:62-112`, `:140-185`) |
| `src/lib/components/chat/MessageInput.svelte`, `src/lib/apis/files/index.ts`, `src/lib/utils/index.ts` | Upload flow, warnings, browser-side extraction for temporary chats |
| `src/lib/components/common/FileItemModal.svelte`, `src/lib/components/common/InterfaceSettings.svelte`, `src/lib/components/common/FileItem.svelte` | Entire-document switch, Default Upload Mode, Inline Citations, file chip |
| `src/lib/components/chat/Messages/ResponseMessage.svelte`, `ContentRenderer.svelte`, `ResponseMessage/StatusHistory/StatusItem.svelte` | Where sources and status lines render |
| `src/lib/components/chat/SettingsModal.svelte`, `src/routes/(app)/admin/settings/[tab]/+page.svelte`, `src/lib/components/admin/Settings/Integrations.svelte` | Admin tab wiring and save pop-up |
| `src/lib/components/common/ConfirmDialog.svelte`, `src/lib/components/common/ExperimentalBadge.svelte` | Confirmation and badge texts |
| `src/lib/apis/knowledge/index.ts` | External knowledge client functions (`:41-330`) |
| `src/lib/components/chat/Chat.svelte`, `src/lib/components/workspace/Models/Knowledge.svelte` | Web attachments and model knowledge in full-context mode |

## 14. Open Questions

Nothing found in the code contradicts `tools/ground-truth.md`; its Data Stores row (Chroma in
`DATA_DIR/vector_db`, pgvector in the slim image, chosen by `VECTOR_DB`) matches
`backend/open_webui/config.py:503-506`. The items below could not be established from the repository.

**Production data and deployment (TO BE CONFIRMED).**

1. The live value of every Documents setting in section 7: extraction engine and its service
   addresses, embedding engine and model, chunk settings, hybrid search, reranking engine and model,
   Top K, Top K Reranker, threshold, BM25 weight, full context mode, bypass mode, custom RAG template,
   upload limits and cloud pickers. These are rows in the `config` table.
2. Which vector store production uses (`VECTOR_DB`), where it lives, and how it is backed up; whether
   the server runs the standard or the slim image; whether it runs in Docker; where the model cache
   lives and whether it survives redeployment (the image places it inside the data folder,
   `Dockerfile:105`, `:112`); the value of `OFFLINE_MODE`.
3. Which external services receive documents or text (extraction engines, embedding and reranking
   providers, OCR services), whether they are approved for the personal and health information MedIT
   GPT may hold, and whether `ENABLE_FORWARD_USER_INFO_HEADERS` is on. If the **External** document
   loader is used, it receives each uploader's name, user id, email and role with every file
   (`backend/open_webui/retrieval/loaders/external_document.py:56-57`).
4. The number of server processes and replicas, which decides whether the per-process model state of
   section 6.5 matters.
5. Whether any external knowledge sources are configured, and with which providers.
6. Webhook and notification destinations for the `retrieval.*` events, which carry file names.
7. Backup and restore arrangements for uploads and the vector store (needed for 11.17).
8. The escalation contact for MedIT GPT and whether tier 1 can see the admin panels or the server log
   (section 11 assumes an administrator does the checking).
9. Environment values: `RAG_EMBEDDING_TIMEOUT`, `AIOHTTP_CLIENT_TIMEOUT`, `RAG_SYSTEM_CONTEXT`,
   `RAG_SOURCE_METADATA_KEYS`, the embedding prefixes, `ENABLE_RAG_CSV_SUMMARY`, `REQUESTS_VERIFY`,
   `MINERU_MAX_MARKDOWN_BYTES`, and the stored `rag.tiktoken_encoding_name` and
   `rag.external_reranker_timeout`, which have no panel field.
10. Retention of the Datalab Marker output copies in `/app/backend/data/uploads/marker_output/`
    (`backend/open_webui/retrieval/loaders/datalab_marker.py:211-224`); nothing in the code deletes them.

**Behaviour inferred from code that should be confirmed by testing.**

11. **Stale models in other processes.** After an admin changes the embedding or reranking model, only
    the process that handled the save reloads it; no code tells other workers or replicas to reload
    (`backend/open_webui/routers/retrieval.py:564-597`, `:1235-1250`; `backend/open_webui/main.py:666-752`).
    Uploads use the new embedding model everywhere, because each upload builds its embedding function
    from the stored settings, but questions in other processes would still use the old one.
12. **Chat uploads are not reindexed.** The Reindex button covers knowledge-base files, the
    knowledge-base search index and memories only (`backend/open_webui/routers/knowledge.py:374-494`;
    `backend/open_webui/routers/memories.py:449-480`). Files attached only to chats would keep old
    embeddings after a model change, and files uploaded while bypass mode was on would stay without
    chunks after it is switched off.
13. **Chroma and dimension changes.** A search with a different-sized embedding raises inside Chroma and
    is swallowed (`backend/open_webui/retrieval/vector/dbs/chroma.py:82-107`), so nothing is found and
    nothing is logged; adding a new file to an existing knowledge-base collection built with the old
    model is expected to fail with Chroma's own dimension error, whose wording comes from the Chroma
    library rather than this repository.
14. **Same-name files.** Sources are grouped and numbered by the `source` metadata, which is the file
    name, so two different files with the same name should share one chip and one number
    (`src/lib/components/chat/Messages/Citations.svelte:118-144`;
    `backend/open_webui/utils/middleware.py:947-950`).
15. **External knowledge failures.** The external search call in `get_sources_from_items` is not wrapped
    on its own (`backend/open_webui/retrieval/utils.py:1581-1589`), so one unreachable external source
    should empty the sources of the whole message. Its runtime errors are plain exceptions, so a failing
    **Verify Connection** most likely returns a non-JSON server error that the panel's client turns into
    no pop-up at all (`src/lib/apis/knowledge/index.ts:223-250`).
16. **Silent Save failure.** `updateRAGConfig` is called without an error handler in the Documents panel
    (`src/lib/components/admin/Settings/Documents.svelte:264-298`), so a refused save should show
    nothing.
17. **Status-code prefix on engine errors.** When an extraction engine raises an HTTP-style error, the
    stored message is that error converted to text, which the installed web framework renders as
    `{status_code}: {detail}` (Starlette's `HTTPException.__str__` in the project virtual environment,
    outside the first-party code). Confirm what users see, for example `400: MinerU returned empty results`.
18. **Passages persist in chats.** Sources, including passage text, are saved with each reply
    (`backend/open_webui/utils/middleware.py:4900-4917`), so document text should remain visible in old
    chats after the file or knowledge base is deleted. Relevant to privacy requests.
19. **Reset Upload Directory and knowledge bases.** The call deletes every file record and empties the
    vector store but does not delete knowledge-base records; their file links are removed by the
    database's cascade rule where it is enforced (`backend/open_webui/models/files.py:455-463`;
    `backend/open_webui/models/knowledge.py:104-105`). What users then see in each knowledge base is not
    established.
20. **Datalab Marker outside Docker.** The output folder is the fixed path `/app/backend/data/uploads/marker_output`
    and the folder is created outside the error handling (`backend/open_webui/retrieval/loaders/datalab_marker.py:211-212`),
    so on a host without that path every Marker extraction may fail.
21. **Document Intelligence without a key setting.** When the key setting is absent rather than empty,
    the code passes neither a key nor an Azure identity and the loader refuses with
    `Provide exactly one of api_key or azure_credential.` (`backend/open_webui/retrieval/loaders/main.py:646-659`;
    `backend/open_webui/retrieval/loaders/local.py:101-102`).
22. **BM25 Weight "Default" button.** Choosing **Default** sends no value, so a previously stored custom
    weight should remain (`src/lib/components/admin/Settings/Documents.svelte:1379-1391`;
    `backend/open_webui/routers/retrieval.py:1031-1033`).

**Not establishable from code, or recorded for completeness.**

23. The panel description of **Top K Reranker** ("Maximum number of hybrid results sent to the reranker.")
    does not match the code, which keeps that many results after rescoring
    (`src/lib/i18n/locales/en-US/translation.json:2355`; `backend/open_webui/retrieval/utils.py:581-606`).
    Which reading the upstream authors intend is not recorded.
24. The front-end client defines four functions for retrieval endpoints the backend no longer has
    (`src/lib/apis/retrieval/index.ts:97-306`), and `Citations/CitationsModal.svelte` is not used by any
    component; both look like leftovers from earlier versions.
25. Security-sensitive: refer to the platform maintainer and U of T Information Security
    (security.utoronto.ca). Three items were noted and deliberately not described: a development-only
    route in the retrieval router, the model "trust remote code" switches, and the environment switches
    that relax retrieval access checks.
26. Whether the pre-downloaded model in the Docker image is still visible when production mounts a data
    volume over `/app/backend/data` depends on the volume type and is a deployment question
    (`Dockerfile:105`, `:160-180`; `docker-compose.yaml:18`).
