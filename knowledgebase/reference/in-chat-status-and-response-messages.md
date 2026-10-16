# In-Chat Status, Progress and Error Text

## At a Glance

- While MedIT GPT writes a reply, the backend sends short **status lines** (grey progress lines such as "Searching the web" or "Retrieved N sources") over the websocket; the front end shows the latest one above the answer and keeps a clickable history.
- Many status lines carry an `action` code instead of finished text; the front end turns the code into translated English, so the same event can read differently in the admin's language. *Corrected 2026-10-10: the wording follows each viewer's own interface language (Settings > General), not the admin's; apart from four known texts, lines without an `action` code and every error text stay as the server sent them (section 5.3; `src/lib/components/chat/Settings/General.svelte:256`).*
- Errors that stop a reply are saved on the message and shown in a red **error box** under the answer; other failures appear as toasts, tool-call result text, or code-output text. *Corrected 2026-10-10: the error box is light grey with an (i) icon, not red; red appears only on the toast that some failures show at the same time (`src/lib/components/chat/Messages/Error.svelte:40-48`; sections 4 and 5.5).*
- The fork's **Hide Processing Details** setting replaces most of this progress text with a single "Thinking..." line (provisional; details in sections 7 and 12). *Updated 2026-10-10: full behaviour in section 5.9, the setting in 7.1, committed versus uncommitted parts in 12.1.*
- *Added 2026-10-10:* A failed **tool call** does not stop the reply: the card gets a red cross and the model carries on; a failed **reply** shows the error box, often under a partial answer (sections 5.5 and 5.6).
- *Added 2026-10-10:* `No sources found` can also mean the retrieval step failed, and `Open WebUI: Server Connection Error` means the server could not reach the model provider; neither is the person's fault (sections 10.1, 10.3 and 11).
- *Added 2026-10-10:* Nothing limits how long a reply may wait for the provider by default, so a stuck line or `Thinking...` stays until **Stop** or a reload (section 5.11).

## 1. Purpose and Who Uses It

This document is the catalogue of every piece of **progress, status and error text that appears inside a
chat response** in MedIT GPT, what each one means, whether it signals a problem, and where the deeper
explanation lives. It is written for tier-1 support staff who are shown a screenshot or read out a line
such as "it says Searching the web and then nothing".

Four kinds of text appear inside or around a response:

| Kind | What it looks like | Who produces it | Main source |
|---|---|---|---|
| **Status line** | One grey line above the answer, shimmering while the step runs; click it to see earlier steps | The server sends a `status` event over the websocket; the browser words it | `backend/open_webui/utils/middleware.py`; `src/lib/components/chat/Messages/ResponseMessage/StatusHistory.svelte:30-76`; `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:13-151` |
| **Processing blocks** | Collapsible lines inside the answer: reasoning (`Thinking...`, `Thought for ...`), code analysis (`Analyzing...`, `Analyzed`), tool-call cards, and the grouped `Exploring` / `Explored` line | The browser, from the structured output the model streams | `src/lib/components/common/Collapsible.svelte:96-122`; `src/lib/components/common/ToolCallDisplay.svelte:199-370`; `src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte:146-232` |
| **Error box** | A rounded, light-grey box with an (i) icon under whatever part of the answer arrived | The server saves `error.content` on the message, or the browser catches a failed request | `src/lib/components/chat/Messages/Error.svelte:37-48`; `src/lib/components/chat/Messages/ResponseMessage.svelte:930-932` |
| **Toast** (pop-up) | A short notice in a corner of the screen that disappears by itself | The browser, for request failures, context compaction and plugin notifications | `src/lib/components/chat/Chat.svelte:1173-1199`, `:1354-1366`, `:3643-3668`, `:3716-3756` |

Who meets these texts:

- **Every person who chats.** Status lines and processing blocks are shown by default; the MedIT GPT
  setting **Hide Processing Details** replaces them with a single `Thinking...` line (section 12).
- **Tier-1 support**, who use this catalogue to tell normal progress from a fault, and to decide what to
  ask for before escalating.
- **The platform maintainer and model administrators**, who can change which steps run (function-calling
  mode, web search, image generation, knowledge, tools) and so which lines appear (section 7).

Neighbouring documents explain the machinery in depth; this document points to them rather than
repeating them: `chat-completion-pipeline-and-generation-tasks.md` (the request lifecycle),
`chat-composer-and-message-display.md` (the chat screen), `web-search-and-web-loading.md`,
`rag-retrieval-embeddings-and-vector-stores.md`, `builtin-native-tools.md`,
`code-execution-and-interpreter.md`, `error-messages-backend-chat-content-and-features.md` and
`user-settings-and-personalisation.md`.

## 2. Navigation and URLs

These texts have no page of their own; they appear wherever a response is drawn. Paths are relative to
the site root; the production host name is **TO BE CONFIRMED**.

| Where | Path | What appears there | Source |
|---|---|---|---|
| A new chat | `/` | All in-response texts for the first reply | `src/routes/(app)/+page.svelte` |
| An existing chat | `/c/{id}` | All in-response texts; saved status lines and errors reappear on reload | `src/routes/(app)/c/[id]/+page.svelte` |
| Settings > Interface > Chat | `/?settings=interface` | The **Hide Processing Details** and **Always Expand Details** switches | `src/lib/components/common/InterfaceSettings.svelte:1312-1378`; `user-settings-and-personalisation.md` section 2 |
| Workspace > Models > edit a model | `/workspace/models/edit` | The model's **Status Updates** capability, which hides status lines for that model | `src/routes/(app)/workspace/models/edit/+page.svelte`; `src/lib/components/workspace/Models/Capabilities.svelte:49-52` |
| Chat > Controls > Advanced Params | side panel in a chat | **Function Calling** (`Default`, `Native`, `Legacy`), which decides whether web search, image generation and model knowledge show as status lines or as tool cards (section 4) | `src/lib/components/chat/Settings/Advanced/AdvancedParams.svelte:240-270` |
| A channel where a model replies | `/channels/{id}` | Model output with the same processing blocks; a failure becomes the message text `Error: {error_content}` | `backend/open_webui/socket/main.py:1126-1129`; `channels-and-direct-messages.md` |

**Server endpoints behind these texts** (for escalation notes; tier 1 does not call them):

| Endpoint | Role here | Source |
|---|---|---|
| `POST /api/chat/completions` | Starts a reply; its immediate failure produces a toast and an error box | `backend/open_webui/main.py:1108`; `src/lib/components/chat/Chat.svelte:3577-3668` |
| Websocket `/ws/socket.io`, event `events` | Carries `status`, `context_compaction`, `chat:message:error`, `chat:completion` and plugin events to the browser | `backend/open_webui/socket/main.py:1134-1162`; `src/lib/components/chat/Chat.svelte:1202-1427` |
| `POST /api/v1/chats/{id}/messages/{message_id}/resolve` | **Allow** / **Deny** on a tool call and ask-user answers; its refusals appear as toasts | `backend/open_webui/main.py:1893`; `backend/open_webui/utils/tool_approval.py:20-128` |
| `POST /api/v1/chats/{id}/messages/{message_id}/event` | Lets the chat owner or an admin (for example an integration) push any event, including a status line, into a message | `backend/open_webui/routers/chats.py:1513-1548` |
| `POST /api/tasks/chat/{chat_id}/stop` | The Stop button; ends the running steps | `backend/open_webui/main.py:2160` |

## 3. Roles and Permissions

The texts themselves need no permission: anyone who can run a chat (role `user` or `admin`) sees the
status lines and errors of their own replies. What permissions and switches change is **which steps run**,
and therefore which lines can appear.

| What | Effect on in-chat text | Source |
|---|---|---|
| Role `pending` | Cannot chat, so sees none of these texts (see `authentication-and-sign-in.md`) | `knowledgebase/tools/ground-truth.md` (Accounts and Access) |
| Permission `features.web_search` plus the site switch `web.search.enable` | Without both, the legacy web-search steps (`Searching the web` and the rest) are skipped; admins skip the permission check | `backend/open_webui/utils/middleware.py:2700-2709` |
| Permission `features.image_generation` | Without it, the legacy image steps (`Creating image` and the rest) are skipped; admins skip the check | `backend/open_webui/utils/middleware.py:2711-2720` |
| Permission `settings.interface` (default on) | Without it the user cannot open Settings > Interface, so cannot change **Hide Processing Details** themselves; the server also discards Interface fields they try to save | `backend/open_webui/config.py:1935`; `src/lib/components/chat/SettingsModal.svelte:393-395`; `backend/open_webui/routers/users.py:492-498` |
| Chat owner or admin | Only they can answer **Allow** / **Deny** or an ask-user card on a chat; anyone else gets `You do not have permission to access this resource. Please contact your administrator for assistance.` | `backend/open_webui/utils/tool_approval.py:27-32` |
| Chat owner or admin | Only they can push events into a message through the event endpoint | `backend/open_webui/routers/chats.py:1522-1534` |
| Admins opening another user's chat | See that chat's saved status lines and error boxes as saved; whether admins may open other chats depends on `ENABLE_ADMIN_CHAT_ACCESS` | `knowledgebase/tools/ground-truth.md` (Admin visibility defaults) |

Model administrators (people who may edit a model in Workspace > Models) control the model's
**Status Updates**, **Citations**, **File Context** and **Builtin Tools** capabilities and its default
Function Calling parameter, which change what appears (section 7). Who holds that right in production is
**TO BE CONFIRMED** (see `workspace-models-and-model-access.md`).

## 4. Key Concepts and Terminology

| Term | Meaning | Source |
|---|---|---|
| **Status event** | A websocket message of type `status` whose data holds `description` (text), `action` (a code the browser turns into words), `done` (finished or not), optional `hidden`, `error`, `query`, `queries`, `urls`, `items`, `count` | `backend/open_webui/utils/middleware.py:1561-1728`, `:2091-2165`; `src/lib/components/chat/Messages/ResponseMessage.svelte:84-97` |
| **Status history** | The list of every status event a reply received, kept on the message as `statusHistory`; the newest entry is the visible line, older ones show when the line is clicked | `backend/open_webui/models/chats.py:1239-1272`; `src/lib/components/chat/Messages/ResponseMessage/StatusHistory.svelte:18-76` |
| **Action code** | A short code in a status event (`web_search`, `web_search_queries_generated`, `queries_generated`, `sources_retrieved`, `knowledge_search`, `context_compaction`) that the browser maps to translated English | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:15-148` |
| **Shimmer** | The moving highlight on a line whose step is still running (`done` is `false`) | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:19-21`, `:129-131` |
| **Hidden status** | A status with `hidden: true`. When it is the newest entry, the whole status line and its history disappear | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory.svelte:21-31`; `src/lib/components/chat/Messages/ResponseMessage.svelte:200-201` |
| **Processing details** (MedIT GPT term) | Status lines, reasoning blocks, code-analysis blocks, tool-call cards, code execution chips and the task list, which **Hide Processing Details** removes | `src/lib/i18n/locales/en-US/translation.json:2923-2924` |
| **Error box** | The rounded grey box under a reply that shows `error.content`; it is not red | `src/lib/components/chat/Messages/Error.svelte:40-48` |
| **Toast** | A pop-up notice from the `svelte-sonner` library (`toast.error`, `toast.success`, `toast.loading`) | `src/lib/components/chat/Chat.svelte:1173-1199` |
| **Function Calling: Native / Legacy** | How tools reach the model. **Native** (the server default) offers web search, image generation, knowledge and code as built-in tools the model calls, shown as tool-call cards. **Legacy** runs web search, image generation and model knowledge before the model answers, shown as status lines | `backend/open_webui/main.py:1290-1294`; `backend/open_webui/utils/middleware.py:2608`, `:2708-2709`, `:2719-2720`, `:2809-2813` |
| **Tool-call card** | One row per tool the model called, with a spinner, tick or cross and a label such as `Executing {NAME}...` | `src/lib/components/common/ToolCallDisplay.svelte:199-288` |
| **Tool result text** | What a tool returned; visible under **Output** when a card is opened. Text starting `Error:` (and similar) turns the card's icon into a red cross | `src/lib/components/common/ToolCallDisplay.svelte:94-158`, `:328-366` |
| **Ask-user card** | Questions from the `ask_user` tool, shown above the composer, not inside the answer | `src/lib/components/chat/AskUserCard.svelte`; `chat-composer-and-message-display.md` section 5.18 |
| **Approval pause** | With tool permissions set to ask, the reply stops before each tool call until the user clicks **Allow** or **Deny** | `backend/open_webui/utils/middleware.py:5928-5948`, `:3613-3655` |
| **Context compaction** | Summarizing older turns when a chat grows past a token threshold; announced by toasts, not status lines | `backend/open_webui/utils/context_compaction.py:75-144`; `src/lib/components/chat/Chat.svelte:1166-1199` |
| **Add-on** | A function, tool or pipe installed by an admin. Add-ons can send their own status lines, toasts, confirmation and input dialogs, with any wording | `src/lib/components/chat/Chat.svelte:1354-1401`; `functions-pipes-filters-actions-and-pipelines.md` |

## 5. Workflows (Step by Step)

### 5.1 What a Response Looks Like, Top to Bottom

The browser draws each assistant reply in this fixed order (`src/lib/components/chat/Messages/ResponseMessage.svelte`):

| Order | Part | Shown when | Source |
|---|---|---|---|
| 1 | Model name | Always, except in compact previews | `src/lib/components/chat/Messages/ResponseMessage.svelte:707-715` |
| 2 | **Status line** (newest status, click for history) | Hide Processing Details is off, the model's Status Updates capability is on (default), the reply has status events, and the newest one is not hidden | `src/lib/components/chat/Messages/ResponseMessage.svelte:198-202`, `:720-722` |
| 3 | Images and files attached to the reply (for example a legacy-mode generated image) | The reply carries image or file items | `src/lib/components/chat/Messages/ResponseMessage.svelte:724-746` |
| 4 | Embeds sent by tools or add-ons | Not in read-only views | `src/lib/components/chat/Messages/ResponseMessage.svelte:748-763` |
| 5 | The answer, with **processing blocks** in the order the model produced them (reasoning, tool calls, code analysis, text) | The reply has content, unless it is an old-style error reply (`error: true`) | `src/lib/components/chat/Messages/ResponseMessage.svelte:857-918`; `src/lib/components/chat/Messages/ContentRenderer.svelte:290-350` |
| 6 | **`Thinking...`** (MedIT GPT) or a thin blinking bar | The reply is still running (section 5.9 for `Thinking...`); the bar shows while text streams, or when no status line is visible | `src/lib/components/chat/Messages/ResponseMessage.svelte:920-928` |
| 7 | **Error box** | The message has an `error` | `src/lib/components/chat/Messages/ResponseMessage.svelte:930-932` |
| 8 | Sources (citation chips) | The reply has sources and the model's Citations capability is on | `src/lib/components/chat/Messages/ResponseMessage.svelte:934-941` |
| 9 | Code execution chips | An add-on reported code runs, and Hide Processing Details is off | `src/lib/components/chat/Messages/ResponseMessage.svelte:944-946` |
| 10 | Action buttons, then follow-up suggestions | The reply has finished | `src/lib/components/chat/Messages/ResponseMessage.svelte:950-1660`; `chat-composer-and-message-display.md` sections 5.12 and 5.19 |

The error box sits **below** any text that arrived before the failure, so a reply can show a partial or
even complete answer with an error under it (`src/lib/components/chat/Messages/ResponseMessage.svelte:857-859`
keeps the content on screen "even if there's an error"). Old chats that stored the error as the message
text itself (`error: true`) show only the box.

### 5.2 The Order of Status Lines During One Reply

The server runs the preparation steps in a fixed order inside `process_chat_payload`
(`backend/open_webui/utils/middleware.py:2391-3276`; overview comment at `:2396-2398`). Which steps
produce status lines depends on the **Function Calling** mode, which is `native` unless the chat or the
model sets `legacy` (`backend/open_webui/main.py:1290-1294`).

**Native mode (the default).** Web search, image generation, model knowledge and code are offered to
the model as built-in tools, so they appear as tool-call cards (5.4), not status lines
(`backend/open_webui/utils/middleware.py:2708-2709`, `:2719-2720`, `:2608`, `:2809-2813`). A reply can show:

1. A toast `Compacting context`, then `Context compacted` (or `Context compaction failed`), when automatic
   compaction runs before anything else (`backend/open_webui/utils/middleware.py:2481-2513`;
   `src/lib/components/chat/Chat.svelte:1173-1199`). These are pop-ups, not status lines.
2. If files are attached (and the model's File Context capability is on): `Querying` with the search
   queries as chips, unless every file is in full-context mode, then `Retrieved {count} sources`,
   `Retrieved 1 source` or `No sources found` (`backend/open_webui/utils/middleware.py:2049-2167`,
   `:3203-3213`).
3. If the model has knowledge attached: a final **hidden** `knowledge_search` status, which makes the
   status line disappear (`backend/open_webui/utils/middleware.py:3248-3259`; section 5.3).
4. The model's answer streams: reasoning, tool-call cards and text (5.4). Add-ons may add their own
   status lines at any point (5.10).

**Legacy mode.** The same steps plus these, in this order:

1. `Searching Knowledge for "{query}"` when the model has knowledge attached; it is sent before the
   filters run (`backend/open_webui/utils/middleware.py:2604-2644`).
2. Web search, when the user turned it on in the composer and is allowed to:
   `Searching the web` → `Searching` with query chips (or `No search query generated`) →
   `Searched {count} sites` (click to list the pages) or an error line such as
   `[ERROR: No results found from web search]` (`backend/open_webui/utils/middleware.py:1560-1730`).
3. Image generation, when turned on: `Creating image` (saved chats only) → `Image created` or
   `An error occurred while generating an image` (`backend/open_webui/utils/middleware.py:1828-2046`).
4. Tools chosen by the task model run without status lines (`backend/open_webui/utils/middleware.py:3196-3203`).
5. Files and knowledge: `Querying` → `Retrieved {count} sources` / `No sources found`, as in native mode.
6. The hidden `knowledge_search` status, then the model's answer.

Each step's line replaces the previous one as the visible line; the earlier lines stay in the history.
A step that is turned off, not permitted, or not applicable produces no line at all.

### 5.3 How the Browser Words a Status Line

The browser chooses the text from the status event's `action`, falling back to the server's
`description` (`src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:13-151`):

| Status event | Text shown | Extras | Source |
|---|---|---|---|
| `action: web_search` with `urls` or `items` | The description translated, with `{{count}}` filled from the number of pages, so `Searched {{count}} sites` reads, for example, "Searched 5 sites" | Click to expand: the query (a link to Google) and one link per page with its site icon. *Corrected 2026-10-10: the core web-search event carries `urls` and `items` but no `query` (`backend/open_webui/utils/middleware.py:1688-1700`), so the Google search link appears only when an add-on's status includes `query`; the site icons are loaded from Google's favicon service (`WebSearchResults.svelte:27-29`, `:71`, `:111`).* | `StatusItem.svelte:15-39`; `src/lib/components/chat/Messages/ResponseMessage/WebSearchResults.svelte:13-143` |
| `action: knowledge_search` | `Searching Knowledge for "{{searchQuery}}"` with the user's message as the query | None | `StatusItem.svelte:40-51` |
| `action: web_search_queries_generated` | `Searching` | One chip per search query | `StatusItem.svelte:52-77` |
| `action: queries_generated` | `Querying` | One chip per retrieval query; an empty list shows no chips | `StatusItem.svelte:78-103` |
| `action: sources_retrieved` | `No sources found` (count 0), `Retrieved 1 source` (count 1), `Retrieved {{count}} sources` (more) | None | `StatusItem.svelte:104-125` |
| Any other status | The description; the four texts `Searching "{{searchQuery}}"`, `No search query generated`, `Generating search query` and `Searching the web` are translated, every other description is shown exactly as sent (English, including error details) | None | `StatusItem.svelte:126-148` |
| `hidden: true` | Nothing | When it is the newest entry the whole status line and history disappear | `StatusItem.svelte:13`; `src/lib/components/chat/Messages/ResponseMessage/StatusHistory.svelte:30-31` |

Things the code does **not** do, which explains common confusion:

- A status sent with `error: true` looks exactly like any other line: grey, no icon, no colour
  (`StatusItem.svelte:126-148` reads no `error` field). Web-search failures therefore read as ordinary
  grey status lines.
- The history list under the line appears only when there are two or more entries, and starts closed
  (`src/lib/components/chat/Messages/ResponseMessage/StatusHistory.svelte:10-16`, `:46-73`).
- A line shimmers only while its `done` is `false`; a step that never sends a finishing event keeps
  shimmering on screen until another line replaces it (`StatusItem.svelte:19-21`, `:129-131`).
- Because a hidden newest entry hides the whole block, a model with knowledge attached loses its visible
  `Querying` / `Retrieved {count} sources` line once preparation finishes (the hidden
  `knowledge_search` entry is sent last, `backend/open_webui/utils/middleware.py:3248-3259`). When the
  browser catches a reply error it also removes the `knowledge_search` entries
  (`src/lib/components/chat/Chat.svelte:3749-3753`). Observed from the code only; section 14.

### 5.4 Processing Blocks While the Model Answers

These come from the reply's structured `output` (or, for older replies, `<details>` blocks in the
text) and are labelled by the browser, not the server (`src/lib/components/chat/Messages/structuredOutput.ts:194-443`;
`src/lib/components/chat/Messages/StructuredOutputRenderer.svelte:74-228`;
`src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte:440-560`).

| Block | While running | When finished | Source |
|---|---|---|---|
| Reasoning (thinking models) | `Thinking...` with a spinner | `Thought for less than a second`, `Thought for {{DURATION}} seconds` (under a minute), `Thought for {{DURATION}}` (a humanized length such as "2 minutes"), or `Thought` when no duration was recorded | `src/lib/components/common/Collapsible.svelte:89-113` |
| Code analysis (code interpreter) | `Analyzing...` with a spinner | `Analyzed`; open it to see the code and its output | `src/lib/components/common/Collapsible.svelte:114-119`; `code-execution-and-interpreter.md` |
| Tool call card | `Preparing {{NAME}}...` (arguments still arriving), then `Executing {{NAME}}...` | `View Result from {{NAME}}` with a green tick, or a red cross when the call failed or its result looks like an error; `Denied {{NAME}}` with a red cross after **Deny** | `src/lib/components/common/ToolCallDisplay.svelte:150-158`, `:213-255` |
| Tool waiting for approval | `Allow {{NAME}}?` with **Allow** and **Deny** | As above | `src/lib/components/common/ToolCallDisplay.svelte:248-276` |
| Ask-user call | `Input needed` | `View Result from ask_user` | `src/lib/components/common/ToolCallDisplay.svelte:142-147`, `:246-247`. *Corrected 2026-10-10: in current replies (structured `output`) a waiting or in-progress ask-user call is not drawn in the answer at all (`src/lib/components/chat/Messages/structuredOutput.ts:396-402`); `Input needed` appears only on replies drawn from `<details>` text, such as older replies or some pipes.* |
| Several blocks in a row | `Exploring` with a spinner, followed by tool names (with counts such as `2 search_web`) and `Ran {{COUNT}} analysis` / `Ran {{COUNT}} analyses` | `Explored` with a tick, or a red cross if any call failed or was denied | `src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte:97-232` |

Points that matter for support:

- `{{NAME}}` is the tool's internal function name, for example `search_web`, `fetch_url`,
  `generate_image`, `query_knowledge_files` or `execute_code` for built-in tools
  (`backend/open_webui/tools/builtin.py:294`, `:333`, `:370`, `:3151`, `:633`), and
  `{server_id}_{tool_name}` for MCP tools (`backend/open_webui/utils/middleware.py:2994-3003`).
  A delegated task reads `Sub-agent: "{task}"` or `Background sub-agent: "{task}"`
  (`src/lib/components/chat/Messages/structuredOutput.ts:202-214`).
- On a narrow screen or narrow side-by-side column the card shows only the bare tool name with its icon;
  the full label appears from the medium container width up
  (`src/lib/components/common/ToolCallDisplay.svelte:238-255`).
- Opening a card shows **Input** (the arguments) and **Output** (the result, cut at 10,000 characters
  with `Show all ({{COUNT}} characters)`) (`src/lib/components/common/ToolCallDisplay.svelte:290-366`).
- The red cross means the tool call **failed or returned an error-looking result**; the model usually
  carries on and explains (`src/lib/components/common/ToolCallDisplay.svelte:94-135`, `:158`). It is not an
  error box and the reply is not stopped.
- With **Always Expand Details** on, these blocks start open (`src/lib/components/chat/Messages/StructuredOutputRenderer.svelte:125`, `:132`, `:185`, `:192`).

### 5.5 When a Reply Fails: How Text Reaches the Error Box

The error box (`src/lib/components/chat/Messages/Error.svelte:40-48`) shows one piece of text: the
message's `error.content`, or for old-style replies (`error: true`) the message text itself
(`src/lib/components/chat/Messages/ResponseMessage.svelte:930-931`). When the content is an object the
box picks, in order, `error.message`, `detail`, `message`, and otherwise prints the object as JSON;
when it is empty the box reads `Error submitting message`, which is hard-coded English and not
translated (`Error.svelte:6-37`). The text sits in one paragraph with no line breaks kept, so a
two-line error reads as one line (`Error.svelte:45-47`).

There are five ways text gets there:

| # | What failed | What the user sees | Saved on the message? | Source |
|---|---|---|---|---|
| 1 | **The request to start the reply was refused** before any work began (for example the model was removed: `Model not found`; or the request was malformed) | A red toast with the server's text, and the same text in the error box of an empty reply | No. The server refuses before it stores the message pair, so the error lives only in the open browser tab (observed from code, section 14) | `backend/open_webui/main.py:1129`, `:1182`, `:1640-1645`; `src/lib/apis/openai/index.ts:3-14`, `:437-448`; `src/lib/components/chat/Chat.svelte:3641-3667` |
| 2 | **The preparation steps or the provider call raised an error** after the reply started (provider unreachable, provider returned an HTTP error, a filter refused, a pipe crashed) | The error box shows the server's text, for example `Open WebUI: Server Connection Error` or the provider's own message; no toast for this path | Yes: `error.content` and `done` are stored on the reply | `backend/open_webui/main.py:1659-1712`; `backend/open_webui/utils/misc.py:43-65`; `src/lib/components/chat/Chat.svelte:1284-1292` |
| 3 | **The provider sent an error inside the stream** (quota, content filter, context too long) | A red toast with the provider's message, and the error box reads `Uh-oh! There was an issue with the response.` followed by that message | Yes, but the stored copy is the provider's raw error, so after a reload the box shows the provider's message **without** the `Uh-oh!` prefix | `backend/open_webui/utils/middleware.py:5072-5091`, `:5226-5249`; `src/lib/components/chat/Chat.svelte:2799-2800`, `:3716-3754` |
| 4 | **A non-streaming provider reply carried an error** | The error box shows the provider's error detail | Yes | `backend/open_webui/utils/middleware.py:4231-4255` |
| 5 | **A later step failed while the answer was already under way**: a follow-up model call after a tool call, the code-interpreter follow-up, the tool-call iteration limit, or an MCP server that could not be reached | The error box appears under the partial answer; for the first three the answer then stops where it was | Yes for the first three (`emit_message_error` stores it); the MCP line is sent to the screen only and is not stored | `backend/open_webui/utils/middleware.py:4855-4867`, `:6328-6346`, `:6527-6536`, `:3006-3013` |

What the user sees in each case, and the exact wording, is in section 10. Points for support:

- **The text is usually not MedIT GPT's own.** In paths 2 to 4 the box repeats what the model provider
  or an add-on said, in the provider's language (often English), so the same fault can read
  differently on different models. `get_response_error_detail` digs through nested `error`,
  `message` and `detail` fields and falls back to `Provider returned HTTP {status_code}` or
  `Provider returned an error` when the provider's body cannot be read
  (`backend/open_webui/utils/misc.py:43-65`).
- **`Open WebUI: Server Connection Error`** names the upstream product even in MedIT GPT. It is a
  licence-protected identifier: the code carries the comment "LICENSE covers this Open WebUI error
  identifier" and the fork has left it unchanged (`backend/open_webui/constants.py:127-130`). It means
  the server could not get an answer from the model provider at all (connection refused, timeout,
  name lookup failure), not that the user's browser lost the server (`backend/open_webui/routers/openai.py:1746-1751`).
- **A toast without an error box** comes from elsewhere in the chat screen (for example file
  uploads or context compaction); see `error-messages-frontend-chat-and-navigation.md`.
- **In a channel**, the same failure becomes the model's message text `Error: {error_content}`
  instead of an error box (`backend/open_webui/socket/main.py:1126-1129`).
- **Over the API without a chat** (no `chat_id`), a stream that breaks mid-way ends with the error
  object `Chat completion stream failed` instead (`backend/open_webui/utils/middleware.py:6644`,
  `:6707-6711`); see `public-api-and-integrations` when that document exists.

### 5.6 Tool Calls That Fail, and the Approval Pause

**A failed tool call does not stop the reply.** The server catches the failure, hands the model a
result text that starts with `Error:` (or a JSON object with an `error` field), and asks the model to
carry on; the model usually explains the problem in its answer. The browser marks such a card with a
red cross because the result "looks like an error" (`src/lib/components/common/ToolCallDisplay.svelte:94-135`,
`:158`; `backend/open_webui/utils/middleware.py:5981-6028`).

The browser treats a result as an error when the text starts with `error:`, `exception:`,
`traceback` or `http error!` (any capitals), or when it is JSON with a non-empty `error`, a `status`
of `error` or `failed`, or `success`/`ok` false together with a `message`
(`ToolCallDisplay.svelte:94-135`; the grouped line repeats the same test,
`src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte:54-93`). A tool that
returns a polite failure in plain words ("I could not find that file") gets a green tick, and a tool
whose correct answer happens to start with "Error:" gets a red cross.

The server's own result texts for tool-call failures are listed in section 10 (for example
`Error: Tool "{name}" not found.` when the model calls a tool that is not available in this chat).
Built-in tools add their own result texts; those are catalogued in `builtin-native-tools.md`.

**The approval pause.** When an administrator has switched on **Tool Permissions** (setting
`chat.tool_permissions.enable`, seeded from `ENABLE_TOOL_PERMISSIONS`, code default off;
`backend/open_webui/config.py:2196`, `:3138`; label and help text at
`src/lib/i18n/locales/en-US/translation.json:2532-2533`), the composer menu offers **Full access**
or **Ask for approval** (`src/lib/components/chat/MessageInput/InputMenu.svelte:57-62`,
`:146-150`). With **Ask for approval**:

1. The model asks for a tool. The server stores the call as `pending`, marks the reply not done, and
   stops (`backend/open_webui/utils/middleware.py:5936-5956`, `:3613-3655`).
2. The card reads `Allow {{NAME}}?` with **Allow** and **Deny** buttons; in a group of several calls
   the group line carries the buttons when exactly one call is waiting
   (`ToolCallDisplay.svelte:244-276`; `ConsecutiveDetailsGroup.svelte:234-240`). Other calls from the
   same turn wait as `queued`.
3. **Allow** queues the call and restarts the reply on the same message; the call keeps the status
   `queued` while it runs, so the card reads `Preparing {{NAME}}...` until the result arrives and it
   becomes `View Result from {{NAME}}` (`backend/open_webui/utils/tool_approval.py:60-64`;
   `backend/open_webui/main.py:1893-1910`; `backend/open_webui/utils/middleware.py:3454-3482`).
4. **Deny** stores the result `Error: tool call rejected by user.` for the model, and the card reads
   `Denied {{NAME}}` with a red cross (`backend/open_webui/utils/tool_approval.py:65-75`;
   `ToolCallDisplay.svelte:218-221`, `:242-243`). The model then answers without the tool.

Limits of the pause, from the code: it applies only to saved chats (`is_saved_chat_id`), not to
temporary chats, and never to automations or channels, which always run with full access
(`backend/open_webui/utils/middleware.py:5938-5942`; `backend/open_webui/main.py:1255-1264`). Only
the chat owner or an admin can answer (section 3). A second click on an answered card, or an answer
from a second tab, is refused with the toast `Tool call has already been resolved.`
(`backend/open_webui/utils/tool_approval.py:55-58`;
`src/lib/components/chat/Messages/StructuredOutputRenderer.svelte:43-63`). The other refusals of the
resolve endpoint are in section 10.

### 5.7 Questions and Dialogs That Interrupt a Reply

Some replies stop to ask the user something. None of these are error boxes.

| What appears | Where | Produced by | What happens on Cancel or timeout | Source |
|---|---|---|---|---|
| **Ask-user card**: one to three questions, each with two or three options marked by the model (one may be `Recommended`), an `Other` field (`Type your answer`), and `Previous`, `Next`, `Cancel`, `Submit answers` | Above the composer; nothing is drawn in the answer while it waits (older replies drawn from text show a card reading `Input needed`) | The built-in `ask_user` tool | In a saved chat the card waits with no time limit; **Cancel** denies the call, so the card reads `Denied ask_user` and the model receives `Error: tool call rejected by user.` | `src/lib/components/chat/AskUserCard.svelte:53-68`, `:227-297`; `src/lib/components/chat/Chat.svelte:559-638`; `backend/open_webui/utils/ask_user.py:25-80` |
| The same card, sent over the websocket (`request:user_input`) when the question did not go through the saved-chat path | Above the composer | The built-in `ask_user` tool run through the browser connection | Closes itself after the tool's time limit (60 to 240 seconds, default 120) and reports `cancelled` to the model | `backend/open_webui/tools/builtin.py:586-621`; `src/lib/components/chat/Chat.svelte:1402-1408`, `:625-638`; `AskUserCard.svelte:58-68` |
| **Add-on confirmation**: a dialog with the add-on's own title and message, and confirm and cancel buttons | Centre of the screen | A function or tool sending a `confirmation` event | Cancel tells the add-on "no" (`false`); what the add-on then does is its own code | `src/lib/components/chat/Chat.svelte:1367-1375`, `:4249-4268` |
| **Add-on input**: the same dialog with a text box or options | Centre of the screen | A function or tool sending an `input` event | Cancel returns `false` to the add-on | `src/lib/components/chat/Chat.svelte:1390-1401`, `:4249-4268` |
| `Confirm Prompt from Embed` with the prompt text | Centre of the screen | An embedded tool view inside a reply that asks to send a prompt on the user's behalf | Nothing is sent | `src/lib/components/chat/Chat.svelte:1455-1466`, `:1487-1498` |

The ask-user rules the model must follow (one ask-user call on its own per turn, one to three
questions, two or three options each) are enforced on the server; a call that breaks them is not
shown as a card but as a tool card whose result starts with `Error:` (section 10)
(`backend/open_webui/utils/ask_user.py:9-22`, `:83-149`). The ask-user flow in the composer is
described in `chat-composer-and-message-display.md` section 5.18.

### 5.8 Code Output and Code Errors Inside a Reply

Code that runs during a reply shows its result in one of three places. The full behaviour (engines,
time limits, packages) is in `code-execution-and-interpreter.md`; this table is only about where
error text appears.

| Where | Mode | Where the error text shows | What a tick or cross means | Source |
|---|---|---|---|---|
| Tool card `execute_code` | Native function calling (the default) | Open the card: **Output** holds JSON with `stdout`, `stderr` and `result`; a Python error (traceback) is in `stderr` | The card has a **green tick even when the code raised an error**, because the tool reports `status: success` with the error in `stderr`; a red cross appears only when the tool itself failed (`{"error": ...}`, for example `Unknown code interpreter engine: {engine}`) | `backend/open_webui/tools/builtin.py:782-792`, `:742`; `src/lib/components/common/ToolCallDisplay.svelte:94-135` |
| `Analyzing...` / `Analyzed` block | Legacy function calling with the code interpreter on | Open the block: the code, then its output below it | No tick or cross; a line that stays at `Analyzing...` means the run has not reported back | `src/lib/components/common/Collapsible.svelte:114-119`; `src/lib/components/chat/Messages/CodeBlock.svelte:409-419` |
| Code execution chips under the reply, and their window with `ERROR`, `OUTPUT` and `Files` | Only when an add-on reports code runs | The chip's window | A cross icon on the chip when the run has an `error`, a tick when it has `output`, three dots when it has neither, a spinner while waiting | `src/lib/components/chat/Messages/CodeExecutions.svelte:28-63`; `src/lib/components/chat/Messages/CodeExecutionModal.svelte:75-104` |

A code block the **user** runs with the **Run** button is not part of the reply's processing: its
output and errors (for example `Execution Time Limit Exceeded`) appear under that code block. See
`code-execution-and-interpreter.md` sections 10.1 and 11.2.

### 5.9 What Hide Processing Details Shows ("Thinking...")

**Hide Processing Details** is a MedIT GPT per-person switch in Settings > Interface (section 12 for
where it came from). Its help text reads:

`Show "Thinking..." instead of status updates, tool calls, reasoning, and code analysis while a response is generated, and keep them hidden afterwards. Tool approval requests and images or embeds from tools still appear.`

(`src/lib/components/common/InterfaceSettings.svelte:1358-1378`;
`src/lib/i18n/locales/en-US/translation.json:2923-2924`). An admin's **Default Interface Settings**
preset can set the starting value for people who have not chosen (`user-settings-and-personalisation.md`
section 5.6; `src/lib/components/chat/SettingsModal.svelte:446-449`).

With the switch on, the code does this:

| Part of the reply | With the switch on | Source |
|---|---|---|
| Status line and its history | Not drawn at all, for every status, including web-search errors and add-on lines | `src/lib/components/chat/Messages/ResponseMessage.svelte:198-202`, `:720-722` |
| `Thinking...` | One shimmering grey line, drawn by the same status component, shown while the reply is not finished, has no error, has no visible answer text yet, and is not waiting on a tool call that needs the user | `src/lib/components/chat/Messages/ResponseMessage.svelte:207-221`, `:920-921`; `src/lib/components/chat/Messages/structuredOutput.ts:454-457` |
| Reasoning blocks, code-analysis blocks and the grouped `Exploring` / `Explored` line | Removed, during and after the reply | `src/lib/components/chat/Messages/structuredOutput.ts:404-415`; `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte:90-104` |
| Tool-call cards | Hidden unless the call is waiting for **Allow** / **Deny** or for an ask-user answer; images a tool returns and tool embeds still show (the embed's small name label is hidden) | `src/lib/components/common/ToolCallDisplay.svelte:178-199`, `:372-388` |
| `<status title="…">` tags an add-on writes into the answer text | Removed | `src/lib/components/chat/Messages/Markdown/HTMLToken.svelte:89-104` |
| Code execution chips | Removed | `src/lib/components/chat/Messages/ResponseMessage.svelte:944-946` |
| Task list above the composer | Removed | `src/lib/components/chat/MessageInput.svelte:1792` |
| Error box, toasts, sources, ask-user card, add-on dialogs | **Still shown** (the switch does not touch them) | `src/lib/components/chat/Messages/ResponseMessage.svelte:930-941` |

Consequences for support:

- With the switch on, a reply that is stuck shows only `Thinking...`, so the person cannot tell
  which step stalled. Ask them to turn the switch off and reload the chat: saved status lines come
  back, because the switch only hides them (`src/lib/components/chat/Messages/ResponseMessage.svelte:198-202`;
  status lines are stored with the message, section 6).
- `Thinking...` disappears as soon as the first answer text arrives, so a slow answer after that
  shows the thin blinking bar instead (`ResponseMessage.svelte:920-928`).
- The same English word `Thinking...` is also the running label of a reasoning block (5.4), which
  this switch hides. With the switch off, `Thinking...` therefore means a thinking model is
  reasoning; with it on, it means "the reply has not produced answer text yet".

### 5.10 Status Lines and Notices from Add-ons

Functions, tools and pipes installed by an admin receive an event emitter and can send any event the
built-in steps send, with their own wording (`backend/open_webui/socket/main.py:1134-1250`;
`functions-pipes-filters-actions-and-pipelines.md`). Support should treat any status line not
listed in section 10 as add-on text.

| What the add-on sends | What the user sees | Saved? | Source |
|---|---|---|---|
| `status` with its own `description` | A grey status line, shown exactly as sent (not translated, no error colour even with `error: true`) | Yes, in the status history | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:126-148`; `backend/open_webui/socket/main.py:1166-1171` |
| `status` with `hidden: true` | Hides the whole status line while it is the newest entry | Yes | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory.svelte:30-31` |
| `<status title="…" done="false">` written into the answer text by a pipe | A grey line inside the answer, shimmering until the pipe rewrites it with `done="true"` | As part of the text | `src/lib/components/chat/Messages/Markdown/HTMLToken.svelte:89-104` |
| `notification` with a type (`success`, `error`, `warning`, otherwise information) and `content` | A toast of that type with the add-on's text | No | `src/lib/components/chat/Chat.svelte:1354-1366` |
| `chat:message:error` | The error box with the add-on's text (it does not stop the reply unless `done` is sent too) | No, unless the add-on also writes the message | `src/lib/components/chat/Chat.svelte:1284-1292`; `backend/open_webui/socket/main.py:1134-1250` |
| `confirmation` or `input` | The dialogs in section 5.7 | No | `src/lib/components/chat/Chat.svelte:1367-1401` |
| `source` with type `code_execution` | Code execution chips (5.8) | Not by the server's event handler | `src/lib/components/chat/Chat.svelte:1328-1345`; `backend/open_webui/socket/main.py:1235-1250` |

The core application itself sends no `notification` events into chats: a search for
`'type': 'notification'` in `backend/open_webui` finds none, and the only notification-related line
in the event emitter drops notifications for internal runs (`backend/open_webui/socket/main.py:1146-1147`).
An integration (or the chat owner, or an admin) can also push any of these events into an existing
message through `POST /api/v1/chats/{id}/messages/{message_id}/event` (`backend/open_webui/routers/chats.py:1513-1548`).

### 5.11 Replies That Never Finish, Stopped Replies and Reloads

**No built-in time limit.** The server waits for the model provider for as long as it takes unless
the environment sets `AIOHTTP_CLIENT_TIMEOUT` (total) or `AIOHTTP_CLIENT_STREAM_IDLE_TIMEOUT` (gap
between pieces); both are unset by default, which means no limit
(`backend/open_webui/env.py:608-625`; `backend/open_webui/utils/session_pool.py:43-51`). A provider
that accepts the request but never answers therefore leaves the last status line, `Thinking...` or
the blinking bar on screen until someone presses **Stop**. The production values are **TO BE
CONFIRMED**.

**What Stop does** (`POST /api/tasks/chat/{chat_id}/stop`, `backend/open_webui/main.py:2160-2214`):

| Situation | Result on screen | Stored | Source |
|---|---|---|---|
| The reply is running | Steps still in progress are marked `incomplete`; the reply ends where it was | `done: true` and the cut-off output | `backend/open_webui/utils/middleware.py:6604-6631` |
| No task is running any more (for example the server restarted, or the reply is paused for approval) | The reply is closed; any call still waiting for **Allow** / **Deny** becomes `rejected` (`Denied {{NAME}}`) | `done: true` | `backend/open_webui/main.py:2174-2212` |

Two display quirks follow from the code (observed from code only, section 14):

- **A tool call cut off by Stop looks finished.** Its status becomes `incomplete`, which the card
  counts as done; with no result to test it shows `View Result from {{NAME}}` with a **green tick**
  and no **Output** (`src/lib/components/common/ToolCallDisplay.svelte:150-158`;
  `src/lib/components/chat/Messages/structuredOutput.ts:194-200`).
- **The visible status line is not closed by Stop.** The top line shimmers according to the
  status event's own `done` flag, and nothing sends a closing status, so a line such as
  `Searching the web` can keep shimmering on a stopped or interrupted reply
  (`src/lib/components/chat/Messages/ResponseMessage/StatusHistory.svelte:42`;
  `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:129-131`).

**Reloading during a reply.** Opening the chat again asks the server which tasks are still running.
If one is, the screen keeps waiting for it; if none is, the browser treats the newest reply as
finished (in its own copy only) unless an ask-user question is waiting, so spinners stop but the
stored message is unchanged (`src/lib/components/chat/Chat.svelte:2375-2412`). The same check runs
when the browser's live connection comes back after a drop (`src/lib/components/chat/Chat.svelte:1529-1552`).
Saved status lines and error boxes reappear on reload because they are stored with the message
(section 6); the toasts do not.

## 6. Data Model

These texts have no table of their own. They are fields of an assistant message, stored in the
chat's JSON history (`chat.chat` → `history.messages[<message id>]`) and copied to the message's row
in the `chat_message` table (`backend/open_webui/models/chats.py:1141-1190`;
`backend/open_webui/models/chat_messages.py:127-165`). The browser reads the JSON history when a chat
opens (`backend/open_webui/routers/chats.py:1325-1347`). Chats contain what people typed and what
the model answered, which can include personal and health information; tier 1 reads them only
through the application, never in the database.

### 6.1 Message Fields Behind the Texts

| Field (JSON key / `chat_message` column) | Holds | Written by | Source |
|---|---|---|---|
| `statusHistory` / `status_history` | Every status event's `data` in arrival order (section 6.2) | The server's event emitter on each `status` event, for saved chats only; the browser keeps its own copy while the chat is open | `backend/open_webui/socket/main.py:1164-1171`; `backend/open_webui/models/chats.py:1239-1272`; `src/lib/components/chat/Chat.svelte:1221-1226` |
| `status` | A single status on old replies (before `statusHistory`); still read for display | Older versions | `src/lib/components/chat/Messages/ResponseMessage.svelte:200` |
| `error` | `{content: …}`, where `content` is a string or the provider's error object; `true` on very old replies whose error text is the message content | The server (sections 5.5 and 10) or the browser after a failed request | `backend/open_webui/main.py:1693-1700`; `backend/open_webui/utils/middleware.py:4240-4247`, `:4855-4861`; `src/lib/components/chat/Chat.svelte:3658-3660`, `:3744-3746`; `backend/open_webui/models/chat_messages.py:155`, `:235-236` |
| `done` | `false` while the reply runs or waits for approval; `true` when finished, failed or stopped | Server | `backend/open_webui/models/chat_messages.py:153`; `backend/open_webui/utils/middleware.py:3634-3640` |
| `output` | The structured reply: `message`, `reasoning`, `function_call` (with a `status`), `function_call_output` (the tool result text), `open_webui:code_interpreter` items | Server | `src/lib/components/chat/Messages/structuredOutput.ts:7-26`, `:85-92` |
| `content` | The answer text; on old replies and some add-on pipes it also carries `<details>` and `<status>` tags | Server | `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte:63`; `src/lib/components/chat/Messages/Markdown/HTMLToken.svelte:89-104` |
| `code_executions` | Code runs an add-on reported (chips, 5.8) | Browser only: the server's event handler saves only sources without a type | `src/lib/components/chat/Chat.svelte:1328-1345`; `backend/open_webui/socket/main.py:1235-1250` |
| `contextSummary` / `context_summary` | The summary written by context compaction, on the message where compaction started | Server | `backend/open_webui/utils/context_compaction.py:113-123`; `backend/open_webui/models/chat_messages.py:161` |

Notes from the code:

- The status write itself updates only the JSON history; the `chat_message` row's
  `status_history` catches up the next time the message is upserted, which every later step of a
  reply does (`backend/open_webui/models/chats.py:1239-1272` has no dual write;
  `backend/open_webui/models/chats.py:1181-1190` does).
- **Temporary chats save nothing**: status lines and errors are sent to the screen only, because the
  emitter saves only when the chat id is a saved one (`backend/open_webui/socket/main.py:1144`).
- **Channels** do not show or save status lines: the channel emitter handles only reply text,
  files and errors, and turns an error into the message text `Error: {error_content}`
  (`backend/open_webui/socket/main.py:1071-1129`).
- **Shared links** copy the chat JSON at share time, so a shared reply shows the same status history
  and error box (`backend/open_webui/models/shared_chats.py:26`, `:81`, `:107`).
- With Redis, a reply still being written is also kept in a Redis hash so a reconnecting browser can
  catch up; it is cleared when the reply ends (`backend/open_webui/tasks.py:199-260`;
  `backend/open_webui/routers/chats.py:1340-1343`).

### 6.2 The Status Event

| Key | Meaning | Who sets it | Source |
|---|---|---|---|
| `action` | Code the browser words: `web_search`, `web_search_queries_generated`, `queries_generated`, `sources_retrieved`, `knowledge_search`; `context_compaction` travels as its own event type | Server, add-ons | `backend/open_webui/utils/middleware.py:1566`, `:1646`, `:2095`, `:2160`, `:2613`, `:3253`; `backend/open_webui/utils/context_compaction.py:76-84` |
| `description` | Text, used when no `action` applies, or as an i18n key such as `Searched {{count}} sites` | Server, add-ons | `StatusItem.svelte:26-36`, `:134-146` |
| `done` | `false` while the step runs (line shimmers), `true` when finished | Server, add-ons | `StatusItem.svelte:19-21` |
| `hidden` | `true` hides the whole status block while it is the newest entry | Server (`knowledge_search` at the end of preparation), add-ons | `backend/open_webui/utils/middleware.py:3248-3259`; `StatusHistory.svelte:30-31` |
| `error` | `true` on failures; **not used by the display** | Server (web search), add-ons | `backend/open_webui/utils/middleware.py:1709`, `:1725`; `StatusItem.svelte:13-151` |
| `query`, `queries` | The user's message, or the generated search or retrieval queries (shown as chips) | Server | `backend/open_webui/utils/middleware.py:1647`, `:2096`, `:2614` |
| `urls`, `items` | The pages a web search found (listed when the line is opened) | Server | `backend/open_webui/utils/middleware.py:1694-1696` |
| `count` | Number of distinct sources found in attached files and knowledge | Server | `backend/open_webui/utils/middleware.py:2142-2163` |

### 6.3 Tool-Call States in `output`

The card's wording follows the `function_call` item's `status` and whether a result exists
(`src/lib/components/chat/Messages/structuredOutput.ts:194-235`;
`src/lib/components/common/ToolCallDisplay.svelte:142-158`, `:240-254`):

| `status` | Result present? | Card reads | Icon |
|---|---|---|---|
| `in_progress` | No | `Preparing {{NAME}}...` | Spinner |
| `completed` | No | `Executing {{NAME}}...` | Spinner |
| `completed` | Yes, normal | `View Result from {{NAME}}` | Green tick |
| `failed` | Yes, error-looking (the server applies the same test as the browser) | `View Result from {{NAME}}` | Red cross |
| `pending` | No | `Allow {{NAME}}?` with **Allow** / **Deny**, or `Input needed` for `ask_user` on older replies drawn from text (current replies do not draw a waiting `ask_user`, `structuredOutput.ts:396-402`) | Wrench (no spinner) |
| `queued` | No | `Preparing {{NAME}}...` (waiting behind another approval, or running after **Allow**) | Spinner |
| `rejected` | Yes (`Error: tool call rejected by user.`) | `Denied {{NAME}}` | Red cross |
| `incomplete` | Usually no (cut off by Stop) | `View Result from {{NAME}}` | Green tick (5.11) |

The server marks `failed` with its own copy of the error test (`backend/open_webui/utils/middleware.py:158-196`,
`:3482`, `:6126`). The `summary` texts that `structuredOutput.ts` attaches to each tool call
(`Tool Approval Needed`, `Tool Executed`, `Executing...`, `Preparing...`) are **never displayed**:
the tool card receives only the attributes and the result, has no `title` property, and the
grouped line ignores `summary` (`src/lib/components/chat/Messages/structuredOutput.ts:216-235`;
`src/lib/components/chat/Messages/StructuredOutputRenderer.svelte:117-128`, `:177-188`;
`src/lib/components/common/ToolCallDisplay.svelte:22-42`;
`src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte:146-177`). The reasoning
and code-analysis summaries in the same file (`Thought for {duration} seconds`, `Thinking...`,
`Analyzed`, `Analyzing...`) are passed as a title but replaced on screen by the translated labels
in section 5.4 (`src/lib/components/common/Collapsible.svelte:73`, `:96-122`).

## 7. Settings and Configuration

No setting changes the **wording** of these texts; settings change **which steps run** and **what is
drawn**. Defaults below are what the code says; live values are data in the `config` table or the
environment and are **TO BE CONFIRMED** for production (`knowledgebase/tools/ground-truth.md`,
Settings).

### 7.1 Per-Person and Per-Chat Choices

| Setting | Where | Effect on in-chat text | Code default | Source |
|---|---|---|---|---|
| **Hide Processing Details** (`hideProcessingDetails`) | Settings > Interface | Replaces status lines and processing blocks with `Thinking...` (5.9) | Off | `src/lib/components/chat/Messages/ResponseMessage.svelte:197`; `src/lib/components/common/InterfaceSettings.svelte:1358-1378`; `src/lib/i18n/locales/en-US/translation.json:2923-2924` |
| **Always Expand Details** (`expandDetails`) | Settings > Interface | Reasoning, code-analysis, tool-call and grouped blocks start open; the status history still starts closed | Off | `src/lib/components/common/InterfaceSettings.svelte:1313-1332`; `src/lib/i18n/locales/en-US/translation.json:2880`; `src/lib/components/chat/Messages/StructuredOutputRenderer.svelte:125`; `src/lib/components/chat/Messages/ResponseMessage.svelte:721` |
| **Function Calling** (`function_calling`: `Default`, `Native`, `Legacy`) | Chat > Controls > Advanced Params (also a model parameter) | Native: web search, images, knowledge and code appear as tool cards. Legacy: they appear as status lines before the answer (5.2) | `native` when neither the chat nor the model sets it | `src/lib/components/chat/Settings/Advanced/AdvancedParams.svelte:240-270`; `backend/open_webui/main.py:1290-1294` |
| Tool permission mode: **Full access** / **Ask for approval** (`tool_approval_mode`) | Composer menu, only when an admin turned on Tool Permissions | Ask for approval adds the `Allow {{NAME}}?` pause (5.6) | Full access | `src/lib/components/chat/MessageInput/InputMenu.svelte:54-66`, `:146-150`; `src/lib/components/chat/Chat.svelte:432-462`; `backend/open_webui/main.py:1255-1264` |
| Web search, image generation and code interpreter switches in the composer | Composer | Turn the legacy-mode steps (and their status lines) on for one message | Off per message | `backend/open_webui/utils/middleware.py:2700-2720`; `chat-composer-and-message-display.md` |

### 7.2 Per-Model Settings (Workspace > Models)

| Setting | Effect on in-chat text | Code default | Source |
|---|---|---|---|
| Capability **Status Updates** (`status_updates`): `Displays status updates (e.g., web search progress) in the response` | Off hides the status line and its history for that model; processing blocks stay | On | `src/lib/components/workspace/Models/Capabilities.svelte:49-52`; `src/lib/i18n/locales/en-US/translation.json:2587-2588`; `src/lib/components/chat/Messages/ResponseMessage.svelte:198-199` |
| Capability **File Context** (`file_context`): `Inject file content into conversation context` | Off skips file retrieval, so no `Querying` / `Retrieved {count} sources` lines | On | `src/lib/i18n/locales/en-US/translation.json:2579-2580`; `backend/open_webui/utils/middleware.py:3207-3214` |
| Capability **Citations** (`citations`): `Displays citations in the response` | Off hides the source chips under the reply | On | `src/lib/i18n/locales/en-US/translation.json:2575-2576`; `src/lib/components/chat/Messages/ResponseMessage.svelte:934` |
| Capability **Builtin Tools** (`builtin_tools`) | Decides whether built-in tools (and so their tool cards) are offered in native mode | See `builtin-native-tools.md` | `src/lib/i18n/locales/en-US/translation.json:2573-2574`; `src/lib/components/workspace/Models/Capabilities.svelte:57-60` |
| Knowledge attached to the model | Legacy: `Searching Knowledge for "{query}"`; both modes: the closing hidden status (5.3) | None attached | `backend/open_webui/utils/middleware.py:2605-2617`, `:3248-3259` |
| Parameter `function_calling` | As 7.1, for every chat with this model unless the chat sets its own | Not set | `backend/open_webui/main.py:1290-1294` |
| Parameter `compact_token_threshold` | Changes when the compaction toasts appear | Not set (site value applies) | `backend/open_webui/main.py:1206-1207` |

### 7.3 Site Settings (Admin)

| Setting key (environment variable that seeds it) | Effect on in-chat text | Code default | Source |
|---|---|---|---|
| `web.search.enable` (`ENABLE_WEB_SEARCH`) plus permission `features.web_search` | Without both, no web-search lines or `search_web` cards | Off | `backend/open_webui/config.py:1161`, `:2941`; `backend/open_webui/utils/middleware.py:2700-2709` |
| `web.search.confirmation.enable`, `web.search.confirmation.content` | A `Use Web Search?` dialog before sending (not in the reply) | Off | `backend/open_webui/config.py:1163`, `:2942-2943`; `src/lib/components/chat/Chat.svelte:4220-4235` |
| `task.query.search.enable`, `task.query.retrieval.enable` (`ENABLE_SEARCH_QUERY_GENERATION`, `ENABLE_RETRIEVAL_QUERY_GENERATION`) | When off, the `Searching` chip shows the person's whole message and `Querying` shows no chips (the refusal is caught and the message itself is used) | On | `backend/open_webui/config.py:2302-2304`, `:3146-3147`; `backend/open_webui/routers/tasks.py:407-417`; `backend/open_webui/utils/middleware.py:1620-1622`, `:2088-2089`, `:2102-2103` |
| `image_generation.enable`, `images.edit.enable`, `image_generation.prompt.enable` | Whether the legacy image steps (`Creating image` …) run | Off, off, see `image-generation-and-editing.md` | `backend/open_webui/config.py:1351`, `:1525`, `:3019`, `:3024`, `:3039`; `backend/open_webui/utils/middleware.py:1866-1868` |
| `code_interpreter.enable` (`ENABLE_CODE_INTERPRETER`) | Whether code analysis blocks or `execute_code` cards can appear | On | `backend/open_webui/config.py:424`, `:2843`; `code-execution-and-interpreter.md` |
| `chat.tool_permissions.enable` (`ENABLE_TOOL_PERMISSIONS`), label **Tool Permissions** | Offers the approval pause to users | Off | `backend/open_webui/config.py:2196`, `:3138`; `src/lib/i18n/locales/en-US/translation.json:2532-2533` |
| `chat.context_compaction.enable`, `chat.context_compaction.token_threshold` (`ENABLE_CONTEXT_COMPACTION`, `CONTEXT_COMPACTION_TOKEN_THRESHOLD`) | Whether and when the `Compacting context` toasts appear | Off; 80,000 tokens | `backend/open_webui/config.py:2194`, `:2198`, `:3133-3134`; `chat-completion-pipeline-and-generation-tasks.md` |
| `ui.default_interface_settings` (`DEFAULT_INTERFACE_SETTINGS`) | Can preset Hide Processing Details and Always Expand Details for everyone who has not chosen | `{}` | `backend/open_webui/config.py:1712-1718`, `:3089`; `user-settings-and-personalisation.md` section 5.6 |

### 7.4 Environment-Only Settings

| Variable | Effect on in-chat text | Code default | Source |
|---|---|---|---|
| `AIOHTTP_CLIENT_TIMEOUT`, `AIOHTTP_CLIENT_STREAM_IDLE_TIMEOUT` | Without them a stalled provider leaves the reply running indefinitely (5.11); with them, a time-out ends in an error box | Unset (no limit) | `backend/open_webui/env.py:608-625`; `backend/open_webui/utils/session_pool.py:43-51` |
| `CHAT_RESPONSE_MAX_TOOL_CALL_ITERATIONS` (old name `CHAT_RESPONSE_MAX_TOOL_CALL_RETRIES`) | After this many tool-call rounds the reply ends with `Tool-call limit reached ({max_tool_call_iterations} iterations).`; `-1` means no limit | 256 | `backend/open_webui/env.py:1082-1098`; `backend/open_webui/utils/middleware.py:5831-5835`, `:6339-6346` |
| `ENABLE_QUERIES_CACHE` | Reuses the generated web-search queries for retrieval, so the `Querying` chips match the `Searching` chips | Off | `backend/open_webui/env.py:370`; `backend/open_webui/utils/middleware.py:1617-1618`; `backend/open_webui/routers/tasks.py:419-421` |
| `ENABLE_CUSTOM_MODEL_FALLBACK` | When a custom model's base model is gone, uses the first default model instead of failing with `Model not found` | Off | `backend/open_webui/env.py:1033`; `backend/open_webui/main.py:1137-1146`, `:1179-1182` |

## 8. Cron Jobs and Background Processes

There is no crontab and nothing on a timer produces these texts. Every status line and error box
comes from the reply that is running, which the server runs as a background task inside the
uvicorn worker that accepted the request (`backend/open_webui/main.py:1851-1857`;
`backend/open_webui/tasks.py:157`). The `POST /api/chat/completions` call returns at once with the
task ids, and everything else reaches the browser over the websocket (`backend/open_webui/main.py:1868-1881`).

| Process | Started | What it does for these texts | Source |
|---|---|---|---|
| The reply task (one per model in the reply) | When a message is sent, or when **Allow** / **Deny** restarts a paused reply | Runs the preparation steps, sends the status events, streams the answer, stores errors and status history | `backend/open_webui/main.py:1851-1857`, `:1893-1910`; `backend/open_webui/utils/middleware.py:2391-3276` |
| `chat:active` events | Start and end of the reply tasks of a chat | Tell the browser a chat is busy or idle; idle with an unfinished reply makes the browser reload the chat | `backend/open_webui/main.py:1868-1875`, `:1748-1772`; `src/lib/components/chat/Chat.svelte:1229-1242` |
| `redis_task_command_listener` | Startup, when Redis is configured | Lets **Stop** reach a reply running in another worker | `backend/open_webui/main.py:392-393`; `backend/open_webui/tasks.py:28-66` |
| `redis_task_heartbeat` | Startup, when Redis is configured and `REDIS_TASK_TTL` (default 300 seconds) is above 0 | Keeps running replies registered; a worker that dies stops renewing them, so after the time-to-live the chat counts as idle and reloads treat the reply as interrupted (5.11) | `backend/open_webui/main.py:394-395`; `backend/open_webui/tasks.py:69-80`; `backend/open_webui/env.py:393` |
| `redis_event_listener` | Startup, when `WEBSOCKET_MANAGER` is `redis` | Delivers status and error events to a browser connected to a different worker | `backend/open_webui/main.py:397-398` |
| In-progress copy of the reply in Redis | During each reply, when Redis is configured | Lets a reloading browser catch up with the text so far; kept up to `REDIS_RESPONSE_STREAM_TTL` (default 3,600 seconds) | `backend/open_webui/tasks.py:199-260`; `backend/open_webui/env.py:387` |
| Background tasks after the answer (title, tags, follow-ups) | When the answer has finished | No status lines; follow-up suggestions appear under the reply (`chat-composer-and-message-display.md`) | `backend/open_webui/utils/middleware.py:4385`, `:6590` |

Without Redis and with more than one worker, a browser connected to one worker does not receive
the events of a reply running in another, so the status line and the answer can appear stuck until
the page reloads. Whether production runs several workers is **TO BE CONFIRMED** (see `CLAUDE.md`,
Deployment).

## 9. Notifications and Emails

The application sends no email (`knowledgebase/tools/ground-truth.md`, Contacts). For the texts in
this catalogue the notices are:

| Notice | Channel | When | Source |
|---|---|---|---|
| `Compacting context`, then `Context compacted` or `Context compaction failed` | Toasts in the chat | Automatic context compaction starts, succeeds or fails (5.2) | `src/lib/components/chat/Chat.svelte:1173-1199`; `backend/open_webui/utils/context_compaction.py:76-144` |
| The text of a failed request (for example `Model not found`), `Uh-oh! There was an issue with the response.` | Red toasts in the chat, alongside the error box | Paths 1 and 3 in 5.5 | `src/lib/components/chat/Chat.svelte:3641-3667`, `:3716-3754` |
| Refusals of **Allow** / **Deny** and ask-user answers, for example `Tool call has already been resolved.` | Red toasts | The resolve endpoint refuses (section 10) | `src/lib/components/chat/Messages/StructuredOutputRenderer.svelte:43-63`; `src/lib/components/chat/Chat.svelte:559-597` |
| Add-on notifications | Toasts of the add-on's chosen type | An installed function or tool sends a `notification` event (5.10) | `src/lib/components/chat/Chat.svelte:1354-1366` |
| **Chat finished** and **Chat failed** | Personal notification targets (webhooks) a person sets up, admin event webhooks, and the browser notification when the tab is in the background | `chat.finished` when a reply in a saved chat ends; `chat.failed` only when a **non-streaming** reply raises during processing, so most failed replies send no `chat.failed` | `backend/open_webui/utils/middleware.py:206-235`, `:4387-4409`; `backend/open_webui/events.py:164-169`; `notifications-webhooks-events-and-banners.md` sections 5.6 and 5.9 |

The code turns no status line into a notification, and the error box has no notification of its
own. A streamed reply that hits an error after it started still finishes normally, so a person
working in another chat or tab gets the usual "finished" toast (and browser notification, if on)
with whatever text arrived as the preview, not a failure notice; a reply that fails before any answer
streams (path 2 in 5.5) sends no finish event, so no notice appears (`backend/open_webui/utils/middleware.py:6545-6572`;
`src/routes/+layout.svelte:735-778`; `backend/open_webui/main.py:1686-1712`). Replies run
by sub-agents (internal runs) drop add-on `notification` events
(`backend/open_webui/socket/main.py:1146-1147`; `backend/open_webui/utils/subagents.py:68`).

## 10. Error, Warning and Notice Messages (Verbatim)

Every text that can appear inside or around a reply, as the code spells it. `{{name}}` marks a
value the browser fills in; `{name}` marks a value the server fills in (rule 12 of the research
instructions). "Support check" names the reference document that explains the text in depth (found
with `grep -rlF` over `knowledgebase/reference/*.md`), or says what to check when nothing else does.
Status lines that are not translated are shown in English whatever the interface language
(`StatusItem.svelte:144-146`).

### 10.1 Status Lines

| Text the user sees | Kind | Source | When it appears | What it means | Support check |
|---|---|---|---|---|---|
| `Searching the web` | Status line (translated) | `backend/open_webui/utils/middleware.py:1561-1570`; `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:142-143` | Legacy mode, web search turned on for the message and permitted | The server is asking the task model for search queries | Normal. If it never moves on: 11.2. `web-search-and-web-loading.md` |
| `Searching`, with one chip per query | Status line (translated) | `backend/open_webui/utils/middleware.py:1642-1651`; `StatusItem.svelte:52-77` | Queries are ready and the search provider is being called | Search under way | If the only chip is the person's whole message, query generation is off or failed (7.3). `web-search-and-web-loading.md` |
| `No search query generated` | Status line (translated) | `backend/open_webui/utils/middleware.py:1630-1640`; `StatusItem.svelte:138-139` | The task model returned an empty list of queries | Web search was skipped; the answer has no web sources | `web-search-and-web-loading.md`; ask whether the question needed the web |
| `Searched {{count}} sites` (reads, for example, "Searched 5 sites") | Status line (translated), click to list the pages | `backend/open_webui/utils/middleware.py:1688-1700`; `StatusItem.svelte:15-29` | Search and page loading finished | The pages listed were given to the model | Normal. `web-search-and-web-loading.md` |
| `No search results found` | Status line, error flag (shown grey) | `backend/open_webui/utils/middleware.py:1702-1713` | The search step returned nothing usable | No web sources | `web-search-and-web-loading.md` |
| `[ERROR: No results found from web search]` | Status line, error | `backend/open_webui/routers/retrieval.py:2953-2957`; shown by `backend/open_webui/utils/middleware.py:1714-1728` | The provider returned no links for any query | No web sources | Try other wording. `web-search-and-web-loading.md` |
| `[ERROR: Something went wrong while searching the web.]` | Status line, error | `backend/open_webui/routers/retrieval.py:2946-2951`, `:3042-3047`; `backend/open_webui/constants.py:16-23`, `:101` | The provider call or the page loading raised an error | The search failed; the reason is only in the server log | Escalate with the time and the chat link; an admin checks the provider, key and quota (`web-search-and-web-loading.md`) |
| `Failed to embed and store the retrieved web pages. Check the embedding configuration in Admin Settings > Documents.` | Status line, error | `backend/open_webui/routers/retrieval.py:3028-3031` | Pages were fetched but could not be turned into searchable text | Embedding service fault | Escalate to the admin (Documents settings). `rag-retrieval-embeddings-and-vector-stores.md` |
| `[ERROR: {message}]` for storage faults, for example `[ERROR: The server is out of storage space.]` | Status line, error | `backend/open_webui/constants.py:6-23` | A storage error (full disk, quota, not writable) during the search | Server storage fault | Escalate to the platform maintainer |
| `An error occurred while searching the web` | Status line, error | `backend/open_webui/utils/middleware.py:1714-1728` | A failure that carried no readable detail | The search failed | Escalate with the time |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Status line, error | `backend/open_webui/routers/retrieval.py:2885-2895`; `backend/open_webui/constants.py` (`ACCESS_PROHIBITED`) | Web search was switched off, or the permission removed, between the composer's check and the search | Rare; seen during a settings change | Check `web.search.enable` and `features.web_search` (`users-groups-roles-and-permissions.md`) |
| `Searching Knowledge for "{{searchQuery}}"` (the person's message as the query) | Status line (translated) | `backend/open_webui/utils/middleware.py:2608-2617`; `StatusItem.svelte:40-51` | Legacy mode, model has knowledge attached | Knowledge search under way | Normal. `knowledge-bases.md` |
| `Querying`, with one chip per retrieval query | Status line (translated) | `backend/open_webui/utils/middleware.py:2091-2100`; `StatusItem.svelte:78-103` | Attached files or knowledge to search, not all in full-context mode | Retrieval under way | No chips: retrieval query generation is off or failed (7.3). `rag-retrieval-embeddings-and-vector-stores.md` |
| `No sources found` | Status line (translated) | `backend/open_webui/utils/middleware.py:2105-2165`; `StatusItem.svelte:111-112` | Retrieval found no distinct source, **or the retrieval step failed** (the failure is logged, not shown) | The answer is not based on the files | 11.4. `rag-retrieval-embeddings-and-vector-stores.md` |
| `Retrieved 1 source` | Status line (translated) | `StatusItem.svelte:113-114` | One distinct source found | Normal | `rag-retrieval-embeddings-and-vector-stores.md` |
| `Retrieved {{count}} sources` | Status line (translated) | `StatusItem.svelte:115-122`; count from `backend/open_webui/utils/middleware.py:2142-2155` | Several distinct sources found | `{{count}}` counts documents, not passages | Normal |
| `Creating image` | Status line | `backend/open_webui/utils/middleware.py:1870-1876` | Legacy mode, image generation on for the message, saved chat | Image being made | Normal. `image-generation-and-editing.md` |
| `Image created` | Status line | `backend/open_webui/utils/middleware.py:1890-1895`, `:1998-2003` | The image (or edit) succeeded | The picture shows above the answer | Normal |
| `An error occurred while generating an image` | Status line | `backend/open_webui/utils/middleware.py:1923-1931`, `:2031-2039` | Generation or editing failed; the model is told the error text and usually repeats it | No picture | `image-generation-and-editing.md` |
| `Image generation is disabled` | Status line | `backend/open_webui/utils/middleware.py:1935-1944` | Effectively never in v0.11.4: with generation off the step returns earlier (`:1866-1868`) | — | `image-generation-and-editing.md` |
| `Generating search query` | Status line (translated label) | `StatusItem.svelte:32-33`, `:140-141` | No server code in v0.11.4 sends it; only an add-on would | Add-on text | 5.10 |
| `Searching "{{searchQuery}}"` | Status line (translated label) | `StatusItem.svelte:133-137` | No server code sends a description containing `{{searchQuery}}`; only an add-on would | Add-on text | 5.10 |
| Any other grey line | Status line (as sent) | `StatusItem.svelte:144-146` | An installed function, tool or pipe sent it | Add-on progress text | `functions-pipes-filters-actions-and-pipelines.md`; ask which add-ons the model uses |
| `Thinking...` (MedIT GPT) | Status-style line | `src/lib/components/chat/Messages/ResponseMessage.svelte:216-221`, `:920-921`; `src/lib/i18n/locales/en-US/translation.json:3222` | Hide Processing Details is on, the reply is running and no answer text has arrived | Work in progress; the steps are hidden | 5.9, 11.1. `user-settings-and-personalisation.md` |

### 10.2 Processing Blocks and Tool Cards

| Text the user sees | Kind | Source | When it appears | What it means | Support check |
|---|---|---|---|---|---|
| `Thinking...` | Processing label, spinner | `src/lib/components/common/Collapsible.svelte:111-112` | A thinking model's reasoning is streaming | Normal | 11.1. `chat-composer-and-message-display.md` |
| `Thought for less than a second` | Processing label | `src/lib/components/common/Collapsible.svelte:98-99` | Reasoning finished, duration under one second | Normal | None |
| `Thought for {{DURATION}} seconds` | Processing label | `src/lib/components/common/Collapsible.svelte:100-103` | Reasoning finished in under a minute | Normal | None |
| `Thought for {{DURATION}}` (for example "Thought for 2 minutes") | Processing label | `src/lib/components/common/Collapsible.svelte:104-107` | Reasoning took a minute or more; the duration is put into words by the date library in the interface language | Normal | None |
| `Thought` | Processing label | `src/lib/components/common/Collapsible.svelte:108-110` | Reasoning finished with no duration recorded | Normal | None |
| `Analyzing...` | Processing label, spinner | `src/lib/components/common/Collapsible.svelte:117-118` | Legacy-mode code analysis is being written or run | Normal | 11.2. `code-execution-and-interpreter.md` |
| `Analyzed` | Processing label | `src/lib/components/common/Collapsible.svelte:115-116` | Code analysis finished; open it for the code and output | Normal | `code-execution-and-interpreter.md` |
| `Exploring`, then tool names (`2 search_web`) and `Ran {{COUNT}} analysis` / `Ran {{COUNT}} analyses` | Group line, spinner | `src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte:146-177` | Several processing blocks in a row, at least one tool call still running | Normal | `builtin-native-tools.md` |
| `Explored` | Group line, tick or red cross | `ConsecutiveDetailsGroup.svelte:177`, `:201-222` | The grouped calls finished; a red cross if any failed or was denied | Open it to see which call failed | 5.6 |
| `Preparing {{NAME}}...` | Tool card, spinner | `src/lib/components/common/ToolCallDisplay.svelte:250-251` | The model is still writing the call's arguments, or the call is queued behind an approval or running after **Allow** | Normal | `builtin-native-tools.md` |
| `Executing {{NAME}}...` | Tool card, spinner | `ToolCallDisplay.svelte:252-253` | The tool is running | Normal; a long wait is the tool, not the model | 11.2 |
| `View Result from {{NAME}}` | Tool card, green tick or red cross | `ToolCallDisplay.svelte:244-245`, `:213-233` | The tool returned (tick), returned an error-looking result (cross), or was cut off by Stop (tick, 5.11) | Open it for **Output** | 5.6 |
| `Allow {{NAME}}?`, buttons `Allow` and `Deny` | Tool card | `ToolCallDisplay.svelte:248-249`, `:257-276`; `ConsecutiveDetailsGroup.svelte:234-298` | Tool Permissions is on and the person chose Ask for approval | The reply is paused until they answer | 5.6. `builtin-native-tools.md` |
| `Denied {{NAME}}` | Tool card, red cross | `ToolCallDisplay.svelte:242-243` | The person clicked **Deny**, or Stop closed a pending approval | The model was told the call was rejected | None |
| `Input needed` | Tool card | `ToolCallDisplay.svelte:246-247` | An ask-user question is waiting, on replies drawn from `<details>` text only (older replies, some pipes); current replies show nothing in the answer and the card is above the composer | Answer the card | 5.7. `chat-composer-and-message-display.md` |
| `Input`, `Output` | Headings in an opened card | `ToolCallDisplay.svelte:298-301`, `:331-334` | The card is opened | Arguments sent; result returned | None |
| `Show all ({{COUNT}} characters)` | Button in an opened card | `ToolCallDisplay.svelte:356-361` | The result is longer than 10,000 characters | Shows the rest | None |
| `Sub-agent: "{task}"`, `Background sub-agent: "{task}"`, `Sub-agent` (as the card's `{{NAME}}`) | Tool card name (not translated) | `src/lib/components/chat/Messages/structuredOutput.ts:201-213` | The model delegated a task (`delegate_task`); the task is cut at 60 characters | Normal | `builtin-native-tools.md` |
| `Web Search`, `File Search`, `Computer Use` (as `{{NAME}}`), with **Output** such as `Search: {queries}`, `Open page: {url}`, `Find in page: {pattern}`, `Queries: {queries}`, `Action: {type}` or `Actions: {types}` | Tool card (not translated) | `src/lib/components/chat/Messages/structuredOutput.ts:94-98`, `:275-322` | The model provider ran one of its own built-in tools and reported it | The provider, not MedIT GPT, ran the tool | `model-connections-openai-ollama-and-direct.md` |
| `tool` | Name in a list of waiting calls | `ConsecutiveDetailsGroup.svelte:274` | Several calls wait for approval and one has no name | None | None |
| `Background sub-agent finished` | Row in the reply | `src/lib/components/chat/Messages/SubagentResultRow.svelte:41` | A background sub-agent reported back | Normal | `builtin-native-tools.md` |
| `out of`, `tasks completed` (reads "2 out of 5 tasks completed") | Task list above the composer | `src/lib/components/chat/Messages/ResponseMessage/TaskList.svelte:30-32`; `src/lib/components/chat/MessageInput.svelte:1792` | The model keeps a task list during the reply; hidden by Hide Processing Details | Progress through the model's plan | `builtin-native-tools.md` |
| `Toggle status history`, `Toggle details` | Accessible names (read by screen readers) | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory.svelte:35`; `ConsecutiveDetailsGroup.svelte:188` | On the status line and on a grouped line | Opens or closes the list | None |

### 10.3 Error Box Texts

Paths 1 to 5 refer to section 5.5. Provider texts vary by model provider and cannot be listed; the
rows below are the texts MedIT GPT itself writes.

| Text the user sees | Kind | Source | When it appears | What it means | Support check |
|---|---|---|---|---|---|
| `Error submitting message` | Error box (English only) | `src/lib/components/chat/Messages/Error.svelte:37` | The stored error has empty content | Unknown failure; nothing more on screen | Escalate with the time and chat link |
| `Uh-oh! There was an issue with the response.` followed by the provider's message | Error box and red toast | `src/lib/components/chat/Chat.svelte:3716-3754`; `src/lib/i18n/locales/en-US/translation.json:3324` | Path 3: the provider reported an error in the stream | The provider refused or failed (quota, content filter, context too long); the second part is its reason | `chat-completion-pipeline-and-generation-tasks.md`; `model-connections-openai-ollama-and-direct.md` |
| `Uh-oh! There was an issue with the response.` alone | Red toast | `src/lib/components/chat/Chat.svelte:3647-3657` | Path 1, when the refusal carried no readable text | The request failed | As above |
| `Open WebUI: Server Connection Error` | Error box | `backend/open_webui/constants.py:127-130`; `backend/open_webui/routers/openai.py:1746-1751`; `backend/open_webui/routers/ollama.py:164-167`, `:190-194` | Path 2: the server got no usable answer from the provider (connection refused, time-out, unreadable error) | Provider unreachable from the server; it names the upstream product (licence-protected wording) | Escalate to the platform maintainer with the model name and time. `model-connections-openai-ollama-and-direct.md` |
| `Ollama: {e}` | Error box | `backend/open_webui/routers/ollama.py:190-194` | Path 2 for an Ollama connection whose request raised | The Ollama server could not be reached; `{e}` is the technical reason | `model-connections-openai-ollama-and-direct.md` |
| `Model not found` | Red toast and error box | `backend/open_webui/main.py:1129`, `:1182`; `backend/open_webui/utils/chat.py:193` | Path 1: the chosen model is not in the model list any more, or a custom model's base model is gone | The model was removed, renamed or its connection is off | `workspace-models-and-model-access.md`; ask the person to pick another model |
| `Model '' was not found` (empty name) | Error box | `backend/open_webui/routers/openai.py:1546-1552`; `backend/open_webui/constants.py:89` | Path 2: the model is listed but its connection no longer offers it | Provider-side model gone | `model-connections-openai-ollama-and-direct.md` |
| `Provider returned HTTP {status_code}`, `Provider returned an error` | Error box | `backend/open_webui/utils/misc.py:43-65` | Path 2: the provider answered with an HTTP error whose body could not be read | Provider refused; reason unknown | `model-connections-openai-ollama-and-direct.md` |
| The provider's own message (for example a quota or rate-limit text) | Error box | `backend/open_webui/utils/misc.py:43-65`; `backend/open_webui/utils/middleware.py:4231-4255`, `:5072-5091`, `:5226-5249` | Paths 2 to 4 | Whatever the provider says | Copy the exact text into the ticket |
| `Tool-call limit reached ({max_tool_call_iterations} iterations).` | Error box under the partial answer | `backend/open_webui/utils/middleware.py:6339-6346` | Path 5: the model kept calling tools for more rounds than `CHAT_RESPONSE_MAX_TOOL_CALL_ITERATIONS` (default 256) | The model looped; the answer stops | `builtin-native-tools.md`; `chat-completion-pipeline-and-generation-tasks.md` |
| `Failed to connect to MCP server '{server_id}'` | Error box (screen only, not saved) | `backend/open_webui/utils/middleware.py:3005-3013` | An MCP tool server chosen for the chat could not be reached; the reply continues without its tools | Tool server down or misconfigured | `workspace-tools-tool-servers-mcp-and-terminals.md` |
| `Terminal unavailable: {e}` | Error box | `backend/open_webui/utils/middleware.py:3061-3063` | Path 2: the terminal attached to the chat could not be prepared | Terminal service down | `workspace-tools-tool-servers-mcp-and-terminals.md` |
| `Direct connection requires an active WebSocket session; cannot generate completion in this context (e.g. background task).` | Error box | `backend/open_webui/utils/chat.py:64-68` | A direct (browser-side) connection was used without a live browser connection | Direct connections need the page open | `model-connections-openai-ollama-and-direct.md` |
| A filter's own refusal text | Error box | `backend/open_webui/utils/middleware.py:2669-2670`, `:3271-3272` | Path 2: an installed filter raised an error (for example a content rule) | Wording is the add-on's | `functions-pipes-filters-actions-and-pipelines.md` |
| `Sub-agent cancelled.` | Error box on a sub-agent's message | `backend/open_webui/utils/subagents.py:519-524` | A delegated task was stopped | Normal after Stop | `builtin-native-tools.md` |
| `Server connection failed` | Red toast and error box | `src/lib/apis/openai/index.ts:3-14`, `:437-448` | Path 1 when the failure carried no readable reason; a network failure shows the browser's own error text instead | The browser could not reach MedIT GPT | 11.5. `error-messages-frontend-chat-and-navigation.md` |
| `Error: {error_content}`, or `Error: An error occurred` when there is no content | Message text in a channel | `backend/open_webui/socket/main.py:1126-1129` | A model reply in a channel failed | As the matching error box text | `channels-and-direct-messages.md` |
| `Chat completion stream failed` | Error object in an API stream | `backend/open_webui/utils/middleware.py:6707-6711` | Only for API callers without a chat | Not seen in the chat screen | `chat-completion-pipeline-and-generation-tasks.md` |

### 10.4 Tool Result Texts (Under **Output**, Usually With a Red Cross)

The model receives these as the tool's answer; the person sees them when they open the card.

| Text the user sees | Kind | Source | When it appears | What it means | Support check |
|---|---|---|---|---|---|
| `Error: Tool "{name}" not found.` | Tool result | `backend/open_webui/utils/middleware.py:5996-5997`, `:3349-3351` | The model called a tool that is not available in this chat | Model mistake, or a tool was removed or not selected | `workspace-tools-tool-servers-mcp-and-terminals.md` |
| `Error: Tool call arguments for '{name}' must be a JSON object. Please try again.` (back-quotes around the name in the source) | Tool result | `backend/open_webui/utils/middleware.py:5985-5992` | The model's arguments were valid JSON but not an object | Model quality issue; it usually retries | `builtin-native-tools.md` |
| `Error: Tool call arguments could not be parsed. The model generated malformed or incomplete JSON for '{tool_function_name}'. Please try again.` (back-quotes in the source) | Tool result | `backend/open_webui/utils/middleware.py:6050-6058` | The model's arguments were unreadable | Model quality issue | `builtin-native-tools.md` |
| `Error: Tool call arguments could not be parsed. The model generated malformed or incomplete JSON.` | Tool result | `backend/open_webui/utils/middleware.py:3334-3340` | Same, for a call run after **Allow** | Model quality issue | `chat-completion-pipeline-and-generation-tasks.md` |
| `Error: Tool call arguments must be a JSON object.` | Tool result | `backend/open_webui/utils/middleware.py:3342-3346` | Same, for a call run after **Allow** | Model quality issue | `workspace-tools-tool-servers-mcp-and-terminals.md` |
| `Error: Browser session is not connected for this direct tool.` | Tool result | `backend/open_webui/utils/middleware.py:3360-3362` | An approved call to a browser-side tool server ran with no live browser connection | Reopen the chat and retry | `workspace-tools-tool-servers-mcp-and-terminals.md` |
| `{"error": "{e}"}` | Tool result | `backend/open_webui/utils/middleware.py:3385-3386`, `:6026-6027` | The tool itself raised an error; `{e}` is its message | Tool fault | Copy the text; `workspace-tools-tool-servers-mcp-and-terminals.md` |
| `Error: tool call rejected by user.` | Tool result, `Denied {{NAME}}` | `backend/open_webui/utils/tool_approval.py:65-75` | **Deny**, a cancelled ask-user card, or Stop on a pending approval | Expected | None |
| `Error: ask_user must be the only tool call, so it did not run. Call ask_user on its own.` | Tool result | `backend/open_webui/utils/ask_user.py:15-19` | The model asked a question together with other tool calls | Model mistake; it usually retries | `builtin-native-tools.md` |
| `Error: only one ask_user call is allowed per turn.` | Tool result | `backend/open_webui/utils/ask_user.py:20-21` | The model asked twice in one turn | Model mistake | `builtin-native-tools.md` |
| `Error: {exc}` with one of `ask_user requires 1-3 questions.`, `Each question must be an object.`, `Each question requires a non-empty id.`, `Duplicate question id: {question_id}`, `Each question requires 2-3 options.`, `Each option must be an object.`, `Each option requires a label and description.`, `Each question requires question text.`, `ask_user arguments must be an object.` | Tool result | `backend/open_webui/utils/ask_user.py:25-60`, `:97-104` | The model's question broke the ask-user rules, so no card appeared | Model mistake | `builtin-native-tools.md` |
| `{"status": "error", "error": "User input requires an active browser session with WebSocket connection."}` | Tool result | `backend/open_webui/tools/builtin.py:589-596` | The ask-user tool ran with no live browser connection | Reopen the chat | `builtin-native-tools.md` |
| `{"status": "error", "error": "Invalid user input response."}` | Tool result | `backend/open_webui/tools/builtin.py:609-610` | The browser's answer to the ask-user card was unreadable | Retry | `builtin-native-tools.md` |
| `{"status": "cancelled", "answers": {}}` (with `"timed_out": true` on the saved-chat path) | Tool result, **green tick** | `backend/open_webui/tools/builtin.py:613-614`; `backend/open_webui/utils/tool_approval.py:82-86` | The ask-user card was cancelled or timed out | The model got no answers | None |
| `Sub-agent produced no output.`, `[output truncated]` | Tool result of `delegate_task` | `backend/open_webui/utils/subagents.py:511-517` | A delegated task returned nothing, or more than the output limit | Normal | `builtin-native-tools.md` |
| Built-in tool texts (for example `Request context not available`, `Unknown code interpreter engine: {engine}`) | Tool result | `backend/open_webui/tools/builtin.py` | Each built-in tool's own failures | See the tool | `builtin-native-tools.md`; `code-execution-and-interpreter.md` |

### 10.5 Toasts During a Reply

| Text the user sees | Kind | Source | When it appears | What it means | Support check |
|---|---|---|---|---|---|
| `Compacting context` | Toast (loading) | `src/lib/components/chat/Chat.svelte:1195-1199`; `backend/open_webui/utils/context_compaction.py:75-85` | Automatic compaction started before the reply | Older turns are being summarized | Normal. `chat-completion-pipeline-and-generation-tasks.md` |
| `Context compacted` | Toast (success) | `src/lib/components/chat/Chat.svelte:1185-1189`; `backend/open_webui/utils/context_compaction.py:135-145` | Compaction finished | Older turns are now a summary | Normal |
| `Context compaction failed` | Toast (error) | `src/lib/components/chat/Chat.svelte:1180-1184`; `backend/open_webui/utils/context_compaction.py:98-111` | The summary could not be made; the error then stops the reply (path 2) | Summary model problem | `chat-completion-pipeline-and-generation-tasks.md` |
| `Message has no resolvable output.` | Toast (error) | `backend/open_webui/utils/tool_approval.py:38-40` | **Allow** / **Deny** on a reply without tool calls | Stale screen | Reload the chat |
| `Tool call not found.` | Toast (error) | `backend/open_webui/utils/tool_approval.py:42-51` | The call is no longer on the reply | Stale screen | Reload the chat |
| `Tool call has already been resolved.` | Toast (error) | `backend/open_webui/utils/tool_approval.py:55-58` | Second click, second tab, or Stop already closed it | Harmless | Reload the chat |
| `ask_user requires an answer or deny.` | Toast (error) | `backend/open_webui/utils/tool_approval.py:60-62` | **Allow** was sent for an ask-user call | Interface mismatch | Reload; escalate if repeated |
| `Tool call does not accept answers.` | Toast (error) | `backend/open_webui/utils/tool_approval.py:76-78` | Answers were sent to a normal tool call | Interface mismatch | Reload; escalate if repeated |
| `Answers are required for ask_user.` | Toast (error) | `backend/open_webui/utils/tool_approval.py:79-80` | An empty ask-user answer | Answer every question | None |
| `Tool call parent message is missing.` | Toast (error) | `backend/open_webui/utils/tool_approval.py:140-143` | The question the reply answers was deleted | The paused reply cannot resume | Press **Stop**; ask again |
| `Tool call message model is missing.` | Toast (error) | `backend/open_webui/utils/tool_approval.py:158-160` | The paused reply has no model recorded | Cannot resume | Press **Stop**; ask again |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Toast (error) | `backend/open_webui/utils/tool_approval.py:27-32` | Someone other than the chat owner or an admin answered | Expected refusal | `users-groups-roles-and-permissions.md` |
| `We could not find what you're looking for :/` | Toast (error) | `backend/open_webui/utils/tool_approval.py:34-36`, `:131-138`; `backend/open_webui/constants.py:78` | The reply or chat was deleted while paused | Stale screen | Reload |
| Add-on notifications (any text) | Toast of the add-on's type | `src/lib/components/chat/Chat.svelte:1354-1366` | An installed function or tool sent a `notification` event | Add-on text | `functions-pipes-filters-actions-and-pipelines.md` |

The manual compaction command (`Compacting context...`, `Wait for the current response to finish
before compacting.` and the skip reasons) runs from the composer, not inside a reply; see
`chat-composer-and-message-display.md` (`src/lib/components/chat/Chat.svelte:2965-3005`).

### 10.6 Ask-User Card, Dialogs and the Code Execution Window

| Text the user sees | Kind | Source | When it appears | What it means | Support check |
|---|---|---|---|---|---|
| `Recommended`, `Other`, `Type your answer`, `Cancel`, `Previous`, `Next`, `Submit answers` | Card labels and buttons | `src/lib/components/chat/AskUserCard.svelte:227`, `:241`, `:245`, `:271`, `:279`, `:288`, `:297` | An ask-user question is waiting | Answer or cancel | 5.7. `chat-composer-and-message-display.md` |
| `Question {index + 1}` (for example "Question 1") | Card heading (not translated) | `backend/open_webui/utils/ask_user.py:65`; `backend/open_webui/tools/builtin.py:579` | The model gave a question no header | Normal | None |
| `Confirm Prompt from Embed`, with the prompt as the message | Dialog title | `src/lib/components/chat/Chat.svelte:1455-1466`, `:1487-1498` | An embedded tool view in a reply asks to send a prompt | Confirm only if the person expects it | `chat-composer-and-message-display.md` |
| `Use Web Search?`, `Your query will be sent to the configured web search provider.`, `Continue`, `Cancel` | Dialog before sending | `src/lib/components/chat/Chat.svelte:4220-4235` | Web search confirmation is on (`web.search.confirmation.enable`); the admin can replace the message | The question will leave MedIT GPT for the search provider | `web-search-and-web-loading.md` |
| Add-on dialog title and message (any text) | Dialog | `src/lib/components/chat/Chat.svelte:1367-1401`, `:4249-4268` | An add-on asks for confirmation or input | Add-on text | `functions-pipes-filters-actions-and-pipelines.md` |
| `Code execution: {name}` (or `Code execution`), `ERROR`, `OUTPUT`, `Files` | Window title and headings | `src/lib/components/chat/Messages/CodeExecutionModal.svelte:39-41`, `:79`, `:85`, `:95` | A code execution chip is opened | The add-on's run and its result | `code-execution-and-interpreter.md` |

### 10.7 Texts Defined but Never Shown

- `Tool Approval Needed`, `Tool Executed`, `Executing...`, `Preparing...`: tool-call summaries built in
  `src/lib/components/chat/Messages/structuredOutput.ts:216-223` and `:309-312`, never drawn
  (section 6.3).
- `Thought for {duration} seconds` and the other reasoning and code summaries in the same file
  (`:247`, `:264`): replaced on screen by the translated labels in 10.2.
- `Generating search query` and `Searching "{{searchQuery}}"`: translated by the status component but
  sent by no server code in v0.11.4 (10.1).
- `Image generation is disabled`: sent only in a timing corner case (10.1).

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it does not change settings, models, roles or chats. What to collect for every
escalation from this section: the chat link (`/c/{id}`, from the address bar), the date, time and
time zone of the reply, the model name shown above the reply, the exact text on screen (status line,
error box or card), and whether **Hide Processing Details** is on. Do not paste the conversation
itself into a ticket: chats can hold personal and health information; the link is enough for an
administrator who is allowed to open it (`ENABLE_ADMIN_CHAT_ACCESS`, see
`knowledgebase/tools/ground-truth.md`).

### 11.1 "It just says Thinking... forever"

**Symptom.** A grey shimmering `Thinking...` stays on screen and no answer arrives.

**Likely causes, in order.**
1. Hide Processing Details is on, so `Thinking...` hides a slow or stuck step (web search, retrieval,
   a tool, a provider that has not answered) (5.9).
2. A thinking model is still reasoning: with the switch off, `Thinking...` with a spinner is the
   reasoning block, which can run for minutes (`src/lib/components/common/Collapsible.svelte:111-112`).
3. The provider accepted the request but never answers; there is no time limit by default (5.11).
4. The reply was interrupted (server restart, lost connection) and the screen was not refreshed (5.11).
5. With several workers and no Redis, the events went to another worker (section 8).

**Diagnostic steps.**
1. Ask whether the line has a small spinner to its left and can be opened (reasoning block, cause 2)
   or is a plain line (cause 1).
2. Ask the person to turn **Hide Processing Details** off in Settings > Interface and reload the
   chat; the saved status lines then show which step was last reached (5.9).
3. Ask them to reload the page. If the reply is no longer running on the server, the spinner stops
   and the partial answer (if any) remains (`src/lib/components/chat/Chat.svelte:2375-2412`).
4. Ask whether other models answer normally; if none do, it is a platform problem.

**Resolution.** Suggest **Stop**, then send the message again, perhaps with another model. For a
thinking model, explain that long reasoning is normal. If every model hangs, escalate at once.

**Escalation.** Chat link, time, model, the last visible status line (with the switch off), and
whether other models work. The administrator checks the provider connection and the
`AIOHTTP_CLIENT_TIMEOUT` setting (section 7.4).

### 11.2 "It said Searching the web and then nothing"

**Symptom.** A status line such as `Searching the web`, `Searching`, `Querying`, `Creating image` or
`Executing {{NAME}}...` stays, often still shimmering, and the reply does not continue.

**Likely causes, in order.**
1. The step is still running: search providers and page loading can be slow, and many pages may be
   fetched (`web-search-and-web-loading.md`).
2. The reply was stopped or interrupted after that line; the line keeps shimmering because nothing
   closes it (5.11).
3. The step failed and the reply went on but the answer is still being written: the error line
   replaces the progress line only for web search (`[ERROR: …]` lines, 10.1).
4. The provider is not answering after the preparation finished (cause 3 in 11.1).

**Diagnostic steps.**
1. Click the status line to open its history and note the last two entries (5.3).
2. Ask whether a blinking bar or `Thinking...` is under the line (the answer stage has started) or
   nothing (still preparing).
3. Reload the page and see whether the reply now shows as finished.

**Resolution.** Wait a minute; then **Stop** and resend. For web search, suggest a simpler question
or switching web search off for that message.

**Escalation.** Chat link, time, model, the status history entries, whether web search, image
generation or tools were on. The administrator checks the search provider and the server log at that
time.

### 11.3 "There's a red error under the answer"

**Symptom.** Text in a rounded box with an (i) icon under the reply. (The box itself is light grey;
the red is usually a toast that appeared at the same time.)

**Likely causes, in order.**
1. The model provider refused or failed: quota, rate limit, content filter, context too long (paths
   3 and 4 in 5.5).
2. The provider could not be reached: `Open WebUI: Server Connection Error` (11.5).
3. A later step failed after part of the answer was written: `Tool-call limit reached (…)`, an MCP
   server, a follow-up call (path 5).
4. An installed filter or pipe refused (10.3).
5. The model or its base model was removed: `Model not found` (11.9).

**Diagnostic steps.**
1. Copy the exact text of the box. Text starting `Uh-oh! There was an issue with the response.` was
   written by the browser at the time; after a reload the same box shows only the provider's part
   (5.5).
2. Note whether any answer text sits above the box (a partial answer) or none.
3. Ask whether it happens with another model and in a new chat.

**Resolution.** Match the text in section 10.3. For provider limits, suggest waiting and retrying or
another model; for a long chat, suggest starting a new chat. Use **Regenerate** to try again.

**Escalation.** The exact text, chat link, time, model, and whether it repeats in a new chat.

### 11.4 "It says No sources found"

**Symptom.** After `Querying`, the line reads `No sources found` and the answer ignores the
attached files or knowledge.

**Likely causes, in order.**
1. Nothing in the files matched the question closely enough (relevance threshold, top-k)
   (`rag-retrieval-embeddings-and-vector-stores.md`).
2. The retrieval step failed (embedding or vector store fault): the code logs the error and still
   shows `No sources found` (`backend/open_webui/utils/middleware.py:2105-2137`).
3. The files are not processed yet, or failed processing (`files-uploads-and-storage.md`).
4. Query generation is off, so the person's whole message was used as the search (7.3).

**Diagnostic steps.**
1. Ask whether the file shows as processed in the chat or knowledge base.
2. Ask whether a different, very specific question about the file finds sources.
3. Ask whether the same happens for every file and knowledge base (a platform fault) or one.

**Resolution.** Suggest rephrasing with words from the document, or, for a file attached to the
message, opening it and choosing **Using Entire Document** where that option is offered, so the whole
file is given to the model without a search (`src/lib/components/common/FileItemModal.svelte:360-362`;
5.2). If every retrieval returns `No sources found`, escalate.

**Escalation.** Chat link, time, model, file or knowledge base name (not its contents), and whether
other files work. The administrator checks the embedding and vector store settings and the server log.

### 11.5 "It says Server Connection Error"

**Symptom.** The error box reads `Open WebUI: Server Connection Error` (or `Ollama: …`), or a toast
reads `Server connection failed` or a browser network error.

**Likely causes, in order.**
1. `Open WebUI: Server Connection Error`: the MedIT GPT server could not reach the model provider
   (provider down, network, wrong address, time-out). The words "Open WebUI" are the upstream
   product name kept for licence reasons; it is still MedIT GPT's error (`backend/open_webui/constants.py:127-130`).
2. `Server connection failed` or a browser error such as a failed fetch: the person's browser could
   not reach the MedIT GPT server at all (network, VPN, server restarting) (`src/lib/apis/openai/index.ts:3-14`).

**Diagnostic steps.**
1. Ask which of the two texts appears.
2. For the first: ask whether every model fails or only one (one provider down, or all).
3. For the second: ask whether the rest of the site loads, and whether it works on another network.

**Resolution.** For the first, suggest another model if one works, and escalate. For the second,
suggest reloading, checking the network or VPN, and trying again later.

**Escalation.** Which text, time, model(s) affected, whether other models work. This is usually a
platform incident; the production escalation route is **TO BE CONFIRMED**.

### 11.6 "A tool has a red cross" (or "It says Error: Tool … not found")

**Symptom.** A tool card or the `Explored` line shows a red cross; opening it shows an `Error:` text
or JSON with `error`.

**Likely causes, in order.**
1. The tool returned an error and the model carried on (normal; the answer usually explains) (5.6).
2. The model called a tool that is not available in this chat: `Error: Tool "{name}" not found.`
3. The model wrote bad arguments (`could not be parsed`, `must be a JSON object`).
4. The person clicked **Deny** (`Denied {{NAME}}`).

**Diagnostic steps.** Open the card and copy the **Output** text; compare it with section 10.4.
Check whether the final answer is still useful.

**Resolution.** If the answer is fine, nothing to do. Otherwise suggest **Regenerate**, or turning on
the tool that was missing. A green tick on `execute_code` does not mean the code worked: check
`stderr` in the output (5.8).

**Escalation.** Tool name, the **Output** text, chat link and time, if the same tool fails for
several people.

### 11.7 "It stopped and asks me to Allow something"

**Symptom.** A card reads `Allow {{NAME}}?` with **Allow** and **Deny**, and the reply waits.

**Likely causes, in order.** The person (or a preset) chose **Ask for approval** in the composer
menu; MedIT GPT then pauses before each tool call (5.6).

**Diagnostic steps.** Ask whether they see **Full access** / **Ask for approval** in the composer
menu and which is chosen.

**Resolution.** Explain **Allow** (run the tool) and **Deny** (the model continues without it). If
they do not want to be asked, they can choose **Full access**. If the toast `Tool call has already
been resolved.` appears, reload the chat.

**Escalation.** Only if **Allow** does nothing after a reload: chat link, time, tool name, the toast.

### 11.8 "I can't see the progress steps any more"

**Symptom.** Replies no longer show `Searching the web`, `Retrieved {count} sources`, reasoning or
tool cards.

**Likely causes, in order.**
1. Hide Processing Details is on (personally, or through the admin's default preset) (5.9).
2. The model's **Status Updates** capability is off (status lines only) (7.2).
3. The model has knowledge attached, and the closing hidden status removed the line (5.3).
4. Function Calling is Native, so web search shows as a `search_web` tool card instead of status lines (5.2).
5. The reply is in a channel or temporary chat, where status lines are not shown or not saved (6.1).

**Diagnostic steps.** Ask them to check Settings > Interface; ask whether all models or one model
behave this way.

**Resolution.** Explain the switch and let the person decide. Model capabilities are changed only by
model administrators.

**Escalation.** Only if the person needs the steps back for one model: model name, to the model's
administrator.

### 11.9 "It says Model not found"

**Symptom.** A red toast and an error box `Model not found`, or the error box `Model '' was not found`.

**Likely causes, in order.** The model was removed, renamed or hidden; a custom model's base model
was removed; the provider stopped offering it (10.3).

**Diagnostic steps.** Ask whether the model still appears in the model picker for a new chat.

**Resolution.** Suggest choosing another model for the chat. Note that after this refusal the
message may be missing when the chat is reopened, because nothing was saved (5.5, path 1).

**Escalation.** Model name and time, to the model administrator (`workspace-models-and-model-access.md`).

### 11.10 "The status line is in English but my interface is in another language"

**Symptom.** Some status lines are translated and some are not.

**Likely causes.** Only the lines in section 5.3 are translated; image lines, error lines from web
search, add-on lines and every error box text are shown exactly as the server or provider sent them
(`StatusItem.svelte:144-146`; `src/lib/components/chat/Messages/Error.svelte:37-47`).

**Resolution.** Explain that this is how the code works. **Escalation.** None needed.

## 12. Local Customisations

The server side of this area matches upstream v0.11.4: `git diff main...uoft` shows no change to
`backend/open_webui/utils/middleware.py`, `backend/open_webui/tools/builtin.py`,
`backend/open_webui/retrieval/`, `backend/open_webui/main.py` or `backend/open_webui/constants.py`,
so every status text and error text the server writes is upstream wording. In particular the fork
left `Open WebUI: Server Connection Error` unchanged; it is guarded by a licence comment
(`backend/open_webui/constants.py:127-130`). The only server-side fork changes touching this area
are the two settings fields `showInlineCitations` and `hideProcessingDetails`
(`backend/open_webui/models/users.py:99-100`).

The browser side carries the MedIT GPT feature **Hide Processing Details**. Part is committed on
`uoft` (`git diff main...uoft`) and part is uncommitted in the working tree (`git diff`); citations
elsewhere in this document are to the working tree.

### 12.1 Hide Processing Details: What Each File Does

| File | Committed on `uoft` | Uncommitted in the working tree | Effect on in-chat text |
|---|---|---|---|
| `src/lib/components/chat/Messages/ResponseMessage.svelte` | Hides the status line and its history; adds the shimmering `Thinking...` line; hides code execution chips; treats a reply as still running while an approved tool call has no result yet | Refactor: `showStatusHistory` flag; `Thinking...` now drawn with the status component; shown while the reply is not done, has no error, no pending tool call and no answer text; the "approved call still running" rule removed (replaced by the `Chat.svelte` change) | `Thinking...` instead of status lines (5.9) |
| `src/lib/components/chat/Chat.svelte` | None | A resumed reply that reports `done: false` is marked running again, so `Thinking...` and the blinking bar return after **Allow** | `Thinking...` reappears after approval (`src/lib/components/chat/Chat.svelte:2847-2850`; `backend/open_webui/utils/middleware.py:3544-3556`) |
| `src/lib/components/chat/Messages/structuredOutput.ts` | `buildOutputDisplayItems` takes the setting and keeps only tool calls, ungrouped | Same rule restructured (each kept call shown on its own); new `hasPendingToolCall` (a call with status `pending`) | Reasoning, code analysis and grouped lines removed (5.9) |
| `src/lib/components/chat/Messages/StructuredOutputRenderer.svelte` | Passes the setting to the output builder and to the tool card | Stops passing it to the tool card (the card reads it itself) | None beyond the above |
| `src/lib/components/common/ToolCallDisplay.svelte` | New `hideProcessingDetails` property: hides the embed name label and every card except those waiting for **Allow** / **Deny** or an answer | Reads the setting directly instead of the property | Only approval and ask-user cards stay (5.6, 5.9) |
| `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte` | Same rule for `<details>` blocks in older replies and pipe output | Same restructure as `structuredOutput.ts` | As above, for older replies |
| `src/lib/components/chat/Messages/Markdown/HTMLToken.svelte` | Hides `<status title="…">` lines written into the answer text | Condition rewritten; same behaviour | Add-on `<status>` lines hidden |
| `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte` | None | One type comment (`/** @type {any} */`) on `status`; no behaviour change | None |
| `src/lib/components/chat/MessageInput.svelte` | Hides the task list above the composer | None | Task list hidden |
| `src/lib/components/channel/Messages/Message.svelte` | Uses the setting when deciding whether a channel message has structured output to draw | None | Channel replies follow the same rule |
| `src/lib/components/common/InterfaceSettings.svelte`, `src/lib/stores/index.ts`, `backend/open_webui/models/users.py` | The switch and its stored field | None | Settings > Interface |
| `src/lib/i18n/locales/en-US/translation.json` | Label `Hide Processing Details` and the first help text | Help text reworded (below) | What the switch says it does |

The help text changed in the working tree (`src/lib/i18n/locales/en-US/translation.json:2923`):

- Committed: `Show "Thinking..." instead of status updates, tool calls, and reasoning while a response is generated, and keep them hidden afterwards. Tool approval requests and tool outputs such as images still appear.`
- Working tree: `Show "Thinking..." instead of status updates, tool calls, reasoning, and code analysis while a response is generated, and keep them hidden afterwards. Tool approval requests and images or embeds from tools still appear.`

The uncommitted `src/lib/i18n/index.ts` change maps a detected browser language to a bundled locale
and adds `en-US` as a fallback after a site default language (`src/lib/i18n/index.ts:75-86`, `:93`).
For this area it means the dotted settings labels (such as the switch's label) fall back to English
rather than showing the raw key when a site default language lacks them; the plain status-line keys
are English text already (`CLAUDE.md`, i18n).

### 12.2 Other Fork Changes That Touch a Reply

- **Inline Citations** (`showInlineCitations`, committed) removes the `[1]`-style markers from the
  answer text; the source chips under the reply stay
  (`src/lib/components/chat/Messages/ContentRenderer.svelte:128-138`;
  `src/lib/i18n/locales/en-US/translation.json:2935-2936`). It does not change any status or error
  text; see `user-settings-and-personalisation.md`.
- The product name (`MedIT GPT`) does not appear in any status or error text of this area; the
  only product name in these texts is the upstream one in `Open WebUI: Server Connection Error`.

## 13. Source File Index

Files read for this document (working tree of 2026-10-10). "Read" means opened at the cited lines;
the large files were read in the parts listed.

### 13.1 Server

| File | What it contributes here |
|---|---|
| `backend/open_webui/utils/middleware.py` | Every core status event (web search 1560-1730, images 1828-2046, files 2049-2167, knowledge 2604-2617 and 3248-3259); the stored errors (4211-4255, 4855-4867, 5072-5091, 5226-5249, 6328-6346, 6527-6536); MCP and terminal failures (3005-3013, 3061-3063); tool-result error texts (3325-3386, 5975-6060); the approval pause (3613-3655, 5936-5956) and resume (3440-3556); the cancelled state (6604-6631); the error test (158-196); chat finished and failed events (206-235, 4387-4409) |
| `backend/open_webui/main.py` | `chat_completion` (1108-1300), the background task and `chat:active` (1748-1772, 1840-1881), the stored error for path 2 (1659-1712), the resolve endpoint (1893-1910), Stop (2160-2214) |
| `backend/open_webui/socket/main.py` | The event emitter, what it stores (1134-1250), the channel emitter and `Error: {error_content}` (1071-1129) |
| `backend/open_webui/constants.py` | `[ERROR: …]` formatting (6-23), `NOT_FOUND`, `MODEL_NOT_FOUND`, `WEB_SEARCH_ERROR`, the licence-guarded `SERVER_CONNECTION_ERROR` (127-130) |
| `backend/open_webui/routers/retrieval.py` | `process_web_search` and its error details (2883-3047) |
| `backend/open_webui/routers/openai.py`, `backend/open_webui/routers/ollama.py` | Provider errors and the connection error (openai 1530-1760; ollama 150-196) |
| `backend/open_webui/utils/misc.py` | `get_response_error_detail` (43-65) |
| `backend/open_webui/utils/tool_approval.py` | Resolve refusals, deny result, ask-user answers, resume payload (1-186, whole file) |
| `backend/open_webui/utils/ask_user.py` | Ask-user rules and error texts (1-149, whole file) |
| `backend/open_webui/tools/builtin.py` | `ask_user` browser path (520-625), `execute_code` results (633-795), image files event (405-500) |
| `backend/open_webui/utils/context_compaction.py` | Compaction events (60-145) |
| `backend/open_webui/utils/chat.py` | `Model not found`, the direct-connection error (55-195) |
| `backend/open_webui/utils/subagents.py` | Sub-agent errors and summaries (500-535); the internal flag (68) |
| `backend/open_webui/models/chats.py`, `backend/open_webui/models/chat_messages.py`, `backend/open_webui/models/shared_chats.py` | Where status history and errors are stored and read (chats 1020-1275; chat_messages 127-165, 196-263, 340-372; shared_chats 19-29, 81, 107) |
| `backend/open_webui/routers/chats.py` | Chat read (1325-1347) and the message event endpoint (1513-1548) |
| `backend/open_webui/routers/tasks.py` | Query generation switches and the query cache (400-436) |
| `backend/open_webui/tasks.py` | Redis task listener, heartbeat and in-progress reply copy (28-100, 157, 199-260, 296-312) |
| `backend/open_webui/utils/session_pool.py`, `backend/open_webui/env.py`, `backend/open_webui/config.py` | Time limits, tool-call limit, query cache, fallback model (env 370, 387-393, 600-625, 1033, 1082-1098); persistent setting defaults (config 424, 1161-1163, 1351, 1525, 1712-1718, 2194-2198, 2302-2304, DEFAULT_CONFIG 2843-3148) |
| `backend/open_webui/utils/notifications.py`, `backend/open_webui/events.py` | `chat.finished` and `chat.failed` (notifications 255-345; events 155-175) |
| `backend/open_webui/models/users.py` | The fork's two settings fields (99-100) |

### 13.2 Browser: Rendering a Reply

| File | What it contributes here |
|---|---|
| `src/lib/components/chat/Messages/ResponseMessage.svelte` | Order of parts, status visibility, `Thinking...`, blinking bar, error box placement (180-230, 700-960) |
| `src/lib/components/chat/Messages/ResponseMessage/StatusHistory.svelte` | The status line and its history (whole file) |
| `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte` | How each status is worded (whole file) |
| `src/lib/components/chat/Messages/ResponseMessage/WebSearchResults.svelte` | The expandable list of searched pages (1-143) |
| `src/lib/components/chat/Messages/ResponseMessage/TaskList.svelte` | Task list wording (30-32) |
| `src/lib/components/chat/Messages/Error.svelte` | The error box (whole file) |
| `src/lib/components/chat/Messages/structuredOutput.ts` | Building cards and blocks from `output`; the unused summaries; `hasPendingToolCall` (1-460) |
| `src/lib/components/chat/Messages/StructuredOutputRenderer.svelte` | Which component draws each item; resolve toasts (whole file) |
| `src/lib/components/common/ToolCallDisplay.svelte` | Tool card labels, icons, error test, **Output** (whole file) |
| `src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte` | `Exploring` / `Explored` grouping and its buttons (15-323) |
| `src/lib/components/common/Collapsible.svelte` | Reasoning and code-analysis labels (1-184, whole file) |
| `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte`, `src/lib/components/chat/Messages/Markdown/HTMLToken.svelte` | Older replies' `<details>` blocks and add-on `<status>` tags (MarkdownTokens 60-150, 440-570; HTMLToken 86-106) |
| `src/lib/components/chat/Messages/CodeExecutions.svelte`, `src/lib/components/chat/Messages/CodeExecutionModal.svelte`, `src/lib/components/chat/Messages/CodeBlock.svelte` | Code execution chips and window; code-interpreter output parsing (CodeExecutions whole file; modal 14-109; CodeBlock 395-440) |
| `src/lib/components/chat/Messages/SubagentResultRow.svelte` | `Background sub-agent finished` (41) |
| `src/lib/components/chat/Messages/ContentRenderer.svelte` | Inline Citations (128-138) |
| `src/lib/components/chat/AskUserCard.svelte` | The ask-user card (whole file) |

### 13.3 Browser: Chat Logic, Settings and Translation

| File | What it contributes here |
|---|---|
| `src/lib/components/chat/Chat.svelte` | Socket event handling (1160-1430), ask-user handling (520-640), approval mode (425-470), reload reconciliation (2355-2425), completion events (2761-2900), request failures and `handleOpenAIError` (3560-3770), dialogs (4215-4290), manual compaction (2965-3005) |
| `src/lib/apis/openai/index.ts`, `src/lib/apis/chats/index.ts` | Request error text extraction (openai 1-25, 421-451; chats 1-16, 1372-1410) |
| `src/lib/components/chat/MessageInput.svelte`, `src/lib/components/chat/MessageInput/InputMenu.svelte` | Task list switch (1792); Full access / Ask for approval (52-66, 140-160) |
| `src/lib/components/common/InterfaceSettings.svelte`, `src/lib/components/chat/SettingsModal.svelte` | Hide Processing Details and Always Expand Details switches; admin preset merge (InterfaceSettings 20-30, 150-160, 1310-1380; SettingsModal 436-456) |
| `src/lib/components/workspace/Models/Capabilities.svelte` | Model capabilities (1-120) |
| `src/lib/components/chat/Settings/Advanced/AdvancedParams.svelte` | Function Calling (240-270) |
| `src/lib/components/common/FileItemModal.svelte` | Using Entire Document (360-362) |
| `src/lib/components/channel/Messages/Message.svelte` | Channel structured output check (151-156) |
| `src/lib/i18n/locales/en-US/translation.json`, `src/lib/i18n/index.ts` | English text of every key cited; fallback rules (index 75-120) |
| `src/lib/stores/index.ts` | Settings type (229-234) |

Previous researcher's scratch files reused: the status-event grep (`status_sq.txt`), the key list
(`keys.txt`) and the translation lookup script (`i18n_lookup.py`) in this document's scratch
sub-folder.

## 14. Open Questions

Everything below could not be established from the repository, or was established by reading the
code only, without running the application (the research instructions forbid starting it).

### 14.1 TO BE CONFIRMED (Organisational or Live Data)

1. **Live values of every setting in section 7**, in particular whether an admin preset turns on
   Hide Processing Details for everyone (`ui.default_interface_settings`), whether Tool
   Permissions, web search, image generation, context compaction and query generation are on, and
   the environment values of `AIOHTTP_CLIENT_TIMEOUT`, `AIOHTTP_CLIENT_STREAM_IDLE_TIMEOUT`,
   `CHAT_RESPONSE_MAX_TOOL_CALL_ITERATIONS`, `ENABLE_QUERIES_CACHE` and
   `ENABLE_CUSTOM_MODEL_FALLBACK`. These live in the `config` table or the environment.
2. **Which model providers production uses**, and therefore the wording of provider error texts
   in the error box (paths 2 to 4 in 5.5). No provider is recorded in the repository.
3. **Which add-ons (functions, tools, pipes, filters) are installed in production.** Their status
   lines, toasts, dialogs and refusal texts are their own and are not in the repository (5.10).
4. **Whether production runs more than one worker or replica, and with Redis.** Without Redis,
   events can miss the browser (section 8); the deployment is not described in the repository.
5. **The escalation route for platform incidents** such as `Open WebUI: Server Connection Error`
   for every model (11.5). No contact, queue or service level exists in the repository.
6. **Whether to tell users about the upstream name in `Open WebUI: Server Connection Error`.** The
   code marks the text as licence-protected (`backend/open_webui/constants.py:127-130`) and the
   project guidance says to leave such strings and their comments intact (`CLAUDE.md`, Conventions);
   whether MedIT GPT guidance should explain it to users is an organisational decision.
7. **Whether the uncommitted Hide Processing Details changes will be committed** (12.1). If they are
   discarded, the help text, the return of `Thinking...` after **Allow** and some details of 5.9
   revert to the committed behaviour.
8. **Web-search result icons are loaded from Google's favicon service in the person's browser**
   (`src/lib/components/chat/Messages/ResponseMessage/WebSearchResults.svelte:71`, `:111`). Whether
   this outside request is acceptable for MedIT GPT is for the platform maintainer to confirm.

### 14.2 Observed From Code Only (Not Run)

1. A request refused before work begins (path 1 in 5.5, for example `Model not found`) is not
   stored, so the message pair may be missing after a reload (`backend/open_webui/main.py:1129`;
   storage starts after the checks, `:1522-1622`).
2. A tool call cut off by **Stop** shows `View Result from {{NAME}}` with a green tick and no output
   (5.11).
3. The visible status line keeps shimmering on a stopped or interrupted reply, because nothing
   sends a closing status (5.11).
4. For a model with knowledge attached, the closing hidden `knowledge_search` status removes the
   visible `Querying` / `Retrieved {count} sources` line once preparation ends (already noted in 5.3
   by the first researcher).
5. If a provider streams an error whose `error` field is a plain string rather than an object, the
   browser's `handleOpenAIError` tests it with the `in` operator, which fails on a string; the live
   error box may then not appear although the server stored the error
   (`src/lib/components/chat/Chat.svelte:3716-3747`; `backend/open_webui/utils/middleware.py:5226-5249`).
6. The `chat_message.status_history` column lags behind the chat JSON until the next upsert of the
   message (6.1); the screen reads the JSON, so no visible effect was found.
7. The tool-call status `requires_approval` is accepted by the server and the browser but no
   v0.11.4 code sets it (`backend/open_webui/utils/tool_approval.py:57`;
   `backend/open_webui/main.py:2186`); it may come from older data or add-ons.
8. `Generating search query` and `Searching "{{searchQuery}}"` are translated by the browser but
   sent by no server code in v0.11.4; whether a production add-on sends them is unknown (10.1).
9. `Image generation is disabled` is reachable only if the image switch changes between two reads
   a moment apart (10.1); this agrees with `image-generation-and-editing.md`.

### 14.3 Security-Sensitive

- One add-on event type handled in `src/lib/components/chat/Chat.svelte` raises a security
  question. Security-sensitive: refer to the platform maintainer and U of T Information Security
  (security.utoronto.ca).

### 14.4 Corrections and Consistency

- Corrected 2026-10-10 in section 5.3: the expanded `Searched {{count}} sites` line shows no Google
  query link for the core event, because that event carries no `query`
  (`backend/open_webui/utils/middleware.py:1688-1700`).
- Corrected 2026-10-10 in section 5.4: a waiting ask-user call is not drawn in current replies, so
  `Input needed` appears only on replies drawn from `<details>` text
  (`src/lib/components/chat/Messages/structuredOutput.ts:396-402`).
- Corrected 2026-10-10 in At a Glance: the error box is light grey, not red
  (`src/lib/components/chat/Messages/Error.svelte:40-48`), and status wording follows each viewer's
  interface language, not the admin's. Three summary bullets were added there, marked.
- No contradiction with `knowledgebase/tools/ground-truth.md`, `knowledgebase/tools/inventory.md`
  or `CLAUDE.md` was found. `CLAUDE.md` describes Hide Processing Details only as a per-user toggle;
  the browser-side split between committed and uncommitted parts is recorded in section 12.
