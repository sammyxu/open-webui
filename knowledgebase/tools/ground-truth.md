# Ground Truth Verified Directly Against the Repository (2026-10-07)

Authoritative facts for the MedIT GPT knowledgebase, checked by reading the files cited, at
**Open WebUI v0.11.4** on branch `uoft`, commit `aeed1832c` (`git describe`: `v0.11.4-3-gaeed1832c`),
working tree of 2026-10-07. Where a fact is *not* determinable from the repository this file says so
explicitly. Do not fill those gaps with assumptions. Every researcher and writer reads this file
first; contradicting it requires evidence recorded in `VERIFICATION.md`.

## Version and Identity

- **Product name in this deployment: MedIT GPT.** Default `WEBUI_NAME` is `MedIT GPT`
  (`backend/open_webui/env.py:951`); front-end `APP_NAME` is `MedIT GPT` (`src/lib/constants.ts:7`).
  The upstream product is **Open WebUI**; upstream appends " (Open WebUI)" to any custom name, and
  the fork removed that suffix. `WEBUI_NAME` is an environment variable, so the live name is
  **TO BE CONFIRMED** for production (it is not a persistent setting).
- **Version 0.11.4** (`package.json:3`). The backend reads it from `package.json`
  (`backend/open_webui/env.py:143-151`), or from the installed package metadata when started with
  `open-webui serve`; the Python package version is derived from `package.json`
  (`pyproject.toml:175-177`). `CHANGELOG.md` dates 0.11.4 to 2026-09-21.
- **Repository.** `origin` is a personal GitHub fork; `upstream` is `open-webui/open-webui`. `main`
  equals `upstream/main` at the v0.11.4 merge (`8bd8b4fac`). `uoft` adds three commits
  (`402a737ba`, `146c436f8`, `aeed1832c`). Upstream branch conventions: work lands on `dev`,
  releases on `main`, tags `v<version>`.
- **Working tree.** Uncommitted changes exist in eleven files (chat message rendering, tool-call
  display, i18n loading, the `en-US` translation file and the Pyodide lock file). Citations are to
  the working tree as of this date.
- **Fork changes** (`git diff main...uoft`): the product name; U of T logos and favicons
  (`static/static/`, `static/favicon.png`, `backend/open_webui/static/`); web manifests and
  `static/opensearch.xml` renamed; two per-user Interface settings, **Hide Processing Details**
  and **Inline Citations** (`showInlineCitations`, `hideProcessingDetails` in the
  `InterfaceSettings` model, `backend/open_webui/models/users.py:99-100`; UI in
  `src/lib/components/common/InterfaceSettings.svelte`); the test-notification text uses the app
  name (`backend/open_webui/utils/notifications.py`). No database migration is local to the fork.
- **Licence.** `LICENSE` §4 restricts changing "Open WebUI" branding except for (i) deployments
  with no more than 50 end users in any rolling 30 days, (ii) written permission from the copyright
  holder, or (iii) an enterprise licence. The maintainer has stated the deployment qualifies;
  **which exception applies is TO BE CONFIRMED** (it is not recorded in the repository).

## Navigation Facts (Added 2026-10-10)

- **Admin settings and analytics open inside the shared Settings window.** `/admin/settings`,
  `/admin/settings/<tab>` and `/admin/analytics` are redirect pages that open
  `/?settings=admin:<tab>` (analytics returns to `/admin` when switched off)
  (`src/routes/(app)/admin/settings/[tab]/+page.svelte:6-10`;
  `src/routes/(app)/admin/analytics/+page.svelte:6-12`). Some tab ids differ from their titles
  (`db`, `web`, `code-execution`); see `../reference/admin-settings-panels.md` section 2.
- Personal settings open in the same window (`/?settings=<tab>`); see
  `../reference/user-settings-and-personalisation.md`.

## Tenancy

- **Single tenant.** There is no organisation, tenant or site table: one running instance is one
  MedIT GPT. Groups (`group`, `group_member`) organize users for permissions and sharing; they are
  not tenants. There is no per-tenant theme or template.

## Accounts and Access

- **Roles are exactly `admin`, `user` and `pending`** (`backend/open_webui/routers/auths.py:772`,
  `:1283`). `pending` accounts exist but cannot use the application until an admin changes the role.
- **New accounts get the `ui.default_user_role` setting**, seeded from `DEFAULT_USER_ROLE`, code
  default `pending` (`backend/open_webui/config.py:1720`, `:3096`;
  `backend/open_webui/routers/auths.py:868`). **The first account ever created becomes `admin`**,
  and on the self-service sign-up path sign-up is then switched off (`ui.enable_signup` set to
  `False`) (`backend/open_webui/routers/auths.py:874-879`). An admin can also be bootstrapped from
  `WEBUI_ADMIN_EMAIL` and `WEBUI_ADMIN_PASSWORD` when no users exist, which also turns sign-up off
  (`backend/open_webui/main.py:377-380`). *Refined 2026-10-07 from the reference research:* the
  **LDAP** path also makes the first account an admin but does **not** switch sign-up off
  (`backend/open_webui/routers/auths.py:663-667`).
- **Sign-up is refused** with `ACCESS_PROHIBITED` when users exist and either `ui.enable_signup` or
  `ui.enable_login_form` is off (`backend/open_webui/routers/auths.py:908-911`).
- **Authentication defaults in code** (live values are data, TO BE CONFIRMED): `WEBUI_AUTH` on
  (`backend/open_webui/env.py:751`); sign-up on (`backend/open_webui/config.py:1664`); login form on
  (`:1666`); token lifetime `JWT_EXPIRES_IN` `4w` (`:2466`, setting `auth.jwt_expiry`); user API keys
  off (`ENABLE_API_KEYS`, `:2454`); OAuth sign-up off (`ENABLE_OAUTH_SIGNUP`, `:2483`); show admin
  details to pending users on (`SHOW_ADMIN_DETAILS`, `:2170`).
- **Sign-in throttling:** 15 attempts per 180 seconds per email address; the refusal is HTTP 429
  with the text `API rate limit exceeded` (`backend/open_webui/routers/auths.py:91`, `:818-822`;
  `backend/open_webui/constants.py`). Without Redis the counter is per worker process.
  *Refined 2026-10-07:* the limiter counts every attempt, successful or not, in one-minute buckets
  and sums the current minute plus the previous three, so the **16th attempt within roughly three
  to four minutes** is refused (`backend/open_webui/utils/rate_limit.py:30`, `:79-109`).
- **Sign-out and token revocation need Redis.** Without a Redis client, revocation is not stored and
  every unexpired token stays valid (`backend/open_webui/utils/auth.py:276-288`, `:315-323`).
- **Role checks answer 401, not 403.** `get_verified_user` (role `user` or `admin`) and
  `get_admin_user` refuse with HTTP 401 and the `ACCESS_PROHIBITED` text `You do not have
  permission to access this resource. Please contact your administrator for assistance.`
  (`backend/open_webui/utils/auth.py:567-576`, `:625-631`; `backend/open_webui/constants.py`).
- **Pending users can sign in**; the app then shows the "Account Activation Pending" overlay with
  **Check Again** and **Sign Out** buttons, and optionally the admin's name and email
  (`src/lib/components/layout/Overlay/AccountPending.svelte:34-79`). Admins can replace its title
  and text (`ui.pending_user_overlay_title`, `ui.pending_user_overlay_content`).
- **Permissions add up across groups.** Default permissions live in the `user.permissions` setting
  (structure `DEFAULT_USER_PERMISSIONS`, `backend/open_webui/config.py:1940-2022`) with sections
  `workspace`, `sharing`, `access_grants`, `chat`, `features` and `settings`. A permission is granted
  if any of the user's groups grants it, otherwise the default decides
  (`backend/open_webui/utils/access_control/__init__.py:75-108`). **A group cannot take away a
  permission the defaults grant.** Admins skip permission checks at each call site. *Refined
  2026-10-10:* "the default" is the saved **Default permissions** only where the calling code passes
  them; otherwise the code and environment defaults apply (`backend/open_webui/utils/access_control/__init__.py:106-108`).
  One place where this matters was referred as security-sensitive (see
  `../reference/channels-and-direct-messages.md` section 14).
- **Admin visibility defaults** (environment-only, live values TO BE CONFIRMED): admins can open
  other users' chats (`ENABLE_ADMIN_CHAT_ACCESS`, default on, `backend/open_webui/env.py:371`) and
  see every workspace item regardless of sharing (`BYPASS_ADMIN_ACCESS_CONTROL`, default on,
  `backend/open_webui/config.py:2086-2092`). Model access control applies to non-admins unless
  `BYPASS_MODEL_ACCESS_CONTROL` is on (default off, `backend/open_webui/env.py:832`). *Refined
  2026-10-07:* it also applies to admins whenever `BYPASS_ADMIN_ACCESS_CONTROL` is off
  (`backend/open_webui/main.py:1150`; `backend/open_webui/utils/models.py:526-528`).
- **Any signed-in user can look up other users**: `GET /api/v1/users/search` returns id, name,
  email, role, bio, groups and whether each is active (`backend/open_webui/routers/users.py:137-161`;
  `backend/open_webui/models/users.py:309-316`). It is how sharing pickers find people.
- **Deleting a user is permanent** (no soft delete): group memberships, the user's chats (with their
  messages and share snapshots), the `user` row and the `auth` row are removed
  (`backend/open_webui/models/users.py:849-863`; `backend/open_webui/models/auths.py:228-239`).
  Files, knowledge bases, custom models, prompts, tools, notes, memories, folders, feedback, channel
  messages, automations and calendar data are **not** removed by that path. "Suspending" a user
  means setting the role to `pending`.
- **No account lockout.** Apart from the rate limit above there is no failed-login counter.
- **Single sign-on failures can show the password message.** A blocked email domain, a missing
  email or subject claim, or a failed code exchange all display `The email or password provided is
  incorrect. Please check for typos and try logging in again.` although the user typed no
  password (`backend/open_webui/utils/oauth.py:1889-2008`). *Refined 2026-10-07:* the same text
  also appears when the provider returns no user details at all (`backend/open_webui/utils/oauth.py:1941-1943`).
- **The "login form" switch only hides the form**; the server-side switch for password sign-in is
  the environment variable `ENABLE_PASSWORD_AUTH` (`backend/open_webui/config.py:1666`, `:1670`).
- **Group sync replaces membership.** When SSO, LDAP or trusted-header group management is on, a
  user is removed from every group not named in the identity provider's claim, including groups an
  admin assigned by hand. *Refined 2026-10-07:* nothing changes when the claim, LDAP attribute or
  header yields no groups (`backend/open_webui/routers/auths.py:693`, `:763-768`;
  `backend/open_webui/utils/oauth.py:1731-1736`), and for single sign-on, groups matching
  `OAUTH_BLOCKED_GROUPS` are exempt from removal. Despite the setting's description, blocked groups
  do not block anyone from signing in.
- **OAuth settings edited while not persisted** (`ENABLE_OAUTH_PERSISTENT_CONFIG` off, the default)
  change only the memory of the server process that handled the save and are lost at restart
  (`backend/open_webui/models/config.py:198-206`); provider registration (client id, secret,
  provider URL, redirect URI, scopes) always comes from the environment at startup.
- Password hashing is set by the environment variable `PASSWORD_HASH_ALGORITHM` (code default
  `bcrypt`; `argon2` supported); the production value is TO BE CONFIRMED.
- The detailed identity model (tables, sign-in paths, permission keys and their evaluation) is in
  the reference documents `authentication-and-sign-in.md`, `sso-oauth-oidc-and-scim.md` and
  `users-groups-roles-and-permissions.md`, and the Phase 0 sweep summary in
  `../reference/_research-notes.md`.

## Settings: Where a Value Comes From

- **Persistent settings** are rows in the `config` table, one per dotted key (`key`, JSON `value`,
  `updated_at`; `backend/open_webui/models/config.py:101-108`). `DEFAULT_CONFIG`
  (`backend/open_webui/config.py:2822`) lists **405 keys**: 404 dotted keys in 33 namespaces plus
  `webhook_url`. At startup only missing keys are inserted from environment-derived defaults
  (`backend/open_webui/models/config.py:240-266`), so **after first boot the stored value wins and
  changing an environment variable has no effect** on that key.
- **Exceptions.** `oauth.*` keys follow the environment unless `ENABLE_OAUTH_PERSISTENT_CONFIG=True`
  (default `False`, `backend/open_webui/config.py:3232`). `ENABLE_PERSISTENT_CONFIG=False`
  (`:3231`) makes every key environment-only and admin edits per-process. `RESET_CONFIG_ON_START=True`
  (`backend/open_webui/env.py:368`) wipes stored settings on every boot.
- *Refined 2026-10-11 (exceptions to "the stored value wins"):* `ui.default_locale` is stored but
  never read; `/api/config` sends the environment constant `DEFAULT_LOCALE` instead
  (`backend/open_webui/config.py:3086`; `backend/open_webui/main.py:2315`). Web-loader keys stored as
  `null` fall back to their environment variable (`backend/open_webui/retrieval/web/utils.py:1065-1068`).
  Some stored keys are inert (no code reads them); see
  `../reference/configuration-persistent-settings-a-to-o.md` section 14 and
  `../reference/configuration-persistent-settings-r-to-w.md` section 14.
- **Environment-only settings** (never stored): for example `WEBUI_NAME`, `WEBUI_SECRET_KEY`,
  `DATABASE_URL`, `REDIS_URL`, `VECTOR_DB`, `STORAGE_PROVIDER`, `ENV`, OAuth client registration.
- **Live values of every setting are data: TO BE CONFIRMED** for production.

## Data Stores

| Store | Default | Configured by | Source |
|---|---|---|---|
| Relational database | SQLite file `DATA_DIR/webui.db` (WAL mode) | `DATABASE_URL`, or the six `DATABASE_*` parts | `backend/open_webui/env.py:271-301`, `:330` |
| Vector store | Chroma at `DATA_DIR/vector_db` (`pgvector` in the slim image) | `VECTOR_DB` | `backend/open_webui/config.py:503-506` |
| Uploaded files | `DATA_DIR/uploads` | `STORAGE_PROVIDER` (`local`, `s3`, `gcs`, `azure`) | `backend/open_webui/config.py:150`, `:174` |
| Cache (models, audio, tool code; *refined 2026-10-10:* the `image/generations` folder is created but unused in v0.11.4, and generated pictures are stored through the storage provider as file records, `backend/open_webui/routers/images.py:54-55`) | `DATA_DIR/cache` | not configurable separately | `backend/open_webui/config.py:182` |
| Redis (optional) | none | `REDIS_URL`, Sentinel or Cluster settings | `backend/open_webui/env.py:381-455` |

- `DATA_DIR` defaults to `backend/data` (`backend/open_webui/env.py:228`); in the Docker image it is
  `/app/backend/data`, the volume mount (`docker-compose.yaml:18`).
- PostgreSQL is supported; **SQLCipher is not usable in v0.11.4** (a `sqlite+sqlcipher://` URL fails
  at import, `backend/open_webui/internal/db.py:244-248`, `:447`).
- Migrations: Alembic, 58 revision files, linear, head `d4c1a8e37b62`; they run when the config
  module is imported unless `ENABLE_DB_MIGRATIONS=False` (`backend/open_webui/config.py:81-82`).
- Tables: 39 defined in `backend/open_webui/models/`; legacy migration-only tables `chatidtag`,
  `document`, `config_old`; temporary `prompt_new`.
- **Which stores production uses is TO BE CONFIRMED.**

## Time, Storage and Logs

- Timestamps are stored as epoch integers. *Refined 2026-10-10:* the unit differs by table:
  **nanoseconds** (`time.time_ns()`) in the automation, calendar, channel, message and note models
  (`backend/open_webui/models/{automations,calendar,channels,messages,notes}.py`), **seconds** in the
  others (for example `backend/open_webui/models/access_grants.py:472`). Within the channel model,
  `channel_file` rows use **seconds** although the field comments say nanoseconds
  (`backend/open_webui/models/channels.py:863-864`). Check the unit per table before comparing dates. There is no server time-zone setting; each user's
  `timezone` is taken from their browser (`backend/open_webui/routers/auths.py:348-374`).
  Automations without a user time zone fall back to the server's local time.
- No academic or business calendar exists in the code.
- **Logs go to standard output only** (`backend/open_webui/utils/logger.py`). The optional audit log
  (`AUDIT_LOG_LEVEL`, default `NONE`, `backend/open_webui/env.py:1234`) writes `DATA_DIR/audit.log`
  and contains personal data. Log shipping and retention are **TO BE CONFIRMED**.

## Contacts That Exist in the Repository

- **None for MedIT GPT.** No email address, mailbox, phone number, ticket queue, service level,
  support URL or named team for this deployment exists anywhere in the repository. The only
  addresses in code are `example.com` placeholders and a test string.
- The interface links to **upstream** resources: `docs.openwebui.com` (about 115 links, mostly admin
  help), `github.com/open-webui`, a Discord invite and `openwebui.com`. These are the upstream
  community, not MedIT GPT support; whether users should be pointed at them is **TO BE CONFIRMED**.
- A pending user may be shown the admin's name and email when "show admin details" is on
  (`SHOW_ADMIN_DETAILS`); that is live data, not a repository contact.
- **The application sends no email.** There is no SMTP or mail-sending code in
  `backend/open_webui`. Notifications are in-app, browser, webhook and websocket only.
- **No person, phone number, ticket queue or service level exists in the repository.** Support
  contacts, escalation routes and hours are **TO BE CONFIRMED** (document 02).

## Environments

| Stage | Host | URL | Deploy method | Source |
|---|---|---|---|---|
| Production | **TO BE CONFIRMED** | **TO BE CONFIRMED** | **TO BE CONFIRMED** | none in repository |
| Test or staging | **TO BE CONFIRMED** | **TO BE CONFIRMED** | **TO BE CONFIRMED** | none in repository |
| Local development | maintainer's machine | `http://localhost:5173` (Vite) proxying to `:8080` | `backend/dev.sh` and `npm run dev` | `backend/dev.sh`, `vite.config.ts`, `CLAUDE.md` |

- The repository supports Docker (`Dockerfile`, `docker-compose*.yaml`), `backend/start.sh`, and
  `pip install open-webui` with `open-webui serve`. Which one production uses is TO BE CONFIRMED.
- `ENV` defaults to `dev` outside Docker (API docs at `/docs`); the image sets `prod`.
- No CI workflow runs for the `uoft` branch.

## Secrets

Never reproduce a value; cite the location only.

- `WEBUI_SECRET_KEY`: environment, or the generated file `backend/.webui_secret_key` (path relative
  to the start script). It signs sessions and encrypts stored OAuth data, and encrypts valves only
  when `ENABLE_VALVE_ENCRYPTION` is on (see the corrected valves line below).
- The repository-root `.env` file, loaded by `backend/open_webui/env.py`, may hold any setting.
- Provider API keys, OAuth client secrets, LDAP bind passwords and web-search keys are stored in
  the `config` table or the environment; the admin settings export includes them.
- Tool and function valves are stored in the database, encrypted **only** when
  `ENABLE_VALVE_ENCRYPTION` is on; its code default is off (`backend/open_webui/env.py:767`;
  `backend/open_webui/utils/valves.py:22-24`). The production value is TO BE CONFIRMED.
  *Corrected 2026-10-08: the first version said valves "are stored encrypted", a claim carried over
  from the pre-existing `CLAUDE.md` without verification.*

## Resolved Later

| Fact | Was | Now | Resolved by | Date |
|---|---|---|---|---|
