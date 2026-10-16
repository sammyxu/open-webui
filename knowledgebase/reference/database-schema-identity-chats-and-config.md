# Database Schema: Identity, Chats, Configuration and Migrations

## At a Glance

- MedIT GPT stores everything in one relational database: SQLite by default (`backend/data/webui.db`) or PostgreSQL. This document covers the engine and session layer, the Alembic migration chain, and the tables for identity (users, API keys, credentials, groups, access grants, OAuth sessions), configuration, chats and their messages, shared chats, folders, tags and feedback.
- Migrations run automatically when the configuration module is imported at start-up; a failed migration stops the application before it serves any page.
- Support never runs SQL against production. The read-only cookbook in section 5 is for an authorized database administrator only, and selects counts and structure, never personal columns.
- Provisional summary; refined at the end of the research.

## 1. Purpose and Who Uses It

MedIT GPT keeps all of its structured data in a single relational database. This document describes
the half of that database that holds **who people are and what they can reach** (users, API keys,
password credentials, groups, access grants, single sign-on sessions), **how the application is
configured** (the `config` table), and **conversations** (chats, chat messages, chat attachments,
shared-chat snapshots, folders, tags and feedback ratings). It also describes the plumbing that
connects the application to the database (`backend/open_webui/internal/db.py`) and the Alembic
migration chain that creates and changes every table (`backend/open_webui/migrations/`).

The sibling document `database-schema-content-and-collaboration.md` covers the other tables (files,
knowledge, models, tools, functions, prompts, skills, memories, notes, channels, messages,
automations and calendars). Between them, the two documents name all 39 tables defined in
`backend/open_webui/models/` and all 42 tables that the migrations create
(`knowledgebase/tools/inventory.md`).

| Who | What they need from this document |
|---|---|
| Tier 1 support | Plain-language answers to "where is my chat", "why did the app not start after an upgrade", "what does deleting a user remove". Tier 1 is read-only and never touches the database. |
| Tier 2 support and an authorized database administrator | The table and column reference (section 6) and the read-only SQL cookbook (section 5.6), to confirm counts and structure without reading personal content. |
| Platform maintainer | The migration chain, guard style and failure modes (sections 5.2 to 5.5 and 6.17), and the engine settings (section 7). |

Facts the rest of this document relies on, from the verified ground truth
(`knowledgebase/tools/ground-truth.md`, "Data Stores" and "Time, Storage and Logs"):

- The default database is the SQLite file `DATA_DIR/webui.db`; PostgreSQL is supported; a SQLCipher
  (encrypted SQLite) URL stops start-up in v0.11.4 (`backend/open_webui/internal/db.py:244-248`, `:447`).
- The chain has 58 revisions, is linear, and its head is `d4c1a8e37b62`.
- Timestamps in the tables of this document are epoch **seconds**, with one exception found in this
  research: `chat.timer_at` (and the timer fields inside `chat.meta`) hold **nanoseconds**
  (`backend/open_webui/models/chats.py:153`; `backend/open_webui/utils/timers.py:42-48`). The ground
  truth lists the nanosecond tables (automations, calendar, channels, messages, notes) and says
  "seconds in the others"; this column is a refinement recorded in section 14.
- Deleting a user is permanent and removes the user's chats, their messages and share snapshots,
  group memberships, the `user` row and the `auth` row (`backend/open_webui/models/users.py:849-863`;
  `backend/open_webui/models/auths.py:228-239`).
- Which database production uses is **TO BE CONFIRMED**.

## 2. Navigation and URLs

There is no screen that shows the schema, and no page or API call runs migrations: migrations run
inside the server process when it starts (section 5.2). The places where the database surfaces are:

| Where | Path | Who | What it does | Source |
|---|---|---|---|---|
| Admin Settings, **Database** tab | `/admin/settings/db` (opens `/?settings=admin:db`) | Admin | Import Config, Export Config, download the **Database** file, export **All Chats** and **Users**; see `admin-settings-panels.md` | `src/lib/components/admin/Settings/Database.svelte:56-156`; `src/lib/i18n/locales/en-US/translation.json:2183-2195` |
| Database file download | `GET /api/v1/utils/db/download` | Admin, only when `ENABLE_ADMIN_EXPORT` is on and the engine is SQLite | Returns the raw SQLite file as `webui.db` | `backend/open_webui/routers/utils.py:74-90` |
| All-chats export | `GET /api/v1/chats/all/db` | Admin, only when `ENABLE_ADMIN_EXPORT` is on | Returns every `chat` row except internal ones (`meta.internal` true, section 6.9) | `backend/open_webui/routers/chats.py:1049-1053`; `backend/open_webui/models/chats.py:1844-1849` |
| Readiness probe | `/ready` | Load balancer or monitoring | 503 `Database not ready` when a `SELECT 1` ping fails | `backend/open_webui/main.py:2968-3006` |
| Database probe | `/health/db` | Load balancer or monitoring | Runs the same ping and returns `{"status": true}` when it succeeds | `backend/open_webui/main.py:3009-3013` |

- The download and export buttons sit behind the `enable_admin_export` feature flag in the front end
  (`src/lib/components/admin/Settings/Database.svelte:123`) and `ENABLE_ADMIN_EXPORT` in the back end
  (`backend/open_webui/config.py:2082`, code default on). The downloaded file and both exports
  contain personal data (all users' chats; the users list) and must be handled as such.
- Health endpoints and their use in deployment are described in `deployment-operations-and-logging.md`.
- The production host is **TO BE CONFIRMED**; paths above are relative to the site root.

## 3. Roles and Permissions

The database has no roles of its own that MedIT GPT users see. Application roles (`admin`, `user`,
`pending`) are a column on the `user` table (section 6.1); how they are enforced is in
`users-groups-roles-and-permissions.md`.

| Action | Who can do it | Evidence |
|---|---|---|
| Create or change tables | Only the server process at start-up, by running the migration chain; no user action triggers it | `backend/open_webui/config.py:64-82` |
| Download the SQLite file, export all chats | Admins, when `ENABLE_ADMIN_EXPORT` is on (otherwise HTTP 401 with the `ACCESS_PROHIBITED` text) | `backend/open_webui/routers/utils.py:75-78`; `backend/open_webui/routers/chats.py:1050-1052` |
| Download the SQLite file on PostgreSQL | Nobody: HTTP 400 `This feature is only available with SQLite databases.` | `backend/open_webui/routers/utils.py:83-84`; `backend/open_webui/constants.py:97` |
| Read rows directly with SQL | An **authorized database administrator** only, read-only, using the cookbook in section 5.6 | support policy in `knowledgebase/reference/_research-prompt.md` rule 8 |
| Tier 1 | Never runs SQL, never opens the database file, never changes settings or data | `knowledgebase/reference/_research-prompt.md` rule 14 |

- Admin powers over other people's data (opening other users' chats, bypassing sharing) are
  environment switches described in the ground truth ("Admin visibility defaults") and in
  `chat-conversations-history-and-organisation.md`.
- Credentials for the database connection itself (`DATABASE_URL`, `DATABASE_PASSWORD`) are
  environment-only secrets; their values are never reproduced here (ground truth, "Secrets").
