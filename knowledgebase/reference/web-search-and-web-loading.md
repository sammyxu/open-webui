# Web Search and Web Page Loading

## At a Glance

- **What it is.** Web search lets an answer use live internet results. One configured search
  engine (32 are supported, from Google PSE, Brave and Bing to self-hosted SearXNG) turns queries
  into links; a web loader downloads the pages; the text is embedded and the best passages are added
  to the prompt as sources (section 5). The same loader serves **Attach Webpage** (a page or YouTube
  transcript added to a message) and the model's `fetch_url` tool.
- **How it is triggered.** Only when web search is on site-wide (`web.search.enable`, code default
  off) and the user has `features.web_search` (default on). The user switches **Web Search** on in
  the composer's **Integrations** menu, or it is switched on by a model's default features or the
  personal **Web Search in Chat** = **Always** setting. In the default **native** function calling
  mode the model is then *offered* the `search_web` and `fetch_url` tools and decides itself whether
  to search; in **legacy** mode the server runs a search step first, writing queries with the task
  model (sections 1, 5.1-5.9).
- **Where it is configured.** Admin Settings > **Web Search** (`/admin/settings/web`): engine and
  its key, result count (default 3), concurrency, domain filter, bypass switches, loader engine
  (Default, Playwright, Firecrawl, Tavily, Microsoft Web IQ, External), timeouts and YouTube
  options. The live values are data and **TO BE CONFIRMED** (section 7).
- **What fails most often, and what users see.** A misconfigured or failing engine shows
  `[ERROR: Something went wrong while searching the web.]` on the reply's status line (the real
  reason is only in the server log in legacy mode); ten engines can fail silently and show
  `[ERROR: No results found from web search]`; empty or blocked pages can surface as `Failed to
  embed and store the retrieved web pages. ...`. Attachments fail with `[ERROR: Error processing
  URL]` (unreachable, error page, or internal address) or a YouTube transcript message (sections 10
  and 11).
- **Privacy.** Queries derived from the conversation go to the outside search provider and page
  addresses to websites or a loader service; four engines also receive the user's name, email, id
  and role regardless of `ENABLE_FORWARD_USER_INFO_HEADERS` (section 5.14; review needed, section
  14). Queries and result lists are saved with the chat.
- **This area matches upstream Open WebUI v0.11.4.** The fork's **Hide Processing Details** setting
  hides the search status lines and tool-call blocks (section 12).

## 1. Purpose and Who Uses It

**What it is.** Web search lets a chat answer use live internet results instead of only the model's
training data, uploaded files and knowledge bases. Web page loading is the companion machinery
that downloads a web page (or a YouTube transcript) and turns it into text the model can read. The
same loading code serves three features: the pages found by a web search, a page a user attaches
by address, and the `fetch_url` tool a model can call by itself.

There are two ways a web search can happen in a chat, and which one applies depends on the
model's **function calling** mode (`native` by default, `backend/open_webui/main.py:1290-1294`):

| Mode | Who decides to search | What happens | Source |
|---|---|---|---|
| **Native** (default) | The model, when the user has switched **Web Search** on for the message | The model is given two tools, `search_web` and `fetch_url`, and calls them if it judges a search useful; it may also answer without searching | `backend/open_webui/utils/tools.py:677-685`; `backend/open_webui/tools/builtin.py:294-362` |
| **Legacy** | The server, whenever Web Search is on for the message | Before the model answers, the server asks the task model for search queries, runs them through the configured provider, loads the result pages and adds them to the prompt as sources | `backend/open_webui/utils/middleware.py:2700-2709`, `:1560-1730` |

**Who uses it.**

| Who | What they do here |
|---|---|
| Any signed-in user with the `features.web_search` permission | Switches **Web Search** on in the composer's **Integrations** menu; reads the "Searched N sites" step and the sources under the answer (section 5) |
| Any user with the `chat.web_upload` permission | Attaches a web page or YouTube video by address through **+** > **Attach Webpage** (section 5.10) |
| Model builders (workspace or admin) | Turn the **Web Search** capability, default feature and built-in tool on or off per model (section 7.6) |
| Administrators | Choose the search provider and the web loader, enter provider keys, set limits, the domain filter and confirmation prompt under Admin Settings > **Web Search** (section 7) |
| Tier-1 support | Explains why a search did not run or found nothing, and gathers evidence for escalation (section 11) |

**Where it lives in the code.** The provider adapters are `backend/open_webui/retrieval/web/` (one
file per provider, plus `main.py` for the shared domain filter and result shape and `utils.py` for
the web loaders). The web loaders that call outside services are in
`backend/open_webui/retrieval/loaders/` (`external_web.py`, `tavily.py`, `youtube.py`,
`microsoft_web_iq.py`). The endpoints are in `backend/open_webui/routers/retrieval.py`
(`process_url`, `process_web`, `search_web`, `process_web_search`, `:2245-3047`). The chat step is
`chat_web_search_handler` in `backend/open_webui/utils/middleware.py:1560-1730`. The admin screen
is `src/lib/components/admin/Settings/WebSearch.svelte`.

**Neighbouring documents.** Embedding, vector storage, the RAG template and citations in general are
in `rag-retrieval-embeddings-and-vector-stores.md`; the built-in tool system as a whole in
`builtin-native-tools.md`; the chat pipeline and query-generation task in
`chat-completion-pipeline-and-generation-tasks.md`; how status lines are drawn in
`in-chat-status-and-response-messages.md`; the composer as a whole in
`chat-composer-and-message-display.md`; the settings storage model in
`configuration-persistent-settings-r-to-w.md`; and the other admin panels in
`admin-settings-panels.md`.

## 2. Navigation and URLs

The production host name is **TO BE CONFIRMED**; addresses below are relative to the site root.

### 2.1 Where Users Meet Web Search

| Place | What the user sees | Condition | Source |
|---|---|---|---|
| Composer, **Integrations** menu (puzzle-piece button) | A **Web Search** row with a globe icon and a switch; tooltip `Search the internet` | Web search on site-wide, user has `features.web_search` (admins always), and every selected model has the `web_search` capability (an unset capability counts as on) | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:444-468`; `src/lib/components/chat/MessageInput.svelte:824-828`, `:759-763` |
| Composer chip row | A **Web Search** chip while the switch is on; clicking it switches web search off | Same as above | `src/lib/components/chat/MessageInput.svelte:2484-2489` |
| Composer **+** menu | **Attach Webpage** (globe icon); greyed out with tooltip `You do not have permission to upload web content.` when the permission is missing | Always listed | `src/lib/components/chat/MessageInput/InputMenu.svelte:246-266` |
| **Attach Webpage** window | Title **Attach Webpage**, field **Webpage URLs** (placeholder `https://example.com`, one address per line), button **Add** | Opened from the **+** menu | `src/lib/components/chat/MessageInput/AttachWebpageModal.svelte:40-93` |
| **Use Web Search?** dialog | Appears before the first web search in a chat when the admin requires confirmation | `web.search.confirmation.enable` on | `src/lib/components/chat/Chat.svelte:4220-4235` |
| Answer, status line | `Searching the web`, then "Searching" with the queries, then `Searched {{count}} sites` (expandable list of pages) | Legacy mode | `backend/open_webui/utils/middleware.py:1562-1700` |
| Answer, tool call | A tool-call block for `search_web` or `fetch_url` | Native mode, when the model calls the tool | `backend/open_webui/utils/tools.py:677-685` |
| Knowledge base page | **Attach Webpage** adds a page to a knowledge base | Owned by `knowledge-bases.md` | `src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:1172-1176` |
| **Settings > Interface** (personal) | **Web Search in Chat** (`settings.personal.interface.webSearchInChat.label`, "Web Search in Chat"; description "Set web search availability for new chats.") | Always | `src/lib/i18n/locales/en-US/translation.json:2991-2992`; owned by `chat-composer-and-message-display.md` |

### 2.2 Links That Start a Chat with Web Content

A new chat reads three optional query parameters when it opens (`src/lib/components/chat/Chat.svelte:2164-2174`):

| Parameter | Effect |
|---|---|
| `?web-search=true` | Switches **Web Search** on for the new chat |
| `?load-url=<address>` | Attaches the page at that address, exactly as **Attach Webpage** would |
| `?youtube=<video id>` | Attaches the transcript of `https://www.youtube.com/watch?v=<video id>` |

Example (fictional): `/?web-search=true` or `/?load-url=https://www.example.com/page`.

### 2.3 Admin Screens

| Screen | Address | Source |
|---|---|---|
| Admin Settings > **Web Search** (group **Tools**) | `/admin/settings/web`, which redirects to `/?settings=admin:web` | `src/routes/(app)/admin/settings/[tab]/+page.svelte:6-10`; `src/lib/components/chat/SettingsModal.svelte:167`, `:341-345`, `:875-876`; title `settings.admin.web.title` = "Web Search" (`src/lib/i18n/locales/en-US/translation.json:2710`) |
| Group and default permissions: **Web Search** (features) and **Allow Web Upload** (chat) | Admin Panel > Users > Groups (owned by `users-groups-roles-and-permissions.md`) | `src/lib/components/admin/Users/Groups/Permissions.svelte:610-613`, `:1050` |
| Model editor: **Capabilities** > **Web Search**, **Default Features** > **Web Search**, **Builtin Tools** > **Web Search** | Workspace > Models, or Admin Settings > Models (owned by `workspace-models-and-model-access.md`) | `src/lib/components/workspace/Models/Capabilities.svelte:25-28`; `src/lib/components/workspace/Models/DefaultFeatures.svelte:13-16`; `src/lib/components/workspace/Models/BuiltinTools.svelte:49-52` |

### 2.4 API Endpoints in This Area

All are under `/api/v1/retrieval` (`backend/open_webui/main.py:852`).

| Method and path | Who | Purpose | Source |
|---|---|---|---|
| `GET /api/v1/retrieval/config` | Admin | Returns all retrieval settings; the `web` object holds every web-search and web-loader setting, including provider keys | `backend/open_webui/routers/retrieval.py:629-789` |
| `POST /api/v1/retrieval/config/update` | Admin | Saves settings; the `web` object is written field by field | `backend/open_webui/routers/retrieval.py:962-983`, `:1313-1398` |
| `POST /api/v1/retrieval/process/url` | Any verified user | Fetches an address; decides whether it is a web page, a YouTube video, an image or a file; used by **Attach Webpage** | `backend/open_webui/routers/retrieval.py:2356-2426` |
| `POST /api/v1/retrieval/process/web` and `/process/youtube` (same handler) | Any verified user | Loads a page or YouTube transcript and (by default) stores it in the vector store | `backend/open_webui/routers/retrieval.py:2429-2508` |
| `POST /api/v1/retrieval/process/web/search` | Verified user with web search on and `features.web_search` (admins always) | Runs a list of queries through the configured provider, loads the pages and stores them | `backend/open_webui/routers/retrieval.py:2882-3047` |

The browser client also defines `processWeb`, `processYoutubeVideo` and `processWebSearch`
(`src/lib/apis/retrieval/index.ts:308-457`), but no component calls them; only `processUrl` is
used (`src/lib/components/chat/Chat.svelte:1816`;
`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:331`). `processWebSearch` sends a body
(`query`, `collection_name`) that does not match what the server expects (`queries`,
`backend/open_webui/routers/retrieval.py:464-465`); it is dead code, not a live failure.

## 3. Roles and Permissions

### 3.1 Who May Do What

| Action | Admin | User | Pending | Source |
|---|---|---|---|---|
| See and use the **Web Search** switch | Yes, when web search is on site-wide | Only with `features.web_search` (default on) | No (cannot use the app) | `src/lib/components/chat/MessageInput.svelte:824-828`; `backend/open_webui/config.py:1908`, `:2009` |
| Run a search through `/process/web/search` | Yes, when web search is on | With `features.web_search` | No | `backend/open_webui/routers/retrieval.py:2885-2895` |
| Attach a web page or YouTube video | Yes | With `chat.web_upload` (default on) | No | `src/lib/components/chat/Chat.svelte:1790-1794`; `backend/open_webui/config.py:1859`, `:1984` |
| Read or change Admin Settings > Web Search | Yes | No (`get_admin_user`) | No | `backend/open_webui/routers/retrieval.py:630`, `:963` |

Both permissions add up across groups and a group cannot remove one the defaults grant
(`knowledgebase/tools/ground-truth.md`, Accounts and Access). The **Web Search** and **Allow Web
Upload** switches in the group editor show `This is a default user permission and will remain
enabled.` when the default grants the permission
(`src/lib/components/admin/Users/Groups/Permissions.svelte:600-620`, `:1050-1058`).

### 3.2 The Three Server-Side Gates for a Chat Search

The `features` flags in a chat request come from the browser, so the server re-checks them:

| Path | Checks before searching | Source |
|---|---|---|
| Legacy step in the chat pipeline | `features.web_search` sent as true, `web.search.enable` on, user is admin or has `features.web_search`, and the model's function calling is `legacy` | `backend/open_webui/utils/middleware.py:2700-2709` |
| Native tools `search_web` and `fetch_url` | The model's **Builtin Tools** > **Web Search** category on (default on), `web.search.enable` on, the model's `web_search` capability on (default on), `features.web_search` sent as true, and the user is admin or has `features.web_search` | `backend/open_webui/utils/tools.py:533-566`, `:677-685` |
| `POST /process/web/search` | `web.search.enable` on (else HTTP 403 `ACCESS_PROHIBITED`), and admin or `features.web_search` (else HTTP 403 `ACCESS_PROHIBITED`) | `backend/open_webui/routers/retrieval.py:2885-2895` |

Built-in tools are offered only when the chat request carries a session id (browser chats do, and
automation runs set one, `backend/open_webui/utils/automations.py:315`, `:488`), function calling is
not `legacy` and the model's **Builtin Tools** capability is on (default on)
(`backend/open_webui/utils/middleware.py:2809-2813`, `:3125-3136`). The native `search_web` tool
calls the provider directly (`backend/open_webui/tools/builtin.py:319`), so it does not pass
through the `/process/web/search` checks; its own gate is the injection check above.

The confirmation dialog (**Use Web Search?**) is enforced only in the browser
(`src/lib/components/chat/Chat.svelte:3165-3173`); the server has no confirmation check.

### 3.3 Attaching Web Pages

The **Attach Webpage** menu item and the upload routine check `chat.web_upload` in the browser
(`src/lib/components/chat/MessageInput/InputMenu.svelte:72-73`; `src/lib/components/chat/Chat.svelte:1791-1794`).
The endpoints `/process/url`, `/process/web` and `/process/youtube` require a verified user
(`backend/open_webui/routers/retrieval.py:2361`, `:2436`). Whether and where the server enforces
`chat.web_upload` is security-sensitive: refer to the platform maintainer and U of T Information
Security (security.utoronto.ca) (section 14).

### 3.4 Who Can Read Stored Search Results

A web search that is embedded is stored in a vector collection named `web-search-{user id}-{hash
of the queries}` (`backend/open_webui/routers/retrieval.py:3013`). Retrieval allows such a
collection only to the user whose id is in the name
(`backend/open_webui/retrieval/utils.py:1345-1348`; see `rag-retrieval-embeddings-and-vector-stores.md`,
section 3.2). An attached web page processed without a named collection is stored under the
SHA-256 of its address (`backend/open_webui/routers/retrieval.py:2461-2463`).

## 4. Key Concepts and Terminology

| Term | Meaning here | Source |
|---|---|---|
| **Web search engine** (provider) | The outside service (or self-hosted search server) that turns a text query into a list of result links, titles and snippets. One engine is active at a time, chosen in `web.search.engine`. The code supports 32 engine identifiers; the admin drop-down offers 31 of them (`azure` is missing from the list) | `backend/open_webui/routers/retrieval.py:2511-2879`; `src/lib/components/admin/Settings/WebSearch.svelte:20-52` |
| **Search result** | One hit from the engine: `link`, `title`, `snippet` | `backend/open_webui/retrieval/web/main.py:47-50` |
| **Web loader** (loader engine) | The code that downloads each result page and extracts its text. Choices: **Default** (`''` or `safe_web`), `playwright`, `firecrawl`, `tavily`, `microsoft_web_iq`, `external` | `backend/open_webui/retrieval/web/utils.py:1049-1152`; `src/lib/components/admin/Settings/WebSearch.svelte:53`, `:1234-1244` |
| **Classic (legacy) web search** | The server-driven search step that runs before the model answers, when the model's function calling is `legacy` | `backend/open_webui/utils/middleware.py:2700-2709` |
| **Native web search tools** | `search_web` (returns titles, links and snippets) and `fetch_url` (returns a page's text) offered to a model in native function calling mode; the model decides whether to call them | `backend/open_webui/tools/builtin.py:294-362`; `backend/open_webui/utils/tools.py:677-685` |
| **Task model** | The model that writes search queries (the "query generation" task); configured with the other task settings, owned by `chat-completion-pipeline-and-generation-tasks.md` | `backend/open_webui/routers/tasks.py:438` |
| **Search query generation** | The task model is asked for one to three search queries in JSON, based on the last six chat messages; switch `task.query.search.enable` (on by default) | `backend/open_webui/config.py:2302`, `:2309-2331`, `:3146` |
| **Result count** | How many results are taken from the engine per query (`web.search.result_count`, default 3) | `backend/open_webui/config.py:1179` |
| **Domain filter list** | An allow or block list of site names applied to results; entries starting with `!` are blocked | `backend/open_webui/retrieval/web/main.py:11-44`; `backend/open_webui/utils/misc.py:73-89`, `:130-179` |
| **Bypass Web Loader** | Use only the engine's snippets; do not download the pages | `backend/open_webui/routers/retrieval.py:2960-2975` |
| **Bypass Embedding and Retrieval** (web) | Put the loaded pages into the prompt whole instead of embedding them and picking the best chunks. Separate from the Documents panel switch of the same name (`rag.bypass_embedding_and_retrieval`) | `backend/open_webui/routers/retrieval.py:2995-3009`; `backend/open_webui/config.py:1172-1174` |
| **Web-search collection** | The temporary vector collection that holds one search's pages, named `web-search-{user id}-{hash}` | `backend/open_webui/routers/retrieval.py:3011-3024` |
| **Source** | One retrieved page as the answer shows it under the reply and as `[1]`-style citations; general mechanics in `rag-retrieval-embeddings-and-vector-stores.md` | `backend/open_webui/retrieval/utils.py:1644-1647`, `:1702-1718` |
| **Attach Webpage** | Adding the text of one or more web addresses (or a YouTube video's transcript) to the next message | `src/lib/components/chat/Chat.svelte:1790-1866` |
| **Local web fetch** | Whether addresses that resolve to private or non-public network addresses may be fetched; environment variable `ENABLE_LOCAL_WEB_FETCH`, off by default | `backend/open_webui/config.py:1110-1118`; `backend/open_webui/retrieval/web/utils.py:124-128` |
| **Slim image** | A smaller Docker image (`USE_SLIM_DOCKER`) without DDGS (DuckDuckGo) search and without Playwright | `backend/open_webui/env.py:45`; `backend/open_webui/retrieval/web/duckduckgo.py:29-32`; `backend/open_webui/retrieval/web/utils.py:682-685` |
| **DDGS** | The `ddgs` Python library behind the `duckduckgo` engine; it needs no key, and its **DDGS Backend** setting picks which public engine it queries (Auto (Random), Bing, Brave, DuckDuckGo, Google, Grokipedia, Mojeek, Wikipedia, Yahoo, Yandex). The admin list shows the engine as **DDGS** | `backend/open_webui/retrieval/web/duckduckgo.py:34-44`; `src/lib/components/admin/Settings/WebSearch.svelte:219-220`, `:1102-1127` |

## 5. Workflows (Step by Step)

### 5.1 How a Web Search Is Triggered

A web search can only happen when the site-wide switch `web.search.enable` is on (code default off,
`backend/open_webui/config.py:1161`; the live value is data, **TO BE CONFIRMED**) and the user is an
admin or has `features.web_search`. Within that, the browser decides whether the message carries
`features.web_search = true` (`src/lib/components/chat/Chat.svelte:3409`):

| Trigger | What switches it on | Source |
|---|---|---|
| Composer switch | The user turns on **Web Search** in the **Integrations** menu; the chip stays until switched off | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:444-468` |
| Model default feature | When a model is selected and it has **Default Features** > **Web Search**, the switch is set from the model's `defaultFeatureIds`. This only happens when the model's `web_search` capability is explicitly on (an unset capability does not trigger it) | `src/lib/components/chat/Chat.svelte:1082-1098` |
| Personal setting **Web Search in Chat** set to always | Web search is active for every message as long as all selected models support it, even with the switch off | `src/lib/components/chat/Chat.svelte:342-355` |
| Link parameter `?web-search=true` | Switches it on for a new chat | `src/lib/components/chat/Chat.svelte:2172-2174` |
| Scheduled automations | An automation whose model has **Web Search** among its default features, with the capability on and web search on site-wide, sends `features.web_search` (owned by `background-processes-and-scheduling.md`) | `backend/open_webui/utils/automations.py:166-197`, `:302-318`, `:474-490` |

What happens next depends on the model's function calling mode (section 1):

- **Legacy**: the server runs the classic web-search step on every such message (5.3).
- **Native** (default): the model receives the `search_web` and `fetch_url` tools and decides for
  itself (5.9). With web search switched off, the tools are not offered at all
  (`backend/open_webui/utils/tools.py:682`), so the model has no built-in way to search.

### 5.2 The "Use Web Search?" Confirmation

When the admin switches on **Web Search Confirmation** (`web.search.confirmation.enable`, code
default off, `backend/open_webui/config.py:1163`):

1. Turning the switch on, or sending a message while web search is active, opens a dialog titled
   `Use Web Search?` (`src/lib/components/chat/Chat.svelte:4220-4235`, `:363-369`, `:3165-3173`).
2. Its text is the admin's **Web Search Confirmation Content** (`web.search.confirmation.content`);
   when that is blank the dialog shows `Your query will be sent to the configured web search
   provider.` (`src/lib/components/chat/Chat.svelte:4223-4225`). The seeded default of the setting
   is the same sentence (`backend/open_webui/config.py:1165-1168`).
3. **Continue** sends the pending message (or switches web search on) and remembers the answer for
   that chat until web search is turned off; **Cancel** switches web search off when it was being
   switched on, or drops the pending send (`src/lib/components/chat/Chat.svelte:371-379`, `:4130-4141`,
   `:4229-4234`).

The dialog is a browser check only (section 3.2). It is covered from the composer side in
`chat-composer-and-message-display.md` (section 5.7).

### 5.3 The Classic (Legacy) Web Search, Step by Step

This is `chat_web_search_handler` (`backend/open_webui/utils/middleware.py:1560-1730`), run before
the model is called:

1. **Status `Searching the web`** is shown under the reply being prepared (`:1562-1571`).
2. **Query generation** (5.4) produces a list of queries; on any failure the user's last message
   is used as the only query (`:1576-1626`).
3. If the list is empty, the status becomes `No search query generated` and the reply continues
   without a search (`:1629-1640`).
4. **Status "Searching"** shows each query as a chip (`:1642-1651`; text from
   `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:52-77`).
5. The queries go to `process_web_search` (`:1654-1658`), which:
   1. re-checks `web.search.enable` and the permission (section 3.2);
   2. sends every query to the configured engine, in parallel unless **Concurrent Requests**
      (`web.search.concurrent_requests`, default 0 = unlimited) limits it
      (`backend/open_webui/routers/retrieval.py:2903-2934`);
   3. collects the links, removes duplicates and keeps their order (`:2936-2943`);
   4. stops with HTTP 404 when no link came back (`:2953-2957`);
   5. loads the pages with the web loader, or uses the snippets only when **Bypass Web Loader** is
      on (5.6; `:2959-2985`);
   6. keeps only the results whose page actually loaded (`:2987-2993`);
   7. either returns the page texts directly (**Bypass Embedding and Retrieval** on) or embeds them
      into a `web-search-{user id}-{hash}` collection, replacing an earlier collection for the same
      user and the same queries (`:2995-3039`).
6. The result is added to the message as a `web_search` source item named after the queries
   (`backend/open_webui/utils/middleware.py:1660-1687`).
7. **Status `Searched {{count}} sites`**, where the count is the number of loaded pages; the line
   expands into the list of pages, each with its title (or address) and a favicon (`:1689-1700`;
   `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:15-39`;
   `src/lib/components/chat/Messages/ResponseMessage/WebSearchResults.svelte:61-141`).
8. If anything failed, the status line shows the error text instead and the reply still goes
   ahead without web results (`backend/open_webui/utils/middleware.py:1714-1728`; section 10).
9. Later in the same request the retrieval step searches the stored pages like any other source
   (5.7), shows `Querying` and `Retrieved {{count}} sources`, and the answer shows the pages as
   sources.

### 5.4 Query Generation

- The task model receives the default template (or the admin's `task.query.prompt_template`),
  which asks for "1-3 broad and relevant search queries" as JSON, gives today's date, and includes
  the last six messages of the chat (`{{MESSAGES:END:6}}`) (`backend/open_webui/config.py:2309-2331`;
  `backend/open_webui/routers/tasks.py:442-448`).
- If **Web Search Query Generation** (`task.query.search.enable`) is off, the task endpoint refuses
  with `{name} is disabled`, where `name` is `Search query generation`
  (`backend/open_webui/routers/tasks.py:406-411`), and the
  handler quietly falls back to the user's message as the query
  (`backend/open_webui/utils/middleware.py:1620-1622`).
- The answer is parsed from the last `{` to the last `}`; if it is not valid JSON the whole reply
  text becomes one query (`:1602-1615`).
- The template allows the model to return an empty list "if no search is unequivocally needed",
  which produces `No search query generated` (`backend/open_webui/config.py:2310`, `:2315`).
- With the environment variable `ENABLE_QUERIES_CACHE` on (default off), the generated queries are
  kept on the request and reused by the retrieval step instead of asking the task model twice
  (`backend/open_webui/env.py:370`; `backend/open_webui/utils/middleware.py:1617-1618`;
  `backend/open_webui/routers/tasks.py:419-421`).
- The task model, its settings and its failures are documented in
  `chat-completion-pipeline-and-generation-tasks.md`.

### 5.5 Calling the Search Engine

- `search_web` in the router picks the adapter for `web.search.engine` and passes the query, the
  result count and the domain filter list (`backend/open_webui/routers/retrieval.py:2511-2879`).
- Engines that need a key or address refuse with a message such as `No BRAVE_SEARCH_API_KEY found
  in environment variables` when it is empty (the wording says "environment variables" even when
  the value would come from the admin screen); an unknown or empty engine gives `No search engine
  API key found in environment variables` (`:2541-2879`). Section 10 lists every one.
- **Result count** (`web.search.result_count`, default 3) is sent to the engine as its maximum and
  most adapters also cut the list to it. Exceptions: Jina caps at 10 per request; Google PSE pages
  through results ten at a time; Sougou always asks for 20 and then cuts
  (`backend/open_webui/retrieval/web/jina_search.py:33`; `backend/open_webui/retrieval/web/google_pse.py:29-54`;
  `backend/open_webui/retrieval/web/sougou.py:31`, `:47`). Because each query is searched
  separately, one message can load up to *result count × number of queries* pages.
- **Domain filter** (5.13) is applied by most adapters after the results arrive; some adapters do
  not apply it (provider table, section 7.3).
- **Errors.** Twenty-two adapters let an error propagate, so the search fails with an error
  status. Ten log it and return an empty list instead, which the user sees as "no results": Exa,
  External, Firecrawl, Microsoft Web IQ, Ollama Cloud, Perplexity, Perplexity Search and Yandex
  always; Sougou for Tencent Cloud errors; SerpApi when the service answers with an error body
  (provider table, section 7.3).

### 5.6 Loading the Result Pages

When **Bypass Web Loader** (`web.search.bypass_web_loader`, default off) is on, no page is
downloaded: each result's snippet becomes the page text, and results without a snippet are dropped
(`backend/open_webui/routers/retrieval.py:2960-2975`). Otherwise `get_web_loader` builds the loader
named in `web.loader.engine` (`backend/open_webui/retrieval/web/utils.py:1049-1152`):

| Engine value | Admin label | How a page is read | Settings it uses | Source |
|---|---|---|---|---|
| `''` or `safe_web` | **Default** | The Open WebUI server downloads the page itself and extracts its text with BeautifulSoup (title, description and language kept as metadata). Up to **Concurrent Requests** pages at once; up to three attempts per page on connection errors, waiting 2 s then 3 s | `web.loader.timeout` (seconds, optional), `web.loader.ssl_verification`, `web.loader.concurrent_requests`, `web.search.trust_env`; environment `USER_AGENT` | `backend/open_webui/retrieval/web/utils.py:932-1046`, `:1083-1097` |
| `playwright` | `playwright` | A Chromium browser (local, or remote through **Playwright WebSocket URL**) opens the page; images, fonts and media are not fetched; the page HTML is turned into text with the `unstructured` library. Pages are loaded one after another, spaced by the concurrency value used as a per-second rate | `web.loader.playwright_ws_url`, `web.loader.playwright_timeout` (milliseconds, default 10000), `web.loader.ssl_verification`, `web.loader.concurrent_requests`, `web.search.trust_env` | `backend/open_webui/retrieval/web/utils.py:651-929`, `:1099-1104` |
| `firecrawl` | `firecrawl` | Each address is sent to the Firecrawl service (`/v2/scrape`), which returns Markdown; retried twice on HTTP 429 or 5xx | `web.loader.firecrawl_api_url` (default `https://api.firecrawl.dev`), `web.loader.firecrawl_api_key`, `web.loader.firecrawl_timeout` (seconds; clamped to 1-300 s for the scrape) | `backend/open_webui/retrieval/web/utils.py:398-473`, `:1106-1115`; `backend/open_webui/retrieval/web/firecrawl.py:137-177` |
| `tavily` | `tavily` | Addresses are sent in batches of 20 to Tavily's Extract service | `web.search.tavily_api_key` (shared with the Tavily search engine), `web.search.tavily_extract_depth` (`basic` or `advanced`); environment `TAVILY_API_BASE_URL` | `backend/open_webui/retrieval/web/utils.py:476-585`, `:1117-1120`; `backend/open_webui/retrieval/loaders/tavily.py:12-92` |
| `microsoft_web_iq` | `microsoft_web_iq` | Each address is sent to the Microsoft Web IQ `/browse` service, which returns Markdown; retried twice on HTTP 202, 429 or 5xx | `web.search.microsoft_web_iq_api_base_url`, `web.search.microsoft_web_iq_api_key`, `web.search.microsoft_web_iq_language` (shared with the engine), `web.loader.timeout` (seconds, default 60) | `backend/open_webui/retrieval/web/utils.py:588-648`, `:1122-1131`; `backend/open_webui/retrieval/loaders/microsoft_web_iq.py:17-109` |
| `external` | `external` | Addresses are posted in batches of 20 to an admin-supplied service that returns the text | `web.loader.external_web_loader_url`, `web.loader.external_web_loader_api_key` | `backend/open_webui/retrieval/web/utils.py:1133-1136`; `backend/open_webui/retrieval/loaders/external_web.py:11-54` |

Points that matter for support:

- **Every address is checked first** (5.12). If every address is refused, the loader is not built
  and the search fails (`backend/open_webui/retrieval/web/utils.py:1056-1061`).
- **One failed page does not stop the others**: every loader is built with
  `continue_on_failure=True`, so failures are logged and skipped
  (`backend/open_webui/retrieval/web/utils.py:1073-1079`). With the Default loader a failed page
  still produces an empty document for its address
  (`backend/open_webui/retrieval/web/utils.py:973-983`, `:1037-1042`), so it counts in
  `Searched {{count}} sites` although it contributed no text.
- **Redirects are not followed** unless the environment variable `AIOHTTP_CLIENT_ALLOW_REDIRECTS`
  is on (default off, `backend/open_webui/env.py:636-637`); the Default loader passes this to
  every request (`backend/open_webui/retrieval/web/utils.py:952`), so a page that only redirects
  yields whatever the redirect response itself contains.
- **SSL verification** (`web.loader.ssl_verification`, default on): the Default loader verifies
  the page's certificate during the download; Playwright, Tavily and Microsoft Web IQ first make a
  separate test connection to port 443 of each `https://` address using the certifi bundle and skip
  the page if it fails; Firecrawl is told to skip verification when the switch is off
  (`backend/open_webui/retrieval/web/utils.py:340-355`, `:383-395`, `:994-997`;
  `backend/open_webui/retrieval/web/firecrawl.py:149`). The **Verify SSL Certificate** switch is
  only displayed for the Default loader, but the stored value applies to all of them
  (`src/lib/components/admin/Settings/WebSearch.svelte:1247-1268`; `backend/open_webui/routers/retrieval.py:2980`).
- **Trust Proxy Environment** (`web.search.trust_env`, default on) lets the loader use the
  server's proxy environment variables (`backend/open_webui/routers/retrieval.py:2982`). It is
  passed only to the web loader, not to the search engine calls.
- **Playwright** needs the `playwright` and `unstructured` packages and a browser. The slim image
  refuses it with `Playwright is unavailable in slim. Use basic HTTP fetching or an external web
  loader.` (`backend/open_webui/retrieval/web/utils.py:682-688`). The `Dockerfile` has no step that
  installs a Playwright browser; the repository's `docker-compose.playwright.yaml` instead runs a
  separate Playwright server and sets `WEB_LOADER_ENGINE=playwright` and
  `PLAYWRIGHT_WS_URL=ws://playwright:3000`. Which arrangement production uses is **TO BE CONFIRMED**.
- An unrecognized engine value fails with `Invalid WEB_LOADER_ENGINE: {engine}. Please set it to
  'safe_web', 'playwright', 'firecrawl', 'tavily', 'external', or 'microsoft_web_iq'.`
  (`backend/open_webui/retrieval/web/utils.py:1148-1152`).

### 5.7 Embedding Versus Bypass: How Results Enter the Prompt

| Mode | What is stored | What the model receives | Source |
|---|---|---|---|
| Default (**Bypass Embedding and Retrieval** off) | The page texts are split, embedded and saved in `web-search-{user id}-{hash}` using the Documents settings (chunk size, embedding model) | The retrieval step searches that collection with freshly generated retrieval queries (or the user's message) and adds only the best chunks, **Top K** from the Documents panel (`rag.top_k`, default 3), through the RAG template | `backend/open_webui/routers/retrieval.py:3010-3039`; `backend/open_webui/utils/middleware.py:2060-2135`; `backend/open_webui/retrieval/utils.py:1644-1647` |
| **Bypass Embedding and Retrieval** on (`web.search.bypass_embedding_and_retrieval`) | Nothing | Every loaded page's full text | `backend/open_webui/routers/retrieval.py:2995-3009`; `backend/open_webui/retrieval/utils.py:1638-1643` |

- If the documents panel's **Full Context Mode** (`rag.full_context`) is on, the whole web-search
  collection is used instead of the best chunks (`backend/open_webui/utils/middleware.py:2133`;
  `backend/open_webui/retrieval/utils.py:1680-1683`).
- The retrieval step runs only when the model's `file_context` capability is on (default on)
  (`backend/open_webui/utils/middleware.py:3206-3214`). With it off, a legacy search still runs and
  shows `Searched {{count}} sites`, but the results are not added to the prompt (section 14).
- If saving to the vector store fails, the search ends with `Failed to embed and store the
  retrieved web pages. Check the embedding configuration in Admin Settings > Documents.`
  (`backend/open_webui/routers/retrieval.py:3025-3031`). This also happens when every loaded page
  was empty, because the store refuses empty content
  (`backend/open_webui/routers/retrieval.py:1819-1820`).
- How the RAG template inserts sources and how `[1]` citations and source chips are drawn are in
  `rag-retrieval-embeddings-and-vector-stores.md` (sections 5.10 and 5.11).

### 5.8 What the User Sees During a Search

| Moment | Text | Source |
|---|---|---|
| Search starts (legacy) | `Searching the web` | `backend/open_webui/utils/middleware.py:1567`; `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:142-143` |
| Queries ready | `Searching` with one chip per query | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:52-77` |
| Pages loaded | `Searched {{count}} sites` (click to list the pages; each opens in a new tab) | `backend/open_webui/utils/middleware.py:1694`; `src/lib/components/chat/Messages/ResponseMessage/WebSearchResults.svelte:61-141` |
| Retrieval over the pages | `Querying` with chips, then `Retrieved {{count}} sources`, `Retrieved 1 source` or `No sources found` | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:78-125` |
| Failure | The error text on the status line (section 10) | `backend/open_webui/utils/middleware.py:1701-1728` |
| Native mode | A collapsible tool-call block for each `search_web` or `fetch_url` call, with its arguments and result | `src/lib/components/common/ToolCallDisplay.svelte:176-199` |

The status lines are hidden when the model's `status_updates` capability is off or when the user
has the fork's **Hide Processing Details** setting on; the user then sees "Thinking..." until the
answer starts (`src/lib/components/chat/Messages/ResponseMessage.svelte:197-221`, `:720-721`;
section 12). Tool-call blocks are likewise hidden with that setting unless they wait for the user
(`src/lib/components/common/ToolCallDisplay.svelte:145`, `:199`).

### 5.9 Native Mode: The Model Searches by Itself

1. When the five gates in section 3.2 pass, the model is offered `search_web` and `fetch_url`
   (`backend/open_webui/utils/tools.py:677-685`). Their descriptions tell the model that
   `search_web` is "Best for current events, external references, or topics not covered in internal
   documents" and that `fetch_url` will "Fetch and extract the main text content from a web page URL"
   (`backend/open_webui/tools/builtin.py:300-306`, `:338-342`).
2. `search_web(query, count)` sends **one** query, exactly as the model wrote it, to the configured
   engine. `count` is capped at `web.search.result_count` (5 if that setting is empty). It returns
   only titles, links and snippets as JSON; no page is downloaded and nothing is stored
   (`backend/open_webui/tools/builtin.py:294-330`). It calls the engine adapter directly, so the
   `/process/web/search` checks, the loader and the embedding step are not involved.
3. `fetch_url(url)` loads one page with the configured web loader, or a file such as a PDF through
   the document extraction pipeline, and returns the text, cut at **Fetch URL Content Length Limit**
   (`web.fetch.max_content_length`, empty = no limit) with `[Content truncated...]` appended
   (`backend/open_webui/tools/builtin.py:333-362`; `backend/open_webui/retrieval/utils.py:245-300`).
4. Failures are returned to the model as `{"error": "..."}` (for example the engine's "No ... found
   in environment variables" message or the invalid-address message); the model usually reports
   them in its answer (`backend/open_webui/tools/builtin.py:328-330`, `:360-362`).
5. Sources: each successful `fetch_url` result becomes a source chip named after the address, with
   the first 500 characters as the excerpt, when the model's `citations` capability is on (default
   on). `search_web` results do not become source chips
   (`backend/open_webui/utils/middleware.py:464-481`, `:5841-5843`, `:6090-6109`).
6. The domain filter list applies to `search_web` (it goes through the engine adapters) but **not**
   to `fetch_url`, which only applies the address checks in 5.12 (`backend/open_webui/retrieval/utils.py:254-258`).

The built-in tool system, tool approval and the tool-call display are in `builtin-native-tools.md`.

### 5.10 Attaching a Web Page by Address

1. The user chooses **+** > **Attach Webpage**, types one or more addresses (one per line) and
   presses **Add** (`src/lib/components/chat/MessageInput/AttachWebpageModal.svelte:40-93`).
2. The browser keeps only well-formed `http`/`https` addresses and removes duplicates; if none is
   left it shows `Please enter a valid URL.` (`src/lib/components/chat/MessageInput/AttachWebpageModal.svelte:20-32`;
   `src/lib/utils/index.ts:977-987`).
3. Each address appears as a chip in the composer while it loads and is sent to
   `POST /api/v1/retrieval/process/url` (`src/lib/components/chat/Chat.svelte:1800-1816`).
4. The server (`backend/open_webui/routers/retrieval.py:2356-2426`):
   - sends a YouTube address to the transcript loader (5.11);
   - otherwise checks the address (5.12) and starts downloading it (`:2245-2273`); redirects are
     not followed unless `AIOHTTP_CLIENT_ALLOW_REDIRECTS` is on, and an HTTP error status from the
     site stops here;
   - for an HTML page, loads it with the configured web loader and, unless **Bypass Embedding and
     Retrieval** (web) is on, saves it in the vector store under the SHA-256 of the address
     (`:2429-2495`);
   - for an image or any other file type, uploads it as a normal file with the address recorded as
     `source_url` (`:2389-2418`); file handling is in `files-uploads-and-storage.md`;
   - refuses anything larger than **Max Upload Size** (`rag.file.max_size`) with the file-too-large
     message (`:2283-2311`).
5. On success the chip shows the page; when the message is sent, the page's full text is added
   (the chip is a `text` item with `context: 'full'`) (`src/lib/components/chat/Chat.svelte:1801-1809`;
   `backend/open_webui/retrieval/utils.py:1411-1422`).
6. On failure the chip is removed and a red pop-up shows the server's message
   (`src/lib/components/chat/Chat.svelte:1857-1862`; section 10).

The same window on a knowledge base page adds pages to that knowledge base
(`src/lib/components/workspace/Knowledge/KnowledgeBase.svelte:303`, `:1172-1176`; owned by
`knowledge-bases.md`).

### 5.11 YouTube Transcripts

1. An address is treated as YouTube when it matches `youtube.com/...` or `youtu.be/...`, with or
   without `www.` (`backend/open_webui/retrieval/utils.py:77-79`). It skips the web loader entirely
   (`backend/open_webui/retrieval/utils.py:266-270`).
2. The 11-character video id is taken from `watch?v=` or from the last part of the path
   (`backend/open_webui/retrieval/loaders/youtube.py:47-74`).
3. The `youtube-transcript-api` library asks YouTube for the list of transcripts, through **Youtube
   Proxy URL** (`rag.youtube_loader_proxy_url`) when set (`backend/open_webui/retrieval/loaders/youtube.py:117-128`).
4. Languages are tried in the order of **Youtube Language** (`rag.youtube_loader_language`, default
   `en`), with English added at the end when it is not already listed; a manually written
   transcript is preferred over an automatic one in the same language (`backend/open_webui/retrieval/loaders/youtube.py:92-100`,
   `:130-168`; `backend/open_webui/config.py:1152`).
5. The transcript text (without timestamps) becomes the attachment. Failures produce the messages
   in section 10 (`backend/open_webui/retrieval/loaders/youtube.py:25-44`, `:170-177`).

The admin API also accepts a `YOUTUBE_LOADER_TRANSLATION` value, but it is kept only in the memory
of the server process that saved it, starts empty on every restart and is not used by the loader
(`backend/open_webui/main.py:670`; `backend/open_webui/routers/retrieval.py:781`, `:1390`).

### 5.12 Address Checks Before Any Download

Every address is checked before the web loaders, the attachment path or `fetch_url` download it
(`backend/open_webui/retrieval/web/utils.py:131-183`; `backend/open_webui/routers/retrieval.py:2246`;
`backend/open_webui/retrieval/utils.py:258`). An address is refused with `The URL you provided is
invalid. Please double-check and try again.` when it:

- is not a well-formed `http` or `https` address;
- names a host that does not resolve (unless local web fetch is on);
- resolves to a private or otherwise non-public network address, unless the environment variable
  `ENABLE_LOCAL_WEB_FETCH` is on (default off, `backend/open_webui/config.py:1110-1118`);
- matches the environment-only `WEB_FETCH_FILTER_LIST`, which is merged with a built-in block list
  (`backend/open_webui/config.py:1121-1149`).

In practice this means pages whose address resolves to a private network address (for example an
intranet site) are refused for attachments, searches and `fetch_url` unless the platform enables
local web fetch. The detailed protections are security-sensitive: refer to the platform maintainer
and U of T Information Security (security.utoronto.ca).

### 5.13 The Domain Filter List

- Typed in the admin panel as a comma-separated list, for example
  `example.com,site.org,!excludedsite.com` (placeholder text), and saved as a list
  (`src/lib/components/admin/Settings/WebSearch.svelte:61-72`, `:1183-1194`).
- Entries without `!` form an **allow list**: when at least one exists, only results whose host is
  that name or a sub-domain of it are kept (matching is on whole name parts, so `utoronto.ca`
  matches `www.utoronto.ca` but not `notutoronto.ca`). Results matching an entry with `!` are
  removed even when they also match an allow entry (`backend/open_webui/utils/misc.py:73-89`, `:130-179`).
- Entries that are IP addresses or ranges are compared with the result host's resolved addresses
  (`backend/open_webui/retrieval/web/main.py:16-38`).
- When any filter is set, results whose link is not a valid address are dropped
  (`backend/open_webui/retrieval/web/main.py:22-24`).
- The list filters search **results**; it does not stop `fetch_url` or **Attach Webpage** from
  loading other sites (5.9, 5.10). Adapters that do not apply it are listed in section 7.3.

### 5.14 What Leaves the Server (Privacy)

| What | Where it goes | When | Source |
|---|---|---|---|
| The last six chat messages | The task model (which may be an outside provider) | Query generation, legacy mode | `backend/open_webui/config.py:2327-2330`; `backend/open_webui/routers/tasks.py:448-471` |
| Search queries | The configured engine (a third-party service, or a self-hosted server for SearXNG, YaCy, OpenSERP or External) | Every search, both modes | Section 7.3 |
| The user's name, id, email and role (as `X-OpenWebUI-User-*` headers, or one signed token when `FORWARD_USER_INFO_HEADER_JWT_SECRET` is set) | The engine | Only for the `external`, `yandex`, `perplexity_search` and `microsoft_web_iq` engines. For these four the code adds the headers whenever a user is known and does not consult `ENABLE_FORWARD_USER_INFO_HEADERS` (default off), the switch that governs forwarding elsewhere | `backend/open_webui/retrieval/web/external.py:30`; `backend/open_webui/retrieval/web/yandex.py:51-52`; `backend/open_webui/retrieval/web/perplexity_search.py:50-52`; `backend/open_webui/retrieval/web/microsoft_web_iq.py:29-30`; `backend/open_webui/utils/headers.py:52-82`; `backend/open_webui/env.py:989-1002` |
| The chat id (`X-OpenWebUI-Chat-Id` header) | The engine | `external` and `yandex` engines, when the request has a chat | `backend/open_webui/retrieval/web/external.py:32-34`; `backend/open_webui/retrieval/web/yandex.py:54-56` |
| Result page addresses | Firecrawl, Tavily, Microsoft Web IQ or the external loader service, when that loader is chosen; otherwise the websites themselves, contacted from the server. With Playwright and a **Playwright WebSocket URL**, the remote browser also receives each address and page, although the server makes the actual requests | Page loading | 5.6; `backend/open_webui/retrieval/web/utils.py:735-790`, `:856-859` |
| Request headers to websites (Default loader) | The websites | Page loading | `User-Agent` from `USER_AGENT` (else `DefaultLangchainUserAgent`), `Accept-Language: en-US,en;q=0.5`, `Referer: https://www.google.com/`, `DNT: 1` (`backend/open_webui/retrieval/web/utils.py:960-968`) |
| Result site names | Google's favicon service, contacted by the **user's browser** | When the user expands `Searched {{count}} sites` | `src/lib/components/chat/Messages/ResponseMessage/WebSearchResults.svelte:70-71`, `:110-111` |
| YouTube video id | YouTube (directly or through the YouTube proxy) | YouTube attachments | `backend/open_webui/retrieval/loaders/youtube.py:117-125` |

Inside MedIT GPT, the queries and the result titles, links and snippets are saved with the chat
(section 6), and page text is kept in the vector store (section 8). Whether sending chat-derived
queries and user identity to these services is acceptable for MedIT GPT is **TO BE CONFIRMED**
with the platform owner and the U of T Privacy Office (section 14).

### 5.15 Timeouts and Limits

| What | Limit | Source |
|---|---|---|
| Results per query | `web.search.result_count`, default 3 | `backend/open_webui/config.py:1179` |
| Queries sent at once | `web.search.concurrent_requests`, default 0 (no limit); also sets DDGS threads | `backend/open_webui/config.py:1196`; `backend/open_webui/routers/retrieval.py:2903-2934`; `backend/open_webui/retrieval/web/duckduckgo.py:41-42` |
| Pages loaded at once (Default loader) or per second (Playwright, Firecrawl, Tavily, Web IQ) | `web.loader.concurrent_requests`, default 10 | `backend/open_webui/config.py:1205`; `backend/open_webui/retrieval/web/utils.py:358-375`, `:970-983` |
| Default loader per-page time | `web.loader.timeout` in seconds; empty = no Open WebUI limit (the HTTP library's own default applies) | `backend/open_webui/config.py:1207`; `backend/open_webui/retrieval/web/utils.py:1083-1097` |
| Playwright page time | `web.loader.playwright_timeout`, default 10000 ms | `backend/open_webui/config.py:1313`; `backend/open_webui/retrieval/web/utils.py:873`, `:913` |
| Firecrawl scrape time | `web.loader.firecrawl_timeout` seconds, clamped 1-300 s; the HTTP wait is that plus 10 s (70 s when unset) | `backend/open_webui/retrieval/web/firecrawl.py:37-60` |
| Firecrawl search | `count × 3` seconds at Firecrawl, `count × 3 + 10` seconds locally | `backend/open_webui/retrieval/web/firecrawl.py:192-199` |
| Microsoft Web IQ browse | `web.loader.timeout` seconds, else 60 s | `backend/open_webui/retrieval/loaders/microsoft_web_iq.py:61-65` |
| Engine calls | Bocha 5 s; Linkup and SearchApi 30 s; engines on the shared connection pool (Brave, Google PSE, SearXNG, Serper, SERPHouse, Serpstack, OpenSERP) use `AIOHTTP_CLIENT_TIMEOUT` (empty = no limit); the others set no timeout | `backend/open_webui/retrieval/web/bocha.py:46`; `backend/open_webui/retrieval/web/linkup.py:47`; `backend/open_webui/retrieval/web/searchapi.py:33`; `backend/open_webui/utils/session_pool.py:43`, `:54-75`; `backend/open_webui/env.py:608-612` |
| Content-type probe of an attached or fetched address | 30 s | `backend/open_webui/retrieval/utils.py:279-280` |
| Download size for attached files | `rag.file.max_size` (MB) | `backend/open_webui/routers/retrieval.py:2245-2311`; `backend/open_webui/retrieval/utils.py:201-212` |
| `fetch_url` text length | `web.fetch.max_content_length`, empty = no limit | `backend/open_webui/tools/builtin.py:350-355` |
| Brave LLM Context size | `web.search.brave_search_context_tokens`, default 8192 (field allows 1024-32768) | `backend/open_webui/config.py:1234`; `src/lib/components/admin/Settings/WebSearch.svelte:434-449` |

## 6. Data Model

Web search has no table of its own. It reads settings, writes to the chat record and the vector
store, and keeps a little state in memory.

### 6.1 Settings Rows

All persistent settings are rows in the `config` table (one row per dotted key; see
`knowledgebase/tools/ground-truth.md`, Settings). This area owns the **78 `web.*` keys**
(`backend/open_webui/config.py:2941-3018`), listed with their admin labels in section 7. It also
reads `rag.youtube_loader_language`, `rag.youtube_loader_proxy_url` (`:2939-2940`),
`task.query.search.enable`, `task.query.prompt_template` (`:3146-3148`), `user.permissions`
(`features.web_search`, `chat.web_upload`), `webui.url` (sent as the Google PSE referrer),
`rag.top_k`, `rag.full_context` and `rag.file.max_size`. The router reads them all in one call
through its key map (`backend/open_webui/routers/retrieval.py:254-443`); the loaders read theirs
through `LOADER_CONFIG_KEYS` (`backend/open_webui/retrieval/utils.py:82-144`).

### 6.2 What a Search Leaves in the Chat

| Where | What is stored | Source |
|---|---|---|
| The assistant message's `statusHistory` (inside the chat JSON) | Each status event: `action` (`web_search`, `web_search_queries_generated`, `queries_generated`, `sources_retrieved`), `description`, `queries`, `urls`, `items` (title, link and snippet of each kept result), `done`, `error` | `backend/open_webui/utils/middleware.py:1562-1728`; `backend/open_webui/socket/main.py:1166-1170`; `backend/open_webui/models/chats.py:1239-1268` |
| `chat_message.status_history` | The per-message table's copy of the list, filled when the message row is written (when that happens is owned by `chat-completion-pipeline-and-generation-tasks.md`) | `backend/open_webui/models/chat_messages.py:154`, `:233-234` |
| The assistant message's `sources` | The web results used in the answer; the source item carries `type: 'web_search'`, `name` (the queries joined by commas), `urls`, `queries` and the collection name | `backend/open_webui/utils/middleware.py:1663-1687`, `:3232-3246`; storage owned by `chat-completion-pipeline-and-generation-tasks.md` |
| A user message's attached files | An attached page is a `text` item with the address as `name` and `url`, the page text in `file.data.content`, and `context: 'full'` | `src/lib/components/chat/Chat.svelte:1801-1853` |

Search queries are derived from the conversation and result snippets come from third-party sites;
both therefore sit inside the chat record with the rest of the conversation and should be handled
like chat content.

### 6.3 Collections in the Vector Store

| Collection name | Holds | Written by | Source |
|---|---|---|---|
| `web-search-{user id}-{SHA-256 of the queries joined by "-"}`, cut to 63 characters | One search's loaded pages, chunked and embedded; replaced when the same user runs the same queries again | `process_web_search` | `backend/open_webui/routers/retrieval.py:3011-3024` |
| First 63 characters of the SHA-256 of the address | One attached web page or YouTube transcript | `process_web` | `backend/open_webui/routers/retrieval.py:2460-2477` |

Chunk metadata includes `source` (the page address) and, depending on the loader, `title`,
`description` and `language` (`backend/open_webui/retrieval/web/utils.py:329-337`); the general
chunk layout is in `rag-retrieval-embeddings-and-vector-stores.md` (section 6.3). The
multi-tenant Milvus and Qdrant back ends store all web-search collections in one shared collection
(`backend/open_webui/retrieval/vector/dbs/milvus_multitenancy.py:75`, `:102`;
`backend/open_webui/retrieval/vector/dbs/qdrant_multitenancy.py:88`, `:125`).

### 6.4 State Held in Server Memory

| Item | Lifetime | Source |
|---|---|---|
| `app.state.YOUTUBE_LOADER_TRANSLATION` | Per process; reset to empty at start; not used by the loader | `backend/open_webui/main.py:670`; `backend/open_webui/routers/retrieval.py:1390` |
| `request.state.cached_queries` | One chat request, when `ENABLE_QUERIES_CACHE` is on | `backend/open_webui/utils/middleware.py:1617-1618` |
| The shared HTTP connection pool used by the asynchronous engines | Per process | `backend/open_webui/utils/session_pool.py:54-75` |

## 7. Settings and Configuration

Every value below is a code default or a seed. After first start the value stored in the `config`
table wins over the environment variable (`knowledgebase/tools/ground-truth.md`, Settings); **the
live values in production are data and TO BE CONFIRMED**. Labels are the English text of the
`settings.admin.web.*` keys (`src/lib/i18n/locales/en-US/translation.json:2642-2735`) unless
quoted otherwise. Provider keys and passwords are entered in masked fields and are returned to
admins by `GET /api/v1/retrieval/config`; this document never reproduces a value.

### 7.1 Admin Settings > Web Search > Search

| Label (description) | Key | Seeded from | Code default | Notes | Source |
|---|---|---|---|---|---|
| **Web Search** ("Allow users to search the web from chats.") | `web.search.enable` | `ENABLE_WEB_SEARCH` | off | Master switch; also hides the composer switch when off | `backend/open_webui/config.py:1161`; `src/lib/components/admin/Settings/WebSearch.svelte:174-180` |
| **Web Search Confirmation** ("Require users to confirm before using Web Search.") | `web.search.confirmation.enable` | `ENABLE_WEB_SEARCH_CONFIRMATION` | off | Browser-side dialog (5.2) | `backend/open_webui/config.py:1163`; `src/lib/components/admin/Settings/WebSearch.svelte:182-191` |
| **Web Search Confirmation Content** ("Message shown before web search runs.") | `web.search.confirmation.content` | `WEB_SEARCH_CONFIRMATION_CONTENT` | `Your query will be sent to the configured web search provider.` | Shown only while confirmation is on | `backend/open_webui/config.py:1165-1168`; `src/lib/components/admin/Settings/WebSearch.svelte:193-206` |
| **Web Search Engine** ("Choose the provider used for web search queries.") | `web.search.engine` | `WEB_SEARCH_ENGINE` | empty | Drop-down of 31 engine ids (7.3); required before the page can be saved; DDGS is greyed out in the slim image | `backend/open_webui/config.py:1170`; `src/lib/components/admin/Settings/WebSearch.svelte:208-228` |
| *Engine-specific fields* | see 7.3 | | | Shown for the selected engine only | `src/lib/components/admin/Settings/WebSearch.svelte:230-1128` |
| **Search Limits** ("Control result volume and parallel search requests.") > **Search Result Count** | `web.search.result_count` | `WEB_SEARCH_RESULT_COUNT` | 3 | Required; free text box | `backend/open_webui/config.py:1179`; `src/lib/components/admin/Settings/WebSearch.svelte:1131-1147` |
| **Search Limits** > **Concurrent Requests** (tooltip: "Limit concurrent search queries. 0 = unlimited (default). Set to 1 for sequential execution (recommended for APIs with strict rate limits like Brave free tier).") | `web.search.concurrent_requests` | `WEB_SEARCH_CONCURRENT_REQUESTS` | 0 | The tooltip text is stored under the key `settings.admin.web.searchResultCount.description` | `backend/open_webui/config.py:1196`; `src/lib/components/admin/Settings/WebSearch.svelte:1149-1166`; `src/lib/i18n/locales/en-US/translation.json:2691` |
| **Fetch URL Content Length Limit** ("Maximum characters to return from fetched URLs. Leave empty for no limit.") | `web.fetch.max_content_length` | `WEB_FETCH_MAX_CONTENT_LENGTH` | empty (no limit) | Applies to the `fetch_url` tool only | `backend/open_webui/config.py:1198-1200`; `src/lib/components/admin/Settings/WebSearch.svelte:1170-1181` |
| **Domain Filter List** ("Restrict or exclude domains using a comma-separated list.") | `web.search.domain.filter_list` | `WEB_SEARCH_DOMAIN_FILTER_LIST` (a JSON list) | empty list | Syntax in 5.13 | `backend/open_webui/config.py:1182-1194`; `src/lib/components/admin/Settings/WebSearch.svelte:1183-1194` |
| **Bypass Embedding and Retrieval** (on: "Inject the entire content as context for comprehensive processing."; off: `Use segmented retrieval for focused and relevant content extraction.`) | `web.search.bypass_embedding_and_retrieval` | `BYPASS_WEB_SEARCH_EMBEDDING_AND_RETRIEVAL` | off | 5.7; also skips storing attached pages | `backend/open_webui/config.py:1172-1174`; `src/lib/components/admin/Settings/WebSearch.svelte:1197-1208` |
| **Bypass Web Loader** ("Use search results without fetching page contents.") | `web.search.bypass_web_loader` | `BYPASS_WEB_SEARCH_WEB_LOADER` | off | 5.6 | `backend/open_webui/config.py:1177`; `src/lib/components/admin/Settings/WebSearch.svelte:1210-1216` |
| **Trust Proxy Environment** (on: "Use proxy environment variables to fetch page contents."; off: `Fetch page contents without proxy environment variables.`) | `web.search.trust_env` | `WEB_SEARCH_TRUST_ENV` | on | Loader only | `backend/open_webui/config.py:1212`; `src/lib/components/admin/Settings/WebSearch.svelte:1218-1226` |

**Search Limits**, **Fetch URL Content Length Limit** and **Domain Filter List** are displayed only
while **Web Search** is on (`src/lib/components/admin/Settings/WebSearch.svelte:1130`, `:1195`).

### 7.2 Admin Settings > Web Search > Loader

| Label (description) | Key | Seeded from | Code default | Shown when | Source |
|---|---|---|---|---|---|
| **Web Loader Engine** ("Choose how web result pages are fetched and read.") | `web.loader.engine` | `WEB_LOADER_ENGINE` | empty (**Default**) | Always; options **Default**, `playwright` (greyed out in slim), `firecrawl`, `tavily`, `microsoft_web_iq`, `external` | `backend/open_webui/config.py:1202`; `src/lib/components/admin/Settings/WebSearch.svelte:1230-1245` |
| **Timeout** ("Maximum time to wait while loading web content.") | `web.loader.timeout` | `WEB_LOADER_TIMEOUT` | empty | Default loader; seconds (also used by the Microsoft Web IQ loader) | `backend/open_webui/config.py:1207`; `src/lib/components/admin/Settings/WebSearch.svelte:1247-1257` |
| **Verify SSL Certificate** ("Validate SSL certificates when fetching web content.") | `web.loader.ssl_verification` | `ENABLE_WEB_LOADER_SSL_VERIFICATION` | on | Default loader (the value applies to every loader, 5.6) | `backend/open_webui/config.py:1210`; `src/lib/components/admin/Settings/WebSearch.svelte:1259-1268` |
| **Playwright WebSocket URL** | `web.loader.playwright_ws_url` | `PLAYWRIGHT_WS_URL` | empty (local browser) | `playwright` | `backend/open_webui/config.py:1311`; `src/lib/components/admin/Settings/WebSearch.svelte:1269-1288` |
| **Playwright Timeout (ms)** | `web.loader.playwright_timeout` | `PLAYWRIGHT_TIMEOUT` | 10000 | `playwright` | `backend/open_webui/config.py:1313`; `src/lib/components/admin/Settings/WebSearch.svelte:1289-1304` |
| **Firecrawl API Base URL**, **Firecrawl API Key** | `web.loader.firecrawl_api_url`, `web.loader.firecrawl_api_key` | `FIRECRAWL_API_BASE_URL`, `FIRECRAWL_API_KEY` | `https://api.firecrawl.dev`, empty | `firecrawl`, unless the engine is also Firecrawl (then they are in the engine block) | `backend/open_webui/config.py:1315-1317`; `src/lib/components/admin/Settings/WebSearch.svelte:1306-1337` |
| **Tavily Extract Depth**, **Tavily API Key** | `web.search.tavily_extract_depth`, `web.search.tavily_api_key` | `TAVILY_EXTRACT_DEPTH`, `TAVILY_API_KEY` | `basic`, empty | `tavily`; the key field is hidden when the engine is also Tavily | `backend/open_webui/config.py:1301-1303`; `src/lib/components/admin/Settings/WebSearch.svelte:1338-1371` |
| **Microsoft Web IQ API Base URL**, **Microsoft Web IQ API Key**, **Language** | `web.search.microsoft_web_iq_api_base_url`, `..._api_key`, `..._language` | `MICROSOFT_WEB_IQ_API_BASE_URL`, `..._API_KEY`, `..._LANGUAGE` | `https://api.microsoft.ai/v3`, empty, `en` | `microsoft_web_iq`, unless the engine is also Microsoft Web IQ | `backend/open_webui/config.py:1291-1295`; `src/lib/components/admin/Settings/WebSearch.svelte:1372-1419` |
| **External Web Loader URL**, **External Web Loader API Key** | `web.loader.external_web_loader_url`, `web.loader.external_web_loader_api_key` | `EXTERNAL_WEB_LOADER_URL`, `EXTERNAL_WEB_LOADER_API_KEY` | empty | `external` | `backend/open_webui/config.py:1325-1327`; `src/lib/components/admin/Settings/WebSearch.svelte:1420-1451` |
| **Concurrent Requests** ("Limit parallel web loader requests.") | `web.loader.concurrent_requests` | `WEB_LOADER_CONCURRENT_REQUESTS` | 10 | Always; required | `backend/open_webui/config.py:1205`; `src/lib/components/admin/Settings/WebSearch.svelte:1454-1464` |
| **Youtube Language** ("Preferred transcript language codes, separated by commas.") | `rag.youtube_loader_language` | `YOUTUBE_LOADER_LANGUAGE` (comma-separated) | `en` | Always | `backend/open_webui/config.py:1152`; `src/lib/components/admin/Settings/WebSearch.svelte:1466-1477` |
| **Youtube Proxy URL** ("Proxy URL used for Youtube loader requests.") | `rag.youtube_loader_proxy_url` | `YOUTUBE_LOADER_PROXY_URL` | empty | Always; placeholder `Enter proxy URL (e.g. https://user:password@host:port)` | `backend/open_webui/config.py:1154`; `src/lib/components/admin/Settings/WebSearch.svelte:1479-1490` |

The **Firecrawl Timeout (s)** field (`web.loader.firecrawl_timeout`, seeded from `FIRECRAWL_TIMEOUT`,
default empty) appears only in the Firecrawl *engine* block, although it is used by the Firecrawl
*loader* (`src/lib/components/admin/Settings/WebSearch.svelte:938-952`;
`backend/open_webui/retrieval/web/utils.py:1110-1115`; `backend/open_webui/config.py:1319`).

### 7.3 Search Engines: What Each Is and What Configures It

The engine value is what `web.search.engine` holds and what the admin drop-down shows (except
`duckduckgo`, shown as **DDGS**, and `serphouse`, shown as **SERPHouse**). "Key check" means the
router refuses to search when the named setting is empty (message in section 10). "Filter" says
whether the domain filter list (5.13) is applied. "On error" says whether a failure surfaces as an
error (**raises**) or silently as no results (**empty**). Dispatcher:
`backend/open_webui/routers/retrieval.py:2511-2879`; admin fields:
`src/lib/components/admin/Settings/WebSearch.svelte:230-1128`.

| Engine value | Adapter file | Service and where queries go | Admin fields → keys (seeded from) | Key check | Filter | On error | Other behaviour |
|---|---|---|---|---|---|---|---|
| `ollama_cloud` | `backend/open_webui/retrieval/web/ollama.py` | Ollama's hosted web search, `https://ollama.com/api/web_search` (address fixed in the router, `backend/open_webui/routers/retrieval.py:2521-2529`) | **Ollama Cloud API Key** → `web.search.ollama_cloud_api_key` (`OLLAMA_CLOUD_API_KEY`) | No | Yes | empty | |
| `perplexity_search` | `backend/open_webui/retrieval/web/perplexity_search.py` | Perplexity Search API, default `https://api.perplexity.ai/search` | **Perplexity Search API URL** → `web.search.perplexity_search_api_url` (`PERPLEXITY_SEARCH_API_URL`); **Perplexity API Key** → `web.search.perplexity_api_key` (`PERPLEXITY_API_KEY`) | Yes | No (accepted but unused) | empty | Sends user identity (5.14) |
| `searxng` | `backend/open_webui/retrieval/web/searxng.py` | A SearXNG meta-search server, at the address given | **Searxng Query URL** (required) → `web.search.searxng_query_url` (`SEARXNG_QUERY_URL`); **Searxng search language (all, en, es, de, fr, etc.)** (required) → `web.search.searxng_language` (`SEARXNG_LANGUAGE`, default `all`) | Yes | Yes | raises | Results sorted by SearXNG score; safe search level 1; older addresses containing `<query>` are accepted; optional client certificate from the environment (7.4) |
| `yacy` | `backend/open_webui/retrieval/web/yacy.py` | A YaCy search server; `/yacysearch.json` is appended | **Yacy Instance URL** → `web.search.yacy_query_url` (`YACY_QUERY_URL`); **Yacy Username** (required) and **Yacy Password** → `web.search.yacy_username`, `web.search.yacy_password` | Yes (URL) | Yes | raises | Digest sign-in when a username or password is set |
| `google_pse` | `backend/open_webui/retrieval/web/google_pse.py` | Google Programmable Search Engine, `https://www.googleapis.com/customsearch/v1` | **Google PSE API Key**, **Google PSE Engine Id** → `web.search.google_pse_api_key`, `web.search.google_pse_engine_id` (`GOOGLE_PSE_API_KEY`, `GOOGLE_PSE_ENGINE_ID`) | Yes (both) | Yes | raises | Ten results per request, more pages when the count is higher; sends `webui.url` as the referrer |
| `brave` | `backend/open_webui/retrieval/web/brave.py` | Brave Search API, `https://api.search.brave.com/res/v1/web/search` | **Brave Search API Key** → `web.search.brave_search_api_key` (`BRAVE_SEARCH_API_KEY`) | Yes | Yes | raises | Retries once after 1 s on HTTP 429 |
| `brave_llm_context` | `backend/open_webui/retrieval/web/brave_llm_context.py` | Brave LLM Context API, `https://api.search.brave.com/res/v1/llm/context`; returns extracted passages | **Brave Search API Key** (same key); **Context Tokens** → `web.search.brave_search_context_tokens` (`BRAVE_SEARCH_CONTEXT_TOKENS`, 8192) | Yes | Yes | raises | Retries once after 1 s on HTTP 429; the pages are still loaded unless **Bypass Web Loader** is on |
| `kagi` | `backend/open_webui/retrieval/web/kagi.py` | Kagi Search API, `https://kagi.com/api/v1/search` | **Kagi Search API Key** → `web.search.kagi_search_api_key` (`KAGI_SEARCH_API_KEY`) | Yes | Applied after conversion; appears to fail when a filter is set (section 14) | raises | Prints the results to the server output |
| `mojeek` | `backend/open_webui/retrieval/web/mojeek.py` | Mojeek Search API, `https://api.mojeek.com/search` | **Mojeek Search API Key** → `web.search.mojeek_search_api_key` (`MOJEEK_SEARCH_API_KEY`) | Yes | Yes | raises | Prints the results to the server output |
| `bocha` | `backend/open_webui/retrieval/web/bocha.py` | Bocha AI web search, `https://api.bochaai.com/v1/web-search` | **Bocha Search API Key** → `web.search.bocha_search_api_key` (`BOCHA_SEARCH_API_KEY`) | Yes | Yes | raises | 5-second limit; the snippet is Bocha's summary |
| `serpstack` | `backend/open_webui/retrieval/web/serpstack.py` | serpstack, `api.serpstack.com/search` | **Serpstack API Key** → `web.search.serpstack_api_key` (`SERPSTACK_API_KEY`); `web.search.serpstack_https` (`SERPSTACK_HTTPS`, on) has no admin field | Yes | Yes | raises | Uses plain HTTP when `serpstack_https` is off |
| `serper` | `backend/open_webui/retrieval/web/serper.py` | Serper (Google results), `https://google.serper.dev/search` | **Serper API Key** → `web.search.serper_api_key` (`SERPER_API_KEY`) | Yes | Yes | raises | |
| `serphouse` | `backend/open_webui/retrieval/web/serphouse.py` | SERPHouse, `https://api.serphouse.com/serp/live` | **SERPHouse API Key**, **SERPHouse Domain** → `web.search.serphouse_api_key`, `web.search.serphouse_domain` (`SERPHOUSE_API_KEY`, `SERPHOUSE_DOMAIN`, default `google.com`) | Yes | Yes | raises | Desktop, web results |
| `serply` | `backend/open_webui/retrieval/web/serply.py` | Serply, `https://api.serply.io/v1/search/` | **Serply API Key** → `web.search.serply_api_key` (`SERPLY_API_KEY`) | Yes | Yes | raises | Fixed English, US location, 10 results requested |
| `searchapi` | `backend/open_webui/retrieval/web/searchapi.py` | SearchApi, `https://www.searchapi.io/api/v1/search` | **SearchApi API Key**, **SearchApi Engine** → `web.search.searchapi_api_key`, `web.search.searchapi_engine` (`SEARCHAPI_API_KEY`, `SEARCHAPI_ENGINE`; empty means `google`) | Yes | Yes | raises | 30-second limit; organic results and top stories |
| `serpapi` | `backend/open_webui/retrieval/web/serpapi.py` | SerpApi, `https://serpapi.com/search` | **SerpApi API Key**, **SerpApi Engine** → `web.search.serpapi_api_key`, `web.search.serpapi_engine` (`SERPAPI_API_KEY`, `SERPAPI_ENGINE`; empty means `google`) | Yes | Yes | empty (the HTTP status is not checked) | Logs the whole response at information level |
| `duckduckgo` | `backend/open_webui/retrieval/web/duckduckgo.py` | The `ddgs` library, which queries public engines without a key | **DDGS Backend** → `web.search.ddgs_backend` (`DDGS_BACKEND`, `auto`) | No | Yes | raises | Moderate safe search; uses the server's proxy environment; refused in the slim image; search **Concurrent Requests** sets its thread count |
| `tavily` | `backend/open_webui/retrieval/web/tavily.py` | Tavily Search API, `{TAVILY_API_BASE_URL}/search` (default `https://api.tavily.com`) | **Tavily API Key** → `web.search.tavily_api_key` (`TAVILY_API_KEY`; shared with the Tavily loader) | Yes | Yes | raises | |
| `staan` | `backend/open_webui/retrieval/web/staan.py` | Staan web search, `https://api.staan.ai/v2/search/web` | **Staan API Key**, **Market** (`Region and language of the search results, e.g. en-us.`), **Max Snippets** (`Maximum extra snippets returned per result. Set to 0 to disable them.`) → `web.search.staan_api_key`, `web.search.staan_market`, `web.search.staan_max_snippets` (`STAAN_API_KEY`, `STAAN_MARKET` `en-us`, `STAAN_MAX_SNIPPETS` 0) | Yes | Yes | raises | Extra snippets are joined into the snippet |
| `jina` | `backend/open_webui/retrieval/web/jina_search.py` | Jina search, default `https://s.jina.ai/` | **Jina API Base URL**, **Jina API Key** → `web.search.jina_api_base_url`, `web.search.jina_api_key` (`JINA_API_BASE_URL`, `JINA_API_KEY`) | No | No | raises | At most 10 results |
| `bing` | `backend/open_webui/retrieval/web/bing.py` | Bing Web Search API v7, default `https://api.bing.microsoft.com/v7.0/search` | **Bing Search V7 Endpoint**, **Bing Search V7 Subscription Key** → `web.search.bing_search_v7_endpoint`, `web.search.bing_search_v7_subscription_key` (`BING_SEARCH_V7_ENDPOINT`, `BING_SEARCH_V7_SUBSCRIPTION_KEY`) | No | Yes | raises | Market taken from `DEFAULT_LOCALE` (empty by default, `backend/open_webui/config.py:1672`) |
| `exa` | `backend/open_webui/retrieval/web/exa.py` | Exa, `https://api.exa.ai/search` | **Exa API Key**, **Max Content Length** ("Maximum characters per Exa search result. Leave empty for no limit.") → `web.search.exa_api_key`, `web.search.exa_max_content_length` (`EXA_API_KEY`, `EXA_MAX_CONTENT_LENGTH`) | Yes | Sent to Exa as `includeDomains`, not applied locally | empty | The snippet is the page text; startup stops if `EXA_MAX_CONTENT_LENGTH` is zero or negative (`backend/open_webui/config.py:1279-1281`) |
| `perplexity` | `backend/open_webui/retrieval/web/perplexity.py` | Perplexity chat completions, `https://api.perplexity.ai/chat/completions`; the query is sent as a question to a Sonar model | **Perplexity API Key**, **Perplexity Model** (suggestions Sonar, Sonar Pro, Sonar Reasoning, Sonar Reasoning Pro, Sonar Deep Research), **Perplexity Search Context Usage** (Low, Medium, High) → `web.search.perplexity_api_key`, `web.search.perplexity_model` (`sonar`), `web.search.perplexity_search_context_usage` (`medium`) | No | Yes | empty | Results are the answer's citations, titled `Source {i + 1}` (Source 1, Source 2, ...); the first carries Perplexity's whole answer as its snippet |
| `microsoft_web_iq` | `backend/open_webui/retrieval/web/microsoft_web_iq.py` | Microsoft Web IQ, `{base}/search/web` (default base `https://api.microsoft.ai/v3`) | **Microsoft Web IQ API Base URL**, **Microsoft Web IQ API Key**, **Language** → `web.search.microsoft_web_iq_*` (`MICROSOFT_WEB_IQ_*`; language `en`); shared with that loader | Yes | Yes | empty | Sends user identity (5.14) |
| `sougou` | `backend/open_webui/retrieval/web/sougou.py` | Sogou search through Tencent Cloud (`tms.tencentcloudapi.com`, action `SearchPro`) | **Sougou Search API sID**, **Sougou Search API SK** → `web.search.sougou_api_sid`, `web.search.sougou_api_sk` (`SOUGOU_API_SID`, `SOUGOU_API_SK`) | Yes (both) | Yes | empty for Tencent Cloud errors | Needs the `tencentcloud` Python package, which is not in `pyproject.toml` or `backend/requirements.txt` |
| `firecrawl` | `backend/open_webui/retrieval/web/firecrawl.py` | Firecrawl search, `{base}/v2/search` | **Firecrawl API Base URL**, **Firecrawl API Key**, **Firecrawl Timeout (s)** → `web.loader.firecrawl_api_url`, `web.loader.firecrawl_api_key`, `web.loader.firecrawl_timeout` (shared with the Firecrawl loader) | No | Yes | empty | Retries twice on HTTP 429 or 5xx |
| `external` | `backend/open_webui/retrieval/web/external.py` | An admin-supplied service; receives `{query, count}` and returns `link`, `title`, `snippet` items | **External Web Search URL**, **External Web Search API Key** → `web.search.external_web_search_url`, `web.search.external_web_search_api_key` (`EXTERNAL_WEB_SEARCH_URL`, `EXTERNAL_WEB_SEARCH_API_KEY`) | No | Yes | empty | Sends user identity and the chat id (5.14) |
| `yandex` | `backend/open_webui/retrieval/web/yandex.py` | Yandex Cloud Search API v2, default `https://searchapi.api.cloud.yandex.net/v2/web/search` | **Yandex Web Search URL**, **Yandex Web Search API Key**, **Yandex Web Search config** (JSON) → `web.search.yandex_web_search_url`, `..._api_key`, `..._config` (`YANDEX_WEB_SEARCH_*`) | No | Yes | empty | Searches the Russian index (`SEARCH_TYPE_RU`) unless the config sets another type; sends user identity and the chat id (5.14) |
| `youcom` | `backend/open_webui/retrieval/web/ydc.py` | You.com YDC Index, `https://ydc-index.io/v1/search` | **You.com API Key** → `web.search.youcom_api_key` (`YOUCOM_API_KEY`, falling back to `YDC_API_KEY`, `backend/open_webui/config.py:1335`) | No | Yes | raises | English results; description and snippets joined |
| `linkup` | `backend/open_webui/retrieval/web/linkup.py` | Linkup, default `https://api.linkup.so/v1/search` (a `url` entry in the parameters overrides it) | **Linkup API Key**, **Parameters** (JSON) → `web.search.linkup_api_key`, `web.search.linkup_search_params` (`LINKUP_API_KEY`, `LINKUP_SEARCH_PARAMS`) | Yes | Yes | raises | Defaults: depth `standard`, output `sourcedAnswer`; 30-second limit |
| `openserp` | `backend/open_webui/retrieval/web/openserp.py` | An OpenSERP server (`{base}/mega/search`), which combines several public engines | **OpenSERP URL** (required) → `web.search.openserp_base_url` (`OPENSERP_BASE_URL`, default `http://localhost:7000`) | Yes | Yes | raises | No key |
| `azure` | `backend/open_webui/retrieval/web/azure.py` | An Azure AI Search index (the organization's own index, not a public web search) | No admin fields and not in the drop-down; only `web.search.azure_ai_search_api_key`, `..._endpoint`, `..._index_name` (`AZURE_AI_SEARCH_*`) set through the environment or the API | Yes (all three) | Yes | raises | Needs `azure-search-documents` (in `backend/requirements.txt`); link, title and snippet are guessed from common field names; snippets cut to 500 characters |

All adapter files share `backend/open_webui/retrieval/web/main.py` (domain filter and the
`SearchResult` shape) and the loaders in `backend/open_webui/retrieval/web/utils.py`.

### 7.4 Environment-Only Settings

These are read once at start-up from the environment and are not stored in the `config` table; the
production values are **TO BE CONFIRMED**.

| Variable | Default | Effect here | Source |
|---|---|---|---|
| `ENABLE_LOCAL_WEB_FETCH` (older name `ENABLE_RAG_LOCAL_WEB_FETCH`) | off | Allows addresses on private or non-public networks to be fetched (5.12) | `backend/open_webui/config.py:1110-1118` |
| `WEB_FETCH_FILTER_LIST` | empty | Comma-separated allow/block entries added to the built-in block list for every fetch (5.12) | `backend/open_webui/config.py:1121-1149` |
| `AIOHTTP_CLIENT_ALLOW_REDIRECTS` | off | Whether page downloads follow redirects | `backend/open_webui/env.py:636-637` |
| `AIOHTTP_CLIENT_SESSION_SSL`, `AIOHTTP_CLIENT_SSL_CERT_FILE` | on, empty | Certificate checking and a custom certificate bundle for outbound connections, used by the Default and Playwright loaders and the attachment download | `backend/open_webui/env.py:547-556`, `:628-631`; `backend/open_webui/retrieval/web/utils.py:723-733`, `:994-997` |
| `AIOHTTP_CLIENT_TIMEOUT` | empty (no limit) | Total time limit for the shared connection pool and the attachment download | `backend/open_webui/env.py:608-612`; `backend/open_webui/utils/session_pool.py:43`; `backend/open_webui/retrieval/web/utils.py:280-285` |
| `USER_AGENT` | empty | Browser identity the Default loader sends to websites (else `DefaultLangchainUserAgent`) | `backend/open_webui/env.py:651-654`; `backend/open_webui/retrieval/web/utils.py:961` |
| `TAVILY_API_BASE_URL` | `https://api.tavily.com` | Base address for Tavily search and extract | `backend/open_webui/env.py:606` |
| `SEARXNG_CLIENT_CERT_FILE`, `SEARXNG_CLIENT_KEY_FILE` | empty | Client certificate presented to the SearXNG server | `backend/open_webui/env.py:633-634`; `backend/open_webui/retrieval/web/searxng.py:26-36` |
| `ENABLE_QUERIES_CACHE` | off | Reuse the web-search queries for the retrieval step (5.4) | `backend/open_webui/env.py:370` |
| `USE_SLIM_DOCKER` | off | Slim image: no DDGS engine, no Playwright loader | `backend/open_webui/env.py:45` |
| `ENABLE_FORWARD_USER_INFO_HEADERS` | off | Governs user-identity forwarding elsewhere; **not** consulted by the four engines that forward identity (5.14) | `backend/open_webui/env.py:989` |
| `FORWARD_USER_INFO_HEADER_USER_NAME`, `..._USER_ID`, `..._USER_EMAIL`, `..._USER_ROLE`, `FORWARD_SESSION_INFO_HEADER_CHAT_ID`, `FORWARD_USER_INFO_HEADER_JWT_SECRET`, `FORWARD_USER_INFO_HEADER_JWT` | `X-OpenWebUI-User-Name`, `X-OpenWebUI-User-Id`, `X-OpenWebUI-User-Email`, `X-OpenWebUI-User-Role`, `X-OpenWebUI-Chat-Id`, empty, `X-OpenWebUI-User-Jwt` | Header names used when identity is forwarded; with the token secret set, one signed token replaces the separate headers | `backend/open_webui/env.py:991-1002` |

### 7.5 Settings Owned by Other Areas That Change Web Search

| Setting | Effect on web search | Owner |
|---|---|---|
| `task.query.search.enable` (**Web Search Query Generation**, on) and `task.query.prompt_template` | Whether and how the task model writes queries (5.4) | `chat-completion-pipeline-and-generation-tasks.md`; `backend/open_webui/config.py:2302-2307`, `:3146-3148` |
| The task model settings | Which model writes the queries | `chat-completion-pipeline-and-generation-tasks.md` |
| `rag.top_k`, `rag.full_context`, hybrid search and reranking, chunk size, embedding model | How the stored pages are searched and how much reaches the prompt (5.7) | `rag-retrieval-embeddings-and-vector-stores.md` |
| `rag.file.max_size` (**Max Upload Size**) | Largest file accepted through **Attach Webpage** | `files-uploads-and-storage.md`; `backend/open_webui/routers/retrieval.py:2376` |
| `user.permissions` > `features.web_search`, `chat.web_upload` (both default on; seeded from `USER_PERMISSIONS_FEATURES_WEB_SEARCH`, `USER_PERMISSIONS_CHAT_WEB_UPLOAD`) | Who may search and attach pages (section 3) | `users-groups-roles-and-permissions.md`; `backend/open_webui/config.py:1859`, `:1908`, `:1984`, `:2009` |

### 7.6 Per-Model and Per-User Settings

| Setting | Where | Effect | Source |
|---|---|---|---|
| **Capabilities** > **Web Search** ("Model can search the web for information") | Model editor | Off hides the composer switch for that model and removes the native tools; unset counts as on | `src/lib/components/workspace/Models/Capabilities.svelte:25-28`; `src/lib/i18n/locales/en-US/translation.json:2596-2597`; `backend/open_webui/utils/tools.py:533-534`, `:681` |
| **Default Features** > **Web Search** | Model editor (offered only when the capability is on) | Switches web search on when the model is chosen (5.1) | `src/lib/components/workspace/Models/ModelEditor.svelte:1250-1262`; `src/lib/i18n/locales/en-US/translation.json:2602-2604` |
| **Builtin Tools** > **Web Search** ("Search the web and fetch URLs") | Model editor, when the **Builtin Tools** capability is on | Off withholds `search_web` and `fetch_url` in native mode | `src/lib/components/workspace/Models/BuiltinTools.svelte:49-52`; `src/lib/i18n/locales/en-US/translation.json:2571-2572`; `backend/open_webui/utils/tools.py:538-540`, `:679` |
| **Function Calling** ("Native mode (default) leverages the model's built-in tool-calling capabilities. Legacy mode works with a wider range of models by calling tools once before execution via prompt injection.") | Advanced parameters of a model, the user or a chat | Chooses native tools or the classic step (section 1) | `src/lib/components/chat/Settings/Advanced/AdvancedParams.svelte:247-262`; `src/lib/i18n/locales/en-US/translation.json:2825-2826`; `backend/open_webui/main.py:1290-1294` |
| **Capabilities** > `file_context`, `citations`, `status_updates` | Model editor | Whether web results reach the prompt, whether `fetch_url` makes source chips, whether status lines show (5.7-5.9) | `backend/open_webui/utils/middleware.py:3207`, `:5841-5843`; `src/lib/components/chat/Messages/ResponseMessage.svelte:198-199` |
| **Web Search in Chat** (**Default** or **Always**) | Settings > Interface (personal) | **Always** keeps web search active in every chat whose models support it | `src/lib/components/common/InterfaceSettings.svelte:258-261`, `:1560-1580`; `src/lib/components/chat/Chat.svelte:349-354` |
| **Hide Processing Details** (fork) | Settings > Interface (personal) | Hides search status lines and tool-call blocks (5.8, section 12) | `src/lib/i18n/locales/en-US/translation.json:2923-2924` |

### 7.7 How Saving the Web Search Panel Works

*Precision 2026-10-11 (read from code, to confirm in a test environment):* the **Documents** panel also posts the whole retrieval configuration it loaded, including the `web` block (`src/lib/components/admin/Settings/Documents.svelte:264-265`), so saving Documents re-saves every `web.*` key as it was when that screen opened; a Web Search change made in another window can be undone. See `configuration-persistent-settings-r-to-w.md` section 14.

1. The panel loads all values with `GET /api/v1/retrieval/config` and converts the domain list and
   YouTube languages to comma-separated text for editing
   (`src/lib/components/admin/Settings/WebSearch.svelte:118-157`).
2. **Save** first runs the browser's form checks: the page cannot be saved while **Web Search
   Engine** is unselected, or while a required field (Searxng Query URL and language, Yacy
   Username, OpenSERP URL, Search Result Count, loader Concurrent Requests) is empty
   (`src/lib/components/admin/Settings/WebSearch.svelte:160-166`, `:215`, `:302`, `:320`, `:357`,
   `:1095`, `:1145`, `:1462`; `src/lib/components/common/SettingsSelect.svelte:9`, `:23`).
3. The lists are split on commas, the Linkup parameters are parsed as JSON, and the whole `web`
   object is posted to `POST /api/v1/retrieval/config/update`
   (`src/lib/components/admin/Settings/WebSearch.svelte:61-107`).
4. The server writes every field of the `web` object and returns the stored values
   (`backend/open_webui/routers/retrieval.py:1313-1398`). A field missing from the request is saved
   as empty (only **Context Tokens** is skipped when missing) because the form's fields default to
   empty (`:792-870`); the panel always sends every field, so this matters only to scripts that
   call the API directly. In the slim image the server refuses to switch the engine to DDGS or the
   loader to Playwright (`:966-983`).
5. On success the shared admin handler shows `Settings saved successfully!` and reloads the public
   configuration (`src/lib/components/chat/SettingsModal.svelte:460-464`).
6. **If the server refuses, or the Linkup parameters are not valid JSON, no message appears**: the
   error is thrown before the success handler runs, so the admin sees neither a success nor an
   error pop-up (`src/lib/components/admin/Settings/WebSearch.svelte:95-107`, `:162-165`;
   `src/lib/apis/retrieval/index.ts:67-95`).

Changes take effect for the next search; nothing is restarted. Saving does not check that a key
or address works; the first search shows whether it does.

## 8. Cron Jobs and Background Processes

There is no crontab and no background loop dedicated to web search. Everything happens inside a
request:

| Work | When it runs | Source |
|---|---|---|
| Classic search: query generation, engine calls, page loading, embedding | Inside the chat request, before the model is called; the reply waits for it | `backend/open_webui/utils/middleware.py:2700-2709` |
| `search_web` and `fetch_url` | Inside the chat request's tool loop, when the model calls them | `backend/open_webui/tools/builtin.py:294-362` |
| Attaching a page | Inside the `/process/url` request, while the chip shows as loading | `backend/open_webui/routers/retrieval.py:2356-2426` |
| Older (synchronous) engine adapters and loaders | Moved to a worker thread so the server stays responsive; still part of the same request | `backend/open_webui/routers/retrieval.py:2511-2517`; `backend/open_webui/retrieval/utils.py:245-251` |
| Scheduled automations | The automations scheduler (`scheduler_worker_loop`) runs a model with web search on when that model lists **Web Search** among its default features (5.1); owned by `background-processes-and-scheduling.md` | `backend/open_webui/utils/automations.py:166-197` |

**No clean-up.** No code was found that deletes `web-search-*` collections or the hash-named
collections of attached pages once they are written; a repeated identical search replaces its own
collection (`backend/open_webui/routers/retrieval.py:3016-3024`). They are removed when the whole
vector store is reset from the Documents panel's Danger Zone
(`backend/open_webui/routers/retrieval.py:3271-3284`; see
`rag-retrieval-embeddings-and-vector-stores.md`, section 5.16), and no removal was found for when a
chat or user is deleted (section 14).

**Saving settings** takes effect immediately for the next request; there is no reload job
(section 7.7).

## 9. Notifications and Emails

The application sends no email (`knowledgebase/tools/ground-truth.md`). For web search and web
loading:

| Channel | What is sent | Source |
|---|---|---|
| Chat status events (socket) | The status lines in 5.8, sent to the user's browser while the reply is prepared and saved on the message | `backend/open_webui/utils/middleware.py:1562-1728`; `backend/open_webui/socket/main.py:1164-1170` |
| Sources (socket and stream) | The web results used, shown under the answer | `backend/open_webui/utils/middleware.py:3232-3246` |
| Tool-call blocks (native mode) | Arguments and results of `search_web` and `fetch_url` | `backend/open_webui/utils/middleware.py:6070-6118` |
| Pop-up messages (toasts) | Attachment failures and the empty-address warning (section 10) | `src/lib/components/chat/Chat.svelte:1792`, `:1861`; `src/lib/components/chat/MessageInput/AttachWebpageModal.svelte:30` |

No in-app notification, browser notification, webhook or platform event is raised by a web search
or a web-page attachment: the processing events published by the retrieval router belong to file
and text processing (`backend/open_webui/routers/retrieval.py:2074-2077`, `:2167-2170`,
`:2225-2228`), not to `process_web` or `process_web_search`.

## 10. Error, Warning and Notice Messages (Verbatim)

Messages are quoted exactly as the code spells them; `{name}` marks a value filled in at run time
(the source's own variable name). Backend error details reach users as the status line of the reply
(chat searches) or as a red pop-up (attachments). Because `ERROR_MESSAGES.DEFAULT` wraps texts as
`[ERROR: …]` (`backend/open_webui/constants.py:16-23`), several messages appear with that prefix.

### 10.1 Chat Status Lines During a Classic Search

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Searching the web` | Status | `backend/open_webui/utils/middleware.py:1567`; `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:142-143` | Legacy search starts | Wait | None |
| `No search query generated` | Status | `backend/open_webui/utils/middleware.py:1635`; `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:30-31` | The task model returned an empty query list | Ask more explicitly (for example "search the web for ...") | Task model behaviour (5.4) |
| `Searching` | Status | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:52-77` | Queries generated (shown with query chips) | Wait | None |
| `Searched {{count}} sites` | Status | `backend/open_webui/utils/middleware.py:1694`; `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:26-29` | Pages loaded; the count is the pages kept after loading | Click to see the pages | If 0, see 11.4 |
| `Generating search query` | Status | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:32-33`, `:140-141` | Display fallback only; the server code in scope does not send it | None | None |
| `[ERROR: No results found from web search]` | Error (status) | `backend/open_webui/routers/retrieval.py:2953-2957` | The engine returned no usable links for any query (also when it failed silently, 7.3) | Rephrase; try again later | Engine choice and key; server log |
| `[ERROR: Something went wrong while searching the web.]` | Error (status) | `backend/open_webui/routers/retrieval.py:2946-2951`, `:3042-3047`; text `backend/open_webui/constants.py:101` | Any engine error (missing key, refused request, network failure, slim DDGS) or a loader failure (all addresses refused, invalid loader) | Try again later | Server log line `Web search failed` or `Web search content loading failed` holds the real cause (10.7) |
| `Failed to embed and store the retrieved web pages. Check the embedding configuration in Admin Settings > Documents.` | Error (status) | `backend/open_webui/routers/retrieval.py:3025-3031` | Saving the pages to the vector store failed, including when every loaded page was empty | Try again; rephrase | Embedding settings; whether pages load (11.5) |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (status) | `backend/open_webui/routers/retrieval.py:2885-2895`; text `backend/open_webui/constants.py:70-72` | Web search off site-wide or permission missing at search time | Ask an admin | `web.search.enable`, `features.web_search` |
| `Playwright is unavailable in slim. Use basic HTTP fetching or an external web loader.` | Error (status or pop-up) | `backend/open_webui/retrieval/web/utils.py:682-685` | Loader set to Playwright in the slim image | Report to support | Loader engine; image type |
| `No search results found` | Error (status) | `backend/open_webui/utils/middleware.py:1707` | Only when the search returns nothing at all; with the current server code a search either returns data or raises, so this line is not expected | Rephrase | None |
| `An error occurred while searching the web` | Error (status) | `backend/open_webui/utils/middleware.py:1722` | An unexpected error in the chat step that carries no detail | Try again | Server log |
| `Querying` | Status | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:78-103` | Retrieval queries over the stored pages | Wait | None |
| `Retrieved {{count}} sources` | Status | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:120-122` | Retrieval found sources | None | None |
| `Retrieved 1 source` | Status | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:114` | One source | None | None |
| `No sources found` | Status | `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte:112` | Retrieval matched nothing in the stored pages | Rephrase | 5.7 |

### 10.2 Engine Configuration Messages

Raised in the engine dispatcher or an adapter. In **legacy** mode the user sees only
`[ERROR: Something went wrong while searching the web.]` and the text below is in the server log;
in **native** mode the text is returned to the model as `{"error": "…"}` and often repeated in the
answer (`backend/open_webui/tools/builtin.py:328-330`).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `No PERPLEXITY_API_KEY found in environment variables` | Error | `backend/open_webui/routers/retrieval.py:2542` | Engine `perplexity_search` with no key | Report | Perplexity API key set |
| `No SEARXNG_QUERY_URL found in environment variables` | Error | `backend/open_webui/routers/retrieval.py:2554` | Engine `searxng` with no address | Report | Searxng Query URL |
| `No OPENSERP_BASE_URL found in environment variables` | Error | `backend/open_webui/routers/retrieval.py:2564` | Engine `openserp` with no address | Report | OpenSERP URL |
| `No YACY_QUERY_URL found in environment variables` | Error | `backend/open_webui/routers/retrieval.py:2577` | Engine `yacy` with no address | Report | Yacy Instance URL |
| `No GOOGLE_PSE_API_KEY or GOOGLE_PSE_ENGINE_ID found in environment variables` | Error | `backend/open_webui/routers/retrieval.py:2589` | Engine `google_pse` missing either value | Report | Both Google PSE fields |
| `No BRAVE_SEARCH_API_KEY found in environment variables` | Error | `backend/open_webui/routers/retrieval.py:2599`, `:2611` | Engine `brave` or `brave_llm_context` with no key | Report | Brave key |
| `No KAGI_SEARCH_API_KEY found in environment variables` | Error | `backend/open_webui/routers/retrieval.py:2622` | Engine `kagi` with no key | Report | Kagi key |
| `No MOJEEK_SEARCH_API_KEY found in environment variables` | Error | `backend/open_webui/routers/retrieval.py:2633` | Engine `mojeek` with no key | Report | Mojeek key |
| `No BOCHA_SEARCH_API_KEY found in environment variables` | Error | `backend/open_webui/routers/retrieval.py:2644` | Engine `bocha` with no key | Report | Bocha key |
| `No SERPSTACK_API_KEY found in environment variables` | Error | `backend/open_webui/routers/retrieval.py:2655` | Engine `serpstack` with no key | Report | Serpstack key |
| `No SERPER_API_KEY found in environment variables` | Error | `backend/open_webui/routers/retrieval.py:2665` | Engine `serper` with no key | Report | Serper key |
| `No SERPHOUSE_API_KEY found in environment variables` | Error | `backend/open_webui/routers/retrieval.py:2676` | Engine `serphouse` with no key | Report | SERPHouse key |
| `No SERPLY_API_KEY found in environment variables` | Error | `backend/open_webui/routers/retrieval.py:2687` | Engine `serply` with no key | Report | Serply key |
| `No TAVILY_API_KEY found in environment variables` | Error | `backend/open_webui/routers/retrieval.py:2707` | Engine `tavily` with no key | Report | Tavily key |
| `No STAAN_API_KEY found in environment variables` | Error | `backend/open_webui/routers/retrieval.py:2720` | Engine `staan` with no key | Report | Staan key |
| `No EXA_API_KEY found in environment variables` | Error | `backend/open_webui/routers/retrieval.py:2732` | Engine `exa` with no key | Report | Exa key |
| `No SEARCHAPI_API_KEY found in environment variables` | Error | `backend/open_webui/routers/retrieval.py:2744` | Engine `searchapi` with no key | Report | SearchApi key |
| `No SERPAPI_API_KEY found in environment variables` | Error | `backend/open_webui/routers/retrieval.py:2756` | Engine `serpapi` with no key | Report | SerpApi key |
| `AZURE_AI_SEARCH_API_KEY, AZURE_AI_SEARCH_ENDPOINT, and AZURE_AI_SEARCH_INDEX_NAME are required for Azure AI Search` | Error | `backend/open_webui/routers/retrieval.py:2787-2789` | Engine `azure` missing any of the three | Report | Environment values |
| `No MICROSOFT_WEB_IQ_API_KEY found in environment variables` | Error | `backend/open_webui/routers/retrieval.py:2813` | Engine `microsoft_web_iq` with no key | Report | Web IQ key |
| `No SOUGOU_API_SID or SOUGOU_API_SK found in environment variables` | Error | `backend/open_webui/routers/retrieval.py:2825` | Engine `sougou` missing either value | Report | Both Sougou fields |
| `No LINKUP_API_KEY found in environment variables` | Error | `backend/open_webui/routers/retrieval.py:2877` | Engine `linkup` with no key | Report | Linkup key |
| `No search engine API key found in environment variables` | Error | `backend/open_webui/routers/retrieval.py:2879` | `web.search.engine` empty or not a known value | Report | Engine selection |
| `DDGS is unavailable in slim. Configure another web search provider in Admin Settings > Web Search.` | Error | `backend/open_webui/retrieval/web/duckduckgo.py:29-32`; on save `backend/open_webui/routers/retrieval.py:966-975` | DDGS engine in the slim image | Report | Engine selection; image type |
| `azure-search-documents is required for Azure AI Search. Install it with: pip install azure-search-documents` | Error | `backend/open_webui/retrieval/web/azure.py:46-49` | Azure engine without that package | Report | Platform maintainer |
| `Linkup search failed: {str(e)}` | Error | `backend/open_webui/retrieval/web/linkup.py:69-71` | Network or HTTP error from Linkup | Report | Linkup key and parameters |
| `Linkup search error: {str(e)}` | Error | `backend/open_webui/retrieval/web/linkup.py:72-74` | Any other Linkup failure (for example a bad response) | Report | As above |
| `Invalid WEB_LOADER_ENGINE: {engine}. Please set it to 'safe_web', 'playwright', 'firecrawl', 'tavily', 'external', or 'microsoft_web_iq'.` | Error | `backend/open_webui/retrieval/web/utils.py:1148-1152` | Stored loader value not recognized | Report | `web.loader.engine` |
| `{name} is disabled` (here `name` is `Search query generation`) | Error (not shown in chat) | `backend/open_webui/routers/tasks.py:406-411`; text `backend/open_webui/constants.py:125` | Query generation off; the chat step silently searches the user's message instead | None | `task.query.search.enable` |

### 10.3 Attach Webpage and YouTube Messages

Shown as a red pop-up by the composer (`src/lib/components/chat/Chat.svelte:1857-1862`); the chip is
removed.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Please enter a valid URL.` | Error (pop-up) | `src/lib/components/chat/MessageInput/AttachWebpageModal.svelte:29-31` | No line in the box is a well-formed `http`/`https` address | Paste the full address including `https://` | None |
| `You do not have permission to upload web content.` | Error (pop-up and menu tooltip) | `src/lib/components/chat/Chat.svelte:1791-1794`; `src/lib/components/chat/MessageInput/InputMenu.svelte:246-249` | User lacks `chat.web_upload` | Ask an admin | User's groups and default permissions |
| `[ERROR: Error processing URL]` | Error | `backend/open_webui/routers/retrieval.py:2419-2426` | The address was refused by the address checks (5.12), could not be reached, returned an HTTP error status, or failed in another unexpected way | Check the address opens in a browser; try the final address after any redirect | Server log for the cause; whether the site is internal (5.12) |
| `[ERROR: Could not read content from {form_data.url}]` | Error | `backend/open_webui/routers/retrieval.py:2450-2455` | The web loader (or file extraction for a linked file) failed | Try again or attach the page as a file | Loader engine and server log |
| `[ERROR: Error querying knowledge base]` | Error | `backend/open_webui/routers/retrieval.py:2501-2508` | The page loaded but storing it failed, typically because no text could be extracted (for example a page built entirely by scripts with the Default loader) | Copy the text into the message instead | Loader engine (Playwright handles script-built pages); embedding settings |
| `Oops! The file you're trying to upload is too large. Please upload a file that is less than {size}.` | Error | `backend/open_webui/routers/retrieval.py:2283-2311`; text `backend/open_webui/constants.py:105-107`; also `backend/open_webui/retrieval/utils.py:211-212` | The linked file is larger than `rag.file.max_size` (`size` is shown in MB) | Download and attach a smaller file | `rag.file.max_size` |
| `[ERROR: Invalid image content]` | Error | `backend/open_webui/routers/retrieval.py:2325-2329` | The address claims to be an image but is not a valid one | Use another address | None |
| `Playwright is unavailable in slim. Use basic HTTP fetching or an external web loader.` | Error | `backend/open_webui/retrieval/web/utils.py:682-685` | Loader set to Playwright in the slim image | Report | Loader engine |
| `YouTube blocked the transcript request for {video_id} from this server. This usually means the server address is rate limited or belongs to a cloud provider. A proxy for these requests can be configured under Admin Settings, Web Search, Youtube Proxy URL.` | Error | `backend/open_webui/retrieval/loaders/youtube.py:28-34`; raised to the user at `backend/open_webui/routers/retrieval.py:2444-2449` | YouTube refused the server's request | Report | **Youtube Proxy URL** |
| `Transcripts are disabled for the YouTube video {video_id}.` | Error | `backend/open_webui/retrieval/loaders/youtube.py:35-36` | The video has no transcripts | Use another source | None |
| `The YouTube video {video_id} is age restricted, so its transcript cannot be retrieved.` | Error | `backend/open_webui/retrieval/loaders/youtube.py:37-38` | Age-restricted video | Use another source | None |
| `The YouTube video {video_id} is unavailable.` | Error | `backend/open_webui/retrieval/loaders/youtube.py:39-40` | Private, removed or invalid video | Check the link | None |
| `YouTube requires additional verification to return the transcript for {video_id}.` | Error | `backend/open_webui/retrieval/loaders/youtube.py:41-42` | YouTube asked for extra verification | Report | YouTube proxy; platform maintainer |
| `Could not retrieve a transcript for the YouTube video {video_id}.` | Error | `backend/open_webui/retrieval/loaders/youtube.py:44` | Any other transcript failure | Try again later | Server log `Loading YouTube transcript failed` |
| `No transcript found for the YouTube video {self.video_id} in these languages: {languages_tried}.` | Error | `backend/open_webui/retrieval/loaders/youtube.py:170-177` | No transcript in the configured languages or English | Report | **Youtube Language** |

### 10.4 Native Tool Results (Seen in the Tool-Call Block and Read by the Model)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `The URL you provided is invalid. Please double-check and try again.` | Error (tool result) | `backend/open_webui/retrieval/web/utils.py:110-161`; text `backend/open_webui/constants.py:99` | `fetch_url` was given an address refused by the checks (5.12) | Paste the page text instead | Whether the address is internal |
| `[Content truncated...]` | Notice (appended to the page text) | `backend/open_webui/tools/builtin.py:353-355` | The fetched page is longer than **Fetch URL Content Length Limit** | None | `web.fetch.max_content_length` |
| `Request context not available` | Error (tool result) | `backend/open_webui/tools/builtin.py:308-309`, `:344-345` | The tool was called outside a chat request | Report | Platform maintainer |

Any engine message from 10.2 can also appear here as `{"error": "…"}`.

### 10.5 Composer and Dialog Texts

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Use Web Search?` | Notice (dialog title) | `src/lib/components/chat/Chat.svelte:4222` | Web search switched on or used while confirmation is required | **Continue** or **Cancel** | `web.search.confirmation.enable` |
| `Your query will be sent to the configured web search provider.` | Notice (dialog text) | `src/lib/components/chat/Chat.svelte:4223-4225`; seeded default `backend/open_webui/config.py:1165-1168` | Same dialog when the admin text is blank (also the seeded admin text) | As above | `web.search.confirmation.content` |
| `Search the internet` | Notice (tooltip) | `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte:445` | Hovering **Web Search** in the Integrations menu | None | None |
| `Attach Webpage` | Label (menu item and window title) | `src/lib/components/chat/MessageInput/InputMenu.svelte:265`; `src/lib/components/chat/MessageInput/AttachWebpageModal.svelte:44` | **+** menu | None | None |
| `Webpage URLs` | Label | `src/lib/components/chat/MessageInput/AttachWebpageModal.svelte:68` | **Attach Webpage** window | One address per line | None |

### 10.6 Admin Panel Messages and Notices

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Settings saved successfully!` | Success (pop-up) | `src/lib/components/chat/SettingsModal.svelte:460-461` | Save succeeded | None | None |
| `DDGS is unavailable in slim. Configure another web search provider in Admin Settings > Web Search.` | Error (HTTP 400; no pop-up, 7.7) | `backend/open_webui/routers/retrieval.py:966-975` | Switching the engine to DDGS in the slim image (through the API; the option is greyed out in the panel) | Choose another engine | Image type |
| `Playwright is unavailable in slim. Use basic HTTP fetching or an external web loader.` | Error (HTTP 400; no pop-up) | `backend/open_webui/routers/retrieval.py:976-983` | Switching the loader to Playwright in the slim image | Choose another loader | Image type |
| `Select a engine` | Notice (placeholder) | `src/lib/components/admin/Settings/WebSearch.svelte:214`, `:217`, `:1236` | No engine chosen | Choose an engine | None |
| `Enter domains separated by commas (e.g., example.com,site.org,!excludedsite.com)` | Notice (placeholder) | `src/lib/components/admin/Settings/WebSearch.svelte:1189-1191` | Empty **Domain Filter List** | None | None |
| `Use segmented retrieval for focused and relevant content extraction.` | Notice (description) | `src/lib/components/admin/Settings/WebSearch.svelte:1199-1201` | **Bypass Embedding and Retrieval** off | None | None |
| `Fetch page contents without proxy environment variables.` | Notice (description) | `src/lib/components/admin/Settings/WebSearch.svelte:1220-1222` | **Trust Proxy Environment** off | None | None |
| `Leave empty to use the default config, or enter a valid json (see https://yandex.cloud/en/docs/search-api/api-ref/WebSearch/search#yandex.cloud.searchapi.v2.WebSearchRequest)` | Notice (tooltip and placeholder) | `src/lib/components/admin/Settings/WebSearch.svelte:1025-1037` | Yandex engine selected | None | None |
| `Max tokens to retrieve (1024-32768, default 8192)` | Notice (placeholder) | `src/lib/components/admin/Settings/WebSearch.svelte:445` | Brave LLM Context selected | None | None |
| `Region and language of the search results, e.g. en-us.` | Notice (description) | `src/lib/components/admin/Settings/WebSearch.svelte:599` | Staan selected | None | None |
| `Maximum extra snippets returned per result. Set to 0 to disable them.` | Notice (description) | `src/lib/components/admin/Settings/WebSearch.svelte:612-614` | Staan selected | None | None |
| `Enter Yacy URL (e.g. http://yacy.example.com:8090)` | Notice (placeholder) | `src/lib/components/admin/Settings/WebSearch.svelte:338` | YaCy selected | None | None |
| `Enter proxy URL (e.g. https://user:password@host:port)` | Notice (placeholder) | `src/lib/components/admin/Settings/WebSearch.svelte:1486` | Empty **Youtube Proxy URL** | None | None |
| `No limit` | Notice (placeholder) | `src/lib/components/admin/Settings/WebSearch.svelte:777`, `:1176` | Empty Exa **Max Content Length** or **Fetch URL Content Length Limit** | None | None |

### 10.7 Server Log Lines That Explain Symptoms

Log lines, not user messages; logs go to standard output (`knowledgebase/tools/ground-truth.md`).

| Log line | Source | Meaning |
|---|---|---|
| `Web search failed` (with the underlying error) | `backend/open_webui/routers/retrieval.py:2947` | The engine call failed; the next lines name the cause (for example a 10.2 message) |
| `Web search content loading failed` | `backend/open_webui/routers/retrieval.py:3043` | The loader step failed |
| `Error saving web search results to vector DB: {e}` | `backend/open_webui/routers/retrieval.py:3027` | Behind `Failed to embed and store ...` |
| `All provided URLs were blocked or invalid: {urls}` | `backend/open_webui/retrieval/web/utils.py:1060` | Every result address was refused (5.12) |
| `Blocked by filter list: {host}` and `Blocked non-global address: {address}` | `backend/open_webui/retrieval/web/utils.py:109`, `:127` | One address was refused (5.12) |
| `Could not resolve host {parsed_url.hostname}: {e}` | `backend/open_webui/retrieval/web/utils.py:160` | The site's name does not resolve from the server |
| `Error fetching {url} with attempt {i + 1}/{retries}: {e}. Retrying...` | `backend/open_webui/retrieval/web/utils.py:1010` | Default loader retrying a page |
| `Error fetching %s: %s` | `backend/open_webui/retrieval/web/utils.py:980` | Default loader gave up on a page (it then counts as an empty page) |
| `Error loading {url}: {e}` / `Error loading {path}: {e}` | `backend/open_webui/retrieval/web/utils.py:887`, `:927`, `:1024` | Playwright or the Default loader (attachments and `fetch_url`) failed on a page |
| `SSL verification failed for {url}: {str(e)}` | `backend/open_webui/retrieval/web/utils.py:354`, `:532`, `:562`, `:619` | The certificate pre-check skipped a page (5.6) |
| `Error extracting content from {url} with Firecrawl: {e}` | `backend/open_webui/retrieval/web/utils.py:450`, `:471` | Firecrawl loader failure |
| `Failed to extract content from {url}: {error}` | `backend/open_webui/retrieval/loaders/tavily.py:87` | Tavily could not extract a page |
| `Error browsing {url} with Microsoft Web IQ: {e}` | `backend/open_webui/retrieval/loaders/microsoft_web_iq.py:44` | Web IQ loader failure |
| `Error extracting content from batch {urls}: {e}` | `backend/open_webui/retrieval/loaders/external_web.py:52` | External loader failure |
| `Error searching Exa: {e}`, `Error in External search: {e}`, `Error in FireCrawl search: {e}`, `Error searching with Microsoft Web IQ API: {e}`, `Error searching Ollama: {e}`, `Error searching with Perplexity API: {e}`, `Error searching with Perplexity Search API: {e}`, `Error in Sougou search: {err}`, `Error in search: {e}` (Yandex) | `backend/open_webui/retrieval/web/exa.py:55`; `backend/open_webui/retrieval/web/external.py:59`; `backend/open_webui/retrieval/web/firecrawl.py:231`; `backend/open_webui/retrieval/web/microsoft_web_iq.py:57`; `backend/open_webui/retrieval/web/ollama.py:51`; `backend/open_webui/retrieval/web/perplexity.py:99`; `backend/open_webui/retrieval/web/perplexity_search.py:67`; `backend/open_webui/retrieval/web/sougou.py:50`; `backend/open_webui/retrieval/web/yandex.py:119` | An engine that fails silently failed; the user sees "no results" |
| `Brave Search rate-limited (429); retrying after %.1fs` | `backend/open_webui/retrieval/web/brave.py:36` | Brave rate limit hit; one retry |
| `Loading YouTube transcript failed: %s` | `backend/open_webui/retrieval/loaders/youtube.py:127` | Cause behind the YouTube messages |
| `No transcript found for any of the specified languages: {languages_tried}. Verify if the video has transcripts, add more languages if needed.` | `backend/open_webui/retrieval/loaders/youtube.py:172-174` | No transcript in the configured languages |
| `search_web error: {e}` / `fetch_url error: {e}` | `backend/open_webui/tools/builtin.py:329`, `:361` | Native tool failures |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it gathers facts, explains behaviour and escalates; it does not change
settings, permissions or models. For every escalation send: the time of the attempt (with time
zone), the chat link or chat id, the model name, the exact status-line or pop-up text (a
screenshot helps), whether **Web Search** was switched on, and for attachments the address
involved (only if the user agrees to share it). Do not copy chat content into tickets beyond what
is needed.

### 11.1 "There's no Web Search option in my chat"

**Symptom.** The **Integrations** menu has no **Web Search** row, or the menu itself is missing.

**Likely causes, in order.**
1. Web search is off site-wide (`web.search.enable`, code default off; live value **TO BE
   CONFIRMED**) (`src/lib/components/chat/MessageInput.svelte:824-828`).
2. The user lacks `features.web_search` (default on) (section 3).
3. One of the selected models has the **Web Search** capability switched off; with several models
   selected, all must support it (`src/lib/components/chat/MessageInput.svelte:759-763`, `:824-828`).

**Diagnostic steps.** Ask which model(s) are selected and whether the option appears with another
model. Ask whether colleagues see it. An admin can confirm the switch under Admin Settings >
**Web Search** and the user's groups.

**Resolution.** Suggest a model that supports web search, if one exists. Otherwise explain that
web search is a site setting.

**Escalation.** Send the model names, the user's role and groups as seen in the admin user list,
and whether others are affected, to the platform admins.

### 11.2 "I turned on Web Search but the answer didn't search the web"

**Symptom.** The switch was on, yet there is no `Searching the web` line, no `Searched ... sites`
and no web sources.

**Likely causes, in order.**
1. **Native mode (the default):** the model decided not to call `search_web`; it is offered the
   tool but chooses whether to use it (section 5.9). A tool-call block appears only if it searched.
2. The user has **Hide Processing Details** on, or the model's status updates are off, so search
   steps are hidden although they ran (section 5.8).
3. Legacy mode: the task model produced no query (`No search query generated`).
4. The model's **Builtin Tools** > **Web Search** category is off, or **Builtin Tools** is off, so
   no tool is offered (section 7.6).
5. The browser sent web search but the server rejected it because the permission or the site
   switch changed (section 3.2).

**Diagnostic steps.** Ask for a screenshot of the full answer, with status lines expanded. Ask
whether **Hide Processing Details** is on (Settings > Interface). Check whether the answer has
source chips or a tool-call block.

**Resolution.** Ask the model explicitly, for example "Search the web for the latest ...". If
details were hidden, explain the setting. If a model never searches, suggest another model.

**Escalation.** Send the model name and a description of the prompt to the platform admins, who
can check the model's function calling mode and built-in tool settings.

### 11.3 "It says '[ERROR: No results found from web search]'"

**Symptom.** The status line under the answer shows this text, and the answer has no web sources.

**Likely causes, in order.**
1. The engine genuinely found nothing for the generated queries.
2. A domain filter removed every result (allow-list entries keep only those sites) (section 5.13).
3. The engine failed **silently**: for Exa, External, Firecrawl, Microsoft Web IQ, Ollama Cloud,
   Perplexity, Perplexity Search, Yandex, Sougou and SerpApi, an error (for example an expired key
   or exhausted credit) looks like "no results" (section 7.3).

**Diagnostic steps.** Ask the user to retry with a simpler question. Ask whether every search
fails or only this one; if every search fails, cause 3 is likely.

**Resolution.** Rephrase; try again later.

**Escalation.** If all searches fail, send the time and chat id to the platform maintainer and ask
them to look for the engine's error line in the server log (section 10.7) and to check the
provider account.

### 11.4 "It searched the web but the answer doesn't use the results"

**Symptom.** The status shows a search happened but the answer ignores it, or the status reads
`Searched 0 sites` (possible when **Bypass Embedding and Retrieval** is on and no page loaded).

**Likely causes, in order.**
1. Every result page failed to load (blocked by the site, a bot check, a redirect that is not
   followed, or a script-built page), so nothing useful was read (section 5.6).
2. Only the best few chunks reach the model (Documents **Top K**, default 3), so most of each page
   is not used (section 5.7).
3. The model's `file_context` capability is off, so results are not added to the prompt (section 5.7).
4. **Bypass Web Loader** is on, so only short snippets were used.

**Diagnostic steps.** Expand `Searched ... sites` and open two or three of the pages in a browser:
do they load without a sign-in or a "verify you are human" step? Note whether the answer shows
`Retrieved ... sources` or `No sources found`.

**Resolution.** Suggest attaching a specific page with **Attach Webpage**, or pasting the text.

**Escalation.** Send the chat id, the listed pages and the status lines to the platform admins;
they can review the loader engine, **Top K** and the model's capabilities.

### 11.5 "It says 'Failed to embed and store the retrieved web pages...'"

**Symptom.** Status line: `Failed to embed and store the retrieved web pages. Check the embedding
configuration in Admin Settings > Documents.`

**Likely causes, in order.**
1. All loaded pages were empty, which the vector store refuses (section 5.7). The message
   mentions embedding even in this case.
2. The embedding model or service is failing (document uploads would fail too).

**Diagnostic steps.** Ask whether file uploads work in a new chat. Open the result pages (if
listed) to see whether they have readable text.

**Resolution.** If uploads also fail, treat it as an embedding outage
(`rag-retrieval-embeddings-and-vector-stores.md`, section 11). Otherwise suggest rephrasing.

**Escalation.** Send the time and chat id to the platform maintainer with "web search embedding
failure"; the log line is `Error saving web search results to vector DB`.

### 11.6 "It says '[ERROR: Something went wrong while searching the web.]'"

**Symptom.** Every search shows this status line; answers come without web results.

**Likely causes, in order.**
1. The engine is misconfigured: missing or invalid key or address (section 10.2). In legacy mode
   the precise reason is only in the server log.
2. The engine service is down, rate-limited or out of credit.
3. Every result address was refused by the address checks (section 5.12), or the loader is
   misconfigured (for example Playwright with no browser).
4. In the slim image, the engine is DDGS.

**Diagnostic steps.** Check whether it happens for everyone and for every question. Note the time
precisely.

**Resolution.** None at tier 1 beyond retrying later.

**Escalation.** Platform maintainer: ask for the `Web search failed` or `Web search content loading
failed` log entries at that time, and the configured engine.

### 11.7 "The AI says it can't search: 'No ... API key found in environment variables'"

**Symptom.** In native mode the answer quotes an error such as `No BRAVE_SEARCH_API_KEY found in
environment variables`, or the tool-call block shows `{"error": ...}`.

**Likely causes, in order.** The engine's key or address is empty (section 10.2), or the engine
value is empty or unknown (`No search engine API key found in environment variables`).

**Diagnostic steps.** Note the exact text; it names the missing setting.

**Resolution.** None at tier 1.

**Escalation.** Send the exact text to the platform admins; it says which field under Admin
Settings > **Web Search** is empty. (The wording says "environment variables" even when the value
is normally entered in the admin screen.)

### 11.8 "A 'Use Web Search?' window keeps popping up"

**Symptom.** Dialog `Use Web Search?` with **Continue** and **Cancel**.

**Likely causes, in order.** The admin requires confirmation before web search
(`web.search.confirmation.enable`); it appears again in each new chat and after web search is
switched off (section 5.2).

**Diagnostic steps.** None needed.

**Resolution.** Explain that **Continue** sends the question to the web search provider and is
remembered for that chat; **Cancel** keeps the chat offline. See also
`chat-composer-and-message-display.md`, section 11.16.

**Escalation.** Only if the wording needs changing (admin setting **Web Search Confirmation
Content**).

### 11.9 "Web search makes the answer very slow"

**Symptom.** Long wait at `Searching the web` or `Searched ... sites` before the answer starts.

**Likely causes, in order.**
1. Several queries, each with several results, means many pages to download and embed (up to
   result count × number of queries, section 5.5).
2. Slow or unresponsive sites: the Default loader has no Open WebUI time limit unless
   **Timeout** is set, and retries connection failures (section 5.15).
3. Playwright, Firecrawl, Tavily and Web IQ load pages one after another at a fixed rate.
4. A slow engine (several set no time limit) or a busy task model.

**Diagnostic steps.** Ask which status line it waits on and for how long; whether it happens with
every question.

**Resolution.** Suggest switching **Web Search** off for questions that do not need current
information.

**Escalation.** Send times and the status line it stalls on to the platform admins, who can review
**Timeout**, **Concurrent Requests** and the result count.

### 11.10 "Attach Webpage says '[ERROR: Error processing URL]'"

**Symptom.** Red pop-up after **Add**; the chip disappears.

**Likely causes, in order.**
1. The site returned an error (page not found, sign-in required, access denied to automated
   requests).
2. The address points to an internal or private network address and local web fetch is off
   (section 5.12).
3. The site's name cannot be resolved from the server, or the site is unreachable.

**Diagnostic steps.** Ask the user to open the address in a private browser window: does it load
without signing in? Is it an internal site (for example only reachable on campus or on VPN)?

**Resolution.** For public pages behind a sign-in, copy the relevant text into the message or save
the page as a file and attach it. Pages on private network addresses are refused unless the
platform allows local web fetch.

**Escalation.** If a public page that loads in a browser fails, send the address (with the user's
agreement), time and chat id to the platform maintainer for the server log.

### 11.11 "Attach Webpage says 'Please enter a valid URL.'"

**Symptom.** Red pop-up; the window stays open.

**Likely causes, in order.** The box contains no complete `http://` or `https://` address (for
example `www.example.com` without `https://`) (section 5.10).

**Diagnostic steps.** Look at what was typed.

**Resolution.** Copy the address from the browser's address bar, including `https://`; one address
per line.

**Escalation.** None.

### 11.12 "I can't attach a page from our internal site"

**Symptom.** Internal or intranet addresses fail with `[ERROR: Error processing URL]`; the AI's
`fetch_url` reports `The URL you provided is invalid. Please double-check and try again.`

**Likely causes, in order.** The address resolves to a private network address and
`ENABLE_LOCAL_WEB_FETCH` is off (default), or the server cannot reach that network (section 5.12).

**Diagnostic steps.** Confirm the site is internal.

**Resolution.** Explain that internal pages are blocked by design; suggest saving the page as a
PDF and attaching it as a file, if the content may be shared with the service.

**Escalation.** Requests to allow internal sites go to the platform owner; this is a security
decision (refer to U of T Information Security, security.utoronto.ca).

### 11.13 "My YouTube video won't attach"

**Symptom.** A red pop-up beginning `YouTube blocked ...`, `Transcripts are disabled ...`, `The
YouTube video ... is age restricted ...`, `... is unavailable.`, `No transcript found ...` or
`Could not retrieve a transcript ...` (section 10.3).

**Likely causes, in order.**
1. The video has no transcript (or none in the configured languages or English).
2. YouTube blocks requests from the server (`YouTube blocked ...`), common for cloud servers.
3. The video is private, removed or age restricted.

**Diagnostic steps.** Ask the user to check on YouTube whether the video offers a transcript and
in which language.

**Resolution.** Use another source, or paste the transcript text from YouTube into the message.

**Escalation.** For `YouTube blocked ...` or `YouTube requires additional verification ...`, send
the time and video address to the platform admins (they can configure **Youtube Proxy URL**). For
missing languages, ask them to review **Youtube Language**.

### 11.14 "It says 'You do not have permission to upload web content.'"

**Symptom.** **Attach Webpage** is greyed out with that tooltip, or the pop-up appears when a link
opens a chat with `?load-url=`.

**Likely causes, in order.** The user lacks `chat.web_upload` (section 3.3).

**Diagnostic steps.** Ask whether colleagues can attach pages.

**Resolution.** Explain it is a permission.

**Escalation.** Access requests go to whoever approves permissions for MedIT GPT (**TO BE
CONFIRMED**), with the user's account email and groups.

### 11.15 "The page I attached is empty or only says something like 'Moved Permanently'"

**Symptom.** The AI says the page has no useful content or quotes a redirect or error notice.

**Likely causes, in order.**
1. The address redirects (for example `http://` to `https://`, or to a new location) and redirects
   are not followed by default (section 5.6).
2. The page is built by scripts and the Default loader only reads the initial HTML.
3. The site served a bot check or cookie wall instead of the content.

**Diagnostic steps.** Open the address in a browser and compare the final address in the address
bar with the one attached.

**Resolution.** Attach the final address shown in the browser, or paste the text.

**Escalation.** If many sites behave this way, send examples to the platform admins (they can
review `AIOHTTP_CLIENT_ALLOW_REDIRECTS` and the loader engine).

### 11.16 "Attaching a link to a PDF says the file is too large"

**Symptom.** `Oops! The file you're trying to upload is too large. Please upload a file that is less
than {size}.`

**Likely causes, in order.** The linked file exceeds the site-wide upload size limit
(`rag.file.max_size`).

**Diagnostic steps.** Note the size shown in the message.

**Resolution.** Attach a smaller file or an excerpt.

**Escalation.** Limit changes go to the platform owner (see `files-uploads-and-storage.md`).

### 11.17 "Attaching a page says '[ERROR: Error querying knowledge base]'"

**Symptom.** Red pop-up after **Add**, although no knowledge base was involved.

**Likely causes, in order.**
1. The page loaded but no text could be extracted (script-built page, image-only page), and the
   empty result could not be stored (section 10.3).
2. The vector store or embedding service failed.

**Diagnostic steps.** Ask whether file uploads work. Open the page: is the text visible without
interaction?

**Resolution.** Paste the text, or save the page as PDF and attach it.

**Escalation.** If uploads also fail, follow `rag-retrieval-embeddings-and-vector-stores.md`.
Otherwise send examples to the platform admins (a Playwright loader reads script-built pages).

### 11.18 "(Admin) I pressed Save on the Web Search page and nothing happened"

**Symptom.** No `Settings saved successfully!` and no error.

**Likely causes, in order.**
1. A required field is empty or no engine is selected; the browser marks the field and blocks the
   save (section 7.7).
2. The server refused the save (slim image with DDGS or Playwright), which shows no pop-up.
3. The Linkup **Parameters** box contains invalid JSON.

**Diagnostic steps.** Scroll the panel for a highlighted field. Check which engine and loader are
selected.

**Resolution.** Admins only: complete the field or fix the JSON. Tier 1 does not change settings.

**Escalation.** If none of these apply, send the time to the platform maintainer for the server log.

### 11.19 "The AI used a site our domain filter should exclude"

**Symptom.** Results or fetched pages from sites the admin meant to exclude.

**Likely causes, in order.**
1. The page came through `fetch_url` or **Attach Webpage**, which the domain filter does not cover
   (section 5.13).
2. The engine does not apply the filter: Jina and Perplexity Search ignore it; Exa passes it to the
   provider instead (section 7.3).
3. The entry is written differently (missing `!`, or a parent domain such as `example.com` versus
   `www.example.com` in the wrong direction).

**Diagnostic steps.** Ask for the chat id and whether the page appeared under `Searched ... sites`
or in a `fetch_url` tool block.

**Resolution.** Explain the scope of the filter.

**Escalation.** Send examples and the engine name to the platform admins.

### 11.20 "Where does my web search go? Is it private?"

**Symptom.** A user asks whether their question is shared outside MedIT GPT.

**Likely causes, in order.** Not a fault: web search sends search queries derived from the
conversation to an outside search service, and page addresses to websites or a loader service
(section 5.14).

**Diagnostic steps.** None.

**Resolution.** Explain that with **Web Search** on, search queries based on their question leave
MedIT GPT for the search provider (in legacy mode the last six messages are also given to the task
model that writes those queries). Whether users may search with confidential or personal health
information, which provider MedIT GPT uses, and the approved wording for users are **TO BE
CONFIRMED**.

**Escalation.** Privacy questions go to the platform owner and the U of T Privacy Office
(privacy.utoronto.ca).

## 12. Local Customisations

**The web search and web loading code matches upstream Open WebUI v0.11.4.** `git diff main...uoft`
shows no change in `backend/open_webui/retrieval/web/`, the four web loaders,
`backend/open_webui/routers/retrieval.py`, `backend/open_webui/retrieval/utils.py`,
`backend/open_webui/utils/middleware.py`, `backend/open_webui/tools/builtin.py`,
`backend/open_webui/utils/tools.py`, `backend/open_webui/config.py`,
`src/lib/components/admin/Settings/WebSearch.svelte`, `src/lib/components/chat/MessageInput/`,
`src/lib/components/chat/Chat.svelte`, `src/lib/apis/retrieval/` or
`src/lib/components/chat/Messages/ResponseMessage/WebSearchResults.svelte`, and the working tree has no
uncommitted change in those files except an unrelated tool-approval fix in `Chat.svelte`
(`src/lib/components/chat/Chat.svelte:2847-2850`).

Fork changes that alter what users see here:

| Change | Effect on web search | Where |
|---|---|---|
| **Hide Processing Details** (personal Interface setting, fork; description in the working tree: `Show "Thinking..." instead of status updates, tool calls, reasoning, and code analysis while a response is generated, and keep them hidden afterwards. Tool approval requests and images or embeds from tools still appear.`) | Hides `Searching the web`, `Searched {{count}} sites`, error status lines and `search_web`/`fetch_url` tool-call blocks; shows "Thinking..." instead | `src/lib/components/chat/Messages/ResponseMessage.svelte:197-221`, `:720-721`; `src/lib/components/common/ToolCallDisplay.svelte:145`, `:199`; `src/lib/i18n/locales/en-US/translation.json:2923-2924` |
| **Inline Citations** (personal Interface setting, fork) | When off, the `[1]`-style markers for web sources are not shown in the text; sources are still listed under the answer | `src/lib/i18n/locales/en-US/translation.json:2935-2936`; mechanics in `rag-retrieval-embeddings-and-vector-stores.md`, section 12 |
| Product name **MedIT GPT** | Not used in this area's outbound requests: the licence-protected user-agent `Open WebUI (https://github.com/open-webui/open-webui) RAG Bot` is still sent to SearXNG, YaCy, External and Yandex, and `Open WebUI (https://github.com/open-webui/open-webui) External Web Loader` to the external loader; the Perplexity engines identify as `open-webui/{VERSION}` | `backend/open_webui/retrieval/web/searxng.py:14-18`; `backend/open_webui/retrieval/web/yacy.py:62-65`; `backend/open_webui/retrieval/web/external.py:24-27`; `backend/open_webui/retrieval/web/yandex.py:44-47`; `backend/open_webui/retrieval/loaders/external_web.py:33-36`; `backend/open_webui/retrieval/web/perplexity.py:66`; `backend/open_webui/retrieval/web/perplexity_search.py:47` |

Uncommitted working-tree changes touching display components in scope are cosmetic for this area:
a type annotation in `StatusItem.svelte` and **Hide Processing Details** now read from the settings
store inside `ToolCallDisplay.svelte` (`git diff -- src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte src/lib/components/common/ToolCallDisplay.svelte`).

## 13. Source File Index

### 13.1 In Scope (Read in Full or by Section)

| File | What it holds | Read |
|---|---|---|
| `backend/open_webui/retrieval/web/main.py` | Domain filter (`get_filtered_results`) and `SearchResult` | Full |
| `backend/open_webui/retrieval/web/utils.py` | Address checks, connection guards, the six web loaders and `get_web_loader` | Full |
| `backend/open_webui/retrieval/web/azure.py`, `bing.py`, `bocha.py`, `brave.py`, `brave_llm_context.py`, `duckduckgo.py`, `exa.py`, `external.py`, `firecrawl.py`, `google_pse.py`, `jina_search.py`, `kagi.py`, `linkup.py`, `microsoft_web_iq.py`, `mojeek.py`, `ollama.py`, `openserp.py`, `perplexity.py`, `perplexity_search.py`, `searchapi.py`, `searxng.py`, `serpapi.py`, `serper.py`, `serphouse.py`, `serply.py`, `serpstack.py`, `sougou.py`, `staan.py`, `tavily.py`, `yacy.py`, `yandex.py`, `ydc.py` | The 32 engine adapters (section 7.3) | Full |
| `backend/open_webui/retrieval/loaders/external_web.py`, `tavily.py`, `youtube.py`, `microsoft_web_iq.py` | External, Tavily, YouTube and Microsoft Web IQ loaders | Full |
| `backend/open_webui/routers/retrieval.py` | Settings key map (`:254-443`), settings endpoints (web parts of `:629-1398`), slim checks (`:962-983`), `save_docs_to_vector_db` (`:1705-1820`, partly), `_fetch_url`, `process_url`, `process_web`, `search_web`, `process_web_search` (`:2245-3047`), vector reset (`:3271-3284`) | By section |
| `backend/open_webui/retrieval/utils.py` | Loader settings, `get_loader`, `get_content_from_url` (`:60-301`); web-search collection access (`:1300-1350`); web items in `get_sources_from_items` (`:1380-1440`, `:1630-1718`) | By section |
| `backend/open_webui/utils/middleware.py` | `chat_web_search_handler` (`:1556-1730`); retrieval step (`:2049-2167`); feature gate (`:2660-2760`); built-in tool injection (`:2805-2815`, `:3110-3140`); file context and sources (`:3195-3260`); tool citations (`:395-481`, `:5841-5843`, `:6070-6120`) | By section |
| `backend/open_webui/tools/builtin.py` | `search_web` and `fetch_url` (`:289-362`) | By section |
| `backend/open_webui/utils/tools.py` | Built-in tool gates (`:520-720`) | By section |
| `backend/open_webui/config.py` | Local fetch and filter list, YouTube settings, web settings (`:1100-1349`); permissions (`:1859`, `:1908`, `:1984`, `:2009`); query template (`:2300-2333`); `DEFAULT_CONFIG` web keys (`:2939-3018`, `:3146-3148`) | By section |
| `src/lib/components/admin/Settings/WebSearch.svelte` | Admin Web Search panel | Full |
| `src/lib/components/chat/MessageInput/AttachWebpageModal.svelte` | **Attach Webpage** window | Full |
| `src/lib/components/chat/Messages/ResponseMessage/StatusHistory/StatusItem.svelte` | Status line texts (working-tree version) | Full |
| `src/lib/components/chat/Messages/ResponseMessage/WebSearchResults.svelte` | Expandable list of searched pages | Full |
| `src/lib/components/chat/Chat.svelte` | Web search activation, confirmation dialog, URL parameters, `uploadWeb` (`:330-380`, `:1080-1105`, `:1785-1900`, `:2155-2175`, `:3155-3180`, `:3400-3415`, `:4125-4145`, `:4215-4240`) | By section |
| `src/lib/components/chat/MessageInput.svelte`, `src/lib/components/chat/MessageInput/IntegrationsMenu.svelte`, `src/lib/components/chat/MessageInput/InputMenu.svelte` | Composer switch, chip and **Attach Webpage** menu item | By section |
| `src/lib/apis/retrieval/index.ts` | `updateRAGConfig`, `processUrl` and the unused web clients (`:60-95`, `:300-457`) | By section |

### 13.2 Read for Context (Owned by Other Areas)

| File | Why |
|---|---|
| `backend/open_webui/constants.py` | Message texts (`INVALID_URL`, `WEB_SEARCH_ERROR`, `FILE_TOO_LARGE`, `ACCESS_PROHIBITED`, `FEATURE_DISABLED`, `_error_message`) |
| `backend/open_webui/env.py` | Slim flag, queries cache, outbound HTTP settings, `TAVILY_API_BASE_URL`, SearXNG certificate, `USER_AGENT`, user-info header settings (`:45`, `:370`, `:540-660`, `:989-1008`) |
| `backend/open_webui/utils/misc.py` | Allow/block list matching (`:60-180`) |
| `backend/open_webui/utils/headers.py` | User-identity headers |
| `backend/open_webui/utils/session_pool.py` | Shared HTTP pool and its timeout |
| `backend/open_webui/routers/tasks.py` | Query generation task (`:400-477`) |
| `backend/open_webui/main.py` | Router mount (`:852`), `/api/config` web flags (`:2270-2366`), function calling default (`:1284-1296`), YouTube translation state (`:670`) |
| `backend/open_webui/utils/automations.py` | Default features in automations (`:160-200`, `:286-320`, `:466-492`) |
| `backend/open_webui/socket/main.py`, `backend/open_webui/models/chats.py`, `backend/open_webui/models/chat_messages.py` | Where status lines and sources are saved |
| `backend/open_webui/retrieval/vector/dbs/milvus_multitenancy.py`, `backend/open_webui/retrieval/vector/dbs/qdrant_multitenancy.py` | Shared web-search collections in multi-tenant stores |
| `src/lib/components/chat/Messages/ResponseMessage.svelte`, `src/lib/components/common/ToolCallDisplay.svelte` | Status and tool-call visibility, **Hide Processing Details** |
| `src/lib/components/chat/SettingsModal.svelte`, `src/routes/(app)/admin/settings/[tab]/+page.svelte` | Admin tab, route and save pop-up |
| `src/lib/components/common/SettingsSelect.svelte`, `src/lib/utils/index.ts` | Required drop-down; URL check |
| `src/lib/components/workspace/Models/Capabilities.svelte`, `DefaultFeatures.svelte`, `BuiltinTools.svelte`, `ModelEditor.svelte`; `src/lib/components/chat/Settings/Advanced/AdvancedParams.svelte` | Per-model web search switches and function calling |
| `src/lib/components/admin/Users/Groups/Permissions.svelte`, `src/lib/components/common/InterfaceSettings.svelte` | Permission switches; **Web Search in Chat** |
| `src/lib/i18n/locales/en-US/translation.json` | English text of dotted keys |
| `pyproject.toml`, `backend/requirements.txt`, `backend/requirements-slim.txt`, `Dockerfile`, `docker-compose.playwright.yaml` | Which optional packages and browsers are installed |

## 14. Open Questions

No contradiction with `knowledgebase/tools/ground-truth.md` or `CLAUDE.md` was found. Items below
could not be established from the repository.

### 14.1 Production Values (TO BE CONFIRMED)

1. Every live `web.*` value (78 keys): whether **Web Search** is on, which engine and loader are
   selected, whether keys are set (not their values), result count, concurrency, timeouts, domain
   filter list, both bypass switches, trust-proxy setting, confirmation switch and wording.
2. Live `rag.youtube_loader_language`, `rag.youtube_loader_proxy_url`, `task.query.search.enable`,
   `task.query.prompt_template`, `rag.top_k`, `rag.full_context`, `rag.file.max_size`, and the
   task model used for query generation (and whether it is an outside provider).
3. Environment-only values: `ENABLE_LOCAL_WEB_FETCH`, `WEB_FETCH_FILTER_LIST`,
   `AIOHTTP_CLIENT_ALLOW_REDIRECTS`, `AIOHTTP_CLIENT_TIMEOUT`, `AIOHTTP_CLIENT_SESSION_SSL`,
   `AIOHTTP_CLIENT_SSL_CERT_FILE`, `USER_AGENT`, `ENABLE_QUERIES_CACHE`, `TAVILY_API_BASE_URL`,
   the SearXNG client certificate, `ENABLE_FORWARD_USER_INFO_HEADERS` and the
   `FORWARD_USER_INFO_HEADER_*` values, `DEFAULT_LOCALE`.
4. Whether production runs the full or the slim image, and, if the Playwright loader is used,
   where its browser runs (`docker-compose.playwright.yaml` or another arrangement).
5. Default and group grants of `features.web_search` and `chat.web_upload`.
6. Per production model: function calling mode (native or legacy), the `web_search`,
   `file_context`, `citations`, `status_updates` and **Builtin Tools** capabilities, the **Builtin
   Tools** > **Web Search** category, and whether **Web Search** is a default feature.
7. Whether any automation runs a model with web search as a default feature.
8. The provider contract behind the chosen engine and loader (account owner, billing, rate limits,
   data residency and retention terms); not in the repository.

### 14.2 Privacy and Security (Refer, Do Not Investigate at Tier 1)

9. **User identity sent to four engines.** For `external`, `yandex`, `perplexity_search` and
   `microsoft_web_iq` the code adds the user's name, id, email and role (or a signed token
   carrying them) to every search request and does not consult `ENABLE_FORWARD_USER_INFO_HEADERS`
   (section 5.14). Whether this is intended upstream behaviour, and whether production uses one of
   these engines, needs review by the platform maintainer and the U of T Privacy Office.
10. **Chat-derived queries leave the service.** Queries generated from the last six messages go to
    the search provider; in legacy mode the messages also go to the task model. Whether this is
    acceptable for MedIT GPT conversations, and what users should be told, is TO BE CONFIRMED with
    the platform owner and the Privacy Office.
11. Users' browsers request favicons for every listed result from Google's favicon service when
    they expand `Searched ... sites` (section 5.14); whether that is acceptable is TO BE CONFIRMED.
12. Where and whether the server enforces `chat.web_upload` is security-sensitive: refer to the
    platform maintainer and U of T Information Security (security.utoronto.ca) (section 3.3).
13. The details of the address checks (section 5.12), including additional block-reason log lines
    not listed in 10.7, are security-sensitive: refer to the platform maintainer and U of T
    Information Security (security.utoronto.ca).
14. Retention: no code was found that removes `web-search-*` or attached-page collections other
    than a full vector-store reset (section 8), including when a chat or user is deleted. The retention expectation is TO BE CONFIRMED.

### 14.3 Behaviours to Confirm in a Test Environment

These are read from the code but were not run (the application was not started).

15. **Kagi with a domain filter**: the filter is applied to already-converted results, which have no
    `get` method, so any search with a filter list set appears to fail
    (`backend/open_webui/retrieval/web/kagi.py:31-39`; `backend/open_webui/retrieval/web/main.py:22`).
16. **Exa and block entries**: the raw filter list, including `!` entries, is sent to Exa as
    `includeDomains` (`backend/open_webui/retrieval/web/exa.py:34`); the effect is unknown.
17. **Loader Concurrent Requests set to 0**: the Default loader would wait indefinitely
    (`asyncio.Semaphore(0)`, `backend/open_webui/retrieval/web/utils.py:971`); the admin field
    is required but has no minimum (`src/lib/components/admin/Settings/WebSearch.svelte:1458-1463`).
18. **Azure engine and the admin panel**: `azure` is not among the drop-down options, so with the
    engine set to `azure` (from the environment) the required drop-down may show no selection and
    block saving any other Web Search setting (`src/lib/components/admin/Settings/WebSearch.svelte:20-52`,
    `:212-227`).
19. **Sougou** needs the `tencentcloud` package, which no dependency list installs; the engine
    should fail with a generic error.
20. **SSL pre-check** for the Playwright, Tavily and Microsoft Web IQ loaders connects directly to
    port 443 with the certifi bundle; pages behind a required proxy, on another port or signed by a
    private certificate authority may be skipped even though they load otherwise
    (`backend/open_webui/retrieval/web/utils.py:340-355`).
21. **Trust Proxy Environment** applies to the asynchronous (web search) path of the Default
    loader only; the synchronous path used for attachments and `fetch_url` always uses
    environment proxies (`backend/open_webui/retrieval/web/utils.py:957-959`, `:987`), and the
    Firecrawl and Tavily loaders compute a proxy they do not use
    (`backend/open_webui/retrieval/web/utils.py:413-421`, `:500-509`).
22. **Error and bot-check pages**: the Default loader does not check the HTTP status of result
    pages (`raise_for_status=False`, `backend/open_webui/retrieval/web/utils.py:943`, `:1003-1005`),
    so a site's error page text can be embedded as if it were content.
23. **Redirects**: what text an attached address that only redirects produces with
    `AIOHTTP_CLIENT_ALLOW_REDIRECTS` off.
24. **`file_context` off**: a legacy search runs and is shown, but its results are not added to the
    prompt (`backend/open_webui/utils/middleware.py:3207-3214`).
25. **`No search results found`** appears unreachable with the current server code (5.3, 10.1).
26. **`m.youtube.com` and `youtube-nocookie.com` addresses** do not match the YouTube check
    (`backend/open_webui/retrieval/utils.py:77-79`) and would go through the web loader, although
    the YouTube loader accepts those hosts (`backend/open_webui/retrieval/loaders/youtube.py:11-18`).
27. **Repeated requests**: an attached address is requested up to three times (download check,
    content-type probe, loader) (`backend/open_webui/routers/retrieval.py:2254-2273`;
    `backend/open_webui/retrieval/utils.py:279-292`); sites with strict rate limits may refuse.
28. **Duplicate results**: when two queries return the same page, it is loaded once but may be
    listed twice in the expanded `Searched ... sites` list (`backend/open_webui/routers/retrieval.py:2936-2993`).
29. The HTTP library's own default time limits (for the Default loader without **Timeout**, and
    engines that set none) are not defined in this repository.
30. **Bing**: whether the Bing Web Search v7 service is still available to new subscribers is
    outside the repository.

### 14.4 Organisational Items

31. Who owns the web search provider accounts and keys, and who rotates them: TO BE CONFIRMED.
32. Who approves `chat.web_upload` and `features.web_search` requests: TO BE CONFIRMED.
33. Support contacts and escalation routes for web search outages: TO BE CONFIRMED (see
    `knowledgebase/tools/ground-truth.md`, Contacts).
34. The approved user-facing wording for the confirmation dialog, if it is to be switched on: TO BE
    CONFIRMED.

### 14.5 Cross-Document Notes

35. `builtin-native-tools.md` (written in parallel) lists `web.fetch.max_content_length` as set in
    the "environment" (its settings table); the admin panel also offers it as **Fetch URL Content
    Length Limit** (`src/lib/components/admin/Settings/WebSearch.svelte:1170-1181`; section 7.1).
    Not corrected here; for that document's owner to review.
