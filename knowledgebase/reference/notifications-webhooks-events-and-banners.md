# Notifications, Webhooks, Events and Banners

## At a Glance

- **MedIT GPT sends no email.** Every notice is an in-app toast, a browser notification, a banner,
  the admin update toast or What's New window, or an HTTP post to a webhook address that an
  administrator or a user typed in (sections 1 and 9.1).
- **181 named events** (`backend/open_webui/events.py`) are published by the server. Each goes to
  Event functions and to **admin event webhooks** (Admin › Settings › General › Events), filtered by
  event name or `prefix.*` pattern and by a "send events for" scope (sections 5.1, 5.2, 9.2).
- **Personal notification targets** (Settings › Notifications) receive only five events: chat
  finished, chat failed, channel message, calendar alert and file processing failed. They need
  **User Webhooks** switched on by an administrator **and** the **User Webhooks** permission; both
  are off by default (sections 3, 5.5, 5.6).
- **"Only when away"** means no request and no open-tab heartbeat for three minutes, so it rarely
  fires while MedIT GPT is open in any tab. `chat.failed` is published only for non-streaming
  replies, sometimes for answers that actually succeeded (sections 4, 5.9, 11.1, 11.6).
- Formats are chosen from the address: Slack and Google Chat text, Discord text, Microsoft Teams
  connector cards, otherwise the full JSON envelope. Delivery is one attempt, with no retry, no
  delivery history and, by default, no time limit; failures appear only in the server log
  (sections 8.1, 9.3, 10.9).
- **Privacy:** generic JSON and Teams payloads carry names and emails; with all events selected
  they also carry message previews and reply text. Treat every webhook as a disclosure of personal
  data (section 9.6).
- **Banners** appear only on the new-chat screen, load when the app loads, and **Remember
  Dismissal** hides them per browser. The **update toast** and **What's New** report **upstream
  Open WebUI** releases and notes, not MedIT GPT releases (sections 5.13, 5.14, 12).
- Fork changes here are branding only: the test notification and browser-notification titles use
  the app name (section 12).

## 1. Purpose and Who Uses It

**MedIT GPT sends no email.** There is no SMTP or mail-sending code anywhere in
`backend/open_webui` (a search for `smtplib`, `aiosmtplib`, `sendmail`, `SMTP`, `email.mime`,
`sendgrid`, `mailgun` and `postmark` finds nothing), and no mail library is declared in the
project dependencies. The verified fact is also recorded in `knowledgebase/tools/ground-truth.md`
("The application sends no email"). Nothing in MedIT GPT can email a user that a chat finished, a
file failed or an account was created. Every notice described below is either shown inside the web
page, shown by the browser, or posted as an HTTP request to a web address that an administrator or
the user typed in.

This area covers how MedIT GPT tells **people** and **other systems** that something happened:

| Channel | Who receives it | What it is for | Source |
|---|---|---|---|
| In-app toast (small card in the corner) | The signed-in user, in the browser tab | A reply finished in a chat you are not looking at, a channel message arrived, a calendar event is about to start; tools and functions can also raise short toasts inside an open chat | `src/routes/+layout.svelte:600-632`, `:735-781`, `:865-893`; `src/lib/components/NotificationToast.svelte`; `src/lib/components/chat/Chat.svelte:1354-1366` |
| Browser (desktop) notification | The signed-in user, through the operating system | The same three triggers, when the user switched on **Browser Notifications** and the browser granted permission | `src/routes/+layout.svelte:620-630`, `:758-768`, `:868-878`; `src/lib/components/chat/Settings/Notifications.svelte:60-78` |
| Notification sound | The signed-in user | A short sound when a toast appears | `src/lib/components/NotificationToast.svelte:68-84` |
| Banners | Every signed-in user, on the new-chat screen | Announcements written by an administrator (for example planned maintenance) | `src/lib/components/chat/Navbar.svelte:270-323`; `src/lib/components/common/Banner.svelte` |
| Update-available toast | Administrators only | A newer **upstream Open WebUI** release exists on GitHub | `src/routes/(app)/+layout.svelte:369-382`, `:428-438`; `src/lib/components/layout/UpdateInfoToast.svelte` |
| "What's New" (changelog) modal | Administrators automatically after an upgrade; anyone from **About** | Release notes, taken from the upstream Open WebUI `CHANGELOG.md` | `src/routes/(app)/+layout.svelte:355-357`; `src/lib/components/ChangelogModal.svelte` |
| Admin event webhooks | An outside system chosen by an administrator (Slack, Discord, Microsoft Teams, Google Chat or any JSON receiver) | An instance-wide feed of named events (181 in the catalogue: sign-ins, chats, files, settings changes and more) | `backend/open_webui/events.py:1034-1071`; `backend/open_webui/utils/webhook.py`; `src/lib/components/admin/Settings/Events.svelte` |
| Personal notification targets (user webhooks) | An outside address chosen by the user | Five personal events: chat finished, chat failed, channel message, calendar alert, file processing failed; also the model's `notify` tool | `backend/open_webui/utils/notifications.py`; `backend/open_webui/routers/notifications.py`; `src/lib/components/chat/Settings/Notifications.svelte` |
| Event functions | Python code an administrator installed under Functions | Custom reactions to any event (for example writing an audit record) | `backend/open_webui/events.py:1103-1168`; see `functions-pipes-filters-actions-and-pipelines.md` |

Who uses this document:

- **Tier-1 support**, to explain why a notification, banner or webhook message did or did not
  arrive, and what personal data left the platform when it did.
- **Administrators**, who configure admin webhooks, the **User Webhooks** switch, the **User
  Webhooks** permission, banners and the **WebUI URL** used in links.
- **Users**, who switch browser notifications and sound on or off and, when allowed, set up their
  own notification targets.

All notices inside the page depend on the browser being connected to the server's live socket
(`src/routes/+layout.svelte:1224-1225`). The webhook deliveries do not: they are sent by the
server whether or not anyone has MedIT GPT open (`backend/open_webui/events.py:1062-1071`,
`:1074-1086`).

## 2. Navigation and URLs

The production host name is **TO BE CONFIRMED**; paths are relative to the site root. Settings
screens open in the **Settings** window over the chat page; the `?settings=` deep links open the
window on a given tab (`src/routes/(app)/+layout.svelte:166-195`).

### 2.1 Screens

| Screen or place | Path or how to reach it | Who | What is there | Source |
|---|---|---|---|---|
| **Settings › Notifications** | Profile menu › **Settings** › **Notifications**; deep link `/?settings=notifications` | Every signed-in user (the tab is always listed) | **Browser Notifications** switch, **Notification Sound** switch, and, when allowed, **Notification Targets** | `src/lib/components/chat/SettingsModal.svelte:199-204`, `:379-405`, `:807-808`; `src/lib/components/chat/Settings/Notifications.svelte:191-342` |
| **Settings › Interface** (two admin-only rows) | `/?settings=interface` | Administrators see the rows | **Toast Notifications for New Updates** and `Show "What's New" Modal on Login` | `src/lib/components/common/InterfaceSettings.svelte:715-761` |
| **Settings › About** | `/?settings=about` | Every signed-in user | **MedIT GPT Version** section (the heading is the app name plus "Version"): installed version, update check, **See what's new**, **Check for updates** | `src/lib/components/chat/Settings/About.svelte:52-110` |
| **Admin › Settings › General** | `/admin/settings/general`, which forwards to `/?settings=admin:general` | Administrators | Top block: **Version**, **See what's new**, **Check for updates**; **Features** section: **User Webhooks** switch and **WebUI URL**; **Events** block: **Webhooks** list; **UI** section: **Banners** | `src/routes/(app)/admin/settings/[tab]/+page.svelte:6-10`; `src/lib/components/admin/Settings/General.svelte:133-185`, `:274-418`, `:483-520` |
| **Admin › Users › Groups** (Default permissions or a group) | `/admin/users/groups` | Administrators | **Features Permissions** › **User Webhooks** switch (permission `features.webhooks`) | `src/lib/components/admin/Users/Groups/Permissions.svelte:960`, `:1153-1167`; `src/lib/components/admin/Users/Groups.svelte:114-118` |
| Banner strip | The new-chat screen (no chat open), under the top bar | Every signed-in user | Admin banners, plus licence banners when licence metadata requires them | `src/lib/components/chat/Navbar.svelte:270-323` |
| Toast click destinations | Clicking a toast | The user | Chat toast opens `/c/{chat_id}`; channel toast opens `/channels/{channel_id}` (with `?thread={parent_id}` for a thread reply); calendar toast opens `/calendar` | `src/routes/+layout.svelte:610-612`, `:772-774`, `:882-885` |
| Update toast link | **Update for the latest features and improvements.** | Administrators | Opens the upstream release list on GitHub (`github.com/open-webui/open-webui/releases`) in a new tab | `src/lib/components/layout/UpdateInfoToast.svelte:24-26` |
| Version link | The "(v… available!)" or "(latest)" text beside the version | Administrators (General) and every user (About) | Opens the upstream GitHub release page for the latest version | `src/lib/components/admin/Settings/General.svelte:148-158`; `src/lib/components/chat/Settings/About.svelte:75-84` |

### 2.2 Server Endpoints

These are the routes the screens above call. Tier 1 does not call them directly; they are listed
so that log lines and browser developer-tool entries can be matched to a screen.

| Method and path | Who may call it | Purpose | Source |
|---|---|---|---|
| `GET /api/events` | Administrators | The event catalogue: every event name with its description and short message, plus a `schema` value equal to the version | `backend/open_webui/main.py:2491-2496`; `backend/open_webui/events.py:678-686` |
| `GET /api/events/webhooks` | Administrators | List admin event webhooks (full addresses included) | `backend/open_webui/main.py:2499-2501` |
| `POST /api/events/webhooks` | Administrators | Create an admin event webhook | `backend/open_webui/main.py:2504-2532` |
| `PUT /api/events/webhooks/{webhook_id}` | Administrators | Change one (also used by the on/off switch) | `backend/open_webui/main.py:2535-2566` |
| `DELETE /api/events/webhooks/{webhook_id}` | Administrators | Delete one | `backend/open_webui/main.py:2569-2583` |
| `GET /api/v1/notifications/events` | Signed-in users allowed to use notification targets | The five events a personal target can receive | `backend/open_webui/routers/notifications.py:44-47`; `backend/open_webui/utils/notifications.py:223-231` |
| `GET /api/v1/notifications/targets` | As above | The user's own targets, with the address masked | `backend/open_webui/routers/notifications.py:50-53`; `backend/open_webui/utils/notifications.py:81-94`, `:152-157` |
| `POST /api/v1/notifications/targets` | As above | Add a target | `backend/open_webui/routers/notifications.py:56-62` |
| `PUT /api/v1/notifications/targets/{target_id}` | As above | Change a target (also the on/off switch) | `backend/open_webui/routers/notifications.py:65-73` |
| `DELETE /api/v1/notifications/targets/{target_id}` | As above | Remove a target | `backend/open_webui/routers/notifications.py:76-81` |
| `PUT /api/v1/notifications/targets/{target_id}/default` | As above | **Make Default** | `backend/open_webui/routers/notifications.py:84-90` |
| `POST /api/v1/notifications/targets/{target_id}/test` | As above | **Send Test** | `backend/open_webui/routers/notifications.py:93-103` |
| `GET /api/v1/configs/banners` | Signed-in users (`user` or `admin`) | Read the banners | `backend/open_webui/routers/configs.py:872-877` |
| `POST /api/v1/configs/banners` | Administrators | Replace the whole banner list | `backend/open_webui/routers/configs.py:852-869` |
| `GET /api/version/updates` | Signed-in users (`user` or `admin`) | Ask GitHub for the latest upstream release | `backend/open_webui/main.py:2594-2613` |
| `GET /api/changelog` | Called by the What's New window | The five newest entries of the bundled `CHANGELOG.md` | `backend/open_webui/main.py:2616-2618`; `backend/open_webui/env.py:184-222` |

The mounting prefix `/api/v1/notifications` is set in `backend/open_webui/main.py:866`. The
front-end callers are `src/lib/apis/notifications/index.ts:53-81` (personal targets) and
`src/lib/apis/index.ts:1624-1768` (event catalogue and admin webhooks).

### 2.3 Live Socket Channels Used for In-App Notices

| Socket event | Carries | Handled in | Source |
|---|---|---|---|
| `events` | Chat progress for every chat of the user, including `chat:completion` (reply finished), `calendar:alert`, and `notification` items raised by tools and functions | `src/routes/+layout.svelte:561-788` (toasts and browser notifications for other chats); `src/lib/components/chat/Chat.svelte:1203-1206`, `:1354-1366` (the open chat) | `src/routes/+layout.svelte:1224`; `backend/open_webui/socket/main.py:1139-1161`; `backend/open_webui/utils/automations.py:576-585` |
| `events:channel` | Channel activity, including new messages | `src/routes/+layout.svelte:790-895` | `src/routes/+layout.svelte:1225` |

## 3. Roles and Permissions

Roles are `admin`, `user` and `pending` (see `knowledgebase/tools/ground-truth.md`). A `pending`
account sees none of this area: the app stops loading before banners and settings are fetched
(`src/routes/(app)/+layout.svelte:218-220`), and the notification, webhook and banner endpoints
require a verified (`user` or `admin`) or admin session (`backend/open_webui/utils/auth.py:567-576`,
`:625-631`).

| Action | `admin` | `user` | Condition | Source |
|---|---|---|---|---|
| See the event catalogue; create, change, switch off or delete admin event webhooks | Yes | No | Admin session | `backend/open_webui/main.py:2491-2583` |
| Turn **User Webhooks** on or off for the whole instance (`ui.enable_user_webhooks`) | Yes | No | Admin › Settings › General › Features | `src/lib/components/admin/Settings/General.svelte:379-385`; `backend/open_webui/routers/auths.py:131` |
| Grant the **User Webhooks** permission (`features.webhooks`) | Yes | No | Default permissions or a group | `src/lib/components/admin/Users/Groups/Permissions.svelte:1153-1167` |
| Use **Notification Targets** (list, add, edit, test, make default, remove) | Yes, when **User Webhooks** is on | Yes, when **User Webhooks** is on **and** the user has `features.webhooks` | When **User Webhooks** is off the server answers 404 to everyone, admins included; a user without the permission gets 403 | `backend/open_webui/routers/notifications.py:34-41`; `src/lib/utils/settings-access.ts:16-18` |
| Have personal events delivered automatically | Yes | Yes | **User Webhooks** on at send time, plus an enabled target that lists the event (the permission is checked when the target is saved, not at send time) | `backend/open_webui/utils/notifications.py:393-417`; `backend/open_webui/routers/users.py:532-547` |
| Let the model call the `notify` tool | Yes | Yes | **User Webhooks** on, the person holds `features.webhooks` (admins always pass), and the model's **Notifications** built-in tool group is not switched off | `backend/open_webui/utils/tools.py:536-540`, `:759-764`; see `builtin-native-tools.md` |
| Switch **Browser Notifications** and **Notification Sound** | Yes | Yes | Browser notifications also need the browser's permission | `src/lib/components/chat/Settings/Notifications.svelte:60-78`, `:212-223` |
| Create, edit, reorder and delete banners | Yes | No | Admin session; saved with the General tab's **Save** | `backend/open_webui/routers/configs.py:852-869`; `src/lib/components/admin/Settings/General.svelte:80-106` |
| See banners | Yes | Yes | On the new-chat screen | `backend/open_webui/routers/configs.py:872-877`; `src/lib/components/chat/Navbar.svelte:271` |
| See the update-available toast | Yes | No | Version check on, toast not dismissed in the last 24 hours, **Toast Notifications for New Updates** on | `src/routes/(app)/+layout.svelte:369-382`, `:428`; `src/lib/components/common/InterfaceSettings.svelte:715-737` |
| Have the What's New window open by itself after an upgrade | Yes | No | `Show "What's New" Modal on Login` on (default) and the stored version differs from the running one | `src/routes/(app)/+layout.svelte:355-357` |
| Open What's New by hand and see the update check in **About** | Yes | Yes | The update check text appears only when the version check is on | `src/lib/components/chat/Settings/About.svelte:64-108` |
| Install or change Event functions | Yes | No | Functions are admin-only (see `functions-pipes-filters-actions-and-pipelines.md`) | `backend/open_webui/events.py:1103-1156` |

Points that often surprise people:

- **User Webhooks is off by default twice over.** The instance switch defaults to off
  (`ENABLE_USER_WEBHOOKS`, `backend/open_webui/config.py:2100`) and so does the default permission
  (`USER_PERMISSIONS_FEATURES_USER_WEBHOOKS`, `backend/open_webui/config.py:1932-1934`, `:2015`).
  Both must be on before an ordinary user sees **Notification Targets**. The live values are data,
  **TO BE CONFIRMED** for production.
- **Removing the permission later does not stop deliveries.** Automatic delivery checks only the
  instance switch and the user's saved targets (`backend/open_webui/utils/notifications.py:393-417`);
  the permission is enforced on the screens and when settings are saved
  (`backend/open_webui/routers/notifications.py:38-41`; `backend/open_webui/routers/users.py:532-547`).
  A user who saved a target while permitted keeps receiving notifications after the permission is
  withdrawn, until the target is removed or **User Webhooks** is switched off. This is read from
  the code; see section 14.
- **Group permissions only add.** As everywhere in MedIT GPT, a group can grant
  `features.webhooks` but cannot take it away when Default permissions grant it
  (`src/lib/components/admin/Users/Groups/Permissions.svelte:1160-1166`; ground truth).

## 4. Key Concepts and Terminology

| Term | Meaning in MedIT GPT | Source |
|---|---|---|
| **Event** | A named record that something happened on the server, such as `chat.finished` or `user.role_updated`. The name is `resource.operation`; the part before the last dot is the *resource*, the last part the *operation* | `backend/open_webui/events.py:995-1031` |
| **Event catalogue** (`EVENTS`) | The fixed list of 181 event names, each with a description and a short message, defined in one class. Publishing a name that is not in the catalogue raises an error | `backend/open_webui/events.py:42-675`, `:988-992` |
| **Publishing** | `publish_event(...)` builds the event and hands it to four *sinks* in turn; a failing sink is logged and the others still run | `backend/open_webui/events.py:1171-1202` |
| **Sinks** | (1) socket sessions: disconnects the person's live socket connections when their account is deleted or their role changes, so open tabs reconnect with fresh permissions (this is not a sign-out); (2) Event functions; (3) admin event webhooks; (4) personal notification targets (five events only). Sinks 2 to 4 start background tasks, so the user's request does not wait for delivery | `backend/open_webui/events.py:1062-1171`; `backend/open_webui/socket/main.py:388-401` |
| **Event envelope** | The JSON object every admin webhook (generic format) and Event function receives: `schema`, `id`, `event`, `resource`, `operation`, `created_at`, `instance_id`, `version`, `source`, `actor`, `subject`, `data`, `message` | `backend/open_webui/events.py:925-944`, `:1017-1031` |
| `schema` and `version` | Both set to the running version (0.11.4), not to a separate schema number | `backend/open_webui/events.py:1018`, `:1025`; `backend/open_webui/main.py:2494` |
| `created_at` | Seconds since 1 January 1970 (UTC) when the event was built | `backend/open_webui/events.py:1023` |
| `instance_id` | The `INSTANCE_ID` environment variable, or a random value generated when the server process starts; empty for events published before startup assigns it | `backend/open_webui/env.py:155`; `backend/open_webui/main.py:360`, `:531`; `backend/open_webui/events.py:1010` |
| `source` | Where the event came from: `api` (default), `system` (start-up and shut-down), `scheduler` (calendar alerts), `oauth`, `ldap`, `trusted_header`, `scim`, `admin`, `channel_webhook` | `backend/open_webui/events.py:1002`; call sites listed in section 9.2 |
| **Actor** | The account that caused the event: its `id`, `name`, `email`, `role`, `created_at` and `updated_at`, plus `type` (`user`). Missing for start-up and shut-down, calendar alerts, channel messages, two of the four failed-automation-run call sites, every SCIM event and groups created during single sign-on (section 9.2) | `backend/open_webui/events.py:704`, `:974-985` |
| **Subject** | What the event is about: `{type, id}`, for example a chat id or a user id | `backend/open_webui/events.py:1011-1015` |
| **Sanitizing** | Before an event leaves, fields whose names look like credentials (`password`, `token`, `secret`, `api_key`, `key`, `authorization`, `cookie` and names ending in `_token`, `_secret`, `_key`) are dropped at every depth, and any text longer than 1,000 characters is cut to 1,000 characters followed by `...` | `backend/open_webui/events.py:19`, `:689-702`, `:947-971` |
| **Admin event webhook** | An address an administrator registered under Admin › Settings › General › Events › Webhooks. Each has a name, an address, an on/off switch, event filters and a "send events for" scope. Stored as a list in the setting `events.webhooks` | `backend/open_webui/events.py:20`, `:707-736`, `:838-851` |
| **Default webhook** | The admin webhook with the id `default`, created from the legacy `webhook_url` setting; listed first and labelled **Default webhook** | `backend/open_webui/events.py:22`, `:854-878`; `src/lib/components/admin/Settings/Events.svelte:65-74`, `:726` |
| **Event filter** | Which events an admin webhook takes: `*` (all), an exact name, or a prefix pattern such as `user.*` (every event whose name starts with `user.`). Names and prefixes are checked against the catalogue when saved | `backend/open_webui/events.py:712-723`, `:766-777` |
| **Send events for** (scope) | **All users and system events** (no scope stored), **System events only** (an empty list: only events with no associated user) or **Specific users or groups** (a list of user and group ids) | `src/lib/components/admin/Settings/Events.svelte:239-251`, `:456-477`; `backend/open_webui/events.py:802-828` |
| **Associated user** | For scope matching, an event is associated with: the actor, the subject when the subject is a user, `data.user_id`, and every id in `data.user_ids`. Group scopes match current members of the group at send time | `backend/open_webui/events.py:780-799`, `:822-828` |
| **Notification target** (personal webhook) | An address a user registered under Settings › Notifications. Type is always `webhook`; it has an id (the **Target ID**), an on/off switch, a list of events and a delivery mode. Stored in the user's own settings record | `backend/open_webui/utils/notifications.py:29-78`; `src/lib/apis/notifications/index.ts:3-16` |
| **Notification-capable events** | The only five events a personal target can receive: `chat.finished`, `chat.failed`, `channel.message`, `calendar.alert`, `retrieval.content.process_failed` | `backend/open_webui/events.py:669-675`; `backend/open_webui/utils/notifications.py:16` |
| **Default target** | The target the `notify` tool uses when the model names none. The first target created becomes the default; **Make Default** changes it | `backend/open_webui/utils/notifications.py:175`, `:213-220`, `:234-243` |
| **Delivery mode** | **Only when away** (`away`, the default) or **Always** (`always`) | `backend/open_webui/utils/notifications.py:18`, `:65-67`; `src/lib/components/chat/Settings/Notifications.svelte:396-413` |
| **Away** | The user has made no signed-in request and sent no live-socket heartbeat for three minutes. An open MedIT GPT tab sends a heartbeat every 30 seconds by default, whether or not the tab is visible, so the user counts as present | `backend/open_webui/models/users.py:918-925`; `backend/open_webui/socket/main.py:489-494`; `backend/open_webui/utils/auth.py:481-483`; `src/routes/+layout.svelte:217-225` |
| **Legacy admin webhook URL** (`webhook_url`) | The single admin webhook address of earlier releases (environment variable `WEBHOOK_URL`). At start-up it is copied into the webhook list as the **Default webhook** | `backend/open_webui/config.py:2080`, `:3122`; `backend/open_webui/events.py:854-878`; `backend/open_webui/main.py:369` |
| **Legacy personal webhook URL** | The single personal address of earlier releases, kept in the user's settings. The first time the user's targets are read it becomes a target with id `webhook` | `backend/open_webui/utils/notifications.py:97-149` |
| **Format detection** | The server shapes the message by the address: Slack and Google Chat get a `text` message, Discord a `content` message, Microsoft Teams a "MessageCard"; anything else gets raw JSON | `backend/open_webui/utils/webhook.py:42-84` |
| **WebUI URL** (`webui.url`) | The public address admins enter in Admin › Settings › General; used to build the links in chat and channel notifications. When empty, links are relative paths such as `/c/{chat_id}` | `backend/open_webui/utils/middleware.py:214`, `:227`; `backend/open_webui/routers/channels.py:942`, `:949`; `src/lib/i18n/locales/en-US/translation.json:2413-2414` |
| **Toast** | A small card in the corner of the page (the `svelte-sonner` library); MedIT GPT's own notification card is `NotificationToast` | `src/lib/components/NotificationToast.svelte`; `src/routes/+layout.svelte:608-618` |
| **Browser notification** | An operating-system notification created with the browser's `Notification` feature, titled "{title} / MedIT GPT" (the app name) | `src/routes/+layout.svelte:622`, `:760`, `:873` |
| **Last active tab** | When several MedIT GPT tabs are open in one browser, the most recently shown tab; only that tab creates browser notifications and plays the toast sound | `src/routes/+layout.svelte:109`, `:1161-1180`; `src/lib/stores/index.ts:169`; `src/lib/components/NotificationToast.svelte:73-74` |
| **Banner** | An administrator-written announcement with a type (**Info**, **Warning**, **Error**, **Success**), Markdown content, optional per-language versions and a **Remember Dismissal** switch. Stored in the setting `ui.banners` | `backend/open_webui/config.py:2150-2167`, `:3126`; `src/lib/components/admin/Settings/Interface/Banners.svelte` |
| **Remember Dismissal** | When on, closing a banner hides it in that browser until browser storage is cleared; when off, closing hides it only until the page is reloaded | `src/lib/components/chat/Navbar.svelte:300-318` |
| **Update toast** | The admin-only card saying a newer upstream version exists | `src/lib/components/layout/UpdateInfoToast.svelte` |
| **What's New** | The release-notes window (changelog modal) | `src/lib/components/ChangelogModal.svelte` |
| **Event function** | An admin-installed function whose type is `event`; its `event` method is called for every published event | `backend/open_webui/events.py:1103-1156` |

## 5. Workflows (Step by Step)

### 5.1 Admin: Add an Admin Event Webhook

1. Go to **Admin › Settings › General** (`/admin/settings/general`) and scroll to the **Events**
   block (between the **Features** and **UI** sections). Under **Webhooks** the description reads
   "Send product events as JSON to external services. Chat destinations receive readable
   messages." (`src/lib/components/admin/Settings/General.svelte:418`;
   `src/lib/components/admin/Settings/Events.svelte:692-716`;
   `src/lib/i18n/locales/en-US/translation.json:2380-2382`).
2. Select the **+** button (tooltip **Add webhook**). The **Add webhook** window opens
   (`src/lib/components/admin/Settings/Events.svelte:396-400`, `:707-715`).
3. Fill in:
   - **Name** (optional; placeholder "Identity audit"). Left empty, it is saved as `Webhook`
     (`src/lib/components/admin/Settings/Events.svelte:417-427`, `:339-340`).
   - **URL** (required; placeholder `https://example.com/events`) and the on/off switch beside it
     (`src/lib/components/admin/Settings/Events.svelte:431-451`).
   - **Send events for**: **All users and system events**, **System events only** or **Specific
     users or groups** (section 5.2) (`src/lib/components/admin/Settings/Events.svelte:453-477`).
   - **Events**: **All events** is ticked by default. Untick it to pick events from the list
     (each shown with its short message) or type a pattern such as `user.*` and press **Add** or
     Enter (`src/lib/components/admin/Settings/Events.svelte:565-653`).
4. Select **Save**. The server checks the address (it must be a public `http` or `https` address
   that resolves) and every event name or pattern, stores the webhook in the `events.webhooks`
   setting and answers. The window closes and **Webhook saved** appears
   (`backend/open_webui/main.py:2504-2532`; `backend/open_webui/events.py:881-908`;
   `src/lib/components/admin/Settings/Events.svelte:338-359`).
5. The list shows the webhook as "{name} - {host} - {events summary} - {scope summary}", for
   example "Webhook - hooks.example.com - All events - All users and system events". Only the
   host part of the address is shown in the list; the full address is visible in the edit window
   (`src/lib/components/admin/Settings/Events.svelte:180-186`, `:719-731`, `:120-126`).
6. Saving publishes a `config.webhook.updated` event, which is itself delivered to every webhook
   whose filters and scope match, including the one just saved. That is the closest thing to a
   test: there is **no Test button for admin webhooks**
   (`backend/open_webui/main.py:2519-2531`; `src/lib/components/admin/Settings/Events.svelte`).

If the save fails, the toast reads **Failed to save webhook**, whatever the server's reason (a
rejected address, an unknown event name). The admin screen does not show the server's message
because its request helper hands back the whole error object rather than its text
(`src/lib/apis/index.ts:1694-1702`; `src/lib/components/admin/Settings/Events.svelte:356-358`).

### 5.2 Admin: Choose Which Events and Which People

**Event filters** (`backend/open_webui/events.py:712-723`, `:766-777`):

| Filter | Matches | Example |
|---|---|---|
| `*` (**All events**) | Every event in the catalogue | — |
| Exact name | Only that event | `chat.finished` |
| `prefix.*` | Every event whose name starts with `prefix.` | `user.*` matches `user.created`, `user.role_updated` and the rest; `knowledge.*` also matches `knowledge.file.added` |

A pattern whose prefix matches no catalogue event, or an exact name not in the catalogue, is
refused. The screen warns first: "Use a valid event name or pattern like user.*"
(`src/lib/components/admin/Settings/Events.svelte:209-237`). The screen also notes that names may
change between upstream releases: "Event names may change as Open WebUI evolves. Use broad patterns
like user.* for integrations that should continue across new related events."
(`src/lib/components/admin/Settings/Events.svelte:644-651`). Removing the last filter puts **All
events** back (`src/lib/components/admin/Settings/Events.svelte:202-207`).

**Send events for** (scope) (`src/lib/components/admin/Settings/Events.svelte:239-251`,
`:465-477`; `backend/open_webui/events.py:780-828`):

| Choice | Stored as | Receives | On-screen explanation |
|---|---|---|---|
| **All users and system events** | no scope (`null`) | Every matching event | "Receives matching events across the instance, including system/config events and events associated with any user." |
| **System events only** | an empty list | Only matching events with **no** associated user (no actor, no user subject, no `user_id` or `user_ids` in the data) | "Receives matching events that are not associated with a user." |
| **Specific users or groups** | a list of user and group ids | Matching events whose actor, user subject, `data.user_id` or `data.user_ids` is one of the chosen users or a current member of a chosen group | "Receives matching user-associated events only when the actor, user subject, or user data matches these users or current group members. System/config events are not sent." |

In practice **System events only** receives very little: the four start-up and shut-down events,
some failed automation runs (those recorded without a user), group changes made through SCIM
provisioning and groups created during single sign-on (section 9.2). SCIM *user* events do not
qualify: the user is their subject, so they count as user-associated
(`backend/open_webui/events.py:1011-1015`, `:789-790`; `backend/open_webui/routers/scim.py:646`,
`:991`; `backend/open_webui/utils/automations.py:358`, `:526`). A settings change
made by an administrator in the interface carries that administrator as the actor, so it counts as
user-associated and is **not** sent to a **System events only** webhook
(`backend/open_webui/events.py:780-799`, `:809-810`; for example
`backend/open_webui/routers/configs.py:861-868`). The people picker searches users by name and
groups by name, five results each (`src/lib/components/admin/Settings/Events.svelte:278-297`).

### 5.3 Admin: Switch Off, Edit or Delete a Webhook

- **Switch off**: the switch on the webhook's row saves at once. If the server refuses, the switch
  flips back and **Failed to update webhook** appears
  (`src/lib/components/admin/Settings/Events.svelte:376-388`, `:745-752`). A switched-off webhook
  receives nothing and is shown faded (`backend/open_webui/events.py:767-768`;
  `src/lib/components/admin/Settings/Events.svelte:722`).
- **Edit**: the gear button (tooltip **Configure**) opens **Edit webhook** with the stored values,
  including the full address; **Save** replaces them and shows **Webhook saved**
  (`src/lib/components/admin/Settings/Events.svelte:117-142`, `:735-743`).
- **Delete**: in **Edit webhook**, **Delete**, then confirm "Are you sure you want to delete this
  webhook? This action cannot be undone." The toast **Webhook deleted** follows. Deleting the
  **Default webhook** also empties the legacy `webhook_url` setting, so it is not re-created at
  the next start-up (`src/lib/components/admin/Settings/Events.svelte:361-374`, `:656-669`,
  `:683-690`; `backend/open_webui/events.py:911-922`).

Each of these changes publishes `config.webhook.updated` with `action` set to `created`,
`updated` or `deleted` (`backend/open_webui/main.py:2519-2582`).

### 5.4 Start-Up: Legacy Webhook Migration

Earlier releases had a single admin webhook address (setting `webhook_url`, environment variable
`WEBHOOK_URL`). At every start-up, after the settings are loaded, the server runs the migration
(`backend/open_webui/main.py:361-370`; `backend/open_webui/events.py:854-878`):

1. If the webhook list already has an entry with id `default`, nothing happens.
2. Otherwise, if `webhook_url` holds an address, a **Default webhook** is added at the top of the
   list with that address, switched on, **All events** and **All users and system events**.
3. If `webhook_url` is empty, nothing happens.

So a deployment that set `WEBHOOK_URL` sends **every event** to that address from v0.11.4 on,
including message previews and reply text (section 9.6). An unused sign-up message,
`New user signed up: {username}`, survives in `backend/open_webui/constants.py:32-34` from the
older single-webhook design; what earlier releases sent is not recorded in this branch's code.
Whether production has a legacy address is data, **TO BE CONFIRMED**.

### 5.5 Admin: Allow Users to Have Their Own Webhooks

1. **Admin › Settings › General › Features › User Webhooks**: switch on ("Allow users to configure
   webhooks from their account.") and select **Save** at the bottom of the tab
   (`src/lib/components/admin/Settings/General.svelte:379-385`;
   `src/lib/i18n/locales/en-US/translation.json:2410-2411`). This sets `ui.enable_user_webhooks`
   (`backend/open_webui/routers/auths.py:131`).
2. **Admin › Users › Groups**: switch on **User Webhooks** under **Features Permissions** in
   **Default permissions** (everyone) or in a group (its members)
   (`src/lib/components/admin/Users/Groups/Permissions.svelte:960`, `:1153-1167`).
3. Optionally fill in **WebUI URL** in the same **Features** section ("Enter the public URL of your
   WebUI. This URL will be used to generate links in the notifications.") so notification links
   are complete addresses (`src/lib/components/admin/Settings/General.svelte:405-415`;
   `src/lib/i18n/locales/en-US/translation.json:2413-2414`).

Administrators need only step 1: they skip the permission check
(`backend/open_webui/routers/notifications.py:38`; `src/lib/utils/settings-access.ts:16-18`).

### 5.6 User: Add a Personal Notification Target

Available only when section 5.5 is done; otherwise the **Notification Targets** heading is not
shown at all (`src/lib/components/chat/Settings/Notifications.svelte:54-58`, `:225`).

1. Open **Settings › Notifications** (`/?settings=notifications`). Under **Notification
   Targets**, select **+** (**Add Notification Target**)
   (`src/lib/components/chat/Settings/Notifications.svelte:225-239`;
   `src/lib/i18n/locales/en-US/translation.json:2995`, `:2998`).
2. In the window:
   - **Target ID for notify** (placeholder "Target ID"): the name the model's `notify` tool can
     use. Left empty, the server uses the address's host name with dots turned into dashes (for
     example `hooks-example-com`), adding `-2`, `-3` if that id is taken. Ids are lower-case and
     keep only letters, digits, `-` and `_`
     (`src/lib/components/chat/Settings/Notifications.svelte:352-361`;
     `backend/open_webui/utils/notifications.py:47-50`, `:160-172`).
   - **Webhook**: the address (placeholder `https://hooks.slack.com/services/...`). **Save**
     stays greyed out until an address is typed
     (`src/lib/components/chat/Settings/Notifications.svelte:363-375`, `:433`).
   - **Automatic Events**: pick any of the five events, shown with the server's labels **Chat
     finished**, **Chat failed**, **Channel message**, **Calendar alert** and **Retrieval Content
     process failed** (`backend/open_webui/utils/notifications.py:223-231`;
     `backend/open_webui/events.py:164-169`, `:267-271`, `:595-599`, `:414-418`). With none
     picked, the target only serves the `notify` tool.
   - **Automatic Delivery** (shown once an event is picked): **Only when away** (default) or
     **Always** (`src/lib/components/chat/Settings/Notifications.svelte:396-413`).
   - The note under the form: "The notify tool always sends to an enabled target, regardless of
     automatic event settings." (`src/lib/components/chat/Settings/Notifications.svelte:415-419`).
3. Select **Save** (it reads **Saving...** while working). The server validates the address and
   the events and stores the target in the user's settings. **Settings saved successfully!**
   confirms it; a refusal shows the server's reason as a toast (section 10)
   (`src/lib/components/chat/Settings/Notifications.svelte:138-165`;
   `backend/open_webui/utils/notifications.py:29-78`, `:160-177`).
4. The list row shows the id, **Webhook**, **Default** for the default target, a masked address
   (`scheme://host/...` plus the last four characters of the path), the chosen events (or **No
   chat alerts**) and the delivery mode
   (`src/lib/components/chat/Settings/Notifications.svelte:249-283`;
   `backend/open_webui/utils/notifications.py:81-94`). The target routes return only this masked
   form, so the screen does not display the full address. (The address is still part of the
   user's own settings record, which the app loads for that user,
   `backend/open_webui/routers/users.py:457-474`.)
5. Row buttons: **Send Test** (section 5.7), **Make Default** (not shown on the default target),
   **Edit**, **Remove**, and an on/off switch
   (`src/lib/components/chat/Settings/Notifications.svelte:286-331`).
   - **Edit** opens the same window with the address field empty and the placeholder **Keep
     current webhook URL**; leaving it empty keeps the stored address
     (`src/lib/components/chat/Settings/Notifications.svelte:120-130`, `:369-371`;
     `backend/open_webui/utils/notifications.py:37-45`).
   - **Remove** deletes at once, with no confirmation and no toast
     (`src/lib/components/chat/Settings/Notifications.svelte:313-322`). If the default target is
     removed, the next remaining target becomes the default
     (`backend/open_webui/utils/notifications.py:200-210`).

### 5.7 User: Send a Test Notification

1. Select **Send Test** on a target row.
2. The server posts one message to that address and waits for the answer
   (`backend/open_webui/routers/notifications.py:93-103`;
   `backend/open_webui/utils/notifications.py:349-364`). A chat destination (Slack, Google Chat,
   Discord, Teams) shows **Test notification** and "This is a test notification from MedIT GPT."
   (the app name; section 12). A generic JSON receiver gets only
   `{"action": "test", "user_id": "<the user's id>"}` (section 9.4).
3. Success shows **Test notification sent.**; failure shows the server's reason, usually **Webhook
   delivery failed** (`src/lib/components/chat/Settings/Notifications.svelte:176-183`;
   `backend/open_webui/utils/notifications.py:259-261`).

The test is sent even when the target is switched off (the test path does not check the switch,
unlike the `notify` tool) (`backend/open_webui/utils/notifications.py:349-364`, `:381-382`).

### 5.8 User: Turn On Browser Notifications and Sound

1. **Settings › Notifications › Browser Notifications**: switching on asks the browser for
   permission (the browser's own prompt). If permission is granted the choice is saved to the
   account; otherwise the switch stays off and a toast explains that the browser has denied
   permission (section 10) (`src/lib/components/chat/Settings/Notifications.svelte:60-78`). The
   line under the switch reads "Allow browser notifications for completed responses."
   (`src/lib/components/chat/Settings/Notifications.svelte:208-210`).
2. Switching off saves the choice; the browser's permission itself is left as it is
   (`src/lib/components/chat/Settings/Notifications.svelte:74-77`).
3. **Notification Sound** (on by default) saves at once
   (`src/lib/components/chat/Settings/Notifications.svelte:212-223`, `:185-188`).

Both choices are stored in the account (`settings.ui`), so they follow the user to other
browsers; the browser permission does not, and the code does not re-check it before creating a
notification (`src/lib/components/chat/SettingsModal.svelte:438-449`;
`src/routes/+layout.svelte:758-768`).

### 5.9 How "Chat Finished" Reaches a User

When a reply finishes, several independent things can happen:

| Path | Fires when | What the user gets | Source |
|---|---|---|---|
| **Toast** | The browser tab is connected and either the finished chat is not the one on screen (and this tab is not in temporary-chat mode) or the tab is hidden | A card for 15 seconds titled with the chat title (or **New Chat**) and a plain-text preview of the reply; clicking opens the chat. Every connected tab of the user that meets the condition shows it | `src/routes/+layout.svelte:735-781` |
| **Browser notification** | As for the toast, **and** this is the last active tab, **and** **Browser Notifications** is on | "{chat title} / MedIT GPT" with the reply preview | `src/routes/+layout.svelte:758-768` |
| **Sound** | The toast appears in the last active tab, **Notification Sound** is on and the user has interacted with the page | A short chime (`/audio/notification.mp3`) | `src/lib/components/NotificationToast.svelte:68-84` |
| **Personal webhook** | The chat is saved (not temporary), the run is not internal, **User Webhooks** is on, and an enabled target lists **Chat finished** and its delivery is **Always**, or **Only when away** and the user has been away three minutes | A message to the target's address (section 9.4) | `backend/open_webui/utils/middleware.py:206-231`; `backend/open_webui/utils/notifications.py:393-417` |
| **Admin webhooks and Event functions** | Every `chat.finished`, filtered by each webhook's settings | The event envelope or a chat message (section 9.3) | `backend/open_webui/events.py:1034-1059`, `:1103-1156` |

Temporary chats are excluded from both the webhook event (the chat id is not a saved id) and from
toasts in other tabs (`backend/open_webui/utils/middleware.py:210-211`;
`src/routes/+layout.svelte:577-583`). Internal runs (for example sub-agents) are excluded from the
event and their socket messages carry an `internal` mark that suppresses the toast
(`backend/open_webui/utils/subagents.py:68`; `backend/open_webui/utils/middleware.py:210`;
`src/routes/+layout.svelte:735-737`).

`chat.failed` is published only when processing a **non-streaming** reply raises an error, which
includes a background task failing after the answer was already delivered (and `chat.finished`
already published). A failed **streaming** reply (the default) publishes no `chat.failed` event
(`backend/open_webui/utils/middleware.py:4377-4409`); the detail is in
`chat-completion-pipeline-and-generation-tasks.md` (sections 5.7 and 5.8). There is no in-app
toast or browser notification for `chat.failed`.

### 5.10 How a Channel Message Reaches Other Members

1. Someone posts in a channel. After the post is saved, the server works out which members are
   **not connected** to the channel's live room at that moment
   (`backend/open_webui/routers/channels.py:1238-1252`).
2. For each such member who can read the channel, when **User Webhooks** is on and the member has
   any saved settings, a `channel.message` event is published with that member as `user_id`
   (`backend/open_webui/routers/channels.py:941-973`). Their targets that list **Channel message**
   receive it, whatever the delivery mode, because the "away" check is skipped for this event
   (`backend/open_webui/utils/notifications.py:406`). Admin webhooks subscribed to
   `channel.message` receive one copy per offline member.
3. Members who are connected get the live socket message instead. In a tab that is not showing
   that channel, or is hidden, the message raises a toast (15 seconds, "{sender name}
   (#{channel name})", or just the sender's name in a direct message) and, in the last active tab
   with **Browser Notifications** on, a browser notification with the sender's profile picture
   (`src/routes/+layout.svelte:790-895`). Your own messages do not raise a toast or browser
   notification for you (`src/routes/+layout.svelte:827`).

There is no per-channel mute in v0.11.4 (no such setting in the channel code). Channels are
described in `channels-and-direct-messages.md`.

### 5.11 How a Calendar Alert Reaches the User

1. The scheduler loop (section 8) finds an upcoming calendar event that has not been alerted yet,
   sends a `calendar:alert` socket message to every connected tab of the owner, records that the
   alert was sent, and publishes `calendar.alert`
   (`backend/open_webui/utils/automations.py:537-614`).
2. In the browser, the alert is handled before any other check, so **every connected tab** shows a
   toast for 30 seconds titled with the event title and the text **Starting now**, **Starting in 1
   minute** or **Starting in {count} minutes**; clicking it opens `/calendar`. The last active tab
   also creates a browser notification "{event title} / MedIT GPT" when **Browser Notifications**
   is on (`src/routes/+layout.svelte:599-632`).
3. Personal targets that list **Calendar alert** receive "**{title}** starting in {minutes} min"
   (or "starting now"), subject to the delivery mode
   (`backend/open_webui/utils/notifications.py:324-338`, `:403-417`).

Alert timing and reminders are described in `automations-calendar-and-timers.md`.

### 5.12 How a File-Processing Failure Reaches the User

When processing an uploaded file for retrieval fails, `retrieval.content.process_failed` is
published with the uploader as actor, the file name and the error text
(`backend/open_webui/routers/retrieval.py:2155-2178`). A personal target listing **Retrieval
Content process failed** receives "Retrieval Content process failed" with "{file name}: {error}";
a generic JSON target receives the whole event envelope, including the uploader's name and email
(`backend/open_webui/utils/notifications.py:340-343`). There is no in-app toast from this event;
what the upload screen shows is described in `files-uploads-and-storage.md` and
`rag-retrieval-embeddings-and-vector-stores.md`.

### 5.13 Admin: Publish, Change or Remove a Banner

1. **Admin › Settings › General › UI › Banners**: select **+** (**Add banner**); a blank banner is
   added only when the last one is not empty ("Create announcements shown to users in the app.")
   (`src/lib/components/admin/Settings/General.svelte:483-519`;
   `src/lib/i18n/locales/en-US/translation.json:2369`, `:2372`).
2. Choose the **Type** (**Info**, **Warning**, **Error**, **Success**; required), type the
   **Content** (Markdown is allowed), and decide **Remember Dismissal** (on by default). Drag the
   handle (tooltip **Reorder**) to change the order; the **×** (tooltip **Delete**) removes one
   (`src/lib/components/admin/Settings/Interface/Banners.svelte:37-98`).
3. To give a banner text in other languages, pick a language in the selector beside **Banners**
   (shown once a banner exists) and type the translated content
   (`src/lib/components/admin/Settings/General.svelte:489-491`;
   `src/lib/components/admin/Settings/Interface/Banners.svelte:65-74`).
4. Select **Save** at the bottom of the General tab. Banners are saved after the other General
   settings, replacing the whole banner list, and a `config.banners.updated` event is published
   (`src/lib/components/admin/Settings/General.svelte:80-106`;
   `backend/open_webui/routers/configs.py:852-869`). A banner left without a type stops the form
   from being submitted (the field is required).
5. Users receive the banner list when the app loads (sign-in or a full page reload); nothing
   pushes a change to pages that are already open (`src/routes/(app)/+layout.svelte:156-159`,
   `:224-225`).
6. Each user sees the banners on the new-chat screen only (no chat open), under the top bar, each
   with a coloured type label, the content and a **×** (**Close Banner**). With **Remember
   Dismissal** on, closing stores the banner's id in the browser (`dismissedBannerIds`) and the
   banner stays hidden in that browser; with it off, closing hides it only until the page reloads
   (`src/lib/components/chat/Navbar.svelte:56-64`, `:271`, `:300-318`;
   `src/lib/components/common/Banner.svelte:47-155`).

Removing a banner and saving deletes it for everyone; dismissal records of banners that no longer
exist are cleaned up the next time the user closes a banner that has **Remember Dismissal** on
(`src/lib/components/chat/Navbar.svelte:306-314`).

### 5.14 Admin: The Update Toast and the What's New Window

**Update toast** (`src/routes/(app)/+layout.svelte:369-382`, `:415-438`;
`backend/open_webui/main.py:2594-2613`):

1. When an administrator's app loads, and the version check is on
   (`ENABLE_VERSION_UPDATE_CHECK`, default on; forced off by `OFFLINE_MODE`), and the toast was not
   closed in the last 24 hours in this browser, the browser asks the server for the latest
   release.
2. The server asks GitHub for the latest **upstream Open WebUI** release (one-second limit) and
   returns it with the running version. On any failure the "latest" value is empty and no toast is
   shown (the version blocks then read `Could not check for updates`, section 10.8).
3. If the latest version is newer and **Toast Notifications for New Updates** is on, the toast
   "A new version (v{LATEST_VERSION}) is now available." appears bottom-right with the link
   **Update for the latest features and improvements.** to the upstream GitHub releases page.
   Closing it (**×**) stores the time in the browser (`dismissedUpdateToast`) and hides it for 24
   hours.

**What's New** (`src/routes/(app)/+layout.svelte:355-357`;
`src/lib/components/ChangelogModal.svelte`):

1. When an administrator's app loads and `Show "What's New" Modal on Login` is on (default), the
   window opens by itself if the version stored in their settings differs from the running
   version, that is after an upgrade or on an administrator's first sign-in.
2. It is titled "What's New in MedIT GPT" (the app name) with **Release Notes** and the running
   version, and lists the five newest entries of the bundled `CHANGELOG.md`, which is the
   **upstream Open WebUI changelog** (versions 0.11.0 to 0.11.4 at this release), grouped by
   section (added, fixed, changed, removed and so on)
   (`src/lib/components/ChangelogModal.svelte:91-169`; `backend/open_webui/main.py:2616-2618`;
   `CHANGELOG.md:8`).
3. **Okay, Let's Go!** or the **×** stores the running version in the account and closes it, so
   it does not open again until the next upgrade
   (`src/lib/components/ChangelogModal.svelte:41-46`, `:194-200`). Closing it with Escape or by
   clicking outside it hides it without recording the version, so it opens again at the next load
   (`src/lib/components/common/Modal.svelte:46-52`, `:134-135`).
4. Anyone can open it again from **See what's new** in **Settings › About**; administrators also
   from **Admin › Settings › General**
   (`src/lib/components/chat/Settings/About.svelte:89-96`;
   `src/lib/components/admin/Settings/General.svelte:163-171`).

Neither the toast nor the window says anything about MedIT GPT's own releases; see section 12.

### 5.15 Event Functions as Listeners

Every published event is also handed, in a background task, to the `event` method of every active
Event function (when plugins are enabled), with the event envelope and its name; failures are
logged and do not affect the user (`backend/open_webui/events.py:1103-1168`). Switching a function
on or off additionally sends `function.enable_started` or `function.disable_started` to Event
functions inside the request, before the change, and then to admin webhooks
(`backend/open_webui/routers/functions.py:297-311`). How to write, install and troubleshoot Event
functions is in `functions-pipes-filters-actions-and-pipelines.md` (sections 5.12, 8.3, 9.3 and
9.4).

### 5.16 Toasts Raised by Tools and Functions Inside a Chat

A tool or function can send an item of type `notification` with a level (`success`, `error`,
`warning`, otherwise information) and text. The open chat shows it as a plain toast of that
colour (`src/lib/components/chat/Chat.svelte:1354-1366`). It appears only in the tab that has
that chat open (`src/lib/components/chat/Chat.svelte:1203-1206`), and items from internal runs
are dropped before they are sent (`backend/open_webui/socket/main.py:1146-1147`). The texts are
written by whoever wrote the tool or function, so they are not catalogued here.

## 6. Data Model

This area has **no table of its own**. Events are not stored: there is no event log, no delivery
history and no queue, so nothing in the database shows whether a webhook message was sent
(`backend/open_webui/events.py:1034-1086`, `:1171-1202`). What is stored lives in settings rows
and in each user's settings record.

### 6.1 Settings Rows (Table `config`)

One row per key, value stored as JSON (`backend/open_webui/models/config.py:101-108`).

| Key | Holds | Written by | Source |
|---|---|---|---|
| `events.webhooks` | The admin webhook list (fields in 6.2). Not one of the seeded defaults: the row appears when the first webhook is saved or migrated; until then the list is empty | Admin › Settings › General › Events; start-up migration | `backend/open_webui/events.py:20`, `:838-851`, `:877`, `:907`, `:921` |
| `webhook_url` | Legacy single admin webhook address; seeded from `WEBHOOK_URL` at first boot; emptied when the **Default webhook** is deleted | Seed; webhook deletion | `backend/open_webui/config.py:2080`, `:3122`; `backend/open_webui/events.py:917-919` |
| `ui.enable_user_webhooks` | The **User Webhooks** switch | Admin › Settings › General | `backend/open_webui/config.py:2100`, `:3125`; `backend/open_webui/routers/auths.py:131` |
| `user.permissions` | Default permissions, including `features.webhooks` | Admin › Users › Groups › Default permissions | `backend/open_webui/config.py:1932-1934`, `:2015` |
| `ui.banners` | The banner list (fields in 6.4); seeded from `WEBUI_BANNERS` at first boot | Admin › Settings › General › UI › Banners | `backend/open_webui/config.py:2150-2167`, `:3126`; `backend/open_webui/routers/configs.py:859` |
| `webui.url` | The **WebUI URL** used to build links in notifications | Admin › Settings › General | `backend/open_webui/utils/middleware.py:214`; `backend/open_webui/routers/channels.py:942` |

Because the server reads these rows on every use, a change applies at once to every worker
process; there is no cache to clear (`backend/open_webui/models/config.py:140-147`;
`backend/open_webui/events.py:838-839`, `:1046`). The exception is a deployment with
`ENABLE_PERSISTENT_CONFIG` off, where a saved value stays in the memory of the process that saved
it (`backend/open_webui/models/config.py:132-138`, `:198-209`; ground truth).

### 6.2 Admin Webhook Object (Inside `events.webhooks`)

| Field | Meaning | Source |
|---|---|---|
| `id` | Random identifier, or `default` for the migrated legacy webhook | `backend/open_webui/events.py:709`, `:866` |
| `name` | Display name; `Default webhook` or `Webhook` when empty | `backend/open_webui/events.py:729` |
| `url` | The full address. Treat it as confidential: the admin list shows only its host, and personal addresses are shown masked (section 5.6); never copy one into a ticket | `backend/open_webui/events.py:710`; `src/lib/components/admin/Settings/Events.svelte:180-186` |
| `enabled` | On/off | `backend/open_webui/events.py:731` |
| `events` | Filters: `*`, exact names, `prefix.*` patterns; empty becomes `*` | `backend/open_webui/events.py:712-723` |
| `targets` | `null` (all), empty list (system only), or a list of `{type: user\|group, id}` | `backend/open_webui/events.py:739-763` |
| `created_at`, `updated_at` | Seconds since 1970 | `backend/open_webui/events.py:734-735` |

### 6.3 Personal Notification Settings (Table `user`, Column `settings`)

The user's settings are one JSON value in the `user` row
(`backend/open_webui/models/users.py:138-141`, `:825-847`). This area uses:

| Path inside `settings` | Meaning | Source |
|---|---|---|
| `notifications.targets[]` | The user's targets: `id`, `type` (`webhook`), `enabled`, `events` (subset of the five), `delivery` (`away` or `always`), `config.url` (the full address), `created_at`, `updated_at` | `backend/open_webui/utils/notifications.py:69-78` |
| `notifications.default_target_id` | The default target's id | `backend/open_webui/utils/notifications.py:126`, `:132-134`, `:175`, `:217` |
| `notifications.legacy_notification_events_migrated` | Marks that the legacy address was converted | `backend/open_webui/utils/notifications.py:127`, `:135-147` |
| `notifications.webhook_url`, `ui.notifications.webhook_url` | Legacy single personal address from earlier releases; read once and converted into a target with id `webhook` | `backend/open_webui/utils/notifications.py:107-129` |
| `ui.notificationEnabled` | **Browser Notifications** (default off) | `src/lib/components/chat/Settings/Notifications.svelte:66`, `:186`; `src/lib/stores/index.ts:275` |
| `ui.notificationSound` | **Notification Sound** (default on) | `src/lib/components/chat/Settings/Notifications.svelte:187`, `:220`; `src/lib/stores/index.ts:234` |
| `ui.notificationSoundAlways` | With **Notification Sound** on, plays the sound for a finished reply in every tab that shows the toast, not only the last active tab; no switch exists for it in the interface (default off) | `src/routes/+layout.svelte:745-756`; `src/lib/stores/index.ts:235` |
| `ui.showUpdateToast` | **Toast Notifications for New Updates** (default on) | `src/lib/components/common/InterfaceSettings.svelte:329`, `:726-730` |
| `ui.showChangelog` | `Show "What's New" Modal on Login` (default on) | `src/lib/components/common/InterfaceSettings.svelte:330`, `:749-753` |
| `ui.version` | The version whose release notes the user last closed | `src/lib/components/ChangelogModal.svelte:41-46` |

Other columns used: `user.last_active_at` (seconds; the "away" test, section 4) and, for calendar
alerts, `calendar_event.meta.alerted_at` (nanoseconds; prevents a second alert)
(`backend/open_webui/models/users.py:918-925`; `backend/open_webui/utils/automations.py:559-594`).

### 6.4 Banner Object (Inside `ui.banners`)

| Field | Meaning | Source |
|---|---|---|
| `id` | Random identifier created in the browser; dismissal is remembered by this id | `backend/open_webui/config.py:2152`; `src/lib/components/admin/Settings/General.svelte:501` |
| `type` | `info`, `warning`, `error` or `success` from the editor; other text is accepted by the server and shown as-is with the Info colour | `backend/open_webui/config.py:2153`; `src/lib/components/common/Banner.svelte:28-33`, `:56-69` |
| `title` | Optional; stored but **not displayed** by the banner component | `backend/open_webui/config.py:2154`; `src/lib/components/common/Banner.svelte:47-155` |
| `content` | Markdown text; line breaks are kept | `backend/open_webui/config.py:2155`; `src/lib/components/common/Banner.svelte:103-113` |
| `i18n` | Per-language versions of `content` | `backend/open_webui/config.py:2151`; `src/lib/components/admin/Settings/Interface/Banners.svelte:65-74` |
| `dismissible` | **Remember Dismissal** | `backend/open_webui/config.py:2156` |
| `timestamp` | Seconds since 1970 when the banner was added in the editor | `backend/open_webui/config.py:2157`; `src/lib/components/admin/Settings/General.svelte:506` |

The browser-side banner type also has a `url` field, and the banner component shows a **Learn
More** link when it is set, but the stored banner model has no `url` field, so banners saved through MedIT GPT do
not show that link (`src/lib/types/index.ts:1-10`; `src/lib/components/common/Banner.svelte:72-101`,
`:117-144`; `backend/open_webui/config.py:2150-2157`).

### 6.5 Browser Storage

| Key (browser `localStorage`) | Meaning | Source |
|---|---|---|
| `dismissedBannerIds` | Ids of banners closed with **Remember Dismissal** on | `src/lib/components/chat/Navbar.svelte:58-64`, `:307-314` |
| `dismissedUpdateToast` | When the update toast was last closed (milliseconds); hides it for 24 hours | `src/routes/(app)/+layout.svelte:372-381`, `:433` |
| `version` | Copy of the version whose release notes were closed | `src/lib/components/ChangelogModal.svelte:42` |

Clearing site data in the browser brings back dismissed banners and the update toast.

## 7. Settings and Configuration

Defaults below are what the code says. The live value of every persistent setting is data in the
`config` table and is **TO BE CONFIRMED** for production; after first boot the stored value wins
over the environment variable (ground truth).

### 7.1 Persistent Settings

| Setting (key) | Environment variable that seeds it | Code default | Where admins change it | Effect | Source |
|---|---|---|---|---|---|
| `ui.enable_user_webhooks` | `ENABLE_USER_WEBHOOKS` | off | Admin › Settings › General › Features › **User Webhooks** | Master switch for personal notification targets, their automatic delivery, channel-message events and the `notify` tool | `backend/open_webui/config.py:2100`, `:3125`; `backend/open_webui/routers/notifications.py:35-36`; `backend/open_webui/utils/notifications.py:394`; `backend/open_webui/routers/channels.py:943`, `:953`; `backend/open_webui/utils/tools.py:759-764` |
| `user.permissions` › `features.webhooks` | `USER_PERMISSIONS_FEATURES_USER_WEBHOOKS` | off | Admin › Users › Groups › Default permissions (or a group) › **User Webhooks** | Lets non-admins see and save notification targets and use `notify` | `backend/open_webui/config.py:1932-1934`, `:2015`; `src/lib/components/admin/Users/Groups/Permissions.svelte:1153-1167` |
| `events.webhooks` | none | empty list | Admin › Settings › General › **Events › Webhooks** | The admin webhook list | `backend/open_webui/events.py:20`, `:838-851` |
| `webhook_url` | `WEBHOOK_URL` | empty | No screen in v0.11.4 | Legacy address, copied into the **Default webhook** at start-up | `backend/open_webui/config.py:2080`, `:3122`; `backend/open_webui/events.py:854-878` |
| `ui.banners` | `WEBUI_BANNERS` (a JSON list) | empty list | Admin › Settings › General › UI › **Banners** | Banners on the new-chat screen. An unreadable `WEBUI_BANNERS` value is logged and ignored | `backend/open_webui/config.py:2150-2167`, `:3126` |
| `webui.url` | `WEBUI_URL` | empty | Admin › Settings › General › Features › **WebUI URL** | Start of every link in chat and channel notifications; relative links when empty | `backend/open_webui/config.py:1661`, `:3082`; `backend/open_webui/routers/auths.py:107` |

### 7.2 Environment-Only Settings That Change This Area

| Variable | Code default | Effect here | Source |
|---|---|---|---|
| `ENABLE_VERSION_UPDATE_CHECK` | on | Update toast, "available!" text and **Check for updates** buttons; when off the server reports the running version as the latest | `backend/open_webui/env.py:1200`; `backend/open_webui/main.py:2347`, `:2596-2598` |
| `OFFLINE_MODE` | off | When on, forces the version check off | `backend/open_webui/env.py:1201-1205` |
| `WEBUI_NAME` | `MedIT GPT` (fork) | The name in browser-notification titles, the test notification, Teams cards and the What's New title | `backend/open_webui/env.py:951`; `backend/open_webui/main.py:538`; `src/routes/+layout.svelte:1274` |
| `ENABLE_PLUGINS` | on | When off, Event functions receive nothing | `backend/open_webui/env.py:1186`; `backend/open_webui/events.py:1106-1107` |
| `INSTANCE_ID` | random per process | The `instance_id` in every event | `backend/open_webui/env.py:155` |
| `AIOHTTP_CLIENT_TIMEOUT` | unset, which means **no time limit** (300 seconds only if the value cannot be read as a number) | Time limit for each webhook post | `backend/open_webui/env.py:608-612`; `backend/open_webui/retrieval/web/utils.py:280-285` |
| `AIOHTTP_CLIENT_SESSION_SSL` | on | Certificate checking for webhook posts | `backend/open_webui/env.py:631`; `backend/open_webui/utils/webhook.py:88-92` |
| `AIOHTTP_CLIENT_ALLOW_REDIRECTS` | off | Whether webhook posts follow redirects | `backend/open_webui/env.py:636-637`; `backend/open_webui/utils/webhook.py:92` |
| `ENABLE_LOCAL_WEB_FETCH` | off | The same address check as web loading decides which webhook addresses are accepted; see `web-search-and-web-loading.md` | `backend/open_webui/config.py:1110-1116`; `backend/open_webui/retrieval/web/utils.py:131-167` |
| `WEBSOCKET_HEARTBEAT_INTERVAL` | unset (the browser then uses 30 seconds); otherwise 5 to 90 seconds | How often an open tab marks the user as present (the "away" test) | `backend/open_webui/env.py:525-532`; `backend/open_webui/main.py:2338`; `src/routes/+layout.svelte:217-225` |
| `SCHEDULER_POLL_INTERVAL`, `CALENDAR_ALERT_LOOKAHEAD_MINUTES` | 10 seconds, 10 minutes | How often and how far ahead calendar alerts are checked | `backend/open_webui/utils/automations.py:53`, `:55` |

### 7.3 Per-User and Per-Model Settings

| Setting | Where | Default | Source |
|---|---|---|---|
| **Browser Notifications** (`notificationEnabled`) | Settings › Notifications | off | `src/lib/components/chat/Settings/Notifications.svelte:26`, `:186` |
| **Notification Sound** (`notificationSound`) | Settings › Notifications | on | `src/lib/components/chat/Settings/Notifications.svelte:27`, `:187` |
| `notificationSoundAlways` | No screen | off | `src/routes/+layout.svelte:747` |
| **Toast Notifications for New Updates** (`showUpdateToast`) | Settings › Interface (admins) | on ("Show update toasts to admins when new versions are available.") | `src/lib/components/common/InterfaceSettings.svelte:715-737`; `src/lib/i18n/locales/en-US/translation.json:2988-2989` |
| `Show "What's New" Modal on Login` (`showChangelog`) | Settings › Interface (admins) | on ("Open the changelog modal after sign-in when enabled.") | `src/lib/components/common/InterfaceSettings.svelte:739-760` |
| Notification targets | Settings › Notifications | none | section 5.6 |
| **Notifications** built-in tool group on a model | Workspace › Models › edit › built-in tools | on unless switched off | `backend/open_webui/utils/tools.py:536-540`, `:759-764`; see `builtin-native-tools.md` |

When the admin has saved **Default interface settings**, users' own choices are merged over them
(`src/lib/components/chat/SettingsModal.svelte:445-449`); see `user-settings-and-personalisation.md`.

## 8. Cron Jobs and Background Processes

There is no crontab and no separate worker (ground truth). Everything in this area happens either
at save time, in a short background task started by the request that published an event, or in
the scheduler loop that runs inside each server process.

### 8.1 Event Delivery Tasks

| Work | When it runs | How | Failure behaviour | Source |
|---|---|---|---|---|
| Admin webhook delivery | Right after each published event | One background task per event; it reads the webhook list, then posts to each matching webhook **one after another** | Each failure is logged and the next webhook is still tried; nothing is retried and nothing is recorded for the admin | `backend/open_webui/events.py:1034-1071` |
| Personal target delivery | Right after each of the five notification-capable events, when **User Webhooks** is on | One background task per event; for each associated user, each matching target in turn | Logged as `Notification delivery failed for user %s and event %s`; no retry | `backend/open_webui/events.py:1074-1086`; `backend/open_webui/utils/notifications.py:393-419` |
| Event functions | Right after each published event, when plugins are enabled | One background task per event; each active Event function in turn | Logged per function; no retry | `backend/open_webui/events.py:1103-1168` |
| Live-socket disconnect | When `user.deleted` or `user.role_updated` is published (open tabs then reconnect) | Inside the publishing request, before the other sinks | Logged as a sink failure | `backend/open_webui/events.py:1089-1100`, `:1171`, `:1198-1202` |
| Channel-message events | After a channel post is saved | A request background task that first runs any model reply in the channel, then publishes one `channel.message` per offline member | — | `backend/open_webui/routers/channels.py:1238-1252`, `:941-973` |

These tasks exist only in the memory of the server process that published the event. A restart or
crash loses deliveries that were still in progress, and with several worker processes each one
delivers the events it published itself (`backend/open_webui/events.py:1062-1066`). Because the
default HTTP client has no time limit (`AIOHTTP_CLIENT_TIMEOUT` unset, section 7.2), a receiving
server that never answers keeps that task waiting and delays the webhooks after it for the same
event; the chat or settings change that published the event is not held up.

### 8.2 Scheduler Loop (Calendar Alerts)

`scheduler_worker_loop` starts with every server process. About every `SCHEDULER_POLL_INTERVAL`
seconds (default 10, plus up to two seconds of random spread) it checks, when the calendar feature
is on, for events starting within the look-ahead window that have not been alerted, and for each:
sends the `calendar:alert` socket message, marks the event as alerted, and publishes
`calendar.alert` (`backend/open_webui/utils/automations.py:53-55`, `:69-126`, `:537-614`). Details
of reminder timing are in `automations-calendar-and-timers.md`.

### 8.3 Start-Up and Shut-Down

| Step | What happens | Source |
|---|---|---|
| Start-up, after settings load | Legacy admin webhook migration (section 5.4), then `system.startup.started` | `backend/open_webui/main.py:361-370` |
| End of start-up | `system.startup.completed` | `backend/open_webui/main.py:471-472` |
| Shut-down | `system.shutdown.started` at the start, `system.shutdown.completed` at the end | `backend/open_webui/main.py:476`, `:496` |

Each worker process runs its own start-up, so a server with several workers publishes these events
once per worker (`backend/open_webui/main.py:345-472`).

### 8.4 Browser-Side Timers

| Timer | Interval | Purpose | Source |
|---|---|---|---|
| Socket heartbeat | 30 seconds by default (server can set 5 to 90) | Keeps `last_active_at` fresh, which decides "away" | `src/routes/+layout.svelte:217-225`; `backend/open_webui/socket/main.py:489-494` |
| Update check | Once when an administrator's app loads (unless the toast was closed in the last 24 hours) and when **Check for updates** is selected | Update toast and "available!" text | `src/routes/(app)/+layout.svelte:369-382`; `src/lib/components/admin/Settings/General.svelte:52-65`, `:108-118`; `src/lib/components/chat/Settings/About.svelte:25-48` |
| Toast lifetime | 15 seconds (chat and channel), 30 seconds (calendar) | How long a notification card stays | `src/routes/+layout.svelte:616`, `:778`, `:890` |

Banners and webhook settings are applied at save time; nothing re-sends or refreshes them on a
schedule.

## 9. Notifications and Emails

### 9.1 No Email

MedIT GPT sends no email of any kind (section 1). Every notification is one of: an in-app toast,
a browser notification, a banner, the admin update toast or What's New window, an HTTP post to an
admin event webhook or to a personal notification target, or a call to an Event function.

### 9.2 Event Catalogue

The catalogue holds **181 events** (`backend/open_webui/events.py:42-661`). The tables below list
every one, with its short message in brackets (the text chat-format webhooks show), when the code
publishes it, the extra fields in `data`, and the personal or content data the payload carries.

How to read the personal-data column:

- **Actor** means the envelope's `actor` block: the acting account's id, **name**, **email**, role
  and creation and update times (`backend/open_webui/events.py:704`, `:974-985`). Rows marked
  **no actor** have none.
- Every event also carries its subject id (a chat, file, user or other id), which identifies a
  person's content even without a name.
- Text fields are cut to 1,000 characters; fields named `content_preview`, `prompt_preview` and
  `input_preview` are already cut to 300 characters by the code that publishes them
  (`backend/open_webui/events.py:968-969`; for example `backend/open_webui/main.py:1435`).
- Line numbers are the start of each publishing call.

#### 9.2.1 System and Configuration Events

| Event (short message) | Published when | `data` fields | Personal or content data | Source |
|---|---|---|---|---|
| `system.startup.started` (Startup started) | A server process begins start-up, after settings load and the legacy webhook migration | none | none (**no actor**, `source` `system`) | `backend/open_webui/main.py:370` |
| `system.startup.completed` (Startup completed) | Start-up finished | none | none | `backend/open_webui/main.py:472` |
| `system.shutdown.started` (Shutdown started) | The process begins to stop | none | none | `backend/open_webui/main.py:476` |
| `system.shutdown.completed` (Shutdown completed) | The process finished stopping | none | none | `backend/open_webui/main.py:496` |
| `config.imported` (Config imported) | An administrator imports a settings file | `keys` (names of the imported settings) | Actor | `backend/open_webui/routers/configs.py:103` |
| `config.updated` (Config updated) | An administrator saves the Audio, Images or Evaluations settings, or the sub-agent switch. **Not** published by the General, Authentication (including LDAP and OAuth), Documents, Web Search or embedding saves | engine names and on/off values for the saved area (`tts_engine`, `stt_engine`; image engines; `keys`, `arena_enabled`, `arena_model_count`; `enabled`) | Actor | `backend/open_webui/routers/audio.py:313`; `backend/open_webui/routers/images.py:307`; `backend/open_webui/routers/evaluations.py:313`; `backend/open_webui/routers/configs.py:796`; no call in `backend/open_webui/routers/auths.py:1270-1512` or `backend/open_webui/routers/retrieval.py:538`, `:963` |
| `config.webhook.updated` (Webhook configuration updated) | An admin webhook is created, changed (including the on/off switch) or deleted | `action`, `enabled`, `events`, `targets` (user and group ids). The address is not included | Actor | `backend/open_webui/main.py:2519`, `:2553`, `:2575` |
| `config.connections.updated` (Config Connections updated) | Admin › Settings › Connections saved | the three connection switches | Actor | `backend/open_webui/routers/configs.py:152` |
| `config.tool_servers.updated` (Config Tool Servers updated) | Tool server connections saved | `count`, `types` | Actor | `backend/open_webui/routers/configs.py:290` |
| `config.terminal_servers.updated` (Config Terminal Servers updated) | Terminal server connections saved | `count` | Actor | `backend/open_webui/routers/configs.py:344` |
| `config.code_execution.updated` (Config Code Execution updated) | Code execution settings saved | engine names and on/off values | Actor | `backend/open_webui/routers/configs.py:715` |
| `config.models.updated` (Config Models updated) | Default models or model order saved | `default_models`, `default_pinned_models`, `model_order_count` | Actor | `backend/open_webui/routers/configs.py:758` |
| `config.banners.updated` (Config Banners updated) | Banners saved | `count` | Actor | `backend/open_webui/routers/configs.py:861` |
| `config.suggestions.updated` (Config Suggestions updated) | Default prompt suggestions saved | `count` | Actor | `backend/open_webui/routers/configs.py:832` |

#### 9.2.2 Sign-In, Account and Group Events

| Event (short message) | Published when | `data` fields | Personal or content data | Source |
|---|---|---|---|---|
| `auth.signup` (User signed up) | Someone creates an account with the sign-up form | `email` | Actor; the new account's email | `backend/open_webui/routers/auths.py:939` |
| `auth.login` (User logged in) | Every successful sign-in: password, LDAP, trusted header, authentication switched off, right after sign-up, single sign-on, and the OAuth token exchange | `auth_method` (`password`, `ldap`, `trusted_header`, `system`, `api`, `oauth`); `provider` for single sign-on | Actor | `backend/open_webui/routers/auths.py:210` (callers `:702`, `:831`, `:947`, `:1771`); `backend/open_webui/utils/oauth.py:2200` |
| `auth.logout` (User logged out) | Sign-out; the actor is empty when the session could not be identified | none | Actor (when known) | `backend/open_webui/routers/auths.py:976` |
| `auth.password_changed` (Password changed) | A user changes their own password, or an administrator sets a user's password (`source` `admin`) | none (no password or hash) | Actor; the user's id | `backend/open_webui/routers/auths.py:412`; `backend/open_webui/routers/users.py:1016` |
| `auth.api_key.created` (API key created) | A user generates an API key | none (the key is not included) | Actor | `backend/open_webui/routers/auths.py:1539` |
| `auth.api_key.deleted` (API key deleted) | A user deletes their API key | none | Actor | `backend/open_webui/routers/auths.py:1561` |
| `auth.oauth_session.deleted` (OAuth session deleted) | A user disconnects a stored OAuth session for a provider | `provider` | Actor | `backend/open_webui/routers/auths.py:1085` |
| `user.created` (User created) | An administrator adds a user (`source` `admin`); first LDAP sign-in; sign-up or the first trusted-header sign-in (`source` `api` or `trusted_header`); SCIM provisioning (**no actor**); first single sign-on | `role`; SCIM adds `email` and `external_id`; single sign-on adds `provider` | Actor (the new user, or the admin who added them); email and external id from SCIM | `backend/open_webui/routers/auths.py:1137`, `:675`, `:887`; `backend/open_webui/routers/scim.py:644`; `backend/open_webui/utils/oauth.py:2139` |
| `user.updated` (User updated) | A user's time zone is recorded; an administrator edits a user; SCIM changes (**no actor**); name, email or picture refreshed at single sign-on | `updated_fields` (names only); `provider` | Actor | `backend/open_webui/routers/auths.py:369`; `backend/open_webui/routers/users.py:998`; `backend/open_webui/routers/scim.py:719`, `:822`; `backend/open_webui/utils/oauth.py:2085` |
| `user.deleted` (User deleted) | An administrator deletes a user; SCIM deletion (**no actor**). Also disconnects the user's live sessions | none; SCIM adds `email` | Actor; email from SCIM | `backend/open_webui/routers/users.py:1067`; `backend/open_webui/routers/scim.py:864`; `backend/open_webui/events.py:1089-1100` |
| `user.role_updated` (User role updated) | An administrator changes a role; trusted-header role sync; SCIM (**no actor**); single sign-on role mapping. Also disconnects the user's live sessions | `role`; `provider` | Actor | `backend/open_webui/routers/users.py:1007`; `backend/open_webui/routers/auths.py:777`; `backend/open_webui/routers/scim.py:728`, `:831`; `backend/open_webui/utils/oauth.py:1636` |
| `user.status_updated` (User status updated) | A user sets their status | none | Actor | `backend/open_webui/routers/users.py:604` |
| `user.settings_updated` (User settings updated) | A user saves any personal setting (each switch in Settings saves at once, so this is frequent) | none | Actor | `backend/open_webui/routers/users.py:551` |
| `user.profile_updated` (User profile updated) | A user edits their profile | `updated_fields` | Actor | `backend/open_webui/routers/auths.py:333` |
| `user.permissions_updated` (User permissions updated) | An administrator saves Default permissions | none | Actor | `backend/open_webui/routers/users.py:428` |
| `group.created` (Group created) | An administrator creates a group; SCIM (**no actor**); single sign-on group creation (**no actor**) | `name`; SCIM adds `member_ids`, `member_count` | Actor; group name; member ids | `backend/open_webui/routers/groups.py:70`; `backend/open_webui/routers/scim.py:989`; `backend/open_webui/utils/oauth.py:1708` |
| `group.updated` (Group updated) | An administrator edits a group; SCIM (**no actor**) | `name`; `updated_fields` or `operation_count` | Actor; group name | `backend/open_webui/routers/groups.py:191`; `backend/open_webui/routers/scim.py:1051`, `:1143` |
| `group.deleted` (Group deleted) | An administrator deletes a group; SCIM (**no actor**) | SCIM adds `name` | Actor | `backend/open_webui/routers/groups.py:311`; `backend/open_webui/routers/scim.py:1192` |
| `group.member_added` (Group member added) | Members added by an administrator, by single sign-on group sync, or by SCIM (**no actor**) | `user_ids` (admin, single sign-on) or `member_ids` and `count` (SCIM) | Actor; member ids | `backend/open_webui/routers/groups.py:236`; `backend/open_webui/utils/oauth.py:1777`; `backend/open_webui/routers/scim.py:997`, `:1059`, `:1151` |
| `group.member_removed` (Group member removed) | As above, for removals | as above | Actor; member ids | `backend/open_webui/routers/groups.py:273`; `backend/open_webui/utils/oauth.py:1740`; `backend/open_webui/routers/scim.py:1067`, `:1159` |

#### 9.2.3 Chat and Message Events

| Event (short message) | Published when | `data` fields | Personal or content data | Source |
|---|---|---|---|---|
| `chat.created` (Chat created) | A chat is created by the first message of a conversation, or through the chat list | `title` (`New Chat` at first), `folder_id` | Actor | `backend/open_webui/main.py:1418`; `backend/open_webui/routers/chats.py:789` |
| `chat.finished` (Chat finished) | A reply finished in a saved, non-internal chat (streaming or not) | `user_id`, `chat_id`, `message_id`, `model_id`, `title`, `url`, `message` (the reply text) | Actor; **chat title; the reply text (first 1,000 characters)**. The event's message is the chat title | `backend/open_webui/utils/middleware.py:215` (callers `:4377`, `:6566`) |
| `chat.failed` (Chat failed) | Processing a non-streaming reply raised an error (section 5.9) | `user_id`, `chat_id`, `message_id`, `model_id`, `url`, `message` (the error text) | Actor; error text | `backend/open_webui/utils/middleware.py:4393` |
| `chat.imported` (Chat imported) | Chats are imported | `count`, `chat_ids` | Actor | `backend/open_webui/routers/chats.py:818` |
| `chat.updated` (Chat updated) | A chat is saved or renamed through the chat update route | `title` | Actor; **chat title** | `backend/open_webui/routers/chats.py:1384` |
| `chat.deleted` (Chat deleted) | One chat is deleted | `owner_id` | Actor | `backend/open_webui/routers/chats.py:1609` |
| `chat.deleted_all` (Chat deleted all) | A user deletes all their chats | none | Actor | `backend/open_webui/routers/chats.py:721` |
| `chat.compacted` (Chat compacted) | A chat's context is compacted | `dropped_messages` (a count) | Actor | `backend/open_webui/routers/chats.py:1310` |
| `chat.pinned`, `chat.unpinned` (Chat pinned, Chat unpinned) | Pin toggled | none | Actor | `backend/open_webui/routers/chats.py:1647` |
| `chat.cloned` (Chat cloned) | A chat is cloned, or forked from a message | `original_chat_id`; `forked_from_message_id` | Actor | `backend/open_webui/routers/chats.py:1765`, `:1812` |
| `chat.archived`, `chat.unarchived` (Chat archived, Chat unarchived) | One chat, or all of a user's chats (then the subject is the user) | none | Actor | `backend/open_webui/routers/chats.py:1930`, `:1119`, `:1134` |
| `chat.shared` (Chat shared) | A share link is created or refreshed | `share_id`; `updated` | Actor | `backend/open_webui/routers/chats.py:1964`, `:1982` |
| `chat.unshared` (Chat unshared) | A share link is removed, or all of a user's links | `share_id`; or `count`, `chat_ids` | Actor | `backend/open_webui/routers/chats.py:2010`, `:1160` |
| `chat.folder_updated` (Chat folder updated) | A chat is moved to another folder | `folder_id` | Actor | `backend/open_webui/routers/chats.py:2144` |
| `chat.tag_added`, `chat.tag_removed` (Chat tag added, Chat tag removed) | A tag is added to or removed from a chat | `tag` | Actor; tag text | `backend/open_webui/routers/chats.py:2202`, `:2233` |
| `message.created` (Message created) | Chat: the user's message and each reply placeholder when a chat request starts. Channel: a post by a person or by a channel's incoming webhook (`source` `channel_webhook`, the actor is the webhook's id and name) | `chat_id` or `channel_id`, `role`, `model`, `content_preview` | Actor; **the first 300 characters of every message a person sends** | `backend/open_webui/main.py:1427`, `:1441`, `:1528`, `:1623`; `backend/open_webui/routers/channels.py:1254`, `:2076` |
| `message.updated` (Message updated) | A chat or channel message is edited | `chat_id` or `channel_id`, `content_preview` | Actor; first 300 characters of the new text | `backend/open_webui/routers/chats.py:1458`; `backend/open_webui/routers/channels.py:1550` |
| `message.deleted` (Message deleted) | A chat or channel message is deleted | `chat_id` or `channel_id` | Actor | `backend/open_webui/routers/chats.py:1497`; `backend/open_webui/routers/channels.py:1800` |
| `message.event_received` (Message event received) | A message-level event is sent to a chat message through its event route | `chat_id`, `event_type` | Actor | `backend/open_webui/routers/chats.py:1551` |
| `message.reaction_added`, `message.reaction_removed` (Message reaction added, Message reaction removed) | A channel reaction is added or removed | `channel_id`, `reaction` | Actor | `backend/open_webui/routers/channels.py:1628`, `:1703` |
| `message.pinned`, `message.unpinned` (Message pinned, Message unpinned) | A channel message is pinned or unpinned | `channel_id` | Actor | `backend/open_webui/routers/channels.py:1413` |

#### 9.2.4 Channel Events

| Event (short message) | Published when | `data` fields | Personal or content data | Source |
|---|---|---|---|---|
| `channel.created` (Channel created) | A channel, group chat or direct message is created | `type`, `name` | Actor; channel name | `backend/open_webui/routers/channels.py:356` |
| `channel.updated` (Channel updated) | A channel is edited | `name`, `type` | Actor; channel name | `backend/open_webui/routers/channels.py:736` |
| `channel.deleted` (Channel deleted) | A channel is deleted | `name`, `type` | Actor; channel name | `backend/open_webui/routers/channels.py:772` |
| `channel.member_added` (Channel member added) | Members or groups are added | `user_ids`, `group_ids` | Actor; member ids | `backend/open_webui/routers/channels.py:649` |
| `channel.member_removed` (Channel member removed) | Members are removed | `user_ids` | Actor; member ids | `backend/open_webui/routers/channels.py:691` |
| `channel.member_active_updated` (Channel member active updated) | A member's active state changes, including reopening an existing direct message | `is_active` | Actor | `backend/open_webui/routers/channels.py:335`, `:608` |
| `channel.message` (Channel message) | Once **per member who is offline** when a post is made, only while **User Webhooks** is on (section 5.10) | `user_id` (the recipient), `channel_id`, `message_id`, `sender_id`, `content`, `message`, `content_preview`, `title` (channel name), `url` | **no actor**; **the message text** (first 1,000 characters), channel name, sender and recipient ids | `backend/open_webui/routers/channels.py:954` |
| `channel.webhook.created` (Channel Webhook created) | An incoming webhook is added to a channel | `channel_id`, `name` | Actor | `backend/open_webui/routers/channels.py:1917` |
| `channel.webhook.updated` (Channel Webhook updated) | An incoming webhook is changed | `channel_id`, `name` | Actor | `backend/open_webui/routers/channels.py:1953` |
| `channel.webhook.deleted` (Channel Webhook deleted) | An incoming webhook is removed | `channel_id` | Actor | `backend/open_webui/routers/channels.py:1986` |

Channel incoming webhooks (other systems posting **into** a channel) are a separate feature,
documented in `channels-and-direct-messages.md`.

#### 9.2.5 File, Folder, Note and Memory Events

| Event (short message) | Published when | `data` fields | Personal or content data | Source |
|---|---|---|---|---|
| `file.uploaded` (File uploaded) | A file is uploaded | `filename`, `content_type` | Actor; **file name** | `backend/open_webui/routers/files.py:314` |
| `file.content_updated` (File content updated) | A file's extracted text is edited | `content_preview` | Actor; first 300 characters of the text | `backend/open_webui/routers/files.py:775` |
| `file.renamed` (File renamed) | A file is renamed | `filename` | Actor; file name | `backend/open_webui/routers/files.py:988` |
| `file.deleted` (File deleted) | A file is deleted | `filename` | Actor; file name | `backend/open_webui/routers/files.py:1051` |
| `file.deleted_all` (File deleted all) | All files are deleted | none | Actor | `backend/open_webui/routers/files.py:591` |
| `folder.created` (Folder created) | A folder is created | `name`, `parent_id`, `owner_id` | Actor; folder name | `backend/open_webui/routers/folders.py:190`, `:217` |
| `folder.updated` (Folder updated) | A folder is renamed | `name` | Actor; folder name | `backend/open_webui/routers/folders.py:376` |
| `folder.parent_updated` (Folder parent updated) | A folder is moved | `parent_id` | Actor | `backend/open_webui/routers/folders.py:433` |
| `folder.access_updated` (Folder access updated) | A folder's sharing changes | `grant_count` | Actor | `backend/open_webui/routers/folders.py:544` |
| `folder.deleted` (Folder deleted) | A folder is deleted | `folder_ids`, `delete_contents` | Actor | `backend/open_webui/routers/folders.py:728` |
| `note.created` (Note created) | A note is created | `title` | Actor; **note title** | `backend/open_webui/routers/notes.py:232` |
| `note.updated` (Note updated) | A note is saved, including edits made by the assistant's note tools | `title` | Actor; note title | `backend/open_webui/routers/notes.py:584`; `backend/open_webui/tools/builtin.py:96` |
| `note.access_updated` (Note access updated) | A note's sharing changes | none | Actor | `backend/open_webui/routers/notes.py:651` |
| `note.pinned`, `note.unpinned` (Note pinned, Note unpinned) | Pin toggled | none | Actor | `backend/open_webui/routers/notes.py:699` |
| `note.deleted` (Note deleted) | A note is deleted | none | Actor | `backend/open_webui/routers/notes.py:747` |
| `memory.created` (Memory created) | A memory is added, singly or in a batch | `content_preview`, `type`, `path`; batch adds `operation` | Actor; **first 300 characters of the memory** | `backend/open_webui/routers/memories.py:224`, `:306` |
| `memory.updated` (Memory updated) | A memory is changed, singly or in a batch | as above | Actor; first 300 characters of the memory | `backend/open_webui/routers/memories.py:595`, `:306` |
| `memory.deleted` (Memory deleted) | One memory, a batch item, or all of a user's memories are deleted | none; batch as above | Actor; batch items carry the text preview | `backend/open_webui/routers/memories.py:623`, `:531`, `:306` |
| `memory.reset` (Memory reset) | Memories are re-indexed (one user, or everyone's) | `count`, `reindex`; `user_count` | Actor | `backend/open_webui/routers/memories.py:500`, `:472` |

#### 9.2.6 Knowledge and Retrieval Events

| Event (short message) | Published when | `data` fields | Personal or content data | Source |
|---|---|---|---|---|
| `knowledge.created` (Knowledge created) | A knowledge base is created | `name` | Actor; knowledge base name | `backend/open_webui/routers/knowledge.py:354` |
| `knowledge.updated` (Knowledge updated) | A knowledge base is edited | `name` | Actor; name | `backend/open_webui/routers/knowledge.py:1200` |
| `knowledge.deleted` (Knowledge deleted) | A knowledge base is deleted | `name` | Actor; name | `backend/open_webui/routers/knowledge.py:1777` |
| `knowledge.reset` (Knowledge reset) | A knowledge base is emptied | `include_directories` | Actor | `backend/open_webui/routers/knowledge.py:1839` |
| `knowledge.reindexed` (Knowledge reindexed) | All knowledge files are re-indexed | `count` | Actor | `backend/open_webui/routers/knowledge.py:454` |
| `knowledge.access_updated` (Knowledge access updated) | Sharing changes | `name` | Actor; name | `backend/open_webui/routers/knowledge.py:1269` |
| `knowledge.file.added` (Knowledge File added) | A file is added to a knowledge base | `knowledge_id`, `directory_id` | Actor | `backend/open_webui/routers/knowledge.py:1509` |
| `knowledge.file.updated` (Knowledge File updated) | A knowledge file is updated | `knowledge_id` | Actor | `backend/open_webui/routers/knowledge.py:1593` |
| `knowledge.file.removed` (Knowledge File removed) | A file is removed | `knowledge_id`, `delete_file` | Actor | `backend/open_webui/routers/knowledge.py:1682` |
| `knowledge.file.moved` (Knowledge File moved) | A file is moved between directories | `knowledge_id`, `directory_id` | Actor | `backend/open_webui/routers/knowledge.py:2406` |
| `knowledge.directory.created` (Knowledge Directory created) | A directory is created | `knowledge_id`, `name`, `parent_id` | Actor; directory name | `backend/open_webui/routers/knowledge.py:2277` |
| `knowledge.directory.updated` (Knowledge Directory updated) | A directory is renamed or moved | `knowledge_id`, `name`, `parent_id` | Actor; directory name | `backend/open_webui/routers/knowledge.py:2314` |
| `knowledge.directory.deleted` (Knowledge Directory deleted) | A directory is deleted | `knowledge_id`, `move_files` | Actor | `backend/open_webui/routers/knowledge.py:2366` |
| `knowledge.external_connection.created` (Knowledge External Connection created) | An external knowledge connection is added | `name`, `provider` | Actor | `backend/open_webui/routers/knowledge.py:708` |
| `knowledge.external_connection.updated` (Knowledge External Connection updated) | It is changed | `name`, `provider` | Actor | `backend/open_webui/routers/knowledge.py:745` |
| `knowledge.external_connection.deleted` (Knowledge External Connection deleted) | It is removed | `name`, `provider` | Actor | `backend/open_webui/routers/knowledge.py:774` |
| `retrieval.content.processed` (Retrieval Content processed) | A file, a pasted text or a batch of files was processed for retrieval | `collection_name`, `filename`; for text `name`, `content_preview`; for a batch `count`, `errors` | Actor; file name; first 300 characters of pasted text | `backend/open_webui/routers/retrieval.py:2074`, `:2136`, `:2225`, `:3448` |
| `retrieval.content.process_failed` (Retrieval Content process failed) | Processing a file failed (also a personal notification event) | `collection_name`, `filename`, `message` (`{filename}: {error}`) | Actor; file name; error text | `backend/open_webui/routers/retrieval.py:2167` |
| `retrieval.collection.deleted` (Retrieval Collection deleted) | Entries are removed from a collection | `file_id` | Actor | `backend/open_webui/routers/retrieval.py:3252` |
| `retrieval.vector_db.reset` (Retrieval Vector Db reset) | An administrator resets the vector database | none | Actor | `backend/open_webui/routers/retrieval.py:3279` |
| `retrieval.uploads.reset` (Retrieval Uploads reset) | An administrator empties the upload folder | none | Actor | `backend/open_webui/routers/retrieval.py:3310` |

#### 9.2.7 Model, Function, Tool, Skill, Prompt and Pipeline Events

| Event (short message) | Published when | `data` fields | Personal or content data | Source |
|---|---|---|---|---|
| `model.created` (Model created) | A workspace model is created | `name` | Actor | `backend/open_webui/routers/models.py:362` |
| `model.imported` (Model imported) | Models are imported | `count`, `model_ids` | Actor | `backend/open_webui/routers/models.py:657` |
| `model.synced` (Model synced) | Models are synced | `count`, `model_ids` | Actor | `backend/open_webui/routers/models.py:701` |
| `model.updated` (Model updated) | A model is edited | `name` | Actor | `backend/open_webui/routers/models.py:1014` |
| `model.deleted` (Model deleted) | One model, or all models, deleted | `name` | Actor | `backend/open_webui/routers/models.py:1143`, `:1159` |
| `model.enabled`, `model.disabled` (Model enabled, Model disabled) | A model is switched on or off | `name` | Actor | `backend/open_webui/routers/models.py:901` |
| `model.access_updated` (Model access updated) | A model's access changes | none | Actor | `backend/open_webui/routers/models.py:1097` |
| `model.provider_config.updated` (Model Provider Config updated) | The OpenAI or Ollama connection settings are saved | `provider`, `enabled`, `base_url_count` | Actor | `backend/open_webui/routers/openai.py:579`; `backend/open_webui/routers/ollama.py:336` |
| `model.provider_request.failed` (Model provider request failed) | A request to an AI provider returned an HTTP error (chat, embeddings, responses, token counting, the Anthropic-compatible route, the proxy, Ollama requests). The server also writes a log line | `error_type` (`model_not_found`, `authentication_failed`, `rate_limited`, `server_failed`, `upstream_error`), `status`, `provider`, `base_url`, `requested_model`, a masked key hint, `upstream_error_code`, `upstream_message` | Actor; the provider address; the provider's error text | `backend/open_webui/events.py:1205-1273`; callers `backend/open_webui/routers/openai.py:518`, `:1684`, `:1696`, `:1725`, `:1836`, `:1964`, `:2086`; `backend/open_webui/routers/ollama.py:143`, `:157`; `backend/open_webui/main.py:1977` |
| `model.provider_model.created` (Provider model created) | A provider model is copied (Ollama) or downloaded | `provider`, `source` or `url_idx`, `base_url` | Actor | `backend/open_webui/routers/ollama.py:788`; `backend/open_webui/routers/openai.py:967` |
| `model.provider_model.deleted` (Provider model deleted) | A provider model is deleted | `provider`, `url_idx`, `base_url` | Actor | `backend/open_webui/routers/ollama.py:831`; `backend/open_webui/routers/openai.py:1049` |
| `function.created` (Function created) | A function is installed | `type`, `name` | Actor | `backend/open_webui/routers/functions.py:237` |
| `function.updated` (Function updated) | A function is edited, or its global switch toggled | `type`, `name`; `is_global` | Actor | `backend/open_webui/routers/functions.py:404`, `:354` |
| `function.deleted` (Function deleted) | A function is deleted | none | Actor | `backend/open_webui/routers/functions.py:446` |
| `function.enabled`, `function.disabled` (Function enabled, Function disabled) | After the on/off switch is saved | `type`, `name` | Actor | `backend/open_webui/routers/functions.py:316` |
| `function.enable_started`, `function.disable_started` (Function enable started, Function disable started) | Before the switch is saved; delivered to Event functions inside the request, then to admin webhooks; not to personal targets | `type`, `name` | Actor | `backend/open_webui/routers/functions.py:297-311` |
| `function.valves_updated` (Function valves updated) | A function's admin valves, or a user's own valves (`scope` `user`), are saved; valve values are not included | `scope` | Actor | `backend/open_webui/routers/functions.py:538`, `:645` |
| `tool.created` (Tool created) | A workspace tool is created | `name` | Actor | `backend/open_webui/routers/tools.py:402` |
| `tool.updated` (Tool updated) | It is edited | `name` | Actor | `backend/open_webui/routers/tools.py:556` |
| `tool.deleted` (Tool deleted) | It is deleted | `name` | Actor | `backend/open_webui/routers/tools.py:681` |
| `tool.access_updated` (Tool access updated) | Its access changes | `name` | Actor | `backend/open_webui/routers/tools.py:630` |
| `tool.valves_updated` (Tool valves updated) | Admin or user valves saved; values not included | `scope` | Actor | `backend/open_webui/routers/tools.py:830`, `:969` |
| `skill.created` (Skill created) | A skill is created | `name` | Actor | `backend/open_webui/routers/skills.py:199` |
| `skill.updated` (Skill updated) | A skill is edited, or its access changes | `name`; `access_updated` | Actor | `backend/open_webui/routers/skills.py:326`, `:399` |
| `skill.deleted` (Skill deleted) | A skill is deleted | `name` | Actor | `backend/open_webui/routers/skills.py:499` |
| `skill.enabled`, `skill.disabled` (Skill enabled, Skill disabled) | A skill is switched on or off | `name` | Actor | `backend/open_webui/routers/skills.py:437` |
| `prompt.created` (Prompt created) | A prompt is created | `name`, `command` | Actor | `backend/open_webui/routers/prompts.py:182` |
| `prompt.updated` (Prompt updated) | A prompt or its details are edited | `name`, `command` | Actor | `backend/open_webui/routers/prompts.py:303`, `:369` |
| `prompt.deleted` (Prompt deleted) | A prompt is deleted | `name`, `command` | Actor | `backend/open_webui/routers/prompts.py:584` |
| `prompt.enabled`, `prompt.disabled` (Prompt enabled, Prompt disabled) | A prompt is switched on or off | `name`, `command` | Actor | `backend/open_webui/routers/prompts.py:531` |
| `prompt.version_updated` (Prompt version updated) | The live version of a prompt is changed | `version_id` | Actor | `backend/open_webui/routers/prompts.py:417` |
| `prompt.access_updated` (Prompt access updated) | Sharing changes | `name` | Actor | `backend/open_webui/routers/prompts.py:483` |
| `pipeline.uploaded` (Pipeline uploaded) | A pipeline file is uploaded to a Pipelines server | `url_idx`, `filename` | Actor | `backend/open_webui/routers/pipelines.py:278` |
| `pipeline.added` (Pipeline added) | A pipeline is added from an address | `url_idx`, `url` | Actor | `backend/open_webui/routers/pipelines.py:334` |
| `pipeline.deleted` (Pipeline deleted) | A pipeline is deleted | `url_idx` | Actor | `backend/open_webui/routers/pipelines.py:384` |
| `pipeline.valves_updated` (Pipeline valves updated) | Published when an administrator **reads** a pipeline's valves; saving the valves publishes nothing | `url_idx` | Actor | `backend/open_webui/routers/pipelines.py:446-472`, `:533-555` |

#### 9.2.8 Calendar, Automation, Feedback, Media and Terminal Events

| Event (short message) | Published when | `data` fields | Personal or content data | Source |
|---|---|---|---|---|
| `calendar.created` (Calendar created) | A calendar is created | `name` | Actor | `backend/open_webui/routers/calendar.py:128` |
| `calendar.updated` (Calendar updated) | It is edited | `name` | Actor | `backend/open_webui/routers/calendar.py:431` |
| `calendar.deleted` (Calendar deleted) | It is deleted | `name` | Actor | `backend/open_webui/routers/calendar.py:462` |
| `calendar.default_updated` (Calendar default updated) | The default calendar changes | `name` | Actor | `backend/open_webui/routers/calendar.py:478` |
| `calendar.event.created` (Calendar Event created) | An event is created | `calendar_id`, `title` | Actor; **event title** | `backend/open_webui/routers/calendar.py:280` |
| `calendar.event.updated` (Calendar Event updated) | An event is edited | `calendar_id`, `title` | Actor; event title | `backend/open_webui/routers/calendar.py:337` |
| `calendar.event.deleted` (Calendar Event deleted) | An event is deleted | `calendar_id`, `title` | Actor; event title | `backend/open_webui/routers/calendar.py:359` |
| `calendar.event.rsvp_updated` (Calendar Event rsvp updated) | An invitee answers | `status` | Actor | `backend/open_webui/routers/calendar.py:381` |
| `calendar.alert` (Calendar alert) | The scheduler sends a reminder (section 5.11); also a personal notification event | `event_id`, `title`, `description`, `start_at`, `minutes_until`, `calendar_id`, `location`, `user_id`, `starts_in`, `message` | **no actor**; **event title, description and location** | `backend/open_webui/utils/automations.py:599` |
| `automation.created` (Automation created) | An automation is created | `name`, `is_active`, `folder_id` | Actor; automation name | `backend/open_webui/routers/automations.py:231` |
| `automation.updated` (Automation updated) | It is edited | `name`, `is_active`, `folder_id` | Actor | `backend/open_webui/routers/automations.py:291` |
| `automation.enabled`, `automation.disabled` (Automation enabled, Automation disabled) | It is switched on or off | `name` | Actor | `backend/open_webui/routers/automations.py:318` |
| `automation.deleted` (Automation deleted) | It is deleted | `name` | Actor | `backend/open_webui/routers/automations.py:373` |
| `automation.run_started` (Automation run started) | Only when someone selects **Run now**; scheduled runs do not publish it | `name` | Actor | `backend/open_webui/routers/automations.py:345` |
| `automation.run_completed` (Automation run completed) | A run finished (chat or channel) | `name`, `chat_id` or `channel_id` and `message_id` | Actor | `backend/open_webui/utils/automations.py:336`, `:512` |
| `automation.run_failed` (Automation run failed) | A run failed; two of the four call sites have **no actor** (the owner was not found, or the run hit an unexpected error caught by the outer handler) | `name`, `error` | Actor where present; error text | `backend/open_webui/utils/automations.py:356`, `:373`, `:451`, `:524` |
| `feedback.created` (Feedback created) | A user rates a reply | `rating` | Actor | `backend/open_webui/routers/evaluations.py:439` |
| `feedback.updated` (Feedback updated) | A rating is changed | `rating` | Actor | `backend/open_webui/routers/evaluations.py:478` |
| `feedback.deleted` (Feedback deleted) | A rating is deleted | none | Actor | `backend/open_webui/routers/evaluations.py:503` |
| `feedback.deleted_all` (Feedback deleted all) | An administrator deletes all feedback, or a user deletes their own | none | Actor | `backend/open_webui/routers/evaluations.py:345`, `:389` |
| `image.generated` (Image generated) | An image is generated | `model`, `size`, `n`, `prompt_preview` | Actor; **first 300 characters of the image prompt** | `backend/open_webui/routers/images.py:580` |
| `image.edited` (Image edited) | An image is edited | `model`, `size`, `n`, `prompt_preview` | Actor; first 300 characters of the prompt | `backend/open_webui/routers/images.py:880` |
| `audio.speech_requested` (Speech requested) | Text-to-speech is requested (also when answered from the cache) | `engine`, `cached`; for new audio also `model`, `input_preview` | Actor; first 300 characters of the text read aloud | `backend/open_webui/routers/audio.py:631`, `:655` |
| `audio.transcription_requested` (Transcription requested) | Speech-to-text is requested | `filename`, `content_type`, `language` | Actor; file name | `backend/open_webui/routers/audio.py:1307` |
| `terminal.session.opened` (Terminal Session opened) | A terminal session opens | `server_id` | Actor | `backend/open_webui/routers/terminals.py:391` |
| `terminal.session.closed` (Terminal Session closed) | It closes | `server_id` | Actor | `backend/open_webui/routers/terminals.py:460` |
| `notification.test` (Notification test) | **Never published in v0.11.4**: defined only; the personal **Send Test** does not use it | — | — | `backend/open_webui/events.py:656-658` |
| `notification.manual` (Notification sent) | **Never published in v0.11.4**: defined only; the `notify` tool does not use it | — | — | `backend/open_webui/events.py:659-661` |

The catalogue entries `notification.test` and `notification.manual` appear in the admin event list
and can be chosen as filters, but no code publishes them (a search of `backend/open_webui` for
`NOTIFICATION_TEST`, `NOTIFICATION_MANUAL` and the two names finds only their definitions).

### 9.3 What an Admin Webhook Receives

For each matching webhook the server builds a short text and posts it in the format the address
suggests (`backend/open_webui/events.py:1034-1059`; `backend/open_webui/utils/webhook.py:18-101`).

The short text is the event's own message (for example "User logged in"; for `chat.finished` the
chat title, for `channel.message` the channel name, for `calendar.alert` the event title) followed
by the subject id in brackets, then the catalogue description, then `Event: {event name}`. A
fictional example for a sign-in:

```
User logged in ({user id})
A user successfully logged in.
Event: auth.login
```

| The address contains | Format sent | What it contains | Source |
|---|---|---|---|
| `https://hooks.slack.com` or `https://chat.googleapis.com` | `{"text": ...}` | The short text only | `backend/open_webui/utils/webhook.py:43-45` |
| `https://discord.com/api/webhooks` | `{"content": ...}` | The short text, cut to 2,000 characters with `... (truncated)` at the end when longer | `backend/open_webui/utils/webhook.py:46-49` |
| `webhook.office.com` (Microsoft Teams connector) | A legacy Teams "MessageCard" | Title: the short message; subtitle "MedIT GPT (0.11.4) - undefined" (the app name, version and an `action` field that events do not have); the upstream Open WebUI logo; the description; and "facts": description, event name and every field of the actor block (id, **name**, **email**, role, times, type) | `backend/open_webui/utils/webhook.py:50-81`; `backend/open_webui/env.py:957` |
| Anything else | The whole event envelope as JSON (section 4) | Everything, including the actor's name and email and every `data` field | `backend/open_webui/utils/webhook.py:82-84`; `backend/open_webui/events.py:925-944` |

A fictional generic JSON example for `chat.finished` (values invented, ids shown as placeholders):

```json
{
  "schema": "0.11.4",
  "id": "{event id}",
  "event": "chat.finished",
  "resource": "chat",
  "operation": "finished",
  "created_at": 1791590400,
  "instance_id": "{instance id}",
  "version": "0.11.4",
  "source": "api",
  "actor": {"id": "{user id}", "name": "Jane Doe", "email": "jane.doe@example.com",
            "role": "user", "created_at": 1780000000, "updated_at": 1790000000, "type": "user"},
  "subject": {"type": "chat", "id": "{chat id}"},
  "data": {"user_id": "{user id}", "chat_id": "{chat id}", "message_id": "{message id}",
           "model_id": "{model id}", "title": "Conference Abstract Ideas",
           "url": "{WebUI URL}/c/{chat id}", "message": "{first 1,000 characters of the reply}"},
  "message": "Conference Abstract Ideas"
}
```

Format detection only looks for those text fragments in the address. A Teams address of another
form (for example a Power Automate workflow address) gets the generic JSON envelope, which Teams
may not display as a message; whether MedIT GPT's Teams tenant still issues `webhook.office.com`
addresses is **TO BE CONFIRMED** (section 14).

### 9.4 What a Personal Notification Target Receives

Personal targets use the same format detection, with message text built per event
(`backend/open_webui/utils/notifications.py:246-343`, `:393-417`):

| Event | Text in Slack, Google Chat, Discord and the Teams card | Teams subtitle action | Generic JSON body | Source |
|---|---|---|---|---|
| `chat.finished` | `**{chat title}**`, then the reply text, then the chat link | `chat` | `{"action": "chat", "message": "{reply}", "title": "{chat title}", "url": "{link}"}` | `backend/open_webui/utils/notifications.py:267-285` |
| `chat.failed` | `**Chat failed**`, then the error text, then the chat link | `chat_failed` | `{"action": "chat_failed", "message": "{error}", "title": "Chat failed", "url": "{link}"}` | `backend/open_webui/utils/notifications.py:287-305` |
| `channel.message` | `**#{channel name}**`, then the message text, then the channel link | `channel` | `{"action": "channel", "message": "{text}", "title": "{channel name}", "url": "{link}"}` | `backend/open_webui/utils/notifications.py:307-322` |
| `calendar.alert` | `**{event title}**` and `starting in {minutes} min` (or `starting now`) | `calendar_alert` | `{"action": "calendar_alert", "title": "{event title}", "minutes_until": {n}, "event_id": "{id}"}` | `backend/open_webui/utils/notifications.py:324-338`; `backend/open_webui/utils/automations.py:598` |
| `retrieval.content.process_failed` | `Retrieval Content process failed`, then `{file name}: {error}`, then `Event: retrieval.content.process_failed` | `undefined` | The whole event envelope, including the actor's name and email (a Teams card also lists the actor's fields) | `backend/open_webui/utils/notifications.py:340-343`; `backend/open_webui/utils/webhook.py:52-60` |
| **Send Test** | `Test notification`, then `This is a test notification from {app_name}.` ("This is a test notification from MedIT GPT." with the default name) | `test` | `{"action": "test", "user_id": "{user id}"}` (the text is not in the JSON) | `backend/open_webui/utils/notifications.py:349-364` |
| `notify` tool | The title (or `Notification`), then the model's message | `notify` | `{"action": "notify", "user_id": "{user id}", "message": "{text}", "title": "{title}"}` | `backend/open_webui/utils/notifications.py:370-390` |

**The chat link drops `/c/`.** For `chat.finished` and `chat.failed`, a link that ends in
`/c/{chat id}` is rewritten to end in `/{chat id}` (`backend/open_webui/utils/notifications.py:271-273`,
`:291-293`). The front end has no route for a bare chat id (the chat route is
`src/routes/(app)/c/[id]`), so following that link appears to open the generic error page, which
shows the status and message (`src/routes/+error.svelte:8`), rather than the chat. This is read
from the code and has not been tried; see section 14. Admin webhooks keep the original `/c/` link
in the JSON `data.url` (`backend/open_webui/utils/middleware.py:227`).

When **WebUI URL** is empty, links are relative (`/c/{chat id}`, `/channels/{channel id}`), with
no host name, so they do not lead back to MedIT GPT from a chat service (`backend/open_webui/utils/middleware.py:227`;
`backend/open_webui/routers/channels.py:949`).

### 9.5 In-App Toasts and Browser Notifications

| Trigger | Toast title | Toast text | Toast stays | Browser notification | Source |
|---|---|---|---|---|---|
| A reply finished in a chat not on screen, or while the tab is hidden | The chat title, or **New Chat** | Plain-text preview of the reply | 15 seconds; click opens the chat | "{chat title} / MedIT GPT", body the preview, icon the site favicon | `src/routes/+layout.svelte:735-781` |
| A channel message from someone else, while that channel is not on screen or the tab is hidden | "{sender name} (#{channel name})", or the sender's name for a direct message | The message text | 15 seconds; click opens the channel or thread | "{same title} / MedIT GPT", body the text, icon the sender's profile picture | `src/routes/+layout.svelte:827-893` |
| A calendar reminder | The event title | **Starting now**, **Starting in 1 minute** or **Starting in {count} minutes** | 30 seconds; click opens `/calendar` | "{event title} / MedIT GPT", body the same text, icon the site favicon | `src/routes/+layout.svelte:600-632` |
| A tool or function sends a `notification` item in the open chat | — | The item's text, coloured by level | The toast library's default | none | `src/lib/components/chat/Chat.svelte:1354-1366` |
| Live connection lost and regained | — | `Connection lost. Reconnecting...`, then `Reconnected` | Default | none | `src/routes/+layout.svelte:162`, `:194` |

The notification card shows the site favicon (`/static/favicon.png`, replaced by U of T artwork in
this fork) beside the title, can be closed with its **×** (**Dismiss notification**) and plays the
sound described in section 5.9 (`src/lib/components/NotificationToast.svelte:103-127`). The
connection toasts are listed for completeness; their behaviour belongs to the socket connection
and is not analysed further here.

### 9.6 Privacy: What Leaves the Platform

Webhook messages go to systems outside MedIT GPT, chosen by whoever typed the address. Treat every
admin webhook and personal target as a disclosure of personal data:

- **Names and email addresses.** Every event with an actor carries the actor's name and email in
  generic JSON and in Teams cards (section 9.3). Chat-format messages (Slack, Google Chat, Discord)
  carry only the short text and ids.
- **Conversation content.** With **All events** in generic JSON, an admin webhook receives the
  first 300 characters of every message people send in saved chats (`message.created`), the first
  1,000 characters of every finished reply (`chat.finished`), image prompts, text sent to
  text-to-speech, memories, file names, note and chat titles and channel messages (section 9.2).
  MedIT GPT chats may contain health information.
- **Personal targets** send the user's own reply text, channel messages from other people, and
  calendar details to an address the user chose (section 9.4).
- **What is removed.** Credential-like fields are dropped and long text is cut (section 4), but
  nothing else is filtered: there is no setting to exclude message text from payloads
  (`backend/open_webui/events.py:947-971`).
- **Where to look.** The admin webhook list in Admin › Settings › General shows each webhook's host
  and filters; the **Notification Targets** list shows a person only their own targets, with the
  address masked (`src/lib/components/admin/Settings/Events.svelte:719-731`;
  `backend/open_webui/routers/notifications.py:50-53`;
  `backend/open_webui/utils/notifications.py:81-94`). No screen lists all users' personal targets;
  they are stored inside each user's settings record (section 6.3).

Whether sending MedIT GPT data to any outside service is approved, and which services, is an
organizational decision: **TO BE CONFIRMED** with the platform maintainer and the U of T Privacy
Office.

## 10. Error, Warning and Notice Messages (Verbatim)

Plain i18n keys display as written (their `en-US` values are empty, so the key is the text);
dotted keys are resolved from `src/lib/i18n/locales/en-US/translation.json`. `{name}` marks a
value filled in at run time.

### 10.1 Admin Events Panel (Admin › Settings › General)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Webhook saved` | Success toast | `src/lib/components/admin/Settings/Events.svelte:355` | An admin webhook was created or edited | none | none |
| `Failed to save webhook` | Error toast | `src/lib/components/admin/Settings/Events.svelte:357` | The server refused the save. The real reason (a rejected address or an unknown event name, section 10.2) is not shown, because the admin request helper passes the whole error object | Check the address is a public `https://` address and the filters are valid names or `prefix.*` patterns, then save again | Escalate with the time; the reason is in the browser's network response, not in the server log |
| `Webhook deleted` | Success toast | `src/lib/components/admin/Settings/Events.svelte:370` | A webhook was deleted | none | none |
| `Failed to delete webhook` | Error toast | `src/lib/components/admin/Settings/Events.svelte:372` | Deletion refused, for example the webhook was already deleted in another tab (`Webhook not found`) | Reload the page | none |
| `Failed to update webhook` | Error toast | `src/lib/components/admin/Settings/Events.svelte:386` | The row's on/off switch could not be saved; the switch flips back | Reload and retry | Escalate if repeated |
| `Use a valid event name or pattern like user.*` | Error toast | `src/lib/components/admin/Settings/Events.svelte:228` | **Add** was used with text that is not `*`, a catalogue name or a `prefix.*` that matches catalogue names | Pick from the list or fix the pattern | none |
| `Are you sure you want to delete this webhook? This action cannot be undone.` | Confirmation | `src/lib/components/admin/Settings/Events.svelte:685` | **Delete** in **Edit webhook** | Confirm or cancel | none |
| `No event webhooks configured.` | Empty state | `src/lib/components/admin/Settings/Events.svelte:760` | No admin webhooks exist | none | none |
| `Receives matching events across the instance, including system/config events and events associated with any user.` | Help text | `src/lib/components/admin/Settings/Events.svelte:467-469` | **Send events for** is **All users and system events** | none | none |
| `Receives matching events that are not associated with a user.` | Help text | `src/lib/components/admin/Settings/Events.svelte:471` | **System events only** | none | Section 5.2: admin settings changes are user-associated |
| `Receives matching user-associated events only when the actor, user subject, or user data matches these users or current group members. System/config events are not sent.` | Help text | `src/lib/components/admin/Settings/Events.svelte:473-475` | **Specific users or groups** | none | none |
| `Event names may change as Open WebUI evolves. Use broad patterns like user.* for integrations that should continue across new related events.` | Help text | `src/lib/components/admin/Settings/Events.svelte:648-650` | **All events** unticked | none | none |
| `Send product events as JSON to external services. Chat destinations receive readable messages.` | Description | `src/lib/components/admin/Settings/Events.svelte:704`; `src/lib/i18n/locales/en-US/translation.json:2381` | Under **Webhooks** | none | none |
| `All events` / `{count} filters` / `All users and system events` / `System events only` / `1 user` / `{count} users` / `1 group` / `{count} groups` | List summary | `src/lib/components/admin/Settings/Events.svelte:144-178` | The row text after the host | none | none |
| `Not configured` | List summary | `src/lib/components/admin/Settings/Events.svelte:180-186` | A webhook's address cannot be read as a URL | Edit the webhook | none |
| `Default webhook` | Label | `src/lib/components/admin/Settings/Events.svelte:726` | The migrated legacy webhook | none | Section 5.4 |
| `Add webhook` / `Edit webhook` / `Name` / `Identity audit` / `URL` / `Send events for` / `Specific users or groups` / `Search users or groups` / `Search or add pattern` / `Add` / `Configure` / `Enabled` / `Disabled` / `Delete` / `Save` / `Remove` / `Group` / `User` / `group` / `user` / `Close` | Labels, placeholders and tooltips | `src/lib/components/admin/Settings/Events.svelte:400-622`, `:666-675`, `:707`, `:735`, `:745` | The panel and its window | none | none |
| `Events` / `Webhooks` | Labels | `src/lib/components/admin/Settings/Events.svelte:568`, `:694`, `:701`; `src/lib/i18n/locales/en-US/translation.json:2380`, `:2382` | Block and field headings | none | none |

### 10.2 Admin Webhook Server Responses

These reach only the browser's network response; the admin screen shows the generic toasts above.

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `The URL you provided is invalid. Please double-check and try again.` | HTTP 400 | `backend/open_webui/constants.py:99`; raised by `backend/open_webui/retrieval/web/utils.py:131-167` from `backend/open_webui/events.py:884-885` | The address is not a valid public `http` or `https` address, or its host does not resolve | Use the receiving service's public address | Escalate; for internal receivers see section 14 |
| `Invalid event pattern: {event_filter}` | HTTP 400 | `backend/open_webui/events.py:721` | A `prefix.*` whose prefix matches no catalogue event | Fix the filter | none |
| `Invalid event: {event_filter}` | HTTP 400 | `backend/open_webui/events.py:723` | An exact name not in the catalogue | Fix the filter | Compare with `GET /api/events` |
| `Invalid targets` / `Invalid target` | HTTP 400 | `backend/open_webui/events.py:743`, `:749`, `:754` | Malformed scope (not from the normal screen) | none | Escalate |
| `Webhook not found` | HTTP 404 | `backend/open_webui/main.py:2540`, `:2573` | Editing or deleting a webhook id that no longer exists | Reload | none |

### 10.3 Personal Notifications Panel (Settings › Notifications)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Response notifications cannot be activated as the website permissions have been denied. Please visit your browser settings to grant the necessary access.` | Error toast | `src/lib/components/chat/Settings/Notifications.svelte:68-72` | **Browser Notifications** switched on but the browser refused permission (or does not support notifications) | Allow notifications for the site in the browser's settings, then switch on again | Browser and operating-system notification settings; section 11.1 |
| `Settings saved successfully!` | Success toast | `src/lib/components/chat/Settings/Notifications.svelte:159` | A target was added or edited | none | none |
| `Test notification sent.` | Success toast | `src/lib/components/chat/Settings/Notifications.svelte:179` | **Send Test** delivered (the receiver answered without an HTTP error) | Check the receiving app | If nothing arrived, section 11.3 |
| `{server message}` | Error toast | `src/lib/components/chat/Settings/Notifications.svelte:99`, `:102`, `:161`, `:172`, `:181` | Any refusal from the server (section 10.4) is shown as its text | Depends on the text | Section 10.4 |
| `Allow browser notifications for completed responses.` | Help text | `src/lib/components/chat/Settings/Notifications.svelte:208-210` | Under **Browser Notifications** | none | none |
| `No notification targets configured.` | Empty state | `src/lib/components/chat/Settings/Notifications.svelte:244-246` | No targets yet | Add one | none |
| `No chat alerts` | Row text | `src/lib/components/chat/Settings/Notifications.svelte:277` | The target lists no automatic events (it serves only the `notify` tool) | Edit and pick events | none |
| `Only when away` / `Always` | Row text and buttons | `src/lib/components/chat/Settings/Notifications.svelte:279-281`, `:409` | Delivery mode | none | Section 4 (away) |
| `The notify tool always sends to an enabled target, regardless of automatic event settings.` | Help text | `src/lib/components/chat/Settings/Notifications.svelte:415-419` | In the target window | none | none |
| `Notifications` / `Browser Notifications` / `Notification Sound` / `Notification Targets` / `Add Notification Target` | Labels | `src/lib/components/chat/Settings/Notifications.svelte:194`, `:200`, `:214`, `:228`, `:234`, `:349`; `src/lib/i18n/locales/en-US/translation.json:2995-2999` | Headings and switches | none | none |
| `Loading...` / `Webhook` / `Default` / `Send Test` / `Make Default` / `Edit` / `Remove` / `Enabled` / `Target ID for notify` / `Target ID` / `Keep current webhook URL` / `Automatic Events` / `Automatic Delivery` / `Cancel` / `Saving...` / `Save` | Labels, placeholders and states | `src/lib/components/chat/Settings/Notifications.svelte:242-435` | The panel and its window | none | none |
| `Chat finished` / `A chat run finished successfully.` / `Chat failed` / `A chat run failed.` | Fallback event labels | `src/lib/components/chat/Settings/Notifications.svelte:29-40` | Shown only if the server's event list could not be loaded; the descriptions are not displayed | none | none |
| `Chat finished` / `Chat failed` / `Channel message` / `Calendar alert` / `Retrieval Content process failed` | Event buttons (from the server, English only) | `backend/open_webui/utils/notifications.py:223-231`; `backend/open_webui/events.py:164-169`, `:267-271`, `:414-418`, `:595-599` | **Automatic Events** in the target window | none | none |

### 10.4 Personal Notification Server Responses

The personal-target screen shows these texts in its error toast
(`src/lib/apis/notifications/index.ts:40-48`), except after **Remove** and **Make Default**, whose
buttons have no error handling, so a refusal there shows nothing
(`src/lib/components/chat/Settings/Notifications.svelte:296-322`).

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `We could not find what you're looking for :/` | HTTP 404 | `backend/open_webui/routers/notifications.py:35-36`, `:79-80`; `backend/open_webui/constants.py:78` | **User Webhooks** is off for the instance (every notifications route), or the target to remove does not exist | Ask an administrator whether personal webhooks are offered | `ui.enable_user_webhooks` (section 7.1) |
| `You do not have permission to access this resource. Please contact your administrator for assistance.` | HTTP 403 | `backend/open_webui/routers/notifications.py:38-41`; `backend/open_webui/constants.py:70-72` | A non-admin without `features.webhooks` | Ask an administrator for the **User Webhooks** permission | The user's groups and Default permissions |
| `The URL you provided is invalid. Please double-check and try again.` | HTTP 400 | `backend/open_webui/utils/notifications.py:44`; `backend/open_webui/constants.py:99` | The address is not a valid public `http(s)` address or does not resolve; also when editing a target whose stored address no longer passes | Paste the address the receiving service gave you | Section 11.3 |
| `Webhook URL is required` | HTTP 400 | `backend/open_webui/utils/notifications.py:41`, `:256` | No address given | Enter the address | none |
| `unsupported notification event: {event}` | HTTP 400 | `backend/open_webui/utils/notifications.py:61` | An event other than the five (not from the normal screen) | none | Escalate |
| `events must be a list` / `Invalid notification delivery mode` / `Unsupported notification target type` | HTTP 400 | `backend/open_webui/utils/notifications.py:56`, `:67`, `:35` | Malformed request (not from the normal screen) | none | Escalate |
| `notification target id already exists` | HTTP 400 | `backend/open_webui/utils/notifications.py:167`, `:190` | The **Target ID** typed is already used by another of the user's targets | Choose another id or leave it empty | none |
| `Notification target not found` | HTTP 400 | `backend/open_webui/utils/notifications.py:197`, `:220`, `:353` | Editing, defaulting or testing a target removed in another tab | Reload | none |
| `Webhook delivery failed` | HTTP 400 | `backend/open_webui/utils/notifications.py:259-261` | **Send Test** could not deliver: the address failed the check at send time, the receiver did not answer, or answered with an HTTP error | Check the address with the receiving service; recreate the webhook there if it was revoked | Server log near the time: `Webhook skipped, URL invalid or not publicly resolvable: …` or an exception trace (section 10.9) |
| `User not found` | HTTP 400 | `backend/open_webui/utils/notifications.py:99-100` | The account record could not be read | Sign out and in | Escalate |

### 10.5 Text Sent to Receivers

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Test notification` + `This is a test notification from {app_name}.` | Webhook text | `backend/open_webui/utils/notifications.py:354-363`; `backend/open_webui/routers/notifications.py:100-101` | **Send Test**; `{app_name}` is `MedIT GPT` unless `WEBUI_NAME` is set | none | none |
| `Chat finished` / `Chat failed` / `Channel` / `Calendar alert` | Default titles | `backend/open_webui/utils/notifications.py:268`, `:288`, `:308`, `:325` | Used when the event carries no title (for example a chat without a title) | none | none |
| `starting {starts_in}` with `in {minutes_until} min` or `now` | Webhook text | `backend/open_webui/utils/notifications.py:327`; `backend/open_webui/utils/automations.py:598`, `:609` | Calendar reminder | none | none |
| `Notification` | Default title | `backend/open_webui/utils/notifications.py:388` | `notify` tool used without a title | none | none |
| `Event: {event name}` | Webhook text line | `backend/open_webui/utils/webhook.py:23-25` | Added to chat-format messages that carry an event name | none | none |
| `... (truncated)` | Webhook text | `backend/open_webui/utils/webhook.py:49` | A Discord message longer than 2,000 characters | none | none |
| `{short message} ({subject id})` | Webhook text | `backend/open_webui/events.py:1039-1044` | Every chat-format admin webhook message (section 9.3) | none | none |
| `Notification sent to {target_id}.` | Tool result | `backend/open_webui/tools/builtin.py:156` | The `notify` tool delivered | none | none |
| `Notification failed: {e}` | Tool result | `backend/open_webui/tools/builtin.py:157-158` | The `notify` tool failed; `{e}` is one of `Notification target not found` (`backend/open_webui/utils/notifications.py:380`), `Notification target is disabled` (`:382`), `Webhook delivery failed` (`:261`), `User not found` (`:100`) | Set up or switch on a target; see `builtin-native-tools.md` | As 10.4 |
| `Notification failed: user not found.` | Tool result | `backend/open_webui/tools/builtin.py:146-147` | The tool ran without a user | none | Escalate |

### 10.6 Toasts and Browser Notifications

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Starting now` / `Starting in 1 minute` / `Starting in {count} minutes` | Toast and browser-notification text | `src/routes/+layout.svelte:601-606` | Calendar reminder | Click to open the calendar | `automations-calendar-and-timers.md` |
| `New Chat` | Toast title | `src/routes/+layout.svelte:741` | A finished reply in a chat that has no title yet | none | none |
| `{title} / {WEBUI_NAME}` (for example "Conference Abstract Ideas / MedIT GPT") | Browser-notification title | `src/routes/+layout.svelte:622`, `:760`, `:873` | Section 9.5 | none | The fork's change, section 12 |
| `Dismiss notification` | Button label (read by screen readers) | `src/lib/components/NotificationToast.svelte:104-111` | The **×** on a notification card | none | none |

### 10.7 Banners

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Info` / `Warning` / `Error` / `Success` | Banner type label | `src/lib/components/common/Banner.svelte:59-69` | Each banner shows its type in capitals | none | none |
| `{banner content}` | Notice | `src/lib/components/common/Banner.svelte:103-113` | Admin-written text | Read it | Admin › Settings › General › UI › Banners |
| `Close Banner` | Button label | `src/lib/components/common/Banner.svelte:146-153` | The **×** on a banner | none | Section 5.13 (Remember Dismissal) |
| `Learn More` | Link | `src/lib/components/common/Banner.svelte:79`, `:124` | Only for a banner with a `url`, which stored banners do not have (section 6.4) | none | none |
| `You are currently using a trial license. Please contact support to upgrade your license.` | Info banner | `src/lib/components/chat/Navbar.svelte:276-286` | The licence metadata says trial | Report to support | Licence status is **TO BE CONFIRMED** (section 14) |
| `Exceeded the number of seats in your license. Please contact support to increase the number of seats.` | Error banner | `src/lib/components/chat/Navbar.svelte:288-298`; `src/lib/components/admin/Users/UserList.svelte:163-176` | Licence metadata has a seat count and the user count exceeds it | Report to support | As above |
| `Create announcements shown to users in the app.` | Help text | `src/lib/components/admin/Settings/General.svelte:516-518` | Under **Banners** | none | none |
| `Banners` / `Add banner` | Labels | `src/lib/components/admin/Settings/General.svelte:486`, `:495`; `src/lib/i18n/locales/en-US/translation.json:2369`, `:2372` | Banner editor | none | none |
| `Reorder` / `Type` / `Content` / `Remember Dismissal` / `Delete` | Labels and tooltips | `src/lib/components/admin/Settings/Interface/Banners.svelte:43`, `:54-62`, `:67`, `:80-81`, `:84-88` | Each banner row | none | none |

The licence banners pass a title (`Trial License`, `License Error`) that the banner component does
not display (`src/lib/components/chat/Navbar.svelte:280`, `:292`;
`src/lib/components/common/Banner.svelte:47-155`).

### 10.8 Update Toast, Version Text and What's New

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `A new version (v{LATEST_VERSION}) is now available.` | Info toast (admins) | `src/lib/components/layout/UpdateInfoToast.svelte:20-22` | A newer upstream Open WebUI release exists | Nothing for users; administrators plan upgrades with the maintainer | Section 11.5 |
| `Update for the latest features and improvements.` | Link | `src/lib/components/layout/UpdateInfoToast.svelte:24-26` | In the toast; opens the upstream GitHub releases | none | none |
| `Could not check for updates` | Notice | `src/lib/components/admin/Settings/General.svelte:143-146`; `src/lib/components/chat/Settings/About.svelte:72-73` | The server could not reach GitHub within one second, or the answer was unusable | none | Server log `Version update check failed: {e}` |
| `Checking for updates...` / `(v{version.latest} available!)` / `(latest)` | Version text (the middle one is assembled from the version and the key `available!`) | `src/lib/components/admin/Settings/General.svelte:153-157`; `src/lib/components/chat/Settings/About.svelte:79-83` | Beside the version number | none | none |
| `What's New in {WEBUI_NAME}` (shown as "What's New in MedIT GPT") | Window title | `src/lib/components/ChangelogModal.svelte:99-102` | The changelog window | none | none |
| `Release Notes` | Label | `src/lib/components/ChangelogModal.svelte:104` | Under the title, with the version | none | none |
| `Loading release notes...` | State | `src/lib/components/ChangelogModal.svelte:185-190` | While the notes load | Wait | none |
| `Could not load release notes.` + `Retry` | Error state | `src/lib/components/ChangelogModal.svelte:170-184` | The notes could not be loaded | **Retry** | Escalate if repeated |
| `Okay, Let's Go!` | Button | `src/lib/components/ChangelogModal.svelte:195-200` | Closes the window and records the version | none | none |
| `See what's new` / `Check for updates` / `Version` | Labels | `src/lib/components/admin/Settings/General.svelte:137`, `:170`, `:182`; `src/lib/components/chat/Settings/About.svelte:61`, `:95`, `:106`; `src/lib/i18n/locales/en-US/translation.json:2377`, `:2404`, `:2412`, `:2736`, `:2739`, `:2741` | Version blocks | none | none |
| `View the installed version and check release updates.` | Description | `src/lib/components/chat/Settings/About.svelte:64`; `src/lib/i18n/locales/en-US/translation.json:2740` | **About** | none | none |
| `Toast Notifications for New Updates` + `Show update toasts to admins when new versions are available.` | Label and description | `src/lib/components/common/InterfaceSettings.svelte:719`, `:735`; `src/lib/i18n/locales/en-US/translation.json:2988-2989` | **Settings › Interface** (admins) | none | none |
| `Show "What's New" Modal on Login` + `Open the changelog modal after sign-in when enabled.` | Label and description | `src/lib/components/common/InterfaceSettings.svelte:742`, `:758` | **Settings › Interface** (admins) | none | none |
| `User Webhooks` + `Allow users to configure webhooks from their account.` | Label and description | `src/lib/components/admin/Settings/General.svelte:380-381`; `src/lib/i18n/locales/en-US/translation.json:2410-2411` | Admin › Settings › General › Features | none | none |
| `WebUI URL` + `Enter the public URL of your WebUI. This URL will be used to generate links in the notifications.` | Label and description | `src/lib/components/admin/Settings/General.svelte:406-407`; `src/lib/i18n/locales/en-US/translation.json:2413-2414` | Admin › Settings › General › Features | none | none |
| `User Webhooks` + `This is a default user permission and will remain enabled.` | Label and notice | `src/lib/components/admin/Users/Groups/Permissions.svelte:1156`, `:1160-1166` | Group permissions; the notice shows when Default permissions grant the permission but the group switch is off | none | Ground truth: groups only add |

### 10.9 Server Log Lines (Not Shown to Users)

| Message | Severity | Source | Trigger | User action | Support check |
|---|---|---|---|---|---|
| `Webhook skipped, URL invalid or not publicly resolvable: {e}` | Log warning | `backend/open_webui/utils/webhook.py:36-39` | At send time the address failed the check (for example its host no longer resolves) | none | The address with the receiving service; DNS |
| exception trace from `log.exception(e)` | Log error | `backend/open_webui/utils/webhook.py:99-101` | The post failed: connection error, certificate error, or an HTTP error answer | none | The HTTP status in the trace; the receiving service |
| `Event webhook failed for {id}` | Log error | `backend/open_webui/events.py:1058-1059` | Unexpected failure around one admin webhook post | none | Escalate with the time |
| `Event webhook delivery could not be scheduled for {event}` | Log error | `backend/open_webui/events.py:1062-1066` | No running loop to start the delivery task | none | Escalate |
| `Invalid event webhook config skipped` | Log error | `backend/open_webui/events.py:847-850` | A stored admin webhook fails validation (for example a filter naming an event later removed) and is ignored | none | Edit or recreate the webhook |
| `Notification delivery could not be scheduled for {event}` | Log error | `backend/open_webui/events.py:1074-1080` | As above, for personal targets | none | Escalate |
| `Notification delivery failed for user {user_id} and event {event}` | Log error | `backend/open_webui/utils/notifications.py:418-419` | A personal target could not be delivered automatically | none | The user's target address; contains a user id, handle as personal data |
| `Event sink failed for {event}` | Log error | `backend/open_webui/events.py:1198-1202` | One of the four sinks raised | none | Escalate |
| `Event functions could not be loaded for {event}` / `Event function failed for {id}` / `Event functions could not be scheduled for {event}` | Log error | `backend/open_webui/events.py:1123-1125`, `:1155-1156`, `:1159-1163` | Event function problems | none | `functions-pipes-filters-actions-and-pipelines.md` |
| `Upstream {provider} request failed: HTTP {status} ({error_type}) url={base_url} model={requested_model} code={error_code} message={error_text}` | Log warning (error for HTTP 500 and above) | `backend/open_webui/events.py:1237-1249` | Every provider HTTP error, whether or not anyone subscribes to `model.provider_request.failed` | none | `model-connections-openai-ollama-and-direct.md` |
| `Version update check failed: {e}` | Log warning | `backend/open_webui/main.py:2611-2613` | GitHub could not be reached or answered with an error | none | Outbound internet access from the server |
| `Error loading WEBUI_BANNERS: {e}` | Log error | `backend/open_webui/config.py:2160-2165` | The `WEBUI_BANNERS` environment variable is not a valid banner list | none | The variable's JSON; banners then start empty |
| `Failed to send notification for calendar alert {id}` / `Failed to mark event {id} as alerted` | Log debug | `backend/open_webui/utils/automations.py:593-594`, `:613-614` | Calendar alert problems | none | `automations-calendar-and-timers.md` |

## 11. Common Tier-1 Issues and Troubleshooting

Tier 1 is read-only: it explains, checks what the user sees and escalates. It never changes
settings, permissions, webhooks or banners. Never ask a user to paste a webhook address into a
ticket: treat every address as a secret (section 6.2). Ask for the service name (Slack, Teams,
Discord) and the host shown in the list instead.

### 11.1 "I never get notified when my chat finishes"

**Symptom.** The user expects a pop-up, a sound, a Slack or Teams message, or an email when a long
answer is ready, and gets nothing.

**Likely causes, in order.**

1. **They expect an email.** MedIT GPT sends no email (section 1).
2. **They are looking at the chat.** Toasts and browser notifications fire only for a chat that is
   not on screen, or while the tab is hidden (`src/routes/+layout.svelte:735-738`).
3. **Browser Notifications is off, or the browser blocked it.** It is off by default; switching it
   on needs the browser's permission, and the permission is per browser and per device
   (`src/lib/components/chat/Settings/Notifications.svelte:26`, `:60-78`). The choice follows the
   account, but a new browser may still lack the permission (section 5.8).
4. **Another MedIT GPT tab is the "last active tab".** Only that tab creates browser notifications
   (`src/routes/+layout.svelte:758`, `:1161-1180`).
5. **MedIT GPT was closed or the computer slept.** In-page notices need an open, connected tab
   (`src/routes/+layout.svelte:1224`).
6. **A personal target uses Only when away.** The user counts as present while any MedIT GPT tab is
   open (heartbeat every 30 seconds) or for three minutes after their last request, so "away"
   messages rarely fire during a normal chat (section 4; `backend/open_webui/models/users.py:918-925`).
7. **Personal webhooks are not offered.** **User Webhooks** is off, or the user lacks the
   permission; then **Notification Targets** is missing from their settings (section 3).
8. **Temporary chat.** No `chat.finished` event exists for temporary chats
   (`backend/open_webui/utils/middleware.py:210-211`).

**Diagnostic steps.**

1. Ask which kind of notice they expect: on-screen card, desktop pop-up, sound, or a message in
   another app.
2. With the user, open **Settings › Notifications**: is **Browser Notifications** on? Is there a
   **Notification Targets** section, and does the target list **Chat finished** and show
   **Always** or **Only when away**?
3. Ask whether the site is allowed to show notifications in the browser's site settings and
   whether the operating system's "do not disturb" or focus mode is on.
4. Ask whether the chat was a temporary chat and whether MedIT GPT stayed open in a tab.

**Resolution.** Explain the rules above. Suggest turning **Browser Notifications** on in each
browser they use, keeping one MedIT GPT tab open in the background, and, if they have a personal
target, choosing **Always** for **Chat finished**. If **Notification Targets** is missing, explain
that personal webhooks are an administrator decision.

**Escalation.** If the setup is right and nothing arrives: send the user's account email (handled
as personal data), the browser and version, the time of a chat that should have notified, and
whether a personal target is involved (service name only, never the address) to the platform
maintainer.

### 11.2 "The webhook stopped working"

**Symptom.** An admin webhook or a personal target used to post messages and no longer does.

**Likely causes, in order.**

1. **It was switched off**, or its filters or scope no longer match the events expected
   (sections 5.2 and 5.3).
2. **The receiving service revoked or rotated the address.** MedIT GPT does not notice: failures
   are only logged, never retried, never shown to the admin, and the webhook stays switched on
   (section 8.1; `backend/open_webui/utils/webhook.py:99-101`).
3. **The address no longer passes the address check at send time**, for example the host stopped
   resolving; the post is skipped with a log warning (`backend/open_webui/utils/webhook.py:31-39`).
4. **User Webhooks was switched off** (personal targets only); automatic delivery stops for
   everyone (`backend/open_webui/utils/notifications.py:394-395`).
5. **The events it relied on are not published**, for example `chat.failed` for streaming replies,
   `config.updated` for General-tab changes, or a **System events only** scope for admin changes
   (sections 5.2, 5.9 and 9.2).
6. **An upgrade renamed or removed events.** A stored filter naming an event that no longer exists
   makes the whole webhook invalid; it is skipped with `Invalid event webhook config skipped` and
   also disappears from the admin list, which shows only valid webhooks
   (`backend/open_webui/events.py:843-851`; `backend/open_webui/main.py:2499-2501`).
7. **A hung receiver.** With no time limit configured, a receiver that never answers holds up the
   later webhooks for that event (section 8.1).

**Diagnostic steps.**

1. Admin webhook: ask an administrator to open Admin › Settings › General › Events and read the
   row: is it faded (off)? Which host, events and scope does it show?
2. Personal target: with the user, check the target's switch and events, then select **Send
   Test**. **Test notification sent.** means the address answered; **Webhook delivery failed**
   means it did not (section 10.4).
3. Ask the receiving service's owner whether the webhook still exists there.

**Resolution.** Tier 1 changes nothing. Explain the findings; the owner of the webhook (the user
for a personal target, an administrator for an admin webhook) recreates the address at the
receiving service and updates MedIT GPT.

**Escalation.** Send the webhook's name and host (never the full address), the time messages
stopped, and whether **Send Test** fails, to the platform maintainer, who can search the server log
for `Webhook skipped`, exception traces from `post_webhook`, `Event webhook failed for` and
`Notification delivery failed for user` (section 10.9).

### 11.3 "Send Test says Webhook delivery failed"

**Symptom.** In **Settings › Notifications**, **Send Test** shows `Webhook delivery failed`, or
saving a target shows `The URL you provided is invalid. Please double-check and try again.`

**Likely causes, in order.**

1. The address was mistyped or copied incompletely.
2. The receiving service deleted or disabled the webhook.
3. The address is on a private or internal network, or its host does not resolve from the
   MedIT GPT server; such addresses are refused (section 7.2, `ENABLE_LOCAL_WEB_FETCH`).
4. The receiver answered with an HTTP error, or the server could not make an outbound connection.

**Diagnostic steps.** Ask which service the address came from and whether it works from that
service's own test tool. Ask whether it is an internal (university network) address.

**Resolution.** Ask the user to create a fresh webhook address at the receiving service and paste
it with **Edit**. Explain that internal addresses may be refused by design.

**Escalation.** If a public address from a mainstream service fails, send the service name, the
time of the test and the exact message to the platform maintainer (who can see the server log
line for that time).

### 11.4 "Users don't see the banner"

**Symptom.** An administrator published a banner and some or all users say they do not see it.

**Likely causes, in order.**

1. **They are inside a chat.** Banners appear only on the new-chat screen
   (`src/lib/components/chat/Navbar.svelte:271`).
2. **Their page was loaded before the banner was saved.** Banners are fetched when the app loads;
   nothing refreshes open pages (`src/routes/(app)/+layout.svelte:156-159`, `:224-225`).
3. **They closed it earlier.** With **Remember Dismissal** on, a closed banner stays hidden in that
   browser (`src/lib/components/chat/Navbar.svelte:300-314`).
4. **The banner was never saved.** Banners save with the General tab's **Save**; a banner without a
   **Type** stops the form from submitting (section 5.13).
5. **Their language has its own banner text**, which may differ from (for example be older than)
   the default text; an empty translation falls back to the default
   (`src/lib/components/common/Banner.svelte:104-112`; `src/lib/utils/localizedContent.ts:10`,
   `:21-33`).

**Diagnostic steps.** Ask the user to select **New Chat** and reload the page; ask whether they
remember closing a banner; ask which language their interface uses. Ask the administrator whether
**Save** was selected after adding the banner.

**Resolution.** Ask the user to reload on the new-chat screen. A banner closed with **Remember
Dismissal** comes back only if the user clears the site's stored data, or if an administrator
publishes it again as a new banner (dismissal is remembered by banner id).

**Escalation.** If a saved banner still does not appear after a reload on the new-chat screen,
send the banner's type, the time it was saved and the user's browser to the platform maintainer.

### 11.5 "It says a new version is available"

**Symptom.** An administrator sees "A new version (v…) is now available." or "(v… available!)"
beside the version number, and asks whether MedIT GPT needs updating; or a user sees the
"available!" text in **Settings › About**.

**Likely causes, in order.**

1. **This is the upstream Open WebUI release check.** The server asks GitHub for the latest
   `open-webui/open-webui` release and compares it with the running version
   (`backend/open_webui/main.py:2594-2613`). It knows nothing about MedIT GPT's own releases or
   the U of T customisations (section 12).
2. Upstream has simply published a newer version than the one MedIT GPT runs (0.11.4).

**Diagnostic steps.** Note the version shown and the version offered.

**Resolution.** Explain that the notice comes from the upstream project and that upgrades of
MedIT GPT are planned by its maintainer; nothing for the user to do. Administrators can hide the
toast for themselves with **Toast Notifications for New Updates**, or close it (it returns after 24
hours) (section 5.14).

**Escalation.** None needed. Whether the maintainer wants the version check switched off
(`ENABLE_VERSION_UPDATE_CHECK`) is **TO BE CONFIRMED**.

### 11.6 "A webhook says my chat failed but the answer looks fine"

**Symptom.** A Slack, Teams or other message says **Chat failed** for a chat whose answer is
complete on screen.

**Likely causes, in order.**

1. **A step after the answer failed.** For non-streaming replies, `chat.failed` is published when
   anything in the processing raises an error, including background tasks such as title, tag or
   follow-up generation that run after the answer was saved and after `chat.finished` was
   published (`backend/open_webui/utils/middleware.py:4377-4409`). The user therefore receives both
   messages for the same chat.
2. A filter function's outlet step failed after the answer was produced (same code path).

**Diagnostic steps.** Ask for the time and the error text in the message (it is the exception's
text). Check whether the chat's title or tags are missing, which points to a failed background
task.

**Resolution.** Explain that the answer is complete and safe to use; the failure message refers to
an after-step. Details and wording are in `chat-completion-pipeline-and-generation-tasks.md`
(sections 5.7 and 5.8).

**Escalation.** Send the time and the error text from the notification (not the conversation) to
the platform maintainer; repeated after-step failures usually point to a task model or filter
problem.

### 11.7 "The link in my notification opens a Not Found page"

**Symptom.** Clicking the link in a personal **Chat finished** or **Chat failed** message opens an
error page instead of the chat.

**Likely causes, in order.**

1. **The link drops `/c/`.** Personal chat notifications rewrite `…/c/{chat id}` to `…/{chat id}`,
   and no page exists at that address (section 9.4). Read from the code; not tried.
2. **WebUI URL is empty**, so the link is relative (no host name) and does not lead back to
   MedIT GPT from the receiving app (section 9.4).

**Diagnostic steps.** Ask the user whether the link contains `/c/` before the long id (they can
read it out without sharing the full message).

**Resolution.** Tell the user to open MedIT GPT and find the chat in the sidebar (search by its
title), or to insert `/c` before the chat id in the address.

**Escalation.** Report the pattern (not the user's link) to the platform maintainer as an upstream
defect candidate.

### 11.8 "I can't find Notification Targets in my settings"

**Symptom.** Instructions mention personal webhooks, but **Settings › Notifications** shows only
**Browser Notifications** and **Notification Sound**.

**Likely causes, in order.** **User Webhooks** is off for the instance (the default), or the user
does not have the **User Webhooks** permission (also off by default)
(`src/lib/utils/settings-access.ts:16-18`; `backend/open_webui/config.py:1932-1934`, `:2100`).

**Diagnostic steps.** None beyond confirming what the screen shows.

**Resolution.** Explain that personal webhooks are offered at the administrators' discretion.

**Escalation.** Pass the request to the platform maintainer; whether MedIT GPT offers personal
webhooks, and to whom, is **TO BE CONFIRMED** and has privacy implications (section 9.6).

### 11.9 "Our Teams channel gets nothing, or shows raw text"

**Symptom.** A webhook pointed at Microsoft Teams (or another chat tool) receives nothing readable.

**Likely causes, in order.**

1. The address is not a `webhook.office.com` connector address (for example a Power Automate
   workflow address), so MedIT GPT sends the generic JSON envelope instead of a Teams card
   (`backend/open_webui/utils/webhook.py:42-84`).
2. The receiving tool expects a format MedIT GPT does not produce; only Slack, Google Chat,
   Discord and Teams connector formats are built in.

**Diagnostic steps.** Ask which service and which kind of webhook (connector or workflow) was
created; ask for the host only.

**Resolution.** Explain the supported formats (section 9.3).

**Escalation.** Send the service name and host to the platform maintainer; the organizational
choice of receiving services is **TO BE CONFIRMED**.

### 11.10 "Our admin webhook is full of people's messages"

**Symptom.** A shared Slack or monitoring channel shows message text, names or email addresses.

**Likely causes, in order.** An admin webhook listens to **All events** (or `message.*`,
`chat.*`) with generic JSON or Teams format; these carry message previews, reply text, names and
emails (sections 9.2 and 9.6).

**Diagnostic steps.** Ask an administrator for the webhook's name, host, events and scope as
shown in the list.

**Resolution.** Tier 1 changes nothing. Treat this as a possible privacy incident: stop and refer
rather than work around it.

**Escalation.** Report immediately to the platform maintainer and to the U of T Privacy Office
(privacy.utoronto.ca); include the webhook name and host, the time range, and the kind of data
seen, but no copies of the messages.

### 11.11 "Browser notifications pop up on the wrong computer, or twice"

**Symptom.** Notifications appear on a device the user is not using, or more than once.

**Likely causes, in order.** The **Browser Notifications** choice follows the account, and every
signed-in browser with permission and an open tab shows notifications for its own last active tab
(sections 5.8 and 9.5). Toasts appear in every connected tab that meets the conditions
(`src/routes/+layout.svelte:735-781`).

**Diagnostic steps.** Ask which devices and browsers have MedIT GPT open.

**Resolution.** Close MedIT GPT tabs on devices not in use, or block notifications for the site in
that browser's settings.

**Escalation.** None normally.

### 11.12 "The What's New window keeps showing Open WebUI release notes"

**Symptom.** After sign-in an administrator sees **What's New in MedIT GPT** listing upstream
changes, or it appears again.

**Likely causes, in order.** It opens for administrators whenever the version recorded in their
settings differs from the running version, for example after an upgrade, on first sign-in, or if
the window was closed with Escape, by clicking outside it or by reloading, rather than with
**Okay, Let's Go!** or **×**; only those two buttons record the version
(`src/routes/(app)/+layout.svelte:355-357`; `src/lib/components/ChangelogModal.svelte:41-46`,
`:110-116`, `:195-200`; `src/lib/components/common/Modal.svelte:46-52`, `:134-135`). The
notes are the upstream changelog bundled with the release (`CHANGELOG.md`).

**Diagnostic steps.** None.

**Resolution.** Close it with **Okay, Let's Go!**; switch off `Show "What's New" Modal on Login` in
**Settings › Interface** to stop it opening by itself.

**Escalation.** None. Whether MedIT GPT should publish its own release notes is **TO BE
CONFIRMED**.

### 11.13 "I get no channel message notifications"

**Symptom.** A channel member is not told about new posts.

**Likely causes, in order.**

1. They were looking at that channel in a visible tab, which does not notify
   (`src/routes/+layout.svelte:827`).
2. **Browser Notifications** is off, or another tab is the last active tab (as 11.1).
3. For a personal target: **User Webhooks** is off, the target does not list **Channel message**,
   or the user was **connected** when the post was made (only offline members get the webhook
   event) (`backend/open_webui/routers/channels.py:941-973`).
4. They are not a member of the channel (`backend/open_webui/routers/channels.py:948-952`).

**Diagnostic steps.** Ask whether they had MedIT GPT open at the time and which notice they
expected.

**Resolution.** Explain the rules; there is no per-channel mute or subscription setting.

**Escalation.** If none of the causes fit, send the channel name, the time and the expected notice
type to the platform maintainer.

## 12. Local Customisations

Compared with upstream Open WebUI v0.11.4 (`git diff main...uoft`), this area has three
branding changes, all from commit `402a737ba` ("Add UofT Branding"); there are no uncommitted
working-tree changes in the files of this area (`git diff` on them is empty).

| Change | Upstream text | MedIT GPT text | Source |
|---|---|---|---|
| Test notification text | "This is a test notification from Open WebUI." (upstream branch `main` only) | `This is a test notification from {app_name}.`, which reads "This is a test notification from MedIT GPT." with the default name | `backend/open_webui/utils/notifications.py:360`; upstream `main:backend/open_webui/utils/notifications.py:360` |
| Browser-notification titles (calendar, chat, channel) | `{title} / Open WebUI` | `{title} / {WEBUI_NAME}`, which reads "{title} / MedIT GPT" | `src/routes/+layout.svelte:622`, `:760`, `:873`; upstream `main:src/routes/+layout.svelte:622`, `:760`, `:873` |
| App name used everywhere else in this area | `Open WebUI`, with " (Open WebUI)" appended to custom names | `MedIT GPT` by default, no suffix | `backend/open_webui/env.py:951`; `backend/open_webui/main.py:538`; ground truth |

Effects of the name change that need no code change of their own: the Teams card subtitle
("MedIT GPT (0.11.4) - …"), the What's New title ("What's New in MedIT GPT"), the **About**
heading ("MedIT GPT Version") and the `notify` tool's sender name all read the app name
(`backend/open_webui/utils/webhook.py:71`; `src/lib/components/ChangelogModal.svelte:100-101`;
`src/lib/components/chat/Settings/About.svelte:61`; `backend/open_webui/tools/builtin.py:149-155`).
The fork's replacement favicon (`backend/open_webui/static/favicon.png`, changed in the same
commit) is the picture on in-app notification cards and on chat and calendar browser notifications
(`src/lib/components/NotificationToast.svelte:117`; `src/routes/+layout.svelte:627`, `:765`;
`backend/open_webui/main.py:3023`).

Unchanged upstream behaviour that matters for MedIT GPT:

- **Update toast and version check** compare against the **upstream Open WebUI** GitHub releases
  and link there (`backend/open_webui/main.py:2603`; `src/lib/components/layout/UpdateInfoToast.svelte:24`).
  They will report every upstream release, whether or not the fork has adopted it.
- **What's New** shows the upstream `CHANGELOG.md`, which the fork has not edited; no MedIT GPT
  release notes exist in the repository (`CHANGELOG.md:8`; `git diff main...uoft -- CHANGELOG.md`
  is empty).
- **Teams card image** stays the upstream Open WebUI favicon at `openwebui.com`, which the licence
  comment protects (`backend/open_webui/env.py:953-957`; `backend/open_webui/utils/webhook.py:72-75`).
- The admin Events note still names Open WebUI ("Event names may change as Open WebUI evolves…"),
  under a licence comment (`src/lib/components/admin/Settings/Events.svelte:645-650`).
- Code defaults that matter here (personal webhooks off, permission off, version check on) are
  upstream's; the production values are **TO BE CONFIRMED** (section 7).

## 13. Source File Index

Directories in scope: `backend/open_webui/` (events, notifications, webhook helper, routers that
publish events), `src/lib/components/` (admin Events and banner editors, notification and banner
components, settings panels), `src/routes/` (root and app layouts), `src/lib/apis/`. Files marked
*all* were read in full.

### 13.1 Back End

| File | What it holds for this area | Read |
|---|---|---|
| `backend/open_webui/events.py` | The event catalogue (181 events), envelope, sanitizing, admin webhook storage and matching, legacy migration, the four sinks, `publish_event`, provider-failure helper | all |
| `backend/open_webui/utils/webhook.py` | `post_webhook`: address check, format detection (Slack, Google Chat, Discord, Teams, generic), the post | all |
| `backend/open_webui/utils/notifications.py` | Personal notification targets: validation, masking, legacy migration, delivery, test, `notify_target`, per-event message text (fork change at `:360`) | all |
| `backend/open_webui/routers/notifications.py` | `/api/v1/notifications/*` routes and their access check | all |
| `backend/open_webui/main.py` | `/api/events*` routes (`:2475-2583`), version check (`:2594-2613`), changelog (`:2616-2618`), start-up migration and system events (`:361-370`, `:471-496`), `enable_user_webhooks` and version flags in the config response (`:2283`, `:2347`, `:2371`), chat message events (`:1306-1452`, `:1495-1530`), router mount (`:866`), static mount (`:3023`), SPA fallback (`:298-311`) | listed ranges |
| `backend/open_webui/config.py` | `WEBHOOK_URL`, `ENABLE_USER_WEBHOOKS`, `USER_PERMISSIONS_FEATURES_USER_WEBHOOKS`, `BannerModel` and `WEBUI_BANNERS`, `ENABLE_LOCAL_WEB_FETCH`, `DEFAULT_CONFIG` entries | `:1108-1116`, `:1925-2022`, `:2076-2104`, `:2145-2167`, `:3115-3130` |
| `backend/open_webui/env.py` | `INSTANCE_ID`, changelog parsing, heartbeat interval, HTTP client timeout, TLS and redirects, `WEBUI_NAME` (fork), `WEBUI_FAVICON_URL`, `ENABLE_PLUGINS`, version check and offline mode | `:155`, `:180-224`, `:523-532`, `:604-640`, `:946-958`, `:1186`, `:1195-1207` |
| `backend/open_webui/constants.py` | `WEBHOOK_MESSAGES` (unused), `ACCESS_PROHIBITED`, `NOT_FOUND`, `INVALID_URL` | `:27-41`, `:66-99` |
| `backend/open_webui/models/config.py` | How settings are read and written (no cache) | `:101-240` |
| `backend/open_webui/models/users.py` | `UserSettings`, settings merge, `last_active_at` update, `is_user_active` (three minutes) | `:136-148`, `:772-776`, `:825-847`, `:918-928` |
| `backend/open_webui/routers/configs.py` | Banner routes and config events | `:95-160`, `:840-877` and the publishing calls |
| `backend/open_webui/routers/users.py` | Stripping notification settings without the permission | `:505-562` |
| `backend/open_webui/routers/channels.py` | `send_notification` and `channel.message` | `:325-345`, `:935-973`, `:1225-1262` |
| `backend/open_webui/utils/middleware.py` | `chat.finished` and `chat.failed` | `:180-236`, `:4210-4420`, `:6550-6580` |
| `backend/open_webui/utils/automations.py` | Scheduler loop and calendar alerts | `:53-130`, `:530-625` |
| `backend/open_webui/tools/builtin.py` | The `notify` tool | `:130-160` |
| `backend/open_webui/utils/tools.py` | When `notify` is offered | `:536-546`, `:750-775` |
| `backend/open_webui/socket/main.py` | Heartbeat, event emitter and internal notifications | `:484-500`, `:1120-1175` |
| `backend/open_webui/utils/auth.py` | Last-active updates on requests | `:475-490`, `:555-566` |
| `backend/open_webui/retrieval/web/utils.py` | `validate_url` and the outbound session used for webhooks | `:107-171`, `:269-296` |
| `backend/open_webui/routers/retrieval.py` | `retrieval.content.process_failed` | `:2150-2185` |
| `backend/open_webui/routers/auths.py` | Sign-in sources and the admin config mapping | `:131`, `:167-222`, `:726-736`, `:745-812`, `:841-849`, `:928-940`, `:1745-1771` |
| `backend/open_webui/utils/oauth.py` | SSO sign-in event; legacy `WEBHOOK_URL` in the runtime map | `:131-180`, `:2196-2210` |
| `backend/open_webui/routers/functions.py` | Function lifecycle events | `:294-325` |
| `backend/open_webui/routers/pipelines.py` | `pipeline.valves_updated` on read | `:446-555` |
| `backend/open_webui/routers/memories.py` | Batch memory events | `:234-319` |
| `backend/open_webui/routers/chats.py`, `audio.py` | Compaction and cached speech events | `:1305-1318`; `:622-640` |
| Every other file with an `EVENTS.` reference (`routers/` audio, auths, automations, calendar, channels, chats, configs, evaluations, files, folders, functions, groups, images, knowledge, memories, models, notes, ollama, openai, pipelines, prompts, retrieval, scim, skills, terminals, tools, users; `utils/` automations, middleware, oauth; `tools/builtin.py`) | Publishing calls for section 9.2, parsed call by call | each publishing call |

### 13.2 Front End

| File | What it holds for this area | Read |
|---|---|---|
| `src/lib/components/admin/Settings/Events.svelte` | Admin webhook list and editor | all |
| `src/lib/components/admin/Settings/General.svelte` | Version block, User Webhooks, WebUI URL, Events block, Banners editor host and save | `:1-200`, `:274-420`, `:478-525` |
| `src/lib/components/admin/Settings/Interface/Banners.svelte` | Banner rows | all |
| `src/lib/components/common/Banner.svelte` | Banner display | all |
| `src/lib/components/chat/Navbar.svelte` | Where banners show and dismissal | `:50-68`, `:265-325` |
| `src/lib/components/admin/Users/UserList.svelte` | Seat licence banner | `:160-176` |
| `src/lib/components/NotificationToast.svelte` | Notification card and sound | all |
| `src/lib/components/chat/Settings/Notifications.svelte` | Personal notification settings | all |
| `src/lib/components/chat/Settings/About.svelte` | Version, update check, See what's new | `:1-112` |
| `src/lib/components/common/InterfaceSettings.svelte` | Update toast and What's New switches | `:99-100`, `:329-330`, `:710-765` |
| `src/lib/components/chat/SettingsModal.svelte` | Tabs, visibility, `saveSettings` | `:195-270`, `:378-410`, `:438-450` |
| `src/lib/components/layout/UpdateInfoToast.svelte` | Update toast | all |
| `src/lib/components/ChangelogModal.svelte` | What's New | all |
| `src/lib/components/common/Modal.svelte` | How windows close | `:40-56`, `:128-146` |
| `src/lib/components/chat/Chat.svelte` | Plugin `notification` toasts in the open chat | `:1203-1206`, `:1340-1380` |
| `src/routes/+layout.svelte` | Socket handlers, toasts, browser notifications, last active tab, heartbeat (fork change at `:622`, `:760`, `:873`) | `:100-232`, `:540-895`, `:1140-1225`, `:1274` |
| `src/routes/(app)/+layout.svelte` | Banner loading, changelog and update toast triggers | `:140-235`, `:345-438` |
| `src/routes/(app)/admin/settings/+page.svelte`, `src/routes/(app)/admin/settings/[tab]/+page.svelte`, `src/routes/+error.svelte` | Admin settings redirects; error page | all |
| `src/lib/apis/notifications/index.ts` | Personal target API client | all |
| `src/lib/apis/index.ts` | Event catalogue, admin webhooks, changelog and version clients | `:1522-1590`, `:1600-1768` |
| `src/lib/apis/configs/index.ts` | Banner clients | `:780-830` |
| `src/lib/utils/settings-access.ts` | `canUseNotificationTargets` | `:1-70` |
| `src/lib/utils/localizedContent.ts`, `src/lib/utils/index.ts` | Banner language choice; version comparison | `:21-33`; `:660-668` |
| `src/lib/stores/index.ts`, `src/lib/types/index.ts` | Stores and setting names; `Banner` type | `:14`, `:104`, `:137`, `:169-170`, `:226-235`, `:275`; `:1-10` |
| `src/lib/components/admin/Users/Groups/Permissions.svelte`, `src/lib/components/admin/Users/Groups.svelte` | User Webhooks permission | `:960`, `:1145-1170`; `:56-118` |
| `src/lib/components/common/SettingsSelect.svelte`, `src/lib/components/common/LocalizedField.svelte` | Required select; translated fields | props only |
| `src/lib/i18n/locales/en-US/translation.json` | Dotted keys and plain-key values | the keys cited |
| `CHANGELOG.md` | Upstream release notes shown in What's New | `:1-12` and version headings |

## 14. Open Questions

Everything below could not be established from the repository, was read from the code without
being tried, or is an organizational matter. Nothing found contradicts `CLAUDE.md`,
`knowledgebase/tools/ground-truth.md` or `knowledgebase/tools/inventory.md`.

### 14.1 Live Values (Data, TO BE CONFIRMED)

1. Whether **User Webhooks** (`ui.enable_user_webhooks`) is on in production, and which groups (or
   Default permissions) grant `features.webhooks`. Code defaults are off and off.
2. Which **admin event webhooks** exist in production (`events.webhooks`): names, receiving
   services, filters and scopes; and whether a legacy `webhook_url` was migrated into a **Default
   webhook** listening to all events (section 5.4).
3. The production **WebUI URL** (`webui.url`); when empty, notification links are relative.
4. Production **banners** (`ui.banners`) and whether `WEBUI_BANNERS` is set.
5. `ENABLE_VERSION_UPDATE_CHECK`, `OFFLINE_MODE`, `AIOHTTP_CLIENT_TIMEOUT`,
   `AIOHTTP_CLIENT_ALLOW_REDIRECTS`, `WEBSOCKET_HEARTBEAT_INTERVAL`, `ENABLE_PLUGINS`,
   `INSTANCE_ID` and `WEBUI_NAME` in production, and the number of worker processes (each publishes
   its own start-up events and delivers its own events).
6. Whether the production server can reach `api.github.com` (needed for the update check) and the
   receiving webhook services (outbound access and any proxy).
7. Whether licence metadata is present, which would show the trial or seat banners
   (`src/lib/components/chat/Navbar.svelte:276-298`).

### 14.2 Organizational (TO BE CONFIRMED)

8. Which outside services, if any, are approved to receive MedIT GPT event data, given that
   payloads carry names, emails, message previews and reply text (section 9.6). To be settled with
   the platform maintainer and the U of T Privacy Office.
9. Whether personal webhooks are offered to users at all, and to whom.
10. Whether the U of T Microsoft Teams tenant still issues `webhook.office.com` connector
    addresses; workflow-style addresses receive the generic JSON envelope instead of a card
    (section 9.3). This depends on Microsoft's service, not on the repository.
11. Whether the maintainer wants the upstream update toast shown to MedIT GPT administrators, and
    whether MedIT GPT will publish its own release notes (What's New shows only upstream notes).
12. Whether tier 1 has an administrator view of Admin › Settings › General to read the webhook
    list, or must ask an administrator (section 11).
13. Support contacts and escalation routes for webhook and notification problems (none exist in
    the repository; see ground truth).

### 14.3 Read From the Code, Not Tried

14. **Personal chat links drop `/c/`** and point to `/{chat id}`, for which no route exists; the
    page shown is assumed to be the generic error page (`backend/open_webui/utils/notifications.py:271-273`,
    `:291-293`; `src/routes/+error.svelte:8`). Likely an upstream defect; worth reproducing and
    reporting upstream.
15. **Withdrawing `features.webhooks` does not stop deliveries** to targets saved earlier, because
    automatic delivery checks only the instance switch (section 3).
16. **`pipeline.valves_updated` fires when valves are read**, and saving pipeline valves publishes
    nothing (`backend/open_webui/routers/pipelines.py:446-472`, `:533-555`).
17. **`notification.test` and `notification.manual` are never published** although they appear in
    the catalogue and filter list.
18. **`config.updated` is not published for most settings screens** (General, Authentication,
    LDAP, OAuth, Documents, Web Search, embeddings), so admin webhooks cannot serve as a complete
    settings-change audit (section 9.2.1).
19. **Calendar alerts with several workers**: each worker checks for due alerts and marks them
    afterwards, with no claim step visible in `_check_calendar_alerts`
    (`backend/open_webui/utils/automations.py:552-594`); whether two workers can send the same
    alert twice was not established.
20. **A legacy personal webhook address that no longer passes the address check** makes reading
    the user's targets fail, because the conversion runs inside the read and the list route does
    not catch the error (`backend/open_webui/utils/notifications.py:111-122`;
    `backend/open_webui/routers/notifications.py:50-53`). What the screen shows then was not
    traced.
21. The `WEBHOOK_URL` entry in the single sign-on runtime settings map
    (`backend/open_webui/utils/oauth.py:169`) is loaded but no code reading it was found; its
    purpose is unknown.
22. `ui.notificationSoundAlways` has no switch; how a user could set it (for example a settings
    import) was not traced.
23. Whether any admin screen or export reveals users' personal target addresses (they are stored
    in each user's settings record, section 6.3) was not traced; the database export described in
    `admin-settings-panels.md` would include the `user` table.

### 14.4 Library and Browser Behaviour (Not in the Repository)

24. With redirects off (the default), whether a `3xx` answer from a moved receiver counts as
    delivered depends on the HTTP library's `raise_for_status()`, which conventionally raises only
    for `4xx` and `5xx`; if so, a moved webhook "succeeds" silently
    (`backend/open_webui/utils/webhook.py:87-96`).
25. With `AIOHTTP_CLIENT_TIMEOUT` unset the session has no total time limit; whether the library
    still applies a connection timeout was not established.
26. Browser throttling of background timers may stretch the 30-second heartbeat; whether that ever
    makes an open tab count as "away" (three minutes) depends on the browser.
27. Some browsers (notably on mobile) do not allow the page-level `Notification` constructor the
    code uses (`src/routes/+layout.svelte:622`, `:760`, `:873`); behaviour on those browsers was
    not established.
28. Whether chat services render the `**bold**` markers in personal notification titles depends on
    each service's formatting rules.

### 14.5 Security-Sensitive (Referred, Not Documented)

29. Which webhook addresses the server accepts or refuses (internal networks, local fetching,
    proxies) and how that check is enforced at connection time. Security-sensitive: refer to the
    platform maintainer and U of T Information Security (security.utoronto.ca).
30. Whether the provider-failure event (`model.provider_request.failed`), which carries the
    provider address and a masked key hint, should be sent to any outside system. Security-sensitive:
    refer to the platform maintainer and U of T Information Security (security.utoronto.ca).

### 14.6 Further Points Found During Review

31. **Invalid stored webhooks are dropped on the next save.** A stored admin webhook that no longer
    validates (for example after an upgrade removes an event it names) is hidden from the admin
    list, and the next create, edit, switch or delete of any webhook rewrites `events.webhooks` from
    the valid entries only, so the hidden one is removed for good
    (`backend/open_webui/events.py:838-851`, `:881-922`). Read from the code, not tried.
32. `WEBHOOK_MESSAGES.USER_SIGNUP` (`New user signed up: {username}`) is defined but used nowhere
    in v0.11.4 (`backend/open_webui/constants.py:32-34`); sign-ups now reach webhooks only as the
    `auth.signup` and `user.created` events.
