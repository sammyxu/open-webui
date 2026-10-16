# The Chat Completion Pipeline and Generation Tasks

## At a Glance

- **What it is.** Everything the server does between a user pressing Send and the last token of the
  answer arriving: checking the request, finding the model and checking access, building the
  prompt (system prompts, variables, files and knowledge, web search, memory, tools), calling the
  provider (Ollama, an OpenAI-compatible connection, a pipe function or the user's own direct
  connection), streaming the answer back, running tools, saving the message, and then running the
  small "background" jobs that name the chat, tag it and suggest follow-up questions.
- **Where it lives.** `POST /api/chat/completions` in `backend/open_webui/main.py:1108-1885` hands
  the work to `backend/open_webui/utils/middleware.py` (prompt building at `:2391-3276`, answer
  handling at `:4211-6733`) and `backend/open_webui/utils/chat.py:148-305` (provider routing).
  Background jobs are in `backend/open_webui/routers/tasks.py`; the running-task registry is
  `backend/open_webui/tasks.py`.
- **How the answer reaches the browser.** For normal chat use the HTTP request returns almost at
  once with a list of task ids (`backend/open_webui/main.py:1851-1881`); the answer itself arrives
  as websocket events (`chat:completion`, `response:completion`, `status`, `chat:message:error`).
  API callers without a websocket session get the answer in the HTTP response instead
  (`backend/open_webui/main.py:1882-1885`).
- **What users see when it fails.** Problems found before the model is called (model not found, no
  access, chat not found) appear as a pop-up **and** a grey error box in the reply. Problems after
  that (provider errors, filter errors, connection failures) appear in the grey error box, and
  provider error chunks also produce a pop-up prefixed in the box with
  `Uh-oh! There was an issue with the response.` (`src/lib/components/chat/Chat.svelte:3643-3668`,
  `:3716-3756`).
- **Stop.** The Stop button (shown while a reply is running and the input is empty) calls
  `POST /api/tasks/chat/{chat_id}/stop`. Without Redis the task list is held separately by each
  server worker process, so with several workers a Stop that lands on the wrong worker does not
  stop the generation (`backend/open_webui/tasks.py:14-17`, `:296-309`).
- **Background tasks.** Title, tags and follow-ups run after the reply (the title for a brand-new
  chat runs immediately, alongside the reply). They use the **Task Model** chosen in
  Admin Settings > Interface (Local Task Model for models on a "local" connection, External Task
  Model for everything else), falling back to the chat's own model
  (`backend/open_webui/utils/task.py:16-27`). If title generation is switched off, or its model
  call fails, the chat is named after the user's first message, but only while the chat holds
  just that first exchange (`backend/open_webui/utils/middleware.py:3990-4000`). A task that
  **raises** (for example the chat's model has dropped out of the server's model list, or a
  Pipelines filter rejects the task call) is not absorbed: the tasks after it are skipped; a new
  chat's title stays `New Chat` and only the server log records why; a follow-up or tag task that
  raises puts a grey error box under the finished answer (streaming replies, the default) or
  publishes a `chat.failed` event although the reply succeeded (non-streaming replies)
  (`backend/open_webui/routers/tasks.py:157-167`, `:197-200`, `:230-235`;
  `backend/open_webui/main.py:1486-1490`, `:1686-1713`;
  `backend/open_webui/utils/middleware.py:4388-4409`; `src/lib/components/chat/Chat.svelte:3488-3492`;
  section 5.8).
- **Code defaults** (live values are data in the `config` table, TO BE CONFIRMED): title, tags,
  follow-up, web-search-query and retrieval-query generation **on**; autocomplete **off**; context
  compaction **off** (threshold 80,000 tokens); sub-agents **off**; tool permissions **off**;
  function calling **native** (`backend/open_webui/config.py:2180-2335`, `:2036-2042`;
  `backend/open_webui/main.py:1290-1294`).
- **This area matches upstream Open WebUI v0.11.4**: no file in scope differs on the `uoft` branch
  or in the working tree. The fork's per-user **Hide Processing Details** setting changes how the
  status lines produced here are displayed (section 12).

## 1. Purpose and Who Uses It

The chat completion pipeline is the engine behind every answer in MedIT GPT. It is not a screen of
its own: it is the server-side path a message takes after the chat composer sends it, and the
place where most "the answer did not come back" problems originate.

Who touches it:

- **Every signed-in user** (role `user` or `admin`) uses it each time they send, regenerate,
  continue or edit-and-resend a message, approve or reject a tool call, or fork or compact a chat.
  The endpoint requires a verified user (`backend/open_webui/main.py:1113`), so the code refuses
  `pending` accounts (see `tools/ground-truth.md`, Accounts and Access).
- **Admins** additionally control the generation tasks and their prompts (Admin Settings >
  Interface), context compaction and tool permissions (same panel), and sub-agents (Admin Settings >
  Sub-agents). Admins can also list and stop any running task by id
  (`backend/open_webui/main.py:2128-2139`).
- **Automations, timers, channels and sub-agents** reuse the same pipeline from inside the server:
  `app.state.CHAT_COMPLETION_HANDLER` exposes `chat_completion` to internal callers
  (`backend/open_webui/main.py:1913-1915`), and sub-agents call it with an internal request
  (`backend/open_webui/utils/subagents.py:487`).
- **API clients** (scripts using an API key, the OpenAI-compatible `/api/v1/chat/completions`
  alias, and the Anthropic-compatible `/api/v1/messages`) go through the same function but without
  a websocket session, so they get the answer in the HTTP response
  (`backend/open_webui/main.py:1109`, `:1882-1885`, `:2002-2068`).

What tier 1 needs from this document: how to recognize which step failed from what the user saw,
which settings govern titles, tags, follow-ups and autocomplete, what Stop really does, and what to
collect before escalating. The composer and message display themselves are documented in
`chat-composer-and-message-display.md`; provider configuration in
`model-connections-openai-ollama-and-direct.md`; the wording of in-chat status lines in
`in-chat-status-and-response-messages.md`.

## 2. Navigation and URLs

### 2.1 Where Users Meet the Pipeline

| What the user does | Where | Evidence |
|---|---|---|
| Sends a message | Chat composer on `/` (new chat) or `/c/{chat_id}` (existing chat); the browser posts to `/api/chat/completions` | `src/lib/components/chat/Chat.svelte:3577-3642`; `src/lib/apis/openai/index.ts:421-451` |
| Stops a reply | **Stop** button in the composer (tooltip and accessible name `Stop`), shown while a reply is running and the input box is empty; the Escape key in the composer does the same | `src/lib/components/chat/MessageInput.svelte:2603-2612`, `:2117-2119`; `src/lib/components/chat/MessageInput.svelte:172-176` |
| Compacts a long chat by hand | Types `/compact` in the composer | `src/lib/components/chat/Chat.svelte:3107-3111`, `:2956-3005` |
| Forks a chat | Types `/fork`, or clicks the **Fork chat** button under a finished reply | `src/lib/components/chat/Chat.svelte:3117-3121`; `src/lib/components/chat/Messages/ResponseMessage.svelte:1552-1560` |
| Checks context size and copies the chat id | Types `/status`: a **Status** panel shows "Context usage", queued messages, tasks and a copyable "Chat ID" | `src/lib/components/chat/Chat.svelte:3112-3116`; `src/lib/components/chat/MessageInput.svelte:1816-1890` |
| Regenerates a chat title | Sidebar chat rename field, **Generate** button (placeholder `Generating...` while it runs) | `src/lib/components/layout/Sidebar/ChatItem.svelte:440-511`, `:628`, `:703-709` |
| Merges several models' answers | **Merge Responses** button under side-by-side answers | `src/lib/components/chat/Messages/MultiResponseMessages.svelte:439-447`; `src/lib/components/chat/Chat.svelte:3901-3953` |
| Approves or rejects a tool call | Approval card in the reply when tool permissions are on | `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte:120-140` |

### 2.2 Admin Screens

Admin settings now open inside the Settings dialog: the route `/admin/settings/{tab}` redirects to
`/?settings=admin:{tab}` (`src/routes/(app)/admin/settings/[tab]/+page.svelte:6-10`).

| Screen | URL | Contents | Evidence |
|---|---|---|---|
| Admin Settings > Interface (group "Experience") | `/admin/settings/interface` | Sections **Tasks** (task models and parameters), **Chat** (Tool Permissions, Context Compaction and its options) and **Generation** (title, voice mode, follow-up, tags, query, autocomplete, image-prompt and tools prompts) | `src/lib/components/chat/SettingsModal.svelte:170`, `:879-884`; `src/lib/components/admin/Settings/Interface.svelte:163-569` |
| Admin Settings > Sub-agents (group "AI") | `/admin/settings/subagents` | Enable sub-agents, Max concurrent, Enable background sub-agents, Max background, Max iterations, Max output, System prompt | `src/lib/components/chat/SettingsModal.svelte:162`, `:293-296`, `:865-866`; `src/lib/components/admin/Settings/Subagents.svelte:59-200` |

### 2.3 API Endpoints in This Area

All paths are relative to the site root; the production host is TO BE CONFIRMED.

| Method and path | Who | Purpose | Evidence |
|---|---|---|---|
| `POST /api/chat/completions` (alias `/api/v1/chat/completions`) | Verified user | Run a chat turn | `backend/open_webui/main.py:1108-1885` |
| `POST /api/v1/chats/{id}/messages/{message_id}/resolve` | Verified user (chat owner or admin) | Approve, reject or answer a paused tool call, then resume the reply | `backend/open_webui/main.py:1893-1910`; `backend/open_webui/utils/tool_approval.py:20-186` |
| `POST /api/chat/completed` | Verified user | **Deprecated**: runs outlet filters for external integrations; the pipeline now runs them inline | `backend/open_webui/main.py:2090-2107` |
| `POST /api/chat/actions/{action_id}` | Verified user | Runs an Action function's button on a message | `backend/open_webui/main.py:2110-2125`; `backend/open_webui/utils/actions.py:19-160` |
| `GET /api/tasks` | Admin | List every running task id | `backend/open_webui/main.py:2137-2139` |
| `POST /api/tasks/stop/{task_id}` | Admin | Stop one task | `backend/open_webui/main.py:2128-2134` |
| `GET /api/tasks/chat/{chat_id}` | Verified user (owner or admin; others get an empty list) | Task ids running for a chat | `backend/open_webui/main.py:2142-2157` |
| `POST /api/tasks/chat/{chat_id}/stop` | Verified user (owner or admin) | Stop every task of a chat (the Stop button) | `backend/open_webui/main.py:2160-2214` |
| `GET /api/v1/tasks/config`, `POST /api/v1/tasks/config/update` | Verified user to read; admin to change | Task settings | `backend/open_webui/routers/tasks.py:108-138` |
| `POST /api/v1/tasks/title/completions`, `/follow_up/completions`, `/tags/completions`, `/image_prompt/completions`, `/queries/completions`, `/auto/completions`, `/emoji/completions`, `/moa/completions` | Verified user | One generation task each | `backend/open_webui/routers/tasks.py:141-660` (router mounted at `/api/v1/tasks`, `backend/open_webui/main.py:848`) |
| `GET /api/v1/chats/config`, `POST /api/v1/chats/config` | Admin | Context compaction and tool-permission settings | `backend/open_webui/routers/chats.py:836-856` |
| `POST /api/v1/chats/{id}/compact` | Chat owner | Manual compaction (`/compact`) | `backend/open_webui/routers/chats.py:1271-1316` |
| `POST /api/v1/chats/{id}/fork` | Chat owner with `chat.import` permission | Fork a chat at a message | `backend/open_webui/routers/chats.py:1672-1772` |
| `GET /api/v1/configs/subagents`, `POST /api/v1/configs/subagents` | Admin | Sub-agent settings | `backend/open_webui/routers/configs.py:783-800` |

Related endpoints owned by neighbouring areas: the Anthropic-compatible `/api/v1/messages`
(`backend/open_webui/main.py:2002-2068`) reuses this pipeline; `GET /api/usage` (models in use)
belongs to `evaluations-feedback-and-analytics.md`.

## 3. Roles and Permissions

### 3.1 Who May Run a Chat Turn

- **Signed-in, verified users only.** `chat_completion` depends on `get_verified_user`
  (`backend/open_webui/main.py:1113`), which admits roles `user` and `admin` (ground truth: role
  checks answer 401 with `ACCESS_PROHIBITED`).
- **Model access.** For a server-side model the code checks access unless
  `BYPASS_MODEL_ACCESS_CONTROL` is on, or the user is an admin and `BYPASS_ADMIN_ACCESS_CONTROL` is
  on (`backend/open_webui/main.py:1149-1161`). The check (`check_model_access`,
  `backend/open_webui/utils/models.py:465-521`) refuses with the plain text `Model not found` when
  the model has no workspace record, when the user has no read grant, or when a chained base model
  is not accessible. A refused model therefore looks exactly like a missing one to the user. A
  second check runs again at the provider call for role `user` (`backend/open_webui/utils/chat.py:198-203`).
- **Chat ownership.** Posting into an existing saved chat requires owning it, or being an admin;
  otherwise the reply is HTTP 404 with `Something went wrong :/`
  (`backend/open_webui/main.py:1494-1499`). Starting a new chat inside a folder requires write
  access to the folder, else HTTP 404 `We could not find what you're looking for :/`
  (`backend/open_webui/main.py:1353-1360`).
- **Channels.** When the pipeline answers in a channel (`chat_id` beginning `channel:`), the caller
  must be a member (group and direct-message channels) or hold write access, and may only target
  their own messages; failures return HTTP 403 `Something went wrong :/`
  (`backend/open_webui/main.py:1311-1350`). The `/api/chat/completed` and `/api/chat/actions`
  endpoints refuse channel chats with `Channel chats are not supported on this endpoint`
  (`backend/open_webui/main.py:2076-2081`).

### 3.2 Feature Permissions Re-checked Inside the Pipeline

The browser sends a `features` object (web search, image generation, code interpreter, memory,
voice; `src/lib/components/chat/Chat.svelte:3393-3417`). Because it is client-supplied, the server
re-checks the matching permission before acting, admins always passing:

| Feature | Global switch | Permission re-checked | Evidence |
|---|---|---|---|
| Memory context | `memories.enable` and `memories.system_context.enable` | `features.memories` | `backend/open_webui/utils/middleware.py:2686-2698` |
| Web search (legacy mode) | `web.search.enable` | `features.web_search` | `backend/open_webui/utils/middleware.py:2700-2709` |
| Image generation (legacy mode) | `image_generation.enable` / `images.edit.enable` | `features.image_generation` | `backend/open_webui/utils/middleware.py:2711-2720`, `:1865-1868` |
| Code interpreter tag detection (legacy mode) | `code_interpreter.enable` | `features.code_interpreter` | `backend/open_webui/utils/middleware.py:4877-4891` |
| User-supplied tool servers | none | `features.direct_tool_servers` (otherwise silently dropped) | `backend/open_webui/main.py:1240-1252` |

In native mode the equivalent checks live in the built-in tool registration
(`backend/open_webui/utils/tools.py:538-800`; see `builtin-native-tools.md`).

### 3.3 Stopping, Listing and Resolving

| Action | Allowed for | Evidence |
|---|---|---|
| Stop all tasks of a chat (Stop button) | Chat owner or admin; others get HTTP 404 | `backend/open_webui/main.py:2160-2171` |
| List task ids of a chat | Chat owner or admin; others get an empty list rather than an error | `backend/open_webui/main.py:2142-2157` |
| List all tasks, stop a task by id | Admin only | `backend/open_webui/main.py:2128-2139` |
| Resolve (approve, reject, answer) a paused tool call | Chat owner or admin; others get HTTP 401 `ACCESS_PROHIBITED` | `backend/open_webui/utils/tool_approval.py:27-32` |

### 3.4 Settings and Chat Management

- Changing task settings (`POST /api/v1/tasks/config/update`), the compaction and tool-permission
  settings (`POST /api/v1/chats/config`) and sub-agent settings (`POST /api/v1/configs/subagents`)
  requires an admin (`backend/open_webui/routers/tasks.py:135-138`;
  `backend/open_webui/routers/chats.py:841-856`; `backend/open_webui/routers/configs.py:788-792`).
  Any verified user can **read** the task settings, including the prompt templates
  (`backend/open_webui/routers/tasks.py:108-110`).
- **Forking** needs the `chat.import` permission (admins skip it), else HTTP 403 with the
  `ACCESS_PROHIBITED` text; the browser hides the Fork chat button and shows `Access prohibited` for
  `/fork` when the permission is missing (`backend/open_webui/routers/chats.py:231-238`, `:1681`;
  `src/lib/components/chat/Chat.svelte:3051-3054`;
  `src/lib/components/chat/Messages/ResponseMessage.svelte:1552`).
- **Manual compaction** works only on the caller's own chat; another user's chat gives HTTP 401
  `We could not find what you're looking for :/` (`backend/open_webui/routers/chats.py:1279-1281`).
- **Background tasks use the user's own access.** Title, tag, follow-up, query and autocomplete
  calls go through the same access check for role `user` (`backend/open_webui/utils/chat.py:198-203`).
  If the configured Task Model is not readable by an ordinary user, those tasks fail for ordinary
  users but still work for admins. The Interface panel warns the admin when a non-public model is
  picked: `This model is not publicly available. Please select another model.`
  (`src/lib/components/admin/Settings/Interface.svelte:103-110`).
- Sub-agents act as the same user, with that user's tools and files. The code refuses further
  delegation from a sub-agent (`backend/open_webui/tools/builtin.py:1703-1704`) and leaves out the
  built-in tools that change memories (`backend/open_webui/utils/tools.py:766-769`;
  `backend/open_webui/utils/subagents.py:34-39`).

## 4. Key Concepts and Terminology

| Term | Plain meaning | Evidence |
|---|---|---|
| **Chat turn** | One Send: a user message plus one assistant reply per selected model. Side-by-side models share one request; the server starts one task per model ("fan out"). | `backend/open_webui/main.py:1802-1881` |
| **Message tree** | Messages are stored as a tree: each has a `parentId` and `childrenIds`, so edits and regenerations create branches. `history.currentId` points at the branch the user is viewing. | `backend/open_webui/main.py:1362-1404`; `backend/open_webui/utils/misc.py:182-214` |
| **Assistant placeholder** | Before the model is called, the server saves an empty assistant message with `done: false` for each model. The reply later fills it in. | `backend/open_webui/main.py:1373-1391`, `:1597-1633` |
| **Task** and **task id** | The background job that produces one reply. Its id is returned to the browser and is what Stop cancels. Tasks are grouped by chat id. | `backend/open_webui/main.py:1815-1857`; `backend/open_webui/tasks.py:157-178` |
| **Session id** | The id of the browser's websocket connection. Its presence tells the server "this came from the web interface, stream over the websocket"; its absence means "API caller, answer over HTTP". | `backend/open_webui/main.py:1803`, `:1882-1885` |
| **Event emitter / event caller** | Server functions that push events to the user's browser (emitter) or ask the browser to do something and wait for the answer (caller: direct tools, browser-side Python, direct connections). | `backend/open_webui/utils/middleware.py:3279-3294`; `backend/open_webui/socket/main.py:1134-1289` |
| **Status** | A progress line under the reply ("Searching the web", "Creating image"). Saved in the message's `statusHistory`. | `backend/open_webui/socket/main.py:1166-1171` |
| **Output items** | The structured form of a reply (OpenAI Responses-style items: `message`, `reasoning`, `function_call`, `function_call_output`, `open_webui:code_interpreter`). Stored in the message's `output`. | `backend/open_webui/utils/middleware.py:593-937`; `backend/open_webui/utils/misc.py:325-574` |
| **Native function calling** (default) | The model is given the tool list and decides itself when to call tools (including built-in web search, knowledge, image and code tools). | `backend/open_webui/main.py:1290-1294`; `backend/open_webui/utils/middleware.py:3189-3195` |
| **Legacy function calling** | Before the main call, the Task Model is asked which tool to use (one round, by prompt), and web search, image generation, knowledge and code-interpreter prompts are run or injected by the pipeline itself. | `backend/open_webui/utils/middleware.py:1334-1557`, `:2604-2751`, `:3196-3204`; label text `settings.personal.general.parameters.functionCalling.description` (`src/lib/i18n/locales/en-US/translation.json:2825`) |
| **Task Model** | The model used for background jobs. "Local Task Model" applies when the chat model's connection type is `local` (Ollama connections by default); "External Task Model" applies to every other model. Empty means "use the chat's own model". | `backend/open_webui/utils/task.py:16-27`; `backend/open_webui/routers/ollama.py:425`; `backend/open_webui/routers/openai.py:732` |
| **Background (generation) tasks** | Short extra model calls: title, tags, follow-ups, search/retrieval queries, autocomplete, emoji, image prompt, tool selection, response merging. Each is tagged in its request metadata with a `task` name from the `TASKS` list. | `backend/open_webui/constants.py:135-148`; `backend/open_webui/routers/tasks.py:184-194` |
| **Filters** (inlet, stream, request, outlet) | Admin-installed functions that can change the request before the model (inlet, request), each streamed chunk (stream), or the finished messages (outlet). | `backend/open_webui/utils/middleware.py:2655-2670`, `:3261-3272`, `:5101-5109`, `:4050-4208`; details in `functions-pipes-filters-actions-and-pipelines.md` |
| **Pipe** | A function that acts as a model; the pipeline hands it the request instead of calling a provider. | `backend/open_webui/utils/chat.py:280-282` |
| **Direct connection** | A model connection configured in the user's own settings; the browser, not the server, calls the provider, relayed over the websocket. | `backend/open_webui/main.py:1162-1164`; `backend/open_webui/utils/chat.py:49-145`; `src/routes/+layout.svelte:646-731` |
| **Arena model** | A model that secretly picks one of several real models at random for blind comparison; the pick is saved as `selectedModelId`. | `backend/open_webui/utils/middleware.py:2400-2427`; `:4257-4265` |
| **Temporary chat** | A chat that is not saved. Its id starts `temporary:` (legacy `local:`); the server skips all saving and title/tag work for it. | `backend/open_webui/utils/chat_id.py:4-27`; `backend/open_webui/utils/middleware.py:3939` |
| **Internal chat** | A server-created chat (sub-agent run, note assistant, timer) marked `internal` in its metadata. | `backend/open_webui/utils/subagents.py:428-435`; `backend/open_webui/utils/middleware.py:2784` |
| **Context compaction** | When a chat grows past a token threshold, older messages are summarized by a model and only the summary plus recent messages are sent. The summary is stored on a message as `contextSummary`, a "checkpoint". | `backend/open_webui/utils/context_compaction.py:42-147` |
| **Sub-agent** | A separate, hidden chat the assistant can start with the built-in `delegate_task` tool to work on a sub-task, either waiting for it (foreground) or continuing while it runs (background). | `backend/open_webui/utils/subagents.py:270-702`; `backend/open_webui/tools/builtin.py:1680-1718` |
| **Fork** | A new chat copied from one branch of an existing chat, up to a chosen message, titled `{original title} (fork)`. | `backend/open_webui/routers/chats.py:1672-1772`; `backend/open_webui/utils/chat_fork.py:4-41` |
| **Resolve** | Answering a paused tool call (approve, reject, or answer an `ask_user` question), which resumes the reply. | `backend/open_webui/utils/tool_approval.py:13-128` |
| **Usage** | Token counts (and any cost fields) reported by the provider, normalized to `input_tokens`, `output_tokens`, `total_tokens` and saved on the reply. | `backend/open_webui/utils/response.py:13-143` |
| **Prompt variables** | Placeholders such as `{{USER_NAME}}`, `{{CURRENT_DATE}}`, `{{prompt}}`, `{{MESSAGES:END:6}}` filled in before a prompt is sent. | `backend/open_webui/utils/task.py:30-257`; `src/lib/utils/index.ts:1219-1231` |
| **Chat variables / user variables** | `{{chat.variables.<key>}}` placeholders in a model's system prompt that the user fills in per chat, and `{{user.variables.<key>}}` values the user stores in their settings. | `backend/open_webui/utils/chat_variables.py:8-288` |

## 5. Workflows (Step by Step)

### 5.1 From Send to the Last Token (Overview)

1. **The browser checks the basics** (a prompt or file is present, a model is selected, required
   chat variables are filled in, file count within limits) and posts the turn to
   `/api/chat/completions` with the model, the new user message, an id for each assistant
   placeholder, the websocket `session_id`, the chosen tools, features, files and a
   `background_tasks` object (`src/lib/components/chat/Chat.svelte:3134-3166`, `:3577-3642`).
2. **The server accepts the request synchronously**: it resolves the model, checks access, merges
   parameters, creates or updates the chat, saves the user message and an empty assistant
   placeholder per model (`backend/open_webui/main.py:1115-1636`). Anything that fails here comes
   back as an HTTP error, which the browser shows as a pop-up and an error box.
3. **One background task per model is started** and the HTTP call returns
   `{"status": true, "task_ids": [...], "chat_id": ...}`; a `chat:active` event marks the chat busy
   (`backend/open_webui/main.py:1802-1881`). For a brand-new chat, title generation starts at the
   same moment (`backend/open_webui/main.py:1471-1492`).
4. **Inside the task the prompt is built** (`process_chat_payload`,
   `backend/open_webui/utils/middleware.py:2391-3276`): history reloaded from the database, context
   compaction, system prompt and variables, folder ("project") prompt and files, model knowledge,
   pipeline and filter inlets, voice/memory/web search/image/code-interpreter features, skills,
   tools, attached files (retrieval), request filters.
5. **Approved tool calls are drained** if this is a resume after a tool approval
   (`backend/open_webui/main.py:1654-1655`; `backend/open_webui/utils/middleware.py:3412-3610`).
6. **The provider is called** (`backend/open_webui/utils/chat.py:148-305`): direct connection via the
   browser, arena pick, pipe function, Ollama, or an OpenAI-compatible connection.
7. **The answer is streamed** to the browser over the websocket as `response:completion` and
   `chat:completion` events, while reasoning, tool calls, citations, images and usage are separated
   out (`backend/open_webui/utils/middleware.py:4431-5821`).
8. **Tool calls are executed** and the model is called again with the results, up to the iteration
   limit; with tool permissions in "ask" mode the reply pauses for approval
   (`backend/open_webui/utils/middleware.py:5891-6346`).
9. **The final reply is saved once** with its output and usage, a `chat.finished` event is published,
   and a final `chat:completion` with `done: true` is sent (`backend/open_webui/utils/middleware.py:6538-6580`).
10. **Outlet filters run inline**, then **background tasks** (follow-ups, title, tags, memory review)
    (`backend/open_webui/utils/middleware.py:6582-6590`, `:3832-4047`, `:4050-4208`); for a
    brand-new chat the title is left to the job started in step 3, and a task that raises can put
    an error box under the finished answer (section 5.7).
11. **The task ends**: it is removed from the registry, `chat:active` false is sent when no other
    task of the chat remains, and any queued internal messages (finished background sub-agents,
    timers) are processed (`backend/open_webui/main.py:1723-1800`).

### 5.2 Accepting the Request (Synchronous Part)

Everything below happens before the HTTP call returns (`backend/open_webui/main.py:1108-1645`).

1. **Model list.** If the server's in-memory model list is empty it is rebuilt
   (`backend/open_webui/main.py:1115-1116`; caching is described in
   `model-connections-openai-ollama-and-direct.md`).
2. **Model resolution.** The `model` id must be in the list, else `Model not found`
   (`backend/open_webui/main.py:1128-1129`). Its workspace record is read; if it is a custom model
   whose base model has disappeared, the request fails with `Model not found`, unless the
   environment switch `ENABLE_CUSTOM_MODEL_FALLBACK` is on, in which case the first model of the
   **default models** setting (`ui.default_models`) is used instead
   (`backend/open_webui/main.py:1133-1147`, `:1179-1185`).
3. **Access check** as in section 3.1 (`backend/open_webui/main.py:1149-1161`). A direct connection
   skips this and is used as supplied (`backend/open_webui/main.py:1162-1164`).
4. **Parameters.** Global defaults (`models.default_params`) are overlaid by the model's own
   parameters, then by the request's non-empty parameters (`backend/open_webui/main.py:1169-1177`;
   `backend/open_webui/utils/misc.py:34-40`). A model-level **Stream Chat Response** value overrides
   the browser's stream choice (`backend/open_webui/main.py:1193-1194`). If streaming and the model's
   **usage** capability is on, the provider is asked to include token usage
   (`backend/open_webui/main.py:1196-1198`).
5. **Intent.** `parent_id: null` with no `chat_id` means "new chat"; a value means "follow-up in an
   existing chat"; no `parent_id` at all means a legacy or API caller with no chat management
   (`backend/open_webui/main.py:1209-1215`).
6. **Metadata** collects the user, chat, message ids, session id, tools, tool servers (dropped if
   the user lacks `features.direct_tool_servers`), files, features, variables, function-calling mode
   (default `native`) and tool approval mode (`full` unless tool permissions are on and the chat
   chose `ask`; always `full` for automations and channels) (`backend/open_webui/main.py:1240-1297`).
7. **New chat.** A chat id is minted, the chat row is created titled `New Chat` with the user
   message and every assistant placeholder, `chat.created` and `message.created` events are
   published, attached files are linked to the chat, and title generation starts in parallel
   (`backend/open_webui/main.py:1299-1492`).
8. **Existing chat.** Ownership is checked, the chat's file list, selected models and chat variables
   are updated, the user message is upserted and linked under its parent, timers set to cancel on
   "user message" are cancelled, attached files are linked, and the assistant placeholders are saved
   (`backend/open_webui/main.py:1493-1633`). The server, not the browser, now owns saving.
9. Any unexpected exception in this part becomes HTTP 400 with the exception text as `detail`
   (`backend/open_webui/main.py:1638-1645`).

### 5.3 Building the Prompt (`process_chat_payload`)

Order of work in `backend/open_webui/utils/middleware.py:2391-3276`:

1. **Arena pick.** An arena model is replaced by a random eligible model now, so every later step
   uses the real model's settings (`:2400-2427`).
2. **Parameters applied** to the request body; Open WebUI-only parameters (`stream_response`,
   `stream_delta_chunk_size`, `function_calling`, `reasoning_tags`, `compact_token_threshold`,
   `system`, `note_id`, `tool_approval_mode`) are removed before the provider sees them; Ollama
   models get parameters as `options` (`:2430-2433`; `backend/open_webui/utils/payload.py:85-132`).
3. **Guided regeneration.** A `regeneration_prompt` is lifted out and later appended as an extra user
   message (`:2435-2436`, `:2481-2482`).
4. **History from the database.** For saved chats the conversation is rebuilt from the database up to
   the new user message, keeping structured tool output the browser would strip; assistant messages
   that only hold an error are left out; images attached to user messages are re-inserted as image
   parts. When continuing a reply, its existing text is appended (`:2438-2479`, `:2221-2243`).
5. **Context compaction** (section 5.13) may replace older messages with a
   `[CONVERSATION SUMMARY]` system note; if compaction fails the full history is used and only a log
   line records it (`:2484-2513`).
6. **Stored output converted** to provider messages (tool calls and results paired, provider-bound
   reasoning details dropped when the model changed, unpaired tool calls removed) (`:2515-2527`).
7. **System prompt variables** in the chat's system message are rendered (`:2529-2536`;
   `backend/open_webui/utils/payload.py:17-65`); remote image links are converted to inline data
   (`:2538`, `:2170-2218`).
8. **Folder ("project")**: the folder's system prompt is added; folder files are added as retrieval
   files in legacy mode or exposed to the built-in knowledge tools in native mode (`:2573-2602`).
9. **Model knowledge**: in legacy mode the model's knowledge bases are added as retrieval files and a
   `knowledge_search` status is shown; in native mode they are offered through tools instead
   (`:2604-2644`, `:3104-3123`).
10. **Pipeline inlet filters**, then **function inlet filters** (errors stop the turn) (`:2649-2670`).
11. **Features**: voice-mode system prompt (`task.voice.prompt.enable`), memory context, web search,
    image generation and code-interpreter prompt. Web search and image generation run here only in
    **legacy** mode; in native mode the model gets tools instead (`:2672-2751`).
12. **Skills**: mentioned skills are inlined; other available skills are listed for the
    `view_skill` tool; an empty message that only mentioned skills is replaced by the skill names
    (`:2753-2922`).
13. **Tools**: workspace tools, MCP tool servers (a connection failure shows an error but the turn
    continues), terminal tools (a failure stops the turn with `Terminal unavailable: {e}`),
    user-supplied tool servers and built-in tools. Native mode passes the tool list to the model;
    legacy mode asks the Task Model to choose (`:2945-3204`).
14. **Files and retrieval**: unless the model's **file context** capability is off, attached files
    are searched (with generated queries unless every file is in full-context mode); a
    `queries_generated` and a `sources_retrieved` status are shown; retrieval errors are logged and
    the turn continues without sources (`:3206-3214`, `:2049-2167`).
15. **Source context** is inserted using the RAG template, into the user message by default or into
    the system message when `RAG_SYSTEM_CONTEXT` is on (`:3234-3236`, `:972-1007`); sources are
    queued for display (`:3238-3246`).
16. **Request filters** run last, then system messages are merged into one and empty text blocks
    removed (`:3261-3274`; `backend/open_webui/utils/misc.py:631-655`, `:747-765`).

### 5.4 Calling the Provider (`generate_chat_completion`)

`backend/open_webui/utils/chat.py:148-305` chooses the route:

| Route | When | What happens | Evidence |
|---|---|---|---|
| Direct connection | The request carried a user-configured model | The server asks the user's browser (over the websocket) to call the provider and relay the stream; with no live browser session it fails with `Direct connection requires an active WebSocket session; cannot generate completion in this context (e.g. background task).` | `backend/open_webui/utils/chat.py:49-145`, `:195-196`; `src/routes/+layout.svelte:646-731` |
| Arena | Model is an arena wrapper not already resolved | Random pick, access re-checked, `selected_model_id` added to the response | `backend/open_webui/utils/chat.py:205-278` |
| Pipe function | Model has `pipe` | The function's own code produces the answer | `backend/open_webui/utils/chat.py:280-282` |
| Ollama | Model `owned_by` `ollama` | Request converted to Ollama format; Ollama replies converted back to OpenAI format (including usage) | `backend/open_webui/utils/chat.py:283-299`; `backend/open_webui/utils/payload.py:357-445`; `backend/open_webui/utils/response.py:146-270` |
| OpenAI-compatible | Everything else | Sent to the configured connection | `backend/open_webui/utils/chat.py:300-305`; `backend/open_webui/routers/openai.py:1487-1752` |

If the provider answers with an HTTP error, the route returns an error response rather than
raising; the pipeline turns it into a failure using the provider's own error text, or
`Provider returned HTTP {status_code}` when the body is not readable
(`backend/open_webui/main.py:1659-1665`; `backend/open_webui/utils/misc.py:43-65`). Connection
failures appear as `Open WebUI: Server Connection Error` (`backend/open_webui/routers/openai.py:1745-1751`;
`backend/open_webui/constants.py:130`). Provider-specific messages are catalogued in
`model-connections-openai-ollama-and-direct.md`.

### 5.5 Streaming the Answer Back: Websocket Versus HTTP

- **Web interface (session id present).** The reply is produced inside the background task and
  every piece is pushed as a websocket event to the user's personal room `user:{user_id}`
  (`backend/open_webui/socket/main.py:1149-1161`). Text arrives as `response:completion` events
  carrying OpenAI Responses-style deltas; whole-output refreshes, usage, errors and the final
  `done: true` arrive as `chat:completion` (`backend/open_webui/utils/middleware.py:4991-5058`,
  `:6575-6580`). Small deltas can be batched: the batch size is the larger of
  `CHAT_RESPONSE_STREAM_DELTA_CHUNK_SIZE` (environment, default 1) and the model or chat
  **Stream Delta Chunk Size** parameter (`backend/open_webui/utils/middleware.py:4928-4931`).
- **Tokens are not written to the database while streaming.** The in-progress text is kept in a
  "response stream" store (Redis hash with a one-hour expiry by default, or the worker's memory
  without Redis), and the final reply is written once at the end
  (`backend/open_webui/utils/middleware.py:4939-4961`, `:6552-6563`;
  `backend/open_webui/tasks.py:199-223`). If the user reloads the chat mid-reply, the chat fetch
  overlays the in-progress text from that store (`backend/open_webui/routers/chats.py:62-85`,
  `:1338-1343`).
- **What else is extracted from the stream**: reasoning (`<think>` and seven other tag pairs, or the
  provider's reasoning field) becomes a collapsible reasoning item unless the **Reasoning Tags**
  parameter is set to off (`backend/open_webui/utils/middleware.py:242-251`, `:4869-4898`); URL
  citations become sources (`:5254-5284`, `:5141-5173`); inline images are stored as files
  (`:5407-5430`); a pipe or filter may embed its own events in the stream (`:5112-5113`).
- **Bad lines are skipped silently.** A chunk that cannot be parsed, or that makes a **stream
  filter** fail, is logged at debug level and dropped; the stream carries on
  (`backend/open_webui/utils/middleware.py:5725-5733`). A provider that sends a plain JSON error
  line, or an error chunk with no choices, produces a `chat:completion` event with `error` and the
  error is saved on the message (`:5070-5093`, `:5226-5249`).
- **Very long lines.** When `CHAT_STREAM_RESPONSE_CHUNK_MAX_BUFFER_SIZE` is set, a single stream line
  longer than that many bytes is dropped (`backend/open_webui/utils/misc.py:1272-1318`).
- **API callers (no session id).** The pipeline returns the provider's stream (or JSON) to the HTTP
  caller, passing each chunk through stream filters and running outlet filters at the end when
  `ENABLE_API_OUTLET_FILTERS` is on (default on). A failure mid-stream ends the stream with an error
  frame whose message is `Chat completion stream failed` (`backend/open_webui/utils/middleware.py:6644-6717`,
  `:4413-4428`).
- **Several workers without a Redis websocket manager.** Events are emitted only by the worker
  running the task, and only if the user's socket is connected to that same worker or
  `WEBSOCKET_MANAGER=redis` is set (`backend/open_webui/socket/main.py:1150-1161`). Otherwise the
  user sees nothing until the reply is finished and the chat is reloaded. See
  `websockets-realtime-and-redis.md`.

### 5.6 Tools, Approval Pauses and the Tool Loop

1. **Native mode.** When the streamed reply ends with tool calls, the pipeline records each call
   as a `function_call` item, runs the tools (sub-agent `delegate_task` calls in parallel, others one
   after another), records `function_call_output` items (status `failed` when the result looks like
   an error), extracts citations from `fetch_url`, `view_file`, `view_knowledge_file`,
   `query_knowledge_files` and `query_chat_files` results when the model's **citations** capability
   is on, and calls the model again with the results (`backend/open_webui/utils/middleware.py:5767-5821`,
   `:5891-6337`).
2. **Malformed tool arguments** are not fatal: the model receives an error text asking it to try
   again (`backend/open_webui/utils/middleware.py:5964-5997`, `:6050-6060`).
3. **Iteration limit.** The loop stops after `CHAT_RESPONSE_MAX_TOOL_CALL_ITERATIONS` rounds
   (environment, default 256; `-1` for unlimited; sub-agents use their own **Max iterations**) and
   shows `Tool-call limit reached ({max_tool_call_iterations} iterations).` in the error box
   (`backend/open_webui/env.py:1082-1098`; `backend/open_webui/utils/middleware.py:5830-5835`,
   `:6339-6346`; `backend/open_webui/utils/subagents.py:451`).
4. **A failed continuation** (the follow-up model call after tools) shows the error in the error box
   and ends the loop (`backend/open_webui/utils/middleware.py:6328-6337`).
5. **Approval ("ask" mode).** When an admin has switched on **Tool Permissions** and the chat uses
   "Ask for approval", the reply is saved with the pending calls and paused before any tool runs
   (`backend/open_webui/utils/middleware.py:5934-5956`, `:3613-3655`). The built-in `ask_user` tool
   pauses the same way to ask the user a question (`:5897-5914`). The reply resumes through the
   resolve endpoint (section 5.15).
6. **Legacy mode** asks the Task Model, with the **Tools Function Calling Prompt**, which tool to call
   (once, before the main answer); the tool result is added as context and shown as a citation
   (`backend/open_webui/utils/middleware.py:1334-1557`).
7. **Code interpreter in legacy mode**: `<code_interpreter>` blocks in the reply are executed in the
   browser (Pyodide) or on Jupyter and the model is called again, up to five times
   (`backend/open_webui/utils/middleware.py:6348-6536`). Details in
   `code-execution-and-interpreter.md`.

### 5.7 Finishing: Saving, Outlet Filters and Background Tasks

1. Every item still `in_progress` is marked `completed`; the full output and usage are saved with
   `done: true`; the in-progress stream store is cleared (`backend/open_webui/utils/middleware.py:6538-6565`).
2. A `chat.finished` event is published for saved, non-internal chats (feeds webhooks and user
   notifications) and the chat list is refreshed (`backend/open_webui/utils/middleware.py:206-235`, `:6566-6573`).
3. The final `chat:completion` with `done: true`, the full output, the current chat title and usage
   is sent (`backend/open_webui/utils/middleware.py:6543-6580`).
4. **Outlet filters** run inline (pipeline outlets, then function outlets). If they change a
   message, the new text is saved with the original kept as `originalContent`, and a `chat:outlet`
   event updates the browser. Errors here are logged at debug level and otherwise ignored
   (`backend/open_webui/utils/middleware.py:4050-4208`).
5. **Background tasks** run: follow-ups, then title and tags (saved chats only), then the memory
   review (`backend/open_webui/utils/middleware.py:3832-4047`). If the chat was deleted while the
   reply streamed, they are skipped (`:3843-3847`). For a brand-new chat the title is not part of
   this step: the server takes it out of the request and runs it in the separate initial title
   job (`backend/open_webui/main.py:1302-1304`, `:1471-1492`), so here it runs only when a first
   message is sent to an existing chat id (embedded chats) or an API caller asks for it
   (`src/lib/components/chat/Chat.svelte:3628-3640`). How failures in this step behave is
   described below the list ("When a background task fails").
6. The task finishes; its id is removed from the registry; when no other task of the chat remains,
   `chat:active` false is sent and pending internal messages (finished background sub-agents,
   timers) are turned into the next turn (`backend/open_webui/main.py:1748-1800`).

The non-streaming path (model parameter Stream Chat Response off) does the same in one step:
error handling, a `chat:completion` with the whole answer, save with usage, `chat.finished`,
outlet filters, background tasks (`backend/open_webui/utils/middleware.py:4211-4411`).

**When a background task fails.** The tasks run one after another and only parts of each are
guarded, so the outcome depends on how the task fails:

| How the task fails | What happens | Evidence |
|---|---|---|
| Switched off (HTTP 200 "disabled" answer), the task-model call failed (logged; the endpoint answers `An internal error has occurred.`), or the answer is not valid JSON | Absorbed: no follow-ups or tags, title as in section 5.12, and the remaining tasks still run. A follow-up or tag answer that is not JSON leaves no log line | `backend/open_webui/routers/tasks.py:143-147`, `:204-211`, `:269-276`, `:334-341`; `backend/open_webui/utils/middleware.py:3915-3937`, `:3973-3979`, `:4025-4036` |
| The task endpoint **raises**: the chat's model is not in the server's model list (or, for titles, no model is recorded), a Pipelines inlet filter answered with an error, or saving the title failed | The exception leaves the handler at once; every later task (title, tags, memory review) is skipped. What follows depends on where the handler was called (next three rows) | `backend/open_webui/routers/tasks.py:157-167`, `:197-200`, `:230-235`, `:262-265`, `:295-300`, `:327-330`; `backend/open_webui/routers/pipelines.py:104-122`; `backend/open_webui/utils/middleware.py:3981`, `:3993` |
| A raising task after a **streaming** reply (the default) | The enclosing `try` handles only cancellation, so the exception reaches the per-reply task's error handler. It logs `Error processing chat payload: %s`, saves the error on the reply that has just been completed (the answer is kept beside it) and sends `chat:message:error`. The user sees a grey error box, for example `Model '' was not found` or the Pipelines filter's message, under a complete answer, and it is still there after a reload. No `chat.failed` event is published; `chat.finished` already was | `backend/open_webui/utils/middleware.py:4900`, `:6566-6573`, `:6590-6591`; `backend/open_webui/main.py:1672`, `:1686-1713`; `backend/open_webui/models/chats.py:980-984`; `src/lib/components/chat/Chat.svelte:1284-1292`; `src/lib/components/chat/Messages/ResponseMessage.svelte:857-858`, `:930-932` |
| A raising task after a **non-streaming** reply | Caught by the handler and logged at debug level only (`Error occurred while processing request: %s`). For a saved chat that is not internal, a `chat.failed` event (message `Chat failed`, with the error text and the chat link) is published although the user already has the answer and `chat.finished` was published first. Nothing changes on screen | `backend/open_webui/utils/middleware.py:4377`, `:4385-4409`; `backend/open_webui/utils/notifications.py:287-305` |
| A raising title task in the **initial title job** (new chat) | Caught by the job's own wrapper and logged as `Error generating initial chat title` with a traceback; the chat keeps the title `New Chat`; nothing appears on screen | `backend/open_webui/main.py:1486-1490` |
| Memory review | The review itself runs as a separate task; its failures are logged at debug level as `Memory review failed: %s` | `backend/open_webui/utils/memory.py:453-471` |

The answer is still sent to the model on the next turn, because only replies that hold nothing but
an error are left out of the history (`backend/open_webui/utils/middleware.py:2240-2242`). As
written, the initial title job's context has no `model` entry, which the memory-review step reads,
so `Error generating initial chat title` with `KeyError: 'model'` is expected after the title step
of every new chat the server creates from the web interface (temporary and embedded chats
excepted), including chats whose title was saved
(`backend/open_webui/main.py:1477-1484`; `backend/open_webui/utils/middleware.py:4038-4047`;
section 14). Delivery of `chat.failed` to webhooks and notification targets is described in
`notifications-webhooks-events-and-banners.md`.

### 5.8 Where Each Step Can Fail and What the User Sees

How the browser shows an error depends on **when** it happens:

- **Before the HTTP call returns** (section 5.2): the browser shows a pop-up with the error text
  and puts the same text in the reply's grey error box; if the error is not plain text the pop-up
  reads `Uh-oh! There was an issue with the response.` (`src/lib/components/chat/Chat.svelte:3643-3668`;
  `src/lib/apis/openai/index.ts:3-14`, `:421-451`).
- **Inside the task** (sections 5.3 to 5.7): the server saves the error on the assistant message
  with `done: true` and sends `chat:message:error`; the browser shows the grey error box only, no
  pop-up (`backend/open_webui/main.py:1686-1713`; `src/lib/components/chat/Chat.svelte:1284-1292`).
- **Error chunks from the provider while streaming**: the browser shows a pop-up with the
  provider's message and the error box reads `Uh-oh! There was an issue with the response.`
  followed by that message on a new line (`backend/open_webui/utils/middleware.py:5226-5249`;
  `src/lib/components/chat/Chat.svelte:2799-2801`, `:3716-3756`).
- The grey error box shows the error's text, or `Error submitting message` when the text is empty
  (`src/lib/components/chat/Messages/Error.svelte:6-37`; `src/lib/components/chat/Messages/ResponseMessage.svelte:930-931`).

| Step | Failure | What the user sees | What is saved | Evidence |
|---|---|---|---|---|
| Browser checks | No text and no file; no model; too many files | Pop-up `Please enter a prompt`, `Model not selected`, or the file-count message; nothing is sent | Nothing | `src/lib/components/chat/Chat.svelte:3134-3161` (see `chat-composer-and-message-display.md`) |
| Model resolution | Model missing from the list, base model deleted, or no access | Pop-up and error box `Model not found` | User message may not be saved (failure precedes chat bookkeeping) | `backend/open_webui/main.py:1128-1129`, `:1180-1182`, `:1640-1645`; `backend/open_webui/utils/models.py:465-521` |
| Chat bookkeeping | Not the chat owner | Pop-up and error box `Something went wrong :/` | Nothing | `backend/open_webui/main.py:1494-1499` |
| Chat bookkeeping | New chat in a folder the user cannot write to | Pop-up and error box `We could not find what you're looking for :/` | Nothing | `backend/open_webui/main.py:1353-1360` |
| Network | Server unreachable, or a proxy returned a non-JSON page | Pop-up with the browser's own network or parsing error text | Nothing on the server | `src/lib/apis/openai/index.ts:428-450` |
| Inlet or request filter | A filter raised an error | Error box with the filter's error text | Error saved, reply `done` | `backend/open_webui/utils/middleware.py:2655-2670`, `:3261-3272`; `backend/open_webui/main.py:1686-1713` |
| Pipeline inlet (external pipelines server) | Pipelines server answered with an error | Error box with the server's `detail` or HTTP reason | Error saved | `backend/open_webui/routers/pipelines.py:104-119` |
| Context compaction | Summary model failed | Pop-up `Context compaction failed`; the reply continues using the full history | A log line | `backend/open_webui/utils/context_compaction.py:98-111`; `backend/open_webui/utils/middleware.py:2512-2513`; `src/lib/components/chat/Chat.svelte:1173-1194` |
| Web search (legacy mode) | Query generation failed | Nothing visible: the user's own message is used as the search query | Nothing | `backend/open_webui/utils/middleware.py:1590-1626` |
| Web search (legacy mode) | Search failed or found nothing | Status line with the error detail, `An error occurred while searching the web`, or `No search results found`; the reply continues | Status saved | `backend/open_webui/utils/middleware.py:1701-1728` |
| Image generation (legacy mode) | Generation failed or switched off | Status `An error occurred while generating an image` or `Image generation is disabled`; the model is told to explain the problem (*corrected 2026-10-10: when switched off the step normally returns silently with no status, `backend/open_webui/utils/middleware.py:1866-1868`*) | Status saved | `backend/open_webui/utils/middleware.py:1913-1946`, `:2021-2041` |
| Files and knowledge | Retrieval raised an error | Status `No sources found`; the reply has no citations | Status saved; error only in the log | `backend/open_webui/utils/middleware.py:2105-2165`; `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:104-123` |
| MCP tool server | Could not connect | Error box `Failed to connect to MCP server '{server_id}'` while the reply continues without those tools | Not saved as the final error | `backend/open_webui/utils/middleware.py:3005-3014` |
| Terminal | Terminal tools could not be loaded | Error box `Terminal unavailable: {e}` | Error saved | `backend/open_webui/utils/middleware.py:3061-3063` |
| Provider call | Provider answered with an HTTP error (bad key, quota, content filter, unknown model) | Error box with the provider's message, or `Provider returned HTTP {status_code}` | Error saved | `backend/open_webui/main.py:1659-1665`; `backend/open_webui/utils/misc.py:43-65` |
| Provider call | Provider unreachable or timed out before answering | Error box `Open WebUI: Server Connection Error` (OpenAI-compatible) or an Ollama-specific text | Error saved | `backend/open_webui/routers/openai.py:1745-1751`; `backend/open_webui/routers/ollama.py:97-200` |
| Provider call | OpenAI-compatible or Ollama connections switched off | Error box `OpenAI API is disabled` or `The Ollama API is disabled. Please enable it to use this feature.` | Error saved | `backend/open_webui/routers/openai.py:1492-1493`; `backend/open_webui/routers/ollama.py:1107-1108` |
| Provider call | Direct connection with no live browser session | Error box with the direct-connection message, or the browser's error object as text | Error saved | `backend/open_webui/utils/chat.py:63-68`, `:126-128`; `backend/open_webui/socket/main.py:1263-1281` |
| Streaming | Provider sent an error chunk | Pop-up plus error box `Uh-oh! There was an issue with the response.` and the provider message | Error saved; text so far kept in the browser | `backend/open_webui/utils/middleware.py:5226-5249`, `:5070-5093` |
| Streaming | Connection dropped or timed out mid-reply | Error box with the error text (or `Error submitting message` if it has none); the partial text stays on screen | Error saved; **the partial text is not saved**, so it disappears on reload | `backend/open_webui/utils/middleware.py:4900`, `:6591`; `backend/open_webui/main.py:1686-1713` |
| Streaming | A stream filter failed, or a chunk could not be parsed | Nothing: the chunk is dropped, so words or the whole reply can be missing | Nothing | `backend/open_webui/utils/middleware.py:5098-5109`, `:5725-5733` |
| Tools | A tool raised an error | The tool call is shown as failed with the error text; the model decides how to continue | Saved in the output | `backend/open_webui/utils/middleware.py:6026-6027`, `:6122-6161` |
| Tools | Too many tool rounds | Error box `Tool-call limit reached ({max_tool_call_iterations} iterations).` | Error saved | `backend/open_webui/utils/middleware.py:6339-6346` |
| Tools | Follow-up model call after tools failed | Error box with the error text | Error saved | `backend/open_webui/utils/middleware.py:6328-6337` |
| Finishing | Outlet filter failed | Nothing visible; the reply is kept unfiltered | A debug log line | `backend/open_webui/utils/middleware.py:4207-4208` |
| Background tasks | Title, tag or follow-up task switched off, its model call failed, or it answered without JSON | No tags or follow-ups. The title becomes the first user message; when the title task was switched off or its call failed, only while the chat holds just its first exchange (otherwise it is unchanged, so a new side-by-side chat stays `New Chat`) | The fallback title, when it applies | `backend/open_webui/routers/tasks.py:204-211`, `:269-276`, `:334-341`; `backend/open_webui/utils/middleware.py:3887-4036` |
| Background tasks (streaming reply) | A background task raised (for example the chat's model is no longer in the model list, or a Pipelines filter rejected the task call) | The complete answer stays, with a grey error box under it showing the error text; the tasks after the failing one do not run | Error saved on the reply beside the answer; log `Error processing chat payload: %s` | `backend/open_webui/utils/middleware.py:6590-6591`; `backend/open_webui/main.py:1686-1713` (section 5.7) |
| Background tasks (non-streaming reply) | As above | Nothing visible; a `chat.failed` event (webhook or notification `Chat failed`) is published for a reply that succeeded | Nothing (a debug log line only) | `backend/open_webui/utils/middleware.py:4385-4409` (section 5.7) |
| Initial title job (new chat) | The title task raised | Title stays `New Chat` | Nothing; log `Error generating initial chat title` | `backend/open_webui/main.py:1486-1490` (section 5.7) |

The `chat.failed` event (which feeds webhooks and "chat failed" notifications) is published in one
place only: when processing a **non-streaming** reply raises an exception
(`backend/open_webui/utils/middleware.py:4388-4409`). Provider errors, streaming failures and
failures before the provider call do not publish it from this code, so a user relying on
"chat failed" notifications will not be told about most failures (section 14). Conversely, that
exception can come from a background task that raised **after** the answer was shown, saved and
announced with `chat.finished` (`backend/open_webui/utils/middleware.py:4350-4385`), so a subscriber
can receive the finished notice (headed with the chat's title) and then `Chat failed` for the same
successful reply (section 5.7). The event goes to admin webhooks (whose text reads
`Chat failed ({chat_id})`), to users' notification targets and to Event functions
(`backend/open_webui/events.py:669-675`, `:1034-1086`, `:1166-1171`;
`backend/open_webui/utils/notifications.py:264-305`); delivery is described in
`notifications-webhooks-events-and-banners.md`.

### 5.9 Stopping a Response

**What the user does.** Clicks **Stop** (or presses Escape in the composer) while a reply is
running. The button shows only while something is active and the input box is empty
(`src/lib/components/chat/MessageInput.svelte:172-176`, `:2603-2612`, `:2117-2119`).

**What the browser does** (`src/lib/components/chat/Chat.svelte:3758-3807`):

1. For a chat with an id (saved or temporary) it calls `POST /api/tasks/chat/{chat_id}/stop`;
   without a chat id it stops each known task id with `POST /api/tasks/stop/{task_id}` (an
   admin-only endpoint, so this path only works for admins).
2. Whatever the server answers, it marks every reply of that turn as done locally and moves on to
   the next queued message. A failed stop call shows a pop-up with the error text.

**What the server does.**

1. `stop_item_tasks` looks up every task id registered under the chat and stops each one
   (`backend/open_webui/tasks.py:296-309`).
2. **With Redis**, the stop is published as a command on the `{REDIS_KEY_PREFIX}:tasks:commands`
   channel; every worker's listener cancels the task if it holds it, and the Redis entries are
   cleaned up straight away (`backend/open_webui/tasks.py:259-277`, `:28-66`; listener started at
   `backend/open_webui/main.py:390-395`).
3. **Without Redis**, the task list is a dictionary in the memory of each worker process
   (`backend/open_webui/tasks.py:14-17`, `:181-196`). The stop only works when the request reaches
   the same worker that is running the reply.
4. **Cancellation inside the task**: the provider connection is closed, every unfinished item is
   marked `incomplete`, the partial reply is saved with `done: true`, and `chat:tasks:cancel` is sent
   so the browser shows the partial text as final (`backend/open_webui/utils/middleware.py:6591-6637`;
   `backend/open_webui/main.py:1673-1685`). Background tasks (follow-ups, title, tags) do not run for
   a stopped reply, because they run only after a reply completes (`:6589-6590`).
5. **"No tasks found" fallback.** For a saved chat where no task was found, the server looks for
   assistant messages still marked unfinished, marks any pending tool calls `rejected`, saves the
   messages as done and sends `chat:completion` (done) and `chat:tasks:cancel`; the answer is
   `{"status": true, "message": "Finalized pending approval message."}`
   (`backend/open_webui/main.py:2174-2214`). This is how a reply paused for tool approval is
   abandoned.

**Several workers without Redis.** If the Stop request lands on a worker that is not running the
reply, that worker finds no task, applies the fallback above (marking the message done in the
database) and tells the browser it stopped. The worker that is really generating keeps calling the
provider and, when it finishes, saves the complete reply over the "done" placeholder. The user sees
the reply stop, but the full answer can appear later after a reload, and the provider call runs to
completion (`backend/open_webui/tasks.py:181-196`, `:296-302`; `backend/open_webui/main.py:2172-2214`;
`backend/open_webui/utils/middleware.py:6552-6563`). The same per-worker blind spot affects the
"busy" indicator in the sidebar, the "Wait for the current response to finish" checks for forking
and compaction, and the reload recovery of in-progress text
(`backend/open_webui/routers/chats.py:129-139`, `:1283-1287`, `:1686-1690`, `:1338-1343`).

**What Stop does not stop.** The title generation started for a brand-new chat runs as a separate,
unregistered job (`backend/open_webui/main.py:1486-1492`), and background sub-agents are registered
under their own hidden chat id (`backend/open_webui/utils/subagents.py:665-670`); stopping the
parent chat does not cancel either. Deleting or archiving a chat stops its tasks, including those of
its internal child chats on delete (`backend/open_webui/routers/chats.py:1593-1601`, `:1920-1923`).

**Task lifetime in Redis.** Each task key expires after `REDIS_TASK_TTL` seconds (default 300,
minimum 60, 0 disables) unless the owning worker's heartbeat renews it every quarter of that time,
so tasks of a crashed worker disappear from the list after a few minutes
(`backend/open_webui/env.py:391-397`; `backend/open_webui/tasks.py:69-80`, `:107-127`).

### 5.10 Background Generation Tasks

Each task is a small, non-streaming model call built from a prompt template. All of them except
merging and emoji use the **Task Model** (section 5.11), the **Task Model Parameters**
(`task.model.params`) when set, and pass through pipeline inlet filters
(`backend/open_webui/routers/tasks.py:73-98`, `:196-202`). Function inlet filters are not applied to
task calls, because those run in `process_chat_payload`, which task calls do not use. The request
metadata carries the task name (column 2) so pipes and filters can recognize task traffic
(`backend/open_webui/routers/tasks.py:188-193`).

| Task | `task` name | When it runs | Switches (admin key, environment variable, code default; user setting) | Prompt template key (environment variable) | How to tell it ran | Evidence |
|---|---|---|---|---|---|---|
| Chat title | `title_generation` | New chat: immediately, in parallel with the first reply (first model only). Sidebar **Generate**: on demand | `task.title.enable` (`ENABLE_TITLE_GENERATION`, on); user **Title Auto-Generation** (`title.auto`, on) | `task.title.prompt_template` (`TITLE_GENERATION_PROMPT_TEMPLATE`); default asks for 2-4 words from the last two messages | Sidebar title changes from `New Chat`; `chat:title` event | `backend/open_webui/main.py:1302-1304`, `:1471-1492`; `backend/open_webui/utils/middleware.py:3939-4000`; `backend/open_webui/routers/tasks.py:141-211`; `backend/open_webui/config.py:2209-2232`, `:2299`; `src/lib/components/chat/Chat.svelte:3628-3640` |
| Chat tags | `tags_generation` | After the first reply of a new chat (first model only); also when a user rates a reply, to tag the feedback | `task.tags.enable` (`ENABLE_TAGS_GENERATION`, on); user **Chat Tags Auto-Generation** (`autoTags`, on) | `task.tags.prompt_template` (`TAGS_GENERATION_PROMPT_TEMPLATE`); default uses the last six messages | Tags appear on the chat; `chat:tags` event | `backend/open_webui/utils/middleware.py:4002-4036`; `backend/open_webui/routers/tasks.py:279-341`; `backend/open_webui/config.py:2234-2252`, `:2297`; `src/lib/components/chat/Messages/ResponseMessage.svelte:577-583` |
| Follow-up suggestions | `follow_up_generation` | After every completed reply, every model | `task.follow_up.enable` (`ENABLE_FOLLOW_UP_GENERATION`, on); user **Follow-Up Auto-Generation** (`autoFollowUps`, on) | `task.follow_up.prompt_template` (`FOLLOW_UP_GENERATION_PROMPT_TEMPLATE`); default asks for 3-5 questions | Suggested questions under the reply; saved as `followUps` | `backend/open_webui/utils/middleware.py:3889-3937`; `backend/open_webui/routers/tasks.py:214-276`; `backend/open_webui/config.py:2277-2295` |
| Web search queries | `query_generation` (type `web_search`) | Legacy mode with web search on, before the reply | `task.query.search.enable` (`ENABLE_SEARCH_QUERY_GENERATION`, on) | `task.query.prompt_template` (`QUERY_GENERATION_PROMPT_TEMPLATE`) | Status "Searching" with query chips; when off or failing, the user's message is searched as-is | `backend/open_webui/utils/middleware.py:1576-1651`; `backend/open_webui/routers/tasks.py:403-476`; `backend/open_webui/config.py:2302-2331` |
| Retrieval queries | `query_generation` (type `retrieval`) | When files or knowledge are attached and not every file is in full-context mode | `task.query.retrieval.enable` (`ENABLE_RETRIEVAL_QUERY_GENERATION`, on) | Same template | Status "Querying" with query chips; when off or failing, the user's message is used | `backend/open_webui/utils/middleware.py:2060-2103`; `backend/open_webui/config.py:2304` |
| Autocomplete | `autocomplete_generation` | While the user types, if both switches are on | `task.autocomplete.enable` (`ENABLE_AUTOCOMPLETE_GENERATION`, **off**); `task.autocomplete.input_max_length` (`AUTOCOMPLETE_GENERATION_INPUT_MAX_LENGTH`, `-1` = no limit); user **Prompt Autocompletion** (`promptAutocomplete`, off; shown only when the admin switch is on) | `task.autocomplete.prompt_template` (`AUTOCOMPLETE_GENERATION_PROMPT_TEMPLATE`) | Greyed suggestion in the composer; errors are silent | `backend/open_webui/routers/tasks.py:479-553`; `backend/open_webui/config.py:2333-2380`; `src/lib/components/chat/MessageInput.svelte:2081-2102`; `src/lib/components/common/InterfaceSettings.svelte:341` |
| Emoji | `emoji_generation` | During a voice call, per spoken reply, if the user turned on **Display Emoji in Call** | No admin switch; user `showEmojiInCall` (off) | Fixed, not configurable; answer limited to 4 tokens | Emoji shown in the call overlay; errors are silent | `backend/open_webui/routers/tasks.py:556-607`; `backend/open_webui/config.py:2439-2441`; `src/lib/components/chat/MessageInput/CallOverlay.svelte:505-516` |
| Image prompt | `image_prompt_generation` | Legacy-mode image generation when `image_generation.prompt.enable` is on | See `image-generation-and-editing.md` | `task.image.prompt_template` (`IMAGE_PROMPT_GENERATION_PROMPT_TEMPLATE`) | Falls back to the user's message on failure | `backend/open_webui/utils/middleware.py:1948-1988`; `backend/open_webui/routers/tasks.py:344-400`; `backend/open_webui/config.py:2254-2274` |
| Tool selection | `function_calling` | Legacy function-calling mode with tools selected | none | `task.tools.prompt_template` (`TOOLS_FUNCTION_CALLING_PROMPT_TEMPLATE`) | Tool result appears as a citation | `backend/open_webui/utils/middleware.py:1334-1557`; `backend/open_webui/config.py:2412-2436` |
| Merge responses | `moa_response_generation` | **Merge Responses** under side-by-side answers | none | Fixed | Merged text above the answers; uses the chat's model, not the Task Model; errors are silent | `backend/open_webui/routers/tasks.py:610-660`; `src/lib/components/chat/Chat.svelte:3901-3953` |
| Context summary | `context_compaction` (plain string, not in `TASKS`) | When compaction triggers (section 5.13) | `chat.context_compaction.enable` (off) | `chat.context_compaction.prompt_template` | Pop-ups `Compacting context` then `Context compacted` | `backend/open_webui/utils/context_compaction.py:336-395` |

Notes:

- **Voice mode prompt** is not a model call: when a voice call is active and
  `task.voice.prompt.enable` (`ENABLE_VOICE_MODE_PROMPT`, on) is set, the voice template
  (`task.voice.prompt_template`) is added to the system message
  (`backend/open_webui/utils/middleware.py:2675-2684`; `backend/open_webui/config.py:2383-2410`).
- **Template placeholders**: `{{prompt}}` (and `:start:N`, `:end:N`, `:middletruncate:N`),
  `{{MESSAGES}}` (and `:START:N`, `:END:N`, `:MIDDLETRUNCATE:N`, with an optional `|start:N`,
  `|end:N` or `|middletruncate:N` content trim), `{{TYPE}}` (autocomplete), `{{TOOLS}}` (tool
  selection), plus the date and user placeholders of section 5.17
  (`backend/open_webui/utils/task.py:108-257`, `:304-409`). An empty template means "use the
  built-in default".
- **Answers must be JSON.** Title, tags, follow-ups and queries are read from the first `{` to the
  last `}` of the model's answer; a model that answers in prose produces no tags or follow-ups and a
  fallback title (`backend/open_webui/utils/middleware.py:3911-3916`, `:3971-3979`, `:4023-4026`).
- **When a task switch is off**, title, tags and follow-up endpoints answer HTTP 200 with a
  `detail` such as `Title generation is disabled`, which the pipeline treats as "no result"; the
  query and autocomplete endpoints answer HTTP 400 (`backend/open_webui/routers/tasks.py:143-147`,
  `:216-220`, `:281-285`, `:405-417`, `:481-485`).
- **Background tasks do not cut an answer short**, because they start only after the reply is
  complete (the new-chat title runs in its own job). Most of their failures are absorbed (no
  pop-up, no error box): a switched-off task, a failed task-model call (recorded in the server log)
  and an answer that is not JSON (not logged) (`backend/open_webui/routers/tasks.py:204-211`,
  `:269-276`, `:334-341`; `backend/open_webui/utils/middleware.py:3936-3937`, `:4035-4036`). They
  are **not** all absorbed: when the chat's model is missing from the model list, or a Pipelines
  inlet filter rejects the task call, the endpoint raises, the remaining tasks are skipped, and the
  user sees a grey error box under the finished answer (streaming) or a `chat.failed` event is
  published (non-streaming); for a new chat's title only the server log records it
  (`backend/open_webui/routers/tasks.py:157-167`, `:197-200`, `:230-235`,
  `:262-265`, `:295-300`, `:327-330`; section 5.7). The tasks' debug log lines include the user's
  email address; the follow-up task's debug line wrongly says
  `generating chat title using model %s for user %s` (`backend/open_webui/routers/tasks.py:171`,
  `:239`, `:304`).
- **Temporary chats** get follow-ups but never titles or tags, and the browser only requests title
  and tags for a chat's first exchange (`backend/open_webui/utils/middleware.py:3939`;
  `src/lib/components/chat/Chat.svelte:3628-3640`).

### 5.11 Which Model Runs a Background Task (the Task Model)

`get_task_model_id` (`backend/open_webui/utils/task.py:16-27`) decides, starting from the chat's
model:

1. If the chat's model has connection type `local` (Ollama connections default to `local`; an
   OpenAI-compatible connection is `external` unless its connection settings say otherwise), use
   **Local Task Model** (`task.model.default`, environment `TASK_MODEL`) when it is set **and**
   currently in the model list.
2. Otherwise use **External Task Model** (`task.model.external`, environment `TASK_MODEL_EXTERNAL`)
   when it is set and in the model list. Models without a connection type, such as pipe functions,
   take this branch.
3. If the chosen setting is empty ("Current Model" in the drop-down) or names a model that no longer
   exists, the chat's own model is used, silently.

(`backend/open_webui/routers/ollama.py:425`; `backend/open_webui/routers/openai.py:732`;
`src/lib/components/admin/Settings/Interface.svelte:180-227`.)

Parameters: when **Task Model Parameters** are set they apply to title, tags, follow-ups, queries,
image prompt and autocomplete; otherwise the title task caps the answer at the task model's own
`max_tokens` or 1,000 tokens (`backend/open_webui/routers/tasks.py:80-98`, `:169-182`, `:202`).
Context compaction has its own model setting (section 5.13) but shares the task parameters
(`backend/open_webui/utils/context_compaction.py:348-372`).

Access: the task call is checked against the **user's** access for role `user`
(`backend/open_webui/utils/chat.py:198-203`). A task model that ordinary users cannot read makes
every background task fail for them, while admins are unaffected (section 3.4).

### 5.12 How a Chat Gets Its Title

1. A new chat is created with the title `New Chat` (`backend/open_webui/main.py:1399`).
2. If the browser asked for a title (user setting **Title Auto-Generation**, default on), title
   generation runs straight away. When the admin switch is on, the Task Model's JSON answer
   `{ "title": ... }` becomes the title; an empty or unreadable answer falls back to the text of the
   first user message (`backend/open_webui/utils/middleware.py:3940-3988`), and a JSON answer with
   no `title` field gives the user's last message, cut to 100 characters plus `...`
   (`:3941-3943`, `:3974`).
3. If no title was produced (admin switch off, user setting off, or the task-model call failed so
   the endpoint answered with its error) and the chat holds exactly the first exchange (two
   messages on the branch and no more than two in the whole chat), the title becomes the text of
   the first user message (`backend/open_webui/utils/middleware.py:3990-4000`). In a new chat with
   **several models side by side**, that last fallback condition counts every assistant
   placeholder, so the chat appears to stay `New Chat` (section 14). If the title task **raised**
   instead (the chat's model missing from the model list, no model recorded, or a Pipelines filter
   error), this step is not reached and the chat keeps `New Chat`; for a new chat the only trace is
   the server log line `Error generating initial chat title` (`backend/open_webui/main.py:1486-1490`;
   section 5.7). In the first-message fallback of this step (not the JSON path of step 2), the
   `chat:title` event carries the reply's text instead of the saved title (empty while a new
   chat's reply is still being written), because the loop at `:3857`
   reuses the variable `message` for the last message of the branch. The browser sets its own copy
   of the title from that event, so the chat header can keep showing `New Chat` and the browser tab
   only the site name until the chat is reopened or reloaded, while the sidebar shows the saved
   title (`backend/open_webui/utils/middleware.py:3857`, `:3995-3999`;
   `src/lib/components/chat/Chat.svelte:1319-1324`, `:4170-4174`;
   `src/lib/components/chat/Navbar.svelte:118-123`; section 14).
4. The title is saved and a `chat:title` event refreshes the sidebar
   (`backend/open_webui/utils/middleware.py:3981-3999`; `src/lib/components/chat/Chat.svelte:1319-1324`).
5. Later, a user can regenerate the title from the sidebar rename field with **Generate**; failures
   show a pop-up with the error, and a "disabled" answer simply leaves the old title
   (`src/lib/components/layout/Sidebar/ChatItem.svelte:495-511`; `src/lib/apis/index.ts:779-849`).

### 5.13 Context Compaction

**What it is for.** Long chats eventually exceed what a model can read. When compaction is on, the
pipeline replaces the oldest part of the conversation with a model-written summary before sending
it, so the chat can continue (`backend/open_webui/utils/context_compaction.py:42-147`).

**Automatic compaction** (each turn of a saved chat, `backend/open_webui/utils/middleware.py:2484-2513`):

1. Off unless **Context Compaction** (`chat.context_compaction.enable`, environment
   `ENABLE_CONTEXT_COMPACTION`, default off) is on (`backend/open_webui/utils/context_compaction.py:51-53`;
   `backend/open_webui/config.py:2194`).
2. If an earlier summary exists, everything before that checkpoint is already replaced by it
   (`backend/open_webui/utils/context_compaction.py:300-312`).
3. **Threshold**: the model or chat **Context Compaction Threshold** parameter
   (`compact_token_threshold`) when set, otherwise **Token Threshold**
   (`chat.context_compaction.token_threshold`, default 80,000), in both cases capped by **Token
   Cap** (`chat.context_compaction.token_cap`, defaulting to the threshold)
   (`backend/open_webui/utils/context_compaction.py:198-234`).
4. **Size estimate**: the provider-reported token usage of the most recent reply plus an estimate
   for anything after it; without usage figures, about one token per four characters and 1,000
   tokens per image (`backend/open_webui/utils/context_compaction.py:237-251`, `:315-325`, `:424-459`).
5. Nothing happens below the threshold or with three messages or fewer (`:60-61`).
6. **What is kept**: **Retained Messages** (`chat.context_compaction.retention_percentage`, default
   40, limited to 10-50) percent of the messages, at least two, cut at the start of a user turn
   (`:63-67`, `:224-229`, `:328-333`).
7. The browser shows a pop-up `Compacting context`, then `Context compacted` (or
   `Context compaction failed`) (`:75-85`, `:135-145`; `src/lib/components/chat/Chat.svelte:1173-1201`).
8. **Which model writes the summary**: **Context Compaction Model**
   (`chat.context_compaction.model`) if it is in the model list, otherwise the chat's model. If
   neither is available the step fails with `No available model for context compaction`
   (`backend/open_webui/utils/context_compaction.py:352-355`).
9. **Prompt**: **Context Compaction Prompt** (`chat.context_compaction.prompt_template`) or the
   built-in prompt, with `{{PREVIOUS_SUMMARY}}`, `{{COMPACTED_MESSAGES}}`, `{{RECENT_MESSAGES}}`,
   `{{MESSAGES}}` and `{{CURRENT_DATE}}` filled in (`:22-39`, `:357-364`;
   `src/lib/components/admin/Settings/Interface.svelte:344-363`). If the model returns nothing, a
   plain list of the first 500 characters of each dropped message (at most 4,000 characters) is used
   instead (`:387-395`).
10. The summary is saved as `contextSummary` on the first kept message (the checkpoint) and sent to
    the model as a system note starting `[CONVERSATION SUMMARY]`
    (`backend/open_webui/utils/context_compaction.py:113-123`; `backend/open_webui/utils/middleware.py:2506-2511`).
11. **If compaction fails**, the turn continues with the full history; the only trace is the pop-up
    and the log line `Context compaction failed; continuing with full chat history`
    (`backend/open_webui/utils/middleware.py:2512-2513`). A provider may then reject the over-long
    request, which shows as an ordinary provider error.

**What the user notices.** The pop-ups above; afterwards the assistant may no longer recall details
that were only in the dropped messages and not in the summary. The dropped messages remain visible
in the chat; they are only left out of what is sent to the model.

**Manual compaction (`/compact`).** Requires compaction to be on, a chat id and no reply in progress
(browser messages `Context compaction is disabled`, `No chat to compact`,
`Wait for the current response to finish before compacting.`). The server summarizes everything
except the latest message, saves the checkpoint, publishes a `chat.compacted` event and returns the
new context usage; the browser shows `Context compacted`, or `Chat is too short to compact`,
`No chat to compact`, `Context compaction is disabled` or `Nothing to compact` when nothing was done
(`src/lib/components/chat/Chat.svelte:2956-3005`; `backend/open_webui/routers/chats.py:1271-1316`;
`backend/open_webui/utils/context_compaction.py:150-195`).

**Context usage display.** `/status` shows "Context usage" as a percentage of the threshold and a
token count, using the same estimate (`backend/open_webui/utils/context_compaction.py:254-297`;
`src/lib/components/chat/MessageInput.svelte:535-548`, `:1816-1855`).

### 5.14 Sub-Agents

**What they are.** When an admin enables sub-agents, models in native function-calling mode get two
extra built-in tools: `delegate_task` (hand a focused job to a helper) and `timer` (schedule a prompt
back into the chat) (`backend/open_webui/utils/tools.py:648-654`). Each delegation creates a real,
hidden chat titled `Sub-agent: {task[:60]}` that runs the same pipeline with the same model, tools,
skills, filters, features and selected files as the parent (`backend/open_webui/utils/subagents.py:317-446`).

**Settings** (Admin Settings > Sub-agents; keys `subagents.*`):

| Label (as spelled in the code) | Key (environment variable) | Default | Effect | Evidence |
|---|---|---|---|---|
| `Enable sub-agents` | `subagents.enable` (`ENABLE_SUBAGENTS`) | off | Offers `delegate_task` and `timer` (not to sub-agents themselves, nor for direct connections) | `backend/open_webui/config.py:2036`; `backend/open_webui/utils/tools.py:648-654`; `src/lib/i18n/locales/en-US/translation.json:2634` |
| `Max concurrent` (`simultaneous sub-agents`) | `subagents.max_concurrent` (`SUBAGENTS_MAX_CONCURRENT`) | 20; `-1` no limit | Foreground sub-agents beyond this wait their turn | `backend/open_webui/config.py:2038`; `backend/open_webui/utils/subagents.py:298-303`, `:370-374`; `src/lib/i18n/locales/en-US/translation.json:2636` |
| `Enable background sub-agents` | `subagents.background_enabled` (`SUBAGENTS_BACKGROUND_ENABLED`) | off | Lets the model continue while the sub-agent works; the `background` option is hidden from the model when off | `backend/open_webui/config.py:2037`; `backend/open_webui/utils/tools.py:789-793`; `src/lib/i18n/locales/en-US/translation.json:2632-2633` |
| `Max background` (`background sub-agents`) | `subagents.max_async` (`SUBAGENTS_MAX_ASYNC`) | 20; `-1` no limit | Refuses new background sub-agents beyond this | `backend/open_webui/config.py:2039`; `backend/open_webui/utils/subagents.py:362-369`; `src/lib/i18n/locales/en-US/translation.json:2635` |
| `Max iterations` (`tool loops per sub-agent`) | `subagents.max_iterations` (`SUBAGENTS_MAX_ITERATIONS`) | 30 | Tool-call rounds per sub-agent | `backend/open_webui/config.py:2040`; `backend/open_webui/utils/subagents.py:451`; `src/lib/i18n/locales/en-US/translation.json:2637` |
| `Max output` (chars) | `subagents.max_output` (`SUBAGENTS_MAX_OUTPUT`) | 30,000 characters | Longer results are cut and end with `[output truncated]` | `backend/open_webui/config.py:2041`; `backend/open_webui/utils/subagents.py:511-512`; `src/lib/i18n/locales/en-US/translation.json:2638` |
| `System prompt` (`Leave empty for the built-in default.`) | `subagents.system_prompt` (`SUBAGENTS_SYSTEM_PROMPT`) | empty: built-in prompt | Added after the parent chat's system prompt | `backend/open_webui/config.py:2042`; `backend/open_webui/utils/subagents.py:23-32`, `:452-465`; `src/lib/i18n/locales/en-US/translation.json:2639-2640` |

The panel's description reads `Allow the AI to delegate tasks to sub-agents. Each sub-agent creates
a real chat with full tool access. Uses additional LLM calls.`
(`src/lib/components/admin/Settings/Subagents.svelte:75-79`).

**Foreground run.** The tool waits for the sub-agent's reply and returns its text (truncated to Max
output) to the parent model (`backend/open_webui/utils/subagents.py:448-518`, `:691-702`).

**Background run.** The tool returns at once with a JSON "dispatched" handle. When the sub-agent
finishes, its result is added to the parent chat as a hidden internal user message starting
`[ASYNC SUBAGENT COMPLETE - {delegation_id}]`; if the parent is idle, a new turn starts automatically
to let the model use it, and the browser reloads the chat (`backend/open_webui/utils/subagents.py:540-689`,
`:72-267`; `backend/open_webui/main.py:1774-1800`). In background mode the browser-side (Pyodide)
code interpreter and user-supplied tool servers are not passed on, because no browser session
serves the sub-agent (`backend/open_webui/utils/subagents.py:310-323`).

**Limits and safeguards.**

- Sub-agents cannot delegate further (`Error: sub-agents cannot delegate recursively.`) and lose the
  memory-changing tools (`backend/open_webui/tools/builtin.py:1703-1704`;
  `backend/open_webui/utils/tools.py:766-769`).
- Not available for direct connections (`Error: sub-agents are unavailable for direct connections.`,
  `backend/open_webui/utils/subagents.py:333-334`).
- Files must already be attached to the parent chat; unknown ids return
  `Error: file_ids not attached or unavailable: {ids}` (`backend/open_webui/utils/subagents.py:335-356`).
- The concurrency counters live in each worker's memory, and the foreground limit is fixed the
  first time a sub-agent runs in that worker: a later change to **Max concurrent** takes effect only
  after a restart (`backend/open_webui/utils/subagents.py:41-44`, `:370-374`).
- Sub-agent chats are deleted with their parent chat (`backend/open_webui/routers/chats.py:1597-1601`;
  `backend/open_webui/models/chats.py:591-600`).
- Each sub-agent makes additional calls to the same model connection; their token usage is saved on
  the sub-agent chat's messages, not on the parent's reply (section 5.18).

All sub-agent messages returned to the model are listed in section 10; most begin `Error:`.

### 5.15 Resolving a Paused Tool Call (`/resolve`)

Used when a reply paused for tool approval or for an `ask_user` question
(`backend/open_webui/main.py:1893-1910`; `backend/open_webui/utils/tool_approval.py`).

1. The browser posts `{call_id, action}` where `action` is `approve`, `reject` or `answer` (with
   `answers`, or `timed_out`) (`src/lib/apis/chats/index.ts:1372-1410`).
2. The server checks the caller owns the chat (or is an admin), finds the message and the pending
   call, and refuses calls that are already resolved (`backend/open_webui/utils/tool_approval.py:27-58`).
3. **Approve** marks the call `queued` and approved; **reject** records the result
   `Error: tool call rejected by user.` for the model; **answer** (only for `ask_user`) records the
   user's answers or a timed-out marker (`backend/open_webui/utils/tool_approval.py:60-95`).
4. The message is saved as not done and the browser is told the new state
   (`backend/open_webui/utils/tool_approval.py:97-116`).
5. A resume request is rebuilt from what was saved at the pause (model, tools, features, files,
   variables, the original session id) and fed back into `chat_completion` as a "continue" of the
   same assistant message (`backend/open_webui/utils/tool_approval.py:131-186`). The approval mode is
   taken from the chat's current setting, defaulting to "ask".
6. Inside the pipeline, approved calls are executed first; if more calls still need approval the
   reply pauses again, otherwise the model is called with the results
   (`backend/open_webui/utils/middleware.py:3412-3610`; `backend/open_webui/main.py:1654-1655`).
7. Errors appear as pop-ups with the server's text, for example
   `Tool call has already been resolved.` (`src/lib/components/chat/Chat.svelte:489-498`, `:564-592`;
   `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte:120-140`).

To abandon a paused reply, the user presses Stop; the server rejects the pending calls and closes
the message (section 5.9, "No tasks found" fallback).

### 5.16 Forking a Chat

1. The user types `/fork` or clicks **Fork chat** under a finished reply. The browser refuses while
   a reply is running (`Wait for the current response to finish before forking.`), without a chat
   (`No chat to fork`) or without the `chat.import` permission (`Access prohibited`); otherwise it
   shows `Forking chat...` (`src/lib/components/chat/Chat.svelte:3046-3089`).
2. The server re-checks the permission, ownership and that no task is running (HTTP 409 with the
   same "wait" text) (`backend/open_webui/routers/chats.py:1681-1690`).
3. It copies only the branch from the first message down to the chosen message (default: the
   message being viewed), renumbering nothing but cutting off other branches
   (`backend/open_webui/utils/chat_fork.py:4-41`).
4. Unfinished assistant messages in the copy are marked done, except those awaiting tool approval
   (`backend/open_webui/routers/chats.py:1710-1724`).
5. The new chat is titled `{original title} (fork)`, keeps the folder when the user can still write
   to it, copies chat variables and the pinned state, records `forked_from` and
   `forked_from_message_id` in its metadata, and publishes a `chat.cloned` event
   (`backend/open_webui/routers/chats.py:1726-1772`).
6. The browser opens the new chat and shows `Chat forked`; failures show `Failed to fork chat` or
   the server's text (`src/lib/components/chat/Chat.svelte:3066-3085`).

Server-side refusals: `chat has no messages to fork`, `message branch contains a cycle`,
`message not found` (HTTP 404) (`backend/open_webui/utils/chat_fork.py:5-19`;
`backend/open_webui/routers/chats.py:1696-1708`).

### 5.17 Prompt, Chat and User Variables

Three kinds of placeholders are filled in before text reaches a model:

1. **Browser-supplied prompt variables** sent with each turn: `{{USER_NAME}}`, `{{USER_EMAIL}}`,
   `{{USER_LOCATION}}` (only when the user enabled location sharing), `{{CURRENT_DATETIME}}`,
   `{{CURRENT_DATE}}`, `{{CURRENT_TIME}}`, `{{CURRENT_WEEKDAY}}`, `{{CURRENT_TIMEZONE}}`,
   `{{USER_LANGUAGE}}` (`src/lib/utils/index.ts:1219-1231`; `src/lib/components/chat/Chat.svelte:3607-3613`).
   They replace matching text in system prompts (`backend/open_webui/utils/payload.py:34-38`;
   `backend/open_webui/utils/task.py:30-33`).
2. **Server-side user placeholders** in system prompts and task templates: `{{USER_NAME}}`,
   `{{USER_EMAIL}}`, `{{USER_BIO}}`, `{{USER_GENDER}}`, `{{USER_BIRTH_DATE}}`, `{{USER_AGE}}`,
   `{{USER_LOCATION}}`, `{{USER_GROUPS}}` and the date and time placeholders, using the server's
   clock (`backend/open_webui/utils/task.py:36-105`). Unknown values become `Unknown`.
3. **Chat and user variables**: `{{chat.variables.<key>}}` placeholders (optionally with a type,
   label, options and default) in a model's system prompt make the browser ask for values per chat;
   `{{user.variables.<key>}}` placeholders use values the user saved in their settings
   (`backend/open_webui/utils/chat_variables.py:8-12`, `:127-168`, `:254-288`). Keys must start with
   a lower-case letter and use only lower-case letters, digits and underscores; values are limited to
   20,000 characters and 100,000 characters in total.

Behaviour to know:

- The browser blocks sending when chat-variable definitions conflict across the selected models
  (`Chat Variables have conflicting model definitions`) and opens the Chat Variables dialog when a
  required value is missing (`src/lib/components/chat/Chat.svelte:3142-3150`).
- On the server, chat variables are rendered leniently: if any value is invalid (for example a value
  not among a select field's options, or too long), **every** chat variable in that prompt renders as
  empty, with no message (`backend/open_webui/utils/chat_variables.py:254-273`;
  `backend/open_webui/utils/payload.py:25-30`).
- Validation messages such as `User variable is too long: {key}` are shown only when a user saves
  their user variables (HTTP 400 from `POST /api/v1/users/user/variables/update`,
  `backend/open_webui/routers/users.py:650-662`).
- **Personal data.** When a system prompt or task template uses them, these placeholders put the
  user's name, email address and, if filled in, biography, gender, birth date, age, location and
  group names into the text sent to the model provider. Whether the production provider
  arrangements cover this is TO BE CONFIRMED.

### 5.18 Token and Usage Reporting

- **Asking for usage.** For streaming replies the server adds `stream_options.include_usage` only
  when the model's **usage** capability is on; many OpenAI-compatible providers report no token
  counts otherwise (`backend/open_webui/main.py:1196-1198`).
- **Normalizing.** Whatever the provider sends (OpenAI `prompt_tokens`/`completion_tokens`, Ollama
  `prompt_eval_count`/`eval_count`, llama.cpp `prompt_n`/`predicted_n`, plus any cost fields) is
  kept and three standard fields are added: `input_tokens`, `output_tokens`, `total_tokens`
  (`backend/open_webui/utils/response.py:13-47`). Ollama replies also get `response_token/s`,
  `prompt_token/s` and an `approximate_total` duration (`backend/open_webui/utils/response.py:163-207`).
- **Adding up.** When a reply involves several model calls (tool rounds, code interpreter rounds),
  token and cost fields are summed across calls (`backend/open_webui/utils/response.py:100-143`;
  `backend/open_webui/utils/middleware.py:5186-5224`).
- **Where it goes.** Usage is sent live in `chat:completion` events and saved on the assistant
  message as `usage` (`backend/open_webui/utils/middleware.py:4363-4375`, `:6545-6563`). Under a
  reply with usage, an information (i) button shows the figures on hover
  (`src/lib/components/chat/Messages/ResponseMessage.svelte:1234-1275`). The latest reply's usage
  also feeds the compaction threshold and the `/status` context figure (section 5.13).
- **Not counted here**: background tasks (title, tags, follow-ups, queries, autocomplete, emoji,
  compaction summaries) do not save their usage anywhere in this code (section 14). Analytics
  dashboards are described in `evaluations-feedback-and-analytics.md`.

### 5.19 API and Integration Callers

- **No session id** (scripts, the OpenAI-compatible alias): the turn runs synchronously and the
  provider's answer (stream or JSON) is returned in the HTTP response; title, tags and follow-ups do
  not run unless the caller sends `background_tasks`; built-in tools are not injected
  (`backend/open_webui/main.py:1882-1885`; `backend/open_webui/utils/middleware.py:2809-2813`,
  `:3096-3099`). Errors come back as HTTP 400 with the error text in `detail`
  (`backend/open_webui/main.py:1714-1722`).
- **Explicit `tools`** in the request body are passed through untouched; `tools: []` turns off all
  server-side tool resolution (`backend/open_webui/utils/middleware.py:2945-2948`).
- **Anthropic Messages format** (`/api/v1/messages`) is converted to the OpenAI format, run through
  this pipeline, and converted back; some connections pass it straight through instead
  (`backend/open_webui/main.py:2002-2068`, `:1943-1999`).
- **`/api/chat/completed`** is kept only for older integrations; outlet filters now run inline
  (`backend/open_webui/main.py:2090-2107`; `backend/open_webui/utils/chat.py:311-374`).
- **`/api/chat/actions/{action_id}`** runs an Action function; it refuses when plugins are disabled,
  the action is unknown, inactive or not attached to the model, or the model is unknown
  (`backend/open_webui/utils/actions.py:19-64`). Actions are documented in
  `functions-pipes-filters-actions-and-pipelines.md`.

## 6. Data Model

The pipeline does not own a table of its own; it writes into the chat tables and keeps running
state in memory or Redis. Values in the database are user data and are not reproduced here.

### 6.1 Tables Written by the Pipeline

| Table | What the pipeline writes | Evidence |
|---|---|---|
| `chat` | New chat row (`title` `New Chat`, `chat` JSON with `history.messages` and `history.currentId`, `models`, `files`, `folder_id`, `variables`); later the title, tags (in `meta`), the message tree and `updated_at` | `backend/open_webui/main.py:1393-1417`, `:1509-1518`; `backend/open_webui/models/chats.py:132-153` |
| `chat_message` | One row per message, dual-written whenever a message in the chat JSON is upserted: `role`, `parent_id`, `content`, `output`, `model_id`, `files`, `sources`, `embeds`, `meta`, `done`, `status_history`, `error`, `usage`, `context_summary`, timestamps | `backend/open_webui/models/chat_messages.py:127-165`; `backend/open_webui/models/chats.py:1141-1190` |
| `chat_file` | Links between the chat, the user message and uploaded files | `backend/open_webui/main.py:1453-1469`, `:1561-1577` |
| `tag` | Missing tag rows created by tag generation; the chat's tag list (`chat.meta.tags`, lower-case with underscores, `none` dropped) is **replaced** by the generated tags | `backend/open_webui/utils/middleware.py:4027`; `backend/open_webui/models/chats.py:865-890` |
| `config` | Task, compaction, tool-permission and sub-agent settings (section 7) | `backend/open_webui/routers/tasks.py:135-138`; `backend/open_webui/routers/chats.py:841-856`; `backend/open_webui/routers/configs.py:788-800` |

A failed write to `chat_message` is logged (`Failed to write to chat_message table: {e}`) and does
not stop the turn (`backend/open_webui/models/chats.py:1181-1190`).

### 6.2 Fields on a Message (in the Chat JSON)

| Field | Meaning | Written by |
|---|---|---|
| `id`, `parentId`, `childrenIds` | Position in the message tree | `backend/open_webui/main.py:1373-1391`, `:1549-1595` |
| `role`, `model`, `modelIdx`, `timestamp` | Author, model id, side-by-side column, creation time (seconds) | Same |
| `content` | Plain text (user messages; legacy or summary text for assistant replies) | `backend/open_webui/main.py:1521-1526` |
| `output` | Structured reply items (text, reasoning, tool calls and results, code interpreter) | `backend/open_webui/utils/middleware.py:6552-6563` |
| `done` | `false` while running or paused, `true` when finished, stopped or failed | `backend/open_webui/main.py:1383`, `:1699`; `backend/open_webui/utils/middleware.py:6559` |
| `error` | `{content: ...}` shown in the grey error box | `backend/open_webui/main.py:1693-1701`; `backend/open_webui/utils/middleware.py:4855-4867` |
| `statusHistory` | Every status line, in order | `backend/open_webui/socket/main.py:1166-1171`; `backend/open_webui/models/chats.py:1239-1264` |
| `sources` | Citations (retrieval, web search, tools, URL annotations) | `backend/open_webui/utils/middleware.py:4901-4917`; `backend/open_webui/socket/main.py:1235-1250` |
| `files`, `embeds` | Images and files produced during the reply; embedded tool UI | `backend/open_webui/socket/main.py:1202-1233` |
| `usage` | Normalized token usage (section 5.18) | `backend/open_webui/utils/middleware.py:4363-4375`, `:6561` |
| `followUps` | Suggested follow-up questions | `backend/open_webui/utils/middleware.py:3926-3934` |
| `selectedModelId` | Model picked by an arena model | `backend/open_webui/utils/middleware.py:4257-4265`, `:5115-5125` |
| `contextSummary` | Compaction checkpoint summary | `backend/open_webui/utils/context_compaction.py:113-123` |
| `originalContent` | Text before an outlet filter changed it | `backend/open_webui/utils/middleware.py:4187-4198` |
| `meta` | On a paused reply: what is needed to resume (session id, tools, files, features, params). On internal messages: `internal`, `type` (`subagent`, `timer`), `status`, delegation ids | `backend/open_webui/utils/middleware.py:3634-3655`; `backend/open_webui/utils/subagents.py:583-599` |

### 6.3 Chat Metadata Used Here

- **Sub-agent chats**: `meta` holds `internal: true`, `type: subagent`, `parent_chat_id`,
  `parent_message_id`, `delegation_id`, `mode` (`foreground` or `background`)
  (`backend/open_webui/utils/subagents.py:428-435`).
- **Forked chats**: `meta.forked_from`, `meta.forked_from_message_id`; the chat JSON holds
  `originalChatId` and `branchPointMessageId` (`backend/open_webui/routers/chats.py:1726-1741`).

### 6.4 Running State (Not in the Database)

| Store | Without Redis | With Redis (`REDIS_URL`) | Evidence |
|---|---|---|---|
| Running tasks | Dictionaries `tasks` and `item_tasks` in each worker's memory | Key `{prefix}:tasks:{task_id}` (expiring), hash `{prefix}:tasks`, set `{prefix}:tasks:item:{chat_id}` | `backend/open_webui/tasks.py:14-23`, `:88-104` |
| Stop commands | Not shared | Pub/sub channel `{prefix}:tasks:commands` | `backend/open_webui/tasks.py:23`, `:130-137` |
| In-progress reply text | Dictionary `response_streams` in the worker's memory | Hash `{prefix}:tasks:response_streams`, per-entry expiry `REDIS_RESPONSE_STREAM_TTL` (default 3,600 seconds) | `backend/open_webui/tasks.py:17`, `:22`, `:199-223`; `backend/open_webui/env.py:386-389` |
| Sub-agent counters | Each worker's memory (also with Redis) | Same | `backend/open_webui/utils/subagents.py:41-44` |

`{prefix}` is `REDIS_KEY_PREFIX`, default `open-webui` (`backend/open_webui/env.py:384`). The
in-progress reply text held there is the user's conversation content.

## 7. Settings and Configuration

Code defaults are what the repository says. **Live values are data in the `config` table (or the
environment) and are TO BE CONFIRMED for production.** After first boot the stored value wins over
the environment variable (ground truth, Settings).

### 7.1 Admin Settings > Interface: Tasks

| Label | Key | Environment variable | Code default | Effect | Evidence |
|---|---|---|---|---|---|
| `Local Task Model` | `task.model.default` | `TASK_MODEL` | empty ("Current Model") | Task model for chats on `local` connections | `backend/open_webui/config.py:2180`, `:3129`; `src/lib/components/admin/Settings/Interface.svelte:188-205`; `src/lib/i18n/locales/en-US/translation.json:2504` |
| `External Task Model` | `task.model.external` | `TASK_MODEL_EXTERNAL` | empty | Task model for every other chat | `backend/open_webui/config.py:2182`, `:3130`; `src/lib/components/admin/Settings/Interface.svelte:207-226`; `src/lib/i18n/locales/en-US/translation.json:2497` |
| `Task Model Parameters` | `task.model.params` | `TASK_MODEL_PARAMS` (JSON) | `{}` | Parameters for task calls (empty values removed) | `backend/open_webui/config.py:2184-2190`, `:3131`; `src/lib/components/admin/Settings/Interface.svelte:229-254` |

The section description reads `Choose fallback models for background tasks. Current Model follows the
active chat model.` (`src/lib/i18n/locales/en-US/translation.json:2520`).

### 7.2 Admin Settings > Interface: Chat

| Label | Key | Environment variable | Code default | Effect | Evidence |
|---|---|---|---|---|---|
| `Tool Permissions` (experimental) | `chat.tool_permissions.enable` | `ENABLE_TOOL_PERMISSIONS` | off | Shows "Full access" and "Ask for approval" in the chat input menu; "ask" pauses before tools run | `backend/open_webui/config.py:2196`, `:3138`; `backend/open_webui/main.py:1254-1264`; `src/lib/i18n/locales/en-US/translation.json:2532-2533` |
| `Context Compaction` | `chat.context_compaction.enable` | `ENABLE_CONTEXT_COMPACTION` | off | Automatic and manual compaction | `backend/open_webui/config.py:2194`, `:3133`; `src/lib/i18n/locales/en-US/translation.json:2491-2492` |
| `Context Compaction Model` | `chat.context_compaction.model` | `CONTEXT_COMPACTION_MODEL` | empty (chat model) | Summary model | `backend/open_webui/config.py:2192`, `:3132`; `src/lib/i18n/locales/en-US/translation.json:2493-2494` |
| `Token Threshold` | `chat.context_compaction.token_threshold` | `CONTEXT_COMPACTION_TOKEN_THRESHOLD` | 80000 | Size that triggers compaction | `backend/open_webui/config.py:2198`; `src/lib/i18n/locales/en-US/translation.json:2530-2531` |
| `Token Cap` | `chat.context_compaction.token_cap` | `CONTEXT_COMPACTION_TOKEN_CAP` | unset (equals the threshold) | Upper limit for model-specific thresholds | `backend/open_webui/config.py:2200-2201`; `backend/open_webui/routers/chats.py:218-221`; `src/lib/i18n/locales/en-US/translation.json:2528-2529` |
| `Retained Messages` | `chat.context_compaction.retention_percentage` | `CONTEXT_COMPACTION_RETENTION_PERCENTAGE` | 40 (forced into 10-50) | Share of recent messages kept | `backend/open_webui/config.py:2203-2205`; `backend/open_webui/routers/chats.py:845`; `src/lib/i18n/locales/en-US/translation.json:2509-2510` |
| `Context Compaction Prompt` | `chat.context_compaction.prompt_template` | `CONTEXT_COMPACTION_PROMPT_TEMPLATE` | empty (built-in) | Summary prompt | `backend/open_webui/config.py:2207`; `src/lib/i18n/locales/en-US/translation.json:2495-2496` |

### 7.3 Admin Settings > Interface: Generation

| Label | Key | Environment variable | Code default | Evidence |
|---|---|---|---|---|
| `Title Generation` / `Title Generation Prompt` | `task.title.enable` / `task.title.prompt_template` | `ENABLE_TITLE_GENERATION` / `TITLE_GENERATION_PROMPT_TEMPLATE` | on / empty | `backend/open_webui/config.py:2299`, `:2209`; `src/lib/i18n/locales/en-US/translation.json:2524-2527` |
| `Voice Mode Prompt` / `Prompt Template` | `task.voice.prompt.enable` / `task.voice.prompt_template` | `ENABLE_VOICE_MODE_PROMPT` / `VOICE_MODE_PROMPT_TEMPLATE` | on / empty | `backend/open_webui/config.py:2385`, `:2383`; `src/lib/i18n/locales/en-US/translation.json:2505-2506`, `:2536-2537` |
| `Follow Up Generation` / `Follow Up Generation Prompt` | `task.follow_up.enable` / `task.follow_up.prompt_template` | `ENABLE_FOLLOW_UP_GENERATION` / `FOLLOW_UP_GENERATION_PROMPT_TEMPLATE` | on / empty | `backend/open_webui/config.py:2295`, `:2277`; `src/lib/i18n/locales/en-US/translation.json:2498-2501` |
| `Tags Generation` / `Tags Generation Prompt` | `task.tags.enable` / `task.tags.prompt_template` | `ENABLE_TAGS_GENERATION` / `TAGS_GENERATION_PROMPT_TEMPLATE` | on / empty | `backend/open_webui/config.py:2297`, `:2234`; `src/lib/i18n/locales/en-US/translation.json:2516-2519` |
| `Retrieval Query Generation` | `task.query.retrieval.enable` | `ENABLE_RETRIEVAL_QUERY_GENERATION` | on | `backend/open_webui/config.py:2304`; `src/lib/i18n/locales/en-US/translation.json:2511-2512` |
| `Web Search Query Generation` | `task.query.search.enable` | `ENABLE_SEARCH_QUERY_GENERATION` | on | `backend/open_webui/config.py:2302`; `src/lib/i18n/locales/en-US/translation.json:2538-2539` |
| `Query Generation Prompt` (shared by both) | `task.query.prompt_template` | `QUERY_GENERATION_PROMPT_TEMPLATE` | empty | `backend/open_webui/config.py:2307`; `src/lib/i18n/locales/en-US/translation.json:2507-2508` |
| `Autocomplete Generation` / `Autocomplete Generation Input Max Length` / `Autocomplete Generation Prompt` | `task.autocomplete.enable` / `task.autocomplete.input_max_length` / `task.autocomplete.prompt_template` | `ENABLE_AUTOCOMPLETE_GENERATION` / `AUTOCOMPLETE_GENERATION_INPUT_MAX_LENGTH` / `AUTOCOMPLETE_GENERATION_PROMPT_TEMPLATE` | off / -1 / empty | `backend/open_webui/config.py:2333-2337`; `src/lib/i18n/locales/en-US/translation.json:2484-2489` |
| `Image Prompt Generation Prompt` | `task.image.prompt_template` | `IMAGE_PROMPT_GENERATION_PROMPT_TEMPLATE` | empty | `backend/open_webui/config.py:2254`; `src/lib/i18n/locales/en-US/translation.json:2502-2503` |
| `Tools Function Calling Prompt` | `task.tools.prompt_template` | `TOOLS_FUNCTION_CALLING_PROMPT_TEMPLATE` | empty | `backend/open_webui/config.py:2412`; `src/lib/i18n/locales/en-US/translation.json:2534-2535` |

Every prompt field shows the placeholder `Leave empty to use the default prompt, or enter a custom
prompt` (`src/lib/components/admin/Settings/Interface.svelte:384-386`). The emoji prompt and the
merge-responses prompt are fixed in code and have no setting (`backend/open_webui/routers/tasks.py:577`, `:628`).

**Saving this panel.** The Save button sends the task and chat settings without waiting for the
answer and the Settings dialog immediately shows `Settings saved successfully!`; a failed save
produces no error message (`src/lib/components/admin/Settings/Interface.svelte:64-86`, `:164-170`;
`src/lib/components/chat/SettingsModal.svelte:880-884`). After saving, reopen the panel to confirm
the values stuck. Loading failures show the server's text or `Failed to load Interface settings`
(`src/lib/components/admin/Settings/Interface.svelte:150-155`).

### 7.4 Admin Settings > Sub-agents

The seven `subagents.*` keys and their defaults are listed in section 5.14. The panel saves with
`POST /api/v1/configs/subagents` and shows `Settings saved successfully!` only after the server
accepts; errors show a pop-up with the error (`src/lib/components/admin/Settings/Subagents.svelte:38-56`).
Saving publishes a `config.updated` event (`backend/open_webui/routers/configs.py:788-800`).

### 7.5 Model and Chat Parameters That Steer the Pipeline

Set per model (Workspace > Models, advanced parameters), per chat (chat controls) or per user
(Settings > General); these never reach the provider (`backend/open_webui/utils/payload.py:90-103`).

| Parameter label | Key | Values | Effect | Evidence |
|---|---|---|---|---|
| `Stream Chat Response` | `stream_response` | Default, On, Off | Streams the reply or returns it in one piece; a model-level value overrides the user's | `backend/open_webui/main.py:1193-1194`; `src/lib/components/chat/Settings/Advanced/AdvancedParams.svelte:115-140` |
| `Stream Delta Chunk Size` | `stream_delta_chunk_size` | number | Batches streamed pieces | `backend/open_webui/utils/middleware.py:4928-4931` |
| `Function Calling` | `function_calling` | Default (native), Native, Legacy | Section 4; label text in `settings.personal.general.parameters.functionCalling.description` | `backend/open_webui/main.py:1290-1294`; `src/lib/components/chat/Settings/Advanced/AdvancedParams.svelte:239-270`; `src/lib/i18n/locales/en-US/translation.json:2825-2826` |
| `Reasoning Tags` | `reasoning_tags` | Enabled, Disabled, Custom start and end tags | Separates "thinking" text from the answer | `backend/open_webui/utils/middleware.py:4869-4898`; `src/lib/i18n/locales/en-US/translation.json:2844-2845` |
| `Context Compaction Threshold` | `compact_token_threshold` | Default, Custom (80000 when first set) | Model-specific compaction threshold, capped by Token Cap | `backend/open_webui/utils/context_compaction.py:232-234`; `src/lib/components/chat/Settings/Advanced/AdvancedParams.svelte:195-215`; `src/lib/i18n/locales/en-US/translation.json:2821-2822` |
| System prompt | `system` | text | The model's system prompt | `backend/open_webui/utils/middleware.py:2429-2430`, `:3221-3230` |
| Tool approval mode | `tool_approval_mode` | `full`, `ask` | Only honoured when Tool Permissions is on | `backend/open_webui/main.py:1254-1264` |

Global defaults for all models come from `models.default_params` and are overlaid by each model's
own parameters (`backend/open_webui/main.py:1169-1177`).

### 7.6 Model Capabilities Read by the Pipeline

| Capability (model settings) | Default | Effect when off | Evidence |
|---|---|---|---|
| usage | off unless set | No usage requested from streaming providers | `backend/open_webui/main.py:1196-1198` |
| builtin tools | on | No built-in tools in native mode | `backend/open_webui/utils/middleware.py:2809-2813` |
| file context | on | Attached files are not retrieved into the prompt (the model gets file tools instead) | `backend/open_webui/utils/middleware.py:3206-3214`; `backend/open_webui/utils/tools.py:594-601` |
| citations | on | Tool results are not shown as citations | `backend/open_webui/utils/middleware.py:5840-5843` |
| terminal | on | Terminal tools not loaded | `backend/open_webui/utils/middleware.py:3036-3040` |
| code interpreter | on | No legacy code-interpreter detection | `backend/open_webui/utils/middleware.py:4882` |
| status updates | on | Status lines are not displayed for that model | `src/lib/components/chat/Messages/ResponseMessage.svelte:198-199` |

Per-category built-in tool switches (`builtinTools`, for example `knowledge`, `code_interpreter`,
`subagents`) are described in `builtin-native-tools.md`.

### 7.7 Personal Settings That Affect Background Tasks

| Label | Setting | Default | Evidence |
|---|---|---|---|
| `Title Auto-Generation` | `title.auto` | on | `src/lib/components/common/InterfaceSettings.svelte:319`; `src/lib/i18n/locales/en-US/translation.json:2987` |
| `Chat Tags Auto-Generation` | `autoTags` | on | `src/lib/components/common/InterfaceSettings.svelte:320`; `src/lib/i18n/locales/en-US/translation.json:2893` |
| `Follow-Up Auto-Generation` | `autoFollowUps` | on | `src/lib/components/common/InterfaceSettings.svelte:321`; `src/lib/i18n/locales/en-US/translation.json:2919` |
| `Prompt Autocompletion` (shown only when the admin switch is on) | `promptAutocomplete` | off | `src/lib/components/common/InterfaceSettings.svelte:341`, `:1636`; `src/lib/i18n/locales/en-US/translation.json:2952` |
| `Display Emoji in Call` | `showEmojiInCall` | off | `src/lib/components/common/InterfaceSettings.svelte:332`; `src/lib/i18n/locales/en-US/translation.json:2906` |

These are stored with the user's settings and sent by the browser with each turn
(`src/lib/components/chat/Chat.svelte:3628-3640`); see `user-settings-and-personalisation.md`.

### 7.8 Environment-Only Settings (Not Editable in the Interface)

| Variable | Code default | Effect | Evidence |
|---|---|---|---|
| `ENABLE_CUSTOM_MODEL_FALLBACK` | off | Custom model with a missing base model falls back to the first default model | `backend/open_webui/env.py:1033`; `backend/open_webui/main.py:1137-1147` |
| `BYPASS_MODEL_ACCESS_CONTROL` | off | Skips model access checks for everyone | `backend/open_webui/env.py:832`; `backend/open_webui/main.py:1150` |
| `CHAT_RESPONSE_MAX_TOOL_CALL_ITERATIONS` (older name `CHAT_RESPONSE_MAX_TOOL_CALL_RETRIES`) | 256; `-1` unlimited | Tool rounds per reply | `backend/open_webui/env.py:1082-1098` |
| `CHAT_RESPONSE_STREAM_DELTA_CHUNK_SIZE` | 1 | Minimum batch of streamed pieces | `backend/open_webui/env.py:1070-1078` |
| `CHAT_STREAM_RESPONSE_CHUNK_MAX_BUFFER_SIZE` | unset (no limit) | Drops stream lines longer than this many bytes | `backend/open_webui/env.py:1108-1116`; `backend/open_webui/utils/misc.py:1272-1318` |
| `ENABLE_API_OUTLET_FILTERS` | on | Outlet filters for API callers | `backend/open_webui/env.py:1052` |
| `ENABLE_CHAT_RESPONSE_BASE64_IMAGE_URL_CONVERSION` | off | Stores inline images in replies as files | `backend/open_webui/env.py:1049-1051`; `backend/open_webui/utils/middleware.py:5567-5576` |
| `ENABLE_CHAT_RESPONSE_STREAM_INPLACE_APPEND` | off | Memory optimization for long streams | `backend/open_webui/env.py:1054-1059` |
| `ENABLE_RESPONSES_API_STATEFUL` | off (experimental) | Sends only new items with `previous_response_id` to Responses API endpoints | `backend/open_webui/env.py:1101-1105`; `backend/open_webui/utils/middleware.py:6235-6242` |
| `ENABLE_QUERIES_CACHE` | off | Reuses the web-search queries for retrieval in the same turn | `backend/open_webui/env.py:370`; `backend/open_webui/utils/middleware.py:1617-1618`; `backend/open_webui/routers/tasks.py:419-421` |
| `RAG_SYSTEM_CONTEXT` | off | Puts retrieved sources in the system message instead of the user message | `backend/open_webui/env.py:372`; `backend/open_webui/utils/middleware.py:996-1007` |
| `ENABLE_REALTIME_CHAT_SAVE` | off | Imported by the pipeline but not used anywhere in `backend/open_webui` in this version | `backend/open_webui/env.py:369`; `backend/open_webui/utils/middleware.py:42` |
| `ENABLE_PLUGINS` | on | When off: no filters, workspace tools or actions | `backend/open_webui/env.py:1186`; `backend/open_webui/utils/middleware.py:2655-2670`, `:3015-3016`; `backend/open_webui/utils/actions.py:20-21` |
| `REDIS_URL` | unset | Shared task registry, stop commands, in-progress text | `backend/open_webui/env.py:381`; `backend/open_webui/main.py:390-395` |
| `REDIS_TASK_TTL` | 300 (values under 60 become 300; 0 disables) | Expiry of task keys without heartbeat | `backend/open_webui/env.py:391-397` |
| `REDIS_RESPONSE_STREAM_TTL` | 3600 | Expiry of saved in-progress text | `backend/open_webui/env.py:386-389` |
| `WEBSOCKET_MANAGER` | unset | `redis` lets any worker deliver events to any browser | `backend/open_webui/env.py:476`; `backend/open_webui/socket/main.py:1151` |
| `WEBSOCKET_EVENT_CALLER_TIMEOUT` | unset (no limit) | How long the server waits for the browser (direct tools, direct connections, browser Python) | `backend/open_webui/env.py:534-542`; `backend/open_webui/socket/main.py:1268-1281` |
| `AIOHTTP_CLIENT_TIMEOUT` / `AIOHTTP_CLIENT_STREAM_IDLE_TIMEOUT` | unset (no total limit) / unset | Provider request limits; a limit can cut long replies | `backend/open_webui/env.py:608-625`; `backend/open_webui/utils/session_pool.py:43-51` |

### 7.9 Other Settings Read Here (Documented Elsewhere)

`ui.default_models` (fallback model), `models.default_params`, `rag.template`, `rag.top_k` and the
other retrieval keys (`backend/open_webui/utils/middleware.py:2107-2114`), `web.search.enable`,
`memories.*`, `image_generation.*`, `images.edit.enable`, `code_interpreter.*`,
`tool_server.connections`, `terminal_server.connections`, `user.permissions`, `webui.url` (used to
build chat links in `chat.finished` events, `backend/open_webui/utils/middleware.py:214-227`).

## 8. Cron Jobs and Background Processes

There is no crontab. Everything below is an in-process asyncio task inside the web server.

| Process | Started | Runs | What it does | Evidence |
|---|---|---|---|---|
| Per-reply task | Each chat turn, one per selected model | Until the reply finishes, fails or is stopped | Builds the prompt, calls the provider, streams, runs tools, saves, runs outlet filters and background tasks | `backend/open_webui/main.py:1802-1857`; `backend/open_webui/tasks.py:157-178` |
| Task clean-up | When a per-reply task ends (done callback) | Once | Removes the task id from the registry and the in-progress text store | `backend/open_webui/tasks.py:140-154`, `:164-165` |
| Initial title job | Each new chat whose browser asked for a title | Once, in parallel with the first reply; not registered as a task | Title generation (section 5.12); any exception is logged as `Error generating initial chat title` (section 5.7) | `backend/open_webui/main.py:1471-1492` |
| Background generation tasks | After each completed reply, inside the per-reply task | Once per reply | Follow-ups, title (when not handed to the initial title job) and tags, memory review, one after another; a task that raises skips the rest (section 5.7) | `backend/open_webui/utils/middleware.py:3832-4047`, `:6589-6590` |
| Memory review | After a reply, every N user turns when enabled | Separate asyncio task | Reviews the conversation for memories (see `memories.md`) | `backend/open_webui/utils/memory.py:410-460` |
| Redis task command listener | Server start, only when Redis is configured | Continuously; reconnects with back-off from 1 to 30 seconds | Receives stop commands and cancels local tasks | `backend/open_webui/main.py:390-393`; `backend/open_webui/tasks.py:24-66` |
| Redis task heartbeat | Server start, when Redis is configured and `REDIS_TASK_TTL` is above 0 | Every `REDIS_TASK_TTL / 4` seconds (75 by default) | Renews the expiry of this worker's running tasks | `backend/open_webui/main.py:394-395`; `backend/open_webui/tasks.py:69-80` |
| Background sub-agent | When the model delegates with `background` | Until the sub-agent finishes | Runs the hidden sub-agent chat, then posts the result back and may start a new parent turn | `backend/open_webui/utils/subagents.py:540-689` |
| Pending internal messages | After a per-reply task ends with no other task running for the chat | Once; waits (polling every 0.25 seconds) until the chat is idle | Turns finished background sub-agent results and fired timers into the next turn | `backend/open_webui/main.py:1774-1800`; `backend/open_webui/utils/subagents.py:72-267` |

Things that happen **at save time**, not in the background: task, compaction and sub-agent settings
take effect on the next request because each request reads them from the `config` table
(`backend/open_webui/routers/tasks.py:80-98`; `backend/open_webui/utils/context_compaction.py:198-213`;
`backend/open_webui/utils/subagents.py:290-297`), except the foreground sub-agent limit described in
section 5.14. Timers, automations and the scheduler loop are described in
`automations-calendar-and-timers.md` and `background-processes-and-scheduling.md`.

## 9. Notifications and Emails

**No email** is sent by this area (the backend has no email-sending code; ground truth).

### 9.1 Websocket Events Sent to the User's Browser

All go to the room `user:{user_id}` as an `events` message carrying `chat_id`, `message_id` and
`data.type` (`backend/open_webui/socket/main.py:1149-1161`).

| Event type | Sent when | What the browser does | Evidence |
|---|---|---|---|
| `chat:active` | A chat starts or stops having running tasks | Sidebar busy state; on "inactive" with an unfinished reply, reloads the chat | `backend/open_webui/main.py:1748-1772`, `:1867-1875`; `src/lib/components/chat/Chat.svelte:1229-1242` |
| `status` | Progress steps (web search, knowledge, queries, sources, images) | Adds a status line | `backend/open_webui/utils/middleware.py:1562-1728`, `:1871-2039`, `:2091-2165`, `:2609-2618`, `:3249-3259`; `src/lib/components/chat/Chat.svelte:1221-1226` |
| `context_compaction` | Compaction starts, succeeds or fails | Loading, success or error pop-up | `backend/open_webui/utils/context_compaction.py:75-145`; `src/lib/components/chat/Chat.svelte:1173-1201` |
| `response:completion` | Each streamed text, reasoning or tool-call delta | Appends to the reply | `backend/open_webui/utils/middleware.py:4997-5005`, `:5050-5057`, `:5879-5889`; `src/lib/components/chat/Chat.svelte:2761-2780` |
| `chat:completion` | Sources, usage, full-output refreshes, provider errors, the final `done: true` | Updates the reply; on done, copies or reads aloud if the user chose so, and starts the next queued message | `backend/open_webui/utils/middleware.py:4901-4907`, `:5217-5224`, `:6575-6580`; `src/lib/components/chat/Chat.svelte:2782-2902` |
| `chat:message:error` | A failure inside the task, including a background task that raised after a complete streaming reply (section 5.7) | Grey error box (under the answer, when there is one) | `backend/open_webui/main.py:1703-1710`; `src/lib/components/chat/Chat.svelte:1284-1292` |
| `chat:tasks:cancel` | A reply is stopped or a paused reply is abandoned | Marks the replies done | `backend/open_webui/main.py:1677-1682`, `:2212`; `backend/open_webui/utils/middleware.py:6621`; `src/lib/components/chat/Chat.svelte:1250-1264` |
| `chat:message:follow_ups` | Follow-ups generated | Shows suggestions | `backend/open_webui/utils/middleware.py:3917-3924` |
| `chat:title`, `chat:tags` | Title or tags saved | Refreshes title, chat list and tags | `backend/open_webui/utils/middleware.py:3983-3999`, `:4029-4034`; `src/lib/components/chat/Chat.svelte:1319-1327` |
| `chat:outlet` | Outlet filters changed messages | Replaces the shown text | `backend/open_webui/utils/middleware.py:4200-4206`; `src/lib/components/chat/Chat.svelte:1299-1315` |
| `chat:list` | A saved chat was created, received a message or finished | Sidebar refresh | `backend/open_webui/main.py:288-295`; `backend/open_webui/utils/middleware.py:232-235` |
| `chat:reload` | A sub-agent result or timer turn was added to the chat | Reloads the chat | `backend/open_webui/utils/subagents.py:230-240`, `:647-658`; `src/lib/components/chat/Chat.svelte:1209-1212` |
| `source`, `files`, `embeds` | Citations, images or tool UI produced during the reply | Adds them to the reply | `backend/open_webui/utils/middleware.py:5156-5173`, `:5425-5430`, `:1493-1510` |

### 9.2 "Reply Finished" Notices

When a reply finishes in a chat the user is not looking at (or the tab is in the background), the
browser shows an in-app pop-up with the chat title (or `New Chat`) and the start of the answer, and,
if the user enabled notifications in their settings, a browser notification titled
`{title} / {WEBUI_NAME}`; it can also play a sound (`src/routes/+layout.svelte:735-781`). This is
driven by the final `chat:completion` event, so it does not appear when that event is not delivered
(section 5.5).

### 9.3 Platform Events (Webhooks and Notification Targets)

The pipeline publishes these events; delivery to admin webhooks and to users' own notification
targets is described in `notifications-webhooks-events-and-banners.md`:

| Event | Published when | Evidence |
|---|---|---|
| `chat.created` | A new chat is created by the pipeline | `backend/open_webui/main.py:1418-1424`; `backend/open_webui/events.py:161-163` |
| `message.created` | User message and each assistant placeholder saved | `backend/open_webui/main.py:1426-1451`, `:1528-1538`, `:1623-1633`; `backend/open_webui/events.py:215-217` |
| `chat.finished` | A reply in a saved, non-internal chat finished; carries the chat link built from `webui.url`, the title and the reply text | `backend/open_webui/utils/middleware.py:206-231`; `backend/open_webui/events.py:164-166` |
| `chat.failed` | Only when processing a non-streaming reply raised an error, which includes a background task (follow-ups, tags) raising after the reply was delivered and `chat.finished` published (sections 5.7 and 5.8) | `backend/open_webui/utils/middleware.py:4388-4409`; `backend/open_webui/events.py:167-169` |
| `chat.compacted` | Manual compaction succeeded | `backend/open_webui/routers/chats.py:1308-1315` |
| `chat.cloned` | A chat was forked | `backend/open_webui/routers/chats.py:1765-1771` |
| `config.updated` | Sub-agent settings saved | `backend/open_webui/routers/configs.py:796-803` |

`chat.finished` and `chat.failed` are the two chat events users can subscribe to for their own
notifications (`backend/open_webui/events.py:669-675`; `backend/open_webui/utils/notifications.py:16-20`).
The `chat.finished` payload contains the full reply text, which is conversation content.

## 10. Error, Warning and Notice Messages (Verbatim)

Placeholders are written `{name}` using the source's variable name. "Pop-up" is a toast; "error
box" is the grey box under a reply (`src/lib/components/chat/Messages/Error.svelte`). Unless stated,
the English text is shown as written (front-end plain i18n keys display their own text).

### 10.1 Backend Errors and Notices Users Can See

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Model not found` | Error | `backend/open_webui/main.py:1129`, `:1182`; `backend/open_webui/utils/models.py:480`, `:491`, `:515`, `:521`; `backend/open_webui/utils/chat.py:193`, `:330`; `backend/open_webui/utils/actions.py:46` | Model id not in the server's list, custom model's base model missing, or the user has no read access to the model (or its base). Shown as a pop-up and in the error box (HTTP 400) | Pick another model; ask an admin whether the model should be available | Admin: is the model listed and active in Workspace > Models, shared with the user's group, and is its base model still offered by the connection? Server log has `Model access denied: ... reason=...` |
| `Something went wrong :/` | Error | `backend/open_webui/main.py:1324`, `:1335`, `:1349`, `:1498`, `:2086` (text from `backend/open_webui/constants.py:16-18`) | Posting into a chat the user does not own (HTTP 404), or a channel the user cannot write to (HTTP 403) | Open a new chat | Confirm chat ownership with the chat id (`/status` shows it); escalate if the user owns it |
| `We could not find what you're looking for :/` | Error | `backend/open_webui/main.py:1317`, `:1359`, `:2167`, `:2171`; `backend/open_webui/routers/chats.py:1281`; `backend/open_webui/utils/tool_approval.py:36`, `:134`, `:138` | Channel missing; new chat in a folder the user cannot write to; stopping a chat that is not the user's; compacting another user's chat; resolving a message that no longer exists | Reload the page; start the chat outside the folder | Check folder sharing; check the chat still exists |
| `Channel chats are not supported on this endpoint` | Error | `backend/open_webui/main.py:2080` | `/api/chat/completed` or an Action called on a channel message (HTTP 400) | None (integration issue) | Escalate with the integration name |
| `Finalized pending approval message.` | Notice (API answer) | `backend/open_webui/main.py:2199` | Stop pressed on a chat with no running task but an unfinished or paused reply | None | Expected after abandoning a tool approval |
| `Direct connection requires an active WebSocket session; cannot generate completion in this context (e.g. background task).` | Error | `backend/open_webui/utils/chat.py:65-68` | A direct (user-configured) connection used without a live browser session, for example by an automation or sub-agent | Use a server-side model for automations | Confirm the model is a direct connection |
| `Missing message id` | Error | `backend/open_webui/utils/chat.py:326`, `:342` | Deprecated `/api/chat/completed` called without a message id (HTTP 400) | None | Integration issue |
| `Error: {e}` | Error | `backend/open_webui/utils/chat.py:339`, `:374`; `backend/open_webui/utils/actions.py:151` | An outlet filter (deprecated endpoint) or an Action raised an error; shown as a pop-up for Actions | Retry; report the Action name | Server log; the Action's author |
| `Provider returned HTTP {status_code}` | Error | `backend/open_webui/utils/misc.py:45` | Provider answered with an HTTP error whose body could not be read | Retry later | Admin: connection health, key, quota |
| `Provider returned an error` | Error | `backend/open_webui/utils/misc.py:45` | As above when not even a status code is known | Retry later | As above |
| `Failed to connect to MCP server '{server_id}'` | Error (reply continues) | `backend/open_webui/utils/middleware.py:3011` | A selected MCP tool server could not be reached or authenticated | Retry; deselect the tool | Admin: tool server status, its authentication; see `workspace-tools-tool-servers-mcp-and-terminals.md` |
| `Terminal unavailable: {e}` | Error | `backend/open_webui/utils/middleware.py:3063` | The selected terminal's tools could not be loaded (HTTP 503 inside the task) | Deselect the terminal and resend | Terminal server status |
| `Tool-call limit reached ({max_tool_call_iterations} iterations).` | Error | `backend/open_webui/utils/middleware.py:6345` | The model kept calling tools past the limit | Rephrase; ask for fewer steps | `CHAT_RESPONSE_MAX_TOOL_CALL_ITERATIONS`, or sub-agent Max iterations |
| `Chat completion stream failed` | Error (API callers) | `backend/open_webui/utils/middleware.py:6710` | Streaming to an API caller failed mid-reply; sent as the last stream event | Retry | Server log `Chat completion stream failed mid-response: ...` |
| `Invalid JSON response` | Error | `backend/open_webui/utils/middleware.py:3668` | A non-streaming reply's body could not be decoded | Retry | Provider or pipe output format |
| `Code interpreter engine not configured.` | Notice (shown as code output) | `backend/open_webui/utils/middleware.py:6423` | Legacy-mode code interpreter with no valid engine set | None | Admin: Code Execution settings |
| `Title generation is disabled` | Notice (API answer, not shown) | `backend/open_webui/routers/tasks.py:146` | Title task called while switched off; the chat gets the first-message title only while it holds just its first exchange (section 5.12) | None | `task.title.enable` |
| `Follow-up generation is disabled` | Notice (API answer, not shown) | `backend/open_webui/routers/tasks.py:219` | Follow-up task called while switched off | None | `task.follow_up.enable` |
| `Tags generation is disabled` | Notice (API answer, not shown) | `backend/open_webui/routers/tasks.py:284` | Tag task called while switched off | None | `task.tags.enable` |
| `No model specified for title generation. Please ensure a model is selected for this chat.` | Error | `backend/open_webui/routers/tasks.py:161` | Sidebar **Generate** on a chat with no recorded model (pop-up) | Send a message first, then retry | None |
| `Model '' was not found` | Error | `backend/open_webui/routers/tasks.py:166`, `:234`, `:299`, `:358`, `:435`, `:511`, `:570`, `:625`; `backend/open_webui/routers/openai.py:1550-1551` (text from `backend/open_webui/constants.py:89`) | A task endpoint, or the OpenAI-compatible route, was given a model id that is not in the list; the name is empty because the code passes none. When a background task hits it after a streaming reply, it appears in the grey error box under a complete answer; after a non-streaming reply it becomes the text of a `chat.failed` event (section 5.7) | Pick an available model; an answer shown above the box is complete | As for `Model not found`; section 11.20 |
| `An internal error has occurred.` | Error (usually not shown) | `backend/open_webui/routers/tasks.py:210`, `:275`, `:340`, `:399`, `:552` | A title, follow-up, tags, image-prompt or autocomplete call failed; the pipeline treats it as "no result". Shown as a pop-up only for sidebar **Generate** | Retry later | Server log `Exception occurred` or `Error generating chat completion: ...`; Task Model access for ordinary users |
| `Search query generation is disabled` | Error (not shown) | `backend/open_webui/routers/tasks.py:410` (text from `backend/open_webui/constants.py:125`) | Web-search query generation switched off; the user's message is searched as-is | None | `task.query.search.enable` |
| `Query generation is disabled` | Error (not shown) | `backend/open_webui/routers/tasks.py:416` | Retrieval query generation switched off; the user's message is used | None | `task.query.retrieval.enable` |
| `Autocompletion generation is disabled` | Error (not shown) | `backend/open_webui/routers/tasks.py:484` | Autocomplete called while switched off | None | `task.autocomplete.enable` |
| `Input prompt exceeds maximum length of {size}` | Error (not shown) | `backend/open_webui/routers/tasks.py:496` (text from `backend/open_webui/constants.py:126`) | Draft longer than **Autocomplete Generation Input Max Length**; no suggestion appears | None | `task.autocomplete.input_max_length` |
| `No available model for context compaction` | Error (log only) | `backend/open_webui/utils/context_compaction.py:355` | Neither the compaction model nor the chat model is in the model list; the turn continues uncompacted | None | Compaction model setting |
| `Wait for the current response to finish before compacting.` | Warning | `backend/open_webui/routers/chats.py:1286`; `src/lib/components/chat/Chat.svelte:2973` | `/compact` while a reply runs (HTTP 409 or a browser check) | Wait, then retry | With several workers and no Redis this check can be wrong (section 5.9) |
| `No model found for context compaction.` | Error | `backend/open_webui/routers/chats.py:1305` | `/compact` on a chat with no recorded model (HTTP 400) | Send a message first | None |
| `Wait for the current response to finish before forking.` | Warning | `backend/open_webui/routers/chats.py:1689`; `src/lib/components/chat/Chat.svelte:3062` | Fork while a reply runs (HTTP 409 or a browser check) | Wait, then retry | As above |
| `chat has no messages to fork` | Error | `backend/open_webui/routers/chats.py:1699`; `backend/open_webui/utils/chat_fork.py:6` | Fork of an empty chat (HTTP 400) | None | None |
| `message not found` | Error | `backend/open_webui/utils/chat_fork.py:19` | Fork at a message that is not in the chat (HTTP 404) | Reload, retry | None |
| `message branch contains a cycle` | Error | `backend/open_webui/utils/chat_fork.py:14` | The chat's message tree is corrupted (HTTP 400) | None | Escalate with the chat id |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error | `backend/open_webui/routers/chats.py:237`; `backend/open_webui/utils/tool_approval.py:31` (text from `backend/open_webui/constants.py:70-72`) | Fork without `chat.import` (HTTP 403); resolving a tool call in another user's chat (HTTP 401) | Ask an admin about the permission | User's group permissions (`chat.import`) |
| `Message has no resolvable output.` | Error | `backend/open_webui/utils/tool_approval.py:40` | Approve or reject on a message without tool calls (HTTP 400, pop-up) | Reload | None |
| `Tool call not found.` | Error | `backend/open_webui/utils/tool_approval.py:51` | The tool call id is not on the message (HTTP 404, pop-up) | Reload | None |
| `Tool call has already been resolved.` | Error | `backend/open_webui/utils/tool_approval.py:58` | Approving twice, or after Stop (HTTP 409, pop-up) | Reload | Expected after double clicks or another tab |
| `ask_user requires an answer or deny.` | Error | `backend/open_webui/utils/tool_approval.py:62` | Approve used on an `ask_user` question (HTTP 400) | Answer or decline instead | None |
| `Tool call does not accept answers.` | Error | `backend/open_webui/utils/tool_approval.py:78` | Answer sent to a normal tool call (HTTP 400) | Approve or reject instead | None |
| `Answers are required for ask_user.` | Error | `backend/open_webui/utils/tool_approval.py:80` | Empty answer to an `ask_user` question (HTTP 400) | Fill in the answer | None |
| `Tool call parent message is missing.` | Error | `backend/open_webui/utils/tool_approval.py:143` | The user message above the paused reply was deleted (HTTP 409) | Start a new turn | Escalate with chat id |
| `Tool call message model is missing.` | Error | `backend/open_webui/utils/tool_approval.py:160` | Paused reply has no model recorded (HTTP 409) | Start a new turn | Escalate with chat id |
| `Plugins are disabled by ENABLE_PLUGINS=false` | Error | `backend/open_webui/utils/actions.py:21` | An Action button used while plugins are disabled (pop-up) | None | `ENABLE_PLUGINS` |
| `Action not found: {action_id}` | Error | `backend/open_webui/utils/actions.py:30` | Action function deleted (pop-up) | Reload | Admin > Functions |
| `Action not available: {action_id}` | Error | `backend/open_webui/utils/actions.py:54`, `:64` | Action inactive, not attached to the model, or not an Action (pop-up) | None | Admin > Functions and the model's Actions |
| `Client session disconnected.` | Error | `backend/open_webui/socket/main.py:1266` | The server needed the browser (direct connection, direct tool, browser Python) but that browser session is gone; appears as the tool result or inside the error text | Keep the tab open; resend | Websocket connectivity (`websockets-realtime-and-redis.md`) |
| `Event call timed out. The browser tab may be inactive or closed.` | Error | `backend/open_webui/socket/main.py:1281` | The browser did not answer within `WEBSOCKET_EVENT_CALLER_TIMEOUT` | Keep the tab in front; resend | Timeout setting |
| `Error submitting message` | Error | `src/lib/components/chat/Messages/Error.svelte:37` | Error box fallback when the error has no text | Retry | Server log at the time of the failure |

### 10.2 Status Lines Emitted by This Code

Status lines appear above the reply and are saved in `statusHistory`. Some are sent with only an
`action` and the browser supplies the wording (last column of the Source cell). They are hidden for
users with **Hide Processing Details** on and for models whose status-updates capability is off
(section 12). Full wording rules: `in-chat-status-and-response-messages.md`.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Searching the web` | Status | `backend/open_webui/utils/middleware.py:1567`; displayed via `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:142-143` | Legacy-mode web search starts | Wait | None |
| `No search query generated` | Status | `backend/open_webui/utils/middleware.py:1635`; `StatusItem.svelte:30-31`, `:138-139` | Query generation returned an empty list | Rephrase to ask for current information | Query generation prompt |
| `Searching` (with query chips) | Status | Action `web_search_queries_generated`, `backend/open_webui/utils/middleware.py:1642-1651`; text from `StatusItem.svelte:52-59` | Search queries ready | Wait | None |
| `Searched {{count}} sites` | Status | `backend/open_webui/utils/middleware.py:1694`; `StatusItem.svelte:26-29` | Search finished with results | None | None |
| `No search results found` | Status (error flag) | `backend/open_webui/utils/middleware.py:1707` | Search engine returned nothing | Rephrase | Web search engine settings (`web-search-and-web-loading.md`) |
| `An error occurred while searching the web` | Status (error flag) | `backend/open_webui/utils/middleware.py:1722` | Search failed without a specific detail; when the search raised an HTTP error its own detail is shown instead | Retry later | Web search provider status and key |
| `Creating image` | Status | `backend/open_webui/utils/middleware.py:1874` | Legacy-mode image generation starts (saved chats only) | Wait | None |
| `Image created` | Status | `backend/open_webui/utils/middleware.py:1893`, `:2001` | Image generated or edited | None | None |
| `An error occurred while generating an image` | Status | `backend/open_webui/utils/middleware.py:1927`, `:2035` | Image generation or editing failed; the model is told the error text and usually explains it | Retry or rephrase | Image engine (`image-generation-and-editing.md`) |
| `Image generation is disabled` | Status | `backend/open_webui/utils/middleware.py:1940` | Image generation requested while switched off. *Corrected 2026-10-10: effectively unreachable; with generation off and no edit, the step returns earlier with no status (`backend/open_webui/utils/middleware.py:1866-1868`), and this branch (`:1935`) is reached only if the setting changes between two reads in one request. See `image-generation-and-editing.md` section 10.* | None | `image_generation.enable` |
| `Searching Knowledge for "{{searchQuery}}"` | Status | Action `knowledge_search`, `backend/open_webui/utils/middleware.py:2609-2618` (and a hidden "done" at `:3249-3259`); text from `StatusItem.svelte:40-50` | Legacy mode with model knowledge | Wait | None |
| `Querying` (with query chips) | Status | Action `queries_generated`, `backend/open_webui/utils/middleware.py:2091-2100`; text from `StatusItem.svelte:78-85` | Retrieval queries ready | Wait | None |
| `No sources found` | Status | Action `sources_retrieved` with count 0, `backend/open_webui/utils/middleware.py:2156-2165`; `StatusItem.svelte:111-112` | Nothing relevant retrieved, **or retrieval failed** | Check the file finished processing; rephrase | Server log around the time; `rag-retrieval-embeddings-and-vector-stores.md` |
| `Retrieved 1 source` | Status | Same; `StatusItem.svelte:113-114` | One source used | None | None |
| `Retrieved {{count}} sources` | Status | Same; `StatusItem.svelte:120-122` | Several sources used | None | None |
| `Compacting context` | Status (pop-up) | `backend/open_webui/utils/context_compaction.py:81`; `src/lib/components/chat/Chat.svelte:1197` | Automatic compaction started | Wait | None |
| `Context compacted` | Notice (pop-up) | `backend/open_webui/utils/context_compaction.py:141`; `src/lib/components/chat/Chat.svelte:1186`, `:2985` | Compaction finished | None | None |
| `Context compaction failed` | Error (pop-up) | `backend/open_webui/utils/context_compaction.py:105`; `src/lib/components/chat/Chat.svelte:1181`, `:3000` | Summary call failed; the reply continues with the full history | None, unless the reply then fails | Compaction model availability; server log |

### 10.3 Front-End Messages Tied to This Pipeline

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Uh-oh! There was an issue with the response.` | Error | `src/lib/components/chat/Chat.svelte:3654`, `:3745`; `src/lib/i18n/locales/en-US/translation.json:3324` | (a) The send request failed with a non-text error (pop-up); (b) prefix of the error box when the provider sent an error chunk, followed by the provider's message | Read the line after it; retry | The provider message names the cause (key, quota, content filter, model) |
| `Please enter a prompt` | Error | `src/lib/components/chat/Chat.svelte:3135` | Send with no text and no file | Type a message | None |
| `Model not selected` | Error | `src/lib/components/chat/Chat.svelte:3139`, `:2636` | No model chosen | Choose a model | Model list empty? See `model-connections-openai-ollama-and-direct.md` |
| `Chat Variables have conflicting model definitions` | Error | `src/lib/components/chat/Chat.svelte:3145` | Selected models define the same chat variable differently | Use one model, or ask the model owner to align the definitions | The models' system prompts |
| `Failed to save chat variables` | Error | `src/lib/components/chat/Chat.svelte:721` | Saving chat variable values failed | Retry | Server log |
| `Compacting context...` | Notice | `src/lib/components/chat/Chat.svelte:2978` | `/compact` started | Wait | None |
| `Context compaction is disabled` | Notice | `src/lib/components/chat/Chat.svelte:2958`, `:2993` | `/compact` while compaction is off | None | `chat.context_compaction.enable` |
| `No chat to compact` | Notice | `src/lib/components/chat/Chat.svelte:2963`, `:2991` | `/compact` in an empty or unsaved chat | None | None |
| `Chat is too short to compact` | Notice | `src/lib/components/chat/Chat.svelte:2989` | Only one message after the last checkpoint | None | None |
| `Nothing to compact` | Notice | `src/lib/components/chat/Chat.svelte:2994` | Server compacted nothing for another reason | None | None |
| `No chat to fork` | Notice | `src/lib/components/chat/Chat.svelte:3048` | `/fork` in an empty or unsaved chat | None | None |
| `Access prohibited` | Error | `src/lib/components/chat/Chat.svelte:3052` | `/fork` without the `chat.import` permission | Ask an admin | Group permissions |
| `Forking chat...` | Notice | `src/lib/components/chat/Chat.svelte:3066` | Fork started | Wait | None |
| `Chat forked` | Notice | `src/lib/components/chat/Chat.svelte:3080` | Fork succeeded; the new chat opens | None | None |
| `Failed to fork chat` | Error | `src/lib/components/chat/Chat.svelte:3082` | Server returned no chat | Retry | Server log |
| `This model is not publicly available. Please select another model.` | Warning (admin) | `src/lib/components/admin/Settings/Interface.svelte:109` | Admin picked a task or compaction model without public read access | Pick a public model, or accept that ordinary users' tasks will fail | Section 5.11 |
| `Failed to load Interface settings` | Error (admin) | `src/lib/components/admin/Settings/Interface.svelte:153` | Task or chat settings could not be loaded | Reload | Server log |
| `Settings saved successfully!` | Notice (admin) | `src/lib/components/chat/SettingsModal.svelte:882`; `src/lib/components/admin/Settings/Subagents.svelte:50` | Interface panel: shown as soon as Save is pressed, before the server answers. Sub-agents panel: shown after the server accepted | Reopen the Interface panel to confirm | Section 7.3 |
| `Allow the AI to delegate tasks to sub-agents. Each sub-agent creates a real chat with full tool access. Uses additional LLM calls.` | Notice (help text) | `src/lib/components/admin/Settings/Subagents.svelte:76-78` | Sub-agents panel | None | None |
| `[object Object]` | Error (admin) | Not a string in the source: it is how the browser renders an error object. `src/lib/components/admin/Settings/Subagents.svelte:32`, `:53` print the error as `${error}`, and `src/lib/apis/configs/index.ts:728`, `:741` throw the server's JSON body | Loading or saving sub-agent settings failed | Retry; report the action | Server log for `/api/v1/configs/subagents` |
| `Generating...` | Notice | `src/lib/components/layout/Sidebar/ChatItem.svelte:628` | Sidebar **Generate** title running | Wait | None |
| `New Chat` | Notice | `backend/open_webui/main.py:1399`; `src/routes/+layout.svelte:741` | Title of a new chat until a title is produced; also the fallback heading of the "reply finished" pop-up | None | Section 5.12 |
| `{title} / {WEBUI_NAME}` | Notice (browser notification) | `src/routes/+layout.svelte:760` | A reply finished in another chat or a background tab, with browser notifications enabled | None | User notification settings |

### 10.4 Tool Results and Model-Facing Texts

These are written for the model, not the user, but users can see them in a tool call's expanded
details (unless processing details are hidden), in sub-agent chats, or paraphrased in the answer.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Error: Tool call arguments could not be parsed. The model generated malformed or incomplete JSON.` | Tool result | `backend/open_webui/utils/middleware.py:3338-3339` | Resumed approved call had unreadable arguments | Retry | Model's tool-calling quality |
| `Error: Tool call arguments could not be parsed. The model generated malformed or incomplete JSON for {tool_function_name}. Please try again.` (the name is in back-quotes in the source) | Tool result | `backend/open_webui/utils/middleware.py:6055-6056` | Model produced unreadable arguments | Retry; try another model | As above |
| `Error: Tool call arguments for {name} must be a JSON object. Please try again.` (the name is in back-quotes in the source) | Tool result | `backend/open_webui/utils/middleware.py:5988` | Arguments were valid JSON but not an object | Retry | As above |
| `Error: Tool call arguments must be a JSON object.` | Tool result | `backend/open_webui/utils/middleware.py:3345` | Same, on the resume path | Retry | As above |
| `Error: Tool "{name}" not found.` | Tool result | `backend/open_webui/utils/middleware.py:3351`, `:5997` | Model called a tool that is not available in this turn | Reselect the tool | Tool still installed and allowed for the user |
| `Error: Browser session is not connected for this direct tool.` | Tool result | `backend/open_webui/utils/middleware.py:3362` | Approved direct (browser-side) tool resumed without a live browser session | Keep the tab open; resend | Websocket connectivity |
| `Error: tool call rejected by user.` | Tool result | `backend/open_webui/utils/tool_approval.py:72` | User rejected a tool call | None | None |
| `{tool_function_name}: Embedded UI result is active and visible to the user.` | Tool result | `backend/open_webui/utils/middleware.py:1084`, `:1150`, `:1165` | Tool returned an embedded interface | None | None |
| `{tool_function_name}: Client error {tool_result.status_code} from embedded UI result.` | Tool result | `backend/open_webui/utils/middleware.py:1090` | Embedded tool interface returned a 4xx status | Retry | Tool author |
| `{tool_function_name}: Server error {tool_result.status_code} from embedded UI result.` | Tool result | `backend/open_webui/utils/middleware.py:1096` | Embedded tool interface returned a 5xx status | Retry | Tool author |
| `{tool_function_name}: Unexpected status code {tool_result.status_code} from embedded UI result.` | Tool result | `backend/open_webui/utils/middleware.py:1102` | Any other status | Retry | Tool author |
| `{tool_function_name}: Image file read successfully.` | Tool result | `backend/open_webui/utils/middleware.py:1175` | Tool returned an image | None | None |
| `[Resource: {resource_uri}] (binary data, mimeType: {resource_mime_type})` | Tool result | `backend/open_webui/utils/middleware.py:1231` | MCP tool returned a non-image binary resource | None | None |
| `Here are the images from the tool results above. Please analyze them.` | Model-facing | `backend/open_webui/utils/middleware.py:6276`; `backend/open_webui/utils/misc.py:412` | Tool returned images; they are passed to the model as a user message | None | None |
| `[CONVERSATION SUMMARY]` | Model-facing | `backend/open_webui/utils/middleware.py:2508` | Prefix of the compaction summary added to the system message | None | None |
| `<context>The requested image has been edited and created and is now being shown to the user. Let them know that it has been generated.</context>` | Model-facing | `backend/open_webui/utils/middleware.py:1912` | Legacy-mode image edit succeeded | None | None |
| `<context>Image generation was attempted but failed. The system is currently unable to generate the image. Tell the user that the following error occurred: {error_message}</context>` | Model-facing | `backend/open_webui/utils/middleware.py:1933` | Legacy-mode image edit failed | None | Image engine |
| `<context>Image generation was requested but the feature is currently disabled by the administrator, so no image was created. Let the user know that image generation is currently unavailable.</context>` | Model-facing | `backend/open_webui/utils/middleware.py:1946` | Image generation switched off | None | `image_generation.enable` |
| `<context>The requested image has been created by the system successfully and is now being shown to the user. Let the user know that the image they requested has been generated and is now shown in the chat.</context>` | Model-facing | `backend/open_webui/utils/middleware.py:2020` | Legacy-mode image generated | None | None |
| `<context>Image generation was attempted but failed because of an error. The system is currently unable to generate the image. Tell the user that the following error occurred: {error_message}</context>` | Model-facing | `backend/open_webui/utils/middleware.py:2041` | Legacy-mode image generation failed | None | Image engine |
| `Error: request context not available.` | Tool result | `backend/open_webui/tools/builtin.py:1702` | `delegate_task` called outside a request | None | Escalate |
| `Error: sub-agents cannot delegate recursively.` | Tool result | `backend/open_webui/tools/builtin.py:1704` | A sub-agent tried to start another sub-agent | None | Expected |
| `Error: task must not be empty.` | Tool result | `backend/open_webui/utils/subagents.py:286` | Model delegated an empty task | None | None |
| `Error: chat and user context are required.` | Tool result | `backend/open_webui/utils/subagents.py:288` | Delegation outside a saved chat | Use a saved (non-temporary) chat | None |
| `Error: background sub-agents are disabled in settings.` | Tool result | `backend/open_webui/utils/subagents.py:308` | Background delegation while background sub-agents are off | None | `subagents.background_enabled` |
| `Error: model context is required.` | Tool result | `backend/open_webui/utils/subagents.py:332` | No model id available to the sub-agent | None | Escalate |
| `Error: sub-agents are unavailable for direct connections.` | Tool result | `backend/open_webui/utils/subagents.py:334` | Delegation from a direct-connection model | Use a server-side model | None |
| `Error: file_ids not attached or unavailable: {ids}` | Tool result | `backend/open_webui/utils/subagents.py:356` | Model passed file ids not attached to the chat | Attach the files to the chat first | None |
| `Error: Async subagent capacity reached ({max_async} running). Wait for one to finish or increase subagents.max_async.` | Tool result | `backend/open_webui/utils/subagents.py:366-367` | Too many background sub-agents in this worker | Wait | `subagents.max_async` |
| `Failed to create sub-agent chat` | Error (inside the next message) | `backend/open_webui/utils/subagents.py:438` | The hidden chat could not be created | Retry | Database health |
| `Error: failed to create {prefix}sub-agent: {exc}` | Tool result | `backend/open_webui/utils/subagents.py:446` | Creating the sub-agent failed (`prefix` is `background ` or empty) | Retry | Server log |
| `Sub-agent chat or completion message no longer exists.` | Tool result | `backend/open_webui/utils/subagents.py:493` | The sub-agent chat was deleted while running | None | None |
| `[output truncated]` | Tool result | `backend/open_webui/utils/subagents.py:512` | Sub-agent result longer than Max output | Ask for a shorter result | `subagents.max_output` |
| `Sub-agent produced no output.` | Tool result | `backend/open_webui/utils/subagents.py:516`, `:702` | Sub-agent finished with empty text | Retry | Sub-agent chat content |
| `Sub-agent cancelled.` | Error (in the sub-agent chat) | `backend/open_webui/utils/subagents.py:523` | Sub-agent task cancelled | None | None |
| `[ASYNC SUBAGENT COMPLETE - {delegation_id}]` | Model-facing (hidden internal message) | `backend/open_webui/utils/subagents.py:553` | First line of a background sub-agent result posted into the parent chat | None | None |
| `A background subagent you dispatched earlier has finished. The original task source is included so you can decide whether to use the result or continue without it.` | Model-facing | `backend/open_webui/utils/subagents.py:555-557` | Same message, second line | None | None |
| `Subagent completed without a final summary.` | Model-facing | `backend/open_webui/utils/subagents.py:572` | Background sub-agent completed with no text | None | None |
| `The subagent was interrupted before completing.` | Model-facing | `backend/open_webui/utils/subagents.py:574` | Background sub-agent cancelled | None | None |
| `The subagent did not complete successfully.{detail}` | Model-facing | `backend/open_webui/utils/subagents.py:579` | Background sub-agent failed | None | Sub-agent chat error |
| `Error: sub-agent was cancelled.` | Tool result | `backend/open_webui/utils/subagents.py:696` | Foreground sub-agent cancelled | None | None |
| `Error: {exc}` | Tool result | `backend/open_webui/utils/subagents.py:677`, `:698` | Sub-agent task could not start or raised | Retry | Server log |
| `Error: {error}` or `Error: sub-agent failed.` | Tool result | `backend/open_webui/utils/subagents.py:701` | Foreground sub-agent ended with an error | Retry | Sub-agent chat error |
| `Sub-agent: {task[:60]}` | Notice (hidden chat title) | `backend/open_webui/utils/subagents.py:400` | Title of every sub-agent chat | None | Use to find sub-agent chats in an admin chat view |

### 10.5 Server Log Lines That Explain Symptoms

Log lines are not shown to users. They are what an administrator searches for in the server's
standard output (ground truth: logs go to standard output only). Several include user ids or, at
debug level, email addresses; handle log extracts as personal data.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Error processing chat metadata: {e}` | Log (warning) | `backend/open_webui/main.py:1641` | Any failure before the task starts (paired with an HTTP 400) | None | Gives the real reason behind a pop-up |
| `Error processing chat payload: %s` | Log (error) | `backend/open_webui/main.py:1688` | Any failure inside the task (paired with the error box), including a background task that raised after a complete streaming reply (section 5.7) | None | Same text as the error box |
| `Error occurred while processing request: %s` | Log (debug) | `backend/open_webui/utils/middleware.py:4389` | Processing a non-streaming reply raised, including a background task that raised after the answer was delivered; paired with a `chat.failed` event for saved chats (section 5.7) | None | Needs debug logging; match its time to the `chat.failed` notification |
| `Chat processing was cancelled` | Log (info) | `backend/open_webui/main.py:1674` | A task was stopped | None | Confirms Stop reached the right worker |
| `Task was cancelled!` | Log (warning) | `backend/open_webui/utils/middleware.py:6592` | A streaming reply was stopped | None | As above |
| `Error generating initial chat title` | Log (exception) | `backend/open_webui/main.py:1490` | The separate title job of a new chat raised. As written it is expected after every new chat the server creates from the web interface (not temporary or embedded chats), with `KeyError: 'model'` from the memory-review step, even when the title was saved (section 5.7; section 14) | None | Read the exception under it: `KeyError: 'model'` alone is not a title failure; another error (for example `Model '' was not found` or a Pipelines filter message) means the title step failed and the chat stays `New Chat` |
| `Failed to process pending internal messages for chat %s` | Log (exception) | `backend/open_webui/main.py:1800` | Background sub-agent result or timer could not be turned into a turn | None | Sub-agent issues |
| `Context compaction failed; continuing with full chat history` | Log (exception) | `backend/open_webui/utils/middleware.py:2513` | Automatic compaction failed | None | Compaction model |
| `Compacted chat context for chat=%s checkpoint=%s response=%s dropped=%d kept=%d summary_chars=%d` | Log (info) | `backend/open_webui/utils/context_compaction.py:125-133` | Automatic compaction succeeded | None | Confirms compaction ran |
| `Provider returned error (non-streaming): %s` | Log (error) | `backend/open_webui/utils/middleware.py:4238` | Provider answered with an error body | None | Provider error text |
| `Provider returned error (streaming): %s` | Log (error) | `backend/open_webui/utils/middleware.py:5229` | Provider sent an error chunk | None | Provider error text |
| `Tool-call iteration limit reached (%s)` | Log (warning) | `backend/open_webui/utils/middleware.py:6344` | Tool loop limit | None | Limit setting |
| `Tool-call continuation failed: %s` | Log (exception) | `backend/open_webui/utils/middleware.py:6335` | Model call after tools failed | None | Provider error |
| `Code interpreter continuation failed: %s` | Log (exception) | `backend/open_webui/utils/middleware.py:6534` | Model call after code execution failed | None | Provider error |
| `Chat completion stream failed mid-response: %s` | Log (exception) | `backend/open_webui/utils/middleware.py:6708` | API stream failed | None | Provider or network |
| `Error running outlet filters: %s` | Log (debug) | `backend/open_webui/utils/middleware.py:4208` | Outlet filter failed (silently) | None | Filter author; needs debug logging |
| `Pipeline outlet filter error: %s` | Log (debug) | `backend/open_webui/utils/middleware.py:4149` | Pipelines outlet failed (silently) | None | Pipelines server |
| `MCP server with id {server_id} not found` | Log (error) | `backend/open_webui/utils/middleware.py:2358` | Selected MCP server no longer configured; its tools are skipped | None | Tool server settings |
| `Access denied to MCP server {server_id} for user {user.id}` | Log (warning) | `backend/open_webui/utils/middleware.py:2362` | User lacks access to the MCP server; its tools are skipped silently | None | Tool server access |
| `Tool "{tool_function_name}" not found` | Log (warning) | `backend/open_webui/utils/middleware.py:1430` | Legacy tool selection named an unknown tool | None | Tools prompt or model |
| `Could not store tool image; retaining inline image` | Log (warning) | `backend/open_webui/utils/middleware.py:1048` | Tool image could not be saved as a file | None | Storage health |
| `Error getting OAuth token: {e}` | Log (error) | `backend/open_webui/utils/middleware.py:3828` | Sign-in session token for tools could not be read; tools needing it may fail | None | `sso-oauth-oidc-and-scim.md` |
| `Model access denied: user_id=%r model_id=%r reason=model_read_denied` (also `arena_read_denied`, `model_unregistered`) | Log (warning) | `backend/open_webui/utils/models.py:475-513` | The reason behind a `Model not found` for one user | None | Model sharing |
| `generating chat title using model %s for user %s ` | Log (debug) | `backend/open_webui/routers/tasks.py:171`, `:239` (the second is the follow-up task) | Title or follow-up task started; shows which task model was chosen | None | Task Model resolution |
| `generating chat tags using model %s for user %s ` | Log (debug) | `backend/open_webui/routers/tasks.py:304` | Tag task started | None | As above |
| `generating %s queries using model %s for user %s` | Log (debug) | `backend/open_webui/routers/tasks.py:440` | Query task started | None | As above |
| `generating autocompletion using model %s for user %s` | Log (debug) | `backend/open_webui/routers/tasks.py:516` | Autocomplete task started | None | As above |
| `Exception occurred` | Log (error) | `backend/open_webui/routers/tasks.py:207`, `:272`, `:396` | Title, follow-up or image-prompt task failed | None | Following traceback |
| `Error generating chat completion: {e}` | Log (error) | `backend/open_webui/routers/tasks.py:337`, `:549` | Tag or autocomplete task failed | None | Error text |
| `Reusing cached queries: %s` | Log (info) | `backend/open_webui/routers/tasks.py:420` | `ENABLE_QUERIES_CACHE` reused web-search queries | None | None |
| `Redis task command listener failed. Retrying: {e}` | Log (exception) | `backend/open_webui/tasks.py:59` | Stop commands cannot be received; Stop may not work until it reconnects | None | Redis health (`websockets-realtime-and-redis.md`) |
| `Redis task command listener stopped. Retrying.` | Log (warning) | `backend/open_webui/tasks.py:55` | Listener ended; reconnecting | None | As above |
| `Error handling distributed task command: {e}` | Log (exception) | `backend/open_webui/tasks.py:54` | A stop command could not be applied | None | As above |
| `Redis task heartbeat failed` | Log (exception) | `backend/open_webui/tasks.py:80` | Task expiries not renewed; running tasks may vanish from the list after `REDIS_TASK_TTL` | None | Redis health |
| `Failed to write to chat_message table: {e}` | Log (warning) | `backend/open_webui/models/chats.py:1190` | The per-message copy failed; the chat JSON was still saved | None | Database health |
| `Dropped line over max buffer size: %s bytes` | Log (info) | `backend/open_webui/utils/misc.py:1304` | A stream line exceeded `CHAT_STREAM_RESPONSE_CHUNK_MAX_BUFFER_SIZE` | None | That setting |

## 11. Common Tier-1 Issues and Troubleshooting

Before anything else, ask the user to type `/status` in the affected chat and copy the **Chat ID**
it shows (`src/lib/components/chat/MessageInput.svelte:1874-1889`), and note the model name, the
exact text in any pop-up or grey error box, and the time (with time zone). Tier 1 changes nothing;
the escalation route for MedIT GPT is TO BE CONFIRMED (no contact exists in the repository).

### 11.1 "It says the model isn't found"

**Symptom.** A pop-up and a grey box reading `Model not found` right after pressing Send; or, in a
task, `Model '' was not found`.

**Likely causes, in order.**
1. The user has no access to that model (or to the base model it is built on); the code reports
   refused access with the same text (`backend/open_webui/utils/models.py:465-521`).
2. The model was removed or renamed at the provider, or its connection is down, so it is no longer
   in the server's model list (`backend/open_webui/main.py:1128-1129`).
3. A custom workspace model whose base model disappeared (`backend/open_webui/main.py:1180-1182`).
4. The chat was opened from an old link and still has a model selected that no longer exists.

**Diagnostic steps.** Ask whether other models work and whether colleagues see the same model in
their model list. Check whether the model appears in the user's model picker after a page reload.
An administrator can confirm the model's sharing in Workspace > Models and look for
`Model access denied: ... reason=...` in the server log (`backend/open_webui/utils/models.py:475-513`).

**Resolution.** Ask the user to choose another available model, or reload the page to refresh the
model list. Model access is changed only by an administrator.

**Escalation.** Send the chat id, model name, the user's role and group (no other personal data), the
time, and whether other users are affected.

### 11.2 "The response just stops halfway"

**Symptom.** Text stops arriving mid-answer; sometimes a grey error box appears, sometimes nothing.

**Likely causes, in order.**
1. The provider connection dropped or hit a time limit (`AIOHTTP_CLIENT_TIMEOUT`,
   `AIOHTTP_CLIENT_STREAM_IDLE_TIMEOUT`) and the error box shows the error text
   (`backend/open_webui/env.py:608-625`; `backend/open_webui/main.py:1686-1713`).
2. The provider sent an error part-way (quota, content filter): pop-up plus
   `Uh-oh! There was an issue with the response.` (`backend/open_webui/utils/middleware.py:5226-5249`).
3. Several server workers without the Redis websocket manager: the reply continues on the server
   but the browser stops receiving it; reloading shows the finished answer
   (`backend/open_webui/socket/main.py:1150-1161`).
4. A stream filter is failing, so remaining chunks are silently dropped
   (`backend/open_webui/utils/middleware.py:5098-5109`, `:5725-5733`).
5. The model hit its own length limit (`max_tokens`) and simply finished (no error).
6. Someone pressed Stop, or Escape was pressed in the composer (`src/lib/components/chat/MessageInput.svelte:2117-2119`).

**Diagnostic steps.** Ask the user to reload the chat. If the full answer now appears, suspect
cause 3; if the text vanishes and only an error remains, suspect cause 1 (partial text from failed
replies is not saved, `backend/open_webui/utils/middleware.py:4939-4961`, `:6552-6563`). Note any
error text. Ask whether it happens with every model or one model.

**Resolution.** Suggest regenerating the reply, asking for a shorter answer, or switching model.

**Escalation.** Chat id, model, time, error text, whether the answer appeared after reload. Mention
if many users report it at once (provider or worker issue).

### 11.3 "My chat never got a title"

**Symptom.** The chat stays `New Chat`, or is named after the full text of the first message.

**Likely causes, in order.**
1. **Title Generation** is off for the site, or the user's **Title Auto-Generation** is off; the
   code then names the chat after the first message (`backend/open_webui/utils/middleware.py:3990-4000`).
2. The title task failed (the Task Model is unreachable or not readable by ordinary users, or it
   answered without the expected JSON); the fallback is the first message (when the model call
   itself failed, only while the chat holds just its first exchange)
   (`backend/open_webui/utils/middleware.py:3957-3979`, `:3990-4000`; section 5.11).
3. The chat was started with several models side by side and no title was produced: the fallback
   does not apply, so it stays `New Chat` (`backend/open_webui/utils/middleware.py:3990`; section 14).
4. It is a temporary chat, which never gets a title (`backend/open_webui/utils/middleware.py:3939`).
5. The chat was started from an API script without `background_tasks`.
6. The title task **raised** (the chat's model had dropped out of the model list, or a Pipelines
   filter rejected the task call): no fallback is applied, so the chat stays `New Chat`, and the
   server log shows `Error generating initial chat title` followed by that error
   (`backend/open_webui/main.py:1486-1490`; section 5.7).
7. The sidebar shows the first message as the title but the chat header still reads `New Chat`:
   the fallback's `chat:title` event carried the reply's text instead of the saved title, and the
   header follows that event until the chat is reopened (section 5.12).

**Diagnostic steps.** Ask whether the user is in a temporary chat, whether several models were
selected, and whether **Title Auto-Generation** is on in their Settings > Interface. Check whether
other users' new chats get titles (site-wide cause) and whether an admin's do (access cause,
section 11.9). For cause 6, an administrator can search the server log at the chat's creation time
for `Error generating initial chat title` and read the exception under it; `KeyError: 'model'` on
its own is expected after every new chat (as written) and is not the cause (section 10.5).

**Resolution.** The user can rename the chat, or use **Generate** in the sidebar rename field to
try again (`src/lib/components/layout/Sidebar/ChatItem.svelte:440-511`). Switching their own
setting on is the user's choice.

**Escalation.** If no user gets generated titles: time, an example chat id, and the observation
that titles equal the first message (or stay `New Chat`). Administrators check Admin Settings >
Interface (Title Generation, Task Model) and, for chats left at `New Chat`, the server log (cause 6).

### 11.4 "I pressed Send and nothing happens until I refresh"

**Symptom.** The message is sent and a reply placeholder appears, but no text streams; after a
reload the answer is there (or the reply is empty).

**Likely causes, in order.**
1. The browser's websocket is not connected to the worker that runs the reply (several workers
   without `WEBSOCKET_MANAGER=redis`, or a proxy blocking websockets)
   (`backend/open_webui/socket/main.py:1150-1161`).
2. A very slow model or long preparation (web search, retrieval, many tools) with status lines
   hidden by **Hide Processing Details** (section 12).
3. The reply is paused waiting for a tool approval that is scrolled out of view.

**Diagnostic steps.** Ask whether status lines appeared, whether the problem affects every chat,
and whether it started after an infrastructure change. Ask the user to reload once and report
whether the answer is then present.

**Resolution.** Reloading shows the saved answer. If the answer is missing after reload, see
section 11.14.

**Escalation.** Platform maintainer, with times and chat ids from several users: this usually points
to deployment configuration (`websockets-realtime-and-redis.md`).

### 11.5 "I pressed Stop but it kept going"

**Symptom.** The reply stops on screen but the full answer appears later; or Stop does nothing.

**Likely causes, in order.**
1. Several server workers without Redis: the Stop request reached a worker that was not running
   the reply (`backend/open_webui/tasks.py:181-196`, `:296-302`; section 5.9).
2. Redis is configured but its command listener is failing (log `Redis task command listener
   failed. Retrying: ...`) (`backend/open_webui/tasks.py:28-66`).
3. What kept going was the title job of a new chat or a background sub-agent, which Stop does not
   cancel (`backend/open_webui/main.py:1486-1492`; `backend/open_webui/utils/subagents.py:665-670`).

**Diagnostic steps.** Ask whether the full answer appeared after a reload, and whether a sub-agent
was running. Note the time of the Stop.

**Resolution.** Explain that the answer may still complete; the user can delete the unwanted reply.
Archiving or deleting the chat also stops its tasks (`backend/open_webui/routers/chats.py:1593-1601`,
`:1920-1923`).

**Escalation.** Platform maintainer with the time, chat id and whether the answer completed; ask them
to check whether Redis is configured for a multi-worker deployment (TO BE CONFIRMED for production).

### 11.6 "It says 'Uh-oh! There was an issue with the response.'"

**Symptom.** A pop-up, and the grey box reads `Uh-oh! There was an issue with the response.`
followed by a second line.

**Likely causes, in order.**
1. The provider rejected the request part-way; the second line is the provider's own message
   (quota, rate limit, content policy, context too long) (`src/lib/components/chat/Chat.svelte:3716-3756`).
2. The send request failed with an error that was not plain text (pop-up only)
   (`src/lib/components/chat/Chat.svelte:3643-3668`).

**Diagnostic steps.** Read the second line. "Context length" wording suggests the chat is too long
(context compaction off or ineffective); quota or rate-limit wording suggests a provider limit.

**Resolution.** Retry later, shorten the request, start a new chat for very long conversations, or
try another model.

**Escalation.** Send the full error text, model, time and chat id; repeated quota or rate-limit
errors across users go to the platform maintainer.

### 11.7 "It says 'Open WebUI: Server Connection Error'"

**Symptom.** The grey box shows `Open WebUI: Server Connection Error`.

**Likely causes, in order.** The model provider is unreachable from the server (outage, network,
expired certificate, wrong address), or a provider request timed out before answering
(`backend/open_webui/routers/openai.py:1745-1751`).

**Diagnostic steps.** Check whether every model from the same connection fails and whether other
users are affected.

**Resolution.** Suggest a model from another connection, if available.

**Escalation.** Platform maintainer: connection name or model, time, affected users. Connection
troubleshooting is in `model-connections-openai-ollama-and-direct.md`.

### 11.8 "I don't get suggested follow-up questions"

**Symptom.** No follow-up suggestions under answers (or chats never get tags).

**Likely causes, in order.**
1. The user's **Follow-Up Auto-Generation** (or **Chat Tags Auto-Generation**) is off
   (`src/lib/components/chat/Chat.svelte:3628-3640`).
2. The site switch (**Follow Up Generation** / **Tags Generation**) is off
   (`backend/open_webui/routers/tasks.py:216-220`, `:281-285`).
3. The Task Model failed or answered without JSON, so nothing is shown
   (`backend/open_webui/utils/middleware.py:3911-3937`).
4. The reply was stopped or failed; tasks run only after a completed reply (section 5.9).
5. Tags are generated only for a chat's first exchange (`src/lib/components/chat/Chat.svelte:3628-3638`).
6. The follow-up task raised (the chat's model had dropped out of the model list, or a Pipelines
   filter rejected the task call); tags and the memory review are then skipped too, and on a
   streaming reply a grey error box appears under the answer
   (`backend/open_webui/utils/middleware.py:3889-3899`; section 11.20).

**Diagnostic steps.** Ask the user to check their Settings > Interface switches, then compare with
another user and with an admin.

**Resolution.** The user can turn their own switch on. Site switches are admin-only.

**Escalation.** If nobody gets follow-ups: time and example chat id for the platform maintainer.

### 11.9 "Titles and suggestions work for my admin but not for me"

**Symptom.** Admins get titles, tags and follow-ups; ordinary users get first-message titles and no
suggestions.

**Likely cause.** The configured Local or External Task Model is not shared with ordinary users.
Background tasks run with the user's own model access, and admins bypass access checks by default
(`backend/open_webui/utils/chat.py:198-203`; ground truth: admin visibility defaults). The admin
panel warns about this: `This model is not publicly available. Please select another model.`
(`src/lib/components/admin/Settings/Interface.svelte:103-110`).

**Diagnostic steps.** Confirm the user is role `user` and that an admin's chats get titles.

**Resolution.** None at tier 1.

**Escalation.** Administrator: share the task model with all users, or choose a public one.

### 11.10 "It said 'Compacting context' and now the assistant forgot what we discussed"

**Symptom.** Pop-ups `Compacting context` and `Context compacted`; afterwards the assistant misses
earlier details. Or `Context compaction failed` and then an error about the request being too long.

**Likely causes, in order.**
1. Compaction replaced older messages with a summary that left the detail out; this is the designed
   behaviour once a chat passes the threshold (section 5.13).
2. The summary model failed and the full, over-long history was sent instead
   (`backend/open_webui/utils/middleware.py:2512-2513`).

**Diagnostic steps.** Ask the user to run `/status` and report the context usage percentage.

**Resolution.** Remind the user to restate key facts, or start a new chat for a new topic. The
earlier messages are still visible to the user even though the model now sees a summary.

**Escalation.** Only if compaction fails repeatedly: chat id, time, model.

### 11.11 "It says 'Tool-call limit reached'"

**Symptom.** The grey box shows `Tool-call limit reached ({max_tool_call_iterations} iterations).`

**Likely causes.** The model kept calling tools (search, knowledge, code) without finishing; the
limit is 256 rounds by default, 30 for sub-agents (`backend/open_webui/utils/middleware.py:5830-5835`,
`:6339-6346`; `backend/open_webui/env.py:1082-1098`).

**Diagnostic steps.** Ask what the user asked for and which tools were on.

**Resolution.** Rephrase into smaller steps, turn off tools that are not needed, or try another
model.

**Escalation.** Chat id and model if it recurs with simple requests.

### 11.12 "I turned on web search but it didn't search"

**Symptom.** Web search was on, but no "Searching the web" status appears and no web citations.

**Likely causes, in order.**
1. In the default **native** function-calling mode the model decides whether to call the web search
   tool; it may answer without searching (`backend/open_webui/utils/middleware.py:2700-2709`;
   `backend/open_webui/utils/tools.py:677-685`).
2. The model does not have the web search capability or the web search built-in tool is off for it.
3. The user lacks the `features.web_search` permission or web search is off site-wide
   (`backend/open_webui/utils/middleware.py:2700-2706`).
4. Status lines are hidden by **Hide Processing Details** (section 12).

**Diagnostic steps.** Ask whether citations or a search status appear on any answer, and whether
the request clearly needed current information.

**Resolution.** Ask the user to say explicitly "search the web for ...". Detailed search behaviour is
in `web-search-and-web-loading.md`.

**Escalation.** If no searches happen for anyone: model name and time.

### 11.13 "The assistant ignores my knowledge base or attached files"

**Symptom.** Answers do not use the attached documents; the status says `No sources found`, or there
is no retrieval status at all.

**Likely causes, in order.**
1. Retrieval found nothing relevant, or retrieval failed (both show `No sources found`)
   (`backend/open_webui/utils/middleware.py:2105-2165`).
2. In native mode, knowledge attached to a model is reached only through the model's own knowledge
   tool calls; the model may not call them, and if built-in tools are off for that model the
   knowledge is not used (`backend/open_webui/utils/middleware.py:2604-2644`, `:2809-2813`,
   `:3104-3123`).
3. The model's **file context** capability is off, so attached files are not retrieved into the
   prompt (`backend/open_webui/utils/middleware.py:3206-3214`).
4. The file has not finished processing (see `files-uploads-and-storage.md`).

**Diagnostic steps.** Ask which status lines appear and whether the file shows as processed.

**Resolution.** Ask the user to reference the document explicitly, wait for processing, or re-attach
the file.

**Escalation.** Chat id, file name (not its contents), model and time; see
`rag-retrieval-embeddings-and-vector-stores.md`.

### 11.14 "My answer disappeared when I reloaded the page"

**Symptom.** Text was visible, but after a reload the reply is empty or shows only an error.

**Likely causes, in order.**
1. The reply failed mid-stream: the error is saved but the partial text is not
   (`backend/open_webui/main.py:1686-1713`; section 5.8).
2. The server restarted (for example a deployment) while the reply was running; with no task left,
   the browser marks the unfinished reply as done and empty (`src/lib/components/chat/Chat.svelte:2374-2410`).
3. With several workers and no Redis, the reload asked a worker that did not know about the running
   reply (section 5.9).

**Diagnostic steps.** Ask whether an error box is shown after reload, and the time.

**Resolution.** Regenerate the reply.

**Escalation.** If it coincides with maintenance or affects many users at once, send times and chat
ids to the platform maintainer.

### 11.15 "I can't fork this chat"

**Symptom.** `/fork` or **Fork chat** shows `Access prohibited`,
`Wait for the current response to finish before forking.`, `No chat to fork` or
`Failed to fork chat`; or the Fork chat button is missing.

**Likely causes, in order.** Missing `chat.import` permission; a reply still running (or appearing to,
with several workers and no Redis); an unsaved or empty chat; a server error
(`src/lib/components/chat/Chat.svelte:3046-3089`; `backend/open_webui/routers/chats.py:1681-1699`).

**Diagnostic steps.** Ask whether the reply has finished and whether it is a temporary chat.

**Resolution.** Wait for the reply to finish, then retry. Permissions are an administrator decision.

**Escalation.** Chat id and exact message.

### 11.16 "Autocomplete suggestions don't appear while I type"

**Likely causes, in order.** Autocomplete is off site-wide (default); the user's **Prompt
Autocompletion** is off (the switch only appears when the site switch is on); the draft is longer
than the configured maximum; the task model failed (errors are silent)
(`backend/open_webui/routers/tasks.py:479-553`; `src/lib/components/chat/MessageInput.svelte:2081-2102`).

**Diagnostic steps.** Ask whether the **Prompt Autocompletion** switch exists in the user's
Settings > Interface.

**Resolution.** If the switch exists, the user can turn it on. Otherwise explain it is not enabled.

**Escalation.** Not normally needed.

### 11.17 "The reply is waiting for my approval and won't go away"

**Symptom.** A tool approval card stays, or clicking it shows `Tool call has already been resolved.`

**Likely causes, in order.** The call was already approved or rejected in another tab or by a
double click; the page shows stale state; the user wants to abandon it
(`backend/open_webui/utils/tool_approval.py:55-58`).

**Resolution.** Reload the chat. To abandon the paused reply, press Stop: pending calls are rejected
and the reply is closed (`backend/open_webui/main.py:2174-2214`).

**Escalation.** Chat id and exact message if reloading does not clear it.

### 11.18 "It says 'Failed to connect to MCP server'"

**Symptom.** The grey box shows `Failed to connect to MCP server '{server_id}'` but an answer still
follows, without that tool's help.

**Likely causes.** The tool server is down, its sign-in has expired, or the user lacks access
(`backend/open_webui/utils/middleware.py:2340-2388`, `:3005-3014`).

**Resolution.** Retry later or deselect the tool; reconnect the integration if the composer offers
it.

**Escalation.** Server id from the message, time, and whether other users are affected; see
`workspace-tools-tool-servers-mcp-and-terminals.md`.

### 11.19 "An admin saved the task settings but they didn't change"

**Symptom.** `Settings saved successfully!` appeared in Admin Settings > Interface, but titles,
prompts or compaction behave as before.

**Likely causes, in order.** The save failed after the success message was already shown (the panel
does not wait for the server) (`src/lib/components/admin/Settings/Interface.svelte:164-170`;
`src/lib/components/chat/SettingsModal.svelte:880-884`); or the change works but only for new
chats (titles and tags run only for a chat's first exchange).

**Diagnostic steps.** Ask the admin to close and reopen the panel and check the value.

**Escalation.** If the value reverts, the platform maintainer checks the server log for the
`/api/v1/tasks/config/update` or `/api/v1/chats/config` request.

### 11.20 "There's an error box under an answer that looks complete"

**Symptom.** The answer finished normally, but a grey error box sits under it, often reading
`Model '' was not found` or a message from a filter, and it is still there after a reload. No
follow-up suggestions appear, and a new chat may get no tags.

**Likely causes, in order.**
1. A background task (follow-ups, then tags) raised after the answer had been saved, because the
   chat's model was not in the server's model list at that moment: for example the model was
   removed, or an administrator saved the OpenAI-compatible connection settings while the reply
   ran, which empties the list until it is rebuilt (`backend/open_webui/routers/tasks.py:230-235`,
   `:295-300`; `backend/open_webui/utils/models.py:445-460`;
   `backend/open_webui/routers/openai.py:346-357`, `:577`). The reply's error handler
   then saves the error beside the answer (`backend/open_webui/main.py:1686-1713`; section 5.7).
2. A Pipelines filter rejected the task call (task calls pass through Pipelines inlet filters like
   any other request); the box then shows the Pipelines server's message
   (`backend/open_webui/routers/tasks.py:196-200`, `:262-265`, `:327-330`;
   `backend/open_webui/routers/pipelines.py:104-122`). Whether MedIT GPT uses a Pipelines server
   with filters is TO BE CONFIRMED.
3. Not a background task at all: the provider or a tool step failed at the end of the reply. The box
   then reads `Uh-oh! There was an issue with the response.` or shows a tool-related error, and the
   answer may stop abruptly (sections 5.6, 11.2 and 11.6).

**Diagnostic steps.** Ask whether the answer reads as complete and whether the box appeared only
after it finished. Note the exact error text and the time. Check whether other users see the same
box at the same time (site-wide cause) and whether it recurs in a new chat with the same model. An
administrator can find `Error processing chat payload: %s` with the same text in the server log at
that time (`backend/open_webui/main.py:1688`).

**Resolution.** Tell the user the answer itself is complete and usable: the box reports a failure of
the extra steps that run after it (suggestions, tags), and the answer is still part of the
conversation the model sees on the next turn (`backend/open_webui/utils/middleware.py:2240-2242`).
Regenerating the reply later gives a fresh reply without the box once the cause has cleared.

**Escalation.** Platform maintainer: chat id, model, time, the exact error text, and whether several
users are affected. Repeated `Model '' was not found` points at the model list (connections, model
availability); a filter message points at the Pipelines configuration.

### 11.21 "A webhook says my chat failed but the answer looks fine"

**Symptom.** A webhook or notification headed `Chat failed` (an admin webhook adds the chat id in
brackets), with an error text and a link to the chat, but the chat shows a normal, complete answer
and no error box. The usual notice for the finished reply, headed with the chat's title, may have
arrived just before it (`backend/open_webui/events.py:1042-1044`;
`backend/open_webui/utils/notifications.py:264-305`).

**Likely causes, in order.**
1. Streaming is switched off for that model, chat or user (**Stream Chat Response**), and a
   background task raised after the answer was delivered. On the non-streaming path that failure
   publishes `chat.failed` and changes nothing on screen
   (`src/lib/components/chat/Chat.svelte:3488-3492`; `backend/open_webui/utils/middleware.py:4377`,
   `:4385-4409`; section 5.7). The error text is usually `Model '' was not found` or a Pipelines
   filter message (section 11.20, causes 1 and 2).
2. A genuine error while a non-streaming reply was being processed or saved; the answer may then
   be missing after a reload (`backend/open_webui/utils/middleware.py:4257-4375`; section 11.14).

**Diagnostic steps.** Open the linked chat and confirm the answer is complete. Ask whether this
model's answers appear all at once rather than word by word (a sign that streaming is off). Note the
time and the error text in the notification. An administrator with debug logging on can find
`Error occurred while processing request: %s` at that time
(`backend/open_webui/utils/middleware.py:4389`).

**Resolution.** Tell the user the answer is complete; the notification reports a failure of the
extra steps that run after the answer. How webhooks and notification targets are set up is
described in `notifications-webhooks-events-and-banners.md`.

**Escalation.** Platform maintainer: chat id, model, time, the notification's error text, and how
often it happens. The same cause on a streaming reply shows an error box instead (section 11.20)
and sends no `Chat failed` notification.

## 12. Local Customisations

**The pipeline itself matches upstream Open WebUI v0.11.4.** `git diff main...uoft` and
`git diff` (working tree) show no change in any file in this area's scope: `backend/open_webui/main.py`,
`backend/open_webui/utils/{middleware,chat,payload,response,misc,task,context_compaction,chat_variables,chat_fork,subagents}.py`,
`backend/open_webui/routers/tasks.py`, `backend/open_webui/tasks.py`, `backend/open_webui/constants.py`,
`src/lib/components/admin/Settings/Subagents.svelte` and `src/lib/components/admin/Settings/Interface.svelte`.

Fork and working-tree changes in neighbouring files change what users **see** of this pipeline:

| Change | Where | Effect on this area | Status |
|---|---|---|---|
| Per-user **Hide Processing Details** (`hideProcessingDetails`) | `src/lib/components/chat/Messages/ResponseMessage.svelte:197-221`, `:720-722`, `:920-921`, `:944`; `src/lib/components/chat/MessageInput.svelte:1792` | Hides the status lines of section 10.2, code-execution panels and the composer task list, showing `Thinking...` until answer text arrives (not while a tool approval waits on the user). Tier 1 should ask whether this setting is on before concluding that "no search happened" or "nothing is happening" | Fork commit on `uoft`, refined by uncommitted working-tree edits |
| Browser notification title uses the site name | `src/routes/+layout.svelte:760` | "Reply finished" browser notifications read `{title} / {WEBUI_NAME}` (MedIT GPT by default) instead of `/ Open WebUI` | Fork commit |
| Resumed tool approvals re-open the reply | `src/lib/components/chat/Chat.svelte:2847-2850` | After an approval, a `chat:completion` with `done: false` marks the reply as running again, so the Stop button and progress indicator return | Uncommitted working-tree edit |

The setting's own wording is in `src/lib/i18n/locales/en-US/translation.json` under
`settings.personal.interface.hideProcessingDetails.*` (also edited in the working tree); it is
documented in `user-settings-and-personalisation.md`.

No configuration default, prompt template, task, compaction or sub-agent behaviour is customized
for MedIT GPT in the repository. Whether production overrides any of the section 7 defaults is
data, TO BE CONFIRMED.

## 13. Source File Index

### 13.1 In Scope (Read in Full or by Section)

| File | What it holds |
|---|---|
| `backend/open_webui/main.py` | `/api/chat/completions` (`:1097-1890`), resolve (`:1893-1910`), `/api/chat/completed` (`:2071-2107`), actions (`:2110-2125`), `/api/tasks*` (`:2128-2214`); Redis listener start-up (`:390-395`); Anthropic-compatible endpoint (`:1925-2068`) |
| `backend/open_webui/utils/middleware.py` | Prompt building (`process_chat_payload`, `:2391-3276`), legacy tools (`:1334-1557`), web search (`:1560-1730`), image generation (`:1828-2046`), retrieval (`:2049-2167`), tool approval drain and pause (`:3412-3655`), background tasks (`:3832-4047`), outlet filters (`:4050-4208`), non-streaming and streaming handlers (`:4211-6717`) |
| `backend/open_webui/utils/chat.py` | Provider routing, direct connections, arena, deprecated `chat_completed` |
| `backend/open_webui/utils/payload.py` | System prompt rendering, parameter application, OpenAI-to-Ollama conversion |
| `backend/open_webui/utils/response.py` | Usage normalization and merging, Ollama response conversion |
| `backend/open_webui/utils/misc.py` | Message-list helpers, output-to-message conversion, provider error detail, stream line handling (read `:1-830`, `:1226-1318`) |
| `backend/open_webui/utils/task.py` | Task model choice, prompt placeholders, task templates |
| `backend/open_webui/routers/tasks.py` | Task settings endpoints and the eight task endpoints |
| `backend/open_webui/tasks.py` | Task registry, stop, Redis listener and heartbeat, in-progress text store |
| `backend/open_webui/utils/context_compaction.py` | Automatic and manual compaction, context usage estimate |
| `backend/open_webui/utils/chat_variables.py` | Chat and user variable parsing, validation, rendering |
| `backend/open_webui/utils/chat_fork.py` | Branch copy for forks |
| `backend/open_webui/utils/subagents.py` | Sub-agent delegation, background completion, pending internal messages |
| `backend/open_webui/constants.py` | `TASKS` list and `ERROR_MESSAGES` texts |
| `src/lib/components/admin/Settings/Subagents.svelte` | Sub-agents admin panel |
| `src/lib/components/admin/Settings/Interface.svelte` | Task, chat (compaction, tool permissions) and generation settings |

### 13.2 Read for Context (Owned by Other Areas)

| File | Why |
|---|---|
| `backend/open_webui/config.py` (`:2036-2042`, `:2176-2460`, `:3100-3160`) | Defaults and prompt templates for the keys in section 7 |
| `backend/open_webui/env.py` (`:369-397`, `:534-542`, `:608-625`, `:1028-1116`, `:1186`) | Environment-only settings |
| `backend/open_webui/routers/chats.py` (`:51-85`, `:129-139`, `:160-238`, `:836-856`, `:1271-1343`, `:1579-1601`, `:1660-1772`, `:1910-1925`) | Chat config, compaction and fork endpoints, response-stream overlay, task stops on delete and archive |
| `backend/open_webui/routers/configs.py` (`:69-76`, `:773-804`) | Sub-agent settings endpoints |
| `backend/open_webui/utils/tool_approval.py` | Resolve endpoint logic |
| `backend/open_webui/utils/actions.py` | Action endpoint logic |
| `backend/open_webui/utils/filter.py` (`:140-250`) | Filter error behaviour |
| `backend/open_webui/utils/models.py` (`:30-60`, `:180-248`, `:443-460`, `:465-560`) | Model access check, connection types, replacement of the in-memory model list |
| `backend/open_webui/utils/tools.py` (`:538-800`) | Built-in tool gating, sub-agent tools |
| `backend/open_webui/tools/builtin.py` (`:1680-1740`) | `delegate_task` and `timer` entry points |
| `backend/open_webui/utils/memory.py` (`:410-471`) | Memory review after a turn and how its failures are logged |
| `backend/open_webui/utils/chat_id.py` | Saved, temporary and channel chat ids |
| `backend/open_webui/utils/session_pool.py` (`:30-140`) | Provider timeouts, stream wrapper |
| `backend/open_webui/socket/main.py` (`:1134-1289`) | Event emitter and caller |
| `backend/open_webui/routers/openai.py` (`:346-357`, `:557-577`, `:1487-1752`), `backend/open_webui/routers/ollama.py` (`:97-200`, `:1100-1135`) | Provider calls and their errors; model-list reset when connection settings are saved |
| `backend/open_webui/routers/pipelines.py` (`:60-135`) | Pipeline inlet filter errors |
| `backend/open_webui/models/chats.py` (`:132-153`, `:591-600`, `:865-890`, `:977-999`, `:1141-1264`) | Chat columns, internal child chats, tag replacement, message upsert (fields merged into the saved message) and status history |
| `backend/open_webui/models/chat_messages.py` (`:127-165`) | `chat_message` columns |
| `backend/open_webui/events.py` (`:155-220`, `:660-680`, `:1069-1202`) | Event names, notification routing and event sinks |
| `backend/open_webui/utils/notifications.py` (`:1-60`, `:255-320`) | Notification event names and how `chat.finished` and `chat.failed` are worded |
| `src/lib/components/chat/Chat.svelte` | Send, stop, event handling, compaction, fork, error display |
| `src/lib/components/chat/MessageInput.svelte` | Stop button, `/status` panel, autocomplete hook |
| `src/lib/components/chat/Navbar.svelte` (`:110-130`) | Chat header title |
| `src/lib/components/chat/Messages/ResponseMessage.svelte`, `.../Messages/Error.svelte`, `.../StatusHistory/StatusItem.svelte` | Error box, usage tooltip, status wording, Hide Processing Details |
| `src/lib/components/chat/SettingsModal.svelte` | Admin tab placement and the Interface save toast |
| `src/lib/components/common/InterfaceSettings.svelte` | Personal switches for titles, tags, follow-ups, autocomplete, emoji |
| `src/lib/components/chat/Settings/Advanced/AdvancedParams.svelte` | Stream, function calling and compaction threshold parameters |
| `src/lib/apis/index.ts`, `src/lib/apis/openai/index.ts`, `src/lib/apis/chats/index.ts`, `src/lib/apis/configs/index.ts` | Browser API clients and their error handling |
| `src/lib/utils/index.ts` (`:1219-1231`) | Browser prompt variables |
| `src/routes/+layout.svelte` (`:600-790`) | Direct connection relay, "reply finished" notifications |
| `src/routes/(app)/admin/settings/[tab]/+page.svelte` | Admin settings redirect |
| `src/lib/components/layout/Sidebar/ChatItem.svelte` (`:440-520`, `:628`, `:703-709`) | Sidebar title regeneration |
| `src/lib/components/chat/MessageInput/CallOverlay.svelte` (`:500-520`) | Emoji task caller |
| `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte` (`:115-150`) | Tool approval buttons |
| `src/lib/components/chat/Messages/MultiResponseMessages.svelte` | Merge Responses button |
| `src/lib/i18n/locales/en-US/translation.json` | English text for dotted keys |

## 14. Open Questions

Nothing found in the code contradicts `tools/ground-truth.md`. The items below could not be
established from the repository.

**Production data and deployment (TO BE CONFIRMED).**

1. Live values of every setting in section 7: the Local and External Task Models and their
   parameters, the title, tags, follow-up, query and autocomplete switches, any custom prompt
   templates, context compaction (on or off, threshold, cap, model), tool permissions and all
   sub-agent settings. These are rows in the `config` table.
2. The deployment shape: number of server workers and replicas, whether `REDIS_URL` is set, and
   whether `WEBSOCKET_MANAGER=redis` is used. These decide whether Stop, live streaming, the busy
   indicator and reload recovery work reliably (sections 5.5 and 5.9).
3. Environment values that change behaviour: `AIOHTTP_CLIENT_TIMEOUT` and
   `AIOHTTP_CLIENT_STREAM_IDLE_TIMEOUT` (unset means no limit, so "stops halfway" by timeout happens
   only if they are set), `CHAT_RESPONSE_MAX_TOOL_CALL_ITERATIONS`, `ENABLE_CUSTOM_MODEL_FALLBACK`,
   `BYPASS_MODEL_ACCESS_CONTROL`, `RAG_SYSTEM_CONTEXT`, `ENABLE_PLUGINS`, `REDIS_TASK_TTL`,
   `WEBSOCKET_EVENT_CALLER_TIMEOUT`.
4. Which providers and models production uses, and whether models have the **usage** capability
   switched on (without it, streaming replies from many OpenAI-compatible providers carry no token
   counts). The default of that capability in the model editor belongs to
   `workspace-models-and-model-access.md`.
5. Whether tier 1 has read access to admin settings and to server logs; the troubleshooting steps
   in section 11 assume an administrator does the checking.
6. The escalation contact for MedIT GPT (none exists in the repository).

**Behaviour inferred from code that should be confirmed by running the application.**

7. **Multi-model new chats** without a generated title appear to stay `New Chat`, because the
   fallback requires at most two messages in the chat and each side-by-side model adds a placeholder
   (`backend/open_webui/utils/middleware.py:3990`; `backend/open_webui/main.py:1373-1391`).
8. **Provider error chunk with a plain-text `error`**: the browser's error handler tests
   `'detail' in innerError`, which fails for a string (`src/lib/components/chat/Chat.svelte:3725`);
   what the user then sees mid-stream is not established. The server does save the error on the
   message (`backend/open_webui/utils/middleware.py:5078-5090`, `:5230-5240`).
9. **Plain-text HTTP error from an OpenAI-compatible provider** (non-JSON body, non-streaming): the
   provider route returns a plain-text response (`backend/open_webui/routers/openai.py:1735-1738`),
   but `process_chat` only treats JSON error responses as failures
   (`backend/open_webui/main.py:1664-1665`). The reply may be left unfinished with no error box.
10. **Send while the websocket is disconnected**: without a session id the server answers
    synchronously in the HTTP response (`backend/open_webui/main.py:1882-1885`), which the browser
    client does not expect for streams; the visible result is not established.
11. **Resuming a tool approval after a page reload** reuses the session id saved at pause time
    (`backend/open_webui/utils/tool_approval.py:180`); browser-side tools or Python on resume would
    then report `Client session disconnected.` This was not tested.
12. **The Interface panel success pop-up before the save completes** (section 7.3) was read from the
    code, not observed.
13. **`chat.failed` events** are published only for exceptions while processing non-streaming
    replies (`backend/open_webui/utils/middleware.py:4388-4409`). Whether upstream intends users'
    "chat failed" notifications to cover streaming failures is not documented; as written, most
    failures do not notify. Conversely, such an exception can come from a background task that
    raised after a successful non-streaming reply, so a `Chat failed` notification can follow the
    `chat.finished` notification for the same answer (section 5.7); this was read from the code,
    not observed.
14. **Usage of background tasks** (titles, tags, follow-ups, queries, autocomplete, emoji,
    compaction summaries) is not saved anywhere in this code; whether analytics or provider-side
    accounting captures it is for `evaluations-feedback-and-analytics.md` and the provider.
15. The admin-only `POST /api/tasks/stop/{task_id}` is the browser's fallback when a reply has task
    ids but no chat id (`src/lib/components/chat/Chat.svelte:3771-3778`); for ordinary users that
    call would be refused. How often a reply can be in that state is not established.
16. `ENABLE_REALTIME_CHAT_SAVE` is imported but not referenced (`backend/open_webui/utils/middleware.py:42`);
    a grep of `backend/open_webui` found no other use. Any operator documentation that relies on it
    is out of date for v0.11.4.
17. The 404 branch of `POST /api/tasks/stop/{task_id}` (`backend/open_webui/main.py:2133-2134`) is
    unreachable as written, because `stop_task` never raises `ValueError`; an unknown task id
    returns `{"status": false, "message": "Task with ID {task_id} not found."}` without Redis, and a
    success message with Redis whether or not any worker held the task
    (`backend/open_webui/tasks.py:259-293`).

**Personal data (handle with care; no detail withheld).**

18. User placeholders put names, email addresses and optional profile details into prompts sent to
    providers (section 5.17); the browser always sends the user's name and email as prompt
    variables (`src/lib/utils/index.ts:1219-1223`). Pipelines servers receive the user's id, name,
    email and role with filter calls (`backend/open_webui/routers/pipelines.py:64`, `:130`). Whether
    production provider and pipeline arrangements cover this is TO BE CONFIRMED.
19. Redis (when used) holds in-progress reply text for up to `REDIS_RESPONSE_STREAM_TTL` seconds;
    server debug logs of task calls include user email addresses
    (`backend/open_webui/routers/tasks.py:171`, `:239`, `:304`, `:363`, `:440`, `:516`, `:575`).
    Log retention is TO BE CONFIRMED (ground truth).

**Security-sensitive (not documented here).**

20. How the pipeline passes the user's single sign-on session token and internally issued tokens to
    tools, filters and sub-agents. Security-sensitive: refer to the platform maintainer and U of T
    Information Security (security.utoronto.ca).
21. How access checks apply to browser-supplied (direct connection) model definitions and to
    client-supplied request fields. Security-sensitive: refer to the platform maintainer and U of T
    Information Security (security.utoronto.ca).

**Background-task failures (added on review; read from the code, to be confirmed by running the
application).**

22. **`Error generating initial chat title` after every new chat.** The initial title job's context
    has no `model` entry (`backend/open_webui/main.py:1477-1484`), but once the title step is done
    the handler reads `ctx['model']` for the memory review
    (`backend/open_webui/utils/middleware.py:4038-4047`). The job is therefore expected to log this
    line with `KeyError: 'model'` for every new chat the server creates from the web interface
    (temporary and embedded chats excepted, `src/lib/components/chat/Chat.svelte:3305-3329`,
    `:3628-3638`), even when the title was saved. Confirm in the server log; if confirmed, it is an
    upstream defect for the platform maintainer to report, and meanwhile it makes genuine title
    failures harder to spot.
23. **A background task that raises after a streaming reply** saves an error on a complete, saved
    reply and shows the error box under it (`backend/open_webui/main.py:1686-1713`; section 5.7).
    Not reproduced; a test environment where the chat's model leaves the model list mid-reply, or a
    Pipelines filter rejects task calls, would confirm what the user sees.
24. **Text of the fallback `chat:title` event.** In the first-message fallback the event carries
    the reply's text rather than the saved title (`backend/open_webui/utils/middleware.py:3857`,
    `:3995-3999`). The effect on the chat header and browser tab described in section 5.12 was read
    from the code, not observed.
25. **Wording of `chat.failed` notifications.** The event's text is the exception's own text
    (`backend/open_webui/utils/middleware.py:4405`). For an HTTP error the web framework puts the
    status code first; in the locally installed Starlette 1.3.1 (a library, not repository code)
    it reads `{status_code}: {detail}`, for example `404: Model '' was not found`. The library
    version in production is TO BE CONFIRMED.
26. **Pipelines filters on task models.** Whether production uses a Pipelines server whose filters
    apply to the task models, and so can reject background task calls (sections 11.20 and 11.21),
    is TO BE CONFIRMED.
