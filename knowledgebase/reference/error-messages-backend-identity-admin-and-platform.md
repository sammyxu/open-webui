# Error Messages: Backend, Identity, Admin and Platform

## At a Glance

- A catalogue of every backend error, warning and notice message raised by the identity, admin and platform code of MedIT GPT (Open WebUI v0.11.4): the shared `ERROR_MESSAGES`, `MESSAGES` and `WEBHOOK_MESSAGES` text in `backend/open_webui/constants.py`, the routers for sign-in, users, groups, SCIM, configuration, utilities, pipelines, functions, analytics, evaluations, tasks and notifications, the auth, OAuth, rate-limit and plugin helpers, `main.py`, the websocket server, the database layer and the start-up configuration files.
- Most messages reach the user as the `detail` field of a JSON error response, which the front end prints in a toast or on the sign-in page; start-up messages appear only in the server output.
- Look a message up by its exact text, then by a long fragment, then by HTTP status code (section 5); rows that another reference document already explains point there.
- Provisional summary; refined at the end of research.
- *Added 2026-10-10 on completion:* section 10 has one subsection per source file (10.2 to 10.22, about 280 rows; 10.23 points to the full constants table in section 4.6). Most rows also appear in a subsystem document and point there; start-up failures (sections 10.20 to 10.22) and several websocket and readiness texts are explained only here. Server texts are shown in English whatever the interface language. Section 11 gives triage for the eight texts tickets quote most, and section 14.2 lists texts that the code cannot actually show.

## 1. Purpose and Who Uses It

This document is a look-up catalogue. A ticket arrives with a message the user saw ("Your session has expired or the token is invalid", "We could not find what you're looking for :/", "API rate limit exceeded"), and support needs to know which part of the server produced it, what condition triggers it, what the user can do, and what to check before escalating.

| Reader | Uses it for |
|---|---|
| Tier-1 support | Match a quoted message to its source and trigger; give the user the right next step; decide whether to escalate |
| Tier-2 support and the platform maintainer | Find every place a shared message is raised (for example the 189 uses of `NOT_FOUND`), read start-up failures, check readiness responses |
| Writers of the numbered guides | One place that lists every shared `ERROR_MESSAGES` text and the files that use it (section 4.6) |

**Scope.** All of `backend/open_webui/constants.py` (every `ERROR_MESSAGES`, `MESSAGES`, `WEBHOOK_MESSAGES` and `TASKS` member); the routers `auths`, `users`, `groups`, `scim`, `configs`, `utils`, `pipelines`, `functions`, `analytics`, `evaluations`, `tasks` and `notifications` in `backend/open_webui/routers/`; the helpers `backend/open_webui/utils/{auth,oauth,rate_limit,plugin}.py`; `backend/open_webui/main.py`; the websocket server `backend/open_webui/socket/main.py`; the database layer `backend/open_webui/internal/db.py`; and the start-up configuration files `backend/open_webui/env.py` and `backend/open_webui/config.py`.

**Companion catalogues.** Messages from the chat, content and feature routers (`chats`, `files`, `knowledge`, `retrieval`, `models`, `openai`, `ollama` and others) are in `error-messages-backend-chat-content-and-features.md`; browser-side toasts are in `error-messages-frontend-chat-and-navigation.md` and `error-messages-frontend-admin-workspace-and-settings.md`; status lines inside a reply are in `in-chat-status-and-response-messages.md`. Those documents may not exist yet at the time of writing (section 14).

**How rows point elsewhere.** Many messages in scope are already explained in a subsystem document (for example `authentication-and-sign-in.md` for sign-in, `sso-oauth-oidc-and-scim.md` for single sign-on and SCIM). For those, the row here keeps the trigger short and the **Support check** column says `See <document>.md section 10`. Messages that no other document explains have their trigger written in full here.

## 2. Navigation and URLs

These messages have no screen of their own. They appear wherever a server response reaches the user or an operator.

### 2.1 Where a Server Message Appears

| Where | How the text gets there | Evidence |
|---|---|---|
| **A toast** (the small pop-up message, usually top right) | Almost every front-end API function throws the parsed JSON body when the response is not OK, keeps its `detail` field, and re-throws it; the calling component prints it with ``toast.error(`${error}`)`` | `src/lib/apis/auths/index.ts:13-25` (the pattern repeats in every module under `src/lib/apis/`); `src/routes/auth/+page.svelte:74-75` |
| **The sign-in page** (`/auth`) | Password, sign-up, LDAP and session errors are toasts; single sign-on failures arrive as a redirect to `/auth?error=<message>`, which the page shows as a toast | `src/routes/auth/+page.svelte:74-75`, `:91-92`, `:101-102`, `:141-142`, `:168-170`; `backend/open_webui/utils/oauth.py:2167-2181` |
| **The home page** (`/`) | A tool-server sign-in (OAuth for an MCP or OpenAPI tool) that fails redirects to `/?error=<message>`; the page shows it as a toast, or `An unknown error occurred.` when the parameter is empty | `src/routes/(app)/+page.svelte:9-10`; `backend/open_webui/utils/oauth.py:1321-1324` |
| **Inside a chat reply** | A chat request that fails shows the server `detail` as a toast and inside the reply after `Uh-oh! There was an issue with the response.` | `src/lib/components/chat/Chat.svelte:3716-3756`; see `chat-completion-pipeline-and-generation-tasks.md` |
| **A JSON API response** | Scripts and OpenAI-compatible clients that call the API with a token or API key receive `{"detail": "<message>"}` with the HTTP status (section 3) | FastAPI's handler for `HTTPException`; `backend/open_webui/main.py:515-517` adds one custom handler |
| **Server start-up output** | Configuration errors stop the server with a Python traceback or exit message on standard output; warnings are log lines | `backend/open_webui/env.py:780-788`; `backend/open_webui/internal/db.py:145-153`; `backend/open_webui/config.py:648-670` |
| **Load balancer or health check** | `/ready` answers HTTP 503 with a short reason until the server is ready | `backend/open_webui/main.py:2968-3006` |

### 2.2 URLs Mentioned in This Catalogue

| URL (relative to the site root) | What it is | Evidence |
|---|---|---|
| `/auth` | Sign-in page; shows `?error=` | `src/routes/auth/+page.svelte:168-170` |
| `/?error=<message>` | Home page with an error toast (tool-server sign-in) | `src/routes/(app)/+page.svelte:9-10` |
| `/api/v1/auths/...` | Sign-in, sign-up, profile, password, API keys, admin authentication settings | `backend/open_webui/routers/auths.py` |
| `/api/v1/users/...`, `/api/v1/groups/...` | User and group management | `backend/open_webui/routers/users.py`; `backend/open_webui/routers/groups.py` |
| `/api/v1/scim/v2/...` | SCIM provisioning, mounted only when `ENABLE_SCIM` is on | `backend/open_webui/main.py:843-887` (per `CLAUDE.md`) |
| `/api/v1/configs/...` | Admin settings endpoints (tool servers, terminals, OAuth client registration) | `backend/open_webui/routers/configs.py` |
| `/api/v1/utils/...` | Code formatting, code execution, database download | `backend/open_webui/routers/utils.py` |
| `/api/v1/functions/...`, `/api/v1/pipelines/...` | Functions and the external Pipelines server | `backend/open_webui/routers/functions.py`; `backend/open_webui/routers/pipelines.py` |
| `/api/v1/tasks/...` | Title, tags, follow-up, query, autocomplete, emoji and mixture-of-agents generation | `backend/open_webui/routers/tasks.py` |
| `/api/v1/evaluations/...`, `/api/v1/analytics/...` | Feedback and the admin analytics dashboard | `backend/open_webui/routers/evaluations.py`; `backend/open_webui/routers/analytics.py` |
| `/api/v1/notifications/...` | Personal notification targets | `backend/open_webui/routers/notifications.py` |
| `/ready`, `/health` | Readiness and liveness checks | `backend/open_webui/main.py:2963-3006` |
| `/oauth/{provider}/login`, `/oauth/{provider}/login/callback` | Single sign-on | `backend/open_webui/main.py:2828-2850` |
| `/oauth/clients/{client_id}/authorize`, `/oauth/clients/{client_id}/callback` | Tool-server OAuth | `backend/open_webui/main.py:2772-2825` |

## 3. Roles and Permissions

### 3.1 The Role-Check Rule: 401 Does Not Always Mean "Signed Out"

Most endpoints are guarded by one of two checks. Both refuse with **HTTP 401** (not 403) and the `ACCESS_PROHIBITED` text `You do not have permission to access this resource. Please contact your administrator for assistance.`:

| Check | Lets through | Refuses | Evidence |
|---|---|---|---|
| `get_verified_user` | role `user` or `admin` | `pending` accounts (and any other role) | `backend/open_webui/utils/auth.py:567-576` |
| `get_admin_user` | role `admin` | everyone else | `backend/open_webui/utils/auth.py:625-631` |

Both run after `get_current_user`, which first checks that a sign-in token or API key is present and valid (section 10.14). So a 401 can mean five different things, and the **text** tells them apart:

| Text with HTTP 401 | Meaning |
|---|---|
| `Not authenticated` | No token was sent at all |
| `401 Unauthorized` | The token has expired or can no longer be read, for example after the server's secret key changed (the token reader returns nothing instead of raising, `backend/open_webui/utils/auth.py:246-251`, so this text and not `Invalid token` is what an expired token produces, `:489-493`) |
| `Invalid token` | The token was revoked, which needs Redis: a sign-out with that token, a password change or admin reset, or an identity-provider logout (`backend/open_webui/utils/auth.py:449-453`) |
| `Your session has expired or the token is invalid. Please sign in again.` | The token is readable but its account no longer exists, or an API key matches no user |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Signed in, but the role is not enough (pending user, or a non-admin on an admin endpoint) |

Several routers also answer **401 with the not-found text** `We could not find what you're looking for :/` when an item does not exist (functions and groups; for example `backend/open_webui/routers/functions.py:277`, `backend/open_webui/routers/groups.py:110`). Treat those as "not found", not as a sign-in problem.

### 3.2 Status Codes Used in This Catalogue

| Status | Usual meaning here | Example |
|---|---|---|
| 400 | The request was refused: bad input, a rule failed, or an internal error was reported as a generic failure | `The email or password provided is incorrect. Please check for typos and try logging in again.` |
| 401 | Not signed in, token not accepted, or role too low (section 3.1); also some not-found answers | `Invalid token` |
| 403 | A specific permission, feature switch or safety rule refused the action | `The requested action has been restricted as a security measure.` |
| 404 | The item does not exist or the caller may not see it; a bare 404 has the text `Not Found` | `We could not find what you're looking for :/` |
| 409 | SCIM only: the user already exists | `User with email {email} already exists` |
| 422 | The request body failed validation before the endpoint ran (FastAPI's own response, a list of problems rather than one text) | Translation overrides with a bad key (section 10.2) |
| 429 | Too many sign-in or token-exchange attempts | `API rate limit exceeded` |
| 500 | The server failed while doing the work | `Oops! Something went wrong while creating your account. Please try again later. If the issue persists, contact support for assistance.` |
| 502 | An upstream model provider could not be reached (Anthropic-compatible endpoint) | `Open WebUI: Server Connection Error` |
| 503 | `/ready` only: start-up not finished, or the database or Redis is down | `Database not ready` |

### 3.3 What Tier 1 May Do

Tier 1 is read-only: it never changes roles, settings, groups or data. For every message here the resolution is guidance to the user or an escalation with the identifiers listed in section 11. Role changes (for example activating a pending account) are an administrator action.

## 4. Key Concepts and Terminology

### 4.1 `detail`: the Text of a Server Error

When the server refuses a request it answers with an HTTP status code (section 3.2) and a JSON body whose `detail` field holds the message, for example `{"detail": "API rate limit exceeded"}`. The web framework builds that body from `HTTPException(status_code, detail)` (`.venv/lib/python3.12/site-packages/fastapi/exception_handlers.py:11-17`, the installed library). The only custom error handler in the application turns a schedule that takes too long to evaluate into an HTTP 400 with the error's text (`backend/open_webui/main.py:515-517`).

Two consequences for support:

- **The toast is usually the `detail` itself**, with nothing added (section 2.1). Asking the user for the exact wording of the toast is the fastest way to find the row in section 10.
- **A validation failure (HTTP 422) has no single text.** Its `detail` is a list of problems (`.venv/lib/python3.12/site-packages/fastapi/exception_handlers.py:20-26`). A component that prints the error with a template string would show the list as `[object Object]` (read from the front-end pattern in section 2.1; confirm in a test environment, section 14). Some documents note that validation texts arrive prefixed with `Value error, ` (for example `authentication-and-sign-in.md` section 10).

### 4.2 How `ERROR_MESSAGES.DEFAULT` Formats a Message

`ERROR_MESSAGES.DEFAULT` is not a fixed text. It is a formatter (`backend/open_webui/constants.py:16-23`, `:41`) that hides the technical reason and shows either a generic sentence or the name of the operation that failed:

| How the code calls it | What the user sees | Example in scope |
|---|---|---|
| With nothing | `Something went wrong :/` | `backend/open_webui/routers/evaluations.py:434-437` |
| With a text | `[ERROR: {text}]` | `ERROR_MESSAGES.DEFAULT('Error creating group')` gives `[ERROR: Error creating group]` (`backend/open_webui/routers/groups.py:82-85`) |
| With an exception and a fallback text | `[ERROR: {fallback}]`; the exception's own text is not shown | `backend/open_webui/routers/groups.py:88-93` |
| With an exception only | `Something went wrong :/` | none in scope; used by content routers (companion catalogue) |
| With a storage error the server recognizes | `[ERROR: File name is too long.]`, `[ERROR: The server is out of storage space.]`, `[ERROR: Server storage quota exceeded.]` or `[ERROR: Server storage is not writable.]` | `backend/open_webui/constants.py:6-13`, `:19-20` |

So a `[ERROR: …]` message names **what** failed, not **why**. The reason, when the code records it, is in the server log at the same moment (section 11).

### 4.3 Text Members and Function Members

`ERROR_MESSAGES` is a Python string enumeration. Most members are fixed texts; the class overrides `__str__` so that the member converts to its text wherever the code prints it (`backend/open_webui/constants.py:37-39`). Thirteen members are **functions** that fill in a value: `DEFAULT`, `INCORRECT_FORMAT`, `MODEL_NOT_FOUND`, `OPENAI_NOT_FOUND`, `FILE_TOO_LARGE`, `INVALID_PASSWORD`, `AUTOMATION_LIMIT_EXCEEDED`, `AUTOMATION_TOO_FREQUENT`, `AUTOMATION_INVALID_RRULE`, `FEATURE_DISABLED`, `INPUT_TOO_LONG`, `REQUIRED_FIELD_EMPTY` and `OAUTH_NOT_CONFIGURED`. Python does not turn functions defined in an enumeration into members, so the code must call them. Three oddities follow:

| Oddity | Effect | Evidence |
|---|---|---|
| Called with no value | `ERROR_MESSAGES.MODEL_NOT_FOUND()` gives `Model '' was not found`, with an empty name; every use in the tasks router is like this | `backend/open_webui/constants.py:89`; `backend/open_webui/routers/tasks.py:164-167` and seven more (section 10.12) |
| Not called at all | `backend/open_webui/routers/openai.py:673` passes `ERROR_MESSAGES.OPENAI_NOT_FOUND` itself as the `detail`. Read from code, the error handler cannot turn a function into JSON, so that response would be a generic server error instead of a 401 carrying `OpenAI API was not found` | `backend/open_webui/constants.py:90`; `.venv/lib/python3.12/site-packages/fastapi/exception_handlers.py:15-17` |
| Same text twice | `USER_NOT_FOUND` has exactly the text of `NOT_FOUND`, so Python treats it as another name for that member; users cannot tell them apart | `backend/open_webui/constants.py:78-79` |

**Members no code uses.** `ENV_VAR_NOT_FOUND`, `EMAIL_MISMATCH`, `USERNAME_TAKEN`, `NAME_TAG_TAKEN`, `FILE_NOT_SENT` and `MALICIOUS` are defined but never raised in the backend, and the `MESSAGES` and `WEBHOOK_MESSAGES` classes are not read anywhere (`grep` of `backend/open_webui` for each name). If a ticket quotes one of these texts, it did not come from the v0.11.4 server code; a plugin stored in the database could still raise it (section 14).

### 4.4 The `{status}: {detail}` Form and the Bare `Not Found`

The web framework's error class has a text form of `{status}: {detail}` (`.venv/lib/python3.12/site-packages/starlette/exceptions.py:15-16`). When server code catches an HTTP error and passes its text on, the user, the log or the model sees the status number in front. In this catalogue's scope the LDAP sign-in hides its detailed reason from the user and logs it as `LDAP authentication error: {e}`, which therefore reads, for example, `LDAP authentication error: 400: Application account bind failed` (`backend/open_webui/routers/auths.py:707-709`). Elsewhere the same form appears as `400: Model not found` in an automation's run record (`automations-calendar-and-timers.md` section 5) or in a built-in tool's error given to the model (`image-generation-and-editing.md` section 10). An HTTP error raised **without** a `detail` gets the standard reason phrase as its text (`.venv/lib/python3.12/site-packages/starlette/exceptions.py:9-10`): a bare 404 reads `Not Found`. In this catalogue that happens for unknown single sign-on providers, unknown tool-server OAuth clients and the switched-off back-channel logout endpoint (sections 10.15 and 10.18).

### 4.5 The Licence-Protected `Open WebUI: Server Connection Error`

`SERVER_CONNECTION_ERROR` is the text `Open WebUI: Server Connection Error`. A comment above it says the LICENSE covers this identifier and that it must not be altered except as the licence permits (`backend/open_webui/constants.py:127-130`); the same text appears as a literal with the same comment in `backend/open_webui/routers/openai.py:664-670`. The `uoft` fork rebranded the product to MedIT GPT but did not change this text (section 12), so MedIT GPT users can see "Open WebUI" in this error. It means the server could not reach a model provider (in scope: the Anthropic-compatible endpoint, section 10.18); it does not mean the user is on the wrong site.

### 4.6 Every Member of `constants.py`

This table lists every member of the four classes in `backend/open_webui/constants.py`: `ERROR_MESSAGES` (58 names, of which 45 are text members and 13 functions), `MESSAGES` (3), `WEBHOOK_MESSAGES` (2) and `TASKS` (10). "Used in" counts every reference outside `constants.py` found by `grep -rnoE` over `backend/open_webui` (paths are relative to `backend/open_webui/`). The Notes column points to the section of this catalogue that lists the message, or to the document that covers it when every use is outside this catalogue's scope.

| Class | Member | Defined at | Kind | Text (verbatim) | Used in (paths under `backend/open_webui/`, with counts) | Notes |
|---|---|---|---|---|---|---|
| `MESSAGES` | `DEFAULT` | `backend/open_webui/constants.py:27` | function (msg) | `{msg}` (empty when no message) | not used | The `MESSAGES` class has no members in use; nothing in the backend reads it |
| `MESSAGES` | `MODEL_ADDED` | `backend/open_webui/constants.py:28` | function (model) | `The model '{model}' has been added successfully.` | not used | Not used (`EVENTS.MODEL_DELETED` in `backend/open_webui/events.py:444` is a different thing) |
| `MESSAGES` | `MODEL_DELETED` | `backend/open_webui/constants.py:29` | function (model) | `The model '{model}' has been deleted successfully.` | not used | Not used |
| `WEBHOOK_MESSAGES` | `DEFAULT` | `backend/open_webui/constants.py:33` | function (msg) | `{msg}` (empty when no message) | not used | The `WEBHOOK_MESSAGES` class is not read anywhere in the backend |
| `WEBHOOK_MESSAGES` | `USER_SIGNUP` | `backend/open_webui/constants.py:34` | function (username) | `New user signed up: {username}`, or without a name `New user signed up` | not used | Not used; sign-up notifications are built elsewhere (see `notifications-webhooks-events-and-banners.md`) |
| `ERROR_MESSAGES` | `DEFAULT` | `backend/open_webui/constants.py:41` | function | `Something went wrong :/` or `[ERROR: {text}]` | main.py (5), routers/audio.py (1), routers/auths.py (1), routers/automations.py (2), routers/channels.py (60), routers/chats.py (21), routers/evaluations.py (1), routers/files.py (13), routers/folders.py (10), routers/functions.py (12), routers/groups.py (11), routers/images.py (5), routers/knowledge.py (2), routers/models.py (3), routers/notes.py (13), routers/prompts.py (5), routers/retrieval.py (16), routers/skills.py (6), routers/tools.py (9), routers/users.py (1), routers/utils.py (1), utils/oauth.py (1) | A formatter, not a fixed text: `Something went wrong :/` or `[ERROR: {text}]` (section 4.2). In scope: 10.2, 10.3, 10.4, 10.7, 10.9, 10.11, 10.15, 10.18 |
| `ERROR_MESSAGES` | `ENV_VAR_NOT_FOUND` | `backend/open_webui/constants.py:42` | text | `Required environment variable not found. Terminating now.` | not used | Not used |
| `ERROR_MESSAGES` | `CREATE_USER_ERROR` | `backend/open_webui/constants.py:43` | text | `Oops! Something went wrong while creating your account. Please try again later. If the issue persists, contact support for assistance.` | routers/auths.py (3), utils/oauth.py (1) | Sections 10.2, 10.15 |
| `ERROR_MESSAGES` | `DELETE_USER_ERROR` | `backend/open_webui/constants.py:44` | text | `Oops! Something went wrong. We encountered an issue while trying to delete the user. Please give it another shot.` | routers/users.py (1) | Section 10.3 |
| `ERROR_MESSAGES` | `EMAIL_MISMATCH` | `backend/open_webui/constants.py:45` | text | `Uh-oh! This email does not match the email your provider is registered with. Please check your email and try again.` | not used | Not used |
| `ERROR_MESSAGES` | `EMAIL_TAKEN` | `backend/open_webui/constants.py:46` | text | `Uh-oh! This email is already registered. Sign in with your existing account or choose another email to start anew.` | routers/auths.py (2), routers/users.py (1), utils/oauth.py (1) | Sections 10.2, 10.3, 10.15 |
| `ERROR_MESSAGES` | `USERNAME_TAKEN` | `backend/open_webui/constants.py:47` | text | `Uh-oh! This username is already registered. Please choose another username.` | not used | Not used |
| `ERROR_MESSAGES` | `PASSWORD_TOO_LONG` | `backend/open_webui/constants.py:48` | text | `Uh-oh! The password you entered is too long. Please make sure your password is less than 72 bytes long.` | utils/auth.py (1) | Raised by `validate_password`; reaches users through sections 10.2 and 10.3 (section 10.14) |
| `ERROR_MESSAGES` | `COMMAND_TAKEN` | `backend/open_webui/constants.py:51` | text | `Uh-oh! This command is already registered. Please choose another command string.` | routers/prompts.py (3) | Prompts; see the companion catalogue and `prompts-and-skills.md` |
| `ERROR_MESSAGES` | `FILE_EXISTS` | `backend/open_webui/constants.py:52` | text | `Uh-oh! This file is already registered. Please choose another file.` | routers/knowledge.py (3) | Knowledge bases; see `knowledge-bases.md` |
| `ERROR_MESSAGES` | `ID_TAKEN` | `backend/open_webui/constants.py:54` | text | `Uh-oh! This id is already registered. Please choose another id string.` | routers/functions.py (1), routers/knowledge.py (1), routers/skills.py (1), routers/tools.py (1) | Section 10.9; also tools, skills and knowledge |
| `ERROR_MESSAGES` | `MODEL_ID_TAKEN` | `backend/open_webui/constants.py:55` | text | `Uh-oh! This model id is already registered. Please choose another model id string.` | routers/models.py (2) | Workspace models; see `workspace-models-and-model-access.md` |
| `ERROR_MESSAGES` | `NAME_TAG_TAKEN` | `backend/open_webui/constants.py:56` | text | `Uh-oh! This name tag is already registered. Please choose another name tag string.` | not used | Not used |
| `ERROR_MESSAGES` | `MODEL_ID_TOO_LONG` | `backend/open_webui/constants.py:57` | text | `The model id is too long. Please make sure your model id is less than 256 characters long.` | routers/models.py (1) | Workspace models; see `workspace-models-and-model-access.md` |
| `ERROR_MESSAGES` | `INVALID_TOKEN` | `backend/open_webui/constants.py:59` | text | `Your session has expired or the token is invalid. Please sign in again.` | routers/auths.py (1), routers/chats.py (1), utils/auth.py (2) | Sections 10.2, 10.14 |
| `ERROR_MESSAGES` | `INVALID_CRED` | `backend/open_webui/constants.py:60` | text | `The email or password provided is incorrect. Please check for typos and try logging in again.` | routers/auths.py (6), utils/oauth.py (9) | Sections 10.2, 10.15; also shown for single sign-on failures |
| `ERROR_MESSAGES` | `INVALID_EMAIL_FORMAT` | `backend/open_webui/constants.py:61` | text | `The email format you entered is invalid. Please double-check and make sure you're using a valid email address (e.g., yourname@example.com).` | routers/auths.py (2) | Section 10.2 |
| `ERROR_MESSAGES` | `INCORRECT_PASSWORD` | `backend/open_webui/constants.py:62` | text | `The password provided is incorrect. Please check for typos and try again.` | routers/auths.py (1) | Section 10.2 |
| `ERROR_MESSAGES` | `INVALID_TRUSTED_HEADER` | `backend/open_webui/constants.py:63` | text | `Your provider has not provided a trusted header. Please contact your administrator for assistance.` | routers/auths.py (1) | Section 10.2 |
| `ERROR_MESSAGES` | `EXISTING_USERS` | `backend/open_webui/constants.py:67` | text | `You can't turn off authentication because there are existing users. If you want to disable WEBUI_AUTH, make sure your web interface doesn't have any existing users and is a fresh installation.` | routers/auths.py (1) | Section 10.2 |
| `ERROR_MESSAGES` | `UNAUTHORIZED` | `backend/open_webui/constants.py:69` | text | `401 Unauthorized` | routers/automations.py (2), routers/calendar.py (2), routers/channels.py (6), routers/knowledge.py (2), routers/models.py (7), routers/notes.py (12), routers/prompts.py (1), routers/skills.py (6), routers/tools.py (6), utils/auth.py (1) | Section 10.14 (expired or unreadable token); the other uses are permission refusals in content routers. *Corrected 2026-10-10: this note first said "ownership refusals"; most of those uses refuse a missing feature or workspace permission (for example `backend/open_webui/routers/models.py:293-298`), and others missing write access (`:1130-1138`).* |
| `ERROR_MESSAGES` | `ACCESS_PROHIBITED` | `backend/open_webui/constants.py:70` | text | `You do not have permission to access this resource. Please contact your administrator for assistance.` | routers/audio.py (2), routers/auths.py (5), routers/chats.py (21), routers/folders.py (11), routers/images.py (4), routers/knowledge.py (14), routers/memories.py (1), routers/models.py (6), routers/notifications.py (1), routers/ollama.py (4), routers/openai.py (2), routers/prompts.py (10), routers/retrieval.py (3), routers/skills.py (1), routers/tools.py (7), routers/utils.py (1), utils/auth.py (3), utils/oauth.py (3), utils/tool_approval.py (1) | The role-check text (section 3.1). In scope: 10.2, 10.7, 10.13, 10.14, 10.15 |
| `ERROR_MESSAGES` | `ACTION_PROHIBITED` | `backend/open_webui/constants.py:73` | text | `The requested action has been restricted as a security measure.` | routers/auths.py (4), routers/users.py (6) | Sections 10.2, 10.3 |
| `ERROR_MESSAGES` | `FILE_NOT_SENT` | `backend/open_webui/constants.py:75` | text | `FILE_NOT_SENT` | not used | Not used (the text is the identifier itself) |
| `ERROR_MESSAGES` | `FILE_NOT_SUPPORTED` | `backend/open_webui/constants.py:76` | text | `Oops! It seems like the file format you're trying to upload is not supported. Please upload a file with a supported format and try again.` | routers/audio.py (1) | Audio; see `audio-speech-to-text-and-text-to-speech.md` |
| `ERROR_MESSAGES` | `NOT_FOUND` | `backend/open_webui/constants.py:78` | text | `We could not find what you're looking for :/` | main.py (4), routers/audio.py (1), routers/automations.py (4), routers/channels.py (34), routers/chats.py (13), routers/evaluations.py (3), routers/files.py (22), routers/folders.py (11), routers/functions.py (11), routers/groups.py (4), routers/knowledge.py (30), routers/memories.py (2), routers/models.py (4), routers/notes.py (8), routers/notifications.py (2), routers/prompts.py (14), routers/retrieval.py (2), routers/skills.py (5), routers/tools.py (12), utils/tool_approval.py (3) | The most used text. In scope: 10.4, 10.9, 10.11, 10.13, 10.18 |
| `ERROR_MESSAGES` | `USER_NOT_FOUND` | `backend/open_webui/constants.py:79` | text | `We could not find what you're looking for :/` | routers/users.py (10) | Same text as `NOT_FOUND` (Python treats it as an alias of that member). Section 10.3 |
| `ERROR_MESSAGES` | `API_KEY_NOT_FOUND` | `backend/open_webui/constants.py:80` | text | `Oops! It looks like there's a hiccup. The API key is missing. Please make sure to provide a valid API key to access this feature.` | routers/auths.py (1) | Section 10.2 |
| `ERROR_MESSAGES` | `API_KEY_NOT_ALLOWED` | `backend/open_webui/constants.py:81` | text | `Use of API key is not enabled in the environment.` | utils/auth.py (2) | Section 10.14 |
| `ERROR_MESSAGES` | `MALICIOUS` | `backend/open_webui/constants.py:83` | text | `Unusual activities detected, please try again in a few minutes.` | not used | Not used |
| `ERROR_MESSAGES` | `PANDOC_NOT_INSTALLED` | `backend/open_webui/constants.py:85` | text | `Pandoc is not installed on the server. Please contact your administrator for assistance.` | routers/retrieval.py (1) | Retrieval; see the companion catalogue |
| `ERROR_MESSAGES` | `INCORRECT_FORMAT` | `backend/open_webui/constants.py:86` | function (err) | `Invalid format. Please use the correct format{err}` | routers/images.py (3) | Image generation; see `image-generation-and-editing.md` |
| `ERROR_MESSAGES` | `RATE_LIMIT_EXCEEDED` | `backend/open_webui/constants.py:87` | text | `API rate limit exceeded` | routers/auths.py (2) | Section 10.2 (sign-in and token exchange) |
| `ERROR_MESSAGES` | `MODEL_NOT_FOUND` | `backend/open_webui/constants.py:89` | function (name) | `Model '{name}' was not found` | routers/ollama.py (9), routers/openai.py (2), routers/tasks.py (8) | Section 10.12 calls it with no name, so users see `Model '' was not found` |
| `ERROR_MESSAGES` | `OPENAI_NOT_FOUND` | `backend/open_webui/constants.py:90` | function (name) | `OpenAI API was not found` | routers/openai.py (1) | Passed **uncalled** at `backend/open_webui/routers/openai.py:673`, so that response cannot carry this text (section 4.3) |
| `ERROR_MESSAGES` | `OLLAMA_NOT_FOUND` | `backend/open_webui/constants.py:91` | text | `WebUI could not connect to Ollama` | routers/ollama.py (1) | Ollama connections; see `model-connections-openai-ollama-and-direct.md` |
| `ERROR_MESSAGES` | `CREATE_API_KEY_ERROR` | `backend/open_webui/constants.py:92` | text | `Oops! Something went wrong while creating your API key. Please try again later. If the issue persists, contact support for assistance.` | routers/auths.py (1) | Section 10.2 |
| `ERROR_MESSAGES` | `API_KEY_CREATION_NOT_ALLOWED` | `backend/open_webui/constants.py:93` | text | `API key creation is not allowed in the environment.` | routers/auths.py (1) | Section 10.2 |
| `ERROR_MESSAGES` | `EMPTY_CONTENT` | `backend/open_webui/constants.py:95` | text | `The content provided is empty. Please ensure that there is text or data present before proceeding.` | routers/files.py (2), routers/retrieval.py (2), storage/provider.py (1) | Files and retrieval; see the companion catalogue |
| `ERROR_MESSAGES` | `DB_NOT_SQLITE` | `backend/open_webui/constants.py:97` | text | `This feature is only available with SQLite databases.` | routers/utils.py (1) | Section 10.7 |
| `ERROR_MESSAGES` | `INVALID_URL` | `backend/open_webui/constants.py:99` | text | `The URL you provided is invalid. Please double-check and try again.` | retrieval/web/utils.py (8), routers/channels.py (1), routers/images.py (1) | Web fetching URL check; also reaches section 10.18 through webhook saves |
| `ERROR_MESSAGES` | `WEB_SEARCH_ERROR` | `backend/open_webui/constants.py:101` | text | `Something went wrong while searching the web.` | routers/retrieval.py (2) | Web search; see `web-search-and-web-loading.md` |
| `ERROR_MESSAGES` | `OLLAMA_API_DISABLED` | `backend/open_webui/constants.py:103` | text | `The Ollama API is disabled. Please enable it to use this feature.` | routers/ollama.py (14) | Ollama connections; see `model-connections-openai-ollama-and-direct.md` |
| `ERROR_MESSAGES` | `FILE_TOO_LARGE` | `backend/open_webui/constants.py:105` | function (size) | `Oops! The file you're trying to upload is too large. Please upload a file that is less than {size}.` | retrieval/utils.py (1), routers/files.py (2), routers/retrieval.py (3) | Uploads; see `files-uploads-and-storage.md` |
| `ERROR_MESSAGES` | `DUPLICATE_CONTENT` | `backend/open_webui/constants.py:109` | text | `Duplicate content detected. Please provide unique content to proceed.` | routers/retrieval.py (1) | Retrieval; see `rag-retrieval-embeddings-and-vector-stores.md` |
| `ERROR_MESSAGES` | `FILE_NOT_PROCESSED` | `backend/open_webui/constants.py:110` | text | `Extracted content is not available for this file. Please ensure that the file is processed before proceeding.` | routers/knowledge.py (1) | Knowledge bases; see `knowledge-bases.md` |
| `ERROR_MESSAGES` | `INVALID_PASSWORD` | `backend/open_webui/constants.py:114` | function (err) | `{err}`, or when empty `The password does not meet the required validation criteria.` | utils/auth.py (1) | Shows the operator's `PASSWORD_VALIDATION_HINT` when set, otherwise `The password does not meet the required validation criteria.` (section 10.14) |
| `ERROR_MESSAGES` | `AUTOMATION_LIMIT_EXCEEDED` | `backend/open_webui/constants.py:116` | function (size) | `Automation limit reached ({size})` | routers/automations.py (1) | Automations; see `automations-calendar-and-timers.md` |
| `ERROR_MESSAGES` | `AUTOMATION_TOO_FREQUENT` | `backend/open_webui/constants.py:117` | function (interval) | `Schedule too frequent. Minimum interval is {interval} seconds.` | routers/automations.py (1) | Automations; see `automations-calendar-and-timers.md` |
| `ERROR_MESSAGES` | `AUTOMATION_INVALID_RRULE` | `backend/open_webui/constants.py:118` | function (err) | `Invalid RRULE: {err}` | models/calendar.py (1), utils/recurrence.py (1) | Automations and calendar; see `automations-calendar-and-timers.md` |
| `ERROR_MESSAGES` | `AUTOMATION_NO_FUTURE_RUNS` | `backend/open_webui/constants.py:119` | text | `RRULE has no future occurrences` | utils/recurrence.py (1) | Automations; see `automations-calendar-and-timers.md` |
| `ERROR_MESSAGES` | `AUTOMATION_COUNT_REQUIRES_DTSTART` | `backend/open_webui/constants.py:120` | text | `RRULE with COUNT requires an explicit DTSTART line to anchor the occurrence window` | utils/recurrence.py (1) | Automations; see `automations-calendar-and-timers.md` |
| `ERROR_MESSAGES` | `CALENDAR_RRULE_TOO_FREQUENT` | `backend/open_webui/constants.py:123` | text | `Recurring events cannot repeat more often than daily` | models/calendar.py (1) | Calendar; see `automations-calendar-and-timers.md` |
| `ERROR_MESSAGES` | `FEATURE_DISABLED` | `backend/open_webui/constants.py:125` | function (name) | `{name} is disabled` | routers/channels.py (1), routers/tasks.py (3), routers/utils.py (1) | Sections 10.7, 10.12 (for example `Code execution is disabled`) |
| `ERROR_MESSAGES` | `INPUT_TOO_LONG` | `backend/open_webui/constants.py:126` | function (size) | `Input prompt exceeds maximum length of {size}` | routers/tasks.py (1) | Section 10.12 |
| `ERROR_MESSAGES` | `SERVER_CONNECTION_ERROR` | `backend/open_webui/constants.py:130` | text | `Open WebUI: Server Connection Error` | main.py (1), routers/ollama.py (3), routers/openai.py (7) | Licence-protected text (section 4.5). Section 10.18 |
| `ERROR_MESSAGES` | `REQUIRED_FIELD_EMPTY` | `backend/open_webui/constants.py:131` | function (name) | `Required field {name} is empty` | routers/auths.py (2) | Section 10.2 (LDAP settings) |
| `ERROR_MESSAGES` | `OAUTH_NOT_CONFIGURED` | `backend/open_webui/constants.py:132` | function (name) | `Provider '{name}' is not configured` | routers/auths.py (2) | Section 10.2 (token exchange) |
| `TASKS` | `DEFAULT` | `backend/open_webui/constants.py:139` | function (task) | `{task}`, or `generation` when empty | not used | Not used. `TASKS` values are internal task names, not messages |
| `TASKS` | `TITLE_GENERATION` | `backend/open_webui/constants.py:140` | text | `title_generation` | main.py (4), routers/tasks.py (1), utils/middleware.py (2) | Internal task name sent in request metadata (section 4.7) |
| `TASKS` | `FOLLOW_UP_GENERATION` | `backend/open_webui/constants.py:141` | text | `follow_up_generation` | routers/tasks.py (1), utils/middleware.py (2) | Internal task name |
| `TASKS` | `TAGS_GENERATION` | `backend/open_webui/constants.py:142` | text | `tags_generation` | main.py (1), routers/tasks.py (1), utils/middleware.py (2) | Internal task name |
| `TASKS` | `EMOJI_GENERATION` | `backend/open_webui/constants.py:143` | text | `emoji_generation` | routers/tasks.py (1) | Internal task name |
| `TASKS` | `QUERY_GENERATION` | `backend/open_webui/constants.py:144` | text | `query_generation` | routers/tasks.py (1) | Internal task name |
| `TASKS` | `IMAGE_PROMPT_GENERATION` | `backend/open_webui/constants.py:145` | text | `image_prompt_generation` | routers/tasks.py (1) | Internal task name |
| `TASKS` | `AUTOCOMPLETE_GENERATION` | `backend/open_webui/constants.py:146` | text | `autocomplete_generation` | routers/tasks.py (1) | Internal task name |
| `TASKS` | `FUNCTION_CALLING` | `backend/open_webui/constants.py:147` | text | `function_calling` | utils/middleware.py (1) | Internal task name |
| `TASKS` | `MOA_RESPONSE_GENERATION` | `backend/open_webui/constants.py:148` | text | `moa_response_generation` | routers/tasks.py (1) | Internal task name |

### 4.7 Other Terms

| Term | Meaning in this catalogue | Evidence |
|---|---|---|
| Toast | The small pop-up message the web page shows; error toasts usually print the server's `detail` | `src/routes/auth/+page.svelte:74-75` |
| Pending user | An account with role `pending`; signed in but refused by `get_verified_user` with HTTP 401 | `backend/open_webui/utils/auth.py:567-576` |
| API key | A personal key used by programs instead of a sign-in token; only when the admin enabled API keys and the user has the permission | `backend/open_webui/utils/auth.py:509-550` |
| Trusted header | Sign-in delegated to a reverse proxy that passes the user's email in a header (`WEBUI_AUTH_TRUSTED_EMAIL_HEADER`) | `backend/open_webui/routers/auths.py:732-735`; `backend/open_webui/env.py:802` |
| LDAP | Directory sign-in with a username and password (`/api/v1/auths/ldap`) | `backend/open_webui/routers/auths.py:476-709` |
| SCIM | Automatic user and group provisioning by an identity provider, with its own token | `backend/open_webui/routers/scim.py:232-290` |
| Token exchange | Swapping an identity-provider token for a MedIT GPT token (`/api/v1/auths/oauth/{provider}/token/exchange`) | `backend/open_webui/routers/auths.py:1624-1771` |
| Redis | Optional shared store; needed for sign-out revocation and multi-worker deployments | `CLAUDE.md`; `backend/open_webui/utils/auth.py:276-287` |
| Readiness | `/ready`: HTTP 200 only when start-up has finished and the database (and Redis, when configured) answer | `backend/open_webui/main.py:2968-3006` |
| `TASKS` names | Internal labels such as `title_generation` that the server attaches to background generation requests (`metadata.task`); filters and pipelines can read them; they are not messages | `backend/open_webui/constants.py:135-148`; `backend/open_webui/routers/tasks.py:188-191` |

## 5. Workflows (Step by Step)

### 5.1 Look Up a Message by Its Text

1. **Get the exact wording.** Ask for a screenshot or a copy of the toast, and note where it appeared: the sign-in page, a toast on an admin or settings screen, inside a chat reply, the output of a script, or the server's start-up output (section 2.1).
2. **Search this document for the exact text.** Every message is quoted in backticks exactly as the code spells it; variable parts are written `{name}` (for example `User with email {email} already exists`).
3. **No match? Search for a long fragment** without the variable parts: `already exists`, `is disabled`, `not found`, `Failed to`, `Required field`.
4. **The text starts with `[ERROR:`.** It came from the `DEFAULT` formatter (section 4.2): the words after `ERROR:` name the operation that failed. Search for the whole bracketed text.
5. **The text starts with a three-digit number and a colon** (`400: …`). It is the `{status}: {detail}` form (section 4.4): look up the part after the colon.
6. **The text is `Something went wrong :/` or `We could not find what you're looking for :/`.** These are shared by many endpoints (section 4.6 lists every file). Ask what the user was doing at that moment, then use the section for that router.
7. **Still no match.** Search the companion catalogues and subsystem documents named in section 1, then section 14 of this document (texts that no code in the repository raises).
8. **Only a status code is known** (a script or monitor reports "401" or "503"): use section 3.2, then the rows with that status in section 10.

### 5.2 Check the Context Before Advising

| Ask or check | Why |
|---|---|
| The account's role (an admin can see it under **Admin Panel → Users**) | A pending account gets the permission text on almost every action (section 3.1) |
| Whether it is one person or many, and since when | Many people at once points to a configuration change, a restart, or an upstream outage (section 11) |
| The time of the error, to the minute | The platform maintainer needs it to find the matching server log lines |
| The page or action, and for chats the chat link | Shared texts such as `Something went wrong :/` are only meaningful with the action |

### 5.3 Find Every Place a Shared Text Is Raised (Maintainers)

Section 4.6 gives the counts. To list the call sites read-only, run from the repository root, for example `grep -rn "ERROR_MESSAGES.ACCESS_PROHIBITED" backend/open_webui`. For a literal text, `grep -rnF "<text>" backend/open_webui`.

### 5.4 Read a Start-Up Failure (Platform Maintainer)

1. Read the **last lines** of the server's start-up output. A fatal configuration error ends start-up with an exit message or a Python `ValueError` naming the setting (sections 10.20 to 10.22).
2. `Error running migrations: {e}` followed by a traceback means a database migration failed; start-up stops (section 10.22).
3. Warnings (for example the CORS warning) do not stop start-up.
4. While the server is starting, `/ready` answers HTTP 503 `Startup not complete`; afterwards `Database not ready` or `Redis not ready` point at the dependency (section 10.18). *Precision 2026-10-11: under uvicorn the port opens only after start-up finishes (`.venv` uvicorn 0.51.0, `server.py:104` before `:142`), so a probe normally gets no connection or waits during start-up rather than seeing `Startup not complete`; see `backend-architecture-and-request-lifecycle.md` section 5.5.*

## 6. Data Model

None in this catalogue. Messages are code, not data: no table stores them. Two places can keep a copy of a message:

| Where | What is kept | Evidence |
|---|---|---|
| The chat history | When a chat request fails after the reply was started, the error text is saved into the reply's `error` field, so it is still shown when the chat is reopened | `backend/open_webui/main.py:1686-1712` |
| The audit log (optional) | When `AUDIT_LOG_LEVEL` is not `NONE`, request details are written to `DATA_DIR/audit.log`, which holds personal data (user names, emails, IP addresses, request bodies); the middleware is placed so that it can capture response bodies | `backend/open_webui/main.py:803-814`; `CLAUDE.md` |

The tables these messages refer to (`user`, `auth`, `group`, `config` and others) are described in `database-schema-identity-chats-and-config.md` (TO BE CONFIRMED whether that document exists yet; section 14).

## 7. Settings and Configuration

No setting changes the wording of a message. Settings decide **whether** a message can appear. The live values are data in the database `config` table or the environment and are **TO BE CONFIRMED** for production.

| Setting (where it lives) | Code default | Messages it controls | Evidence |
|---|---|---|---|
| `ENABLE_PASSWORD_AUTH` (environment) | on | Off: password and LDAP sign-in answer `The requested action has been restricted as a security measure.` | `backend/open_webui/config.py:1670`; `backend/open_webui/routers/auths.py:486-490`, `:724-728` |
| `ui.enable_signup`, `ui.enable_login_form` (persistent, seeded from `ENABLE_SIGNUP`, `ENABLE_LOGIN_FORM`) | on, on | Off: sign-up answers the permission text with HTTP 403 | `backend/open_webui/config.py:1664`, `:1666`, `:3083-3084`; `backend/open_webui/routers/auths.py:908-917` |
| `ldap.enable` (persistent, seeded from `ENABLE_LDAP`) | off | Off: `LDAP authentication is not enabled` | `backend/open_webui/config.py:2788`, `:3211`; `backend/open_webui/routers/auths.py:483-484` |
| `WEBUI_AUTH_TRUSTED_EMAIL_HEADER` (environment) | unset | Set: `Your provider has not provided a trusted header. Please contact your administrator for assistance.`, `User mismatch. Please sign in again.`, and password changes refused | `backend/open_webui/env.py:802`; `backend/open_webui/routers/auths.py:394-395`, `:732-735`; `backend/open_webui/utils/auth.py:461-468` |
| `ENABLE_PASSWORD_VALIDATION`, `PASSWORD_VALIDATION_HINT` (environment) | off, empty | On: new passwords that fail the pattern get the hint text, or `The password does not meet the required validation criteria.` | `backend/open_webui/env.py:814`, `:829`; `backend/open_webui/utils/auth.py:197-199` |
| `PASSWORD_HASH_ALGORITHM` (environment) | `bcrypt` | `bcrypt`: passwords over 72 bytes get `Uh-oh! The password you entered is too long. Please make sure your password is less than 72 bytes long.` | `backend/open_webui/env.py:815`; `backend/open_webui/utils/auth.py:192-195` |
| `auth.enable_api_keys` (persistent, seeded from `ENABLE_API_KEYS`) and the `features.api_keys` permission | off | Off or no permission: `API key creation is not allowed in the environment.` and `Use of API key is not enabled in the environment.` | `backend/open_webui/config.py:2454`, `:3155`; `backend/open_webui/routers/auths.py:1517-1525`; `backend/open_webui/utils/auth.py:526-537` |
| `auth.api_key.endpoint_restrictions`, `auth.api_key.allowed_endpoints` (persistent) | see `authentication-and-sign-in.md` | On: an API key used outside the allowed paths gets the permission text with HTTP 403 | `backend/open_webui/utils/auth.py:541-550` |
| `ENABLE_OAUTH_TOKEN_EXCHANGE`, `OAUTH_TOKEN_EXCHANGE_RATE_LIMIT` (environment) | off | Off: `Token exchange is disabled`; the optional limit gives `API rate limit exceeded` | `backend/open_webui/env.py:883-890`; `backend/open_webui/routers/auths.py:94-101`, `:1636-1648` |
| `ENABLE_SCIM`, `SCIM_TOKEN`, `SCIM_AUTH_PROVIDER` (environment) | off | SCIM texts in section 10.5 | `backend/open_webui/env.py:907-917` |
| `ENABLE_OAUTH_BACKCHANNEL_LOGOUT` (environment) | off | Off: the back-channel logout address answers a bare `Not Found` | `backend/open_webui/env.py:901`; `backend/open_webui/main.py:2858-2865` |
| `ENABLE_PUBLIC_ACTIVE_USERS_COUNT` (environment) | on | Off: non-admins get `Access denied. Only administrators can view usage statistics.` | `backend/open_webui/env.py:367`; `backend/open_webui/main.py:2629-2632` |
| `ENABLE_ADMIN_EXPORT` (environment) | on | Off: the database download answers the permission text | `backend/open_webui/config.py:2082`; `backend/open_webui/routers/utils.py:77-78` |
| `code_execution.enable` (persistent) | on | Off: `Code execution is disabled` | `backend/open_webui/config.py:409`, `:2836`; `backend/open_webui/routers/utils.py:43-47` |
| `task.*.enable`, `task.autocomplete.input_max_length` (persistent) | see `chat-completion-pipeline-and-generation-tasks.md` | Generation-disabled texts and `Input prompt exceeds maximum length of {size}` (section 10.12) | `backend/open_webui/config.py:3145-3150`; `backend/open_webui/routers/tasks.py:142-146`, `:491-496` |
| `ui.enable_user_webhooks` (persistent, seeded from `ENABLE_USER_WEBHOOKS`) and the `features.webhooks` permission | off | Off: every personal-notification call answers `We could not find what you're looking for :/` | `backend/open_webui/config.py:2100`, `:3125`; `backend/open_webui/routers/notifications.py:34-41` |
| `ENABLE_PLUGINS` (environment) | on | Off: loading a tool or function raises `Plugins are disabled by ENABLE_PLUGINS=false` | `backend/open_webui/env.py:1186`; `backend/open_webui/utils/plugin.py:207-208`, `:260-261` |
| `WEBUI_SECRET_KEY`, `WEBUI_AUTH` (environment) | secret unset, authentication on | Secret unset with authentication on: the server refuses to start (section 10.21) | `backend/open_webui/env.py:751`, `:762-788` |

## 8. Cron Jobs and Background Processes

None in this catalogue. The messages here are produced when a request arrives or when the server starts. Background loops (`backend/open_webui/socket/main.py`, `backend/open_webui/utils/automations.py`) write log lines rather than user messages; see `background-processes-and-scheduling.md` and section 10.19 for the websocket server's log lines.

## 9. Notifications and Emails

None in this catalogue. The application sends no email (`CLAUDE.md`; `knowledgebase/tools/ground-truth.md`). The messages here are HTTP responses and log lines, not notifications. Personal notification targets have their own messages, catalogued in `notifications-webhooks-events-and-banners.md` section 10 (summarized in section 10.13 here).

## 10. Error, Warning and Notice Messages (Verbatim)

### 10.1 How to Read This Catalogue

- **One row per distinct message per source file.** The Source cell lists every line in that file that raises it (the line of `raise HTTPException(` or equivalent). The same text raised by another file has its own row in that file's section.
- **Severity** gives the kind and the HTTP status: *Error (HTTP 400)* is a refusal shown to the user; *API error* is seen mainly by programs; *Replaced* means a later `except` swaps the text for another before it leaves the server (the replacement is named); *Log* is a server log line, never shown to users; *Start-up failure* stops the server.
- **Placeholders.** `{name}` stands for a value filled in at run time, using the source's variable name.
- **Rows already explained elsewhere** keep a short trigger and say `See <document>.md section 10` in Support check.
- **Tier-1 actions are read-only** (section 3.3). "Escalate" means: send the platform maintainer the exact text, the time, the user's email (in the ticket, not in this knowledgebase) and what they were doing.

### 10.2 `backend/open_webui/routers/auths.py` (Sign-In, Sign-Up, Profile, API Keys, LDAP, Token Exchange)

Every message in this file is also explained in `authentication-and-sign-in.md` section 10.1; token-exchange and single sign-on aspects are also in `sso-oauth-oidc-and-scim.md` section 10.1.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `The email or password provided is incorrect. Please check for typos and try logging in again.` | Error (HTTP 400) | `backend/open_webui/routers/auths.py:833`; also `:344`, `:378`, `:423` (no session; not expected because the session check runs first); `:704` (LDAP, replaced by `LDAP authentication failed.`) | Email-and-password sign-in with an unknown email or a wrong password, or for an account with no usable local password (single sign-on, LDAP or SCIM accounts) | Check the email and password; SSO users use the SSO button | See `authentication-and-sign-in.md` section 10 |
| `API rate limit exceeded` | Error (HTTP 429) | `backend/open_webui/routers/auths.py:819`, `:1645` | More than 15 sign-in attempts for one email within about three to four minutes (`:91`, section 10.16); or the optional token-exchange limit | Wait a few minutes, then retry once | See `authentication-and-sign-in.md` section 10 |
| `The requested action has been restricted as a security measure.` | Error (HTTP 403 at `:487`, `:725`; HTTP 400 at `:395`, `:1196`) | `backend/open_webui/routers/auths.py:395`, `:487`, `:725`, `:1196` | Password or LDAP sign-in while `ENABLE_PASSWORD_AUTH` is off; **Change Password** in trusted-header mode; the admin-contact lookup while admin details are hidden | Use the sign-in method the site offers | See `authentication-and-sign-in.md` section 10 |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 403) | `backend/open_webui/routers/auths.py:911`, `:914`, `:917`, `:1676`, `:1727` | Sign-up while new sign-ups or the login form are off (or no-login mode with existing users); token exchange for a client or account that is not allowed | Ask an administrator for an account | See `authentication-and-sign-in.md` section 10 |
| `Your session has expired or the token is invalid. Please sign in again.` | Error (HTTP 401) | `backend/open_webui/routers/auths.py:274` | The session check found the token's expiry time already passed | Sign in again | See `authentication-and-sign-in.md` section 10 |
| `{e}` (the password rule text: `Uh-oh! The password you entered is too long. Please make sure your password is less than 72 bytes long.`, the operator's `PASSWORD_VALIDATION_HINT`, or `The password does not meet the required validation criteria.`) | Error (HTTP 400) | `backend/open_webui/routers/auths.py:407`, `:929`, `:1119` | A new password failed `validate_password` (section 10.14) during **Change Password**, sign-up or **Add User** | Choose a shorter password, or one that meets the stated rule | See `authentication-and-sign-in.md` section 10 |
| `The password provided is incorrect. Please check for typos and try again.` | Error (HTTP 400) | `backend/open_webui/routers/auths.py:421` | **Change Password** with a wrong current password (including SSO and LDAP accounts, which have no known local password) | Re-enter the current password; SSO and LDAP users cannot change it here | See `authentication-and-sign-in.md` section 10 |
| `Something went wrong :/` | Error (HTTP 400) | `backend/open_webui/routers/auths.py:342` | Saving the profile found no account to update | Reload and retry | See `authentication-and-sign-in.md` section 10 |
| `LDAP authentication is not enabled` | Error (HTTP 400) | `backend/open_webui/routers/auths.py:484` | LDAP sign-in while LDAP is off | Use the other sign-in method | See `authentication-and-sign-in.md` section 10 |
| `Failed to configure TLS for LDAP connection.` | Error (HTTP 400) | `backend/open_webui/routers/auths.py:524` | The LDAP TLS settings cannot be used | None | Escalate; see `authentication-and-sign-in.md` section 10 |
| `LDAP authentication failed.` | Error (HTTP 400) | `backend/open_webui/routers/auths.py:709` | Any LDAP failure after the connection starts; the real reason is logged as `LDAP authentication error: {e}` (`:708`) | Check username and password; retry once | See `authentication-and-sign-in.md` section 10 |
| `Application account bind failed` | Replaced by `LDAP authentication failed.` | `backend/open_webui/routers/auths.py:542` | The directory refused the application account | None | Appears only in the log line; escalate |
| `User not found in the LDAP server` | Replaced by `LDAP authentication failed.` | `backend/open_webui/routers/auths.py:565` | No directory entry matched the username | Check the username | See `authentication-and-sign-in.md` section 10 |
| `User does not have a valid email address.` | Replaced by `LDAP authentication failed.` | `backend/open_webui/routers/auths.py:579` | The directory entry has no email value | None | Escalate (directory data) |
| `Authentication failed.` | Replaced by `LDAP authentication failed.` | `backend/open_webui/routers/auths.py:645` | The directory refused the person's password | Re-enter the password | See `authentication-and-sign-in.md` section 10 |
| `Oops! Something went wrong while creating your account. Please try again later. If the issue persists, contact support for assistance.` | Error (HTTP 500); replaced at `:661` | `backend/open_webui/routers/auths.py:872`, `:1158`; `:661` (LDAP) | The database did not return the new account | Retry later | Escalate; see `authentication-and-sign-in.md` section 10 |
| `Internal error occurred during LDAP user creation.` | Replaced by `LDAP authentication failed.` | `backend/open_webui/routers/auths.py:688` | Creating the account for a new LDAP user failed | None | Escalate |
| `User record mismatch.` | Replaced by `LDAP authentication failed.` | `backend/open_webui/routers/auths.py:706` | The typed username is not among the entry's username values | Check the username | See `authentication-and-sign-in.md` section 10 |
| `Your provider has not provided a trusted header. Please contact your administrator for assistance.` | Error (HTTP 400) | `backend/open_webui/routers/auths.py:735` | Trusted-header mode, but the request arrived without the email header | None | Escalate (proxy configuration); see `authentication-and-sign-in.md` section 10 |
| `You can't turn off authentication because there are existing users. If you want to disable WEBUI_AUTH, make sure your web interface doesn't have any existing users and is a fresh installation.` | Error (HTTP 400) | `backend/open_webui/routers/auths.py:801` | No-login mode (`WEBUI_AUTH` off) on an installation that has accounts | None | Escalate (server configuration) |
| `The email format you entered is invalid. Please double-check and make sure you're using a valid email address (e.g., yourname@example.com).` | Error (HTTP 400) | `backend/open_webui/routers/auths.py:920`, `:1110` | Sign-up or **Add User** with an address the server's format check rejects | Correct the address | See `authentication-and-sign-in.md` section 10 |
| `Uh-oh! This email is already registered. Sign in with your existing account or choose another email to start anew.` | Error (HTTP 400) | `backend/open_webui/routers/auths.py:923`, `:1113` | Sign-up or **Add User** with an email that already has an account | Sign in instead, or reset access through an admin | See `authentication-and-sign-in.md` section 10 |
| `An internal error occurred during signup.` | Error (HTTP 500) | `backend/open_webui/routers/auths.py:952` | Unexpected error while creating the account | Retry later | Escalate |
| `Failed to sign out from the OpenID provider.` | Error (HTTP 500) | `backend/open_webui/routers/auths.py:1043` | SSO sign-out could not read the provider's settings; the inner reason `Failed to fetch OpenID configuration` (`:1039`) is only logged as `OpenID signout error: {e}` (`:1042`) | Close the browser to end the session | See `sso-oauth-oidc-and-scim.md` section 10 |
| `No OAuth session found for this provider` | Error (HTTP 404) | `backend/open_webui/routers/auths.py:1081` | Disconnecting a tool-server sign-in that no longer exists | Reload | See `authentication-and-sign-in.md` section 10 |
| `An internal error occurred while adding the user.` | Error (HTTP 500) | `backend/open_webui/routers/auths.py:1163` | Unexpected error during **Add User** | Retry | Escalate |
| `I18N must be a dictionary` | Error (HTTP 422, shown as a list) | `backend/open_webui/routers/auths.py:1245-1246` | Admin settings saved with the translation-override block empty | None | See `admin-settings-panels.md` section 10 |
| `Invalid language: {locale}` | Error (HTTP 422) | `backend/open_webui/routers/auths.py:1254-1255` | A translation override with a blank or reserved language name | Correct the override | See `authentication-and-sign-in.md` section 10 |
| `Invalid translation key: {key}` | Error (HTTP 422) | `backend/open_webui/routers/auths.py:1258-1259` | A translation override with a blank or reserved key | Correct the override | See `admin-settings-panels.md` section 10 |
| `Interpolation placeholders do not match: {locale}: {key}` | Error (HTTP 422) | `backend/open_webui/routers/auths.py:1261-1262` | A translation override drops or renames a `{{placeholder}}` | Keep the placeholders as in the original | See `admin-settings-panels.md` section 10 |
| `Required field {name} is empty` (here `{name}` is `label`, `host`, `attribute_for_mail`, `attribute_for_username`, `search_base` or `attribute_for_groups`) | Error (HTTP 400) | `backend/open_webui/routers/auths.py:1335`, `:1340`; `backend/open_webui/constants.py:131` | Saving LDAP settings with a required field empty, or the group attribute empty while group management is on | Fill in the field | See `authentication-and-sign-in.md` section 10 |
| `API key creation is not allowed in the environment.` | Error (HTTP 403) | `backend/open_webui/routers/auths.py:1522` | Creating, reading or deleting an API key while API keys are off or without the `features.api_keys` permission | Ask an admin whether API keys are available | See `authentication-and-sign-in.md` section 10 |
| `Oops! Something went wrong while creating your API key. Please try again later. If the issue persists, contact support for assistance.` | Error (HTTP 500) | `backend/open_webui/routers/auths.py:1550` | Saving the new key reported failure | Retry | Escalate |
| `Oops! It looks like there's a hiccup. The API key is missing. Please make sure to provide a valid API key to access this feature.` | Error (HTTP 404) | `backend/open_webui/routers/auths.py:1581` | Reading the API key when none exists (the Account tab treats this as "no key yet") | Create a key if allowed | See `authentication-and-sign-in.md` section 10 |
| `Token exchange is disabled` | API error (HTTP 403) | `backend/open_webui/routers/auths.py:1637` | A program called token exchange while `ENABLE_OAUTH_TOKEN_EXCHANGE` is off | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `Provider '{name}' is not configured` | API error (HTTP 404) | `backend/open_webui/routers/auths.py:1654`, `:1662`; `backend/open_webui/constants.py:132` | Token exchange named a provider that is not set up (`{name}` is the lower-cased provider in the address) | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `Unable to determine which client the token was issued to` | API error (HTTP 400) | `backend/open_webui/routers/auths.py:1670` | Token exchange with a trusted-client list when the token's client cannot be determined | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `Invalid token or unable to fetch user info` | Replaced by the next message | `backend/open_webui/routers/auths.py:1687` | The provider returned no user details | None | See `authentication-and-sign-in.md` section 10 |
| `Invalid token or unable to validate with provider` | API error (HTTP 400) | `backend/open_webui/routers/auths.py:1693` | The provider would not confirm the token | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `Token missing required 'sub' claim` | API error (HTTP 400) | `backend/open_webui/routers/auths.py:1706` | The provider's answer has no subject identifier | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `Token missing required email claim` | API error (HTTP 400) | `backend/open_webui/routers/auths.py:1715` | The provider's answer has no email | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `User not found. Please sign in via the web interface first.` | API error (HTTP 403) | `backend/open_webui/routers/auths.py:1749` | Token exchange for a person who has never signed in on the website | Sign in on the website once | See `sso-oauth-oidc-and-scim.md` section 10 |

### 10.3 `backend/open_webui/routers/users.py` (User Administration and Personal Account Data)

Also explained in `users-groups-roles-and-permissions.md` section 10.1, except the variable texts listed under `{exc}`.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `We could not find what you're looking for :/` (constant `USER_NOT_FOUND`) | Error (HTTP 400; HTTP 404 at `:1113`) | `backend/open_webui/routers/users.py:559`, `:611`, `:667`, `:694`, `:808`, `:829`, `:843`, `:890`, `:1031`, `:1113` | The user id no longer exists (deleted, or a stale page), or the signed-in account could not be updated | Reload the page | See `users-groups-roles-and-permissions.md` section 10 |
| `The requested action has been restricted as a security measure.` | Error (HTTP 403) | `backend/open_webui/routers/users.py:576`, `:597`, `:930`, `:937`, `:1050`, `:1081` | Reading or saving a personal status while user status is switched off (`:576`, `:597`); another admin edits the primary admin, or the primary admin removes their own admin role (`:930`, `:937`); deleting the primary admin or one's own account (`:1050`, `:1081`) | None; the first admin account is protected | See `users-groups-roles-and-permissions.md` section 10 |
| `{exc}`: one of `User variables must be an object.`, `User variables are too large.`, `User variables must be JSON serializable.`, `Invalid user variable key: {key}`, `User variable must be a string: {key}`, `User variable is too long: {key}` | Error (HTTP 400) | `backend/open_webui/routers/users.py:657-663`; texts at `backend/open_webui/utils/chat_variables.py:185`, `:189`, `:191`, `:196`, `:198`, `:201` | Saving personal variables in **Settings → Account** (`src/lib/components/chat/Settings/Account.svelte:162-165`) with a key that does not start with a lowercase letter or uses characters other than lowercase letters, digits and underscores, a value over 20,000 characters, or all variables together over 100,000 characters of JSON (`backend/open_webui/utils/chat_variables.py:8`, `:11-12`) | Rename the key (for example `team_name`), or shorten the value | None; the toast names the key |
| `start_date must be before end_date` | Error (HTTP 400) | `backend/open_webui/routers/users.py:723` | A usage request with its start after its end | Choose a valid range | See `users-groups-roles-and-permissions.md` section 10 |
| `Could not verify primary admin status.` | Error (HTTP 500) | `backend/open_webui/routers/users.py:946`, `:1058` | The primary-admin lookup failed while saving or deleting a user (log `Error checking primary admin status: {e}`) | Retry | Escalate with the time |
| `Uh-oh! This email is already registered. Sign in with your existing account or choose another email to start anew.` | Error (HTTP 400) | `backend/open_webui/routers/users.py:957` | An admin changes a user's email to one another account uses | Choose another email | See `users-groups-roles-and-permissions.md` section 10 |
| `{e}` (password rule text, section 10.14) | Error (HTTP 400) | `backend/open_webui/routers/users.py:966` | An admin sets a new password that breaks a rule | Choose another password | See `users-groups-roles-and-permissions.md` section 10 |
| `Something went wrong :/` | Error (HTTP 400) | `backend/open_webui/routers/users.py:1026` | The user record could not be re-read after an admin edit | Reload and check the change | See `users-groups-roles-and-permissions.md` section 10 |
| `Oops! Something went wrong. We encountered an issue while trying to delete the user. Please give it another shot.` | Error (HTTP 500) | `backend/open_webui/routers/users.py:1075` | Deleting the user's chats or rows failed | Retry once | Escalate if it repeats |

### 10.4 `backend/open_webui/routers/groups.py` (Groups)

Also explained in `users-groups-roles-and-permissions.md` section 10.1. Every `[ERROR: …]` text comes from the `DEFAULT` formatter (section 4.2); the same text is used whether the save simply returned nothing or raised an error, and in the second case the reason is logged (for example `Error creating a new group: {e}`, `backend/open_webui/routers/groups.py:89`).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `[ERROR: Error creating group]` | Error (HTTP 400) | `backend/open_webui/routers/groups.py:82`, `:90` | The new group could not be stored | Retry; check the name | See `users-groups-roles-and-permissions.md` section 10 |
| `We could not find what you're looking for :/` | Error (HTTP 401 at `:110`, `:125`, `:151`; HTTP 404 at `:347`) | `backend/open_webui/routers/groups.py:110`, `:125`, `:151`, `:347` | The group id no longer exists (opening, reading details, exporting, or previewing access) | Reload the group list | Note the unusual 401 (section 3.1); see `users-groups-roles-and-permissions.md` section 10 |
| `[ERROR: Error getting group members]` | Error (HTTP 400) | `backend/open_webui/routers/groups.py:169` | Listing a group's members through the API failed | None | Escalate |
| `[ERROR: Error updating group]` | Error (HTTP 400) | `backend/open_webui/routers/groups.py:203`, `:211` | Saving the group failed | Retry | See `users-groups-roles-and-permissions.md` section 10 |
| `[ERROR: Error adding users to group]` | Error (HTTP 400) | `backend/open_webui/routers/groups.py:248`, `:256` | Adding members failed, for example because the group no longer exists | Reload and retry | See `users-groups-roles-and-permissions.md` section 10 |
| `[ERROR: Error removing users from group]` | Error (HTTP 400) | `backend/open_webui/routers/groups.py:285`, `:293` | Removing members failed | Reload and retry | See `users-groups-roles-and-permissions.md` section 10 |
| `[ERROR: Error deleting group]` | Error (HTTP 400) | `backend/open_webui/routers/groups.py:319`, `:327` | Deleting the group failed | Reload and retry | See `users-groups-roles-and-permissions.md` section 10 |

### 10.5 `backend/open_webui/routers/scim.py` (SCIM Provisioning)

These texts are read by the identity provider's provisioning service (they appear in its provisioning logs), not by people using MedIT GPT. Most are plain HTTP errors (`{"detail": …}`); the rows marked *SCIM error* use the SCIM error format, which also carries `status` and a `scimType` code (`backend/open_webui/routers/scim.py:48-65`). All are also explained in `sso-oauth-oidc-and-scim.md` section 10.1. Whether MedIT GPT uses SCIM is **TO BE CONFIRMED** (it needs `ENABLE_SCIM`).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Authorization header required` | API error (HTTP 401) | `backend/open_webui/routers/scim.py:238` | The SCIM client sent no credentials | None (identity-provider setup) | See `sso-oauth-oidc-and-scim.md` section 10 |
| `Invalid authorization format. Expected: Bearer <token>` | API error (HTTP 401) | `backend/open_webui/routers/scim.py:247` | The credentials were not `Bearer` plus a token | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `Invalid authentication scheme` | API error (HTTP 401) | `backend/open_webui/routers/scim.py:254` | A scheme other than `Bearer` | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `SCIM is not enabled` | API error (HTTP 403) | `backend/open_webui/routers/scim.py:264` | SCIM is switched off for a mounted router (not expected: the router is mounted only when SCIM is on) | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `Invalid SCIM token` | API error (HTTP 401) | `backend/open_webui/routers/scim.py:273` | The token does not match the configured SCIM token, or none is configured | None | Escalate to the maintainer; see `sso-oauth-oidc-and-scim.md` section 10 |
| `Authentication failed` | API error (HTTP 401) | `backend/open_webui/routers/scim.py:287` | An unexpected error while checking the credentials | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `SCIM_AUTH_PROVIDER environment variable is required when SCIM is enabled` | API error (HTTP 500) | `backend/open_webui/routers/scim.py:312` | An external-ID lookup or write while `SCIM_AUTH_PROVIDER` is empty | None | Escalate (server configuration) |
| `User {user_id} not found` | API error (HTTP 404; *SCIM error* at `:568`) | `backend/open_webui/routers/scim.py:568`, `:670`, `:750`, `:852` | The id is unknown, or belongs to an account SCIM cannot see | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `User with externalId {user_data.externalId} already exists` | API error (HTTP 409) | `backend/open_webui/routers/scim.py:585` | Creating an account whose external id is already taken | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `User with email {email} already exists` | API error (HTTP 409) | `backend/open_webui/routers/scim.py:601` | Creating an account whose email already has an account (for example one created by password sign-up) | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `Failed to create user` | API error (HTTP 500) | `backend/open_webui/routers/scim.py:632` | The account could not be stored | None | Escalate |
| `Failed to stamp SCIM user` | API error (HTTP 500) | `backend/open_webui/routers/scim.py:639` | The account was stored but could not be marked as SCIM-managed | None | Escalate |
| `Failed to update user` | API error (HTTP 500) | `backend/open_webui/routers/scim.py:703`, `:812` | A replace or patch could not be stored | None | Escalate |
| `Unsupported PATCH operation: {operation.op}` | *SCIM error* (HTTP 400) | `backend/open_webui/routers/scim.py:768` | A user patch other than add, replace or remove | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `Remove requires a path` | *SCIM error* (HTTP 400) | `backend/open_webui/routers/scim.py:771` | A remove without a path | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `Removing {path} is not supported` | *SCIM error* (HTTP 400) | `backend/open_webui/routers/scim.py:773` | Removing anything other than the external id | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `A pathless operation requires an attribute object` | *SCIM error* (HTTP 400) | `backend/open_webui/routers/scim.py:777` | A patch with neither a path nor an attribute object | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `active must be a boolean` | *SCIM error* (HTTP 400) | `backend/open_webui/routers/scim.py:785` | `active` sent as something other than true or false | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `{path} must be a string` | *SCIM error* (HTTP 400) | `backend/open_webui/routers/scim.py:791` | A name or email patch whose value is not text | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `externalId must be a string or null` | *SCIM error* (HTTP 400) | `backend/open_webui/routers/scim.py:795` | An external-id patch with another kind of value | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `Unsupported PATCH path: {path}` | *SCIM error* (HTTP 400) | `backend/open_webui/routers/scim.py:801` | A patch to an attribute the code does not handle | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `Failed to delete user` | API error (HTTP 500) | `backend/open_webui/routers/scim.py:859` | The account or its chats could not be deleted | None | Escalate |
| `Group {group_id} not found` | API error (HTTP 404) | `backend/open_webui/routers/scim.py:930`, `:1019`, `:1089`, `:1180` | The group id is unknown | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `No admin user found` | API error (HTTP 500) | `backend/open_webui/routers/scim.py:963` | Creating a group while no admin account exists | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `Failed to create group` | API error (HTTP 500) | `backend/open_webui/routers/scim.py:970` | The group could not be stored | None | Escalate |
| `Failed to update group` | API error (HTTP 500) | `backend/open_webui/routers/scim.py:1046`, `:1138` | A group replace or patch could not be stored | None | Escalate |
| `Failed to delete group` | API error (HTTP 500) | `backend/open_webui/routers/scim.py:1187` | The group could not be deleted | None | Escalate |

### 10.6 `backend/open_webui/routers/configs.py` (Tool Servers, Terminal Servers and OAuth Client Registration)

Every route in this file is admin-only (`get_admin_user`, for example `backend/open_webui/routers/configs.py:552`), so only administrators meet these texts, and not always as written. **Register Client** and **Verify** replace a refusal with the dialog's own `Registration failed`, `Connection failed` or `Server connection failed` toast (`src/lib/components/AddToolServerModal.svelte:143-146`, `:198`, `:229-231`; `src/lib/components/AddTerminalServerModal.svelte:213-253`), so the server's text is then visible only in the browser's developer tools (Network tab). The orchestrator policy, lifecycle and refresh actions show the server's text inside the dialog's own wording, `Failed to load policy: {error}`, `Failed to save policy: {error}` or `Failed to refresh terminals: {error}` (`src/lib/components/AddTerminalServerModal.svelte:327`, `:352`, `:383`). Every row except the `{detail}` pass-through is also explained in `workspace-tools-tool-servers-mcp-and-terminals.md` section 10.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Failed to register OAuth client: {e}` | Error (HTTP 400) | `backend/open_webui/routers/configs.py:206` | **Register Client** for an MCP tool server that signs in with OAuth 2.1 failed. `{e}` is the registration helper's reason, for example the discovery or dynamic-registration texts in section 10.15 | Admin: check the server URL and the OAuth Server URL, then register again | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 and `sso-oauth-oidc-and-scim.md` section 10 |
| `Terminal server URL is required` | Error (HTTP 400) | `backend/open_webui/routers/configs.py:367`, `:437`, `:474`, `:513` | Verify, policy, lifecycle or refresh request for a terminal server with an empty URL | Enter the URL | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Failed to connect to the terminal server` | Error (HTTP 400) | `backend/open_webui/routers/configs.py:401` | **Verify**: neither the orchestrator check (`{url}/api/v1/policies`) nor the plain-terminal check (`{url}/api/config`) answered successfully (`:378-396`) | Check the URL and key | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `{detail}` (the orchestrator's own answer) | Error (the terminal server's own HTTP status) | `backend/open_webui/routers/configs.py:459` (policy), `:496` (lifecycle), `:543` (refresh) | An orchestrator terminal server answered a policy, lifecycle or refresh request with an error; MedIT GPT passes its response text and status through unchanged (`:456-459`) | None | Not explained elsewhere. Escalate to whoever runs the terminal server, with the text, the status and the time |
| `Failed to access policy on terminal server` | Error (HTTP 400) | `backend/open_webui/routers/configs.py:464` | The policy request could not be sent, or its answer could not be read (no answer, network error, unreadable JSON) | Retry | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Failed to access lifecycle on terminal server` | Error (HTTP 400) | `backend/open_webui/routers/configs.py:501` | As above, for the lifecycle request | Retry | As above |
| `Failed to refresh terminals` | Error (HTTP 400) | `backend/open_webui/routers/configs.py:548` | As above, for **Refresh Terminals** | Retry | As above |
| `Failed to parse OAuth 2.1 discovery document from {discovery_url}` | Error (HTTP 400) | `backend/open_webui/routers/configs.py:585` | **Verify** for an MCP tool server set to OAuth 2.1: a discovery address answered HTTP 200 but its content is not a valid OAuth server description (`:557-588`) | Admin: check the OAuth Server URL | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Failed to fetch OAuth 2.1 discovery document from {discovery_urls}` | Error (HTTP 400) | `backend/open_webui/routers/configs.py:590` | As above, but no discovery address answered HTTP 200; `{discovery_urls}` is the whole list of addresses tried, printed as a Python list | Admin: check the server and OAuth Server URLs | As above |
| `Failed to create MCP client` | Error (HTTP 400) | `backend/open_webui/routers/configs.py:634` | **Verify** for an MCP tool server without OAuth: connecting to it or listing its tools failed (`:595-637`) | Admin: check the address and authentication | As above |
| `Failed to connect to the tool server` | Error (HTTP 400) | `backend/open_webui/routers/configs.py:677` | **Verify** for an OpenAPI tool server failed, or any other unexpected error during verification (`:641-680`) | Admin: check the address, path and authentication | As above |

### 10.7 `backend/open_webui/routers/utils.py` (Code Formatting, Code Execution and Database Download)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{e}` (the code formatter's own error, typically a text beginning `Cannot parse` that names the line and column) | Error (HTTP 400) | `backend/open_webui/routers/utils.py:38`; wording from the installed formatter, `.venv/lib/python3.12/site-packages/black/parsing.py:84-88` | An administrator saved a function or a workspace tool, or pressed Ctrl+Shift+F (Cmd+Shift+F on a Mac) in its code editor, and the code is not valid Python. Only administrators format on the server; for others the browser formats (`src/lib/components/common/CodeEditor.svelte:181-190`, `:296-299`). On save, the editor shows this toast and then saves the unformatted code anyway (`src/lib/components/admin/Functions/FunctionEditor.svelte:347-363`; `src/lib/components/workspace/Tools/ToolkitEditor.svelte:187-203`), so a save error from section 10.9 or the tools router usually follows | Fix the Python syntax at the line named in the toast | Not explained elsewhere. None; the problem is in the code being edited |
| `Code execution is disabled` | Error (HTTP 403) | `backend/open_webui/routers/utils.py:44`; text from `backend/open_webui/constants.py:125` | **Run** on a code block with the Jupyter engine after code execution was switched off (`code_execution.enable`); the code block shows it as a toast (`src/lib/components/chat/Messages/CodeBlock.svelte:149-152`) | Reload the page | See `code-execution-and-interpreter.md` section 10 |
| `[ERROR: Code execution engine not supported]` | Error (HTTP 400) | `backend/open_webui/routers/utils.py:68` | The page believes the engine is `jupyter` but the saved engine is something else (the code default is `pyodide`, which runs in the browser, `backend/open_webui/config.py:411`) | Reload the page | See `code-execution-and-interpreter.md` section 10 |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 401) | `backend/open_webui/routers/utils.py:78` | The admin **Database** download while `ENABLE_ADMIN_EXPORT` is off (environment, code default on, `backend/open_webui/config.py:2082`); shown as a toast (`src/lib/components/admin/Settings/Database.svelte:130-134`) | None | See `admin-settings-panels.md` section 10 |
| `This feature is only available with SQLite databases.` | Error (HTTP 400) | `backend/open_webui/routers/utils.py:84` | The **Database** download when the database is not SQLite (for example PostgreSQL) | None; database backups are an infrastructure task (**TO BE CONFIRMED** who does them) | See `admin-settings-panels.md` section 10 |

### 10.8 `backend/open_webui/routers/pipelines.py` (Pipelines Servers and Pipelines Filters)

The management routes behind **Admin Settings → Pipelines** are admin-only (`backend/open_webui/routers/pipelines.py:205`, `:228`, `:317`, `:367`, `:412`, `:451`, `:498`, `:539`). The filter calls run during every user's chats and generation tasks. All rows are also explained in `functions-pipes-filters-actions-and-pipelines.md` section 10.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Only Python (.py) files are allowed.` | Error (HTTP 400) | `backend/open_webui/routers/pipelines.py:235` | Uploading a pipeline file whose name does not end in `.py` | Choose a `.py` file | See `functions-pipes-filters-actions-and-pipelines.md` section 10, which records what the panel shows instead |
| `Pipeline not found` | Error (HTTP 404, or the Pipelines server's status when it answered) | `backend/open_webui/routers/pipelines.py:301` (upload), `:355` (install from URL), `:405` (delete), `:440` (list), `:487` (read valves), `:527` (valves definition), `:570` (save valves) | MedIT GPT could not complete the call to the Pipelines server and that server gave no `detail`: it is unreachable, the address or key is wrong, or it failed without explanation. The cause is logged as `Connection error: {e}` (for example `:288`) | Admin: check the Pipelines connection | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `{detail}` (the Pipelines server's own `detail`, management routes) | Error (that server's HTTP status) | The same lines as `Pipeline not found` | The Pipelines server answered a management call with an error and a JSON `detail`, which MedIT GPT passes on (for example `:290-304`) | Admin: read the text; it comes from the Pipelines server | See `functions-pipes-filters-actions-and-pipelines.md` section 10; the Pipelines server's own logs |
| `{detail}` (a Pipelines filter's own `detail`) | Error in the reply's error box; the filter's HTTP status for programs and generation tasks | `backend/open_webui/routers/pipelines.py:108` (inlet), `:174` (outlet) | Inlet: before the model call, a Pipelines filter answered with an error status and a JSON `detail`. In chats the text is saved on the reply and shown in its error box (`backend/open_webui/main.py:1686-1713`); generation tasks answer with it (section 10.12). Outlet: after the reply, the error is only logged at debug level during chats (`backend/open_webui/utils/middleware.py:4145-4149`); only the deprecated `/api/chat/completed` endpoint returns it, as `{status}: {detail}` (`backend/open_webui/utils/chat.py:334-337`; section 10.18) | Retry; report the exact text | See `functions-pipes-filters-actions-and-pipelines.md` section 10; the Pipelines server's logs |
| `{e.message}` (the HTTP reason phrase, for example `Internal Server Error` or `Bad Request`) | Error (as the row above) | `backend/open_webui/routers/pipelines.py:117` (inlet), `:183` (outlet) | A Pipelines filter answered with an error status and no JSON `detail`; the text is the standard name of that status, which the HTTP client keeps as the error's message (`.venv/lib/python3.12/site-packages/aiohttp/client_reqrep.py:636-641`) | Retry | As above |

### 10.9 `backend/open_webui/routers/functions.py` (Functions)

The function list, editor and valves are admin-only; personal valves (**UserValves**) are open to every verified user (`backend/open_webui/routers/functions.py:569-668`). Every `[ERROR: …]` text comes from the `DEFAULT` formatter (section 4.2): when it is given the exception, a recognized storage error replaces the text with one of the storage messages, for example `[ERROR: The server is out of storage space.]` (`backend/open_webui/constants.py:6-13`, `:19-20`). Several not-found answers use HTTP 401 (section 3.1). All rows are also explained in `functions-pipes-filters-actions-and-pipelines.md` section 10.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Please enter a valid URL` | Not expected from the server | `backend/open_webui/routers/functions.py:115` | The request model already refuses an empty or non-web address with HTTP 422 before this line runs (`:86-87`, a web-address field), so this server check cannot fire; the same words come from the import dialog's own check in the browser | Enter the address | See `functions-pipes-filters-actions-and-pipelines.md` section 10; section 14 |
| `Failed to fetch the function` | Error (the address's own HTTP status) | `backend/open_webui/routers/functions.py:137` | **Import From Link**: the address answered with a status other than 200 | Use a raw-file link the server can read | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `No data received from the URL` | Error (HTTP 400) | `backend/open_webui/routers/functions.py:140` | The address answered with an empty file | Check the link | As above |
| `[ERROR: Error fetching function]` | Error (HTTP 500) | `backend/open_webui/routers/functions.py:148` | The download itself failed (unknown host, refused connection, certificate problem, time limit) | Try later | As above |
| `[ERROR: Error loading function]` | Error (HTTP 400) | `backend/open_webui/routers/functions.py:189` | API-only bulk sync: one supplied function failed to load, or its valves failed to validate | None | As above; log `Failed to load a function: {e}` (`:188`) |
| `Only alphanumeric characters and underscores are allowed in the id` | Error (HTTP 400) | `backend/open_webui/routers/functions.py:208` | The Function ID is not a valid Python name (Python's `isidentifier` check, `:207`) | Change the ID | As above |
| `[ERROR: Error creating function]` | Error (HTTP 400) | `backend/open_webui/routers/functions.py:246` (the stored row was not returned), `:254` (an error while loading the code, installing its packages or storing it) | **Save** of a new function failed | Correct the code; an administrator checks the packages | As above; log `Failed to create a new function: {e}` (`:253`) |
| `Uh-oh! This id is already registered. Please choose another id string.` | Error (HTTP 400) | `backend/open_webui/routers/functions.py:259` | A new function's ID, lower-cased, is already used (`:213-216`) | Choose another ID | As above |
| `We could not find what you're looking for :/` | Error (HTTP 401) | `backend/open_webui/routers/functions.py:277`, `:331`, `:368`, `:476`, `:506`, `:552`, `:558`, `:584`, `:612`, `:660`, `:665` | The function no longer exists, or valves were saved for a function whose code has no `Valves` (`:552`) or `UserValves` (`:660`) class. The 401 does not mean the person is signed out | Go back to the list and reload | As above |
| `[ERROR: Error updating function]` | Error (HTTP 400) | `backend/open_webui/routers/functions.py:326` (on/off switch), `:363` (**Global** switch), `:413`, `:421` (save) | The change could not be stored, or saved code failed to load; in that case the loader also switches the function off (`backend/open_webui/utils/plugin.py:307-313`) | Correct the code, save, then switch the function back on | As above |
| `[ERROR: Error getting function valves]` | Error (HTTP 400) | `backend/open_webui/routers/functions.py:471` | Reading the admin valves raised an error | None | As above |
| `[ERROR: Error updating function valves]` | Error (HTTP 400) | `backend/open_webui/routers/functions.py:547` | Admin valve values do not fit the function's `Valves` definition (wrong type, missing required value) | Correct the value | As above; log `Error updating function values by id {id}: {e}` (`:546`) |
| `[ERROR: Error getting function user valves]` | Error (HTTP 400) | `backend/open_webui/routers/functions.py:579` | Reading a person's own valves raised an error | None | As above |
| `Function is not active` | Error (HTTP 400) | `backend/open_webui/routers/functions.py:630` | Saving personal valves for a function that is switched off | Ask whether the function should be on | As above |
| `[ERROR: Error updating function user valves]` | Error (HTTP 400) | `backend/open_webui/routers/functions.py:655` | A person's own valve values do not fit the function's `UserValves` definition | Correct the value | As above; log `Error updating function user valves by id {id}: {e}` (`:654`) |

### 10.10 `backend/open_webui/routers/analytics.py` (Admin Analytics)

None found in code: this file raises no message of its own (no `HTTPException`, `raise` or `detail` in it). Its eight routes all use `get_admin_user` (`backend/open_webui/routers/analytics.py:63`, `:91`, `:134`, `:168`, `:205`, `:240`, `:294`, `:347`), and when `ENABLE_ADMIN_ANALYTICS` is off (environment, code default on, `backend/open_webui/config.py:2094`) the router is not mounted at all (`backend/open_webui/main.py:878-879`). Two texts can therefore appear on analytics addresses:

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 401) | `backend/open_webui/utils/auth.py:627`, through every route in `backend/open_webui/routers/analytics.py` | A non-admin reached an analytics address | None | Sections 3.1 and 10.14; the analytics pages are described in `evaluations-feedback-and-analytics.md` |
| `Method Not Allowed`, or the application page itself instead of data | Read from code (HTTP 405, or HTTP 200 with the page) | `backend/open_webui/main.py:298-310`, `:3066-3075`; `.venv/lib/python3.12/site-packages/starlette/staticfiles.py:113-114` | Analytics switched off while the server also serves the built web pages (as the Docker image does): no analytics route exists, so the request falls through to the web-page server, which answers a read with the application page and anything else with HTTP 405. The analytics page itself returns to `/admin` when analytics is off (`src/routes/(app)/admin/analytics/+page.svelte:6-12`), so this needs an old tab or a script | Reload the page | Whether `ENABLE_ADMIN_ANALYTICS` is meant to be on is **TO BE CONFIRMED** |

### 10.11 `backend/open_webui/routers/evaluations.py` (Ratings and the Evaluations Page)

All rows are also explained in `evaluations-feedback-and-analytics.md` section 10, which records the toast each one produces.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Something went wrong :/` | Error (HTTP 400) | `backend/open_webui/routers/evaluations.py:434` | A new rating (thumbs up or down, with its details) could not be stored | Try again later | See `evaluations-feedback-and-analytics.md` section 10; escalate with the time |
| `We could not find what you're looking for :/` | Error (HTTP 404) | `backend/open_webui/routers/evaluations.py:457` (read), `:476` (update), `:501` (delete) | The rating no longer exists, or, for a non-admin, belongs to someone else (`:451-454`, `:470-473`, `:495-498`) | Reload; rate again if needed | As above |
| `Embedding model load failed: {e}` | Log (error) | `backend/open_webui/routers/evaluations.py:82` | The leaderboard's topic-search model could not be loaded; the search falls back to the plain ranking (`:178-180`) | None | As above |
| `Embedding error: {e}` | Log (error) | `backend/open_webui/routers/evaluations.py:191` | The topic-search model failed while encoding; same fallback (`:192`) | None | As above |

### 10.12 `backend/open_webui/routers/tasks.py` (Background Generation Tasks)

These endpoints produce chat titles, follow-up suggestions, tags, image prompts, web-search and retrieval queries, autocomplete suggestions, the call-mode emoji and **Merge Responses** (mixture of agents). All need a verified user (for example `backend/open_webui/routers/tasks.py:142`). Most of these texts do not reach people: the chat pipeline treats a refusal as "no result" (`chat-completion-pipeline-and-generation-tasks.md` section 10 names the few places that show one, such as the sidebar's **Generate**). A Pipelines inlet filter error (section 10.8) passes out of each endpoint unchanged, with the filter's status (for example `:196-200`). Every row except `{e}` is also explained in `chat-completion-pipeline-and-generation-tasks.md` section 10.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Title generation is disabled` | Notice (HTTP 200, not shown) | `backend/open_webui/routers/tasks.py:144` | Title task called while switched off (`task.title.enable`) | None | See `chat-completion-pipeline-and-generation-tasks.md` section 10 |
| `No model specified for title generation. Please ensure a model is selected for this chat.` | Error (HTTP 400) | `backend/open_webui/routers/tasks.py:159` | Title task called with an empty model id | Select a model | As above |
| `Model '' was not found` | Error (HTTP 404) | `backend/open_webui/routers/tasks.py:164`, `:232`, `:297`, `:356`, `:433`, `:509`, `:568`, `:623` | The chat's model is not in the server's model list; the quotes are empty because the code passes no name (section 4.3). After a streaming reply it can appear in the grey error box under a complete answer | Pick an available model; an answer above the box is complete | As above; section 11.6 |
| `Follow-up generation is disabled` | Notice (HTTP 200, not shown) | `backend/open_webui/routers/tasks.py:217` | Follow-up task called while switched off | None | As above |
| `Tags generation is disabled` | Notice (HTTP 200, not shown) | `backend/open_webui/routers/tasks.py:282` | Tags task called while switched off | None | As above |
| `An internal error has occurred.` | Error (HTTP 400 at `:208`, `:273`, `:397`; HTTP 500 at `:338`, `:550`) | `backend/open_webui/routers/tasks.py:208` (title), `:273` (follow-ups), `:338` (tags), `:397` (image prompt), `:550` (autocomplete) | The task-model call failed; the reason is logged as `Exception occurred` (`:207`, `:272`, `:396`) or `Error generating chat completion: {e}` (`:337`, `:549`) | Retry later | As above |
| `Search query generation is disabled` | Error (HTTP 400, not shown) | `backend/open_webui/routers/tasks.py:408`; composed at run time by the `FEATURE_DISABLED` formatter (`backend/open_webui/constants.py:125`), so the whole sentence is not a literal in the source, as with `Query generation is disabled` and `Autocompletion generation is disabled` | Web-search query generation switched off (`task.query.search.enable`); the user's message is searched as written | None | As above |
| `Query generation is disabled` | Error (HTTP 400, not shown) | `backend/open_webui/routers/tasks.py:414` | Retrieval query generation switched off (`task.query.retrieval.enable`) | None | As above |
| `{e}` (the failure's own text; for an HTTP error from a provider it reads `{status}: {detail}`, section 4.4) | Error (HTTP 400, not shown) | `backend/open_webui/routers/tasks.py:473` (queries), `:604` (call-mode emoji), `:657` (**Merge Responses**) | The task-model call failed. The web interface does not show the text: query generation falls back to the user's own words (`backend/open_webui/utils/middleware.py:1590-1600`), the call overlay only logs it in the browser console (`src/lib/components/chat/MessageInput/CallOverlay.svelte:509-514`), and **Merge Responses** leaves the merged answer empty (`src/lib/components/chat/Chat.svelte:3911-3947`) | Retry **Merge Responses** once | Not explained elsewhere. Escalate if merging stays empty, with the chat link and the time |
| `Autocompletion generation is disabled` | Error (HTTP 400, not shown) | `backend/open_webui/routers/tasks.py:482` | Autocomplete called while switched off (`task.autocomplete.enable`, code default off) | None | As above |
| `Input prompt exceeds maximum length of {size}` | Error (HTTP 400, not shown) | `backend/open_webui/routers/tasks.py:494`; text from `backend/open_webui/constants.py:126` | The draft is longer than `task.autocomplete.input_max_length` (when that is above 0); no suggestion appears | None | As above |

### 10.13 `backend/open_webui/routers/notifications.py` (Personal Notification Targets)

Personal webhook targets in **Settings → Notifications**. Every route needs a verified user and then passes `_check_notifications_access` (`backend/open_webui/routers/notifications.py:34-41`). All rows are also explained in `notifications-webhooks-events-and-banners.md` section 10.4, which records which buttons show the text.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `We could not find what you're looking for :/` | Error (HTTP 404) | `backend/open_webui/routers/notifications.py:36`, `:80` | **User Webhooks** (`ui.enable_user_webhooks`, code default off) is off, which every route reports this way (`:35-36`); or the target to remove no longer exists (`:79-80`) | Ask an administrator whether personal webhooks are offered | See `notifications-webhooks-events-and-banners.md` section 10 |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 403) | `backend/open_webui/routers/notifications.py:41` | A non-admin without the `features.webhooks` permission | Ask an administrator for the permission | As above |
| `{e}` (a rule text from `backend/open_webui/utils/notifications.py`) | Error (HTTP 400) | `backend/open_webui/routers/notifications.py:62` (add), `:73` (edit), `:90` (make default), `:103` (send test) | One of: `Webhook URL is required`, `The URL you provided is invalid. Please double-check and try again.`, `notification target id already exists`, `Notification target not found`, `Webhook delivery failed` (send test only), `User not found`, or, from malformed requests, `unsupported notification event: {event}`, `events must be a list`, `Invalid notification delivery mode`, `Unsupported notification target type` (`backend/open_webui/utils/notifications.py:35-67`, `:100`, `:167`, `:190`, `:197`, `:220`, `:256`, `:261`, `:353`) | Depends on the text: usually correct the address, or reload | As above |

### 10.14 `backend/open_webui/utils/auth.py` (Sign-In Token, API Key and Role Checks)

These checks run before almost every endpoint, so their texts can appear anywhere in the application. In order: a sign-in token or API key must be present (`Not authenticated`), readable and not revoked, and belong to an existing account (`backend/open_webui/utils/auth.py:393-506`); then the role check (`:567-576`, `:625-631`). A failed token check also removes the browser's sign-in cookies (`:494-506`). Section 3.1 explains how to tell the 401 texts apart; `authentication-and-sign-in.md` section 10 explains each in full.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Not authenticated` | Error (HTTP 401) | `backend/open_webui/utils/auth.py:416` | No sign-in token or API key reached the server, typically from a script or integration | Sign in again; programs must send their key | See `authentication-and-sign-in.md` section 10 |
| `Invalid token` | Error (HTTP 401) | `backend/open_webui/utils/auth.py:450`; also `:443`, which is not expected because the token reader never raises (`:246-251`) | A token that was revoked, which needs Redis: a sign-out with that token, a password change or admin reset, or an identity-provider logout (`:276-312`) | Sign in again | As above; section 11.4 |
| `Your session has expired or the token is invalid. Please sign in again.` | Error (HTTP 401) | `backend/open_webui/utils/auth.py:457`, `:514` | A readable token whose account no longer exists (`:455-460`), or an API key that matches no account (`:509-517`) | Sign in again; programs use the current key | As above; section 11.3 |
| `User mismatch. Please sign in again.` | Error (HTTP 401) | `backend/open_webui/utils/auth.py:465` | Trusted-header mode only: the proxy's email header now names a different person from the session (`:462-468`) | Sign out and sign in again | As above; `sso-oauth-oidc-and-scim.md` section 10 |
| `401 Unauthorized` | Error (HTTP 401) | `backend/open_webui/utils/auth.py:490`; text from `backend/open_webui/constants.py:69` | The token has expired or cannot be read, for example after the server's secret key changed (`:489-493`) | Sign in again | See `authentication-and-sign-in.md` section 10; section 11.4 |
| `Use of API key is not enabled in the environment.` | Error (HTTP 403) | `backend/open_webui/utils/auth.py:527`, `:536` | An API key was used while API keys are switched off (`auth.enable_api_keys`, `:526-527`), or by a non-admin without the `features.api_keys` permission (`:529-536`) | Ask an administrator whether API keys are available | See `authentication-and-sign-in.md` section 10 |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 401 at `:572`, `:627`; HTTP 403 at `:547`) | `backend/open_webui/utils/auth.py:572` (`get_verified_user`), `:627` (`get_admin_user`), `:547` (API key outside the allowed endpoints) | A `pending` account on any signed-in endpoint; a non-admin on an admin endpoint; an API key used on a path outside **Allowed Endpoints** while endpoint restrictions are on (`:541-550`) | A pending account waits for an administrator to activate it | Section 3.1; section 11.2 |
| `Uh-oh! The password you entered is too long. Please make sure your password is less than 72 bytes long.` | Error, raised to the caller | `backend/open_webui/utils/auth.py:193`; text from `backend/open_webui/constants.py:48-50` | `validate_password` with `PASSWORD_HASH_ALGORITHM` = `bcrypt` (the code default) and a new password over 72 bytes in UTF-8, where an accented letter takes two bytes (`:190-195`) | Choose a shorter password | Shown as HTTP 400 by sections 10.2 and 10.3; see `authentication-and-sign-in.md` section 10 |
| `{PASSWORD_VALIDATION_HINT}`, or when that is empty `The password does not meet the required validation criteria.` | Error, raised to the caller | `backend/open_webui/utils/auth.py:199`; text from `backend/open_webui/constants.py:114` | `ENABLE_PASSWORD_VALIDATION` is on and the new password does not match the configured pattern (`:197-199`); the text is the operator's hint | Follow the hint | As above |
| `Unsupported PASSWORD_HASH_ALGORITHM: {PASSWORD_HASH_ALGORITHM}` | Error, raised to the caller | `backend/open_webui/utils/auth.py:187` | A new password is being hashed while the variable holds something other than `bcrypt` or `argon2` (`:180-187`) | None | Escalate (server configuration); see `authentication-and-sign-in.md` section 10 for what the person sees |
| `Cannot revoke tokens for user {user_id}: Redis is not configured, existing sessions stay valid until expiry.` | Log (warning) | `backend/open_webui/utils/auth.py:354-357` | A password change or admin reset (or another per-user revocation) on a server without Redis (`:349-358`) | None | Explains why other sessions stayed signed in; see `authentication-and-sign-in.md` section 10 |
| `Failed to create admin account from environment variables` | Log (error) | `backend/open_webui/utils/auth.py:661` | Start-up admin bootstrap (`WEBUI_ADMIN_EMAIL`, `WEBUI_ADMIN_PASSWORD`, no users yet) did not store the account | None | Escalate (deployment); see `authentication-and-sign-in.md` section 10 |
| `Error creating admin account: {e}` | Log (error) | `backend/open_webui/utils/auth.py:664` | The same bootstrap raised an error | None | As above |

Lines beginning `License:` (`backend/open_webui/utils/auth.py:116`, `:124`, `:136`, `:170`) are written only when a licence key is configured (`LICENSE_KEY`, `backend/open_webui/env.py:922`); whether MedIT GPT has one is **TO BE CONFIRMED**.

### 10.15 `backend/open_webui/utils/oauth.py` (Single Sign-On, Tool-Server Sign-In and Back-Channel Logout)

Three groups of texts. **Single sign-on** failures are caught and sent back to the sign-in page as `/auth?error=<message>`, which shows the text as a toast (`backend/open_webui/utils/oauth.py:2167-2181`; `src/routes/auth/+page.svelte:168-170`), so the HTTP status is not seen. **Tool-server sign-in** (OAuth for an MCP tool server) failures after the provider's answer go to `/?error=<message>` and show on the home page (`backend/open_webui/utils/oauth.py:1318-1324`; `src/routes/(app)/+page.svelte:9-10`); failures before the person leaves MedIT GPT show as a plain error page. **Back-channel logout** texts are read only by the identity provider. All rows are also explained in `sso-oauth-oidc-and-scim.md` section 10, which also lists this file's server log lines (its section 10.3).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{"detail":"Not Found"}` (single sign-on) | Error page (HTTP 404, the framework's default text) | `backend/open_webui/utils/oauth.py:1853`, `:1855`, `:1859` (start), `:1875`, `:1877` (return) | Single sign-on is off in the server process that answered, or the provider in the address is not registered | Use the sign-in method the site offers | See `sso-oauth-oidc-and-scim.md` section 10 |
| `The email or password provided is incorrect. Please check for typos and try logging in again.` | Error (shown after the redirect to `/auth`) | `backend/open_webui/utils/oauth.py:1911`, `:1920` (code exchange failed), `:1943` (no user details), `:1953` (no subject claim), `:1988`, `:1991`, `:1994` (GitHub email lookup), `:1999` (no email claim), `:2008` (email domain not allowed) | Single sign-on only, although no password was typed (ground truth) | Try once more; note the time | As above; section 11.1 |
| `Uh-oh! This email is already registered. Sign in with your existing account or choose another email to start anew.` | Error (after the redirect) | `backend/open_webui/utils/oauth.py:2099` | OAuth sign-up is on, no account carries this provider's subject, and another account already uses the email (`:2094-2099`) | Sign in the way that account was created | As above |
| `Oops! Something went wrong while creating your account. Please try again later. If the issue persists, contact support for assistance.` | Error (after the redirect) | `backend/open_webui/utils/oauth.py:2128` | The new single sign-on account could not be stored | Try again later | As above; escalate with the time |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | Error (HTTP 403; after the redirect at sign-in) | `backend/open_webui/utils/oauth.py:2149` (no account and OAuth sign-up off), `:1605` (role mapping: the person's roles match no allowed or admin role), `:1578` (token exchange: no readable roles claim) | See the trigger in each line | Contact an administrator | As above; section 11.2 |
| `[ERROR: Error during OAuth process]` | Error (after the redirect) | `backend/open_webui/utils/oauth.py:2172` | Any other failure during the single sign-on callback, for example a database error or a failure while applying group mapping | Try once more | As above; log `Error during OAuth process: {e}` (`:2168`) |
| `{"detail":"Not Found"}` (tool-server sign-in) | Error page (HTTP 404) | `backend/open_webui/utils/oauth.py:1197`, `:1203` (start), `:1237` (return) | The tool server's sign-in details cannot be loaded (removed, not an OAuth tool server, or an unreadable stored registration) | None | As above |
| `OAuth authorization state was not generated` | Error page (HTTP 500) | `backend/open_webui/utils/oauth.py:1212` | Internal failure while starting a tool-server connection | Try again | As above |
| `OAuth authorization endpoint could not be resolved for this client. Re-register the MCP server; its OAuth discovery documents may be missing or unreachable.` | Error page (HTTP 400) | `backend/open_webui/utils/oauth.py:1225` | Starting a connection to a tool server whose sign-in address is unknown | None | As above; escalate to the administrator who manages the tool server |
| `OAuth callback failed: {detail}` | Error (toast on the home page) | Built at `backend/open_webui/utils/oauth.py:282-310`; used at `:1306` | The tool-server connection round trip failed; `{detail}` is one of the next six texts or the sign-in service's own error, and the whole message is cut at 200 characters with `...` (`:310`) | Connect the tool again | As above |
| `OAuth callback state is invalid or expired` | Error (as `{detail}` above) | `backend/open_webui/utils/oauth.py:1247` | The round trip's saved state was missing or expired, for example the connection was started in another tab or browser | Start again from the same tab | As above |
| `OAuth callback user is not authorized` | Error (as `{detail}`) | `backend/open_webui/utils/oauth.py:1253` | The account that started the connection is no longer `user` or `admin` | Contact an administrator | As above |
| `OAuth callback user does not match authenticated session` | Error (as `{detail}`) | `backend/open_webui/utils/oauth.py:1260` | A different MedIT GPT account is signed in in this browser | Sign in as the right account and connect again | As above |
| `Missing state parameter in callback (session may have expired)` | Error (as `{detail}`) | `backend/open_webui/utils/oauth.py:299` | The sign-in service returned without the state value | Connect again | As above |
| `Missing expected key '{missing}' in OAuth response` | Error (as `{detail}`) | `backend/open_webui/utils/oauth.py:301` | The sign-in service's answer lacked a required value | None | As above |
| `Upstream provider returned {e.status}: {e.message}` | Error (as `{detail}`) | `backend/open_webui/utils/oauth.py:293` | The sign-in service answered with an HTTP error | Try later | As above |
| `Token exchange failed: {error_desc}` | Error (toast on the home page) | `backend/open_webui/utils/oauth.py:1278` | The sign-in service refused to issue a token; `{error_desc}` is its reason | Try again | As above |
| `Failed to store OAuth session server-side` | Error (toast on the home page) | `backend/open_webui/utils/oauth.py:1299` | The connection worked but could not be saved | Try again | As above |
| `Failed to obtain OAuth token` | Error (toast on the home page) | `backend/open_webui/utils/oauth.py:1303` | The sign-in service returned no token | Try again | As above |
| `Could not discover the OAuth authorization server metadata (authorization_endpoint) for {oauth_server_url}. The MCP server must expose RFC 8414 / RFC 9728 discovery documents so Open WebUI can resolve where to send users to authorize.` | Error, raised to the caller (inside `Failed to register OAuth client: {e}`, section 10.6) | `backend/open_webui/utils/oauth.py:578` | Registering a tool server whose sign-in service publishes no usable discovery document. The text says "Open WebUI" although the product is MedIT GPT (section 12) | Administrator only | As above |
| `Dynamic client registration failed: {error_text}` | Error, raised to the caller (as above) | `backend/open_webui/utils/oauth.py:636` | The sign-in service refused automatic registration and gave a reason | Administrator only | As above |
| `Error parsing client registration response` | Error, raised to the caller (as above) | `backend/open_webui/utils/oauth.py:636` | The registration answer could not be read and carried no text | Administrator only | As above |
| `Dynamic client registration failed` | Not expected | `backend/open_webui/utils/oauth.py:641` | Read from code, unreachable: the block before it always returns or raises (`:599-640`) | None | Section 14 |
| `Missing logout_token parameter` | API error (HTTP 400, `error_description` with `error` = `invalid_request`) | `backend/open_webui/utils/oauth.py:2281` | Back-channel logout notice without a logout token | None (identity provider) | As above |
| `Malformed logout_token` | API error (as above) | `backend/open_webui/utils/oauth.py:2292` | The logout token could not be read | None | As above |
| `logout_token missing iss claim` | API error (as above) | `backend/open_webui/utils/oauth.py:2298` | The token does not say who issued it | None | As above |
| `No configured provider matches token issuer` | API error (as above) | `backend/open_webui/utils/oauth.py:2329` | The issuer is not a registered provider | None | As above |
| `Invalid logout_token: {e}` | API error (as above) | `backend/open_webui/utils/oauth.py:2365` | The notice failed the server's authenticity checks; `{e}` names the failed check | None | As above; escalate to the maintainer |
| `Failed to validate logout_token` | API error (as above) | `backend/open_webui/utils/oauth.py:2371` | An unexpected error during those checks | None | As above |
| `Missing backchannel-logout event claim` | API error (as above) | `backend/open_webui/utils/oauth.py:2380` | The token does not declare itself a back-channel logout notice | None | As above |
| `logout_token must not contain nonce` | API error (as above) | `backend/open_webui/utils/oauth.py:2388` | The token carries a value the standard forbids in logout notices | None | As above |
| `logout_token must contain sub or sid` | API error (as above) | `backend/open_webui/utils/oauth.py:2399` | The token names neither a person nor a provider session | None | As above |

### 10.16 `backend/open_webui/utils/rate_limit.py` (Sign-In Throttling)

This file raises no message of its own. It decides when `backend/open_webui/routers/auths.py` refuses a sign-in with `API rate limit exceeded` (section 10.2), so the facts support needs are collected here.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `API rate limit exceeded` | Error (HTTP 429) | Raised at `backend/open_webui/routers/auths.py:819` (sign-in) and `:1645` (token exchange); decided by `backend/open_webui/utils/rate_limit.py:47-61` | The sign-in limiter allows 15 attempts per email in a 180-second window (`backend/open_webui/routers/auths.py:91`). The window is counted in one-minute buckets: the current minute plus the previous three (`backend/open_webui/utils/rate_limit.py:30`, `:88-93`, `:101-109`), so the 16th attempt within roughly three to four minutes is refused | Stop for at least four minutes, then sign in once | Section 11.5 |

| Behaviour | Evidence |
|---|---|
| Every attempt counts, successful or refused, because the counter goes up before the comparison; retrying while blocked keeps the block going | `backend/open_webui/utils/rate_limit.py:83`, `:93`, `:106-109` |
| The counter is per email address, lower-cased | `backend/open_webui/routers/auths.py:818`; `backend/open_webui/utils/rate_limit.py:36` |
| With Redis the count is shared by every server process; without Redis, or when a Redis call fails, each process counts on its own | `backend/open_webui/utils/rate_limit.py:55-61`, `:101-109` |
| The token-exchange limiter exists only when `OAUTH_TOKEN_EXCHANGE_RATE_LIMIT` is set | `backend/open_webui/routers/auths.py:94-101` |

### 10.17 `backend/open_webui/utils/plugin.py` (Loading Functions and Workspace Tools)

These texts are raised to the code that asked for a function or tool. Through the function and tool editors they are hidden behind `[ERROR: …]` texts (section 10.9); in chats they can reach the reply's error box.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Plugins are disabled by ENABLE_PLUGINS=false` | Error, raised to the caller | `backend/open_webui/utils/plugin.py:208` (tools), `:261` (functions) | Loading a workspace tool or a function while `ENABLE_PLUGINS` is off (environment, code default on, `backend/open_webui/env.py:1186`) | Reload the page | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `Toolkit not found: {tool_id}` | Not expected | `backend/open_webui/utils/plugin.py:214` | Reached only when a tool is loaded without its code, which no caller does in v0.11.4: the one helper that could, `get_tool_module` (`backend/open_webui/routers/tools.py:52-57`), is never called | None | Section 14 |
| `No Tools class found in the module` | Error, raised to the caller | `backend/open_webui/utils/plugin.py:250` | A workspace tool's code defines no `Tools` class | Fix the code | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Function not found: {function_id}` | Error, raised to the caller | `backend/open_webui/utils/plugin.py:267`, `:390` | A function was deleted while something still referred to it: a pipe model from a model list loaded earlier (`:387-390`), or a stream filter not held in this server process's memory (`:404-411`) | Reload the page | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `No Function class found in the module` | Error, raised to the caller | `backend/open_webui/utils/plugin.py:306` | The function's code defines none of `Pipe`, `Filter`, `Action` or `Event`; the loader also switches the function off (`:307-313`) | Fix the code | As above |
| `Tool not found: {tool_id}` | Not expected in normal use | `backend/open_webui/utils/plugin.py:349` | Loading a tool whose row no longer exists; the tool routes check that the tool exists first (for example `backend/open_webui/routers/tools.py:746-751`), so only a deletion between the two checks reaches it | Reload | Section 14 |
| `Error loading module: {function_id}: {e}` (or `{tool_id}` for tools) | Log (error) | `backend/open_webui/utils/plugin.py:252`, `:308` | The stored code raised an error while loading; `{e}` is the Python error | None | The cause behind most `[ERROR: …]` texts in section 10.9 |
| `Error installing packages: {new_reqs}` | Log (error) | `backend/open_webui/utils/plugin.py:446` | A package listed in the code's `requirements` line failed to install; `{new_reqs}` is the space-separated list | None | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `Error installing requirements: {e}` | Log (error) | `backend/open_webui/utils/plugin.py:484` | The start-up installation of every function's and admin tool's packages failed (`:453-484`); start-up continues | None | As above |
| `ENABLE_PIP_INSTALL_FRONTMATTER_REQUIREMENTS is disabled, skipping installation of requirements.` | Log (info) | `backend/open_webui/utils/plugin.py:425` | Package installation switched off (`backend/open_webui/env.py:1188-1190`); code that needs a missing package then fails to load | None | Explains a missing-module error |
| `Offline mode enabled, skipping installation of requirements.` | Log (info) | `backend/open_webui/utils/plugin.py:429` | `OFFLINE_MODE` is on (`backend/open_webui/env.py:1201`) | None | As above |
| `ENABLE_PLUGINS is disabled, skipping tool and function dependencies.` | Log (info) | `backend/open_webui/utils/plugin.py:462` | Start-up with plugins switched off | None | None |

### 10.18 `backend/open_webui/main.py` (Chat Endpoints, Model Unload, Webhooks, Readiness and Start-Up)

`main.py` defines the top-level endpoints (inventory: 39 routes). Chat texts are explained in full in `chat-completion-pipeline-and-generation-tasks.md` section 10; the rows here keep the trigger short.

**Chat completions and related chat endpoints**

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Model not found` | Error (HTTP 400; pop-up and reply error box) | `backend/open_webui/main.py:1129`, `:1182`, turned into HTTP 400 at `:1640-1645`; also `backend/open_webui/utils/models.py:480`, `:491` through the access check at `:1157` | The chat's model is not in the server's model list; a workspace model's base model is missing and no fallback is set (`ENABLE_CUSTOM_MODEL_FALLBACK`, code default off, `backend/open_webui/env.py:1033`); or the person has no access to the model | Pick another model | See `chat-completion-pipeline-and-generation-tasks.md` section 10; section 11.6 |
| `We could not find what you're looking for :/` | Error (HTTP 404) | `backend/open_webui/main.py:1315` (channel missing), `:1357` (new chat in a folder the person cannot write to), `:2167`, `:2171` (stopping a chat that is not the person's, or does not exist) | See the trigger in each line | Reload; start the chat outside the folder | As above |
| `Something went wrong :/` | Error (HTTP 403 at `:1322`, `:1333`, `:1347`; HTTP 404 at `:1496`, `:2084`) | `backend/open_webui/main.py:1322`, `:1333`, `:1347`, `:1496`, `:2084` | A model reply into a channel the person is not a member of or cannot write to, or targeting another member's channel message (`:1311-1350`); posting into a chat the person does not own (`:1494-1499`); the deprecated completed or action endpoints for such a chat (`:2083-2087`) | Open a new chat | As above; section 11.7 |
| `{e}` (the reason, for example a filter's or tool's error text) | Error (HTTP 400) | `backend/open_webui/main.py:1642` | Any other failure while preparing the chat, before the reply task starts; logged as `Error processing chat metadata: {e}` (`:1641`) | Retry; report the text | As above |
| `{error_detail}` (the failure's text) | Error (the reply's error box; HTTP 400 at `:1719` for programs) | `backend/open_webui/main.py:1686-1722`; provider error answers are turned into text at `:1664-1665` (`backend/open_webui/utils/misc.py:43-65`) | Any failure inside the reply task: a provider error, a Pipelines inlet filter, a function filter, a tool. The text is saved on the reply (`:1689-1701`), so it is still shown after a reload, and logged as `Error processing chat payload: {error_detail}` (`:1688`). Callers without a chat get HTTP 400 | Retry; report the exact text | As above |
| `Channel chats are not supported on this endpoint` | API error (HTTP 400) | `backend/open_webui/main.py:2078` | The deprecated `/api/chat/completed` endpoint or an Action called for a channel message | None (integration issue) | As above |
| `{e}` (deprecated completed and action endpoints) | API error (HTTP 400) | `backend/open_webui/main.py:2104` (`/api/chat/completed`), `:2122` (`/api/chat/actions/{action_id}`) | The outlet filters or the Action failed; an HTTP error inside reads `{status}: {detail}` (section 4.4), for example from a Pipelines outlet filter (section 10.8) | Retry | See `functions-pipes-filters-actions-and-pipelines.md` section 10 |
| `Finalized pending approval message.` | Notice (API answer) | `backend/open_webui/main.py:2199` | **Stop** on a chat with no running task but an unfinished or paused reply; the other stop answers (`Task {task_id} stopped.` and similar) come from `backend/open_webui/tasks.py:277-309` | None | See `chat-completion-pipeline-and-generation-tasks.md` section 10 |
| `{e}` (stop one task) | Not expected | `backend/open_webui/main.py:2134` | Admin-only stop of one task by id; the function it calls returns a status message instead of raising (`backend/open_webui/tasks.py:259-293`), so this HTTP 404 is not expected | None | Section 14 |
| `Schedule took too long to evaluate; simplify its recurrence rule.` | Error (HTTP 400) | Handler at `backend/open_webui/main.py:515-517`; text from `backend/open_webui/utils/recurrence.py:103` | Working out an automation's recurrence took too long; the only custom error handler in the application turns this into HTTP 400 | Simplify the schedule | See `automations-calendar-and-timers.md` section 10 |

**Anthropic-compatible endpoint, model unload and usage**

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Open WebUI: Server Connection Error` | API error (HTTP 502) | `backend/open_webui/main.py:1996`; text from `backend/open_webui/constants.py:130` | `/api/v1/messages` (Anthropic-compatible) for a model on a connection that is passed straight through (`:2041-2044`), when the provider could not be reached or the pass-through failed; logged as `Failed to passthrough Anthropic Messages request for model {requested_model}` (`:1995`). Other models go through the chat pipeline above | Retry later | Licence-protected text (section 4.5); see `model-connections-openai-ollama-and-direct.md` section 10 |
| `Unable to count Anthropic input tokens for model {requested_model}` | Log (warning) | `backend/open_webui/main.py:2028` | The token count for an Anthropic-compatible request failed; the request still runs (`:2024-2028`) | None | Not explained elsewhere; informational |
| `Failed to unload model on {len(errors)} node(s): {errors}` | Error (HTTP 500) | `backend/open_webui/main.py:1015` | Admin **Unload** in the model selector (`src/lib/components/chat/ModelSelector/Selector.svelte:791-792`) for an Ollama model, when one or more Ollama servers refused or could not be reached; `{errors}` lists each server's index and error | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `{detail}` (llama.cpp's own answer) | Error (llama.cpp's HTTP status) | `backend/open_webui/main.py:1051` | Unload of a model on a llama.cpp connection that answered with an error | None | As above |
| `{e}` (unload) | Error (HTTP 500) | `backend/open_webui/main.py:1057` | The llama.cpp unload call failed (no answer, network error); logged at `:1056` | None | As above |
| `Provider "{provider}" does not support model unloading` | Error (HTTP 400) | `backend/open_webui/main.py:1059` | Unload of a model on an OpenAI-compatible connection whose provider type is not `llama.cpp`; `{provider}` reads `default` when no type is set | None | As above |
| `Model "{model_id}" not found` | Error (HTTP 404) | `backend/open_webui/main.py:1064` | Unload of a model that is in neither the Ollama nor the OpenAI model list | Reload the model list | As above |
| `Access denied. Only administrators can view usage statistics.` | Error (HTTP 403) | `backend/open_webui/main.py:2630` | A non-admin asked for the active-user count while `ENABLE_PUBLIC_ACTIVE_USERS_COUNT` is off; the user menu then shows no count (`src/lib/components/layout/Sidebar/UserMenu.svelte:74-84`) | None | See `users-groups-roles-and-permissions.md` section 10 |
| `Internal Server Error` (usage) | Error (HTTP 500) | `backend/open_webui/main.py:2643` | The active-user count could not be read; logged as `Error getting usage statistics: {e}` (`:2642`) | None | See `evaluations-feedback-and-analytics.md` section 10 |
| `Invalid token` (`/api/config`) | Not expected | `backend/open_webui/main.py:2243` | The token reader never raises (`backend/open_webui/utils/auth.py:246-251`), so an unreadable token makes `/api/config` answer as for a signed-out visitor instead | None | Section 14 |

**Event webhooks (admin), tool-server sign-in and back-channel logout**

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `{e}` (an event-webhook rule text) | Error (HTTP 400) | `backend/open_webui/main.py:2517` (create), `:2551` (edit) | Saving an admin event webhook that a rule in `backend/open_webui/events.py` refused, for example `The URL you provided is invalid. Please double-check and try again.` | Correct the address or the event filter | See `notifications-webhooks-events-and-banners.md` section 10 |
| `Webhook not found` | Error (HTTP 404) | `backend/open_webui/main.py:2540`, `:2573` | Editing or deleting an event webhook that no longer exists | Reload | As above |
| `{"detail":"Not Found"}` (tool-server sign-in) | Error page (HTTP 404) | `backend/open_webui/main.py:2783` | Starting a tool-server connection whose OAuth registration cannot be loaded | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `Failed to re-register OAuth client` | Error page (HTTP 500) | `backend/open_webui/main.py:2793` | The tool server's stored registration failed the pre-check and automatic re-registration failed (`:2785-2796`) | None | As above; escalate to the tool-server administrator |
| `OAuth client unavailable after re-registration` | Error page (HTTP 500) | `backend/open_webui/main.py:2801` | Re-registration reported success but the registration still cannot be loaded | None | As above |
| `OAuth client registration is still invalid after re-registration` | Error page (HTTP 500) | `backend/open_webui/main.py:2807` | The new registration also failed the pre-check | None | As above |
| `{"detail":"Not Found"}` (back-channel logout) | API error (HTTP 404) | `backend/open_webui/main.py:2864` | The identity provider sent a back-channel logout while `ENABLE_OAUTH_BACKCHANNEL_LOGOUT` is off (`backend/open_webui/env.py:901`) | None | As above |
| `No Redis URL provided` | Not shown | `backend/open_webui/main.py:2666` | Raised and caught at once whenever `ENABLE_STAR_SESSIONS_MIDDLEWARE` is off (the default, `backend/open_webui/env.py:967`), to fall back to cookie sessions (`:2667-2674`); never displayed or logged | None | Section 14 |

**Health, readiness, cache files and unknown addresses**

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Startup not complete` | Readiness (HTTP 503) | `backend/open_webui/main.py:2977` | `/ready` asked before start-up finished (the last start-up step sets the flag, `:471`); logged at info level as `Readiness check failed: startup not complete` (`:2976`) | None | Normal while the server starts (start-up first installs plugin packages and may pre-fetch models and tool servers, `:387-460`); escalate if it lasts *Precision 2026-10-11: under uvicorn the port opens only after start-up finishes (`.venv` uvicorn 0.51.0, `server.py:104` before `:142`), so a probe normally gets no connection or waits during start-up rather than seeing `Startup not complete`; see `backend-architecture-and-request-lifecycle.md` section 5.5.* |
| `Database not ready` | Readiness (HTTP 503) | `backend/open_webui/main.py:2987` | The database did not answer a test query; logged as `Readiness check DB ping failed: {e}` (`:2986`) | None | Escalate at once: every user is affected |
| `Redis not ready` | Readiness (HTTP 503) | `backend/open_webui/main.py:3001` | Redis is configured and did not answer; logged as `Readiness check Redis ping failed: {e}` (`:3000`), where `{e}` may be `Redis PING returned False` (`:2998`) | None | Escalate at once |
| `Internal Server Error` (`/health/db`) | Read from code (HTTP 500, plain text) | `backend/open_webui/main.py:3009-3013` | `/health/db` when the database does not answer: the endpoint has no error handling, so the framework's default answer is sent. `/health` itself always answers `{"status": true}` (`:2963-2965`) | None | As `Database not ready` |
| `File not found` | Error (HTTP 404) | `backend/open_webui/main.py:3042`, `:3044` | A `/cache/{path}` address that points outside the cache folder or at a file that does not exist. No code in `src/` or the backend helpers builds links to this route (search for `/cache/`); its comment mentions tool outputs | None | Not explained elsewhere |
| `Method Not Allowed`, or the application page itself instead of data | Read from code (HTTP 405, or HTTP 200 with the page) | `backend/open_webui/main.py:298-310`, `:3066-3075`; `.venv/lib/python3.12/site-packages/starlette/staticfiles.py:113-114` | Any address that matches no route (for example a router that is not mounted, section 10.10) while the server also serves the built web pages: reads get the application page, other methods get HTTP 405. Without the built pages the answer is `{"detail":"Not Found"}` | None | Section 14 |

**Start-up and background log lines in this file** (operators only; start-up continues after each)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Failed to pre-fetch models at startup: {e}` | Log (warning) | `backend/open_webui/main.py:429` | The `models.base_models_cache` setting is on and the model list could not be fetched during start-up (`:407-429`) | None | See `model-connections-openai-ollama-and-direct.md` section 10 |
| `Failed to initialize tool servers at startup: {e}` | Log (warning) | `backend/open_webui/main.py:454` | Tool-server descriptions could not be fetched at start-up | None | See `workspace-tools-tool-servers-mcp-and-terminals.md` section 10 |
| `Failed to initialize terminal servers at startup: {e}` | Log (warning) | `backend/open_webui/main.py:460` | As above, for terminal servers | None | As above |
| `License data retrieval is still pending; continuing startup without it` | Log (warning) | `backend/open_webui/main.py:467` | Only with `LICENSE_KEY`: the licence lookup took longer than two seconds (`:463-467`) | None | Whether a licence key is used is **TO BE CONFIRMED** |
| `License data retrieval failed during startup: {e}` | Log (warning) | `backend/open_webui/main.py:469` | As above, when the lookup raised an error | None | As above |
| `Error adding OAuth client for MCP tool server {server_id}: InvalidToken. Stored OAuth client data is invalid; reconnect this tool server.` | Log (error) | `backend/open_webui/main.py:648-652` | At start-up, an MCP tool server's stored OAuth registration could not be decrypted, for example after the secret key changed | None | The tool-server administrator reconnects it; see `sso-oauth-oidc-and-scim.md` section 10 |
| `Error adding OAuth client for MCP tool server {server_id}: {e}` | Log (error) | `backend/open_webui/main.py:654-658` | Any other failure loading that registration | None | As above |
| `Error updating models: {e}` | Log (error) | `backend/open_webui/main.py:696` | The embedding or reranking model for document search could not be set up at start-up (`:672-697`) | None | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `Version update check failed: {e}` | Log (warning) | `backend/open_webui/main.py:2612` | The check for a newer upstream release failed | None | See `notifications-webhooks-events-and-banners.md` section 10 |
| `Frontend build directory not found at '{FRONTEND_BUILD_DIR}'. Serving API only.` | Log (warning) | `backend/open_webui/main.py:3077` | The built web pages are missing (normal for the backend-only development server; not expected in the Docker image) | None | Escalate if users report a blank site after a deployment |

### 10.19 `backend/open_webui/socket/main.py` (Websocket Server)

The websocket server pushes chat progress and other live updates. It sends almost no text to people: a connection whose token is missing, unreadable, revoked or belongs to a pending account is simply not registered, with no message (`backend/open_webui/socket/main.py:421-445`, `:448-460`; `backend/open_webui/utils/auth.py:579-589`). The texts below reach a tool or plugin that asked the browser for something, a channel, or the note editor. Note-editing log lines (`backend/open_webui/socket/main.py:535-940`) are in `notes.md` section 10.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Client session disconnected.` | Error (returned to the calling tool or plugin) | `backend/open_webui/socket/main.py:1266` | Server code needed the browser (for example a direct connection, a direct tool or browser-side code execution) but the browser session it names is gone or belongs to someone else; logged as `Event caller: session {session_id} not owned by requesting user or disconnected` (`:1265`) | Keep the tab open and resend | See `chat-completion-pipeline-and-generation-tasks.md` section 10 |
| `Event call timed out. The browser tab may be inactive or closed.` | Error (as above) | `backend/open_webui/socket/main.py:1281` | The browser did not answer within `WEBSOCKET_EVENT_CALLER_TIMEOUT` seconds (`:1277`); logged as `Event caller timed out for session {session_id}` (`:1280`). With the variable unset (the default) this call has no time limit, so the text needs the variable to be set (`backend/open_webui/env.py:534-542`; `.venv/lib/python3.12/site-packages/socketio/async_server.py:281-284`) | Keep the tab in front and resend | As above |
| `Failed to join document` | Error (websocket `error` event) | `backend/open_webui/socket/main.py:732` | Joining a note for live editing failed; logged as `Error in yjs_document_join: {e}` (`:731`). The note editor does not display it | Reload the note | See `notes.md` section 10 |
| `Error: {error_content}` | Error (text of the model's reply in a channel) | `backend/open_webui/socket/main.py:1126-1129` | A model answering in a channel failed; its reply is replaced by `Error: ` and the error text, or `Error: An error occurred` when the error has no text | Retry | See `channels-and-direct-messages.md` section 10 |
| `Reaping {len(expired)} orphaned session(s) from the session pool` | Log (warning) | `backend/open_webui/socket/main.py:237` | Connections that missed their heartbeats for longer than the session time-out (at least 120 seconds, `:129`) were removed, for example after a server process stopped | None | Not explained elsewhere. Frequent repeats point at crashing server processes: escalate |
| `Unable to renew session cleanup lock. Retrying cleanup ownership.` | Log (warning) | `backend/open_webui/socket/main.py:226`, `:253` | With several server processes, this one lost the clean-up lock | None | Normal now and then with several processes |
| `Session pool cleanup failed. Retrying.` | Log (exception) | `backend/open_webui/socket/main.py:262` | The session clean-up loop hit an error | None | Not explained elsewhere. Escalate if it repeats; with `WEBSOCKET_MANAGER=redis` the session list is kept in Redis (`:133-184`), so check Redis first |
| `Unable to renew usage cleanup lock. Retrying cleanup ownership.` | Log (warning) | `backend/open_webui/socket/main.py:278` | As above, for the model-usage clean-up | None | See `evaluations-feedback-and-analytics.md` section 10 |
| `Usage pool cleanup failed. Retrying.` | Log (exception) | `backend/open_webui/socket/main.py:307` | The model-usage clean-up loop hit an error | None | As above |
| `Redis event listener stopped. Retrying.` | Log (warning) | `backend/open_webui/socket/main.py:984` | Only with `WEBSOCKET_MANAGER=redis`: the subscription to shared events ended; the server reconnects after a growing delay (`:994-995`) | None | Not explained elsewhere. Redis connectivity; events relayed between server processes through Redis (`:977-983`) are not received meanwhile |
| `Redis event listener failed. Retrying.` | Log (exception) | `backend/open_webui/socket/main.py:988` | As above, after an error | None | As above |

### 10.20 `backend/open_webui/internal/db.py` (Database Connection at Start-Up)

These run when the application is imported, before it serves anything. A `ValueError` here ends start-up with a Python traceback whose last line is `ValueError: ` followed by the text; people using the site see only that it is unavailable. Only the platform maintainer can act on them, and none is explained in another document. Whether production uses the slim image, database IAM authentication or SQLCipher is **TO BE CONFIRMED**. A `DATABASE_URL` the database library cannot read fails inside that library, with the library's own wording.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Slim requires SQLite or PostgreSQL for DATABASE_URL. Use the standard image for other databases.` | Start-up failure | `backend/open_webui/internal/db.py:148` | The slim image (`USE_SLIM_DOCKER=true`, `backend/open_webui/env.py:45`) with a `DATABASE_URL` that is neither SQLite nor PostgreSQL (`:146-150`) | None | Escalate (deployment) |
| `AWS RDS IAM authentication requires the standard image. Slim supports PostgreSQL database credentials.` | Start-up failure | `backend/open_webui/internal/db.py:152` | The slim image with `DATABASE_ENABLE_IAM_TOKEN_AUTH=true` (`backend/open_webui/env.py:304`) | None | Escalate (deployment) |
| `DATABASE_ENABLE_IAM_TOKEN_AUTH is only supported for PostgreSQL databases` | Start-up failure | `backend/open_webui/internal/db.py:171` (created at `:205`) | Database IAM sign-in switched on with a URL that is not PostgreSQL | None | Escalate (deployment) |
| `DATABASE_ENABLE_IAM_TOKEN_AUTH requires a database host and user` | Start-up failure | `backend/open_webui/internal/db.py:173` | Database IAM sign-in switched on with a URL that has no host or no user name | None | Escalate (deployment) |
| `DATABASE_PASSWORD is required when using sqlite+sqlcipher:// URLs` | Start-up failure | `backend/open_webui/internal/db.py:292` | An encrypted-SQLite (SQLCipher) URL without the `DATABASE_PASSWORD` variable (`:289-292`) | None | Escalate (deployment) |
| `sqlite+sqlcipher:// URLs are not supported with async engine. Use standard sqlite:// or postgresql:// instead.` | Start-up failure | `backend/open_webui/internal/db.py:245`, raised from `:447` | Any SQLCipher URL that passed the password check: SQLCipher is not usable in v0.11.4 (ground truth) | None | Escalate (deployment) |
| `AWS RDS IAM token auth not applied to {url}: the token is issued for {auth.username}@{auth.host}:{auth.port}, so this connection uses the password from its own URL` | Log (warning) | `backend/open_webui/internal/db.py:222-229` | With database IAM sign-in on, a second connection (for example the pgvector store, `backend/open_webui/retrieval/vector/dbs/pgvector.py:110`) points at a different host, port or user, so it keeps its own credentials | None | Informational; escalate if that store cannot connect |

### 10.21 `backend/open_webui/env.py` (Environment Settings Read at Start-Up)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `WEBUI_SECRET_KEY is not set. It is a hard requirement when authentication is enabled.` (first line; full text below) | Start-up failure (the process exits) | `backend/open_webui/env.py:781` | `WEBUI_AUTH` is on (the default, `:751`) and neither `WEBUI_SECRET_KEY` nor the older `WEBUI_JWT_SECRET_KEY` is set (`:762-765`, `:780`). `backend/start.sh` generates a key when none is set; `backend/dev.sh` does not (`CLAUDE.md`) | None | Escalate: the start method or the secret store did not provide the key. Never ask anyone for the key's value. See `authentication-and-sign-in.md` section 10 |
| `CUDA unavailable (USE_CUDA_DOCKER=true), falling back to CPU: {exc}` | Log (error) | Built at `backend/open_webui/env.py:59`, logged at `:129-131` | The CUDA image found no usable GPU (the inner `CUDA not available` at `:56` is the usual `{exc}`); the server continues on the CPU (`:58-61`) | None | Not explained elsewhere. Escalate if a GPU was expected |
| `Invalid WEBSOCKET_REDIS_OPTIONS, defaulting to socket_timeout=None` | Log (warning) | `backend/open_webui/env.py:490` | `WEBSOCKET_REDIS_OPTIONS` is not valid JSON; the default options are used (`:486-491`) | None | Not explained elsewhere. Deployment configuration |
| `SSL CA bundle path does not exist: {path}, ignoring` | Log (warning) | `backend/open_webui/env.py:564-567` | `AIOHTTP_CLIENT_SSL_CERT_FILE` names a file that does not exist; outgoing connections then use the default certificate checks (`:575`, `:593`, `:601`) | None | Not explained elsewhere. Escalate if calls to services with a private certificate authority start failing |
| `Invalid PASSWORD_VALIDATION_REGEX_PATTERN: {e}` | Log (error) | `backend/open_webui/env.py:826` | The password-rule pattern is not a valid regular expression; the built-in pattern is used instead (`:822-827`) | None | See `authentication-and-sign-in.md` section 10 |
| `SCIM is enabled but SCIM_AUTH_PROVIDER is not set. Set SCIM_AUTH_PROVIDER to the OAuth provider name (e.g. 'microsoft', 'oidc') to enable externalId storage.` | Log (warning) | `backend/open_webui/env.py:912-916` | `ENABLE_SCIM` on without `SCIM_AUTH_PROVIDER`; external-id writes then fail with the HTTP 500 in section 10.5 | None | See `sso-oauth-oidc-and-scim.md` section 10 |
| `dotenv not installed, skipping...` | Printed at start-up | `backend/open_webui/env.py:42` | The `python-dotenv` package is missing, so the repository-root `.env` file is not read (`:38-42`) | None | Not explained elsewhere. Deployment |

The full secret-key message (`backend/open_webui/env.py:781-788`) reads:

```text
WEBUI_SECRET_KEY is not set. It is a hard requirement when authentication is enabled.
The supported start methods set or auto-generate it for you: use start.sh (Linux/macOS), start_windows.bat (Windows), or `open-webui serve`.
If you start the backend another way (e.g. invoking uvicorn directly, which is unsupported), you must set WEBUI_SECRET_KEY yourself to a long random value.
See https://docs.openwebui.com/reference/env-configuration#webui_secret_key
```

### 10.22 `backend/open_webui/config.py` (Migrations and Configuration Read at Start-Up)

Like section 10.20, an error raised here stops start-up with a traceback (a `ValueError`, or a plain `Exception` for the code-challenge check). Several checks run whatever vector store is chosen, so a stray variable can stop a server that does not use that store (noted per row).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Error running migrations: {e}` | Log (exception), then start-up failure | `backend/open_webui/config.py:77-78`, run at import when `ENABLE_DB_MIGRATIONS` is on (`:81-82`; `backend/open_webui/env.py:157`) | A database migration failed; the error is raised again, so start-up stops | None | Escalate at once with the full traceback. The migration history is in `database-schema-identity-chats-and-config.md` (**TO BE CONFIRMED** whether written yet) |
| `Pgvector requires setting PGVECTOR_DB_URL or using Postgres with vector extension as the primary database.` | Start-up failure | `backend/open_webui/config.py:650` | `VECTOR_DB=pgvector` in the standard image with neither `PGVECTOR_DB_URL` nor a PostgreSQL `DATABASE_URL` (`:648-652`) | None | See `rag-retrieval-embeddings-and-vector-stores.md` section 10 |
| `PGVECTOR_INITIALIZE_MAX_VECTOR_LENGTH is set to {PGVECTOR_INITIALIZE_MAX_VECTOR_LENGTH}, which exceeds the 2000 dimension limit of the 'vector' type. Set PGVECTOR_USE_HALFVEC=true to enable the 'halfvec' type required for high-dimensional embeddings.` | Start-up failure | `backend/open_webui/config.py:658` | That variable above 2,000 without `PGVECTOR_USE_HALFVEC=true`; checked whatever `VECTOR_DB` is (`:653-663`) | None | Not explained elsewhere. Escalate (deployment) |
| `PGVECTOR_PGCRYPTO is enabled but PGVECTOR_PGCRYPTO_KEY is not set. Please provide a valid key.` | Start-up failure | `backend/open_webui/config.py:669` | `PGVECTOR_PGCRYPTO=true` without its key; checked whatever `VECTOR_DB` is (`:666-669`) | None | Not explained elsewhere. Escalate (deployment) |
| `Oracle23ai requires setting ORACLE_DB_USER, ORACLE_DB_PASSWORD, and ORACLE_DB_DSN.` | Start-up failure | `backend/open_webui/config.py:816` | `VECTOR_DB=oracle23ai` in the standard image with one of those variables missing (`:814-816`) | None | Not explained elsewhere. Escalate (deployment) |
| `Oracle23ai requires setting ORACLE_WALLET_DIR and ORACLE_WALLET_PASSWORD when using wallet authentication.` | Start-up failure | `backend/open_webui/config.py:818` | Oracle wallet sign-in on without the wallet folder or its password (`:817-820`) | None | As above |
| `EXA_MAX_CONTENT_LENGTH must be a positive integer or unset` | Start-up failure | `backend/open_webui/config.py:1281` | `EXA_MAX_CONTENT_LENGTH` is zero or negative; a value that is not a number fails one line earlier with Python's own conversion error (`:1279`) | None | Not explained elsewhere. Escalate (deployment) |
| `EVALUATION_ARENA_MODELS must be a JSON list of objects` | Log only (caught at once) | `backend/open_webui/config.py:2060`, logged as `Error loading EVALUATION_ARENA_MODELS: {e}` at `:2062` | The variable is JSON but not a list of objects; start-up continues with no environment-defined arena models (`:2063`) | None | See `evaluations-feedback-and-analytics.md` section 10 |
| `THREAD_POOL_SIZE is not a valid integer: {THREAD_POOL_SIZE}. Defaulting to None.` | Log (warning) | `backend/open_webui/config.py:2110` | `THREAD_POOL_SIZE` is not a whole number; the default thread pool is used | None | Not explained elsewhere. Deployment |
| `Invalid scheme in CORS_ALLOW_ORIGIN: '{origin}'. Only 'http' and 'https' and CORS_ALLOW_CUSTOM_SCHEME are allowed.` | Start-up failure | `backend/open_webui/config.py:2120`, checked for each origin at `:2146-2147` | An entry in `CORS_ALLOW_ORIGIN` (semicolon-separated, `:2134`) whose scheme is not `http`, `https` or one listed in `CORS_ALLOW_CUSTOM_SCHEME` | None | Not explained elsewhere. Escalate (deployment) |
| `Invalid URL structure in CORS_ALLOW_ORIGIN: '{origin}'.` | Start-up failure | `backend/open_webui/config.py:2126` | An entry in `CORS_ALLOW_ORIGIN` without a host part | None | As above |
| `WARNING: CORS_ALLOW_ORIGIN IS SET TO '*' - NOT RECOMMENDED FOR PRODUCTION DEPLOYMENTS.` | Log (warning) | `backend/open_webui/config.py:2141-2142` | `CORS_ALLOW_ORIGIN` left at its default `*` | None | Not explained elsewhere. Whether production sets it is **TO BE CONFIRMED**; the setting is the platform maintainer's decision |
| `⚠️  SECURITY WARNING: JWT_EXPIRES_IN is set to '-1'` | Log (warning) | `backend/open_webui/config.py:2468-2472` | The token-lifetime variable is `-1` | None | Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca); see `authentication-and-sign-in.md` section 10 |
| `Code challenge methods other than "%s" not supported. Given: "%s"` | Start-up failure | `backend/open_webui/config.py:2646-2648`, evaluated when the single sign-on providers are registered at start-up (`backend/open_webui/main.py:524`; `backend/open_webui/utils/oauth.py:1337-1343`) | `OAUTH_CODE_CHALLENGE_METHOD` set to anything other than `S256`; the printed text has `S256` in the first `%s` and the configured value in the second | None | See `sso-oauth-oidc-and-scim.md` section 10 |

Other configuration warnings in this file are explained where their setting is: the Ollama and OpenAI connection lists (`backend/open_webui/config.py:310-312`, `:357-359`; `model-connections-openai-ollama-and-direct.md` section 10), the OAuth authorize parameters and the missing-logout warning (`:2511-2513`, `:2631-2633`, `:2771-2779`; `sso-oauth-oidc-and-scim.md` section 10), prompt suggestions (`:1682`; `prompts-and-skills.md`), banners (`:2164`; `notifications-webhooks-events-and-banners.md`) and interface defaults (`:1715`; `user-settings-and-personalisation.md`). Five logged loading errors are not explained elsewhere: `Error loading TOOL_SERVER_CONNECTIONS: {e}` (`:384`), `Error loading MODEL_ORDER_LIST: {e}` (`:1690`), `Error loading DEFAULT_MODEL_METADATA: {e}` (`:1698`), `Error loading DEFAULT_MODEL_PARAMS: {e}` (`:1706`) and `Error loading TASK_MODEL_PARAMS: {e}` (`:2187`); each means that environment variable is not valid JSON, and start-up continues with an empty value.

### 10.23 Every Member of `constants.py`

The table of every member of `ERROR_MESSAGES`, `MESSAGES`, `WEBHOOK_MESSAGES` and `TASKS`, with its text and the files that use it, is section 4.6. *Checked 2026-10-10:* a fresh count of every reference outside `backend/open_webui/constants.py` (`grep -rnoE` over `backend/open_webui`) matched all 73 rows of that table, with no member missing.

## 11. Common Tier-1 Issues and Troubleshooting

These are triage patterns for the texts tickets quote most often. Each points to the subsystem document that covers the deeper cases. Tier 1 is read-only (section 3.3): the resolution is guidance or an escalation. For every escalation, send the exact text (a screenshot is best), the date and time to the minute, the person's email (in the ticket only, never in this knowledgebase), the page address without the site name (for example `/c/<chat id>`), what they clicked, and whether colleagues are affected. Server texts appear in English whatever the interface language: no component passes them through translation (a search of `src/` for translation calls on error values found none).

### 11.1 "It says the email or password is incorrect"

**Symptom.** The sign-in page shows `The email or password provided is incorrect. Please check for typos and try logging in again.`, after typing a password or after choosing single sign-on.

**Likely causes, in order.**
1. A mistyped email or password on the password form (`backend/open_webui/routers/auths.py:833`).
2. The account has no usable local password, because single sign-on, LDAP or SCIM created it, and the person used the password form (section 10.2).
3. Single sign-on: the code exchange failed, the provider sent no user details, subject or email, or the email domain is not in **Allowed Domains**. All of these show this password text although no password was typed (`backend/open_webui/utils/oauth.py:1911-2008`; ground truth).
4. Not a lockout: apart from the rate limit there is no failed-sign-in counter (ground truth). After 15 attempts in a few minutes the text changes to `API rate limit exceeded` (section 11.5).

**Diagnostic steps** (read-only).
1. Ask whether they used the email and password boxes or a single sign-on button, and when.
2. Ask them to type the email by hand: the server lower-cases it, so letter case does not matter (`backend/open_webui/routers/auths.py:818-825`), but spaces and old addresses do.
3. For single sign-on, ask whether colleagues with the same email domain can sign in today. Many failures at once point to the provider or its configuration.
4. Ask an administrator to confirm, read-only, that an account with this email exists (**Admin Panel → Users**).

**Resolution.** Retype carefully; single sign-on users use the single sign-on button, not the password boxes. Password resets and account changes are administrator actions, not tier 1.

**Escalation.** The standard details above, plus which method was used and the provider's name. The maintainer matches the time against the log lines listed in `sso-oauth-oidc-and-scim.md` section 10.3 (single sign-on) or `authentication-and-sign-in.md` section 10.3 (password and LDAP). Deeper cases: `authentication-and-sign-in.md` sections 11.1 and 11.24; `sso-oauth-oidc-and-scim.md` section 11.1.

### 11.2 "Everything I click says I don't have permission"

**Symptom.** `You do not have permission to access this resource. Please contact your administrator for assistance.` With HTTP 401 it comes from a role check; with HTTP 403 from a specific rule (section 3.1).

**Likely causes, in order.**
1. The account is `pending`: a new account waiting for activation, or one an administrator suspended by setting it to pending (ground truth). Every signed-in endpoint refuses it with HTTP 401 (`backend/open_webui/utils/auth.py:570-576`); the person normally sees the **Account Activation Pending** screen instead of toasts.
2. A non-admin reached an admin page or kept an admin tab open after their role changed (`backend/open_webui/utils/auth.py:625-631`).
3. HTTP 403 cases: a program's API key used on a path outside **Allowed Endpoints** (`backend/open_webui/utils/auth.py:541-550`); sign-up while sign-up is off (`backend/open_webui/routers/auths.py:908-917`); single sign-on with no account and OAuth sign-up off, or roles that match no allowed role (`backend/open_webui/utils/oauth.py:2149`, `:1605`); personal webhooks without the permission (`backend/open_webui/routers/notifications.py:41`); and many content checks in the companion catalogue.

**Diagnostic steps** (read-only).
1. Ask whether every action fails or only one, and what it was.
2. Ask an administrator to check the account's role (**Admin Panel → Users**): `pending`, `user` or `admin`.
3. For a program, ask which address it called and whether it uses an API key.

**Resolution.** A pending account waits for an administrator to activate it; tier 1 does not change roles. For a single feature, the person asks an administrator whether their group should have it.

**Escalation.** The standard details, the role seen, and the HTTP status (401 or 403) when a program reports it. Deeper cases: `authentication-and-sign-in.md` sections 11.3 and 11.18; `users-groups-roles-and-permissions.md` sections 11.1 and 11.2.

### 11.3 "It says my session has expired or the token is invalid"

**Symptom.** `Your session has expired or the token is invalid. Please sign in again.` (HTTP 401).

**Likely causes, in order.**
1. The account behind the sign-in token no longer exists: it was deleted (deletion is permanent, ground truth), or deleted and created again, which gives it a new identity (`backend/open_webui/utils/auth.py:455-460`).
2. A program used an API key that matches no account, for example a deleted or replaced key (`backend/open_webui/utils/auth.py:509-517`).
3. The sign-in page's own session check found the token's expiry time already passed (`backend/open_webui/routers/auths.py:274`).

**Diagnostic steps** (read-only).
1. Ask whether it appears straight after signing in (points to cause 1) or from a script (cause 2).
2. Ask an administrator whether the account exists and whether it was recently deleted or recreated.

**Resolution.** Sign out and sign in again; a program needs its current key. If the account was deleted, the person needs a new account from an administrator.

**Escalation.** The standard details, and for a program the time of the first failure and whether the key was recently replaced. Deeper cases: `authentication-and-sign-in.md` section 11.7.

### 11.4 "I see '401 Unauthorized'"

**Symptom.** `401 Unauthorized`, or `Invalid token`, usually on opening the site or on the first action of the day.

**Likely causes, in order.**
1. The sign-in token expired (lifetime setting `auth.jwt_expiry`, code default four weeks; ground truth).
2. The server's secret key changed, so no existing token can be read: everyone is affected at once, for example after a container was recreated without a fixed `WEBUI_SECRET_KEY` (`CLAUDE.md`; `backend/open_webui/utils/auth.py:246-251`, `:489-493`).
3. `Invalid token` instead: the token was revoked, which needs Redis, after a sign-out with that token, a password change or reset, or an identity-provider logout (`backend/open_webui/utils/auth.py:449-453`).
4. On notes, channels, automations, the calendar or a workspace item (a model, prompt, skill, tool or knowledge base), `401 Unauthorized` is instead a permission refusal: the person lacks the permission for that feature or kind of item, or write access to that item (for example `backend/open_webui/routers/models.py:293-298`, `:1130-1138`; the content-router uses in section 4.6; companion catalogue).

**Diagnostic steps** (read-only).
1. Ask whether colleagues saw it at the same time; many at once points to cause 2.
2. Ask what they were doing: opening the site (causes 1 to 3) or saving a shared item (cause 4).
3. Ask whether they changed their password or signed out elsewhere just before (cause 3).

**Resolution.** Sign in again. For a shared item, the owner can grant write access.

**Escalation.** Many people at once: escalate at once with the times and a count; the maintainer checks whether the secret key changed. Never ask anyone for the key's value. Deeper cases: `authentication-and-sign-in.md` sections 11.8 and 11.9.

### 11.5 "It says 'API rate limit exceeded' when I sign in"

**Symptom.** The sign-in page shows `API rate limit exceeded` (HTTP 429).

**Likely causes, in order.**
1. More than 15 sign-in attempts for the same email within about three to four minutes, successful ones included (section 10.16).
2. A password manager, browser extension or script retrying in a loop; every attempt counts, including refused ones, so retrying keeps the block going.
3. Several people sharing one account email, whose attempts all count together.
4. For programs only: the optional token-exchange limit (`backend/open_webui/routers/auths.py:94-101`).

**Diagnostic steps** (read-only).
1. Ask how many attempts were made and whether anything signs in automatically.
2. Ask whether the person made all the attempts themselves.

**Resolution.** Stop for at least four minutes without trying, then sign in once, carefully. Without Redis each server process counts separately, so behaviour can differ between attempts (ground truth).

**Escalation.** If it continues after a ten-minute pause, the standard details and the times of the attempts. If the person says they did not make the attempts, treat it as a suspected security incident: stop and refer to U of T Information Security (security.utoronto.ca) rather than troubleshooting further. Deeper cases: `authentication-and-sign-in.md` section 11.2.

### 11.6 "My chat says 'Model not found'"

**Symptom.** `Model not found` as a pop-up and in the reply's error box; or `Model '' was not found`, often in a grey box under an answer that is complete.

**Likely causes, in order.**
1. The model is not in the server's model list: removed, renamed, or its connection is not answering (`backend/open_webui/main.py:1128-1129`).
2. The person has no access to the model: the access check gives the same text (`backend/open_webui/utils/models.py:465-491`).
3. A workspace model whose base model is missing, with no fallback configured (`backend/open_webui/main.py:1180-1182`; `ENABLE_CUSTOM_MODEL_FALLBACK`, code default off, `backend/open_webui/env.py:1033`).
4. `Model '' was not found`: a background task such as the title, tags or follow-up suggestions could not find the model; the empty quotes are a quirk of the code, not a lost name (sections 4.3 and 10.12).

**Diagnostic steps** (read-only).
1. Ask for the model name shown at the top of the chat and the chat address.
2. Ask whether a new chat with the same model works, and whether colleagues can see that model.
3. For the grey box under a complete answer, confirm that the answer itself is complete.

**Resolution.** Choose another available model, or start a new chat. An answer shown above a `Model '' was not found` box is complete.

**Escalation.** The standard details plus the model name. Deeper cases: `chat-completion-pipeline-and-generation-tasks.md` sections 11.1 and 11.20; `workspace-models-and-model-access.md` section 11.2; `users-groups-roles-and-permissions.md` section 11.10; `model-connections-openai-ollama-and-direct.md` section 11.3.

### 11.7 "It just says 'Something went wrong :/'"

**Symptom.** `Something went wrong :/` with no other detail. It is the generic output of the `DEFAULT` formatter when the code gives it nothing, or only an exception (section 4.2), and many endpoints use it (section 4.6 lists the files).

**Likely causes, in order (in this catalogue's scope).**
1. Posting into a chat the person does not own (HTTP 404, `backend/open_webui/main.py:1494-1499`), or a model reply in a channel they cannot write to (HTTP 403, `:1319-1350`).
2. A rating that could not be stored (`backend/open_webui/routers/evaluations.py:434`).
3. A profile save that found no account (`backend/open_webui/routers/auths.py:342`), or an admin edit whose user could not be re-read (`backend/open_webui/routers/users.py:1026`).
4. Outside this scope: chats, folders, channels, notes, files and other content routers (companion catalogue).

**Diagnostic steps** (read-only).
1. Ask exactly what they clicked, on which page, and the time; the text alone does not identify the cause.
2. Ask whether it happens again on a second try and in a new chat.

**Resolution.** Reload the page and retry once; for a chat, start a new chat of their own.

**Escalation.** The standard details. The maintainer matches the time with the server log, which records the reason for some of these paths (for example a rating that could not be stored, `evaluations-feedback-and-analytics.md` section 10).

### 11.8 "I got a message that starts with '[ERROR:'"

**Symptom.** A text such as `[ERROR: Error creating group]` or `[ERROR: Error updating function]`.

**Meaning.** The words after `ERROR:` name the operation that failed, not why (section 4.2). The reason, when the code records it, is in the server log at the same minute, for example `Error creating a new group: {e}` (`backend/open_webui/routers/groups.py:89`).

**Likely causes, in order.**
1. For functions and tools: the code just saved does not load, or one of its packages failed to install (section 10.9).
2. A database problem while saving (groups, section 10.4; functions, section 10.9).
3. A storage problem on the server: `[ERROR: The server is out of storage space.]`, `[ERROR: Server storage quota exceeded.]`, `[ERROR: Server storage is not writable.]` or `[ERROR: File name is too long.]` (`backend/open_webui/constants.py:6-13`, `:19-20`).

**Diagnostic steps** (read-only).
1. Get the whole bracketed text and the time.
2. Ask whether the person had just changed the code of a function or tool.

**Resolution.** Retry once. Code problems are fixed by whoever wrote the function or tool.

**Escalation.** The standard details. Escalate the storage texts at once: they mean the server's disk is full or not writable, which is likely to affect everyone.

## 12. Local Customisations

Checked read-only with `git diff main...uoft` over every file in scope (`backend/open_webui/constants.py`, the twelve routers, the four helpers, `main.py`, `socket/main.py`, `internal/db.py`, `env.py` and `config.py`) and `git diff --` for the working tree.

| What | Fork change | Effect on messages | Evidence |
|---|---|---|---|
| `backend/open_webui/env.py` | The default `WEBUI_NAME` is `MedIT GPT`, and the upstream rule that appended " (Open WebUI)" to any other name is removed | No message text in scope changes. The name reaches people through the site title and, in scope, the personal test notification: the notifications router passes the application name (`backend/open_webui/routers/notifications.py:97-101`; set at `backend/open_webui/main.py:538`) to a test text the fork changed to `This is a test notification from {app_name}.` (`backend/open_webui/utils/notifications.py:360`) | `backend/open_webui/env.py:951` |
| Every other file in scope | None | The texts match upstream v0.11.4 | `git diff main...uoft` lists only `env.py` among these files |
| Working tree | No uncommitted change in any backend file | None. The uncommitted front-end changes (chat rendering and the language loader, `src/lib/i18n/index.ts`) do not touch how server texts are printed | `git diff -- backend/` is empty; `git diff -- src/` |

"Open WebUI" therefore still appears in some texts that MedIT GPT users or administrators can see:

| Text | Where | Evidence |
|---|---|---|
| `Open WebUI: Server Connection Error` | Model-provider connection failures (section 4.5); licence-protected | `backend/open_webui/constants.py:127-130` |
| `... so Open WebUI can resolve where to send users to authorize.` | End of the tool-server discovery error, seen by administrators inside `Failed to register OAuth client: {e}` (sections 10.6, 10.15) | `backend/open_webui/utils/oauth.py:578-583` |
| A `docs.openwebui.com` link | The secret-key start-up message (section 10.21), seen by operators | `backend/open_webui/env.py:787` |
| The page title `Open WebUI` | The API documentation at `/docs`, only when `ENV=dev` | `backend/open_webui/main.py:506-510` |

## 13. Source File Index

| File | What this catalogue takes from it | Sections |
|---|---|---|
| `backend/open_webui/constants.py` | Every shared text, the `DEFAULT` formatter and the storage-error texts | 4.2, 4.3, 4.5, 4.6, 10 |
| `backend/open_webui/routers/auths.py` | Sign-in, sign-up, profile, API key, LDAP and token-exchange texts; the sign-in limiter | 10.2, 10.16, 11.1, 11.5 |
| `backend/open_webui/routers/users.py` | User administration texts | 10.3, 11.7 |
| `backend/open_webui/routers/groups.py` | Group texts | 10.4, 11.8 |
| `backend/open_webui/routers/scim.py` | SCIM texts | 10.5 |
| `backend/open_webui/routers/configs.py` | Tool-server, terminal-server and OAuth client registration texts | 10.6 |
| `backend/open_webui/routers/utils.py` | Code formatting, code execution and database download | 10.7 |
| `backend/open_webui/routers/pipelines.py` | Pipelines management and filter texts | 10.8 |
| `backend/open_webui/routers/functions.py` | Function texts | 10.9 |
| `backend/open_webui/routers/analytics.py` | Admin analytics guards (no texts of its own) | 10.10 |
| `backend/open_webui/routers/evaluations.py` | Rating texts and leaderboard log lines | 10.11, 11.7 |
| `backend/open_webui/routers/tasks.py` | Generation-task texts | 4.3, 10.12 |
| `backend/open_webui/routers/notifications.py` | Personal notification texts | 10.13, 12 |
| `backend/open_webui/utils/auth.py` | Token, API key, role and password checks | 3.1, 10.14, 11.2, 11.3, 11.4 |
| `backend/open_webui/utils/oauth.py` | Single sign-on, tool-server sign-in and back-channel logout texts | 2.1, 10.15, 11.1 |
| `backend/open_webui/utils/rate_limit.py` | The rolling-window counter | 10.16, 11.5 |
| `backend/open_webui/utils/plugin.py` | Function and tool loading texts | 10.17 |
| `backend/open_webui/main.py` | Chat, unload, webhook, readiness and start-up texts; the only custom error handler; unmatched addresses | 2.1, 4.1, 10.10, 10.18, 11.6, 11.7 |
| `backend/open_webui/socket/main.py` | Websocket texts and background-loop log lines | 10.19 |
| `backend/open_webui/internal/db.py` | Database start-up failures | 10.20 |
| `backend/open_webui/env.py` | Environment start-up checks; the fork's default name | 7, 10.21, 12 |
| `backend/open_webui/config.py` | Migrations and configuration start-up checks | 7, 10.22 |
| `backend/open_webui/utils/notifications.py` | The rule texts behind personal notification refusals; the fork's test text | 10.13, 12 |
| `backend/open_webui/utils/chat_variables.py` | Personal variable texts | 10.3 |
| `backend/open_webui/utils/recurrence.py` | The schedule time-out text | 10.18 |
| `backend/open_webui/utils/misc.py` | How a provider's error answer becomes text | 10.18 |
| `backend/open_webui/utils/models.py` | The model access check | 10.18, 11.6 |
| `backend/open_webui/utils/middleware.py`, `backend/open_webui/utils/chat.py` | Where Pipelines and query-generation errors are absorbed | 10.8, 10.12 |
| `backend/open_webui/routers/tools.py`, `backend/open_webui/routers/models.py`, `backend/open_webui/routers/openai.py` | Callers that show why some texts cannot occur, and the content-router permission refusals | 4.3, 4.6, 10.17, 11.4 |
| `backend/open_webui/tasks.py`, `backend/open_webui/events.py`, `backend/open_webui/retrieval/vector/dbs/pgvector.py`, `backend/open_webui/utils/automations.py` | Task stop answers, event names and webhook rules, the pgvector connection, background loops | 4.6, 8, 10.18, 10.20 |
| `src/lib/apis/auths/index.ts`, `src/routes/auth/+page.svelte`, `src/routes/(app)/+page.svelte` | How a server `detail` becomes a toast, on the sign-in and home pages | 2.1, 10.15 |
| `src/lib/components/AddToolServerModal.svelte`, `src/lib/components/AddTerminalServerModal.svelte` | The dialogs' own error toasts | 10.6 |
| `src/lib/components/common/CodeEditor.svelte`, `src/lib/components/admin/Functions/FunctionEditor.svelte`, `src/lib/components/workspace/Tools/ToolkitEditor.svelte`, `src/lib/components/chat/Messages/CodeBlock.svelte`, `src/lib/components/admin/Settings/Database.svelte` | Formatting, code execution and database download toasts | 10.7 |
| `src/lib/components/chat/Chat.svelte`, `src/lib/components/chat/MessageInput/CallOverlay.svelte`, `src/lib/components/chat/ModelSelector/Selector.svelte`, `src/lib/components/layout/Sidebar/UserMenu.svelte`, `src/lib/components/chat/Settings/Account.svelte`, `src/routes/(app)/admin/analytics/+page.svelte` | Where task, unload, usage, variable and analytics answers end up | 2.1, 10.3, 10.10, 10.12, 10.18 |
| `.venv/lib/python3.12/site-packages/fastapi/exception_handlers.py`, `.venv/lib/python3.12/site-packages/starlette/exceptions.py`, `.venv/lib/python3.12/site-packages/starlette/staticfiles.py` | The framework's error bodies, default texts and unmatched-address behaviour (installed library) | 4.1, 4.3, 4.4, 10.10, 10.18 |
| `.venv/lib/python3.12/site-packages/black/parsing.py`, `.venv/lib/python3.12/site-packages/aiohttp/client_reqrep.py`, `.venv/lib/python3.12/site-packages/socketio/async_server.py` | Formatter wording, HTTP reason phrases and the event-call time limit (installed libraries) | 10.7, 10.8, 10.19 |
| `CLAUDE.md`, `knowledgebase/tools/ground-truth.md`, `knowledgebase/tools/inventory.md` | Verified project facts used without re-deriving them | throughout |

## 14. Open Questions

### 14.1 Documents Referred to That Do Not Exist Yet

As of 2026-10-10 these planned documents (`knowledgebase/reference/_areas.md`) are not in `knowledgebase/reference/`, so pointers to them are provisional: `error-messages-frontend-admin-workspace-and-settings.md` and `in-chat-status-and-response-messages.md` (section 1), `database-schema-identity-chats-and-config.md` (sections 6 and 10.22), `background-processes-and-scheduling.md` (section 8) and `websockets-realtime-and-redis.md`. The companion `error-messages-backend-chat-content-and-features.md` stops inside its section 10 (last subsection 10.27, no sections 11 to 14), so pointers to it are to section 10 only.

### 14.2 Texts That Cannot Be Shown, Read From Code

If a ticket quotes one of these, it did not come from the code path listed; ask where it appeared. A function or tool stored in the database runs arbitrary Python and could raise any text, so whether an installed plugin uses one of the unused texts is data and **TO BE CONFIRMED**.

| Text | Source | Why it cannot be shown |
|---|---|---|
| `Required environment variable not found. Terminating now.`, `Uh-oh! This email does not match the email your provider is registered with. Please check your email and try again.`, `Uh-oh! This username is already registered. Please choose another username.`, `Uh-oh! This name tag is already registered. Please choose another name tag string.`, `FILE_NOT_SENT`, `Unusual activities detected, please try again in a few minutes.` | `backend/open_webui/constants.py:42`, `:45`, `:47`, `:56`, `:75`, `:83` | No backend code uses these members (section 4.3) |
| `The model '{model}' has been added successfully.`, `The model '{model}' has been deleted successfully.`, `New user signed up: {username}` | `backend/open_webui/constants.py:27-34` | The `MESSAGES` and `WEBHOOK_MESSAGES` classes are not read anywhere (section 4.6) |
| `OpenAI API was not found` | `backend/open_webui/routers/openai.py:673` | The function is passed uncalled, so that response cannot carry the text (section 4.3) |
| `Invalid token` | `backend/open_webui/utils/auth.py:443`; `backend/open_webui/main.py:2243` | The token reader never raises (`backend/open_webui/utils/auth.py:246-251`); the same text from `:450` is reachable |
| `Toolkit not found: {tool_id}` | `backend/open_webui/utils/plugin.py:214` | No caller loads a tool without its code (section 10.17) |
| `Tool not found: {tool_id}` | `backend/open_webui/utils/plugin.py:349` | Only in a race: the tool routes check that the tool exists first (section 10.17) |
| `Dynamic client registration failed` | `backend/open_webui/utils/oauth.py:641` | The block before it always returns or raises (`:599-640`). `sso-oauth-oidc-and-scim.md` section 10 describes it as "Registration ended without an answer"; the two documents disagree and the maintainer should settle it |
| `Please enter a valid URL` (from the server) | `backend/open_webui/routers/functions.py:115` | The request model refuses an empty address first; the same words do appear from the browser's own check |
| `{e}` (stop one task) | `backend/open_webui/main.py:2134` | The function called returns a status instead of raising (section 10.18) |
| `No Redis URL provided` | `backend/open_webui/main.py:2666` | Raised and caught at once; never displayed or logged |
| `Redis PING returned False`, `EVALUATION_ARENA_MODELS must be a JSON list of objects` | `backend/open_webui/main.py:2998`; `backend/open_webui/config.py:2060` | Only ever inside a log line |
| `SCIM is not enabled` | `backend/open_webui/routers/scim.py:264` | The SCIM router is mounted only when SCIM is on (section 10.5) |
| `Event call timed out. The browser tab may be inactive or closed.` | `backend/open_webui/socket/main.py:1281` | Not while `WEBSOCKET_EVENT_CALLER_TIMEOUT` is unset, its default (section 10.19); the production value is **TO BE CONFIRMED** |
| The LDAP reasons marked *Replaced* in section 10.2 | `backend/open_webui/routers/auths.py:542-706` | People see `LDAP authentication failed.`; the reasons appear only in the log line |
| Pipelines outlet errors during chats | `backend/open_webui/routers/pipelines.py:174`, `:183` | Logged at debug level only (section 10.8) |

### 14.3 Read From Code, Not Exercised

- How a component shows an HTTP 422 validation answer, whose `detail` is a list: read as `[object Object]` from the front-end pattern (section 4.1), not confirmed in a running system.
- Unknown addresses answered with the application page or `Method Not Allowed` when the server also serves the built pages (sections 10.10 and 10.18), and the plain `Internal Server Error` from `/health/db` when the database is down.
- The rate limiter's effective window of three to four minutes is worked out from the code (section 10.16), not measured.
- The code formatter's wording (section 10.7) comes from the installed `black` package, pinned at `black==26.5.1` (`pyproject.toml:104`); the version in the production image is **TO BE CONFIRMED**.
- Whether the note editor and the channel view show the websocket texts of section 10.19 is taken from `notes.md` and `channels-and-direct-messages.md`, not re-checked here.

### 14.4 Production Facts **TO BE CONFIRMED**

- The live value of every setting named in sections 7 and 10 (live values are data, ground truth).
- Which optional parts production uses, because each decides whether a group of texts can appear: Redis (token revocation and `Invalid token`, shared rate limiting, `Redis not ready`, the websocket listener lines), PostgreSQL or SQLite (the database download), pgvector or Oracle, the slim or CUDA image, database IAM sign-in, LDAP, SCIM, single sign-on and its provider, trusted-header sign-in, OAuth token exchange, back-channel logout, a licence key (the `License:` lines), admin analytics, personal webhooks, a Pipelines server, terminal servers and MCP tool servers with OAuth.
- Where the server log goes, who may read it, and for how long (ground truth). Every escalation in section 11 relies on the maintainer reading the log at the time of the error.
- Who takes database backups when the database download is refused (section 10.7).
- Whether tier 1 has any read-only administrator view; section 11 assumes an administrator checks roles and accounts on tier 1's behalf.
- Support contacts, escalation routes and hours (ground truth).

### 14.5 Security-Sensitive Items Left Out

- One server log line in `backend/open_webui/utils/auth.py` about the token revocation check is not catalogued. Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca).
- How licence data is verified (`backend/open_webui/utils/auth.py:89-172`), and how stored OAuth client data and database credentials are handled, are not described. Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca).
- The back-channel logout texts (section 10.15) are listed without describing the checks behind them.
- The meaning of the `JWT_EXPIRES_IN` and `CORS_ALLOW_ORIGIN` warnings (section 10.22) for this deployment is a decision for the maintainer and Information Security, not tier 1.

### 14.6 Corrections and Consistency

- *Corrected 2026-10-10:* the `UNAUTHORIZED` note in section 4.6 called the content-router uses "ownership refusals"; most refuse a missing feature or workspace permission (section 11.4).
- Section 4.6 was checked against a fresh count on 2026-10-10 (section 10.23): no difference.
- No contradiction with `knowledgebase/tools/ground-truth.md` was found: the role-check 401s, the Redis-dependent revocation, the sign-in rate limit and the single sign-on password text all agree with the code read for sections 10.14 to 10.16.
- One disagreement with another reference document is open: `Dynamic client registration failed` (section 14.2).
