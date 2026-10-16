# Built-In (Native) Tools

## At a Glance

- **What they are.** 53 Python functions shipped inside MedIT GPT
  (`backend/open_webui/tools/builtin.py`) that the model can call by itself while it answers: tell
  the time, search the web and read pages, search and read knowledge bases, chat files, notes,
  earlier chats, channels and memories, write notes and memories, keep a task checklist, create
  calendar events and automations, generate or edit images, run Python, send a webhook
  notification, ask the person a question, delegate to a sub-agent or set a timer (catalogue in
  section 4.3). They are not workspace tools (code pasted into Workspace › Tools) or tool servers
  (external OpenAPI or MCP services) (section 1.1).
- **When the model gets them.** Only for messages sent from the app (not plain API calls), with
  **Function Calling** not set to `Legacy` (native is the default) and the model's **Builtin
  Tools** capability on (default on). Each of sixteen groups can be switched off per model, and
  most families also need an admin feature switch, a permission and sometimes a model capability
  or the matching message-box toggle (section 3.2). With the code defaults, web search, images,
  channels, sub-agents and timers, automations (for non-admins) and notifications are off until an
  admin enables them; time, ask-user, knowledge, chat history, notes, calendar, memory and the
  task checklist are on, and the code interpreter when its toggle is used.
- **Data-changing tools.** 21 tools can create, change or delete data (section 4.4). Everything runs
  with **Full access** unless an admin switches on **Tool Permissions** and the person chooses
  **Ask for approval**, which pauses before every tool call (section 5.4). The model can also
  pause to ask one to three multiple-choice questions in a card above the message box (5.5).
- **What people see.** Each call is an entry such as `View Result from {{NAME}}` that opens to its
  input and output; a red cross marks an error (4.2, 5.6, 5.10). Replies stop after 256 rounds of
  tool calls with `Tool-call limit reached ({max_tool_call_iterations} iterations).` (5.10).
- **Local change.** The fork's personal setting **Hide Processing Details** hides tool entries
  (except approvals) and shows `Thinking...` instead; the back end matches upstream v0.11.4
  (section 12). Live values of every switch are TO BE CONFIRMED (section 14).

## 1. Purpose and Who Uses It

Built-in (native) tools are actions that the AI model can take by itself while it writes a reply:
look up the time, search the web, search the person's knowledge bases, files, notes, chats,
channels and memories, write a note, add a calendar event, schedule an automation, generate an
image, run code, ask the person a question, or hand part of the job to a helper ("sub-agent"). The
model decides when to call them; the person sees each call in the reply as an expandable entry.

The module that defines them says: "These tools are automatically available when native function
calling is enabled." (`backend/open_webui/tools/builtin.py:1-7`). Native function calling is the
default for every chat (`backend/open_webui/main.py:1290-1294`), so in practice the tools are on
unless a switch described in section 3 or 7 turns them off.

### 1.1 Built-In Tools Versus Workspace Tools and Tool Servers

| Kind | What it is | Who provides it | How it reaches the model | Source |
|---|---|---|---|---|
| **Built-in tool** (this document) | One of 53 Python functions shipped in `backend/open_webui/tools/builtin.py` (plus `kb_exec`, see below) | Part of MedIT GPT itself; cannot be edited in the interface | Added automatically by `get_builtin_tools` when the chat runs in native mode; each gets the id `builtin:<name>` and type `builtin` | `backend/open_webui/utils/tools.py:520-802`, `:795-800`; `backend/open_webui/utils/middleware.py:3096-3138` |
| **Workspace tool** | Python code a user or admin pastes into Workspace › Tools, stored in the `tool` table | Users with workspace tool permission, or admins | Only when selected for the chat or attached to the model, and only when plugins are enabled; access is checked per tool | `backend/open_webui/utils/tools.py:267-299`; `backend/open_webui/utils/middleware.py:3015-3029` |
| **Tool server** (OpenAPI or MCP) | An external service the admin or the person connects | Admin (Settings › Integrations) or the person (direct tool servers) | MCP and OpenAPI servers by tool id; direct servers are run by the browser | `backend/open_webui/utils/middleware.py:2962-3014`, `:3065-3084` |
| **Terminal tools** | Commands run on an Open Terminal server | Admin-configured terminal connection | When a terminal is selected and the model's Terminal capability is on | `backend/open_webui/utils/middleware.py:3034-3063` |

Workspace tools, tool servers and terminals are documented in
`workspace-tools-tool-servers-mcp-and-terminals.md`. Two practical consequences of the split:

- **A selected tool wins a name clash.** Built-in tools are added only under names not already
  taken by a selected workspace tool, MCP tool, terminal tool or direct tool server
  (`backend/open_webui/utils/middleware.py:3136-3138`).
- **Built-in tools are offered only to requests from the app** (the chat page, and automations,
  channel replies and timers, which carry their own session ids; section 3.1), not to plain API
  calls. The pipeline requires a session id; the source comment reads "API callers don't expect hidden tools; they can
  explicitly request tools via tool_ids." (`backend/open_webui/utils/middleware.py:2809-2813`,
  `:3096-3099`). A caller that sends its own `tools` list, even an empty one, also skips them
  (`:2945-2948`).

**`kb_exec`, the 54th built-in.** `kb_exec` (shell-style commands over knowledge bases) lives in
`backend/open_webui/tools/knowledge_fs.py` and is re-exported by `builtin.py`
(`backend/open_webui/tools/builtin.py:67`). It is off unless the environment variable
`ENABLE_KB_EXEC` is `true` (`backend/open_webui/env.py:968`); when on it replaces most knowledge
browsing tools (`backend/open_webui/utils/tools.py:607-620`). It is documented in
`knowledge-bases.md` section 5.23 and is not one of the 53 functions counted here.

### 1.2 Who Uses It

| Who | What they do in this area | Source |
|---|---|---|
| Every signed-in person who chats | Sees tool calls in replies; answers `ask_user` questions; approves or denies tool calls when Tool Permissions is on; chooses **Full access** or **Ask for approval** in the composer's **More** menu | `src/lib/components/chat/MessageInput/InputMenu.svelte:54-65`, `:146-185`, `:545-590`; `src/lib/components/chat/AskUserCard.svelte` |
| Model builders (workspace model editors and admins) | Switch the **Builtin Tools** capability and the sixteen built-in tool groups on or off for one model | `src/lib/components/workspace/Models/ModelEditor.svelte:1245-1269`; `src/lib/components/workspace/Models/BuiltinTools.svelte:11-77` |
| Admins | Switch whole features on or off (web search, images, code interpreter, memories, notes, channels, calendar, automations, user webhooks, sub-agents), set model defaults for every model, set user and group permissions, switch on **Tool Permissions** | sections 3 and 7 |
| Tier-1 support | Explains why a tool was or was not used, what a tool-call entry means, and how approval and questions work; escalates data-changing surprises | section 11 |

## 2. Navigation and URLs

Built-in tools have no page of their own. They show up inside chat replies and are controlled from
several settings screens. Admin settings URLs of the form `/admin/settings/<tab>` open the settings
view over the home page (`/?settings=admin:<tab>`) (`src/routes/(app)/admin/settings/[tab]/+page.svelte:5-9`).

### 2.1 Where People See and Control Built-In Tools

| Place | URL | What is there | Source |
|---|---|---|---|
| A chat | `/c/{id}` | Tool-call entries in replies (section 5.6), the **Allow**/**Deny** buttons (5.4), the question card for `ask_user` (5.5), the task list from `create_tasks` (5.9) | `src/lib/components/common/ToolCallDisplay.svelte`; `src/lib/components/chat/AskUserCard.svelte` |
| Composer **More** menu › **Tool Permissions** | in any chat | **Full access** or **Ask for approval**; shown only when an admin has switched Tool Permissions on | `src/lib/components/chat/MessageInput/InputMenu.svelte:54-65`, `:74`, `:146-185`, `:545-590` |
| Composer feature toggles (web search, image generation, code interpreter) | in any chat | Turning a toggle on is what lets the model have the matching built-in tools (section 3.2) | `src/lib/components/chat/Chat.svelte:3393-3416` |
| Settings › Personalization › **Memory** | personal settings | The person's memory switch (saved as `memory` in their settings) decides whether memory tools are offered | `src/lib/components/chat/Settings/Personalization.svelte:128-138`; `src/lib/i18n/locales/en-US/translation.json:3003`; `src/lib/components/chat/Chat.svelte:3412-3414` |
| Admin Settings › Interface › Chat › **Tool Permissions** | `/admin/settings/interface` | Site-wide switch that makes the approval modes available | `src/lib/components/admin/Settings/Interface.svelte:258-269` |
| Admin Settings › Models › **Model Defaults** › **Model Capabilities** | `/admin/settings/models` | Default capabilities (including **Builtin Tools**) and the default **Builtin Tools** groups for every model | `src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:186-221`; `src/lib/components/admin/Settings/Models.svelte:44`, `:774` |
| Admin Settings › **Sub-agents** | `/admin/settings/subagents` | Switch that offers `delegate_task` and `timer`, and sub-agent limits | `src/lib/components/admin/Settings/Subagents.svelte`; `src/lib/components/chat/SettingsModal.svelte:292-297` |
| Admin Settings › **General** | `/admin/settings/general` | Memories, Notes, Channels, Calendar, Automations and User Webhooks switches | `src/lib/components/admin/Settings/General.svelte:316-385` |
| Admin Settings › **Web Search** | `/admin/settings/web` | Web Search switch | `src/lib/components/admin/Settings/WebSearch.svelte:172-180` |
| Admin Settings › **Images** | `/admin/settings/images` | Image Generation and Image Edit switches | `src/lib/components/admin/Settings/Images.svelte:310-316`, `:731-738` |
| Admin Settings › **Code Execution** | `/admin/settings/code-execution` | Enable Code Interpreter switch | `src/lib/components/admin/Settings/CodeExecution.svelte:170-176` |
| Workspace › Models › edit a model | `/workspace/models/edit?id={id}` | **Capabilities** (including **Builtin Tools**) and, when that capability is on, the **Builtin Tools** groups | `src/lib/components/workspace/Models/ModelEditor.svelte:1245-1269` |
| Admin Panel › Users › **Groups** (default and group permissions) | `/admin/users/groups` | The `features.*` and `chat.file_upload` permissions that gate tool families; see `users-groups-roles-and-permissions.md` | `backend/open_webui/config.py:1938-2022` |

### 2.2 API Endpoints in This Area

| Method and path | Who | Purpose | Source |
|---|---|---|---|
| `POST /api/chat/completions` | Verified user | The chat request; built-in tools are resolved inside it | `backend/open_webui/main.py:1255-1296`; `backend/open_webui/utils/middleware.py:2809-3204` |
| `POST /api/v1/chats/{id}/messages/{message_id}/resolve` | Verified user who owns the chat, or an admin | Approve, reject or answer a paused tool call, then resume the reply | `backend/open_webui/main.py:1893-1910`; `backend/open_webui/utils/tool_approval.py:20-128` |
| `POST /api/tasks/chat/{chat_id}/stop` | Chat owner or admin | Stop the reply; when nothing is running, a reply paused for approval is closed and its pending calls are marked rejected | `backend/open_webui/main.py:2160-2214` |
| `GET /api/v1/chats/config`, `POST /api/v1/chats/config` | Admin | Read or save the Tool Permissions switch (`ENABLE_TOOL_PERMISSIONS`) with the other chat settings | `backend/open_webui/routers/chats.py:836-857`, `:58`, `:167` |
| `GET /api/config` | Any visitor; the feature fields are included only for a signed-in person | Tells the browser `enable_tool_permissions` and the feature switches | `backend/open_webui/main.py:2268-2276`, `:2342-2365`, `:2388-2389` |

There is no endpoint that lists or runs built-in tools directly; they run only inside a chat reply.

## 3. Roles and Permissions

Built-in tools act **as the person whose request is being answered** (the sender of the message,
or the owner of the automation or timer): they receive that person's account (`__user__`) and
read or change only what that person could reach through the interface, with a few differences
listed per tool in section 4.3 (`backend/open_webui/utils/tools.py:771-786`).
Admins pass every `features.*` and `chat.*` permission check in this area automatically
(`backend/open_webui/utils/tools.py:559-575`). There is no separate permission for "use built-in
tools" as a whole.

### 3.1 Conditions for Any Built-In Tool

All four must hold before any built-in tool is offered (`backend/open_webui/utils/middleware.py:2809-2813`,
`:2945-2948`, `:3099-3138`):

| # | Condition | Default | Where it is set | Source |
|---|---|---|---|---|
| 1 | The request comes with a session id: a browser chat, an automation run (`automation:{id}`), a channel reply (`channel:{id}`) or a timer run. A note's AI chat qualifies regardless | Chat page requests carry one; plain API calls do not | Not a setting | `backend/open_webui/utils/middleware.py:2809-2813`; `backend/open_webui/utils/automations.py:315`, `:488`; `backend/open_webui/utils/timers.py:388` |
| 2 | **Function Calling** is not `legacy` | `native` | Advanced parameters: the person's or the chat's, else the model's, else the admin's default (section 7.4) | `backend/open_webui/main.py:1170-1177`, `:1290-1294` |
| 3 | The model's **Builtin Tools** capability is on ("Automatically inject system tools in native function calling mode (e.g., timestamps, memory, chat history, notes, etc.)") | on | Workspace › Models (per model) or Admin Settings › Models › Model Defaults | `src/lib/constants.ts:115-128`; `src/lib/components/workspace/Models/Capabilities.svelte:57-60`; `src/lib/i18n/locales/en-US/translation.json:2573-2574` |
| 4 | The caller did not send its own `tools` list | Chat page sends none | Not a setting | `backend/open_webui/utils/middleware.py:2945-2948` |

### 3.2 Conditions per Tool Group

Each group has a **Builtin Tools** switch on the model (all default on) plus the conditions below.
"Composer toggle" means the person switched that feature on for the message (or the model turns it
on by default); "permission" means the `features.*` or `chat.*` permission from default or group
permissions (`backend/open_webui/config.py:1938-2022`).

| Group switch (model editor label) | Tools | Admin switch (persistent key, code default) | Model capability | Composer or personal switch | Permission (code default) | Other condition | Source |
|---|---|---|---|---|---|---|---|
| `time` (**Time & Calculation**) | `get_current_timestamp`, `calculate_timestamp` | none | none | none | none | none | `backend/open_webui/utils/tools.py:578-579` |
| `user_input` (**Ask User**) | `ask_user` | none | none | none | none | none | `backend/open_webui/utils/tools.py:581-582` |
| `files` (**Files**) | `list_chat_files`, `query_chat_files`, `grep_chat_files`, `view_file` | none | **File Upload** on **and File Context off** | none | `chat.file_upload` (on) | The chat has at least one uploaded file (web links and pasted data do not count) | `backend/open_webui/utils/tools.py:584-601` |
| `knowledge` (**Knowledge Base**) | Without attached knowledge: `list_knowledge_bases`, `search_knowledge_bases`, `query_knowledge_bases`, `grep_knowledge_files`, `search_knowledge_files`, `query_knowledge_files`, `view_knowledge_file`. With knowledge attached to the model, folder or (File Context off) chat: `list_knowledge`, `search_knowledge_files`, `grep_knowledge_files`, `query_knowledge_files`, plus `view_file` and `view_knowledge_file` for files or knowledge bases and `view_note` for notes | none | none | none | none (each tool checks read access itself) | `ENABLE_KB_EXEC` (environment, off) swaps in `kb_exec` | `backend/open_webui/utils/tools.py:603-642`; `knowledge-bases.md` 5.21-5.23 |
| `chats` (**Chat History**) | `search_chats`, `view_chat` | none | none | none | none | none | `backend/open_webui/utils/tools.py:645-646` |
| `subagents` (**Sub-agents**) | `delegate_task`, `timer` | `subagents.enable` (`ENABLE_SUBAGENTS`, **off**) | none | none | none | Not inside a sub-agent run; not a direct connection | `backend/open_webui/utils/tools.py:648-654`; `backend/open_webui/config.py:2036` |
| `memory` (**Memory**) | `search_memories`, `list_memory_paths`, `read_memory_path`, `list_memories`, `update_memory`, `add_memory`, `replace_memory_content`, `delete_memory` | `memories.enable` (`ENABLE_MEMORIES`, on) | **Memory** on | Personal **Memory** switch on (falls back to the site setting) | `features.memories` (on) | Inside a sub-agent run the four changing tools are removed | `backend/open_webui/utils/tools.py:656-675`, `:766-769`; `backend/open_webui/utils/subagents.py:34-39`; `src/lib/components/chat/Chat.svelte:3412-3414` |
| `web_search` (**Web Search**) | `search_web`, `fetch_url` | `web.search.enable` (`ENABLE_WEB_SEARCH`, **off**) | **Web Search** on | Web search toggle on for the message (or the person's "always" setting) | `features.web_search` (on) | none | `backend/open_webui/utils/tools.py:677-685`; `src/lib/components/chat/Chat.svelte:342-354` |
| `image_generation` (**Image Generation**) | `generate_image` | `image_generation.enable` (`ENABLE_IMAGE_GENERATION`, **off**) | **Image Generation** on | Image toggle on | `features.image_generation` (on) | none | `backend/open_webui/utils/tools.py:689-696` |
| same | `edit_image` | `images.edit.enable` (`ENABLE_IMAGE_EDIT`, **off**) | **Image Generation** on | Image toggle on | `features.image_generation` (on) | none | `backend/open_webui/utils/tools.py:697-704` |
| `code_interpreter` (**Code Interpreter**) | `execute_code` | `code_interpreter.enable` (`ENABLE_CODE_INTERPRETER`, on) | **Code Interpreter** on | Code interpreter toggle on | `features.code_interpreter` (on) | none | `backend/open_webui/utils/tools.py:706-715` |
| `notes` (**Notes**) | `search_notes`, `view_note`, `write_note`, `replace_note_content` | `notes.enable` (`ENABLE_NOTES`, on) | none | none | `features.notes` (on) | A note's own AI chat gets these four regardless of the switch, setting and permission | `backend/open_webui/utils/tools.py:717-721` |
| `channels` (**Channels**) | `search_channels`, `search_channel_messages`, `view_channel_thread`, `view_channel_message` | `channels.enable` (`ENABLE_CHANNELS`, **off**) | none | none | `features.channels` (on) | none | `backend/open_webui/utils/tools.py:723-732` |
| (no switch) | `view_skill` | none | none | none | none | At least one skill the person can use is listed for the model to load on demand | `backend/open_webui/utils/tools.py:734-736`; `backend/open_webui/utils/middleware.py:2830-2854` |
| `tasks` (**Task Management**) | `create_tasks`, `update_task` | none | none | none | none | The chat is saved (not a temporary or channel chat) | `backend/open_webui/utils/tools.py:738-741` |
| `automations` (**Automations**) | `create_automation`, `update_automation`, `list_automations`, `toggle_automation`, `delete_automation` | `automations.enable` (`ENABLE_AUTOMATIONS`, on) | none | none | `features.automations` (**off**) | none | `backend/open_webui/utils/tools.py:743-751` |
| `calendar` (**Calendar**) | `search_calendar_events`, `create_calendar_event`, `update_calendar_event`, `delete_calendar_event` | `calendar.enable` (`ENABLE_CALENDAR`, on) | none | none | `features.calendar` (on) | none | `backend/open_webui/utils/tools.py:753-757` |
| `notifications` (**Notifications**) | `notify` | `ui.enable_user_webhooks` (`ENABLE_USER_WEBHOOKS`, **off**) | none | none | `features.webhooks` (**off**) | none | `backend/open_webui/utils/tools.py:759-764` |

Code defaults come from `backend/open_webui/config.py:424`, `:426`, `:1161`, `:1351`, `:1525`,
`:1904-1934`, `:2028-2050`, `:2100`. **The live values of every switch and permission are data in
the `config` table and are TO BE CONFIRMED for production** (`ground-truth.md`, Settings).

With the code defaults, a non-admin in a new deployment would be offered the time, ask-user, chat
history, knowledge, memory (if their memory switch is on), code interpreter (when toggled), notes,
calendar and task tools; web search, image, channel, sub-agent, automation and notification tools
need an admin to switch something on first. The **Files** tools appear only on models whose
**File Context** capability is switched off; with File Context on (the default) the chat's files
are read into the conversation before the answer instead (`src/lib/constants.ts:115-116`;
`backend/open_webui/utils/tools.py:594-601`; `backend/open_webui/utils/middleware.py:3206-3214`).

### 3.3 Who May Resolve Tool Calls and Choose the Approval Mode

| Action | Who | Source |
|---|---|---|
| Choose **Full access** or **Ask for approval** | Any person, but the menu entry appears only when the admin switch **Tool Permissions** (`chat.tool_permissions.enable`, `ENABLE_TOOL_PERMISSIONS`, code default off) is on | `src/lib/components/chat/MessageInput/InputMenu.svelte:74`, `:146-185`; `backend/open_webui/config.py:2196`, `:3138` |
| Approve, deny or answer a paused call | The chat's owner, or an admin; anyone else gets HTTP 401 with the `ACCESS_PROHIBITED` text | `backend/open_webui/utils/tool_approval.py:27-32` |
| Switch Tool Permissions on or off | Admins (`POST /api/v1/chats/config`) | `backend/open_webui/routers/chats.py:841-857` |

Automation runs and channel replies always run with **Full access**, whatever the person chose,
and so does every chat while the admin switch is off (`backend/open_webui/main.py:1255-1264`).
A fired timer's request carries no approval mode, so it also runs with full access
(`backend/open_webui/utils/timers.py:376-396`; `backend/open_webui/main.py:1255-1264`).

## 4. Key Concepts and Terminology

### 4.1 Glossary

| Term | Meaning | Source |
|---|---|---|
| **Native function calling** | The model receives a list of tool definitions and decides itself when to call one; the server runs the tool and calls the model again with the result. The default (`native`) | `backend/open_webui/main.py:1290-1294`; `backend/open_webui/utils/middleware.py:3189-3195` |
| **Legacy function calling** | The older mode in which the task model picks one tool before the answer. Built-in tools are not offered in legacy mode, except in a note's AI chat | `backend/open_webui/utils/middleware.py:2809-2813`, `:3196-3204` |
| **Builtin Tools capability** | Per-model switch (`capabilities.builtin_tools`, default on) that turns all built-in tools on or off for that model | `src/lib/constants.ts:115-128`; `backend/open_webui/utils/middleware.py:2812` |
| **Built-in tool group** | One of the sixteen switches under **Builtin Tools** in the model editor (stored as `meta.builtinTools.<group>`; a group that is not listed counts as on) | `src/lib/components/workspace/Models/BuiltinTools.svelte:11-90`; `backend/open_webui/utils/tools.py:536-540` |
| **Composer toggle** | The web search, image generation and code interpreter switches in the chat input; they are sent with the message as `features` | `src/lib/components/chat/Chat.svelte:3393-3416` |
| **Tool call** | A `function_call` item saved in the reply's output, with the tool name, its arguments (input) and a status | `backend/open_webui/utils/middleware.py:5916-5932` |
| **Tool result** | A `function_call_output` item holding the text returned to the model, plus any files or embeds for display | `backend/open_webui/utils/middleware.py:6122-6152` |
| **Tool approval mode** | `full` (**Full access**: tools run straight away) or `ask` (**Ask for approval**: the reply pauses before each tool call). Only selectable when the admin switch **Tool Permissions** is on | `backend/open_webui/main.py:1255-1264`; `src/lib/components/chat/MessageInput/InputMenu.svelte:54-65` |
| **Resolve** | Approving, denying or answering a paused tool call, which resumes the reply | `backend/open_webui/utils/tool_approval.py:20-128` |
| **Ask-user question** | The `ask_user` tool: the reply pauses and a card with one to three multiple-choice questions appears above the message box | `backend/open_webui/utils/ask_user.py:9-149`; `src/lib/components/chat/AskUserCard.svelte` |
| **Sub-agent** | A hidden helper chat started by `delegate_task`, running the same model and tools as the person; see `chat-completion-pipeline-and-generation-tasks.md` section 5.14 | `backend/open_webui/tools/builtin.py:1680-1718` |
| **Timer** | A one-shot reminder the model sets with `timer`: at the chosen time the stored prompt is sent back into the same chat | `backend/open_webui/utils/timers.py:69-168`, `:230-419` |
| **Internal chat** | A hidden chat the server creates for a sub-agent run or a timer (meta `internal: true`, type `subagent` or `timer`); hidden from chat lists and search | `backend/open_webui/utils/timers.py:144-155`; `backend/open_webui/utils/subagents.py:428-435`; `backend/open_webui/models/chats.py:2019` |
| **Attached knowledge** | Knowledge bases, files and notes attached to the model, to the chat's folder, or (when File Context is off) to the chat; it decides which knowledge tools are offered | `backend/open_webui/utils/tools.py:481-517` |
| **Task list** | A checklist the model keeps for a long request with `create_tasks` and `update_task`, saved on the chat and shown in the chat | `backend/open_webui/tools/builtin.py:3556-3697` |
| **Session id** | The id of the browser connection (or `automation:{id}`, `channel:{id}`, `timer:{chat}`) that marks a request as coming from the app rather than the API | `backend/open_webui/utils/middleware.py:2809-2813` |
| **`kb_exec`** | Optional shell-style knowledge tool, off by default; see section 1.1 | `backend/open_webui/env.py:968` |

### 4.2 What a Tool-Call Entry Shows

Each tool call appears in the reply as one line with an icon and a label; clicking it opens the
**Input** (the arguments the model sent) and, when finished, the **Output** (what the tool
returned) (`src/lib/components/common/ToolCallDisplay.svelte:199-370`). On narrow screens only the
tool's name is shown (`:238-239`). Several tool calls in a row are folded into one group line
reading **Exploring** (while any is running) or **Explored**, followed by the tool names with
counts, for example "Explored 2 search_web, fetch_url" (an invented example)
(`src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte:97-177`).

| State | Status in the saved output | Icon | Label (wide screens) | Source |
|---|---|---|---|---|
| Model is still writing the call | `in_progress` | Spinner | `Preparing {{NAME}}...` | `src/lib/components/common/ToolCallDisplay.svelte:150-156`, `:250-251` |
| Tool is running | `completed` without a result yet | Spinner | `Executing {{NAME}}...` | `:155`, `:252-253` |
| Waiting for approval (ask mode) | `pending` | Wrench | `Allow {{NAME}}?` with **Allow** and **Deny** buttons | `:144`, `:248-249`, `:258-276` |
| Waiting for an answer (`ask_user`) | `pending` | Wrench | `Input needed` | `:142-143`, `:246-247` |
| Finished | result present | Green tick | `View Result from {{NAME}}` | `:151-154`, `:226-229`, `:244-245` |
| Finished with an error | `failed`, or a result that looks like an error | Red cross | `View Result from {{NAME}}` | `:158`, `:222-225` |
| Denied | `rejected` | Red cross | `Denied {{NAME}}` | `:150`, `:218-221`, `:242-243` |

- **What counts as an error.** A result is flagged when its text starts with `error:`,
  `exception:`, `traceback` or `http error!` (any case), or when it is JSON with a non-empty
  `error`, a `status` of `error` or `failed`, or `success`/`ok` false with a message. The server
  uses the same rule to save the status `failed` (`backend/open_webui/utils/middleware.py:158-197`;
  `src/lib/components/common/ToolCallDisplay.svelte:94-135`).
- **Long outputs** show the first 10,000 characters and a button `Show all ({{COUNT}} characters)`
  (`src/lib/components/common/ToolCallDisplay.svelte:44`, `:344-362`).
- **Images** returned by a tool appear under the entry once it finishes (`:372-387`); web pages a
  tool asks to embed appear as frames when embeds are allowed (`:178-198`).
- **Sub-agent calls** are labelled `Sub-agent: "{task}"` or `Background sub-agent: "{task}"`
  (task cut to 60 characters) instead of `delegate_task`
  (`src/lib/components/chat/Messages/structuredOutput.ts:202-213`).
- **A pending `ask_user` call is not listed** among the reply's tool calls; its question card
  appears above the message box instead (`src/lib/components/chat/Messages/structuredOutput.ts:396-402`;
  `src/lib/components/chat/MessageInput.svelte:1774-1786`).
- The personal setting **Hide Processing Details** (a MedIT GPT addition) hides these entries;
  see section 5.6 and section 12.

### 4.3 Catalogue of the 53 Built-In Tools

One row per function in `backend/open_webui/tools/builtin.py`. **Group** is the model editor's
**Builtin Tools** switch that offers it; the full set of conditions per group is in section 3.2.
**Changes data** is "Yes" when the tool creates, changes or deletes something stored (including
files and settings rows), "External" when it only sends a request to an outside service, and "No"
when it only reads. Every tool returns text (often JSON) to the model; unless noted, a failure is
returned to the model as JSON `{"error": "<reason>"}` and the entry shows a red cross (section
4.2). The person sees each call's input and output in the reply.

#### Time, Web, Images, Questions, Code and Notifications

| # | Tool | Group | What it does, in plain language | Reads or changes | Changes data | Limits and notes | Source |
|---|---|---|---|---|---|---|---|
| 1 | `get_current_timestamp` | Time & Calculation | Tells the model the current date and time, in UTC and in the person's own time zone when the browser has reported one | The server clock; the person's saved time zone | No | none | `backend/open_webui/tools/builtin.py:161-194` |
| 2 | `calculate_timestamp` | Time & Calculation | Works out a past moment ("3 days ago", "last month", "a year ago") so the model can filter searches by date | The server clock; the person's time zone | No | If the date library is missing, a month counts as 30 days and a year as 365 | `backend/open_webui/tools/builtin.py:197-286` |
| 3 | `search_web` | Web Search | Searches the web with the search engine the admin chose and returns a title, link and snippet per result | Sends the query to the configured provider | External | Returns at most the admin's **Search Result Count** (`web.search.result_count`, code default 3; 5 only if the stored value is empty), even if the model asks for more | `backend/open_webui/tools/builtin.py:294-330`; `backend/open_webui/config.py:1179`, `:2947`; `web-search-and-web-loading.md` |
| 4 | `fetch_url` | Web Search | Downloads a web page and returns its readable text | Fetches the address through the web loader | External | Text longer than the admin's maximum fetch length is cut and ends `[Content truncated...]`; the page is added as a citation when the model's Citations capability is on | `backend/open_webui/tools/builtin.py:333-362`; `backend/open_webui/utils/middleware.py:6089-6111` |
| 5 | `generate_image` | Image Generation | Creates an image from a description with the admin's image engine; the image appears in the reply | Calls the image engine; saves the image to the reply | Yes (stores the image file and links it to the message) | Tells the model the image "is already visible to the user in the chat" so it does not repeat it | `backend/open_webui/tools/builtin.py:370-437` |
| 6 | `edit_image` | Image Generation | Changes one or more existing images according to an instruction (add, remove, replace, extend, combine) | Calls the image edit engine; saves the result to the reply | Yes (as above) | Needs the separate **Image Edit** admin switch | `backend/open_webui/tools/builtin.py:440-510`; `backend/open_webui/utils/tools.py:697-704` |
| 7 | `ask_user` | Ask User | Pauses the reply and asks the person one to three multiple-choice questions | Nothing until answered; the answers are saved in the reply | Yes (answers saved in the chat) | 1–3 questions, each with 2–3 options; must be the only tool in that step; details in section 5.5 | `backend/open_webui/tools/builtin.py:518-625`; `backend/open_webui/utils/ask_user.py:9-149` |
| 8 | `execute_code` | Code Interpreter | Runs Python code and returns its printed output, errors and result | Runs code in the person's browser (Pyodide engine) or on the admin's Jupyter server; charts printed as images are uploaded | Yes when the code prints an image (stored as a file and shown as a Markdown image labelled `Output Image`) | Python modules on the admin's block list (`CODE_INTERPRETER_BLOCKED_MODULES`) are restricted; Pyodide needs the browser connected; see `code-execution-and-interpreter.md` | `backend/open_webui/tools/builtin.py:633-792` |
| 9 | `list_memory_paths` | Memory | Lists the "paths" (named groups) the person's memories are filed under, with counts | The person's own memories | No | Up to 100 paths by default | `backend/open_webui/tools/builtin.py:800-828`; `backend/open_webui/routers/memories.py:409-422` |
| 10 | `read_memory_path` | Memory | Reads the memories stored under one path, with nearby parent and child paths | The person's own memories | No | Up to 50 memories by default | `backend/open_webui/tools/builtin.py:831-862`; `backend/open_webui/routers/memories.py:425-446` |
| 11 | `search_memories` | Memory | Finds the person's memories by words, path, type or id | The person's own memories | No | 5 results by default | `backend/open_webui/tools/builtin.py:865-920`; `backend/open_webui/routers/memories.py:391-406` |
| 12 | `add_memory` | Memory | Saves a new long-term memory (a preference, goal or standing instruction) | Creates a memory and its search entry | Yes | The tool description tells the model not to save short-lived details unless asked; the new memory is recorded as created `manual`, like one typed in Settings | `backend/open_webui/tools/builtin.py:923-960`; `backend/open_webui/routers/memories.py:183-231` |
| 13 | `update_memory` | Memory | Applies several memory changes at once: add, replace, move to another path, or remove | Creates, changes or deletes the person's memories | Yes | Each change is recorded as made by `tool` with the chat, message and model | `backend/open_webui/tools/builtin.py:963-1001`; `backend/open_webui/routers/memories.py:234-324` |
| 14 | `replace_memory_content` | Memory | Corrects the text (and optionally type or path) of one memory | Changes one memory | Yes | none | `backend/open_webui/tools/builtin.py:1004-1050`; `backend/open_webui/routers/memories.py:548` |
| 15 | `delete_memory` | Memory | Deletes one memory by id | Deletes the memory and its search entry | Yes | Returns `Memory not found or access denied` when the id is not one of the person's | `backend/open_webui/tools/builtin.py:1053-1082` |
| 16 | `list_memories` | Memory | Lists all of the person's memories with ids and dates | The person's own memories | No | No limit on the number returned | `backend/open_webui/tools/builtin.py:1085-1119` |
| 17 | `notify` | Notifications | Sends a message to one of the person's own notification targets (a webhook set in Settings › Notifications) | The person's notification settings; posts to the target's webhook address | External | Uses the default target when none is named; the target is matched by its id; failures come back as `Notification failed: {e}` | `backend/open_webui/tools/builtin.py:131-158`; `backend/open_webui/utils/notifications.py:234-243`, `:370-390` |

Inside a sub-agent run, tools 12 to 15 are removed so helpers cannot use them to change memories
(`backend/open_webui/utils/tools.py:766-769`; `backend/open_webui/utils/subagents.py:34-39`).

#### Notes, Chat History, Sub-Agents and Channels

| # | Tool | Group | What it does, in plain language | Reads or changes | Changes data | Limits and notes | Source |
|---|---|---|---|---|---|---|---|
| 18 | `search_notes` | Notes | Finds notes by title and text, with a short snippet around the match | Notes the person owns or that are shared with them for reading | No | 5 results by default; can filter by last-updated date | `backend/open_webui/tools/builtin.py:1127-1221` |
| 19 | `view_note` | Notes (also Knowledge Base when a note is attached) | Reads a whole note | One note, if the person owns it, can read it through sharing, or is an admin | No | Returns `Note not found` or `Access denied` | `backend/open_webui/tools/builtin.py:1224-1283` |
| 20 | `write_note` | Notes | Creates a new note with a title and text | Creates a note owned by the person | Yes | The new note is private (no sharing) | `backend/open_webui/tools/builtin.py:1286-1332` |
| 21 | `replace_note_content` | Notes | Rewrites a note, either completely or by replacing marked character ranges, and optionally renames it | Changes one note the person owns, can edit through sharing, or any note for an admin | Yes | Stops any AI writing already running in that note; the note is saved as plain Markdown (its rich-text form is cleared) and open copies update live; refusals listed in section 10.3 | `backend/open_webui/tools/builtin.py:1335-1504`; `:78-102` |
| 22 | `search_chats` | Chat History | Searches the person's earlier chats by title and message text, skipping the current chat | The person's own chats; archived chats are skipped unless the search text contains `archived:true`; hidden internal chats are never included | No | 5 results by default; can filter by last-updated date; the chat-search filter words (`tag:`, `folder:`, `pinned:`, `archived:`, `shared:`) work here too | `backend/open_webui/tools/builtin.py:1512-1607`; `backend/open_webui/models/chats.py:1963-2025` |
| 23 | `view_chat` | Chat History | Reads the visible conversation of one earlier chat | One of the person's own chats only (this applies to admins too) | No | Returns the messages on the chat's current branch only; `Chat not found or access denied` otherwise | `backend/open_webui/tools/builtin.py:1610-1672` |
| 24 | `delegate_task` | Sub-agents | Hands a focused job to a helper that runs in a hidden chat with the same model and tools, then returns its answer (or, with background mode, continues the chat when the helper finishes) | Creates a hidden sub-agent chat; the helper can use any tool the person's chat could | Yes (creates chats; the helper may change data through its own tools) | Not available inside a helper or for direct connections; limits and messages in `chat-completion-pipeline-and-generation-tasks.md` 5.14 | `backend/open_webui/tools/builtin.py:1680-1718`; `backend/open_webui/utils/subagents.py` |
| 25 | `timer` | Sub-agents | Sets a one-shot reminder: at the chosen time the stored prompt is sent back into this chat and the model answers it | Creates a hidden timer chat that holds the prompt and settings | Yes | `at` is a relative time (`10s`, `5m`, `1h`, `2d`, or `in 10 seconds`) or a date-time with a time zone; can be cancelled automatically when the person reads the chat or sends a message; section 5.8 | `backend/open_webui/tools/builtin.py:1721-1755`; `backend/open_webui/utils/timers.py:39-168` |
| 26 | `search_channels` | Channels | Finds channels by name or description | Channels the person can access | No | 5 results by default | `backend/open_webui/tools/builtin.py:1763-1812` |
| 27 | `search_channel_messages` | Channels | Searches messages, including thread replies, across the channels the person can access | Channel messages | No | 10 results by default; can filter by date | `backend/open_webui/tools/builtin.py:1815-1893` |
| 28 | `view_channel_message` | Channels | Reads one channel message with its author and reply count | One message, if the person can access its channel | No | Returns the author's display name; `Message not found`, `Channel not found` or `Access denied` | `backend/open_webui/tools/builtin.py:1896-1954` |
| 29 | `view_channel_thread` | Channels | Reads a whole thread: the first message and every reply in order | One thread, if the person can access its channel | No | Returns each author's display name | `backend/open_webui/tools/builtin.py:1957-2038` |

The channel tools pass other people's messages and display names to the model and into the
reply's tool output; support staff should treat those outputs as personal data.

#### Knowledge Bases, Chat Files and Skills

The knowledge tools are described in more depth, with their scope rules and limits, in
`knowledge-bases.md` sections 5.21 to 5.23. Which of them a model gets depends on whether knowledge
is attached (section 3.2).

| # | Tool | Group | What it does, in plain language | Reads or changes | Changes data | Limits and notes | Source |
|---|---|---|---|---|---|---|---|
| 30 | `list_knowledge_bases` | Knowledge Base (nothing attached) | Lists the knowledge bases the person can read, with file counts | Knowledge bases the person owns, or can read through sharing | No | 10 per call by default, with paging | `backend/open_webui/tools/builtin.py:2046-2101` |
| 31 | `search_knowledge_bases` | Knowledge Base (nothing attached) | Finds readable knowledge bases by words in the name or description | As above | No | 5 by default | `backend/open_webui/tools/builtin.py:2104-2161` |
| 32 | `search_knowledge_files` | Knowledge Base | Finds files by file name, inside the attached knowledge or across readable knowledge bases | Files in readable knowledge bases | No | 5 by default; refuses a knowledge base that is not attached (`Knowledge base {knowledge_id} is not attached to this model`) or not readable (`Access denied to knowledge base {knowledge_id}`) | `backend/open_webui/tools/builtin.py:2164-2326` |
| 33 | `list_chat_files` | Files | Lists the files uploaded to the current chat | Files attached to this chat that the person can read | No | Web links and pasted images are not listed | `backend/open_webui/tools/builtin.py:2413-2450`; `:2329-2360` |
| 34 | `grep_chat_files` | Files | Searches the chat's uploaded files for exact text or a pattern and returns matching lines with line numbers | The extracted text of the chat's files | No | At most 50 matching lines (`KNOWLEDGE_GREP_MAX_MATCHES`), then `[{KNOWLEDGE_GREP_MAX_MATCHES} of {total_matches} matches shown — use file_id to narrow]`; patterns use RE2 syntax | `backend/open_webui/tools/builtin.py:2453-2506`; `:2363-2410`; `backend/open_webui/env.py:1177` |
| 35 | `query_chat_files` | Files | Finds the passages in the chat's uploaded files closest in meaning to a question | The chat files' search index | No | At most the admin's **Top K** (`rag.top_k`, code default 3; 5 only if the stored value is empty); uses the admin's hybrid search and reranking settings; results become citations | `backend/open_webui/tools/builtin.py:2509-2626`; `backend/open_webui/config.py:968`, `:2899` |
| 36 | `grep_knowledge_files` | Knowledge Base | Exact text or pattern search through knowledge files, returning matching lines | The extracted text of attached or readable knowledge files | No | 50 matching lines; without attachments, the first 200 readable knowledge bases | `backend/open_webui/tools/builtin.py:2629-2747` |
| 37 | `view_file` | Files; Knowledge Base (files attached) | Reads a file's extracted text in pages, by characters or by lines | One file the person owns, can read through sharing, or that is attached to the model; any file for an admin | No | 10,000 characters by default, 100,000 at most (`VIEW_FILE_DEFAULT_MAX_CHARS`, `VIEW_FILE_MAX_CHARS`); 100 lines when a line range has no end; `File not found` also when access is refused | `backend/open_webui/tools/builtin.py:2750-2860`; `backend/open_webui/env.py:1179-1180` |
| 38 | `view_knowledge_file` | Knowledge Base | Reads a knowledge file's extracted text in pages and says which knowledge base it is in | One file in a knowledge base the person can read, or the person's own file | No | Same size limits as `view_file`; `Access denied` otherwise | `backend/open_webui/tools/builtin.py:2863-3006` |
| 39 | `list_knowledge` | Knowledge Base (knowledge attached) | Lists what is attached: knowledge bases (name, description, file count), single files and notes; with a knowledge base id, pages through its files | Attached knowledge the person can read | No | Up to 200 files per page (50 by default) | `backend/open_webui/tools/builtin.py:3009-3148` |
| 40 | `query_knowledge_files` | Knowledge Base | Finds the passages closest in meaning to a question across attached knowledge, named knowledge bases, or the person's readable knowledge bases; attached notes are returned whole | Knowledge search indexes; connected (external) knowledge sources are asked too | No (External for connected sources) | 5 results by default; without attachments or named bases, the 50 most recently updated readable knowledge bases; results become citations | `backend/open_webui/tools/builtin.py:3151-3369` |
| 41 | `query_knowledge_bases` | Knowledge Base (nothing attached) | Finds which knowledge bases are about a topic, by meaning of their name and description | The knowledge-base index | No | 5 by default; scans up to 10,000 readable knowledge bases | `backend/open_webui/tools/builtin.py:3372-3474`; `:75` |
| 42 | `view_skill` | none (offered when skills are listed) | Loads the full instructions of a skill the model was told about, so it can follow them | One active skill the person owns or can read, or a skill on the connected terminal | No | `Skill '{id}' not found` or `Access denied` | `backend/open_webui/tools/builtin.py:3482-3545`; `backend/open_webui/utils/middleware.py:2830-2854` |

**Skills in native mode.** When built-in tools are on, every active skill the person can use is
listed to the model by name and description, and the model loads the ones it needs with
`view_skill`; a skill mentioned directly in the message is added in full instead
(`backend/open_webui/utils/middleware.py:2830-2854`). With built-in tools off, only skills that are
selected for the chat, attached to the model or mentioned are added, in full
(`backend/open_webui/utils/middleware.py:2771-2776`, `:2833-2848`). Skills themselves are covered in
`prompts-and-skills.md`.

#### Task List, Automations and Calendar

| # | Tool | Group | What it does, in plain language | Reads or changes | Changes data | Limits and notes | Source |
|---|---|---|---|---|---|---|---|
| 43 | `create_tasks` | Task Management | Creates (or replaces) a visible checklist for a long, multi-step request | Saves the list on the current chat and shows it in the chat | Yes (the chat's task list) | Only in saved chats; statuses `pending`, `in_progress`, `completed`, `cancelled`; items with no text are dropped | `backend/open_webui/tools/builtin.py:3556-3640` |
| 44 | `update_task` | Task Management | Ticks off (or changes the status of) one checklist item | The current chat's task list | Yes | `Task with id "{id}" not found`; `Invalid status: {status}. Must be one of: cancelled, completed, in_progress, pending` | `backend/open_webui/tools/builtin.py:3643-3690` |
| 45 | `create_automation` | Automations | Schedules a prompt to run automatically, once or on a repeating schedule, using the current chat's model; when created from a channel reply, the automation's target is that channel | Creates an automation owned by the person, active at once | Yes | The schedule is an iCalendar rule read in the person's time zone; non-admins are held to the admin's maximum number of automations and minimum interval (`Automation limit reached ({size})`, `Schedule too frequent. Minimum interval is {interval} seconds.`); `Could not detect current model`, `Invalid schedule: {e}`, `Folder not found` | `backend/open_webui/tools/builtin.py:3709-3814`; `backend/open_webui/routers/automations.py:69-95`; `backend/open_webui/constants.py:116-117` |
| 46 | `update_automation` | Automations | Changes an automation's name, prompt, schedule, model or folder; anything not given stays the same | One of the person's own automations | Yes | `Automation not found`; `Access denied` for someone else's automation; the minimum-interval rule applies | `backend/open_webui/tools/builtin.py:3817-3918` |
| 47 | `list_automations` | Automations | Lists the person's automations with schedule, status and next run times | The person's own automations | No | 10 by default; can filter active or paused, and by folder | `backend/open_webui/tools/builtin.py:3921-3990` |
| 48 | `toggle_automation` | Automations | Pauses an active automation or resumes a paused one | One of the person's own automations | Yes | `Automation not found`; `Access denied` | `backend/open_webui/tools/builtin.py:3993-4041` |
| 49 | `delete_automation` | Automations | Deletes an automation and its whole run history | One of the person's own automations | Yes (permanent) | Returns `Automation "{name}" deleted` | `backend/open_webui/tools/builtin.py:4044-4085` |
| 50 | `search_calendar_events` | Calendar | Finds calendar events by words (title, description, location) and/or a date range | Events in calendars the person owns or can read through sharing | No | 10 by default; dates are read in the person's time zone (UTC if unknown) | `backend/open_webui/tools/builtin.py:4151-4237`; `:4096-4108`; `backend/open_webui/models/calendar.py:486-516`, `:593-623` |
| 51 | `create_calendar_event` | Calendar | Adds an event or reminder ("remind me", "add to my calendar") | Creates an event in the first calendar marked default among those the person can see (normally their own), or in a named calendar they can edit | Yes | Without an end time an event lasts one hour; reminder 10 minutes before unless set (0 = at the time, -1 = none); `No calendars found. Cannot create event.`, `Calendar not found`, `Access denied to this calendar` | `backend/open_webui/tools/builtin.py:4240-4364` |
| 52 | `update_calendar_event` | Calendar | Changes an event's details, cancels it, or changes its reminder | One event the person created, or one in a calendar they can edit; any event for an admin | Yes | `Event not found`; `Access denied` | `backend/open_webui/tools/builtin.py:4367-4485` |
| 53 | `delete_calendar_event` | Calendar | Deletes an event permanently | As above | Yes (permanent) | Returns `Event "{title}" deleted` | `backend/open_webui/tools/builtin.py:4488-4545` |

The automation, calendar and timer systems themselves (how runs happen, alerts, limits) are in
`automations-calendar-and-timers.md`.

### 4.4 Which Tools Can Change Data

Twenty-one of the 53 tools can create, change or delete stored data: `generate_image`,
`edit_image`, `ask_user` (answers saved in the chat), `execute_code` (output images), the four
memory writers (`add_memory`, `update_memory`, `replace_memory_content`, `delete_memory`),
`write_note`, `replace_note_content`, `delegate_task`, `timer`, `create_tasks`, `update_task`,
the four automation writers (`create_automation`, `update_automation`, `toggle_automation`,
`delete_automation`) and the three calendar writers (`create_calendar_event`,
`update_calendar_event`, `delete_calendar_event`). Three more reach outside services without
storing anything locally: `search_web`, `fetch_url` and `notify` (rows 3, 4 and 17 of the
catalogue). Only **Ask for approval** (section 5.4) makes the person confirm a tool before it
runs, and it then applies to every tool call, reading ones included; the code has no per-tool
approval list (`backend/open_webui/utils/middleware.py:5934-5956`).

## 5. Workflows (Step by Step)

### 5.1 How a Reply Uses Built-In Tools

1. The person sends a message from the chat page. The browser includes the composer toggles
   (`features`), the approval mode and its session id; the request's parameters are the
   person's own default parameters overlaid with the chat's (`src/lib/components/chat/Chat.svelte:3393-3416`,
   `:3577-3587`).
2. The server settles the **Function Calling** mode: the person's or chat's setting first, then
   the model's (which includes the admin's default parameters), then `native`
   (`backend/open_webui/main.py:1170-1177`, `:1290-1294`). It settles the approval mode
   (`backend/open_webui/main.py:1255-1264`).
3. If the conditions in section 3.1 hold, the server lists the attached knowledge for the model in
   its instructions, adds file context, and builds the built-in tool list from the groups in
   section 3.2 (`backend/open_webui/utils/middleware.py:3099-3138`;
   `backend/open_webui/utils/tools.py:520-802`). Built-in tools are added after any selected
   workspace tools, MCP or terminal tools, and never replace one with the same name.
4. The tool definitions go to the model with the conversation (`backend/open_webui/utils/middleware.py:3184-3195`).
5. When the model answers with one or more tool calls, each call is recorded and shown as a
   tool-call entry. Then, in this order (`backend/open_webui/utils/middleware.py:5891-6060`):
   - an `ask_user` call pauses the reply for the question card (section 5.5);
   - in **Ask for approval** mode, the reply pauses for approval (section 5.4);
   - otherwise the tools run: `delegate_task` calls side by side, all others one after another.
6. Each result is recorded (status `failed` if it looks like an error, section 4.2), citations
   are taken from `fetch_url`, `view_file`, `view_knowledge_file`, `query_knowledge_files` and
   `query_chat_files` when the model's Citations capability is on, and the model is called again
   with the results (`backend/open_webui/utils/middleware.py:6089-6302`).
7. Steps 5 and 6 repeat until the model answers without a tool call, or until the round limit
   (section 7.3) is reached, which shows `Tool-call limit reached ({max_tool_call_iterations} iterations).`
   (`backend/open_webui/utils/middleware.py:5891-5894`, `:6339-6346`).

The order of the wider chat pipeline (filters, retrieval, saving, background tasks) is in
`chat-completion-pipeline-and-generation-tasks.md`, sections 5.6 and 5.15.

### 5.2 Turn Built-In Tools On or Off for One Model

Who: anyone who can edit the model (workspace model editors, admins).

1. Open Workspace › Models and edit the model (`/workspace/models/edit?id={id}`).
2. Under **Capabilities**, the **Builtin Tools** box switches all built-in tools on or off for
   this model (`src/lib/components/workspace/Models/Capabilities.svelte:57-60`).
3. When **Builtin Tools** is ticked, a second list titled **Builtin Tools** appears with sixteen
   boxes, one per group: **Time & Calculation**, **Ask User**, **Memory**, **Chat History**,
   **Notes**, **Knowledge Base**, **Files**, **Channels**, **Notifications**, **Web Search**,
   **Image Generation**, **Code Interpreter**, **Task Management**, **Automations**,
   **Calendar**, **Sub-agents**; hovering a name shows its description
   (`src/lib/components/workspace/Models/ModelEditor.svelte:1265-1269`;
   `src/lib/components/workspace/Models/BuiltinTools.svelte:11-122`;
   `src/lib/i18n/locales/en-US/translation.json:2540-2572`).
4. Unticking a group stores `false` for it; ticking it again removes the entry, so the group
   counts as on (`src/lib/components/workspace/Models/BuiltinTools.svelte:83-90`;
   `src/lib/components/workspace/Models/ModelEditor.svelte:393-398`).
5. Save the model. The change applies to the next message sent with that model.

Unticking a group only removes tools; ticking it does not by itself make tools appear when the
admin switch, permission, capability or composer toggle for that family is off (section 3.2).
The **Web Search**, **Image Generation** and **Code Interpreter** capabilities are separate boxes
under **Capabilities** and must also be on.

### 5.3 Admin: Defaults for Every Model and Feature Switches

1. **Model defaults.** Admin Settings › Models › **Model Defaults** › **Model Capabilities**
   (`/admin/settings/models`) holds default capabilities and, when **Builtin Tools** is ticked
   there, default **Builtin Tools** groups (`src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:186-221`).
   On save they are stored in the `models.default_metadata` setting
   (`src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte:107-121`;
   `backend/open_webui/routers/configs.py:66`).
2. **How defaults combine with a model's own settings.** Default capabilities are a base that each
   model's own capability choices override one by one; default **Builtin Tools** groups apply only
   to models that have no group choices of their own (`backend/open_webui/utils/models.py:337-355`).
3. **Feature switches** (all under Admin Settings): **Web Search** (`/admin/settings/web`),
   **Image Generation** and **Image Edit** (`/admin/settings/images`), **Enable Code Interpreter**
   (`/admin/settings/code-execution`), and **Memories**, **Notes**, **Channels**, **Calendar**,
   **Automations** and **User Webhooks** (`/admin/settings/general`), plus **Enable sub-agents**
   (`/admin/settings/subagents`). Section 7.1 lists their keys and code defaults.
4. **Permissions.** The `features.*` and `chat.file_upload` permissions in Admin Panel › Users ›
   Groups decide which families a non-admin gets (section 3.2; `users-groups-roles-and-permissions.md`).

### 5.4 Tool Approval ("Ask for Approval")

**Turning it on.** An admin switches on Admin Settings › Interface › Chat › **Tool Permissions**
(label shown with an **Experimental** badge; description `Show Full access and Ask for approval in
the chat input menu.`) (`src/lib/components/admin/Settings/Interface.svelte:258-269`;
`src/lib/i18n/locales/en-US/translation.json:2532-2533`). Until then every chat runs with full
access (`backend/open_webui/main.py:1255-1264`).

**Choosing the mode (the person).**

1. In the chat input, open the **More** menu; a **Tool Permissions** entry shows the current mode
   (`src/lib/components/chat/MessageInput/InputMenu.svelte:146-185`).
2. Pick **Full access** (`Run tools without asking for approval.`) or **Ask for approval**
   (`Stop before each tool call until you allow or deny it.`) (`:54-65`, `:545-590`).
3. The choice is saved in the person's settings (so it becomes their default for new chats) and,
   for a saved chat, in that chat's parameters (`src/lib/components/chat/Chat.svelte:437-462`).
   Failures to save are only logged in the browser console.

**What happens in Ask for approval mode.**

1. When the model calls one or more tools, nothing runs yet. The reply is saved with the calls,
   the first is marked `pending` (waiting) and the rest `queued`, and the reply stops
   (`backend/open_webui/utils/middleware.py:5934-5956`, `:3613-3655`). This applies to every tool,
   built-in or not, including read-only ones. The pause needs a saved chat: in a temporary chat
   the code skips it, so tools run without asking (`backend/open_webui/utils/middleware.py:5935-5940`;
   `backend/open_webui/utils/chat_id.py:15-16`).
2. The person sees the entry `Allow {{NAME}}?` with **Allow** and **Deny** buttons; when several
   tool calls are grouped, the group line carries the buttons, or each pending call is listed with
   its own buttons (`src/lib/components/common/ToolCallDisplay.svelte:248-276`;
   `src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte:234-297`). Opening the
   entry shows the **Input** the model wants to send, so the person can check it first.
3. **Allow** runs that call; if more calls are waiting the reply pauses again on the next one,
   otherwise the model continues with the results (`backend/open_webui/utils/tool_approval.py:60-64`;
   `backend/open_webui/utils/middleware.py:3412-3610`).
4. **Deny** records the result `Error: tool call rejected by user.` for the model, the entry
   shows `Denied {{NAME}}` with a red cross, and the model continues (and can, for example,
   explain that it could not proceed) (`backend/open_webui/utils/tool_approval.py:65-75`).
5. Buttons appear only in the person's own, editable view of the chat (`save` is off for
   read-only views) (`src/lib/components/chat/Messages/ResponseMessage.svelte:870`;
   `src/lib/components/chat/Messages/StructuredOutputRenderer.svelte:171-186`).

**Timeouts.** The code sets no time limit on an approval: a paused reply waits until the person
answers, switches mode or presses **Stop**.

**After a reload.** The pause is saved in the chat (calls, statuses and the settings needed to
resume), so reopening the chat shows the same **Allow**/**Deny** entry and resolving it resumes the
reply with the original model, tools and features (`backend/open_webui/utils/middleware.py:3634-3655`;
`backend/open_webui/utils/tool_approval.py:131-186`).

**Switching to Full access while a call waits** approves the first waiting call in the chat
automatically, and later tool calls then run without asking
(`src/lib/components/chat/Chat.svelte:465-500`; `backend/open_webui/utils/tool_approval.py:152-156`).
If the model had asked for several tools in the same step, the others stay `queued` behind the
first; outside ask mode the code does not promote them for approval, and the resumed reply
appears to stop again while they are unresolved (`backend/open_webui/utils/middleware.py:3504-3530`;
`backend/open_webui/main.py:1654-1655`). This is read from the code and is TO BE CONFIRMED
(section 14.3); **Stop** closes such a reply.

**Pressing Stop** while a reply is paused (so no task is running for the chat) closes the reply
and marks the waiting calls as rejected (`backend/open_webui/main.py:2160-2214`;
`backend/open_webui/tasks.py:296-309`). The Stop button stays visible while the reply
is paused, because the reply is not finished (`src/lib/components/chat/MessageInput.svelte:172-175`,
`:2603-2612`).

**Where approval never applies.** Automation runs, channel replies and fired timers always use
full access (`backend/open_webui/main.py:1255-1258`; section 5.8).

### 5.5 Ask-User Questions (`ask_user`)

1. The model calls `ask_user` with one to three questions, each with a short header, the
   question and two or three options (label and description); "Other" free text is allowed unless
   the model turns it off (`backend/open_webui/utils/ask_user.py:25-80`).
2. It must be the **only** tool call in that step, and only one `ask_user` per step; otherwise the
   model is told `Error: ask_user must be the only tool call, so it did not run. Call ask_user on its own.`
   or `Error: only one ask_user call is allowed per turn.` and the other calls go ahead
   (`backend/open_webui/utils/ask_user.py:9-22`; `backend/open_webui/utils/middleware.py:5897-5903`).
   Badly formed questions are refused with the messages in sections 10.3 and 10.4.
3. The reply pauses and is saved with the question (`backend/open_webui/utils/middleware.py:5904-5914`).
   The question is not listed among the reply's tool calls; instead a card appears above the
   message box (`src/lib/components/chat/Messages/structuredOutput.ts:396-402`;
   `src/lib/components/chat/MessageInput.svelte:1774-1786`).
4. The card shows the header, a counter such as `1/3` when there are several questions, the
   question, the options (the first is marked **Recommended**), an **Other** field with the
   placeholder **Type your answer**, and the buttons **Cancel**, **Previous**, **Next** and
   **Submit answers** (`src/lib/components/chat/AskUserCard.svelte:173-303`).
5. Choosing an option moves to the next question; on the last question it submits at once.
   **Submit answers** is available when every question has an answer
   (`src/lib/components/chat/AskUserCard.svelte:83-137`, `:290-298`).
6. Submitting saves the answers as the tool's result and resumes the reply; **Cancel** counts as a
   refusal (the model receives `Error: tool call rejected by user.`)
   (`src/lib/components/chat/Chat.svelte:559-623`; `backend/open_webui/utils/tool_approval.py:65-95`).
7. **Timeout.** The question card for a saved pause has no time limit and survives a reload
   (`src/lib/components/chat/Chat.svelte:599-623`, `timeoutMs: null`). The model's `timeout_ms`
   (60 to 240 seconds, default 120) applies only on the older live path, where a tool asks the
   browser directly; there the card closes itself after the time and the tool reports
   `cancelled` (`src/lib/components/chat/Chat.svelte:1402-1408`, `:625-637`;
   `src/lib/components/chat/AskUserCard.svelte:59-69`; `backend/open_webui/tools/builtin.py:586-614`).
   On that path, a chat with no browser connection gets
   `User input requires an active browser session with WebSocket connection.` (`backend/open_webui/tools/builtin.py:589-596`).
8. While the card is shown the Stop button is hidden; **Cancel** is the way out
   (`src/lib/components/chat/MessageInput.svelte:172-175`).

### 5.6 How Tool Calls and Results Appear, and Hide Processing Details

**Normal display.** Each call is an entry as described in section 4.2: a spinner while it is
prepared and run, then a green tick (or red cross) with `View Result from {{NAME}}`. Opening an
entry shows **Input** and **Output**. A run of consecutive tool calls (and reasoning or code
analysis) is folded into one **Exploring**/**Explored** line that opens to the individual entries
(`src/lib/components/chat/Messages/structuredOutput.ts:344-444`;
`src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte:146-232`). The personal
setting that opens all such entries by default is `expandDetails`
(`src/lib/components/chat/Messages/StructuredOutputRenderer.svelte:125`, `:185`). Images from
`generate_image` and `edit_image` appear in the reply itself (the tool saves them to the
message), and images printed by `execute_code` appear in its output as Markdown images labelled `Output Image`
(`backend/open_webui/tools/builtin.py:401-432`, `:744-780`).

**Hide Processing Details (MedIT GPT addition).** Settings › Interface › **Hide Processing
Details**, described as `Show "Thinking..." instead of status updates, tool calls, reasoning, and
code analysis while a response is generated, and keep them hidden afterwards. Tool approval
requests and images or embeds from tools still appear.`
(`src/lib/components/common/InterfaceSettings.svelte:1358-1378`;
`src/lib/i18n/locales/en-US/translation.json:2923-2924`). Admins can set a default for everyone
in Admin Settings › General, which each person can override
(`src/lib/components/admin/Settings/General.svelte:41`, `:71-78`;
`backend/open_webui/routers/auths.py:115`). When it is on:

| What | Behaviour | Source |
|---|---|---|
| Tool-call entries | Hidden, except an entry waiting for **Allow**/**Deny** (or an answer) | `src/lib/components/common/ToolCallDisplay.svelte:145`, `:199-200` |
| Grouping | Reasoning and code-analysis entries are dropped; tool calls are kept one by one (not grouped) so a waiting approval can still show | `src/lib/components/chat/Messages/structuredOutput.ts:403-416`; `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte:89-105` |
| Images and embedded pages from tools | Still shown; an embed loses the tool-name caption | `src/lib/components/common/ToolCallDisplay.svelte:178-198`, `:372-387` |
| Status lines (for example web search progress) | Hidden | `src/lib/components/chat/Messages/ResponseMessage.svelte:197-199` |
| While the reply runs | `Thinking...` is shown until answer text appears, unless a tool call is waiting for the person | `src/lib/components/chat/Messages/ResponseMessage.svelte:214-221`, `:920-921` |
| Task checklist above the message box | Hidden | `src/lib/components/chat/MessageInput.svelte:1792-1796` |

The setting changes only what is drawn; tools still run and their results are still saved in the
chat. Section 12 records how this differs from upstream.

### 5.7 Sub-Agents (`delegate_task`)

When an admin has turned on **Enable sub-agents** (off in code), the model can hand a sub-task to
a helper. The reply shows an entry labelled `Sub-agent: "{task}"` (or `Background sub-agent:
"{task}"`) instead of `delegate_task`; several sub-agent calls in one step run side by side
(`src/lib/components/chat/Messages/structuredOutput.ts:202-213`;
`backend/open_webui/utils/middleware.py:6030-6044`). The helper works in a hidden chat titled
`Sub-agent: {task}` (first 60 characters; `backend/open_webui/utils/subagents.py:400`) with the
same model, tools and files; in background mode
the parent chat later shows a row `Background sub-agent finished`
(`src/lib/components/chat/Messages/SubagentResultRow.svelte:41`). A helper cannot start its own
helpers (`Error: sub-agents cannot delegate recursively.`) and loses the four memory-changing
tools (`backend/open_webui/tools/builtin.py:1703-1704`; `backend/open_webui/utils/tools.py:766-769`).
Settings, limits, background behaviour and every sub-agent message are documented in
`chat-completion-pipeline-and-generation-tasks.md` section 5.14.

### 5.8 Timers (`timer`)

`timer` is offered together with `delegate_task` (same **Sub-agents** group and the same admin
switch) (`backend/open_webui/utils/tools.py:648-654`).

1. **Setting.** The model calls `timer` with a prompt, a time `at` and optionally `cancel_on`.
   `at` is either relative (a number and a unit: `s`, `sec`, `second`, `seconds`, `m`, `min`,
   `minute`, `minutes`, `h`, `hour`, `hours`, `d`, `day` or `days`, optionally preceded by `+` or
   `in`) or a full date-time with a time
   zone such as `2026-11-03T09:00:00-05:00` (an invented example); it must be in the future
   (`backend/open_webui/utils/timers.py:28-66`).
2. **What is stored.** A hidden chat titled `Timer: {prompt}` (first 60 characters) holding the
   prompt, the due time, the status `pending` and the parent chat's model, tools, skills, filters,
   features, files and variables (`backend/open_webui/utils/timers.py:97-157`). The model is told
   `{"status": "set", "at": "<UTC time>", "cancel_on": [...]}` (`:161-168`).
3. **Waiting.** The in-process scheduler checks for due timers every `TIMER_POLL_INTERVAL`
   seconds (default 1), up to ten at a time (`backend/open_webui/utils/automations.py:54`, `:86-99`).
4. **Cancelling.** If `cancel_on` includes `chat.read`, the timer is cancelled when the person
   opens the chat (the browser reports it as read); with `chat.user_message`, when the person sends
   a new message in that chat. Only the person's own timers on that chat are cancelled
   (`backend/open_webui/socket/main.py:610-638`; `backend/open_webui/main.py:1539-1547`;
   `backend/open_webui/utils/timers.py:202-227`). The code has no screen to list or cancel timers
   by hand.
5. **Firing.** When due, the timer is claimed, and if the parent chat is busy with a reply it is
   put back and retried on the next check (`backend/open_webui/utils/timers.py:171-199`, `:295-308`).
   Otherwise the prompt is added to the parent chat as a hidden message after the latest finished
   reply, a new reply is started with the stored settings, and the browser is told to reload the
   chat (`:310-416`). The chat shows a collapsed row **Timer** followed by the prompt text, which
   opens to show the full prompt (`src/lib/components/chat/Messages/UserMessage.svelte:346-377`).
   The new reply runs with full access (no approval pauses), because the timer's request carries
   no approval mode (`backend/open_webui/utils/timers.py:376-396`; `backend/open_webui/main.py:1255-1264`).
6. **Failures** are recorded only on the hidden timer chat (`status: error` with a reason such as
   `parent chat no longer exists`, `timer user no longer exists`, `owner no longer permitted to run timers`
   or `model context is missing`); the person is not told (`backend/open_webui/utils/timers.py:245-271`,
   `:417-429`).
7. **Refusals to the model** when setting a timer are listed in section 10.4; timers are refused
   inside a sub-agent run and for direct connections.

The scheduler loop itself is described in `automations-calendar-and-timers.md`.

### 5.9 Task Checklist (`create_tasks`, `update_task`)

1. For a long request, the model may call `create_tasks` with a list of steps; each has text and a
   status (`pending`, `in_progress`, `completed`, `cancelled`). Calling it again replaces the list
   (`backend/open_webui/tools/builtin.py:3593-3640`).
2. The list is saved on the chat (`tasks`) and pushed to the browser
   (`backend/open_webui/tools/builtin.py:3580-3590`, `:3631-3632`; `src/lib/components/chat/Chat.svelte:1271-1272`).
3. While the reply is running, a box above the message box reads
   `{completed} out of {total} tasks completed` with the steps and their state
   (`src/lib/components/chat/MessageInput.svelte:1792-1796`;
   `src/lib/components/chat/Messages/ResponseMessage/TaskList.svelte:20-34`). The chat's status
   panel shows a **Tasks** count (`src/lib/components/chat/MessageInput.svelte:1865-1872`).
4. The model ticks steps off with `update_task` (`backend/open_webui/tools/builtin.py:3643-3690`).
5. Only in saved chats; in a temporary chat the tools are not offered
   (`backend/open_webui/utils/tools.py:738-741`).

### 5.10 When a Built-In Tool Fails

| Situation | What the person sees | What the model receives | Source |
|---|---|---|---|
| The tool reports a problem (for example no access, not found, bad input) | The entry finishes with a red cross; the reason is in its **Output** | The JSON error or `Error: …` text, so it can explain or try again | `backend/open_webui/utils/middleware.py:158-197`, `:6122-6152` |
| The tool crashes | As above | `{"error": "<exception text>"}` | `backend/open_webui/utils/middleware.py:6026-6028` |
| The model asks for a tool that is not available | Red-cross entry | `Error: Tool "{name}" not found.` | `:5995-5997` |
| The model sends arguments that are not valid JSON | Entry with an error result | `Error: Tool call arguments could not be parsed. The model generated malformed or incomplete JSON for '{tool_function_name}'. Please try again.` or `Error: Tool call arguments for '{name}' must be a JSON object. Please try again.` (in the source the tool name is wrapped in backticks, not quotes) | `:5984-5994`, `:6050-6060` |
| The person denies the call | `Denied {{NAME}}` | `Error: tool call rejected by user.` | `backend/open_webui/utils/tool_approval.py:65-75` |
| Too many rounds of tool calls | Error box in the reply: `Tool-call limit reached ({max_tool_call_iterations} iterations).` | (loop ends) | `backend/open_webui/utils/middleware.py:6339-6346` |
| The follow-up call to the model after the tools fails | Error box with the provider's error | (loop ends) | `:6328-6337` |

Parameters the model invents but the tool does not define are dropped before the call
(`backend/open_webui/utils/middleware.py:6001-6002`). Most refusals are worded for the model, not
the person; tier 1 reads them in the entry's **Output** (section 10).

## 6. Data Model

Built-in tools have **no table of their own**: their definitions are Python code, and the list the
model sees is rebuilt for every message (`backend/open_webui/utils/tools.py:520-802`). What is
stored is the configuration that switches them, the record of each call inside the chat, and
whatever data the tools themselves create.

### 6.1 Where the Switches Are Stored

| What | Where | Source |
|---|---|---|
| A model's **Builtin Tools** capability | `meta.capabilities.builtin_tools` of the model (the `model` table's `meta` JSON for workspace models) | `src/lib/constants.ts:115-128`; `backend/open_webui/utils/middleware.py:2812` |
| A model's group switches | `meta.builtinTools`, for example `{"web_search": false}`; a missing group counts as on | `src/lib/components/workspace/Models/ModelEditor.svelte:393-398`; `backend/open_webui/utils/tools.py:536-540` |
| Defaults for every model | Setting `models.default_metadata` (`capabilities`, `builtinTools`, `defaultFeatureIds`) | `backend/open_webui/config.py:3094`; `backend/open_webui/utils/models.py:337-355` |
| Feature switches and permissions | Settings rows such as `web.search.enable`, `subagents.enable`, `chat.tool_permissions.enable`, `user.permissions` | section 7.1 |
| A person's approval mode | Their settings, `ui.params.tool_approval_mode`; and, per saved chat, the chat's `params.tool_approval_mode` | `src/lib/components/chat/Chat.svelte:437-462` |
| A person's Hide Processing Details choice | Their settings, `hideProcessingDetails` in the interface settings model; admin default in `ui.default_interface_settings` | `backend/open_webui/models/users.py:100`; `backend/open_webui/routers/auths.py:115` |
| Function Calling mode | `params.function_calling` on the model, in the person's settings, in the chat, or in the admin's default model parameters (`models.default_params`) | `backend/open_webui/main.py:1170-1177`, `:1290-1294` |

### 6.2 How a Tool Call Is Recorded in the Chat

Each reply's `output` (saved in the chat's history and, in parallel, in the `chat_message`
table's `output` column) holds items in order (`backend/open_webui/models/chats.py:1141-1190`;
`backend/open_webui/models/chat_messages.py:128-155`):

| Item `type` | Fields | Meaning | Source |
|---|---|---|---|
| `function_call` | `id`, `call_id`, `name`, `arguments` (JSON text), `status`, optionally `approved` | One tool call by the model | `backend/open_webui/utils/middleware.py:5916-5932` |
| `function_call_output` | `id` (`fco_…`), `call_id`, `output` (a list of `input_text` parts and, for images sent back to the model, `input_image` parts), `status`, optionally `files` and `embeds` | The result returned to the model | `backend/open_webui/utils/middleware.py:6122-6152` |
| `message` | `content` with `output_text` parts | The model's visible text | `backend/open_webui/utils/middleware.py:3531-3539` |

**Statuses of a `function_call`:** `in_progress` (being prepared), `pending` (waiting for the
person: approval or `ask_user`), `queued` (waiting behind another approval, or approved and about
to run), `completed`, `failed`, `rejected` (denied, or closed by Stop); the server also treats
`requires_approval` as waiting (`backend/open_webui/utils/middleware.py:3613-3633`, `:6154-6161`;
`backend/open_webui/utils/tool_approval.py:55-75`; `backend/open_webui/main.py:2183-2189`).

**While a reply is paused**, the assistant message is saved with `done: false` and its `meta`
holds what is needed to resume: `session_id`, `tool_ids`, `skill_ids`, `terminal_id`,
`tool_servers`, `filter_ids`, `features`, `variables`, `files` and `params`
(`backend/open_webui/utils/middleware.py:3634-3655`). An `ask_user` answer is saved as the call's
result: `{"status": "answered", "answers": {...}}` keyed by question id, each answer either the
chosen option (`option_index`, `label`, `description`) or `{"type": "other", "text": ...}`
(`backend/open_webui/utils/tool_approval.py:76-95`; `src/lib/components/chat/AskUserCard.svelte:92-115`).

Tool inputs and outputs can contain personal or health information (search queries, note and
memory text, channel messages with names, file excerpts). They stay in the chat until the chat is
deleted, and are part of the chat object that the chat menu's JSON export downloads
(`src/lib/components/layout/Navbar/Menu.svelte:240-255`).

### 6.3 Other Records Built-In Tools Create

| Record | Created or changed by | Where | Source |
|---|---|---|---|
| Task list | `create_tasks`, `update_task` | `chat.tasks` (JSON list of `id`, `content`, `status`) | `backend/open_webui/models/chats.py:148`, `:2666-2677` |
| Timer | `timer` | A hidden `chat` row: `meta` with `internal: true`, `type: "timer"`, `parent_chat_id`, `parent_message_id`, `timer_at`, `status` (`pending`, `running`, `completed`, `cancelled`, `error`), `cancel_on`, `run` (stored settings), `timer_error` on failure; column `timer_at` set only while it waits | `backend/open_webui/utils/timers.py:119-157`, `:189-199`, `:219-226`, `:422-429`; `backend/open_webui/models/chats.py:153` |
| Timer prompt in the parent chat | a fired timer | A user message with `meta: {"internal": true, "type": "timer", "timer_id": ...}` | `backend/open_webui/utils/timers.py:325-334` |
| Sub-agent run | `delegate_task` | A hidden `chat` row with `meta` `internal: true`, `type: "subagent"`, the parent chat and message, a delegation id and the mode; see the pipeline document | `backend/open_webui/utils/subagents.py:428-435`; `chat-completion-pipeline-and-generation-tasks.md` 5.14 |
| Memories | the memory writers | `memory` rows and the vector collection `user-memory-{user_id}` | `backend/open_webui/routers/memories.py:183-231`, `:234-324`; `backend/open_webui/tools/builtin.py:1070-1073` |
| Notes | `write_note`, `replace_note_content` | `note` rows (`data.content.md`; `json` and `html` cleared on rewrite) | `backend/open_webui/tools/builtin.py:1310-1316`, `:1470-1485` |
| Automations | automation writers | `automation` rows; `delete_automation` also deletes `automation_run` rows | `backend/open_webui/tools/builtin.py:3781-3797`, `:4073-4074` |
| Calendar events | calendar writers | `calendar_event` rows (reminder minutes in `meta.alert_minutes`) | `backend/open_webui/tools/builtin.py:4329-4351` |
| Images | `generate_image`, `edit_image`, `execute_code` | Files in storage plus file records, linked to the message (`files`) | `backend/open_webui/tools/builtin.py:402-412`, `:744-780` |
| Images sent back to the model | any tool returning an image | Stored so the model can see them | `backend/open_webui/utils/middleware.py:1029`, `:6133-6140` |

Each of those areas has its own reference document (`memories.md`, `notes.md`,
`automations-calendar-and-timers.md`, `image-generation-and-editing.md`,
`code-execution-and-interpreter.md`).

## 7. Settings and Configuration

All values below are **code defaults**. Persistent settings are rows in the `config` table, seeded
from the environment on first start; after that the stored value wins. **Live production values
are TO BE CONFIRMED** (`ground-truth.md`, Settings).

### 7.1 Persistent Settings That Affect Built-In Tools

| Setting key | Environment variable | Code default | Where admins change it | Effect here | Source |
|---|---|---|---|---|---|
| `chat.tool_permissions.enable` | `ENABLE_TOOL_PERMISSIONS` | off | Admin Settings › Interface › Chat › **Tool Permissions** | Makes **Full access**/**Ask for approval** available; off means every chat runs with full access | `backend/open_webui/config.py:2196`, `:3138`; `backend/open_webui/main.py:1255-1264` |
| `subagents.enable` | `ENABLE_SUBAGENTS` | off | Admin Settings › Sub-agents › **Enable sub-agents** | Offers `delegate_task` and `timer` | `backend/open_webui/config.py:2036`, `:3108`; `backend/open_webui/utils/tools.py:648-654` |
| `subagents.background_enabled` | `SUBAGENTS_BACKGROUND_ENABLED` | off | same panel, **Enable background sub-agents** | When off, the `background` option is removed from `delegate_task` | `backend/open_webui/config.py:2037`; `backend/open_webui/utils/tools.py:789-793` |
| `subagents.max_concurrent`, `.max_async`, `.max_iterations`, `.max_output`, `.system_prompt` | `SUBAGENTS_*` | 20, 20, 30, 30,000, empty | same panel | Sub-agent limits; see `chat-completion-pipeline-and-generation-tasks.md` 5.14 | `backend/open_webui/config.py:2038-2042`, `:3110-3114` |
| `memories.enable` | `ENABLE_MEMORIES` | on | Admin Settings › General › **Memories** | Memory tools | `backend/open_webui/config.py:426`, `:2844` |
| `web.search.enable` | `ENABLE_WEB_SEARCH` | **off** | Admin Settings › Web Search › **Web Search** | `search_web`, `fetch_url` | `backend/open_webui/config.py:1161`, `:2941` |
| `web.search.engine`, `web.search.result_count` | `WEB_SEARCH_ENGINE`, `WEB_SEARCH_RESULT_COUNT` | empty (none chosen), 3 | Admin Settings › Web Search | Provider used and result cap for `search_web` | `backend/open_webui/config.py:1170`, `:1179`, `:2944-2947`; `backend/open_webui/tools/builtin.py:312-317` |
| `web.fetch.max_content_length` | `WEB_FETCH_MAX_CONTENT_LENGTH` | no limit | Admin Settings › Web Search › **Fetch URL Content Length Limit** (`src/lib/components/admin/Settings/WebSearch.svelte:1171-1177`; `src/lib/i18n/locales/en-US/translation.json:2662`); *corrected 2026-10-08 from "environment"* | Cuts `fetch_url` text | `backend/open_webui/config.py:1198-1200`, `:2950`; `backend/open_webui/tools/builtin.py:352-355` |
| `image_generation.enable` | `ENABLE_IMAGE_GENERATION` | **off** | Admin Settings › Images › **Image Generation** | `generate_image` | `backend/open_webui/config.py:1351`, `:3019` |
| `images.edit.enable` | `ENABLE_IMAGE_EDIT` | **off** | Admin Settings › Images › **Image Edit** | `edit_image` | `backend/open_webui/config.py:1525`, `:3039` |
| `code_interpreter.enable` | `ENABLE_CODE_INTERPRETER` | on | Admin Settings › Code Execution › **Enable Code Interpreter** | `execute_code` | `backend/open_webui/config.py:424`, `:2843` |
| `code_interpreter.engine` | `CODE_INTERPRETER_ENGINE` | `pyodide` (in the browser) | Admin Settings › Code Execution | Where `execute_code` runs (`pyodide` or `jupyter`) | `backend/open_webui/config.py:433`, `:2850`; `backend/open_webui/tools/builtin.py:688-742` |
| `notes.enable` | `ENABLE_NOTES` | on | Admin Settings › General › **Notes** | Notes tools | `backend/open_webui/config.py:2050`, `:3118` |
| `channels.enable` | `ENABLE_CHANNELS` | **off** | Admin Settings › General › **Channels** | Channel tools | `backend/open_webui/config.py:2028`, `:3104` |
| `automations.enable` | `ENABLE_AUTOMATIONS` | on | Admin Settings › General › **Automations** | Automation tools | `backend/open_webui/config.py:2034`, `:3107` |
| `automations.max_count`, `automations.min_interval` | `AUTOMATION_MAX_COUNT`, `AUTOMATION_MIN_INTERVAL` | empty (no limit) | environment | Limits applied by `create_automation` and `update_automation` for non-admins | `backend/open_webui/config.py:2044-2046`, `:3115-3116`; `backend/open_webui/routers/automations.py:69-95` |
| `calendar.enable` | `ENABLE_CALENDAR` | on | Admin Settings › General › **Calendar** | Calendar tools | `backend/open_webui/config.py:2032`, `:3106` |
| `ui.enable_user_webhooks` | `ENABLE_USER_WEBHOOKS` | **off** | Admin Settings › General › **User Webhooks** | `notify` | `backend/open_webui/config.py:2100`, `:3125` |
| `user.permissions` | `USER_PERMISSIONS_*` | see 3.2 | Admin Panel › Users › Groups | `features.*` and `chat.file_upload` gates | `backend/open_webui/config.py:1857`, `:1904-1934` |
| `models.default_metadata` | `DEFAULT_MODEL_METADATA` | empty | Admin Settings › Models › **Model Defaults** | Default capabilities and Builtin Tools groups for every model | `backend/open_webui/config.py:1696-1701`, `:3094` |
| `rag.top_k` and the other retrieval settings | `RAG_TOP_K` … | 3 | Admin Settings › Documents | Result cap and search method for `query_chat_files` | `backend/open_webui/config.py:968`, `:2899`; `backend/open_webui/tools/builtin.py:2564-2602` |
| `ui.default_interface_settings` | `DEFAULT_INTERFACE_SETTINGS` | empty | Admin Settings › General (user interface defaults) | Can set **Hide Processing Details** for everyone by default | `backend/open_webui/config.py:1713-1718`; `backend/open_webui/routers/auths.py:115` |

### 7.2 Environment-Only Settings

| Variable | Code default | Effect | Source |
|---|---|---|---|
| `CHAT_RESPONSE_MAX_TOOL_CALL_ITERATIONS` (old name `CHAT_RESPONSE_MAX_TOOL_CALL_RETRIES`) | 256; `-1` means no limit | Rounds of tool calls per reply before `Tool-call limit reached ({max_tool_call_iterations} iterations).` | `backend/open_webui/env.py:1080-1098` |
| `ENABLE_KB_EXEC` | off | Replaces the knowledge browsing tools with `kb_exec` | `backend/open_webui/env.py:968` |
| `KNOWLEDGE_GREP_MAX_MATCHES` | 50 | Matching lines returned by `grep_knowledge_files`, `grep_chat_files` and `kb_exec` grep | `backend/open_webui/env.py:1176-1177` |
| `VIEW_FILE_DEFAULT_MAX_CHARS`, `VIEW_FILE_MAX_CHARS` | 10,000 and 100,000 | Characters returned by `view_file` and `view_knowledge_file` | `backend/open_webui/env.py:1178-1180` |
| `KB_EXEC_MAX_OUTPUT_CHARS`, `KB_EXEC_MAX_GREP_FILES` | 30,000 and 200 | `kb_exec` limits | `backend/open_webui/env.py:1172-1175` |
| `TIMER_POLL_INTERVAL` | 1 second (minimum 1) | How often due timers are checked | `backend/open_webui/utils/automations.py:54`, `:99` |
| `SCHEDULER_POLL_INTERVAL` (old name `AUTOMATION_POLL_INTERVAL`) | 10 seconds | How often due automations and calendar alerts are checked | `backend/open_webui/utils/automations.py:53` |
| `CODE_INTERPRETER_BLOCKED_MODULES` | empty | Python modules whose import `execute_code` restricts | `backend/open_webui/config.py:462-464`; `backend/open_webui/tools/builtin.py:660-686` |
| `WEBSOCKET_EVENT_CALLER_TIMEOUT` | empty (no time limit); 300 seconds if the value is not a number | How long the server waits for the browser to answer an event call (in-browser `execute_code`, `ask_user` on the live path) | `backend/open_webui/env.py:534-542`; `backend/open_webui/socket/main.py:1268-1281` |

`ENABLE_PLUGINS` and `SAFE_MODE` affect workspace tools and functions, not built-in tools: the
plugin switch is checked only for selected workspace tools (`backend/open_webui/utils/middleware.py:3015-3016`;
`backend/open_webui/utils/tools.py:269-270`), and nothing in `get_builtin_tools` reads either.

### 7.3 Limits Fixed in Code

| Limit | Value | Source |
|---|---|---|
| Questions per `ask_user` call | 1 to 3, each with 2 or 3 options | `backend/open_webui/utils/ask_user.py:27-28`, `:45-46` |
| `ask_user` text lengths | id 64, header 48 (default `Question {n}`), question 500, option label 80, option description 240 characters (longer text is cut) | `backend/open_webui/utils/ask_user.py:37`, `:52-53`, `:58`, `:65` |
| `ask_user` live-path timeout | 60,000 to 240,000 ms, default 120,000 | `backend/open_webui/utils/ask_user.py:72-74` |
| `ask_user` calls per step | one, and alone | `backend/open_webui/utils/ask_user.py:9-22` |
| Output preview in a tool-call entry | 10,000 characters, then `Show all ({{COUNT}} characters)` | `src/lib/components/common/ToolCallDisplay.svelte:44`, `:344-362` |
| Knowledge bases scanned without attachments | 50 (`query_knowledge_files`), 200 (`grep_knowledge_files`), up to 10,000 (`query_knowledge_bases`) | `backend/open_webui/tools/builtin.py:3290-3299`, `:2716-2725`, `:75` |
| Files listed per `list_knowledge` page | 200 at most (50 by default) | `backend/open_webui/tools/builtin.py:3053` |
| Lines returned by a `view_file` line range without an end | 100 | `backend/open_webui/tools/builtin.py:2815`, `:2955` |
| Timers fired per check | 10 | `backend/open_webui/utils/automations.py:93` |
| Calendar event without an end time | lasts 1 hour; reminder 10 minutes before | `backend/open_webui/tools/builtin.py:4324-4338` |
| Default result counts | `search_notes`, `search_chats`, `search_channels`, `search_memories`, `search_knowledge_bases`, `search_knowledge_files`, `query_knowledge_files`, `query_knowledge_bases`: 5; `search_channel_messages`, `list_knowledge_bases`, `list_automations`, `search_calendar_events`: 10 | function signatures in `backend/open_webui/tools/builtin.py` |

### 7.4 Per-Model and Per-Chat Controls

| Control | Where | Effect | Source |
|---|---|---|---|
| **Builtin Tools** capability | Model editor › Capabilities | All built-in tools on or off | `src/lib/components/workspace/Models/Capabilities.svelte:57-60` |
| **Builtin Tools** groups (sixteen) | Model editor, shown when the capability is on | Each family on or off | `src/lib/components/workspace/Models/BuiltinTools.svelte:11-77` |
| **Web Search**, **Image Generation**, **Code Interpreter**, **Memory**, **File Upload**, **File Context**, **Citations** capabilities | Model editor › Capabilities | Gate the matching families (3.2); Citations decides whether tool results become citations | `src/lib/components/workspace/Models/Capabilities.svelte:12-60`; `backend/open_webui/utils/middleware.py:5840-5843` |
| Default features | Model editor, under Capabilities | Turns the composer's web search, image or code interpreter toggle on by default for that model | `src/lib/components/workspace/Models/ModelEditor.svelte:1249-1261`; `src/lib/components/chat/Chat.svelte:1084-1106` |
| **Function Calling** (`Default`, `Native`, `Legacy`) | Advanced parameters: personal Settings › General, the chat's controls, the model editor, or the admin's **Model Parameters** default for every model (Admin Settings › Models › Model Defaults) | `Legacy` removes all built-in tools; the person's or chat's value wins over the model's, which wins over the admin default (`backend/open_webui/main.py:1170-1177`). Description: `Native mode (default) leverages the model's built-in tool-calling capabilities. Legacy mode works with a wider range of models by calling tools once before execution via prompt injection.` | `src/lib/components/chat/Settings/Advanced/AdvancedParams.svelte:239-268`; `src/lib/i18n/locales/en-US/translation.json:2825-2826`; `backend/open_webui/main.py:1290-1294` |

## 8. Cron Jobs and Background Processes

There is no crontab. Built-in tools run **inside the chat reply** that called them, in the web
server process that is handling that reply (`backend/open_webui/utils/middleware.py:5891-6060`).
Three things in this area happen outside that moment:

| What | How it runs | Interval or trigger | Source |
|---|---|---|---|
| **Due timers** (`timer`) | The `scheduler_worker_loop` asyncio task, started in every server process at startup, claims up to ten due timers per check and starts each in its own task | Every `TIMER_POLL_INTERVAL` seconds (default 1) | `backend/open_webui/main.py:403-405`; `backend/open_webui/utils/automations.py:69-126`; `backend/open_webui/utils/timers.py:171-199`, `:230-419` |
| **Automations created by `create_automation`** | The same loop runs due automations | Every `SCHEDULER_POLL_INTERVAL` seconds (default 10) plus up to 2 seconds of jitter, when `automations.enable` is on | `backend/open_webui/utils/automations.py:101-118`; `automations-calendar-and-timers.md` |
| **Calendar reminders for events created by the calendar tools** | The same loop checks calendar alerts | Same interval, when `calendar.enable` is on | `backend/open_webui/utils/automations.py:120-124` |
| **Background sub-agents** (`delegate_task` with background on) | An asyncio task per sub-agent; the parent chat continues when it finishes | On demand | `chat-completion-pipeline-and-generation-tasks.md` 5.14 |

**Happens at save time, not in the background:**

- Approving, denying or answering a paused tool call resumes the reply immediately as part of
  the `/resolve` request; nothing waits on a schedule (`backend/open_webui/main.py:1893-1910`).
- A paused reply has no background task while it waits: the reply's task ends at the pause and a
  new one starts on resume (`backend/open_webui/utils/middleware.py:5941-5956`;
  `backend/open_webui/utils/tool_approval.py:131-186`).
- Timer cancellation happens when the chat is read or a message is sent
  (`backend/open_webui/socket/main.py:610-638`; `backend/open_webui/main.py:1539-1547`).

**Several server processes.** Every process runs the scheduler loop. On PostgreSQL a due timer is
claimed with a row lock that other processes skip (`backend/open_webui/utils/timers.py:181-182`);
the per-timer lock is held in each process's memory (`:36`, `:231-232`). Whether two processes can
claim the same timer on SQLite is not established by the code and is listed in section 14.

## 9. Notifications and Emails

The application sends **no email** (`ground-truth.md`). In this area, messages leave the chat only
in the ways below.

### 9.1 The `notify` Tool (Personal Webhooks)

`notify` posts a message to one of the person's own notification targets, the webhooks they set in
Settings › Notifications. It is offered only when the admin has switched on **User Webhooks** and
the person has the `features.webhooks` permission (both off in code) (`backend/open_webui/utils/tools.py:759-764`).

- **Target.** The target named by the model (matched by its id, ignoring case) or, when none is
  named, the person's default target; a target that is switched off is refused
  (`backend/open_webui/utils/notifications.py:234-243`, `:370-382`).
- **Content.** The title (default `Notification`), the message, and data
  `{"action": "notify", "user_id": ..., "message": ..., "title": ...}`, sent under the
  application's name (`WEBUI_NAME`, which defaults to `MedIT GPT` on this fork)
  (`backend/open_webui/utils/notifications.py:383-389`; `backend/open_webui/tools/builtin.py:149-155`;
  `backend/open_webui/env.py:951`). A generic webhook receives that data as the request body,
  including the person's user id; Slack, Google Chat and Discord addresses receive text only, and
  Microsoft Teams a message card (`backend/open_webui/utils/webhook.py:40-90`).
- **Result to the model.** `Notification sent to {target_id}.` or `Notification failed: {e}`,
  where the reason can be `Notification target not found`, `Notification target is disabled`,
  `Webhook URL is required` or `Webhook delivery failed`
  (`backend/open_webui/tools/builtin.py:145-158`; `backend/open_webui/utils/notifications.py:254-261`).

The webhook system itself is documented in `notifications-webhooks-events-and-banners.md`.

### 9.2 Live Updates Sent to the Browser

| Event | Sent when | Effect for the person | Source |
|---|---|---|---|
| `chat:message:files` | `generate_image` or `edit_image` produced images | The images appear in the reply | `backend/open_webui/tools/builtin.py:414-423`, `:487-496` |
| `chat:message:tasks` | `create_tasks` or `update_task` | The checklist above the message box updates | `backend/open_webui/tools/builtin.py:3580-3590`; `src/lib/components/chat/Chat.svelte:1271-1272` |
| `events:note` (to everyone viewing the note) | `replace_note_content` changed a note | Open copies of the note refresh | `backend/open_webui/tools/builtin.py:94-102` |
| `chat:completion` with the reply's output | A call pauses for approval or a question, or is resolved | The entry shows **Allow**/**Deny**, the question card, or the new state | `backend/open_webui/utils/middleware.py:5913`, `:5948-5955`; `backend/open_webui/utils/tool_approval.py:107-116` |
| `chat:tasks:cancel` | **Stop** closed a paused reply | The browser stops waiting | `backend/open_webui/main.py:2210-2212` |
| `chat:reload` | A timer fired in the chat | The chat reloads and shows the **Timer** row and the new reply | `backend/open_webui/utils/timers.py:367-375` |
| `request:user_input` (a request the browser answers) | `ask_user` on the live path | The question card opens with a time limit | `backend/open_webui/tools/builtin.py:598-607`; `src/lib/components/chat/Chat.svelte:1402-1408` |
| `execute:python` (a request the browser answers) | `execute_code` with the Pyodide engine | The code runs in the person's browser | `backend/open_webui/tools/builtin.py:696-706` |

### 9.3 Application Events

Some tools cause events on the application's event bus, which is delivered to its event sinks
(the browser session, event functions, admin event webhooks and personal notifications)
(`backend/open_webui/events.py:1171-1202`): note updates (`replace_note_content`); memory
created, updated and deleted events from `add_memory`, `update_memory` and
`replace_memory_content`, which go through the memory router (`delete_memory` deletes directly and
publishes no event) (`backend/open_webui/tools/builtin.py:94-102`, `:1053-1082`;
`backend/open_webui/routers/memories.py:224`, `:306`, `:595`). As for every reply, the
finished-chat event follows at the end, whether or not tools were used
(`backend/open_webui/utils/middleware.py:206-235`). Which events reach which webhook is
covered in `notifications-webhooks-events-and-banners.md`.

Calendar reminders for events created with the calendar tools are sent by the calendar alert
loop (section 8), not by the tools.

## 10. Error, Warning and Notice Messages (Verbatim)

Plain i18n keys display as written; `{{NAME}}` and `{{COUNT}}` are filled in by the interface.
Dotted keys are resolved from `src/lib/i18n/locales/en-US/translation.json`. Most tool messages in
10.3 to 10.5 are **returned to the model**, not shown as pop-ups: the person sees them only by
opening the tool-call entry's **Output**, and the model usually paraphrases them in its answer.
Messages from the resolve endpoint (10.6) appear as red pop-ups (toasts) printing the server's
`detail` (`src/lib/components/chat/Chat.svelte:496`, `:575`, `:593`;
`src/lib/components/chat/Messages/StructuredOutputRenderer.svelte:60`;
`src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte:136`).

### 10.1 In the Chat (Tool-Call Entries, Approval, Question Card, Checklist)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Preparing {{NAME}}...` | Info | `src/lib/components/common/ToolCallDisplay.svelte:251` | The model is still writing the call | Wait | none |
| `Executing {{NAME}}...` | Info | `src/lib/components/common/ToolCallDisplay.svelte:253` | The tool is running | Wait | If it never finishes, see 11.9 |
| `View Result from {{NAME}}` | Info (green tick, or red cross on error) | `src/lib/components/common/ToolCallDisplay.svelte:245` | The tool finished | Click to see **Input** and **Output** | A red cross means the output looks like an error (4.2) |
| `Allow {{NAME}}?` | Notice (action needed) | `src/lib/components/common/ToolCallDisplay.svelte:249` | **Ask for approval** mode; the call waits | **Allow** or **Deny**; open it to check the input | 5.4 |
| `Allow` | Button | `src/lib/components/common/ToolCallDisplay.svelte:266`; `src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte:243`, `:284` | Waiting call | Runs the call | none |
| `Deny` | Button | `src/lib/components/common/ToolCallDisplay.svelte:274`; `src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte:251`, `:292` | Waiting call | Refuses the call; the model is told | none |
| `Denied {{NAME}}` | Warning (red cross) | `src/lib/components/common/ToolCallDisplay.svelte:243` | The person denied the call, cancelled a question, or pressed Stop while it waited | none | 5.4 |
| `Input needed` | Notice | `src/lib/components/common/ToolCallDisplay.svelte:247` | An `ask_user` question waits (where the entry is shown) | Answer in the card above the message box | 5.5 |
| `Input` | Label | `src/lib/components/common/ToolCallDisplay.svelte:301` | Entry opened | none | The arguments the model sent |
| `Output` | Label | `src/lib/components/common/ToolCallDisplay.svelte:334` | Entry opened after the tool finished | none | What the tool returned (10.3) |
| `Show all ({{COUNT}} characters)` | Button | `src/lib/components/common/ToolCallDisplay.svelte:358-360` | Output longer than 10,000 characters | Click to show all | none |
| `Exploring` | Info | `src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte:177` | Group of entries with one still running | Wait | none |
| `Explored` | Info | `src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte:177` | Group of finished entries; followed by tool names and counts | Click to open | none |
| `Ran {{COUNT}} analysis` | Info | `src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte:167` | One code-analysis block in the group | none | none |
| `Ran {{COUNT}} analyses` | Info | `src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte:169` | Several code-analysis blocks | none | none |
| `Toggle details` | Accessible name | `src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte:188` | Group line (screen readers) | none | none |
| `tool` | Label | `src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte:274` | A waiting call has no name | none | none |
| `Sub-agent` / `Background sub-agent` (shown as `Sub-agent: "{task}"`) | Label | `src/lib/components/chat/Messages/structuredOutput.ts:202-213` | A `delegate_task` entry | none | 5.7 |
| `Background sub-agent finished` | Info | `src/lib/components/chat/Messages/SubagentResultRow.svelte:41` | A background sub-agent's result arrived in the chat | none | 5.7 |
| `Timer` | Label | `src/lib/components/chat/Messages/UserMessage.svelte:356` | A timer fired and its prompt was added | Click to read the prompt | 5.8 |
| `Thinking...` | Info | `src/lib/components/chat/Messages/ResponseMessage.svelte:921` | **Hide Processing Details** is on and the reply is still working | Wait | 5.6 |
| `out of` … `tasks completed` (shown, for example, as 2 out of 5 tasks completed) | Info | `src/lib/components/chat/Messages/ResponseMessage/TaskList.svelte:28-33` | The model keeps a checklist and the reply is running | none | 5.9 |
| `Tasks` | Label | `src/lib/components/chat/MessageInput.svelte:1867` | Chat status panel, when a checklist exists | none | none |
| `Recommended` | Label | `src/lib/components/chat/AskUserCard.svelte:227` | First option of a question | none | The model chose the order |
| `Other` | Label | `src/lib/components/chat/AskUserCard.svelte:241` | Free-text answers allowed | Type an answer | none |
| `Type your answer` | Placeholder | `src/lib/components/chat/AskUserCard.svelte:245` | As above | none | none |
| `Cancel` | Button | `src/lib/components/chat/AskUserCard.svelte:271` | Question card | Refuses the question | The model receives `Error: tool call rejected by user.` |
| `Previous` | Button | `src/lib/components/chat/AskUserCard.svelte:279` | Several questions | Go back | none |
| `Next` | Button | `src/lib/components/chat/AskUserCard.svelte:288` | Several questions, not on the last | Go forward | none |
| `Submit answers` | Button | `src/lib/components/chat/AskUserCard.svelte:297` | Last question; enabled when all are answered | Send answers | none |
| `Question {n}` (header when the model gives none) | Label | `backend/open_webui/utils/ask_user.py:65`; `backend/open_webui/tools/builtin.py:579` | Question without a header | none | none |
| `Tool Permissions` | Menu entry | `src/lib/components/chat/MessageInput/InputMenu.svelte:167`, `:559` | Admin switch **Tool Permissions** on | Opens the mode choice | Not shown at all when the admin switch is off |
| `Full access` | Menu choice | `src/lib/components/chat/MessageInput/InputMenu.svelte:58`, `:173-175` | As above | Tools run without asking | none |
| `Run tools without asking for approval.` | Tooltip | `src/lib/components/chat/MessageInput/InputMenu.svelte:59` | Hovering **Full access** | none | none |
| `Ask for approval` | Menu choice | `src/lib/components/chat/MessageInput/InputMenu.svelte:63` | As above | Each tool call waits | none |
| `Stop before each tool call until you allow or deny it.` | Tooltip | `src/lib/components/chat/MessageInput/InputMenu.svelte:64` | Hovering **Ask for approval** | none | none |

### 10.2 Settings Screens

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Builtin Tools` (capability) | Label | `src/lib/components/workspace/Models/Capabilities.svelte:58`; `src/lib/i18n/locales/en-US/translation.json:2574` | Model editor › Capabilities | Tick to allow built-in tools | none |
| `Automatically inject system tools in native function calling mode (e.g., timestamps, memory, chat history, notes, etc.)` | Tooltip | `src/lib/components/workspace/Models/Capabilities.svelte:59`; `src/lib/i18n/locales/en-US/translation.json:2573` | Hovering the capability | none | none |
| `Builtin Tools` (group list title) | Heading | `src/lib/components/workspace/Models/BuiltinTools.svelte:95`; `src/lib/i18n/locales/en-US/translation.json:2568` | Model editor or Model Defaults, when the capability is on | none | none |
| `Time & Calculation` / `Get current time and perform date/time calculations` | Label / tooltip | `src/lib/components/workspace/Models/BuiltinTools.svelte:14-15`; `src/lib/i18n/locales/en-US/translation.json:2566-2567` | Group list | Untick to remove the group | none |
| `Ask User` / `Pause a response to ask the user a clarifying question` | Label / tooltip | `BuiltinTools.svelte:18-19`; `translation.json:2569-2570` | As above | As above | none |
| `Memory` / `Search and manage user memories` | Label / tooltip | `BuiltinTools.svelte:22-23`; `translation.json:2556-2557` | As above | As above | none |
| `Chat History` / `Search and view user chat history` | Label / tooltip | `BuiltinTools.svelte:26-27`; `translation.json:2546-2547` | As above | As above | none |
| `Notes` / `Search, view, and manage user notes` | Label / tooltip | `BuiltinTools.svelte:30-31`; `translation.json:2558-2559` | As above | As above | none |
| `Knowledge Base` / `Browse and query knowledge bases` | Label / tooltip | `BuiltinTools.svelte:34-35`; `translation.json:2554-2555` | As above | As above | none |
| `Files` / `List, search, and read files attached to the current chat` | Label / tooltip | `BuiltinTools.svelte:38-39`; `translation.json:2550-2551` | As above | As above | none |
| `Channels` / `Search channels and channel messages` | Label / tooltip | `BuiltinTools.svelte:42-43`; `translation.json:2544-2545` | As above | As above | none |
| `Notifications` / `Send notifications to configured webhook targets` | Label / tooltip | `BuiltinTools.svelte:46-47`; `translation.json:2560-2561` | As above | As above | none |
| `Web Search` / `Search the web and fetch URLs` | Label / tooltip | `BuiltinTools.svelte:50-51`; `translation.json:2571-2572` | As above | As above | none |
| `Image Generation` / `Generate and edit images` | Label / tooltip | `BuiltinTools.svelte:54-55`; `translation.json:2552-2553` | As above | As above | none |
| `Code Interpreter` / `Execute code` | Label / tooltip | `BuiltinTools.svelte:58-59`; `translation.json:2548-2549` | As above | As above | none |
| `Task Management` / `Break down complex requests into trackable steps` | Label / tooltip | `BuiltinTools.svelte:62-63`; `translation.json:2564-2565` | As above | As above | none |
| `Automations` / `Create and manage scheduled automations` | Label / tooltip | `BuiltinTools.svelte:66-67`; `translation.json:2540-2541` | As above | As above | none |
| `Calendar` / `List calendars, search, create, update, and delete calendar events` | Label / tooltip | `BuiltinTools.svelte:70-71`; `translation.json:2542-2543` | As above | As above | The description mentions listing calendars, but no built-in tool lists calendars (4.3) |
| `Sub-agents` / `Delegate focused work to parallel sub-agents` | Label / tooltip | `BuiltinTools.svelte:74-75`; `translation.json:2562-2563` | As above | As above | Also governs `timer` (5.8) |
| `Tool Permissions` / `Show Full access and Ask for approval in the chat input menu.` | Label / description | `src/lib/components/admin/Settings/Interface.svelte:259-265`; `src/lib/i18n/locales/en-US/translation.json:2532-2533` | Admin Settings › Interface › Chat | Switch on to allow approval mode | Shown with an **Experimental** badge |
| `Experimental` | Badge | `src/lib/components/common/ExperimentalBadge.svelte:12` | Next to Tool Permissions | none | none |
| `Hide Processing Details` | Label | `src/lib/components/common/InterfaceSettings.svelte:1361`; `src/lib/i18n/locales/en-US/translation.json:2924` | Settings › Interface (and admin user defaults) | Switch | 5.6 |
| `Show "Thinking..." instead of status updates, tool calls, reasoning, and code analysis while a response is generated, and keep them hidden afterwards. Tool approval requests and images or embeds from tools still appear.` | Description | `src/lib/components/common/InterfaceSettings.svelte:1377`; `src/lib/i18n/locales/en-US/translation.json:2923` | As above | none | Wording changed in the uncommitted working tree (section 12) |
| `Function Calling` / `Native mode (default) leverages the model's built-in tool-calling capabilities. Legacy mode works with a wider range of models by calling tools once before execution via prompt injection.` | Label / tooltip | `src/lib/components/chat/Settings/Advanced/AdvancedParams.svelte:241`, `:247`; `src/lib/i18n/locales/en-US/translation.json:2825-2826` | Advanced parameters | `Default`, `Native`, `Legacy` | `Legacy` removes built-in tools |

### 10.3 Tool Results Returned to the Model (`backend/open_webui/tools/builtin.py`)

Unless stated, each is returned as JSON `{"error": "<message>"}` and the entry shows a red cross.
"Support check" assumes tier 1 can see the entry's **Output** in the person's chat or a screenshot.
Crashes inside a tool return the raw exception text instead (`{"error": "<exception>"}`), which
can be anything; those are worth escalating with the chat id.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Request context not available` | Error (internal) | `backend/open_webui/tools/builtin.py:309`, `:345`, `:385`, `:458`, `:654`, `:885`, `:943`, `:989`, `:1022`, `:1065`, `:1095`, `:1145`, `:1236`, `:1300`, `:1363`, `:1535`, `:1623`, `:1777`, `:1834`, `:1908`, `:1969`, `:2061`, `:2121`, `:2185`, `:2424`, `:2474`, `:2527`, `:2652`, `:2773`, `:2885`, `:3031`, `:3170`, `:3388`, `:3496`, `:3740`, `:3839`, `:3937`, `:4005`, `:4056`, `:4170`, `:4269`, `:4396`, `:4500` | The tool was called without the server's request context (not expected from the chat page) | Retry | Escalate with chat id if it repeats |
| `User context not available` | Error (internal) | `backend/open_webui/tools/builtin.py:1148`, `:1239`, `:1303`, `:1366`, `:1538`, `:1626`, `:1780`, `:1837`, `:1911`, `:1972`, `:2064`, `:2124`, `:2188`, `:2427`, `:2477`, `:2530`, `:2655`, `:2776`, `:2888`, `:3034`, `:3173`, `:3391`, `:3499`, `:3743`, `:3842`, `:3940`, `:4008`, `:4059`, `:4173`, `:4272`, `:4399`, `:4503` | Called without the person's account details | Retry | As above |
| `Access denied` | Error | `backend/open_webui/tools/builtin.py:1264`, `:1931`, `:1992`, `:2942`, `:3534`, `:3859`, `:4022`, `:4070`, `:4416`, `:4425`, `:4520`, `:4529` | The person cannot read that note, channel message, file or skill, or does not own that automation, or cannot edit that calendar event | Ask the owner to share it, or use your own item | Check sharing of the item named in the entry's **Input** |
| `Notification failed: user not found.` | Error | `backend/open_webui/tools/builtin.py:147` | `notify` without an account | Retry | Escalate |
| `Notification sent to {target_id}.` | Success (plain text) | `backend/open_webui/tools/builtin.py:156` | `notify` delivered | none | none |
| `Notification failed: {e}` | Error (plain text) | `backend/open_webui/tools/builtin.py:158` | Delivery failed; `{e}` is a reason from 10.7 | Check Settings › Notifications | 11.11 |
| `The image has been successfully generated and is already visible to the user in the chat. You do not need to display or embed the image again - just acknowledge that it has been created.` | Success (to the model) | `backend/open_webui/tools/builtin.py:428` | `generate_image` succeeded | none | none |
| `The edited image has been successfully generated and is already visible to the user in the chat. You do not need to display or embed the image again - just acknowledge that it has been created.` | Success (to the model) | `backend/open_webui/tools/builtin.py:501` | `edit_image` succeeded | none | none |
| `ask_user requires 1-3 questions.` | Error | `backend/open_webui/tools/builtin.py:536` (also `backend/open_webui/utils/ask_user.py:28`) | The model sent no questions or more than three | none (the model retries) | none |
| `Each question must be an object.` | Error | `backend/open_webui/tools/builtin.py:542`; `ask_user.py:35` | Malformed question | none | none |
| `Each question requires a non-empty id.` | Error | `backend/open_webui/tools/builtin.py:546`; `ask_user.py:39` | Question without an id | none | none |
| `Duplicate question id: {question_id}` | Error | `backend/open_webui/tools/builtin.py:548`; `ask_user.py:41` | Two questions share an id | none | none |
| `Each question requires 2-3 options.` | Error | `backend/open_webui/tools/builtin.py:553`; `ask_user.py:46` | Wrong number of options | none | none |
| `Each option must be an object.` | Error | `backend/open_webui/tools/builtin.py:558`; `ask_user.py:51` | Malformed option | none | none |
| `Each option requires a label and description.` | Error | `backend/open_webui/tools/builtin.py:563`; `ask_user.py:55` | Option missing text | none | none |
| `Each question requires question text.` | Error | `backend/open_webui/tools/builtin.py:574`; `ask_user.py:60` | Empty question | none | none |
| `User input requires an active browser session with WebSocket connection.` | Error | `backend/open_webui/tools/builtin.py:593` | `ask_user` on the live path with no browser connected | Keep the chat open in a browser | 5.5 |
| `Invalid user input response.` | Error | `backend/open_webui/tools/builtin.py:610` | The browser's answer was not readable | Retry | Escalate if repeated |
| `Event call not available. WebSocket connection required for pyodide execution.` | Error | `backend/open_webui/tools/builtin.py:693` | `execute_code` with the in-browser engine but no browser connection | Keep the chat open; retry | `code-execution-and-interpreter.md` |
| `Unknown code interpreter engine: {engine}` | Error | `backend/open_webui/tools/builtin.py:742` | The admin's engine setting is neither `pyodide` nor `jupyter` | none | Escalate to an admin |
| `Memory {memory_id} deleted` | Success | `backend/open_webui/tools/builtin.py:1075` | `delete_memory` succeeded | none | none |
| `Memory not found or access denied` | Error | `backend/open_webui/tools/builtin.py:1079` | The id is not one of the person's memories | none | none |
| `Note not found` | Error | `backend/open_webui/tools/builtin.py:1245`, `:1374` | `view_note` or `replace_note_content` with an unknown id | none | none |
| `Failed to create note` | Error | `backend/open_webui/tools/builtin.py:1319` | `write_note` could not save | Retry | Escalate with time |
| `Write access denied` | Error | `backend/open_webui/tools/builtin.py:1378` | `replace_note_content` on a note the person cannot edit | Ask the owner for edit access | Note sharing |
| `operations must be a non-empty list` | Error | `backend/open_webui/tools/builtin.py:1384` | Malformed note edit | none (the model retries) | none |
| `each operation must be an object` | Error | `backend/open_webui/tools/builtin.py:1390` | As above | none | none |
| `replace operation must be the only operation` | Error | `backend/open_webui/tools/builtin.py:1400` | As above | none | none |
| `replace operation content must be a string` | Error | `backend/open_webui/tools/builtin.py:1408` | As above | none | none |
| `unknown operation action` | Error | `backend/open_webui/tools/builtin.py:1419` | As above | none | none |
| `operation start and end must be integers` | Error | `backend/open_webui/tools/builtin.py:1427` | As above | none | none |
| `operation content must be a string` | Error | `backend/open_webui/tools/builtin.py:1431` | As above | none | none |
| `operation range is out of bounds` | Error | `backend/open_webui/tools/builtin.py:1435` | The model's character positions do not fit the note | none | none |
| `operation expected text does not match current content` | Error | `backend/open_webui/tools/builtin.py:1440` | The note changed since the model read it | Ask the model to reread the note | none |
| `operation ranges must not overlap` | Error | `backend/open_webui/tools/builtin.py:1453` | As above | none | none |
| `content or operations is required` | Error | `backend/open_webui/tools/builtin.py:1463` | Nothing to write | none | none |
| `Failed to update note` | Error | `backend/open_webui/tools/builtin.py:1488` | Save failed | Retry | Escalate with time |
| `Chat not found or access denied` | Error | `backend/open_webui/tools/builtin.py:1634` | `view_chat` on a chat that is not the person's own | none | Admins cannot read others' chats through this tool either |
| `Error: request context not available.` | Error (plain text) | `backend/open_webui/tools/builtin.py:1702`, `:1740` | `delegate_task` or `timer` without context | Retry | Escalate |
| `Error: sub-agents cannot delegate recursively.` | Error (plain text) | `backend/open_webui/tools/builtin.py:1704` | A sub-agent tried to start another | none | 5.7 |
| `Error: timers cannot be set from internal chats.` | Error (plain text) | `backend/open_webui/tools/builtin.py:1742` | A sub-agent tried to set a timer | none | 5.8 |
| `Message not found` | Error | `backend/open_webui/tools/builtin.py:1919`, `:1981` | Unknown channel message id | none | none |
| `Channel not found` | Error | `backend/open_webui/tools/builtin.py:1924`, `:1986` | The message's channel no longer exists | none | none |
| `Knowledge base {knowledge_id} is not attached to this model` | Error | `backend/open_webui/tools/builtin.py:2215` | The model named a knowledge base outside its attached knowledge | none | `knowledge-bases.md` 5.22 |
| `Access denied to knowledge base {knowledge_id}` | Error | `backend/open_webui/tools/builtin.py:2291` | The person cannot read that knowledge base | Ask the owner to share it | Knowledge base sharing |
| `No matches for "{pattern}"` | Info (plain text) | `backend/open_webui/tools/builtin.py:2401`, `:2405` | A grep found nothing | none | none |
| `[{total_matches} total matches]` | Info (plain text) | `backend/open_webui/tools/builtin.py:2402` | Grep with counts only | none | none |
| `[{KNOWLEDGE_GREP_MAX_MATCHES} of {total_matches} matches shown — use file_id to narrow]` | Notice (plain text) | `backend/open_webui/tools/builtin.py:2409` | More than 50 matching lines | none | none |
| `Pattern is required` | Error | `backend/open_webui/tools/builtin.py:2480`, `:2658` | Empty search pattern | none | none |
| `No files are attached to this chat` | Error | `backend/open_webui/tools/builtin.py:2495`, `:2555` | Chat-file tool with no uploaded files | Attach the file to the chat | none |
| `File not found` | Error | `backend/open_webui/tools/builtin.py:2497`, `:2557`, `:2676`, `:2799`, `:2802`, `:2917` | Unknown file, a file not attached to this chat, or (deliberately the same text) a file the person may not read | Re-attach the file | Check the file's owner and sharing |
| `No accessible files found` | Error | `backend/open_webui/tools/builtin.py:2501`, `:2561`, `:2741` | None of the files can be read by the person | As above | As above |
| `Embedding function not configured` | Error | `backend/open_webui/tools/builtin.py:2578`, `:3208`, `:3404` | The server has no embedding model loaded | none | Escalate: retrieval set-up (`rag-retrieval-embeddings-and-vector-stores.md`) |
| `Skill '{id}' not found` | Error | `backend/open_webui/tools/builtin.py:3509`, `:3521` | Unknown or inactive skill | none | Check the skill is active |
| `Saved chat context not available` | Error | `backend/open_webui/tools/builtin.py:3608`, `:3660` | Task tools in a chat that is not saved | none | none |
| `Invalid status: {status}. Must be one of: {", ".join(sorted(VALID_TASK_STATUSES))}` (reads `… Must be one of: cancelled, completed, in_progress, pending`) | Error | `backend/open_webui/tools/builtin.py:3666` | Unknown task status | none | none |
| `Task with id "{id}" not found` | Error | `backend/open_webui/tools/builtin.py:3679` | Unknown checklist item | none | none |
| `Folder not found` | Error | `backend/open_webui/tools/builtin.py:3705` (returned at `:3767`, `:3874`, `:3953`) | Automation folder is not one of the person's folders | none | none |
| `User not found` | Error | `backend/open_webui/tools/builtin.py:3754`, `:3853` | Account missing | none | Escalate |
| `Could not detect current model` | Error | `backend/open_webui/tools/builtin.py:3762` | `create_automation` could not tell which model the chat uses | Retry | Escalate |
| `Invalid schedule: {e}` | Error | `backend/open_webui/tools/builtin.py:3773`, `:3881` | The schedule rule is not valid | Rephrase the schedule | `automations-calendar-and-timers.md` |
| `Automation not found` | Error | `backend/open_webui/tools/builtin.py:3857`, `:4020`, `:4068` | Unknown automation id | none | none |
| `Automation "{name}" deleted` | Success | `backend/open_webui/tools/builtin.py:4079` | `delete_automation` succeeded | none | Deletion is permanent |
| `Invalid start datetime: {e}` | Error | `backend/open_webui/tools/builtin.py:4192`, `:4440` | Unreadable start date | none | none |
| `Invalid end datetime: {e}` | Error | `backend/open_webui/tools/builtin.py:4197`, `:4447` | Unreadable end date | none | none |
| `No calendars found. Cannot create event.` | Error | `backend/open_webui/tools/builtin.py:4286` | No calendar could be found or created for the person (a person with no calendar is normally given a `Personal` one automatically, so this is unusual) | Retry | Escalate with time; `backend/open_webui/models/calendar.py:266-289`, `:291-312` |
| `Calendar not found` | Error | `backend/open_webui/tools/builtin.py:4292` | Unknown calendar id | none | none |
| `Access denied to this calendar` | Error | `backend/open_webui/tools/builtin.py:4305` | No write access to the named calendar | Ask the owner | Calendar sharing |
| `Invalid start datetime: {e}. Use format like "2026-04-20 09:00"` | Error | `backend/open_webui/tools/builtin.py:4316` | Unreadable start date when creating | none | none |
| `Invalid end datetime: {e}. Use format like "2026-04-20 10:00"` | Error | `backend/open_webui/tools/builtin.py:4323` | Unreadable end date when creating | none | none |
| `Failed to create event` | Error | `backend/open_webui/tools/builtin.py:4353` | Save failed | Retry | Escalate with time |
| `Event not found` | Error | `backend/open_webui/tools/builtin.py:4410`, `:4514` | Unknown event id | none | none |
| `Failed to update event` | Error | `backend/open_webui/tools/builtin.py:4474` | Save failed | Retry | Escalate |
| `Failed to delete event` | Error | `backend/open_webui/tools/builtin.py:4534` | Delete failed | Retry | Escalate |
| `Event "{title}" deleted` | Success | `backend/open_webui/tools/builtin.py:4539` | `delete_calendar_event` succeeded | none | Deletion is permanent |
| `[Content truncated...]` | Notice (appended to the text) | `backend/open_webui/tools/builtin.py:355` | `fetch_url` text longer than the admin's limit | none | none |
| `Client session disconnected.` | Error (inside the result; for `execute_code` it appears as `stderr` and the entry may still show a green tick) | `backend/open_webui/socket/main.py:1266` | A tool needed the browser (in-browser code, live question) but the person's session is not connected | Keep the chat open in the browser and retry | 11.9 |
| `Event call timed out. The browser tab may be inactive or closed.` | Error (as above) | `backend/open_webui/socket/main.py:1281` | The browser did not answer within `WEBSOCKET_EVENT_CALLER_TIMEOUT` (only when that is set) | Keep the tab active and retry | 11.9 |

Messages from the search-pattern checker used by `grep_chat_files` and `grep_knowledge_files`
(`Search patterns over {MAX_SEARCH_PATTERN_LENGTH} characters are not supported`,
`Invalid or unsupported regex (RE2 syntax): {e}`, and the time-budget message) come from
`backend/open_webui/tools/knowledge_fs.py:90-128` and are listed in `knowledge-bases.md` 10.8.
Automation limit messages returned by `create_automation` and `update_automation`
(`Automation limit reached ({size})`, `Schedule too frequent. Minimum interval is {interval} seconds.`)
come from `backend/open_webui/constants.py:116-117`.

### 10.4 Timers and Ask-User Staging (`backend/open_webui/utils/timers.py`, `backend/open_webui/utils/ask_user.py`)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Error: prompt must not be empty.` | Error (to the model) | `backend/open_webui/utils/timers.py:82` | `timer` with an empty prompt | none | none |
| `Error: chat and user context are required.` | Error (to the model) | `backend/open_webui/utils/timers.py:84` | `timer` outside a chat | none | none |
| `Error: {exc}` wrapping `at must be in the future.` | Error (to the model) | `backend/open_webui/utils/timers.py:47`, `:65`, `:89` | The time is now or past | Ask for a later time | none |
| `Error: {exc}` wrapping `at must be a relative time such as 10s or in 10 seconds, or an RFC 3339 timestamp with a timezone.` | Error (to the model) | `backend/open_webui/utils/timers.py:51-53`, `:57-59`, `:89` | Unreadable time | Rephrase the time | none |
| `Error: {exc}` wrapping `absolute at values must include an explicit timezone.` | Error (to the model) | `backend/open_webui/utils/timers.py:61`, `:89` | Date-time without a time zone | none | none |
| `Error: cancel_on accepts only chat.read and chat.user_message.` | Error (to the model) | `backend/open_webui/utils/timers.py:94` | Unknown cancel event | none | none |
| `Error: model context is required.` | Error (to the model) | `backend/open_webui/utils/timers.py:99` | No model id | Retry | Escalate |
| `Error: timers are unavailable for direct connections.` | Error (to the model) | `backend/open_webui/utils/timers.py:101` | The chat uses a direct (browser-side) connection | Use a server-side model | none |
| `Error: failed to create timer.` | Error (to the model) | `backend/open_webui/utils/timers.py:159` | The timer chat could not be saved | Retry | Escalate with time |
| `parent chat no longer exists` | Stored reason (not shown) | `backend/open_webui/utils/timers.py:248`, `:293` | The chat was deleted before the timer fired | none | Visible only in the hidden timer chat's data |
| `timer task message is missing` | Stored reason | `backend/open_webui/utils/timers.py:254` | Timer record damaged | none | Escalate |
| `timer user no longer exists` | Stored reason | `backend/open_webui/utils/timers.py:259` | Account deleted | none | none |
| `owner no longer permitted to run timers` | Stored reason | `backend/open_webui/utils/timers.py:264` | The owner's role is no longer `user` or `admin` (for example set to `pending`) | none | none |
| `model context is missing` | Stored reason | `backend/open_webui/utils/timers.py:270` | No model stored | none | Escalate |
| `Error: ask_user must be the only tool call, so it did not run. Call ask_user on its own.` | Error (to the model) | `backend/open_webui/utils/ask_user.py:18` | `ask_user` combined with other tool calls | none (the model retries) | none |
| `Error: only one ask_user call is allowed per turn.` | Error (to the model) | `backend/open_webui/utils/ask_user.py:21` | Two `ask_user` calls at once | none | none |
| `Error: {exc}` wrapping `ask_user arguments must be an object.` or one of the question checks in 10.3 | Error (to the model) | `backend/open_webui/utils/ask_user.py:97-104` | Malformed question set | none | none |

### 10.5 The Tool Loop (`backend/open_webui/utils/middleware.py`)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Tool-call limit reached ({max_tool_call_iterations} iterations).` | Error (error box in the reply) | `backend/open_webui/utils/middleware.py:6339-6346` | The model kept calling tools for more rounds than the limit (default 256) | Simplify the request or start a new chat | Check `CHAT_RESPONSE_MAX_TOOL_CALL_ITERATIONS` (environment) |
| `Error: Tool "{name}" not found.` | Error (to the model) | `backend/open_webui/utils/middleware.py:5995-5997` | The model called a tool that was not offered for this message | none | Usually a switch is off (3.2) |
| `Error: Tool call arguments for '{name}' must be a JSON object. Please try again.` (backticks around the name in the source) | Error (to the model) | `backend/open_webui/utils/middleware.py:5985-5992` | Arguments were JSON but not an object | none | Model quality issue |
| `Error: Tool call arguments could not be parsed. The model generated malformed or incomplete JSON for '{tool_function_name}'. Please try again.` (backticks around the name in the source) | Error (to the model) | `backend/open_webui/utils/middleware.py:6050-6059` | Arguments were not readable | none | Model quality issue |
| `Here are the images from the tool results above. Please analyze them.` | Instruction to the model | `backend/open_webui/utils/middleware.py:6269-6281` | A tool returned images and the provider cannot take images in tool results | none | none |

### 10.6 Resolving and Stopping (`backend/open_webui/utils/tool_approval.py`, `backend/open_webui/main.py`)

These come back from `POST /api/v1/chats/{id}/messages/{message_id}/resolve` and appear as
pop-ups; the chat then reloads (`src/lib/components/chat/Chat.svelte:573-576`, `:591-594`).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 401) | `backend/open_webui/utils/tool_approval.py:28-32`; `backend/open_webui/constants.py:70-72` | Resolving a call in a chat the person does not own (and is not an admin), or a chat that is not saved | Open your own chat | 11.6 |
| `We could not find what you're looking for :/` | Error (HTTP 404) | `backend/open_webui/utils/tool_approval.py:36`, `:134`, `:138`; `backend/open_webui/constants.py:78`; also `backend/open_webui/main.py:2167`, `:2171` (Stop) | The message or chat no longer exists | Reload | none |
| `Message has no resolvable output.` | Error (HTTP 400) | `backend/open_webui/utils/tool_approval.py:40` | The message has no tool calls | Reload | none |
| `Tool call not found.` | Error (HTTP 404) | `backend/open_webui/utils/tool_approval.py:51` | Stale page | Reload | none |
| `Tool call has already been resolved.` | Error (HTTP 409) | `backend/open_webui/utils/tool_approval.py:55-58` | Clicked twice, or resolved in another tab or by Stop | Reload | none |
| `ask_user requires an answer or deny.` | Error (HTTP 400) | `backend/open_webui/utils/tool_approval.py:61-62` | An approve was sent for a question | Answer or cancel the card | none |
| `Error: tool call rejected by user.` | Result saved for the model | `backend/open_webui/utils/tool_approval.py:65-75` | **Deny**, or **Cancel** on a question card | none | none |
| `Tool call does not accept answers.` | Error (HTTP 400) | `backend/open_webui/utils/tool_approval.py:77-78` | Answers sent for a call that is not `ask_user` | Reload | none |
| `Answers are required for ask_user.` | Error (HTTP 400) | `backend/open_webui/utils/tool_approval.py:79-80` | Empty answer | Answer every question | none |
| `Tool call parent message is missing.` | Error (HTTP 409) | `backend/open_webui/utils/tool_approval.py:142-143` | The question that led to the reply was deleted | Start a new message | Escalate with chat id |
| `Tool call message model is missing.` | Error (HTTP 409) | `backend/open_webui/utils/tool_approval.py:158-160` | No model recorded on the reply | Start a new message | Escalate with chat id |
| `Finalized pending approval message.` | Info (API response only) | `backend/open_webui/main.py:2197-2200` | **Stop** closed a paused reply | none | none |

### 10.7 Notification Delivery (`backend/open_webui/utils/notifications.py`)

Shown to the model inside `Notification failed: {e}` (10.3).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Notification target not found` | Error | `backend/open_webui/utils/notifications.py:380` | No default target, or the named id does not exist | Set up a target in Settings › Notifications | `notifications-webhooks-events-and-banners.md` |
| `Notification target is disabled` | Error | `backend/open_webui/utils/notifications.py:382` | The target is switched off | Switch it on | none |
| `Webhook URL is required` | Error | `backend/open_webui/utils/notifications.py:256` | The target has no address | Add the address | none |
| `Webhook delivery failed` | Error | `backend/open_webui/utils/notifications.py:261` | The webhook service refused or could not be reached | Check the address with its provider | Server log has the reason |
| `User not found` | Error | `backend/open_webui/utils/notifications.py:100` | Account missing | none | Escalate |

### 10.8 Server Log Lines (Not Shown to Users)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{tool} error: {e}`, for example `search_web error: {e}`, `generate_image error: {e}`, `execute_code error: {e}` | Log (exception, with trace) | `backend/open_webui/tools/builtin.py:329`, `:436`, `:791` and the `except` block of every tool | A tool crashed | none | Search the log for the tool name; the task tools log as `tasks error: {e}` (`:3639`) and `update_task_status error: {e}` (`:3689`) |
| `fetch_url error: {e}` | Log (warning) | `backend/open_webui/tools/builtin.py:361` | A page could not be fetched | none | none |
| `Tool-call iteration limit reached (%s)` | Log (warning) | `backend/open_webui/utils/middleware.py:6344` | Round limit hit | none | Pairs with 10.5 |
| `Tool-call continuation failed: %s` | Log (exception) | `backend/open_webui/utils/middleware.py:6335` | The follow-up model call failed | none | The provider error follows |
| `Error extracting citation source: {e}` | Log (exception) | `backend/open_webui/utils/middleware.py:6111` | A tool result could not be turned into a citation | none | none |
| `Timer {timer_id} completion failed` | Log (exception) | `backend/open_webui/utils/timers.py:418` | A fired timer's reply crashed | none | The timer is marked `error` |
| `Scheduler: timer error` | Log (exception) | `backend/open_webui/utils/automations.py:95-96` | Claiming due timers failed | none | Escalate if repeated |
| `Failed to cancel chat.read timers for chat %s` / `Failed to cancel chat.user_message timers for chat %s` | Log (exception) | `backend/open_webui/socket/main.py:639`; `backend/open_webui/main.py:1547` | Timer cancellation failed | none | The timer may still fire |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it can explain, check what the person sees, and escalate, but it does not
change settings, roles, permissions or data. Useful evidence for any escalation: the chat's id
(typing `/status` in the message box of a chat with messages opens a panel with a **Chat ID** row,
`src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte:63-64`;
`src/lib/components/chat/MessageInput.svelte:1465`, `:1816-1880`), the model's name, the time, and
a screenshot of the tool-call entry opened to show **Input** and **Output**. Never ask the person
to paste health information or other personal data into a ticket.

### 11.1 "It didn't search the web" or "The model says it can't browse"

**Symptom.** The reply answers from the model's own knowledge, or says it has no web access; no
`search_web` entry appears.

**Likely causes, in order.**
1. The web search toggle in the message box was not on for that message (the tools are offered
   only when it is, unless the person's web search setting is "always") (`src/lib/components/chat/Chat.svelte:342-354`;
   `backend/open_webui/utils/tools.py:677-685`).
2. Web search is switched off site-wide (code default off) or the person lacks the **Web Search**
   permission; in both cases the toggle is not offered at all (`backend/open_webui/config.py:1161`;
   `users-groups-roles-and-permissions.md`).
3. The model's **Web Search** capability, its **Builtin Tools** capability, or its **Web Search**
   built-in tool group is off (section 3.2).
4. The model's **Function Calling** is `Legacy`: the search then runs before the answer (with a
   status line) rather than as a tool, or the person chose `Legacy` in their own advanced
   parameters (`backend/open_webui/utils/middleware.py:2700-2709`).
5. The request came from the API, not the chat page (section 1.1).
6. The model chose not to search (models decide for themselves when to call tools).

**Diagnostic steps.** Ask for a screenshot of the message box showing the toggles; ask whether the
web search toggle is visible at all; ask the person to open the model's details if they can see
them; check whether other people using the same model have the same problem.

**Resolution.** Ask the person to switch the web search toggle on and resend. If the toggle is
missing, explain that web search is not enabled for them.

**Escalation.** To an admin with the model name, the person's role, and whether the toggle is
visible: an admin checks Admin Settings › Web Search, the person's group permissions and the
model's capabilities and **Builtin Tools** groups.

### 11.2 "It can't see my notes / memories / calendar / channels / earlier chats"

**Symptom.** The model says it has no access to a feature, or never uses it.

**Likely causes, in order.**
1. The family's admin switch is off: channels (code default off), memories, notes, calendar,
   automations (section 7.1).
2. The person lacks the matching permission (`features.notes`, `features.memories`,
   `features.calendar`, `features.channels`, `features.automations` (code default off)).
3. For memories: the person's own **Memory** switch in Settings › Personalization is off, or the
   model's **Memory** capability is off (`src/lib/components/chat/Chat.svelte:3412-3414`;
   `backend/open_webui/utils/tools.py:656-675`).
4. The model's **Builtin Tools** capability or that family's group is off (section 5.2).
5. Function Calling is `Legacy`, or the request came from the API.

**Diagnostic steps.** Check whether the person can open the feature itself (the Notes, Calendar
or Channels pages; memories in Settings › Personalization). If they cannot, the cause is the admin
switch or permission; if they can, it is the model's settings or Function Calling.

**Resolution.** Explain which switch applies; for memories, the person can turn their own
**Memory** switch on.

**Escalation.** To an admin or the model's owner with the model name and the feature.

### 11.3 "Every step asks me to Allow or Deny"

**Symptom.** Replies stop with `Allow {{NAME}}?` and **Allow**/**Deny** buttons.

**Likely causes, in order.** The person (or their default) chose **Ask for approval** in the
**More** menu › **Tool Permissions**; the choice is saved in their settings and in the chat
(`src/lib/components/chat/Chat.svelte:437-462`).

**Diagnostic steps.** Ask the person to open the **More** menu and read the mode shown next to
**Tool Permissions**.

**Resolution.** Explain the two modes (section 5.4). To stop being asked, choose **Full access**;
the call waiting for approval is approved automatically (if several were waiting from one step,
see 5.4 and press **Stop** if the reply does not continue). Approval applies to every tool call,
including read-only ones; there is no per-tool list.

**Escalation.** None normally.

### 11.4 "I don't see Tool Permissions (Ask for approval) in the menu"

**Symptom.** The person wants to approve tools before they run but the option is missing.

**Likely causes, in order.** The admin switch **Tool Permissions** (Admin Settings › Interface ›
Chat) is off, which is the code default; while it is off every chat runs with full access
(`src/lib/components/chat/MessageInput/InputMenu.svelte:74`, `:146`; `backend/open_webui/main.py:1255-1264`).

**Diagnostic steps.** Confirm the **More** menu shows no **Tool Permissions** entry.

**Resolution.** Explain that approval mode is a site-level choice. Meanwhile a person can
remove whole tool groups only on models they can edit (section 5.2).

**Escalation.** Request to the platform owner if approval mode is wanted (live value TO BE
CONFIRMED).

### 11.5 "My reply is stuck" or "I clicked Allow and nothing happened"

**Symptom.** A reply shows a waiting entry, or nothing after clicking **Allow**, **Deny** or
answering a question; or a pop-up such as `Tool call has already been resolved.`

**Likely causes, in order.**
1. The reply is paused waiting for approval or an answer, possibly further up the chat
   (the pause has no time limit) (section 5.4).
2. The call was already resolved in another tab or by **Stop**; the pop-up shows the server's
   message from 10.6 and the chat reloads (`src/lib/components/chat/Chat.svelte:573-594`).
3. The resumed reply is running but its updates are not arriving (connection problem; see
   `websockets-realtime-and-redis.md`).
4. A tool is slow (see 11.9).

**Diagnostic steps.** Ask the person to reload the chat and look for an entry with **Allow**/**Deny**
or a question card above the message box; ask for the exact pop-up text.

**Resolution.** Resolve the waiting call, or press **Stop** (shown while a reply is paused) to
close the reply and mark waiting calls as denied, then resend (`backend/open_webui/main.py:2160-2214`).

**Escalation.** If a reloaded chat still cannot be resolved or stopped: the chat id, the message
time and the pop-up text.

### 11.6 "It says I don't have permission when I click Allow or answer the question"

**Symptom.** Pop-up `You do not have permission to access this resource. Please contact your administrator for assistance.`
after **Allow**, **Deny**, **Submit answers** or **Cancel**.

**Likely causes, in order.**
1. The chat belongs to someone else (for example a shared chat opened by another person); only
   the owner or an admin may resolve (`backend/open_webui/utils/tool_approval.py:27-32`).
2. The chat is a temporary chat: the resolve endpoint looks the chat up in the database, where a
   temporary chat is not stored. This is read from the code and is TO BE CONFIRMED in a test
   environment (`backend/open_webui/utils/tool_approval.py:27`; `backend/open_webui/utils/chat_id.py:4-16`).

**Diagnostic steps.** Ask whether the chat is the person's own and whether it is a temporary chat.

**Resolution.** Use a normal (saved) chat for requests where the model may ask questions.

**Escalation.** If it happens in the person's own saved chat: chat id and time.

### 11.7 "A question box appeared above where I type" or "The question disappeared"

**Symptom.** A card with a header, a question and options (one marked **Recommended**) appears
above the message box; or the person closed it and the reply ended.

**Likely causes, in order.** The model used `ask_user` to check something before continuing
(section 5.5). **Cancel** refuses the question; the model is told the person declined.

**Diagnostic steps.** Ask whether the person pressed **Cancel**; check the entry list for
`Denied ask_user`.

**Resolution.** Answer each question (or type under **Other**) and press **Submit answers**. If it
was cancelled by mistake, resend the request.

**Escalation.** None normally.

### 11.8 "The AI changed or deleted something I didn't ask it to"

**Symptom.** A note was rewritten, a memory removed, a calendar event or automation created,
changed or deleted, or a note created, apparently by the model.

**Likely causes, in order.**
1. The model used one of the 21 data-changing tools (section 4.4) with **Full access** (the
   default), so nothing asked first.
2. A timer or automation set up earlier ran later (sections 5.8 and 8).
3. A sub-agent working on a delegated task made the change (memory changes are blocked for
   sub-agents) (section 5.7).

**Diagnostic steps.** Ask for the chat and a screenshot of the matching entry (for example
`View Result from replace_note_content`) opened to show **Input** and **Output**; the output
usually names the item's id and title.

**Resolution.** Tier 1 cannot undo changes. Deletions by `delete_memory`, `delete_automation` and
`delete_calendar_event` are permanent in the code (`backend/open_webui/tools/builtin.py:1070-1073`,
`:4073-4074`, `:4532`). A note rewritten by `replace_note_content` is replaced in full (the code
keeps no earlier version in that path). Explain **Ask for approval** if the site allows it, and
that the model's owner can switch off groups such as **Notes**, **Memory**, **Calendar** or
**Automations** for that model.

**Escalation.** Restore requests go to the platform maintainer with chat id, item name and time;
whether backups allow restoring a single item is TO BE CONFIRMED.

### 11.9 "It has said 'Executing…' for ages"

**Symptom.** An entry stays on `Executing {{NAME}}...` (or the group on **Exploring**).

**Likely causes, in order.**
1. `execute_code` with the in-browser engine needs the person's browser tab to stay open and
   connected. If the connection is gone, the tool returns at once with `Client session disconnected.`
   in its output; if the tab is connected but does not answer, the server waits for
   `WEBSOCKET_EVENT_CALLER_TIMEOUT`, which has no limit unless set, and then reports
   `Event call timed out. The browser tab may be inactive or closed.`
   (`backend/open_webui/tools/builtin.py:688-723`; `backend/open_webui/socket/main.py:1258-1286`;
   `backend/open_webui/env.py:534-542`). Those texts appear in the output's `stderr`, and the entry
   can still show a green tick, because the result's `status` is `success`
   (`backend/open_webui/tools/builtin.py:709-718`, `:782-789`).
2. A sub-agent (`Sub-agent: "…"`) is still working; foreground sub-agents can take as long as
   their own tool loop (`chat-completion-pipeline-and-generation-tasks.md` 5.14).
3. A slow outside service: web page, search provider, image engine, Jupyter server.
4. The page stopped receiving updates while the server finished (reloading shows the final state).

**Diagnostic steps.** Ask which tool name the entry shows and whether reloading changes it.

**Resolution.** Reload; if still running, press **Stop** and resend, keeping the tab open for code
runs.

**Escalation.** Repeated stalls for one tool across people: tool name, model, times.

### 11.10 "It says 'Tool-call limit reached (256 iterations).'"

**Symptom.** The reply ends with the error box `Tool-call limit reached ({max_tool_call_iterations} iterations).`

**Likely causes, in order.** The model kept calling tools round after round (often repeating a
failing call) until the limit (`CHAT_RESPONSE_MAX_TOOL_CALL_ITERATIONS`, default 256; sub-agents
use **Max iterations**, default 30) (`backend/open_webui/utils/middleware.py:5891-5894`,
`:6339-6346`; `backend/open_webui/env.py:1080-1098`).

**Diagnostic steps.** Look at the last few entries: the same tool with an error output points to
the cause (for example a refused file or a bad pattern).

**Resolution.** Rephrase the request more narrowly or start a new chat; fix the underlying refusal
(for example share the file).

**Escalation.** If it happens with simple requests: model name and chat id (the model may handle
tools poorly).

### 11.11 "The notification never arrived"

**Symptom.** The model said it sent a notification, or its entry shows `Notification failed: …`.

**Likely causes, in order.**
1. No default notification target, or the target is switched off or has no address (10.7).
2. The webhook service refused the message (`Webhook delivery failed`).
3. `notify` was not offered (user webhooks off site-wide or no **User Webhooks** permission, both
   off in code), so the model only claimed to send it.

**Diagnostic steps.** Open the `notify` entry's **Output**; ask whether Settings › Notifications
lists a target and which is the default.

**Resolution.** Guide the person to set up or switch on a target and press **Send Test** next to
it; success shows `Test notification sent.` (`src/lib/components/chat/Settings/Notifications.svelte:176-179`,
`:287-292`).

**Escalation.** `Webhook delivery failed` for a correct address: time and target type (not the
address itself).

### 11.12 "The reminder (timer) never went off"

**Symptom.** The model said it set a timer (`{"status": "set", …}` in the `timer` entry) but nothing
appeared later.

**Likely causes, in order.**
1. The timer was set to cancel when the chat is read (`chat.read`) or when the person sends a
   message (`chat.user_message`), and the person opened the chat or wrote in it first
   (`backend/open_webui/utils/timers.py:202-227`).
2. The chat was deleted, the account removed or set to `pending`, or the model removed; the timer
   ended with a stored error the person does not see (`backend/open_webui/utils/timers.py:245-271`).
3. The chat was busy with another reply each time it came due (it is retried on every check)
   (`:295-308`).
4. The server was not running at the due time; on restart the timer fires at the next check
   (claiming uses the due time, not a schedule) (`backend/open_webui/utils/timers.py:171-199`).
5. The person expected a calendar reminder: a timer re-prompts the chat, while
   `create_calendar_event` makes a calendar event with an alert (different tools).

**Diagnostic steps.** Ask for the `timer` entry's **Input** (`at`, `cancel_on`) and **Output**
(the UTC time it was set for); compare with the person's local time.

**Resolution.** Explain the cancel options and the UTC time shown; suggest a calendar event for
reminders that must not be cancelled by reading the chat.

**Escalation.** Timer that should have fired: chat id, the `at` value and the expected time (the
hidden timer chat holds the status).

### 11.13 "I can't see the tool steps any more" or "It only says Thinking…"

**Symptom.** No tool entries, status lines or reasoning appear; only `Thinking...` while the reply
works.

**Likely causes, in order.** **Hide Processing Details** is on in Settings › Interface, by the
person's choice or by an admin default (section 5.6).

**Diagnostic steps.** Ask the person to check Settings › Interface › **Hide Processing Details**.

**Resolution.** Switch it off to see entries again; approvals and tool images still show while it
is on.

**Escalation.** None.

### 11.14 "It brought up something from another of my chats"

**Symptom.** The model refers to an earlier conversation.

**Likely causes, in order.**
1. The **Chat History** group (`search_chats`, `view_chat`) is on by default for every model and
   has no admin switch or permission of its own; the model searched the person's own chats
   (`backend/open_webui/utils/tools.py:644-646`;
   `backend/open_webui/tools/builtin.py:1543-1549`).
2. Memories (the person's saved memories) were used (`memories.md`).

**Diagnostic steps.** Look for `search_chats` or `view_chat` entries in the reply.

**Resolution.** Explain that the model can search only the person's own chats. Archiving a chat
keeps it out of ordinary searches, but not reliably: the model's search text can include
`archived:true` (`backend/open_webui/models/chats.py:2000-2004`, `:2021-2024`). Deleting the chat,
or asking the model's owner to switch off **Chat History** for that model, are the reliable
options; `view_chat` can still open any of the person's own chats by id.

**Escalation.** If another person's chat content appears: treat as a possible privacy incident
and refer to the U of T Privacy Office (privacy.utoronto.ca) and Information Security
(security.utoronto.ca) with the chat id; do not investigate further at tier 1.

### 11.15 "It used a knowledge base I didn't attach"

See `knowledge-bases.md` 11.13: with nothing attached, the knowledge tools search the person's
readable knowledge bases, including shared ones (`backend/open_webui/utils/tools.py:631-642`).

### 11.16 "Tools work in the chat page but not through the API"

**Symptom.** The same model calls tools in the browser but not for an API client.

**Likely causes, in order.** Built-in tools are added only for requests with a browser session id;
API callers get only tools they name (`backend/open_webui/utils/middleware.py:2809-2813`,
`:3096-3099`).

**Diagnostic steps.** Confirm the request is from a script or integration.

**Resolution.** Explain that this is by design; the integration owner can request tools
explicitly.

**Escalation.** None.

### 11.17 "The event was put in the wrong calendar or at the wrong time"

**Symptom.** An event made by the model appears at an unexpected hour or in another calendar.

**Likely causes, in order.**
1. Times are read in the person's time zone as reported by their browser; with no time zone
   recorded, UTC is used (`backend/open_webui/tools/builtin.py:4096-4119`;
   `backend/open_webui/routers/auths.py:348-374`).
2. No calendar was named, so the first calendar marked default among those the person can see is
   used; if a calendar shared with the person is someone else's default and comes first, the
   event may be attempted there (it is refused without write access). This ordering effect is
   read from the code and is TO BE CONFIRMED (`backend/open_webui/tools/builtin.py:4280-4305`;
   `backend/open_webui/models/calendar.py:291-312`).

**Diagnostic steps.** Ask for the `create_calendar_event` entry's **Input** and **Output** (the
output shows the local start and the calendar id).

**Resolution.** Ask the person to name the calendar and the time zone in the request, or edit the
event on the Calendar page.

**Escalation.** Persistent time-zone errors: the person's time zone and an example.

### 11.18 "The model says the tool isn't available" or "Tool not found"

**Symptom.** An entry output `Error: Tool "{name}" not found.`, or the model says it cannot use a
tool it used before.

**Likely causes, in order.** The tool was not offered for this message: a switch, permission,
toggle, capability or group in section 3.2 changed; the chat moved to a model with different
settings; or the person is now in a temporary chat (task tools need a saved chat).

**Diagnostic steps.** Compare the model and toggles with a message where it worked.

**Resolution.** Use the same model and toggles; otherwise escalate as in 11.1 or 11.2.

**Escalation.** Model name, tool name, and when it last worked.

## 12. Local Customisations

Compared with read-only `git diff main...uoft` (the three fork commits) and `git diff` (uncommitted
working tree) on 2026-10-08.

**Back end: matches upstream v0.11.4.** None of the in-scope back-end files differ:
`backend/open_webui/tools/builtin.py`, `backend/open_webui/utils/tools.py`,
`backend/open_webui/utils/middleware.py`, `backend/open_webui/utils/tool_approval.py`,
`backend/open_webui/utils/ask_user.py`, `backend/open_webui/utils/timers.py` and
`backend/open_webui/config.py`. One indirect effect: the fork changed the default `WEBUI_NAME` to
`MedIT GPT` and removed the upstream ` (Open WebUI)` suffix (`backend/open_webui/env.py:951`), so
`notify` messages are sent under that name unless the environment sets another; the tool still
falls back to `Open WebUI` when no name is available (`backend/open_webui/tools/builtin.py:149-153`,
a licence-protected line left intact).

**Front end: Hide Processing Details (fork commits).** The fork added the per-person setting
**Hide Processing Details** (`hideProcessingDetails` in the interface settings model,
`backend/open_webui/models/users.py:100`; switch in
`src/lib/components/common/InterfaceSettings.svelte:1358-1378`; English text in
`src/lib/i18n/locales/en-US/translation.json:2923-2924`) and taught the tool-call display to honour
it:

| File | Fork change (committed) | Source |
|---|---|---|
| `src/lib/components/common/ToolCallDisplay.svelte` | Hides tool-call entries unless they wait for approval or an answer; hides the tool-name caption above embedded frames; images still show | `:178-199` |
| `src/lib/components/chat/Messages/structuredOutput.ts` and `StructuredOutputRenderer.svelte` | Drops reasoning and code-analysis entries and stops grouping tool calls when the setting is on | `src/lib/components/chat/Messages/structuredOutput.ts:344-416`; `src/lib/components/chat/Messages/StructuredOutputRenderer.svelte:70-71` |
| `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte` | The same for replies stored as text with detail blocks | `:73-105`, `:146-147` |
| `src/lib/components/chat/Messages/ResponseMessage.svelte` | Hides status history and legacy code-execution blocks; shows `Thinking...` while the reply works | `:197-221`, `:720-722`, `:920-921`, `:944` |

**Front end: uncommitted working-tree changes in this area.**

| File | What the uncommitted change does | Source |
|---|---|---|
| `src/lib/components/common/ToolCallDisplay.svelte` | Reads the setting directly from the person's settings instead of receiving it from the parent component | `:145` |
| `src/lib/components/chat/Messages/structuredOutput.ts`, `MarkdownTokens.svelte`, `StructuredOutputRenderer.svelte` | Reworks the hidden-details grouping (each tool call flushed as its own entry) and adds `hasPendingToolCall` ("A tool call waiting on the user: an approval, or an ask_user answer") | `src/lib/components/chat/Messages/structuredOutput.ts:403-416`, `:454-457`; `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte:89-105` |
| `src/lib/components/chat/Messages/ResponseMessage.svelte` | Simplifies when `Thinking...` shows: not while a tool call waits for the person; drops the committed work-around that treated an approved, still-running call as in progress | `:197-221` |
| `src/lib/components/chat/Chat.svelte` | When a reply resumes after an approval and the server reports it as not done, marks the message as not done again (comment: "Resuming after a tool approval reports done: false on a message the pause marked done") | `:2847-2850` |
| `src/lib/i18n/locales/en-US/translation.json` | Rewords the setting's description to mention code analysis and "images or embeds from tools" | `:2923` |

Everything else in scope (the 53 tools, their gates, approval, `ask_user`, timers, the
model-editor switches and admin settings) matches upstream v0.11.4. Whether the uncommitted
changes will be committed and deployed is TO BE CONFIRMED.

## 13. Source File Index

"Read" says how much of the file was read for this document: **full**, or **parts** (the
functions or lines cited).

### 13.1 Back End

| File | What it holds for this area | Read |
|---|---|---|
| `backend/open_webui/tools/builtin.py` | The 53 built-in tools and their helpers | full |
| `backend/open_webui/tools/knowledge_fs.py` | `kb_exec` and the search-pattern checker used by the grep tools | parts |
| `backend/open_webui/utils/tools.py` | `get_builtin_tools` (which tools are offered), `get_attached_knowledge`, tool specs; `get_tools` for workspace tools | parts (`:1-130`, `:267-330`, `:481-805`) |
| `backend/open_webui/utils/middleware.py` | When built-in tools are used, how they are injected, the tool loop, approval pauses and resumes, error detection, citations, iteration limit | parts (`:150-335`, `:2640-3220`, `:3279-3660`, `:5820-6392`) |
| `backend/open_webui/utils/tool_approval.py` | Approve, reject and answer; building the resume request | full |
| `backend/open_webui/utils/ask_user.py` | Checking and staging `ask_user` calls | full |
| `backend/open_webui/utils/timers.py` | Creating, claiming, cancelling and firing timers | full |
| `backend/open_webui/utils/automations.py` | The scheduler loop (timers, automations, calendar alerts) | parts (`:1-130`) |
| `backend/open_webui/utils/subagents.py` | Internal (sub-agent) requests, the memory-changing tools they lose, the hidden sub-agent chat | parts (`:20-75`, `:395-440`) |
| `backend/open_webui/tasks.py` | `stop_item_tasks` (Stop on a paused reply) | parts (`:296-315`) |
| `backend/open_webui/utils/notifications.py` | `notify_target` and webhook targets | parts |
| `backend/open_webui/utils/webhook.py` | Webhook payload formats | parts (`:30-100`) |
| `backend/open_webui/utils/chat_id.py` | Saved, temporary and channel chat ids | parts (`:1-21`) |
| `backend/open_webui/utils/models.py` | How admin model defaults merge into each model | parts (`:335-375`) |
| `backend/open_webui/main.py` | Function Calling default, approval mode, `/resolve`, Stop for paused replies, `/api/config`, scheduler start | parts |
| `backend/open_webui/config.py` | Feature switches, permissions and defaults | parts |
| `backend/open_webui/env.py` | Tool limits, `ENABLE_KB_EXEC`, `WEBSOCKET_EVENT_CALLER_TIMEOUT` | parts |
| `backend/open_webui/constants.py` | `ACCESS_PROHIBITED`, `NOT_FOUND`, automation limit texts | parts |
| `backend/open_webui/routers/chats.py` | Chat settings endpoints holding the Tool Permissions switch | parts (`:150-200`, `:830-860`) |
| `backend/open_webui/routers/memories.py` | Memory functions the memory tools call | parts |
| `backend/open_webui/routers/automations.py` | Automation limits | parts (`:69-120`) |
| `backend/open_webui/models/chats.py` | `chat` table (tasks, timers, internal chats), message storage | parts |
| `backend/open_webui/models/chat_messages.py` | `chat_message` table | parts |
| `backend/open_webui/models/calendar.py` | Default calendar creation and event queries | parts |
| `backend/open_webui/models/notes.py` | Note updates | parts |
| `backend/open_webui/models/users.py` | Interface settings, including `hideProcessingDetails` | parts (`:80-110`) |
| `backend/open_webui/socket/main.py` | Chat-read handling that cancels timers; the browser event call and its timeout | parts (`:610-640`, `:1258-1287`) |
| `backend/open_webui/events.py` | `publish_event` and event sinks | parts (`:1171-1202`) |

### 13.2 Front End

| File | What it holds for this area | Read |
|---|---|---|
| `src/lib/components/common/ToolCallDisplay.svelte` | One tool-call entry: states, Allow/Deny, input and output, images, Hide Processing Details | full |
| `src/lib/components/chat/AskUserCard.svelte` | The question card | full |
| `src/lib/components/chat/Chat.svelte` | Approval mode, pending questions, resolve calls, features sent with a message, live events | parts |
| `src/lib/components/chat/MessageInput.svelte` | Where the question card and task checklist appear; Stop button; status panel | parts |
| `src/lib/components/chat/MessageInput/InputMenu.svelte` | **Tool Permissions** menu | parts |
| `src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte` | `/status` command | parts |
| `src/lib/components/chat/Messages/StructuredOutputRenderer.svelte` | Renders a reply's output items | full |
| `src/lib/components/chat/Messages/structuredOutput.ts` | Turns output items into entries; sub-agent labels; hidden-details grouping | parts (`:185-457`) |
| `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte` | Same for text replies with detail blocks | parts |
| `src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte` | The **Exploring**/**Explored** group line | parts (`:95-300`) |
| `src/lib/components/chat/Messages/ResponseMessage.svelte` | Status history, `Thinking...`, when approval buttons are allowed | parts |
| `src/lib/components/chat/Messages/ResponseMessage/TaskList.svelte` | Task checklist | parts |
| `src/lib/components/chat/Messages/UserMessage.svelte` | **Timer** row | parts (`:300-385`) |
| `src/lib/components/chat/Messages/SubagentResultRow.svelte` | Background sub-agent result row | one line (`:41`) |
| `src/lib/components/workspace/Models/BuiltinTools.svelte` | The sixteen Builtin Tools group switches | full |
| `src/lib/components/workspace/Models/Capabilities.svelte` | Model capabilities including **Builtin Tools** | full |
| `src/lib/components/workspace/Models/ModelEditor.svelte` | Where capabilities and groups appear and how they are saved | parts |
| `src/lib/components/admin/Settings/Models/ModelDefaultsPanel.svelte` | Admin defaults for every model | parts |
| `src/lib/components/admin/Settings/Interface.svelte` | **Tool Permissions** switch | parts |
| `src/lib/components/admin/Settings/General.svelte` | Feature switches; user interface defaults | parts |
| `src/lib/components/admin/Settings/WebSearch.svelte`, `Images.svelte`, `CodeExecution.svelte` | Feature switches | parts |
| `src/lib/components/common/InterfaceSettings.svelte` | **Hide Processing Details** switch | parts |
| `src/lib/components/chat/Settings/Personalization.svelte` | Personal **Memory** switch | parts |
| `src/lib/components/chat/Settings/Notifications.svelte` | Notification targets and **Send Test** | parts (`:170-300`) |
| `src/lib/components/chat/Settings/Advanced/AdvancedParams.svelte` | **Function Calling** parameter | parts |
| `src/lib/components/chat/SettingsModal.svelte` | Admin settings tabs and groups | parts |
| `src/lib/components/layout/Navbar/Menu.svelte` | Chat JSON export | parts (`:240-255`) |
| `src/lib/apis/chats/index.ts` | `resolveChatMessageToolCall` | parts (`:1372-1410`) |
| `src/lib/constants.ts` | Default model capabilities | parts |
| `src/lib/i18n/locales/en-US/translation.json` | English text of dotted keys | parts |
| `src/routes/(app)/admin/settings/[tab]/+page.svelte` | Admin settings URL redirect | full |

## 14. Open Questions

Everything below could not be established from the repository, or was read from code and needs
confirming in a test environment. Items marked **TO BE CONFIRMED** are organisational or data
questions.

### 14.1 Live Configuration (Data, Not Code)

1. **TO BE CONFIRMED:** live values of every switch in section 7.1, especially
   `chat.tool_permissions.enable` (Tool Permissions), `subagents.enable`, `web.search.enable`,
   `image_generation.enable`, `images.edit.enable`, `code_interpreter.enable` and
   `code_interpreter.engine`, `memories.enable`, `notes.enable`, `channels.enable`,
   `calendar.enable`, `automations.enable` and `ui.enable_user_webhooks`.
2. **TO BE CONFIRMED:** the live `user.permissions` values and group grants for `features.*` and
   `chat.file_upload`, which decide which tool families each person gets.
3. **TO BE CONFIRMED:** the live `models.default_metadata` (default capabilities and Builtin Tools
   groups) and, per model, whether **Builtin Tools** is on and which groups are off (data in the
   `model` table).
4. **TO BE CONFIRMED:** the live `ui.default_interface_settings`, in particular whether **Hide
   Processing Details** is on by default for everyone.
5. **TO BE CONFIRMED:** environment values of `CHAT_RESPONSE_MAX_TOOL_CALL_ITERATIONS`,
   `ENABLE_KB_EXEC`, `KNOWLEDGE_GREP_MAX_MATCHES`, `VIEW_FILE_*`, `TIMER_POLL_INTERVAL`,
   `SCHEDULER_POLL_INTERVAL`, `CODE_INTERPRETER_BLOCKED_MODULES`, `WEB_FETCH_MAX_CONTENT_LENGTH`,
   `WEBSOCKET_EVENT_CALLER_TIMEOUT`, `AUTOMATION_MAX_COUNT` and `AUTOMATION_MIN_INTERVAL`.
   (*Precision 2026-10-08:* `WEB_FETCH_MAX_CONTENT_LENGTH` only seeds the persistent setting
   `web.fetch.max_content_length`, which admins edit in Web Search; its live value is in the
   `config` table.)
6. **TO BE CONFIRMED:** whether people use the Function Calling `Legacy` setting anywhere (it
   removes all built-in tools).

### 14.2 Organisational and Privacy Questions

7. **TO BE CONFIRMED:** which outside services built-in tools send data to in production (the
   web search provider, pages fetched by `fetch_url`, the image engine, a Jupyter server, webhook
   targets used by `notify`), and whether each is approved for the data classification of what
   people type into MedIT GPT (chats may contain personal health information). This is a question
   for the data steward and the Privacy Office, not tier 1.
8. **TO BE CONFIRMED:** retention and backup of chats, which keep every tool input and output
   (including note, memory, file and channel excerpts), and whether a single item changed or
   deleted by a tool (note, memory, automation, calendar event) can be restored.
9. **TO BE CONFIRMED:** whether the platform owner wants **Ask for approval** available, given that
   21 tools can change data and the code default is full access with no per-tool approval.
10. **TO BE CONFIRMED:** who owns the decision to turn on sub-agents and timers (off in code), and
    channels, automations and user webhooks for non-admins.
11. **TO BE CONFIRMED:** whether the uncommitted working-tree changes listed in section 12 will be
    committed and deployed (they change how Hide Processing Details groups tool calls and when
    `Thinking...` shows).

### 14.3 Behaviour Read from Code, to Confirm in a Test Environment

12. **Temporary chats and `ask_user` or approval.** The resolve endpoint looks the chat up in the
    database, so answering a question in a temporary chat appears to fail with the
    `ACCESS_PROHIBITED` text; approval pauses are skipped in temporary chats (tools run without
    asking) (`backend/open_webui/utils/tool_approval.py:27-32`;
    `backend/open_webui/utils/middleware.py:5904-5914`, `:5935-5940`).
13. **Timers on SQLite with several server processes.** Claiming uses a row lock only on
    PostgreSQL; whether two processes on SQLite can fire the same timer twice is not established
    (`backend/open_webui/utils/timers.py:171-199`).
14. **Timer runs setting more timers.** A fired timer's reply is not marked internal and carries a
    session id, so the code does not appear to stop it from offering `timer` and `delegate_task`
    again (chains of timers) (`backend/open_webui/utils/timers.py:376-416`;
    `backend/open_webui/utils/tools.py:648-654`).
15. **Timers stuck in `running`.** A timer whose reply is interrupted by a restart after it was
    claimed appears to stay in `running` and is not claimed again (`backend/open_webui/utils/timers.py:171-199`,
    `:230-244`).
16. **Default calendar choice.** With no calendar named, `create_calendar_event` takes the first
    calendar marked default among all calendars the person can see, which could be a calendar
    shared with them; the outcome then depends on their write access (`backend/open_webui/tools/builtin.py:4280-4305`).
17. **No screen lists or cancels timers.** No front-end page for pending timers was found; whether
    admins have another way to see them (other than the database) is TO BE CONFIRMED.
18. **`ask_user` timeout ignored for saved chats.** The model's `timeout_ms` is not applied to the
    card shown for a saved pause; confirm this is intended (`src/lib/components/chat/Chat.svelte:599-623`).
19. **`Input needed` label.** Pending `ask_user` calls are left out of the structured output, so the
    label may only appear for replies stored as text; confirm where people can see it
    (`src/lib/components/chat/Messages/structuredOutput.ts:396-402`).
20. **Closing the tab during an in-browser code run.** With `WEBSOCKET_EVENT_CALLER_TIMEOUT` unset
    there is no time limit on the server's wait; whether a call already in flight ends when the tab
    closes, or waits until Stop, is not established by the code (`backend/open_webui/socket/main.py:1268-1281`).
21. **Switching to Full access with several calls waiting.** Only the first waiting call is
    approved; the others from the same step stay `queued`, and in Full access mode the code does
    not promote them, so the resumed reply may stop again (`src/lib/components/chat/Chat.svelte:465-500`;
    `backend/open_webui/utils/middleware.py:3504-3530`).
22. **Task checklist visibility.** The checklist box shows only while a reply is running; after
    that, only the `/status` panel's **Tasks** count shows it exists (`src/lib/components/chat/MessageInput.svelte:1792-1796`, `:1865-1872`).

### 14.4 Discrepancies Noticed in the Code (No Contradiction with Ground Truth)

23. The `notify` tool's description says the target can be an "id or name", but the code matches
    the id only (`backend/open_webui/tools/builtin.py:142`; `backend/open_webui/utils/notifications.py:234-243`).
24. The **Calendar** group's description says it can "List calendars", but no built-in tool lists
    calendars (`src/lib/i18n/locales/en-US/translation.json:2542`).
25. The **Sub-agents** group also controls `timer`, which its label and description do not mention
    (`backend/open_webui/utils/tools.py:648-654`; `src/lib/i18n/locales/en-US/translation.json:2562-2563`).
26. Nothing found here contradicts `ground-truth.md` or `inventory.md`; the inventory's 53 functions
    match `builtin.py`, which also re-exports `kb_exec` from `backend/open_webui/tools/knowledge_fs.py`.

### 14.5 Security-Sensitive Questions

27. Whether every data-changing built-in tool applies the same access checks as the matching page
    or API (one possible difference was noticed in the automation tools). Security-sensitive: refer
    to the platform maintainer and U of T Information Security (security.utoronto.ca).
28. The isolation of code run by `execute_code` and of pages fetched by `fetch_url`.
    Security-sensitive: refer to the platform maintainer and U of T Information Security
    (security.utoronto.ca).
