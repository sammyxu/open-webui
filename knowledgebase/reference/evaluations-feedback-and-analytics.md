# Evaluations, Feedback, Arena and Analytics

## At a Glance

- *Provisional; refined at the end of research.*
- Users rate an assistant response with thumbs up or thumbs down, optionally adding reason tags and a comment; each rating is stored as a feedback row on the server.
- Admins see all feedback on the admin Evaluations page (`/admin/evaluations`), which also computes a model leaderboard from the ratings and lets admins export and delete feedback.
- Arena models are a special model type that answers with a randomly chosen underlying model so users can compare models blind; they are configured under the `evaluation.arena.*` settings.
- Admin analytics dashboards exist only when `ENABLE_ADMIN_ANALYTICS` is on; a personal Usage panel in Settings and the `/api/usage` endpoint report usage. *Corrected 2026-10-10: the dashboards live in the Settings window (`/?settings=admin%3Aanalytics`); the old path `/admin/analytics` only redirects there, or to `/admin` when analytics is off (`src/routes/(app)/admin/analytics/+page.svelte:6-12`; section 2.1).*

## 1. Purpose and Who Uses It

This area covers how people judge the quality of MedIT GPT's answers and how admins see usage:

- **Rating a response.** Under each finished assistant response a user can press **Good Response** (thumbs up) or **Bad Response** (thumbs down). A small form then opens where the user can pick a 1-to-10 score, a reason, write a comment and edit tags. Each rating is saved on the server as one **feedback** row, which also stores a copy of the whole conversation (section 6.1) (`src/lib/components/chat/Messages/ResponseMessage.svelte:1279-1354`, `:482-604`; `src/lib/components/chat/Messages/RateComment.svelte:114-275`).
- **The admin Evaluations page** (`/admin/evaluations`) has two tabs: **Leaderboard**, which ranks models with an Elo-style score worked out from ratings, and **Feedback**, a list of every rating with export and delete actions (`src/lib/components/admin/Evaluations.svelte:85-125`; `backend/open_webui/routers/evaluations.py:44-133`).
- **Arena models** are a special entry in the model picker. They pass each request on to a randomly chosen real model and hide which one answered until the user rates the answer. The aim is blind comparison. Admins configure them in Settings, Admin, Quality, **Evaluations** (`backend/open_webui/utils/middleware.py:2400-2427`; `src/lib/components/admin/Settings/Evaluations.svelte`).
- **Admin analytics** is a dashboard of message counts, token estimates, users and models over a chosen period, in Settings, Admin, Quality, **Analytics**. It exists only when the environment switch `ENABLE_ADMIN_ANALYTICS` is on (code default on) (`backend/open_webui/main.py:878-879`; `backend/open_webui/config.py:2094`; `src/lib/components/admin/Analytics/Dashboard.svelte`).
- **Personal usage.** Every signed-in user has a **Usage** tab in their own Settings that shows their own token estimates, activity heatmap, streaks, top models and most-used tools (`src/lib/components/chat/Settings/Usage.svelte`; `backend/open_webui/routers/users.py:706-777`).
- **Live activity indicator.** The user menu can show how many people are active right now and which models are running, from `/api/usage` (`src/lib/components/layout/Sidebar/UserMenu.svelte:142-160`; `backend/open_webui/main.py:2621-2643`).

| Who | What they do here |
|---|---|
| Any user with the rating permission | Rates responses, fills in the rating form, changes a rating, sees which model answered an arena chat after rating it |
| Any signed-in user | Opens their own **Usage** tab; may see the active-user count in the user menu when public counts are on |
| Admin | Reads every feedback row on the Evaluations page, exports or deletes feedback, reads the leaderboard, configures arena models, reads analytics, switches message rating on or off |
| Tier 1 support | Read-only: explains what the buttons and pages do, checks settings with an admin, escalates. Tier 1 does not change ratings, settings or permissions |

Who is expected to review feedback, how often, and for what purpose is **TO BE CONFIRMED** (no policy exists in the repository; see section 14).

## 2. Navigation and URLs

The production host name is **TO BE CONFIRMED**; paths below are relative to the site root.

### 2.1 Pages and Panels

| What | Path or place | How to reach it | Who | Source |
|---|---|---|---|---|
| Thumbs buttons and rating form | Under each finished assistant response in a chat (`/c/<chat id>`) | Hover over an older response, or look under the latest one | Users with the rating permission; admins | `src/lib/components/chat/Messages/ResponseMessage.svelte:1085`, `:1278-1355`, `:1644-1656` |
| Admin Panel bar | `/admin` | Admin Panel; the bar lists **Users**, **Evaluations**, **Functions** (only when plugins are on) and **Settings** | Admins | `src/routes/(app)/admin/+layout.svelte:71-107` |
| Evaluations page | `/admin/evaluations` | Redirects at once to `/admin/evaluations/leaderboard` | Admins | `src/routes/(app)/admin/evaluations/+page.svelte:5-7` |
| Leaderboard tab | `/admin/evaluations/leaderboard` | Evaluations, **Leaderboard** | Admins | `src/lib/components/admin/Evaluations.svelte:85-100`, `:121-122` |
| Feedback tab | `/admin/evaluations/feedback` | Evaluations, **Feedback** | Admins | `src/lib/components/admin/Evaluations.svelte:102-117`, `:123-124` |
| Any other `/admin/evaluations/<word>` | Shows the Leaderboard | Unknown tab names fall back to the leaderboard | Admins | `src/lib/components/admin/Evaluations.svelte:14-18` |
| Arena model settings | Settings window, **Admin** section, **Quality** group, **Evaluations** tab; deep link `/?settings=admin:evaluations`; the old path `/admin/settings/evaluations` redirects there | Admin Panel, **Settings**, then **Evaluations** in the left list | Admins | `src/lib/components/chat/SettingsModal.svelte:163`, `:316-321`, `:867-868`; `src/routes/(app)/admin/settings/[tab]/+page.svelte:6-9` |
| Analytics dashboard | Settings window, **Admin** section, **Quality** group, **Analytics** tab; deep link `/?settings=admin:analytics` | Admin Panel, **Settings**, then **Analytics** | Admins, only when `ENABLE_ADMIN_ANALYTICS` is on | `src/lib/components/chat/SettingsModal.svelte:164`, `:322-327`, `:407-411`, `:869-870` |
| Old analytics paths | `/admin/analytics` and `/admin/analytics/<anything>` | Redirect to `/?settings=admin%3Aanalytics`, or to `/admin` when analytics is off | Admins | `src/routes/(app)/admin/analytics/+page.svelte:6-12`; `src/routes/(app)/admin/analytics/[tab]/+page.svelte:6-12` |
| Message rating switch | Settings window, Admin, **General** tab, **Features** section, **Message Rating** | Admin Panel, **Settings** (opens on General) | Admins | `src/lib/components/admin/Settings/General.svelte:274`, `:285-291` |
| Rating permission | Admin Panel, **Users**, **Groups** (and the default permissions), **Allow Rate Response** | See `users-groups-roles-and-permissions.md` | Admins | `src/lib/components/admin/Users/Groups/Permissions.svelte:782-799` |
| Personal Usage panel | Settings window, **Personal** section, **Data** group, **Usage** tab; deep link `/?settings=usage` | User menu, **Settings**, **Usage** | Every signed-in user | `src/lib/components/chat/SettingsModal.svelte:151-153`, `:241-246`, `:841-842` |
| Active-user count | Small green dot and number beside your name at the top of the user menu | Open the user menu | Admins, or everyone when `ENABLE_PUBLIC_ACTIVE_USERS_COUNT` is on | `src/lib/components/layout/Sidebar/UserMenu.svelte:87-94`, `:142-160` |

How the `?settings=` deep link works: the app layout reads the parameter, opens the Settings window on that tab, and removes the parameter from the address bar. A non-admin who follows an `admin:` link lands on the **General** tab instead (`src/routes/(app)/+layout.svelte:166-195`). A tab that is not available to the user (for example Analytics when it is switched off) also falls back to General (`src/lib/components/chat/SettingsModal.svelte:490-497`).

Display names of the tabs come from dotted translation keys: **Usage** (`settings.personal.usage.title`, `src/lib/i18n/locales/en-US/translation.json:3054`), **Evaluations** (`settings.admin.evaluations.title`, `:2368`) and **Analytics** (`settings.admin.analytics.title`, `:1976`). The group headings **Data**, **Quality**, **Personal** and **Admin** are plain keys (`src/lib/components/chat/SettingsModal.svelte:151-153`, `:163-164`, `:560`, `:753`).

### 2.2 Server Endpoints

All feedback and evaluation routes are under `/api/v1/evaluations` (`backend/open_webui/main.py:877`). Analytics routes are under `/api/v1/analytics` and are **mounted only when `ENABLE_ADMIN_ANALYTICS` is on**; otherwise they are not registered at all (`backend/open_webui/main.py:878-879`). A request to an unregistered path then falls through to the handler that serves the web app's pages (`backend/open_webui/main.py:298-310`, `:3066-3075`), so it gets a page rather than data.

| Method and path | Who | What it does | Source |
|---|---|---|---|
| `POST /api/v1/evaluations/feedback` | Signed-in user | Creates a feedback row for the caller | `backend/open_webui/routers/evaluations.py:425-446` |
| `GET /api/v1/evaluations/feedback/{id}` | Owner, or any admin | Reads one feedback row, including its conversation snapshot | `backend/open_webui/routers/evaluations.py:449-459` |
| `POST /api/v1/evaluations/feedback/{id}` | Owner, or any admin | Updates the rating, comment, tags or snapshot | `backend/open_webui/routers/evaluations.py:462-485` |
| `DELETE /api/v1/evaluations/feedback/{id}` | Owner, or any admin | Deletes one feedback row | `backend/open_webui/routers/evaluations.py:488-509` |
| `GET /api/v1/evaluations/feedbacks/user?page=` | Signed-in user | Lists the caller's own feedback, 30 a page | `backend/open_webui/routers/evaluations.py:366-378` |
| `DELETE /api/v1/evaluations/feedbacks` | Signed-in user | Deletes all of the caller's own feedback | `backend/open_webui/routers/evaluations.py:381-396` |
| `GET /api/v1/evaluations/feedbacks/list` | Admin | Lists all feedback with sorting, model filter and paging (30 a page) | `backend/open_webui/routers/evaluations.py:399-422` |
| `GET /api/v1/evaluations/feedbacks/models` | Admin | Distinct model ids found in feedback, for the filter list | `backend/open_webui/routers/evaluations.py:327-329` |
| `GET /api/v1/evaluations/feedbacks/all/ids` | Admin | Id, owner id and dates of every feedback row | `backend/open_webui/routers/evaluations.py:332-334` |
| `GET /api/v1/evaluations/feedbacks/all/export` | Admin | Every feedback row in full, including snapshots; optional `model_id` filter | `backend/open_webui/routers/evaluations.py:354-363` |
| `DELETE /api/v1/evaluations/feedbacks/all` | Admin | Deletes every feedback row on the server | `backend/open_webui/routers/evaluations.py:337-351` |
| `GET /api/v1/evaluations/leaderboard?query=` | Admin | Elo ratings, wins, losses and top tags per model; `query` re-weights by topic | `backend/open_webui/routers/evaluations.py:222-265` |
| `GET /api/v1/evaluations/leaderboard/{model_id}/history?days=` | Admin | Daily wins and losses for one model (default 30 days, 0 for all) | `backend/open_webui/routers/evaluations.py:268-277` |
| `GET /api/v1/evaluations/config` | Admin | Reads the arena switch and arena model list | `backend/open_webui/routers/evaluations.py:285-287` |
| `POST /api/v1/evaluations/config` | Admin | Saves the arena switch and arena model list | `backend/open_webui/routers/evaluations.py:300-324` |
| `GET /api/v1/analytics/summary` | Admin | Totals of messages, chats, models and users for a period | `backend/open_webui/routers/analytics.py:163-187` |
| `GET /api/v1/analytics/models` | Admin | Messages, distinct users and distinct chats per model | `backend/open_webui/routers/analytics.py:58-82` |
| `GET /api/v1/analytics/users` | Admin | Messages and token estimates per user, with name and email (top 50 by default) | `backend/open_webui/routers/analytics.py:85-122` |
| `GET /api/v1/analytics/messages` | Admin | Raw stored messages filtered by chat, model or user (up to 100) | `backend/open_webui/routers/analytics.py:125-153` |
| `GET /api/v1/analytics/daily` | Admin | Messages per model per day, or per hour | `backend/open_webui/routers/analytics.py:199-217` |
| `GET /api/v1/analytics/tokens` | Admin | Token estimates per model and in total | `backend/open_webui/routers/analytics.py:235-261` |
| `GET /api/v1/analytics/models/{model_id}/chats` | Admin | Chats that used a model: title, owner name, last update | `backend/open_webui/routers/analytics.py:285-319` |
| `GET /api/v1/analytics/models/{model_id}/overview?days=` | Admin | A model's daily wins and losses and the top ten chat tags | `backend/open_webui/routers/analytics.py:343-421` |
| `GET /api/v1/users/usage` | Signed-in user | The caller's own Usage panel data | `backend/open_webui/routers/users.py:706-777` |
| `GET /api/usage` | Signed-in user; admins only when `ENABLE_PUBLIC_ACTIVE_USERS_COUNT` is off | Models in use right now and the number of active users | `backend/open_webui/main.py:2621-2643` |

The front-end callers are in `src/lib/apis/evaluations/index.ts`, `src/lib/apis/analytics/index.ts`, `src/lib/apis/users/index.ts:716-749` (`getUserUsage`) and `src/lib/apis/index.ts:1442-1467` (`getUsage`).

## 3. Roles and Permissions

Roles are `admin`, `user` and `pending` (see `knowledgebase/tools/ground-truth.md`). "Signed-in user" below means role `user` or `admin`, checked by `get_verified_user`; "admin" means `get_admin_user`. Both refuse other callers with HTTP 401 and the `ACCESS_PROHIBITED` text (ground truth; `backend/open_webui/utils/auth.py:567-576`, `:625-631`).

### 3.1 Who Can Do What

| Action | Regular user | Admin | Where enforced |
|---|---|---|---|
| See the thumbs buttons | Only when message rating is on, the chat is not temporary, the view is not read-only, the response has finished, and the user has **Allow Rate Response** | Yes, when message rating is on and the chat is not temporary (the permission check is skipped for admins) | Interface: `src/lib/components/chat/Messages/ResponseMessage.svelte:1085`, `:1278-1279` |
| Create a feedback row | Yes, for themselves | Yes | `backend/open_webui/routers/evaluations.py:425-432` |
| Read, change or delete one feedback row | Only their own (the lookup includes their user id) | Any row | `backend/open_webui/routers/evaluations.py:449-459`, `:462-476`, `:488-501`; `backend/open_webui/models/feedbacks.py:187-198`, `:485-508`, `:520-528` |
| List or delete all of their own feedback | Through the API only; the interface has no screen for it | Same | `backend/open_webui/routers/evaluations.py:369-396` (no caller in `src/lib/apis/evaluations/index.ts`) |
| See the Evaluations page, leaderboard and every feedback row | No; the admin layout sends non-admins to `/` | Yes | `src/routes/(app)/admin/+layout.svelte:15-17`; `backend/open_webui/routers/evaluations.py:222-226`, `:399-407` |
| Export all feedback, including conversation snapshots | No | Yes | `backend/open_webui/routers/evaluations.py:354-363` |
| Delete every feedback row on the server | No | Through the API only; the interface has no button for it | `backend/open_webui/routers/evaluations.py:337-351` |
| Configure arena models | No | Yes | `backend/open_webui/routers/evaluations.py:285-324` |
| Use an arena model in chat | Only if the arena model's access list grants them read | Yes, while `BYPASS_ADMIN_ACCESS_CONTROL` is on (code default on) | `backend/open_webui/utils/models.py:465-480`, `:524-576` |
| Open the analytics dashboard | No; the tab is not offered and the routes are admin-only | Yes, when `ENABLE_ADMIN_ANALYTICS` is on | `src/lib/components/chat/SettingsModal.svelte:407-411`; `src/lib/components/admin/Analytics.svelte:12-15`; `backend/open_webui/routers/analytics.py:63`, `:91`, `:134`, `:168`, `:205`, `:240`, `:294`, `:347` |
| Open their own Usage panel | Yes, always offered | Yes | `src/lib/components/chat/SettingsModal.svelte:379-405`; `backend/open_webui/routers/users.py:706-713` |
| See the active-user count | Only when `ENABLE_PUBLIC_ACTIVE_USERS_COUNT` is on (code default on) | Yes | `backend/open_webui/main.py:2628-2633`; `backend/open_webui/env.py:367`; `src/lib/components/layout/Sidebar/UserMenu.svelte:91`, `:142` |

A `pending` user cannot rate, see usage or call any of these endpoints, because every route here needs at least a signed-in `user` (ground truth).

### 3.2 The Rating Permission and the Global Switch

Two separate controls decide whether the thumbs buttons appear:

1. **Message Rating** (persistent setting `ui.enable_message_rating`, seeded from `ENABLE_MESSAGE_RATING`, code default `True`) turns rating on or off for everyone, admins included (`backend/open_webui/config.py:2098`, `:3124`; `backend/open_webui/main.py:2370`). The admin label is **Message Rating** and its description is "Let users rate assistant responses." (`src/lib/components/admin/Settings/General.svelte:285-291`; `src/lib/i18n/locales/en-US/translation.json:2394-2395`).
2. **Allow Rate Response** is the chat permission `chat.rate_response`, seeded from `USER_PERMISSIONS_CHAT_RATE_RESPONSE`, code default `True` (`backend/open_webui/config.py:1871`, `:1989`; `backend/open_webui/routers/users.py:246`; `src/lib/constants/permissions.ts:50`). It is set in the default permissions and per group (`src/lib/components/admin/Users/Groups/Permissions.svelte:782-799`).

Because permissions add up across groups, a group cannot take away a permission the defaults grant (ground truth). When a group switch is off but the default is on, the group editor says `This is a default user permission and will remain enabled.` (`src/lib/components/admin/Users/Groups/Permissions.svelte:792-797`). To stop a set of people from rating, the default must be off and only the groups that should rate turn it on. The live values are data and **TO BE CONFIRMED**.

Both controls are applied by the interface when it draws the buttons (`src/lib/components/chat/Messages/ResponseMessage.svelte:1279`). Whether the server should also enforce them is a security question: refer it (section 14).

### 3.3 Arena Model Access Lists

Each arena model carries its own access list in `meta.access_grants`, stored inside the `evaluation.arena.models` setting rather than in the `access_grant` table (`backend/open_webui/utils/access_control/__init__.py:111-148`). The rules are:

- **An empty list means private**: nobody but admins (with the bypass on) sees the model (`backend/open_webui/utils/access_control/__init__.py:124-130`).
- A grant for user `*` with `read` makes it visible to everyone; grants for specific users or groups make it visible to them (`backend/open_webui/utils/access_control/__init__.py:126-146`).
- The built-in fallback **Arena Model** (shown when arena models are on but none are configured) has no access list, so in a default install only admins see it (`backend/open_webui/config.py:2067-2078`; `backend/open_webui/utils/models.py:134-148`, `:550-561`).
- Model lists hide arena models a user cannot read (`backend/open_webui/utils/models.py:550-561`). Sending a chat to one anyway is refused: the check raises `Model not found` (`backend/open_webui/utils/models.py:465-480`), which the chat endpoint returns as HTTP 400 with that text (`backend/open_webui/main.py:1149-1161`, `:1640-1645`), and the server log gets a `Model access denied: ... reason=arena_read_denied` line.
- Older arena entries that used the legacy `access_control` shape are converted to `access_grants` at startup (`backend/open_webui/main.py:660-664`, inside `initialize_runtime_config` at `:621`; `backend/open_webui/utils/access_control/__init__.py:182-188`).

How the editor sets these lists is in section 5.7. The wider model-access rules are in `workspace-models-and-model-access.md`.

### 3.4 What Admins Can See About Other People

- **Feedback rows**: who rated (name and profile picture in the list; the API also returns email, role and activity dates), the model, the result, the comment, reason and tags, and through the detail window the prompt and response text taken from the stored conversation copy (`backend/open_webui/models/feedbacks.py:108-122`, `:215-279`; `src/lib/components/admin/Evaluations/Feedbacks.svelte:421-511`; `src/lib/components/admin/Evaluations/FeedbackModal.svelte:61-135`).
- **Exports** contain every field of every row, including the whole conversation copy (`backend/open_webui/routers/evaluations.py:354-363`; `backend/open_webui/models/feedbacks.py:281-284`).
- **The Chat ID link** in the detail window opens `/s/<chat id>`. For an admin with `ENABLE_ADMIN_CHAT_ACCESS` on (code default on) that shows the chat as it is now, not the copy stored with the feedback (`src/lib/components/admin/Evaluations/FeedbackModal.svelte:61-73`; `backend/open_webui/routers/chats.py:1226-1233`).
- **Analytics**: names and emails of the most active users, their message counts and token estimates, and the titles and owners of chats that used a model (`backend/open_webui/routers/analytics.py:85-122`, `:285-319`; `backend/open_webui/models/chats.py:1621-1685`). The `/api/v1/analytics/messages` route can return stored message content, but no screen calls it (`backend/open_webui/routers/analytics.py:125-153`; `getMessages` has no caller outside `src/lib/apis/analytics/index.ts`).

All of this can include health or other sensitive details that people typed into chats. Section 6.5 lists where such data sits.

## 4. Key Concepts and Terminology

| Term | Meaning in MedIT GPT | Source |
|---|---|---|
| **Feedback** | One stored rating of one assistant response. The interface always saves it with `type` `rating`. A response has at most one feedback row per rater: its id is written into the message as `feedbackId` and reused when the rating changes | `src/lib/components/chat/Messages/ResponseMessage.svelte:507-508`, `:547-570`; `backend/open_webui/models/feedbacks.py:20-30` |
| **Good Response / Bad Response** | The thumbs-up and thumbs-down buttons. They store `rating` `1` or `-1` | `src/lib/components/chat/Messages/ResponseMessage.svelte:1280-1292`, `:1318-1330` |
| **Won / Lost / Draw** | How the admin Feedback list shows a rating of `1`, `-1` or `0`. The interface itself only ever sends `1` or `-1`, so **Draw** appears only for rows written by another client | `src/lib/components/admin/Evaluations/Feedbacks.svelte:480-491` |
| **Detailed rating** | The optional 1-to-10 score in the rating form, stored as `details.rating`. After a thumbs up only 6 to 10 can be picked; after a thumbs down only 1 to 5. The admin detail window shows this number under **Rating** | `src/lib/components/chat/Messages/RateComment.svelte:135-162`; `src/lib/components/admin/Evaluations/FeedbackModal.svelte:101-107` |
| **Reason** | One reason picked from a fixed list, stored as a code such as `too_verbose`; the lists differ for thumbs up and thumbs down (section 5.1) | `src/lib/components/chat/Messages/RateComment.svelte:17-35`, `:166-216` |
| **Comment** | Free text typed into "Feel free to add specific details" | `src/lib/components/chat/Messages/RateComment.svelte:218-226` |
| **Tags** | Topic words attached to a rating. When a rating is first given, the browser asks the model to suggest tags (the "tags generation" task); the user can add or remove tags in the form. Tags drive the leaderboard topic search and the "top tags" per model | `src/lib/components/chat/Messages/ResponseMessage.svelte:577-600`; `src/lib/components/chat/Messages/RateComment.svelte:228-244`; `backend/open_webui/routers/evaluations.py:136-206` |
| **Snapshot** | A full copy of the chat record, fetched from the server at the moment of rating and stored in the feedback row. It is replaced every time the rating or form is saved again | `src/lib/components/chat/Messages/ResponseMessage.svelte:498-503`, `:527-529`; `backend/open_webui/models/feedbacks.py:28`, `:477-478` |
| **Sibling models** | The other responses to the same prompt: a side-by-side answer from a second model, or a regenerated answer. Their model ids are stored as `sibling_model_ids` and become the "opponents" in the Elo calculation. A response with no siblings has no opponents | `src/lib/components/chat/Messages/ResponseMessage.svelte:512-518`; `backend/open_webui/routers/evaluations.py:118-131` |
| **Leaderboard** | The admin table ranking models by an Elo rating computed from feedback each time the page asks for it. Nothing is stored. Every model starts at 1000; each comparison moves ratings by up to 32 points (K-factor), more for upsets | `backend/open_webui/routers/evaluations.py:44-65`, `:86-133`, `:222-265` |
| **Topic search** | Typing in the leaderboard search box re-weights every rating by how close its tags are to the words typed, giving a "best model for this topic" view. It uses a small embedding model, `TaylorAI/bge-micro-v2` by default (`AUXILIARY_EMBEDDING_MODEL`), or the main embedding engine in the slim image | `backend/open_webui/routers/evaluations.py:57-83`, `:163-206`, `:232-244` |
| **Arena model** | A model-picker entry (`owned_by` `arena`) that forwards each request to a randomly chosen real model, from an explicit list or from every non-arena model. The fallback entry is called **Arena Model** with id `arena-model` | `backend/open_webui/config.py:2067-2078`; `backend/open_webui/utils/models.py:115-149`; `backend/open_webui/utils/middleware.py:2400-2427` |
| **Blind comparison** | While an arena answer is shown, the message keeps the arena model's name; the real model id (`selected_model_id`) is stored on the message and revealed only in the rating form: `This response was generated by "{model}"` | `src/lib/components/chat/Chat.svelte:2838-2841`; `src/lib/components/chat/Messages/RateComment.svelte:74-83`, `:106-112` |
| **Filter mode** | For an arena model, **include** means "choose only from these models" and **exclude** means "choose from every model except these" | `backend/open_webui/utils/middleware.py:2404-2421`; `src/lib/components/admin/Settings/Evaluations/ArenaModelModal.svelte` |
| **Analytics message count** | Counts **assistant** responses only, from the `chat_message` table. The dashboard says so: "Message counts are based on assistant responses." | `backend/open_webui/models/chat_messages.py:520-545`; `src/lib/components/admin/Analytics/Dashboard.svelte:623-625` |
| **Token estimates** | Input and output token numbers read from the `usage` stored with each response (`input_tokens`/`output_tokens`, or `prompt_tokens`/`completion_tokens`). Responses with no stored usage count as zero tokens. Both the dashboard and the Usage panel call them estimates | `backend/open_webui/models/chat_messages.py:63-85`, `:585-633`; `src/lib/components/chat/Settings/Usage.svelte:486-488` |
| **Active users** | People whose account was active in the last three minutes (`last_active_at`) | `backend/open_webui/models/users.py:901-908` |
| **Models in use** | Models with a response being generated right now: the browser sends a `usage` signal every second while it waits for an answer, and the server forgets a model three seconds after the last signal | `src/lib/components/chat/Chat.svelte:2623-2631`; `backend/open_webui/socket/main.py:127-128`, `:266-308`, `:407-418` |
| **Longest active chat** | In the Usage panel, the longest total time spent in one chat, adding up gaps between consecutive messages of 30 minutes or less | `backend/open_webui/models/chats.py:46`, `:1851-1879` |
| **Streak** | Consecutive days with at least one message. "Current streak" counts back from the last day of the period | `backend/open_webui/routers/users.py:392-408` |

## 5. Workflows (Step by Step)

### 5.1 Rate a Response (User)

1. Wait for the response to finish. The thumbs buttons are drawn only once the message is done (`src/lib/components/chat/Messages/ResponseMessage.svelte:1085`). On the latest response they are always visible; on older responses they appear when the pointer is over the message, unless the personal Interface setting **Accessibility Mode** (stored as `highContrastMode`) is on (`:1283-1285`, `:1321-1323`; `src/lib/components/common/InterfaceSettings.svelte:599-611`; `src/lib/i18n/locales/en-US/translation.json:2872`).
2. Press **Good Response** (thumbs up) or **Bad Response** (thumbs down). Both buttons are disabled while the rating is being saved (`:1290`, `:1328`).
3. Behind the scenes the browser (`feedbackHandler`, `:482-604`):
   - writes the rating into the message's `annotation`; if the rating changed direction it clears the previous reason and 1-to-10 score (`:486-496`);
   - **fetches the whole chat from the server** to use as the snapshot (`:498-503`);
   - builds the feedback: `data` holds the rating and any form fields, the rated model (`selectedModelId` for arena answers, otherwise the message's model) and, when the prompt has more than one response, the sibling models; `meta` holds the arena flag, model, message id, message position, chat id and each model's base model (`:507-545`);
   - updates the existing feedback row if the message already has a `feedbackId`, otherwise creates a new row and remembers its id on the message (`:547-567`);
   - saves the message (with `annotation` and `feedbackId`) back into the chat record (`:569-570`; `src/lib/components/chat/Messages.svelte:409-416`).
4. The rating form opens under the response and the page scrolls to it (`src/lib/components/chat/Messages/ResponseMessage.svelte:574-575`, `:1293-1297`, `:1644-1656`).
5. If the rating has no tags yet and the response has text, the browser asks the server to suggest tags (the tags generation task) and saves them into both the message and the feedback row (`:577-600`; `src/lib/apis/index.ts:851-921`). When tags generation is off, the server answers `Tags generation is disabled` and the tags stay empty (`backend/open_webui/routers/tasks.py:279-285`).

Rating a response has no undo in the interface: pressing the same thumb again saves the same rating and reopens the form; pressing the other thumb switches the rating (`src/lib/components/chat/Messages/ResponseMessage.svelte:486-496`).

### 5.2 Fill In the Rating Form

The form (`src/lib/components/chat/Messages/RateComment.svelte`) has, in order:

| Part | What the user sees | Stored as | Source |
|---|---|---|---|
| Heading | `How would you rate this response?` and a close button | | `:118-131` |
| Arena reveal | For arena answers: `This response was generated by "{model}"`, also shown once as a toast when the form opens | | `:74-83`, `:106-112` |
| 1-to-10 scale | Ten round buttons labelled `1 - Awful` to `10 - Amazing`; only 6 to 10 after a thumbs up, only 1 to 5 after a thumbs down | `details.rating` | `:133-164` |
| Reasons | `Why?` and one button per reason (table below); one reason can be chosen | `reason` (a code) | `:166-216` |
| Comment | A text box with the placeholder `Feel free to add specific details` | `comment` | `:218-226` |
| Tags | Tag chips with add and remove; suggestions come from the user's own chat tags (`/api/v1/chats/all/tags`, `src/lib/apis/chats/index.ts:654-657`) | `tags` | `:228-244` |
| Save | **Save** sends everything and shows `Thanks for your feedback!` | | `:85-103`, `:246-253` |
| Public review link | Only when community sharing is on: `Leave a public review for {modelName}` and `Help the community discover great models`, a link to `https://openwebui.com/models?q=<model id>` | | `:256-274` |

| After a thumbs up | Code | After a thumbs down | Code |
|---|---|---|---|
| Accurate information | `accurate_information` | Don't like the style | `dont_like_the_style` |
| Followed instructions perfectly | `followed_instructions_perfectly` | Too verbose | `too_verbose` |
| Showcased creativity | `showcased_creativity` | Not helpful | `not_helpful` |
| Positive attitude | `positive_attitude` | Not factually correct | `not_factually_correct` |
| Attention to detail | `attention_to_detail` | Didn't fully follow instructions | `didnt_fully_follow_instructions` |
| Thorough explanation | `thorough_explanation` | Refused when it shouldn't have | `refused_when_it_shouldnt_have` |
| Other | `other` | Being lazy | `being_lazy` |
| | | Other | `other` |

Sources: `src/lib/components/chat/Messages/RateComment.svelte:17-35` (codes) and `:181-211` (labels). No field is required; the "Please select a reason" check is commented out (`:87-90`).

When **Save** is pressed, the form hands its values to the same `feedbackHandler`, which re-fetches the chat, updates the feedback row (snapshot included) and saves the message (`src/lib/components/chat/Messages/ResponseMessage.svelte:1649-1653`, `:482-570`). The toast `Thanks for your feedback!` is shown by the form itself before the server answers, so it appears even if the save then fails (`src/lib/components/chat/Messages/RateComment.svelte:92-102`).

### 5.3 Make Ratings Count on the Leaderboard

The leaderboard only learns from **comparisons**. A rating counts only when the rated response has siblings, that is, other responses to the same prompt (`backend/open_webui/routers/evaluations.py:108-131`; `src/lib/components/chat/Messages/ResponseMessage.svelte:512-518`). Ways to create siblings:

1. **Side-by-side models**: choose two or more models in the model selector before sending; each answers the same prompt (see `chat-composer-and-message-display.md`).
2. **Regenerate**: regenerating adds another response to the same prompt.
3. **Arena model**: with an arena model, each regeneration may land on a different hidden model.

Then rate one of the responses. A thumbs up on response A with sibling B counts as "A beat B"; a thumbs down counts as "B beat A" (`backend/open_webui/routers/evaluations.py:115-131`). A single response rated on its own is still stored and still shows in the Feedback list, in the model's activity chart and in tag counts, but it does not move any leaderboard rating.

A regenerated answer from the same model counts as a match against itself: the stored opponent id equals the rated model, so the model gets one win and one loss and its rating does not change (`backend/open_webui/routers/evaluations.py:118-131`). Sibling lists include every earlier regeneration, not only the one on screen (`src/lib/components/chat/Messages/ResponseMessage.svelte:514-516`).

### 5.4 Chat With an Arena Model (Blind Comparison)

1. Pick the arena model (for example **Arena Model**) in the model selector. It is only listed for people its access list allows (section 3.3).
2. Send a prompt. The server picks one real model at random **before** any other processing, so that model's knowledge, tools and settings apply (`backend/open_webui/utils/middleware.py:2400-2427`):
   - with a model list in **include** mode, from that list;
   - with a model list in **exclude** mode, from every non-arena model except those listed;
   - with no list, from every non-arena model the server knows.
3. The response is labelled with the arena model's name. The real model id travels back with the answer and is stored on the message as `selectedModelId` with `arena` set (`src/lib/components/chat/Chat.svelte:2838-2841`; `backend/open_webui/utils/middleware.py:4257-4265`, `:5115-5125`). A fallback in `backend/open_webui/utils/chat.py:214-249` does the same choice when a request reaches the chat code without going through the middleware.
4. Regenerate to get another, possibly different, hidden model; rate one of the answers. The rating form then reveals `This response was generated by "{model}"` (`src/lib/components/chat/Messages/RateComment.svelte:74-83`, `:106-112`).
5. Continuing a response (**Continue Response**) reuses the model that was chosen, not a new random one (`src/lib/components/chat/Chat.svelte:3879-3892`).

Whether an arena model is meant to be combined with other models side by side is **TO BE CONFIRMED**; the model selector has no arena-specific code (`src/lib/components/chat/ModelSelector/`).

### 5.5 See Your Own Usage (User)

1. Open the user menu, **Settings**, then **Usage** under **Data**, or go to `/?settings=usage` (section 2.1).
2. The panel calls `GET /api/v1/users/usage` with no options, so the period is the last **730 days** (`src/lib/components/chat/Settings/Usage.svelte:131-140`; `backend/open_webui/routers/users.py:714-720`).
3. What it shows (`src/lib/components/chat/Settings/Usage.svelte:272-491`; `backend/open_webui/routers/users.py:730-777`):

| Shown as | Meaning | Period |
|---|---|---|
| **Lifetime tokens** | Sum of input and output token estimates of your assistant responses | All time |
| **Peak tokens** | The highest single day's token estimate | Last 730 days |
| **Longest active chat** | Longest total active time in one chat (gaps over 30 minutes are not counted), shown as `0m`, `{hours}h {minutes}m` or `{days}d {hours}h` | All time |
| **Current streak** / **Longest streak** | Consecutive days with at least one message | Last 730 days |
| **Token activity** heatmap | One square per day, coloured by the most-used model that day; **Daily**, **Weekly** and **Cumulative** views; hover text gives tokens, messages, chats and top models | Last 730 days, trimmed to the width of the window (at least 26 weeks when there is data) |
| **Models** | Number of different models you have used | All time |
| **Average tokens per chat** | Lifetime tokens divided by your number of chats | All time |
| **Average messages per active day** | Messages divided by active days | Last 730 days |
| **User messages** / **Assistant messages** | Counts and percentage share | Last 730 days |
| **Total chats** | Your chats, excluding internal ones | All time |
| **Top models** | Up to five models with messages and tokens | Last 730 days |
| **Most used tools** | Up to five tool names with run counts; hidden when there are none | Last 730 days |

4. Days are cut at midnight in **your** time zone, which your browser sends when you sign in and again every time the app loads; if none is known the server uses UTC (`backend/open_webui/routers/users.py:732`, `:735`; `backend/open_webui/models/chat_messages.py:52-60`; `src/routes/auth/+page.svelte:58-62`; `src/routes/+layout.svelte:1294-1298`; `backend/open_webui/routers/auths.py:356-376`).
5. The panel ends with `Token counts are estimates and may not reflect actual API usage` (`src/lib/components/chat/Settings/Usage.svelte:486-488`).

Everything here is read from your stored messages, so deleting chats lowers these figures (section 6.4).

### 5.6 See Who Is Active Now

Opening the user menu fetches `/api/usage` when public counts are on or the user is an admin (`src/lib/components/layout/Sidebar/UserMenu.svelte:87-94`). A green dot and a number appear beside the user's name when at least one person is active; hovering shows `Running: {model ids} ✨` while models are generating, otherwise `Active Users` (`:142-160`). "Active" means signed-in activity in the last three minutes, and "running" means a response is being generated right now (section 4).

### 5.7 Configure Arena Models (Admin)

1. Open **Admin Panel**, **Settings**, then **Evaluations** (or `/?settings=admin:evaluations`). The panel loads the current values from `GET /api/v1/evaluations/config` (`src/lib/components/admin/Settings/Evaluations.svelte:75-82`).
2. **Arena Models** switch: its description reads "Message rating should be enabled to use this feature" (`settings.admin.evaluations.arenaModels.label` and `.description`, `src/lib/i18n/locales/en-US/translation.json:2365-2366`; `src/lib/components/admin/Settings/Evaluations.svelte:100-113`). The code does not link the two switches: arena models work with rating off, but then nobody can rate their answers. A change to this switch is saved only with the **Save** button at the bottom (`:87-93`, `:165-172`).
3. With the switch on, the **Models** section lists the configured arena models. When the list is empty it says `Using the default arena model with all models. Click the plus button to add custom models.` (`:115-154`).
4. Press the plus button (tooltip **Add Arena Model**) to open **Add Arena Model** (`src/lib/components/admin/Settings/Evaluations/ArenaModelModal.svelte:160-168`):
   - **Profile image**: click the picture to upload a GIF, WebP, JPEG or PNG; it is cropped to 250 by 250 pixels and stored inline (`:195-279`).
   - **Name** (placeholder `Model Name`) and **Description**, each with optional translations through the language selector (`:188-194`, `:281-326`).
   - **ID**: filled in from the name (lower case, other characters turned into hyphens) and locked once the model exists (`:32-44`, `:297-312`).
   - **Access**: **Private** or **Public**, plus an **Access List** of users and groups (the shared access editor, `src/lib/components/workspace/common/AccessControl.svelte:517-582`). A new arena model starts with no grants, which means private (section 3.3).
   - **Models**: an **Include** or **Exclude** toggle, the chosen models, and a `Select a model` list with a plus button; with nothing chosen the hint says `Leave empty to include all models or select specific models` (`src/lib/components/admin/Settings/Evaluations/ArenaModelModal.svelte:336-410`).
5. **Save** in the window stores the whole arena list at once through `POST /api/v1/evaluations/config`, shows `Settings saved successfully!` and reloads the model list (`src/lib/components/admin/Settings/Evaluations.svelte:24-50`). It refuses a missing name or id (`Name and ID are required, please fill them out`) and, for a new model, a name already used by any model (`Model name already exists, please choose a different one`) (`src/lib/components/admin/Settings/Evaluations/ArenaModelModal.svelte:69-84`).
6. To change or remove an arena model, press its gear icon. The window is titled **Edit Arena Model** and adds **Delete**, which asks `Confirm your action` / `This action cannot be undone. Do you wish to continue?` before removing it and saving the list (`src/lib/components/admin/Settings/Evaluations/Model.svelte:16-24`, `:52-62`; `src/lib/components/admin/Settings/Evaluations/ArenaModelModal.svelte:152-158`, `:412-423`; `src/lib/components/common/ConfirmDialog.svelte:130-153`; `src/lib/components/admin/Settings/Evaluations.svelte:52-73`).
7. Each save publishes a `CONFIG_UPDATED` event naming the keys changed and the number of arena models (`backend/open_webui/routers/evaluations.py:313-323`; section 9).

### 5.8 Read the Leaderboard (Admin)

1. Open **Admin Panel**, **Evaluations** (lands on **Leaderboard**). The number beside **Leaderboard** is the number of rows the table will show (`src/lib/components/admin/Evaluations.svelte:33-57`; `src/lib/components/admin/Evaluations/Leaderboard.svelte:87`).
2. The table lists **every visible model** in the admin's model list (arena and hidden models excluded) plus any rated model that is no longer in the list, shown by its raw id (`src/lib/components/admin/Evaluations/Leaderboard.svelte:45-92`). Columns: **RK**, **Model**, **Rating**, **Won**, **Lost** (`:177`). Models never compared show `-` and sort to the bottom (`:56-66`, `:82-86`, `:207-209`). Hovering a row turns Won and Lost into percentages (`:233-248`).
3. Click a column heading to sort; click again to reverse (`:26-33`, `:104-120`).
4. Type in **Search** to re-rank by topic. After half a second the leaderboard is recalculated with each rating weighted by how closely its tags match the words typed (`:94-102`; `backend/open_webui/routers/evaluations.py:232-246`). Clear the box (x) to return to the plain ranking (`src/lib/components/admin/Evaluations/Leaderboard.svelte:139-151`).
5. Click a row to open the model window: the model name, an **Activity** chart of daily wins (up) and losses (down) for **30D**, **1Y** or **All** (weekly bars for the last two), and **Tags** with counts (`src/lib/components/admin/Evaluations/LeaderboardModal.svelte:15-20`, `:62-137`; `src/lib/components/admin/Evaluations/ModelActivityChart.svelte:30-55`, `:181-194`). The chart counts **every** thumbs up as a win and every thumbs down as a loss for that model, whether or not it was a comparison (`backend/open_webui/models/feedbacks.py:320-384`), so its totals can differ from the table.
6. The footer reads `ⓘ The evaluation leaderboard is based on the Elo rating system and is updated in real-time.` (`src/lib/components/admin/Evaluations/Leaderboard.svelte:257-265`). "Real time" means it is recalculated from all feedback on every load; nothing is cached (`backend/open_webui/routers/evaluations.py:222-265`).

### 5.9 Review Feedback (Admin)

1. **Admin Panel**, **Evaluations**, **Feedback** (`/admin/evaluations/feedback`). The number beside **Feedback** is the total count (`src/lib/components/admin/Evaluations.svelte:49-57`, `:102-117`).
2. Filter by model with the selector at the top left (**All** or one model id) (`src/lib/components/admin/Evaluations/Feedbacks.svelte:235-269`; ids from `GET /api/v1/evaluations/feedbacks/models`).
3. The table shows 30 rows a page, with page controls when there are more (`:518-520`; `backend/open_webui/routers/evaluations.py:366`, `:408-411`). Columns (`src/lib/components/admin/Evaluations/Feedbacks.svelte:319-417`, `:421-511`):
   - **User**: the rater's picture, name on hover;
   - **Models**: the rated model; for comparisons a second line lists the other models, shortened to `{first two}, and {COUNT} more`;
   - **Result**: **Won**, **Draw** or **Lost**;
   - **Updated At**: relative time such as "3 days ago";
   - a **More** menu with **Delete**.
4. Click a heading to sort by user name, model, result or last update; the first click sorts ascending (`:49-56`; `backend/open_webui/models/feedbacks.py:234-256`).
5. Click a row to open **Feedback Details** (`src/lib/components/admin/Evaluations/FeedbackModal.svelte:42-155`): **Chat ID** (a link to `/s/<chat id>`), **Prompt** and **Response** (taken from the stored conversation copy), **Rating** (the 1-to-10 score, or `-`), **Reason** (the stored code, for example `too_verbose`), **Comment**, the tags, and **Close**.
6. Feedback whose rater account has been deleted is **not listed** (the list joins each row to an existing user) but is still in exports and still counts on the leaderboard (`backend/open_webui/models/feedbacks.py:215-224`, `:281-284`, `:314-318`).

When the list is empty it says `No feedback found` and `Try adjusting your search or filter to find what you are looking for.` (`src/lib/components/admin/Evaluations/Feedbacks.svelte:306-314`).

### 5.10 Export Feedback (Admin)

1. On the Feedback tab, open **Export** (shown only when at least one row exists) and choose **Export as JSON** or **Export as CSV** (`src/lib/components/admin/Evaluations/Feedbacks.svelte:272-301`).
2. The browser downloads every row matching the model filter from `GET /api/v1/evaluations/feedbacks/all/export` (`:189-209`; `backend/open_webui/routers/evaluations.py:354-363`).
3. Files are named `feedback-history-export-<number>.json` or `.csv`, where the number is the download time in milliseconds (`src/lib/components/admin/Evaluations/Feedbacks.svelte:201`, `:206`).

| Format | Contents | Source |
|---|---|---|
| JSON | Every field of every row: id, user id, version, type, `data` (rating, reason, comment, tags, 1-to-10 score, models), `meta` (chat id, message id, models) and the **full conversation snapshot** | `src/lib/components/admin/Evaluations/Feedbacks.svelte:203-206`; `backend/open_webui/models/feedbacks.py:33-44` |
| CSV | Columns `id`, `user_id`, `chat_id`, `model_id`, `sibling_model_ids` (joined with `;`), `rating`, `reason`, `comment`, `created_at`, `updated_at`; no snapshot and no tags | `src/lib/components/admin/Evaluations/Feedbacks.svelte:157-187` |

The CSV `chat_id` column is read from `data.chat_id`, but the interface stores the chat id in `meta.chat_id`, so for ratings made in MedIT GPT that column is empty (`src/lib/components/admin/Evaluations/Feedbacks.svelte:163`; `src/lib/components/chat/Messages/ResponseMessage.svelte:520-526`). Timestamps are epoch seconds (`backend/open_webui/models/feedbacks.py:160-161`). The JSON export grows with the length of every rated conversation, because each row carries its own complete copy; one long chat rated ten times is copied ten times.

### 5.11 Delete Feedback (Admin)

1. In the Feedback list, open the row's **More** menu and choose **Delete** (`src/lib/components/admin/Evaluations/FeedbackMenu.svelte:15-34`). There is **no confirmation step**.
2. On success the toast says `Feedback deleted successfully` and the list returns to page 1 (`src/lib/components/admin/Evaluations/Feedbacks.svelte:115-125`).
3. Deletion is permanent; there is no soft delete (`backend/open_webui/models/feedbacks.py:510-518`).

What deleting does **not** do: the thumb stays highlighted in the user's chat, because the rating is also saved inside the chat record (section 6.2). If that user rates the response again, the update of the old row fails quietly and a new row is created (`src/lib/components/chat/Messages/ResponseMessage.svelte:547-567`).

Bulk deletion exists only in the API: `DELETE /api/v1/evaluations/feedbacks/all` (admin, every row) and `DELETE /api/v1/evaluations/feedbacks` (the caller's own rows). No screen calls them (`backend/open_webui/routers/evaluations.py:337-351`, `:381-396`).

### 5.12 Turn Rating On or Off (Admin)

- **For everyone**: **Admin Panel**, **Settings**, **General**, **Features**, **Message Rating** (`src/lib/components/admin/Settings/General.svelte:274`, `:285-291`). The value is the persistent setting `ui.enable_message_rating`, saved with the other General settings through `POST /api/v1/auths/admin/config` (`backend/open_webui/routers/auths.py:104-119`, `:1269-1296`); see `admin-settings-panels.md` for how that form saves.
- **For some people**: the **Allow Rate Response** permission (section 3.2; `users-groups-roles-and-permissions.md`).
- Turning rating off only hides the buttons; stored feedback, the leaderboard and exports are unchanged.

### 5.13 Use the Analytics Dashboard (Admin)

1. Open **Admin Panel**, **Settings**, then **Analytics** (or `/admin/analytics`, which redirects there). The tab is missing when `ENABLE_ADMIN_ANALYTICS` is off (section 2.1).
2. Choose a period: **Last 24 hours**, **Last 7 days** (the default), **Last 30 days**, **Last 90 days**, **All time** or **Custom range** with a start and an end date; the end date counts as a whole day (`src/lib/components/admin/Analytics/Dashboard.svelte:24-68`, `:251-273`). The choice is remembered in this browser only (keys `analyticsPeriod`, `analyticsCustomStart`, `analyticsCustomEnd` in local storage, `:223-232`).
3. Optionally choose a group (**All Users** or a group name); the selector appears only when groups exist (`:240-250`). The group filter applies to the totals, tables and daily chart, but **not to the hourly chart** of the last 24 hours (`backend/open_webui/routers/analytics.py:209-214`; `backend/open_webui/models/chat_messages.py:1011-1016`).
4. Read the results (`src/lib/components/admin/Analytics/Dashboard.svelte:285-625`):
   - the totals line: messages, tokens (hover: `Token counts are estimates and may not reflect actual API usage`), chats and users;
   - **Daily Messages** (or **Hourly Messages** for 24 hours), a line chart of up to eight models, drawn only when there are at least two points;
   - **Model Usage**: **#**, **Model**, **Messages**, **Users**, **Chats**, **Tokens** and **%** of messages, sortable;
   - **User Activity**: **#**, **User** (name, else email, else the start of the user id), **Messages** and **Tokens**, for the 50 most active people;
   - the footnote `ⓘ Message counts are based on assistant responses.`
5. Click a model row for its window (`src/lib/components/admin/Analytics/AnalyticsModelModal.svelte:179-299`):
   - **Overview**: **Feedback Activity** (tooltip `Thumbs up/down ratings from users on model responses`) for **30D**, **1Y** or **All**, and the ten most common **Tags** of chats that ever used the model, archived chats included (`backend/open_webui/routers/analytics.py:343-421`);
   - **Chats** (only when `ENABLE_ADMIN_CHAT_ACCESS` is on): chats that used the model in the dashboard period, with title, owner and last update, 50 at a time; untitled chats read `No preview`; clicking one opens `/s/<chat id>` (`src/lib/components/admin/Analytics/AnalyticsModelModal.svelte:84-148`, `:207-216`, `:271-286`; `src/lib/components/common/ChatList.svelte:154`).

How the numbers are counted and which time zone applies are in sections 6.4 and 7.3.

## 6. Data Model

Timestamps in both tables below are **epoch seconds** (`backend/open_webui/models/feedbacks.py:160-161`; `backend/open_webui/models/chat_messages.py:280`, `:306`). Tier 1 never queries these tables; this section explains what an admin or the platform maintainer would find.

### 6.1 The `feedback` Table

Created by migration `af906e964978` (`backend/open_webui/migrations/versions/af906e964978_add_feedback_table.py:24-34`); model in `backend/open_webui/models/feedbacks.py:20-30`. It has no foreign keys: `user_id` and the chat id inside `meta` are plain values, so nothing is removed automatically when a user or chat is deleted.

| Column | Type | What the interface puts there | Source |
|---|---|---|---|
| `id` | text, primary key | A random UUID made by the server | `backend/open_webui/models/feedbacks.py:22`, `:152` |
| `user_id` | text | The rater; set by the server from the session, never from the request | `:23`, `:153-158`, `:104-105` |
| `version` | big integer | Always `0` | `:24`, `:159` |
| `type` | text | `rating` | `:25`; `src/lib/components/chat/Messages/ResponseMessage.svelte:508` |
| `data` | JSON | Rating details (table below) | `backend/open_webui/models/feedbacks.py:26`, `:77-83` |
| `meta` | JSON | Where the rating came from (table below) | `:27`, `:86-91` |
| `snapshot` | JSON | `{"chat": <the full chat record>}` | `:28`, `:94-96` |
| `created_at`, `updated_at` | big integer | Set by the server; `updated_at` changes on every save | `:29-30`, `:160-161`, `:480`, `:505` |

**`data`**, built in `src/lib/components/chat/Messages/ResponseMessage.svelte:509-519` and `:588-589`:

| Key | Meaning |
|---|---|
| `rating` | `1` (thumbs up) or `-1` (thumbs down) |
| `model_id` | The model that wrote the response; for arena answers the hidden real model |
| `sibling_model_ids` | Models of the other responses to the same prompt (only when there are any) |
| `reason` | Reason code from the form, or empty |
| `comment` | The typed comment, or empty |
| `tags` | Topic tags (generated, then editable) |
| `details.rating` | The 1-to-10 score, or empty |

**`meta`**, built in `src/lib/components/chat/Messages/ResponseMessage.svelte:520-545`:

| Key | Meaning |
|---|---|
| `arena` | `true` when the response came from an arena model |
| `model_id` | The model id shown on the message (the arena id for arena answers) |
| `message_id` | The rated message's id |
| `message_index` | The position of the message in the conversation |
| `chat_id` | The chat's id |
| `base_models` | For each model involved, its base model id (or empty) |

**`snapshot`** is the whole chat as returned by `GET /api/v1/chats/{id}` at the time of the last save: title, the complete message history with every branch (not only the messages up to the rated one), files lists and other chat fields (`src/lib/components/chat/Messages/ResponseMessage.svelte:498-503`, `:527-529`). The server stores whatever the client sends here (`SnapshotData` accepts extra fields, `backend/open_webui/models/feedbacks.py:94-96`). The admin list and leaderboard deliberately leave the snapshot out (`backend/open_webui/models/feedbacks.py:52-61`, `:70-75`, `:314-318`); the single-row read and the export include it (`backend/open_webui/routers/evaluations.py:354-363`, `:449-459`).

### 6.2 Where Else a Rating Lives

The rating is also written into the chat record itself: the rated message in `chat.history.messages` gets `annotation` (rating, reason, comment, tags, details) and `feedbackId` (`src/lib/components/chat/Messages/ResponseMessage.svelte:486-496`, `:565`, `:570`; `src/lib/components/chat/Messages.svelte:409-416`). Arena answers also carry `selectedModelId` and `arena` (`src/lib/components/chat/Chat.svelte:2838-2841`). Consequences:

- The highlighted thumb a user sees comes from the chat record, not from the `feedback` table (`src/lib/components/chat/Messages/ResponseMessage.svelte:1285-1288`, `:1323-1326`).
- A chat export, a shared chat copy and every later feedback snapshot of the same chat contain the earlier ratings and comments.
- The `chat_message` table does not copy `annotation` (it stores only the fields listed in `backend/open_webui/models/chat_messages.py:211-244`).

### 6.3 The `chat_message` Table (Read by Analytics and Usage)

Defined in `backend/open_webui/models/chat_messages.py:127-172`; created and back-filled from existing chats by migration `8452d01d26d7` (`backend/open_webui/migrations/versions/8452d01d26d7_add_chat_message_table.py:58-215`). It holds one row per message of every saved chat, written alongside the chat record. Its full schema belongs to `chat-conversations-history-and-organisation.md`; the columns analytics and usage rely on are:

| Column | Used for | Source |
|---|---|---|
| `id` | `{chat id}-{message id}` | `backend/open_webui/models/chat_messages.py:131`, `:281-282` |
| `chat_id` | Chat counts, the Chats list in the model window, "Longest active chat"; deleting the chat deletes its rows | `:132`; `backend/open_webui/models/chats.py:2476-2531` |
| `user_id` | Per-user counts, the group filter, the Usage panel | `:133` |
| `role` | Analytics counts only `assistant` rows; the Usage panel counts both | `:136`, `:530-533`; `:697-699` |
| `model_id` | Per-model counts; for arena answers this stays the **arena** id, because the real model is saved separately as `selectedModelId` | `:144`, `:221-222`; `backend/open_webui/utils/middleware.py:4257-4265` |
| `usage` | Token estimates (`input_tokens`/`output_tokens`, or `prompt_tokens`/`completion_tokens`); responses without it add nothing | `:158`, `:63-85` |
| `output`, `meta` | Tool names for **Most used tools** | `:141`, `:150`, `:88-119`, `:885-908` |
| `created_at` | Every date filter and every day or hour bucket; taken from the message's own `timestamp` | `:164`, `:266` |

Indexes on (`model_id`, `created_at`) and (`user_id`, `created_at`) support these queries (`:167-172`).

### 6.4 What Makes the Numbers Go Up or Down

| Event | Effect on analytics and Usage | Source |
|---|---|---|
| A response finishes in a saved chat | One more `assistant` row (and the prompt as a `user` row) | `backend/open_webui/models/chats.py:1141-1187` |
| A chat, a folder of chats or all of a user's chats is deleted | Their rows are deleted, so past counts and tokens drop | `backend/open_webui/models/chats.py:2476-2531` |
| A message is deleted from a chat | Its row and the rows of its direct replies are removed | `backend/open_webui/models/chats.py:935-960`, `:1196-1233` |
| Chats are imported | Their messages are added with their **original** timestamps, so old days can gain activity | `backend/open_webui/models/chats.py:686-708` |
| A chat is archived | No change; archived chats still count | `backend/open_webui/models/chat_messages.py:520-545` (no archive filter) |
| A temporary chat | Kept only in the open browser tab, so never counted unless the user saves it | `chat-conversations-history-and-organisation.md` (Key Concepts, "Temporary chat") |
| Timers and sub-agents post a result into a chat | Counted like any other response | `backend/open_webui/utils/timers.py:364-365`; `backend/open_webui/utils/subagents.py:227-228` |
| A user account is deleted | The user's chats are deleted with it (ground truth), so their rows go too; their **feedback stays** | ground truth; `backend/open_webui/models/feedbacks.py` (no caller of `delete_feedbacks_by_user_id` outside `backend/open_webui/routers/evaluations.py:387`) |
| A feedback row is deleted | Leaderboard and feedback charts change; message analytics do not | `backend/open_webui/routers/evaluations.py:488-509` |

### 6.5 Personal and Sensitive Data in This Area

MedIT GPT chats may contain health details and other personal information. In this area they end up in:

| Place | What it holds | Who can see it |
|---|---|---|
| `feedback.snapshot` | A complete copy of each rated chat, kept after the chat or the user is deleted | Admins (detail window, export); the rater through the API |
| `feedback.data.comment` | Free text the rater typed | Admins; the rater |
| JSON export files | Every snapshot and comment; once downloaded, outside the application's control | Whoever holds the file |
| CSV export files | User ids, comments, reasons and ratings (no snapshot) | Whoever holds the file |
| Analytics **User Activity** and the users endpoint | Names, emails, message counts and token estimates per person | Admins |
| Analytics model window, **Chats** tab | Chat titles and owner names | Admins with `ENABLE_ADMIN_CHAT_ACCESS` |
| Feedback **Chat ID** link and the Chats tab links | The live chat, through `/s/<chat id>` | Admins with `ENABLE_ADMIN_CHAT_ACCESS` |
| Event webhooks for feedback (section 9) | Rater identity and the rating value | Whatever system receives them |

Retention: no code deletes feedback on a schedule or by age; rows stay until an admin deletes them (section 8). Who may export feedback, where exports may be stored and how long feedback should be kept are **TO BE CONFIRMED** (section 14). Tier 1 must not ask users or admins to send exports or screenshots of feedback details, because they can contain health information.

## 7. Settings and Configuration

Code defaults are what the repository says. Live values of persistent settings are rows in the `config` table, and live values of environment settings are in the deployment's environment; both are **TO BE CONFIRMED** for production (ground truth, "Settings: Where a Value Comes From").

### 7.1 Persistent Settings (Stored in the `config` Table)

| Key | Seeded from | Code default | Effect | Edited in | Source |
|---|---|---|---|---|---|
| `evaluation.arena.enable` | `ENABLE_EVALUATION_ARENA_MODELS` | `True` | Adds arena models (or the fallback **Arena Model**) to the model list | Settings, **Evaluations**, **Arena Models** | `backend/open_webui/config.py:2054`, `:3120`; `backend/open_webui/utils/models.py:116-149` |
| `evaluation.arena.models` | `EVALUATION_ARENA_MODELS` (a JSON list of objects) | `[]` | The configured arena models: `id`, `name` and `meta` with `profile_image_url`, `description`, `model_ids`, `filter_mode`, `access_grants`, `i18n` | Settings, **Evaluations**, **Models** | `backend/open_webui/config.py:2055-2065`, `:3121`; `src/lib/components/admin/Settings/Evaluations/ArenaModelModal.svelte:86-98` |
| `ui.enable_message_rating` | `ENABLE_MESSAGE_RATING` | `True` | Shows the thumbs buttons | Settings, **General**, **Features**, **Message Rating** | `backend/open_webui/config.py:2098`, `:3124`; `backend/open_webui/routers/auths.py:119` |
| `ui.enable_community_sharing` | `ENABLE_COMMUNITY_SHARING` | `True` | In this area: shows the `Leave a public review for {modelName}` link in the rating form | Settings, **General**, **Features**, **Community Sharing** ("Allow users to share chats with the Open WebUI community.") | `backend/open_webui/config.py:2096`, `:3123`; `src/lib/components/admin/Settings/General.svelte:275-284`; `src/lib/i18n/locales/en-US/translation.json:2378-2379`; `src/lib/components/chat/Messages/RateComment.svelte:256` |
| `task.tags.enable` | `ENABLE_TAGS_GENERATION` | `True` | Lets the rating flow ask for topic tags; off means ratings get no tags and topic search has nothing to match | Settings, **Interface**, **Tags Generation** ("Create chat tags from conversation content.") | `backend/open_webui/config.py:2297`, `:3144`; `backend/open_webui/routers/tasks.py:53`, `:279-285`; `src/lib/components/admin/Settings/Interface.svelte:437-443`; `src/lib/i18n/locales/en-US/translation.json:2516-2517` |
| `user.permissions` → `chat.rate_response` | `USER_PERMISSIONS_CHAT_RATE_RESPONSE` | `True` | The **Allow Rate Response** permission | Users, Groups, default permissions | `backend/open_webui/config.py:1871`, `:1989` |

The arena keys were renamed from the older `ENABLE_EVALUATION_ARENA_MODELS` and `EVALUATION_ARENA_MODELS` storage names by migration `3ff2c63645b8` (`backend/open_webui/migrations/versions/3ff2c63645b8_reshape_config_to_per_key_rows.py:83-84`); the API still uses the old names as field names (`backend/open_webui/routers/evaluations.py:33-36`, `:295-297`).

If `EVALUATION_ARENA_MODELS` is not valid JSON or not a list of objects, the server logs `Error loading EVALUATION_ARENA_MODELS: {e}` and uses an empty list (`backend/open_webui/config.py:2055-2063`). Because the setting is persistent, the environment value only matters until the first boot (ground truth). Each entry needs `id`, `name` and `meta`: the model-list code reads those three keys directly (`backend/open_webui/utils/models.py:120-133`), so an entry missing one would break model listing. Whether that has happened is a log check for the maintainer.

### 7.2 Environment-Only Settings

These are read once at startup and are not stored in the database; changing one needs a restart.

| Variable | Code default | Effect in this area | Source |
|---|---|---|---|
| `ENABLE_ADMIN_ANALYTICS` | `True` | Registers the `/api/v1/analytics` routes and shows the **Analytics** tab | `backend/open_webui/config.py:2094`; `backend/open_webui/main.py:878-879`, `:2375`; `src/lib/components/chat/SettingsModal.svelte:407-411` |
| `ENABLE_PUBLIC_ACTIVE_USERS_COUNT` | `True` | Lets every signed-in user read `/api/usage` and see the active-user count; off limits both to admins | `backend/open_webui/env.py:367`; `backend/open_webui/main.py:2349`, `:2628-2633` |
| `ENABLE_ADMIN_CHAT_ACCESS` | `True` | Shows the **Chats** tab in the analytics model window and lets the feedback **Chat ID** link open the chat | `backend/open_webui/env.py:371`; `src/lib/components/admin/Analytics/AnalyticsModelModal.svelte:207-216`; `backend/open_webui/routers/chats.py:1226-1233` |
| `BYPASS_ADMIN_ACCESS_CONTROL` | `True` | While on, admins see every arena model regardless of its access list | `backend/open_webui/config.py:2086-2092`; `backend/open_webui/utils/models.py:526-528` |
| `BYPASS_MODEL_ACCESS_CONTROL` | `False` | When on, nobody's model list is filtered, arena models included | `backend/open_webui/env.py:832`; `backend/open_webui/utils/models.py:526-528` |
| `AUXILIARY_EMBEDDING_MODEL` | `TaylorAI/bge-micro-v2` | The small model used for leaderboard topic search | `backend/open_webui/routers/evaluations.py:68-83` |
| `USE_SLIM` | (image build option) | In the slim image, topic search uses the main embedding engine instead | `backend/open_webui/routers/evaluations.py:74-75`, `:234-242` |

`ENABLE_ADMIN_EXPORT` does not govern the feedback export; the Feedback tab's **Export** menu has no such check (`src/lib/components/admin/Evaluations/Feedbacks.svelte:272-301`).

### 7.3 Time Zones and Periods

| View | Where a "day" begins | How the period is chosen | Source |
|---|---|---|---|
| Personal **Usage** heatmap, active days, streaks | Midnight in the user's own time zone (sent by the browser at sign-in and on every app load); UTC when unknown or invalid | Last 730 days, ending now | `backend/open_webui/routers/users.py:714-735`; `backend/open_webui/models/chat_messages.py:52-60`, `:728-737`, `:768-840` |
| Admin analytics **Daily Messages** | Midnight in the **server's** time zone (no per-admin time zone) | Rolling: "Last 7 days" means the last 7 × 24 hours from now | `backend/open_webui/models/chat_messages.py:994`, `:1000-1007`; `src/lib/components/admin/Analytics/Dashboard.svelte:47-58` |
| Admin analytics **Hourly Messages** | Hours in the server's time zone; labels such as "2 PM" are server hours | Last 24 hours | `backend/open_webui/models/chat_messages.py:1037`, `:1043-1052`; `src/lib/components/admin/Analytics/ChartLine.svelte:85-98` |
| Admin analytics **Custom range** | Start is the browser's reading of the chosen date; end adds one day less one second | Two date fields | `src/lib/components/admin/Analytics/Dashboard.svelte:59-64` |
| Feedback history charts (leaderboard window, analytics **Feedback Activity**) | Server time zone | 30 days, 365 days, or from the first rating | `backend/open_webui/models/feedbacks.py:320-384`, `:386-423`; `backend/open_webui/routers/analytics.py:352-404` |
| Feedback list **Updated At** | Relative to the viewer's clock ("3 days ago") | | `src/lib/components/admin/Evaluations/Feedbacks.svelte:494-496` |

The repository has no server time-zone setting (ground truth); the server process's local zone (often UTC in containers) decides the analytics buckets, and the production value is **TO BE CONFIRMED**. JavaScript reads a date written as `2026-10-01` as midnight UTC, so the custom-range start and the date labels drawn by the feedback activity chart (`src/lib/components/admin/Evaluations/ModelActivityChart.svelte:57-63`) can fall on the previous evening for an admin in Toronto; this is to be confirmed in a test environment (section 14).

### 7.4 Fixed Limits in Code

| Limit | Value | Source |
|---|---|---|
| Feedback list page size | 30 | `backend/open_webui/routers/evaluations.py:366`; `src/lib/components/admin/Evaluations/Feedbacks.svelte:518-520` |
| Elo starting rating and K-factor | 1000 and 32 | `backend/open_webui/routers/evaluations.py:100-105` |
| Top tags per model | 5 on the leaderboard, 10 in the analytics window | `backend/open_webui/routers/evaluations.py:136`; `backend/open_webui/routers/analytics.py:418-419` |
| Chats scanned for analytics tags | 10,000 | `backend/open_webui/routers/analytics.py:358-366` |
| Users in **User Activity** | 50 | `backend/open_webui/routers/analytics.py:90`; `src/lib/components/admin/Analytics/Dashboard.svelte:125` |
| Chats per page in the analytics **Chats** tab | 50 (server maximum 100) | `src/lib/components/admin/Analytics/AnalyticsModelModal.svelte:47`; `backend/open_webui/routers/analytics.py:291` |
| Models drawn in the daily chart | 8 | `src/lib/components/admin/Analytics/Dashboard.svelte:316-317` |
| Usage period | 7 to 732 days, default 730 | `backend/open_webui/routers/users.py:708`, `:719` |
| "Active" user window | 3 minutes | `backend/open_webui/models/users.py:903-906` |
| "Running" model window | 3 seconds after the last signal; the browser signals every second | `backend/open_webui/socket/main.py:128`; `src/lib/components/chat/Chat.svelte:2624-2630` |
| Gap that ends an active chat stretch | 30 minutes | `backend/open_webui/models/chats.py:46` |
| Heatmap colour steps | 1, 5, 10 and 20 messages a day | `src/lib/components/chat/Settings/Usage.svelte:226-233` |
| Leaderboard search delay | 0.5 seconds | `src/lib/components/admin/Evaluations/Leaderboard.svelte:94-98` |

## 8. Cron Jobs and Background Processes

There is no crontab (ground truth). *Corrected 2026-10-10: `knowledgebase/tools/ground-truth.md` does not record this fact; it is stated in `CLAUDE.md` ("Startup Order and Background Jobs"), and a search of `backend/`, `scripts/`, the `Dockerfile` and `docker-compose.yaml` found no crontab. The fact stands; only its source was wrong.* Nearly everything in this area happens **at request time**:

| What | When it runs | Notes | Source |
|---|---|---|---|
| Leaderboard (Elo, wins, losses, top tags) | Each time the Leaderboard tab loads or the search box changes | Reads every feedback row; nothing is cached or stored | `backend/open_webui/routers/evaluations.py:222-265` |
| Topic-search embedding model | Loaded the first time someone searches the leaderboard, then kept in memory by that server process | A failure is logged as `Embedding model load failed: {e}` and the search falls back to the plain ranking | `backend/open_webui/routers/evaluations.py:66-83`, `:178-180` |
| Analytics figures | Each dashboard load or filter change; five requests run in parallel | No pre-aggregated tables; large databases make this slower | `src/lib/components/admin/Analytics/Dashboard.svelte:117-161`; `backend/open_webui/routers/analytics.py` |
| Usage panel | Each time the Usage tab opens | | `src/lib/components/chat/Settings/Usage.svelte:269` |
| Tag suggestions for a rating | Right after the first thumbs press on a response, from the browser | A normal model request through the tasks route; uses the task model settings (see `chat-completion-pipeline-and-generation-tasks.md`) | `src/lib/components/chat/Messages/ResponseMessage.svelte:577-600`; `backend/open_webui/routers/tasks.py:279-300` |
| Feedback event delivery | Right after each feedback create, update or delete and each arena settings save | Sent as background tasks to event webhooks and event functions (section 9) | `backend/open_webui/events.py:1062-1071`, `:1159-1171`, `:1174-1202` |

Background loops and startup steps that touch this area:

| What | Schedule | Effect | Source |
|---|---|---|---|
| `periodic_usage_pool_cleanup` | Started at startup by every worker; loops every 3 seconds | Drops models from the "running" list three seconds after their last `usage` signal. With Redis as the websocket manager the list is shared and a Redis lock lets only one worker clean it; without Redis each worker keeps its own list, so the **Running** tooltip only reflects connections handled by the worker that answered | `backend/open_webui/main.py:400`; `backend/open_webui/socket/main.py:133-191`, `:266-308` |
| Arena access migration | Once per startup, in `initialize_runtime_config` | Converts legacy `access_control` entries on arena models to `access_grants` and saves the list | `backend/open_webui/main.py:368`, `:621`, `:660-664` |
| `chat_message` back-fill | Once, when migration `8452d01d26d7` runs | Copies every existing chat's messages into `chat_message` so analytics covers chats from before the table existed | `backend/open_webui/migrations/versions/8452d01d26d7_add_chat_message_table.py:58-215` |

**No retention job.** No code removes feedback rows, their conversation snapshots or `chat_message` rows by age; only the deletions described in sections 5.11 and 6.4 remove them (`backend/open_webui/models/feedbacks.py:510-540` and its only callers in `backend/open_webui/routers/evaluations.py`). Any retention period for feedback is therefore a policy matter, **TO BE CONFIRMED**.

## 9. Notifications and Emails

The application sends **no email** (ground truth). In this area people learn about events through:

### 9.1 On-Screen Messages

Toasts and in-page notices (all listed verbatim in section 10): `Thanks for your feedback!` after saving the rating form, the arena reveal `This response was generated by "{model}"`, `Feedback deleted successfully`, `Settings saved successfully!` after arena changes, and error toasts that print the server's message.

### 9.2 Event Webhooks and Event Functions

Every feedback change publishes an event (`backend/open_webui/routers/evaluations.py`). Events go to the configured **event webhooks** whose filters match, and to active **Event** functions when plugins are on (`backend/open_webui/events.py:1034-1071`, `:1103-1171`). Feedback events are **not** in the list that raises in-app or browser notifications (`backend/open_webui/events.py:669-675`).

| Event name | Sent when | `subject` | `data` | Source |
|---|---|---|---|---|
| `feedback.created` ("Feedback created") | A rating is first saved | the new feedback id | `rating` | `backend/open_webui/routers/evaluations.py:439-445`; `backend/open_webui/events.py:624-626` |
| `feedback.updated` ("Feedback updated") | A rating, form or tags update is saved | the feedback id | `rating` | `backend/open_webui/routers/evaluations.py:478-484`; `backend/open_webui/events.py:627-629` |
| `feedback.deleted` ("Feedback deleted") | One row is deleted | the feedback id | | `backend/open_webui/routers/evaluations.py:503-508`; `backend/open_webui/events.py:630-632` |
| `feedback.deleted_all` ("Feedback deleted all") | All rows, or all of one user's rows, are deleted (and at least one existed) | `all`, or the user's id with type `user` | | `backend/open_webui/routers/evaluations.py:344-350`, `:388-395`; `backend/open_webui/events.py:633-635` |
| `config.updated` ("Config updated") | Arena settings are saved | `evaluation` | the keys changed, `arena_enabled`, `arena_model_count` | `backend/open_webui/routers/evaluations.py:313-323`; `backend/open_webui/events.py:60-62` |

Each event carries an `actor` block with the acting person's id, name, **email**, role and account dates (`backend/open_webui/events.py:704`, `:974-985`, `:1017-1031`). Whether MedIT GPT has any event webhook or event function configured is data, **TO BE CONFIRMED**; see `functions-pipes-filters-actions-and-pipelines.md` for Event functions.

### 9.3 Socket Traffic

While a response is being generated the browser sends a `usage` socket message every second naming the model; this feeds the **Running** list and is not shown to anyone as a notification (`src/lib/components/chat/Chat.svelte:2623-2631`; `backend/open_webui/socket/main.py:407-418`). No socket event is pushed to other people when someone rates a response.

## 10. Error, Warning and Notice Messages (Verbatim)

Placeholders are written `{name}` with the source's variable name (rule 12). A backend `detail` reaches the screen through the toast named in the Trigger column. "Log" rows are server log lines that explain a symptom; users never see them.

### 10.1 Rating a Response (Chat)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Good Response` | Tooltip | `src/lib/components/chat/Messages/ResponseMessage.svelte:1280-1282` | Hovering the thumbs-up button | None | None |
| `Bad Response` | Tooltip | `src/lib/components/chat/Messages/ResponseMessage.svelte:1318-1320` | Hovering the thumbs-down button | None | None |
| `How would you rate this response?` | Notice | `src/lib/components/chat/Messages/RateComment.svelte:119` | The rating form opens after a thumbs press | Optionally fill in the form and press **Save**, or close it | None |
| `This response was generated by "{model}"` | Success toast and in-form notice | `src/lib/components/chat/Messages/RateComment.svelte:74-83`, `:106-112` | The rating form opens on an arena answer; `{model}` is the real model's name, or its id when the model is not in the user's list | None; this is the blind-comparison reveal | If the id is shown instead of a name, the hidden model is not in that user's model list |
| `1 - Awful` / `10 - Amazing` | Scale labels | `src/lib/components/chat/Messages/RateComment.svelte:154-162` | Always under the 1-to-10 scale | Pick a score; only half the scale is available, matching the thumb | None |
| `Why?` | Notice | `src/lib/components/chat/Messages/RateComment.svelte:167-168` | Shown above the reason buttons | Pick a reason (optional) | None |
| `Feel free to add specific details` | Placeholder | `src/lib/components/chat/Messages/RateComment.svelte:222` | Empty comment box | Type a comment (optional) | Remind users not to put personal health information in comments |
| `Thanks for your feedback!` | Success toast | `src/lib/components/chat/Messages/RateComment.svelte:101` | **Save** pressed in the rating form; shown before the server answers | None | It does not prove the save worked; an error toast after it means it failed |
| `Leave a public review for {modelName}` / `Help the community discover great models` | Notice (link) | `src/lib/components/chat/Messages/RateComment.svelte:256-274` | Community sharing is on and the message has a model | Optional: opens `openwebui.com` in a new tab with only the model id in the search | Whether users should be pointed at the upstream community is TO BE CONFIRMED |
| `We could not find what you're looking for :/` | Error toast | `src/lib/components/chat/Messages/ResponseMessage.svelte:498-503`; text `backend/open_webui/constants.py:78`; raised `backend/open_webui/routers/chats.py:1347` | Pressing a thumb when the chat cannot be loaded from the server (deleted, or not the user's) | Reload the page; the thumbs stay disabled until then | Was the chat deleted or opened from someone else's link? |
| `Something went wrong :/` | Error toast | `src/lib/components/chat/Messages/ResponseMessage.svelte:560-562`; text `backend/open_webui/constants.py:16-18`; raised `backend/open_webui/routers/evaluations.py:433-437` | The server could not store a new feedback row (database error) | Try again later | Escalate with the time; the server log has `Error creating a new feedback: {e}` |
| `We could not find what you're looking for :/` | Error toast | `src/lib/components/chat/Messages/ResponseMessage.svelte:592-598`; raised `backend/open_webui/routers/evaluations.py:475-476` | Saving tags for a rating whose row no longer exists (for example deleted by an admin a moment before) | Rate again; a new row is created | None |
| `Your session has expired or the token is invalid. Please sign in again.` (or the `ACCESS_PROHIBITED` text) | Error toast | Any of the toasts above; text in `backend/open_webui/constants.py:59`, `:70-72` | The session ended while rating | Sign in again and re-rate | See `authentication-and-sign-in.md` |
| `Tags generation is disabled` | Response detail (not shown) | `backend/open_webui/routers/tasks.py:281-285` | Rating while **Tags Generation** is off; the browser quietly stores no tags | None | Explains empty tags and an unresponsive leaderboard search |

### 10.2 Admin Evaluations Page

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `No models found` | Empty state | `src/lib/components/admin/Evaluations/Leaderboard.svelte:167-168` | The admin's model list is empty and no rated model exists | Check model connections | See `model-connections-openai-ollama-and-direct.md` |
| `ⓘ The evaluation leaderboard is based on the Elo rating system and is updated in real-time.` | Notice | `src/lib/components/admin/Evaluations/Leaderboard.svelte:257-265` | Always under the leaderboard | None | None |
| `No activity data` | Empty state | `src/lib/components/admin/Evaluations/ModelActivityChart.svelte:186-189` | A model window's chart has no wins or losses in the chosen range | Try **All** | None |
| `No feedback found` / `Try adjusting your search or filter to find what you are looking for.` | Empty state | `src/lib/components/admin/Evaluations/Feedbacks.svelte:306-314` | The Feedback list (with its model filter) has no rows | Set the filter to **All** | Ratings by deleted accounts are not listed |
| `and {COUNT} more` | Notice | `src/lib/components/admin/Evaluations/Feedbacks.svelte:456-461` | A comparison rating involved more than two other models | None | Hover for the full list |
| `Feedback deleted successfully` | Success toast | `src/lib/components/admin/Evaluations/Feedbacks.svelte:115-125` | **Delete** in a row's **More** menu succeeded | None | The user's chat still shows the thumb (section 5.11) |
| `We could not find what you're looking for :/` | Error toast | `src/lib/components/admin/Evaluations/Feedbacks.svelte:116-118`; raised `backend/open_webui/routers/evaluations.py:500-501` | Deleting a row that no longer exists (another admin deleted it) | Reload the list | None |
| `{error}` (the server's message) | Error toast | `src/lib/components/admin/Evaluations/Feedbacks.svelte:85-88` | The Feedback list could not load | Reload; sign in again if the session ended | Escalate with the time if it persists |
| `{err}` (the server's message) | Error toast | `src/lib/components/admin/Evaluations/Feedbacks.svelte:190-195` | An export failed | Retry; very large exports may take long | Escalate with the time and the model filter used |
| `Redirecting you to Open WebUI Community` | Success toast | `src/lib/components/admin/Evaluations/Feedbacks.svelte:127-155` | Not reachable: the function is defined but no button calls it in v0.11.4 | None | If a user reports seeing it, the build differs from this repository |

### 10.3 Arena Model Settings

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Message rating should be enabled to use this feature` | Description and tooltip | `src/lib/components/admin/Settings/Evaluations.svelte:101-111`; `src/lib/i18n/locales/en-US/translation.json:2365` | Always beside the **Arena Models** switch | Keep **Message Rating** on if arena results should be rated | The code does not enforce this |
| `Using the default arena model with all models. Click the plus button to add custom models.` | Notice | `src/lib/components/admin/Settings/Evaluations.svelte:146-151` | Arena models on and none configured | Add an arena model to control which models and who can use it | The fallback **Arena Model** is visible only to admins (section 3.3) |
| `Settings saved successfully!` | Success toast | `src/lib/components/admin/Settings/Evaluations.svelte:30-33` | Arena settings saved | None | None |
| `{err}` (the server's message) | Error toast | `src/lib/components/admin/Settings/Evaluations.svelte:25-28`, `:77-80` | Loading or saving arena settings failed | Retry | Usually the `ACCESS_PROHIBITED` text: the account is not an admin |
| `Name and ID are required, please fill them out` | Error toast | `src/lib/components/admin/Settings/Evaluations/ArenaModelModal.svelte:72-76` | **Save** with an empty name or id | Fill both in | None |
| `Model name already exists, please choose a different one` | Error toast | `src/lib/components/admin/Settings/Evaluations/ArenaModelModal.svelte:78-84` | Adding an arena model whose name matches any model in the list | Choose another name | None |
| `{error}` | Error toast | `src/lib/components/admin/Settings/Evaluations/ArenaModelModal.svelte:100-104` | An unexpected error while saving | Retry | Escalate with the time |
| `Leave empty to include all models or select specific models` | Notice | `src/lib/components/admin/Settings/Evaluations/ArenaModelModal.svelte:377-381` | No models chosen for the arena model | Choose models, or leave empty for "any model" | An empty list means any model the server knows |
| `Confirm your action` / `This action cannot be undone. Do you wish to continue?` | Confirmation | `src/lib/components/common/ConfirmDialog.svelte:130-153`; used at `src/lib/components/admin/Settings/Evaluations/ArenaModelModal.svelte:152-158` | **Delete** in **Edit Arena Model** | **Confirm** removes the arena model | None |
| `Model not found` | Chat error | Raised `backend/open_webui/utils/models.py:465-480`; returned `backend/open_webui/main.py:1640-1645` | Sending to an arena model the user is not allowed to use | Pick another model | The arena model's access list; log line `Model access denied: user_id=%r model_id=%r reason=arena_read_denied` |
| `Error loading EVALUATION_ARENA_MODELS: {e}` | Log | `backend/open_webui/config.py:2055-2063` | Invalid `EVALUATION_ARENA_MODELS` at startup (`{e}` can be `EVALUATION_ARENA_MODELS must be a JSON list of objects`) | None | Maintainer fixes the environment value; only matters before the setting is stored |

### 10.4 Analytics Dashboard

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Token counts are estimates and may not reflect actual API usage` | Tooltip | `src/lib/components/admin/Analytics/Dashboard.svelte:294-301` | Hovering the token total | None | Provider bills are the source of truth for cost |
| `No data` | Empty state | `src/lib/components/admin/Analytics/Dashboard.svelte:509-515`, `:610-616` | No assistant responses in the period or group (or the dashboard failed to load) | Widen the period; check the group | A load failure shows the same empty tables; the browser console has `Dashboard load failed:` |
| `ⓘ Message counts are based on assistant responses.` | Notice | `src/lib/components/admin/Analytics/Dashboard.svelte:623-625` | Always | None | Explains why counts are about half of all messages |
| `Thumbs up/down ratings from users on model responses` | Tooltip | `src/lib/components/admin/Analytics/AnalyticsModelModal.svelte:225-229` | Hovering **Feedback Activity** | None | None |
| `No activity data` | Empty state | `src/lib/components/admin/Evaluations/ModelActivityChart.svelte:186-189` (shared chart) | The model has no ratings in the range | Try **All** | None |
| `No preview` | Notice | `src/lib/components/admin/Analytics/AnalyticsModelModal.svelte:103`, `:135` | A chat in the **Chats** tab has no title | None | None |
| `No chats found` | Empty state | `src/lib/components/common/ChatList.svelte:28`, `:121-124` | No chats used the model in the dashboard period | Widen the period | None |

### 10.5 Usage Panel and Active Users

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Failed to load usage` | Error notice | `src/lib/components/chat/Settings/Usage.svelte:283-286` | `GET /api/v1/users/usage` failed | Close and reopen Settings; sign in again if the session ended | Escalate with the time; the browser console has `Usage load failed:` |
| `No usage data found` | Empty state | `src/lib/components/chat/Settings/Usage.svelte:410-415` | No messages and no tokens recorded for the user | None | Temporary chats are never counted; deleted chats no longer count |
| `No model usage found` | Empty state | `src/lib/components/chat/Settings/Usage.svelte:453-457` | No assistant responses in the last 730 days | None | None |
| `{label}: {tokens} tokens, {messages} messages, {chats} chats ({model}). {modelSummary}` | Tooltip | `src/lib/components/chat/Settings/Usage.svelte:235-254` | Hovering a heatmap square; `{label}` is the date, `Week of {date}` or `Through {date}`; `{modelSummary}` is up to three models with counts, or `No model data` | None | None |
| `Token counts are estimates and may not reflect actual API usage` | Notice | `src/lib/components/chat/Settings/Usage.svelte:486-488` | Always at the bottom of the panel | None | None |
| `start_date must be before end_date` | Error (API) | `backend/open_webui/routers/users.py:722-726` | A caller asked for a period that ends before it starts; the panel itself never sends dates | None | Only seen by API users |
| `Running: {model_ids} ✨` | Tooltip | `src/lib/components/layout/Sidebar/UserMenu.svelte:142-147` | Hovering the active-user count while responses are being generated | None | Lists model ids, not names |
| `Active Users` | Tooltip | `src/lib/components/layout/Sidebar/UserMenu.svelte:144-146` | Hovering the count when nothing is generating | None | None |
| `Access denied. Only administrators can view usage statistics.` | Error (API, 403) | `backend/open_webui/main.py:2628-2633` | A non-admin calls `/api/usage` while `ENABLE_PUBLIC_ACTIVE_USERS_COUNT` is off; the menu does not call it then | None | None |
| `Internal Server Error` | Error (API, 500) | `backend/open_webui/main.py:2639-2643` | Reading usage failed | None | Log line `Error getting usage statistics: {e}` |

### 10.6 Permission Editor

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `This is a default user permission and will remain enabled.` | Warning | `src/lib/components/admin/Users/Groups/Permissions.svelte:792-797` | **Allow Rate Response** switched off for a group while the default is on | Turn it off in the default permissions instead | See section 3.2 |

### 10.7 Server Log Lines

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Error creating a new feedback: {e}` | Log (exception) | `backend/open_webui/models/feedbacks.py:172-174` | Database error while inserting feedback | None | Maintainer checks the database |
| `Embedding model load failed: {e}` | Log (error) | `backend/open_webui/routers/evaluations.py:76-83` | The topic-search model could not be loaded (for example it could not be downloaded) | None | Search falls back to the plain ranking |
| `Embedding error: {e}` | Log (error) | `backend/open_webui/routers/evaluations.py:186-192` | The topic-search model failed while encoding | None | Same fallback |
| `Model access denied: user_id=%r model_id=%r reason=arena_read_denied` | Log (warning) | `backend/open_webui/utils/models.py:475-480` | Someone tried to use an arena model they cannot read | None | Compare with the arena model's access list |
| `Error getting usage statistics: {e}` | Log (error) | `backend/open_webui/main.py:2641-2642` | `/api/usage` failed | None | Usually a database problem |
| `Usage pool cleanup failed. Retrying.` | Log (exception) | `backend/open_webui/socket/main.py:306-308` | The cleanup loop hit an error | None | Usually Redis; see `websockets-realtime-and-redis.md` |
| `Unable to renew usage cleanup lock. Retrying cleanup ownership.` | Log (warning) | `backend/open_webui/socket/main.py:277-279` | With Redis, this worker lost the cleanup lock | None | Normal now and then with several workers |
| `Event webhook failed for {id}` | Log (exception) | `backend/open_webui/events.py:1058-1059` | Delivering a feedback or config event to a webhook failed | None | See section 9.2 |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it explains, checks what the person sees, and escalates. It does not change settings, permissions, ratings or feedback. Never ask for exports, screenshots of feedback details or pasted chat text, because they may contain health information; ask for the chat id (the part after `/c/` in the address bar) and the approximate time instead.

### 11.1 "The thumbs buttons are missing"

**Symptom.** No **Good Response** / **Bad Response** buttons under an answer.

**Likely causes, in order.**
1. The answer is not the latest one: on older answers the buttons are invisible until the pointer is over the message or keyboard focus is inside it (`src/app.css:68-76`; `src/lib/components/chat/Messages/ResponseMessage.svelte:1283-1285`).
2. The chat is a **temporary chat** (including when an admin enforces temporary chats); rating is never offered there (`src/lib/components/chat/Messages/ResponseMessage.svelte:1279`; `chat-conversations-history-and-organisation.md`).
3. The answer is still being generated or stopped before finishing (`message.done` is false) (`:1085`).
4. The page is a read-only view, such as a shared link under `/s/` (`:1278`).
5. An admin has switched **Message Rating** off for everyone (section 3.2).
6. The person lacks **Allow Rate Response** (default permission off and no group grants it) (section 3.2).

**Diagnostic steps.** Ask whether the buttons are missing on the latest answer too; ask them to hover over an older answer; check the address bar (`/c/<id>` is a saved chat, `/s/<id>` is a shared view); ask whether the chat was started as temporary. Ask an admin to read the **Message Rating** switch and the person's effective **Allow Rate Response** permission.

**Resolution.** Explain hover behaviour; for temporary chats, explain that rating needs a saved chat. If settings or permissions are the cause, that is an admin decision.

**Escalation.** To an admin: the person's account (from the ticket, not this document), whether every chat or one chat is affected, the chat id, and whether the chat is temporary.

### 11.2 "I pressed thumbs up and nothing happened" or "The thumbs buttons are greyed out"

**Symptom.** Pressing a thumb does not open the form, or the buttons stay dimmed with a busy cursor.

**Likely causes, in order.**
1. The browser could not load the chat from the server, showed an error toast (often `We could not find what you're looking for :/`) and left the buttons disabled until the page is reloaded (`src/lib/components/chat/Messages/ResponseMessage.svelte:480-503`, `:1290`, `:1328`).
2. The session expired (`Your session has expired or the token is invalid. Please sign in again.`).
3. A slow network: the buttons are disabled while saving (`:1290`).

**Diagnostic steps.** Ask what toast appeared; ask them to reload and try again; check whether the chat still exists in their sidebar.

**Resolution.** Reload the page; sign in again if prompted. A chat that no longer exists cannot be rated.

**Escalation.** If it fails after a reload in a chat that exists: chat id, time, the exact toast text.

### 11.3 "I can't remove my rating"

**Symptom.** A person wants to undo a thumbs up or down.

**Likely causes, in order.**
1. There is no undo: pressing the same thumb again keeps the rating; pressing the other thumb switches it (`src/lib/components/chat/Messages/ResponseMessage.svelte:486-496`).

**Diagnostic steps.** None needed.

**Resolution.** Explain they can switch the rating and edit the comment. Removing the stored feedback needs an admin, and even then the thumb stays highlighted in their chat because the rating is also saved in the chat (section 6.2).

**Escalation.** If they need the stored feedback (and its conversation copy) deleted, for example for privacy reasons: escalate to an admin with the chat id and the time of rating. A privacy concern also goes to the U of T Privacy Office route the organisation uses (TO BE CONFIRMED).

### 11.4 "The leaderboard is empty" or "Every model shows a dash"

**Symptom.** On **Evaluations**, **Leaderboard**, models are listed with `-` for rating, won and lost, or the page says `No models found`.

**Likely causes, in order.**
1. People rated single answers only. The leaderboard counts only comparisons, that is ratings of an answer that has sibling answers to the same prompt (section 5.3) (`backend/open_webui/routers/evaluations.py:108-131`).
2. Few or no ratings exist at all (message rating off, permission off, or simply unused).
3. Feedback was deleted.
4. `No models found`: the admin's model list is empty and no rated model exists (`src/lib/components/admin/Evaluations/Leaderboard.svelte:167-168`).

**Diagnostic steps.** With an admin, open the **Feedback** tab: is the count beside it zero? Do rows show a second line of other models (comparisons) under **Models**? (`src/lib/components/admin/Evaluations/Feedbacks.svelte:443-475`.)

**Resolution.** Explain that rankings appear only after people compare models: side-by-side models, regenerating, or using an arena model, then rating one of the answers.

**Escalation.** None normally. If the Feedback tab shows comparison rows but the leaderboard stays at `-`, escalate with the time and the number of feedback rows.

### 11.5 "The leaderboard numbers don't match the chart" or "Won and Lost don't add up"

**Symptom.** The model window's activity chart, the Feedback count and the table disagree.

**Likely causes, in order.**
1. The chart counts every thumbs up and down for that model; the table counts only comparisons (`backend/open_webui/models/feedbacks.py:320-384`; `backend/open_webui/routers/evaluations.py:108-131`).
2. A comparison counts for both models: one model's win is the other's loss, and a regenerated answer from the same model adds one win and one loss to that model (section 5.3).
3. The number beside **Leaderboard** is the number of models listed, not the number of ratings (`src/lib/components/admin/Evaluations.svelte:38-47`).
4. The Feedback list hides ratings from deleted accounts, while the leaderboard still counts them (`backend/open_webui/models/feedbacks.py:215-224`, `:314-318`).

**Diagnostic steps.** Compare which view the person is reading; note the model and range.

**Resolution.** Explain the different counting rules.

**Escalation.** None unless figures are needed for a report; then the maintainer can compute them from an export.

### 11.6 "Searching the leaderboard doesn't change the ranking"

**Symptom.** Typing a topic in the leaderboard search leaves the order unchanged.

**Likely causes, in order.**
1. Ratings have no tags, usually because **Tags Generation** is off (section 7.1); without tags there is nothing to match, and the plain ranking is returned (`backend/open_webui/routers/evaluations.py:182-184`).
2. The topic-search model could not be loaded, for example because the server cannot download it; the server logs `Embedding model load failed: {e}` and returns the plain ranking (`:72-83`, `:178-180`).
3. In the slim image the main embedding engine is used instead; if it fails the request fails and the page keeps showing the previous ranking (`:234-242`; `src/lib/components/admin/Evaluations/Leaderboard.svelte:88-91`). TO BE CONFIRMED in a test environment.
4. The first search after a restart is slow while the model loads.

**Diagnostic steps.** Open a model's window: does **Tags** show anything? Ask the admin whether **Tags Generation** is on.

**Resolution.** Explain the dependency on tags. Turning tag generation on is an admin decision and only affects new ratings.

**Escalation.** To the maintainer with the time of the search if tags exist but search has no effect (log check for the two embedding lines in section 10.7).

### 11.7 "I can't find the Analytics page" or "Evaluations is missing"

**Symptom.** An admin cannot find analytics, or a user cannot find evaluations.

**Likely causes, in order.**
1. In v0.11.4 analytics lives in the Settings window: **Admin Panel**, **Settings**, **Analytics** (under **Quality**). `/admin/analytics` only redirects there (section 2.1).
2. `ENABLE_ADMIN_ANALYTICS` is off, so the tab does not exist and `/admin/analytics` returns to `/admin` (`src/routes/(app)/admin/analytics/+page.svelte:6-12`).
3. The person is not an admin: the Admin Panel and the admin Settings tabs are admin-only (section 3.1).
4. Arena settings and the Evaluations page are two different places: arena models are in **Settings**, **Evaluations**; ratings are in **Admin Panel**, **Evaluations** (section 2.1).

**Diagnostic steps.** Confirm the person's role; ask them to open **Admin Panel**, **Settings** and look for **Analytics** under **Quality**; try the search box at the top of the Settings list.

**Resolution.** Give the path. If the tab is absent for an admin, analytics is switched off in this deployment.

**Escalation.** Whether analytics should be on is a platform decision (environment variable, needs a restart): send to the maintainer.

### 11.8 "Analytics shows the wrong day" or "The hours are off"

**Symptom.** Activity appears on the day before or after, or the hourly chart is shifted by several hours.

**Likely causes, in order.**
1. Admin analytics cuts days and hours in the **server's** time zone, not the admin's; if the server runs on UTC, evening activity in Toronto lands on the next day and hourly labels are 4 or 5 hours ahead (section 7.3) (`backend/open_webui/models/chat_messages.py:994`, `:1037`).
2. Periods are rolling: "Last 7 days" is the last 168 hours, not seven calendar days (`src/lib/components/admin/Analytics/Dashboard.svelte:47-58`).
3. A custom start date is read by the browser as midnight UTC, which is the previous evening in Toronto (`:59-64`). TO BE CONFIRMED in a test environment.
4. Imported chats keep their original dates, so old days can gain activity (section 6.4).
5. The feedback activity charts can label each bar with the previous day for viewers west of UTC (`src/lib/components/admin/Evaluations/ModelActivityChart.svelte:57-63`). TO BE CONFIRMED in a test environment.

**Diagnostic steps.** Ask which chart, which period and what time zone the admin is in; note that the personal **Usage** panel, by contrast, uses the person's own time zone.

**Resolution.** Explain the server-time rule; suggest wider periods for reports.

**Escalation.** The server's time zone is a platform setting (TO BE CONFIRMED); send questions about it to the maintainer.

### 11.9 "Analytics numbers are lower than expected" or "Usage went down"

**Symptom.** Message or token totals drop, or are smaller than people expect.

**Likely causes, in order.**
1. Only assistant responses are counted (`ⓘ Message counts are based on assistant responses.`).
2. Deleted chats take their messages out of every count (section 6.4).
3. Temporary chats are never counted.
4. A group filter is selected (and, for the 24-hour view, ignored, which can make that view look larger) (section 5.13).
5. Arena answers are counted under the arena model's id, not the real model (section 6.3).
6. Tokens are zero for answers whose provider returned no usage figures (section 4).

**Diagnostic steps.** Ask for the period, group and model; check whether chats were deleted recently (by the person, or because an account was deleted).

**Resolution.** Explain the counting rules. Analytics is not a billing record.

**Escalation.** For reconciliation with provider bills, send to the maintainer; provider dashboards are the source of truth for cost (TO BE CONFIRMED which providers MedIT GPT uses).

### 11.10 "I can't find Usage"

**Symptom.** A person cannot find their own usage figures.

**Likely causes, in order.**
1. It is a tab in the Settings window, not a page: user menu, **Settings**, **Usage** under **Data** (section 2.1).
2. The person searched the sidebar instead of the Settings window.

**Diagnostic steps.** Ask them to open **Settings** and type "usage" in the search box at the top of the tab list.

**Resolution.** Give the path or the link `/?settings=usage`. The tab is offered to every signed-in user (`src/lib/components/chat/SettingsModal.svelte:379-411`).

**Escalation.** None; if the tab is genuinely absent, report the version shown in **About**.

### 11.11 "Usage says Failed to load usage" or "No usage data found"

**Symptom.** The Usage tab shows `Failed to load usage` or `No usage data found`.

**Likely causes, in order.**
1. `No usage data found`: the person has no saved messages in the last 730 days and no token estimates at all, for example a new account or one that only used temporary chats (`src/lib/components/chat/Settings/Usage.svelte:57`, `:410-415`).
2. Their chats were deleted, which removes the history the panel reads.
3. `Failed to load usage`: the request failed (session expired, server busy) (`:131-140`, `:283-286`).

**Diagnostic steps.** Ask whether they have saved chats in the sidebar; ask them to close Settings, reload and reopen.

**Resolution.** Explain; sign in again if needed.

**Escalation.** If `Failed to load usage` persists for one person: the time and their account, to the maintainer.

### 11.12 "My streak or active days are wrong"

**Symptom.** The Usage panel's streak, active days or heatmap squares do not match the person's memory.

**Likely causes, in order.**
1. Days are cut in the time zone last sent by their browser (at sign-in and on every app load); the whole history is redrawn in that zone, so after travel, on a device set to another zone, or if none was ever recorded (UTC is used), days shift (section 7.3; `src/routes/+layout.svelte:1294-1298`).
2. The current streak counts back from today; one day without a message resets it (`backend/open_webui/routers/users.py:392-408`).
3. Deleted chats remove their days.

**Diagnostic steps.** Ask for their time zone and whether they recently signed in from elsewhere.

**Resolution.** Explain; reloading the app on their usual device, with its clock set to their home time zone, records that zone again.

**Escalation.** None.

### 11.13 "Exported feedback is huge"

**Symptom.** The JSON export from the Feedback tab is very large or slow.

**Likely causes, in order.**
1. Every row carries a complete copy of its chat, including every branch, and the same chat is copied again for each rating (sections 5.10 and 6.1).
2. No model filter was set, so every row was exported.

**Diagnostic steps.** Ask which format and filter were used.

**Resolution.** Suggest the CSV export (no snapshots) or a model filter. Remind the admin that the export holds conversation text that may include health information and must be stored and shared under the organisation's data rules (TO BE CONFIRMED).

**Escalation.** If an export is needed for analysis or has been shared outside the team, escalate to the platform owner and, for a possible privacy incident, the U of T privacy route (privacy.utoronto.ca).

### 11.14 "The CSV export has an empty chat_id column"

**Symptom.** In the CSV, `chat_id` is blank for every row.

**Likely causes, in order.**
1. The CSV builder reads the chat id from the wrong place (`data.chat_id`), while the interface stores it in `meta.chat_id` (`src/lib/components/admin/Evaluations/Feedbacks.svelte:163`; `src/lib/components/chat/Messages/ResponseMessage.svelte:520-526`).

**Diagnostic steps.** None needed.

**Resolution.** Use the JSON export, where `meta.chat_id` is present. This is product behaviour in v0.11.4.

**Escalation.** Report as a defect to the maintainer if a fix is wanted.

### 11.15 "I deleted a rating but the thumb is still highlighted" or "A deleted rating came back"

**Symptom.** After an admin deletes a feedback row, the person still sees their thumb highlighted, or a new row appears later.

**Likely causes, in order.**
1. The rating is also stored in the chat record, which the delete does not touch (section 6.2).
2. When the person rates the same answer again, the update of the deleted row fails quietly and a new row is created (`src/lib/components/chat/Messages/ResponseMessage.svelte:547-567`).

**Diagnostic steps.** None needed.

**Resolution.** Explain both behaviours.

**Escalation.** None.

### 11.16 "I can't see the Arena Model" or "Only admins can see the arena"

**Symptom.** People cannot pick an arena model, or only admins can.

**Likely causes, in order.**
1. The arena model's access list is empty, which means private; the built-in **Arena Model** is always private (section 3.3).
2. **Arena Models** is switched off (`evaluation.arena.enable`).
3. The person's groups are not on the access list.

**Diagnostic steps.** Ask an admin to open **Settings**, **Evaluations**, open the arena model's gear icon and read its access setting.

**Resolution.** Opening access is an admin decision.

**Escalation.** To an admin with the arena model's name and the people or groups who need it.

### 11.17 "The arena keeps picking the same model" or "It picked a model I didn't expect"

**Symptom.** Arena answers seem to come from one model, or from a model nobody intended.

**Likely causes, in order.**
1. Each request picks at random, so repeats happen; only regenerating asks again (`backend/open_webui/utils/middleware.py:2413-2421`).
2. An empty model list means any non-arena model the server knows, including ones not meant for comparison (section 5.4).
3. **Exclude** mode picks from everything not listed.

**Diagnostic steps.** Ask an admin to read the arena model's **Models** list and **Include**/**Exclude** mode.

**Resolution.** Admin decision.

**Escalation.** Questions about which models may be offered through the arena, and to whom, go to the maintainer (see section 14 for a related security referral).

### 11.18 "The arena reveal shows a code instead of a model name"

**Symptom.** `This response was generated by "{model}"` shows an id rather than a friendly name.

**Likely causes, in order.**
1. The chosen model is not in that person's own model list, so only its id is known to the browser (`src/lib/components/chat/Messages/RateComment.svelte:74-83`).

**Diagnostic steps.** None needed.

**Resolution.** Explain.

**Escalation.** If this exposes models people should not be routed to, see 11.17.

### 11.19 "The active users count is missing or looks wrong"

**Symptom.** No green dot and number in the user menu, or the number or the **Running** list looks off.

**Likely causes, in order.**
1. `ENABLE_PUBLIC_ACTIVE_USERS_COUNT` is off and the person is not an admin (section 7.2).
2. Nobody counts as active: the dot appears only when at least one account was active in the last three minutes (`src/lib/components/layout/Sidebar/UserMenu.svelte:142`; `backend/open_webui/models/users.py:901-908`).
3. With several workers and no Redis, the **Running** list only reflects the worker that answered (section 8).

**Diagnostic steps.** Ask whether they are an admin; reopen the menu after a minute.

**Resolution.** Explain; the number is a rough indicator.

**Escalation.** None.

### 11.20 "A feedback entry has disappeared from the Feedback list"

**Symptom.** An admin can no longer find a rating they saw before.

**Likely causes, in order.**
1. The rater's account was deleted: the list only shows rows whose user still exists, though the row is still in exports and on the leaderboard (`backend/open_webui/models/feedbacks.py:215-224`).
2. Another admin deleted it (no confirmation step, section 5.11).
3. A model filter is set.

**Diagnostic steps.** Set the filter to **All**; ask whether the account was removed.

**Resolution.** Explain. The row can still be found in a JSON export, which should only be made if there is a real need (privacy).

**Escalation.** If feedback of a deleted person must be removed for privacy, escalate to the platform owner; it is not removed automatically.

### 11.21 "Feedback Details shows no prompt or response" or "The Chat ID link doesn't open"

**Symptom.** In **Feedback Details** the **Prompt**/**Response** parts are missing, or the **Chat ID** link shows an error.

**Likely causes, in order.**
1. The link opens the chat as it is now; if the chat was deleted, or admin chat access is off, it fails (`backend/open_webui/routers/chats.py:1226-1233`).
2. The row has no usable conversation copy (for example it was created by an API client rather than the interface), so the window cannot find the messages (`src/lib/components/admin/Evaluations/FeedbackModal.svelte:75-99`). TO BE CONFIRMED in a test environment.
3. The details request failed and only the summary fields are shown (`:24-35`).

**Diagnostic steps.** Ask whether the chat still exists; reopen the window.

**Resolution.** Explain that the stored copy is shown when available and the link is to the live chat.

**Escalation.** If many rows are affected: the time and the number of rows, to the maintainer.

## 12. Local Customisations

Checked with read-only `git diff main...uoft -- <paths>` (committed fork changes) and `git diff -- <paths>` (uncommitted working-tree changes) over every file in this area's scope and the shared files cited here.

| File | Committed fork change (`main...uoft`) | Uncommitted change | Effect on this area |
|---|---|---|---|
| `backend/open_webui/routers/evaluations.py`, `backend/open_webui/models/feedbacks.py`, `backend/open_webui/routers/analytics.py`, `backend/open_webui/models/chat_messages.py` | None | None | Matches upstream v0.11.4 |
| `src/lib/components/admin/Evaluations.svelte`, `src/lib/components/admin/Evaluations/`, `src/lib/components/admin/Analytics.svelte`, `src/lib/components/admin/Analytics/`, `src/routes/(app)/admin/evaluations/`, `src/routes/(app)/admin/analytics/` | None | None | Matches upstream |
| `src/lib/components/admin/Settings/Evaluations.svelte`, `src/lib/components/admin/Settings/Evaluations/`, `src/lib/apis/evaluations/`, `src/lib/apis/analytics/` | None | None | Matches upstream |
| `src/lib/components/chat/Messages/RateComment.svelte`, `src/lib/components/chat/Settings/Usage.svelte` | None | None | Matches upstream |
| `src/lib/components/chat/Messages/ResponseMessage.svelte` | Yes: the **Hide Processing Details** setting (status history, "Thinking..." indicator, code executions) | Yes: a rework of the same feature | **None on rating**: the changed lines are in the status and progress parts of the file, not in `feedbackHandler`, the thumbs buttons or the rating form. Line numbers cited here are from the working tree |
| `src/lib/components/chat/Chat.svelte` | None | Yes: five lines after the usage handling that mark a resumed tool-approval message as not done | None on the arena reveal or usage signal; citations are from the working tree |
| `src/lib/i18n/locales/en-US/translation.json` | Yes: four keys for **Hide Processing Details** and **Inline Citations** | Yes: one description reworded | None; no key used in this area changed |
| `src/routes/+layout.svelte` | Yes: browser notification titles use the app name instead of "Open WebUI" | None | None on the settings deep link or time-zone sync cited here |
| `backend/open_webui/main.py`, `backend/open_webui/config.py`, `backend/open_webui/routers/users.py`, `backend/open_webui/utils/models.py`, `backend/open_webui/utils/middleware.py`, `backend/open_webui/utils/chat.py`, `backend/open_webui/socket/main.py`, `backend/open_webui/events.py`, `src/lib/components/chat/SettingsModal.svelte` | None | None | Matches upstream |

**Conclusion: this area matches upstream Open WebUI v0.11.4.** The product name in event payloads and webhook titles comes from `WEBUI_NAME` (`backend/open_webui/events.py:1038`), which the fork defaults to `MedIT GPT` (ground truth). Licence comments in this area (the fallback logo path `/favicon.png` for arena models and leaderboard images, the community wordmark comments) are unchanged in code and must stay so (`backend/open_webui/config.py:2071-2074`; `src/lib/components/admin/Evaluations/Leaderboard.svelte:216-221`; `src/lib/components/admin/Evaluations/Feedbacks.svelte:128-131`). The file served at `/favicon.png` is one of the images the fork replaced with U of T artwork (ground truth, "Fork changes"), so the built-in **Arena Model**, new arena models without an uploaded picture, and leaderboard or analytics rows whose model picture fails to load show that replacement image (`backend/open_webui/config.py:2074`; `src/lib/components/admin/Settings/Evaluations/ArenaModelModal.svelte:49`; `src/lib/components/admin/Evaluations/Leaderboard.svelte:216-221`; `src/lib/components/admin/Analytics/Dashboard.svelte:486-491`).

## 13. Source File Index

Every file cited in this document, with what it contributes. Files marked **(scope)** are this area's own; the rest are shared files read for one behaviour.

### 13.1 Backend

| File | Role here |
|---|---|
| `backend/open_webui/routers/evaluations.py` **(scope)** | Feedback create, read, update, delete; admin list, export, bulk delete; Elo leaderboard and topic search; model history; arena config read and save; feedback events |
| `backend/open_webui/models/feedbacks.py` **(scope)** | `feedback` table, forms, list queries (joined to users), leaderboard and history queries, deletes |
| `backend/open_webui/routers/analytics.py` **(scope)** | Admin analytics routes: summary, models, users, messages, daily or hourly, tokens, model chats, model overview |
| `backend/open_webui/models/chat_messages.py` **(scope, analytics parts)** | `chat_message` table; token extraction; all analytics and personal usage aggregations; time-zone helpers |
| `backend/open_webui/main.py` | Router mounts (analytics only when enabled); `/api/config` feature flags; `/api/usage`; arena access migration at startup; chat endpoint access check and error conversion; static page fallback |
| `backend/open_webui/config.py` | Arena, analytics, rating, community sharing, tags generation and rate permission defaults; `DEFAULT_CONFIG` keys; fallback **Arena Model** |
| `backend/open_webui/env.py` | `ENABLE_PUBLIC_ACTIVE_USERS_COUNT`, `ENABLE_ADMIN_CHAT_ACCESS`, `BYPASS_MODEL_ACCESS_CONTROL` |
| `backend/open_webui/constants.py` | Text of `Something went wrong :/`, `We could not find what you're looking for :/` and the session messages |
| `backend/open_webui/events.py` | Feedback and config event definitions, actor fields, webhook and event-function delivery, notification event list |
| `backend/open_webui/utils/models.py` | Adds arena models to the model list; arena access check and list filtering |
| `backend/open_webui/utils/middleware.py` | Random arena model choice before processing; saving `selectedModelId` on the message |
| `backend/open_webui/utils/chat.py` | Fallback arena choice and `selected_model_id` in responses |
| `backend/open_webui/utils/access_control/__init__.py` | `has_access` rules for config-stored access lists; legacy `access_control` conversion |
| `backend/open_webui/utils/auth.py` | `get_verified_user` and `get_admin_user` refusals |
| `backend/open_webui/utils/timers.py`, `backend/open_webui/utils/subagents.py` | Write result messages into chats, so they count in analytics |
| `backend/open_webui/routers/users.py` | `/api/v1/users/usage` for the personal Usage panel; streaks and weekly or cumulative views; rate permission field |
| `backend/open_webui/routers/auths.py` | Admin config keys for **Message Rating** and **Community Sharing**; time-zone update route |
| `backend/open_webui/routers/tasks.py` | Tags generation task and its `Tags generation is disabled` answer |
| `backend/open_webui/routers/chats.py` | Chat lookup used by the rating flow; `/s/<chat id>` fallback for admins |
| `backend/open_webui/models/chats.py` | Writes `chat_message` rows with each chat change; deletes them with chats; usage chat stats; chats-by-model list |
| `backend/open_webui/models/users.py` | Active-user count |
| `backend/open_webui/socket/main.py` | Usage pool, `usage` socket handler, cleanup loop, Redis lock |
| `backend/open_webui/utils/audit.py` | Optional audit log: which requests it records and how much of each body it keeps (section 14.3; row added 2026-10-10) |

### 13.2 Migrations

| File | Role here |
|---|---|
| `backend/open_webui/migrations/versions/af906e964978_add_feedback_table.py` | Creates the `feedback` table |
| `backend/open_webui/migrations/versions/8452d01d26d7_add_chat_message_table.py` | Creates `chat_message` and back-fills it from existing chats |
| `backend/open_webui/migrations/versions/3ff2c63645b8_reshape_config_to_per_key_rows.py` | Maps the old arena setting names to `evaluation.arena.*` |

### 13.3 Front End: Pages and Components

| File | Role here |
|---|---|
| `src/routes/(app)/admin/evaluations/+page.svelte` **(scope)** | Redirects to the Leaderboard tab |
| `src/routes/(app)/admin/evaluations/[tab]/+page.svelte` **(scope)** | Renders the Evaluations page for a tab |
| `src/routes/(app)/admin/analytics/+page.svelte`, `src/routes/(app)/admin/analytics/[tab]/+page.svelte` **(scope)** | Redirect into the Settings window's Analytics tab, or to `/admin` when analytics is off |
| `src/lib/components/admin/Evaluations.svelte` **(scope)** | Leaderboard and Feedback tabs with counts |
| `src/lib/components/admin/Evaluations/Leaderboard.svelte` **(scope)** | Leaderboard table, sorting, topic search, footnote |
| `src/lib/components/admin/Evaluations/LeaderboardModal.svelte` **(scope)** | Model window with activity chart and tags |
| `src/lib/components/admin/Evaluations/ModelActivityChart.svelte` **(scope)** | Wins and losses bar chart (also used by analytics) |
| `src/lib/components/admin/Evaluations/Feedbacks.svelte` **(scope)** | Feedback list, filter, sorting, export (JSON and CSV), delete, unused community share function |
| `src/lib/components/admin/Evaluations/FeedbackModal.svelte` **(scope)** | **Feedback Details** window |
| `src/lib/components/admin/Evaluations/FeedbackMenu.svelte` **(scope)** | Row menu with **Delete** |
| `src/lib/components/admin/Analytics.svelte` **(scope)** | Admin-only wrapper for the dashboard |
| `src/lib/components/admin/Analytics/Dashboard.svelte` **(scope)** | Periods, group filter, totals, chart, Model Usage and User Activity tables |
| `src/lib/components/admin/Analytics/ChartLine.svelte` **(scope)** | Daily or hourly line chart and its date labels |
| `src/lib/components/admin/Analytics/AnalyticsModelModal.svelte` **(scope)** | Model window: Overview and Chats tabs |
| `src/lib/components/admin/Settings/Evaluations.svelte` **(scope)** | **Arena Models** switch and list |
| `src/lib/components/admin/Settings/Evaluations/ArenaModelModal.svelte` **(scope)** | Add or edit an arena model |
| `src/lib/components/admin/Settings/Evaluations/Model.svelte` **(scope)** | One arena model row with its gear icon |
| `src/lib/components/chat/Messages/RateComment.svelte` **(scope)** | The rating form |
| `src/lib/components/chat/Messages/ResponseMessage.svelte` **(scope, rating parts)** | Thumbs buttons and `feedbackHandler` |
| `src/lib/components/chat/Settings/Usage.svelte` **(scope)** | Personal Usage panel |
| `src/lib/components/chat/SettingsModal.svelte` | Settings window tabs, groups and availability rules (Usage, Evaluations, Analytics) |
| `src/lib/components/chat/Chat.svelte` | Stores the arena reveal on messages; sends the `usage` signal; Continue Response model choice |
| `src/lib/components/chat/Messages.svelte` | `saveMessage`, which writes the rating into the chat |
| `src/lib/components/chat/ModelSelector` | Model selector (no arena-specific code) |
| `src/lib/components/admin/Settings/General.svelte` | **Message Rating** and **Community Sharing** switches |
| `src/lib/components/admin/Settings/Interface.svelte` | **Tags Generation** switch |
| `src/lib/components/admin/Users/Groups/Permissions.svelte` | **Allow Rate Response** permission and its warning |
| `src/lib/components/workspace/common/AccessControl.svelte` | Access editor used for arena models |
| `src/lib/components/common/ConfirmDialog.svelte` | Default confirmation texts |
| `src/lib/components/common/ChatList.svelte` | Chats list in the analytics model window |
| `src/lib/components/common/InterfaceSettings.svelte` | **Accessibility Mode** switch that keeps action buttons visible |
| `src/lib/components/layout/Sidebar/UserMenu.svelte` | Active-user count and **Running** tooltip |
| `src/routes/(app)/admin/+layout.svelte` | Admin-only guard and the Admin Panel bar |
| `src/routes/(app)/admin/settings/[tab]/+page.svelte` | Redirects old admin settings paths into the Settings window |
| `src/routes/(app)/+layout.svelte` | `?settings=` deep link handling |
| `src/routes/+layout.svelte` | Time-zone sync on every app load |
| `src/routes/auth/+page.svelte` | Time-zone sync at sign-in |
| `src/app.css` | `hover-reveal` rule that hides buttons on older answers until hover or focus |

### 13.4 Front End: API Clients, Constants and Text

| File | Role here |
|---|---|
| `src/lib/apis/evaluations/index.ts` **(scope)** | Calls for config, leaderboard, history, feedback list, export and single-row create, read, update, delete |
| `src/lib/apis/analytics/index.ts` **(scope)** | Calls for every analytics route (`getMessages` has no caller) |
| `src/lib/apis/users/index.ts` | `getUserUsage` |
| `src/lib/apis/index.ts` | `getUsage` (`/api/usage`) and `generateTags` |
| `src/lib/apis/chats/index.ts` | `getChatById` (snapshot source) and `getAllTags` (tag suggestions) |
| `src/lib/constants/permissions.ts` | Front-end default for `rate_response` |
| `src/lib/i18n/locales/en-US/translation.json` | English text of the dotted keys quoted here |

### 13.5 Knowledgebase Files

| File | Role here |
|---|---|
| `knowledgebase/tools/ground-truth.md` | Verified facts relied on (roles, settings persistence, user deletion, time zones, no email) |
| `knowledgebase/reference/_areas.md` | This area's scope and focus (area 24), and the planned names of documents not yet written |
| `knowledgebase/reference/users-groups-roles-and-permissions.md` | How permissions, including **Allow Rate Response**, are evaluated and edited (sections 2.1 and 5.12) |
| `knowledgebase/reference/workspace-models-and-model-access.md` | The wider model-access rules that arena access lists follow (section 3.3) |
| `knowledgebase/reference/chat-composer-and-message-display.md` | Side-by-side models and regenerating, which create the comparisons the leaderboard counts (section 5.3) |
| `knowledgebase/reference/chat-conversations-history-and-organisation.md` | The full `chat_message` schema and temporary chats (sections 6.3, 6.4 and 11.1) |
| `knowledgebase/reference/chat-completion-pipeline-and-generation-tasks.md` | The task model and the tags generation task behind rating tags (section 8) |
| `knowledgebase/reference/functions-pipes-filters-actions-and-pipelines.md` | Event functions, which receive feedback and configuration events (section 9.2) |
| `knowledgebase/reference/model-connections-openai-ollama-and-direct.md` | Model connections, the check when the leaderboard says `No models found` (section 10.2) |
| `knowledgebase/reference/authentication-and-sign-in.md` | Session-expiry and sign-in messages that can interrupt rating (section 10.1) |
| `knowledgebase/reference/admin-settings-panels.md` | How the admin **General** settings form saves **Message Rating** (section 5.12); still being written on 2026-10-10, when it held only its At a Glance section |
| `websockets-realtime-and-redis.md` (planned) | Redis and the usage cleanup loop behind the **Running** list (section 10.7); area 41 in `knowledgebase/reference/_areas.md`, not yet written on 2026-10-10 |
| `knowledgebase/tools/inventory.md` | Generated inventory checked for contradictions (section 14.7) |

`knowledgebase/tools/ground-truth.md` is also the source for the `pending` role (section 3.1), permissions adding up across groups (section 3.2), and the fork's `WEBUI_NAME` default and replacement `/favicon.png` (section 12). `CLAUDE.md` at the repository root (local guidance, gitignored) records the absence of a crontab cited in section 8; see the correction there, which also names the `Dockerfile` and `docker-compose.yaml` as places searched for one.

## 14. Open Questions

The repository could not settle any of the items below. Each item gives the section where it is raised; items marked **TO BE CONFIRMED** repeat a point made there. Tier 1 does not answer these questions; it passes them to the person named in each heading. The test environment, the production host and every support contact are themselves **TO BE CONFIRMED** (ground truth, "Environments" and "Contacts That Exist in the Repository").

### 14.1 Live Configuration (Answered by an Admin or the Platform Maintainer)

These values are data, not code (section 7). An admin can read the persistent settings in the Settings window; environment settings live in the deployment's environment, which the platform maintainer can read, and changing one needs a restart (section 7.2).

| Setting or fact | Code default | Why it matters | Who can answer | Where raised |
|---|---|---|---|---|
| `ENABLE_ADMIN_ANALYTICS` (environment) | On | Off removes the **Analytics** tab and the `/api/v1/analytics` routes | Platform maintainer; an admin can see whether the tab exists | 1, 2.2, 7.2, 11.7 |
| **Message Rating** (`ui.enable_message_rating`) | On | Off hides the thumbs buttons from everyone, admins included | An admin (Settings, **General**, **Features**) | 3.2, 5.12, 7.1, 11.1 |
| **Allow Rate Response** (`chat.rate_response`): the saved default and each group's value | On | Decides who can rate; a group cannot take away a permission the default grants | An admin (Users, Groups and the default permissions) | 3.2, 7.1, 11.1 |
| **Arena Models** (`evaluation.arena.enable`) and the configured arena models (`evaluation.arena.models`) | On; no models, so the fallback **Arena Model** is used | Whether arena entries appear in the model picker, and which | An admin (Settings, **Evaluations**) | 3.3, 5.7, 7.1, 11.16 |
| Each arena model's access list, **Include** or **Exclude** mode and model list | No grants (private); empty list (any non-arena model) | Who can pick the arena model, and which hidden models can answer | An admin (the arena model's gear icon) | 3.3, 5.4, 11.16, 11.17 |
| **Community Sharing** (`ui.enable_community_sharing`) | On | On shows the public review link to `openwebui.com` in the rating form (section 14.3) | An admin (Settings, **General**, **Features**) | 7.1, 10.1 |
| **Tags Generation** (`task.tags.enable`) and the task model | On | Without tags the leaderboard topic search has nothing to match; with it on, the conversation up to the rated response is sent for tag suggestions (`src/lib/components/chat/Messages/ResponseMessage.svelte:505`, `:579`) | An admin (Settings, **Interface**) | 5.1, 7.1, 8, 11.6 |
| Event webhooks and Event functions | | Feedback and arena-settings events go to them, with the acting person's name and email | An admin or the platform maintainer | 9.2 |
| Who holds the `admin` role | | Admins read every feedback row, export conversation copies and see names and emails in analytics | An admin (Admin Panel, **Users**) | 3.4, 6.5 |
| `ENABLE_PUBLIC_ACTIVE_USERS_COUNT` (environment) | On | On lets every signed-in user see the active-user count and the ids of models generating right now | Platform maintainer | 3.1, 7.2, 11.19 |
| `ENABLE_ADMIN_CHAT_ACCESS`, `BYPASS_ADMIN_ACCESS_CONTROL`, `BYPASS_MODEL_ACCESS_CONTROL` (environment) | On, on, off | Whether admins can open raters' live chats from feedback and analytics, and who sees arena models | Platform maintainer | 3.1, 3.4, 7.2 |
| `USE_SLIM`, `AUXILIARY_EMBEDDING_MODEL`, and whether the server can download that model | Image build option; `TaylorAI/bge-micro-v2` | Leaderboard topic search depends on them | Platform maintainer | 7.2, 11.6 |

### 14.2 Deployment Facts (Answered by the Platform Maintainer)

| Question | Why it matters | Where raised |
|---|---|---|
| The production host name | Paths in this document are relative to the site root | 2 |
| The server process's time zone | The daily and hourly analytics charts and the feedback history charts cut days and hours in that zone | 7.3, 11.8 |
| The number of workers, and whether Redis is the websocket manager | Without Redis each worker keeps its own **Running** list | 8, 11.19 |
| Which model providers MedIT GPT uses | Needed to reconcile token estimates with provider bills; analytics is not a billing record | 11.9 |
| The live `WEBUI_NAME` | Event payloads and webhook titles use it; the fork's code default is `MedIT GPT` | 12 |
| Whether the uncommitted working-tree changes in `src/lib/components/chat/Messages/ResponseMessage.svelte` and `src/lib/components/chat/Chat.svelte` will be committed and deployed | Line numbers cited from those files are from the working tree | 12 |
| Whether a test environment exists | Section 14.4 needs one | 14.4 |

### 14.3 Privacy and Retention (Answered by the Service Owner and the U of T Privacy Office)

MedIT GPT chats may contain health details, so every item here concerns personal and possibly health information (section 6.5). The service owner is **TO BE CONFIRMED**; privacy questions also go to the U of T Privacy Office (privacy.utoronto.ca).

- **Conversation copies in feedback.** Each rating stores a complete copy of the chat, every branch included, and replaces it on each save (sections 4 and 6.1). The copy stays after the chat or the rater's account is deleted (sections 6.4 and 6.5). The rating form does not mention this (section 5.2 lists every part of the form), and its comment box invites "specific details" (section 10.1). Whether this is acceptable, and whether people should be told about it or warned not to type health details, is **TO BE CONFIRMED**.
- **Who may see feedback and analytics.** Admins see each rater's name and picture, the comment and, in **Feedback Details**, the prompt and response. The API also returns email and role, the **Chat ID** link opens the live chat while `ENABLE_ADMIN_CHAT_ACCESS` is on, and analytics lists names, emails and chat titles (sections 3.4 and 6.5). Who is expected to review feedback, how often and for what purpose (section 1), and whether admins may open raters' live chats and under what policy, are **TO BE CONFIRMED**.
- **Exports.** The JSON export holds every conversation copy, and the CSV holds user ids, comments, reasons and ratings. Once downloaded, both are outside the application's control, and `ENABLE_ADMIN_EXPORT` does not govern them (sections 5.10, 6.5 and 7.2). Who may export feedback, where exports may be stored and shared, and when they must be destroyed are **TO BE CONFIRMED** (sections 6.5 and 11.13).
- **Retention.** No code deletes feedback, its conversation copies or `chat_message` rows by age (section 8). How long feedback should be kept is **TO BE CONFIRMED**, as are whether backups exist and how long deleted feedback survives in them.
- **Deleted accounts.** A deleted person's feedback stays: out of the Feedback list, but in exports and on the leaderboard (sections 5.9, 6.4 and 11.20). Who removes it, and whether off-boarding should include it, is **TO BE CONFIRMED**.
- **Requests to remove a rating.** Deleting a feedback row leaves the rating and comment in the chat record, in later copies of the same chat and in any export already downloaded (sections 5.11 and 6.2). How a removal request should handle those copies, and which privacy route the organisation uses for such requests (section 11.3), are **TO BE CONFIRMED**.
- **Event webhooks.** Feedback events carry the acting person's name and email (section 9.2). Where any configured webhook delivers, and whether that destination is approved for personal data, is **TO BE CONFIRMED**.
- **Audit log.** When the optional audit log records request bodies (`AUDIT_LOG_LEVEL` set to `REQUEST` or `REQUEST_RESPONSE`; code default `NONE`), feedback saves are not among the paths it skips by default, so each entry would hold the first 2,048 bytes of the save by default (`MAX_BODY_LOG_SIZE`), which can include the comment and the start of the conversation copy (`backend/open_webui/env.py:1234-1248`; `backend/open_webui/utils/audit.py:101-113`, `:121`, `:186-194`, `:235-260`, `:275-302`; order of the body's fields in `src/lib/components/chat/Messages/ResponseMessage.svelte:507-530`). The live level is **TO BE CONFIRMED** with the platform maintainer.
- **Upstream community link.** With **Community Sharing** on, the rating form invites people to review the model on `openwebui.com`, with the model id in the address (sections 5.2 and 10.1). Whether MedIT GPT users should be pointed at the upstream community is **TO BE CONFIRMED** (ground truth).
- **Support routes.** The repository names no support contact, privacy route or platform owner for MedIT GPT (ground truth, "Contacts That Exist in the Repository"); who receives the escalations in sections 11.3, 11.13 and 11.20 is **TO BE CONFIRMED**.

### 14.4 Behaviour to Confirm in a Test Environment (Answered by the Platform Maintainer)

Read from the code, not observed. Each needs a test environment (section 14.2) or a log check rather than a look at production data.

- In the slim image, a failure of the main embedding engine during a leaderboard search fails the request and leaves the previous ranking on screen (section 11.6).
- A custom analytics start date is read as midnight UTC, the previous evening in Toronto (sections 7.3 and 11.8).
- The feedback activity charts may label each bar with the previous day for viewers west of UTC (sections 7.3 and 11.8).
- What **Feedback Details** shows for a row without a usable conversation copy (section 11.21). The window reads the stored message list without first checking that it exists (`src/lib/components/admin/Evaluations/FeedbackModal.svelte:75-79`), so the result may be an error rather than an empty window.
- Whether arena models are meant to be combined with other models side by side, and what happens when they are; the model selector has no arena-specific code (section 5.4).
- Log checks: whether any stored arena entry lacks `id`, `name` or `meta`, which would break model listing (section 7.1), and whether `Embedding model load failed: {e}` or `Embedding error: {e}` appears when a topic search has no effect (sections 10.7 and 11.6).
- Also read from code only: rating an answer again after an admin deleted its row creates a new row (section 5.11); the first topic search after a restart is slow while the model loads (section 11.6); with several workers and no Redis, the **Running** tooltip reflects one worker (section 8).

### 14.5 Discrepancies Noticed in the Code (Answered by the Platform Maintainer or Upstream)

None of these contradicts the ground truth (section 14.7). They are product behaviour in v0.11.4 that support should know about and that the maintainer may report upstream.

- The CSV export reads `chat_id` from `data`, where the interface does not put it, so the column is empty for ratings made in MedIT GPT (sections 5.10 and 11.14).
- The **Arena Models** description says `Message rating should be enabled to use this feature`, but the code does not link the two switches (sections 5.7 and 10.3).
- `Thanks for your feedback!` is shown before the server answers, so it also appears when the save fails (sections 5.2 and 10.1).
- Feedback rows are deleted without a confirmation step, while deleting an arena model asks for one (sections 5.7 and 5.11).
- `Redirecting you to Open WebUI Community` belongs to a share function that no button calls (section 10.2).
- Arena answers are counted under the arena model's id in analytics (section 6.3), but under the hidden real model in the feedback's `data.model_id`, its sibling ids and on the leaderboard (sections 5.3 and 6.1; `src/lib/components/chat/Messages/ResponseMessage.svelte:511-517`), so the two views attribute the same answers differently.
- Two windows show a **Tags** list, and they count different things: the leaderboard window lists the five most common feedback tags (`backend/open_webui/routers/evaluations.py:136-160`, `:247`, `:257`; `src/lib/components/admin/Evaluations/LeaderboardModal.svelte:58-59`), while the analytics model window lists the ten most common tags of chats that used the model (`backend/open_webui/routers/analytics.py:406-419`) (sections 5.8 and 5.13).
- The analytics group filter does not apply to the hourly chart (section 5.13).
- On the leaderboard, the number beside **Leaderboard** counts listed models rather than ratings, the model window's chart counts every rating while the table counts only comparisons, and a regenerated answer from the same model counts as a match against itself (sections 5.3, 5.8 and 11.5).
- The Feedback list leaves out ratings by deleted accounts, while exports and the leaderboard still include them (sections 5.9 and 11.20).
- Some routes have no screen: listing or deleting one's own feedback, deleting all feedback, and `/api/v1/analytics/messages` (sections 3.1, 3.4 and 5.11).

### 14.6 Security-Sensitive Items (Referred Without Detail)

- Server-side enforcement of the **Message Rating** switch and the **Allow Rate Response** permission (section 3.2). Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca).
- One question about how an arena model chooses its underlying model relative to each person's own model access (sections 5.4, 11.17 and 11.18). Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca).
- Validation of feedback content supplied by the browser, including the conversation copy, before admins view or export it (section 6.1). Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca).
- Whether admin access to feedback, conversation copies and analytics is logged or reviewed (sections 3.4 and 6.5). Security-sensitive: refer to the platform maintainer and U of T Information Security (security.utoronto.ca).

### 14.7 Consistency With the Ground Truth and Corrections

No contradiction with `CLAUDE.md`, `knowledgebase/tools/ground-truth.md` or `knowledgebase/tools/inventory.md` was found. The ground-truth statement that deleting a user leaves feedback in place is confirmed: the feedback delete methods are called only from `backend/open_webui/routers/evaluations.py` (`:343`, `:387`, `:496-498`) (section 6.4). The roles, permissions, time-zone, admin-visibility and settings-persistence facts the document relies on match the ground truth.

Corrections made while completing this document:

| Date | Section | Correction |
|---|---|---|
| 2026-10-10 | 8, opening sentence | Cited the ground truth for "there is no crontab", but `knowledgebase/tools/ground-truth.md` does not say so. The statement is in `CLAUDE.md`, and a search of `backend/`, `scripts/`, the `Dockerfile` and `docker-compose.yaml` found no crontab. The fact stands; only its source was corrected |
