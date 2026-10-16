# Chat Composer, Message Display and Rendering

## At a Glance

- **What it is.** The main chat screen of MedIT GPT: the landing page at `/` (a new chat) and a saved
  conversation at `/c/{id}`. One front-end component, `src/lib/components/chat/Chat.svelte`, controls
  both; there is no separate server-rendered page (`src/routes/(app)/+page.svelte:15`,
  `src/routes/(app)/c/[id]/+page.svelte:7`).
- **The composer** (`src/lib/components/chat/MessageInput.svelte`) is a rich-text box with, from left to
  right underneath it: the **+** ("More") attachments menu, the **Integrations** menu (tools, skills,
  filters, **Web Search**, **Image**, **Code Interpreter**), chips for whatever is switched on, then on the
  right the **model selector**, an optional **Chat Variables** button, the **Dictate** microphone, and
  either **Voice mode**, **Send message** or **Stop**. In this version the model selector sits inside
  the composer, not in the top bar (`src/lib/components/chat/MessageInput.svelte:2577-2585`).
- **Messages.** Each response has an action row: version arrows (`2/3`), **Edit**, **Copy**,
  **Read Aloud**, an info icon (token usage), **Good Response** / **Bad Response**, **Continue Response**,
  **Regenerate**, any admin-installed action buttons, **Fork chat**, **Delete** and a timestamp
  (`src/lib/components/chat/Messages/ResponseMessage.svelte:967-1642`). User messages have **Edit**,
  **Copy**, **Delete** and version arrows (`src/lib/components/chat/Messages/UserMessage.svelte:416-725`).
- **Rendering.** Responses are Markdown (headings, lists, tables with **Copy** and **Export to CSV**,
  alerts), code blocks with **Copy**/**Run**/**Save**/**Preview**, KaTeX maths, Mermaid and Vega
  diagrams, sanitized HTML (video, audio, YouTube and sandboxed iframes only), inline citation chips,
  a "Sources" list, a collapsible status line, reasoning and tool-call cards, and follow-up suggestions.
- **Typing while a response is generating** queues the new message above the composer (setting
  **Enable Message Queue**, on by default); queued messages are sent together when the response
  finishes (`src/lib/components/chat/Chat.svelte:3191-3214`, `:2487-2524`).
- **Errors** appear inside the response as a grey box with an info icon, usually reading
  `Uh-oh! There was an issue with the response.` followed by the provider's detail, plus a pop-up toast
  (`src/lib/components/chat/Chat.svelte:3716-3756`; `src/lib/components/chat/Messages/Error.svelte:40-48`).
- **The fork's changes (MedIT GPT only).** Two per-user switches in **Settings > Interface > Chat**:
  **Hide Processing Details** (default off) replaces status lines, reasoning, tool calls and code
  analysis with a single `Thinking...` line, while still showing tool approval requests and tool images or
  embeds; **Inline Citations** (default on) can remove the `[1]` source chips from the answer text while
  the source list under the response stays. Part of this is committed on `uoft`; refinements are
  **uncommitted** in the working tree (section 12).
- **Permissions** that hide controls are the `chat.*` keys (all on by default except
  `chat.temporary_enforced`) plus `features.web_search`, `features.image_generation`,
  `features.code_interpreter` and `features.direct_tool_servers` (`backend/open_webui/config.py:1849-1916`).
- **Stored data.** The conversation tree lives in the `chat` table's `chat` JSON (`history.messages`,
  `history.currentId`) and is mirrored row by row in `chat_message`; a thumbs rating writes a `feedback`
  row with a full snapshot of the chat; drafts live only in the browser's session storage and the
  message queue only in browser memory (section 6).
- **Neighbouring documents.** Chat list, folders, sharing and archive: `chat-conversations-history-and-organisation.md`.
  Server side of a reply: `chat-completion-pipeline-and-generation-tasks.md`. Every status line text:
  `in-chat-status-and-response-messages.md`. Tools such as `ask_user`: `builtin-native-tools.md`. Code
  running: `code-execution-and-interpreter.md`. Voice: `audio-speech-to-text-and-text-to-speech.md`.
  Upload limits and storage: `files-uploads-and-storage.md`. The settings screen itself:
  `user-settings-and-personalisation.md`.

## 1. Purpose and Who Uses It

The chat screen is where people do almost everything in MedIT GPT: pick a model, type or dictate a
question, attach files, switch on tools or web search, read the streamed answer, and act on it (copy,
rate, regenerate, edit, branch). Tier-1 support will mostly meet this area through screenshots, so this
document names every visible part and says what it does to stored data.

Who uses it:

- **Every signed-in account with the role `user` or `admin`.** Accounts with the role `pending` see the
  "Account Activation Pending" overlay instead and cannot reach the chat screen (ground truth).
- **Admins** see the same screen. Most controls are shown to an admin regardless of permission
  settings, because almost every check is written as `role === 'admin' || permission`
  (for example `src/lib/components/chat/MessageInput.svelte:2630`, `:2671`;
  `src/lib/components/chat/Messages/ResponseMessage.svelte:1146`, `:1279`, `:1357`, `:1394`, `:1552`,
  `:1583`).
- **People viewing someone else's chat** (for example through a shared folder, or an admin opening a
  user's chat when admin chat access is on) see it **read-only**: the composer is replaced by the words
  `Read only` and edit, rate, regenerate and delete buttons are hidden
  (`src/lib/components/chat/Chat.svelte:391-392`, `:4433-4438`;
  `src/lib/components/chat/Messages/ResponseMessage.svelte:1086`, `:1278`).
- **Notes users** see the same chat engine embedded in a note's side panel (`embedded` mode,
  `src/lib/components/chat/Chat.svelte:132-146`, `:4296-4322`); notes are documented elsewhere.

What this area does **not** cover: the sidebar chat list, folders, search, sharing, archiving and export
(`chat-conversations-history-and-organisation.md`); what the server does with a message
(`chat-completion-pipeline-and-generation-tasks.md`); the voice call overlay
(`audio-speech-to-text-and-text-to-speech.md`).

## 2. Navigation and URLs

All URLs are relative to the site root; the production host name is **TO BE CONFIRMED**.

| URL | What it shows | Source |
|---|---|---|
| `/` | A new, empty chat (the landing screen with the model name, composer and suggestions). A `?error=` query value is shown as an error pop-up, falling back to `An unknown error occurred.` | `src/routes/(app)/+page.svelte:8-15` |
| `/c/{id}` | A saved conversation, loaded by id | `src/routes/(app)/c/[id]/+page.svelte:1-7` |
| `/folders/{id}` | Opening a folder resets the chat screen to a new chat inside that folder (folder title and chat list replace the suggestions) | `src/lib/components/chat/Chat.svelte:1577-1581`; `src/lib/components/chat/Placeholder.svelte:130-143`, `:285-288` |
| `/home` | A stub page: a header with **Notes** and **Calendar** links and an empty body. Nothing in the front end links to it; its **Notes** link points to `/playground/notes`, a route that does not exist in this version | `src/routes/(app)/home/+layout.svelte:17-73`; `src/routes/(app)/home/+page.svelte` (empty file) |

**How the URL changes.** A new chat stays at `/` until the first message is sent; the server then
returns the new chat id and the browser address is replaced with `/c/{id}` without a page reload
(`src/lib/components/chat/Chat.svelte:3681-3694`, `:3978-3980`). Starting a new chat from inside a
saved one rewrites the address back to `/` (`src/lib/components/chat/Chat.svelte:2141-2143`).
Temporary chats never get a `/c/` address; their id is generated in the browser
(`src/lib/components/chat/Chat.svelte:3324-3326`, `:3993-3995`).

**Query parameters on a new chat** (read once when the chat initializes,
`src/lib/components/chat/Chat.svelte:2015-2259`):

| Parameter | Effect | Source line |
|---|---|---|
| `models=a,b` or `model=a` | Preselects one or more models. One unknown model id opens the model selector with the id typed into its search box | `:2068-2091` |
| `temporary-chat=true` | Starts a temporary chat | `:2038-2040` |
| `youtube={video id}` | Attaches that YouTube video as web content | `:2164-2166` |
| `load-url={url}` | Attaches a web page | `:2168-2170` |
| `web-search=true`, `image-generation=true`, `code-interpreter=true` | Switches the matching toggle on | `:2172-2182` |
| `tools=a,b` or `tool-ids=a,b` | Selects tools (unknown ids ignored) | `:2184-2196` |
| `call=true` | Opens the voice call overlay | `:2207-2209` |
| `q={text}` | Puts the text in the composer and sends it, unless `submit=false` | `:2243-2251` |

**Ways into a chat from elsewhere.** Clicking a model mention in a message (`@` chip) opens
`/?model={id}` (`src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens/MentionToken.svelte:96-98`);
links in a response to `/c/...`, `/notes/...` or `/channels/...` on the same site open inside the app
instead of a new tab (`src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens.svelte:52-68`).

**Browser tab title.** `{chat title} / {site name}` with the title cut to 30 characters and `...`, or
just the site name when **Display Chat Title in Tab** is off (`src/lib/components/chat/Chat.svelte:4166-4175`).

**Keyboard shortcuts that act on this screen** (defaults; users can rebind them, and "Cmd" means Ctrl
outside macOS, `src/lib/shortcuts.ts:132-141`, `:185`):

| Shortcut (default) | Action | Source |
|---|---|---|
| Cmd+Shift+O | New chat | `src/lib/shortcuts.ts:86` |
| Cmd+Shift+' | New temporary chat | `src/lib/shortcuts.ts:87` |
| Cmd+Shift+M | Open the model selector | `src/lib/shortcuts.ts:89` |
| Cmd+Shift+L | Start or confirm dictation | `src/lib/shortcuts.ts:90`; `src/lib/components/chat/MessageInput.svelte:1333-1346` |
| Shift+Escape | Focus the composer | `src/lib/shortcuts.ts:99` |
| Cmd+Shift+Enter | Add the composer text as a user message plus a placeholder response (`[RESPONSE] {id}`) without calling the model | `src/lib/shortcuts.ts:100`; `src/routes/(app)/+layout.svelte:321-324`; `src/lib/components/chat/Chat.svelte:2633-2696` |
| Cmd+R (composer focused) | Regenerate the last response | `src/lib/shortcuts.ts:101`; `src/routes/(app)/+layout.svelte:343-349` |
| Cmd+Alt+Enter / Cmd+Alt+Backspace | Allow / Deny the latest tool approval request | `src/lib/shortcuts.ts:102-103`; `src/routes/(app)/+layout.svelte:325-342` |
| Cmd+Shift+; / Cmd+Shift+C | Copy the last code block / the last response | `src/lib/shortcuts.ts:104-105` |
| Escape (composer focused) | Stop the response and clear the @-model, tools, filters and toggles | `src/lib/components/chat/MessageInput.svelte:2117-2119`, `:2169-2178` |

## 3. Roles and Permissions

Three things decide whether a control appears: the user's **role**, the **permission keys** an admin
grants (defaults plus groups, ground truth), and **switches** on the admin side or on the selected
**model**. Admins skip the permission checks in this area because each check is written as
`role === 'admin' || permission`.

### 3.1 Permission Keys That Hide or Block Controls

Code defaults come from `backend/open_webui/config.py:1849-1937` and are assembled into
`DEFAULT_USER_PERMISSIONS` at `backend/open_webui/config.py:1978-2000` (`chat`), `:2001-2016`
(`features`) and `:2017-2019` (`settings`). Live values
are data in the `user.permissions` setting and in group permissions: **TO BE CONFIRMED** for
production.

| Permission key | Code default | What a user without it sees | Front-end check |
|---|---|---|---|
| `chat.controls` | on | No **Controls** (knobs) button in the top bar; no **Controls** tab or section in the side panel | `src/lib/components/chat/Navbar.svelte:246-258`; `src/lib/components/chat/ChatControls.svelte:65`; `src/lib/components/chat/Controls/Controls.svelte:56` |
| `chat.valves` | on | No **Valves** section in Controls; no valves knob on tools or filters in the Integrations menu; clicking a filter chip only removes it | `src/lib/components/chat/Controls/Controls.svelte:94-107`; `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:415`, `:625`; `src/lib/components/chat/MessageInput.svelte:2425-2438` |
| `chat.system_prompt` | on | No **System Prompt** box in Controls | `src/lib/components/chat/Controls/Controls.svelte:109-129` |
| `chat.params` | on | No **Advanced Params** in Controls | `src/lib/components/chat/Controls/Controls.svelte:131-146` |
| `chat.file_upload` | on | In the **+** menu, **Upload Files**, **Capture**, **Attach Files**, **Attach Notes**, **Attach Knowledge** and **Reference Chats** are greyed with a tooltip; **Google Drive** and **Microsoft OneDrive** disappear; dropped or pasted files are refused | `src/lib/components/chat/MessageInput/InputMenu.svelte:68-70`, `:187-392`; `src/lib/components/chat/MessageInput.svelte:918-922` |
| `chat.web_upload` | on | **Attach Webpage** greyed; web addresses cannot be attached | `src/lib/components/chat/MessageInput/InputMenu.svelte:73`, `:246-267`; `src/lib/components/chat/Chat.svelte:1790-1794` |
| `chat.delete` | on | The hidden delete-chat button used by the Cmd+Shift+Backspace shortcut is not rendered | `src/lib/components/chat/Navbar.svelte:153-164` |
| `chat.delete_message` | on | No **Delete** under messages | `src/lib/components/chat/Messages/UserMessage.svelte:593`; `src/lib/components/chat/Messages/ResponseMessage.svelte:1583` |
| `chat.continue_response` | on | No **Continue Response** | `src/lib/components/chat/Messages/ResponseMessage.svelte:1357` |
| `chat.regenerate_response` | on | No **Regenerate** button or menu | `src/lib/components/chat/Messages/ResponseMessage.svelte:1394` |
| `chat.rate_response` | on | No **Good Response** / **Bad Response** | `src/lib/components/chat/Messages/ResponseMessage.svelte:1279` |
| `chat.edit` | on | No **Edit** under responses (checked for the `user` role only; editing your own message is not gated) | `src/lib/components/chat/Messages/ResponseMessage.svelte:1087` |
| `chat.import` | on | No **Fork chat** button and no `/fork` command; a fork attempt shows `Access prohibited` | `src/lib/components/chat/Messages/ResponseMessage.svelte:1552`; `src/lib/components/chat/MessageInput.svelte:1466-1468`; `src/lib/components/chat/Chat.svelte:3051-3054` |
| `chat.stt` | on | No **Dictate** microphone | `src/lib/components/chat/MessageInput.svelte:2630` |
| `chat.tts` | on | No **Read Aloud** | `src/lib/components/chat/Messages/ResponseMessage.svelte:1146` |
| `chat.call` | on | No **Voice mode** button | `src/lib/components/chat/MessageInput.svelte:2671` |
| `chat.multiple_models` | on | Opening a saved chat that used several models keeps only the first one selected | `src/lib/components/chat/Chat.svelte:2323-2325` |
| `chat.temporary` | on | No **Temporary Chat** button and no `/temporary` command | `src/lib/components/chat/Navbar.svelte:180`; `src/lib/components/chat/MessageInput.svelte:184-190`; `src/lib/components/chat/Chat.svelte:2042-2044` |
| `chat.temporary_enforced` | **off** | When on: every new chat is temporary and the toggle is hidden | `src/lib/components/chat/Chat.svelte:2025-2027`; `src/lib/components/chat/Navbar.svelte:180` |
| `features.web_search` | on | No **Web Search** entry or chip | `src/lib/components/chat/MessageInput.svelte:824-828`; `src/lib/components/chat/Chat.svelte:349-354` |
| `features.image_generation` | on | No **Image** entry | `src/lib/components/chat/MessageInput.svelte:830-834` |
| `features.code_interpreter` | on | No **Code Interpreter** entry | `src/lib/components/chat/MessageInput.svelte:836-841` |
| `features.direct_tool_servers` | **off** | User-added ("Direct") terminals are not offered | `src/lib/components/chat/MessageInput.svelte:802-809`; `src/lib/components/chat/MessageInput/TerminalMenu.svelte:164` |
| `settings.interface` | on | No **Interface** tab in Settings, so the fork's two switches cannot be changed by the user | `src/lib/components/chat/SettingsModal.svelte:394` |

`chat.share` and `chat.export` are used by the chat menu, not by this area.

**Server-side checks.** Some of these keys are also checked by the server on particular endpoints, for
example `chat.import` (`backend/open_webui/routers/chats.py:233`), `chat.delete`
(`backend/open_webui/routers/chats.py:713`), `chat.tts` (`backend/open_webui/routers/audio.py:612`),
`chat.stt` (`backend/open_webui/routers/audio.py:1258`), `chat.controls`, `chat.system_prompt` and
`chat.params` when saving settings (`backend/open_webui/routers/users.py:504-515`) and
`features.web_search` (`backend/open_webui/routers/retrieval.py:2891`). Whether every key in the table
is enforced on the server is Security-sensitive: refer to the platform maintainer and U of T Information
Security (security.utoronto.ca).

**Two different fall-backs.** The **Delete** button under a user message treats a missing
`chat.delete_message` key as "off" (`?? false`, `src/lib/components/chat/Messages/UserMessage.svelte:593`),
while the one under a response treats it as "on" (`?? true`,
`src/lib/components/chat/Messages/ResponseMessage.svelte:1583`). The **+** menu likewise has no
fall-back for `chat.file_upload` (`src/lib/components/chat/MessageInput/InputMenu.svelte:68-70`). These
only matter if a stored permission set lacks the key.

### 3.2 Admin Switches and Model Capabilities

A control can also be missing because an admin switched a feature off for everyone, or because the
selected model does not declare a capability. Every model capability defaults to **on** when the model
does not mention it (`src/lib/components/chat/MessageInput.svelte:759-763`).

| Control | Also needs | Source |
|---|---|---|
| **Web Search** | Admin web search on (`web.search.enable`) and every selected model with the `web_search` capability | `src/lib/components/chat/MessageInput.svelte:824-828` |
| **Image** | Admin image generation on (`image_generation.enable`) and every selected model with `image_generation` | `src/lib/components/chat/MessageInput.svelte:830-834` |
| **Code Interpreter** | Admin code interpreter on (`code_interpreter.enable`), every selected model with `code_interpreter`, and no terminal selected | `src/lib/components/chat/MessageInput.svelte:836-846` |
| **Run** on Python code blocks | Admin code execution on (`code_execution.enable`, default on) | `src/lib/components/chat/Messages/CodeBlock.svelte:498` |
| **Good / Bad Response** | Admin message rating on (`ui.enable_message_rating`, default on) and not a temporary chat | `src/lib/components/chat/Messages/ResponseMessage.svelte:1279` |
| **Tool Permissions** entry in the + menu | Admin tool permissions on (`chat.tool_permissions.enable`, default **off**) | `src/lib/components/chat/MessageInput/InputMenu.svelte:74`, `:146` |
| **Compact** command and context gauge | Admin context compaction on (`chat.context_compaction.enable`, default **off**) | `src/lib/components/chat/Chat.svelte:264`; `src/lib/components/chat/MessageInput.svelte:1463` |
| Prompt autocompletion ghost text | Admin autocomplete on (`task.autocomplete.enable`, default **off**) and the user's **Prompt Autocompletion** | `src/lib/components/chat/MessageInput.svelte:2081-2082` |
| **Attach Notes** | Admin notes on (`notes.enable`, default on) | `src/lib/components/chat/MessageInput/InputMenu.svelte:301` |
| **Google Drive** / **Microsoft OneDrive** | Admin integrations on (`google_drive.enable`, `onedrive.enable` with personal or business accounts) | `src/lib/components/chat/MessageInput/InputMenu.svelte:394`, `:437` |
| Image attachments | Every selected model with `vision` | `src/lib/components/chat/MessageInput.svelte:1126-1130` |
| File attachments | Every selected model with `file_upload` (unless a terminal stores uploads) | `src/lib/components/chat/MessageInput.svelte:924-929` |
| Inline citation chips and the sources list | The model's `citations` capability | `src/lib/components/chat/Messages/ContentRenderer.svelte:128-130`; `src/lib/components/chat/Messages/ResponseMessage.svelte:934` |
| Status lines | The model's `status_updates` capability (and the fork's **Hide Processing Details** off) | `src/lib/components/chat/Messages/ResponseMessage.svelte:198-199` |
| **Valves** button next to the model selector | A single selected model that has user valves | `src/lib/components/chat/MessageInput.svelte:2347-2364` |

The `/api/config` response that delivers these switches to the browser is built at
`backend/open_webui/main.py:2359-2378` and `:2394-2437`.

## 4. Key Concepts and Terminology

| Term | Meaning on this screen | Source |
|---|---|---|
| **Composer** | The message box at the bottom (or centre, on a new chat). A rich-text editor; what is sent is Markdown converted from it | `src/lib/components/chat/MessageInput.svelte:2052-2216`; `src/lib/components/common/RichTextInput.svelte:963-993` |
| **@-model** | A model picked with `@` in the composer. It answers the **next** message only and shows as a chip with an X above the text | `src/lib/components/chat/MessageInput.svelte:1904-1929`; `src/lib/components/chat/Chat.svelte:3250-3254` |
| **Integrations** | The puzzle-piece menu next to **+**: tools, skills, toggleable filters, Web Search, Image, Code Interpreter | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:304-522` |
| **Tool / tool call** | A function the model may call. Each call appears as a card ("Executing ...", "View Result from ...") with its input and output | `src/lib/components/common/ToolCallDisplay.svelte:236-256` |
| **Tool approval** | When the user's tool mode is **Ask for approval**, the model pauses before each tool call and shows **Allow** / **Deny** | `src/lib/components/chat/MessageInput/InputMenu.svelte:54-65`; `src/lib/components/common/ToolCallDisplay.svelte:258-276` |
| **Ask-user card** | A question card above the composer, raised by the `ask_user` tool or a plugin, with choices, an **Other** box and **Submit answers** | `src/lib/components/chat/AskUserCard.svelte:173-303` |
| **Skill** | A reusable instruction pack selectable in Integrations or with `$` | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:655-731` |
| **Filter (toggle)** | An admin-installed function the model allows users to switch on per message; shows as a blue chip | `src/lib/components/chat/MessageInput.svelte:2413-2482` |
| **Valves** | User-adjustable settings of a tool, function or model, opened from a knob icon | `src/lib/components/chat/Controls/Valves.svelte:145-230` |
| **Chat Variables** | Named values a model asks for before the first send (defined by the model); stored on the chat | `src/lib/components/chat/Chat.svelte:640-727`, `:4179-4218` |
| **Input variables** | `{{name}}` placeholders inside an inserted prompt; a form asks for each value | `src/lib/components/chat/MessageInput.svelte:263-281`; `src/lib/utils/index.ts:1731-1751` |
| **Message queue** | Messages typed while a response is still generating, held above the composer and sent together afterwards | `src/lib/components/chat/MessageInput.svelte:1798-1814`; `src/lib/components/chat/Chat.svelte:2487-2524` |
| **Branch / version** | Every edit or regeneration adds a sibling message instead of overwriting; arrows and `n/m` switch between them | `src/lib/components/chat/Messages.svelte:199-307` |
| **Current branch** | The path from the first message to the message the chat is showing (`history.currentId`) | `src/lib/components/chat/Messages.svelte:89-107` |
| **Multi-model response** | One question answered by several selected models side by side (or in tabs) | `src/lib/components/chat/Messages/MultiResponseMessages.svelte:228-459` |
| **Merge Responses** | Asks a model to combine the side-by-side answers into one "Merged Response" | `src/lib/components/chat/Messages/MultiResponseMessages.svelte:397-454`; `src/lib/components/chat/Chat.svelte:3901-3951` |
| **Status history** | The grey one-line progress text above an answer ("Searching the web", "Retrieved 3 sources"), expandable to the full list | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory.svelte:30-76` |
| **Details blocks** | Collapsible sections inside an answer: reasoning ("Thought for 5 seconds"), code analysis ("Analyzed") and tool calls ("Explored") | `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte:63-110`; `src/lib/components/common/Collapsible.svelte:96-121` |
| **Structured output** | Newer responses are stored as a list of output items (message text, reasoning, function calls and their outputs) rather than one text; the screen renders either form | `src/lib/components/chat/Messages/structuredOutput.ts:344-444`; `src/lib/components/chat/Messages/ContentRenderer.svelte:290-361` |
| **Citation / source** | `[1]` markers in the answer become small chips; the button under the answer (`3 Sources`) lists every source | `src/lib/utils/marked/citation-extension.ts:12-57`; `src/lib/components/chat/Messages/Citations.svelte:171-249` |
| **Artifacts** | A side panel that previews HTML or SVG produced in the answer | `src/lib/components/chat/Artifacts.svelte:124-280`; `src/lib/components/chat/Chat.svelte:1949-2002` |
| **Embeds** | Interactive frames returned by a tool or source, shown in the answer or in the side panel | `src/lib/components/chat/Messages/ResponseMessage.svelte:748-765`; `src/lib/components/chat/ChatControls/Embeds.svelte:45-86` |
| **Overview** | A tree diagram of every message and branch in the chat, in the side panel | `src/lib/components/chat/Overview/View.svelte:65-131` |
| **Temporary chat** | A chat that is not saved; dashed composer border and a "Temporary Chat" label | `src/lib/components/chat/MessageInput.svelte:1896-1898`; `src/lib/components/chat/Placeholder.svelte:116-126` |
| **Fork** | Copies the conversation up to a message into a new chat | `src/lib/components/chat/Chat.svelte:3046-3089` |
| **Compact** | Shortens older messages so a long chat can continue (admin-enabled) | `src/lib/components/chat/Chat.svelte:2956-3005` |
| **Follow-ups** | Suggested next questions shown under the last answer | `src/lib/components/chat/Messages/ResponseMessage/FollowUps.svelte:11-35` |
| **Floating quick actions** | **Ask** and **Explain** buttons that appear when text in an answer is selected | `src/lib/components/chat/ContentRenderer/FloatingButtons.svelte:23-37` |
| **Processing details** (fork term) | The status lines, reasoning, code analysis and tool-call cards that **Hide Processing Details** removes | `src/lib/i18n/locales/en-US/translation.json:2923` |

## 5. Workflows (Step by Step)

### 5.1 Tour of a New Chat (the Landing Screen)

What a user sees at `/` before sending anything (`src/lib/components/chat/Chat.svelte:4386-4646`):

1. **Top bar** (`src/lib/components/chat/Navbar.svelte`). On a phone, a sidebar button
   (`Open Sidebar` / `Close Sidebar`, `:98`). On the right, the **Temporary Chat** button (a dotted speech
   bubble, `:180-213`) and the **Controls** button (sliders icon, `:246-258`). The title area stays empty
   until the chat is saved.
2. **Banners** under the top bar, only on a new empty chat: admin banners (dismissible ones are
   remembered in the browser), and licence notices **Trial License** or **License Error**
   (`src/lib/components/chat/Navbar.svelte:270-324`).
3. **Model heading** (`src/lib/components/chat/Placeholder.svelte:128-238`): the avatar of each
   selected model (overlapping when several; clicking one switches which description shows), the model's
   name (or `Hello, {name}` when there is none), the model's description and an author line `By ...`.
   When a temporary chat is on, a small **Temporary Chat** label with an eye-slash icon sits above, with the
   tooltip `This chat won't appear in history and your messages will not be saved.` (`:116-126`).
4. **The composer**, centred, with the placeholder text `How can I help you today?` (`:241-281`).
5. **Suggestions** underneath: a `Suggested` heading with prompt cards (a title and a grey second line, or
   the prompt text and the word `Prompt`). They come from the selected model, or else from the admin's
   default suggestions; the order is shuffled and the list filters as you type (fuzzy match, hidden above
   500 typed characters). With no suggestions, the line shows the site name and version, for example
   `MedIT GPT ‧ v0.11.4` (`src/lib/components/chat/Suggestions.svelte:43-127`;
   `src/lib/components/chat/Placeholder.svelte:98-106`). Clicking a card sends it at once, unless
   **Insert Suggestion Prompt to Input** is on, in which case it is only placed in the composer
   (`src/lib/components/chat/Chat.svelte:920-932`).
6. **Inside a folder** (`/folders/...`), the model heading is replaced by the folder title and the
   suggestions by the folder's chat list (`src/lib/components/chat/Placeholder.svelte:130-143`,
   `:285-288`; details in `chat-conversations-history-and-organisation.md`). If the folder is shared with
   the user without write access, the composer is not shown (`:108-112`, `:242`).
7. **Landing Page Mode set to chat** puts the composer at the bottom and a left-aligned greeting with
   suggestions in the message area instead (`src/lib/components/chat/Chat.svelte:4387`;
   `src/lib/components/chat/ChatPlaceholder.svelte:60-164`).

### 5.2 Tour of an Open Chat

1. **Top bar**: the chat title, a `...` **Chat actions** menu (share, move, archive, delete and so on;
   that menu lives in `src/lib/components/layout/Navbar/Menu.svelte` and is documented with chat
   management), **Save Chat** instead of Temporary Chat while a temporary chat is open, **New Chat** on a
   phone, and **Controls** (`src/lib/components/chat/Navbar.svelte:118-258`). A temporary chat also shows
   `Temporary Chat` under the bar (`:264-268`).
2. **The message list** shows the last 8 messages of the current branch; scrolling to the top shows
   `Loading...` and loads 8 more (`src/lib/components/chat/Messages.svelte:59-84`, `:482-496`).
3. **User messages**: right-aligned grey bubbles by default (setting **Chat Bubble UI**), attachments
   above the text, a timestamp and buttons that appear on hover (section 5.11).
4. **Responses**: the model's avatar and name, then in order the status line, any images or files the
   model produced, tool embeds, the answer, a blinking caret while it streams, an error box if something
   failed, the **Sources** button, code-execution chips, and the action row (section 5.12), the rating
   form after a rating, and follow-up questions under the last answer
   (`src/lib/components/chat/Messages/ResponseMessage.svelte:699-1675`).
5. **Composer** at the bottom (section 5.3). When you scroll up during a chat, a round down-arrow
   button (`Scroll to bottom`) appears above the composer (`src/lib/components/chat/MessageInput.svelte:1679-1705`).
6. **Side panel** on the right, opened with **Controls**: tabs **Controls**, **Files** and
   **Overview**; it is also where **Artifacts**, **Embeds** and the voice call appear (section 5.20).

### 5.3 The Composer, Part by Part

From top to bottom (`src/lib/components/chat/MessageInput.svelte:1760-2781`):

| Part | When it appears | What it does |
|---|---|---|
| Ask-user card | A tool or plugin is waiting for answers | Question form; see 5.18 (`:1774-1789`) |
| Task list | Tasks are running for this chat; hidden by the fork's **Hide Processing Details** | `{done} out of {total} tasks completed` with a checklist (`:1791-1796`; `src/lib/components/chat/Messages/ResponseMessage/TaskList.svelte:19-115`) |
| Queued messages | Messages typed while a response is generating | Rows with **Send now**, **Edit**, **Delete** (`:1798-1814`) |
| Status panel | After `/status` | `Context usage`, `Queued messages`, `Tasks`, `Chat ID` (click to copy) and **Close** (`:1816-1892`) |
| @-model chip | A model was picked with `@` | Avatar and name with an X to remove (`:1904-1929`) |
| Attachments row | Files are attached | Image thumbnails (yellow warning icon naming the models that cannot read images) and file chips, each removable (`:1931-2024`) |
| Text box | Always | Placeholder `Send a Message` (or `How can I help you today?` on a new chat); an **Expand input** button appears when the text is longer than two lines (`:2026-2079`) |
| **+** button (`More`) | Always | Attachments menu (5.6) (`:2225-2293`) |
| **Integrations** button | At least one of: tools, skills, toggleable filters, Web Search, Image, Code Interpreter is available | Menu of switches (5.7) (`:2295-2345`) |
| Valves knob | One model selected and it has user valves | Opens that model's valves (`:2347-2364`) |
| Chips | Something is switched on | Tool count (`{COUNT} Available Tools`), skill count, filter chips, **Web Search**, **Image**, **Code Interpreter**, amber **Click to connect** chips for tools that need sign-in, and the terminal picker (`:2366-2571`) |
| Model selector | Always | Shows the current model and opens the model list; the selector itself is `src/lib/components/chat/ModelSelector.svelte`, outside this area, and is told it may offer a "set default" option only while the chat is empty (`showSetDefault`, `:2575-2585`) |
| **Chat Variables** knob | The selected model defines chat variables | Opens the Chat Variables form (`:2587-2601`) |
| **Stop** | A response is generating and the text box is empty | Stops generation (`:2603-2627`) |
| **Dictate** (microphone) | No response is running and the user has `chat.stt` | Starts dictation (`:2629-2668`) |
| **Voice mode** | Text box empty, not embedded, user has `chat.call` | Opens the voice call (`:2671-2733`) |
| **Send message** (up arrow) | There is text or a file | Sends (`:2735-2767`); greyed and disabled when the box is empty |
| Footer line | The licence metadata includes an input footer | Small centred text under the composer (`:2774-2780`) |

Behind the scenes the composer saves a **draft** of the text, files (except images) and switches in the
browser's session storage, half a second after typing stops, and only if the text is under 5,000
characters (`src/lib/components/chat/Chat.svelte:4032-4071`). The draft is restored when the user comes
back to the same chat in the same tab (`:756-779`, `:864-866`). Temporary chats keep no draft
(`:4484-4488`).

### 5.4 Sending a Message

What happens, in order, when the user presses Send or Enter (`src/lib/components/chat/Chat.svelte:3096-3224`):

1. **Commands typed as the whole message** run instead of sending: `/compact`, `/status`, `/fork` and
   `/model` or `/model {id}` (`:3107-3128`).
2. **Tools waiting for sign-in** block sending with `Please connect all required integrations before sending a message`
   (`:3130-3133`).
3. **Nothing to send** (no text, no file): `Please enter a prompt` (`:3134-3137`).
4. **No usable model**: `Model not selected` (`:3138-3141`). A model that has been removed or hidden since
   the chat was opened becomes an empty selection at this point (`:3099-3105`).
5. **Chat Variables**: conflicting definitions between the selected models show the conflict list and
   `Chat Variables have conflicting model definitions`; missing required values open the form (`:3142-3151`).
6. **Too many files** (admin limit, none by default):
   `You can only chat with a maximum of {maxCount} file(s) at a time.` (`:3153-3163`).
7. **Web search confirmation** (admin switch, off by default): the **Use Web Search?** dialog (`:3165-3173`).
8. **A file is still uploading or failed**: the message goes into the queue instead (`:3175-3189`).
9. **A response is still generating**: queued, or (queue off) the running response is stopped first
   (`:3191-3214`; 5.9).
10. **Send**: the composer is cleared and a user message is added under the message currently shown,
    carrying the text, attachments and the list of selected models (`:2908-2954`). One empty response is
    added per selected model and a single request goes to the server, which fans out to every model
    (`:3226-3391`). If an image is attached and a selected model lacks the vision capability, the user sees
    `Model {modelName} is not vision capable` but the request still goes ahead (`:3336-3358`).
11. **First message of a new chat**: the server creates the chat and returns its id; the address changes
    to `/c/{id}` and the chat appears in the sidebar (`:3677-3706`). The browser asks the server to
    generate a title and tags for new chats (if **Title Auto-Generation** and **Chat Tags Auto-Generation**
    are on) and follow-up suggestions for every reply (**Follow-Up Auto-Generation**) (`:3628-3640`).
12. **Streaming**: the reply arrives over the websocket and fills in the response
    (`:1203-1421`, `:2761-2902`). While it streams, the browser sends a usage heartbeat every second
    (`:2623-2631`).
13. **When the reply finishes**: optional auto-copy (**Auto-Copy Response to Clipboard**) and auto
    read-aloud, the sidebar list refreshes, and any queued messages are sent (`:2855-2899`).

### 5.5 Keyboard Behaviour: Enter, Shift+Enter and Friends

The setting **Enter Key Behavior** (Settings > Interface, Input section) has two values,
`Enter to Send` (default) and `Ctrl+Enter to Send`; its description is
`Choose whether Enter sends immediately or uses Ctrl+Enter.`
(`src/lib/components/common/InterfaceSettings.svelte:1588-1610`;
`src/lib/i18n/locales/en-US/translation.json:2913-2914`, `:528`, `:854`).

| Key | Default ("Enter to Send") | With "Ctrl+Enter to Send" | Source |
|---|---|---|---|
| Enter | Sends | Inserts a new line | `src/lib/components/chat/MessageInput.svelte:2155-2165` |
| Shift+Enter | New line | New line | `src/lib/components/common/RichTextInput.svelte:1172-1181` |
| Ctrl+Enter (Cmd+Enter on a Mac) | No effect | Sends | `src/lib/components/chat/MessageInput.svelte:2113`, `:2155-2158` |
| Enter inside a list, code block or heading | Continues the list or block; does not send | Same | `src/lib/components/common/RichTextInput.svelte:1183-1192` |
| Enter while the `/`, `#`, `@`, `$` or `:` pop-up is open | Picks the highlighted item | Same | `src/lib/components/chat/MessageInput/CommandSuggestionList.svelte:56-83`; `src/lib/components/chat/MessageInput.svelte:2138` |
| Enter on a phone or tablet | Never sends; use the send button | Same | `src/lib/components/chat/MessageInput.svelte:2139-2146` |
| Enter while composing Chinese or Japanese (IME) | Confirms the character, does not send | Same | `src/lib/components/chat/MessageInput.svelte:701-725`, `:2147-2149` |
| Tab | Accepts a grey suggestion (autocomplete or first follow-up); otherwise jumps to the next `{{placeholder}}`; in a code block inserts a tab | Same | `src/lib/components/common/RichTextInput.svelte:1146-1162`; `src/lib/components/common/RichTextInput/AutoCompletion.js` |
| Up arrow in an empty composer | Opens **Edit** on your last message | Same | `src/lib/components/chat/MessageInput.svelte:2121-2136` |
| Escape | Stops the response and clears the @-model, tools, filters and toggles | Same | `src/lib/components/chat/MessageInput.svelte:2117-2119`, `:2169-2178` |

Other typing behaviour:

- With **Rich Text Input for Chat** on (default), Markdown typed in the box becomes formatting (lists,
  code blocks, tables); single asterisks are kept literally so prompts are not italicized by accident
  (`src/lib/components/common/RichTextInput.svelte:185-193`, `:810-852`). With it off, the box is plain
  text. **Show Formatting Toolbar** adds a pop-up toolbar (`H1`, `H2`, `H3`, `Bullet List`, `Ordered List`,
  `Task List`, `Bold`, `Italic`, `Underline`, `Strikethrough`, `Code Block`, `Emoji` and list indent buttons)
  (`src/lib/components/common/RichTextInput/FormattingButtons.svelte:31-199`).
- **Pasting more than 1,000 characters** with **Paste Large Text as File** on attaches the text as a
  file named `Pasted_Text_{timestamp}.txt` instead of putting it in the box; holding Shift while pasting
  skips this (`src/lib/components/chat/MessageInput.svelte:2180-2205`; `src/lib/constants.ts:130`).
  Pasted images and files are attached (`:2206-2212`).
- **Prompt Autocompletion** (needs the admin switch) shows grey suggested text after a one-second pause;
  Tab or a right swipe accepts it (`src/lib/components/common/RichTextInput/AutoCompletion.js`;
  `src/lib/components/chat/MessageInput.svelte:2081-2103`).
- In the message **edit** box, Escape cancels and Ctrl or Cmd+Enter confirms
  (`src/lib/components/chat/Messages/UserMessage.svelte:295-306`;
  `src/lib/components/chat/Messages/ResponseMessage.svelte:799-810`).

### 5.6 Attaching Files, Pages, Notes, Knowledge and Other Chats

**The + (More) menu** (`src/lib/components/chat/MessageInput/InputMenu.svelte:126-720`), top to bottom:

| Item | What it does | Shown when |
|---|---|---|
| **Tool Permissions** | Submenu to choose `Full access` (`Run tools without asking for approval.`) or `Ask for approval` (`Stop before each tool call until you allow or deny it.`) | Admin tool permissions switch on (`:54-65`, `:146-185`, `:545-593`) |
| **Upload Files** | Opens the file picker (`:195-210`) | Always; greyed without upload rights |
| **Capture** | On a computer, a screen capture (the browser asks which screen); on a phone, the camera (`:221-243`; `src/lib/components/chat/MessageInput.svelte:861-897`) | Always; greyed without upload rights |
| **Attach Webpage** | A form `Attach Webpage` with `Webpage URLs`, one per line, and **Add**; invalid entries give `Please enter a valid URL.` (`:252-266`; `src/lib/components/chat/MessageInput/AttachWebpageModal.svelte:20-94`) | Always; greyed without `chat.web_upload` |
| **Attach Files** | Searchable list of the user's earlier uploads, 50 at a time (`:277-298`; `src/lib/components/chat/MessageInput/InputMenu/Files.svelte:61-169`) | Always; greyed and inactive without upload rights |
| **Attach Notes** | Searchable list of notes (`:301-331`; `src/lib/components/chat/MessageInput/InputMenu/Notes.svelte`) | Admin notes switch on; greyed without upload rights but still opens |
| **Attach Knowledge** | Searchable list of knowledge bases; the arrow (`Show Files`) lists single files inside (`:341-360`; `src/lib/components/chat/MessageInput/InputMenu/Knowledge.svelte:187-345`) | Always; greyed without upload rights but still opens |
| **Reference Chats** | Searchable list of the user's other chats (`:371-390`; `src/lib/components/chat/MessageInput/InputMenu/Chats.svelte`) | Always; greyed without upload rights but still opens |
| **Google Drive** / **Microsoft OneDrive** (`personal` or `work/school`) | Cloud pickers (`:393-541`, `:670-716`) | Admin switches on and upload rights |

**Other ways to attach** (`src/lib/components/chat/MessageInput.svelte:1218-1326`): drag files onto the
chat (a blurred `Drag and Drop Container` overlay appears); drag a chat, folder or note from the sidebar
to add it as a reference; drag a model to make it the @-model; paste images or files; type `#` for
knowledge, folders, files or a web address, or `@` for models, knowledge and (with a terminal selected)
terminal files (section 5.8).

**Upload rules and messages** (`src/lib/components/chat/MessageInput.svelte:918-1197`):

1. Without `chat.file_upload`: `You do not have permission to upload files.` (`:919-922`).
2. If a selected model lacks file-upload capability: `Model(s) do not support file upload` (`:926-929`).
3. Over the admin file-count limit: `You can only chat with a maximum of {maxCount} file(s) at a time.`
   (`:1090-1100`). Over the admin size limit: `File size should not exceed {maxSize} MB.` (`:1110-1124`).
   Neither limit exists by default (`backend/open_webui/config.py:981-983`).
4. Images need every selected model to have vision: `Selected model(s) do not support image inputs`
   (`:1126-1130`). Images are shrunk when the user's **Image Compression** is on or the admin set a
   maximum width or height; iPhone HEIC photos are converted to JPEG first (`:1132-1192`).
5. An empty file: `You cannot upload an empty file.` (`:949-952`).
6. During upload the chip shows a spinner. A server warning about the file (for example partial text
   extraction) appears as a yellow warning pop-up while the file still attaches (`:1025-1028`). A failed
   upload removes the chip and shows the error (`:1039-1049`).
7. In a **temporary chat** nothing is uploaded to the server: text is extracted in the browser, and images
   stay inside the message; a failure shows `Failed to extract content from the file: {error}` or
   `Failed to extract content from the file.` (`:1052-1084`, `:1176-1183`).

What happens to uploads on the server, and the size and type limits, is in `files-uploads-and-storage.md`.

### 5.7 Integrations: Tools, Skills, Filters, Web Search, Image and Code Interpreter

The **Integrations** menu (`src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:293-735`):

- **Tools** with a count opens a searchable list (`Search tools`, `No tools found`); each tool has a
  switch, an optional valves knob and, for connected sign-in tools, a `Disconnect OAuth` button
  (`:314-335`, `:523-654`). A tool that needs the user to sign in to another service is dimmed; clicking it
  starts that sign-in and the draft is saved so it is restored afterwards (`:244-258`;
  `src/lib/components/chat/Chat.svelte:4073-4085`).
- **Skills** with a count opens a searchable list (`Search skills`, `No skills found`); terminal skills are
  labelled `Terminal` (`:337-357`, `:655-731`).
- **Filters** the model allows to be toggled, each with a switch and optional valves knob (`:364-442`).
- **Web Search** (tooltip `Search the internet`), **Image** (`Generate an image`) and **Code Interpreter**
  (`Execute code for analysis`), each with a switch (`:444-521`).

Anything switched on also shows as a chip in the composer; clicking a chip (an X appears on hover)
switches it off (`src/lib/components/chat/MessageInput.svelte:2413-2544`).

**Defaults from the model.** When exactly one model is selected, its default tools, skills, filters and
features (web search, image, code interpreter) are switched on automatically, and switching models resets
all toggles to the new model's defaults (`src/lib/components/chat/Chat.svelte:736-744`, `:970-982`,
`:1008-1120`). Tools that need sign-in become amber **Click to connect** chips
(`src/lib/components/chat/MessageInput.svelte:2546-2560`).

**Web search confirmation.** If the admin switched on web search confirmation, turning on Web Search (or
sending with it on) opens **Use Web Search?** with either the admin's custom text or
`Your query will be sent to the configured web search provider.` and buttons **Continue** / **Cancel**
(`src/lib/components/chat/Chat.svelte:357-379`, `:4130-4140`, `:4220-4235`). Confirming lasts until web
search is switched off; cancelling switches it off. The user setting **Web Search in Chat** set to always
keeps web search on for every message when all selected models support it (`:342-355`).

### 5.8 Slash Commands, Prompts and Variables

Typing a trigger character opens a pop-up list (`src/lib/components/chat/MessageInput.svelte:1366-1587`;
`src/lib/components/chat/MessageInput/CommandSuggestionList.svelte:92-258`):

| Type | Shows | Picking an item |
|---|---|---|
| `/` | `Commands`, `Prompts` (the workspace prompts whose command matches) and `Skills` | Runs the command, inserts the prompt text, or adds a skill mention (*precision 2026-10-09, read from code, to confirm in a test environment: a skill picked from `/` may be inserted with the editor's default `@` marker, which the server's skill-mention pattern does not match, so it may not count as a `$` mention; see `prompts-and-skills.md` sections 1 and 4.4*) |
| `#` | A typed web or YouTube address, `Folders`, `Collections` (knowledge bases) and `Files` | Attaches it |
| `@` | Terminal files (with a terminal selected), a typed address, folders, knowledge, files, then `Models` | Attaches it, or makes the model the @-model |
| `$` | Skills | Adds a skill mention |
| `:` + two letters | `Emojis` (up to 50) | Inserts the emoji |

A web address that is not valid gives
`Oops! Looks like the URL is invalid. Please double-check and try again.`
(`src/lib/components/chat/MessageInput/Commands/AtCommands.svelte:204-208`;
`src/lib/components/chat/MessageInput/Commands/Knowledge.svelte:217-218`).

**Commands** (`src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte:53-440`; only those that
apply are listed):

| Command | Label and hint in the list | Effect |
|---|---|---|
| `/temporary` | `Temporary` with `On`/`Off`; tooltip `Toggle temporary chat for this new chat.` | Switches temporary chat (new chats only) |
| `/compact` | `Compact` with `{percent}% full`; tooltip `Shorten older messages so this chat can keep going.` | Compacts the chat (admin switch); greyed while a response runs |
| `/fork` | `Fork` with `Current branch`; tooltip `Fork the current chat branch into a new chat.` | Copies the current branch into a new chat; greyed while a response runs |
| `/status` | `Status` with `Check what is running in this chat.` | Opens the status panel |
| `/model` | `Model`; tooltip `Show or switch the current model.` | Opens the model selector; typing `/model {id}` and sending switches directly and shows `Model switched to: {id}` |
| `/settings` | `Settings`; tooltip `Open settings.` | Opens Settings |
| `/skills:create` | `Create skill`; tooltip `Create a reusable terminal skill from this chat.` | Only with a terminal selected and some chat content |

**Prompt variables.** When a prompt is inserted (from `/`, a suggestion card or a follow-up), built-in
placeholders are filled first (`src/lib/components/chat/MessageInput.svelte:283-402`):
`{{CLIPBOARD}}` (asks for clipboard access; refusal shows `Failed to read clipboard contents`; images on
the clipboard are attached), `{{USER_LOCATION}}` (browser location; refusal shows
`Location access not allowed` and inserts `LOCATION_UNKNOWN`), `{{USER_NAME}}`, `{{USER_EMAIL}}`,
`{{USER_BIO}}`, `{{USER_GENDER}}`, `{{USER_BIRTH_DATE}}`, `{{USER_AGE}}`, `{{USER_LANGUAGE}}`,
`{{CURRENT_DATE}}`, `{{CURRENT_TIME}}`, `{{CURRENT_DATETIME}}`, `{{CURRENT_TIMEZONE}}` and
`{{CURRENT_WEEKDAY}}`. `{{USER_NAME}}` falls back to `User`; the e-mail, bio, gender, birth date and age
placeholders are left untouched when that profile field is empty, and are then treated as input variables
(below). These fill
in the user's own profile details, so they reach the model only when a prompt uses them.

Any other `{{name}}` or `{{name | type...}}` placeholder then opens the **Input Variables** form
(`src/lib/components/chat/MessageInput.svelte:263-281`; `src/lib/utils/index.ts:1731-1751`;
`src/lib/components/chat/MessageInput/InputVariablesModal.svelte`). Fields can be text, a list
(`Select an option`), a checkbox (`Enter value (true/false)`), a colour (`Enter hex color (e.g. #FF0000)`),
date, time, month, e-mail, number, range (`Enter value`), telephone, address, a map
(`Enter coordinates (e.g. 51.505, -0.09)`) or a long text; required ones show `* required`. **Save** puts
the values into the text; **Cancel** closes the form and leaves the `{{...}}` placeholders in the
composer, where Tab jumps between them. Placeholders typed by hand do not open the form; only inserted
text does.

**Chat Variables** are different: the selected model defines them. A knob button next to the model
selector opens a **Chat Variables** form with the same field types; on a saved chat the values are stored
on the chat, and saving them can fail with `Failed to save chat variables`
(`src/lib/components/chat/Chat.svelte:640-727`, `:4211-4218`). If required values are missing when the user
sends, the form opens and the message is not sent. If two selected models define the same variable
differently, a **Chat Variables** window lists each conflicting key with the models involved under
`Selected models define incompatible Chat Variables.` (`:4179-4210`).

### 5.9 Typing While a Response Is Generating: the Message Queue

With **Enable Message Queue** on (the default), anything sent while the current response is still
generating is held, not sent (`src/lib/components/chat/Chat.svelte:3191-3208`):

1. The composer clears and the message appears in a box above it, with an arrow icon, its text (or
   `Empty message` when it only has files), file chips with a spinner while uploading, and
   `Upload failed` if a file failed (`src/lib/components/chat/MessageInput/QueuedMessageItem.svelte:22-79`).
2. Each row has **Send now** (stops the current response and sends that item on its own; disabled with the
   tooltip `Waiting for upload` while its files upload or after a failure), **Edit** (moves the text and
   files back into the composer) and **Delete** (`:82-146`; `src/lib/components/chat/Chat.svelte:2526-2561`).
3. When the response finishes, is stopped, or ends in an error, **all queued messages are combined into
   one message**: their texts joined with blank lines and all their files together
   (`src/lib/components/chat/Chat.svelte:2487-2524`, `:1250-1262`, `:1284-1292`, `:3804-3806`).
4. If any queued item still has an uploading or failed file, nothing in the queue is sent until that item
   is edited or deleted (`:2493-2500`).
5. The queue is kept per chat in browser memory only (`src/lib/stores/index.ts:123-125`): reloading the
   page loses it. Switching to another chat keeps it, and it is sent when the user returns to an idle chat
   (`src/lib/components/chat/Chat.svelte:857-862`).

With **Enable Message Queue** off, sending while a response is generating stops that response and sends
the new message immediately (`:3209-3213`).

A message sent while one of **its own** files is still uploading is queued the same way, whatever the
setting, and goes out when the upload finishes (`:3175-3189`, `:1868-1884`).

### 5.10 Stopping a Response

The **Stop** button (a square in a circle, tooltip `Stop`) replaces the send area while a response is
active and the composer is empty (`src/lib/components/chat/MessageInput.svelte:2603-2627`); Escape in the
composer does the same (`:2117-2119`). Stopping asks the server to stop every running task of this chat and
marks every response to the current question as finished; whatever text had arrived stays
(`src/lib/components/chat/Chat.svelte:3758-3807`). Queued messages are then sent. While an ask-user card is
open the composer does not count as active, so the Stop button is not shown
(`src/lib/components/chat/MessageInput.svelte:172-176`).

### 5.11 Actions on Your Own Messages

Buttons under a user message appear on hover (always, with **Accessibility Mode**)
(`src/lib/components/chat/Messages/UserMessage.svelte:416-725`):

| Button | What it does | What changes in stored data |
|---|---|---|
| **Edit** | Opens the message in an edit box with its attachments (removable) and three buttons: **Save**, **Cancel**, **Send** (`:205-345`, `:535-562`). Hidden in read-only views | **Save** overwrites the message text and files in place and does not ask the model again; **Send** adds a new version of the question beside the old one and gets a new answer (`src/lib/components/chat/Messages.svelte:318-359`) |
| **Copy** | Copies the message text; shows `Copying to clipboard was successful!` (`:71-76`, `:564-591`) | Nothing |
| **Delete** | Asks `Delete message?` (Shift+click skips the question) (`:125-131`, `:593-626`) | Removes the message **and the answers directly under it**; the questions that followed are re-attached to the message above; the server removes the same messages (section 6.3) |
| `<` `2/3` `>` | Switches between versions of this question; double-click the counter to type a number (`:439-533`, `:628-723`) | Changes which branch is shown (section 5.13) |
| Timestamp | Short time; full date on hover (`:422-437`) | Nothing |

An empty edit gives `Please enter a message or attach a file.` (`:97-101`). **Delete** is not offered on
the very first message of a chat unless it has other versions, or while a response is generating
(`:594`; `src/lib/components/chat/Chat.svelte:4423`).

Two special kinds of message can appear in the user's position: a **Timer** row (an automation's timed
prompt, expandable) and a **Background sub-agent finished** row with a one-line summary that expands to
the full result (`src/lib/components/chat/Messages/UserMessage.svelte:346-381`;
`src/lib/components/chat/Messages/SubagentResultRow.svelte:33-66`).

### 5.12 Actions on a Response

The row under a response (`src/lib/components/chat/Messages/ResponseMessage.svelte:966-1642`) is
always visible on the last response and appears on hover on older ones. Buttons only show once the
response has finished.

| Button | Shown when | What it does | Stored-data effect |
|---|---|---|---|
| `<` `n/m` `>` | The question has more than one answer | Switches version (`:988-1083`) | Changes the shown branch |
| **Edit** | Not read-only; `chat.edit` for the `user` role | Text responses open a text box with **Save As Copy**, **Cancel** and **Save**; reasoning and tool blocks are protected from editing. Structured responses open a block editor with a **Visual** / JSON switch (`:417-478`, `:767-850`; `src/lib/components/chat/Messages/OutputEditView.svelte:231-370`) | **Save** replaces the text and keeps the previous text as `originalContent`; **Save As Copy** adds the edited text as a new version beside the original (`src/lib/components/chat/Messages.svelte:360-401`) |
| **Copy** | Always | Copies the answer text without reasoning or tool details, adding the admin's response watermark if one is set; **Copy Formatted Text** copies rich text (`:238-249`, `:1118-1144`) | Nothing |
| **Read Aloud** | `chat.tts` | Speaks the answer; click again to stop; `No content to speak` if empty (`:272-388`, `:1146-1232`) | Nothing |
| Info (i) | The response has usage data | Hover shows the token counts and timings as a small table (`:1234-1276`) | Nothing |
| **Good Response** / **Bad Response** | Not a temporary chat; admin rating switch on; `chat.rate_response` | Records the rating and opens the feedback form (`:1279-1355`) | Sets `annotation.rating` on the message and creates or updates a `feedback` row with a snapshot of the whole chat (`:482-604`) |
| **Continue Response** | Last response only; `chat.continue_response` | Asks the same model to carry on writing the same answer (`:1357-1392`; `src/lib/components/chat/Chat.svelte:3875-3899`) | Appends to the same message |
| **Regenerate** | `chat.regenerate_response` | With **Regenerate Menu** on (default) a menu: a `Suggest a change` box, **Try Again**, **Add Details**, **More Concise**; otherwise a plain button (`:1394-1504`; `src/lib/components/chat/Messages/ResponseMessage/RegenerateMenu.svelte:18-121`) | Adds a new answer beside the old one; the suggestion text is sent to the model as a regeneration instruction (`src/lib/components/chat/Chat.svelte:3842-3873`) |
| Action buttons | The model has admin-installed action functions | One button per action with its own icon (`:1506-1550`) | Whatever the action does; its reply can change messages (`src/lib/components/chat/Chat.svelte:2571-2621`) |
| **Fork chat** | Not read-only; `chat.import` | Copies the conversation up to this answer into a new chat and opens it: `Forking chat...` then `Chat forked` (`:1552-1581`; `src/lib/components/chat/Chat.svelte:3046-3089`) | New chat row |
| **Delete** | The question has more than one answer; `chat.delete_message`; greyed while generating | Asks `Delete message?`; Shift+click skips the question (`:1583-1623`) | Removes this answer and the messages directly under it (the next question); anything further down is re-attached to the question above (section 6.3) |
| **Insert into note** | Only in the notes side chat | Copies the answer into the note (`:972-986`) | The note |
| Timestamp | Always | Full date on hover (`:1625-1638`) | Nothing |

**The feedback form** after a thumbs click (`src/lib/components/chat/Messages/RateComment.svelte:106-275`):
`How would you rate this response?`, a 1 to 10 scale (`1 - Awful`, `10 - Amazing`; a thumbs-up enables 6
to 10, a thumbs-down 1 to 5), `Why?` with reason buttons (for a good answer: `Accurate information`,
`Followed instructions perfectly`, `Showcased creativity`, `Positive attitude`, `Attention to detail`,
`Thorough explanation`, `Other`; for a bad one: `Don't like the style`, `Too verbose`, `Not helpful`,
`Not factually correct`, `Didn't fully follow instructions`, `Refused when it shouldn't have`,
`Being lazy`, `Other`), a comment box (`Feel free to add specific details`), tags (the model suggests some
automatically) and **Save**, which shows `Thanks for your feedback!`. When admin community sharing is on,
a link `Leave a public review for {modelName}` with `Help the community discover great models` points to
openwebui.com (`:256-273`). For "arena" models the form names the model that really answered:
`This response was generated by "{model}"` (`:74-83`, `:106-112`).

### 5.13 Versions and Branches

A chat is a tree, not a list. Editing a question with **Send**, regenerating, **Save As Copy** or merging
adds a sibling instead of overwriting, and the arrows with `n/m` move between siblings
(`src/lib/components/chat/Messages.svelte:199-307`). Moving to a sibling shows the newest path below it
(`getDeepestChildId`). With **Scroll On Branch Change** on (default), the view scrolls to keep the
message in place.

What is saved: the whole tree is stored with every save, together with `history.currentId`, the message
the chat is showing (`src/lib/components/chat/Chat.svelte:4002-4014`). Arrow navigation in a normal
(single-model) chat changes `currentId` in the browser; it is written to the server the next time the
chat is saved (for example when a message is sent). Navigation inside a multi-model answer, and clicking a
node in the **Overview**, save at once (`src/lib/components/chat/Messages/MultiResponseMessages.svelte:84-133`;
`src/lib/components/chat/Chat.svelte:1122-1144`). See section 14 for the consequence.

### 5.14 Several Models at Once

When several models are selected (users need `chat.multiple_models` to keep more than one in a saved
chat), one question gets one answer per model (`src/lib/components/chat/Chat.svelte:3259-3302`):

- **Side by side** (default): one card per model in a horizontal row; the card currently counted as "the"
  answer has a solid border, the others a dashed one; clicking a card makes it the current branch
  (`src/lib/components/chat/Messages/MultiResponseMessages.svelte:321-385`, `:193-202`).
- **In tabs** with **Display Multi-model Responses in Tabs** on: a tab per model name (`:234-319`).
- Each column has its own versions; **Regenerate** in a column re-asks only that model (`:302-307`,
  `:366-371`; `src/lib/components/chat/Chat.svelte:3864-3870`).
- When every column has finished, the last question shows **Merge Responses**: a model is asked to
  combine the answers, which stream into a **Merged Response** block under the cards
  (`src/lib/components/chat/Messages/MultiResponseMessages.svelte:389-457`;
  `src/lib/components/chat/Chat.svelte:3901-3951`). The merged text is stored as `merged` on the answer
  the chat is currently showing for that question (`:3901-3909`).
- Voice mode refuses several models: `Select only one model to call`
  (`src/lib/components/chat/MessageInput.svelte:2679-2683`).
- A rating on one column records the other columns' model ids as siblings
  (`src/lib/components/chat/Messages/ResponseMessage.svelte:507-519`).

### 5.15 How a Response Renders

While a response streams, a thin blinking bar marks the end of the text
(`src/lib/components/chat/Messages/ResponseMessage.svelte:922-927`); with **Fade Effect for Streaming
Text** on (default) new words fade in (`src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens/TextToken.svelte:10-18`);
with **Response Auto-Scroll** on the view follows the text (`src/lib/components/chat/Chat.svelte:2469-2483`).
With **Render Markdown in Assistant Messages** off the answer is shown as plain text, apart from reasoning
and tool blocks (`src/lib/components/chat/Messages/ContentRenderer.svelte:314-361`).

Markdown is parsed with `marked` and these extensions: KaTeX maths, `<details>` blocks, citations,
footnotes, `:::` colon fences, double-tilde-only strikethrough, and `@`, `#`, `$` mentions
(`src/lib/components/chat/Messages/Markdown.svelte:1-28`). The built-in values `{{USER_NAME}}` and the
model name are substituted in the displayed text (`:73`).

| Element | How it looks and behaves | Source |
|---|---|---|
| Headings, paragraphs, lists | Standard. Task-list checkboxes are drawn but ticking them in an answer saves nothing | `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte:195-442`; `src/lib/components/chat/Messages/ResponseMessage.svelte:878-880` |
| Tables | Scrollable; on hover **Copy** (the Markdown) and **Export to CSV** (`table-{id}-{n}.csv`, UTF-8) | `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte:152-188`, `:231-315` |
| Alerts | `> [!NOTE]`, `TIP`, `IMPORTANT`, `WARNING`, `CAUTION` become coloured boxes headed by the type | `src/lib/components/chat/Messages/Markdown/AlertRenderer.svelte:18-117` |
| Links | Open in a new tab (`rel="nofollow"`); links to this site's chats, notes or channels open in the app; a same-site note link shows as a **Note** card with title and `By {name}` | `src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens.svelte:52-99`; `src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens/NoteLinkToken.svelte:44-73` |
| Images | Shown inline, including from other sites | `src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens.svelte:100-101` |
| Inline code | Click copies it: `Copied to clipboard` | `src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens/CodespanToken.svelte:17-25` |
| Footnotes `[^1]` | Superscript marker | `src/lib/utils/marked/footnote-extension.ts:11-32` |
| Strikethrough | Only `~~text~~`; a single `~` stays literal | `src/lib/utils/marked/strikethrough-extension.ts:1-29` |
| Mentions | `@model` chips (click opens a new chat with that model), `#channel` chips; `$skill` only for active skills | `src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens/MentionToken.svelte:26-122` |
| `:::type` fences | A bordered box headed by the type in title case (or its `subject`, plus `· {recipient}`), with **Copy** | `src/lib/utils/marked/colon-fence-extension.ts:20-60`; `src/lib/components/chat/Messages/Markdown/ColonFenceBlock.svelte:25-91` |
| Maths | KaTeX (with chemistry `\ce{}` and units `\pu{}`) for `$...$`, `$$...$$`, `\(...\)`, `\[...\]` and `\begin{equation}`; a dollar sign must be next to a space or punctuation to count; clicking a formula copies its LaTeX (`Copied to clipboard`) | `src/lib/utils/marked/katex-extension.ts:1-20`; `src/lib/components/chat/Messages/Markdown/KatexRenderer.svelte:30-63` |
| Raw HTML | Sanitized. Only `<video>`, `<audio>`, YouTube embeds, other `<iframe>`s (fully sandboxed), `<br>`, status tags and HTML files are rendered; any other tag is shown as text | `src/lib/components/chat/Messages/Markdown/HTMLToken.svelte:14-138` |

**Code blocks** (`src/lib/components/chat/Messages/CodeBlock.svelte:436-651`). A header shows the language
and buttons:

- **Collapse** / **Expand** (with **Always Collapse Code Blocks** they start collapsed, showing
  `{COUNT} hidden lines`) (`:485-496`, `:587-597`).
- **Run** for Python (`python`, `py`, or unlabelled code that looks like Python), when the admin's code
  execution is on (default). It shows `Running` then an output area with `STDOUT/STDERR`, `RESULT` and any
  plotted images (`:498-519`, `:600-647`). With the admin engine set to Jupyter the code runs on the server;
  otherwise (default `pyodide`) it runs inside the browser, loading common packages automatically, and gives
  up after 60 seconds with `Execution Time Limit Exceeded` (`:141-357`;
  `backend/open_webui/config.py:411`). Details: `code-execution-and-interpreter.md`.
- **Save** / **Saved** (not in read-only views): the block is an editable code editor; Save writes the
  edited code back into the stored answer (`:521-528`, `:557-571`;
  `src/lib/components/chat/Messages/ResponseMessage.svelte:892-916`).
- **Copy** / **Copied** (`:530-533`).
- **Preview** for `html` and `svg` blocks opens the Artifacts panel (`:535-544`).
- `diff` and `patch` blocks are drawn as coloured line-by-line changes with line numbers, and get an
  **Edit** / **Done** switch (`:473-484`, `:558-559`; `src/lib/components/chat/Messages/DiffBlock.svelte`).
- `mermaid`, `vega` and `vega-lite` blocks become diagrams (pan and zoom) once the closing fence arrives; a
  broken diagram shows a red box with `Failed to render diagram: {message}` or
  `Failed to render visualization: {message}` above the source (`:359-391`, `:441-459`).

With **Detect Artifacts Automatically** on (default), a finished `html` or `svg` block opens the Artifacts
panel by itself, on screens wider than a phone and only in a saved chat
(`src/lib/components/chat/Messages/ContentRenderer.svelte:142-171`).

**Embedded web content and sandbox settings.** Four per-user settings control what embedded pages may do.
Defaults differ by place in the code:

| Where | Scripts | Forms | Downloads | Same origin | Source |
|---|---|---|---|---|---|
| Artifacts panel | setting, default on | setting, default on | setting, default on | setting, default off | `src/lib/components/chat/Artifacts.svelte:246-264` |
| HTML file embedded in an answer (`<file type="html">`) | setting, default on | setting, default on | setting, default on | setting, default off | `src/lib/components/chat/Messages/Markdown/HTMLToken.svelte:106-131` |
| HTML source in the citation window | setting, default on | setting, default on | setting, default on | setting, default off | `src/lib/components/chat/Messages/Citations/CitationModal.svelte:216-230` |
| Embeds attached to a response | always on | setting, default on | not set | setting, default off | `src/lib/components/chat/Messages/ResponseMessage.svelte:748-765` |
| Embeds returned by a tool | always on | setting, default **off** | not set | setting, default off | `src/lib/components/common/ToolCallDisplay.svelte:186-196`; `src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte:309-322` |
| Plain `<iframe>` in the answer text | fully sandboxed (nothing allowed) | | | | `src/lib/components/chat/Messages/Markdown/HTMLToken.svelte:69-88` |

The settings are **iframe Sandbox Allow Scripts**, **iframe Sandbox Allow Forms**, **iframe Sandbox Allow
Downloads** and **iframe Sandbox Allow Same Origin** (`src/lib/i18n/locales/en-US/translation.json:2926-2932`).
The Artifacts panel and HTML sources also get the admin's content security policy (`IFRAME_CSP`,
environment only, empty by default; `backend/open_webui/config.py:1731`).

### 5.16 Citations and Sources

When a response used knowledge, files or web search, the server attaches **sources**
(`src/lib/components/chat/Chat.svelte:1328-1353`, `:2803-2805`).

- **Inline chips.** `[1]`, `[1,2]` or `[1#section]` in the answer become small grey chips showing the
  source's name or web domain (long names shortened as `first 15...last 10`). Several sources in one chip
  read `{first} +{n}` and list the others on hover. Clicking a chip opens that source
  (`src/lib/utils/marked/citation-extension.ts:12-57`;
  `src/lib/components/chat/Messages/Markdown/SourceToken.svelte:42-80`;
  `src/lib/components/chat/Messages/Markdown/Source.svelte:23-53`). Without any sources the markers stay as
  plain text (`src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens.svelte:143-148`).
- **The Sources button** under the answer reads `1 Source` or `{COUNT} Sources`, with up to three site
  icons; it expands into a numbered list (`src/lib/components/chat/Messages/Citations.svelte:171-249`).
- **The citation window** (`src/lib/components/chat/Messages/Citations/CitationModal.svelte:99-271`): the
  source name as a link (`Open link` or `Open file`; a file opens at the cited page), or `Citation`;
  `Parameters` for tool sources; each excerpt under `Content` (for web pages the word links to the exact
  passage), a `Relevance` score (a coloured percentage when every score is between -1 and 1 — green 80 and
  above, yellow 60, orange 40, red below — otherwise the raw distance, and hidden when exactly one score is
  an outlier), `(page N)`, and the text rendered as Markdown, cut at 10,000 characters with
  `Show all ({COUNT} characters)` (setting **Render Markdown in Previews**).
- **Sources with an embed address** open in the side panel instead (or in a new tab in a read-only view);
  the embedded page is given the chat, message and source ids as address parameters
  (`src/lib/components/chat/Messages/Citations.svelte:45-67`;
  `src/lib/components/chat/ChatControls/Embeds.svelte:12-42`).
- **Site icons** next to web sources and web-search results are fetched by the user's browser from
  Google's favicon service (`www.google.com/s2/favicons`), and the search-query line in a web-search status
  links to a Google search (`src/lib/components/chat/Messages/Citations.svelte:186-198`;
  `src/lib/components/chat/Messages/ResponseMessage/WebSearchResults.svelte:27-113`).
- If the model's `citations` capability is off, markers are removed from the text and no Sources button
  appears (`src/lib/components/chat/Messages/ContentRenderer.svelte:128-138`;
  `src/lib/components/chat/Messages/ResponseMessage.svelte:934-942`). The fork's **Inline Citations**
  switch removes only the markers (5.23).

### 5.17 Status Lines, Reasoning, Tool Calls and Code Analysis (Normal View)

These are the "processing details" that the fork can hide (5.22). With **Hide Processing Details** off:

- **Status line** above the answer: the latest step, shimmering while it runs; clicking it toggles the
  full list of steps when there is more than one (`Toggle status history`)
  (`src/lib/components/chat/Messages/ResponseMessage/StatusHistory.svelte:30-76`). Known steps are worded by
  the browser, for example `Searching Knowledge for "{searchQuery}"`, `Searching` with query chips,
  `Querying`, `No sources found`, `Retrieved 1 source`, `Retrieved {count} sources`, `Searching the web`,
  `Generating search query`; other steps show the server's text
  (`src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:13-151`). A web search
  step expands to show the query and the pages found. The full catalogue is in
  `in-chat-status-and-response-messages.md`.
- **Reasoning** (thinking models): a collapsible line `Thinking...` that becomes
  `Thought for less than a second`, `Thought for {DURATION} seconds`, `Thought for {DURATION}` (over a
  minute) or `Thought`; opening it shows the reasoning as a quote
  (`src/lib/components/common/Collapsible.svelte:96-113`;
  `src/lib/components/chat/Messages/structuredOutput.ts:238-255`).
- **Code analysis** (code interpreter): `Analyzing...` then `Analyzed`, opening to the code
  (`src/lib/components/common/Collapsible.svelte:114-119`).
- **Tool calls**: a card per call whose label reads `Preparing {NAME}...`, `Executing {NAME}...`,
  `View Result from {NAME}`, `Allow {NAME}?`, `Input needed` or `Denied {NAME}`, with a spinner, green tick
  or red cross. Opening it shows `Input` (the arguments) and `Output` (cut at 10,000 characters with
  `Show all ({COUNT} characters)`). The cross also appears when the tool's output looks like an error
  (starts with "error:", "exception:", "traceback" or "http error!", or reports a failed status)
  (`src/lib/components/common/ToolCallDisplay.svelte:94-158`, `:199-370`). Images a tool returns are shown
  under the card (`:372-387`). A delegated task reads `Sub-agent: "{task}"` or
  `Background sub-agent: "{task}"` (`src/lib/components/chat/Messages/structuredOutput.ts:202-214`).
- **Groups**: several reasoning, analysis or tool blocks in a row fold into one line, `Exploring` while
  running and `Explored` afterwards, followed by the tool names (with counts) and `Ran {COUNT} analysis` /
  `Ran {COUNT} analyses` (`src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte:97-265`).
- **Always Expand Details** opens all of these by default
  (`src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte:467`, `:528`).
- **Code execution chips** under the answer (from the server-side code interpreter) open a window titled
  `Code execution: {name}` with a badge (`error`, `success`, `incomplete`), the code, `ERROR`, `OUTPUT` and
  `Files` (`src/lib/components/chat/Messages/CodeExecutions.svelte:26-63`;
  `src/lib/components/chat/Messages/CodeExecutionModal.svelte:14-109`).
- **Task list** above the composer: `{done} out of {total} tasks completed` with a checklist while the
  model works through tasks (`src/lib/components/chat/Messages/ResponseMessage/TaskList.svelte:19-115`).
- **Files shown by a terminal tool** appear as a preview card with **Download** and **Open**, or
  `Terminal unavailable` / `No preview available` (`src/lib/components/chat/Messages/TerminalOutputFile.svelte:235-319`).

Structured responses (a list of output items) and older text responses with embedded `<details>` blocks
produce the same display (`src/lib/components/chat/Messages/structuredOutput.ts:344-444`;
`src/lib/components/chat/Messages/StructuredOutputRenderer.svelte:74-228`;
`src/lib/utils/marked/extension.ts:29-60`).

### 5.18 Tool Approval Requests and Ask-User Cards

**Tool approval.** When the admin has enabled tool permissions and the user picks
**Ask for approval** in **+ > Tool Permissions**, the model stops before each tool call. The call card
reads `Allow {NAME}?` with **Allow** and **Deny** (a group of several waiting calls lists each one with its
own buttons) (`src/lib/components/common/ToolCallDisplay.svelte:258-276`;
`src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte:234-298`). Keyboard:
Cmd+Alt+Enter allows and Cmd+Alt+Backspace denies the latest one.

- **Allow** runs the tool and the model continues in the same response; **Deny** records the tool output
  `Error: tool call rejected by user.` and the model continues without it
  (`backend/open_webui/main.py:1893-1910`; `backend/open_webui/utils/tool_approval.py:60-73`).
- The choice is stored in the user's settings and in the chat's settings
  (`src/lib/components/chat/Chat.svelte:432-463`). Switching back to **Full access** automatically allows the
  most recent waiting call (`:465-503`).
- Errors from the server appear as a red pop-up, for example `Tool call has already been resolved.`
  (`backend/open_webui/utils/tool_approval.py:56-58`).

**Ask-user cards** (`src/lib/components/chat/AskUserCard.svelte:173-303`). The `ask_user` tool, or a
plugin, can ask the user questions. A card appears **above the composer** (not inside the answer):

1. A header, `1/3` when there are several questions, and the question text.
2. Options with descriptions; the first is marked `Recommended`. Clicking an option records it and moves to
   the next question.
3. `Other` with a `Type your answer` box (unless the tool disallows it); Enter moves on.
4. **Cancel** (refuses the request), **Previous**, **Next**, and on the last question **Submit answers**
   (greyed until every question has an answer).
5. A time limit, if the tool set one, cancels the card automatically (`:59-69`).

Answering or cancelling a saved `ask_user` call is sent to the server, which resumes the response
(`src/lib/components/chat/Chat.svelte:559-623`). While the card is open the Stop button is not shown.

**Other plugin pop-ups.** Plugins can also open a confirmation dialog or a one-field input dialog with
their own title and text (`src/lib/components/chat/Chat.svelte:1367-1401`, `:4249-4270`), or show
pop-up notifications (`:1354-1366`).

### 5.19 Follow-Up Suggestions and Floating Quick Actions

- **Follow-ups**: under the last finished answer, a `Follow up` heading with suggested questions
  (`src/lib/components/chat/Messages/ResponseMessage/FollowUps.svelte:11-35`). Clicking one sends it at once
  as a new message under that answer; with **Insert Follow-Up Prompt to Input** it only fills the composer;
  **Keep Follow-Up Prompts in Chat** keeps them under older answers too
  (`src/lib/components/chat/Messages/ResponseMessage.svelte:1658-1673`). The first suggestion also appears
  as grey text in the empty composer; Tab accepts it (`src/lib/components/chat/MessageInput.svelte:2064-2068`;
  `src/lib/components/common/RichTextInput.svelte:321-341`). They exist only while **Follow-Up
  Auto-Generation** is on (`src/lib/components/chat/Chat.svelte:3639`).
- **Floating quick actions** (setting **Floating Quick Actions**, default on): selecting text in a finished
  answer shows **Ask** and **Explain** buttons. **Explain** puts the selection, quoted, plus the word
  "Explain" into the composer; **Ask** first shows an `Ask a question` box. Nothing is sent until the user
  presses Send. Users can define their own actions
  (`src/lib/components/chat/ContentRenderer/FloatingButtons.svelte:19-170`;
  `src/lib/components/chat/Messages/ContentRenderer.svelte:183-286`, `:364-373`).

### 5.20 The Side Panel: Controls, Files, Overview, Artifacts and Embeds

Opened with the **Controls** button in the top bar (needs `chat.controls`). On screens 1,024 pixels wide or
more it is a resizable panel (at least 350 pixels, width remembered in the browser); on smaller screens it is
a full-height drawer (`src/lib/components/chat/ChatControls.svelte:122-138`, `:195-436`). It closes itself on a
new, unsaved chat (`:189`). What it shows, in priority order: the voice call, an embed, the Artifacts
panel, otherwise the tabs.

**Tabs** (`src/lib/components/chat/ChatControls.svelte:63-99`):

- **Controls** (`src/lib/components/chat/Controls/Controls.svelte:40-149`): `Files` (the documents attached
  to this chat; removing one here stops it being used), `Valves` (choose `Tools` or `Functions`, then
  `Select a tool` / `Select a function`; changes save automatically after half a second and show
  `Valves updated`; `src/lib/components/chat/Controls/Valves.svelte:41-230`), `System Prompt` (a text box,
  placeholder `Enter system prompt`, for this chat only) and `Advanced Params` (model parameters for this
  chat). Each section's open or closed state is remembered in the browser. Changes to the system prompt,
  parameters and files are saved to the chat automatically about 0.4 seconds after a change
  (`src/lib/components/chat/Chat.svelte:809-813`, `:4016-4030`).
- **Files**: the file browser of a selected terminal, or of the in-browser Python sandbox when Code
  Interpreter is on and the admin engine is not Jupyter (`src/lib/components/chat/ChatControls.svelte:83-86`;
  `code-execution-and-interpreter.md`).
- **Overview**: a tree of every message in the chat with user names or model names, two lines of text
  (errors in red), and arrows between them; the current path is animated. Clicking a node jumps to that
  branch (and saves it). Buttons: a heart (`Add to favorites` / `Remove from favorites`), `Viewport Pinned` /
  `Viewport Unpinned`, `Vertical Layout`, `Horizontal Layout`
  (`src/lib/components/chat/Overview/View.svelte:65-195`; `src/lib/components/chat/Overview/Node.svelte:26-106`;
  `src/lib/components/chat/Overview/Flow.svelte:28-73`).

**Artifacts panel** (`src/lib/components/chat/Artifacts.svelte:124-280`): the HTML or SVG code found in the
chat's answers on the current branch (`src/lib/components/chat/Chat.svelte:1949-2002`), with
`Previous version`, `Version {selectedVersion} of {totalVersions}`, `Next version`, **Copy**, **Download**
(saves `artifact-{chatId}-{n}.html`), `Open in full screen` and a close button. Links to other sites inside
the preview do nothing. With nothing to show: `No HTML, CSS, or JavaScript content found.`

**Embeds panel** (`src/lib/components/chat/ChatControls/Embeds.svelte:45-86`): a source's interactive page
with its title (or `Embedded Content`) as a link and a close button (`Close embed`).

### 5.21 How an Error Appears Inside a Response

1. **Where errors come from.**
   - The request never reached a model or was refused (for example the provider rejected it): the browser
     shows a red pop-up with the error text and stores it on the response
     (`src/lib/components/chat/Chat.svelte:3643-3668`, `:3670-3673`).
   - The provider failed while the answer was streaming: the server saves `error.content` on the message
     and sends a `chat:message:error` event (`backend/open_webui/utils/middleware.py:4240-4256`,
     `:4854-4868`; `src/lib/components/chat/Chat.svelte:1284-1292`).
   - An action button failed: red pop-up and the error is put on the last message
     (`src/lib/components/chat/Chat.svelte:2589-2593`).
2. **What the user sees.** Under whatever part of the answer arrived, a grey rounded box with an (i) icon
   holds the error text (`src/lib/components/chat/Messages/ResponseMessage.svelte:930-932`;
   `src/lib/components/chat/Messages/Error.svelte:40-48`). When the browser itself caught the error the text
   is `Uh-oh! There was an issue with the response.` followed on a new line by the provider's message
   (`src/lib/components/chat/Chat.svelte:3716-3756`). The box pulls the message out of the error data (a
   `message`, a `detail` or plain text) and otherwise prints the raw data; an empty error reads
   `Error submitting message` (`src/lib/components/chat/Messages/Error.svelte:6-37`).
3. **What else happens.** The response is marked finished, so the action row appears (Regenerate is the
   usual next step); knowledge-search status lines are dropped from that response
   (`src/lib/components/chat/Chat.svelte:3747-3753`); queued messages are sent.
4. **It stays.** The error is saved with the message, so it is still visible after a reload, and the
   Overview shows it in red (`src/lib/components/chat/Overview/Node.svelte:47-51`, `:85-88`).
5. **Older chats** may hold an error as the message text itself (`error: true`); then only the error box is
   shown (`src/lib/components/chat/Messages/ResponseMessage.svelte:857-859`).
6. **A response that was cut off** (for example the browser was closed, or the server restarted) and has no
   task still running is marked finished when the chat is reopened, without an error message
   (`src/lib/components/chat/Chat.svelte:2398-2412`); **Continue Response** can pick it up.

The texts the server can put in the error box (provider errors, `Failed to connect to MCP server '{server_id}'`,
and others) are catalogued in `chat-completion-pipeline-and-generation-tasks.md`
(`backend/open_webui/utils/middleware.py:3010-3011`).

### 5.22 The Fork's Hide Processing Details

**Where.** Settings > Interface > Chat > **Hide Processing Details**, a switch, default off
(`src/lib/components/common/InterfaceSettings.svelte:1358-1378`, `:80`, `:358`). Its description in the
working tree reads:
`Show "Thinking..." instead of status updates, tool calls, reasoning, and code analysis while a response is generated, and keep them hidden afterwards. Tool approval requests and images or embeds from tools still appear.`
(`src/lib/i18n/locales/en-US/translation.json:2923-2924`). The setting is saved in the user's settings
as `hideProcessingDetails` (`backend/open_webui/models/users.py:100`); an admin can preset it for everyone
through the default interface settings, and a user's own choice wins (section 7.3).

**What changes while a response is generating** (working tree,
`src/lib/components/chat/Messages/ResponseMessage.svelte:197-221`, `:920-928`):

- Until the first words of the answer arrive, a single shimmering `Thinking...` line is shown in place of
  the status line (it uses the same look as a status step,
  `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:126-148`).
- It is not shown if the response has finished or failed, or while a tool call waits for the user (an
  approval or an ask-user question), so the approval card is not mistaken for progress
  (`src/lib/components/chat/Messages/structuredOutput.ts:454-457`).
- Once answer text appears, the normal text and blinking bar take over.

**What is hidden, during and after the response:**

| Hidden | Source |
|---|---|
| The status line and its expandable history | `src/lib/components/chat/Messages/ResponseMessage.svelte:198-202`, `:720-722` |
| `<status>` lines that custom models write into the answer text | `src/lib/components/chat/Messages/Markdown/HTMLToken.svelte:89-105` |
| Reasoning blocks ("Thought for ...") and code analysis blocks ("Analyzed") | `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte:90-105`; `src/lib/components/chat/Messages/structuredOutput.ts:404-416` |
| Tool-call cards that do not need the user, and the grouped "Explored ..." line | `src/lib/components/common/ToolCallDisplay.svelte:145`, `:199-200`; the same two files above |
| Code execution chips under the answer | `src/lib/components/chat/Messages/ResponseMessage.svelte:944-946` |
| The task list above the composer | `src/lib/components/chat/MessageInput.svelte:1791-1796` |

**What still appears:** the answer; tool approval cards (**Allow** / **Deny**); the ask-user card above the
composer; images returned by tools; embeds returned by tools (without the tool-name caption); images,
files and embeds attached to the response; inline citations and the Sources button; follow-ups; error
boxes; and all action buttons (`src/lib/components/common/ToolCallDisplay.svelte:178-199`, `:372-387`).

It is a display preference only: nothing is removed from the stored chat, switching it off brings every
detail back on old and new chats, and **Copy** and **Read Aloud** behave the same either way (they never
include these details) (`src/lib/components/chat/Messages/ResponseMessage.svelte:203-204`, `:238-249`).

**Committed versus working tree.** The committed `uoft` version drew its own `Thinking...` line and kept it
up while an approved tool resumed, by inspecting the tool-call state; the uncommitted working tree replaces
that with the shared status look, a simpler "waiting on the user" test (`hasPendingToolCall`), and a change
in `src/lib/components/chat/Chat.svelte:2847-2850` that marks the response as running again when the server
reports `done: false` after an approval (section 12).

### 5.23 The Fork's Inline Citations

**Where.** Settings > Interface > Chat > **Inline Citations**, a switch, default **on**
(`src/lib/components/common/InterfaceSettings.svelte:1335-1356`, `:79`, `:357`). Description:
`Show source links within responses. When off, sources are still listed below each response.`
(`src/lib/i18n/locales/en-US/translation.json:2935-2936`). Stored as `showInlineCitations`
(`backend/open_webui/models/users.py:99`).

**When off** (`src/lib/components/chat/Messages/ContentRenderer.svelte:128-138`):

- Citation markers such as `[1]`, `[2, 3]` or `[1#section]` are removed from the answer text (outside code
  blocks and inline code), together with the space before them, so no chips appear. This applies to both
  text and structured responses (`:320`; `src/lib/components/chat/Messages/StructuredOutputRenderer.svelte:82`).
- Already-displayed answers change as soon as the switch moves (the formatting is reactive).
- The **Sources** button and the citation window are unaffected.
- **Copy** and **Read Aloud** still use the original text, so copied text keeps the `[1]` markers
  (`src/lib/components/chat/Messages/ResponseMessage.svelte:203-204`, `:1124-1126`).
- Side effect: any bracketed number in ordinary prose, such as "see step [2]", is removed too, because the
  pattern cannot tell it from a citation. Upstream already behaves this way for models whose `citations`
  capability is off.

When the model's `citations` capability is off, markers are removed whatever this switch says, and the
Sources button is hidden as well.

### 5.24 Temporary Chats, Read-Only Views and Voice Buttons

- **Temporary chat.** The dotted-bubble button in the top bar (new chats only) or `/temporary` switches it on;
  the address gets `?temporary-chat=true`, the composer border turns dashed and a `Temporary Chat` label
  appears (`src/lib/components/chat/Navbar.svelte:180-213`; `src/lib/components/chat/MessageInput.svelte:568-586`,
  `:1896-1898`). Nothing is saved on the server, attachments stay in the browser, there is no rating, and
  closing the tab loses the conversation. **Save Chat** turns it into a normal chat titled from the first
  message: `Conversation saved successfully` or `Failed to save conversation`, or `No conversation to save`
  when empty (`src/lib/components/chat/Chat.svelte:4346-4383`). **Temporary Chat by Default** and the
  `chat.temporary_enforced` permission start new chats in this mode (`:2025-2044`).
- **Read-only view.** Opening a chat that belongs to someone else shows `Read only` instead of the composer,
  hides edit, rating, regenerate and delete buttons, disables code saving and floating actions, and opens
  source embeds in a new tab (`src/lib/components/chat/Chat.svelte:391-411`, `:4433-4438`;
  `src/lib/components/chat/Messages/ResponseMessage.svelte:860-877`).
- **Dictate** (microphone, `Dictate`): asks for microphone access (`Permission denied when accessing microphone: {error}`
  on refusal), then replaces the composer with a recording bar (waveform, timer, an X to cancel and a tick,
  `Confirm recording`, to finish). The transcript is inserted at the cursor and, with the voice setting to
  send automatically, sent (`src/lib/components/chat/MessageInput.svelte:1735-1758`, `:2629-2668`;
  `src/lib/components/chat/MessageInput/VoiceRecording.svelte:174-414`, `:464-640`). The browser's own speech
  recognition is used when the admin or user chose it, otherwise the recording goes to the server.
- **Voice mode** (`Voice mode`): opens the call view in the side panel after checking for one model and a
  microphone (`src/lib/components/chat/MessageInput.svelte:2671-2733`). Everything else about voice is in
  `audio-speech-to-text-and-text-to-speech.md`.

## 6. Data Model

This area is front end; it reads and writes data through the chats API. Full table descriptions belong to
`chat-conversations-history-and-organisation.md`; this section covers the fields the screen relies on.

### 6.1 The Chat Row and Its Message Tree

The `chat` table (`backend/open_webui/models/chats.py:129-153`) stores one row per conversation. The
screen uses:

| Column | Holds | Written by this screen |
|---|---|---|
| `chat` (JSON) | `title`, `models` (selected model ids), `params` (system prompt, advanced parameters, tool approval mode), `files` (documents attached to the chat), `history` (`messages` keyed by id and `currentId`) and a flat `messages` list of the current branch | `src/lib/components/chat/Chat.svelte:4002-4014` (every save), `:4016-4030` (controls autosave), `src/lib/components/chat/Messages.svelte:176-197` (edits, ratings, deletes) |
| `variables` (JSON) | Chat Variables values | `src/lib/components/chat/Chat.svelte:714-727` |
| `tasks` (JSON) | The task list shown above the composer | Read at `src/lib/components/chat/Chat.svelte:2354-2355` |
| `current_message_id` | The message the chat opens on | Read at `src/lib/components/chat/Chat.svelte:2340-2342` |
| `last_read_at` | When the user last viewed the chat (for unread markers) | Sent over the websocket at `src/lib/components/chat/Chat.svelte:1146-1151` |

Every message in `history.messages` is a JSON object. Fields the screen reads or writes:

| Field | Meaning | Source |
|---|---|---|
| `id`, `parentId`, `childrenIds` | The tree: siblings are versions | `src/lib/components/chat/Chat.svelte:2923-2944`, `:3268-3301` |
| `role` | `user` or `assistant` | same |
| `content` | Text (older responses also embed `<details>` blocks for reasoning and tools) | `src/lib/utils/marked/extension.ts:29-60` |
| `output` | Structured response items: `message`, `reasoning`, `function_call`, `function_call_output`, `open_webui:code_interpreter`, and provider tool items | `src/lib/components/chat/Messages/structuredOutput.ts:1-98` |
| `files` | Attachments on a question, or images and files produced by a response | `src/lib/components/chat/Chat.svelte:2931`; `src/lib/components/chat/Messages/ResponseMessage.svelte:724-746` |
| `models` (question) / `model`, `modelName`, `modelIdx` (answer) | Which models were asked; which model answered and which column it belongs to | `src/lib/components/chat/Chat.svelte:2933`, `:3270-3281` |
| `done` | Finished or still streaming | `src/lib/components/chat/Chat.svelte:2847-2856` |
| `error` | `{ content }` shown in the error box | `src/lib/components/chat/Chat.svelte:3744-3746` |
| `statusHistory` | Status steps | `src/lib/components/chat/Chat.svelte:1221-1226` |
| `sources` | Citation data | `src/lib/components/chat/Chat.svelte:1346-1353` |
| `code_executions` | Code interpreter runs | `src/lib/components/chat/Chat.svelte:1329-1345` |
| `embeds` | Interactive frames | `src/lib/components/chat/Chat.svelte:1273-1283` |
| `followUps` | Suggested next questions | `src/lib/components/chat/Chat.svelte:1293-1298` |
| `usage` | Token counts shown by the info icon | `src/lib/components/chat/Chat.svelte:2843-2845` |
| `annotation` | `rating` (1 or -1), `reason`, `comment`, `tags`, `details.rating` (1 to 10) | `src/lib/components/chat/Messages/ResponseMessage.svelte:486-496`; `src/lib/components/chat/Messages/RateComment.svelte:92-99` |
| `feedbackId` | The `feedback` row for this rating | `src/lib/components/chat/Messages/ResponseMessage.svelte:548-567` |
| `originalContent` | The text before an in-place edit or before an outlet filter changed it | `src/lib/components/chat/Messages.svelte:393`; `src/lib/components/chat/Chat.svelte:1299-1315` |
| `merged` | `{ status, content }` of a Merge Responses run | `src/lib/components/chat/Chat.svelte:3901-3909` |
| `favorite` | Heart in the Overview | `src/lib/components/chat/Overview/Node.svelte:67-82` |
| `selectedModelId`, `arena` | The real model behind an arena model | `src/lib/components/chat/Chat.svelte:2838-2841` |
| `meta.internal`, `meta.type` (`timer`, `subagent`) | Special rows in the user position | `src/lib/components/chat/Messages/UserMessage.svelte:139`, `:346-381` |
| `contextSummary` | Marker left by compaction; context counting starts there | `src/lib/components/chat/Chat.svelte:293-299` |

The server also keeps one row per message in the `chat_message` table (`role`, `parent_id`, `content`,
`output`, `model_id`, `files`, `sources`, `embeds`, `meta`, `done`, `status_history`, `error`, `usage`;
`backend/open_webui/models/chat_messages.py:127-158`).

### 6.2 What Each Action Writes

| Action | Server call | Effect | Source |
|---|---|---|---|
| Send | `POST /api/chat/completions` | The server creates the chat if new, adds the question and answer messages and streams the answer | `src/lib/components/chat/Chat.svelte:3577-3642` |
| Any save (edit, rating, branch switch in a multi-model answer, Overview click) | `POST /api/v1/chats/{id}` | Whole `history` and current-branch `messages` replaced | `src/lib/apis/chats/index.ts:1278`; `src/lib/components/chat/Chat.svelte:4002-4014`; `src/lib/components/chat/Messages.svelte:176-197` |
| Delete a message | `DELETE /api/v1/chats/{id}/messages/{message_id}` | 6.3 | `src/lib/apis/chats/index.ts:1347`; `src/lib/components/chat/Messages.svelte:418-459` |
| Rate | `POST /api/v1/evaluations/feedback` (or update) | A `feedback` row with `data` (rating, model ids, reason, comment, tags), `meta` (chat id, message id and index) and `snapshot` (the **entire chat** at that moment) | `src/lib/components/chat/Messages/ResponseMessage.svelte:482-604`; `backend/open_webui/models/feedbacks.py:20-30` |
| Allow, Deny, answer | `POST /api/v1/chats/{id}/messages/{message_id}/resolve` | Tool call status updated and the response resumed | `src/lib/apis/chats/index.ts:1372-1410`; `backend/open_webui/main.py:1893-1910` |
| Stop | `POST /api/tasks/chat/{chat_id}/stop` | Running tasks of the chat stopped | `src/lib/apis/index.ts:333`; `src/lib/components/chat/Chat.svelte:3765-3778` |
| Fork | `POST /api/v1/chats/{id}/fork` | New chat | `src/lib/apis/chats/index.ts:996` |
| Compact | `POST /api/v1/chats/{id}/compact` | Older messages summarized | `src/lib/apis/chats/index.ts:1314` |
| Run code (Jupyter engine) | `POST /api/v1/utils/code/execute` | Nothing stored | `src/lib/apis/utils/index.ts:33` |

Because a rating stores a full snapshot of the chat in `feedback`, the content of rated conversations is
also held in the evaluation data that admins can see; treat it as personal data
(`backend/open_webui/models/feedbacks.py:28`).

### 6.3 Deleting a Message

The browser and the server apply the same rule
(`src/lib/components/chat/Messages.svelte:418-459`; `backend/open_webui/models/chats.py:935-974`,
`:1196-1237`): the message **and its direct replies** are removed from `history.messages`; replies to those
replies are re-attached to the deleted message's parent; the chat then shows the newest remaining path;
the removed ids are also deleted from `chat_message`. Only the chat's owner or an admin may delete; anyone
else gets the `ACCESS_PROHIBITED` text (`backend/open_webui/routers/chats.py:1468-1503`). There is no undo.

### 6.4 Kept Only in the Browser

| Item | Where | Lifetime | Source |
|---|---|---|---|
| Composer draft (text under 5,000 characters, files except images, switches) | Session storage key `chat-input` or `chat-input-{chat id}` | The browser tab | `src/lib/components/chat/Chat.svelte:4032-4092` |
| Model selection carried between new chats | Session storage `selectedModels` | The browser tab | `src/lib/components/chat/Chat.svelte:938-949`, `:2097-2100` |
| Message queue | Memory (`chatRequestQueues`) | Until reload | `src/lib/stores/index.ts:123-125` |
| Dismissed banners | Local storage `dismissedBannerIds` | Permanent in that browser | `src/lib/components/chat/Navbar.svelte:58-64`, `:300-319` |
| Side panel width; Controls section open or closed | Local storage `chatControlsSize`, `chatControls.*` | Permanent in that browser | `src/lib/components/chat/ChatControls.svelte:309-318`; `src/lib/components/chat/Controls/Controls.svelte:18-30` |
| Temporary chats | Memory only | Until the tab closes | `src/lib/components/chat/Chat.svelte:3993-3996` |

### 6.5 User Settings Used Here

Interface choices are saved in the user's settings under `ui` (for the fork's two switches,
`backend/open_webui/models/users.py:99-100`). When the browser loads them, the server lays them over the
admin's default interface settings (`backend/open_webui/routers/users.py:457-472`). The per-user tool
approval choice is `ui.params.tool_approval_mode` (`src/lib/components/chat/Chat.svelte:444-455`).

## 7. Settings and Configuration

Code defaults below are what the repository says. Live values are data in the `config` table (or the
environment): **TO BE CONFIRMED** for production. After first boot the stored value wins over the
environment variable (ground truth).

### 7.1 Admin Settings That Change This Screen

| Setting key (`config` table) | Seeded from | Code default | Effect here | Source |
|---|---|---|---|---|
| `web.search.enable` | `ENABLE_WEB_SEARCH` | off | Web Search entry and chip | `backend/open_webui/config.py:1161`, `:2941` |
| `web.search.confirmation.enable` | `ENABLE_WEB_SEARCH_CONFIRMATION` | off | **Use Web Search?** dialog | `backend/open_webui/config.py:1163`, `:2942` |
| `web.search.confirmation.content` | `WEB_SEARCH_CONFIRMATION_CONTENT` | `Your query will be sent to the configured web search provider.` | Dialog text | `backend/open_webui/config.py:1165-1168`, `:2943` |
| `image_generation.enable` | `ENABLE_IMAGE_GENERATION` | off | Image entry | `backend/open_webui/config.py:1351`, `:3019` |
| `code_interpreter.enable` | `ENABLE_CODE_INTERPRETER` | on | Code Interpreter entry | `backend/open_webui/config.py:424`, `:2843` |
| `code_execution.enable` | `ENABLE_CODE_EXECUTION` | on | **Run** on Python code blocks | `backend/open_webui/config.py:409`, `:2836` |
| `code_execution.engine` | `CODE_EXECUTION_ENGINE` | `pyodide` (in the browser) | Where **Run** executes | `backend/open_webui/config.py:411`, `:2837` |
| `code_interpreter.engine` | `CODE_INTERPRETER_ENGINE` | `pyodide` | Whether the side panel offers the in-browser Files tab | `backend/open_webui/config.py:433`, `:2850` |
| `chat.tool_permissions.enable` | `ENABLE_TOOL_PERMISSIONS` | off | **Tool Permissions** in the + menu | `backend/open_webui/config.py:2196`, `:3138` |
| `chat.context_compaction.enable` | `ENABLE_CONTEXT_COMPACTION` | off | `/compact`, context gauge | `backend/open_webui/config.py:2194`, `:3133` |
| `task.autocomplete.enable` | `ENABLE_AUTOCOMPLETE_GENERATION` | off | Prompt autocompletion | `backend/open_webui/config.py:2333`, `:3149` |
| `ui.enable_message_rating` | `ENABLE_MESSAGE_RATING` | on | Good / Bad Response | `backend/open_webui/config.py:2098`, `:3124` |
| `ui.enable_community_sharing` | `ENABLE_COMMUNITY_SHARING` | on | The openwebui.com review link in the feedback form | `backend/open_webui/config.py:2096`, `:3123` |
| `ui.watermark` | `RESPONSE_WATERMARK` | empty | Text appended to every copied response | `backend/open_webui/config.py:1729`, `:3100` |
| `ui.default_models` | `DEFAULT_MODELS` | none | Model(s) preselected on a new chat when the user has no saved choice | `backend/open_webui/config.py:1674`, `:3087`; `src/lib/components/chat/Chat.svelte:2093-2133` |
| `ui.prompt_suggestions` | `DEFAULT_PROMPT_SUGGESTIONS` | none, which shows six built-in upstream examples ("Help me study", "Give me ideas", "Tell me a fun fact", "Show me a code snippet", "Explain options trading", "Overcome procrastination"); an empty list shows none | Landing-page suggestions when the model has none | `backend/open_webui/config.py:1678-1683`, `:3091`; `src/lib/utils/localizedContent.ts:131-176` |
| `ui.default_interface_settings` | `DEFAULT_INTERFACE_SETTINGS` (JSON) | `{}` | Default values for every Interface setting, including the fork's two (7.3) | `backend/open_webui/config.py:1711-1718`, `:3089` |
| `rag.file.max_count`, `rag.file.max_size` | `RAG_FILE_MAX_COUNT`, `RAG_FILE_MAX_SIZE` | none | File count and size limits in the composer | `backend/open_webui/config.py:981-983`, `:2906-2907` |
| `file.image_compression_width`, `file.image_compression_height` | same names | none | Maximum image size before upload | `backend/open_webui/config.py:989-995`, `:2908-2909` |
| `notes.enable` | `ENABLE_NOTES` | on | **Attach Notes** | `backend/open_webui/config.py:2050`, `:3118` |
| `google_drive.enable`, `onedrive.enable` | `ENABLE_GOOGLE_DRIVE_INTEGRATION`, `ENABLE_ONEDRIVE_INTEGRATION` | off | Cloud pickers | `backend/open_webui/config.py:843`, `:849`, `:2857`, `:2860` |
| `audio.stt.engine` | `AUDIO_STT_ENGINE` | empty (server) | `web` makes dictation use the browser and blocks Voice mode (`Call feature is not supported when using Web STT engine`) | `backend/open_webui/config.py:1586`, `:3057`; `src/lib/components/chat/MessageInput.svelte:2685-2691` |
| `audio.tts.split_on` | `AUDIO_TTS_SPLIT_ON` | `punctuation` | How Read Aloud splits text | `backend/open_webui/config.py:1642`, `:3076` |
| `user.permissions` | the `USER_PERMISSIONS_*` variables | section 3 | Which controls show | `backend/open_webui/config.py:3101` |

Environment-only (not stored): `IFRAME_CSP`, empty by default, a content security policy injected into the
Artifacts panel and HTML citation previews (`backend/open_webui/config.py:1731`;
`backend/open_webui/main.py:2437`).

### 7.2 Per-Model Settings

Set by admins (or model owners) on each model, outside this area, and read here: capabilities (`vision`,
`file_upload`, `web_search`, `image_generation`, `code_interpreter`, `terminal`, `citations`,
`status_updates`, each on unless switched off), default tools, skills, filters and features, prompt
suggestions, chat variable definitions, a background image, a text-to-speech voice and whether to stream
(`src/lib/components/chat/MessageInput.svelte:745-801`; `src/lib/components/chat/Chat.svelte:181-188`,
`:1008-1120`, `:3488-3492`; `src/lib/components/chat/Messages/ResponseMessage.svelte:266-270`).

### 7.3 Per-User Interface Settings Used by This Screen

All are in Settings > Interface (shown when the user is an admin or has `settings.interface`,
`src/lib/components/chat/SettingsModal.svelte:394`); the screen itself is described in
`user-settings-and-personalisation.md`. Defaults are the code defaults used when neither the user nor the
admin's default interface settings set a value. The admin defaults are merged under the user's own values
when settings load, and a switch whose value comes from the admin default (the user never changed it)
shows a small `Default` label beside it (`backend/open_webui/routers/users.py:457-472`;
`src/lib/components/common/InterfaceSettings.svelte:24`, `:153-159`, `:1346`, `:1369`;
`src/lib/components/common/Switch.svelte:30-32`).

| Label (en-US) | Key | Default | Effect | Label source (`translation.json`) |
|---|---|---|---|---|
| **Hide Processing Details** (fork) | `hideProcessingDetails` | off | 5.22 | `:2924` |
| **Inline Citations** (fork) | `showInlineCitations` | on | 5.23 | `:2936` |
| **Enter Key Behavior** | `ctrlEnterToSend` | Enter to Send | 5.5 | `:2914` |
| **Enable Message Queue** | `enableMessageQueue` | on | 5.9 | `:2912` |
| **Chat Bubble UI** | `chatBubble` | on | Question bubbles on the right, no avatar or name | `:2887` |
| **Display the Username Instead of You in the Chat** | `showUsername` | off | Name shown over questions (bubble UI off) | `:2910` |
| **Widescreen Mode** | `widescreenMode` | off | Full-width messages and composer | `:2994` |
| **Landing Page Mode** | `landingPageMode` | not set | `chat` puts the composer at the bottom of a new chat | `:2946` |
| **Temporary Chat by Default** | `temporaryChatByDefault` | off | New chats start temporary | `:2980` |
| **Display Chat Title in Tab** | `showChatTitleInTab` | on | Browser tab title | `:2904` |
| **Fade Effect for Streaming Text** | `chatFadeStreamingText` | on | Words fade in | `:2916` |
| **Render Markdown in User Messages** | `renderMarkdownInUserMessages` | on | Questions shown as Markdown or plain text | `:2960` |
| **Render Markdown in Assistant Messages** | `renderMarkdownInAssistantMessages` | on | Answers shown as Markdown or plain text | `:2956` |
| **Render Markdown in Previews** | `renderMarkdownInPreviews` | on | Citation window text | `:2958` |
| **Title Auto-Generation** | `title.auto` | on | Asks for a title on new chats | `:2987` |
| **Follow-Up Auto-Generation** | `autoFollowUps` | on | Follow-up suggestions | `:2919` |
| **Chat Tags Auto-Generation** | `autoTags` | on | Tags on new chats | `:2893` |
| **Response Auto-Scroll** | `scrollOnResponseGeneration` | on | Follow streaming text | `:2962` |
| **Scroll On Branch Change** | `scrollOnBranchChange` | on | Scroll when switching versions | `:2966` |
| **Insert Suggestion Prompt to Input** | `insertSuggestionPrompt` | off | Suggestion cards fill the composer instead of sending | `:2942` |
| **Keep Follow-Up Prompts in Chat** | `keepFollowUpPrompts` | off | Follow-ups under older answers too | `:2944` |
| **Insert Follow-Up Prompt to Input** | `insertFollowUpPrompt` | off | Follow-ups fill the composer instead of sending | `:2938` |
| **Regenerate Menu** | `regenerateMenu` | on | Regenerate opens a menu | `:2954` |
| **Always Collapse Code Blocks** | `collapseCodeBlocks` | off | Code blocks start collapsed | `:2878` |
| **Always Expand Details** | `expandDetails` | off | Reasoning and tool blocks start open | `:2880` |
| **Display Multi-model Responses in Tabs** | `displayMultiModelResponsesInTabs` | off | Tabs instead of side-by-side cards | `:2908` |
| **Floating Quick Actions** | `showFloatingActionButtons` | on | Ask / Explain on selected text | `:2917` |
| **Rich Text Input for Chat** | `richTextInput` | on | Formatting in the composer | `:2964` |
| **Show Formatting Toolbar** | `showFormattingToolbar` | off | Formatting pop-up toolbar | `:2976` |
| **Insert Prompt as Rich Text** | `insertPromptAsRichText` | off | Inserted prompts keep their formatting | `:2940` |
| **Prompt Autocompletion** | `promptAutocomplete` | off | Grey suggested text (with the admin switch) | `:2952` |
| **Paste Large Text as File** | `largeTextAsFile` | off | Long pastes become a file | `:2950` |
| **Detect Artifacts Automatically** | `detectArtifacts` | on | Artifacts panel opens by itself | `:2902` |
| **iframe Sandbox Allow Scripts** / **Forms** / **Downloads** / **Same Origin** | `iframeSandboxAllow*` | on / on / on / off (see 5.15 for exceptions) | Embedded pages | `:2926-2932` |
| **Copy Formatted Text** | `copyFormatted` | off | Copy keeps formatting | `:2897` |
| **Auto-Copy Response to Clipboard** | `responseAutoCopy` | off | Each finished answer is copied | `:2883` |
| **Web Search in Chat** | `webSearch` | off | `always` keeps web search on | `:2992` |
| **Allow User Location** | `userLocation` | off | Includes the browser's location in each request's prompt variables | `:2874` |
| **Image Compression** | `imageCompression` | off | Shrinks images before upload | `:2933` |
| **Default Upload Mode** | `defaultUploadContext` | not set | `full` stamps new uploads with the full-context mode (meaning in `files-uploads-and-storage.md`) | `:2900` |
| **Accessibility Mode** | `highContrastMode` | off | Buttons always visible, focus outlines | `:2872` |
| **Haptic Feedback** | `hapticFeedback` | off | Vibration while text streams (phones) | `:2922` |
| **Chat Direction** | `chatDirection` | auto | Left-to-right or right-to-left layout | `:2889` |
| **Terminal File Display** / **Show Files on Terminal Select** | `terminalFileDisplay` / `showFilesOnTerminalSelect` | side panel / on | Terminal files inline or in the panel | `:2982`, `:2974` |

Usage of each key in this area: `hideProcessingDetails` and `showInlineCitations` (5.22, 5.23);
`ctrlEnterToSend` `src/lib/components/chat/MessageInput.svelte:2072`, `:2155-2158`;
`enableMessageQueue` `src/lib/components/chat/Chat.svelte:3197`; `chatBubble`
`src/lib/components/chat/Messages/UserMessage.svelte:139`, `:384-391`; `insertSuggestionPrompt`
`src/lib/components/chat/Chat.svelte:926`; `insertFollowUpPrompt` and `keepFollowUpPrompts`
`src/lib/components/chat/Messages/ResponseMessage.svelte:1658-1670`; `regenerateMenu` `:1395`;
`expandDetails` `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte:467`; `collapseCodeBlocks`
`:209`; `displayMultiModelResponsesInTabs` `src/lib/components/chat/Messages/MultiResponseMessages.svelte:234`;
`showFloatingActionButtons` `src/lib/components/chat/Messages/ResponseMessage.svelte:867-869`;
`detectArtifacts` `src/lib/components/chat/Messages/ContentRenderer.svelte:157`; `largeTextAsFile`
`src/lib/components/chat/MessageInput.svelte:2080`, `:2189`; `richTextInput`, `showFormattingToolbar`,
`insertPromptAsRichText`, `promptAutocomplete` `:2050-2082`; `responseAutoCopy`
`src/lib/components/chat/Chat.svelte:2860-2862`; `userLocation` `:3480-3486`; `webSearch` `:353`;
`imageCompression` `src/lib/components/chat/MessageInput.svelte:1132-1166`; `defaultUploadContext` `:945`;
`copyFormatted` `src/lib/components/chat/Messages/ResponseMessage.svelte:245`.

### 7.4 Per-Chat Settings

The side panel's **System Prompt**, **Advanced Params** and attached **Files**, and the tool approval mode,
are stored in the chat's `params` and `files` (section 6.1) and saved automatically. A user-level system
prompt (from Settings) applies when the chat has none (`src/lib/components/chat/Chat.svelte:3493-3499`).

## 8. Cron Jobs and Background Processes

There is no scheduled job in this area. Everything below happens in the user's browser while the chat is
open, or is requested from the server as part of sending a message.

| What | When | Source |
|---|---|---|
| Draft autosave to session storage | 0.5 seconds after typing stops | `src/lib/components/chat/Chat.svelte:4055-4071` |
| Chat controls autosave (system prompt, parameters, files) | 0.4 seconds after a change; also when leaving the chat | `src/lib/components/chat/Chat.svelte:809-813`, `:1632-1638` |
| Usage heartbeat over the websocket (`usage` event with model and chat id) | Every second while a request is in flight | `src/lib/components/chat/Chat.svelte:2623-2631`, `:3366-3389` |
| Queue processing | When a response finishes, stops or fails; when a queued file finishes uploading; when returning to an idle chat | `src/lib/components/chat/Chat.svelte:2487-2524`, `:857-862`, `:1868-1884` |
| Reconnect check | When the websocket reconnects and the last response is unfinished, the chat reloads if the server has no task running for it | `src/lib/components/chat/Chat.svelte:1535-1552` |
| "Chat inactive" reload | When the server reports the chat is no longer active and a response is still open | `src/lib/components/chat/Chat.svelte:1229-1242` |
| Mark as read | On opening, leaving or switching chats (`last_read_at`) | `src/lib/components/chat/Chat.svelte:815-855`, `:1146-1151` |
| Title, tag and follow-up generation | Requested with each send (`background_tasks`) and run by the server after the reply; results arrive as `chat:title`, `chat:tags` and `chat:message:follow_ups` events | `src/lib/components/chat/Chat.svelte:3628-3640`, `:1293-1298`, `:1319-1327`; server side in `chat-completion-pipeline-and-generation-tasks.md` |
| Feedback tag generation | After a thumbs rating, the browser asks a model for tags | `src/lib/components/chat/Messages/ResponseMessage.svelte:574-601` |
| In-browser Python (Run, 60 second limit) | On click | `src/lib/components/chat/Messages/CodeBlock.svelte:222-357` |

## 9. Notifications and Emails

The application sends **no email** (ground truth). In this area users are informed by:

- **Pop-up notifications (toasts)** raised by the screen itself (section 10), and by the server or plugins
  through `notification` events, shown as success, error, warning or information toasts with the text the
  server sent (`src/lib/components/chat/Chat.svelte:1354-1366`).
- **Dialogs requested by the server or a plugin**: a confirmation (`confirmation` event), a one-field input
  (`input` event), and the ask-user card (`request:user_input` event)
  (`src/lib/components/chat/Chat.svelte:1367-1408`, `:4249-4270`). A plugin can also run a script in the page
  (`execute` event, `:1376-1389`); Security-sensitive: refer to the platform maintainer and U of T
  Information Security (security.utoronto.ca) for anything about what plugins may run.
- **Banners** under the top bar on a new chat: admin banners and licence notices
  (`src/lib/components/chat/Navbar.svelte:270-324`).
- **Websocket events** that update the open chat (status, text deltas, files, embeds, sources, errors, title,
  tags, follow-ups, tasks, favourites, compaction progress) are listed in
  `src/lib/components/chat/Chat.svelte:1203-1421`. Events for a chat that is not on screen are ignored by
  this component; the sidebar handles unread markers.
- **Context compaction** progress toasts: `Compacting context`, then `Context compacted` or
  `Context compaction failed` (`src/lib/components/chat/Chat.svelte:1173-1201`).
- Browser (desktop) notifications for finished replies are outside this area.

## 10. Error, Warning and Notice Messages (Verbatim)

Severity: **Error** (red pop-up), **Warning** (yellow pop-up), **Success** (green pop-up), **Info** (neutral
pop-up), **Loading** (pop-up with a spinner that later turns into another message), **Inline** (text on the
page), **Dialog** (a window with buttons). Values in `{braces}` are filled in at run time. Every plain i18n
key in this area displays as written in English (the `en-US` file leaves them empty, so the key is shown).
Status-line texts are catalogued in `in-chat-status-and-response-messages.md` and are not repeated here.

### 10.1 Sending, Commands and the Chat as a Whole

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Please enter a prompt` | Error | `src/lib/components/chat/Chat.svelte:3134-3137` | Send with no text and no file (normally the button is disabled) | Type something | None |
| `Model not selected` | Error | `src/lib/components/chat/Chat.svelte:3138-3141`, `:2635-2636`, `:3018-3020` | Sending with no model selected, or the chat's model was removed or hidden | Pick a model in the selector | Was the model removed, hidden or access withdrawn? (`models` area) |
| `Model not selected` | Error | `src/lib/components/chat/Messages.svelte:318-322` | Editing a message (Send or Save) while no model is selected | Pick a model first | As above |
| `Model not found` | Error | `src/lib/components/chat/Chat.svelte:2641-2644` | Cmd+Shift+Enter with a model that no longer exists | Pick another model | As above |
| `Model {modelName} is not vision capable` | Error | `src/lib/components/chat/Chat.svelte:3346-3356` | An image is in the conversation and a selected model lacks vision (the message is still sent) | Use a vision model or remove the image | Model capabilities |
| `Please connect all required integrations before sending a message` | Warning | `src/lib/components/chat/Chat.svelte:3130-3133` | The model's default tools include one the user has not signed in to | Click the amber chip to connect | Tool's sign-in configuration |
| `Chat Variables have conflicting model definitions` | Error | `src/lib/components/chat/Chat.svelte:3142-3147` | Two selected models define the same chat variable differently | Select one model | Model definitions |
| `Selected models define incompatible Chat Variables.` | Dialog | `src/lib/components/chat/Chat.svelte:4179-4210` | Same as above; window titled `Chat Variables` lists the keys and models | Close and change models | As above |
| `Failed to save chat variables` | Error | `src/lib/components/chat/Chat.svelte:714-724` | Saving Chat Variables to the server failed | Try again | Server log at that time |
| `You can only chat with a maximum of {maxCount} file(s) at a time.` | Error | `src/lib/components/chat/Chat.svelte:3153-3163` | On send: files on the message plus files already attached to the chat exceed the admin limit | Remove files or start a new chat | `rag.file.max_count` |
| `You can only chat with a maximum of {maxCount} file(s) at a time.` | Error | `src/lib/components/chat/MessageInput.svelte:1090-1100` | On attaching: the composer would hold more files than the limit | Attach fewer files | As above |
| `Use Web Search?` | Dialog (title) | `src/lib/components/chat/Chat.svelte:4220-4222` | Web search switched on or used while the admin requires confirmation | **Continue** or **Cancel** | `web.search.confirmation.enable` |
| `Your query will be sent to the configured web search provider.` | Dialog (text) | `backend/open_webui/config.py:1165-1168` | Same dialog: this is the seeded default of the admin text | As above | `web.search.confirmation.content` |
| `Your query will be sent to the configured web search provider.` | Dialog (text) | `src/lib/components/chat/Chat.svelte:4223-4225` | Same dialog when the stored admin text is empty | As above | As above |
| `Uh-oh! There was an issue with the response.` | Error (pop-up) and Inline (first line of the error box) | `src/lib/components/chat/Chat.svelte:3653-3655`, `:3744-3746` | The request or the provider failed; the box adds the provider's own text on the next line | Regenerate; if it persists, report it | Provider status, server log for the time and model (section 11.6) |
| `Error submitting message` | Inline | `src/lib/components/chat/Messages/Error.svelte:37` | A response error with no readable text | Regenerate | Server log |
| `Failed to connect to MCP server '{server_id}'` | Inline (error box) | `backend/open_webui/utils/middleware.py:3010-3011` | A tool server could not be reached during the reply (one example of server-side texts; full list in the pipeline document) | Retry later or switch the tool off | Tool server status |
| `{error}` (the server's or browser's own text) | Error | `src/lib/components/chat/Chat.svelte:496`, `:575`, `:593`, `:1861`, `:2590`, `:3085`, `:3657`, `:3727-3741`, `:3768`, `:3774`, `:4098`, `:4161` | Any failed request in this area that is passed through as-is | Read the text; retry | Match the text in the server log |
| Server notifications (any text) | Success, Error, Warning or Info | `src/lib/components/chat/Chat.svelte:1354-1366` | A plugin or the server sent a `notification` event | Depends | The plugin that sent it |
| `Parent message not found` | Error | `src/lib/components/chat/Chat.svelte:3846-3851` | Regenerate on a response whose question is missing from the tree | Reload the chat | Possibly a damaged chat history (section 14) |
| `Failed to create chat` | Error | `src/lib/components/chat/Chat.svelte:3306-3312` | The notes side chat could not create its chat | Retry | Server log |
| `Access prohibited` | Error | `src/lib/components/chat/Chat.svelte:3051-3054` | `/fork` or **Fork chat** without `chat.import` | None | Permissions |
| `No chat to fork` | Info | `src/lib/components/chat/Chat.svelte:3047-3049` | `/fork` on an empty chat | None | None |
| `Wait for the current response to finish before forking.` | Warning | `src/lib/components/chat/Chat.svelte:3056-3064` | Fork while a response runs | Wait or stop | None |
| `Forking chat...` | Loading | `src/lib/components/chat/Chat.svelte:3066` | Fork started | Wait | None |
| `Chat forked` | Success | `src/lib/components/chat/Chat.svelte:3080` | Fork done; the new chat opens | None | None |
| `Failed to fork chat` | Error | `src/lib/components/chat/Chat.svelte:3082` | The server returned no new chat | Retry | Server log |
| `Context compaction is disabled` | Info | `src/lib/components/chat/Chat.svelte:2957-2960`, `:2992-2993` | `/compact` with the admin switch off | None | `chat.context_compaction.enable` |
| `No chat to compact` | Info | `src/lib/components/chat/Chat.svelte:2962-2965`, `:2990-2991` | `/compact` on an empty chat | None | None |
| `Wait for the current response to finish before compacting.` | Warning | `src/lib/components/chat/Chat.svelte:2967-2975` | `/compact` while a response runs | Wait | None |
| `Compacting context...` | Loading | `src/lib/components/chat/Chat.svelte:2978` | Manual compaction started | Wait | None |
| `Chat is too short to compact` | Info | `src/lib/components/chat/Chat.svelte:2987-2989` | Nothing old enough to shorten | None | None |
| `Nothing to compact` | Info | `src/lib/components/chat/Chat.svelte:2994` | Server skipped for another reason | None | None |
| `Compacting context` | Loading | `src/lib/components/chat/Chat.svelte:1196-1200` | The server started compacting automatically | Wait | None |
| `Context compacted` | Success | `src/lib/components/chat/Chat.svelte:1186`, `:2985` | Compaction finished | None | None |
| `Context compaction failed` | Error | `src/lib/components/chat/Chat.svelte:1181`, `:3000` | Compaction failed (manual: the server's text if any) | Continue; start a new chat if the model runs out of context | Server log |
| `Current model: {currentModels}` | Info | `src/lib/components/chat/Chat.svelte:3013-3021` | `/model` sent with no model id | None | None |
| `Model not found: {modelId}` | Error | `src/lib/components/chat/Chat.svelte:3028-3031` | `/model {id}` with an unknown id | Check the id | None |
| `Model switched to: {id}` | Success | `src/lib/components/chat/Chat.svelte:3037-3040` | `/model {id}` worked | None | None |
| `Read only` | Inline | `src/lib/components/chat/Chat.svelte:4433-4438` | Viewing a chat owned by someone else | None | Expected |
| `Confirm Prompt from Embed` | Dialog | `src/lib/components/chat/Chat.svelte:1448-1500` | An embedded page (for example a tool's interactive frame) asked to send the shown text as a message | Confirm only if the text is expected | Which tool or page asked |
| `An unknown error occurred.` | Error | `src/routes/(app)/+page.svelte:8-12` | The address `/` was opened with an empty `error` parameter (a non-empty one is shown as-is) | None | What redirected the user (often sign-in, see the authentication documents) |
| `Chat moved successfully` | Success | `src/lib/components/chat/Chat.svelte:4103-4108` | Move from the chat menu worked | None | Chat management document |
| `Failed to move chat` | Error | `src/lib/components/chat/Chat.svelte:4109-4111` | Move attempted without a chat or folder id | Retry | As above |
| `Chat archived.` | Success | `src/lib/components/chat/Chat.svelte:4114-4121` | Archive from the chat menu worked | None | As above |
| `Failed to archive chat.` | Error | `src/lib/components/chat/Chat.svelte:4122-4125` | Archive failed | Retry | Server log |
| `Delete chat?` | Dialog (title) | `src/lib/components/chat/Chat.svelte:4237-4243` | Delete from the chat menu or shortcut | Confirm or cancel | As above |
| `This will delete {title}.` | Dialog (text) | `src/lib/components/chat/Chat.svelte:4244-4246` | Same dialog; the chat title is shown in the middle | As above | As above |
| `Chat deleted.` | Success | `src/lib/components/chat/Chat.svelte:4146-4158` | Chat deleted | None | As above |
| `No conversation to save` | Error | `src/lib/components/chat/Chat.svelte:4346-4351` | **Save Chat** on an empty temporary chat | None | None |
| `Conversation saved successfully` | Success | `src/lib/components/chat/Chat.svelte:4371-4377` | **Save Chat** turned a temporary chat into a saved one | None | None |
| `Failed to save conversation` | Error | `src/lib/components/chat/Chat.svelte:4379-4381` | **Save Chat** failed | Retry; copy the text out first | Server log |
| `File uploaded successfully` | Success | `src/lib/components/chat/Chat.svelte:1776` | A Google Drive upload path that nothing in the current composer calls (section 14) | None | None |
| `Error uploading file: {error}` | Error | `src/lib/components/chat/Chat.svelte:1777-1787` | Same unused path | None | None |
| `You do not have permission to upload web content.` | Error | `src/lib/components/chat/Chat.svelte:1790-1794` | Attaching a web page (via `#`, `@` or an address parameter) without `chat.web_upload` | None | Permissions |
| `You do not have permission to upload web content.` | Inline (tooltip) | `src/lib/components/chat/MessageInput/InputMenu.svelte:246-249` | Hovering the greyed **Attach Webpage** | None | As above |
| `Trial License` | Inline (banner title) | `src/lib/components/chat/Navbar.svelte:276-280` | Licence metadata says trial | Report to the platform maintainer | Licence (TO BE CONFIRMED) |
| `You are currently using a trial license. Please contact support to upgrade your license.` | Inline (banner text) | `src/lib/components/chat/Navbar.svelte:281-283` | Same banner | As above | As above |
| `License Error` | Inline (banner title) | `src/lib/components/chat/Navbar.svelte:288-292` | More users than licensed seats | Report to the platform maintainer | Licence (TO BE CONFIRMED) |
| `Exceeded the number of seats in your license. Please contact support to increase the number of seats.` | Inline (banner text) | `src/lib/components/chat/Navbar.svelte:293-295` | Same banner | As above | As above |
| `This chat won't appear in history and your messages will not be saved.` | Inline (tooltip) | `src/lib/components/chat/Placeholder.svelte:117-125` | Hovering the Temporary Chat label on the landing screen | None | Expected |
| `This chat won't appear in history and your messages will not be saved.` | Inline (tooltip) | `src/lib/components/chat/ChatPlaceholder.svelte:96-105` | Same, in Landing Page Mode `chat` | None | Expected |

### 10.2 Composer, Attachments and Voice

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `You do not have permission to upload files.` | Error | `src/lib/components/chat/MessageInput.svelte:918-922` | Dropping, pasting or picking a file without `chat.file_upload` | None | Permissions |
| `You do not have permission to upload files.` | Inline (tooltip) | `src/lib/components/chat/MessageInput/InputMenu.svelte:188-192`, `:214-218`, `:270-274`, `:303-307`, `:334-338`, `:364-368` | Hovering a greyed item in the + menu | None | As above |
| `Model(s) do not support file upload` | Error | `src/lib/components/chat/MessageInput.svelte:924-929` | Uploading while a selected model lacks the `file_upload` capability | Choose another model | Model capabilities |
| `Model(s) do not support file upload` | Inline (tooltip) | `src/lib/components/chat/MessageInput/InputMenu.svelte:188-189`, `:214-215`, `:270-271`, `:303-304`, `:334-335`, `:364-365` | Hovering a greyed item in the + menu | Choose another model | As above |
| `You cannot upload an empty file.` | Error | `src/lib/components/chat/MessageInput.svelte:949-952` | A 0-byte file | Check the file | None |
| `File size should not exceed {maxSize} MB.` | Error | `src/lib/components/chat/MessageInput.svelte:1110-1124` | File above the admin size limit | Use a smaller file | `rag.file.max_size` |
| `Selected model(s) do not support image inputs` | Error | `src/lib/components/chat/MessageInput.svelte:1126-1130` | Image with no vision-capable model selected | Choose a vision model | Model capabilities |
| `Failed to upload file.` | Error (terminal uploads) or silent removal | `src/lib/components/chat/MessageInput.svelte:985-989`, `:1039-1043` | The upload returned nothing | Retry | Server log; `files-uploads-and-storage.md` |
| `{uploadedFile.error}` (server warning about the file) | Warning | `src/lib/components/chat/MessageInput.svelte:1025-1028` | The file uploaded but processing reported a problem | Check the answer uses the file | Server log; files document |
| `Failed to extract content from the file: {error}` | Error | `src/lib/components/chat/MessageInput.svelte:1055-1060` | Temporary chat: the browser could not read the file | Use a saved chat or another format | None |
| `Failed to extract content from the file.` | Error | `src/lib/components/chat/MessageInput.svelte:1062-1068` | Same, follow-up message | As above | None |
| `File not found.` | Error | `src/lib/components/chat/MessageInput.svelte:1723-1729` | The file picker returned no file | Pick again | None |
| `Error accessing Google Drive: {error}` | Error | `src/lib/components/chat/MessageInput.svelte:2253-2259` | The Google Drive picker failed | Retry | Google Drive integration settings |
| `Please enter a valid URL.` | Error | `src/lib/components/chat/MessageInput/AttachWebpageModal.svelte:20-31` | **Attach Webpage** with no valid http(s) address | Fix the address | None |
| `Oops! Looks like the URL is invalid. Please double-check and try again.` | Error | `src/lib/components/chat/MessageInput/Commands/AtCommands.svelte:204-208` | An address typed after `@` is not valid | Fix the address | None |
| `Oops! Looks like the URL is invalid. Please double-check and try again.` | Error | `src/lib/components/chat/MessageInput/Commands/Knowledge.svelte:217-218`, `:245-246` | An address typed after `#` is not valid | Fix the address | None |
| `Failed to read clipboard contents` | Error | `src/lib/components/chat/MessageInput.svelte:284-288` | A prompt with `{{CLIPBOARD}}` and clipboard access refused | Allow clipboard access in the browser | Browser permission |
| `Location access not allowed` | Error | `src/lib/components/chat/MessageInput.svelte:311-320` | A prompt with `{{USER_LOCATION}}` and location refused; `LOCATION_UNKNOWN` is inserted | Allow location in the browser | Browser permission |
| `Cannot create an empty note.` | Error | `src/lib/components/chat/MessageInput.svelte:1199-1203` | Defined for a "create note from composer" function that nothing calls in this version | None | None |
| `Permission denied when accessing microphone: {error}` | Error | `src/lib/components/chat/MessageInput.svelte:2639-2651` | **Dictate** and the browser refused the microphone | Allow the microphone for the site | Browser and operating-system microphone permission |
| `Permission denied when accessing microphone` | Error | `src/lib/components/chat/MessageInput.svelte:2659-2661` | Microphone check failed unexpectedly | As above | As above |
| `Select only one model to call` | Error | `src/lib/components/chat/MessageInput.svelte:2679-2683` | **Voice mode** with several models | Keep one model | None |
| `Call feature is not supported when using Web STT engine` | Error | `src/lib/components/chat/MessageInput.svelte:2685-2691` | **Voice mode** while the admin speech-to-text engine is the browser (`web`) | None | `audio.stt.engine` |
| `Permission denied when accessing media devices` | Error | `src/lib/components/chat/MessageInput.svelte:2721-2726` | **Voice mode** and the browser refused the microphone | Allow the microphone | Browser permission |
| `Error accessing media devices.` | Error | `src/lib/components/chat/MessageInput/VoiceRecording.svelte:233-239` | The dictation bar could not open the microphone | Allow the microphone | Browser permission |
| `Error starting recording.` | Error | `src/lib/components/chat/MessageInput/VoiceRecording.svelte:290-297` | The browser could not start recording | Try another browser | None |
| `Speech recognition error: {error}` | Error | `src/lib/components/chat/MessageInput/VoiceRecording.svelte:354-360` | Browser speech recognition failed | Retry | Browser support |
| `OAuth session disconnected` | Success | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:606-608` | `Disconnect OAuth` on a tool | None | None |
| `Failed to disconnect` | Error | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:614-616` | Disconnect failed (or the server's text) | Retry | Server log |
| `Empty message` | Inline | `src/lib/components/chat/MessageInput/QueuedMessageItem.svelte:66-72` | A queued message with files only | None | None |
| `Upload failed` | Inline | `src/lib/components/chat/MessageInput/QueuedMessageItem.svelte:74-78` | A queued message's file failed; the queue waits (5.9) | Edit or delete that queued item | Files document |
| `Waiting for upload` | Inline (tooltip) | `src/lib/components/chat/MessageInput/QueuedMessageItem.svelte:84-104` | **Send now** while that item's files upload or failed | Wait, or edit or delete | None |
| `Waiting for upload...` | Inline (tooltip) | `src/lib/components/chat/MessageInput.svelte:2736-2739` | Shown only when a parent sets `uploadPending`; the chat screen never does (section 14) | None | None |
| `Valves updated` | Success | `src/lib/components/chat/Controls/Valves.svelte:97-113` | A valve value saved | None | None |
| `No tools found` | Inline | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:545-546` | Tool search matched nothing | Clear the search | Tool access |
| `No skills found` | Inline | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:677-678` | Skill search matched nothing | Clear the search | Skill access |
| `No chats found` | Inline | `src/lib/components/chat/MessageInput/InputMenu/Chats.svelte:118-119` | **Reference Chats** list is empty | None | None |
| `No chats found` | Inline | `src/lib/components/chat/Placeholder/ChatList.svelte:170-173` | A folder's chat list is empty | None | None |
| `No files found` | Inline | `src/lib/components/chat/MessageInput/InputMenu/Files.svelte:109-110` | **Attach Files** list is empty | None | Files document |
| `No notes found` | Inline | `src/lib/components/chat/MessageInput/InputMenu/Notes.svelte:119-120` | **Attach Notes** list is empty | None | None |
| `No knowledge bases found.` | Inline | `src/lib/components/chat/MessageInput/InputMenu/Knowledge.svelte:196-199` | **Attach Knowledge** finds no knowledge base the user can read | None | Knowledge access |
| `No files in this knowledge base.` | Inline | `src/lib/components/chat/MessageInput/InputMenu/Knowledge.svelte:271-274` | An expanded knowledge base is empty | None | Knowledge document |

### 10.3 Messages, Rendering and Tools

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Copying to clipboard was successful!` | Success | `src/lib/components/chat/Messages/UserMessage.svelte:71-76` | **Copy** under a question | None | None |
| `Copying to clipboard was successful!` | Success | `src/lib/components/chat/Messages/ResponseMessage.svelte:238-249` | **Copy** under an answer | None | None |
| `Please enter a message or attach a file.` | Error | `src/lib/components/chat/Messages/UserMessage.svelte:97-101` | Saving or sending an edited question that is empty | Type text or keep a file | None |
| `Delete message?` | Dialog | `src/lib/components/chat/Messages/UserMessage.svelte:125-131` | **Delete** under a question (Shift+click skips it) | Confirm; there is no undo | None |
| `Delete message?` | Dialog | `src/lib/components/chat/Messages/ResponseMessage.svelte:684-690` | **Delete** under an answer | Confirm; there is no undo | None |
| `No content to speak` | Info | `src/lib/components/chat/Messages/ResponseMessage.svelte:273-277`, `:324-329` | **Read Aloud** on an answer with no plain text (for example only a tool card) | None | None |
| `{error}` (speech or feedback failure) | Error | `src/lib/components/chat/Messages/ResponseMessage.svelte:352`, `:371`, `:499`, `:561`, `:597` | Read Aloud or rating request failed | Retry | Audio document; server log |
| `Thanks for your feedback!` | Success | `src/lib/components/chat/Messages/RateComment.svelte:85-103` | **Save** in the feedback form | None | None |
| `This response was generated by "{model}"` | Success and Inline | `src/lib/components/chat/Messages/RateComment.svelte:74-83`, `:106-112` | Rating an answer from an arena model | None | None |
| `Copied to clipboard` | Success | `src/lib/components/chat/Messages/Markdown/KatexRenderer.svelte:53-62` | Clicking a formula | None | None |
| `Copied to clipboard` | Success | `src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens/CodespanToken.svelte:17-25` | Clicking inline code | None | None |
| `Execution Time Limit Exceeded` | Inline (in the code output) | `src/lib/components/chat/Messages/CodeBlock.svelte:260-269` | In-browser **Run** took over 60 seconds | Simplify the code | `code-execution-and-interpreter.md` |
| `{error}` (code execution) | Error | `src/lib/components/chat/Messages/CodeBlock.svelte:148-152` | Server-side (Jupyter) **Run** failed | Retry | Code execution settings |
| `Failed to render diagram: {errorMsg}` | Inline (red box) | `src/lib/components/chat/Messages/CodeBlock.svelte:368-377`, `:450-456` | A Mermaid block the library cannot draw | Ask the model to fix the diagram | None |
| `Failed to render visualization: {errorMsg}` | Inline (red box) | `src/lib/components/chat/Messages/CodeBlock.svelte:378-390` | A Vega or Vega-Lite block that cannot be drawn | As above | None |
| `No HTML, CSS, or JavaScript content found.` | Inline | `src/lib/components/chat/Artifacts.svelte:272-276` | Artifacts panel opened with nothing to show | Close the panel | None |
| `Thinking...` | Inline (fork) | `src/lib/components/chat/Messages/ResponseMessage.svelte:216-221`, `:920-921` | **Hide Processing Details** on and no answer text yet | Wait | 5.22 |
| `Allow {NAME}?` | Inline (tool card) | `src/lib/components/common/ToolCallDisplay.svelte:248-249` | A tool call waits for approval | **Allow** or **Deny** | Tool Permissions mode |
| `Input needed` | Inline (tool card) | `src/lib/components/common/ToolCallDisplay.svelte:246-247` | An `ask_user` call waits (the card is above the composer) | Answer the card | None |
| `Denied {NAME}` | Inline (tool card) | `src/lib/components/common/ToolCallDisplay.svelte:242-243` | The user denied the call | None | None |
| `Error: tool call rejected by user.` | Inline (tool output) | `backend/open_webui/utils/tool_approval.py:65-73` | Shown as the denied call's output | None | Expected after **Deny** |
| `Tool call has already been resolved.` | Error | `backend/open_webui/utils/tool_approval.py:53-58`; shown by `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte:135-137`, `src/lib/components/chat/Messages/StructuredOutputRenderer.svelte:59-61`, `src/lib/components/chat/Chat.svelte:495-497`, `:574-577`, `:592-595` | **Allow**, **Deny** or an answer for a call that was already handled (double click, second tab) | Reload the chat | None |
| `Tool call not found.` | Error | `backend/open_webui/utils/tool_approval.py:41-51`; shown as above | The call is no longer in the stored message | Reload | Possibly edited or deleted message |
| `Message has no resolvable output.` | Error | `backend/open_webui/utils/tool_approval.py:38-40`; shown as above | The stored message has no tool data | Reload | As above |
| `ask_user requires an answer or deny.` | Error | `backend/open_webui/utils/tool_approval.py:60-62`; shown as above | Approving an ask-user call instead of answering | Answer the card | None |
| `Tool call does not accept answers.` | Error | `backend/open_webui/utils/tool_approval.py:76-78`; shown as above | An answer was sent for an ordinary tool | Reload | None |
| `Answers are required for ask_user.` | Error | `backend/open_webui/utils/tool_approval.py:79-80`; shown as above | Empty ask-user submission | Answer every question | None |
| `We could not find what you're looking for :/` | Error | `backend/open_webui/constants.py:78`; `backend/open_webui/utils/tool_approval.py:33-34` | The message to resolve does not exist | Reload | None |
| `Download failed` | Error | `src/lib/components/chat/Messages/TerminalOutputFile.svelte:216-222` | **Download** on a terminal file preview failed | Retry | Terminal connection |
| `Terminal unavailable` | Inline | `src/lib/components/chat/Messages/TerminalOutputFile.svelte:278-281` | The terminal that produced the file is not selected or not reachable | Select that terminal | Terminal configuration |
| `Preview failed` | Inline | `src/lib/components/chat/Messages/TerminalOutputFile.svelte:137-205` | The terminal file could not be fetched | Retry | As above |
| `No preview available` | Inline | `src/lib/components/chat/Messages/TerminalOutputFile.svelte:309-315` | The file type cannot be previewed | Use **Download** | None |
| `Must be a JSON array` | Inline | `src/lib/components/chat/Messages/OutputEditView.svelte:47-57` | JSON view of a structured edit holds something other than a list | Fix the JSON | None |
| `Invalid JSON` | Inline | `src/lib/components/chat/Messages/OutputEditView.svelte:58-60` | JSON view text cannot be parsed | Fix the JSON | None |
| `No output items` | Inline | `src/lib/components/chat/Messages/OutputEditView.svelte:363-367` | Every block was removed in the visual editor | **Cancel** to keep the original | None |

### 10.4 Folder Landing Screen

These live in this area's files but belong to folder management (`chat-conversations-history-and-organisation.md`).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Folder name cannot be empty.` | Error | `src/lib/components/chat/Placeholder/FolderTitle.svelte:45-48`, `:143-146` | Saving or creating a folder with no name | Type a name | None |
| `Folder updated successfully` | Success | `src/lib/components/chat/Placeholder/FolderTitle.svelte:72-73`, `:98-99` | Rename, settings or icon change saved | None | None |
| `Folder deleted successfully` | Success | `src/lib/components/chat/Placeholder/FolderTitle.svelte:120-122` | Folder deleted | None | None |
| `Folder created successfully` | Success | `src/lib/components/chat/Placeholder/FolderTitle.svelte:160-162` | Sub-folder created | None | None |
| `Delete folder?` | Dialog (title) | `src/lib/components/chat/Placeholder/FolderTitle.svelte:183-186` | Delete from the folder menu | Confirm or cancel | None |
| `Are you sure you want to delete "{NAME}"?` | Dialog (text) | `src/lib/components/chat/Placeholder/FolderTitle.svelte:195-197` | Same dialog; a checkbox `Delete all contents inside this folder` is ticked by default | Untick to keep the chats | Folder document |
| `{error}` | Error | `src/lib/components/chat/Placeholder/FolderTitle.svelte:61`, `:76`, `:92`, `:102`, `:115`, `:128`, `:156` | A folder request failed | Retry | Server log |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it never changes data, settings, roles or access. Useful identifiers for any escalation:
the chat id (the part after `/c/` in the address, or **Chat ID** in the `/status` panel,
`src/lib/components/chat/MessageInput.svelte:1874-1889`), the approximate time, the model name shown above the
answer, the exact text of any pop-up or error box, the browser and device, and a screenshot. The support
mailbox, queue and hours are **TO BE CONFIRMED**.

### 11.1 "Pressing Enter doesn't send my message"

**Symptom.** Enter makes a new line, or nothing happens.

**Likely causes, in order.**
1. **Enter Key Behavior** is set to `Ctrl+Enter to Send` (`src/lib/components/chat/MessageInput.svelte:2155-2158`).
2. The cursor is inside a list, code block or heading, where Enter continues the block
   (`src/lib/components/common/RichTextInput.svelte:1183-1192`).
3. A `/`, `#`, `@`, `$` or `:` pop-up is open and Enter picks an item
   (`src/lib/components/chat/MessageInput/CommandSuggestionList.svelte:71-77`).
4. The device is a phone or tablet: Enter never sends there (`src/lib/components/chat/MessageInput.svelte:2139-2146`).
5. The text box is empty and nothing is attached (`:2162`).

**Diagnostic steps.** Ask which device and whether the text is a list or code. Ask the user to open
Settings > Interface and read the **Enter Key Behavior** button.

**Resolution.** Press Ctrl+Enter (Cmd+Enter on a Mac) or the send arrow; leave the list with a second Enter or
Shift+Tab; or change **Enter Key Behavior** themselves.

**Escalation.** Not normally needed; if Enter fails in plain text on a computer with `Enter to Send`, send the
browser, keyboard language (input method) and a screen recording.

### 11.2 "Enter sends my message before I've finished"

**Symptom.** The user wants a line break.

**Likely causes, in order.** Default behaviour (`Enter to Send`).

**Diagnostic steps.** None.

**Resolution.** Shift+Enter gives a new line (`src/lib/components/common/RichTextInput.svelte:1172-1181`); or
switch **Enter Key Behavior** to `Ctrl+Enter to Send`.

**Escalation.** None.

### 11.3 "The send button is grey and I can't send"

**Symptom.** The up-arrow button is pale and does nothing.

**Likely causes, in order.**
1. The box is empty and nothing is attached (`src/lib/components/chat/MessageInput.svelte:2743-2747`).
2. A response is running: the area shows **Stop** instead; typing makes **Send** reappear, and the message is
   queued (5.9).
3. A dictation is in progress (the composer is replaced by the recording bar).

**Diagnostic steps.** Ask for a screenshot of the composer area.

**Resolution.** Type text or attach a file; wait for or stop the running response.

**Escalation.** If text is present and the button stays grey, send the screenshot, browser and chat id.

### 11.4 "My message is stuck in a box above the input and hasn't been sent"

**Symptom.** A row with an arrow icon, the message text and **Send now** / **Edit** / **Delete** icons sits above
the composer.

**Likely causes, in order.**
1. The previous response is still generating; queued messages go out together when it finishes
   (`src/lib/components/chat/Chat.svelte:3191-3208`, `:2487-2524`).
2. One queued item has a file that is still uploading or shows `Upload failed`; the whole queue waits
   (`:2493-2500`).
3. The previous response is stuck "generating" (see 11.7).

**Diagnostic steps.** Is a response still streaming (blinking bar or Stop button)? Does any queued row show
`Upload failed` or a spinner?

**Resolution.** Wait, or click **Send now** on the item (this stops the running response). For `Upload failed`,
click **Edit** or **Delete** on that item. Note that several queued messages are merged into one message.
Reloading the page discards the queue (`src/lib/stores/index.ts:123-125`).

**Escalation.** If uploads fail repeatedly, follow `files-uploads-and-storage.md` with the file type and size.

### 11.5 "It says 'Model not selected'"

**Symptom.** Red pop-up `Model not selected` on send, or the model selector shows no model.

**Likely causes, in order.**
1. The chat's model was removed, hidden, or the user lost access to it; the selection becomes empty
   (`src/lib/components/chat/Chat.svelte:3099-3105`, `:2316-2321`).
2. No models are available to the user at all.
3. With `chat.multiple_models` off, a multi-model chat reopens with only its first model, which may itself be
   unavailable (`:2323-2325`).

**Diagnostic steps.** Ask the user to open the model selector and say which models are listed. Check whether the
same model works in a new chat.

**Resolution.** Pick an available model and send again.

**Escalation.** If the list is empty or a needed model is missing, escalate to the model administrators with the
user's group membership and the model name (`models` area).

### 11.6 "I get 'Uh-oh! There was an issue with the response.'"

**Symptom.** A red pop-up and a grey box under the answer starting with
`Uh-oh! There was an issue with the response.` and a second line of detail, or another text in the grey box.

**Likely causes, in order.**
1. The model provider returned an error (rate limit, quota, model unavailable, request too large); the second line
   is the provider's text (`src/lib/components/chat/Chat.svelte:3716-3756`).
2. The conversation is too long for the model.
3. A tool server or plugin failed during the reply (for example `Failed to connect to MCP server '{server_id}'`,
   `backend/open_webui/utils/middleware.py:3010-3011`).
4. A network interruption between the browser and the server (`src/lib/components/chat/Chat.svelte:3643-3668`).

**Diagnostic steps.** Read the second line exactly. Try **Regenerate**. Try the same question in a new chat and
with another model. Note the time.

**Resolution.** Regenerate, start a new chat for very long conversations, or switch off the failing tool.

**Escalation.** Send the full error text, model, time and chat id to the platform maintainer; the server log at that
time holds the provider's response (`chat-completion-pipeline-and-generation-tasks.md`).

### 11.7 "The answer stopped halfway / never finished"

**Symptom.** The answer ends mid-sentence, or the blinking bar stays forever.

**Likely causes, in order.**
1. The user pressed Stop or Escape (Escape in the composer stops generation,
   `src/lib/components/chat/MessageInput.svelte:2117-2119`).
2. The model hit its output limit.
3. The connection or server was interrupted; on reopening, an unfinished answer with no running task is marked
   finished (`src/lib/components/chat/Chat.svelte:2398-2412`, `:1535-1552`).
4. A tool approval or ask-user question is waiting (look for **Allow** / **Deny** or a card above the composer).

**Diagnostic steps.** Reload the chat. Look for an approval card or ask-user card. Check for an error box.

**Resolution.** **Continue Response** (last answer only) asks the model to carry on; **Regenerate** starts again.

**Escalation.** If answers regularly stop for many users, send times, models and chat ids to the platform maintainer.

### 11.8 "I can't see the thinking steps, tool details or 'Searching...' lines anymore"

**Symptom.** Answers show only text; no status line, no "Thought for ..." blocks, no tool cards, no task list.

**Likely causes, in order.**
1. **Hide Processing Details** is on for this user (MedIT GPT fork, 5.22), possibly as an admin default (it then
   shows a small `Default` label beside the switch).
2. The model's `status_updates` capability is off (status lines only,
   `src/lib/components/chat/Messages/ResponseMessage.svelte:198-199`).
3. The model simply did not use tools or reasoning for that answer.

**Diagnostic steps.** Ask the user to open Settings > Interface > Chat and read the **Hide Processing Details**
switch. Compare with another model.

**Resolution.** The user can switch **Hide Processing Details** off; details reappear on every chat at once,
because nothing was deleted.

**Escalation.** If the switch is off and details are still missing for a model, ask the model administrators about
that model's capabilities.

### 11.9 "It just says 'Thinking...' and nothing else for a long time"

**Symptom.** With **Hide Processing Details** on, a shimmering `Thinking...` line stays.

**Likely causes, in order.**
1. The model is working through tools, searches or reasoning, which are hidden; `Thinking...` stays until answer text
   arrives (`src/lib/components/chat/Messages/ResponseMessage.svelte:216-221`).
2. A slow provider or a long tool run.
3. The response is actually stuck (see 11.7).

**Diagnostic steps.** Ask the user to switch **Hide Processing Details** off temporarily to see the real progress
line.

**Resolution.** Wait, or stop and regenerate.

**Escalation.** As 11.7, noting that the setting was on.

### 11.10 "The little [1] source links in answers disappeared"

**Symptom.** Answers that used documents or web search no longer show the small source chips in the text.

**Likely causes, in order.**
1. **Inline Citations** is off for this user (fork, 5.23); the **Sources** button under the answer should still be
   there.
2. The model's `citations` capability is off: then the **Sources** button is also missing
   (`src/lib/components/chat/Messages/ResponseMessage.svelte:934-942`).
3. The model did not cite (no `[n]` markers in its answer).

**Diagnostic steps.** Is the `{COUNT} Sources` button present under the answer? Ask the user to read the
**Inline Citations** switch in Settings > Interface > Chat.

**Resolution.** The user switches **Inline Citations** back on; the chips return immediately on existing answers.

**Escalation.** If the switch is on and the Sources button is also missing, ask the model administrators about the
model's citations capability.

### 11.11 "Numbers in square brackets vanished from my answer"

**Symptom.** Text such as "see step [2]" lost its "[2]".

**Likely causes, in order.** **Inline Citations** off, or a model without the `citations` capability: the code removes
every `[number]` pattern outside code, citation or not (`src/lib/components/chat/Messages/ContentRenderer.svelte:133-138`).

**Diagnostic steps.** Ask whether **Inline Citations** is off. Use **Copy**: the copied text still contains the
brackets (`src/lib/components/chat/Messages/ResponseMessage.svelte:1124-1126`).

**Resolution.** Switch **Inline Citations** on, or copy the answer to see the original text.

**Escalation.** Report to the platform maintainer as a known side effect of the fork setting if it causes real
problems (section 14).

### 11.12 "A tool keeps asking me to Allow or Deny" or "It says 'Tool call has already been resolved.'"

**Symptom.** Cards reading `Allow {NAME}?` with **Allow** and **Deny**; or a red pop-up after clicking one.

**Likely causes, in order.**
1. The user's **Tool Permissions** mode is `Ask for approval` (only offered when the admin enabled tool permissions,
   `src/lib/components/chat/MessageInput/InputMenu.svelte:74`, `:146-185`).
2. The call was already handled (double click, or the chat is open in two tabs):
   `Tool call has already been resolved.` (`backend/open_webui/utils/tool_approval.py:53-58`).

**Diagnostic steps.** Ask the user to open **+ > Tool Permissions** and read the selected mode. Ask whether the chat
is open twice.

**Resolution.** Choose **Allow** or **Deny** for each call, or switch the mode to `Full access` (this also allows the
most recent waiting call, `src/lib/components/chat/Chat.svelte:465-503`). For the pop-up, reload the chat.

**Escalation.** If a tool asks even in `Full access` mode, send the tool name, chat id and time.

### 11.13 "I can't attach files; the + menu items are greyed out"

**Symptom.** Greyed items with a tooltip, or a red pop-up on drop or paste.

**Likely causes, in order.**
1. A selected model lacks file upload: `Model(s) do not support file upload`
   (`src/lib/components/chat/MessageInput/InputMenu.svelte:188-189`).
2. The user lacks `chat.file_upload`: `You do not have permission to upload files.`
3. Admin limits on count or size (`You can only chat with a maximum of {maxCount} file(s) at a time.`,
   `File size should not exceed {maxSize} MB.`).
4. An empty or unreadable file.

**Diagnostic steps.** Read the tooltip text. Try with another model. Note the file's type and size.

**Resolution.** Switch model, use smaller or fewer files.

**Escalation.** Permission questions go to the user's administrator (access is not changed by tier 1); upload
failures with a file type and size go per `files-uploads-and-storage.md`.

### 11.14 "My image upload says the model doesn't support images"

**Symptom.** `Selected model(s) do not support image inputs`, or a yellow warning icon on an image thumbnail, or
`Model {modelName} is not vision capable` after sending.

**Likely causes, in order.** At least one selected model lacks the `vision` capability
(`src/lib/components/chat/MessageInput.svelte:1126-1130`, `:1949-1972`; `src/lib/components/chat/Chat.svelte:3336-3358`).

**Diagnostic steps.** Hover the warning icon: it names the models that cannot see images.

**Resolution.** Choose a vision-capable model or remove that model from the selection.

**Escalation.** If no vision model is available to the user, raise it with the model administrators.

### 11.15 "Web Search, Image or Code Interpreter is missing from the menu"

**Symptom.** The Integrations menu lacks the entry, or the Integrations button is missing entirely.

**Likely causes, in order.**
1. The admin feature switch is off (web search and image generation are off by default,
   `backend/open_webui/config.py:1161`, `:1351`).
2. A selected model lacks the matching capability; with several models selected, every one must have it
   (`src/lib/components/chat/MessageInput.svelte:824-841`).
3. The user lacks `features.web_search`, `features.image_generation` or `features.code_interpreter`.
4. Code Interpreter only: a terminal is selected (they are mutually exclusive, `:843-846`).

**Diagnostic steps.** Try with a single, different model. Ask whether a terminal is selected (terminal chip in the
composer).

**Resolution.** Switch model, or deselect the terminal.

**Escalation.** Feature or permission requests go to the administrators with the user's group and the model.

### 11.16 "A 'Use Web Search?' window pops up"

**Symptom.** A dialog titled `Use Web Search?` with **Continue** and **Cancel**.

**Likely causes, in order.** The admin requires confirmation for web search (`web.search.confirmation.enable`); the
dialog appears when web search is switched on or used in a chat
(`src/lib/components/chat/Chat.svelte:357-379`, `:3165-3173`).

**Diagnostic steps.** None needed.

**Resolution.** **Continue** to search (it is remembered for that chat until web search is turned off), **Cancel**
to send without searching.

**Escalation.** Questions about the wording or the provider go to the platform maintainer.

### 11.17 "There's no Run button on my code" or "It says 'Execution Time Limit Exceeded'"

**Symptom.** A Python block without **Run**; or the output shows `Execution Time Limit Exceeded`.

**Likely causes, in order.**
1. The block is not marked as Python and does not look like Python (`src/lib/components/chat/Messages/CodeBlock.svelte:106-139`, `:498`).
2. The admin switched code execution off.
3. Time limit: in-browser runs stop after 60 seconds (`:260-269`).
4. Large packages take time to load in the browser on the first run.

**Diagnostic steps.** Check the language label at the top of the block.

**Resolution.** Ask the model to label the block `python`; shorten the work; retry.

**Escalation.** Per `code-execution-and-interpreter.md`.

### 11.18 "The diagram shows 'Failed to render diagram'"

**Symptom.** A red box `Failed to render diagram: {errorMsg}` (or `Failed to render visualization: ...`) above
the diagram source.

**Likely causes, in order.** The model wrote invalid Mermaid or Vega syntax
(`src/lib/components/chat/Messages/CodeBlock.svelte:367-391`).

**Diagnostic steps.** Read the error after the colon.

**Resolution.** Ask the model to correct the diagram, quoting the error.

**Escalation.** None unless every diagram fails.

### 11.19 "I edited my question and my old answer disappeared" or "What does 2/2 mean?"

**Symptom.** After an edit or regenerate, the earlier answer is gone and `2/2` with arrows appears.

**Likely causes, in order.** Edit with **Send**, **Regenerate**, **Save As Copy** and **Merge Responses** add a new
version beside the old one (5.13).

**Diagnostic steps.** Look for `<` `n/m` `>` under the question or answer.

**Resolution.** Use the arrows (or double-click the counter and type a number) to go back. The **Overview** tab in the
side panel shows every version.

**Escalation.** None.

### 11.20 "I switched to another answer version, but after reloading it shows the old one"

**Symptom.** The version chosen with the arrows is not the one shown after a reload.

**Likely causes, in order.** In a single-model chat, arrow navigation is only saved the next time the chat is saved,
for example when a message is sent (5.13; `src/lib/components/chat/Messages.svelte:199-307`).

**Diagnostic steps.** Ask whether anything was sent after switching.

**Resolution.** Switch again; clicking the version in the **Overview** tab saves it straight away
(`src/lib/components/chat/Chat.svelte:1122-1144`).

**Escalation.** Report to the platform maintainer if this matters to users (section 14).

### 11.21 "I deleted a message but it came back after reloading"

**Symptom.** A deleted message reappears.

**Likely causes, in order.** The server refused or failed the delete; the browser had already removed it from the
screen and shows no error (`src/lib/components/chat/Messages.svelte:418-459`). Only the chat's owner or an admin can
delete (`backend/open_webui/routers/chats.py:1468-1503`).

**Diagnostic steps.** Ask whether the chat belongs to the user (a read-only chat has no Delete button at all).

**Resolution.** Try again after a reload.

**Escalation.** Send the chat id, the message time and the time of the attempt.

### 11.22 "The Delete, Regenerate, Continue or thumbs buttons are missing"

**Symptom.** Some buttons under answers or questions are not there.

**Likely causes, in order.**
1. The answer is still generating (buttons appear when it finishes).
2. **Delete** under an answer only appears when the question has more than one answer; under a question it is not
   offered for the very first message without versions (`src/lib/components/chat/Messages/ResponseMessage.svelte:1584`;
   `src/lib/components/chat/Messages/UserMessage.svelte:594`).
3. **Continue Response** is only on the last answer (`src/lib/components/chat/Messages/ResponseMessage.svelte:1357`).
4. Rating is hidden in temporary chats and when the admin switched rating off (`:1279`).
5. A permission (`chat.delete_message`, `chat.regenerate_response`, `chat.continue_response`, `chat.rate_response`,
   `chat.edit`, `chat.tts`) is off for the user's groups (section 3.1).
6. The chat is read-only (someone else's chat).
7. Older answers only show buttons on hover (unless **Accessibility Mode** is on).

**Diagnostic steps.** Ask which button, on which message, and whether the chat is temporary or read-only.

**Resolution.** Explain the rule that applies.

**Escalation.** Permission questions go to the user's administrator with the permission key from section 3.1.

### 11.23 "My prompt still shows {{...}} in the text"

**Symptom.** After inserting a saved prompt, the composer contains `{{name}}`-style placeholders.

**Likely causes, in order.**
1. The **Input Variables** form was cancelled, which leaves the placeholders
   (`src/lib/components/chat/MessageInput.svelte:263-281`).
2. A profile placeholder (`{{USER_BIO}}`, `{{USER_EMAIL}}` and similar) found an empty profile field and was treated as
   an input variable (`:329-369`).
3. The placeholders were typed or pasted by hand, which does not open the form.

**Diagnostic steps.** Ask how the prompt was inserted and whether a form appeared.

**Resolution.** Press Tab to jump to each placeholder and type the value, or re-insert the prompt and fill the form.

**Escalation.** If a shared prompt is badly written, tell its owner (`prompts` area).

### 11.24 "A 'Chat Variables' window opens when I try to send"

**Symptom.** The message is not sent and a `Chat Variables` form appears, or a red pop-up
`Chat Variables have conflicting model definitions`.

**Likely causes, in order.** The selected model requires chat variables that are empty; or two selected models define
the same variable differently (`src/lib/components/chat/Chat.svelte:3142-3151`, `:4179-4218`).

**Diagnostic steps.** Ask which models are selected.

**Resolution.** Fill in and **Save** the form, then send again; for a conflict, select one model.

**Escalation.** Conflicting definitions go to the model owners.

### 11.25 "The microphone or voice button says permission denied"

**Symptom.** `Permission denied when accessing microphone: {error}`, `Permission denied when accessing media devices`,
`Error accessing media devices.`, or `Call feature is not supported when using Web STT engine`.

**Likely causes, in order.** The browser or operating system blocks the microphone for the site; no microphone; the
admin's speech-to-text engine is the browser, which disables Voice mode
(`src/lib/components/chat/MessageInput.svelte:2636-2726`).

**Diagnostic steps.** Ask the user to check the site's microphone permission in the browser.

**Resolution.** Allow the microphone and reload; use Dictate instead of Voice mode when the latter is unsupported.

**Escalation.** Per `audio-speech-to-text-and-text-to-speech.md`.

### 11.26 "The chat says 'Read only' and there's no input box"

**Symptom.** `Read only` where the composer should be.

**Likely causes, in order.** The chat belongs to another account (opened through a shared folder, a link, or by an
admin) (`src/lib/components/chat/Chat.svelte:391-392`, `:4433-4438`).

**Diagnostic steps.** Ask how the chat was opened.

**Resolution.** To continue the conversation, the user can start their own chat (the **Fork chat** button is not
shown in a read-only view, `src/lib/components/chat/Messages/ResponseMessage.svelte:1552`).

**Escalation.** Access questions go to the chat's owner or the administrators.

### 11.27 "Pasting long text turned it into a file"

**Symptom.** A `Pasted_Text_{timestamp}.txt` chip appears instead of the text.

**Likely causes, in order.** **Paste Large Text as File** is on and the paste exceeded 1,000 characters
(`src/lib/components/chat/MessageInput.svelte:2180-2205`; `src/lib/constants.ts:130`).

**Diagnostic steps.** None.

**Resolution.** Hold Shift while pasting to paste as text, or switch the setting off.

**Escalation.** None.

## 12. Local Customisations

Apart from the items below, every file in this area matches upstream Open WebUI v0.11.4. Checked with
`git diff main...uoft` (committed fork changes) and `git diff` (uncommitted working-tree changes) on
2026-10-07. Both fork features live entirely in the browser; the server only stores the two new user settings
(`backend/open_webui/models/users.py:99-100`).

### 12.1 Committed on the `uoft` Branch

| File | Change |
|---|---|
| `src/lib/components/common/InterfaceSettings.svelte` (outside this area's scope, the settings screen) | Adds the **Inline Citations** and **Hide Processing Details** switches to the Chat section, defaults on and off (`:79-80`, `:357-358`, `:1335-1378`) |
| `src/lib/stores/index.ts` | Adds `showInlineCitations` and `hideProcessingDetails` to the settings type (`:232-233`) |
| `backend/open_webui/models/users.py` | Adds the two keys to the stored interface settings model (`:99-100`) |
| `src/lib/i18n/locales/en-US/translation.json` | Labels and descriptions (`:2923-2924`, `:2935-2936`). The other 63 locale files get the same keys with empty values, so every language shows the English text for these two settings |
| `src/lib/components/chat/Messages/ContentRenderer.svelte` | **Inline Citations**: `hideInlineCitations` combines the model capability with the user switch, and the citation-stripping function became reactive so visible answers update at once (`:128-138`) |
| `src/lib/components/chat/MessageInput.svelte` | Hides the task list above the composer when processing details are hidden (`:1791-1796`) |
| `src/lib/components/chat/Messages/ResponseMessage.svelte` | Hides the status history and code-execution chips; adds the `Thinking...` indicator (`:197-221`, `:720-722`, `:920-928`, `:944-946`) |
| `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte` | Drops reasoning and code-analysis blocks from text answers and keeps tool calls ungrouped (`:69-110`, `:146-147`) |
| `src/lib/components/chat/Messages/structuredOutput.ts` and `src/lib/components/chat/Messages/StructuredOutputRenderer.svelte` | The same filtering for structured answers (`structuredOutput.ts:344-347`, `:404-416`; `StructuredOutputRenderer.svelte:70-71`) |
| `src/lib/components/chat/Messages/Markdown/HTMLToken.svelte` | Hides `<status>` lines written into the answer text (`:89-105`) |
| `src/lib/components/common/ToolCallDisplay.svelte` | Shows only calls that wait for the user, and drops the tool-name caption above embeds, when details are hidden (`:178-200`) |

### 12.2 Uncommitted in the Working Tree (as of 2026-10-07)

These refine the Hide Processing Details behaviour. They are what the code does today but are not yet part of
the branch history; whether the production build includes them is **TO BE CONFIRMED**.

| File | Change | Effect a user would notice |
|---|---|---|
| `src/lib/components/chat/Chat.svelte:2847-2850` | When the server reports `done: false` on a message (as it does when a reply resumes after a tool approval), the message is marked as running again | The `Thinking...` line, the blinking bar and the Stop button come back while an approved tool runs |
| `src/lib/components/chat/Messages/ResponseMessage.svelte:67`, `:70-75`, `:197-221`, `:920-921` | The committed "in progress" logic (inspecting approved and unresolved tool calls and `<details status="pending">` text) is replaced by `!message.done`, `hasPendingToolCall` and a check for visible answer text; the indicator now uses the standard status-line look | Same text, consistent styling; behaviour after approvals now depends on the `Chat.svelte` change above |
| `src/lib/components/chat/Messages/structuredOutput.ts:404-416`, `:454-457` | Each kept tool call is flushed on its own; new `hasPendingToolCall` (a `function_call` whose status is `pending`) | No grouped "Explored" header while hidden; approval cards stand alone |
| `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte:90-105`, `:518-531` | Same per-call flushing for text answers; no longer passes the setting to the tool card | As above |
| `src/lib/components/chat/Messages/StructuredOutputRenderer.svelte:176-188` | No longer passes the setting to the tool card | None by itself |
| `src/lib/components/common/ToolCallDisplay.svelte:36-45`, `:145` | Reads **Hide Processing Details** from the user's settings itself instead of receiving it | The rule applies to every tool card, including grouped ones |
| `src/lib/components/chat/Messages/Markdown/HTMLToken.svelte:93-105` | Simplified condition, same result | None |
| `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:8` | Type annotation only | None |
| `src/lib/i18n/locales/en-US/translation.json:2923` | Description reworded: the committed wording listed only status updates, tool calls and reasoning, and said that tool outputs such as images still appear; the working tree adds code analysis and says images or embeds from tools still appear | New wording in Settings |
| `src/lib/i18n/index.ts` (outside this area) | Maps a browser language such as `en-CA` or `fr-CA` to the closest available translation and falls back to English after a configured default language | Which language the whole interface opens in (`i18n` area) |
| `static/pyodide/pyodide-lock.json` (outside this area) | Pyodide package lock changes | In-browser Python (`code-execution-and-interpreter.md`) |

### 12.3 Points to Note About the Fork Features

- Both switches change display only. Stored chats are identical whichever way they are set, so exports, shared
  chats and admin views still contain every detail.
- **Copy** and **Read Aloud** ignore **Inline Citations**: copied text keeps `[n]` markers (5.23).
- With **Inline Citations** off, any `[number]` in prose outside code is removed as well (5.23, 11.11). Upstream
  already does this for models without the `citations` capability.
- Admins can preset both switches for everyone through `ui.default_interface_settings` (7.1, 7.3); users can still
  change them unless they lack `settings.interface`.

## 13. Source File Index

Every file this document cites, plus every file in this area's scope as defined in `_areas.md` (area 5):
142 files, 109 in scope and 33 cited from other areas for context. **In scope** says which is which. The 24
in-scope files that sections 1 to 12 do not cite were opened only far enough to describe them here; "not
imported" means a search of `src/` found no import of the file.

### 13.1 Routes

| File | What it holds | In scope |
|---|---|---|
| `src/routes/(app)/+page.svelte` | The `/` page: shows an `error` address parameter as a pop-up, then mounts the chat screen for a new chat (2) | Yes |
| `src/routes/(app)/c/[id]/+page.svelte` | The `/c/{id}` page: mounts the chat screen with the chat id taken from the address (2) | Yes |
| `src/routes/(app)/home/+layout.svelte` | Header of the `/home` stub with **Notes** and **Calendar** links (2) | Yes |
| `src/routes/(app)/home/+page.svelte` | Empty file (the `/home` body) | Yes |
| `src/routes/(app)/+layout.svelte` | App-wide shortcut handling used on this screen: add a message without a reply, regenerate, allow or deny a tool call (2) | No |

### 13.2 Chat Shell

The screen around the message list: top bar, landing screen, side panel and the cards outside the messages.

| File | What it holds | In scope |
|---|---|---|
| `src/lib/components/chat/Chat.svelte` | The chat screen as a whole: loading, address parameters, send, queue, stop, regenerate, continue, fork, compact, merge, websocket events, drafts, autosave, temporary and read-only modes, plugin dialogs; carries an uncommitted fork change (12.2) | Yes |
| `src/lib/components/chat/Navbar.svelte` | Top bar: sidebar button, title, chat menu, **Temporary Chat** or **Save Chat**, **Controls**, the hidden delete shortcut, banners and licence notices (5.1, 5.2) | Yes |
| `src/lib/components/chat/Placeholder.svelte` | New-chat landing screen: model heading, temporary label, centred composer and suggestions, or a folder's title and chats (5.1) | Yes |
| `src/lib/components/chat/ChatPlaceholder.svelte` | Greeting and suggestions inside the message area when **Landing Page Mode** is `chat` (5.1) | Yes |
| `src/lib/components/chat/Suggestions.svelte` | Suggestion cards: `Suggested` heading, shuffled order, fuzzy filtering, and the site name and version line when there are none (5.1) | Yes |
| `src/lib/components/chat/Placeholder/FolderTitle.svelte` | Folder heading on a folder's landing screen: rename, settings, icon, new sub-folder, delete (10.4) | Yes |
| `src/lib/components/chat/Placeholder/FolderPlaceholder.svelte` | Folder landing body: the folder's chats, 10 per page, sortable by title or update time, with owner details for shared folders (`src/lib/components/chat/Placeholder/FolderPlaceholder.svelte:28-43`) | Yes |
| `src/lib/components/chat/Placeholder/ChatList.svelte` | The folder's chat table (`Title`, `Updated at`, date groups; `No chats found` when empty) | Yes |
| `src/lib/components/chat/Placeholder/FolderKnowledge.svelte` | Empty file, imported for a folder **Knowledge** tab whose buttons are commented out (`src/lib/components/chat/Placeholder/FolderPlaceholder.svelte:171-197`) | Yes |
| `src/lib/components/chat/AskUserCard.svelte` | Ask-user card above the composer: questions, options, `Other`, **Previous**, **Next**, **Submit answers**, time limit (5.18) | Yes |
| `src/lib/components/chat/ChatControls.svelte` | Side panel: a resizable panel or a drawer showing the voice call, an embed, Artifacts, or the **Controls**, **Files** and **Overview** tabs (5.20) | Yes |
| `src/lib/components/chat/ChatControls/Embeds.svelte` | Embeds panel: an interactive page with its title and `Close embed` (5.20) | Yes |
| `src/lib/components/chat/Controls/Controls.svelte` | **Controls** tab: `Files`, `Valves`, `System Prompt` and `Advanced Params`, each behind its `chat.*` permission (3.1, 5.20) | Yes |
| `src/lib/components/chat/Controls/Valves.svelte` | Valves section: choose a tool or function and edit its user valves; saves with `Valves updated` (5.20) | Yes |
| `src/lib/components/chat/Overview.svelte` | Wrapper that mounts the Overview tree inside the diagram library | Yes |
| `src/lib/components/chat/Overview/View.svelte` | **Overview** tab: builds the message tree; clicking a node switches to that branch and saves it (5.13, 5.20) | Yes |
| `src/lib/components/chat/Overview/Node.svelte` | One Overview node: avatar, name, two lines of text, errors in red, favourite heart (5.20) | Yes |
| `src/lib/components/chat/Overview/Flow.svelte` | Overview canvas and its buttons: `Viewport Pinned` / `Viewport Unpinned`, `Vertical Layout`, `Horizontal Layout` (5.20) | Yes |
| `src/lib/components/chat/Artifacts.svelte` | Artifacts panel: HTML and SVG preview, versions, **Copy**, **Download**, full screen, sandbox switches (5.15, 5.20) | Yes |
| `src/lib/components/chat/ContentRenderer/FloatingButtons.svelte` | **Ask** and **Explain** buttons on selected answer text, plus user-defined quick actions (5.19) | Yes |
| `src/lib/components/chat/ModelSelector.svelte` | The model selector placed in the composer; documented in `workspace-models-and-model-access.md` | No |
| `src/lib/components/chat/SettingsModal.svelte` | Settings window; shows the **Interface** tab to admins and to users with `settings.interface` (7.3) | No |
| `src/lib/components/layout/Navbar/Menu.svelte` | The `...` **Chat actions** menu; documented with chat management | No |

### 13.3 Composer and `MessageInput/`

| File | What it holds | In scope |
|---|---|---|
| `src/lib/components/chat/MessageInput.svelte` | The composer: text box, chips, attachments and upload rules, trigger pop-ups, prompt variables, model selector slot, **Stop**, **Dictate**, **Voice mode**, **Send**, the `/status` panel, queued rows and footer; hides the task list for the fork (5.3 to 5.10, 12.1) | Yes |
| `src/lib/components/chat/MessageInput/InputMenu.svelte` | The **+** (More) menu: **Tool Permissions**, **Upload Files**, **Capture**, **Attach Webpage**, **Attach Files**, **Attach Notes**, **Attach Knowledge**, **Reference Chats** and the cloud pickers (5.6) | Yes |
| `src/lib/components/chat/MessageInput/InputMenu/Files.svelte` | **Attach Files** list of the user's earlier uploads, 50 at a time (5.6) | Yes |
| `src/lib/components/chat/MessageInput/InputMenu/Notes.svelte` | **Attach Notes** list (5.6) | Yes |
| `src/lib/components/chat/MessageInput/InputMenu/Knowledge.svelte` | **Attach Knowledge** list, with `Show Files` for single files (5.6) | Yes |
| `src/lib/components/chat/MessageInput/InputMenu/Chats.svelte` | **Reference Chats** list (5.6) | Yes |
| `src/lib/components/chat/MessageInput/InputMenu/SearchInput.svelte` | Search box shared by the four lists above and by the Integrations tool and skill lists | Yes |
| `src/lib/components/chat/MessageInput/AttachWebpageModal.svelte` | **Attach Webpage** form: `Webpage URLs`, one per line (5.6) | Yes |
| `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte` | **Integrations** menu: tools, skills, toggleable filters, **Web Search**, **Image**, **Code Interpreter**, valves knobs and `Disconnect OAuth` (5.7) | Yes |
| `src/lib/components/chat/MessageInput/TerminalMenu.svelte` | Terminal picker in the chip row; user-added terminals need `features.direct_tool_servers` (3.1) | Yes |
| `src/lib/components/chat/MessageInput/CommandSuggestionList.svelte` | The trigger pop-up: picks the list for `/`, `#`, `@`, `$` or `:` and handles keyboard selection (5.5, 5.8) | Yes |
| `src/lib/components/chat/MessageInput/Commands/SlashCommands.svelte` | `/` list: `Commands`, `Prompts` and `Skills` (5.8) | Yes |
| `src/lib/components/chat/MessageInput/Commands/Knowledge.svelte` | `#` list: a typed web or YouTube address, `Folders`, `Collections` and `Files` (5.8) | Yes |
| `src/lib/components/chat/MessageInput/Commands/AtCommands.svelte` | `@` list: terminal files, a typed address, folders, knowledge, files and `Models` (5.8) | Yes |
| `src/lib/components/chat/MessageInput/Commands/Skills.svelte` | `$` list of skills; terminal skills labelled `Terminal` (5.8) | Yes |
| `src/lib/components/chat/MessageInput/Commands/Emojis.svelte` | `:` list of emojis (5.8) | Yes |
| `src/lib/components/chat/MessageInput/Commands/Models.svelte` | A `Models` list that is not imported (the `@` list shows models instead) | Yes |
| `src/lib/components/chat/MessageInput/Commands/Prompts.svelte` | A `Prompts` list that is not imported (the `/` list shows prompts instead) | Yes |
| `src/lib/components/chat/MessageInput/InputVariablesModal.svelte` | **Input Variables** form for `{{name}}` placeholders in inserted prompts (5.8) | Yes |
| `src/lib/components/chat/MessageInput/QueuedMessageItem.svelte` | One queued message: text or `Empty message`, file chips, `Upload failed`, **Send now**, **Edit**, **Delete** (5.9) | Yes |
| `src/lib/components/chat/MessageInput/VoiceRecording.svelte` | Dictation bar: waveform, timer, cancel and `Confirm recording`; browser or server transcription (5.24) | Yes |
| `src/lib/components/chat/MessageInput/FilesOverlay.svelte` | Blurred `Drag and Drop Container` overlay while files are dragged over the chat; also used by notes, channels and knowledge (5.6) | Yes |
| `src/lib/components/chat/MessageInput/CallOverlay.svelte` | Voice call view in the side panel (`Listening...`, `Thinking...`, `Tap to interrupt`, `Muted`, mute, camera, screen share); documented in `audio-speech-to-text-and-text-to-speech.md` | Yes |
| `src/lib/components/chat/MessageInput/CallOverlay/VideoInputMenu.svelte` | Camera choice menu inside the voice call | Yes |

### 13.4 Messages and `Messages/`

Includes the `Markdown/`, `ResponseMessage/` and `Citations/` sub-folders.

| File | What it holds | In scope |
|---|---|---|
| `src/lib/components/chat/Messages.svelte` | The message list: the current branch 8 messages at a time, version switching, and the edit, save and delete handlers with the delete rule (5.2, 5.13, 6.3) | Yes |
| `src/lib/components/chat/Messages/Message.svelte` | Chooses the question, single-answer or multi-model component for each message | Yes |
| `src/lib/components/chat/Messages/UserMessage.svelte` | A question: bubble or name, attachments, **Edit** (**Save**, **Cancel**, **Send**), **Copy**, **Delete**, versions, timestamp, timer and sub-agent rows (5.11) | Yes |
| `src/lib/components/chat/Messages/ResponseMessage.svelte` | An answer: status line, files, embeds, content, caret, error box, **Sources**, code-execution chips, action row, rating and follow-ups; the fork's `Thinking...` and hiding (5.12, 5.22) | Yes |
| `src/lib/components/chat/Messages/MultiResponseMessages.svelte` | Several models' answers side by side or in tabs, and **Merge Responses** (5.14) | Yes |
| `src/lib/components/chat/Messages/Name.svelte` | Styling wrapper for the name line above a message | Yes |
| `src/lib/components/chat/Messages/ProfileImage.svelte` | Avatar with a fallback picture, for people and models | Yes |
| `src/lib/components/chat/Messages/Skeleton.svelte` | Grey placeholder lines; here shown in the **Merged Response** block until its text arrives (`src/lib/components/chat/Messages/MultiResponseMessages.svelte:406-407`) | Yes |
| `src/lib/components/chat/Messages/ContentRenderer.svelte` | Markdown or plain text, citation-marker removal (the fork's **Inline Citations**), automatic Artifacts and the floating buttons (5.15, 5.23) | Yes |
| `src/lib/components/chat/Messages/Markdown.svelte` | Sets up `marked` with the extensions in `src/lib/utils/marked/` and fills in `{{USER_NAME}}` and the model name (5.15) | Yes |
| `src/lib/components/chat/Messages/StructuredOutputRenderer.svelte` | Draws answers stored as output items; the fork's filtering (5.17, 12) | Yes |
| `src/lib/components/chat/Messages/structuredOutput.ts` | Turns output items into display blocks; reasoning durations; sub-agent labels; the fork's `hasPendingToolCall` (5.17, 5.22) | Yes |
| `src/lib/components/chat/Messages/OutputEditView.svelte` | Block editor for structured answers with the **Visual** / JSON switch (5.12) | Yes |
| `src/lib/components/chat/Messages/CodeBlock.svelte` | Code block header and buttons (**Collapse**, **Run**, **Save**, **Copy**, **Preview**), in-browser or Jupyter runs, Mermaid and Vega diagrams (5.15) | Yes |
| `src/lib/components/chat/Messages/DiffBlock.svelte` | Coloured line-by-line view of `diff` and `patch` blocks (5.15) | Yes |
| `src/lib/components/chat/Messages/diff.ts` | `parseDiffRows`, which splits a diff into the rows `DiffBlock.svelte` draws | Yes |
| `src/lib/components/chat/Messages/CodeExecutions.svelte` | Code execution chips under an answer (5.17) | Yes |
| `src/lib/components/chat/Messages/CodeExecutionModal.svelte` | `Code execution: {name}` window with the code, `ERROR`, `OUTPUT` and `Files` (5.17) | Yes |
| `src/lib/components/chat/Messages/Error.svelte` | The grey error box and how it pulls a message out of the error data (5.21) | Yes |
| `src/lib/components/chat/Messages/RateComment.svelte` | Feedback form after a thumbs rating (5.12) | Yes |
| `src/lib/components/chat/Messages/SubagentResultRow.svelte` | **Background sub-agent finished** row in the question position (5.11) | Yes |
| `src/lib/components/chat/Messages/TerminalOutputFile.svelte` | Preview card for a file shown by a terminal tool, with **Download** and **Open** (5.17) | Yes |
| `src/lib/components/chat/Messages/Citations.svelte` | **Sources** button and list, embed-address sources and site icons (5.16) | Yes |
| `src/lib/components/chat/Messages/Citations/CitationModal.svelte` | Citation window for one source: link, `Parameters`, excerpts, `Relevance` and page (5.16) | Yes |
| `src/lib/components/chat/Messages/Citations/CitationsModal.svelte` | A `Citations` window listing every source; not imported | Yes |
| `src/lib/components/chat/Messages/ResponseMessage/StatusHistory.svelte` | Status line above an answer and its expandable history (5.17) | Yes |
| `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte` | Wording of each status step; its look is reused by the fork's `Thinking...` (5.17, 5.22) | Yes |
| `src/lib/components/chat/Messages/ResponseMessage/WebSearchResults.svelte` | Expanded web-search step: the query and the pages found (5.16, 5.17) | Yes |
| `src/lib/components/chat/Messages/ResponseMessage/TaskList.svelte` | `{done} out of {total} tasks completed` checklist above the composer (5.17) | Yes |
| `src/lib/components/chat/Messages/ResponseMessage/FollowUps.svelte` | `Follow up` suggestions under the last answer (5.19) | Yes |
| `src/lib/components/chat/Messages/ResponseMessage/RegenerateMenu.svelte` | Regenerate menu: `Suggest a change`, **Try Again**, **Add Details**, **More Concise** (5.12) | Yes |
| `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte` | Block rendering: headings, lists, tables with **Copy** and **Export to CSV**, details blocks; the fork's hiding (5.15, 5.22) | Yes |
| `src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens.svelte` | Inline rendering: links (same-site chats, notes and channels open in the app), images and citation markers (5.15) | Yes |
| `src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens/TextToken.svelte` | Plain text with the streaming fade-in (5.15) | Yes |
| `src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens/CodespanToken.svelte` | Inline code that copies itself on click (5.15) | Yes |
| `src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens/MentionToken.svelte` | `@model`, `#channel` and `$skill` chips (5.15) | Yes |
| `src/lib/components/chat/Messages/Markdown/MarkdownInlineTokens/NoteLinkToken.svelte` | **Note** card for a link to a note on the same site (5.15) | Yes |
| `src/lib/components/chat/Messages/Markdown/HTMLToken.svelte` | Sanitized raw HTML: video, audio, YouTube, sandboxed iframes, HTML files and `<status>` lines, which the fork can hide (5.15, 5.22) | Yes |
| `src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte` | Folds runs of reasoning, analysis and tool blocks into `Exploring` / `Explored`; grouped approval buttons (5.17, 5.18) | Yes |
| `src/lib/components/chat/Messages/Markdown/AlertRenderer.svelte` | `> [!NOTE]`-style alert boxes (5.15) | Yes |
| `src/lib/components/chat/Messages/Markdown/ColonFenceBlock.svelte` | `:::type` boxes with **Copy** (5.15) | Yes |
| `src/lib/components/chat/Messages/Markdown/KatexRenderer.svelte` | KaTeX maths; a click copies the LaTeX (5.15) | Yes |
| `src/lib/components/chat/Messages/Markdown/SourceToken.svelte` | Inline citation marker: one source chip, or `{first} +{n}` with a hover list (5.16) | Yes |
| `src/lib/components/chat/Messages/Markdown/Source.svelte` | One source chip showing the shortened source name or web domain (5.16) | Yes |

### 13.5 Common Components

| File | What it holds | In scope |
|---|---|---|
| `src/lib/components/common/ToolCallDisplay.svelte` | Tool-call card: labels, `Input` and `Output`, **Allow** / **Deny**, returned images and embeds; the fork's hiding (5.17, 5.18, 12) | Yes |
| `src/lib/components/common/RichTextInput.svelte` | The editor behind the composer: Markdown conversion, Enter and Shift+Enter, Tab, paste handling and ghost text (5.5) | Yes |
| `src/lib/components/common/RichTextInput/AutoCompletion.js` | Grey ghost-text suggestion (prompt autocompletion or the first follow-up); Tab accepts it (5.5) | Yes |
| `src/lib/components/common/RichTextInput/FormattingButtons.svelte` | Buttons of the formatting toolbar (**Show Formatting Toolbar**) (5.5) | Yes |
| `src/lib/components/common/RichTextInput/suggestions.ts` | `getSuggestionRenderer`, which places the trigger pop-up next to the cursor (`src/lib/components/chat/MessageInput.svelte:78`, `:1370`) | Yes |
| `src/lib/components/common/RichTextInput/Collaboration.ts` | Live co-editing over the websocket; switched on by the notes editor (`src/lib/components/notes/NoteEditor.svelte:1375`), not by the composer | Yes |
| `src/lib/components/common/RichTextInput/Image/image.ts` | Inline image node with safe-address filtering; used when a caller sets `image`, which the notes editor does (`src/lib/components/notes/NoteEditor.svelte:1380`) and the composer does not | Yes |
| `src/lib/components/common/RichTextInput/Image/index.ts` | Re-exports the image node | Yes |
| `src/lib/components/common/RichTextInput/listDragHandlePlugin.js` | Drag handles for reordering list items; used with `dragHandle`, which only the notes editor sets (`src/lib/components/notes/NoteEditor.svelte:1378`) | Yes |
| `src/lib/components/common/RichTextInput/commands.ts` | A `/` suggestion extension that is not imported | Yes |
| `src/lib/components/common/Collapsible.svelte` | Collapsible titles for reasoning (`Thought for ...`) and code analysis (`Analyzed`) (5.17) | No |
| `src/lib/components/common/InterfaceSettings.svelte` | Settings > Interface, including the fork's two switches (5.22, 5.23, 7.3) | No |
| `src/lib/components/common/Switch.svelte` | The switch control and its `Default` label (7.3) | No |
| `src/lib/components/notes/NoteEditor.svelte` | The notes editor; cited only to show which shared editor features (co-editing, images, drag handles) it switches on and the composer does not; documented in `notes.md` | No |

### 13.6 Utilities, Stores, API Clients and Translations

| File | What it holds | In scope |
|---|---|---|
| `src/lib/utils/marked/extension.ts` | `<details>` blocks in text answers (reasoning, tools, code analysis) (5.17) | Yes |
| `src/lib/utils/marked/citation-extension.ts` | Reads `[1]`, `[1,2]` and `[1#section]` as citation markers (5.16) | Yes |
| `src/lib/utils/marked/katex-extension.ts` | Maths delimiters for KaTeX (5.15) | Yes |
| `src/lib/utils/marked/footnote-extension.ts` | `[^1]` footnote markers (5.15) | Yes |
| `src/lib/utils/marked/strikethrough-extension.ts` | Strikethrough with `~~` only (5.15) | Yes |
| `src/lib/utils/marked/colon-fence-extension.ts` | `:::type` fences (5.15) | Yes |
| `src/lib/utils/marked/mention-extension.ts` | `<@...>`, `<#...>` and `<$...>` mention tokens, an id with an optional label (registered at `src/lib/components/chat/Messages/Markdown.svelte:24-26`) | Yes |
| `src/lib/utils/index.ts` | Input-variable parsing for inserted prompts (`src/lib/utils/index.ts:1731-1751`) | No |
| `src/lib/utils/localizedContent.ts` | The six built-in upstream prompt suggestions (`src/lib/utils/localizedContent.ts:131-176`) | No |
| `src/lib/shortcuts.ts` | Default keyboard shortcuts (2) | No |
| `src/lib/constants.ts` | The 1,000-character threshold for **Paste Large Text as File** (`src/lib/constants.ts:130`) | No |
| `src/lib/stores/index.ts` | The in-memory message queue (`src/lib/stores/index.ts:123-125`) and the settings type with the fork's two keys (`:232-233`) | No |
| `src/lib/apis/chats/index.ts` | Browser calls that save a chat, delete a message, resolve a tool call, fork and compact (6.2) | No |
| `src/lib/apis/index.ts` | Browser call that stops a chat's running tasks (6.2) | No |
| `src/lib/apis/utils/index.ts` | Browser call for server-side code runs (6.2) | No |
| `src/lib/i18n/index.ts` | Interface language selection; uncommitted change (12.2) | No |
| `src/lib/i18n/locales/en-US/translation.json` | English text of dotted settings keys, including the fork's labels and descriptions (7.3, 12) | No |
| `static/pyodide/pyodide-lock.json` | In-browser Python package lock; uncommitted change (12.2) | No |

### 13.7 Server Files Cited for Context

| File | What it holds | In scope |
|---|---|---|
| `backend/open_webui/config.py` | Permission defaults and `DEFAULT_USER_PERMISSIONS`, the seeded admin settings of section 7.1, and `IFRAME_CSP` (3.1, 7.1) | No |
| `backend/open_webui/env.py` | Environment-only switches named in section 14, such as `ENABLE_ADMIN_CHAT_ACCESS` (`backend/open_webui/env.py:371`) | No |
| `backend/open_webui/main.py` | The `/api/config` switches the screen reads, and the tool-call resolve endpoint (3.2, 5.18) | No |
| `backend/open_webui/constants.py` | `ERROR_MESSAGES` texts (10.3) | No |
| `backend/open_webui/models/chats.py` | The `chat` table and the message delete rule (6.1, 6.3) | No |
| `backend/open_webui/models/chat_messages.py` | The `chat_message` table (6.1) | No |
| `backend/open_webui/models/feedbacks.py` | The `feedback` table, including the chat snapshot (6.2) | No |
| `backend/open_webui/models/users.py` | The stored interface settings, including the fork's two keys (6.5, 12.1) | No |
| `backend/open_webui/routers/chats.py` | Server checks of `chat.import` and `chat.delete`; the message delete endpoint (3.1, 6.3) | No |
| `backend/open_webui/routers/users.py` | Server checks when settings are saved; admin interface defaults laid under the user's own (3.1, 6.5) | No |
| `backend/open_webui/routers/audio.py` | Server checks of `chat.tts` and `chat.stt` (3.1) | No |
| `backend/open_webui/routers/retrieval.py` | Server check of `features.web_search` (3.1) | No |
| `backend/open_webui/utils/middleware.py` | Saving a provider error on the message and sending `chat:message:error`; the MCP connection failure text (5.21) | No |
| `backend/open_webui/utils/tool_approval.py` | **Allow**, **Deny** and answer handling, and its error texts (5.18, 10.3) | No |

## 14. Open Questions

Nothing below could be established from the repository. Items are grouped by who can answer them, and each
names what to look up; numbers in parentheses are the sections where the gap matters. Every **TO BE CONFIRMED** item, every
Security-sensitive referral and every unknown stated in sections 1 to 13 is listed here.

### 14.1 Live Data and Settings

Answered by an admin, or by whoever can read the production `config` table, user records and model records.
All of these are data, not code: **TO BE CONFIRMED** for production.

1. **Feature switches:** the live values of `web.search.enable`, `image_generation.enable`, `code_interpreter.enable`, `code_execution.enable`, `chat.tool_permissions.enable`, `chat.context_compaction.enable`, `task.autocomplete.enable`, `notes.enable`, `google_drive.enable` and `onedrive.enable`, which decide what the **+** and **Integrations** menus offer (3.2, 7.1).
2. **Engines:** the live `code_execution.engine` and `code_interpreter.engine` (`pyodide` in the browser, or Jupyter on a server), `audio.stt.engine` (`web` blocks **Voice mode**) and `audio.tts.split_on` (how **Read Aloud** splits text), which decide where **Run** executes, whether the side panel has a **Files** tab and which voice errors users can meet (5.15, 5.20, 7.1, 10.2).
3. **Web search confirmation:** the live `web.search.confirmation.enable` and `web.search.confirmation.content`, that is, whether **Use Web Search?** appears and with what wording (5.7, 11.16).
4. **Upload limits:** the live `rag.file.max_count`, `rag.file.max_size`, `file.image_compression_width` and `file.image_compression_height`, the numbers behind the file-count and file-size errors (5.6, 11.13).
5. **What a new chat shows:** the live `ui.default_models`, `ui.prompt_suggestions` (whether the six upstream example cards such as "Help me study" still appear) and any admin banners (5.1, 7.1).
6. **Rating and copying:** the live `ui.enable_message_rating`, `ui.enable_community_sharing` (whether the feedback form links to openwebui.com) and `ui.watermark` (text added to every copied answer) (5.12, 7.1).
7. **Admin defaults for interface settings:** the live `ui.default_interface_settings` JSON, in particular whether it presets **Hide Processing Details**, **Inline Citations**, **Enable Message Queue** or **Enter Key Behavior** for everyone (a preset switch shows the `Default` label) (6.5, 7.3, 11.8).
8. **One account's own interface settings:** these are stored per account in the user's settings under `ui` (for example `hideProcessingDetails`, `showInlineCitations`, `ctrlEnterToSend`, `enableMessageQueue`); support learns them by asking the user to read each switch, and who may look them up on request is TO BE CONFIRMED (6.5, 11.1, 11.8, 11.10).
9. **Permissions in force:** the live `user.permissions` defaults and each group's grants for the section 3.1 keys, in particular `chat.temporary_enforced`, `features.direct_tool_servers` and `chat.file_upload`, and whether the default for `settings.interface` was turned off, which would stop users without a granting group from changing the fork's switches (3.1, 11.13, 11.22).
10. **What each production model supports:** per model, the `vision`, `file_upload`, `web_search`, `image_generation`, `code_interpreter`, `citations`, `status_updates` and `terminal` capabilities; default tools (and which of them need a sign-in), skills, filters and features; action buttons; user valves; chat variables; prompt suggestions; and which models are arena models (3.2, 7.2, 11.14, 11.15).

### 14.2 Deployment

Answered by the platform maintainer.

11. **Production address:** the host name of MedIT GPT; this document writes every URL relative to the site root (2).
12. **Which build is live:** which commit of `uoft` production runs, and whether it includes the uncommitted working-tree changes of 2026-10-07 (12.2), which change when `Thinking...` shows after a tool approval, how tool cards group while details are hidden, the **Hide Processing Details** description and how the interface language is chosen.
13. **Environment-only values:** `WEBUI_NAME` (code default `MedIT GPT`; shown in the browser tab title and in the site name and version line shown when there are no suggestions), `IFRAME_CSP` (`backend/open_webui/config.py:1731`) and `ENABLE_ADMIN_CHAT_ACCESS` (`backend/open_webui/env.py:371`; whether admins can open users' chats, which they then see read-only) (1, 2, 5.1, 5.15).
14. **Licence metadata:** whether production loads licence metadata, which reaches the browser through `/api/config` (`backend/open_webui/main.py:2254`, `:2439`); without it the code shows neither the `Trial License` and `License Error` banners nor the composer footer line (5.3, 10.1).
15. **Network reach of users' browsers:** whether browsers on the networks people work from can reach Google's favicon service (`www.google.com/s2/favicons`) and the sites whose images and embeds appear in answers; if not, site icons and embedded media do not load (5.15, 5.16).

### 14.3 Product Behaviour

Answered by the platform maintainer for the fork, by upstream Open WebUI, or by a run in a test environment.

16. **Version choice saved late:** in a single-model chat, switching versions with the arrows is saved only at the next save, so a reload can show the earlier version (`src/lib/components/chat/Messages.svelte:199-307`; 5.13, 11.20); whether to save it at once, as clicking in the **Overview** does, is for the maintainer.
17. **Bracketed numbers removed:** with **Inline Citations** off, every `[number]` outside code is removed whether or not it is a citation, while **Copy** keeps the markers (`src/lib/components/chat/Messages/ContentRenderer.svelte:133-138`; 5.23, 11.11); whether the fork should narrow the pattern or make **Copy** follow the switch is for the maintainer.
18. **`Parent message not found`:** shown when Regenerate finds no question above the answer (`src/lib/components/chat/Chat.svelte:3846-3851`); how a stored chat tree loses a parent is not established, so the maintainer needs the chat id to inspect its stored history (10.1).
19. **Unreachable Google Drive upload path:** `uploadGoogleDriveFile` (`src/lib/components/chat/Chat.svelte:1663`) runs only for an upload event of type `google-drive` (`:1889-1890`), which no component under `src/` sends; if `File uploaded successfully` or `Error uploading file: {error}` is reported from the chat screen, the maintainer should trace what produced it (10.1).
20. **`Waiting for upload...` tooltip:** it appears only when a parent sets `uploadPending` on the composer (`src/lib/components/chat/MessageInput.svelte:148`, `:2736-2739`), and no component under `src/` sets it; whether this is leftover upstream code is for upstream (10.2).
21. **`Cannot create an empty note.`:** it belongs to a `createNote` function in the composer that nothing calls in this version (`src/lib/components/chat/MessageInput.svelte:1199-1203`); whether upstream plans to expose it is unknown (10.2).
22. **Unused and empty files:** `src/lib/components/chat/MessageInput/Commands/Models.svelte`, `src/lib/components/chat/MessageInput/Commands/Prompts.svelte`, `src/lib/components/chat/Messages/Citations/CitationsModal.svelte` and `src/lib/components/common/RichTextInput/commands.ts` are not imported by any file under `src/`, and `src/lib/components/chat/Placeholder/FolderKnowledge.svelte` and `src/routes/(app)/home/+page.svelte` are empty (13); whether they are leftovers or unfinished features is for upstream.
23. **The `/home` stub:** nothing in the front end links to `/home`, and its **Notes** link points to `/playground/notes`, which does not exist in this version (`src/routes/(app)/home/+layout.svelte:17-73`); whether upstream will finish the page, and whether any bookmark sends users there, is unknown (2).
24. **Behaviour read from the code, not observed:** the research rules forbid starting the application, so a test run should confirm that `Thinking...`, the blinking bar and **Stop** return while an approved tool runs (working tree only, 5.22), that queued messages go out as one combined message (5.9), that a message delete the server refuses disappears without an error until a reload (11.21), that a cut-off answer is marked finished on reopening without an error (5.21), and that switching **Inline Citations** changes answers already on screen (5.23).

### 14.4 People and Process

Answered by the people responsible for the MedIT GPT service.

25. **Support contact:** the support mailbox, queue and hours for MedIT GPT; none exists in the repository (11).
26. **Escalation roles:** who "the platform maintainer", "the model administrators" (and model owners) and "the user's administrator" named in section 11 are, how tier 1 reaches each, and who approves requests for a permission or a model change (3.1, 11).
27. **Tier 1's own access:** whether tier 1 can see admin settings, the server log or a user's chat, or must ask an admin each time; the support checks in sections 10 and 11 assume someone with that access (10, 11).
28. **Feedback data:** who reviews thumbs ratings and their feedback rows, each of which holds a snapshot of the whole conversation, and how long they are kept (6.2).
29. **Upstream community links:** whether users should be sent to openwebui.com from the feedback form (`Leave a public review for {modelName}`), or to the upstream community at all; the ground truth leaves this TO BE CONFIRMED (5.12).
30. **Licence notices:** who handles licence matters if a `Trial License` or `License Error` banner appears, since its text tells users to contact support without saying whom (10.1).

### 14.5 Security-Sensitive Items

Deliberately not described in this document; answered by the platform maintainer with U of T Information
Security.

31. Whether every permission key in section 3.1 is enforced by the server as well as by the screen (3.1). Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca).
32. What plugins may run in the user's page through `execute` events (9). Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca).
