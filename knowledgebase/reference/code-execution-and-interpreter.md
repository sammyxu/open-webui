# Code Execution and Code Interpreter

## At a Glance

- **Two features.** **Code execution** is the **Run** button on a Python code block (in a reply or
  the person's own message): the person runs code that is already on screen and only they see the
  output, which is not saved. The **code interpreter** is a composer switch: the model writes
  Python during its reply, the platform runs it, and the model reads the output and continues; code
  and output are saved with the reply.
- **Two engines per feature**, set separately in Admin Settings › **Code Execution**
  (`/admin/settings/code-execution`): `pyodide` (the default; Python 3.14 in WebAssembly, running
  inside the person's browser tab) or `jupyter` (a Jupyter server the administrator configures,
  reached from the MedIT GPT server; labelled `jupyter (Legacy)`). Both switches are on in the code
  defaults; live values are **TO BE CONFIRMED**.
- **Who can use what.** The **Run** button has no per-user permission, only the admin switch. The
  code interpreter needs the admin switch, the `features.code_interpreter` permission (default on),
  a model that allows it, and no terminal selected; the server re-checks all of this.
- **Native versus legacy.** By default the code interpreter is the `execute_code` tool (see
  `builtin-native-tools.md`); in legacy Function Calling mode the model writes
  `<code_interpreter>` tags, shown as `Analyzing...`/`Analyzed`, and at most five blocks run per
  reply.
- **Limits and failures.** In the browser every run stops at 60 seconds
  (`Execution Time Limit Exceeded`); on Jupyter the **Code Execution Timeout** (default 60 seconds)
  applies to each wait for output (`Execution timed out.`). With the browser engine the code
  interpreter needs the chat tab to stay open (`Client session disconnected.`). Only the bundled
  packages in section 5.8 install automatically.
- **Files.** In-browser code reads chat attachments from `/mnt/uploads/` and writes files there,
  visible in the side panel's **Files** tab; they live in the browser only (kept between page loads
  only when `ENABLE_PYODIDE_FILE_PERSISTENCE` is on). Printed charts become saved pictures
  (`Output Image`) for the code interpreter. Files written on a Jupyter server are not brought back.
- **Privacy.** The `pyodide` engine keeps code and files in the browser; the `jupyter` engine sends
  the code, which may contain chat data, to the Jupyter server. The fork's **Hide Processing
  Details** setting hides code analysis and `execute_code` output, charts included (section 12).

## 1. Purpose and Who Uses It

MedIT GPT can run Python code in two different ways. Support staff need to tell them apart, because
they have separate switches, separate engines and different failure messages.

| | **Code execution** | **Code interpreter** |
|---|---|---|
| What the person does | Clicks **Run** on a Python code block that is already on screen (in a reply, or in their own message) | Turns on **Code Interpreter** in the chat composer before sending; the model then decides to write and run code while it answers |
| Who writes the code | Whoever wrote the message; the person can edit the block before running it | The model, during the reply |
| Who sees the output | Only the person who clicked, under the block; the output is not saved with the chat (section 6) | The model reads the output and continues its answer; the code and output are saved in the reply |
| Admin switch | **Enable Code Execution** (`code_execution.enable`) | **Enable Code Interpreter** (`code_interpreter.enable`) |
| Per-user permission | None found in code (section 3) | `features.code_interpreter` |
| Engine setting | **Code Execution Engine** (`code_execution.engine`) | **Code Interpreter Engine** (`code_interpreter.engine`) |
| Where the code runs with the default engine (`pyodide`) | In an in-browser sandbox in the person's own browser tab (section 4) | Also in the person's browser: the server asks the open chat tab to run it and waits for the answer |
| Where the code runs with the `jupyter` engine | On the Jupyter server the administrator configured, called by the MedIT GPT server | Same, with the code interpreter's own Jupyter settings |

Evidence: the Run button and its two engine paths are in
`src/lib/components/chat/Messages/CodeBlock.svelte:141-220`, `:498-519`; the server endpoint for the
Jupyter path is `backend/open_webui/routers/utils.py:41-71`; the code interpreter is wired in
`backend/open_webui/utils/middleware.py:2722-2751` (prompt), `:4872-4891` (gates) and
`:6348-6536` (the run loop), and as the `execute_code` tool in
`backend/open_webui/tools/builtin.py:633-792`; the settings are in
`backend/open_webui/config.py:405-496`.

**Who uses it.**

- **Students, staff and faculty using chat** see the **Run** button on Python code blocks and, when
  allowed, the **Code Interpreter** switch in the composer. Typical uses are calculations, quick data
  analysis of an uploaded spreadsheet and charts.
- **Administrators** configure both features in Admin Settings › **Code Execution** (section 7) and
  grant or withhold the code interpreter through permissions (section 3).
- **Tier-1 support** explains what the person sees, works out which of the two features is involved
  and which engine is configured, and escalates engine or permission problems.

**Two code interpreter modes.** Which mechanism the code interpreter uses depends on the chat's
**Function Calling** parameter, whose default is `native` (`backend/open_webui/main.py:1290-1294`):

- **Native** (the default): the model is given a tool called `execute_code` and calls it like any
  other built-in tool. That tool is documented in `builtin-native-tools.md` (row 8 and its sections
  on images and messages); this document covers what is specific to code.
- **Legacy**: the server adds an instruction to the person's message telling the model to wrap code in
  `<code_interpreter type="code" lang="python">` tags; the server watches the reply for those tags,
  stops the stream, runs the code, appends the output and asks the model to continue
  (`backend/open_webui/utils/middleware.py:2725-2738`, `:5677-5687`, `:6348-6536`).

**Privacy in one sentence.** With the `pyodide` engine the code, and any files it reads, stay in the
person's browser; with the `jupyter` engine the code (which can contain data pasted into the chat)
is sent by the MedIT GPT server to the Jupyter server the administrator configured
(`backend/open_webui/utils/code_interpreter.py:119-153`). Which engine production uses, and where
any Jupyter server is hosted, are **TO BE CONFIRMED** (section 14).

## 2. Navigation and URLs

URLs are relative to the site root; the production host name is **TO BE CONFIRMED**.

### 2.1 Where People Meet the Features

| What | Where | Visible text | Source |
|---|---|---|---|
| **Run** button | Top bar of a fenced code block whose language is `python` or `py` (any capitalization), or has no language but looks like Python, in a reply or in the person's own message (`/c/{id}`) | `Run`; while running `Running` (not clickable) and `Running...` in the output area | `src/lib/components/chat/Messages/CodeBlock.svelte:498-519`, `:610-614`; `src/lib/components/chat/Messages/UserMessage.svelte:393-399` |
| Output of a run | Under the code block | Headings `STDOUT/STDERR` and `RESULT`; charts as pictures | `src/lib/components/chat/Messages/CodeBlock.svelte:606-647` |
| **Code Interpreter** switch | Composer › **Integrations** button (tooltip `Integrations`) › `Code Interpreter` with a switch; tooltip `Execute code for analysis` | `Code Interpreter` | `src/lib/components/chat/MessageInput.svelte:2302-2345`; `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:304`, `:497-521` |
| Code Interpreter pill | Shown in the composer while the switch is on; clicking it turns the feature off | Tooltip `Code Interpreter`; screen-reader name `Disable Code Interpreter` | `src/lib/components/chat/MessageInput.svelte:2520-2545` |
| Turning it on from a link | Adding `?code-interpreter=true` to a new-chat URL switches it on (the server still checks the switch and permission, section 3) | none | `src/lib/components/chat/Chat.svelte:2180-2182`, `:3404-3408` |
| Code interpreter blocks in a reply (legacy mode) | Inside the reply, a collapsible line | `Analyzing...` while running, `Analyzed` when done; several details in a row are folded into one line, `Exploring` or `Explored` followed by `Ran {{COUNT}} analysis` or `Ran {{COUNT}} analyses` | `src/lib/components/common/Collapsible.svelte:114-119`; `src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte:165-177` |
| `execute_code` calls in a reply (native mode) | A tool-call entry, as for every built-in tool | See `builtin-native-tools.md` and `chat-composer-and-message-display.md` | `src/lib/components/common/ToolCallDisplay.svelte` |
| In-browser file browser | Side panel (top-bar **Controls** button) › **Files** tab; shown while the Code Interpreter is on and the code interpreter engine is not `jupyter` | Region name `Pyodide file browser` | `src/lib/components/chat/ChatControls.svelte:83-85`, `:238-247`, `:297-298`; `src/lib/components/chat/PyodideFileNav.svelte:358-365` |
| Code execution chips | Under a reply, when an add-on reports a code execution (section 4) | Modal title `Code execution: {name}` | `src/lib/components/chat/Messages/ResponseMessage.svelte:944-946`; `src/lib/components/chat/Messages/CodeExecutionModal.svelte:37-42` |

The side panel itself is described in `chat-composer-and-message-display.md` (section 5.20).

### 2.2 Administrator Pages

| Page | URL | Notes | Source |
|---|---|---|---|
| Admin Settings › **Code Execution** | `/admin/settings/code-execution`, which opens the settings window at `/?settings=admin:code-execution` | Listed under the **Tools** group of the admin tabs; window heading `Code Execution` | `src/routes/(app)/admin/settings/[tab]/+page.svelte:6-10`; `src/lib/components/chat/SettingsModal.svelte:168`, `:346-351`, `:877-878`; `src/lib/components/admin/Settings/CodeExecution.svelte:46-48` |
| Default permissions and group permissions | Admin › Users › Groups (`/admin/users/groups`); **Default permissions** or a group › **Code Interpreter** switch | Covered in `users-groups-roles-and-permissions.md` | `src/lib/components/admin/Users/Groups.svelte:220`; `src/lib/components/admin/Users/Groups/Permissions.svelte:1080-1096` |
| Per-model controls | Workspace › Models › edit a model: **Capabilities**, **Builtin Tools** and **Default Features** each have a `Code Interpreter` entry | Covered in `workspace-models-and-model-access.md` | `src/lib/components/workspace/Models/Capabilities.svelte:33-35`; `src/lib/components/workspace/Models/BuiltinTools.svelte:57-59`; `src/lib/components/workspace/Models/DefaultFeatures.svelte:21-23` |

### 2.3 API Endpoints and Channels in Scope

| Method and path | Who may call | Purpose | Source |
|---|---|---|---|
| `GET /api/v1/configs/code_execution` | Admins | Reads the fifteen Code Execution settings | `backend/open_webui/routers/configs.py:704-706` |
| `POST /api/v1/configs/code_execution` | Admins | Saves them | `backend/open_webui/routers/configs.py:709-728` |
| `POST /api/v1/utils/code/execute` | Any signed-in user (role `user` or `admin`) | Runs one code block on the Jupyter engine for the **Run** button | `backend/open_webui/routers/utils.py:41-71` |
| `POST /api/v1/utils/code/format` | Admins | Formats Python code with Black for the code editor (section 5.6) | `backend/open_webui/routers/utils.py:30-38` |
| `GET /api/config` | Signed-in users | Tells the browser whether each feature is on and which engine each uses (`features.enable_code_execution`, `features.enable_code_interpreter`, `features.enable_pyodide_file_persistence`, `code.engine`, `code.interpreter_engine`) | `backend/open_webui/main.py:2348`, `:2365-2366`, `:2399-2402` |
| `/pyodide/` (static files) | The browser | The in-browser Python runtime and its bundled packages, served from the built front end | `src/lib/workers/pyodide.worker.ts:27-28`; `src/lib/pyodide/pyodideSandboxHost.ts:191-194` |
| Socket.IO request `execute:python` | Server to the person's browser tab | Asks the tab that sent the message to run code-interpreter code in the browser and return the output | `backend/open_webui/utils/middleware.py:6395-6405`; `backend/open_webui/tools/builtin.py:696-706`; `src/routes/+layout.svelte:634-641` |
| `GET /api/v1/files/{id}/content` | The browser | Fetches files attached to the chat so in-browser code can read them; also the address of pictures saved from code output | `src/routes/+layout.svelte:321-338`; `backend/open_webui/routers/images.py:553` |

## 3. Roles and Permissions

Roles are `admin`, `user` and `pending` (`knowledgebase/tools/ground-truth.md`); `pending` accounts
cannot use chat at all, so neither feature applies to them.

### 3.1 Who Can Do What

| Action | `admin` | `user` | Checked by | Source |
|---|---|---|---|---|
| See and click **Run** on a Python block | Yes, when **Enable Code Execution** is on | Same; there is no per-user permission for code execution | The browser hides the button when `features.enable_code_execution` is false (and shows it if the value is missing) | `src/lib/components/chat/Messages/CodeBlock.svelte:498` |
| Run a block on the Jupyter engine | Yes | Yes | The server refuses when the switch is off; any signed-in role `user` or `admin` passes | `backend/open_webui/routers/utils.py:41-47` |
| See the **Code Interpreter** switch in the composer | Yes, when **Enable Code Interpreter** is on | Only with the `features.code_interpreter` permission | The browser; it also needs every selected model to allow the capability and no terminal to be selected | `src/lib/components/chat/MessageInput.svelte:836-846` |
| Have code-interpreter code actually run (native mode, `execute_code`) | Yes | With the permission | The server, five checks (below) | `backend/open_webui/utils/tools.py:706-715` |
| Have code-interpreter code actually run (legacy mode, `<code_interpreter>` tags) | Yes | With the permission | The server, the same checks | `backend/open_webui/utils/middleware.py:4872-4891` |
| Open or save Admin Settings › Code Execution | Yes | No | Admin-only endpoints | `backend/open_webui/routers/configs.py:704-712` |
| Format Python in a code editor with **Ctrl+Shift+F** | On the server | In the browser (Pyodide) | Admin-only format endpoint; others use the in-browser runtime | `backend/open_webui/routers/utils.py:30-38`; `src/lib/components/common/CodeEditor.svelte:181-187` |

**The five server checks for the code interpreter** (all must pass; admins skip only the last):

1. The model's **Builtin Tools** › `Code Interpreter` entry is not switched off (`meta.builtinTools.code_interpreter`, default on).
2. **Enable Code Interpreter** is on (`code_interpreter.enable`).
3. The model's **Capabilities** › `Code Interpreter` is not switched off (`meta.capabilities.code_interpreter`, default on).
4. The chat request asked for the code interpreter (the composer switch was on).
5. The person is an admin or has `features.code_interpreter`.

Evidence: `backend/open_webui/utils/tools.py:532-540`, `:559-566`, `:706-715`;
`backend/open_webui/utils/middleware.py:4874-4891`.

### 3.2 The Permission

| Permission | Code default | Environment variable | Admin control | Source |
|---|---|---|---|---|
| `features.code_interpreter` | on | `USER_PERMISSIONS_FEATURES_CODE_INTERPRETER` (`True`) | Admin › Users › Groups › **Default permissions** or a group › `Code Interpreter` | `backend/open_webui/config.py:1914-1916`, `:2011`; `backend/open_webui/routers/users.py:268`; `src/lib/components/admin/Users/Groups/Permissions.svelte:1080-1096` |

Permissions add up across groups and a group cannot take away a permission the defaults grant; in
that case the group screen shows `This is a default user permission and will remain enabled.`
(`src/lib/components/admin/Users/Groups/Permissions.svelte:1090-1095`; ground truth). The live
default permissions are data in the `user.permissions` setting: **TO BE CONFIRMED**.

### 3.3 What People See When Something Is Off

| Situation | What the person sees | Source |
|---|---|---|
| **Enable Code Execution** off | No **Run** button on any code block, for anyone | `src/lib/components/chat/Messages/CodeBlock.svelte:498` |
| **Enable Code Interpreter** off, or no `features.code_interpreter` permission | No `Code Interpreter` entry in the Integrations menu and no pill; a model's default feature does not switch it on; a `?code-interpreter=true` link is ignored when sending | `src/lib/components/chat/MessageInput.svelte:836-841`; `src/lib/components/chat/Chat.svelte:1100-1106`, `:3404-3408` |
| One of the selected models has the capability off | No `Code Interpreter` entry while that model is selected | `src/lib/components/chat/MessageInput.svelte:759-763`, `:789-794`, `:839` |
| A terminal is selected | No `Code Interpreter` entry; selecting a terminal switches it off (they are mutually exclusive) | `src/lib/components/chat/MessageInput.svelte:838`, `:843-846` |
| The admin changed a switch while the person had MedIT GPT open | The person's page keeps the old state until it next loads the configuration (page reload or sign-in); the server applies the new state at once | `src/routes/+layout.svelte:1267-1291`; `backend/open_webui/routers/utils.py:43-47`; `backend/open_webui/utils/middleware.py:4881` |
| Code execution switched off after the page loaded, Jupyter engine | Clicking **Run** shows a red toast `Code execution is disabled` | `backend/open_webui/routers/utils.py:43-47`; `backend/open_webui/constants.py:125`; `src/lib/components/chat/Messages/CodeBlock.svelte:149-152` |

The code interpreter's model-level controls (Capabilities, Builtin Tools, Default Features) are
described in `workspace-models-and-model-access.md`; group and default permissions in
`users-groups-roles-and-permissions.md`.

### 3.4 Where the Code Interpreter Is Not Available

- **Automations.** A model's default features are applied to scheduled runs for web search and image
  generation only; the code comment says the code interpreter "requires the frontend event emitter
  and does not work in headless backend execution" (`backend/open_webui/utils/automations.py:184-189`).
- **Background sub-agents.** When a sub-agent runs in the background, the code interpreter is
  removed from its features unless the code interpreter engine is `jupyter`
  (`backend/open_webui/utils/subagents.py:310-316`).
- **Anything without the person's open browser tab** on the `pyodide` engine, because the browser
  runs the code (sections 4 and 11).

## 4. Key Concepts and Terminology

| Term | Meaning in MedIT GPT | Source |
|---|---|---|
| **Code execution** | Running a code block that is already on screen with its **Run** button. The person sees the output; the model does not. | `src/lib/components/chat/Messages/CodeBlock.svelte:141-220` |
| **Code interpreter** | A chat feature the person switches on; the model may then write Python, have it run, read the output and continue its answer. | `backend/open_webui/config.py:466-496`; `backend/open_webui/utils/middleware.py:6348-6536` |
| **Engine** | Where code runs. Each feature has its own engine setting with two choices, `pyodide` and `jupyter`; the admin list labels the second `jupyter (Legacy)`. | `src/lib/components/admin/Settings/CodeExecution.svelte:20`, `:79-81`, `:193-195` |
| **Pyodide** | Python compiled to WebAssembly so it runs inside a web page. This build uses Pyodide `314.0.3`, which provides Python `3.14.0`. | `package.json:137`; `static/pyodide/pyodide-lock.json` (`info.python`) |
| **In-browser sandbox** | The Pyodide runtime started for a browser tab. By default it is a hidden, isolated frame inside the page; when the environment setting `ENABLE_PYODIDE_FILE_PERSISTENCE` is on it is a background worker whose files are kept in the browser's storage (section 6). | `src/lib/pyodide/createPyodideWorker.ts:7-10`; `src/lib/pyodide/pyodideSandboxHost.ts:196-248`; `src/lib/workers/pyodide.worker.ts:49-63`; `backend/open_webui/env.py:1211` |
| **Shared sandbox** | One in-browser sandbox per tab, created by the first code-interpreter run or by opening the **Files** tab. A **Run** click uses it when it exists, so files and variables are shared; otherwise each click starts a new, separate runtime. | `src/routes/+layout.svelte:282-293`; `src/lib/components/chat/PyodideFileNav.svelte:100-107`; `src/lib/components/chat/Messages/CodeBlock.svelte:243-252` |
| **Jupyter** | A separate Jupyter server, run and secured by whoever hosts it, that MedIT GPT's server sends code to. Each run starts a fresh kernel (a Python process on that server) and shuts it down afterwards, so variables do not carry over between runs. | `backend/open_webui/utils/code_interpreter.py:57-77`, `:101-105` |
| **Native and legacy modes** | The chat's **Function Calling** parameter. Native (default): the code interpreter is the `execute_code` tool. Legacy: the model writes `<code_interpreter>` tags that the server runs. | `backend/open_webui/main.py:1290-1294`; `backend/open_webui/utils/middleware.py:2725-2751`, `:4872-4891` |
| **Code interpreter prompt** | The instructions the server adds in legacy mode, telling the model how to write runnable code. Admins can replace them (**Code Interpreter Prompt Template**). A second block about the in-browser environment is added for the `pyodide` engine in both modes. | `backend/open_webui/config.py:466-496`; `backend/open_webui/utils/middleware.py:2728-2751` |
| **stdout, stderr, result** | What a run returns: printed text, error text, and the value of the last expression. The Run button shows the first two under `STDOUT/STDERR` and the last under `RESULT`. | `backend/open_webui/utils/code_interpreter.py:15-22`; `src/lib/components/chat/Messages/CodeBlock.svelte:616-644` |
| **Output Image** | A chart printed by code is turned into a picture. For the code interpreter the server saves it as a file and puts a Markdown picture labelled `Output Image`, pointing at that file, in the output; for the Run button the picture is shown straight from the run and not saved. | `backend/open_webui/utils/middleware.py:6432-6463`; `backend/open_webui/tools/builtin.py:744-780`; `src/lib/components/chat/Messages/CodeBlock.svelte:154-211`, `:634-641` |
| **`/mnt/uploads`** | The folder inside the in-browser sandbox where files attached to the chat are placed for the code interpreter and where code may write files; the **Files** tab opens there. | `backend/open_webui/config.py:491-496`; `src/routes/+layout.svelte:321-346`; `src/lib/workers/pyodide.worker.ts:111-121`; `src/lib/components/chat/PyodideFileNav.svelte:1-3` |
| **Blocked modules** | Python modules an administrator lists in `CODE_INTERPRETER_BLOCKED_MODULES`; code-interpreter code that imports one directly stops with `Direct import of module {name} is restricted.` | `backend/open_webui/config.py:462-464`; `backend/open_webui/utils/middleware.py:6373-6391`; `backend/open_webui/tools/builtin.py:660-686` |
| **Time limit** | In the browser, 60 seconds per run, after which the output shows `Execution Time Limit Exceeded`. On Jupyter, the **Code Execution Timeout** setting (default 60 seconds), after which `Execution timed out.` is added to the error text. | `src/lib/components/chat/Messages/CodeBlock.svelte:260-269`; `src/routes/+layout.svelte:348-373`; `backend/open_webui/utils/code_interpreter.py:156-186` |
| **Code execution chips** | Small buttons under a reply listing code runs reported by an add-on (a function, tool or pipe) through an event whose data type is `code_execution`. Nothing in the core application sends these. Clicking one opens a window with the code and its `ERROR`, `OUTPUT` and `Files`. | `src/lib/components/chat/Chat.svelte:1328-1345`; `src/lib/components/chat/Messages/CodeExecutions.svelte:28-63`; `src/lib/components/chat/Messages/CodeExecutionModal.svelte:14-109` |
| **Retries (legacy)** | The server runs at most five code blocks per reply in legacy mode. | `backend/open_webui/utils/middleware.py:6348-6352` |

## 5. Workflows (Step by Step)

### 5.1 Running a Code Block with the Browser Engine (`pyodide`, the Default)

1. The person clicks **Run** on a Python block. Any edits they typed into the block are what runs;
   the edits are not saved to the message by running (`src/lib/components/chat/Messages/CodeBlock.svelte:505-512`).
2. The browser reads the engine from the configuration it loaded (`code.engine`). For anything
   other than `jupyter` it runs the code in the browser (`src/lib/components/chat/Messages/CodeBlock.svelte:148`, `:217-219`).
3. The browser looks for imports it knows how to install (table in 5.8) and starts or reuses an
   in-browser sandbox. If the tab already has the shared sandbox (the code interpreter or the
   **Files** tab created it), that one is used; otherwise a new runtime is started for this click
   (`src/lib/components/chat/Messages/CodeBlock.svelte:222-258`).
4. A 60-second timer starts as the code is handed over. The first run in a sandbox also has to load
   the Python runtime from `/pyodide/` and install the detected packages, and that time counts
   against the 60 seconds (`src/lib/components/chat/Messages/CodeBlock.svelte:254-269`;
   `src/lib/workers/pyodide.worker.ts:242-258`; `src/lib/pyodide/pyodideSandboxHost.ts:145-153`).
5. If the code mentions `matplotlib`, the sandbox replaces `plt.show()` so that each chart is
   printed as a PNG picture instead of opening a window (`src/lib/workers/pyodide.worker.ts:193-220`;
   `src/lib/pyodide/pyodideSandboxHost.ts:109-129`, `:137`).
6. The output appears under the block: printed text and errors under `STDOUT/STDERR`, the value of
   the last line under `RESULT`, and charts as pictures (alternative text `Output`). Very long
   printed output (over 100 lines) gets its own scroll area
   (`src/lib/components/chat/Messages/CodeBlock.svelte:271-347`, `:606-647`).
7. After the run the **Files** tab, if open, refreshes itself (`src/lib/components/chat/Messages/CodeBlock.svelte:345-346`;
   `src/lib/components/chat/PyodideFileNav.svelte:333-344`).
8. If 60 seconds pass first, the output shows `Execution Time Limit Exceeded`; a runtime started
   just for this click is stopped, the shared sandbox is left running
   (`src/lib/components/chat/Messages/CodeBlock.svelte:260-269`).

The output stays on screen only; it is not written to the chat (section 6).

### 5.2 Running a Code Block with the Server Engine (`jupyter`)

1. The browser sends the block's code to `POST /api/v1/utils/code/execute`
   (`src/lib/components/chat/Messages/CodeBlock.svelte:148-152`; `src/lib/apis/utils/index.ts:30-62`).
2. The server refuses with `Code execution is disabled` when **Enable Code Execution** is off, and
   with `[ERROR: Code execution engine not supported]` when the saved engine is not `jupyter`
   (`backend/open_webui/routers/utils.py:43-71`; `backend/open_webui/constants.py:16-23`, `:125`).
3. The server connects to the **Jupyter URL**, signs in with the chosen authentication type
   (`None`, `Token` or `Password`), starts a new kernel, sends the code and collects printed text,
   errors (with their traceback), PNG pictures and text results until the kernel reports it is idle
   (`backend/open_webui/utils/code_interpreter.py:69-189`).
4. If no message arrives from the kernel within the **Code Execution Timeout** (default 60 seconds),
   the server stops waiting and adds `Execution timed out.` to the error text
   (`backend/open_webui/utils/code_interpreter.py:156-186`). The limit applies to each wait for the
   kernel's next message, so code that keeps printing can run longer than the number shown.
5. The kernel is shut down after every run, whatever the outcome
   (`backend/open_webui/utils/code_interpreter.py:60-67`).
6. A connection or sign-in failure does not raise an error to the browser; it comes back as error
   text beginning `Error: ` and is shown under `STDOUT/STDERR`
   (`backend/open_webui/utils/code_interpreter.py:69-77`). An empty **Jupyter URL** is the
   exception (section 11.6). A refused request (step 2) appears as a
   red toast (`src/lib/components/chat/Messages/CodeBlock.svelte:149-152`).

### 5.3 The Code Interpreter in Native Mode (the Default)

1. The person switches on **Code Interpreter** (section 2.1) and sends a message. The browser sends
   `code_interpreter: true` only when the admin switch and the permission allow it
   (`src/lib/components/chat/Chat.svelte:3394-3410`).
2. For the `pyodide` engine the server appends a short description of the in-browser environment
   (no package installs, files in `/mnt/uploads`) to the system message
   (`backend/open_webui/utils/middleware.py:2739-2751`; `backend/open_webui/config.py:484-496`).
3. If the five checks in section 3.1 pass, the model is offered the `execute_code` tool
   (`backend/open_webui/utils/tools.py:706-715`).
4. When the model calls it, the server cleans the code (removes terminal colour codes and Markdown
   code fences) and, when blocked modules are configured, adds the import restriction
   (`backend/open_webui/tools/builtin.py:656-686`; `backend/open_webui/utils/sanitize.py:44-57`).
5. **`pyodide` engine:** the server asks the browser tab that sent the message to run the code,
   passing the files attached to the chat. The tab downloads each attached file, places it in
   `/mnt/uploads/` under its file name, runs the code in the shared sandbox with the same
   60-second limit, and returns the output (`backend/open_webui/tools/builtin.py:688-722`;
   `src/routes/+layout.svelte:295-435`, `:634-641`). The server waits for that answer for as long
   as `WEBSOCKET_EVENT_CALLER_TIMEOUT` allows; the code default is no limit
   (`backend/open_webui/env.py:534-542`; `backend/open_webui/socket/main.py:1258-1281`).
6. **`jupyter` engine:** the server runs the code with the code interpreter's own Jupyter settings,
   as in 5.2 steps 3 to 5; attached files are not sent (`backend/open_webui/tools/builtin.py:724-739`).
7. Each PNG picture in the output is saved as a file linked to the chat message and replaced by
   a Markdown picture labelled `Output Image` that points at the file's `/api/v1/files/{id}/content`
   address (`backend/open_webui/tools/builtin.py:744-780`;
   `backend/open_webui/routers/images.py:520-559`).
8. The model receives `status`, `stdout`, `stderr` and `result` and continues its answer
   (`backend/open_webui/tools/builtin.py:782-789`). The person sees a tool-call entry with the code
   as input and the output; see `builtin-native-tools.md` for that display and the tool's messages.

### 5.4 The Code Interpreter in Legacy Mode

1. With the chat's **Function Calling** set to `legacy`, the server adds the code interpreter prompt
   (the admin's template, or the default) to the person's latest message, plus the in-browser
   environment block for the `pyodide` engine (`backend/open_webui/utils/middleware.py:2722-2738`).
2. The model writes `<code_interpreter type="code" lang="python">` … `</code_interpreter>`. When the
   server sees the opening tag in the stream it starts a code item, shown as `Analyzing...`; at the
   closing tag it stops reading the model's reply (`backend/open_webui/utils/middleware.py:4620-4634`,
   `:4669-4754`, `:5677-5687`; `src/lib/components/common/Collapsible.svelte:114-119`).
3. The server cleans the code, adds the blocked-modules guard if configured, and runs it: in the
   browser for `pyodide`, on Jupyter for `jupyter`; for any other engine value the output is
   `Code interpreter engine not configured.` (`backend/open_webui/utils/middleware.py:6365-6423`).
4. Pictures in the output are saved as files as in 5.3 step 7
   (`backend/open_webui/utils/middleware.py:6432-6463`).
5. The code item is marked complete (`Analyzed`) and the server asks the model to continue, sending
   it the conversation plus the code and **only the printed output, or the result when nothing was
   printed**; error text is not part of what the model is sent
   (`backend/open_webui/utils/middleware.py:6467-6531`; `backend/open_webui/utils/misc.py:546-563`).
6. Steps 2 to 5 repeat while the model ends on a new code block, up to five blocks per reply
   (`backend/open_webui/utils/middleware.py:6348-6352`).
7. The finished reply, including each code block and its output, is saved to the chat
   (`backend/open_webui/utils/middleware.py:6538-6563`).

### 5.5 Working with Files in the In-Browser Sandbox

1. With **Code Interpreter** on and the code interpreter engine not `jupyter`, open the side panel
   (**Controls** in the top bar) and choose **Files** (`src/lib/components/chat/ChatControls.svelte:83-85`).
2. The browser opens at `/mnt/uploads` and lists folders first, then files by name. Opening the tab
   creates the tab's shared sandbox if it does not exist yet
   (`src/lib/components/chat/PyodideFileNav.svelte:1-3`, `:100-107`, `:148-171`, `:340-344`).
3. Toolbar: **Back**, **Forward**, the path as breadcrumbs, **Refresh**, and an **Actions** menu
   with **New Folder**, **New File** and **Upload**; files can also be dropped onto the panel
   (`Drop files here`). Each file row has a menu with **Open**, **Download**, **Copy Path** and
   **Delete** (`src/lib/components/chat/PyodideFileNav.svelte:250-329`, `:351-438`;
   `src/lib/components/chat/FileNav/FileNavToolbar.svelte:142-314`;
   `src/lib/components/chat/FileNav/FileEntryRow.svelte:355-447`).
4. Opening a file shows a preview: text, or a picture for common image types; files that are not
   text show `[Binary file: {entry.size} bytes]` (`src/lib/components/chat/PyodideFileNav.svelte:173-204`).
5. Deleting asks `Are you sure you want to delete this?` under the title `Delete {{name}}`
   (`src/lib/components/chat/PyodideFileNav.svelte:351-356`).
6. Files attached to the chat are copied into `/mnt/uploads/` again before every code-interpreter
   run, so a changed copy of an attached file is replaced by the original at the next run
   (`src/routes/+layout.svelte:321-346`; `src/lib/workers/pyodide.worker.ts:186-190`;
   `src/lib/pyodide/pyodideSandboxHost.ts:131-135`).
7. **Download** on a file saves it from the browser's memory to the person's computer; nothing is
   uploaded to MedIT GPT (`src/lib/components/chat/PyodideFileNav.svelte:214-229`).

Some controls of the shared file browser have no effect here because the Pyodide browser does not
connect them: **Sort**, the **Actions** menu's **Download** and **Show Hidden Files**, **Rename**
on a row, and dragging files between folders (`src/lib/components/chat/PyodideFileNav.svelte:393-417`,
`:504-510`; defaults in `src/lib/components/chat/FileNav/FileNavToolbar.svelte:22-30` and
`src/lib/components/chat/FileNav/FileEntryRow.svelte:24-28`).

### 5.6 Formatting Python in a Code Editor

1. In an editable code block (or the tool and function editors), **Ctrl+Shift+F** (**Cmd+Shift+F**
   on a Mac) formats the code with Black (`src/lib/components/common/CodeEditor.svelte:288-303`).
2. Admins' code is formatted by the server (`POST /api/v1/utils/code/format`); everyone else's in the
   browser, which loads Pyodide and the bundled `black` package
   (`src/lib/components/common/CodeEditor.svelte:97-187`; `backend/open_webui/routers/utils.py:30-38`).
3. Success shows `Code formatted successfully`; a failure shows the error text in a red toast
   (`src/lib/components/common/CodeEditor.svelte:181-201`).
4. Each code editor on the page listens for the shortcut at page level, so on a chat with several
   code blocks the shortcut acts on each of them, whatever their language
   (`src/lib/components/common/CodeEditor.svelte:181-187`, `:289-303`).

### 5.7 Configuring the Features (Administrators)

1. Open Admin Settings › **Code Execution** (`/admin/settings/code-execution`).
2. Section **Code Execution**: **Enable Code Execution**; when on, **Code Execution Engine**; when
   the engine is `jupyter`, **Jupyter URL**, **Jupyter Auth** (`None`, `Token`, `Password`), the
   token or password field, and **Code Execution Timeout**
   (`src/lib/components/admin/Settings/CodeExecution.svelte:52-165`).
3. Section **Code Interpreter**: the same fields for the code interpreter, plus **Code Interpreter
   Prompt Template** (`src/lib/components/admin/Settings/CodeExecution.svelte:167-294`).
4. Choosing `jupyter` replaces the engine description with
   `Warning: Jupyter execution enables arbitrary code execution, posing severe security risks—proceed with extreme caution.`
   (`src/lib/components/admin/Settings/CodeExecution.svelte:67-71`, `:181-185`).
5. **Save** stores all fifteen values at once, publishes the `config.code_execution.updated` event,
   shows `Settings saved successfully!` and reloads the admin's own copy of the configuration
   (`backend/open_webui/routers/configs.py:709-728`; `src/lib/components/chat/SettingsModal.svelte:460-464`).
   Other people pick up the change when their page next loads the configuration (section 3.3).

Blocked modules, the in-browser file persistence switch and the browser wait limit are environment
variables with no control in this panel (section 7).

### 5.8 Packages the Browser Engine Installs Automatically

Before each in-browser run, the browser scans the code for these imports and installs the matching
bundled package; the list is the same for the **Run** button and the code interpreter
(`src/lib/components/chat/Messages/CodeBlock.svelte:223-239`; `src/routes/+layout.svelte:301-317`).

| The code contains | Package installed |
|---|---|
| `import requests` / `from requests` | `requests` |
| `import bs4` / `from bs4` | `beautifulsoup4` |
| `import numpy` / `from numpy` | `numpy` |
| `import pandas` / `from pandas` | `pandas` |
| `import matplotlib` / `from matplotlib` | `matplotlib` |
| `import seaborn` / `from seaborn` | `seaborn` |
| `import sklearn` / `from sklearn` | `scikit-learn` |
| `import scipy` / `from scipy` | `scipy` |
| `import re` / `from re` | `regex` (the standard `re` module itself needs no install) |
| `import sympy` / `from sympy` | `sympy` |
| `import tiktoken` / `from tiktoken` | `tiktoken` |
| `import pytz` / `from pytz` | `pytz` |
| `import openpyxl`, or pandas Excel calls such as `.read_excel(` or `.to_excel(` | `openpyxl` |

The build also bundles `micropip`, `packaging`, `black` and `openai` (`scripts/prepare-pyodide.js:1-38`),
but the browser does not install those automatically from an import (section 11.3). In this
checkout `static/pyodide/` holds 50 wheel files, which include every package the listed packages
depend on according to `static/pyodide/pyodide-lock.json`; what a production build holds is
**TO BE CONFIRMED**. The lock file itself describes 361 packages of the Pyodide distribution, far
more than are bundled; the script's own comment says a package with no bundled wheel "is installed
from PyPI in the user's browser instead" (`scripts/prepare-pyodide.js:210`), which would need the
person's browser to reach the internet. The Python standard library is part of the runtime
(`static/pyodide/` holds `python_stdlib.zip`).

### 5.9 Preparing the In-Browser Runtime (Build Time)

`npm run dev` and `npm run build` first run `scripts/prepare-pyodide.js` (`package.json:6-9`, `:22`).
In a normal build it downloads the Pyodide packages listed at the top of the script and the extra pure-Python wheels
from PyPI into `static/pyodide/`, records them in `static/pyodide/pyodide-lock.json`, and stops the
build with `No wheel bundled for: {missing}` if a listed package has no bundled wheel
(`scripts/prepare-pyodide.js:74-130`, `:145-233`, `:252-257`). With `USE_SLIM=true` (the slim Docker
image) it bundles the runtime only and rewrites the lock file so that each package is fetched from
`https://cdn.jsdelivr.net/pyodide/v{version}/full/` by the person's browser when first needed
(`scripts/prepare-pyodide.js:236-251`; `Dockerfile:29`, `:46`). Proxy settings are taken from
`HTTPS_PROXY`, `ALL_PROXY` or `HTTP_PROXY` (`scripts/prepare-pyodide.js:44-72`). Build details
belong to `developer-tools-scripts-and-tests.md`.

## 6. Data Model

Neither feature has a table of its own. What is kept, and where:

| Data | Where it is kept | How long | Source |
|---|---|---|---|
| The fifteen Code Execution settings | `config` table, one row per dotted key (section 7) | Until changed | `backend/open_webui/routers/configs.py:45-60`, `:713`; `backend/open_webui/models/config.py:198-220` |
| Output of a **Run** click (any engine) | Only on screen, in the code block's memory | Lost when the block is redrawn or the page reloads; not written to the chat | `src/lib/components/chat/Messages/CodeBlock.svelte:67-73`, `:141-357` |
| Code-interpreter code and output, legacy mode | The reply's `output` list, item type `open_webui:code_interpreter`, with `code`, `lang`, `attributes`, `status`, `output` (`stdout`, `stderr`, `result`), `started_at`, `ended_at`, `duration`. Saved in the chat's history (`chat` table) and copied to `chat_message.output` | With the chat | `backend/open_webui/utils/middleware.py:4620-4634`, `:4714-4717`, `:6467-6468`, `:6552-6563`; `backend/open_webui/models/chats.py:1141-1192`; `backend/open_webui/models/chat_messages.py:128-155` |
| Code-interpreter calls, native mode | The reply's `output` list as a tool call and its result (the code is the call's argument; the result is the JSON with `stdout`, `stderr`, `result`) | With the chat | `backend/open_webui/tools/builtin.py:782-789`; `builtin-native-tools.md` section 6 |
| Pictures printed by code-interpreter code | A `file` record (name `generated-image.png`, stored under a generated id) in the configured storage, linked to the chat and message by a `chat_file` row; not added to the search index (`process=False`) | Until the file or chat is deleted | `backend/open_webui/routers/images.py:520-559`; `backend/open_webui/routers/files.py:347-367`; `backend/open_webui/models/chats.py:218-230` |
| Files in the in-browser sandbox (`/mnt/uploads` and any folder created there) | **Default:** the memory of the hidden sandbox frame in that tab. **With `ENABLE_PYODIDE_FILE_PERSISTENCE` on:** also saved to the browser's own storage (IndexedDB) for the site | Default: until the sandbox is stopped (page reload, closing the tab, or the time limit in a code-interpreter run). With persistence: until deleted in the **Files** tab or the browser's site data is cleared | `src/lib/pyodide/createPyodideWorker.ts:7-10`; `src/lib/pyodide/pyodideSandboxHost.ts:29`, `:180-182`; `src/lib/workers/pyodide.worker.ts:49-70`, `:93-105`, `:308-317` |
| Files attached to the chat, as seen by in-browser code | Copied from the server into the sandbox before each code-interpreter run | As the row above | `src/routes/+layout.svelte:321-346` |
| Code sent to a Jupyter server | Leaves MedIT GPT; held by that server for the life of the kernel, which MedIT GPT shuts down after each run | What the Jupyter server keeps (logs, files written by code) is outside this repository: **TO BE CONFIRMED** | `backend/open_webui/utils/code_interpreter.py:60-67`, `:119-153` |
| Code execution chips reported by add-ons | In the browser's copy of the message (`code_executions`); the server's event handler stores only untyped sources, so these are not saved by it | Until the page reloads, as far as the code shows | `src/lib/components/chat/Chat.svelte:1328-1345`; `backend/open_webui/socket/main.py:1235-1250` |
| Whether the composer's Code Interpreter switch was on | The chat draft in the browser's session storage | For the browser session | `src/lib/components/chat/Chat.svelte:755-775`, `:838`, `:4040-4053` |

**Privacy notes.**

- With persistence on, the in-browser files belong to the browser profile and the site, not to the
  MedIT GPT account: every chat in that browser sees the same `/mnt/uploads`, and no code in `src/`
  clears that storage at sign-out (only `src/lib/workers/pyodide.worker.ts` uses it). On a shared
  computer, people should delete their files from the **Files** tab. Whether persistence is on in
  production is **TO BE CONFIRMED** (code default off, `backend/open_webui/env.py:1211`).
- With the `jupyter` engine, whatever is in the code (including data the person pasted or the model
  copied from the chat) is sent to the Jupyter server. Attached files are not sent to Jupyter by
  either feature (`backend/open_webui/routers/utils.py:49-64`; `backend/open_webui/tools/builtin.py:724-735`;
  `backend/open_webui/utils/middleware.py:6406-6421`).
- Chats may contain personal and health information (the research rules treat the stored data that
  way, `knowledgebase/reference/_research-prompt.md` rule 8); the same care applies to
  code-interpreter output stored with a chat and to output pictures stored as files.

## 7. Settings and Configuration

The values below are what the repository says. The live value of every persistent setting is data
in the `config` table, and of every environment variable in the deployment's environment:
**TO BE CONFIRMED** for production. After the first start the stored value wins over the
environment variable (ground truth).

### 7.1 Persistent Settings (Admin Settings › Code Execution)

Labels and descriptions are the `en-US` text of `settings.admin.codeExecution.*`
(`src/lib/i18n/locales/en-US/translation.json:2137-2167`).

| Key | Environment variable | Code default | Label and description in the panel | Effect | Source |
|---|---|---|---|---|---|
| `code_execution.enable` | `ENABLE_CODE_EXECUTION` | on | **Enable Code Execution**: `Allow models to run generated code and return execution results.` | Shows or hides the **Run** button; the server refuses Jupyter runs when off. (The description speaks of models, but this switch governs the person's **Run** button.) | `backend/open_webui/config.py:409`, `:2836`; `src/lib/components/admin/Settings/CodeExecution.svelte:56-62` |
| `code_execution.engine` | `CODE_EXECUTION_ENGINE` | `pyodide` | **Code Execution Engine**: `Choose the runtime used for generated code blocks.` | Browser or Jupyter for the **Run** button | `backend/open_webui/config.py:411`, `:2837`; `src/lib/components/admin/Settings/CodeExecution.svelte:64-83` |
| `code_execution.jupyter.url` | `CODE_EXECUTION_JUPYTER_URL` | empty | **Jupyter URL**: `Connect code execution to a Jupyter server endpoint.` (placeholder `Enter Jupyter URL`) | Server address for **Run** on Jupyter | `backend/open_webui/config.py:413`, `:2838`; `src/lib/components/admin/Settings/CodeExecution.svelte:85-99` |
| `code_execution.jupyter.auth` | `CODE_EXECUTION_JUPYTER_AUTH` | empty (`None`) | **Jupyter Auth**: `Select how Open WebUI authenticates with the Jupyter server.` Choices `None`, `Token`, `Password` | Which credential is used | `backend/open_webui/config.py:415`, `:2839`; `src/lib/components/admin/Settings/CodeExecution.svelte:104-118` |
| `code_execution.jupyter.auth_token` | `CODE_EXECUTION_JUPYTER_AUTH_TOKEN` | empty | **Jupyter Token**: `Credentials used to authenticate with the Jupyter server.` (masked field) | Secret: location only | `backend/open_webui/config.py:417`, `:2840`; `src/lib/components/admin/Settings/CodeExecution.svelte:120-147` |
| `code_execution.jupyter.auth_password` | `CODE_EXECUTION_JUPYTER_AUTH_PASSWORD` | empty | **Jupyter Password**: same description (masked field) | Secret: location only | `backend/open_webui/config.py:420`, `:2841`; `src/lib/components/admin/Settings/CodeExecution.svelte:120-147` |
| `code_execution.jupyter.timeout` | `CODE_EXECUTION_JUPYTER_TIMEOUT` | `60` (seconds) | **Code Execution Timeout**: `Maximum runtime in seconds before execution is stopped.` (placeholder `e.g. 60`) | Wait limit per kernel message (section 5.2) | `backend/open_webui/config.py:422`, `:2842`; `src/lib/components/admin/Settings/CodeExecution.svelte:149-162` |
| `code_interpreter.enable` | `ENABLE_CODE_INTERPRETER` | on | **Enable Code Interpreter**: `Allow models to use the code interpreter tool during chats.` | Offers the composer switch; one of the five server checks | `backend/open_webui/config.py:424`, `:2843`; `src/lib/components/admin/Settings/CodeExecution.svelte:170-176` |
| `code_interpreter.engine` | `CODE_INTERPRETER_ENGINE` | `pyodide` | **Code Interpreter Engine**: `Choose the runtime used by the code interpreter tool.` | Browser or Jupyter for the code interpreter; also decides whether the in-browser environment note is added and whether the **Files** tab appears | `backend/open_webui/config.py:433`, `:2850`; `src/lib/components/admin/Settings/CodeExecution.svelte:178-197`; `src/lib/components/chat/ChatControls.svelte:83-85` |
| `code_interpreter.prompt_template` | `CODE_INTERPRETER_PROMPT_TEMPLATE` | empty (use the built-in prompt) | **Code Interpreter Prompt Template**: `Leave empty to use the default prompt, or enter a custom prompt.` | Replaces the legacy-mode prompt (7.3) | `backend/open_webui/config.py:435`, `:2851`; `src/lib/components/admin/Settings/CodeExecution.svelte:279-292` |
| `code_interpreter.jupyter.url` | `CODE_INTERPRETER_JUPYTER_URL`, else `CODE_EXECUTION_JUPYTER_URL` | empty | **Jupyter URL**: `Connect code interpreter to a Jupyter server endpoint.` | Server address for the code interpreter | `backend/open_webui/config.py:437`, `:2852`; `src/lib/components/admin/Settings/CodeExecution.svelte:199-213` |
| `code_interpreter.jupyter.auth` | `CODE_INTERPRETER_JUPYTER_AUTH`, else `CODE_EXECUTION_JUPYTER_AUTH` | empty (`None`) | **Jupyter Auth** (as above) | As above | `backend/open_webui/config.py:439-442`, `:2853`; `src/lib/components/admin/Settings/CodeExecution.svelte:218-232` |
| `code_interpreter.jupyter.auth_token` | `CODE_INTERPRETER_JUPYTER_AUTH_TOKEN`, else the code-execution one | empty | **Jupyter Token** | Secret: location only | `backend/open_webui/config.py:444-447`, `:2854` |
| `code_interpreter.jupyter.auth_password` | `CODE_INTERPRETER_JUPYTER_AUTH_PASSWORD`, else the code-execution one | empty | **Jupyter Password** | Secret: location only | `backend/open_webui/config.py:450-453`, `:2855` |
| `code_interpreter.jupyter.timeout` | `CODE_INTERPRETER_JUPYTER_TIMEOUT`, else `CODE_EXECUTION_JUPYTER_TIMEOUT` | `60` | **Code Execution Timeout** (same label as the code-execution field) | As above, for the code interpreter | `backend/open_webui/config.py:455-460`, `:2856`; `src/lib/components/admin/Settings/CodeExecution.svelte:263-276` |

Notes:

- The fallbacks from `CODE_INTERPRETER_*` to `CODE_EXECUTION_*` happen only when the defaults are
  first seeded; after that each key is stored separately (`backend/open_webui/config.py:437-460`;
  ground truth on seeding).
- Both timeout variables are converted with `int(...)` when the configuration module loads, so a
  value that is not a whole number stops the application from starting
  (`backend/open_webui/config.py:422`, `:455-460`; migrations and settings load at import, ground truth).
- The server accepts an empty timeout from the panel (`int | None`,
  `backend/open_webui/routers/configs.py:693`, `:701`); what an empty value does at run time is in
  section 14.
- The token and password are ordinary persistent settings, are returned to the admin panel, and
  are part of the admin settings export (ground truth on secrets). Never copy them into a ticket.
- The fork did not change any of these defaults (section 12).

### 7.2 Environment-Only Settings

| Variable | Code default | Effect | Source |
|---|---|---|---|
| `CODE_INTERPRETER_BLOCKED_MODULES` | empty | Comma-separated list of modules code-interpreter code may not import directly (both modes). Read once when the server starts; no admin control. Security-sensitive: how far this restriction reaches is a question for the platform maintainer and U of T Information Security (security.utoronto.ca) | `backend/open_webui/config.py:462-464`; `backend/open_webui/utils/middleware.py:26`, `:6373-6391`; `backend/open_webui/tools/builtin.py:660-686` |
| `ENABLE_PYODIDE_FILE_PERSISTENCE` | `false` | `true` keeps in-browser sandbox files in the browser's storage between page loads (section 6) | `backend/open_webui/env.py:1211`; `backend/open_webui/main.py:2348`; `src/lib/pyodide/createPyodideWorker.ts:7-10` |
| `WEBSOCKET_EVENT_CALLER_TIMEOUT` | empty: no limit; a value that is not a number becomes 300 seconds | How long the server waits for the browser to answer an `execute:python` request | `backend/open_webui/env.py:534-542`; `backend/open_webui/socket/main.py:1268-1281` |
| `USER_PERMISSIONS_FEATURES_CODE_INTERPRETER` | `True` | Seed for the default `features.code_interpreter` permission | `backend/open_webui/config.py:1914-1916`, `:2011` |
| `USE_SLIM` (build) | `false` | Slim build: in-browser packages come from the jsDelivr CDN instead of the bundle (section 5.9) | `scripts/prepare-pyodide.js:236-251`; `Dockerfile:6`, `:29` |
| `HTTPS_PROXY`, `ALL_PROXY`, `HTTP_PROXY` (build) | none | Proxy for the preparation script's downloads | `scripts/prepare-pyodide.js:44-72` |

### 7.3 Built-in Prompts (Not Editable Except Where Noted)

- **Default code interpreter prompt** (`DEFAULT_CODE_INTERPRETER_PROMPT`,
  `backend/open_webui/config.py:466-481`), used in legacy mode when the template is empty. It is
  headed `#### Code Interpreter` and tells the model, among other things, to enclose code in
  `<code_interpreter type="code" lang="python">` tags "and stop right away", not to use Markdown
  fences inside the tags, to print meaningful output explicitly, to iterate when results are
  unclear, to display any image, audio or file link in the output "exactly as-is", and to respond
  in the chat's primary language. Its first bullet says the shell "runs directly in the user's
  browser", whichever engine is set. Replaceable with **Code Interpreter Prompt Template**.
- **In-browser environment note** (`CODE_INTERPRETER_PYODIDE_PROMPT`,
  `backend/open_webui/config.py:483-496`), added for the `pyodide` engine only, in both modes: no
  package installs (`pip install`, `subprocess` and `micropip.install()` "are not available"),
  attached files are at `/mnt/uploads/`, output files may be written there for the person to
  download from the file browser, and the file system "persists across code executions within the
  same session". Not replaceable from the panel.
- The native tool's own description is the `execute_code` docstring
  (`backend/open_webui/tools/builtin.py:643-650`).

### 7.4 Fixed Limits in the Code

| Limit | Value | Source |
|---|---|---|
| In-browser run time (Run button and code interpreter) | 60 seconds | `src/lib/components/chat/Messages/CodeBlock.svelte:260-269`; `src/routes/+layout.svelte:348-373` |
| In-browser formatting with Black | 60 seconds | `src/lib/components/common/CodeEditor.svelte:168-177` |
| Each **Files** tab request (list, read, upload, delete) | 30 seconds | `src/lib/components/chat/PyodideFileNav.svelte:109-128` |
| Code blocks run per reply, legacy mode | 5 | `backend/open_webui/utils/middleware.py:6348-6352` |
| Default in the Jupyter client's own signature (every caller passes the saved setting instead) | 60 seconds | `backend/open_webui/utils/code_interpreter.py:36`, `:192-194`; callers `backend/open_webui/routers/utils.py:63`, `backend/open_webui/tools/builtin.py:734`, `backend/open_webui/utils/middleware.py:6420` |

### 7.5 Related Settings Documented Elsewhere

- Model **Capabilities**, **Builtin Tools** and **Default Features** › `Code Interpreter`:
  `workspace-models-and-model-access.md`.
- The chat's **Function Calling** parameter (native or legacy): `chat-completion-pipeline-and-generation-tasks.md`.
- **Hide Processing Details** (fork setting) and how it hides code analysis: section 12 and
  `chat-composer-and-message-display.md`.
- The general persistent-setting mechanics: `configuration-persistent-settings-a-to-o.md`.

## 8. Cron Jobs and Background Processes

There is no scheduled job, crontab entry or startup loop for either feature (none of the seven
startup loops in `knowledgebase/tools/inventory.md` touches code execution). Everything happens
while a request is being handled:

| What | When it runs | Where | Source |
|---|---|---|---|
| A **Run** click | When clicked | In the browser (`pyodide`) or as one web request to the server, which calls Jupyter (`jupyter`) | `src/lib/components/chat/Messages/CodeBlock.svelte:141-220`; `backend/open_webui/routers/utils.py:41-71` |
| The legacy code-interpreter loop | Inside the reply's own processing task, after each code block the model writes, up to five times | Server, with the browser or Jupyter doing the run | `backend/open_webui/utils/middleware.py:6348-6536` |
| `execute_code` (native) | When the model calls the tool during a reply | As above | `backend/open_webui/tools/builtin.py:633-792` |
| Waiting for the browser | The server's chat task waits on the `execute:python` request; the browser's own 60-second limit usually ends it first | Server and browser | `backend/open_webui/socket/main.py:1258-1281`; `src/routes/+layout.svelte:348-373` |
| Jupyter kernel shutdown | At the end of every run | Server to Jupyter | `backend/open_webui/utils/code_interpreter.py:60-67` |
| The tab's shared in-browser sandbox | Stays loaded in the background of the tab between runs until it is stopped (time limit or page reload) | Browser | `src/routes/+layout.svelte:282-293`, `:354-356` |
| Delivery of `config.code_execution.updated` | Started as background tasks when an admin saves the panel | Server | `backend/open_webui/routers/configs.py:715-727`; `backend/open_webui/events.py:1062-1066`, `:1159-1171` |
| Preparing the in-browser runtime | At build time (`npm run dev` / `npm run build`), not at run time | Build machine | `package.json:6-9`, `:22`; `scripts/prepare-pyodide.js:235-257` |

Not run in the background: **automations** do not use the code interpreter, and **background
sub-agents** drop it unless the engine is `jupyter` (section 3.4). No job removes pictures saved
from code output; they stay with the chat (section 6).

## 9. Notifications and Emails

The application sends no email (ground truth). For this area:

- **No in-app or browser notification** is raised by running code; results appear in place (under
  the code block or in the reply). Short messages appear as toasts (section 10).
- **Event `config.code_execution.updated`** (description `Code execution configuration was updated.`,
  message `Config Code Execution updated`) is published each time an admin saves the Code Execution
  panel (`backend/open_webui/events.py:83-87`; `backend/open_webui/routers/configs.py:715-727`). Its
  data is `code_execution_enabled`, `code_execution_engine`, `code_interpreter_enabled` and
  `code_interpreter_engine`; it does not carry the Jupyter address, token or password. It goes to
  any event webhooks configured to receive it, with the text `Config Code Execution updated (code_execution)`,
  and to active Event functions (`backend/open_webui/events.py:1034-1060`, `:1103-1171`). It is not
  one of the events that raise user notifications (`backend/open_webui/events.py:669-675`,
  `:1083-1086`). The event's actor block holds the saving admin's id, name, email and role
  (`backend/open_webui/events.py:704`, `:974-985`), so webhook receivers get that personal data.
  Which webhooks exist in production is **TO BE CONFIRMED**.
- **Socket request `execute:python`.** In-browser code-interpreter runs are a request from the
  server to one browser tab, which answers with the output; it is not shown as a notification
  (`src/routes/+layout.svelte:634-641`).
- **Socket events during a reply.** The reply's progress (`chat:completion` with the growing output,
  including code items) is pushed to the browser as the code runs
  (`backend/open_webui/utils/middleware.py:6353-6360`, `:6480-6487`); see
  `chat-completion-pipeline-and-generation-tasks.md` for the event stream.
- **Add-on events.** A function or tool can send a `source` or `citation` event whose data type is
  `code_execution`; the browser shows it as a code execution chip (`src/lib/components/chat/Chat.svelte:1328-1345`).

## 10. Error, Warning and Notice Messages (Verbatim)

Messages are quoted as the code spells them. `{name}` marks a value filled in at run time. Where
the visible text comes from Python, Jupyter or the browser rather than from MedIT GPT's code, the
row says so instead of quoting it.

### 10.1 Running Code (Run Button and Code Interpreter)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Execution Time Limit Exceeded` | Error (in the output area, or a toast when formatting) | `src/lib/components/chat/Messages/CodeBlock.svelte:263`; `src/routes/+layout.svelte:352`; `src/lib/components/common/CodeEditor.svelte:176` | An in-browser run (or in-browser Black formatting) took more than 60 seconds, including the time to load Python and packages on a first run | Simplify the code or the data; run again (the second run is faster once the runtime is loaded) | Section 11.2 |
| `Running...` | Notice (output area) | `src/lib/components/chat/Messages/CodeBlock.svelte:610-614` | A **Run** is in progress (button shows `Running`) | Wait up to 60 seconds (browser engine) | Section 11.2 if it never ends |
| `Code execution is disabled` | Error (red toast, HTTP 403) | `backend/open_webui/routers/utils.py:43-47`; `backend/open_webui/constants.py:125`; toast `src/lib/components/chat/Messages/CodeBlock.svelte:149-152` | **Run** with the Jupyter engine after an admin switched code execution off | Reload the page; the button then disappears | Confirm the switch with an admin |
| `[ERROR: Code execution engine not supported]` | Error (red toast, HTTP 400) | `backend/open_webui/routers/utils.py:67-71`; `backend/open_webui/constants.py:16-23` | The page thinks the engine is `jupyter` but the saved engine is not (the page's configuration is out of date) | Reload the page | Compare **Code Execution Engine** with what the person sees |
| `Error: {err}` | Error (under `STDOUT/STDERR`, or in the code-interpreter output) | `backend/open_webui/utils/code_interpreter.py:69-77` | Anything failing between MedIT GPT's server and the Jupyter server: connection refused or timed out, wrong address, refused sign-in, kernel could not start. `{err}` is the underlying library's text | None; report it | Escalate with the text and time (section 11.6) |
| `Execution timed out.` | Error (appended to the error text) | `backend/open_webui/utils/code_interpreter.py:184-186` | Jupyter engine: no message from the kernel within the configured timeout | Shorten the work, or print progress | Section 11.2 |
| `_xsrf token not found` (shown after `Error: `) | Error (as above) | `backend/open_webui/utils/code_interpreter.py:79-95`, prefixed at `:76` | Jupyter engine with **Password** authentication: the Jupyter server's sign-in page did not return what password sign-in needs | None | Escalate: Jupyter authentication configuration |
| `Code interpreter engine not configured.` | Error (the code interpreter's printed output, legacy mode) | `backend/open_webui/utils/middleware.py:6422-6423` | The saved code interpreter engine is neither `pyodide` nor `jupyter` | None | Escalate: the engine setting |
| `Unknown code interpreter engine: {engine}` | Error (tool result, native mode) | `backend/open_webui/tools/builtin.py:741-742` | As above, native mode | None | Escalate (see `builtin-native-tools.md`) |
| `Event call not available. WebSocket connection required for pyodide execution.` | Error (tool result, native mode) | `backend/open_webui/tools/builtin.py:689-694` | Browser engine, but the request has no live browser connection to run it in (for example a request made through the API) | Use the chat in the browser | `builtin-native-tools.md` |
| `Request context not available` | Error (tool result, native mode) | `backend/open_webui/tools/builtin.py:653-654` | `execute_code` called without a request (internal call) | None | Escalate |
| `Client session disconnected.` | Error (in `stderr` of the output) | `backend/open_webui/socket/main.py:1262-1266`; handled at `backend/open_webui/utils/middleware.py:6427-6430` and `backend/open_webui/tools/builtin.py:709-714` | Browser engine: the tab that sent the message is no longer connected (closed, reloaded, network lost), or the connection belongs to another account | Keep the chat tab open until the reply finishes; send again | Section 11.4 |
| `Event call timed out. The browser tab may be inactive or closed.` | Error (in `stderr`) | `backend/open_webui/socket/main.py:1279-1281` | Browser engine: the tab did not answer within `WEBSOCKET_EVENT_CALLER_TIMEOUT` (only when that variable is set) | Keep the tab open and in front; send again | Section 11.4 |
| `Direct import of module {name} is restricted.` | Error (Python `ImportError` text in the output) | `backend/open_webui/utils/middleware.py:6373-6391`; `backend/open_webui/tools/builtin.py:660-686` | Code-interpreter code imported a module on the administrator's blocked list | Ask for an approach that does not use that module | The list is `CODE_INTERPRETER_BLOCKED_MODULES` (section 7.2) |
| Python's own error text, for example a traceback ending in a `ModuleNotFoundError` or `NameError` line | Error (under `STDOUT/STDERR`; in native mode also in the tool's `stderr`) | Produced by Python; captured at `src/lib/workers/pyodide.worker.ts:231-233`, `src/lib/pyodide/pyodideSandboxHost.ts:138-141`, `backend/open_webui/utils/code_interpreter.py:178-179` | The code itself failed | Fix the code or ask the model to | Section 11.3 for missing modules |
| `[processResult error]: {message}` | Error (in `RESULT`) | `src/lib/workers/pyodide.worker.ts:363-366`; `src/lib/pyodide/pyodideSandboxHost.ts:104-106` | The value of the last line could not be converted for display | Print the value instead of leaving it as the last line | None |
| `Running`, `Run`, `STDOUT/STDERR`, `RESULT` | Labels | `src/lib/components/chat/Messages/CodeBlock.svelte:503`, `:515`, `:612-630` | Run button states and output headings | None | None |
| `Failed to render diagram: {errorMsg}` | Error (inside a Mermaid block) | `src/lib/components/chat/Messages/CodeBlock.svelte:369-377` | A `mermaid` block could not be drawn (diagram blocks, not code execution) | Ask for a corrected diagram | `chat-composer-and-message-display.md` |
| `Failed to render visualization: {errorMsg}` | Error (inside a Vega block) | `src/lib/components/chat/Messages/CodeBlock.svelte:378-389` | A `vega` or `vega-lite` block could not be drawn | As above | As above |
| `{{COUNT}} hidden lines` | Notice | `src/lib/components/chat/Messages/CodeBlock.svelte:588-596` | A collapsed code block (button `Expand`) | Click **Expand** | None |

### 10.2 Code Interpreter Display

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Analyzing...` | Notice (spinner) | `src/lib/components/common/Collapsible.svelte:114-119` | Legacy mode: a code block is being written or run | Wait | Section 11.2 if it never changes |
| `Analyzed` | Notice | `src/lib/components/common/Collapsible.svelte:114-117` | Legacy mode: the block finished (also shown for a block left unrun at the end of a reply) | Click to see code and output | Section 11.4 (cause 7) |
| `Ran {{COUNT}} analysis` / `Ran {{COUNT}} analyses` | Notice (after `Exploring` or `Explored`) | `src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte:165-177` | Several processing details in a row, including code blocks | Click to expand | None |
| `Code execution: {name}` / `Code execution` | Window title | `src/lib/components/chat/Messages/CodeExecutionModal.svelte:37-42` | A code execution chip from an add-on was clicked | None | The add-on's author |
| `error`, `success`, `incomplete` | Badge (shown capitalized) | `src/lib/components/chat/Messages/CodeExecutionModal.svelte:17-27` | State of an add-on's code execution | None | None |
| `ERROR`, `OUTPUT`, `Files` | Headings | `src/lib/components/chat/Messages/CodeExecutionModal.svelte:75-104` | Parts of an add-on's code execution | None | None |

### 10.3 In-Browser File Browser (Files Tab)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `No files yet. Upload files or run Python code to create them.` | Notice | `src/lib/components/chat/PyodideFileNav.svelte:452-458` | The folder is empty | Upload, or run code that writes files | Section 11.5 |
| `Failed to list directory` | Error (red text) | `src/lib/components/chat/PyodideFileNav.svelte:157-169` | The sandbox did not answer the listing within 30 seconds or failed | Click **Refresh**; reload the page | Section 11.5 |
| `Failed to read file` | Error (in the preview) | `src/lib/components/chat/PyodideFileNav.svelte:185-202` | Reading the file from the sandbox failed or timed out | Try again | None |
| `Error: {res.error}` | Error (in the preview) | `src/lib/components/chat/PyodideFileNav.svelte:186-188` | The sandbox reported an error reading the file (for example it no longer exists) | Refresh the list | None |
| `[Binary file: {entry.size} bytes]` | Notice (in the preview) | `src/lib/components/chat/PyodideFileNav.svelte:192-198` | The file is not text and not a supported picture | Use **Download** | None |
| `Delete {{name}}` / `Are you sure you want to delete this?` | Confirmation | `src/lib/components/chat/PyodideFileNav.svelte:351-356` | **Delete** on a file or folder | Confirm or cancel | None |
| `Drop files here` | Notice | `src/lib/components/chat/PyodideFileNav.svelte:366-386` | Files dragged over the panel | Drop to upload into the current folder | None |
| `Path copied` | Success (toast) | `src/lib/components/chat/FileNav/FileEntryRow.svelte:404-416` | **Copy Path** | None | None |
| `Could not read file.` | Notice (preview) | `src/lib/components/chat/FileNav/FilePreview.svelte:507-511` | The shared preview has nothing to show for the selected file | Use **Download** | Shared with terminal file browsers (`workspace-tools-tool-servers-mcp-and-terminals.md`) |
| `JSON parse error: {{error}}` | Error (preview) | `src/lib/components/chat/FileNav/FilePreview.svelte:240-247`, `:472-476` | A JSON file that is not valid JSON | None | As above |

### 10.4 Formatting and Administration

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Code formatted successfully` | Success (toast) | `src/lib/components/common/CodeEditor.svelte:181-201` | **Ctrl+Shift+F** formatted the code | None | None |
| `Pyodide worker error` | Error (toast) | `src/lib/components/common/CodeEditor.svelte:155-160`, `:188` | In-browser formatting failed to start | Reload the page | Section 11.1 |
| Black's error text | Error (toast; HTTP 400 for admins) | `backend/open_webui/routers/utils.py:30-38`; `src/lib/components/common/CodeEditor.svelte:181-189` | The code could not be parsed as Python, so Black refused to format it (also happens for code in another language) | None; the code is unchanged | None |
| `Warning: Jupyter execution enables arbitrary code execution, posing severe security risks—proceed with extreme caution.` | Warning (panel description) | `src/lib/components/admin/Settings/CodeExecution.svelte:67-71`, `:181-185` | An engine set to `jupyter` | Admin decision | Section 14 |
| `Settings saved successfully!` | Success (toast) | `src/lib/components/chat/SettingsModal.svelte:460-464` | The Code Execution panel saved | None | None |
| `Select a engine`, `Select an auth method`, `Enter Jupyter URL`, `Enter Jupyter Token`, `Enter Jupyter Password`, `e.g. 60`, `Leave empty to use the default prompt, or enter a custom prompt` | Placeholders | `src/lib/components/admin/Settings/CodeExecution.svelte:75-78`, `:95`, `:112`, `:133`, `:141`, `:159`, `:288-290` | Empty fields in the panel | None | None |
| `This is a default user permission and will remain enabled.` | Notice | `src/lib/components/admin/Users/Groups/Permissions.svelte:1090-1095` | A group's `Code Interpreter` permission is off but the default grants it | None | `users-groups-roles-and-permissions.md` |
| `Code execution configuration was updated.` / `Config Code Execution updated` | Event description and webhook text | `backend/open_webui/events.py:83-87`, `:1042-1044` | The panel was saved | None | Section 9 |

### 10.5 Log Lines and Browser Console (Not Shown to Users)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `execute code failed, %s` | Server log (exception) | `backend/open_webui/utils/code_interpreter.py:74-76` | Any Jupyter run failure (pairs with `Error: {err}`) | None | Search the log at the time of the report |
| `close kernel failed, %s` | Server log (exception) | `backend/open_webui/utils/code_interpreter.py:61-66` | The Jupyter kernel could not be shut down after a run | None | Escalate: kernels may be left running on the Jupyter server |
| `Code interpreter continuation failed: %s` | Server log (exception) | `backend/open_webui/utils/middleware.py:6532-6536` | Legacy mode: asking the model to continue after a run failed; the reply also shows an error (see `chat-completion-pipeline-and-generation-tasks.md`) | Regenerate | Search the log |
| `execute_code error: {e}` | Server log (exception) | `backend/open_webui/tools/builtin.py:790-792` | Native mode: `execute_code` crashed; the tool returns `{"error": ...}` | None | Search the log |
| `Event caller: session {session_id} not owned by requesting user or disconnected` | Server log (warning) | `backend/open_webui/socket/main.py:1262-1266` | Pairs with `Client session disconnected.` | None | Section 11.4 |
| `Event caller timed out for session {session_id}` | Server log (warning) | `backend/open_webui/socket/main.py:1279-1281` | Pairs with the time-out message | None | Section 11.4 |
| `Code interpreter output: %s` | Server log (debug only) | `backend/open_webui/utils/middleware.py:6425` | Legacy mode, every run; contains the code's output, which may include personal data | None | Handle debug logs with care |
| `Failed to fetch file for Pyodide:` | Browser console | `src/routes/+layout.svelte:334-336` | An attached file could not be downloaded into the sandbox (the run continues without it) | None | Section 11.5 |
| `Error syncing from IndexedDB:` / `Error syncing to IndexedDB:` | Browser console | `src/lib/workers/pyodide.worker.ts:55-63`, `:96-105`, `:308-317` | Persistence on: the browser's storage could not be read or written | None | Section 11.5 |
| `Python output:` / `Python result:` / `execute:python` | Browser console | `src/lib/workers/pyodide.worker.ts:29-31`, `:227`; `src/routes/+layout.svelte:638-640` | Every run; the console holds the code, attached file names and output | None | Treat console screenshots as possibly holding personal data |

### 10.6 Build-Time Messages (Developers Only)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `No wheel bundled for: {missing}` | Build error (stops the build) | `scripts/prepare-pyodide.js:210-233` | A package the script must bundle has no wheel in `static/pyodide/` | None | `developer-tools-scripts-and-tests.md` |
| `Failed to load Pyodide:` | Build error (script stops downloading) | `scripts/prepare-pyodide.js:77-85` | The Pyodide runtime could not start in Node | None | As above |
| `Package installation failed:` / `Failed to load or install micropip:` / `Failed to write lock file:` | Build error | `scripts/prepare-pyodide.js:109-129` | A package download or the lock-file write failed | None | As above |
| `Pyodide version mismatch, removing static/pyodide directory` | Build notice | `scripts/prepare-pyodide.js:90-97` | The bundled runtime's version differs from `package.json` | None | As above |
| `Could not read pyodide-lock.json, skipping PyPI wheel download` | Build warning | `scripts/prepare-pyodide.js:146-153` | No lock file to add the PyPI wheels to | None | As above |
| `Failed to fetch PyPI metadata for {pkg}: {res.status}` / `No pure-Python wheel found for {pkg}=={version}, skipping` / `Failed to download {wheel.filename}: {wheelRes.status}` | Build error or warning | `scripts/prepare-pyodide.js:155-184` | PyPI could not be reached or had no suitable wheel | None | As above |
| `Invalid network proxy URL: "{preferedProxy}"` | Build warning | `scripts/prepare-pyodide.js:62-68` | A proxy variable is not a valid URL | None | As above |
| `All listed packages are bundled` | Build notice | `scripts/prepare-pyodide.js:232` | The bundle check passed | None | None |

## 11. Common Tier-1 Issues and Troubleshooting

First establish **which feature** is involved (the person clicked **Run**, or the model ran code
during a reply with **Code Interpreter** on) and, for the code interpreter, whether the reply shows
`Analyzing...`/`Analyzed` lines (legacy mode) or tool-call entries (native mode). Tier 1 does not
change settings, permissions or models; an administrator can read Admin Settings › Code Execution
to tell you the engines in use.

### 11.1 "The Run button does nothing" (or "There is no Run button")

**Symptom.** The person expects to run a code block but nothing visible happens, or there is no
**Run** button.

**Likely causes, in order.**

1. **The first run is still loading.** With the browser engine the button turns into `Running` and
   the output area shows `Running...` while Python and the packages download; this counts against
   the 60-second limit (`src/lib/components/chat/Messages/CodeBlock.svelte:254-269`, `:499-504`, `:610-614`).
2. **No button because of the block's language.** The button appears only for blocks marked
   `python` or `py`, or unmarked blocks that look like Python; a block marked `python3`, `ipython`
   or another language gets none (`src/lib/components/chat/Messages/CodeBlock.svelte:106-139`, `:498`).
   Only code fenced with three backticks becomes a code block at all; other code is shown as plain
   text (`src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte:205-230`).
3. **Code execution is switched off** (`code_execution.enable`), so there is no button anywhere
   (`src/lib/components/chat/Messages/CodeBlock.svelte:498`).
4. **The in-browser runtime could not start.** When the background worker variant is in use
   (persistence on) and the worker reports an error, the run ends with no message at all
   (`src/lib/components/chat/Messages/CodeBlock.svelte:351-356`); otherwise the button stays at
   `Running` until the 60-second limit. In the default variant a start-up error is caught and its
   text appears in the output (`src/lib/pyodide/pyodideSandboxHost.ts:145-186`). Causes can be the
   `/pyodide/` files missing from the deployment, or the browser blocking them.
5. **Jupyter engine:** the request failed; this shows a red toast rather than nothing (section 11.6).

**Diagnostic steps.**

1. Ask whether the button changed to `Running` and whether anything appeared under the block after a
   minute.
2. Ask for the first line of the code block (the language word after the three backticks).
3. Ask whether other people see **Run** buttons (if no one does, the switch is probably off).
4. Ask the person to try a one-line block such as `print("hello")` marked `python`.
5. If they can, ask for a screenshot of the browser's developer console during a run (it may hold
   code and output, so handle it as possibly personal data).

**Resolution.** Explain the language rule and the first-run delay; suggest asking the model to mark
the block `python`. If one-line code also fails, escalate.

**Escalation.** To the platform maintainer: the person's browser and version, time of the attempt,
what they saw, the console screenshot, and whether `/pyodide/` is reachable on the site (an admin or
developer checks this).

### 11.2 "Code runs forever" (or "It says Execution Time Limit Exceeded")

**Symptom.** `Running...` or `Analyzing...` (or a tool-call spinner) does not go away, or the
output says `Execution Time Limit Exceeded` or `Execution timed out.`

**Likely causes, in order.**

1. **The browser's 60-second limit** was reached: heavy code, large data, or a slow first load of
   Python and packages (`src/lib/components/chat/Messages/CodeBlock.svelte:260-269`;
   `src/routes/+layout.svelte:348-373`).
2. **The chat tab was closed or reloaded while the code interpreter's browser engine was
   running.** The server waits for the tab's answer with no time limit unless
   `WEBSOCKET_EVENT_CALLER_TIMEOUT` is set (`backend/open_webui/env.py:534-542`;
   `backend/open_webui/socket/main.py:1268-1278`), so the reply can stay at `Analyzing...` or a
   spinner (that the wait continues after the tab disconnects is library behaviour, section 14). If the tab had already gone before the run started, the output says
   `Client session disconnected.` instead (`backend/open_webui/socket/main.py:1262-1266`).
3. **Jupyter engine:** the **Code Execution Timeout** passed with no message from the kernel
   (`Execution timed out.`), or the Jupyter server is slow or overloaded
   (`backend/open_webui/utils/code_interpreter.py:156-186`).
4. **The model keeps writing more code** (legacy mode runs up to five blocks per reply)
   (`backend/open_webui/utils/middleware.py:6348-6352`).

**Diagnostic steps.**

1. Which feature, and which message, if any.
2. Was the chat tab kept open and in front until the reply finished?
3. Does a small calculation finish quickly? If so, the original work is simply too large.
4. For a stuck reply: note the chat's URL (`/c/{id}`) and the time.

**Resolution.** Suggest smaller data or simpler code, keeping the tab open while the code
interpreter works, pressing **Stop** on a stuck reply and sending again. The 60-second browser limit
is fixed in the code; there is no setting for it (section 7.4).

**Escalation.** To an administrator if Jupyter runs time out repeatedly (with times, chat URL and
the error text), or if replies hang often (they may consider `WEBSOCKET_EVENT_CALLER_TIMEOUT`).

### 11.3 "It says a module isn't available"

**Symptom.** The output contains a Python `ModuleNotFoundError` (Python's own text) or
`Direct import of module {name} is restricted.`

**Likely causes, in order.**

1. **The package is not bundled** for the browser engine. Only the packages in section 5.8 are
   installed automatically, plus the standard library; others are not installed for the code, and the
   in-browser environment note tells the model not to try (`backend/open_webui/config.py:486-489`).
2. **The package is bundled but not detected.** Detection is a text search for specific imports, so
   `import openai`, `import black`, `import PIL` and similar do not trigger an install, even though
   the files are bundled (`src/lib/components/chat/Messages/CodeBlock.svelte:223-239`;
   `src/routes/+layout.svelte:301-317`). It may work later in the same tab if another run already
   installed the package into the shared sandbox.
3. **The administrator blocked the module** (`Direct import of module {name} is restricted.`,
   code interpreter only; section 7.2).
4. **Jupyter engine:** the module is not installed on the Jupyter server (**TO BE CONFIRMED** what
   it has).
5. **Slim build:** packages come from the jsDelivr CDN and the person's browser could not reach it
   (`scripts/prepare-pyodide.js:236-251`; which build production uses is **TO BE CONFIRMED**).

**Diagnostic steps.** Get the exact module name and the full error line; check it against the
table in section 5.8; ask whether the message mentions "restricted".

**Resolution.** Ask the model to solve the task with the available packages (for example `pandas`,
`numpy`, `matplotlib`, `scipy`, `scikit-learn`, `sympy`). A blocked module stays blocked.

**Escalation.** A request for a new package or for unblocking a module goes to the platform
maintainer (packages are added at build time in `scripts/prepare-pyodide.js`).

### 11.4 "The code interpreter doesn't run my code"

**Symptom.** The model answers without running anything, writes code that does not run, or the run
shows `Client session disconnected.`

**Likely causes, in order.**

1. **The Code Interpreter switch was not on for that message** (no pill in the composer), or it is
   not offered to the person (section 3.3).
2. **The model chose not to run code**; the switch makes the feature available, the model decides.
3. **The browser tab was not connected** (closed, reloaded, or network dropped) while the browser
   engine was in use: `Client session disconnected.` (`backend/open_webui/socket/main.py:1262-1266`).
4. **Legacy mode:** the model wrote ordinary code fences instead of the `<code_interpreter>` tags,
   so the server saw no block to run (`backend/open_webui/config.py:473-474`); the code then
   shows as a normal block with a **Run** button.
5. **Legacy mode with the model's Builtin Tools › Code Interpreter off:** the prompt asking for tags
   is still added, but the server does not look for them, so nothing runs
   (`backend/open_webui/utils/middleware.py:2722-2738` compared with `:4877-4891`).
6. **Automations and background sub-agents** do not offer it (section 3.4).
7. **Five blocks already ran in this reply** (legacy); a sixth shows `Analyzed` with no output
   (`backend/open_webui/utils/middleware.py:6348-6352`, `:6538-6541`).

**Diagnostic steps.** Ask for a screenshot of the composer before sending (is the pill there?), the
model name, whether the reply shows `Analyzing...`/`Analyzed` or tool-call entries, and whether the
tab stayed open.

**Resolution.** Turn the switch on before sending; ask the model explicitly to run the code; keep
the tab open. Offer the **Run** button on the code as an alternative.

**Escalation.** If the switch is missing for someone who should have it, to an administrator
(permission, model settings). If the model consistently writes code without running it, to the
platform maintainer with the model name and chat URL (model or Function Calling settings).

### 11.5 "Files created by the code don't show up"

**Symptom.** The model or the code says it saved a file, but the person cannot find it.

**Likely causes, in order.**

1. **The Files tab only exists for the browser engine and only while Code Interpreter is on**
   (`src/lib/components/chat/ChatControls.svelte:83-85`). With the `jupyter` engine, files are
   written on the Jupyter server and nothing brings them back; only printed text and PNG pictures
   return (`backend/open_webui/utils/code_interpreter.py:166-189`).
2. **The file was written by a Run click in a separate runtime.** Without the tab's shared sandbox,
   each **Run** uses its own runtime, whose files the Files tab does not show
   (`src/lib/components/chat/Messages/CodeBlock.svelte:243-252`).
3. **The sandbox was restarted.** A page reload, or the 60-second limit in a code-interpreter run
   (which stops and replaces the sandbox, `src/routes/+layout.svelte:354-356`), clears files unless
   persistence is on (section 6).
4. **The file is outside `/mnt/uploads`.** The tab opens there; use the breadcrumbs to go to `/`
   (`src/lib/components/chat/PyodideFileNav.svelte:1-3`, `:132-144`).
5. **The list is out of date.** Click **Refresh** (`src/lib/components/chat/PyodideFileNav.svelte:402-412`).

**Diagnostic steps.** Engine in use; whether the switch is on; whether the page was reloaded since;
the file path the code used.

**Resolution.** Ask the model to save files in `/mnt/uploads/` and to print a short summary; use
**Download** in the Files tab to keep a copy (files in the sandbox are not stored by MedIT GPT).
For data the person must keep, ask the model to print the result so it is saved with the chat.

**Escalation.** Not normally needed. If the Files tab shows `Failed to list directory` repeatedly
after a reload, escalate with the browser and time.

### 11.6 "Running code shows an `Error:` message"

**Symptom.** With the `jupyter` engine, the output (Run button or code interpreter) shows text
beginning `Error: `, the code interpreter shows a short Python message about a string index, or
**Run** shows a red toast about a response that is not valid JSON.

**Likely causes, in order.**

1. The **Jupyter URL** is wrong, empty or unreachable from the MedIT GPT server. An empty URL fails
   before any connection is attempted, outside the client's own error handling
   (`backend/open_webui/utils/code_interpreter.py:51-53`, compare `:69-77`): the code interpreter
   then reports Python's index error text as its output (`backend/open_webui/utils/middleware.py:6464-6465`;
   `backend/open_webui/tools/builtin.py:790-792`), and **Run** gets a server error that the browser
   cannot read, shown as the browser's own error text in a toast
   (`backend/open_webui/routers/utils.py:49-66`; `src/lib/apis/utils/index.ts:43-59`). The exact
   wording comes from Python and the browser.
2. **Jupyter Auth** does not match the server (wrong token or password, or the wrong type).
3. The Jupyter server is down or refuses new kernels.

**Diagnostic steps.** Record the exact text after `Error: ` and the time; check whether every run
fails (configuration) or only some (server load).

**Resolution.** None at tier 1; the person can use the browser engine only if an administrator
switches to it.

**Escalation.** To the administrator responsible for the Jupyter server, with the error text, times
and which feature failed. Never ask anyone to send the token or password.

### 11.7 "I can't find the Code Interpreter switch"

**Symptom.** The Integrations menu has no `Code Interpreter` entry.

**Likely causes, in order.** The admin switch is off; the person lacks `features.code_interpreter`;
one of the selected models has the capability off; a terminal is selected; the page has not been
reloaded since a change (section 3.3).

**Diagnostic steps.** Ask which models are selected and whether a terminal is chosen; try with a
single common model; ask the person to reload.

**Resolution.** Deselect the terminal, choose another model, reload.

**Escalation.** To an administrator for permissions or the switch, naming the person (by their
MedIT GPT account, not by personal details in the ticket title) and the model.

### 11.8 "My chart doesn't appear"

**Symptom.** The code made a chart but no picture is shown.

**Likely causes, in order.**

1. **Hide Processing Details is on** (fork setting): code analysis lines and tool-call entries are
   hidden, and so are pictures inside them, unless the model repeats the picture in its answer
   (section 12).
2. **The browser engine only captures charts shown with `plt.show()`**; a chart saved with
   `savefig` goes to a file instead (`src/lib/workers/pyodide.worker.ts:193-220`).
3. **Only PNG pictures printed on their own line are converted** (native mode checks for PNG;
   the Run button looks for lines starting with a PNG data address)
   (`backend/open_webui/tools/builtin.py:752-780`; `src/lib/components/chat/Messages/CodeBlock.svelte:159-180`).
4. **Saving the picture as a file failed**, which can leave a broken picture
   (`backend/open_webui/utils/middleware.py:6450-6463`).

**Diagnostic steps.** Ask whether Settings › Interface › **Hide Processing Details** is on; whether
the reply shows `Analyzed` or a tool-call entry; expand it to look for the picture.

**Resolution.** Suggest turning Hide Processing Details off for such chats, or asking the model to
include the chart in its answer; ask for `plt.show()`.

**Escalation.** If pictures are broken for everyone, to the platform maintainer (file storage).

### 11.9 "The code interpreter ran, but ignores the errors"

**Symptom.** In legacy mode the code fails, but the model carries on as though it had no output, or
repeats the same failing code.

**Likely cause.** In legacy mode the model is sent only the printed output (or the result when
nothing was printed); the error text is not included, so the model does not see the traceback
(`backend/open_webui/utils/misc.py:546-563`). Native mode sends `stderr` to the model
(`backend/open_webui/tools/builtin.py:782-789`).

**Diagnostic steps.** Expand the `Analyzed` line and look at the output under `STDOUT/STDERR`.

**Resolution.** The person can copy the error into their next message.

**Escalation.** If this happens often, to the platform maintainer: the chat's Function Calling mode
could be reviewed.

### 11.10 "Files I made earlier are gone" (or "I see files I didn't make")

**Symptom.** The Files tab is empty after a reload, or shows files from other chats or other people.

**Likely causes.** With persistence off (the code default) files live only until the sandbox stops.
With persistence on they are kept in the browser profile for the site, shared by all chats and
by every MedIT GPT account used in that browser profile, and nothing clears them at sign-out
(section 6).

**Diagnostic steps.** Is this a shared or public computer? Was the page reloaded?

**Resolution.** Explain the behaviour; on shared computers, delete files from the Files tab after
use. Treat any report of seeing another person's files as a privacy matter.

**Escalation.** A report of someone else's files: stop and refer to the U of T Privacy Office
(privacy.utoronto.ca) and the platform maintainer, with the computer location and time, without
opening or copying the files.

### 11.11 "The page gets slow after I run code a few times"

**Symptom.** The chat page becomes sluggish after several **Run** clicks.

**Likely cause.** When the tab has no shared sandbox, each **Run** click starts a new in-browser
Python runtime; the code stops only the most recent one when the block goes away, so earlier ones
stay loaded until the page is reloaded (`src/lib/components/chat/Messages/CodeBlock.svelte:243-252`,
`:428-433`).

**Resolution.** Reload the page. Turning on the Code Interpreter switch and opening the **Files**
tab first makes later runs share one sandbox.

**Escalation.** Not needed; mention it in feedback to the platform maintainer if frequent.

### 11.12 "Pressing Ctrl+Shift+F gave me several error messages"

**Symptom.** Several toasts appear at once after the formatting shortcut.

**Likely cause.** Every editable code block on the page reacts to the shortcut and tries to format
its code as Python; blocks in other languages fail (section 5.6).

**Resolution.** Ignore the messages; nothing is changed in the failed blocks. Avoid the shortcut on
pages with several code blocks.

**Escalation.** None.

### 11.13 "The output of my Run disappeared"

**Symptom.** Output under a block is gone after a reload or after switching chats.

**Likely cause.** **Run** output is not saved (section 6).

**Resolution.** Run again, or copy the output into a message.

**Escalation.** None.

### 11.14 "The Code Execution settings did not save" (Administrators)

**Symptom.** After **Save**, the values revert and no `Settings saved successfully!` toast appears.

**Likely cause.** The panel shows no error when the save request fails; the toast appears only after
a successful save (`src/lib/components/admin/Settings/CodeExecution.svelte:26-28`, `:39-45`;
`src/lib/apis/configs/index.ts:606-634`).

**Diagnostic steps.** Time of the attempt; whether other admin panels save.

**Resolution.** None at tier 1.

**Escalation.** To the platform maintainer with the time; the server log will hold the failure.

## 12. Local Customisations

### 12.1 The Area Itself Matches Upstream v0.11.4

Read-only `git diff main...uoft` and `git diff` show **no change** in the files that implement code
execution and the code interpreter: `backend/open_webui/utils/code_interpreter.py`,
`backend/open_webui/utils/middleware.py`, `backend/open_webui/config.py`,
`backend/open_webui/tools/builtin.py`, `backend/open_webui/routers/utils.py`,
`backend/open_webui/routers/configs.py`, `backend/open_webui/socket/main.py`,
`src/lib/components/admin/Settings/CodeExecution.svelte`,
`src/lib/components/chat/Messages/CodeBlock.svelte`, `CodeExecutions.svelte`,
`CodeExecutionModal.svelte`, `src/lib/workers/pyodide.worker.ts`, `src/lib/pyodide/`,
`src/lib/components/chat/PyodideFileNav.svelte`, `src/lib/components/common/CodeEditor.svelte`,
`src/lib/components/common/Collapsible.svelte`, `src/lib/components/chat/ChatControls.svelte` and
`scripts/prepare-pyodide.js`. Settings, defaults, engines, limits and messages in this document are
upstream behaviour.

### 12.2 Hide Processing Details (Fork Setting) Changes What Is Shown

The fork's per-person setting **Hide Processing Details** (Settings › Interface; English text
`Show "Thinking..." instead of status updates, tool calls, reasoning, and code analysis while a response is generated, and keep them hidden afterwards. Tool approval requests and images or embeds from tools still appear.`,
`src/lib/i18n/locales/en-US/translation.json:2923-2924`) affects this area as follows. The setting
itself is documented in `chat-composer-and-message-display.md`.

| When the setting is on | Source | Change |
|---|---|---|
| Legacy code-interpreter blocks (`Analyzing...`/`Analyzed`) are not shown, alone or grouped | `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte:73-108`, `:146-147`; `src/lib/components/chat/Messages/structuredOutput.ts:344-416` | Committed in `uoft`; reworked in the uncommitted working tree |
| `execute_code` tool-call entries (native mode) are hidden unless they wait for an approval; pictures inside their output are hidden with them, because they are part of the output text and not the tool's separate picture list | `src/lib/components/common/ToolCallDisplay.svelte:142-147`, `:199`, `:372-387`; `backend/open_webui/tools/builtin.py:744-780` | Committed; the working tree moved the setting read into the component |
| Code execution chips from add-ons are not shown | `src/lib/components/chat/Messages/ResponseMessage.svelte:944-946` (upstream: `{#if message.code_executions}`) | Committed |
| The model still runs code and still receives the output; only the display changes | `backend/open_webui/utils/middleware.py:6348-6536` (unchanged) | n/a |

The description says images "from tools still appear"; for `execute_code` charts this holds only
if the model repeats the picture in its answer (section 11.8, section 14).

### 12.3 Other Differences in the Working Tree

- `static/pyodide/pyodide-lock.json` differs from the committed file only in the `black` entry
  (version `26.5.1` committed, `26.10.0` in the working tree, with a matching new wheel file). This
  is what `scripts/prepare-pyodide.js` does when it fetches the latest `black` from PyPI during
  `npm run dev` or `npm run build` (`scripts/prepare-pyodide.js:145-207`); it is a side effect of
  building, not a deliberate fork change. Both wheel files are present in `static/pyodide/`, which
  is otherwise ignored by git except for the lock file (`.gitignore:22-24`).
- No fork change touches the `code_execution.*` or `code_interpreter.*` settings, the
  `features.code_interpreter` permission, or the default prompts.

## 13. Source File Index

Files read for this document (whole file unless lines are given). Paths are repository-relative.

### 13.1 In Scope

| File | Role |
|---|---|
| `backend/open_webui/utils/code_interpreter.py` | Jupyter client: sign-in, kernel start and shutdown, run, output collection, time-out |
| `backend/open_webui/utils/middleware.py` (lines 26-28, 90, 254, 1013-1266, 2672-2751, 3279-3298, 4476-4891, 5570-5800, 6330-6620) | Code interpreter prompt, the five checks, `<code_interpreter>` tag detection, the legacy run loop, pictures, feeding output back |
| `backend/open_webui/config.py` (lines 405-496, 1908-1916, 2000-2015, 2822-2856) | Settings, environment variables, default prompts, permission default, `DEFAULT_CONFIG` keys |
| `src/lib/components/admin/Settings/CodeExecution.svelte` | Admin Settings › Code Execution panel |
| `src/lib/components/chat/Messages/CodeBlock.svelte` | Code block, **Run** button, both engine paths, output display |
| `src/lib/components/chat/Messages/CodeExecutions.svelte` | Code execution chips from add-ons |
| `src/lib/components/chat/Messages/CodeExecutionModal.svelte` | Window for one add-on code execution |
| `src/lib/workers/pyodide.worker.ts` | Background-worker sandbox with browser-storage persistence |
| `src/lib/pyodide/createPyodideWorker.ts` | Chooses the sandbox variant |
| `src/lib/pyodide/pyodideSandboxHost.ts` | Default sandbox (hidden isolated frame) |
| `src/lib/components/chat/PyodideFileNav.svelte` | **Files** tab for the in-browser sandbox |
| `scripts/prepare-pyodide.js` | Build-time preparation of the runtime and bundled packages |
| `static/pyodide/pyodide-lock.json` (summarized: `info`, package count, entries for the bundled packages), the file list of `static/pyodide/`, `static/pyodide/package.json` (header) | Bundled runtime and packages |

### 13.2 Supporting Files

| File | Role |
|---|---|
| `backend/open_webui/routers/utils.py` (lines 1-90) | `/api/v1/utils/code/execute` and `/code/format` |
| `backend/open_webui/routers/configs.py` (lines 45-60, 80-87, 683-728) | Code Execution settings endpoints and event |
| `backend/open_webui/tools/builtin.py` (lines 630-792) | `execute_code` tool (native mode) |
| `backend/open_webui/utils/tools.py` (lines 520-575, 640-720) | Built-in tool checks |
| `backend/open_webui/socket/main.py` (lines 1222-1289) | Browser request channel (`execute:python`), its messages and time-out |
| `backend/open_webui/env.py` (lines 530-542, 1200-1216) | `WEBSOCKET_EVENT_CALLER_TIMEOUT`, `ENABLE_PYODIDE_FILE_PERSISTENCE` |
| `backend/open_webui/main.py` (lines 1275-1297, 2224-2402) | Function Calling default; `/api/config` flags |
| `backend/open_webui/events.py` (lines 1-30, 78-92, 669-705, 974-1066, 1069-1204) | `config.code_execution.updated` event and its delivery |
| `backend/open_webui/constants.py` (lines 1-60, 125) | Error message helpers |
| `backend/open_webui/utils/misc.py` (lines 325-355, 536-570) | What the model is sent after a legacy run |
| `backend/open_webui/utils/files.py` (lines 33, 108-147); `backend/open_webui/routers/images.py` (lines 520-575); `backend/open_webui/routers/files.py` (lines 327-390) | Saving output pictures as files |
| `backend/open_webui/utils/sanitize.py` (lines 44-57) | Code clean-up before running |
| `backend/open_webui/utils/automations.py` (lines 175-195); `backend/open_webui/utils/subagents.py` (lines 300-320) | Where the code interpreter is excluded |
| `backend/open_webui/models/config.py` (lines 141-238); `backend/open_webui/models/chats.py` (lines 218-230, 1141-1192, 2571-2576); `backend/open_webui/models/chat_messages.py` (lines 128-155) | Where settings and reply output are stored |
| `backend/open_webui/routers/users.py` (lines 255-275) | Permission model default |
| `src/routes/+layout.svelte` (lines 255-450, 600-700, 1255-1295) | Browser side of `execute:python`, shared sandbox, configuration loading |
| `src/lib/components/chat/Chat.svelte` (lines 755-775, 830-840, 900-980, 1075-1110, 1300-1350, 1600-1626, 2170-2185, 3394-3413, 4040-4060) | Feature flags sent with a message; chips; drafts |
| `src/lib/components/chat/MessageInput.svelte` (lines 740-850, 2165-2182, 2290-2350, 2515-2560); `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte` (lines 300-335, 490-525) | Composer switch and pill |
| `src/lib/components/chat/ChatControls.svelte` (lines 60-110, 222-262, 290-300, 420-430) | **Files** tab condition |
| `src/lib/components/chat/SettingsModal.svelte` (lines 57, 150-190, 330-360, 460-464, 877-878); `src/routes/(app)/admin/settings/+page.svelte`; `src/routes/(app)/admin/settings/[tab]/+page.svelte` | Admin navigation and save toast |
| `src/lib/components/common/CodeEditor.svelte` (lines 95-215, 237, 270-305) | Editing and Black formatting |
| `src/lib/components/common/Collapsible.svelte` (lines 90-175); `src/lib/components/chat/Messages/Markdown/ConsecutiveDetailsGroup.svelte` (lines 110-235); `src/lib/components/chat/Messages/Markdown/MarkdownTokens.svelte` (lines 60-150, 190-240, 300-580); `src/lib/components/chat/Messages/structuredOutput.ts` (lines 250-345, 340-420, 630-665); `src/lib/components/chat/Messages/StructuredOutputRenderer.svelte` (lines 60-75, 175-185) | How code-interpreter items are displayed and hidden |
| `src/lib/components/common/ToolCallDisplay.svelte` (lines 130-200, 365-388) | Tool-call entries and Hide Processing Details |
| `src/lib/components/chat/Messages/ResponseMessage.svelte` (lines 95-115, 195-220, 938-950); `src/lib/components/chat/Messages/UserMessage.svelte` (lines 385-402); `src/lib/components/chat/Messages/ContentRenderer.svelte` (lines 140-170, 290-350) | Where code blocks and chips are rendered |
| `src/lib/components/chat/FileNav/FileNavToolbar.svelte` (lines 1-60, 125-329); `src/lib/components/chat/FileNav/FileEntryRow.svelte` (lines 1-60, 355-452); `src/lib/components/chat/FileNav/FilePreview.svelte` (lines 20-40, 240-250, 470-512) | Shared file browser parts |
| `src/lib/components/admin/Users/Groups/Permissions.svelte` (lines 1070-1100); `src/lib/components/workspace/Models/ModelEditor.svelte` (lines 1245-1262) | Permission switch; model default features |
| `src/lib/apis/configs/index.ts` (lines 579-634); `src/lib/apis/utils/index.ts` (lines 30-80); `src/lib/apis/files/index.ts` (lines 315-341) | Browser API calls |
| `src/lib/i18n/locales/en-US/translation.json` (dotted keys `settings.admin.codeExecution.*`, `settings.admin.models.*.codeInterpreter.*`, `settings.personal.interface.hideProcessingDetails.*`) | English text of dotted keys |
| `package.json` (lines 6-9, 22, 137); `Dockerfile` (lines 1-50 and `USE_SLIM` lines); `.gitignore` (lines 22-24); `.dockerignore` | Build wiring |

Outside the repository, the installed `python-socketio` 5.16.2 (`AsyncServer.call`) was read to
confirm how the server's wait for the browser behaves (section 14).

## 14. Open Questions

### 14.1 Organisational and Live Values (TO BE CONFIRMED)

1. **Live values of the fifteen settings** (`code_execution.*`, `code_interpreter.*`) in production,
   especially both engines and both switches. They are data in the `config` table.
2. **Whether a Jupyter server is used at all**, where it is hosted, who runs and secures it, what
   packages it has, what it logs and keeps, and who supports it. Nothing in the repository says.
3. **Privacy review of the Jupyter engine.** Code sent to Jupyter can contain chat content, which
   may include personal or health information. Whether a U of T Information Risk Assessment
   (uoft.me/Information-Risk-Assessment) covers it is not recorded here.
4. **Environment values in production:** `ENABLE_PYODIDE_FILE_PERSISTENCE`,
   `WEBSOCKET_EVENT_CALLER_TIMEOUT`, `CODE_INTERPRETER_BLOCKED_MODULES`,
   `USER_PERMISSIONS_FEATURES_CODE_INTERPRETER`.
5. **Which build production runs** (full or `USE_SLIM`). In a slim build the person's browser
   downloads Python packages from the jsDelivr CDN, which matters for networks that block it and
   for privacy notices. What `static/pyodide/` holds in the production build is likewise unknown.
6. **The Function Calling mode in use** per model (native is the code default; a model or chat can
   set legacy). Data.
7. **Whether U of T wants a per-user control for the Run button**; the code has none.
8. **Escalation contacts** (platform maintainer, Jupyter owner) are not in the repository.

### 14.2 Security-Sensitive (Referred, Not Documented)

9. The isolation of code run in the browser sandbox and on a Jupyter server, and what such code can
   reach. Security-sensitive: refer to the platform maintainer and U of T Information Security
   (security.utoronto.ca).
10. How far the `CODE_INTERPRETER_BLOCKED_MODULES` restriction reaches. Security-sensitive: refer as
    above.
11. How the Jupyter credentials are handled between MedIT GPT and the Jupyter server.
    Security-sensitive: refer as above.

### 14.3 Behaviour Not Established from the Code Alone

12. **Network access from in-browser Python.** The code neither provides nor blocks it; the default
    prompt mentions "API calls" (`backend/open_webui/config.py:472`). Whether requests succeed
    depends on the browser and on any `CONTENT_SECURITY_POLICY` the deployment sets
    (`backend/open_webui/utils/security_headers.py:44`, `:131-133`). Not tested.
13. **Whether a restrictive `CORS_ALLOW_ORIGIN`** (`backend/open_webui/config.py:2134`, default `*`)
    or a Content-Security-Policy stops the default sandbox frame from loading `/pyodide/` files.
    The frame is isolated from the page's origin (`src/lib/pyodide/pyodideSandboxHost.ts:209-215`),
    which suggests its file requests are cross-origin. Not tested.
14. **Memory limits** for in-browser Python: none are set in the code; whatever the browser and
    WebAssembly allow applies. Not established.
15. **An empty timeout saved from the panel.** The server stores an empty value
    (`backend/open_webui/routers/configs.py:693`, `:701`) and the Jupyter client passes it to
    `asyncio.wait_for` (`backend/open_webui/utils/code_interpreter.py:159`); in Python that means no
    limit. Not tested.
16. **A tab closed in the middle of an in-browser run.** The installed python-socketio 5.16.2
    documents that its wait continues until the time-out even if the connection drops; with
    `WEBSOCKET_EVENT_CALLER_TIMEOUT` unset (no time-out) the reply would wait indefinitely. This is
    library behaviour outside the repository.
17. **Start-up failure of the background-worker variant** surfaces either as no message or as the
    60-second time-out, depending on how the browser reports errors from the worker; not tested.
18. **Exact texts from Python, Pyodide, Jupyter, Black and the browser** (module-not-found hints,
    the empty-URL index error, JSON parse errors in toasts) are not in the repository and are
    described, not quoted.
19. **Whether add-on code execution chips survive a page reload.** The server does not store them
    (`backend/open_webui/socket/main.py:1235-1250`); whether the browser saves them with the chat
    was not established.
20. **Whether output pictures saved from code appear in the person's file list** elsewhere in the
    interface; see `files-uploads-and-storage.md`.

### 14.4 Discrepancies and Upstream Quirks Noted

21. The **Hide Processing Details** description says images from tools still appear, but
    `execute_code` charts are part of the hidden output text, so they disappear unless the model
    repeats them (section 12.2).
22. The **Enable Code Execution** description (`Allow models to run generated code and return execution results.`)
    describes the code interpreter more than the **Run** button it actually governs.
23. The **Code Execution Timeout** description (`Maximum runtime in seconds before execution is stopped.`)
    does not match the code, which limits each wait for the kernel's next message.
24. The default code interpreter prompt says the shell "runs directly in the user's browser" even
    when the engine is Jupyter (`backend/open_webui/config.py:471`).
25. In legacy mode the model is not sent error text after a run (`backend/open_webui/utils/misc.py:555-563`),
    although the prompt asks it to "refine the code and re-execute" (`backend/open_webui/config.py:477`).
26. In legacy mode the code interpreter prompt is added whenever the request asks for the feature
    (`backend/open_webui/utils/middleware.py:2722-2738`), while the run step also checks the
    model's Builtin Tools entry, the switch and the permission (`:4877-4891`); a model with Builtin
    Tools › Code Interpreter off can therefore be told to write tags that are not run.
27. The Pyodide file browser shows **Sort**, folder **Download**, **Show Hidden Files**, **Rename**
    and drag-to-move, which do nothing there (section 5.5).
28. Repeated **Run** clicks without a shared sandbox leave earlier runtimes loaded
    (`src/lib/components/chat/Messages/CodeBlock.svelte:246-252`).
29. **Ctrl+Shift+F** is handled by every code editor on the page, whatever its language
    (`src/lib/components/common/CodeEditor.svelte:181-187`, `:289-303`).
30. Build observation for `developer-tools-scripts-and-tests.md`: the lock file written by
    `micropip.freeze()` (`scripts/prepare-pyodide.js:121-123`) is then overwritten by the copy of
    the npm package's own lock file (`:132-137`, `:253-254`); the bundled lock in this checkout is
    the npm lock's 354 entries plus the seven PyPI entries (361).
31. The admin engine placeholder reads `Select a engine` (upstream wording).

No contradiction with `knowledgebase/tools/ground-truth.md` or `knowledgebase/tools/inventory.md`
was found.
