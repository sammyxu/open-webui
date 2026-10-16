# Database Schema: Content, Workspace and Collaboration

## At a Glance

- *Provisional; refined at the end of the research.* This document describes, as structure only,
  the relational tables that hold user content and workspace items in MedIT GPT (Open WebUI
  v0.11.4): files, knowledge bases, custom models, tools, functions, prompts and their history,
  skills, memories, notes, channels and their messages, automations, and calendars.
- It also covers how files, knowledge bases and memories map to vector-store collections, and
  which vector rows are removed when the relational row is deleted.
- Timestamps are epoch integers whose unit differs by table (nanoseconds in the automation,
  calendar, channel, message and note models; seconds elsewhere), so check the unit before
  comparing dates.
- Deleting a user does not remove this content; it stays in the database with an owner id that no
  longer matches a user.
- The identity, chat, config and migration tables are in the sibling document
  [`database-schema-identity-chats-and-config.md`](database-schema-identity-chats-and-config.md),
  which also owns the migration-chain table and the SQL cookbook conventions.

## 1. Purpose and Who Uses It

This is the structural reference for the 24 relational tables that hold what people **make** in
MedIT GPT: uploaded files, knowledge bases and their folders, custom models, tools, functions,
prompts and prompt versions, skills, memories, notes, channels with their members, files, webhooks,
messages and reactions, automations and their run history, and calendars with events and
attendees. It also describes the vector-store side of files, knowledge bases and memories: which
collection names the code derives from row ids, and which vector data is removed when a row goes.

| Reader | What they use this document for |
|---|---|
| Tier-1 support | Understanding what a symptom means in data terms ("deleted" versus "hidden", seconds versus nanoseconds, what a user deletion leaves behind) so the escalation names the right table and identifiers |
| Tier-2 support and the platform maintainer | Column meanings, keys, cascades, which code writes and deletes rows, and the read-only SQL cookbook in section 5.6 |
| An authorized database administrator | The cookbook: counts and structure only, never personal columns or content |

What this document does **not** cover:

- The identity, chat, configuration, access-grant and migration-chain tables are in
  [`database-schema-identity-chats-and-config.md`](database-schema-identity-chats-and-config.md),
  which owns the migration-chain table and the SQL cookbook conventions. Access grants
  (`access_grant`) are referred to here only as the place where sharing for knowledge bases,
  models, tools, prompts, skills, notes, channels and calendars is stored.
- What each feature does for users is in the functional documents named in section 4.3; this
  document links to them instead of repeating their workflows.
- Support never runs SQL against production, and nothing in this document asks tier 1 to open the
  database. Tier 1 is read-only (section 3).

Every table in scope is defined in one of fourteen model files under `backend/open_webui/models/`
(`files.py`, `knowledge.py`, `models.py`, `tools.py`, `functions.py`, `prompts.py`,
`prompt_history.py`, `skills.py`, `memories.py`, `notes.py`, `channels.py`, `messages.py`,
`automations.py`, `calendar.py`). The database itself is SQLite by default or PostgreSQL
(`../tools/ground-truth.md`, Data Stores); which one production uses is **TO BE CONFIRMED**.

## 2. Navigation and URLs

There is no screen that shows these tables directly. Rows are written and read through the
interface pages and API routes below; the table each one feeds is listed so a symptom on a page can
be traced to the right subsection of section 6. Paths are relative to the site root; the production
host is **TO BE CONFIRMED**.

### 2.1 Pages and API Prefixes Per Table

| Tables | Interface pages | API prefix (router file) | Mount source |
|---|---|---|---|
| `file` | Chat composer uploads; knowledge base pages; **Settings › Data Controls › Manage Files** (personal) | `/api/v1/files` (`backend/open_webui/routers/files.py`) | `backend/open_webui/main.py:874` |
| `knowledge`, `knowledge_file`, `knowledge_directory` | `/workspace/knowledge`, `/workspace/knowledge/{id}`, `/workspace/knowledge/create` | `/api/v1/knowledge` (`routers/knowledge.py`) | `backend/open_webui/main.py:866` |
| `model` | `/workspace/models`, `/workspace/models/create`, `/workspace/models/edit`; admin model settings | `/api/v1/models` (`routers/models.py`) | `backend/open_webui/main.py:864` |
| `tool` | `/workspace/tools`, `/workspace/tools/create`, `/workspace/tools/edit` | `/api/v1/tools` (`routers/tools.py`) | `backend/open_webui/main.py:868` |
| `function` | `/admin/functions`, `/admin/functions/create`, `/admin/functions/edit` | `/api/v1/functions` (`routers/functions.py`) | `backend/open_webui/main.py:875` |
| `prompt`, `prompt_history` | `/workspace/prompts`, `/workspace/prompts/{id}`, `/workspace/prompts/create` | `/api/v1/prompts` (`routers/prompts.py`) | `backend/open_webui/main.py:867` |
| `skill` | `/workspace/skills`, `/workspace/skills/create`, `/workspace/skills/edit` | `/api/v1/skills` (`routers/skills.py`) | `backend/open_webui/main.py:869` |
| `memory` | **Settings › Personalization › Memory** | `/api/v1/memories` (`routers/memories.py`) | `backend/open_webui/main.py:871` |
| `note`, `pinned_note` | `/notes`, `/notes/{id}`, `/notes/new` | `/api/v1/notes` (`routers/notes.py`) | `backend/open_webui/main.py:861` |
| `channel`, `channel_member`, `channel_file`, `channel_webhook`, `message`, `message_reaction` | `/channels/{id}` and the sidebar's channel and direct-message lists | `/api/v1/channels` (`routers/channels.py`) | `backend/open_webui/main.py:859` |
| `automation`, `automation_run` | `/automations`, `/automations/{id}` | `/api/v1/automations` (`routers/automations.py`) | `backend/open_webui/main.py:880` |
| `calendar`, `calendar_event`, `calendar_event_attendee` | `/calendar` | `/api/v1/calendars` (plural; `routers/calendar.py`) | `backend/open_webui/main.py:881` |

Router file paths in the table are under `backend/open_webui/`. Page routes are under
`src/routes/(app)/` (`../tools/inventory.md`, Frontend pages).

### 2.2 Admin Actions That Delete Rows in Bulk

| Action (where) | Endpoint | Tables affected | Source |
|---|---|---|---|
| **Reset Vector Storage/Knowledge** (Admin › Settings › Documents) | `POST /api/v1/retrieval/reset/db` | Clears the whole vector store, then deletes every `knowledge` row and its access grants | `backend/open_webui/routers/retrieval.py:3271-3284`; `backend/open_webui/models/knowledge.py:808-820` |
| **Reset Upload Directory** (Admin › Settings › Documents) | `DELETE /api/v1/files/all` | Deletes every `file` row, every stored file and the whole vector store (see `files-uploads-and-storage.md` and `_research-notes.md`, product defect 9) | `backend/open_webui/routers/files.py:575-596`; `backend/open_webui/models/files.py:455-463` |
| Memory reset (personal **Clear memory**, see `memories.md`) | `POST /api/v1/memories/reset` and the delete-all route | `memory` rows and the person's memory collection (section 6.11) | `backend/open_webui/routers/memories.py:483` |

The admin **Database** tab (download the SQLite file, export settings, chats and users) belongs to
the sibling document and to `admin-settings-panels.md`; the raw download works only on SQLite
(`backend/open_webui/routers/utils.py:74-90`).

## 3. Roles and Permissions

- **Nobody runs SQL from inside MedIT GPT.** There is no query console. Rows change only through
  the API routes in section 2.1, each of which applies its own role and permission checks
  (documented in the functional documents listed in section 4.3).
- **Tier 1 is read-only.** Tier 1 never changes rows, settings, roles or access, and does not open
  the database. Tier 1 gathers identifiers (section 11) and escalates.
- **Database access** (a SQLite file on the server, or a PostgreSQL login) is held by whoever runs
  the platform; who that is, and whether a read-only database role exists for support, is
  **TO BE CONFIRMED**. The cookbook in section 5.6 is written for such a read-only role.
- **Ownership is a plain column.** Almost every table here has a `user_id` column naming the owner
  or author. It is not a declared foreign key to `user` in any in-scope model; only the
  `channel_member`, `channel_webhook`, `message_reaction`, `automation_run`, `calendar_event_attendee`
  and other in-scope references point at other content tables (section 6.25). Nothing in the
  database stops a `user_id` from naming a deleted user.
- **Sharing is stored outside these tables.** Read and write access for knowledge bases, models,
  tools, prompts, skills, notes, channels and calendars is a set of `access_grant` rows keyed by
  resource type and id (`backend/open_webui/models/access_grants.py`; grants are read and written
  by `AccessGrants.get_grants_by_resource`, `set_access_grants` and `revoke_all_access` in each
  model file, for example `backend/open_webui/models/knowledge.py:188-189`, `:223`, `:801`).
  Files, functions, memories, automations and messages have **no** access grants: a file is
  reachable by its owner, admins, or through a knowledge base, channel or chat that holds it (see
  `files-uploads-and-storage.md`); functions are admin-managed; memories, automations and their
  runs are private to their owner. The migration that introduced grants explicitly treated old
  file permissions as private (`backend/open_webui/migrations/versions/f1e2d3c4b5a6_add_access_grant_table.py:107-111`).
- **Admins and the bypass switches.** Whether admins see every workspace item regardless of sharing
  is governed by `BYPASS_ADMIN_ACCESS_CONTROL` and related environment settings
  (`../tools/ground-truth.md`, Accounts and Access); live values are **TO BE CONFIRMED**.

## 4. Key Concepts and Terminology

### 4.1 Terms

| Term | Meaning here | Source |
|---|---|---|
| Model file | The Python file in `backend/open_webui/models/` that pairs a SQLAlchemy table class with Pydantic models and a repository class exported as a singleton (`Files`, `Knowledges`, `Models`, `Tools`, `Functions`, `Prompts`, `PromptHistories`, `Skills`, `Memories`, `Notes`, `Channels`, `Messages`, `Automations`, `AutomationRuns`, `Calendars`, `CalendarEvents`) | `CLAUDE.md`, Backend architecture; for example `backend/open_webui/models/files.py:466`, `backend/open_webui/models/knowledge.py:1119` |
| Migration | An Alembic revision in `backend/open_webui/migrations/versions/`. Migrations, not the model files, create the tables: no runtime code calls `create_all` on the application metadata (the only `create_all` calls are for the pgvector and openGauss vector tables, which use their own metadata) | `backend/open_webui/retrieval/vector/dbs/pgvector.py:59`, `:150-153`; chain in the sibling document |
| Declared versus actual schema | The model file is what the code expects; the migration is what the database holds. They differ in places (extra indexes, nullability, the leftover `knowledge.data` column); each subsection of section 6 notes differences | section 6 |
| Epoch seconds / nanoseconds | Timestamps are integers counting from 1 January 1970 UTC. Seconds have 10 digits today (`int(time.time())`); nanoseconds have 19 (`time.time_ns()`). Divide nanoseconds by 1,000,000,000 to get seconds | `../tools/ground-truth.md`, Time, Storage and Logs |
| `JSON` column | A SQLAlchemy `JSON` column: stored as text in SQLite and as the `json` type in PostgreSQL. The code can filter inside it (for example `File.meta['data']['knowledge_id']`) | `backend/open_webui/models/files.py:27-28`, `:430-436` |
| `JSONField` column | The application's own text-backed JSON type: always stored as text (`UnicodeText`), encoded and decoded by the application | `backend/open_webui/internal/db.py:125-144` |
| Hard delete | The row is removed with SQL `DELETE`. Every in-scope table is hard-deleted by its delete routes except `channel`, which also has `archived_at` and `deleted_at` columns (section 6.14) | each model file's `delete_*` methods |
| Soft disable | A boolean that hides or switches off a row without removing it: `is_active` on `model`, `function`, `prompt`, `skill`, `automation` and `channel_member` | `backend/open_webui/models/models.py:122`; `functions.py:29`; `prompts.py:36`; `skills.py:29`; `automations.py:29`; `channels.py:107` |
| Declared cascade | A foreign key with `ON DELETE CASCADE` or `SET NULL`. PostgreSQL applies it; on SQLite the application never sets `PRAGMA foreign_keys=ON`, so the rule is not applied and child rows remain | `backend/open_webui/internal/db.py:335-399` (the pragmas the code does set); `../tools/ground-truth.md` |
| Orphan | A row whose parent or owner row no longer exists (for example a `knowledge_file` row after its knowledge base was deleted on SQLite, or a note whose owner was deleted) | sections 6 and 11 |
| Collection | A named group of vectors in the vector store. Names are derived from row ids (section 6.27) | `backend/open_webui/retrieval/vector/` |

### 4.2 Timestamp Unit Per Table

Check the unit before comparing dates across tables (`../tools/ground-truth.md`, Time, Storage
and Logs). Units below were read from the code that writes each column; the evidence is in each
table's subsection.

| Unit | Tables |
|---|---|
| Seconds | `file`, `knowledge`, `knowledge_file`, `knowledge_directory`, `model`, `tool`, `function`, `prompt`, `prompt_history`, `skill`, `memory`, `channel_file` |
| Nanoseconds | `note`, `pinned_note`, `channel`, `channel_member`, `channel_webhook`, `message`, `message_reaction`, `automation`, `automation_run`, `calendar`, `calendar_event`, `calendar_event_attendee` |

### 4.3 Functional Documents for Each Table Group

| Tables | Functional document |
|---|---|
| `file` | `files-uploads-and-storage.md` |
| `knowledge`, `knowledge_file`, `knowledge_directory` | `knowledge-bases.md` |
| vector collections | `rag-retrieval-embeddings-and-vector-stores.md` |
| `model` | `workspace-models-and-model-access.md` |
| `tool` | `workspace-tools-tool-servers-mcp-and-terminals.md` |
| `function` | `functions-pipes-filters-actions-and-pipelines.md` |
| `prompt`, `prompt_history`, `skill` | `prompts-and-skills.md` |
| `memory` | `memories.md` |
| `note`, `pinned_note` | `notes.md` |
| `channel`, `channel_member`, `channel_file`, `channel_webhook`, `message`, `message_reaction` | `channels-and-direct-messages.md` |
| `automation`, `automation_run`, `calendar`, `calendar_event`, `calendar_event_attendee` | `automations-calendar-and-timers.md` |

## 5. Workflows (Step by Step)

*Written after section 6; see below.*

## 6. Data Model

### How to Read the Table Subsections

Each table has one subsection with the same layout as the sibling document:

- **Columns.** Type as the model declares it, then the type the migration created where it
  differs; **Null** is whether the database column accepts NULL as created by the migrations
  ("yes" when no `nullable=False` is declared); **Default** is the code default (`default=`, applied
  by the application on insert) or the database default (`server_default`, written "DB:"); a dash
  means none. JSON columns list **field names only**, never values.
- **Keys and indexes**, **foreign keys and cascades** as declared. On SQLite the declared cascades
  are not applied (section 4.1, "Declared cascade").
- **Timestamps**, **written by**, **deleted by**, **soft or hard**, and **left behind when the owner
  is deleted**. User deletion removes only group memberships, the user's chats and the `user` and
  `auth` rows (`../tools/ground-truth.md`, Accounts and Access), so every table in this document
  keeps its rows when the owner is deleted; each subsection says what that looks like.
- **Model versus migration** differences, read from code. The local development database matched
  the models' columns except `knowledge.data` (`../tools/VERIFICATION.md`, Database Verification);
  index differences were not checked there and are **TO BE CONFIRMED** per database (section 5.6
  has the query).

Router paths below are under `backend/open_webui/routers/`; model paths under
`backend/open_webui/models/`.

### 6.1 `file`

An uploaded or generated file: the original name, where the bytes are stored, the extracted text,
and the processing status. One row per upload; the bytes live in storage (`DATA_DIR/uploads` or a
cloud bucket), not in the database.

| Column | Type | Null | Default | Meaning | Source |
|---|---|---|---|---|---|
| `id` | String (primary key) | no | - | Random UUID made by the upload handler; also part of the stored object's name and of the vector collection name `file-{id}` | `backend/open_webui/models/files.py:20`; `backend/open_webui/routers/files.py:365-367` |
| `user_id` | String | yes | - | Uploader (owner) | `backend/open_webui/models/files.py:21` |
| `hash` | Text | yes | - | SHA-256 of the **extracted text**; set when processing succeeds, cleared to NULL when it fails; used for the duplicate check and to delete chunks | `backend/open_webui/models/files.py:22`; `backend/open_webui/routers/retrieval.py:2069`, `:2134`, `:2164-2165` |
| `filename` | Text | yes | - | Name as uploaded; changed by **Rename** | `backend/open_webui/models/files.py:24`, `:394-405` |
| `path` | Text | yes | - | Storage location: a path under the upload folder for local storage, or an `s3://`, `gs://` or Azure container address | `backend/open_webui/models/files.py:25`; `backend/open_webui/storage/provider.py:62-71`, `:161`, `:233`, `:297` |
| `data` | JSON (`JSON`) | yes | - | Processing state and extracted text. Fields: `status` (`pending`, `processing`, `completed`, `failed`), `error`, `content` | `backend/open_webui/models/files.py:27`; `backend/open_webui/routers/files.py:238`, `:416`; `backend/open_webui/routers/retrieval.py:2064-2068`, `:2131`, `:2161` |
| `meta` | JSON (`JSON`; created as `JSONField` text, converted by `c29facfe716b`) | yes | - | Fields: `name`, `content_type`, `size`, `file_hash` (SHA-256 of the raw bytes), `data` (the metadata sent with the upload, for example `knowledge_id`, `directory_id`, `channel_id`, `source_url`), `collection_name` (the collection it was last indexed into) | `backend/open_webui/models/files.py:28`, `:52-57`; `backend/open_webui/routers/files.py:418-424`; `backend/open_webui/routers/retrieval.py:2121-2127` |
| `created_at` | BigInteger | yes | - | Upload time, epoch **seconds** | `backend/open_webui/models/files.py:30`, `:136` |
| `updated_at` | BigInteger | yes | - | Last change to any field, epoch **seconds**; NULL is possible on very old rows | `backend/open_webui/models/files.py:31`, `:87`, `:348` |

- **Keys and indexes.** Primary key `id`. The model also declares indexes on `user_id` and
  `created_at` (`backend/open_webui/models/files.py:21`, `:30`), but no migration creates them;
  whether they exist depends on how the database was first built (**TO BE CONFIRMED**).
- **Foreign keys.** None on this table. Three join tables point **at** it with `ON DELETE CASCADE`:
  `knowledge_file.file_id` (6.3), `channel_file.file_id` (6.16) and `chat_file.file_id` (sibling
  document).
- **Written by.** `insert_new_file` (`backend/open_webui/models/files.py:121-151`), reached through
  the upload handler (`backend/open_webui/routers/files.py:408-427`) from chat uploads, knowledge
  uploads, model profile images, web-page fetches, generated images and generated audio
  (`backend/open_webui/routers/models.py:622`; `backend/open_webui/routers/retrieval.py:2397`;
  `backend/open_webui/routers/images.py:531`; `backend/open_webui/utils/files.py:173`). Updates
  merge new keys into `data` and `meta` rather than replacing them
  (`backend/open_webui/models/files.py:331-392`).
- **Deleted by.** Hard delete only: `DELETE /api/v1/files/{id}` (owner, admin, or a person with
  write access through a knowledge base) (`backend/open_webui/routers/files.py:1013-1060`); the
  knowledge router's file clean-up (`backend/open_webui/routers/knowledge.py:64-80`); and the
  admin delete-all (`backend/open_webui/routers/files.py:575-596`). The single delete first
  removes the file's `knowledge_file` links and its chunks from each knowledge base's collection
  (`:1025-1036`), then the row, the stored object and the file's own vector data (`:1039-1043`).
  What that last vector step does depends on the vector database (section 6.27).
- **Owner deleted.** Rows stay with the old `user_id`; the stored object stays in storage.
- **Model versus migration.** The initial schema had only `id`, `user_id`, `filename`, `meta` and
  `created_at` (`backend/open_webui/migrations/versions/7e5b5dc7342b_init.py:67-77`); `hash`,
  `data` and `updated_at` were added by `c0fbf31ca0db` (`c0fbf31ca0db_update_file_table.py:27-32`),
  `path` by `c29facfe716b`, which also copied a legacy `meta.path` into it
  (`c29facfe716b_update_file_table_path.py:28-67`). An `access_control` column was added by
  `7826ab40b532` and dropped by `f1e2d3c4b5a6`, which created no grants for files because file
  permissions were owner-only (`f1e2d3c4b5a6_add_access_grant_table.py:107-111`, `:215-223`).
  Migration file names in this paragraph are under `backend/open_webui/migrations/versions/`.

### 6.2 `knowledge`

A knowledge base: a named, shareable set of files indexed together. Its files are linked through
`knowledge_file`; its folders are `knowledge_directory` rows; its sharing is in `access_grant`
(resource type `knowledge`).

| Column | Type | Null | Default | Meaning | Source |
|---|---|---|---|---|---|
| `id` | Text (primary key) | no | - | Random UUID; also the name of the knowledge base's vector collection. Rows migrated from the old document feature kept the old collection name as their id | `backend/open_webui/models/knowledge.py:51`, `:210`; `backend/open_webui/migrations/versions/6a39f3d8e55c_add_knowledge_table.py:66-80` |
| `user_id` | Text | no (migration) | - | Owner (creator) | `backend/open_webui/models/knowledge.py:52`; `6a39f3d8e55c_add_knowledge_table.py:32` |
| `name` | Text | no (migration) | - | Display name; no uniqueness in the schema | `backend/open_webui/models/knowledge.py:54`; `6a39f3d8e55c_add_knowledge_table.py:33` |
| `description` | Text | yes | - | Description as typed (required by the API form) | `backend/open_webui/models/knowledge.py:55`, `:165-168` |
| `meta` | JSON (`JSON`) | yes | - | Empty for ordinary knowledge bases. Fields used: `source` (`external` for connected knowledge bases), `read_only`, `external` (connection and field-mapping details); migrated legacy rows have `legacy`, `document`, `tags`. Details in `knowledge-bases.md` section 6.2 | `backend/open_webui/models/knowledge.py:57`, `:294-303`; `6a39f3d8e55c_add_knowledge_table.py:72-76` |
| `data` | JSON | yes | - | **Leftover, not used.** Present in the database but not mapped by the v0.11.4 model (see below) | `backend/open_webui/migrations/versions/81cc2ce44d79_update_channel_file_and_knowledge_table.py:39-43` |
| `created_at` | BigInteger | no (migration) | - | Creation time, epoch **seconds** | `backend/open_webui/models/knowledge.py:59`, `:212` |
| `updated_at` | BigInteger | yes | - | Epoch **seconds**; changes on rename, description, `meta` or access changes and on reset, not when files are added | `backend/open_webui/models/knowledge.py:60`, `:746`, `:768`, `:789` |

- **Keys and indexes.** Primary key `id`; no other index.
- **Foreign keys.** None on this table. `knowledge_file.knowledge_id` and
  `knowledge_directory.knowledge_id` point at it with `ON DELETE CASCADE`.
- **Written by.** `insert_new_knowledge`, `update_knowledge_by_id`, `update_knowledge_meta_by_id`
  and `reset_knowledge_by_id` (`backend/open_webui/models/knowledge.py:203-229`, `:731-796`), from
  the knowledge router's create, update, external-source and reset routes
  (`backend/open_webui/routers/knowledge.py:318`, `:894`, `:944`, `:1009`, `:1146`, `:1792`).
- **Deleted by.** Hard delete: `DELETE /api/v1/knowledge/{id}/delete` (owner, write grant or admin)
  removes the knowledge base from every custom model's knowledge list, deletes its vector
  collection (local knowledge bases), removes its entry from the `knowledge-bases` collection,
  revokes all its access grants and deletes the row
  (`backend/open_webui/routers/knowledge.py:1702-1784`; `backend/open_webui/models/knowledge.py:798-806`).
  **Reset Vector Storage/Knowledge** deletes every row (`backend/open_webui/models/knowledge.py:808-820`).
  The files themselves are not deleted by a knowledge base deletion.
- **Children left on SQLite.** The model deletes only the `knowledge` row and relies on the declared
  cascades for `knowledge_file` and `knowledge_directory`; on SQLite those rows remain
  (`knowledge-bases.md` section 5.15).
- **Owner deleted.** The knowledge base, its links and its vector collection remain; shared users
  keep their access through `access_grant`.
- **The `knowledge.data` leftover.** The original table had a `data` column holding `file_ids`.
  Migration `3e0e00844bb0` copied those ids into `knowledge_file` rows (skipping ids whose file row
  no longer existed) and dropped the column
  (`backend/open_webui/migrations/versions/3e0e00844bb0_add_knowledge_file_table.py:73-128`); the
  next-but-one migration `81cc2ce44d79` added an empty `data` column back
  (`81cc2ce44d79_update_channel_file_and_knowledge_table.py:39-43`). The v0.11.4 model does not map
  it (`backend/open_webui/models/knowledge.py:48-60`), so no code reads or writes it; it is
  recorded as a benign leftover (`../tools/VERIFICATION.md`, Database Verification item 4;
  `_research-notes.md`, product defect 7). Because of the skip at `:111-115`, a knowledge base that
  listed a file whose row was already gone lost that link during the upgrade.
- **Other history.** `access_control` was added by `922e7a387820` and replaced by `access_grant`
  rows in `f1e2d3c4b5a6`, where a NULL value became a public read grant (`user` principal `*`)
  and `{}` became private (`f1e2d3c4b5a6_add_access_grant_table.py:8-11`, `:99-134`).

### 6.3 `knowledge_file`

The link between a knowledge base and a file, with the folder the file sits in. A file can appear
once per knowledge base.

| Column | Type | Null | Default | Meaning | Source |
|---|---|---|---|---|---|
| `id` | Text (primary key) | no | - | Random UUID | `backend/open_webui/models/knowledge.py:102`, `:687` |
| `knowledge_id` | Text, foreign key to `knowledge.id`, `ON DELETE CASCADE` | no | - | The knowledge base | `backend/open_webui/models/knowledge.py:104` |
| `file_id` | Text, foreign key to `file.id`, `ON DELETE CASCADE` | no | - | The file | `backend/open_webui/models/knowledge.py:105` |
| `directory_id` | Text, foreign key to `knowledge_directory.id`, `ON DELETE SET NULL` (constraint `fk_knowledge_file_directory_id`) | yes | - | The folder; NULL means the root | `backend/open_webui/models/knowledge.py:106`; `backend/open_webui/migrations/versions/3c9b0ca343fd_add_knowledge_directory_table.py:48-59` |
| `user_id` | Text | no | - | Who added the file (can differ from the file's owner) | `backend/open_webui/models/knowledge.py:107` |
| `created_at` | BigInteger | no | - | When linked, epoch **seconds** | `backend/open_webui/models/knowledge.py:109`, `:692` |
| `updated_at` | BigInteger | no | - | Epoch **seconds**; changes when the file is moved to another folder | `backend/open_webui/models/knowledge.py:110`, `:1110` |

- **Keys and indexes.** Primary key `id`; unique `uq_knowledge_file_knowledge_file` on
  (`knowledge_id`, `file_id`); index `ix_knowledge_file_directory_id`
  (`backend/open_webui/models/knowledge.py:112-115`). The creating migration also built
  `ix_knowledge_file_knowledge_id`, `ix_knowledge_file_file_id` and `ix_knowledge_file_user_id`,
  which the model does not declare
  (`backend/open_webui/migrations/versions/3e0e00844bb0_add_knowledge_file_table.py:52-59`).
- **Written by.** `add_file_to_knowledge_by_id` (`backend/open_webui/models/knowledge.py:676-707`);
  folder moves (`:1097-1116`) and folder deletion with "move files" (`:1030-1036`, `:1049-1063`).
- **Deleted by.** Hard delete: removing a file from a knowledge base (`:720-729`); reset (`:737`);
  deleting a folder without moving its files (`:1065-1075`); and deleting the file itself, which
  removes its links in every knowledge base first (`backend/open_webui/routers/files.py:1025-1029`).
  The delete-all and knowledge-base delete paths rely on the cascades, so on SQLite the links
  remain.
- **Owner deleted.** Links remain; the `user_id` "added by" no longer resolves to a person.
- **History.** The rows were first created from `knowledge.data.file_ids` (6.2).

### 6.4 `knowledge_directory`

A folder inside a knowledge base. Folders nest through `parent_id`.

| Column | Type | Null | Default | Meaning | Source |
|---|---|---|---|---|---|
| `id` | Text (primary key) | no | - | Random UUID | `backend/open_webui/models/knowledge.py:66`, `:836` |
| `knowledge_id` | Text, foreign key to `knowledge.id`, `ON DELETE CASCADE` | no | - | The knowledge base | `backend/open_webui/models/knowledge.py:67` |
| `parent_id` | Text, foreign key to `knowledge_directory.id`, `ON DELETE CASCADE` | yes | - | Parent folder; NULL for a top-level folder | `backend/open_webui/models/knowledge.py:68` |
| `name` | Text | no | - | Folder name | `backend/open_webui/models/knowledge.py:69` |
| `user_id` | Text | no | - | Who created the folder | `backend/open_webui/models/knowledge.py:70` |
| `created_at` | BigInteger | no | - | Epoch **seconds** | `backend/open_webui/models/knowledge.py:72`, `:834` |
| `updated_at` | BigInteger | no | - | Epoch **seconds**; changes on rename or move | `backend/open_webui/models/knowledge.py:73`, `:949`, `:982` |

- **Keys and indexes.** Primary key `id`; unique `uq_knowledge_directory_knowledge_parent_name` on
  (`knowledge_id`, `parent_id`, `name`); indexes `ix_knowledge_directory_knowledge_id` and
  `ix_knowledge_directory_parent_id` (`backend/open_webui/models/knowledge.py:75-79`;
  `backend/open_webui/migrations/versions/3c9b0ca343fd_add_knowledge_directory_table.py:26-45`).
  Both SQLite and PostgreSQL treat NULLs as distinct in a unique constraint by default, so the
  database itself does not stop two top-level folders with the same name (read from the
  constraint; `knowledge-bases.md` section 14 lists it).
- **Written by.** `create_directory`, `rename_directory`, `move_directory` (with a cycle check)
  (`backend/open_webui/models/knowledge.py:824-850`, `:940-988`). A unique-constraint failure on
  create or rename makes the method return nothing, which the router reports as
  `Failed to create directory. A directory with this name may already exist at this level.` or
  `Failed to update directory. This may be caused by a naming conflict or circular move.`
  (`backend/open_webui/routers/knowledge.py:2272-2276`, `:2309-2313`).
- **Deleted by.** Hard delete of one folder (`backend/open_webui/models/knowledge.py:1009-1047`);
  reset with folders included, which the interface uses (`:739-741`). The code deletes only the
  named folder and relies on the `parent_id` cascade for its sub-folders (comment at `:1041`): on
  SQLite the sub-folders remain with a parent that no longer exists, and stop appearing in the
  folder tree (`knowledge-bases.md` section 14).
- **Owner deleted.** Folders remain.
