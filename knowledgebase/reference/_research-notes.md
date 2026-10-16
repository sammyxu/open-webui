# Research Notes and Gaps

Not a reference document (underscore prefix). Every researcher's structured summary and, above
all, its **gaps** list, harvested as each report arrived. The gaps feed
`../13-open-questions.md`. Findings marked **verified** were re-read against the source in the
main loop before being used in `../tools/ground-truth.md` or `CLAUDE.md`.

## Phase 0 and 1 Sweeps (2026-10-07)

### Sweep: Configuration System, Data Stores and Storage Layout

**Key findings (verified items marked).**

- Persistent config is one `config` row per dotted key (`backend/open_webui/models/config.py:101-108`);
  `DEFAULT_CONFIG` (`backend/open_webui/config.py:2822`) holds **405 keys** (404 dotted in 33
  namespaces plus `webhook_url`). Largest namespaces: `web` 78, `rag` 76, `oauth` 53, `audio` 30,
  `image_generation` 20, `ui` 20, `task` 19, `ldap` 17, `images` 13. **Verified.**
- Precedence: a stored row wins over the environment; `seed_defaults` inserts only missing keys
  (`backend/open_webui/models/config.py:240-266`). `oauth.*` keys follow the environment unless
  `ENABLE_OAUTH_PERSISTENT_CONFIG=True` (default `False`, `backend/open_webui/config.py:3232`);
  admin edits to them then live only in that process's memory. `ENABLE_PERSISTENT_CONFIG=False`
  makes every key environment-only and every admin edit per-process and lost on restart.
  `RESET_CONFIG_ON_START=True` wipes the table on every boot. A legacy `DATA_DIR/config.json` is
  imported once and renamed. **Verified** (precedence and OAuth exception).
- Env-only settings (not in `DEFAULT_CONFIG`): `VECTOR_DB`, `STORAGE_PROVIDER`, `DATABASE_URL`,
  `REDIS_URL`, `WEBUI_NAME`, `WEBUI_SECRET_KEY`, OAuth client registration values.
- `webui.url` (seeded from `WEBUI_URL`) is database-persisted: changing the environment variable
  after first boot has no effect.
- No config caching and no Redis config sync: `Config.get` reads the database each call; replicas
  stay consistent only through the shared database.
- `GET /api/v1/configs/export` returns every stored key, including provider API keys and OAuth
  client secrets; `GET /api/v1/utils/db/download` lets an admin download the raw SQLite file when
  `ENABLE_ADMIN_EXPORT` is on (default `True`). Both are sensitive.
- `WEBUI_SECRET_KEY`: startup exits with a multi-line message when authentication is on and the
  key is empty (`backend/open_webui/env.py:780-788`). `backend/start.sh` generates
  `.webui_secret_key` in its own directory; in the Docker image that is `/app/backend`, outside the
  `/app/backend/data` volume, so a recreated container gets a new key unless `WEBUI_SECRET_KEY` or
  `WEBUI_SECRET_KEY_FILE` is set. A new key logs everyone out and makes encrypted valves and stored
  OAuth client data unreadable. **Verified** (`Dockerfile` `WORKDIR /app/backend`,
  `docker-compose.yaml:18`, `backend/start.sh:16-17`, `:31`).
- Database selection: default `sqlite:///{DATA_DIR}/webui.db`; a full set of `DATABASE_TYPE`,
  credentials, `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME` overrides `DATABASE_URL`.
  **SQLCipher URLs fail at import** in v0.11.4 (`backend/open_webui/internal/db.py:244-248`,
  `:447`). **Verified.**
- Migrations run when `open_webui.config` is imported (`backend/open_webui/config.py:81-82`), in
  every process; failure aborts startup. 58 revision files, linear chain, head `d4c1a8e37b62`
  (`add_chat_timer_at_and_chat_indexes`), root `7e5b5dc7342b`. Two revisions have no
  existence guards (`856c5b02fb54`, `d4c1a8e37b62`). **Verified** (import-time run).
- Tables: 39 in `backend/open_webui/models/`; migration-only tables `chatidtag`, `document`
  (legacy, never dropped), `prompt_new` (temporary), `config_old` (preserved blob table), plus
  Alembic's `alembic_version`; vector-store tables such as `document_chunk` exist only for some
  `VECTOR_DB` choices.
- Vector store: `VECTOR_DB` default `chroma` (`pgvector` in the slim image), stored at
  `DATA_DIR/vector_db`; embedding engine default local SentenceTransformers with
  `sentence-transformers/all-MiniLM-L6-v2`; both embedding settings are database-persisted.
- File storage: `STORAGE_PROVIDER` default `local` (`DATA_DIR/uploads`); cloud providers also keep
  a local copy unless `STORAGE_LOCAL_CACHE=false`.
- Redis (optional) carries: task manager and stop commands; websocket manager, session and usage
  pools and Yjs documents (only with `WEBSOCKET_MANAGER=redis`); optional server-side sessions;
  rate limiting; JWT revocation; model and tool-server caches; the `/ready` probe.
- Sign-in rate limit: 15 attempts per 180 seconds per email address
  (`backend/open_webui/routers/auths.py:91`, `:818-822`); the refusal reads `API rate limit exceeded`.
  **Verified.**
- Time: timestamps are epoch integers; no server time zone setting; each user has a `timezone`
  column set from the browser; automations fall back to the server's local time.

**Gaps (what the repository cannot tell us).**

1. Live values in the `config` table (352 database-authoritative keys), including the embedding
   model in use, `webui.url`, sign-up and permission settings, and whether rows were edited,
   imported or carried over from `config.json`.
2. Production environment values: `ENABLE_PERSISTENT_CONFIG`, `ENABLE_OAUTH_PERSISTENT_CONFIG`,
   `RESET_CONFIG_ON_START`, `DATA_DIR`, `DATABASE_URL`/`DATABASE_*`, `VECTOR_DB`, `STORAGE_PROVIDER`,
   `REDIS_URL`/Sentinel/Cluster, `WEBSOCKET_MANAGER`, `UVICORN_WORKERS`, `ENV`, `WEBUI_BUILD_HASH`.
3. Where production's `WEBUI_SECRET_KEY` comes from and whether it survives a redeploy.
4. The local `.env` file was not read (access denied by the permission system); the local
   `backend/data/` store was deliberately not opened.
5. Applied migration state in production (`alembic_version`) and whether `chatidtag`, `document`
   and `config_old` still exist there.
6. Deployment shape (image, `open-webui serve` or `start.sh`), volume mounts, host or container time
   zone, storage bucket names and their access policies.
7. Vector store contents and dimensions, and whether stored embeddings match the configured model.
8. Behaviour that needs execution: whether SQLCipher fails exactly as read, whether several
   workers seeding config on a fresh database can collide, real Redis TTL and failover behaviour.

### Sweep: Deployment, Environments, Process Model and CI

**Key findings (verified items marked).**

- Image: two stages, `node:22-alpine3.20` build and `python:3.11-slim-bookworm` runtime; `WORKDIR
  /app/backend`; `ENV=prod`, `PORT=8080`; `EXPOSE 8080`; `HEALTHCHECK` calls `/health`;
  `CMD ["bash", "start.sh"]` (`Dockerfile:27`, `:56`, `:74`, `:119`, `:210-231`). Build arguments
  `USE_CUDA`, `USE_OLLAMA`, `USE_SLIM`, `USE_PERMISSION_HARDENING`, embedding model choices, `UID`
  and `GID` (root by default). Model caches sit under the data volume path.
- `backend/start.sh`: optional Playwright install, secret key file generation in its own directory,
  optional bundled Ollama and CUDA paths, Hugging Face Space mode, then `exec` uvicorn with
  `--workers ${UVICORN_WORKERS:-1}` and `--forwarded-allow-ips ${FORWARDED_ALLOW_IPS:-*}`.
  `backend/dev.sh` does not handle the secret key. **Verified.**
- The secret-key file generated in the container lands outside the data volume, so recreating the
  container without `WEBUI_SECRET_KEY` signs everyone out. **Verified.** A separate build-hygiene
  observation about the key file and the Docker build context was reported privately to the
  maintainer; it is security-sensitive and deliberately not recorded in the knowledgebase.
- Compose: the base `docker-compose.yaml` runs `ollama` and `open-webui` (named volume `open-webui`
  at `/app/backend/data`, port `${OPEN_WEBUI_PORT-3000}:8080`); overlays for GPU, AMD GPU, API port,
  data bind mount, Playwright; a standalone OpenTelemetry stack; an image-generation test overlay.
  The `open-webui` service declares both `build:` and an upstream `image:`; whether `up -d` pulls
  the upstream image instead of building the fork is Compose behaviour (external, unverified here).
- `Makefile` targets `remove` and `update` call scripts that do not exist in the repository.
  `docker-cleanup.sh` runs `docker compose down -v`, which deletes the data volume.
- CI: no workflow triggers on pushes or pull requests to `uoft`; `docker.yaml` can be dispatched
  manually. Upstream release workflows target `main`.
- `ENV` defaults to `dev` outside Docker, which enables `/docs`, `/openapi.json` and a debug
  embeddings endpoint registered only when `ENV == 'dev'` (`backend/open_webui/routers/retrieval.py:3320-3324`).
  **Verified.**
- Multiple workers or replicas need: `WEBSOCKET_MANAGER=redis` with Redis; Redis for task stop,
  JWT revocation and shared rate limiting; one shared `WEBUI_SECRET_KEY`; PostgreSQL; shared storage
  and vector store; one instance running migrations. Nothing in the code warns when these are
  missing. The automations scheduler runs in every worker.
- Without Redis, signing out does not revoke the token on the server: `is_valid_token` returns
  `True` when no Redis client exists and `invalidate_token` stores nothing
  (`backend/open_webui/utils/auth.py:276-288`, `:315-323`). **Verified.**
- Health: `/health` always returns `{"status": true}`; `/ready` returns 503 `Startup not complete`,
  `Database not ready` or `Redis not ready`; `/health/db` pings the database and fails as an
  unhandled error. **Verified** (`/health`, `/ready`).
- Logs go to stdout only (loguru); `LOG_FORMAT=json` for JSON lines; `GLOBAL_LOG_LEVEL`; no
  per-source levels in v0.11.4. The audit log (`AUDIT_LOG_LEVEL`, default `NONE`) writes
  `DATA_DIR/audit.log`, rotating at 10 MB, with user id, name, email, role, source IP and (at the
  request levels) request bodies, so it is personal data.
- `/api/version` is unauthenticated; `/api/version/updates` checks upstream GitHub releases, so it
  reports upstream versions for this fork.
- No production host, domain or URL for MedIT GPT appears anywhere in the repository; the only
  branded strings are display names (`backend/open_webui/env.py:951`, `src/lib/constants.ts:7`,
  `src/app.html`, `static/opensearch.xml`, the web manifests).

**Gaps.**

1. Production host, domain, DNS, TLS termination and reverse proxy (including websocket upgrade
   for `/ws/socket.io`).
2. Deployment method and artefact: Docker, Compose, Kubernetes, OpenShift or pip; registry and tag;
   whether the running image was built from `uoft`.
3. Production settings: how `WEBUI_SECRET_KEY` is supplied; `ENV`; `UVICORN_WORKERS` and replica
   count; `DATABASE_URL`; `REDIS_URL`; `WEBSOCKET_MANAGER`; `STORAGE_PROVIDER`; `VECTOR_DB`;
   `AUDIT_LOG_LEVEL`; `WEBUI_URL`; `CORS_ALLOW_ORIGIN`; SSO configuration; `LICENSE_KEY`.
4. GitHub settings on the fork: whether Actions or Dependabot are enabled, branch protection.
5. Which LICENSE §4 exception covers the rebrand, and the actual user count.
6. Operations: log shipping and retention, backups of the data volume, resource sizing, image
   variant (standard, slim, CUDA).

### Sweep: Identity, Sign-In, Roles, Groups and Permissions

**Key findings (verified items marked; the rest feed the identity reference documents, whose
researchers re-derive them from source).**

- `user` table columns include `email` (unique), `username` (never set by any sign-in path),
  `role` (default `pending`), profile fields, `timezone`, presence and status fields, `info`,
  `variables`, `settings` (with a `ui` dictionary), `oauth`, `scim`, `last_active_at` (written at
  most once a minute per user per worker). The fork's two settings live in `user.settings.ui` and
  are governed by the `settings.interface` permission.
- Roles are exactly `admin`, `user`, `pending` **(verified)**; the server does not validate the role
  string on admin update, and any other value behaves like `pending` in the interface.
- `auth.active` is only ever written as `True` by the application; an inactive row (database edit
  only) is refused like a wrong password.
- Sign-in paths: email and password; LDAP (generic `LDAP authentication failed.` for most
  failures, real reason only in the server log); OAuth or OIDC providers `google`, `microsoft`,
  `github`, `oidc`, `feishu` (registered from environment variables at startup); trusted headers
  (auto-creates unknown users even with sign-up off); no-login mode (`WEBUI_AUTH=False`); SCIM
  provisioning (creates users without an `auth` row); token exchange (off by default).
- SSO details: allowed-domain list, merge-by-email (off by default), OAuth sign-up (off by default,
  separate from `ui.enable_signup`), role mapping from a roles claim (`OAUTH_ALLOWED_ROLES`,
  `OAUTH_ADMIN_ROLES`; an admin whose claim only matches an allowed role is demoted at next login),
  group mapping that **replaces** membership, optional group creation. Errors redirect to
  `/auth?error=...` and appear as a pop-up. **Verified** (domain check shows `INVALID_CRED`).
- Sign-out returns an identity-provider logout URL for OAuth users; back-channel logout is
  optional and needs Redis to end existing sessions.
- `get_verified_user` and `get_admin_user` answer 401 `ACCESS_PROHIBITED` **(verified)**; pending
  users see the Account Activation Pending overlay **(verified)**; `/api/v1/auths/admin/details`
  supplies the admin contact when `auth.admin.show` is on.
- Permission defaults (`user.permissions`) by section: `workspace` (all off), `sharing` (all off),
  `access_grants` (on), `chat` (all on except `temporary_enforced`), `features` (`api_keys`,
  `direct_tool_servers`, `automations`, `webhooks` off; the rest on), `settings.interface` (on).
  Additive across groups **(verified)**. Global feature switches are separate (for example
  `channels.enable`, default off).
- Admin defaults: may open other users' chats; bypass workspace sharing **(verified)**.
- Any signed-in user can search users and see names and emails **(verified)**.
- The primary admin (earliest `created_at`) cannot be demoted, edited by other admins, or deleted;
  no admin can delete themselves.
- User deletion is hard and leaves most owned content behind **(verified)**; on SQLite, rows that
  rely on database cascades can be orphaned because foreign-key enforcement is not switched on.
- Rate limit: 15 sign-in attempts per 180 seconds per email, counting successes too; no lockout
  **(verified)**. LDAP, trusted header, OAuth callback and sign-up are not rate limited.
- Server logs contain personal data (sign-in emails, OAuth claims on failure).
- Several credential-handling observations were reported privately to the maintainer as
  security-sensitive and are deliberately not recorded here.

**Gaps.**

1. Live `config` rows for identity: `ui.default_user_role`, `ui.enable_signup`,
   `ui.enable_login_form`, `ui.enable_password_change_form`, `ui.default_group_id`, pending-overlay
   text, `auth.jwt_expiry`, `auth.enable_api_keys` and endpoint restrictions, `auth.admin.show`,
   `auth.admin.email`, `user.permissions`, `users.enable_status`, `webui.url`, all `ldap.*`, and
   `oauth.*` when persisted.
2. Environment-only identity settings in production: `WEBUI_AUTH`, `ENABLE_PASSWORD_AUTH`, trusted
   headers, which SSO providers are configured and their claim names and role, admin and domain
   lists, `ENABLE_SCIM`, back-channel logout, token exchange, `PASSWORD_HASH_ALGORITHM`, password
   validation, admin bypass switches, cookie settings, `WEBUI_NAME`.
3. Whether Redis is configured (token revocation, shared rate limit) and how many workers or
   replicas run.
4. Whether production uses SQLite or PostgreSQL (cascade behaviour on user and group deletion).
5. Who the primary admin is; current roles; group names, members, permissions and share settings;
   access grants per resource; which users are SSO-linked or SCIM-created.
6. What the identity provider actually sends in its role and group claims.

## Phase 2 Research (from 2026-10-07)

Batch 1 (authentication, users and permissions, chat composer, chat pipeline) ran four researchers
in parallel; all four were stopped together by the account session limit after about 35 minutes.
Progressive writing preserved the documents, but no final summary arrived, so the entries below are
harvested from each document's section 14 and from the main-loop review. Counts come from the stats
helper (section 10 message rows, section 11 symptom headings, section 14 items).

### authentication-and-sign-in.md

Status: complete (14 of 14 sections), 1,898 lines, 105 messages, 25 symptoms, 15 open questions.

**Gaps (section 14, condensed).** Which sign-in methods production offers (`WEBUI_AUTH`,
`ENABLE_PASSWORD_AUTH`, login form, LDAP, OAuth providers, trusted headers); live values of every
authentication setting; whether Redis is configured and how many processes run; password policy in
force; cookie and sign-out redirect settings; how people obtain accounts and who approves pending
users, by what channel and how fast; U of T processes for password changes and resets for SSO and
LDAP accounts and the identity checks an admin must make; API-key policy; network requirements
(VPN, proxy) and the LDAP username format; several behaviours read from code but not exercised
(double pop-up on refused token, silent failures of some buttons, `[object Object]` validation
errors); upstream wording that may not suit this deployment (first-run note, "WebUI" in the pending
overlay, upstream links). Two ground-truth refinements were verified and applied (LDAP first admin
does not switch sign-up off; the rate-limit window is three to four minutes). One checker false
flag was fixed. Security-sensitive matters were reviewed and deliberately left undescribed.

### chat-completion-pipeline-and-generation-tasks.md

Status: complete, 1,972 lines, 168 messages, 19 symptoms, 21 open questions. The researcher died
just before correcting its claims about background-task failures; a repair agent was briefed with
verified evidence (title generation can raise before its own error handling, and on the
non-streaming path such an error publishes a `chat.failed` event although the reply succeeded).

**Gaps (section 14, condensed).** Live task-model, title, tag, follow-up, query, autocomplete,
compaction and sub-agent settings; workers, replicas, Redis and websocket manager (decide whether
Stop and live streaming work reliably); environment timeouts and limits
(`AIOHTTP_CLIENT_TIMEOUT`, `AIOHTTP_CLIENT_STREAM_IDLE_TIMEOUT`,
`CHAT_RESPONSE_MAX_TOOL_CALL_ITERATIONS` and others); which providers and models run and whether
the usage capability is on; whether tier 1 can read admin settings and server logs; behaviours
inferred from code needing a test environment (multi-model chats left titled "New Chat",
plain-text provider errors, sending while disconnected, resuming tool approval after reload);
`chat.failed` events cover only non-streaming exceptions; background-task token usage is not
recorded; **personal data:** user placeholders and pipeline filter calls can send names and email
addresses to model providers and pipeline servers (privacy review TO BE CONFIRMED); Redis holds
in-progress reply text; debug logs include emails. Two items were marked security-sensitive.

### chat-composer-and-message-display.md and users-groups-roles-and-permissions.md

Status: truncated (sections 13 and 14, and section 14, respectively); repair agents appending only
the missing sections. Entries follow when the repairs finish.

### chat-composer-and-message-display.md (repaired)

Status: repaired to 14 of 14 sections (a repair agent appended sections 13 and 14 only; sections 1
to 12 unchanged), 2,253 lines, 145 messages, 27 symptoms, 32 open questions; 907 citations resolve;
142 files indexed (109 in scope, 33 cross-area).

**Gaps (section 14, condensed).** Live feature switches and engines (web search, image generation,
code execution and interpreter, speech-to-text and text-to-speech); web search confirmation text;
upload limits; default models and prompt suggestions (whether the upstream example cards still
show); message rating, community sharing and watermark settings; admin defaults for interface
settings (`ui.default_interface_settings`, including whether Hide Processing Details or Inline
Citations are preset); permissions in force; per-model capabilities in production; which build is
live and whether the uncommitted rendering changes are deployed; environment-only values such as
`WEBUI_NAME`; licence metadata reaching the browser; whether users' networks reach external favicon
and CDN services; product behaviours to confirm in a test environment (version choice saved late,
bracketed numbers removed when Inline Citations is off, `Parent message not found`, unreachable
Google Drive upload path, unused and empty components, a `/home` stub linking to a page that does
not exist); support contact and escalation roles; tier 1's own access; who reviews feedback rows
(each holds a snapshot of the conversation) and their retention; whether users may be sent to
upstream community links; who handles licence notices. Two items referred as security-sensitive.

**Process note.** The repair agent found that researchers running in parallel were overwriting each
other's temporary files in the shared scratchpad; rule 19a now requires a per-slug sub-folder.

### users-groups-roles-and-permissions.md (repaired)

Status: repaired to 14 of 14 sections, 1,859 lines, 90 messages, 19 symptoms, 66 open questions;
850 citations resolve. The repair agent also completed the correction the original researcher was
making when it stopped: model access citations now include the chat path, the record-less base
model case, both bypass switches, arena models, and an availability refusal (a custom model whose
base model is unavailable is refused for everyone, admins included). Section 13 gained 14 rows so
every one of the 129 cited files is indexed.

**Ground truth refined (verified):** model access control also applies to admins whenever
`BYPASS_ADMIN_ACCESS_CONTROL` is off (`backend/open_webui/main.py:1150`;
`backend/open_webui/utils/models.py:526-528`).

**Gaps (section 14, condensed).** Live data: current roles, the primary admin, group names,
members, permissions and share settings, access grants per resource, live `user.permissions`,
the default group. Deployment: admin bypass switches, model access bypass, custom-model fallback,
database engine (cascade behaviour on deletion), Redis, worker count. People and process: who
approves pending users and through which channel, who may create groups and grant sharing, the
offboarding process given that deletion is permanent and leaves owned content behind. Product
behaviour: interface-versus-server enforcement of some permission keys, CSV import edge cases.
Knowledgebase consistency: two notes for the maintainer of this knowledgebase. One model-access
enforcement observation was referred as security-sensitive and requested privately for the
maintainer.

### chat-completion-pipeline-and-generation-tasks.md (corrected)

Status after the correction pass: 14 of 14 sections, 2,163 lines, 21 symptoms, 26 open questions;
1,021 citations resolve. Supersedes the counts in the earlier entry for this document.

**Correction applied (layer: reference).** The original text said background-task failures are
always swallowed and that a failed title falls back to the first message. The code shows: a new web
chat's title runs in a separate job (`backend/open_webui/main.py:1471-1492`) that logs
`Error generating initial chat title` on failure and leaves `New Chat`; task endpoints raise before
their own error handling when the model is not in the model list or a Pipelines inlet filter fails;
on the streaming path such a raise reaches `process_chat`'s handler and puts an error box under an
already complete answer; on the non-streaming path it publishes `chat.failed` after `chat.finished`;
the first-message fallback applies only while the chat holds its first exchange.

**Defect read from code (verified in the main loop; confirm in a test environment).** The initial
title job's context has no `model` key (`backend/open_webui/main.py:1477-1484`) but the handler
reads `ctx['model']` after saving the title (`backend/open_webui/utils/middleware.py:4042`), so
every new web chat should log `Error generating initial chat title` with a `KeyError`, even when
the title saved. Upstream code (no fork difference). Support must not read that log line alone as
a failure.

**Further findings for section 14:** the fallback title event can carry the reply's text instead of
the question (header keeps `New Chat` while the sidebar shows the saved title); saving the OpenAI
connection settings empties the model list briefly, so background tasks finishing in that window
raise `Model '' was not found`; the wording of `chat.failed` depends on the installed Starlette
version; whether production uses Pipelines filters is TO BE CONFIRMED.

### chat-conversations-history-and-organisation.md

Status: complete on first pass, 1,948 lines, 99 messages (83 checkable quotes all verified), 21
symptoms, 34 open questions; 734 citations resolve; links and personal-data checks clean; local
customisations: none (matches upstream v0.11.4).

**Gaps (condensed).** Live values of `folders.enable`, `folders.max_file_count`,
`ui.enable_community_sharing`; live default and group permissions for the chat, sharing and
folder keys; production `ENABLE_ADMIN_CHAT_ACCESS` and `ENABLE_ADMIN_EXPORT`; SQLite versus
PostgreSQL (declared deletion cascades are not enforced on SQLite as configured); whether share
links from before the `shared_chat` table exist (migrated to public-to-signed-in-users); which
event webhooks or Event functions are configured (events carry the actor's email and up to 300
characters of message text); backups and how a deleted chat could be restored; request-size limits
affecting imports; policy on community sharing (sends chats to openwebui.com), public and open
chat sharing, folder sharing and chat retention (the code has none); support contacts. Behaviours
not established from code: share page branch switching, share recipients opening attached files,
spinner sticking after an abnormal end, ChatGPT import fidelity, live updates in shared folders.
Interface defects worth reporting upstream: the share dialog's wording for a new private link; the
Archive All dialog's "cannot be undone"; a no-op **Mark all as read** in the folder menu; a Safari
copy-link false success; several silent failures; unused components; share access entries left
behind on chat deletion. Four items were referred as security-sensitive (privacy of shared and
deleted chats, server-side enforcement of some interface-only checks, admin access to internal
chats); they are recorded for the maintainer outside the knowledgebase.

### model-connections-openai-ollama-and-direct.md (continued after the limit)

Status: sections 1 to 7 by the first researcher, 8 to 14 appended by a continuation agent (end of
7.3 extended); 1,884 lines, 131 message rows (124 distinct texts), 15 symptoms; 803 citations
resolve. Two quote-checker flags in 5.10 are benign: the interface renders `Enter model tag (e.g.
{{modelTag}})` with hard-coded values (`mistral:7b`, `my-modelfile`), and the document quotes what
the admin sees (`src/lib/components/admin/Settings/Models/Manage/ManageOllama.svelte:655-656`,
`:873-874`).

**Key findings.** Saving OpenAI or Ollama connections empties the model registry in the process
that handled the save until it is rebuilt (by the admin's browser refresh, the next model-list
request or a chat); if every provider fails during that rebuild, everyone's list goes empty and
chats answer `Model not found`. A model list cached in Redis survives a restart. With the cache on,
connections using session or OAuth authentication contribute nothing to the startup pre-fetch.
Empty lists read `No results found` for users and `No models available` for admins. Several
interface defects read from code (unconfirmed): GGUF upload failures go only to the console; the
cancel pop-up depends on the follow-up delete; the admin tab reports `Settings saved successfully!`
before saves finish; a busy Save button after a failed headers check; deleting a llama.cpp model
from the picker calls the Ollama delete.

**Gaps (condensed).** Live `openai.*`, `ollama.*`, `direct.*`, `models.*` values; which providers
production uses and each connection's authentication type; environment timeouts, TLS checking,
`MODELS_CACHE_TTL`, pass-through and forwarded-header switches, bypass variables, fallback switch,
websocket manager, Redis and process count; production host and live `WEBUI_NAME`; desktop app use;
whether to point people at upstream help; who owns provider keys and quotas, whether support helps
with personal endpoints, whether direct connections should be offered; behaviours to confirm in a
test environment. Several items referred as security-sensitive (key storage, what some
authentication options send, data sent to pipelines servers, the generic pass-through, production
TLS checking).

### sso-oauth-oidc-and-scim.md (continued after the limit)

Status: sections 1 to 6 by the first researcher; 6.6 completed and 7 to 14 appended by a
continuation agent; 2,176 lines, 177 message rows (80 server, 19 browser, 78 log), 22 symptoms,
20 open questions; 916 citations resolve. One benign quote flag: the start-up message about code
challenge methods is composed from a template with `S256` filled in
(`backend/open_webui/config.py:2643-2648`).

**Key findings.** Several admin OAuth fields have no effect on sign-in (client id, secret, provider
name and URL, redirect URI, scopes come from the environment at startup); with OAuth persistence
off, saves still change one process's memory; emptying **Allowed Roles** means no non-admin role is
allowed although the placeholder suggests `*`; **Blocked Groups** only exempt memberships from
group mapping and block nobody from signing in; the admin tool-server dialog shows only
`Registration failed`; consent pages of tool servers may show the upstream product name
(licence-protected); one token-exchange message can never be shown. The code contains no UTORid,
Shibboleth or SAML support; the production identity provider is TO BE CONFIRMED. Three ground-truth
refinements were verified and applied (group sync exemptions and empty-claim behaviour, per-process
OAuth edits, the password message when the provider returns no user details).

**Gaps (condensed).** Which identity provider production uses and how; registered providers and
environment values (redirects, PKCE, audience, separators, cookies, sign-out); live `oauth.*`
values and persistence switches; optional features in use (trusted headers and which proxy, SCIM,
back-channel logout, token exchange, OAuth tool servers); Redis and process count; what the
provider's claims contain; who governs roles and groups and approves identity-provider changes; how
accounts are created and requested; U of T sign-out behaviour and shared-computer advice;
access-removal policy; contacts and service levels; host names and webhooks; behaviours read from
code but not run. Seven items referred as security-sensitive.

### workspace-models-and-model-access.md (continued after the limit)

Status: sections 1 to 3 by the first researcher, 4 to 14 appended by a continuation agent; 2,130
lines, 148 messages, 22 symptoms, 44 open questions grouped as live data, deployment environment,
people and process, product behaviour and knowledgebase consistency; 823 citations resolve. The
continuation agent passed all checks but was stopped (the build was paused) during its own final
read-through, so give this document an extra claim review in Phase 4. Detailed gap harvest
pending: read its section 14 when resuming.

## Product Defects and Quirks Read From Code (Running List)

For document 03 ("quirks and confirmed defects") and `ai/facts.json`. Each was verified by
re-reading the cited code in the main loop; none has been reproduced in a running instance, so each
is "read from code; confirm in a test environment" until then.

| # | What | Evidence | Upstream or fork |
|---|---|---|---|
| 1 | Every new web chat should log `Error generating initial chat title` (a `KeyError`) even when the title saved; memory review is skipped on that path | `backend/open_webui/main.py:1477-1492`; `backend/open_webui/utils/middleware.py:4038-4047` | upstream |
| 2 | The fallback title event sends the reply's text, so the header can keep "New Chat" while the sidebar shows the saved title | `backend/open_webui/utils/middleware.py:3857`, `:3990-4000` | upstream |
| 3 | Saving OpenAI or Ollama connection settings empties the model registry until it is rebuilt; requests in that window fail with `Model '' was not found` or `Model not found` | `backend/open_webui/routers/openai.py:344-357`, `:578` | upstream |
| 4 | A SQLCipher `DATABASE_URL` stops startup | `backend/open_webui/internal/db.py:244-248`, `:447` | upstream |
| 5 | The first LDAP account becomes admin but sign-up stays on | `backend/open_webui/routers/auths.py:663-667` | upstream |
| 6 | In the Docker image the generated secret key lives outside the data volume, so recreating the container signs everyone out | `Dockerfile` (`WORKDIR /app/backend`); `backend/start.sh:16-17`, `:31`; `docker-compose.yaml:18` | upstream design |
| 7 | `knowledge.data` column exists in the schema but is unmapped (benign) | migrations `3e0e00844bb0`, `81cc2ce44d79` | upstream |
| 8 | `make remove` and `make update` call scripts not in the repository | `Makefile` | upstream |
| 9 | **Reset Upload Directory** (described as "Delete uploaded files from the upload directory.") deletes every file record and stored file for all users and resets the entire vector store, including knowledge-base and memory vectors | `src/lib/i18n/locales/en-US/translation.json:2328-2329`; `src/lib/components/admin/Settings/Documents.svelte:354-365`; `backend/open_webui/routers/files.py:576-583` | upstream |
| 10 | Saving a function with a blank name (or empty base fields while a translation language is selected) does nothing: the editor calls `toast.error` but never imports `toast`, so the intended `Name and description are required` never appears | `src/lib/components/admin/Functions/FunctionEditor.svelte:329-333` (no `toast` import in the file) | upstream |
| 11 | Links in personal "chat finished" notifications lose `/c/`: a URL ending in `/c/{chat_id}` is rewritten to end in `/{chat_id}`, which matches no page | `backend/open_webui/utils/notifications.py:270-271`; routes under `src/routes/(app)/c/[id]/` | upstream |
| 12 | Pressing **Save** on the personal Interface tab replaces the person's own default model with the admin's first default model whenever admin default models are set | `src/lib/components/common/InterfaceSettings.svelte:394-397` (load), `:251-252` (save) | upstream |
| 13 | A mistyped `AUDIT_LOG_LEVEL` stops the server from starting: the error handler calls `logger.error` on the module `open_webui.utils.logger`, which has no `error` attribute, so an `AttributeError` replaces the intended "Invalid audit level" log line | `backend/open_webui/main.py:211`, `:797-801`; `backend/open_webui/utils/logger.py` (no `error` name) | upstream |

### workspace-models-and-model-access.md (gap harvest, 2026-10-08)

**Corrections applied in the main loop after verification:** the chat model selector is in the
composer, bottom right, not "at the top of a chat" (sections 1 and 2.1); precision notes added to
section 3.3 (first toggle creates a disabled record without access entries) and to the users
document (Model Defaults metadata hides record-less base models from admins without the bypass).

**Gaps (condensed).** Which provider models have settings records and which are public, shared or
admin-only; production workspace models (owners, sharing, hidden or disabled, attached knowledge
not shared with the model's audience); live default, pinned and order lists; arena models and their
access lists; live workspace and sharing permission values; community sharing (sends models to
openwebui.com); event webhooks (model events carry personal data); models owned by deleted accounts
(`Deleted User`); admin bypass and persistence switches; base-model cache, Redis and process count;
engines in production; backups (models without an export file are unrecoverable after deletion);
policy on public models, attaching personal or confidential files to shared models, ownership
transfer when people leave (the interface has none), naming and id conventions (ids cannot be
changed); whether native function calling works with each base model. Interface behaviours to
confirm: custom-model fallback and the system prompt, Shift+delete without confirmation, **Set as
default** reporting success when the server discards it, **Make Private** removing every access
entry, the id-length message saying "less than 256" while 256 is accepted, import entries clearing
parameters, `[object Object]` pop-ups. One item referred as security-sensitive.

### files-uploads-and-storage.md

Status: complete on first pass, 1,814 lines, 129 message rows (128 checkable quotes all verified),
25 symptoms, 37 open questions; 737 citations resolve; no local customisations in scope.

**Key findings.** **Reset Upload Directory** deletes every file record and stored file and resets
the entire vector store, knowledge-base and memory vectors included (verified in the main loop;
product defect 9 below). The storage-full error usually shows the operating system's text as
`[ERROR: {strerror}]`; the friendlier `[ERROR: The server is out of storage space.]` appears only on
paths that pass the error object. **Allowed File Extensions** entries must be lower case without
dots. **Max Upload Count** is checked only in the composer. A processing failure shows a warning
but leaves the file attached. Deleting a chat or a user leaves its files; all file deletion is
permanent; Shift skips the delete confirmation in the Files manager. OneDrive failures go only to
the browser console. Stored Google Drive and SharePoint id keys have no effect (the browser receives
the environment values). `STORAGE_LOCAL_CACHE=false` removes the local copy only after processing,
and later cloud reads leave fresh local copies (refines the Phase 0 sweep).

**Gaps (condensed).** Live upload limits, compression caps, picker switches and identifiers; upload
permissions and per-model file capabilities; admin bypass and knowledge-file retention switches;
event destinations (file events carry names, emails, file names and text); production storage
provider and bucket, local-cache and S3 tagging settings (tagging writes uploader names and emails
into object tags), data residency of local copies, capacity and monitoring, backups and retention
(none in code), database engine, server operating system, slim image, cloud-picker app
registrations; behaviours to confirm (restart during processing leaves a long spinner, chat-file
linking duplicate check, state after Reset Upload Directory, large S3 bucket deletion, note
attachments for collaborators, HEIC uploads); who may run destructive resets and under what change
control; storage-incident escalation; policy on admins viewing others' files. Several items
referred as security-sensitive.

### rag-retrieval-embeddings-and-vector-stores.md

Status: complete on first pass, 1,885 lines, 166 message rows (about 210 messages; 156 checkable
quotes all verified), 20 symptoms, 26 open questions; 977 citations resolve; coverage complete for
15 vector backends and 12 loaders; no local customisations in scope.

**Key findings.** Independently confirms the Reset Upload Directory hazard. The External document
loader always sends the uploader's identity with each file. Mistral OCR and PaddleOCR-VL store
their error text as document content (it gets embedded and can be quoted). A failed reranker load
silently turns hybrid search off while the admin sees `Settings saved successfully!`. The Chroma
backend swallows search errors, so chunks made with a different embedding model silently stop
matching. Reindex covers knowledge-base files, the knowledge search index and memories, not chat
uploads. With several workers only the process that handled an admin save reloads the embedding or
reranking model. Retrieved passages are saved inside replies, so document text stays readable in
old chats after a file is deleted (relevant to privacy requests).

**Gaps (condensed).** Live values of every Documents setting; production vector store, its
location and backups; image variant, model cache persistence, `OFFLINE_MODE`; which external
services receive documents and whether they are approved for health data; worker count; external
knowledge sources; event destinations; environment timeouts and switches; retention of Datalab
Marker output copies (never deleted by code); behaviours to confirm (dimension mismatch on Chroma,
duplicate file names sharing a source chip, an unreachable external source emptying all sources,
silent save failures, status-code prefixes on extraction errors). The panel's **Top K Reranker**
description contradicts the code. Three items referred as security-sensitive.

### knowledge-bases.md

Status: complete on first pass (finished just before the third usage limit), 2,037 lines, 127
message rows (about 186 strings; 146 checkable fragments all verified), 21 symptoms, 48 open
questions; 822 citations resolve; no local customisations in scope.

**Key findings (read from code, to confirm in a test environment).** `File added successfully.`
can appear although adding the file to the knowledge base later fails; removing a file you own
(file retention off, the default) deletes the file everywhere it is used, but its indexed text in
other knowledge bases is not cleaned up; on SQLite, deleting a knowledge base or directory leaves
orphan rows; knowledge bases picked with `#` vanish from the composer when the person lacks upload
permission or the model has File Upload off; **Sync directory** removes everything outside the
chosen folder; deleting a directory deletes its files by default; edit and rename gaps between
owners and collaborators; a file left "processing" by a restart is never recovered; there is no
limit on files per knowledge base; with nothing attached, the model's knowledge tools search only
the 50 most recently updated readable knowledge bases (200 for grep).

**Gaps (condensed).** Live permission values (Knowledge Access is off in code) and `rag.*`
settings; connected knowledge bases; stuck uploads; models whose knowledge bases are not shared
with their audience; event subscriptions; orphan rows on SQLite; production database engine,
vector store, storage provider, environment-only switches (file retention, admin bypass, `kb_exec`
and tool limits), proxy timeouts for reindex, worker count, backups and single-knowledge-base
restore, extraction engines and Pandoc, log retention; who grants Knowledge Access and sharing,
what documents may be stored and whether public sharing is allowed, who handles restores and admin
exports, who owns connected sources. Three items referred as security-sensitive.

### Third usage limit (2026-10-08)

The web-search and built-in-tools researchers had not created their files when the limit hit
(they read for about 30 minutes first), so nothing survived; rule 1 of the research instructions
now requires creating the file within the first few minutes.

### web-search-and-web-loading.md

Status: complete on first pass, 1,556 lines, 82 user-facing messages plus 19 log rows, 20 symptoms,
35 open questions; 630 citations resolve; quotes verified (one YouTube message is split across
string literals in source, quote correct); coverage 32 of 32 providers; no local customisations
(the fork's Hide Processing Details hides search status lines and tool-call blocks).

**Key findings.** **Privacy:** the `external`, `yandex`, `perplexity_search` and `microsoft_web_iq`
engines receive the user's name, id, email and role (or a signed token carrying them) on every
search regardless of `ENABLE_FORWARD_USER_INFO_HEADERS`; `external` and `yandex` also receive the
chat id. In native function-calling mode (the default) the model gets `search_web` and `fetch_url`
only while the composer toggle is on and decides itself whether to search. Legacy-mode engine
errors show only `[ERROR: Something went wrong while searching the web.]`; ten engines fail silently
with `[ERROR: No results found from web search]`. When every loaded page is empty the user sees an
embedding-failure message that points at the wrong cause. The domain filter does not cover
`fetch_url` or Attach Webpage and some engines ignore it. Admin save failures are silent. Azure is
missing from the admin engine drop-down.

**Gaps (condensed).** Live values of all 78 `web.*` keys and related task, YouTube and RAG keys;
environment-only fetch, redirect, timeout, user-agent, cache and forward-header settings; image
variant and Playwright location; live web-search and web-upload permissions; models' function-calling
modes, capabilities and default features; automations that search; provider contracts, billing and
data residency. **Privacy review needed** (platform owner and Privacy Office): identity forwarding to
four engines, chat-derived queries sent to outside services, browsers loading Google favicons for
results, no deletion of stored searches or attached-page collections. Behaviours to confirm (Kagi
with a domain filter, Exa block entries, a zero concurrency value hanging the loader, the Azure
save issue, Sougou's missing dependency, SSL pre-check skipping some pages, error and bot-check
pages embedded as content, `m.youtube.com` not detected). Organisational: who owns and rotates
provider keys, who approves the two permissions, the approved confirmation wording. Note for
`builtin-native-tools.md`: `web.fetch.max_content_length` is also an admin panel setting ("Fetch URL
Content Length Limit"). Two items referred as security-sensitive.

### workspace-tools-tool-servers-mcp-and-terminals.md

Status: complete on first pass, 1,528 lines, 143 message rows (12 quote flags, all benign: messages
joined at runtime, `{{label}}` slots, a browser `Error: ` prefix, an exception name filled in, a
Markdown escape), 18 symptoms; 724 citations resolve; no local customisations in scope (the fork's
Hide Processing Details hides tool-call details, which matters when diagnosing tool errors).

**Ground-truth defect found and fixed.** Valves are encrypted only when `ENABLE_VALVE_ENCRYPTION`
is on (default off); ground truth and `CLAUDE.md` said they are always encrypted. Verified and
corrected (VERIFICATION.md defect 5).

**Key findings.** An admin tool server or terminal without access grants is admin-only; new admin
terminals are saved switched off; a person's own tool servers need both **Direct Integrations** and
`features.direct_tool_servers` (both off by default) and are called from the browser (CORS, open
tab); MCP uses Streamable HTTP only, connects per message, 10-second handshake; with Redis the cached
tool-server descriptions never expire until an admin save or restart; the background description
fetch sends only a bearer key, so a server can pass **Verify** yet be missing from menus;
**Registration failed** and **Connection failed** hide the reason (debug log only); startup installs
packages only for admin-owned tools; while the Shell tab is open the model can read and type into
the shell.

**Gaps (condensed).** Which tools, servers and terminals exist with their grants and authentication
types; Direct Integrations and tool permissions; environment values (plugins, pip, offline mode,
timeouts, certificate checks, redirects, user-info forwarding, admin bypass, valve encryption);
Redis and process count; internet or package-index reachability; community sharing; proxy limits;
who may be granted Tools Access and who reviews tool code and packages; which external servers may
receive chat content that could include health information (Privacy Office); escalation contacts;
whether people may add their own servers. Behaviours to confirm in a test environment; several
items referred as security-sensitive.

### builtin-native-tools.md

Status: complete on first pass, 1,748 lines, 185 message rows (about 215 strings, all verified), 18
symptoms, 28 open questions; 786 citations resolve; coverage 53 of 53 tools. One row corrected in
the main loop (`web.fetch.max_content_length` is an admin setting, not environment-only;
VERIFICATION.md defect 6).

**Key findings.** **Chat History** tools are on for every model by default with no admin switch or
permission, and archiving a chat does not reliably hide it from them. Approval is all-or-nothing:
tools run with full access unless an admin enables Tool Permissions and the person chooses "Ask for
approval", which then pauses before every call; automations, channel replies and fired timers always
run with full access. The Files tools appear only on models with File Context off (not the default).
Timers fall under the Sub-agents switch (off in code; its label does not mention timers). In-browser
code runs can wait indefinitely on an unresponsive tab unless `WEBSOCKET_EVENT_CALLER_TIMEOUT` is
set. `delete_memory`, `delete_automation`, `delete_calendar_event` are permanent and
`replace_note_content` keeps no earlier version. 21 of the 53 tools can change data.

**Gaps (condensed).** Live values of every tool switch and permission, model defaults and per-model
tool groups, the default for Hide Processing Details, environment limits; whether Legacy function
calling is used; which outside services receive data through tools and whether each is approved for
health data (data steward and Privacy Office); chat retention and backups (chats keep every tool
input and output); who decides approval mode, sub-agents, timers, channels, automations, user
webhooks; behaviours to test (ask-user in temporary chats, duplicate timer firing on SQLite with
several processes, timers that never finish after a restart, no screen to list or cancel timers,
default-calendar choice, partial approval when switching to Full access, question timeout ignored
for saved chats). Code discrepancies: `notify` matches only ids, the Calendar group description
mentions a listing tool that does not exist. Two items referred as security-sensitive.

### memories.md (continued after the reboot)

Status: sections 1 to 9 by the first researcher (interrupted by a usage limit and then the host
reboot), 10 to 14 appended by a continuation agent; 1,415 lines, 59 message rows (about 89
strings, all verified), 11 symptoms; 533 citations resolve. One correction under rule 21
(VERIFICATION.md defect 7). No local customisations in scope.

**Key findings.** Memory tools receive refusals as `{"error": "{status_code}: {detail}"}`; a batch
with one invalid operation saves none of them; the review prompt shows the literal
`"type":"user|context"`, and a model that copies it has its whole answer refused with only a debug
log line; several failures show no message (a failed list load looks like having no memories, a
refused **Remove** closes the dialog with the memory still shown, a failed **Clear memory** shows
nothing, a failed embedding on **Add** leaves the dialog open and each retry saves another copy);
people cannot export their memories (Data Controls exports chats only); on SQLite an admin can
download the whole database, which contains everyone's memories.

**Gaps (condensed).** Live `memories.*` settings (including whether background review is on),
`features.memories` defaults and group values, relevance threshold, models with memory off, tool
approval mode, the Hide Processing Details default, admin export and database engine, log levels;
providers, embedding engine and vector store; event destinations. **Privacy (Privacy Office):**
whether health details may be stored in memories and whether users should be told, whether
providers are approved for that data, retention (no expiry in code), who removes memories of deleted
accounts, admin access policy, backups, copies outside the memory table (chat tool entries,
webhooks, audit log, provider), whether on-screen viewing satisfies an access request. Two items
referred as security-sensitive.

### functions-pipes-filters-actions-and-pipelines.md (continued after the reboot)

Status: sections 1 to 9 by the first researcher, 10 to 14 appended by a continuation agent; 1,765
lines, 119 message rows (129 distinct strings, all verified), 17 symptoms; 784 citations resolve.
Two corrections under rule 21 (section 5.3, import carries the whole `meta` object; section 5.6,
`Error fetching valves` versus `No valves`), made by the continuation agent and not yet re-checked
in the main loop (Phase 4). `CLAUDE.md` refined from this research (start-up installs requirements
only for active functions and admin-owned tools, `backend/open_webui/utils/plugin.py:465-480`,
verified). Product defect 10 (missing `toast` import) verified.

**Key findings.** Valves can report success without saving when the database write fails; the
Pipelines upload always shows `Something went wrong :/` and hides the server's reason; the Filter
starter code, saved unchanged, blocks chats from the third question with `Conversation turn limit
exceeded. Max turns: 4`; a function whose code fails to load is switched off automatically during
an ordinary request; the on/off switch fails silently; **Import JSON** reports success even when
every function failed. In scope the fork changes only the default name; Hide Processing Details
hides function status lines and Inline Citations off removes `[n]` markers from pipe text.

**Gaps (condensed).** Production host; whether a Pipelines server runs and where; installed
functions and Event functions and where they send data; live switches and stored settings; worker
count and Redis; outbound internet or package-index access; proxy time limits; whether a turn limit
is intended; escalation contact; whether tier 1 can see admin pages or logs; sharing to
openwebui.com; who reviews installed functions for privacy (they receive personal data); whether
some filters are mandatory. Behaviours to confirm in a test environment. Four items referred as
security-sensitive.

### prompts-and-skills.md (continued after the reboot)

Status: sections 1 to 5.15 by the first researcher, the rest appended by a continuation agent
(section 5 gained skills workflows 5.16 to 5.27); 1,982 lines, 87 message rows (101 strings, all
verified), 21 symptoms; 791 citations resolve. Two corrections under rule 21 (skills picked from
`/` versus `$` mentions; VERIFICATION.md item 9, aligned in the composer document as a precision
note). No local customisations in scope (Hide Processing Details hides `view_skill` calls).

**Key findings (read from code).** A model's default skills are added to every message even when
the person switches them off in the Integrations menu; a `$` mention anywhere in a chat keeps
sending that skill in full on every later message; placeholders such as `{{USER_NAME}}` inside a
skill are never filled in; saving re-applies sharing with the saver's own permissions; the prompt
version-comparison route can never be reached (declared after a catch-all route); in channels,
choosing a prompt from `/` inserts a `$command` chip; skill JSON import reports success even when
every entry failed; the prompt history list sends every author's email to anyone who can read the
prompt.

**Gaps (condensed).** Live permission values, community sharing, prompt suggestions, webhooks and
event functions; counts of prompts and skills, public ones (including those made public by the
access-grant migration), ones owned by deleted accounts, switched-off prompts still holding
commands; model default skills not shared with the model's users; native-mode models; whether
prompt or skill text holds personal or health data; deployment switches and backups; whether staff
may share to openwebui.com (sends the owner's name and email); who arbitrates command and skill
names; privacy-incident route and contacts; naming conventions; whether authors' emails in history
are acceptable. One item referred as security-sensitive (what Skills Access allows).

### notes.md

Status: complete on first pass (the researcher was doing final heading checks when the fifth usage
limit hit; no final summary arrived), 1,526 lines, 61 message rows, 18 symptoms, 23 open questions.
Ground truth refined from its section 14 (timestamp units: nanoseconds in automations, calendar,
channels, messages and notes; seconds elsewhere; verified).

**Key findings (from its At a Glance).** Notes are rich-text documents separate from chats; both
`notes.enable` and `features.notes` are on in code, but sharing needs **Notes Sharing** (off) and
public sharing **Notes Public Sharing** (off), so with defaults only admins can share; admins can
open, edit and delete any note; the body saves half a second after the last edit **only through the
live websocket connection**, with no save button and no version history; deletion is permanent and
Shift skips confirmation; a read-only share is hidden by the list's default **Write** filter.

**Gaps (condensed).** Live note switches and sharing permissions; whether staff should share notes
and whether public sharing is acceptable; admin bypass; process count and websocket manager (real-
time collaboration across workers); file limits; event destinations (they receive note titles and
content); production host for note links; behaviours to test (offline edits, body from an address,
images after an AI rewrite and in PDF downloads, undo after an AI rewrite, attachments for
collaborators, edits racing a rejoin, large notes); backups and recovery of deleted notes; privacy
escalation route; clean-up of side chats and attachments left by deleted notes; upstream intent of
an unused AI menu. Three items referred as security-sensitive.

### channels-and-direct-messages.md (continued after the limit)

Status: sections 1 to 9 by the first researcher, 10 to 14 appended by a continuation agent; 1,649
lines, 68 messages (44 checkable quotes verified), 15 symptoms; 658 citations resolve. Three
corrections under rule 21 (VERIFICATION.md item 10). Two ground-truth refinements verified and
applied (`channel_file` timestamps are seconds; permission defaults fall back to code defaults
when the caller passes none). Fork effects: the tab title uses the app name; Hide Processing
Details applies to channel model replies; fallback pictures; uncommitted shared chat components
reach channels.

**Key findings.** Group channels and direct messages created from the screens carry no access
grants, so notification-target messages are not sent for them; several likely upstream interface
defects (empty error pop-ups on **Edit Channel** update and delete, webhook posts shown as sender
`Webhook` in **Pinned Messages**, a reaction tooltip naming only three of four people,
`[object Object]` for a refused webhook picture, `Copied` on failed copies).

**Gaps (condensed).** Whether `channels.enable` is on in production and whether channels are meant to
be offered; live settings including environment-only channel permission and profile-image
settings; database engine (deleting a channel removes webhooks and file links only where cascades
are enforced); multi-worker behaviour; event destinations receiving channel text; whether any trace
records who deleted a message; channels whose creator's account is gone; deployment of working-tree
changes; escalation; which model providers receive channel threads. **Privacy Office:** whether
admins may read private conversations, retention of message rows after deletion, telling users that
mentioning a model sends the thread to its provider and that prompt variables such as
`{{USER_EMAIL}}` are shared with the channel. Two items referred as security-sensitive.

### audio-speech-to-text-and-text-to-speech.md (continued after the limit)

Status: sections 1 to 9 by the first researcher, 10 to 14 appended by a continuation agent; 1,561
lines, 86 message rows (57 user-facing, 29 log or console lines; 98 checkable quotes verified), 15
symptoms; 660 citations resolve. Three corrections under rule 21 (VERIFICATION.md item 11; two
verified in the main loop). No local customisations in scope.

**Key findings.** The admin Audio save has no error handler (refusals and failed Whisper model
loads show nothing; "Settings saved successfully!" simply never appears); a new Whisper model name
is stored before the model loads, so a failed load leaves a setting that breaks transcription after
a restart; if Kokoro fails to load when a call starts the user sees "Permission denied when
accessing media devices"; speech failures during a call show nothing and leave the call waiting;
"Open WebUI: Server Connection Error" keeps the upstream name (licence-protected); every key box on
the admin page is required, so a keyless OpenAI-compatible service cannot be saved; debug-level logs
contain transcripts and the browser console holds transcripts, answer sentences and camera stills.

**Gaps (condensed).** Production address and whether it is served over HTTPS (browsers allow the
microphone only on secure pages); full or slim image; live engines, models, voices and limits;
speech permissions; proxy upload limits; log access, retention and debug use; event destinations;
support contacts. **Privacy:** retention of cached recordings, transcripts and generated speech (the
code deletes none), backups and who may clear them; which outside services receive audio or text
and whether each is approved for possible health information; transcription of attached
recordings with `chat.stt` off; browser speech services; Kokoro model source and caching; identity
headers to speech services. Two items referred as security-sensitive.

### image-generation-and-editing.md

Status: complete on first pass, about 1,335 lines, 64 message rows (105 checkable quotes all
verified), 15 symptoms; 437 citations resolve; no local customisations in scope (Hide Processing
Details hides progress lines and tool entries). Cross-document defect found and corrected in the
pipeline document (VERIFICATION.md item 12); ground truth's cache row refined.

**Key findings.** Generated pictures are stored through the storage provider as
`generated-image.<ext>` file records (the cache folder is unused); the prompt is stored with every
picture, and for Gemini edits the full source pictures too, for ComfyUI the whole workflow; both
image switches are off by default; there is no separate edit permission, and editing in chat also
needs the Image Generation switch; admins skip the permission but not the switches; users cannot
choose size or model; a blank edit model is sent as an empty name and the Gemini Base URL has no
built-in address; failures mostly show `Something went wrong :/` or only an HTTP reason phrase as
`[ERROR: {error}]`; no time limit unless `AIOHTTP_CLIENT_TIMEOUT` is set; native tools write no
`chat_file` row (shared-chat viewers may not load those pictures; to test); `image.generated` and
`image.edited` events carry the user's id, name, email, role and the first 300 characters of the
prompt; the session-pool docstring claims connection limits the code does not apply.

**Gaps (condensed).** Live switches, engines, models, sizes, steps, prompt generation, permission
values, model capabilities and function-calling modes, environment values; which outside service
production uses and under what agreement; proxy limits; event subscribers; whether the cache folder
holds pictures from older releases; the Gemini address; behaviours to test. **Privacy (data steward
and Privacy Office):** whether sending prompts and pictures to the engines is acceptable for content
that may include health information; retention of stored prompts and pictures; whether the feature
is offered at all. Two items referred as security-sensitive.

### code-execution-and-interpreter.md

Status: complete on first pass (the researcher was re-reading for accuracy when the sixth usage
limit hit; no final summary arrived), 1,232 lines, 60 message rows, 14 symptoms, 31 open questions.
Detailed harvest from its section 14 (organisational and live values; security-sensitive; behaviour
not established from code; discrepancies and upstream quirks) to be completed in Phase 7.

**Key points (from its At a Glance).** Two features: **code execution** (the **Run** button on a
Python block) and the **code interpreter** (the model writes and runs code during a reply), each
with its own engine setting in Admin Settings › Code Execution; the **Run** button has no per-user
permission, only the admin switch; by default the code interpreter is the native `execute_code`
tool; in-browser runs stop at 60 seconds; in-browser code reads chat attachments from
`/mnt/uploads/` and writes files there; the `pyodide` engine keeps code and files in the browser,
while the `jupyter` engine sends them to the configured server (privacy question for production).

### automations-calendar-and-timers.md

Status: complete on first pass (the researcher had passed all four checkers and was running the
absolutes audit when the limit hit), 1,714 lines, 87 message rows, 15 symptoms, 46 open questions.
Section 14 groups: live configuration; organisational and privacy questions; behaviour to confirm;
discrepancies in the code; security-sensitive questions.

**Key points (from its At a Glance).** An automation is a saved prompt run by a chosen model on an
iCalendar recurrence rule; access needs the site switch (on in code) and, for non-admins, the
`features.automations` permission (off by default); schedules are read in the owner's stored time
zone (reported by the browser at each visit); one background loop runs in every server process (due
timers every second, due automations every `SCHEDULER_POLL_INTERVAL` seconds); runs act as the
owner with full tool access and no approval; the calendar gives everyone a `Personal` calendar and a
read-only **Scheduled Tasks** view; timers are hidden chats that re-prompt their chat when due. The
area matches upstream; the fork only changes notification titles to the site name.

### evaluations-feedback-and-analytics.md (repaired)

Status: sections 1 to 13 by the first researcher (stopped by the sixth usage limit inside 13.5),
13.5 completed and section 14 appended by a repair agent; 1,222 lines, 61 message rows (62 checkable
quotes verified), 21 symptoms, 51 open questions; 610 citations resolve. Two minor corrections
(VERIFICATION.md item 13).

**Key points.** Each rating stores a copy of the conversation; the audit log, when set to record
request bodies, would keep the first 2,048 bytes of every feedback save (feedback routes are not
skipped by default); the leaderboard shows the top five feedback tags while the analytics model
window shows the top ten chat tags; **Feedback Details** may error on a row without a conversation
copy; the arena picks from every model on the server (referred as security-sensitive).

**Gaps (condensed).** Whether analytics is on; message rating and **Allow Rate Response** values;
arena configuration and access lists; community sharing; tags generation and its task model; event
destinations; admin role holders; several environment switches; production host, server time zone,
workers, Redis, providers, live name, deployment of working-tree changes, test environment.
**Privacy and retention:** whether storing a conversation copy with each rating is acceptable and
whether people should be told; who reviews feedback; whether admins may open raters' live chats;
export handling; feedback retention and backups; removal of deleted accounts' feedback; requests to
remove a rating; webhook destinations; audit log level. Four items referred as security-sensitive.

### admin-settings-panels.md

Status: complete on first pass, 1,729 lines, 106 message rows (101 checkable fragments verified),
16 symptoms; 712 citations resolve; coverage 18 of 18 panels. Ground truth and `CLAUDE.md` gained a
verified navigation fact: admin settings and analytics open in the shared Settings window
(`/?settings=admin:<tab>`); the `/admin/...` paths only redirect.

**Key findings.** The real layout differs from the area brief: sign-up, default role and group,
API keys, JWT expiry and the pending overlay are on **Authentication**; banners, UI Translations,
Default Interface Settings and Events are on **General**; prompt suggestions are in **Models ›
Model Defaults**; the Database tab has no reset; there is no single webhook URL (the legacy value
becomes an event webhook at start-up). General and Authentication post the same 31 keys, so a stale
tab can undo the other's changes, and invalid values are dropped silently. Interface reports
success before the save finishes; Audio, Web Search, Code Execution and the last Documents step show
nothing on failure. Import writes rows only (no validation, no runtime rebuild, open browsers not
refreshed). The export contains secrets (and the environment OAuth values when OAuth persistence is
off). Admins can preset Hide Processing Details and Inline Citations for everyone through Default
Interface Settings. The response watermark is added only on copy. The update check compares with
upstream releases.

**Gaps (condensed).** Live values of every setting, `webui.url`, database engine, environment flags
(persistence, reset, admin export and analytics, update check and offline mode, plugins, slim image,
name), process count, data-handling rules for exports and downloads, fork update process, licence
exception, backups, event webhooks, automation limits. Two items referred as security-sensitive.

### notifications-webhooks-events-and-banners.md

Status: complete on first pass, 1,862 lines, 98 message rows (174 strings; 95 checkable fragments
verified, one assembled update string explained), 13 symptoms, 32 open questions; 890 citations
resolve. The event catalogue covers all 181 events with triggers, payload fields and personal data
(matched against `backend/open_webui/events.py` by script). Fork changes: the test-notification text
and three browser-notification titles use the app name. Product defect 11 verified (chat links lose
`/c/`).

**Key findings.** No email anywhere. `notification.test` and `notification.manual` are defined but
never published; `pipeline.valves_updated` fires on a valves read, not a save; `config.updated` is not
published by several saves. "Only when away" rarely fires (three minutes without a request or a
heartbeat, while any open tab sends a heartbeat every 30 seconds). Admin Events save errors always
show `Failed to save webhook`. Webhooks get one attempt with no retry, no delivery history and no
time limit by default; failures appear only in the server log. Withdrawing the user-webhooks
permission does not stop deliveries to saved targets. A legacy `WEBHOOK_URL` becomes a Default
webhook receiving every event; an invalid stored webhook disappears from the list and is deleted at
the next save. **Privacy:** generic JSON and Teams payloads carry the actor's name and email; with
all events selected a webhook receives the first 300 characters of every user message and the first
1,000 of every reply. Banners show only on the new-chat screen, load once per page load, and never
display their stored title. The update toast and What's New report upstream releases; closing What's
New with Escape does not record the version.

**Gaps (condensed).** Live user-webhook permission, admin webhooks and any migrated legacy address,
WebUI URL, banners, version check and offline mode, timeouts, heartbeat interval, plugins, instance
id, name, worker count, outbound access to GitHub and webhook services, licence metadata.
Organizational: which outside services may receive MedIT GPT data (Privacy Office); whether personal
webhooks are offered; whether the U of T Teams tenant still issues connector addresses; whether the
upstream update toast should stay on and whether MedIT GPT will publish its own release notes;
tier 1's view of admin webhooks; support contacts. Behaviours to test (duplicate calendar alerts
with several workers, deliveries after permission withdrawal). Two items referred as
security-sensitive.

### user-settings-and-personalisation.md

Status: complete on first pass, 1,281 lines, 65 message rows (169 backticked quotes verified), 15
symptoms, 30 open questions; 591 citations resolve; coverage 14 of 14 panels. Product defect 12
verified (Interface Save overwrites the personal default model).

**Key findings.** The fork's two switches, **Hide Processing Details** (`ui.hideProcessingDetails`,
default off) and **Inline Citations** (`ui.showInlineCitations`, default on), are committed; only
the reworded Hide Processing Details description and the language-matching change in
`src/lib/i18n/index.ts` are uncommitted; the other 63 locales carry the two keys as empty strings, so
the labels show in English everywhere. Refused saves look successful (the server silently drops
changes the person lacks permission for, and the success toast still appears, including
"Default model updated"). iframe Sandbox Allow Forms and Compress Images in Channels show on by
default but behave as off until saved. The site default language may not apply (the browser's own
language is saved first; `ui.default_locale` is never read at runtime; live test needed). Theme and
language are per browser; changes are not pushed to other open windows. Saving valves rewrites the
whole settings object. The user menu's Keyboard item never shows.

**Gaps (condensed).** Admin preset contents (whether the two fork switches are preset); production
permissions and switches; version check, offline mode, easter eggs (on in code), default locale,
name; whether production includes the working-tree changes and how upstream releases are adopted
(About's "available!" refers to upstream); who may look up or reset a person's stored settings (no
reset control exists); retention of location, gender, birth date, bio and user variables;
**Privacy Office:** whether users may send usage statistics to the Open WebUI Community site;
upstream links on About and General. Three items referred as security-sensitive.

### error-messages-backend-chat-content-and-features.md (continued after the limit)

Status: sections 1 to 9 and 10.1 to 10.12 by the first researcher, 10.13 to 10.36 and 11 to 14 by a
continuation agent (which reused the first researcher's extraction script); 1,589 lines; section 10
has 562 rows (about 581 distinct texts; 495 rows point to an area document, the rest are covered only
here); 408 checkable quotes verified; 800 citations resolve. Retrieval is grouped by sub-package
(seven subsections) rather than one per file. Corrections and resolutions logged as
VERIFICATION.md item 14.

**Key findings.** Never-shown texts include `OpenAI API was not found`, the Anthropic **Verify**
refusal (replaced by `Open WebUI: Server Connection Error`), the slim Chroma message, the PaddleOCR-VL
configuration text, the openGauss length checks, `retry count exceeded`, several loader and
embedding texts in helpers nothing calls. Several search providers log failures and return no
results (Exa, External, Microsoft Web IQ, both Perplexity engines, Ollama, Sougou, Yandex,
Firecrawl), so failures look like "no results". Rows 10.1 to 10.12 pass the checkers but were not
re-traced line by line.

**Gaps (condensed).** Production upload limits and extensions, image variant, every engine and
connection in use (which decide which rows can occur); log access and retention; escalation contact;
status lines pending the in-chat status catalogue; front-end wrapper cross-checks pending the
front-end catalogues; out-of-scope helpers whose texts reach chat users. Four items referred as
security-sensitive.

### error-messages-backend-identity-admin-and-platform.md (continued after the limit)

Status: sections 1 to 9 and 10.1 to 10.5 by the first researcher, 10.6 to 10.23 and 11 to 14 by a
continuation agent; 1,072 lines; section 10 has 282 rows (244 distinct texts, 240 also in an area
document); 702 citations resolve; coverage of all 73 constants-enum members complete (table in
section 4.6). Two benign quote flags (an illustrative log line built from two pieces; the composed
`Search query generation is disabled`). Corrections logged as VERIFICATION.md item 15 (including a
correction to the SSO document).

**Key findings.** Texts the code cannot show: unused constants and the never-read `MESSAGES` and
`WEBHOOK_MESSAGES` classes, `OpenAI API was not found`, two `Invalid token` sites, `Toolkit not found`,
`Dynamic client registration failed` (bare form), the server's `Please enter a valid URL`, the
stop-task 404, `No Redis URL provided`, `SCIM is not enabled` (the router is mounted only when SCIM is
on), `Event call timed out…` without `WEBSOCKET_EVENT_CALLER_TIMEOUT`. In scope only `env.py` differs
from upstream (the default name), and no message text changed.

**Gaps (condensed).** Behaviour to confirm (how 422 validation errors display, unknown addresses
when built pages are served, `/health/db` failures, formatter wording); production values of every
setting and which optional parts are in use (Redis, PostgreSQL, vector store, image variant, LDAP,
SCIM, SSO provider, trusted headers, token exchange, back-channel logout, licence key, analytics,
personal webhooks, Pipelines, terminal and MCP OAuth servers); log destination and readers; backups;
whether tier 1 has a read-only admin view; support contacts. Several items referred as
security-sensitive.

### error-messages-frontend-chat-and-navigation.md (continued after the limit)

Status: title and At a Glance by the first researcher, sections 1 to 14 by a continuation agent
(which reused the first researcher's harvest scripts); 1,205 lines; section 10 has 374 rows quoting
383 distinct fixed texts plus 12 server-text patterns; all 453 harvested pop-up and dialog call
sites cited; 349 of 383 texts are also in an area document; 611 citations resolve. The agent ran
`run_all_checks.sh`, which regenerated `ai/*.json` (derived files; harmless).

**Key findings.** Success pop-ups that do not check the result (`Copied shared chat URL to
clipboard!` before the link exists in Safari, several `Copied` pop-ups, `Thanks for your feedback!`,
import and share `Saved` pop-ups, `Settings saved successfully!` on some tabs); failures that show
nothing (OneDrive picker, uploads that return nothing, playground runs, unreachable terminal
servers, clearing a status); blank pop-ups that print a missing `error.message`; two pop-ups for one
failure (status save, failed download); texts no user can reach (the unused Google Drive path, the
character-card helper, `Cannot create an empty note.`, commented-out lines).

**Gaps (condensed).** Hosting (proxies, workers, Redis) behind connection-lost and Backend Required
symptoms; live admin translation overrides (`ui.i18n`) that may change any wording; live name,
token expiry, upload limits, version check; whether users should see upstream GitHub and Discord links
on the Backend Required screen and update card, and which MedIT GPT contact replaces them; whether the
onboarding sentence "does not make any external connections" is true here; centrally provided tool
or terminal servers; library and browser behaviour. Two items referred as security-sensitive.

### in-chat-status-and-response-messages.md (continued after the limit)

Status: sections 1 to 5.4 by the first researcher, 5.5 to 5.11 and 6 to 14 by a continuation agent
(reusing the first researcher's harvest); 1,215 lines; section 10 has 101 rows covering 139 distinct
texts; 65 checkable quotes verified; 530 citations resolve. Three corrections under rule 21
(VERIFICATION.md item 16, pending main-loop check).

**Key findings.** The tool-card summaries in `structuredOutput.ts` (`Tool Approval Needed`, `Tool
Executed`, `Executing...`, `Preparing...`) are never displayed (confirms the front-end catalogue).
Hide Processing Details is browser-only; part committed on `uoft`, part uncommitted (the
`StatusItem.svelte` change is only a type comment; the working tree rewords the help text and brings
`Thinking...` back after **Allow** via `Chat.svelte`). No provider time limit by default, so a stuck
reply waits until Stop or reload. `No sources found` can also mean retrieval failed (logged, not
shown). `execute_code` shows a green tick even when the code raised; a tool call cut off by Stop also
shows a green tick; Stop leaves the visible status line shimmering. Requests refused before work
begins may leave no saved message after reload. A streamed reply that fails partway still triggers
the normal finished notice.

**Gaps (condensed).** Live interface preset (whether Hide Processing Details is on for everyone),
tool permissions, web search, image generation, compaction and query generation settings, timeouts
and tool-iteration limits; providers in use (their error wording); installed add-ons; worker count
and Redis; escalation route; whether user guidance should explain the licence-protected "Open WebUI"
wording in the connection error; whether the uncommitted Hide Processing Details changes will be
committed; acceptability of loading web-search icons from Google's favicon service. One item referred
as security-sensitive.

### configuration-environment-variables-bootstrap.md (continued after the limit)

Status: sections 1 to 7.2 by the first researcher, 7.3 to 7.17 and 8 to 14 by a continuation agent;
1,005 lines; 457 distinct variable names catalogued (238 from the inventory scope, 20 the inventory
pattern cannot catch, 170 environment-only names read in `config.py`, 29 used only by start scripts,
the image, the front-end build or proxies) plus 12 Docker build arguments; coverage of the scope
complete; 65 message rows. One correction under rule 21 (VERIFICATION.md item 17). The quote checker
now includes root files (mistake 12).

**Key findings.** Under `start.sh`, setting only the deprecated `WEBUI_JWT_SECRET_KEY` stops
start-up; `WEBUI_BUILD_VERSION`, `ENABLE_REALTIME_CHAT_SAVE`, `TRUSTED_SIGNATURE_KEY` and the
`USE_TIKTOKEN_ENCODING_NAME` build argument are set or read but unused; `CUSTOM_NAME` and
`LICENSE_KEY` contact upstream openwebui.com servers at start-up and either can replace the MedIT GPT
name; the version check calls GitHub; `ENABLE_FORWARD_USER_INFO_HEADERS` sends names, ids, emails and
roles to model providers; OpenSearch certificate checking defaults to off; no overall HTTP timeout by
default; production front-end builds strip `console.log`, `console.debug` and `console.error`; code
comments disagree with the code on pool limits and the calendar look-ahead; `.env` never overrides
the real environment (python-dotenv 1.2.2 locally; production version TO BE CONFIRMED).

**Gaps (condensed).** Every production value (start method and where the environment is defined,
secret-key source and consistency across workers, workers, replicas, Redis, websocket manager,
database, data volume, vector store, storage provider, identity switches, privacy switches, log
level and format, audit level, log shipping and retention, telemetry export, proxies, CA bundle,
offline mode, licence key, custom name, version check, CORS origins, security headers, product name,
licence exception). Several items referred as security-sensitive.

### error-messages-frontend-admin-workspace-and-settings.md (continued after the limit)

Status: sections 1 to 10.2 by the first researcher, 10.3 to 10.18 and 11 to 14 by a continuation
agent; 1,352 lines; section 10 has 432 rows (about 427 distinct texts; 364 of the continuation's 386
rows point to an area document); 656 citations resolve. Three cross-document corrections in
`admin-settings-panels.md` verified and applied (VERIFICATION.md item 18); the quote checker now
unescapes `\|` (mistake 13). Fork changes in scope: `OnBoarding.svelte` shows the product name.

**Key findings.** Green pop-ups that prove nothing (admin Connections, admin Interface and personal
Audio report "saved" before the save finishes; the Personalization Save stores nothing; Documents,
Web Search and Code Execution report "saved" when a failure carries no server reason; batch imports
report success when every entry failed). Failures with no message (admin Audio, Web Search, Code
Execution, parts of Documents, on/off switches, shortcuts, knowledge-base reset). Save buttons stuck
disabled until reload (Images after invalid JSON, the connection dialog after invalid headers).
Misleading texts ("cannot be undone" on Archive All; `Invalid JSON file` on a network failure;
Functions Import From Link always reports success). Never-shown texts include `Name and description
are required` (missing `toast` import; product defect 10).

**Gaps (condensed).** Contacts and escalation; production host and proxy; live feature switches;
local policy on community sharing, stats sync and plugin funding links; licence exception and
whether upstream licence notices should show; admin wording overrides; log retention; process count;
production product name.

### configuration-persistent-settings-a-to-o.md (continued after the limit)

Status: sections 1 to 6 by the first researcher, section 7 (23 namespace tables) and 8 to 14 by a
continuation agent reusing the first researcher's parser; 1,189 lines; **199 keys** catalogued (one
row each, script-checked; 159 label citations match `en-US`); coverage of the shared 405-key scope
complete. Two corrections under rule 21 (VERIFICATION.md item 19).

**Key findings.** 27 keys are inert rows no code reads (the Google, Microsoft, GitHub and Feishu
sign-in keys, four OAuth timing and method keys, the Google Drive and OneDrive picker keys); five
OAuth fields appear on the screen but are not used for sign-in; 39 keys have no screen; General and
Authentication each re-save the other's keys as loaded; General, Authentication, Interface and
Documents saves publish no `config.updated` event; `notes.enable` does not gate the notes API (the
`features.notes` permission does); `folders.max_file_count` is checked only in the browser;
`ldap.server.label` is read but unused; invalid JWT expiry, default role and channel response mode
values are dropped silently.

**Gaps (condensed).** Live values of all 199 keys and whether rows exist; persistence, reset and
migration switches; process count and Redis; SSO provider and its variables; legacy rows from before
the per-key split; slim image; event subscribers (config events carry the admin's name and email).
Several items referred as security-sensitive.

### configuration-persistent-settings-r-to-w.md (continued after the limit)

Status: title and At a Glance by the first researcher, sections 1 to 14 by a continuation agent;
1,017 lines; **206 keys** (`rag` 76, `web` 78, `ui` 20, `task` 19, `subagents` 7, and one each for
`tool_server`, `terminal_server`, `user`, `users`, `webui`, `webhook_url`), script-checked one row
each; with the a-to-o catalogue's 199 the total is 405, matching ground truth; 1,161 citations
resolve; coverage of both configuration scopes complete (a table of the 65 `USER_PERMISSIONS_*`
seeds was added to 7.13). Cross-document refinements logged as VERIFICATION.md item 20.

**Key findings.** Saving Documents re-saves every `web.*` key as loaded (can undo a Web Search
change); a failed reranker load saves hybrid search as off with only a log line; `ui.default_locale`
does nothing; `null` web-loader keys fall back to the environment; the embedding model, reranker and
OAuth 2.1 tool-server clients are rebuilt only at start-up or on save and only in the process that
handled the save; terminal servers are prepared at start-up only when a tool server exists; invalid
JSON in `TERMINAL_SERVER_CONNECTIONS` or a non-positive `EXA_MAX_CONTENT_LENGTH` stops start-up;
search errors say a value was not "found in environment variables" although it comes from stored
settings; nine keys have no screen and four have no save path at all (`rag.tiktoken_encoding_name`
and three Azure AI Search keys). The new-chat model order: address, folder, the tab's remembered
choice, the user's own default, then the admin default.

**Gaps (condensed).** Live values of all 206 keys; slim image, workers, replicas, Redis; persistence
and reset switches; `webui.url` and `DEFAULT_LOCALE`; who the platform maintainer is; whether a legacy
`WEBHOOK_URL` created a Default webhook; behaviours to test. One item referred as security-sensitive.

### backend-architecture-and-request-lifecycle.md (continued after the limit)

Status: title and At a Glance by the first researcher, sections 1 to 14 by a continuation agent;
1,681 lines; tables of all 31 routers and all 39 top-level endpoints (coverage complete); 103 message
rows; 11 symptoms; 695 citations resolve; two At a Glance inaccuracies corrected under rule 21.
`CLAUDE.md`'s start-up order and mount list match the code. Cross-document corrections logged as
VERIFICATION.md item 21; product defect 13 verified.

**Key findings.** A mistyped `AUDIT_LOG_LEVEL` stops start-up (defect 13). Under uvicorn, probes
never see `Startup not complete` (the port opens only after start-up). The session check's cookie
deletion on a 401 may not reach the browser (FastAPI discards the injected response when a
dependency raises; to confirm). The shared HTTP client's docstring promises connection limits the
code does not apply, and there is no overall time-out by default. An API-only start deletes the
top-level files in `STATIC_DIR` even without a build to copy from. Open tabs reload after a
deployment only if the version or `DEPLOYMENT_ID` changes, and the fork keeps the upstream version.

**Gaps (condensed).** Production host, run method, workers and instances, proxy (websocket
upgrades, caching, headers, rate limits), which probe the load balancer uses, tier 1's access to
monitoring, environment values, custom user headers, licence key, upgrade ownership, support
contacts, whether `DEPLOYMENT_ID` is set, cookie flags. Several items referred as security- or
privacy-sensitive.
