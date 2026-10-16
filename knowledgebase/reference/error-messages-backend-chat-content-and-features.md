# Error Messages: Backend, Chat, Content and Features

## At a Glance

- A cross-cutting catalogue of every error message the MedIT GPT backend raises from the chat,
  content and feature routers (chats, folders, channels, notes, files, knowledge, retrieval,
  models, prompts, skills, tools, memories, audio, images, automations, calendar, terminals, and
  the OpenAI and Ollama proxies), the chat helper modules in `backend/open_webui/utils/`, the
  retrieval package and the built-in tools.
- Most messages reach the user as a toast that prints the server's `detail` text; some reach the
  model instead (tool results) or appear as an error box under a chat response.
- The full `ERROR_MESSAGES` constant table is owned by the sibling catalogue
  [`error-messages-backend-identity-admin-and-platform.md`](error-messages-backend-identity-admin-and-platform.md);
  this document lists where each constant is raised within its own scope.
- Section 10 is the catalogue, grouped by source file; section 11 groups the most frequent content
  messages into triage patterns.
- Section 10 holds 36 subsections and about 560 rows; most rows point to the area document that
  explains the message in depth. No message text in scope differs from upstream v0.11.4 (section 12),
  and a few texts can never reach a user (section 14.1).

## 1. Purpose and Who Uses It

This catalogue lets tier-1 support take an error text that a MedIT GPT user reports from the chat,
content or feature parts of the application, find the server code that produced it, and see what
usually causes it and what to check. It lists **server (backend) text only**. Texts written by the
browser itself (for example `Session expired. Please sign in again.`) belong to the two front-end
catalogues planned as areas 30 and 31 in `_areas.md`.

| Reader | What they use it for |
|---|---|
| Tier-1 support (read-only) | Matching a reported text to a row in section 10, then following the row's support check or the pattern in section 11 |
| Platform maintainer | The source lines and triggers behind an escalation; the server-log-only rows (vector store, loader and provider start-up failures) |
| Administrators | Messages that only appear on admin screens (connection checks, document and audio settings) |
| Integrators using the API | Texts returned by `/openai`, `/ollama` and `/api/v1/...` without any screen in between |

Scope, as assigned in `_areas.md` row 29 (plus `utils/models.py`):

- the routers `chats`, `folders`, `channels`, `notes`, `files`, `knowledge`, `retrieval`, `models`,
  `prompts`, `skills`, `tools`, `memories`, `audio`, `images`, `automations`, `calendar`,
  `terminals`, `openai` and `ollama` in `backend/open_webui/routers/`;
- the helpers `middleware.py`, `chat.py`, `tools.py`, `files.py`, `memory.py`, `automations.py`,
  `code_interpreter.py` and `models.py` in `backend/open_webui/utils/`;
- everything under `backend/open_webui/retrieval/` (loaders, vector stores, web search, embedding
  and reranking helpers) and `backend/open_webui/tools/` (the built-in tools and the knowledge
  file-system tool).

The text of the shared constants (`ERROR_MESSAGES`, `backend/open_webui/constants.py:37-132`) and
every message raised by the identity, admin and platform code are catalogued in the sibling
document [`error-messages-backend-identity-admin-and-platform.md`](error-messages-backend-identity-admin-and-platform.md).
This document lists where each constant is raised **within its own scope** and what it means
there. Status lines (`'type': 'status'` events) are catalogued in the in-chat status catalogue
planned as area 32; this document only notes where an error text from its scope becomes a status
line.

## 2. Navigation and URLs

### 2.1 Where the Routers in Scope Are Mounted

Every router below answers under the path shown (`backend/open_webui/main.py:843-883`). The URL a
user's browser called tells you which section 10 subsection to search.

| Router file | Path prefix | Mounted at |
|---|---|---|
| `routers/chats.py` | `/api/v1/chats` | `backend/open_webui/main.py:861` |
| `routers/folders.py` | `/api/v1/folders` | `backend/open_webui/main.py:873` |
| `routers/channels.py` | `/api/v1/channels` | `backend/open_webui/main.py:860` |
| `routers/notes.py` | `/api/v1/notes` | `backend/open_webui/main.py:862` |
| `routers/files.py` | `/api/v1/files` | `backend/open_webui/main.py:875` |
| `routers/knowledge.py` | `/api/v1/knowledge` | `backend/open_webui/main.py:867` |
| `routers/retrieval.py` | `/api/v1/retrieval` | `backend/open_webui/main.py:852` |
| `routers/models.py` | `/api/v1/models` | `backend/open_webui/main.py:865` |
| `routers/prompts.py` | `/api/v1/prompts` | `backend/open_webui/main.py:868` |
| `routers/skills.py` | `/api/v1/skills` | `backend/open_webui/main.py:870` |
| `routers/tools.py` | `/api/v1/tools` | `backend/open_webui/main.py:869` |
| `routers/memories.py` | `/api/v1/memories` | `backend/open_webui/main.py:872` |
| `routers/audio.py` | `/api/v1/audio` | `backend/open_webui/main.py:851` |
| `routers/images.py` | `/api/v1/images` | `backend/open_webui/main.py:849` |
| `routers/automations.py` | `/api/v1/automations` | `backend/open_webui/main.py:882` |
| `routers/calendar.py` | `/api/v1/calendars` (plural) | `backend/open_webui/main.py:883` |
| `routers/terminals.py` | `/api/v1/terminals` | `backend/open_webui/main.py:881` |
| `routers/openai.py` | `/openai` | `backend/open_webui/main.py:844` |
| `routers/ollama.py` | `/ollama` | `backend/open_webui/main.py:843` |

The helpers in `utils/`, `retrieval/` and `tools/` have no URL of their own: their messages
surface through the router or chat request that called them (section 2.2).

### 2.2 Where a Backend Message Appears on Screen

| Surface | How a backend text gets there | Evidence |
|---|---|---|
| **Red pop-up (toast)** printing the server text | The API helper throws the response's `detail` and the screen calls `toast.error` with it; about 300 call sites print the thrown text unchanged | `src/lib/apis/chats/index.ts:4-10`, `:24-30`; `src/lib/apis/index.ts:201-202`; for example `src/lib/components/AddConnectionModal.svelte:84` |
| **Yellow pop-up after an upload** | Upload and processing failures stored on the file record as `error` are shown as a warning while the file stays attached | `src/lib/components/chat/MessageInput.svelte:1025-1028`; `backend/open_webui/routers/files.py:262-266` |
| **Error box under a chat response** | The chat pipeline stores `{'error': {'content': ...}}` on the message and sends a `chat:message:error` or `chat:completion` event; the response shows the box | `backend/open_webui/utils/middleware.py:4232-4262`, `:4845-4867`; `src/lib/components/chat/Chat.svelte:1284-1285`; `src/lib/components/chat/Messages/ResponseMessage.svelte:930-932`; `src/lib/components/chat/Messages/Error.svelte:6-36` |
| **Toast plus error box when the chat request itself fails** | The request to `/api/chat/completions` fails, or the answer carries an `error`; the box then starts with `Uh-oh! There was an issue with the response.` | `src/lib/components/chat/Chat.svelte:3643-3664`, `:3716-3750` |
| **Status line under a response** | A web-search failure prints the search endpoint's `detail` (or `An error occurred while searching the web`) as a red status line | `backend/open_webui/utils/middleware.py:1714-1727` |
| **Tool result** (read by the model, visible when the user expands the tool call) | Built-in tools return JSON with an `error` key or text starting `Error:`; the tool-call display marks those results as failed | `backend/open_webui/tools/builtin.py:194` (one of 53 such returns); `src/lib/components/common/ToolCallDisplay.svelte:94-134` |
| **Text inside a document** | Some extraction engines store an error sentence as the file's text instead of failing | `backend/open_webui/retrieval/loaders/mistral.py:391-403`; `backend/open_webui/retrieval/loaders/paddleocr_vl.py:116-127` |
| **Server log only** | Start-up and configuration failures of vector stores, loaders and providers; tier 1 cannot see these | for example `backend/open_webui/retrieval/vector/factory.py:97` |

### 2.3 Error Text the Browser Writes Itself

Two fallbacks are front-end text, not server text, but they wrap server messages and are often
quoted in tickets:

| Text | When | Source |
|---|---|---|
| `Uh-oh! There was an issue with the response.` | First line of the error box when the chat answer carried an error | `src/lib/components/chat/Chat.svelte:3744-3746` |
| `Error submitting message` | The error box when the stored error is empty | `src/lib/components/chat/Messages/Error.svelte:36` |

## 3. Roles and Permissions

### 3.1 Status Codes Used in Scope

The status code is not shown to the user, but the browser's developer tools (Network tab) and the
server log show it, and it narrows the search.

| Code | How the code in scope uses it | What the user usually sees |
|---|---|---|
| 400 | Invalid input, a failed save, a duplicate, and many wrapped failures (`[ERROR: …]`) | A red pop-up with the text |
| 401 | **Both** an expired or missing session **and**, in many routers, "not allowed" (for example `ACCESS_PROHIBITED` in `chats.py`, `prompts.py`, `tools.py`, `skills.py`, `models.py`) | A red pop-up; the session is ended only when the session check also fails (3.2) |
| 403 | "Not allowed", or a feature switched off (`Channels is disabled`, `OpenAI API is disabled` is 503 instead) | A red pop-up |
| 404 | The item does not exist **or** the person may not see it (`We could not find what you're looking for :/`) | A red pop-up, or an empty page |
| 409 | A chat is still generating (`Wait for the current response to finish …`), or a terminal needs a saved chat | A red pop-up |
| 413 | A file or downloaded page is larger than the size limit | A red pop-up |
| 422 | Calendar date and recurrence errors; FastAPI's own request-shape check | A red pop-up (the chats helper joins validation messages, `src/lib/apis/chats/index.ts:4-10`) |
| 500 | A provider or engine failure the code passes through, or an unexpected error | A red pop-up or an error box |
| 502 | An upstream service answered with something unusable (terminal proxy, MinerU, Datalab Marker, token counting, TTS format) | A red pop-up or warning |
| 503 | A required engine or connection is not configured or reachable (`The Ollama API is disabled. …`, slim-image messages, vector store unreachable) | A red pop-up, or an error box in chat |
| 504 | MinerU or Datalab Marker timed out | A yellow upload warning |

A single global handler turns calendar-recurrence time-outs into HTTP 400 with the error text
(`backend/open_webui/main.py:515-517`); otherwise FastAPI's default handler sends
`{"detail": ...}` with the status code given in the code.
*Corrected 2026-10-10: the global handler answers 400 only for recurrence-rule time-outs that no
router catches, for example the automation schedule checks that run after the rule validation
(`backend/open_webui/routers/automations.py:90`, `:229`; `backend/open_webui/utils/recurrence.py:16`,
`:97-103`). A time-out while saving a calendar event is a `ValueError` that the calendar router
catches and answers with HTTP 422 (`backend/open_webui/routers/calendar.py:278-279`, `:333-334`;
`backend/open_webui/models/calendar.py:186-189`).*

### 3.2 A 401 Does Not Always Sign the User Out

The browser watches every response. On a 401 from the backend it asks `/api/v1/auths/` whether the
session is still valid, and only when that check also answers 401 does it clear the session and
show `Session expired. Please sign in again.` (`src/routes/+layout.svelte:931-950`, `:952-963`,
`:1080-1090`). So a permission refusal sent as 401 (common in this scope) shows its text and leaves
the user signed in.

### 3.3 Who Sees Which Messages

| Audience | Messages they can meet |
|---|---|
| Every signed-in user | Chat, folder, file, knowledge, note, channel, memory, prompt, skill, tool, model, audio, image, automation and calendar texts in section 10; chat error boxes |
| Users with a workspace permission | Create, import and share refusals (`401 Unauthorized`, `ACCESS_PROHIBITED`) appear when the permission is missing; the permission model is in `users-groups-roles-and-permissions.md` |
| Administrators only | Document, embedding, reranking, web-search, audio and image **settings** saves (`routers/retrieval.py`, `routers/audio.py`, `routers/images.py` config endpoints), connection checks (`routers/openai.py`, `routers/ollama.py`), model import and export |
| The model (and the user, by expanding the tool call) | Tool results from `backend/open_webui/tools/` and the tool-call errors in `utils/middleware.py` (section 10.27 to 10.29) |
| Server log only | Vector store, loader, embedding and provider start-up and configuration failures (section 10.33 to 10.36) |

Admin checks themselves (`get_admin_user`, `get_verified_user`) live in `backend/open_webui/utils/auth.py`
and are catalogued in the sibling document.

## 4. Key Concepts and Terminology

| Term | Meaning in this catalogue | Evidence |
|---|---|---|
| `detail` | The field of a JSON error answer that holds the message. The code sets it with `raise HTTPException(status_code=..., detail=...)`; FastAPI sends `{"detail": ...}` | for example `backend/open_webui/routers/chats.py:693-696` |
| `ERROR_MESSAGES.<NAME>` | A shared text from `backend/open_webui/constants.py`. Four of them make up most rows in section 10: `NOT_FOUND`, `ACCESS_PROHIBITED`, `UNAUTHORIZED` and `DEFAULT` (4.1). The full table is in the sibling catalogue | `backend/open_webui/constants.py:69-79` |
| `[ERROR: …]` | A text that went through `ERROR_MESSAGES.DEFAULT(...)` with a reason; whatever follows `ERROR:` is the reason (4.2) | `backend/open_webui/constants.py:16-23` |
| `Something went wrong :/` | `ERROR_MESSAGES.DEFAULT()` with no reason, or with an exception and no fallback text. In this scope it is used both for unexpected failures **and** as a plain refusal: with HTTP 403 in channels, notes and automations, with HTTP 401 in chats and models | `backend/open_webui/constants.py:17-22`; for example `backend/open_webui/routers/automations.py:130-133` |
| `Open WebUI: Server Connection Error` | `ERROR_MESSAGES.SERVER_CONNECTION_ERROR`: a model, speech or token-count provider could not be reached or gave no usable answer. The words "Open WebUI" stay in MedIT GPT because the licence comment protects this identifier | `backend/open_webui/constants.py:127-130` |
| `External: …` | Text the provider itself returned, passed through after this prefix (OpenAI-compatible connections, speech-to-text and text-to-speech engines) | `backend/open_webui/routers/openai.py:658-662`; `backend/open_webui/routers/audio.py:349-360` |
| `{status}: {detail}` | When code turns an HTTP error into plain text with `str(e)`, the installed web framework (Starlette) writes the status code first, for example `400: [ERROR: No results found from web search]`. Tools and the document-processing step do this, so the model or the upload warning sees the number | `backend/open_webui/routers/retrieval.py:2155-2189`; `backend/open_webui/tools/builtin.py:194` |
| Tool result | What a tool hands back to the model. Built-in tools return JSON such as `{"error": "File not found"}` or text starting `Error:`; the model reads it and usually explains it in its own words | `backend/open_webui/tools/builtin.py:2497`; `backend/open_webui/tools/knowledge_fs.py:1182` |
| Error box | The grey box with an information icon under a chat response that shows `message.error.content` | `src/lib/components/chat/Messages/Error.svelte:39-48` |
| Error as document text | Mistral OCR and PaddleOCR-vl store an error sentence as the file's text instead of failing the upload, so a chat can quote it | `backend/open_webui/retrieval/loaders/mistral.py:283-293`, `:391-403`; `backend/open_webui/retrieval/loaders/paddleocr_vl.py:101-127` |
| Slim image | A smaller build without local models or some libraries; many messages that mention "slim" only occur there. Whether production uses it is TO BE CONFIRMED | `backend/open_webui/routers/retrieval.py:540`; `backend/open_webui/routers/audio.py:219` |

### 4.1 The Four Generic Texts

| Text | Constant | Typical meaning in this scope |
|---|---|---|
| `We could not find what you're looking for :/` | `NOT_FOUND` (`backend/open_webui/constants.py:78`) | The item does not exist **or** the person may not see it. In most routers a private item and a deleted item give the same answer; opening a knowledge base, model, skill or tool that exists but is not shared with the person answers `ACCESS_PROHIBITED` instead (sections 10.6, 10.8, 10.10, 10.11) |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | `ACCESS_PROHIBITED` (`backend/open_webui/constants.py:70-72`) | The person may see the item but not do this action (write, share, delete, export) or lacks a workspace permission |
| `401 Unauthorized` | `UNAUTHORIZED` (`backend/open_webui/constants.py:69`) | Despite the wording, usually "you lack the permission to create this kind of item" (notes, channels, knowledge, models, prompts, skills, tools) or a feature permission (automations, calendar) |
| `Something went wrong :/` | `DEFAULT()` (`backend/open_webui/constants.py:17-18`) | An unexpected failure, or a refusal without explanation (see the per-file rows) |

### 4.2 How `ERROR_MESSAGES.DEFAULT` Builds Its Text

`DEFAULT` is a function, not a fixed text (`backend/open_webui/constants.py:16-23`, `:41`):

| Called with | Result |
|---|---|
| nothing, or an empty value | `Something went wrong :/` |
| a text, for example `'Error creating folder'` | `[ERROR: Error creating folder]` |
| an exception and a fallback text | `[ERROR: <fallback>]`, so the exception's own words are hidden |
| an exception and no fallback | `Something went wrong :/` |
| a disk or file-system error (`OSError`) whose cause is in the list | `[ERROR: File name is too long.]`, `[ERROR: The server is out of storage space.]`, `[ERROR: Server storage quota exceeded.]` or `[ERROR: Server storage is not writable.]` instead of the fallback (`backend/open_webui/constants.py:6-13`, `:19-20`) |

So every row in section 10 written `[ERROR: <fallback>]` can also appear as one of the four
storage texts when the underlying failure was a full or read-only disk.

## 5. Workflows (Step by Step)

### 5.1 Look a Reported Message Up

1. Get the exact text from the user (a screenshot is best), plus the time, what they clicked and,
   if they can see it, the address in the browser bar.
2. Search this document for the exact text. If the text has a value in it (a file name, a model
   name, a number), search for a long fixed fragment instead; placeholders are written `{name}`.
3. If the text starts with `[ERROR: `, search for what follows. If it starts with a number and a
   colon (`400: `), drop the number and search again (section 4).
4. If several rows match (the generic texts in 4.1 appear in almost every router), choose the
   subsection from what the user was doing (table in 2.1, or the surface in 2.2).
5. Follow the row's **Support check**. Where it says `See <document>.md section 10`, that area
   document explains the trigger and the settings in depth.
6. If nothing matches, the text is probably written by the browser (front-end catalogues, areas 30
   and 31 in `_areas.md`), comes from the identity, admin or platform code (sibling catalogue), or
   is a provider's own words passed through (`External: …`, section 11.6).

### 5.2 Tell Which Layer Produced the Text

| Clue | Layer |
|---|---|
| Starts with `External: `, `Ollama: `, `HTTP Error: ` or names a provider (`Mistral`, `Azure`, `Deepgram`, `MinerU`, `Datalab Marker`, `Docling`, `Tika`) | An outside service the server called; the words after the prefix are the service's |
| `Open WebUI: Server Connection Error` | The server could not reach the provider at all |
| Starts with `[ERROR: ` or is one of the four generic texts | MedIT GPT's own server code |
| Starts with `Error:` inside an expanded tool call | A tool result written for the model (section 10.20, 10.28, 10.29) |
| Appears inside an answer as if it were document text | An extraction engine stored it as the file's text (section 11.5) |
| Shown with `Uh-oh! There was an issue with the response.` above it | The chat request carried a provider or pipeline error (2.3) |

### 5.3 What to Collect Before Escalating

- The exact text and whether it was a red pop-up, a yellow pop-up, an error box under a response, a
  status line or inside a tool call.
- The time (with time zone), the screen, and the chat, file, knowledge base, model or note name or
  link involved (never its contents).
- For a provider or engine message: which model or feature was in use.
- Tier 1 cannot read the server log; the maintainer matches the time against it. Do not ask the
  user for passwords, keys or tokens, and do not copy chat or file contents into a ticket.

## 6. Data Model

Most messages in this catalogue are answers to a request and are not stored. Four kinds of error
text are saved and can be seen again later:

| Where it is kept | What is saved | Written by | Seen again when |
|---|---|---|---|
| The file record (`file` table, `data` column) | `status` set to `failed` and `error` set to the processing failure text | `backend/open_webui/routers/files.py:256-266`; `backend/open_webui/routers/retrieval.py:2155-2165` | The file is attached again, or its processing status is checked; see `files-uploads-and-storage.md` section 6 |
| The chat message inside the saved chat | `error.content`, the text of the error box | `backend/open_webui/utils/middleware.py:4244-4253`, `:4855-4860`, `:5079-5089`, `:5227-5237` | The chat is reopened: the error box is shown again under that response |
| The automation run record (`automation_run`) | `status` `error` and the error text (cut to 4,000 characters) | `backend/open_webui/utils/automations.py:353-380`, `:448-458`, `:521-531` | The automation's run history; see `automations-calendar-and-timers.md` section 6.2 |
| A document's stored text (vector store and file content) | An extraction engine's error sentence instead of the document text | `backend/open_webui/retrieval/loaders/mistral.py:283-293`, `:391-403`; `backend/open_webui/retrieval/loaders/paddleocr_vl.py:101-127` | Any chat that retrieves from that file; see `rag-retrieval-embeddings-and-vector-stores.md` section 10 |

No table holds a list of errors; the server log is the only history of the other messages
(Logs go to standard output only, see `tools/ground-truth.md`).

## 7. Settings and Configuration

Settings decide **which** of these messages a user can meet; the live values are data held in the
`config` table or the environment and are **TO BE CONFIRMED** for production.

| Setting area | Messages it governs | Documented in |
|---|---|---|
| Upload size and allowed extensions (**Documents** admin tab) | `Oops! The file you're trying to upload is too large. …`, `[ERROR: File type {file_extension} is not allowed]` | `files-uploads-and-storage.md` section 7 |
| Content extraction engine, embedding engine, reranker, text splitter (**Documents** admin tab) | The loader, embedding and reranker rows (10.30 to 10.33) | `rag-retrieval-embeddings-and-vector-stores.md` section 7 |
| Web search provider and keys, web loader engine (**Web Search** admin tab) | `No … found in environment variables`, `[ERROR: No results found from web search]` | `web-search-and-web-loading.md` section 7 |
| OpenAI and Ollama connections and their on/off switches (**Connections** admin tab) | `OpenAI API is disabled`, `The Ollama API is disabled. …`, `Open WebUI: Server Connection Error` | `model-connections-openai-ollama-and-direct.md` section 7 |
| Speech-to-text and text-to-speech engines (**Audio** admin tab) | The audio rows (10.13) | `audio-speech-to-text-and-text-to-speech.md` section 7 |
| Image engine and size (**Images** admin tab) | The image rows (10.14) | `image-generation-and-editing.md` section 7 |
| Feature switches and user permissions (channels, notes, automations, calendar, workspace items) | `Channels is disabled`, `401 Unauthorized`, `ACCESS_PROHIBITED` refusals | `users-groups-roles-and-permissions.md` section 7 and each area document |
| Automation limits | `Automation limit reached ({max_count})`, `Schedule too frequent. …` | `automations-calendar-and-timers.md` section 7 |
| Vector store, storage provider and slim build (environment only) | The server-log rows (10.34) and the `… unavailable in slim` texts | `rag-retrieval-embeddings-and-vector-stores.md` section 7; `tools/ground-truth.md` |

## 8. Cron Jobs and Background Processes

There is no crontab. Some messages in scope are produced by work that runs without the user
waiting on the screen:

| Background work | Messages it can record | Where they surface |
|---|---|---|
| File processing after an upload (extraction, embedding) | The loader, embedding and vector-store texts (10.5, 10.7, 10.30 to 10.34) | The file record's `error`, a yellow pop-up, the `retrieval.content.process_failed` event (section 9) |
| The automations scheduler loop (`scheduler_worker_loop`) | `User not found`, `Owner no longer permitted to run automations`, `Failed to create chat`, `Channel not found`, pipeline errors (10.25) | The automation's run history; the `automation.run.failed` event |
| Chat generation tasks (title, tags, follow-ups, query and image-prompt generation) | `Query generation failed`, `Image prompt generation failed` (10.20) | A status line or error box; otherwise only the log |
| Memory background review | The memory-operation texts (10.24) | Server log; the review is not shown to the user |

Details of each loop are in `background-processes-and-scheduling.md` (area 42).

## 9. Notifications and Emails

The application sends no email. Error texts in scope travel through these in-app channels:

| Channel | Carries | Evidence |
|---|---|---|
| `chat:message:error` socket event | The text of an error box (MCP server unreachable, pipeline and provider errors) | `backend/open_webui/utils/middleware.py:3006-3012`, `:4254-4260`, `:4861-4866` |
| `chat:completion` socket event with `error` | A provider's streamed error | `backend/open_webui/utils/middleware.py:5090`, `:5193-5198`, `:5238-5245` |
| `retrieval.content.process_failed` application event | `{filename}: {e}` for a failed document processing | `backend/open_webui/routers/retrieval.py:2167-2178` |
| `automation.run.failed` application event | The automation's name and error text | `backend/open_webui/utils/automations.py:356-361`, `:372-379`, `:450-457`, `:525-531` |

How application events reach webhooks and in-app notifications is in
`notifications-webhooks-events-and-banners.md` section 9.

## 10. Error, Warning and Notice Messages (Verbatim)

How to read the table:

- **Severity.** `Error (HTTP n)` is an error answer with that status, normally shown as a red
  pop-up that prints the text (section 2.2). `Warning` is the yellow pop-up after an upload.
  `Error box` is the text under a chat response. `Tool result` is handed to the model and is
  visible when the user expands the tool call. `Status` is a status line under a response. `Log`
  means the server log only, or a start-up or configuration failure that stops a feature.
  `Internal` is an exception that the code in scope catches and replaces, so the user sees the
  replacement named in the row instead.
- **Source.** The first citation is the full path; further lines in the same file are written
  `:line`. A range is the whole `raise` statement.
- **Placeholders.** `{name}` is the source's own variable name. `[ERROR: …]` and the four storage
  variants are explained in section 4.2.
- **Already documented.** When an area document explains the message, the trigger is kept short
  and the support check reads `See <document>.md section 10`.
- **Further labels used from 10.13 on** (added 2026-10-10). **Run error** is saved on an automation's
  run record; **Code output** is shown as a code block's error output; **Text stored as the document
  (no error)** is extraction output that a chat can later quote (11.5); **Processing failure** becomes
  a file's failure text (10.7); **Start-up** stops the server and is seen in the server log only;
  **Event** is an application event, not screen text; **Never sent**, **Never shown** and **Never raised**
  mark texts the code does not deliver, with the reason in section 14.1.

### 10.1 `routers/chats.py` (Chat History, Sharing and Tags)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 401; 403 at `:235-238`) | `backend/open_webui/routers/chats.py:235-238`, `:619-622`, `:668-671`, `:684-687`, `:714-717`, `:749`, `:1052`, `:1393-1396`, `:1418-1421`, `:1424-1427`, `:1479-1482`, `:1485-1488`, `:1492-1495`, `:1527-1530`, `:1533-1536`, `:1581-1584`, `:1866-1869`, `:1953`, `:1957`, `:2001` | Import, clone or fork without the import permission (403); delete, share or change a chat or message that is not yours or without the permission; reading a share not given to you; admin-only chat lists and stats exports | Ask an admin about the permission, or the chat's owner | See `chat-conversations-history-and-organisation.md` section 10 |
| `Something went wrong :/` | Error (HTTP 400, 401 or 500) | `backend/open_webui/routers/chats.py:287`, `:409`, `:647`, `:704`, `:799`, `:828`, `:954`, `:1041`, `:1632`, `:1656`, `:1684`, `:1760`, `:1821-1824`, `:1826`, `:1898-1901`, `:1939`, `:1976`, `:1980`, `:2153`, `:2214` | 401: pin, fork, clone, archive, move or tag a chat that is not yours; 400 and 500: an unexpected failure listing, importing, cloning, forking or sharing | Retry once; escalate if it repeats | See `chat-conversations-history-and-organisation.md` section 10 |
| `We could not find what you're looking for :/` | Error (HTTP 404; 401 at `:1233`, `:1281`, `:1347`, `:1850-1853`, `:2173`, `:2248`) | `backend/open_webui/routers/chats.py:677-680`, `:782-785`, `:1233`, `:1281`, `:1347`, `:1588-1591`, `:1850-1853`, `:2042-2045`, `:2078-2081`, `:2112-2115`, `:2138-2141`, `:2173`, `:2248` | The chat, share or tag is gone or not reachable by this person; a new chat into a folder they cannot write to | Reload; ask the owner for access | See `chat-conversations-history-and-organisation.md` section 10 |
| `Your session has expired or the token is invalid. Please sign in again.` | Error (HTTP 401) | `backend/open_webui/routers/chats.py:1221-1224` | A signed-out visitor opens a share link that is not open to everyone (a signed-in visitor gets `ACCESS_PROHIBITED` from the same line) | Sign in, then open the link again | See `chat-conversations-history-and-organisation.md` section 10 |
| `Failed to process chat stats` | Error (HTTP 400) | `backend/open_webui/routers/chats.py:693-696` | One chat's statistics could not be computed for the stats export | Retry | See `chat-conversations-history-and-organisation.md` section 10 |
| `Wait for the current response to finish before compacting.` | Error (HTTP 409) | `backend/open_webui/routers/chats.py:1284-1287` | Compacting a chat while a reply is still being written | Wait for the reply, then retry | See `chat-conversations-history-and-organisation.md` section 10 |
| `No model found for context compaction.` | Error (HTTP 400) | `backend/open_webui/routers/chats.py:1305` | Compacting with no model available for the task | Pick a model and retry | See `chat-conversations-history-and-organisation.md` section 10 |
| `Wait for the current response to finish before forking.` | Error (HTTP 409) | `backend/open_webui/routers/chats.py:1687-1690` | Forking while a reply is still being written | Wait, then retry | See `chat-conversations-history-and-organisation.md` section 10 |
| `chat has no messages to fork` | Error (HTTP 400) | `backend/open_webui/routers/chats.py:1699` | Forking a chat with no current message | None | See `chat-conversations-history-and-organisation.md` section 10 |
| `{detail}`: `message not found` (HTTP 404), `message branch contains a cycle` or `chat has no messages to fork` (HTTP 400) | Error | `backend/open_webui/routers/chats.py:1703-1708`; texts in `backend/open_webui/utils/chat_fork.py:6`, `:14`, `:19` | Building the forked history failed: the chosen message or one of the earlier messages it hangs from is missing, the chat has no messages, or the stored message links loop | Fork from another message; report a cycle | See `chat-completion-pipeline-and-generation-tasks.md` section 10 (cycle); a cycle means damaged chat data: escalate with the chat link |
| `[ERROR: Tag name cannot be 'None']` | Error (HTTP 400) | `backend/open_webui/routers/chats.py:2195-2198` | Adding a tag named `none` | Choose another tag name | See `chat-conversations-history-and-organisation.md` section 10 |

### 10.2 `routers/folders.py` (Chat Folders)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 403) | `backend/open_webui/routers/folders.py:70-73`, `:80-83`, `:171-174`, `:183-186`, `:210-213`, `:369-372`, `:527-530`, `:587-590`, `:646-649`, `:691-694`, `:704-707` | Folders switched off or no folders permission; changing someone else's folder without write access; deleting a folder you do not own | Ask the folder owner or an admin | See `chat-conversations-history-and-organisation.md` section 10 |
| `[ERROR: Folder already exists]` | Error (HTTP 400) | `backend/open_webui/routers/folders.py:160-163`, `:356-359`, `:418-421` | A folder with the same name (ignoring case) already exists at that level | Pick another name | See `chat-conversations-history-and-organisation.md` section 10 |
| `We could not find what you're looking for :/` | Error (HTTP 404) | `backend/open_webui/routers/folders.py:178-181`, `:319-322`, `:344-347`, `:364-367`, `:449-452`, `:493-496`, `:519-522`, `:576-579`, `:638-641`, `:686-689`, `:749-752` | The folder is gone or not reachable | Reload the sidebar | See `chat-conversations-history-and-organisation.md` section 10 |
| `[ERROR: Error creating folder]` | Error (HTTP 400) | `backend/open_webui/routers/folders.py:200-203`, `:228-231` | Unexpected failure creating a folder | Retry | See `chat-conversations-history-and-organisation.md` section 10 |
| `[ERROR: Error updating folder]` | Error (HTTP 400) | `backend/open_webui/routers/folders.py:387-390`, `:444-447`, `:488-491` | Unexpected failure renaming, moving or saving a folder | Retry | See `chat-conversations-history-and-organisation.md` section 10 |
| `[ERROR: Cannot move a folder into itself or one of its subfolders]` | Error (HTTP 400) | `backend/open_webui/routers/folders.py:426-429` | Dragging a folder into one of its own sub-folders | Move it elsewhere | See `chat-conversations-history-and-organisation.md` section 10 |
| `[ERROR: Error deleting folder]` | Error (HTTP 400) | `backend/open_webui/routers/folders.py:739-742` | Unexpected failure deleting a folder | Do not retry blindly; some chats may already be gone | See `chat-conversations-history-and-organisation.md` section 10 |

### 10.3 `routers/channels.py` (Channels and Direct Messages)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Channels is disabled` | Error (HTTP 403) | `backend/open_webui/routers/channels.py:144-147` | The site switch for channels is off; every channel request is refused, admins included | None | See `channels-and-direct-messages.md` section 10 |
| `401 Unauthorized` | Error (HTTP 401; 403 for webhooks) | `backend/open_webui/routers/channels.py:153-156`, `:307-310`, `:1891`, `:1911`, `:1943`, `:1978` | No channels permission; a non-admin creating a standard channel; managing a channel's webhooks when not its creator or an admin | Ask an admin | See `channels-and-direct-messages.md` section 10 |
| `Something went wrong :/` | Error (HTTP 403 or 400) | `backend/open_webui/routers/channels.py:288`, `:368`, `:401`, `:435`, `:537`, `:540`, `:642`, `:659`, `:686`, `:701`, `:724`, `:746`, `:768`, `:782`, `:819`, `:822`, `:886`, `:889`, `:1144`, `:1153`, `:1160`, `:1213`, `:1270`, `:1293`, `:1296`, `:1303`, `:1334`, `:1337`, `:1344`, `:1374`, `:1378`, `:1385`, `:1424`, `:1449`, `:1452`, `:1513`, `:1517`, `:1520`, `:1525`, `:1528`, `:1560`, `:1588`, `:1597`, `:1604`, `:1638`, `:1662`, `:1671`, `:1678`, `:1713`, `:1739`, `:1743`, `:1746`, `:1755`, `:1758`, `:1810`, `:1841`, `:1844`, `:1915`, `:1951` | 403: not a member, no read or write grant, not the message author, or not the creator or an admin for member and settings changes; 400: a quoted or thread message in another channel, or an unexpected failure | Ask the channel creator; retry once for a 400 | See `channels-and-direct-messages.md` section 10 |
| `Error creating channel` | Internal (user sees `Something went wrong :/`, HTTP 400) | `backend/open_webui/routers/channels.py:285`, `:365` | Saving a new channel or direct message returned nothing; the exception is logged and replaced | Retry | Server log at that time (`log.exception`, `:287`, `:367`) |
| `We could not find what you're looking for :/` | Error (HTTP 404) | `backend/open_webui/routers/channels.py:394`, `:528`, `:602`, `:605`, `:639`, `:683`, `:721`, `:765`, `:815`, `:882`, `:1140`, `:1289`, `:1300`, `:1330`, `:1341`, `:1370`, `:1382`, `:1445`, `:1506`, `:1510`, `:1584`, `:1601`, `:1658`, `:1675`, `:1732`, `:1736`, `:1837`, `:1887`, `:1907`, `:1939`, `:1947`, `:1974`, `:1982`, `:2026` | The channel, message or webhook is gone, or the person's membership is missing | Reload | See `channels-and-direct-messages.md` section 10 |
| `Error creating message` | Internal (user sees `Something went wrong :/`, HTTP 400) | `backend/open_webui/routers/channels.py:1210` | Saving a posted message returned nothing; logged and replaced | Retry; copy the message text first | Server log at that time |
| `The URL you provided is invalid. Please double-check and try again.` | Error (HTTP 401) | `backend/open_webui/routers/channels.py:2019-2022` | An outside system posted to a webhook address that was deleted or whose secret part is wrong | Ask the channel creator for the current address | See `channels-and-direct-messages.md` section 10 |
| `[ERROR: Failed to create message]` | Error (HTTP 400) | `backend/open_webui/routers/channels.py:2037-2040` | A webhook post could not be saved | Retry | See `channels-and-direct-messages.md` section 10 |

### 10.4 `routers/notes.py` (Notes)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `401 Unauthorized` | Error (HTTP 401) | `backend/open_webui/routers/notes.py:74-77`, `:122-125`, `:163-166`, `:216-219`, `:264-267`, `:318-321`, `:408-411`, `:466-469`, `:536-539`, `:617-620`, `:675-678`, `:724-727` | A non-admin without the notes permission uses any notes action | Ask an admin about the notes permission | See `notes.md` section 10 |
| `Something went wrong :/` | Error (HTTP 403 or 400) | `backend/open_webui/routers/notes.py:242`, `:285`, `:337`, `:392`, `:427`, `:485`, `:514`, `:555`, `:594`, `:636`, `:694`, `:743`, `:756` | 403: no read access (open, side chat, pin) or no write access (save, share, delete); 400: saving, deleting or creating the side chat failed | Ask the note's owner; retry a 400 once | See `notes.md` section 10 |
| `We could not find what you're looking for :/` | Error (HTTP 404) | `backend/open_webui/routers/notes.py:271`, `:325`, `:415`, `:473`, `:543`, `:624`, `:682`, `:731` | The note does not exist (deleted, or a mistyped link) | Check the link | See `notes.md` section 10 |

### 10.5 `routers/files.py` (Uploads and the File Store)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `File type {content_type} is not supported for processing` | Warning | `backend/open_webui/routers/files.py:187` | An image or other media file uploaded with processing when the extraction engine is not set up for that type | Attach images in the chat composer instead | See `files-uploads-and-storage.md` section 10 |
| `Failed to link file {file_item.id} to knowledge {knowledge_id}` | Warning | `backend/open_webui/routers/files.py:253` | A file uploaded from a knowledge base was processed but could not be linked to it | Add the file to the knowledge base again | See `files-uploads-and-storage.md` section 10 |
| `{e.detail}` or `{e}`: the processing failure text (any row of 10.7, 10.30 or 10.32, often prefixed `400: `) | Warning | `backend/open_webui/routers/files.py:256-266` | Background processing of an upload failed; the text is stored on the file record and shown as the yellow pop-up | Read the text and use its row | Look the inner text up in this document (section 5.1, step 3) |
| `[ERROR: Invalid metadata format]` | Error (HTTP 400) | `backend/open_webui/routers/files.py:340-343` | The metadata sent with an upload is not valid JSON (scripts and integrations) | Report the tool used | See `files-uploads-and-storage.md` section 10 |
| `[ERROR: File type {file_extension} is not allowed]` | Error (HTTP 400) | `backend/open_webui/routers/files.py:359-362` | The extension is not in the allowed list (or the file has none) | Convert to an allowed type | See `files-uploads-and-storage.md` section 10 |
| `[ERROR: {e.strerror}]` (falls back to `[ERROR: Error uploading file]`) | Error (HTTP 400) | `backend/open_webui/routers/files.py:379-382`, `:390-393` | The server's storage refused the write; the reason is the operating system's own words, for example `No space left on device` | Try later | See `files-uploads-and-storage.md` section 10; escalate as a storage incident |
| `Oops! The file you're trying to upload is too large. Please upload a file that is less than {max_size} MB.` | Error (HTTP 413) | `backend/open_webui/routers/files.py:397-400`, `:737-740` | Above the maximum upload size (upload, or replacing a file's text) | Use a smaller file or split it | See `files-uploads-and-storage.md` section 10 |
| `[ERROR: Error uploading file]` | Error (HTTP 400) | `backend/open_webui/routers/files.py:462-465`, `:471-478` | The file record could not be created, or another unexpected upload failure | Retry | See `files-uploads-and-storage.md` section 10 |
| `The content provided is empty. Please ensure that there is text or data present before proceeding.` | Error (HTTP 400) | `backend/open_webui/routers/files.py:471-478` | A zero-byte file reached the server (the storage layer refuses it) | Check the file | See `files-uploads-and-storage.md` section 10 |
| `No files found matching the pattern.` | Error (HTTP 404) | `backend/open_webui/routers/files.py:543-546` | A file search found nothing (the Files manager shows its own text) | None | See `files-uploads-and-storage.md` section 10 |
| `[ERROR: Error deleting files]` | Error (HTTP 400) | `backend/open_webui/routers/files.py:587-590`, `:594-597`, `:1047-1050` | Delete-all failed, or a deleted file's stored bytes or search entries could not be removed | None; the record may already be gone | See `files-uploads-and-storage.md` section 10 |
| `We could not find what you're looking for :/` | Error (HTTP 404) | `backend/open_webui/routers/files.py:610-613`, `:618-621`, `:637-640`, `:677-680`, `:695-698`, `:703-706`, `:729-732`, `:784-787`, `:805-808`, `:838-841`, `:852-855`, `:865-868`, `:872-875`, `:887-890`, `:901-904`, `:914-917`, `:935-938`, `:954-957`, `:980-983`, `:1002-1005`, `:1020-1023`, `:1065-1068` | The file does not exist, the person may not read or change it, or its stored bytes are gone | Ask the owner to share it through a knowledge base, channel or shared chat | See `files-uploads-and-storage.md` section 10 |
| `[ERROR: Error getting file content]` | Error (HTTP 400) | `backend/open_webui/routers/files.py:847-850`, `:896-899` | Reading the stored bytes failed | Retry | See `files-uploads-and-storage.md` section 10 |
| `[ERROR: Error renaming file]` | Error (HTTP 400) | `backend/open_webui/routers/files.py:997-1000` | The new name could not be saved | Retry | See `files-uploads-and-storage.md` section 10 |
| `[ERROR: Error deleting file]` | Error (HTTP 400) | `backend/open_webui/routers/files.py:1060-1063` | The file record could not be deleted | Retry | See `files-uploads-and-storage.md` section 10 |

### 10.6 `routers/knowledge.py` (Knowledge Bases)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `External knowledge bases are read-only.` | Error (HTTP 400) | `backend/open_webui/routers/knowledge.py:148-151` | Changing files, directories or the index of a knowledge base connected to an outside source | None | See `knowledge-bases.md` section 10 |
| `Target directory not found.` / `Parent directory not found.` | Error (HTTP 404) | `backend/open_webui/routers/knowledge.py:166-169`, called at `:1458`, `:2073`, `:2263`, `:2301`, `:2393` | The chosen directory was deleted or belongs to another knowledge base | Reload and choose again | See `knowledge-bases.md` section 10 |
| `401 Unauthorized` | Error (HTTP 401) | `backend/open_webui/routers/knowledge.py:331-334`, `:381-384` | Creating a knowledge base without the knowledge permission; a non-admin starting a full reindex | Ask an admin | See `knowledge-bases.md` section 10 |
| `Uh-oh! This file is already registered. Please choose another file.` | Error (HTTP 400) | `backend/open_webui/routers/knowledge.py:363-366`, `:926`, `:991` | The new knowledge base could not be written to the database (the wording about files is misleading) | Retry | See `knowledge-bases.md` section 10 |
| `{e}`: the processing failure with its status code, for example `400: Duplicate content detected. Please provide unique content to proceed.` | Error (HTTP 400) | `backend/open_webui/routers/knowledge.py:1499-1502`, `:1583-1586`, `:2125` | Indexing failed while adding, updating or batch-adding a file | Read the inner text and use its row (10.7) | See `knowledge-bases.md` section 10 |
| `{e}` (per file, reindex) | Log | `backend/open_webui/routers/knowledge.py:438-451` | A file failed during an admin's full reindex; recorded only as log warnings | None | Server log lines `File ID: {…}, Error: {…}` |
| `Unsupported external knowledge provider.` | Error (HTTP 400) | `backend/open_webui/routers/knowledge.py:566-569` | Admin connection form names a provider the code does not support | Admin: choose a supported provider | See `knowledge-bases.md` section 10 |
| `Knowledge source name is required.` | Error (HTTP 400) | `backend/open_webui/routers/knowledge.py:572` | Admin connection form without a name | Fill it in | See `knowledge-bases.md` section 10 |
| `Knowledge source endpoint is required.` | Error (HTTP 400) | `backend/open_webui/routers/knowledge.py:575` | Admin connection form without an endpoint | Fill it in | See `knowledge-bases.md` section 10 |
| `Only collection sources are supported.` | Error (HTTP 400) | `backend/open_webui/routers/knowledge.py:596` | Admin source of a kind other than a collection | Use a collection | See `knowledge-bases.md` section 10 |
| `Collection name is required.` | Error (HTTP 400) | `backend/open_webui/routers/knowledge.py:598` | Admin source without a collection name | Fill it in | See `knowledge-bases.md` section 10 |
| `Content field is required.` | Error (HTTP 400) | `backend/open_webui/routers/knowledge.py:614` | Admin source without a content field | Fill it in | See `knowledge-bases.md` section 10 |
| `Vector field is required.` | Error (HTTP 400) | `backend/open_webui/routers/knowledge.py:616` | Admin source without a vector field | Fill it in | See `knowledge-bases.md` section 10 |
| `We could not find what you're looking for :/` | Error (HTTP 404 or 400) | `backend/open_webui/routers/knowledge.py:725`, `:739`, `:764`, `:791`, `:888`, `:903`, `:1019`, `:1135-1138`, `:1159-1162`, `:1234-1237`, `:1307-1310`, `:1367-1370`, `:1435-1438`, `:1462-1465`, `:1518-1521`, `:1534-1537`, `:1559-1562`, `:1566-1569`, `:1602-1605`, `:1624-1627`, `:1649-1652`, `:1656-1659`, `:1691-1694`, `:1711-1714`, `:1802-1805`, `:2049-2052`, `:2171-2174`, `:2229-2232`, `:2388-2391` | The knowledge base, file, connection or directory is gone or not reachable | Reload; ask the owner | See `knowledge-bases.md` section 10 |
| `External connection is still used by knowledge bases.` | Error (HTTP 400) | `backend/open_webui/routers/knowledge.py:767-770` | Admin deleting a connection that knowledge bases still use | Remove those first | See `knowledge-bases.md` section 10 |
| `Test query is required.` | Error (HTTP 400) | `backend/open_webui/routers/knowledge.py:817` | Admin testing a source without a test query | Enter one | See `knowledge-bases.md` section 10 |
| `External connection not found.` | Error (HTTP 404) | `backend/open_webui/routers/knowledge.py:864`, `:1027` | The saved connection was removed | Reload | See `knowledge-bases.md` section 10 |
| `Knowledge name is required.` | Error (HTTP 400) | `backend/open_webui/routers/knowledge.py:905`, `:952`, `:1021` | Admin left a connected knowledge base's name blank | Fill it in | See `knowledge-bases.md` section 10 |
| `Test query returned no results.` | Error (HTTP 400) | `backend/open_webui/routers/knowledge.py:965`, `:1041` | Admin's test query found nothing in the source | Check the collection and fields | See `knowledge-bases.md` section 10 |
| `Something went wrong :/` | Error (HTTP 400) | `backend/open_webui/routers/knowledge.py:1066`, `:1083` | Saving an edited connected source failed | Retry | See `knowledge-bases.md` section 10 |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 401, 403 or 400) | `backend/open_webui/routers/knowledge.py:1130-1133`, `:1174-1177`, `:1250-1253`, `:1322-1325`, `:1383-1386`, `:1453-1456`, `:1475-1478`, `:1552-1555`, `:1642-1645`, `:1727-1730`, `:1820-1823`, `:2067-2070`, `:2093-2096`, `:2246-2249` | Opening a knowledge base not shared with you (401); changing one without write access; adding a file you cannot read (403) | Ask the owner for access | See `knowledge-bases.md` section 10 |
| `Uh-oh! This id is already registered. Please choose another id string.` | Error (HTTP 400) | `backend/open_webui/routers/knowledge.py:1209-1212` | Saving a name or description failed in the database (misleading wording) | Retry | See `knowledge-bases.md` section 10 |
| `Extracted content is not available for this file. Please ensure that the file is processed before proceeding.` | Error (HTTP 400) | `backend/open_webui/routers/knowledge.py:1467-1470` | Adding an existing file that has no extracted text | Upload the file again | See `knowledge-bases.md` section 10 |
| `File {missing_ids[0]} not found` | Error (HTTP 400) | `backend/open_webui/routers/knowledge.py:2084-2087` | A batch add (API) named a file that does not exist | Check the file ids | See `knowledge-bases.md` section 10 |
| `Some files failed to process` | Warning field (not shown) | `backend/open_webui/routers/knowledge.py:2139-2149` | A batch add with failures; the per-file texts are `{file_id}: {error}` | None | See `knowledge-bases.md` section 10 |
| `Failed to create directory. A directory with this name may already exist at this level.` | Error (HTTP 400) | `backend/open_webui/routers/knowledge.py:2273-2276` | Same directory name already used at that level, or a database error | Pick another name | See `knowledge-bases.md` section 10 |
| `Failed to update directory. This may be caused by a naming conflict or circular move.` | Error (HTTP 400) | `backend/open_webui/routers/knowledge.py:2310-2313` | Rename to a taken name, or a move into the directory's own sub-tree | Choose another name or place | See `knowledge-bases.md` section 10 |
| `Failed to delete directory.` | Error (HTTP 500) | `backend/open_webui/routers/knowledge.py:2345-2348` | The directory could not be removed | Retry | See `knowledge-bases.md` section 10 |
| `Failed to move file.` | Error (HTTP 500) | `backend/open_webui/routers/knowledge.py:2402-2405` | The move could not be saved | Retry | See `knowledge-bases.md` section 10 |

### 10.7 `routers/retrieval.py` (Document Processing, Search Settings and Web Search)

Engine texts below marked "Tool result or internal" reach the model when the built-in
`search_web` tool runs (it returns `{"error": "<text>"}`, `backend/open_webui/tools/builtin.py:319-330`);
in the classic web-search path the same failure is replaced by
`[ERROR: Something went wrong while searching the web.]` (`backend/open_webui/routers/retrieval.py:2946-2951`).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `[ERROR: Error loading reranking model]` | Internal (log) | `backend/open_webui/routers/retrieval.py:206` | The ColBERT reranker could not be loaded at start-up or after an admin save; the save then logs `Error loading reranking model: {e}` and switches hybrid search off (`:1251-1253`); at start-up the log reads `Error updating models: {e}` (`backend/open_webui/main.py:695-697`) | None | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `[ERROR: CrossEncoder error]` | Internal (log) | `backend/open_webui/routers/retrieval.py:224` | As above for a sentence-transformers reranker | None | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Slim requires an external embedding engine (openai, ollama, azure_openai).` | Error (HTTP 400), admin | `backend/open_webui/routers/retrieval.py:540` | Slim image, local embedding engine chosen | Admin: choose an external engine | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `[ERROR: Error updating embedding configuration]` | Error (HTTP 500), admin | `backend/open_webui/routers/retrieval.py:623-626` | Saving or loading the new embedding settings failed | Admin: check the engine and key | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `DDGS is unavailable in slim. Configure another web search provider in Admin Settings > Web Search.` | Error (HTTP 400), admin | `backend/open_webui/routers/retrieval.py:972-975` | Slim image, DuckDuckGo (DDGS) chosen as the search engine | Admin: choose another engine | See `web-search-and-web-loading.md` section 10 |
| `Playwright is unavailable in slim. Use basic HTTP fetching or an external web loader.` | Error (HTTP 400), admin | `backend/open_webui/routers/retrieval.py:981-983` | Slim image, Playwright chosen as the web loader | Admin: choose another loader | See `web-search-and-web-loading.md` section 10 |
| `Transformers tokenization is unavailable in slim. Use character or token splitting.` | Error (HTTP 400 on save; 503 while processing) | `backend/open_webui/routers/retrieval.py:985-987`, `:1651` | Slim image with the Token (Transformers) text splitter | Admin: choose another splitter | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Slim requires an external reranker, or an empty reranking model for cosine scoring.` | Error (HTTP 400), admin | `backend/open_webui/routers/retrieval.py:1001-1003` | Slim image, local reranker chosen | Admin: use an external reranker or clear the model | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `[ERROR: Error updating reranking configuration]` | Error (HTTP 500), admin | `backend/open_webui/routers/retrieval.py:1256-1259` | An unexpected failure while storing the reranking settings | Admin: retry | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Tokenizer model required for Token (Transformers) text splitter` | Warning (upload) | `backend/open_webui/routers/retrieval.py:1679` | Token (Transformers) splitter with no tokenizer model and no local embedding model to borrow one from | Report it | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Duplicate content detected. Please provide unique content to proceed.` | Warning (upload) or Error (HTTP 400) | `backend/open_webui/routers/retrieval.py:1753` | The same extracted text is already in that collection from another file | Use the existing copy | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `[ERROR: Invalid text splitter]` | Warning (upload) | `backend/open_webui/routers/retrieval.py:1817` | The stored text splitter value is not one the code knows | Report it | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `The content provided is empty. Please ensure that there is text or data present before proceeding.` | Warning (upload) or Error (HTTP 400) | `backend/open_webui/routers/retrieval.py:1820`, `:2015` | Extraction produced no text (for example a scanned PDF with text recognition off) | Provide a text-based version | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Error saving document to vector database` | Warning (upload) | `backend/open_webui/routers/retrieval.py:2151` | The vector store did not report success | Retry later | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `{e}`: any processing failure, prefixed with its status code when it came from an engine (for example `504: MinerU processing timed out after 10 minutes`) | Warning (upload) or Error (HTTP 400) | `backend/open_webui/routers/retrieval.py:2155-2189` | Extraction or embedding failed; the text is stored on the file, published as an event and returned | Use the inner text's row | Search for the inner text (section 5.1, step 3) |
| `Pandoc is not installed on the server. Please contact your administrator for assistance.` | Error (HTTP 400) | `backend/open_webui/routers/retrieval.py:2181-2184` | A loader needed the pandoc program and it is missing | None | See `rag-retrieval-embeddings-and-vector-stores.md` section 10; escalate to the maintainer |
| `We could not find what you're looking for :/` | Error (HTTP 404) | `backend/open_webui/routers/retrieval.py:2192`, `:3222-3225` | The file to process or the entry to delete does not exist or is not the requester's | Reload | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Something went wrong :/` | Error (HTTP 500) | `backend/open_webui/routers/retrieval.py:2239-2242` | Pasted text could not be saved for retrieval | Retry | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Oops! The file you're trying to upload is too large. Please upload a file that is less than {max_size_mb} MB.` | Error (HTTP 413) | `backend/open_webui/routers/retrieval.py:2286-2289`, `:2297-2300`, `:2308-2311` | A linked file or web page is larger than the upload limit | Download and upload a smaller copy | See `web-search-and-web-loading.md` section 10 |
| `[ERROR: Invalid image content]` | Error (HTTP 400) | `backend/open_webui/routers/retrieval.py:2326-2329` | The address claims to be an image but is not a valid one | Check the link | See `web-search-and-web-loading.md` section 10 |
| `[ERROR: Error processing URL]` | Error (HTTP 400) | `backend/open_webui/routers/retrieval.py:2423-2426` | The address was refused by the address checks, could not be reached or returned an error | Check the address | See `web-search-and-web-loading.md` section 10 |
| `{e}`: a YouTube transcript text (10.32) | Error (HTTP 400) | `backend/open_webui/routers/retrieval.py:2446-2449` | Adding a YouTube link whose transcript could not be fetched | Use another video or paste the text | See `web-search-and-web-loading.md` section 10 |
| `[ERROR: Could not read content from {form_data.url}]` | Error (HTTP 400) | `backend/open_webui/routers/retrieval.py:2452-2455` | The web loader (or file extraction for a linked file) failed | Retry, or attach the page as a file | See `web-search-and-web-loading.md` section 10 |
| `[ERROR: Error querying knowledge base]` | Error (HTTP 400) | `backend/open_webui/routers/retrieval.py:2505-2508`, `:3125-3128`, `:3193-3196` | Storing a loaded page failed, or a search of documents or collections failed | Retry | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `No PERPLEXITY_API_KEY found in environment variables` | Tool result or internal | `backend/open_webui/routers/retrieval.py:2542` | The chosen search engine needs this key and it is empty | None | See `web-search-and-web-loading.md` section 10 |
| `No SEARXNG_QUERY_URL found in environment variables` | Tool result or internal | `backend/open_webui/routers/retrieval.py:2554` | As above (address) | None | See `web-search-and-web-loading.md` section 10 |
| `No OPENSERP_BASE_URL found in environment variables` | Tool result or internal | `backend/open_webui/routers/retrieval.py:2564` | As above (address) | None | See `web-search-and-web-loading.md` section 10 |
| `No YACY_QUERY_URL found in environment variables` | Tool result or internal | `backend/open_webui/routers/retrieval.py:2577` | As above (address) | None | See `web-search-and-web-loading.md` section 10 |
| `No GOOGLE_PSE_API_KEY or GOOGLE_PSE_ENGINE_ID found in environment variables` | Tool result or internal | `backend/open_webui/routers/retrieval.py:2589` | As above (either value missing) | None | See `web-search-and-web-loading.md` section 10 |
| `No BRAVE_SEARCH_API_KEY found in environment variables` | Tool result or internal | `backend/open_webui/routers/retrieval.py:2599`, `:2611` | As above (two Brave engines) | None | See `web-search-and-web-loading.md` section 10 |
| `No KAGI_SEARCH_API_KEY found in environment variables` | Tool result or internal | `backend/open_webui/routers/retrieval.py:2622` | As above | None | See `web-search-and-web-loading.md` section 10 |
| `No MOJEEK_SEARCH_API_KEY found in environment variables` | Tool result or internal | `backend/open_webui/routers/retrieval.py:2633` | As above | None | See `web-search-and-web-loading.md` section 10 |
| `No BOCHA_SEARCH_API_KEY found in environment variables` | Tool result or internal | `backend/open_webui/routers/retrieval.py:2644` | As above | None | See `web-search-and-web-loading.md` section 10 |
| `No SERPSTACK_API_KEY found in environment variables` | Tool result or internal | `backend/open_webui/routers/retrieval.py:2655` | As above | None | See `web-search-and-web-loading.md` section 10 |
| `No SERPER_API_KEY found in environment variables` | Tool result or internal | `backend/open_webui/routers/retrieval.py:2665` | As above | None | See `web-search-and-web-loading.md` section 10 |
| `No SERPHOUSE_API_KEY found in environment variables` | Tool result or internal | `backend/open_webui/routers/retrieval.py:2676` | As above | None | See `web-search-and-web-loading.md` section 10 |
| `No SERPLY_API_KEY found in environment variables` | Tool result or internal | `backend/open_webui/routers/retrieval.py:2687` | As above | None | See `web-search-and-web-loading.md` section 10 |
| `No TAVILY_API_KEY found in environment variables` | Tool result or internal | `backend/open_webui/routers/retrieval.py:2707` | As above | None | See `web-search-and-web-loading.md` section 10 |
| `No STAAN_API_KEY found in environment variables` | Tool result or internal | `backend/open_webui/routers/retrieval.py:2720` | As above | None | See `web-search-and-web-loading.md` section 10 |
| `No EXA_API_KEY found in environment variables` | Tool result or internal | `backend/open_webui/routers/retrieval.py:2732` | As above | None | See `web-search-and-web-loading.md` section 10 |
| `No SEARCHAPI_API_KEY found in environment variables` | Tool result or internal | `backend/open_webui/routers/retrieval.py:2744` | As above | None | See `web-search-and-web-loading.md` section 10 |
| `No SERPAPI_API_KEY found in environment variables` | Tool result or internal | `backend/open_webui/routers/retrieval.py:2756` | As above | None | See `web-search-and-web-loading.md` section 10 |
| `AZURE_AI_SEARCH_API_KEY, AZURE_AI_SEARCH_ENDPOINT, and AZURE_AI_SEARCH_INDEX_NAME are required for Azure AI Search` | Tool result or internal | `backend/open_webui/routers/retrieval.py:2787-2789` | Azure AI Search chosen with any of the three values missing | None | See `web-search-and-web-loading.md` section 10 |
| `No MICROSOFT_WEB_IQ_API_KEY found in environment variables` | Tool result or internal | `backend/open_webui/routers/retrieval.py:2813` | As above | None | See `web-search-and-web-loading.md` section 10 |
| `No SOUGOU_API_SID or SOUGOU_API_SK found in environment variables` | Tool result or internal | `backend/open_webui/routers/retrieval.py:2825` | As above (either value missing) | None | See `web-search-and-web-loading.md` section 10 |
| `No LINKUP_API_KEY found in environment variables` | Tool result or internal | `backend/open_webui/routers/retrieval.py:2877` | As above | None | See `web-search-and-web-loading.md` section 10 |
| `No search engine API key found in environment variables` | Tool result or internal | `backend/open_webui/routers/retrieval.py:2879` | No search engine is chosen, or the stored value is not a known engine | None | See `web-search-and-web-loading.md` section 10 |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 403); a status line in chat | `backend/open_webui/routers/retrieval.py:2886-2889`, `:2892-2895`, `:3060-3063` | Web search off site-wide or the web-search permission missing; writing to or searching a collection the person cannot access | Ask an admin | See `web-search-and-web-loading.md` and `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `[ERROR: Something went wrong while searching the web.]` | Error (HTTP 400); a status line in chat | `backend/open_webui/routers/retrieval.py:2948-2951`, `:3044-3047` | Any search-engine failure (missing key, refused request, network) or a page-loading failure | Retry later | See `web-search-and-web-loading.md` section 10 |
| `[ERROR: No results found from web search]` | Error (HTTP 404); a status line in chat | `backend/open_webui/routers/retrieval.py:2954-2957` | The engine returned no usable links for any query | Rephrase | See `web-search-and-web-loading.md` section 10 |
| `Failed to embed and store the retrieved web pages. Check the embedding configuration in Admin Settings > Documents.` | Error (HTTP 500); a status line in chat | `backend/open_webui/routers/retrieval.py:3028-3031` | Saving the loaded pages to the vector store failed, including when every page was empty | Retry; report if it repeats | See `web-search-and-web-loading.md` section 10 |
| `[ERROR: File has no hash; cannot delete vector entries by hash.]` | Error (HTTP 400) | `backend/open_webui/routers/retrieval.py:3236-3239` | Deleting search entries for a file that never processed successfully | None | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `File not found` | Per-file result of a batch | `backend/open_webui/routers/retrieval.py:3381` | Batch processing named a file that does not exist | None | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Permission denied: not file owner` | Per-file result of a batch | `backend/open_webui/routers/retrieval.py:3390` | Batch processing named another person's file (non-admin) | None | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |

### 10.8 `routers/models.py` (Workspace Models)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Background image is not accessible.` | Error (HTTP 403) | `backend/open_webui/routers/models.py:113` | The model's background image file is missing or the person cannot read it | Choose another image | See `workspace-models-and-model-access.md` section 10 |
| `{error}`: a background-image check, for example `Background image must be at most 5 MiB.`, `Background image must be PNG, JPEG, WebP, or GIF.`, `Background image must be at most 25 megapixels.`, `Invalid background image.` or `Invalid background image data URI.` | Error (HTTP 400) | `backend/open_webui/routers/models.py:120`, `:670`; texts in `backend/open_webui/utils/validate.py:106-119` and `backend/open_webui/routers/models.py:613`, `:618` | Saving or importing a model whose background image fails the size, format or encoding checks | Use a PNG, JPEG, WebP or GIF under 5 MiB and 25 megapixels | See `workspace-models-and-model-access.md` section 10 |
| `Could not validate background image.` | Error (HTTP 500) | `backend/open_webui/routers/models.py:123` | The image's recorded type could not be corrected | Retry | See `workspace-models-and-model-access.md` section 10 |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 403, 401 or 400) | `backend/open_webui/routers/models.py:146-149`, `:406`, `:759-762`, `:958-961`, `:1048-1051`, `:1079-1082` | A knowledge file the person cannot read (403); exporting models they may not write (403); opening a model without read access (401); saving or re-sharing without write access (400) | Ask the model's owner | See `workspace-models-and-model-access.md` section 10 |
| `401 Unauthorized` | Error (HTTP 401) | `backend/open_webui/routers/models.py:296-299`, `:319-322`, `:394-397`, `:454-457`, `:916-919`, `:976-979`, `:1136-1139` | Creating, importing or exporting without the models permission; switching, saving or deleting without write access | Ask an admin | See `workspace-models-and-model-access.md` section 10 |
| `The model id is too long. Please make sure your model id is less than 256 characters long.` | Error (HTTP 400) | `backend/open_webui/routers/models.py:302-305` | A model id longer than 256 characters | Shorten it | See `workspace-models-and-model-access.md` section 10 |
| `Uh-oh! This model id is already registered. Please choose another model id string.` | Error (HTTP 401) | `backend/open_webui/routers/models.py:312-315`, `:334-337` | Another model record already uses the id (including ones the person cannot see), or a non-admin reused a provider model's id | Choose another id | See `workspace-models-and-model-access.md` section 10 |
| `Something went wrong :/` | Error (HTTP 401) | `backend/open_webui/routers/models.py:357-360` | The new model could not be written | Retry | See `workspace-models-and-model-access.md` section 10 |
| `Image file is missing` | Internal (user sees `Could not export background for model {model.id}.`) | `backend/open_webui/routers/models.py:415` | Export: the background image's file record is gone | Remove or replace the background, then export | Same as the next row |
| `Could not export background for model {model.id}.` | Error (HTTP 400) | `backend/open_webui/routers/models.py:425-427` | Export: a model's background image is missing or invalid | Fix that model's background | See `workspace-models-and-model-access.md` section 10 |
| `Could not import model {model_id}.` | Error (HTTP 500) | `backend/open_webui/routers/models.py:646` | Import: one model could not be written; earlier ones were imported | Check which models arrived | See `workspace-models-and-model-access.md` section 10 |
| `Invalid JSON format` | Error (HTTP 400) | `backend/open_webui/routers/models.py:666` | The import body is not a list | Use an exported file | See `workspace-models-and-model-access.md` section 10 |
| `{e}` | Error (HTTP 500) | `backend/open_webui/routers/models.py:671-673` | Any other unexpected import failure; the exception's own words are passed through | Report the text | Server log at that time |
| `We could not find what you're looking for :/` | Error (HTTP 404; 401 when switching, saving or deleting) | `backend/open_webui/routers/models.py:764-767`, `:921-924`, `:942-945`, `:1120-1123` | The model no longer exists | Reload | See `workspace-models-and-model-access.md` section 10 |
| `[ERROR: Error updating function]` | Error (HTTP 400) | `backend/open_webui/routers/models.py:911-914` | The model's on/off switch could not be saved (the text says "function") | Retry | See `workspace-models-and-model-access.md` section 10 |
| `[ERROR: Error creating model entry]` | Error (HTTP 500) | `backend/open_webui/routers/models.py:1063-1066` | An admin changed access on a provider model and its record could not be created | Retry | See `workspace-models-and-model-access.md` section 10 |

### 10.9 `routers/prompts.py` (Prompts)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `401 Unauthorized` | Error (HTTP 401) | `backend/open_webui/routers/prompts.py:164-167` | Creating, importing or cloning a prompt without the prompts or import permission | Ask an admin | See `prompts-and-skills.md` section 10 |
| `Something went wrong :/` | Error (HTTP 400) | `backend/open_webui/routers/prompts.py:190-193`, `:312-315`, `:378-381`, `:426-429`, `:540-543` | The database refused a save, or the chosen version does not belong to the prompt | Retry | See `prompts-and-skills.md` section 10 |
| `Uh-oh! This command is already registered. Please choose another command string.` | Error (HTTP 400) | `backend/open_webui/routers/prompts.py:194-197`, `:287-290`, `:360-363` | Another prompt anywhere on the site already uses that command | Choose another command | See `prompts-and-skills.md` section 10 |
| `We could not find what you're looking for :/` | Error (HTTP 404) | `backend/open_webui/routers/prompts.py:238-241`, `:261-264`, `:335-338`, `:394-397`, `:451-454`, `:508-511`, `:561-564`, `:612-615`, `:649-652`, `:673-676`, `:692-695`, `:723-726`, `:743-746`, `:767-770` | The prompt or version is gone, or (when opening) the person cannot read it | Reload | See `prompts-and-skills.md` section 10 |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 401) | `backend/open_webui/routers/prompts.py:278-281`, `:351-354`, `:410-413`, `:467-470`, `:524-527`, `:577-580`, `:629-632`, `:666-669`, `:709-712`, `:760-763` | Saving, renaming, restoring, sharing, switching or deleting without write access; reading history without read access | Ask the owner | See `prompts-and-skills.md` section 10 |
| `Cannot delete the active production version` | Error (HTTP 400) | `backend/open_webui/routers/prompts.py:716-719` | Deleting the live version | Make another version live first | See `prompts-and-skills.md` section 10 |

### 10.10 `routers/skills.py` (Skills)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `401 Unauthorized` | Error (HTTP 401) | `backend/open_webui/routers/skills.py:135-138`, `:162-165`, `:300-303`, `:383-386`, `:451-454`, `:492-495` | Exporting, creating, importing or cloning without the permission; saving, sharing, switching or deleting without write access | Ask an admin or the owner | See `prompts-and-skills.md` section 10 |
| `[ERROR: Invalid skill ID]` | Error (HTTP 400) | `backend/open_webui/routers/skills.py:171-174` | The id has characters other than `a-z`, `0-9`, `-` and `_` (usually from an import) | Fix the id | See `prompts-and-skills.md` section 10 |
| `Uh-oh! This id is already registered. Please choose another id string.` | Error (HTTP 400) | `backend/open_webui/routers/skills.py:178-181` | Another skill already has the id | Choose another id | See `prompts-and-skills.md` section 10 |
| `[ERROR: Error creating skill]` | Error (HTTP 400) | `backend/open_webui/routers/skills.py:208-211`, `:216-219` | The database refused the new skill, usually a name another skill already has | Choose another name | See `prompts-and-skills.md` section 10 |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 401) | `backend/open_webui/routers/skills.py:258-261` | Opening a skill the person cannot read | Ask the owner | See `prompts-and-skills.md` section 10 |
| `We could not find what you're looking for :/` | Error (HTTP 404) | `backend/open_webui/routers/skills.py:263-266`, `:284-287`, `:367-370`, `:456-459`, `:476-479` | The skill no longer exists | Reload | See `prompts-and-skills.md` section 10 |
| `[ERROR: Error updating skill]` | Error (HTTP 400) | `backend/open_webui/routers/skills.py:335-338`, `:342-345` | The save was refused, usually a rename to a taken name | Choose another name | See `prompts-and-skills.md` section 10 |
| `[ERROR: Error toggling skill]` | Error (HTTP 400) | `backend/open_webui/routers/skills.py:446-449` | The on/off switch could not be saved | Retry | See `prompts-and-skills.md` section 10 |

### 10.11 `routers/tools.py` (Workspace Tools)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Please enter a valid URL` | Error (HTTP 400) | `backend/open_webui/routers/tools.py:272` | Importing a tool from an empty or malformed address | Check the address | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Failed to fetch the tool` | Error (the remote server's status) | `backend/open_webui/routers/tools.py:294` | The address answered with an error | Check the address | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `No data received from the URL` | Error (HTTP 400) | `backend/open_webui/routers/tools.py:297` | The address answered with nothing | Check the address | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `[ERROR: Error fetching tool]` | Error (HTTP 500) | `backend/open_webui/routers/tools.py:305-308` | Any other failure loading a tool from an address | Retry | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `401 Unauthorized` | Error (HTTP 401) | `backend/open_webui/routers/tools.py:328-331`, `:363-366`, `:512-515`, `:523-526`, `:614-617`, `:670-673` | Missing the tools permission or write access for that action | Ask an admin or the owner | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Only alphanumeric characters and underscores are allowed in the id` | Error (HTTP 400) | `backend/open_webui/routers/tools.py:369-372` | A tool id with other characters | Fix the id | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `[ERROR: Error creating tools]` | Error (HTTP 400) | `backend/open_webui/routers/tools.py:411-414` | The new tool could not be saved | Retry | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `[ERROR: Error creating tool]` | Error (HTTP 400) | `backend/open_webui/routers/tools.py:419-422` | The tool's code failed to load while creating it | Check the code | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Uh-oh! This id is already registered. Please choose another id string.` | Error (HTTP 400) | `backend/open_webui/routers/tools.py:424-427` | Another tool already uses the id | Choose another id | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 401 or 400) | `backend/open_webui/routers/tools.py:468-471`, `:719-722`, `:764-767`, `:811-814`, `:872-875`, `:912-915`, `:954-957` | Opening a tool or its settings (valves) without the needed access | Ask the owner | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `We could not find what you're looking for :/` | Error (HTTP 404 or 401) | `backend/open_webui/routers/tools.py:473-476`, `:495-498`, `:598-601`, `:654-657`, `:703-706`, `:748-751`, `:795-798`, `:819-822`, `:856-859`, `:896-899`, `:938-941`, `:984-987` | The tool is gone, or settings were saved for a tool that declares none | Reload | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `[ERROR: Error updating tools]` | Error (HTTP 400) | `backend/open_webui/routers/tools.py:565-568` | The tool could not be saved | Retry | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `[ERROR: Error updating tool]` | Error (HTTP 400) | `backend/open_webui/routers/tools.py:573-576` | The edited code failed to load | Check the code | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `[ERROR: Error getting tool valves]` | Error (HTTP 400) | `backend/open_webui/routers/tools.py:728-731` | The tool's settings could not be read | Retry | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `[ERROR: Error updating tool valves]` | Error (HTTP 400) | `backend/open_webui/routers/tools.py:839-842` | The tool's settings could not be saved (often a value of the wrong type) | Check the values | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `[ERROR: Error getting tool user valves]` | Error (HTTP 400) | `backend/open_webui/routers/tools.py:881-884` | The person's own tool settings could not be read | Retry | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `[ERROR: Error updating tool user valves]` | Error (HTTP 400) | `backend/open_webui/routers/tools.py:979-982` | The person's own tool settings could not be saved | Check the values | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |

### 10.12 `routers/memories.py` (Memories)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `We could not find what you're looking for :/` | Error (HTTP 404) | `backend/open_webui/routers/memories.py:38-41`, `:575` | Memories switched off site-wide while the page was open; updating a memory that is gone or not the person's | Reload | See `memories.md` section 10 |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 403) | `backend/open_webui/routers/memories.py:44-47` | A non-admin without the memories permission | Ask an admin | See `memories.md` section 10 |
| `{e}`: `Memory not found: {memory_id}` or `Unsupported memory operation: {action}` | Error (HTTP 404) | `backend/open_webui/routers/memories.py:255-258`; texts in `backend/open_webui/models/memories.py:221`, `:240`, `:255`, `:261` | A memory operation named a memory that does not exist | Reload | See `memories.md` section 10 |
| `No memories found for user` | Error (HTTP 404), not shown | `backend/open_webui/routers/memories.py:346` | A memory search when the person has none | None | See `memories.md` section 10 |
| `No memory update provided` | Error (HTTP 400) | `backend/open_webui/routers/memories.py:564` | An update with no text, type or path | None | See `memories.md` section 10 |

### 10.13 `routers/audio.py` (Speech-to-Text and Text-to-Speech)

Transcription texts reach the user as a red pop-up from dictation, a call or an attached
recording; speech texts from **Read Aloud**. The admin save refusals are not shown on the admin
page (the save simply does not confirm). The audio area document explains each in depth.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Configure an external speech-to-text engine. Local Whisper is unavailable in slim.` | Error (HTTP 503) | `backend/open_webui/routers/audio.py:219` | Slim image with the local Whisper engine still selected | None | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Local Whisper is unavailable in slim. Select an external speech-to-text engine.` | Error (HTTP 400), admin, not shown | `backend/open_webui/routers/audio.py:295` | Slim image: saving the local Whisper engine while another engine is stored | Admin: choose an external engine | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Local TTS is unavailable in slim. Select an external text-to-speech engine.` | Error (HTTP 400), admin, not shown | `backend/open_webui/routers/audio.py:297` | Slim image: saving the local `transformers` speech engine while another is stored | Admin: choose an external engine | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Configure an external text-to-speech engine. Local TTS is unavailable in slim.` | Error (HTTP 503) | `backend/open_webui/routers/audio.py:328`, `:519` | Defensive check inside the local speech path; the speech endpoint's own check (`:605`) answers first | None | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Open WebUI: Server Connection Error` | Error (the provider's status, or HTTP 500) | `backend/open_webui/routers/audio.py:349`, `:771`, `:824`, `:956-959`, `:1129-1132` | The speech or transcription service could not be reached or answered without a usable message. For OpenAI-compatible and Deepgram transcription the text arrives inside `Error transcribing chunk: ` (below) | Retry later | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `External: {msg}` | Error (the provider's status, or HTTP 500) | `backend/open_webui/routers/audio.py:355`, `:357`, `:359` (speech); `:765`, `:767` (OpenAI), `:834`, `:836` (Deepgram), `:950`, `:952` (Azure), `:1121`, `:1123`, `:1125` (Mistral) | The outside service refused or failed; the words after `External: ` are the service's own (or the raw error when its reply could not be read) | Retry later; report the exact text if it persists | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `TTS returned unsupported format {mime_type}. Configure the provider to return MP3, WAV, Ogg, or another browser-playable audio format.` | Error (HTTP 502) | `backend/open_webui/routers/audio.py:385-388` | Slim image: the speech service returned audio the slim build cannot pass on | None | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Invalid voice id` | Error (HTTP 400) | `backend/open_webui/routers/audio.py:448`, `:452` | ElevenLabs: no voice chosen, or a voice not in the account's list | Choose another voice in **Settings > Audio** | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Mistral API key is required for Mistral TTS` | Error (HTTP 400) | `backend/open_webui/routers/audio.py:558` | Mistral speech engine with no key stored | None | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `No audio_data in Mistral TTS response` | Internal (user sees `Open WebUI: Server Connection Error`, HTTP 500 unless Mistral sent an error status) | `backend/open_webui/routers/audio.py:582` | Mistral answered a speech request without audio; the error handler (`:586-588`, `:341-360`) finds no message in the reply and uses the connection-error text | Retry later | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Configure an external text-to-speech engine.` | Error (HTTP 503) | `backend/open_webui/routers/audio.py:605` | Slim image with the speech engine empty or `transformers` | Reload the page | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `We could not find what you're looking for :/` | Error (HTTP 404) | `backend/open_webui/routers/audio.py:607-610` | **Read Aloud** asked the server for speech while the server's speech engine is `Web API` (empty); the page still holds an older engine setting | Reload the page | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 403) | `backend/open_webui/routers/audio.py:613-616` (speech), `:1259-1262` (transcription) | A non-admin without the `chat.tts` or `chat.stt` permission | Ask an admin | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Invalid JSON payload` | Error (HTTP 400) | `backend/open_webui/routers/audio.py:648` | A speech request whose body is not JSON (MedIT GPT's own pages send JSON) | None | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Unsupported TTS engine: {engine}` | Error (HTTP 400) | `backend/open_webui/routers/audio.py:652` | The stored speech engine has no handler (a value stored from the environment or the API) | None | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Failed to parse Deepgram response` | Internal (user sees `Error transcribing chunk: Open WebUI: Server Connection Error`, HTTP 500) | `backend/open_webui/routers/audio.py:812` | Deepgram answered without a transcript where the code expects it (log line `Malformed Deepgram response: {exc}`, `:811`); the handler at `:819-837` finds no error message in the reply and substitutes the connection-error text | Retry later | Not described elsewhere; server log at that time |
| `Audio file not found` | Error (HTTP 400) | `backend/open_webui/routers/audio.py:843`, `:990` | Azure or Mistral engine: the prepared recording was missing when the server came to send it | Retry | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `File size ({audio_size}MB) exceeds Azure limit of {AZURE_MAX_FILE_SIZE_MB}MB` | Error (HTTP 400) | `backend/open_webui/routers/audio.py:847-850` | Azure engine and a file over its limit (`{audio_size}` is the size in whole megabytes); normally the server has already compressed and cut the file | Use a shorter recording | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Azure API key and region are required for Azure STT` | Error (HTTP 400) | `backend/open_webui/routers/audio.py:879` | Azure engine with no key stored | None | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `No transcription found in response` / `Empty transcript in response` | Internal (user sees `Failed to parse Azure response: {e}` or `Failed to parse Mistral response: {e}`) | `backend/open_webui/routers/audio.py:913`, `:917` (Azure); `:1069`, `:1102` (Mistral) | The engine answered without text, for example after a silent recording | Speak again | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Failed to parse Azure response: {e}` | Error (HTTP 500) | `backend/open_webui/routers/audio.py:929` | Azure's reply had no usable text; `{e}` is one of the two internal texts above | Speak again, closer to the microphone | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `{message}` (Azure's own words) | Error (Azure's status) | `backend/open_webui/routers/audio.py:945` | Azure refused with one of `EmptyAudioFile`, `AudioLengthLimitExceeded`, `NoLanguageIdentified` or `MultipleLanguagesIdentified`, whose message is passed through | Follow the message | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `An error occurred during transcription.` | Error (Azure's status) | `backend/open_webui/routers/audio.py:948` | Azure refused with any other code; the code is logged (`:947`) | Retry later | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `File size exceeds limit of {MAX_FILE_SIZE_MB}MB` | Error (HTTP 400) | `backend/open_webui/routers/audio.py:994` | Mistral engine and a file over the limit (reached when preparation is bypassed) | Use a shorter recording | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Mistral API key is required for Mistral STT` | Error (HTTP 400) | `backend/open_webui/routers/audio.py:1001` | Mistral transcription with no key stored | None | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Mistral chat transcription requires MP3 or WAV in slim; local conversion is unavailable.` | Error (HTTP 400) | `backend/open_webui/routers/audio.py:1016-1018` | Slim image, Mistral chat-completions mode, and a recording that is not `.mp3` or `.wav` | None | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Audio conversion failed. Chat completions API requires mp3 or wav format.` | Error (HTTP 500) | `backend/open_webui/routers/audio.py:1026-1029` | Mistral chat-completions mode could not convert the recording to MP3 | Record again | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Failed to parse Mistral response: {e}` | Error (HTTP 500) | `backend/open_webui/routers/audio.py:1113` | Mistral's reply had no usable text | Speak again | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Audio conversion failed. The audio file may be corrupted or empty.` | Error (HTTP 400) | `backend/open_webui/routers/audio.py:1145-1148` | The recording needed converting to MP3 and the conversion failed (empty or damaged recording) | Record again, speaking for longer | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `[ERROR: Error processing audio file]` (or one of the four storage texts, section 4.2) | Error (HTTP 400) | `backend/open_webui/routers/audio.py:1161-1164` | Cutting a large recording into pieces failed | Use a shorter recording | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Audio chunk cannot be reduced below max file size.` | Internal (user sees `[ERROR: Error processing audio file]`) | `backend/open_webui/routers/audio.py:1242` | A piece of the recording could not be made small enough | Use a shorter recording | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Error transcribing chunk: {transcribe_exc}` | Error (HTTP 500) | `backend/open_webui/routers/audio.py:1173-1176` | The engine call failed with an error that was not already an HTTP error; the inner text is often `External: {msg}` or `Open WebUI: Server Connection Error` | Retry later | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Oops! It seems like the file format you're trying to upload is not supported. Please upload a file with a supported format and try again.` | Error (HTTP 400) | `backend/open_webui/routers/audio.py:1267-1270` | The recording's declared type is not in the supported types for transcription | None | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Invalid audio file extension` | Error (HTTP 400) | `backend/open_webui/routers/audio.py:1278-1281` | The file name's extension is not in the allowed transcription extensions | Try another browser | See `audio-speech-to-text-and-text-to-speech.md` section 10 |
| `Invalid file path detected` | Internal (user sees `Transcription failed.`) | `backend/open_webui/routers/audio.py:1294` | A defensive check on where the uploaded recording is cached; the outer handler (`:1333-1341`) replaces it. Not expected in normal use | Retry | Not described elsewhere; server log traceback |
| `Transcription failed.` | Error (HTTP 400) | `backend/open_webui/routers/audio.py:1328-1331`, `:1338-1341` | Any other transcription failure (cache write failed, no server engine ran, unexpected error) | Reload the page and retry | See `audio-speech-to-text-and-text-to-speech.md` section 10 |

### 10.14 `routers/images.py` (Image Generation and Editing)

Creation and edit failures reach the user as a red pop-up in the image playground or, when a
model generates an image in chat, as a tool result or status line (the image area document,
section 10, describes those paths). Settings texts appear only on the admin **Images** tab.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `[ERROR: Failed to connect to the image generation engine]` (or a storage text, section 4.2) | Error (HTTP 400) | `backend/open_webui/routers/images.py:222-225` | Automatic1111 (or an empty engine value): reading the engine's current model failed, on every creation request while it is down | Wait, or tell the admin | See `image-generation-and-editing.md` section 10 |
| `Invalid format. Please use the correct format  (auto is only allowed with models matching {IMAGE_AUTO_SIZE_MODELS_REGEX_PATTERN}).` | Error (HTTP 400), admin | `backend/open_webui/routers/images.py:281-286` | Saving **Image Size** `auto` with a model whose name does not match the pattern (note the double space in the text) | Admin: a fixed size or a matching model | See `image-generation-and-editing.md` section 10 |
| `Invalid format. Please use the correct format  (e.g., 512x512).` | Error (HTTP 400), admin | `backend/open_webui/routers/images.py:290-293` | **Image Size** is not blank, `auto` or `{width}x{height}` | Admin: type for example `1024x1024` | See `image-generation-and-editing.md` section 10 |
| `Invalid format. Please use the correct format  (e.g., 50).` | Error (HTTP 400), admin | `backend/open_webui/routers/images.py:296-299` | **Steps** below 0 | Admin: enter 0 or more | See `image-generation-and-editing.md` section 10 |
| `Unsupported image engine` | Error (HTTP 400), admin | `backend/open_webui/routers/images.py:351` | The connection check named an engine other than Automatic1111 or ComfyUI (the admin page does not) | None | See `image-generation-and-editing.md` section 10 |
| `The URL you provided is invalid. Please double-check and try again.` | Error (HTTP 400), admin | `backend/open_webui/routers/images.py:359` | The admin's connection check could not reach the engine address, or it answered with an error status | Admin: check address and key | See `image-generation-and-editing.md` section 10 |
| `[ERROR: Failed to retrieve image generation models]` | Error (HTTP 400), admin | `backend/open_webui/routers/images.py:439-442` | The engine's model list could not be read (engine unreachable, or the workflow's model node does not match) | Admin: check the engine | See `image-generation-and-editing.md` section 10 |
| `Failed to retrieve image data from the generation backend` | Internal (user sees `Something went wrong :/`) | `backend/open_webui/routers/images.py:522` | The engine's picture could not be downloaded or decoded | Retry | See `image-generation-and-editing.md` section 10 |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 403) | `backend/open_webui/routers/images.py:566-569`, `:574-577` (creation); `:866-869`, `:874-877` (edit) | Image generation (or image editing) switched off site-wide, or a non-admin without the `features.image_generation` permission | Ask an admin | See `image-generation-and-editing.md` section 10 |
| `[ERROR: {error}]`, for example `[ERROR: Bad Request]` or `[ERROR: Unauthorized]` | Error (HTTP 400) | `backend/open_webui/routers/images.py:841-845` (creation), `:1199-1204` (edit) | The engine answered with an error status; `{error}` is only the HTTP reason phrase (`e.message` of the web client's response error, `:842-844`), not the engine's explanation | Rephrase or retry; report repeated failures | See `image-generation-and-editing.md` section 10 |
| `Something went wrong :/` | Error (HTTP 400) | `backend/open_webui/routers/images.py:841-845`, `:1199-1204` | Any creation or edit failure that is not an engine error status: unreachable engine, unexpected answer, a picture that could not be stored. `ERROR_MESSAGES.DEFAULT` with a bare exception gives this text (section 4.2) | Retry later; report | See `image-generation-and-editing.md` section 10 |
| `We could not find what you're looking for :/` | Error (HTTP 404) | `backend/open_webui/routers/images.py:951`, raised in `backend/open_webui/routers/files.py:912-915`, `:934-937`, `:952-955` | Edit: a source picture's file no longer exists, its stored bytes are gone, or the person may not read it | Attach the picture again | See `image-generation-and-editing.md` section 10 |
| `[ERROR: Error loading image]` (or a storage text) | Error (HTTP 400) | `backend/open_webui/routers/images.py:972-975` | Edit: a source picture could not be read (bad inline data, a failed or refused web link, a storage error) | Attach the picture again | See `image-generation-and-editing.md` section 10 |
| `Failed to upload images to ComfyUI.` | Internal (user sees `Something went wrong :/`) | `backend/open_webui/routers/images.py:1136` | Edit with ComfyUI: uploading a source picture to the engine failed (debug log `Error uploading images to ComfyUI: %s`, `:1135`) | Retry later | See `image-generation-and-editing.md` section 10 |

### 10.15 `routers/automations.py` (Automations)

Shown as red pop-ups on the **Automations** pages. Errors recorded while a scheduled run executes
come from `utils/automations.py` (10.25).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `401 Unauthorized` | Error (HTTP 403) | `backend/open_webui/routers/automations.py:48-51`, `:55-58` | **Automations** switched off site-wide, or a non-admin without the `features.automations` permission | Ask an admin about access | See `automations-calendar-and-timers.md` section 10 |
| `We could not find what you're looking for :/` | Error (HTTP 404) | `backend/open_webui/routers/automations.py:63-66`, `:103-106`, `:115-118`, `:122-125` | The automation does not exist or is someone else's (admins included); the chosen folder is not the person's; a channel destination while channels are off, with no channel, or a deleted channel | Use their own automation; pick another destination | See `automations-calendar-and-timers.md` section 10 |
| `Automation limit reached ({max_count})` | Error (HTTP 403) | `backend/open_webui/routers/automations.py:80-83` | A non-admin creating an automation while already owning the maximum number (paused ones count) | Delete unused automations | See `automations-calendar-and-timers.md` section 10 |
| `Schedule too frequent. Minimum interval is {min_interval} seconds.` | Error (HTTP 400) | `backend/open_webui/routers/automations.py:92-95` | A non-admin saving a schedule whose next two runs are closer than the minimum interval | Choose a less frequent schedule | See `automations-calendar-and-timers.md` section 10 |
| `Something went wrong :/` | Error (HTTP 403) | `backend/open_webui/routers/automations.py:130-133`, `:141-144` | Channel destination when the person lacks the channels permission, is not a member, or may not post in that channel | Choose a channel they can post in | See `automations-calendar-and-timers.md` section 10 |
| `{e}`: `Invalid RRULE: {err}`, `RRULE has no future occurrences`, `RRULE with COUNT requires an explicit DTSTART line to anchor the occurrence window` or `Schedule took too long to evaluate; simplify its recurrence rule.` | Error (HTTP 400) | `backend/open_webui/routers/automations.py:221-224` (create), `:281-284` (update); texts in `backend/open_webui/utils/recurrence.py:103`, `:115`, `:123`, `:125` | The schedule rule cannot be read, never runs again (judged in the person's stored time zone), uses `COUNT` without `DTSTART`, or took too long to evaluate | Fix the custom rule or use a preset | See `automations-calendar-and-timers.md` section 10 |

### 10.16 `routers/calendar.py` (Calendar)

Shown as red pop-ups on `/calendar`. Several refusals are reachable only through the API because the
page hides the control.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `401 Unauthorized` | Error (HTTP 403) | `backend/open_webui/routers/calendar.py:41-44`, `:46-49` | **Calendar** switched off site-wide, or a non-admin without the `features.calendar` permission | Ask an admin about access | See `automations-calendar-and-timers.md` section 10 |
| `Calendar not found` | Error (HTTP 404) | `backend/open_webui/routers/calendar.py:66`, `:477` | Unknown calendar id (for example an event saved while no calendar was loaded), or making someone else's calendar the default | Reload the page | See `automations-calendar-and-timers.md` section 10 |
| `Access denied` | Error (HTTP 403) | `backend/open_webui/routers/calendar.py:79` | No read access (opening) or write access (adding, changing, deleting) through the calendar's sharing | Ask the owner | See `automations-calendar-and-timers.md` section 10 |
| `Invalid date format. Use ISO 8601 (e.g. 2026-04-01T00:00:00)` | Error (HTTP 400) | `backend/open_webui/routers/calendar.py:169` | API: an unreadable `start` or `end` when listing events | Fix the request | See `automations-calendar-and-timers.md` section 10 |
| `{e}`: `Recurring events cannot repeat more often than daily`, `Invalid RRULE: {err}`, `Schedule took too long to evaluate; simplify its recurrence rule.` or the recurrence library's own text | Error (HTTP 422) | `backend/open_webui/routers/calendar.py:279` (create), `:334` (update); texts in `backend/open_webui/models/calendar.py:191`, `:193` and `backend/open_webui/utils/recurrence.py:44`, `:49`, `:69`, `:103` | An event's repeat rule is more often than daily, cannot be read, or took too long to evaluate | Use Daily or a longer repeat | See `automations-calendar-and-timers.md` section 10 |
| `Event not found` | Error (HTTP 404) | `backend/open_webui/routers/calendar.py:307`, `:321`, `:352` | The event was deleted (possibly by someone else with write access) | Reload | See `automations-calendar-and-timers.md` section 10 |
| `Failed to update` | Error (HTTP 500) | `backend/open_webui/routers/calendar.py:336` (event), `:430` (calendar) | The event or calendar vanished during the update | Reload and retry | See `automations-calendar-and-timers.md` section 10 |
| `Failed to delete` | Error (HTTP 500) | `backend/open_webui/routers/calendar.py:358` (event), `:461` (calendar) | The deletion did not succeed | Retry | See `automations-calendar-and-timers.md` section 10 |
| `Invalid status` | Error (HTTP 400) | `backend/open_webui/routers/calendar.py:376` | API: an invitation answer other than the four allowed values | Fix the request | See `automations-calendar-and-timers.md` section 10 |
| `Not an attendee of this event` | Error (HTTP 404) | `backend/open_webui/routers/calendar.py:380` | API: answering an invitation the person did not receive | None | See `automations-calendar-and-timers.md` section 10 |
| `Only owner can manage sharing` | Error (HTTP 403) | `backend/open_webui/routers/calendar.py:412` | API: someone with write access but not the owner changed sharing | Ask the owner | See `automations-calendar-and-timers.md` section 10 |
| `System calendars cannot be deleted` | Error (HTTP 400) | `backend/open_webui/routers/calendar.py:447` | API: deleting the Scheduled Tasks calendar | None | See `automations-calendar-and-timers.md` section 10 |
| `Only owner can delete calendar` | Error (HTTP 403) | `backend/open_webui/routers/calendar.py:453` | Deleting a calendar shared with write access | Ask the owner | See `automations-calendar-and-timers.md` section 10 |
| `Default calendar cannot be deleted` | Error (HTTP 400) | `backend/open_webui/routers/calendar.py:457` | API: deleting the default calendar (the page hides the bin) | None | See `automations-calendar-and-timers.md` section 10 |

### 10.17 `routers/terminals.py` (Terminal Pass-Through)

These texts are sent as `{"error": ...}` answers (or as WebSocket close reasons) to the terminal
dock and shell. The page does not print them: the dock shows `Terminal request failed ({status})`
and the shell `[Connection closed]` instead (see the tools document, section 10), so the HTTP
status is the useful clue.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Terminal server '{server_id}' not found` | Error (HTTP 404), not shown | `backend/open_webui/routers/terminals.py:121`; close reason `Terminal server not found` at `:305` | The admin terminal named in the request no longer exists | Choose another terminal | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Terminal server disabled` | Error (HTTP 403), not shown | `backend/open_webui/routers/terminals.py:124`; close reason at `:309` | The admin terminal is switched off | Choose another terminal | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Access denied` | Error (HTTP 403), not shown | `backend/open_webui/routers/terminals.py:128`; close reason at `:313` | The person is not on that terminal's access list | Ask an admin | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Terminal server URL not configured` | Error (HTTP 503), not shown | `backend/open_webui/routers/terminals.py:132`; close reason at `:343` | The admin terminal has no address | Escalate | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Invalid path` / `Path not allowed` | Error (HTTP 400 / 403), not shown | `backend/open_webui/routers/terminals.py:136`, `:147` | The pass-through refused the requested location | Escalate if seen in normal use | Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca) |
| `Terminal server is not available in chats` | Error (HTTP 403), not shown | `backend/open_webui/routers/terminals.py:158`; close reason at `:317` | The terminal's chat context is switched off | Choose another terminal | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `A saved chat is required for this terminal` | Error (HTTP 409), not shown | `backend/open_webui/routers/terminals.py:161`; close reason at `:355` | A per-chat terminal used from a chat that has not been saved yet | Send a message first so the chat is saved | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Terminal proxy error: {error}` | Error (HTTP 502), not shown | `backend/open_webui/routers/terminals.py:245`, `:249` | The terminal could not be reached, timed out (300-second limit, `:191`) or failed unexpectedly | Retry later | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Expected auth message`, `Auth timeout or invalid payload`, `Invalid token` | WebSocket close reasons, not shown | `backend/open_webui/routers/terminals.py:271`, `:275`, `:278`, `:294`, `:297` | The shell connection was refused at its sign-in step (for example an expired session) | Reload the page; sign in again | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |

### 10.18 `routers/openai.py` (OpenAI-Compatible Connections, `/openai`)

In a chat these texts reach the user through the chat pipeline as the error box (2.2). On the
admin **Connections** tab the **Verify** button does not print the server text: it shows
`OpenAI: {message}` when the provider's answer has an `error.message`, otherwise
`OpenAI: Network Problem` (`src/lib/apis/openai/index.ts:362-381`).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `OpenAI API is disabled` | Error (HTTP 503) | `backend/open_webui/routers/openai.py:362`, `:871`, `:1493` | The site switch for OpenAI-compatible connections is off and a model list, chat or model-management call reached the router | Ask an admin | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Connection not found` | Error (HTTP 404), admin | `backend/open_webui/routers/openai.py:367` | Model management named a connection position that no longer exists | Close and reopen **Manage Models** | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Provider "{provider}" does not support model management` | Error (HTTP 400), admin | `backend/open_webui/routers/openai.py:371-374` | Model management on a connection whose provider type has none; `{provider}` reads `default` when none is set | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Provider "{provider}" does not support {operation}` | Error (HTTP 400), admin | `backend/open_webui/routers/openai.py:383` | An operation the provider type lacks | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `{error}` (the provider's own error answer) or `{e}` | Error (the provider's status, or HTTP 500), admin | `backend/open_webui/routers/openai.py:431`, `:448` | Model management: the provider refused the request (its JSON or text is passed on unchanged), or the request itself failed | Admin: read the provider's words | Not described elsewhere; the provider's own logs |
| `model is required` | Error (HTTP 400) | `backend/open_webui/routers/openai.py:458` | An Anthropic-format request through an OpenAI-compatible connection named no model (scripts) | The script must send a model | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Model '' was not found` | Error (HTTP 404) | `backend/open_webui/routers/openai.py:476`, `:1549-1552` | The model is not in the server's OpenAI-compatible list at the moment of use, even after a fresh fetch; the name is empty because the code passes none | Reload the page and choose a listed model | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `{response_data}` (the provider's own error answer) | Error (the provider's status) | `backend/open_webui/routers/openai.py:528` | An Anthropic-format token count: the provider refused | None | Not described elsewhere; the provider's own words |
| `Invalid token-count response from upstream provider` | Error (HTTP 502) | `backend/open_webui/routers/openai.py:532` | The provider's token count had no valid `input_tokens` | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Open WebUI: Server Connection Error` | Error (HTTP 502 at `:539`; HTTP 500 or the provider's status elsewhere) | `backend/open_webui/routers/openai.py:539`, `:669`, `:932`, `:1121`, `:1148`, `:1151`, `:1748-1751`, `:1854-1857`, `:1985-1988`, `:2110-2113` | No usable answer from the provider: unreachable address, refused or broken connection, time-out, or an unexpected failure while sending | Retry later; report if it persists | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 403 at `:603-606`; HTTP 401 at `:868`) | `backend/open_webui/routers/openai.py:603-606`, `:868` | The legacy `/openai/audio/speech` route without the `chat.tts` permission; a non-admin asking for one connection's raw model list | Ask an admin | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `External: {res["error"]}` / `External: {e}` | Error (the provider's status, or HTTP 500) | `backend/open_webui/routers/openai.py:660`, `:662` | The legacy speech route: the provider refused, or its answer could not be read. MedIT GPT's own pages do not call this route (no caller of `synthesizeOpenAISpeech` in `src/`) | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `OpenAI API was not found` | Never sent (a generic server error is returned instead) | `backend/open_webui/routers/openai.py:673`; text in `backend/open_webui/constants.py:90` | The legacy speech route when no connection is exactly `https://api.openai.com/v1`. The code passes the message **function** without calling it; the web framework's error handler cannot turn a function into JSON, so the answer is a bare server error rather than this text (checked against the pinned FastAPI 0.136.3, `pyproject.toml:9`) | None | Section 14 |
| `Failed to connect to Anthropic API` | Internal (user sees `Unexpected error: Failed to connect to Anthropic API`) | `backend/open_webui/routers/openai.py:898` | One Anthropic connection's model list could not be read | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `HTTP Error: {r.status}` / `External Error: {res["error"]}` | Internal (user sees them inside `Unexpected error: {e}`) | `backend/open_webui/routers/openai.py:907`, `:911`, raised at `:914` | One connection's model list answered with a status other than 200 | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Unexpected error: {e}` | Error (HTTP 500), admin, usually not shown | `backend/open_webui/routers/openai.py:935-936` | One connection's own model list failed; the Connections tab ignores these failures | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `{result['error']}` (Anthropic model-list error) | Never sent (replaced by `Open WebUI: Server Connection Error`) | `backend/open_webui/routers/openai.py:1123`, replaced at `:1149-1151` | **Verify** on an Anthropic address that refused the model list. The refusal is raised inside the same `try` whose general handler replaces it, so the provider's words are lost (the error text itself comes from `backend/open_webui/utils/anthropic.py:71-78`) | Admin: check the key | Section 14 |
| The provider's own error answer (JSON or text) | Error (the provider's status), admin | `backend/open_webui/routers/openai.py:1113`, `:1115`, `:1139`, `:1141` | **Verify**: the address answered the model list with an error; the page shows `OpenAI: {message}` or `OpenAI: Network Problem` | Admin: check address and key | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Invalid model name: must not be empty or contain path separators or traversal sequences` | Error (HTTP 400) | `backend/open_webui/routers/openai.py:1214-1217` | Azure (classic address form): the deployment name is empty or contains characters a deployment name cannot have | Admin: correct **Model IDs** | See `model-connections-openai-ollama-and-direct.md` section 10 |
| The provider's own error answer, or `{"error": {"message": "{error_body}", "code": {status}}}` when it is not JSON | Error (the provider's status); error box in chat | `backend/open_webui/routers/openai.py:1694`, `:1706-1709`, `:1736`, `:1738` (chat); `:1847`, `:1849` (embeddings); `:1975`, `:1977` (Responses API); `:2097`, `:2099` (pass-through) | The provider refused a chat, embedding or pass-through request; its words are passed on and the chat pipeline shows them in the error box | Retry; report the exact text | See `chat-completion-pipeline-and-generation-tasks.md` section 10 |
| `Direct API passthrough is disabled. Set ENABLE_OPENAI_API_PASSTHROUGH=True to enable.` | Error (HTTP 403) | `backend/open_webui/routers/openai.py:2002-2005` | A script called an `/openai/...` path that has no dedicated route while the pass-through is off (the code default) | Use a supported endpoint | See `model-connections-openai-ollama-and-direct.md` section 10; turning it on is a security decision for the maintainer |

### 10.19 `routers/ollama.py` (Ollama Connections, `/ollama`)

As for 10.18, chat failures reach the error box; **Verify** shows `Ollama: {message}` or
`Ollama: Network Problem` instead of the server text (`src/lib/apis/ollama/index.ts:22`). When
Ollama itself answers with an `error` field, that text is passed on unchanged.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{res['error']}` (Ollama's own words) | Error (Ollama's status) | `backend/open_webui/routers/ollama.py:152` | Ollama refused a request with an error text, for example an unknown model tag during a pull | Follow Ollama's words | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Open WebUI: Server Connection Error` | Error (Ollama's status, or HTTP 500) | `backend/open_webui/routers/ollama.py:164-167`, `:193`, `:283` | Ollama answered with an error that had no `error` text, a request failed without any description, or **Verify** could not connect | Retry later | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Ollama: {e}` | Error (Ollama's status, or HTTP 500) | `backend/open_webui/routers/ollama.py:191-194` | Ollama could not be reached or the connection broke; the words after `Ollama:` are the network library's | Retry later | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `HTTP Error: {r.status}` / `External Error: {res["error"]}` | Internal (user sees them inside `Unexpected error: {exc}`) | `backend/open_webui/routers/ollama.py:274`, `:277`, raised at `:278` | **Verify**: the address answered the version check with a status other than 200 | Admin: check the address | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Unexpected error: {exc}` | Error (HTTP 500), admin | `backend/open_webui/routers/ollama.py:286` | **Verify** failed for a reason other than a connection error; the page shows `Ollama: Network Problem` | Admin: check the address | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 401; 403 at `:1077`) | `backend/open_webui/routers/ollama.py:490`, `:556`, `:1077`, `:1498` | A non-admin asked for one server's list or version, or named a server position that does not host the model | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `The Ollama API is disabled. Please enable it to use this feature.` | Error (HTTP 503) | `backend/open_webui/routers/ollama.py:493`, `:661`, `:698`, `:738`, `:770`, `:808`, `:849`, `:896`, `:947`, `:1006`, `:1108`, `:1280`, `:1396`, `:1454` | The site switch for Ollama is off and a list, pull, push, create, copy, delete, show, embedding or chat call reached the router | Ask an admin | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `WebUI could not connect to Ollama` | Error (HTTP 500), usually not shown | `backend/open_webui/routers/ollama.py:579` | No enabled Ollama server answered the version check (**About** then omits the Ollama version) | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Missing name of the model to unload.` | Error (HTTP 400), admin | `backend/open_webui/routers/ollama.py:605` | An unload call without a model name | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Model '{model}' was not found` (also `{form_data.model}` and `{form_data.source}`) | Error (HTTP 400) | `backend/open_webui/routers/ollama.py:612`, `:704`, `:776`, `:818`, `:861`, `:909`, `:960`, `:1016`, `:1089-1092` | The model is not on any enabled Ollama server, even after a fresh fetch (deleted, server off or down, or filtered out by **Model IDs**) | Choose a listed model | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Failed to unload model on {len(errors)} nodes: {errors}` | Error (HTTP 500), admin | `backend/open_webui/routers/ollama.py:644-647`; per-server texts `{e}` collected at `:641` | Unloading failed on at least one Ollama server | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `{exc}`: a request-validation text, for example one containing `At least one of 'content' or 'tool_calls' must be provided` | Error (HTTP 400) | `backend/open_webui/routers/ollama.py:1129`, `:1234`, `:1288`, `:1338`; inner text `:1049` | A chat, completion or embedding request (scripts, or a pipe that calls Ollama) did not match the expected shape | Fix the request | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Ollama: Could not create blob, Please try again.` | Error inside the progress stream, admin, not shown | `backend/open_webui/routers/ollama.py:1601` (download), `:1688` (upload) | Ollama refused the model file; in URL mode the stream ends, in file mode the text goes to the browser console | Admin: check Ollama's disk space | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Invalid file_url. Only URLs from allowed hosts are permitted.` | Error (HTTP 400), admin | `backend/open_webui/routers/ollama.py:1615-1618` | **Upload a GGUF model** from an address outside the two allowed hosts | Use a Hugging Face or GitHub address | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Failed to create model in Ollama. {resp_text}` | Error inside the progress stream, admin, not shown | `backend/open_webui/routers/ollama.py:1718`, sent at `:1721` | File-mode upload: Ollama refused to create the model | Admin: read Ollama's words | See `model-connections-openai-ollama-and-direct.md` section 10 |

### 10.20 `utils/middleware.py` (The Chat Pipeline)

The pipeline turns most failures into the error box under the reply (saved with the message and
sent as `chat:message:error` or `chat:completion`, 2.2), a status line, or a tool result. Plain
status lines are owned by the in-chat status catalogue (area 32); only error-flagged ones are
listed here. The pipeline area document explains each path.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{"error": {error}}` from a Responses API `response.failed` event | Error box | `backend/open_webui/utils/middleware.py:931-934` | A connection of the `Responses` type reported the reply as failed; the provider's error object is passed on | Retry; report the exact text | See `chat-completion-pipeline-and-generation-tasks.md` section 10 |
| `No JSON object found in the response` | Internal (log at debug level; the step falls back) | `backend/open_webui/utils/middleware.py:1419`, `:1609`, `:1978`, `:2080` | The task model's answer for tool selection, search queries, image prompt or retrieval queries contained no `{`; the code then skips tool selection or uses the raw answer or the user's own message | None | See `image-generation-and-editing.md` section 10 |
| `{"error": "{e}"}` (a tool's own exception text) | Tool result | `backend/open_webui/utils/middleware.py:1466` (legacy tool selection), `:3386` (resumed after approval), `:6027` (native tool calls) | The tool raised an error; the model receives the exception text and the tool call is marked failed | Retry; report the tool's name | See `builtin-native-tools.md` and `chat-completion-pipeline-and-generation-tasks.md` section 10 |
| `Query generation failed` | Internal (logged; the user's message is searched as written) | `backend/open_webui/utils/middleware.py:1597`, `:1599`, raised at `:1600` | Generating web-search queries failed and its answer carried no `detail` | None | See `chat-completion-pipeline-and-generation-tasks.md` section 10 |
| `{detail}` (the query task's own error text) | Internal (logged; the user's message is searched as written) | `backend/open_webui/utils/middleware.py:1597`, raised at `:1600` | Generating web-search queries failed with a reason, for example `Model '' was not found` | None | See `chat-completion-pipeline-and-generation-tasks.md` section 10 |
| `No search results found` | Status (error flag) | `backend/open_webui/utils/middleware.py:1705-1710` | Legacy-mode web search returned nothing usable | Rephrase | See `web-search-and-web-loading.md` section 10 |
| `{detail}` (the search endpoint's text) or `An error occurred while searching the web` | Status (error flag) | `backend/open_webui/utils/middleware.py:1720-1726` | Legacy-mode web search failed; an HTTP error's own text (for example `[ERROR: No results found from web search]`, 10.7) is shown when there is one | Retry later | See `web-search-and-web-loading.md` section 10 |
| `An error occurred while generating an image` | Status (error flag) | `backend/open_webui/utils/middleware.py:1927` (edit), `:2035` (creation) | Legacy-mode image editing or generation failed; the model is told the error text | Retry or rephrase | See `image-generation-and-editing.md` section 10 |
| `Image prompt generation failed` (or the task's own `{detail}`) | Internal (logged; the user's message becomes the image prompt) | `backend/open_webui/utils/middleware.py:1966`, `:1968`, raised at `:1969` | Generating the image prompt failed | None | See `image-generation-and-editing.md` section 10 |
| `{e}` (a filter function's own error text) | Error box | `backend/open_webui/utils/middleware.py:2669-2670` (inlet), `:3271-3272` (request) | An inlet or request filter refused or failed; the turn stops | Report the text; it is the filter author's | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `Failed to connect to MCP server '{server_id}'` | Error box (the reply continues) | `backend/open_webui/utils/middleware.py:3006-3012` | A selected MCP tool server could not be reached or signed in to | Retry; deselect the tool | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Terminal unavailable: {e}` | Error box (HTTP 503 inside the task) | `backend/open_webui/utils/middleware.py:3063` | The selected terminal's tools could not be loaded | Deselect the terminal and resend | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Error: Tool call arguments could not be parsed. The model generated malformed or incomplete JSON.` | Tool result | `backend/open_webui/utils/middleware.py:3335-3341` | A call resumed after approval had unreadable arguments | Retry | See `chat-completion-pipeline-and-generation-tasks.md` section 10 |
| `Error: Tool call arguments must be a JSON object.` | Tool result | `backend/open_webui/utils/middleware.py:3343-3346` | A resumed call's arguments were valid JSON but not an object | Retry | See `chat-completion-pipeline-and-generation-tasks.md` section 10 |
| `Error: Tool "{name}" not found.` | Tool result | `backend/open_webui/utils/middleware.py:3351`, `:5997` | The model called a tool that is not available in this turn | Reselect the tool | See `chat-completion-pipeline-and-generation-tasks.md` section 10 |
| `Error: Browser session is not connected for this direct tool.` | Tool result | `backend/open_webui/utils/middleware.py:3362` | An approved browser-side tool was resumed without a live browser tab | Keep the tab open; resend | See `chat-completion-pipeline-and-generation-tasks.md` section 10 |
| `Invalid JSON response` | Error box | `backend/open_webui/utils/middleware.py:3668` | A non-streaming reply's body could not be decoded | Retry | See `chat-completion-pipeline-and-generation-tasks.md` section 10 |
| `{error}` (the provider's error text or object) | Error box | `backend/open_webui/utils/middleware.py:4230-4255` (non-streaming), `:5075-5090` (a streamed line without `data:`), `:5191-5197` (a stream's closing metadata), `:5226-5248` (a streamed error chunk) | The provider answered the chat with an error; its words are saved on the message and shown (log lines `Provider returned error (non-streaming): %s`, `:4238`, and `(streaming)`, `:5229`) | Retry; report the exact text | See `chat-completion-pipeline-and-generation-tasks.md` section 10; patterns in section 11.6 |
| `Chat failed` (with `{e}` as its message) | Event (`chat.failed`), not an on-screen text | `backend/open_webui/utils/middleware.py:4388-4408` | Processing a non-streaming reply in a saved chat raised an error; the event reaches webhooks and notifications | None | See `notifications-webhooks-events-and-banners.md` section 9 |
| `Tool call arguments must be a JSON object.` | Internal (user sees the next row) | `backend/open_webui/utils/middleware.py:5977` | Native tool calling: arguments that are valid JSON but not an object | Retry | See `chat-completion-pipeline-and-generation-tasks.md` section 10 |
| `Error: Tool call arguments for {name} must be a JSON object. Please try again.` (the name is in back-quotes in the source) | Tool result | `backend/open_webui/utils/middleware.py:5985-5992` | As above, handed to the model so it can retry | Retry | See `chat-completion-pipeline-and-generation-tasks.md` section 10 |
| `Error: Tool call arguments could not be parsed. The model generated malformed or incomplete JSON for {tool_function_name}. Please try again.` (the name is in back-quotes in the source) | Tool result | `backend/open_webui/utils/middleware.py:6050-6059` | The model produced unreadable tool arguments | Retry; try another model | See `chat-completion-pipeline-and-generation-tasks.md` section 10 |
| The provider's error after a tool or code step (`{error_content}`) | Error box | `backend/open_webui/utils/middleware.py:6328-6337` (after tools), `:6528`, `:6535` (after code execution) | The model call that continues the answer after tools or code ran failed | Retry | See `chat-completion-pipeline-and-generation-tasks.md` section 10 |
| `Tool-call limit reached ({max_tool_call_iterations} iterations).` | Error box | `backend/open_webui/utils/middleware.py:6339-6346` | The model kept calling tools past the limit | Rephrase; ask for fewer steps | See `chat-completion-pipeline-and-generation-tasks.md` section 10 |
| `Code interpreter engine not configured.` | Notice (shown as the code's output) | `backend/open_webui/utils/middleware.py:6423` | Legacy-mode code interpreter with no usable engine set | None | See `code-execution-and-interpreter.md` section 10 |
| `Chat completion stream failed` | Error (API callers, last stream event) | `backend/open_webui/utils/middleware.py:6708-6710` | Streaming to an API caller failed mid-reply | Retry | See `chat-completion-pipeline-and-generation-tasks.md` section 10 |

### 10.21 `utils/chat.py` (Model Routing)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Direct connection requires an active WebSocket session; cannot generate completion in this context (e.g. background task).` | Error box or run error | `backend/open_webui/utils/chat.py:65-68` | A personal (direct) connection's model was used without a live browser tab: an automation, timer, sub-agent or API script | Use a site-wide model for unattended work | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `{res}` (the browser's whole reply, for example `{'error': 'Client session disconnected.'}`) | Error box | `backend/open_webui/utils/chat.py:128` | Streaming through a direct connection: the browser tab reported failure | Keep the tab open; resend | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `{res['error']}` (the browser's error text) | Error box | `backend/open_webui/utils/chat.py:142-143` | Non-streaming through a direct connection: the browser tab reported an error | Keep the tab open; resend | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Model not found` | Error box in a chat (`backend/open_webui/main.py:1686-1710`); Error (HTTP 400) on the deprecated `/api/chat/completed` (`backend/open_webui/main.py:2103-2107`) | `backend/open_webui/utils/chat.py:193`, `:330` | The chosen model is not in the server's model list at the moment of use (most chats are refused earlier with the same text, `backend/open_webui/main.py:1128-1129`) | Reload and pick a listed model | See `chat-completion-pipeline-and-generation-tasks.md` section 10; pattern in section 11.3 |
| `Missing message id` | Error (HTTP 400, `backend/open_webui/main.py:2103-2107`) | `backend/open_webui/utils/chat.py:326`, `:342` | The deprecated `/api/chat/completed` was called without a message id (integrations) | None | See `chat-completion-pipeline-and-generation-tasks.md` section 10 |
| `Error: {e}` | Error (HTTP 400) | `backend/open_webui/utils/chat.py:339`, `:374` | An outlet filter (Pipelines or a function) failed on the deprecated `/api/chat/completed` endpoint | Report the filter's text | See `chat-completion-pipeline-and-generation-tasks.md` section 10 |

### 10.22 `utils/models.py` (Model Access Check)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Model not found` | Error (HTTP 400 when the chat request is refused, `backend/open_webui/main.py:1638-1645`) | `backend/open_webui/utils/models.py:480`, `:491`, `:515`, `:521` | A non-admin (or an admin when admin bypass is off) chose a model they may not read, a provider model with no model record, an arena model not shared with them, or a model whose base model they may not read. The refusal is worded like a missing model on purpose | Pick a listed model; ask an admin about sharing | See `workspace-models-and-model-access.md` and `chat-completion-pipeline-and-generation-tasks.md` section 10; pattern in section 11.3 |
| `Model access denied: user_id=%r model_id=%r reason=arena_read_denied` (also `reason=model_unregistered`, `reason=model_read_denied`) | Log (warning) | `backend/open_webui/utils/models.py:475-479`, `:486-490`, `:510-514` | Written just before the three `Model not found` refusals above; the base-model refusal at `:521` writes no line here | None | Gives the real reason behind `Model not found`; the line holds a user id, so treat log extracts as personal data |
| `Failed to update Redis model cache, using in-process cache: {e}` | Log (warning) | `backend/open_webui/utils/models.py:457` | The shared model list could not be written to Redis; this worker keeps its own copy, so workers may briefly offer different model lists | None | See `workspace-models-and-model-access.md` section 10 |

### 10.23 `utils/files.py` (Image and Audio Helpers)

None found in code that reaches a user. The helpers in this file return nothing instead of raising
when an image address cannot be fetched, is too large or compressed, or a stored image cannot be
read (`backend/open_webui/utils/files.py:55-105`, `:209-241`), so a failed image is simply missing
from the chat or tool result without a message. The searches covered `raise`, `HTTPException`,
`error`, `except` and logging calls across the 241-line file.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Error decoding base64 audio data: {e}` | Log (printed to standard output, not through the logger) | `backend/open_webui/utils/files.py:159-161` | Audio returned inline by a model or tool could not be decoded; the audio is dropped | None | Not described elsewhere; server output at that time |

### 10.24 `utils/memory.py` (Memory Operations)

These are raised by the memory routes and by the built-in memory tools, so they appear as a red
pop-up in **Settings > Personalization** or inside a tool call's output as
`{"error": "400: <text>"}`. The background memory review runs without the user and records
failures only at debug level.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Memory content cannot be empty` | Error (HTTP 400) or tool result | `backend/open_webui/utils/memory.py:24` | A memory's text is empty or only spaces | Type the memory's text | See `memories.md` section 10 |
| `Invalid memory path` | Error (HTTP 400) or tool result | `backend/open_webui/utils/memory.py:34` | A part of the memory path is `.` or `..`, or it contains a control character | Remove that part | See `memories.md` section 10 |
| `Memory path is required` | Error (HTTP 400) or tool result | `backend/open_webui/utils/memory.py:189` | Reading memories by path with an empty path | None (the model retries) | See `memories.md` section 10 |
| `No memory operations provided` | Error (HTTP 400) or tool result | `backend/open_webui/utils/memory.py:253` | A batch memory update with no operations | None | See `memories.md` section 10 |
| `Memory id is required for replace` / `Memory id is required for move` / `Memory id is required for remove` | Error (HTTP 400) or tool result | `backend/open_webui/utils/memory.py:266`, `:273`, `:277` | A batch operation names no memory id | None (the model retries) | See `memories.md` section 10 |
| `Unsupported memory operation: {action}` | Error (HTTP 400); not expected | `backend/open_webui/utils/memory.py:279` | Any action other than the four allowed ones; the request's form check refuses those earlier | None | See `memories.md` section 10 |
| `Memory review failed: %s` | Log (debug) | `backend/open_webui/utils/memory.py:465-471` | The background review of a finished chat failed (for example its model call failed or one of the texts above was raised); nothing is shown | None | See `memories.md` section 10; needs debug logging |

### 10.25 `utils/automations.py` (Scheduled Runs)

Run errors are saved on the automation's run record (cut to 4,000 characters) and shown beside the
run on the automation's page and on the calendar's past runs; each also publishes the
`automation.run.failed` event (sections 6 and 9).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Channel not found` | Run error | `backend/open_webui/utils/automations.py:261`, recorded at `:520-529` | Channel destination while channels are off site-wide, or no channel stored | Change the destination | See `automations-calendar-and-timers.md` section 10 |
| `User not found` | Run error | `backend/open_webui/utils/automations.py:354-362` | The owner's account no longer exists (nobody can see the record, because only the owner opens the automation) | None | See `automations-calendar-and-timers.md` section 10 |
| `Owner no longer permitted to run automations` | Run error | `backend/open_webui/utils/automations.py:367-380` | At run time the owner is not a `user` or `admin`, or no longer has the automations permission | Ask an admin about the permission | See `automations-calendar-and-timers.md` section 10 |
| `Failed to create chat` | Run error | `backend/open_webui/utils/automations.py:448-458` | The run's new chat could not be saved | Retry with **Run now** | See `automations-calendar-and-timers.md` section 10 |
| `{error}` (any other failure, for example `400: Model not found`) | Run error | `backend/open_webui/utils/automations.py:520-529` | Any other failure before the reply started; an HTTP error is recorded with its status in front | Retry with **Run now** | See `automations-calendar-and-timers.md` section 10 |
| `Automation {automation.id} failed` | Log (exception) | `backend/open_webui/utils/automations.py:521` | Written with the traceback for the previous row | None | Matches the run record's time |
| `Scheduler: timer error` / `Scheduler: automation error` / `Scheduler: calendar alert error` / `Scheduler worker error` | Log (exception) | `backend/open_webui/utils/automations.py:96`, `:114`, `:121`, `:124` | One pass of the scheduler loop failed for timers, due automations, calendar alerts or the loop itself; the loop carries on at the next poll | None | See `automations-calendar-and-timers.md` section 10 |
| `Terminal server {server_id} not found for CWD set` / `Failed to set terminal CWD to {cwd}: HTTP {resp.status} — {body[:200]}` / `Failed to set terminal CWD: {e}` | Log (warning); never written | `backend/open_webui/utils/automations.py:218`, `:245`, `:247` | From a helper that nothing calls; it would also stop at its first step, because it reads the terminal list from an application attribute that nothing sets (`:212-214`) | None | See `automations-calendar-and-timers.md` section 10; section 14 |

### 10.26 `utils/code_interpreter.py` (Jupyter Engine)

Shown as the code block's error output under the reply (or handed to the model when the code
interpreter is a tool). The legacy-mode text `Code interpreter engine not configured.` is in 10.20.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Error: {err}` | Code output (error) | `backend/open_webui/utils/code_interpreter.py:74-76` | Signing in to the Jupyter server, starting a kernel or running the code failed; `{err}` is the failure's own text (for example an HTTP status from the Jupyter server) | Retry later | See `code-execution-and-interpreter.md` section 10 |
| `_xsrf token not found` | Internal (user sees it inside `Error: {err}`, above) | `backend/open_webui/utils/code_interpreter.py:84-86` | Password sign-in to Jupyter: the sign-in page returned an empty form token | None | See `code-execution-and-interpreter.md` section 10 |
| `Execution timed out.` | Code output (error, appended) | `backend/open_webui/utils/code_interpreter.py:184-186` | No output arrived from the Jupyter kernel within the configured time-out; the limit applies to each wait for output (`:159`), not to the whole run | Simplify the code | See `code-execution-and-interpreter.md` section 10 |

### 10.27 `utils/tools.py` (Tool Servers and Terminals at Chat Time)

The terminal texts reach the user inside `Terminal unavailable: {e}` in the error box (10.20). The
tool-server call failures are handed to the model as `{"error": "<text>"}` and the tool call is
marked failed.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Terminal server '{terminal_id}' not found` | Error box (inside `Terminal unavailable: {e}`) | `backend/open_webui/utils/tools.py:1376` | The selected admin terminal was removed between choosing it and sending | Choose another terminal | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Terminal server '{terminal_id}' is disabled` | Error box (as above) | `backend/open_webui/utils/tools.py:1378` | The selected admin terminal is switched off | Choose another terminal | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Access denied to terminal {terminal_id}` | Error box (as above) | `backend/open_webui/utils/tools.py:1382` | The person is no longer on the terminal's access list | Ask an admin | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Terminal server '{terminal_id}' is unavailable` | Error box (as above) | `backend/open_webui/utils/tools.py:1388` | The terminal's specification could not be loaded | Retry later | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Terminal server '{terminal_id}' has no available tools` | Error box (as above) | `backend/open_webui/utils/tools.py:1392` | The terminal's specification lists no functions | Escalate | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Terminal server '{terminal_id}' is not available for {terminal_context}` | Error box (as above) | `backend/open_webui/utils/tools.py:1413` | The terminal's chat (or automation) context is switched off | Choose another terminal | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Terminal server '{terminal_id}' requires a saved {terminal_context} context` | Error box (as above) | `backend/open_webui/utils/tools.py:1422` | A per-chat terminal used where there is no saved chat (for example a temporary chat) | Use a normal (saved) chat | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `{error_body}` (the tool server's own error answer) or the connection error's text | Internal (logged; at chat time that server's tools are skipped, on the admin **Verify** the dialog shows its own failure text) | `backend/open_webui/utils/tools.py:1487-1489`, `:1503-1513`; callers `:1574-1581` and `backend/open_webui/routers/configs.py:672` | Fetching a tool server's specification failed (error status, unreachable, time-out) | Retry later | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10; log line `Failed to connect to {url} OpenAPI tool server` (`:1580`) |
| `No matching route found for operationId: {name}` / `No matching method found for operationId: {name}` | Tool result (`{"error": ...}`) | `backend/open_webui/utils/tools.py:1647`, `:1662`, returned at `:1779-1782` | The cached specification no longer contains the function the model called | Retry after the list is refreshed | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `HTTP error {response.status}: {text}` | Tool result (`{"error": ...}`) | `backend/open_webui/utils/tools.py:1738`, `:1763`, returned at `:1779-1782` | An admin tool server or terminal answered the call with an HTTP error; `{text}` is its own reply | Retry; report if repeated | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `{error}` (any other call failure) | Tool result (`{"error": ...}`) | `backend/open_webui/utils/tools.py:1779-1782` | The call to the tool server failed for another reason (unreachable, time-out); logged as `API Request Error: {error}` | Retry later | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |

### 10.28 `tools/builtin.py` (Built-In Tool Results)

Every row is a tool result handed to the model, normally as JSON `{"error": "<text>"}` (plain text
where marked). The person sees it only by opening the tool call's **Output**, where the entry is
marked failed, and the model usually explains it in its own words. The built-in tools area
document lists each tool with its results; the texts the tools pass on from other code are listed
under their own files (for example the web-search texts in 10.7 and the memory texts in 10.24).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{e}` (the failure's own text; an HTTP error from the code a tool calls appears as `{status}: {detail}`, section 4) | Tool result | `backend/open_webui/tools/builtin.py:194`, `:286`, `:330`, `:362`, `:437`, `:510`, `:625`, `:792`, `:828`, `:862`, `:920`, `:960`, `:1001`, `:1050`, `:1082`, `:1119`, `:1221`, `:1283`, `:1332`, `:1504`, `:1607`, `:1672`, `:1812`, `:1893`, `:1954`, `:2038`, `:2101`, `:2161`, `:2326`, `:2450`, `:2506`, `:2626`, `:2747`, `:2860`, `:3006`, `:3148`, `:3369`, `:3474`, `:3545`, `:3640`, `:3690`, `:3767`, `:3814`, `:3874`, `:3918`, `:3953`, `:3990`, `:4041`, `:4085`, `:4237`, `:4364`, `:4485`, `:4545` | Any failure inside a built-in tool, for example `400: [ERROR: No results found from web search]` from `search_web` or `400: Memory content cannot be empty` from a memory tool | Read the inner text and use its row | See `builtin-native-tools.md` section 10; escalate unfamiliar texts with the chat link |
| `Notification failed: user not found.` / `Notification failed: {e}` | Tool result (plain text) | `backend/open_webui/tools/builtin.py:147`, `:157-158` | `notify` without an account, or delivery failed | Check **Settings > Notifications** | See `builtin-native-tools.md` section 10 |
| `Request context not available` | Tool result | `backend/open_webui/tools/builtin.py:309`, `:345`, `:385`, `:458`, `:654`, `:885`, `:943`, `:989`, `:1022`, `:1065`, `:1095`, `:1145`, `:1236`, `:1300`, `:1363`, `:1535`, `:1623`, `:1777`, `:1834`, `:1908`, `:1969`, `:2061`, `:2121`, `:2185`, `:2424`, `:2474`, `:2527`, `:2652`, `:2773`, `:2885`, `:3031`, `:3170`, `:3388`, `:3496`, `:3740`, `:3839`, `:3937`, `:4005`, `:4056`, `:4170`, `:4269`, `:4396`, `:4500` | The tool ran without the server's request details (not expected in a normal chat) | Retry | See `builtin-native-tools.md` section 10 |
| `User context not available` | Tool result | `backend/open_webui/tools/builtin.py:1148`, `:1239`, `:1303`, `:1366`, `:1538`, `:1626`, `:1780`, `:1837`, `:1911`, `:1972`, `:2064`, `:2124`, `:2188`, `:2427`, `:2477`, `:2530`, `:2655`, `:2776`, `:2888`, `:3034`, `:3173`, `:3391`, `:3499`, `:3743`, `:3842`, `:3940`, `:4008`, `:4059`, `:4173`, `:4272`, `:4399`, `:4503` | The tool ran without the person's account details | Retry | See `builtin-native-tools.md` section 10 |
| `ask_user requires 1-3 questions.`, `Each question must be an object.`, `Each question requires a non-empty id.`, `Duplicate question id: {question_id}`, `Each question requires 2-3 options.`, `Each option must be an object.`, `Each option requires a label and description.`, `Each question requires question text.` | Tool result (`{"status": "error", "error": ...}`) | `backend/open_webui/tools/builtin.py:536`, `:542`, `:546`, `:548`, `:553`, `:558`, `:563`, `:574`, returned at `:623-625` | The model's question card for the person was malformed | None (the model retries) | See `builtin-native-tools.md` section 10 |
| `User input requires an active browser session with WebSocket connection.` | Tool result | `backend/open_webui/tools/builtin.py:589-596` | `ask_user` with no browser connected | Keep the chat open in a browser | See `builtin-native-tools.md` section 10 |
| `Invalid user input response.` | Tool result | `backend/open_webui/tools/builtin.py:610` | The browser's answer to the question card was not readable | Retry | See `builtin-native-tools.md` section 10 |
| `{output.get('error')}` (the browser's own error text, for example `Client session disconnected.`) | Tool result | `backend/open_webui/tools/builtin.py:611-612` | The browser reported an error instead of answers | Keep the tab open; retry | Not described elsewhere for this tool; the browser-call texts are in `chat-completion-pipeline-and-generation-tasks.md` section 10 |
| `Event call not available. WebSocket connection required for pyodide execution.` | Tool result | `backend/open_webui/tools/builtin.py:693` | `execute_code` with the in-browser engine but no browser connection | Keep the chat open; retry | See `builtin-native-tools.md` section 10 |
| `Unknown code interpreter engine: {engine}` | Tool result | `backend/open_webui/tools/builtin.py:742` | The stored engine is neither `pyodide` nor `jupyter` | None | See `builtin-native-tools.md` section 10 |
| `Memory not found or access denied` | Tool result | `backend/open_webui/tools/builtin.py:1079` | `delete_memory` with an id that is not one of the person's memories | None | See `builtin-native-tools.md` section 10 |
| `Note not found` | Tool result | `backend/open_webui/tools/builtin.py:1245`, `:1374` | `view_note` or `replace_note_content` with an unknown id | None | See `builtin-native-tools.md` section 10 |
| `Access denied` | Tool result | `backend/open_webui/tools/builtin.py:1264`, `:1931`, `:1992`, `:2942`, `:3534`, `:3859`, `:4022`, `:4070`, `:4416`, `:4425`, `:4520`, `:4529` | The person cannot read that note, channel message, file or skill, does not own that automation, or cannot change that calendar event | Ask the owner to share it | See `builtin-native-tools.md` section 10 |
| `Failed to create note` / `Failed to update note` | Tool result | `backend/open_webui/tools/builtin.py:1319`, `:1488` | The note could not be saved | Retry | See `builtin-native-tools.md` section 10 |
| `Write access denied` | Tool result | `backend/open_webui/tools/builtin.py:1378` | `replace_note_content` on a note the person cannot edit | Ask the owner for edit access | See `builtin-native-tools.md` section 10 |
| `operations must be a non-empty list`, `each operation must be an object`, `replace operation must be the only operation`, `replace operation content must be a string`, `unknown operation action`, `operation start and end must be integers`, `operation content must be a string`, `operation range is out of bounds`, `operation expected text does not match current content`, `operation ranges must not overlap`, `content or operations is required` | Tool result | `backend/open_webui/tools/builtin.py:1384`, `:1390`, `:1399-1403`, `:1407-1411`, `:1419`, `:1427`, `:1431`, `:1435`, `:1439-1443`, `:1453`, `:1463` | The model's note edit was malformed, or the note changed since the model read it | Ask the model to reread the note | See `builtin-native-tools.md` section 10 |
| `Chat not found or access denied` | Tool result | `backend/open_webui/tools/builtin.py:1634` | `view_chat` on a chat that is not the person's own | None | See `builtin-native-tools.md` section 10 |
| `Error: request context not available.` | Tool result (plain text) | `backend/open_webui/tools/builtin.py:1702`, `:1740` | `delegate_task` or the timer tool without request details | Retry | See `builtin-native-tools.md` section 10 |
| `Error: sub-agents cannot delegate recursively.` | Tool result (plain text) | `backend/open_webui/tools/builtin.py:1704` | A sub-agent tried to start another sub-agent | None | See `builtin-native-tools.md` section 10 |
| `Error: timers cannot be set from internal chats.` | Tool result (plain text) | `backend/open_webui/tools/builtin.py:1742` | A sub-agent tried to set a timer | None | See `builtin-native-tools.md` section 10 |
| `Message not found` / `Channel not found` | Tool result | `backend/open_webui/tools/builtin.py:1919`, `:1981`; `:1924`, `:1986` | Unknown channel message id, or its channel no longer exists | None | See `builtin-native-tools.md` section 10 |
| `Knowledge base {knowledge_id} is not attached to this model` | Tool result | `backend/open_webui/tools/builtin.py:2215` | The model named a knowledge base outside the model's attached knowledge | None | See `builtin-native-tools.md` and `knowledge-bases.md` section 10 |
| `Access denied to knowledge base {knowledge_id}` | Tool result | `backend/open_webui/tools/builtin.py:2291` | The person cannot read that knowledge base | Ask the owner to share it | See `builtin-native-tools.md` and `knowledge-bases.md` section 10 |
| `{err}` (a search-pattern refusal from 10.29) | Tool result | `backend/open_webui/tools/builtin.py:2371-2373` | `grep_chat_files` or `grep_knowledge_files` with a pattern that is too long, not valid, or too slow | Ask for a simpler search | See `knowledge-bases.md` section 10 |
| `Pattern is required` | Tool result | `backend/open_webui/tools/builtin.py:2480`, `:2658` | Empty search pattern | None | See `builtin-native-tools.md` section 10 |
| `No files are attached to this chat` | Tool result | `backend/open_webui/tools/builtin.py:2495`, `:2555` | A chat-file tool in a chat with no uploaded files | Attach the file to the chat | See `builtin-native-tools.md` section 10 |
| `File not found` | Tool result | `backend/open_webui/tools/builtin.py:2497`, `:2557`, `:2676`, `:2799`, `:2802`, `:2917` | Unknown file, a file not attached to this chat, or a file the person may not read (deliberately the same text) | Re-attach the file | See `builtin-native-tools.md` section 10 |
| `No accessible files found` | Tool result | `backend/open_webui/tools/builtin.py:2501`, `:2561`, `:2741` | None of the files can be read by the person | Re-attach the files | See `builtin-native-tools.md` section 10 |
| `Embedding function not configured` | Tool result | `backend/open_webui/tools/builtin.py:2578`, `:3208`, `:3404` | The server has no embedding function loaded | None | See `builtin-native-tools.md` section 10; escalate as a retrieval set-up problem |
| `Skill '{id}' not found` | Tool result | `backend/open_webui/tools/builtin.py:3509`, `:3521` | Unknown or inactive skill | None | See `builtin-native-tools.md` section 10 |
| `Saved chat context not available` | Tool result | `backend/open_webui/tools/builtin.py:3608`, `:3660` | Checklist tools in a chat that is not saved | None | See `builtin-native-tools.md` section 10 |
| `Invalid status: {status}. Must be one of: {", ".join(sorted(VALID_TASK_STATUSES))}` | Tool result | `backend/open_webui/tools/builtin.py:3666` | Unknown checklist status | None | See `builtin-native-tools.md` section 10 |
| `Task with id "{id}" not found` | Tool result | `backend/open_webui/tools/builtin.py:3679` | Unknown checklist item | None | See `builtin-native-tools.md` section 10 |
| `Folder not found` | Tool result (raised, returned at `:3767`, `:3874`, `:3953`) | `backend/open_webui/tools/builtin.py:3705` | The automation's folder is not one of the person's folders | None | See `builtin-native-tools.md` section 10 |
| `User not found` | Tool result | `backend/open_webui/tools/builtin.py:3754`, `:3853` | The account behind the call is missing | None | See `builtin-native-tools.md` section 10 |
| `Could not detect current model` | Tool result | `backend/open_webui/tools/builtin.py:3762` | `create_automation` could not tell which model the chat uses | Retry | See `builtin-native-tools.md` section 10 |
| `Invalid schedule: {e}` | Tool result | `backend/open_webui/tools/builtin.py:3773`, `:3881` | The schedule rule is not valid (`{e}` is a recurrence text from 10.15) | Rephrase the schedule | See `builtin-native-tools.md` section 10 |
| `{e.detail}`: `Automation limit reached ({max_count})` or `Schedule too frequent. Minimum interval is {min_interval} seconds.` | Tool result | `backend/open_webui/tools/builtin.py:3776-3778`, `:3886` | The automation limits refused the model's automation (texts from 10.15) | Delete unused automations or choose a less frequent schedule | See `builtin-native-tools.md` section 10 |
| `Automation not found` | Tool result | `backend/open_webui/tools/builtin.py:3857`, `:4020`, `:4068` | Unknown automation id | None | See `builtin-native-tools.md` section 10 |
| `Invalid start datetime: {e}` / `Invalid end datetime: {e}` | Tool result | `backend/open_webui/tools/builtin.py:4192`, `:4197`, `:4440`, `:4447` | An unreadable date when searching or updating calendar events | None | See `builtin-native-tools.md` section 10 |
| `No calendars found. Cannot create event.` | Tool result | `backend/open_webui/tools/builtin.py:4286` | No calendar could be found or created for the person | Retry | See `builtin-native-tools.md` section 10 |
| `Calendar not found` | Tool result | `backend/open_webui/tools/builtin.py:4292` | Unknown calendar id | None | See `builtin-native-tools.md` section 10 |
| `Access denied to this calendar` | Tool result | `backend/open_webui/tools/builtin.py:4305` | No write access to the named calendar | Ask the owner | See `builtin-native-tools.md` section 10 |
| `Invalid start datetime: {e}. Use format like "2026-04-20 09:00"` / `Invalid end datetime: {e}. Use format like "2026-04-20 10:00"` | Tool result | `backend/open_webui/tools/builtin.py:4316`, `:4323` | An unreadable date when creating an event | None | See `builtin-native-tools.md` section 10 |
| `Failed to create event` / `Failed to update event` / `Failed to delete event` | Tool result | `backend/open_webui/tools/builtin.py:4353`, `:4474`, `:4534` | The calendar event could not be saved or deleted | Retry | See `builtin-native-tools.md` section 10 |
| `Event not found` | Tool result | `backend/open_webui/tools/builtin.py:4410`, `:4514` | Unknown event id | None | See `builtin-native-tools.md` section 10 |

### 10.29 `tools/knowledge_fs.py` (The `kb_exec` Knowledge File-System Tool)

All rows are plain-text tool results read by the model; the knowledge area document explains the
commands.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Search patterns over {MAX_SEARCH_PATTERN_LENGTH} characters are not supported` | Tool result | `backend/open_webui/tools/knowledge_fs.py:92-93` | A search pattern longer than the limit | Ask for a simpler search | See `knowledge-bases.md` section 10 |
| `Invalid or unsupported regex (RE2 syntax): {e}` | Tool result | `backend/open_webui/tools/knowledge_fs.py:106-107` | The model's pattern is not a valid RE2 expression | None (the model retries) | See `knowledge-bases.md` section 10 |
| `Search exceeded {MATCH_BUDGET_SECONDS:g}s, narrow the pattern` | Tool result (reaches the model through `Error: {e}` below) | `backend/open_webui/tools/knowledge_fs.py:120-121` | A pattern search ran past its time budget | Ask for a narrower search | See `knowledge-bases.md` section 10 |
| `Ambiguous filename "{ref}". Use full path to disambiguate:` (followed by the matching files) | Tool result | `backend/open_webui/tools/knowledge_fs.py:512-516` | Several reachable files share the name | None (the model retries with a path) | See `knowledge-bases.md` section 10 |
| `Directory not found: {dir_path}` | Tool result (inside a listing) | `backend/open_webui/tools/knowledge_fs.py:587`, `:1052` | A listed folder does not exist in the knowledge base | None | See `knowledge-bases.md` section 10 |
| `File not found: {args[0]}` (also `{file_ref}`) | Tool result | `backend/open_webui/tools/knowledge_fs.py:647`, `:676`, `:705`, `:911`, `:932`, `:1009` | The file is not reachable by this person and model | Check the file is in an attached knowledge base | See `knowledge-bases.md` section 10 |
| `Too many files ({len(accessible)}). Scope your search: grep "{pattern}" docs/ or grep "{pattern}" *.py` | Tool result | `backend/open_webui/tools/knowledge_fs.py:802-803` | A search across more files than the limit | None (the model narrows it) | See `knowledge-bases.md` section 10 |
| `Invalid range: start ({start}) > end ({end})` | Tool result | `backend/open_webui/tools/knowledge_fs.py:1005` | The `sed` command was given a start line after its end line | None (the model retries) | Not described elsewhere; a model mistake, no action |
| `Usage: …` hints, for example `Usage: cat [-n] <file_id or filename>`, `Usage: kb_exec("<command>"). Run kb_exec("ls") to start.` | Tool result | `backend/open_webui/tools/knowledge_fs.py:643`, `:672`, `:701`, `:726`, `:857`, `:907`, `:928`, `:999`, `:1185` | A command was called without its arguments | None (the model retries) | See `knowledge-bases.md` section 10 (the `kb_exec` usage line); the per-command hints are not described elsewhere |
| `Unknown command: {cmd_name}. Available: {", ".join(sorted(COMMAND_MAP.keys()))}` | Tool result | `backend/open_webui/tools/knowledge_fs.py:1121-1122` | An unsupported command | None | See `knowledge-bases.md` section 10 |
| `Error: User context not available` | Tool result | `backend/open_webui/tools/knowledge_fs.py:1181-1182` | `kb_exec` ran without the person's account details | Retry | See `knowledge-bases.md` section 10 |
| `Could not parse command. Run kb_exec("ls") to start.` | Tool result | `backend/open_webui/tools/knowledge_fs.py:1189-1190` | The command line could not be split into commands | None | See `knowledge-bases.md` section 10 |
| `Error: {e}` | Tool result | `backend/open_webui/tools/knowledge_fs.py:1201-1203` | Any failure while running the command (logged `kb_exec error: {e}`) | Retry; escalate if repeated | See `knowledge-bases.md` section 10 |

### 10.30 `retrieval/loaders/` (Document Extraction Engines)

These texts become the processing failure of an uploaded or knowledge-base file: stored on the file
record, shown as the yellow pop-up after an upload, and returned by the processing endpoint
(10.7, the `{e}` row). A text raised as an HTTP error arrives with its status in front, for example
`504: MinerU processing timed out after 10 minutes`. One row per message per file; the engine
names are the **Documents** admin tab's labels.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Error loading {self.file_path}` | Warning (upload) | `backend/open_webui/retrieval/loaders/main.py:180-181` (CSV) | A CSV file could not be read; the text includes the file's location on the server | Check the file opens; save it again as UTF-8 | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `<No text content found>` | Text stored as the document (no error) | `backend/open_webui/retrieval/loaders/main.py:244` (Tika), `:305` (Docling) | The engine answered but returned no text; the file shows as processed and a chat may quote this text | Provide a text-based version | See `rag-retrieval-embeddings-and-vector-stores.md` section 10; pattern in section 11.5 |
| `Error calling Tika: {r.reason}` | Warning (upload) | `backend/open_webui/retrieval/loaders/main.py:253` | Tika answered with an error status (`{r.reason}` is its HTTP reason phrase) | Retry later | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Error calling Docling: conversion status {conversion_status} - {error_details}` | Warning (upload) | `backend/open_webui/retrieval/loaders/main.py:294-301` | Docling reported the conversion as `failure` or `skipped` (`no error message provided` when it gave no reason) | Try another format of the document | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Error calling Docling: {error_msg}`, where `{error_msg}` is `Error calling Docling API: {r.reason}` followed by ` - ` and Docling's detail or text when it gave one | Warning (upload) | `backend/open_webui/retrieval/loaders/main.py:320-329` | Docling answered with an error status | Retry later | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Document archive is too large after decompression` | Warning (upload) | `backend/open_webui/retrieval/loaders/main.py:520-539` | An Office, e-book or other zip-based file expands beyond the size limit | Split or simplify the document | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `This file type requires an external document extractor in slim. Configure one that supports it.` | Warning (upload; HTTP 503 inside) | `backend/open_webui/retrieval/loaders/main.py:700-712` | Slim image, the default engine, and a file type other than text, Markdown, HTML, XML or CSV | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Processing .epub files requires the 'unstructured' package. Install it with: pip install unstructured` (also `.doc`, `.msg` and `.odt`) | Warning (upload) | `backend/open_webui/retrieval/loaders/main.py:753-756`, `:766-769`, `:801-804`, `:809-812` | The server lacks the optional `unstructured` package. The standard image installs it (`backend/requirements.txt:73`), so this points to a `pip` installation without that extra | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 (the `.epub`, `.msg` and `.odt` variants are not quoted there) |
| `The 'unstructured' package is not installed. Falling back to plain text loading for .rst file. Install it with: pip install unstructured` (also for `.xml`, and `Falling back to pandas for Excel file loading.` / `Falling back to python-pptx for PowerPoint file loading.` with `Install unstructured for better results: pip install unstructured`) | Log (warning) | `backend/open_webui/retrieval/loaders/main.py:729-733`, `:739-743`, `:777-781`, `:790-794` | As above for file types that have a simpler fallback; the file is still processed | None | Not described elsewhere; explains poorer extraction of those types |
| `Error loading {self.file_path}` | Warning (upload) | `backend/open_webui/retrieval/loaders/local.py:13-17` (text files) | A text file could not be read with the detected encoding; the text includes the file's location on the server | Save the file again as UTF-8 | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Unsupported email file type: {detected}` | Warning (upload) | `backend/open_webui/retrieval/loaders/local.py:72-78` | A `.msg` file that is neither an Outlook message nor a plain e-mail | Save the message in another format | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Provide exactly one of api_key or azure_credential.` | Warning (upload); not expected | `backend/open_webui/retrieval/loaders/local.py:101-102` | Document Intelligence with its key setting missing rather than empty (the code default is empty, `backend/open_webui/config.py:951`) | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `PDF mode must be 'single' or 'page'` | Warning (upload) | `backend/open_webui/retrieval/loaders/pdf.py:14-15` | The stored PDF loader mode is neither value | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `File not found: {self.file_path}` | Warning (upload; HTTP 404 inside) | `backend/open_webui/retrieval/loaders/datalab_marker.py:105-106` | The stored file was missing when Datalab Marker processing began | Upload the file again | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Datalab Marker request failed: {e}` / `Datalab Marker request failed: {result.get("error", "Unknown error")}` | Warning (upload; HTTP 400 inside) | `backend/open_webui/retrieval/loaders/datalab_marker.py:107-111`, `:117-121` | Marker answered with an error status, or without success | Retry later | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Invalid JSON response: {e}` | Warning (upload; HTTP 502 inside) | `backend/open_webui/retrieval/loaders/datalab_marker.py:112-113` | Marker's answer could not be read | Retry later | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `{e}` (any other failure) | Warning (upload; HTTP 500 inside) | `backend/open_webui/retrieval/loaders/datalab_marker.py:114-115` | Sending the file to Marker failed for another reason (for example the address could not be reached) | Retry later | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Polling failed: {e}` | Warning (upload; HTTP 502 inside) | `backend/open_webui/retrieval/loaders/datalab_marker.py:133-138` | A status check on the Marker job failed | Retry later | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Marker processing failed: {error_msg}` | Warning (upload; HTTP 400 inside) | `backend/open_webui/retrieval/loaders/datalab_marker.py:158-164` | Marker reported failure (`Marker returned failure without error message` when it gave no reason) | Try another format | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Marker processing timed out` | Warning (upload; HTTP 504 inside) | `backend/open_webui/retrieval/loaders/datalab_marker.py:165-169` | No result after the polling limit | Retry later, or a smaller file | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Final processing failed: {error_msg}` | Warning (upload; HTTP 400 inside) | `backend/open_webui/retrieval/loaders/datalab_marker.py:171-176` | The job completed without success (`Unknown processing error` when no reason) | Try another format | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Custom Marker endpoint returned success but no 'output' field found. Available fields: {available_fields}. Expected either 'request_check_url' for polling or 'output' field for direct response.` | Warning (upload; HTTP 502 inside) | `backend/open_webui/retrieval/loaders/datalab_marker.py:188-193` | A self-hosted Marker answered in an unexpected shape | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Unsupported output format: {self.output_format}` | Warning (upload; HTTP 400 inside) | `backend/open_webui/retrieval/loaders/datalab_marker.py:199-203` | The stored output format is not Markdown, JSON or HTML | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Marker returned empty content` | Warning (upload; HTTP 400 inside) | `backend/open_webui/retrieval/loaders/datalab_marker.py:205-209` | Marker found no text | Provide a text-based version | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Error connecting to endpoint: {e}` | Warning (upload) | `backend/open_webui/retrieval/loaders/external_document.py:63-67` | The external document loader could not be reached | Retry later | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Error loading document: Unable to parse content` / `Error loading document: No content returned` / `Error loading document: {response.status_code} {response.text}` | Warning (upload) | `backend/open_webui/retrieval/loaders/external_document.py:89-90`, `:92-93`, `:94-95` | The external loader's answer was unreadable, empty, or an error status | Retry later | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Invalid API mode: {self.api_mode}. Must be 'local' or 'cloud'` / `API key is required for Cloud API mode` | Warning (upload) | `backend/open_webui/retrieval/loaders/mineru.py:51-52`, `:55-56` | MinerU settings are inconsistent | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `File not found: {self.file_path}` | Warning (upload; HTTP 404 inside) | `backend/open_webui/retrieval/loaders/mineru.py:111-112`, `:305-306` | The stored file was missing when MinerU processing began | Upload the file again | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `MinerU Local API request timed out` | Warning (upload; HTTP 504 inside) | `backend/open_webui/retrieval/loaders/mineru.py:113-117` | No answer within the MinerU time-out | Retry later, or a smaller file | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `{error_detail}`: `MinerU Local API request failed: {e}`, `Failed to request upload URL: {e}` or `Failed to poll batch status: {e}`, each followed by ` - ` and MinerU's own message | Warning (upload; HTTP 400 inside) | `backend/open_webui/retrieval/loaders/mineru.py:118-126`, `:246-254`, `:347-355` | MinerU answered with an error status | Retry later | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Error calling MinerU Local API: {str(e)}` | Warning (upload; HTTP 500 inside) | `backend/open_webui/retrieval/loaders/mineru.py:127-131` | Connection or other failure calling local MinerU | Retry later | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Invalid JSON response from MinerU Local API: {e}` / `MinerU Local API response missing 'results' field` | Warning (upload; HTTP 502 inside) | `backend/open_webui/retrieval/loaders/mineru.py:137-140`, `:144-147` | Local MinerU answered in an unexpected shape | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `MinerU returned empty results` / `MinerU returned empty markdown content` | Warning (upload; HTTP 400 inside) | `backend/open_webui/retrieval/loaders/mineru.py:151-154`, `:161-164` | Local MinerU found nothing to extract | Provide a text-based version | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Error requesting upload URL: {str(e)}` | Warning (upload; HTTP 500 inside) | `backend/open_webui/retrieval/loaders/mineru.py:255-259` | MinerU cloud could not be reached to start the upload | Retry later | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Invalid JSON response: {e}` | Warning (upload; HTTP 502 inside) | `backend/open_webui/retrieval/loaders/mineru.py:264-267` | MinerU cloud's answer could not be read | Retry later | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `MinerU Cloud API error: {result.get("msg", "Unknown error")}` | Warning (upload; HTTP 400 inside) | `backend/open_webui/retrieval/loaders/mineru.py:271-274`, `:372-375` | MinerU cloud reported an error code | Retry later | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `MinerU Cloud API response missing batch_id or file_urls` | Warning (upload; HTTP 502 inside) | `backend/open_webui/retrieval/loaders/mineru.py:281-284` | Unexpected answer from MinerU cloud | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `File upload to presigned URL timed out` / `Failed to upload file to presigned URL: {e}` / `Error uploading file: {str(e)}` | Warning (upload; HTTP 504, 400 or 500 inside) | `backend/open_webui/retrieval/loaders/mineru.py:308-311`, `:313-316`, `:318-321` | Uploading the file to MinerU cloud failed | Retry later | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Error polling batch status: {str(e)}` / `Invalid JSON response while polling: {e}` | Warning (upload; HTTP 500 or 502 inside) | `backend/open_webui/retrieval/loaders/mineru.py:357-360`, `:365-368` | A status check on the MinerU job failed | Retry later | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `File {filename} not found in batch results` | Warning (upload; HTTP 502 inside) | `backend/open_webui/retrieval/loaders/mineru.py:388-391` | MinerU's results did not include the file | Retry later | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `MinerU processing failed: {error_msg}` | Warning (upload; HTTP 400 inside) | `backend/open_webui/retrieval/loaders/mineru.py:400-403` | MinerU reported failure | Try another format | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `MinerU processing timed out after 10 minutes` | Warning (upload; HTTP 504 inside) | `backend/open_webui/retrieval/loaders/mineru.py:414-417` | No result after the polling limit | Retry later, or a smaller file | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Failed to download results ZIP: {e}` / `Error downloading results: {str(e)}` | Warning (upload; HTTP 400 or 500 inside) | `backend/open_webui/retrieval/loaders/mineru.py:430-433`, `:435-438` | Fetching MinerU's results failed | Retry later | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Markdown file in results ZIP is too large: {member.filename}` | Warning (upload; HTTP 502 inside) | `backend/open_webui/retrieval/loaders/mineru.py:463-466` | MinerU's result is over the Markdown size limit | Split the document | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `{error_msg}`: `Found .md files but couldn't read them: {read_errors}` or `No .md files found in ZIP. Available files: {all_files}` | Warning (upload; HTTP 502 inside) | `backend/open_webui/retrieval/loaders/mineru.py:481-490` | MinerU's result had no usable Markdown | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Invalid ZIP file received: {e}` / `Error extracting ZIP: {str(e)}` | Warning (upload; HTTP 502 or 500 inside) | `backend/open_webui/retrieval/loaders/mineru.py:492-495`, `:499-502` | MinerU's result could not be opened | Retry later | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Extracted markdown content is empty` | Warning (upload; HTTP 400 inside) | `backend/open_webui/retrieval/loaders/mineru.py:513-516` | MinerU's result was empty | Provide a text-based version | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `API key cannot be empty.` | Warning (upload); not expected | `backend/open_webui/retrieval/loaders/mistral.py:52-53` | Mistral OCR chosen with the key setting missing rather than empty; an empty key makes the code use the default engine instead (`backend/open_webui/retrieval/loaders/main.py:676-683`) | Escalate | Not described elsewhere |
| `File not found at {file_path}` | Warning (upload) | `backend/open_webui/retrieval/loaders/mistral.py:54-55` | The stored file was missing when Mistral OCR began | Upload the file again | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `File ID not found in upload response.` / `Signed URL not found in response.` | Internal (stored as the document text `Error during processing: {e}`) | `backend/open_webui/retrieval/loaders/mistral.py:205`, `:227` | Mistral's answers to the upload steps were missing a field | Escalate | Not described elsewhere; the content row below applies |
| `No text content found` | Text stored as the document (no error) | `backend/open_webui/retrieval/loaders/mistral.py:286-293` | Mistral OCR answered with no pages (internal code `no_pages`) | Provide a clearer scan or a text version | See `rag-retrieval-embeddings-and-vector-stores.md` section 10; pattern in section 11.5 |
| `No valid text content found in document` | Text stored as the document (no error) | `backend/open_webui/retrieval/loaders/mistral.py:341-353` | Mistral OCR returned pages without text (internal code `no_valid_pages`) | As above | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Error during processing: {e}` | Text stored as the document (no error) | `backend/open_webui/retrieval/loaders/mistral.py:391-403` | Any Mistral OCR failure, including a refused key (internal code `processing_failed`) | Escalate; the file looks processed but holds only this sentence | See `rag-retrieval-embeddings-and-vector-stores.md` section 10; pattern in section 11.5 |
| `PaddleOCR-vl API URL and Token are required.` | Never shown | `backend/open_webui/retrieval/loaders/paddleocr_vl.py:27-28` | The only caller chooses this engine only when both settings are present (`backend/open_webui/retrieval/loaders/main.py:688-697`) | None | Section 14 |
| `File not found at {file_path}` | Warning (upload) | `backend/open_webui/retrieval/loaders/paddleocr_vl.py:29-30` | The stored file was missing when PaddleOCR-vl began | Upload the file again | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `No valid text content found in document` | Text stored as the document (no error) | `backend/open_webui/retrieval/loaders/paddleocr_vl.py:101-112` | PaddleOCR-vl found no text on any page (internal code `no_valid_pages`) | Provide a clearer scan | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Error during OCR processing: {e}` | Text stored as the document (no error) | `backend/open_webui/retrieval/loaders/paddleocr_vl.py:116-127` | Any PaddleOCR-vl failure (internal code `processing_failed`; log `Error calling PaddleOCR-vl: {e}`) | Escalate; the file looks processed but holds only this sentence | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |

### 10.31 `retrieval/models/` (Rerankers)

The rerankers never show a message. The external reranker logs its failure and hands back no
scores, so results keep their original order (10.33); the ColBERT checks are defensive.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Expected query embeddings to have 3 dimensions, but got {query_embeddings.dim()}.` / `Expected document embeddings to have 3 dimensions, but got {document_embeddings.dim()}.` / `There should be either one query or queries equal to the number of documents.` | Internal; not expected | `backend/open_webui/retrieval/models/colbert.py:40-45` | Defensive shape checks in the ColBERT reranker; its own `predict` always passes inputs of the right shape (`:61-74`) | None | Not described elsewhere |
| `No results found in external reranking response` | Log (error) | `backend/open_webui/retrieval/models/external.py:63-65` | The external reranker answered without a `results` list; documents are not rescored | None | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Error in external reranking: {e}` | Log (exception) | `backend/open_webui/retrieval/models/external.py:67-69` | The external reranker could not be reached or refused the request; documents are not rescored | None | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |

### 10.32 Web Page and YouTube Loading (`retrieval/web/utils.py`, `retrieval/loaders/youtube.py`, `tavily.py`, `external_web.py`, `microsoft_web_iq.py`)

Used when a person attaches a web page or YouTube link, when web search loads result pages, and by
the `fetch_url` tool. For an attached page the user sees the router's wrapper text
(`[ERROR: Error processing URL]` or `[ERROR: Could not read content from {form_data.url}]`, 10.7);
YouTube texts are shown unchanged. During a web search, a page that fails is skipped and logged.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `The URL you provided is invalid. Please double-check and try again.` | Internal (an attached page shows `[ERROR: Error processing URL]`, `backend/open_webui/routers/retrieval.py:2246`, `:2421-2426`; the web and YouTube endpoints show `[ERROR: Could not read content from {form_data.url}]`, `:2450-2455`); tool result from `fetch_url` | `backend/open_webui/retrieval/web/utils.py:110`, `:122`, `:128`, `:134`, `:142`, `:149`, `:161`, `:1061`; checked at `backend/open_webui/retrieval/utils.py:258` | The address is malformed or was refused by the server's address checks | Paste the page's text instead | See `web-search-and-web-loading.md` section 10; whether an address should be reachable is security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca) |
| `getaddrinfo for {host} returned empty list` | Internal (logged; the page is skipped) | `backend/open_webui/retrieval/web/utils.py:197` | The page's host name did not resolve when the connection was made | Check the address | Not described elsewhere |
| `SSL certificate verification failed for {url}` | Internal (logged, for example `SSL verification failed for {url}: {e}` at `:532` or `Error loading {url}: {e}` at `:887`; the page is skipped) | `backend/open_webui/retrieval/web/utils.py:383-393`; called at `:529`, `:559`, `:616`, `:864`, `:905` | Certificate checking is on and the site's certificate did not verify (Tavily, Microsoft Web IQ and Playwright loaders) | Try another source | Not described elsewhere |
| `No valid URLs to process after SSL verification` | Log (warning); the raised form is never sent | `backend/open_webui/retrieval/web/utils.py:535-539`, `:566-570`, `:622-626` | Every address failed the certificate check. The code raises only when failures may not be skipped, and the only caller always allows skipping (`:1073-1079`) | Try another source | Section 14 (raised form) |
| `Playwright is unavailable in slim. Use basic HTTP fetching or an external web loader.` | Error (HTTP 503 inside) | `backend/open_webui/retrieval/web/utils.py:682-685` | Slim image with Playwright stored as the web loader | Escalate | See `web-search-and-web-loading.md` section 10 |
| `page.goto() returned None for url {url}` | Internal (logged `Error loading {url}: {e}`; the page is skipped) | `backend/open_webui/retrieval/web/utils.py:874-875`, `:914-915`, logged at `:886-888` | Playwright opened the address but got no page back | Try another source | Not described elsewhere |
| `retry count exceeded` | Never raised | `backend/open_webui/retrieval/web/utils.py:985-1012` | After the retry loop; the last attempt re-raises its own error first and the only caller uses the default of three attempts (`:976`) | None | Section 14 |
| `Invalid WEB_LOADER_ENGINE: {engine}. Please set it to 'safe_web', 'playwright', 'firecrawl', 'tavily', 'external', or 'microsoft_web_iq'.` | Internal (attaching a page shows the router's wrapper text) | `backend/open_webui/retrieval/web/utils.py:1148-1152` | The stored web loader value is not one the code knows | Escalate | See `web-search-and-web-loading.md` section 10 |
| `At least one URL must be provided.` | Never raised in practice | `backend/open_webui/retrieval/loaders/tavily.py:45-46` | The Tavily loader is created only after at least one address passed (`backend/open_webui/retrieval/web/utils.py:535-545`, `:566-577`) | None | Section 14 |
| `Failed to extract content from {url}: {error}` / `Error extracting content from batch {batch_urls}: {e}` | Log (error) | `backend/open_webui/retrieval/loaders/tavily.py:87`, `:90` | Tavily could not extract a page; the page is skipped | None | Not described elsewhere |
| `Error extracting content from batch {urls}: {e}` | Log (error) | `backend/open_webui/retrieval/loaders/external_web.py:52` | The external web loader failed for a batch; the batch is skipped | None | Not described elsewhere |
| `Error browsing {url} with Microsoft Web IQ: {e}` | Log (warning) | `backend/open_webui/retrieval/loaders/microsoft_web_iq.py:44` | Microsoft Web IQ could not load a page; the page is skipped | None | Not described elsewhere |
| `YouTube blocked the transcript request for {video_id} from this server. This usually means the server address is rate limited or belongs to a cloud provider. A proxy for these requests can be configured under Admin Settings, Web Search, Youtube Proxy URL.` | Error (HTTP 400) | `backend/open_webui/retrieval/loaders/youtube.py:28-34`, raised at `:128`, `:168` | YouTube refused the server's request | Report it | See `web-search-and-web-loading.md` section 10 |
| `Transcripts are disabled for the YouTube video {video_id}.` | Error (HTTP 400) | `backend/open_webui/retrieval/loaders/youtube.py:35-36` | The video has no transcripts | Use another source | See `web-search-and-web-loading.md` section 10 |
| `The YouTube video {video_id} is age restricted, so its transcript cannot be retrieved.` | Error (HTTP 400) | `backend/open_webui/retrieval/loaders/youtube.py:37-38` | Age-restricted video | Use another source | See `web-search-and-web-loading.md` section 10 |
| `The YouTube video {video_id} is unavailable.` | Error (HTTP 400) | `backend/open_webui/retrieval/loaders/youtube.py:39-40` | Private, removed or invalid video | Check the link | See `web-search-and-web-loading.md` section 10 |
| `YouTube requires additional verification to return the transcript for {video_id}.` | Error (HTTP 400) | `backend/open_webui/retrieval/loaders/youtube.py:41-42` | YouTube asked for extra verification | Report it | See `web-search-and-web-loading.md` section 10 |
| `Could not retrieve a transcript for the YouTube video {video_id}.` | Error (HTTP 400) | `backend/open_webui/retrieval/loaders/youtube.py:44` | Any other transcript failure (log `Loading YouTube transcript failed: %s`, `:127`) | Try again later | See `web-search-and-web-loading.md` section 10 |
| `No transcript found for the YouTube video {self.video_id} in these languages: {languages_tried}.` | Error (HTTP 400) | `backend/open_webui/retrieval/loaders/youtube.py:170-177` | No transcript in the configured languages | Report it | See `web-search-and-web-loading.md` section 10 |
| ``Could not import "youtube_transcript_api" Python package. Please install it with `pip install youtube-transcript-api`.`` | Internal; not expected | `backend/open_webui/retrieval/loaders/youtube.py:111-115` | The YouTube package is missing; it is a core dependency of every build (`pyproject.toml:105`) | Escalate | Not described elsewhere |

### 10.33 `retrieval/utils.py` (Embeddings, Search and Reranking Helpers)

An embedding failure while a file is processed becomes that file's failure text (10.7, the `{e}`
row); during a chat it leaves the reply without sources (status `No sources found`, owned by the
pipeline document); through the search endpoints it becomes `[ERROR: Error querying knowledge base]`
(10.7); in a tool it is a tool result. Three helpers here (`generate_openai_batch_embeddings`,
`generate_azure_openai_batch_embeddings`, `generate_ollama_batch_embeddings`, at `:899`, `:963`,
`:1045`) have no caller in the repository; only their asynchronous twins run.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Oops! The file you're trying to upload is too large. Please upload a file that is less than {max_size} MB.` | Internal on the web endpoint (shown as `[ERROR: Could not read content from {form_data.url}]`, `backend/open_webui/routers/retrieval.py:2450-2455`); tool result from `fetch_url` | `backend/open_webui/retrieval/utils.py:211-212` | A linked file being downloaded for its text is larger than the upload limit | Download it and attach a smaller copy | See `web-search-and-web-loading.md` section 10 |
| `Hybrid search failed for all collections. Using Non-hybrid search as fallback.` | Internal (in chats and tools the search is repeated without hybrid search, debug log `Hybrid search failed, falling back to vector search: %s`, `:732-733`; through the search endpoints it is replaced by `[ERROR: Error querying knowledge base]`, `backend/open_webui/routers/retrieval.py:3153`, `:3193-3196`) | `backend/open_webui/retrieval/utils.py:893-894` | Hybrid search failed for every collection | None | Not described elsewhere; the `query_collection_with_hybrid_search` log line below gives the cause |
| `Unexpected OpenAI embeddings response: missing 'data' key` | Processing failure or no sources (see above) | `backend/open_webui/retrieval/utils.py:957-960` (also `:926`, not called) | The OpenAI-compatible embedding service answered without embeddings | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Unexpected Azure OpenAI embeddings response: missing 'data' key` | Processing failure or no sources | `backend/open_webui/retrieval/utils.py:1039-1042` (also `:1001`, not called) | The Azure OpenAI embedding service answered without embeddings | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Azure OpenAI embedding request failed: max retries (429) exceeded` | Never raised | `backend/open_webui/retrieval/utils.py:1002` | Only in the synchronous Azure helper, which nothing calls; the asynchronous one does not retry on HTTP 429 | None | Section 14 |
| `Ollama embed error ({r.status}): {error_detail}` | Processing failure or no sources | `backend/open_webui/retrieval/utils.py:1104-1107` (also `({r.status_code})` at `:1069`, not called) | The Ollama embedding call was refused, for example a model that is not pulled | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Unexpected Ollama embeddings response: missing 'embeddings' key` | Processing failure or no sources | `backend/open_webui/retrieval/utils.py:1109-1112` (also `:1075`, not called) | Ollama answered without embeddings | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Configure an external embedding engine (openai, ollama, azure_openai).` | Processing failure or no sources (HTTP 503 inside) | `backend/open_webui/retrieval/utils.py:1129-1130` | Slim image with the local embedding engine | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `No embedding model is loaded. Set RAG_EMBEDDING_MODEL to a valid SentenceTransformer model name, or configure an external RAG_EMBEDDING_ENGINE (ollama, openai, azure_openai).` | Processing failure or no sources, on every upload and document question | `backend/open_webui/retrieval/utils.py:1132-1137` | The local embedding model failed to load | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Embedding generation failed for batch {i + 1}/{len(batches)}` | Processing failure or no sources | `backend/open_webui/retrieval/utils.py:1188-1192` | One batch of a multi-batch embedding returned nothing | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Unknown embedding engine: {embedding_engine}` | Processing failure or no sources | `backend/open_webui/retrieval/utils.py:1205-1206` | The stored embedding engine is not one the code knows | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Configure an external reranker, or clear the reranking model to use cosine scoring.` | Internal in chats and tools (the search falls back, see the hybrid row); Error (HTTP 503) on `/api/v1/retrieval/query/doc` (`backend/open_webui/routers/retrieval.py:3076`, `:3087`, `:3121-3122`); `[ERROR: Error querying knowledge base]` on `/api/v1/retrieval/query/collection` | `backend/open_webui/retrieval/utils.py:1264-1271` | Slim image with a local reranking model stored and hybrid search on | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Error getting doc {collection_name}: {e}` / `Failed to fetch collection {name}: {e}` | Log (exception) | `backend/open_webui/retrieval/utils.py:367-369`, `:839-841` | Reading a collection from the vector store failed | None | Not described elsewhere; vector store health (10.34) |
| `query_collection: %s collection(s) had failing queries: %s` / `query_collection_with_hybrid_search: %s collection(s) had failing queries: %s` | Log (error) | `backend/open_webui/retrieval/utils.py:779-785`, `:885-891` | Some collections could not be searched; the names are listed | None | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Cannot determine model snapshot path: {e}` | Log (exception) | `backend/open_webui/retrieval/utils.py:1755-1756` | A local model could not be found or downloaded | None | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `No valid scores found, check your reranking function. Returning original documents.` | Log (warning) | `backend/open_webui/retrieval/utils.py:1849-1850` | The reranker gave no scores (10.31); results keep their original order | None | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |

### 10.34 `retrieval/vector/` (Vector Store Clients)

Which store production uses is TO BE CONFIRMED (`tools/ground-truth.md`). In the standard image the
store's client is created when the server starts (`backend/open_webui/retrieval/vector/factory.py:100`),
so a "Start-up" row stops the whole application and appears only in the server log; users see the
site as unavailable. In the slim image the client is created on first use and the same failures
answer HTTP 503 (`:104-123`), which reaches users as a processing failure (10.7) or a chat without
sources. "Defensive" rows guard search filters and collection names against values MedIT GPT's own
code does not produce.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Slim requires PostgreSQL/pgvector for vector storage. Set VECTOR_DB=pgvector and PGVECTOR_DB_URL, or use the standard image.` | Error (HTTP 503) on first use | `backend/open_webui/retrieval/vector/factory.py:20-24` | Slim image with a vector store other than pgvector | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Unsupported vector type: {vector_type}` | Start-up (standard image) | `backend/open_webui/retrieval/vector/factory.py:96-97` | `VECTOR_DB` names a store the code does not know | Escalate | Not described elsewhere; the environment setting |
| `Configure PGVECTOR_DB_URL for remote vector storage.` | Error (HTTP 503) on first use | `backend/open_webui/retrieval/vector/factory.py:113-114` | Slim image without a PostgreSQL address for pgvector | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Unable to connect to configured vector database ({VECTOR_DB}): {exc}` | Error (HTTP 503) on first use | `backend/open_webui/retrieval/vector/factory.py:115-122` | Slim image: creating the store's client failed; `{exc}` is one of the start-up texts below | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Unsupported metadata filter for '{key}': {value}` | Internal; defensive | `backend/open_webui/retrieval/vector/utils.py:64-68` | A search filter in a form the store helpers do not support | None | Not described elsewhere |
| `Configure CHROMA_HTTP_HOST: embedded Chroma is unavailable in slim.` | Never shown | `backend/open_webui/retrieval/vector/dbs/chroma.py:34-35` | The Chroma client is created only by the factory, which in the slim image refuses every store but pgvector first (`backend/open_webui/retrieval/vector/factory.py:20-24`, `:83`) | None | Section 14 |
| `distance_strategy must be 'cosine' or 'euclidean'` | Start-up | `backend/open_webui/retrieval/vector/dbs/mariadb_vector.py:110-111` | MariaDB Vector with another distance setting | Escalate | Not described elsewhere |
| `MariaDBVectorClient requires mariadb+mariadbconnector:// (official MariaDB driver) to ensure qmark paramstyle and correct VECTOR binding.` | Start-up | `backend/open_webui/retrieval/vector/dbs/mariadb_vector.py:113-117` | MariaDB Vector with a database address for another driver | Escalate | Not described elsewhere |
| `VECTOR_LENGTH {self.vector_length} does not match existing vector column dimension {existing}. Cannot change vector size after initialization without migrating the data.` | Start-up | `backend/open_webui/retrieval/vector/dbs/mariadb_vector.py:207-210`, checked at `:135` | The vector length setting changed after data existed | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 (the pgvector form) |
| `Expected str, got {type(value).__name__}` / `Unsupported Milvus filter value type: {type(value).__name__}` / `Invalid Milvus metadata filter key: {key}` | Internal; defensive | `backend/open_webui/retrieval/vector/dbs/milvus.py:44`, `:55`, `:62` | A search filter value or key the Milvus client refuses | None | Not described elsewhere |
| `Cannot create Milvus collection without items to determine vector dimension.` / `Cannot create Milvus collection for upsert without items to determine vector dimension.` | Internal; not expected | `backend/open_webui/retrieval/vector/dbs/milvus.py:316`, `:354-356` | Saving zero chunks into a collection that does not exist yet (empty content is refused earlier, 10.7) | None | Not described elsewhere |
| `Invalid Milvus resource_id (collection name): {resource_id}` / `Invalid Milvus metadata filter key: {key}` / `Expected str for Milvus expression value, got {type(value).__name__}` / `Unsupported Milvus filter value type for key {key}: {type(value).__name__}` | Internal; defensive | `backend/open_webui/retrieval/vector/dbs/milvus_multitenancy.py:49`, `:55`, `:61`, `:309` | A collection name or search filter the multitenant Milvus client refuses | None | Not described elsewhere |
| `Vector dimension mismatch: configured {VECTOR_LENGTH} vs. {db_vector_length} in the database.` / `The 'vector' column type is not Vector.` / `The 'vector' column does not exist in the 'document_chunk' table.` | Never raised | `backend/open_webui/retrieval/vector/dbs/opengauss.py:157-163` | The openGauss length check is defined (`:144`) but nothing calls it | None | Section 14 |
| `Invalid Oracle metadata filter key: {key}` | Internal; defensive | `backend/open_webui/retrieval/vector/dbs/oracle23ai.py:72` | A search filter key the Oracle client refuses | None | Not described elsewhere |
| `{obj} is not JSON serializable` | Internal | `backend/open_webui/retrieval/vector/dbs/oracle23ai.py:391` | A value read from Oracle could not be turned into JSON | None | Not described elsewhere |
| `PGVECTOR_PGCRYPTO_KEY must be set when PGVECTOR_PGCRYPTO is enabled.` | Start-up (standard image); HTTP 503 on first use (slim) | `backend/open_webui/retrieval/vector/dbs/pgvector.py:143-144` | pgvector encryption is switched on without its key setting | Escalate | Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca) |
| `Existing pgvector index '{index_name}' uses method '{existing_method}' but configuration now requires '{index_method}'. Automatic rebuild is disabled to prevent long-running maintenance. Drop the index manually (optionally after tuning maintenance_work_mem/max_parallel_maintenance_workers) and recreate it with the new method before restarting Open WebUI.` | Start-up | `backend/open_webui/retrieval/vector/dbs/pgvector.py:220-225` | The pgvector index method setting changed after the index existed | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `The 'vector' column type does not match the expected type ('{expected_type.__name__}') for VECTOR_LENGTH {VECTOR_LENGTH}.` | Start-up | `backend/open_webui/retrieval/vector/dbs/pgvector.py:310-313`, checked at `:147` | The stored vector column has a different type from the one the length setting needs | Escalate | Not described elsewhere |
| `VECTOR_LENGTH {VECTOR_LENGTH} does not match existing vector column dimension {db_vector_length}. Cannot change vector size after initialization without migrating the data.` | Start-up | `backend/open_webui/retrieval/vector/dbs/pgvector.py:317-320` | The vector length setting changed after data existed | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `The 'vector' column does not exist in the 'document_chunk' table.` | Start-up | `backend/open_webui/retrieval/vector/dbs/pgvector.py:322` | The pgvector table exists without its vector column | Escalate | Not described elsewhere |
| `Required configuration missing: {", ".join(missing_vars)}` / `Failed to initialize Pinecone index: {e}` | Start-up | `backend/open_webui/retrieval/vector/dbs/pinecone.py:102`, `:128` | Pinecone settings missing, or its index unavailable | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `QDRANT_URI is not set. Please configure it in the environment variables.` | Start-up | `backend/open_webui/retrieval/vector/dbs/qdrant_multitenancy.py:59-60` | Multitenant Qdrant without an address | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `valkey-glide-sync is required when VECTOR_DB=valkey. Install it with: pip install valkey-glide-sync==2.3.1` | Start-up | `backend/open_webui/retrieval/vector/dbs/valkey.py:58-60` | Valkey chosen without its client package | Escalate | Not described elsewhere |
| `Invalid filter field name: {key}. Field names must start with a letter or underscore and contain only alphanumerics/underscores.` / `Unsupported filter operator {op} for key {key}. Supported operators: $in, $ne, $eq.` | Internal; defensive | `backend/open_webui/retrieval/vector/dbs/valkey.py:119-122`, `:136-138` | A search filter the Valkey client refuses | None | Not described elsewhere |
| `VALKEY_URL is required when VECTOR_DB=valkey. Set it to your Valkey server URL (e.g., valkey://localhost:6379).` | Start-up | `backend/open_webui/retrieval/vector/dbs/valkey.py:154-157` | Valkey chosen without an address | Escalate | Not described elsewhere |
| `Invalid VALKEY_DISTANCE_METRIC={VALKEY_DISTANCE_METRIC}. Must be one of: {", ".join(sorted(_VALID_DISTANCE_METRICS))}.` | Start-up | `backend/open_webui/retrieval/vector/dbs/valkey.py:166-169` | Unknown Valkey distance setting | Escalate | Not described elsewhere |
| `Failed to connect to Valkey at {host}:{port}: {e}` / `Failed to create batch write client for Valkey at {host}:{port}: {e}` / `Failed to ping Valkey at {host}:{port}: {e}` | Start-up | `backend/open_webui/retrieval/vector/dbs/valkey.py:200`, `:213`, `:218` | The Valkey server could not be reached | Escalate | Not described elsewhere |
| `Valkey core {self._format_version(version)} is below the minimum required version {self._format_version(MIN_VALKEY_VERSION)}. valkey-search 1.2.0 requires Valkey core 9.0.1 or later. Upgrade your server or use valkey-bundle:9.1.0-rc2+.` | Start-up | `backend/open_webui/retrieval/vector/dbs/valkey.py:277-281`, checked at `:222` | The Valkey server is too old | Escalate | Not described elsewhere |
| `The valkey-search module is not loaded on the Valkey server. This backend requires valkey-search >= {self._format_version(MIN_SEARCH_MODULE_VERSION)}. Use valkey-bundle:9.1.0-rc2+ or load libsearch.so via --loadmodule on a Valkey 9.0.1+ server.` | Start-up | `backend/open_webui/retrieval/vector/dbs/valkey.py:317-321`, checked at `:223` | The Valkey server lacks its search module | Escalate | Not described elsewhere |
| `valkey-search {self._format_version(search_version)} is below the minimum required version {self._format_version(MIN_SEARCH_MODULE_VERSION)}. Earlier versions lack the TEXT field type and filter-only FT.SEARCH support required by this backend. Upgrade to valkey-bundle:9.1.0-rc2+ or load valkey-search 1.2.0+ as a module.` | Start-up | `backend/open_webui/retrieval/vector/dbs/valkey.py:328-333` | The search module is too old | Escalate | Not described elsewhere |
| `Collection {collection_name} was created with dim={existing}, refusing to insert vectors with dim={dimension}. Recreate the collection (e.g., via VECTOR_DB_CLIENT.delete_collection) if you intend to switch embedding models.` | Processing failure (10.7) | `backend/open_webui/retrieval/vector/dbs/valkey.py:440-444`, checked at `:476` | Saving into a collection built with another embedding model's vector size (after an embedding model change) | Escalate | Not described elsewhere; the embedding change in `rag-retrieval-embeddings-and-vector-stores.md` |
| `Failed to connect to Weaviate: {e}` | Start-up | `backend/open_webui/retrieval/vector/dbs/weaviate.py:92-93` | The Weaviate server could not be reached | Escalate | Not described elsewhere |
| `Collection name must be a non-empty string` / `Could not sanitize collection name to be a valid Weaviate class name` | Internal; defensive | `backend/open_webui/retrieval/vector/dbs/weaviate.py:98`, `:109` | A collection name the Weaviate client cannot use | None | Not described elsewhere |

### 10.35 `retrieval/web/` (Web Search Providers)

A provider's failure reaches the person in one of two ways. The built-in `search_web` tool hands
the text to the model as `{"error": "<text>"}` (`backend/open_webui/tools/builtin.py:328-330`); the
classic search before a reply replaces it with `[ERROR: Something went wrong while searching the
web.]` (10.7). Several providers log the failure and return no results instead, so a broken
provider can look like "no results" (`[ERROR: No results found from web search]`, 10.7, or the
status `No search results found`, 10.20). The 19 provider files not named below raise or log no
message of their own; their failures pass on the underlying error's own text.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `azure-search-documents is required for Azure AI Search. Install it with: pip install azure-search-documents` | Tool result or internal | `backend/open_webui/retrieval/web/azure.py:42-49` | Azure AI Search chosen on a server without that package | Escalate | See `web-search-and-web-loading.md` section 10 |
| `Azure AI Search error: {ex}` | Log (error); the error is passed on | `backend/open_webui/retrieval/web/azure.py:122-124` | Azure AI Search refused or failed | Retry later | Not described elsewhere |
| `Error: {ex}` | Log (error); the error is passed on | `backend/open_webui/retrieval/web/bing.py:43-45` | Bing search refused or failed | Retry later | Not described elsewhere |
| `DDGS is unavailable in slim. Configure another web search provider in Admin Settings > Web Search.` | Tool result or internal | `backend/open_webui/retrieval/web/duckduckgo.py:29-32` | Slim image with DuckDuckGo (DDGS) as the engine | Escalate | See `web-search-and-web-loading.md` section 10 |
| `Firecrawl {method} {url} failed without a response` | Never raised | `backend/open_webui/retrieval/web/firecrawl.py:119-122` | After the retry loop; with the fixed retry count (`:17`) every path returns or raises its own error first | None | Section 14 |
| `Linkup search failed: {str(e)}` / `Linkup search error: {str(e)}` | Tool result or internal | `backend/open_webui/retrieval/web/linkup.py:69-74` | Network or HTTP error from Linkup, or any other Linkup failure | Retry later | See `web-search-and-web-loading.md` section 10 |
| ``No `rawData` in response body: {response_body}`` | Internal (logged `Error in search: {e}`; the search returns no results) | `backend/open_webui/retrieval/web/yandex.py:86-87`, caught at `:118-121` | Yandex answered without the expected data | Retry later | Not described elsewhere |
| `Error searching Exa: {e}`, `Error in External search: {e}`, `Error searching with Microsoft Web IQ API: {e}`, `Error searching with Perplexity API: {e}`, `Error searching with Perplexity Search API: {e}`, `Error searching Ollama: {e}`, `Error in Sougou search: {err}`, `Error in FireCrawl search: {e}` (in that order in the Source cell) | Log (error); the search returns no results | `backend/open_webui/retrieval/web/exa.py:55-56`, `backend/open_webui/retrieval/web/external.py:59-60`, `backend/open_webui/retrieval/web/microsoft_web_iq.py:57-58`, `backend/open_webui/retrieval/web/perplexity.py:99-100`, `backend/open_webui/retrieval/web/perplexity_search.py:67-68`, `backend/open_webui/retrieval/web/ollama.py:51-52`, `backend/open_webui/retrieval/web/sougou.py:50-51`, `backend/open_webui/retrieval/web/firecrawl.py:230-232` | The provider refused or failed; the person sees "no results" instead of an error | Retry later; report if every search finds nothing | Not described elsewhere; the provider's key and status |

### 10.36 `retrieval/external.py` and the Remaining Retrieval Files

External knowledge sources (an admin connects an outside Qdrant, Milvus or pgvector collection to a
knowledge base) raise these during retrieval. They are not turned into readable HTTP errors: in a
chat the reply ends up without sources (`No sources found`), and the admin test shows the router's
own texts (10.6). The other files in the package, `retrieval/vector/async_client.py`,
`retrieval/vector/main.py`, `retrieval/vector/type.py`, `retrieval/web/main.py` and
`retrieval/models/base_reranker.py`, raise or log no message (searched for `raise`, `HTTPException`
and logging calls).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Invalid {label}` (for example `Invalid table name`) | Internal (retrieval fails) | `backend/open_webui/retrieval/external.py:83-86`, called at `:238-248` | A pgvector source's table or field name has characters the safe-name check refuses | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `qdrant-client is not installed` / `pymilvus is not installed` / `psycopg and pgvector are required for pgvector retrieval` | Internal (retrieval fails) | `backend/open_webui/retrieval/external.py:90-93`, `:137-140`, `:208-214` | The server lacks the provider's library | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Embedding function is not configured` | Internal (retrieval fails) | `backend/open_webui/retrieval/external.py:96`, `:143`, `:217` | No embedding function in this server process | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `External source collection is not configured` / `Milvus collection is not configured` / `pgvector collection is not configured` | Internal (retrieval fails) | `backend/open_webui/retrieval/external.py:101-103`, `:148-150`, `:222-224` | The source has no collection name | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `External knowledge connection is not configured` / `External knowledge connection not found` | Internal (retrieval fails) | `backend/open_webui/retrieval/external.py:299-306` | The link between the knowledge base and its connection is broken | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `External knowledge connection is disabled` | Internal (retrieval fails) | `backend/open_webui/retrieval/external.py:320-321` | The source's switch is off | Ask an admin | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Unsupported external knowledge provider: {connection.get("provider")}` | Internal (retrieval fails) | `backend/open_webui/retrieval/external.py:361-362` | The stored provider is not one the code knows | Escalate | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it matches the text, explains it, gathers identifiers and escalates. It does
not change files, knowledge bases, models, settings, permissions or sharing. Never ask a user for
passwords, keys or tokens, and never copy chat or document contents into a ticket; MedIT GPT chats
and documents may hold health information. Each pattern below points to the section 10 rows that
explain the individual texts.

### 11.1 "It says my file is too large or not supported"

**Symptom.** A red pop-up when uploading, for example `Oops! The file you're trying to upload is too
large. Please upload a file that is less than {max_size} MB.` or `[ERROR: File type
{file_extension} is not allowed]`; or a yellow pop-up after the upload such as `File type
{content_type} is not supported for processing` or `400: Document archive is too large after
decompression`; or, for a voice recording, `Oops! It seems like the file format you're trying to
upload is not supported. Please upload a file with a supported format and try again.`

**Likely causes, in order.**

1. The file is over the site's upload limit (`rag.file.max_size`, stated in megabytes in the
   message; the code default is no limit, `backend/open_webui/config.py:983`; live value **TO BE
   CONFIRMED**) (`backend/open_webui/routers/files.py:394-400`; for linked files
   `backend/open_webui/routers/retrieval.py:2286-2311`).
2. The extension is not in the allowed list (`rag.file.allowed_extensions`; the code default is an
   empty list, which allows every type, `backend/open_webui/config.py:998-1000`; live value **TO BE
   CONFIRMED**) (`backend/open_webui/routers/files.py:354-362`).
3. An image or other media file was uploaded for processing where extraction is not set up for its
   type (`backend/open_webui/routers/files.py:187`, 10.5).
4. A compressed Office or e-book file expands beyond the limit
   (`backend/open_webui/retrieval/loaders/main.py:520-539`, 10.30).
5. The slim image with the default extraction engine and a type that needs a parser
   (`backend/open_webui/retrieval/loaders/main.py:700-712`; whether production uses the slim image is
   **TO BE CONFIRMED**).
6. For dictation or calls: the recording's type or extension is not accepted for transcription
   (`backend/open_webui/routers/audio.py:1264-1281`, 10.13).

**Diagnostic steps** (read-only).

1. Get the exact text and whether it was a red or yellow pop-up, plus the file's type and size (not
   the file itself).
2. Note where the upload happened: the chat composer, a knowledge base (name and link), or a web link.
3. Match the text in 10.5, 10.7, 10.13 or 10.30. For the size message, compare the file size with the
   number in the message.
4. Ask whether the same file type of a smaller size uploads; if no file uploads at all, treat it as
   11.5 or a platform problem.

**Resolution.** Guidance only: use a smaller file or split it; save the document in a common text
format (for example PDF with a text layer, or Word); attach pictures directly in the chat composer
rather than to a knowledge base; for recordings, try another browser.

**Escalation.** Send the exact text, the time with time zone, the file type and size, where it was
uploaded (knowledge base name or chat link) and the browser address. Ask the platform maintainer
whether the limit or allowed types are intended. Do not attach the file if it may contain personal
or health information.

### 11.2 "It says 'We could not find what you're looking for :/'"

**Symptom.** A red pop-up or an empty page with `We could not find what you're looking for :/`.

**Likely causes, in order.**

1. The item was deleted (chat, folder, file, knowledge base, note, prompt, skill, tool, model,
   automation): almost every router answers this text with HTTP 404 (10.1 to 10.12, 10.15).
2. The item exists but the person may not see it. Most routers deliberately give a private item and a
   deleted item the same answer (4.1); files also answer it when the person may not read them
   (`backend/open_webui/routers/files.py`, 10.5).
3. A feature was switched off while the page was open, for example **Memories**
   (`backend/open_webui/routers/memories.py:38-41`, 10.12), or the text-to-speech engine changed to
   `Web API` before the page was reloaded (`backend/open_webui/routers/audio.py:607-610`, 10.13).
4. A file's stored bytes are gone although its record remains (`backend/open_webui/routers/files.py`,
   10.5).

**Diagnostic steps** (read-only).

1. Get the browser address; its path names the area (table 2.1) and usually contains the item's id.
2. Ask the person to reload the page and check whether the item still appears in their own list.
3. Ask whether the item was theirs or shared with them, and by whom.

**Resolution.** Reload the page. If the item belonged to someone else, ask the owner to share it again
or send a copy. If a feature disappeared, explain that the page reflects the site settings after a
reload.

**Escalation.** Send the browser address, the time and what the person clicked. The maintainer can
check whether the item exists and who owns it; tier 1 does not look items up in the database.

### 11.3 "It says the model was not found"

**Symptom.** `Model not found` as a pop-up or in the error box; `Model '' was not found` (sometimes
in the error box under a complete answer); `Model '{model}' was not found` from Ollama; or an
automation's run error `400: Model not found`.

**Likely causes, in order.**

1. The model was removed or renamed at the provider, or its connection was switched off
   (`backend/open_webui/routers/openai.py:1540-1552`; `backend/open_webui/routers/ollama.py:1081-1092`;
   10.18, 10.19).
2. The person no longer has access to the model or to its base model; the refusal is deliberately
   worded as "not found" and the server log names the reason (`Model access denied: ...`,
   `backend/open_webui/utils/models.py:465-521`, 10.22).
3. A workspace model whose base model has gone (10.22; `workspace-models-and-model-access.md`).
4. The server's model list was briefly empty, for example just after an admin saved the connections;
   background tasks then report `Model '' was not found` (10.18;
   `chat-completion-pipeline-and-generation-tasks.md` section 10).
5. An automation still names a model that has gone (10.25).

**Diagnostic steps** (read-only).

1. Get the exact text, the model name as shown in the picker, and the chat link.
2. Ask the person to reload and look for the model in the picker.
3. Ask whether a colleague in the same group can use the same model (access problem versus a removed
   model).
4. For an automation, ask for the automation's name and the time of the failed run.

**Resolution.** Pick a listed model, or edit the automation to use one. If the model should be
available, escalate; tier 1 does not change sharing.

**Escalation.** Send the model name, chat link or automation name, time, and whether others are
affected. The maintainer reads the `Model access denied` log line (which contains a user id, so the
log extract is personal data).

### 11.4 "It says duplicate content detected"

**Symptom.** `Duplicate content detected. Please provide unique content to proceed.` as a yellow
pop-up after an upload, or `400: Duplicate content detected. Please provide unique content to
proceed.` when adding a file to a knowledge base.

**Likely causes, in order.**

1. The same document is already in that knowledge base under another file entry: the check compares
   a fingerprint of the **extracted text**, not the file name, and only refuses when the match
   belongs to a different file (`backend/open_webui/routers/retrieval.py:2069`, `:2108-2112`,
   `:1734-1753`).
2. Two different files whose extraction produced the same text, for example two scans that both
   produced no text and were stored with the same placeholder sentence (read from code: the
   fingerprint is of the stored text; 10.30 lists the placeholder sentences).
3. The person uploaded the file again after an earlier attempt that did succeed.

**Diagnostic steps** (read-only).

1. Get the knowledge base's name and link and the file's name.
2. Ask the person (or the knowledge base's owner) to look in the knowledge base's file list for a
   file with the same content.
3. If the file is a scan, ask whether the earlier file was also a scan (cause 2).

**Resolution.** Use the existing copy. If the old copy is wrong, the knowledge base's owner removes it
first and then adds the new one. For scans, see 11.5.

**Escalation.** Send the knowledge base name and id, the file names and the time. The server log has
`Document with hash %s already exists` (`backend/open_webui/routers/retrieval.py:1752`).

### 11.5 "My document uploaded, but the answers say there is no text or quote an error"

**Symptom.** Either a yellow pop-up after the upload with a processing failure (often with a status
number in front, for example `504: MinerU processing timed out after 10 minutes`), or a file that
looks processed while the model answers that the document is empty, says `No sources found`, or
quotes a sentence such as `No text content found`, `<No text content found>`, `Error during
processing: {e}` or `Error during OCR processing: {e}`.

**Likely causes, in order.**

1. A scanned document with no text layer and no text recognition configured: extraction finds no
   text and the file fails with `The content provided is empty. Please ensure that there is text or
   data present before proceeding.` (`backend/open_webui/routers/retrieval.py:1819-1820`, 10.7).
2. The extraction engine failed or timed out; the text names the engine (`Error calling Tika`,
   `Error calling Docling`, `MinerU ...`, `Datalab Marker ...`, `Error loading document: ...`)
   (10.30).
3. Mistral OCR or PaddleOCR-vl, and Tika or Docling when they return nothing, store a short sentence
   as the document's text instead of failing, so the file looks processed but holds only that
   sentence (`backend/open_webui/retrieval/loaders/mistral.py:286-293`, `:341-353`, `:391-403`;
   `backend/open_webui/retrieval/loaders/paddleocr_vl.py:101-127`;
   `backend/open_webui/retrieval/loaders/main.py:244`, `:305`; 10.30).
4. Embedding failed (engine refused, local model not loaded): every upload fails the same way
   (10.33).
5. The vector store is unreachable (10.34), which affects every upload and search.

**Diagnostic steps** (read-only).

1. Get the exact pop-up text, or a screenshot of the answer, the file's type and whether it is a
   scan.
2. Identify the engine from the text (table above; 5.2).
3. Ask whether a small plain-text file uploads and is answered correctly. If it is not, the problem
   is site-wide (causes 4 and 5): escalate as an incident.

**Resolution.** Ask for a text-based version of the document, or paste the relevant passage into the
chat. Do not retry a large file repeatedly while an engine is timing out.

**Escalation.** Send the exact text, the file type and size, the knowledge base name or chat link,
the time, and whether other files fail. Name the engine if the text names it. Do not send the
document.

### 11.6 "The reply shows an error from the AI provider"

**Symptom.** The error box under the reply (often below `Uh-oh! There was an issue with the
response.`) shows a provider's words, for example a quota or key message in the provider's own
format; or `Open WebUI: Server Connection Error`; `Ollama: {e}`; `External: {msg}` from speech
services; or `Provider returned HTTP {status_code}`. On the admin **Connections** tab the same
problem shows `OpenAI: Network Problem` or `Ollama: Network Problem`.

**Likely causes, in order.**

1. The provider could not be reached or timed out: `Open WebUI: Server Connection Error` (the words
   "Open WebUI" remain because the licence comment protects this identifier,
   `backend/open_webui/constants.py:127-130`) (10.18, 10.19, 10.13).
2. The provider refused the request: an invalid or expired key, a quota or rate limit, a model it no
   longer offers, or a request too long for the model. Its own words are passed through unchanged
   (`backend/open_webui/routers/openai.py:1694`, `:1706-1709`, `:1736-1738`;
   `backend/open_webui/utils/middleware.py:4230-4255`, `:5226-5248`; 10.18, 10.20).
3. A function or pipe that the chat passes through raised its own error (10.20;
   `functions-pipes-filters-actions-and-pipelines.md`).
4. For speech and transcription: the speech service refused (`External: {msg}`) or was unreachable
   (10.13).

**Diagnostic steps** (read-only).

1. Get the exact text and the model name; note any provider prefix (5.2).
2. Ask whether other models work. If every model on one connection fails, the connection is the
   problem; if one model fails, that model.
3. Ask whether it repeats after a minute (rate limits clear; outages do not).

**Resolution.** Retry later, try another model, or shorten the request. Tier 1 never sees or changes
provider keys.

**Escalation.** Send the exact text, model name, chat link, time, and whether other people or models
are affected. Several users at once is an incident for the platform maintainer.

### 11.7 "It just says 'Something went wrong :/'"

**Symptom.** A red pop-up (or an automation run error) with only `Something went wrong :/`.

**Likely causes, in order.**

1. A refusal without explanation. In channels, notes and automations the text is used with HTTP 403
   for "not a member" or "no access" (10.3, 10.4, 10.15); in chats and models with HTTP 401 for acting
   on an item that is not the person's (10.1, 10.8); posting into a chat the person does not own
   answers it with HTTP 404 (`chat-completion-pipeline-and-generation-tasks.md` section 10).
2. An unexpected failure where the code supplies no reason: `ERROR_MESSAGES.DEFAULT` with a bare
   exception gives this text (4.2), for example image creation or editing that failed for a reason
   other than an engine error status (10.14), or saving pasted text for retrieval (10.7).
3. A storage problem shows a storage text instead (`[ERROR: The server is out of storage space.]` and
   the others in 4.2), so a plain `Something went wrong :/` is usually not a full disk.

**Diagnostic steps** (read-only).

1. Ask what the person was doing, on which screen, and get the browser address (table 2.1 names the
   subsection to read).
2. If the person can open the browser's developer tools, the status number (403, 401, 404 or 400/500)
   tells a refusal from a failure (3.1).
3. For a refusal, ask who owns the item and whether the person is a member (channels) or was given
   access (notes).

**Resolution.** For a refusal, ask the owner or a channel's creator for access. For a failure, retry
once; if it repeats, escalate.

**Escalation.** Send the time with time zone, the screen and action, the browser address and the
status number if known. The maintainer matches the time against the server log, which records the
exception behind most of these.

## 12. Local Customisations

**The message texts in this catalogue match upstream v0.11.4.** Read-only
`git diff main...uoft` over every file in scope (the 19 routers listed in 2.1, the eight helpers in
`backend/open_webui/utils/`, all of `backend/open_webui/retrieval/` and `backend/open_webui/tools/`,
and `backend/open_webui/constants.py`) shows no change, and `git diff` shows no uncommitted change in
`backend/open_webui/`. The fork's backend changes are elsewhere (`env.py`, `models/users.py`,
`utils/notifications.py` and the static images; `tools/ground-truth.md`).

Three fork changes still matter when reading these messages:

| Change | Effect on the messages in this catalogue | Evidence |
|---|---|---|
| Product name `MedIT GPT` (default `WEBUI_NAME`) | None of the texts in section 10 contain the product name. `Open WebUI: Server Connection Error` keeps the upstream name because the licence comment protects that identifier (section 4); the pgvector index text also says `before restarting Open WebUI` (10.34) | `backend/open_webui/env.py:951`; `backend/open_webui/constants.py:127-130`; `backend/open_webui/retrieval/vector/dbs/pgvector.py:220-225` |
| **Hide Processing Details** (per-user Interface setting) | When a person turns it on, status lines are hidden, tool-call entries are hidden except calls waiting for approval or an answer, and code-execution output is hidden, so the **Status**, **Tool result** and **Code output** rows (10.20, 10.26 to 10.29) are not visible to that person. The error box under a reply is still shown. The person may turn the setting off in **Settings > Interface** to see the details; tier 1 does not change it for them | `backend/open_webui/models/users.py:100`; `src/lib/components/chat/Messages/ResponseMessage.svelte:197-199`, `:930-931`, `:944`; `src/lib/components/common/ToolCallDisplay.svelte:199`; `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte:94-99`; `src/lib/i18n/locales/en-US/translation.json:2923-2924` |
| **Inline Citations** (per-user Interface setting) | No effect on any message here | `backend/open_webui/models/users.py:99` |

The working tree's uncommitted front-end changes (rule 10 of `_research-prompt.md`) touch how the
reply shows tool calls, approvals and status while processing details are hidden, and reword the
**Hide Processing Details** description in `en-US` (`src/lib/i18n/locales/en-US/translation.json:2923`).
They do not change any backend text, the error box (`src/lib/components/chat/Messages/Error.svelte`)
or the rule that marks a tool result as failed (`src/lib/components/common/ToolCallDisplay.svelte:94-134`).

## 13. Source File Index

Section 10 subsections are one per source file for routers, helpers and tools, and one per
sub-package for `retrieval/` (with one row per message per file inside).

| File | Section | What it contributes |
|---|---|---|
| `backend/open_webui/constants.py` | 4, 10 (all) | Text of every `ERROR_MESSAGES` constant and the `DEFAULT` builder (`:6-23`, `:37-132`) |
| `backend/open_webui/routers/chats.py` | 10.1 | Chat history, sharing, tags, compaction and forking refusals |
| `backend/open_webui/routers/folders.py` | 10.2 | Folder refusals and failures |
| `backend/open_webui/routers/channels.py` | 10.3 | Channel, message and webhook texts |
| `backend/open_webui/routers/notes.py` | 10.4 | Notes refusals |
| `backend/open_webui/routers/files.py` | 10.5, 10.14 | Upload, file store and file-content texts |
| `backend/open_webui/routers/knowledge.py` | 10.6 | Knowledge base and external connection texts |
| `backend/open_webui/routers/retrieval.py` | 10.7 | Processing, settings, web and search texts; wrappers for loader errors |
| `backend/open_webui/routers/models.py` | 10.8 | Workspace model texts |
| `backend/open_webui/routers/prompts.py` | 10.9 | Prompt texts |
| `backend/open_webui/routers/skills.py` | 10.10 | Skill texts |
| `backend/open_webui/routers/tools.py` | 10.11 | Workspace tool texts |
| `backend/open_webui/routers/memories.py` | 10.12 | Memory route texts |
| `backend/open_webui/routers/audio.py` | 10.13 | Speech-to-text and text-to-speech texts |
| `backend/open_webui/routers/images.py` | 10.14 | Image generation, editing and settings texts |
| `backend/open_webui/routers/automations.py` | 10.15 | Automation refusals and schedule errors |
| `backend/open_webui/routers/calendar.py` | 10.16 | Calendar refusals |
| `backend/open_webui/routers/terminals.py` | 10.17 | Terminal pass-through answers and close reasons |
| `backend/open_webui/routers/openai.py` | 10.18 | OpenAI-compatible connection texts |
| `backend/open_webui/routers/ollama.py` | 10.19 | Ollama connection texts |
| `backend/open_webui/utils/middleware.py` | 10.20 | Chat pipeline error boxes, error statuses and tool results |
| `backend/open_webui/utils/chat.py` | 10.21 | Model routing and direct-connection errors |
| `backend/open_webui/utils/models.py` | 10.22 | Model access refusal and its log lines |
| `backend/open_webui/utils/files.py` | 10.23 | No user-facing text; one printed line |
| `backend/open_webui/utils/memory.py` | 10.24 | Memory operation validation |
| `backend/open_webui/utils/automations.py` | 10.25 | Run errors and scheduler log lines |
| `backend/open_webui/utils/code_interpreter.py` | 10.26 | Jupyter engine output errors |
| `backend/open_webui/utils/tools.py` | 10.27 | Terminal and tool-server call errors |
| `backend/open_webui/tools/builtin.py` | 10.28 | Built-in tool results |
| `backend/open_webui/tools/knowledge_fs.py` | 10.29 | `kb_exec` results |
| `backend/open_webui/retrieval/loaders/main.py`, `local.py`, `pdf.py`, `datalab_marker.py`, `external_document.py`, `mineru.py`, `mistral.py`, `paddleocr_vl.py` | 10.30 | Extraction engine texts and texts stored as document content |
| `backend/open_webui/retrieval/models/colbert.py`, `external.py` | 10.31 | Reranker checks and log lines |
| `backend/open_webui/retrieval/web/utils.py`; `backend/open_webui/retrieval/loaders/youtube.py`, `tavily.py`, `external_web.py`, `microsoft_web_iq.py` | 10.32 | Web page and YouTube loading |
| `backend/open_webui/retrieval/utils.py` | 10.33 | Embedding, search and reranking helpers |
| `backend/open_webui/retrieval/vector/factory.py`, `utils.py` and `dbs/*.py` | 10.34 | Vector store start-up and runtime texts |
| `backend/open_webui/retrieval/web/*.py` (providers) | 10.35 | Search provider texts and log lines |
| `backend/open_webui/retrieval/external.py` | 10.36 | External knowledge retrieval texts |
| `backend/open_webui/main.py` | 3.1, 10.21, 10.22 | Recurrence time-out handler (`:515-517`); chat request error wrapping (`:1638-1645`, `:1686-1710`, `:2103-2107`) |
| `backend/open_webui/models/calendar.py`, `backend/open_webui/utils/recurrence.py` | 3.1, 10.15, 10.16 | Recurrence rule texts passed through by the automation and calendar routers |
| `backend/open_webui/models/memories.py`, `backend/open_webui/utils/chat_fork.py`, `backend/open_webui/utils/validate.py`, `backend/open_webui/utils/anthropic.py`, `backend/open_webui/routers/configs.py` | 10.1, 10.8, 10.12, 10.18, 10.27 | Inner texts passed through by routers in scope |
| `pyproject.toml`, `backend/requirements.txt` | 10.18, 10.30, 10.32 | The pinned FastAPI version; which optional packages the standard image installs |
| `src/lib/apis/chats/index.ts`, `src/lib/apis/openai/index.ts`, `src/lib/apis/ollama/index.ts`, `src/routes/+layout.svelte` | 2.2, 3.2, 10.18, 10.19 | How the browser prints server texts and handles 401 answers |
| `src/lib/components/chat/Chat.svelte`, `src/lib/components/chat/Messages/ResponseMessage.svelte`, `src/lib/components/chat/Messages/Error.svelte`, `src/lib/components/common/ToolCallDisplay.svelte`, `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte` | 2.2, 2.3, 12 | Error box, tool-call display and the Hide Processing Details behaviour |

## 14. Open Questions

### 14.1 Messages That Can Never Be Shown (Read From Code)

| Message | Why it never reaches a user | Evidence |
|---|---|---|
| `OpenAI API was not found` | The legacy `/openai/audio/speech` route passes the message **function** instead of calling it; the web framework's error handler cannot serialize a function, so the caller receives a bare server error. Checked by running the handler against the pinned FastAPI 0.136.3 in the project's virtual environment (no application, no database). This settles the "probably a generic server error … TO BE CONFIRMED" note in `model-connections-openai-ollama-and-direct.md` section 10.2, which this document does not edit | `backend/open_webui/routers/openai.py:672-673`; `backend/open_webui/constants.py:90`; `pyproject.toml:9` |
| Anthropic **Verify** refusal (`{result['error']}`, for example `HTTP Error: 401`) | Raised inside the same `try` whose general handler replaces it with `Open WebUI: Server Connection Error` | `backend/open_webui/routers/openai.py:1118-1124`, `:1149-1151` |
| `PaddleOCR-vl API URL and Token are required.` | The only caller chooses this engine only when both settings are present | `backend/open_webui/retrieval/loaders/paddleocr_vl.py:27-28`; `backend/open_webui/retrieval/loaders/main.py:688-697` |
| `Configure CHROMA_HTTP_HOST: embedded Chroma is unavailable in slim.` | The factory refuses every store except pgvector in the slim image before the Chroma client is created. **Possible contradiction:** `rag-retrieval-embeddings-and-vector-stores.md` section 10.1 lists this text as a slim-image error | `backend/open_webui/retrieval/vector/dbs/chroma.py:34-35`; `backend/open_webui/retrieval/vector/factory.py:20-24`, `:80-83` |
| The three openGauss length-check texts | `check_vector_length` is defined but never called | `backend/open_webui/retrieval/vector/dbs/opengauss.py:144-163` |
| `retry count exceeded` | The last attempt re-raises its own error first, and the only caller uses the default of three attempts | `backend/open_webui/retrieval/web/utils.py:976`, `:985-1012` |
| `No valid URLs to process after SSL verification` (raised form) | Raised only when failures may not be skipped; the only caller always allows skipping, so the warning form is logged instead | `backend/open_webui/retrieval/web/utils.py:535-539`, `:1073-1079` |
| `At least one URL must be provided.` | The Tavily loader is created only after at least one address passed | `backend/open_webui/retrieval/loaders/tavily.py:45-46`; `backend/open_webui/retrieval/web/utils.py:535-545` |
| `Firecrawl {method} {url} failed without a response` | With the fixed retry count every path returns or raises its own error first | `backend/open_webui/retrieval/web/firecrawl.py:17`, `:85-122` |
| `Azure OpenAI embedding request failed: max retries (429) exceeded`, and the copies of the embedding texts at `:926`, `:1001`, `:1069`, `:1075` | They sit in three synchronous helpers that nothing in the repository calls | `backend/open_webui/retrieval/utils.py:899`, `:963`, `:1002`, `:1045` |
| `Terminal server {server_id} not found for CWD set` and the two `Failed to set terminal CWD` log lines | The helper is never called, and it would stop at its first step because nothing sets the application attribute it reads | `backend/open_webui/utils/automations.py:202-247` |

Messages that are reachable only in unusual set-ups or are defensive (not expected in normal use):
`Invalid file path detected` (`backend/open_webui/routers/audio.py:1294`); `Configure an external
text-to-speech engine. Local TTS is unavailable in slim.` (`:328`, `:519`); `Unsupported memory
operation: {action}` (`backend/open_webui/utils/memory.py:279`); the ColBERT shape checks
(`backend/open_webui/retrieval/models/colbert.py:40-45`); `API key cannot be empty.` and `Provide
exactly one of api_key or azure_credential.` (only when a key setting is missing rather than empty);
the `unstructured` package texts (not in the standard image); the `youtube_transcript_api` import text
(a core dependency); and the "Defensive" filter and collection-name rows in 10.34.

### 14.2 Values and Facts the Code Cannot Settle (TO BE CONFIRMED)

1. Production upload limit (`rag.file.max_size`) and allowed extensions (`rag.file.allowed_extensions`);
   the code defaults are no limit and no restriction, so whether users can meet the 11.1 refusals at
   all is a data question.
2. Whether production runs the standard or the slim image: every "slim" row depends on it.
3. Which vector store, extraction engine, embedding engine, reranker, web search provider, web loader,
   speech engines, image engine and model connections production uses; each decides which rows of
   10.13 to 10.36 can occur.
4. Who can read the server log, and how long it is kept: many rows end in "server log" (shared with
   `tools/ground-truth.md`).
5. The support contact for escalations (shared with `tools/ground-truth.md`).

### 14.3 Gaps in Coverage

1. **Grouping of `retrieval/`.** The brief asked for one subsection per source file. The package has
   71 Python files, and sections 3.3, 5.2, 7 and 8 (written before this continuation) already point to
   10.30 to 10.36 for the loader, reranker, embedding, vector-store and provider texts. The package was
   therefore grouped into seven subsections by sub-package, with one row per message per file inside,
   so those references hold.
2. **Rows 10.1 to 10.12 were not re-verified line by line** in this continuation; the citation,
   quote and PII checks pass for the whole document, and one claim in 3.1 was corrected after the
   calendar time-out handling was traced.
3. **Status lines** are listed only where they carry an error (10.20). The in-chat status catalogue
   (area 32 in `_areas.md`) does not exist yet.
4. **Front-end wrappers.** How every front-end screen prints each backend text was established only
   where cited. On 2026-10-10 the area 30 catalogue (`error-messages-frontend-chat-and-navigation.md`)
   was being written in parallel and the area 31 catalogue
   (`error-messages-frontend-admin-workspace-and-settings`) did not exist yet; the cross-references
   from section 10 to them were not checked.
5. **Helpers outside the assigned scope** whose texts reach chat users (`utils/timers.py`,
   `utils/subagents.py`, `utils/tool_approval.py`, `utils/ask_user.py`, `utils/actions.py`,
   `utils/mcp/client.py`, `utils/images/comfyui.py`, `utils/recurrence.py`, `utils/chat_fork.py`,
   `utils/misc.py`, `socket/main.py`) are cited here only where a router in scope passes their text
   on; their own catalogues are in `builtin-native-tools.md`, `chat-completion-pipeline-and-generation-tasks.md`
   and `automations-calendar-and-timers.md`.
6. **Log lines** are included only when they explain a symptom; a full log-line catalogue for these
   files was not attempted.
7. **Security-sensitive items referred, not described:** the terminal pass-through path refusals
   (10.17), the server's address checks for web pages and images (10.32), the pgvector encryption key
   requirement (10.34), and one retrieval log line about refused collection names, which is not
   catalogued. Security-sensitive: refer to the platform maintainer and U of T Information Security
   (security.utoronto.ca).

### 14.4 Contradictions With Other Documents (Recorded, Not Changed Here)

1. `model-connections-openai-ollama-and-direct.md` section 10.2 marks the `OpenAI API was not found`
   outcome TO BE CONFIRMED; 14.1 above settles it from code and a framework check.
2. `rag-retrieval-embeddings-and-vector-stores.md` section 10.1 lists `Configure CHROMA_HTTP_HOST:
   embedded Chroma is unavailable in slim.` as reachable; 14.1 above finds it unreachable.
3. No contradiction with `tools/ground-truth.md` was found.
